#!/usr/bin/env python3
"""Generate a checked domain/source field requirement policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_domain_configs import build_domain_configs
from generate_source_bindings import build_source_bindings
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "domain-source-field-policy"
OUTPUT_PATH = GENERATED / "ope-domain-source-field-policy.generated.json"
SCHEMA = SPEC / "domain-source-field-policy.schema.json"
GENERATED_AT = "2026-06-04T23:59:45Z"

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


class DomainSourceFieldPolicyError(Exception):
    pass


def field_policy(
    name: str,
    *,
    record_surface: str,
    requirement_level: str,
    field_paths: list[str],
    reason: str,
    domain_extension_allowed: bool,
    safe_next_action: str,
) -> dict[str, Any]:
    return {
        "fieldPolicyName": name,
        "recordSurface": record_surface,
        "requirementLevel": requirement_level,
        "fieldPaths": field_paths,
        "reason": reason,
        "domainExtensionAllowed": domain_extension_allowed,
        "credentialValuesAllowed": False,
        "rawPrivateDataAllowed": False,
        "safeNextAction": safe_next_action,
    }


def universal_domain_fields() -> list[dict[str, Any]]:
    return [
        field_policy(
            "domain_identity",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["domainConfigId", "domainId", "domainKey", "version"],
            reason="Every domain needs stable identity and versioned readback binding.",
            domain_extension_allowed=False,
            safe_next_action="keep identity fields in the core domain config record",
        ),
        field_policy(
            "question_templates",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["questionTemplates"],
            reason="Forecast contracts start from reusable question templates and output type shape.",
            domain_extension_allowed=False,
            safe_next_action="define at least one question template before setup intake",
        ),
        field_policy(
            "horizons",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["horizons"],
            reason="Forecast close and resolution timing need a declared horizon boundary.",
            domain_extension_allowed=False,
            safe_next_action="define at least one horizon template before source binding",
        ),
        field_policy(
            "resolution_criteria",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["resolutionCriteria"],
            reason="Outcome interpretation must be declared before forecast artifacts can be meaningful.",
            domain_extension_allowed=False,
            safe_next_action="add yes/no/ambiguous/annulled resolution criteria",
        ),
        field_policy(
            "baseline_method",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["baselineMethod"],
            reason="Every domain needs a baseline fallback before stronger method claims.",
            domain_extension_allowed=False,
            safe_next_action="bind a baseline method and keep it default until approved evidence exists",
        ),
        field_policy(
            "accepted_source_roles",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["acceptedSourceRoles"],
            reason="Source roles define what evidence can be mapped before forecast execution.",
            domain_extension_allowed=False,
            safe_next_action="define forecast-time, baseline, and resolution roles as needed",
        ),
        field_policy(
            "exclusion_rules",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["exclusionRules"],
            reason="Unscorable and non-comparable outcomes must be explicit before scoring.",
            domain_extension_allowed=False,
            safe_next_action="add exclusion rules instead of silently dropping outcomes",
        ),
        field_policy(
            "sample_thresholds",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["sampleThresholds"],
            reason="Calibration and quality claims need domain-specific sample gates.",
            domain_extension_allowed=False,
            safe_next_action="declare thresholds and keep claims blocked below them",
        ),
        field_policy(
            "claim_boundaries",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["claimBoundaries"],
            reason="Domain configs must not imply quality, calibration, or readiness claims prematurely.",
            domain_extension_allowed=False,
            safe_next_action="keep claim flags false until checked evidence permits a separate update",
        ),
        field_policy(
            "execution_boundary",
            record_surface="domain_config",
            requirement_level="required_every_domain",
            field_paths=["executionBoundary"],
            reason="Domain config readbacks define shape only and do not execute forecasts or private reads.",
            domain_extension_allowed=False,
            safe_next_action="keep domain config execution boundary non-mutating",
        ),
    ]


def universal_source_binding_fields() -> list[dict[str, Any]]:
    return [
        field_policy(
            "source_binding_identity",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["sourceBindingId", "domainConfigId", "domainKey", "predictionId"],
            reason="A source binding must attach to a known domain config and prediction setup.",
            domain_extension_allowed=False,
            safe_next_action="bind source records by ID instead of by raw file or SQL layout",
        ),
        field_policy(
            "source_binding_mode",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["sourceBindingMode"],
            reason="The binding mode tells agents whether the source came from a manifest, adapter, or database manifest.",
            domain_extension_allowed=False,
            safe_next_action="choose an approved binding mode before field mapping",
        ),
        field_policy(
            "credential_policy",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["credentialPolicy"],
            reason="Credential handling must be explicit and reference-only for every source binding.",
            domain_extension_allowed=False,
            safe_next_action="replace secret values with caller-owned credential references",
        ),
        field_policy(
            "source_role_bindings",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["sourceRoleBindings"],
            reason="Each accepted source role needs source kind, source reference, adapter reference, and boundary metadata.",
            domain_extension_allowed=False,
            safe_next_action="map sources to configured role keys through sanitized bindings",
        ),
        field_policy(
            "pre_forecast_checks",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["preForecastChecks"],
            reason="Mapping, quality, leakage, freshness, privacy, and outcome availability checks gate forecast execution.",
            domain_extension_allowed=False,
            safe_next_action="run every pre-forecast check before allowing forecast generation",
        ),
        field_policy(
            "setup_operations",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["setupOperations"],
            reason="Draft, validate, confirm, update, archive, and redact operations stay receipt-backed.",
            domain_extension_allowed=False,
            safe_next_action="use setup operations instead of raw config mutation",
        ),
        field_policy(
            "configuration_input_boundary",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["configurationInputBoundary"],
            reason="Source setup must declare sanitized manifest, mapping, provenance, and query boundaries.",
            domain_extension_allowed=False,
            safe_next_action="stop unsafe inputs before source intake or method gates",
        ),
        field_policy(
            "execution_boundary",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["executionBoundary"],
            reason="Source binding readbacks do not execute APIs, database queries, or forecast creation.",
            domain_extension_allowed=False,
            safe_next_action="keep source binding execution boundary non-mutating",
        ),
        field_policy(
            "next_action",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["nextAction"],
            reason="Agents need deterministic routing from accepted, partial, rejected, and blocked bindings.",
            domain_extension_allowed=False,
            safe_next_action="return an agent-readable next action for every binding case",
        ),
        field_policy(
            "summary",
            record_surface="source_binding",
            requirement_level="required_every_source_binding",
            field_paths=["summary"],
            reason="Summary flags give compact checks for approved kinds, blockers, role coverage, and forecast allowance.",
            domain_extension_allowed=False,
            safe_next_action="keep source binding summary aligned with checks and roles",
        ),
    ]


def domain_specific_extension_fields() -> list[dict[str, Any]]:
    return [
        field_policy(
            "question_parameters",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["questionTemplates[].requiredParameters"],
            reason="Parameter names vary by domain while the template container remains universal.",
            domain_extension_allowed=True,
            safe_next_action="keep parameter names inside question template requiredParameters",
        ),
        field_policy(
            "role_keys",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["acceptedSourceRoles[].roleKey", "resolutionCriteria.primaryOutcomeRole"],
            reason="Role names are domain vocabulary but must stay inside universal role containers.",
            domain_extension_allowed=True,
            safe_next_action="define role keys in acceptedSourceRoles and reference them from resolution criteria",
        ),
        field_policy(
            "role_required_fields",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["acceptedSourceRoles[].requiredFields"],
            reason="Required source columns differ by domain and source role.",
            domain_extension_allowed=True,
            safe_next_action="declare role-specific fields without adding new top-level source schemas",
        ),
        field_policy(
            "resolution_text_criteria",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["resolutionCriteria.yesCriteria", "resolutionCriteria.noCriteria"],
            reason="Outcome interpretation prose is domain-specific while resolution criteria are universal.",
            domain_extension_allowed=True,
            safe_next_action="write domain-specific criteria inside the resolutionCriteria object",
        ),
        field_policy(
            "exclusion_reason_codes",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["exclusionRules[].reasonCode"],
            reason="Domains need their own unscorable and manual-review reason codes.",
            domain_extension_allowed=True,
            safe_next_action="add domain-specific reason codes inside exclusion rules",
        ),
        field_policy(
            "domain_specific_horizon_labels",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["horizons[].label", "horizons[].startsAfter", "horizons[].endsAfter"],
            reason="Horizon wording varies by operational domain, but each domain still needs horizons.",
            domain_extension_allowed=True,
            safe_next_action="store domain horizon labels and timing descriptions inside horizon templates",
        ),
        field_policy(
            "baseline_threshold_values",
            record_surface="domain_config",
            requirement_level="domain_specific_extension",
            field_paths=["baselineMethod.minimumRows", "baselineMethod.minimumPositiveOutcomes"],
            reason="Baseline sample requirements vary by domain but the baseline method object remains universal.",
            domain_extension_allowed=True,
            safe_next_action="set domain-specific thresholds without changing the baseline method container",
        ),
        field_policy(
            "source_quality_threshold_values",
            record_surface="source_binding",
            requirement_level="domain_specific_extension",
            field_paths=["preForecastChecks[].minimumScore"],
            reason="Quality thresholds may differ by domain and source role while the check set stays universal.",
            domain_extension_allowed=True,
            safe_next_action="set source quality thresholds inside preForecastChecks",
        ),
    ]


def blocked_fields() -> list[dict[str, Any]]:
    return [
        field_policy(
            "credential_value",
            record_surface="shared_boundary",
            requirement_level="blocked",
            field_paths=["credentialValue", "apiToken", "password", "secret"],
            reason="OPE records may reference credentials but must not store secret values.",
            domain_extension_allowed=False,
            safe_next_action="replace raw secrets with caller-managed credentialRef values",
        ),
        field_policy(
            "raw_sql_query",
            record_surface="source_binding",
            requirement_level="blocked",
            field_paths=["rawSql", "queryText"],
            reason="Database setup uses approved query manifests, not arbitrary raw SQL fields.",
            domain_extension_allowed=False,
            safe_next_action="use an approved database adapter manifest with a query boundary",
        ),
        field_policy(
            "raw_private_row",
            record_surface="source_binding",
            requirement_level="blocked",
            field_paths=["rows[]", "privatePayload"],
            reason="OPE setup records store sanitized manifests and mappings, not raw private rows.",
            domain_extension_allowed=False,
            safe_next_action="emit sanitized source-adapter output before source intake",
        ),
        field_policy(
            "post_outcome_forecast_evidence",
            record_surface="domain_config",
            requirement_level="blocked",
            field_paths=["forecastTimeEvidence.outcomeRows", "acceptedSourceRoles[].forecastTimeAllowed"],
            reason="Resolution-only evidence must not become forecast-time evidence.",
            domain_extension_allowed=False,
            safe_next_action="mark outcome roles as resolution-only and exclude them before forecast close",
        ),
        field_policy(
            "production_quality_claim",
            record_surface="domain_config",
            requirement_level="blocked",
            field_paths=["claimBoundaries.qualityClaimAllowed", "claimBoundaries.productionReadinessClaimAllowed"],
            reason="New domain configs cannot claim quality or production readiness without scored evidence.",
            domain_extension_allowed=False,
            safe_next_action="keep claim boundaries false until a separate evidence gate passes",
        ),
        field_policy(
            "hosted_runtime_flag",
            record_surface="shared_boundary",
            requirement_level="blocked",
            field_paths=["hostedRuntimeEnabled", "startsNetworkListener"],
            reason="Domain/source field policy does not promote hosted runtime or listeners.",
            domain_extension_allowed=False,
            safe_next_action="use runtime transport readiness before adding hosted or network surfaces",
        ),
    ]


def source_kind_field_rules() -> list[dict[str, Any]]:
    rules = [
        ("fixture", False, "Committed fixtures need source and adapter references but no credentials."),
        ("local_file", False, "Approved local files use sanitized manifests and path boundaries."),
        ("source_adapter_output", False, "Adapter outputs hand OPE sanitized manifests, mappings, and provenance."),
        ("api", True, "Private API bindings require credential references and approved adapter boundaries."),
        ("database", True, "Database bindings require credential references and approved query manifests."),
    ]
    return [
        {
            "sourceKind": source_kind,
            "sourceRefRequired": True,
            "adapterRefRequired": True,
            "credentialReferenceRequired": credential_required,
            "credentialValueAllowed": False,
            "rawPayloadStored": False,
            "sanitizedManifestRequired": True,
            "queryBoundaryRequired": source_kind in {"api", "database"},
            "notes": notes,
        }
        for source_kind, credential_required, notes in rules
    ]


def field_decision_case(
    case_name: str,
    case_status: str,
    target_record_surface: str,
    field_policy_name: str,
    case_result: str,
    safe_next_action: str,
    *,
    policy_violation: bool,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": case_status,
        "targetRecordSurface": target_record_surface,
        "fieldPolicyName": field_policy_name,
        "caseResult": case_result,
        "safeNextAction": safe_next_action,
        "policyViolation": policy_violation,
        "forecastArtifactsCreated": False,
        "credentialValuesStored": False,
        "rawPrivateDataStored": False,
        "sanitizedDiagnosticsOnly": True,
    }


def field_decision_cases() -> list[dict[str, Any]]:
    return [
        field_decision_case(
            "weather_transit_core_ready",
            "accepted_universal_domain_fields",
            "domain_config",
            "domain_identity",
            "weather transit config carries every universal domain field",
            "allow source binding checks to continue",
            policy_violation=False,
        ),
        field_decision_case(
            "seaport_extension_ready",
            "accepted_domain_specific_extensions",
            "domain_config",
            "role_required_fields",
            "seaport parameters and role fields stay inside extension-safe containers",
            "keep candidate setup behind source confirmation",
            policy_violation=False,
        ),
        field_decision_case(
            "missing_resolution_criteria",
            "blocked_missing_required_domain_field",
            "domain_config",
            "resolution_criteria",
            "domain config cannot omit outcome interpretation",
            "add resolution criteria before source binding or forecast execution",
            policy_violation=True,
        ),
        field_decision_case(
            "credential_value_in_source_binding",
            "blocked_credential_value_storage",
            "source_binding",
            "credential_value",
            "raw credential-like content must be redacted and rejected",
            "replace the value with a caller-owned credential reference",
            policy_violation=True,
        ),
        field_decision_case(
            "raw_sql_query_as_binding_field",
            "blocked_raw_sql_field",
            "source_binding",
            "raw_sql_query",
            "raw SQL cannot become an OPE source-binding field",
            "use an approved database query manifest boundary",
            policy_violation=True,
        ),
        field_decision_case(
            "domain_quality_claim_enabled",
            "blocked_claim_boundary_violation",
            "domain_config",
            "production_quality_claim",
            "new domain configs must keep quality and production claims false",
            "wait for scored evidence and a separate readiness gate",
            policy_violation=True,
        ),
        field_decision_case(
            "outcome_role_marked_forecast_time",
            "blocked_resolution_role_forecast_time_leakage",
            "domain_config",
            "post_outcome_forecast_evidence",
            "resolution-only roles cannot be forecast-time evidence",
            "mark outcome roles resolution-only and rerun leakage checks",
            policy_violation=True,
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    rows = [
        ("cli", "python3 scripts/ope.py domain-source-field-policy", "Prints the checked field policy readback."),
        ("domain_configs", "python3 scripts/ope.py domain-configs", "Source domain configs for required field containers."),
        ("source_bindings", "python3 scripts/ope.py source-bindings", "Source binding cases for source field and safety boundaries."),
        ("source_quality", "python3 scripts/ope.py source-quality", "Source quality and mapping confidence remain separate readbacks."),
        ("source_intake", "python3 scripts/ope.py source-intake", "Source intake uses the resulting manifests and mappings."),
        ("runtime_security", "python3 scripts/ope.py runtime-security", "Runtime security blocks credentials, raw SQL, and private payloads."),
        ("workspace_tenant_isolation", "python3 scripts/ope.py workspace-tenant-isolation", "Tenant isolation scopes source bindings and credential references."),
    ]
    return [
        {
            "readbackSurface": surface,
            "command": command,
            "mutatesState": False,
            "startsNetworkListener": False,
            "credentialValuesReturned": False,
            "notes": notes,
        }
        for surface, command, notes in rows
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksWriteState": False,
        "createsForecasts": False,
        "readsPrivateData": False,
        "storesCredentialValues": False,
        "rawSqlAllowed": False,
        "arbitraryPrivateApiParsingByOpe": False,
        "arbitraryDatabaseParsingByOpe": False,
        "hostedRuntimeImplemented": False,
        "qualityClaimsUpgraded": False,
    }


def build_domain_source_field_policy() -> dict[str, Any]:
    configs = build_domain_configs()
    bindings = build_source_bindings()
    domain_fields = universal_domain_fields()
    source_fields = universal_source_binding_fields()
    extension_fields = domain_specific_extension_fields()
    blocked = blocked_fields()
    cases = field_decision_cases()
    record = {
        "domainSourceFieldPolicyId": "domainsourcefieldpolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "domain_source_field_policy_checked",
        "decisionStatus": "universal_domain_and_source_fields_with_domain_extension_boundary",
        "normalChecksMutateState": False,
        "generatedRuntimeTypesIncluded": False,
        "sourceBinding": {
            "domainConfigCommand": "python3 scripts/ope.py domain-configs",
            "sourceBindingCommand": "python3 scripts/ope.py source-bindings",
            "domainConfigCount": len(configs),
            "sourceBindingCaseCount": len(bindings),
            "boundDomainKeys": [item["domainKey"] for item in configs.values()],
            "boundSourceBindingCases": [item["bindingCase"] for item in bindings.values()],
            "rawSourceDataRead": False,
            "notes": "Field policy is derived from checked domain config and source binding surfaces.",
        },
        "universalDomainFields": domain_fields,
        "universalSourceBindingFields": source_fields,
        "domainSpecificExtensionFields": extension_fields,
        "blockedFields": blocked,
        "sourceKindFieldRules": source_kind_field_rules(),
        "fieldDecisionCases": cases,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "universalDomainFieldCount": len(domain_fields),
            "universalSourceBindingFieldCount": len(source_fields),
            "domainSpecificExtensionFieldCount": len(extension_fields),
            "blockedFieldCount": len(blocked),
            "sourceKindRuleCount": 5,
            "fieldDecisionCaseCount": len(cases),
            "normalChecksMutateState": False,
            "generatedRuntimeTypesIncluded": False,
        },
        "warnings": [
            "This policy classifies fields only; it does not create forecasts or execute private sources.",
            "Domain-specific vocabulary belongs inside approved extension containers, not new top-level records.",
            "Credential values, raw SQL, raw private rows, hosted runtime flags, and premature quality claims are blocked.",
        ],
    }
    validate_domain_source_field_policy(record)
    return record


def validate_domain_source_field_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise DomainSourceFieldPolicyError(f"domain source field policy schema validation failed: {errors[0]}")
    if [item["fieldPolicyName"] for item in record["universalDomainFields"]] != UNIVERSAL_DOMAIN_FIELDS:
        raise DomainSourceFieldPolicyError("universal domain field order drifted")
    if [item["fieldPolicyName"] for item in record["universalSourceBindingFields"]] != UNIVERSAL_SOURCE_FIELDS:
        raise DomainSourceFieldPolicyError("universal source field order drifted")
    if [item["fieldPolicyName"] for item in record["domainSpecificExtensionFields"]] != DOMAIN_EXTENSION_FIELDS:
        raise DomainSourceFieldPolicyError("domain extension field order drifted")
    if [item["fieldPolicyName"] for item in record["blockedFields"]] != BLOCKED_FIELDS:
        raise DomainSourceFieldPolicyError("blocked field order drifted")
    if [item["caseName"] for item in record["fieldDecisionCases"]] != FIELD_CASES:
        raise DomainSourceFieldPolicyError("field decision case order drifted")
    if [item["readbackSurface"] for item in record["readbacks"]] != READBACKS:
        raise DomainSourceFieldPolicyError("readback order drifted")
    for item in [*record["universalDomainFields"], *record["universalSourceBindingFields"]]:
        if item["domainExtensionAllowed"]:
            raise DomainSourceFieldPolicyError("universal fields must not move to domain extensions")
        if item["credentialValuesAllowed"] or item["rawPrivateDataAllowed"]:
            raise DomainSourceFieldPolicyError("universal fields must block credentials and raw private data")
    for item in record["domainSpecificExtensionFields"]:
        if not item["domainExtensionAllowed"]:
            raise DomainSourceFieldPolicyError("domain-specific fields must be marked extension-safe")
        if item["credentialValuesAllowed"] or item["rawPrivateDataAllowed"]:
            raise DomainSourceFieldPolicyError("domain-specific extensions must block credentials and raw private data")
    for item in record["blockedFields"]:
        if item["requirementLevel"] != "blocked":
            raise DomainSourceFieldPolicyError("blocked fields must use blocked requirement level")
        if item["domainExtensionAllowed"] or item["credentialValuesAllowed"] or item["rawPrivateDataAllowed"]:
            raise DomainSourceFieldPolicyError("blocked fields must stay blocked across all value classes")
    if any(record["executionBoundary"].values()):
        raise DomainSourceFieldPolicyError("execution boundary flags should stay false")


def field_payload(record: dict[str, Any], field_policy_name: str) -> dict[str, Any]:
    for section in [
        "universalDomainFields",
        "universalSourceBindingFields",
        "domainSpecificExtensionFields",
        "blockedFields",
    ]:
        for item in record[section]:
            if item["fieldPolicyName"] == field_policy_name:
                return item
    raise DomainSourceFieldPolicyError(f"unknown field policy {field_policy_name}")


def case_payload(record: dict[str, Any], case_name: str) -> dict[str, Any]:
    for item in record["fieldDecisionCases"]:
        if item["caseName"] == case_name:
            return item
    raise DomainSourceFieldPolicyError(f"unknown field case {case_name}")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBinding"]
    if view == "domain-fields":
        return record["universalDomainFields"]
    if view == "source-fields":
        return record["universalSourceBindingFields"]
    if view == "extensions":
        return record["domainSpecificExtensionFields"]
    if view == "blocked":
        return record["blockedFields"]
    if view == "source-kinds":
        return record["sourceKindFieldRules"]
    if view == "cases":
        return record["fieldDecisionCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise DomainSourceFieldPolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated domain/source field policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated domain/source field policy fixture")
    parser.add_argument(
        "--field",
        choices=[*UNIVERSAL_DOMAIN_FIELDS, *UNIVERSAL_SOURCE_FIELDS, *DOMAIN_EXTENSION_FIELDS, *BLOCKED_FIELDS],
        help="print one field policy row",
    )
    parser.add_argument("--case", choices=FIELD_CASES, help="print one field decision case")
    parser.add_argument(
        "--view",
        choices=[
            "full",
            "source",
            "domain-fields",
            "source-fields",
            "extensions",
            "blocked",
            "source-kinds",
            "cases",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="emit a focused domain/source field policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_domain_source_field_policy()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="domain source field policy",
            regen="python3 scripts/generate_domain_source_field_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="domain source field policy",
            regen="python3 scripts/generate_domain_source_field_policy.py --write",
        )
        return
    if args.field:
        print(render_json(field_payload(record, args.field)), end="")
        return
    if args.case:
        print(render_json(case_payload(record, args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
