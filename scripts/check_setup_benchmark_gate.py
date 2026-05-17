#!/usr/bin/env python3
"""Check setup-specific benchmark gate boundaries."""

from __future__ import annotations

from generate_setup_benchmark_gate import build_gates


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    gates = build_gates()
    require(
        set(gates) == {"accepted", "accepted_partial", "needs_confirmation", "rejected"},
        "setup benchmark gates should cover every source-intake outcome",
    )

    accepted = gates["accepted"]
    require(accepted["gateStatus"] == "approved_provisional", "accepted gate should allow deterministic execution")
    require(accepted["decision"]["executionAllowed"] is True, "accepted gate should allow execution")
    require(accepted["decision"]["qualityClaimAllowed"] is False, "accepted gate must not allow quality claims")
    require(accepted["antiLeakageControls"]["sameQuestionSet"] is True, "accepted gate should share question set")
    require(accepted["antiLeakageControls"]["sameSourcePolicy"] is True, "accepted gate should share source policy")
    require(accepted["antiLeakageControls"]["sameRetrievalWindow"] is True, "accepted gate should share retrieval window")
    require(accepted["antiLeakageControls"]["leakageValidated"] is True, "accepted gate should pass leakage validation")
    require(accepted["metricThresholds"]["baselineLiftPositive"] is True, "accepted gate should have positive lift")
    require(
        accepted["metricThresholds"]["qualitySampleThresholdMet"] is False,
        "accepted gate should remain below quality-claim sample threshold",
    )
    require(
        "quality_sample_threshold_not_met" in accepted["reasonCodes"],
        "accepted gate should explain quality sample boundary",
    )

    partial = gates["accepted_partial"]
    require(partial["gateStatus"] == "blocked", "partial gate should block deterministic execution")
    require("missing_weather_forecast" in partial["reasonCodes"], "partial gate should explain missing weather source")

    needs = gates["needs_confirmation"]
    require(needs["gateStatus"] == "blocked", "needs-confirmation gate should block")
    require("mapping_confirmation_required" in needs["reasonCodes"], "needs gate should require mapping confirmation")

    rejected = gates["rejected"]
    require(rejected["gateStatus"] == "blocked", "rejected gate should block")
    require("source_intake_rejected" in rejected["reasonCodes"], "rejected gate should bind source intake rejection")
    require(
        "post_close_or_unavailable_forecast_source" in rejected["reasonCodes"],
        "rejected gate should preserve leakage reason codes",
    )

    for gate in gates.values():
        require(gate["decision"]["stateOfTheArtClaimAllowed"] is False, "state-of-the-art claims should stay blocked")
        require(gate["decision"]["benchmarkClaimAllowed"] is False, "benchmark claims should stay blocked")

    print("checked setup benchmark gates")


if __name__ == "__main__":
    main()
