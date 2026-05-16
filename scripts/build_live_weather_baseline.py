#!/usr/bin/env python3
"""Build a deterministic weather-logistics baseline from normalized live weather input."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fetch_open_meteo_weather import build_url, load_fixture, normalize_response


DEFAULT_THRESHOLD_MM = 20.0


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def baseline_probability(baseline_history: dict[str, Any]) -> float:
    comparable_days = int(baseline_history["comparableServiceDays"])
    if comparable_days <= 0:
        raise ValueError("baseline comparableServiceDays must be positive")
    return round(float(baseline_history["disruptionDays"]) / comparable_days, 2)


def build_baseline_record(
    *,
    normalized_weather: dict[str, Any],
    baseline_history: dict[str, Any],
    generated_at: str,
    precipitation_threshold_mm: float = DEFAULT_THRESHOLD_MM,
) -> dict[str, Any]:
    fields = normalized_weather["normalizedFields"]
    forecast_precipitation = float(fields["forecastDailyPrecipitationMm"])
    if forecast_precipitation < precipitation_threshold_mm:
        raise ValueError("baseline fixture only covers daily_precipitation_gte_20mm")
    probability = baseline_probability(baseline_history)
    return {
        "baselineForecastId": "forecast-401",
        "generatedAt": generated_at,
        "domain": "weather-logistics",
        "geography": normalized_weather["geography"],
        "serviceDate": normalized_weather["serviceDate"],
        "method": "historical_frequency_by_weather_threshold",
        "forecastOutput": {
            "outputType": "binary",
            "probability": probability,
        },
        "sourceRefs": [
            normalized_weather["sourceRef"],
            baseline_history["sourceRef"],
        ],
        "features": {
            "forecastDailyPrecipitationMm": forecast_precipitation,
            "precipitationThresholdMm": precipitation_threshold_mm,
            "forecastExceedsThreshold": True,
            "weatherThresholdBucket": baseline_history["weatherThresholdBucket"],
            "lookbackStartsAt": baseline_history["lookbackStartsAt"],
            "lookbackEndsAt": baseline_history["lookbackEndsAt"],
            "comparableServiceDays": baseline_history["comparableServiceDays"],
            "disruptionDays": baseline_history["disruptionDays"],
            "smoothing": baseline_history["smoothing"],
        },
        "limitations": [
            "Fixture baseline only; not a calibrated live performance claim.",
            "Applies only to the declared geography, threshold bucket, and lookback window.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-fixture", type=Path, required=True)
    parser.add_argument("--baseline-history", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    payload, raw = load_fixture(args.weather_fixture)
    normalized_weather = normalize_response(
        payload=payload,
        raw=raw,
        source_url=build_url("warsaw", args.service_date),
        retrieved_at=args.retrieved_at,
        location_key="warsaw",
        service_date=args.service_date,
    )
    baseline = build_baseline_record(
        normalized_weather=normalized_weather,
        baseline_history=load_json(args.baseline_history),
        generated_at=args.generated_at,
    )
    output = json.dumps(baseline, indent=2, sort_keys=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
