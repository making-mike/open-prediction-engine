#!/usr/bin/env python3
"""Check the weather-transit-delay forward-run workflow fixture."""

from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path

import run_transit_delay_forecast as transit_forecast
from run_transit_delay_forward import fixture_forward_run, run_resolve_from_state
from ope_fixtures import render_json


def check_fixture_summary() -> None:
    summary = fixture_forward_run()
    forecast = summary["forecastStage"]
    resolution = summary["resolutionStage"]
    score = summary["scoreStage"]
    claims = summary["claimBoundary"]

    if summary["domain"] != "weather-transit-delays":
        raise AssertionError("forward run should use the transit delay domain")
    if summary["runMode"] != "fixture_replay" or summary["runStatus"] != "scored":
        raise AssertionError("fixture forward run should complete through scoring")
    if forecast["forecastedAt"] > forecast["closeAt"]:
        raise AssertionError("forward run forecast must be recorded before close")
    if forecast["probability"] <= forecast["baselineProbability"]:
        raise AssertionError("fixture forward run should lift above baseline")
    if resolution["status"] != "resolved" or resolution["outcomeLabel"] != "yes":
        raise AssertionError("fixture forward run should resolve to a Yes outcome")
    if score["scoreStatus"] != "scored" or score["baselineLift"] <= 0:
        raise AssertionError("fixture forward run should score with positive baseline lift")
    if claims["qualityClaimAllowed"] or claims["calibrationClaimAllowed"]:
        raise AssertionError("forward run must keep quality and calibration claims blocked")
    if claims["resolvedComparableOutcomes"] != 1:
        raise AssertionError("fixture forward run should expose exactly one comparable resolved outcome")
    if "append more comparable forward runs" not in summary["nextAction"]:
        raise AssertionError("forward run should require more comparable outcomes before stronger claims")


def write_recorded_state(run_dir: Path) -> Path:
    state = copy.deepcopy(fixture_forward_run())
    state["runMode"] = "live_forecast"
    state["runStatus"] = "forecast_recorded"
    state.pop("captureStage", None)
    state.pop("resolutionStage", None)
    state.pop("scoreStage", None)
    state["claimBoundary"]["resolvedComparableOutcomes"] = 0
    state_path = run_dir / "forward-run-state.json"
    state["artifacts"] = {
        "forecastDirectory": str(run_dir / "forecast"),
        "runStatePath": str(state_path),
    }
    state["nextAction"] = "capture transit delay outcome after the forecast horizon and run resolve"
    state_path.write_text(render_json(state), encoding="utf-8")
    return state_path


def resolve_args(state_path: Path, now: str, trip_updates: str | None) -> argparse.Namespace:
    return argparse.Namespace(
        phase="resolve",
        write=False,
        check=False,
        run_dir=None,
        run_state=str(state_path),
        weather_forecast=None,
        historical_delays=str(transit_forecast.DEFAULT_HISTORY),
        trip_updates=trip_updates,
        live_weather=False,
        input_protobuf=None,
        static_gtfs=None,
        download_static_gtfs=False,
        timeout=15,
        max_bytes=25_000_000,
        static_gtfs_max_bytes=120_000_000,
        network=transit_forecast.NETWORK,
        geography=transit_forecast.GEOGRAPHY,
        service_window=transit_forecast.SERVICE_WINDOW,
        service_date=transit_forecast.SERVICE_DATE,
        late_seconds=transit_forecast.LATE_SECONDS,
        event_threshold=transit_forecast.EVENT_THRESHOLD,
        min_observations=transit_forecast.MIN_OBSERVATIONS,
        now=now,
        generated_at=None,
        forecasted_at=None,
        forecast_close_time=None,
        horizon_start=None,
        horizon_end=None,
        resolve_at=None,
    )


def check_stale_capture_guard() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = write_recorded_state(Path(temp_dir))
        summary = run_resolve_from_state(resolve_args(state_path, "2026-06-10T10:30:00Z", None))
        if summary["runStatus"] != "blocked":
            raise AssertionError("a live resolve attempted too long after resolveAt must be blocked, not resolved")
        guard = summary.get("resolutionGuard")
        if not guard or guard["reasonCode"] != "stale_capture_window":
            raise AssertionError("blocked stale resolve must record the stale_capture_window reason code")
        if guard["captureLagSeconds"] <= guard["maxCaptureLagSeconds"]:
            raise AssertionError("blocked stale resolve must record a capture lag above the tolerance")
        if "resolutionStage" in summary or "scoreStage" in summary:
            raise AssertionError("blocked stale resolve must not produce resolution or scoring stages")
        rewritten = json.loads(state_path.read_text(encoding="utf-8"))
        if rewritten["runStatus"] != "blocked":
            raise AssertionError("blocked stale resolve must persist the blocked run state")


def check_on_time_resolve() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = write_recorded_state(Path(temp_dir))
        summary = run_resolve_from_state(
            resolve_args(state_path, "2026-06-10T08:30:00Z", str(transit_forecast.DEFAULT_TRIP_UPDATES))
        )
        if summary["runStatus"] != "scored":
            raise AssertionError("an on-time capture within the lag tolerance should resolve and score")
        if summary["resolutionStage"]["status"] != "resolved":
            raise AssertionError("on-time fixture rows should resolve the declared window")


def main() -> None:
    check_fixture_summary()
    check_stale_capture_guard()
    check_on_time_resolve()
    print("checked transit delay forward run")


if __name__ == "__main__":
    main()
