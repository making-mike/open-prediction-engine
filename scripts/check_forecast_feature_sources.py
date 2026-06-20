#!/usr/bin/env python3
"""Check the composable forecast-time feature sources (Phase 0 + calendar/FMI)."""

from __future__ import annotations

import forecast_feature_sources as fs
import run_transit_delay_forecast as forecast


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_weather_only_unchanged() -> None:
    """The composable path must reproduce legacy weather behaviour byte-for-byte.

    With no FMI fields and no calendar, weather_adjustment over a plain weather
    dict is the entire adjustment — the framework adds nothing.
    """
    weather = {
        "forecastPrecipitationMm": 12.0,
        "forecastSnowfallMm": 0.0,
        "forecastWindGustKmh": 55.0,
        "temperatureC": 4.0,
    }
    adjustment, factors = forecast.weather_adjustment(weather)
    require(adjustment == round(0.08 + 0.07 + 0.06, 4), "legacy precip+gust adjustment must be unchanged")
    require("roadSurfaceTempC" not in weather, "no FMI fields means no road term")
    require(all("road surface" not in f and "visibility" not in f for f in factors), "absent FMI fields contribute no factors")


def test_fmi_merge_activates_winter_terms() -> None:
    base = {
        "forecastPrecipitationMm": 0.0,
        "forecastSnowfallMm": 0.0,
        "forecastWindGustKmh": 0.0,
        "temperatureC": None,
    }
    merged = fs.merge_fmi_weather(
        base,
        {"temperatureC": -7.4, "snowfallMm": 3.1, "roadSurfaceTempC": -3.5, "visibilityM": 700.0},
    )
    require(merged["temperatureC"] == -7.4, "FMI temperature should fill the weather dict")
    require(merged["forecastSnowfallMm"] == 3.1, "FMI snowfall should fill the weather dict")
    adjustment, factors = forecast.weather_adjustment(merged)
    # snow>=1 (+0.10) + temp<=-5 (+0.04) + road<=0 (+0.08) + visibility<=1000 (+0.04)
    require(adjustment == round(0.10 + 0.04 + 0.08 + 0.04, 4), f"winter terms should stack, got {adjustment}")
    require(any("snowfall" in f for f in factors), "snowfall factor expected")
    require(any("road surface" in f for f in factors), "road-surface factor expected")
    require(any("visibility" in f for f in factors), "visibility factor expected")


def test_fmi_absent_is_noop() -> None:
    base = {"forecastPrecipitationMm": 0.0, "forecastSnowfallMm": 0.0, "forecastWindGustKmh": 0.0, "temperatureC": None}
    require(fs.merge_fmi_weather(base, None) == base, "no FMI input must leave the weather dict unchanged")


def test_calendar_known_dates() -> None:
    # 2026-12-06 is Finnish Independence Day (a Sunday in 2026).
    indep = fs.calendar_features("2026-12-06")
    require(indep["isHoliday"] and indep["holidayName"] == "independence_day", "Dec 6 should be Independence Day")
    # A summer Saturday: weekend, not school term.
    sat = fs.calendar_features("2026-07-04")
    require(sat["isWeekend"] and not sat["isSchoolTerm"], "July Saturday should be weekend, non-term")
    # A spring weekday in term.
    weekday = fs.calendar_features("2026-03-10")
    require(not weekday["isWeekend"] and weekday["isSchoolTerm"], "March 10 should be a school-term weekday")
    # Easter Sunday 2026 is April 5.
    easter = fs.calendar_features("2026-04-05")
    require(easter["holidayName"] == "easter_sunday", "2026-04-05 should be Easter Sunday")


def test_calendar_contribution_signs() -> None:
    holiday_adj, _ = fs.calendar_contribution(fs.calendar_features("2026-12-06"))
    require(holiday_adj < 0, "holiday should reduce delay risk")
    weekday_adj, factors = fs.calendar_contribution(fs.calendar_features("2026-03-10"))
    require(weekday_adj > 0, "school-term weekday should raise delay risk")
    require(any("school-term" in f for f in factors), "weekday factor should mention school term")
    weekend_adj, _ = fs.calendar_contribution(fs.calendar_features("2026-07-04"))
    require(weekend_adj < 0, "weekend should reduce delay risk")


def test_calendar_provenance_ref() -> None:
    ref = fs.calendar_provenance_ref(fs.calendar_features("2026-03-10"), "2026-03-10T02:00:00Z")
    require(ref["sourceType"] == "other", "calendar source type should be 'other' (derived)")
    require(len(ref["contentHash"]) >= 8, "calendar provenance should carry a content hash")
    require("uri" not in ref, "computed calendar source has no file uri")


def test_registry_metadata() -> None:
    ids = {s["sourceId"] for s in fs.FEATURE_SOURCES}
    require({"source-1205", "source-1210"}.issubset(ids), "FMI and calendar sources should be registered")
    require(all(s["forecastTime"] for s in fs.FEATURE_SOURCES), "all Phase 0/1 sources are forecast-time")


def main() -> None:
    test_weather_only_unchanged()
    test_fmi_merge_activates_winter_terms()
    test_fmi_absent_is_noop()
    test_calendar_known_dates()
    test_calendar_contribution_signs()
    test_calendar_provenance_ref()
    test_registry_metadata()
    print("checked forecast feature sources")


if __name__ == "__main__":
    main()
