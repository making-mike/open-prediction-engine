#!/usr/bin/env python3
"""Check sanitized pilot evidence ledger invariants."""

from __future__ import annotations

from generate_pilot_evidence_ledger import CASE_ORDER, build_pilot_evidence_ledger


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

    print("checked pilot evidence ledger")


if __name__ == "__main__":
    main()
