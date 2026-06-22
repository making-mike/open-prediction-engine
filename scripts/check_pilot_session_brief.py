#!/usr/bin/env python3
"""Check the supervised pilot session brief readback."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_pilot_session_brief import build_pilot_session_brief, validate_pilot_session_brief
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("pilot session brief generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_pilot_session_brief()
    validate_pilot_session_brief(record)

    require(record["pilotSessionBriefId"] == "pilotsessionbrief-001", "brief id drifted")
    require(record["briefStatus"] == "ready_for_supervised_session", "brief status drifted")
    require(
        record["recommendedTask"]["scenarioKey"] == "engine_setup_shortcut_comprehension",
        "brief should default to setup-comprehension task",
    )
    require(
        record["genericAgentGuidance"]["flowStatus"] == "checked_domain_agnostic_setup_flow",
        "brief should embed the generic agent guidance flow",
    )
    question_text = " ".join(record["genericAgentGuidance"]["clarificationQuestions"]).lower()
    for phrase in ["decision", "outcome", "horizon", "approved source", "resolution source"]:
        require(phrase in question_text, f"generic brief questions should mention {phrase}")

    commands = {item["stepKey"]: item for item in record["commandSequence"]}
    require(
        commands["open_brief"]["command"] == "python3 scripts/ope.py pilot-session-brief",
        "brief command loop should start from the session brief",
    )
    require(
        commands["open_agent_guide"]["command"] == "python3 scripts/ope.py agent-guide --section generic",
        "brief should route moderators to generic agent guidance",
    )
    require(
        commands["print_summary_draft"]["command"] == "python3 scripts/ope.py pilot-summary-template --section draft",
        "brief should expose the non-ledger-ready summary draft command",
    )
    require(
        commands["append_local_evidence"]["mutatesLocalState"] is True,
        "explicit local append should be the only mutating command",
    )
    for key, item in commands.items():
        if key != "append_local_evidence":
            require(item["mutatesLocalState"] is False, f"{key} should be read-only")

    require(
        record["summaryDraft"]["draftClassifiesAs"] == "needs_redaction",
        "brief should include a non-ledger-ready draft status",
    )
    require(record["summary"]["realSessionsRecorded"] == 0, "brief must not count real sessions")
    require(record["summary"]["ledgerRowsWritten"] == 0, "brief must not write ledger rows")
    require(record["summary"]["qualityClaimAllowed"] is False, "brief must not allow quality claims")
    require(record["summary"]["hostedRuntimeAllowed"] is False, "brief must not allow hosted runtime")

    boundary = record["executionBoundary"]
    require(boundary["readOnlyBrief"] is True, "brief boundary should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyBrief":
            continue
        require(value is False, f"{key} should stay false")

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-session-brief", "--section", "summary"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"pilot-session-brief summary CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["briefStatus"] == "ready_for_supervised_session", "CLI brief summary status drifted")
    require(payload["recommendedScenarioKey"] == "engine_setup_shortcut_comprehension", "CLI brief task drifted")
    require(payload["genericAgentGuidanceReady"] is True, "CLI brief should expose generic guidance readiness")

    commands_cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-session-brief", "--section", "commands"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(commands_cli.returncode == 0, f"pilot-session-brief commands CLI failed: {commands_cli.stderr or commands_cli.stdout}")
    commands_payload = json.loads(commands_cli.stdout)
    require(commands_payload[1]["command"] == "python3 scripts/ope.py agent-guide --section generic", "CLI brief command sequence drifted")

    print("checked pilot session brief")


if __name__ == "__main__":
    main()
