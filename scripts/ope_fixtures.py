#!/usr/bin/env python3
"""Shared helpers for rendering and writing/checking generated fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import validate_record


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def compact_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=False) + "\n"


def write_generated(path: Path, data: Any, *, label: str, regen: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")
    print(f"generated {label}")


def check_generated(path: Path, data: Any, *, label: str, regen: str) -> None:
    expected = render_json(data)
    if not path.exists():
        print(f"missing {label}: {path}", file=sys.stderr)
        print(f"run `{regen}`", file=sys.stderr)
        raise SystemExit(1)
    if path.read_text(encoding="utf-8") != expected:
        print(f"{label} drift: {path}", file=sys.stderr)
        print(f"run `{regen}`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {label}")


def validate_and_emit(
    data: Any,
    schema_path: Path,
    path: Path,
    *,
    write: bool,
    label: str,
    regen: str,
) -> None:
    """Validate a record, then write it or check it for drift."""
    errors = validate_record(data, schema_path)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    if write:
        write_generated(path, data, label=label, regen=regen)
    else:
        check_generated(path, data, label=label, regen=regen)
