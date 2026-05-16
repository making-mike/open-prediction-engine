#!/usr/bin/env python3
"""Run dependency-free repository checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, "scripts/check_json.py"])
    run([sys.executable, "scripts/check_schema_contracts.py"])
    run([sys.executable, "scripts/check_contract_validator.py"])
    run([sys.executable, "scripts/generate_fixture_reports.py"])
    run([sys.executable, "scripts/run_fixture_loop.py"])
    run([sys.executable, "scripts/check_live_weather_connector.py"])
    run([sys.executable, "scripts/check_live_weather_baseline.py"])
    run([sys.executable, "scripts/check_live_weather_evidence.py"])
    run([sys.executable, "scripts/resolve_live_weather_outcome.py"])
    run([sys.executable, "scripts/run_forecast_pipeline.py"])
    run([sys.executable, "scripts/resolve_pipeline_outcome.py"])
    run([sys.executable, "scripts/generate_record_index.py"])
    run([sys.executable, "scripts/generate_release_manifest.py"])
    run([sys.executable, "scripts/check_benchmarks.py"])
    run([sys.executable, "scripts/check_read_access.py"])
    run([sys.executable, "scripts/check_read_contracts.py"])
    run([sys.executable, "scripts/check_forecast_requests.py"])
    run([sys.executable, "scripts/check_forecast_pipeline.py"])
    run([sys.executable, "scripts/check_pipeline_resolution.py"])
    run([sys.executable, "scripts/check_ci_workflow.py"])
    run([sys.executable, "scripts/check_hardening.py"])
    run([sys.executable, "scripts/check_cli.py"])
    run([sys.executable, "scripts/check_fixtures.py"])


if __name__ == "__main__":
    main()
