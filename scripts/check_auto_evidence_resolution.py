#!/usr/bin/env python3
"""Check auto-evidence resolution and scoring invariants."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from read_ope_record import read_record
from resolve_auto_evidence_outcome import PREFIX, build_outputs


ROOT = Path(__file__).resolve().parents[1]


def run_resolution_cli() -> None:
    subprocess.run(
        [sys.executable, "scripts/resolve_auto_evidence_outcome.py"],
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
        raise AssertionError("auto-evidence resolution fixture should resolve normally")
    if scoring["scoreStatus"] != "scored":
        raise AssertionError("auto-evidence resolved fixture should be scored")
    if summary["requestId"] != "forecastrequest-007":
        raise AssertionError("auto-evidence outcome summary lost request binding")
    if summary["evidencePlanId"] != "evidenceplan-019":
        raise AssertionError("auto-evidence outcome summary lost evidence-plan binding")
    if summary["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("auto-evidence outcome summary lost source-set binding")
    if summary["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("auto-evidence outcome summary lost source-policy binding")
    if summary["forecastId"] != scoring["forecastId"]:
        raise AssertionError("auto-evidence outcome summary lost forecast binding")
    if track_record["counts"]["nResolved"] != 1:
        raise AssertionError("auto-evidence track record should include one resolved outcome")

    run_resolution_cli()

    track_response = read_record("track-record", "trackrecord-601")
    if track_response["record"]["summary"]["primaryScore"] != scoring["primaryScore"]:
        raise AssertionError("auto-evidence track record should be readable after resolution")

    card_response = read_record("forecast-card", "forecast-602", "question-601")
    card = card_response["record"]
    if card["status"] != "resolved":
        raise AssertionError("auto-evidence card should surface resolved status")
    if card["score"]["primaryScore"] != scoring["primaryScore"]:
        raise AssertionError("auto-evidence card should surface score summary")
    if card["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("auto-evidence card should preserve claim boundary")
    if card["qualityClaim"]["resolvedComparableOutcomes"] != 1:
        raise AssertionError("auto-evidence card should expose one comparable resolved outcome")
    if card["requestBinding"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("auto-evidence card should preserve source-policy binding")
    if card["requestBinding"]["sourceMode"] != "auto_evidence_fixture_replay":
        raise AssertionError("auto-evidence card should preserve source mode")

    print("checked auto-evidence resolution and scoring")


if __name__ == "__main__":
    main()
