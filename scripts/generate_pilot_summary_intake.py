#!/usr/bin/env python3
"""Generate or check the sanitized pilot-summary intake classifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_agent_pilot_validation import build_agent_pilot_validation
from generate_pilot_evidence_ledger import build_pilot_evidence_ledger
from generate_pilot_session_packet import build_pilot_session_packet
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-summary-intake"
OUTPUT_PATH = GENERATED / "ope-pilot-summary-intake.generated.json"
SCHEMA = SPEC / "pilot-summary-intake.schema.json"
GENERATED_AT = "2026-06-10T12:30:00Z"

CASE_ORDER = [
    "accepted_local_setup_summary",
    "accepted_claim_confusion_summary",
    "needs_redaction_source_detail",
    "blocked_raw_transcript",
    "blocked_private_rows",
    "blocked_quality_claim",
]

SECTION_NAMES = ["policy", "cases", "rules", "summary", "boundary"]


class PilotSummaryIntakeError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def submitted_shape(
    *,
    task_refs: bool = True,
    ratings: bool = True,
    findings: bool = True,
    friction: bool = True,
    signals: bool = True,
    next_action: bool = True,
) -> dict[str, bool]:
    return {
        "hasTaskRefs": task_refs,
        "hasDimensionRatings": ratings,
        "hasSanitizedFindings": findings,
        "hasFrictionClasses": friction,
        "hasExpansionSignals": signals,
        "hasNextAction": next_action,
    }


def risk_signals(
    *,
    raw_transcript: bool = False,
    private_rows: bool = False,
    credentials: bool = False,
    identity: bool = False,
    source_detail: bool = False,
    claim_overreach: bool = False,
) -> dict[str, bool]:
    return {
        "rawTranscriptDetected": raw_transcript,
        "privateRowsDetected": private_rows,
        "credentialLikeTextDetected": credentials,
        "participantIdentityDetected": identity,
        "unredactedSourceDetailDetected": source_detail,
        "claimOverreachDetected": claim_overreach,
    }


def submission_case(
    *,
    index: int,
    case_key: str,
    task_refs: list[str],
    risks: dict[str, bool],
    decision: str,
    ledger_ready: bool,
    accepted: bool,
    review_outcome: str,
    required_fixes: list[str],
    next_action: str,
    shape: dict[str, bool] | None = None,
) -> dict[str, Any]:
    return {
        "caseId": f"pilotsummarycase-{index:03d}",
        "caseKey": case_key,
        "evidenceClass": "checked_intake_example",
        "taskRefs": task_refs,
        "submittedShape": shape or submitted_shape(),
        "riskSignals": risks,
        "intakeDecision": decision,
        "ledgerReady": ledger_ready,
        "acceptedForAggregation": accepted,
        "contributesRealSessionEvidence": False,
        "reviewOutcome": review_outcome,
        "requiredFixes": required_fixes,
        "nextAction": next_action,
    }


def build_submission_cases() -> list[dict[str, Any]]:
    return [
        submission_case(
            index=1,
            case_key="accepted_local_setup_summary",
            task_refs=["agentpilottask-001", "agentpilottask-004"],
            risks=risk_signals(),
            decision="accept_for_ledger_review",
            ledger_ready=True,
            accepted=True,
            review_outcome="Summary has task refs, ratings, sanitized findings, friction classes, expansion signals, and no unsafe signals.",
            required_fixes=[],
            next_action="Submit as a sanitized real-session summary only after moderator review confirms no unsafe details.",
        ),
        submission_case(
            index=2,
            case_key="accepted_claim_confusion_summary",
            task_refs=["agentpilottask-005"],
            risks=risk_signals(),
            decision="accept_with_product_signal",
            ledger_ready=True,
            accepted=True,
            review_outcome="Claim-boundary confusion is safe to aggregate as a product signal when the note stays sanitized.",
            required_fixes=[],
            next_action="Submit as a sanitized product signal and route follow-up toward claim-copy/readback improvements.",
        ),
        submission_case(
            index=3,
            case_key="needs_redaction_source_detail",
            task_refs=["agentpilottask-002"],
            risks=risk_signals(source_detail=True),
            decision="needs_redaction",
            ledger_ready=False,
            accepted=False,
            review_outcome="The summary shape is usable, but unredacted source detail must be removed before ledger review.",
            required_fixes=[
                "Replace source names, table names, and private operational details with generic source-role language.",
                "Re-run sanitization review before any ledger submission.",
            ],
            next_action="Redact source-specific details, then reclassify the summary.",
        ),
        submission_case(
            index=4,
            case_key="blocked_raw_transcript",
            task_refs=["agentpilottask-001"],
            risks=risk_signals(raw_transcript=True),
            decision="block_raw_transcript",
            ledger_ready=False,
            accepted=False,
            review_outcome="Raw transcript text is never ledger-ready and must not be stored in checked fixtures.",
            required_fixes=[
                "Discard transcript text.",
                "Create a new summarized finding with dimension scores and no quoted session content.",
            ],
            next_action="Block intake and request a sanitized summary instead of transcript text.",
        ),
        submission_case(
            index=5,
            case_key="blocked_private_rows",
            task_refs=["agentpilottask-003"],
            risks=risk_signals(private_rows=True, credentials=True, identity=True),
            decision="block_private_data",
            ledger_ready=False,
            accepted=False,
            review_outcome="Private rows, credentials, or participant identity block repository intake.",
            required_fixes=[
                "Discard private details and credential-like text.",
                "Record only the blocked reason, safe next action, and sanitized comprehension signal.",
            ],
            next_action="Block intake and replace the submitted notes with a safe blocked-path summary.",
        ),
        submission_case(
            index=6,
            case_key="blocked_quality_claim",
            task_refs=["agentpilottask-005"],
            risks=risk_signals(claim_overreach=True),
            decision="block_claim_overreach",
            ledger_ready=False,
            accepted=False,
            review_outcome="A summary that claims forecast quality, calibration, hosted readiness, or production runtime maturity is not ledger-ready.",
            required_fixes=[
                "Remove quality, calibration, hosted-runtime, and production-readiness claims.",
                "Reframe the finding as usability evidence or claim-boundary confusion.",
            ],
            next_action="Block intake until the claim language is rewritten as a sanitized product signal.",
        ),
    ]


def build_input_policy(
    *,
    ledger: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    return {
        "policyId": "pilotsummarypolicy-001",
        "allowedFields": packet["evidenceTemplate"]["allowedFields"],
        "blockedSignals": ledger["intakePolicy"]["blockedInputs"],
        "requiredReviewChecks": [
            item["check"]
            for item in packet["sanitizationReview"]["checks"]
        ],
        "acceptedUse": "Ledger-ready summaries can be manually added as real pilot evidence only after review; this checked classifier does not write ledger rows.",
    }


def decision_rule(index: int, condition: str, decision: str, effect: str) -> dict[str, Any]:
    return {
        "ruleId": f"pilotsummaryrule-{index:03d}",
        "condition": condition,
        "decision": decision,
        "effect": effect,
    }


def build_decision_rules() -> list[dict[str, Any]]:
    return [
        decision_rule(
            1,
            "All required summary fields are present and no unsafe signal is detected.",
            "Accept for ledger review.",
            "The summary is ledger-ready after moderator review, but this classifier still records zero real sessions.",
        ),
        decision_rule(
            2,
            "Claim-boundary confusion is described without quality or hosted-runtime overclaiming.",
            "Accept with product signal.",
            "The finding can improve copy and readbacks but cannot count as forecast-quality evidence.",
        ),
        decision_rule(
            3,
            "Unredacted source details appear without raw transcripts or private rows.",
            "Needs redaction.",
            "The summary must be rewritten before ledger review.",
        ),
        decision_rule(
            4,
            "Raw transcripts, recordings, private rows, credentials, prompt logs, or participant identity appear.",
            "Block intake.",
            "Unsafe details must be discarded rather than stored for later cleanup.",
        ),
        decision_rule(
            5,
            "The summary claims calibration, forecast quality, hosted readiness, or production runtime maturity.",
            "Block claim overreach.",
            "The summary must be rewritten as usability evidence before it can be reviewed.",
        ),
    ]


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = sum(1 for item in cases if item["ledgerReady"])
    needs_redaction = sum(1 for item in cases if item["intakeDecision"] == "needs_redaction")
    blocked = sum(1 for item in cases if item["intakeDecision"].startswith("block_"))
    return {
        "totalCaseCount": len(cases),
        "acceptedLedgerReadyCount": accepted,
        "needsRedactionCount": needs_redaction,
        "blockedCaseCount": blocked,
        "realSessionsRecorded": 0,
        "ledgerRowsWritten": 0,
        "intakeStatus": "ready_for_sanitized_real_summaries",
        "expansionEvidenceReady": False,
        "qualityClaimAllowed": False,
        "hostedRuntimeAllowed": False,
    }


def build_pilot_summary_intake() -> dict[str, Any]:
    manifest = build_manifest()
    pilot = build_agent_pilot_validation()
    ledger = build_pilot_evidence_ledger()
    packet = build_pilot_session_packet()
    cases = build_submission_cases()
    intake = {
        "pilotSummaryIntakeId": "pilotsummaryintake-001",
        "generatedAt": GENERATED_AT,
        "intakeMode": "checked_sanitized_pilot_summary_intake_classifier",
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "agentPilotValidationId": pilot["agentPilotValidationId"],
            "pilotEvidenceLedgerId": ledger["pilotEvidenceLedgerId"],
            "pilotSessionPacketId": packet["pilotSessionPacketId"],
            "pilotEvidencePolicyId": ledger["intakePolicy"]["policyId"],
            "pilotSessionReviewId": packet["sanitizationReview"]["reviewId"],
        },
        "inputPolicy": build_input_policy(ledger=ledger, packet=packet),
        "submissionCases": cases,
        "decisionRules": build_decision_rules(),
        "summary": build_summary(cases),
        "executionBoundary": {
            "readOnlyClassifier": True,
            "usesCheckedExamplesOnly": True,
            "runsPilotSessions": False,
            "writesPilotEvidenceLedger": False,
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
            "This classifier contains checked examples only and does not record real pilot sessions.",
            "Ledger-ready means safe for moderator review; it does not automatically write pilot evidence.",
            "Blocked summaries must be discarded or rewritten before repository storage.",
            "Accepted pilot summaries remain usability evidence, not forecast-quality or calibration evidence.",
        ],
    }
    validate_intake(intake)
    return intake


def validate_intake(intake: dict[str, Any]) -> None:
    errors = validate_record(intake, SCHEMA)
    if errors:
        raise PilotSummaryIntakeError(f"pilot summary intake schema validation failed: {errors[0]}")
    cases = intake["submissionCases"]
    if [item["caseKey"] for item in cases] != CASE_ORDER:
        raise PilotSummaryIntakeError("pilot summary case order drifted")
    if intake["bindings"]["pilotSessionPacketId"] != "pilotsessionpacket-001":
        raise PilotSummaryIntakeError("pilot session packet binding drifted")
    if intake["bindings"]["pilotEvidenceLedgerId"] != "pilotevidenceledger-001":
        raise PilotSummaryIntakeError("pilot evidence ledger binding drifted")
    for item in cases:
        if item["contributesRealSessionEvidence"]:
            raise PilotSummaryIntakeError("checked intake examples must not count as real sessions")
        if item["ledgerReady"] and not item["acceptedForAggregation"]:
            raise PilotSummaryIntakeError("ledger-ready examples should be accepted for aggregation")
    blocked = {item["caseKey"] for item in cases if item["intakeDecision"].startswith("block_")}
    if blocked != {"blocked_raw_transcript", "blocked_private_rows", "blocked_quality_claim"}:
        raise PilotSummaryIntakeError("blocked case coverage drifted")
    summary = intake["summary"]
    if summary["realSessionsRecorded"] != 0 or summary["ledgerRowsWritten"] != 0:
        raise PilotSummaryIntakeError("checked intake classifier must not record real sessions or write ledger rows")
    if summary["expansionEvidenceReady"] or summary["qualityClaimAllowed"] or summary["hostedRuntimeAllowed"]:
        raise PilotSummaryIntakeError("pilot summary intake must not unblock expansion, quality claims, or hosted runtime")
    boundary = intake["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyClassifier", "usesCheckedExamplesOnly"}:
            if value is not True:
                raise PilotSummaryIntakeError(f"execution boundary {key} should be true")
        elif value is not False:
            raise PilotSummaryIntakeError(f"execution boundary {key} should be false")


def summary(intake: dict[str, Any]) -> dict[str, Any]:
    return {
        "pilotSummaryIntakeId": intake["pilotSummaryIntakeId"],
        "intakeMode": intake["intakeMode"],
        "bindings": intake["bindings"],
        "summary": intake["summary"],
        "submissionCases": [
            {
                "caseKey": item["caseKey"],
                "intakeDecision": item["intakeDecision"],
                "ledgerReady": item["ledgerReady"],
                "acceptedForAggregation": item["acceptedForAggregation"],
                "contributesRealSessionEvidence": item["contributesRealSessionEvidence"],
                "nextAction": item["nextAction"],
            }
            for item in intake["submissionCases"]
        ],
        "warnings": intake["warnings"],
    }


def section(intake: dict[str, Any], section_name: str) -> Any:
    if section_name == "policy":
        return intake["inputPolicy"]
    if section_name == "cases":
        return intake["submissionCases"]
    if section_name == "rules":
        return intake["decisionRules"]
    if section_name == "summary":
        return intake["summary"]
    if section_name == "boundary":
        return intake["executionBoundary"]
    raise PilotSummaryIntakeError(f"unsupported section {section_name}")


def case(intake: dict[str, Any], case_key: str) -> dict[str, Any]:
    for item in intake["submissionCases"]:
        if item["caseKey"] == case_key:
            return item
    raise PilotSummaryIntakeError(f"unknown pilot summary intake case {case_key}")


def write_intake(intake: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(intake), encoding="utf-8")
    print("generated pilot summary intake")


def check_intake(intake: dict[str, Any]) -> None:
    expected = render_json(intake)
    if not OUTPUT_PATH.exists():
        print(f"missing pilot summary intake: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_pilot_summary_intake.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"pilot summary intake drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_pilot_summary_intake.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked pilot summary intake")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one pilot summary intake case")
    parser.add_argument("--section", choices=SECTION_NAMES, help="print one pilot summary intake section")
    parser.add_argument("--check", action="store_true", help="check generated pilot summary intake drift")
    parser.add_argument("--write", action="store_true", help="refresh generated pilot summary intake")
    args = parser.parse_args()
    try:
        intake = build_pilot_summary_intake()
    except PilotSummaryIntakeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_intake(intake)
    elif args.check:
        check_intake(intake)
    elif args.case:
        sys.stdout.write(render_json(case(intake, args.case)))
    elif args.section:
        sys.stdout.write(render_json(section(intake, args.section)))
    else:
        sys.stdout.write(render_json(summary(intake)))


if __name__ == "__main__":
    main()
