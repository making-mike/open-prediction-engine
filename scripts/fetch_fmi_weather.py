#!/usr/bin/env python3
"""Fetch or normalize allow-listed FMI open-data winter weather for OPE.

The Finnish Meteorological Institute publishes open data over a WFS endpoint as
GML "timevaluepair" series. This connector mirrors the Open-Meteo connector's
shape — allowlisted location, urllib fetch, deterministic normalize, content
hash, fixture-backed `--check`, opt-in live `--write` — and produces the winter
signals the Open-Meteo file does not carry: temperature, snowfall, road-surface
temperature, and visibility. Those populate the snowfall / temperature / road
hooks the forecast's `weather_adjustment` already scores.

Live parameter / stored-query mapping may need tuning against FMI's catalog;
the committed fixture pins the parser contract so checks stay deterministic and
offline, and the live path is best-effort and opt-in (same posture as the rest
of OPE's live connectors).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "spec" / "fixtures" / "local-source-files" / "fmi-winter-weather.gml.xml"

FMI_ENDPOINT = "https://opendata.fmi.fi/wfs"
FORECAST_STORED_QUERY = "fmi::forecast::harmonie::surface::point::timevaluepair"
ALLOWLISTED_LOCATIONS = {
    "helsinki": {
        "name": "Helsinki",
        "place": "Helsinki",
        "sourceId": "source-1205",
    },
}
# The HARMONIE surface point forecast exposes Temperature (deg C) and
# Precipitation1h (mm). Snowfall is derived from these (see FREEZING_C) because
# FMI's Snow1h parameter conflates rain and snow. Road-surface temperature and
# visibility are NOT in this forecast product (requesting them returns HTTP 400),
# so they are not requested live; the parser still maps them for a future FMI
# road-weather query.
FMI_PARAMETERS = ["Temperature", "Precipitation1h"]
# Aggregate over roughly the next 24 forecast hours rather than a single point.
HORIZON_POINTS = 24

FIELD_COLUMNS = [
    "network",
    "geography",
    "service_window",
    "service_date",
    "retrieved_at",
    "temperature_c",
    "snowfall_mm",
    "road_surface_temp_c",
    "visibility_m",
]


class FmiWeatherError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def content_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build_url(location_key: str) -> str:
    location = ALLOWLISTED_LOCATIONS.get(location_key)
    if location is None:
        raise FmiWeatherError(f"location {location_key!r} is not allow-listed")
    query = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "getFeature",
        "storedquery_id": FORECAST_STORED_QUERY,
        "place": location["place"],
        "parameters": ",".join(FMI_PARAMETERS),
    }
    return f"{FMI_ENDPOINT}?{urlencode(query)}"


def fetch_raw(url: str, timeout: int = 20) -> bytes:
    request = Request(url, headers={"User-Agent": "ope-fmi-connector/0"})
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 (allowlisted host)
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise FmiWeatherError(f"FMI fetch failed: {exc}") from exc


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


# Precipitation counts as snowfall only when the hour is at/below this
# temperature. FMI's own "Snow1h" parameter conflates rain and snow (it returns
# large values during warm-season rain), so we derive snowfall ourselves from
# the two parameters that read correctly: Temperature and Precipitation1h.
FREEZING_C = 1.0


def _field_for(series_id: str) -> str | None:
    lowered = series_id.lower()
    if "roadsurface" in lowered or "tsurf" in lowered or "roadtemperature" in lowered:
        return "road_surface_temp_c"
    if "precip" in lowered:
        return "precip_mm"
    if "visibility" in lowered or "vis" in lowered:
        return "visibility_m"
    if "temperature" in lowered or "t2m" in lowered:
        return "temperature_c"
    return None


def _series_by_time(raw: bytes) -> dict[str, dict[str, float]]:
    """Collect each recognized FMI parameter as a {timestamp: value} map, NaN-free."""
    root = ET.fromstring(raw)
    series: dict[str, dict[str, float]] = {}
    for node in root.iter():
        if _localname(node.tag) != "MeasurementTimeseries":
            continue
        series_id = next((v for k, v in node.attrib.items() if _localname(k) == "id"), "")
        field = _field_for(series_id)
        if field is None:
            continue
        by_time = series.setdefault(field, {})
        for tvp in node.iter():
            if _localname(tvp.tag) != "MeasurementTVP":
                continue
            time_text = value_text = None
            for child in tvp:
                name = _localname(child.tag)
                if name == "time":
                    time_text = (child.text or "").strip()
                elif name == "value":
                    value_text = (child.text or "").strip()
            if not time_text or not value_text:
                continue
            try:
                parsed = float(value_text)
            except ValueError:
                continue
            if parsed != parsed:  # skip NaN fill values
                continue
            by_time[time_text] = parsed
    return series


def parse_timeseries(raw: bytes) -> dict[str, float]:
    """Reduce the FMI forecast to horizon features: coldest temperature and the
    peak hourly snowfall (precipitation occurring at/below freezing)."""
    series = _series_by_time(raw)
    temps = series.get("temperature_c", {})
    precip = series.get("precip_mm", {})
    horizon = sorted(set(temps) | set(precip))[:HORIZON_POINTS]

    values: dict[str, float] = {}
    temp_window = [temps[t] for t in horizon if t in temps]
    if temp_window:
        values["temperature_c"] = min(temp_window)
    if precip:
        snow_hours = [precip[t] for t in horizon if t in precip and temps.get(t, 99.0) <= FREEZING_C]
        values["snowfall_mm"] = round(max(snow_hours), 3) if snow_hours else 0.0
    for extra in ("road_surface_temp_c", "visibility_m"):
        pts = series.get(extra, {})
        window = [pts[t] for t in sorted(pts)[:HORIZON_POINTS]]
        if window:
            values[extra] = min(window)
    if not values:
        raise FmiWeatherError("FMI response contained no recognized parameter series")
    return values


def normalize(values: dict[str, float], scope: dict[str, str], retrieved_at: str) -> dict[str, Any]:
    return {
        "network": scope["network"],
        "geography": scope["geography"],
        "service_window": scope["service_window"],
        "service_date": scope["service_date"],
        "retrieved_at": retrieved_at,
        "temperature_c": values.get("temperature_c", ""),
        "snowfall_mm": values.get("snowfall_mm", ""),
        "road_surface_temp_c": values.get("road_surface_temp_c", ""),
        "visibility_m": values.get("visibility_m", ""),
    }


def write_csv(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_COLUMNS)
        writer.writeheader()
        writer.writerow(record)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--location", default="helsinki", choices=sorted(ALLOWLISTED_LOCATIONS))
    parser.add_argument("--network", default="hsl-route-4560")
    parser.add_argument("--geography", default="helsinki")
    parser.add_argument("--service-window", default="rolling-24h")
    parser.add_argument("--service-date")
    parser.add_argument("--write", help="write a normalized FMI weather CSV to this path")
    parser.add_argument("--live", action="store_true", help="fetch from FMI instead of the committed fixture")
    parser.add_argument("--check", action="store_true", help="parse the committed fixture and assert the contract")
    parser.add_argument("--retrieved-at", default=None)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)

    try:
        if args.check:
            raw = FIXTURE.read_bytes()
            values = parse_timeseries(raw)
            for field in ("temperature_c", "snowfall_mm"):
                if field not in values:
                    raise FmiWeatherError(f"fixture parse missing {field}")
            print("checked fmi winter weather connector")
            return 0

        if args.live:
            raw = fetch_raw(build_url(args.location), timeout=args.timeout)
        else:
            raw = FIXTURE.read_bytes()
        values = parse_timeseries(raw)
        retrieved_at = args.retrieved_at or utc_now()
        scope = {
            "network": args.network,
            "geography": args.geography,
            "service_window": args.service_window,
            "service_date": args.service_date or datetime.now(timezone.utc).date().isoformat(),
        }
        record = normalize(values, scope, retrieved_at)
        if args.write:
            write_csv(Path(args.write), record)
            print(f"wrote FMI weather to {args.write} (hash {content_hash(raw)[:12]})")
        else:
            import json

            print(json.dumps(record, indent=2))
        return 0
    except (FmiWeatherError, OSError, ET.ParseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
