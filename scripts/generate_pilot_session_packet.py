#!/usr/bin/env python3
"""Generate or check the real pilot-session collection packet."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_agent_pilot_validation import build_agent_pilot_validation
from generate_developer_adoption_surface import build_developer_adoption_surface
from generate_pilot_evidence_ledger import build_pilot_evidence_ledger
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-session-packet"
OUTPUT_PATH = GENERATED / "ope-pilot-session-packet.generated.json"
SCHEMA = SPEC / "pilot-session-packet.schema.json"
GENERATED_AT = "2026-06-10T12:00:00Z"

SECTION_NAMES = [
    "plan",
    "tasks",
    "template",
    "sanitization",
    "summary",
    "boundary",
]


class PilotSessionPacketError(Exception):
    pass


def session_step(index: int, action: str, expected_output: str) -> dict[str, Any]:
    return {
        "stepId": f"pilotsessionstep-{index:03d}",
        "order": index,
        "action": action,
        "expectedOutput": expected_output,
    }


def build_session_plan(pilot: dict[str, Any]) -> dict[str, Any]:
    return {
        "planId": "pilotsessionplan-001",
        "minimumRealSessions": pilot["pilotProtocol"]["minimumSessions"],
        "targetRealSessions": pilot["pilotProtocol"]["targetSessions"],
        "participantProfiles": ["agent_developer", "supervising_developer"],
        "moderatorChecklist": [
            "Confirm the participant is using the local MVP and understands no hosted service is being tested.",
            "Choose one checked task scenario and keep the task command visible.",
            "Capture only scores, sanitized findings, friction classes, expansion signals, and next action.",
            "Stop intake if raw transcripts, private rows, credentials, prompt logs, or participant identity appear.",
        ],
        "participantBrief": [
            "Use the checked local MVP commands as written; do not connect private production systems.",
            "Explain what you trust, what is confusing, and where the readback blocks claims or runtime expansion.",
            "Do not paste raw conversation logs, private data, credentials, or identifying details into the summary.",
        ],
        "sessionSteps": [
            session_step(
                1,
                "Select one checked task card from the packet.",
                "A task ID, command, expected outcome class, and measured dimensions are known before the session starts.",
            ),
            session_step(
                2,
                "Run or inspect the local MVP command in the participant environment.",
                "The participant can describe the readback, blocked state, or claim boundary in their own words.",
            ),
            session_step(
                3,
                "Score the required dimensions from 1 to 5 using only sanitized evidence notes.",
                "Dimension ratings are ready for the pilot evidence ledger without raw transcript text.",
            ),
            session_step(
                4,
                "Classify friction and expansion signals from the checked vocabulary.",
                "Repeated real-session patterns can later guide adoption, docs, runtime, or type-generation decisions.",
            ),
            session_step(
                5,
                "Run the sanitization review before any ledger submission.",
                "Unsafe notes are redacted or discarded before they become repository evidence.",
            ),
        ],
    }


def task_card(task: dict[str, Any]) -> dict[str, Any]:
    claim_required = "claim_boundary_comprehension" in task["measures"]
    friction_options = ["none", "readback_navigation", "claim_boundary_confusion"]
    if "source_intake_comprehension" in task["measures"]:
        friction_options.append("source_runtime_gap")
    if "runtime_gap_classification" in task["measures"]:
        friction_options.append("schema_integration_friction")
    expansion_options = ["keep_local_mvp", "run_more_pilots", "improve_docs"]
    if "runtime_gap_classification" in task["measures"]:
        expansion_options.append("consider_next_source_runtime")
    if claim_required:
        expansion_options.append("tighten_claim_copy")
    return {
        "taskId": task["taskId"],
        "scenarioKey": task["scenarioKey"],
        "title": task["title"],
        "command": task["command"],
        "expectedOutcomeClass": task["expectedOutcomeClass"],
        "measures": task["measures"],
        "captureFields": [
            "task_refs",
            "dimension_scores",
            "sanitized_findings",
            "friction_classes",
            "expansion_signals",
            "next_action",
        ],
        "ledgerMapping": {
            "frictionClassOptions": friction_options[:5],
            "expansionSignalOptions": expansion_options[:5],
            "claimBoundaryRequired": claim_required,
        },
        "moderatorPrompt": task["participantPrompt"],
    }


def build_task_cards(pilot: dict[str, Any]) -> list[dict[str, Any]]:
    return [task_card(task) for task in pilot["taskScenarios"]]


def build_evidence_template() -> dict[str, Any]:
    return {
        "templateId": "pilotsessiontemplate-001",
        "allowedFields": [
            "Task IDs from the checked pilot validation pack.",
            "Dimension ratings from 1 to 5 with short sanitized evidence notes.",
            "Sanitized findings that omit participant identity, raw transcript text, private data, and credentials.",
            "Friction classes and expansion signals from the checked vocabulary.",
            "One next action for adoption, documentation, runtime selection, or evidence collection.",
        ],
        "blockedFields": [
            "Raw transcripts, recordings, prompt logs, or full chat excerpts.",
            "Private source rows, customer or participant identifiers, credentials, and internal table names.",
            "Claims that one pilot session proves forecast quality, calibration, hosted readiness, or production runtime maturity.",
        ],
        "requiredFields": [
            "At least one task reference.",
            "At least one dimension rating.",
            "At least one sanitized finding.",
            "At least one friction class.",
            "At least one expansion signal.",
        ],
        "ledgerSubmissionShape": {
            "taskRefs": True,
            "dimensionRatings": True,
            "sanitizedFindings": True,
            "frictionClasses": True,
            "expansionSignals": True,
            "nextAction": True,
            "canSubmitToPilotEvidence": True,
        },
    }


def review_check(index: int, check: str) -> dict[str, Any]:
    return {
        "checkId": f"pilotsessioncheck-{index:03d}",
        "check": check,
        "requiredForLedgerSubmission": True,
    }


def build_sanitization_review() -> dict[str, Any]:
    checks = [
        review_check(1, "No raw transcript, recording, prompt log, or full chat excerpt is included."),
        review_check(2, "No private source rows, credentials, customer names, or participant identity are included."),
        review_check(3, "All findings are summarized enough to be stored in the repository."),
        review_check(4, "Dimension scores use the checked feedback dimensions and 1-5 scale."),
        review_check(5, "Friction classes and expansion signals use the checked ledger vocabulary."),
        review_check(6, "Claim-boundary confusion is recorded as a product signal, not as quality evidence."),
        review_check(7, "The summary does not unblock hosted runtime, generated types, stronger methods, or broad source runtimes."),
    ]
    return {
        "reviewId": "pilotsessionreview-001",
        "checks": checks,
        "requiredPassCount": len(checks),
    }


def build_collection_summary(
    *,
    task_count: int,
    pilot: dict[str, Any],
    ledger: dict[str, Any],
) -> dict[str, Any]:
    return {
        "taskCardCount": task_count,
        "minimumRealSessions": pilot["pilotProtocol"]["minimumSessions"],
        "targetRealSessions": pilot["pilotProtocol"]["targetSessions"],
        "realSessionsRecorded": ledger["summary"]["acceptedRealSessionCount"],
        "packetStatus": "ready_for_real_pilot_sessions",
        "ledgerSubmissionReady": True,
        "expansionEvidenceReady": False,
        "qualityClaimAllowed": False,
        "hostedRuntimeAllowed": False,
    }


def build_pilot_session_packet() -> dict[str, Any]:
    manifest = build_manifest()
    pilot = build_agent_pilot_validation()
    ledger = build_pilot_evidence_ledger()
    adoption = build_developer_adoption_surface()
    task_cards = build_task_cards(pilot)
    packet = {
        "pilotSessionPacketId": "pilotsessionpacket-001",
        "generatedAt": GENERATED_AT,
        "packetMode": "checked_real_pilot_session_collection_packet",
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "agentPilotValidationId": pilot["agentPilotValidationId"],
            "pilotEvidenceLedgerId": ledger["pilotEvidenceLedgerId"],
            "developerAdoptionSurfaceId": adoption["developerAdoptionSurfaceId"],
            "pilotProtocolId": pilot["pilotProtocol"]["protocolId"],
            "pilotEvidencePolicyId": ledger["intakePolicy"]["policyId"],
        },
        "sessionPlan": build_session_plan(pilot),
        "taskCards": task_cards,
        "evidenceTemplate": build_evidence_template(),
        "sanitizationReview": build_sanitization_review(),
        "stopConditions": [
            "Stop the session intake if the participant submits raw transcript text or recordings.",
            "Stop the session intake if private rows, credentials, source secrets, or participant identity appear.",
            "Stop the session intake if notes cannot be summarized without private operational details.",
            "Stop any expansion interpretation that treats pilot usability evidence as forecast-quality or calibration evidence.",
        ],
        "collectionSummary": build_collection_summary(task_count=len(task_cards), pilot=pilot, ledger=ledger),
        "executionBoundary": {
            "readOnlyPacket": True,
            "usesCheckedTaskDefinitions": True,
            "runsPilotSessions": False,
            "writesPilotEvidence": False,
            "recordsRawTranscripts": False,
            "storesPrivateData": False,
            "storesCredentials": False,
            "storesPromptLogs": False,
            "storesParticipantIdentity": False,
            "createsForecastArtifacts": False,
            "startsHostedRuntime": False,
            "fetchesLiveData": False,
            "unblocksExpansion": False,
        },
        "warnings": [
            "This packet prepares real pilot sessions but does not run them or record any real session evidence.",
            "Ledger submission is allowed only after sanitization review passes and unsafe details are removed.",
            "Pilot usability evidence can guide adoption and expansion priorities, but it is not forecast-quality or calibration evidence.",
            "Expansion remains blocked until enough real sanitized sessions and corpus evidence exist.",
        ],
    }
    validate_packet(packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> None:
    errors = validate_record(packet, SCHEMA)
    if errors:
        raise PilotSessionPacketError(f"pilot session packet schema validation failed: {errors[0]}")
    if packet["bindings"]["agentPilotValidationId"] != "agentpilotvalidation-001":
        raise PilotSessionPacketError("agent pilot validation binding drifted")
    if packet["bindings"]["pilotEvidenceLedgerId"] != "pilotevidenceledger-001":
        raise PilotSessionPacketError("pilot evidence ledger binding drifted")
    if packet["bindings"]["pilotEvidencePolicyId"] != "pilotevidencepolicy-001":
        raise PilotSessionPacketError("pilot evidence policy binding drifted")
    task_cards = packet["taskCards"]
    expected_order = [
        "local_file_setup_readback",
        "accepted_adapter_output_ready",
        "unsafe_source_block",
        "forecast_run_readback",
        "claim_gate_readback",
    ]
    if [item["scenarioKey"] for item in task_cards] != expected_order:
        raise PilotSessionPacketError("pilot session task order drifted")
    if packet["collectionSummary"]["taskCardCount"] != len(task_cards):
        raise PilotSessionPacketError("task card count drifted")
    if packet["collectionSummary"]["realSessionsRecorded"] != 0:
        raise PilotSessionPacketError("pilot session packet must not record real sessions")
    if packet["collectionSummary"]["expansionEvidenceReady"] or packet["collectionSummary"]["qualityClaimAllowed"]:
        raise PilotSessionPacketError("pilot session packet must not unblock expansion or quality claims")
    review = packet["sanitizationReview"]
    if review["requiredPassCount"] != len(review["checks"]):
        raise PilotSessionPacketError("all sanitization checks should be required")
    boundary = packet["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyPacket", "usesCheckedTaskDefinitions"}:
            if value is not True:
                raise PilotSessionPacketError(f"execution boundary {key} should be true")
        elif value is not False:
            raise PilotSessionPacketError(f"execution boundary {key} should be false")


def summary(packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "pilotSessionPacketId": packet["pilotSessionPacketId"],
        "packetMode": packet["packetMode"],
        "bindings": packet["bindings"],
        "collectionSummary": packet["collectionSummary"],
        "taskCards": [
            {
                "taskId": item["taskId"],
                "scenarioKey": item["scenarioKey"],
                "expectedOutcomeClass": item["expectedOutcomeClass"],
                "captureFields": item["captureFields"],
                "claimBoundaryRequired": item["ledgerMapping"]["claimBoundaryRequired"],
            }
            for item in packet["taskCards"]
        ],
        "stopConditions": packet["stopConditions"],
    }


def section(packet: dict[str, Any], section_name: str) -> Any:
    if section_name == "plan":
        return packet["sessionPlan"]
    if section_name == "tasks":
        return packet["taskCards"]
    if section_name == "template":
        return packet["evidenceTemplate"]
    if section_name == "sanitization":
        return packet["sanitizationReview"]
    if section_name == "summary":
        return packet["collectionSummary"]
    if section_name == "boundary":
        return packet["executionBoundary"]
    raise PilotSessionPacketError(f"unsupported section {section_name}")


def task(packet: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    for item in packet["taskCards"]:
        if item["scenarioKey"] == scenario_key:
            return item
    raise PilotSessionPacketError(f"unknown pilot session task {scenario_key}")


def write_packet(packet: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(packet), encoding="utf-8")
    print("generated pilot session packet")


def check_packet(packet: dict[str, Any]) -> None:
    expected = render_json(packet)
    if not OUTPUT_PATH.exists():
        print(f"missing pilot session packet: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_pilot_session_packet.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"pilot session packet drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_pilot_session_packet.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked pilot session packet")


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
        ],
        help="print one pilot session task card",
    )
    parser.add_argument(
        "--section",
        choices=SECTION_NAMES,
        help="print one pilot session packet section",
    )
    parser.add_argument("--check", action="store_true", help="check generated pilot session packet drift")
    parser.add_argument("--write", action="store_true", help="refresh generated pilot session packet")
    args = parser.parse_args()
    try:
        packet = build_pilot_session_packet()
    except PilotSessionPacketError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_packet(packet)
    elif args.check:
        check_packet(packet)
    elif args.task:
        sys.stdout.write(render_json(task(packet, args.task)))
    elif args.section:
        sys.stdout.write(render_json(section(packet, args.section)))
    else:
        sys.stdout.write(render_json(summary(packet)))


if __name__ == "__main__":
    main()
