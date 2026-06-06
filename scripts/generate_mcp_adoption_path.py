#!/usr/bin/env python3
"""Generate or check MCP adoption path transcript fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spec" / "fixtures" / "generated" / "mcp-adoption" / "ope-mcp-adoption-path.generated.json"
SCHEMA = SPEC / "mcp-adoption-path.schema.json"
GENERATED_AT = "2026-06-05T15:20:00Z"


def success_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "toolName": "ope_agent_integration_readiness",
            "arguments": {"scenario": "helsinki_bus_disruption"},
            "expectedOperation": "agent_integration_readiness",
            "expectedStatus": "ready_for_agent_incorporation",
        },
        {
            "step": 2,
            "toolName": "ope_agent_integration_candidates",
            "arguments": {"scenario": "helsinki_bus_disruption"},
            "expectedOperation": "agent_integration_candidates",
            "expectedStatus": "candidates_available",
        },
        {
            "step": 3,
            "toolName": "ope_agent_integration_guided_forecast",
            "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "accepted_adapter_output"},
            "expectedOperation": "agent_integration_guided_forecast",
            "expectedStatus": "forecast_card_ready",
        },
        {
            "step": 4,
            "toolName": "ope_forecast_card",
            "arguments": {"forecastId": "forecast-1102", "questionId": "question-1102"},
            "expectedOperation": "forecast_card",
            "expectedStatus": "ok",
        },
    ]


def blocked_transcripts() -> list[dict[str, Any]]:
    blocked_cases = [
        ("raw_credential_value", ["raw_credential_value"], 0),
        ("raw_sql_query", ["raw_sql_query"], 0),
        ("private_row_exposure", ["private_row_exposure"], 0),
        ("unapproved_source", ["unapproved_source"], 0),
    ]
    rows = [
        {
            "transcriptId": f"mcpadoptionblocked-{index:03d}",
            "caseKey": case_key,
            "toolName": "ope_agent_integration_guided_forecast",
            "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": case_key},
            "expectedStatus": "blocked",
            "expectedExitCode": exit_code,
            "expectedBlockerCodes": blocker_codes,
            "forecastArtifactsCreated": False,
        }
        for index, (case_key, blocker_codes, exit_code) in enumerate(blocked_cases, start=1)
    ]
    rows.append(
        {
            "transcriptId": "mcpadoptionblocked-005",
            "caseKey": "response_too_large",
            "toolName": "ope_agent_integration_guided_forecast",
            "arguments": {
                "scenario": "helsinki_bus_disruption",
                "guidedCase": "accepted_adapter_output",
                "maxBytes": 20,
            },
            "expectedStatus": "response_too_large",
            "expectedExitCode": 5,
            "expectedBlockerCodes": ["response_too_large"],
            "forecastArtifactsCreated": False,
        }
    )
    return rows


def equivalence_checks() -> list[dict[str, Any]]:
    return [
        {
            "checkName": "readiness_envelope",
            "mcpToolName": "ope_agent_integration_readiness",
            "agentCallOperation": "agent_integration_readiness",
            "semanticFields": ["operation", "status", "payload.readinessStatus", "recordBinding"],
        },
        {
            "checkName": "candidate_contracts",
            "mcpToolName": "ope_agent_integration_candidates",
            "agentCallOperation": "agent_integration_candidates",
            "semanticFields": ["operation", "status", "payload.summary", "payload.candidates"],
        },
        {
            "checkName": "guided_forecast_success",
            "mcpToolName": "ope_agent_integration_guided_forecast",
            "agentCallOperation": "agent_integration_guided_forecast",
            "semanticFields": ["operation", "payload.forecastId", "payload.questionId", "payload.forecastCardCommand"],
        },
        {
            "checkName": "blocked_guided_cases",
            "mcpToolName": "ope_agent_integration_guided_forecast",
            "agentCallOperation": "agent_integration_guided_forecast",
            "semanticFields": ["payload.guidedStatus", "payload.blockerCodes", "payload.forecastId"],
        },
        {
            "checkName": "forecast_card_readback",
            "mcpToolName": "ope_forecast_card",
            "agentCallOperation": "forecast_card",
            "semanticFields": ["operation", "recordBinding.forecastId", "payload.record.forecast.probability"],
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "selectorOnlyArguments": True,
        "acceptsCredentialValues": False,
        "acceptsRawSql": False,
        "acceptsRawPrivateRows": False,
        "fetchesLiveData": False,
        "opensNetworkListener": False,
        "hostedRuntime": False,
        "executesPrivateSources": False,
        "createsForecastArtifacts": False,
        "qualityClaimAllowed": False,
    }


def build_mcp_adoption_path() -> dict[str, Any]:
    blocked = blocked_transcripts()
    checks = equivalence_checks()
    return {
        "mcpAdoptionPathId": "mcpadoptionpath-001",
        "generatedAt": GENERATED_AT,
        "adoptionStatus": "checked_mcp_adoption_transcripts",
        "mcpCommand": "python3 scripts/ope.py mcp-stdio",
        "successTranscript": {
            "transcriptId": "mcpadoptionsuccess-001",
            "scenario": "helsinki_bus_disruption",
            "steps": success_steps(),
            "expectedForecastId": "forecast-1102",
            "expectedQuestionId": "question-1102",
        },
        "blockedTranscripts": blocked,
        "equivalenceChecks": checks,
        "executionBoundary": execution_boundary(),
        "summary": {
            "successStepCount": 4,
            "blockedTranscriptCount": len(blocked),
            "equivalenceCheckCount": len(checks),
            "acceptedForecastId": "forecast-1102",
            "acceptedQuestionId": "question-1102",
        },
    }


def validate_mcp_adoption_path(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise AssertionError(f"MCP adoption path validation failed: {errors[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--view",
        choices=["full", "success", "blocked", "boundary", "summary"],
        default="full",
    )
    args = parser.parse_args()

    record = build_mcp_adoption_path()
    validate_mcp_adoption_path(record)
    rendered = render_json(record)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered, encoding="utf-8")
        print(f"generated {OUT.relative_to(ROOT)}")
        return

    if args.check:
        if not OUT.exists():
            raise SystemExit(f"missing generated MCP adoption path: {OUT}")
        current = OUT.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(f"MCP adoption path drift: {OUT}\nrun `python3 scripts/generate_mcp_adoption_path.py --write`")
        print("checked MCP adoption path")
        return

    if args.view == "success":
        payload: Any = record["successTranscript"]
    elif args.view == "blocked":
        payload = record["blockedTranscripts"]
    elif args.view == "boundary":
        payload = record["executionBoundary"]
    elif args.view == "summary":
        payload = {
            "mcpAdoptionPathId": record["mcpAdoptionPathId"],
            "adoptionStatus": record["adoptionStatus"],
            "summary": record["summary"],
        }
    else:
        payload = record
    print(json.dumps(payload, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
