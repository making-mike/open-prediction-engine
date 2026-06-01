#!/usr/bin/env python3
"""Generate a checked resolution runtime reliability read model."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "resolution-runtime-reliability"
OUTPUT_PATH = GENERATED / "resolution-runtime-reliability.generated.json"
SCHEMA = SPEC / "resolution-runtime-reliability.schema.json"
GENERATED_AT = "2026-05-27T12:30:00Z"


class ResolutionRuntimeReliabilityError(Exception):
    pass


def claim_boundary() -> dict[str, bool]:
    return {
        "createsForecastArtifacts": False,
        "createsResolutionArtifacts": False,
        "createsScoringRecords": False,
        "calibrationClaimAllowed": False,
    }


def failure(
    failure_class: str,
    category: str,
    stages: list[str],
    retryable: bool,
    retry_after: str | None,
    next_action: str,
    diagnostic: str,
    signals: list[str],
) -> dict[str, Any]:
    return {
        "failureClass": failure_class,
        "failureCategory": category,
        "runtimeStages": stages,
        "retryable": retryable,
        "retryAfter": retry_after,
        "nextAction": next_action,
        "sanitizedDiagnostic": diagnostic,
        "safeSignals": signals,
        "rawDiagnosticsExposed": False,
        "stackTraceExposed": False,
        "absolutePathsExposed": False,
        "claimBoundary": claim_boundary(),
    }


def build_failure_taxonomy() -> list[dict[str, Any]]:
    return [
        failure(
            "source_availability",
            "source",
            ["forecast_live_capture", "resolution_outcome_capture"],
            True,
            "PT10M",
            "retry_after_backoff",
            "The declared source was unavailable or returned no usable response.",
            ["source_unavailable", "no_successful_connector_result"],
        ),
        failure(
            "empty_sources",
            "source",
            ["forecast_live_capture", "resolution_outcome_capture"],
            True,
            "PT30M",
            "provide_fresh_source",
            "The source was readable but did not contain rows usable for the declared window.",
            ["empty_result_set", "no_window_rows"],
        ),
        failure(
            "decode_failures",
            "decode",
            ["forecast_live_capture", "resolution_outcome_capture"],
            True,
            "PT10M",
            "retry_after_backoff",
            "The local source payload could not be decoded into the expected checked shape.",
            ["decode_error", "unsupported_payload_shape"],
        ),
        failure(
            "schedule_join_failures",
            "join",
            ["forecast_live_capture", "resolver_attempt"],
            False,
            None,
            "rerun_schedule_join",
            "Transit rows could not be joined to the declared schedule reference.",
            ["missing_trip_id", "static_schedule_join_failed"],
        ),
        failure(
            "coverage_gaps",
            "coverage",
            ["forward_forecast_run", "resolver_attempt"],
            False,
            None,
            "stop_and_request_confirmation",
            "The resolved or forecast-time sample did not meet the declared comparable-window coverage.",
            ["below_minimum_rows", "non_comparable_window"],
        ),
        failure(
            "resolver_failures",
            "resolver",
            ["resolver_attempt"],
            True,
            "PT5M",
            "retry_after_backoff",
            "The checked resolver attempt failed before producing resolution or scoring artifacts.",
            ["resolver_exit_nonzero", "resolver_output_missing"],
        ),
        failure(
            "stale_state",
            "state",
            ["resolution_job_scan", "scheduler_tick"],
            True,
            "PT60M",
            "wait_for_next_tick",
            "Saved forward-run state is older than the accepted freshness window for the next action.",
            ["state_generated_before_current_policy", "freshness_window_expired"],
        ),
        failure(
            "invalid_state",
            "state",
            ["resolution_job_scan", "scheduler_tick"],
            False,
            None,
            "inspect_invalid_state",
            "Saved forward-run state is missing required forecast or resolution metadata.",
            ["missing_forecast_id", "missing_resolve_at"],
        ),
        failure(
            "network_timeouts",
            "network",
            ["forecast_live_capture", "resolution_outcome_capture"],
            True,
            "PT15M",
            "retry_after_backoff",
            "The approved live source request timed out without exposing raw transport details.",
            ["request_timeout", "no_response_before_deadline"],
        ),
        failure(
            "rate_limits",
            "policy",
            ["forecast_live_capture", "resolution_outcome_capture"],
            True,
            "PT60M",
            "retry_after_backoff",
            "The approved source indicated rate limiting or quota exhaustion.",
            ["rate_limited", "quota_exhausted"],
        ),
    ]


def diagnostics(status: str = "ok") -> dict[str, Any]:
    return {
        "diagnosticLevel": "sanitized_summary",
        "status": status,
        "rawDiagnosticsExposed": False,
        "stackTraceExposed": False,
    }


def provenance(
    index: int,
    action_type: str,
    command: str,
    source_provider: str,
    source_role: str,
    evidence_classification: str,
    forecast_time: bool,
    resolution_only: bool,
    artifact_paths: list[str],
    status: str = "ok",
) -> dict[str, Any]:
    return {
        "runtimeActionId": f"resolutionruntimeaction-{index:03d}",
        "actionType": action_type,
        "command": command,
        "timestamp": GENERATED_AT,
        "sourceProvider": source_provider,
        "sourceRole": source_role,
        "evidenceClassification": evidence_classification,
        "forecastTimeEvidence": forecast_time,
        "resolutionOnlyEvidence": resolution_only,
        "allowedArtifactPaths": artifact_paths,
        "artifactHashStatus": "paths_only" if artifact_paths else "not_applicable",
        "diagnostics": diagnostics(status),
    }


def build_provenance_ledger() -> list[dict[str, Any]]:
    return [
        provenance(
            1,
            "forecast_live_capture",
            "python3 scripts/ope.py transit-api-connector --schedule-join",
            "hsl_gtfs_rt",
            "forecast_time_transit_feed",
            "forecast_time",
            True,
            False,
            ["spec/fixtures/generated/transit-api-connector/hsl-transit-api-connector.generated.json"],
        ),
        provenance(
            2,
            "forward_forecast_run",
            "python3 scripts/ope.py transit-delay-forward-run",
            "fixture_replay",
            "forecast_time_weather",
            "forecast_time",
            True,
            False,
            ["spec/fixtures/generated/transit-delay-forward-run/weather-transit-delays-forward-run.generated.json"],
        ),
        provenance(
            3,
            "resolution_job_scan",
            "python3 scripts/ope.py resolution-jobs",
            "fixture_replay",
            "forward_run_state",
            "runtime_control",
            False,
            False,
            ["spec/fixtures/generated/resolution-jobs/resolution-jobs.generated.json"],
        ),
        provenance(
            4,
            "scheduler_tick",
            "python3 scripts/ope.py resolution-scheduler",
            "local_scheduler",
            "scheduler_control",
            "runtime_control",
            False,
            False,
            ["spec/fixtures/generated/resolution-scheduler/resolution-scheduler-run.generated.json"],
        ),
        provenance(
            5,
            "resolver_attempt",
            "python3 scripts/ope.py resolve-due-forward-runs",
            "fixture_replay",
            "resolution_outcome",
            "resolution_only",
            False,
            True,
            ["spec/fixtures/generated/transit-forward-run-resolver/resolve-due-forward-runs.generated.json"],
        ),
        provenance(
            6,
            "shutdown_readback",
            "python3 scripts/ope.py agent-call --operation resolution_scheduler_status",
            "local_scheduler",
            "runtime_log",
            "runtime_control",
            False,
            False,
            [],
            "not_run",
        ),
    ]


def build_reliability() -> dict[str, Any]:
    reliability = {
        "resolutionRuntimeReliabilityId": "resolutionruntimereliability-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "reliabilityMode": "checked_fixture_read_model",
        "runtimeScope": "resolution_runtime_reliability",
        "failureTaxonomy": build_failure_taxonomy(),
        "provenanceLedger": build_provenance_ledger(),
        "executionBoundary": {
            "readModelDoesNotExecute": True,
            "normalChecksUseLiveNetwork": False,
            "usesPostCloseOutcomeAsForecastEvidence": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "createsHostedRuntime": False,
            "createsOsScheduler": False,
            "createsCalibrationClaims": False,
        },
        "sourcePolicyBoundary": {
            "liveCapturesAreLocalOnly": True,
            "liveCaptureRequiresExplicitFlag": True,
            "liveCaptureWorkspace": ".ope/live/",
            "liveCaptureFilesCommitted": False,
            "outcomeDataIsResolutionOnly": True,
            "resolutionOutcomeMayEnterForecastProvenance": False,
            "sourcePolicyRequiredBeforeHostedRuntime": True,
        },
        "warnings": [
            "This reliability record is a checked read model; it does not execute scheduler or resolver commands.",
            "Outcome data is resolution-only and must not be reused as forecast-time provenance.",
            "Live captures remain ignored local artifacts under .ope/live/ and require explicit live flags.",
            "Failure diagnostics are sanitized categories and safe signals, not raw source contents or stack traces.",
            "Calibration claims remain blocked until enough comparable resolved windows exist.",
        ],
    }
    validate_reliability(reliability)
    return reliability


def validate_reliability(reliability: dict[str, Any]) -> None:
    errors = validate_record(reliability, SCHEMA)
    if errors:
        raise ResolutionRuntimeReliabilityError(f"resolution runtime reliability schema validation failed: {errors[0]}")
    boundary = reliability["executionBoundary"]
    forbidden_boundary_flags = [
        "normalChecksUseLiveNetwork",
        "usesPostCloseOutcomeAsForecastEvidence",
        "createsForecastArtifacts",
        "createsResolutionArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
        "createsOsScheduler",
        "createsCalibrationClaims",
    ]
    if not boundary["readModelDoesNotExecute"]:
        raise ResolutionRuntimeReliabilityError("reliability read model must not execute")
    for flag in forbidden_boundary_flags:
        if boundary[flag]:
            raise ResolutionRuntimeReliabilityError(f"reliability read model must keep {flag} false")
    if reliability["sourcePolicyBoundary"]["resolutionOutcomeMayEnterForecastProvenance"]:
        raise ResolutionRuntimeReliabilityError("resolution outcomes must not enter forecast-time provenance")
    for item in reliability["failureTaxonomy"]:
        if item["rawDiagnosticsExposed"] or item["stackTraceExposed"] or item["absolutePathsExposed"]:
            raise ResolutionRuntimeReliabilityError("failure diagnostics must be sanitized")
        claims = item["claimBoundary"]
        if any(claims.values()):
            raise ResolutionRuntimeReliabilityError("failure taxonomy must not create artifacts or claims")
    for item in reliability["provenanceLedger"]:
        if item["forecastTimeEvidence"] and item["resolutionOnlyEvidence"]:
            raise ResolutionRuntimeReliabilityError("provenance cannot be both forecast-time and resolution-only")
        if item["sourceRole"] == "resolution_outcome" and item["forecastTimeEvidence"]:
            raise ResolutionRuntimeReliabilityError("resolution outcomes must not be forecast-time evidence")
        diagnostics_record = item["diagnostics"]
        if diagnostics_record["rawDiagnosticsExposed"] or diagnostics_record["stackTraceExposed"]:
            raise ResolutionRuntimeReliabilityError("provenance diagnostics must be sanitized")


def write_reliability(reliability: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, reliability, label="resolution runtime reliability", regen="python3 scripts/generate_resolution_runtime_reliability.py --write")


def check_reliability(reliability: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, reliability, label="resolution runtime reliability", regen="python3 scripts/generate_resolution_runtime_reliability.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        reliability = build_reliability()
        if args.write:
            write_reliability(reliability)
        elif args.check:
            check_reliability(reliability)
        else:
            sys.stdout.write(render_json(reliability))
    except ResolutionRuntimeReliabilityError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
