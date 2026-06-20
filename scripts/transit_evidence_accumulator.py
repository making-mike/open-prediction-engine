#!/usr/bin/env python3
"""Reusable in-window transit evidence accumulator.

A single GTFS-RT snapshot taken at ``resolveAt`` is already stale — by then the
window's trips have aged out of the live feed, which is the root of the day-late
resolution failure. The fix is to accumulate captures across the whole horizon
into one evidence CSV keyed by ``(trip_id, stop_id)``, keeping the latest
observation per stop event, and resolve from that accumulated file. OPE's
``resolve_trip_updates`` then applies ``captured_within_resolution_window`` as
the freshness guard, so only rows captured between the horizon start and a short
lag past ``resolveAt`` count.

This module factors that pattern out of the route-scoped example so both the
single-route ticker and the campaign tick share one implementation. The CSV
merge core (``merge_rows``) is pure and unit-tested; ``capture_and_accumulate``
adds the live fetch + static-GTFS schedule join.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable


FIELDS = [
    "network",
    "geography",
    "service_window",
    "captured_at",
    "observed_service_date",
    "trip_id",
    "stop_id",
    "delay_seconds",
]


def shape_row(row: dict[str, Any], scope: dict[str, str]) -> dict[str, Any]:
    """Normalise a schedule-derived row to the accumulator field set.

    Stamps the scope network/geography/window but preserves the *observed*
    service date from the row itself (not the requested scope date), so a
    capture that drifts into the next service day is visible rather than
    silently relabelled.
    """
    return {
        "network": scope["network"],
        "geography": scope["geography"],
        "service_window": scope["service_window"],
        "captured_at": row.get("captured_at", ""),
        "observed_service_date": row.get("service_date", ""),
        "trip_id": str(row.get("trip_id", "")),
        "stop_id": str(row.get("stop_id", "")),
        "delay_seconds": row.get("delay_seconds", ""),
    }


def merge_rows(
    accumulator_path: Path,
    fresh_rows: Iterable[dict[str, Any]],
) -> dict[str, int]:
    """Merge fresh accumulator-shaped rows into the CSV, keyed by (trip, stop).

    The latest observation per ``(trip_id, stop_id)`` wins. Returns counts of
    rows seen this capture and total accumulated stop events. Pure: no network.
    """
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    if accumulator_path.exists():
        with accumulator_path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                merged[(row["trip_id"], row["stop_id"])] = row
    fresh_count = 0
    for row in fresh_rows:
        merged[(row["trip_id"], row["stop_id"])] = row
        fresh_count += 1
    accumulator_path.parent.mkdir(parents=True, exist_ok=True)
    with accumulator_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(merged.values())
    return {"freshRows": fresh_count, "accumulatedStopEvents": len(merged)}


def capture_and_accumulate(
    *,
    accumulator_path: Path,
    static_gtfs_path: Path,
    scope: dict[str, str],
    route_prefix: str | None = None,
    timeout: int = 30,
    max_bytes: int = 5_000_000,
) -> dict[str, Any]:
    """Fetch one live HSL capture, join it to static GTFS, and accumulate.

    Optional ``route_prefix`` restricts rows to one GTFS route (e.g. ``4560_``);
    omit it to accumulate the whole network scope (the campaign case). Returns
    the merge counts plus the feed capture timestamp.
    """
    import connect_transit_api as hsl

    raw = hsl.fetch_hsl_trip_updates(timeout=timeout, max_bytes=max_bytes)
    header, entities = hsl.parse_feed(raw)
    rows, _meta = hsl.schedule_derived_rows(
        entities,
        static_gtfs_path=static_gtfs_path,
        network=scope["network"],
        geography=scope["geography"],
        service_window=scope["service_window"],
        service_date=None,
        header_timestamp=header.get("timestamp"),
    )
    fresh = [
        shape_row(row, scope)
        for row in rows
        if route_prefix is None or str(row.get("trip_id", "")).startswith(route_prefix)
    ]
    counts = merge_rows(accumulator_path, fresh)
    counts["capturedAt"] = hsl.timestamp_to_iso(header.get("timestamp"))
    return counts


def write_final(accumulator_path: Path, final_path: Path) -> int:
    """Snapshot the accumulator to the immutable outcome file used for resolve."""
    with accumulator_path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    final_path.parent.mkdir(parents=True, exist_ok=True)
    with final_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)
