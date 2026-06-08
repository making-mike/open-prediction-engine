#!/usr/bin/env python3
"""Generate or check the sanitized pilot summary template readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_pilot_evidence_ledger import build_pilot_evidence_ledger
from generate_pilot_session_packet import build_pilot_session_packet
from generate_pilot_summary_intake import classify_summary_submission, empty_risk_signals
from generate_pilot_supervision_status import RECOMMENDED_SCENARIO_KEY, build_pilot_supervision_status
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-summary-template"
OUTPUT_PATH = GENERATED / "ope-pilot-summary-template.generated.json"
SCHEMA = SPEC / "pilot-summary-template.schema.json"
SUBMISSION_SCHEMA = SPEC / "pilot-summary-submission.schema.json"
GENERATED_AT = "2026-06-10T13:00:00Z"
SECTION_NAMES = ["summary", "draft", "guidance", "checklist", "commands", "boundary", "warnings"]


class PilotSummaryTemplateError(Exception):
    pass


def find_task(packet: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    for item in packet["taskCards"]:
        if item["scenarioKey"] == scenario_key:
            return item
    raise PilotSummaryTemplateError(f"missing pilot session task {scenario_key}")


def recommended_task_from_packet(packet: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    task = find_task(packet, scenario_key)
    return {
        "taskId": task["taskId"],
        "scenarioKey": task["scenarioKey"],
        "title": task["title"],
        "taskCommand": task["command"],
        "expectedOutcomeClass": task["expectedOutcomeClass"],
        "measures": task["measures"],
    }


def draft_submission(task: dict[str, Any]) -> dict[str, Any]:
    risks = empty_risk_signals()
    risks["unredactedSourceDetailDetected"] = True
    return {
        "summaryId": "pilotsummaryinput-999",
        "evidenceClass": "future_real_summary",
        "taskRefs": [task["taskId"]],
        "dimensionRatings": [],
        "sanitizedFindings": [
            "Replace this placeholder with sanitized findings only; do not include transcript text, source rows, credentials, or participant identity."
        ],
        "frictionClasses": ["privacy_redaction_needed"],
        "expansionSignals": ["run_more_pilots"],
        "nextAction": "Replace this placeholder with one safe next action after moderator review.",
        "riskSignals": risks,
    }


def field_guidance(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "fieldName": "summaryId",
            "required": True,
            "allowedValues": ["pilotsummaryinput-<unique-number>"],
            "operatorInstruction": "Use a unique local summary ID before classification and append.",
        },
        {
            "fieldName": "taskRefs",
            "required": True,
            "allowedValues": [task["taskId"]],
            "operatorInstruction": "Keep the checked task ID that was actually used in the supervised session.",
        },
        {
            "fieldName": "dimensionRatings",
            "required": True,
            "allowedValues": task["measures"],
            "operatorInstruction": "Add one to five ratings with short sanitized evidence notes for the measured dimensions.",
        },
        {
            "fieldName": "sanitizedFindings",
            "required": True,
            "allowedValues": [],
            "operatorInstruction": "Summarize behavior without raw transcript text, private rows, credentials, prompt logs, or identity.",
        },
        {
            "fieldName": "frictionClasses",
            "required": True,
            "allowedValues": [
                "none",
                "readback_navigation",
                "claim_boundary_confusion",
                "source_runtime_gap",
                "schema_integration_friction",
                "privacy_redaction_needed",
                "parallel_risk_engine_confusion",
                "audit_layer_only_confusion",
            ],
            "operatorInstruction": "Choose checked friction classes only; use none when no friction was observed.",
        },
        {
            "fieldName": "expansionSignals",
            "required": True,
            "allowedValues": [
                "keep_local_mvp",
                "run_more_pilots",
                "improve_docs",
                "consider_next_source_runtime",
                "tighten_claim_copy",
            ],
            "operatorInstruction": "Choose checked expansion signals without treating one session as quality or runtime evidence.",
        },
        {
            "fieldName": "riskSignals",
            "required": True,
            "allowedValues": [
                "rawTranscriptDetected",
                "privateRowsDetected",
                "credentialLikeTextDetected",
                "participantIdentityDetected",
                "unredactedSourceDetailDetected",
                "claimOverreachDetected",
            ],
            "operatorInstruction": "Keep any detected unsafe signal true until redaction is complete; unchanged drafts are not ledger-ready.",
        },
        {
            "fieldName": "nextAction",
            "required": True,
            "allowedValues": [],
            "operatorInstruction": "Record one safe next action for adoption, documentation, runtime selection, or evidence collection.",
        },
    ]


def checklist(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "checkId": item["checkId"],
            "required": item["requiredForLedgerSubmission"],
            "check": item["check"],
        }
        for item in packet["sanitizationReview"]["checks"]
    ]


def command_step(
    *,
    order: int,
    step_key: str,
    command: str,
    expected_operator_action: str,
    mutates_local_state: bool = False,
) -> dict[str, Any]:
    return {
        "stepKey": step_key,
        "order": order,
        "command": command,
        "expectedOperatorAction": expected_operator_action,
        "mutatesLocalState": mutates_local_state,
    }


def command_sequence() -> list[dict[str, Any]]:
    return [
        command_step(
            order=1,
            step_key="print_draft",
            command="python3 scripts/ope.py pilot-summary-template --section draft",
            expected_operator_action="Use the printed JSON shape as a local sanitized summary draft and fill it outside checked fixtures.",
        ),
        command_step(
            order=2,
            step_key="classify_summary",
            command="python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
            expected_operator_action="Classify the filled sanitized summary without writing a ledger row.",
        ),
        command_step(
            order=3,
            step_key="append_local_evidence",
            command="python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
            expected_operator_action="Append only an accepted sanitized summary after explicit moderator approval.",
            mutates_local_state=True,
        ),
        command_step(
            order=4,
            step_key="review_status",
            command="python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary",
            expected_operator_action="Confirm updated local evidence count and blocked claim boundaries.",
        ),
    ]


def template_safety(draft: dict[str, Any]) -> dict[str, Any]:
    result = classify_summary_submission(draft, input_ref="pilot-summary-template-draft")
    return {
        "draftClassifiesAs": result["intakeDecision"],
        "draftLedgerReady": result["ledgerReady"],
        "draftContributesRealSessionEvidence": result["contributesRealSessionEvidence"],
        "draftWritesLedgerRows": result["ledgerRowsWritten"] > 0,
        "unchangedDraftAppendAllowed": result["ledgerReady"] and result["candidateRealSessionEvidence"],
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "readOnlyTemplate": True,
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": False,
        "runsPilotSessions": False,
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


def summary(
    *,
    task: dict[str, Any],
    draft: dict[str, Any],
    safety: dict[str, Any],
) -> dict[str, Any]:
    return {
        "templateStatus": "ready_for_operator_fill",
        "recommendedScenarioKey": task["scenarioKey"],
        "recommendedTaskId": task["taskId"],
        "draftSummaryId": draft["summaryId"],
        "draftClassifiesAs": safety["draftClassifiesAs"],
        "draftLedgerReady": safety["draftLedgerReady"],
        "draftContributesRealSessionEvidence": safety["draftContributesRealSessionEvidence"],
        "realSessionsRecorded": 0,
        "ledgerRowsWritten": 0,
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "hostedRuntimeAllowed": False,
        "generatedTypesEvidenceReady": False,
        "expansionEvidenceReady": False,
    }


def build_pilot_summary_template(*, scenario_key: str = RECOMMENDED_SCENARIO_KEY) -> dict[str, Any]:
    packet = build_pilot_session_packet()
    ledger = build_pilot_evidence_ledger()
    supervision = build_pilot_supervision_status()
    task = recommended_task_from_packet(packet, scenario_key)
    draft = draft_submission(task)
    safety = template_safety(draft)
    record = {
        "pilotSummaryTemplateId": "pilotsummarytemplate-001",
        "generatedAt": GENERATED_AT,
        "templateStatus": "ready_for_operator_fill",
        "bindings": {
            "pilotSessionPacketId": packet["pilotSessionPacketId"],
            "pilotSessionReviewId": packet["sanitizationReview"]["reviewId"],
            "pilotSummaryIntakeId": "pilotsummaryintake-001",
            "pilotEvidenceLedgerId": ledger["pilotEvidenceLedgerId"],
            "pilotSupervisionStatusId": supervision["pilotSupervisionStatusId"],
            "pilotSummarySubmissionSchema": "spec/pilot-summary-submission.schema.json",
        },
        "recommendedTask": task,
        "draftSubmission": draft,
        "fieldGuidance": field_guidance(task),
        "sanitizationChecklist": checklist(packet),
        "commandSequence": command_sequence(),
        "templateSafety": safety,
        "executionBoundary": execution_boundary(),
        "warnings": [
            "The included draft is intentionally not ledger-ready until an operator fills ratings and clears sanitization risks.",
            "Do not commit real pilot summaries; classify and append approved summaries to the ignored local ledger only.",
            "This template does not run pilot sessions, write evidence, or upgrade quality, calibration, hosted-runtime, generated-type, or expansion claims.",
        ],
    }
    record["summary"] = summary(task=task, draft=draft, safety=safety)
    validate_pilot_summary_template(record)
    return record


def validate_pilot_summary_template(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PilotSummaryTemplateError(f"pilot summary template schema validation failed: {errors[0]}")
    draft_errors = validate_record(record["draftSubmission"], SUBMISSION_SCHEMA)
    if draft_errors:
        raise PilotSummaryTemplateError(f"pilot summary draft schema validation failed: {draft_errors[0]}")
    safety = record["templateSafety"]
    if safety["draftClassifiesAs"] != "needs_redaction":
        raise PilotSummaryTemplateError("template draft should classify as needs_redaction")
    if safety["draftLedgerReady"] or safety["draftContributesRealSessionEvidence"] or safety["draftWritesLedgerRows"]:
        raise PilotSummaryTemplateError("template draft must not be ledger-ready or count evidence")
    boundary = record["executionBoundary"]
    for key, value in boundary.items():
        if key == "readOnlyTemplate":
            if value is not True:
                raise PilotSummaryTemplateError("template read-only boundary should be true")
        elif value is not False:
            raise PilotSummaryTemplateError(f"template boundary {key} should be false")


def load_generated_template() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    record = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_pilot_summary_template(record)
    return record


def write_template(record: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        record,
        label="pilot summary template",
        regen="python3 scripts/generate_pilot_summary_template.py --write",
    )


def check_template(record: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        record,
        label="pilot summary template",
        regen="python3 scripts/generate_pilot_summary_template.py --write",
    )


def section(record: dict[str, Any], section_name: str) -> Any:
    if section_name == "summary":
        return record["summary"]
    if section_name == "draft":
        return record["draftSubmission"]
    if section_name == "guidance":
        return record["fieldGuidance"]
    if section_name == "checklist":
        return record["sanitizationChecklist"]
    if section_name == "commands":
        return record["commandSequence"]
    if section_name == "boundary":
        return record["executionBoundary"]
    if section_name == "warnings":
        return record["warnings"]
    raise PilotSummaryTemplateError(f"unsupported section {section_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--task",
        choices=[
            "local_file_setup_readback",
            "accepted_adapter_output_ready",
            "unsafe_source_block",
            "forecast_run_readback",
            "claim_gate_readback",
            "engine_setup_shortcut_comprehension",
            "repeating_prediction_campaign",
        ],
        default=RECOMMENDED_SCENARIO_KEY,
        help="pilot task scenario to draft a summary for",
    )
    parser.add_argument("--section", choices=SECTION_NAMES, help="print one pilot summary template section")
    parser.add_argument("--check", action="store_true", help="check generated pilot summary template drift")
    parser.add_argument("--write", action="store_true", help="refresh generated pilot summary template")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.write or args.check or args.rebuild or args.task != RECOMMENDED_SCENARIO_KEY:
            record = build_pilot_summary_template(scenario_key=args.task)
        else:
            record = load_generated_template() or build_pilot_summary_template()
    except PilotSummaryTemplateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_template(record)
    elif args.check:
        check_template(record)
    elif args.section:
        sys.stdout.write(render_json(section(record, args.section)))
    else:
        sys.stdout.write(render_json(record))


if __name__ == "__main__":
    main()
