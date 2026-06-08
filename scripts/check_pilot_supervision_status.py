#!/usr/bin/env python3
"""Check the supervised pilot operator status readback."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from generate_pilot_evidence_ledger import build_local_pilot_evidence_append_plan

try:
    from generate_pilot_supervision_status import build_pilot_supervision_status
except ModuleNotFoundError as exc:  # pragma: no cover - intentional TDD failure before implementation.
    raise AssertionError("pilot supervision status generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "accepted-setup-engine-summary.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_blocked_boundary(boundary: dict[str, bool]) -> None:
    require(boundary["readOnlyStatus"] is True, "status readback should be read-only")
    require(boundary["usesCheckedPilotPacket"] is True, "status readback should use the checked pilot packet")
    require(boundary["writesCheckedFixtures"] is False, "status readback must not write checked fixtures")
    require(boundary["writesIgnoredLocalLedger"] is False, "status readback must not write ignored local ledger")
    require(boundary["recordsRawTranscripts"] is False, "status readback must not store raw transcripts")
    require(boundary["storesPrivateData"] is False, "status readback must not store private data")
    require(boundary["storesCredentials"] is False, "status readback must not store credentials")
    require(boundary["storesPromptLogs"] is False, "status readback must not store prompt logs")
    require(boundary["storesParticipantIdentity"] is False, "status readback must not store participant identity")
    require(boundary["unblocksExpansion"] is False, "status readback must not unblock expansion")
    require(boundary["qualityClaimsUpgraded"] is False, "status readback must not upgrade quality claims")
    require(boundary["calibrationClaimsUpgraded"] is False, "status readback must not upgrade calibration claims")
    require(boundary["hostedRuntimeUnblocked"] is False, "status readback must not unblock hosted runtime")
    require(boundary["generatedTypesUnblocked"] is False, "status readback must not unblock generated types")


def check_default_status() -> None:
    status = build_pilot_supervision_status()
    progress = status["realSessionProgress"]
    require(status["status"] == "real_sessions_needed", "default supervision status should require real sessions")
    require(status["localEvidenceMode"] == "not_requested", "default supervision status should not inspect local evidence")
    require(progress["acceptedRealSessionCount"] == 0, "default status must not count real sessions")
    require(progress["minimumRealSessions"] == 3, "minimum real-session threshold drifted")
    require(progress["targetRealSessions"] == 5, "target real-session threshold drifted")
    require(progress["remainingMinimumSessions"] == 3, "default status should require three more minimum sessions")
    require(progress["remainingTargetSessions"] == 5, "default status should require five more target sessions")
    require(progress["minimumMet"] is False, "default status must not mark the minimum met")
    require(progress["targetMet"] is False, "default status must not mark the target met")

    task = status["recommendedNextTask"]
    require(task["taskId"] == "agentpilottask-006", "recommended next task ID drifted")
    require(
        task["scenarioKey"] == "engine_setup_shortcut_comprehension",
        "recommended next task should measure setup-engine shortcut comprehension",
    )
    require(
        task["command"] == "python3 scripts/ope.py pilot-session-packet --task engine_setup_shortcut_comprehension",
        "recommended task command should expose the setup-comprehension task card",
    )
    require(task["claimBoundaryRequired"] is True, "recommended task should require claim-boundary capture")

    step_commands = {step["stepKey"]: step["command"] for step in status["commandSequence"]}
    require(
        step_commands["open_task_packet"] == "python3 scripts/ope.py pilot-session-packet --task engine_setup_shortcut_comprehension",
        "command sequence should start from the setup-comprehension task packet",
    )
    require(
        step_commands["use_agent_guide"] == "python3 scripts/ope.py agent-guide --section generic",
        "command sequence should include the generic agent guide for real-session moderation",
    )
    require(
        step_commands["classify_summary"] == "python3 scripts/ope.py pilot-summary-intake --input <summary.json>",
        "command sequence should classify sanitized summaries before ledger append",
    )
    require(
        step_commands["append_local_evidence"]
        == "python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
        "command sequence should append only after explicit local write",
    )
    require(
        step_commands["review_findings"] == "python3 scripts/ope.py pilot-findings --from-local-ledger --section summary",
        "command sequence should review local-ledger findings after append",
    )
    require(
        step_commands["review_status"] == "python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary",
        "command sequence should loop back to supervision status",
    )

    checks = {item["checkKey"]: item for item in status["evidenceLoopChecks"]}
    require(checks["sanitized_summary_required"]["required"] is True, "sanitized summary check should be required")
    require(checks["local_write_explicit"]["required"] is True, "local write check should be required")
    require(checks["no_quality_upgrade"]["required"] is True, "quality boundary check should be required")
    require_blocked_boundary(status["executionBoundary"])
    require(status["summary"]["pilotEvidenceReady"] is False, "summary must keep pilot evidence blocked")
    require(status["summary"]["expansionEvidenceReady"] is False, "summary must keep expansion blocked")
    require(status["summary"]["qualityClaimAllowed"] is False, "summary must keep quality claims blocked")
    require(status["summary"]["hostedRuntimeAllowed"] is False, "summary must keep hosted runtime blocked")
    require(status["summary"]["generatedTypesEvidenceReady"] is False, "summary must keep generated types blocked")


def check_local_ledger_status() -> None:
    with TemporaryDirectory() as tmp:
        local_ledger = Path(tmp) / "pilot-evidence-ledger.json"
        append_plan = build_local_pilot_evidence_append_plan(
            ACCEPTED_SUMMARY,
            write_local=True,
            local_ledger_path=local_ledger,
        )
        require(append_plan["appendDecision"] == "written_to_local_ledger", "setup fixture should write one local row")
        status = build_pilot_supervision_status(from_local_ledger=True, local_ledger_path=local_ledger)
    progress = status["realSessionProgress"]
    require(status["localEvidenceMode"] == "ignored_local_ledger", "explicit local mode should read ignored evidence")
    require(status["localEvidenceStatus"] == "readable", "temporary local ledger should be readable")
    require(progress["acceptedRealSessionCount"] == 1, "local ledger should count one accepted real session")
    require(progress["remainingMinimumSessions"] == 2, "one accepted session should leave two minimum sessions")
    require(progress["remainingTargetSessions"] == 4, "one accepted session should leave four target sessions")
    require(status["status"] == "real_sessions_needed", "one local session should still require more real sessions")
    require(status["summary"]["pilotEvidenceReady"] is False, "one session must not unblock pilot evidence")
    require(status["summary"]["qualityClaimAllowed"] is False, "one session must not allow quality claims")


def check_cli_status() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-supervision-status", "--section", "summary"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    payload: dict[str, Any] = json.loads(result.stdout)
    require(payload["status"] == "real_sessions_needed", "CLI summary status should require real sessions")
    require(payload["remainingMinimumSessions"] == 3, "CLI summary should expose remaining minimum sessions")
    require(payload["recommendedScenarioKey"] == "engine_setup_shortcut_comprehension", "CLI summary recommended task drifted")


def main() -> None:
    check_default_status()
    check_local_ledger_status()
    check_cli_status()
    print("checked pilot supervision status")


if __name__ == "__main__":
    main()
