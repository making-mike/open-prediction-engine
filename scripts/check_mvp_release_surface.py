#!/usr/bin/env python3
"""Smoke-check the local MVP release surface and claim boundary."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from generate_release_manifest import build_manifest


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(*args: str) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
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
    require(adoption["summary"]["quickstartStepCount"] == 6, "developer adoption quickstart count drifted")
    require(adoption["bindings"]["forecastId"] == "forecast-1102", "developer adoption forecast binding drifted")
    require(adoption["summary"]["qualityClaimAllowed"] is False, "developer adoption must keep quality claims blocked")
    require(adoption["summary"]["generatedTypesIncluded"] is False, "developer adoption should defer generated runtime types")

    pilot_evidence = run_cli("pilot-evidence")
    require(pilot_evidence["summary"]["acceptedRealSessionCount"] == 0, "pilot evidence should not count real sessions yet")
    require(pilot_evidence["summary"]["pilotEvidenceStatus"] == "real_sessions_needed", "pilot evidence should require real sessions")
    require(pilot_evidence["summary"]["expansionEvidenceReady"] is False, "pilot evidence must not unblock expansion")
    require(pilot_evidence["summary"]["qualityClaimAllowed"] is False, "pilot evidence must keep quality claims blocked")

    pilot_session = run_cli("pilot-session-packet")
    require(pilot_session["collectionSummary"]["taskCardCount"] == 5, "pilot session packet should expose five task cards")
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

    track_gate = run_cli("transit-track-record-gate")
    require(track_gate["claimBoundary"]["qualityClaimAllowed"] is False, "MVP transit gate must block quality claims")
    require(track_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "MVP transit gate must block calibration claims")
    require(track_gate["calibrationGate"]["summaryGenerated"] is False, "MVP transit gate must not generate calibration below threshold")

    print("checked MVP release surface")


if __name__ == "__main__":
    main()
