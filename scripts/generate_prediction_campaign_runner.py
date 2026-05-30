#!/usr/bin/env python3
"""Generate or check the local prediction campaign runner readback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import DEFAULT_CASE, build_prediction_campaign_manifest, find_case
from generate_repeating_prediction_setup import EXAMPLE_ORDER, build_repeating_prediction_setup
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, compact_json, render_json, write_generated


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


def build_runner_decisions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    planned = manifest["plannedRuns"]
    return [
        runner_decision(
            1,
            planned[0],
            "ready_to_create_forecast",
            "Dry-run clock is at the first candidate create time and forecast close has not passed.",
            "A later effectful runner may create the forecast only with explicit local execution.",
        ),
        runner_decision(
            2,
            planned[1],
            "wait_until_create_time",
            "The second candidate is planned but not due at the dry-run readback time.",
            "Wait until forecastCreateAt before creating the run.",
        ),
        runner_decision(
            3,
            planned[2],
            "skip_missed_close",
            "The missed-run policy is defined for cases where forecastCloseAt has already passed.",
            "Record a skipped or missed state instead of backfilling a forecast.",
        ),
        runner_decision(
            4,
            planned[3],
            "blocked_duplicate",
            "The duplicate key policy blocks a second forecast for the same campaign date/window key.",
            "Keep the original run and do not create a duplicate forecast artifact.",
        ),
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
        "acceptedForDryRun": True,
        "createsCampaignManifest": False,
        "writesCampaignState": False,
        "nextAction": "Review the normalized campaign request; use --write-local only when creating the ready forecast in ignored local state.",
    }


def build_runner_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    if args.setup_json and args.manifest_json:
        raise SystemExit("--setup-json and --manifest-json cannot be combined")
    if args.plan_count < 4 or args.plan_count > 12:
        raise SystemExit("--plan-count for the runner must be between 4 and 12")

    if args.manifest_json:
        manifest = load_json_record(args.manifest_json, MANIFEST_SCHEMA, "manifest JSON")
        if len(manifest["plannedRuns"]) < 4:
            raise SystemExit("manifest JSON must include at least 4 planned runs for the runner readback")
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
    manifest = build_prediction_campaign_manifest(case_key=args.case, plan_count=args.plan_count, setup=setup)
    return manifest, build_campaign_creation_request(manifest, case, args, input_mode=input_mode)


def build_prediction_campaign_runner(args: argparse.Namespace | None = None) -> dict[str, Any]:
    if args is None:
        args = default_args()
    manifest, creation_request = build_runner_inputs(args)
    first_run = manifest["plannedRuns"][0]
    decisions = build_runner_decisions(manifest)
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
                "--write-local",
                "--output-format",
            ],
            "requiresExplicitLiveFetchFlag": True,
            "requiresExplicitResolverExecutionFlag": True,
            "defaultMissedRunPolicy": "skip_if_forecast_close_passed",
        },
        "campaignCreationRequest": creation_request,
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
            "readyToCreateForecastCount": 1,
            "forecastArtifactsCreated": 0,
            "resolvedComparableOutcomes": 0,
            "nextForecastRunId": first_run["runId"],
            "nextAction": "Use --write-local for the ready-run creation tick; future-window scheduling remains next.",
        },
        "summary": {
            "terminalRunnerSurfaceImplemented": True,
            "dryRunOnly": True,
            "forecastCreationImplemented": False,
            "resolverExecutionImplemented": False,
            "writesLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "qualityClaimAllowed": False,
            "recommendedNextMilestone": "Milestone 93 forecast scheduling after explicit local creation",
        },
        "executionBoundary": {
            "readOnlyDryRun": True,
            "createsForecastArtifacts": False,
            "executesForecastRunner": False,
            "sleepsOrPolls": False,
            "writesIgnoredLiveState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This runner readback checks command semantics by default; --write-local performs one ready-run creation tick.",
            "Forecast scheduling across future windows remains a later effectful milestone and must preserve forecast-before-close boundaries.",
            "Live weather and resolver execution require explicit future flags and remain disabled in normal checks.",
            "No calibration or quality claim is allowed from dry-run runner decisions.",
        ],
    }


def build_local_start_result(runner: dict[str, Any], write_result: dict[str, Any]) -> dict[str, Any]:
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
        "artifactWrites": write_result["artifactWrites"],
        "stateWrites": write_result["stateWrites"],
        "summary": {
            "terminalRunnerSurfaceImplemented": True,
            "foregroundExecutionImplemented": True,
            "forecastCreationImplemented": True,
            "forecastArtifactsCreated": write_result["summary"]["forecastArtifactsCreated"],
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
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
    }


def print_start_result(result: dict[str, Any], output_format: str | None) -> None:
    if output_format == "human":
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
        "decisions": runner["runnerDecisions"],
        "missed-run-policy": runner["missedRunPolicy"],
        "summary": runner["summary"],
        "boundary": runner["executionBoundary"],
    }
    print(render_json(views[view]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    errors = validate_record(data, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    if write:
        write_generated(OUTPUT_PATH, data, label="prediction campaign runner", regen="python3 scripts/generate_prediction_campaign_runner.py --write")
    else:
        check_generated(OUTPUT_PATH, data, label="prediction campaign runner", regen="python3 scripts/generate_prediction_campaign_runner.py --write")


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
        choices=["runner", "campaign-creation", "decisions", "missed-run-policy", "summary", "boundary"],
        default="runner",
        help="print one prediction campaign runner view",
    )
    args = parser.parse_args()

    if args.write or args.check:
        if args.write_local:
            raise SystemExit("--write-local cannot be combined with --write or --check")
        if args.setup_json or args.manifest_json or flag_overrides(args):
            raise SystemExit("custom campaign inputs cannot be combined with --write or --check")
        runner = build_prediction_campaign_runner(args)
        check_or_write(runner, write=args.write)
        return
    runner = build_prediction_campaign_runner(args)
    if args.write_local:
        from generate_prediction_campaign_forecast_write import (
            PredictionCampaignForecastWriteError,
            execute_local_forecast_write,
        )

        try:
            write_result = execute_local_forecast_write()
        except PredictionCampaignForecastWriteError as exc:
            raise SystemExit(str(exc)) from exc
        print_start_result(build_local_start_result(runner, write_result), args.output_format)
        return
    errors = validate_record(runner, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(runner, args.view)


if __name__ == "__main__":
    main()
