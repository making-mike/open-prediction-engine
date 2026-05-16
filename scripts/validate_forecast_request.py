#!/usr/bin/env python3
"""Validate controlled OPE forecast requests without executing them."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


SUPPORTED_DOMAIN = "weather-logistics"
SUPPORTED_GEOGRAPHY = "Warsaw"
SUPPORTED_OUTPUT_TYPE = "binary"
SUPPORTED_HORIZON = "1-day"
MAX_FREE_COST_USD = 0
UNSAFE_PHRASES = [
    "ignore previous",
    "reveal any secrets",
    "exfiltrate",
    "system prompt",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def question_hash(question_text: str) -> str:
    return "sha256-" + hashlib.sha256(question_text.encode("utf-8")).hexdigest()


def reason(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def approval_required(request: dict[str, Any]) -> bool:
    risk = request["riskReview"]
    return any(
        bool(risk[key])
        for key in ["highImpact", "paid", "external", "privacySensitive"]
    )


def validate_service_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def collect_reasons(request: dict[str, Any]) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    text = request["questionText"].lower()
    if any(phrase in text for phrase in UNSAFE_PHRASES):
        reasons.append(reason("unsafe_request", "Request text failed safety review."))
    if len(request["questionText"]) > 500:
        reasons.append(reason("oversized_input", "Request text exceeds the supported size limit."))
    if request["domain"] != SUPPORTED_DOMAIN:
        reasons.append(reason("unsupported_domain", "Domain is not supported."))
    if request["geography"] != SUPPORTED_GEOGRAPHY:
        reasons.append(reason("unsupported_geography", "Geography is not allow-listed."))
    if request["outputType"] != SUPPORTED_OUTPUT_TYPE:
        reasons.append(reason("unsupported_output_type", "Output type is not supported."))
    if request["horizonLabel"] != SUPPORTED_HORIZON:
        reasons.append(reason("unsupported_horizon", "Horizon is not supported."))
    if not validate_service_date(request["serviceDate"]):
        reasons.append(reason("invalid_service_date", "Service date is invalid."))
    if "?" not in request["questionText"]:
        reasons.append(reason("unresolvable_question", "Question text must be an explicit question."))
    controls = request["controls"]
    if controls["cancelRequested"]:
        reasons.append(reason("canceled", "Request was canceled before execution."))
    if controls["timeoutSeconds"] <= 0:
        reasons.append(reason("timeout_invalid", "Timeout must be positive."))
    paid = bool(request["riskReview"]["paid"])
    if paid and controls["maxCostUsd"] <= 0:
        reasons.append(reason("missing_cost_cap", "Paid requests require a positive cost cap."))
    if not paid and controls["maxCostUsd"] != MAX_FREE_COST_USD:
        reasons.append(reason("unexpected_cost_cap", "Unpaid requests must use a zero cost cap."))
    if approval_required(request) and request["approval"]["status"] != "approved":
        reasons.append(reason("approval_required", "Request requires approval before execution."))
    if request["approval"]["status"] == "rejected":
        reasons.append(reason("approval_rejected", "Request approval was rejected."))
    return reasons


def decision_status(reasons: list[dict[str, str]]) -> str:
    codes = {item["code"] for item in reasons}
    if "canceled" in codes:
        return "canceled"
    if "approval_required" in codes and len(codes) == 1:
        return "blocked"
    if codes:
        return "rejected"
    return "accepted"


def validate_request(request: dict[str, Any]) -> dict[str, Any]:
    reasons = collect_reasons(request)
    status = decision_status(reasons)
    return {
        "requestId": request["requestId"],
        "decisionStatus": status,
        "executionAllowed": status == "accepted",
        "effectfulGeneration": False,
        "reasonCodes": [item["code"] for item in reasons],
        "reasons": reasons,
        "auditLog": {
            "requestId": request["requestId"],
            "decisionStatus": status,
            "requestedAction": request["requestedAction"],
            "questionHash": question_hash(request["questionText"]),
            "rawQuestionLogged": False,
            "maxCostUsd": request["controls"]["maxCostUsd"],
            "timeoutSeconds": request["controls"]["timeoutSeconds"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    decision = validate_request(load_json(args.input))
    sys.stdout.write(json.dumps(decision, indent=2, sort_keys=False) + "\n")


if __name__ == "__main__":
    main()
