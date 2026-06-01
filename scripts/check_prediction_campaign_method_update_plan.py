#!/usr/bin/env python3
"""Check prediction campaign method-update plan semantics."""

from __future__ import annotations

from generate_prediction_campaign_method_update_plan import build_prediction_campaign_method_update_plan


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    blocked = build_prediction_campaign_method_update_plan()
    require(blocked["planStatus"] == "blocked_by_method_update_gate", "default plan should be gate-blocked")
    require(blocked["decision"]["methodUpdatePlanReady"] is False, "gate-blocked plan must not be ready")
    require(blocked["approvalArtifact"]["approvalStatus"] == "not_ready", "gate-blocked approval should not be ready")
    require(blocked["rollbackRecord"]["rollbackStatus"] == "not_ready", "gate-blocked rollback should not be ready")

    regression = build_prediction_campaign_method_update_plan(method_update_plan_case="regression_risk")
    require(regression["planStatus"] == "blocked_regression_risk", "regression status drifted")
    require(
        "candidate_underperforms_baseline" in regression["preflightChecks"]["blockingReasons"],
        "regression case should keep the candidate blocked",
    )
    require(regression["decision"]["methodUpdatePlanReady"] is False, "regression case must not be plan-ready")

    approval_missing = build_prediction_campaign_method_update_plan(method_update_plan_case="approval_missing")
    require(
        approval_missing["planStatus"] == "blocked_missing_approval_artifact",
        "approval-missing status drifted",
    )
    require(
        approval_missing["preflightChecks"]["methodUpdateGateReady"] is False,
        "approval-missing case should not pass the gate yet",
    )
    require(
        "approval_artifact_missing" in approval_missing["preflightChecks"]["blockingReasons"],
        "approval-missing case should name approval blocker",
    )

    rollback_missing = build_prediction_campaign_method_update_plan(method_update_plan_case="rollback_missing")
    require(
        rollback_missing["planStatus"] == "blocked_missing_rollback_record",
        "rollback-missing status drifted",
    )
    require(rollback_missing["approvalArtifact"]["approvalStatus"] == "approved", "rollback case should have approval")
    require(rollback_missing["rollbackRecord"]["rollbackStatus"] == "missing", "rollback case should miss rollback")
    require(
        rollback_missing["decision"]["effectfulUpdateAllowedNow"] is False,
        "rollback-missing case must not allow mutation",
    )

    plan_ready = build_prediction_campaign_method_update_plan(method_update_plan_case="plan_ready")
    require(plan_ready["planStatus"] == "ready_for_explicit_effectful_command", "plan-ready status drifted")
    require(plan_ready["approvalArtifact"]["approvalStatus"] == "approved", "plan-ready approval should be approved")
    require(plan_ready["rollbackRecord"]["rollbackStatus"] == "present", "plan-ready rollback should be present")
    require(plan_ready["preflightChecks"]["auditTrailReady"] is True, "plan-ready audit trail should be ready")
    require(plan_ready["decision"]["methodUpdatePlanReady"] is True, "plan-ready decision should be true")
    require(plan_ready["decision"]["effectfulUpdateAllowedNow"] is False, "plan readback must not allow mutation now")
    require(
        plan_ready["executionBoundary"]["writesMethodRegistry"] is False,
        "plan readback must not write method registry",
    )
    require(
        plan_ready["futureEffectfulCommand"]["implementedNow"] is True,
        "effectful command should now be implemented behind explicit write-local",
    )
    print("checked prediction campaign method update plan")


if __name__ == "__main__":
    main()
