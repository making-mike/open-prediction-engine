#!/usr/bin/env python3
"""Check Helsinki traffic pilot runbook invariants."""

from __future__ import annotations

from generate_helsinki_traffic_pilot_runbook import build_helsinki_traffic_pilot_runbook


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_helsinki_traffic_pilot_runbook()
    scope = record["pilotScope"]
    operator = record["operatorStatus"]
    smoke = record["miniCampaignSmoke"]
    summary = record["summary"]
    boundary = record["executionBoundary"]

    require(record["runbookStatus"] == "checked_local_pilot_operations_runbook", "runbook status drifted")
    require(record["domain"] == "weather-transit-delays", "runbook domain drifted")
    require(record["bindings"]["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(record["bindings"]["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")
    require(
        record["bindings"]["predictionCampaignPreCalibrationId"] == "predictioncampaignprecalibration-001",
        "pre-calibration binding drifted",
    )

    require(scope["geography"] == "helsinki", "pilot geography drifted")
    require(scope["network"] == "hsl-surface", "pilot network drifted")
    require(scope["targetRunCount"] == 100, "target run count drifted")
    require(scope["miniSmokeRunCount"] == 3, "mini smoke run count drifted")
    require(scope["bestAvailableMethodId"] == "transitmethod-100", "best available method drifted")
    require(
        scope["optionalPreCalibrationCommand"] == "python3 scripts/ope.py prediction-campaign pre-calibration",
        "optional pre-calibration command drifted",
    )
    require("--pre-calibrate" in scope["launchWithPreCalibrationCommand"], "launch command must request pre-calibration")
    require(scope["normalChecksUseLiveNetwork"] is False, "normal checks must not use live network")
    require(scope["normalChecksWriteLocalState"] is False, "normal checks must not write local state")

    command_keys = {item["commandKey"] for item in operator["statusCommands"]}
    require(
        command_keys
        == {
            "next_forecast",
            "next_resolution",
            "due_resolver_jobs",
            "append_readiness",
            "ledger_counts",
            "exclusion_rate",
            "calibration_threshold_progress",
        },
        "operator status command coverage drifted",
    )
    require(operator["nextForecastRunId"] == "predictionrun-1301", "next forecast run drifted")
    require(operator["nextResolutionRunId"] == "predictionrun-1301", "next resolution run drifted")
    require(operator["calibrationThreshold"] == 100, "calibration threshold drifted")
    require(operator["calibrationComparableCount"] == 1, "checked comparable count drifted")
    require(operator["calibrationProgressPercent"] == 1.0, "calibration progress drifted")
    require(operator["exclusionRate"] == 0.875, "exclusion rate drifted")

    require(smoke["smokeStatus"] == "checked_three_run_smoke_ready", "smoke status drifted")
    require(smoke["runCount"] == 3, "smoke run count drifted")
    require(smoke["targetRunCount"] == 3, "smoke target count drifted")
    require(
        smoke["expectedRunIds"] == ["predictionrun-1301", "predictionrun-1302", "predictionrun-1303"],
        "smoke expected run ids drifted",
    )
    smoke_command_keys = {item["commandKey"] for item in smoke["commands"]}
    require(
        smoke_command_keys
        == {
            "mini_plan",
            "mini_runner_schedule",
            "mini_foreground_tick",
            "mini_resolution_queue",
            "mini_append_readiness",
        },
        "mini smoke command coverage drifted",
    )
    require(len(smoke["checks"]) == 5, "mini smoke check count drifted")
    require(smoke["normalChecksMutateState"] is False, "mini smoke must not mutate state")

    phases = {item["phase"] for item in record["runbookSteps"]}
    step_by_key = {item["stepKey"]: item for item in record["runbookSteps"]}
    for phase in ["setup", "smoke", "forecast", "monitor", "resolve", "append", "calibrate", "recover", "stop"]:
        require(phase in phases, f"missing runbook phase {phase}")
    require("review_pre_calibration" in step_by_key, "missing pre-calibration review step")
    require(
        step_by_key["review_pre_calibration"]["command"] == "python3 scripts/ope.py prediction-campaign pre-calibration",
        "pre-calibration review command drifted",
    )
    require(step_by_key["review_pre_calibration"]["mutatesState"] is False, "pre-calibration review must be read-only")
    require("--pre-calibrate" in step_by_key["create_next_forecast"]["command"], "forecast launch must pre-calibrate")
    require(any(item["mutatesState"] for item in record["runbookSteps"]), "runbook should identify effectful steps")
    require(len(record["successCriteria"]) == 6, "success criteria count drifted")
    require(len(record["abortCriteria"]) == 6, "abort criteria count drifted")
    require(
        {item["criterionKey"] for item in record["successCriteria"]}
        >= {
            "hundred_comparable_outcomes",
            "acceptable_exclusion_rate",
            "forecast_before_close",
            "no_duplicate_forecasts",
            "complete_provenance",
            "baseline_until_gate",
        },
        "success criteria coverage drifted",
    )
    require(
        {item["criterionKey"] for item in record["abortCriteria"]}
        >= {
            "source_outage",
            "unsafe_evidence",
            "clock_drift",
            "path_safety_failure",
            "duplicate_or_overwrite_attempt",
            "repeated_missed_windows",
        },
        "abort criteria coverage drifted",
    )

    require(summary["runbookReady"] is True, "runbook should be ready")
    require(summary["miniCampaignSmokeReady"] is True, "mini smoke should be ready")
    require(summary["operatorStatusReady"] is True, "operator status should be ready")
    require(summary["bestAvailableMethodId"] == "transitmethod-100", "summary best method drifted")
    require(summary["optionalPreCalibrationAvailable"] is True, "optional pre-calibration should be ready")
    require(summary["optionalPreCalibrationStatus"] == "ready", "optional pre-calibration status drifted")
    require(summary["qualityClaimAllowed"] is False, "quality claim must stay blocked")
    require(summary["calibrationClaimAllowed"] is False, "calibration claim must stay blocked")

    require(boundary["readOnlyRunbook"] is True, "runbook boundary should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyRunbook":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked Helsinki traffic pilot runbook")


if __name__ == "__main__":
    main()
