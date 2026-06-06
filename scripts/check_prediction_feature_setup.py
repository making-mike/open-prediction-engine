#!/usr/bin/env python3
"""Check prediction-feature setup contract readbacks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_prediction_feature_setup import build_prediction_feature_setup, validate_prediction_feature_setup
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("prediction feature setup generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_prediction_feature_setup()
    validate_prediction_feature_setup(record)

    require(record["predictionFeatureSetupId"] == "predictionfeaturesetup-001", "setup id drifted")
    require(record["setupStatus"] == "checked_compact_contract", "setup status drifted")
    require(record["createsNewForecastPath"] is False, "setup contract must not create a new forecast path")
    require(record["hostedRuntimeRequired"] is False, "setup contract must not require hosted runtime")

    request = record["requestContract"]
    required = {item["fieldName"]: item for item in request["requiredFields"]}
    for field in ["hostFeatureIntent", "decisionToSupport", "approvedSourceRefs", "resolutionHints", "responseSizeBudgetBytes"]:
        require(field in required, f"request contract missing {field}")
    require(request["acceptsCredentialValues"] is False, "request must reject credential values")
    require(request["acceptsRawPrivateRows"] is False, "request must reject raw private rows")
    require(request["acceptsRawSql"] is False, "request must reject raw SQL")

    responses = {item["caseKey"]: item for item in record["responseExamples"]}
    require(set(responses) == {"accepted", "needs_clarification", "blocked", "rejected", "response_too_large"}, "response case coverage drifted")
    accepted = responses["accepted"]
    require(accepted["decision"] == "forecast_card_ready", "accepted decision drifted")
    require(accepted["forecastId"] == "forecast-1102", "accepted forecast binding drifted")
    require(accepted["questionId"] == "question-1102", "accepted question binding drifted")
    require("forecast-card" in accepted["forecastCardCommand"], "accepted response should expose forecast-card command")
    require(accepted["createsForecastArtifacts"] is False, "accepted response must not create artifacts in this readback")
    require(accepted["qualityClaimAllowed"] is False, "accepted response must block quality claims")
    require(responses["needs_clarification"]["decision"] == "needs_clarification", "clarification decision drifted")
    require(responses["blocked"]["decision"] == "blocked", "blocked decision drifted")
    require(responses["rejected"]["decision"] == "rejected", "rejected decision drifted")
    require(responses["response_too_large"]["decision"] == "response_too_large", "too-large decision drifted")
    for response in responses.values():
        require(response["storesCredentialValues"] is False, f"{response['caseKey']} must not store credential values")
        require(response["storesRawPrivateRows"] is False, f"{response['caseKey']} must not store raw private rows")
        require(response["executesPrivateSources"] is False, f"{response['caseKey']} must not execute private sources")

    interfaces = {item["interface"]: item for item in record["interfaceBindings"]}
    require(set(interfaces) == {"cli", "agent_call", "local_mcp_guidance"}, "interface binding coverage drifted")
    require(interfaces["cli"]["command"] == "python3 scripts/ope.py prediction-feature-setup", "CLI command drifted")
    require(
        interfaces["agent_call"]["command"] == "python3 scripts/ope.py agent-call --operation prediction_feature_setup",
        "agent-call command drifted",
    )
    require(interfaces["local_mcp_guidance"]["implementedStatus"] == "guidance_only", "MCP guidance status drifted")

    boundary = record["executionBoundary"]
    for key in [
        "createsForecastArtifacts",
        "fetchesLiveData",
        "storesCredentialValues",
        "storesRawPrivateRows",
        "acceptsRawSql",
        "opensNetworkListener",
        "hostedRuntime",
        "qualityClaimAllowed",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should remain false")

    summary = record["summary"]
    require(summary["responseExampleCount"] == 5, "response example count drifted")
    require(summary["interfaceBindingCount"] == 3, "interface binding count drifted")
    require(summary["acceptedForecastId"] == "forecast-1102", "summary forecast binding drifted")

    cli = subprocess.run(
        [sys.executable, "scripts/ope.py", "prediction-feature-setup", "--view", "response", "--case", "accepted"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(cli.returncode == 0, f"prediction-feature-setup CLI failed: {cli.stderr or cli.stdout}")
    cli_payload = json.loads(cli.stdout)
    require(cli_payload["decision"] == "forecast_card_ready", "CLI response decision drifted")
    require(cli_payload["forecastId"] == "forecast-1102", "CLI response forecast binding drifted")

    agent_call = subprocess.run(
        [sys.executable, "scripts/ope.py", "agent-call", "--operation", "prediction_feature_setup"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(agent_call.returncode == 0, f"prediction feature setup agent-call failed: {agent_call.stderr or agent_call.stdout}")
    envelope = json.loads(agent_call.stdout)
    require(envelope["operation"] == "prediction_feature_setup", "agent-call operation drifted")
    require(envelope["payload"]["forecastId"] == "forecast-1102", "agent-call forecast binding drifted")
    require(envelope["recordBinding"]["forecastId"] == "forecast-1102", "agent-call record binding drifted")

    print("checked prediction feature setup")


if __name__ == "__main__":
    main()
