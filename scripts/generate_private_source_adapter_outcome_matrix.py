#!/usr/bin/env python3
"""Generate or check the private source adapter outcome matrix."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_source_adapter_capabilities import build_capabilities, load_generated_capabilities
from generate_private_setup_workflow import build_workflow, load_generated_workflow
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-source-adapters"
MATRIX_PATH = GENERATED / "ope-private-source-adapter-outcome-matrix.generated.json"
SCHEMA = SPEC / "private-source-adapter-outcome-matrix.schema.json"
CAPABILITY_PATH = "spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-capabilities.generated.json"
GENERATED_AT = "2026-06-06T21:30:00Z"
CAPABILITY_SOURCE_KINDS = [
    "local_file",
    "manual_mapping",
    "manual_upload",
    "auto_evidence_connector",
    "private_api",
    "private_database",
]
OUTCOME_CLASSES = [
    "available_fixture",
    "approval_required_fixture",
    "planned_runtime",
    "unsupported_source",
    "credential_missing",
    "rejected_unsafe_source",
]
BLOCK_FORECAST_AND_SCORING = [
    "forecast_artifact",
    "forecast_card",
    "scoring_report",
    "credential_record",
    "live_fetch_result",
]


class PrivateSourceAdapterOutcomeMatrixError(Exception):
    pass


def outcome_class(
    class_id: str,
    outcome: str,
    setup_outcome: str,
    terminal: bool,
    can_enter_setup: bool,
    next_action: str,
    description: str,
) -> dict[str, Any]:
    return {
        "outcomeClassId": class_id,
        "outcomeClass": outcome,
        "setupOutcomeClass": setup_outcome,
        "terminal": terminal,
        "canEnterSetup": can_enter_setup,
        "agentNextAction": next_action,
        "description": description,
    }


def outcome_classes() -> list[dict[str, Any]]:
    return [
        outcome_class(
            "privateadapteroutcomeclass-001",
            "available_fixture",
            "setup_ready",
            False,
            True,
            "follow_row_next_action",
            "The source kind is available in the local fixture surface and can proceed to the row-specific checked command.",
        ),
        outcome_class(
            "privateadapteroutcomeclass-002",
            "approval_required_fixture",
            "needs_confirmation",
            False,
            False,
            "request_mapping_confirmation",
            "The source kind is fixture-supported only after caller confirmation or approval.",
        ),
        outcome_class(
            "privateadapteroutcomeclass-003",
            "planned_runtime",
            "runtime_not_implemented",
            True,
            False,
            "wait_for_runtime",
            "The source kind is declared for future support, but the current local runtime cannot execute it.",
        ),
        outcome_class(
            "privateadapteroutcomeclass-004",
            "unsupported_source",
            "unsupported_source",
            True,
            False,
            "replace_source",
            "The source kind is outside the capability contract and must be replaced before setup.",
        ),
        outcome_class(
            "privateadapteroutcomeclass-005",
            "credential_missing",
            "runtime_not_implemented",
            True,
            False,
            "request_credentials_after_runtime",
            "The source would require credentials, but no credential runtime is implemented in the current local surface.",
        ),
        outcome_class(
            "privateadapteroutcomeclass-006",
            "rejected_unsafe_source",
            "rejected_source",
            True,
            False,
            "reject_source",
            "The source is unsafe for setup and must not enter source intake, forecasting, or scoring.",
        ),
    ]


def row(
    *,
    row_id: str,
    source_kind: str,
    binding_status: str,
    outcome: str,
    setup_outcome: str,
    can_enter_setup: bool,
    can_execute_source_read: bool,
    requires_approval: bool,
    requires_credential: bool,
    has_credential_runtime: bool,
    can_create_source_manifest: bool,
    next_action: str,
    blocked_artifacts: list[str],
    reason_codes: list[str],
    agent_instruction: str,
    adapter_id: str | None = None,
) -> dict[str, Any]:
    result = {
        "outcomeRowId": row_id,
        "sourceKind": source_kind,
        "capabilityBindingStatus": binding_status,
        "outcomeClass": outcome,
        "setupOutcomeClass": setup_outcome,
        "canEnterSetup": can_enter_setup,
        "canExecuteSourceRead": can_execute_source_read,
        "requiresApproval": requires_approval,
        "requiresCredential": requires_credential,
        "hasCredentialRuntime": has_credential_runtime,
        "canCreateSourceManifest": can_create_source_manifest,
        "canCreateForecastArtifacts": False,
        "canCreateScoringRecords": False,
        "agentNextAction": next_action,
        "blockedArtifacts": blocked_artifacts,
        "reasonCodes": reason_codes,
        "agentInstruction": agent_instruction,
    }
    if adapter_id is not None:
        result["adapterId"] = adapter_id
    return result


def outcome_rows(capability: dict[str, Any]) -> list[dict[str, Any]]:
    adapters = {item["sourceKind"]: item for item in capability["adapters"]}
    return [
        row(
            row_id="privateadapteroutcomerow-001",
            source_kind="local_file",
            adapter_id=adapters["local_file"]["adapterId"],
            binding_status="bound_adapter",
            outcome="available_fixture",
            setup_outcome="setup_ready",
            can_enter_setup=True,
            can_execute_source_read=True,
            requires_approval=False,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=True,
            next_action="run_source_builder",
            blocked_artifacts=BLOCK_FORECAST_AND_SCORING,
            reason_codes=["fixture_available", "approved_local_file_required", "forecast_outputs_blocked"],
            agent_instruction="Run the source builder on caller-approved local files, then continue through handoff and intake.",
        ),
        row(
            row_id="privateadapteroutcomerow-002",
            source_kind="manual_mapping",
            adapter_id=adapters["manual_mapping"]["adapterId"],
            binding_status="bound_adapter",
            outcome="approval_required_fixture",
            setup_outcome="needs_confirmation",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=True,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="request_mapping_confirmation",
            blocked_artifacts=["source_manifest"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["caller_confirmation_required", "mapping_is_proposal", "forecast_outputs_blocked"],
            agent_instruction="Ask the caller to confirm proposed mappings before treating them as source-intake inputs.",
        ),
        row(
            row_id="privateadapteroutcomerow-003",
            source_kind="auto_evidence_connector",
            adapter_id=adapters["auto_evidence_connector"]["adapterId"],
            binding_status="bound_adapter",
            outcome="available_fixture",
            setup_outcome="setup_ready",
            can_enter_setup=True,
            can_execute_source_read=True,
            requires_approval=False,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="use_auto_evidence_fixture",
            blocked_artifacts=["source_manifest"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["fixture_replay_available", "normal_checks_offline", "forecast_outputs_blocked"],
            agent_instruction="Use policy-bound fixture replay only; do not claim production live evidence gathering.",
        ),
        row(
            row_id="privateadapteroutcomerow-004",
            source_kind="manual_upload",
            adapter_id=adapters["manual_upload"]["adapterId"],
            binding_status="bound_adapter",
            outcome="planned_runtime",
            setup_outcome="runtime_not_implemented",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=True,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="wait_for_runtime",
            blocked_artifacts=["source_manifest", "field_mapping"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["manual_upload_runtime_missing", "approval_required", "forecast_outputs_blocked"],
            agent_instruction="Do not ingest uploaded data until an explicit upload runtime and approval path are implemented.",
        ),
        row(
            row_id="privateadapteroutcomerow-005",
            source_kind="private_api",
            adapter_id=adapters["private_api"]["adapterId"],
            binding_status="bound_adapter",
            outcome="credential_missing",
            setup_outcome="runtime_not_implemented",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=True,
            requires_credential=True,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="request_credentials_after_runtime",
            blocked_artifacts=["source_manifest", "field_mapping"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["private_api_runtime_missing", "credential_runtime_missing", "forecast_outputs_blocked"],
            agent_instruction="Do not request or expose credentials in OPE artifacts; wait for an explicit private API runtime.",
        ),
        row(
            row_id="privateadapteroutcomerow-006",
            source_kind="private_database",
            adapter_id=adapters["private_database"]["adapterId"],
            binding_status="bound_adapter",
            outcome="credential_missing",
            setup_outcome="runtime_not_implemented",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=True,
            requires_credential=True,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="request_credentials_after_runtime",
            blocked_artifacts=["source_manifest", "field_mapping"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["private_database_runtime_missing", "credential_runtime_missing", "forecast_outputs_blocked"],
            agent_instruction="Do not connect databases or run queries until an explicit private database runtime exists.",
        ),
        row(
            row_id="privateadapteroutcomerow-007",
            source_kind="unregistered_source",
            binding_status="not_in_capability_contract",
            outcome="unsupported_source",
            setup_outcome="unsupported_source",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=False,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="replace_source",
            blocked_artifacts=["source_manifest", "field_mapping"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["source_kind_unregistered", "capability_contract_missing", "forecast_outputs_blocked"],
            agent_instruction="Replace the source with a source kind declared in the private source adapter capability contract.",
        ),
        row(
            row_id="privateadapteroutcomerow-008",
            source_kind="unsafe_source",
            binding_status="blocked_by_safety_policy",
            outcome="rejected_unsafe_source",
            setup_outcome="rejected_source",
            can_enter_setup=False,
            can_execute_source_read=False,
            requires_approval=False,
            requires_credential=False,
            has_credential_runtime=False,
            can_create_source_manifest=False,
            next_action="reject_source",
            blocked_artifacts=["source_manifest", "field_mapping"] + BLOCK_FORECAST_AND_SCORING,
            reason_codes=["unsafe_source", "secret_or_leakage_risk", "forecast_outputs_blocked"],
            agent_instruction="Reject the source and keep it out of source intake, method gates, forecasts, and scoring.",
        ),
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privateadaptermatrixguard-001",
            "name": "capability_binding",
            "rule": "Every declared source kind in the capability contract must have one bound outcome row.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
        {
            "guardId": "privateadaptermatrixguard-002",
            "name": "workflow_outcome_binding",
            "rule": "Every matrix outcome must bind to a private setup workflow outcome class.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
        {
            "guardId": "privateadaptermatrixguard-003",
            "name": "no_execution",
            "rule": "The matrix may recommend next actions but must not execute source reads by itself.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
        {
            "guardId": "privateadaptermatrixguard-004",
            "name": "no_artifacts",
            "rule": "The matrix must not create forecast artifacts, cards, scoring records, or credential records.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
        {
            "guardId": "privateadaptermatrixguard-005",
            "name": "planned_runtimes_blocked",
            "rule": "Manual upload, private API, and private database rows must stay runtime-not-implemented.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
        {
            "guardId": "privateadaptermatrixguard-006",
            "name": "unsafe_sources_rejected",
            "rule": "Unsafe and unregistered sources must not enter setup, source intake, forecasting, or scoring.",
            "checkedBy": ["scripts/check_private_source_adapter_outcome_matrix.py"],
        },
    ]


def build_matrix() -> dict[str, Any]:
    workflow = build_workflow()
    capability = build_capabilities()
    matrix = {
        "privateSourceAdapterOutcomeMatrixId": "privateadapteroutcomematrix-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "decision_matrix_contract_only",
        "boundPrivateSourceAdapterCapabilityId": capability["privateSourceAdapterCapabilityId"],
        "boundPrivateSetupWorkflowId": workflow["privateSetupWorkflowId"],
        "boundPrivateSourceAdapterCapabilityPath": CAPABILITY_PATH,
        "outcomeClasses": outcome_classes(),
        "outcomeRows": outcome_rows(capability),
        "executionBoundary": {
            "matrixDoesNotExecute": True,
            "normalChecksOffline": True,
            "createsSourceManifests": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
            "privateAdapterRuntimeImplemented": False,
        },
        "guards": guards(),
        "warnings": [
            "This matrix recommends agent next actions; it does not execute source reads.",
            "Planned private adapters cannot create source manifests, forecast artifacts, cards, or scoring records.",
            "Credentials must stay out of OPE artifacts and prompt-visible records.",
            "Unsafe and unregistered sources must be replaced before setup continues.",
        ],
    }
    validate_matrix(matrix, capability, workflow)
    return matrix


def validate_matrix(matrix: dict[str, Any], capability: dict[str, Any], workflow: dict[str, Any]) -> None:
    errors = validate_record(matrix, SCHEMA)
    if errors:
        raise PrivateSourceAdapterOutcomeMatrixError(f"private source adapter outcome matrix schema validation failed: {errors[0]}")

    if matrix["boundPrivateSourceAdapterCapabilityId"] != capability["privateSourceAdapterCapabilityId"]:
        raise PrivateSourceAdapterOutcomeMatrixError("matrix must bind private source adapter capabilities")
    if matrix["boundPrivateSetupWorkflowId"] != workflow["privateSetupWorkflowId"]:
        raise PrivateSourceAdapterOutcomeMatrixError("matrix must bind private setup workflow")

    classes = {item["outcomeClass"]: item for item in matrix["outcomeClasses"]}
    if list(classes) != OUTCOME_CLASSES:
        raise PrivateSourceAdapterOutcomeMatrixError("outcome class order drift")

    workflow_outcomes = {item["outcomeClass"] for item in workflow["outcomeClasses"]}
    for item in matrix["outcomeClasses"]:
        if item["setupOutcomeClass"] not in workflow_outcomes:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{item['outcomeClass']} should bind workflow outcome")
        if item["outcomeClass"] != "available_fixture" and item["canEnterSetup"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{item['outcomeClass']} should not enter setup")

    rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    expected_rows = set(CAPABILITY_SOURCE_KINDS + ["unregistered_source", "unsafe_source"])
    if set(rows) != expected_rows:
        raise PrivateSourceAdapterOutcomeMatrixError("outcome row source kind drift")

    capability_adapters = {item["sourceKind"]: item for item in capability["adapters"]}
    for source_kind in CAPABILITY_SOURCE_KINDS:
        row_item = rows[source_kind]
        adapter = capability_adapters[source_kind]
        if row_item["capabilityBindingStatus"] != "bound_adapter":
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} should bind a capability adapter")
        if row_item["adapterId"] != adapter["adapterId"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} adapter binding drift")
        if row_item["requiresApproval"] != adapter["approvalRequired"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} approval boundary drift")
        if row_item["canExecuteSourceRead"] and not adapter["canInspect"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} cannot execute reads without inspect capability")

    if rows["local_file"]["outcomeClass"] != "available_fixture" or not rows["local_file"]["canCreateSourceManifest"]:
        raise PrivateSourceAdapterOutcomeMatrixError("local_file should be an available source-builder fixture")
    if rows["manual_mapping"]["outcomeClass"] != "approval_required_fixture":
        raise PrivateSourceAdapterOutcomeMatrixError("manual_mapping should require approval")
    if rows["auto_evidence_connector"]["agentNextAction"] != "use_auto_evidence_fixture":
        raise PrivateSourceAdapterOutcomeMatrixError("auto_evidence_connector should route to fixture replay")
    if rows["manual_upload"]["outcomeClass"] != "planned_runtime":
        raise PrivateSourceAdapterOutcomeMatrixError("manual_upload should remain planned runtime")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row_item = rows[source_kind]
        if row_item["setupOutcomeClass"] != "runtime_not_implemented":
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} must bind runtime_not_implemented")
        if row_item["canEnterSetup"] or row_item["canExecuteSourceRead"] or row_item["canCreateSourceManifest"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} must remain non-executing")
    for source_kind in ["private_api", "private_database"]:
        if rows[source_kind]["outcomeClass"] != "credential_missing":
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} should surface credential_missing")
        if not rows[source_kind]["requiresCredential"] or rows[source_kind]["hasCredentialRuntime"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} should lack credential runtime")

    if rows["unregistered_source"]["outcomeClass"] != "unsupported_source":
        raise PrivateSourceAdapterOutcomeMatrixError("unregistered_source should be unsupported")
    if rows["unsafe_source"]["outcomeClass"] != "rejected_unsafe_source":
        raise PrivateSourceAdapterOutcomeMatrixError("unsafe_source should be rejected")

    for source_kind, row_item in rows.items():
        if row_item["canCreateForecastArtifacts"] or row_item["canCreateScoringRecords"]:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} must not create forecast or scoring records")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record"]:
            if blocked not in row_item["blockedArtifacts"]:
                raise PrivateSourceAdapterOutcomeMatrixError(f"{source_kind} must block {blocked}")

    boundary = matrix["executionBoundary"]
    if boundary["matrixDoesNotExecute"] is not True or boundary["normalChecksOffline"] is not True:
        raise PrivateSourceAdapterOutcomeMatrixError("matrix should be declaration-only and offline")
    for key in [
        "createsSourceManifests",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
        "privateAdapterRuntimeImplemented",
    ]:
        if boundary[key] is not False:
            raise PrivateSourceAdapterOutcomeMatrixError(f"{key} should remain false")


def write_matrix(matrix: dict[str, Any]) -> None:
    write_generated(MATRIX_PATH, matrix, label="private source adapter outcome matrix", regen="python3 scripts/generate_private_source_adapter_outcome_matrix.py --write")


def check_matrix(matrix: dict[str, Any]) -> None:
    check_generated(MATRIX_PATH, matrix, label="private source adapter outcome matrix", regen="python3 scripts/generate_private_source_adapter_outcome_matrix.py --write")


def load_generated_matrix() -> dict[str, Any] | None:
    if not MATRIX_PATH.exists():
        return None
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    capability = load_generated_capabilities() or build_capabilities()
    workflow = load_generated_workflow() or build_workflow()
    validate_matrix(matrix, capability, workflow)
    return matrix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private source adapter outcome matrix drift")
    parser.add_argument("--write", action="store_true", help="write generated private source adapter outcome matrix")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.write or args.check or args.rebuild:
            matrix = build_matrix()
        else:
            matrix = load_generated_matrix() or build_matrix()
    except PrivateSourceAdapterOutcomeMatrixError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_matrix(matrix)
    elif args.check:
        check_matrix(matrix)
    else:
        sys.stdout.write(render_json(matrix))


if __name__ == "__main__":
    main()
