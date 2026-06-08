#!/usr/bin/env python3
"""Check pilot findings readback for real adoption sessions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

try:
    from generate_pilot_evidence_ledger import build_local_pilot_evidence_append_plan
    from generate_pilot_findings import build_pilot_findings, validate_pilot_findings
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("pilot findings generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
ACCEPTED_SUMMARY = ROOT / "spec" / "fixtures" / "pilot-summary-intake" / "accepted-setup-engine-summary.json"


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
    require(record["simulatedAgentSessionCount"] == 8, "pilot findings should include eight simulated sessions")
    require(record["minimumRealSessions"] == 3, "minimum real sessions drifted")
    require(record["targetRealSessions"] == 5, "target real sessions drifted")
    require(record["summary"]["acceptedRealSessionCount"] == 0, "accepted real session count drifted")
    require(
        record["summary"]["acceptedSimulatedAgentSessionCount"] == 8,
        "accepted simulated agent session count drifted",
    )
    require(record["summary"]["nonHelsinkiSimulatedSessionCount"] == 3, "pilot findings should report non-Helsinki sessions")
    require(record["summary"]["setupEngineFirstRate"] >= 0.8, "setup-engine-first rate should meet comprehension threshold")
    require(record["summary"]["parallelRiskEngineProposalCount"] == 1, "parallel risk-engine confusion count drifted")
    require(record["summary"]["auditLayerConfusionCount"] == 1, "audit-layer confusion count drifted")
    require(record["summary"]["agentSimulationEvidenceReady"] is True, "agent simulation evidence should be ready")
    require(record["summary"]["pilotEvidenceReady"] is False, "real pilot evidence should still be blocked")
    require(record["summary"]["expansionEvidenceReady"] is False, "pilot findings must not unblock expansion")
    require(record["summary"]["generatedTypesEvidenceReady"] is False, "pilot findings must not unblock generated types")
    require(record["summary"]["qualityClaimAllowed"] is False, "pilot findings must not allow quality claims")
    require(record["summary"]["hostedRuntimeAllowed"] is False, "pilot findings must not allow hosted runtime")
    require(record["summary"]["localPilotEvidenceMode"] == "not_requested", "default local evidence mode drifted")
    require(record["summary"]["localPilotEvidenceStatus"] == "not_requested", "default local evidence status drifted")
    require(record["summary"]["localLedgerRowCount"] == 0, "default local ledger row count drifted")

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
        any(item["frictionClass"] == "audit_layer_only_confusion" for item in record["frictionSummary"]),
        "pilot findings should expose audit-layer-only confusion",
    )
    require(
        any(item["frictionClass"] == "parallel_risk_engine_confusion" for item in record["frictionSummary"]),
        "pilot findings should expose parallel risk-engine confusion",
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
    require(payload["acceptedSimulatedAgentSessionCount"] == 8, "pilot-findings CLI simulated count drifted")
    require(payload["nonHelsinkiSimulatedSessionCount"] == 3, "pilot-findings CLI non-Helsinki count drifted")
    require(payload["setupEngineFirstRate"] >= 0.8, "pilot-findings CLI setup-engine rate drifted")
    require(payload["agentSimulationEvidenceReady"] is True, "pilot-findings CLI simulation readiness drifted")
    require(payload["pilotEvidenceReady"] is False, "pilot-findings CLI must keep evidence blocked")

    with TemporaryDirectory() as tmp:
        local_ledger = Path(tmp) / "pilot-evidence-ledger.json"
        build_local_pilot_evidence_append_plan(
            ACCEPTED_SUMMARY,
            write_local=True,
            local_ledger_path=local_ledger,
        )
        local_record = build_pilot_findings(
            from_local_ledger=True,
            local_ledger_path=local_ledger,
        )
        validate_pilot_findings(local_record)
        require(local_record["realSessionCount"] == 1, "local pilot findings should count temp local session")
        require(local_record["summary"]["acceptedRealSessionCount"] == 1, "local findings accepted count drifted")
        require(local_record["summary"]["localPilotEvidenceMode"] == "ignored_local_ledger", "local findings mode drifted")
        require(local_record["summary"]["localPilotEvidenceStatus"] == "readable", "local findings should read temp ledger")
        require(local_record["summary"]["localLedgerRowCount"] == 1, "local findings row count drifted")
        require(local_record["summary"]["pilotEvidenceReady"] is False, "one local session should not unblock pilot evidence")
        require(local_record["summary"]["expansionEvidenceReady"] is False, "local findings must not unblock expansion")
        require(local_record["summary"]["qualityClaimAllowed"] is False, "local findings must not allow quality claims")
        require(
            any(
                item["frictionClass"] == "none" and item["realSessionSignalCount"] == 1
                for item in local_record["frictionSummary"]
            ),
            "local findings should include real-session friction counts",
        )

    print("checked pilot findings")


if __name__ == "__main__":
    main()
