#!/usr/bin/env python3
"""Generate or check prediction campaign method-update gate readbacks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from generate_prediction_campaign_calibration_status import build_prediction_campaign_calibration_status
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_transit_method_options import BASELINE_METHOD_ID, WEATHER_ADJUSTMENT_METHOD_ID, build_options
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-method-update-gate"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-method-update-gate.generated.json"
SCHEMA = SPEC / "prediction-campaign-method-update-gate.schema.json"
GENERATED_AT = "2026-05-31T04:00:00Z"
DEFAULT_CASE = "below_threshold"
METHOD_UPDATE_CASES = [
    "below_threshold",
    "threshold_met_needs_approval",
    "approved_plan_ready",
    "regression_risk",
]


def round_float(value: float) -> float:
    return round(value, 10)


def calibration_case_for(gate_case: str) -> str:
    if gate_case == "below_threshold":
        return "below_threshold"
    return "threshold_met"


def gate_status_for(gate_case: str) -> str:
    statuses = {
        "below_threshold": "blocked_insufficient_calibration_evidence",
        "threshold_met_needs_approval": "review_required",
        "approved_plan_ready": "plan_ready",
        "regression_risk": "blocked_regression_risk",
    }
    return statuses[gate_case]


def approval_status_for(gate_case: str) -> str:
    if gate_case == "below_threshold":
        return "not_requested"
    if gate_case == "approved_plan_ready":
        return "approved"
    return "missing"


def candidate_lift_for(gate_case: str, candidate: dict[str, Any]) -> float:
    if gate_case == "regression_risk":
        return -0.02
    return float(candidate.get("baselineLift", 0.06))


def rejection_reasons(gate_case: str) -> list[str]:
    if gate_case == "below_threshold":
        return [
            "resolved_comparable_sample_below_calibration_threshold",
            "calibration_summary_missing",
            "explicit_method_update_approval_not_requested",
        ]
    if gate_case == "threshold_met_needs_approval":
        return ["explicit_method_update_approval_missing", "method_update_audit_trail_missing"]
    if gate_case == "regression_risk":
        return ["candidate_underperforms_baseline", "benchmark_regression_review_required"]
    return []


def proposal_status_for(gate_case: str) -> str:
    if gate_case == "approved_plan_ready":
        return "ready_for_explicit_update_plan"
    if gate_case == "threshold_met_needs_approval":
        return "needs_approval"
    return "blocked"


def selection_eligibility_for(gate_case: str) -> str:
    if gate_case == "approved_plan_ready":
        return "eligible_for_explicit_plan"
    if gate_case == "threshold_met_needs_approval":
        return "requires_review"
    return "blocked"


def recommended_next_action(gate_case: str) -> str:
    if gate_case == "below_threshold":
        return "Keep the baseline method and continue collecting comparable resolved outcomes."
    if gate_case == "threshold_met_needs_approval":
        return "Collect explicit method-owner approval and an audit trail before preparing a method-update plan."
    if gate_case == "regression_risk":
        return "Keep the baseline method and review candidate benchmark regression before any update plan."
    return "Prepare a future explicit method-update plan; do not apply it from this readback."


def build_prediction_campaign_method_update_gate(*, method_update_case: str = DEFAULT_CASE) -> dict[str, Any]:
    if method_update_case not in METHOD_UPDATE_CASES:
        raise ValueError(f"unknown method update case: {method_update_case}")
    manifest = build_prediction_campaign_manifest()
    calibration = build_prediction_campaign_calibration_status(
        calibration_case=calibration_case_for(method_update_case)
    )
    options = build_options()
    method_options = {option["methodId"]: option for option in options["methodOptions"]}
    candidate = method_options[WEATHER_ADJUSTMENT_METHOD_ID]
    approval_status = approval_status_for(method_update_case)
    gate_status = gate_status_for(method_update_case)
    candidate_lift = candidate_lift_for(method_update_case, candidate)
    comparable_ready = (
        calibration["thresholdReadback"]["resolvedComparableSampleSize"]
        >= calibration["thresholdReadback"]["minimumComparableResolvedForCalibration"]
    )
    plan_ready = gate_status == "plan_ready"
    received_approvals = (
        ["method_owner_approval", "calibration_review_approval", "source_policy_review"]
        if approval_status == "approved"
        else []
    )
    proposal_change = (
        "baseline_to_transparent_weather_adjustment"
        if method_update_case in {"threshold_met_needs_approval", "approved_plan_ready"}
        else "none"
    )
    return {
        "predictionCampaignMethodUpdateGateId": "predictioncampaignmethodupdategate-001",
        "generatedAt": GENERATED_AT,
        "gateCase": method_update_case,
        "gateStatus": gate_status,
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignCalibrationStatusId": calibration["predictionCampaignCalibrationStatusId"],
            "transitMethodOptionsId": options["transitMethodOptionsId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
            "currentMethodId": BASELINE_METHOD_ID,
            "candidateMethodId": WEATHER_ADJUSTMENT_METHOD_ID,
        },
        "evidenceReadback": {
            "resolvedComparableSampleSize": calibration["thresholdReadback"]["resolvedComparableSampleSize"],
            "minimumComparableResolvedForCalibration": calibration["thresholdReadback"][
                "minimumComparableResolvedForCalibration"
            ],
            "exclusionRate": calibration["thresholdReadback"]["exclusionRate"],
            "calibrationStatus": calibration["calibrationStatus"],
            "calibrationSummaryGenerated": calibration["calibrationReadback"]["summaryGenerated"],
            "calibrationMeasurementOnly": calibration["calibrationReadback"]["measurementOnly"],
            "candidateBenchmarkStatus": candidate["benchmarkStatus"],
            "candidateBaselineLift": round_float(candidate_lift),
            "cleanAntiLeakageEvidence": method_update_case != "below_threshold",
            "comparableEvidenceReady": comparable_ready,
            "approvalStatus": approval_status,
        },
        "methodUpdateProposal": {
            "currentMethodId": BASELINE_METHOD_ID,
            "candidateMethodId": WEATHER_ADJUSTMENT_METHOD_ID,
            "proposedChange": proposal_change,
            "candidateSelectionEligibility": selection_eligibility_for(method_update_case),
            "probabilityRecalibrationProposed": False,
            "methodWeightChangeProposed": False,
            "automaticUpdateAllowed": False,
            "explicitApprovalRequired": True,
            "proposalStatus": proposal_status_for(method_update_case),
            "rejectionReasons": rejection_reasons(method_update_case),
        },
        "approvalGate": {
            "requiredApprovals": [
                "method_owner_approval",
                "calibration_review_approval",
                "source_policy_review",
            ],
            "receivedApprovals": received_approvals,
            "approvalStatus": approval_status,
            "policyStatus": "passed_source_policy_review" if approval_status == "approved" else "pending_source_policy_review",
            "benchmarkStatus": "passed_positive_lift_review" if plan_ready else gate_status,
            "antiLeakageStatus": "passed_forecast_time_only_review" if method_update_case != "below_threshold" else "not_ready",
            "auditTrailStatus": "present_fixture" if approval_status == "approved" else "missing",
        },
        "decision": {
            "methodUpdatePlanReady": plan_ready,
            "effectfulUpdateAllowedNow": False,
            "automaticUpdateAllowed": False,
            "requiresFutureEffectfulCommand": plan_ready,
            "qualityClaimAllowed": False,
            "recommendedNextAction": recommended_next_action(method_update_case),
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign method-update-gate",
            "acceptedFlags": ["--method-update-case", "--output-format", "--view"],
            "defaultMode": "checked_method_update_gate_readback",
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
            "startsNextCycle": False,
        },
        "warnings": [
            "This gate is a readback and never applies a method update.",
            "Automatic probability recalibration and automatic method changes remain disallowed.",
            "A plan-ready result still requires a future explicit effectful update command with an audit trail.",
        ],
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "gate": record,
        "evidence": record["evidenceReadback"],
        "proposal": record["methodUpdateProposal"],
        "approval": record["approvalGate"],
        "decision": record["decision"],
        "summary": {
            "gateStatus": record["gateStatus"],
            "methodUpdatePlanReady": record["decision"]["methodUpdatePlanReady"],
            "effectfulUpdateAllowedNow": record["decision"]["effectfulUpdateAllowedNow"],
            "automaticUpdateAllowed": record["decision"]["automaticUpdateAllowed"],
            "recommendedNextAction": record["decision"]["recommendedNextAction"],
        },
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        print(f"{record['gateStatus']} plan_ready={record['decision']['methodUpdatePlanReady']}")
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
        label="prediction campaign method update gate",
        regen="python3 scripts/generate_prediction_campaign_method_update_gate.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated method-update gate")
    parser.add_argument("--check", action="store_true", help="check generated method-update gate drift")
    parser.add_argument(
        "--method-update-case",
        choices=METHOD_UPDATE_CASES,
        default=DEFAULT_CASE,
        help="checked method-update gate case",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["gate", "evidence", "proposal", "approval", "decision", "summary", "boundary"],
        default="gate",
        help="print one prediction campaign method-update gate view",
    )
    args = parser.parse_args()
    if (args.write or args.check) and args.method_update_case != DEFAULT_CASE:
        raise SystemExit("custom method-update cases cannot be combined with --write or --check")
    record = build_prediction_campaign_method_update_gate(method_update_case=args.method_update_case)
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
