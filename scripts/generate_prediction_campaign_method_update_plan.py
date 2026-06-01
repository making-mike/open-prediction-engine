#!/usr/bin/env python3
"""Generate or check prediction campaign method-update plan readbacks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from generate_prediction_campaign_method_update_gate import build_prediction_campaign_method_update_gate
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-method-update-plan"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-method-update-plan.generated.json"
SCHEMA = SPEC / "prediction-campaign-method-update-plan.schema.json"
GENERATED_AT = "2026-05-31T04:30:00Z"
DEFAULT_CASE = "gate_blocked"
METHOD_UPDATE_PLAN_CASES = [
    "gate_blocked",
    "regression_risk",
    "approval_missing",
    "rollback_missing",
    "plan_ready",
]


def gate_case_for(plan_case: str) -> str:
    if plan_case == "gate_blocked":
        return "below_threshold"
    if plan_case == "regression_risk":
        return "regression_risk"
    if plan_case == "approval_missing":
        return "threshold_met_needs_approval"
    return "approved_plan_ready"


def plan_status_for(plan_case: str) -> str:
    statuses = {
        "gate_blocked": "blocked_by_method_update_gate",
        "regression_risk": "blocked_regression_risk",
        "approval_missing": "blocked_missing_approval_artifact",
        "rollback_missing": "blocked_missing_rollback_record",
        "plan_ready": "ready_for_explicit_effectful_command",
    }
    return statuses[plan_case]


def approval_artifact(plan_case: str, gate: dict[str, Any]) -> dict[str, Any]:
    required = gate["approvalGate"]["requiredApprovals"]
    if plan_case == "gate_blocked":
        return {
            "approvalArtifactId": "methodupdateapproval-001",
            "approvalStatus": "not_ready",
            "requiredApprovals": required,
            "receivedApprovals": [],
            "approvedAt": "none",
            "auditTrailStatus": "not_ready",
            "missingItems": ["method_update_gate_plan_ready"],
        }
    if plan_case == "regression_risk":
        return {
            "approvalArtifactId": "methodupdateapproval-001",
            "approvalStatus": "not_ready",
            "requiredApprovals": required,
            "receivedApprovals": [],
            "approvedAt": "none",
            "auditTrailStatus": "not_ready",
            "missingItems": ["candidate_underperforms_baseline", "benchmark_regression_review_required"],
        }
    if plan_case == "approval_missing":
        return {
            "approvalArtifactId": "methodupdateapproval-001",
            "approvalStatus": "missing",
            "requiredApprovals": required,
            "receivedApprovals": [],
            "approvedAt": "none",
            "auditTrailStatus": "missing",
            "missingItems": ["method_owner_approval", "calibration_review_approval", "source_policy_review"],
        }
    return {
        "approvalArtifactId": "methodupdateapproval-001",
        "approvalStatus": "approved",
        "requiredApprovals": required,
        "receivedApprovals": required,
        "approvedAt": "2026-06-12T08:00:00Z",
        "auditTrailStatus": "present_fixture",
        "missingItems": [],
    }


def rollback_record(plan_case: str, current_method_id: str) -> dict[str, Any]:
    if plan_case == "gate_blocked":
        return {
            "rollbackRecordId": "methodupdaterollback-001",
            "rollbackStatus": "not_ready",
            "rollbackCommandShape": "none",
            "restoresMethodId": current_method_id,
            "preservesForecastHistory": True,
            "requiresApprovalBeforeRollback": True,
            "missingItems": ["method_update_gate_plan_ready"],
        }
    if plan_case == "regression_risk":
        return {
            "rollbackRecordId": "methodupdaterollback-001",
            "rollbackStatus": "not_ready",
            "rollbackCommandShape": "none",
            "restoresMethodId": current_method_id,
            "preservesForecastHistory": True,
            "requiresApprovalBeforeRollback": True,
            "missingItems": ["candidate_underperforms_baseline", "benchmark_regression_review_required"],
        }
    if plan_case == "rollback_missing":
        return {
            "rollbackRecordId": "methodupdaterollback-001",
            "rollbackStatus": "missing",
            "rollbackCommandShape": "python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-id predictioncampaignmethodupdateplan-001 --write-local",
            "restoresMethodId": current_method_id,
            "preservesForecastHistory": True,
            "requiresApprovalBeforeRollback": True,
            "missingItems": ["rollback_reason_policy", "restore_previous_method_binding", "rollback_audit_entry"],
        }
    return {
        "rollbackRecordId": "methodupdaterollback-001",
        "rollbackStatus": "present",
        "rollbackCommandShape": "python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-id predictioncampaignmethodupdateplan-001 --write-local",
        "restoresMethodId": current_method_id,
        "preservesForecastHistory": True,
        "requiresApprovalBeforeRollback": True,
        "missingItems": [],
    }


def blocking_reasons(plan_case: str) -> list[str]:
    if plan_case == "gate_blocked":
        return ["method_update_gate_not_plan_ready"]
    if plan_case == "regression_risk":
        return ["candidate_underperforms_baseline", "benchmark_regression_review_required"]
    if plan_case == "approval_missing":
        return ["approval_artifact_missing"]
    if plan_case == "rollback_missing":
        return ["rollback_record_missing"]
    return []


def recommended_next_action(plan_case: str) -> str:
    if plan_case == "gate_blocked":
        return "Keep collecting comparable evidence until the method-update gate is plan-ready."
    if plan_case == "regression_risk":
        return "Keep the baseline method and continue the pilot on transitmethod-100."
    if plan_case == "approval_missing":
        return "Create the approval artifact before preparing any effectful method-update command."
    if plan_case == "rollback_missing":
        return "Create the rollback record before preparing any effectful method-update command."
    return "A future explicit effectful command may be designed from this plan; do not apply it from this readback."


def build_prediction_campaign_method_update_plan(*, method_update_plan_case: str = DEFAULT_CASE) -> dict[str, Any]:
    if method_update_plan_case not in METHOD_UPDATE_PLAN_CASES:
        raise ValueError(f"unknown method update plan case: {method_update_plan_case}")
    gate = build_prediction_campaign_method_update_gate(method_update_case=gate_case_for(method_update_plan_case))
    bindings = gate["bindings"]
    current_method_id = bindings["currentMethodId"]
    candidate_method_id = bindings["candidateMethodId"]
    approval = approval_artifact(method_update_plan_case, gate)
    rollback = rollback_record(method_update_plan_case, current_method_id)
    plan_ready = method_update_plan_case == "plan_ready"
    gate_ready = gate["decision"]["methodUpdatePlanReady"]
    approval_ready = approval["approvalStatus"] == "approved"
    rollback_ready = rollback["rollbackStatus"] == "present"
    return {
        "predictionCampaignMethodUpdatePlanId": "predictioncampaignmethodupdateplan-001",
        "generatedAt": GENERATED_AT,
        "planCase": method_update_plan_case,
        "planStatus": plan_status_for(method_update_plan_case),
        "domain": gate["domain"],
        "bindings": {
            "predictionCampaignManifestId": bindings["predictionCampaignManifestId"],
            "predictionCampaignMethodUpdateGateId": gate["predictionCampaignMethodUpdateGateId"],
            "campaignId": bindings["campaignId"],
            "cycleId": bindings["cycleId"],
            "sourcePolicyId": bindings["sourcePolicyId"],
            "currentMethodId": current_method_id,
            "candidateMethodId": candidate_method_id,
        },
        "approvalArtifact": approval,
        "futureEffectfulCommand": {
            "commandShape": "python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-id predictioncampaignmethodupdateplan-001 --method-update-plan-case plan_ready --write-local",
            "dryRunPreviewCommand": "python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view command",
            "targetMethodId": candidate_method_id,
            "requiresWriteFlag": True,
            "requiresApprovalArtifact": True,
            "requiresRollbackRecord": True,
            "implementedNow": True,
            "normalChecksMayRun": False,
            "writesMethodRegistry": False,
            "writesCampaignState": True,
            "updatesForecastProbabilities": False,
            "changesForecastMethod": True,
        },
        "rollbackRecord": rollback,
        "preflightChecks": {
            "methodUpdateGateReady": gate_ready,
            "approvalArtifactReady": approval_ready,
            "rollbackRecordReady": rollback_ready,
            "auditTrailReady": approval_ready and rollback_ready,
            "effectfulCommandBlockedInNormalChecks": True,
            "blockingReasons": blocking_reasons(method_update_plan_case),
        },
        "decision": {
            "methodUpdatePlanReady": plan_ready,
            "effectfulUpdateAllowedNow": False,
            "automaticUpdateAllowed": False,
            "futureEffectfulCommandRequired": plan_ready,
            "qualityClaimAllowed": False,
            "recommendedNextAction": recommended_next_action(method_update_plan_case),
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign method-update-plan",
            "acceptedFlags": ["--method-update-plan-case", "--output-format", "--view"],
            "defaultMode": "checked_method_update_plan_readback",
            "capturedStdoutMode": "json",
            "normalChecksMutateState": False,
        },
        "executionBoundary": {
            "readsIgnoredLiveState": False,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsForecastArtifacts": False,
            "updatesForecastProbabilities": False,
            "changesForecastMethod": False,
            "changesMethodWeights": False,
            "writesMethodRegistry": False,
            "writesPlanArtifact": False,
            "startsNextCycle": False,
        },
        "warnings": [
            "This plan is a readback and never applies a method update.",
            "The effectful command is implemented only behind an explicit --write-local action command.",
            "Rollback records must preserve forecast history and cannot rewrite prior forecasts.",
        ],
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "plan": record,
        "approval": record["approvalArtifact"],
        "command": record["futureEffectfulCommand"],
        "rollback": record["rollbackRecord"],
        "preflight": record["preflightChecks"],
        "decision": record["decision"],
        "summary": {
            "planStatus": record["planStatus"],
            "methodUpdatePlanReady": record["decision"]["methodUpdatePlanReady"],
            "effectfulUpdateAllowedNow": record["decision"]["effectfulUpdateAllowedNow"],
            "futureEffectfulCommandRequired": record["decision"]["futureEffectfulCommandRequired"],
            "recommendedNextAction": record["decision"]["recommendedNextAction"],
        },
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        print(f"{record['planStatus']} plan_ready={record['decision']['methodUpdatePlanReady']}")
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign method update plan",
        regen="python3 scripts/generate_prediction_campaign_method_update_plan.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated method-update plan")
    parser.add_argument("--check", action="store_true", help="check generated method-update plan drift")
    parser.add_argument(
        "--method-update-plan-case",
        choices=METHOD_UPDATE_PLAN_CASES,
        default=DEFAULT_CASE,
        help="checked method-update plan case",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["plan", "approval", "command", "rollback", "preflight", "decision", "summary", "boundary"],
        default="plan",
        help="print one prediction campaign method-update plan view",
    )
    args = parser.parse_args()
    if (args.write or args.check) and args.method_update_plan_case != DEFAULT_CASE:
        raise SystemExit("custom method-update plan cases cannot be combined with --write or --check")
    record = build_prediction_campaign_method_update_plan(method_update_plan_case=args.method_update_plan_case)
    if args.write or args.check:
        check_or_write(record, write=args.write)
        return
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
