#!/usr/bin/env python3
"""Minimal local MCP stdio scaffold for OPE agent adapter operations."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, TextIO

from agent_adapter_dispatcher import (
    DEFAULT_CALLER_INTENT,
    DEFAULT_FORECAST_ID,
    DEFAULT_PRIVATE_SETUP_REQUEST_ID,
    DEFAULT_QUESTION_ID,
    output_envelope,
)
from generate_agent_adapter_protocol_map import OPERATIONS, build_protocol_map, mcp_tool_name
from generate_setup_engine import DEFAULT_GOAL, SETUP_ENGINE_VIEWS
from read_ope_record import DEFAULT_MAX_BYTES
from run_agent_forecast import build_summary as build_forecast_run_summary


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_VERSION = "2025-11-25"
SERVER_NAME = "open-prediction-engine"
SERVER_VERSION = "0.1.0"
FORECAST_RUN_TOOL_NAME = "ope_forecast_run"
TOOL_TO_OPERATION = {mcp_tool_name(operation): operation for operation in OPERATIONS}
JSONRPC_PARSE_ERROR = -32700
JSONRPC_INVALID_REQUEST = -32600
JSONRPC_METHOD_NOT_FOUND = -32601
JSONRPC_INVALID_PARAMS = -32602
JSONRPC_INTERNAL_ERROR = -32603


class McpProtocolError(Exception):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def render(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=False)


def response(message_id: str | int | None, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def error_response(message_id: str | int | None, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": message_id,
        "error": {
            "code": code,
            "message": message,
        },
    }


def input_schema(fields: list[dict[str, Any]]) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for item in fields:
        name = item["name"]
        if item["required"]:
            required.append(name)
        properties[name] = schema_for_field(item)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema


def schema_for_field(item: dict[str, Any]) -> dict[str, Any]:
    value_type = item["type"]
    base = {
        "description": item["notes"],
    }
    if value_type == "integer":
        base.update({"type": "integer", "minimum": 1})
    elif value_type == "id":
        base.update({"type": "string", "minLength": 1, "maxLength": 120})
    elif value_type == "string-list":
        base.update(
            {
                "type": "array",
                "maxItems": 24,
                "items": {"type": "string", "minLength": 1, "maxLength": 260},
            }
        )
    elif value_type == "path-or-json-object":
        base.update(
            {
                "oneOf": [
                    {"type": "string", "minLength": 1, "maxLength": 240},
                    {"type": "object"},
                ]
            }
        )
    else:
        base.update({"type": "string", "minLength": 1, "maxLength": 240})
    return base


def output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "agentEnvelopeId",
            "generatedAt",
            "operation",
            "recordBinding",
            "state",
            "status",
            "exitCode",
            "payload",
            "error",
            "warnings",
        ],
        "properties": {
            "agentEnvelopeId": {"type": "string"},
            "operation": {"type": "string"},
            "status": {"type": "string", "enum": ["ok", "error"]},
            "exitCode": {"type": "integer"},
            "payload": {"oneOf": [{"type": "object"}, {"type": "null"}]},
            "error": {"oneOf": [{"type": "object"}, {"type": "null"}]},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


def forecast_run_input_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "request": {
                "description": "Forecast request path or object. Defaults to the checked auto-evidence fixture request.",
                "oneOf": [
                    {"type": "string", "minLength": 1, "maxLength": 240},
                    {"type": "object"},
                ],
            },
            "maxBytes": {
                "description": "Caps the forecast-run summary size and returns a response_too_large summary when exceeded.",
                "type": "integer",
                "minimum": 1,
            },
        },
    }


def forecast_run_output_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": True,
        "required": [
            "forecastRunSummaryId",
            "runStatus",
            "decisionStatus",
            "recordBinding",
            "outputs",
            "error",
            "warnings",
        ],
        "properties": {
            "forecastRunSummaryId": {"type": "string"},
            "runStatus": {"type": "string"},
            "decisionStatus": {"type": "string"},
            "recordBinding": {"type": "object"},
            "outputs": {"type": "object"},
            "error": {"oneOf": [{"type": "object"}, {"type": "null"}]},
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


def tool_definitions() -> list[dict[str, Any]]:
    protocol_map = build_protocol_map()
    tools = []
    for operation in protocol_map["operations"]:
        tools.append(
            {
                "name": operation["mcp"]["toolName"],
                "title": operation["operation"].replace("_", " ").title(),
                "description": operation["usageGuidance"],
                "inputSchema": input_schema(operation["mcp"]["argumentFields"]),
                "outputSchema": output_schema(),
            }
        )
    tools.append(
        {
            "name": FORECAST_RUN_TOOL_NAME,
            "title": "Forecast Run",
            "description": "Run the fixture-safe OPE forecast orchestration and return a bound forecast-run summary.",
            "inputSchema": forecast_run_input_schema(),
            "outputSchema": forecast_run_output_schema(),
        }
    )
    return tools


def write_request_object(value: dict[str, Any]) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        suffix=".json",
        prefix="ope-mcp-request-",
        delete=False,
    )
    with tmp:
        json.dump(value, tmp)
        tmp.write("\n")
    return Path(tmp.name)


def normalized_arguments(operation: str, arguments: Any) -> tuple[argparse.Namespace, Path | None]:
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Tool arguments must be an object.")

    fields = {field["name"]: field for field in next_tool_fields(operation)}
    allowed = set(fields)
    unexpected = sorted(set(arguments) - allowed)
    if unexpected:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"Unknown tool argument: {unexpected[0]}")
    for name, field in fields.items():
        if field["required"] and name not in arguments:
            raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"Missing required tool argument: {name}")

    temporary_request: Path | None = None
    request_value = arguments.get("request")
    if isinstance(request_value, dict):
        temporary_request = write_request_object(request_value)
        request_path = temporary_request
    elif isinstance(request_value, str):
        request_path = Path(request_value)
    else:
        request_path = ROOT / "spec" / "fixtures" / "requests" / "auto-weather-logistics-request.json"

    max_bytes = arguments.get("maxBytes", DEFAULT_MAX_BYTES)
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "maxBytes must be a positive integer.")

    caller_intent = arguments.get("callerIntent", DEFAULT_CALLER_INTENT)
    if not isinstance(caller_intent, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "callerIntent must be a string.")

    forecast_id = arguments.get("forecastId", DEFAULT_FORECAST_ID)
    question_id = arguments.get("questionId", DEFAULT_QUESTION_ID)
    if not isinstance(forecast_id, str) or not isinstance(question_id, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "forecastId and questionId must be strings.")

    private_setup_request_id = arguments.get("privateSetupRequestId", DEFAULT_PRIVATE_SETUP_REQUEST_ID)
    private_setup_case = arguments.get("privateSetupCase")
    if not isinstance(private_setup_request_id, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "privateSetupRequestId must be a string.")
    if private_setup_case is not None and not isinstance(private_setup_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "privateSetupCase must be a string.")

    source_kind = arguments.get("sourceKind")
    if source_kind is not None and not isinstance(source_kind, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "sourceKind must be a string.")

    source_builder_case = arguments.get("sourceBuilderCase", "local_draft")
    if not isinstance(source_builder_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "sourceBuilderCase must be a string.")
    source_handoff_case = arguments.get("sourceHandoffCase", "unconfirmed_builder_draft")
    if not isinstance(source_handoff_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "sourceHandoffCase must be a string.")
    method_gate_case = arguments.get("methodGateCase", "unconfirmed_builder_draft")
    if not isinstance(method_gate_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "methodGateCase must be a string.")
    forecast_execution_case = arguments.get("forecastExecutionCase", "unconfirmed_builder_draft")
    if not isinstance(forecast_execution_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "forecastExecutionCase must be a string.")
    scenario = arguments.get("scenario", "helsinki_bus_disruption")
    if not isinstance(scenario, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "scenario must be a string.")
    goal = arguments.get("goal", DEFAULT_GOAL)
    if not isinstance(goal, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "goal must be a string.")
    setup_engine_view = arguments.get("view", "full")
    if not isinstance(setup_engine_view, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "view must be a string.")
    if setup_engine_view not in SETUP_ENGINE_VIEWS:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "view must be a supported setup-engine view.")
    guided_case = arguments.get("guidedCase", "accepted_adapter_output")
    if not isinstance(guided_case, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "guidedCase must be a string.")
    internal_operation = arguments.get("internalOperation", "read_status")
    if not isinstance(internal_operation, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "internalOperation must be a string.")
    prediction_id = arguments.get("predictionId", "predictioncampaign-001")
    if not isinstance(prediction_id, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "predictionId must be a string.")
    idempotency_key = arguments.get("idempotencyKey")
    if idempotency_key is not None and not isinstance(idempotency_key, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "idempotencyKey must be a string.")

    source_builder_inputs = arguments.get("sourceBuilderInputs", [])
    mapping_hints = arguments.get("mappingHints", [])
    if not isinstance(source_builder_inputs, list) or not all(isinstance(item, str) for item in source_builder_inputs):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "sourceBuilderInputs must be an array of strings.")
    if not isinstance(mapping_hints, list) or not all(isinstance(item, str) for item in mapping_hints):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "mappingHints must be an array of strings.")

    args = argparse.Namespace(
        operation=operation,
        request=request_path,
        forecast_id=forecast_id,
        question_id=question_id,
        private_setup_request_id=private_setup_request_id,
        private_setup_case=private_setup_case,
        source_kind=source_kind,
        source_builder_case=source_builder_case,
        source_builder_inputs=source_builder_inputs,
        source_builder_mapping_hints=mapping_hints,
        source_handoff_case=source_handoff_case,
        method_gate_case=method_gate_case,
        forecast_execution_case=forecast_execution_case,
        scenario=scenario,
        goal=goal,
        setup_engine_view=setup_engine_view,
        guided_case=guided_case,
        internal_operation=internal_operation,
        prediction_id=prediction_id,
        idempotency_key=idempotency_key,
        max_bytes=max_bytes,
        caller_intent=caller_intent,
    )
    return args, temporary_request


def next_tool_fields(operation: str) -> list[dict[str, Any]]:
    protocol_map = build_protocol_map()
    for item in protocol_map["operations"]:
        if item["operation"] == operation:
            return item["mcp"]["argumentFields"]
    raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"Unsupported operation: {operation}")


def call_tool(params: Any) -> dict[str, Any]:
    if not isinstance(params, dict):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "tools/call params must be an object.")
    tool_name = params.get("name")
    if not isinstance(tool_name, str):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "tools/call requires a tool name.")
    if tool_name == FORECAST_RUN_TOOL_NAME:
        return call_forecast_run(params.get("arguments"))
    if tool_name not in TOOL_TO_OPERATION:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"Unknown tool: {tool_name}")

    operation = TOOL_TO_OPERATION[tool_name]
    args, temporary_request = normalized_arguments(operation, params.get("arguments"))
    try:
        envelope = output_envelope(args)
    finally:
        if temporary_request is not None:
            try:
                temporary_request.unlink()
            except FileNotFoundError:
                pass

    envelope_text = json.dumps(envelope, indent=2, sort_keys=False)
    result = {
        "content": [
            {
                "type": "text",
                "text": envelope_text,
            }
        ],
        "structuredContent": envelope,
    }
    if envelope["status"] == "error":
        result["isError"] = True
    return result


def call_forecast_run(arguments: Any) -> dict[str, Any]:
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "Tool arguments must be an object.")
    unexpected = sorted(set(arguments) - {"request", "maxBytes"})
    if unexpected:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, f"Unknown tool argument: {unexpected[0]}")

    temporary_request: Path | None = None
    request_value = arguments.get("request")
    if isinstance(request_value, dict):
        temporary_request = write_request_object(request_value)
        request_path = temporary_request
    elif isinstance(request_value, str):
        request_path = Path(request_value)
    elif request_value is None:
        request_path = ROOT / "spec" / "fixtures" / "requests" / "auto-weather-logistics-request.json"
    else:
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "request must be a path string or object.")

    max_bytes = arguments.get("maxBytes")
    if max_bytes is not None and (not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 1):
        raise McpProtocolError(JSONRPC_INVALID_PARAMS, "maxBytes must be a positive integer.")

    try:
        summary = build_forecast_run_summary(request_path, max_bytes=max_bytes)
    finally:
        if temporary_request is not None:
            try:
                temporary_request.unlink()
            except FileNotFoundError:
                pass

    summary_text = json.dumps(summary, indent=2, sort_keys=False)
    result = {
        "content": [
            {
                "type": "text",
                "text": summary_text,
            }
        ],
        "structuredContent": summary,
    }
    if summary["runStatus"] != "completed":
        result["isError"] = True
    return result


def initialize_result() -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {
                "listChanged": False,
            }
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "title": "Open Prediction Engine",
            "version": SERVER_VERSION,
            "description": "Local OPE stdio MCP scaffold exposing schema-bound forecast adapter envelopes.",
        },
        "instructions": (
            "Use tools/list to inspect OPE forecast adapter tools. "
            "Tool calls return the OPE agent envelope as structuredContent."
        ),
    }


def handle_request(message: dict[str, Any], initialized: bool) -> tuple[dict[str, Any] | None, bool]:
    message_id = message.get("id")
    method = message.get("method")
    if not isinstance(method, str):
        raise McpProtocolError(JSONRPC_INVALID_REQUEST, "JSON-RPC method must be a string.")

    if "id" not in message:
        return None, initialized or method == "notifications/initialized"

    if method == "initialize":
        return response(message_id, initialize_result()), initialized
    if not initialized:
        raise McpProtocolError(JSONRPC_INVALID_REQUEST, "MCP client must initialize before calling tools.")
    if method == "tools/list":
        return response(message_id, {"tools": tool_definitions()}), initialized
    if method == "tools/call":
        return response(message_id, call_tool(message.get("params"))), initialized
    if method == "ping":
        return response(message_id, {}), initialized
    raise McpProtocolError(JSONRPC_METHOD_NOT_FOUND, f"Unsupported MCP method: {method}")


def serve(input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout) -> None:
    initialized = False
    for raw_line in input_stream:
        line = raw_line.strip()
        if not line:
            continue
        message_id: str | int | None = None
        try:
            message = json.loads(line)
            if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
                raise McpProtocolError(JSONRPC_INVALID_REQUEST, "Expected one JSON-RPC 2.0 request per line.")
            message_id = message.get("id")
            reply, initialized = handle_request(message, initialized)
        except json.JSONDecodeError:
            reply = error_response(None, JSONRPC_PARSE_ERROR, "Invalid JSON-RPC message.")
        except McpProtocolError as exc:
            reply = error_response(message_id, exc.code, exc.message)
        except Exception:
            reply = error_response(message_id, JSONRPC_INTERNAL_ERROR, "MCP adapter operation failed.")
        if reply is not None:
            output_stream.write(render(reply) + "\n")
            output_stream.flush()


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
