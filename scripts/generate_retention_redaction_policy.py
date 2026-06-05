#!/usr/bin/env python3
"""Generate a checked retention and redaction policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_credential_reference_policy import build_credential_reference_policy
from generate_lifecycle_operation_store import build_lifecycle_operation_store
from generate_persistent_sqlite_policy import build_persistent_sqlite_policy
from generate_pilot_summary_intake import build_pilot_summary_intake
from generate_runtime_security import build_runtime_security
from generate_workspace_tenant_isolation import build_workspace_tenant_isolation
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "retention-redaction-policy"
OUTPUT_PATH = GENERATED / "ope-retention-redaction-policy.generated.json"
SCHEMA = SPEC / "retention-redaction-policy.schema.json"
GENERATED_AT = "2026-06-04T23:58:00Z"

RETENTION_CLASSES = [
    "forecast_lifecycle_record",
    "evidence_trace_record",
    "source_connector_result",
    "source_binding_config",
    "credential_reference_record",
    "pilot_session_summary",
    "local_usage_trace_event",
    "operation_receipt",
]

POLICY_ACTIONS = [
    "retain_append_only",
    "archive_tombstone",
    "redaction_receipt",
    "sanitized_projection_rebuild",
    "physical_delete_exception",
]

PHYSICAL_DELETE_GATES = [
    "authorized_erasure_basis",
    "tenant_workspace_scope_verified",
    "record_class_allows_physical_delete",
    "legal_or_safety_review_recorded",
    "audit_tombstone_retained",
    "redaction_receipt_retained",
    "immutable_forecast_history_preserved_or_rendered_unscorable",
    "operator_approval_recorded",
]

POLICY_CASES = [
    "normal_forecast_lifecycle_retention",
    "archive_inactive_prediction",
    "redact_private_source_detail",
    "redact_credential_like_field",
    "pilot_summary_needs_redaction",
    "usage_trace_aggregate_only",
    "source_connector_raw_preview_requested",
    "physical_delete_missing_legal_basis",
    "physical_delete_with_authorized_erasure",
    "physical_delete_for_forecast_history",
    "redaction_receipt_replay",
    "tombstone_rebuild_read_model",
]

READBACKS = [
    "cli",
    "lifecycle_operation_store",
    "persistent_sqlite_policy",
    "runtime_security",
    "workspace_tenant_isolation",
    "pilot_summary_intake",
    "credential_reference_policy",
]


class RetentionRedactionPolicyError(Exception):
    pass


def retention_class(
    record_class: str,
    default_action: str,
    minimum_retention: str,
    rationale: str,
    *,
    raw_content_retained: bool = False,
    physical_delete_eligible: bool = False,
    aggregate_only_after_window: bool = False,
) -> dict[str, Any]:
    return {
        "recordClass": record_class,
        "defaultAction": default_action,
        "minimumRetention": minimum_retention,
        "archiveAction": "archive_tombstone",
        "redactionAction": "redaction_receipt",
        "physicalDeleteEligible": physical_delete_eligible,
        "auditMetadataRetained": True,
        "rawContentRetained": raw_content_retained,
        "retainCredentialValues": False,
        "aggregateOnlyAfterWindow": aggregate_only_after_window,
        "silentDeleteAllowed": False,
        "normalChecksWriteState": False,
        "rationale": rationale,
    }


def retention_classes() -> list[dict[str, Any]]:
    return [
        retention_class(
            "forecast_lifecycle_record",
            "retain_append_only",
            "indefinite_for_audit_and_scoring",
            "Forecast questions, artifacts, histories, resolutions, and scores are append-only evidence.",
            raw_content_retained=True,
        ),
        retention_class(
            "evidence_trace_record",
            "retain_append_only",
            "indefinite_for_provenance",
            "Evidence traces preserve source and connector bindings while keeping raw source payloads out of readbacks.",
            raw_content_retained=False,
        ),
        retention_class(
            "source_connector_result",
            "redaction_receipt",
            "metadata_only_until_source_policy_expires",
            "Connector records keep metadata, normalized fields, hashes, and provenance rather than raw previews.",
            physical_delete_eligible=True,
        ),
        retention_class(
            "source_binding_config",
            "archive_tombstone",
            "while_prediction_or_workspace_exists",
            "Source bindings can leave active read models, but audit metadata and tombstones remain.",
        ),
        retention_class(
            "credential_reference_record",
            "redaction_receipt",
            "until_reference_revoked_and_audit_receipt_recorded",
            "Credential records retain only opaque references, scope, lifecycle, and redaction receipts.",
        ),
        retention_class(
            "pilot_session_summary",
            "redaction_receipt",
            "sanitized_summary_only_until_pilot_evidence_window_closes",
            "Pilot evidence keeps sanitized summaries and blocks raw transcripts or private rows.",
            physical_delete_eligible=True,
        ),
        retention_class(
            "local_usage_trace_event",
            "sanitized_projection_rebuild",
            "aggregate_after_local_metric_window",
            "Usage traces are local-only and can be rolled into aggregate product metrics after the evidence window.",
            aggregate_only_after_window=True,
        ),
        retention_class(
            "operation_receipt",
            "retain_append_only",
            "indefinite_for_idempotency_and_audit",
            "Operation receipts prove what happened, support idempotent retry, and remain audit metadata.",
            raw_content_retained=True,
        ),
    ]


def policy_action(
    action_name: str,
    action_status: str,
    operation_name: str,
    safe_next_action: str,
    *,
    writes_audit_tombstone: bool = False,
    writes_redaction_receipt: bool = False,
    rebuilds_sanitized_projection: bool = False,
    requires_all_physical_delete_gates: bool = False,
    physically_deletes_records: bool = False,
) -> dict[str, Any]:
    return {
        "actionName": action_name,
        "actionStatus": action_status,
        "operationName": operation_name,
        "writesAuditTombstone": writes_audit_tombstone,
        "writesRedactionReceipt": writes_redaction_receipt,
        "rebuildsSanitizedProjection": rebuilds_sanitized_projection,
        "requiresAllPhysicalDeleteGates": requires_all_physical_delete_gates,
        "physicallyDeletesRecords": physically_deletes_records,
        "normalChecksExecuteAction": False,
        "silentDeleteAllowed": False,
        "safeNextAction": safe_next_action,
    }


def policy_actions() -> list[dict[str, Any]]:
    return [
        policy_action(
            "retain_append_only",
            "default_retention",
            "none",
            "keep immutable records and receipts available for scoring, provenance, and retry readbacks",
        ),
        policy_action(
            "archive_tombstone",
            "audit_tombstone_append",
            "record.archive",
            "append an archive tombstone and rebuild active read models without deleting records",
            writes_audit_tombstone=True,
        ),
        policy_action(
            "redaction_receipt",
            "redaction_receipt_append",
            "record.redact",
            "append a redaction receipt and replace unsafe fields with sanitized projections",
            writes_redaction_receipt=True,
        ),
        policy_action(
            "sanitized_projection_rebuild",
            "projection_rebuild",
            "read_model.rebuild",
            "rebuild local read models from retained receipts and sanitized aggregate inputs",
            rebuilds_sanitized_projection=True,
        ),
        policy_action(
            "physical_delete_exception",
            "exception_preflight_only",
            "future.physical_delete_exception",
            "require every gate and retain audit tombstone plus redaction receipt before any future delete path",
            requires_all_physical_delete_gates=True,
            physically_deletes_records=True,
        ),
    ]


def physical_delete_gate(
    gate_name: str,
    evidence_required: str,
    failure_status: str,
    *,
    blocks_forecast_history: bool = False,
) -> dict[str, Any]:
    return {
        "gateName": gate_name,
        "gateStatus": "required_exception_gate",
        "requiredForException": True,
        "blocksForecastHistory": blocks_forecast_history,
        "normalChecksEvaluateAsEffectful": False,
        "evidenceRequired": evidence_required,
        "failureStatus": failure_status,
    }


def physical_delete_gates() -> list[dict[str, Any]]:
    return [
        physical_delete_gate(
            "authorized_erasure_basis",
            "A recorded legal, safety, or operator-approved erasure basis scoped to the target record.",
            "blocked_missing_erasure_basis",
        ),
        physical_delete_gate(
            "tenant_workspace_scope_verified",
            "A tenant and workspace scope match proving the caller can request this exception.",
            "blocked_scope_mismatch",
        ),
        physical_delete_gate(
            "record_class_allows_physical_delete",
            "A record-class policy that allows physical delete exceptions for the target class.",
            "blocked_record_class",
            blocks_forecast_history=True,
        ),
        physical_delete_gate(
            "legal_or_safety_review_recorded",
            "A review receipt explaining why tombstone and redaction are insufficient.",
            "blocked_missing_review",
        ),
        physical_delete_gate(
            "audit_tombstone_retained",
            "An archive tombstone that preserves record identity, scope, reason, actor, and timestamp.",
            "blocked_missing_audit_tombstone",
        ),
        physical_delete_gate(
            "redaction_receipt_retained",
            "A redaction receipt that records removed field classes without retaining unsafe values.",
            "blocked_missing_redaction_receipt",
        ),
        physical_delete_gate(
            "immutable_forecast_history_preserved_or_rendered_unscorable",
            "Forecast lifecycle integrity must be preserved, or the affected forecast becomes explicitly unscorable.",
            "blocked_forecast_integrity_risk",
            blocks_forecast_history=True,
        ),
        physical_delete_gate(
            "operator_approval_recorded",
            "An explicit operator approval receipt for the physical delete exception preflight.",
            "blocked_missing_operator_approval",
        ),
    ]


def decision_case(
    case_name: str,
    case_status: str,
    record_class: str,
    selected_action: str,
    safe_next_action: str,
    *,
    gate_coverage: list[str] | None = None,
    physically_deletes_records: bool = False,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": case_status,
        "recordClass": record_class,
        "selectedAction": selected_action,
        "gateCoverage": gate_coverage or [],
        "physicallyDeletesRecords": physically_deletes_records,
        "normalChecksWriteState": False,
        "credentialValuesRetained": False,
        "sanitizedDiagnosticsOnly": True,
        "auditMetadataRetained": True,
        "safeNextAction": safe_next_action,
    }


def decision_cases() -> list[dict[str, Any]]:
    return [
        decision_case(
            "normal_forecast_lifecycle_retention",
            "retained_append_only",
            "forecast_lifecycle_record",
            "retain_append_only",
            "keep the lifecycle record available for provenance, scoring, and calibration readbacks",
        ),
        decision_case(
            "archive_inactive_prediction",
            "archived_with_tombstone",
            "source_binding_config",
            "archive_tombstone",
            "append a tombstone and remove the config from active read models",
        ),
        decision_case(
            "redact_private_source_detail",
            "redaction_required",
            "source_binding_config",
            "redaction_receipt",
            "append a redaction receipt and replace unsafe source details with a sanitized summary",
        ),
        decision_case(
            "redact_credential_like_field",
            "redaction_required",
            "credential_reference_record",
            "redaction_receipt",
            "redact the submitted field and retain only the scoped opaque credential reference",
        ),
        decision_case(
            "pilot_summary_needs_redaction",
            "redaction_required",
            "pilot_session_summary",
            "redaction_receipt",
            "rewrite the summary without raw transcript, participant identity, private rows, or source details",
        ),
        decision_case(
            "usage_trace_aggregate_only",
            "aggregate_projection_only",
            "local_usage_trace_event",
            "sanitized_projection_rebuild",
            "rebuild aggregate local metrics and keep no raw prompt, credential, or private row content",
        ),
        decision_case(
            "source_connector_raw_preview_requested",
            "blocked_raw_retention",
            "source_connector_result",
            "redaction_receipt",
            "store metadata, hashes, and normalized fields only; block raw preview retention",
        ),
        decision_case(
            "physical_delete_missing_legal_basis",
            "blocked_missing_gate",
            "pilot_session_summary",
            "physical_delete_exception",
            "fall back to redaction receipt until every physical-delete exception gate is documented",
            gate_coverage=["tenant_workspace_scope_verified", "record_class_allows_physical_delete"],
        ),
        decision_case(
            "physical_delete_with_authorized_erasure",
            "exception_preflight_ready",
            "pilot_session_summary",
            "physical_delete_exception",
            "future effectful runtime may execute only after retaining tombstone and redaction receipts",
            gate_coverage=PHYSICAL_DELETE_GATES,
            physically_deletes_records=True,
        ),
        decision_case(
            "physical_delete_for_forecast_history",
            "blocked_record_class",
            "forecast_lifecycle_record",
            "retain_append_only",
            "preserve immutable forecast history or render affected forecasts explicitly unscorable",
            gate_coverage=["record_class_allows_physical_delete"],
        ),
        decision_case(
            "redaction_receipt_replay",
            "idempotent_replay",
            "credential_reference_record",
            "redaction_receipt",
            "return the existing redaction receipt instead of writing a duplicate receipt",
        ),
        decision_case(
            "tombstone_rebuild_read_model",
            "projection_rebuild_only",
            "source_binding_config",
            "sanitized_projection_rebuild",
            "rebuild active read models from retained tombstones without changing immutable records",
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    rows = [
        ("cli", "python3 scripts/ope.py retention-redaction-policy", "Prints this checked retention/redaction policy."),
        ("lifecycle_operation_store", "python3 scripts/ope.py lifecycle-operation-store", "Provides archive, redaction, receipt, and no-physical-delete lifecycle evidence."),
        ("persistent_sqlite_policy", "python3 scripts/ope.py persistent-sqlite-policy", "Keeps physical delete disabled for default and normal-check storage paths."),
        ("runtime_security", "python3 scripts/ope.py runtime-security", "Blocks physical delete, credential values, raw SQL, and raw file layout exposure."),
        ("workspace_tenant_isolation", "python3 scripts/ope.py workspace-tenant-isolation", "Scopes any future erasure preflight to tenant and workspace ownership."),
        ("pilot_summary_intake", "python3 scripts/ope.py pilot-summary-intake", "Classifies summaries that need redaction or block raw transcripts and private data."),
        ("credential_reference_policy", "python3 scripts/ope.py credential-reference-policy", "Requires redaction receipts for unsafe credential-like submissions."),
    ]
    return [
        {
            "readbackSurface": surface,
            "command": command,
            "mutatesState": False,
            "physicallyDeletesRecords": False,
            "notes": notes,
        }
        for surface, command, notes in rows
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksPhysicallyDelete": False,
        "normalChecksWriteState": False,
        "silentDeleteAllowed": False,
        "forecastHistoryRewriteAllowed": False,
        "credentialValuesRetained": False,
        "rawPrivateRowsRetained": False,
        "rawPilotTranscriptsRetained": False,
        "physicalDeleteDefaultEnabled": False,
        "hostedErasureWorkflowImplemented": False,
        "qualityClaimsUpgraded": False,
    }


def build_source_bindings() -> dict[str, Any]:
    lifecycle_store = build_lifecycle_operation_store()
    persistent_sqlite = build_persistent_sqlite_policy()
    runtime_security = build_runtime_security()
    workspace_isolation = build_workspace_tenant_isolation()
    pilot_summary = build_pilot_summary_intake()
    credential_policy = build_credential_reference_policy()
    physical_deletes = sum(item["physicalDeletes"] for item in lifecycle_store["runtimeScenarios"])
    return {
        "lifecycleOperationStoreStatus": lifecycle_store["storeStatus"],
        "persistentSqlitePolicyStatus": persistent_sqlite["policyStatus"],
        "runtimeSecurityStatus": "runtime_security_checked",
        "workspaceTenantIsolationStatus": workspace_isolation["isolationStatus"],
        "pilotSummaryIntakeStatus": pilot_summary["intakeMode"],
        "credentialReferencePolicyStatus": credential_policy["policyStatus"],
        "normalChecksWriteState": False,
        "physicalDeletesInLifecycleScenarios": physical_deletes,
        "notes": "Policy binds existing lifecycle, storage, security, tenant, pilot, and credential readbacks without executing deletion.",
    }


def build_retention_redaction_policy() -> dict[str, Any]:
    classes = retention_classes()
    actions = policy_actions()
    gates = physical_delete_gates()
    cases = decision_cases()
    exception_cases = sum(1 for item in cases if item["selectedAction"] == "physical_delete_exception")
    blocked_physical_delete_cases = sum(1 for item in cases if item["caseStatus"].startswith("blocked_"))
    record = {
        "retentionRedactionPolicyId": "retentionredactionpolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "retention_redaction_policy_checked",
        "decisionStatus": "tombstones_and_redaction_receipts_default_physical_delete_exception_only",
        "normalChecksMutateState": False,
        "physicalDeleteDefaultEnabled": False,
        "sourceBindings": build_source_bindings(),
        "retentionClasses": classes,
        "policyActions": actions,
        "physicalDeleteGates": gates,
        "decisionCases": cases,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "retentionClassCount": len(classes),
            "policyActionCount": len(actions),
            "decisionCaseCount": len(cases),
            "physicalDeleteGateCount": len(gates),
            "readbackCount": len(READBACKS),
            "normalChecksMutateState": False,
            "physicalDeleteDefaultEnabled": False,
            "physicalDeleteExceptionCaseCount": exception_cases,
            "blockedPhysicalDeleteCaseCount": blocked_physical_delete_cases,
        },
        "warnings": [
            "Archive tombstones and redaction receipts are the default delete replacements for OPE records.",
            "Rare physical deletion is an exception preflight only and is not implemented as a normal-check or hosted workflow.",
            "Immutable forecast histories are preserved; if required evidence is removed, affected forecasts must become explicitly unscorable rather than silently rewritten.",
        ],
    }
    validate_retention_redaction_policy(record)
    return record


def validate_retention_redaction_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise RetentionRedactionPolicyError(f"retention redaction policy schema validation failed: {errors[0]}")
    if [item["recordClass"] for item in record["retentionClasses"]] != RETENTION_CLASSES:
        raise RetentionRedactionPolicyError("retention class order drifted")
    if [item["actionName"] for item in record["policyActions"]] != POLICY_ACTIONS:
        raise RetentionRedactionPolicyError("policy action order drifted")
    if [item["gateName"] for item in record["physicalDeleteGates"]] != PHYSICAL_DELETE_GATES:
        raise RetentionRedactionPolicyError("physical delete gate order drifted")
    if [item["caseName"] for item in record["decisionCases"]] != POLICY_CASES:
        raise RetentionRedactionPolicyError("decision case order drifted")
    if [item["readbackSurface"] for item in record["readbacks"]] != READBACKS:
        raise RetentionRedactionPolicyError("readback order drifted")
    for item in record["retentionClasses"]:
        if item["silentDeleteAllowed"] or item["normalChecksWriteState"]:
            raise RetentionRedactionPolicyError("retention classes must stay non-mutating and non-silent-delete")
        if item["retainCredentialValues"]:
            raise RetentionRedactionPolicyError("retention classes must not retain credential values")
    for item in record["policyActions"]:
        if item["normalChecksExecuteAction"] or item["silentDeleteAllowed"]:
            raise RetentionRedactionPolicyError("policy actions must not execute during normal checks or allow silent delete")
        if item["actionName"] != "physical_delete_exception" and item["physicallyDeletesRecords"]:
            raise RetentionRedactionPolicyError("only the physical delete exception action can physically delete")
    for item in record["physicalDeleteGates"]:
        if not item["requiredForException"] or item["normalChecksEvaluateAsEffectful"]:
            raise RetentionRedactionPolicyError("physical delete gates must be required and non-effectful in readbacks")
    for item in record["decisionCases"]:
        if item["normalChecksWriteState"] or item["credentialValuesRetained"] or not item["sanitizedDiagnosticsOnly"]:
            raise RetentionRedactionPolicyError("decision cases must be sanitized and non-mutating")
        if item["selectedAction"] != "physical_delete_exception" and item["physicallyDeletesRecords"]:
            raise RetentionRedactionPolicyError("non-exception cases must not physically delete")
    for item in record["readbacks"]:
        if item["mutatesState"] or item["physicallyDeletesRecords"]:
            raise RetentionRedactionPolicyError("readbacks must not mutate or physically delete records")
    for key, value in record["executionBoundary"].items():
        if value is not False:
            raise RetentionRedactionPolicyError(f"execution boundary {key} should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBindings"]
    if view == "classes":
        return record["retentionClasses"]
    if view == "actions":
        return record["policyActions"]
    if view == "gates":
        return record["physicalDeleteGates"]
    if view == "cases":
        return record["decisionCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise RetentionRedactionPolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated retention/redaction policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated retention/redaction policy fixture")
    parser.add_argument("--record-class", choices=RETENTION_CLASSES, help="print one retention class policy")
    parser.add_argument("--action", choices=POLICY_ACTIONS, help="print one retention/redaction policy action")
    parser.add_argument("--gate", choices=PHYSICAL_DELETE_GATES, help="print one physical-delete exception gate")
    parser.add_argument("--case", choices=POLICY_CASES, help="print one retention/redaction policy case")
    parser.add_argument(
        "--view",
        choices=["full", "source", "classes", "actions", "gates", "cases", "readbacks", "boundary", "summary"],
        default="full",
        help="print a focused retention/redaction policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_retention_redaction_policy()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="retention redaction policy",
            regen="python3 scripts/generate_retention_redaction_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="retention redaction policy",
            regen="python3 scripts/generate_retention_redaction_policy.py --write",
        )
        return
    if args.record_class:
        payload: Any = next(item for item in record["retentionClasses"] if item["recordClass"] == args.record_class)
    elif args.action:
        payload = next(item for item in record["policyActions"] if item["actionName"] == args.action)
    elif args.gate:
        payload = next(item for item in record["physicalDeleteGates"] if item["gateName"] == args.gate)
    elif args.case:
        payload = next(item for item in record["decisionCases"] if item["caseName"] == args.case)
    else:
        payload = view_payload(record, args.view)
    sys.stdout.write(render_json(payload))


if __name__ == "__main__":
    main()
