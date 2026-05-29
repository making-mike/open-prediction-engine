#!/usr/bin/env python3
"""Run a weather-transit-delay forecast-to-resolution workflow."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import connect_transit_api as transit_api
import fetch_open_meteo_weather as open_meteo
import run_transit_delay_forecast as transit_forecast
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-delay-forward-run"
OUTPUT_PATH = GENERATED / "weather-transit-delays-forward-run.generated.json"
SCHEMA = SPEC / "transit-delay-forward-run.schema.json"
LIVE_WORKSPACE = ROOT / ".ope" / "live" / "transit-forward-run"
HELSINKI_TZ = ZoneInfo("Europe/Helsinki")


class ForwardRunError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def local_uri(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        rel = path.resolve()
    normalized = str(rel).replace("\\", "/")
    return f"local://{normalized}"


def workspace_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def default_window_context(service_date: str, service_window: str, generated_at: str | None = None) -> dict[str, str]:
    if service_window == "morning_peak":
        service_day = datetime.fromisoformat(service_date).date()
        local_start = datetime.combine(service_day, datetime.min.time(), tzinfo=HELSINKI_TZ) + timedelta(hours=7)
        local_end = datetime.combine(service_day, datetime.min.time(), tzinfo=HELSINKI_TZ) + timedelta(hours=10)
        forecast_close = local_start - timedelta(minutes=30)
        resolve_at = local_end + timedelta(minutes=15)
        forecasted_at = parse_timestamp(generated_at) if generated_at else utc_now()
        return {
            "generated_at": generated_at or format_timestamp(forecasted_at),
            "forecasted_at": generated_at or format_timestamp(forecasted_at),
            "forecast_close_time": format_timestamp(forecast_close),
            "horizon_start": format_timestamp(local_start),
            "horizon_end": format_timestamp(local_end),
            "resolve_at": format_timestamp(resolve_at),
        }
    return {
        "generated_at": generated_at or transit_forecast.GENERATED_AT,
        "forecasted_at": generated_at or transit_forecast.FORECASTED_AT,
        "forecast_close_time": transit_forecast.FORECAST_CLOSE_TIME,
        "horizon_start": transit_forecast.HORIZON_START,
        "horizon_end": transit_forecast.HORIZON_END,
        "resolve_at": transit_forecast.RESOLVE_AT,
    }


def context_from_args(args: argparse.Namespace) -> dict[str, str]:
    if args.generated_at or args.forecasted_at or args.forecast_close_time or args.horizon_start or args.horizon_end or args.resolve_at:
        defaults = default_window_context(args.service_date, args.service_window, args.generated_at)
        return {
            "generated_at": args.generated_at or defaults["generated_at"],
            "forecasted_at": args.forecasted_at or defaults["forecasted_at"],
            "forecast_close_time": args.forecast_close_time or defaults["forecast_close_time"],
            "horizon_start": args.horizon_start or defaults["horizon_start"],
            "horizon_end": args.horizon_end or defaults["horizon_end"],
            "resolve_at": args.resolve_at or defaults["resolve_at"],
        }
    if args.check or args.write or args.phase == "fixture":
        return {
            "generated_at": transit_forecast.GENERATED_AT,
            "forecasted_at": transit_forecast.FORECASTED_AT,
            "forecast_close_time": transit_forecast.FORECAST_CLOSE_TIME,
            "horizon_start": transit_forecast.HORIZON_START,
            "horizon_end": transit_forecast.HORIZON_END,
            "resolve_at": transit_forecast.RESOLVE_AT,
        }
    return default_window_context(args.service_date, args.service_window)


def absolutize(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def write_record_set(records: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, record in records.items():
        filename = transit_forecast.OUTPUT_NAMES.get(name)
        if filename:
            (output_dir / filename).write_text(render_json(record), encoding="utf-8")


def build_forecast_records(
    *,
    weather_path: Path,
    history_path: Path,
    args: argparse.Namespace,
    context: dict[str, str],
    trip_updates_path: Path | None,
) -> dict[str, Any]:
    return transit_forecast.build_records(
        weather_path=weather_path,
        history_path=history_path,
        trip_updates_path=trip_updates_path,
        network=args.network,
        geography=args.geography,
        service_window=args.service_window,
        service_date=args.service_date,
        late_seconds=args.late_seconds,
        event_threshold=args.event_threshold,
        min_observations=args.min_observations,
        generated_at=context["generated_at"],
        forecasted_at=context["forecasted_at"],
        forecast_close_time=context["forecast_close_time"],
        horizon_start=context["horizon_start"],
        horizon_end=context["horizon_end"],
        resolve_at=context["resolve_at"],
    )


def write_live_weather_source(path: Path, args: argparse.Namespace, context: dict[str, str]) -> Path:
    source_url = open_meteo.build_url("helsinki", args.service_date)
    raw = open_meteo.fetch_raw(source_url)
    payload = json.loads(raw.decode("utf-8"))
    normalized = open_meteo.normalize_response(
        payload=payload,
        raw=raw,
        source_url=source_url,
        retrieved_at=context["forecasted_at"],
        location_key="helsinki",
        service_date=args.service_date,
    )
    fields = normalized["normalizedFields"]
    row = {
        "network": args.network,
        "geography": args.geography,
        "service_date": args.service_date,
        "service_window": args.service_window,
        "retrieved_at": context["forecasted_at"],
        "forecast_precipitation_mm": fields["forecastDailyPrecipitationMm"],
        "forecast_snowfall_mm": 0.0,
        "forecast_wind_gust_kmh": fields["windGusts10mMaxKmh"],
        "temperature_c": None,
        "source_status": normalized["sourceStatus"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json({"records": [row], "source": normalized["sourceRef"]}), encoding="utf-8")
    return path


def capture_transit_rows(args: argparse.Namespace, context: dict[str, str], run_dir: Path) -> tuple[dict[str, Any], Path]:
    workspace = run_dir / "transit-capture"
    if args.input_protobuf:
        raw = transit_api.load_raw_input(absolutize(args.input_protobuf))
    else:
        raw = transit_api.fetch_hsl_trip_updates(args.timeout, args.max_bytes)
    static_gtfs_path = transit_api.resolve_static_gtfs_path(
        static_gtfs=args.static_gtfs,
        download_static_gtfs_flag=args.download_static_gtfs,
        workspace=workspace,
        timeout=args.timeout,
        max_bytes=args.static_gtfs_max_bytes,
    )
    rows, metadata = transit_api.decode_trip_update_rows(
        raw,
        network=args.network,
        geography=args.geography,
        service_window=args.service_window,
        service_date=args.service_date,
        schedule_join=True,
        static_gtfs_path=static_gtfs_path,
    )
    delay_source = (
        "static_gtfs_schedule_join"
        if metadata.get("scheduleJoin", {}).get("scheduleDerivedDelayRowCount", 0) > 0
        else "explicit_gtfs_rt_delay"
    )
    summary = transit_api.save_capture(
        raw=raw,
        rows=rows,
        metadata=metadata,
        workspace=workspace,
        network=args.network,
        geography=args.geography,
        service_window=args.service_window,
        service_date=args.service_date,
        forecast_close_time=context["forecast_close_time"],
        late_seconds=args.late_seconds,
        delay_source=delay_source,
    )
    decoded_path = ROOT / summary["decodedCsvPath"]
    return summary, decoded_path


def summary_from_records(
    *,
    records: dict[str, Any],
    run_mode: str,
    run_dir: Path,
    scope: dict[str, str],
    weather_path: Path,
    history_path: Path,
    forecast_dir: Path,
    resolved_dir: Path | None,
    capture_summary: dict[str, Any] | None,
) -> dict[str, Any]:
    artifact = records["artifact"]
    run_summary = records["summary"]
    scoring = run_summary.get("score")
    resolution = run_summary.get("resolution")
    output: dict[str, Any] = {
        "forwardRunId": "transitdelayforwardrun-001",
        "generatedAt": run_summary["generatedAt"],
        "domain": "weather-transit-delays",
        "runMode": run_mode,
        "runStatus": "forecast_recorded",
        "forecastStage": {
            "forecastId": artifact["forecastId"],
            "questionId": artifact["questionId"],
            "forecastedAt": artifact["forecastedAt"],
            "closeAt": artifact["closedAt"],
            "resolveAt": artifact["resolutionPlan"]["scheduledResolutionAt"],
            "horizon": artifact["horizon"],
            "network": scope["network"],
            "geography": scope["geography"],
            "serviceDate": scope["service_date"],
            "serviceWindow": scope["service_window"],
            "probability": artifact["forecastOutput"]["probability"],
            "baselineProbability": artifact["baselineForecast"]["probability"],
            "weatherSourceRef": workspace_path(weather_path),
            "historySourceRef": workspace_path(history_path),
        },
        "claimBoundary": {
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "normalChecksUseLiveNetwork": False,
            "resolvedComparableOutcomes": 0,
        },
        "artifacts": {
            "forecastDirectory": workspace_path(forecast_dir),
        },
        "nextAction": "capture transit delay outcome after the forecast horizon and run resolve",
        "warnings": [
            "One forward run is not enough for calibration or public quality claims.",
            "Transit delay outcome rows are resolution evidence, not forecast-time evidence.",
        ],
    }
    if resolved_dir is not None:
        output["artifacts"]["resolvedDirectory"] = workspace_path(resolved_dir)
    if run_mode != "fixture_replay":
        output["artifacts"]["runStatePath"] = workspace_path(run_dir / "forward-run-state.json")
    if capture_summary is not None:
        schedule_join = capture_summary["feed"].get("scheduleJoin") or {}
        output["captureStage"] = {
            "providerId": capture_summary["providerId"],
            "decodedCsvPath": capture_summary["decodedCsvPath"],
            "sourceAdapterOutputPath": capture_summary.get("sourceAdapterOutputPath") or capture_summary["decodedCsvPath"],
            "delayDerivation": capture_summary.get("delayDerivation", "static_gtfs_schedule_join"),
            "rowCount": capture_summary["delaySummary"]["rowCount"],
            "matchedTripUpdateCount": schedule_join.get("matchedTripUpdateCount", 0),
            "unmatchedTripUpdateCount": schedule_join.get("unmatchedTripUpdateCount", 0),
        }
    elif resolution is not None:
        output["captureStage"] = {
            "providerId": "fixture_rows",
            "decodedCsvPath": "spec/fixtures/local-source-files/transit-trip-updates.csv",
            "sourceAdapterOutputPath": "spec/fixtures/local-source-files/transit-trip-updates.csv",
            "delayDerivation": "fixture_rows",
            "rowCount": resolution["observationCount"],
            "matchedTripUpdateCount": 0,
            "unmatchedTripUpdateCount": 0,
        }
    if resolution is not None:
        output["resolutionStage"] = {
            "status": resolution["status"],
            "observationCount": resolution["observationCount"],
            "lateCount": resolution["lateCount"],
            "lateRatio": resolution["lateRatio"],
            "outcomeLabel": "unknown" if resolution["outcome"] is None else "yes" if resolution["outcome"] else "no",
        }
        if resolution["status"] == "resolved":
            output["runStatus"] = "resolved"
    if scoring is not None:
        output["scoreStage"] = {"scoreStatus": scoring["scoreStatus"]}
        if scoring["scoreStatus"] == "scored":
            output["runStatus"] = "scored"
            output["scoreStage"].update(
                {
                    "primaryScore": scoring["primaryScore"],
                    "baselineScore": scoring["baselineScore"],
                    "baselineLift": scoring["baselineLift"],
                }
            )
            output["claimBoundary"]["resolvedComparableOutcomes"] = 1
        elif output.get("resolutionStage", {}).get("status") == "ambiguous":
            output["runStatus"] = "ambiguous"
    if run_mode != "fixture_replay":
        output["claimBoundary"]["normalChecksUseLiveNetwork"] = False
        output["warnings"].append("Live files are local developer artifacts under .ope/live and are not committed fixtures.")
    if output["runStatus"] == "forecast_recorded":
        output["nextAction"] = (
            f"After {artifact['horizon']['endsAt']}, run transit-delay-forward-run --phase resolve "
            f"--run-state {workspace_path(run_dir / 'forward-run-state.json')} --download-static-gtfs"
        )
    else:
        output["nextAction"] = "append more comparable forward runs before any calibration claim"
    validate_summary(output)
    return output


def validate_summary(summary: dict[str, Any]) -> None:
    errors = validate_record(summary, SCHEMA)
    if errors:
        raise ForwardRunError(f"forward-run summary failed schema validation: {errors[0]}")
    if summary["claimBoundary"]["calibrationClaimAllowed"]:
        raise ForwardRunError("forward run must not allow calibration claims")
    if summary["forecastStage"]["forecastedAt"] > summary["forecastStage"]["closeAt"]:
        raise ForwardRunError("forecast must be recorded before close")


def fixture_forward_run() -> dict[str, Any]:
    class Args:
        network = transit_forecast.NETWORK
        geography = transit_forecast.GEOGRAPHY
        service_window = transit_forecast.SERVICE_WINDOW
        service_date = transit_forecast.SERVICE_DATE
        late_seconds = transit_forecast.LATE_SECONDS
        event_threshold = transit_forecast.EVENT_THRESHOLD
        min_observations = transit_forecast.MIN_OBSERVATIONS

    args = Args()
    context = {
        "generated_at": transit_forecast.GENERATED_AT,
        "forecasted_at": transit_forecast.FORECASTED_AT,
        "forecast_close_time": transit_forecast.FORECAST_CLOSE_TIME,
        "horizon_start": transit_forecast.HORIZON_START,
        "horizon_end": transit_forecast.HORIZON_END,
        "resolve_at": transit_forecast.RESOLVE_AT,
    }
    records = build_forecast_records(
        weather_path=transit_forecast.DEFAULT_WEATHER,
        history_path=transit_forecast.DEFAULT_HISTORY,
        args=args,
        context=context,
        trip_updates_path=transit_forecast.DEFAULT_TRIP_UPDATES,
    )
    return summary_from_records(
        records=records,
        run_mode="fixture_replay",
        run_dir=GENERATED,
        scope={
            "network": args.network,
            "geography": args.geography,
            "service_date": args.service_date,
            "service_window": args.service_window,
        },
        weather_path=transit_forecast.DEFAULT_WEATHER,
        history_path=transit_forecast.DEFAULT_HISTORY,
        forecast_dir=ROOT / "spec" / "fixtures" / "generated" / "transit-delay-forecast",
        resolved_dir=ROOT / "spec" / "fixtures" / "generated" / "transit-delay-forecast",
        capture_summary=None,
    )


def run_live(args: argparse.Namespace) -> dict[str, Any]:
    context = context_from_args(args)
    run_dir = absolutize(args.run_dir) if args.run_dir else LIVE_WORKSPACE / f"{args.service_date}-{args.service_window}-{context['generated_at'].replace(':', '').replace('-', '').replace('Z', 'Z')}"
    run_dir.mkdir(parents=True, exist_ok=True)

    weather_path = absolutize(args.weather_forecast) if args.weather_forecast else run_dir / "weather" / "transit-weather-forecast.json"
    if args.live_weather or not args.weather_forecast:
        weather_path = write_live_weather_source(weather_path, args, context)
    history_path = absolutize(args.historical_delays)
    forecast_dir = run_dir / "forecast"
    forecast_records = build_forecast_records(
        weather_path=weather_path,
        history_path=history_path,
        args=args,
        context=context,
        trip_updates_path=None,
    )
    write_record_set(forecast_records, forecast_dir)

    if args.phase == "forecast":
        summary = summary_from_records(
            records=forecast_records,
            run_mode="live_forecast",
            run_dir=run_dir,
            scope={
                "network": args.network,
                "geography": args.geography,
                "service_date": args.service_date,
                "service_window": args.service_window,
            },
            weather_path=weather_path,
            history_path=history_path,
            forecast_dir=forecast_dir,
            resolved_dir=None,
            capture_summary=None,
        )
        (run_dir / "forward-run-state.json").write_text(render_json(summary), encoding="utf-8")
        return summary

    trip_updates_path: Path
    capture_summary: dict[str, Any] | None = None
    if args.trip_updates:
        trip_updates_path = absolutize(args.trip_updates)
    else:
        capture_summary, trip_updates_path = capture_transit_rows(args, context, run_dir)
    resolved_records = build_forecast_records(
        weather_path=weather_path,
        history_path=history_path,
        args=args,
        context=context,
        trip_updates_path=trip_updates_path,
    )
    resolved_dir = run_dir / "resolved"
    write_record_set(resolved_records, resolved_dir)
    summary = summary_from_records(
        records=resolved_records,
        run_mode="live_full" if args.phase == "full" else "live_resolution",
        run_dir=run_dir,
        scope={
            "network": args.network,
            "geography": args.geography,
            "service_date": args.service_date,
            "service_window": args.service_window,
        },
        weather_path=weather_path,
        history_path=history_path,
        forecast_dir=forecast_dir,
        resolved_dir=resolved_dir,
        capture_summary=capture_summary,
    )
    (run_dir / "forward-run-state.json").write_text(render_json(summary), encoding="utf-8")
    return summary


def run_resolve_from_state(args: argparse.Namespace) -> dict[str, Any]:
    if not args.run_state:
        raise ForwardRunError("--run-state is required for --phase resolve")
    state_path = absolutize(args.run_state)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    args.network = state["forecastStage"]["network"]
    args.geography = state["forecastStage"]["geography"]
    args.service_date = state["forecastStage"]["serviceDate"]
    args.service_window = state["forecastStage"]["serviceWindow"]
    run_dir = state_path.parent
    args.run_dir = str(run_dir)
    args.weather_forecast = state["forecastStage"]["weatherSourceRef"]
    args.historical_delays = state["forecastStage"]["historySourceRef"]
    args.generated_at = format_timestamp(utc_now())
    args.forecasted_at = state["forecastStage"]["forecastedAt"]
    args.forecast_close_time = state["forecastStage"]["closeAt"]
    args.horizon_start = state["forecastStage"]["horizon"]["startsAt"]
    args.horizon_end = state["forecastStage"]["horizon"]["endsAt"]
    args.resolve_at = state["forecastStage"]["resolveAt"]
    return run_live(args)


def write_fixture(summary: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, summary, label="transit delay forward run", regen="python3 scripts/run_transit_delay_forward.py --write")


def check_fixture(summary: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, summary, label="transit delay forward run", regen="python3 scripts/run_transit_delay_forward.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["fixture", "forecast", "resolve", "full"], default="fixture")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--run-dir")
    parser.add_argument("--run-state")
    parser.add_argument("--weather-forecast")
    parser.add_argument("--historical-delays", default=str(transit_forecast.DEFAULT_HISTORY))
    parser.add_argument("--trip-updates")
    parser.add_argument("--live-weather", action="store_true")
    parser.add_argument("--input-protobuf")
    parser.add_argument("--static-gtfs")
    parser.add_argument("--download-static-gtfs", action="store_true")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--static-gtfs-max-bytes", type=int, default=120_000_000)
    parser.add_argument("--network", default=transit_forecast.NETWORK)
    parser.add_argument("--geography", default=transit_forecast.GEOGRAPHY)
    parser.add_argument("--service-window", default=transit_forecast.SERVICE_WINDOW)
    parser.add_argument("--service-date", default=transit_forecast.SERVICE_DATE)
    parser.add_argument("--late-seconds", type=int, default=transit_forecast.LATE_SECONDS)
    parser.add_argument("--event-threshold", type=float, default=transit_forecast.EVENT_THRESHOLD)
    parser.add_argument("--min-observations", type=int, default=transit_forecast.MIN_OBSERVATIONS)
    parser.add_argument("--generated-at")
    parser.add_argument("--forecasted-at")
    parser.add_argument("--forecast-close-time")
    parser.add_argument("--horizon-start")
    parser.add_argument("--horizon-end")
    parser.add_argument("--resolve-at")
    args = parser.parse_args()

    try:
        if args.write or args.check or args.phase == "fixture":
            summary = fixture_forward_run()
            if args.write:
                write_fixture(summary)
            elif args.check:
                check_fixture(summary)
            else:
                sys.stdout.write(render_json(summary))
            return
        summary = run_resolve_from_state(args) if args.phase == "resolve" else run_live(args)
        sys.stdout.write(render_json(summary))
    except (OSError, json.JSONDecodeError, transit_forecast.TransitForecastError, transit_api.TransitApiConnectorError, ForwardRunError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
