#!/usr/bin/env python3
"""Generate a checked runtime transport readiness readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "runtime-transport-readiness"
OUTPUT_PATH = GENERATED / "ope-runtime-transport-readiness.generated.json"
SCHEMA = SPEC / "runtime-transport-readiness.schema.json"
GENERATED_AT = "2026-06-04T23:59:00Z"

CURRENT_SURFACES = [
    "embedded_internal_api",
    "cli",
    "agent_call",
    "local_mcp_stdio",
]

FUTURE_SURFACES = [
    "local_http_adapter",
    "queue_adapter",
    "hosted_service_runtime",
    "opp_http_provider",
]

CRITERIA = [
    "internal_api_stable",
    "lifecycle_operation_store_checked",
    "runtime_security_checked",
    "persistent_sqlite_policy_checked",
    "lifecycle_lease_policy_checked",
    "agent_adapter_protocol_map_checked",
    "pilot_evidence_threshold_met",
    "hosted_observability_plan_checked",
    "production_secret_reference_policy_checked",
    "hosted_storage_migration_checked",
]

BLOCKED_CASES = [
    "normal_check_http_server",
    "implicit_hosted_service",
    "opp_http_endpoint_request",
    "queue_worker_without_readiness",
    "production_secret_value_in_record",
    "default_live_fetch",
    "unbounded_background_daemon",
]


class RuntimeTransportReadinessError(Exception):
    pass


def current_surface(
    name: str,
    command: str,
    adapter_role: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "surfaceName": name,
        "surfaceStatus": "implemented_local",
        "command": command,
        "adapterRole": adapter_role,
        "testedInNormalChecks": True,
        "startsNetworkListener": False,
        "hostedRuntimeRequired": False,
        "mutatesStateByDefault": False,
        "credentialValuesAccepted": False,
        "notes": notes,
    }


def current_surfaces() -> list[dict[str, Any]]:
    return [
        current_surface(
            "embedded_internal_api",
            "python3 scripts/ope.py internal-api",
            "in_process_operation_surface",
            "Stable internal API operation surface for host software and adapters.",
        ),
        current_surface(
            "cli",
            "python3 scripts/ope.py",
            "local_terminal_surface",
            "Local command surface for checks, readbacks, and explicit opt-in operations.",
        ),
        current_surface(
            "agent_call",
            "python3 scripts/ope.py agent-call",
            "transport_neutral_envelope_surface",
            "Compact agent envelopes over checked internal operations.",
        ),
        current_surface(
            "local_mcp_stdio",
            "python3 scripts/ope.py mcp-stdio",
            "local_stdio_tool_surface",
            "Local MCP stdio scaffold over the dispatcher without network listeners.",
        ),
    ]


def future_surface(
    name: str,
    status: str,
    proposed_command: str,
    readiness_gate: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "surfaceName": name,
        "surfaceStatus": status,
        "proposedCommand": proposed_command,
        "readinessGate": readiness_gate,
        "implementedNow": False,
        "advertisedNow": False,
        "normalChecksStartSurface": False,
        "requiresReadinessGate": True,
        "reason": reason,
    }


def future_surfaces() -> list[dict[str, Any]]:
    return [
        future_surface(
            "local_http_adapter",
            "deferred_pending_adoption_evidence",
            "python3 scripts/ope.py http-serve",
            "adoption_need_and_security_gate",
            "Local HTTP should wait until CLI, agent-call, and MCP usage show a concrete need and security controls are checked.",
        ),
        future_surface(
            "queue_adapter",
            "deferred_pending_hosted_runtime_gate",
            "python3 scripts/ope.py queue-worker",
            "hosted_runtime_readiness_gate",
            "Queue workers require hosted/runtime readiness, durable operation leases, and observability before implementation.",
        ),
        future_surface(
            "hosted_service_runtime",
            "blocked_pending_readiness_gate",
            "not_implemented",
            "pilot_security_storage_and_ops_readiness",
            "Hosted service runtime waits for pilot evidence, storage migration, secret handling, and operational readiness.",
        ),
        future_surface(
            "opp_http_provider",
            "future_adapter_only",
            "python3 scripts/ope.py opp-http-provider",
            "provider_runtime_readiness_gate",
            "OPP remains a checked fixture adapter over OPE records until an explicit HTTP provider gate is met.",
        ),
    ]


def runtime_decisions() -> dict[str, str]:
    return {
        "firstEmbeddedRuntime": "in_process_cli_agent_call_and_local_mcp",
        "localHttpDecision": "deferred_until_adoption_need_and_security_gate",
        "hostedRuntimeDecision": "deferred_until_pilot_security_storage_and_ops_readiness",
        "queueDecision": "deferred_until_hosted_runtime_gate",
        "oppProviderDecision": "fixture_adapter_now_http_provider_future",
    }


def criterion(
    name: str,
    status: str,
    evidence_command: str,
    evidence_status: str,
    notes: str,
    *,
    blocks_hosted: bool,
    blocks_http: bool,
) -> dict[str, Any]:
    return {
        "criterionName": name,
        "criterionStatus": status,
        "evidenceCommand": evidence_command,
        "evidenceStatus": evidence_status,
        "blocksHostedRuntime": blocks_hosted,
        "blocksLocalHttp": blocks_http,
        "normalChecksMutateState": False,
        "notes": notes,
    }


def readiness_criteria() -> list[dict[str, Any]]:
    met = "met_for_local_readbacks"
    unmet = "not_met_for_hosted_or_http_runtime"
    return [
        criterion(
            "internal_api_stable",
            met,
            "python3 scripts/ope.py internal-api",
            "checked",
            "The internal API surface is checked for local readbacks and adapter wrapping.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "lifecycle_operation_store_checked",
            met,
            "python3 scripts/ope.py lifecycle-operation-store",
            "checked",
            "Lifecycle operation receipts, leases, idempotency, and read models are checked locally.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "runtime_security_checked",
            met,
            "python3 scripts/ope.py runtime-security",
            "checked",
            "Runtime hardening covers dependency, module, path, size, credential, and boundary controls.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "persistent_sqlite_policy_checked",
            met,
            "python3 scripts/ope.py persistent-sqlite-policy",
            "checked",
            "Persistent local SQLite paths are explicit opt-in and normal checks remain ephemeral.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "lifecycle_lease_policy_checked",
            met,
            "python3 scripts/ope.py lifecycle-lease-policy",
            "checked",
            "Strict leases and idempotency-only guards are classified before effectful runtime expansion.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "agent_adapter_protocol_map_checked",
            met,
            "python3 scripts/ope.py agent-protocol-map",
            "checked",
            "MCP stdio is tested locally while HTTP and queue adapters stay future transports.",
            blocks_hosted=False,
            blocks_http=False,
        ),
        criterion(
            "pilot_evidence_threshold_met",
            unmet,
            "python3 scripts/ope.py pilot-evidence",
            "not_met",
            "Real pilot sessions and enough comparable outcomes are still needed before runtime promotion.",
            blocks_hosted=True,
            blocks_http=True,
        ),
        criterion(
            "hosted_observability_plan_checked",
            unmet,
            "python3 scripts/ope.py expansion-readiness",
            "not_met",
            "Hosted runtime needs checked logs, metrics, traces, incident handling, and operator readbacks.",
            blocks_hosted=True,
            blocks_http=False,
        ),
        criterion(
            "production_secret_reference_policy_checked",
            unmet,
            "python3 scripts/ope.py expansion-readiness",
            "not_met",
            "Private API and hosted database credentials still need a checked reference-only mechanism.",
            blocks_hosted=True,
            blocks_http=True,
        ),
        criterion(
            "hosted_storage_migration_checked",
            unmet,
            "python3 scripts/ope.py postgres-compatibility",
            "not_met",
            "Postgres compatibility is checked, but hosted storage migration and execution are not implemented.",
            blocks_hosted=True,
            blocks_http=False,
        ),
    ]


def blocked_case(
    name: str,
    status: str,
    requested_surface: str,
    safe_next_action: str,
) -> dict[str, Any]:
    return {
        "caseName": name,
        "caseStatus": status,
        "requestedSurface": requested_surface,
        "safeNextAction": safe_next_action,
        "networkListenerStarted": False,
        "hostedRuntimeStarted": False,
        "stateWritten": False,
        "credentialValuesStored": False,
        "sanitizedDiagnosticsOnly": True,
    }


def blocked_cases() -> list[dict[str, Any]]:
    return [
        blocked_case("normal_check_http_server", "blocked_normal_check_network_listener", "local_http_adapter", "use_cli_or_agent_call_readback"),
        blocked_case("implicit_hosted_service", "blocked_hosted_runtime_not_ready", "hosted_service_runtime", "read_expansion_readiness_gate"),
        blocked_case("opp_http_endpoint_request", "blocked_opp_http_provider_future", "opp_http_provider", "use_opp_provider_adapter_fixture"),
        blocked_case("queue_worker_without_readiness", "blocked_queue_runtime_not_ready", "queue_adapter", "use_background_worker_readback"),
        blocked_case("production_secret_value_in_record", "blocked_credential_value_storage", "hosted_service_runtime", "replace_with_credential_reference"),
        blocked_case("default_live_fetch", "blocked_default_live_network", "hosted_service_runtime", "use_fixture_or_explicit_live_gate"),
        blocked_case("unbounded_background_daemon", "blocked_unbounded_daemon", "queue_adapter", "use_bounded_foreground_scheduler"),
    ]


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py runtime-transport-readiness",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Prints the checked runtime transport readiness gate.",
        },
        {
            "readbackSurface": "internal_api",
            "command": "python3 scripts/ope.py internal-api",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Current in-process operation surface remains the tested runtime core.",
        },
        {
            "readbackSurface": "agent_protocol_map",
            "command": "python3 scripts/ope.py agent-protocol-map",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Protocol map keeps MCP stdio tested and HTTP/queue future.",
        },
        {
            "readbackSurface": "runtime_security",
            "command": "python3 scripts/ope.py runtime-security",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Runtime hardening blocks hidden services, raw SQL, and credential leakage.",
        },
        {
            "readbackSurface": "opp_provider_adapter",
            "command": "python3 scripts/ope.py opp-provider-adapter",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "OPP provider mapping stays a fixture adapter, not an HTTP runtime.",
        },
        {
            "readbackSurface": "lifecycle_lease_policy",
            "command": "python3 scripts/ope.py lifecycle-lease-policy",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Lease policy must be stable before worker or hosted queue promotion.",
        },
        {
            "readbackSurface": "expansion_readiness",
            "command": "python3 scripts/ope.py expansion-readiness",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "Expansion readiness keeps hosted runtime, broader sources, and stronger methods blocked.",
        },
        {
            "readbackSurface": "mvp_release_surface",
            "command": "python3 scripts/check_mvp_release_surface.py",
            "mutatesState": False,
            "startsNetworkListener": False,
            "notes": "MVP smoke checks cover local runtime readbacks and blocked paths.",
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "networkListenerStarted": False,
        "localHttpServerImplemented": False,
        "hostedServiceImplemented": False,
        "queueRuntimeImplemented": False,
        "oppHttpProviderImplemented": False,
        "normalChecksUseNetwork": False,
        "normalChecksWriteState": False,
        "credentialValuesStored": False,
        "paymentSettlementImplemented": False,
        "productionLiveFetchEnabled": False,
        "qualityClaimsUpgraded": False,
    }


def build_runtime_transport_readiness() -> dict[str, Any]:
    current = current_surfaces()
    future = future_surfaces()
    criteria = readiness_criteria()
    blocked = blocked_cases()
    record = {
        "runtimeTransportReadinessId": "runtimetransportreadiness-001",
        "generatedAt": GENERATED_AT,
        "readinessStatus": "runtime_transport_readiness_checked",
        "decisionStatus": "local_surfaces_ready_http_queue_and_hosted_deferred",
        "normalChecksOffline": True,
        "hostedRuntimeAllowedNow": False,
        "localHttpAllowedNow": False,
        "currentSurfaces": current,
        "futureSurfaces": future,
        "runtimeDecisions": runtime_decisions(),
        "readinessCriteria": criteria,
        "blockedCases": blocked,
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "currentSurfaceCount": len(current),
            "futureSurfaceCount": len(future),
            "readinessCriteriaCount": len(criteria),
            "metLocalCriteriaCount": len([item for item in criteria if item["criterionStatus"] == "met_for_local_readbacks"]),
            "blockedCaseCount": len(blocked),
            "hostedRuntimeAllowedNow": False,
            "localHttpAllowedNow": False,
            "normalChecksOffline": True,
        },
        "warnings": [
            "Current tested transport surfaces are local, compact, and non-networked.",
            "Local HTTP is deferred until adoption evidence and security controls justify a listener.",
            "Hosted runtime, queue workers, and OPP HTTP provider behavior require explicit readiness gates before implementation.",
        ],
    }
    validate_runtime_transport_readiness(record)
    return record


def validate_runtime_transport_readiness(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise RuntimeTransportReadinessError(f"runtime transport readiness schema validation failed: {errors[0]}")
    if [item["surfaceName"] for item in record["currentSurfaces"]] != CURRENT_SURFACES:
        raise RuntimeTransportReadinessError("current surface order drifted")
    if [item["surfaceName"] for item in record["futureSurfaces"]] != FUTURE_SURFACES:
        raise RuntimeTransportReadinessError("future surface order drifted")
    if [item["criterionName"] for item in record["readinessCriteria"]] != CRITERIA:
        raise RuntimeTransportReadinessError("readiness criteria order drifted")
    if [item["caseName"] for item in record["blockedCases"]] != BLOCKED_CASES:
        raise RuntimeTransportReadinessError("blocked case order drifted")
    for item in record["currentSurfaces"]:
        if item["startsNetworkListener"] or item["hostedRuntimeRequired"] or item["credentialValuesAccepted"]:
            raise RuntimeTransportReadinessError("current surfaces must stay local and non-networked")
    for item in record["futureSurfaces"]:
        if item["implementedNow"] or item["advertisedNow"] or item["normalChecksStartSurface"]:
            raise RuntimeTransportReadinessError("future surfaces must not be implemented or started in normal checks")
    if any(record["executionBoundary"].values()):
        raise RuntimeTransportReadinessError("execution boundary flags should stay false")


def surface_payload(record: dict[str, Any], surface_name: str) -> dict[str, Any]:
    for item in [*record["currentSurfaces"], *record["futureSurfaces"]]:
        if item["surfaceName"] == surface_name:
            return item
    raise RuntimeTransportReadinessError(f"unknown surface {surface_name}")


def case_payload(record: dict[str, Any], case_name: str) -> dict[str, Any]:
    for item in record["blockedCases"]:
        if item["caseName"] == case_name:
            return item
    raise RuntimeTransportReadinessError(f"unknown case {case_name}")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "current":
        return record["currentSurfaces"]
    if view == "future":
        return record["futureSurfaces"]
    if view == "decisions":
        return record["runtimeDecisions"]
    if view == "criteria":
        return record["readinessCriteria"]
    if view == "blocked":
        return record["blockedCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise RuntimeTransportReadinessError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated runtime transport readiness fixture")
    parser.add_argument("--check", action="store_true", help="check generated runtime transport readiness fixture")
    parser.add_argument("--surface", choices=[*CURRENT_SURFACES, *FUTURE_SURFACES], help="print one transport surface")
    parser.add_argument("--case", choices=BLOCKED_CASES, help="print one blocked transport case")
    parser.add_argument(
        "--view",
        choices=["full", "current", "future", "decisions", "criteria", "blocked", "readbacks", "boundary", "summary"],
        default="full",
        help="emit a focused runtime transport readiness view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_runtime_transport_readiness()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="runtime transport readiness",
            regen="python3 scripts/generate_runtime_transport_readiness.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="runtime transport readiness",
            regen="python3 scripts/generate_runtime_transport_readiness.py --write",
        )
        return
    if args.surface:
        print(render_json(surface_payload(record, args.surface)), end="")
        return
    if args.case:
        print(render_json(case_payload(record, args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
