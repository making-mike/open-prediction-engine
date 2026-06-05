#!/usr/bin/env python3
"""Check workspace tenant isolation policy invariants."""

from __future__ import annotations

try:
    from generate_workspace_tenant_isolation import build_workspace_tenant_isolation
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("workspace tenant isolation generator is missing") from exc


SCOPE_KEYS = [
    "tenant_id",
    "workspace_id",
    "prediction_id",
    "source_binding_id",
    "operation_idempotency_namespace",
]

QUEUE_POLICIES = [
    "active_predictions",
    "due_forecasts",
    "due_resolutions",
    "blocked_operations",
    "failed_operations",
    "source_health_blockers",
    "calibration_progress",
    "track_record_progress",
]

SOURCE_POLICIES = [
    "tenant_owned_source_binding",
    "cross_tenant_source_clone_requires_new_binding",
    "credential_reference_tenant_owned",
    "sanitized_source_diagnostics_only",
    "private_payload_not_in_records",
]

ACCESS_CASES = [
    "same_tenant_workspace_read",
    "cross_tenant_prediction_read",
    "cross_workspace_source_binding_reuse",
    "cross_tenant_queue_peek",
    "idempotency_namespace_collision",
    "credential_reference_other_tenant",
    "admin_override_without_audit",
]

READBACKS = [
    "cli",
    "prediction_workspace_registry",
    "internal_api",
    "runtime_security",
    "runtime_transport_readiness",
    "database_source_adapter_runtime",
    "lifecycle_lease_policy",
]

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksWriteState",
    "hostedTenantRuntimeImplemented",
    "crossTenantReadAllowed",
    "crossTenantSourceReuseAllowed",
    "crossTenantQueueScanAllowed",
    "credentialValuesStored",
    "rawPrivateRowsStored",
    "networkListenerStarted",
    "rawCrudExposed",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    isolation = build_workspace_tenant_isolation()

    require(isolation["isolationStatus"] == "workspace_tenant_isolation_checked", "isolation status drifted")
    require(
        isolation["decisionStatus"] == "tenant_scoped_workspaces_with_resource_source_and_queue_isolation",
        "decision status drifted",
    )
    require(isolation["normalChecksMutateState"] is False, "normal checks must not mutate tenant state")
    require(isolation["hostedTenantRuntimeImplemented"] is False, "hosted tenant runtime must remain unimplemented")

    source = isolation["sourceBinding"]
    require(source["sourceSurface"] == "prediction_workspace_registry", "source surface drifted")
    require(source["sourceCommand"] == "python3 scripts/ope.py prediction-workspace-registry", "source command drifted")
    require(source["sourceRegistryId"] == "workspace-registry-001", "source registry binding drifted")
    require(source["sourceWorkspaceId"] == "opeworkspace-001", "source workspace binding drifted")
    require(source["rawRegistryMutationAllowed"] is False, "source binding must not allow raw registry mutation")

    tenant_workspaces = isolation["tenantWorkspaceBindings"]
    require(len(tenant_workspaces) == 2, "tenant isolation should include two checked workspace bindings")
    require(len({item["tenantId"] for item in tenant_workspaces}) == len(tenant_workspaces), "tenant IDs should be unique")
    require(
        len({item["workspaceId"] for item in tenant_workspaces}) == len(tenant_workspaces),
        "tenant workspace IDs should be unique",
    )
    require(
        len({item["idempotencyNamespacePrefix"] for item in tenant_workspaces}) == len(tenant_workspaces),
        "idempotency namespace prefixes should be tenant-unique",
    )
    require(
        len({item["credentialScopeId"] for item in tenant_workspaces}) == len(tenant_workspaces),
        "credential scopes should be tenant-unique",
    )
    prediction_ids = set()
    source_binding_ids = set()
    queue_refs = set()
    for item in tenant_workspaces:
        require(item["tenantId"].startswith("tenant-"), "tenant IDs should use the tenant namespace")
        require(item["workspaceId"].startswith("opeworkspace-"), "workspace IDs should use the workspace namespace")
        require(item["owner"]["ownerId"], "tenant workspace should include owner metadata")
        require(item["resourcePolicyId"], "tenant workspace should include a resource policy")
        require(item["credentialScopeId"], "tenant workspace should include a credential scope")
        require(item["rawSqlExposed"] is False, "tenant workspace must not expose raw SQL")
        require(item["rawPrivateRowsExposed"] is False, "tenant workspace must not expose raw private rows")
        for prediction_id in item["predictionIds"]:
            require(prediction_id not in prediction_ids, "prediction IDs should not cross tenant workspaces")
            prediction_ids.add(prediction_id)
        for source_binding_id in item["sourceBindingIds"]:
            require(source_binding_id not in source_binding_ids, "source bindings should not cross tenant workspaces")
            source_binding_ids.add(source_binding_id)
        for queue_ref in item["operationQueueRefs"]:
            require(queue_ref not in queue_refs, "operation queue refs should not cross tenant workspaces")
            queue_refs.add(queue_ref)

    model = isolation["isolationModel"]
    for key in [
        "tenantIdRequired",
        "workspaceIdRequired",
        "predictionIdsTenantScoped",
        "sourceBindingsTenantScoped",
        "operationQueuesTenantScoped",
        "idempotencyNamespacesTenantScoped",
        "credentialReferencesTenantScoped",
        "crossTenantReadsBlocked",
        "crossTenantWritesBlocked",
        "sanitizedDiagnosticsOnly",
        "auditRequiredForAdministrativeOverride",
    ]:
        require(model[key] is True, f"isolation model should set {key}")

    scope_keys = {item["scopeKeyName"]: item for item in isolation["scopeKeys"]}
    require(list(scope_keys) == SCOPE_KEYS, "scope key order drifted")
    for item in scope_keys.values():
        require(item["requiredForLookup"] is True, f"{item['scopeKeyName']} should be required for lookup")
        require(item["includedInAudit"] is True, f"{item['scopeKeyName']} should be included in audit")
        require(item["rawValuePublic"] is False, f"{item['scopeKeyName']} should not expose raw values publicly")

    resource_controls = {item["tenantId"]: item for item in isolation["tenantResourceControls"]}
    require(set(resource_controls) == {item["tenantId"] for item in tenant_workspaces}, "resource controls should cover tenants")
    for item in resource_controls.values():
        require(item["currentActivePredictions"] <= item["maximumActivePredictions"], "active prediction tenant limit exceeded")
        require(item["currentQueuedOperations"] <= item["maximumQueuedOperations"], "queued operation tenant limit exceeded")
        require(item["currentReadbackBytes"] <= item["maximumReadbackBytes"], "readback byte tenant limit exceeded")
        require(item["resourceStatus"] in {"within_limits", "blocked"}, "resource status drifted")
        require(item["rawLimitMutationAllowed"] is False, "resource controls must not allow raw limit mutation")

    queue_policies = {item["queueName"]: item for item in isolation["operationQueuePolicies"]}
    require(list(queue_policies) == QUEUE_POLICIES, "operation queue policy order drifted")
    for item in queue_policies.values():
        require(item["tenantScoped"] is True, f"{item['queueName']} should be tenant-scoped")
        require(item["workspaceScoped"] is True, f"{item['queueName']} should be workspace-scoped")
        require(item["crossTenantPeekAllowed"] is False, f"{item['queueName']} must block cross-tenant peek")
        require(item["rawQueueCrudExposed"] is False, f"{item['queueName']} must not expose raw queue CRUD")
        require(item["sanitizedDiagnosticsOnly"] is True, f"{item['queueName']} diagnostics should be sanitized")

    source_policies = {item["policyName"]: item for item in isolation["sourceBindingPolicies"]}
    require(list(source_policies) == SOURCE_POLICIES, "source binding policy order drifted")
    for item in source_policies.values():
        require(item["tenantScoped"] is True, f"{item['policyName']} should be tenant-scoped")
        require(item["workspaceScoped"] is True, f"{item['policyName']} should be workspace-scoped")
        require(item["credentialValuesStored"] is False, f"{item['policyName']} must not store credential values")
        require(item["rawPrivateRowsStored"] is False, f"{item['policyName']} must not store raw private rows")

    cases = {item["caseName"]: item for item in isolation["accessCases"]}
    require(list(cases) == ACCESS_CASES, "tenant access case order drifted")
    require(cases["same_tenant_workspace_read"]["caseStatus"] == "accepted_same_tenant_workspace", "accepted case drifted")
    for case_name in ACCESS_CASES[1:]:
        case = cases[case_name]
        require(case["caseStatus"].startswith("blocked_"), f"{case_name} should be blocked")
        require(case["accessAllowed"] is False, f"{case_name} must not allow access")
        require(case["operationReceiptsWritten"] is False, f"{case_name} must not write receipts")
        require(case["immutableRecordsWritten"] is False, f"{case_name} must not write records")
        require(case["credentialValuesStored"] is False, f"{case_name} must not store credentials")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case_name} diagnostics should be sanitized")

    readbacks = {item["readbackSurface"]: item for item in isolation["readbacks"]}
    require(list(readbacks) == READBACKS, "readback order drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py workspace-tenant-isolation", "CLI readback command drifted")
    for item in readbacks.values():
        require(item["mutatesState"] is False, "readbacks must not mutate state")
        require(item["startsNetworkListener"] is False, "readbacks must not start network listeners")
        require(item["credentialValuesReturned"] is False, "readbacks must not return credential values")

    boundary = isolation["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")
    require(not any(boundary.values()), "execution boundary flags should all stay false")

    summary = isolation["summary"]
    require(summary["tenantWorkspaceCount"] == len(tenant_workspaces), "tenant workspace count drifted")
    require(summary["scopeKeyCount"] == len(SCOPE_KEYS), "scope key count drifted")
    require(summary["queuePolicyCount"] == len(QUEUE_POLICIES), "queue policy count drifted")
    require(summary["sourcePolicyCount"] == len(SOURCE_POLICIES), "source policy count drifted")
    require(summary["accessCaseCount"] == len(ACCESS_CASES), "access case count drifted")
    require(summary["blockedAccessCaseCount"] == len(ACCESS_CASES) - 1, "blocked access case count drifted")
    require(summary["normalChecksMutateState"] is False, "summary normal-check mutation flag drifted")
    require(summary["hostedTenantRuntimeImplemented"] is False, "summary hosted tenant runtime flag drifted")

    print("checked workspace tenant isolation")


if __name__ == "__main__":
    main()
