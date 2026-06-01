#!/usr/bin/env python3
"""Check prediction campaign explain invariants."""

from __future__ import annotations

from generate_prediction_campaign_explain import build_prediction_campaign_explain


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_prediction_campaign_explain()
    bindings = record["bindings"]
    snapshot = record["campaignSnapshot"]
    claims = record["claimBoundary"]
    summary = record["summary"]
    boundary = record["executionBoundary"]
    task = record["pilotTaskCard"]
    error_codes = {item["errorCode"] for item in record["sanitizedErrorEnvelopes"]}
    agent_ops = {item["operation"] for item in record["agentReadbacks"]}

    require(record["explainStatus"] == "checked_pilot_readback", "explain status drifted")
    require(bindings["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(bindings["runId"] == "predictionrun-1301", "run binding drifted")
    require(bindings["forecastId"] == "forecast-1301", "forecast binding drifted")
    require(bindings["questionId"] == "question-1301", "question binding drifted")

    require(snapshot["plannedRunCount"] == 4, "planned run count drifted")
    require(snapshot["nextForecastRunId"] == "predictionrun-1301", "next run drifted")
    require(snapshot["nextForecastCloseAt"] == "2026-06-11T04:45:00Z", "forecast close drifted")
    require(snapshot["resolvedComparableSampleSize"] == 1, "comparable sample count drifted")
    require(snapshot["minimumComparableResolvedForCalibration"] == 100, "calibration threshold drifted")
    require(snapshot["qualityClaimAllowed"] is False, "snapshot must keep quality claim blocked")

    require(len(record["explanationPrompts"]) == 5, "explanation prompt count drifted")
    require(len(record["workflowRunbook"]) == 5, "workflow runbook step count drifted")
    require(task["scenarioKey"] == "repeating_prediction_campaign", "pilot task scenario drifted")
    require(task["command"] == "python3 scripts/ope.py prediction-campaign explain", "pilot task command drifted")
    require("claim_boundary_comprehension" in task["measures"], "pilot task must capture claim boundary")

    require(agent_ops == {"plan", "status", "health", "append_readiness", "calibration_status"}, "agent readback coverage drifted")
    require(all(item["implementedInAgentAdapter"] for item in record["agentReadbacks"]), "agent adapter readbacks should be implemented")
    require(
        error_codes
        == {
            "invalid_interval",
            "missed_forecast_close",
            "unavailable_live_source",
            "duplicate_campaign",
            "unsafe_source_policy",
            "unsupported_post_calibration_action",
        },
        "sanitized error envelope coverage drifted",
    )
    for error in record["sanitizedErrorEnvelopes"]:
        require(error["sanitized"] is True, "error envelopes must be sanitized")
        require(error["storesPrivateData"] is False, "error envelopes must not store private data")
        require(error["safeToShowCaller"] is True, "error envelopes should be caller-safe")

    require(claims["qualityClaimAllowed"] is False, "quality claim must stay blocked")
    require(claims["calibrationClaimAllowed"] is False, "calibration claim must stay blocked")
    require(summary["campaignExplainImplemented"] is True, "campaign explain should be implemented")
    require(summary["pilotTaskCardReady"] is True, "pilot task should be ready")
    require(summary["runbookReady"] is True, "runbook should be ready")
    require(summary["agentAdapterReadbacksImplemented"] is True, "agent adapter readbacks should be implemented")
    require(summary["usageTraceEventsSpecified"] == 10, "campaign usage trace event count drifted")
    require(summary["writesCampaignState"] is False, "explain must not write campaign state")
    for key, value in boundary.items():
        if key == "readOnlyReadback":
            require(value is True, "read-only boundary should be true")
        else:
            require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign explain")


if __name__ == "__main__":
    main()
