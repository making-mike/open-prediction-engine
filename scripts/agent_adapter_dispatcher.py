#!/usr/bin/env python3
"""Dispatch one local agent adapter operation and return one OPE envelope."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from build_agent_adapter_fixtures import (
    EXIT_CODES,
    SCHEMA,
    AgentAdapterError,
    FORECAST_EXECUTION_CASES,
    binding_from_card,
    binding_from_trace,
    envelope,
    forecast_execution_result_payload,
    load_private_setup_adapter_conformance_summary,
    load_private_setup_adapter_runbook,
    load_private_source_kind_selection_examples,
    load_resolution_job_registry,
    load_resolution_scheduler_run,
    nullable_binding,
    nullable_state,
    private_source_adapter_guidance_payload as build_private_source_adapter_guidance_payload,
    render_json,
    resolution_scheduler_status_payload as build_resolution_scheduler_status_payload,
    SOURCE_BUILDER_CASES,
    SOURCE_HANDOFF_CASES,
    METHOD_GATE_CASES,
    method_gate_result_payload,
    source_builder_result_payload,
    source_handoff_result_payload,
    state_from_method_gate_payload,
    state_from_forecast_execution_payload,
    state_from_private_setup_adapter_conformance_summary,
    state_from_private_setup_adapter_runbook,
    state_from_private_source_adapter_guidance,
    state_from_private_source_kind_selection,
    state_from_resolution_job_registry,
    state_from_resolution_scheduler_status,
    state_from_source_builder_payload,
    state_from_source_handoff_payload,
    state_from_card,
    validate_envelope_semantics,
)
from build_source_manifest import SourceBuildError
from generate_source_intake_handoff import SourceIntakeHandoffError
from generate_source_handoff_method_gate import SourceHandoffMethodGateError
from ope_schema import validate_record
from plan_auto_evidence import DEFAULT_REQUEST, EvidencePlanError, build_plan
from run_source_handoff_forecast import SourceHandoffForecastError
from generate_private_setup_agent_bundles import (
    BAD_REQUEST_CASES,
    PrivateSetupAgentBundleError,
    bundle_by_case,
    bundle_by_request_id,
)
from read_ope_record import DEFAULT_MAX_BYTES, PublicError, read_record
from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORECAST_ID = "forecast-602"
DEFAULT_QUESTION_ID = "question-601"
DEFAULT_PRIVATE_SETUP_REQUEST_ID = "privatesetuprequest-001"
DEFAULT_CALLER_INTENT = "Call one local OPE agent adapter operation."
CAPABILITY_BY_OPERATION = {
    "forecast_request_validation": "validation",
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
    "resolution_status": "resolution_check",
    "scoring_summary": "scoring_read",
}
INPUT_TYPE_BY_OPERATION = {
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
FORECAST_BOUND_OPERATIONS = {
    "evidence_trace",
    "forecast_card",
    "lifecycle_bundle",
    "resolution_status",
    "scoring_summary",
}


class AgentCallError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        retryable: bool = False,
        binding: dict[str, str | None] | None = None,
        state: dict[str, str | None] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.binding = binding or nullable_binding()
        self.state = state or nullable_state()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def input_ref_for(args: argparse.Namespace) -> str:
    if args.operation in {"evidence_trace", "forecast_card", "lifecycle_bundle"}:
        return args.forecast_id
    if args.operation == "forecast_request_validation":
        request = load_json(args.request)
        if not isinstance(request, dict):
            raise AgentCallError("validation_failed", "Request contract validation failed.")
        value = request.get("requestId")
        if not isinstance(value, str):
            raise AgentCallError("validation_failed", "Request contract validation failed.")
        return value
    if args.operation == "evidence_plan":
        plan = build_plan(args.request)
        return plan["evidencePlanId"]
    if args.operation == "resolution_status":
        return resolution_payload(args.forecast_id, args.question_id)["resolutionRecordId"]
    if args.operation == "scoring_summary":
        return scoring_payload(args.forecast_id, args.question_id)["scoringReportId"]
    if args.operation == "private_setup_bundle":
        bundle = private_setup_bundle(args.private_setup_request_id, args.private_setup_case)
        return bundle["privateSetupAgentBundleId"]
    if args.operation == "private_setup_adapter_runbook":
        runbook = load_private_setup_adapter_runbook()
        return runbook["privateSetupAdapterChainRunbookId"]
    if args.operation == "private_setup_adapter_conformance_summary":
        summary = load_private_setup_adapter_conformance_summary()
        return summary["privateSetupAdapterConformanceSummaryId"]
    if args.operation == "private_source_adapter_guidance":
        guidance = build_private_source_adapter_guidance_payload()
        return guidance["bindingSummary"]["privateSourceAdapterCapabilityId"]
    if args.operation == "private_source_kind_selection":
        examples = load_private_source_kind_selection_examples()
        return examples["privateSourceKindSelectionExamplesId"]
    if args.operation == "private_setup_source_builder":
        payload = source_builder_payload(args)
        return payload["sourceManifestBuild"]["sourceManifestBuildId"]
    if args.operation == "private_setup_source_handoff":
        payload = source_handoff_payload(args)
        return payload["sourceIntakeHandoff"]["sourceIntakeHandoffId"]
    if args.operation == "private_setup_method_gate":
        payload = method_gate_payload(args)
        return payload["sourceHandoffMethodGate"]["sourceHandoffMethodGateId"]
    if args.operation == "private_setup_forecast_execution":
        payload = forecast_execution_payload(args)
        return payload["setupForecastRun"]["setupForecastRunId"]
    if args.operation == "resolution_jobs":
        registry = load_resolution_job_registry()
        return registry["resolutionJobRegistryId"]
    if args.operation == "resolution_scheduler_status":
        payload = build_resolution_scheduler_status_payload(load_resolution_scheduler_run())
        return payload["resolutionSchedulerStatusId"]
    raise AgentCallError("bad_request", "Unsupported agent operation.")


def valid_max_bytes(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def safe_max_bytes(value: Any) -> int | None:
    return value if valid_max_bytes(value) else None


def ensure_valid_adapter_request(args: argparse.Namespace) -> None:
    if not valid_max_bytes(args.max_bytes):
        raise AgentCallError("bad_request", "maxBytes must be a positive integer.")


def safe_caller_intent(value: Any) -> str:
    if isinstance(value, str) and 3 <= len(value) <= 200:
        return value
    return DEFAULT_CALLER_INTENT


def read_card_and_bundle(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    card = read_record("forecast-card", forecast_id, question_id)
    bundle = read_record("forecast-bundle", forecast_id, question_id)
    return card, bundle


def request_validation_payload(request_path: Path) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    request = load_json(request_path)
    decision = validate_request(request)
    request_id = decision.get("requestId")
    audit_log = decision.get("auditLog", {})
    binding = nullable_binding(
        requestId=request_id if isinstance(request_id, str) else None,
        sourcePolicyId=audit_log.get("sourcePolicyId") if isinstance(audit_log.get("sourcePolicyId"), str) else None,
    )
    state = nullable_state(
        decisionStatus=decision["decisionStatus"],
        approvalStatus=request.get("approval", {}).get("status") if isinstance(request, dict) else None,
        dataMode=audit_log.get("dataMode") if isinstance(audit_log.get("dataMode"), str) else None,
    )
    warnings = ["Validation does not execute forecast generation or live evidence fetching."]
    if decision["decisionStatus"] == "blocked":
        warnings.append("Request requires approval before execution.")
    if decision["decisionStatus"] == "rejected":
        warnings.append("Request was rejected before execution.")
    return decision, binding, state, warnings


def evidence_plan_payload(request_path: Path) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    request = load_json(request_path)
    decision = validate_request(request)
    plan = build_plan(request_path)
    binding = nullable_binding(
        requestId=plan["requestId"],
        evidencePlanId=plan["evidencePlanId"],
        sourcePolicyId=plan["sourcePolicy"]["sourcePolicyId"],
    )
    state = nullable_state(
        decisionStatus=decision["decisionStatus"],
        approvalStatus=request.get("approval", {}).get("status") if isinstance(request, dict) else None,
        dataMode=plan["dataMode"],
        planStatus=plan["planStatus"],
        executionMode=plan["executionMode"],
    )
    if plan["planStatus"] == "blocked":
        raise AgentCallError(
            "approval_required",
            "Request requires approval before evidence planning.",
            binding=binding,
            state=state,
        )
    if plan["planStatus"] != "planned":
        raise AgentCallError(
            "validation_failed",
            "Evidence plan could not proceed for the request.",
            binding=binding,
            state=state,
        )
    return plan, binding, state, plan["warnings"]


def forecast_card_payload(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    card_response, _bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    return card_response, binding_from_card(card), state_from_card(card), card["warnings"]


def lifecycle_bundle_payload(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    card_response, bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    warnings = [
        "Bundle read is local and read-only; it does not mutate forecast lifecycle records.",
        "Full bundles are larger than forecast cards and may include detailed provenance records.",
    ]
    return bundle_response, binding_from_card(card), state_from_card(card), warnings


def evidence_trace_payload(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    card_response, _bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    trace_response = read_record("evidence-trace", forecast_id, question_id)
    trace = trace_response["record"]
    warnings = [
        "Evidence trace is local, read-only, and excludes raw fixture contents and raw diagnostics.",
        "Connector results do not claim all possible internet evidence was gathered.",
    ]
    return trace_response, binding_from_trace(trace, card), state_from_card(card), warnings


def resolution_payload(forecast_id: str, question_id: str | None) -> dict[str, Any]:
    _card_response, bundle_response = read_card_and_bundle(forecast_id, question_id)
    records = bundle_response["record"]["records"]
    resolution = records["resolutionRecord"]
    outcome_summary = records["outcomeSummary"]
    if resolution is None:
        raise AgentCallError("not_found", "Resolution record was not found.")
    quality_claim = {
        "publicationStatus": outcome_summary.get("publicationStatus") if outcome_summary else None,
        "qualityClaimStatus": outcome_summary.get("qualityClaimStatus") if outcome_summary else None,
        "minimumCalibrationSampleSize": outcome_summary.get("minimumCalibrationSampleSize") if outcome_summary else None,
    }
    if outcome_summary:
        for key in [
            "resolvedComparableAutoEvidenceOutcomes",
            "resolvedComparablePipelineOutcomes",
            "resolvedComparableLiveOutcomes",
            "resolvedComparableSourceHandoffOutcomes",
        ]:
            if key in outcome_summary:
                quality_claim[key] = outcome_summary[key]
    return {
        "forecastId": forecast_id,
        "questionId": bundle_response["record"]["questionId"],
        "resolutionRecordId": resolution["resolutionRecordId"],
        "resolutionStatus": resolution["status"],
        "resolvedAt": resolution.get("resolvedAt"),
        "resolvedOutcome": resolution.get("resolvedOutcome"),
        "resolutionSource": resolution.get("resolutionSource"),
        "qualityClaim": quality_claim,
    }


def resolution_status_payload(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    card_response, _bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    payload = resolution_payload(forecast_id, question_id)
    return (
        payload,
        binding_from_card(card),
        state_from_card(card),
        ["Resolution is fixture-mode and should not be treated as a production live-source workflow."],
    )


def scoring_payload(forecast_id: str, question_id: str | None) -> dict[str, Any]:
    card_response, bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    scoring = bundle_response["record"]["records"]["scoringReport"]
    if scoring is None:
        raise AgentCallError("not_found", "Scoring report was not found.")
    return {
        "forecastId": forecast_id,
        "questionId": bundle_response["record"]["questionId"],
        "scoringReportId": scoring["scoringReportId"],
        "scoreStatus": scoring["scoreStatus"],
        "scoringRule": scoring["scoringRule"],
        "primaryScore": scoring.get("primaryScore"),
        "baselineScore": scoring.get("baselineScore"),
        "baselineLift": scoring.get("baselineLift"),
        "higherIsBetter": scoring.get("higherIsBetter"),
        "generatedAt": scoring["generatedAt"],
        "qualityClaim": card["qualityClaim"],
    }


def scoring_summary_payload(forecast_id: str, question_id: str | None) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    card_response, _bundle_response = read_card_and_bundle(forecast_id, question_id)
    card = card_response["record"]
    payload = scoring_payload(forecast_id, question_id)
    return (
        payload,
        binding_from_card(card),
        state_from_card(card),
        ["A single scored fixture outcome is not enough for a live calibration or quality claim."],
    )


def private_setup_bundle(request_id: str, bundle_case: str | None) -> dict[str, Any]:
    if bundle_case and bundle_case not in BAD_REQUEST_CASES:
        raise AgentCallError(
            "bad_request",
            "Private setup case must be unknown_source_kind or missing_approval.",
            binding=nullable_binding(requestId=request_id),
        )
    try:
        if bundle_case:
            return bundle_by_case(bundle_case)
        return bundle_by_request_id(request_id)
    except PrivateSetupAgentBundleError as exc:
        raise AgentCallError(
            "not_found",
            "Private setup agent bundle was not found.",
            binding=nullable_binding(requestId=request_id),
        ) from exc


def private_setup_bundle_payload(
    request_id: str,
    bundle_case: str | None,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    bundle = private_setup_bundle(request_id, bundle_case)
    request_summary = bundle["requestSummary"]
    action_summary = bundle["actionSummary"]
    source_policy = request_summary["sourcePolicy"]
    binding = nullable_binding(requestId=request_summary["privateSetupRequestId"])
    state = nullable_state(
        decisionStatus=action_summary["routeDecision"],
        approvalStatus=source_policy["approvalStatus"],
        dataMode=source_policy["dataMode"],
        planStatus=bundle["runtimeStatus"],
        sourceMode=bundle["sourceKind"],
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )
    warnings = [
        *bundle["warnings"],
        "The adapter envelope is read-only and does not execute the suggested setup command.",
    ]
    return bundle, binding, state, warnings


def private_setup_adapter_runbook_payload() -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    runbook = load_private_setup_adapter_runbook()
    source_path = runbook["sourcePath"]
    binding = nullable_binding(requestId=source_path["privateSetupRequestId"])
    state = state_from_private_setup_adapter_runbook(runbook)
    warnings = [
        *runbook["warnings"],
        "The adapter envelope is read-only and does not execute the operation sequence.",
    ]
    return runbook, binding, state, warnings


def private_setup_adapter_conformance_summary_payload() -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    summary = load_private_setup_adapter_conformance_summary()
    binding = nullable_binding(
        questionId=summary["bindings"]["generatedQuestionId"],
        forecastId=summary["bindings"]["generatedForecastId"],
    )
    state = state_from_private_setup_adapter_conformance_summary(summary)
    warnings = [
        *summary["warnings"],
        "The adapter envelope is read-only and does not execute adapter calls or create forecast artifacts.",
    ]
    return summary, binding, state, warnings


def private_source_adapter_guidance_payload() -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    guidance = build_private_source_adapter_guidance_payload()
    binding = nullable_binding()
    state = state_from_private_source_adapter_guidance(guidance)
    return guidance, binding, state, guidance["warnings"]


def selected_source_kind_payload(examples: dict[str, Any], source_kind: str) -> dict[str, Any]:
    rows = {item["sourceKind"]: item for item in examples["selectionExamples"]}
    if source_kind not in rows:
        raise AgentCallError(
            "bad_request",
            "Unsupported private source kind selection.",
            state=state_from_private_source_kind_selection(examples, source_kind),
        )
    return {
        "privateSourceKindSelectionExamplesId": examples["privateSourceKindSelectionExamplesId"],
        "generatedAt": examples["generatedAt"],
        "scope": examples["scope"],
        "runtimeStatus": "selected_example_only",
        "requestedSourceKind": source_kind,
        "availableSourceKinds": list(rows),
        "bindings": examples["bindings"],
        "selectedExample": rows[source_kind],
        "executionBoundary": examples["executionBoundary"],
        "warnings": [
            "This selected recommendation is read-only guidance and does not execute the recommended path.",
            "Forecast artifacts and scoring records still require explicit later gates.",
        ],
    }


def private_source_kind_selection_payload(
    source_kind: str | None,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    examples = load_private_source_kind_selection_examples()
    binding = nullable_binding()
    if source_kind:
        payload = selected_source_kind_payload(examples, source_kind)
        state = state_from_private_source_kind_selection(examples, source_kind)
        state["planStatus"] = payload["runtimeStatus"]
        warnings = [
            *payload["warnings"],
            "The adapter envelope is read-only and does not execute source setup, fixture evidence, forecast execution, or scoring.",
        ]
        return payload, binding, state, warnings

    state = state_from_private_source_kind_selection(examples)
    warnings = [
        *examples["warnings"],
        "The adapter envelope is read-only and does not execute source setup, fixture evidence, forecast execution, or scoring.",
    ]
    return examples, binding, state, warnings


def source_builder_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.source_builder_inputs and args.source_builder_case != "local_draft":
        raise AgentCallError(
            "bad_request",
            "Provide either --source-builder-case or explicit --source-builder-input values, not both.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        )
    try:
        return source_builder_result_payload(
            private_setup_request_id=args.private_setup_request_id,
            source_builder_case=args.source_builder_case,
            source_builder_inputs=args.source_builder_inputs,
            mapping_hints=args.source_builder_mapping_hints,
        )
    except SourceBuildError as exc:
        raise AgentCallError(
            "validation_failed",
            "Source-builder input could not be parsed or validated.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        ) from exc


def private_setup_source_builder_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    payload = source_builder_payload(args)
    return (
        payload,
        nullable_binding(requestId=payload["privateSetupRequestId"]),
        state_from_source_builder_payload(payload),
        payload["warnings"],
    )


def source_handoff_payload(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return source_handoff_result_payload(
            private_setup_request_id=args.private_setup_request_id,
            source_handoff_case=args.source_handoff_case,
        )
    except SourceIntakeHandoffError as exc:
        raise AgentCallError(
            "validation_failed",
            "Source-handoff case could not be parsed or validated.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        ) from exc


def private_setup_source_handoff_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    payload = source_handoff_payload(args)
    return (
        payload,
        nullable_binding(requestId=payload["privateSetupRequestId"]),
        state_from_source_handoff_payload(payload),
        payload["warnings"],
    )


def method_gate_payload(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return method_gate_result_payload(
            private_setup_request_id=args.private_setup_request_id,
            method_gate_case=args.method_gate_case,
        )
    except SourceHandoffMethodGateError as exc:
        raise AgentCallError(
            "validation_failed",
            "Method-gate case could not be parsed or validated.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        ) from exc


def private_setup_method_gate_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    payload = method_gate_payload(args)
    return (
        payload,
        nullable_binding(requestId=payload["privateSetupRequestId"]),
        state_from_method_gate_payload(payload),
        payload["warnings"],
    )


def forecast_execution_payload(args: argparse.Namespace) -> dict[str, Any]:
    try:
        return forecast_execution_result_payload(
            private_setup_request_id=args.private_setup_request_id,
            forecast_execution_case=args.forecast_execution_case,
        )
    except SourceHandoffForecastError as exc:
        raise AgentCallError(
            "validation_failed",
            "Forecast-execution case could not be parsed or validated.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        ) from exc
    except SourceHandoffMethodGateError as exc:
        raise AgentCallError(
            "validation_failed",
            "Forecast-execution method gate could not be parsed or validated.",
            binding=nullable_binding(requestId=args.private_setup_request_id),
        ) from exc


def private_setup_forecast_execution_payload(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    payload = forecast_execution_payload(args)
    run = payload["setupForecastRun"]
    return (
        payload,
        nullable_binding(
            requestId=payload["privateSetupRequestId"],
            questionId=run["recordBinding"]["questionId"],
            forecastId=run["recordBinding"]["forecastId"],
        ),
        state_from_forecast_execution_payload(payload),
        payload["warnings"],
    )


def resolution_jobs_payload() -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    registry = load_resolution_job_registry()
    return (
        registry,
        nullable_binding(),
        state_from_resolution_job_registry(registry),
        [
            *registry["warnings"],
            "The adapter envelope is read-only and cannot execute resolver commands.",
        ],
    )


def resolution_scheduler_status_adapter_payload() -> tuple[dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    payload = build_resolution_scheduler_status_payload(load_resolution_scheduler_run())
    return (
        payload,
        nullable_binding(),
        state_from_resolution_scheduler_status(payload),
        [
            *payload["warnings"],
            "The adapter envelope is read-only and cannot execute due jobs.",
        ],
    )


def operation_payload(args: argparse.Namespace) -> tuple[str, dict[str, Any], dict[str, str | None], dict[str, str | None], list[str]]:
    if args.operation == "forecast_request_validation":
        payload, binding, state, warnings = request_validation_payload(args.request)
        return payload["requestId"] or "forecastrequest-000", payload, binding, state, warnings
    if args.operation == "evidence_plan":
        payload, binding, state, warnings = evidence_plan_payload(args.request)
        return payload["evidencePlanId"], payload, binding, state, warnings
    if args.operation == "evidence_trace":
        payload, binding, state, warnings = evidence_trace_payload(args.forecast_id, args.question_id)
        return payload["recordId"], payload, binding, state, warnings
    if args.operation == "forecast_card":
        payload, binding, state, warnings = forecast_card_payload(args.forecast_id, args.question_id)
        return payload["recordId"], payload, binding, state, warnings
    if args.operation == "lifecycle_bundle":
        payload, binding, state, warnings = lifecycle_bundle_payload(args.forecast_id, args.question_id)
        return payload["recordId"], payload, binding, state, warnings
    if args.operation == "resolution_status":
        payload, binding, state, warnings = resolution_status_payload(args.forecast_id, args.question_id)
        return payload["resolutionRecordId"], payload, binding, state, warnings
    if args.operation == "scoring_summary":
        payload, binding, state, warnings = scoring_summary_payload(args.forecast_id, args.question_id)
        return payload["scoringReportId"], payload, binding, state, warnings
    if args.operation == "private_setup_bundle":
        payload, binding, state, warnings = private_setup_bundle_payload(args.private_setup_request_id, args.private_setup_case)
        return payload["privateSetupAgentBundleId"], payload, binding, state, warnings
    if args.operation == "private_setup_adapter_runbook":
        payload, binding, state, warnings = private_setup_adapter_runbook_payload()
        return payload["privateSetupAdapterChainRunbookId"], payload, binding, state, warnings
    if args.operation == "private_setup_adapter_conformance_summary":
        payload, binding, state, warnings = private_setup_adapter_conformance_summary_payload()
        return payload["privateSetupAdapterConformanceSummaryId"], payload, binding, state, warnings
    if args.operation == "private_source_adapter_guidance":
        payload, binding, state, warnings = private_source_adapter_guidance_payload()
        return payload["bindingSummary"]["privateSourceAdapterCapabilityId"], payload, binding, state, warnings
    if args.operation == "private_source_kind_selection":
        payload, binding, state, warnings = private_source_kind_selection_payload(args.source_kind)
        return payload["privateSourceKindSelectionExamplesId"], payload, binding, state, warnings
    if args.operation == "private_setup_source_builder":
        payload, binding, state, warnings = private_setup_source_builder_payload(args)
        return payload["sourceManifestBuild"]["sourceManifestBuildId"], payload, binding, state, warnings
    if args.operation == "private_setup_source_handoff":
        payload, binding, state, warnings = private_setup_source_handoff_payload(args)
        return payload["sourceIntakeHandoff"]["sourceIntakeHandoffId"], payload, binding, state, warnings
    if args.operation == "private_setup_method_gate":
        payload, binding, state, warnings = private_setup_method_gate_payload(args)
        return payload["sourceHandoffMethodGate"]["sourceHandoffMethodGateId"], payload, binding, state, warnings
    if args.operation == "private_setup_forecast_execution":
        payload, binding, state, warnings = private_setup_forecast_execution_payload(args)
        return payload["setupForecastRun"]["setupForecastRunId"], payload, binding, state, warnings
    if args.operation == "resolution_jobs":
        payload, binding, state, warnings = resolution_jobs_payload()
        return payload["resolutionJobRegistryId"], payload, binding, state, warnings
    if args.operation == "resolution_scheduler_status":
        payload, binding, state, warnings = resolution_scheduler_status_adapter_payload()
        return payload["resolutionSchedulerStatusId"], payload, binding, state, warnings
    raise AgentCallError("bad_request", "Unsupported agent operation.")


def sanitized_error(exc: Exception) -> tuple[str, str, bool]:
    if isinstance(exc, AgentCallError):
        return exc.code, exc.message, exc.retryable
    if isinstance(exc, PublicError):
        return exc.code, exc.message, False
    if isinstance(exc, EvidencePlanError):
        return "validation_failed", "Evidence plan could not be built for the request.", False
    return "internal_error", "Agent adapter operation failed.", False


def output_envelope(args: argparse.Namespace) -> dict[str, Any]:
    question_id = args.question_id if args.operation in FORECAST_BOUND_OPERATIONS else None
    forecast_id = args.forecast_id if args.operation in FORECAST_BOUND_OPERATIONS else None
    try:
        ensure_valid_adapter_request(args)
        input_ref, payload, binding, state, warnings = operation_payload(args)
        item = envelope(
            "agentenvelope-101",
            args.operation,
            CAPABILITY_BY_OPERATION[args.operation],
            INPUT_TYPE_BY_OPERATION[args.operation],
            input_ref,
            payload,
            question_id=question_id,
            forecast_id=forecast_id,
            caller_intent=safe_caller_intent(args.caller_intent),
            record_binding=binding,
            state=state,
            max_bytes=args.max_bytes,
            warnings=warnings,
        )
        validate_output(item, args.max_bytes)
        return item
    except Exception as exc:
        code, message, retryable = sanitized_error(exc)
        binding = exc.binding if isinstance(exc, AgentCallError) else nullable_binding(
            questionId=question_id,
            forecastId=forecast_id,
        )
        state = exc.state if isinstance(exc, AgentCallError) else nullable_state()
        item = envelope(
            "agentenvelope-101",
            args.operation,
            CAPABILITY_BY_OPERATION.get(args.operation, "read_only"),
            INPUT_TYPE_BY_OPERATION.get(args.operation, "forecast_card"),
            safe_input_ref(args),
            None,
            question_id=question_id,
            forecast_id=forecast_id,
            caller_intent=safe_caller_intent(args.caller_intent),
            record_binding=binding,
            state=state,
            max_bytes=safe_max_bytes(args.max_bytes),
            status="error",
            error={
                "code": code,
                "message": message,
                "retryable": retryable,
            },
            warnings=["Error payload is sanitized and does not expose raw diagnostics."],
        )
        validate_error_output(item)
        return item


def safe_input_ref(args: argparse.Namespace) -> str:
    if args.operation in FORECAST_BOUND_OPERATIONS:
        return args.forecast_id
    if args.operation == "private_setup_bundle":
        return args.private_setup_request_id
    if args.operation == "private_setup_adapter_runbook":
        return "privatesetupadapterchainrunbook-001"
    if args.operation == "private_setup_adapter_conformance_summary":
        return "privatesetupadapterconformancesummary-001"
    if args.operation == "private_source_adapter_guidance":
        return "privatesourceadaptercapability-001"
    if args.operation == "private_source_kind_selection":
        return "privatesourcekindselectionexamples-001"
    if args.operation == "private_setup_source_builder":
        return "sourcemanifestbuild-000"
    if args.operation == "private_setup_source_handoff":
        return "sourceintakehandoff-000"
    if args.operation == "private_setup_method_gate":
        return "sourcehandoffmethodgate-000"
    if args.operation == "private_setup_forecast_execution":
        return "setupforecastrun-000"
    if args.operation == "resolution_jobs":
        return "resolutionjobregistry-001"
    if args.operation == "resolution_scheduler_status":
        return "resolutionschedulerstatus-001"
    try:
        return input_ref_for(args)
    except Exception:
        return "forecastrequest-000"


def validate_output(item: dict[str, Any], max_bytes: int) -> None:
    output = render_json(item)
    if len(output.encode("utf-8")) > max_bytes:
        raise AgentCallError("response_too_large", "Agent adapter response exceeds configured size limit.")
    errors = validate_record(item, SCHEMA)
    if errors:
        raise AgentCallError("internal_error", "Agent adapter envelope validation failed.")
    try:
        validate_envelope_semantics(item)
    except AgentAdapterError as exc:
        raise AgentCallError("internal_error", "Agent adapter envelope binding validation failed.") from exc


def validate_error_output(item: dict[str, Any]) -> None:
    errors = validate_record(item, SCHEMA)
    if errors:
        raise AgentCallError("internal_error", "Agent adapter error envelope validation failed.")
    try:
        validate_envelope_semantics(item)
    except AgentAdapterError as exc:
        raise AgentCallError("internal_error", "Agent adapter error envelope binding validation failed.") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--operation",
        choices=sorted(CAPABILITY_BY_OPERATION),
        required=True,
    )
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--forecast-id", default=DEFAULT_FORECAST_ID)
    parser.add_argument("--question-id", default=DEFAULT_QUESTION_ID)
    parser.add_argument("--private-setup-request-id", default=DEFAULT_PRIVATE_SETUP_REQUEST_ID)
    parser.add_argument("--private-setup-case", choices=BAD_REQUEST_CASES)
    parser.add_argument("--source-builder-case", choices=SOURCE_BUILDER_CASES, default="local_draft")
    parser.add_argument("--source-builder-input", action="append", default=[], dest="source_builder_inputs")
    parser.add_argument("--source-builder-mapping-hint", action="append", default=[], dest="source_builder_mapping_hints")
    parser.add_argument("--source-kind")
    parser.add_argument("--source-handoff-case", choices=SOURCE_HANDOFF_CASES, default="unconfirmed_builder_draft")
    parser.add_argument("--method-gate-case", choices=METHOD_GATE_CASES, default="unconfirmed_builder_draft")
    parser.add_argument("--forecast-execution-case", choices=FORECAST_EXECUTION_CASES, default="unconfirmed_builder_draft")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--caller-intent", default=DEFAULT_CALLER_INTENT)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    item = output_envelope(args)
    sys.stdout.write(render_json(item))
    raise SystemExit(item["exitCode"])


if __name__ == "__main__":
    main()
