#!/usr/bin/env python3
"""Check read-only OPE record access behavior."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from read_ope_record import PublicError, assert_public_access, list_records, read_record, render_response


ROOT = Path(__file__).resolve().parents[1]


def run_reader(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/read_ope_record.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def check_artifact_read() -> None:
    response = read_record("forecast-artifact", "forecast-101", "question-101")
    record = response["record"]
    if record["forecastId"] != "forecast-101":
        raise AssertionError("forecast artifact lookup returned wrong record")
    if response["access"]["mode"] != "read_only_file":
        raise AssertionError("read access must be explicitly read-only")


def check_track_record_read() -> None:
    response = read_record("track-record", "trackrecord-101")
    if response["record"]["domain"] != "weather-logistics":
        raise AssertionError("track-record lookup returned wrong domain")


def check_forecast_bundle_read() -> None:
    response = read_record("forecast-bundle", "forecast-502", "question-501")
    record = response["record"]
    if record["bundleId"] != "forecastbundle-forecast-502":
        raise AssertionError("forecast bundle lookup returned wrong bundle")
    if record["includedRecords"]["evidencePacket"] != "evidence-501":
        raise AssertionError("forecast bundle missed evidence binding")
    if record["includedRecords"]["resolutionRecord"] != "resolution-501":
        raise AssertionError("forecast bundle missed resolution binding")
    if record["includedRecords"]["scoringReport"] != "scoring-501":
        raise AssertionError("forecast bundle missed scoring binding")
    if record["includedRecords"]["trackRecordReport"] != "trackrecord-501":
        raise AssertionError("forecast bundle missed track-record binding")
    if record["records"]["pipelineRun"]["requestId"] != "forecastrequest-006":
        raise AssertionError("forecast bundle missed request binding")


def check_forecast_card_read() -> None:
    response = read_record("forecast-card", "forecast-502", "question-501")
    record = response["record"]
    if record["cardId"] != "forecastcard-forecast-502":
        raise AssertionError("forecast card lookup returned wrong card")
    if record["forecast"]["probability"] != 0.41:
        raise AssertionError("forecast card returned wrong probability")
    if record["score"]["baselineLift"] != 0.2603:
        raise AssertionError("forecast card returned wrong score summary")
    if record["qualityClaim"]["status"] != "not_enough_resolved_pipeline_outcomes":
        raise AssertionError("forecast card missed claim boundary")
    if record["requestBinding"]["effectfulGeneration"] is not False:
        raise AssertionError("forecast card missed fixture dry-run request binding")
    forbidden = json.dumps(record)
    if "contentHash" in forbidden or "supportingEvidence" in forbidden:
        raise AssertionError("forecast card should not expose source hashes or supporting evidence URIs")


def check_historical_forecast_card_read() -> None:
    response = read_record("forecast-card", "forecast-702", "question-701")
    record = response["record"]
    if record["forecast"]["probability"] != 0.22:
        raise AssertionError("historical forecast card returned wrong probability")
    if record["forecast"] != record["baseline"]:
        raise AssertionError("historical forecast card should show baseline equality")
    if record["requestBinding"]["sourceMode"] != "committed_fixture":
        raise AssertionError("historical forecast card missed committed fixture binding")
    if record["links"]["evidenceTrace"] is not None:
        raise AssertionError("historical forecast card should not link an auto-evidence trace")


def check_setup_forecast_card_read() -> None:
    response = read_record("forecast-card", "forecast-901", "question-901")
    record = response["record"]
    setup = record["setupBinding"]
    if setup["setupForecastRunId"] != "setupforecastrun-901":
        raise AssertionError("setup forecast card missed setup run binding")
    if setup["sourceIntakeReportId"] != "sourceintakereport-001":
        raise AssertionError("setup forecast card missed source intake binding")
    if setup["setupBenchmarkGateId"] != "setupbenchmarkgate-001":
        raise AssertionError("setup forecast card missed setup benchmark gate binding")
    if setup["selectedMethodClass"] != "deterministic_statistical":
        raise AssertionError("setup forecast card returned wrong selected method")
    if record["forecast"]["probability"] <= record["baseline"]["probability"]:
        raise AssertionError("setup forecast card should show deterministic lift over baseline")
    if record["links"]["evidenceTrace"] is not None:
        raise AssertionError("setup forecast card should not link an auto-evidence trace")


def check_source_handoff_forecast_card_read() -> None:
    response = read_record("forecast-card", "forecast-1102", "question-1102")
    record = response["record"]
    setup = record["setupBinding"]
    if setup["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("source-handoff forecast card missed setup run binding")
    if setup["sourceIntakeHandoffId"] != "sourceintakehandoff-002":
        raise AssertionError("source-handoff forecast card missed handoff binding")
    if setup["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("source-handoff forecast card missed method gate binding")
    if setup["sourceIntakeReportId"] != "sourceintakereport-102":
        raise AssertionError("source-handoff forecast card missed source intake binding")
    if setup["setupBenchmarkGateId"] != "setupbenchmarkgate-102":
        raise AssertionError("source-handoff forecast card missed benchmark gate binding")
    if setup["selectedMethodClass"] != "deterministic_statistical":
        raise AssertionError("source-handoff forecast card returned wrong selected method")
    if record["forecast"]["probability"] <= record["baseline"]["probability"]:
        raise AssertionError("source-handoff forecast card should show deterministic lift over baseline")
    if record["links"]["evidenceTrace"] is not None:
        raise AssertionError("source-handoff forecast card should not link an auto-evidence trace")


def check_campaign_forecast_card_read() -> None:
    response = read_record("forecast-card", "forecast-1301", "question-1301")
    record = response["record"]
    if record["status"] != "open":
        raise AssertionError("campaign forecast card should remain open before resolution")
    if record["forecast"] != record["baseline"]:
        raise AssertionError("campaign forecast card should expose baseline-only equality")
    if record["score"] is not None:
        raise AssertionError("campaign forecast card should not expose a score before resolution")
    if record["qualityClaim"]["status"] != "unresolved":
        raise AssertionError("campaign forecast card should preserve unresolved claim boundary")
    if record["links"]["resolutionRecord"] is not None or record["links"]["scoringReport"] is not None:
        raise AssertionError("campaign forecast card should not link resolution or scoring records yet")


def check_evidence_trace_read() -> None:
    response = read_record("evidence-trace", "forecast-602", "question-601")
    record = response["record"]
    if record["evidenceTraceId"] != "evidencetrace-602":
        raise AssertionError("evidence trace lookup returned wrong trace")
    if record["recordBinding"]["evidencePlanId"] != "evidenceplan-019":
        raise AssertionError("evidence trace missed evidence-plan binding")
    if record["recordBinding"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("evidence trace missed source-set binding")
    if record["recordBinding"]["sourceConnectorRegistryId"] != "sourceconnectorregistry-001":
        raise AssertionError("evidence trace missed connector registry binding")
    if record["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence trace missed connector result-set binding")
    if record["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("evidence trace must not claim all evidence coverage")
    if record["controls"]["rawStackTracesExposed"] is not False:
        raise AssertionError("evidence trace should not expose raw stack traces")
    rendered = json.dumps(record)
    if "fixturePath" in rendered or "rawSourceMetadata" in rendered:
        raise AssertionError("evidence trace should not expose raw fixture metadata")


def check_evidence_source_set_read() -> None:
    response = read_record("evidence-source-set", "evidencesourceset-019")
    record = response["record"]
    if record["sourceConnectorRegistryId"] != "sourceconnectorregistry-001":
        raise AssertionError("evidence source-set read missed connector registry binding")


def check_source_connector_results_read() -> None:
    response = read_record("source-connector-results", "sourceconnectorresults-001")
    record = response["record"]
    if record["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("source connector result read returned wrong result set")


def check_record_list() -> None:
    response = list_records("forecast-artifact", domain="weather-logistics")
    if response["count"] < 1:
        raise AssertionError("record list should include weather-logistics artifacts")
    if any(record["domain"] != "weather-logistics" for record in response["records"]):
        raise AssertionError("record list domain filter leaked another domain")

    bundles = list_records("forecast-bundle", domain="weather-logistics")
    if bundles["count"] < 1:
        raise AssertionError("forecast bundle list should include weather-logistics bundles")

    cards = list_records("forecast-card", domain="weather-logistics")
    if cards["count"] < 1:
        raise AssertionError("forecast card list should include weather-logistics cards")

    traces = list_records("evidence-trace", domain="weather-logistics")
    if traces["count"] < 1:
        raise AssertionError("evidence trace list should include weather-logistics traces")


def check_binding_failure() -> None:
    result = run_reader(
        "--record-type",
        "forecast-artifact",
        "--id",
        "forecast-101",
        "--question-id",
        "question-does-not-match-999",
    )
    if result.returncode == 0:
        raise AssertionError("mismatched question binding should fail")
    error = json.loads(result.stderr)
    if error["error"]["code"] != "binding_mismatch":
        raise AssertionError("binding failure should return a sanitized binding_mismatch code")


def check_sanitized_not_found() -> None:
    result = run_reader("--record-type", "forecast-artifact", "--id", "forecast-missing-999")
    if result.returncode == 0:
        raise AssertionError("missing record should fail")
    if str(ROOT) in result.stderr or "spec/fixtures" in result.stderr:
        raise AssertionError("public errors must not leak local paths")
    error = json.loads(result.stderr)
    if error["error"]["code"] != "not_found":
        raise AssertionError("missing record should return not_found")


def check_response_size_limit() -> None:
    try:
        render_response(read_record("forecast-artifact", "forecast-101"), max_bytes=20)
    except PublicError as exc:
        if exc.code != "response_too_large":
            raise
    else:
        raise AssertionError("tiny max_bytes should fail")


def check_access_policy() -> None:
    now = datetime(2026, 6, 1, tzinfo=timezone.utc)
    for policy in [
        {"visibility": "private"},
        {"visibility": "embargoed"},
        {"visibility": "public", "embargoUntil": "2026-06-02T00:00:00Z"},
    ]:
        try:
            assert_public_access({"accessPolicy": policy}, now=now)
        except PublicError as exc:
            if exc.code != "access_denied":
                raise
        else:
            raise AssertionError(f"policy {policy} should deny access")


def main() -> None:
    check_artifact_read()
    check_track_record_read()
    check_forecast_bundle_read()
    check_forecast_card_read()
    check_historical_forecast_card_read()
    check_setup_forecast_card_read()
    check_source_handoff_forecast_card_read()
    check_campaign_forecast_card_read()
    check_evidence_trace_read()
    check_evidence_source_set_read()
    check_source_connector_results_read()
    check_record_list()
    check_binding_failure()
    check_sanitized_not_found()
    check_response_size_limit()
    check_access_policy()
    print("checked read-only OPE record access")


if __name__ == "__main__":
    main()
