#!/usr/bin/env python3
"""Check the sanitized pilot summary template readback."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from generate_pilot_summary_intake import classify_summary_file

try:
    from generate_pilot_summary_template import build_pilot_summary_template
except ModuleNotFoundError as exc:  # pragma: no cover - intentional TDD failure before implementation.
    raise AssertionError("pilot summary template generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_blocked_boundary(boundary: dict[str, bool]) -> None:
    require(boundary["readOnlyTemplate"] is True, "template should be read-only")
    require(boundary["writesCheckedFixtures"] is False, "template must not write checked fixtures")
    require(boundary["writesIgnoredLocalLedger"] is False, "template must not write ignored local evidence")
    require(boundary["runsPilotSessions"] is False, "template must not run pilot sessions")
    require(boundary["recordsRawTranscripts"] is False, "template must not record raw transcripts")
    require(boundary["storesPrivateData"] is False, "template must not store private data")
    require(boundary["storesCredentials"] is False, "template must not store credentials")
    require(boundary["storesPromptLogs"] is False, "template must not store prompt logs")
    require(boundary["storesParticipantIdentity"] is False, "template must not store participant identity")
    require(boundary["createsForecastArtifacts"] is False, "template must not create forecast artifacts")
    require(boundary["unblocksExpansion"] is False, "template must not unblock expansion")
    require(boundary["qualityClaimsUpgraded"] is False, "template must not upgrade quality claims")
    require(boundary["calibrationClaimsUpgraded"] is False, "template must not upgrade calibration claims")
    require(boundary["hostedRuntimeUnblocked"] is False, "template must not unblock hosted runtime")
    require(boundary["generatedTypesUnblocked"] is False, "template must not unblock generated types")


def check_default_template() -> None:
    template = build_pilot_summary_template()
    require(template["templateStatus"] == "ready_for_operator_fill", "template status drifted")
    require(template["recommendedTask"]["scenarioKey"] == "engine_setup_shortcut_comprehension", "default task should be setup comprehension")
    require(template["recommendedTask"]["taskId"] == "agentpilottask-006", "default task id drifted")
    draft = template["draftSubmission"]
    require(draft["evidenceClass"] == "future_real_summary", "draft should use future real summary evidence class")
    require(draft["taskRefs"] == ["agentpilottask-006"], "draft should bind to recommended task")
    require(draft["dimensionRatings"] == [], "draft should require operator-entered ratings")
    require(draft["riskSignals"]["unredactedSourceDetailDetected"] is True, "draft should classify as needs-redaction by default")
    require(template["templateSafety"]["draftClassifiesAs"] == "needs_redaction", "draft should not be ledger-ready unchanged")
    require(template["templateSafety"]["draftLedgerReady"] is False, "draft must not be ledger-ready unchanged")
    require(template["templateSafety"]["draftContributesRealSessionEvidence"] is False, "draft must not count real evidence")
    require(template["summary"]["draftLedgerReady"] is False, "summary should keep draft blocked until edited")
    require(template["summary"]["qualityClaimAllowed"] is False, "summary must keep quality claims blocked")
    require(template["summary"]["hostedRuntimeAllowed"] is False, "summary must keep hosted runtime blocked")
    require(template["summary"]["generatedTypesEvidenceReady"] is False, "summary must keep generated types blocked")
    require_blocked_boundary(template["executionBoundary"])

    guidance_by_field = {item["fieldName"]: item for item in template["fieldGuidance"]}
    require(guidance_by_field["dimensionRatings"]["required"] is True, "dimension rating guidance should be required")
    require("engine_setup_shortcut_comprehension" in guidance_by_field["dimensionRatings"]["allowedValues"], "dimension guidance should include setup comprehension")
    require(guidance_by_field["riskSignals"]["required"] is True, "risk signal guidance should be required")
    commands = {item["stepKey"]: item["command"] for item in template["commandSequence"]}
    require(commands["print_draft"] == "python3 scripts/ope.py pilot-summary-template --section draft", "template should expose draft print command")
    require(commands["classify_summary"] == "python3 scripts/ope.py pilot-summary-intake --input <summary.json>", "template should route to intake classifier")
    require(
        commands["append_local_evidence"]
        == "python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local",
        "template should preserve explicit local append command",
    )


def check_template_draft_classifies_blocked() -> None:
    template = build_pilot_summary_template()
    with TemporaryDirectory() as tmp:
        draft_path = Path(tmp) / "draft-summary.json"
        draft_path.write_text(json.dumps(template["draftSubmission"], indent=2) + "\n", encoding="utf-8")
        result = classify_summary_file(draft_path)
    require(result["intakeDecision"] == "needs_redaction", "draft should classify as needs_redaction")
    require(result["ledgerReady"] is False, "draft should not be ledger-ready")
    require(result["candidateRealSessionEvidence"] is False, "draft should not become candidate evidence")
    require(result["realSessionsRecorded"] == 0, "draft classification must not record sessions")
    require(result["ledgerRowsWritten"] == 0, "draft classification must not write rows")


def check_cli_template() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-summary-template", "--section", "summary"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    summary: dict[str, Any] = json.loads(result.stdout)
    require(summary["templateStatus"] == "ready_for_operator_fill", "CLI summary status drifted")
    require(summary["recommendedScenarioKey"] == "engine_setup_shortcut_comprehension", "CLI summary recommended task drifted")
    require(summary["draftLedgerReady"] is False, "CLI summary should keep draft blocked")
    require(summary["qualityClaimAllowed"] is False, "CLI summary should block quality claims")

    draft = subprocess.run(
        [sys.executable, "scripts/ope.py", "pilot-summary-template", "--section", "draft"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    draft_payload: dict[str, Any] = json.loads(draft.stdout)
    require(draft_payload["taskRefs"] == ["agentpilottask-006"], "CLI draft task refs drifted")
    require(draft_payload["riskSignals"]["unredactedSourceDetailDetected"] is True, "CLI draft should be blocked unchanged")


def main() -> None:
    check_default_template()
    check_template_draft_classifies_blocked()
    check_cli_template()
    print("checked pilot summary template")


if __name__ == "__main__":
    main()
