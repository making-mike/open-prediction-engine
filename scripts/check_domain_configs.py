#!/usr/bin/env python3
"""Check domain configuration semantics."""

from __future__ import annotations

from generate_domain_configs import SEAPORT_DOMAIN, WEATHER_TRANSIT_DOMAIN, build_domain_configs


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def roles(config: dict[str, object]) -> dict[str, dict[str, object]]:
    return {item["roleKey"]: item for item in config["acceptedSourceRoles"]}  # type: ignore[index]


def assert_common_config(config: dict[str, object]) -> None:
    role_rows = roles(config)
    require(config["questionTemplates"], "domain config should include question templates")
    require(config["horizons"], "domain config should include horizons")
    require(config["resolutionCriteria"]["primaryOutcomeRole"] in role_rows, "resolution role should be accepted")  # type: ignore[index]
    require(config["baselineMethod"]["methodClass"] == "historical_frequency", "baseline should be historical")  # type: ignore[index]
    require(config["baselineMethod"]["defaultUntilApprovedUpdate"] is True, "baseline should stay default")  # type: ignore[index]
    require(any(item["timing"] == "forecast_time" for item in role_rows.values()), "forecast-time role missing")
    require(any(item["timing"] == "resolution" for item in role_rows.values()), "resolution role missing")
    for role_row in role_rows.values():
        require(role_row["credentialValuesStored"] is False, "domain configs must not store credentials")
        if role_row["timing"] == "resolution":
            require(role_row["forecastTimeAllowed"] is False, "resolution roles must not be forecast evidence")
    claims = config["claimBoundaries"]  # type: ignore[index]
    require(claims["qualityClaimAllowed"] is False, "quality claims should be blocked")
    require(claims["calibrationClaimAllowed"] is False, "calibration claims should be blocked")
    require(claims["stateOfTheArtClaimAllowed"] is False, "state-of-the-art claims should be blocked")
    require(claims["productionReadinessClaimAllowed"] is False, "production claims should be blocked")
    boundary = config["executionBoundary"]  # type: ignore[index]
    for key, value in boundary.items():
        require(value is False, f"execution boundary should keep {key} false")
    summary = config["summary"]  # type: ignore[index]
    require(all(summary.values()), "domain config summary flags should all be true")


def main() -> None:
    configs = build_domain_configs()
    require(set(configs) == {WEATHER_TRANSIT_DOMAIN, SEAPORT_DOMAIN}, "domain config coverage drifted")
    transit = configs[WEATHER_TRANSIT_DOMAIN]
    seaport = configs[SEAPORT_DOMAIN]

    for config in configs.values():
        assert_common_config(config)

    transit_roles = roles(transit)
    require(transit["configStatus"] == "defined_readback", "transit config status drifted")
    require("weather_forecast" in transit_roles, "transit config should accept weather forecast role")
    require("historical_delay_baseline" in transit_roles, "transit config should accept delay baseline role")
    require("transit_delay_outcome" in transit_roles, "transit config should accept outcome role")
    require(transit["sampleThresholds"]["minimumComparableForecastsForCalibration"] == 100, "transit threshold drifted")

    seaport_roles = roles(seaport)
    require(seaport["configStatus"] == "candidate_readback", "seaport config status drifted")
    require("vessel_schedule" in seaport_roles, "seaport config should accept vessel schedule role")
    require("historical_berth_baseline" in seaport_roles, "seaport config should accept berth baseline role")
    require("berth_availability_outcome" in seaport_roles, "seaport config should accept outcome role")
    require("database" in seaport_roles["vessel_schedule"]["acceptedSourceKinds"], "seaport should allow database adapters")
    print("checked domain configs")


if __name__ == "__main__":
    main()
