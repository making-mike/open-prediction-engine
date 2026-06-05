#!/usr/bin/env python3
"""Check retention, redaction, tombstone, and physical-delete policy boundaries."""

from __future__ import annotations

try:
    from generate_retention_redaction_policy import build_retention_redaction_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("retention redaction policy generator is missing") from exc


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

READBACKS = [
    "cli",
    "lifecycle_operation_store",
    "persistent_sqlite_policy",
    "runtime_security",
    "workspace_tenant_isolation",
    "pilot_summary_intake",
    "credential_reference_policy",
]

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksPhysicallyDelete",
    "normalChecksWriteState",
    "silentDeleteAllowed",
    "forecastHistoryRewriteAllowed",
    "credentialValuesRetained",
    "rawPrivateRowsRetained",
    "rawPilotTranscriptsRetained",
    "physicalDeleteDefaultEnabled",
    "hostedErasureWorkflowImplemented",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_retention_redaction_policy()

    require(policy["policyStatus"] == "retention_redaction_policy_checked", "policy status drifted")
    require(
        policy["decisionStatus"] == "tombstones_and_redaction_receipts_default_physical_delete_exception_only",
        "decision status drifted",
    )
    require(policy["normalChecksMutateState"] is False, "normal checks must not mutate state")
    require(policy["physicalDeleteDefaultEnabled"] is False, "physical delete must not be default")

    sources = policy["sourceBindings"]
    require(sources["lifecycleOperationStoreStatus"] == "local_sqlite_runtime_checked", "lifecycle source drifted")
    require(sources["persistentSqlitePolicyStatus"] == "persistent_sqlite_path_policy_checked", "persistent policy source drifted")
    require(sources["runtimeSecurityStatus"] == "runtime_security_checked", "runtime security source drifted")
    require(sources["credentialReferencePolicyStatus"] == "credential_reference_policy_checked", "credential source drifted")
    require(sources["normalChecksWriteState"] is False, "source bindings must stay read-only")
    require(sources["physicalDeletesInLifecycleScenarios"] == 0, "lifecycle scenarios must not physically delete")

    classes = {item["recordClass"]: item for item in policy["retentionClasses"]}
    require(list(classes) == RETENTION_CLASSES, "retention class order drifted")
    require(classes["forecast_lifecycle_record"]["defaultAction"] == "retain_append_only", "forecast lifecycle default drifted")
    require(classes["forecast_lifecycle_record"]["physicalDeleteEligible"] is False, "forecast lifecycle should not be physically deleted")
    require(classes["credential_reference_record"]["retainCredentialValues"] is False, "credential values must not be retained")
    require(classes["pilot_session_summary"]["rawContentRetained"] is False, "pilot raw content must not be retained")
    require(classes["local_usage_trace_event"]["aggregateOnlyAfterWindow"] is True, "usage traces should aggregate after window")
    for item in classes.values():
        require(item["auditMetadataRetained"] is True, f"{item['recordClass']} should retain audit metadata")
        require(item["silentDeleteAllowed"] is False, f"{item['recordClass']} must not allow silent delete")
        require(item["normalChecksWriteState"] is False, f"{item['recordClass']} readback must not write state")

    actions = {item["actionName"]: item for item in policy["policyActions"]}
    require(list(actions) == POLICY_ACTIONS, "policy action order drifted")
    require(actions["retain_append_only"]["writesAuditTombstone"] is False, "retain action should not tombstone")
    require(actions["archive_tombstone"]["writesAuditTombstone"] is True, "archive should write tombstone")
    require(actions["redaction_receipt"]["writesRedactionReceipt"] is True, "redaction should write receipt")
    require(actions["physical_delete_exception"]["requiresAllPhysicalDeleteGates"] is True, "physical delete should require all gates")
    for name, item in actions.items():
        require(item["normalChecksExecuteAction"] is False, f"{name} must not execute in normal checks")
        require(item["silentDeleteAllowed"] is False, f"{name} must not allow silent delete")
        if name != "physical_delete_exception":
            require(item["physicallyDeletesRecords"] is False, f"{name} must not physically delete")

    gates = {item["gateName"]: item for item in policy["physicalDeleteGates"]}
    require(list(gates) == PHYSICAL_DELETE_GATES, "physical delete gate order drifted")
    require(gates["record_class_allows_physical_delete"]["blocksForecastHistory"] is True, "gate should block forecast history")
    require(gates["audit_tombstone_retained"]["requiredForException"] is True, "audit tombstone should be required")
    require(gates["redaction_receipt_retained"]["requiredForException"] is True, "redaction receipt should be required")
    for item in gates.values():
        require(item["requiredForException"] is True, f"{item['gateName']} should be required")
        require(item["normalChecksEvaluateAsEffectful"] is False, f"{item['gateName']} should stay non-effectful")

    cases = {item["caseName"]: item for item in policy["decisionCases"]}
    require(list(cases) == POLICY_CASES, "decision case order drifted")
    require(cases["normal_forecast_lifecycle_retention"]["caseStatus"] == "retained_append_only", "normal retention drifted")
    require(cases["archive_inactive_prediction"]["selectedAction"] == "archive_tombstone", "archive action drifted")
    require(cases["redact_private_source_detail"]["selectedAction"] == "redaction_receipt", "private redaction action drifted")
    require(cases["redact_credential_like_field"]["selectedAction"] == "redaction_receipt", "credential redaction action drifted")
    require(cases["source_connector_raw_preview_requested"]["caseStatus"] == "blocked_raw_retention", "raw preview case drifted")
    require(cases["physical_delete_missing_legal_basis"]["caseStatus"] == "blocked_missing_gate", "missing legal basis should block")
    require(cases["physical_delete_with_authorized_erasure"]["caseStatus"] == "exception_preflight_ready", "authorized erasure case drifted")
    require(cases["physical_delete_for_forecast_history"]["caseStatus"] == "blocked_record_class", "forecast physical delete should block")
    require(cases["redaction_receipt_replay"]["caseStatus"] == "idempotent_replay", "redaction replay should be idempotent")
    require(cases["tombstone_rebuild_read_model"]["caseStatus"] == "projection_rebuild_only", "tombstone rebuild case drifted")
    for item in cases.values():
        require(item["normalChecksWriteState"] is False, f"{item['caseName']} must not write state")
        require(item["sanitizedDiagnosticsOnly"] is True, f"{item['caseName']} should keep diagnostics sanitized")
        require(item["credentialValuesRetained"] is False, f"{item['caseName']} must not retain credentials")
        if item["selectedAction"] != "physical_delete_exception":
            require(item["physicallyDeletesRecords"] is False, f"{item['caseName']} must not physically delete")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(list(readbacks) == READBACKS, "readback order drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py retention-redaction-policy", "CLI readback drifted")
    for item in readbacks.values():
        require(item["mutatesState"] is False, f"{item['readbackSurface']} must not mutate state")
        require(item["physicallyDeletesRecords"] is False, f"{item['readbackSurface']} must not physically delete")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = policy["summary"]
    require(summary["retentionClassCount"] == len(RETENTION_CLASSES), "retention class count drifted")
    require(summary["policyActionCount"] == len(POLICY_ACTIONS), "action count drifted")
    require(summary["decisionCaseCount"] == len(POLICY_CASES), "case count drifted")
    require(summary["physicalDeleteGateCount"] == len(PHYSICAL_DELETE_GATES), "gate count drifted")
    require(summary["readbackCount"] == len(READBACKS), "readback count drifted")
    require(summary["normalChecksMutateState"] is False, "summary mutation flag drifted")
    require(summary["physicalDeleteDefaultEnabled"] is False, "summary physical delete default drifted")

    print("checked retention redaction policy")


if __name__ == "__main__":
    main()
