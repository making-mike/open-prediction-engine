#!/usr/bin/env python3
"""Check provisional live weather evidence generation in fixture mode."""

from __future__ import annotations

import json
from pathlib import Path

from build_live_weather_baseline import build_baseline_record, load_json
from build_live_weather_evidence import build_live_evidence_bundle
from fetch_open_meteo_weather import build_url, load_fixture, normalize_response


ROOT = Path(__file__).resolve().parents[1]
WEATHER_FIXTURE = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
BASELINE_HISTORY = ROOT / "spec" / "fixtures" / "source" / "weather-logistics-warsaw-2026-06-03" / "baseline-history.json"
SERVICE_DATE = "2026-06-03"
RETRIEVED_AT = "2026-06-02T09:30:00Z"
FORECASTED_AT = "2026-06-02T10:00:00Z"


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
        generated_at=FORECASTED_AT,
    )
    bundle = build_live_evidence_bundle(
        normalized_weather=normalized_weather,
        baseline=baseline,
        forecasted_at=FORECASTED_AT,
    )
    if bundle["publicationStatus"] != "provisional":
        raise AssertionError("live evidence bundle must remain provisional")
    if bundle["resolvedComparableLiveOutcomes"] != 0:
        raise AssertionError("prototype live evidence must not claim resolved live outcomes")
    evidence = bundle["evidencePacket"]
    if evidence["forecastOutput"]["probability"] != 0.41:
        raise AssertionError("live deterministic model probability drifted")
    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    if forecast_source_ids.intersection(resolution_source_ids):
        raise AssertionError("live evidence must not include future resolution sources as forecast inputs")
    json.dumps(bundle)
    print("checked live weather evidence fixture mode")


if __name__ == "__main__":
    main()
