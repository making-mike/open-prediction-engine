#!/usr/bin/env python3
"""Build or check transport-neutral agent adapter envelope fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from read_ope_record import PublicError, read_record
from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-adapter"
SCHEMA = SPEC / "agent-envelope.schema.json"
GENERATED_AT = "2026-06-06T12:20:00Z"
FORECAST_ID = "forecast-602"
QUESTION_ID = "question-601"
MISSING_FORECAST_ID = "forecast-999"

OUTPUT_FILES = {
    "forecast_request_validation": "ope-agent-forecast-request-validation-envelope.generated.json",
    "evidence_plan": "ope-agent-evidence-plan-envelope.generated.json",
    "evidence_trace": "ope-agent-evidence-trace-envelope.generated.json",
    "forecast_card": "ope-agent-forecast-card-envelope.generated.json",
    "lifecycle_bundle": "ope-agent-lifecycle-bundle-envelope.generated.json",
    "resolution_status": "ope-agent-resolution-status-envelope.generated.json",
    "scoring_summary": "ope-agent-scoring-summary-envelope.generated.json",
    "forecast_card_error": "ope-agent-sanitized-error-envelope.generated.json",
}

EXIT_CODES = {
    "ok": 0,
    "bad_request": 2,
    "validation_failed": 2,
    "approval_required": 3,
    "not_found": 4,
    "access_denied": 4,
    "binding_mismatch": 4,
    "conflict": 4,
    "response_too_large": 5,
    "rate_limited": 5,
    "internal_error": 1,
}


class AgentAdapterError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def nullable_binding(**values: str | None) -> dict[str, str | None]:
    binding = {
        "requestId": None,
        "pipelineRunId": None,
        "questionId": None,
        "forecastId": None,
        "evidencePlanId": None,
        "evidenceSourceSetId": None,
        "sourcePolicyId": None,
        "resolutionRecordId": None,
        "scoringReportId": None,
    }
    binding.update(values)
    return binding


def nullable_state(**values: str | None) -> dict[str, str | None]:
    state = {
        "decisionStatus": None,
        "approvalStatus": None,
        "dataMode": None,
        "planStatus": None,
        "executionMode": None,
        "sourceMode": None,
        "forecastStatus": None,
        "resolutionStatus": None,
        "scoreStatus": None,
        "qualityClaimStatus": None,
    }
    state.update(values)
    return state


def adapter(capability_mode: str) -> dict[str, str]:
    return {
        "surface": "local_cli",
        "adapterVersion": "0.1.0",
        "transport": "stdio_process",
        "capabilityMode": capability_mode,
    }


def adapter_request(
    operation: str,
    input_record_type: str,
    input_ref: str,
    *,
    question_id: str | None = None,
    forecast_id: str | None = None,
    max_bytes: int | None = None,
    caller_intent: str,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "inputRecordType": input_record_type,
        "inputRef": input_ref,
        "questionId": question_id,
        "forecastId": forecast_id,
        "maxBytes": max_bytes,
        "callerIntent": caller_intent,
    }


def envelope(
    envelope_id: str,
    operation: str,
    capability_mode: str,
    input_record_type: str,
    input_ref: str,
    payload: dict[str, Any] | None,
    *,
    question_id: str | None = None,
    forecast_id: str | None = None,
    caller_intent: str,
    record_binding: dict[str, str | None],
    state: dict[str, str | None],
    max_bytes: int | None = 65536,
    status: str = "ok",
    error: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    exit_code = 0 if status == "ok" else EXIT_CODES.get(error["code"], 1) if error else 1
    return {
        "agentEnvelopeId": envelope_id,
        "generatedAt": GENERATED_AT,
        "adapter": adapter(capability_mode),
        "operation": operation,
        "adapterRequest": adapter_request(
            operation,
            input_record_type,
            input_ref,
            question_id=question_id,
            forecast_id=forecast_id,
            max_bytes=max_bytes,
            caller_intent=caller_intent,
        ),
        "recordBinding": record_binding,
        "state": state,
        "status": status,
        "exitCode": exit_code,
        "payload": payload,
        "error": error,
        "warnings": warnings or [],
    }


def expect_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AgentAdapterError(f"{label} mismatch")


def expect_optional_equal(label: str, actual: Any, expected: Any) -> None:
    if actual is not None and expected is not None and actual != expected:
        raise AgentAdapterError(f"{label} mismatch")


def validate_status_semantics(item: dict[str, Any]) -> None:
    status = item["status"]
    if status == "ok":
        expect_equal("ok envelope exit code", item["exitCode"], 0)
        if item["error"] is not None:
            raise AgentAdapterError("ok envelope must not include an error object")
        if not isinstance(item["payload"], dict):
            raise AgentAdapterError("ok envelope must include an object payload")
        return
    if item["exitCode"] == 0:
        raise AgentAdapterError("error envelope must use a nonzero exit code")
    if item["payload"] is not None:
        raise AgentAdapterError("error envelope must not include a success payload")
    if not isinstance(item["error"], dict):
        raise AgentAdapterError("error envelope must include an error object")


def validate_record_binding(item: dict[str, Any]) -> None:
    request = item["adapterRequest"]
    binding = item["recordBinding"]
    expect_equal("adapter operation", request["operation"], item["operation"])
    expect_optional_equal("adapter request question binding", request["questionId"], binding["questionId"])
    expect_optional_equal("adapter request forecast binding", request["forecastId"], binding["forecastId"])


def validate_payload_binding(item: dict[str, Any]) -> None:
    if item["status"] == "error":
        return

    operation = item["operation"]
    request = item["adapterRequest"]
    binding = item["recordBinding"]
    payload = item["payload"]

    if operation == "forecast_request_validation":
        expect_equal("request validation input ref", payload["requestId"], request["inputRef"])
        expect_equal("request validation request binding", payload["requestId"], binding["requestId"])
        expect_equal("request validation decision state", payload["decisionStatus"], item["state"]["decisionStatus"])
        expect_equal(
            "request validation source policy binding",
            payload["auditLog"]["sourcePolicyId"],
            binding["sourcePolicyId"],
        )
        return

    if operation == "evidence_plan":
        expect_equal("evidence plan input ref", payload["evidencePlanId"], request["inputRef"])
        expect_equal("evidence plan request binding", payload["requestId"], binding["requestId"])
        expect_equal("evidence plan id binding", payload["evidencePlanId"], binding["evidencePlanId"])
        expect_equal("evidence plan source policy binding", payload["sourcePolicy"]["sourcePolicyId"], binding["sourcePolicyId"])
        expect_equal("evidence plan state", payload["planStatus"], item["state"]["planStatus"])
        return

    if operation == "evidence_trace":
        response = payload
        trace = response["record"]
        trace_binding = trace["recordBinding"]
        expect_equal("evidence trace response record id", response["recordId"], request["inputRef"])
        expect_equal("evidence trace forecast binding", trace["forecastId"], binding["forecastId"])
        expect_equal("evidence trace question binding", trace["questionId"], binding["questionId"])
        expect_equal("evidence trace request binding", trace_binding["requestId"], binding["requestId"])
        expect_equal("evidence trace pipeline binding", trace_binding["pipelineRunId"], binding["pipelineRunId"])
        expect_equal("evidence trace evidence plan binding", trace_binding["evidencePlanId"], binding["evidencePlanId"])
        expect_equal(
            "evidence trace source-set binding",
            trace_binding["evidenceSourceSetId"],
            binding["evidenceSourceSetId"],
        )
        expect_equal("evidence trace source-policy binding", trace_binding["sourcePolicyId"], binding["sourcePolicyId"])
        expect_equal("evidence trace resolution binding", trace_binding["resolutionRecordId"], binding["resolutionRecordId"])
        expect_equal("evidence trace scoring binding", trace_binding["scoringReportId"], binding["scoringReportId"])
        return

    if operation in {"forecast_card", "lifecycle_bundle"}:
        response = payload
        record = response["record"]
        expect_equal(f"{operation} response record id", response["recordId"], request["inputRef"])
        expect_equal(f"{operation} forecast binding", record["forecastId"], binding["forecastId"])
        expect_equal(f"{operation} question binding", record["questionId"], binding["questionId"])
        if operation == "forecast_card":
            request_binding = record["requestBinding"]
            links = record["links"]
            expect_equal("forecast card request binding", request_binding["requestId"], binding["requestId"])
            expect_equal("forecast card pipeline binding", request_binding["pipelineRunId"], binding["pipelineRunId"])
            expect_equal("forecast card evidence plan binding", request_binding["evidencePlanId"], binding["evidencePlanId"])
            expect_equal(
                "forecast card evidence source-set binding",
                request_binding["evidenceSourceSetId"],
                binding["evidenceSourceSetId"],
            )
            expect_equal("forecast card source policy binding", request_binding["sourcePolicyId"], binding["sourcePolicyId"])
            expect_equal("forecast card resolution binding", links["resolutionRecord"], binding["resolutionRecordId"])
            expect_equal("forecast card scoring binding", links["scoringReport"], binding["scoringReportId"])
        else:
            included = record["includedRecords"]
            expect_equal("bundle resolution binding", included["resolutionRecord"], binding["resolutionRecordId"])
            expect_equal("bundle scoring binding", included["scoringReport"], binding["scoringReportId"])
            expect_equal("bundle pipeline binding", included["pipelineRun"], binding["pipelineRunId"])
        return

    if operation == "resolution_status":
        expect_equal("resolution status input ref", payload["resolutionRecordId"], request["inputRef"])
        expect_equal("resolution status forecast binding", payload["forecastId"], binding["forecastId"])
        expect_equal("resolution status question binding", payload["questionId"], binding["questionId"])
        expect_equal("resolution status record binding", payload["resolutionRecordId"], binding["resolutionRecordId"])
        expect_equal("resolution status state", payload["resolutionStatus"], item["state"]["resolutionStatus"])
        return

    if operation == "scoring_summary":
        expect_equal("scoring summary input ref", payload["scoringReportId"], request["inputRef"])
        expect_equal("scoring summary forecast binding", payload["forecastId"], binding["forecastId"])
        expect_equal("scoring summary question binding", payload["questionId"], binding["questionId"])
        expect_equal("scoring summary record binding", payload["scoringReportId"], binding["scoringReportId"])
        expect_equal("scoring summary state", payload["scoreStatus"], item["state"]["scoreStatus"])


def validate_envelope_semantics(item: dict[str, Any]) -> None:
    validate_status_semantics(item)
    validate_record_binding(item)
    validate_payload_binding(item)


def binding_from_card(card: dict[str, Any]) -> dict[str, str | None]:
    request_binding = card["requestBinding"]
    links = card["links"]
    return nullable_binding(
        requestId=request_binding["requestId"],
        pipelineRunId=request_binding["pipelineRunId"],
        questionId=card["questionId"],
        forecastId=card["forecastId"],
        evidencePlanId=request_binding["evidencePlanId"],
        evidenceSourceSetId=request_binding["evidenceSourceSetId"],
        sourcePolicyId=request_binding["sourcePolicyId"],
        resolutionRecordId=links["resolutionRecord"],
        scoringReportId=links["scoringReport"],
    )


def binding_from_trace(trace: dict[str, Any], card: dict[str, Any]) -> dict[str, str | None]:
    trace_binding = trace["recordBinding"]
    card_binding = binding_from_card(card)
    return nullable_binding(
        requestId=trace_binding["requestId"],
        pipelineRunId=trace_binding["pipelineRunId"],
        questionId=trace_binding["questionId"],
        forecastId=trace_binding["forecastId"],
        evidencePlanId=trace_binding["evidencePlanId"],
        evidenceSourceSetId=trace_binding["evidenceSourceSetId"],
        sourcePolicyId=trace_binding["sourcePolicyId"],
        resolutionRecordId=card_binding["resolutionRecordId"],
        scoringReportId=card_binding["scoringReportId"],
    )


def state_from_card(card: dict[str, Any]) -> dict[str, str | None]:
    request_binding = card["requestBinding"]
    return nullable_state(
        decisionStatus="accepted",
        approvalStatus="approved",
        dataMode="auto",
        executionMode=request_binding["executionMode"],
        sourceMode=request_binding["sourceMode"],
        forecastStatus=card["status"],
        resolutionStatus=card["resolution"]["status"],
        scoreStatus=card["score"]["scoreStatus"] if card["score"] else None,
        qualityClaimStatus=card["qualityClaim"]["status"],
    )


def build_request_validation_envelope() -> dict[str, Any]:
    request = load_json(DEFAULT_REQUEST)
    decision = validate_request(request)
    return envelope(
        "agentenvelope-001",
        "forecast_request_validation",
        "validation",
        "forecast_request",
        request["requestId"],
        decision,
        caller_intent="Validate an agent-submitted forecast request without executing it.",
        record_binding=nullable_binding(
            requestId=request["requestId"],
            sourcePolicyId=request["sourcePolicy"]["sourcePolicyId"],
        ),
        state=nullable_state(
            decisionStatus=decision["decisionStatus"],
            approvalStatus=request["approval"]["status"],
            dataMode=request["dataMode"],
        ),
        warnings=[
            "Validation does not execute forecast generation or live evidence fetching.",
        ],
    )


def build_evidence_plan_envelope() -> dict[str, Any]:
    plan = build_plan(DEFAULT_REQUEST)
    return envelope(
        "agentenvelope-002",
        "evidence_plan",
        "dry_run_generation",
        "evidence_gathering_plan",
        plan["evidencePlanId"],
        plan,
        caller_intent="Inspect the dry-run evidence plan before any live source gathering.",
        record_binding=nullable_binding(
            requestId=plan["requestId"],
            evidencePlanId=plan["evidencePlanId"],
            sourcePolicyId=plan["sourcePolicy"]["sourcePolicyId"],
        ),
        state=nullable_state(
            decisionStatus="accepted",
            approvalStatus="approved",
            dataMode=plan["dataMode"],
            planStatus=plan["planStatus"],
            executionMode=plan["executionMode"],
        ),
        warnings=plan["warnings"],
    )


def build_card_and_bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    card_response = read_record("forecast-card", FORECAST_ID, QUESTION_ID)
    bundle_response = read_record("forecast-bundle", FORECAST_ID, QUESTION_ID)
    return card_response, bundle_response


def build_forecast_card_envelope(card_response: dict[str, Any]) -> dict[str, Any]:
    card = card_response["record"]
    return envelope(
        "agentenvelope-003",
        "forecast_card",
        "read_only",
        "forecast_card",
        card["forecastId"],
        card_response,
        question_id=card["questionId"],
        forecast_id=card["forecastId"],
        caller_intent="Read a compact claim-safe forecast card before deciding whether to act.",
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=card["warnings"],
    )


def build_evidence_trace_envelope(
    card_response: dict[str, Any],
    trace_response: dict[str, Any],
) -> dict[str, Any]:
    card = card_response["record"]
    trace = trace_response["record"]
    return envelope(
        "agentenvelope-004",
        "evidence_trace",
        "read_only",
        "evidence_trace",
        trace["forecastId"],
        trace_response,
        question_id=trace["questionId"],
        forecast_id=trace["forecastId"],
        caller_intent="Inspect connector-bound evidence provenance without reading raw fixtures.",
        record_binding=binding_from_trace(trace, card),
        state=state_from_card(card),
        warnings=trace["warnings"],
    )


def build_lifecycle_bundle_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
) -> dict[str, Any]:
    card = card_response["record"]
    bundle = bundle_response["record"]
    return envelope(
        "agentenvelope-005",
        "lifecycle_bundle",
        "read_only",
        "lifecycle_bundle",
        bundle["forecastId"],
        bundle_response,
        question_id=bundle["questionId"],
        forecast_id=bundle["forecastId"],
        caller_intent="Inspect the bound lifecycle bundle for provenance and audit context.",
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "Bundle read is local and read-only; it does not mutate forecast lifecycle records.",
            "Full bundles are larger than forecast cards and may include detailed provenance records.",
        ],
    )


def build_resolution_status_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
) -> dict[str, Any]:
    card = card_response["record"]
    records = bundle_response["record"]["records"]
    resolution = records["resolutionRecord"]
    outcome_summary = records["outcomeSummary"]
    payload = {
        "forecastId": FORECAST_ID,
        "questionId": QUESTION_ID,
        "resolutionRecordId": resolution["resolutionRecordId"],
        "resolutionStatus": resolution["status"],
        "resolvedAt": resolution["resolvedAt"],
        "resolvedOutcome": resolution["resolvedOutcome"],
        "resolutionSource": resolution["resolutionSource"],
        "qualityClaim": {
            "publicationStatus": outcome_summary["publicationStatus"],
            "qualityClaimStatus": outcome_summary["qualityClaimStatus"],
            "minimumCalibrationSampleSize": outcome_summary["minimumCalibrationSampleSize"],
            "resolvedComparableAutoEvidenceOutcomes": outcome_summary[
                "resolvedComparableAutoEvidenceOutcomes"
            ],
        },
    }
    return envelope(
        "agentenvelope-006",
        "resolution_status",
        "resolution_check",
        "resolution_status",
        resolution["resolutionRecordId"],
        payload,
        question_id=QUESTION_ID,
        forecast_id=FORECAST_ID,
        caller_intent="Check whether the forecast is resolved, ambiguous, annulled, or still pending.",
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "Resolution is fixture-mode and should not be treated as a production live-source workflow.",
        ],
    )


def build_scoring_summary_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
) -> dict[str, Any]:
    card = card_response["record"]
    records = bundle_response["record"]["records"]
    scoring = records["scoringReport"]
    payload = {
        "forecastId": FORECAST_ID,
        "questionId": QUESTION_ID,
        "scoringReportId": scoring["scoringReportId"],
        "scoreStatus": scoring["scoreStatus"],
        "scoringRule": scoring["scoringRule"],
        "primaryScore": scoring["primaryScore"],
        "baselineScore": scoring["baselineScore"],
        "baselineLift": scoring["baselineLift"],
        "higherIsBetter": scoring["higherIsBetter"],
        "generatedAt": scoring["generatedAt"],
        "qualityClaim": card["qualityClaim"],
    }
    return envelope(
        "agentenvelope-007",
        "scoring_summary",
        "scoring_read",
        "scoring_summary",
        scoring["scoringReportId"],
        payload,
        question_id=QUESTION_ID,
        forecast_id=FORECAST_ID,
        caller_intent="Read the score summary and baseline comparison before making a quality claim.",
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "A single scored fixture outcome is not enough for a live calibration or quality claim.",
        ],
    )


def build_error_envelope() -> dict[str, Any]:
    try:
        read_record("forecast-card", MISSING_FORECAST_ID, QUESTION_ID)
    except PublicError as exc:
        return envelope(
            "agentenvelope-008",
            "forecast_card",
            "read_only",
            "forecast_card",
            MISSING_FORECAST_ID,
            None,
            question_id=QUESTION_ID,
            forecast_id=MISSING_FORECAST_ID,
            caller_intent="Read a forecast card that does not exist to demonstrate sanitized errors.",
            record_binding=nullable_binding(questionId=QUESTION_ID, forecastId=MISSING_FORECAST_ID),
            state=nullable_state(),
            status="error",
            error={
                "code": exc.code,
                "message": exc.message,
                "retryable": False,
            },
            warnings=[
                "Error payloads are sanitized and must not expose local absolute paths or raw diagnostics.",
            ],
        )
    raise AgentAdapterError("missing-record read unexpectedly succeeded")


def build_envelopes() -> dict[str, dict[str, Any]]:
    card_response, bundle_response = build_card_and_bundle()
    trace_response = read_record("evidence-trace", FORECAST_ID, QUESTION_ID)
    envelopes = {
        OUTPUT_FILES["forecast_request_validation"]: build_request_validation_envelope(),
        OUTPUT_FILES["evidence_plan"]: build_evidence_plan_envelope(),
        OUTPUT_FILES["forecast_card"]: build_forecast_card_envelope(card_response),
        OUTPUT_FILES["evidence_trace"]: build_evidence_trace_envelope(card_response, trace_response),
        OUTPUT_FILES["lifecycle_bundle"]: build_lifecycle_bundle_envelope(card_response, bundle_response),
        OUTPUT_FILES["resolution_status"]: build_resolution_status_envelope(card_response, bundle_response),
        OUTPUT_FILES["scoring_summary"]: build_scoring_summary_envelope(card_response, bundle_response),
        OUTPUT_FILES["forecast_card_error"]: build_error_envelope(),
    }
    for filename, item in envelopes.items():
        errors = validate_record(item, SCHEMA)
        if errors:
            raise AgentAdapterError(f"{filename} schema validation failed: {errors[0]}")
        try:
            validate_envelope_semantics(item)
        except AgentAdapterError as exc:
            raise AgentAdapterError(f"{filename} semantic validation failed: {exc}") from exc
    return envelopes


def write_envelopes(envelopes: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for filename, item in envelopes.items():
        (GENERATED / filename).write_text(render_json(item), encoding="utf-8")
    print(f"generated {len(envelopes)} agent adapter envelopes")


def check_envelopes(envelopes: dict[str, dict[str, Any]]) -> None:
    for filename, item in envelopes.items():
        path = GENERATED / filename
        if not path.exists():
            print(f"missing agent adapter envelope: {path}", file=sys.stderr)
            print("run `python3 scripts/build_agent_adapter_fixtures.py --write`", file=sys.stderr)
            raise SystemExit(1)
        expected = render_json(item)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"agent adapter envelope drift: {path}", file=sys.stderr)
            print("run `python3 scripts/build_agent_adapter_fixtures.py --write`", file=sys.stderr)
            raise SystemExit(1)
    print(f"checked {len(envelopes)} agent adapter envelopes")


def envelope_collection(envelopes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "agentEnvelopeSetId": "agentenvelopeset-001",
        "generatedAt": GENERATED_AT,
        "count": len(envelopes),
        "envelopes": list(envelopes.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated agent-envelope drift")
    parser.add_argument("--write", action="store_true", help="write generated agent-envelope fixtures")
    args = parser.parse_args()
    try:
        envelopes = build_envelopes()
    except (AgentAdapterError, PublicError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_envelopes(envelopes)
    elif args.check:
        check_envelopes(envelopes)
    else:
        sys.stdout.write(render_json(envelope_collection(envelopes)))


if __name__ == "__main__":
    main()
