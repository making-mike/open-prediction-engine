#!/usr/bin/env python3
"""Validate OPE fixtures against the local JSON Schema subset used by this repo."""

from __future__ import annotations

from ope_schema import (
    ROOT,
    SCHEMALESS_GENERATED_SUFFIXES,
    Validator,
    iter_contract_records,
    iter_generated_fixtures,
    load_json,
    schema_for,
    validate_record,
)


def main() -> None:
    validator = Validator()
    failures: list[str] = []
    records = iter_contract_records()
    for record_path, schema_path in records:
        errors = validate_record(load_json(record_path), schema_path, validator)
        for error in errors:
            failures.append(f"{record_path.relative_to(ROOT)} against {schema_path.name}: {error}")

    # Coverage guard: every generated fixture must either resolve to a schema or
    # be an explicitly allow-listed schema-less intermediate. schema_for() returns
    # None on a miss, and iter_contract_records() silently drops misses, so without
    # this check a renamed fixture or a stale endswith() rule would quietly stop
    # being validated. Turn that into a hard failure instead.
    uncovered = [
        path.relative_to(ROOT)
        for path in iter_generated_fixtures()
        if schema_for(path) is None and not path.name.endswith(SCHEMALESS_GENERATED_SUFFIXES)
    ]
    for path in uncovered:
        failures.append(
            f"{path}: no schema matched and not an allow-listed intermediate "
            "(add a schema_for rule, or extend SCHEMALESS_GENERATED_SUFFIXES if intentional)"
        )

    if failures:
        for failure in failures:
            print(failure)
        raise SystemExit(1)
    print(f"validated {len(records)} schema-bound fixture records; all generated fixtures covered")


if __name__ == "__main__":
    main()
