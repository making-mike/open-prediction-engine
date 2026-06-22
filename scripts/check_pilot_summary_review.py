#!/usr/bin/env python3
"""Check the read-only pilot summary review bundle."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_pilot_summary_review import build_pilot_summary_review, validate_pilot_summary_review
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("pilot summary review generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "accepted-setup-engine-summary.json"
BLOCKED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "blocked-raw-transcript-summary.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    accepted = build_pilot_summary_review(ACCEPTED_SUMMARY)
    validate_pilot_summary_review(accepted)

    require(accepted["pilotSummaryReviewId"] == "pilotsummaryreview-001", "review id drifted")
    require(accepted["reviewMode"] == "read_only_pilot_summary_review", "review mode drifted")
    require(accepted["inputSummaryId"] == "pilotsummaryinput-001", "accepted input summary id drifted")
    require(accepted["classification"]["intakeDecision"] == "accept_for_ledger_review", "accepted intake decision drifted")
    require(accepted["appendPlan"]["appendDecision"] == "ready_for_local_write", "accepted append decision drifted")
    require(accepted["reviewDecision"]["canAppendWithWriteLocal"] is True, "accepted summary should be append-ready")
    require(accepted["reviewDecision"]["blockedByIntake"] is False, "accepted summary should not be blocked")
    require(accepted["summary"]["candidateRealSessionEvidence"] is True, "accepted summary should be candidate evidence")
    require(accepted["summary"]["contributesRealSessionEvidence"] is False, "read-only review must not count evidence")
    require(accepted["summary"]["ledgerRowsWritten"] == 0, "read-only review must not write ledger rows")
    require(accepted["summary"]["realSessionsRecorded"] == 0, "read-only review must not record sessions")
    require(accepted["summary"]["qualityClaimAllowed"] is False, "review must not allow quality claims")

    commands = {item["stepKey"]: item for item in accepted["operatorCommands"]}
    require(
        commands["classify_summary"]["command"].endswith("accepted-setup-engine-summary.json"),
        "accepted review should expose classify command for input file",
    )
    require(
        commands["dry_run_append"]["command"].startswith("python3 scripts/ope.py pilot-evidence --input-summary"),
        "accepted review should expose dry-run append command",
    )
    require(
        commands["write_local_append"]["mutatesLocalState"] is True,
        "explicit write-local append should be the only mutating command",
    )
    for key, command in commands.items():
        if key != "write_local_append":
            require(command["mutatesLocalState"] is False, f"{key} should be read-only")

    boundary = accepted["executionBoundary"]
    require(boundary["readOnlyReview"] is True, "review should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyReview":
            continue
        require(value is False, f"{key} should stay false")

    blocked = build_pilot_summary_review(BLOCKED_SUMMARY)
    validate_pilot_summary_review(blocked)
    require(blocked["inputSummaryId"] == "pilotsummaryinput-002", "blocked input summary id drifted")
    require(blocked["classification"]["intakeDecision"] == "block_raw_transcript", "blocked decision drifted")
    require(blocked["appendPlan"]["appendDecision"] == "blocked_by_intake", "blocked append decision drifted")
    require(blocked["reviewDecision"]["canAppendWithWriteLocal"] is False, "blocked summary must not be append-ready")
    require(blocked["reviewDecision"]["blockedByIntake"] is True, "blocked summary should be blocked by intake")
    require(blocked["summary"]["candidateRealSessionEvidence"] is False, "blocked summary should not be candidate evidence")
    blocked_commands = {item["stepKey"]: item for item in blocked["operatorCommands"]}
    require("write_local_append" not in blocked_commands, "blocked review must not expose write-local append command")

    cli = subprocess.run(
        [
            sys.executable,
            "scripts/ope.py",
            "pilot-summary-review",
            "--input",
            str(ACCEPTED_SUMMARY),
            "--section",
            "summary",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"pilot-summary-review summary CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["appendDecision"] == "ready_for_local_write", "CLI accepted append decision drifted")
    require(payload["canAppendWithWriteLocal"] is True, "CLI accepted review should be append-ready")
    require(payload["ledgerRowsWritten"] == 0, "CLI summary must remain read-only")

    blocked_cli = subprocess.run(
        [
            sys.executable,
            "scripts/ope.py",
            "pilot-summary-review",
            "--input",
            str(BLOCKED_SUMMARY),
            "--section",
            "summary",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(blocked_cli.returncode == 0, f"blocked pilot-summary-review CLI failed: {blocked_cli.stderr or blocked_cli.stdout}")
    blocked_payload = json.loads(blocked_cli.stdout)
    require(blocked_payload["appendDecision"] == "blocked_by_intake", "CLI blocked append decision drifted")
    require(blocked_payload["canAppendWithWriteLocal"] is False, "CLI blocked review should not be append-ready")

    print("checked pilot summary review")


if __name__ == "__main__":
    main()
