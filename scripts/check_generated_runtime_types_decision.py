#!/usr/bin/env python3
"""Check generated runtime types decision readback."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_generated_runtime_types_decision import (
        build_generated_runtime_types_decision,
        validate_generated_runtime_types_decision,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("generated runtime types decision generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_generated_runtime_types_decision()
    validate_generated_runtime_types_decision(record)

    require(record["generatedRuntimeTypesDecisionId"] == "generatedtypesdecision-001", "decision id drifted")
    require(record["decisionStatus"] == "defer_until_adoption_evidence", "decision status drifted")
    require(record["selectedLanguageTargets"] == [], "generated type targets should remain empty")
    require(record["firstAcceptedScope"] == [], "accepted type scope should remain empty")
    require(record["evidenceReview"]["acceptedRealSessionCount"] == 0, "decision must reflect zero real sessions")
    require(
        record["evidenceReview"]["acceptedSimulatedAgentSessionCount"] == 8,
        "decision should reflect simulated sessions",
    )
    require(
        record["evidenceReview"]["agentSimulationEvidenceReady"] is True,
        "decision should reflect ready simulated evidence",
    )
    require(record["evidenceReview"]["typeRelatedFrictionObserved"] is False, "type friction evidence should not be ready")
    require(record["jsonFallback"]["validatorCommand"] == "python3 scripts/ope.py validate --input <record.json>", "validator fallback drifted")
    require(
        any("prediction-feature-setup" in item for item in record["jsonFallback"]["stableJsonExamples"]),
        "prediction feature JSON fallback missing",
    )
    for key in [
        "hostedRuntimeImplied",
        "fullSpecSdkStabilityClaimed",
        "productionSourceParsingImplied",
        "qualityClaimsUpgraded",
        "generatedFilesWritten",
    ]:
        require(record["executionBoundary"][key] is False, f"decision boundary {key} should stay false")

    blocked = {item["caseKey"]: item for item in record["blockedBroaderGenerationCases"]}
    require(
        set(blocked)
        >= {"full_spec_sdk", "private_source_runtime_types", "hosted_client_sdk", "forecast_quality_model_types"},
        "blocked generation case coverage drifted",
    )

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "generated-types-decision", "--section", "summary"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"generated-types-decision CLI failed: {cli.stderr or cli.stdout}")
    payload = json.loads(cli.stdout)
    require(payload["decisionStatus"] == "defer_until_adoption_evidence", "CLI decision status drifted")
    require(payload["generatedTypesIncluded"] is False, "CLI should not include generated types")
    require(payload["acceptedSimulatedAgentSessionCount"] == 8, "CLI simulated session count drifted")

    print("checked generated runtime types decision")


if __name__ == "__main__":
    main()
