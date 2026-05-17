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

from ope_schema import SPEC, validate_record
from source_connector_catalog import (
    FORECAST_TIME_CONNECTORS,
    connector_policy_checks,
)


SUPPORTED_DOMAIN = "weather-logistics"
SUPPORTED_GEOGRAPHY = "Warsaw"
SUPPORTED_OUTPUT_TYPE = "binary"
SUPPORTED_HORIZON = "1-day"
MAX_FREE_COST_USD = 0
SUPPORTED_PROVIDED_CONNECTORS = {"committed_fixture", "manual_upload"}
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


def request_id(request: dict[str, Any]) -> str | None:
    value = request.get("requestId")
    return value if isinstance(value, str) else None


def source_policy_id(request: dict[str, Any]) -> str | None:
    policy = request.get("sourcePolicy")
    if not isinstance(policy, dict):
        return None
    value = policy.get("sourcePolicyId")
    return value if isinstance(value, str) else None


def controls_value(request: dict[str, Any], key: str) -> Any:
    controls = request.get("controls")
    if not isinstance(controls, dict):
        return None
    return controls.get(key)


def safe_question_hash(request: dict[str, Any]) -> str | None:
    text = request.get("questionText")
    if not isinstance(text, str):
        return None
    return question_hash(text)


def audit_log(request: dict[str, Any], status: str) -> dict[str, Any]:
    return {
        "requestId": request_id(request),
        "decisionStatus": status,
        "requestedAction": request.get("requestedAction"),
        "dataMode": request.get("dataMode"),
        "sourcePolicyId": source_policy_id(request),
        "questionHash": safe_question_hash(request),
        "rawQuestionLogged": False,
        "maxCostUsd": controls_value(request, "maxCostUsd"),
        "timeoutSeconds": controls_value(request, "timeoutSeconds"),
    }


def schema_reasons(request: dict[str, Any]) -> list[dict[str, str]]:
    errors = validate_record(request, SPEC / "forecast-request.schema.json")
    if not errors:
        return []
    reasons = [
        reason(
            "validation_failed",
            "Request contract validation failed.",
        )
    ]
    text = request.get("questionText")
    if isinstance(text, str):
        lowered = text.lower()
        if len(text) > 500:
            reasons.append(reason("oversized_input", "Request text exceeds the supported size limit."))
        if any(phrase in lowered for phrase in UNSAFE_PHRASES):
            reasons.append(reason("unsafe_request", "Request text failed safety review."))
    return reasons


def approval_required(request: dict[str, Any]) -> bool:
    risk = request["riskReview"]
    policy = request.get("sourcePolicy", {})
    return bool(policy.get("approvalRequired")) or any(
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
    data_mode = request["dataMode"]
    source_policy = request["sourcePolicy"]
    connectors = set(source_policy["allowedConnectors"])
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
    if data_mode == "provided":
        unsupported = connectors - SUPPORTED_PROVIDED_CONNECTORS
        if unsupported:
            reasons.append(reason("unsupported_connector", "Provided-data mode uses an unsupported connector."))
        if source_policy["allowNetworkAccess"]:
            reasons.append(reason("provided_data_network_disallowed", "Provided-data mode must not allow network access."))
        if source_policy["maxNetworkCalls"] != 0:
            reasons.append(reason("unexpected_network_call_cap", "Provided-data mode must use zero network calls."))
    if data_mode == "auto":
        checks = connector_policy_checks(source_policy)
        if checks["unregisteredConnectors"]:
            reasons.append(reason("connector_not_registered", "Auto data mode names a connector missing from the connector registry."))
        if checks["unsupportedConnectors"]:
            reasons.append(reason("unsupported_connector", "Auto data mode uses an unsupported connector."))
        if checks["resolutionOnlyConnectors"]:
            reasons.append(reason("resolution_only_connector", "Resolution-only connectors must not be used for forecast-time evidence."))
        if not connectors & FORECAST_TIME_CONNECTORS:
            reasons.append(reason("missing_forecast_time_connector", "Auto data mode requires at least one forecast-time connector."))
        if not source_policy["allowNetworkAccess"]:
            reasons.append(reason("auto_evidence_network_required", "Auto data mode requires explicit network access policy."))
        if source_policy["maxNetworkCalls"] <= 0:
            reasons.append(reason("missing_network_call_cap", "Auto data mode requires a positive network call cap."))
        if source_policy["maxCostUsd"] != MAX_FREE_COST_USD:
            reasons.append(reason("unexpected_source_cost", "Current auto evidence support must remain free."))
    if data_mode == "hybrid":
        reasons.append(reason("unsupported_data_mode", "Hybrid data mode is contracted but not implemented yet."))
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
    if source_policy["maxCostUsd"] > controls["maxCostUsd"]:
        reasons.append(reason("source_policy_exceeds_cost_cap", "Source policy cost cap exceeds request controls."))
    if source_policy["maxNetworkCalls"] > 0 and not source_policy["allowNetworkAccess"]:
        reasons.append(reason("network_policy_mismatch", "Network call cap requires explicit network access."))
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
    if not isinstance(request, dict):
        reasons = [reason("validation_failed", "Request contract validation failed.")]
        return {
            "requestId": None,
            "decisionStatus": "rejected",
            "executionAllowed": False,
            "effectfulGeneration": False,
            "reasonCodes": [item["code"] for item in reasons],
            "reasons": reasons,
            "auditLog": {
                "requestId": None,
                "decisionStatus": "rejected",
                "requestedAction": None,
                "dataMode": None,
                "sourcePolicyId": None,
                "questionHash": None,
                "rawQuestionLogged": False,
                "maxCostUsd": None,
                "timeoutSeconds": None,
            },
        }

    reasons = schema_reasons(request)
    if reasons:
        return {
            "requestId": request_id(request),
            "decisionStatus": "rejected",
            "executionAllowed": False,
            "effectfulGeneration": False,
            "reasonCodes": [item["code"] for item in reasons],
            "reasons": reasons,
            "auditLog": audit_log(request, "rejected"),
        }

    reasons = collect_reasons(request)
    status = decision_status(reasons)
    return {
        "requestId": request_id(request),
        "decisionStatus": status,
        "executionAllowed": status == "accepted",
        "effectfulGeneration": False,
        "reasonCodes": [item["code"] for item in reasons],
        "reasons": reasons,
        "auditLog": audit_log(request, status),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    decision = validate_request(load_json(args.input))
    sys.stdout.write(json.dumps(decision, indent=2, sort_keys=False) + "\n")


if __name__ == "__main__":
    main()
