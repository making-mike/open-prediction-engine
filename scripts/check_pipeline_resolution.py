#!/usr/bin/env python3
"""Check request-bound pipeline resolution and scoring invariants."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from read_ope_record import read_record
from resolve_pipeline_outcome import PREFIX, build_outputs


ROOT = Path(__file__).resolve().parents[1]


def run_resolution_cli() -> None:
    subprocess.run(
        [sys.executable, "scripts/resolve_pipeline_outcome.py"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> None:
    outputs = build_outputs()
    resolution = outputs[f"{PREFIX}-resolution.generated.json"]
    scoring = outputs[f"{PREFIX}-scoring.generated.json"]
    summary = outputs[f"{PREFIX}-outcome-summary.generated.json"]
    track_record = outputs[f"{PREFIX}-track-record.generated.json"]

    if resolution["status"] != "resolved":
        raise AssertionError("pipeline resolution fixture should resolve normally")
    if scoring["scoreStatus"] != "scored":
        raise AssertionError("pipeline resolved fixture should be scored")
    if summary["requestId"] != "forecastrequest-006":
        raise AssertionError("pipeline outcome summary lost request binding")
    if summary["forecastId"] != scoring["forecastId"]:
        raise AssertionError("pipeline outcome summary lost forecast binding")
    if track_record["counts"]["nResolved"] != 1:
        raise AssertionError("pipeline track record should include one resolved outcome")

    run_resolution_cli()

    response = read_record("track-record", "trackrecord-501")
    if response["record"]["summary"]["primaryScore"] != scoring["primaryScore"]:
        raise AssertionError("pipeline track record should be readable after resolution")

    print("checked pipeline resolution and scoring")


if __name__ == "__main__":
    main()
