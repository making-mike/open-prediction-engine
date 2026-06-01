#!/usr/bin/env python3
"""Generate or check a prediction campaign resolution-attempt readback."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import compact_json, render_json, validate_and_emit
from prediction_campaign_resolution_runtime import (
    PredictionCampaignResolutionError,
    execute_local_resolution_write,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-resolution-attempt"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-resolution-attempt.generated.json"
SCHEMA = SPEC / "prediction-campaign-resolution-attempt.schema.json"
GENERATED_AT = "2026-05-31T00:30:00Z"
DEFAULT_NOW = "2026-06-11T07:15:00Z"
DEFAULT_CASE = "due_open"
TERMINAL_RUN_STATUSES = {"resolved", "ambiguous", "annulled"}
EXCLUDED_RUN_STATUSES = {"skipped", "missed", "canceled", "failed", "manually_stopped"}
DUPLICATE_RUN_STATUS = "blocked_duplicate"
ATTEMPT_CASES: dict[str, dict[str, Any]] = {
    "due_open": {
        "description": "Default checked due unresolved campaign run.",
        "runStatus": None,
        "questionStatus": "open",
    },
    "already_resolved": {
        "description": "Resolved campaign run must not be resolved or scored again.",
        "runStatus": "resolved",
        "questionStatus": "resolved",
    },
    "ambiguous": {
        "description": "Ambiguous campaign run is terminal until corrected and must not be scored as comparable evidence.",
        "runStatus": "ambiguous",
        "questionStatus": "ambiguous",
    },
    "annulled": {
        "description": "Annulled campaign run is terminal and excluded from resolution, scoring, and append.",
        "runStatus": "annulled",
        "questionStatus": "annulled",
    },
    "missed": {
        "description": "Missed forecast window is excluded and must not be backfilled, resolved, scored, or appended.",
        "runStatus": "missed",
        "questionStatus": "closed",
    },
    "blocked_duplicate": {
        "description": "Duplicate campaign key blocks a second forecast, resolution, scoring, and append.",
        "runStatus": "blocked_duplicate",
        "questionStatus": "open",
    },
}


def id_suffix(run_id: str) -> str:
    return run_id.rsplit("-", 1)[-1]


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def find_run(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in manifest["plannedRuns"]:
        if run["runId"] == run_id:
            return run
    raise SystemExit(f"prediction campaign manifest has no planned run {run_id}")


def attempt_guard(
    index: int,
    *,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "guardId": f"campaignresolutionguard-{index:03d}",
        "guardStatus": status,
        "requiredBeforeResolve": required,
        "blocksResolve": blocks,
        "message": message,
    }


def build_attempt_guards(
    *,
    run: dict[str, Any],
    artifact: dict[str, Any],
    run_status: str,
    due: bool,
    execute_resolvers: bool,
    outcome_source_declared: bool,
    missing_outcome: bool,
) -> list[dict[str, Any]]:
    resolver_ready = outcome_source_declared or missing_outcome
    return [
        attempt_guard(
            1,
            status="pass",
            required=True,
            blocks=False,
            message=f"Campaign run {run['runId']} is bound to forecast {artifact['forecastId']}.",
        ),
        attempt_guard(
            2,
            status="block" if terminal_or_excluded(run_status) or duplicate_status(run_status) else "pass",
            required=True,
            blocks=terminal_or_excluded(run_status) or duplicate_status(run_status),
            message="Already terminal, excluded, or duplicate campaign runs cannot be resolved or scored again.",
        ),
        attempt_guard(
            3,
            status="pass" if artifact["questionStatus"] == "open" else "block",
            required=True,
            blocks=artifact["questionStatus"] != "open",
            message="Only open campaign forecasts can enter the resolution attempt path.",
        ),
        attempt_guard(
            4,
            status="pass" if due else "block",
            required=True,
            blocks=not due,
            message=f"Resolution may start only at or after {run['resolutionEligibleAt']}.",
        ),
        attempt_guard(
            5,
            status="pass" if execute_resolvers else "warn",
            required=False,
            blocks=False,
            message="--execute-resolvers is required before any resolver attempt can move beyond dry-run readback.",
        ),
        attempt_guard(
            6,
            status=(
                "block"
                if execute_resolvers
                and due
                and not resolver_ready
                and not terminal_or_excluded(run_status)
                and not duplicate_status(run_status)
                else "pass"
                if execute_resolvers and due and resolver_ready
                else "warn"
            ),
            required=True,
            blocks=execute_resolvers
            and due
            and not resolver_ready
            and not terminal_or_excluded(run_status)
            and not duplicate_status(run_status),
            message=(
                "A declared outcome source or explicit missing-outcome exclusion is available; add --write-local to mutate ignored local state."
                if resolver_ready
                else "Campaign outcome source execution requires --outcome-csv or --missing-outcome before local writes."
            ),
        ),
    ]


def terminal_or_excluded(run_status: str) -> bool:
    return run_status in TERMINAL_RUN_STATUSES or run_status in EXCLUDED_RUN_STATUSES


def duplicate_status(run_status: str) -> bool:
    return run_status == DUPLICATE_RUN_STATUS


def attempt_status(
    *,
    due: bool,
    open_question: bool,
    run_status: str,
    execute_resolvers: bool,
    outcome_source_declared: bool,
    missing_outcome: bool,
) -> str:
    if duplicate_status(run_status):
        return "blocked_duplicate_run"
    if run_status in EXCLUDED_RUN_STATUSES:
        return "blocked_excluded_run"
    if run_status in TERMINAL_RUN_STATUSES:
        return "blocked_already_terminal"
    if not open_question:
        return "blocked_already_terminal"
    if not due:
        return "not_due_wait"
    if execute_resolvers:
        if outcome_source_declared or missing_outcome:
            return "dry_run_execute_ready"
        return "blocked_missing_outcome_source"
    return "dry_run_due_ready"


def attempt_result(*, status: str) -> dict[str, Any]:
    if status == "dry_run_due_ready":
        return {
            "resultStatus": "dry_run_ready",
            "failureCategory": "none",
            "retryable": True,
            "retryAfter": "with_explicit_execute_resolvers_and_checked_outcome_source",
            "sanitizedDiagnostics": "Due campaign run is ready for an explicit resolver attempt.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    if status == "dry_run_execute_ready":
        return {
            "resultStatus": "dry_run_ready",
            "failureCategory": "none",
            "retryable": True,
            "retryAfter": "with_explicit_write_local",
            "sanitizedDiagnostics": "Outcome source inputs are declared; explicit --write-local is required before mutation.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    if status == "not_due_wait":
        return {
            "resultStatus": "not_run",
            "failureCategory": "not_due",
            "retryable": True,
            "retryAfter": "at_resolution_eligible_time",
            "sanitizedDiagnostics": "Campaign run has not reached its resolution window.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    if status == "blocked_already_terminal":
        return {
            "resultStatus": "blocked",
            "failureCategory": "already_terminal",
            "retryable": False,
            "retryAfter": "never_without_new_run",
            "sanitizedDiagnostics": "Campaign forecast is already terminal and must not be resolved or scored again.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    if status == "blocked_excluded_run":
        return {
            "resultStatus": "blocked",
            "failureCategory": "excluded_run",
            "retryable": False,
            "retryAfter": "never_for_excluded_run",
            "sanitizedDiagnostics": "Campaign run is excluded and must not be backfilled, resolved, scored, or appended.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    if status == "blocked_duplicate_run":
        return {
            "resultStatus": "blocked",
            "failureCategory": "duplicate_blocked",
            "retryable": False,
            "retryAfter": "never_for_duplicate_key",
            "sanitizedDiagnostics": "Campaign duplicate-key policy blocks duplicate resolution and duplicate scoring.",
            "resolutionArtifactsCreated": False,
            "scoringRecordsCreated": False,
        }
    return {
        "resultStatus": "blocked",
        "failureCategory": "source_unavailable",
        "retryable": True,
        "retryAfter": "after_checked_campaign_outcome_source_is_available",
        "sanitizedDiagnostics": "Explicit resolver execution was requested, but no checked campaign outcome source is available.",
        "resolutionArtifactsCreated": False,
        "scoringRecordsCreated": False,
    }


def duplicate_safety() -> dict[str, Any]:
    return {
        "terminalRunStatuses": sorted(TERMINAL_RUN_STATUSES),
        "excludedRunStatuses": sorted(EXCLUDED_RUN_STATUSES),
        "duplicateRunStatus": DUPLICATE_RUN_STATUS,
        "terminalResolutionBlocked": True,
        "terminalScoringBlocked": True,
        "excludedResolutionBlocked": True,
        "duplicateResolutionBlocked": True,
        "duplicateScoringBlocked": True,
        "priorEvidenceOverwriteAllowed": False,
    }


def build_prediction_campaign_resolution_attempt(
    *,
    run_id: str = "predictionrun-1301",
    now: str = DEFAULT_NOW,
    execute_resolvers: bool = False,
    outcome_csv: str | None = None,
    missing_outcome: bool = False,
    case: str = DEFAULT_CASE,
) -> dict[str, Any]:
    if case not in ATTEMPT_CASES:
        raise SystemExit(f"unknown prediction campaign resolution attempt case: {case}")
    manifest = build_prediction_campaign_manifest()
    write_plan = build_prediction_campaign_forecast_write(run_id=run_id if run_id != "predictionrun-1301" else None)
    records = build_prediction_campaign_forecast_artifact(run_id=run_id if run_id != "predictionrun-1301" else None)
    run = find_run(manifest, run_id)
    artifact = records["artifact"]
    case_def = ATTEMPT_CASES[case]
    run_status = case_def["runStatus"] or ("due_resolution" if parse_utc(now) >= parse_utc(run["resolutionEligibleAt"]) else "waiting_resolution")
    artifact = dict(artifact)
    artifact["questionStatus"] = case_def["questionStatus"]
    due = parse_utc(now) >= parse_utc(run["resolutionEligibleAt"])
    status = attempt_status(
        due=due,
        open_question=artifact["questionStatus"] == "open",
        run_status=run_status,
        execute_resolvers=execute_resolvers,
        outcome_source_declared=outcome_csv is not None,
        missing_outcome=missing_outcome,
    )
    result = attempt_result(status=status)
    suffix = id_suffix(run_id)
    return {
        "predictionCampaignResolutionAttemptId": f"predictioncampaignresolutionattempt-{suffix}",
        "generatedAt": GENERATED_AT,
        "attemptCase": {
            "caseKey": case,
            "description": case_def["description"],
            "simulatedReadback": case != DEFAULT_CASE,
        },
        "attemptStatus": status,
        "executionMode": "execute_requested" if execute_resolvers else "dry_run",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": write_plan["bindings"]["predictionCampaignRunnerId"],
            "predictionCampaignForecastWriteId": write_plan["predictionCampaignForecastWriteId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": run["runId"],
            "questionId": artifact["questionId"],
            "forecastId": artifact["forecastId"],
            "resolutionId": run["resolutionId"],
            "scoringReportId": run["scoringReportId"],
            "sourcePolicyId": run["sourcePolicyId"],
        },
        "resolverTarget": {
            "runStatePath": write_plan["targetState"]["runStatePath"],
            "forecastArtifactPath": write_plan["targetState"]["forecastArtifactPath"],
            "resolutionEligibleAt": run["resolutionEligibleAt"],
            "now": now,
            "due": due,
            "runStatus": run_status,
            "questionStatus": artifact["questionStatus"],
            "serviceDate": run["serviceDate"],
            "serviceWindow": run["serviceWindow"],
        },
        "attemptGuards": build_attempt_guards(
            run=run,
            artifact=artifact,
            run_status=run_status,
            due=due,
            execute_resolvers=execute_resolvers,
            outcome_source_declared=outcome_csv is not None,
            missing_outcome=missing_outcome,
        ),
        "attemptResult": result,
        "duplicateSafety": duplicate_safety(),
        "sourceFetchMetadata": {
            "fetchAttempted": False,
            "sourceProvider": (
                "local_transit_outcome_csv"
                if outcome_csv
                else "missing_outcome_exclusion"
                if missing_outcome
                else "none"
            ),
            "sourceRole": "resolution_outcome",
            "liveNetworkUsed": False,
            "localOutcomePath": outcome_csv or "none",
            "sanitizedOnly": True,
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign resolve",
            "acceptedFlags": [
                "--run-id",
                "--now",
                "--attempt-case",
                "--execute-resolvers",
                "--write-local",
                "--outcome-csv",
                "--missing-outcome",
                "--output-format",
                "--view",
            ],
            "defaultMode": "checked_resolution_attempt_readback",
            "explicitResolverFlagRequired": True,
            "normalChecksExecuteResolver": False,
        },
        "summary": {
            "resolutionAttemptReadbackImplemented": True,
            "dueRunSelected": due,
            "resolverExecutionRequested": execute_resolvers,
            "resolverExecutionImplemented": True,
            "duplicateSafetyImplemented": True,
            "resolutionArtifactsCreated": result["resolutionArtifactsCreated"],
            "scoringRecordsCreated": result["scoringRecordsCreated"],
            "retryable": result["retryable"],
            "recommendedNextAction": result["retryAfter"],
        },
        "executionBoundary": {
            "normalChecksUseLiveNetwork": False,
            "requiresExplicitResolverFlag": True,
            "readsIgnoredLiveState": False,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This readback records a campaign resolver attempt decision; it does not resolve or score the forecast.",
            "Effectful resolver execution requires explicit --execute-resolvers plus --write-local and an outcome source or missing-outcome exclusion.",
            "Normal checks do not read ignored local campaign state, fetch live data, write campaign state, or append corpus evidence.",
        ],
    }


def print_view(attempt: dict[str, Any], output_format: str | None, view: str) -> None:
    views = {
        "attempt": attempt,
        "target": attempt["resolverTarget"],
        "guards": attempt["attemptGuards"],
        "result": attempt["attemptResult"],
        "summary": attempt["summary"],
        "boundary": attempt["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        print(
            f"{attempt['bindings']['runId']} {attempt['attemptStatus']} "
            f"retryable={attempt['attemptResult']['retryable']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign resolution attempt",
        regen="python3 scripts/generate_prediction_campaign_resolution_attempt.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign resolution attempt")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign resolution attempt drift")
    parser.add_argument("--run-id", default="predictionrun-1301", help="campaign run ID to inspect")
    parser.add_argument("--now", default=DEFAULT_NOW, help="UTC resolver-attempt clock")
    parser.add_argument(
        "--case",
        choices=sorted(ATTEMPT_CASES),
        default=DEFAULT_CASE,
        help="checked resolution-attempt case to inspect",
    )
    parser.add_argument("--execute-resolvers", action="store_true", help="request explicit campaign resolver execution")
    parser.add_argument(
        "--write-local",
        action="store_true",
        help="explicitly write campaign resolution and scoring records into ignored local state",
    )
    parser.add_argument("--outcome-csv", help="approved local transit outcome CSV/JSON for resolution")
    parser.add_argument(
        "--missing-outcome",
        action="store_true",
        help="write an explicit missing-outcome exclusion instead of a comparable outcome",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["attempt", "target", "guards", "result", "summary", "boundary"],
        default="attempt",
        help="print one campaign resolution-attempt view",
    )
    args = parser.parse_args()

    if (
        (args.write or args.check)
        and (
            args.run_id != "predictionrun-1301"
            or args.now != DEFAULT_NOW
            or args.execute_resolvers
            or args.outcome_csv
            or args.missing_outcome
            or args.case != DEFAULT_CASE
        )
    ):
        raise SystemExit("custom resolution attempt inputs cannot be combined with --write or --check")
    if args.write_local:
        if args.write or args.check:
            raise SystemExit("--write-local cannot be combined with --write or --check")
        if not args.execute_resolvers:
            raise SystemExit("--write-local requires --execute-resolvers")
        if args.case != DEFAULT_CASE:
            raise SystemExit("--write-local cannot be combined with simulated --case inputs")
        try:
            result = execute_local_resolution_write(
                run_id=args.run_id,
                now=args.now,
                outcome_csv=args.outcome_csv,
                missing_outcome=args.missing_outcome,
            )
        except PredictionCampaignResolutionError as exc:
            raise SystemExit(str(exc)) from exc
        if args.output_format == "human":
            print(
                f"{result['bindings']['runId']} {result['resolutionWriteStatus']} "
                f"scoreStatus={result['outcomeSummary']['scoreStatus']} "
                f"newFiles={result['summary']['newFileWriteCount']}"
            )
            return
        if args.output_format == "jsonl":
            print(compact_json(result), end="")
            return
        print(render_json(result), end="")
        return
    attempt = build_prediction_campaign_resolution_attempt(
        run_id=args.run_id,
        now=args.now,
        execute_resolvers=args.execute_resolvers,
        outcome_csv=args.outcome_csv,
        missing_outcome=args.missing_outcome,
        case=args.case,
    )
    errors = validate_record(attempt, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    if args.write or args.check:
        check_or_write(attempt, write=args.write)
        return
    print_view(attempt, args.output_format, args.view)


if __name__ == "__main__":
    main()
