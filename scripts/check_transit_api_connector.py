#!/usr/bin/env python3
"""Check transit API connector contract and decoder boundaries."""

from __future__ import annotations

import tempfile
from pathlib import Path

from connect_transit_api import (
    connector_record,
    decode_trip_update_rows,
    synthetic_gtfs_rt,
    synthetic_gtfs_rt_without_delay,
    write_synthetic_static_gtfs,
)


def main() -> None:
    record = connector_record()
    if record["provider"]["providerId"] != "hsl_gtfs_rt_trip_updates":
        raise AssertionError("transit API connector should expose the HSL TripUpdates provider")
    if record["api"]["method"] != "GET":
        raise AssertionError("HSL GTFS-RT connector should use GET")
    if record["api"]["requiresCredentials"] is not False:
        raise AssertionError("HSL GTFS-RT connector should not require credentials")
    if record["api"]["requestParametersSupported"] is not False:
        raise AssertionError("HSL GTFS-RT connector should not claim filtering parameters")
    if not record["api"]["companionStaticGtfsPackage"].endswith("/gtfs/hsl.zip"):
        raise AssertionError("HSL GTFS-RT connector should name the companion static GTFS package")
    if record["decoder"]["dependencyPolicy"] != "python_standard_library_only":
        raise AssertionError("transit API decoder should stay stdlib-only")
    if record["decoder"]["scheduleJoinStatus"] != "implemented_opt_in":
        raise AssertionError("transit API connector should expose opt-in schedule join")
    if "route_id" not in record["decoder"]["scheduleJoinMatchKeys"]:
        raise AssertionError("schedule join should declare route_id as a match key")
    if "delay_seconds" not in record["decoder"]["decodedFields"]:
        raise AssertionError("transit API connector must decode delay seconds")
    if record["sourceAdapterBoundary"]["canProduceSourceAdapterOutput"] is not True:
        raise AssertionError("transit API connector should produce source adapter output")
    if record["sourceAdapterBoundary"]["createsForecastArtifacts"]:
        raise AssertionError("transit API connector must not create forecast artifacts")
    if record["sourceAdapterBoundary"]["createsScoringRecords"]:
        raise AssertionError("transit API connector must not create scoring records")
    if record["sourceAdapterBoundary"]["storesCredentials"]:
        raise AssertionError("transit API connector must not store credentials")
    if record["liveBoundary"]["normalChecksOffline"] is not True:
        raise AssertionError("normal checks should stay offline")
    if record["liveBoundary"]["liveFetchRequiresExplicitFlag"] is not True:
        raise AssertionError("live fetch must require an explicit flag")

    rows, metadata = decode_trip_update_rows(
        synthetic_gtfs_rt(),
        network="hsl-surface",
        geography="helsinki",
        service_window="morning_peak",
    )
    if metadata["decodedDelayRowCount"] != 2:
        raise AssertionError("synthetic decoder should emit two rows")
    if rows[0]["delay_seconds"] != 340:
        raise AssertionError("synthetic decoder should prefer departure delay")
    if rows[1]["delay_seconds"] != 60:
        raise AssertionError("synthetic decoder should fallback to arrival delay")
    if rows[0]["service_date"] != "2026-06-10":
        raise AssertionError("synthetic decoder should normalize service date")

    with tempfile.TemporaryDirectory() as temp_dir:
        static_gtfs_path = Path(temp_dir) / "synthetic-gtfs.zip"
        write_synthetic_static_gtfs(static_gtfs_path)
        joined_rows, joined_metadata = decode_trip_update_rows(
            synthetic_gtfs_rt_without_delay(),
            network="hsl-surface",
            geography="helsinki",
            service_window="morning_peak",
            schedule_join=True,
            static_gtfs_path=static_gtfs_path,
        )
    if joined_metadata["scheduleJoin"]["scheduleDerivedDelayRowCount"] != 2:
        raise AssertionError("synthetic schedule join should emit two delay rows")
    if joined_rows[0]["delay_seconds"] != 300:
        raise AssertionError("synthetic schedule join should compute departure delay")
    if joined_rows[1]["delay_seconds"] != 120:
        raise AssertionError("synthetic schedule join should compute arrival delay")

    print("checked transit API connector")


if __name__ == "__main__":
    main()
