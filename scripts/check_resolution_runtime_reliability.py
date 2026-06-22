#!/usr/bin/env python3
"""Check the resolution runtime reliability read model."""

from __future__ import annotations

from generate_resolution_runtime_reliability import build_reliability


REQUIRED_FAILURE_CLASSES = {
    "source_availability",
    "empty_sources",
    "decode_failures",
    "schedule_join_failures",
    "coverage_gaps",
    "late_capture_window",
    "resolver_failures",
    "stale_state",
    "invalid_state",
    "network_timeouts",
    "rate_limits",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    reliability = build_reliability()
    failures = reliability["failureTaxonomy"]
    failure_classes = {item["failureClass"] for item in failures}
    require(failure_classes == REQUIRED_FAILURE_CLASSES, "failure taxonomy should cover the required runtime classes")
    for item in failures:
        require("retryable" in item and isinstance(item["retryable"], bool), "failure retryability must be explicit")
        require("retryAfter" in item, "failure retry-after must be explicit")
        require(item["nextAction"], "failure next action must be explicit")
        require(item["sanitizedDiagnostic"], "failure diagnostic must be present")
        require(item["safeSignals"], "failure safe signals must be present")
        require(item["rawDiagnosticsExposed"] is False, "failure must not expose raw diagnostics")
        require(item["stackTraceExposed"] is False, "failure must not expose stack traces")
        require(item["absolutePathsExposed"] is False, "failure must not expose absolute paths")
        claims = item["claimBoundary"]
        require(not any(claims.values()), "failure rows must not create artifacts or claims")

    retryable_failures = {item["failureClass"] for item in failures if item["retryable"]}
    require(
        {"source_availability", "network_timeouts", "rate_limits", "resolver_failures"}.issubset(retryable_failures),
        "transient failures should be retryable",
    )
    non_retryable_failures = {item["failureClass"] for item in failures if not item["retryable"]}
    require(
        {"schedule_join_failures", "coverage_gaps", "late_capture_window", "invalid_state"}.issubset(non_retryable_failures),
        "structural failures should not be automatic retries",
    )

    ledger = reliability["provenanceLedger"]
    action_types = {item["actionType"] for item in ledger}
    require(
        {"forecast_live_capture", "forward_forecast_run", "resolution_job_scan", "scheduler_tick", "resolver_attempt"}.issubset(action_types),
        "provenance ledger should cover forecast, scheduler, scan, and resolver actions",
    )
    require(any(item["forecastTimeEvidence"] for item in ledger), "ledger should include forecast-time provenance")
    require(any(item["resolutionOnlyEvidence"] for item in ledger), "ledger should include resolution-only provenance")
    for item in ledger:
        require(not (item["forecastTimeEvidence"] and item["resolutionOnlyEvidence"]), "ledger classification cannot be both forecast-time and resolution-only")
        require(item["command"].startswith("python3 scripts/ope.py "), "ledger commands should use the local CLI")
        require("timestamp" in item, "ledger actions must include timestamps")
        require(item["sourceProvider"], "ledger actions must include source provider")
        require(item["sourceRole"], "ledger actions must include source role")
        require(item["evidenceClassification"], "ledger actions must include evidence classification")
        require(item["artifactHashStatus"] in {"paths_only", "not_applicable"}, "ledger should declare artifact hash status")
        diagnostics = item["diagnostics"]
        require(diagnostics["rawDiagnosticsExposed"] is False, "ledger diagnostics must not expose raw details")
        require(diagnostics["stackTraceExposed"] is False, "ledger diagnostics must not expose stack traces")
        if item["sourceRole"] == "resolution_outcome":
            require(item["resolutionOnlyEvidence"] is True, "resolution outcomes should be resolution-only evidence")
            require(item["forecastTimeEvidence"] is False, "resolution outcomes must not be forecast-time evidence")

    boundary = reliability["executionBoundary"]
    require(boundary["readModelDoesNotExecute"] is True, "reliability record should be a non-executing read model")
    for flag in [
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
    ]:
        require(boundary[flag] is False, f"execution boundary should keep {flag} false")

    source_boundary = reliability["sourcePolicyBoundary"]
    require(source_boundary["liveCapturesAreLocalOnly"] is True, "live captures should remain local")
    require(source_boundary["liveCaptureRequiresExplicitFlag"] is True, "live captures should require explicit flags")
    require(source_boundary["liveCaptureFilesCommitted"] is False, "live captures should not be committed fixtures")
    require(source_boundary["outcomeDataIsResolutionOnly"] is True, "outcome data should be resolution-only")
    require(
        source_boundary["resolutionOutcomeMayEnterForecastProvenance"] is False,
        "resolution outcomes must not enter forecast-time provenance",
    )
    print("checked resolution runtime reliability")


if __name__ == "__main__":
    main()
