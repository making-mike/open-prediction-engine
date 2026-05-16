#!/usr/bin/env python3
"""Smoke-test the local OPE CLI wrapper."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> None:
    run_cli("generate-fixtures")
    run_cli("resolve-live")
    run_cli("pipeline")
    run_cli("resolve-pipeline")
    run_cli("manifest")

    artifact = run_cli(
        "read",
        "--record-type",
        "forecast-artifact",
        "--id",
        "forecast-101",
        "--question-id",
        "question-101",
    )
    artifact_payload = json.loads(artifact.stdout)
    if artifact_payload["record"]["forecastId"] != "forecast-101":
        raise AssertionError("CLI read returned wrong artifact")

    bundle = run_cli(
        "read",
        "--record-type",
        "forecast-bundle",
        "--id",
        "forecast-502",
        "--question-id",
        "question-501",
    )
    bundle_payload = json.loads(bundle.stdout)
    if bundle_payload["record"]["includedRecords"]["scoringReport"] != "scoring-501":
        raise AssertionError("CLI read returned wrong forecast bundle")

    card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-502",
        "--question-id",
        "question-501",
    )
    card_payload = json.loads(card.stdout)
    if card_payload["record"]["qualityClaim"]["status"] != "not_enough_resolved_pipeline_outcomes":
        raise AssertionError("CLI read returned wrong forecast card")

    listed = run_cli("list", "--record-type", "forecast-artifact", "--domain", "weather-logistics")
    listed_payload = json.loads(listed.stdout)
    if listed_payload["count"] < 1:
        raise AssertionError("CLI list returned no weather-logistics artifacts")

    decision = run_cli(
        "request",
        "--input",
        "spec/fixtures/requests/valid-weather-logistics-request.json",
    )
    decision_payload = json.loads(decision.stdout)
    if decision_payload["decisionStatus"] != "accepted":
        raise AssertionError("CLI request validation returned wrong decision")

    validated = run_cli(
        "validate",
        "--input",
        "spec/fixtures/valid/binary-weather-logistics-question.json",
    )
    validation_payload = json.loads(validated.stdout)
    if validation_payload["valid"] is not True:
        raise AssertionError("CLI contract validation returned wrong decision")

    weather = run_cli(
        "weather",
        "--location",
        "warsaw",
        "--service-date",
        "2026-06-03",
        "--fixture",
        "spec/fixtures/live/open-meteo-warsaw-forecast-response.json",
        "--retrieved-at",
        "2026-06-02T09:30:00Z",
    )
    weather_payload = json.loads(weather.stdout)
    if weather_payload["normalizedFields"]["forecastDailyPrecipitationMm"] != 24:
        raise AssertionError("CLI weather normalization drifted")

    print("checked local OPE CLI")


if __name__ == "__main__":
    main()
