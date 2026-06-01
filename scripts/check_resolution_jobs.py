#!/usr/bin/env python3
"""Check the agent-facing resolution job registry."""

from __future__ import annotations

from generate_resolution_jobs import build_registry


class Args:
    live = False
    workspace = ".ope/live/transit-forward-run"
    run_state: list[str] = []
    campaign = None
    now = None
    limit = 50


class CampaignArgs(Args):
    campaign = "predictioncampaign-001"


class DueCampaignArgs(CampaignArgs):
    now = "2026-06-11T07:15:00Z"


def main() -> None:
    registry = build_registry(Args())
    summary = registry["summary"]
    jobs = {job["jobStatus"]: job for job in registry["jobs"]}
    if registry["registryMode"] != "fixture_registry":
        raise AssertionError("resolution job registry should default to fixture mode")
    if summary["jobCount"] != 3:
        raise AssertionError("resolution job registry should expose three fixture jobs")
    if summary["pendingDueCount"] != 1 or summary["pendingNotDueCount"] != 1:
        raise AssertionError("resolution job registry should expose due and not-due pending jobs")
    if summary["alreadyResolvedCount"] != 1:
        raise AssertionError("resolution job registry should expose one already-resolved job")
    if jobs["pending_due"]["agentAction"]["recommendedAction"] != "call_resolver_execute":
        raise AssertionError("due resolution job should route agents to resolver execution")
    if jobs["pending_not_due"]["agentAction"]["recommendedAction"] != "wait":
        raise AssertionError("not-due resolution job should tell agents to wait")
    if registry["executionBoundary"]["registryExecutesResolvers"]:
        raise AssertionError("resolution job registry must not execute resolver commands")
    if registry["executionBoundary"]["calibrationClaimAllowed"]:
        raise AssertionError("resolution job registry must keep calibration claims blocked")

    campaign_registry = build_registry(CampaignArgs())
    campaign_summary = campaign_registry["summary"]
    campaign_jobs = [
        job for job in campaign_registry["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    if campaign_registry["registryMode"] != "campaign_fixture_registry":
        raise AssertionError("campaign-aware resolution jobs should use campaign fixture mode")
    if campaign_registry["sourceBinding"]["sourceKind"] != "forward_run_state_and_campaign_manifest":
        raise AssertionError("campaign-aware resolution jobs should bind the campaign manifest")
    if campaign_summary["jobCount"] != 4:
        raise AssertionError("campaign-aware resolution jobs should include the campaign forecast")
    if campaign_summary["pendingNotDueCount"] != 2:
        raise AssertionError("campaign-aware resolution jobs should add one waiting campaign job")
    if len(campaign_jobs) != 1:
        raise AssertionError("campaign-aware resolution jobs should expose exactly one campaign job")
    campaign_job = campaign_jobs[0]
    if campaign_job["target"]["campaignRunId"] != "predictionrun-1301":
        raise AssertionError("campaign resolution job run binding drifted")
    if campaign_job["target"]["forecastId"] != "forecast-1301":
        raise AssertionError("campaign resolution job forecast binding drifted")
    if campaign_job["jobStatus"] != "pending_not_due":
        raise AssertionError("campaign resolution job should not be due in the checked fixture")
    if campaign_job["agentAction"]["recommendedAction"] != "wait":
        raise AssertionError("campaign resolution job should tell agents to wait")
    if campaign_job["claimBoundary"]["createsResolutionArtifacts"]:
        raise AssertionError("campaign resolution job must not create resolution artifacts")

    due_campaign_registry = build_registry(DueCampaignArgs())
    due_campaign_jobs = [
        job for job in due_campaign_registry["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    if len(due_campaign_jobs) != 1:
        raise AssertionError("due campaign registry should expose exactly one campaign job")
    due_campaign_job = due_campaign_jobs[0]
    if due_campaign_job["jobStatus"] != "pending_due":
        raise AssertionError("due campaign resolution job should be pending due")
    if due_campaign_job["agentAction"]["recommendedAction"] != "call_campaign_resolver_attempt":
        raise AssertionError("due campaign job should route agents to the checked campaign resolver attempt")
    if "prediction-campaign resolve --run-id predictionrun-1301" not in " ".join(due_campaign_job["agentAction"]["commands"]):
        raise AssertionError("due campaign job should include the resolution-attempt command")
    if due_campaign_job["claimBoundary"]["createsResolutionArtifacts"]:
        raise AssertionError("due campaign resolution job must stay non-mutating")
    print("checked resolution jobs")


if __name__ == "__main__":
    main()
