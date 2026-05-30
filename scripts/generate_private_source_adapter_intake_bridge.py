#!/usr/bin/env python3
"""Generate or check the private source adapter intake bridge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_source_adapter_outcome_matrix import build_matrix
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-source-adapters"
BRIDGE_PATH = GENERATED / "ope-private-source-adapter-intake-bridge.generated.json"
SCHEMA = SPEC / "private-source-adapter-intake-bridge.schema.json"
MATRIX_PATH = "spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-outcome-matrix.generated.json"
GENERATED_AT = "2026-06-06T22:00:00Z"
NO_COMMAND = "none"
FORECAST_SCORE_CREDENTIAL_BLOCKS = [
    "forecast_artifact",
    "forecast_card",
    "scoring_report",
    "credential_record",
    "live_fetch_result",
]


class PrivateSourceAdapterIntakeBridgeError(Exception):
    pass


def bridge_row(
    *,
    row_id: str,
    outcome_row: dict[str, Any],
    bridge_status: str,
    allowed_entrypoint: str,
    current_command: str,
    retry_condition: str,
    retry_command: str,
    required_inputs: list[str],
    allowed_outputs: list[str],
    blocked_outputs: list[str],
    agent_instruction: str,
) -> dict[str, Any]:
    return {
        "bridgeRowId": row_id,
        "sourceKind": outcome_row["sourceKind"],
        "outcomeRowId": outcome_row["outcomeRowId"],
        "outcomeClass": outcome_row["outcomeClass"],
        "setupOutcomeClass": outcome_row["setupOutcomeClass"],
        "bridgeStatus": bridge_status,
        "allowedEntrypoint": allowed_entrypoint,
        "currentCommand": current_command,
        "retryCondition": retry_condition,
        "retryCommand": retry_command,
        "requiredInputs": required_inputs,
        "allowedDownstreamOutputs": allowed_outputs,
        "blockedOutputs": blocked_outputs,
        "bridgeCreatesOutputs": False,
        "canCreateForecastArtifacts": False,
        "canCreateScoringRecords": False,
        "canStoreCredentials": False,
        "agentInstruction": agent_instruction,
    }


def bridge_rows(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    return [
        bridge_row(
            row_id="privateadapterbridge-001",
            outcome_row=rows["local_file"],
            bridge_status="allowed_current_entrypoint",
            allowed_entrypoint="source_builder",
            current_command="python3 scripts/ope.py source-builder",
            retry_condition="no_retry_needed",
            retry_command=NO_COMMAND,
            required_inputs=["caller_approved_local_file_paths"],
            allowed_outputs=["source_manifest_build", "draft_source_manifest", "draft_field_mapping"],
            blocked_outputs=FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Run source-builder only for caller-approved local files; continue to handoff before intake or forecasting.",
        ),
        bridge_row(
            row_id="privateadapterbridge-002",
            outcome_row=rows["manual_mapping"],
            bridge_status="approval_required",
            allowed_entrypoint="source_handoff_confirmation",
            current_command=NO_COMMAND,
            retry_condition="after_mapping_confirmation",
            retry_command="python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
            required_inputs=["caller_confirmed_field_mapping", "source_builder_draft"],
            allowed_outputs=["source_intake_handoff", "source_intake_report"],
            blocked_outputs=["source_manifest"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Ask the caller to confirm mappings, then run source-handoff confirmation before method gates.",
        ),
        bridge_row(
            row_id="privateadapterbridge-003",
            outcome_row=rows["auto_evidence_connector"],
            bridge_status="fixture_entrypoint",
            allowed_entrypoint="auto_evidence_fixture",
            current_command="python3 scripts/ope.py gather-evidence",
            retry_condition="no_retry_needed",
            retry_command=NO_COMMAND,
            required_inputs=["accepted_auto_evidence_request_fixture", "source_policy_allows_fixture_connector"],
            allowed_outputs=["evidence_source_set"],
            blocked_outputs=["source_manifest", "field_mapping"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Use fixture replay for policy-bound auto evidence; do not treat it as production live gathering.",
        ),
        bridge_row(
            row_id="privateadapterbridge-004",
            outcome_row=rows["manual_upload"],
            bridge_status="runtime_not_implemented",
            allowed_entrypoint="no_current_entrypoint",
            current_command=NO_COMMAND,
            retry_condition="after_runtime_available",
            retry_command=NO_COMMAND,
            required_inputs=["future_manual_upload_runtime", "caller_approval"],
            allowed_outputs=[],
            blocked_outputs=["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Wait for a checked manual-upload runtime; do not ingest uploads through the current bridge.",
        ),
        bridge_row(
            row_id="privateadapterbridge-005",
            outcome_row=rows["private_api"],
            bridge_status="credential_runtime_missing",
            allowed_entrypoint="no_current_entrypoint",
            current_command=NO_COMMAND,
            retry_condition="after_runtime_available",
            retry_command=NO_COMMAND,
            required_inputs=["future_private_api_runtime", "credential_safe_runtime", "caller_approval"],
            allowed_outputs=[],
            blocked_outputs=["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Wait for a credential-safe private API runtime; do not request secrets in OPE artifacts.",
        ),
        bridge_row(
            row_id="privateadapterbridge-006",
            outcome_row=rows["private_database"],
            bridge_status="credential_runtime_missing",
            allowed_entrypoint="no_current_entrypoint",
            current_command=NO_COMMAND,
            retry_condition="after_runtime_available",
            retry_command=NO_COMMAND,
            required_inputs=["future_private_database_runtime", "credential_safe_runtime", "caller_approval"],
            allowed_outputs=[],
            blocked_outputs=["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Wait for a credential-safe private database runtime; do not connect databases through this bridge.",
        ),
        bridge_row(
            row_id="privateadapterbridge-007",
            outcome_row=rows["unregistered_source"],
            bridge_status="unsupported_source",
            allowed_entrypoint="no_current_entrypoint",
            current_command=NO_COMMAND,
            retry_condition="after_source_replaced",
            retry_command=NO_COMMAND,
            required_inputs=["replacement_source_kind_declared_in_capability_contract"],
            allowed_outputs=[],
            blocked_outputs=["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Replace the unregistered source kind with a declared adapter before trying setup again.",
        ),
        bridge_row(
            row_id="privateadapterbridge-008",
            outcome_row=rows["unsafe_source"],
            bridge_status="rejected_source",
            allowed_entrypoint="no_current_entrypoint",
            current_command=NO_COMMAND,
            retry_condition="never_without_new_source",
            retry_command=NO_COMMAND,
            required_inputs=["safe_replacement_source"],
            allowed_outputs=[],
            blocked_outputs=["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_CREDENTIAL_BLOCKS,
            agent_instruction="Reject unsafe source input and require a safe replacement before any setup step.",
        ),
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privateadapterbridgeguard-001",
            "name": "outcome_matrix_binding",
            "rule": "Every bridge row must bind one private source adapter outcome row.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
        {
            "guardId": "privateadapterbridgeguard-002",
            "name": "checked_entrypoints_only",
            "rule": "Runnable bridge commands must point only to checked local OPE commands.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
        {
            "guardId": "privateadapterbridgeguard-003",
            "name": "confirmation_before_handoff",
            "rule": "Manual mapping rows require caller confirmation before source-handoff confirmation.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
        {
            "guardId": "privateadapterbridgeguard-004",
            "name": "planned_runtimes_non_generating",
            "rule": "Manual upload, private API, and private database rows must stay non-generating.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
        {
            "guardId": "privateadapterbridgeguard-005",
            "name": "no_forecast_or_score_outputs",
            "rule": "Bridge rows must not create forecast artifacts, forecast cards, scoring records, or credential records.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
        {
            "guardId": "privateadapterbridgeguard-006",
            "name": "unsafe_sources_stop",
            "rule": "Unsupported and unsafe sources must not enter source intake through the bridge.",
            "checkedBy": ["scripts/check_private_source_adapter_intake_bridge.py"],
        },
    ]


def build_bridge() -> dict[str, Any]:
    matrix = build_matrix()
    bridge = {
        "privateSourceAdapterIntakeBridgeId": "privateadapterintakebridge-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "bridge_contract_only",
        "boundPrivateSourceAdapterOutcomeMatrixId": matrix["privateSourceAdapterOutcomeMatrixId"],
        "boundPrivateSourceAdapterCapabilityId": matrix["boundPrivateSourceAdapterCapabilityId"],
        "boundPrivateSetupWorkflowId": matrix["boundPrivateSetupWorkflowId"],
        "boundPrivateSourceAdapterOutcomeMatrixPath": MATRIX_PATH,
        "bridgeRows": bridge_rows(matrix),
        "executionBoundary": {
            "bridgeDoesNotExecute": True,
            "normalChecksOffline": True,
            "createsSourceManifests": False,
            "createsFieldMappings": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
            "privateAdapterRuntimeImplemented": False,
            "onlyRoutesToCheckedEntrypoints": True,
        },
        "guards": guards(),
        "warnings": [
            "This bridge routes agent next actions; it does not execute source intake by itself.",
            "Only local-file source-builder and fixture auto-evidence commands are current runnable entrypoints.",
            "Manual mapping requires caller confirmation before source-handoff confirmation.",
            "Planned, unsupported, unsafe, and credential-missing rows remain non-generating.",
        ],
    }
    validate_bridge(bridge, matrix)
    return bridge


def validate_bridge(bridge: dict[str, Any], matrix: dict[str, Any]) -> None:
    errors = validate_record(bridge, SCHEMA)
    if errors:
        raise PrivateSourceAdapterIntakeBridgeError(f"private source adapter intake bridge schema validation failed: {errors[0]}")

    if bridge["boundPrivateSourceAdapterOutcomeMatrixId"] != matrix["privateSourceAdapterOutcomeMatrixId"]:
        raise PrivateSourceAdapterIntakeBridgeError("bridge must bind outcome matrix")
    if bridge["boundPrivateSourceAdapterCapabilityId"] != matrix["boundPrivateSourceAdapterCapabilityId"]:
        raise PrivateSourceAdapterIntakeBridgeError("bridge must preserve capability binding")
    if bridge["boundPrivateSetupWorkflowId"] != matrix["boundPrivateSetupWorkflowId"]:
        raise PrivateSourceAdapterIntakeBridgeError("bridge must preserve workflow binding")

    matrix_rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    bridge_rows_by_kind = {item["sourceKind"]: item for item in bridge["bridgeRows"]}
    if set(bridge_rows_by_kind) != set(matrix_rows):
        raise PrivateSourceAdapterIntakeBridgeError("bridge source kind coverage drift")

    for source_kind, bridge_row_item in bridge_rows_by_kind.items():
        matrix_row = matrix_rows[source_kind]
        if bridge_row_item["outcomeRowId"] != matrix_row["outcomeRowId"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} outcome row binding drift")
        if bridge_row_item["outcomeClass"] != matrix_row["outcomeClass"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} outcome class drift")
        if bridge_row_item["setupOutcomeClass"] != matrix_row["setupOutcomeClass"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} setup outcome drift")
        if bridge_row_item["bridgeCreatesOutputs"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} bridge row must not create outputs")
        if bridge_row_item["canCreateForecastArtifacts"] or bridge_row_item["canCreateScoringRecords"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} must not create forecast or scoring outputs")
        if bridge_row_item["canStoreCredentials"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} must not store credentials")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record"]:
            if blocked not in bridge_row_item["blockedOutputs"]:
                raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should block {blocked}")

    local_file = bridge_rows_by_kind["local_file"]
    if local_file["allowedEntrypoint"] != "source_builder":
        raise PrivateSourceAdapterIntakeBridgeError("local_file should route to source_builder")
    if local_file["currentCommand"] != "python3 scripts/ope.py source-builder":
        raise PrivateSourceAdapterIntakeBridgeError("local_file command should be source-builder")
    if "draft_source_manifest" not in local_file["allowedDownstreamOutputs"]:
        raise PrivateSourceAdapterIntakeBridgeError("local_file should allow draft source manifest downstream")

    manual_mapping = bridge_rows_by_kind["manual_mapping"]
    if manual_mapping["allowedEntrypoint"] != "source_handoff_confirmation":
        raise PrivateSourceAdapterIntakeBridgeError("manual_mapping should route to source-handoff confirmation")
    if manual_mapping["retryCondition"] != "after_mapping_confirmation":
        raise PrivateSourceAdapterIntakeBridgeError("manual_mapping should retry after confirmation")
    if manual_mapping["retryCommand"] != "python3 scripts/ope.py source-handoff --case confirmed_builder_draft":
        raise PrivateSourceAdapterIntakeBridgeError("manual_mapping retry command should bind confirmed source-handoff")

    auto_evidence = bridge_rows_by_kind["auto_evidence_connector"]
    if auto_evidence["allowedEntrypoint"] != "auto_evidence_fixture":
        raise PrivateSourceAdapterIntakeBridgeError("auto_evidence_connector should route to fixture evidence")
    if auto_evidence["currentCommand"] != "python3 scripts/ope.py gather-evidence":
        raise PrivateSourceAdapterIntakeBridgeError("auto_evidence_connector command should be gather-evidence")

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        item = bridge_rows_by_kind[source_kind]
        if item["allowedEntrypoint"] != "no_current_entrypoint":
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should have no current entrypoint")
        if item["currentCommand"] != NO_COMMAND or item["retryCommand"] != NO_COMMAND:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should not expose a current command")
        if item["allowedDownstreamOutputs"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should not allow downstream outputs")

    for source_kind in ["unregistered_source", "unsafe_source"]:
        item = bridge_rows_by_kind[source_kind]
        if item["allowedEntrypoint"] != "no_current_entrypoint":
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should have no entrypoint")
        if item["allowedDownstreamOutputs"]:
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should not allow outputs")
        if item["retryCondition"] == "no_retry_needed":
            raise PrivateSourceAdapterIntakeBridgeError(f"{source_kind} should require replacement or stop")

    boundary = bridge["executionBoundary"]
    if boundary["bridgeDoesNotExecute"] is not True or boundary["normalChecksOffline"] is not True:
        raise PrivateSourceAdapterIntakeBridgeError("bridge should remain non-executing and offline")
    if boundary["onlyRoutesToCheckedEntrypoints"] is not True:
        raise PrivateSourceAdapterIntakeBridgeError("bridge should route only to checked entrypoints")
    for key in [
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
        "privateAdapterRuntimeImplemented",
    ]:
        if boundary[key] is not False:
            raise PrivateSourceAdapterIntakeBridgeError(f"{key} should remain false")


def write_bridge(bridge: dict[str, Any]) -> None:
    write_generated(BRIDGE_PATH, bridge, label="private source adapter intake bridge", regen="python3 scripts/generate_private_source_adapter_intake_bridge.py --write")


def check_bridge(bridge: dict[str, Any]) -> None:
    check_generated(BRIDGE_PATH, bridge, label="private source adapter intake bridge", regen="python3 scripts/generate_private_source_adapter_intake_bridge.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private source adapter intake bridge drift")
    parser.add_argument("--write", action="store_true", help="write generated private source adapter intake bridge")
    args = parser.parse_args()
    try:
        bridge = build_bridge()
    except PrivateSourceAdapterIntakeBridgeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_bridge(bridge)
    elif args.check:
        check_bridge(bridge)
    else:
        sys.stdout.write(render_json(bridge))


if __name__ == "__main__":
    main()
