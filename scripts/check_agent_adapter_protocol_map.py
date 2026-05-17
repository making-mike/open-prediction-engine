#!/usr/bin/env python3
"""Check agent adapter protocol-map invariants."""

from __future__ import annotations

from generate_agent_adapter_protocol_map import ENVELOPE_SCHEMA, OPERATIONS, build_protocol_map


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    protocol_map = build_protocol_map()
    require(
        protocol_map["adapterContract"]["runtimeStatus"] == "local_mcp_stdio_scaffold",
        "protocol map should advertise the local MCP stdio scaffold",
    )
    require(
        protocol_map["adapterContract"]["localDispatcherImplemented"] is True,
        "local dispatcher should be marked implemented",
    )
    require(
        protocol_map["adapterContract"]["protocolRuntimeImplemented"] is True,
        "protocol runtime flag should reflect local MCP stdio support",
    )
    require(
        protocol_map["adapterContract"]["mcpStdioScaffoldImplemented"] is True,
        "MCP stdio scaffold should be marked implemented",
    )
    require(
        protocol_map["adapterContract"]["httpRuntimeImplemented"] is False,
        "HTTP runtime should remain unimplemented",
    )
    require(
        protocol_map["adapterContract"]["queueRuntimeImplemented"] is False,
        "queue runtime should remain unimplemented",
    )

    operations = {item["operation"]: item for item in protocol_map["operations"]}
    require(set(operations) == set(OPERATIONS), "protocol map should cover every agent operation exactly once")
    for operation, item in operations.items():
        require(item["outputEnvelopeSchema"] == ENVELOPE_SCHEMA, f"{operation} should return the agent envelope schema")
        require(item["localCli"]["implemented"] is True, f"{operation} should have an implemented local CLI mapping")
        require(
            item["localCli"]["exitCodeSource"] == "agentEnvelope.exitCode",
            f"{operation} should preserve envelope exit codes",
        )
        require(item["mcp"]["implemented"] is True, f"{operation} should expose MCP stdio scaffold support")
        require(item["http"]["implemented"] is False, f"{operation} must not claim HTTP runtime support")
        require(item["queue"]["implemented"] is False, f"{operation} must not claim queue runtime support")
        require(
            item["mcp"]["toolName"] == f"ope_{operation}",
            f"{operation} should have a deterministic MCP tool name",
        )
        require(
            item["queue"]["requestMessageType"] == f"ope.{operation}.requested",
            f"{operation} should have a deterministic queue message type",
        )
        require(
            item["queue"]["resultMessageType"] == "ope.agent_envelope.ready",
            f"{operation} queue result should be an agent envelope",
        )
        for transport in ["mcp", "http", "queue"]:
            boundary = item[transport]["credentialBoundary"]
            require("secret" not in boundary.lower(), f"{operation} {transport} boundary should avoid secret material")
            require("argument" in boundary.lower() or "payload" in boundary.lower(), f"{operation} {transport} boundary should name prompt-visible boundaries")

    evidence_plan = operations["evidence_plan"]
    require(evidence_plan["requiresApproval"] is True, "evidence plan should remain approval-aware")
    require(
        evidence_plan["sideEffectLevel"] == "dry_run_generation",
        "evidence plan should be dry-run generation, not live fetching",
    )
    for operation in ["evidence_trace", "forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"]:
        require(operations[operation]["requiresApproval"] is False, f"{operation} should be read/status-only")

    exit_codes = {item["exitCode"]: item for item in protocol_map["exitCodeMapping"]}
    require(set(exit_codes) == {0, 1, 2, 3, 4, 5}, "exit code mapping should cover 0 through 5")
    require(exit_codes[0]["status"] == "ok", "exit code 0 should be ok")
    require("approval_required" in exit_codes[3]["errorCodes"], "exit code 3 should map approval_required")
    require("response_too_large" in exit_codes[5]["errorCodes"], "exit code 5 should map response_too_large")

    transports = {item["transport"]: item for item in protocol_map["transportBoundaries"]}
    require(transports["local_cli"]["implemented"] is True, "local CLI should be implemented")
    require(transports["mcp"]["implemented"] is True, "MCP stdio scaffold should be implemented")
    for transport in ["http", "queue"]:
        require(transports[transport]["implemented"] is False, f"{transport} should remain mapping-only")
        require("credential" in transports[transport]["credentialBoundary"].lower(), f"{transport} should define credentials")

    examples = {item["preferredOperation"] for item in protocol_map["decisionExamples"]}
    for operation in ["evidence_trace", "forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"]:
        require(operation in examples, f"decision examples should explain when to use {operation}")

    warnings = " ".join(protocol_map["warnings"]).lower()
    require("http and queue" in warnings and "not implemented" in warnings, "warnings should state HTTP and queue are not implemented")
    require("local scaffold" in warnings, "warnings should describe MCP as a local scaffold")
    require("approval" in warnings, "warnings should preserve approval-gate boundaries")
    require("secrets" in warnings, "warnings should prohibit secrets in protocol-visible records")

    print("checked agent adapter protocol map")


if __name__ == "__main__":
    main()
