#!/usr/bin/env python3
"""Composable forecast-time feature sources for the transit-delay predictor.

Generalizes the single weather adjustment into a small registry of forecast-time
feature contributors. Each contributor turns its inputs into an additive
probability adjustment (transparent beta terms, never fitted), human-readable
factors, and a provenance reference. Two rules hold:

- Forecast-time only. A contributor may use only inputs knowable before the
  window opens (a weather forecast, the calendar). Real-time/resolution signals
  do not belong here.
- Lift is earned, not asserted. The coefficients below are transparent guesses;
  whether a source actually helps is decided later by the calibration gate and
  the feature-attribution surface, never here.

Composition is additive and conditional: a source contributes only when its
input is supplied. With no extra sources (the checked fixture path), the
forecast reproduces the weather-only behaviour byte-for-byte.

Phase 1 sources: FMI winter weather (deepens the weather feature dict with
temperature / snowfall / road-surface / visibility) and a Finnish calendar
contributor (public holidays, school terms, day of week). Pure standard library.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Any


# --- source registry (documentation + attribution + provenance metadata) -----
FEATURE_SOURCES: list[dict[str, Any]] = [
    {
        "sourceId": "source-1201",
        "name": "Transit Weather Forecast File",
        "sourceType": "public_dataset",
        "forecastTime": True,
        "note": "Open-Meteo precipitation + wind gusts (existing).",
    },
    {
        "sourceId": "source-1205",
        "name": "FMI Open Data Winter Weather",
        "sourceType": "official",
        "forecastTime": True,
        "note": "Temperature, snowfall, road-surface temperature, visibility.",
    },
    {
        "sourceId": "source-1210",
        "name": "Finnish Calendar Features",
        "sourceType": "other",
        "forecastTime": True,
        "note": "Public holidays, school terms, day of week (derived).",
    },
]


# --- FMI: deepen the weather feature dict ------------------------------------
def merge_fmi_weather(weather: dict[str, Any], fmi: dict[str, Any] | None) -> dict[str, Any]:
    """Return a weather feature dict with FMI winter fields filled in.

    FMI provides the official temperature / snowfall the Open-Meteo file does not
    carry, plus road-surface temperature and visibility. FMI values win for the
    fields it supplies; everything else is untouched, so omitting FMI leaves the
    weather dict (and therefore the forecast) unchanged.
    """
    if not fmi:
        return weather
    merged = dict(weather)
    if fmi.get("temperatureC") is not None:
        merged["temperatureC"] = fmi["temperatureC"]
    if fmi.get("snowfallMm") is not None:
        merged["forecastSnowfallMm"] = fmi["snowfallMm"]
    if fmi.get("roadSurfaceTempC") is not None:
        merged["roadSurfaceTempC"] = fmi["roadSurfaceTempC"]
    if fmi.get("visibilityM") is not None:
        merged["visibilityM"] = fmi["visibilityM"]
    return merged


# --- Finnish calendar ---------------------------------------------------------
def easter_sunday(year: int) -> date:
    """Anonymous Gregorian (Meeus/Jones/Butcher) algorithm."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    m = (32 + 2 * e + 2 * i - h - k) % 7
    n = (a + 11 * h + 22 * m) // 451
    month, day = divmod(h + m - 7 * n + 114, 31)
    return date(year, month, day + 1)


def saturday_between(year: int, month: int, lo: int, hi: int) -> date:
    """The Saturday whose date falls in [lo, hi] of the given month (Fin. style)."""
    for day in range(lo, hi + 1):
        candidate = date(year, month, day)
        if candidate.weekday() == 5:
            return candidate
    return date(year, month, lo)


def finnish_holidays(year: int) -> dict[date, str]:
    easter = easter_sunday(year)
    holidays = {
        date(year, 1, 1): "new_year",
        date(year, 1, 6): "epiphany",
        easter - timedelta(days=2): "good_friday",
        easter: "easter_sunday",
        easter + timedelta(days=1): "easter_monday",
        date(year, 5, 1): "may_day",
        easter + timedelta(days=39): "ascension",
        easter + timedelta(days=49): "pentecost",
        saturday_between(year, 6, 20, 26): "midsummer_day",
        saturday_between(year, 11, 1, 6) if date(year, 10, 31).weekday() != 5 else date(year, 10, 31): "all_saints",
        date(year, 12, 6): "independence_day",
        date(year, 12, 24): "christmas_eve",
        date(year, 12, 25): "christmas_day",
        date(year, 12, 26): "st_stephens_day",
    }
    holidays[holidays_midsummer_eve(year)] = "midsummer_eve"
    return holidays


def holidays_midsummer_eve(year: int) -> date:
    return saturday_between(year, 6, 20, 26) - timedelta(days=1)


def is_school_term(d: date) -> bool:
    """Approximate Finnish basic-education term (documented heuristic, not legal).

    Autumn term mid-August to mid-December; spring term early January to early
    June. Summer break and the Christmas break (Dec 22 - Jan 6) are out of term.
    """
    md = (d.month, d.day)
    if (d.month == 12 and d.day >= 22) or (d.month == 1 and d.day <= 6):
        return False
    if d.month in (1, 2, 3, 4, 5):
        return True
    if d.month == 6 and d.day <= 5:
        return True
    if d.month == 8 and d.day >= 11:
        return True
    if d.month in (9, 10, 11, 12):
        return True
    return False  # June 6 - Aug 10 summer break, all of July


def calendar_features(service_date: str) -> dict[str, Any]:
    d = datetime.strptime(service_date, "%Y-%m-%d").date()
    holidays = finnish_holidays(d.year)
    holiday_name = holidays.get(d)
    return {
        "serviceDate": service_date,
        "dayOfWeek": d.strftime("%A").lower(),
        "isWeekend": d.weekday() >= 5,
        "isHoliday": holiday_name is not None,
        "holidayName": holiday_name or "none",
        "isSchoolTerm": is_school_term(d),
    }


def calendar_contribution(features: dict[str, Any]) -> tuple[float, list[str]]:
    """Transparent calendar beta terms. Holidays/weekends lighten road traffic;
    school-term weekdays load the network. Signs are intuitions to be validated,
    not calibrated weights."""
    adjustment = 0.0
    factors: list[str] = []
    if features["isHoliday"]:
        adjustment -= 0.04
        factors.append(f"public holiday ({features['holidayName']}), lighter traffic")
    elif features["isWeekend"]:
        adjustment -= 0.02
        factors.append(f"weekend ({features['dayOfWeek']}), lighter traffic")
    elif features["isSchoolTerm"]:
        adjustment += 0.03
        factors.append("school-term weekday, heavier traffic")
    else:
        factors.append("non-term weekday, neutral traffic")
    return round(adjustment, 4), factors


def calendar_provenance_ref(features: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    digest = hashlib.sha256(
        json.dumps(features, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "sourceId": "source-1210",
        "name": "Finnish Calendar Features",
        "sourceType": "other",
        "contentHash": digest,
        "retrievedAt": retrieved_at,
    }
