#!/usr/bin/env python3
"""Check agent integration golden-path invariants."""

from __future__ import annotations

try:
    from generate_agent_integration import (  # type: ignore[import-not-found]
        GUIDED_CASES,
        REQUIRED_MCP_TOOLS,
        SOURCE_ROLES,
        build_agent_integration,
        guided_case_payload,
        view_payload,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - red phase guard
    raise AssertionError("agent integration generator is missing") from exc


REQUIRED_REASON_CODES = {
    "candidate_validated",
    "missing_threshold",
    "ambiguous_service_window",
    "vague_geography",
    "missing_resolution_source",
    "unapproved_source",
    "raw_credential_value",
    "raw_sql_query",
    "unsafe_adapter_output",
    "private_row_exposure",
    "post_outcome_evidence",
    "past_tense_question",
    "unresolvable_outcome",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_agent_integration()
    require(record["integrationStatus"] == "agent_integration_golden_path_checked", "status drifted")
    require(record["scenario"] == "helsinki_bus_disruption", "Helsinki starter scenario should be the default")
    require(
        record["surface"]["primaryTransport"] == "local_cli_mcp",
        "first integration surface should stay local CLI/MCP",
    )
    require(
        set(record["surface"]["mcpTools"]) == set(REQUIRED_MCP_TOOLS),
        "integration MCP tools drifted",
    )

    roles = {item["roleKey"]: item for item in record["starterPack"]["sourceRoles"]}
    require(set(roles) == set(SOURCE_ROLES), "starter pack should expose the three required source roles")
    require(roles["weather_forecast"]["forecastTimeAllowed"] is True, "weather should be forecast-time evidence")
    require(
        roles["historical_delay_baseline"]["forecastTimeAllowed"] is True,
        "historical baseline should be forecast-time evidence",
    )
    require(
        roles["transit_delay_outcome"]["forecastTimeAllowed"] is False,
        "HSL outcome evidence should remain resolution-only",
    )
    require(
        roles["transit_delay_outcome"]["resolutionOnly"] is True,
        "HSL outcome role should be explicitly resolution-only",
    )

    candidates = {item["caseKey"]: item for item in record["candidateQuestions"]}
    require(
        candidates["helsinki_surface_transit_peak_delay"]["status"] == "forecastable",
        "Helsinki candidate should be forecastable",
    )
    require(
        candidates["helsinki_surface_transit_peak_delay"]["questionText"]
        == "Will HSL surface transit exceed the beta delay threshold during morning peak on {service_date}?",
        "Helsinki candidate text drifted",
    )
    require(
        candidates["vague_next_week_transit"]["status"] == "needs_clarification",
        "vague transit question should need clarification",
    )
    require(
        candidates["past_tense_transit_delay"]["status"] == "rejected",
        "past-tense question should be rejected",
    )

    statuses = {item["status"] for item in record["candidateQuestions"]}
    require(
        statuses == {"forecastable", "needs_clarification", "blocked", "rejected"},
        "candidate statuses should cover the declared status set",
    )
    reason_codes = {
        reason
        for item in record["candidateQuestions"]
        for reason in item["reasonCodes"]
    }
    require(REQUIRED_REASON_CODES.issubset(reason_codes), "candidate reason-code coverage is incomplete")

    validations = {item["candidateCaseKey"]: item for item in record["validationReports"]}
    checks = {
        item["checkKey"]: item["result"]
        for item in validations["helsinki_surface_transit_peak_delay"]["checks"]
    }
    for check_key in [
        "future_boundary",
        "resolvability",
        "source_policy",
        "source_roles",
        "leakage",
        "baseline_feasibility",
        "claim_boundary",
    ]:
        require(checks[check_key] == "passed", f"{check_key} should pass for the accepted candidate")
    vague_checks = {
        item["checkKey"]: item["result"]
        for item in validations["vague_next_week_transit"]["checks"]
    }
    require(vague_checks["resolvability"] == "needs_clarification", "vague question should fail resolvability clearly")

    accepted = {item["caseKey"]: item for item in record["guidedForecastCases"]}["accepted_adapter_output"]
    require(accepted["guidedStatus"] == "forecast_card_ready", "accepted guided case should reach a forecast card")
    require(accepted["forecastId"] == "forecast-1102", "accepted guided case should bind forecast-1102")
    require(accepted["questionId"] == "question-1102", "accepted guided case should bind question-1102")
    require(accepted["toolCallCount"] <= 3, "accepted guided case should require no more than three routine tool calls")
    require("forecast-card" in accepted["forecastCardCommand"], "accepted case should return a forecast-card command")
    require("forecast-bundle" in accepted["lifecycleBundleCommand"], "accepted case should return a lifecycle bundle command")

    for case in record["guidedForecastCases"]:
        if case["caseKey"] == "accepted_adapter_output":
            continue
        require(case["guidedStatus"] == "blocked", f"{case['caseKey']} should be blocked")
        require(case["forecastId"] is None, f"{case['caseKey']} must not bind a forecast")
        require(case["questionId"] is None, f"{case['caseKey']} must not bind a question")
        require(case["forecastCardCommand"] is None, f"{case['caseKey']} must not expose a forecast-card command")

    require(set(GUIDED_CASES) == {item["caseKey"] for item in record["guidedForecastCases"]}, "guided case list drifted")
    efficiency = record["efficiencyGate"]
    require(efficiency["routineToolCallTarget"] == 3, "first-forecast target should remain three calls")
    require(efficiency["acceptedCaseToolCallCount"] <= 3, "accepted case should meet the call-count target")
    require(efficiency["firstForecastFastTargetMet"] is True, "first forecast fast gate should pass")
    require(efficiency["decisionsAvoided"] >= 8, "efficiency gate should count avoided decisions")
    require(efficiency["forecastCardSuccessStatus"] == "forecast_card_ready", "success status drifted")

    boundary = record["executionBoundary"]
    for key, value in boundary.items():
        if key.endswith("Blocked") or key in {"approvedFilesAndSanitizedAdaptersOnly", "normalChecksAreReadOnly"}:
            require(value is True, f"{key} should be true")
        else:
            require(value is False, f"{key} should be false")

    require(view_payload(record, "candidates") == record["candidateQuestions"], "candidate view drifted")
    require(view_payload(record, "validation") == record["validationReports"], "validation view drifted")
    require(
        guided_case_payload(record, "accepted_adapter_output")["forecastId"] == "forecast-1102",
        "guided accepted payload lookup drifted",
    )
    require(
        guided_case_payload(record, "missing_weather_source")["guidedStatus"] == "blocked",
        "guided blocker payload lookup drifted",
    )

    print("checked agent integration golden path")


if __name__ == "__main__":
    main()
