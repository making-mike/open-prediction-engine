#!/usr/bin/env python3
"""Minimal host wrapper for embedding an OPE-backed prediction feature locally."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rendered_ope_command(args: tuple[str, ...]) -> str:
    return "python3 scripts/ope.py " + shlex.join(args)


def run_ope(*args: str, call_sequence: list[str] | None = None) -> dict[str, Any]:
    if call_sequence is not None:
        call_sequence.append(rendered_ope_command(args))
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return json.loads(result.stdout)


def boundary() -> dict[str, bool]:
    return {
        "createsForecastArtifacts": False,
        "fetchesLiveData": False,
        "storesCredentialValues": False,
        "storesRawPrivateRows": False,
        "acceptsRawSql": False,
        "opensNetworkListener": False,
        "startsHiddenWorker": False,
        "hostedRuntime": False,
        "implementsOpeScoring": False,
        "implementsOpeCalibration": False,
        "implementsCustomRiskEngine": False,
        "qualityClaimAllowed": False,
    }


def blocked(
    reason_codes: list[str],
    next_action: str,
    *,
    setup_plan: dict[str, Any] | None = None,
    call_sequence: list[str] | None = None,
) -> dict[str, Any]:
    sequence = call_sequence or []
    return {
        "exampleStatus": "blocked",
        "reasonCodes": reason_codes,
        "nextAction": next_action,
        "opeCommandExecuted": bool(sequence),
        "opeCallSequence": sequence,
        "setupEnginePlan": setup_plan,
        "setupResponse": None,
        "forecastCard": None,
        "executionBoundary": boundary(),
        "summary": {
            "decision": "blocked",
            "forecastId": None,
            "questionId": None,
            "qualityClaimAllowed": False,
        },
    }


def unsafe_block_reasons(request: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if request.get("credentialValues") or request.get("rawCredentialValues"):
        reasons.append("raw_credentials")
    if request.get("rawPrivateRows"):
        reasons.append("raw_private_rows")
    if request.get("rawSql"):
        reasons.append("raw_sql")
    if any(not source.get("approved", False) for source in request.get("approvedSourceRefs", [])):
        reasons.append("unapproved_source")
    if request.get("evidenceTiming") == "post_outcome":
        reasons.append("post_outcome_evidence")
    if request.get("hostedRuntimeRequired") is True:
        reasons.append("hosted_runtime")
    return reasons


def source_role_aliases(source_role: str) -> set[str]:
    normalized = source_role.lower().replace("-", "_")
    aliases: set[str] = set()
    if "forecast" in normalized or "signal" in normalized or "weather" in normalized:
        aliases.add("forecast_time_signal")
    if "historical" in normalized or "history" in normalized or "baseline" in normalized:
        aliases.add("historical_outcome")
    if "resolution" in normalized or "outcome" in normalized:
        aliases.add("resolution_outcome")
    return aliases


def approved_role_coverage(request: dict[str, Any]) -> set[str]:
    coverage: set[str] = set()
    for source in request.get("approvedSourceRefs", []):
        if not source.get("approved", False):
            continue
        coverage.update(source_role_aliases(str(source.get("sourceRole", ""))))
    return coverage


def has_resolvable_outcome_definition(request: dict[str, Any]) -> bool:
    outcome = request.get("outcomeDefinition")
    if not isinstance(outcome, dict):
        return False
    required = ("metric", "threshold", "window")
    return all(outcome.get(key) not in (None, "") for key in required)


def setup_block_reasons(request: dict[str, Any], setup: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    required_roles = {
        role["roleName"]
        for role in setup["requiredSourceRoles"]
        if role["roleName"] in {"forecast_time_signal", "historical_outcome", "resolution_outcome"}
    }
    if not required_roles <= approved_role_coverage(request):
        reasons.append("missing_source_roles")
    if not has_resolvable_outcome_definition(request):
        reasons.append("vague_outcome")
    return reasons


def setup_engine_plan(setup: dict[str, Any]) -> dict[str, Any]:
    return {
        "setupEngineId": setup["setupEngineId"],
        "setupStatus": setup["engineSetupStatus"],
        "goal": setup["goal"],
        "renderBeforeForecastArtifacts": setup["hostWrapper"]["renderBeforeForecastArtifacts"],
        "candidateContracts": [
            {
                "contractId": contract["contractId"],
                "title": contract["title"],
                "status": contract["contractStatus"],
                "questionTemplate": contract["questionTemplate"],
                "requiredSourceRoles": contract["requiredSourceRoles"],
                "baselineMethodId": contract["baselineMethod"]["methodId"],
                "nextAction": contract["nextAction"],
            }
            for contract in setup["candidateForecastContracts"]
        ],
        "sourceRoles": [role["roleName"] for role in setup["requiredSourceRoles"]],
        "baselineStatus": {
            "defaultMethodId": setup["baselineGuidance"]["defaultMethodId"],
            "benchmarkGateRequired": setup["baselineGuidance"]["benchmarkGateRequired"],
            "calibrationGateRequired": setup["baselineGuidance"]["calibrationGateRequired"],
            "strongerMethodsAllowedAfter": setup["baselineGuidance"]["strongerMethodsAllowedAfter"],
        },
        "forecastCardPreview": {
            "readAfter": "accepted prediction-feature setup response",
            "fields": [
                "forecastId",
                "questionId",
                "probability",
                "baselineMethod",
                "sourceSummary",
                "claimWarning",
            ],
            "qualityClaimAllowed": setup["claimBoundary"]["qualityClaimAllowed"],
        },
        "requiredHostInputs": [
            "hostFeatureIntent",
            "decisionToSupport",
            "approvedSourceRefs",
            "outcomeDefinition",
            "resolutionHints",
            "responseSizeBudgetBytes",
        ],
        "warnings": setup["warnings"]
        + [
            "Host wrapper renders OPE setup output; it does not implement OPE scoring or calibration.",
            "Custom methods should be added through OPE method extensions and gates, not an untracked host risk engine.",
        ],
        "customMethodExtension": {
            "allowedPath": "Add a custom forecast method through OPE method registry, setup benchmark, leakage, approval, and rollback gates.",
            "untrackedRiskEngineAllowed": False,
        },
    }


def accepted_response(request: dict[str, Any]) -> dict[str, Any]:
    call_sequence: list[str] = []
    goal = str(request.get("setupGoal") or request["hostFeatureIntent"])
    setup_engine = run_ope("setup-engine", "--goal", goal, call_sequence=call_sequence)
    plan = setup_engine_plan(setup_engine)
    setup_reasons = setup_block_reasons(request, setup_engine)
    if setup_reasons:
        return blocked(
            setup_reasons,
            "Render the setup plan, add the missing host inputs or approved source-role references, then rerun the wrapper.",
            setup_plan=plan,
            call_sequence=call_sequence,
        )

    setup = run_ope("prediction-feature-setup", "--view", "response", "--case", "accepted", call_sequence=call_sequence)
    forecast_id = setup["forecastId"]
    question_id = setup["questionId"]
    card = run_ope(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        forecast_id,
        "--question-id",
        question_id,
        call_sequence=call_sequence,
    )
    return {
        "exampleStatus": "setup_plan_and_forecast_card_ready",
        "hostFeatureIntent": request["hostFeatureIntent"],
        "opeCommandExecuted": True,
        "opeCallSequence": call_sequence,
        "setupEnginePlan": plan,
        "setupResponse": setup,
        "forecastCard": card,
        "executionBoundary": boundary(),
        "summary": {
            "decision": "setup_plan_and_forecast_card_ready",
            "setupStatus": plan["setupStatus"],
            "setupRenderedBeforeForecastCard": True,
            "forecastId": forecast_id,
            "questionId": question_id,
            "probability": card["record"]["forecast"]["probability"],
            "qualityClaimAllowed": setup["qualityClaimAllowed"],
        },
    }


def build_response(request: dict[str, Any]) -> dict[str, Any]:
    reasons = unsafe_block_reasons(request)
    if reasons:
        return blocked(
            reasons,
            "Remove unsafe inline data or assumptions, replace them with approved source references, then rerun the wrapper.",
        )
    return accepted_response(request)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="Path to a host feature request JSON file.")
    parser.add_argument("--output-format", choices=["json"], default="json")
    args = parser.parse_args()

    request_path = (ROOT / args.request).resolve()
    request = load_json(request_path)
    print(json.dumps(build_response(request), indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
