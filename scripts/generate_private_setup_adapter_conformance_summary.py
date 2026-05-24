#!/usr/bin/env python3
"""Generate or check compact private setup adapter conformance summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_agent_adapter_protocol_map import build_protocol_map
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-adapter-conformance"
SUMMARY_PATH = GENERATED / "ope-private-setup-adapter-conformance-summary.generated.json"
MATRIX_PATH = GENERATED / "ope-private-setup-adapter-conformance-matrix.generated.json"
SCHEMA = SPEC / "private-setup-adapter-conformance-summary.schema.json"
GENERATED_AT = "2026-06-07T13:15:00Z"
MATRIX_ID = "privatesetupadapterconformancematrix-001"
SUMMARY_ID = "privatesetupadapterconformancesummary-001"
GENERATED_FORECAST_ID = "forecast-1102"
GENERATED_QUESTION_ID = "question-1102"


class PrivateSetupAdapterConformanceSummaryError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def execution_boundary() -> dict[str, bool]:
    return {
        "summaryDoesNotExecute": True,
        "summaryDoesNotEmbedEnvelopes": True,
        "readsPrivateData": False,
        "runsCommands": False,
        "createsSourceManifests": False,
        "createsFieldMappings": False,
        "createsForecastArtifacts": False,
        "createsScoringRecords": False,
        "resolvesOutcomes": False,
        "fetchesLiveData": False,
        "storesCredentials": False,
        "createsHostedRuntime": False,
    }


def phase_summaries() -> list[dict[str, Any]]:
    return [
        {
            "phase": "source_builder",
            "caseCount": 6,
            "successCases": 5,
            "errorCases": 1,
            "artifactGeneratingCases": 0,
            "allowedNextActions": [
                "review_and_confirm_mappings",
                "replace_rejected_sources",
                "fix_source_builder_input",
            ],
        },
        {
            "phase": "source_handoff",
            "caseCount": 7,
            "successCases": 7,
            "errorCases": 0,
            "artifactGeneratingCases": 0,
            "allowedNextActions": [
                "ask_mapping_confirmation",
                "run_setup_method_gate",
                "collect_more_data",
                "replace_rejected_sources",
            ],
        },
        {
            "phase": "method_gate",
            "caseCount": 7,
            "successCases": 7,
            "errorCases": 0,
            "artifactGeneratingCases": 0,
            "allowedNextActions": [
                "ask_mapping_confirmation",
                "await_explicit_setup_forecast_execution",
                "collect_more_data",
                "replace_rejected_sources",
            ],
        },
        {
            "phase": "forecast_execution",
            "caseCount": 7,
            "successCases": 7,
            "errorCases": 0,
            "artifactGeneratingCases": 1,
            "allowedNextActions": [
                "ask_mapping_confirmation",
                "read_forecast_card",
                "collect_more_data",
                "replace_rejected_sources",
            ],
        },
        {
            "phase": "forecast_readback",
            "caseCount": 4,
            "successCases": 4,
            "errorCases": 0,
            "artifactGeneratingCases": 0,
            "allowedNextActions": [
                "inspect_forecast_card",
                "inspect_lifecycle_bundle",
                "inspect_resolution_status",
                "inspect_scoring_summary",
            ],
        },
    ]


def operation_summaries() -> list[dict[str, Any]]:
    return [
        {
            "operation": "private_setup_source_builder",
            "phase": "source_builder",
            "caseCount": 6,
            "payloadShapes": ["source_builder_result", "sanitized_error"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": False,
        },
        {
            "operation": "private_setup_source_handoff",
            "phase": "source_handoff",
            "caseCount": 7,
            "payloadShapes": ["source_handoff_result"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": False,
        },
        {
            "operation": "private_setup_method_gate",
            "phase": "method_gate",
            "caseCount": 7,
            "payloadShapes": ["method_gate_result"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": False,
        },
        {
            "operation": "private_setup_forecast_execution",
            "phase": "forecast_execution",
            "caseCount": 7,
            "payloadShapes": ["forecast_execution_result"],
            "canCreateForecastArtifacts": True,
            "usesNormalForecastReadSurface": False,
        },
        {
            "operation": "forecast_card",
            "phase": "forecast_readback",
            "caseCount": 1,
            "payloadShapes": ["forecast_card_readback"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": True,
        },
        {
            "operation": "lifecycle_bundle",
            "phase": "forecast_readback",
            "caseCount": 1,
            "payloadShapes": ["lifecycle_bundle_readback"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": True,
        },
        {
            "operation": "resolution_status",
            "phase": "forecast_readback",
            "caseCount": 1,
            "payloadShapes": ["resolution_status_readback"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": True,
        },
        {
            "operation": "scoring_summary",
            "phase": "forecast_readback",
            "caseCount": 1,
            "payloadShapes": ["scoring_summary_readback"],
            "canCreateForecastArtifacts": False,
            "usesNormalForecastReadSurface": True,
        },
    ]


def build_summary() -> dict[str, Any]:
    protocol_map = build_protocol_map()
    summary = {
        "privateSetupAdapterConformanceSummaryId": SUMMARY_ID,
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "compact_adapter_conformance_summary",
        "bindings": {
            "privateSetupAdapterConformanceMatrixId": MATRIX_ID,
            "privateSetupAdapterConformanceMatrixPath": str(MATRIX_PATH.relative_to(ROOT)),
            "agentEnvelopeSchema": "spec/agent-envelope.schema.json",
            "protocolMapId": protocol_map["protocolMapId"],
            "generatedForecastId": GENERATED_FORECAST_ID,
            "generatedQuestionId": GENERATED_QUESTION_ID,
        },
        "caseTotals": {
            "totalCases": 31,
            "successCases": 30,
            "errorCases": 1,
            "artifactGeneratingCases": 1,
            "publicReadRecordGeneratingCases": 1,
            "blockedForecastExecutionCases": 6,
            "readbackCases": 4,
        },
        "phaseSummaries": phase_summaries(),
        "operationSummaries": operation_summaries(),
        "artifactBoundary": {
            "artifactCreationAllowedOnlyFor": "private_setup_forecast_execution:confirmed_builder_draft",
            "generatedForecastId": GENERATED_FORECAST_ID,
            "generatedQuestionId": GENERATED_QUESTION_ID,
            "normalReadbackOperations": [
                "forecast_card",
                "lifecycle_bundle",
                "resolution_status",
                "scoring_summary",
            ],
            "qualityClaimAllowed": False,
            "matrixCreatesArtifacts": False,
        },
        "sanitizedErrorCoverage": {
            "covered": True,
            "errorCases": 1,
            "operations": ["private_setup_source_builder"],
            "errorCodes": ["validation_failed"],
        },
        "readSurface": {
            "compactSummaryDoesNotEmbedEnvelopes": True,
            "fullMatrixForImplementers": str(MATRIX_PATH.relative_to(ROOT)),
            "agentOperation": "private_setup_adapter_conformance_summary",
            "mcpTool": "ope_private_setup_adapter_conformance_summary",
            "recommendedForRoutineAgents": True,
        },
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This summary is read-only conformance guidance and does not execute adapter calls.",
            "Routine agents should use this compact summary before loading the full embedded-envelope matrix.",
            "Only the confirmed forecast-execution case in the referenced matrix points to generated fixture forecast artifacts.",
        ],
    }
    validate_summary(summary)
    return summary


def validate_summary(summary: dict[str, Any]) -> None:
    errors = validate_record(summary, SCHEMA)
    if errors:
        raise PrivateSetupAdapterConformanceSummaryError(
            f"private setup adapter conformance summary schema validation failed: {errors[0]}"
        )
    phase_total = sum(item["caseCount"] for item in summary["phaseSummaries"])
    if phase_total != summary["caseTotals"]["totalCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("phase case counts should match total cases")
    operation_total = sum(item["caseCount"] for item in summary["operationSummaries"])
    if operation_total != summary["caseTotals"]["totalCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("operation case counts should match total cases")
    readback_ops = [
        item["operation"]
        for item in summary["operationSummaries"]
        if item["usesNormalForecastReadSurface"]
    ]
    if readback_ops != summary["artifactBoundary"]["normalReadbackOperations"]:
        raise PrivateSetupAdapterConformanceSummaryError("readback operations should match artifact boundary")
    if summary["caseTotals"]["artifactGeneratingCases"] != 1:
        raise PrivateSetupAdapterConformanceSummaryError("summary should expose exactly one artifact-generating case")
    if summary["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise PrivateSetupAdapterConformanceSummaryError("summary should not execute")
    if summary["executionBoundary"]["summaryDoesNotEmbedEnvelopes"] is not True:
        raise PrivateSetupAdapterConformanceSummaryError("summary should not embed envelopes")
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
        if summary["executionBoundary"][key] is not False:
            raise PrivateSetupAdapterConformanceSummaryError(f"{key} must remain false")


def validate_against_matrix(summary: dict[str, Any]) -> None:
    if not MATRIX_PATH.exists():
        return
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    if matrix["privateSetupAdapterConformanceMatrixId"] != summary["bindings"]["privateSetupAdapterConformanceMatrixId"]:
        raise PrivateSetupAdapterConformanceSummaryError("summary should bind the generated conformance matrix")
    cases = matrix["operationCases"]
    if len(cases) != summary["caseTotals"]["totalCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("summary total cases should match matrix")
    if sum(1 for case in cases if case["expectedStatus"] == "ok") != summary["caseTotals"]["successCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("summary success cases should match matrix")
    if sum(1 for case in cases if case["expectedStatus"] == "error") != summary["caseTotals"]["errorCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("summary error cases should match matrix")
    if sum(1 for case in cases if case["forecastArtifactsCreated"]) != summary["caseTotals"]["artifactGeneratingCases"]:
        raise PrivateSetupAdapterConformanceSummaryError("summary artifact cases should match matrix")
    matrix_phase_counts: dict[str, int] = {}
    for case in cases:
        matrix_phase_counts[case["phase"]] = matrix_phase_counts.get(case["phase"], 0) + 1
    summary_phase_counts = {item["phase"]: item["caseCount"] for item in summary["phaseSummaries"]}
    if matrix_phase_counts != summary_phase_counts:
        raise PrivateSetupAdapterConformanceSummaryError("summary phase counts should match matrix")


def write_summary(summary: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(render_json(summary), encoding="utf-8")
    print("generated private setup adapter conformance summary")


def check_summary(summary: dict[str, Any]) -> None:
    expected = render_json(summary)
    if not SUMMARY_PATH.exists():
        print(f"missing private setup adapter conformance summary: {SUMMARY_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_adapter_conformance_summary.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = SUMMARY_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private setup adapter conformance summary drift: {SUMMARY_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_adapter_conformance_summary.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private setup adapter conformance summary")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup adapter conformance summary")
    parser.add_argument("--write", action="store_true", help="write generated private setup adapter conformance summary")
    args = parser.parse_args()
    summary = build_summary()
    validate_against_matrix(summary)
    if args.write:
        write_summary(summary)
    elif args.check:
        check_summary(summary)
    else:
        sys.stdout.write(render_json(summary))


if __name__ == "__main__":
    main()
