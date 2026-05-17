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
    binding_from_card,
    binding_from_trace,
    envelope,
    nullable_binding,
    nullable_state,
    render_json,
    state_from_card,
    validate_envelope_semantics,
)
from ope_schema import validate_record
from plan_auto_evidence import DEFAULT_REQUEST, EvidencePlanError, build_plan
from read_ope_record import DEFAULT_MAX_BYTES, PublicError, read_record
from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORECAST_ID = "forecast-602"
DEFAULT_QUESTION_ID = "question-601"
DEFAULT_CALLER_INTENT = "Call one local OPE agent adapter operation."
CAPABILITY_BY_OPERATION = {
    "forecast_request_validation": "validation",
    "evidence_plan": "dry_run_generation",
    "evidence_trace": "read_only",
    "forecast_card": "read_only",
    "lifecycle_bundle": "read_only",
    "resolution_status": "resolution_check",
    "scoring_summary": "scoring_read",
}
INPUT_TYPE_BY_OPERATION = {
    "forecast_request_validation": "forecast_request",
    "evidence_plan": "evidence_gathering_plan",
    "evidence_trace": "evidence_trace",
    "forecast_card": "forecast_card",
    "lifecycle_bundle": "lifecycle_bundle",
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
    raise AgentCallError("bad_request", "Unsupported agent operation.")


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
    return {
        "forecastId": forecast_id,
        "questionId": bundle_response["record"]["questionId"],
        "resolutionRecordId": resolution["resolutionRecordId"],
        "resolutionStatus": resolution["status"],
        "resolvedAt": resolution.get("resolvedAt"),
        "resolvedOutcome": resolution.get("resolvedOutcome"),
        "resolutionSource": resolution.get("resolutionSource"),
        "qualityClaim": {
            "publicationStatus": outcome_summary.get("publicationStatus") if outcome_summary else None,
            "qualityClaimStatus": outcome_summary.get("qualityClaimStatus") if outcome_summary else None,
            "minimumCalibrationSampleSize": outcome_summary.get("minimumCalibrationSampleSize") if outcome_summary else None,
            "resolvedComparableAutoEvidenceOutcomes": outcome_summary.get("resolvedComparableAutoEvidenceOutcomes")
            if outcome_summary
            else None,
        },
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
            caller_intent=args.caller_intent,
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
            caller_intent=args.caller_intent,
            record_binding=binding,
            state=state,
            max_bytes=args.max_bytes,
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
