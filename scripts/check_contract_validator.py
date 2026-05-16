#!/usr/bin/env python3
"""Smoke-test the reusable OPE contract validator surface."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

from ope_schema import SPEC, load_json, schema_for, validate_file, validate_record


ROOT = Path(__file__).resolve().parents[1]
VALID_QUESTION = ROOT / "spec" / "fixtures" / "valid" / "binary-weather-logistics-question.json"
QUESTION_SCHEMA = SPEC / "forecast-question.schema.json"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/validate_contract_record.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def main() -> None:
    inferred_schema = schema_for(VALID_QUESTION)
    if inferred_schema != QUESTION_SCHEMA:
        raise AssertionError("schema inference returned the wrong forecast question schema")

    schema_path, errors = validate_file(VALID_QUESTION)
    if schema_path != QUESTION_SCHEMA or errors:
        raise AssertionError("valid forecast question should pass inferred schema validation")

    invalid_question = deepcopy(load_json(VALID_QUESTION))
    del invalid_question["questionId"]
    errors = validate_record(invalid_question, QUESTION_SCHEMA)
    if not any("missing required property 'questionId'" in error for error in errors):
        raise AssertionError("validator should report a missing required questionId")

    result = run_validator("--input", "spec/fixtures/valid/binary-weather-logistics-question.json")
    payload = json.loads(result.stdout)
    if payload["valid"] is not True or payload["schema"] != "spec/forecast-question.schema.json":
        raise AssertionError("single-record validator CLI returned an unexpected valid response")

    with tempfile.TemporaryDirectory() as tmp:
        invalid_path = Path(tmp) / "invalid-question.json"
        invalid_path.write_text(json.dumps(invalid_question), encoding="utf-8")
        failed = subprocess.run(
            [
                sys.executable,
                "scripts/validate_contract_record.py",
                "--input",
                str(invalid_path),
                "--schema",
                "spec/forecast-question.schema.json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if failed.returncode == 0:
            raise AssertionError("single-record validator CLI should fail invalid records")
        failed_payload = json.loads(failed.stdout)
        if failed_payload["valid"] is not False or not failed_payload["errors"]:
            raise AssertionError("single-record validator CLI should report validation errors")

    print("checked reusable contract validator")


if __name__ == "__main__":
    main()
