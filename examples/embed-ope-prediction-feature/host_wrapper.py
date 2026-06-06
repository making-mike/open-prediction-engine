#!/usr/bin/env python3
"""Minimal host wrapper for embedding an OPE-backed prediction feature locally."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_ope(*args: str) -> dict[str, Any]:
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
        "qualityClaimAllowed": False,
    }


def blocked(reason_codes: list[str], next_action: str) -> dict[str, Any]:
    return {
        "exampleStatus": "blocked",
        "reasonCodes": reason_codes,
        "nextAction": next_action,
        "opeCommandExecuted": False,
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


def block_reasons(request: dict[str, Any]) -> list[str]:
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


def accepted_response(request: dict[str, Any]) -> dict[str, Any]:
    setup = run_ope("prediction-feature-setup", "--view", "response", "--case", "accepted")
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
    )
    return {
        "exampleStatus": "forecast_card_ready",
        "hostFeatureIntent": request["hostFeatureIntent"],
        "opeCommandExecuted": True,
        "setupResponse": setup,
        "forecastCard": card,
        "executionBoundary": boundary(),
        "summary": {
            "decision": setup["decision"],
            "forecastId": forecast_id,
            "questionId": question_id,
            "probability": card["record"]["forecast"]["probability"],
            "qualityClaimAllowed": setup["qualityClaimAllowed"],
        },
    }


def build_response(request: dict[str, Any]) -> dict[str, Any]:
    reasons = block_reasons(request)
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
