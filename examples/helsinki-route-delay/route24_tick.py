#!/usr/bin/env python3
"""One tick of the self-rolling route-4560 24-hour on-time predictor.

Run repeatedly (e.g. every 15 minutes by a ticker loop). The predictor keeps
itself going: each run forecasts route 4560's next 24 hours, accumulates
in-window evidence, resolves after the horizon, scores, and records the outcome
into the predictor's calibration store — then the next day's run is created
automatically. Comparable resolved runs accumulate toward OPE's 30 (track
record) / 100 (calibration) gate, one per day.

Each invocation looks at the latest run and does exactly one of:

- No runs yet, or the latest run is terminal and a day has rolled over: create
  the next day's forecast run (live weather, route-4560 / rolling-24h scope,
  a 24h horizon). A terminal run is also (idempotently) recorded into the
  calibration store and its outcome appended to the rolling baseline history.
- Before the active run's resolveAt: capture the live HSL GTFS-RT feed, join it
  to the cached static GTFS schedule, filter route 4560, and merge into the
  run's accumulator CSV keyed by (trip_id, stop_id), keeping the latest
  observation per stop event. This builds genuine in-window resolution evidence
  across the whole 24h horizon, which a single end-of-window snapshot cannot.
- At/after resolveAt: write the final outcome CSV from the accumulator and
  delegate resolution + scoring to OPE's checked
  `transit-delay-forward-run --phase resolve --trip-updates <file>` path, then
  record the scored run into the calibration store.

Forecast math, resolution rules, scoring, and claim gating all stay inside OPE.
This script only orchestrates evidence and the daily roll. Pure stdlib.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import transit_evidence_accumulator as acc  # noqa: E402

BASE_DIR = ROOT / ".ope" / "live" / "route-4560-24h"
HISTORY_PATH = BASE_DIR / "route-4560-history.csv"
STATIC_GTFS = (ROOT / ".ope" / "live" / "helsinki-route-app"
               / "2026-06-10-morning_peak" / "transit-capture" / "cache" / "hsl.zip")
FORWARD = SCRIPTS / "run_transit_delay_forward.py"
CALIBRATE = SCRIPTS / "record_calibration_outcome.py"
FMI = SCRIPTS / "fetch_fmi_weather.py"

ROUTE_PREFIX = "4560_"
SCOPE = {"network": "hsl-route-4560", "geography": "helsinki", "service_window": "rolling-24h"}
HORIZON_HOURS = 24
CLOSE_LAG_MIN = 10
RESOLVE_LAG_MIN = 15
TERMINAL = {"resolved", "scored", "ambiguous", "blocked"}


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def run_paths(run_dir: Path) -> tuple[Path, Path, Path]:
    return (
        run_dir / "forward-run-state.json",
        run_dir / "outcome-accumulator.csv",
        run_dir / "outcome-final.csv",
    )


def latest_run_dir() -> Path | None:
    if not BASE_DIR.exists():
        return None
    runs = sorted(p for p in BASE_DIR.glob("run-*") if (p / "forward-run-state.json").exists())
    return runs[-1] if runs else None


def fetch_fmi(date: str, run_dir: Path, retrieved_at: str) -> Path | None:
    """Best-effort live FMI winter-weather fetch for the run scope.

    Returns the written CSV path on success, or None so the forecast proceeds
    on Open-Meteo + calendar alone. FMI's live parameter mapping is not yet
    validated, so a failure here must never block the predictor.
    """
    out_path = run_dir / "fmi" / "fmi-winter-weather.csv"
    cmd = [
        sys.executable, str(FMI), "--live", "--write", str(out_path),
        "--service-date", date, "--network", SCOPE["network"],
        "--geography", SCOPE["geography"], "--service-window", SCOPE["service_window"],
        "--retrieved-at", retrieved_at,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0 and out_path.exists():
        return out_path
    print(json.dumps({"tick": "fmi_skipped", "reason": (proc.stderr or "fetch failed").strip()[:120]}))
    return None


def create_next_run(now: datetime) -> Path | None:
    """Create today's route-4560 24h forecast run if it does not exist yet."""
    date = now.date().isoformat()
    run_dir = BASE_DIR / f"run-{date.replace('-', '')}"
    state_path, _, _ = run_paths(run_dir)
    if state_path.exists():
        return run_dir
    if not HISTORY_PATH.exists():
        print(json.dumps({"tick": "create_run_skipped", "reason": "missing baseline history", "path": str(HISTORY_PATH)}))
        return None
    run_dir.mkdir(parents=True, exist_ok=True)
    close = now + timedelta(minutes=CLOSE_LAG_MIN)
    h_start = close
    h_end = h_start + timedelta(hours=HORIZON_HOURS)
    resolve_at = h_end + timedelta(minutes=RESOLVE_LAG_MIN)
    cmd = [
        sys.executable, str(FORWARD), "--phase", "forecast",
        "--network", SCOPE["network"], "--geography", SCOPE["geography"],
        "--service-window", SCOPE["service_window"], "--service-date", date,
        "--live-weather", "--historical-delays", str(HISTORY_PATH),
        "--run-dir", str(run_dir),
        "--now", iso(now), "--generated-at", iso(now), "--forecasted-at", iso(now),
        "--forecast-close-time", iso(close),
        "--horizon-start", iso(h_start), "--horizon-end", iso(h_end), "--resolve-at", iso(resolve_at),
        "--calendar",
    ]
    fmi_path = fetch_fmi(date, run_dir, iso(now))
    if fmi_path is not None:
        cmd += ["--fmi-weather", str(fmi_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    ok = proc.returncode == 0
    print(json.dumps({"tick": "create_run", "runDir": run_dir.name, "ok": ok, "resolveAt": iso(resolve_at)}))
    if not ok:
        print(proc.stderr or proc.stdout)
    return run_dir if ok else None


def accumulate(run_dir: Path, forecast: dict) -> None:
    _, acc_path, _ = run_paths(run_dir)
    result = acc.capture_and_accumulate(
        accumulator_path=acc_path,
        static_gtfs_path=STATIC_GTFS,
        scope={
            "network": forecast["network"],
            "geography": forecast["geography"],
            "service_window": forecast["serviceWindow"],
        },
        route_prefix=ROUTE_PREFIX,
    )
    print(json.dumps({
        "tick": "accumulate",
        "runDir": run_dir.name,
        "capturedAt": result["capturedAt"],
        "routeRowsThisCapture": result["freshRows"],
        "accumulatedStopEvents": result["accumulatedStopEvents"],
    }))


def resolve(run_dir: Path) -> None:
    state_path, acc_path, final_path = run_paths(run_dir)
    acc.write_final(acc_path, final_path)
    cmd = [
        sys.executable, str(FORWARD), "--phase", "resolve",
        "--run-state", str(state_path), "--trip-updates", str(final_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout or proc.stderr)
    calibrate(state_path)
    append_history(state_path)


def calibrate(state_path: Path) -> None:
    """Record the now-terminal run into the predictor's calibration store.

    Decoupled from resolution by design (OPE keeps resolution a pure scoring
    write); running it after each resolve advances the track-record/calibration
    gate automatically. Idempotent on rowKey, so repeat ticks are safe no-ops.
    """
    cmd = [sys.executable, str(CALIBRATE), "--run-state", str(state_path), "--run-source", "single"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(proc.stdout or proc.stderr)


def append_history(state_path: Path) -> None:
    """Append a scored run's observed outcome to the rolling baseline history.

    This lets the baseline adapt as real outcomes accumulate, instead of staying
    pinned to the seed history. Deduplicated by the run's observed timestamp.
    """
    state = json.loads(state_path.read_text(encoding="utf-8"))
    if state.get("runStatus") != "scored":
        return
    forecast = state["forecastStage"]
    resolution = state.get("resolutionStage") or {}
    observed_at = state.get("generatedAt") or forecast["resolveAt"]
    existing = HISTORY_PATH.read_text(encoding="utf-8") if HISTORY_PATH.exists() else ""
    if observed_at in existing:
        return
    row = (
        f'{forecast["network"]},{forecast["geography"]},{forecast["serviceWindow"]},'
        f'{forecast["serviceDate"]},{observed_at},{resolution.get("observationCount", 0)},'
        f'{resolution.get("lateRatio", 0.0)}\n'
    )
    with HISTORY_PATH.open("a", encoding="utf-8") as handle:
        handle.write(row)
    print(json.dumps({"tick": "history_append", "observedAt": observed_at}))


def main() -> int:
    now = now_utc()
    latest = latest_run_dir()
    if latest is None:
        create_next_run(now)
        return 0
    state_path, _, _ = run_paths(latest)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    status = state.get("runStatus")
    if status in TERMINAL:
        if status in ("scored", "ambiguous"):
            calibrate(state_path)
            append_history(state_path)
        else:
            print(json.dumps({"tick": "noop", "runDir": latest.name, "runStatus": status}))
        create_next_run(now)
        return 0
    forecast = state["forecastStage"]
    if now >= parse_ts(forecast["resolveAt"]):
        resolve(latest)
    else:
        accumulate(latest, forecast)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
