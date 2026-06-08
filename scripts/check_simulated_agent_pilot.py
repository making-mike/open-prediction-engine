#!/usr/bin/env python3
"""Check user-authorized simulated agent pilot sessions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_simulated_agent_pilot import build_simulated_agent_pilot, validate_simulated_agent_pilot
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("simulated agent pilot generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
USER_PROMPT = (
    "I need to know which buses in Helsinki will be late tomorrow and by late i mean 2+ minutes at the stop. "
    "We can provide data about planned work."
)
EXPECTED_CASES = {"accepted", "needs_clarification", "blocked", "rejected", "response_too_large"}
NON_HELSINKI_DOMAINS = {"retail_stockout", "sla_breach", "seaport_berth_availability"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_simulated_agent_pilot()
    validate_simulated_agent_pilot(record)

    require(record["simulatedAgentPilotId"] == "simulatedagentpilot-001", "simulated pilot id drifted")
    require(record["simulationStatus"] == "checked_agent_only_simulation", "simulation status drifted")
    require(record["userProvidedPrompt"] == USER_PROMPT, "user prompt fixture drifted")
    require(record["normalizedCurrentDate"] == "2026-06-05", "current date normalization drifted")
    require(record["normalizedTomorrowDate"] == "2026-06-06", "tomorrow normalization drifted")
    require(record["summary"]["simulatedSessionCount"] == 8, "simulation should cover eight sessions")
    require(record["summary"]["userPromptSessionCount"] == 1, "simulation should include one user prompt")
    require(record["summary"]["generatedPromptSessionCount"] == 7, "simulation should include seven generated prompts")
    require(record["summary"]["nonHelsinkiSessionCount"] == 3, "simulation should include three non-Helsinki sessions")
    require(record["summary"]["setupEngineFirstCount"] >= 4, "simulation should measure setup-engine-first behavior")
    require(record["summary"]["parallelRiskEngineProposalCount"] == 1, "simulation should retain one parallel risk-engine confusion signal")
    require(record["summary"]["auditLayerConfusionCount"] == 1, "simulation should retain one audit-layer confusion signal")
    require(record["summary"]["engineSetupComprehensionReady"] is True, "simulated setup comprehension should be ready")
    require(record["summary"]["caseCoverage"] == sorted(EXPECTED_CASES), "case coverage drifted")
    require(record["summary"]["timeMeasurementMode"] == "deterministic_estimate", "time mode drifted")
    require(record["summary"]["tokenCountMode"] == "approximate_whitespace_tokens", "token count mode drifted")
    require(record["summary"]["realSessionsRecorded"] == 0, "simulated pilot must not count real sessions")
    require(record["summary"]["pilotEvidenceReady"] is False, "simulated pilot must not unblock real pilot evidence")
    require(record["summary"]["qualityClaimAllowed"] is False, "simulated pilot must not allow quality claims")
    require(record["summary"]["hostedRuntimeAllowed"] is False, "simulated pilot must not allow hosted runtime")

    sessions = record["simulatedSessions"]
    require(len(sessions) == 8, "session count drifted")
    require({session["expectedCase"] for session in sessions} == EXPECTED_CASES, "session expected case coverage drifted")
    require(sessions[0]["prompt"] == USER_PROMPT, "first session should use the user prompt")
    require(sessions[0]["expectedCase"] == "needs_clarification", "user prompt should need clarification")
    require(sessions[0]["normalizedHorizonDate"] == "2026-06-06", "user prompt horizon should normalize tomorrow")
    require(
        {session["domainContext"] for session in sessions if session["domainContext"] != "helsinki_transit"}
        == NON_HELSINKI_DOMAINS,
        "simulation should cover non-Helsinki setup contexts",
    )

    total_prompt_tokens = 0
    total_response_tokens = 0
    for session in sessions:
        require(session["promptApproxTokens"] > 0, f"{session['sessionId']} prompt tokens missing")
        require(session["responseApproxTokens"] > 0, f"{session['sessionId']} response tokens missing")
        require(
            session["totalApproxTokens"] == session["promptApproxTokens"] + session["responseApproxTokens"],
            f"{session['sessionId']} total token count drifted",
        )
        require(session["elapsedMsEstimate"] >= 1, f"{session['sessionId']} elapsed estimate missing")
        require(session["opeResponse"]["caseKey"] == session["expectedCase"], f"{session['sessionId']} OPE case drifted")
        require(session["opeResponse"]["decision"] == session["decision"], f"{session['sessionId']} decision drifted")
        require(
            session["setupEngineCommand"].startswith("python3 scripts/ope.py setup-engine --goal "),
            f"{session['sessionId']} should expose setup-engine command",
        )
        require(
            session["setupComprehension"]["usesSetupEngineBeforeCustomEngine"] is True
            or session["setupComprehension"]["confusionSignal"] in {"parallel_risk_engine_first", "audit_layer_only"},
            f"{session['sessionId']} should either use setup-engine first or record a comprehension confusion signal",
        )
        require(
            session["setupComprehension"]["customRiskEngineProposedBeforeOpe"] is False
            or session["setupComprehension"]["confusionSignal"] == "parallel_risk_engine_first",
            f"{session['sessionId']} custom engine confusion should be explicit",
        )
        require(
            session["setupComprehension"]["auditLayerOnlyDescription"] is False
            or session["setupComprehension"]["confusionSignal"] == "audit_layer_only",
            f"{session['sessionId']} audit-layer confusion should be explicit",
        )
        require(session["storesRawPromptAsPilotEvidence"] is False, f"{session['sessionId']} stores raw prompt evidence")
        require(session["storesRawPrivateRows"] is False, f"{session['sessionId']} stores raw private rows")
        require(session["storesCredentialValues"] is False, f"{session['sessionId']} stores credential values")
        total_prompt_tokens += session["promptApproxTokens"]
        total_response_tokens += session["responseApproxTokens"]

    require(record["summary"]["totalPromptApproxTokens"] == total_prompt_tokens, "prompt token summary drifted")
    require(record["summary"]["totalResponseApproxTokens"] == total_response_tokens, "response token summary drifted")
    require(
        record["summary"]["totalApproxTokens"] == total_prompt_tokens + total_response_tokens,
        "total token summary drifted",
    )

    for case in EXPECTED_CASES:
        cli_case = subprocess.run(
            [sys.executable, "scripts/ope.py", "prediction-feature-setup", "--view", "response", "--case", case],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        require(cli_case.returncode == 0, f"prediction-feature-setup case {case} failed: {cli_case.stderr}")
        payload = json.loads(cli_case.stdout)
        require(payload["caseKey"] == case, f"prediction-feature-setup case {case} payload drifted")

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "simulated-agent-pilot", "--section", "summary"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"simulated-agent-pilot CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["simulatedSessionCount"] == 8, "simulated-agent-pilot CLI summary drifted")
    require(payload["nonHelsinkiSessionCount"] == 3, "simulated-agent-pilot CLI non-Helsinki count drifted")
    require(payload["engineSetupComprehensionReady"] is True, "simulated-agent-pilot CLI setup comprehension drifted")
    require(payload["realSessionsRecorded"] == 0, "simulated-agent-pilot CLI must not count real sessions")

    print("checked simulated agent pilot")


if __name__ == "__main__":
    main()
