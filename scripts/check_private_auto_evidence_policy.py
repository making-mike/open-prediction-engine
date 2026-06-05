#!/usr/bin/env python3
"""Check private data:auto source-policy boundaries."""

from __future__ import annotations

try:
    from generate_private_auto_evidence_policy import build_private_auto_evidence_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("private auto-evidence policy generator is missing") from exc


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

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksReadPrivateSources",
    "normalChecksResolveSecrets",
    "normalChecksNetworkAccess",
    "normalChecksWriteState",
    "arbitraryWebSearchAllowed",
    "arbitraryPrivateApiParsingAllowed",
    "arbitraryDatabaseParsingAllowed",
    "rawSqlExecutionAllowed",
    "rawPrivatePayloadRetentionAllowed",
    "postOutcomeEvidenceAsForecastEvidenceAllowed",
    "hostedRuntimeImplemented",
    "qualityClaimsUpgraded",
    "generatedRuntimeTypesEnabled",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_private_auto_evidence_policy()

    require(policy["policyStatus"] == "private_auto_evidence_policy_checked", "policy status drifted")
    require(
        policy["decisionStatus"] == "private_data_auto_requires_bound_source_policy_and_approved_adapters",
        "decision status drifted",
    )
    require(policy["normalChecksMutateState"] is False, "normal checks must not mutate state")
    require(policy["normalChecksReadPrivateSources"] is False, "normal checks must not read private sources")

    sources = policy["sourceBindings"]
    require(sources["sourcePolicySchemaId"] == "https://openprediction.engine/spec/source-policy.schema.json", "source policy schema drifted")
    require(sources["privateSourceAdapterStatus"] == "private_source_adapter_capabilities_checked", "adapter source drifted")
    require(sources["domainSourceFieldPolicyStatus"] == "domain_source_field_policy_checked", "field policy source drifted")
    require(sources["credentialReferencePolicyStatus"] == "credential_reference_policy_checked", "credential source drifted")
    require(sources["retentionRedactionPolicyStatus"] == "retention_redaction_policy_checked", "retention source drifted")
    require(sources["runtimeSecurityStatus"] == "runtime_security_checked", "runtime security source drifted")
    require(sources["workspaceTenantIsolationStatus"] == "workspace_tenant_isolation_checked", "tenant source drifted")
    require(sources["normalChecksWriteState"] is False, "source bindings must stay read-only")

    kinds = {item["sourceKind"]: item for item in policy["sourceKindPolicies"]}
    require(list(kinds) == SOURCE_KINDS, "source kind order drifted")
    require(kinds["local_file"]["currentPolicyStatus"] == "allowed_with_approved_local_runtime", "local file status drifted")
    require(kinds["source_adapter_output"]["currentPolicyStatus"] == "allowed_with_sanitized_adapter_output", "adapter output status drifted")
    require(kinds["database_query_manifest"]["currentPolicyStatus"] == "manifest_only_no_raw_sql_execution", "database manifest status drifted")
    require(kinds["private_api_manifest"]["credentialReferenceRequired"] is True, "private API should require credential reference")
    require(kinds["web_search"]["currentPolicyStatus"] == "blocked_for_private_data_auto", "private web search should block")
    require(kinds["web_search"]["networkAccessAllowed"] is False, "private web search should not enable network")
    for item in kinds.values():
        require(item["sourcePolicyRequired"] is True, f"{item['sourceKind']} should require source policy")
        require(item["tenantWorkspaceScopeRequired"] is True, f"{item['sourceKind']} should require tenant/workspace scope")
        require(item["normalChecksReadPrivateSource"] is False, f"{item['sourceKind']} must not read private source")
        require(item["normalChecksResolveCredential"] is False, f"{item['sourceKind']} must not resolve credentials")
        require(item["rawPayloadRetentionAllowed"] is False, f"{item['sourceKind']} must not retain raw payloads")

    gates = {item["gateName"]: item for item in policy["policyGates"]}
    require(list(gates) == POLICY_GATES, "policy gate order drifted")
    require(gates["credential_reference_scoped"]["blocksCredentialValues"] is True, "credential gate should block credential values")
    require(gates["adapter_capability_checked"]["blocksUnregisteredAdapters"] is True, "adapter gate should block unregistered adapters")
    require(gates["forecast_before_close_preserved"]["blocksPostOutcomeEvidence"] is True, "forecast timing gate should block post-outcome evidence")
    for item in gates.values():
        require(item["requiredForPrivateAuto"] is True, f"{item['gateName']} should be required")
        require(item["normalChecksEvaluateAsEffectful"] is False, f"{item['gateName']} should stay non-effectful")

    cases = {item["caseName"]: item for item in policy["decisionCases"]}
    require(list(cases) == DECISION_CASES, "decision case order drifted")
    require(cases["approved_local_file_auto"]["caseStatus"] == "policy_ready", "local file case drifted")
    require(cases["approved_adapter_output_auto"]["selectedSourceKind"] == "source_adapter_output", "adapter output case drifted")
    require(cases["approved_database_query_manifest"]["caseStatus"] == "manifest_ready_no_execution", "database manifest case drifted")
    require(cases["private_api_manifest_with_scoped_credential"]["caseStatus"] == "manifest_ready_no_execution", "private API manifest case drifted")
    require(cases["manual_upload_without_adapter_contract"]["caseStatus"] == "blocked_missing_adapter_contract", "manual upload block drifted")
    require(cases["private_api_missing_credential_ref"]["caseStatus"] == "blocked_missing_credential_reference", "missing credential block drifted")
    require(cases["database_raw_sql_auto"]["caseStatus"] == "blocked_raw_sql", "raw SQL block drifted")
    require(cases["web_search_private_setup"]["caseStatus"] == "blocked_private_web_search", "private web search block drifted")
    require(cases["cross_tenant_source_binding"]["caseStatus"] == "blocked_scope_mismatch", "cross-tenant block drifted")
    require(cases["post_outcome_capture_as_forecast_evidence"]["caseStatus"] == "blocked_post_outcome_evidence", "post-outcome block drifted")
    require(cases["raw_private_payload_retention"]["caseStatus"] == "blocked_raw_payload_retention", "raw payload block drifted")
    require(cases["unregistered_private_connector"]["caseStatus"] == "blocked_unregistered_adapter", "unregistered connector block drifted")
    for item in cases.values():
        require(item["normalChecksReadPrivateSources"] is False, f"{item['caseName']} must not read private sources")
        require(item["normalChecksWriteState"] is False, f"{item['caseName']} must not write state")
        require(item["credentialValuesStored"] is False, f"{item['caseName']} must not store credentials")
        require(item["sanitizedDiagnosticsOnly"] is True, f"{item['caseName']} should keep diagnostics sanitized")
        if item["caseStatus"].startswith("blocked_"):
            require(item["eligibleForForecastExecution"] is False, f"{item['caseName']} should not be forecast-eligible")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(list(readbacks) == READBACKS, "readback order drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py private-auto-evidence-policy", "CLI readback drifted")
    for item in readbacks.values():
        require(item["mutatesState"] is False, f"{item['readbackSurface']} must not mutate state")
        require(item["readsPrivateSource"] is False, f"{item['readbackSurface']} must not read private sources")
        require(item["resolvesCredentials"] is False, f"{item['readbackSurface']} must not resolve credentials")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = policy["summary"]
    require(summary["sourceKindCount"] == len(SOURCE_KINDS), "source kind count drifted")
    require(summary["policyGateCount"] == len(POLICY_GATES), "gate count drifted")
    require(summary["decisionCaseCount"] == len(DECISION_CASES), "case count drifted")
    require(summary["readbackCount"] == len(READBACKS), "readback count drifted")
    require(summary["blockedCaseCount"] == 8, "blocked case count drifted")
    require(summary["manifestOnlyCaseCount"] == 2, "manifest-only case count drifted")
    require(summary["normalChecksReadPrivateSources"] is False, "summary private read flag drifted")
    require(summary["normalChecksMutateState"] is False, "summary mutation flag drifted")

    print("checked private auto-evidence policy")


if __name__ == "__main__":
    main()
