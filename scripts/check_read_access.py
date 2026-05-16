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
    check_record_list()
    check_binding_failure()
    check_sanitized_not_found()
    check_response_size_limit()
    check_access_policy()
    print("checked read-only OPE record access")


if __name__ == "__main__":
    main()
