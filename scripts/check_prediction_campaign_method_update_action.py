#!/usr/bin/env python3
"""Check prediction campaign method-update action semantics."""

from __future__ import annotations

import tempfile
from pathlib import Path

import generate_prediction_campaign_method_update_action as action_module
from generate_prediction_campaign_method_update_action import (
    BASELINE_METHOD_ID,
    WEATHER_ADJUSTMENT_METHOD_ID,
    PredictionCampaignMethodUpdateError,
    build_prediction_campaign_method_update_action,
    execute_local_method_update,
)
from ope_fixtures import render_json


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def campaign_state(resolved: int = 100) -> dict[str, object]:
    return {
        "stateType": "prediction_campaign_state",
        "stateVersion": 1,
        "writtenAt": "2026-05-31T05:00:00Z",
        "campaignId": "predictioncampaign-001",
        "cycleId": "predictioncycle-001",
        "resolvedComparableOutcomes": resolved,
        "executionBoundary": {
            "qualityClaimAllowed": False,
        },
    }


def write_campaign_state(root: Path, resolved: int = 100) -> Path:
    path = root / ".ope" / "live" / "prediction-campaigns" / "predictioncampaign-001" / "campaign-manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(campaign_state(resolved=resolved)), encoding="utf-8")
    return path


def main() -> None:
    blocked = build_prediction_campaign_method_update_action()
    require(blocked["operation"] == "apply", "default action should be apply")
    require(blocked["actionStatus"] == "blocked_by_method_update_plan", "default action should be plan-blocked")
    require(blocked["decision"]["localWriteEligible"] is False, "blocked action must not be write-eligible")
    require(blocked["executionBoundary"]["writesMethodBinding"] is False, "default action must not write bindings")

    regression = build_prediction_campaign_method_update_action(method_update_plan_case="regression_risk")
    require(regression["actionStatus"] == "blocked_candidate_regression_risk", "regression action status drifted")
    require(regression["candidateEvidence"]["evidenceSupportsCandidate"] is False, "regression evidence must block candidate")

    ready = build_prediction_campaign_method_update_action(method_update_plan_case="plan_ready")
    require(ready["actionStatus"] == "ready_for_explicit_local_apply", "plan-ready apply status drifted")
    require(ready["decision"]["localWriteEligible"] is True, "plan-ready apply should be write-eligible")
    require(ready["methodBinding"]["targetMethodId"] == WEATHER_ADJUSTMENT_METHOD_ID, "apply target method drifted")
    require(ready["writeResult"]["writeStatus"] == "not_run", "dry-run apply must not run writes")
    for check in ready["preflightChecks"]:
        require(check["blocksWrite"] is False, f"ready apply preflight should not block: {check['checkId']}")

    rollback_ready = build_prediction_campaign_method_update_action(
        operation="rollback",
        method_update_plan_case="plan_ready",
    )
    require(
        rollback_ready["actionStatus"] == "ready_for_explicit_local_rollback",
        "plan-ready rollback status drifted",
    )
    require(rollback_ready["methodBinding"]["targetMethodId"] == BASELINE_METHOD_ID, "rollback target drifted")

    mismatch = build_prediction_campaign_method_update_action(
        method_update_plan_case="plan_ready",
        method_update_plan_id="predictioncampaignmethodupdateplan-999",
    )
    require(mismatch["actionStatus"] == "blocked_plan_id_mismatch", "plan id mismatch should block")

    original_root = action_module.LOCAL_WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        action_module.LOCAL_WORKSPACE_ROOT = temp_root
        write_campaign_state(temp_root, resolved=100)

        applied_result = execute_local_method_update(ready)
        require(applied_result["writeStatus"] == "local_apply_completed", "apply write should complete")
        applied = build_prediction_campaign_method_update_action(
            method_update_plan_case="plan_ready",
            write_result=applied_result,
        )
        require(applied["executionBoundary"]["writesMethodBinding"] is True, "apply should write method binding")
        binding_path = temp_root / ready["methodBinding"]["methodBindingPath"]
        binding = action_module.read_json(binding_path)
        require(binding["activeMethodId"] == WEATHER_ADJUSTMENT_METHOD_ID, "binding should activate candidate")
        state = action_module.read_json(temp_root / ready["writePlan"]["campaignStatePath"])
        require(state["activeMethodId"] == WEATHER_ADJUSTMENT_METHOD_ID, "campaign state should activate candidate")
        require(state["executionBoundary"]["rewritesPriorForecastHistories"] is False, "apply must not rewrite histories")

        applied_again = execute_local_method_update(ready)
        require(applied_again["writeStatus"] == "local_apply_already_present", "apply should be idempotent")

        rolled_back_result = execute_local_method_update(rollback_ready)
        require(rolled_back_result["writeStatus"] == "local_rollback_completed", "rollback write should complete")
        binding_after = action_module.read_json(binding_path)
        require(binding_after["activeMethodId"] == BASELINE_METHOD_ID, "rollback should restore baseline")

    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        action_module.LOCAL_WORKSPACE_ROOT = temp_root
        write_campaign_state(temp_root, resolved=99)
        try:
            execute_local_method_update(ready)
        except PredictionCampaignMethodUpdateError as exc:
            require("100 resolved comparable outcomes" in str(exc), "threshold blocker message drifted")
        else:
            raise AssertionError("apply should block when local campaign state is below threshold")

    action_module.LOCAL_WORKSPACE_ROOT = original_root
    print("checked prediction campaign method update action")


if __name__ == "__main__":
    main()
