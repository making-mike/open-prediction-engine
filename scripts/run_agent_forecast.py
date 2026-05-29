#!/usr/bin/env python3
"""Build or check an agent-facing forecast run summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from gather_auto_evidence import EvidenceGatheringError, build_source_set
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, EvidencePlanError, build_plan
from read_ope_record import PublicError, read_record
from resolve_auto_evidence_outcome import build_outputs as build_resolution_outputs
from run_auto_evidence_forecast import AutoEvidenceForecastError, build_outputs as build_forecast_outputs
from run_historical_baseline_forecast import (
    HistoricalBaselineError,
    build_outputs as build_historical_outputs,
)
from select_forecasting_method import MethodSelectionError, build_selection
from validate_forecast_request import load_json, validate_request
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "forecast-run"
SUMMARY_PATH = GENERATED / "weather-logistics-agent-forecast-run.generated.json"
SCHEMA = SPEC / "forecast-run-summary.schema.json"
GENERATED_AT = "2026-06-06T13:05:00Z"
DEFAULT_FORECAST_RUN_ID = "forecastrun-001"
HISTORICAL_REQUEST_ID = "forecastrequest-008"


class ForecastRunError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def nullable_binding(**values: str | None) -> dict[str, str | None]:
    binding = {
        "requestId": None,
        "sourcePolicyId": None,
        "evidencePlanId": None,
        "evidenceSourceSetId": None,
        "methodSelectionId": None,
        "pipelineRunId": None,
        "questionId": None,
        "forecastId": None,
        "forecastCardId": None,
        "forecastBundleId": None,
        "resolutionRecordId": None,
        "scoringReportId": None,
    }
    binding.update(values)
    return binding


def empty_state(**values: str | None) -> dict[str, str | None]:
    state = {
        "planStatus": None,
        "gatheringStatus": None,
        "forecastStatus": None,
        "resolutionStatus": None,
        "scoreStatus": None,
        "qualityClaimStatus": None,
    }
    state.update(values)
    return state


def empty_outputs() -> dict[str, None]:
    return {
        "forecastCard": None,
        "evidenceTrace": None,
        "lifecycleBundle": None,
        "resolutionStatus": None,
        "scoringSummary": None,
    }


def safe_request_summary(request_path: Path, request: Any, decision: dict[str, Any] | None = None) -> dict[str, str | None]:
    data = request if isinstance(request, dict) else {}
    audit = decision.get("auditLog", {}) if decision else {}
    return {
        "requestId": audit.get("requestId") if isinstance(audit.get("requestId"), str) else data.get("requestId"),
        "requestPath": rel(request_path),
        "requestedAction": data.get("requestedAction"),
        "dataMode": data.get("dataMode"),
        "domain": data.get("domain"),
        "geography": data.get("geography"),
        "serviceDate": data.get("serviceDate"),
        "horizonLabel": data.get("horizonLabel"),
    }


def controls(request_validated: bool, *, execution_started: bool) -> dict[str, bool]:
    return {
        "requestValidated": request_validated,
        "networkAccess": False,
        "liveFetch": False,
        "effectfulGeneration": False,
        "paidAction": False,
        "privateSourceAccess": False,
    }


def failure_summary(
    request_path: Path,
    request: Any,
    decision: dict[str, Any] | None,
    *,
    summary_id: str = DEFAULT_FORECAST_RUN_ID,
    run_status: str,
    error_code: str,
    message: str,
    retryable: bool = False,
) -> dict[str, Any]:
    audit = decision.get("auditLog", {}) if decision else {}
    decision_status = decision["decisionStatus"] if decision else "rejected"
    summary = {
        "forecastRunSummaryId": summary_id,
        "generatedAt": GENERATED_AT,
        "request": safe_request_summary(request_path, request, decision),
        "runStatus": run_status,
        "decisionStatus": decision_status,
        "executionMode": "not_started",
        "sourceMode": "none",
        "controls": controls(decision is not None, execution_started=False),
        "recordBinding": nullable_binding(
            requestId=audit.get("requestId") if isinstance(audit.get("requestId"), str) else None,
            sourcePolicyId=audit.get("sourcePolicyId") if isinstance(audit.get("sourcePolicyId"), str) else None,
        ),
        "state": empty_state(),
        "outputs": empty_outputs(),
        "forecast": None,
        "qualityClaim": None,
        "error": {
            "code": error_code,
            "message": message,
            "retryable": retryable,
        },
        "warnings": [
            "No forecast outputs were generated for this run.",
            "Failure summary is sanitized and does not expose raw diagnostics.",
        ],
    }
    validate_summary(summary)
    return summary


def decision_failure_summary(
    request_path: Path,
    request: Any,
    decision: dict[str, Any],
    *,
    summary_id: str = DEFAULT_FORECAST_RUN_ID,
) -> dict[str, Any]:
    status = decision["decisionStatus"]
    code = decision["reasonCodes"][0] if decision["reasonCodes"] else status
    message = decision["reasons"][0]["message"] if decision["reasons"] else "Forecast request was not accepted."
    if status == "blocked":
        run_status = "blocked"
        code = "approval_required"
    elif status == "canceled":
        run_status = "canceled"
        code = "canceled"
    else:
        run_status = "rejected"
    return failure_summary(
        request_path,
        request,
        decision,
        summary_id=summary_id,
        run_status=run_status,
        error_code=code,
        message=message,
    )


def assert_default_fixture_path(request: dict[str, Any]) -> None:
    if request.get("requestId") != "forecastrequest-007":
        raise ForecastRunError(
            "unsupported_fixture_path",
            "The local forecast-run orchestrator currently supports the checked auto-evidence fixture request.",
        )
    if request.get("requestedAction") != "generate_forecast" or request.get("dataMode") != "auto":
        raise ForecastRunError(
            "unsupported_fixture_path",
            "The local forecast-run orchestrator requires generate_forecast with dataMode auto.",
        )


def assert_historical_fixture_path(request: dict[str, Any]) -> None:
    if request.get("requestId") != HISTORICAL_REQUEST_ID:
        raise ForecastRunError(
            "unsupported_fixture_path",
            "The local forecast-run orchestrator currently supports the checked auto-evidence and historical-only fixture requests.",
        )
    if request.get("requestedAction") != "generate_forecast" or request.get("dataMode") != "provided":
        raise ForecastRunError(
            "unsupported_fixture_path",
            "The historical fixture path requires generate_forecast with dataMode provided.",
        )


def output_ref(operation: str, record_type: str, record_id: str, question_id: str) -> dict[str, str]:
    return {
        "operation": operation,
        "recordType": record_type,
        "recordId": record_id,
        "questionId": question_id,
    }


def completed_summary(
    request_path: Path,
    request: dict[str, Any],
    decision: dict[str, Any],
    *,
    summary_id: str = DEFAULT_FORECAST_RUN_ID,
) -> dict[str, Any]:
    assert_default_fixture_path(request)
    plan = build_plan(request_path)
    source_set = build_source_set(request_path)
    method_selection = build_selection(request_path)
    forecast_outputs = build_forecast_outputs(request_path)
    resolution_outputs = build_resolution_outputs()

    pipeline_run = forecast_outputs["weather-logistics-auto-evidence-pipeline-run.generated.json"]
    artifact = forecast_outputs["weather-logistics-auto-evidence-artifact.generated.json"]
    question = forecast_outputs["weather-logistics-auto-evidence-question.generated.json"]
    resolution = resolution_outputs["weather-logistics-auto-evidence-resolution-resolution.generated.json"]
    scoring = resolution_outputs["weather-logistics-auto-evidence-resolution-scoring.generated.json"]
    outcome_summary = resolution_outputs["weather-logistics-auto-evidence-resolution-outcome-summary.generated.json"]

    forecast_id = artifact["forecastId"]
    question_id = question["questionId"]
    card_response = read_record("forecast-card", forecast_id, question_id)
    bundle_response = read_record("forecast-bundle", forecast_id, question_id)
    card = card_response["record"]
    bundle = bundle_response["record"]

    summary = {
        "forecastRunSummaryId": summary_id,
        "generatedAt": GENERATED_AT,
        "request": safe_request_summary(request_path, request, decision),
        "runStatus": "completed",
        "decisionStatus": decision["decisionStatus"],
        "executionMode": pipeline_run["executionMode"],
        "sourceMode": pipeline_run["controls"]["sourceMode"],
        "controls": controls(True, execution_started=True),
        "recordBinding": nullable_binding(
            requestId=decision["requestId"],
            sourcePolicyId=plan["sourcePolicy"]["sourcePolicyId"],
            evidencePlanId=plan["evidencePlanId"],
            evidenceSourceSetId=source_set["evidenceSourceSetId"],
            methodSelectionId=method_selection["methodSelectionId"],
            pipelineRunId=pipeline_run["pipelineRunId"],
            questionId=question_id,
            forecastId=forecast_id,
            forecastCardId=card["cardId"],
            forecastBundleId=bundle["bundleId"],
            resolutionRecordId=resolution["resolutionRecordId"],
            scoringReportId=scoring["scoringReportId"],
        ),
        "state": empty_state(
            planStatus=plan["planStatus"],
            gatheringStatus=source_set["executionMode"],
            forecastStatus=card["status"],
            resolutionStatus=resolution["status"],
            scoreStatus=scoring["scoreStatus"],
            qualityClaimStatus=outcome_summary["qualityClaimStatus"],
        ),
        "outputs": {
            "forecastCard": output_ref("forecast_card", "forecast-card", forecast_id, question_id),
            "evidenceTrace": output_ref("evidence_trace", "evidence-trace", forecast_id, question_id),
            "lifecycleBundle": output_ref("lifecycle_bundle", "forecast-bundle", forecast_id, question_id),
            "resolutionStatus": output_ref(
                "resolution_status",
                "resolution-record",
                resolution["resolutionRecordId"],
                question_id,
            ),
            "scoringSummary": output_ref(
                "scoring_summary",
                "scoring-report",
                scoring["scoringReportId"],
                question_id,
            ),
        },
        "forecast": {
            "forecastedAt": card["forecastedAt"],
            "modelId": card["model"]["modelId"],
            "modelVersion": card["model"]["version"],
            "probability": card["forecast"]["probability"],
            "baselineProbability": card["baseline"]["probability"],
        },
        "qualityClaim": card["qualityClaim"],
        "error": None,
        "warnings": [
            "Fixture-mode run only; no live source was fetched.",
            "Forecast quality remains provisional until enough comparable outcomes resolve.",
            "Use forecastCard for compact action context, evidenceTrace for source provenance, and lifecycleBundle for audit context.",
        ],
    }
    validate_completed_bindings(summary, plan, source_set, method_selection, pipeline_run, card, bundle, resolution, scoring)
    validate_summary(summary)
    return summary


def historical_completed_summary(
    request_path: Path,
    request: dict[str, Any],
    decision: dict[str, Any],
    *,
    summary_id: str = DEFAULT_FORECAST_RUN_ID,
) -> dict[str, Any]:
    assert_historical_fixture_path(request)
    forecast_outputs = build_historical_outputs(request_path)

    prefix = "weather-logistics-historical-baseline"
    pipeline_run = forecast_outputs[f"{prefix}-pipeline-run.generated.json"]
    artifact = forecast_outputs[f"{prefix}-artifact.generated.json"]
    question = forecast_outputs[f"{prefix}-question.generated.json"]

    forecast_id = artifact["forecastId"]
    question_id = question["questionId"]
    card_response = read_record("forecast-card", forecast_id, question_id)
    bundle_response = read_record("forecast-bundle", forecast_id, question_id)
    card = card_response["record"]
    bundle = bundle_response["record"]

    summary = {
        "forecastRunSummaryId": summary_id,
        "generatedAt": GENERATED_AT,
        "request": safe_request_summary(request_path, request, decision),
        "runStatus": "completed",
        "decisionStatus": decision["decisionStatus"],
        "executionMode": pipeline_run["executionMode"],
        "sourceMode": pipeline_run["controls"]["sourceMode"],
        "controls": controls(True, execution_started=True),
        "recordBinding": nullable_binding(
            requestId=decision["requestId"],
            sourcePolicyId=request["sourcePolicy"]["sourcePolicyId"],
            pipelineRunId=pipeline_run["pipelineRunId"],
            questionId=question_id,
            forecastId=forecast_id,
            forecastCardId=card["cardId"],
            forecastBundleId=bundle["bundleId"],
        ),
        "state": empty_state(
            gatheringStatus="provided_fixture",
            forecastStatus=card["status"],
            qualityClaimStatus="unresolved",
        ),
        "outputs": {
            "forecastCard": output_ref("forecast_card", "forecast-card", forecast_id, question_id),
            "evidenceTrace": None,
            "lifecycleBundle": output_ref("lifecycle_bundle", "forecast-bundle", forecast_id, question_id),
            "resolutionStatus": None,
            "scoringSummary": None,
        },
        "forecast": {
            "forecastedAt": card["forecastedAt"],
            "modelId": card["model"]["modelId"],
            "modelVersion": card["model"]["version"],
            "probability": card["forecast"]["probability"],
            "baselineProbability": card["baseline"]["probability"],
        },
        "qualityClaim": None,
        "error": None,
        "warnings": [
            "Historical-only fixture run; no weather API, auto-evidence connector, or live source was used.",
            "Forecast output equals the historical-frequency baseline and should not be treated as a day-specific weather-adjusted model forecast.",
            "Resolution and scoring are not generated for this historical-only fixture run.",
        ],
    }
    validate_historical_bindings(summary, request, pipeline_run, card, bundle)
    validate_summary(summary)
    return summary


def validate_completed_bindings(
    summary: dict[str, Any],
    plan: dict[str, Any],
    source_set: dict[str, Any],
    method_selection: dict[str, Any],
    pipeline_run: dict[str, Any],
    card: dict[str, Any],
    bundle: dict[str, Any],
    resolution: dict[str, Any],
    scoring: dict[str, Any],
) -> None:
    binding = summary["recordBinding"]
    if binding["requestId"] != plan["requestId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost request/evidence-plan binding.")
    if binding["sourcePolicyId"] != source_set["sourcePolicyId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost source-policy binding.")
    if binding["methodSelectionId"] != method_selection["methodSelectionId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost method-selection binding.")
    if binding["pipelineRunId"] != pipeline_run["pipelineRunId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost pipeline-run binding.")
    if binding["forecastId"] != card["forecastId"] or binding["forecastId"] != bundle["forecastId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost forecast binding.")
    if binding["questionId"] != card["questionId"] or binding["questionId"] != bundle["questionId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost question binding.")
    if binding["resolutionRecordId"] != resolution["resolutionRecordId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost resolution binding.")
    if binding["scoringReportId"] != scoring["scoringReportId"]:
        raise ForecastRunError("binding_mismatch", "Forecast run lost scoring binding.")
    if any(summary["controls"][key] for key in ["networkAccess", "liveFetch", "effectfulGeneration", "paidAction", "privateSourceAccess"]):
        raise ForecastRunError("unsafe_run", "Forecast run summary overstated safe fixture controls.")


def validate_historical_bindings(
    summary: dict[str, Any],
    request: dict[str, Any],
    pipeline_run: dict[str, Any],
    card: dict[str, Any],
    bundle: dict[str, Any],
) -> None:
    binding = summary["recordBinding"]
    if binding["requestId"] != request["requestId"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run lost request binding.")
    if binding["sourcePolicyId"] != request["sourcePolicy"]["sourcePolicyId"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run lost source-policy binding.")
    if binding["pipelineRunId"] != pipeline_run["pipelineRunId"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run lost pipeline-run binding.")
    if binding["forecastId"] != card["forecastId"] or binding["forecastId"] != bundle["forecastId"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run lost forecast binding.")
    if binding["questionId"] != card["questionId"] or binding["questionId"] != bundle["questionId"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run lost question binding.")
    for key in ["evidencePlanId", "evidenceSourceSetId", "methodSelectionId", "resolutionRecordId", "scoringReportId"]:
        if binding[key] is not None:
            raise ForecastRunError("binding_mismatch", "Historical forecast run should not bind unavailable records.")
    if summary["outputs"]["evidenceTrace"] is not None:
        raise ForecastRunError("binding_mismatch", "Historical forecast run should not expose an evidence trace.")
    if summary["forecast"]["probability"] != summary["forecast"]["baselineProbability"]:
        raise ForecastRunError("binding_mismatch", "Historical forecast run should expose baseline equality.")
    if any(summary["controls"][key] for key in ["networkAccess", "liveFetch", "effectfulGeneration", "paidAction", "privateSourceAccess"]):
        raise ForecastRunError("unsafe_run", "Historical forecast run overstated safe fixture controls.")


def build_summary(
    request_path: Path = DEFAULT_REQUEST,
    max_bytes: int | None = None,
    summary_id: str = DEFAULT_FORECAST_RUN_ID,
) -> dict[str, Any]:
    try:
        request = load_json(request_path)
    except (OSError, json.JSONDecodeError):
        return failure_summary(
            request_path,
            {},
            None,
            summary_id=summary_id,
            run_status="rejected",
            error_code="validation_failed",
            message="Forecast request could not be loaded or parsed.",
        )
    decision = validate_request(request)
    if decision["decisionStatus"] != "accepted":
        return decision_failure_summary(request_path, request, decision, summary_id=summary_id)
    try:
        if request.get("requestId") == HISTORICAL_REQUEST_ID:
            summary = historical_completed_summary(request_path, request, decision, summary_id=summary_id)
        else:
            summary = completed_summary(request_path, request, decision, summary_id=summary_id)
    except (
        ForecastRunError,
        EvidencePlanError,
        EvidenceGatheringError,
        AutoEvidenceForecastError,
        HistoricalBaselineError,
        MethodSelectionError,
        PublicError,
    ) as exc:
        code = exc.code if isinstance(exc, ForecastRunError) else getattr(exc, "code", "forecast_run_failed")
        message = exc.message if isinstance(exc, (ForecastRunError, PublicError)) else "Forecast run could not complete."
        summary = failure_summary(
            request_path,
            request,
            decision,
            summary_id=summary_id,
            run_status="failed",
            error_code=code,
            message=message,
        )
    if max_bytes is not None and len(render_json(summary).encode("utf-8")) > max_bytes:
        return failure_summary(
            request_path,
            request,
            decision,
            summary_id=summary_id,
            run_status="failed",
            error_code="response_too_large",
            message="Forecast run summary exceeds configured size limit.",
        )
    return summary


def validate_summary(summary: dict[str, Any]) -> None:
    errors = validate_record(summary, SCHEMA)
    if errors:
        raise ForecastRunError("internal_error", f"forecast run summary schema validation failed: {errors[0]}")


def write_summary(summary: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(render_json(summary), encoding="utf-8")
    print("generated agent forecast run summary")


def check_summary(summary: dict[str, Any]) -> None:
    expected = render_json(summary)
    if not SUMMARY_PATH.exists():
        print(f"missing agent forecast run summary: {SUMMARY_PATH}", file=sys.stderr)
        print("run `python3 scripts/run_agent_forecast.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = SUMMARY_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"agent forecast run summary drift: {SUMMARY_PATH}", file=sys.stderr)
        print("run `python3 scripts/run_agent_forecast.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked agent forecast run summary")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--check", action="store_true", help="check generated forecast-run summary drift")
    parser.add_argument("--write", action="store_true", help="write generated forecast-run summary")
    args = parser.parse_args()
    summary = build_summary(args.request, max_bytes=args.max_bytes)
    if args.write:
        write_summary(summary)
    elif args.check:
        check_summary(summary)
    else:
        sys.stdout.write(render_json(summary))


if __name__ == "__main__":
    main()
