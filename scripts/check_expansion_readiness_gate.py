#!/usr/bin/env python3
"""Check expansion readiness gate invariants."""

from __future__ import annotations

from generate_expansion_readiness_gate import OPTION_ORDER, build_expansion_readiness_gate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    gate = build_expansion_readiness_gate()
    bindings = gate["bindings"]
    evidence = {item["source"]: item for item in gate["evidenceInputs"]}
    options = {item["area"]: item for item in gate["expansionOptions"]}
    criteria = {item["area"]: item for item in gate["successCriteria"]}
    boundary = gate["executionBoundary"]
    summary = gate["summary"]

    require(gate["gateStatus"] == "blocked_pending_evidence", "gate status drifted")
    require(
        gate["decision"]["currentPosture"] == "hold_local_mvp_and_gather_evidence",
        "gate posture should hold local MVP and gather evidence",
    )
    require(bindings["developerAdoptionSurfaceId"] == "developeradoptionsurface-001", "adoption binding drifted")
    require(bindings["pilotEvidenceLedgerId"] == "pilotevidenceledger-001", "pilot evidence binding drifted")
    require(bindings["localUsageTraceId"] == "localusagetrace-001", "usage trace binding drifted")
    require(bindings["transitCorpusGrowthLoopId"] == "transitcorpusgrowthloop-001", "corpus growth binding drifted")
    require(bindings["localSourceRuntimeId"] == "localsourceruntime-001", "local source runtime binding drifted")

    require([item["area"] for item in gate["expansionOptions"]] == OPTION_ORDER, "option order drifted")
    require(options["hosted_runtime"]["status"] == "blocked_pending_evidence", "hosted runtime should be blocked")
    require(
        "hosted_service" in options["hosted_runtime"]["blockedBy"],
        "hosted runtime blocker should cite hosted service non-goal",
    )
    require(
        options["broader_private_sources"]["status"] == "blocked_pending_evidence",
        "broader private sources should be blocked",
    )
    require(
        options["generated_runtime_types"]["status"] == "deferred_pending_adoption_evidence",
        "generated runtime types should remain deferred",
    )
    require(
        "not_enough_resolved_comparable_outcomes" in options["stronger_methods"]["blockedBy"],
        "stronger methods should be blocked by comparable sample size",
    )

    require(evidence["agent pilot validation"]["status"] == "synthetic_only", "pilot evidence must be synthetic-only")
    require(evidence["pilot evidence ledger"]["status"] == "below_threshold", "pilot evidence ledger must be below threshold")
    require(
        "acceptedRealSessions=0" in evidence["pilot evidence ledger"]["observedValue"],
        "pilot evidence ledger should show zero real sessions",
    )
    require(
        evidence["transit baseline track-record gate"]["status"] == "below_threshold",
        "track-record evidence must be below threshold",
    )
    require(evidence["approved local-folder source runtime"]["status"] == "met", "local runtime evidence should be met")

    require(criteria["local MVP adoption"]["ready"] is True, "local MVP adoption criterion should be ready")
    require(criteria["real pilot evidence"]["ready"] is False, "real pilot evidence should not be ready")
    require(criteria["public transit track record"]["ready"] is False, "transit track record should not be ready")
    require(criteria["generated type evidence"]["ready"] is False, "generated type evidence should not be ready")

    require(summary["readyOptionCount"] == 0, "ready option count must remain zero")
    require(summary["blockedOptionCount"] == 5, "blocked option count drifted")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")
    require(summary["hostedRuntimeAllowed"] is False, "hosted runtime must remain blocked")
    require(summary["generatedTypesIncluded"] is False, "generated runtime types must not be included")

    require(boundary["readOnlyGate"] is True, "gate must be read-only")
    require(boundary["deterministicOffline"] is True, "gate must be deterministic offline")
    for key, value in boundary.items():
        if key in {"readOnlyGate", "deterministicOffline"}:
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked expansion readiness gate")


if __name__ == "__main__":
    main()
