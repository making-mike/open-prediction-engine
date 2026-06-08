#!/usr/bin/env python3
"""Generate or check the sanitized pilot evidence ledger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_agent_pilot_validation import build_agent_pilot_validation
from generate_developer_adoption_surface import build_developer_adoption_surface
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-evidence"
OUTPUT_PATH = GENERATED / "ope-pilot-evidence-ledger.generated.json"
SCHEMA = SPEC / "pilot-evidence-ledger.schema.json"
LOCAL_APPEND_SCHEMA = SPEC / "pilot-evidence-local-append.schema.json"
LOCAL_READBACK_SCHEMA = SPEC / "pilot-evidence-local-readback.schema.json"
GENERATED_AT = "2026-06-10T11:30:00Z"
LOCAL_PILOT_LEDGER = ROOT / ".ope" / "live" / "pilot-evidence" / "pilot-evidence-ledger.json"
LOCAL_PILOT_LEDGER_RELATIVE = ".ope/live/pilot-evidence/pilot-evidence-ledger.json"

CASE_ORDER = [
    "accepted_sanitized_summary",
    "needs_redaction",
    "raw_transcript_blocked",
    "private_data_blocked",
    "claim_boundary_confusion",
]


class PilotEvidenceLedgerError(Exception):
    pass


def input_signals(
    *,
    raw_transcript: bool = False,
    private_data: bool = False,
    credential_like: bool = False,
    claim_confusion: bool = False,
    runtime_gap: bool = False,
) -> dict[str, bool]:
    return {
        "rawTranscriptSubmitted": raw_transcript,
        "privateDataSubmitted": private_data,
        "credentialLikeTextSubmitted": credential_like,
        "claimConfusionObserved": claim_confusion,
        "runtimeGapObserved": runtime_gap,
    }


def privacy_checks(*, notes_redacted: bool) -> dict[str, bool]:
    return {
        "rawTranscriptStored": False,
        "privateDataStored": False,
        "credentialsStored": False,
        "promptLogStored": False,
        "participantIdentityStored": False,
        "notesRedacted": notes_redacted,
    }


def rating(dimension_id: str, score: int, note: str) -> dict[str, Any]:
    return {
        "dimensionId": dimension_id,
        "score": score,
        "evidenceNote": note,
    }


def case_row(
    *,
    index: int,
    case_key: str,
    participant_profile: str,
    task_refs: list[str],
    intake_status: str,
    accepted: bool,
    signals: dict[str, bool],
    notes_redacted: bool,
    ratings: list[dict[str, Any]],
    findings: list[str],
    friction_classes: list[str],
    expansion_signals: list[str],
    next_action: str,
) -> dict[str, Any]:
    return {
        "caseId": f"pilotevidencecase-{index:03d}",
        "caseKey": case_key,
        "evidenceClass": "synthetic_example",
        "participantProfile": participant_profile,
        "taskRefs": task_refs,
        "intakeStatus": intake_status,
        "acceptedForAggregation": accepted,
        "contributesRealSessionEvidence": False,
        "inputSignals": signals,
        "privacyChecks": privacy_checks(notes_redacted=notes_redacted),
        "dimensionRatings": ratings,
        "sanitizedFindings": findings,
        "frictionClasses": friction_classes,
        "expansionSignals": expansion_signals,
        "nextAction": next_action,
    }


def build_case_rows() -> list[dict[str, Any]]:
    return [
        case_row(
            index=1,
            case_key="accepted_sanitized_summary",
            participant_profile="agent_developer",
            task_refs=["agentpilottask-001", "agentpilottask-004", "agentpilottask-005"],
            intake_status="accepted_for_aggregation",
            accepted=True,
            signals=input_signals(),
            notes_redacted=True,
            ratings=[
                rating("task_completion", 5, "Completed local setup readback and forecast-run readback without moderator correction."),
                rating("forecast_card_comprehension", 4, "Identified probability, baseline, resolution, scoring, and claim status."),
                rating("claim_boundary_comprehension", 5, "Kept one scored fixture separate from calibration or broad quality claims."),
                rating("trust_for_agent_decision_support", 4, "Would use the card for supervised agent support with claim warnings visible."),
            ],
            findings=[
                "Participant reached forecast-1102 card and lifecycle bundle from the local MVP path.",
                "Participant understood that public transit calibration remains below threshold.",
            ],
            friction_classes=["none"],
            expansion_signals=["keep_local_mvp", "run_more_pilots"],
            next_action="Count this shape as an acceptable sanitized-summary format for future real sessions.",
        ),
        case_row(
            index=2,
            case_key="needs_redaction",
            participant_profile="supervising_developer",
            task_refs=["agentpilottask-002"],
            intake_status="needs_redaction",
            accepted=False,
            signals=input_signals(runtime_gap=True),
            notes_redacted=False,
            ratings=[
                rating("source_intake_comprehension", 3, "Understood accepted adapter output but included too much implementation-specific context in notes."),
                rating("runtime_gap_classification", 4, "Correctly identified a missing runtime feature rather than a failed forecast."),
            ],
            findings=[
                "Summary is structurally useful but needs further redaction before aggregation.",
                "Runtime gap should be classified without copying private source names or table details.",
            ],
            friction_classes=["privacy_redaction_needed", "source_runtime_gap"],
            expansion_signals=["consider_next_source_runtime", "run_more_pilots"],
            next_action="Redact source-specific details, then reclassify as accepted or blocked.",
        ),
        case_row(
            index=3,
            case_key="raw_transcript_blocked",
            participant_profile="agent_developer",
            task_refs=["agentpilottask-001"],
            intake_status="blocked_raw_transcript",
            accepted=False,
            signals=input_signals(raw_transcript=True),
            notes_redacted=False,
            ratings=[],
            findings=[
                "Raw transcript input must be rejected before it enters the checked ledger.",
                "Only summarized dimension scores and sanitized findings are allowed.",
            ],
            friction_classes=["privacy_redaction_needed"],
            expansion_signals=["run_more_pilots"],
            next_action="Replace raw transcript with a sanitized summary that follows the intake policy.",
        ),
        case_row(
            index=4,
            case_key="private_data_blocked",
            participant_profile="supervising_developer",
            task_refs=["agentpilottask-003"],
            intake_status="blocked_private_data",
            accepted=False,
            signals=input_signals(private_data=True, credential_like=True),
            notes_redacted=False,
            ratings=[],
            findings=[
                "Private rows or credential-like details must not be stored in pilot evidence.",
                "Unsafe source notes should be reduced to blocked reason, next action, and dimension scores.",
            ],
            friction_classes=["privacy_redaction_needed"],
            expansion_signals=["improve_docs"],
            next_action="Discard private details and record only sanitized blocked-path comprehension findings.",
        ),
        case_row(
            index=5,
            case_key="claim_boundary_confusion",
            participant_profile="agent_developer",
            task_refs=["agentpilottask-005"],
            intake_status="accepted_with_claim_boundary_issue",
            accepted=True,
            signals=input_signals(claim_confusion=True),
            notes_redacted=True,
            ratings=[
                rating("task_completion", 4, "Completed the claim-gate readback."),
                rating("claim_boundary_comprehension", 2, "Initially treated one scored transit run as a quality claim."),
                rating("trust_for_agent_decision_support", 3, "Would need stronger visible warnings before trusting agent use."),
            ],
            findings=[
                "Claim-boundary confusion is safe to aggregate because notes are sanitized.",
                "This signal blocks expansion messaging until copy and read surfaces are improved.",
            ],
            friction_classes=["claim_boundary_confusion", "readback_navigation"],
            expansion_signals=["tighten_claim_copy", "improve_docs", "run_more_pilots"],
            next_action="Use this as a negative pilot signal and tighten claim-boundary readbacks before expansion.",
        ),
    ]


def build_intake_policy(pilot: dict[str, Any]) -> dict[str, Any]:
    return {
        "policyId": "pilotevidencepolicy-001",
        "minimumRealSessions": pilot["pilotProtocol"]["minimumSessions"],
        "targetRealSessions": pilot["pilotProtocol"]["targetSessions"],
        "allowedInputs": [
            "Dimension scores tied to checked pilot task IDs.",
            "Sanitized findings that omit participant identity, private data, raw transcript text, and credentials.",
            "Friction classes and expansion signals chosen from the checked ledger vocabulary.",
        ],
        "blockedInputs": [
            "Raw transcripts, recordings, prompt logs, or full chat excerpts.",
            "Private source rows, source credentials, customer names, internal table names, or unredacted identifiers.",
            "Any pilot note that turns fixture success into quality, calibration, hosted-runtime, or production-readiness claims.",
        ],
        "requiredSanitizationChecks": [
            "Confirm no raw transcript or recording text is stored.",
            "Confirm no private rows, credentials, prompt logs, or participant identity are stored.",
            "Confirm findings are summarized enough for repository storage.",
            "Confirm claim-boundary confusion is recorded as a product signal, not a quality claim.",
        ],
        "acceptedUse": "Accepted sanitized summaries may inform adoption fixes and expansion-readiness decisions, but not forecast quality, calibration, or production-runtime claims.",
    }


def aggregation_rule(index: int, rule: str, effect: str) -> dict[str, Any]:
    return {
        "ruleId": f"pilotevidencerule-{index:03d}",
        "rule": rule,
        "effect": effect,
    }


def build_aggregation_rules() -> list[dict[str, Any]]:
    return [
        aggregation_rule(
            1,
            "Only accepted sanitized real-session summaries can count toward minimum or target pilot-session thresholds.",
            "Synthetic checked examples keep the schema testable but do not unblock expansion.",
        ),
        aggregation_rule(
            2,
            "Any raw transcript, private data, credential-like text, prompt log, or participant identity blocks intake.",
            "The evidence row must be redacted or discarded before aggregation.",
        ),
        aggregation_rule(
            3,
            "Claim-boundary confusion can be accepted as a sanitized finding.",
            "It increases the issue count and blocks stronger messaging until read surfaces are tightened.",
        ),
        aggregation_rule(
            4,
            "Runtime gaps should be classified separately from usability gaps.",
            "Only repeated real-session runtime gaps can justify a next runtime milestone.",
        ),
    ]


def next_action(index: int, priority: int, action: str, blocks: bool) -> dict[str, Any]:
    return {
        "actionId": f"pilotevidenceaction-{index:03d}",
        "priority": priority,
        "action": action,
        "blocksExpansionUntilDone": blocks,
    }


def build_next_actions() -> list[dict[str, Any]]:
    return [
        next_action(
            1,
            1,
            "Run 3-5 real local MVP pilot sessions using the checked agent-pilot-validation tasks.",
            True,
        ),
        next_action(
            2,
            2,
            "Record only sanitized dimension scores, findings, friction classes, and expansion signals.",
            True,
        ),
        next_action(
            3,
            3,
            "Tighten developer adoption or claim-boundary surfaces if real sessions repeat confusion.",
            False,
        ),
        next_action(
            4,
            4,
            "Use repeated real runtime-gap evidence before choosing one next private-source or hosted runtime path.",
            True,
        ),
    ]


def build_pilot_evidence_ledger() -> dict[str, Any]:
    manifest = build_manifest()
    pilot = build_agent_pilot_validation()
    adoption = build_developer_adoption_surface()
    cases = build_case_rows()
    accepted_synthetic = sum(1 for item in cases if item["acceptedForAggregation"])
    blocked = sum(1 for item in cases if item["intakeStatus"].startswith("blocked_"))
    needs_redaction = sum(1 for item in cases if item["intakeStatus"] == "needs_redaction")
    claim_issues = sum(1 for item in cases if item["inputSignals"]["claimConfusionObserved"])
    ledger = {
        "pilotEvidenceLedgerId": "pilotevidenceledger-001",
        "generatedAt": GENERATED_AT,
        "ledgerMode": "checked_sanitized_pilot_summary_intake",
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "agentPilotValidationId": pilot["agentPilotValidationId"],
            "developerAdoptionSurfaceId": adoption["developerAdoptionSurfaceId"],
            "pilotProtocolId": pilot["pilotProtocol"]["protocolId"],
            "feedbackSchemaId": pilot["feedbackSchema"]["feedbackSchemaId"],
        },
        "intakePolicy": build_intake_policy(pilot),
        "caseRows": cases,
        "aggregationRules": build_aggregation_rules(),
        "summary": {
            "totalCaseCount": len(cases),
            "acceptedSyntheticSummaryCount": accepted_synthetic,
            "acceptedRealSessionCount": 0,
            "blockedCaseCount": blocked,
            "needsRedactionCount": needs_redaction,
            "claimBoundaryIssueCount": claim_issues,
            "minimumRealSessions": pilot["pilotProtocol"]["minimumSessions"],
            "targetRealSessions": pilot["pilotProtocol"]["targetSessions"],
            "pilotEvidenceStatus": "real_sessions_needed",
            "expansionEvidenceReady": False,
            "qualityClaimAllowed": False,
            "hostedRuntimeAllowed": False,
            "generatedTypesEvidenceReady": False,
        },
        "nextActions": build_next_actions(),
        "executionBoundary": {
            "readOnlyLedger": True,
            "usesSyntheticCheckedExamplesOnly": True,
            "declaresFutureRealSummaryIntake": True,
            "runsPilotSessions": False,
            "recordsRawTranscripts": False,
            "storesPrivateData": False,
            "storesCredentials": False,
            "storesPromptLogs": False,
            "createsForecastArtifacts": False,
            "startsHostedRuntime": False,
            "fetchesLiveData": False,
            "generatesRuntimeTypes": False,
            "unblocksExpansion": False,
        },
        "warnings": [
            "The checked ledger contains synthetic examples only; real pilot sessions have not been recorded.",
            "Raw transcripts, private data, credentials, prompt logs, and participant identity must stay out of the repository.",
            "Accepted pilot evidence can guide adoption and runtime priorities, but it is not forecast-quality or calibration evidence.",
            "Expansion remains blocked until enough real sanitized sessions and corpus evidence exist.",
        ],
    }
    validate_ledger(ledger)
    return ledger


def validate_ledger(ledger: dict[str, Any]) -> None:
    errors = validate_record(ledger, SCHEMA)
    if errors:
        raise PilotEvidenceLedgerError(f"pilot evidence ledger schema validation failed: {errors[0]}")
    cases = ledger["caseRows"]
    if [item["caseKey"] for item in cases] != CASE_ORDER:
        raise PilotEvidenceLedgerError("pilot evidence case order drifted")
    for item in cases:
        privacy = item["privacyChecks"]
        for key in ("rawTranscriptStored", "privateDataStored", "credentialsStored", "promptLogStored", "participantIdentityStored"):
            if privacy[key] is not False:
                raise PilotEvidenceLedgerError(f"privacy field {key} must remain false")
        if item["contributesRealSessionEvidence"] is not False:
            raise PilotEvidenceLedgerError("checked examples must not contribute real session evidence")
    blocked = {item["caseKey"]: item for item in cases if item["intakeStatus"].startswith("blocked_")}
    if set(blocked) != {"raw_transcript_blocked", "private_data_blocked"}:
        raise PilotEvidenceLedgerError("blocked case coverage drifted")
    if cases[0]["acceptedForAggregation"] is not True:
        raise PilotEvidenceLedgerError("accepted sanitized summary should aggregate")
    if cases[1]["intakeStatus"] != "needs_redaction":
        raise PilotEvidenceLedgerError("redaction case status drifted")
    if cases[4]["inputSignals"]["claimConfusionObserved"] is not True:
        raise PilotEvidenceLedgerError("claim-boundary confusion case should flag confusion")
    summary = ledger["summary"]
    if summary["acceptedRealSessionCount"] != 0:
        raise PilotEvidenceLedgerError("checked ledger should not record real sessions")
    if summary["expansionEvidenceReady"] or summary["qualityClaimAllowed"] or summary["hostedRuntimeAllowed"]:
        raise PilotEvidenceLedgerError("pilot evidence summary must not unblock expansion or quality claims")
    boundary = ledger["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyLedger", "usesSyntheticCheckedExamplesOnly", "declaresFutureRealSummaryIntake"}:
            if value is not True:
                raise PilotEvidenceLedgerError(f"execution boundary {key} should be true")
        elif value is not False:
            raise PilotEvidenceLedgerError(f"execution boundary {key} should be false")


def summary(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "pilotEvidenceLedgerId": ledger["pilotEvidenceLedgerId"],
        "ledgerMode": ledger["ledgerMode"],
        "bindings": ledger["bindings"],
        "summary": ledger["summary"],
        "caseRows": [
            {
                "caseKey": item["caseKey"],
                "intakeStatus": item["intakeStatus"],
                "acceptedForAggregation": item["acceptedForAggregation"],
                "contributesRealSessionEvidence": item["contributesRealSessionEvidence"],
                "frictionClasses": item["frictionClasses"],
                "expansionSignals": item["expansionSignals"],
            }
            for item in ledger["caseRows"]
        ],
        "nextActions": ledger["nextActions"],
    }


def section(ledger: dict[str, Any], section_name: str) -> Any:
    if section_name == "policy":
        return ledger["intakePolicy"]
    if section_name == "cases":
        return ledger["caseRows"]
    if section_name == "summary":
        return ledger["summary"]
    if section_name == "next-actions":
        return ledger["nextActions"]
    if section_name == "boundary":
        return ledger["executionBoundary"]
    raise PilotEvidenceLedgerError(f"unsupported section {section_name}")


def case(ledger: dict[str, Any], case_key: str) -> dict[str, Any]:
    for row in ledger["caseRows"]:
        if row["caseKey"] == case_key:
            return row
    raise PilotEvidenceLedgerError(f"unknown pilot evidence case {case_key}")


def write_ledger(ledger: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, ledger, label="pilot evidence ledger", regen="python3 scripts/generate_pilot_evidence_ledger.py --write")


def check_ledger(ledger: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, ledger, label="pilot evidence ledger", regen="python3 scripts/generate_pilot_evidence_ledger.py --write")


def load_generated_ledger() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    ledger = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_ledger(ledger)
    return ledger


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def local_ledger_path_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def local_case_id(summary_id: str) -> str:
    match = re.search(r"-(\d+)$", summary_id)
    if match:
        return f"pilotevidencelocal-{int(match.group(1)):03d}"
    return "pilotevidencelocal-999"


def append_execution_boundary(*, writes_local: bool = False) -> dict[str, bool]:
    return {
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": writes_local,
        "recordsRawTranscripts": False,
        "storesPrivateData": False,
        "storesCredentials": False,
        "storesPromptLogs": False,
        "storesParticipantIdentity": False,
        "createsForecastArtifacts": False,
        "startsHostedRuntime": False,
        "fetchesLiveData": False,
        "unblocksExpansion": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
    }


def local_readback_boundary() -> dict[str, bool]:
    return {
        "readOnlyReadback": True,
        "readsIgnoredLocalLedger": True,
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": False,
        "recordsRawTranscripts": False,
        "storesPrivateData": False,
        "storesCredentials": False,
        "storesPromptLogs": False,
        "storesParticipantIdentity": False,
        "createsForecastArtifacts": False,
        "startsHostedRuntime": False,
        "fetchesLiveData": False,
        "unblocksExpansion": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
    }


def load_summary_submission(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    from generate_pilot_summary_intake import INPUT_SCHEMA, PilotSummaryIntakeError, classify_summary_file

    try:
        result = classify_summary_file(path)
    except PilotSummaryIntakeError as exc:
        raise PilotEvidenceLedgerError(str(exc)) from exc
    try:
        submission = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PilotEvidenceLedgerError(f"could not read pilot summary input {path}: {exc}") from exc
    if not isinstance(submission, dict):
        raise PilotEvidenceLedgerError("pilot summary input must be a JSON object")
    errors = validate_record(submission, INPUT_SCHEMA)
    if errors:
        raise PilotEvidenceLedgerError(f"pilot summary input schema validation failed: {errors[0]}")
    return submission, result


def candidate_row_from_summary(
    submission: dict[str, Any],
    intake_result: dict[str, Any],
    *,
    input_ref: str,
) -> dict[str, Any]:
    risks = intake_result["riskSignals"]
    friction_classes = submission["frictionClasses"]
    intake_status = (
        "accepted_with_product_signal"
        if intake_result["intakeDecision"] == "accept_with_product_signal"
        else "accepted_for_aggregation"
    )
    return {
        "caseId": local_case_id(submission["summaryId"]),
        "caseKey": "local_real_session_summary",
        "sourceSummaryId": submission["summaryId"],
        "inputRef": input_ref,
        "evidenceClass": "future_real_summary",
        "taskRefs": submission["taskRefs"],
        "intakeStatus": intake_status,
        "acceptedForAggregation": True,
        "contributesRealSessionEvidence": True,
        "inputSignals": {
            "rawTranscriptSubmitted": risks["rawTranscriptDetected"],
            "privateDataSubmitted": risks["privateRowsDetected"],
            "credentialLikeTextSubmitted": risks["credentialLikeTextDetected"],
            "claimConfusionObserved": "claim_boundary_confusion" in friction_classes,
            "runtimeGapObserved": "source_runtime_gap" in friction_classes,
        },
        "privacyChecks": privacy_checks(notes_redacted=True),
        "dimensionRatings": submission["dimensionRatings"],
        "sanitizedFindings": submission["sanitizedFindings"],
        "frictionClasses": friction_classes,
        "expansionSignals": submission["expansionSignals"],
        "nextAction": submission["nextAction"],
    }


def validate_local_case_row(row: dict[str, Any]) -> None:
    append_plan = {
        "pilotEvidenceAppendPlanId": "pilotevidenceappendplan-001",
        "generatedAt": GENERATED_AT,
        "appendMode": "local_pilot_summary_append_plan",
        "inputRef": row["inputRef"],
        "inputSummaryId": row["sourceSummaryId"],
        "intakeDecision": row["intakeStatus"],
        "appendDecision": "ready_for_local_write",
        "localLedgerPath": LOCAL_PILOT_LEDGER_RELATIVE,
        "writeLocalRequired": True,
        "writeLocalRequested": False,
        "candidateRealSessionEvidence": True,
        "contributesRealSessionEvidence": False,
        "ledgerRowsWritten": 0,
        "realSessionsRecorded": 0,
        "candidateRow": row,
        "executionBoundary": append_execution_boundary(),
        "warnings": [
            "Validation wrapper for one local pilot evidence row.",
            "This wrapper is not written as a checked fixture.",
        ],
    }
    errors = validate_record(append_plan, LOCAL_APPEND_SCHEMA)
    if errors:
        raise PilotEvidenceLedgerError(f"local pilot evidence row validation failed: {errors[0]}")
    privacy = row["privacyChecks"]
    for key in ("rawTranscriptStored", "privateDataStored", "credentialsStored", "promptLogStored", "participantIdentityStored"):
        if privacy[key] is not False:
            raise PilotEvidenceLedgerError(f"local row privacy field {key} must remain false")
    signals = row["inputSignals"]
    if signals["rawTranscriptSubmitted"] or signals["privateDataSubmitted"] or signals["credentialLikeTextSubmitted"]:
        raise PilotEvidenceLedgerError("local evidence rows cannot preserve unsafe input signals")
    if row["acceptedForAggregation"] is not True or row["contributesRealSessionEvidence"] is not True:
        raise PilotEvidenceLedgerError("local evidence rows must be accepted real-session rows")


def load_local_pilot_rows(local_ledger_path: Path | None = None) -> tuple[str, list[dict[str, Any]]]:
    path = local_ledger_path or LOCAL_PILOT_LEDGER
    if not path.exists():
        return "missing", []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PilotEvidenceLedgerError(f"could not read local pilot evidence ledger {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PilotEvidenceLedgerError(f"local pilot evidence ledger is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise PilotEvidenceLedgerError("local pilot evidence ledger must be a JSON object")
    rows = payload.get("caseRows")
    if not isinstance(rows, list):
        raise PilotEvidenceLedgerError("local pilot evidence ledger must contain caseRows")
    for row in rows:
        if not isinstance(row, dict):
            raise PilotEvidenceLedgerError("local pilot evidence row must be a JSON object")
        validate_local_case_row(row)
    return "readable", rows


def aggregate_local_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    pilot = build_agent_pilot_validation()
    accepted_real = sum(
        1
        for row in rows
        if row["acceptedForAggregation"] and row["contributesRealSessionEvidence"]
    )
    claim_issues = sum(1 for row in rows if "claim_boundary_confusion" in row["frictionClasses"])
    minimum = pilot["pilotProtocol"]["minimumSessions"]
    target = pilot["pilotProtocol"]["targetSessions"]
    return {
        "totalLocalRowCount": len(rows),
        "acceptedRealSessionCount": accepted_real,
        "claimBoundaryIssueCount": claim_issues,
        "minimumRealSessions": minimum,
        "targetRealSessions": target,
        "pilotEvidenceReady": accepted_real >= minimum,
        "expansionEvidenceReady": False,
        "qualityClaimAllowed": False,
        "hostedRuntimeAllowed": False,
        "generatedTypesEvidenceReady": False,
    }


def local_friction_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        if not row["contributesRealSessionEvidence"]:
            continue
        for friction_class in row["frictionClasses"]:
            counter[friction_class] += 1
    return [
        {
            "frictionClass": key,
            "realSessionSignalCount": counter[key],
        }
        for key in sorted(counter)
    ]


def local_ledger_document(
    rows: list[dict[str, Any]],
    *,
    local_ledger_path: Path,
    generated_at: str | None = None,
) -> dict[str, Any]:
    return {
        "localPilotEvidenceLedgerId": "pilotevidencelocalledger-001",
        "generatedAt": generated_at or utc_now(),
        "ledgerMode": "ignored_local_pilot_evidence_ledger",
        "localLedgerPath": local_ledger_path_label(local_ledger_path),
        "caseRows": rows,
        "summary": aggregate_local_rows(rows),
        "warnings": [
            "This ignored local ledger can contain real supervised session summaries after moderator approval.",
            "Do not commit this file; .ope/live/ is ignored by git.",
            "Rows remain product/adoption evidence, not forecast-quality or calibration evidence.",
        ],
    }


def write_local_pilot_rows(rows: list[dict[str, Any]], *, local_ledger_path: Path) -> None:
    local_ledger_path.parent.mkdir(parents=True, exist_ok=True)
    payload = local_ledger_document(rows, local_ledger_path=local_ledger_path)
    local_ledger_path.write_text(render_json(payload), encoding="utf-8")


def validate_append_plan(plan: dict[str, Any]) -> None:
    errors = validate_record(plan, LOCAL_APPEND_SCHEMA)
    if errors:
        raise PilotEvidenceLedgerError(f"pilot evidence append plan schema validation failed: {errors[0]}")
    boundary = plan["executionBoundary"]
    if boundary["writesCheckedFixtures"] is not False:
        raise PilotEvidenceLedgerError("append plan must not write checked fixtures")
    for key in (
        "recordsRawTranscripts",
        "storesPrivateData",
        "storesCredentials",
        "storesPromptLogs",
        "storesParticipantIdentity",
        "createsForecastArtifacts",
        "startsHostedRuntime",
        "fetchesLiveData",
        "unblocksExpansion",
        "qualityClaimsUpgraded",
        "calibrationClaimsUpgraded",
    ):
        if boundary[key] is not False:
            raise PilotEvidenceLedgerError(f"append plan boundary {key} should be false")


def build_local_pilot_evidence_append_plan(
    input_summary: Path,
    *,
    write_local: bool = False,
    local_ledger_path: Path | None = None,
) -> dict[str, Any]:
    path = Path(input_summary)
    local_path = local_ledger_path or LOCAL_PILOT_LEDGER
    submission, intake_result = load_summary_submission(path)
    input_ref = path.name
    candidate: dict[str, Any] | None = None
    append_decision = "blocked_by_intake"
    ledger_rows_written = 0
    real_sessions_recorded = 0
    contributes_real_session = False

    if intake_result["ledgerReady"] and intake_result["candidateRealSessionEvidence"]:
        candidate = candidate_row_from_summary(submission, intake_result, input_ref=input_ref)
        validate_local_case_row(candidate)
        append_decision = "ready_for_local_write"

    if write_local and candidate is not None:
        _, existing_rows = load_local_pilot_rows(local_path)
        if any(row["sourceSummaryId"] == candidate["sourceSummaryId"] for row in existing_rows):
            append_decision = "already_recorded"
            rows = existing_rows
        else:
            append_decision = "written_to_local_ledger"
            rows = [*existing_rows, candidate]
            write_local_pilot_rows(rows, local_ledger_path=local_path)
            ledger_rows_written = 1
        real_sessions_recorded = aggregate_local_rows(rows)["acceptedRealSessionCount"]
        contributes_real_session = True

    plan = {
        "pilotEvidenceAppendPlanId": "pilotevidenceappendplan-001",
        "generatedAt": utc_now() if write_local else GENERATED_AT,
        "appendMode": "local_pilot_summary_append_plan",
        "inputRef": input_ref,
        "inputSummaryId": intake_result["inputSummaryId"],
        "intakeDecision": intake_result["intakeDecision"],
        "appendDecision": append_decision,
        "localLedgerPath": local_ledger_path_label(local_path),
        "writeLocalRequired": candidate is not None,
        "writeLocalRequested": write_local,
        "candidateRealSessionEvidence": candidate is not None,
        "contributesRealSessionEvidence": contributes_real_session,
        "ledgerRowsWritten": ledger_rows_written,
        "realSessionsRecorded": real_sessions_recorded,
        "candidateRow": candidate,
        "executionBoundary": append_execution_boundary(writes_local=write_local and ledger_rows_written == 1),
        "warnings": [
            "Dry-run append plans do not write pilot evidence or count real sessions.",
            "Use --write-local only after moderator review confirms the summary is sanitized.",
            "Local pilot evidence is stored under .ope/live/ and must not be committed.",
            "Local pilot evidence informs adoption findings only; it does not upgrade forecast quality or calibration claims.",
        ],
    }
    validate_append_plan(plan)
    return plan


def build_local_pilot_evidence_readback(
    *,
    local_ledger_path: Path | None = None,
) -> dict[str, Any]:
    local_path = local_ledger_path or LOCAL_PILOT_LEDGER
    status, rows = load_local_pilot_rows(local_path)
    readback = {
        "pilotEvidenceLocalReadbackId": "pilotevidencelocalreadback-001",
        "generatedAt": GENERATED_AT,
        "readMode": "ignored_local_pilot_evidence_ledger",
        "localLedgerPath": local_ledger_path_label(local_path),
        "localLedgerStatus": status,
        "caseRows": rows,
        "summary": aggregate_local_rows(rows),
        "frictionSummary": local_friction_summary(rows),
        "executionBoundary": local_readback_boundary(),
        "warnings": [
            "This readback inspects ignored local pilot evidence only when explicitly requested.",
            "Missing local evidence keeps real-session counts at zero.",
            "Accepted local sessions do not upgrade quality, calibration, hosted runtime, or generated-type claims.",
        ],
    }
    errors = validate_record(readback, LOCAL_READBACK_SCHEMA)
    if errors:
        raise PilotEvidenceLedgerError(f"pilot evidence local readback schema validation failed: {errors[0]}")
    return readback


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one pilot evidence case")
    parser.add_argument(
        "--section",
        choices=["policy", "cases", "summary", "next-actions", "boundary"],
        help="print one pilot evidence ledger section",
    )
    parser.add_argument(
        "--input-summary",
        help="classify one sanitized pilot summary and print a local ledger append plan",
    )
    parser.add_argument(
        "--write-local",
        action="store_true",
        help="append an accepted sanitized summary to the ignored local pilot evidence ledger",
    )
    parser.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="read ignored local pilot evidence instead of the checked synthetic ledger",
    )
    parser.add_argument("--check", action="store_true", help="check generated pilot evidence ledger drift")
    parser.add_argument("--write", action="store_true", help="refresh generated pilot evidence ledger")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.input_summary:
            if args.case or args.section or args.check or args.write or args.rebuild or args.from_local_ledger:
                raise PilotEvidenceLedgerError("--input-summary can only be combined with --write-local")
            sys.stdout.write(render_json(build_local_pilot_evidence_append_plan(Path(args.input_summary), write_local=args.write_local)))
            return
        if args.write_local:
            raise PilotEvidenceLedgerError("--write-local requires --input-summary")
        if args.from_local_ledger:
            readback = build_local_pilot_evidence_readback()
            if args.case or args.check or args.write or args.rebuild:
                raise PilotEvidenceLedgerError("--from-local-ledger can only be combined with --section")
            if args.section == "summary":
                payload: Any = readback["summary"]
            elif args.section == "cases":
                payload = readback["caseRows"]
            elif args.section == "boundary":
                payload = readback["executionBoundary"]
            elif args.section:
                raise PilotEvidenceLedgerError(f"--from-local-ledger does not expose section {args.section}")
            else:
                payload = readback
            sys.stdout.write(render_json(payload))
            return
        if args.write or args.check or args.rebuild:
            ledger = build_pilot_evidence_ledger()
        else:
            ledger = load_generated_ledger() or build_pilot_evidence_ledger()
    except PilotEvidenceLedgerError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_ledger(ledger)
    elif args.check:
        check_ledger(ledger)
    elif args.case:
        sys.stdout.write(render_json(case(ledger, args.case)))
    elif args.section:
        sys.stdout.write(render_json(section(ledger, args.section)))
    else:
        sys.stdout.write(render_json(summary(ledger)))


if __name__ == "__main__":
    main()
