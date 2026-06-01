#!/usr/bin/env python3
"""Check pilot session packet invariants."""

from __future__ import annotations

from generate_pilot_session_packet import build_pilot_session_packet


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    packet = build_pilot_session_packet()
    summary = packet["collectionSummary"]
    boundary = packet["executionBoundary"]
    tasks = {item["scenarioKey"]: item for item in packet["taskCards"]}

    require(packet["packetMode"] == "checked_real_pilot_session_collection_packet", "packet mode drifted")
    require(packet["bindings"]["agentPilotValidationId"] == "agentpilotvalidation-001", "pilot validation binding drifted")
    require(packet["bindings"]["pilotEvidenceLedgerId"] == "pilotevidenceledger-001", "pilot evidence binding drifted")
    require(packet["bindings"]["pilotEvidencePolicyId"] == "pilotevidencepolicy-001", "pilot evidence policy binding drifted")
    require(packet["bindings"]["developerAdoptionSurfaceId"] == "developeradoptionsurface-001", "developer adoption binding drifted")
    require(packet["bindings"]["predictionCampaignExplainId"] == "predictioncampaignexplain-001", "campaign explain binding drifted")

    require(summary["taskCardCount"] == 6, "pilot session packet should expose six task cards")
    require(summary["minimumRealSessions"] == 3, "minimum real session count drifted")
    require(summary["targetRealSessions"] == 5, "target real session count drifted")
    require(summary["realSessionsRecorded"] == 0, "packet must not record real sessions")
    require(summary["packetStatus"] == "ready_for_real_pilot_sessions", "packet status drifted")
    require(summary["ledgerSubmissionReady"] is True, "packet should be ready for sanitized ledger submissions")
    require(summary["expansionEvidenceReady"] is False, "packet must not unblock expansion")
    require(summary["qualityClaimAllowed"] is False, "packet must not allow quality claims")
    require(summary["hostedRuntimeAllowed"] is False, "packet must not allow hosted runtime")

    require(set(tasks) == {
        "local_file_setup_readback",
        "accepted_adapter_output_ready",
        "unsafe_source_block",
        "forecast_run_readback",
        "claim_gate_readback",
        "repeating_prediction_campaign",
    }, "task card coverage drifted")
    require(tasks["unsafe_source_block"]["expectedOutcomeClass"] == "blocked_unsafe", "unsafe source task should stay blocked")
    require(tasks["accepted_adapter_output_ready"]["expectedOutcomeClass"] == "ready_for_forecast_execution", "adapter task boundary drifted")
    require(tasks["claim_gate_readback"]["ledgerMapping"]["claimBoundaryRequired"] is True, "claim gate should require claim-boundary capture")
    require(tasks["repeating_prediction_campaign"]["command"] == "python3 scripts/ope.py prediction-campaign explain", "campaign task command drifted")
    require(tasks["repeating_prediction_campaign"]["ledgerMapping"]["claimBoundaryRequired"] is True, "campaign task should require claim-boundary capture")

    template = packet["evidenceTemplate"]
    require(template["ledgerSubmissionShape"]["canSubmitToPilotEvidence"] is True, "template should be ledger-submission shaped")
    require(any("Raw transcripts" in item for item in template["blockedFields"]), "template must block raw transcripts")
    require(any("Private source rows" in item for item in template["blockedFields"]), "template must block private source details")

    review = packet["sanitizationReview"]
    require(review["requiredPassCount"] == len(review["checks"]), "all sanitization checks should be required")
    require(len(review["checks"]) == 7, "sanitization check count drifted")
    for check in review["checks"]:
        require(check["requiredForLedgerSubmission"] is True, "each sanitization check should be required")

    require(boundary["readOnlyPacket"] is True, "packet should be read-only")
    require(boundary["usesCheckedTaskDefinitions"] is True, "packet should use checked task definitions")
    for key, value in boundary.items():
        if key in {"readOnlyPacket", "usesCheckedTaskDefinitions"}:
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked pilot session packet")


if __name__ == "__main__":
    main()
