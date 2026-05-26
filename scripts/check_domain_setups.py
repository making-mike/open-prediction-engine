#!/usr/bin/env python3
"""Check semantic boundaries for OPE domain setup records."""

from __future__ import annotations

from typing import Any

from generate_domain_setups import SEAPORT_DOMAIN, TRANSIT_DOMAIN, WEATHER_DOMAIN, build_setups


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def source_roles(setup: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["roleKey"]: item for item in setup["sourceRoles"]}


def assert_common_setup_rules(setup: dict[str, Any]) -> None:
    require(setup["questionTemplates"], "setup should include at least one question template")
    require(
        all(template["outputType"] == "binary" for template in setup["questionTemplates"]),
        "current setup fixtures should use binary outputs",
    )
    require(setup["resolutionPolicy"]["scoringRule"] == "brier", "binary setups should use Brier scoring")
    require(setup["scoringPolicy"]["primaryScoringRule"] == "brier", "scoring policy should use Brier scoring")
    require(setup["baselinePolicy"]["baselineRequired"] is True, "baseline comparison should be required")
    require(setup["methodPolicy"]["baselineComparisonRequired"] is True, "method policy should require baselines")
    require(setup["methodPolicy"]["leakageCheckRequired"] is True, "method policy should require leakage checks")
    require(setup["recalculationPolicy"]["appendHistoryRequired"] is True, "recalculation must append history")
    require(
        setup["recalculationPolicy"]["postOutcomeEvidenceAllowed"] is False,
        "post-outcome evidence must not enter forecast-time recalculation",
    )
    require(
        setup["claimPolicy"]["universalDomainClaimAllowed"] is False,
        "setups must not claim universal domain coverage",
    )
    require(
        "domain_setup" in setup["scoringPolicy"]["reportingSlices"],
        "scores should be sliceable by domain setup",
    )
    require(
        setup["scoringPolicy"]["minimumResolvedForecastsForQualityClaim"] > 0,
        "quality claim threshold should be positive",
    )


def assert_weather_reference(setup: dict[str, Any]) -> None:
    require(setup["setupKind"] == "reference_setup", "weather setup should be a reference setup")
    require(setup["maturityStatus"] == "fixture_ready", "weather setup should be fixture-ready")
    implementation = setup["localImplementation"]
    require(implementation["forecastRunnable"] is True, "weather reference setup should be runnable")
    require(
        implementation["generatedForecastRecords"] is True,
        "weather reference setup should generate forecast records",
    )
    require("forecast-run" in implementation["cliForecastCommand"], "weather setup should expose forecast-run CLI")

    roles = source_roles(setup)
    require(
        {"weather_forecast", "historical_baseline", "declared_operations_outcome"}.issubset(roles),
        "weather setup should bind forecast, baseline, and resolution roles",
    )
    require(roles["weather_forecast"]["timing"] == "forecast_time", "weather evidence should be forecast-time")
    require(roles["historical_baseline"]["timing"] == "baseline", "historical role should be baseline")
    require(
        roles["declared_operations_outcome"]["forecastTimeAllowed"] is False,
        "resolution outcome must not be forecast-time evidence",
    )
    require(
        setup["claimPolicy"]["calibrationClaimAllowed"] is False,
        "fixture-ready setup should not claim calibration",
    )
    require(
        setup["claimPolicy"]["stateOfTheArtClaimAllowed"] is False,
        "fixture-ready setup should not claim state-of-the-art performance",
    )


def assert_candidate_private_setup(setup: dict[str, Any]) -> None:
    require(setup["setupKind"] == "candidate_private_setup", "seaport setup should be a candidate private setup")
    require(setup["maturityStatus"] == "candidate", "seaport setup should remain candidate")
    implementation = setup["localImplementation"]
    require(implementation["forecastRunnable"] is False, "candidate setup must not be runnable yet")
    require(
        implementation["generatedForecastRecords"] is False,
        "candidate setup must not claim generated forecast records",
    )
    require(implementation["cliForecastCommand"] is None, "candidate setup must not expose a forecast command")

    roles = source_roles(setup)
    expected_roles = {
        "vessel_schedule",
        "historical_arrivals",
        "berth_occupancy",
        "ais_position",
        "marine_weather",
        "operations_outcome",
    }
    require(expected_roles.issubset(roles), "candidate setup should prove a non-weather source-role shape")
    require(roles["operations_outcome"]["forecastTimeAllowed"] is False, "outcome role must be resolution-only")
    require(
        setup["baselinePolicy"]["fallbackWhenInsufficientData"] == "needs_more_data",
        "candidate setup should ask for more data instead of overclaiming",
    )

    claims = setup["claimPolicy"]
    blocked = " ".join(claims["blockedClaims"]).lower()
    for phrase in ["calibrated", "benchmarked", "production readiness", "state-of-the-art"]:
        require(phrase in blocked, f"candidate setup should block {phrase} claims")
    require(claims["qualityClaimAllowed"] is False, "candidate setup must block quality claims")
    require(claims["benchmarkClaimAllowed"] is False, "candidate setup must block benchmark claims")
    require(claims["calibrationClaimAllowed"] is False, "candidate setup must block calibration claims")
    require(
        claims["productionReadinessClaimAllowed"] is False,
        "candidate setup must block production readiness claims",
    )


def assert_transit_reference(setup: dict[str, Any]) -> None:
    require(setup["setupKind"] == "reference_setup", "transit setup should be a reference setup")
    require(setup["maturityStatus"] == "fixture_ready", "transit setup should be fixture-ready")
    implementation = setup["localImplementation"]
    require(implementation["forecastRunnable"] is True, "transit setup should expose a local runnable command")
    require("transit-delay-forecast" in implementation["cliForecastCommand"], "transit setup should expose transit CLI")

    roles = source_roles(setup)
    expected_roles = {
        "weather_forecast",
        "historical_delay_baseline",
        "transit_schedule",
        "transit_delay_outcome",
    }
    require(expected_roles.issubset(roles), "transit setup should bind weather, baseline, schedule, and outcome roles")
    require(roles["weather_forecast"]["timing"] == "forecast_time", "transit weather should be forecast-time")
    require(roles["historical_delay_baseline"]["timing"] == "baseline", "transit history should be baseline")
    require(roles["transit_delay_outcome"]["forecastTimeAllowed"] is False, "transit outcome must be resolution-only")
    require(
        setup["claimPolicy"]["calibrationClaimAllowed"] is False,
        "transit setup should not claim calibration",
    )
    require(
        setup["claimPolicy"]["productionReadinessClaimAllowed"] is False,
        "transit setup should not claim production readiness",
    )


def main() -> None:
    setups = build_setups()
    require(
        set(setups) == {WEATHER_DOMAIN, SEAPORT_DOMAIN, TRANSIT_DOMAIN},
        "should build weather, seaport, and transit setup fixtures",
    )
    require(
        setups[WEATHER_DOMAIN]["domain"] != setups[SEAPORT_DOMAIN]["domain"],
        "setup fixtures should cover distinct domains",
    )
    for setup in setups.values():
        assert_common_setup_rules(setup)
    assert_weather_reference(setups[WEATHER_DOMAIN])
    assert_candidate_private_setup(setups[SEAPORT_DOMAIN])
    assert_transit_reference(setups[TRANSIT_DOMAIN])
    print("checked domain setup semantics")


if __name__ == "__main__":
    main()
