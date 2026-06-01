#!/usr/bin/env python3
"""Generate or check the agent-facing forecast-run runbook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_agent_adapter_protocol_map import build_protocol_map
from generate_forecast_run_intake_matrix import build_matrix
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "forecast-run"
RUNBOOK_PATH = GENERATED / "weather-logistics-agent-forecast-runbook.generated.json"
SCHEMA = SPEC / "agent-forecast-runbook.schema.json"
GENERATED_AT = "2026-06-06T13:30:00Z"


NEXT_ACTION_BY_OUTCOME = {
    "accepted": "read_forecast_card",
    "rejected": "revise_request",
    "blocked": "request_approval",
    "canceled": "stop_terminal",
    "unsupported_fixture_path": "use_supported_fixture_or_wait",
    "response_too_large": "increase_max_bytes_or_read_smaller_output",
}


class ForecastRunbookError(Exception):
    pass


def operation_map(protocol_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["operation"]: item for item in protocol_map["operations"]}


def workflow_steps(operations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "stepId": "runbookstep-001",
            "order": 1,
            "name": "validate_request",
            "purpose": "Validate the request before any forecast run or evidence work.",
            "cliCommand": operations["forecast_request_validation"]["localCli"]["command"],
            "mcpTool": operations["forecast_request_validation"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "validation_only",
            "nextActionLabel": "inspect_decision",
            "stopCondition": "Stop or revise if the request is rejected, blocked, or canceled.",
        },
        {
            "stepId": "runbookstep-002",
            "order": 2,
            "name": "run_forecast",
            "purpose": "Run the local fixture-safe forecast orchestration for the accepted auto-evidence request.",
            "cliCommand": "python3 scripts/ope.py forecast-run",
            "mcpTool": "ope_forecast_run",
            "expectedSchema": "spec/forecast-run-summary.schema.json",
            "sideEffectLevel": "fixture_dry_run",
            "nextActionLabel": "read_forecast_card",
            "stopCondition": "Branch on runStatus and error.code before reading downstream outputs.",
        },
        {
            "stepId": "runbookstep-003",
            "order": 3,
            "name": "inspect_intake_outcome",
            "purpose": "Map the forecast-run outcome to an explicit safe next action.",
            "cliCommand": "python3 scripts/ope.py forecast-run-matrix",
            "mcpTool": None,
            "expectedSchema": "spec/forecast-run-intake-matrix.schema.json",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "inspect_decision",
            "stopCondition": "Do not read forecast outputs for non-completed outcomes.",
        },
        {
            "stepId": "runbookstep-004",
            "order": 4,
            "name": "read_forecast_card",
            "purpose": "Read compact probability, baseline, status, and quality-claim warnings.",
            "cliCommand": operations["forecast_card"]["localCli"]["command"],
            "mcpTool": operations["forecast_card"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "read_evidence_trace",
            "stopCondition": "Stop if forecastId or questionId no longer matches the forecast-run summary.",
        },
        {
            "stepId": "runbookstep-005",
            "order": 5,
            "name": "read_evidence_trace",
            "purpose": "Read connector-bound source provenance without raw fixture contents.",
            "cliCommand": operations["evidence_trace"]["localCli"]["command"],
            "mcpTool": operations["evidence_trace"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "read_lifecycle_bundle",
            "stopCondition": "Do not treat connector trace coverage as all internet evidence.",
        },
        {
            "stepId": "runbookstep-006",
            "order": 6,
            "name": "read_lifecycle_bundle",
            "purpose": "Read audit context, evidence, provenance, resolution, and scoring bindings.",
            "cliCommand": operations["lifecycle_bundle"]["localCli"]["command"],
            "mcpTool": operations["lifecycle_bundle"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "check_resolution_status",
            "stopCondition": "Use the bundle for audit context, not as a new source of forecast semantics.",
        },
        {
            "stepId": "runbookstep-007",
            "order": 7,
            "name": "check_resolution_status",
            "purpose": "Confirm whether the forecast is resolved, provisional, ambiguous, or unscorable.",
            "cliCommand": operations["resolution_status"]["localCli"]["command"],
            "mcpTool": operations["resolution_status"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "status_read",
            "nextActionLabel": "read_scoring_summary",
            "stopCondition": "Do not treat unresolved or unscorable outcomes as normal scored forecasts.",
        },
        {
            "stepId": "runbookstep-008",
            "order": 8,
            "name": "read_scoring_summary",
            "purpose": "Inspect score, baseline comparison, and quality-claim boundary before acting.",
            "cliCommand": operations["scoring_summary"]["localCli"]["command"],
            "mcpTool": operations["scoring_summary"]["mcp"]["toolName"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "sideEffectLevel": "scoring_read",
            "nextActionLabel": "read_scoring_summary",
            "stopCondition": "Do not generalize one fixture score into a live calibration claim.",
        },
    ]


def outcome_playbooks(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    playbooks = []
    for outcome in matrix["outcomes"]:
        outcome_class = outcome["outcomeClass"]
        playbooks.append(
            {
                "outcomeClass": outcome_class,
                "runStatus": outcome["runStatus"],
                "decisionStatus": outcome["decisionStatus"],
                "retryPolicy": outcome["retryPolicy"],
                "nextActionLabel": NEXT_ACTION_BY_OUTCOME[outcome_class],
                "summaryPath": outcome["summaryPath"],
                "mcpTool": outcome["mcpExpectation"]["toolName"],
                "mcpIsError": outcome["mcpExpectation"]["isError"],
                "generatesForecastOutputs": outcome["generatesForecastOutputs"],
                "mustNotBindForecastOutputs": not outcome["generatesForecastOutputs"],
                "agentInstruction": outcome["agentNextAction"],
            }
        )
    return playbooks


def read_surface_choices(operations: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    choices = {
        "forecast_card": (
            "Use first for compact action context after a completed forecast run.",
            "Do not treat provisional quality claims as calibrated live performance.",
        ),
        "evidence_trace": (
            "Use when the caller needs connector-bound source provenance without raw fixture contents.",
            "Do not treat connector trace coverage as all internet evidence.",
        ),
        "lifecycle_bundle": (
            "Use when the caller needs evidence, provenance, history, resolution, and scoring context.",
            "Use for audit or explanation, not as a separate forecast source.",
        ),
        "resolution_status": (
            "Use before deciding whether to wait, resolve, score, or report an outcome.",
            "Exclude ambiguous, annulled, or unresolved outcomes from normal scoring claims.",
        ),
        "scoring_summary": (
            "Use before making baseline-comparison or quality-sensitive downstream decisions.",
            "Report scores with domain, horizon, sample-size, and fixture-mode boundaries.",
        ),
    }
    return [
        {
            "operation": operation,
            "whenToUse": choices[operation][0],
            "cliCommand": operations[operation]["localCli"]["command"],
            "mcpTool": operations[operation]["mcp"]["toolName"],
            "requires": ["forecastId", "questionId"],
            "expectedSchema": "spec/agent-envelope.schema.json",
            "agentRule": choices[operation][1],
        }
        for operation in ["forecast_card", "evidence_trace", "lifecycle_bundle", "resolution_status", "scoring_summary"]
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "runbookguard-001",
            "name": "request_result_binding",
            "rule": "Carry requestId, forecastId, and questionId from the forecast-run summary into every read.",
            "checkedBy": ["scripts/check_agent_forecast_run.py", "scripts/check_agent_forecast_runbook.py"],
        },
        {
            "guardId": "runbookguard-002",
            "name": "non_completed_no_outputs",
            "rule": "Rejected, blocked, canceled, unsupported, and oversized outcomes must not bind forecast outputs.",
            "checkedBy": ["scripts/check_forecast_run_intake_matrix.py", "scripts/check_agent_forecast_runbook.py"],
        },
        {
            "guardId": "runbookguard-003",
            "name": "approval_gate",
            "rule": "Approval-required requests must ask for approval before retry and must not bypass request policy.",
            "checkedBy": ["scripts/check_forecast_requests.py", "scripts/check_mcp_adapter.py"],
        },
        {
            "guardId": "runbookguard-004",
            "name": "local_fixture_boundary",
            "rule": "Treat forecast-run as local fixture-safe orchestration, not hosted execution or live internet search.",
            "checkedBy": ["scripts/check_agent_forecast_run.py", "scripts/generate_release_manifest.py"],
        },
        {
            "guardId": "runbookguard-005",
            "name": "credential_boundary",
            "rule": "Never pass secrets, tokens, private data, or credentials in prompt-visible tool arguments.",
            "checkedBy": ["scripts/check_mcp_adapter.py", "scripts/check_hardening.py"],
        },
        {
            "guardId": "runbookguard-006",
            "name": "quality_claim_boundary",
            "rule": "Report forecast quality with sample-size and fixture-mode warnings until enough outcomes resolve.",
            "checkedBy": ["scripts/check_agent_forecast_run.py", "scripts/check_auto_evidence_resolution.py"],
        },
    ]


def example_sequence(accepted_summary: dict[str, Any]) -> dict[str, Any]:
    forecast_id = accepted_summary["recordBinding"]["forecastId"]
    question_id = accepted_summary["recordBinding"]["questionId"]
    return {
        "requestFixture": "spec/fixtures/requests/auto-weather-logistics-request.json",
        "forecastId": forecast_id,
        "questionId": question_id,
        "commands": [
            {
                "order": 1,
                "command": "python3 scripts/ope.py forecast-run",
                "expectedSignal": f"runStatus completed with forecastId {forecast_id}",
            },
            {
                "order": 2,
                "command": (
                    "python3 scripts/ope.py read --record-type forecast-card "
                    f"--id {forecast_id} --question-id {question_id}"
                ),
                "expectedSignal": "compact forecast card with provisional quality claim",
            },
            {
                "order": 3,
                "command": (
                    "python3 scripts/ope.py read --record-type evidence-trace "
                    f"--id {forecast_id} --question-id {question_id}"
                ),
                "expectedSignal": "connector-bound evidence trace with source set and result bindings",
            },
            {
                "order": 4,
                "command": (
                    "python3 scripts/ope.py read --record-type forecast-bundle "
                    f"--id {forecast_id} --question-id {question_id}"
                ),
                "expectedSignal": "bound lifecycle bundle with evidence and scoring context",
            },
            {
                "order": 5,
                "command": (
                    "python3 scripts/ope.py agent-call --operation resolution_status "
                    f"--forecast-id {forecast_id} --question-id {question_id}"
                ),
                "expectedSignal": "resolution status envelope bound to the same forecast and question",
            },
            {
                "order": 6,
                "command": (
                    "python3 scripts/ope.py agent-call --operation scoring_summary "
                    f"--forecast-id {forecast_id} --question-id {question_id}"
                ),
                "expectedSignal": "scoring summary envelope with baseline comparison boundary",
            },
        ],
        "mcpTools": [
            "ope_forecast_run",
            "ope_forecast_card",
            "ope_evidence_trace",
            "ope_lifecycle_bundle",
            "ope_resolution_status",
            "ope_scoring_summary",
        ],
    }


def build_runbook() -> dict[str, Any]:
    matrix, summaries = build_matrix()
    protocol_map = build_protocol_map()
    operations = operation_map(protocol_map)
    runbook = {
        "agentForecastRunbookId": "forecastrunbook-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "runtimeStatus": "local_fixture_safe",
        "entrypoints": {
            "cliCommand": "python3 scripts/ope.py forecast-run",
            "mcpTool": "ope_forecast_run",
            "summarySchema": "spec/forecast-run-summary.schema.json",
            "intakeMatrixSchema": "spec/forecast-run-intake-matrix.schema.json",
            "runbookSchema": "spec/agent-forecast-runbook.schema.json",
        },
        "workflow": workflow_steps(operations),
        "outcomePlaybooks": outcome_playbooks(matrix),
        "readSurfaceChoices": read_surface_choices(operations),
        "guards": guards(),
        "exampleSequence": example_sequence(summaries["accepted"]),
        "warnings": [
            "Runbook describes local CLI and MCP stdio behavior only.",
            "The default forecast-run path is fixture-safe and does not fetch live internet sources.",
            "Non-completed outcomes must not be treated as generated forecasts.",
            "Quality claims remain provisional until enough comparable outcomes resolve.",
        ],
    }
    validate_runbook(runbook, matrix, protocol_map, summaries["accepted"])
    return runbook


def validate_runbook(
    runbook: dict[str, Any],
    matrix: dict[str, Any],
    protocol_map: dict[str, Any],
    accepted_summary: dict[str, Any],
) -> None:
    errors = validate_record(runbook, SCHEMA)
    if errors:
        raise ForecastRunbookError(f"agent forecast runbook schema validation failed: {errors[0]}")

    outcomes = {item["outcomeClass"]: item for item in matrix["outcomes"]}
    playbooks = {item["outcomeClass"]: item for item in runbook["outcomePlaybooks"]}
    if set(playbooks) != set(outcomes):
        raise ForecastRunbookError("runbook should cover the same outcome classes as the intake matrix")
    for outcome_class, outcome in outcomes.items():
        playbook = playbooks[outcome_class]
        if playbook["runStatus"] != outcome["runStatus"]:
            raise ForecastRunbookError("runbook/matrix runStatus drift")
        if playbook["decisionStatus"] != outcome["decisionStatus"]:
            raise ForecastRunbookError("runbook/matrix decisionStatus drift")
        if playbook["retryPolicy"] != outcome["retryPolicy"]:
            raise ForecastRunbookError("runbook/matrix retryPolicy drift")
        if playbook["nextActionLabel"] != NEXT_ACTION_BY_OUTCOME[outcome_class]:
            raise ForecastRunbookError("runbook next-action label drift")
        if playbook["mcpIsError"] != outcome["mcpExpectation"]["isError"]:
            raise ForecastRunbookError("runbook/MCP expectation drift")
        if playbook["generatesForecastOutputs"] != outcome["generatesForecastOutputs"]:
            raise ForecastRunbookError("runbook output-generation drift")
        if outcome_class == "accepted" and playbook["mustNotBindForecastOutputs"]:
            raise ForecastRunbookError("accepted outcome should allow generated forecast bindings")
        if outcome_class != "accepted" and not playbook["mustNotBindForecastOutputs"]:
            raise ForecastRunbookError("non-completed outcomes must forbid forecast bindings")

    expected_tools = {"ope_forecast_run"}
    expected_tools.update(item["mcp"]["toolName"] for item in protocol_map["operations"])
    workflow_tools = {item["mcpTool"] for item in runbook["workflow"] if item["mcpTool"] is not None}
    if not workflow_tools.issubset(expected_tools):
        raise ForecastRunbookError("runbook references an unknown MCP tool")
    sequence_tools = set(runbook["exampleSequence"]["mcpTools"])
    if not sequence_tools.issubset(expected_tools):
        raise ForecastRunbookError("runbook sequence references an unknown MCP tool")

    if runbook["exampleSequence"]["forecastId"] != accepted_summary["recordBinding"]["forecastId"]:
        raise ForecastRunbookError("runbook example forecastId drift")
    if runbook["exampleSequence"]["questionId"] != accepted_summary["recordBinding"]["questionId"]:
        raise ForecastRunbookError("runbook example questionId drift")


def write_runbook(runbook: dict[str, Any]) -> None:
    write_generated(RUNBOOK_PATH, runbook, label="agent forecast runbook", regen="python3 scripts/generate_agent_forecast_runbook.py --write")


def check_runbook(runbook: dict[str, Any]) -> None:
    check_generated(RUNBOOK_PATH, runbook, label="agent forecast runbook", regen="python3 scripts/generate_agent_forecast_runbook.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated runbook drift")
    parser.add_argument("--write", action="store_true", help="write generated runbook")
    args = parser.parse_args()
    try:
        runbook = build_runbook()
    except ForecastRunbookError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_runbook(runbook)
    elif args.check:
        check_runbook(runbook)
    else:
        sys.stdout.write(render_json(runbook))


if __name__ == "__main__":
    main()
