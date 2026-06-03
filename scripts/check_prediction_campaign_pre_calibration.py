#!/usr/bin/env python3
"""Check prediction campaign pre-calibration invariants."""

from __future__ import annotations

from generate_prediction_campaign_pre_calibration import (
    MINIMUM_HISTORICAL_ROWS,
    build_prediction_campaign_pre_calibration,
)
from generate_transit_method_options import BASELINE_METHOD_ID


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_prediction_campaign_pre_calibration()
    bindings = record["bindings"]
    source = record["historySource"]
    method = record["calibrationMethod"]
    binding = record["engineBinding"]
    checks = record["preflightChecks"]
    summary = record["summary"]
    boundary = record["executionBoundary"]

    require(record["preCalibrationStatus"] == "ready", "default pre-calibration should be ready")
    require(record["domain"] == "weather-transit-delays", "pre-calibration domain drifted")
    require(bindings["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(bindings["cycleId"] == "predictioncycle-001", "cycle binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")
    require(bindings["methodId"] == BASELINE_METHOD_ID, "pre-calibration must bind baseline method")
    require(bindings["firstPilotRunId"] == "predictionrun-1301", "first pilot run drifted")
    require(bindings["firstPilotServiceDate"] == "2026-06-11", "first pilot date drifted")

    require(source["sourcePath"] == "spec/fixtures/local-source-files/transit-delay-history.csv", "history source drifted")
    require(source["rowCount"] == 30, "history row count drifted")
    require(source["scopedRowCount"] == 30, "scoped history row count drifted")
    require(source["resolvedOutcomeRowCount"] == 30, "resolved history row count drifted")
    require(source["minimumHistoricalRows"] == MINIMUM_HISTORICAL_ROWS, "minimum historical rows drifted")
    require(source["firstHistoricalServiceDate"] == "2026-05-01", "first historical date drifted")
    require(source["lastHistoricalServiceDate"] == "2026-05-30", "last historical date drifted")
    require(source["lastHistoricalServiceDate"] < bindings["firstPilotServiceDate"], "history must end before pilot")
    require(source["leakageCheckStatus"] == "pass", "history leakage check should pass")
    require(len(source["contentHash"]) == 64, "history source hash should be sha256")

    require(method["methodName"] == "historical_frequency_laplace_pre_calibration", "method name drifted")
    require(method["outputType"] == "binary", "pre-calibration output type drifted")
    require(method["positiveOutcomeCount"] == 7, "positive historical outcome count drifted")
    require(method["negativeOutcomeCount"] == 23, "negative historical outcome count drifted")
    require(method["rawEventRate"] == 0.2333333333, "raw event rate drifted")
    require(method["smoothing"] == "laplace_add_one", "smoothing drifted")
    require(method["calibratedProbability"] == 0.25, "calibrated probability drifted")
    require(method["calibrationChangesMethodClass"] is False, "pre-calibration must not change method class")
    require(method["automaticProbabilityUpdateAllowed"] is False, "automatic probability updates must be blocked")

    require(binding["activeMethodId"] == BASELINE_METHOD_ID, "active method drifted")
    require(binding["calibratedProbability"] == method["calibratedProbability"], "binding probability drifted")
    require(
        binding["preCalibrationArtifactPath"]
        == ".ope/live/prediction-campaigns/predictioncampaign-001/pre-calibration/predictioncampaignprecalibration-001.json",
        "pre-calibration target path drifted",
    )
    require(
        binding["methodBindingPath"] == ".ope/live/prediction-campaigns/predictioncampaign-001/method-binding.json",
        "method binding target path drifted",
    )
    require(binding["forecastArtifactCanUseBeforePilot"] is True, "ready binding should be usable before pilot")
    require(binding["normalChecksReadLocalBinding"] is False, "normal checks must not read ignored method binding")
    require(binding["prospectiveOnly"] is True, "pre-calibration must be prospective only")
    require(binding["priorForecastHistoryRewriteAllowed"] is False, "pre-calibration must not rewrite history")
    require(binding["changesForecastMethod"] is False, "pre-calibration must not change method")

    require(len(checks) == 4, "pre-calibration check count drifted")
    for check in checks:
        require(check["checkStatus"] == "pass", "default pre-calibration checks should pass")
        require(check["blocksWrite"] is False, "default pre-calibration checks should not block write")
        require(check["requiredBeforeWrite"] is True, "pre-calibration checks should be required")

    require(record["writePlan"]["requiresWriteLocal"] is True, "pre-calibration should require explicit local write")
    require(record["writePlan"]["writeLocalRequested"] is False, "normal pre-calibration readback must not request write")
    require(record["writeResult"]["writeStatus"] == "not_run", "default pre-calibration must not write")
    require(record["writeResult"]["artifactWrites"] == [], "default pre-calibration must not write artifacts")
    require(record["writeResult"]["stateWrites"] == [], "default pre-calibration must not write state")

    require(summary["preCalibrationImplemented"] is True, "pre-calibration should be implemented")
    require(summary["historicalOnly"] is True, "pre-calibration must be historical-only")
    require(summary["localWriteEligible"] is True, "default pre-calibration should be write eligible")
    require(summary["calibratedProbability"] == 0.25, "summary probability drifted")
    require(summary["writesMethodBinding"] is False, "normal checks must not write method binding")
    require(summary["changesForecastMethod"] is False, "pre-calibration must keep baseline method")
    require(summary["qualityClaimAllowed"] is False, "pre-calibration must not allow quality claims")

    require(boundary["readsHistoricalSource"] is True, "pre-calibration should read historical source")
    require(boundary["readsIgnoredLiveState"] is False, "pre-calibration must not read ignored live state")
    for key, value in boundary.items():
        if key == "readsHistoricalSource":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign pre-calibration")


if __name__ == "__main__":
    main()
