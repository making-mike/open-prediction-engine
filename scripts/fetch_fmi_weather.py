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
        "latlon": "60.1699,24.9384",
        "sourceId": "source-1205",
    },
}
FMI_PARAMETERS = ["Temperature", "Snowfall", "RoadSurfaceTemperature", "Visibility"]

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
        "latlon": location["latlon"],
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


def _field_for(series_id: str) -> str | None:
    lowered = series_id.lower()
    if "roadsurface" in lowered or "tsurf" in lowered or "roadtemperature" in lowered:
        return "road_surface_temp_c"
    if "snow" in lowered:
        return "snowfall_mm"
    if "visibility" in lowered or "vis" in lowered:
        return "visibility_m"
    if "temperature" in lowered or "t2m" in lowered:
        return "temperature_c"
    return None


def parse_timeseries(raw: bytes) -> dict[str, float]:
    """Extract the latest value per known parameter from FMI GML timevaluepairs."""
    root = ET.fromstring(raw)
    values: dict[str, float] = {}
    for series in root.iter():
        if _localname(series.tag) != "MeasurementTimeseries":
            continue
        series_id = next(
            (v for k, v in series.attrib.items() if _localname(k) == "id"),
            "",
        )
        field = _field_for(series_id)
        if field is None:
            continue
        latest_time = ""
        latest_value: float | None = None
        for tvp in series.iter():
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
            if time_text >= latest_time:
                latest_time = time_text
                latest_value = parsed
        if latest_value is not None:
            values[field] = latest_value
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
            for field in ("temperature_c", "snowfall_mm", "road_surface_temp_c"):
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
