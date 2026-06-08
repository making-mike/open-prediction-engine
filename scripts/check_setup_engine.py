#!/usr/bin/env python3
"""Check setup-engine readbacks for CLI, agent-call, and local MCP routing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_setup_engine import (
        SETUP_ENGINE_VIEWS,
        build_setup_engine,
        validate_setup_engine,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("setup engine generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GOAL = "add predictions to my app"
VIEW_NAMES = {"summary", "contracts", "sources", "baseline", "host-wrapper", "claim-boundary", "examples"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def load_cli_json(*args: str) -> dict[str, object]:
    completed = run_cli(*args)
    require(completed.returncode == 0, f"CLI failed for {' '.join(args)}: {completed.stderr or completed.stdout}")
    payload = json.loads(completed.stdout)
    require(isinstance(payload, dict), "CLI payload should be a JSON object")
    return payload


def main() -> None:
    require(set(SETUP_ENGINE_VIEWS) >= VIEW_NAMES | {"full"}, "setup-engine view coverage drifted")

    record = build_setup_engine(DEFAULT_GOAL)
    validate_setup_engine(record)

    require(record["setupEngineId"] == "setupengine-001", "setup-engine id drifted")
    require(record["goal"] == DEFAULT_GOAL, "setup-engine goal drifted")
    require(record["engineSetupStatus"] == "checked_readback", "setup-engine status drifted")
    require(record["recommendedFirstCommand"] == 'python3 scripts/ope.py setup-engine --goal "add predictions to my app"', "first command drifted")
    require(record["createsForecastArtifacts"] is False, "setup-engine readback must not create forecast artifacts")
    require(record["hostedRuntimeRequired"] is False, "setup-engine readback must not require hosted runtime")

    candidate_contracts = record["candidateForecastContracts"]
    require(len(candidate_contracts) >= 3, "setup-engine should return generic candidate contracts")
    contract_statuses = {item["contractStatus"] for item in candidate_contracts}
    require({"forecastable", "needs_clarification", "blocked"} <= contract_statuses, "setup-engine should cover forecastable, clarification, and blocked candidates")
    require(candidate_contracts[0]["contractStatus"] == "forecastable", "first candidate should be forecastable")
    require(candidate_contracts[0]["baselineMethod"]["methodId"] == "historical_frequency_baseline", "baseline method drifted")

    source_roles = record["requiredSourceRoles"]
    role_names = {item["roleName"] for item in source_roles}
    require({"forecast_time_signal", "historical_outcome", "resolution_outcome"} <= role_names, "source roles should be domain-agnostic")
    for role in source_roles:
        require(role["acceptsCredentialValues"] is False, f"{role['roleName']} must reject credential values")
        require(role["acceptsRawPrivateRows"] is False, f"{role['roleName']} must reject raw private rows")

    host_wrapper = record["hostWrapper"]
    require(host_wrapper["renderBeforeForecastArtifacts"] is True, "host wrapper should render setup before forecast artifacts")
    require(host_wrapper["wrapperStatus"] == "ready_for_host_render", "host wrapper status drifted")
    require("candidateForecastContracts" in host_wrapper["renderSections"], "host wrapper should expose candidate contracts")

    boundary = record["claimBoundary"]
    for key in [
        "qualityClaimAllowed",
        "calibrationClaimAllowed",
        "hostedRuntimeProvided",
        "trainedModelProvided",
        "executesLiveFetch",
        "acceptsRawSql",
        "acceptsCredentialValues",
        "acceptsRawPrivateRows",
    ]:
        require(boundary[key] is False, f"claim boundary {key} should remain false")

    examples = record["exampleGoals"]
    require(len(examples) == 8, "setup-engine should expose the generic catalog examples")
    transit_examples = [item for item in examples if item["goalKey"] == "public_transit_disruption_risk"]
    require(transit_examples, "transit should be one catalog example, not the default")
    require("Helsinki" not in transit_examples[0]["goal"], "transit setup-engine example should not default to Helsinki")
    require(any(item["classification"] == "rejected" for item in examples), "example catalog should include a rejected case")

    interfaces = {item["interface"]: item for item in record["interfaceBindings"]}
    require(set(interfaces) == {"cli", "agent_call", "local_mcp"}, "interface binding coverage drifted")
    require(interfaces["cli"]["command"].startswith("python3 scripts/ope.py setup-engine"), "CLI binding drifted")
    require(interfaces["agent_call"]["command"] == "python3 scripts/ope.py agent-call --operation setup_engine", "agent-call binding drifted")
    require(interfaces["local_mcp"]["toolName"] == "ope_setup_engine", "MCP tool binding drifted")

    cli_payload = load_cli_json("setup-engine", "--goal", DEFAULT_GOAL)
    require(cli_payload["goal"] == DEFAULT_GOAL, "setup-engine CLI should preserve goal")
    require(cli_payload["hostWrapper"]["renderBeforeForecastArtifacts"] is True, "setup-engine CLI should expose host wrapper")

    source_view = load_cli_json("setup-engine", "--goal", DEFAULT_GOAL, "--view", "sources")
    require(source_view["view"] == "sources", "sources view should identify itself")
    require(len(source_view["requiredSourceRoles"]) >= 3, "sources view should include source roles")

    claim_view = load_cli_json("setup-engine", "--goal", DEFAULT_GOAL, "--view", "claim-boundary")
    require(claim_view["claimBoundary"]["qualityClaimAllowed"] is False, "claim-boundary view should block quality claims")

    examples_view = load_cli_json("setup-engine", "--goal", DEFAULT_GOAL, "--view", "examples")
    require(examples_view["catalogBinding"]["predictionGoalCatalogId"] == "predictiongoalcatalog-001", "examples view should bind prediction goal catalog")
    require(examples_view["summary"]["goalExampleCount"] == 8, "examples view should expose catalog summary")
    require(
        {item["goalKey"] for item in examples_view["exampleGoals"]} >= {"stockout_risk", "public_transit_disruption_risk"},
        "examples view should expose generic catalog goals",
    )

    agent_call = load_cli_json("agent-call", "--operation", "setup_engine", "--goal", DEFAULT_GOAL)
    require(agent_call["operation"] == "setup_engine", "agent-call operation drifted")
    require(agent_call["payload"]["goal"] == DEFAULT_GOAL, "agent-call setup-engine goal drifted")
    require(agent_call["payload"]["claimBoundary"]["qualityClaimAllowed"] is False, "agent-call should block quality claims")
    require(agent_call["state"]["forecastStatus"] == "not_created_by_setup_engine", "agent-call forecast status drifted")

    protocol_map = load_cli_json("agent-protocol-map")
    operation_names = {item["operation"] for item in protocol_map["operations"]}
    require("setup_engine" in operation_names, "protocol map should expose setup_engine operation")
    setup_operation = next(item for item in protocol_map["operations"] if item["operation"] == "setup_engine")
    require(setup_operation["mcp"]["toolName"] == "ope_setup_engine", "protocol map MCP tool name drifted")
    argument_names = {item["name"] for item in setup_operation["mcp"]["argumentFields"]}
    require({"goal", "view"} <= argument_names, "protocol map should expose goal and view arguments")

    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-11-25",
            "capabilities": {},
            "clientInfo": {"name": "setup-engine-check", "version": "0.1.0"},
        },
    }
    mcp_tool_call = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "ope_setup_engine", "arguments": {"goal": DEFAULT_GOAL, "view": "summary"}},
    }
    mcp_initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    mcp_completed = subprocess.run(
        [sys.executable, "scripts/ope_mcp_stdio.py"],
        cwd=ROOT,
        input=json.dumps(mcp_request) + "\n" + json.dumps(mcp_initialized) + "\n" + json.dumps(mcp_tool_call) + "\n",
        check=False,
        text=True,
        capture_output=True,
    )
    require(mcp_completed.returncode == 0, f"MCP setup-engine call failed: {mcp_completed.stderr or mcp_completed.stdout}")
    responses = [json.loads(line) for line in mcp_completed.stdout.splitlines() if line.strip()]
    result = responses[-1]["result"]
    tool_payload = json.loads(result["content"][0]["text"])
    require(tool_payload["operation"] == "setup_engine", "MCP setup-engine operation drifted")
    require(tool_payload["payload"]["goal"] == DEFAULT_GOAL, "MCP setup-engine goal drifted")
    require(tool_payload["payload"]["view"] == "summary", "MCP setup-engine view drifted")

    print("checked setup engine")


if __name__ == "__main__":
    main()
