#!/usr/bin/env python3
"""Check credential-reference policy invariants."""

from __future__ import annotations

try:
    from generate_credential_reference_policy import build_credential_reference_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("credential reference policy generator is missing") from exc


REFERENCE_MECHANISMS = [
    "caller_secret_store_alias",
    "host_runtime_secret_handle",
    "local_operator_session_ref",
    "public_no_credential",
]

SCOPE_KEYS = [
    "tenant_id",
    "workspace_id",
    "source_binding_id",
    "source_role",
    "adapter_ref",
    "source_kind",
    "source_policy_id",
    "credential_purpose",
]

LIFECYCLE_STATES = [
    "proposed",
    "approved",
    "active",
    "rotation_due",
    "revoked",
    "redaction_required",
]

CONSUMER_RULES = [
    "private_api_adapter",
    "database_adapter",
    "source_binding_validation",
    "runtime_readback",
    "agent_envelope",
    "normal_checks",
]

POLICY_CASES = [
    "accepted_private_api_reference",
    "accepted_database_reference",
    "public_source_no_credential",
    "missing_reference_for_private_api",
    "raw_api_token_submitted",
    "database_password_in_connection_string",
    "cross_tenant_reference",
    "unscoped_reference",
    "adapter_mismatch",
    "revoked_reference",
    "normal_check_resolution_attempt",
]

READBACKS = [
    "cli",
    "source_bindings",
    "domain_source_field_policy",
    "database_source_adapter_runtime",
    "runtime_security",
    "workspace_tenant_isolation",
    "agent_adapter_dispatcher",
]

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksResolveSecrets",
    "storesCredentialValues",
    "printsCredentialValues",
    "readsEnvironmentSecrets",
    "writesSecretStore",
    "crossTenantCredentialReuseAllowed",
    "unscopedReferencesAllowed",
    "rawConnectionStringsAllowed",
    "databaseConnectionsOpened",
    "apiCallsExecuted",
    "hostedSecretManagerImplemented",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_credential_reference_policy()

    require(policy["policyStatus"] == "credential_reference_policy_checked", "policy status drifted")
    require(
        policy["decisionStatus"] == "opaque_caller_owned_references_scoped_to_workspace_source_and_adapter",
        "decision status drifted",
    )
    require(policy["normalChecksMutateState"] is False, "normal checks must not mutate credential policy state")
    require(policy["secretResolverImplemented"] is False, "credential policy must not implement a secret resolver")

    source = policy["sourceBinding"]
    require(source["sourceBindingCommand"] == "python3 scripts/ope.py source-bindings", "source binding command drifted")
    require(
        source["databaseRuntimeCommand"] == "python3 scripts/ope.py database-source-adapter-runtime",
        "database runtime command drifted",
    )
    require(source["sourceBindingCaseCount"] == 4, "policy should bind four source binding cases")
    require(source["databaseRuntimeCaseCount"] == 9, "policy should bind nine database runtime cases")
    require(source["rawCredentialValuesRead"] is False, "policy must not read raw credential values")

    mechanisms = {item["mechanismName"]: item for item in policy["acceptedReferenceMechanisms"]}
    require(list(mechanisms) == REFERENCE_MECHANISMS, "reference mechanism order drifted")
    for item in mechanisms.values():
        require(item["mechanismStatus"] == "accepted_reference_mechanism", f"{item['mechanismName']} status drifted")
        require(item["secretValueStored"] is False, f"{item['mechanismName']} must not store secret values")
        require(
            item["secretLookupDuringNormalChecks"] is False,
            f"{item['mechanismName']} must not look up secrets in normal checks",
        )
        require(item["promptVisibleSecretAllowed"] is False, f"{item['mechanismName']} must block prompt-visible secrets")
        require(item["requiredScopeKeys"] == SCOPE_KEYS, f"{item['mechanismName']} scope keys drifted")
    require("api" in mechanisms["caller_secret_store_alias"]["allowedForSourceKinds"], "caller aliases should allow API")
    require("database" in mechanisms["host_runtime_secret_handle"]["allowedForSourceKinds"], "host handles should allow DB")
    require(mechanisms["public_no_credential"]["callerApprovalRequired"] is False, "public no-credential should not need approval")

    scope = {item["scopeKeyName"]: item for item in policy["requiredScopeKeys"]}
    require(list(scope) == SCOPE_KEYS, "scope key order drifted")
    for item in scope.values():
        require(item["requiredForPrivateApi"] is True, f"{item['scopeKeyName']} should be required for private APIs")
        require(item["requiredForDatabase"] is True, f"{item['scopeKeyName']} should be required for databases")
        require(item["containsSecretMaterial"] is False, f"{item['scopeKeyName']} must not contain secret material")

    lifecycle = {item["stateName"]: item for item in policy["lifecycleStates"]}
    require(list(lifecycle) == LIFECYCLE_STATES, "lifecycle state order drifted")
    require(lifecycle["active"]["allowsRuntimeUse"] is True, "active references should allow explicit runtime use")
    for state_name, item in lifecycle.items():
        require(
            item["allowsNormalCheckSecretResolution"] is False,
            f"{state_name} must not allow normal-check secret resolution",
        )
        require(item["credentialValuesStored"] is False, f"{state_name} must not store credential values")
    for state_name in ["revoked", "redaction_required"]:
        require(lifecycle[state_name]["allowsRuntimeUse"] is False, f"{state_name} must block runtime use")

    consumers = {item["consumerName"]: item for item in policy["consumerRules"]}
    require(list(consumers) == CONSUMER_RULES, "consumer rule order drifted")
    for item in consumers.values():
        require(item["canReceiveCredentialValue"] is False, f"{item['consumerName']} must not receive credential values")
        require(
            item["canResolveSecretInNormalChecks"] is False,
            f"{item['consumerName']} must not resolve secrets in normal checks",
        )
        require(item["requiresScopeMatch"] is True, f"{item['consumerName']} should require scope match")
        require(item["requiresAdapterMatch"] is True, f"{item['consumerName']} should require adapter match")
    require(
        consumers["normal_checks"]["mayUseCredentialReference"] is False,
        "normal checks should not use credential references for secret resolution",
    )

    cases = {item["caseName"]: item for item in policy["credentialReferenceCases"]}
    require(list(cases) == POLICY_CASES, "credential reference case order drifted")
    for name in POLICY_CASES[:3]:
        require(cases[name]["caseStatus"].startswith("accepted_"), f"{name} should be accepted")
        require(cases[name]["credentialValuesStored"] is False, f"{name} must not store credentials")
        require(cases[name]["secretResolvedInNormalChecks"] is False, f"{name} must not resolve secrets in checks")
        require(cases[name]["sanitizedDiagnosticsOnly"] is True, f"{name} should keep diagnostics sanitized")
    for name in POLICY_CASES[3:]:
        require(cases[name]["caseStatus"].startswith("blocked_"), f"{name} should be blocked")
        require(cases[name]["sourceBindingAccepted"] is False, f"{name} must not accept binding")
        require(cases[name]["canEnterAdapterRuntime"] is False, f"{name} must not enter adapter runtime")
        require(cases[name]["credentialValuesStored"] is False, f"{name} must not store credentials")
        require(cases[name]["secretResolvedInNormalChecks"] is False, f"{name} must not resolve secrets in checks")
        require(cases[name]["crossTenantReuseAllowed"] is False, f"{name} must not allow cross-tenant reuse")
        require(cases[name]["sanitizedDiagnosticsOnly"] is True, f"{name} should keep diagnostics sanitized")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(list(readbacks) == READBACKS, "readback order drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py credential-reference-policy", "CLI command drifted")
    for item in readbacks.values():
        require(item["mutatesState"] is False, "readbacks must not mutate state")
        require(item["resolvesSecrets"] is False, "readbacks must not resolve secrets")
        require(item["credentialValuesReturned"] is False, "readbacks must not return credential values")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")
    require(not any(boundary.values()), "execution boundary flags should all stay false")

    summary = policy["summary"]
    require(summary["acceptedReferenceMechanismCount"] == len(REFERENCE_MECHANISMS), "mechanism count drifted")
    require(summary["requiredScopeKeyCount"] == len(SCOPE_KEYS), "scope key count drifted")
    require(summary["lifecycleStateCount"] == len(LIFECYCLE_STATES), "lifecycle state count drifted")
    require(summary["consumerRuleCount"] == len(CONSUMER_RULES), "consumer rule count drifted")
    require(summary["credentialReferenceCaseCount"] == len(POLICY_CASES), "case count drifted")
    require(summary["blockedCaseCount"] == len(POLICY_CASES) - 3, "blocked case count drifted")
    require(summary["normalChecksResolveSecrets"] is False, "summary normal-check secret-resolution flag drifted")
    require(summary["secretResolverImplemented"] is False, "summary secret resolver flag drifted")

    print("checked credential reference policy")


if __name__ == "__main__":
    main()
