#!/usr/bin/env python3
"""Check the shared fixture-scaffold helpers."""

from __future__ import annotations

import io
import json
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ope_fixtures import check_generated, compact_json, render_json, validate_and_emit, write_generated


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    sample = {"b": 1, "a": [1, 2]}
    require(
        render_json(sample) == '{\n  "b": 1,\n  "a": [\n    1,\n    2\n  ]\n}\n',
        "render_json must pretty-print indent=2, insertion order, trailing newline",
    )
    require(
        compact_json(sample) == '{"b":1,"a":[1,2]}\n',
        "compact_json must use compact separators and a trailing newline",
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested" / "record.generated.json"
        regen = "python3 scripts/generate_example.py --write"

        out = io.StringIO()
        with redirect_stdout(out):
            write_generated(path, sample, label="example record", regen=regen)
        require(
            path.read_text(encoding="utf-8") == render_json(sample),
            "write_generated must write render_json output",
        )
        require(out.getvalue() == "generated example record\n", "write_generated must announce generation")

        out = io.StringIO()
        with redirect_stdout(out):
            check_generated(path, sample, label="example record", regen=regen)
        require(out.getvalue() == "checked example record\n", "check_generated must announce a clean check")

        path.write_text("drifted\n", encoding="utf-8")
        err = io.StringIO()
        raised = False
        try:
            with redirect_stderr(err):
                check_generated(path, sample, label="example record", regen=regen)
        except SystemExit as exc:
            raised = exc.code == 1
        require(raised, "check_generated must SystemExit(1) on drift")
        require("example record drift:" in err.getvalue(), "drift message must name the label")
        require(regen in err.getvalue(), "drift message must include the regen command")

        missing = Path(tmp) / "absent.generated.json"
        err = io.StringIO()
        raised = False
        try:
            with redirect_stderr(err):
                check_generated(missing, sample, label="example record", regen=regen)
        except SystemExit as exc:
            raised = exc.code == 1
        require(raised, "check_generated must SystemExit(1) when the file is missing")
        require("missing example record:" in err.getvalue(), "missing message must name the label")

        schema_path = Path(tmp) / "thing.schema.json"
        schema_path.write_text(
            json.dumps(
                {
                    "type": "object",
                    "required": ["name"],
                    "properties": {"name": {"type": "string"}},
                    "additionalProperties": False,
                }
            ),
            encoding="utf-8",
        )
        thing_path = Path(tmp) / "thing.generated.json"
        valid = {"name": "ok"}

        out = io.StringIO()
        with redirect_stdout(out):
            validate_and_emit(valid, schema_path, thing_path, write=True, label="thing", regen=regen)
        require(
            thing_path.read_text(encoding="utf-8") == render_json(valid),
            "validate_and_emit must write validated data",
        )
        require(out.getvalue() == "generated thing\n", "validate_and_emit must announce a write")

        out = io.StringIO()
        with redirect_stdout(out):
            validate_and_emit(valid, schema_path, thing_path, write=False, label="thing", regen=regen)
        require(out.getvalue() == "checked thing\n", "validate_and_emit must check validated data")

        raised = False
        with redirect_stdout(io.StringIO()):
            try:
                validate_and_emit({"name": 123}, schema_path, thing_path, write=False, label="thing", regen=regen)
            except SystemExit as exc:
                raised = exc.code == 1
        require(raised, "validate_and_emit must SystemExit(1) on schema-invalid data")

    print("checked shared fixture helpers")


if __name__ == "__main__":
    main()
