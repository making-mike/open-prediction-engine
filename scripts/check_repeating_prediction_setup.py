#!/usr/bin/env python3
"""Check repeating prediction setup contract invariants."""

from __future__ import annotations

from generate_repeating_prediction_setup import (
    EXAMPLE_ORDER,
    POST_CALIBRATION_ACTIONS,
    SCHEDULE_POLICY_ORDER,
    build_repeating_prediction_setup,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    setup = build_repeating_prediction_setup()
    bindings = setup["bindings"]
    schedules = {item["policyKind"]: item for item in setup["supportedSchedulePolicies"]}
    examples = {item["caseKey"]: item for item in setup["campaignExamples"]}
    post_actions = {item["action"]: item for item in setup["postCalibrationPolicies"]}
    requirements = {item["requirementKey"]: item for item in setup["contractRequirements"]}
    summary = setup["summary"]
    boundary = setup["executionBoundary"]

    require(setup["setupStatus"] == "contract_ready_non_executing", "setup status drifted")
    require(setup["domain"] == "weather-transit-delays", "reference domain drifted")
    require(bindings["domainSetupId"] == "domainsetup-003", "domain setup binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")
    require(bindings["transitMethodOptionsId"] == "transitmethodoptions-001", "method options binding drifted")
    require(
        bindings["transitBaselineTrackRecordGateId"] == "transitbaselinetrackrecordgate-001",
        "track-record gate binding drifted",
    )
    require(
        bindings["transitLiveEvidencePromotionId"] == "transitliveevidencepromotion-001",
        "live evidence promotion binding drifted",
    )

    require([item["policyKind"] for item in setup["supportedSchedulePolicies"]] == SCHEDULE_POLICY_ORDER, "schedule policy order drifted")
    require([item["caseKey"] for item in setup["campaignExamples"]] == EXAMPLE_ORDER, "example order drifted")
    require([item["action"] for item in setup["postCalibrationPolicies"]] == POST_CALIBRATION_ACTIONS, "post-calibration action order drifted")

    require("PT1H" in schedules["interval"]["durationExamples"], "interval policy should support hourly runs")
    require("PT6H" in schedules["interval"]["durationExamples"], "interval policy should support multi-hour runs")
    require("P1D" in schedules["interval"]["durationExamples"], "interval policy should support daily runs")
    require("P1W" in schedules["interval"]["durationExamples"], "interval policy should support weekly runs")
    require(
        "calibration_threshold" in schedules["open_ended"]["endConditionKinds"],
        "open-ended policy should allow calibration thresholds",
    )

    daily = examples["daily_100_run_transit_calibration"]
    require(daily["schedulePolicy"]["targetCount"] == 100, "daily calibration target count drifted")
    require(daily["schedulePolicy"]["interval"] == "P1D", "daily calibration interval drifted")
    require(daily["endConditions"][0]["conditionKind"] == "fixed_count", "daily calibration should be count-bounded")

    hourly = examples["hourly_short_horizon_count"]
    require(hourly["schedulePolicy"]["interval"] == "PT1H", "hourly interval drifted")
    require(hourly["schedulePolicy"]["targetCount"] == 24, "hourly target count drifted")

    weekly = examples["weekly_until_date_campaign"]
    require(weekly["schedulePolicy"]["policyKind"] == "until_date", "weekly example should be until-date")
    require(weekly["schedulePolicy"]["interval"] == "P1W", "weekly interval drifted")
    require(weekly["endConditions"][0]["conditionKind"] == "until_date", "weekly end condition drifted")

    weekday = examples["weekday_peak_window_campaign"]
    require(
        weekday["schedulePolicy"]["selectedWeekdays"] == ["monday", "tuesday", "wednesday", "thursday", "friday"],
        "weekday selection drifted",
    )
    require("morning_peak" in weekday["schedulePolicy"]["selectedWindows"], "weekday window drifted")

    restart = examples["post_calibration_restart_campaign"]
    require(restart["schedulePolicy"]["thresholdValue"] == 100, "calibration threshold value drifted")
    require(
        restart["postCalibrationPolicy"]["action"] == "pause_then_resume_after",
        "post-calibration restart action drifted",
    )
    require(post_actions["pause_then_resume_after"]["delay"] == "P14D", "pause-then-resume delay drifted")
    require(post_actions["start_next_cycle_after"]["delay"] == "P30D", "start-next-cycle delay drifted")

    for example in setup["campaignExamples"]:
        require(example["createsForecastArtifacts"] is False, "examples must not create forecast artifacts")
        require(example["mutatesCampaignState"] is False, "examples must not mutate campaign state")
        require("forecast_before_close" in example["requiredRunBoundaries"], "example missing forecast-before-close boundary")
        require("resolve_after_horizon" in example["requiredRunBoundaries"], "example missing resolve-after-horizon boundary")
        require(
            "resolution_only_evidence_excluded_from_forecast_inputs" in example["requiredRunBoundaries"],
            "example missing resolution-only evidence boundary",
        )

    require(requirements["source_policy_binding"]["enforcedByCurrentContract"] is True, "source policy requirement should be enforced")
    require(summary["supportedSchedulePolicyCount"] == 6, "schedule policy count drifted")
    require(summary["campaignExampleCount"] == 6, "campaign example count drifted")
    require(summary["postCalibrationActionCount"] == 4, "post-calibration action count drifted")
    require(summary["finiteCampaignSupported"] is True, "finite campaigns should be supported by contract")
    require(summary["untilDateCampaignSupported"] is True, "until-date campaigns should be supported by contract")
    require(summary["openEndedCampaignSupported"] is True, "open-ended campaigns should be supported by contract")
    require(summary["calibrationThresholdSupported"] is True, "calibration threshold should be supported by contract")
    require(summary["runnerImplemented"] is False, "runner must remain unimplemented in this milestone")
    require(summary["campaignManifestImplemented"] is False, "campaign manifest must remain unimplemented in this milestone")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")

    require(boundary["readOnlyContract"] is True, "contract should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyContract":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked repeating prediction setup")


if __name__ == "__main__":
    main()
