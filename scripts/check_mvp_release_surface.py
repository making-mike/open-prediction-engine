#!/usr/bin/env python3
"""Smoke-check the local MVP release surface and claim boundary."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

from generate_release_manifest import build_manifest


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(*args: str) -> dict[str, object]:
    command = [sys.executable, "scripts/ope.py", *args]
    rendered = shlex.join(command)
    started = time.perf_counter()
    print(f"[check_mvp_release_surface] start {rendered}", file=sys.stderr, flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    print(
        (
            f"[check_mvp_release_surface] done exit={result.returncode} "
            f"elapsed={time.perf_counter() - started:.2f}s {rendered}"
        ),
        file=sys.stderr,
        flush=True,
    )
    result.check_returncode()
    return json.loads(result.stdout)


def main() -> None:
    manifest = build_manifest()
    mvp = manifest["mvpLocalRuntime"]
    claim_review = mvp["claimReview"]

    require(mvp["surfaceStatus"] == "local_mvp_fixture_ready", "MVP surface status drifted")
    require(mvp["runtimeMode"] == "local_cli_and_generated_records", "MVP runtime mode drifted")
    require(mvp["runbookPath"] == "spec/mvp-local-runtime.md", "MVP runbook path drifted")
    require("approved_local_folder_runtime" in mvp["supportedSourceInputs"], "MVP should expose the approved local-folder runtime")
    require({item["interface"] for item in mvp["machineInterfaces"]} == {"cli", "agent_call", "mcp_stdio"}, "MVP machine interface coverage drifted")
    require(claim_review["qualityClaimsAllowed"] is False, "MVP must not allow quality claims")
    require(claim_review["liveCalibrationClaimAllowed"] is False, "MVP must not allow live calibration claims")
    require(claim_review["normalChecksUseLiveNetwork"] is False, "MVP release checks must stay offline")
    for non_goal in claim_review["nonGoalRefs"]:
        require(non_goal in manifest["nonGoals"], f"MVP non-goal {non_goal} missing from release manifest")

    local = run_cli("private-setup-orchestrator", "--case", "local_file_confirmed")
    require(local["orchestratorStatus"] == "completed_forecast_readback", "local setup path should complete readback")
    require(local["forecastId"] == "forecast-1102", "local setup path should bind forecast-1102")
    require(local["readbackSummary"]["scoreStatus"] == "scored", "local setup path should expose scored readback")
    require(local["qualityClaimAllowed"] is False, "local setup path must keep quality claim blocked")

    local_runtime = run_cli("local-source-runtime")
    require(local_runtime["summary"]["forecastCardReadyCount"] == 1, "local source runtime should expose one ready card")
    require(local_runtime["forecastCardReadback"]["forecastId"] == "forecast-1102", "local source runtime forecast binding drifted")
    require(local_runtime["summary"]["blockedCount"] == 6, "local source runtime should expose blocked examples")
    require(local_runtime["summary"]["qualityClaimAllowed"] is False, "local source runtime must keep quality claims blocked")

    adoption = run_cli("developer-adoption")
    require(adoption["summary"]["quickstartStepCount"] == 7, "developer adoption quickstart count drifted")
    require(adoption["bindings"]["forecastId"] == "forecast-1102", "developer adoption forecast binding drifted")
    require(adoption["summary"]["qualityClaimAllowed"] is False, "developer adoption must keep quality claims blocked")
    require(adoption["summary"]["generatedTypesIncluded"] is False, "developer adoption should defer generated runtime types")

    pilot_evidence = run_cli("pilot-evidence")
    require(pilot_evidence["summary"]["acceptedRealSessionCount"] == 0, "pilot evidence should not count real sessions yet")
    require(pilot_evidence["summary"]["pilotEvidenceStatus"] == "real_sessions_needed", "pilot evidence should require real sessions")
    require(pilot_evidence["summary"]["expansionEvidenceReady"] is False, "pilot evidence must not unblock expansion")
    require(pilot_evidence["summary"]["qualityClaimAllowed"] is False, "pilot evidence must keep quality claims blocked")

    pilot_session = run_cli("pilot-session-packet")
    require(pilot_session["collectionSummary"]["taskCardCount"] == 6, "pilot session packet should expose six task cards")
    require(pilot_session["collectionSummary"]["realSessionsRecorded"] == 0, "pilot session packet must not record real sessions")
    require(pilot_session["collectionSummary"]["ledgerSubmissionReady"] is True, "pilot session packet should be ledger-submission ready")
    require(pilot_session["collectionSummary"]["expansionEvidenceReady"] is False, "pilot session packet must not unblock expansion")
    require(pilot_session["collectionSummary"]["qualityClaimAllowed"] is False, "pilot session packet must keep quality claims blocked")

    pilot_summary = run_cli("pilot-summary-intake")
    require(pilot_summary["summary"]["acceptedLedgerReadyCount"] == 2, "pilot summary intake should expose two ledger-ready examples")
    require(pilot_summary["summary"]["blockedCaseCount"] == 3, "pilot summary intake should expose blocked examples")
    require(pilot_summary["summary"]["realSessionsRecorded"] == 0, "pilot summary intake must not record real sessions")
    require(pilot_summary["summary"]["ledgerRowsWritten"] == 0, "pilot summary intake must not write ledger rows")
    require(pilot_summary["summary"]["expansionEvidenceReady"] is False, "pilot summary intake must not unblock expansion")
    require(pilot_summary["summary"]["qualityClaimAllowed"] is False, "pilot summary intake must keep quality claims blocked")

    expansion = run_cli("expansion-readiness")
    require(expansion["gateStatus"] == "blocked_pending_evidence", "expansion readiness should remain blocked")
    require(expansion["bindings"]["pilotEvidenceLedgerId"] == "pilotevidenceledger-001", "expansion readiness pilot evidence binding drifted")
    require(expansion["summary"]["readyOptionCount"] == 0, "expansion readiness should not mark options ready")
    require(expansion["summary"]["hostedRuntimeAllowed"] is False, "expansion readiness must block hosted runtime")
    require(expansion["summary"]["qualityClaimAllowed"] is False, "expansion readiness must block quality claims")
    require(expansion["summary"]["generatedTypesIncluded"] is False, "expansion readiness should defer generated runtime types")

    campaign_plan = run_cli("prediction-campaign", "plan")
    require(campaign_plan["planningWindow"]["dryRunPlannerImplemented"] is True, "prediction campaign should expose a dry-run planner")
    require(len(campaign_plan["plannedRuns"]) == 4, "prediction campaign should expose four planned runs")
    require(campaign_plan["plannedRuns"][0]["runId"] == "predictionrun-1301", "prediction campaign run ID drifted")
    require(campaign_plan["plannedRuns"][0]["createsForecastArtifacts"] is False, "prediction campaign must not create artifacts")

    campaign_runner = run_cli("prediction-campaign", "start")
    require(campaign_runner["runnerStatus"] == "dry_run_ready_non_executing", "prediction campaign runner status drifted")
    require(campaign_runner["summary"]["terminalRunnerSurfaceImplemented"] is True, "prediction campaign runner surface should be implemented")
    require(campaign_runner["summary"]["forecastCreationImplemented"] is True, "prediction campaign runner should expose explicit local forecast creation")
    require(campaign_runner["summary"]["preCalibrationImplemented"] is True, "prediction campaign runner should expose pre-calibration")
    require(campaign_runner["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign runner must not write live state")

    campaign_pre_calibration = run_cli("prediction-campaign", "pre-calibration")
    require(campaign_pre_calibration["preCalibrationStatus"] == "ready", "prediction campaign pre-calibration status drifted")
    require(campaign_pre_calibration["calibrationMethod"]["calibratedProbability"] == 0.25, "prediction campaign pre-calibration probability drifted")
    require(campaign_pre_calibration["summary"]["historicalOnly"] is True, "prediction campaign pre-calibration must be historical-only")
    require(campaign_pre_calibration["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign pre-calibration must not write by default")

    campaign_forecast_creation = run_cli("prediction-campaign", "forecast-create")
    require(campaign_forecast_creation["creationStatus"] == "ready_dry_run_creation_request", "prediction campaign forecast creation status drifted")
    require(campaign_forecast_creation["readyRun"]["runId"] == "predictionrun-1301", "prediction campaign forecast creation run drifted")
    require(campaign_forecast_creation["summary"]["effectfulForecastCreationImplemented"] is False, "prediction campaign forecast creation must remain non-effectful")
    require(campaign_forecast_creation["executionBoundary"]["createsForecastArtifacts"] is False, "prediction campaign forecast creation must not create artifacts")

    campaign_forecast_artifact = run_cli("prediction-campaign", "forecast-artifact")
    require(campaign_forecast_artifact["forecastId"] == "forecast-1301", "prediction campaign forecast artifact ID drifted")
    require(campaign_forecast_artifact["questionId"] == "question-1301", "prediction campaign forecast question ID drifted")
    require(campaign_forecast_artifact["questionStatus"] == "open", "prediction campaign forecast should remain unresolved")
    require(
        campaign_forecast_artifact["forecastOutput"] == campaign_forecast_artifact["baselineForecast"],
        "prediction campaign forecast artifact should remain baseline-only",
    )

    campaign_card = run_cli("read", "--record-type", "forecast-card", "--id", "forecast-1301", "--question-id", "question-1301")
    require(campaign_card["record"]["status"] == "open", "prediction campaign forecast card should remain open")
    require(campaign_card["record"]["score"] is None, "prediction campaign forecast card should remain unscored")
    require(campaign_card["record"]["qualityClaim"]["status"] == "unresolved", "prediction campaign forecast card quality boundary drifted")

    campaign_forecast_write = run_cli("prediction-campaign", "forecast-write")
    require(campaign_forecast_write["writeStatus"] == "ready_for_explicit_local_write", "prediction campaign forecast write status drifted")
    require(campaign_forecast_write["bindings"]["forecastId"] == "forecast-1301", "prediction campaign forecast write binding drifted")
    require(campaign_forecast_write["summary"]["effectfulLocalWriteImplemented"] is False, "prediction campaign forecast write should remain a plan")
    require(campaign_forecast_write["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign forecast write must not mutate state")

    campaign_resolution_attempt = run_cli("prediction-campaign", "resolve")
    require(campaign_resolution_attempt["attemptStatus"] == "dry_run_due_ready", "prediction campaign resolution attempt status drifted")
    require(campaign_resolution_attempt["bindings"]["forecastId"] == "forecast-1301", "prediction campaign resolution attempt binding drifted")
    require(campaign_resolution_attempt["attemptResult"]["failureCategory"] == "none", "dry-run resolution attempt should not fail")
    require(campaign_resolution_attempt["executionBoundary"]["executesResolvers"] is False, "resolution attempt must not execute resolvers")

    campaign_resolution_execute = run_cli("prediction-campaign", "resolve", "--run-id", "predictionrun-1301", "--execute-resolvers")
    require(campaign_resolution_execute["attemptStatus"] == "blocked_missing_outcome_source", "explicit resolution attempt status drifted")
    require(campaign_resolution_execute["attemptResult"]["failureCategory"] == "source_unavailable", "explicit resolution attempt failure category drifted")
    require(campaign_resolution_execute["summary"]["resolverExecutionImplemented"] is True, "resolver execution runtime should be implemented")
    require(campaign_resolution_execute["duplicateSafety"]["duplicateScoringBlocked"] is True, "resolution attempt must block duplicate scoring")

    campaign_resolution_source_ready = run_cli(
        "prediction-campaign",
        "resolve",
        "--run-id",
        "predictionrun-1301",
        "--execute-resolvers",
        "--outcome-csv",
        ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv",
    )
    require(
        campaign_resolution_source_ready["attemptStatus"] == "dry_run_execute_ready",
        "declared outcome source should make resolution ready for explicit write",
    )
    require(
        campaign_resolution_source_ready["summary"]["resolutionArtifactsCreated"] is False,
        "source-ready resolution readback must remain non-mutating",
    )

    campaign_resolution_duplicate = run_cli("prediction-campaign", "resolve", "--attempt-case", "blocked_duplicate", "--execute-resolvers")
    require(campaign_resolution_duplicate["attemptStatus"] == "blocked_duplicate_run", "duplicate resolution attempt status drifted")
    require(campaign_resolution_duplicate["attemptResult"]["failureCategory"] == "duplicate_blocked", "duplicate resolution failure category drifted")
    require(campaign_resolution_duplicate["attemptResult"]["scoringRecordsCreated"] is False, "duplicate resolution attempt must not create scoring")

    campaign_doctor = run_cli("prediction-campaign", "doctor")
    require(campaign_doctor["doctorStatus"] == "actionable_due_run", "prediction campaign doctor status drifted")
    require(campaign_doctor["health"]["dueRunCount"] == 1, "prediction campaign doctor should expose one due run")
    require(campaign_doctor["health"]["blockedRunCount"] == 1, "prediction campaign doctor should expose one blocked resolver path")
    require(campaign_doctor["duplicateProtection"]["priorEvidenceOverwriteAllowed"] is False, "doctor must block prior evidence overwrite")
    require(campaign_doctor["summary"]["appendReadyReadbackImplemented"] is True, "doctor should expose append-ready readback")
    require(campaign_doctor["executionBoundary"]["writesIgnoredLiveState"] is False, "doctor must not write ignored state")

    campaign_resume = run_cli("prediction-campaign", "resume")
    require(campaign_resume["resumeStatus"] == "checked_resume_plan_non_mutating", "prediction campaign resume status drifted")
    require(campaign_resume["bindings"]["forecastId"] == "forecast-1301", "prediction campaign resume forecast binding drifted")
    require(campaign_resume["observedState"]["priorEvidenceOverwriteAllowed"] is False, "prediction campaign resume must not allow overwrite")
    require(campaign_resume["summary"]["effectfulResumeImplemented"] is False, "prediction campaign resume must remain non-effectful")
    require(campaign_resume["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign resume must not write live state")

    campaign_resume_state = run_cli("prediction-campaign", "resume", "--resume-case", "interrupted_after_forecast_write", "--view", "state")
    require(campaign_resume_state["sourceKind"] == "simulated_interrupted_campaign_state", "interrupted resume source kind drifted")
    require(campaign_resume_state["localRunStateCount"] == 1, "interrupted resume should find one run state")
    require(campaign_resume_state["priorEvidenceOverwriteAllowed"] is False, "interrupted resume must not allow overwrite")

    campaign_append_ready = run_cli("prediction-campaign", "append-ready")
    require(campaign_append_ready["ledgerStatus"] == "checked_exclusion_append_ready", "append-ready ledger status drifted")
    require(campaign_append_ready["summary"]["excludedRowCount"] == 1, "append-ready should expose one exclusion row")
    require(campaign_append_ready["executionBoundary"]["writesIgnoredLiveState"] is False, "append-ready must stay dry-run")
    campaign_append_summary = run_cli("prediction-campaign", "append", "--ledger-case", "comparable_scored", "--view", "summary")
    require(campaign_append_summary["comparableRowCount"] == 1, "append dry-run should expose one comparable row")
    require(campaign_append_summary["writesIgnoredLiveState"] is False, "append dry-run must not write ignored state")

    adapter = run_cli("private-setup-orchestrator", "--case", "source_adapter_output_accepted")
    require(adapter["orchestratorStatus"] == "ready_for_forecast_execution", "accepted adapter path should stop before forecast execution")
    require(adapter["forecastId"] is None, "accepted adapter path must not invent forecast artifacts")
    require(adapter["nextAction"] == "run_explicit_setup_forecast_execution", "accepted adapter path should route to explicit forecast execution")

    blocked_expectations = {
        "missing_approval": ("missing_approval", "confirm_approval"),
        "unconfirmed_mapping": ("needs_confirmation", "confirm_mapping"),
        "unsafe_source": ("blocked_unsafe", "stop_unsafe_connector"),
        "response_too_large": ("response_too_large", "retry_with_smaller_readback"),
    }
    for case, (status, next_action) in blocked_expectations.items():
        run = run_cli("private-setup-orchestrator", "--case", case)
        require(run["orchestratorStatus"] == status, f"{case} status drifted")
        require(run["nextAction"] == next_action, f"{case} next action drifted")
        require(run["forecastArtifactsPresent"] is False, f"{case} must not create forecast artifacts")
        require(run["forecastId"] is None, f"{case} must not bind a forecast")

    forecast_run = run_cli("forecast-run")
    require(forecast_run["runStatus"] == "completed", "MVP forecast-run should complete")
    require(forecast_run["recordBinding"]["forecastId"] == "forecast-602", "MVP forecast-run forecast binding drifted")
    require(forecast_run["state"]["scoreStatus"] == "scored", "MVP forecast-run should expose scored state")
    require(forecast_run["qualityClaim"]["status"] == "not_enough_resolved_auto_evidence_outcomes", "MVP forecast-run must keep quality provisional")

    envelope = run_cli(
        "agent-call",
        "--operation",
        "forecast_card",
        "--forecast-id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    require(envelope["status"] == "ok", "MVP agent-call forecast card should return ok")
    require(envelope["exitCode"] == 0, "MVP agent-call forecast card should return exit code 0")
    require(envelope["recordBinding"]["forecastId"] == "forecast-1102", "MVP agent-call forecast binding drifted")

    protocol_map = run_cli("agent-protocol-map")
    require(protocol_map["adapterContract"]["mcpCommand"] == "python3 scripts/ope.py mcp-stdio", "MVP MCP command drifted")
    require(protocol_map["adapterContract"]["mcpStdioScaffoldImplemented"] is True, "MVP MCP scaffold should be implemented")
    require(protocol_map["adapterContract"]["httpRuntimeImplemented"] is False, "MVP must not claim HTTP runtime")
    require(protocol_map["adapterContract"]["queueRuntimeImplemented"] is False, "MVP must not claim queue runtime")

    resolution_jobs = run_cli("resolution-jobs")
    require(resolution_jobs["summary"]["pendingDueCount"] == 1, "MVP resolution jobs should expose one due fixture job")
    require(resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "MVP resolution jobs must not execute resolvers")

    campaign_resolution_jobs = run_cli("resolution-jobs", "--campaign", "predictioncampaign-001")
    campaign_jobs = [
        job for job in campaign_resolution_jobs["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    require(campaign_resolution_jobs["registryMode"] == "campaign_fixture_registry", "campaign resolution jobs mode drifted")
    require(len(campaign_jobs) == 1, "campaign resolution jobs should expose one campaign job")
    require(campaign_jobs[0]["target"]["forecastId"] == "forecast-1301", "campaign resolution job forecast binding drifted")
    require(campaign_jobs[0]["agentAction"]["recommendedAction"] == "wait", "campaign resolution job should tell agents to wait")
    require(campaign_resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "campaign resolution jobs must not execute resolvers")

    due_campaign_resolution_jobs = run_cli(
        "resolution-jobs",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_jobs = [
        job for job in due_campaign_resolution_jobs["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    require(due_campaign_jobs[0]["agentAction"]["recommendedAction"] == "call_campaign_resolver_attempt", "due campaign job should route to resolver attempt")
    require(due_campaign_resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "due campaign resolution jobs must not execute resolvers")

    campaign_scheduler = run_cli("resolution-scheduler", "--campaign", "predictioncampaign-001")
    campaign_actions = [
        action for action in campaign_scheduler["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    require(campaign_scheduler["schedulerMode"] == "campaign_fixture_once", "campaign scheduler mode drifted")
    require(len(campaign_actions) == 1, "campaign scheduler should expose one campaign action")
    require(campaign_actions[0]["schedulerAction"] == "wait_until_due", "campaign scheduler should wait until due")
    require(campaign_scheduler["executionMode"] == "dry_run", "campaign scheduler fixture should stay dry-run")
    require(campaign_scheduler["executionBoundary"]["hostedSchedulerCreated"] is False, "campaign scheduler must not create hosted schedulers")

    due_campaign_scheduler = run_cli(
        "resolution-scheduler",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_actions = [
        action for action in due_campaign_scheduler["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    require(due_campaign_actions[0]["schedulerAction"] == "campaign_resolver_attempt_ready", "due campaign scheduler action drifted")
    require(due_campaign_scheduler["ticks"][0]["resolverSummary"]["ranResolver"] is False, "due campaign scheduler must not run resolvers")

    track_gate = run_cli("transit-track-record-gate")
    require(track_gate["claimBoundary"]["qualityClaimAllowed"] is False, "MVP transit gate must block quality claims")
    require(track_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "MVP transit gate must block calibration claims")
    require(track_gate["calibrationGate"]["summaryGenerated"] is False, "MVP transit gate must not generate calibration below threshold")
    campaign_track_gate = run_cli("transit-track-record-gate", "--campaign", "predictioncampaign-001")
    require(campaign_track_gate["campaignLedger"]["included"] is True, "MVP transit gate should include explicit campaign ledger")
    require(campaign_track_gate["sampleSummary"]["excludedSampleSize"] == 7, "campaign ledger should add excluded audit rows")
    campaign_comparable_gate = run_cli(
        "transit-track-record-gate",
        "--campaign",
        "predictioncampaign-001",
        "--ledger-case",
        "comparable_scored",
    )
    require(campaign_comparable_gate["sampleSummary"]["resolvedComparableSampleSize"] == 2, "campaign comparable ledger should add sample")
    require(campaign_comparable_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "campaign ledger must not unlock calibration below threshold")
    campaign_calibration = run_cli("prediction-campaign", "calibration-status")
    require(
        campaign_calibration["calibrationStatus"] == "not_enough_resolved_comparable_outcomes",
        "campaign calibration default should stay below threshold",
    )
    require(campaign_calibration["calibrationReadback"]["summaryGenerated"] is False, "below-threshold calibration must not summarize")
    campaign_restart = run_cli(
        "prediction-campaign",
        "calibration-status",
        "--calibration-case",
        "post_calibration_restart",
        "--view",
        "cycle",
    )
    require(campaign_restart["postCalibrationAction"] == "pause_then_resume_after", "post-calibration restart action drifted")
    require(campaign_restart["writesCampaignState"] is False, "post-calibration restart readback must not mutate state")
    campaign_method_gate = run_cli("prediction-campaign", "method-update-gate")
    require(
        campaign_method_gate["gateStatus"] == "blocked_insufficient_calibration_evidence",
        "campaign method-update gate default should stay below threshold",
    )
    require(
        campaign_method_gate["decision"]["effectfulUpdateAllowedNow"] is False,
        "campaign method-update gate must not allow effectful updates",
    )
    require(
        campaign_method_gate["executionBoundary"]["changesForecastMethod"] is False,
        "campaign method-update gate must not change forecast methods",
    )
    campaign_method_plan = run_cli("prediction-campaign", "method-update-plan")
    require(
        campaign_method_plan["planStatus"] == "blocked_by_method_update_gate",
        "campaign method-update plan default should be gate-blocked",
    )
    require(
        campaign_method_plan["decision"]["effectfulUpdateAllowedNow"] is False,
        "campaign method-update plan must not allow effectful updates",
    )
    require(
        campaign_method_plan["futureEffectfulCommand"]["implementedNow"] is True,
        "campaign method-update plan should expose the guarded effectful command",
    )
    campaign_method_apply = run_cli("prediction-campaign", "apply-method-update")
    require(
        campaign_method_apply["actionStatus"] == "blocked_by_method_update_plan",
        "campaign method-update apply default should be plan-blocked",
    )
    require(
        campaign_method_apply["executionBoundary"]["writesMethodBinding"] is False,
        "campaign method-update apply dry run must not write method bindings",
    )
    campaign_explain = run_cli("prediction-campaign", "explain")
    require(campaign_explain["predictionCampaignExplainId"] == "predictioncampaignexplain-001", "campaign explain ID drifted")
    require(campaign_explain["campaignSnapshot"]["nextForecastId"] == "forecast-1301", "campaign explain next forecast drifted")
    require(campaign_explain["claimBoundary"]["qualityClaimAllowed"] is False, "campaign explain must block quality claims")
    require(campaign_explain["summary"]["agentAdapterReadbacksImplemented"] is True, "campaign explain should expose adapter readbacks")
    campaign_pilot_runbook = run_cli("prediction-campaign", "pilot-runbook")
    require(
        campaign_pilot_runbook["pilotScope"]["targetRunCount"] == 100,
        "campaign pilot runbook target count drifted",
    )
    require(
        campaign_pilot_runbook["miniCampaignSmoke"]["runCount"] == 3,
        "campaign pilot runbook mini smoke count drifted",
    )
    require(
        campaign_pilot_runbook["summary"]["bestAvailableMethodId"] == "transitmethod-100",
        "campaign pilot runbook best method drifted",
    )
    require(
        campaign_pilot_runbook["executionBoundary"]["normalChecksWriteLiveState"] is False,
        "campaign pilot runbook must not write local state",
    )
    campaign_pilot_readiness = run_cli("prediction-campaign", "pilot-readiness")
    require(
        campaign_pilot_readiness["readinessStatus"] == "checked_ready_for_operator_launch",
        "campaign pilot readiness status drifted",
    )
    require(
        campaign_pilot_readiness["summary"]["checkedPrerequisitesPassed"] is True,
        "campaign pilot readiness checked prerequisites should pass",
    )
    require(
        campaign_pilot_readiness["executionBoundary"]["startsPilot"] is False,
        "campaign pilot readiness must not start the pilot",
    )
    campaign_agent = run_cli("agent-call", "--operation", "campaign_status")
    require(campaign_agent["status"] == "ok", "campaign status agent-call should return ok")
    require(campaign_agent["payload"]["campaignSnapshot"]["nextForecastId"] == "forecast-1301", "campaign status agent-call next forecast drifted")
    require(campaign_agent["payload"]["executionBoundary"]["createsForecastArtifacts"] is False, "campaign status agent-call must not create artifacts")

    print("checked MVP release surface")


if __name__ == "__main__":
    main()
