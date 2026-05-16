#!/usr/bin/env python3
"""Fetch or normalize allow-listed Open-Meteo weather data for OPE."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


OPEN_METEO_ENDPOINT = "https://api.open-meteo.com/v1/forecast"
DAILY_VARIABLES = [
    "precipitation_sum",
    "precipitation_probability_max",
    "weather_code",
    "wind_gusts_10m_max",
]
ALLOWLISTED_LOCATIONS = {
    "warsaw": {
        "name": "Warsaw",
        "latitude": 52.2297,
        "longitude": 21.0122,
        "timezone": "Europe/Warsaw",
        "sourceId": "source-401",
    }
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def content_hash(raw: bytes) -> str:
    return "sha256-" + hashlib.sha256(raw).hexdigest()


def build_url(location_key: str, service_date: str) -> str:
    location = ALLOWLISTED_LOCATIONS[location_key]
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "daily": ",".join(DAILY_VARIABLES),
        "timezone": location["timezone"],
        "precipitation_unit": "mm",
        "start_date": service_date,
        "end_date": service_date,
    }
    return OPEN_METEO_ENDPOINT + "?" + urlencode(params)


def fetch_raw(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "open-prediction-engine/0 fixture-prototype"})
    try:
        with urlopen(request, timeout=20) as response:
            return response.read()
    except HTTPError as exc:
        raise SystemExit(f"Open-Meteo HTTP error {exc.code}: {exc.reason}") from exc
    except URLError as exc:
        raise SystemExit(f"Open-Meteo request failed: {exc.reason}") from exc


def daily_value(payload: dict[str, Any], service_date: str, variable: str) -> Any:
    daily = payload.get("daily")
    if not isinstance(daily, dict):
        raise ValueError("Open-Meteo response is missing daily data")
    dates = daily.get("time")
    values = daily.get(variable)
    if not isinstance(dates, list) or not isinstance(values, list):
        raise ValueError(f"Open-Meteo response is missing daily {variable}")
    if service_date not in dates:
        raise ValueError(f"Open-Meteo response does not include service date {service_date}")
    index = dates.index(service_date)
    if index >= len(values):
        raise ValueError(f"Open-Meteo daily {variable} has no value for {service_date}")
    return values[index]


def normalize_response(
    *,
    payload: dict[str, Any],
    raw: bytes,
    source_url: str,
    retrieved_at: str,
    location_key: str,
    service_date: str,
    source_status: str = "current",
) -> dict[str, Any]:
    if source_status not in {"current", "corrected"}:
        raise ValueError(f"unsupported source status {source_status!r}")
    location = ALLOWLISTED_LOCATIONS[location_key]
    if payload.get("timezone") != location["timezone"]:
        raise ValueError(
            f"Open-Meteo response timezone {payload.get('timezone')!r} does not match "
            f"allow-listed timezone {location['timezone']!r}"
        )
    return {
        "sourceRef": {
            "sourceId": location["sourceId"],
            "name": f"Open-Meteo weather forecast for {location['name']}",
            "sourceType": "public_dataset",
            "uri": source_url,
            "retrievedAt": retrieved_at,
            "contentHash": content_hash(raw),
        },
        "provider": "Open-Meteo",
        "geography": location["name"],
        "serviceDate": service_date,
        "sourceStatus": source_status,
        "correctionReviewRequired": source_status == "corrected",
        "normalizedFields": {
            "forecastDailyPrecipitationMm": daily_value(payload, service_date, "precipitation_sum"),
            "precipitationProbabilityMaxPercent": daily_value(
                payload,
                service_date,
                "precipitation_probability_max",
            ),
            "weatherCode": daily_value(payload, service_date, "weather_code"),
            "windGusts10mMaxKmh": daily_value(payload, service_date, "wind_gusts_10m_max"),
            "timezone": payload["timezone"],
            "utcOffsetSeconds": payload.get("utc_offset_seconds"),
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "dailyUnits": payload.get("daily_units", {}),
        },
    }


def load_fixture(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    return json.loads(raw.decode("utf-8")), raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--location", choices=sorted(ALLOWLISTED_LOCATIONS), required=True)
    parser.add_argument("--service-date", required=True, help="ISO date, e.g. 2026-06-03")
    parser.add_argument("--fixture", type=Path, help="normalize this fixture response instead of fetching")
    parser.add_argument("--live", action="store_true", help="perform an opt-in live Open-Meteo request")
    parser.add_argument(
        "--source-status",
        choices=["current", "corrected"],
        default="current",
        help="label corrected/backfilled provider responses for review",
    )
    parser.add_argument("--retrieved-at", help="override retrieval timestamp for deterministic checks")
    parser.add_argument("--output", type=Path, help="write normalized JSON to this path")
    args = parser.parse_args()

    source_url = build_url(args.location, args.service_date)
    if args.fixture and args.live:
        raise SystemExit("use either --fixture or --live, not both")
    if args.fixture:
        payload, raw = load_fixture(args.fixture)
    elif args.live:
        raw = fetch_raw(source_url)
        payload = json.loads(raw.decode("utf-8"))
    else:
        raise SystemExit("live network access is opt-in; pass --fixture or --live")

    normalized = normalize_response(
        payload=payload,
        raw=raw,
        source_url=source_url,
        retrieved_at=args.retrieved_at or utc_now(),
        location_key=args.location,
        service_date=args.service_date,
        source_status=args.source_status,
    )
    output = json.dumps(normalized, indent=2, sort_keys=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)


if __name__ == "__main__":
    main()
