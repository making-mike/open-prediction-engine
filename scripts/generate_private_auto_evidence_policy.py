#!/usr/bin/env python3
"""Generate a checked private data:auto source-policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_credential_reference_policy import build_credential_reference_policy
from generate_database_source_adapter_runtime import build_database_source_adapter_runtime
from generate_domain_source_field_policy import build_domain_source_field_policy
from generate_private_source_adapter_capabilities import build_capabilities as build_private_source_adapter_capabilities
from generate_retention_redaction_policy import build_retention_redaction_policy
from generate_runtime_security import build_runtime_security
from generate_workspace_tenant_isolation import build_workspace_tenant_isolation
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-auto-evidence-policy"
OUTPUT_PATH = GENERATED / "ope-private-auto-evidence-policy.generated.json"
SCHEMA = SPEC / "private-auto-evidence-policy.schema.json"
GENERATED_AT = "2026-06-05T08:40:00Z"

SOURCE_KINDS = [
    "local_file",
    "manual_mapping",
    "auto_evidence_connector",
    "source_adapter_output",
    "database_query_manifest",
    "private_api_manifest",
    "manual_upload",
    "web_search",
]

POLICY_GATES = [
    "domain_config_bound",
    "source_binding_bound",
    "source_policy_bound",
    "tenant_workspace_scope_bound",
    "caller_approval_recorded",
    "credential_reference_scoped",
    "adapter_capability_checked",
    "freshness_window_declared",
    "retention_policy_bound",
    "leakage_checks_declared",
    "forecast_before_close_preserved",
    "normal_checks_non_effectful",
]

DECISION_CASES = [
    "approved_local_file_auto",
    "approved_adapter_output_auto",
    "approved_database_query_manifest",
    "private_api_manifest_with_scoped_credential",
    "manual_mapping_with_confirmation",
    "manual_upload_without_adapter_contract",
    "private_api_missing_credential_ref",
    "database_raw_sql_auto",
    "web_search_private_setup",
    "cross_tenant_source_binding",
    "post_outcome_capture_as_forecast_evidence",
    "raw_private_payload_retention",
    "unregistered_private_connector",
]

READBACKS = [
    "cli",
    "source_policy_schema",
    "auto_evidence",
    "private_source_adapters",
    "domain_source_field_policy",
    "credential_reference_policy",
    "retention_redaction_policy",
    "runtime_security",
    "workspace_tenant_isolation",
    "database_source_adapter_runtime",
]


class PrivateAutoEvidencePolicyError(Exception):
    pass


def source_kind_policy(
    source_kind: str,
    current_policy_status: str,
    data_auto_role: str,
    safe_next_action: str,
    *,
    caller_approval_required: bool = True,
    credential_reference_required: bool = False,
    adapter_contract_required: bool = True,
    network_access_allowed: bool = False,
) -> dict[str, Any]:
    return {
        "sourceKind": source_kind,
        "currentPolicyStatus": current_policy_status,
        "dataAutoRole": data_auto_role,
        "sourcePolicyRequired": True,
        "tenantWorkspaceScopeRequired": True,
        "callerApprovalRequired": caller_approval_required,
        "credentialReferenceRequired": credential_reference_required,
        "adapterContractRequired": adapter_contract_required,
        "networkAccessAllowed": network_access_allowed,
        "normalChecksReadPrivateSource": False,
        "normalChecksResolveCredential": False,
        "rawPayloadRetentionAllowed": False,
        "safeNextAction": safe_next_action,
    }


def source_kind_policies() -> list[dict[str, Any]]:
    return [
        source_kind_policy(
            "local_file",
            "allowed_with_approved_local_runtime",
            "forecast_time_evidence",
            "route through approved local-source runtime and source-intake gates",
            credential_reference_required=False,
        ),
        source_kind_policy(
            "manual_mapping",
            "allowed_with_confirmed_mapping",
            "forecast_time_evidence",
            "require caller confirmation before treating inferred mappings as setup inputs",
            credential_reference_required=False,
        ),
        source_kind_policy(
            "auto_evidence_connector",
            "allowed_fixture_replay_only",
            "forecast_time_evidence",
            "use existing fixture-replay auto-evidence connectors until a live readiness gate lands",
            credential_reference_required=False,
        ),
        source_kind_policy(
            "source_adapter_output",
            "allowed_with_sanitized_adapter_output",
            "forecast_time_evidence",
            "accept only sanitized adapter-output handoffs that pass source-adapter intake",
            credential_reference_required=False,
        ),
        source_kind_policy(
            "database_query_manifest",
            "manifest_only_no_raw_sql_execution",
            "forecast_time_evidence",
            "declare approved dataset, query boundary, freshness, and audit fields before any future execution",
            credential_reference_required=True,
        ),
        source_kind_policy(
            "private_api_manifest",
            "manifest_only_no_runtime_execution",
            "forecast_time_evidence",
            "declare endpoint family, source policy, credential reference, rate limit, freshness, and audit fields",
            credential_reference_required=True,
        ),
        source_kind_policy(
            "manual_upload",
            "planned_adapter_contract_required",
            "not_allowed",
            "wait for a manual-upload adapter contract before allowing data:auto source discovery",
            credential_reference_required=False,
        ),
        source_kind_policy(
            "web_search",
            "blocked_for_private_data_auto",
            "not_allowed",
            "keep broad web search outside private data:auto setup until a separate allow-listed policy exists",
            caller_approval_required=True,
            credential_reference_required=False,
            adapter_contract_required=True,
            network_access_allowed=False,
        ),
    ]


def policy_gate(
    gate_name: str,
    evidence_required: str,
    failure_status: str,
    *,
    blocks_credential_values: bool = False,
    blocks_unregistered_adapters: bool = False,
    blocks_post_outcome_evidence: bool = False,
) -> dict[str, Any]:
    return {
        "gateName": gate_name,
        "gateStatus": "required_private_auto_gate",
        "requiredForPrivateAuto": True,
        "blocksCredentialValues": blocks_credential_values,
        "blocksUnregisteredAdapters": blocks_unregistered_adapters,
        "blocksPostOutcomeEvidence": blocks_post_outcome_evidence,
        "normalChecksEvaluateAsEffectful": False,
        "evidenceRequired": evidence_required,
        "failureStatus": failure_status,
    }


def policy_gates() -> list[dict[str, Any]]:
    return [
        policy_gate(
            "domain_config_bound",
            "A checked domain config with question templates, horizons, resolution criteria, and claim boundaries.",
            "blocked_missing_domain_config",
        ),
        policy_gate(
            "source_binding_bound",
            "A source binding that maps source roles, setup operations, and pre-forecast checks.",
            "blocked_missing_source_binding",
        ),
        policy_gate(
            "source_policy_bound",
            "A source policy ID with source classes, connectors or source kinds, freshness, approval, and retention posture.",
            "blocked_missing_source_policy",
        ),
        policy_gate(
            "tenant_workspace_scope_bound",
            "Tenant, workspace, prediction, and source-binding IDs must agree before private setup guidance is returned.",
            "blocked_scope_mismatch",
        ),
        policy_gate(
            "caller_approval_recorded",
            "A caller approval or explicit fixture replay boundary must exist before private data:auto setup can proceed.",
            "blocked_missing_approval",
        ),
        policy_gate(
            "credential_reference_scoped",
            "Private API and database manifests require scoped opaque credential references, never credential values.",
            "blocked_missing_or_unsafe_credential_reference",
            blocks_credential_values=True,
        ),
        policy_gate(
            "adapter_capability_checked",
            "The source kind must map to a checked adapter capability and cannot imply unregistered connector execution.",
            "blocked_unregistered_adapter",
            blocks_unregistered_adapters=True,
        ),
        policy_gate(
            "freshness_window_declared",
            "Forecast-time evidence requires retrieved-at, max age, and close-time compatibility.",
            "blocked_missing_freshness_window",
        ),
        policy_gate(
            "retention_policy_bound",
            "Private setup evidence must bind to metadata-only or redaction-receipt retention rules.",
            "blocked_retention_policy_mismatch",
        ),
        policy_gate(
            "leakage_checks_declared",
            "The source binding must declare leakage, privacy, mapping-confidence, and outcome-availability checks.",
            "blocked_missing_leakage_checks",
        ),
        policy_gate(
            "forecast_before_close_preserved",
            "Evidence gathered after the outcome or close-time cannot be treated as forecast-time evidence.",
            "blocked_post_outcome_evidence",
            blocks_post_outcome_evidence=True,
        ),
        policy_gate(
            "normal_checks_non_effectful",
            "Normal checks must not read private sources, resolve secrets, call networks, or write runtime state.",
            "blocked_effectful_normal_check",
        ),
    ]


def decision_case(
    case_name: str,
    case_status: str,
    selected_source_kind: str,
    safe_next_action: str,
    *,
    selected_gate_failures: list[str] | None = None,
    source_policy_bound: bool = True,
    eligible_for_forecast_execution: bool = False,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": case_status,
        "selectedSourceKind": selected_source_kind,
        "selectedGateFailures": selected_gate_failures or [],
        "sourcePolicyBound": source_policy_bound,
        "eligibleForForecastExecution": eligible_for_forecast_execution,
        "credentialValuesStored": False,
        "normalChecksReadPrivateSources": False,
        "normalChecksWriteState": False,
        "sanitizedDiagnosticsOnly": True,
        "safeNextAction": safe_next_action,
    }


def decision_cases() -> list[dict[str, Any]]:
    return [
        decision_case(
            "approved_local_file_auto",
            "policy_ready",
            "local_file",
            "route to local-source runtime, source intake, source handoff, method gate, and setup forecast execution",
            eligible_for_forecast_execution=True,
        ),
        decision_case(
            "approved_adapter_output_auto",
            "policy_ready",
            "source_adapter_output",
            "accept sanitized adapter output and continue through source-adapter intake and source handoff",
            eligible_for_forecast_execution=True,
        ),
        decision_case(
            "approved_database_query_manifest",
            "manifest_ready_no_execution",
            "database_query_manifest",
            "record the manifest boundary and wait for an explicit approved database runtime execution path",
        ),
        decision_case(
            "private_api_manifest_with_scoped_credential",
            "manifest_ready_no_execution",
            "private_api_manifest",
            "record endpoint family, source policy, credential reference, rate limit, and freshness without calling the API",
        ),
        decision_case(
            "manual_mapping_with_confirmation",
            "policy_ready",
            "manual_mapping",
            "treat confirmed mapping as setup input and preserve mapping confidence separately from source quality",
            eligible_for_forecast_execution=True,
        ),
        decision_case(
            "manual_upload_without_adapter_contract",
            "blocked_missing_adapter_contract",
            "manual_upload",
            "add a checked manual-upload adapter contract before using manual uploads in data:auto private setup",
            selected_gate_failures=["adapter_capability_checked"],
        ),
        decision_case(
            "private_api_missing_credential_ref",
            "blocked_missing_credential_reference",
            "private_api_manifest",
            "replace credential values with a scoped opaque credential reference before retrying",
            selected_gate_failures=["credential_reference_scoped"],
        ),
        decision_case(
            "database_raw_sql_auto",
            "blocked_raw_sql",
            "database_query_manifest",
            "replace raw SQL with an approved query manifest boundary and sanitized adapter output handoff",
            selected_gate_failures=["source_binding_bound", "credential_reference_scoped"],
        ),
        decision_case(
            "web_search_private_setup",
            "blocked_private_web_search",
            "web_search",
            "use allow-listed APIs or checked adapters; broad web search remains outside private data:auto",
            selected_gate_failures=["adapter_capability_checked", "normal_checks_non_effectful"],
            source_policy_bound=False,
        ),
        decision_case(
            "cross_tenant_source_binding",
            "blocked_scope_mismatch",
            "source_adapter_output",
            "return sanitized scope diagnostics and require matching tenant/workspace/source-binding IDs",
            selected_gate_failures=["tenant_workspace_scope_bound"],
        ),
        decision_case(
            "post_outcome_capture_as_forecast_evidence",
            "blocked_post_outcome_evidence",
            "auto_evidence_connector",
            "classify the capture as resolution-only or excluded evidence instead of forecast-time evidence",
            selected_gate_failures=["forecast_before_close_preserved"],
        ),
        decision_case(
            "raw_private_payload_retention",
            "blocked_raw_payload_retention",
            "source_adapter_output",
            "keep hashes, normalized fields, and redaction receipts; reject raw private payload retention",
            selected_gate_failures=["retention_policy_bound"],
        ),
        decision_case(
            "unregistered_private_connector",
            "blocked_unregistered_adapter",
            "private_api_manifest",
            "add a checked adapter capability and source-policy binding before source discovery",
            selected_gate_failures=["adapter_capability_checked"],
            source_policy_bound=False,
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    rows = [
        ("cli", "python3 scripts/ope.py private-auto-evidence-policy", "Prints this checked private data:auto policy."),
        ("source_policy_schema", "spec/source-policy.schema.json", "Keeps the base source-policy contract explicit and schema-bound."),
        ("auto_evidence", "python3 scripts/ope.py evidence-plan", "Preserves fixture-replay auto-evidence as the current executable data:auto path."),
        ("private_source_adapters", "python3 scripts/ope.py private-source-adapters", "Declares source-kind capabilities without executing private reads."),
        ("domain_source_field_policy", "python3 scripts/ope.py domain-source-field-policy", "Blocks raw credential, SQL, private-row, and claim fields in setup records."),
        ("credential_reference_policy", "python3 scripts/ope.py credential-reference-policy", "Requires scoped opaque credential references for private API and database manifests."),
        ("retention_redaction_policy", "python3 scripts/ope.py retention-redaction-policy", "Keeps raw payload retention blocked and redaction receipts available."),
        ("runtime_security", "python3 scripts/ope.py runtime-security", "Keeps normal checks offline, non-networked, and credential-free."),
        ("workspace_tenant_isolation", "python3 scripts/ope.py workspace-tenant-isolation", "Scopes private source bindings to tenant and workspace ownership."),
        ("database_source_adapter_runtime", "python3 scripts/ope.py database-source-adapter-runtime", "Shows the only approved database adapter fixture path."),
    ]
    return [
        {
            "readbackSurface": surface,
            "command": command,
            "mutatesState": False,
            "readsPrivateSource": False,
            "resolvesCredentials": False,
            "notes": notes,
        }
        for surface, command, notes in rows
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksReadPrivateSources": False,
        "normalChecksResolveSecrets": False,
        "normalChecksNetworkAccess": False,
        "normalChecksWriteState": False,
        "arbitraryWebSearchAllowed": False,
        "arbitraryPrivateApiParsingAllowed": False,
        "arbitraryDatabaseParsingAllowed": False,
        "rawSqlExecutionAllowed": False,
        "rawPrivatePayloadRetentionAllowed": False,
        "postOutcomeEvidenceAsForecastEvidenceAllowed": False,
        "hostedRuntimeImplemented": False,
        "qualityClaimsUpgraded": False,
        "generatedRuntimeTypesEnabled": False,
    }


def build_source_bindings() -> dict[str, Any]:
    adapters = build_private_source_adapter_capabilities()
    field_policy = build_domain_source_field_policy()
    credential_policy = build_credential_reference_policy()
    retention_policy = build_retention_redaction_policy()
    runtime_security = build_runtime_security()
    workspace_isolation = build_workspace_tenant_isolation()
    database_runtime = build_database_source_adapter_runtime()
    return {
        "sourcePolicySchemaId": "https://openprediction.engine/spec/source-policy.schema.json",
        "autoEvidenceStatus": "fixture_replay_auto_evidence_checked",
        "privateSourceAdapterStatus": "private_source_adapter_capabilities_checked",
        "domainSourceFieldPolicyStatus": field_policy["policyStatus"],
        "credentialReferencePolicyStatus": credential_policy["policyStatus"],
        "retentionRedactionPolicyStatus": retention_policy["policyStatus"],
        "runtimeSecurityStatus": "runtime_security_checked"
        if runtime_security["securityStatus"] == "lightweight_runtime_hardening_checked"
        else runtime_security["securityStatus"],
        "workspaceTenantIsolationStatus": workspace_isolation["isolationStatus"],
        "databaseSourceAdapterRuntimeStatus": database_runtime["runtimeStatus"],
        "normalChecksWriteState": False,
        "notes": (
            "Private data:auto uses source-policy plus checked adapter, credential, retention, security, and tenant "
            f"readbacks; adapter runtime status is {adapters['runtimeStatus']}."
        ),
    }


def build_private_auto_evidence_policy() -> dict[str, Any]:
    kinds = source_kind_policies()
    gates = policy_gates()
    cases = decision_cases()
    record = {
        "privateAutoEvidencePolicyId": "privateautoevidencepolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "private_auto_evidence_policy_checked",
        "decisionStatus": "private_data_auto_requires_bound_source_policy_and_approved_adapters",
        "normalChecksMutateState": False,
        "normalChecksReadPrivateSources": False,
        "sourceBindings": build_source_bindings(),
        "sourceKindPolicies": kinds,
        "policyGates": gates,
        "decisionCases": cases,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "sourceKindCount": len(kinds),
            "policyGateCount": len(gates),
            "decisionCaseCount": len(cases),
            "readbackCount": len(READBACKS),
            "blockedCaseCount": sum(1 for item in cases if item["caseStatus"].startswith("blocked_")),
            "manifestOnlyCaseCount": sum(1 for item in cases if item["caseStatus"] == "manifest_ready_no_execution"),
            "normalChecksReadPrivateSources": False,
            "normalChecksMutateState": False,
        },
        "warnings": [
            "Private data:auto does not mean arbitrary private-source discovery; it requires bound source policy and checked adapter capabilities.",
            "Private API and database manifests may describe future runtime boundaries, but normal checks do not call APIs, open databases, run SQL, or resolve secrets.",
            "Broad web search remains blocked for private setup until a separate allow-listed policy and readiness gate exists.",
        ],
    }
    validate_private_auto_evidence_policy(record)
    return record


def validate_private_auto_evidence_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PrivateAutoEvidencePolicyError(f"private auto-evidence policy schema validation failed: {errors[0]}")
    if [item["sourceKind"] for item in record["sourceKindPolicies"]] != SOURCE_KINDS:
        raise PrivateAutoEvidencePolicyError("source kind policy order drifted")
    if [item["gateName"] for item in record["policyGates"]] != POLICY_GATES:
        raise PrivateAutoEvidencePolicyError("policy gate order drifted")
    if [item["caseName"] for item in record["decisionCases"]] != DECISION_CASES:
        raise PrivateAutoEvidencePolicyError("decision case order drifted")
    if [item["readbackSurface"] for item in record["readbacks"]] != READBACKS:
        raise PrivateAutoEvidencePolicyError("readback order drifted")
    for item in record["sourceKindPolicies"]:
        if not item["sourcePolicyRequired"] or not item["tenantWorkspaceScopeRequired"]:
            raise PrivateAutoEvidencePolicyError("source kind policies must require source policy and tenant/workspace scope")
        if item["normalChecksReadPrivateSource"] or item["normalChecksResolveCredential"]:
            raise PrivateAutoEvidencePolicyError("normal checks must not read private sources or resolve credentials")
        if item["rawPayloadRetentionAllowed"]:
            raise PrivateAutoEvidencePolicyError("private data:auto must not retain raw private payloads")
    for item in record["policyGates"]:
        if not item["requiredForPrivateAuto"] or item["normalChecksEvaluateAsEffectful"]:
            raise PrivateAutoEvidencePolicyError("policy gates must be required and non-effectful")
    for item in record["decisionCases"]:
        if item["credentialValuesStored"] or item["normalChecksReadPrivateSources"] or item["normalChecksWriteState"]:
            raise PrivateAutoEvidencePolicyError("decision cases must avoid credentials, private reads, and writes")
        if not item["sanitizedDiagnosticsOnly"]:
            raise PrivateAutoEvidencePolicyError("decision cases must keep diagnostics sanitized")
        if item["caseStatus"].startswith("blocked_") and item["eligibleForForecastExecution"]:
            raise PrivateAutoEvidencePolicyError("blocked cases must not be forecast-execution eligible")
    for item in record["readbacks"]:
        if item["mutatesState"] or item["readsPrivateSource"] or item["resolvesCredentials"]:
            raise PrivateAutoEvidencePolicyError("readbacks must not mutate, read private sources, or resolve credentials")
    for key, value in record["executionBoundary"].items():
        if value is not False:
            raise PrivateAutoEvidencePolicyError(f"execution boundary {key} should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBindings"]
    if view == "source-kinds":
        return record["sourceKindPolicies"]
    if view == "gates":
        return record["policyGates"]
    if view == "cases":
        return record["decisionCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise PrivateAutoEvidencePolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated private data:auto policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated private data:auto policy fixture")
    parser.add_argument("--source-kind", choices=SOURCE_KINDS, help="print one source-kind policy")
    parser.add_argument("--gate", choices=POLICY_GATES, help="print one private data:auto policy gate")
    parser.add_argument("--case", choices=DECISION_CASES, help="print one private data:auto policy case")
    parser.add_argument(
        "--view",
        choices=["full", "source", "source-kinds", "gates", "cases", "readbacks", "boundary", "summary"],
        default="full",
        help="print a focused private data:auto policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_private_auto_evidence_policy()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="private auto-evidence policy",
            regen="python3 scripts/generate_private_auto_evidence_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="private auto-evidence policy",
            regen="python3 scripts/generate_private_auto_evidence_policy.py --write",
        )
        return
    if args.source_kind:
        payload: Any = next(item for item in record["sourceKindPolicies"] if item["sourceKind"] == args.source_kind)
    elif args.gate:
        payload = next(item for item in record["policyGates"] if item["gateName"] == args.gate)
    elif args.case:
        payload = next(item for item in record["decisionCases"] if item["caseName"] == args.case)
    else:
        payload = view_payload(record, args.view)
    sys.stdout.write(render_json(payload))


if __name__ == "__main__":
    main()
