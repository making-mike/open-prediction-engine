#!/usr/bin/env python3
"""Generate or check the public read-only record index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from read_ope_record import RECORD_TYPES, list_records
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "spec" / "fixtures" / "generated" / "record-index.generated.json"
GENERATED_AT = "2026-06-06T10:30:00Z"


def build_index() -> dict[str, Any]:
    record_sets = []
    for record_type in sorted(RECORD_TYPES):
        listed = list_records(record_type)
        record_sets.append(
            {
                "recordType": record_type,
                "count": listed["count"],
                "records": listed["records"],
            }
        )
    return {
        "recordIndexId": "recordindex-001",
        "generatedAt": GENERATED_AT,
        "access": {
            "mode": "read_only_file",
            "source": "spec/fixtures/generated",
        },
        "recordSets": record_sets,
    }


def write_index(index: dict[str, Any]) -> None:
    INDEX_PATH.write_text(render_json(index), encoding="utf-8")
    print("generated public record index")


def check_index(index: dict[str, Any]) -> None:
    expected = render_json(index)
    if not INDEX_PATH.exists():
        print(f"missing record index: {INDEX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_record_index.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = INDEX_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"record index drift: {INDEX_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_record_index.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked public record index")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write index instead of checking it")
    args = parser.parse_args()
    index = build_index()
    if args.write:
        write_index(index)
    else:
        check_index(index)


if __name__ == "__main__":
    main()
