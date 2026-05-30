#!/usr/bin/env python3
"""Check prediction campaign forecast-creation handoff invariants."""

from __future__ import annotations

from generate_prediction_campaign_forecast_creation import build_prediction_campaign_forecast_creation


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    creation = build_prediction_campaign_forecast_creation()
    bindings = creation["bindings"]
    ready_run = creation["readyRun"]
    checks = creation["readinessChecks"]
    artifact_plan = creation["artifactPlan"]
    command = creation["commandSurface"]
    summary = creation["summary"]
    boundary = creation["executionBoundary"]

    require(creation["creationStatus"] == "ready_dry_run_creation_request", "creation status drifted")
    require(creation["domain"] == "weather-transit-delays", "creation domain drifted")
    require(bindings["predictionCampaignManifestId"] == "predictioncampaignmanifest-001", "manifest binding drifted")
    require(bindings["predictionCampaignRunnerId"] == "predictioncampaignrunner-001", "runner binding drifted")
    require(bindings["runId"] == "predictionrun-1301", "run binding drifted")
    require(bindings["runnerDecisionId"] == "predictionrunnerdecision-001", "runner decision binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")

    require(ready_run["runId"] == "predictionrun-1301", "ready run ID drifted")
    require(ready_run["questionId"] == "question-1301", "ready question ID drifted")
    require(ready_run["forecastId"] == "forecast-1301", "ready forecast ID drifted")
    require(ready_run["runStatus"] == "planned_forecast_pending", "ready run status drifted")
    require(ready_run["runnerDecisionStatus"] == "ready_to_create_forecast", "runner decision status drifted")
    require("weather-transit-delays" in ready_run["duplicateKey"], "duplicate key should bind domain")

    require(len(checks) == 6, "readiness check count drifted")
    for check in checks:
        require(check["checkStatus"] == "pass", "dry-run readiness checks should pass")
        require(check["blocksCreation"] is False, "dry-run readiness checks should not block the ready run")
    required_checks = [check for check in checks if check["requiredBeforeCreation"]]
    require(len(required_checks) == 5, "required readiness check count drifted")

    require(artifact_plan["questionId"] == ready_run["questionId"], "artifact question binding drifted")
    require(artifact_plan["forecastId"] == ready_run["forecastId"], "artifact forecast binding drifted")
    require(artifact_plan["forecastArtifactPath"].endswith("/forecast-1301.json"), "forecast artifact path drifted")
    require(artifact_plan["writesCheckedFixtures"] is False, "forecast creation must not write checked fixtures")
    require(artifact_plan["writesIgnoredLiveState"] is False, "forecast creation must not write live state")
    require(artifact_plan["createsForecastArtifacts"] is False, "forecast creation must not create artifacts yet")

    require(command["command"] == "python3 scripts/ope.py prediction-campaign forecast-create", "command drifted")
    for flag in ["--run-id", "--manifest-json", "--setup-json", "--live-weather", "--output-format"]:
        require(flag in command["acceptedFlags"], f"{flag} should be accepted by the forecast creation surface")
    require(command["defaultMode"] == "dry_run_readback", "default mode drifted")
    require(command["capturedStdoutMode"] == "json", "captured output mode drifted")
    require(command["explicitExecutionRequired"] is True, "effectful execution must remain explicit")

    require(summary["forecastCreationReadbackImplemented"] is True, "forecast creation readback should be implemented")
    require(summary["effectfulForecastCreationImplemented"] is False, "effectful forecast creation should remain unimplemented")
    require(summary["readyRunCount"] == 1, "ready run count drifted")
    require(summary["blockedRunCount"] == 0, "blocked run count drifted")
    require(summary["artifactCreationAllowedInNormalChecks"] is False, "normal checks must not create artifacts")
    require(summary["normalChecksUseLiveNetwork"] is False, "normal checks must stay offline")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")

    require(boundary["readOnlyPlanning"] is True, "boundary should remain read-only planning")
    for key, value in boundary.items():
        if key == "readOnlyPlanning":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign forecast creation")


if __name__ == "__main__":
    main()
