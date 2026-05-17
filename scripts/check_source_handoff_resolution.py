#!/usr/bin/env python3
"""Check source-handoff forecast resolution and scoring invariants."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from read_ope_record import read_record
from resolve_source_handoff_outcome import PREFIX, build_outputs


ROOT = Path(__file__).resolve().parents[1]


def run_resolution_cli() -> None:
    subprocess.run(
        [sys.executable, "scripts/resolve_source_handoff_outcome.py"],
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
        raise AssertionError("source-handoff resolution should resolve normally")
    if resolution["resolvedOutcome"]["value"] is not True:
        raise AssertionError("source-handoff resolution should use declared positive outcome")
    if resolution["resolutionSource"]["sourceId"] != "localsource-003":
        raise AssertionError("source-handoff resolution should bind declared outcome source")
    if scoring["scoreStatus"] != "scored":
        raise AssertionError("source-handoff resolved fixture should be scored")
    if scoring["forecastId"] != "forecast-1102":
        raise AssertionError("source-handoff scoring should bind forecast-1102")
    if scoring["primaryScore"] >= scoring["baselineScore"]:
        raise AssertionError("source-handoff deterministic forecast should beat baseline on positive outcome")
    if summary["sourceIntakeHandoffId"] != "sourceintakehandoff-002":
        raise AssertionError("source-handoff outcome summary lost handoff binding")
    if summary["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("source-handoff outcome summary lost method gate binding")
    if summary["resolvedComparableSourceHandoffOutcomes"] != 1:
        raise AssertionError("source-handoff outcome summary should count one resolved outcome")
    if track_record["counts"]["nResolved"] != 1:
        raise AssertionError("source-handoff track record should include one resolved outcome")

    run_resolution_cli()

    card = read_record("forecast-card", "forecast-1102", "question-1102")["record"]
    if card["status"] != "resolved":
        raise AssertionError("source-handoff forecast card should be resolved")
    if card["score"]["scoreStatus"] != "scored":
        raise AssertionError("source-handoff forecast card should expose score")
    if card["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("source-handoff forecast card should preserve quality boundary")
    if card["qualityClaim"]["resolvedComparableOutcomes"] != 1:
        raise AssertionError("source-handoff forecast card should expose resolved comparable count")
    if card["links"]["trackRecordReport"] != "trackrecord-1102":
        raise AssertionError("source-handoff forecast card should link track record")

    track_response = read_record("track-record", "trackrecord-1102")
    if track_response["record"]["summary"]["primaryScore"] != scoring["primaryScore"]:
        raise AssertionError("source-handoff track record should be readable after resolution")

    print("checked source-handoff resolution and scoring")


if __name__ == "__main__":
    main()
