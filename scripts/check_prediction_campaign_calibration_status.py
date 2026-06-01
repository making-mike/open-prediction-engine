#!/usr/bin/env python3
"""Check prediction campaign calibration-status semantics."""

from __future__ import annotations

from pathlib import Path
import tempfile

from generate_prediction_campaign_calibration_status import build_prediction_campaign_calibration_status
from ope_fixtures import render_json
import generate_transit_baseline_track_record_gate as track_gate_module


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    below = build_prediction_campaign_calibration_status()
    require(
        below["calibrationStatus"] == "not_enough_resolved_comparable_outcomes",
        "default calibration status should stay below threshold",
    )
    require(below["thresholdReadback"]["resolvedComparableSampleSize"] == 1, "below-threshold sample drifted")
    require(below["calibrationReadback"]["summaryGenerated"] is False, "below threshold must not generate summary")
    require(below["calibrationReadback"]["calibrationSummary"] is None, "below threshold summary must be null")
    require(below["summary"]["calibrationClaimAllowed"] is False, "below threshold must block calibration claims")
    require(below["executionBoundary"]["writesCampaignState"] is False, "calibration status must be read-only")
    require(below["executionBoundary"]["changesForecastMethod"] is False, "calibration status must not change method")

    threshold = build_prediction_campaign_calibration_status(calibration_case="threshold_met")
    require(threshold["calibrationStatus"] == "ready", "threshold-met status drifted")
    require(threshold["thresholdReadback"]["resolvedComparableSampleSize"] == 100, "threshold sample drifted")
    require(threshold["calibrationReadback"]["summaryGenerated"] is True, "threshold case should generate summary")
    require(
        threshold["calibrationReadback"]["calibrationSummary"]["measurementOnly"] is True,
        "threshold summary should remain measurement-only",
    )
    require(
        threshold["calibrationReadback"]["automaticMethodChangeAllowed"] is False,
        "threshold case must not allow automatic method change",
    )

    exclusions = build_prediction_campaign_calibration_status(calibration_case="too_many_exclusions")
    require(
        exclusions["calibrationStatus"] == "blocked_too_many_exclusions",
        "too-many-exclusions status drifted",
    )
    require(exclusions["calibrationReadback"]["summaryGenerated"] is False, "exclusion block must withhold summary")
    require(exclusions["summary"]["calibrationClaimAllowed"] is False, "exclusion block must block calibration claim")

    restart = build_prediction_campaign_calibration_status(calibration_case="post_calibration_restart")
    require(restart["calibrationStatus"] == "post_calibration_restart_ready", "restart status drifted")
    require(restart["cycleState"]["cycleState"] == "pause_scheduled", "restart should schedule a pause")
    require(restart["cycleState"]["postCalibrationAction"] == "pause_then_resume_after", "restart action drifted")
    require(restart["cycleState"]["nextCycleId"] == "predictioncycle-002", "restart next cycle drifted")
    require(restart["executionBoundary"]["startsNextCycle"] is False, "restart readback must not start a cycle")
    check_local_ledger_cases()
    print("checked prediction campaign calibration status")


def comparable_row(index: int, *, complete: bool = True) -> dict:
    suffix = f"{1300 + index}"
    outcome_yes = index % 4 == 0
    row = {
        "rowId": f"campaignledgerrow-{suffix}",
        "rowKind": "comparable",
        "rowKey": f"predictioncampaign-001:predictionrun-{suffix}:forecast-{suffix}:scoring-{suffix}:comparable",
        "campaignId": "predictioncampaign-001",
        "cycleId": "predictioncycle-001",
        "runId": f"predictionrun-{suffix}",
        "questionId": f"question-{suffix}",
        "forecastId": f"forecast-{suffix}",
        "evidencePacketId": f"evidence-{suffix}",
        "historyId": f"history-{suffix}",
        "serviceDate": "2026-06-11",
        "serviceWindow": "morning_peak",
        "sourcePolicyId": "sourcepolicy-1201",
        "runStatus": "scored",
        "runStatePath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}.json",
        "forecastArtifactPath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}/forecast-{suffix}.json",
        "evidencePacketPath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}/evidence-{suffix}.json",
        "forecastHistoryPath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}/history-{suffix}.json",
        "resolutionRecordPath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}/resolution-{suffix}.json",
        "scoringReportPath": f".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-{suffix}/scoring-{suffix}.json",
        "forecastProbability": 0.25,
        "baselineProbability": 0.3,
        "resolutionRecordId": f"resolution-{suffix}",
        "scoringReportId": f"scoring-{suffix}",
        "outcomeLabel": "yes" if outcome_yes else "no",
        "scoreStatus": "scored",
        "primaryScore": 0.5625 if outcome_yes else 0.0625,
        "baselineScore": 0.49 if outcome_yes else 0.09,
    }
    if not complete:
        row["scoringReportPath"] = "none"
    return row


def excluded_row(index: int) -> dict:
    suffix = f"{1500 + index}"
    return {
        "rowId": f"campaignledgerrow-{suffix}",
        "rowKind": "excluded",
        "rowKey": f"predictioncampaign-001:predictionrun-{suffix}:forecast-{suffix}:scoring-{suffix}:excluded",
        "campaignId": "predictioncampaign-001",
        "cycleId": "predictioncycle-001",
        "runId": f"predictionrun-{suffix}",
        "questionId": f"question-{suffix}",
        "forecastId": f"forecast-{suffix}",
        "sourcePolicyId": "sourcepolicy-1201",
        "scoreStatus": "excluded",
        "exclusionReason": "missing_outcome",
    }


def write_local_ledger(root: Path, comparable_count: int, excluded_count: int, *, complete: bool = True) -> None:
    rows = [comparable_row(index, complete=complete or index != 1) for index in range(1, comparable_count + 1)]
    excluded = [excluded_row(index) for index in range(1, excluded_count + 1)]
    path = root / ".ope/live/prediction-campaigns/predictioncampaign-001/evidence-ledger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_json(
            {
                "stateType": "prediction_campaign_evidence_ledger",
                "writtenAt": "2026-06-25T07:30:00Z",
                "campaignId": "predictioncampaign-001",
                "cycleId": "predictioncycle-001",
                "domain": "weather-transit-delays",
                "ledgerPath": ".ope/live/prediction-campaigns/predictioncampaign-001/evidence-ledger.json",
                "appendOnly": True,
                "rowKeys": [row["rowKey"] for row in rows + excluded],
                "comparableRows": rows,
                "excludedRows": excluded,
                "summary": {
                    "comparableRowCount": len(rows),
                    "excludedRowCount": len(excluded),
                    "qualityClaimAllowed": False,
                    "calibrationClaimAllowed": False,
                },
            }
        ),
        encoding="utf-8",
    )


def local_record(comparable_count: int, excluded_count: int, *, complete: bool = True) -> dict:
    original_root = track_gate_module.LOCAL_WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        track_gate_module.LOCAL_WORKSPACE_ROOT = root
        try:
            write_local_ledger(root, comparable_count, excluded_count, complete=complete)
            return build_prediction_campaign_calibration_status(
                campaign="predictioncampaign-001",
                from_local_ledger=True,
            )
        finally:
            track_gate_module.LOCAL_WORKSPACE_ROOT = original_root


def check_local_ledger_cases() -> None:
    below = local_record(99, 1)
    require(below["calibrationCase"] == "local_ledger", "local calibration case should be explicit")
    require(
        below["calibrationStatus"] == "not_enough_resolved_comparable_outcomes",
        "99 comparable local rows should stay below threshold",
    )
    require(below["thresholdReadback"]["resolvedComparableSampleSize"] == 99, "local below-threshold count drifted")
    require(below["executionBoundary"]["readsIgnoredLiveState"] is True, "local calibration should read ignored ledger")
    require(below["calibrationReadback"]["summaryGenerated"] is False, "local below-threshold must not summarize")

    ready = local_record(100, 10)
    require(ready["calibrationStatus"] == "ready", "100 comparable local rows should be calibration-ready")
    require(ready["thresholdReadback"]["campaignLedgerCase"] == "local_evidence_ledger", "local ledger case drifted")
    require(ready["thresholdReadback"]["sourceOutcomeProvenanceComplete"] is True, "local provenance should be complete")
    require(ready["calibrationReadback"]["summaryGenerated"] is True, "local ready case should summarize")
    summary = ready["calibrationReadback"]["calibrationSummary"]
    require(summary["sampleSize"] == 100, "local calibration summary sample size drifted")
    require(summary["bucketCount"] == 10, "local calibration summary bucket count drifted")
    require(summary["measurementOnly"] is True, "local calibration summary must be measurement-only")
    require(ready["summary"]["methodUpdateImplemented"] is False, "local calibration must not implement method update")

    exclusions = local_record(100, 60)
    require(
        exclusions["calibrationStatus"] == "blocked_too_many_exclusions",
        "high local exclusion rate should block calibration",
    )
    require(exclusions["calibrationReadback"]["summaryGenerated"] is False, "blocked exclusion case must not summarize")

    incomplete = local_record(100, 0, complete=False)
    require(
        incomplete["calibrationStatus"] == "blocked_incomplete_provenance",
        "incomplete local provenance should block calibration",
    )
    require(incomplete["summary"]["calibrationClaimAllowed"] is False, "incomplete provenance must block claims")


if __name__ == "__main__":
    main()
