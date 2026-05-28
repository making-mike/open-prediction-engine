#!/usr/bin/env python3
"""Check the transit corpus growth-loop read model."""

from __future__ import annotations

from generate_transit_corpus_growth_loop import CASE_ORDER, build_growth_loop


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    growth = build_growth_loop()
    candidates = growth["candidateUpdates"]
    progress = growth["progressReadback"]
    protocol = growth["appendProtocol"]
    boundary = growth["executionBoundary"]

    require([item["candidateCase"] for item in candidates] == CASE_ORDER, "candidate coverage/order drifted")
    require(protocol["appendOnly"] is True, "append protocol should be append-only")
    require(protocol["manualCorpusEditingRequired"] is False, "growth loop should not require manual corpus editing")
    require(protocol["canonicalCorpusMutationImplemented"] is False, "checked growth loop should not claim canonical mutation")
    require(protocol["normalChecksMutateCorpus"] is False, "normal checks must not mutate the corpus")
    require(
        set(protocol["requiredBindings"]) == {
            "forward_run_state",
            "forecast_artifact",
            "resolution_record",
            "scoring_report",
            "source_policy",
            "corpus_policy",
        },
        "append protocol binding set drifted",
    )

    ready = [item for item in candidates if item["appendDecision"] == "append_ready"]
    require(len(ready) == 1, "growth loop should expose one append-ready candidate")
    ready_row = ready[0]
    require(ready_row["candidateCase"] == "comparable_resolved", "append-ready candidate should be comparable resolved")
    for key in [
        "requiredBindingsPresent",
        "forecastBeforeClose",
        "resolvedAfterHorizon",
        "scorePresent",
        "forecastTimeEvidenceBoundaryPreserved",
        "resolutionOnlyEvidenceBoundaryPreserved",
    ]:
        require(ready_row[key] is True, f"append-ready candidate should satisfy {key}")
    require(ready_row["appendOnlyWrite"]["wouldAppendCorpusRow"] is True, "append-ready candidate should append one row")

    excluded = [item for item in candidates if item["appendDecision"] != "append_ready"]
    require(len(excluded) == 5, "growth loop should expose five excluded/rejected candidates")
    require(
        {item["reasonCode"] for item in excluded} == {
            "missing_outcome",
            "stale_evidence",
            "leakage_risk",
            "post_close_source",
            "incomparable_window",
        },
        "excluded reason coverage drifted",
    )
    for item in excluded:
        require(item["appendOnlyWrite"]["wouldAppendCorpusRow"] is False, "excluded candidates should not append comparable rows")
    leakage = next(item for item in candidates if item["candidateCase"] == "leakage_risk")
    require(leakage["appendDecision"] == "reject_from_corpus", "leakage-risk candidate should be rejected")
    require(leakage["forecastTimeEvidenceBoundaryPreserved"] is False, "leakage-risk candidate should break forecast-time boundary")

    ledger = growth["exclusionLedger"]
    require(len(ledger) == 5, "exclusion ledger should contain five rows")
    require(
        {row["reasonCode"] for row in ledger} == {item["reasonCode"] for item in excluded},
        "exclusion ledger should cover excluded reasons",
    )
    for row in ledger:
        require(row["countsTowardComparableResolved"] is False, "excluded rows must not count toward comparable resolved")
        require(row["countsTowardCalibration"] is False, "excluded rows must not count toward calibration")
    require(
        next(row for row in ledger if row["reasonCode"] == "leakage_risk")["safeToRetainForAudit"] is False,
        "leakage-risk rows should not be retained as safe audit examples",
    )

    require(progress["currentComparableResolved"] == 1, "current comparable count drifted")
    require(progress["appendReadyComparableCount"] == 1, "append-ready count drifted")
    require(progress["projectedComparableResolved"] == 2, "projected comparable count drifted")
    require(progress["remainingForTrackRecord"] == 28, "track-record remaining count drifted")
    require(progress["remainingForCalibration"] == 98, "calibration remaining count drifted")
    require(progress["qualityClaimAllowed"] is False, "quality claim should remain blocked")
    require(progress["calibrationClaimAllowed"] is False, "calibration claim should remain blocked")
    require(progress["baselineTrackRecordAllowed"] is False, "track-record claim should remain blocked")

    require(boundary["appendOnlyContractDeclared"] is True, "growth boundary should declare append-only contract")
    require(boundary["normalChecksDeterministicOffline"] is True, "growth boundary should keep checks deterministic offline")
    for key in [
        "executesAppend",
        "modifiesExistingCorpusRows",
        "readsIgnoredLiveWorkspace",
        "fetchesLiveData",
        "createsForecastArtifacts",
        "createsResolutionRecords",
        "createsScoringRecords",
        "storesCredentials",
        "allowsQualityClaims",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should remain false")

    print("checked transit corpus growth loop")


if __name__ == "__main__":
    main()
