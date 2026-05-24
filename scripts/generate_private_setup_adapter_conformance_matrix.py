#!/usr/bin/env python3
"""Generate or check private setup adapter conformance examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_agent_adapter_fixtures import (
    OUTPUT_FILES,
    SOURCE_HANDOFF_FORECAST_ID,
    SOURCE_HANDOFF_QUESTION_ID,
    build_envelopes,
)
from generate_agent_adapter_protocol_map import build_protocol_map
from generate_private_setup_adapter_chain_runbook import build_runbook
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-adapter-conformance"
MATRIX_PATH = GENERATED / "ope-private-setup-adapter-conformance-matrix.generated.json"
SCHEMA = SPEC / "private-setup-adapter-conformance-matrix.schema.json"
GENERATED_AT = "2026-06-07T12:45:00Z"
PRIVATE_SETUP_REQUEST_ID = "privatesetuprequest-001"

SOURCE_BUILDER_ROWS = [
    ("private_setup_source_builder", "local_draft"),
    ("private_setup_source_builder_contains_secret", "contains_secret"),
    ("private_setup_source_builder_unsupported_format", "unsupported_format"),
    ("private_setup_source_builder_oversized", "oversized"),
    ("private_setup_source_builder_leakage", "leakage"),
]
SOURCE_HANDOFF_ROWS = [
    ("private_setup_source_handoff_unconfirmed_builder_draft", "unconfirmed_builder_draft"),
    ("private_setup_source_handoff_confirmed_builder_draft", "confirmed_builder_draft"),
    ("private_setup_source_handoff_insufficient_confirmed_builder_draft", "insufficient_confirmed_builder_draft"),
    ("private_setup_source_handoff_contains_secret", "contains_secret"),
    ("private_setup_source_handoff_unsupported_format", "unsupported_format"),
    ("private_setup_source_handoff_oversized", "oversized"),
    ("private_setup_source_handoff_leakage", "leakage"),
]
METHOD_GATE_ROWS = [
    ("private_setup_method_gate_unconfirmed_builder_draft", "unconfirmed_builder_draft"),
    ("private_setup_method_gate_confirmed_builder_draft", "confirmed_builder_draft"),
    ("private_setup_method_gate_insufficient_confirmed_builder_draft", "insufficient_confirmed_builder_draft"),
    ("private_setup_method_gate_contains_secret", "contains_secret"),
    ("private_setup_method_gate_unsupported_format", "unsupported_format"),
    ("private_setup_method_gate_oversized", "oversized"),
    ("private_setup_method_gate_leakage", "leakage"),
]
FORECAST_EXECUTION_ROWS = [
    ("private_setup_forecast_execution_unconfirmed_builder_draft", "unconfirmed_builder_draft"),
    ("private_setup_forecast_execution_confirmed_builder_draft", "confirmed_builder_draft"),
    ("private_setup_forecast_execution_insufficient_confirmed_builder_draft", "insufficient_confirmed_builder_draft"),
    ("private_setup_forecast_execution_contains_secret", "contains_secret"),
    ("private_setup_forecast_execution_unsupported_format", "unsupported_format"),
    ("private_setup_forecast_execution_oversized", "oversized"),
    ("private_setup_forecast_execution_leakage", "leakage"),
]
READBACK_ROWS = [
    ("private_setup_forecast_card_readback", "forecast_card", "inspect_forecast_card"),
    ("private_setup_lifecycle_bundle_readback", "lifecycle_bundle", "inspect_lifecycle_bundle"),
    ("private_setup_resolution_status_readback", "resolution_status", "inspect_resolution_status"),
    ("private_setup_scoring_summary_readback", "scoring_summary", "inspect_scoring_summary"),
]


class PrivateSetupAdapterConformanceMatrixError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def agent_call_command(operation: str, adapter_case: str | None) -> str:
    base = f"python3 scripts/ope.py agent-call --operation {operation}"
    if operation == "private_setup_source_builder":
        if adapter_case == "malformed_input":
            return f"{base} --source-builder-input malformed-input"
        return (
            f"{base} --private-setup-request-id {PRIVATE_SETUP_REQUEST_ID} "
            f"--source-builder-case {adapter_case}"
        )
    if operation == "private_setup_source_handoff":
        return (
            f"{base} --private-setup-request-id {PRIVATE_SETUP_REQUEST_ID} "
            f"--source-handoff-case {adapter_case}"
        )
    if operation == "private_setup_method_gate":
        return (
            f"{base} --private-setup-request-id {PRIVATE_SETUP_REQUEST_ID} "
            f"--method-gate-case {adapter_case}"
        )
    if operation == "private_setup_forecast_execution":
        return (
            f"{base} --private-setup-request-id {PRIVATE_SETUP_REQUEST_ID} "
            f"--forecast-execution-case {adapter_case}"
        )
    return f"{base} --forecast-id {SOURCE_HANDOFF_FORECAST_ID} --question-id {SOURCE_HANDOFF_QUESTION_ID}"


def payload_shape(operation: str, adapter_case: str, envelope: dict[str, Any]) -> str:
    if envelope["status"] == "error":
        return "sanitized_error"
    if operation == "private_setup_source_builder":
        return "source_builder_result"
    if operation == "private_setup_source_handoff":
        return "source_handoff_result"
    if operation == "private_setup_method_gate":
        return "method_gate_result"
    if operation == "private_setup_forecast_execution":
        return "forecast_execution_result"
    return {
        "forecast_card": "forecast_card_readback",
        "lifecycle_bundle": "lifecycle_bundle_readback",
        "resolution_status": "resolution_status_readback",
        "scoring_summary": "scoring_summary_readback",
    }[operation]


def payload_status(operation: str, envelope: dict[str, Any]) -> str | None:
    if envelope["payload"] is None:
        return None
    payload = envelope["payload"]
    if operation == "private_setup_source_builder":
        return payload["sourceManifestBuild"]["buildStatus"]
    if operation == "private_setup_source_handoff":
        return payload["sourceIntakeHandoff"]["handoffStatus"]
    if operation == "private_setup_method_gate":
        return payload["sourceHandoffMethodGate"]["methodGateStatus"]
    if operation == "private_setup_forecast_execution":
        return payload["setupForecastRun"]["runStatus"]
    if operation in {"forecast_card", "lifecycle_bundle"}:
        return payload["record"]["status"]
    if operation == "resolution_status":
        return payload["resolutionStatus"]
    if operation == "scoring_summary":
        return payload["scoreStatus"]
    raise PrivateSetupAdapterConformanceMatrixError(f"unsupported operation for status: {operation}")


def next_action(operation: str, envelope: dict[str, Any], fallback: str | None = None) -> str | None:
    if envelope["payload"] is None:
        return "fix_source_builder_input"
    payload = envelope["payload"]
    if operation in {
        "private_setup_source_builder",
        "private_setup_source_handoff",
        "private_setup_method_gate",
        "private_setup_forecast_execution",
    }:
        return payload["adapterGuidance"]["nextAction"]
    return fallback


def forecast_artifacts_created(operation: str, envelope: dict[str, Any]) -> bool:
    if envelope["payload"] is None:
        return False
    payload = envelope["payload"]
    if operation == "private_setup_forecast_execution":
        return bool(payload["adapterGuidance"]["forecastArtifactsCreated"])
    return False


def public_read_records_created(operation: str, envelope: dict[str, Any]) -> bool:
    if envelope["payload"] is None:
        return False
    payload = envelope["payload"]
    if operation == "private_setup_forecast_execution":
        return bool(payload["executionBoundary"]["createsPublicReadRecords"])
    return False


def quality_claim_allowed(envelope: dict[str, Any]) -> bool:
    payload = envelope["payload"]
    if not isinstance(payload, dict):
        return False
    quality = None
    if "qualityClaim" in payload:
        quality = payload["qualityClaim"]
    elif "record" in payload and isinstance(payload["record"], dict):
        quality = payload["record"].get("qualityClaim")
    if not isinstance(quality, dict):
        return False
    return quality.get("status") in {"allowed", "claim_allowed"}


def operation_case(
    index: int,
    *,
    phase: str,
    operation: str,
    adapter_case: str,
    envelope_filename: str,
    envelope: dict[str, Any],
    fallback_next_action: str | None = None,
) -> dict[str, Any]:
    error = envelope["error"]
    return {
        "operationCaseId": f"privatesetupadapterconformancecase-{index:03d}",
        "phase": phase,
        "operation": operation,
        "adapterCase": adapter_case,
        "envelopeFilename": envelope_filename,
        "agentCallCommand": agent_call_command(operation, adapter_case),
        "expectedStatus": envelope["status"],
        "expectedExitCode": envelope["exitCode"],
        "expectedErrorCode": error["code"] if isinstance(error, dict) else None,
        "payloadShape": payload_shape(operation, adapter_case, envelope),
        "payloadStatus": payload_status(operation, envelope),
        "nextAction": next_action(operation, envelope, fallback_next_action),
        "forecastArtifactsCreated": forecast_artifacts_created(operation, envelope),
        "publicReadRecordsCreated": public_read_records_created(operation, envelope),
        "scoringRecordsCreated": False,
        "resolutionCreated": False,
        "qualityClaimAllowed": quality_claim_allowed(envelope),
        "envelope": envelope,
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "matrixDoesNotExecute": True,
        "usesExistingGeneratedEnvelopes": True,
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


def envelope_by_key(envelopes: dict[str, dict[str, Any]], key: str) -> tuple[str, dict[str, Any]]:
    filename = OUTPUT_FILES[key]
    if filename not in envelopes:
        raise PrivateSetupAdapterConformanceMatrixError(f"missing envelope for {key}")
    return filename, envelopes[filename]


def build_matrix() -> dict[str, Any]:
    envelopes = build_envelopes()
    protocol_map = build_protocol_map()
    runbook = build_runbook()
    cases: list[dict[str, Any]] = []
    index = 1

    for key, adapter_case in SOURCE_BUILDER_ROWS:
        filename, envelope = envelope_by_key(envelopes, key)
        cases.append(
            operation_case(
                index,
                phase="source_builder",
                operation="private_setup_source_builder",
                adapter_case=adapter_case,
                envelope_filename=filename,
                envelope=envelope,
            )
        )
        index += 1

    filename, envelope = envelope_by_key(envelopes, "private_setup_source_builder_error")
    cases.append(
        operation_case(
            index,
            phase="source_builder",
            operation="private_setup_source_builder",
            adapter_case="malformed_input",
            envelope_filename=filename,
            envelope=envelope,
        )
    )
    index += 1

    for key, adapter_case in SOURCE_HANDOFF_ROWS:
        filename, envelope = envelope_by_key(envelopes, key)
        cases.append(
            operation_case(
                index,
                phase="source_handoff",
                operation="private_setup_source_handoff",
                adapter_case=adapter_case,
                envelope_filename=filename,
                envelope=envelope,
            )
        )
        index += 1

    for key, adapter_case in METHOD_GATE_ROWS:
        filename, envelope = envelope_by_key(envelopes, key)
        cases.append(
            operation_case(
                index,
                phase="method_gate",
                operation="private_setup_method_gate",
                adapter_case=adapter_case,
                envelope_filename=filename,
                envelope=envelope,
            )
        )
        index += 1

    for key, adapter_case in FORECAST_EXECUTION_ROWS:
        filename, envelope = envelope_by_key(envelopes, key)
        cases.append(
            operation_case(
                index,
                phase="forecast_execution",
                operation="private_setup_forecast_execution",
                adapter_case=adapter_case,
                envelope_filename=filename,
                envelope=envelope,
            )
        )
        index += 1

    for key, operation, fallback_next_action in READBACK_ROWS:
        filename, envelope = envelope_by_key(envelopes, key)
        cases.append(
            operation_case(
                index,
                phase="forecast_readback",
                operation=operation,
                adapter_case="generated_forecast_readback",
                envelope_filename=filename,
                envelope=envelope,
                fallback_next_action=fallback_next_action,
            )
        )
        index += 1

    matrix = {
        "privateSetupAdapterConformanceMatrixId": "privatesetupadapterconformancematrix-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "adapter_conformance_examples_only",
        "bindings": {
            "agentEnvelopeSchema": "spec/agent-envelope.schema.json",
            "protocolMapId": protocol_map["protocolMapId"],
            "privateSetupAdapterChainRunbookId": runbook["privateSetupAdapterChainRunbookId"],
            "generatedForecastId": SOURCE_HANDOFF_FORECAST_ID,
            "generatedQuestionId": SOURCE_HANDOFF_QUESTION_ID,
        },
        "operationCases": cases,
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This matrix is adapter conformance evidence only and does not execute private setup operations.",
            "Rows embed existing generated envelopes; they do not create new source, forecast, resolution, or scoring artifacts.",
            "Generated forecast readback stays routed through normal forecast card, lifecycle bundle, resolution, and scoring operations.",
        ],
    }
    validate_matrix(matrix)
    return matrix


def validate_matrix(matrix: dict[str, Any]) -> None:
    errors = validate_record(matrix, SCHEMA)
    if errors:
        raise PrivateSetupAdapterConformanceMatrixError(
            f"private setup adapter conformance matrix schema validation failed: {errors[0]}"
        )
    cases = matrix["operationCases"]
    if len(cases) != 31:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain 31 operation cases")
    phases = [case["phase"] for case in cases]
    if phases.count("source_builder") != 6:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain six source-builder rows")
    if phases.count("source_handoff") != 7:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain seven source-handoff rows")
    if phases.count("method_gate") != 7:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain seven method-gate rows")
    if phases.count("forecast_execution") != 7:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain seven forecast-execution rows")
    if phases.count("forecast_readback") != 4:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain four forecast-readback rows")

    for case in cases:
        envelope = case["envelope"]
        if case["operation"] != envelope["operation"]:
            raise PrivateSetupAdapterConformanceMatrixError(f"{case['operationCaseId']} operation drift")
        if case["expectedStatus"] != envelope["status"] or case["expectedExitCode"] != envelope["exitCode"]:
            raise PrivateSetupAdapterConformanceMatrixError(f"{case['operationCaseId']} status drift")
        if case["expectedStatus"] == "error" and envelope["payload"] is not None:
            raise PrivateSetupAdapterConformanceMatrixError(f"{case['operationCaseId']} error rows must not carry payloads")
        if case["scoringRecordsCreated"] or case["resolutionCreated"] or case["qualityClaimAllowed"]:
            raise PrivateSetupAdapterConformanceMatrixError(f"{case['operationCaseId']} should not allow scoring, resolution, or quality claims")

    confirmed_forecast_rows = [
        case for case in cases
        if case["operation"] == "private_setup_forecast_execution"
        and case["adapterCase"] == "confirmed_builder_draft"
    ]
    if len(confirmed_forecast_rows) != 1:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should contain one confirmed forecast-execution row")
    confirmed = confirmed_forecast_rows[0]
    if confirmed["forecastArtifactsCreated"] is not True or confirmed["publicReadRecordsCreated"] is not True:
        raise PrivateSetupAdapterConformanceMatrixError("confirmed forecast execution should record generated artifacts")
    if confirmed["payloadStatus"] != "generated" or confirmed["nextAction"] != "read_forecast_card":
        raise PrivateSetupAdapterConformanceMatrixError("confirmed forecast execution should route to forecast-card readback")

    blocked_forecast_rows = [
        case for case in cases
        if case["operation"] == "private_setup_forecast_execution"
        and case["adapterCase"] != "confirmed_builder_draft"
    ]
    if any(case["forecastArtifactsCreated"] or case["publicReadRecordsCreated"] for case in blocked_forecast_rows):
        raise PrivateSetupAdapterConformanceMatrixError("blocked forecast execution rows must not create artifacts")
    if not any(case["expectedStatus"] == "error" and case["expectedErrorCode"] == "validation_failed" for case in cases):
        raise PrivateSetupAdapterConformanceMatrixError("matrix should include sanitized source-builder validation error")

    boundary = matrix["executionBoundary"]
    if boundary["matrixDoesNotExecute"] is not True or boundary["usesExistingGeneratedEnvelopes"] is not True:
        raise PrivateSetupAdapterConformanceMatrixError("matrix should only summarize existing envelopes")
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
        if boundary[key] is not False:
            raise PrivateSetupAdapterConformanceMatrixError(f"{key} must remain false")


def write_matrix(matrix: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(render_json(matrix), encoding="utf-8")
    print("generated private setup adapter conformance matrix")


def check_matrix(matrix: dict[str, Any]) -> None:
    expected = render_json(matrix)
    if not MATRIX_PATH.exists():
        print(f"missing private setup adapter conformance matrix: {MATRIX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = MATRIX_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private setup adapter conformance matrix drift: {MATRIX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private setup adapter conformance matrix")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup adapter conformance matrix")
    parser.add_argument("--write", action="store_true", help="write generated private setup adapter conformance matrix")
    args = parser.parse_args()
    matrix = build_matrix()
    if args.write:
        write_matrix(matrix)
    elif args.check:
        check_matrix(matrix)
    else:
        sys.stdout.write(render_json(matrix))


if __name__ == "__main__":
    main()
