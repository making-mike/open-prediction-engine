#!/usr/bin/env python3
"""Validate OPE fixtures against the local JSON Schema subset used by this repo."""

from __future__ import annotations

from ope_schema import ROOT, Validator, iter_contract_records, load_json, validate_record


def main() -> None:
    validator = Validator()
    failures: list[str] = []
    records = iter_contract_records()
    for record_path, schema_path in records:
        errors = validate_record(load_json(record_path), schema_path, validator)
        for error in errors:
            failures.append(f"{record_path.relative_to(ROOT)} against {schema_path.name}: {error}")
    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)
    print(f"validated {len(records)} schema-bound fixture records")


if __name__ == "__main__":
    main()
