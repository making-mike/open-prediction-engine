#!/usr/bin/env python3
"""Smoke-test the local MCP stdio scaffold for OPE agent tools."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from generate_forecast_run_intake_matrix import CASES, build_matrix
from generate_agent_adapter_protocol_map import OPERATIONS, mcp_tool_name
from ope_schema import SPEC, validate_record
from ope_mcp_stdio import FORECAST_RUN_TOOL_NAME


ROOT = Path(__file__).resolve().parents[1]


def message(message_id: int | None, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {
        "jsonrpc": "2.0",
        "method": method,
    }
    if message_id is not None:
        item["id"] = message_id
    if params is not None:
        item["params"] = params
    return item


def run_mcp(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = "\n".join(json.dumps(item, separators=(",", ":")) for item in messages) + "\n"
    completed = subprocess.run(
        [sys.executable, "scripts/ope.py", "mcp-stdio"],
        cwd=ROOT,
        input=payload,
        text=True,
        capture_output=True,
        check=True,
    )
    if "/Users/" in completed.stdout or "Traceback" in completed.stderr:
        raise AssertionError("MCP output should not expose local paths or tracebacks")
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    responses = [json.loads(line) for line in lines]
    for item in responses:
        if item.get("jsonrpc") != "2.0":
            raise AssertionError("MCP response should be JSON-RPC 2.0")
    return responses


def by_id(responses: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed = {}
    for item in responses:
        if "id" in item:
            indexed[item["id"]] = item
    return indexed


def assert_envelope(data: dict[str, Any]) -> None:
    errors = validate_record(data, SPEC / "agent-envelope.schema.json")
    if errors:
        raise AssertionError(f"MCP structured envelope failed schema validation: {errors[0]}")


def assert_forecast_run(data: dict[str, Any]) -> None:
    errors = validate_record(data, SPEC / "forecast-run-summary.schema.json")
    if errors:
        raise AssertionError(f"MCP forecast-run summary failed schema validation: {errors[0]}")


def forecast_run_arguments(case: Any) -> dict[str, Any]:
    arguments: dict[str, Any] = {}
    if case.outcome_class not in {"accepted", "response_too_large"}:
        arguments["request"] = str(case.request_path.relative_to(ROOT))
    if case.max_bytes is not None:
        arguments["maxBytes"] = case.max_bytes
    return arguments


def assert_forecast_run_result(
    result: dict[str, Any],
    expectation: dict[str, Any],
    *,
    outcome_class: str,
) -> None:
    actual_is_error = bool(result.get("isError"))
    if actual_is_error is not expectation["mcpExpectation"]["isError"]:
        raise AssertionError(f"{outcome_class} MCP result had wrong isError state")
    summary = result["structuredContent"]
    assert_forecast_run(summary)
    if json.loads(result["content"][0]["text"])["forecastRunSummaryId"] != summary["forecastRunSummaryId"]:
        raise AssertionError(f"{outcome_class} MCP text content should mirror structured forecast-run JSON")
    if summary["runStatus"] != expectation["runStatus"]:
        raise AssertionError(f"{outcome_class} MCP forecast-run returned wrong run status")
    if summary["decisionStatus"] != expectation["decisionStatus"]:
        raise AssertionError(f"{outcome_class} MCP forecast-run returned wrong decision status")
    error_code = summary["error"]["code"] if isinstance(summary["error"], dict) else None
    if error_code != expectation["errorCode"]:
        raise AssertionError(f"{outcome_class} MCP forecast-run returned wrong error code")
    if outcome_class == "accepted":
        if summary["recordBinding"]["forecastId"] != "forecast-602":
            raise AssertionError("accepted MCP forecast-run should bind forecast-602")
        if summary["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
            raise AssertionError("accepted MCP forecast-run should keep quality claim provisional")
    else:
        if summary["recordBinding"]["forecastId"] is not None:
            raise AssertionError(f"{outcome_class} MCP forecast-run must not bind a forecast")
        if summary["outputs"]["forecastCard"] is not None:
            raise AssertionError(f"{outcome_class} MCP forecast-run must not link a forecast card")
        if summary["forecast"] is not None or summary["qualityClaim"] is not None:
            raise AssertionError(f"{outcome_class} MCP forecast-run must not include forecast or quality claims")


def main() -> None:
    matrix, _summaries = build_matrix()
    expected_outcomes = {item["outcomeClass"]: item for item in matrix["outcomes"]}
    forecast_run_ids = {
        case.outcome_class: 6 + index
        for index, case in enumerate(CASES)
    }
    forecast_run_messages = [
        message(
            forecast_run_ids[case.outcome_class],
            "tools/call",
            {
                "name": FORECAST_RUN_TOOL_NAME,
                "arguments": forecast_run_arguments(case),
            },
        )
        for case in CASES
    ]
    responses = run_mcp(
        [
            message(
                1,
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "ope-mcp-check",
                        "version": "0.1.0",
                    },
                },
            ),
            message(None, "notifications/initialized"),
            message(2, "tools/list"),
            message(
                3,
                "tools/call",
                {
                    "name": "ope_forecast_card",
                    "arguments": {
                        "forecastId": "forecast-602",
                        "questionId": "question-601",
                    },
                },
            ),
            message(
                4,
                "tools/call",
                {
                    "name": "ope_evidence_trace",
                    "arguments": {
                        "forecastId": "forecast-602",
                        "questionId": "question-601",
                    },
                },
            ),
            message(
                5,
                "tools/call",
                {
                    "name": "ope_evidence_plan",
                    "arguments": {
                        "request": "spec/fixtures/requests/approval-required-sensitive-request.json",
                    },
                },
            ),
            *forecast_run_messages,
            message(
                6 + len(CASES),
                "tools/call",
                {
                    "name": "ope_missing_tool",
                    "arguments": {},
                },
            ),
        ]
    )
    indexed = by_id(responses)

    initialize = indexed[1]["result"]
    if initialize["protocolVersion"] != "2025-11-25":
        raise AssertionError("MCP initialize should use the checked protocol version")
    if "tools" not in initialize["capabilities"]:
        raise AssertionError("MCP initialize should advertise tool support")

    tools = indexed[2]["result"]["tools"]
    names = {tool["name"] for tool in tools}
    expected_names = {mcp_tool_name(operation) for operation in OPERATIONS}
    expected_names.add(FORECAST_RUN_TOOL_NAME)
    if names != expected_names:
        raise AssertionError("MCP tools/list should expose the mapped OPE tools")
    for tool in tools:
        schema = tool["inputSchema"]
        if schema.get("additionalProperties") is not False:
            raise AssertionError(f"{tool['name']} should reject unexpected prompt-visible arguments")
        prompt_visible = " ".join(schema.get("properties", {})).lower()
        for forbidden in ["secret", "token", "authorization", "credential", "api_key"]:
            if forbidden in prompt_visible:
                raise AssertionError(f"{tool['name']} should not expose credential arguments")

    card = indexed[3]["result"]
    if card.get("isError"):
        raise AssertionError("forecast-card MCP tool should succeed")
    card_envelope = card["structuredContent"]
    assert_envelope(card_envelope)
    if card_envelope["operation"] != "forecast_card":
        raise AssertionError("forecast-card MCP tool returned the wrong operation")
    if card_envelope["recordBinding"]["forecastId"] != "forecast-602":
        raise AssertionError("forecast-card MCP tool lost forecast binding")
    if json.loads(card["content"][0]["text"])["agentEnvelopeId"] != card_envelope["agentEnvelopeId"]:
        raise AssertionError("text content should mirror structured envelope JSON")

    trace = indexed[4]["result"]
    if trace.get("isError"):
        raise AssertionError("evidence-trace MCP tool should succeed")
    trace_envelope = trace["structuredContent"]
    assert_envelope(trace_envelope)
    if trace_envelope["operation"] != "evidence_trace":
        raise AssertionError("evidence-trace MCP tool returned the wrong operation")
    if trace_envelope["payload"]["record"]["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence-trace MCP tool lost connector result-set binding")

    approval = indexed[5]["result"]
    if approval.get("isError") is not True:
        raise AssertionError("approval-required MCP tool should return a tool execution error")
    approval_envelope = approval["structuredContent"]
    assert_envelope(approval_envelope)
    if approval_envelope["exitCode"] != 3:
        raise AssertionError("approval-required MCP envelope should preserve exit code 3")
    if approval_envelope["error"]["code"] != "approval_required":
        raise AssertionError("approval-required MCP envelope should preserve error code")

    for case in CASES:
        result = indexed[forecast_run_ids[case.outcome_class]]["result"]
        assert_forecast_run_result(
            result,
            expected_outcomes[case.outcome_class],
            outcome_class=case.outcome_class,
        )

    unknown = indexed[6 + len(CASES)]
    if unknown["error"]["code"] != -32602:
        raise AssertionError("unknown MCP tools should return a protocol invalid-params error")

    print("checked local MCP stdio adapter")


if __name__ == "__main__":
    main()
