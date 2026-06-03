#!/usr/bin/env python3
"""Generate or check the local prediction campaign runner readback."""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import (
    DEFAULT_CASE,
    build_prediction_campaign_manifest,
    find_case,
    target_count_for_case,
)
from generate_repeating_prediction_setup import EXAMPLE_ORDER, build_repeating_prediction_setup
from generate_transit_method_options import BASELINE_METHOD_ID, WEATHER_ADJUSTMENT_METHOD_ID
from ope_schema import SPEC, validate_record
from ope_fixtures import compact_json, render_json, validate_and_emit


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-runner"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-runner.generated.json"
SCHEMA = SPEC / "prediction-campaign-runner.schema.json"
SETUP_SCHEMA = SPEC / "repeating-prediction-setup.schema.json"
MANIFEST_SCHEMA = SPEC / "prediction-campaign-manifest.schema.json"
GENERATED_AT = "2026-05-29T00:15:00Z"
INPUT_FLAG_FIELDS = [
    "domain",
    "service_window",
    "interval",
    "count",
    "until",
    "calibration_target",
    "post_calibration_action",
    "post_calibration_delay",
    "live_weather",
    "execute_resolvers",
    "pre_calibrate",
    "history_source",
]


def default_args() -> argparse.Namespace:
    return argparse.Namespace(
        case=DEFAULT_CASE,
        plan_count=4,
        domain=None,
        service_window=None,
        interval=None,
        count=None,
        until=None,
        calibration_target=None,
        post_calibration_action=None,
        post_calibration_delay=None,
        setup_json=None,
        manifest_json=None,
        live_weather=False,
        execute_resolvers=False,
        pre_calibrate=False,
        history_source=None,
        full_materialization=False,
        write_local=False,
        watch=False,
        max_ticks=None,
        poll_seconds=60,
        now=None,
    )


def recurrence_mode(mode: str, flag: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "flagBinding": flag,
        "supportedByDryRun": True,
        "createsForecastArtifacts": False,
    }


def runner_decision(index: int, run: dict[str, Any], status: str, reason: str, next_action: str) -> dict[str, Any]:
    return {
        "decisionId": f"predictionrunnerdecision-{index:03d}",
        "runId": run["runId"],
        "decisionStatus": status,
        "reason": reason,
        "nextAction": next_action,
        "forecastArtifactsCreated": False,
        "liveFetchRequired": False,
        "resolverExecutionRequired": False,
        "writesLiveState": False,
    }


def parse_utc(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise SystemExit(f"Invalid UTC timestamp: {value}") from exc


def clock_decision(index: int, run: dict[str, Any], runner_clock: datetime) -> dict[str, Any]:
    forecast_create = parse_utc(run["forecastCreateAt"])
    forecast_close = parse_utc(run["forecastCloseAt"])
    if runner_clock < forecast_create:
        return runner_decision(
            index,
            run,
            "wait_until_create_time",
            "Runner clock is before forecastCreateAt for this campaign run.",
            "Wait until forecastCreateAt before creating the run.",
        )
    if runner_clock > forecast_close:
        return runner_decision(
            index,
            run,
            "skip_missed_close",
            "Runner clock is after forecastCloseAt and the missed-run policy blocks backfill.",
            "Record a missed state instead of backfilling a forecast.",
        )
    return runner_decision(
        index,
        run,
        "ready_to_create_forecast",
        "Runner clock is inside the forecast creation window for this campaign run.",
        "Create the forecast only with explicit local execution.",
    )


def build_runner_decisions(manifest: dict[str, Any], runner_clock: datetime | None = None) -> list[dict[str, Any]]:
    planned = manifest["plannedRuns"]
    if runner_clock is not None:
        return [
            clock_decision(index, run, runner_clock)
            for index, run in enumerate(planned, start=1)
        ]
    templates = [
        (
            "ready_to_create_forecast",
            "Dry-run clock is at the first candidate create time and forecast close has not passed.",
            "A later effectful runner may create the forecast only with explicit local execution.",
        ),
        (
            "wait_until_create_time",
            "The second candidate is planned but not due at the dry-run readback time.",
            "Wait until forecastCreateAt before creating the run.",
        ),
        (
            "skip_missed_close",
            "The missed-run policy is defined for cases where forecastCloseAt has already passed.",
            "Record a skipped or missed state instead of backfilling a forecast.",
        ),
        (
            "blocked_duplicate",
            "The duplicate key policy blocks a second forecast for the same campaign date/window key.",
            "Keep the original run and do not create a duplicate forecast artifact.",
        ),
    ]
    return [
        runner_decision(index, run, templates[index - 1][0], templates[index - 1][1], templates[index - 1][2])
        for index, run in enumerate(planned[: len(templates)], start=1)
    ]


def missed_run_policy() -> dict[str, Any]:
    return {
        "policyName": "skip_if_forecast_close_passed",
        "defaultAction": "mark_missed_without_forecast",
        "decisionStatus": "skip_missed_close",
        "recordedRunStatus": "missed",
        "triggerCondition": "Apply when forecastCloseAt is earlier than the runner clock before any forecast artifact is created.",
        "exclusionReasonCode": "missed_forecast_close",
        "excludedFromComparableEvidence": True,
        "createsForecastArtifacts": False,
        "createsResolutionArtifacts": False,
        "createsScoringRecords": False,
        "appendsCorpusEvidence": False,
        "nextAction": "Record a missed run state and plan the next eligible window instead of backfilling a forecast.",
    }


def schedule_action(status: str) -> str:
    if status == "ready_to_create_forecast":
        return "create_with_explicit_write_local"
    if status == "wait_until_create_time":
        return "wait_until_forecast_create_at"
    if status == "skip_missed_close":
        return "record_missed_without_forecast"
    if status == "blocked_duplicate":
        return "block_duplicate_without_forecast"
    return "inspect_manual_status"


def build_forecast_schedule(
    manifest: dict[str, Any],
    decisions: list[dict[str, Any]],
    *,
    runner_clock: str | None = None,
) -> dict[str, Any]:
    runs = {run["runId"]: run for run in manifest["plannedRuns"]}
    first_run = manifest["plannedRuns"][0]
    next_row = None
    rows = []
    for decision in decisions:
        run = runs[decision["runId"]]
        row = {
            "runId": run["runId"],
            "decisionStatus": decision["decisionStatus"],
            "scheduleAction": schedule_action(decision["decisionStatus"]),
            "forecastCreateAt": run["forecastCreateAt"],
            "forecastCloseAt": run["forecastCloseAt"],
            "createsForecastArtifacts": False,
            "writesCampaignState": False,
            "nextAction": decision["nextAction"],
        }
        rows.append(row)
        if next_row is None and row["decisionStatus"] in ("ready_to_create_forecast", "wait_until_create_time"):
            next_row = row
    if next_row is None:
        next_row = rows[0]
    return {
        "scheduleMode": "foreground_tick_plan",
        "runnerClock": runner_clock or first_run["forecastCreateAt"],
        "tickPolicy": "Create the ready forecast before close only when --write-local is explicit; wait, miss, or block all other candidate states.",
        "readyRunId": next_row["runId"],
        "nextForecastCreateAt": next_row["forecastCreateAt"],
        "nextForecastCloseAt": next_row["forecastCloseAt"],
        "creationCommand": "python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl",
        "capturedOutputMode": "jsonl",
        "scheduleRows": rows,
        "normalChecksWriteLiveState": False,
        "requiresExplicitWriteLocal": True,
        "createsForecastArtifactsInDryRun": False,
        "nextAction": "Use --now to inspect later due windows and --write-local to create the next due forecast; long-running polling remains separate.",
    }


def method_selection_binding(manifest: dict[str, Any]) -> dict[str, Any]:
    campaign_id = manifest["campaign"]["campaignId"]
    root = f".ope/live/prediction-campaigns/{campaign_id}"
    return {
        "bindingStatus": "baseline_default_no_local_override",
        "defaultMethodId": BASELINE_METHOD_ID,
        "activeMethodId": BASELINE_METHOD_ID,
        "candidateMethodId": WEATHER_ADJUSTMENT_METHOD_ID,
        "methodBindingPath": f"{root}/method-binding.json",
        "applyCommand": "python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --write-local",
        "rollbackCommand": "python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --write-local",
        "requiresApprovedLocalBinding": True,
        "normalChecksReadLocalBinding": False,
        "normalChecksChangeMethod": False,
        "futureForecastsOnly": True,
        "priorForecastHistoryRewriteAllowed": False,
    }


def resolve_input_path(path_value: str) -> Path:
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def load_json_record(path_value: str, schema: Path, label: str) -> dict[str, Any]:
    path = resolve_input_path(path_value)
    if not path.exists():
        raise SystemExit(f"{label} not found: {path_value}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{label} is not valid JSON: {path_value}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{label} must be a JSON object: {path_value}")
    errors = validate_record(data, schema)
    if errors:
        joined = "\n".join(errors)
        raise SystemExit(f"{label} failed schema validation:\n{joined}")
    return data


def flag_overrides(args: argparse.Namespace) -> list[str]:
    overrides = []
    for field in INPUT_FLAG_FIELDS:
        value = getattr(args, field)
        if value is True or (value not in (None, False)):
            overrides.append("--" + field.replace("_", "-"))
    return overrides


def first_number(*values: Any) -> str:
    for value in values:
        if value is not None:
            return str(value)
    return "none"


def source_case_values(case: dict[str, Any] | None) -> dict[str, str]:
    if case is None:
        return {
            "interval": "from_manifest",
            "targetCount": "none",
            "until": "none",
            "calibrationTarget": "none",
            "postCalibrationAction": "none",
            "postCalibrationDelay": "none",
        }
    schedule = case["schedulePolicy"]
    end_conditions = case["endConditions"]
    post_policy = case["postCalibrationPolicy"]
    return {
        "interval": schedule["interval"],
        "targetCount": first_number(
            schedule.get("targetCount"),
            *(condition.get("targetCount") for condition in end_conditions),
        ),
        "until": first_number(
            schedule.get("untilDate"),
            *(condition.get("targetDate") for condition in end_conditions),
        ),
        "calibrationTarget": first_number(
            schedule.get("thresholdValue"),
            *(condition.get("thresholdValue") for condition in end_conditions),
        ),
        "postCalibrationAction": post_policy["action"],
        "postCalibrationDelay": post_policy["delay"],
    }


def build_campaign_creation_request(
    manifest: dict[str, Any],
    case: dict[str, Any] | None,
    args: argparse.Namespace,
    *,
    input_mode: str,
) -> dict[str, Any]:
    source_values = source_case_values(case)
    overrides = flag_overrides(args)
    first_run = manifest["plannedRuns"][0]
    return {
        "inputMode": "flag_overrides" if input_mode == "default_fixture" and overrides else input_mode,
        "setupJsonPath": args.setup_json or "none",
        "manifestJsonPath": args.manifest_json or "none",
        "flagOverrides": overrides,
        "domain": args.domain or manifest["domain"],
        "serviceWindow": args.service_window or manifest["campaign"].get("serviceWindow", first_run["serviceWindow"]),
        "interval": args.interval or source_values["interval"],
        "targetCount": first_number(args.count, source_values["targetCount"]),
        "until": args.until or source_values["until"],
        "calibrationTarget": first_number(args.calibration_target, source_values["calibrationTarget"]),
        "postCalibrationAction": args.post_calibration_action or source_values["postCalibrationAction"],
        "postCalibrationDelay": args.post_calibration_delay or source_values["postCalibrationDelay"],
        "candidatePlanCount": str(manifest["progress"]["plannedRunCount"]),
        "liveWeatherRequested": args.live_weather,
        "resolverExecutionRequested": args.execute_resolvers,
        "preCalibrationRequested": args.pre_calibrate,
        "historySourcePath": args.history_source or "spec/fixtures/local-source-files/transit-delay-history.csv",
        "acceptedForDryRun": True,
        "createsCampaignManifest": False,
        "writesCampaignState": False,
        "nextAction": "Review the normalized campaign request; use --write-local only when creating the ready forecast in ignored local state.",
    }


def pre_calibration_summary(args: argparse.Namespace) -> dict[str, Any]:
    if not args.pre_calibrate:
        return {
            "requestStatus": "not_requested",
            "preCalibrationStatus": "not_requested",
            "predictionCampaignPreCalibrationId": "none",
            "historySourcePath": "none",
            "resolvedOutcomeRowCount": 0,
            "calibratedProbability": 0.25,
            "activeMethodId": BASELINE_METHOD_ID,
            "preCalibrationArtifactPath": "none",
            "methodBindingPath": ".ope/live/prediction-campaigns/predictioncampaign-001/method-binding.json",
            "forecastProbabilitySource": "default_checked_baseline",
            "localWriteRequiredBeforeUse": False,
            "writesDuringDryRun": False,
            "qualityClaimAllowed": False,
            "nextAction": "Add --pre-calibrate to compute a historical-only baseline binding before launch.",
        }

    from generate_prediction_campaign_pre_calibration import build_prediction_campaign_pre_calibration

    record = build_prediction_campaign_pre_calibration(history_source=args.history_source)
    return {
        "requestStatus": "requested",
        "preCalibrationStatus": record["preCalibrationStatus"],
        "predictionCampaignPreCalibrationId": record["predictionCampaignPreCalibrationId"],
        "historySourcePath": record["historySource"]["sourcePath"],
        "resolvedOutcomeRowCount": record["historySource"]["resolvedOutcomeRowCount"],
        "calibratedProbability": record["calibrationMethod"]["calibratedProbability"],
        "activeMethodId": record["engineBinding"]["activeMethodId"],
        "preCalibrationArtifactPath": record["engineBinding"]["preCalibrationArtifactPath"],
        "methodBindingPath": record["engineBinding"]["methodBindingPath"],
        "forecastProbabilitySource": "historical_pre_calibration",
        "localWriteRequiredBeforeUse": True,
        "writesDuringDryRun": False,
        "qualityClaimAllowed": False,
        "nextAction": (
            "Review prediction-campaign pre-calibration, then use --pre-calibrate with --write-local "
            "so the launch tick writes the binding before the forecast."
        ),
    }


def build_runner_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.setup_json and args.manifest_json:
        raise SystemExit("--setup-json and --manifest-json cannot be combined")
    if args.plan_count < 2 or args.plan_count > 12:
        raise SystemExit("--plan-count for the runner must be between 2 and 12")
    if args.count is not None and (args.count < 1 or args.count > 100):
        raise SystemExit("--count for the runner must be between 1 and 100")

    if args.manifest_json:
        if args.full_materialization:
            raise SystemExit("--full-materialization cannot be combined with --manifest-json")
        manifest = load_json_record(args.manifest_json, MANIFEST_SCHEMA, "manifest JSON")
        if len(manifest["plannedRuns"]) < 2:
            raise SystemExit("manifest JSON must include at least 2 planned runs for the runner readback")
        try:
            case = find_case(build_repeating_prediction_setup(), manifest["campaign"]["recurrenceCaseKey"])
        except Exception:
            case = None
        return manifest, build_campaign_creation_request(manifest, case, args, input_mode="manifest_json")

    setup = build_repeating_prediction_setup()
    input_mode = "default_fixture"
    if args.setup_json:
        setup = load_json_record(args.setup_json, SETUP_SCHEMA, "setup JSON")
        input_mode = "setup_json"
    case = find_case(setup, args.case)
    target_count = args.count
    if args.full_materialization and target_count is None:
        target_count = target_count_for_case(case)
    manifest = build_prediction_campaign_manifest(
        case_key=args.case,
        plan_count=args.plan_count,
        target_count=target_count,
        full_materialization=args.full_materialization,
        setup=setup,
    )
    return manifest, build_campaign_creation_request(manifest, case, args, input_mode=input_mode)


def build_prediction_campaign_runner(args: argparse.Namespace | None = None) -> dict[str, Any]:
    if args is None:
        args = default_args()
    manifest, creation_request = build_runner_inputs(args)
    first_run = manifest["plannedRuns"][0]
    runner_clock = parse_utc(args.now) if args.now else None
    decisions = build_runner_decisions(manifest, runner_clock=runner_clock)
    return {
        "predictionCampaignRunnerId": "predictioncampaignrunner-001",
        "generatedAt": GENERATED_AT,
        "runnerStatus": "dry_run_ready_non_executing",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "repeatingPredictionSetupId": manifest["bindings"]["repeatingPredictionSetupId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
            "manifestPath": "spec/fixtures/generated/prediction-campaign-manifest/weather-transit-delay-campaign-manifest.generated.json",
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign start",
            "acceptsSetupJson": True,
            "acceptsManifestJson": True,
            "flags": [
                "--case",
                "--plan-count",
                "--domain",
                "--service-window",
                "--interval",
                "--count",
                "--until",
                "--calibration-target",
                "--post-calibration-action",
                "--post-calibration-delay",
                "--setup-json",
                "--manifest-json",
                "--live-weather",
                "--execute-resolvers",
                "--pre-calibrate",
                "--history-source",
                "--full-materialization",
                "--watch",
                "--max-ticks",
                "--poll-seconds",
                "--now",
                "--write-local",
                "--output-format",
            ],
            "requiresExplicitLiveFetchFlag": True,
            "requiresExplicitResolverExecutionFlag": True,
            "defaultMissedRunPolicy": "skip_if_forecast_close_passed",
        },
        "campaignCreationRequest": creation_request,
        "forecastSchedule": build_forecast_schedule(manifest, decisions, runner_clock=args.now),
        "methodSelectionBinding": method_selection_binding(manifest),
        "preCalibration": pre_calibration_summary(args),
        "supportedRecurrenceModes": [
            recurrence_mode("fixed_count", "--count"),
            recurrence_mode("until_date", "--until"),
            recurrence_mode("open_ended", "--count omitted with explicit stop policy"),
            recurrence_mode("interval", "--interval"),
            recurrence_mode("calibration_threshold", "--calibration-target"),
            recurrence_mode("post_calibration_restart", "--post-calibration-action pause_then_resume_after"),
        ],
        "runnerDecisions": decisions,
        "missedRunPolicy": missed_run_policy(),
        "outputModes": {
            "interactiveTerminalMode": "compact_human_status_lines",
            "capturedStdoutMode": "jsonl",
            "jsonlExample": "{\"event\":\"campaign_runner_decision\",\"runId\":\"predictionrun-1301\",\"decisionStatus\":\"ready_to_create_forecast\"}",
            "humanLineExample": "predictionrun-1301 ready_to_create_forecast forecastCloseAt=2026-06-11T04:45:00Z",
        },
        "progress": {
            "plannedRunCount": manifest["progress"]["plannedRunCount"],
            "readyToCreateForecastCount": sum(
                1 for decision in decisions if decision["decisionStatus"] == "ready_to_create_forecast"
            ),
            "materializedRunCount": len(manifest["plannedRuns"]),
            "forecastArtifactsCreated": 0,
            "resolvedComparableOutcomes": 0,
            "nextForecastRunId": runner_next_forecast_run_id(decisions, first_run),
            "nextAction": "Use --write-local for the next due creation tick; future-window polling remains separate.",
        },
        "summary": {
            "terminalRunnerSurfaceImplemented": True,
            "dryRunOnly": True,
            "forecastCreationImplemented": True,
            "resolverExecutionImplemented": False,
            "writesLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "preCalibrationImplemented": True,
            "qualityClaimAllowed": False,
            "recommendedNextMilestone": "Milestone 105 campaign outcome resolver execution",
        },
        "executionBoundary": {
            "readOnlyDryRun": True,
            "createsForecastArtifacts": False,
            "executesForecastRunner": False,
            "sleepsOrPolls": False,
            "writesIgnoredLiveState": False,
            "writesPreCalibrationState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This runner readback checks command semantics by default; --write-local performs one due-run creation tick.",
            "Optional --pre-calibrate uses historical data only and writes a prospective baseline binding only when --write-local is explicit.",
            "Long-running future-window polling remains separate and must preserve forecast-before-close boundaries.",
            "Live weather and resolver execution require explicit future flags and remain disabled in normal checks.",
            "No calibration or quality claim is allowed from dry-run runner decisions.",
        ],
    }


def build_local_start_result(
    runner: dict[str, Any],
    write_result: dict[str, Any],
    *,
    pre_calibration_result: dict[str, Any] | str = "none",
) -> dict[str, Any]:
    return {
        "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
        "generatedAt": write_result["generatedAt"],
        "runnerStatus": "local_forecast_created",
        "domain": runner["domain"],
        "bindings": write_result["bindings"],
        "runnerDecisionId": write_result["bindings"]["runnerDecisionId"],
        "runId": write_result["bindings"]["runId"],
        "forecastId": write_result["bindings"]["forecastId"],
        "writeStatus": write_result["writeStatus"],
        "idempotencyKey": write_result["idempotencyKey"],
        "preCalibrationResult": pre_calibration_result,
        "artifactWrites": write_result["artifactWrites"],
        "stateWrites": write_result["stateWrites"],
        "summary": {
            "terminalRunnerSurfaceImplemented": True,
            "foregroundExecutionImplemented": True,
            "forecastCreationImplemented": True,
            "forecastArtifactsCreated": write_result["summary"]["forecastArtifactsCreated"],
            "preCalibrationRequested": runner["preCalibration"]["requestStatus"] == "requested",
            "preCalibrationWriteStatus": (
                pre_calibration_result["writeStatus"]
                if isinstance(pre_calibration_result, dict)
                else "not_requested"
            ),
            "newFileWriteCount": write_result["summary"]["newFileWriteCount"],
            "alreadyPresentCount": write_result["summary"]["alreadyPresentCount"],
            "resolverExecutionImplemented": False,
            "fetchesLiveData": False,
            "qualityClaimAllowed": False,
            "nextAction": write_result["summary"]["nextAction"],
        },
        "executionBoundary": {
            "writesIgnoredLiveState": True,
            "writesCampaignState": True,
            "writesPreCalibrationState": isinstance(pre_calibration_result, dict),
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
    }


def runner_next_forecast_run_id(decisions: list[dict[str, Any]], fallback_run: dict[str, Any]) -> str:
    for decision in decisions:
        if decision["decisionStatus"] in ("ready_to_create_forecast", "wait_until_create_time"):
            return str(decision["runId"])
    return str(fallback_run["runId"])


def ready_run_id_for_write(runner: dict[str, Any]) -> str:
    for row in runner["forecastSchedule"]["scheduleRows"]:
        if row["scheduleAction"] == "create_with_explicit_write_local":
            return str(row["runId"])
    raise SystemExit("No campaign run is currently ready for --write-local")


def local_run_state_path(runner: dict[str, Any], run_id: str) -> Path:
    campaign_id = runner["bindings"]["campaignId"]
    return ROOT / ".ope" / "live" / "prediction-campaigns" / campaign_id / f"{run_id}.json"


def local_run_state_exists(runner: dict[str, Any], run_id: str) -> bool:
    return local_run_state_path(runner, run_id).exists()


def pre_calibration_record_for_args(args: argparse.Namespace) -> dict[str, Any] | None:
    if not args.pre_calibrate:
        return None
    from generate_prediction_campaign_pre_calibration import build_prediction_campaign_pre_calibration

    return build_prediction_campaign_pre_calibration(history_source=args.history_source)


def execute_pre_calibration_for_args(args: argparse.Namespace) -> tuple[dict[str, Any] | None, dict[str, Any] | str]:
    record = pre_calibration_record_for_args(args)
    if record is None:
        return None, "none"
    from generate_prediction_campaign_pre_calibration import (
        execute_local_pre_calibration,
        build_prediction_campaign_pre_calibration,
    )

    result = execute_local_pre_calibration(record)
    written_record = build_prediction_campaign_pre_calibration(
        history_source=args.history_source,
        write_result=result,
    )
    return written_record, result


def build_resolution_attempts_for_tick(
    runner: dict[str, Any],
    manifest: dict[str, Any],
    *,
    execute_resolvers: bool,
) -> list[dict[str, Any]]:
    if not execute_resolvers:
        return []
    from generate_prediction_campaign_resolution_attempt import build_prediction_campaign_resolution_attempt

    runs = {run["runId"]: run for run in manifest["plannedRuns"]}
    runner_clock = runner["forecastSchedule"]["runnerClock"]
    attempts = []
    for row in runner["forecastSchedule"]["scheduleRows"]:
        run = runs[row["runId"]]
        if parse_utc(runner_clock) < parse_utc(run["resolutionEligibleAt"]):
            continue
        attempts.append(
            build_prediction_campaign_resolution_attempt(
                run_id=row["runId"],
                now=runner_clock,
                execute_resolvers=True,
            )
        )
    return attempts


def build_foreground_tick(
    runner: dict[str, Any],
    manifest: dict[str, Any],
    args: argparse.Namespace,
    *,
    tick_number: int,
    execute_local_write: bool,
    execute_resolvers: bool,
) -> dict[str, Any]:
    write_result = None
    pre_calibration_record = None
    pre_calibration_write_result: dict[str, Any] | str = "none"
    selected_run_id = None
    actions = []
    resolution_attempts = build_resolution_attempts_for_tick(
        runner,
        manifest,
        execute_resolvers=execute_resolvers,
    )
    for row in runner["forecastSchedule"]["scheduleRows"]:
        existing_state = execute_local_write and local_run_state_exists(runner, row["runId"])
        if existing_state:
            action_status = "already_created_waiting_resolution"
            forecast_created = False
            writes_campaign_state = False
        elif row["scheduleAction"] == "create_with_explicit_write_local":
            if selected_run_id is not None:
                action_status = "ready_deferred_after_one_creation"
                forecast_created = False
                writes_campaign_state = False
            elif execute_local_write:
                from prediction_campaign_forecast_write_runtime import execute_local_forecast_write
                from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write

                pre_calibration_record, pre_calibration_write_result = execute_pre_calibration_for_args(args)

                write_result = execute_local_forecast_write(
                    run_id=row["runId"],
                    manifest=manifest,
                    runner=runner,
                    plan_builder=lambda **kwargs: build_prediction_campaign_forecast_write(
                        **kwargs,
                        pre_calibration=pre_calibration_record,
                    ),
                )
                selected_run_id = row["runId"]
                action_status = write_result["writeStatus"]
                forecast_created = write_result["summary"]["forecastArtifactsCreated"] > 0
                writes_campaign_state = write_result["executionBoundary"]["writesCampaignState"]
            else:
                selected_run_id = row["runId"]
                action_status = "dry_run_ready_for_write_local"
                forecast_created = False
                writes_campaign_state = False
        elif row["scheduleAction"] == "wait_until_forecast_create_at":
            action_status = "waiting_for_create_time"
            forecast_created = False
            writes_campaign_state = False
        elif row["scheduleAction"] == "record_missed_without_forecast":
            action_status = "missed_record_not_written"
            forecast_created = False
            writes_campaign_state = False
        else:
            action_status = "blocked_without_write"
            forecast_created = False
            writes_campaign_state = False
        actions.append(
            {
                "runId": row["runId"],
                "decisionStatus": row["decisionStatus"],
                "scheduleAction": row["scheduleAction"],
                "actionStatus": action_status,
                "forecastCreated": forecast_created,
                "writesCampaignState": writes_campaign_state,
                "preCalibrationRequested": args.pre_calibrate,
                "preCalibrationStatus": (
                    "not_requested"
                    if not args.pre_calibrate
                    else (
                        pre_calibration_write_result["writeStatus"]
                        if isinstance(pre_calibration_write_result, dict)
                        else "dry_run_ready"
                    )
                ),
            }
        )

    return {
        "tickNumber": tick_number,
        "startedAt": write_result["generatedAt"] if write_result else runner["generatedAt"],
        "tickStatus": (
            "local_forecast_created"
            if write_result
            else ("no_due_forecast_created" if execute_local_write else "dry_run_ready")
        ),
        "runnerClock": runner["forecastSchedule"]["runnerClock"],
        "readyRunId": selected_run_id or runner["forecastSchedule"]["readyRunId"],
        "actions": actions,
        "preCalibrationResult": pre_calibration_write_result,
        "writeResult": write_result or "none",
        "resolutionAttempts": resolution_attempts,
        "nextPollSeconds": 0,
    }


def build_foreground_result(
    runner: dict[str, Any],
    ticks: list[dict[str, Any]],
    *,
    execute_local_write: bool,
    execute_resolvers: bool,
    poll_seconds: int,
) -> dict[str, Any]:
    created_count = sum(1 for tick in ticks for action in tick["actions"] if action["forecastCreated"])
    resolution_attempt_count = sum(len(tick["resolutionAttempts"]) for tick in ticks)
    pre_calibration_write_count = len(
        [
            tick
            for tick in ticks
            if isinstance(tick.get("preCalibrationResult"), dict)
            and tick["preCalibrationResult"]["writeStatus"]
            in {"local_pre_calibration_completed", "local_pre_calibration_already_present"}
        ]
    )
    return {
        "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
        "generatedAt": ticks[-1]["startedAt"],
        "runnerStatus": "foreground_forecast_ticks_completed",
        "domain": runner["domain"],
        "executionMode": (
            "explicit_local_write_and_resolver_attempt"
            if execute_local_write and execute_resolvers
            else "explicit_resolver_attempt"
            if execute_resolvers
            else "explicit_local_write"
            if execute_local_write
            else "dry_run"
        ),
        "tickCount": len(ticks),
        "pollSeconds": poll_seconds,
        "ticks": ticks,
        "summary": {
            "foregroundExecutionImplemented": True,
            "boundedForegroundSchedulingImplemented": True,
            "nextDueRunSchedulingImplemented": True,
            "futureWindowPollingImplemented": False,
            "forecastArtifactsCreated": created_count,
            "writesCampaignState": execute_local_write and created_count > 0,
            "preCalibrationRequested": runner["preCalibration"]["requestStatus"] == "requested",
            "preCalibrationWriteCount": pre_calibration_write_count,
            "resolutionAttemptCount": resolution_attempt_count,
            "resolverExecutionRequested": execute_resolvers,
            "resolverExecutionImplemented": False,
            "fetchesLiveData": False,
            "appendsCorpusEvidence": False,
            "qualityClaimAllowed": False,
            "nextAction": (
                "Attach a checked campaign outcome source before any campaign resolver can create resolution or scoring records."
                if resolution_attempt_count
                else "Use campaign-aware resolution jobs after the created forecast reaches its resolution window."
            ),
        },
        "executionBoundary": {
            "writesIgnoredLiveState": execute_local_write and created_count > 0,
            "writesCampaignState": execute_local_write and created_count > 0,
            "writesPreCalibrationState": pre_calibration_write_count > 0,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
    }


def run_foreground_ticks(runner: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.watch and args.max_ticks is None:
        raise SystemExit("--watch requires --max-ticks for this bounded campaign runner slice")
    if args.max_ticks is not None and args.max_ticks < 1:
        raise SystemExit("--max-ticks must be at least 1")
    if args.poll_seconds < 1:
        raise SystemExit("--poll-seconds must be at least 1")

    max_ticks = args.max_ticks if args.max_ticks is not None else 1
    manifest, _creation_request = build_runner_inputs(args)
    ticks = []
    for tick_number in range(1, max_ticks + 1):
        tick = build_foreground_tick(
            runner,
            manifest,
            args,
            tick_number=tick_number,
            execute_local_write=args.write_local and tick_number == 1,
            execute_resolvers=args.execute_resolvers,
        )
        tick["nextPollSeconds"] = args.poll_seconds if tick_number < max_ticks else 0
        ticks.append(tick)
        if tick_number < max_ticks:
            time.sleep(args.poll_seconds)
    return build_foreground_result(
        runner,
        ticks,
        execute_local_write=args.write_local,
        execute_resolvers=args.execute_resolvers,
        poll_seconds=args.poll_seconds,
    )


def print_start_result(result: dict[str, Any], output_format: str | None) -> None:
    if output_format == "human":
        if result.get("runnerStatus") == "foreground_forecast_ticks_completed":
            print(
                f"forecast scheduler {result['executionMode']} "
                f"ticks={result['tickCount']} created={result['summary']['forecastArtifactsCreated']}"
            )
            return
        print(
            f"{result['runId']} {result['writeStatus']} "
            f"forecastId={result['forecastId']} newFiles={result['summary']['newFileWriteCount']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(result), end="")
        return
    print(render_json(result), end="")


def print_view(runner: dict[str, Any], view: str) -> None:
    views = {
        "runner": runner,
        "campaign-creation": runner["campaignCreationRequest"],
        "forecast-schedule": runner["forecastSchedule"],
        "decisions": runner["runnerDecisions"],
        "pre-calibration": runner["preCalibration"],
        "missed-run-policy": runner["missedRunPolicy"],
        "summary": runner["summary"],
        "boundary": runner["executionBoundary"],
    }
    print(render_json(views[view]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(data, SCHEMA, OUTPUT_PATH, write=write, label="prediction campaign runner", regen="python3 scripts/generate_prediction_campaign_runner.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign runner")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign runner drift")
    parser.add_argument(
        "--case",
        choices=EXAMPLE_ORDER,
        default=DEFAULT_CASE,
        help="choose one repeating prediction setup example to expand",
    )
    parser.add_argument(
        "--plan-count",
        type=int,
        default=4,
        help="number of dry-run candidate runs to include in the runner readback",
    )
    parser.add_argument("--domain", help="dry-run runner domain selector")
    parser.add_argument("--service-window", help="dry-run runner service window selector")
    parser.add_argument("--interval", help="dry-run runner recurrence interval")
    parser.add_argument("--count", type=int, help="dry-run runner finite run count")
    parser.add_argument("--until", help="dry-run runner until-date boundary")
    parser.add_argument("--calibration-target", type=int, help="dry-run runner calibration target")
    parser.add_argument("--post-calibration-action", help="dry-run runner post-calibration action")
    parser.add_argument("--post-calibration-delay", help="dry-run runner post-calibration delay")
    parser.add_argument("--setup-json", help="dry-run runner setup JSON input path")
    parser.add_argument("--manifest-json", help="dry-run runner manifest JSON input path")
    parser.add_argument("--live-weather", action="store_true", help="record an explicit future live-weather request")
    parser.add_argument("--execute-resolvers", action="store_true", help="record an explicit future resolver request")
    parser.add_argument(
        "--pre-calibrate",
        action="store_true",
        help="compute optional historical-only pre-calibration before an explicit local launch write",
    )
    parser.add_argument("--history-source", help="approved historical delay CSV/JSON source for --pre-calibrate")
    parser.add_argument(
        "--full-materialization",
        action="store_true",
        help="expand the complete local pilot plan before foreground scheduling",
    )
    parser.add_argument("--watch", action="store_true", help="run bounded foreground forecast scheduling ticks")
    parser.add_argument("--max-ticks", type=int, help="number of foreground scheduling ticks to run")
    parser.add_argument("--poll-seconds", type=int, default=60, help="seconds between foreground scheduling ticks")
    parser.add_argument("--now", help="UTC runner clock for forecast scheduling decisions")
    parser.add_argument(
        "--write-local",
        action="store_true",
        help="explicitly create the ready campaign forecast in ignored local state",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for --write-local output",
    )
    parser.add_argument(
        "--view",
        choices=[
            "runner",
            "campaign-creation",
            "forecast-schedule",
            "decisions",
            "pre-calibration",
            "missed-run-policy",
            "summary",
            "boundary",
        ],
        default="runner",
        help="print one prediction campaign runner view",
    )
    args = parser.parse_args()

    if args.write or args.check:
        if args.write_local:
            raise SystemExit("--write-local cannot be combined with --write or --check")
        if args.setup_json or args.manifest_json or args.now or args.full_materialization or flag_overrides(args):
            raise SystemExit("custom campaign inputs cannot be combined with --write or --check")
        runner = build_prediction_campaign_runner(args)
        check_or_write(runner, write=args.write)
        return
    runner = build_prediction_campaign_runner(args)
    if args.watch or args.max_ticks is not None:
        try:
            result = run_foreground_ticks(runner, args)
        except Exception as exc:
            raise SystemExit(str(exc)) from exc
        print_start_result(result, args.output_format)
        return
    if args.write_local:
        from prediction_campaign_forecast_write_runtime import (
            PredictionCampaignForecastWriteError,
            execute_local_forecast_write,
        )
        from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
        from generate_prediction_campaign_pre_calibration import PredictionCampaignPreCalibrationError

        try:
            manifest, _creation_request = build_runner_inputs(args)
            pre_calibration_record, pre_calibration_result = execute_pre_calibration_for_args(args)
            write_result = execute_local_forecast_write(
                run_id=ready_run_id_for_write(runner),
                manifest=manifest,
                runner=runner,
                plan_builder=lambda **kwargs: build_prediction_campaign_forecast_write(
                    **kwargs,
                    pre_calibration=pre_calibration_record,
                ),
            )
        except (PredictionCampaignForecastWriteError, PredictionCampaignPreCalibrationError) as exc:
            raise SystemExit(str(exc)) from exc
        print_start_result(
            build_local_start_result(
                runner,
                write_result,
                pre_calibration_result=pre_calibration_result,
            ),
            args.output_format,
        )
        return
    errors = validate_record(runner, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(runner, args.view)


if __name__ == "__main__":
    main()
