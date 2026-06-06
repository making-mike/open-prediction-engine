#!/usr/bin/env python3
"""Check agent guidance loop milestones."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_agent_guidance import build_agent_guidance, validate_agent_guidance
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("agent guidance generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CASES = {"accepted", "needs_clarification", "blocked", "rejected", "response_too_large"}
EXPECTED_MILESTONES = ["142", "143", "144", "145"]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_agent_guidance()
    validate_agent_guidance(record)

    require(record["agentGuidanceId"] == "agentguidance-001", "agent guidance id drifted")
    require(record["guidanceStatus"] == "checked_agent_guidance_loop", "agent guidance status drifted")
    require(record["implementedMilestones"] == EXPECTED_MILESTONES, "implemented milestone coverage drifted")
    require(record["summary"]["guidanceCaseCount"] == 5, "guidance should expose five cases")
    require(record["summary"]["promptPlannerReady"] is True, "prompt planner should be ready")
    require(record["summary"]["helsinkiNarrowingFlowReady"] is True, "Helsinki narrowing flow should be ready")
    require(record["summary"]["instructionPackReady"] is True, "instruction pack should be ready")
    require(record["summary"]["realSessionsRecorded"] == 0, "agent guidance must not count real sessions")
    require(record["summary"]["forecastArtifactsCreated"] is False, "agent guidance must not create forecast artifacts")
    require(record["summary"]["qualityClaimAllowed"] is False, "agent guidance must not allow quality claims")

    cases = {case["caseKey"]: case for case in record["guidanceCases"]}
    require(set(cases) == EXPECTED_CASES, "guidance case coverage drifted")
    accepted = cases["accepted"]
    require(accepted["agentNextMove"] == "read_forecast_card", "accepted case should route to forecast card")
    require(accepted["safeCommands"][0].endswith("--case accepted"), "accepted case command drifted")
    require(accepted["forecastId"] == "forecast-1102", "accepted case forecast id drifted")

    clarify = cases["needs_clarification"]
    require(clarify["agentNextMove"] == "ask_user", "clarification case should ask the user")
    require(clarify["normalizedHorizonDate"] == "2026-06-06", "Helsinki prompt should normalize tomorrow")
    require(len(clarify["questionsToAsk"]) == 4, "Helsinki clarification should ask four focused questions")
    question_text = " ".join(clarify["questionsToAsk"]).lower()
    for phrase in ["route", "stop", "time window", "planned-work", "outcome source"]:
        require(phrase in question_text, f"clarification questions should mention {phrase}")
    require("planned_work" in clarify["requiredSourceRoles"], "planned work role should be required")
    require("transit_delay_outcome" in clarify["requiredSourceRoles"], "outcome role should be required")

    blocked = cases["blocked"]
    require(blocked["agentNextMove"] == "replace_unsafe_inputs", "blocked case next move drifted")
    require("raw_credential_value" in blocked["reasonCodes"], "blocked case should include credential blocker")
    require(blocked["safeCommands"] == [], "blocked case must not expose execution commands")

    rejected = cases["rejected"]
    require(rejected["agentNextMove"] == "rewrite_as_future_contract", "rejected case next move drifted")
    require("unresolvable_outcome" in rejected["reasonCodes"], "rejected case reason coverage drifted")

    too_large = cases["response_too_large"]
    require(too_large["agentNextMove"] == "narrow_scope_or_raise_budget", "too-large next move drifted")
    require("response_size_budget_exceeded" in too_large["reasonCodes"], "too-large reason code drifted")

    planner = record["promptPlanner"]
    require(planner["plannerStatus"] == "checked_prompt_to_question_planner", "planner status drifted")
    require(planner["plannerInput"]["rawPromptAllowed"] is True, "planner should accept a bounded raw prompt")
    require(planner["plannerInput"]["credentialValuesAllowed"] is False, "planner must reject credentials")
    require(planner["plannerOutput"]["questionCount"] == 4, "planner should expose four questions")
    require(planner["plannerOutput"]["agentNextMove"] == "ask_user", "planner next move drifted")

    helsinki = record["helsinkiNarrowingFlow"]
    require(helsinki["flowStatus"] == "checked_narrowing_flow", "Helsinki narrowing status drifted")
    require(helsinki["broadPromptCase"] == "needs_clarification", "broad prompt should need clarification")
    require(helsinki["readyAfterClarificationCase"] == "accepted", "clarified prompt should route accepted")
    require(len(helsinki["narrowingQuestions"]) == 4, "Helsinki flow should expose four narrowing questions")
    require(
        helsinki["safeNextCommands"][-1].endswith("--case accepted"),
        "Helsinki flow should end with accepted setup command",
    )

    pack = record["agentInstructionPack"]
    require(pack["packStatus"] == "checked_agent_instruction_pack", "instruction pack status drifted")
    require(len(pack["doRules"]) >= 5, "instruction pack should expose do rules")
    require(len(pack["doNotRules"]) >= 5, "instruction pack should expose do-not rules")
    require(pack["minimumAgentLoop"][0]["stepKey"] == "classify_prompt", "agent loop should start with classification")
    require(pack["minimumAgentLoop"][-1]["stepKey"] == "read_or_stop", "agent loop should end with read-or-stop")

    for key, value in record["executionBoundary"].items():
        if key in {"agentUsesOwnIntelligence", "normalChecksAreReadOnly"}:
            require(value is True, f"{key} should stay true")
        else:
            require(value is False, f"{key} should stay false")

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "agent-guide", "--section", "summary"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"agent-guide summary CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["guidanceCaseCount"] == 5, "agent-guide summary count drifted")
    require(payload["instructionPackReady"] is True, "agent-guide summary instruction pack drifted")

    user_prompt_cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "agent-guide", "--case", "needs_clarification"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(user_prompt_cli.returncode == 0, f"agent-guide case CLI failed: {user_prompt_cli.stderr or user_prompt_cli.stdout}")
    user_payload = json.loads(user_prompt_cli.stdout)
    require(user_payload["agentNextMove"] == "ask_user", "agent-guide user prompt case drifted")
    require(user_payload["normalizedHorizonDate"] == "2026-06-06", "agent-guide user prompt date drifted")

    print("checked agent guidance loop")


if __name__ == "__main__":
    main()
