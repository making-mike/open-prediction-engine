#!/usr/bin/env python3
"""Generate or check the supervised pilot operator status readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_pilot_evidence_ledger import LOCAL_PILOT_LEDGER
from generate_pilot_findings import build_pilot_findings
from generate_pilot_session_packet import build_pilot_session_packet
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "pilot-supervision-status"
OUTPUT_PATH = GENERATED / "ope-pilot-supervision-status.generated.json"
SCHEMA = SPEC / "pilot-supervision-status.schema.json"
GENERATED_AT = "2026-06-10T12:30:00Z"
RECOMMENDED_SCENARIO_KEY = "engine_setup_shortcut_comprehension"
RECOMMENDED_TASK_COMMAND = "python3 scripts/ope.py pilot-session-packet --task engine_setup_shortcut_comprehension"

SECTION_NAMES = [
    "summary",
    "progress",
    "commands",
    "checks",
    "boundary",
    "warnings",
]


class PilotSupervisionStatusError(Exception):
    pass


def find_task(packet: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    for task in packet["taskCards"]:
        if task["scenarioKey"] == scenario_key:
            return task
    raise PilotSupervisionStatusError(f"missing pilot session task {scenario_key}")


def build_progress(findings_summary: dict[str, Any]) -> dict[str, Any]:
    accepted = findings_summary["acceptedRealSessionCount"]
    minimum = findings_summary["minimumRealSessions"]
    target = findings_summary["targetRealSessions"]
    return {
        "acceptedRealSessionCount": accepted,
        "minimumRealSessions": minimum,
        "targetRealSessions": target,
        "remainingMinimumSessions": max(0, minimum - accepted),
        "remainingTargetSessions": max(0, target - accepted),
        "minimumMet": accepted >= minimum,
        "targetMet": accepted >= target,
    }


def status_from_progress(progress: dict[str, Any]) -> str:
    if progress["targetMet"]:
        return "target_met_review_ready"
    if progress["minimumMet"]:
        return "minimum_met_review_ready"
    return "real_sessions_needed"


def build_recommended_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "taskId": task["taskId"],
        "scenarioKey": task["scenarioKey"],
        "title": task["title"],
        "command": RECOMMENDED_TASK_COMMAND,
        "taskCommand": task["command"],
        "expectedOutcomeClass": task["expectedOutcomeClass"],
        "measures": task["measures"],
        "claimBoundaryRequired": task["ledgerMapping"]["claimBoundaryRequired"],
        "reason": (
            "Real sessions should verify that agents treat OPE as the first setup engine before proposing "
            "a custom lightweight risk engine or audit-only layer."
        ),
    }


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


def build_command_sequence() -> list[dict[str, Any]]:
    return [
        command_step(
            order=1,
            step_key="open_task_packet",
            command=RECOMMENDED_TASK_COMMAND,
            expected_operator_action="Open the checked setup-comprehension task card before the supervised session starts.",
        ),
        command_step(
            order=2,
            step_key="use_agent_guide",
            command="python3 scripts/ope.py agent-guide --section generic",
            expected_operator_action="Keep the generic agent guidance loop visible before narrowing to an example domain.",
        ),
        command_step(
            order=3,
            step_key="classify_summary",
            command="python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
            expected_operator_action="Classify a moderator-approved sanitized summary without writing any evidence row.",
        ),
        command_step(
            order=4,
            step_key="append_local_evidence",
            command="python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
            expected_operator_action="Append only accepted sanitized summaries to the ignored local ledger after explicit approval.",
            mutates_local_state=True,
        ),
        command_step(
            order=5,
            step_key="review_findings",
            command="python3 scripts/ope.py pilot-findings --from-local-ledger --section summary",
            expected_operator_action="Review adoption findings with ignored local evidence included.",
        ),
        command_step(
            order=6,
            step_key="review_status",
            command="python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary",
            expected_operator_action="Confirm remaining real-session count and blocked expansion boundaries.",
        ),
    ]


def evidence_check(
    *,
    check_key: str,
    command: str,
    acceptance: str,
    required: bool = True,
) -> dict[str, Any]:
    return {
        "checkKey": check_key,
        "required": required,
        "command": command,
        "acceptance": acceptance,
    }


def build_evidence_loop_checks() -> list[dict[str, Any]]:
    return [
        evidence_check(
            check_key="sanitized_summary_required",
            command="python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
            acceptance="The intake decision is accept_for_ledger_review or accept_with_product_signal before append.",
        ),
        evidence_check(
            check_key="local_write_explicit",
            command="python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
            acceptance="The operator explicitly requested --write-local after moderator sanitization review.",
        ),
        evidence_check(
            check_key="local_ledger_review",
            command="python3 scripts/ope.py pilot-findings --from-local-ledger --section summary",
            acceptance="Accepted real-session count updates only from ignored local ledger rows.",
        ),
        evidence_check(
            check_key="no_quality_upgrade",
            command="python3 scripts/ope.py expansion-readiness",
            acceptance="Hosted runtime, generated types, stronger methods, calibration, and quality claims remain blocked.",
        ),
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "readOnlyStatus": True,
        "usesCheckedPilotPacket": True,
        "writesCheckedFixtures": False,
        "writesIgnoredLocalLedger": False,
        "recordsRawTranscripts": False,
        "storesPrivateData": False,
        "storesCredentials": False,
        "storesPromptLogs": False,
        "storesParticipantIdentity": False,
        "unblocksExpansion": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
        "hostedRuntimeUnblocked": False,
        "generatedTypesUnblocked": False,
    }


def build_summary(
    *,
    status: str,
    local_mode: str,
    local_status: str,
    local_path: str,
    progress: dict[str, Any],
    recommended_task: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "localEvidenceMode": local_mode,
        "localEvidenceStatus": local_status,
        "localLedgerPath": local_path,
        "acceptedRealSessionCount": progress["acceptedRealSessionCount"],
        "minimumRealSessions": progress["minimumRealSessions"],
        "targetRealSessions": progress["targetRealSessions"],
        "remainingMinimumSessions": progress["remainingMinimumSessions"],
        "remainingTargetSessions": progress["remainingTargetSessions"],
        "minimumMet": progress["minimumMet"],
        "targetMet": progress["targetMet"],
        "recommendedScenarioKey": recommended_task["scenarioKey"],
        "recommendedCommand": recommended_task["command"],
        "pilotEvidenceReady": progress["minimumMet"],
        "expansionEvidenceReady": False,
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "hostedRuntimeAllowed": False,
        "generatedTypesEvidenceReady": False,
    }


def build_pilot_supervision_status(
    *,
    from_local_ledger: bool = False,
    local_ledger_path: Path | None = None,
) -> dict[str, Any]:
    packet = build_pilot_session_packet()
    findings = build_pilot_findings(from_local_ledger=from_local_ledger, local_ledger_path=local_ledger_path)
    findings_summary = findings["summary"]
    progress = build_progress(findings_summary)
    status = status_from_progress(progress)
    recommended_task = build_recommended_task(find_task(packet, RECOMMENDED_SCENARIO_KEY))
    local_mode = findings_summary["localPilotEvidenceMode"]
    local_status = findings_summary["localPilotEvidenceStatus"]
    local_path = findings_summary["localLedgerPath"]
    record = {
        "pilotSupervisionStatusId": "pilotsupervisionstatus-001",
        "generatedAt": GENERATED_AT,
        "status": status,
        "localEvidenceMode": local_mode,
        "localEvidenceStatus": local_status,
        "localLedgerPath": local_path,
        "sourceRecords": findings["sourceRecords"],
        "realSessionProgress": progress,
        "recommendedNextTask": recommended_task,
        "commandSequence": build_command_sequence(),
        "evidenceLoopChecks": build_evidence_loop_checks(),
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This status readback does not run pilot sessions or write local evidence.",
            "Use --from-local-ledger only when intentionally inspecting ignored local pilot evidence.",
            "Do not commit .ope/live pilot evidence; store only sanitized summaries after moderator approval.",
            "Pilot evidence can guide adoption fixes, but it does not upgrade forecast quality, calibration, hosted runtime, or generated-type claims.",
        ],
    }
    record["summary"] = build_summary(
        status=status,
        local_mode=local_mode,
        local_status=local_status,
        local_path=local_path,
        progress=progress,
        recommended_task=recommended_task,
    )
    validate_pilot_supervision_status(record)
    return record


def validate_pilot_supervision_status(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PilotSupervisionStatusError(f"pilot supervision status schema validation failed: {errors[0]}")
    if record["recommendedNextTask"]["scenarioKey"] != RECOMMENDED_SCENARIO_KEY:
        raise PilotSupervisionStatusError("recommended pilot task drifted")
    if record["recommendedNextTask"]["taskId"] != "agentpilottask-006":
        raise PilotSupervisionStatusError("recommended pilot task id drifted")
    progress = record["realSessionProgress"]
    if progress["remainingMinimumSessions"] != max(0, progress["minimumRealSessions"] - progress["acceptedRealSessionCount"]):
        raise PilotSupervisionStatusError("remaining minimum real-session count drifted")
    if progress["remainingTargetSessions"] != max(0, progress["targetRealSessions"] - progress["acceptedRealSessionCount"]):
        raise PilotSupervisionStatusError("remaining target real-session count drifted")
    boundary = record["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyStatus", "usesCheckedPilotPacket"}:
            if value is not True:
                raise PilotSupervisionStatusError(f"execution boundary {key} should be true")
        elif value is not False:
            raise PilotSupervisionStatusError(f"execution boundary {key} should be false")


def load_generated_status() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    record = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_pilot_supervision_status(record)
    return record


def write_status(record: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        record,
        label="pilot supervision status",
        regen="python3 scripts/generate_pilot_supervision_status.py --write",
    )


def check_status(record: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        record,
        label="pilot supervision status",
        regen="python3 scripts/generate_pilot_supervision_status.py --write",
    )


def section(record: dict[str, Any], section_name: str) -> Any:
    if section_name == "summary":
        return record["summary"]
    if section_name == "progress":
        return record["realSessionProgress"]
    if section_name == "commands":
        return record["commandSequence"]
    if section_name == "checks":
        return record["evidenceLoopChecks"]
    if section_name == "boundary":
        return record["executionBoundary"]
    if section_name == "warnings":
        return record["warnings"]
    raise PilotSupervisionStatusError(f"unsupported section {section_name}")


def local_ledger_arg(value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        return ROOT / path
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section",
        choices=SECTION_NAMES,
        help="print one pilot supervision status section",
    )
    parser.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="include ignored local pilot evidence rows from .ope/live",
    )
    parser.add_argument(
        "--local-ledger",
        help=f"override ignored local ledger path for tests or local runs; defaults to {LOCAL_PILOT_LEDGER.relative_to(ROOT)}",
    )
    parser.add_argument("--check", action="store_true", help="check generated pilot supervision status drift")
    parser.add_argument("--write", action="store_true", help="refresh generated pilot supervision status")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()

    try:
        local_path = local_ledger_arg(args.local_ledger)
        if args.write or args.check or args.rebuild or args.from_local_ledger or local_path is not None:
            record = build_pilot_supervision_status(from_local_ledger=args.from_local_ledger, local_ledger_path=local_path)
        else:
            record = load_generated_status() or build_pilot_supervision_status()
    except PilotSupervisionStatusError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    if args.write:
        write_status(record)
    elif args.check:
        check_status(record)
    elif args.section:
        sys.stdout.write(render_json(section(record, args.section)))
    else:
        sys.stdout.write(render_json(record))


if __name__ == "__main__":
    main()
