#!/usr/bin/env python3
"""Check prediction campaign evidence ledger semantics."""

from __future__ import annotations

from pathlib import Path
import tempfile

import generate_prediction_campaign_evidence_ledger as ledger_module
from check_prediction_campaign_resolution_attempt import seed_local_forecast
import generate_transit_baseline_track_record_gate as track_gate_module
import prediction_campaign_resolution_runtime as resolution_runtime


def main() -> None:
    ledger = ledger_module.build_prediction_campaign_evidence_ledger()
    if ledger["ledgerStatus"] != "checked_exclusion_append_ready":
        raise AssertionError("prediction campaign ledger status drifted")
    if ledger["ledgerMode"] != "append-ready":
        raise AssertionError("prediction campaign ledger default mode drifted")
    if ledger["summary"]["comparableAppendReady"]:
        raise AssertionError("default prediction campaign ledger should not be comparable append-ready")
    if not ledger["summary"]["exclusionAppendReady"]:
        raise AssertionError("default prediction campaign ledger should preserve the exclusion audit row")
    if ledger["summary"]["comparableRowCount"] != 0 or ledger["summary"]["excludedRowCount"] != 1:
        raise AssertionError("default prediction campaign ledger row counts drifted")
    if ledger["duplicateProtection"]["priorEvidenceOverwriteAllowed"]:
        raise AssertionError("prediction campaign ledger must not allow prior evidence overwrite")
    if ledger["executionBoundary"]["writesIgnoredLiveState"] or ledger["executionBoundary"]["appendsCorpusEvidence"]:
        raise AssertionError("prediction campaign ledger normal checks must not write local state")
    blocked = [check for check in ledger["appendChecks"] if check["blocksComparableAppend"]]
    if not blocked:
        raise AssertionError("default prediction campaign ledger should block comparable append")

    comparable = ledger_module.build_prediction_campaign_evidence_ledger(ledger_case="comparable_scored")
    if comparable["ledgerStatus"] != "checked_comparable_append_ready":
        raise AssertionError("comparable prediction campaign ledger status drifted")
    if not comparable["summary"]["comparableAppendReady"]:
        raise AssertionError("comparable prediction campaign ledger should be comparable append-ready")
    if comparable["summary"]["exclusionAppendReady"]:
        raise AssertionError("comparable prediction campaign ledger should not be exclusion append-ready")
    if comparable["summary"]["comparableRowCount"] != 1 or comparable["summary"]["excludedRowCount"] != 0:
        raise AssertionError("comparable prediction campaign ledger row counts drifted")
    if any(check["blocksComparableAppend"] for check in comparable["appendChecks"]):
        raise AssertionError("comparable prediction campaign ledger should pass append checks")
    if comparable["executionBoundary"]["writesIgnoredLiveState"] or comparable["executionBoundary"]["appendsCorpusEvidence"]:
        raise AssertionError("comparable prediction campaign ledger dry run must not write local state")
    check_effectful_append(missing_outcome=False)
    check_effectful_append(missing_outcome=True)
    print("checked prediction campaign evidence ledger")


def check_effectful_append(*, missing_outcome: bool) -> None:
    original_ledger_root = ledger_module.ROOT
    original_resolution_root = resolution_runtime.ROOT
    original_track_gate_root = track_gate_module.LOCAL_WORKSPACE_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ledger_module.ROOT = root
        resolution_runtime.ROOT = root
        try:
            outcome_csv = seed_local_forecast(root)
            resolution_runtime.execute_local_resolution_write(
                run_id="predictionrun-1301",
                now="2026-06-11T07:15:00Z",
                outcome_csv=None if missing_outcome else outcome_csv,
                missing_outcome=missing_outcome,
            )
            ready = ledger_module.build_prediction_campaign_evidence_ledger(from_local=True)
            expected_ready_status = "local_exclusion_append_ready" if missing_outcome else "local_comparable_append_ready"
            if ready["ledgerStatus"] != expected_ready_status:
                raise AssertionError("local prediction campaign ledger readiness status drifted")
            if not ready["executionBoundary"]["readsIgnoredLiveState"]:
                raise AssertionError("local prediction campaign ledger should read ignored state only when explicit")
            row_collection = ready["excludedRows"] if missing_outcome else ready["comparableRows"]
            row = row_collection[0]
            if row["evidencePacketId"] != "evidence-1301" or row["historyId"] != "history-1301":
                raise AssertionError("local ledger row should preserve evidence and history provenance")
            for key in [
                "runStatePath",
                "forecastArtifactPath",
                "evidencePacketPath",
                "forecastHistoryPath",
                "resolutionRecordPath",
                "scoringReportPath",
            ]:
                if not row[key].startswith(".ope/live/prediction-campaigns/"):
                    raise AssertionError(f"local ledger row {key} should stay under ignored local campaign state")
            written = ledger_module.build_prediction_campaign_evidence_ledger(mode="append", write_local=True)
            if written["ledgerStatus"] != "local_append_written":
                raise AssertionError("local prediction campaign ledger append should write the first row")
            if written["localWriteResult"]["appendedRowCount"] != 1:
                raise AssertionError("local prediction campaign ledger should append one row")
            if not written["executionBoundary"]["appendsCorpusEvidence"]:
                raise AssertionError("local append should mark corpus evidence append in the execution boundary")
            if written["executionBoundary"]["qualityClaimAllowed"] or written["executionBoundary"]["calibrationClaimAllowed"]:
                raise AssertionError("local append must not allow quality or calibration claims")
            repeated = ledger_module.build_prediction_campaign_evidence_ledger(mode="append", write_local=True)
            if repeated["ledgerStatus"] != "local_append_already_present":
                raise AssertionError("local prediction campaign ledger append should be idempotent")
            if repeated["localWriteResult"]["alreadyPresentCount"] != 1:
                raise AssertionError("local prediction campaign ledger should detect the existing row")
            track_gate_module.LOCAL_WORKSPACE_ROOT = root
            gate = track_gate_module.build_gate(campaign="predictioncampaign-001", from_local_ledger=True)
            if gate["campaignLedger"]["ledgerCase"] != "local_evidence_ledger":
                raise AssertionError("track-record gate should identify local campaign ledger input")
            if missing_outcome:
                if gate["sampleSummary"]["resolvedComparableSampleSize"] != 1:
                    raise AssertionError("local excluded ledger row must not increase comparable sample size")
                if gate["campaignLedger"]["excludedRowCount"] != 1:
                    raise AssertionError("track-record gate should count local excluded rows")
            else:
                if gate["sampleSummary"]["resolvedComparableSampleSize"] != 2:
                    raise AssertionError("track-record gate should count explicit local comparable rows")
                if gate["campaignLedger"]["comparableRowCount"] != 1:
                    raise AssertionError("track-record gate should count local comparable rows")
        finally:
            ledger_module.ROOT = original_ledger_root
            resolution_runtime.ROOT = original_resolution_root
            track_gate_module.LOCAL_WORKSPACE_ROOT = original_track_gate_root


if __name__ == "__main__":
    main()
