#!/usr/bin/env python3
"""Check deterministic baseline generation for fixture-mode live weather input."""

from __future__ import annotations

import json
from pathlib import Path

from build_live_weather_baseline import build_baseline_record, load_json
from fetch_open_meteo_weather import build_url, load_fixture, normalize_response


ROOT = Path(__file__).resolve().parents[1]
WEATHER_FIXTURE = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
BASELINE_HISTORY = ROOT / "spec" / "fixtures" / "source" / "weather-logistics-warsaw-2026-06-03" / "baseline-history.json"
SERVICE_DATE = "2026-06-03"
RETRIEVED_AT = "2026-06-02T09:30:00Z"
GENERATED_AT = "2026-06-02T09:31:00Z"


def main() -> None:
    payload, raw = load_fixture(WEATHER_FIXTURE)
    normalized_weather = normalize_response(
        payload=payload,
        raw=raw,
        source_url=build_url("warsaw", SERVICE_DATE),
        retrieved_at=RETRIEVED_AT,
        location_key="warsaw",
        service_date=SERVICE_DATE,
    )
    baseline = build_baseline_record(
        normalized_weather=normalized_weather,
        baseline_history=load_json(BASELINE_HISTORY),
        generated_at=GENERATED_AT,
    )
    if baseline["forecastOutput"]["probability"] != 0.22:
        raise AssertionError("live weather baseline probability drifted")
    if baseline["features"]["forecastExceedsThreshold"] is not True:
        raise AssertionError("baseline should preserve threshold feature")
    source_types = {source["sourceType"] for source in baseline["sourceRefs"]}
    if source_types != {"public_dataset", "internal_dataset"}:
        raise AssertionError("baseline should bind public weather and internal baseline sources")
    json.dumps(baseline)
    print("checked live weather baseline fixture mode")


if __name__ == "__main__":
    main()
