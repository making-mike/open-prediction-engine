#!/usr/bin/env python3
"""Generate a checked runtime security and hardening readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "runtime-security"
OUTPUT_PATH = GENERATED / "ope-runtime-security.generated.json"
SCHEMA = SPEC / "runtime-security.schema.json"
GENERATED_AT = "2026-06-04T18:20:00Z"


class RuntimeSecurityError(Exception):
    pass


def dependency_budget() -> dict[str, Any]:
    return {
        "coreRuntimeDependencyPolicy": "python_stdlib_only",
        "allowedRuntimeDependencyGroups": ["python_standard_library"],
        "runtimeDependencies": [],
        "runtimeDependencyCount": 0,
        "thirdPartyRuntimeDependenciesAllowed": False,
        "devOnlyDependencies": ["ruff", "mypy"],
        "packageInstallRequiredForNormalChecks": False,
        "checkedBy": [
            "python3 scripts/check_runtime_security.py",
            "python3 scripts/check_hardening.py",
            "python3 scripts/release_check.py",
        ],
        "notes": "Core OPE runtime checks use the Python standard library; ruff and mypy remain release-only static tools.",
    }


def module_boundary(
    name: str,
    path: str,
    responsibility: str,
    allowed_calls: list[str],
    forbidden_calls: list[str],
) -> dict[str, Any]:
    return {
        "moduleName": name,
        "modulePath": path,
        "responsibility": responsibility,
        "allowedCallClasses": allowed_calls,
        "forbiddenCallClasses": forbidden_calls,
        "singleResponsibility": True,
        "rawSqlExposed": False,
        "credentialValuesAccepted": False,
        "hiddenServiceRequired": False,
        "adapterBoundaryDocumented": True,
    }


def module_boundaries() -> list[dict[str, Any]]:
    return [
        module_boundary(
            "core_lifecycle",
            "scripts/lifecycle_operation_store_runtime.py",
            "Validate operation preflight, idempotency, leases, immutable writes, and read-model effects.",
            ["storage_adapter", "read_model_projection"],
            ["transport_listener", "source_fetch", "credential_value_storage"],
        ),
        module_boundary(
            "storage_adapter",
            "scripts/lifecycle_operation_store_runtime.py",
            "Provide local SQLite-compatible storage semantics without exposing raw SQL to agent callers.",
            ["sqlite_connection", "schema_migration", "projection_upsert"],
            ["network_database_endpoint", "raw_sql_agent_surface", "physical_delete"],
        ),
        module_boundary(
            "source_adapter",
            "scripts/generate_source_adapter_intake.py",
            "Accept sanitized adapter output and source-policy bindings without executing private source reads.",
            ["source_policy_reference", "sanitized_adapter_output"],
            ["credential_value_storage", "unbounded_source_scan", "implicit_live_fetch"],
        ),
        module_boundary(
            "method_adapter",
            "scripts/select_setup_method.py",
            "Select allowed forecasting methods only after setup benchmark and method-gate checks.",
            ["method_registry", "benchmark_gate", "claim_boundary"],
            ["automatic_method_upgrade", "training_data_leakage", "quality_overclaim"],
        ),
        module_boundary(
            "transport_adapter",
            "scripts/agent_adapter_dispatcher.py",
            "Wrap internal operations for CLI, agent-call, and local MCP surfaces without changing semantics.",
            ["internal_api_operation", "compact_envelope"],
            ["raw_file_layout", "raw_sql_agent_surface", "hidden_network_listener"],
        ),
        module_boundary(
            "worker_runtime",
            "scripts/background_worker_runtime.py",
            "Run bounded foreground-equivalent worker ticks with explicit control state and no hidden daemon.",
            ["internal_api_run_tick", "worker_control_state", "bounded_loop"],
            ["unbounded_background_loop", "implicit_live_fetch", "host_event_loop_ownership"],
        ),
        module_boundary(
            "domain_source_setup",
            "scripts/generate_source_bindings.py",
            "Bind approved domain/source setup records with mapping confidence, source quality, and leakage checks.",
            ["domain_config", "source_binding", "credential_reference"],
            ["credential_value_storage", "raw_private_rows", "unchecked_database_query"],
        ),
    ]


def runtime_surface_control(
    name: str,
    owner_module: str,
    input_bytes: int,
    response_bytes: int,
    notes: str,
) -> dict[str, Any]:
    return {
        "surfaceName": name,
        "ownerModule": owner_module,
        "pathAllowlistRequired": True,
        "symlinkEscapeCheckRequired": True,
        "databasePathCheckRequired": True,
        "inputSizeLimitBytes": input_bytes,
        "responseSizeLimitBytes": response_bytes,
        "sanitizedDiagnosticsRequired": True,
        "credentialReferenceOnly": True,
        "credentialValuesStored": False,
        "networkAccessDefault": "disabled",
        "rawSqlExposed": False,
        "rawFileLayoutExposed": False,
        "notes": notes,
    }


def runtime_surface_controls() -> list[dict[str, Any]]:
    return [
        runtime_surface_control(
            "embedded_internal_api",
            "core_lifecycle",
            65536,
            65536,
            "Internal API calls are bounded, receipt-backed, and return sanitized read models.",
        ),
        runtime_surface_control(
            "local_sqlite_storage_adapter",
            "storage_adapter",
            262144,
            65536,
            "SQLite checks run in memory or approved local state paths and never expose raw SQL to agents.",
        ),
        runtime_surface_control(
            "background_worker_runtime",
            "worker_runtime",
            65536,
            65536,
            "Worker checks run one bounded tick, honor control state, and avoid live source execution by default.",
        ),
        runtime_surface_control(
            "local_source_runtime",
            "source_adapter",
            262144,
            65536,
            "Local source intake accepts only caller-approved files under an allow-listed folder.",
        ),
        runtime_surface_control(
            "domain_source_setup",
            "domain_source_setup",
            131072,
            65536,
            "Domain and source setup records expose references, confidence, and blockers without private payloads.",
        ),
    ]


def path_and_database_guards() -> dict[str, Any]:
    return {
        "allowedLocalStateRoots": [".ope/state"],
        "allowedFixtureRoots": ["spec/fixtures", "spec/fixtures/generated"],
        "pathTraversalBlocked": True,
        "symlinkEscapeBlocked": True,
        "absolutePathRequiresApproval": True,
        "localSourcePathAllowlistRequired": True,
        "databasePathAllowlistRequired": True,
        "persistentDatabaseDefaultAllowed": False,
        "normalChecksUseEphemeralSqlite": True,
        "sanitizedDiagnostics": [
            "path_traversal_blocked",
            "symlink_escape_blocked",
            "database_path_not_allowlisted",
            "response_too_large",
        ],
    }


def credential_handling() -> dict[str, Any]:
    return {
        "credentialValuesStoredInRecords": False,
        "credentialReferencesAllowed": True,
        "allowedCredentialFields": ["credentialRef", "sourcePolicyId", "sanitizedProvenance"],
        "redactionReceiptRequiredForUnsafeFields": True,
        "sourcePolicyIdRequired": True,
        "sanitizedProvenanceRequired": True,
        "environmentSecretEchoAllowed": False,
        "notes": "Records may point at caller-managed credential references but must not contain secret values.",
    }


def threat_model_note(
    name: str,
    risk: str,
    mitigation: str,
    checks: list[str],
) -> dict[str, Any]:
    return {
        "threatName": name,
        "risk": risk,
        "mitigation": mitigation,
        "mitigationStatus": "checked_or_bounded",
        "checkedBy": checks,
        "rawSensitiveDataExposed": False,
    }


def threat_model_notes() -> list[dict[str, Any]]:
    return [
        threat_model_note(
            "malicious_source_data",
            "Caller-provided source rows may contain malformed, adversarial, or misleading data.",
            "Source intake and local runtime checks bind source policy, mapping confidence, size limits, and sanitized diagnostics before forecast use.",
            ["scripts/check_source_intake.py", "scripts/check_local_source_runtime.py"],
        ),
        threat_model_note(
            "prompt_source_injection",
            "Source text could try to override agent instructions or forecast method boundaries.",
            "OPE treats source payloads as evidence records, never instructions, and keeps method selection behind checked gates.",
            ["scripts/check_setup_method_decision.py", "scripts/check_source_handoff_method_gate.py"],
        ),
        threat_model_note(
            "path_traversal",
            "A caller could try to bind files outside the approved local source or state roots.",
            "Path traversal, symlink escape, and database path checks are explicit runtime surface controls.",
            ["scripts/check_local_source_runtime.py", "scripts/check_runtime_security.py"],
        ),
        threat_model_note(
            "idempotency_replay",
            "Repeated agent calls could duplicate lifecycle writes or replay stale operations.",
            "Effectful operations require idempotency keys and receipt-backed lifecycle preflight before mutation.",
            ["scripts/check_lifecycle_operation_store.py", "scripts/check_internal_api.py"],
        ),
        threat_model_note(
            "lease_abuse",
            "A caller could monopolize a prediction lease or race another mutation.",
            "Per-prediction leases block concurrent mutation, expose stale recovery, and keep worker ticks bounded.",
            ["scripts/check_prediction_workspace_registry.py", "scripts/check_background_worker_runtime.py"],
        ),
        threat_model_note(
            "oversized_responses",
            "Large readbacks could overwhelm agent callers or hide oversized matrices in compact surfaces.",
            "Read responses, adapter summaries, and runtime surfaces declare byte budgets and response_too_large blockers.",
            ["scripts/check_hardening.py", "scripts/check_private_setup_adapter_conformance_summary.py"],
        ),
        threat_model_note(
            "accidental_private_data_exposure",
            "Private rows, raw transcripts, credentials, or participant identity could leak into checked records.",
            "Pilot, source, adapter, and credential records use sanitized summaries, redaction receipts, and credential references only.",
            ["scripts/check_pilot_summary_intake.py", "scripts/check_private_source_adapter_capabilities.py"],
        ),
    ]


def agent_readable_checks() -> list[dict[str, Any]]:
    return [
        {
            "command": "python3 scripts/check_runtime_security.py",
            "purpose": "Validate the runtime security readback contract and Milestone 117 invariants.",
            "hiddenServiceRequired": False,
        },
        {
            "command": "python3 scripts/check_hardening.py",
            "purpose": "Run repo-wide secret, size, binding, duplicate, and adapter payload guards.",
            "hiddenServiceRequired": False,
        },
        {
            "command": "python3 scripts/ope.py runtime-security --check",
            "purpose": "Check the generated runtime-security fixture through the CLI.",
            "hiddenServiceRequired": False,
        },
        {
            "command": "python3 scripts/ope.py check",
            "purpose": "Run all local canonical checks without live source fetches or hidden services.",
            "hiddenServiceRequired": False,
        },
    ]


def blocked_example(case_name: str, diagnostic: str, safe_next_action: str) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "blocked": True,
        "sanitizedDiagnosticCode": diagnostic,
        "rawValueEchoed": False,
        "safeNextAction": safe_next_action,
    }


def blocked_examples() -> list[dict[str, Any]]:
    return [
        blocked_example(
            "path_traversal",
            "path_traversal_blocked",
            "Choose a caller-approved file under the configured source allow-list.",
        ),
        blocked_example(
            "symlink_escape",
            "symlink_escape_blocked",
            "Resolve the path and bind only files that remain under the approved root.",
        ),
        blocked_example(
            "database_outside_allowlist",
            "database_path_not_allowlisted",
            "Use ephemeral SQLite for checks or an approved local state database path.",
        ),
        blocked_example(
            "oversized_response",
            "response_too_large",
            "Use a compact readback view or explicitly request the larger matrix surface.",
        ),
        blocked_example(
            "credential_value_in_record",
            "credential_value_redacted",
            "Replace the value with a caller-managed credential reference and source policy id.",
        ),
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "hostedRuntimeRequired": False,
        "networkListenerStarted": False,
        "liveSourceFetchDefault": False,
        "credentialValuesStored": False,
        "rawSqlExposed": False,
        "rawFileLayoutExposed": False,
        "unboundedBackgroundLoopAllowed": False,
        "physicalDeleteAllowed": False,
    }


def build_runtime_security() -> dict[str, Any]:
    modules = module_boundaries()
    surfaces = runtime_surface_controls()
    threats = threat_model_notes()
    blocked = blocked_examples()
    return {
        "runtimeSecurityId": "runtime-security-001",
        "generatedAt": GENERATED_AT,
        "securityStatus": "lightweight_runtime_hardening_checked",
        "runtimeScope": "embedded_local_runtime",
        "dependencyBudget": dependency_budget(),
        "moduleBoundaries": modules,
        "runtimeSurfaceControls": surfaces,
        "pathAndDatabaseGuards": path_and_database_guards(),
        "credentialHandling": credential_handling(),
        "threatModelNotes": threats,
        "agentReadableChecks": agent_readable_checks(),
        "blockedExamples": blocked,
        "executionBoundary": execution_boundary(),
        "summary": {
            "runtimeDependencyCount": 0,
            "moduleBoundaryCount": len(modules),
            "surfaceControlCount": len(surfaces),
            "threatModelNoteCount": len(threats),
            "blockedExampleCount": len(blocked),
            "normalChecksStartHiddenService": False,
        },
        "warnings": [
            "This readback is a lightweight hardening contract, not an independent security audit.",
            "Credential references remain caller-managed and must not be expanded into OPE records.",
            "Future hosted or database-backed runtimes must pass equivalent controls before promotion.",
        ],
    }


def validate_runtime_security(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise RuntimeSecurityError("runtime security record failed schema validation")

    if record["summary"]["runtimeDependencyCount"] != len(record["dependencyBudget"]["runtimeDependencies"]):
        raise RuntimeSecurityError("runtime dependency count drifted")
    if record["summary"]["moduleBoundaryCount"] != len(record["moduleBoundaries"]):
        raise RuntimeSecurityError("module boundary count drifted")
    if record["summary"]["surfaceControlCount"] != len(record["runtimeSurfaceControls"]):
        raise RuntimeSecurityError("surface control count drifted")
    if record["summary"]["threatModelNoteCount"] != len(record["threatModelNotes"]):
        raise RuntimeSecurityError("threat model count drifted")
    if record["summary"]["blockedExampleCount"] != len(record["blockedExamples"]):
        raise RuntimeSecurityError("blocked example count drifted")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "budget":
        return record["dependencyBudget"]
    if view == "modules":
        return record["moduleBoundaries"]
    if view == "surfaces":
        return record["runtimeSurfaceControls"]
    if view == "threats":
        return record["threatModelNotes"]
    if view == "blocked":
        return record["blockedExamples"]
    if view == "boundary":
        return record["executionBoundary"]
    raise RuntimeSecurityError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated runtime security fixture")
    parser.add_argument("--check", action="store_true", help="check generated runtime security fixture for drift")
    parser.add_argument(
        "--view",
        choices=["full", "budget", "modules", "surfaces", "threats", "blocked", "boundary"],
        default="full",
        help="emit a focused runtime security readback view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_runtime_security()
    validate_runtime_security(record)

    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="runtime security hardening",
            regen="python3 scripts/generate_runtime_security.py --write",
        )
        return

    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="runtime security hardening",
            regen="python3 scripts/generate_runtime_security.py --write",
        )
        return

    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
