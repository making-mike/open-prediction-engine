#!/usr/bin/env python3
"""Generate or check a read-only pilot summary review bundle."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_pilot_evidence_ledger import build_local_pilot_evidence_append_plan
from generate_pilot_summary_intake import classify_summary_file
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-summary-review"
OUTPUT_PATH = GENERATED / "ope-pilot-summary-review.generated.json"
SCHEMA = SPEC / "pilot-summary-review.schema.json"
DEFAULT_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "accepted-setup-engine-summary.json"
GENERATED_AT = "2026-06-11T10:00:00Z"
SECTION_NAMES = [
    "summary",
    "classification",
    "append-plan",
    "decision",
    "commands",
    "boundary",
    "warnings",
]


class PilotSummaryReviewError(Exception):
    pass


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


def input_label(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def operator_commands(input_path: Path, *, can_append: bool) -> list[dict[str, Any]]:
    label = input_label(input_path)
    commands = [
        command_step(
            1,
            "classify_summary",
            f"python3 scripts/ope.py pilot-summary-intake --input {label}",
            "Classify the sanitized summary without writing evidence.",
        ),
        command_step(
            2,
            "dry_run_append",
            f"python3 scripts/ope.py pilot-evidence --input-summary {label}",
            "Inspect the local append plan without writing the ignored ledger.",
        ),
        command_step(
            3,
            "review_summary",
            f"python3 scripts/ope.py pilot-summary-review --input {label} --section summary",
            "Confirm whether moderator-approved --write-local append is allowed.",
        ),
    ]
    if can_append:
        commands.append(
            command_step(
                4,
                "write_local_append",
                f"python3 scripts/ope.py pilot-evidence --input-summary {label} --write-local",
                "Append only after moderator approval confirms the summary is sanitized.",
                mutates_local_state=True,
            )
        )
        commands.extend(
            [
                command_step(
                    5,
                    "review_findings",
                    "python3 scripts/ope.py pilot-findings --from-local-ledger --section summary",
                    "Review ignored local pilot findings after append.",
                ),
                command_step(
                    6,
                    "review_status",
                    "python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary",
                    "Confirm remaining real-session count and blocked claim boundaries.",
                ),
            ]
        )
    else:
        commands.append(
            command_step(
                4,
                "return_for_redaction",
                "python3 scripts/ope.py pilot-summary-template --section draft",
                "Use a fresh draft shape to replace blocked or redaction-needed material.",
            )
        )
    return commands


def execution_boundary() -> dict[str, bool]:
    return {
        "readOnlyReview": True,
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": False,
        "recordsRealSessions": False,
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
        "generatedTypesUnblocked": False,
    }


def review_decision(classification: dict[str, Any], append_plan: dict[str, Any]) -> dict[str, Any]:
    can_append = append_plan["appendDecision"] == "ready_for_local_write"
    needs_redaction = classification["intakeDecision"] == "needs_redaction"
    blocked = append_plan["appendDecision"] == "blocked_by_intake" and not needs_redaction
    if can_append:
        next_action = "Moderator may run the explicit --write-local append after confirming the summary remains sanitized."
    elif needs_redaction:
        next_action = "Redact or complete the summary, then re-run pilot-summary-review before any append."
    else:
        next_action = "Do not append this summary; replace blocked material with a sanitized summary draft."
    return {
        "canAppendWithWriteLocal": can_append,
        "blockedByIntake": blocked,
        "needsRedaction": needs_redaction,
        "requiresModeratorApproval": can_append,
        "nextAction": next_action,
    }


def summary(classification: dict[str, Any], append_plan: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "inputSummaryId": classification["inputSummaryId"],
        "intakeDecision": classification["intakeDecision"],
        "appendDecision": append_plan["appendDecision"],
        "ledgerReady": classification["ledgerReady"],
        "canAppendWithWriteLocal": decision["canAppendWithWriteLocal"],
        "candidateRealSessionEvidence": append_plan["candidateRealSessionEvidence"],
        "contributesRealSessionEvidence": append_plan["contributesRealSessionEvidence"],
        "writeLocalRequired": append_plan["writeLocalRequired"],
        "writeLocalRequested": append_plan["writeLocalRequested"],
        "ledgerRowsWritten": append_plan["ledgerRowsWritten"],
        "realSessionsRecorded": append_plan["realSessionsRecorded"],
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "hostedRuntimeAllowed": False,
        "generatedTypesEvidenceReady": False,
        "expansionEvidenceReady": False,
    }


def build_pilot_summary_review(input_summary: Path = DEFAULT_SUMMARY) -> dict[str, Any]:
    input_path = Path(input_summary)
    classification = classify_summary_file(input_path)
    append_plan = build_local_pilot_evidence_append_plan(input_path)
    decision = review_decision(classification, append_plan)
    record = {
        "pilotSummaryReviewId": "pilotsummaryreview-001",
        "generatedAt": GENERATED_AT,
        "reviewMode": "read_only_pilot_summary_review",
        "inputRef": input_label(input_path),
        "inputSummaryId": classification["inputSummaryId"],
        "classification": classification,
        "appendPlan": append_plan,
        "reviewDecision": decision,
        "operatorCommands": operator_commands(input_path, can_append=decision["canAppendWithWriteLocal"]),
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This review is read-only and does not write pilot evidence.",
            "Only explicit moderator-approved --write-local can append accepted sanitized summaries to the ignored local ledger.",
            "Blocked summaries must not be appended or committed.",
            "Pilot usability evidence does not upgrade forecast quality, calibration, hosted runtime, generated types, or expansion claims.",
        ],
        "summary": summary(classification, append_plan, decision),
    }
    validate_pilot_summary_review(record)
    return record


def validate_pilot_summary_review(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PilotSummaryReviewError(f"pilot summary review validation failed: {errors[0]}")
    if record["appendPlan"]["writeLocalRequested"] is not False:
        raise PilotSummaryReviewError("pilot summary review must not request local writes")
    if record["summary"]["ledgerRowsWritten"] != 0 or record["summary"]["realSessionsRecorded"] != 0:
        raise PilotSummaryReviewError("pilot summary review must not write rows or record sessions")
    boundary = record["executionBoundary"]
    if boundary["readOnlyReview"] is not True:
        raise PilotSummaryReviewError("pilot summary review should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyReview":
            continue
        if value is not False:
            raise PilotSummaryReviewError(f"pilot summary review boundary {key} should be false")


def view_payload(record: dict[str, Any], section: str | None) -> Any:
    if section == "summary":
        return record["summary"]
    if section == "classification":
        return record["classification"]
    if section == "append-plan":
        return record["appendPlan"]
    if section == "decision":
        return record["reviewDecision"]
    if section == "commands":
        return record["operatorCommands"]
    if section == "boundary":
        return record["executionBoundary"]
    if section == "warnings":
        return record["warnings"]
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default=str(DEFAULT_SUMMARY),
        help="sanitized pilot summary JSON to review",
    )
    parser.add_argument("--section", choices=SECTION_NAMES, help="print one review section")
    parser.add_argument("--write", action="store_true", help="write generated pilot summary review fixture")
    parser.add_argument("--check", action="store_true", help="check generated pilot summary review drift")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        record = build_pilot_summary_review(Path(args.input))
    except PilotSummaryReviewError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="pilot summary review",
            regen="python3 scripts/generate_pilot_summary_review.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="pilot summary review",
            regen="python3 scripts/generate_pilot_summary_review.py --write",
        )
        return
    print(render_json(view_payload(record, args.section)), end="")


if __name__ == "__main__":
    main()
