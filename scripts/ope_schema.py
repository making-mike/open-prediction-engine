"""Reusable OPE JSON Schema subset validation helpers."""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec"


class SchemaError(Exception):
    """Raised when a schema uses unsupported local validator features."""


class Validator:
    """Validate records against the JSON Schema subset used by OPE contracts."""

    def __init__(self) -> None:
        self.cache: dict[Path, dict[str, Any]] = {}

    def load_schema(self, path: Path) -> dict[str, Any]:
        path = path.resolve()
        if path not in self.cache:
            self.cache[path] = json.loads(path.read_text(encoding="utf-8"))
        return self.cache[path]

    def resolve_ref(
        self,
        ref: str,
        current_file: Path,
        root_schema: dict[str, Any],
    ) -> tuple[dict[str, Any], Path, dict[str, Any]]:
        if "#" in ref:
            file_part, pointer = ref.split("#", 1)
        else:
            file_part, pointer = ref, ""
        if file_part:
            target_file = (current_file.parent / file_part).resolve()
            target_root = self.load_schema(target_file)
        else:
            target_file = current_file
            target_root = root_schema
        target: Any = target_root
        if pointer:
            if not pointer.startswith("/"):
                raise SchemaError(f"unsupported JSON pointer {ref!r}")
            for part in pointer.lstrip("/").split("/"):
                part = part.replace("~1", "/").replace("~0", "~")
                target = target[part]
        return target, target_file, target_root

    def validate(
        self,
        data: Any,
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str = "$",
    ) -> list[str]:
        errors: list[str] = []

        if "$ref" in schema:
            target, target_file, target_root = self.resolve_ref(schema["$ref"], schema_file, root_schema)
            return self.validate(data, target, target_file, target_root, path)

        if "allOf" in schema:
            for index, subschema in enumerate(schema["allOf"]):
                errors.extend(self.validate(data, subschema, schema_file, root_schema, f"{path}.allOf[{index}]"))

        if "oneOf" in schema:
            matches = [
                not self.validate(data, subschema, schema_file, root_schema, path)
                for subschema in schema["oneOf"]
            ]
            if sum(1 for item in matches if item) != 1:
                errors.append(f"{path}: expected exactly one matching schema, got {sum(matches)}")

        if "if" in schema:
            if_matches = not self.validate(data, schema["if"], schema_file, root_schema, path)
            if if_matches and "then" in schema:
                errors.extend(self.validate(data, schema["then"], schema_file, root_schema, path))

        if "const" in schema and data != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}, got {data!r}")

        if "enum" in schema and data not in schema["enum"]:
            errors.append(f"{path}: expected one of {schema['enum']!r}, got {data!r}")

        expected_type = schema.get("type")
        if expected_type and not self.is_type(data, expected_type):
            errors.append(f"{path}: expected type {expected_type}, got {type(data).__name__}")
            return errors

        if isinstance(data, dict):
            errors.extend(self.validate_object(data, schema, schema_file, root_schema, path))
        elif isinstance(data, list):
            errors.extend(self.validate_array(data, schema, schema_file, root_schema, path))
        elif isinstance(data, str):
            errors.extend(self.validate_string(data, schema, path))
        elif self.is_number(data):
            errors.extend(self.validate_number(data, schema, path))

        return errors

    def validate_object(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        errors: list[str] = []
        required = schema.get("required", [])
        for key in required:
            if key not in data:
                errors.append(f"{path}: missing required property {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            allowed = set(properties)
            for key in data:
                if key not in allowed:
                    errors.append(f"{path}: unexpected property {key!r}")
        for key, subschema in properties.items():
            if key in data:
                errors.extend(
                    self.validate(data[key], subschema, schema_file, root_schema, f"{path}.{key}")
                )
        return errors

    def validate_array(
        self,
        data: list[Any],
        schema: dict[str, Any],
        schema_file: Path,
        root_schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        errors: list[str] = []
        if "minItems" in schema and len(data) < schema["minItems"]:
            errors.append(f"{path}: expected at least {schema['minItems']} items")
        if "maxItems" in schema and len(data) > schema["maxItems"]:
            errors.append(f"{path}: expected at most {schema['maxItems']} items")
        if "items" in schema:
            for index, item in enumerate(data):
                errors.extend(
                    self.validate(item, schema["items"], schema_file, root_schema, f"{path}[{index}]")
                )
        return errors

    def validate_string(self, data: str, schema: dict[str, Any], path: str) -> list[str]:
        errors: list[str] = []
        if "minLength" in schema and len(data) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(data) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], data):
            errors.append(f"{path}: does not match pattern {schema['pattern']!r}")
        if "format" in schema:
            fmt = schema["format"]
            if fmt == "date-time":
                try:
                    datetime.fromisoformat(data.replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"{path}: invalid date-time")
            elif fmt == "date":
                try:
                    date.fromisoformat(data)
                except ValueError:
                    errors.append(f"{path}: invalid date")
            elif fmt == "uri":
                parsed = urlparse(data)
                if not parsed.scheme:
                    errors.append(f"{path}: invalid uri")
        return errors

    def validate_number(self, data: int | float, schema: dict[str, Any], path: str) -> list[str]:
        errors: list[str] = []
        if "minimum" in schema and data < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and data > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")
        if "exclusiveMinimum" in schema and data <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: not greater than {schema['exclusiveMinimum']}")
        if "exclusiveMaximum" in schema and data >= schema["exclusiveMaximum"]:
            errors.append(f"{path}: not less than {schema['exclusiveMaximum']}")
        return errors

    @staticmethod
    def is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    def is_type(self, data: Any, expected: str) -> bool:
        if expected == "object":
            return isinstance(data, dict)
        if expected == "array":
            return isinstance(data, list)
        if expected == "string":
            return isinstance(data, str)
        if expected == "boolean":
            return isinstance(data, bool)
        if expected == "number":
            return self.is_number(data)
        if expected == "integer":
            return isinstance(data, int) and not isinstance(data, bool)
        if expected == "null":
            return data is None
        raise SchemaError(f"unsupported schema type {expected!r}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_for(path: Path, spec_root: Path = SPEC) -> Path | None:
    name = path.name
    parts = path.parts
    if "invalid" in parts or "source" in parts or "live" in parts:
        return None
    if "benchmark" in parts:
        return spec_root / "benchmark-run.schema.json"
    if "requests" in parts:
        return spec_root / "forecast-request.schema.json"
    if name.endswith("-question.json") or name.endswith("-question.generated.json"):
        return spec_root / "forecast-question.schema.json"
    if name.endswith("-history.json") or name.endswith("-history.generated.json"):
        return spec_root / "forecast-history.schema.json"
    if name.endswith("-evidence.json") or name.endswith("-evidence.generated.json"):
        return spec_root / "evidence-packet.schema.json"
    if name.endswith("-artifact.json") or name.endswith("-artifact.generated.json"):
        return spec_root / "forecast-artifact.schema.json"
    if name.endswith("-resolution.json") or name.endswith("-resolution.generated.json"):
        return spec_root / "resolution-record.schema.json"
    if name.endswith("-scoring.json") or name.endswith("-scoring.generated.json"):
        return spec_root / "scoring-report.schema.json"
    if name.endswith("-track-record.json") or name.endswith("-track-record.generated.json"):
        return spec_root / "track-record-report.schema.json"
    if name.endswith("-calibration.generated.json"):
        return spec_root / "calibration-summary.schema.json"
    if name.endswith("-pipeline-run.generated.json"):
        return spec_root / "pipeline-run.schema.json"
    if name == "record-index.generated.json":
        return spec_root / "record-index.schema.json"
    if name == "release-manifest.generated.json":
        return spec_root / "release-manifest.schema.json"
    if name == "weather-logistics-aggregate-forecast.json":
        return spec_root / "aggregate-forecast.schema.json"
    return None


def iter_contract_records(fixtures_root: Path = SPEC / "fixtures", spec_root: Path = SPEC) -> list[tuple[Path, Path]]:
    records: list[tuple[Path, Path]] = []
    for path in sorted(fixtures_root.rglob("*.json")):
        schema = schema_for(path, spec_root)
        if schema is not None:
            records.append((path, schema))
    return records


def validate_record(
    data: Any,
    schema_path: Path,
    validator: Validator | None = None,
) -> list[str]:
    validator = validator or Validator()
    schema = validator.load_schema(schema_path)
    return validator.validate(data, schema, schema_path, schema)


def validate_file(
    record_path: Path,
    schema_path: Path | None = None,
    validator: Validator | None = None,
) -> tuple[Path, list[str]]:
    schema_path = schema_path or schema_for(record_path)
    if schema_path is None:
        raise SchemaError(f"no schema could be inferred for {record_path}")
    return schema_path, validate_record(load_json(record_path), schema_path, validator)
