#!/usr/bin/env python3
"""Generate the compact prediction-feature setup contract readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-feature-setup"
OUTPUT_PATH = GENERATED / "ope-prediction-feature-setup.generated.json"
SCHEMA = SPEC / "prediction-feature-setup.schema.json"
GENERATED_AT = "2026-06-05T14:20:00Z"
CASE_KEYS = ["accepted", "needs_clarification", "blocked", "rejected", "response_too_large"]


class PredictionFeatureSetupError(Exception):
    pass


def request_field(field_name: str, field_type: str, purpose: str) -> dict[str, str]:
    return {"fieldName": field_name, "fieldType": field_type, "purpose": purpose}


def request_contract() -> dict[str, Any]:
    return {
        "contractId": "predictionfeaturesetuprequest-001",
        "contractStatus": "checked_compact_request_contract",
        "requiredFields": [
            request_field("hostFeatureIntent", "string", "Describe the host feature that needs prediction support."),
            request_field("decisionToSupport", "string", "Name the user or system decision that changes if a forecast is useful."),
            request_field("approvedSourceRefs", "array", "List approved source references, not raw rows or credentials."),
            request_field("resolutionHints", "array", "Name candidate outcome sources, windows, thresholds, or resolution rules."),
            request_field("responseSizeBudgetBytes", "integer", "Bound the response size for tool-call context."),
        ],
        "optionalFields": ["domainHint", "existingSetupId", "preferredSourceKind"],
        "acceptsCredentialValues": False,
        "acceptsRawPrivateRows": False,
        "acceptsRawSql": False,
    }


def response(
    case_key: str,
    decision: str,
    reason_codes: list[str],
    next_action: str,
    *,
    forecast_id: str | None = None,
    question_id: str | None = None,
    card: str | None = None,
    bundle: str | None = None,
) -> dict[str, Any]:
    return {
        "caseKey": case_key,
        "decision": decision,
        "reasonCodes": reason_codes,
        "requiredSourceRoles": ["weather_forecast", "historical_delay_baseline", "transit_delay_outcome"],
        "nextAction": next_action,
        "forecastId": forecast_id,
        "questionId": question_id,
        "forecastCardCommand": card,
        "lifecycleBundleCommand": bundle,
        "createsForecastArtifacts": False,
        "storesCredentialValues": False,
        "storesRawPrivateRows": False,
        "executesPrivateSources": False,
        "qualityClaimAllowed": False,
    }


def response_examples() -> list[dict[str, Any]]:
    card = "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102"
    bundle = "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102"
    return [
        response(
            "accepted",
            "forecast_card_ready",
            ["candidate_validated"],
            "Read the forecast card, then inspect the lifecycle bundle if provenance or method context is needed.",
            forecast_id="forecast-1102",
            question_id="question-1102",
            card=card,
            bundle=bundle,
        ),
        response(
            "needs_clarification",
            "needs_clarification",
            ["missing_threshold", "ambiguous_service_window"],
            "Ask the caller for a measurable threshold and a specific future service window.",
        ),
        response(
            "blocked",
            "blocked",
            ["raw_credential_value", "unapproved_source"],
            "Replace unsafe inputs with approved source references and credential references before retrying.",
        ),
        response(
            "rejected",
            "rejected",
            ["past_tense_question", "unresolvable_outcome"],
            "Use historical analysis or rewrite the request as a measurable future outcome.",
        ),
        response(
            "response_too_large",
            "response_too_large",
            ["response_size_budget_exceeded"],
            "Retry with a larger approved byte budget or request a narrower readback view.",
        ),
    ]


def interface_bindings() -> list[dict[str, str]]:
    return [
        {
            "interface": "cli",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py prediction-feature-setup",
            "boundary": "CLI returns compact checked readbacks over existing agent integration surfaces.",
        },
        {
            "interface": "agent_call",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py agent-call --operation prediction_feature_setup",
            "boundary": "Agent-call returns one transport-neutral envelope and does not accept raw private payloads.",
        },
        {
            "interface": "local_mcp_guidance",
            "implementedStatus": "guidance_only",
            "command": "spec/agent-adapter-protocol-map.md",
            "boundary": "MCP exposure should wrap the same compact response after the local tool is added.",
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "createsForecastArtifacts": False,
        "fetchesLiveData": False,
        "storesCredentialValues": False,
        "storesRawPrivateRows": False,
        "acceptsRawSql": False,
        "opensNetworkListener": False,
        "hostedRuntime": False,
        "qualityClaimAllowed": False,
    }


def build_prediction_feature_setup() -> dict[str, Any]:
    responses = response_examples()
    return {
        "predictionFeatureSetupId": "predictionfeaturesetup-001",
        "generatedAt": GENERATED_AT,
        "setupStatus": "checked_compact_contract",
        "requestContract": request_contract(),
        "responseExamples": responses,
        "interfaceBindings": interface_bindings(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "responseExampleCount": len(responses),
            "interfaceBindingCount": 3,
            "acceptedForecastId": "forecast-1102",
            "acceptedQuestionId": "question-1102",
        },
        "warnings": [
            "Prediction feature setup is a compact readback over existing OPE agent integration surfaces.",
            "Accepted responses return existing forecast-card and lifecycle-bundle commands rather than creating a new forecast path.",
            "Credential values, raw private rows, raw SQL, hidden live fetches, hosted runtime flags, and quality claims remain blocked.",
        ],
        "createsNewForecastPath": False,
        "hostedRuntimeRequired": False,
    }


def validate_prediction_feature_setup(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise PredictionFeatureSetupError("prediction feature setup failed schema validation")


def response_by_case(record: dict[str, Any], case_key: str) -> dict[str, Any]:
    for item in record["responseExamples"]:
        if item["caseKey"] == case_key:
            return item
    raise PredictionFeatureSetupError(f"unsupported case {case_key}")


def view_payload(record: dict[str, Any], view: str, case_key: str) -> Any:
    if view == "full":
        return record
    if view == "request":
        return record["requestContract"]
    if view == "responses":
        return record["responseExamples"]
    if view == "response":
        return response_by_case(record, case_key)
    if view == "interfaces":
        return record["interfaceBindings"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return {"predictionFeatureSetupId": record["predictionFeatureSetupId"], "setupStatus": record["setupStatus"], "summary": record["summary"]}
    raise PredictionFeatureSetupError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated prediction-feature setup fixture")
    parser.add_argument("--check", action="store_true", help="check generated prediction-feature setup fixture")
    parser.add_argument("--view", choices=["full", "request", "responses", "response", "interfaces", "boundary", "summary"], default="full")
    parser.add_argument("--case", choices=CASE_KEYS, default="accepted")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_prediction_feature_setup()
    validate_prediction_feature_setup(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="prediction feature setup",
            regen="python3 scripts/generate_prediction_feature_setup.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="prediction feature setup",
            regen="python3 scripts/generate_prediction_feature_setup.py --write",
        )
        return
    print(render_json(view_payload(record, args.view, args.case)), end="")


if __name__ == "__main__":
    main()
