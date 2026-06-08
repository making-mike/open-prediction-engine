#!/usr/bin/env python3
"""Check pilot summary intake classifier invariants."""

from __future__ import annotations

from generate_pilot_summary_intake import (
    CASE_ORDER,
    PILOT_SUMMARY_INPUT_FIXTURES,
    build_pilot_summary_intake,
    classify_summary_file,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    intake = build_pilot_summary_intake()
    cases = {item["caseKey"]: item for item in intake["submissionCases"]}
    summary = intake["summary"]
    boundary = intake["executionBoundary"]

    require(intake["intakeMode"] == "checked_sanitized_pilot_summary_intake_classifier", "intake mode drifted")
    require(intake["bindings"]["agentPilotValidationId"] == "agentpilotvalidation-001", "pilot validation binding drifted")
    require(intake["bindings"]["pilotEvidenceLedgerId"] == "pilotevidenceledger-001", "pilot evidence binding drifted")
    require(intake["bindings"]["pilotSessionPacketId"] == "pilotsessionpacket-001", "pilot session packet binding drifted")
    require(intake["bindings"]["pilotEvidencePolicyId"] == "pilotevidencepolicy-001", "pilot evidence policy binding drifted")
    require(intake["bindings"]["pilotSessionReviewId"] == "pilotsessionreview-001", "pilot session review binding drifted")
    require([item["caseKey"] for item in intake["submissionCases"]] == CASE_ORDER, "pilot summary case order drifted")

    require(cases["accepted_local_setup_summary"]["ledgerReady"] is True, "local setup summary should be ledger-ready")
    require(cases["accepted_claim_confusion_summary"]["intakeDecision"] == "accept_with_product_signal", "claim confusion should be product signal")
    require(cases["needs_redaction_source_detail"]["intakeDecision"] == "needs_redaction", "source-detail case should require redaction")
    require(cases["blocked_raw_transcript"]["riskSignals"]["rawTranscriptDetected"] is True, "raw transcript signal should block")
    require(cases["blocked_private_rows"]["riskSignals"]["privateRowsDetected"] is True, "private row signal should block")
    require(cases["blocked_private_rows"]["riskSignals"]["credentialLikeTextDetected"] is True, "credential signal should block")
    require(cases["blocked_quality_claim"]["riskSignals"]["claimOverreachDetected"] is True, "claim overreach should block")

    for row in intake["submissionCases"]:
        require(row["contributesRealSessionEvidence"] is False, "checked examples must not count as real sessions")
        if row["ledgerReady"]:
            require(row["acceptedForAggregation"] is True, "ledger-ready examples should aggregate after review")
        else:
            require(row["acceptedForAggregation"] is False, "non-ready examples should not aggregate")

    require(summary["totalCaseCount"] == 6, "summary case count drifted")
    require(summary["acceptedLedgerReadyCount"] == 2, "accepted ledger-ready count drifted")
    require(summary["needsRedactionCount"] == 1, "needs-redaction count drifted")
    require(summary["blockedCaseCount"] == 3, "blocked case count drifted")
    require(summary["realSessionsRecorded"] == 0, "intake must not record real sessions")
    require(summary["ledgerRowsWritten"] == 0, "intake must not write ledger rows")
    require(summary["intakeStatus"] == "ready_for_sanitized_real_summaries", "intake status drifted")
    require(summary["expansionEvidenceReady"] is False, "intake must not unblock expansion")
    require(summary["qualityClaimAllowed"] is False, "intake must not allow quality claims")
    require(summary["hostedRuntimeAllowed"] is False, "intake must not allow hosted runtime")

    require(boundary["readOnlyClassifier"] is True, "classifier should be read-only")
    require(boundary["usesCheckedExamplesOnly"] is True, "classifier should use checked examples")
    for key, value in boundary.items():
        if key in {"readOnlyClassifier", "usesCheckedExamplesOnly"}:
            continue
        require(value is False, f"execution boundary {key} should remain false")

    accepted_input = classify_summary_file(
        PILOT_SUMMARY_INPUT_FIXTURES / "accepted-setup-engine-summary.json"
    )
    blocked_input = classify_summary_file(
        PILOT_SUMMARY_INPUT_FIXTURES / "blocked-raw-transcript-summary.json"
    )

    require(
        accepted_input["intakeDecision"] == "accept_for_ledger_review",
        "accepted sanitized input should be accepted for ledger review",
    )
    require(accepted_input["ledgerReady"] is True, "accepted sanitized input should be ledger-ready")
    require(
        accepted_input["candidateRealSessionEvidence"] is True,
        "accepted sanitized input should be marked as candidate real-session evidence",
    )
    require(
        accepted_input["contributesRealSessionEvidence"] is False,
        "input classification should not count real evidence before ledger review",
    )
    require(accepted_input["ledgerRowsWritten"] == 0, "input classification must not write ledger rows")

    require(
        blocked_input["intakeDecision"] == "block_raw_transcript",
        "raw transcript input should be blocked",
    )
    require(blocked_input["ledgerReady"] is False, "blocked input should not be ledger-ready")
    require(
        blocked_input["candidateRealSessionEvidence"] is False,
        "blocked input should not be candidate real-session evidence",
    )
    require(blocked_input["ledgerRowsWritten"] == 0, "blocked input classification must not write ledger rows")

    print("checked pilot summary intake")


if __name__ == "__main__":
    main()
