#!/usr/bin/env python3
"""Check the FMI winter-weather connector against its committed GML fixture."""

from __future__ import annotations

import fetch_fmi_weather as fmi


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_parse_latest_per_parameter() -> None:
    raw = fmi.FIXTURE.read_bytes()
    values = fmi.parse_timeseries(raw)
    # latest temperature is the 06:00 sample (-7.4), not the 05:00 one (-6.2)
    require(values["temperature_c"] == -7.4, f"latest temperature should win, got {values.get('temperature_c')}")
    require(values["snowfall_mm"] == 3.1, f"latest snowfall should win, got {values.get('snowfall_mm')}")
    require(values["road_surface_temp_c"] == -3.5, "road-surface temperature should parse")
    require(values["visibility_m"] == 700.0, "visibility should parse")


def test_normalize_scopes_record() -> None:
    raw = fmi.FIXTURE.read_bytes()
    values = fmi.parse_timeseries(raw)
    record = fmi.normalize(
        values,
        {"network": "hsl-route-4560", "geography": "helsinki", "service_window": "rolling-24h", "service_date": "2026-01-15"},
        "2026-01-15T04:00:00Z",
    )
    require(set(record.keys()) == set(fmi.FIELD_COLUMNS), "normalized record must match the field columns exactly")
    require(record["network"] == "hsl-route-4560", "scope network should be stamped")
    require(record["temperature_c"] == -7.4, "normalized temperature should carry through")


def test_content_hash_stable() -> None:
    raw = fmi.FIXTURE.read_bytes()
    require(fmi.content_hash(raw) == fmi.content_hash(raw), "content hash must be deterministic")
    require(len(fmi.content_hash(raw)) == 64, "sha256 hex digest expected")


def test_field_mapping() -> None:
    require(fmi._field_for("mts-1-1-Temperature") == "temperature_c", "temperature id should map")
    require(fmi._field_for("mts-1-2-Snowfall") == "snowfall_mm", "snowfall id should map")
    require(fmi._field_for("mts-1-3-RoadSurfaceTemperature") == "road_surface_temp_c", "road id should map")
    require(fmi._field_for("mts-x-Pressure") is None, "unknown parameter should not map")


def main() -> None:
    test_parse_latest_per_parameter()
    test_normalize_scopes_record()
    test_content_hash_stable()
    test_field_mapping()
    print("checked fmi winter weather connector parse")


if __name__ == "__main__":
    main()
