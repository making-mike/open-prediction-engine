#!/usr/bin/env python3
"""Build a provisional live weather-logistics evidence bundle in fixture mode."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from build_live_weather_baseline import build_baseline_record, load_json
from fetch_open_meteo_weather import build_url, load_fixture, normalize_response


def model_probability(baseline: dict[str, Any]) -> float:
    probability = float(baseline["forecastOutput"]["probability"])
    adjustment = 0.19 if baseline["features"]["forecastExceedsThreshold"] else -0.07
    return round(min(0.95, max(0.01, probability + adjustment)), 2)


def horizon_for_service_date(service_date: str) -> dict[str, str]:
    return {
        "startsAt": f"{service_date}T00:00:00Z",
        "endsAt": f"{service_date}T23:59:59Z",
        "label": "1-day",
    }


def resolution_time_for_service_date(service_date: str) -> str:
    return f"{date.fromisoformat(service_date) + timedelta(days=1)}T12:00:00Z"


def resolution_criteria(geography: str, service_date: str, threshold: float) -> str:
    return (
        "Resolve Yes if the declared operations source reports at least one weather-coded "
        f"delivery disruption in {geography} on {service_date} and the declared weather "
        f"observation source records daily precipitation of at least {threshold:g} millimeters. "
        "Resolve No otherwise."
    )


def build_live_evidence_bundle(
    *,
    normalized_weather: dict[str, Any],
    baseline: dict[str, Any],
    forecasted_at: str,
) -> dict[str, Any]:
    service_date = normalized_weather["serviceDate"]
    geography = normalized_weather["geography"]
    threshold = float(baseline["features"]["precipitationThresholdMm"])
    horizon = horizon_for_service_date(service_date)
    operations_source = {
        "sourceId": "source-402",
        "name": "Declared Warsaw operations event source",
        "sourceType": "internal_dataset",
    }
    weather_observation_source = {
        "sourceId": "source-403",
        "name": "Open-Meteo weather observation for Warsaw",
        "sourceType": "public_dataset",
    }
    forecast_output = {
        "outputType": "binary",
        "probability": model_probability(baseline),
    }
    question = {
        "questionId": "question-401",
        "title": f"Will heavy rain disrupt last-mile delivery operations in {geography} on {service_date}?",
        "background": "Provisional live-data prototype question for the selected weather-logistics wedge.",
        "domain": "weather-logistics",
        "outputType": "binary",
        "status": "open",
        "openAt": forecasted_at,
        "closeAt": f"{service_date}T00:00:00Z",
        "resolveAt": resolution_time_for_service_date(service_date),
        "horizon": horizon,
        "resolutionCriteria": resolution_criteria(geography, service_date, threshold),
        "resolutionAuthority": "OPE prototype resolver",
        "resolutionMode": "automated_measurement",
        "primaryResolutionSource": operations_source,
        "fallbackResolutionSources": [weather_observation_source],
        "validOutcomeSpace": {
            "description": "Binary outcome: Yes if disruption and precipitation criteria are both satisfied; No otherwise.",
            "labels": ["yes", "no"],
        },
        "clarificationHistory": [],
        "incentiveRiskReview": {
            "riskLevel": "minimal",
            "notes": "Prototype public-weather input with unresolved operations outcome.",
        },
        "createdAt": forecasted_at,
        "updatedAt": forecasted_at,
    }
    feature_snapshot = {
        "featureSnapshotId": "featuresnapshot-401",
        "questionId": question["questionId"],
        "generatedAt": forecasted_at,
        "domain": "weather-logistics",
        "horizon": horizon,
        "sourceIds": [source["sourceId"] for source in baseline["sourceRefs"]],
        "features": baseline["features"],
    }
    evidence_packet = {
        "evidencePacketId": "evidence-401",
        "forecastId": "forecast-402",
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": "weather-logistics",
        "horizon": horizon,
        "forecastedAt": forecasted_at,
        "model": {
            "modelId": "model-401",
            "version": "weather-logistics-threshold-fixture-live-v0",
            "configurationHash": "sha256-live-prototype-model-001",
        },
        "inputSourceClasses": ["public_dataset", "internal_dataset"],
        "provenanceReferences": baseline["sourceRefs"],
        "featureSnapshotRef": "https://example.test/fixtures/live/weather-logistics-live-feature-snapshot.json",
        "forecastOutput": forecast_output,
        "baselineForecast": baseline["forecastOutput"],
        "rationaleSummary": "Provisional deterministic model raises the baseline when public weather input crosses the declared heavy-rain threshold.",
        "keyFactors": [
            f"forecast precipitation {baseline['features']['forecastDailyPrecipitationMm']} mm",
            f"threshold {threshold:g} mm",
            f"baseline disruption rate {baseline['forecastOutput']['probability']}",
            "no resolved live outcome yet",
        ],
        "resolutionCriteria": question["resolutionCriteria"],
        "resolutionSource": operations_source,
        "fallbackResolutionSources": [weather_observation_source],
        "scheduledResolutionAt": question["resolveAt"],
    }
    forecast_artifact = {
        "forecastId": evidence_packet["forecastId"],
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": "weather-logistics",
        "horizon": horizon,
        "forecastedAt": forecasted_at,
        "closedAt": question["closeAt"],
        "outputType": "binary",
        "forecastOutput": forecast_output,
        "baselineForecast": baseline["forecastOutput"],
        "model": evidence_packet["model"],
        "evidencePacketId": evidence_packet["evidencePacketId"],
        "resolutionPlan": {
            "resolutionCriteria": question["resolutionCriteria"],
            "resolutionAuthority": question["resolutionAuthority"],
            "primaryResolutionSource": operations_source,
            "fallbackResolutionSources": [weather_observation_source],
            "scheduledResolutionAt": question["resolveAt"],
        },
    }
    return {
        "publicationStatus": "provisional",
        "qualityClaimStatus": "not_enough_resolved_live_outcomes",
        "minimumCalibrationSampleSize": 30,
        "resolvedComparableLiveOutcomes": 0,
        "question": question,
        "featureSnapshot": feature_snapshot,
        "baseline": baseline,
        "evidencePacket": evidence_packet,
        "forecastArtifact": forecast_artifact,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-fixture", type=Path, required=True)
    parser.add_argument("--baseline-history", type=Path, required=True)
    parser.add_argument("--service-date", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--forecasted-at", required=True)
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
        generated_at=args.forecasted_at,
    )
    bundle = build_live_evidence_bundle(
        normalized_weather=normalized_weather,
        baseline=baseline,
        forecasted_at=args.forecasted_at,
    )
    output = json.dumps(bundle, indent=2, sort_keys=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
