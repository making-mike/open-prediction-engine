#!/usr/bin/env python3
"""Check the reusable in-window transit evidence accumulator merge core."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import transit_evidence_accumulator as acc


SCOPE = {"network": "hsl-route-4560", "geography": "helsinki", "service_window": "rolling-24h"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def derived(trip_id: str, stop_id: str, captured_at: str, service_date: str, delay: int) -> dict:
    return {
        "trip_id": trip_id,
        "stop_id": stop_id,
        "captured_at": captured_at,
        "service_date": service_date,
        "delay_seconds": delay,
    }


def test_shape_preserves_observed_service_date() -> None:
    row = acc.shape_row(derived("4560_1", "S1", "2026-06-12T00:10:00Z", "2026-06-12", 30), SCOPE)
    require(row["network"] == "hsl-route-4560", "scope network should be stamped")
    require(row["observed_service_date"] == "2026-06-12", "observed service date must come from the row, not the scope")
    require(set(row.keys()) == set(acc.FIELDS), "shaped row should match the accumulator field set exactly")


def test_merge_dedups_and_keeps_latest() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = Path(raw) / "acc.csv"
        first = [
            acc.shape_row(derived("4560_1", "S1", "2026-06-11T14:00:00Z", "2026-06-11", 10), SCOPE),
            acc.shape_row(derived("4560_1", "S2", "2026-06-11T14:00:00Z", "2026-06-11", 20), SCOPE),
        ]
        counts = acc.merge_rows(path, first)
        require(counts["accumulatedStopEvents"] == 2, "two distinct stop events should accumulate")

        # A later capture updates S1 and adds S3; S2 is untouched.
        second = [
            acc.shape_row(derived("4560_1", "S1", "2026-06-11T18:00:00Z", "2026-06-11", 300), SCOPE),
            acc.shape_row(derived("4560_1", "S3", "2026-06-11T18:00:00Z", "2026-06-11", 5), SCOPE),
        ]
        counts = acc.merge_rows(path, second)
        require(counts["accumulatedStopEvents"] == 3, "merge should keep S2 and add S3, total three")

        rows = {(r["trip_id"], r["stop_id"]): r for r in csv.DictReader(path.open(newline=""))}
        require(rows[("4560_1", "S1")]["delay_seconds"] == "300", "latest observation per stop event should win")
        require(rows[("4560_1", "S1")]["captured_at"] == "2026-06-11T18:00:00Z", "latest capture timestamp should win")
        require(("4560_1", "S2") in rows, "earlier-only stop event should be retained")


def test_write_final_snapshots_accumulator() -> None:
    with tempfile.TemporaryDirectory() as raw:
        acc_path = Path(raw) / "acc.csv"
        final_path = Path(raw) / "final.csv"
        acc.merge_rows(acc_path, [acc.shape_row(derived("4560_1", "S1", "2026-06-11T14:00:00Z", "2026-06-11", 10), SCOPE)])
        count = acc.write_final(acc_path, final_path)
        require(count == 1, "final snapshot should carry every accumulated row")
        require(final_path.exists(), "final outcome file should be written")
        header = next(csv.reader(final_path.open(newline="")))
        require(header == acc.FIELDS, "final file should use the resolve-compatible field set")


def main() -> None:
    test_shape_preserves_observed_service_date()
    test_merge_dedups_and_keeps_latest()
    test_write_final_snapshots_accumulator()
    print("checked transit evidence accumulator")


if __name__ == "__main__":
    main()
