#!/usr/bin/env python3
"""Generate a checked workspace tenant isolation readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_prediction_workspace_registry import build_prediction_workspace_registry
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "workspace-tenant-isolation"
OUTPUT_PATH = GENERATED / "ope-workspace-tenant-isolation.generated.json"
SCHEMA = SPEC / "workspace-tenant-isolation.schema.json"
GENERATED_AT = "2026-06-04T23:59:30Z"

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


class WorkspaceTenantIsolationError(Exception):
    pass


def tenant_workspace_binding(
    *,
    tenant_id: str,
    workspace_id: str,
    workspace_status: str,
    owner_id: str,
    owner_type: str,
    contact_ref: str,
    prediction_ids: list[str],
    source_binding_ids: list[str],
    operation_queue_refs: list[str],
    idempotency_namespace_prefix: str,
    resource_policy_id: str,
    credential_scope_id: str,
) -> dict[str, Any]:
    return {
        "tenantId": tenant_id,
        "workspaceId": workspace_id,
        "workspaceStatus": workspace_status,
        "owner": {
            "ownerId": owner_id,
            "ownerType": owner_type,
            "contactRef": contact_ref,
        },
        "predictionIds": prediction_ids,
        "sourceBindingIds": source_binding_ids,
        "operationQueueRefs": operation_queue_refs,
        "idempotencyNamespacePrefix": idempotency_namespace_prefix,
        "resourcePolicyId": resource_policy_id,
        "credentialScopeId": credential_scope_id,
        "rawSqlExposed": False,
        "rawPrivateRowsExposed": False,
    }


def tenant_workspace_bindings() -> list[dict[str, Any]]:
    return [
        tenant_workspace_binding(
            tenant_id="tenant-001",
            workspace_id="opeworkspace-001",
            workspace_status="active",
            owner_id="operatorlocal-001",
            owner_type="team",
            contact_ref="local-operator-record",
            prediction_ids=["prediction-001"],
            source_binding_ids=["sourcebinding-001"],
            operation_queue_refs=[
                "queueactive-001",
                "queuedueforecast-001",
                "queuedueresolution-001",
                "queuecalibration-001",
            ],
            idempotency_namespace_prefix="tenant-001/opeworkspace-001",
            resource_policy_id="resourcepolicy-001",
            credential_scope_id="credentialscope-001",
        ),
        tenant_workspace_binding(
            tenant_id="tenant-002",
            workspace_id="opeworkspace-002",
            workspace_status="paused",
            owner_id="serviceops-001",
            owner_type="service",
            contact_ref="ops-service-record",
            prediction_ids=["prediction-002"],
            source_binding_ids=["sourcebinding-002"],
            operation_queue_refs=[
                "queueactive-002",
                "queueblocked-002",
                "queuefailed-002",
                "queuesourcehealth-002",
            ],
            idempotency_namespace_prefix="tenant-002/opeworkspace-002",
            resource_policy_id="resourcepolicy-002",
            credential_scope_id="credentialscope-002",
        ),
    ]


def isolation_model() -> dict[str, bool]:
    return {
        "tenantIdRequired": True,
        "workspaceIdRequired": True,
        "predictionIdsTenantScoped": True,
        "sourceBindingsTenantScoped": True,
        "operationQueuesTenantScoped": True,
        "idempotencyNamespacesTenantScoped": True,
        "credentialReferencesTenantScoped": True,
        "crossTenantReadsBlocked": True,
        "crossTenantWritesBlocked": True,
        "sanitizedDiagnosticsOnly": True,
        "auditRequiredForAdministrativeOverride": True,
    }


def scope_key(name: str, source_field: str, notes: str) -> dict[str, Any]:
    return {
        "scopeKeyName": name,
        "sourceField": source_field,
        "requiredForLookup": True,
        "includedInAudit": True,
        "rawValuePublic": False,
        "notes": notes,
    }


def scope_keys() -> list[dict[str, Any]]:
    return [
        scope_key("tenant_id", "tenantId", "Every workspace readback and write preflight must bind a tenant."),
        scope_key("workspace_id", "workspaceId", "Workspace ID separates tenant-local prediction definitions and queues."),
        scope_key("prediction_id", "predictionId", "Prediction IDs are resolved only inside a tenant/workspace scope."),
        scope_key("source_binding_id", "sourceBindingId", "Source bindings remain tenant/workspace-owned and cannot be reused raw."),
        scope_key(
            "operation_idempotency_namespace",
            "idempotencyNamespacePrefix",
            "Idempotency keys include the tenant/workspace namespace before operation-specific keys.",
        ),
    ]


def tenant_resource_control(
    *,
    tenant_id: str,
    workspace_id: str,
    resource_policy_id: str,
    maximum_active_predictions: int,
    current_active_predictions: int,
    maximum_queued_operations: int,
    current_queued_operations: int,
    maximum_readback_bytes: int,
    current_readback_bytes: int,
    maximum_source_bindings: int,
    current_source_bindings: int,
    max_runtime_seconds_per_tick: int,
    resource_status: str,
) -> dict[str, Any]:
    return {
        "tenantId": tenant_id,
        "workspaceId": workspace_id,
        "resourcePolicyId": resource_policy_id,
        "maximumActivePredictions": maximum_active_predictions,
        "currentActivePredictions": current_active_predictions,
        "maximumQueuedOperations": maximum_queued_operations,
        "currentQueuedOperations": current_queued_operations,
        "maximumReadbackBytes": maximum_readback_bytes,
        "currentReadbackBytes": current_readback_bytes,
        "maximumSourceBindings": maximum_source_bindings,
        "currentSourceBindings": current_source_bindings,
        "maxRuntimeSecondsPerTick": max_runtime_seconds_per_tick,
        "resourceStatus": resource_status,
        "rawLimitMutationAllowed": False,
    }


def tenant_resource_controls() -> list[dict[str, Any]]:
    return [
        tenant_resource_control(
            tenant_id="tenant-001",
            workspace_id="opeworkspace-001",
            resource_policy_id="resourcepolicy-001",
            maximum_active_predictions=8,
            current_active_predictions=1,
            maximum_queued_operations=32,
            current_queued_operations=3,
            maximum_readback_bytes=65536,
            current_readback_bytes=12288,
            maximum_source_bindings=8,
            current_source_bindings=1,
            max_runtime_seconds_per_tick=30,
            resource_status="within_limits",
        ),
        tenant_resource_control(
            tenant_id="tenant-002",
            workspace_id="opeworkspace-002",
            resource_policy_id="resourcepolicy-002",
            maximum_active_predictions=4,
            current_active_predictions=0,
            maximum_queued_operations=16,
            current_queued_operations=2,
            maximum_readback_bytes=32768,
            current_readback_bytes=8192,
            maximum_source_bindings=4,
            current_source_bindings=1,
            max_runtime_seconds_per_tick=15,
            resource_status="blocked",
        ),
    ]


def operation_queue_policy(queue_name: str) -> dict[str, Any]:
    return {
        "queueName": queue_name,
        "queueScopeKeyTemplate": f"{{tenantId}}:{{workspaceId}}:{queue_name}",
        "tenantScoped": True,
        "workspaceScoped": True,
        "readModelOnly": True,
        "crossTenantPeekAllowed": False,
        "rawQueueCrudExposed": False,
        "sanitizedDiagnosticsOnly": True,
        "nextAction": "read scoped workspace status or request an audited internal API operation",
    }


def operation_queue_policies() -> list[dict[str, Any]]:
    return [operation_queue_policy(name) for name in QUEUE_POLICIES]


def source_binding_policy(
    policy_name: str,
    *,
    cross_tenant_reuse_allowed: bool,
    cloning_requires_new_binding: bool,
    safe_next_action: str,
) -> dict[str, Any]:
    return {
        "policyName": policy_name,
        "tenantScoped": True,
        "workspaceScoped": True,
        "crossTenantReuseAllowed": cross_tenant_reuse_allowed,
        "cloningRequiresNewBinding": cloning_requires_new_binding,
        "credentialValuesStored": False,
        "rawPrivateRowsStored": False,
        "sanitizedDiagnosticsOnly": True,
        "safeNextAction": safe_next_action,
    }


def source_binding_policies() -> list[dict[str, Any]]:
    return [
        source_binding_policy(
            "tenant_owned_source_binding",
            cross_tenant_reuse_allowed=False,
            cloning_requires_new_binding=False,
            safe_next_action="keep source binding lookup inside the tenant workspace",
        ),
        source_binding_policy(
            "cross_tenant_source_clone_requires_new_binding",
            cross_tenant_reuse_allowed=False,
            cloning_requires_new_binding=True,
            safe_next_action="create a new sanitized source binding under the target tenant",
        ),
        source_binding_policy(
            "credential_reference_tenant_owned",
            cross_tenant_reuse_allowed=False,
            cloning_requires_new_binding=False,
            safe_next_action="replace foreign credential references with a caller-owned reference",
        ),
        source_binding_policy(
            "sanitized_source_diagnostics_only",
            cross_tenant_reuse_allowed=False,
            cloning_requires_new_binding=False,
            safe_next_action="return diagnostic codes without source payloads or private row values",
        ),
        source_binding_policy(
            "private_payload_not_in_records",
            cross_tenant_reuse_allowed=False,
            cloning_requires_new_binding=False,
            safe_next_action="store only manifest, mapping, quality, provenance, and policy references",
        ),
    ]


def access_case(
    case_name: str,
    case_status: str,
    requested_resource_kind: str,
    safe_next_action: str,
    *,
    requesting_tenant_id: str = "tenant-001",
    target_tenant_id: str = "tenant-002",
    requesting_workspace_id: str = "opeworkspace-001",
    target_workspace_id: str = "opeworkspace-002",
    access_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": case_status,
        "requestingTenantId": requesting_tenant_id,
        "targetTenantId": target_tenant_id,
        "requestingWorkspaceId": requesting_workspace_id,
        "targetWorkspaceId": target_workspace_id,
        "requestedResourceKind": requested_resource_kind,
        "accessAllowed": access_allowed,
        "operationReceiptsWritten": False,
        "immutableRecordsWritten": False,
        "credentialValuesStored": False,
        "sanitizedDiagnosticsOnly": True,
        "safeNextAction": safe_next_action,
    }


def access_cases() -> list[dict[str, Any]]:
    return [
        access_case(
            "same_tenant_workspace_read",
            "accepted_same_tenant_workspace",
            "prediction",
            "return scoped compact workspace readback",
            requesting_tenant_id="tenant-001",
            target_tenant_id="tenant-001",
            requesting_workspace_id="opeworkspace-001",
            target_workspace_id="opeworkspace-001",
            access_allowed=True,
        ),
        access_case(
            "cross_tenant_prediction_read",
            "blocked_cross_tenant_prediction_read",
            "prediction",
            "ask the caller for the correct tenant workspace scope",
        ),
        access_case(
            "cross_workspace_source_binding_reuse",
            "blocked_cross_workspace_source_binding_reuse",
            "source_binding",
            "create a new source binding after explicit target-tenant approval",
        ),
        access_case(
            "cross_tenant_queue_peek",
            "blocked_cross_tenant_queue_peek",
            "operation_queue",
            "read only queue summaries scoped to the caller tenant workspace",
        ),
        access_case(
            "idempotency_namespace_collision",
            "blocked_idempotency_namespace_collision",
            "idempotency_namespace",
            "prefix the idempotency key with the tenant and workspace namespace",
        ),
        access_case(
            "credential_reference_other_tenant",
            "blocked_credential_reference_scope",
            "credential_reference",
            "request a caller-owned credential reference instead of reusing another tenant reference",
        ),
        access_case(
            "admin_override_without_audit",
            "blocked_admin_override_missing_audit",
            "admin_override",
            "require an audited administrative override record before scoped access changes",
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py workspace-tenant-isolation",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Prints the checked tenant isolation readback without writing workspace state.",
        },
        {
            "readbackSurface": "prediction_workspace_registry",
            "command": "python3 scripts/ope.py prediction-workspace-registry",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Source registry remains prediction/workspace scoped and readback-only.",
        },
        {
            "readbackSurface": "internal_api",
            "command": "python3 scripts/ope.py internal-api",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Future effectful tenant-aware operations must use internal API preflight and receipts.",
        },
        {
            "readbackSurface": "runtime_security",
            "command": "python3 scripts/ope.py runtime-security",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Runtime security keeps path, credential, and raw private data boundaries checked.",
        },
        {
            "readbackSurface": "runtime_transport_readiness",
            "command": "python3 scripts/ope.py runtime-transport-readiness",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Tenant isolation does not promote HTTP, hosted, queue, or provider runtimes.",
        },
        {
            "readbackSurface": "database_source_adapter_runtime",
            "command": "python3 scripts/ope.py database-source-adapter-runtime",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Database source adapter output stays sanitized and credential-reference-only.",
        },
        {
            "readbackSurface": "lifecycle_lease_policy",
            "command": "python3 scripts/ope.py lifecycle-lease-policy",
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": "Lease and idempotency policies include tenant/workspace scope before operation keys.",
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksWriteState": False,
        "hostedTenantRuntimeImplemented": False,
        "crossTenantReadAllowed": False,
        "crossTenantSourceReuseAllowed": False,
        "crossTenantQueueScanAllowed": False,
        "credentialValuesStored": False,
        "rawPrivateRowsStored": False,
        "networkListenerStarted": False,
        "rawCrudExposed": False,
        "qualityClaimsUpgraded": False,
    }


def build_workspace_tenant_isolation() -> dict[str, Any]:
    registry = build_prediction_workspace_registry()
    tenants = tenant_workspace_bindings()
    queues = operation_queue_policies()
    sources = source_binding_policies()
    cases = access_cases()
    blocked_cases = [item for item in cases if item["accessAllowed"] is False]
    record = {
        "workspaceTenantIsolationId": "workspacetenantisolation-001",
        "generatedAt": GENERATED_AT,
        "isolationStatus": "workspace_tenant_isolation_checked",
        "decisionStatus": "tenant_scoped_workspaces_with_resource_source_and_queue_isolation",
        "normalChecksMutateState": False,
        "hostedTenantRuntimeImplemented": False,
        "sourceBinding": {
            "sourceSurface": "prediction_workspace_registry",
            "sourceCommand": "python3 scripts/ope.py prediction-workspace-registry",
            "sourceRegistryId": registry["predictionWorkspaceRegistryId"],
            "sourceWorkspaceId": registry["workspaceId"],
            "rawRegistryMutationAllowed": False,
            "notes": "Tenant isolation is layered over the checked multi-prediction workspace registry.",
        },
        "tenantWorkspaceBindings": tenants,
        "isolationModel": isolation_model(),
        "scopeKeys": scope_keys(),
        "tenantResourceControls": tenant_resource_controls(),
        "operationQueuePolicies": queues,
        "sourceBindingPolicies": sources,
        "accessCases": cases,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "tenantWorkspaceCount": len(tenants),
            "scopeKeyCount": len(SCOPE_KEYS),
            "queuePolicyCount": len(queues),
            "sourcePolicyCount": len(sources),
            "accessCaseCount": len(cases),
            "blockedAccessCaseCount": len(blocked_cases),
            "tenantScopeRequired": True,
            "workspaceScopeRequired": True,
            "queueIsolationEnforced": True,
            "sourceBindingIsolationEnforced": True,
            "credentialReferenceIsolationEnforced": True,
            "normalChecksMutateState": False,
            "hostedTenantRuntimeImplemented": False,
        },
        "warnings": [
            "This is a checked isolation policy readback and does not implement hosted multitenancy.",
            "Tenant/workspace scope is required before reading prediction resources, source bindings, or operation queues.",
            "Cross-tenant source reuse requires a new sanitized binding and caller-owned credential reference.",
            "Normal checks write no state, start no network listener, and store no credential values or raw private rows.",
        ],
    }
    validate_workspace_tenant_isolation(record)
    return record


def _require_unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise WorkspaceTenantIsolationError(f"duplicate {label} in workspace tenant isolation")


def validate_workspace_tenant_isolation(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise WorkspaceTenantIsolationError(f"workspace tenant isolation schema validation failed: {errors[0]}")
    if [item["scopeKeyName"] for item in record["scopeKeys"]] != SCOPE_KEYS:
        raise WorkspaceTenantIsolationError("scope key order drifted")
    if [item["queueName"] for item in record["operationQueuePolicies"]] != QUEUE_POLICIES:
        raise WorkspaceTenantIsolationError("operation queue policy order drifted")
    if [item["policyName"] for item in record["sourceBindingPolicies"]] != SOURCE_POLICIES:
        raise WorkspaceTenantIsolationError("source binding policy order drifted")
    if [item["caseName"] for item in record["accessCases"]] != ACCESS_CASES:
        raise WorkspaceTenantIsolationError("access case order drifted")
    if [item["readbackSurface"] for item in record["readbacks"]] != READBACKS:
        raise WorkspaceTenantIsolationError("readback order drifted")

    tenants = record["tenantWorkspaceBindings"]
    _require_unique([item["tenantId"] for item in tenants], "tenantId")
    _require_unique([item["workspaceId"] for item in tenants], "workspaceId")
    _require_unique([item["idempotencyNamespacePrefix"] for item in tenants], "idempotencyNamespacePrefix")
    _require_unique([item["credentialScopeId"] for item in tenants], "credentialScopeId")

    seen_predictions: set[str] = set()
    seen_sources: set[str] = set()
    seen_queues: set[str] = set()
    tenant_ids = {item["tenantId"] for item in tenants}
    workspace_ids = {item["workspaceId"] for item in tenants}
    for item in tenants:
        if item["rawSqlExposed"] or item["rawPrivateRowsExposed"]:
            raise WorkspaceTenantIsolationError("tenant workspace bindings must not expose raw SQL or private rows")
        for prediction_id in item["predictionIds"]:
            if prediction_id in seen_predictions:
                raise WorkspaceTenantIsolationError("prediction IDs must not cross tenant workspaces")
            seen_predictions.add(prediction_id)
        for source_binding_id in item["sourceBindingIds"]:
            if source_binding_id in seen_sources:
                raise WorkspaceTenantIsolationError("source binding IDs must not cross tenant workspaces")
            seen_sources.add(source_binding_id)
        for queue_ref in item["operationQueueRefs"]:
            if queue_ref in seen_queues:
                raise WorkspaceTenantIsolationError("queue refs must not cross tenant workspaces")
            seen_queues.add(queue_ref)

    for item in record["tenantResourceControls"]:
        if item["tenantId"] not in tenant_ids or item["workspaceId"] not in workspace_ids:
            raise WorkspaceTenantIsolationError("resource controls must bind known tenant workspaces")
        if item["currentActivePredictions"] > item["maximumActivePredictions"]:
            raise WorkspaceTenantIsolationError("tenant active prediction resource limit exceeded")
        if item["currentQueuedOperations"] > item["maximumQueuedOperations"]:
            raise WorkspaceTenantIsolationError("tenant queued operation resource limit exceeded")
        if item["currentReadbackBytes"] > item["maximumReadbackBytes"]:
            raise WorkspaceTenantIsolationError("tenant readback byte resource limit exceeded")
        if item["currentSourceBindings"] > item["maximumSourceBindings"]:
            raise WorkspaceTenantIsolationError("tenant source binding resource limit exceeded")
        if item["rawLimitMutationAllowed"]:
            raise WorkspaceTenantIsolationError("resource controls must not allow raw limit mutation")

    for item in record["operationQueuePolicies"]:
        if not item["tenantScoped"] or not item["workspaceScoped"]:
            raise WorkspaceTenantIsolationError("operation queue policies must be tenant and workspace scoped")
        if item["crossTenantPeekAllowed"] or item["rawQueueCrudExposed"]:
            raise WorkspaceTenantIsolationError("operation queue policies must block cross-tenant peek and raw CRUD")
        if not item["sanitizedDiagnosticsOnly"]:
            raise WorkspaceTenantIsolationError("operation queue diagnostics must be sanitized")

    for item in record["sourceBindingPolicies"]:
        if not item["tenantScoped"] or not item["workspaceScoped"]:
            raise WorkspaceTenantIsolationError("source binding policies must be tenant and workspace scoped")
        if item["credentialValuesStored"] or item["rawPrivateRowsStored"]:
            raise WorkspaceTenantIsolationError("source binding policies must not store credentials or raw private rows")
        if item["crossTenantReuseAllowed"]:
            raise WorkspaceTenantIsolationError("source binding policies must not allow cross-tenant reuse")

    cases = record["accessCases"]
    accepted = cases[0]
    if accepted["caseName"] != "same_tenant_workspace_read" or not accepted["accessAllowed"]:
        raise WorkspaceTenantIsolationError("first access case must be the accepted same-tenant read")
    for item in cases[1:]:
        if not item["caseStatus"].startswith("blocked_") or item["accessAllowed"]:
            raise WorkspaceTenantIsolationError("cross-tenant access cases must be blocked")
        if item["operationReceiptsWritten"] or item["immutableRecordsWritten"]:
            raise WorkspaceTenantIsolationError("blocked access cases must not write receipts or records")
        if item["credentialValuesStored"] or not item["sanitizedDiagnosticsOnly"]:
            raise WorkspaceTenantIsolationError("blocked access cases must keep credential and diagnostic boundaries")

    if any(record["executionBoundary"].values()):
        raise WorkspaceTenantIsolationError("execution boundary flags should stay false")


def tenant_payload(record: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    for item in record["tenantWorkspaceBindings"]:
        if item["tenantId"] == tenant_id:
            return item
    raise WorkspaceTenantIsolationError(f"unknown tenant {tenant_id}")


def case_payload(record: dict[str, Any], case_name: str) -> dict[str, Any]:
    for item in record["accessCases"]:
        if item["caseName"] == case_name:
            return item
    raise WorkspaceTenantIsolationError(f"unknown access case {case_name}")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBinding"]
    if view == "tenants":
        return record["tenantWorkspaceBindings"]
    if view == "model":
        return record["isolationModel"]
    if view == "scope":
        return record["scopeKeys"]
    if view == "resources":
        return record["tenantResourceControls"]
    if view == "queues":
        return record["operationQueuePolicies"]
    if view == "sources":
        return record["sourceBindingPolicies"]
    if view == "cases":
        return record["accessCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise WorkspaceTenantIsolationError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated workspace tenant isolation fixture")
    parser.add_argument("--check", action="store_true", help="check generated workspace tenant isolation fixture")
    parser.add_argument("--tenant-id", choices=["tenant-001", "tenant-002"], help="print one tenant workspace binding")
    parser.add_argument("--case", choices=ACCESS_CASES, help="print one checked tenant access case")
    parser.add_argument(
        "--view",
        choices=[
            "full",
            "source",
            "tenants",
            "model",
            "scope",
            "resources",
            "queues",
            "sources",
            "cases",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="emit a focused workspace tenant isolation view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_workspace_tenant_isolation()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="workspace tenant isolation",
            regen="python3 scripts/generate_workspace_tenant_isolation.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="workspace tenant isolation",
            regen="python3 scripts/generate_workspace_tenant_isolation.py --write",
        )
        return
    if args.tenant_id:
        print(render_json(tenant_payload(record, args.tenant_id)), end="")
        return
    if args.case:
        print(render_json(case_payload(record, args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
