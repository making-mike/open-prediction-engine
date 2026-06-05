#!/usr/bin/env python3
"""Generate a checked credential-reference policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_database_source_adapter_runtime import build_database_source_adapter_runtime
from generate_source_bindings import build_source_bindings
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "credential-reference-policy"
OUTPUT_PATH = GENERATED / "ope-credential-reference-policy.generated.json"
SCHEMA = SPEC / "credential-reference-policy.schema.json"
GENERATED_AT = "2026-06-05T00:26:00Z"

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


class CredentialReferencePolicyError(Exception):
    pass


def reference_mechanism(
    name: str,
    allowed_for_source_kinds: list[str],
    notes: str,
    safe_next_action: str,
    *,
    caller_approval_required: bool = True,
    rotation_supported: bool = True,
    revocation_supported: bool = True,
) -> dict[str, Any]:
    return {
        "mechanismName": name,
        "mechanismStatus": "accepted_reference_mechanism",
        "allowedForSourceKinds": allowed_for_source_kinds,
        "requiredScopeKeys": SCOPE_KEYS,
        "callerApprovalRequired": caller_approval_required,
        "rotationSupported": rotation_supported,
        "revocationSupported": revocation_supported,
        "secretValueStored": False,
        "secretLookupDuringNormalChecks": False,
        "promptVisibleSecretAllowed": False,
        "notes": notes,
        "safeNextAction": safe_next_action,
    }


def accepted_reference_mechanisms() -> list[dict[str, Any]]:
    return [
        reference_mechanism(
            "caller_secret_store_alias",
            ["api", "database"],
            "The caller owns the secret store and passes OPE only an opaque reference bound to source setup scope.",
            "store only the opaque caller-managed credentialRef in OPE records",
        ),
        reference_mechanism(
            "host_runtime_secret_handle",
            ["api", "database"],
            "A host application may resolve a scoped secret handle outside OPE during explicit runtime execution.",
            "keep the handle scoped and resolve it only in the host runtime, never in normal checks",
        ),
        reference_mechanism(
            "local_operator_session_ref",
            ["api", "database"],
            "A local operator may provide an ephemeral session reference for an explicit command without persisting a secret.",
            "require an approval receipt and avoid writing the resolved value to OPE records",
        ),
        reference_mechanism(
            "public_no_credential",
            ["fixture", "local_file", "source_adapter_output", "api"],
            "Public fixtures, local files, sanitized adapter outputs, and public APIs may use the explicit no-credential sentinel.",
            "use the no-credential sentinel only when the source policy marks credentials unnecessary",
            caller_approval_required=False,
            rotation_supported=False,
            revocation_supported=False,
        ),
    ]


def scope_key(name: str, prevents: str, safe_next_action: str) -> dict[str, Any]:
    return {
        "scopeKeyName": name,
        "requiredForPrivateApi": True,
        "requiredForDatabase": True,
        "containsSecretMaterial": False,
        "prevents": prevents,
        "safeNextAction": safe_next_action,
    }


def required_scope_keys() -> list[dict[str, Any]]:
    return [
        scope_key("tenant_id", "cross-tenant credential reference reuse", "bind the reference to the caller tenant"),
        scope_key("workspace_id", "cross-workspace source reuse", "bind the reference to one prediction workspace"),
        scope_key("source_binding_id", "credential reuse outside the confirmed source binding", "attach the reference to one source binding"),
        scope_key("source_role", "using resolution-only or unrelated credentials as forecast-time sources", "bind the reference to the source role"),
        scope_key("adapter_ref", "using the reference with an unapproved adapter", "bind the reference to the adapter identity"),
        scope_key("source_kind", "using API credentials in database flows or database credentials in API flows", "bind the reference to source kind"),
        scope_key("source_policy_id", "bypassing freshness, leakage, and source-policy gates", "bind the reference to a checked source policy"),
        scope_key("credential_purpose", "broad all-purpose secret handles", "declare read-only API or read-only database purpose"),
    ]


def lifecycle_state(
    name: str,
    status: str,
    safe_next_action: str,
    *,
    allows_runtime_use: bool,
    requires_approval_receipt: bool,
    requires_redaction_receipt: bool,
) -> dict[str, Any]:
    return {
        "stateName": name,
        "stateStatus": status,
        "allowsRuntimeUse": allows_runtime_use,
        "allowsNormalCheckSecretResolution": False,
        "requiresApprovalReceipt": requires_approval_receipt,
        "requiresRedactionReceipt": requires_redaction_receipt,
        "credentialValuesStored": False,
        "safeNextAction": safe_next_action,
    }


def lifecycle_states() -> list[dict[str, Any]]:
    return [
        lifecycle_state(
            "proposed",
            "waiting_for_approval",
            "collect caller approval and scope binding before runtime use",
            allows_runtime_use=False,
            requires_approval_receipt=True,
            requires_redaction_receipt=False,
        ),
        lifecycle_state(
            "approved",
            "approved_not_resolved",
            "allow source-binding validation but do not resolve the secret in normal checks",
            allows_runtime_use=False,
            requires_approval_receipt=True,
            requires_redaction_receipt=False,
        ),
        lifecycle_state(
            "active",
            "runtime_use_allowed_when_explicit",
            "allow explicit approved adapter runtime to ask the caller or host to resolve the reference",
            allows_runtime_use=True,
            requires_approval_receipt=True,
            requires_redaction_receipt=False,
        ),
        lifecycle_state(
            "rotation_due",
            "rotation_required",
            "rotate the caller-owned reference before accepting new runtime use",
            allows_runtime_use=False,
            requires_approval_receipt=True,
            requires_redaction_receipt=False,
        ),
        lifecycle_state(
            "revoked",
            "blocked_revoked",
            "replace the reference and rerun source-binding validation",
            allows_runtime_use=False,
            requires_approval_receipt=True,
            requires_redaction_receipt=False,
        ),
        lifecycle_state(
            "redaction_required",
            "blocked_redaction_required",
            "write a redaction receipt for unsafe submitted material before continuing",
            allows_runtime_use=False,
            requires_approval_receipt=True,
            requires_redaction_receipt=True,
        ),
    ]


def consumer_rule(
    name: str,
    allowed_operations: list[str],
    notes: str,
    *,
    may_use_credential_reference: bool,
    requires_approval: bool,
) -> dict[str, Any]:
    return {
        "consumerName": name,
        "mayUseCredentialReference": may_use_credential_reference,
        "canResolveSecretInNormalChecks": False,
        "canReceiveCredentialValue": False,
        "requiresScopeMatch": True,
        "requiresAdapterMatch": True,
        "requiresApproval": requires_approval,
        "allowedOperations": allowed_operations,
        "notes": notes,
    }


def consumer_rules() -> list[dict[str, Any]]:
    return [
        consumer_rule(
            "private_api_adapter",
            ["validate_reference", "explicit_runtime_fetch"],
            "Private API adapters may receive only scoped references after caller approval; private API runtime is still future work.",
            may_use_credential_reference=True,
            requires_approval=True,
        ),
        consumer_rule(
            "database_adapter",
            ["validate_reference", "explicit_runtime_query"],
            "The checked database adapter runtime may bind a scoped credentialRef but normal checks do not open databases.",
            may_use_credential_reference=True,
            requires_approval=True,
        ),
        consumer_rule(
            "source_binding_validation",
            ["validate_scope", "check_secret_absence"],
            "Source binding validation checks reference shape and scope but never resolves a secret value.",
            may_use_credential_reference=True,
            requires_approval=True,
        ),
        consumer_rule(
            "runtime_readback",
            ["print_status", "print_boundary"],
            "Runtime readbacks may show reference status, scope, and next action without secret material.",
            may_use_credential_reference=True,
            requires_approval=False,
        ),
        consumer_rule(
            "agent_envelope",
            ["return_status", "return_sanitized_error"],
            "Agent envelopes can mention credentialRef IDs and blockers but cannot accept or return secret values.",
            may_use_credential_reference=True,
            requires_approval=False,
        ),
        consumer_rule(
            "normal_checks",
            ["validate_fixture", "check_drift"],
            "Normal checks can verify policy fixtures but cannot use credential references to resolve secrets.",
            may_use_credential_reference=False,
            requires_approval=False,
        ),
    ]


def credential_reference_case(
    case_name: str,
    case_status: str,
    source_kind: str,
    reference_input_class: str,
    next_action: str,
    *,
    accepted: bool,
    can_enter_adapter_runtime: bool,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": case_status,
        "sourceKind": source_kind,
        "referenceInputClass": reference_input_class,
        "sourceBindingAccepted": accepted,
        "canEnterAdapterRuntime": can_enter_adapter_runtime,
        "credentialValuesStored": False,
        "secretResolvedInNormalChecks": False,
        "crossTenantReuseAllowed": False,
        "sanitizedDiagnosticsOnly": True,
        "nextAction": next_action,
    }


def credential_reference_cases() -> list[dict[str, Any]]:
    return [
        credential_reference_case(
            "accepted_private_api_reference",
            "accepted_private_api_reference",
            "api",
            "opaque_reference",
            "keep private API runtime deferred until a checked adapter exists",
            accepted=True,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "accepted_database_reference",
            "accepted_database_reference",
            "database",
            "opaque_reference",
            "route the scoped reference through the approved database adapter runtime boundary",
            accepted=True,
            can_enter_adapter_runtime=True,
        ),
        credential_reference_case(
            "public_source_no_credential",
            "accepted_public_no_credential",
            "api",
            "none_public_source",
            "use the no-credential sentinel only for public or fixture source policies",
            accepted=True,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "missing_reference_for_private_api",
            "blocked_missing_credential_reference",
            "api",
            "missing_reference",
            "provide a scoped caller-owned credentialRef before private API setup continues",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "raw_api_token_submitted",
            "blocked_raw_api_token",
            "api",
            "raw_secret_value",
            "redact the value and replace it with an opaque caller-owned reference",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "database_password_in_connection_string",
            "blocked_database_password_connection_string",
            "database",
            "raw_connection_string",
            "replace raw connection strings with query manifests and scoped credential references",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "cross_tenant_reference",
            "blocked_cross_tenant_reference",
            "database",
            "wrong_scope",
            "create a new tenant-scoped reference and source binding",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "unscoped_reference",
            "blocked_unscoped_reference",
            "api",
            "unscoped_reference",
            "add tenant, workspace, source-binding, role, adapter, source-kind, policy, and purpose scope",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "adapter_mismatch",
            "blocked_adapter_mismatch",
            "database",
            "wrong_adapter",
            "bind the reference to the approved adapter for this source role",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "revoked_reference",
            "blocked_revoked_reference",
            "api",
            "revoked_reference",
            "replace the revoked reference and rerun source-binding validation",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
        credential_reference_case(
            "normal_check_resolution_attempt",
            "blocked_normal_check_secret_resolution",
            "database",
            "secret_resolution_request",
            "do not resolve secrets in normal checks; use explicit approved runtime only",
            accepted=False,
            can_enter_adapter_runtime=False,
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    rows = [
        ("cli", "python3 scripts/ope.py credential-reference-policy", "Prints the checked credential-reference policy."),
        ("source_bindings", "python3 scripts/ope.py source-bindings", "Binds credentialRef fields to source roles and source kinds."),
        ("domain_source_field_policy", "python3 scripts/ope.py domain-source-field-policy", "Classifies credential policy as a universal source-binding field."),
        ("database_source_adapter_runtime", "python3 scripts/ope.py database-source-adapter-runtime", "Shows one approved database fixture path and missing-reference blockers."),
        ("runtime_security", "python3 scripts/ope.py runtime-security", "Keeps runtime credential handling reference-only."),
        ("workspace_tenant_isolation", "python3 scripts/ope.py workspace-tenant-isolation", "Scopes credential references by tenant and workspace."),
        ("agent_adapter_dispatcher", "python3 scripts/ope.py agent-call --operation database_source_adapter_runtime_status", "Returns credential-safe adapter status envelopes."),
    ]
    return [
        {
            "readbackSurface": surface,
            "command": command,
            "mutatesState": False,
            "resolvesSecrets": False,
            "credentialValuesReturned": False,
            "notes": notes,
        }
        for surface, command, notes in rows
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksResolveSecrets": False,
        "storesCredentialValues": False,
        "printsCredentialValues": False,
        "readsEnvironmentSecrets": False,
        "writesSecretStore": False,
        "crossTenantCredentialReuseAllowed": False,
        "unscopedReferencesAllowed": False,
        "rawConnectionStringsAllowed": False,
        "databaseConnectionsOpened": False,
        "apiCallsExecuted": False,
        "hostedSecretManagerImplemented": False,
        "qualityClaimsUpgraded": False,
    }


def build_credential_reference_policy() -> dict[str, Any]:
    source_bindings = build_source_bindings()
    database_runtime = build_database_source_adapter_runtime()
    mechanisms = accepted_reference_mechanisms()
    scope = required_scope_keys()
    lifecycle = lifecycle_states()
    consumers = consumer_rules()
    cases = credential_reference_cases()
    blocked_count = sum(1 for item in cases if item["caseStatus"].startswith("blocked_"))
    record = {
        "credentialReferencePolicyId": "credentialreferencepolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "credential_reference_policy_checked",
        "decisionStatus": "opaque_caller_owned_references_scoped_to_workspace_source_and_adapter",
        "normalChecksMutateState": False,
        "secretResolverImplemented": False,
        "sourceBinding": {
            "sourceBindingCommand": "python3 scripts/ope.py source-bindings",
            "databaseRuntimeCommand": "python3 scripts/ope.py database-source-adapter-runtime",
            "sourceBindingCaseCount": len(source_bindings),
            "databaseRuntimeCaseCount": len(database_runtime["runtimeCases"]),
            "privateSourceKindsRequiringCredentialRef": ["api", "database"],
            "rawCredentialValuesRead": False,
            "notes": "Policy binds existing source-binding and database-runtime readbacks without resolving secrets.",
        },
        "acceptedReferenceMechanisms": mechanisms,
        "requiredScopeKeys": scope,
        "lifecycleStates": lifecycle,
        "consumerRules": consumers,
        "credentialReferenceCases": cases,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "acceptedReferenceMechanismCount": len(mechanisms),
            "requiredScopeKeyCount": len(scope),
            "lifecycleStateCount": len(lifecycle),
            "consumerRuleCount": len(consumers),
            "credentialReferenceCaseCount": len(cases),
            "blockedCaseCount": blocked_count,
            "normalChecksResolveSecrets": False,
            "secretResolverImplemented": False,
        },
        "warnings": [
            "Credential references are opaque caller-owned identifiers, not secret values or connection strings.",
            "Normal checks validate policy fixtures only and do not resolve secrets, read environment variables, or open databases.",
            "Private API and database references must be scoped to tenant, workspace, source binding, source role, adapter, source kind, source policy, and purpose.",
        ],
    }
    validate_credential_reference_policy(record)
    return record


def validate_credential_reference_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise CredentialReferencePolicyError(f"credential reference policy schema validation failed: {errors[0]}")
    if [item["mechanismName"] for item in record["acceptedReferenceMechanisms"]] != REFERENCE_MECHANISMS:
        raise CredentialReferencePolicyError("reference mechanism order drifted")
    if [item["scopeKeyName"] for item in record["requiredScopeKeys"]] != SCOPE_KEYS:
        raise CredentialReferencePolicyError("scope key order drifted")
    if [item["stateName"] for item in record["lifecycleStates"]] != LIFECYCLE_STATES:
        raise CredentialReferencePolicyError("lifecycle state order drifted")
    if [item["consumerName"] for item in record["consumerRules"]] != CONSUMER_RULES:
        raise CredentialReferencePolicyError("consumer rule order drifted")
    if [item["caseName"] for item in record["credentialReferenceCases"]] != POLICY_CASES:
        raise CredentialReferencePolicyError("credential reference case order drifted")
    if [item["readbackSurface"] for item in record["readbacks"]] != READBACKS:
        raise CredentialReferencePolicyError("readback order drifted")
    for item in record["acceptedReferenceMechanisms"]:
        if item["requiredScopeKeys"] != SCOPE_KEYS:
            raise CredentialReferencePolicyError("mechanism scope keys drifted")
        if item["secretValueStored"] or item["secretLookupDuringNormalChecks"] or item["promptVisibleSecretAllowed"]:
            raise CredentialReferencePolicyError("credential mechanisms must not expose secret values")
    for item in record["requiredScopeKeys"]:
        if not item["requiredForPrivateApi"] or not item["requiredForDatabase"]:
            raise CredentialReferencePolicyError("scope keys must be required for private API and database references")
        if item["containsSecretMaterial"]:
            raise CredentialReferencePolicyError("scope keys must not contain secret material")
    for item in record["consumerRules"]:
        if item["canReceiveCredentialValue"] or item["canResolveSecretInNormalChecks"]:
            raise CredentialReferencePolicyError("consumer rules must block credential values and normal-check resolution")
        if not item["requiresScopeMatch"] or not item["requiresAdapterMatch"]:
            raise CredentialReferencePolicyError("consumer rules must require scope and adapter matches")
    if any(record["executionBoundary"].values()):
        raise CredentialReferencePolicyError("execution boundary flags should stay false")


def mechanism_payload(record: dict[str, Any], mechanism_name: str) -> dict[str, Any]:
    for item in record["acceptedReferenceMechanisms"]:
        if item["mechanismName"] == mechanism_name:
            return item
    raise CredentialReferencePolicyError(f"unknown credential reference mechanism {mechanism_name}")


def scope_key_payload(record: dict[str, Any], scope_key_name: str) -> dict[str, Any]:
    for item in record["requiredScopeKeys"]:
        if item["scopeKeyName"] == scope_key_name:
            return item
    raise CredentialReferencePolicyError(f"unknown credential reference scope key {scope_key_name}")


def lifecycle_payload(record: dict[str, Any], state_name: str) -> dict[str, Any]:
    for item in record["lifecycleStates"]:
        if item["stateName"] == state_name:
            return item
    raise CredentialReferencePolicyError(f"unknown credential reference lifecycle state {state_name}")


def consumer_payload(record: dict[str, Any], consumer_name: str) -> dict[str, Any]:
    for item in record["consumerRules"]:
        if item["consumerName"] == consumer_name:
            return item
    raise CredentialReferencePolicyError(f"unknown credential reference consumer {consumer_name}")


def case_payload(record: dict[str, Any], case_name: str) -> dict[str, Any]:
    for item in record["credentialReferenceCases"]:
        if item["caseName"] == case_name:
            return item
    raise CredentialReferencePolicyError(f"unknown credential reference case {case_name}")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBinding"]
    if view == "mechanisms":
        return record["acceptedReferenceMechanisms"]
    if view == "scope":
        return record["requiredScopeKeys"]
    if view == "lifecycle":
        return record["lifecycleStates"]
    if view == "consumers":
        return record["consumerRules"]
    if view == "cases":
        return record["credentialReferenceCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise CredentialReferencePolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated credential-reference policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated credential-reference policy fixture")
    parser.add_argument("--mechanism", choices=REFERENCE_MECHANISMS, help="print one accepted reference mechanism")
    parser.add_argument("--scope-key", choices=SCOPE_KEYS, help="print one required scope key")
    parser.add_argument("--state", choices=LIFECYCLE_STATES, help="print one lifecycle state")
    parser.add_argument("--consumer", choices=CONSUMER_RULES, help="print one consumer rule")
    parser.add_argument("--case", choices=POLICY_CASES, help="print one credential-reference case")
    parser.add_argument(
        "--view",
        choices=[
            "full",
            "source",
            "mechanisms",
            "scope",
            "lifecycle",
            "consumers",
            "cases",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="emit a focused credential-reference policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_credential_reference_policy()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="credential reference policy",
            regen="python3 scripts/generate_credential_reference_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="credential reference policy",
            regen="python3 scripts/generate_credential_reference_policy.py --write",
        )
        return
    if args.mechanism:
        print(render_json(mechanism_payload(record, args.mechanism)), end="")
        return
    if args.scope_key:
        print(render_json(scope_key_payload(record, args.scope_key)), end="")
        return
    if args.state:
        print(render_json(lifecycle_payload(record, args.state)), end="")
        return
    if args.consumer:
        print(render_json(consumer_payload(record, args.consumer)), end="")
        return
    if args.case:
        print(render_json(case_payload(record, args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
