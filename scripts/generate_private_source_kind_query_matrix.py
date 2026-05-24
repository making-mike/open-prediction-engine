#!/usr/bin/env python3
"""Generate or check private source-kind selection adapter query examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from agent_adapter_dispatcher import (
    DEFAULT_CALLER_INTENT,
    DEFAULT_FORECAST_ID,
    DEFAULT_PRIVATE_SETUP_REQUEST_ID,
    DEFAULT_QUESTION_ID,
    output_envelope,
)
from generate_agent_adapter_protocol_map import build_protocol_map
from generate_private_source_kind_selection_examples import SOURCE_KIND_ORDER, build_examples
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST
from read_ope_record import DEFAULT_MAX_BYTES


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-source-kind-selection"
MATRIX_PATH = GENERATED / "ope-private-source-kind-query-matrix.generated.json"
SCHEMA = SPEC / "private-source-kind-query-matrix.schema.json"
GENERATED_AT = "2026-06-07T12:10:00Z"
UNSUPPORTED_SOURCE_KIND = "spreadsheet_macro"


class PrivateSourceKindQueryMatrixError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def dispatcher_args(source_kind: str | None) -> argparse.Namespace:
    return argparse.Namespace(
        operation="private_source_kind_selection",
        request=DEFAULT_REQUEST,
        forecast_id=DEFAULT_FORECAST_ID,
        question_id=DEFAULT_QUESTION_ID,
        private_setup_request_id=DEFAULT_PRIVATE_SETUP_REQUEST_ID,
        private_setup_case=None,
        source_kind=source_kind,
        source_builder_case="local_draft",
        source_builder_inputs=[],
        source_builder_mapping_hints=[],
        source_handoff_case="unconfirmed_builder_draft",
        method_gate_case="unconfirmed_builder_draft",
        forecast_execution_case="unconfirmed_builder_draft",
        max_bytes=DEFAULT_MAX_BYTES,
        caller_intent=DEFAULT_CALLER_INTENT,
    )


def agent_call_command(source_kind: str | None) -> str:
    command = "python3 scripts/ope.py agent-call --operation private_source_kind_selection"
    if source_kind is not None:
        command += f" --source-kind {source_kind}"
    return command


def envelope_for(source_kind: str | None) -> dict[str, Any]:
    return output_envelope(dispatcher_args(source_kind))


def case_from_envelope(
    index: int,
    *,
    query_mode: str,
    source_kind: str | None,
    envelope: dict[str, Any],
    expected_immediate_action: str | None,
    selected_example_id: str | None,
) -> dict[str, Any]:
    error = envelope["error"]
    return {
        "queryCaseId": f"sourcekindquerycase-{index:03d}",
        "queryMode": query_mode,
        "sourceKind": source_kind,
        "agentCallCommand": agent_call_command(source_kind),
        "mcpTool": "ope_private_source_kind_selection",
        "expectedStatus": envelope["status"],
        "expectedExitCode": envelope["exitCode"],
        "expectedErrorCode": error["code"] if isinstance(error, dict) else None,
        "payloadShape": payload_shape(envelope),
        "expectedImmediateAction": expected_immediate_action,
        "selectedExampleId": selected_example_id,
        "envelope": envelope,
    }


def payload_shape(envelope: dict[str, Any]) -> str:
    payload = envelope["payload"]
    if payload is None:
        return "sanitized_error"
    if "selectedExample" in payload:
        return "selected_example_only"
    return "full_examples"


def execution_boundary() -> dict[str, bool]:
    return {
        "matrixDoesNotExecute": True,
        "usesAdapterEnvelopeOnly": True,
        "readsPrivateData": False,
        "runsCommands": False,
        "createsSourceManifests": False,
        "createsFieldMappings": False,
        "createsForecastArtifacts": False,
        "createsScoringRecords": False,
        "fetchesLiveData": False,
        "storesCredentials": False,
        "createsHostedRuntime": False,
    }


def build_matrix() -> dict[str, Any]:
    examples = build_examples()
    examples_by_source = {
        item["sourceKind"]: item
        for item in examples["selectionExamples"]
    }
    protocol_map = build_protocol_map()

    cases = [
        case_from_envelope(
            1,
            query_mode="full_list",
            source_kind=None,
            envelope=envelope_for(None),
            expected_immediate_action=None,
            selected_example_id=None,
        )
    ]
    for offset, source_kind in enumerate(SOURCE_KIND_ORDER, start=2):
        example = examples_by_source[source_kind]
        cases.append(
            case_from_envelope(
                offset,
                query_mode="selected_source_kind",
                source_kind=source_kind,
                envelope=envelope_for(source_kind),
                expected_immediate_action=example["recommendation"]["immediateAction"],
                selected_example_id=example["selectionExampleId"],
            )
        )
    cases.append(
        case_from_envelope(
            10,
            query_mode="unsupported_source_kind",
            source_kind=UNSUPPORTED_SOURCE_KIND,
            envelope=envelope_for(UNSUPPORTED_SOURCE_KIND),
            expected_immediate_action=None,
            selected_example_id=None,
        )
    )

    matrix = {
        "privateSourceKindQueryMatrixId": "privatesourcekindquerymatrix-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "adapter_query_examples_only",
        "bindings": {
            "privateSourceKindSelectionExamplesId": examples["privateSourceKindSelectionExamplesId"],
            "agentEnvelopeSchema": "spec/agent-envelope.schema.json",
            "protocolMapId": protocol_map["protocolMapId"],
        },
        "queryCases": cases,
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This matrix is adapter conformance evidence only and does not execute selected setup paths.",
            "Selected examples remain recommendations; forecast artifacts require later source intake, method gates, and explicit forecast execution.",
            "The unsupported source-kind case must stay a sanitized bad_request envelope with no payload.",
        ],
    }
    validate_matrix(matrix, examples_by_source)
    return matrix


def validate_matrix(
    matrix: dict[str, Any],
    examples_by_source: dict[str, dict[str, Any]],
) -> None:
    errors = validate_record(matrix, SCHEMA)
    if errors:
        raise PrivateSourceKindQueryMatrixError(
            f"private source-kind query matrix schema validation failed: {errors[0]}"
        )

    cases = matrix["queryCases"]
    if [case["queryMode"] for case in cases] != [
        "full_list",
        *["selected_source_kind" for _ in SOURCE_KIND_ORDER],
        "unsupported_source_kind",
    ]:
        raise PrivateSourceKindQueryMatrixError("query matrix should preserve full, selected, unsupported order")

    full_case = cases[0]
    full_envelope = full_case["envelope"]
    if full_case["payloadShape"] != "full_examples" or full_envelope["status"] != "ok":
        raise PrivateSourceKindQueryMatrixError("full-list case should return the full examples envelope")
    if full_envelope["payload"]["privateSourceKindSelectionExamplesId"] != matrix["bindings"]["privateSourceKindSelectionExamplesId"]:
        raise PrivateSourceKindQueryMatrixError("full-list case should bind the source-kind examples record")

    for case in cases[1:9]:
        source_kind = case["sourceKind"]
        envelope = case["envelope"]
        payload = envelope["payload"]
        example = examples_by_source[source_kind]
        if case["payloadShape"] != "selected_example_only":
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} should return selected_example_only")
        if envelope["status"] != "ok" or envelope["exitCode"] != 0:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should succeed")
        if "selectionExamples" in payload:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should omit full examples")
        if payload["requestedSourceKind"] != source_kind:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should echo source kind")
        if payload["selectedExample"]["selectionExampleId"] != example["selectionExampleId"]:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should bind selection example")
        if payload["selectedExample"]["recommendation"]["immediateAction"] != case["expectedImmediateAction"]:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query immediate action drift")
        if envelope["state"]["sourceMode"] != source_kind:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should preserve state source mode")
        if envelope["state"]["planStatus"] != "selected_example_only":
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query should preserve selected plan status")
        boundary = payload["executionBoundary"]
        if boundary["examplesDoNotExecute"] is not True or boundary["runsCommands"] is not False:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query must remain non-executing")
        if boundary["createsForecastArtifacts"] or boundary["createsScoringRecords"]:
            raise PrivateSourceKindQueryMatrixError(f"{source_kind} selected query must not forecast or score")

    unsupported = cases[-1]
    unsupported_envelope = unsupported["envelope"]
    if unsupported["payloadShape"] != "sanitized_error":
        raise PrivateSourceKindQueryMatrixError("unsupported source-kind case should be a sanitized error")
    if unsupported_envelope["status"] != "error" or unsupported_envelope["exitCode"] != 2:
        raise PrivateSourceKindQueryMatrixError("unsupported source-kind case should return exit code 2")
    if unsupported_envelope["payload"] is not None:
        raise PrivateSourceKindQueryMatrixError("unsupported source-kind case should not include a payload")
    if unsupported_envelope["error"]["code"] != "bad_request":
        raise PrivateSourceKindQueryMatrixError("unsupported source-kind case should return bad_request")
    if unsupported_envelope["state"]["sourceMode"] != UNSUPPORTED_SOURCE_KIND:
        raise PrivateSourceKindQueryMatrixError("unsupported source-kind case should preserve sanitized source mode")

    boundary = matrix["executionBoundary"]
    if boundary["matrixDoesNotExecute"] is not True or boundary["usesAdapterEnvelopeOnly"] is not True:
        raise PrivateSourceKindQueryMatrixError("query matrix should be non-executing adapter evidence")
    for key in [
        "readsPrivateData",
        "runsCommands",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        if boundary[key] is not False:
            raise PrivateSourceKindQueryMatrixError(f"{key} must remain false")


def write_matrix(matrix: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    MATRIX_PATH.write_text(render_json(matrix), encoding="utf-8")
    print("generated private source-kind query matrix")


def check_matrix(matrix: dict[str, Any]) -> None:
    expected = render_json(matrix)
    if not MATRIX_PATH.exists():
        print(f"missing private source-kind query matrix: {MATRIX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_source_kind_query_matrix.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = MATRIX_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private source-kind query matrix drift: {MATRIX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_source_kind_query_matrix.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private source-kind query matrix")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private source-kind query matrix")
    parser.add_argument("--write", action="store_true", help="write generated private source-kind query matrix")
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
