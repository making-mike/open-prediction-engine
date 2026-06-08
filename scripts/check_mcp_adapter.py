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
    forecast_run_start_id = 27
    forecast_run_ids = {
        case.outcome_class: forecast_run_start_id + index
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
            message(
                6,
                "tools/call",
                {
                    "name": "ope_private_setup_bundle",
                    "arguments": {
                        "privateSetupRequestId": "privatesetuprequest-001",
                    },
                },
            ),
            message(
                7,
                "tools/call",
                {
                    "name": "ope_private_setup_source_builder",
                    "arguments": {
                        "privateSetupRequestId": "privatesetuprequest-001",
                        "sourceBuilderCase": "local_draft",
                    },
                },
            ),
            message(
                8,
                "tools/call",
                {
                    "name": "ope_private_setup_source_handoff",
                    "arguments": {
                        "privateSetupRequestId": "privatesetuprequest-001",
                        "sourceHandoffCase": "confirmed_builder_draft",
                    },
                },
            ),
            message(
                9,
                "tools/call",
                {
                    "name": "ope_private_setup_method_gate",
                    "arguments": {
                        "privateSetupRequestId": "privatesetuprequest-001",
                        "methodGateCase": "confirmed_builder_draft",
                    },
                },
            ),
            message(
                10,
                "tools/call",
                {
                    "name": "ope_private_setup_forecast_execution",
                    "arguments": {
                        "privateSetupRequestId": "privatesetuprequest-001",
                        "forecastExecutionCase": "confirmed_builder_draft",
                    },
                },
            ),
            message(
                11,
                "tools/call",
                {
                    "name": "ope_private_setup_adapter_runbook",
                    "arguments": {},
                },
            ),
            message(
                12,
                "tools/call",
                {
                    "name": "ope_private_setup_adapter_conformance_summary",
                    "arguments": {},
                },
            ),
            message(
                13,
                "tools/call",
                {
                    "name": "ope_private_source_adapter_guidance",
                    "arguments": {},
                },
            ),
            message(
                14,
                "tools/call",
                {
                    "name": "ope_private_source_kind_selection",
                    "arguments": {},
                },
            ),
            message(
                15,
                "tools/call",
                {
                    "name": "ope_private_source_kind_selection",
                    "arguments": {
                        "sourceKind": "private_api",
                    },
                },
            ),
            message(
                16,
                "tools/call",
                {
                    "name": "ope_resolution_jobs",
                    "arguments": {},
                },
            ),
            message(
                17,
                "tools/call",
                {
                    "name": "ope_resolution_scheduler_status",
                    "arguments": {},
                },
            ),
            message(
                18,
                "tools/call",
                {
                    "name": "ope_campaign_plan",
                    "arguments": {},
                },
            ),
            message(
                19,
                "tools/call",
                {
                    "name": "ope_campaign_status",
                    "arguments": {},
                },
            ),
            message(
                20,
                "tools/call",
                {
                    "name": "ope_campaign_health",
                    "arguments": {},
                },
            ),
            message(
                21,
                "tools/call",
                {
                    "name": "ope_campaign_append_readiness",
                    "arguments": {},
                },
            ),
            message(
                22,
                "tools/call",
                {
                    "name": "ope_campaign_calibration_status",
                    "arguments": {},
                },
            ),
            message(
                23,
                "tools/call",
                {
                    "name": "ope_agent_integration_readiness",
                    "arguments": {
                        "scenario": "helsinki_bus_disruption",
                    },
                },
            ),
            message(
                24,
                "tools/call",
                {
                    "name": "ope_agent_integration_candidates",
                    "arguments": {
                        "scenario": "helsinki_bus_disruption",
                    },
                },
            ),
            message(
                25,
                "tools/call",
                {
                    "name": "ope_agent_integration_guided_forecast",
                    "arguments": {
                        "scenario": "helsinki_bus_disruption",
                        "guidedCase": "accepted_adapter_output",
                    },
                },
            ),
            message(
                26,
                "tools/call",
                {
                    "name": "ope_setup_engine",
                    "arguments": {
                        "goal": "add predictions to my app",
                        "view": "summary",
                    },
                },
            ),
            *forecast_run_messages,
            message(
                forecast_run_start_id + len(CASES),
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

    private_setup = indexed[6]["result"]
    if private_setup.get("isError"):
        raise AssertionError("private-setup-bundle MCP tool should succeed")
    private_setup_envelope = private_setup["structuredContent"]
    assert_envelope(private_setup_envelope)
    if private_setup_envelope["operation"] != "private_setup_bundle":
        raise AssertionError("private-setup-bundle MCP tool returned the wrong operation")
    if private_setup_envelope["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-bundle MCP tool lost request binding")
    if private_setup_envelope["payload"]["executionBoundary"]["runsSuggestedCommand"] is not False:
        raise AssertionError("private-setup-bundle MCP tool must not execute suggested commands")

    source_builder = indexed[7]["result"]
    if source_builder.get("isError"):
        raise AssertionError("private-setup-source-builder MCP tool should succeed")
    source_builder_envelope = source_builder["structuredContent"]
    assert_envelope(source_builder_envelope)
    if source_builder_envelope["operation"] != "private_setup_source_builder":
        raise AssertionError("private-setup-source-builder MCP tool returned the wrong operation")
    if source_builder_envelope["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-source-builder MCP tool lost request binding")
    source_builder_payload = source_builder_envelope["payload"]
    if source_builder_payload["sourceManifestBuild"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("private-setup-source-builder MCP tool must not allow forecast execution")
    if source_builder_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-source-builder MCP tool must not create forecast artifacts")

    source_handoff = indexed[8]["result"]
    if source_handoff.get("isError"):
        raise AssertionError("private-setup-source-handoff MCP tool should succeed")
    source_handoff_envelope = source_handoff["structuredContent"]
    assert_envelope(source_handoff_envelope)
    if source_handoff_envelope["operation"] != "private_setup_source_handoff":
        raise AssertionError("private-setup-source-handoff MCP tool returned the wrong operation")
    if source_handoff_envelope["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-source-handoff MCP tool lost request binding")
    source_handoff_payload = source_handoff_envelope["payload"]
    if source_handoff_payload["sourceIntakeHandoff"]["handoffStatus"] != "ready_for_method_gating":
        raise AssertionError("private-setup-source-handoff MCP tool should expose confirmed handoff readiness")
    if source_handoff_payload["adapterGuidance"]["forecastExecutionAllowed"] is not False:
        raise AssertionError("private-setup-source-handoff MCP tool must not allow forecast execution directly")
    if source_handoff_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-source-handoff MCP tool must not create forecast artifacts")

    method_gate = indexed[9]["result"]
    if method_gate.get("isError"):
        raise AssertionError("private-setup-method-gate MCP tool should succeed")
    method_gate_envelope = method_gate["structuredContent"]
    assert_envelope(method_gate_envelope)
    if method_gate_envelope["operation"] != "private_setup_method_gate":
        raise AssertionError("private-setup-method-gate MCP tool returned the wrong operation")
    if method_gate_envelope["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-method-gate MCP tool lost request binding")
    method_gate_payload = method_gate_envelope["payload"]
    if method_gate_payload["sourceHandoffMethodGate"]["methodGateStatus"] != "method_selected":
        raise AssertionError("private-setup-method-gate MCP tool should expose selected method")
    if method_gate_payload["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not True:
        raise AssertionError("private-setup-method-gate MCP tool should recommend explicit setup forecast execution")
    if method_gate_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-method-gate MCP tool must not create forecast artifacts")

    forecast_execution = indexed[10]["result"]
    if forecast_execution.get("isError"):
        raise AssertionError("private-setup-forecast-execution MCP tool should succeed")
    forecast_execution_envelope = forecast_execution["structuredContent"]
    assert_envelope(forecast_execution_envelope)
    if forecast_execution_envelope["operation"] != "private_setup_forecast_execution":
        raise AssertionError("private-setup-forecast-execution MCP tool returned the wrong operation")
    if forecast_execution_envelope["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-forecast-execution MCP tool lost request binding")
    forecast_execution_payload = forecast_execution_envelope["payload"]
    if forecast_execution_payload["setupForecastRun"]["runStatus"] != "generated":
        raise AssertionError("private-setup-forecast-execution MCP tool should generate the confirmed run")
    if forecast_execution_payload["bindingSummary"]["forecastId"] != "forecast-1102":
        raise AssertionError("private-setup-forecast-execution MCP tool should bind forecast-1102")
    if forecast_execution_payload["forecastArtifacts"]["forecastArtifact"]["forecastId"] != "forecast-1102":
        raise AssertionError("private-setup-forecast-execution MCP tool should return forecast-1102 artifact")
    if forecast_execution_payload["executionBoundary"]["createsScoringRecords"] is not False:
        raise AssertionError("private-setup-forecast-execution MCP tool must not create scoring records")

    adapter_runbook = indexed[11]["result"]
    if adapter_runbook.get("isError"):
        raise AssertionError("private-setup-adapter-runbook MCP tool should succeed")
    adapter_runbook_envelope = adapter_runbook["structuredContent"]
    assert_envelope(adapter_runbook_envelope)
    if adapter_runbook_envelope["operation"] != "private_setup_adapter_runbook":
        raise AssertionError("private-setup-adapter-runbook MCP tool returned the wrong operation")
    adapter_runbook_payload = adapter_runbook_envelope["payload"]
    if adapter_runbook_payload["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-setup-adapter-runbook MCP tool must not execute adapter calls")
    if adapter_runbook_payload["operationSequence"][-4]["operation"] != "forecast_card":
        raise AssertionError("private-setup-adapter-runbook MCP tool should route readback to forecast_card")

    adapter_conformance_summary = indexed[12]["result"]
    if adapter_conformance_summary.get("isError"):
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool should succeed")
    adapter_conformance_summary_envelope = adapter_conformance_summary["structuredContent"]
    assert_envelope(adapter_conformance_summary_envelope)
    if adapter_conformance_summary_envelope["operation"] != "private_setup_adapter_conformance_summary":
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool returned the wrong operation")
    adapter_conformance_summary_payload = adapter_conformance_summary_envelope["payload"]
    if adapter_conformance_summary_payload["caseTotals"]["totalCases"] != 31:
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool should expose case totals")
    if adapter_conformance_summary_payload["readSurface"]["compactSummaryDoesNotEmbedEnvelopes"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool should stay compact")
    if adapter_conformance_summary_payload["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool must not execute")
    if adapter_conformance_summary_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-adapter-conformance-summary MCP tool must not create forecast artifacts")

    source_guidance = indexed[13]["result"]
    if source_guidance.get("isError"):
        raise AssertionError("private-source-adapter-guidance MCP tool should succeed")
    source_guidance_envelope = source_guidance["structuredContent"]
    assert_envelope(source_guidance_envelope)
    if source_guidance_envelope["operation"] != "private_source_adapter_guidance":
        raise AssertionError("private-source-adapter-guidance MCP tool returned the wrong operation")
    source_guidance_payload = source_guidance_envelope["payload"]
    if source_guidance_payload["bindingSummary"]["privateSourceAdapterCapabilityId"] != "privatesourceadaptercapability-001":
        raise AssertionError("private-source-adapter-guidance MCP tool should bind capabilities")
    source_summary = {item["sourceKind"]: item for item in source_guidance_payload["sourceKindSummary"]}
    if source_summary["local_file"]["allowedEntrypoint"] != "source_builder":
        raise AssertionError("private-source-adapter-guidance MCP tool should route local files to source-builder")
    if source_summary["private_database"]["allowedEntrypoint"] != "no_current_entrypoint":
        raise AssertionError("private-source-adapter-guidance MCP tool should keep private databases planned-only")
    if source_guidance_payload["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-source-adapter-guidance MCP tool must not execute adapter calls")
    if source_guidance_payload["executionBoundary"]["createsSourceManifests"] is not False:
        raise AssertionError("private-source-adapter-guidance MCP tool must not create source manifests")

    source_selection = indexed[14]["result"]
    if source_selection.get("isError"):
        raise AssertionError("private-source-kind-selection MCP tool should succeed")
    source_selection_envelope = source_selection["structuredContent"]
    assert_envelope(source_selection_envelope)
    if source_selection_envelope["operation"] != "private_source_kind_selection":
        raise AssertionError("private-source-kind-selection MCP tool returned the wrong operation")
    source_selection_payload = source_selection_envelope["payload"]
    if source_selection_payload["privateSourceKindSelectionExamplesId"] != "privatesourcekindselectionexamples-001":
        raise AssertionError("private-source-kind-selection MCP tool should return checked examples")
    source_selection_rows = {
        item["sourceKind"]: item
        for item in source_selection_payload["selectionExamples"]
    }
    if source_selection_rows["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise AssertionError("private-source-kind-selection MCP tool should route local files to source-builder")
    if source_selection_rows["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("private-source-kind-selection MCP tool should require mapping confirmation")
    if source_selection_rows["private_database"]["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("private-source-kind-selection MCP tool should keep private databases planned-only")
    if source_selection_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("private-source-kind-selection MCP tool must not run commands")
    if source_selection_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-kind-selection MCP tool must not create forecast artifacts")

    selected_source_selection = indexed[15]["result"]
    if selected_source_selection.get("isError"):
        raise AssertionError("selected private-source-kind-selection MCP tool should succeed")
    selected_source_selection_envelope = selected_source_selection["structuredContent"]
    assert_envelope(selected_source_selection_envelope)
    if selected_source_selection_envelope["operation"] != "private_source_kind_selection":
        raise AssertionError("selected private-source-kind-selection MCP tool returned the wrong operation")
    selected_source_selection_payload = selected_source_selection_envelope["payload"]
    if selected_source_selection_payload["runtimeStatus"] != "selected_example_only":
        raise AssertionError("selected private-source-kind-selection MCP tool should return a compact payload")
    if selected_source_selection_payload["requestedSourceKind"] != "private_api":
        raise AssertionError("selected private-source-kind-selection MCP tool should echo sourceKind")
    if "selectionExamples" in selected_source_selection_payload:
        raise AssertionError("selected private-source-kind-selection MCP tool should not return all examples")
    if selected_source_selection_payload["selectedExample"]["sourceKind"] != "private_api":
        raise AssertionError("selected private-source-kind-selection MCP tool should return private API")
    if selected_source_selection_payload["selectedExample"]["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("selected private-source-kind-selection MCP tool should keep private API planned-only")
    if selected_source_selection_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("selected private-source-kind-selection MCP tool must not run commands")
    if selected_source_selection_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("selected private-source-kind-selection MCP tool must not create forecast artifacts")

    resolution_jobs = indexed[16]["result"]
    if resolution_jobs.get("isError"):
        raise AssertionError("resolution-jobs MCP tool should succeed")
    resolution_jobs_envelope = resolution_jobs["structuredContent"]
    assert_envelope(resolution_jobs_envelope)
    if resolution_jobs_envelope["operation"] != "resolution_jobs":
        raise AssertionError("resolution-jobs MCP tool returned the wrong operation")
    resolution_jobs_payload = resolution_jobs_envelope["payload"]
    if resolution_jobs_payload["summary"]["pendingDueCount"] != 1:
        raise AssertionError("resolution-jobs MCP tool should expose one due job")
    if resolution_jobs_payload["executionBoundary"]["registryExecutesResolvers"] is not False:
        raise AssertionError("resolution-jobs MCP tool must not execute resolvers")

    scheduler_status = indexed[17]["result"]
    if scheduler_status.get("isError"):
        raise AssertionError("resolution-scheduler-status MCP tool should succeed")
    scheduler_status_envelope = scheduler_status["structuredContent"]
    assert_envelope(scheduler_status_envelope)
    if scheduler_status_envelope["operation"] != "resolution_scheduler_status":
        raise AssertionError("resolution-scheduler-status MCP tool returned the wrong operation")
    scheduler_status_payload = scheduler_status_envelope["payload"]
    if scheduler_status_payload["lastTick"]["tickStatus"] != "due_pending":
        raise AssertionError("resolution-scheduler-status MCP tool should expose the latest tick")
    if scheduler_status_payload["executionMode"] != "dry_run":
        raise AssertionError("resolution-scheduler-status MCP tool should expose dry-run mode")
    if scheduler_status_payload["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("resolution-scheduler-status MCP tool must not execute resolvers")

    campaign_plan = indexed[18]["result"]
    if campaign_plan.get("isError"):
        raise AssertionError("campaign-plan MCP tool should succeed")
    campaign_plan_envelope = campaign_plan["structuredContent"]
    assert_envelope(campaign_plan_envelope)
    if campaign_plan_envelope["operation"] != "campaign_plan":
        raise AssertionError("campaign-plan MCP tool returned the wrong operation")
    if campaign_plan_envelope["payload"]["predictionCampaignManifestId"] != "predictioncampaignmanifest-001":
        raise AssertionError("campaign-plan MCP tool should return the campaign manifest")
    if campaign_plan_envelope["payload"]["localStatePolicy"]["normalChecksWriteLiveState"] is not False:
        raise AssertionError("campaign-plan MCP tool must keep normal checks non-mutating")

    campaign_status = indexed[19]["result"]
    if campaign_status.get("isError"):
        raise AssertionError("campaign-status MCP tool should succeed")
    campaign_status_envelope = campaign_status["structuredContent"]
    assert_envelope(campaign_status_envelope)
    if campaign_status_envelope["operation"] != "campaign_status":
        raise AssertionError("campaign-status MCP tool returned the wrong operation")
    if campaign_status_envelope["payload"]["campaignSnapshot"]["nextForecastId"] != "forecast-1301":
        raise AssertionError("campaign-status MCP tool should expose forecast-1301")
    if campaign_status_envelope["payload"]["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("campaign-status MCP tool must keep quality claims blocked")

    campaign_health = indexed[20]["result"]
    if campaign_health.get("isError"):
        raise AssertionError("campaign-health MCP tool should succeed")
    campaign_health_envelope = campaign_health["structuredContent"]
    assert_envelope(campaign_health_envelope)
    if campaign_health_envelope["operation"] != "campaign_health":
        raise AssertionError("campaign-health MCP tool returned the wrong operation")
    if campaign_health_envelope["payload"]["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("campaign-health MCP tool must not execute resolvers")

    campaign_append = indexed[21]["result"]
    if campaign_append.get("isError"):
        raise AssertionError("campaign-append-readiness MCP tool should succeed")
    campaign_append_envelope = campaign_append["structuredContent"]
    assert_envelope(campaign_append_envelope)
    if campaign_append_envelope["operation"] != "campaign_append_readiness":
        raise AssertionError("campaign-append-readiness MCP tool returned the wrong operation")
    if campaign_append_envelope["payload"]["appendCandidate"]["comparableAppendReady"] is not False:
        raise AssertionError("campaign-append-readiness MCP tool should keep comparable append blocked")
    if campaign_append_envelope["payload"]["executionBoundary"]["appendsCorpusEvidence"] is not False:
        raise AssertionError("campaign-append-readiness MCP tool must not append corpus evidence")

    campaign_calibration = indexed[22]["result"]
    if campaign_calibration.get("isError"):
        raise AssertionError("campaign-calibration-status MCP tool should succeed")
    campaign_calibration_envelope = campaign_calibration["structuredContent"]
    assert_envelope(campaign_calibration_envelope)
    if campaign_calibration_envelope["operation"] != "campaign_calibration_status":
        raise AssertionError("campaign-calibration-status MCP tool returned the wrong operation")
    if campaign_calibration_envelope["payload"]["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("campaign-calibration-status MCP tool should expose below-threshold status")
    if campaign_calibration_envelope["payload"]["executionBoundary"]["updatesForecastProbabilities"] is not False:
        raise AssertionError("campaign-calibration-status MCP tool must not update probabilities")

    integration_readiness = indexed[23]["result"]
    if integration_readiness.get("isError"):
        raise AssertionError("agent-integration-readiness MCP tool should succeed")
    readiness_envelope = integration_readiness["structuredContent"]
    assert_envelope(readiness_envelope)
    if readiness_envelope["operation"] != "agent_integration_readiness":
        raise AssertionError("agent-integration-readiness MCP tool returned the wrong operation")
    readiness_payload = readiness_envelope["payload"]
    if readiness_payload["summary"]["firstForecastFastTargetMet"] is not True:
        raise AssertionError("agent-integration-readiness MCP tool should report the fast first forecast gate")
    readiness_roles = {
        item["roleKey"]: item
        for item in readiness_payload["starterPack"]["sourceRoles"]
    }
    if set(readiness_roles) != {"weather_forecast", "historical_delay_baseline", "transit_delay_outcome"}:
        raise AssertionError("agent-integration-readiness MCP tool should expose required source roles")
    if readiness_roles["transit_delay_outcome"]["forecastTimeAllowed"] is not False:
        raise AssertionError("agent-integration-readiness MCP tool should keep HSL outcome resolution-only")

    integration_candidates = indexed[24]["result"]
    if integration_candidates.get("isError"):
        raise AssertionError("agent-integration-candidates MCP tool should succeed")
    candidates_envelope = integration_candidates["structuredContent"]
    assert_envelope(candidates_envelope)
    if candidates_envelope["operation"] != "agent_integration_candidates":
        raise AssertionError("agent-integration-candidates MCP tool returned the wrong operation")
    candidate_rows = {
        item["caseKey"]: item
        for item in candidates_envelope["payload"]["candidateQuestions"]
    }
    if candidate_rows["helsinki_surface_transit_peak_delay"]["status"] != "forecastable":
        raise AssertionError("agent-integration-candidates MCP tool should expose the forecastable Helsinki candidate")
    if candidate_rows["vague_next_week_transit"]["status"] != "needs_clarification":
        raise AssertionError("agent-integration-candidates MCP tool should classify vague next-week transit as needs_clarification")
    if "raw_credential_value" not in candidate_rows["raw_credential_value"]["reasonCodes"]:
        raise AssertionError("agent-integration-candidates MCP tool should expose raw credential blocker code")

    integration_guided = indexed[25]["result"]
    if integration_guided.get("isError"):
        raise AssertionError("agent-integration-guided-forecast MCP tool should succeed")
    guided_envelope = integration_guided["structuredContent"]
    assert_envelope(guided_envelope)
    if guided_envelope["operation"] != "agent_integration_guided_forecast":
        raise AssertionError("agent-integration-guided-forecast MCP tool returned the wrong operation")
    guided_payload = guided_envelope["payload"]
    if guided_payload["guidedStatus"] != "forecast_card_ready":
        raise AssertionError("agent-integration-guided-forecast MCP tool should reach a forecast card")
    if guided_payload["toolCallCount"] > 3:
        raise AssertionError("agent-integration-guided-forecast MCP tool should meet the three-call target")
    if guided_payload["forecastId"] != "forecast-1102" or guided_payload["questionId"] != "question-1102":
        raise AssertionError("agent-integration-guided-forecast MCP tool should bind forecast-1102/question-1102")
    if guided_payload["createsForecastArtifacts"] is not False:
        raise AssertionError("agent-integration-guided-forecast MCP tool should stay readback-only")

    setup_engine = indexed[26]["result"]
    if setup_engine.get("isError"):
        raise AssertionError("setup-engine MCP tool should succeed")
    setup_engine_envelope = setup_engine["structuredContent"]
    assert_envelope(setup_engine_envelope)
    if setup_engine_envelope["operation"] != "setup_engine":
        raise AssertionError("setup-engine MCP tool returned the wrong operation")
    setup_engine_payload = setup_engine_envelope["payload"]
    if setup_engine_payload["view"] != "summary":
        raise AssertionError("setup-engine MCP tool should return the requested summary view")
    if setup_engine_payload["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("setup-engine MCP tool should render setup before forecast artifacts")
    if setup_engine_payload["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("setup-engine MCP tool should keep quality claims blocked")

    for case in CASES:
        result = indexed[forecast_run_ids[case.outcome_class]]["result"]
        assert_forecast_run_result(
            result,
            expected_outcomes[case.outcome_class],
            outcome_class=case.outcome_class,
        )

    unknown = indexed[forecast_run_start_id + len(CASES)]
    if unknown["error"]["code"] != -32602:
        raise AssertionError("unknown MCP tools should return a protocol invalid-params error")

    print("checked local MCP stdio adapter")


if __name__ == "__main__":
    main()
