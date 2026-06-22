#!/usr/bin/env python3
"""Generate or check the supervised pilot session brief."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-session-brief"
OUTPUT_PATH = GENERATED / "ope-pilot-session-brief.generated.json"
SCHEMA = SPEC / "pilot-session-brief.schema.json"
RECOMMENDED_SCENARIO_KEY = "engine_setup_shortcut_comprehension"
PACKET_PATH = ROOT / "spec" / "fixtures" / "generated" / "pilot-session-packet" / "ope-pilot-session-packet.generated.json"
AGENT_GUIDANCE_PATH = ROOT / "spec" / "fixtures" / "generated" / "agent-guidance" / "ope-agent-guidance.generated.json"
SUMMARY_TEMPLATE_PATH = ROOT / "spec" / "fixtures" / "generated" / "pilot-summary-template" / "ope-pilot-summary-template.generated.json"
SUPERVISION_STATUS_PATH = ROOT / "spec" / "fixtures" / "generated" / "pilot-supervision-status" / "ope-pilot-supervision-status.generated.json"
GENERATED_AT = "2026-06-11T09:00:00Z"
SECTION_NAMES = [
    "summary",
    "task",
    "guidance",
    "preflight",
    "participant",
    "runbook",
    "draft",
    "commands",
    "safety",
    "boundary",
    "warnings",
]


class PilotSessionBriefError(Exception):
    pass


def load_generated_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError as exc:
        raise PilotSessionBriefError(f"missing generated dependency: {path}") from exc
    if not isinstance(payload, dict):
        raise PilotSessionBriefError(f"generated dependency is not an object: {path}")
    return payload


def find_task(packet: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    for task in packet["taskCards"]:
        if task["scenarioKey"] == scenario_key:
            return task
    raise PilotSessionBriefError(f"missing pilot session task {scenario_key}")


def recommended_task(task: dict[str, Any], supervision: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": task["taskId"],
        "scenarioKey": task["scenarioKey"],
        "title": task["title"],
        "command": supervision["recommendedNextTask"]["command"],
        "taskCommand": task["command"],
        "expectedOutcomeClass": task["expectedOutcomeClass"],
        "measures": task["measures"],
        "claimBoundaryRequired": task["ledgerMapping"]["claimBoundaryRequired"],
    }


def generic_guidance(agent_guidance: dict[str, Any]) -> dict[str, Any]:
    generic = agent_guidance["domainAgnosticSetupFlow"]
    return {
        "flowStatus": generic["flowStatus"],
        "clarificationQuestions": generic["clarificationQuestions"],
        "safeNextCommands": generic["safeNextCommands"],
        "keepsHelsinkiAsExample": generic["keepsHelsinkiAsExample"],
    }


def brief_check(order: int, check_key: str, instruction: str) -> dict[str, Any]:
    return {
        "checkKey": check_key,
        "order": order,
        "instruction": instruction,
        "required": True,
    }


def moderator_preflight(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        brief_check(
            1,
            "open_checked_task",
            f"Open the checked task card for {task['scenarioKey']} before the session starts.",
        ),
        brief_check(
            2,
            "use_generic_agent_guide",
            "Keep the domain-agnostic agent guide visible so the participant asks reusable setup questions first.",
        ),
        brief_check(
            3,
            "confirm_no_private_payloads",
            "Confirm the session will not capture raw transcripts, private rows, credentials, prompt logs, or identity.",
        ),
        brief_check(
            4,
            "prepare_nonledger_draft",
            "Prepare a local summary draft from the checked template, but leave it outside checked fixtures.",
        ),
        brief_check(
            5,
            "confirm_claim_boundary",
            "Remind the participant that usability evidence does not upgrade forecast quality, calibration, or hosted runtime claims.",
        ),
    ]


def participant_brief(task: dict[str, Any]) -> list[str]:
    return [
        "Use OPE setup readbacks before proposing a custom prediction engine.",
        "Explain which parts OPE owns: forecast contracts, source roles, baseline policy, forecast cards, resolver/scorer boundaries, and calibration gates.",
        "Explain which parts the host app owns: UI, approved source connections, runtime invocation, notifications, and optional method extensions.",
        f"Run or inspect the checked task command: {task['command']}",
        "Do not paste raw private data, credentials, prompt logs, or participant identity into the summary.",
    ]


def brief_step(order: int, step_key: str, instruction: str, expected_output: str) -> dict[str, Any]:
    return {
        "stepKey": step_key,
        "order": order,
        "instruction": instruction,
        "expectedOutput": expected_output,
    }


def session_runbook() -> list[dict[str, Any]]:
    return [
        brief_step(
            1,
            "start_from_generic_questions",
            "Ask the participant to identify the decision, outcome, horizon, source refs, baseline, and resolution source.",
            "The participant narrows the host prediction goal before implementation advice.",
        ),
        brief_step(
            2,
            "observe_setup_engine_first",
            "Watch whether the participant uses setup-engine or equivalent OPE setup readbacks before proposing app logic.",
            "Setup-engine-first, parallel-risk-engine, or audit-layer-only behavior can be classified.",
        ),
        brief_step(
            3,
            "capture_responsibility_split",
            "Ask the participant to distinguish OPE-owned records from host-owned UI/source/runtime work.",
            "The summary can record OPE-host responsibility comprehension without raw transcript text.",
        ),
        brief_step(
            4,
            "score_and_sanitize",
            "Score measured dimensions, record sanitized findings, choose friction classes, and run the sanitization checklist.",
            "Only sanitized ratings and findings are ready for intake classification.",
        ),
        brief_step(
            5,
            "classify_before_append",
            "Classify the filled summary, then append only accepted summaries with explicit --write-local.",
            "Ignored local evidence can update pilot findings only after moderator approval.",
        ),
    ]


def summary_draft(template: dict[str, Any]) -> dict[str, Any]:
    return {
        "draftSummaryId": template["summary"]["draftSummaryId"],
        "draftClassifiesAs": template["summary"]["draftClassifiesAs"],
        "draftLedgerReady": template["summary"]["draftLedgerReady"],
        "draftContributesRealSessionEvidence": template["summary"]["draftContributesRealSessionEvidence"],
        "printCommand": "python3 scripts/ope.py pilot-summary-template --section draft",
        "classificationCommand": "python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
    }


def command_step(
    order: int,
    step_key: str,
    command: str,
    expected_operator_action: str,
    *,
    mutates_local_state: bool = False,
) -> dict[str, Any]:
    return {
        "stepKey": step_key,
        "order": order,
        "command": command,
        "expectedOperatorAction": expected_operator_action,
        "mutatesLocalState": mutates_local_state,
    }


def command_sequence(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        command_step(
            1,
            "open_brief",
            "python3 scripts/ope.py pilot-session-brief",
            "Open the joined moderator brief before the supervised session.",
        ),
        command_step(
            2,
            "open_agent_guide",
            "python3 scripts/ope.py agent-guide --section generic",
            "Keep reusable setup questions visible during the session.",
        ),
        command_step(
            3,
            "open_task_packet",
            "python3 scripts/ope.py pilot-session-packet --task engine_setup_shortcut_comprehension",
            f"Open the checked task card for {task['scenarioKey']}.",
        ),
        command_step(
            4,
            "print_summary_draft",
            "python3 scripts/ope.py pilot-summary-template --section draft",
            "Fill the draft locally after the session; do not commit the filled summary.",
        ),
        command_step(
            5,
            "classify_summary",
            "python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
            "Classify the filled sanitized summary without writing a ledger row.",
        ),
        command_step(
            6,
            "append_local_evidence",
            "python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
            "Append only accepted sanitized summaries after explicit moderator approval.",
            mutates_local_state=True,
        ),
        command_step(
            7,
            "review_findings",
            "python3 scripts/ope.py pilot-findings --from-local-ledger --section summary",
            "Review ignored local pilot findings after append.",
        ),
        command_step(
            8,
            "review_status",
            "python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary",
            "Confirm remaining real-session count and blocked claim boundaries.",
        ),
    ]


def evidence_safety(packet: dict[str, Any], supervision: dict[str, Any]) -> dict[str, Any]:
    return {
        "sanitizationCheckCount": len(packet["sanitizationReview"]["checks"]),
        "requiredPassCount": packet["sanitizationReview"]["requiredPassCount"],
        "explicitWriteRequired": True,
        "localLedgerPath": supervision["summary"]["localLedgerPath"],
        "blockedInputs": [
            "raw_transcripts",
            "recordings",
            "prompt_logs",
            "private_rows",
            "credential_values",
            "participant_identity",
            "claim_overreach",
        ],
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "readOnlyBrief": True,
        "runsPilotSessions": False,
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": False,
        "recordsRawTranscripts": False,
        "storesPrivateData": False,
        "storesCredentials": False,
        "storesPromptLogs": False,
        "storesParticipantIdentity": False,
        "createsForecastArtifacts": False,
        "unblocksExpansion": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
        "hostedRuntimeUnblocked": False,
        "generatedTypesUnblocked": False,
    }


def summary(task: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "briefStatus": "ready_for_supervised_session",
        "recommendedScenarioKey": task["scenarioKey"],
        "recommendedTaskId": task["taskId"],
        "genericAgentGuidanceReady": True,
        "summaryDraftReady": True,
        "draftClassifiesAs": draft["draftClassifiesAs"],
        "draftLedgerReady": draft["draftLedgerReady"],
        "realSessionsRecorded": 0,
        "ledgerRowsWritten": 0,
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "hostedRuntimeAllowed": False,
        "generatedTypesEvidenceReady": False,
        "expansionEvidenceReady": False,
    }


def build_pilot_session_brief(*, scenario_key: str = RECOMMENDED_SCENARIO_KEY) -> dict[str, Any]:
    packet = load_generated_json(PACKET_PATH)
    agent_guidance = load_generated_json(AGENT_GUIDANCE_PATH)
    template = load_generated_json(SUMMARY_TEMPLATE_PATH)
    supervision = load_generated_json(SUPERVISION_STATUS_PATH)
    task = find_task(packet, scenario_key)
    task_readback = recommended_task(task, supervision)
    draft = summary_draft(template)
    return {
        "pilotSessionBriefId": "pilotsessionbrief-001",
        "generatedAt": GENERATED_AT,
        "briefStatus": "ready_for_supervised_session",
        "sourceRecords": {
            "pilotSessionPacketId": packet["pilotSessionPacketId"],
            "agentGuidanceId": agent_guidance["agentGuidanceId"],
            "pilotSummaryTemplateId": template["pilotSummaryTemplateId"],
            "pilotSupervisionStatusId": supervision["pilotSupervisionStatusId"],
        },
        "recommendedTask": task_readback,
        "genericAgentGuidance": generic_guidance(agent_guidance),
        "moderatorPreflight": moderator_preflight(task),
        "participantBrief": participant_brief(task),
        "sessionRunbook": session_runbook(),
        "summaryDraft": draft,
        "commandSequence": command_sequence(task),
        "evidenceSafety": evidence_safety(packet, supervision),
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This brief does not run a pilot session or write evidence.",
            "Filled summaries must stay outside checked fixtures and pass pilot-summary-intake before append.",
            "Only explicit --write-local can append accepted sanitized summaries to the ignored local ledger.",
            "Pilot usability evidence does not upgrade forecast quality, calibration, hosted runtime, generated-type, or expansion claims.",
        ],
        "summary": summary(task_readback, draft),
    }


def validate_pilot_session_brief(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PilotSessionBriefError(f"pilot session brief validation failed: {errors[0]}")


def view_payload(record: dict[str, Any], section: str | None) -> Any:
    if section == "summary":
        return record["summary"]
    if section == "task":
        return record["recommendedTask"]
    if section == "guidance":
        return record["genericAgentGuidance"]
    if section == "preflight":
        return record["moderatorPreflight"]
    if section == "participant":
        return record["participantBrief"]
    if section == "runbook":
        return record["sessionRunbook"]
    if section == "draft":
        return record["summaryDraft"]
    if section == "commands":
        return record["commandSequence"]
    if section == "safety":
        return record["evidenceSafety"]
    if section == "boundary":
        return record["executionBoundary"]
    if section == "warnings":
        return record["warnings"]
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=[RECOMMENDED_SCENARIO_KEY],
        default=RECOMMENDED_SCENARIO_KEY,
        help="checked pilot task to brief",
    )
    parser.add_argument("--section", choices=SECTION_NAMES, help="print one brief section")
    parser.add_argument("--write", action="store_true", help="write generated pilot session brief fixture")
    parser.add_argument("--check", action="store_true", help="check generated pilot session brief drift")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_pilot_session_brief(scenario_key=args.task)
    validate_pilot_session_brief(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="pilot session brief",
            regen="python3 scripts/generate_pilot_session_brief.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="pilot session brief",
            regen="python3 scripts/generate_pilot_session_brief.py --write",
        )
        return
    print(render_json(view_payload(record, args.section)), end="")


if __name__ == "__main__":
    main()
