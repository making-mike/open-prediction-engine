#!/usr/bin/env python3
"""Generate or check the OPE agent adapter protocol mapping."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-adapter"
MAP_PATH = GENERATED / "ope-agent-adapter-protocol-map.generated.json"
SCHEMA = SPEC / "agent-adapter-protocol-map.schema.json"
ENVELOPE_SCHEMA = "spec/agent-envelope.schema.json"
GENERATED_AT = "2026-06-06T12:45:00Z"
MCP_PROTOCOL_VERSION = "2025-11-25"

OPERATIONS = [
    "forecast_request_validation",
    "evidence_plan",
    "evidence_trace",
    "forecast_card",
    "lifecycle_bundle",
    "resolution_status",
    "scoring_summary",
]

INPUT_RECORD_TYPES = {
    "forecast_request_validation": "forecast_request",
    "evidence_plan": "evidence_gathering_plan",
    "evidence_trace": "evidence_trace",
    "forecast_card": "forecast_card",
    "lifecycle_bundle": "lifecycle_bundle",
    "resolution_status": "resolution_status",
    "scoring_summary": "scoring_summary",
}

SIDE_EFFECT_LEVELS = {
    "forecast_request_validation": "validation_only",
    "evidence_plan": "dry_run_generation",
    "evidence_trace": "read_only",
    "forecast_card": "read_only",
    "lifecycle_bundle": "read_only",
    "resolution_status": "status_read",
    "scoring_summary": "scoring_read",
}

USAGE_GUIDANCE = {
    "forecast_request_validation": "Use before any forecast execution, live fetch, paid action, or privacy-sensitive action.",
    "evidence_plan": "Use after an accepted request to inspect source policy, planned connectors, and approval boundaries.",
    "evidence_trace": "Use when the caller needs connector-bound source provenance without raw fixture contents.",
    "forecast_card": "Use first for compact downstream decisions that need probability, baseline, status, and warnings.",
    "lifecycle_bundle": "Use when the caller needs audit context, provenance, evidence, history, resolution, and scoring records.",
    "resolution_status": "Use when an agent needs to decide whether to wait, resolve, score, or treat a forecast as provisional.",
    "scoring_summary": "Use when an agent needs score, baseline comparison, and quality-claim boundaries before acting.",
}

HTTP_PATHS = {
    "forecast_request_validation": "/agent/forecast-request-validation",
    "evidence_plan": "/agent/evidence-plan",
    "evidence_trace": "/agent/evidence-trace",
    "forecast_card": "/agent/forecast-card",
    "lifecycle_bundle": "/agent/lifecycle-bundle",
    "resolution_status": "/agent/resolution-status",
    "scoring_summary": "/agent/scoring-summary",
}


class ProtocolMapError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def field(
    name: str,
    required: bool,
    value_type: str,
    source: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "name": name,
        "required": required,
        "type": value_type,
        "source": source,
        "notes": notes,
    }


def input_fields(operation: str) -> list[dict[str, Any]]:
    common = [
        field(
            "maxBytes",
            False,
            "integer",
            "agent-call --max-bytes",
            "Caps response size; adapters must return response_too_large when exceeded.",
        ),
        field(
            "callerIntent",
            False,
            "string",
            "agent-call --caller-intent",
            "Short safe caller intent for audit context, not hidden prompt text.",
        ),
    ]
    if operation == "forecast_request_validation":
        return [
            field(
                "request",
                True,
                "path-or-json-object",
                "agent-call --request",
                "Forecast request record to validate without execution.",
            ),
            *common,
        ]
    if operation == "evidence_plan":
        return [
            field(
                "request",
                True,
                "path-or-json-object",
                "agent-call --request",
                "Forecast request record used to build a dry-run evidence plan.",
            ),
            *common,
        ]
    return [
        field(
            "forecastId",
            True,
            "id",
            "agent-call --forecast-id",
            "Forecast record ID to bind across card, bundle, resolution, and scoring reads.",
        ),
        field(
            "questionId",
            True,
            "id",
            "agent-call --question-id",
            "Question ID used to prevent cross-question record binding drift.",
        ),
        *common,
    ]


def cli_command(operation: str) -> str:
    if operation in {"forecast_request_validation", "evidence_plan"}:
        return (
            "python3 scripts/ope.py agent-call "
            f"--operation {operation} "
            "--request spec/fixtures/requests/auto-weather-logistics-request.json"
        )
    return (
        "python3 scripts/ope.py agent-call "
        f"--operation {operation} "
        "--forecast-id forecast-602 --question-id question-601"
    )


def mcp_tool_name(operation: str) -> str:
    return f"ope_{operation}"


def queue_message_type(operation: str) -> str:
    return f"ope.{operation}.requested"


def status_mapping() -> list[dict[str, Any]]:
    return [
        {"httpStatus": 200, "envelopeExitCode": 0, "meaning": "Successful envelope."},
        {"httpStatus": 500, "envelopeExitCode": 1, "meaning": "Internal adapter failure."},
        {"httpStatus": 400, "envelopeExitCode": 2, "meaning": "Bad or invalid caller input."},
        {"httpStatus": 403, "envelopeExitCode": 3, "meaning": "Policy or approval gate blocks execution."},
        {"httpStatus": 404, "envelopeExitCode": 4, "meaning": "Missing, denied, conflicting, or mismatched record."},
        {"httpStatus": 429, "envelopeExitCode": 5, "meaning": "Local size, quota, or rate limit exceeded."},
    ]


def approval_gate(operation: str) -> str:
    if operation in {"forecast_request_validation", "forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"}:
        return "Read, validation, and status operations should remain approval-free unless caller policy marks the record sensitive."
    return "Evidence planning may return approval_required and must not perform live fetches, paid calls, or private-source access."


def credential_boundary(operation: str) -> str:
    if operation == "evidence_plan":
        return "Connector credentials stay server-side and must never appear in prompt-visible arguments or returned records."
    return "Credentials are not required for the current local operation and must not be accepted in prompt-visible arguments."


def operation_map(operation: str) -> dict[str, Any]:
    fields = input_fields(operation)
    return {
        "operation": operation,
        "inputRecordType": INPUT_RECORD_TYPES[operation],
        "sideEffectLevel": SIDE_EFFECT_LEVELS[operation],
        "requiresApproval": operation == "evidence_plan",
        "inputFields": fields,
        "outputEnvelopeSchema": ENVELOPE_SCHEMA,
        "localCli": {
            "implemented": True,
            "command": cli_command(operation),
            "exitCodeSource": "agentEnvelope.exitCode",
        },
        "mcp": {
            "implemented": True,
            "toolName": mcp_tool_name(operation),
            "argumentFields": fields,
            "returns": ENVELOPE_SCHEMA,
            "approvalGate": approval_gate(operation),
            "credentialBoundary": credential_boundary(operation),
        },
        "http": {
            "implemented": False,
            "method": "POST",
            "path": HTTP_PATHS[operation],
            "argumentFields": fields,
            "statusMapping": status_mapping(),
            "approvalGate": approval_gate(operation),
            "credentialBoundary": credential_boundary(operation),
        },
        "queue": {
            "implemented": False,
            "requestMessageType": queue_message_type(operation),
            "resultMessageType": "ope.agent_envelope.ready",
            "correlationKeys": ["operation", "requestId", "questionId", "forecastId", "agentEnvelopeId"],
            "approvalGate": approval_gate(operation),
            "credentialBoundary": credential_boundary(operation),
        },
        "usageGuidance": USAGE_GUIDANCE[operation],
        "warnings": [
            "The local MCP stdio scaffold must preserve the envelope schema, exitCode, status, warnings, and recordBinding fields.",
            "HTTP and queue mappings are not implemented runtimes.",
        ],
    }


def exit_code_mapping() -> list[dict[str, Any]]:
    return [
        {"exitCode": 0, "status": "ok", "errorCodes": [], "meaning": "Success."},
        {"exitCode": 1, "status": "error", "errorCodes": ["internal_error"], "meaning": "Internal adapter failure."},
        {
            "exitCode": 2,
            "status": "error",
            "errorCodes": ["bad_request", "validation_failed"],
            "meaning": "Bad, malformed, or contract-invalid caller input.",
        },
        {
            "exitCode": 3,
            "status": "error",
            "errorCodes": ["approval_required"],
            "meaning": "A policy or approval gate blocks the requested operation.",
        },
        {
            "exitCode": 4,
            "status": "error",
            "errorCodes": ["not_found", "access_denied", "binding_mismatch", "conflict"],
            "meaning": "The requested record is missing, denied, conflicting, or not bound to the requested IDs.",
        },
        {
            "exitCode": 5,
            "status": "error",
            "errorCodes": ["response_too_large", "rate_limited"],
            "meaning": "The adapter hit a local size, quota, or rate limit.",
        },
    ]


def transport_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "transport": "local_cli",
            "implemented": True,
            "boundary": "Implemented as python3 scripts/ope.py agent-call returning one JSON envelope to stdout.",
            "approvalGate": "The dispatcher surfaces approval_required and does not bypass request policy.",
            "credentialBoundary": "No credentials are needed or accepted in local prompt-visible arguments.",
        },
        {
            "transport": "mcp",
            "implemented": True,
            "boundary": "Implemented locally as a stdio JSON-RPC scaffold exposing one tool per agent operation.",
            "approvalGate": "The MCP scaffold exposes validation, dry-run, read, status, and scoring tools only.",
            "credentialBoundary": "MCP credentials must stay in server configuration, not tool arguments or records.",
        },
        {
            "transport": "http",
            "implemented": False,
            "boundary": "Future HTTP endpoints should keep OPE record semantics and map status from envelope exit codes.",
            "approvalGate": "Effectful, paid, live-fetch, or privacy-sensitive requests must be approval-gated.",
            "credentialBoundary": "HTTP credentials must be transport metadata, not forecast artifacts or provenance text.",
        },
        {
            "transport": "queue",
            "implemented": False,
            "boundary": "Future queues should use request messages plus an ope.agent_envelope.ready result envelope.",
            "approvalGate": "Queued jobs must persist approval state and reject stale or unapproved effectful work.",
            "credentialBoundary": "Worker credentials must be scoped server-side and excluded from queued payloads.",
        },
    ]


def decision_examples() -> list[dict[str, Any]]:
    return [
        {
            "situation": "The agent needs a compact probability before taking a reversible downstream action.",
            "preferredOperation": "forecast_card",
            "reason": "The card includes probability, baseline, status, request binding, and claim warnings.",
            "requiredSignals": ["forecastId", "questionId", "probability", "baseline", "qualityClaim.status"],
            "downstreamRule": "Act only when caller policy accepts the quality boundary and resolution status.",
        },
        {
            "situation": "The agent needs audit context or wants to explain what evidence supported the forecast.",
            "preferredOperation": "evidence_trace",
            "reason": "The trace links the evidence plan, source policy, source set, connector registry, connector results, and gathered source records.",
            "requiredSignals": ["requestId", "sourcePolicyId", "evidencePlanId", "evidenceSourceSetId", "sourceConnectorResultSetId"],
            "downstreamRule": "Use the trace for provenance inspection, not as proof that all possible internet evidence was gathered.",
        },
        {
            "situation": "The agent needs the full forecast lifecycle for audit or explanation.",
            "preferredOperation": "lifecycle_bundle",
            "reason": "The bundle contains bound lifecycle records, evidence, history, resolution, and scoring context.",
            "requiredSignals": ["requestId", "sourcePolicyId", "evidencePacket", "forecastHistory", "scoringReport"],
            "downstreamRule": "Use the bundle for audit context, not as a separate source of forecast semantics.",
        },
        {
            "situation": "The agent needs to know whether a forecast has resolved before scoring or waiting.",
            "preferredOperation": "resolution_status",
            "reason": "Resolution status is smaller than a full bundle and carries source and quality-claim status.",
            "requiredSignals": ["resolutionStatus", "resolvedAt", "resolvedOutcome", "resolutionSource"],
            "downstreamRule": "Do not score unresolved, ambiguous, annulled, or missing outcomes as normal resolved forecasts.",
        },
        {
            "situation": "The agent needs to compare the forecast to a baseline before using it in a decision.",
            "preferredOperation": "scoring_summary",
            "reason": "Scoring summary exposes scoring rule, primary score, baseline score, and quality boundary.",
            "requiredSignals": ["scoreStatus", "scoringRule", "primaryScore", "baselineScore", "qualityClaim.status"],
            "downstreamRule": "Do not generalize one fixture score into a live calibration or state-of-the-art claim.",
        },
    ]


def build_protocol_map() -> dict[str, Any]:
    protocol_map = {
        "protocolMapId": "protocolmap-001",
        "generatedAt": GENERATED_AT,
        "adapterContract": {
            "dispatcherCommand": "python3 scripts/ope.py agent-call",
            "mcpCommand": "python3 scripts/ope.py mcp-stdio",
            "mcpProtocolVersion": MCP_PROTOCOL_VERSION,
            "envelopeSchema": ENVELOPE_SCHEMA,
            "runtimeStatus": "local_mcp_stdio_scaffold",
            "localDispatcherImplemented": True,
            "protocolRuntimeImplemented": True,
            "mcpStdioScaffoldImplemented": True,
            "httpRuntimeImplemented": False,
            "queueRuntimeImplemented": False,
        },
        "operations": [operation_map(operation) for operation in OPERATIONS],
        "exitCodeMapping": exit_code_mapping(),
        "transportBoundaries": transport_boundaries(),
        "decisionExamples": decision_examples(),
        "warnings": [
            "The MCP stdio adapter is a local scaffold, not a hosted or production adapter runtime.",
            "HTTP and queue mappings are not implemented runtimes.",
            "Protocol adapters must preserve OPE record semantics and envelope exit codes.",
            "Paid, effectful, live-fetch, or privacy-sensitive forecast requests remain approval-gated.",
            "Do not place secrets in forecast artifacts, provenance metadata, tool arguments, or queued payloads.",
        ],
    }
    validate_protocol_map(protocol_map)
    return protocol_map


def validate_protocol_map(protocol_map: dict[str, Any]) -> None:
    errors = validate_record(protocol_map, SCHEMA)
    if errors:
        raise ProtocolMapError(f"agent adapter protocol map schema validation failed: {errors[0]}")


def write_protocol_map(protocol_map: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    MAP_PATH.write_text(render_json(protocol_map), encoding="utf-8")
    print("generated agent adapter protocol map")


def check_protocol_map(protocol_map: dict[str, Any]) -> None:
    expected = render_json(protocol_map)
    if not MAP_PATH.exists():
        print(f"missing agent adapter protocol map: {MAP_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_agent_adapter_protocol_map.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = MAP_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"agent adapter protocol map drift: {MAP_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_agent_adapter_protocol_map.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked agent adapter protocol map")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated protocol-map drift")
    parser.add_argument("--write", action="store_true", help="write generated protocol map")
    args = parser.parse_args()
    try:
        protocol_map = build_protocol_map()
    except ProtocolMapError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_protocol_map(protocol_map)
    elif args.check:
        check_protocol_map(protocol_map)
    else:
        sys.stdout.write(render_json(protocol_map))


if __name__ == "__main__":
    main()
