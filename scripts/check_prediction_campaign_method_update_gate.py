#!/usr/bin/env python3
"""Check prediction campaign method-update gate semantics."""

from __future__ import annotations

from generate_prediction_campaign_method_update_gate import build_prediction_campaign_method_update_gate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    below = build_prediction_campaign_method_update_gate()
    require(
        below["gateStatus"] == "blocked_insufficient_calibration_evidence",
        "default method-update gate should stay below threshold",
    )
    require(below["evidenceReadback"]["resolvedComparableSampleSize"] == 1, "below-threshold sample drifted")
    require(below["decision"]["methodUpdatePlanReady"] is False, "below threshold must not be plan-ready")
    require(
        below["executionBoundary"]["changesForecastMethod"] is False,
        "method-update gate must not change the forecast method",
    )
    require(
        below["executionBoundary"]["updatesForecastProbabilities"] is False,
        "method-update gate must not update probabilities",
    )

    review = build_prediction_campaign_method_update_gate(method_update_case="threshold_met_needs_approval")
    require(review["gateStatus"] == "review_required", "threshold-met review status drifted")
    require(review["evidenceReadback"]["comparableEvidenceReady"] is True, "threshold case should have evidence ready")
    require(review["approvalGate"]["approvalStatus"] == "missing", "review case should require approval")
    require(review["methodUpdateProposal"]["proposalStatus"] == "needs_approval", "review proposal status drifted")
    require(review["decision"]["effectfulUpdateAllowedNow"] is False, "review case must not allow mutation")

    approved = build_prediction_campaign_method_update_gate(method_update_case="approved_plan_ready")
    require(approved["gateStatus"] == "plan_ready", "approved case should be plan-ready")
    require(approved["approvalGate"]["approvalStatus"] == "approved", "approved case approval status drifted")
    require(
        approved["methodUpdateProposal"]["candidateSelectionEligibility"] == "eligible_for_explicit_plan",
        "approved case should only be eligible for an explicit plan",
    )
    require(approved["decision"]["methodUpdatePlanReady"] is True, "approved case should be plan-ready")
    require(approved["decision"]["automaticUpdateAllowed"] is False, "approved case must not allow automatic updates")
    require(approved["executionBoundary"]["writesMethodRegistry"] is False, "approved case must not write registry")

    regression = build_prediction_campaign_method_update_gate(method_update_case="regression_risk")
    require(regression["gateStatus"] == "blocked_regression_risk", "regression case status drifted")
    require(regression["evidenceReadback"]["candidateBaselineLift"] < 0, "regression case should show negative lift")
    require(
        "candidate_underperforms_baseline" in regression["methodUpdateProposal"]["rejectionReasons"],
        "regression case should reject the candidate",
    )
    print("checked prediction campaign method update gate")


if __name__ == "__main__":
    main()
