#!/usr/bin/env python3
"""Generate or check the agent guidance loop readback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_pilot_findings import build_pilot_findings
from generate_prediction_feature_setup import build_prediction_feature_setup, response_by_case
from generate_simulated_agent_pilot import build_simulated_agent_pilot
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-guidance"
OUTPUT_PATH = GENERATED / "ope-agent-guidance.generated.json"
SCHEMA = SPEC / "agent-guidance.schema.json"
GENERATED_AT = "2026-06-06T10:20:00Z"
IMPLEMENTED_MILESTONES = ["142", "143", "144", "145"]
CASE_KEYS = ["accepted", "needs_clarification", "blocked", "rejected", "response_too_large"]
USER_PROMPT = (
    "I need to know which buses in Helsinki will be late tomorrow and by late i mean 2+ minutes at the stop. "
    "We can provide data about planned work."
)
HELSINKI_QUESTIONS = [
    "Which route, stop, or bounded service area should this cover?",
    "What time window on 2026-06-06 should count for the 2+ minute lateness threshold?",
    "Which approved planned-work source reference can OPE use?",
    "Which outcome source will confirm whether each scoped bus was 2+ minutes late?",
]
HELSINKI_SOURCE_ROLES = [
    "planned_work",
    "schedule",
    "historical_delay_baseline",
    "transit_delay_outcome",
]


class AgentGuidanceError(Exception):
    pass


def command_for_case(case_key: str) -> str:
    return f"python3 scripts/ope.py prediction-feature-setup --view response --case {case_key}"


def simulated_session_by_case(simulated: dict[str, Any], case_key: str) -> dict[str, Any]:
    for session in simulated["simulatedSessions"]:
        if session["expectedCase"] == case_key:
            return session
    raise AgentGuidanceError(f"missing simulated session for {case_key}")


def guidance_case(
    index: int,
    case_key: str,
    response: dict[str, Any],
    session: dict[str, Any],
) -> dict[str, Any]:
    next_moves = {
        "accepted": "read_forecast_card",
        "needs_clarification": "ask_user",
        "blocked": "replace_unsafe_inputs",
        "rejected": "rewrite_as_future_contract",
        "response_too_large": "narrow_scope_or_raise_budget",
    }
    explanations = {
        "accepted": "The caller supplied enough approved source context to read the existing forecast card and lifecycle bundle.",
        "needs_clarification": "The prompt is forecast-shaped, but the agent must narrow scope and source references before retrying.",
        "blocked": "The prompt includes unsafe input handling; the agent must replace raw values with approved references.",
        "rejected": "The prompt is not a measurable future forecast contract and should be rewritten before OPE routing.",
        "response_too_large": "The requested readback is too broad for compact agent context; the agent should narrow scope or raise the approved budget.",
    }
    questions = HELSINKI_QUESTIONS if case_key == "needs_clarification" else []
    required_roles = HELSINKI_SOURCE_ROLES if case_key == "needs_clarification" else response["requiredSourceRoles"]
    safe_commands: list[str] = []
    if case_key == "accepted":
        safe_commands = [
            command_for_case("accepted"),
            response["forecastCardCommand"],
            response["lifecycleBundleCommand"],
        ]
    elif case_key == "needs_clarification":
        safe_commands = [command_for_case("needs_clarification")]
    elif case_key == "response_too_large":
        safe_commands = [command_for_case("response_too_large")]
    return {
        "guidanceCaseId": f"agentguidancecase-{index:03d}",
        "caseKey": case_key,
        "classification": response["decision"],
        "agentNextMove": next_moves[case_key],
        "sourcePrompt": session["prompt"],
        "normalizedHorizonDate": session["normalizedHorizonDate"],
        "reasonCodes": response["reasonCodes"],
        "requiredSourceRoles": required_roles,
        "questionsToAsk": questions,
        "safeCommands": [command for command in safe_commands if command],
        "forecastId": response["forecastId"] or "",
        "questionId": response["questionId"] or "",
        "explanation": explanations[case_key],
        "createsForecastArtifacts": False,
        "storesCredentialValues": False,
        "storesRawPrivateRows": False,
        "executesSources": False,
        "qualityClaimAllowed": False,
    }


def build_guidance_cases(
    prediction_feature_setup: dict[str, Any],
    simulated: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        guidance_case(
            index,
            case_key,
            response_by_case(prediction_feature_setup, case_key),
            simulated_session_by_case(simulated, case_key),
        )
        for index, case_key in enumerate(CASE_KEYS, start=1)
    ]


def build_prompt_planner() -> dict[str, Any]:
    return {
        "plannerId": "agentplanner-001",
        "plannerStatus": "checked_prompt_to_question_planner",
        "plannerInput": {
            "rawPromptAllowed": True,
            "maxPromptChars": 600,
            "credentialValuesAllowed": False,
            "rawPrivateRowsAllowed": False,
            "rawSqlAllowed": False,
        },
        "plannerOutput": {
            "agentNextMove": "ask_user",
            "questionCount": len(HELSINKI_QUESTIONS),
            "questionsToAsk": HELSINKI_QUESTIONS,
            "requiredSourceRoles": HELSINKI_SOURCE_ROLES,
            "safeRetryCommand": command_for_case("needs_clarification"),
        },
    }


def build_helsinki_narrowing_flow() -> dict[str, Any]:
    return {
        "flowId": "helsinkinarrowingflow-001",
        "flowStatus": "checked_narrowing_flow",
        "broadPrompt": USER_PROMPT,
        "normalizedHorizonDate": "2026-06-06",
        "broadPromptCase": "needs_clarification",
        "narrowingQuestions": HELSINKI_QUESTIONS,
        "clarifiedPromptExample": (
            "Forecast whether route 550 buses at stop HSL-1234 will be 2+ minutes late during the 2026-06-06 "
            "morning peak, using approved planned_work_ref, schedule_ref, historical_delay_baseline_ref, and "
            "transit_delay_outcome_ref."
        ),
        "readyAfterClarificationCase": "accepted",
        "safeNextCommands": [
            "python3 scripts/ope.py agent-guide --case needs_clarification",
            command_for_case("needs_clarification"),
            command_for_case("accepted"),
        ],
    }


def build_instruction_pack() -> dict[str, Any]:
    return {
        "packId": "agentinstructionpack-001",
        "packStatus": "checked_agent_instruction_pack",
        "doRules": [
            "Classify the developer prompt before trying to forecast.",
            "Ask focused questions when OPE returns needs_clarification.",
            "Use approved source references rather than raw private payloads.",
            "Read forecast cards and lifecycle bundles instead of inventing forecast summaries.",
            "Carry OPE's claim boundaries into user-facing copy.",
        ],
        "doNotRules": [
            "Do not paste credential values into OPE requests.",
            "Do not pass raw private rows or raw SQL as source context.",
            "Do not treat post-outcome evidence as forecast-time evidence.",
            "Do not claim hosted runtime or production quality from local fixtures.",
            "Do not answer oversized readbacks by dumping broad matrices into agent context.",
        ],
        "minimumAgentLoop": [
            {
                "stepKey": "classify_prompt",
                "instruction": "Call the guidance surface or prediction-feature setup response before deciding what to do.",
                "safeCommand": "python3 scripts/ope.py agent-guide --section summary",
            },
            {
                "stepKey": "ask_or_block",
                "instruction": "If the case needs clarification, ask the returned questions; if blocked, replace unsafe inputs.",
                "safeCommand": "python3 scripts/ope.py agent-guide --case needs_clarification",
            },
            {
                "stepKey": "retry_with_refs",
                "instruction": "After the caller provides scoped answers and approved source refs, retry the compact setup path.",
                "safeCommand": command_for_case("accepted"),
            },
            {
                "stepKey": "read_or_stop",
                "instruction": "Read the forecast card when accepted; otherwise stop at the returned boundary and next action.",
                "safeCommand": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            },
        ],
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "agentUsesOwnIntelligence": True,
        "normalChecksAreReadOnly": True,
        "createsForecastArtifacts": False,
        "executesSources": False,
        "fetchesLiveData": False,
        "storesCredentialValues": False,
        "storesRawPrivateRows": False,
        "acceptsRawSql": False,
        "qualityClaimsUpgraded": False,
        "hostedRuntimeImplemented": False,
    }


def build_agent_guidance() -> dict[str, Any]:
    prediction_feature_setup = build_prediction_feature_setup()
    simulated = build_simulated_agent_pilot()
    pilot_findings = build_pilot_findings()
    guidance_cases = build_guidance_cases(prediction_feature_setup, simulated)
    return {
        "agentGuidanceId": "agentguidance-001",
        "generatedAt": GENERATED_AT,
        "guidanceStatus": "checked_agent_guidance_loop",
        "implementedMilestones": IMPLEMENTED_MILESTONES,
        "sourceRecords": {
            "predictionFeatureSetupId": prediction_feature_setup["predictionFeatureSetupId"],
            "simulatedAgentPilotId": simulated["simulatedAgentPilotId"],
            "pilotFindingsId": pilot_findings["pilotFindingsId"],
        },
        "guidanceCases": guidance_cases,
        "promptPlanner": build_prompt_planner(),
        "helsinkiNarrowingFlow": build_helsinki_narrowing_flow(),
        "agentInstructionPack": build_instruction_pack(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "guidanceCaseCount": len(guidance_cases),
            "implementedMilestoneCount": len(IMPLEMENTED_MILESTONES),
            "promptPlannerReady": True,
            "helsinkiNarrowingFlowReady": True,
            "instructionPackReady": True,
            "realSessionsRecorded": 0,
            "forecastArtifactsCreated": False,
            "qualityClaimAllowed": False,
            "hostedRuntimeImplemented": False,
        },
    }


def validate_agent_guidance(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise AgentGuidanceError(f"agent guidance validation failed: {errors[0]}")


def case_payload(record: dict[str, Any], case_key: str) -> dict[str, Any]:
    for item in record["guidanceCases"]:
        if item["caseKey"] == case_key:
            return item
    raise AgentGuidanceError(f"unsupported guidance case {case_key}")


def view_payload(record: dict[str, Any], section: str | None, case_key: str) -> Any:
    if case_key:
        return case_payload(record, case_key)
    if section == "summary":
        return record["summary"]
    if section == "cases":
        return record["guidanceCases"]
    if section == "planner":
        return record["promptPlanner"]
    if section == "helsinki":
        return record["helsinkiNarrowingFlow"]
    if section == "instructions":
        return record["agentInstructionPack"]
    if section == "boundary":
        return record["executionBoundary"]
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated agent guidance fixture")
    parser.add_argument("--check", action="store_true", help="check generated agent guidance fixture")
    parser.add_argument(
        "--section",
        choices=["summary", "cases", "planner", "helsinki", "instructions", "boundary"],
        help="print one agent guidance section",
    )
    parser.add_argument("--case", choices=CASE_KEYS, help="print one guidance case")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_agent_guidance()
    validate_agent_guidance(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="agent guidance",
            regen="python3 scripts/generate_agent_guidance.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="agent guidance",
            regen="python3 scripts/generate_agent_guidance.py --write",
        )
        return
    print(render_json(view_payload(record, args.section, args.case or "")), end="")


if __name__ == "__main__":
    main()
