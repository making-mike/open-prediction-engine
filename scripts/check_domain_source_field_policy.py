#!/usr/bin/env python3
"""Check domain/source field requirement policy invariants."""

from __future__ import annotations

try:
    from generate_domain_source_field_policy import build_domain_source_field_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("domain source field policy generator is missing") from exc


UNIVERSAL_DOMAIN_FIELDS = [
    "domain_identity",
    "question_templates",
    "horizons",
    "resolution_criteria",
    "baseline_method",
    "accepted_source_roles",
    "exclusion_rules",
    "sample_thresholds",
    "claim_boundaries",
    "execution_boundary",
]

UNIVERSAL_SOURCE_FIELDS = [
    "source_binding_identity",
    "source_binding_mode",
    "credential_policy",
    "source_role_bindings",
    "pre_forecast_checks",
    "setup_operations",
    "configuration_input_boundary",
    "execution_boundary",
    "next_action",
    "summary",
]

DOMAIN_EXTENSION_FIELDS = [
    "question_parameters",
    "role_keys",
    "role_required_fields",
    "resolution_text_criteria",
    "exclusion_reason_codes",
    "domain_specific_horizon_labels",
    "baseline_threshold_values",
    "source_quality_threshold_values",
]

BLOCKED_FIELDS = [
    "credential_value",
    "raw_sql_query",
    "raw_private_row",
    "post_outcome_forecast_evidence",
    "production_quality_claim",
    "hosted_runtime_flag",
]

FIELD_CASES = [
    "weather_transit_core_ready",
    "seaport_extension_ready",
    "missing_resolution_criteria",
    "credential_value_in_source_binding",
    "raw_sql_query_as_binding_field",
    "domain_quality_claim_enabled",
    "outcome_role_marked_forecast_time",
]

READBACKS = [
    "cli",
    "domain_configs",
    "source_bindings",
    "source_quality",
    "source_intake",
    "runtime_security",
    "workspace_tenant_isolation",
]

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksWriteState",
    "createsForecasts",
    "readsPrivateData",
    "storesCredentialValues",
    "rawSqlAllowed",
    "arbitraryPrivateApiParsingByOpe",
    "arbitraryDatabaseParsingByOpe",
    "hostedRuntimeImplemented",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_domain_source_field_policy()

    require(policy["policyStatus"] == "domain_source_field_policy_checked", "policy status drifted")
    require(
        policy["decisionStatus"] == "universal_domain_and_source_fields_with_domain_extension_boundary",
        "decision status drifted",
    )
    require(policy["normalChecksMutateState"] is False, "normal checks must not mutate field policy state")
    require(policy["generatedRuntimeTypesIncluded"] is False, "field policy must not generate runtime types")

    source = policy["sourceBinding"]
    require(source["domainConfigCommand"] == "python3 scripts/ope.py domain-configs", "domain config source command drifted")
    require(source["sourceBindingCommand"] == "python3 scripts/ope.py source-bindings", "source binding command drifted")
    require(source["domainConfigCount"] == 2, "field policy should bind two checked domain configs")
    require(source["sourceBindingCaseCount"] == 4, "field policy should bind four source binding cases")
    require(source["rawSourceDataRead"] is False, "field policy must not read raw source data")

    domain_fields = {item["fieldPolicyName"]: item for item in policy["universalDomainFields"]}
    require(list(domain_fields) == UNIVERSAL_DOMAIN_FIELDS, "universal domain field order drifted")
    for item in domain_fields.values():
        require(item["recordSurface"] == "domain_config", f"{item['fieldPolicyName']} should be domain config")
        require(item["requirementLevel"] == "required_every_domain", f"{item['fieldPolicyName']} should be required")
        require(item["domainExtensionAllowed"] is False, f"{item['fieldPolicyName']} should not move to extension")
        require(item["credentialValuesAllowed"] is False, f"{item['fieldPolicyName']} should not allow credentials")
        require(item["rawPrivateDataAllowed"] is False, f"{item['fieldPolicyName']} should not allow raw private data")

    source_fields = {item["fieldPolicyName"]: item for item in policy["universalSourceBindingFields"]}
    require(list(source_fields) == UNIVERSAL_SOURCE_FIELDS, "universal source field order drifted")
    for item in source_fields.values():
        require(item["recordSurface"] == "source_binding", f"{item['fieldPolicyName']} should be source binding")
        require(item["requirementLevel"] == "required_every_source_binding", f"{item['fieldPolicyName']} should be required")
        require(item["domainExtensionAllowed"] is False, f"{item['fieldPolicyName']} should not move to extension")
        require(item["credentialValuesAllowed"] is False, f"{item['fieldPolicyName']} should not allow credentials")
        require(item["rawPrivateDataAllowed"] is False, f"{item['fieldPolicyName']} should not allow raw private data")

    extensions = {item["fieldPolicyName"]: item for item in policy["domainSpecificExtensionFields"]}
    require(list(extensions) == DOMAIN_EXTENSION_FIELDS, "domain extension field order drifted")
    for item in extensions.values():
        require(item["requirementLevel"] == "domain_specific_extension", f"{item['fieldPolicyName']} should be extension")
        require(item["domainExtensionAllowed"] is True, f"{item['fieldPolicyName']} should allow extension values")
        require(item["credentialValuesAllowed"] is False, f"{item['fieldPolicyName']} must not allow credentials")
        require(item["rawPrivateDataAllowed"] is False, f"{item['fieldPolicyName']} must not allow raw private data")

    blocked = {item["fieldPolicyName"]: item for item in policy["blockedFields"]}
    require(list(blocked) == BLOCKED_FIELDS, "blocked field order drifted")
    for item in blocked.values():
        require(item["requirementLevel"] == "blocked", f"{item['fieldPolicyName']} should be blocked")
        require(item["domainExtensionAllowed"] is False, f"{item['fieldPolicyName']} must not be extension")
        require(item["safeNextAction"], f"{item['fieldPolicyName']} should include safe next action")

    source_kind_rules = {item["sourceKind"]: item for item in policy["sourceKindFieldRules"]}
    require(set(source_kind_rules) == {"fixture", "local_file", "source_adapter_output", "api", "database"}, "source kind coverage drifted")
    for item in source_kind_rules.values():
        require(item["sourceRefRequired"] is True, f"{item['sourceKind']} should require sourceRef")
        require(item["adapterRefRequired"] is True, f"{item['sourceKind']} should require adapterRef")
        require(item["credentialValueAllowed"] is False, f"{item['sourceKind']} must not allow credential values")
        require(item["rawPayloadStored"] is False, f"{item['sourceKind']} must not store raw payloads")
    require(source_kind_rules["database"]["credentialReferenceRequired"] is True, "database sources should require credential refs")
    require(source_kind_rules["api"]["credentialReferenceRequired"] is True, "private API sources should require credential refs when private")

    cases = {item["caseName"]: item for item in policy["fieldDecisionCases"]}
    require(list(cases) == FIELD_CASES, "field decision case order drifted")
    for name in FIELD_CASES[:2]:
        require(cases[name]["caseStatus"].startswith("accepted_"), f"{name} should be accepted")
        require(cases[name]["forecastArtifactsCreated"] is False, f"{name} should not create forecast artifacts")
        require(cases[name]["policyViolation"] is False, f"{name} should not violate policy")
    for name in FIELD_CASES[2:]:
        require(cases[name]["caseStatus"].startswith("blocked_"), f"{name} should be blocked")
        require(cases[name]["policyViolation"] is True, f"{name} should record policy violation")
        require(cases[name]["forecastArtifactsCreated"] is False, f"{name} should not create forecast artifacts")
        require(cases[name]["credentialValuesStored"] is False, f"{name} must not store credentials")
        require(cases[name]["rawPrivateDataStored"] is False, f"{name} must not store raw private data")
        require(cases[name]["sanitizedDiagnosticsOnly"] is True, f"{name} should keep diagnostics sanitized")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(list(readbacks) == READBACKS, "readback order drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py domain-source-field-policy", "CLI command drifted")
    for item in readbacks.values():
        require(item["mutatesState"] is False, "readbacks must not mutate state")
        require(item["startsNetworkListener"] is False, "readbacks must not start network listeners")
        require(item["credentialValuesReturned"] is False, "readbacks must not return credential values")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")
    require(not any(boundary.values()), "execution boundary flags should all stay false")

    summary = policy["summary"]
    require(summary["universalDomainFieldCount"] == len(UNIVERSAL_DOMAIN_FIELDS), "domain field count drifted")
    require(summary["universalSourceBindingFieldCount"] == len(UNIVERSAL_SOURCE_FIELDS), "source field count drifted")
    require(summary["domainSpecificExtensionFieldCount"] == len(DOMAIN_EXTENSION_FIELDS), "extension count drifted")
    require(summary["blockedFieldCount"] == len(BLOCKED_FIELDS), "blocked count drifted")
    require(summary["fieldDecisionCaseCount"] == len(FIELD_CASES), "case count drifted")
    require(summary["normalChecksMutateState"] is False, "summary normal-check mutation flag drifted")
    require(summary["generatedRuntimeTypesIncluded"] is False, "summary generated runtime type flag drifted")

    print("checked domain source field policy")


if __name__ == "__main__":
    main()
