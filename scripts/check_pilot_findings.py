#!/usr/bin/env python3
"""Check pilot findings readback for real adoption sessions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_pilot_findings import build_pilot_findings, validate_pilot_findings
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("pilot findings generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_pilot_findings()
    validate_pilot_findings(record)

    require(record["pilotFindingsId"] == "pilotfindings-001", "pilot findings id drifted")
    require(
        record["findingsStatus"] == "agent_simulation_completed_real_sessions_needed",
        "pilot findings status drifted",
    )
    require(record["realSessionCount"] == 0, "pilot findings must not fabricate real sessions")
    require(record["simulatedAgentSessionCount"] == 5, "pilot findings should include five simulated sessions")
    require(record["minimumRealSessions"] == 3, "minimum real sessions drifted")
    require(record["targetRealSessions"] == 5, "target real sessions drifted")
    require(record["summary"]["acceptedRealSessionCount"] == 0, "accepted real session count drifted")
    require(
        record["summary"]["acceptedSimulatedAgentSessionCount"] == 5,
        "accepted simulated agent session count drifted",
    )
    require(record["summary"]["agentSimulationEvidenceReady"] is True, "agent simulation evidence should be ready")
    require(record["summary"]["pilotEvidenceReady"] is False, "real pilot evidence should still be blocked")
    require(record["summary"]["expansionEvidenceReady"] is False, "pilot findings must not unblock expansion")
    require(record["summary"]["generatedTypesEvidenceReady"] is False, "pilot findings must not unblock generated types")
    require(record["summary"]["qualityClaimAllowed"] is False, "pilot findings must not allow quality claims")
    require(record["summary"]["hostedRuntimeAllowed"] is False, "pilot findings must not allow hosted runtime")

    for key in [
        "rawTranscriptsStored",
        "privateDataStored",
        "credentialValuesStored",
        "hostProjectSecretsStored",
        "qualityClaimsUpgraded",
        "calibrationClaimsUpgraded",
        "hostedRuntimeUnblocked",
        "generatedTypesUnblocked",
    ]:
        require(record["executionBoundary"][key] is False, f"pilot findings boundary {key} should stay false")

    require(len(record["frictionSummary"]) >= 4, "pilot findings should expose friction rows")
    require(
        any(item["simulatedAgentSignalCount"] > 0 for item in record["frictionSummary"]),
        "pilot findings should expose simulated agent friction",
    )
    require(
        {item["frictionClass"] for item in record["frictionSummary"]}
        >= {"claim_boundary_confusion", "privacy_redaction_needed", "readback_navigation", "source_runtime_gap"},
        "pilot findings friction classes drifted",
    )
    require(
        record["nextActions"][0]["actionKey"] == "review_simulated_agent_pilot",
        "first next action should expose simulated pilot readback",
    )
    require(
        any(action["actionKey"] == "run_supervised_sessions" for action in record["nextActions"]),
        "next actions should still request real sessions",
    )

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-findings", "--section", "summary"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"pilot-findings CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["acceptedRealSessionCount"] == 0, "pilot-findings CLI summary drifted")
    require(payload["acceptedSimulatedAgentSessionCount"] == 5, "pilot-findings CLI simulated count drifted")
    require(payload["agentSimulationEvidenceReady"] is True, "pilot-findings CLI simulation readiness drifted")
    require(payload["pilotEvidenceReady"] is False, "pilot-findings CLI must keep evidence blocked")

    print("checked pilot findings")


if __name__ == "__main__":
    main()
