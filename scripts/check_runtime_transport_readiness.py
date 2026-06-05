#!/usr/bin/env python3
"""Check runtime transport readiness and hosted/runtime boundaries."""

from __future__ import annotations

try:
    from generate_runtime_transport_readiness import build_runtime_transport_readiness
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("runtime transport readiness generator is missing") from exc


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

REQUIRED_BOUNDARY_FALSE = [
    "networkListenerStarted",
    "localHttpServerImplemented",
    "hostedServiceImplemented",
    "queueRuntimeImplemented",
    "oppHttpProviderImplemented",
    "normalChecksUseNetwork",
    "normalChecksWriteState",
    "credentialValuesStored",
    "paymentSettlementImplemented",
    "productionLiveFetchEnabled",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    readiness = build_runtime_transport_readiness()

    require(readiness["readinessStatus"] == "runtime_transport_readiness_checked", "readiness status drifted")
    require(
        readiness["decisionStatus"] == "local_surfaces_ready_http_queue_and_hosted_deferred",
        "decision status drifted",
    )
    require(readiness["normalChecksOffline"] is True, "normal checks should remain offline")
    require(readiness["hostedRuntimeAllowedNow"] is False, "hosted runtime must remain blocked")
    require(readiness["localHttpAllowedNow"] is False, "local HTTP must remain deferred")

    current = {item["surfaceName"]: item for item in readiness["currentSurfaces"]}
    require(list(current) == CURRENT_SURFACES, "current transport surface order drifted")
    for name, item in current.items():
        require(item["surfaceStatus"] == "implemented_local", f"{name} should be locally implemented")
        require(item["testedInNormalChecks"] is True, f"{name} should be covered by normal checks")
        require(item["startsNetworkListener"] is False, f"{name} must not start network listeners")
        require(item["hostedRuntimeRequired"] is False, f"{name} must not require hosted runtime")
        require(item["mutatesStateByDefault"] is False, f"{name} must not mutate state by default")
        require(item["credentialValuesAccepted"] is False, f"{name} must not accept credential values")

    future = {item["surfaceName"]: item for item in readiness["futureSurfaces"]}
    require(list(future) == FUTURE_SURFACES, "future transport surface order drifted")
    require(future["local_http_adapter"]["surfaceStatus"] == "deferred_pending_adoption_evidence", "local HTTP status drifted")
    require(future["queue_adapter"]["surfaceStatus"] == "deferred_pending_hosted_runtime_gate", "queue adapter status drifted")
    require(future["hosted_service_runtime"]["surfaceStatus"] == "blocked_pending_readiness_gate", "hosted runtime status drifted")
    require(future["opp_http_provider"]["surfaceStatus"] == "future_adapter_only", "OPP HTTP status drifted")
    for name, item in future.items():
        require(item["implementedNow"] is False, f"{name} must not be implemented now")
        require(item["advertisedNow"] is False, f"{name} must not be advertised now")
        require(item["normalChecksStartSurface"] is False, f"{name} must not start during normal checks")
        require(item["requiresReadinessGate"] is True, f"{name} should require a readiness gate")

    decisions = readiness["runtimeDecisions"]
    require(decisions["firstEmbeddedRuntime"] == "in_process_cli_agent_call_and_local_mcp", "embedded runtime decision drifted")
    require(decisions["localHttpDecision"] == "deferred_until_adoption_need_and_security_gate", "local HTTP decision drifted")
    require(decisions["hostedRuntimeDecision"] == "deferred_until_pilot_security_storage_and_ops_readiness", "hosted runtime decision drifted")

    criteria = {item["criterionName"]: item for item in readiness["readinessCriteria"]}
    require(list(criteria) == CRITERIA, "readiness criteria order drifted")
    for name in CRITERIA[:6]:
        require(criteria[name]["criterionStatus"] == "met_for_local_readbacks", f"{name} should be met for local readbacks")
    for name in CRITERIA[6:]:
        require(criteria[name]["criterionStatus"] == "not_met_for_hosted_or_http_runtime", f"{name} should block hosted/http runtime")
    for item in criteria.values():
        require(item["evidenceCommand"].startswith("python3 scripts/ope.py "), f"{item['criterionName']} evidence command drifted")
        require(item["normalChecksMutateState"] is False, f"{item['criterionName']} should not mutate state in normal checks")

    cases = {item["caseName"]: item for item in readiness["blockedCases"]}
    require(list(cases) == BLOCKED_CASES, "blocked case order drifted")
    for case in cases.values():
        require(case["caseStatus"].startswith("blocked_"), f"{case['caseName']} should be blocked")
        require(case["networkListenerStarted"] is False, f"{case['caseName']} must not start a listener")
        require(case["hostedRuntimeStarted"] is False, f"{case['caseName']} must not start hosted runtime")
        require(case["stateWritten"] is False, f"{case['caseName']} must not write state")
        require(case["credentialValuesStored"] is False, f"{case['caseName']} must not store credentials")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case['caseName']} should keep diagnostics sanitized")

    readbacks = {item["readbackSurface"]: item for item in readiness["readbacks"]}
    require(
        set(readbacks)
        == {
            "cli",
            "internal_api",
            "agent_protocol_map",
            "runtime_security",
            "opp_provider_adapter",
            "lifecycle_lease_policy",
            "expansion_readiness",
            "mvp_release_surface",
        },
        "readback surface coverage drifted",
    )
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py runtime-transport-readiness", "CLI command drifted")
    for readback in readbacks.values():
        require(readback["mutatesState"] is False, "readbacks must not mutate state")
        require(readback["startsNetworkListener"] is False, "readbacks must not start listeners")

    boundary = readiness["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = readiness["summary"]
    require(summary["currentSurfaceCount"] == len(CURRENT_SURFACES), "current surface count drifted")
    require(summary["futureSurfaceCount"] == len(FUTURE_SURFACES), "future surface count drifted")
    require(summary["readinessCriteriaCount"] == len(CRITERIA), "criteria count drifted")
    require(summary["metLocalCriteriaCount"] == 6, "met local criteria count drifted")
    require(summary["blockedCaseCount"] == len(BLOCKED_CASES), "blocked case count drifted")
    require(summary["hostedRuntimeAllowedNow"] is False, "summary hosted flag drifted")
    require(summary["localHttpAllowedNow"] is False, "summary local HTTP flag drifted")
    require(summary["normalChecksOffline"] is True, "summary normal-check offline flag drifted")

    print("checked runtime transport readiness")


if __name__ == "__main__":
    main()
