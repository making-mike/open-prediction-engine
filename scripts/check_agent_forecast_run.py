#!/usr/bin/env python3
"""Check agent forecast-run summary bindings and failure states."""

from __future__ import annotations

from pathlib import Path

from ope_schema import SPEC, validate_record
from run_agent_forecast import DEFAULT_REQUEST, build_summary


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate(summary: dict[str, object]) -> None:
    errors = validate_record(summary, SPEC / "forecast-run-summary.schema.json")
    if errors:
        raise AssertionError(f"forecast-run summary failed schema validation: {errors[0]}")


def main() -> None:
    completed = build_summary(DEFAULT_REQUEST)
    validate(completed)
    require(completed["runStatus"] == "completed", "default run should complete")
    require(completed["decisionStatus"] == "accepted", "default run should use an accepted request")
    controls = completed["controls"]
    for key in ["networkAccess", "liveFetch", "effectfulGeneration", "paidAction", "privateSourceAccess"]:
        require(controls[key] is False, f"forecast-run should keep {key} disabled")

    binding = completed["recordBinding"]
    require(binding["requestId"] == "forecastrequest-007", "forecast-run should bind the request")
    require(binding["sourcePolicyId"] == "sourcepolicy-019", "forecast-run should bind the source policy")
    require(binding["evidencePlanId"] == "evidenceplan-019", "forecast-run should bind the evidence plan")
    require(binding["evidenceSourceSetId"] == "evidencesourceset-019", "forecast-run should bind the source set")
    require(binding["methodSelectionId"] == "methodselection-001", "forecast-run should bind method selection")
    require(binding["pipelineRunId"] == "pipelinerun-601", "forecast-run should bind pipeline run")
    require(binding["forecastId"] == "forecast-602", "forecast-run should bind forecast id")
    require(binding["questionId"] == "question-601", "forecast-run should bind question id")
    require(binding["resolutionRecordId"] == "resolution-601", "forecast-run should bind resolution")
    require(binding["scoringReportId"] == "scoring-601", "forecast-run should bind scoring")

    outputs = completed["outputs"]
    require(outputs["forecastCard"]["operation"] == "forecast_card", "forecast-card output should be linked")
    require(outputs["evidenceTrace"]["operation"] == "evidence_trace", "evidence-trace output should be linked")
    require(outputs["evidenceTrace"]["recordType"] == "evidence-trace", "evidence-trace output should name trace record type")
    require(outputs["lifecycleBundle"]["operation"] == "lifecycle_bundle", "bundle output should be linked")
    require(outputs["resolutionStatus"]["operation"] == "resolution_status", "resolution output should be linked")
    require(outputs["scoringSummary"]["operation"] == "scoring_summary", "scoring output should be linked")

    forecast = completed["forecast"]
    require(forecast["probability"] == 0.41, "forecast-run should expose forecast probability")
    require(forecast["baselineProbability"] == 0.22, "forecast-run should expose baseline probability")
    quality = completed["qualityClaim"]
    require(
        quality["status"] == "not_enough_resolved_auto_evidence_outcomes",
        "forecast-run should keep quality claim provisional",
    )
    require(quality["resolvedComparableOutcomes"] == 1, "forecast-run should report resolved sample count")

    historical = build_summary(ROOT / "spec" / "fixtures" / "requests" / "historical-weather-logistics-request.json")
    validate(historical)
    require(historical["runStatus"] == "completed", "historical-only run should complete")
    require(historical["sourceMode"] == "committed_fixture", "historical-only run should use committed fixture")
    historical_binding = historical["recordBinding"]
    require(historical_binding["requestId"] == "forecastrequest-008", "historical run should bind request")
    require(historical_binding["sourcePolicyId"] == "sourcepolicy-701", "historical run should bind source policy")
    require(historical_binding["forecastId"] == "forecast-702", "historical run should bind forecast id")
    require(historical_binding["evidencePlanId"] is None, "historical run should not bind an evidence plan")
    require(historical_binding["evidenceSourceSetId"] is None, "historical run should not bind a source set")
    require(historical["outputs"]["evidenceTrace"] is None, "historical run should not link evidence trace")
    require(historical["forecast"]["probability"] == 0.22, "historical run should expose baseline probability")
    require(
        historical["forecast"]["probability"] == historical["forecast"]["baselineProbability"],
        "historical run should expose baseline equality",
    )

    approval = build_summary(ROOT / "spec" / "fixtures" / "requests" / "approval-required-sensitive-request.json")
    validate(approval)
    require(approval["runStatus"] == "blocked", "approval-required request should be blocked")
    require(approval["error"]["code"] == "approval_required", "blocked summary should preserve approval code")
    require(approval["recordBinding"]["forecastId"] is None, "blocked summary must not bind a forecast")

    rejected = build_summary(ROOT / "spec" / "fixtures" / "requests" / "unresolvable-request.json")
    validate(rejected)
    require(rejected["runStatus"] == "rejected", "unresolvable request should be rejected")
    require(rejected["error"]["code"] == "unsupported_geography", "rejected summary should preserve first reason code")

    canceled = build_summary(ROOT / "spec" / "fixtures" / "requests" / "canceled-request.json")
    validate(canceled)
    require(canceled["runStatus"] == "canceled", "canceled request should remain canceled")
    require(canceled["error"]["code"] == "canceled", "canceled summary should preserve canceled code")

    oversized = build_summary(DEFAULT_REQUEST, max_bytes=500)
    validate(oversized)
    require(oversized["runStatus"] == "failed", "oversized output should become a failure summary")
    require(oversized["error"]["code"] == "response_too_large", "oversized summary should preserve limit code")
    require(oversized["recordBinding"]["forecastId"] is None, "oversized summary should avoid partial output links")

    print("checked agent forecast run summary")


if __name__ == "__main__":
    main()
