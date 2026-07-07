#!/usr/bin/env python3
"""Check the FMI winter-weather connector against its committed GML fixture."""

from __future__ import annotations

import fetch_fmi_weather as fmi


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_temperature_is_horizon_min() -> None:
    raw = fmi.FIXTURE.read_bytes()
    values = fmi.parse_timeseries(raw)
    # coldest of -4.0 / -5.5 / -3.0 (the NaN hour is skipped)
    require(values["temperature_c"] == -5.5, f"coldest temperature should win, got {values.get('temperature_c')}")


def test_snowfall_derived_from_freezing_precip() -> None:
    raw = fmi.FIXTURE.read_bytes()
    values = fmi.parse_timeseries(raw)
    # every precip hour with a known temperature is below freezing; peak is 2.4mm.
    # the 08:00 precip (0.6) is excluded because its temperature is NaN (unknown).
    require(values["snowfall_mm"] == 2.4, f"peak freezing-hour precip should be snowfall, got {values.get('snowfall_mm')}")


def test_warm_precip_is_not_snow() -> None:
    gml = b"""<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
        xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:wml2="http://www.opengis.net/waterml/2.0">
      <wml2:MeasurementTimeseries gml:id="mts-1-1-Temperature">
        <wml2:point><wml2:MeasurementTVP><wml2:time>2026-07-06T05:00:00Z</wml2:time>
          <wml2:value>13.0</wml2:value></wml2:MeasurementTVP></wml2:point></wml2:MeasurementTimeseries>
      <wml2:MeasurementTimeseries gml:id="mts-1-1-Precipitation1h">
        <wml2:point><wml2:MeasurementTVP><wml2:time>2026-07-06T05:00:00Z</wml2:time>
          <wml2:value>3.0</wml2:value></wml2:MeasurementTVP></wml2:point></wml2:MeasurementTimeseries>
      </wfs:FeatureCollection>"""
    values = fmi.parse_timeseries(gml)
    require(values["snowfall_mm"] == 0.0, "rain at 13 C must not count as snowfall")


def test_nan_values_skipped() -> None:
    gml = b"""<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0"
        xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:wml2="http://www.opengis.net/waterml/2.0">
      <wml2:MeasurementTimeseries gml:id="mts-1-1-Temperature">
        <wml2:point><wml2:MeasurementTVP><wml2:time>2026-01-15T05:00:00Z</wml2:time>
          <wml2:value>NaN</wml2:value></wml2:MeasurementTVP></wml2:point>
        <wml2:point><wml2:MeasurementTVP><wml2:time>2026-01-15T06:00:00Z</wml2:time>
          <wml2:value>-4.0</wml2:value></wml2:MeasurementTVP></wml2:point>
      </wml2:MeasurementTimeseries></wfs:FeatureCollection>"""
    values = fmi.parse_timeseries(gml)
    require(values["temperature_c"] == -4.0, "NaN points must be skipped, real value retained")


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
    require(record["temperature_c"] == -5.5, "normalized temperature should carry through")
    require(record["road_surface_temp_c"] == "", "road surface is absent from the forecast product")


def test_content_hash_stable() -> None:
    raw = fmi.FIXTURE.read_bytes()
    require(fmi.content_hash(raw) == fmi.content_hash(raw), "content hash must be deterministic")
    require(len(fmi.content_hash(raw)) == 64, "sha256 hex digest expected")


def test_field_mapping() -> None:
    require(fmi._field_for("mts-1-1-Temperature") == "temperature_c", "temperature id should map")
    require(fmi._field_for("mts-1-1-Precipitation1h") == "precip_mm", "precipitation id should map")
    require(fmi._field_for("mts-1-3-RoadSurfaceTemperature") == "road_surface_temp_c", "road id should map")
    require(fmi._field_for("mts-x-Pressure") is None, "unknown parameter should not map")


def main() -> None:
    test_temperature_is_horizon_min()
    test_snowfall_derived_from_freezing_precip()
    test_warm_precip_is_not_snow()
    test_nan_values_skipped()
    test_normalize_scopes_record()
    test_content_hash_stable()
    test_field_mapping()
    print("checked fmi winter weather connector parse")


if __name__ == "__main__":
    main()
