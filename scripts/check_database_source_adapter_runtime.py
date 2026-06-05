#!/usr/bin/env python3
"""Check approved database source-adapter runtime boundaries."""

from __future__ import annotations

try:
    from generate_database_source_adapter_runtime import build_database_source_adapter_runtime
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("database source-adapter runtime generator is missing") from exc


REQUIRED_CASES = [
    "approved_fixture",
    "missing_approval",
    "missing_credential_reference",
    "unsafe_query_boundary",
    "oversized_result",
    "stale_source",
    "leakage_risk",
    "missing_outcome_source",
    "insufficient_comparable_history",
]

REQUIRED_REQUEST_FIELDS = {
    "sourceBindingId",
    "sourceRole",
    "approvedQueryManifestRef",
    "credentialRef",
    "rowLimit",
    "timeLimitSeconds",
    "freshnessWindowHours",
    "leakageWindow",
    "callerApprovalStatus",
}

REQUIRED_OUTPUT_FIELDS = {
    "sourceManifest",
    "fieldMapping",
    "provenanceSummary",
    "sourceQualitySignals",
    "mappingConfidenceSignals",
    "outcomeAvailabilityStatus",
    "queryBoundarySummary",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runtime = build_database_source_adapter_runtime()

    require(
        runtime["runtimeStatus"] == "approved_database_source_adapter_runtime_checked",
        "runtime status drifted",
    )
    require(runtime["runtimeScope"] == "bounded_caller_approved_database_adapter", "runtime scope drifted")
    require(runtime["normalChecksOffline"] is True, "normal checks must stay offline")
    require(runtime["sourceBindingId"] == "sourcebinding-115002", "database runtime should bind the checked seaport source binding")
    require(runtime["domainKey"] == "seaport-berth-availability", "database runtime domain drifted")

    cases = {item["caseName"]: item for item in runtime["runtimeCases"]}
    require(list(cases) == REQUIRED_CASES, "database runtime case order drifted")

    approved = cases["approved_fixture"]
    require(set(approved["runtimeRequest"]) == REQUIRED_REQUEST_FIELDS, "runtime request shape drifted")
    request = approved["runtimeRequest"]
    require(request["sourceBindingId"] == runtime["sourceBindingId"], "approved request should bind source binding")
    require(request["sourceRole"] == "vessel_schedule", "approved request should use the database schedule role")
    require(request["credentialRef"].startswith("credentialref-"), "approved request should use a credential reference")
    require(request["approvedQueryManifestRef"].startswith("querymanifest-"), "approved request should use a query manifest reference")
    require(request["rowLimit"] <= 500, "approved request row limit should stay bounded")
    require(request["timeLimitSeconds"] <= 30, "approved request time limit should stay bounded")
    require(request["freshnessWindowHours"] <= 24, "approved request freshness window should stay bounded")
    require(request["callerApprovalStatus"] == "approved", "approved request should require caller approval")
    require(request["leakageWindow"]["forecastCloseTime"], "approved request should declare forecast close time")
    require(request["leakageWindow"]["resolutionEvidenceAfter"], "approved request should declare resolution boundary")

    output = approved["sanitizedAdapterOutput"]
    require(set(output) == REQUIRED_OUTPUT_FIELDS, "sanitized adapter output shape drifted")
    require(output["provenanceSummary"]["rawRowsIncluded"] is False, "sanitized output must not include raw private rows")
    require(output["provenanceSummary"]["credentialValuesIncluded"] is False, "sanitized output must not include credential values")
    require(output["provenanceSummary"]["stackTraceIncluded"] is False, "sanitized output must not include stack traces")
    require(output["sourceQualitySignals"]["freshnessStatus"] == "pass", "approved source quality should pass freshness")
    require(output["mappingConfidenceSignals"]["mappingStatus"] == "confirmed", "approved mapping should be confirmed")
    require(output["outcomeAvailabilityStatus"]["status"] == "available_resolution_only", "approved output should bind resolution-only outcome")
    require(output["queryBoundarySummary"]["rawSqlIncluded"] is False, "query boundary must not expose raw SQL")
    require(output["queryBoundarySummary"]["unapprovedSchemaScan"] is False, "query boundary must not scan unapproved schemas")
    require(approved["sourceAdapterOutputCompatible"] is True, "approved output should be adapter-output compatible")
    require(approved["canEnterSourceAdapterIntake"] is True, "approved output should enter source-adapter intake")
    require(approved["databaseSpecificForecastPathCreated"] is False, "approved path must not create database-specific forecasts")
    require(approved["forecastArtifactsCreated"] is False, "approved path should not create forecast artifacts directly")

    blocked_expected = {
        "missing_approval": ("blocked_missing_approval", "confirm_caller_approval"),
        "missing_credential_reference": ("blocked_missing_credential_reference", "provide_credential_reference"),
        "unsafe_query_boundary": ("blocked_unsafe_query_boundary", "replace_query_manifest"),
        "oversized_result": ("blocked_oversized_result", "reduce_row_or_time_limits"),
        "stale_source": ("blocked_stale_source", "refresh_source_within_policy"),
        "leakage_risk": ("blocked_leakage_risk", "separate_resolution_evidence"),
        "missing_outcome_source": ("blocked_missing_outcome_source", "bind_resolution_only_outcome"),
        "insufficient_comparable_history": ("blocked_insufficient_comparable_history", "collect_more_history"),
    }
    for case_name, (status, next_action) in blocked_expected.items():
        case = cases[case_name]
        require(case["caseStatus"] == status, f"{case_name} status drifted")
        require(case["nextAction"] == next_action, f"{case_name} next action drifted")
        require(case["canEnterSourceAdapterIntake"] is False, f"{case_name} should stop before source-adapter intake")
        require(case["forecastArtifactsCreated"] is False, f"{case_name} must not create forecast artifacts")
        require(case["rawPrivateRowsStored"] is False, f"{case_name} must not store raw private rows")
        require(case["credentialValuesStored"] is False, f"{case_name} must not store credentials")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case_name} should keep diagnostics sanitized")

    routing = runtime["routing"]
    require(routing["acceptedOutputRoutesToSourceAdapterIntake"] is True, "accepted output should route to source-adapter intake")
    require(routing["routesToSourceIntake"] is True, "accepted output should route to source intake")
    require(routing["routesToSourceHandoff"] is True, "accepted output should route to source handoff")
    require(routing["routesToSetupBenchmark"] is True, "accepted output should route to setup benchmark")
    require(routing["routesToSetupMethodDecision"] is True, "accepted output should route to setup method decision")
    require(routing["routesToForecastExecutionGate"] is True, "accepted output should route to forecast execution gate")
    require(routing["databaseSpecificForecastPathCreated"] is False, "database runtime must not create a forecast path")

    readbacks = {item["readbackSurface"]: item for item in runtime["readbacks"]}
    require(set(readbacks) == {"cli", "internal_api", "agent_call"}, "database runtime readback coverage drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py database-source-adapter-runtime", "CLI readback drifted")
    require(readbacks["internal_api"]["operationName"] == "database_source_adapter_status", "internal API readback drifted")
    require(
        readbacks["agent_call"]["command"]
        == "python3 scripts/ope.py agent-call --operation database_source_adapter_runtime_status",
        "agent-call readback drifted",
    )
    for readback in readbacks.values():
        require(readback["mutatesState"] is False, "readbacks should not mutate state")
        require(readback["requiresCredentialValues"] is False, "readbacks should not require credential values")

    boundary = runtime["executionBoundary"]
    for key in [
        "productionDatabaseConnectionOpened",
        "normalChecksConnectToDatabase",
        "credentialValuesStored",
        "rawSqlWithSecretsAccepted",
        "rawPrivateRowsStored",
        "stackTracesExposed",
        "unapprovedSchemaScansAllowed",
        "arbitraryDatabaseAccessAllowed",
        "forecastArtifactsCreated",
        "scoringRecordsCreated",
        "hostedRuntimeRequired",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = runtime["summary"]
    require(summary["caseCount"] == len(REQUIRED_CASES), "case count drifted")
    require(summary["blockedCaseCount"] == len(REQUIRED_CASES) - 1, "blocked count drifted")
    require(summary["approvedExecutionPathCount"] == 1, "approved path count drifted")
    require(summary["sourceAdapterOutputCompatibleCount"] == 1, "adapter-compatible output count drifted")
    require(summary["forecastArtifactsCreated"] is False, "summary should not create forecast artifacts")
    require(summary["credentialsStored"] is False, "summary should not store credentials")

    print("checked database source adapter runtime")


if __name__ == "__main__":
    main()
