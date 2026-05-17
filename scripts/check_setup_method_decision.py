#!/usr/bin/env python3
"""Check setup-aware method decision boundaries."""

from __future__ import annotations

from select_setup_method import build_decisions


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def candidates(decision: dict) -> dict[str, dict]:
    return {item["methodClass"]: item for item in decision["methodCandidates"]}


def main() -> None:
    decisions = build_decisions()
    require(
        set(decisions) == {"accepted", "accepted_partial", "needs_confirmation", "rejected"},
        "setup method decisions should cover source-intake outcomes",
    )

    accepted = decisions["accepted"]
    accepted_candidates = candidates(accepted)
    require(accepted["decisionStatus"] == "method_selected", "accepted case should select benchmark-approved method")
    require(
        accepted["selectedMethodClass"] == "deterministic_statistical",
        "accepted case should choose deterministic statistical method",
    )
    require(
        accepted["selectedSetupBenchmarkGateId"] == "setupbenchmarkgate-001",
        "accepted case should bind setup benchmark gate",
    )
    require(
        accepted_candidates["historical_baseline"]["finalEligibilityStatus"] == "eligible",
        "accepted baseline should be eligible",
    )
    require(
        accepted_candidates["deterministic_statistical"]["sourceEligibilityStatus"] == "eligible",
        "accepted deterministic method should pass source eligibility",
    )
    require(
        accepted_candidates["deterministic_statistical"]["benchmarkEligibilityStatus"] == "eligible",
        "accepted deterministic method should pass setup benchmark gate",
    )
    require(
        accepted_candidates["deterministic_statistical"]["finalEligibilityStatus"] == "eligible",
        "accepted deterministic method should be final-eligible with provisional benchmark gate",
    )
    require(
        "quality_sample_threshold_not_met" in accepted_candidates["deterministic_statistical"]["reasonCodes"],
        "accepted deterministic method should keep quality claim boundary",
    )

    partial = decisions["accepted_partial"]
    partial_candidates = candidates(partial)
    require(partial["decisionStatus"] == "baseline_selected", "partial case should select baseline")
    require(
        "missing_weather_forecast" in partial_candidates["deterministic_statistical"]["reasonCodes"],
        "partial deterministic method should explain missing forecast-time evidence",
    )
    require(
        partial_candidates["deterministic_statistical"]["setupBenchmarkGateId"] == "setupbenchmarkgate-002",
        "partial deterministic method should bind the blocked setup benchmark gate",
    )

    needs = decisions["needs_confirmation"]
    needs_candidates = candidates(needs)
    require(needs["decisionStatus"] == "needs_confirmation", "needs-confirmation case should block method selection")
    require(needs["selectedMethodClass"] == "none", "needs-confirmation case must not select a method")
    require(
        needs["sourceIntakeSummary"]["proposedMappingCount"] > 0,
        "needs-confirmation case should expose proposed mappings",
    )
    require(
        needs_candidates["historical_baseline"]["finalEligibilityStatus"] == "needs_confirmation",
        "baseline should wait for mapping confirmation",
    )

    rejected = decisions["rejected"]
    rejected_candidates = candidates(rejected)
    require(rejected["decisionStatus"] == "rejected", "rejected case should reject method selection")
    require(rejected["selectedMethodClass"] == "none", "rejected case must not select a method")
    require(
        "post_close_or_unavailable_forecast_source" in rejected_candidates["deterministic_statistical"]["reasonCodes"],
        "rejected deterministic method should explain leakage risk",
    )
    require(
        "insufficient_comparable_rows" in rejected_candidates["historical_baseline"]["reasonCodes"],
        "rejected baseline should explain insufficient historical data",
    )

    for decision in decisions.values():
        boundary = decision["qualityClaimBoundary"]
        require(boundary["stateOfTheArtClaimAllowed"] is False, "state-of-the-art claims should stay blocked")
        require(boundary["productionReadinessClaimAllowed"] is False, "production readiness should stay blocked")

    print("checked setup method decisions")


if __name__ == "__main__":
    main()
