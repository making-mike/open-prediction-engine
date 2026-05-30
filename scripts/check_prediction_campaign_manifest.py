#!/usr/bin/env python3
"""Check prediction campaign manifest invariants."""

from __future__ import annotations

from datetime import datetime
from pathlib import PurePosixPath

from generate_prediction_campaign_manifest import (
    RUN_STATUSES,
    build_prediction_campaign_manifest,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def require_local_live_path(path: str) -> None:
    parsed = PurePosixPath(path)
    require(not parsed.is_absolute(), f"{path} should be relative")
    require(".." not in parsed.parts, f"{path} should not traverse parent directories")
    require(
        path.startswith(".ope/live/prediction-campaigns/"),
        f"{path} should stay under the ignored prediction campaign workspace",
    )


def main() -> None:
    manifest = build_prediction_campaign_manifest()
    bindings = manifest["bindings"]
    local_state = manifest["localStatePolicy"]
    campaign = manifest["campaign"]
    planning = manifest["planningWindow"]
    planned_runs = manifest["plannedRuns"]
    progress = manifest["progress"]
    summary = manifest["summary"]
    boundary = manifest["executionBoundary"]

    require(manifest["manifestStatus"] == "planned_dry_run_non_executing", "manifest status drifted")
    require(manifest["domain"] == "weather-transit-delays", "domain drifted")
    require(bindings["repeatingPredictionSetupId"] == "repeatingpredictionsetup-001", "setup binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")
    require(campaign["campaignId"] == "predictioncampaign-001", "campaign id drifted")
    require(campaign["cycleId"] == "predictioncycle-001", "cycle id drifted")
    require(campaign["recurrenceCaseKey"] == "daily_100_run_transit_calibration", "case binding drifted")
    require(campaign["runnerImplemented"] is False, "runner must remain unimplemented")

    require(local_state["workspaceRoot"] == ".ope/live/prediction-campaigns", "workspace root drifted")
    require(local_state["gitIgnored"] is True, "campaign workspace should remain ignored")
    require(local_state["normalChecksWriteLiveState"] is False, "normal checks must not write live campaign state")
    require(local_state["credentialsStored"] is False, "campaign manifest must not store credentials")
    require(local_state["privateRowsStored"] is False, "campaign manifest must not store private rows")
    require_local_live_path(local_state["campaignStatePath"])
    require_local_live_path(campaign["campaignStatePath"])

    require(planning["dryRunPlannerImplemented"] is True, "dry-run planner should be implemented")
    require(planning["nextCandidateCount"] == 4, "planned candidate count drifted")
    require(planning["statusesHandled"] == RUN_STATUSES, "handled statuses drifted")
    for status in ["skipped", "missed", "canceled", "failed", "manually_stopped", "blocked_duplicate"]:
        require(status in planning["statusesHandled"], f"{status} status should be handled")

    run_ids = {item["runId"] for item in planned_runs}
    question_ids = {item["questionId"] for item in planned_runs}
    forecast_ids = {item["forecastId"] for item in planned_runs}
    resolution_ids = {item["resolutionId"] for item in planned_runs}
    scoring_ids = {item["scoringReportId"] for item in planned_runs}
    duplicate_keys = {item["duplicateKey"] for item in planned_runs}
    require(len(run_ids) == len(planned_runs), "run IDs must be unique")
    require(len(question_ids) == len(planned_runs), "question IDs must be unique")
    require(len(forecast_ids) == len(planned_runs), "forecast IDs must be unique")
    require(len(resolution_ids) == len(planned_runs), "resolution IDs must be unique")
    require(len(scoring_ids) == len(planned_runs), "scoring IDs must be unique")
    require(len(duplicate_keys) == len(planned_runs), "duplicate keys should be unique in the fixture plan")
    require("forecast-1102" not in forecast_ids, "campaign forecasts must not reuse fixture forecast IDs")

    for index, run in enumerate(planned_runs, start=1):
        require(run["sequenceNumber"] == index, "run sequence drifted")
        require(run["cycleId"] == campaign["cycleId"], "run cycle binding drifted")
        require(run["sourcePolicyId"] == bindings["sourcePolicyId"], "run source policy binding drifted")
        require(run["runStatus"] == "planned_forecast_pending", "fixture runs should start pending")
        require(run["createsForecastArtifacts"] is False, "dry-run planned runs must not create forecasts")
        require(run["fetchesLiveData"] is False, "dry-run planned runs must not fetch live data")
        require(run["mutatesCampaignState"] is False, "dry-run planned runs must not mutate state")
        require_local_live_path(run["plannedStatePath"])
        require(parse_utc(run["forecastCloseAt"]) < parse_utc(run["horizonStartsAt"]), "forecast must close before horizon")
        require(parse_utc(run["horizonEndsAt"]) < parse_utc(run["resolutionEligibleAt"]), "resolution must wait for horizon end")

    status_examples = {item["runStatus"]: item for item in manifest["statusExamples"]}
    require(set(status_examples) == set(RUN_STATUSES), "status example coverage drifted")
    for status, example in status_examples.items():
        require(example["createsForecastArtifacts"] is False, f"{status} example must not create artifacts")
        require(example["mutatesCampaignState"] is False, f"{status} example must not mutate campaign state")

    require(progress["plannedRunCount"] == len(planned_runs), "progress planned count drifted")
    require(progress["forecastArtifactsCreated"] == 0, "dry-run manifest must not create forecast artifacts")
    require(progress["resolvedComparableOutcomes"] == 0, "dry-run manifest must not count outcomes")
    require(progress["nextForecastRunId"] == planned_runs[0]["runId"], "next forecast run drifted")
    require(progress["nextResolutionRunId"] == "none", "dry-run manifest should not have resolution due")

    require(summary["campaignManifestImplemented"] is True, "campaign manifest should be implemented")
    require(summary["dryRunPlannerImplemented"] is True, "dry-run planner summary drifted")
    require(summary["runnerImplemented"] is False, "runner summary must remain false")
    require(summary["uniqueRunIdsMinted"] is True, "unique run IDs should be minted")
    require(summary["duplicatePreventionEnabled"] is True, "duplicate prevention should be enabled")
    require(summary["mutatesLiveState"] is False, "summary must not mutate live state")
    require(summary["normalChecksUseLiveNetwork"] is False, "normal checks must stay offline")
    require(summary["qualityClaimAllowed"] is False, "quality claims must remain blocked")

    require(boundary["readOnlyDryRun"] is True, "boundary should remain read-only dry run")
    for key, value in boundary.items():
        if key == "readOnlyDryRun":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign manifest")


if __name__ == "__main__":
    main()
