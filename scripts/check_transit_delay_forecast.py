#!/usr/bin/env python3
"""Check the local weather-transit-delay forecast prototype."""

from __future__ import annotations

from run_transit_delay_forecast import (
    DEFAULT_TRIP_UPDATES,
    EVENT_THRESHOLD,
    LATE_SECONDS,
    MIN_OBSERVATIONS,
    default_records,
    load_rows,
    resolve_trip_updates,
)


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
    if records["summary"]["resolution"]["outOfWindowRowCount"] != 0:
        raise AssertionError("fixture trip updates should all be captured inside the resolution window")

    rows = load_rows(DEFAULT_TRIP_UPDATES)
    late_capture_rows = [{**row, "captured_at": "2026-06-11T08:38:00Z"} for row in rows]
    late_capture = resolve_trip_updates(
        late_capture_rows,
        Args.network,
        Args.geography,
        Args.service_window,
        Args.service_date,
        LATE_SECONDS,
        EVENT_THRESHOLD,
        MIN_OBSERVATIONS,
        horizon_start=Args.horizon_start,
        resolve_at=Args.resolve_at,
    )
    if late_capture["status"] != "ambiguous" or late_capture["outcome"] is not None:
        raise AssertionError("rows captured a day after resolveAt must not resolve the question")
    if late_capture["outOfWindowRowCount"] != len(rows) or late_capture["observationCount"] != 0:
        raise AssertionError("rows captured outside the resolution window must be excluded from the late ratio")
    if "outside the resolution window" not in late_capture["reason"]:
        raise AssertionError("ambiguous late-capture resolution should explain the window exclusion")
    print("checked transit delay forecast prototype")


if __name__ == "__main__":
    main()
