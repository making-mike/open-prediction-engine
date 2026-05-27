#!/usr/bin/env python3
"""Check compact private setup adapter conformance summary boundaries."""

from __future__ import annotations

from build_agent_adapter_fixtures import (
    envelope,
    nullable_binding,
    render_json as render_envelope_json,
    state_from_private_setup_adapter_conformance_summary,
)
from generate_private_setup_adapter_conformance_summary import (
    MATRIX_PATH,
    build_summary,
    render_json,
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

    budget = summary["sizeBudget"]
    summary_bytes = len(render_json(summary).encode("utf-8"))
    require(summary_bytes <= budget["compactSummaryPayloadMaxBytes"], "summary payload should fit compact byte budget")
    require(budget["compactAgentEnvelopeMaxBytes"] > budget["compactSummaryPayloadMaxBytes"], "agent envelope budget should exceed payload budget")
    require(budget["fullMatrixRequiresExplicitCommand"] is True, "full matrix should require explicit read command")
    require(budget["oversizedAdapterErrorCode"] == "response_too_large", "oversized adapter reads should use response_too_large")
    require("operationCases" not in summary, "summary should not embed full matrix operation cases")
    require("envelopes" not in summary, "summary should not embed generated envelopes")
    guards = budget["shapeGuards"]
    require(guards["embedsEnvelopeRows"] is False, "summary should not embed envelope rows")
    require(guards["embedsOperationCases"] is False, "summary should not embed operation cases")
    require(guards["matrixPathOnly"] is True, "summary should reference the full matrix by path only")
    if MATRIX_PATH.exists():
        matrix_bytes = MATRIX_PATH.stat().st_size
        require(matrix_bytes > summary_bytes * 10, "full matrix should remain much larger than compact summary")
        require(matrix_bytes <= budget["fullMatrixReferenceMaxBytes"], "full matrix should fit reference byte budget")
    summary_envelope = envelope(
        "agentenvelope-045",
        "private_setup_adapter_conformance_summary",
        "read_only",
        "private_setup_adapter_conformance_summary",
        summary["privateSetupAdapterConformanceSummaryId"],
        summary,
        caller_intent="Read compact private setup adapter conformance guidance without loading full envelopes.",
        record_binding=nullable_binding(
            questionId=summary["bindings"]["generatedQuestionId"],
            forecastId=summary["bindings"]["generatedForecastId"],
        ),
        state=state_from_private_setup_adapter_conformance_summary(summary),
        max_bytes=budget["compactAgentEnvelopeMaxBytes"],
        warnings=[
            *summary["warnings"],
            "The adapter envelope is read-only and does not execute adapter calls or create forecast artifacts.",
        ],
    )
    summary_envelope_bytes = len(render_envelope_json(summary_envelope).encode("utf-8"))
    require(summary_envelope_bytes <= budget["compactAgentEnvelopeMaxBytes"], "summary envelope should fit compact byte budget")

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
