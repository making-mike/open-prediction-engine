#!/usr/bin/env python3
"""Check sanitized pilot evidence ledger invariants."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from generate_pilot_evidence_ledger import (
    CASE_ORDER,
    build_local_pilot_evidence_append_plan,
    build_local_pilot_evidence_readback,
    build_pilot_evidence_ledger,
)


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "accepted-setup-engine-summary.json"
BLOCKED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "blocked-raw-transcript-summary.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    ledger = build_pilot_evidence_ledger()
    cases = {item["caseKey"]: item for item in ledger["caseRows"]}
    summary = ledger["summary"]
    boundary = ledger["executionBoundary"]

    require(ledger["ledgerMode"] == "checked_sanitized_pilot_summary_intake", "ledger mode drifted")
    require(ledger["bindings"]["agentPilotValidationId"] == "agentpilotvalidation-001", "pilot validation binding drifted")
    require(ledger["bindings"]["developerAdoptionSurfaceId"] == "developeradoptionsurface-001", "adoption binding drifted")
    require([item["caseKey"] for item in ledger["caseRows"]] == CASE_ORDER, "pilot evidence case order drifted")

    require(cases["accepted_sanitized_summary"]["intakeStatus"] == "accepted_for_aggregation", "accepted case status drifted")
    require(cases["accepted_sanitized_summary"]["acceptedForAggregation"] is True, "accepted case should aggregate")
    require(cases["needs_redaction"]["intakeStatus"] == "needs_redaction", "redaction case status drifted")
    require(cases["raw_transcript_blocked"]["inputSignals"]["rawTranscriptSubmitted"] is True, "raw transcript case should flag raw input")
    require(cases["private_data_blocked"]["inputSignals"]["privateDataSubmitted"] is True, "private data case should flag private input")
    require(cases["private_data_blocked"]["inputSignals"]["credentialLikeTextSubmitted"] is True, "private data case should flag credentials")
    require(cases["claim_boundary_confusion"]["inputSignals"]["claimConfusionObserved"] is True, "claim confusion case should flag confusion")
    require(cases["claim_boundary_confusion"]["acceptedForAggregation"] is True, "claim confusion case should be aggregateable as a product signal")

    for row in ledger["caseRows"]:
        require(row["contributesRealSessionEvidence"] is False, "checked cases must not count as real sessions")
        privacy = row["privacyChecks"]
        require(privacy["rawTranscriptStored"] is False, "raw transcripts must not be stored")
        require(privacy["privateDataStored"] is False, "private data must not be stored")
        require(privacy["credentialsStored"] is False, "credentials must not be stored")
        require(privacy["promptLogStored"] is False, "prompt logs must not be stored")
        require(privacy["participantIdentityStored"] is False, "participant identity must not be stored")

    require(summary["totalCaseCount"] == 5, "summary case count drifted")
    require(summary["acceptedSyntheticSummaryCount"] == 2, "accepted synthetic count drifted")
    require(summary["acceptedRealSessionCount"] == 0, "real session count must remain zero")
    require(summary["blockedCaseCount"] == 2, "blocked case count drifted")
    require(summary["needsRedactionCount"] == 1, "needs-redaction count drifted")
    require(summary["claimBoundaryIssueCount"] == 1, "claim-boundary issue count drifted")
    require(summary["pilotEvidenceStatus"] == "real_sessions_needed", "pilot evidence status drifted")
    require(summary["expansionEvidenceReady"] is False, "pilot evidence must not unblock expansion")
    require(summary["qualityClaimAllowed"] is False, "pilot evidence must not allow quality claims")
    require(summary["hostedRuntimeAllowed"] is False, "pilot evidence must not allow hosted runtime")
    require(summary["generatedTypesEvidenceReady"] is False, "generated type evidence must not be ready")

    require(boundary["readOnlyLedger"] is True, "ledger should be read-only")
    require(boundary["usesSyntheticCheckedExamplesOnly"] is True, "ledger should use synthetic examples only")
    require(boundary["declaresFutureRealSummaryIntake"] is True, "ledger should declare future real summary intake")
    for key, value in boundary.items():
        if key in {"readOnlyLedger", "usesSyntheticCheckedExamplesOnly", "declaresFutureRealSummaryIntake"}:
            continue
        require(value is False, f"execution boundary {key} should remain false")

    accepted_plan = build_local_pilot_evidence_append_plan(ACCEPTED_SUMMARY)
    require(accepted_plan["appendDecision"] == "ready_for_local_write", "accepted summary should produce local write plan")
    require(accepted_plan["inputSummaryId"] == "pilotsummaryinput-001", "accepted append plan summary id drifted")
    require(accepted_plan["writeLocalRequired"] is True, "accepted append plan should require explicit local write")
    require(accepted_plan["writeLocalRequested"] is False, "accepted append plan should be dry-run by default")
    require(accepted_plan["candidateRealSessionEvidence"] is True, "accepted append plan should identify candidate evidence")
    require(accepted_plan["contributesRealSessionEvidence"] is False, "dry-run append plan must not count evidence")
    require(accepted_plan["ledgerRowsWritten"] == 0, "dry-run append plan must not write rows")
    require(accepted_plan["realSessionsRecorded"] == 0, "dry-run append plan must not record sessions")
    require(accepted_plan["candidateRow"]["contributesRealSessionEvidence"] is True, "candidate row should be a real-session row if written")
    require(accepted_plan["candidateRow"]["sourceSummaryId"] == "pilotsummaryinput-001", "candidate row summary id drifted")
    require("parallel_risk_engine_confusion" not in accepted_plan["candidateRow"]["frictionClasses"], "fixture friction class drifted")

    blocked_plan = build_local_pilot_evidence_append_plan(BLOCKED_SUMMARY)
    require(blocked_plan["appendDecision"] == "blocked_by_intake", "blocked summary should not produce a local write plan")
    require(blocked_plan["candidateRealSessionEvidence"] is False, "blocked append plan should not mark candidate evidence")
    require(blocked_plan["candidateRow"] is None, "blocked append plan should not expose a candidate row")
    require(blocked_plan["ledgerRowsWritten"] == 0, "blocked append plan must not write rows")
    require(blocked_plan["realSessionsRecorded"] == 0, "blocked append plan must not record sessions")

    with TemporaryDirectory() as tmp:
        local_ledger = Path(tmp) / "pilot-evidence-ledger.json"
        first_write = build_local_pilot_evidence_append_plan(
            ACCEPTED_SUMMARY,
            write_local=True,
            local_ledger_path=local_ledger,
        )
        second_write = build_local_pilot_evidence_append_plan(
            ACCEPTED_SUMMARY,
            write_local=True,
            local_ledger_path=local_ledger,
        )
        local_readback = build_local_pilot_evidence_readback(local_ledger_path=local_ledger)
        require(first_write["appendDecision"] == "written_to_local_ledger", "first local write should append")
        require(first_write["ledgerRowsWritten"] == 1, "first local write should write one row")
        require(first_write["realSessionsRecorded"] == 1, "first local write should record one session")
        require(second_write["appendDecision"] == "already_recorded", "duplicate local write should be idempotent")
        require(second_write["ledgerRowsWritten"] == 0, "duplicate local write should not append")
        require(second_write["realSessionsRecorded"] == 1, "duplicate local write should preserve one session")
        require(local_readback["localLedgerStatus"] == "readable", "local readback should read temp ledger")
        require(local_readback["summary"]["acceptedRealSessionCount"] == 1, "local readback should count one accepted session")
        require(local_readback["summary"]["pilotEvidenceReady"] is False, "one local session should not satisfy pilot minimum")
        require(local_readback["summary"]["qualityClaimAllowed"] is False, "local readback must not allow quality claims")

    print("checked pilot evidence ledger")


if __name__ == "__main__":
    main()
