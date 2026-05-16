#!/usr/bin/env python3
"""Validate read-surface outputs against explicit contracts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ope_schema import SPEC, load_json, validate_record
from read_ope_record import read_record


ROOT = Path(__file__).resolve().parents[1]
RECORD_INDEX = ROOT / "spec" / "fixtures" / "generated" / "record-index.generated.json"
FORECAST_CARD_SCHEMA = SPEC / "forecast-card.schema.json"
RECORD_INDEX_SCHEMA = SPEC / "record-index.schema.json"


def assert_valid(data: object, schema_path: Path, label: str) -> None:
    errors = validate_record(data, schema_path)
    if errors:
        raise AssertionError(f"{label} failed schema validation: {errors[0]}")


def main() -> None:
    index = load_json(RECORD_INDEX)
    assert_valid(index, RECORD_INDEX_SCHEMA, "record index")
    indexed_types = {record_set["recordType"] for record_set in index["recordSets"]}
    for required_type in ["forecast-artifact", "forecast-bundle", "forecast-card", "track-record"]:
        if required_type not in indexed_types:
            raise AssertionError(f"record index missing {required_type}")

    card_response = read_record("forecast-card", "forecast-502", "question-501")
    card = card_response["record"]
    assert_valid(card, FORECAST_CARD_SCHEMA, "forecast card")
    if card["qualityClaim"]["minimumSampleSize"] <= card["qualityClaim"]["resolvedComparableOutcomes"]:
        raise AssertionError("forecast card should preserve below-threshold claim boundary")
    if card["requestBinding"]["effectfulGeneration"] is not False:
        raise AssertionError("forecast card should preserve dry-run request binding")

    malformed = deepcopy(card)
    del malformed["warnings"]
    if not validate_record(malformed, FORECAST_CARD_SCHEMA):
        raise AssertionError("forecast-card schema should reject missing warnings")

    print("checked read surface contracts")


if __name__ == "__main__":
    main()
