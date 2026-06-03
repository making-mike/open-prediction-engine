#!/usr/bin/env python3
"""Generate or check private source adapter capability declarations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_workflow import build_workflow, load_generated_workflow
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-source-adapters"
CAPABILITY_PATH = GENERATED / "ope-private-source-adapter-capabilities.generated.json"
SCHEMA = SPEC / "private-source-adapter-capability.schema.json"
GENERATED_AT = "2026-06-06T21:00:00Z"
SUPPORTED_SOURCE_ORDER = [
    "local_file",
    "manual_mapping",
    "manual_upload",
    "auto_evidence_connector",
    "private_api",
    "private_database",
]


class PrivateSourceAdapterCapabilityError(Exception):
    pass


def adapter(
    *,
    adapter_id: str,
    source_kind: str,
    display_name: str,
    implementation_status: str,
    availability_status: str,
    setup_outcome: str,
    can_inspect: bool,
    can_execute_in_normal_checks: bool,
    approval_required: bool,
    credential_boundary: str,
    prompt_visibility: str,
    privacy_boundary: str,
    freshness_boundary: str,
    rate_limit_boundary: str,
    audit_log_boundary: str,
    supported_contracts: list[str],
    blocked_actions: list[str],
    next_action: str,
    can_fetch_live: bool = False,
    can_parse_generic: bool = False,
    can_store_secrets: bool = False,
) -> dict[str, Any]:
    return {
        "adapterId": adapter_id,
        "sourceKind": source_kind,
        "displayName": display_name,
        "implementationStatus": implementation_status,
        "availabilityStatus": availability_status,
        "setupOutcomeIfRequested": setup_outcome,
        "canInspect": can_inspect,
        "canFetchLive": can_fetch_live,
        "canParseGeneric": can_parse_generic,
        "canStoreSecrets": can_store_secrets,
        "canExecuteInNormalChecks": can_execute_in_normal_checks,
        "approvalRequired": approval_required,
        "credentialBoundary": credential_boundary,
        "promptVisibility": prompt_visibility,
        "privacyBoundary": privacy_boundary,
        "freshnessBoundary": freshness_boundary,
        "rateLimitBoundary": rate_limit_boundary,
        "auditLogBoundary": audit_log_boundary,
        "supportedContracts": supported_contracts,
        "blockedActions": blocked_actions,
        "nextAction": next_action,
    }


def adapters() -> list[dict[str, Any]]:
    common_blocked = [
        "store_credentials",
        "include_secrets_in_artifacts",
        "create_forecast_without_intake",
    ]
    return [
        adapter(
            adapter_id="privateadapter-local-file-001",
            source_kind="local_file",
            display_name="Local file source builder",
            implementation_status="implemented_fixture",
            availability_status="available_fixture",
            setup_outcome="setup_ready",
            can_inspect=True,
            can_execute_in_normal_checks=True,
            approval_required=False,
            credential_boundary="none_required",
            prompt_visibility="metadata_only_prompt_visible",
            privacy_boundary="Only caller-approved CSV/JSON fixture paths and sanitized metadata enter build records.",
            freshness_boundary="No watcher exists; freshness comes from explicit caller-provided files.",
            rate_limit_boundary="No remote rate limit; local checks cap file size and source count.",
            audit_log_boundary="Build records capture inspected file metadata, rejection reasons, and generated draft paths.",
            supported_contracts=[
                "spec/source-manifest-build.schema.json",
                "spec/source-manifest.schema.json",
                "spec/field-mapping.schema.json",
                "spec/source-intake-handoff.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "fetch_live_private_api",
                "connect_private_database",
                "parse_arbitrary_private_schema",
                "claim_live_freshness",
            ],
            next_action="use_source_builder",
        ),
        adapter(
            adapter_id="privateadapter-manual-mapping-001",
            source_kind="manual_mapping",
            display_name="Manual mapping confirmation",
            implementation_status="implemented_fixture",
            availability_status="approval_gated_fixture",
            setup_outcome="needs_confirmation",
            can_inspect=True,
            can_execute_in_normal_checks=True,
            approval_required=True,
            credential_boundary="none_required",
            prompt_visibility="metadata_only_prompt_visible",
            privacy_boundary="Only mapping decisions and sanitized field names are prompt-visible.",
            freshness_boundary="Freshness is inherited from the source manifest being confirmed.",
            rate_limit_boundary="No remote rate limit; confirmation is a caller-supervised local action.",
            audit_log_boundary="Handoff records capture whether mappings are proposed, confirmed, or rejected.",
            supported_contracts=[
                "spec/field-mapping.schema.json",
                "spec/source-intake-handoff.schema.json",
                "spec/source-intake-report.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "fetch_live_private_api",
                "connect_private_database",
                "parse_arbitrary_private_schema",
            ],
            next_action="use_manual_mapping_confirmation",
        ),
        adapter(
            adapter_id="privateadapter-manual-upload-001",
            source_kind="manual_upload",
            display_name="Manual upload intake",
            implementation_status="planned_contract_only",
            availability_status="planned_contract_only",
            setup_outcome="runtime_not_implemented",
            can_inspect=False,
            can_execute_in_normal_checks=False,
            approval_required=True,
            credential_boundary="none_required",
            prompt_visibility="no_secrets_prompt_visible",
            privacy_boundary="No uploaded bytes or private rows enter artifacts because upload intake is not implemented.",
            freshness_boundary="Upload recency must be declared by a future runtime; current checks cannot verify it.",
            rate_limit_boundary="Future upload intake must declare size and rate limits before execution.",
            audit_log_boundary="Future runtime must record approval, upload reference, hash, timestamp, and sanitized errors.",
            supported_contracts=[
                "spec/private-source-adapter-capability.schema.json",
                "spec/private-setup-workflow.schema.json",
                "spec/source-policy.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "ingest_manual_upload",
                "parse_arbitrary_private_schema",
                "claim_live_freshness",
            ],
            next_action="wait_for_runtime",
        ),
        adapter(
            adapter_id="privateadapter-auto-evidence-001",
            source_kind="auto_evidence_connector",
            display_name="Policy-bound auto-evidence fixture connector",
            implementation_status="implemented_fixture",
            availability_status="available_fixture",
            setup_outcome="setup_ready",
            can_inspect=True,
            can_execute_in_normal_checks=True,
            approval_required=False,
            credential_boundary="none_required",
            prompt_visibility="metadata_only_prompt_visible",
            privacy_boundary="Fixture replay exposes normalized public fixture metadata, not private live connector payloads.",
            freshness_boundary="Normal checks use committed fixtures; live freshness is only an explicit opt-in readiness probe.",
            rate_limit_boundary="Normal checks make no network calls, so external connector rate limits are not exercised.",
            audit_log_boundary="Connector result records capture fixture status, unavailable evidence, and sanitized diagnostics.",
            supported_contracts=[
                "spec/source-policy.schema.json",
                "spec/evidence-gathering-plan.schema.json",
                "spec/evidence-source-set.schema.json",
                "spec/source-connector-registry.schema.json",
                "spec/source-connector-result-set.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "fetch_live_private_api",
                "connect_private_database",
                "claim_live_freshness",
            ],
            next_action="use_auto_evidence_fixture",
        ),
        adapter(
            adapter_id="privateadapter-private-api-001",
            source_kind="private_api",
            display_name="Private API connector",
            implementation_status="planned_contract_only",
            availability_status="planned_contract_only",
            setup_outcome="runtime_not_implemented",
            can_inspect=False,
            can_execute_in_normal_checks=False,
            approval_required=True,
            credential_boundary="caller_provided_out_of_band",
            prompt_visibility="no_secrets_prompt_visible",
            privacy_boundary="No private API credentials, request payloads, or response rows enter generated artifacts.",
            freshness_boundary="Future adapters must declare request time, cache policy, and source freshness before forecasting.",
            rate_limit_boundary="Future adapters must declare rate limits and retries before any call is allowed.",
            audit_log_boundary="Future runtime must record approval, endpoint identity, scopes, timestamps, and sanitized errors.",
            supported_contracts=[
                "spec/private-source-adapter-capability.schema.json",
                "spec/private-setup-workflow.schema.json",
                "spec/source-policy.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "fetch_live_private_api",
                "parse_arbitrary_private_schema",
                "run_effectful_query",
                "claim_live_freshness",
            ],
            next_action="wait_for_runtime",
        ),
        adapter(
            adapter_id="privateadapter-private-database-001",
            source_kind="private_database",
            display_name="Private database connector",
            implementation_status="planned_contract_only",
            availability_status="planned_contract_only",
            setup_outcome="runtime_not_implemented",
            can_inspect=False,
            can_execute_in_normal_checks=False,
            approval_required=True,
            credential_boundary="caller_provided_out_of_band",
            prompt_visibility="no_secrets_prompt_visible",
            privacy_boundary="No database credentials, query text with secrets, or private rows enter generated artifacts.",
            freshness_boundary="Future adapters must declare query timestamp, isolation, and freshness policy before forecasting.",
            rate_limit_boundary="Future adapters must declare query limits, timeout, and retry policy before execution.",
            audit_log_boundary="Future runtime must record approval, dataset identity, query boundary, timestamps, and sanitized errors.",
            supported_contracts=[
                "spec/private-source-adapter-capability.schema.json",
                "spec/private-setup-workflow.schema.json",
                "spec/source-policy.schema.json",
            ],
            blocked_actions=common_blocked
            + [
                "connect_private_database",
                "parse_arbitrary_private_schema",
                "run_effectful_query",
                "claim_live_freshness",
            ],
            next_action="wait_for_runtime",
        ),
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privateadapterguard-001",
            "name": "declaration_only",
            "rule": "Capability records describe adapter boundaries and must not execute source reads by implication.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py"],
        },
        {
            "guardId": "privateadapterguard-002",
            "name": "workflow_source_binding",
            "rule": "Adapter source kinds must match the domain-agnostic private setup workflow source kinds.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py"],
        },
        {
            "guardId": "privateadapterguard-003",
            "name": "no_secret_storage",
            "rule": "Adapters must not store credentials or expose secrets in generated artifacts.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py", "scripts/check_hardening.py"],
        },
        {
            "guardId": "privateadapterguard-004",
            "name": "normal_checks_offline",
            "rule": "Normal checks may inspect fixtures but must not fetch live private API or database data.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py", "scripts/run_checks.py"],
        },
        {
            "guardId": "privateadapterguard-005",
            "name": "planned_private_runtimes",
            "rule": "Private API, private database, and manual upload adapters remain non-executable until a runtime lands.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py"],
        },
        {
            "guardId": "privateadapterguard-006",
            "name": "freshness_and_audit_boundary",
            "rule": "Freshness, rate-limit, privacy, and audit boundaries must be declared before setup attempts.",
            "checkedBy": ["scripts/check_private_source_adapter_capabilities.py"],
        },
    ]


def build_capabilities() -> dict[str, Any]:
    workflow = build_workflow()
    capability = {
        "privateSourceAdapterCapabilityId": "privatesourceadaptercapability-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "capability_contract_only",
        "boundPrivateSetupWorkflowId": workflow["privateSetupWorkflowId"],
        "boundPrivateSetupWorkflowPath": "spec/fixtures/generated/private-setup-workflow/ope-private-setup-workflow.generated.json",
        "supportedSourceKinds": SUPPORTED_SOURCE_ORDER,
        "adapters": adapters(),
        "executionBoundary": {
            "declarationsDoNotExecute": True,
            "normalChecksOffline": True,
            "credentialStorageImplemented": False,
            "genericPrivateApiRuntimeImplemented": False,
            "genericPrivateDatabaseRuntimeImplemented": False,
            "manualUploadRuntimeImplemented": False,
            "arbitraryPrivateSchemaParsingImplemented": False,
        },
        "guards": guards(),
        "warnings": [
            "This is a capability declaration, not a connector runtime.",
            "Private API, private database, and manual upload adapters cannot execute in the current local surface.",
            "No adapter may store credentials or include secrets in forecast artifacts.",
            "Normal checks remain offline and fixture-safe.",
        ],
    }
    validate_capabilities(capability, workflow)
    return capability


def validate_capabilities(capability: dict[str, Any], workflow: dict[str, Any]) -> None:
    errors = validate_record(capability, SCHEMA)
    if errors:
        raise PrivateSourceAdapterCapabilityError(f"private source adapter capability schema validation failed: {errors[0]}")

    workflow_source_kinds = [item["sourceKind"] for item in workflow["supportedSourceKinds"]]
    if workflow_source_kinds != SUPPORTED_SOURCE_ORDER:
        raise PrivateSourceAdapterCapabilityError("private setup workflow source kind order drift")
    if capability["supportedSourceKinds"] != workflow_source_kinds:
        raise PrivateSourceAdapterCapabilityError("capability source kinds must match private setup workflow")

    adapters_by_kind = {item["sourceKind"]: item for item in capability["adapters"]}
    if list(adapters_by_kind) != SUPPORTED_SOURCE_ORDER:
        raise PrivateSourceAdapterCapabilityError("adapter source kind order drift")
    if set(adapters_by_kind) != set(workflow_source_kinds):
        raise PrivateSourceAdapterCapabilityError("adapter source kind set must match private setup workflow")

    workflow_support = {item["sourceKind"]: item for item in workflow["supportedSourceKinds"]}
    for source_kind, item in adapters_by_kind.items():
        if item["implementationStatus"] != workflow_support[source_kind]["implementationStatus"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} implementation status must match workflow support")
        if item["canStoreSecrets"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must not store secrets")
        if item["canExecuteInNormalChecks"] and item["canFetchLive"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must not live-fetch in normal checks")
        if "include_secrets_in_artifacts" not in item["blockedActions"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must block secret artifact inclusion")
        if "create_forecast_without_intake" not in item["blockedActions"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must block forecasts without intake")

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        item = adapters_by_kind[source_kind]
        if item["setupOutcomeIfRequested"] != "runtime_not_implemented":
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must resolve to runtime_not_implemented")
        if item["nextAction"] != "wait_for_runtime":
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} should wait for runtime")
        if item["canInspect"] or item["canFetchLive"] or item["canParseGeneric"] or item["canExecuteInNormalChecks"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} must remain non-executable")
        if not item["approvalRequired"]:
            raise PrivateSourceAdapterCapabilityError(f"{source_kind} should remain approval-gated")

    if adapters_by_kind["local_file"]["nextAction"] != "use_source_builder":
        raise PrivateSourceAdapterCapabilityError("local_file should route to source builder")
    if adapters_by_kind["manual_mapping"]["nextAction"] != "use_manual_mapping_confirmation":
        raise PrivateSourceAdapterCapabilityError("manual_mapping should route to mapping confirmation")
    if adapters_by_kind["manual_mapping"]["approvalRequired"] is not True:
        raise PrivateSourceAdapterCapabilityError("manual_mapping should require caller confirmation")
    if adapters_by_kind["auto_evidence_connector"]["canFetchLive"]:
        raise PrivateSourceAdapterCapabilityError("auto_evidence_connector must not live-fetch in normal checks")

    boundary = capability["executionBoundary"]
    expected_false_keys = [
        "credentialStorageImplemented",
        "genericPrivateApiRuntimeImplemented",
        "genericPrivateDatabaseRuntimeImplemented",
        "manualUploadRuntimeImplemented",
        "arbitraryPrivateSchemaParsingImplemented",
    ]
    if boundary["declarationsDoNotExecute"] is not True or boundary["normalChecksOffline"] is not True:
        raise PrivateSourceAdapterCapabilityError("capability execution boundary should be declaration-only and offline")
    for key in expected_false_keys:
        if boundary[key] is not False:
            raise PrivateSourceAdapterCapabilityError(f"{key} should remain false")


def write_capabilities(capability: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    CAPABILITY_PATH.write_text(render_json(capability), encoding="utf-8")
    print("generated private source adapter capabilities")


def check_capabilities(capability: dict[str, Any]) -> None:
    expected = render_json(capability)
    if not CAPABILITY_PATH.exists():
        print(f"missing private source adapter capabilities: {CAPABILITY_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_source_adapter_capabilities.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = CAPABILITY_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private source adapter capability drift: {CAPABILITY_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_source_adapter_capabilities.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private source adapter capabilities")


def load_generated_capabilities() -> dict[str, Any] | None:
    if not CAPABILITY_PATH.exists():
        return None
    capability = json.loads(CAPABILITY_PATH.read_text(encoding="utf-8"))
    workflow = load_generated_workflow() or build_workflow()
    validate_capabilities(capability, workflow)
    return capability


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private source adapter capability drift")
    parser.add_argument("--write", action="store_true", help="write generated private source adapter capability records")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.write or args.check or args.rebuild:
            capability = build_capabilities()
        else:
            capability = load_generated_capabilities() or build_capabilities()
    except PrivateSourceAdapterCapabilityError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_capabilities(capability)
    elif args.check:
        check_capabilities(capability)
    else:
        sys.stdout.write(render_json(capability))


if __name__ == "__main__":
    main()
