#!/usr/bin/env python3
"""Check prediction campaign runner invariants."""

from __future__ import annotations

from generate_prediction_campaign_runner import build_prediction_campaign_runner, default_args, run_foreground_ticks


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runner = build_prediction_campaign_runner()
    bindings = runner["bindings"]
    command = runner["commandSurface"]
    creation = runner["campaignCreationRequest"]
    forecast_schedule = runner["forecastSchedule"]
    method_binding = runner["methodSelectionBinding"]
    pre_calibration = runner["preCalibration"]
    decisions = runner["runnerDecisions"]
    missed_policy = runner["missedRunPolicy"]
    progress = runner["progress"]
    summary = runner["summary"]
    boundary = runner["executionBoundary"]

    require(runner["runnerStatus"] == "dry_run_ready_non_executing", "runner status drifted")
    require(runner["domain"] == "weather-transit-delays", "runner domain drifted")
    require(bindings["predictionCampaignManifestId"] == "predictioncampaignmanifest-001", "manifest binding drifted")
    require(bindings["repeatingPredictionSetupId"] == "repeatingpredictionsetup-001", "setup binding drifted")
    require(bindings["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(bindings["cycleId"] == "predictioncycle-001", "cycle binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")

    require(command["command"] == "python3 scripts/ope.py prediction-campaign start", "runner command drifted")
    for flag in [
        "--case",
        "--plan-count",
        "--interval",
        "--count",
        "--until",
        "--calibration-target",
        "--post-calibration-action",
        "--live-weather",
        "--execute-resolvers",
        "--pre-calibrate",
        "--history-source",
        "--full-materialization",
        "--watch",
        "--max-ticks",
        "--poll-seconds",
        "--now",
        "--write-local",
        "--output-format",
    ]:
        require(flag in command["flags"], f"{flag} should be exposed")
    require(command["acceptsSetupJson"] is True, "runner should accept setup JSON")
    require(command["acceptsManifestJson"] is True, "runner should accept manifest JSON")
    require(command["requiresExplicitLiveFetchFlag"] is True, "live fetch should require explicit flag")
    require(command["requiresExplicitResolverExecutionFlag"] is True, "resolver execution should require explicit flag")
    require(command["defaultMissedRunPolicy"] == "skip_if_forecast_close_passed", "missed-run policy drifted")

    require(creation["inputMode"] == "default_fixture", "default campaign input mode drifted")
    require(creation["setupJsonPath"] == "none", "default setup JSON path drifted")
    require(creation["manifestJsonPath"] == "none", "default manifest JSON path drifted")
    require(creation["flagOverrides"] == [], "default campaign input should not have flag overrides")
    require(creation["domain"] == "weather-transit-delays", "campaign creation domain drifted")
    require(creation["serviceWindow"] == "morning_peak", "campaign creation service window drifted")
    require(creation["interval"] == "P1D", "campaign creation interval drifted")
    require(creation["targetCount"] == "100", "campaign creation target count drifted")
    require(creation["preCalibrationRequested"] is False, "default pre-calibration request drifted")
    require(
        creation["historySourcePath"] == "spec/fixtures/local-source-files/transit-delay-history.csv",
        "default history source path drifted",
    )
    require(creation["acceptedForDryRun"] is True, "campaign creation input should be accepted for dry-run")
    require(creation["createsCampaignManifest"] is False, "dry-run campaign input must not create a manifest")
    require(creation["writesCampaignState"] is False, "dry-run campaign input must not write state")

    require(forecast_schedule["scheduleMode"] == "foreground_tick_plan", "forecast schedule mode drifted")
    require(forecast_schedule["readyRunId"] == "predictionrun-1301", "forecast schedule ready run drifted")
    require(
        forecast_schedule["creationCommand"] == "python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl",
        "forecast schedule creation command drifted",
    )
    require(forecast_schedule["normalChecksWriteLiveState"] is False, "forecast schedule normal checks must not write state")
    require(forecast_schedule["requiresExplicitWriteLocal"] is True, "forecast schedule should require explicit local write")
    require(forecast_schedule["createsForecastArtifactsInDryRun"] is False, "forecast schedule dry-run must not create forecasts")
    schedule_rows = {item["decisionStatus"]: item for item in forecast_schedule["scheduleRows"]}
    require(schedule_rows["ready_to_create_forecast"]["scheduleAction"] == "create_with_explicit_write_local", "ready schedule action drifted")
    require(schedule_rows["wait_until_create_time"]["scheduleAction"] == "wait_until_forecast_create_at", "wait schedule action drifted")
    require(schedule_rows["skip_missed_close"]["scheduleAction"] == "record_missed_without_forecast", "missed schedule action drifted")
    require(schedule_rows["blocked_duplicate"]["scheduleAction"] == "block_duplicate_without_forecast", "duplicate schedule action drifted")
    for row in forecast_schedule["scheduleRows"]:
        require(row["createsForecastArtifacts"] is False, "forecast schedule rows must not create artifacts")
        require(row["writesCampaignState"] is False, "forecast schedule rows must not write state")

    require(method_binding["bindingStatus"] == "baseline_default_no_local_override", "method binding status drifted")
    require(method_binding["defaultMethodId"] == "transitmethod-100", "default method binding drifted")
    require(method_binding["activeMethodId"] == "transitmethod-100", "active method binding should default to baseline")
    require(method_binding["candidateMethodId"] == "transitmethod-101", "candidate method binding drifted")
    require(
        method_binding["methodBindingPath"]
        == ".ope/live/prediction-campaigns/predictioncampaign-001/method-binding.json",
        "method binding path drifted",
    )
    require(method_binding["requiresApprovedLocalBinding"] is True, "non-baseline methods require approved binding")
    require(method_binding["normalChecksReadLocalBinding"] is False, "normal checks must not read local method binding")
    require(method_binding["normalChecksChangeMethod"] is False, "normal checks must not change method")
    require(method_binding["futureForecastsOnly"] is True, "method binding must be prospective")
    require(
        method_binding["priorForecastHistoryRewriteAllowed"] is False,
        "method binding must not rewrite history",
    )

    require(pre_calibration["requestStatus"] == "not_requested", "default pre-calibration should be off")
    require(pre_calibration["preCalibrationStatus"] == "not_requested", "default pre-calibration status drifted")
    require(pre_calibration["calibratedProbability"] == 0.25, "default pre-calibration probability drifted")
    require(pre_calibration["activeMethodId"] == "transitmethod-100", "pre-calibration method binding drifted")
    require(pre_calibration["localWriteRequiredBeforeUse"] is False, "default pre-calibration should not require write")
    require(pre_calibration["writesDuringDryRun"] is False, "pre-calibration dry-run must not write")
    require(pre_calibration["qualityClaimAllowed"] is False, "pre-calibration must not allow quality claims")

    require(missed_policy["policyName"] == "skip_if_forecast_close_passed", "missed-run policy name drifted")
    require(missed_policy["defaultAction"] == "mark_missed_without_forecast", "missed-run default action drifted")
    require(missed_policy["decisionStatus"] == "skip_missed_close", "missed-run decision status drifted")
    require(missed_policy["recordedRunStatus"] == "missed", "missed-run recorded status drifted")
    require(missed_policy["exclusionReasonCode"] == "missed_forecast_close", "missed-run reason code drifted")
    require(missed_policy["excludedFromComparableEvidence"] is True, "missed runs must be excluded from comparable evidence")
    require(missed_policy["createsForecastArtifacts"] is False, "missed runs must not create forecasts")
    require(missed_policy["createsResolutionArtifacts"] is False, "missed runs must not create resolutions")
    require(missed_policy["createsScoringRecords"] is False, "missed runs must not create scoring records")
    require(missed_policy["appendsCorpusEvidence"] is False, "missed runs must not append corpus evidence")

    modes = {item["mode"]: item for item in runner["supportedRecurrenceModes"]}
    for mode in ["fixed_count", "until_date", "open_ended", "interval", "calibration_threshold", "post_calibration_restart"]:
        require(mode in modes, f"{mode} should be supported by dry-run runner")
        require(modes[mode]["supportedByDryRun"] is True, f"{mode} should be dry-run supported")
        require(modes[mode]["createsForecastArtifacts"] is False, f"{mode} must not create artifacts")

    statuses = {item["decisionStatus"]: item for item in decisions}
    require(set(statuses) == {"ready_to_create_forecast", "wait_until_create_time", "skip_missed_close", "blocked_duplicate"}, "decision coverage drifted")
    require(statuses["ready_to_create_forecast"]["runId"] == "predictionrun-1301", "ready run binding drifted")
    for decision in decisions:
        require(decision["forecastArtifactsCreated"] is False, "dry-run decisions must not create artifacts")
        require(decision["liveFetchRequired"] is False, "dry-run decisions must not require live fetch")
        require(decision["resolverExecutionRequired"] is False, "dry-run decisions must not execute resolvers")
        require(decision["writesLiveState"] is False, "dry-run decisions must not write live state")

    require(runner["outputModes"]["capturedStdoutMode"] == "jsonl", "captured output should be JSONL")
    require(runner["outputModes"]["interactiveTerminalMode"] == "compact_human_status_lines", "interactive output drifted")
    require(progress["plannedRunCount"] == 4, "planned run count drifted")
    require(progress["readyToCreateForecastCount"] == 1, "ready count drifted")
    require(progress["materializedRunCount"] == 4, "materialized run count drifted")
    require(progress["forecastArtifactsCreated"] == 0, "runner must not create forecasts")
    require(progress["resolvedComparableOutcomes"] == 0, "runner must not count outcomes")
    require(progress["nextForecastRunId"] == "predictionrun-1301", "next forecast run drifted")

    require(summary["terminalRunnerSurfaceImplemented"] is True, "terminal runner surface should be implemented")
    require(summary["dryRunOnly"] is True, "runner should remain dry-run only")
    require(summary["forecastCreationImplemented"] is True, "explicit local forecast creation should be implemented")
    require(summary["resolverExecutionImplemented"] is False, "resolver execution must remain unimplemented")
    require(summary["writesLiveState"] is False, "runner summary must not write state")
    require(summary["normalChecksUseLiveNetwork"] is False, "normal checks must stay offline")
    require(summary["preCalibrationImplemented"] is True, "runner should expose pre-calibration")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")

    require(boundary["readOnlyDryRun"] is True, "boundary should remain read-only dry run")
    for key, value in boundary.items():
        if key == "readOnlyDryRun":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    mini_args = default_args()
    mini_args.plan_count = 3
    mini_args.count = 3
    mini_runner = build_prediction_campaign_runner(mini_args)
    mini_statuses = {item["decisionStatus"] for item in mini_runner["runnerDecisions"]}
    require(mini_runner["campaignCreationRequest"]["targetCount"] == "3", "mini runner target count drifted")
    require(mini_runner["progress"]["plannedRunCount"] == 3, "mini runner planned count drifted")
    require(len(mini_runner["forecastSchedule"]["scheduleRows"]) == 3, "mini runner schedule row count drifted")
    require(
        mini_statuses == {"ready_to_create_forecast", "wait_until_create_time", "skip_missed_close"},
        "mini runner decision coverage drifted",
    )

    pre_args = default_args()
    pre_args.pre_calibrate = True
    pre_runner = build_prediction_campaign_runner(pre_args)
    pre = pre_runner["preCalibration"]
    require(pre_runner["campaignCreationRequest"]["preCalibrationRequested"] is True, "pre-calibration flag should be bound")
    require(pre["requestStatus"] == "requested", "pre-calibration request status drifted")
    require(pre["preCalibrationStatus"] == "ready", "pre-calibration should be ready for default history")
    require(pre["resolvedOutcomeRowCount"] == 30, "pre-calibration row count drifted")
    require(pre["calibratedProbability"] == 0.25, "pre-calibration probability drifted")
    require(pre["forecastProbabilitySource"] == "historical_pre_calibration", "pre-calibration source drifted")
    require(pre["localWriteRequiredBeforeUse"] is True, "requested pre-calibration should require local write before use")

    full_args = default_args()
    full_args.full_materialization = True
    full_args.count = 100
    full_args.now = "2026-09-18T00:00:00Z"
    full_runner = build_prediction_campaign_runner(full_args)
    require(full_runner["progress"]["plannedRunCount"] == 100, "full runner planned count drifted")
    require(full_runner["progress"]["materializedRunCount"] == 100, "full runner materialized count drifted")
    require(len(full_runner["runnerDecisions"]) == 100, "full runner should expose 100 clock decisions")
    require(len(full_runner["forecastSchedule"]["scheduleRows"]) == 100, "full runner should expose 100 schedule rows")
    require(full_runner["forecastSchedule"]["readyRunId"] == "predictionrun-1400", "full runner final ready run drifted")
    require(full_runner["progress"]["nextForecastRunId"] == "predictionrun-1400", "full runner next forecast drifted")
    full_tick = run_foreground_ticks(full_runner, full_args)["ticks"][0]
    require(full_tick["readyRunId"] == "predictionrun-1400", "full foreground tick ready run drifted")
    require(len(full_tick["actions"]) == 100, "full foreground tick should inspect 100 actions")
    require(
        full_tick["actions"][-1]["actionStatus"] == "dry_run_ready_for_write_local",
        "full foreground tick should leave the final run ready in dry-run",
    )

    resolver_args = default_args()
    resolver_args.now = "2026-06-11T07:15:00Z"
    resolver_args.max_ticks = 1
    resolver_args.execute_resolvers = True
    resolver_args.write_local = False
    resolver_result = run_foreground_ticks(build_prediction_campaign_runner(resolver_args), resolver_args)
    resolver_tick = resolver_result["ticks"][0]
    require(
        resolver_result["executionMode"] == "explicit_resolver_attempt",
        "explicit resolver foreground mode drifted",
    )
    require(
        resolver_result["summary"]["resolutionAttemptCount"] == 1,
        "foreground runner should call one checked campaign resolution attempt when due",
    )
    require(
        resolver_tick["resolutionAttempts"][0]["attemptStatus"] == "blocked_missing_outcome_source",
        "explicit campaign resolution attempt should block on missing outcome source",
    )
    require(
        resolver_result["executionBoundary"]["executesResolvers"] is False,
        "foreground resolver attempt readback must not execute resolvers yet",
    )

    print("checked prediction campaign runner")


if __name__ == "__main__":
    main()
