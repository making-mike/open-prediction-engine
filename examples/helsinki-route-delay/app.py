#!/usr/bin/env python3
"""Helsinki most-popular-route delay-risk CLI dashboard.

A small host app built on top of the Open Prediction Engine (OPE).

What it does, in one run:
  1. Pulls the live HSL GTFS-RT TripUpdates feed and finds the route with the
     most active trips right now  -> "Helsinki's most popular route".
  2. Delegates the actual forecast to OPE's checked `transit-delay-forward-run`
     surface using live Open-Meteo weather, which logs a real, resolvable
     forward-run with a `resolveAt` timestamp.
  3. Renders a claim-safe CLI dashboard: the busiest route, the weather drivers,
     the delay-risk probability vs baseline, the claim boundary, and the exact
     command to resolve + score the forecast once the window has passed.

This app deliberately does NOT invent its own forecast math, probabilities, or
quality claims. Forecasting, logging, resolution, and scoring all stay inside
OPE. The app only adds (a) popular-route detection and (b) presentation.

Honest scope note: OPE's forward-run currently forecasts at the HSL surface
network + service-window level. The busiest *route* is detected live and shown
as context; the forecast is for the network/window that route runs in.
Route-isolated resolution is a clear next step, not a claim this app makes.

Pure standard library. Network access is used only for the explicit live feed
and weather fetch, mirroring OPE's opt-in live posture.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# --- locate the repo + reuse OPE's own GTFS-RT decoder -----------------------
APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import connect_transit_api as hsl  # noqa: E402  (path injected above)

HELSINKI_TZ = ZoneInfo("Europe/Helsinki")
# Today's morning peak forecast must be placed before this local hour (OPE sets
# forecast close 30 min before the 07:00 window start).
MORNING_PEAK_CLOSE_HOUR = 6  # 06:30 local; if past it, forecast the next day.
DEFAULT_TIMEOUT = 20
DEFAULT_MAX_BYTES = 5_000_000


class AppError(RuntimeError):
    pass


# --- step 1: most popular route ---------------------------------------------
def scan_routes(timeout: int, max_bytes: int) -> dict:
    """Fetch the live feed and rank routes by number of active trips."""
    raw = hsl.fetch_hsl_trip_updates(timeout=timeout, max_bytes=max_bytes)
    header, entities = hsl.parse_feed(raw)

    route_trips: Counter[str] = Counter()
    route_stop_updates: Counter[str] = Counter()
    for entity in entities:
        trip_update = entity.get("tripUpdate") or {}
        trip = trip_update.get("trip") or {}
        route_id = trip.get("routeId")
        if not route_id:
            continue
        route_trips[route_id] += 1
        route_stop_updates[route_id] += len(trip_update.get("stopTimeUpdates") or [])

    if not route_trips:
        raise AppError("live feed contained no routed trip updates")

    total_trips = sum(route_trips.values())
    ranked = [
        {
            "routeId": route_id,
            "activeTrips": trips,
            "stopTimeUpdates": route_stop_updates[route_id],
            "shareOfActiveTrips": round(trips / total_trips, 4),
        }
        for route_id, trips in route_trips.most_common()
    ]
    feed_ts = header.get("timestamp")
    return {
        "feedTimestamp": hsl.timestamp_to_iso(feed_ts) if feed_ts else None,
        "totalRoutedTrips": total_trips,
        "distinctRoutes": len(route_trips),
        "ranked": ranked,
    }


# --- step 2: next open forecast window ---------------------------------------
def next_morning_peak_date(now_local: datetime | None = None) -> str:
    now_local = now_local or datetime.now(HELSINKI_TZ)
    target = now_local.date()
    if now_local.hour >= MORNING_PEAK_CLOSE_HOUR:
        target = target + timedelta(days=1)
    return target.isoformat()


# --- step 3: delegate the real forecast to OPE -------------------------------
def run_forecast(service_date: str, run_dir: Path) -> dict:
    cmd = [
        sys.executable,
        str(SCRIPTS / "ope.py"),
        "transit-delay-forward-run",
        "--phase", "forecast",
        "--live-weather",
        "--service-date", service_date,
        "--service-window", "morning_peak",
        "--run-dir", str(run_dir),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise AppError(
            "OPE forward-run failed:\n"
            + (proc.stderr.strip() or proc.stdout.strip() or "unknown error")
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        raise AppError(f"could not parse OPE output: {exc}\n{proc.stdout[:400]}")


# --- step 4: render ----------------------------------------------------------
def _bar(value: float, width: int = 24) -> str:
    filled = max(0, min(width, round(value * width)))
    return "█" * filled + "·" * (width - filled)


def render(routes: dict, forecast: dict | None, run_dir: Path) -> str:
    top = routes["ranked"][0]
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  HELSINKI · MOST POPULAR ROUTE · DELAY-RISK FORECAST")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Live HSL feed timestamp : {routes['feedTimestamp']}")
    lines.append(f"  Active routed trips     : {routes['totalRoutedTrips']} "
                 f"across {routes['distinctRoutes']} routes")
    lines.append("")
    lines.append("  Busiest routes right now (by active trips):")
    for i, r in enumerate(routes["ranked"][:5], 1):
        marker = "►" if i == 1 else " "
        lines.append(
            f"   {marker} {i}. {r['routeId']:<14} "
            f"{r['activeTrips']:>3} trips  ({r['shareOfActiveTrips']*100:4.1f}%)"
        )
    lines.append("")
    lines.append(f"  ★ Most popular route: {top['routeId']} "
                 f"({top['activeTrips']} active trips)")
    lines.append("")

    if forecast is None:
        lines.append("  (route scan only; forecast skipped)")
        lines.append("=" * 60)
        return "\n".join(lines)

    fs = forecast["forecastStage"]
    cb = forecast.get("claimBoundary", {})
    prob = fs["probability"]
    baseline = fs["baselineProbability"]
    lift = prob - baseline
    lines.append("-" * 60)
    lines.append("  DELAY-RISK FORECAST  (via OPE transit-delay-forward-run)")
    lines.append("-" * 60)
    lines.append(f"  Question : will the HSL surface network exceed its delay")
    lines.append(f"             threshold during the {fs['serviceWindow']} window?")
    lines.append(f"  Scope    : network={fs['network']} geography={fs['geography']}")
    lines.append(f"  Window   : {fs['horizon']['startsAt']} → {fs['horizon']['endsAt']}")
    lines.append(f"  Service  : {fs['serviceDate']}  (busiest route {top['routeId']} runs here)")
    lines.append("")
    lines.append(f"  Forecast P(delay)  {prob*100:5.1f}%  |{_bar(prob)}|")
    lines.append(f"  Baseline  P(delay) {baseline*100:5.1f}%  |{_bar(baseline)}|")
    sign = "+" if lift >= 0 else ""
    lines.append(f"  Weather lift over baseline: {sign}{lift*100:.1f} pts")
    lines.append("")
    lines.append("  Claim boundary (honest by design):")
    lines.append(f"   · qualityClaimAllowed     = {cb.get('qualityClaimAllowed')}")
    lines.append(f"   · calibrationClaimAllowed = {cb.get('calibrationClaimAllowed')}")
    lines.append(f"   · resolvedComparableOutcomes = {cb.get('resolvedComparableOutcomes')}")
    lines.append("   → This is a provisional baseline+weather forecast with NO")
    lines.append("     track record yet. Resolve many windows before trusting it.")
    lines.append("")
    lines.append(f"  Forecast logged at: {run_dir}/forward-run-state.json")
    lines.append(f"  Resolve after {fs['resolveAt']} with:")
    lines.append(f"   python3 scripts/ope.py transit-delay-forward-run --phase resolve \\")
    lines.append(f"     --run-state {run_dir}/forward-run-state.json --download-static-gtfs")
    lines.append("=" * 60)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run-dir", default=None,
                        help="where OPE writes the forward-run state "
                             "(default: .ope/live/helsinki-route-app/<date>)")
    parser.add_argument("--no-forecast", action="store_true",
                        help="only scan the busiest route, do not forecast")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON instead of the dashboard")
    args = parser.parse_args(argv)

    try:
        routes = scan_routes(args.timeout, args.max_bytes)
        forecast = None
        run_dir = Path(args.run_dir) if args.run_dir else None
        if not args.no_forecast:
            service_date = next_morning_peak_date()
            run_dir = run_dir or (ROOT / ".ope" / "live" / "helsinki-route-app"
                                  / f"{service_date}-morning_peak")
            run_dir.mkdir(parents=True, exist_ok=True)
            forecast = run_forecast(service_date, run_dir)
    except AppError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({
            "routes": routes,
            "forecast": forecast,
            "runDir": str(run_dir) if run_dir else None,
        }, indent=2))
    else:
        print(render(routes, forecast, run_dir or Path(".")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
