#!/usr/bin/env python3
"""Validate one OPE record against an inferred or explicit schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ope_schema import ROOT, SchemaError, validate_file


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="record JSON file to validate")
    parser.add_argument("--schema", type=Path, help="schema JSON file; inferred when omitted")
    args = parser.parse_args()

    try:
        schema_path, errors = validate_file(args.input, args.schema)
    except (FileNotFoundError, json.JSONDecodeError, SchemaError) as exc:
        response = {
            "valid": False,
            "input": display_path(args.input),
            "schema": display_path(args.schema) if args.schema else None,
            "errors": [str(exc)],
        }
        sys.stdout.write(json.dumps(response, indent=2, sort_keys=False) + "\n")
        raise SystemExit(1) from exc

    response = {
        "valid": not errors,
        "input": display_path(args.input),
        "schema": display_path(schema_path),
        "errors": errors,
    }
    sys.stdout.write(json.dumps(response, indent=2, sort_keys=False) + "\n")
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
