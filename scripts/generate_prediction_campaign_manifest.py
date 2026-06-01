#!/usr/bin/env python3
"""Generate or check the local prediction campaign manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from generate_repeating_prediction_setup import EXAMPLE_ORDER, build_repeating_prediction_setup
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json, validate_and_emit


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-manifest"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-manifest.generated.json"
SCHEMA = SPEC / "prediction-campaign-manifest.schema.json"
GENERATED_AT = "2026-05-29T00:00:00Z"
DEFAULT_CASE = "daily_100_run_transit_calibration"
DEFAULT_PLAN_COUNT = 4
MAX_PREVIEW_COUNT = 12
MAX_FULL_MATERIALIZATION_COUNT = 100

RUN_STATUSES = [
    "planned_forecast_pending",
    "waiting_resolution",
    "due_resolution",
    "resolved",
    "skipped",
    "missed",
    "canceled",
    "failed",
    "manually_stopped",
    "blocked_duplicate",
]


class PredictionCampaignManifestError(Exception):
    pass


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def find_case(setup: dict[str, Any], case_key: str) -> dict[str, Any]:
    cases = {item["caseKey"]: item for item in setup["campaignExamples"]}
    if case_key not in cases:
        raise PredictionCampaignManifestError(f"Unknown campaign case: {case_key}")
    return cases[case_key]


def run_id(prefix: str, sequence: int) -> str:
    return f"{prefix}-{1300 + sequence}"


def target_count_for_case(case: dict[str, Any]) -> int:
    schedule = case["schedulePolicy"]
    if "targetCount" in schedule:
        return int(schedule["targetCount"])
    for condition in case["endConditions"]:
        if "targetCount" in condition:
            return int(condition["targetCount"])
    return DEFAULT_PLAN_COUNT


def build_planned_runs(
    setup: dict[str, Any],
    case: dict[str, Any],
    *,
    plan_count: int,
) -> list[dict[str, Any]]:
    schedule = case["schedulePolicy"]
    source_policy_id = setup["sourcePolicyBinding"]["sourcePolicyId"]
    start = parse_utc(schedule["nextForecastCandidateAt"])
    service_window = schedule.get("selectedWindows", ["morning_peak"])[0]
    cycle_id = "predictioncycle-001"
    runs = []
    for sequence in range(1, plan_count + 1):
        service_date = (start + timedelta(days=sequence - 1)).date().isoformat()
        forecast_create = start + timedelta(days=sequence - 1)
        forecast_close = forecast_create + timedelta(hours=4, minutes=45)
        horizon_start = forecast_create + timedelta(hours=5)
        horizon_end = forecast_create + timedelta(hours=7)
        resolution_eligible = horizon_end + timedelta(minutes=15)
        runs.append(
            {
                "runId": run_id("predictionrun", sequence),
                "cycleId": cycle_id,
                "sequenceNumber": sequence,
                "serviceDate": service_date,
                "serviceWindow": service_window,
                "forecastCreateAt": timestamp(forecast_create),
                "forecastCloseAt": timestamp(forecast_close),
                "horizonStartsAt": timestamp(horizon_start),
                "horizonEndsAt": timestamp(horizon_end),
                "resolutionEligibleAt": timestamp(resolution_eligible),
                "questionId": run_id("question", sequence),
                "forecastId": run_id("forecast", sequence),
                "resolutionId": run_id("resolution", sequence),
                "scoringReportId": run_id("scoring", sequence),
                "sourcePolicyId": source_policy_id,
                "runStatus": "planned_forecast_pending",
                "duplicateKey": f"weather-transit-delays:hsl-surface:helsinki:{service_date}:{service_window}",
                "plannedStatePath": f".ope/live/prediction-campaigns/predictioncampaign-001/{run_id('predictionrun', sequence)}.json",
                "createsForecastArtifacts": False,
                "fetchesLiveData": False,
                "mutatesCampaignState": False,
            }
        )
    return runs


def build_materialization(
    planned_runs: list[dict[str, Any]],
    *,
    target_count: int,
    full_materialization: bool,
) -> dict[str, Any]:
    duplicate_keys = [run["duplicateKey"] for run in planned_runs]
    duplicate_conflict_count = len(duplicate_keys) - len(set(duplicate_keys))
    first_run = planned_runs[0]
    final_run = planned_runs[-1]
    return {
        "materializationMode": "full_100_run_pilot" if full_materialization else "bounded_preview",
        "targetRunCount": target_count,
        "materializedRunCount": len(planned_runs),
        "boundedPreview": not full_materialization,
        "boundedPreviewMaxCount": MAX_PREVIEW_COUNT,
        "fullMaterializationRequested": full_materialization,
        "fullMaterializationAvailable": True,
        "firstRunId": first_run["runId"],
        "nextRunId": first_run["runId"],
        "finalRunId": final_run["runId"],
        "firstServiceDate": first_run["serviceDate"],
        "finalServiceDate": final_run["serviceDate"],
        "duplicateKeyCount": len(duplicate_keys),
        "duplicateConflictCount": duplicate_conflict_count,
        "duplicateAuditStatus": "duplicate_conflicts" if duplicate_conflict_count else "unique_duplicate_keys",
        "createsForecastArtifacts": False,
        "writesCampaignState": False,
        "normalChecksWriteLiveState": False,
        "nextAction": (
            "Review the full 100-run pilot plan before enabling local forecast runner writes."
            if full_materialization
            else "Use --full-materialization with --count 100 to inspect the complete Helsinki pilot plan."
        ),
    }


def status_example(status: str, meaning: str, next_action: str) -> dict[str, Any]:
    return {
        "runStatus": status,
        "meaning": meaning,
        "nextAction": next_action,
        "createsForecastArtifacts": False,
        "mutatesCampaignState": False,
    }


def build_status_examples() -> list[dict[str, Any]]:
    return [
        status_example(
            "planned_forecast_pending",
            "A future run has unique IDs and a candidate window, but no forecast artifact exists yet.",
            "A later runner may create the forecast only before forecastCloseAt.",
        ),
        status_example(
            "waiting_resolution",
            "A forecast exists and the service window has not ended yet.",
            "Wait until resolutionEligibleAt before attempting resolution.",
        ),
        status_example(
            "due_resolution",
            "A forecast exists, the horizon has ended, and resolution-only evidence may be gathered.",
            "Run a checked resolver only with an explicit execution command in a later milestone.",
        ),
        status_example(
            "resolved",
            "Resolution and scoring records exist and can be considered for comparable evidence if claim gates allow it.",
            "Inspect scoring and append-readiness before any corpus mutation.",
        ),
        status_example(
            "skipped",
            "The runner intentionally skipped a candidate before close time with a recorded reason.",
            "Keep the skipped run out of comparable outcome counts.",
        ),
        status_example(
            "missed",
            "The runner noticed the forecast close time after it had already passed.",
            "Do not backfill; record the missed window and plan the next eligible run.",
        ),
        status_example(
            "canceled",
            "The caller canceled a planned or waiting run.",
            "Preserve the cancellation reason and do not create new artifacts for the run.",
        ),
        status_example(
            "failed",
            "A planned execution failed with sanitized diagnostics.",
            "Retry only if the close-time and source-policy boundaries still allow it.",
        ),
        status_example(
            "manually_stopped",
            "The caller stopped the campaign or cycle before the end condition was reached.",
            "Leave future runs uncreated unless the caller explicitly resumes.",
        ),
        status_example(
            "blocked_duplicate",
            "A service date/window duplicate key already exists in the campaign.",
            "Do not create a second forecast for the same campaign key.",
        ),
    ]


def build_prediction_campaign_manifest(
    *,
    case_key: str = DEFAULT_CASE,
    plan_count: int = DEFAULT_PLAN_COUNT,
    target_count: int | None = None,
    full_materialization: bool = False,
    setup: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if setup is None:
        setup = build_repeating_prediction_setup()
    case = find_case(setup, case_key)
    schedule = case["schedulePolicy"]
    target_run_count = target_count or target_count_for_case(case)
    materialized_count = target_run_count if full_materialization else plan_count
    planned_runs = build_planned_runs(setup, case, plan_count=materialized_count)
    first_run = planned_runs[0]
    manifest = {
        "predictionCampaignManifestId": "predictioncampaignmanifest-001",
        "generatedAt": GENERATED_AT,
        "manifestStatus": "planned_dry_run_non_executing",
        "domain": setup["domain"],
        "bindings": {
            "repeatingPredictionSetupId": setup["repeatingPredictionSetupId"],
            "domainSetupId": setup["bindings"]["domainSetupId"],
            "sourcePolicyId": setup["bindings"]["sourcePolicyId"],
            "transitMethodOptionsId": setup["bindings"]["transitMethodOptionsId"],
            "transitBaselineTrackRecordGateId": setup["bindings"]["transitBaselineTrackRecordGateId"],
            "transitLiveEvidencePromotionId": setup["bindings"]["transitLiveEvidencePromotionId"],
            "repeatingPredictionSetupPath": "spec/fixtures/generated/repeating-prediction-setup/ope-repeating-prediction-setup.generated.json",
        },
        "localStatePolicy": {
            "workspaceRoot": ".ope/live/prediction-campaigns",
            "campaignStatePath": ".ope/live/prediction-campaigns/predictioncampaign-001/campaign-manifest.json",
            "relativePathsOnly": True,
            "gitIgnored": True,
            "normalChecksWriteLiveState": False,
            "credentialsStored": False,
            "privateRowsStored": False,
            "sanitizedDiagnosticsOnly": True,
        },
        "campaign": {
            "campaignId": "predictioncampaign-001",
            "cycleId": "predictioncycle-001",
            "recurrenceCaseKey": case_key,
            "schedulePolicyId": schedule["schedulePolicyId"],
            "timezone": schedule["timezone"],
            "serviceWindow": first_run["serviceWindow"],
            "createdFromSetupAt": GENERATED_AT,
            "campaignStatePath": ".ope/live/prediction-campaigns/predictioncampaign-001/campaign-manifest.json",
            "runnerImplemented": False,
        },
        "idNamespace": {
            "campaignId": "predictioncampaign-001",
            "cycleId": "predictioncycle-001",
            "runIdPrefix": "predictionrun",
            "questionIdPrefix": "question",
            "forecastIdPrefix": "forecast",
            "resolutionIdPrefix": "resolution",
            "scoringReportIdPrefix": "scoring",
            "nextSequenceStart": 1301,
            "uniquenessRule": "IDs are minted from the campaign sequence and must not reuse committed fixture IDs such as forecast-1102.",
        },
        "planningWindow": {
            "dryRunPlannerImplemented": True,
            "nextCandidateCount": len(planned_runs),
            "duplicateKeyFields": ["domain", "network", "geography", "serviceDate", "serviceWindow"],
            "duplicatePolicy": "Block a candidate when the duplicate key already exists for the campaign cycle.",
            "missedWindowPolicy": "If forecastCloseAt has passed before forecast creation, mark the run missed and never backfill a forecast.",
            "manualStopPolicy": "Manual stop freezes future planning until an explicit resume creates a new cycle or run range.",
            "statusesHandled": RUN_STATUSES,
        },
        "materialization": build_materialization(
            planned_runs,
            target_count=target_run_count,
            full_materialization=full_materialization,
        ),
        "plannedRuns": planned_runs,
        "statusExamples": build_status_examples(),
        "progress": {
            "plannedRunCount": len(planned_runs),
            "forecastArtifactsCreated": 0,
            "resolvedComparableOutcomes": 0,
            "dueResolutionCount": 0,
            "blockedDuplicateCount": 0,
            "skippedCount": 0,
            "nextForecastRunId": first_run["runId"],
            "nextResolutionRunId": "none",
            "nextAction": "Use a future terminal campaign runner to create the first forecast before forecastCloseAt.",
        },
        "summary": {
            "campaignManifestImplemented": True,
            "dryRunPlannerImplemented": True,
            "fullMaterializationImplemented": True,
            "runnerImplemented": False,
            "plannedRunCount": len(planned_runs),
            "targetRunCount": target_run_count,
            "uniqueRunIdsMinted": True,
            "duplicatePreventionEnabled": True,
            "mutatesLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "qualityClaimAllowed": False,
            "recommendedNextMilestone": "Milestone 93: Terminal Campaign Runner",
        },
        "executionBoundary": {
            "readOnlyDryRun": True,
            "writesIgnoredLiveState": False,
            "createsForecastArtifacts": False,
            "executesForecastRunner": False,
            "startsScheduler": False,
            "fetchesLiveData": False,
            "resolvesOutcomes": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This manifest is a dry-run planning readback; it does not write campaign state during normal checks.",
            "The .ope/live/prediction-campaigns path is reserved for explicit local campaign state and remains git ignored.",
            "Planned IDs are placeholders for future runner-created artifacts, not committed forecast, resolution, or scoring records.",
            "Calibration and quality claims remain blocked until enough comparable resolved outcomes are appended through a checked ledger.",
        ],
    }
    return manifest


def plan_view(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "campaign": manifest["campaign"],
        "planningWindow": manifest["planningWindow"],
        "materialization": manifest["materialization"],
        "plannedRuns": manifest["plannedRuns"],
    }


def status_view(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "campaign": manifest["campaign"],
        "progress": manifest["progress"],
        "statusExamples": manifest["statusExamples"],
        "executionBoundary": manifest["executionBoundary"],
    }


def print_view(manifest: dict[str, Any], view: str) -> None:
    views = {
        "manifest": manifest,
        "plan": plan_view(manifest),
        "status": status_view(manifest),
        "summary": manifest["summary"],
        "boundary": manifest["executionBoundary"],
    }
    print(render_json(views[view]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(data, SCHEMA, OUTPUT_PATH, write=write, label="prediction campaign manifest", regen="python3 scripts/generate_prediction_campaign_manifest.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign manifest")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign manifest drift")
    parser.add_argument(
        "--case",
        choices=EXAMPLE_ORDER,
        default=DEFAULT_CASE,
        help="choose one repeating prediction setup example to expand",
    )
    parser.add_argument(
        "--plan-count",
        type=int,
        default=DEFAULT_PLAN_COUNT,
        help="number of candidate runs to include in the dry-run plan",
    )
    parser.add_argument(
        "--count",
        type=int,
        help="target run count for explicit full pilot materialization",
    )
    parser.add_argument(
        "--full-materialization",
        action="store_true",
        help="expand the complete local pilot plan instead of the bounded preview",
    )
    parser.add_argument(
        "--view",
        choices=["manifest", "plan", "status", "summary", "boundary"],
        default="manifest",
        help="print one prediction campaign view",
    )
    args = parser.parse_args()

    if args.plan_count < 1 or args.plan_count > MAX_PREVIEW_COUNT:
        raise SystemExit(f"--plan-count must be between 1 and {MAX_PREVIEW_COUNT}")
    target_count = args.count
    if target_count is not None and (target_count < 1 or target_count > MAX_FULL_MATERIALIZATION_COUNT):
        raise SystemExit(f"--count must be between 1 and {MAX_FULL_MATERIALIZATION_COUNT}")
    if args.full_materialization:
        full_target_count = target_count or target_count_for_case(
            find_case(build_repeating_prediction_setup(), args.case)
        )
        if full_target_count > MAX_FULL_MATERIALIZATION_COUNT:
            raise SystemExit(f"--full-materialization supports at most {MAX_FULL_MATERIALIZATION_COUNT} runs")
        target_count = full_target_count

    manifest = build_prediction_campaign_manifest(
        case_key=args.case,
        plan_count=args.plan_count,
        target_count=target_count,
        full_materialization=args.full_materialization,
    )
    if args.write or args.check:
        check_or_write(manifest, write=args.write)
        return
    errors = validate_record(manifest, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(manifest, args.view)


if __name__ == "__main__":
    main()
