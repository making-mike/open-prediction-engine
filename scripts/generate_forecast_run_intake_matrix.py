#!/usr/bin/env python3
"""Generate or check forecast-run intake outcome examples and matrix."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from run_agent_forecast import DEFAULT_REQUEST, build_summary, render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "forecast-run"
MATRIX_PATH = GENERATED / "weather-logistics-forecast-run-intake-matrix.generated.json"
SUMMARY_SCHEMA = "spec/forecast-run-summary.schema.json"
MATRIX_SCHEMA = SPEC / "forecast-run-intake-matrix.schema.json"
GENERATED_AT = "2026-06-06T13:15:00Z"


class ForecastRunMatrixError(Exception):
    pass


@dataclass(frozen=True)
class IntakeCase:
    outcome_class: str
    request_path: Path
    summary_id: str
    summary_filename: str
    max_bytes: int | None
    terminal: bool
    retry_policy: str
    agent_next_action: str


CASES = [
    IntakeCase(
        outcome_class="accepted",
        request_path=DEFAULT_REQUEST,
        summary_id="forecastrun-001",
        summary_filename="weather-logistics-agent-forecast-run.generated.json",
        max_bytes=None,
        terminal=False,
        retry_policy="not_needed",
        agent_next_action="Use forecastCard for compact action context or lifecycleBundle for audit context.",
    ),
    IntakeCase(
        outcome_class="rejected",
        request_path=ROOT / "spec" / "fixtures" / "requests" / "unresolvable-request.json",
        summary_id="forecastrun-002",
        summary_filename="weather-logistics-rejected-forecast-run.generated.json",
        max_bytes=None,
        terminal=True,
        retry_policy="revise_request_then_retry",
        agent_next_action="Revise the geography, question text, or source policy before retrying.",
    ),
    IntakeCase(
        outcome_class="blocked",
        request_path=ROOT / "spec" / "fixtures" / "requests" / "approval-required-sensitive-request.json",
        summary_id="forecastrun-003",
        summary_filename="weather-logistics-blocked-forecast-run.generated.json",
        max_bytes=None,
        terminal=False,
        retry_policy="approval_then_retry",
        agent_next_action="Request explicit approval before retrying the forecast run.",
    ),
    IntakeCase(
        outcome_class="canceled",
        request_path=ROOT / "spec" / "fixtures" / "requests" / "canceled-request.json",
        summary_id="forecastrun-004",
        summary_filename="weather-logistics-canceled-forecast-run.generated.json",
        max_bytes=None,
        terminal=True,
        retry_policy="stop_terminal",
        agent_next_action="Stop; the caller canceled the request before execution.",
    ),
    IntakeCase(
        outcome_class="unsupported_fixture_path",
        request_path=ROOT / "spec" / "fixtures" / "requests" / "generate-weather-logistics-request.json",
        summary_id="forecastrun-005",
        summary_filename="weather-logistics-unsupported-fixture-path-forecast-run.generated.json",
        max_bytes=None,
        terminal=True,
        retry_policy="supported_fixture_or_runtime_expansion_required",
        agent_next_action="Use the supported auto-evidence fixture request or wait for broader runtime support.",
    ),
    IntakeCase(
        outcome_class="response_too_large",
        request_path=DEFAULT_REQUEST,
        summary_id="forecastrun-006",
        summary_filename="weather-logistics-response-too-large-forecast-run.generated.json",
        max_bytes=500,
        terminal=False,
        retry_policy="increase_max_bytes_or_read_smaller_output",
        agent_next_action="Retry with a larger maxBytes limit or read smaller operation-specific outputs.",
    ),
]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def mcp_is_error(summary: dict[str, Any]) -> bool:
    return summary["runStatus"] != "completed"


def expected_error_code(summary: dict[str, Any]) -> str | None:
    error = summary["error"]
    return error["code"] if isinstance(error, dict) else None


def build_case_summary(case: IntakeCase) -> dict[str, Any]:
    summary = build_summary(
        case.request_path,
        max_bytes=case.max_bytes,
        summary_id=case.summary_id,
    )
    validate_summary(summary)
    return summary


def validate_summary(summary: dict[str, Any]) -> None:
    errors = validate_record(summary, SPEC / "forecast-run-summary.schema.json")
    if errors:
        raise ForecastRunMatrixError(f"forecast-run summary failed schema validation: {errors[0]}")


def outcome_entry(case: IntakeCase, summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "outcomeClass": case.outcome_class,
        "requestFixture": rel(case.request_path),
        "summaryPath": rel(GENERATED / case.summary_filename),
        "forecastRunSummaryId": summary["forecastRunSummaryId"],
        "runStatus": summary["runStatus"],
        "decisionStatus": summary["decisionStatus"],
        "errorCode": expected_error_code(summary),
        "generatesForecastOutputs": summary["runStatus"] == "completed",
        "terminal": case.terminal,
        "retryPolicy": case.retry_policy,
        "agentNextAction": case.agent_next_action,
        "mcpExpectation": {
            "toolName": "ope_forecast_run",
            "isError": mcp_is_error(summary),
            "structuredSchema": SUMMARY_SCHEMA,
        },
    }


def validate_matrix(matrix: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> None:
    errors = validate_record(matrix, MATRIX_SCHEMA)
    if errors:
        raise ForecastRunMatrixError(f"forecast-run intake matrix failed schema validation: {errors[0]}")
    outcomes = {item["outcomeClass"]: item for item in matrix["outcomes"]}
    expected_classes = {case.outcome_class for case in CASES}
    if set(outcomes) != expected_classes:
        raise ForecastRunMatrixError("forecast-run matrix should cover each expected outcome class")
    for case in CASES:
        entry = outcomes[case.outcome_class]
        summary = summaries[case.outcome_class]
        if entry["forecastRunSummaryId"] != summary["forecastRunSummaryId"]:
            raise ForecastRunMatrixError("matrix/summary id binding mismatch")
        if entry["runStatus"] != summary["runStatus"]:
            raise ForecastRunMatrixError("matrix/summary run status mismatch")
        if entry["decisionStatus"] != summary["decisionStatus"]:
            raise ForecastRunMatrixError("matrix/summary decision status mismatch")
        if entry["errorCode"] != expected_error_code(summary):
            raise ForecastRunMatrixError("matrix/summary error-code mismatch")
        binding = summary["recordBinding"]
        output_bound = any(
            binding[key] is not None
            for key in [
                "evidencePlanId",
                "evidenceSourceSetId",
                "methodSelectionId",
                "pipelineRunId",
                "questionId",
                "forecastId",
                "resolutionRecordId",
                "scoringReportId",
            ]
        )
        if summary["runStatus"] != "completed" and output_bound:
            raise ForecastRunMatrixError("non-completed forecast-run summary must not bind generated outputs")
        if summary["runStatus"] == "completed" and not entry["generatesForecastOutputs"]:
            raise ForecastRunMatrixError("completed forecast-run summary should generate forecast outputs")
        if summary["runStatus"] != "completed" and entry["generatesForecastOutputs"]:
            raise ForecastRunMatrixError("failed forecast-run summary must not claim generated outputs")


def build_matrix() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    summaries = {
        case.outcome_class: build_case_summary(case)
        for case in CASES
    }
    matrix = {
        "forecastRunIntakeMatrixId": "forecastrunmatrix-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "supportedDefaultRequestId": "forecastrequest-007",
        "summarySchema": SUMMARY_SCHEMA,
        "outcomes": [
            outcome_entry(case, summaries[case.outcome_class])
            for case in CASES
        ],
        "warnings": [
            "Only the accepted default auto-evidence fixture path generates forecast outputs.",
            "Blocked, rejected, canceled, unsupported, and oversized outcomes must not bind forecast IDs.",
            "The matrix is local and fixture-safe; it is not a hosted service or live-fetch workflow.",
        ],
    }
    validate_matrix(matrix, summaries)
    return matrix, summaries


def write_outputs(matrix: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    expected_names = {MATRIX_PATH.name, *[case.summary_filename for case in CASES]}
    for path in GENERATED.glob("*forecast-run.generated.json"):
        if path.name not in expected_names:
            path.unlink()
    for case in CASES:
        (GENERATED / case.summary_filename).write_text(
            render_json(summaries[case.outcome_class]),
            encoding="utf-8",
        )
    MATRIX_PATH.write_text(render_json(matrix), encoding="utf-8")
    print("generated forecast-run intake matrix")


def check_outputs(matrix: dict[str, Any], summaries: dict[str, dict[str, Any]]) -> None:
    expected = {
        MATRIX_PATH: render_json(matrix),
    }
    for case in CASES:
        expected[GENERATED / case.summary_filename] = render_json(summaries[case.outcome_class])

    errors: list[str] = []
    expected_paths = set(expected)
    for path in sorted(GENERATED.glob("*forecast-run.generated.json")):
        if path not in expected_paths:
            errors.append(f"stale forecast-run summary: {path}")
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing forecast-run intake output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"forecast-run intake drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_forecast_run_intake_matrix.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked forecast-run intake matrix")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated intake matrix drift")
    parser.add_argument("--write", action="store_true", help="write generated intake matrix and summaries")
    args = parser.parse_args()
    try:
        matrix, summaries = build_matrix()
    except ForecastRunMatrixError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(matrix, summaries)
    elif args.check:
        check_outputs(matrix, summaries)
    else:
        sys.stdout.write(render_json(matrix))


if __name__ == "__main__":
    main()
