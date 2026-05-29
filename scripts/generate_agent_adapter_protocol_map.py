#!/usr/bin/env python3
"""Generate or check the OPE agent adapter protocol mapping."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


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
    "private_setup_bundle",
    "private_setup_adapter_runbook",
    "private_setup_adapter_conformance_summary",
    "private_source_adapter_guidance",
    "private_source_kind_selection",
    "private_setup_source_builder",
    "private_setup_source_handoff",
    "private_setup_method_gate",
    "private_setup_forecast_execution",
    "resolution_jobs",
    "resolution_scheduler_status",
    "resolution_status",
    "scoring_summary",
]

INPUT_RECORD_TYPES = {
    "forecast_request_validation": "forecast_request",
    "evidence_plan": "evidence_gathering_plan",
    "evidence_trace": "evidence_trace",
    "forecast_card": "forecast_card",
    "lifecycle_bundle": "lifecycle_bundle",
    "private_setup_bundle": "private_setup_agent_bundle",
    "private_setup_adapter_runbook": "private_setup_adapter_chain_runbook",
    "private_setup_adapter_conformance_summary": "private_setup_adapter_conformance_summary",
    "private_source_adapter_guidance": "private_source_adapter_capability",
    "private_source_kind_selection": "private_source_kind_selection_examples",
    "private_setup_source_builder": "source_manifest_build",
    "private_setup_source_handoff": "source_intake_handoff",
    "private_setup_method_gate": "source_handoff_method_gate",
    "private_setup_forecast_execution": "setup_forecast_run",
    "resolution_jobs": "resolution_job_registry",
    "resolution_scheduler_status": "resolution_scheduler_status",
    "resolution_status": "resolution_status",
    "scoring_summary": "scoring_summary",
}

SIDE_EFFECT_LEVELS = {
    "forecast_request_validation": "validation_only",
    "evidence_plan": "dry_run_generation",
    "evidence_trace": "read_only",
    "forecast_card": "read_only",
    "lifecycle_bundle": "read_only",
    "private_setup_bundle": "read_only",
    "private_setup_adapter_runbook": "read_only",
    "private_setup_adapter_conformance_summary": "read_only",
    "private_source_adapter_guidance": "read_only",
    "private_source_kind_selection": "read_only",
    "private_setup_source_builder": "dry_run_generation",
    "private_setup_source_handoff": "dry_run_generation",
    "private_setup_method_gate": "dry_run_generation",
    "private_setup_forecast_execution": "forecast_execution",
    "resolution_jobs": "read_only",
    "resolution_scheduler_status": "read_only",
    "resolution_status": "status_read",
    "scoring_summary": "scoring_read",
}

USAGE_GUIDANCE = {
    "forecast_request_validation": "Use before any forecast execution, live fetch, paid action, or privacy-sensitive action.",
    "evidence_plan": "Use after an accepted request to inspect source policy, planned connectors, and approval boundaries.",
    "evidence_trace": "Use when the caller needs connector-bound source provenance without raw fixture contents.",
    "forecast_card": "Use first for compact downstream decisions that need probability, baseline, status, warnings, and setup bindings, including generated private setup forecasts.",
    "lifecycle_bundle": "Use when the caller needs audit context, provenance, evidence, history, setup bindings, resolution, and scoring records for normal or setup-generated forecasts.",
    "private_setup_bundle": "Use when an agent needs setup guidance for a private setup request without executing source setup.",
    "private_setup_adapter_runbook": "Use when an agent needs the checked private setup adapter operation sequence and readback path without executing adapter calls.",
    "private_setup_adapter_conformance_summary": "Use when an agent needs compact private setup adapter conformance status without loading the full embedded-envelope matrix.",
    "private_source_adapter_guidance": "Use when an agent needs private source adapter capability, outcome, and intake-bridge guidance without executing source reads.",
    "private_source_kind_selection": "Use when an agent needs checked source-kind path selection examples without executing source setup, fixture evidence, forecast execution, or scoring.",
    "private_setup_source_builder": "Use after local-file setup guidance to inspect caller-approved CSV/JSON files and draft setup records.",
    "private_setup_source_handoff": "Use after source-builder guidance to inspect checked source-handoff next actions and confirmation gates.",
    "private_setup_method_gate": "Use after confirmed source-handoff guidance to inspect setup benchmark and method-decision readiness.",
    "private_setup_forecast_execution": "Use only after method-gate readiness to run checked setup forecast execution and return artifacts for allowed cases; read generated forecasts through normal read operations.",
    "resolution_jobs": "Use when an agent needs pending, due, resolved, invalid, and waiting resolution-job guidance without reading local state files or executing resolvers.",
    "resolution_scheduler_status": "Use when an agent needs the last scheduler tick, shutdown reason, log path, execution mode, queue state readbacks, and next action without starting a scheduler.",
    "resolution_status": "Use when an agent needs to decide whether a normal or setup-generated forecast is resolved, pending, ambiguous, or annulled.",
    "scoring_summary": "Use when an agent needs score, baseline comparison, and quality-claim boundaries before acting on a normal or setup-generated forecast.",
}

HTTP_PATHS = {
    "forecast_request_validation": "/agent/forecast-request-validation",
    "evidence_plan": "/agent/evidence-plan",
    "evidence_trace": "/agent/evidence-trace",
    "forecast_card": "/agent/forecast-card",
    "lifecycle_bundle": "/agent/lifecycle-bundle",
    "private_setup_bundle": "/agent/private-setup-bundle",
    "private_setup_adapter_runbook": "/agent/private-setup-adapter-runbook",
    "private_setup_adapter_conformance_summary": "/agent/private-setup-adapter-conformance-summary",
    "private_source_adapter_guidance": "/agent/private-source-adapter-guidance",
    "private_source_kind_selection": "/agent/private-source-kind-selection",
    "private_setup_source_builder": "/agent/private-setup-source-builder",
    "private_setup_source_handoff": "/agent/private-setup-source-handoff",
    "private_setup_method_gate": "/agent/private-setup-method-gate",
    "private_setup_forecast_execution": "/agent/private-setup-forecast-execution",
    "resolution_jobs": "/agent/resolution-jobs",
    "resolution_scheduler_status": "/agent/resolution-scheduler-status",
    "resolution_status": "/agent/resolution-status",
    "scoring_summary": "/agent/scoring-summary",
}


class ProtocolMapError(Exception):
    pass


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
    if operation == "private_setup_bundle":
        return [
            field(
                "privateSetupRequestId",
                False,
                "id",
                "agent-call --private-setup-request-id",
                "Private setup request ID to read as a guidance bundle; defaults to the checked local-file fixture.",
            ),
            field(
                "privateSetupCase",
                False,
                "string",
                "agent-call --private-setup-case",
                "Optional checked bad-request example case: unknown_source_kind or missing_approval.",
            ),
            *common,
        ]
    if operation == "private_setup_adapter_runbook":
        return [
            *common,
        ]
    if operation == "private_setup_adapter_conformance_summary":
        return [
            *common,
        ]
    if operation == "resolution_jobs":
        return [
            *common,
        ]
    if operation == "resolution_scheduler_status":
        return [
            *common,
        ]
    if operation == "private_source_adapter_guidance":
        return [
            *common,
        ]
    if operation == "private_source_kind_selection":
        return [
            field(
                "sourceKind",
                False,
                "string",
                "agent-call --source-kind",
                "Optional source kind to return one selected example; unknown values return a sanitized bad_request envelope.",
            ),
            *common,
        ]
    if operation == "private_setup_source_builder":
        return [
            field(
                "privateSetupRequestId",
                False,
                "id",
                "agent-call --private-setup-request-id",
                "Private setup request ID to bind to the source-builder adapter result.",
            ),
            field(
                "sourceBuilderCase",
                False,
                "string",
                "agent-call --source-builder-case",
                "Optional checked source-builder fixture case for local adapter verification.",
            ),
            field(
                "sourceBuilderInputs",
                False,
                "string-list",
                "agent-call --source-builder-input",
                "Caller-approved local source_role=path inputs; adapters must not discover files implicitly.",
            ),
            field(
                "mappingHints",
                False,
                "string-list",
                "agent-call --source-builder-mapping-hint",
                "Caller-provided source_role.source_field=target_field hints; inferred mappings still require confirmation.",
            ),
            *common,
        ]
    if operation == "private_setup_source_handoff":
        return [
            field(
                "privateSetupRequestId",
                False,
                "id",
                "agent-call --private-setup-request-id",
                "Private setup request ID to bind to the source-handoff adapter result.",
            ),
            field(
                "sourceHandoffCase",
                False,
                "string",
                "agent-call --source-handoff-case",
                "Checked source-handoff fixture case; adapters must not accept raw private data in this operation.",
            ),
            *common,
        ]
    if operation == "private_setup_method_gate":
        return [
            field(
                "privateSetupRequestId",
                False,
                "id",
                "agent-call --private-setup-request-id",
                "Private setup request ID to bind to the method-gate adapter result.",
            ),
            field(
                "methodGateCase",
                False,
                "string",
                "agent-call --method-gate-case",
                "Checked source-handoff method-gate fixture case; adapters must not accept raw private data in this operation.",
            ),
            *common,
        ]
    if operation == "private_setup_forecast_execution":
        return [
            field(
                "privateSetupRequestId",
                False,
                "id",
                "agent-call --private-setup-request-id",
                "Private setup request ID to bind to the forecast-execution adapter result.",
            ),
            field(
                "forecastExecutionCase",
                False,
                "string",
                "agent-call --forecast-execution-case",
                "Checked source-handoff forecast-execution fixture case; adapters must not accept raw private data in this operation.",
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
    if operation == "private_setup_bundle":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_bundle "
            "--private-setup-request-id privatesetuprequest-001"
        )
    if operation == "private_setup_adapter_runbook":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_adapter_runbook"
        )
    if operation == "private_setup_adapter_conformance_summary":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_adapter_conformance_summary"
        )
    if operation == "resolution_jobs":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation resolution_jobs"
        )
    if operation == "resolution_scheduler_status":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation resolution_scheduler_status"
        )
    if operation == "private_source_adapter_guidance":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_source_adapter_guidance"
        )
    if operation == "private_source_kind_selection":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_source_kind_selection"
        )
    if operation == "private_setup_source_builder":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_source_builder "
            "--private-setup-request-id privatesetuprequest-001 "
            "--source-builder-case local_draft"
        )
    if operation == "private_setup_source_handoff":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_source_handoff "
            "--private-setup-request-id privatesetuprequest-001 "
            "--source-handoff-case confirmed_builder_draft"
        )
    if operation == "private_setup_method_gate":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_method_gate "
            "--private-setup-request-id privatesetuprequest-001 "
            "--method-gate-case confirmed_builder_draft"
        )
    if operation == "private_setup_forecast_execution":
        return (
            "python3 scripts/ope.py agent-call "
            "--operation private_setup_forecast_execution "
            "--private-setup-request-id privatesetuprequest-001 "
            "--forecast-execution-case confirmed_builder_draft"
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
    if operation in {
        "forecast_request_validation",
        "forecast_card",
        "lifecycle_bundle",
        "private_setup_bundle",
        "private_setup_adapter_runbook",
        "private_setup_adapter_conformance_summary",
        "private_source_adapter_guidance",
        "private_source_kind_selection",
        "resolution_jobs",
        "resolution_scheduler_status",
        "resolution_status",
        "scoring_summary",
    }:
        return "Read, validation, and status operations should remain approval-free unless caller policy marks the record sensitive."
    if operation == "private_setup_source_builder":
        return "Source-builder adapter inputs must be explicit caller-approved paths; it must not discover or read private files implicitly."
    if operation == "private_setup_source_handoff":
        return "Source-handoff adapter cases must preserve caller confirmation gates before routing to setup method gates."
    if operation == "private_setup_method_gate":
        return "Method-gate adapter cases must preserve setup benchmark and method-decision gates before recommending explicit forecast execution."
    if operation == "private_setup_forecast_execution":
        return "Forecast-execution adapter calls must require method-gate permission and remain blocked for unconfirmed, insufficient, rejected, or leakage cases."
    return "Evidence planning may return approval_required and must not perform live fetches, paid calls, or private-source access."


def credential_boundary(operation: str) -> str:
    if operation == "evidence_plan":
        return "Connector credentials stay server-side and must never appear in prompt-visible arguments or returned records."
    if operation == "private_setup_bundle":
        return "Private setup bundle reads accept no credentials in prompt-visible arguments and return only guidance records."
    if operation == "private_setup_adapter_runbook":
        return "Private setup adapter-runbook reads accept no credentials in prompt-visible arguments and return only checked operation-sequence guidance."
    if operation == "private_setup_adapter_conformance_summary":
        return "Private setup adapter conformance-summary reads accept no credentials in prompt-visible arguments and return only compact checked conformance guidance."
    if operation == "private_source_adapter_guidance":
        return "Private source adapter guidance accepts no credentials in prompt-visible arguments and returns only capability, outcome, and routing guidance records."
    if operation == "private_source_kind_selection":
        return "Private source-kind selection accepts no credentials in prompt-visible arguments and returns only checked selection examples."
    if operation == "private_setup_source_builder":
        return "Source-builder adapter arguments may include caller-approved paths and mapping hints, but never credentials or tokens."
    if operation == "private_setup_source_handoff":
        return "Source-handoff adapter arguments may include checked case IDs only, not raw private payloads, credentials, or tokens."
    if operation == "private_setup_method_gate":
        return "Method-gate adapter arguments may include checked case IDs only, not raw private payloads, credentials, or tokens."
    if operation == "private_setup_forecast_execution":
        return "Forecast-execution adapter arguments may include checked case IDs only, not raw private payloads, credentials, or tokens."
    if operation == "resolution_jobs":
        return "Resolution-job readbacks accept no credentials in prompt-visible arguments and return only checked registry guidance."
    if operation == "resolution_scheduler_status":
        return "Resolution-scheduler status reads accept no credentials in prompt-visible arguments and return only checked scheduler readback guidance."
    return "Credentials are not required for the current local operation and must not be accepted in prompt-visible arguments."


def operation_map(operation: str) -> dict[str, Any]:
    fields = input_fields(operation)
    return {
        "operation": operation,
        "inputRecordType": INPUT_RECORD_TYPES[operation],
        "sideEffectLevel": SIDE_EFFECT_LEVELS[operation],
        "requiresApproval": operation in {
            "evidence_plan",
            "private_setup_source_builder",
            "private_setup_source_handoff",
            "private_setup_method_gate",
            "private_setup_forecast_execution",
        },
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
            "situation": "The agent needs to understand the first safe setup action for a private setup request.",
            "preferredOperation": "private_setup_bundle",
            "reason": "The bundle joins request, first-action, and runbook guidance without executing source setup.",
            "requiredSignals": ["requestId", "sourceKind", "actionStatus", "nextActionLabel", "executionBoundary"],
            "downstreamRule": "Use the bundle as setup guidance only; do not treat it as a forecast or source-intake artifact.",
        },
        {
            "situation": "The agent needs the full private setup adapter sequence before calling setup operations.",
            "preferredOperation": "private_setup_adapter_runbook",
            "reason": "The runbook lists setup guidance, source-builder, source-handoff, method-gate, forecast execution, and normal readback order.",
            "requiredSignals": ["operationSequence", "branchPlaybooks", "executionBoundary", "warnings"],
            "downstreamRule": "Use the runbook as read-only guidance; it must not execute adapter calls or create source, forecast, resolution, or scoring artifacts.",
        },
        {
            "situation": "The agent needs compact private setup adapter conformance status before deciding which adapter operation to call.",
            "preferredOperation": "private_setup_adapter_conformance_summary",
            "reason": "The summary records phase counts, operation coverage, artifact boundaries, sanitized-error coverage, and the full matrix pointer without embedding every envelope.",
            "requiredSignals": ["caseTotals", "operationSummaries", "artifactBoundary", "readSurface", "executionBoundary"],
            "downstreamRule": "Use the summary for routine conformance checks; load the full matrix only when implementing or debugging adapter behavior.",
        },
        {
            "situation": "The agent needs to know which private source kinds OPE can currently route before setup.",
            "preferredOperation": "private_source_adapter_guidance",
            "reason": "The guidance joins capability declarations, outcome classes, and intake-bridge routing without executing source reads.",
            "requiredSignals": ["sourceKindSummary", "capability", "outcomeMatrix", "intakeBridge", "executionBoundary"],
            "downstreamRule": "Use this as source-kind guidance only; planned private API, database, and upload paths remain non-executing.",
        },
        {
            "situation": "The agent needs to choose the next private source-kind path before lower-level setup calls.",
            "preferredOperation": "private_source_kind_selection",
            "reason": "The examples bind source adapter guidance, first actions, and the adapter-chain runbook into source-kind-specific next actions.",
            "requiredSignals": ["selectionExamples", "recommendation.immediateAction", "adapterChainBinding", "executionBoundary"],
            "downstreamRule": "Use these examples as read-only path selection; do not execute source setup, fixture evidence, forecasts, or scoring from this operation.",
        },
        {
            "situation": "The private setup bundle says caller-approved local files are the next setup step.",
            "preferredOperation": "private_setup_source_builder",
            "reason": "The adapter inspects explicit CSV/JSON paths and returns draft manifest and mapping guidance.",
            "requiredSignals": ["buildStatus", "inputFiles", "draftArtifacts", "confirmationRequired"],
            "downstreamRule": "Do not forecast from drafts until source intake, method gates, and benchmark decisions pass.",
        },
        {
            "situation": "The agent needs to continue from source-builder guidance into source-handoff next actions.",
            "preferredOperation": "private_setup_source_handoff",
            "reason": "The adapter returns checked handoff status, mapping confirmation, intake binding, and method-gate readiness.",
            "requiredSignals": ["handoffStatus", "nextAction", "sourceIntakeReportId", "requiresMappingConfirmation"],
            "downstreamRule": "Only confirmed accepted handoffs may proceed to setup benchmark and method gates; the adapter itself does not forecast.",
        },
        {
            "situation": "The agent needs to know whether a confirmed private setup may run explicit forecast execution.",
            "preferredOperation": "private_setup_method_gate",
            "reason": "The adapter returns setup benchmark, method decision, selected method, and explicit forecast-execution readiness.",
            "requiredSignals": ["methodGateStatus", "setupBenchmarkGateId", "setupMethodDecisionId", "canRecommendExplicitSetupForecastExecution"],
            "downstreamRule": "Run setup forecast execution only when the method gate recommends it; the adapter itself does not create forecasts.",
        },
        {
            "situation": "The agent has method-gate permission and needs the setup forecast artifacts.",
            "preferredOperation": "private_setup_forecast_execution",
            "reason": "The adapter returns a setup forecast run plus forecast artifacts only for the allowed confirmed handoff.",
            "requiredSignals": ["runStatus", "setupForecastRunId", "forecastArtifactsCreated", "forecastId"],
            "downstreamRule": "Use the returned forecastId and questionId with forecast_card, lifecycle_bundle, resolution_status, or scoring_summary; do not invent a private setup read API.",
        },
        {
            "situation": "The agent needs to know whether any forward-run forecasts are due for outcome resolution.",
            "preferredOperation": "resolution_jobs",
            "reason": "The registry exposes pending, due, waiting, resolved, and invalid job guidance without executing resolvers.",
            "requiredSignals": ["summary", "jobs", "agentAction", "executionBoundary"],
            "downstreamRule": "Use due job commands only after explicit live resolver approval; the readback itself must not execute.",
        },
        {
            "situation": "The agent needs the latest scheduler status before deciding to wait, execute, inspect, or stop.",
            "preferredOperation": "resolution_scheduler_status",
            "reason": "The status payload exposes the latest tick, queue states, shutdown/log path, execution mode, and next action.",
            "requiredSignals": ["lastTick", "lastShutdown", "logPath", "executionMode", "nextRecommendedAction"],
            "downstreamRule": "Use the status as read-only guidance; it must not start a scheduler, execute resolvers, or create outcomes.",
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
