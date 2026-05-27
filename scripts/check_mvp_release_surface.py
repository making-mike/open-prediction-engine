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
