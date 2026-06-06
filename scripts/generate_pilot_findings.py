#!/usr/bin/env python3
"""Generate or check the pilot findings readback."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spec" / "fixtures" / "generated" / "pilot-findings" / "ope-pilot-findings.generated.json"
SCHEMA = SPEC / "pilot-findings.schema.json"
GENERATED_AT = "2026-06-05T15:50:00Z"
PILOT_EVIDENCE = ROOT / "spec" / "fixtures" / "generated" / "pilot-evidence" / "ope-pilot-evidence-ledger.generated.json"
PILOT_SUMMARY_INTAKE = ROOT / "spec" / "fixtures" / "generated" / "pilot-summary-intake" / "ope-pilot-summary-intake.generated.json"
PILOT_SESSION_PACKET = ROOT / "spec" / "fixtures" / "generated" / "pilot-session-packet" / "ope-pilot-session-packet.generated.json"
SIMULATED_AGENT_PILOT = (
    ROOT / "spec" / "fixtures" / "generated" / "simulated-agent-pilot" / "ope-simulated-agent-pilot.generated.json"
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_records() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if PILOT_EVIDENCE.exists():
        ledger = load_json(PILOT_EVIDENCE)
    else:
        from generate_pilot_evidence_ledger import build_pilot_evidence_ledger

        ledger = build_pilot_evidence_ledger()

    if PILOT_SUMMARY_INTAKE.exists():
        summary_intake = load_json(PILOT_SUMMARY_INTAKE)
    else:
        from generate_pilot_summary_intake import build_pilot_summary_intake

        summary_intake = build_pilot_summary_intake()

    if PILOT_SESSION_PACKET.exists():
        packet = load_json(PILOT_SESSION_PACKET)
    else:
        from generate_pilot_session_packet import build_pilot_session_packet

        packet = build_pilot_session_packet()

    if SIMULATED_AGENT_PILOT.exists():
        simulated = load_json(SIMULATED_AGENT_PILOT)
    else:
        from generate_simulated_agent_pilot import build_simulated_agent_pilot

        simulated = build_simulated_agent_pilot()

    return ledger, summary_intake, packet, simulated


def friction_summary(ledger: dict[str, Any], simulated: dict[str, Any]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in ledger["caseRows"]:
        for friction_class in row["frictionClasses"]:
            counter[friction_class] += 1
    simulated_counter: Counter[str] = Counter()
    for session in simulated["simulatedSessions"]:
        for friction_class in session["frictionClasses"]:
            simulated_counter[friction_class] += 1
    interpretations = {
        "claim_boundary_confusion": "Synthetic and simulated examples show claim-copy and retrospective-proof warnings still need real pilot validation.",
        "privacy_redaction_needed": "Synthetic and simulated examples show sanitization review is required before evidence can count.",
        "readback_navigation": "Synthetic and simulated examples suggest agents may need clearer card, bundle, and scoped readback routing.",
        "source_runtime_gap": "Simulated examples identify source-runtime gaps without unblocking private-source execution.",
        "none": "Accepted synthetic and simulated examples show the intended path, but they are not real-session evidence.",
    }
    return [
        {
            "frictionClass": key,
            "syntheticSignalCount": counter[key],
            "simulatedAgentSignalCount": simulated_counter[key],
            "realSessionSignalCount": 0,
            "interpretation": interpretations.get(key, "Non-real signal; wait for real sanitized sessions."),
        }
        for key in sorted(set(counter) | set(simulated_counter))
    ]


def next_actions() -> list[dict[str, str]]:
    return [
        {
            "actionKey": "review_simulated_agent_pilot",
            "status": "completed_agent_only_simulation",
            "command": "python3 scripts/ope.py simulated-agent-pilot --section summary",
            "reason": "Five user-authorized simulated sessions now cover accepted, clarification, blocked, rejected, and response-too-large outcomes.",
        },
        {
            "actionKey": "run_supervised_sessions",
            "status": "required",
            "command": "python3 scripts/ope.py pilot-session-packet",
            "reason": "Three to five supervised sessions are still required before adoption findings can be accepted.",
        },
        {
            "actionKey": "classify_sanitized_summaries",
            "status": "required_after_session",
            "command": "python3 scripts/ope.py pilot-summary-intake",
            "reason": "Only sanitized summaries that pass intake review may become real pilot evidence.",
        },
        {
            "actionKey": "keep_expansion_blocked",
            "status": "active_boundary",
            "command": "python3 scripts/ope.py expansion-readiness",
            "reason": "Zero real sessions means hosted runtime, broader private sources, generated types, and stronger methods remain blocked or deferred.",
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "rawTranscriptsStored": False,
        "privateDataStored": False,
        "credentialValuesStored": False,
        "hostProjectSecretsStored": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
        "hostedRuntimeUnblocked": False,
        "generatedTypesUnblocked": False,
    }


def build_pilot_findings() -> dict[str, Any]:
    ledger, summary_intake, packet, simulated = upstream_records()
    ledger_summary = ledger["summary"]
    simulated_summary = simulated["summary"]
    real_count = ledger_summary["acceptedRealSessionCount"]
    simulated_count = simulated_summary["simulatedSessionCount"]
    minimum = ledger_summary["minimumRealSessions"]
    target = ledger_summary["targetRealSessions"]
    evidence_ready = real_count >= minimum
    simulation_ready = simulated_count >= target
    status = "ready_for_review" if evidence_ready else "real_sessions_needed"
    if simulation_ready and not evidence_ready:
        status = "agent_simulation_completed_real_sessions_needed"
    return {
        "pilotFindingsId": "pilotfindings-001",
        "generatedAt": GENERATED_AT,
        "findingsStatus": status,
        "realSessionCount": real_count,
        "simulatedAgentSessionCount": simulated_count,
        "minimumRealSessions": minimum,
        "targetRealSessions": target,
        "sourceRecords": {
            "pilotEvidenceLedgerId": ledger["pilotEvidenceLedgerId"],
            "pilotSummaryIntakeId": summary_intake["pilotSummaryIntakeId"],
            "pilotSessionPacketId": packet["pilotSessionPacketId"],
            "simulatedAgentPilotId": simulated["simulatedAgentPilotId"],
        },
        "frictionSummary": friction_summary(ledger, simulated),
        "nextActions": next_actions(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "acceptedRealSessionCount": real_count,
            "acceptedSimulatedAgentSessionCount": simulated_count,
            "minimumRealSessions": minimum,
            "targetRealSessions": target,
            "agentSimulationEvidenceReady": simulation_ready,
            "pilotEvidenceReady": evidence_ready,
            "expansionEvidenceReady": False,
            "generatedTypesEvidenceReady": False,
            "qualityClaimAllowed": False,
            "hostedRuntimeAllowed": False,
        },
    }


def validate_pilot_findings(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise AssertionError(f"pilot findings validation failed: {errors[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--section",
        choices=["summary", "friction", "next-actions", "boundary"],
        help="print one pilot findings section",
    )
    args = parser.parse_args()

    record = build_pilot_findings()
    validate_pilot_findings(record)
    rendered = render_json(record)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered, encoding="utf-8")
        print(f"generated {OUT.relative_to(ROOT)}")
        return
    if args.check:
        if not OUT.exists():
            raise SystemExit(f"missing generated pilot findings: {OUT}")
        current = OUT.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(f"pilot findings drift: {OUT}\nrun `python3 scripts/generate_pilot_findings.py --write`")
        print("checked pilot findings")
        return

    if args.section == "summary":
        payload: Any = record["summary"]
    elif args.section == "friction":
        payload = record["frictionSummary"]
    elif args.section == "next-actions":
        payload = record["nextActions"]
    elif args.section == "boundary":
        payload = record["executionBoundary"]
    else:
        payload = record
    print(json.dumps(payload, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
