#!/usr/bin/env python3
"""Check the local deterministic forecast pipeline scaffold."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from read_ope_record import read_record
from run_forecast_pipeline import PipelineRejected, build_outputs


ROOT = Path(__file__).resolve().parents[1]
BLOCKED_REQUEST = ROOT / "spec" / "fixtures" / "requests" / "approval-required-sensitive-request.json"


def run_pipeline_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/run_forecast_pipeline.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> None:
    outputs = build_outputs()
    pipeline_run = outputs["weather-logistics-pipeline-pipeline-run.generated.json"]
    evidence = outputs["weather-logistics-pipeline-evidence.generated.json"]
    artifact = outputs["weather-logistics-pipeline-artifact.generated.json"]
    if pipeline_run["executionStatus"] != "generated_fixture":
        raise AssertionError("pipeline should generate fixture outputs for accepted requests")
    if pipeline_run["effectfulGeneration"] is not False:
        raise AssertionError("pipeline scaffold must remain fixture dry-run only")
    if evidence["forecastId"] != artifact["forecastId"]:
        raise AssertionError("pipeline evidence/artifact forecast binding mismatch")

    try:
        build_outputs(BLOCKED_REQUEST)
    except PipelineRejected:
        pass
    else:
        raise AssertionError("blocked request must not generate pipeline outputs")

    run_pipeline_cli()

    response = read_record("forecast-artifact", "forecast-502", "question-501")
    if response["record"]["evidencePacketId"] != "evidence-501":
        raise AssertionError("pipeline artifact should be readable with its evidence binding")

    print("checked local forecast pipeline scaffold")


if __name__ == "__main__":
    main()
