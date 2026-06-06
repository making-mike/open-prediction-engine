#!/usr/bin/env python3
"""Check MCP adoption path transcript fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from check_mcp_adapter import assert_envelope, by_id, message, run_mcp
try:
    from generate_mcp_adoption_path import build_mcp_adoption_path, validate_mcp_adoption_path
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("MCP adoption path generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message_text: str) -> None:
    if not condition:
        raise AssertionError(message_text)


def agent_call(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", "agent-call", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(result.stdout.strip(), f"agent-call returned no JSON: {result.stderr}")
    require(result.returncode in {0, 1, 2, 3, 4, 5}, f"agent-call failed unexpectedly: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


def main() -> None:
    record = build_mcp_adoption_path()
    validate_mcp_adoption_path(record)

    require(record["mcpAdoptionPathId"] == "mcpadoptionpath-001", "MCP adoption path id drifted")
    require(record["adoptionStatus"] == "checked_mcp_adoption_transcripts", "MCP adoption status drifted")
    require(record["summary"]["successStepCount"] == 4, "success step count drifted")
    require(record["summary"]["blockedTranscriptCount"] == 5, "blocked transcript count drifted")
    require(record["executionBoundary"]["selectorOnlyArguments"] is True, "MCP arguments should stay selector-only")
    for key in [
        "acceptsCredentialValues",
        "acceptsRawSql",
        "acceptsRawPrivateRows",
        "fetchesLiveData",
        "opensNetworkListener",
        "hostedRuntime",
        "executesPrivateSources",
        "createsForecastArtifacts",
        "qualityClaimAllowed",
    ]:
        require(record["executionBoundary"][key] is False, f"MCP boundary {key} should stay false")

    tool_sequence = [step["toolName"] for step in record["successTranscript"]["steps"]]
    require(
        tool_sequence == [
            "ope_agent_integration_readiness",
            "ope_agent_integration_candidates",
            "ope_agent_integration_guided_forecast",
            "ope_forecast_card",
        ],
        "success transcript tool order drifted",
    )

    blocked_cases = {item["caseKey"]: item for item in record["blockedTranscripts"]}
    require(
        set(blocked_cases)
        == {
            "raw_credential_value",
            "raw_sql_query",
            "private_row_exposure",
            "unapproved_source",
            "response_too_large",
        },
        "blocked transcript coverage drifted",
    )

    messages = [
        message(
            1,
            "initialize",
            {
                "protocolVersion": "2025-11-25",
                "capabilities": {},
                "clientInfo": {"name": "ope-mcp-adoption-check", "version": "0.1.0"},
            },
        ),
        message(None, "notifications/initialized"),
        message(2, "tools/call", {"name": "ope_agent_integration_readiness", "arguments": {"scenario": "helsinki_bus_disruption"}}),
        message(3, "tools/call", {"name": "ope_agent_integration_candidates", "arguments": {"scenario": "helsinki_bus_disruption"}}),
        message(
            4,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "accepted_adapter_output"},
            },
        ),
        message(
            5,
            "tools/call",
            {
                "name": "ope_forecast_card",
                "arguments": {"forecastId": "forecast-1102", "questionId": "question-1102"},
            },
        ),
        message(
            6,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "raw_credential_value"},
            },
        ),
        message(
            7,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "raw_sql_query"},
            },
        ),
        message(
            8,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "private_row_exposure"},
            },
        ),
        message(
            9,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {"scenario": "helsinki_bus_disruption", "guidedCase": "unapproved_source"},
            },
        ),
        message(
            10,
            "tools/call",
            {
                "name": "ope_agent_integration_guided_forecast",
                "arguments": {
                    "scenario": "helsinki_bus_disruption",
                    "guidedCase": "accepted_adapter_output",
                    "maxBytes": 20,
                },
            },
        ),
    ]
    indexed = by_id(run_mcp(messages))

    readiness = indexed[2]["result"]["structuredContent"]
    assert_envelope(readiness)
    require(readiness["operation"] == "agent_integration_readiness", "MCP readiness operation drifted")
    require(readiness["payload"]["summary"]["firstForecastFastTargetMet"] is True, "MCP readiness status drifted")

    candidates = indexed[3]["result"]["structuredContent"]
    assert_envelope(candidates)
    require(candidates["operation"] == "agent_integration_candidates", "MCP candidates operation drifted")
    forecastable = [
        item
        for item in candidates["payload"]["candidateQuestions"]
        if item["status"] == "forecastable"
    ]
    require(forecastable, "MCP candidates lost forecastable rows")

    guided = indexed[4]["result"]["structuredContent"]
    assert_envelope(guided)
    require(guided["operation"] == "agent_integration_guided_forecast", "MCP guided operation drifted")
    require(guided["payload"]["forecastId"] == "forecast-1102", "MCP guided forecast binding drifted")
    require(guided["payload"]["forecastCardCommand"], "MCP guided forecast should return forecast-card command")

    card = indexed[5]["result"]["structuredContent"]
    assert_envelope(card)
    require(card["operation"] == "forecast_card", "MCP forecast-card operation drifted")
    require(card["recordBinding"]["forecastId"] == "forecast-1102", "MCP forecast-card binding drifted")

    for message_id, case_key in [
        (6, "raw_credential_value"),
        (7, "raw_sql_query"),
        (8, "private_row_exposure"),
        (9, "unapproved_source"),
    ]:
        envelope = indexed[message_id]["result"]["structuredContent"]
        assert_envelope(envelope)
        require(envelope["status"] == "ok", f"{case_key} MCP envelope should be a checked blocked readback")
        require(envelope["payload"]["guidedStatus"] == "blocked", f"{case_key} should be blocked")
        require(case_key in envelope["payload"]["blockerCodes"], f"{case_key} blocker code drifted")
        require(envelope["payload"]["forecastId"] is None, f"{case_key} should not bind forecast id")
        equivalent = agent_call("--operation", "agent_integration_guided_forecast", "--case", case_key)
        require(
            equivalent["payload"]["blockerCodes"] == envelope["payload"]["blockerCodes"],
            f"{case_key} MCP/agent-call blocker equivalence drifted",
        )

    too_large_result = indexed[10]["result"]
    require(too_large_result.get("isError") is True, "response-too-large MCP result should be an error")
    too_large = too_large_result["structuredContent"]
    assert_envelope(too_large)
    require(too_large["status"] == "error", "response-too-large envelope status drifted")
    require(too_large["exitCode"] == 5, "response-too-large exit code drifted")
    require(too_large["error"]["code"] == "response_too_large", "response-too-large error code drifted")
    equivalent_too_large = agent_call(
        "--operation",
        "agent_integration_guided_forecast",
        "--case",
        "accepted_adapter_output",
        "--max-bytes",
        "20",
    )
    require(
        equivalent_too_large["error"]["code"] == too_large["error"]["code"],
        "response-too-large MCP/agent-call equivalence drifted",
    )

    print("checked MCP adoption path")


if __name__ == "__main__":
    main()
