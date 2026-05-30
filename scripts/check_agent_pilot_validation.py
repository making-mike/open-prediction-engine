#!/usr/bin/env python3
"""Check agent pilot validation pack invariants."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from generate_agent_pilot_validation import CASE_ORDER, build_agent_pilot_validation


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
    pack = build_agent_pilot_validation()
    scenarios = {scenario["scenarioKey"]: scenario for scenario in pack["taskScenarios"]}

    require(list(scenarios) == CASE_ORDER, "pilot scenarios should stay in the intended task order")
    require(pack["pilotProtocol"]["minimumSessions"] == 3, "pilot should require at least three sessions")
    require(pack["pilotProtocol"]["targetSessions"] == 5, "pilot target should remain five sessions")
    require(pack["successMetrics"]["minimumTaskCompletionRate"] == 0.8, "task completion threshold drifted")
    require(pack["successMetrics"]["minimumMedianTrustScore"] == 4, "trust threshold drifted")
    require(pack["successMetrics"]["minimumClaimBoundaryMedianScore"] == 4, "claim-boundary threshold drifted")

    protocol_boundary = pack["pilotProtocol"]["privacyBoundary"]
    for key in ("storesRawTranscripts", "storesPrivateData", "storesCredentials", "storesPromptLogs"):
        require(protocol_boundary[key] is False, f"privacy boundary {key} should remain false")
    require(protocol_boundary["requiresSanitizedSummaries"] is True, "pilot should require sanitized summaries")
    require(protocol_boundary["usesSyntheticExamplesOnly"] is True, "checked examples should remain synthetic")

    execution_boundary = pack["executionBoundary"]
    for key, value in execution_boundary.items():
        if key in {"usesExistingCheckedFixturesOnly", "storesSyntheticExamplesOnly"}:
            require(value is True, f"execution boundary {key} should remain true")
        else:
            require(value is False, f"execution boundary {key} should remain false")

    dimension_ids = {dimension["dimensionId"] for dimension in pack["feedbackSchema"]["dimensions"]}
    for scenario in scenarios.values():
        for dimension in scenario["measures"]:
            require(dimension in dimension_ids, f"task measure {dimension} missing from feedback schema")

    surfaces = {item["surface"] for item in pack["comprehensionRubric"]}
    require(surfaces == {"forecast_card", "lifecycle_bundle", "source_intake", "blocked_path", "claim_boundary"}, "rubric coverage drifted")

    for summary in pack["examplePilotSummaries"]:
        require(summary["isSyntheticExample"] is True, "example summaries should remain synthetic")
        require(summary["rawTranscriptStored"] is False, "raw transcripts must not be stored")
        require(summary["privateDataStored"] is False, "private data must not be stored")
        rating_ids = {rating["dimensionId"] for rating in summary["ratings"]}
        require(rating_ids <= dimension_ids, "example summary rating references unknown dimension")

    local = run_cli("private-setup-orchestrator", "--case", "local_file_confirmed")
    require(local["orchestratorStatus"] == "completed_forecast_readback", "local-file pilot task status drifted")
    require(local["forecastId"] == "forecast-1102", "local-file pilot task forecast binding drifted")
    require(local["qualityClaimAllowed"] is False, "local-file pilot task must keep quality claim blocked")

    accepted = run_cli("private-setup-orchestrator", "--case", "source_adapter_output_accepted")
    require(accepted["orchestratorStatus"] == "ready_for_forecast_execution", "accepted adapter pilot status drifted")
    require(accepted["forecastId"] is None, "accepted adapter pilot task should not bind a forecast")
    require(accepted["nextAction"] == "run_explicit_setup_forecast_execution", "accepted adapter pilot next action drifted")

    unsafe = run_cli("private-setup-orchestrator", "--case", "unsafe_source")
    require(unsafe["orchestratorStatus"] == "blocked_unsafe", "unsafe pilot task status drifted")
    require(unsafe["forecastArtifactsPresent"] is False, "unsafe pilot task must not create forecast artifacts")
    require(unsafe["nextAction"] == "stop_unsafe_connector", "unsafe pilot task next action drifted")

    forecast_run = run_cli("forecast-run")
    require(forecast_run["runStatus"] == "completed", "forecast-run pilot task should complete")
    require(forecast_run["recordBinding"]["forecastId"] == "forecast-602", "forecast-run pilot binding drifted")
    require(forecast_run["qualityClaim"]["status"] == "not_enough_resolved_auto_evidence_outcomes", "forecast-run pilot must remain provisional")

    claim_gate = run_cli("transit-track-record-gate")
    require(claim_gate["claimBoundary"]["qualityClaimAllowed"] is False, "claim-gate pilot task must block quality claims")
    require(claim_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "claim-gate pilot task must block calibration claims")

    print("checked agent pilot validation pack")


if __name__ == "__main__":
    main()
