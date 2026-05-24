#!/usr/bin/env python3
"""Check compact private setup adapter conformance summary boundaries."""

from __future__ import annotations

from generate_private_setup_adapter_conformance_summary import (
    build_summary,
    validate_against_matrix,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    summary = build_summary()
    validate_against_matrix(summary)

    totals = summary["caseTotals"]
    require(totals["totalCases"] == 31, "summary should cover 31 matrix cases")
    require(totals["successCases"] == 30, "summary should cover 30 success cases")
    require(totals["errorCases"] == 1, "summary should cover one sanitized error case")
    require(totals["artifactGeneratingCases"] == 1, "summary should expose one artifact-generating case")
    require(totals["blockedForecastExecutionCases"] == 6, "summary should expose six blocked forecast-execution cases")

    phase_counts = {item["phase"]: item["caseCount"] for item in summary["phaseSummaries"]}
    require(phase_counts == {
        "source_builder": 6,
        "source_handoff": 7,
        "method_gate": 7,
        "forecast_execution": 7,
        "forecast_readback": 4,
    }, "summary phase counts drifted")

    operations = {item["operation"]: item for item in summary["operationSummaries"]}
    require(set(operations) == {
        "private_setup_source_builder",
        "private_setup_source_handoff",
        "private_setup_method_gate",
        "private_setup_forecast_execution",
        "forecast_card",
        "lifecycle_bundle",
        "resolution_status",
        "scoring_summary",
    }, "summary operations drifted")
    require(operations["private_setup_forecast_execution"]["canCreateForecastArtifacts"] is True, "forecast execution should be the only artifact-capable operation")
    for operation, row in operations.items():
        if operation == "private_setup_forecast_execution":
            continue
        require(row["canCreateForecastArtifacts"] is False, f"{operation} should not create forecast artifacts")
    readback_operations = [
        operation
        for operation, row in operations.items()
        if row["usesNormalForecastReadSurface"]
    ]
    require(readback_operations == ["forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"], "summary should preserve normal readback operations")

    artifact = summary["artifactBoundary"]
    require(artifact["artifactCreationAllowedOnlyFor"] == "private_setup_forecast_execution:confirmed_builder_draft", "artifact boundary should name confirmed execution only")
    require(artifact["generatedForecastId"] == "forecast-1102", "summary should bind forecast-1102")
    require(artifact["qualityClaimAllowed"] is False, "summary should keep quality claims blocked")
    require(artifact["matrixCreatesArtifacts"] is False, "summary should not claim the matrix creates artifacts")

    errors = summary["sanitizedErrorCoverage"]
    require(errors["covered"] is True, "summary should include sanitized error coverage")
    require(errors["operations"] == ["private_setup_source_builder"], "summary should bind source-builder sanitized error")
    require(errors["errorCodes"] == ["validation_failed"], "summary should bind validation_failed error")

    read_surface = summary["readSurface"]
    require(read_surface["compactSummaryDoesNotEmbedEnvelopes"] is True, "summary should not embed envelopes")
    require(read_surface["agentOperation"] == "private_setup_adapter_conformance_summary", "summary should expose agent operation")
    require(read_surface["mcpTool"] == "ope_private_setup_adapter_conformance_summary", "summary should expose MCP tool")

    boundary = summary["executionBoundary"]
    require(boundary["summaryDoesNotExecute"] is True, "summary should not execute")
    require(boundary["summaryDoesNotEmbedEnvelopes"] is True, "summary should not embed envelopes")
    for key in [
        "readsPrivateData",
        "runsCommands",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "resolvesOutcomes",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    print("checked private setup adapter conformance summary")


if __name__ == "__main__":
    main()
