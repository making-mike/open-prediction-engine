#!/usr/bin/env python3
"""Check source intake status, method, mapping, and safety boundaries."""

from __future__ import annotations

from generate_source_intake import build_fixture_cases, evaluate_intake


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def reports_by_case() -> dict[str, dict]:
    cases = build_fixture_cases()
    return {
        case: evaluate_intake(case, manifest, field_mapping)
        for case, (manifest, field_mapping) in cases.items()
    }


def method_eligibility(report: dict) -> dict[str, bool]:
    return {
        item["methodClass"]: item["eligible"]
        for item in report["methodEligibility"]
    }


def source_decisions(report: dict) -> dict[str, dict]:
    return {
        item["sourceRole"]: item
        for item in report["sourceDecisions"]
    }


def main() -> None:
    cases = build_fixture_cases()
    reports = reports_by_case()
    require(
        set(reports) == {"accepted", "accepted_partial", "needs_confirmation", "rejected"},
        "source intake should cover the four expected outcomes",
    )

    accepted = reports["accepted"]
    require(accepted["intakeStatus"] == "accepted", "accepted fixture should be accepted")
    require(accepted["canProduceForecast"] is True, "accepted fixture should allow forecast generation")
    accepted_methods = method_eligibility(accepted)
    require(accepted_methods["historical_baseline"] is True, "accepted fixture should enable baseline")
    require(accepted_methods["deterministic_statistical"] is True, "accepted fixture should enable deterministic method")
    accepted_manifest, _accepted_mapping = cases["accepted"]
    weather_source = next(source for source in accepted_manifest["sources"] if source["sourceRole"] == "weather_forecast")
    weather_features = {
        item["fieldName"]: item["value"]
        for item in weather_source["featureSummary"]["numericValues"]
    }
    require(
        weather_features["forecast_daily_precipitation_mm"] == 24.0,
        "accepted fixture should expose sanitized precipitation feature summary",
    )

    partial = reports["accepted_partial"]
    require(partial["intakeStatus"] == "accepted_partial", "partial fixture should be accepted_partial")
    require(partial["canProduceForecast"] is True, "partial fixture should still allow a baseline forecast")
    partial_methods = method_eligibility(partial)
    require(partial_methods["historical_baseline"] is True, "partial fixture should enable baseline")
    require(partial_methods["deterministic_statistical"] is False, "partial fixture should not enable weather method")
    coverage = {item["sourceRole"]: item for item in partial["roleCoverage"]}
    require(coverage["weather_forecast"]["status"] == "missing", "partial fixture should miss forecast-time weather")

    needs = reports["needs_confirmation"]
    require(needs["intakeStatus"] == "needs_confirmation", "needs-confirmation fixture should require confirmation")
    require(needs["canProduceForecast"] is False, "proposed mappings should block forecast generation")
    require(
        all(item["decision"] != "accepted" for item in needs["mappingDecisions"] if item["mappingOrigin"] == "agent_inferred"),
        "agent-inferred mappings must remain proposals until confirmed",
    )
    require(
        any("mapping_requires_confirmation" in item["reasonCodes"] for item in needs["mappingDecisions"]),
        "needs-confirmation fixture should explain mapping confirmation",
    )

    rejected = reports["rejected"]
    require(rejected["intakeStatus"] == "rejected", "rejected fixture should be rejected")
    require(rejected["forecastGenerationAllowed"] is False, "rejected fixture must not allow forecast generation")
    rejected_sources = source_decisions(rejected)
    weather_reasons = set(rejected_sources["weather_forecast"]["reasonCodes"])
    require("post_close_or_unavailable_forecast_source" in weather_reasons, "rejected fixture should detect leakage")
    require("source_contains_secrets" in weather_reasons, "rejected fixture should reject sources with secrets")
    baseline_reasons = set(rejected_sources["historical_baseline"]["reasonCodes"])
    require("insufficient_comparable_rows" in baseline_reasons, "rejected fixture should detect low sample size")
    require("insufficient_positive_outcomes" in baseline_reasons, "rejected fixture should detect no positives")

    print("checked source intake boundaries")


if __name__ == "__main__":
    main()
