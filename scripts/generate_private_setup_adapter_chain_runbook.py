#!/usr/bin/env python3
"""Generate or check the private setup adapter-chain runbook."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_agent_adapter_fixtures import (
    forecast_execution_result_payload,
    method_gate_result_payload,
    source_builder_result_payload,
    source_handoff_result_payload,
)
from generate_agent_adapter_protocol_map import build_protocol_map
from generate_private_setup_agent_bundles import bundle_by_request_id
from ope_schema import SPEC, validate_record
from read_ope_record import read_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-adapter-chain"
RUNBOOK_PATH = GENERATED / "ope-private-setup-adapter-chain-runbook.generated.json"
SCHEMA = SPEC / "private-setup-adapter-chain-runbook.schema.json"
GENERATED_AT = "2026-06-07T11:10:00Z"
PRIVATE_SETUP_REQUEST_ID = "privatesetuprequest-001"
FORECAST_ID = "forecast-1102"
QUESTION_ID = "question-1102"


class PrivateSetupAdapterChainRunbookError(Exception):
    pass


def operation_map() -> dict[str, dict[str, Any]]:
    return {item["operation"]: item for item in build_protocol_map()["operations"]}


def input_field(name: str, value: str, source: str) -> dict[str, str]:
    return {
        "name": name,
        "value": value,
        "source": source,
    }


def agent_call_command(operation: str, *args: str) -> str:
    parts = ["python3", "scripts/ope.py", "agent-call", "--operation", operation, *args]
    return " ".join(parts)


def mcp_tool(operations: dict[str, dict[str, Any]], operation: str) -> str:
    return operations[operation]["mcp"]["toolName"]


def side_effect(operations: dict[str, dict[str, Any]], operation: str) -> str:
    return operations[operation]["sideEffectLevel"]


def step(
    *,
    sequence: int,
    phase: str,
    operation: str,
    cli_command: str,
    required_inputs: list[dict[str, str]],
    expected_field: str,
    expected_value: str,
    allowed_next: list[str],
    next_action: str,
    stop_condition: str,
    creates_forecast_artifacts: bool,
    operations: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "runbookStepId": f"adapterchainstep-{sequence:03d}",
        "order": sequence,
        "phase": phase,
        "operation": operation,
        "cliCommand": cli_command,
        "mcpTool": mcp_tool(operations, operation),
        "requiredInputs": required_inputs,
        "expectedEnvelopeStatus": "ok",
        "expectedPayloadStatusField": expected_field,
        "expectedPayloadStatusValue": expected_value,
        "allowedNextOperations": allowed_next,
        "nextAction": next_action,
        "stopCondition": stop_condition,
        "createsForecastArtifacts": creates_forecast_artifacts,
        "createsScoringRecords": False,
        "sideEffectLevel": side_effect(operations, operation),
    }


def operation_sequence(
    operations: dict[str, dict[str, Any]],
    bundle: dict[str, Any],
) -> list[dict[str, Any]]:
    builder = source_builder_result_payload(source_builder_case="local_draft")
    handoff = source_handoff_result_payload(source_handoff_case="confirmed_builder_draft")
    method_gate = method_gate_result_payload(method_gate_case="confirmed_builder_draft")
    execution = forecast_execution_result_payload(forecast_execution_case="confirmed_builder_draft")
    card = read_record("forecast-card", FORECAST_ID, QUESTION_ID)["record"]
    bundle_record = read_record("forecast-bundle", FORECAST_ID, QUESTION_ID)["record"]
    resolution = bundle_record["records"]["resolutionRecord"]
    scoring = bundle_record["records"]["scoringReport"]

    return [
        step(
            sequence=1,
            phase="setup_guidance",
            operation="private_setup_bundle",
            cli_command=agent_call_command(
                "private_setup_bundle",
                "--private-setup-request-id",
                PRIVATE_SETUP_REQUEST_ID,
            ),
            required_inputs=[
                input_field("privateSetupRequestId", PRIVATE_SETUP_REQUEST_ID, "caller setup request"),
            ],
            expected_field="payload.actionSummary.actionStatus",
            expected_value=bundle["actionSummary"]["actionStatus"],
            allowed_next=["private_setup_source_builder"],
            next_action="run_source_builder",
            stop_condition="Stop if the bundle does not route local files to source-builder guidance.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=2,
            phase="source_builder",
            operation="private_setup_source_builder",
            cli_command=agent_call_command(
                "private_setup_source_builder",
                "--private-setup-request-id",
                PRIVATE_SETUP_REQUEST_ID,
                "--source-builder-case",
                "local_draft",
            ),
            required_inputs=[
                input_field("privateSetupRequestId", PRIVATE_SETUP_REQUEST_ID, "private setup bundle"),
                input_field("sourceBuilderCase", "local_draft", "checked local fixture case"),
            ],
            expected_field="payload.sourceManifestBuild.buildStatus",
            expected_value=builder["sourceManifestBuild"]["buildStatus"],
            allowed_next=["private_setup_source_handoff"],
            next_action="run_source_handoff",
            stop_condition="Stop until caller-reviewed mappings are ready for source-handoff guidance.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=3,
            phase="source_handoff",
            operation="private_setup_source_handoff",
            cli_command=agent_call_command(
                "private_setup_source_handoff",
                "--private-setup-request-id",
                PRIVATE_SETUP_REQUEST_ID,
                "--source-handoff-case",
                "confirmed_builder_draft",
            ),
            required_inputs=[
                input_field("privateSetupRequestId", PRIVATE_SETUP_REQUEST_ID, "private setup bundle"),
                input_field("sourceHandoffCase", "confirmed_builder_draft", "caller-confirmed source-builder draft"),
            ],
            expected_field="payload.sourceIntakeHandoff.handoffStatus",
            expected_value=handoff["sourceIntakeHandoff"]["handoffStatus"],
            allowed_next=["private_setup_method_gate"],
            next_action="run_method_gate",
            stop_condition="Stop unless the handoff is ready for method gating.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=4,
            phase="method_gate",
            operation="private_setup_method_gate",
            cli_command=agent_call_command(
                "private_setup_method_gate",
                "--private-setup-request-id",
                PRIVATE_SETUP_REQUEST_ID,
                "--method-gate-case",
                "confirmed_builder_draft",
            ),
            required_inputs=[
                input_field("privateSetupRequestId", PRIVATE_SETUP_REQUEST_ID, "private setup bundle"),
                input_field("methodGateCase", "confirmed_builder_draft", "ready source-handoff fixture"),
            ],
            expected_field="payload.sourceHandoffMethodGate.methodGateStatus",
            expected_value=method_gate["sourceHandoffMethodGate"]["methodGateStatus"],
            allowed_next=["private_setup_forecast_execution"],
            next_action="run_forecast_execution",
            stop_condition="Stop unless method gates explicitly allow setup forecast execution.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=5,
            phase="forecast_execution",
            operation="private_setup_forecast_execution",
            cli_command=agent_call_command(
                "private_setup_forecast_execution",
                "--private-setup-request-id",
                PRIVATE_SETUP_REQUEST_ID,
                "--forecast-execution-case",
                "confirmed_builder_draft",
            ),
            required_inputs=[
                input_field("privateSetupRequestId", PRIVATE_SETUP_REQUEST_ID, "private setup bundle"),
                input_field("forecastExecutionCase", "confirmed_builder_draft", "method-gate allowed fixture"),
            ],
            expected_field="payload.setupForecastRun.runStatus",
            expected_value=execution["setupForecastRun"]["runStatus"],
            allowed_next=["forecast_card"],
            next_action="read_forecast_card",
            stop_condition="Stop before readback if no forecastId and questionId are generated.",
            creates_forecast_artifacts=True,
            operations=operations,
        ),
        step(
            sequence=6,
            phase="forecast_readback",
            operation="forecast_card",
            cli_command=agent_call_command(
                "forecast_card",
                "--forecast-id",
                FORECAST_ID,
                "--question-id",
                QUESTION_ID,
            ),
            required_inputs=[
                input_field("forecastId", FORECAST_ID, "setup forecast execution result"),
                input_field("questionId", QUESTION_ID, "setup forecast execution result"),
            ],
            expected_field="payload.record.status",
            expected_value=card["status"],
            allowed_next=["lifecycle_bundle"],
            next_action="read_lifecycle_bundle",
            stop_condition="Stop if the card does not preserve setup forecast run and source-handoff bindings.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=7,
            phase="forecast_readback",
            operation="lifecycle_bundle",
            cli_command=agent_call_command(
                "lifecycle_bundle",
                "--forecast-id",
                FORECAST_ID,
                "--question-id",
                QUESTION_ID,
            ),
            required_inputs=[
                input_field("forecastId", FORECAST_ID, "setup forecast execution result"),
                input_field("questionId", QUESTION_ID, "setup forecast execution result"),
            ],
            expected_field="payload.record.includedRecords.setupForecastRun",
            expected_value=bundle_record["includedRecords"]["setupForecastRun"],
            allowed_next=["resolution_status"],
            next_action="check_resolution_status",
            stop_condition="Use the bundle for audit context, not as a new forecast source.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=8,
            phase="forecast_readback",
            operation="resolution_status",
            cli_command=agent_call_command(
                "resolution_status",
                "--forecast-id",
                FORECAST_ID,
                "--question-id",
                QUESTION_ID,
            ),
            required_inputs=[
                input_field("forecastId", FORECAST_ID, "setup forecast execution result"),
                input_field("questionId", QUESTION_ID, "setup forecast execution result"),
            ],
            expected_field="payload.resolutionStatus",
            expected_value=resolution["status"],
            allowed_next=["scoring_summary"],
            next_action="read_scoring_summary",
            stop_condition="Do not score unresolved, ambiguous, annulled, or unscorable outcomes as normal.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
        step(
            sequence=9,
            phase="forecast_readback",
            operation="scoring_summary",
            cli_command=agent_call_command(
                "scoring_summary",
                "--forecast-id",
                FORECAST_ID,
                "--question-id",
                QUESTION_ID,
            ),
            required_inputs=[
                input_field("forecastId", FORECAST_ID, "setup forecast execution result"),
                input_field("questionId", QUESTION_ID, "setup forecast execution result"),
            ],
            expected_field="payload.scoreStatus",
            expected_value=scoring["scoreStatus"],
            allowed_next=[],
            next_action="stop",
            stop_condition="Stop before quality claims because source-handoff sample size remains below threshold.",
            creates_forecast_artifacts=False,
            operations=operations,
        ),
    ]


def branch_playbooks() -> list[dict[str, Any]]:
    unconfirmed = source_handoff_result_payload(source_handoff_case="unconfirmed_builder_draft")
    confirmed = source_handoff_result_payload(source_handoff_case="confirmed_builder_draft")
    insufficient = source_handoff_result_payload(source_handoff_case="insufficient_confirmed_builder_draft")
    rejected = source_builder_result_payload(source_builder_case="contains_secret")
    generated = forecast_execution_result_payload(forecast_execution_case="confirmed_builder_draft")
    return [
        {
            "branchId": "adapterchainbranch-001",
            "branchName": "mapping_confirmation_required",
            "triggerOperation": "private_setup_source_handoff",
            "triggerCase": "unconfirmed_builder_draft",
            "triggerStatusField": "payload.sourceIntakeHandoff.handoffStatus",
            "triggerStatus": unconfirmed["sourceIntakeHandoff"]["handoffStatus"],
            "nextAction": "ask_mapping_confirmation",
            "allowedNextOperation": None,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Stop until the caller confirms inferred mappings and aliases.",
            "agentInstruction": "Ask for confirmation; do not proceed to method gates or forecasts from proposed mappings.",
        },
        {
            "branchId": "adapterchainbranch-002",
            "branchName": "confirmed_handoff_ready",
            "triggerOperation": "private_setup_source_handoff",
            "triggerCase": "confirmed_builder_draft",
            "triggerStatusField": "payload.sourceIntakeHandoff.handoffStatus",
            "triggerStatus": confirmed["sourceIntakeHandoff"]["handoffStatus"],
            "nextAction": "run_method_gate",
            "allowedNextOperation": "private_setup_method_gate",
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Proceed only to method gates; source-handoff itself does not forecast.",
            "agentInstruction": "Carry source-intake, field-mapping, and handoff IDs into method-gate guidance.",
        },
        {
            "branchId": "adapterchainbranch-003",
            "branchName": "insufficient_data",
            "triggerOperation": "private_setup_source_handoff",
            "triggerCase": "insufficient_confirmed_builder_draft",
            "triggerStatusField": "payload.sourceIntakeHandoff.handoffStatus",
            "triggerStatus": insufficient["sourceIntakeHandoff"]["handoffStatus"],
            "nextAction": "collect_more_data",
            "allowedNextOperation": "private_setup_source_builder",
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Stop until the caller supplies enough usable forecast-time and outcome rows.",
            "agentInstruction": "Return to source-builder guidance after adding data; do not force a method gate.",
        },
        {
            "branchId": "adapterchainbranch-004",
            "branchName": "rejected_source",
            "triggerOperation": "private_setup_source_builder",
            "triggerCase": "contains_secret",
            "triggerStatusField": "payload.sourceManifestBuild.buildStatus",
            "triggerStatus": rejected["sourceManifestBuild"]["buildStatus"],
            "nextAction": "replace_rejected_sources",
            "allowedNextOperation": "private_setup_source_builder",
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Stop until rejected, secret-bearing, oversized, unsupported, or leakage sources are replaced.",
            "agentInstruction": "Do not pass rejected builder outputs to source-handoff, method gates, forecasts, or scoring.",
        },
        {
            "branchId": "adapterchainbranch-005",
            "branchName": "generated_forecast_readback",
            "triggerOperation": "private_setup_forecast_execution",
            "triggerCase": "confirmed_builder_draft",
            "triggerStatusField": "payload.setupForecastRun.runStatus",
            "triggerStatus": generated["setupForecastRun"]["runStatus"],
            "nextAction": "read_forecast_card",
            "allowedNextOperation": "forecast_card",
            "forecastArtifactsAllowed": True,
            "scoringAllowed": False,
            "stopCondition": "Read generated forecasts through normal read operations before any downstream use.",
            "agentInstruction": "Use forecast-1102 and question-1102 with card, bundle, resolution, and scoring reads.",
        },
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "adapterchainguard-001",
            "name": "operation_binding",
            "rule": "Every step must bind an existing protocol-map operation and MCP tool.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
        {
            "guardId": "adapterchainguard-002",
            "name": "local_file_path_only",
            "rule": "The current adapter chain runbook covers only the checked local-file private setup path.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
        {
            "guardId": "adapterchainguard-003",
            "name": "confirmation_before_method_gate",
            "rule": "Unconfirmed source-handoff cases must stop for caller mapping confirmation before method gates.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
        {
            "guardId": "adapterchainguard-004",
            "name": "blocked_cases_do_not_forecast",
            "rule": "Insufficient-data and rejected-source branches must not allow forecast artifacts or scoring.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
        {
            "guardId": "adapterchainguard-005",
            "name": "normal_readback_operations",
            "rule": "Generated setup forecasts must use normal readback operations instead of a private read API.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
        {
            "guardId": "adapterchainguard-006",
            "name": "guidance_only_boundary",
            "rule": "The runbook may name adapter calls but must not execute them or create records.",
            "checkedBy": ["scripts/check_private_setup_adapter_chain_runbook.py"],
        },
    ]


def build_runbook() -> dict[str, Any]:
    operations = operation_map()
    bundle = bundle_by_request_id(PRIVATE_SETUP_REQUEST_ID)
    source_policy = bundle["requestSummary"]["sourcePolicy"]
    runbook = {
        "privateSetupAdapterChainRunbookId": "privatesetupadapterchainrunbook-001",
        "generatedAt": GENERATED_AT,
        "scope": "private_setup_local_file_adapter_chain",
        "runtimeStatus": "runbook_guidance_only",
        "entrypoints": {
            "runbookCommand": "python3 scripts/ope.py private-setup-adapter-runbook",
            "adapterDispatcherCommand": "python3 scripts/ope.py agent-call",
            "protocolMapFixture": "spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json",
            "runbookSchema": "spec/private-setup-adapter-chain-runbook.schema.json",
        },
        "sourcePath": {
            "privateSetupRequestId": PRIVATE_SETUP_REQUEST_ID,
            "privateSetupAgentBundleId": bundle["privateSetupAgentBundleId"],
            "sourceKind": bundle["sourceKind"],
            "dataMode": source_policy["dataMode"],
            "approvalStatus": source_policy["approvalStatus"],
            "allowLiveFetch": source_policy["allowLiveFetch"],
            "allowCredentialUse": source_policy["allowCredentialUse"],
        },
        "operationSequence": operation_sequence(operations, bundle),
        "branchPlaybooks": branch_playbooks(),
        "executionBoundary": {
            "runbookDoesNotExecute": True,
            "runsAdapterCalls": False,
            "readsPrivateData": False,
            "createsSourceManifests": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "createsHostedRuntime": False,
            "normalChecksOffline": True,
        },
        "guards": guards(),
        "warnings": [
            "This runbook is guidance over adapter operations; it does not execute adapter calls.",
            "Mapping confirmation, insufficient data, and rejected source cases stop before method gates or forecast artifacts.",
            "Generated setup forecasts are read through normal forecast readback operations, not a private setup read API.",
            "The runbook does not imply hosted service, production adapter runtime, live fetching, credential handling, calibration, or quality claims.",
        ],
    }
    validate_runbook(runbook)
    return runbook


def validate_runbook(runbook: dict[str, Any]) -> None:
    errors = validate_record(runbook, SCHEMA)
    if errors:
        raise PrivateSetupAdapterChainRunbookError(
            f"private setup adapter-chain runbook schema validation failed: {errors[0]}"
        )
    operations = operation_map()
    operation_names = set(operations)
    sequence = runbook["operationSequence"]
    if [step["order"] for step in sequence] != list(range(1, len(sequence) + 1)):
        raise PrivateSetupAdapterChainRunbookError("operation sequence order should be contiguous")
    for item in sequence:
        operation = item["operation"]
        if operation not in operation_names:
            raise PrivateSetupAdapterChainRunbookError(f"unknown operation in runbook: {operation}")
        if item["mcpTool"] != operations[operation]["mcp"]["toolName"]:
            raise PrivateSetupAdapterChainRunbookError(f"{operation} MCP tool binding drift")
        if item["sideEffectLevel"] != operations[operation]["sideEffectLevel"]:
            raise PrivateSetupAdapterChainRunbookError(f"{operation} side-effect binding drift")
        if item["createsScoringRecords"] is not False:
            raise PrivateSetupAdapterChainRunbookError("runbook steps must not create scoring records")

    forecast_step = next(item for item in sequence if item["operation"] == "private_setup_forecast_execution")
    if forecast_step["createsForecastArtifacts"] is not True:
        raise PrivateSetupAdapterChainRunbookError("confirmed forecast execution step should allow forecast artifacts")
    for item in sequence:
        if item["operation"] != "private_setup_forecast_execution" and item["createsForecastArtifacts"] is not False:
            raise PrivateSetupAdapterChainRunbookError(f"{item['operation']} should not create forecast artifacts")

    readback_ops = [item["operation"] for item in sequence if item["phase"] == "forecast_readback"]
    if readback_ops != ["forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"]:
        raise PrivateSetupAdapterChainRunbookError("readback sequence should use normal read operations")

    expected_branches = {
        "mapping_confirmation_required",
        "confirmed_handoff_ready",
        "insufficient_data",
        "rejected_source",
        "generated_forecast_readback",
    }
    branches = {item["branchName"]: item for item in runbook["branchPlaybooks"]}
    if set(branches) != expected_branches:
        raise PrivateSetupAdapterChainRunbookError("adapter-chain runbook should cover required branch playbooks")
    for name in ["mapping_confirmation_required", "insufficient_data", "rejected_source"]:
        branch = branches[name]
        if branch["forecastArtifactsAllowed"] or branch["scoringAllowed"]:
            raise PrivateSetupAdapterChainRunbookError(f"{name} branch must not allow forecast artifacts or scoring")
    if branches["generated_forecast_readback"]["allowedNextOperation"] != "forecast_card":
        raise PrivateSetupAdapterChainRunbookError("generated forecast branch should route to forecast_card")

    boundary = runbook["executionBoundary"]
    if boundary["runbookDoesNotExecute"] is not True or boundary["runsAdapterCalls"] is not False:
        raise PrivateSetupAdapterChainRunbookError("runbook must remain non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        if boundary[key] is not False:
            raise PrivateSetupAdapterChainRunbookError(f"{key} should remain false")


def write_runbook(runbook: dict[str, Any]) -> None:
    write_generated(RUNBOOK_PATH, runbook, label="private setup adapter-chain runbook", regen="python3 scripts/generate_private_setup_adapter_chain_runbook.py --write")


def check_runbook(runbook: dict[str, Any]) -> None:
    check_generated(RUNBOOK_PATH, runbook, label="private setup adapter-chain runbook", regen="python3 scripts/generate_private_setup_adapter_chain_runbook.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated runbook drift")
    parser.add_argument("--write", action="store_true", help="write generated runbook")
    args = parser.parse_args()
    try:
        runbook = build_runbook()
    except PrivateSetupAdapterChainRunbookError as exc:
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
