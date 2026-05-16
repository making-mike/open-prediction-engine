#!/usr/bin/env python3
"""Resolve and score the provisional live weather-logistics fixture outcome."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from build_live_weather_baseline import build_baseline_record, load_json
from build_live_weather_evidence import build_live_evidence_bundle
from fetch_open_meteo_weather import build_url, load_fixture, normalize_response
from generate_fixture_reports import expected_calibration_error
from ope_scoring import (
    baseline_lift,
    calibration_buckets,
    score_forecast_output,
    should_exclude_resolution,
    track_record_summary,
)


ROOT = Path(__file__).resolve().parents[1]
WEATHER_FORECAST = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
BASELINE_HISTORY = ROOT / "spec" / "fixtures" / "source" / "weather-logistics-warsaw-2026-06-03" / "baseline-history.json"
OPERATIONS_OUTCOME = ROOT / "spec" / "fixtures" / "live" / "weather-logistics-warsaw-2026-06-03-operations-outcome.json"
WEATHER_OBSERVATION = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-observation-response.json"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "live-outcome"
SERVICE_DATE = "2026-06-03"
FORECAST_RETRIEVED_AT = "2026-06-02T09:30:00Z"
FORECASTED_AT = "2026-06-02T10:00:00Z"
RESOLVED_AT = "2026-06-04T10:30:00Z"
GENERATED_AT = "2026-06-04T10:35:00Z"
MIN_CALIBRATION_SAMPLE_SIZE = 30


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 10)


def build_provisional_bundle() -> dict[str, Any]:
    payload, raw = load_fixture(WEATHER_FORECAST)
    normalized_weather = normalize_response(
        payload=payload,
        raw=raw,
        source_url=build_url("warsaw", SERVICE_DATE),
        retrieved_at=FORECAST_RETRIEVED_AT,
        location_key="warsaw",
        service_date=SERVICE_DATE,
    )
    baseline = build_baseline_record(
        normalized_weather=normalized_weather,
        baseline_history=load_json(BASELINE_HISTORY),
        generated_at=FORECASTED_AT,
    )
    return build_live_evidence_bundle(
        normalized_weather=normalized_weather,
        baseline=baseline,
        forecasted_at=FORECASTED_AT,
    )


def build_history(bundle: dict[str, Any]) -> dict[str, Any]:
    baseline = bundle["baseline"]
    evidence = bundle["evidencePacket"]
    return {
        "historyId": "history-401",
        "questionId": bundle["question"]["questionId"],
        "entries": [
            {
                "forecastId": baseline["baselineForecastId"],
                "forecastedAt": baseline["generatedAt"],
                "state": "superseded",
                "sourceClass": "baseline",
                "model": {
                    "modelId": "model-400",
                    "version": "historical-frequency-live-fixture-v0",
                },
                "forecastOutput": baseline["forecastOutput"],
                "rationaleSummary": "Historical-frequency baseline generated from the weather-threshold fixture history.",
            },
            {
                "forecastId": evidence["forecastId"],
                "forecastedAt": evidence["forecastedAt"],
                "state": "active",
                "sourceClass": "model",
                "model": evidence["model"],
                "forecastOutput": evidence["forecastOutput"],
                "supersedesForecastId": baseline["baselineForecastId"],
                "rationaleSummary": evidence["rationaleSummary"],
                "evidencePacketId": evidence["evidencePacketId"],
            },
        ],
        "createdAt": baseline["generatedAt"],
        "updatedAt": evidence["forecastedAt"],
    }


def unscorable_resolution(
    bundle: dict[str, Any],
    status: str,
    reason: str,
    operations: dict[str, Any],
    weather_observation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "resolutionRecordId": "resolution-401",
        "questionId": bundle["question"]["questionId"],
        "status": status,
        "resolvedAt": RESOLVED_AT,
        "resolutionSource": operations["sourceRef"],
        "resolutionAuthority": bundle["question"]["resolutionAuthority"],
        "unscorableReason": reason,
        "supportingEvidence": [
            operations["sourceRef"]["uri"],
            weather_observation["sourceRef"]["uri"],
        ],
    }


def build_resolution(
    bundle: dict[str, Any],
    operations: dict[str, Any],
    weather_observation: dict[str, Any],
) -> dict[str, Any]:
    if operations.get("coverageStatus") != "complete":
        return unscorable_resolution(
            bundle,
            "annulled",
            "Operations outcome source does not cover the declared geography and service date.",
            operations,
            weather_observation,
        )
    observation = weather_observation["observation"]
    if weather_observation.get("sourceStatus") == "corrected":
        return unscorable_resolution(
            bundle,
            "stale_source",
            "Weather observation source was corrected after the forecast and requires review.",
            operations,
            weather_observation,
        )
    if observation.get("qualityFlag") != "complete":
        return unscorable_resolution(
            bundle,
            "ambiguous",
            "Weather observation source quality does not support a normal resolution.",
            operations,
            weather_observation,
        )

    threshold = float(bundle["baseline"]["features"]["precipitationThresholdMm"])
    disruption_seen = any(event["weatherCoded"] for event in operations["events"])
    threshold_met = float(observation["dailyPrecipitationMm"]) >= threshold
    return {
        "resolutionRecordId": "resolution-401",
        "questionId": bundle["question"]["questionId"],
        "status": "resolved",
        "resolvedAt": RESOLVED_AT,
        "resolutionSource": operations["sourceRef"],
        "resolutionAuthority": bundle["question"]["resolutionAuthority"],
        "resolvedOutcome": {
            "outputType": "binary",
            "value": bool(disruption_seen and threshold_met),
        },
        "supportingEvidence": [
            operations["sourceRef"]["uri"],
            weather_observation["sourceRef"]["uri"],
        ],
    }


def build_reports(bundle: dict[str, Any], history: dict[str, Any], resolution: dict[str, Any]) -> dict[str, Any]:
    evidence = bundle["evidencePacket"]
    if should_exclude_resolution(resolution):
        return {
            "live-weather-logistics-scoring.generated.json": {
                "scoringReportId": "scoring-401",
                "questionId": bundle["question"]["questionId"],
                "forecastId": evidence["forecastId"],
                "historyId": history["historyId"],
                "resolutionRecordId": resolution["resolutionRecordId"],
                "scoreStatus": "excluded",
                "scoringRule": "not_scored",
                "excludedReason": resolution["unscorableReason"],
                "generatedAt": GENERATED_AT,
            }
        }

    forecast_score = score_forecast_output(evidence["forecastOutput"], resolution["resolvedOutcome"], "brier")
    baseline_score = score_forecast_output(evidence["baselineForecast"], resolution["resolvedOutcome"], "brier")
    lift = baseline_lift(forecast_score, baseline_score)
    probability = evidence["forecastOutput"]["probability"]
    outcome = bool(resolution["resolvedOutcome"]["value"])
    buckets = calibration_buckets([(probability, outcome)], bucket_count=10)
    calibration_error = expected_calibration_error(buckets, 1)

    scoring = {
        "scoringReportId": "scoring-401",
        "questionId": bundle["question"]["questionId"],
        "forecastId": evidence["forecastId"],
        "historyId": history["historyId"],
        "resolutionRecordId": resolution["resolutionRecordId"],
        "scoreStatus": "scored",
        "scoringRule": "brier",
        "primaryScore": round_float(forecast_score),
        "higherIsBetter": False,
        "timeWeighting": {
            "method": "latest_only",
            "totalWeight": 1,
        },
        "baselineScore": round_float(baseline_score),
        "baselineLift": round_float(lift),
        "generatedAt": GENERATED_AT,
    }
    calibration = {
        "calibrationSummaryId": "calibration-401",
        "generatedAt": GENERATED_AT,
        "domain": bundle["question"]["domain"],
        "horizonBucket": bundle["question"]["horizon"]["label"],
        "outputType": bundle["question"]["outputType"],
        "coveragePeriod": {
            "startsAt": bundle["question"]["openAt"],
            "endsAt": resolution["resolvedAt"],
        },
        "sampleSize": 1,
        "expectedCalibrationError": round_float(calibration_error),
        "buckets": [
            {
                "lowerProbability": round_float(bucket["lowerProbability"]),
                "upperProbability": round_float(bucket["upperProbability"]),
                "count": bucket["count"],
                "meanForecastProbability": round_float(bucket["meanForecastProbability"]),
                "observedFrequency": round_float(bucket["observedFrequency"]),
            }
            for bucket in buckets
        ],
    }
    summary = track_record_summary(
        domain=bundle["question"]["domain"],
        horizon_bucket=bundle["question"]["horizon"]["label"],
        output_type=bundle["question"]["outputType"],
        scoring_rule="brier",
        scores=[forecast_score],
        baseline_scores=[baseline_score],
        n_ambiguous=0,
        n_annulled=0,
        n_forecasts=len(history["entries"]),
    )
    track_record = {
        "trackRecordReportId": "trackrecord-401",
        "generatedAt": GENERATED_AT,
        "coveragePeriod": {
            "startsAt": bundle["question"]["openAt"],
            "endsAt": resolution["resolvedAt"],
        },
        "domain": summary["domain"],
        "horizonBucket": summary["horizonBucket"],
        "outputType": summary["outputType"],
        "counts": summary["counts"],
        "summary": {
            "primaryScoringRule": summary["summary"]["primaryScoringRule"],
            "primaryScore": round_float(summary["summary"]["primaryScore"]),
            "baselineScore": round_float(summary["summary"]["baselineScore"]),
            "baselineLift": round_float(summary["summary"]["baselineLift"]),
            "calibrationError": calibration["expectedCalibrationError"],
            "lastUpdated": GENERATED_AT,
        },
        "scoreHistogram": [
            {
                "lower": 0,
                "upper": 0.5,
                "count": 1,
            }
        ],
        "slices": [],
    }
    return {
        "live-weather-logistics-scoring.generated.json": scoring,
        "live-weather-logistics-calibration.generated.json": calibration,
        "live-weather-logistics-track-record.generated.json": track_record,
    }


def build_outputs() -> dict[str, Any]:
    bundle = build_provisional_bundle()
    operations = load_json(OPERATIONS_OUTCOME)
    weather_observation = load_json(WEATHER_OBSERVATION)
    history = build_history(bundle)
    resolution = build_resolution(bundle, operations, weather_observation)
    resolved_question = deepcopy(bundle["question"])
    resolved_question["status"] = resolution["status"]
    resolved_question["updatedAt"] = resolution["resolvedAt"]

    outputs: dict[str, Any] = {
        "live-weather-logistics-question.generated.json": resolved_question,
        "live-weather-logistics-feature-snapshot.generated.json": bundle["featureSnapshot"],
        "live-weather-logistics-evidence.generated.json": bundle["evidencePacket"],
        "live-weather-logistics-artifact.generated.json": bundle["forecastArtifact"],
        "live-weather-logistics-history.generated.json": history,
        "live-weather-logistics-resolution.generated.json": resolution,
        "live-weather-logistics-outcome-summary.generated.json": {
            "publicationStatus": "provisional",
            "qualityClaimStatus": "not_enough_resolved_live_outcomes",
            "minimumCalibrationSampleSize": MIN_CALIBRATION_SAMPLE_SIZE,
            "resolvedComparableLiveOutcomes": 1 if resolution["status"] == "resolved" else 0,
            "questionId": bundle["question"]["questionId"],
            "forecastId": bundle["evidencePacket"]["forecastId"],
            "resolutionRecordId": resolution["resolutionRecordId"],
            "generatedAt": GENERATED_AT,
        },
    }
    outputs.update(build_reports(bundle, history, resolution))
    validate_outputs(outputs)
    return outputs


def validate_outputs(outputs: dict[str, Any]) -> None:
    resolution = outputs["live-weather-logistics-resolution.generated.json"]
    scoring = outputs["live-weather-logistics-scoring.generated.json"]
    if resolution["status"] == "resolved":
        if scoring["scoreStatus"] != "scored":
            raise AssertionError("resolved live outcome must be scored")
        summary = outputs["live-weather-logistics-outcome-summary.generated.json"]
        if summary["resolvedComparableLiveOutcomes"] >= summary["minimumCalibrationSampleSize"]:
            raise AssertionError("fixture live outcome should remain below calibration threshold")
    else:
        if scoring["scoreStatus"] != "excluded":
            raise AssertionError("unscorable live outcome must be excluded")

    evidence = outputs["live-weather-logistics-evidence.generated.json"]
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    if forecast_source_ids.intersection(resolution_source_ids):
        raise AssertionError("live forecast evidence must not include future resolution sources")


def write_outputs(outputs: dict[str, Any]) -> None:
    for filename, output in outputs.items():
        write_json(GENERATED / filename, output)
    print(f"generated {len(outputs)} live outcome outputs")


def check_outputs(outputs: dict[str, Any]) -> None:
    errors: list[str] = []
    for filename, output in outputs.items():
        path = GENERATED / filename
        expected = render_json(output)
        if not path.exists():
            errors.append(f"missing live outcome output: {path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"live outcome drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/resolve_live_weather_outcome.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(outputs)} live outcome outputs")


def check_unscorable_variants() -> None:
    bundle = build_provisional_bundle()
    operations = load_json(OPERATIONS_OUTCOME)
    weather_observation = load_json(WEATHER_OBSERVATION)

    missing_ops = deepcopy(operations)
    missing_ops["coverageStatus"] = "missing_declared_geography"
    if build_resolution(bundle, missing_ops, weather_observation)["status"] != "annulled":
        raise AssertionError("missing operations coverage should annul the live outcome")

    conflicting_weather = deepcopy(weather_observation)
    conflicting_weather["observation"]["qualityFlag"] = "conflicting_station_reports"
    if build_resolution(bundle, operations, conflicting_weather)["status"] != "ambiguous":
        raise AssertionError("conflicting weather observations should be ambiguous")

    corrected_weather = deepcopy(weather_observation)
    corrected_weather["sourceStatus"] = "corrected"
    if build_resolution(bundle, operations, corrected_weather)["status"] != "stale_source":
        raise AssertionError("corrected weather observations should be treated as stale_source")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated live outcome outputs")
    args = parser.parse_args()
    outputs = build_outputs()
    check_unscorable_variants()
    if args.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)


if __name__ == "__main__":
    main()
