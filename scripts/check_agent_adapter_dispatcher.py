#!/usr/bin/env python3
"""Smoke-test the local single-operation agent adapter dispatcher."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = [sys.executable, "scripts/ope.py", "agent-call"]


def run_dispatcher(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*DISPATCHER, *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"dispatcher did not return JSON: {result.stdout!r} {result.stderr!r}") from exc
    errors = validate_record(data, SPEC / "agent-envelope.schema.json")
    if errors:
        raise AssertionError(f"dispatcher envelope failed schema validation: {errors[0]}")
    return data


def assert_error(
    result: subprocess.CompletedProcess[str],
    *,
    exit_code: int,
    error_code: str,
) -> dict[str, object]:
    data = payload(result)
    if result.returncode != exit_code:
        raise AssertionError(f"expected exit code {exit_code}, got {result.returncode}")
    if data["status"] != "error":
        raise AssertionError("expected an error envelope")
    if data["exitCode"] != exit_code:
        raise AssertionError("error envelope exitCode should match process exit code")
    if data["error"]["code"] != error_code:
        raise AssertionError(f"expected error code {error_code}, got {data['error']['code']}")
    if "/Users/" in result.stdout or "Traceback" in result.stderr:
        raise AssertionError("dispatcher error output should be sanitized")
    return data


def main() -> None:
    success = run_dispatcher(
        "--operation",
        "forecast_card",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    success_payload = payload(success)
    if success.returncode != 0:
        raise AssertionError(f"forecast-card agent call should succeed: {success.stderr}")
    if success_payload["payload"]["record"]["forecastId"] != "forecast-602":
        raise AssertionError("forecast-card agent call should bind forecast-602")
    if success_payload["recordBinding"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("forecast-card agent call should preserve source policy binding")

    trace = run_dispatcher(
        "--operation",
        "evidence_trace",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    trace_payload = payload(trace)
    if trace.returncode != 0:
        raise AssertionError(f"evidence-trace agent call should succeed: {trace.stderr}")
    if trace_payload["payload"]["record"]["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence-trace agent call should preserve connector result-set binding")
    if trace_payload["recordBinding"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("evidence-trace agent call should preserve source-set binding")

    scoring = run_dispatcher(
        "--operation",
        "scoring_summary",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    scoring_payload = payload(scoring)
    if scoring.returncode != 0 or scoring_payload["payload"]["scoringReportId"] != "scoring-601":
        raise AssertionError("scoring-summary agent call should return scoring-601")

    request = run_dispatcher(
        "--operation",
        "forecast_request_validation",
        "--request",
        "spec/fixtures/requests/auto-weather-logistics-request.json",
    )
    request_payload = payload(request)
    if request.returncode != 0 or request_payload["payload"]["decisionStatus"] != "accepted":
        raise AssertionError("request-validation agent call should return accepted decision")

    not_found = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-999",
            "--question-id",
            "question-601",
        ),
        exit_code=4,
        error_code="not_found",
    )
    if not_found["recordBinding"]["forecastId"] != "forecast-999":
        raise AssertionError("not-found envelope should preserve requested forecast id")

    binding = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-602",
            "--question-id",
            "question-999",
        ),
        exit_code=4,
        error_code="binding_mismatch",
    )
    if binding["recordBinding"]["questionId"] != "question-999":
        raise AssertionError("binding-mismatch envelope should preserve requested question id")

    approval = assert_error(
        run_dispatcher(
            "--operation",
            "evidence_plan",
            "--request",
            "spec/fixtures/requests/approval-required-sensitive-request.json",
        ),
        exit_code=3,
        error_code="approval_required",
    )
    if approval["state"]["planStatus"] != "blocked":
        raise AssertionError("approval-required envelope should preserve blocked plan status")

    too_large = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-602",
            "--question-id",
            "question-601",
            "--max-bytes",
            "500",
        ),
        exit_code=5,
        error_code="response_too_large",
    )
    if too_large["payload"] is not None:
        raise AssertionError("response-too-large envelope should not include the oversized payload")

    print("checked local agent adapter dispatcher")


if __name__ == "__main__":
    main()
