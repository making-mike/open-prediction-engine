#!/usr/bin/env python3
"""Check the local weather-transit-delay forecast prototype."""

from __future__ import annotations

from run_transit_delay_forecast import default_records


class Args:
    weather_forecast = None
    historical_delays = None
    trip_updates = None
    unresolved = False
    network = "hsl-surface"
    geography = "helsinki"
    service_window = "morning_peak"
    service_date = "2026-06-10"
    late_seconds = 300
    event_threshold = 0.2
    min_observations = 10
    generated_at = "2026-06-10T08:15:00Z"
    forecasted_at = "2026-06-10T02:00:00Z"
    forecast_close_time = "2026-06-10T02:30:00Z"
    horizon_start = "2026-06-10T03:00:00Z"
    horizon_end = "2026-06-10T07:00:00Z"
    resolve_at = "2026-06-10T08:00:00Z"


def main() -> None:
    records = default_records(Args())
    artifact = records["artifact"]
    resolution = records["resolution"]
    scoring = records["scoring"]
    summary = records["summary"]
    if artifact["domain"] != "weather-transit-delays":
        raise AssertionError("transit forecast should use the transit delay domain")
    if artifact["forecastOutput"]["probability"] <= artifact["baselineForecast"]["probability"]:
        raise AssertionError("fixture weather adjustment should lift probability above the baseline")
    if resolution["status"] != "resolved" or resolution["resolvedOutcome"]["value"] is not True:
        raise AssertionError("fixture trip updates should resolve to a Yes delay event")
    if scoring["scoreStatus"] != "scored" or scoring["baselineLift"] <= 0:
        raise AssertionError("fixture forecast should score with positive baseline lift")
    if summary["qualityClaim"]["status"] != "not_enough_resolved_transit_delay_outcomes":
        raise AssertionError("transit delay prototype must keep quality claim blocked")
    print("checked transit delay forecast prototype")


if __name__ == "__main__":
    main()
