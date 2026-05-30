#!/usr/bin/env python3
"""Check prediction campaign runner invariants."""

from __future__ import annotations

from generate_prediction_campaign_runner import build_prediction_campaign_runner


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runner = build_prediction_campaign_runner()
    bindings = runner["bindings"]
    command = runner["commandSurface"]
    decisions = runner["runnerDecisions"]
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
        "--interval",
        "--count",
        "--until",
        "--calibration-target",
        "--post-calibration-action",
        "--live-weather",
        "--execute-resolvers",
        "--output-format",
    ]:
        require(flag in command["flags"], f"{flag} should be exposed")
    require(command["acceptsSetupJson"] is True, "runner should accept setup JSON")
    require(command["acceptsManifestJson"] is True, "runner should accept manifest JSON")
    require(command["requiresExplicitLiveFetchFlag"] is True, "live fetch should require explicit flag")
    require(command["requiresExplicitResolverExecutionFlag"] is True, "resolver execution should require explicit flag")
    require(command["defaultMissedRunPolicy"] == "skip_if_forecast_close_passed", "missed-run policy drifted")

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
    require(progress["forecastArtifactsCreated"] == 0, "runner must not create forecasts")
    require(progress["resolvedComparableOutcomes"] == 0, "runner must not count outcomes")
    require(progress["nextForecastRunId"] == "predictionrun-1301", "next forecast run drifted")

    require(summary["terminalRunnerSurfaceImplemented"] is True, "terminal runner surface should be implemented")
    require(summary["dryRunOnly"] is True, "runner should remain dry-run only")
    require(summary["forecastCreationImplemented"] is False, "forecast creation must remain unimplemented")
    require(summary["resolverExecutionImplemented"] is False, "resolver execution must remain unimplemented")
    require(summary["writesLiveState"] is False, "runner summary must not write state")
    require(summary["normalChecksUseLiveNetwork"] is False, "normal checks must stay offline")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")

    require(boundary["readOnlyDryRun"] is True, "boundary should remain read-only dry run")
    for key, value in boundary.items():
        if key == "readOnlyDryRun":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign runner")


if __name__ == "__main__":
    main()
