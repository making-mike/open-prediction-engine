#!/usr/bin/env python3
"""Check auto-evidence fixture forecast generation and read access."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from read_ope_record import read_record
from run_auto_evidence_forecast import AutoEvidenceForecastError, build_outputs


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_REQUEST = ROOT / "spec" / "fixtures" / "requests" / "approval-required-sensitive-request.json"


def run_forecast_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/run_auto_evidence_forecast.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> None:
    outputs = build_outputs()
    pipeline_run = outputs["weather-logistics-auto-evidence-pipeline-run.generated.json"]
    evidence = outputs["weather-logistics-auto-evidence-evidence.generated.json"]
    artifact = outputs["weather-logistics-auto-evidence-artifact.generated.json"]

    if pipeline_run["outputs"]["evidencePlanId"] != "evidenceplan-019":
        raise AssertionError("auto-evidence forecast should bind evidence plan")
    if pipeline_run["outputs"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("auto-evidence forecast should bind evidence source set")
    if pipeline_run["controls"]["sourceMode"] != "auto_evidence_fixture_replay":
        raise AssertionError("auto-evidence forecast should declare fixture replay source mode")
    if pipeline_run["effectfulGeneration"] is not False:
        raise AssertionError("auto-evidence forecast must not be effectful")
    if evidence["forecastId"] != artifact["forecastId"]:
        raise AssertionError("auto-evidence evidence/artifact binding mismatch")
    if "source-402" in {source["sourceId"] for source in evidence["provenanceReferences"]}:
        raise AssertionError("auto-evidence forecast must not include outcome source provenance")

    try:
        build_outputs(BLOCKED_REQUEST)
    except AutoEvidenceForecastError:
        pass
    else:
        raise AssertionError("blocked request must not generate auto-evidence forecast outputs")

    run_forecast_cli()

    response = read_record("forecast-artifact", "forecast-602", "question-601")
    if response["record"]["evidencePacketId"] != "evidence-601":
        raise AssertionError("auto-evidence artifact should be readable with evidence binding")

    bundle = read_record("forecast-bundle", "forecast-602", "question-601")
    if bundle["record"]["includedRecords"]["pipelineRun"] != "pipelinerun-601":
        raise AssertionError("auto-evidence bundle should include pipeline run")

    card = read_record("forecast-card", "forecast-602", "question-601")
    if card["record"]["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("auto-evidence card should expose the resolved auto-evidence claim boundary")
    if card["record"]["requestBinding"]["requestId"] != "forecastrequest-007":
        raise AssertionError("auto-evidence card should preserve request binding")
    if card["record"]["requestBinding"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("auto-evidence card should expose source policy binding")
    if card["record"]["requestBinding"]["evidencePlanId"] != "evidenceplan-019":
        raise AssertionError("auto-evidence card should expose evidence plan binding")
    if card["record"]["requestBinding"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("auto-evidence card should expose evidence source set binding")
    if card["record"]["requestBinding"]["sourceMode"] != "auto_evidence_fixture_replay":
        raise AssertionError("auto-evidence card should expose evidence mode")
    if card["record"]["requestBinding"]["effectfulGeneration"] is not False:
        raise AssertionError("auto-evidence card should preserve non-effectful generation")

    print("checked auto-evidence forecast generation")


if __name__ == "__main__":
    main()
