#!/usr/bin/env python3
"""Check forecast-run intake matrix outcome and binding invariants."""

from __future__ import annotations

from generate_forecast_run_intake_matrix import CASES, build_matrix


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    matrix, summaries = build_matrix()
    outcomes = {item["outcomeClass"]: item for item in matrix["outcomes"]}
    require(set(outcomes) == {case.outcome_class for case in CASES}, "matrix should cover every intake class")

    accepted = outcomes["accepted"]
    require(accepted["generatesForecastOutputs"] is True, "accepted run should generate outputs")
    require(accepted["mcpExpectation"]["isError"] is False, "accepted MCP run should not be a tool error")
    accepted_summary = summaries["accepted"]
    require(accepted_summary["recordBinding"]["forecastId"] == "forecast-602", "accepted run should bind forecast-602")
    require(accepted_summary["outputs"]["forecastCard"]["recordId"] == "forecast-602", "accepted run should link card")
    require(accepted_summary["outputs"]["evidenceTrace"]["recordId"] == "forecast-602", "accepted run should link evidence trace")

    for outcome_class in ["rejected", "blocked", "canceled", "unsupported_fixture_path", "response_too_large"]:
        entry = outcomes[outcome_class]
        summary = summaries[outcome_class]
        require(entry["generatesForecastOutputs"] is False, f"{outcome_class} must not generate outputs")
        require(entry["mcpExpectation"]["isError"] is True, f"{outcome_class} MCP call should be a tool error")
        require(summary["forecast"] is None, f"{outcome_class} must not include a forecast")
        require(summary["qualityClaim"] is None, f"{outcome_class} must not include quality claims")
        require(summary["recordBinding"]["forecastId"] is None, f"{outcome_class} must not bind a forecast")
        require(summary["outputs"]["forecastCard"] is None, f"{outcome_class} must not link a card")
        require(summary["outputs"]["evidenceTrace"] is None, f"{outcome_class} must not link an evidence trace")

    require(outcomes["blocked"]["retryPolicy"] == "approval_then_retry", "blocked should ask for approval")
    require(outcomes["rejected"]["retryPolicy"] == "revise_request_then_retry", "rejected should ask for revision")
    require(outcomes["canceled"]["terminal"] is True, "canceled should be terminal")
    require(
        outcomes["unsupported_fixture_path"]["retryPolicy"] == "supported_fixture_or_runtime_expansion_required",
        "unsupported fixture path should not retry blindly",
    )
    require(
        outcomes["response_too_large"]["retryPolicy"] == "increase_max_bytes_or_read_smaller_output",
        "response-too-large should recommend a size-aware retry",
    )

    print("checked forecast-run intake matrix")


if __name__ == "__main__":
    main()
