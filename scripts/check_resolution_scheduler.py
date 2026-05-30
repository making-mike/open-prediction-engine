#!/usr/bin/env python3
"""Check the local terminal resolution scheduler fixture."""

from __future__ import annotations

from run_resolution_scheduler import run_scheduler


class Args:
    live = False
    watch = False
    execute = False
    workspace = ".ope/live/transit-forward-run"
    run_state: list[str] = []
    campaign = None
    limit = 50
    poll_seconds = 60
    max_ticks = 1
    log_file = ".ope/live/resolution-scheduler/scheduler-runs.jsonl"
    output_format = "jsonl"
    trip_updates = None
    input_protobuf = None
    static_gtfs = None
    download_static_gtfs = False
    timeout = None
    max_bytes = None
    static_gtfs_max_bytes = None


class CampaignArgs(Args):
    campaign = "predictioncampaign-001"


def main() -> None:
    report = run_scheduler(Args())
    if report is None:
        raise AssertionError("scheduler fixture should produce a report")
    if report["schedulerMode"] != "fixture_once":
        raise AssertionError("scheduler fixture should run one offline tick")
    if report["executionMode"] != "dry_run":
        raise AssertionError("scheduler fixture should be dry-run")
    if report["tickCount"] != 1:
        raise AssertionError("scheduler fixture should contain one tick")
    tick = report["ticks"][0]
    if tick["jobSummary"]["pendingDueCount"] != 1:
        raise AssertionError("scheduler fixture should see one due job")
    if tick["tickStatus"] != "due_pending":
        raise AssertionError("scheduler fixture should report due pending without --execute")
    if tick["resolverSummary"]["ranResolver"] or tick["resolverSummary"]["executedCount"]:
        raise AssertionError("scheduler fixture must not run resolver execution")
    if report["executionBoundary"]["hostedSchedulerCreated"] or report["executionBoundary"]["osSchedulerCreated"]:
        raise AssertionError("terminal scheduler must not create hosted or OS schedulers")
    if report["executionBoundary"]["calibrationClaimAllowed"]:
        raise AssertionError("scheduler must keep calibration claims blocked")
    if not any("--output-format jsonl" in warning for warning in report["warnings"]):
        raise AssertionError("scheduler should tell agents how to force machine-readable stdout")

    campaign_report = run_scheduler(CampaignArgs())
    if campaign_report is None:
        raise AssertionError("campaign scheduler fixture should produce a report")
    if campaign_report["schedulerMode"] != "campaign_fixture_once":
        raise AssertionError("campaign scheduler fixture mode drifted")
    campaign_tick = campaign_report["ticks"][0]
    if campaign_tick["jobSummary"]["jobCount"] != 4:
        raise AssertionError("campaign scheduler should include one campaign job")
    if campaign_tick["jobSummary"]["pendingNotDueCount"] != 2:
        raise AssertionError("campaign scheduler should add one waiting campaign job")
    campaign_actions = [
        action for action in campaign_tick["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    if len(campaign_actions) != 1:
        raise AssertionError("campaign scheduler should expose one campaign action")
    if campaign_actions[0]["schedulerAction"] != "wait_until_due":
        raise AssertionError("campaign scheduler should wait for the campaign resolution time")
    if campaign_tick["resolverSummary"]["ranResolver"] or campaign_tick["resolverSummary"]["executedCount"]:
        raise AssertionError("campaign scheduler fixture must not run resolver execution")
    if not any("Campaign-aware scheduler" in warning for warning in campaign_report["warnings"]):
        raise AssertionError("campaign scheduler should document the campaign non-execution boundary")
    print("checked resolution scheduler")


if __name__ == "__main__":
    main()
