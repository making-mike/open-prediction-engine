#!/usr/bin/env python3
"""Run a local weather-transit-delay forecast from approved CSV/JSON files."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_scoring import baseline_lift, binary_brier


ROOT = Path(__file__).resolve().parents[1]
LOCAL_FIXTURES = ROOT / "spec" / "fixtures" / "local-source-files"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-delay-forecast"

DOMAIN = "weather-transit-delays"
GENERATED_AT = "2026-06-10T08:15:00Z"
FORECASTED_AT = "2026-06-10T02:00:00Z"
FORECAST_CLOSE_TIME = "2026-06-10T02:30:00Z"
SERVICE_DATE = "2026-06-10"
NETWORK = "hsl-surface"
GEOGRAPHY = "helsinki"
SERVICE_WINDOW = "morning_peak"
HORIZON_START = "2026-06-10T03:00:00Z"
HORIZON_END = "2026-06-10T07:00:00Z"
RESOLVE_AT = "2026-06-10T08:00:00Z"
LATE_SECONDS = 300
EVENT_THRESHOLD = 0.2
MIN_OBSERVATIONS = 10

DEFAULT_WEATHER = LOCAL_FIXTURES / "transit-weather-forecast.json"
DEFAULT_HISTORY = LOCAL_FIXTURES / "transit-delay-history.csv"
DEFAULT_TRIP_UPDATES = LOCAL_FIXTURES / "transit-trip-updates.csv"

OUTPUT_NAMES = {
    "question": "weather-transit-delays-question.generated.json",
    "evidence": "weather-transit-delays-evidence.generated.json",
    "artifact": "weather-transit-delays-artifact.generated.json",
    "history": "weather-transit-delays-history.generated.json",
    "resolution": "weather-transit-delays-resolution.generated.json",
    "scoring": "weather-transit-delays-scoring.generated.json",
    "summary": "weather-transit-delays-run-summary.generated.json",
}


class TransitForecastError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def normalize_key(value: str) -> str:
    lowered = value.strip().lower()
    chars = [char if char.isalnum() else "_" for char in lowered]
    normalized = "_".join(filter(None, "".join(chars).split("_")))
    return normalized or "field"


def normalize_text(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = normalize_text(value)
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    return None


def parse_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_time(value: str) -> datetime:
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise TransitForecastError(f"missing source file: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [{normalize_key(key): value for key, value in row.items()} for row in csv.DictReader(handle)]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("records"), list):
            data = data["records"]
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise TransitForecastError("JSON source must be an array of objects or an object with a records array")
        return [{normalize_key(str(key)): value for key, value in item.items()} for item in data]
    raise TransitForecastError(f"unsupported source format: {path}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_uri(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        rel = path.resolve()
    normalized = str(rel).replace("\\", "/")
    return f"local://{normalized}"


def source_ref(source_id: str, name: str, source_type: str, path: Path, retrieved_at: str | None = None) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "sourceId": source_id,
        "name": name,
        "sourceType": source_type,
        "uri": local_uri(path),
        "contentHash": sha256(path),
    }
    if retrieved_at is not None:
        ref["retrievedAt"] = retrieved_at
    return ref


def matches_scope(row: dict[str, Any], network: str, geography: str, service_window: str, service_date: str | None = None) -> bool:
    if row.get("network") is not None and normalize_text(row["network"]) != normalize_text(network):
        return False
    if row.get("geography") is not None and normalize_text(row["geography"]) != normalize_text(geography):
        return False
    if row.get("service_window") is not None and normalize_text(row["service_window"]) != normalize_text(service_window):
        return False
    if service_date is not None and row.get("service_date") is not None and str(row["service_date"]).strip() != service_date:
        return False
    return True


def weather_features(
    rows: list[dict[str, Any]],
    network: str,
    geography: str,
    service_window: str,
    service_date: str,
    forecast_close_time: str,
) -> dict[str, Any]:
    scoped = [row for row in rows if matches_scope(row, network, geography, service_window, service_date)]
    if not scoped:
        raise TransitForecastError("weather source has no row for the requested network/geography/window/date")
    row = scoped[0]
    retrieved_at = row.get("retrieved_at")
    if retrieved_at is None:
        raise TransitForecastError("weather source must include retrieved_at")
    if parse_time(str(retrieved_at)) > parse_time(forecast_close_time):
        raise TransitForecastError("weather source retrieved_at is after forecast close")
    precipitation = first_number(row, ["forecast_precipitation_mm", "precipitation_mm", "rain_mm"], 0.0)
    snowfall = first_number(row, ["forecast_snowfall_mm", "snowfall_mm"], 0.0)
    wind_gust = first_number(row, ["forecast_wind_gust_kmh", "wind_gust_kmh"], 0.0)
    temperature = first_number(row, ["temperature_c", "temp_c"], None)
    return {
        "retrievedAt": str(retrieved_at),
        "forecastPrecipitationMm": precipitation,
        "forecastSnowfallMm": snowfall,
        "forecastWindGustKmh": wind_gust,
        "temperatureC": temperature,
    }


def first_number(row: dict[str, Any], names: list[str], default: float | None) -> float | None:
    for name in names:
        value = parse_float(row.get(name))
        if value is not None:
            return value
    return default


def historical_outcome(row: dict[str, Any], event_threshold: float) -> bool | None:
    explicit = parse_bool(row.get("delay_event"))
    if explicit is not None:
        return explicit
    ratio = parse_float(row.get("late_observation_ratio"))
    if ratio is not None:
        return ratio >= event_threshold
    return None


def baseline_from_history(
    rows: list[dict[str, Any]],
    network: str,
    geography: str,
    service_window: str,
    event_threshold: float,
) -> dict[str, Any]:
    scoped = [row for row in rows if matches_scope(row, network, geography, service_window)]
    outcomes = [historical_outcome(row, event_threshold) for row in scoped]
    outcomes = [outcome for outcome in outcomes if outcome is not None]
    if not outcomes:
        raise TransitForecastError("historical delay source has no resolvable outcomes for the requested scope")
    positives = sum(1 for outcome in outcomes if outcome)
    row_count = len(outcomes)
    probability = round((positives + 1.0) / (row_count + 2.0), 4)
    return {
        "rowCount": row_count,
        "positiveOutcomeCount": positives,
        "probability": probability,
        "smoothing": "laplace_add_one",
    }


def weather_adjustment(features: dict[str, Any]) -> tuple[float, list[str]]:
    adjustment = 0.0
    factors: list[str] = []
    precipitation = float(features["forecastPrecipitationMm"] or 0.0)
    snowfall = float(features["forecastSnowfallMm"] or 0.0)
    wind_gust = float(features["forecastWindGustKmh"] or 0.0)
    temperature = features.get("temperatureC")
    if precipitation >= 5:
        adjustment += 0.08
        factors.append(f"forecast precipitation {precipitation:g} mm")
    if precipitation >= 10:
        adjustment += 0.07
        factors.append("precipitation crosses 10 mm beta bucket")
    if snowfall >= 1:
        adjustment += 0.1
        factors.append(f"forecast snowfall {snowfall:g} mm")
    if wind_gust >= 50:
        adjustment += 0.06
        factors.append(f"forecast wind gust {wind_gust:g} km/h")
    if temperature is not None and (float(temperature) <= -5 or float(temperature) >= 30):
        adjustment += 0.04
        factors.append(f"temperature stress {float(temperature):g} C")
    if not factors:
        factors.append("no beta weather stress bucket crossed")
    return round(adjustment, 4), factors


def forecast_probability(baseline: float, adjustment: float) -> float:
    return round(min(0.95, max(0.01, baseline + adjustment)), 4)


def resolve_trip_updates(
    rows: list[dict[str, Any]],
    network: str,
    geography: str,
    service_window: str,
    service_date: str,
    late_seconds: int,
    event_threshold: float,
    min_observations: int,
) -> dict[str, Any]:
    scoped = [row for row in rows if matches_scope(row, network, geography, service_window, service_date)]
    delays = [parse_float(row.get("delay_seconds")) for row in scoped]
    delays = [delay for delay in delays if delay is not None]
    observation_count = len(delays)
    late_count = sum(1 for delay in delays if delay >= late_seconds)
    late_ratio = round(late_count / observation_count, 4) if observation_count else 0.0
    if observation_count < min_observations:
        return {
            "status": "ambiguous",
            "observationCount": observation_count,
            "lateCount": late_count,
            "lateRatio": late_ratio,
            "outcome": None,
            "reason": "transit outcome feed did not meet the minimum observation count",
        }
    return {
        "status": "resolved",
        "observationCount": observation_count,
        "lateCount": late_count,
        "lateRatio": late_ratio,
        "outcome": late_ratio >= event_threshold,
        "reason": "coverage checks passed",
    }


def horizon(horizon_start: str, horizon_end: str, service_window: str) -> dict[str, Any]:
    return {
        "startsAt": horizon_start,
        "endsAt": horizon_end,
        "label": f"same-day-{normalize_text(service_window).replace('_', '-')}",
    }


def resolution_criteria(network: str, geography: str, service_window: str, service_date: str, late_seconds: int, event_threshold: float, min_observations: int) -> str:
    threshold_percent = int(event_threshold * 100)
    return (
        f"Resolve Yes if collected GTFS-RT TripUpdates or equivalent transit delay rows for {network} in "
        f"{geography} during {service_window} on {service_date} include at least {min_observations} eligible "
        f"trip-stop observations and at least {threshold_percent}% have delay_seconds >= {late_seconds}. "
        "Resolve No if coverage passes and the ratio is below threshold. Resolve Ambiguous if coverage fails."
    )


def build_records(
    *,
    weather_path: Path,
    history_path: Path,
    trip_updates_path: Path | None,
    network: str,
    geography: str,
    service_window: str,
    service_date: str,
    late_seconds: int,
    event_threshold: float,
    min_observations: int,
    generated_at: str,
    forecasted_at: str,
    forecast_close_time: str,
    horizon_start: str,
    horizon_end: str,
    resolve_at: str,
) -> dict[str, Any]:
    weather = weather_features(
        load_rows(weather_path),
        network,
        geography,
        service_window,
        service_date,
        forecast_close_time,
    )
    baseline = baseline_from_history(load_rows(history_path), network, geography, service_window, event_threshold)
    adjustment, factors = weather_adjustment(weather)
    probability = forecast_probability(float(baseline["probability"]), adjustment)

    weather_ref = source_ref("source-1201", "Transit Weather Forecast File", "public_dataset", weather_path, weather["retrievedAt"])
    history_ref = source_ref("source-1202", "Historical Transit Delay File", "public_dataset", history_path, forecasted_at)
    if trip_updates_path is None:
        outcome_ref = {
            "sourceId": "source-1203",
            "name": "Transit Delay Outcome File",
            "sourceType": "public_dataset",
        }
    else:
        outcome_ref = source_ref(
            "source-1203",
            "Transit Delay Outcome File",
            "public_dataset",
            trip_updates_path,
            generated_at,
        )
    criteria = resolution_criteria(network, geography, service_window, service_date, late_seconds, event_threshold, min_observations)
    title = (
        f"Will {network} in {geography} exceed the beta delay threshold during "
        f"{service_window} on {service_date}?"
    )
    question = {
        "questionId": "question-1201",
        "title": title,
        "background": "Generated by the local weather-transit-delays custom-file prototype.",
        "domain": DOMAIN,
        "outputType": "binary",
        "status": "open",
        "openAt": forecasted_at,
        "closeAt": forecast_close_time,
        "resolveAt": resolve_at,
        "horizon": horizon(horizon_start, horizon_end, service_window),
        "resolutionCriteria": criteria,
        "resolutionAuthority": "OPE local transit delay resolver",
        "resolutionMode": "automated_measurement",
        "primaryResolutionSource": outcome_ref,
        "fallbackResolutionSources": [],
        "validOutcomeSpace": {
            "description": "Binary outcome: Yes if the network late-observation ratio meets the declared threshold; No otherwise.",
            "labels": ["yes", "no"],
        },
        "clarificationHistory": [],
        "incentiveRiskReview": {
            "riskLevel": "minimal",
            "notes": "Local public-transit delay fixture prototype; no passenger-level, fare, enforcement, or public-safety use.",
        },
        "createdAt": forecasted_at,
        "updatedAt": forecasted_at,
    }
    model = {
        "modelId": "model-1201",
        "version": "weather-transit-delay-local-baseline-v0",
        "trainingCutoff": forecast_close_time,
        "configurationHash": "sha256-transit-delay-local-baseline-v0",
    }
    forecast_output = {"outputType": "binary", "probability": probability}
    baseline_output = {"outputType": "binary", "probability": baseline["probability"]}
    evidence = {
        "evidencePacketId": "evidence-1201",
        "forecastId": "forecast-1201",
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": DOMAIN,
        "horizon": question["horizon"],
        "forecastedAt": forecasted_at,
        "model": model,
        "inputSourceClasses": ["public_dataset"],
        "provenanceReferences": [weather_ref, history_ref],
        "featureSnapshotRef": "https://example.test/fixtures/generated/transit-delay-forecast/weather-transit-delays-feature-snapshot.generated.json",
        "forecastOutput": forecast_output,
        "baselineForecast": baseline_output,
        "calibrationBand": {
            "lower": round(max(0.0, probability - 0.15), 4),
            "upper": round(min(1.0, probability + 0.15), 4),
            "coverage": 0.8,
            "sampleSize": baseline["rowCount"],
        },
        "rationaleSummary": (
            "Local beta method starts from a Laplace-smoothed historical delay-event frequency and applies a "
            "transparent weather stress adjustment. It is runnable for custom local files but is not calibrated."
        ),
        "keyFactors": [
            f"historical comparable windows {baseline['rowCount']}",
            f"historical delay events {baseline['positiveOutcomeCount']}",
            f"baseline probability {baseline['probability']}",
            f"weather adjustment {adjustment}",
            *factors[:6],
            "resolution source excluded from forecast-time evidence",
        ][:12],
        "resolutionCriteria": criteria,
        "resolutionSource": outcome_ref,
        "fallbackResolutionSources": [],
        "scheduledResolutionAt": resolve_at,
    }
    artifact = {
        "forecastId": evidence["forecastId"],
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": DOMAIN,
        "horizon": question["horizon"],
        "forecastedAt": forecasted_at,
        "closedAt": forecast_close_time,
        "outputType": "binary",
        "forecastOutput": forecast_output,
        "baselineForecast": baseline_output,
        "model": model,
        "evidencePacketId": evidence["evidencePacketId"],
        "resolutionPlan": {
            "resolutionCriteria": criteria,
            "resolutionAuthority": question["resolutionAuthority"],
            "primaryResolutionSource": outcome_ref,
            "fallbackResolutionSources": [],
            "scheduledResolutionAt": resolve_at,
        },
    }
    history = {
        "historyId": "history-1201",
        "questionId": question["questionId"],
        "entries": [
            {
                "forecastId": artifact["forecastId"],
                "forecastedAt": forecasted_at,
                "state": "active",
                "sourceClass": "model",
                "model": model,
                "forecastOutput": forecast_output,
                "rationaleSummary": evidence["rationaleSummary"],
                "evidencePacketId": evidence["evidencePacketId"],
            }
        ],
        "createdAt": forecasted_at,
        "updatedAt": forecasted_at,
    }
    records: dict[str, Any] = {
        "question": question,
        "evidence": evidence,
        "artifact": artifact,
        "history": history,
    }
    resolution_summary = None
    if trip_updates_path is not None:
        resolution_summary = resolve_trip_updates(
            load_rows(trip_updates_path),
            network,
            geography,
            service_window,
            service_date,
            late_seconds,
            event_threshold,
            min_observations,
        )
        if resolution_summary["status"] == "resolved":
            resolution = {
                "resolutionRecordId": "resolution-1201",
                "questionId": question["questionId"],
                "status": "resolved",
                "resolvedAt": generated_at,
                "resolutionSource": outcome_ref,
                "resolutionAuthority": question["resolutionAuthority"],
                "resolvedOutcome": {
                    "outputType": "binary",
                    "value": bool(resolution_summary["outcome"]),
                },
                "supportingEvidence": [local_uri(trip_updates_path)],
            }
            primary_score = round(binary_brier(probability, bool(resolution_summary["outcome"])), 6)
            baseline_score = round(binary_brier(float(baseline["probability"]), bool(resolution_summary["outcome"])), 6)
            scoring = {
                "scoringReportId": "scoring-1201",
                "questionId": question["questionId"],
                "forecastId": artifact["forecastId"],
                "historyId": history["historyId"],
                "resolutionRecordId": resolution["resolutionRecordId"],
                "scoreStatus": "scored",
                "scoringRule": "brier",
                "primaryScore": primary_score,
                "higherIsBetter": False,
                "timeWeighting": {
                    "method": "latest_only",
                    "totalWeight": 1.0,
                },
                "baselineScore": baseline_score,
                "baselineLift": round(baseline_lift(primary_score, baseline_score), 6),
                "generatedAt": generated_at,
            }
        else:
            resolution = {
                "resolutionRecordId": "resolution-1201",
                "questionId": question["questionId"],
                "status": "ambiguous",
                "resolvedAt": generated_at,
                "resolutionSource": outcome_ref,
                "resolutionAuthority": question["resolutionAuthority"],
                "unscorableReason": str(resolution_summary["reason"]),
                "supportingEvidence": [local_uri(trip_updates_path)],
            }
            scoring = {
                "scoringReportId": "scoring-1201",
                "questionId": question["questionId"],
                "forecastId": artifact["forecastId"],
                "historyId": history["historyId"],
                "resolutionRecordId": resolution["resolutionRecordId"],
                "scoreStatus": "excluded",
                "scoringRule": "not_scored",
                "excludedReason": str(resolution_summary["reason"]),
                "generatedAt": generated_at,
            }
        records["resolution"] = resolution
        records["scoring"] = scoring

    records["summary"] = build_summary(records, baseline, weather, resolution_summary, generated_at)
    validate_records(records)
    return records


def output_path(name: str, output_dir: Path) -> Path:
    return output_dir / OUTPUT_NAMES[name]


def build_summary(
    records: dict[str, Any],
    baseline: dict[str, Any],
    weather: dict[str, Any],
    resolution_summary: dict[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    artifact = records["artifact"]
    scoring = records.get("scoring")
    return {
        "runId": "transitdelayrun-1201",
        "generatedAt": generated_at,
        "domain": DOMAIN,
        "runStatus": "completed",
        "forecastId": artifact["forecastId"],
        "questionId": artifact["questionId"],
        "forecast": artifact["forecastOutput"],
        "baseline": artifact["baselineForecast"],
        "sourceSummary": {
            "historicalComparableWindows": baseline["rowCount"],
            "historicalPositiveOutcomes": baseline["positiveOutcomeCount"],
            "weatherRetrievedAt": weather["retrievedAt"],
            "forecastPrecipitationMm": weather["forecastPrecipitationMm"],
            "forecastSnowfallMm": weather["forecastSnowfallMm"],
            "forecastWindGustKmh": weather["forecastWindGustKmh"],
        },
        "resolution": resolution_summary,
        "score": scoring,
        "qualityClaim": {
            "status": "not_enough_resolved_transit_delay_outcomes",
            "minimumSampleSize": 100,
            "resolvedComparableOutcomes": 1 if scoring and scoring["scoreStatus"] == "scored" else 0,
        },
        "warnings": [
            "Local custom-file prototype only; live connector outputs must be passed explicitly as approved files.",
            "Weather adjustment is transparent beta logic, not a calibrated causal claim.",
            "Resolution rows are excluded from forecast-time provenance.",
        ],
    }


def validate_records(records: dict[str, Any]) -> None:
    schemas = {
        "question": "forecast-question.schema.json",
        "evidence": "evidence-packet.schema.json",
        "artifact": "forecast-artifact.schema.json",
        "history": "forecast-history.schema.json",
        "resolution": "resolution-record.schema.json",
        "scoring": "scoring-report.schema.json",
    }
    for name, schema_name in schemas.items():
        if name not in records:
            continue
        errors = validate_record(records[name], SPEC / schema_name)
        if errors:
            raise TransitForecastError(f"{name} failed schema validation: {errors[0]}")

    if records["artifact"]["forecastId"] != records["evidence"]["forecastId"]:
        raise TransitForecastError("forecast artifact and evidence packet must bind the same forecast")
    if records["artifact"]["questionId"] != records["question"]["questionId"]:
        raise TransitForecastError("forecast artifact and question must bind the same question")
    if records["history"]["entries"][-1]["forecastId"] != records["artifact"]["forecastId"]:
        raise TransitForecastError("forecast history must end with the generated forecast")
    forecast_sources = {item["sourceId"] for item in records["evidence"]["provenanceReferences"]}
    resolution_source = records["question"]["primaryResolutionSource"]["sourceId"]
    if resolution_source in forecast_sources:
        raise TransitForecastError("resolution source must not be included in forecast-time provenance")


def write_outputs(records: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = {OUTPUT_NAMES[name] for name in records}
    for path in output_dir.glob("*.generated.json"):
        if path.name not in expected:
            path.unlink()
    for name, record in records.items():
        output_path(name, output_dir).write_text(render_json(record), encoding="utf-8")
    print(f"generated {len(records)} transit delay forecast outputs")


def check_outputs(records: dict[str, Any], output_dir: Path) -> None:
    errors: list[str] = []
    expected = {OUTPUT_NAMES[name] for name in records}
    for path in sorted(output_dir.glob("*.generated.json")):
        if path.name not in expected:
            errors.append(f"stale transit delay forecast output: {path}")
    for name, record in records.items():
        path = output_path(name, output_dir)
        if not path.exists():
            errors.append(f"missing transit delay forecast output: {path}")
            continue
        if path.read_text(encoding="utf-8") != render_json(record):
            errors.append(f"transit delay forecast drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/run_transit_delay_forecast.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(records)} transit delay forecast outputs")


def default_records(args: argparse.Namespace) -> dict[str, Any]:
    weather = Path(args.weather_forecast or DEFAULT_WEATHER)
    history = Path(args.historical_delays or DEFAULT_HISTORY)
    trip_updates = None if args.unresolved else Path(args.trip_updates) if args.trip_updates else DEFAULT_TRIP_UPDATES
    if not weather.is_absolute():
        weather = ROOT / weather
    if not history.is_absolute():
        history = ROOT / history
    if trip_updates is not None and not trip_updates.is_absolute():
        trip_updates = ROOT / trip_updates
    return build_records(
        weather_path=weather,
        history_path=history,
        trip_updates_path=trip_updates,
        network=args.network,
        geography=args.geography,
        service_window=args.service_window,
        service_date=args.service_date,
        late_seconds=args.late_seconds,
        event_threshold=args.event_threshold,
        min_observations=args.min_observations,
        generated_at=args.generated_at,
        forecasted_at=args.forecasted_at,
        forecast_close_time=args.forecast_close_time,
        horizon_start=args.horizon_start,
        horizon_end=args.horizon_end,
        resolve_at=args.resolve_at,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weather-forecast", help="approved CSV/JSON weather forecast source")
    parser.add_argument("--historical-delays", help="approved CSV/JSON historical delay source")
    parser.add_argument("--trip-updates", help="approved CSV/JSON transit outcome rows; omit with --unresolved")
    parser.add_argument("--unresolved", action="store_true", help="emit forecast records without resolution/scoring")
    parser.add_argument("--network", default=NETWORK)
    parser.add_argument("--geography", default=GEOGRAPHY)
    parser.add_argument("--service-window", default=SERVICE_WINDOW)
    parser.add_argument("--service-date", default=SERVICE_DATE)
    parser.add_argument("--late-seconds", type=int, default=LATE_SECONDS)
    parser.add_argument("--event-threshold", type=float, default=EVENT_THRESHOLD)
    parser.add_argument("--min-observations", type=int, default=MIN_OBSERVATIONS)
    parser.add_argument("--generated-at", default=GENERATED_AT)
    parser.add_argument("--forecasted-at", default=FORECASTED_AT)
    parser.add_argument("--forecast-close-time", default=FORECAST_CLOSE_TIME)
    parser.add_argument("--horizon-start", default=HORIZON_START)
    parser.add_argument("--horizon-end", default=HORIZON_END)
    parser.add_argument("--resolve-at", default=RESOLVE_AT)
    parser.add_argument("--output-dir", default=str(GENERATED))
    parser.add_argument("--check", action="store_true", help="check generated transit delay forecast drift")
    parser.add_argument("--write", action="store_true", help="write generated transit delay forecast outputs")
    args = parser.parse_args()
    if args.unresolved:
        args.trip_updates = None
    try:
        records = default_records(args)
    except (OSError, json.JSONDecodeError, csv.Error, TransitForecastError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir
    if args.write:
        write_outputs(records, output_dir)
    elif args.check:
        check_outputs(records, output_dir)
    else:
        print(render_json(records["summary"]), end="")


if __name__ == "__main__":
    main()
