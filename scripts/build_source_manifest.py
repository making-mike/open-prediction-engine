#!/usr/bin/env python3
"""Inspect approved local files and draft source manifest inputs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from generate_domain_setups import WEATHER_DOMAIN
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
LOCAL_FIXTURES = ROOT / "spec" / "fixtures" / "local-source-files"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-builder"
BUILD_SCHEMA = SPEC / "source-manifest-build.schema.json"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"

GENERATED_AT = "2026-06-06T17:30:00Z"
CREATED_AT = "2026-06-02T10:15:00Z"
FORECAST_CLOSE_TIME = "2026-06-02T12:00:00Z"
MAX_FILE_BYTES = 2048

CASE_ORDER = ["local_draft", "contains_secret", "unsupported_format", "oversized", "leakage"]

SECRET_TOKENS = {"api_key", "apikey", "secret", "password", "passwd", "token", "credential", "bearer"}
PERSONAL_TOKENS = {"email", "phone", "full_name", "name", "address"}
LEAKAGE_FIELDS = {"actual_disruption", "resolved_at", "outcome_known_at", "post_outcome_notes"}
TRUE_VALUES = {"true", "1", "yes", "y"}

TARGET_REGISTRY = {
    "weather_forecast": {
        "geography": ("string", {"geography"}, {"city", "location"}),
        "service_date": ("date", {"service_date"}, {"date", "forecast_date"}),
        "retrieved_at": ("date_time", {"retrieved_at"}, {"loaded_at", "captured_at"}),
        "forecast_daily_precipitation_mm": (
            "number",
            {"forecast_daily_precipitation_mm"},
            {"rain_mm", "daily_precipitation_mm"},
        ),
    },
    "historical_baseline": {
        "service_date": ("date", {"service_date"}, {"date"}),
        "geography": ("string", {"geography"}, {"city", "location"}),
        "disruption_observed": ("boolean", {"disruption_observed"}, {"disrupted", "actual_disruption"}),
    },
    "declared_operations_outcome": {
        "service_date": ("date", {"service_date"}, {"date"}),
        "geography": ("string", {"geography"}, {"city", "location"}),
        "disruption_observed": ("boolean", {"disruption_observed"}, {"disrupted", "actual_disruption"}),
    },
}


class SourceBuildError(Exception):
    pass


@dataclass
class FieldStats:
    name: str
    values: list[Any]


@dataclass
class FileInspection:
    file_id: str
    source_role: str
    path: Path
    file_format: str
    byte_size: int
    content_hash: str | None
    status: str
    reason_codes: list[str]
    rows: list[dict[str, Any]]
    fields: list[FieldStats]
    contains_secrets: bool
    contains_personal_data: bool
    has_leakage_indicators: bool
    available_before_close: bool
    retrieved_at: str | None

    @property
    def row_count(self) -> int | None:
        if self.status != "inspected":
            return None
        return len(self.rows)


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def normalize_field(value: str) -> str:
    lowered = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    if not normalized:
        normalized = "field"
    if not normalized[0].isalpha():
        normalized = f"field_{normalized}"
    return normalized


def normalize_value(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or "unknown"


def parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_date(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
        return text


def scalar(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value).strip()
    if text == "":
        return None
    return text


def coerce_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def detect_type(name: str, values: list[Any]) -> str:
    present = [value for value in values if value is not None]
    if not present:
        return "unknown"
    if name.endswith("_id") or name in {"id", "asset_identifier", "vessel_id", "ship_id"}:
        return "id"
    if all(isinstance(value, bool) or str(value).strip().lower() in TRUE_VALUES | {"false", "0", "no", "n"} for value in present):
        return "boolean"
    if all(parse_timestamp(value) is not None and "T" in str(value) for value in present):
        return "date_time"
    if all(parse_date(value) is not None for value in present):
        return "date"
    if all(coerce_number(value) is not None for value in present):
        if all(float(coerce_number(value) or 0).is_integer() for value in present):
            return "integer"
        return "number"
    unique = {str(value).strip().lower() for value in present}
    if len(unique) <= 8:
        return "categorical"
    return "string"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".json":
        return "json"
    return "unsupported"


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in raw.items():
        normalized[normalize_field(str(key))] = scalar(value)
    return normalized


def read_rows(path: Path, fmt: str) -> list[dict[str, Any]]:
    if fmt == "csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return [normalize_record(row) for row in csv.DictReader(handle)]
    if fmt == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("records"), list):
            data = data["records"]
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise SourceBuildError("JSON source must be an array of objects or an object with a records array")
        return [normalize_record(item) for item in data]
    raise SourceBuildError(f"unsupported format: {fmt}")


def build_field_stats(rows: list[dict[str, Any]]) -> list[FieldStats]:
    names: list[str] = []
    for row in rows:
        for name in row:
            if name not in names:
                names.append(name)
    return [FieldStats(name=name, values=[row.get(name) for row in rows]) for name in names]


def contains_secret(fields: list[FieldStats]) -> bool:
    for field in fields:
        tokens = set(field.name.split("_"))
        if field.name in SECRET_TOKENS or tokens & SECRET_TOKENS:
            return True
        for value in field.values:
            lowered = str(value).strip().lower()
            if "secret" in lowered or "bearer " in lowered:
                return True
    return False


def contains_personal_data(fields: list[FieldStats]) -> bool:
    for field in fields:
        tokens = set(field.name.split("_"))
        if field.name in PERSONAL_TOKENS or tokens & PERSONAL_TOKENS:
            return True
    return False


def has_leakage(path: Path, source_role: str, fields: list[FieldStats]) -> bool:
    field_names = {field.name for field in fields}
    if "post_outcome" in normalize_field(path.stem):
        return True
    if source_role == "declared_operations_outcome":
        return False
    return bool(field_names & LEAKAGE_FIELDS)


def retrieved_at(fields: list[FieldStats]) -> str | None:
    for name in ("retrieved_at", "loaded_at", "captured_at"):
        field = next((item for item in fields if item.name == name), None)
        if field is None:
            continue
        for value in field.values:
            parsed = parse_timestamp(value)
            if parsed is not None:
                return parsed.isoformat().replace("+00:00", "Z")
    return None


def inspect_file(file_id: str, source_role: str, path: Path) -> FileInspection:
    path = path.resolve()
    fmt = file_format(path)
    byte_size = path.stat().st_size if path.exists() else 0
    content_hash = sha256(path) if path.exists() else None
    reason_codes: list[str] = []
    rows: list[dict[str, Any]] = []
    fields: list[FieldStats] = []

    if not path.exists():
        reason_codes.append("file_not_found")
    if fmt == "unsupported":
        reason_codes.append("unsupported_format")
    if byte_size > MAX_FILE_BYTES:
        reason_codes.append("file_too_large")

    if not reason_codes:
        try:
            rows = read_rows(path, fmt)
            fields = build_field_stats(rows)
        except (OSError, json.JSONDecodeError, csv.Error, SourceBuildError):
            reason_codes.append("parse_failed")

    secret_flag = contains_secret(fields)
    personal_flag = contains_personal_data(fields)
    leakage_flag = has_leakage(path, source_role, fields)
    if secret_flag:
        reason_codes.append("source_contains_secrets")
    if leakage_flag:
        reason_codes.append("post_outcome_leakage_indicator")

    retrieved = retrieved_at(fields)
    close = parse_timestamp(FORECAST_CLOSE_TIME)
    retrieved_dt = parse_timestamp(retrieved)
    available_before_close = True
    if source_role == "declared_operations_outcome":
        available_before_close = False
    elif retrieved_dt is not None and close is not None:
        available_before_close = retrieved_dt <= close

    status = "rejected" if reason_codes else "inspected"
    return FileInspection(
        file_id=file_id,
        source_role=source_role,
        path=path,
        file_format=fmt,
        byte_size=byte_size,
        content_hash=content_hash,
        status=status,
        reason_codes=sorted(set(reason_codes)),
        rows=rows,
        fields=fields,
        contains_secrets=secret_flag,
        contains_personal_data=personal_flag,
        has_leakage_indicators=leakage_flag,
        available_before_close=available_before_close,
        retrieved_at=retrieved,
    )


def source_class(source_role: str) -> str:
    if source_role == "weather_forecast":
        return "public_dataset"
    return "internal_dataset"


def max_source_age(source_role: str) -> int:
    if source_role == "weather_forecast":
        return 24
    return 8760


def display_name(source_role: str) -> str:
    return source_role.replace("_", " ").title()


def local_ref(path: Path) -> str:
    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        rel = path
    return f"local://{rel}"


def source_ref(path: Path) -> str:
    return local_ref(path).replace("\\", "/")


def field_inventory(fields: list[FieldStats], sample_count: int) -> list[dict[str, Any]]:
    inventory = []
    for field in fields:
        inventory.append(
            {
                "fieldName": field.name,
                "observedType": detect_type(field.name, field.values),
                "sampleCount": sample_count,
                "nonNullCount": len([value for value in field.values if value is not None]),
                "exampleValuesStored": False,
            }
        )
    return inventory


def first_value(fields: list[FieldStats], names: set[str]) -> Any:
    for field in fields:
        if field.name not in names:
            continue
        for value in field.values:
            if value is not None:
                return value
    return None


def values_for(fields: list[FieldStats], names: set[str]) -> list[Any]:
    values: list[Any] = []
    for field in fields:
        if field.name in names:
            values.extend([value for value in field.values if value is not None])
    return values


def service_dates(fields: list[FieldStats]) -> tuple[str | None, str | None]:
    parsed = [
        value
        for value in (parse_date(item) for item in values_for(fields, {"service_date", "date", "forecast_date"}))
        if value is not None
    ]
    if not parsed:
        return None, None
    return min(parsed), max(parsed)


def geographies(fields: list[FieldStats]) -> list[str]:
    values = values_for(fields, {"geography", "city", "location", "port"})
    normalized = sorted({normalize_value(str(value)) for value in values if str(value).strip()})
    return normalized[:24]


def entity_identifiers(fields: list[FieldStats]) -> list[str]:
    values = values_for(fields, {"asset_identifier", "vessel_id", "ship_id", "vehicle_id"})
    normalized = sorted({str(value).strip() for value in values if str(value).strip()})
    return normalized[:80]


def positive_outcome_count(fields: list[FieldStats]) -> int | None:
    values = values_for(fields, {"disruption_observed", "disrupted", "actual_disruption"})
    if not values:
        return None
    return len([value for value in values if str(value).strip().lower() in TRUE_VALUES])


def feature_summary(fields: list[FieldStats]) -> dict[str, Any] | None:
    numeric_values = []
    categorical_values = []
    for field in fields:
        if field.name in {"rain_mm", "forecast_daily_precipitation_mm", "precipitation_mm"}:
            value = next((coerce_number(item) for item in field.values if coerce_number(item) is not None), None)
            if value is not None:
                target_name = "forecast_daily_precipitation_mm" if field.name == "rain_mm" else field.name
                numeric_values.append({"fieldName": target_name, "value": value, "unit": "mm"})
        if field.name == "source_status":
            value = next((str(item) for item in field.values if item is not None), None)
            if value is not None:
                categorical_values.append({"fieldName": field.name, "value": value})
    if not numeric_values and not categorical_values:
        return None
    return {
        "numericValues": numeric_values[:24],
        "categoricalValues": categorical_values[:24],
    }


def build_source_entry(index: int, inspection: FileInspection) -> dict[str, Any]:
    start, end = service_dates(inspection.fields)
    entry = {
        "sourceId": f"localsource-{index:03d}",
        "sourceRole": inspection.source_role,
        "displayName": display_name(inspection.source_role),
        "connectorType": "local_file",
        "sourceClass": source_class(inspection.source_role),
        "sourceRef": source_ref(inspection.path),
        "contentHash": inspection.content_hash or "missing-hash",
        "rowCount": inspection.row_count or 0,
        "positiveOutcomeCount": positive_outcome_count(inspection.fields),
        "retrieval": {
            "retrievedAt": inspection.retrieved_at if inspection.source_role == "weather_forecast" else CREATED_AT if inspection.source_role != "declared_operations_outcome" else None,
            "availableBeforeForecastClose": inspection.available_before_close,
            "maxSourceAgeHours": max_source_age(inspection.source_role),
        },
        "coverage": {
            "geographies": geographies(inspection.fields),
            "serviceDateStart": start,
            "serviceDateEnd": end,
            "entityIdentifiers": entity_identifiers(inspection.fields),
        },
        "privacy": {
            "privacyClass": (
                "personal"
                if inspection.contains_personal_data
                else "public"
                if source_class(inspection.source_role) == "public_dataset"
                else "internal"
            ),
            "containsSecrets": inspection.contains_secrets,
            "containsPersonalData": inspection.contains_personal_data,
            "approvalRequired": inspection.contains_personal_data,
            "rawRetention": "metadata_only",
        },
        "fieldInventory": field_inventory(inspection.fields, inspection.row_count or 0),
    }
    summary = feature_summary(inspection.fields)
    if summary is not None:
        entry["featureSummary"] = summary
    return entry


def mapping_entry(
    index: int,
    source_id: str,
    source_role: str,
    source_field: str,
    target_field: str,
    target_type: str,
    origin: str,
) -> dict[str, Any]:
    proposed = origin == "agent_inferred"
    if origin == "user_provided":
        note = "Caller-provided mapping hint."
        confidence = 1.0
    elif proposed:
        note = "Agent-inferred mapping must be confirmed before forecast execution."
        confidence = 0.72
    else:
        note = "Registry-backed local field match."
        confidence = 0.98
    return {
        "mappingId": f"draftmapping-{index:03d}",
        "sourceId": source_id,
        "sourceRole": source_role,
        "sourceField": source_field,
        "targetField": target_field,
        "targetFieldType": target_type,
        "mappingOrigin": origin,
        "mappingStatus": "proposed" if proposed else "confirmed",
        "confidence": confidence,
        "requiresConfirmation": proposed,
        "validationNotes": [note],
    }


def target_type_for(source_role: str, target_field: str) -> str:
    registry = TARGET_REGISTRY.get(source_role, {})
    if target_field in registry:
        return registry[target_field][0]
    return "string"


def build_mappings(
    source_entries: list[dict[str, Any]],
    inspections: list[FileInspection],
    mapping_hints: dict[tuple[str, str], str] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mappings: list[dict[str, Any]] = []
    aliases: list[dict[str, Any]] = []
    mapping_index = 1
    alias_index = 1
    mapping_hints = mapping_hints or {}

    for source_entry_data, inspection in zip(source_entries, inspections):
        registry = TARGET_REGISTRY.get(inspection.source_role, {})
        field_names = [field.name for field in inspection.fields]
        mapped_targets: set[str] = set()
        for field_name in field_names:
            hinted_target = mapping_hints.get((inspection.source_role, field_name))
            if hinted_target is None:
                continue
            mappings.append(
                mapping_entry(
                    mapping_index,
                    source_entry_data["sourceId"],
                    inspection.source_role,
                    field_name,
                    hinted_target,
                    target_type_for(inspection.source_role, hinted_target),
                    "user_provided",
                )
            )
            mapped_targets.add(hinted_target)
            mapping_index += 1
        for target_field, (target_type, exact_names, inferred_names) in registry.items():
            if target_field in mapped_targets:
                continue
            for field_name in field_names:
                if field_name in exact_names:
                    mappings.append(
                        mapping_entry(
                            mapping_index,
                            source_entry_data["sourceId"],
                            inspection.source_role,
                            field_name,
                            target_field,
                            target_type,
                            "registry_backed",
                        )
                    )
                    mapping_index += 1
                    break
                if field_name in inferred_names:
                    mappings.append(
                        mapping_entry(
                            mapping_index,
                            source_entry_data["sourceId"],
                            inspection.source_role,
                            field_name,
                            target_field,
                            target_type,
                            "agent_inferred",
                        )
                    )
                    mapping_index += 1
                    break

        geography_fields = [field for field in inspection.fields if field.name in {"geography", "city", "location", "port"}]
        for field in geography_fields:
            for raw_value in field.values[:4]:
                if raw_value is None:
                    continue
                source_value = str(raw_value).strip()
                canonical = normalize_value(source_value)
                proposed = source_value != canonical
                aliases.append(
                    {
                        "aliasMappingId": f"draftaliasmapping-{alias_index:03d}",
                        "entityType": "geography",
                        "sourceValue": source_value,
                        "canonicalValue": canonical,
                        "mappingOrigin": "agent_inferred" if proposed else "registry_backed",
                        "mappingStatus": "proposed" if proposed else "confirmed",
                        "requiresConfirmation": proposed,
                    }
                )
                alias_index += 1
                break

    return mappings, aliases


def build_manifest(case_number: int, inspections: list[FileInspection]) -> dict[str, Any]:
    sources = [build_source_entry(index, inspection) for index, inspection in enumerate(inspections, start=1)]
    return {
        "sourceManifestId": f"sourcemanifestdraft-{case_number:03d}",
        "createdAt": CREATED_AT,
        "domainSetupId": "domainsetup-001",
        "domain": WEATHER_DOMAIN,
        "forecastParameters": {
            "questionTemplateId": "template-001",
            "horizonLabel": "1-day",
            "forecastCloseTime": FORECAST_CLOSE_TIME,
            "geography": "Warsaw",
            "serviceDate": "2026-06-03",
            "assetIdentifier": None,
            "location": None,
            "targetWindow": None,
        },
        "sources": sources,
    }


def build_field_mapping(
    case_number: int,
    manifest: dict[str, Any],
    inspections: list[FileInspection],
    mapping_hints: dict[tuple[str, str], str] | None = None,
) -> dict[str, Any]:
    mappings, aliases = build_mappings(manifest["sources"], inspections, mapping_hints)
    return {
        "fieldMappingId": f"fieldmappingdraft-{case_number:03d}",
        "createdAt": CREATED_AT,
        "domainSetupId": "domainsetup-001",
        "domain": WEATHER_DOMAIN,
        "sourceManifestId": manifest["sourceManifestId"],
        "mappings": mappings,
        "aliasMappings": aliases,
    }


def decision_for(inspection: FileInspection) -> dict[str, Any]:
    try:
        rel = inspection.path.relative_to(ROOT)
    except ValueError:
        rel = inspection.path
    return {
        "fileId": inspection.file_id,
        "localPath": str(rel),
        "sourceRole": inspection.source_role,
        "fileFormat": inspection.file_format,
        "inspectionStatus": inspection.status,
        "byteSize": inspection.byte_size,
        "rowCount": inspection.row_count,
        "contentHash": inspection.content_hash,
        "detectedFields": [field.name for field in inspection.fields],
        "privacyFlags": {
            "containsSecrets": inspection.contains_secrets,
            "containsPersonalData": inspection.contains_personal_data,
            "approvalRequired": inspection.contains_personal_data,
        },
        "leakageFlags": {
            "hasPostOutcomeIndicators": inspection.has_leakage_indicators,
            "availableBeforeForecastClose": inspection.available_before_close,
        },
        "reasonCodes": inspection.reason_codes,
    }


def build_paths(case: str) -> tuple[Path, Path, Path]:
    slug = case_slug(case)
    return (
        GENERATED / f"weather-logistics-{slug}-source-manifest-build.generated.json",
        GENERATED / f"weather-logistics-{slug}-source-manifest.json",
        GENERATED / f"weather-logistics-{slug}-field-mapping.json",
    )


def build_case(case: str) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    fixture_cases = {
        "local_draft": {
            "inputs": [
                ("weather_forecast", LOCAL_FIXTURES / "weather-forecast.json"),
                ("historical_baseline", LOCAL_FIXTURES / "history.csv"),
                ("declared_operations_outcome", LOCAL_FIXTURES / "outcome.csv"),
            ],
            "mapping_hints": {
                ("declared_operations_outcome", "date"): "service_date",
            },
        },
        "contains_secret": {
            "inputs": [
                ("historical_baseline", LOCAL_FIXTURES / "contains-secret.csv"),
            ],
            "mapping_hints": {},
        },
        "unsupported_format": {
            "inputs": [
                ("historical_baseline", LOCAL_FIXTURES / "unsupported.txt"),
            ],
            "mapping_hints": {},
        },
        "oversized": {
            "inputs": [
                ("historical_baseline", LOCAL_FIXTURES / "oversized.csv"),
            ],
            "mapping_hints": {},
        },
        "leakage": {
            "inputs": [
                ("weather_forecast", LOCAL_FIXTURES / "post-outcome-leakage.csv"),
            ],
            "mapping_hints": {},
        },
    }
    if case not in fixture_cases:
        raise SourceBuildError(f"unknown case: {case}")
    fixture = fixture_cases[case]
    return build_from_inputs(
        CASE_ORDER.index(case) + 1,
        case,
        fixture["inputs"],
        mapping_hints=fixture["mapping_hints"],
    )


def build_from_inputs(
    case_number: int,
    case: str,
    inputs: list[tuple[str, Path]],
    output_dir: Path = GENERATED,
    mapping_hints: dict[tuple[str, str], str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    inspections = [
        inspect_file(f"localfile-{index:03d}", source_role, path)
        for index, (source_role, path) in enumerate(inputs, start=1)
    ]
    rejected = any(inspection.status == "rejected" for inspection in inspections)
    manifest = None
    field_mapping = None
    if not rejected:
        manifest = build_manifest(case_number, inspections)
        field_mapping = build_field_mapping(case_number, manifest, inspections, mapping_hints)
        validate_or_raise(manifest, SOURCE_MANIFEST_SCHEMA, "source manifest")
        validate_or_raise(field_mapping, FIELD_MAPPING_SCHEMA, "field mapping")

    build_path, manifest_path, mapping_path = build_paths(case)
    if output_dir != GENERATED:
        output_dir = output_dir.resolve()
        build_path = output_dir / build_path.name
        manifest_path = output_dir / manifest_path.name
        mapping_path = output_dir / mapping_path.name

    proposed_mappings = []
    if field_mapping is not None:
        proposed_mappings = [
            item for item in field_mapping["mappings"] + field_mapping["aliasMappings"]
            if item["mappingOrigin"] == "agent_inferred" and item["requiresConfirmation"]
        ]
    confirmation_required = bool(proposed_mappings)
    draft_artifacts = {
        "sourceManifestId": manifest["sourceManifestId"] if manifest else None,
        "fieldMappingId": field_mapping["fieldMappingId"] if field_mapping else None,
        "sourceManifestPath": str(manifest_path.relative_to(ROOT)) if manifest else None,
        "fieldMappingPath": str(mapping_path.relative_to(ROOT)) if field_mapping else None,
    }
    required_actions = []
    warnings = [
        "Local builder drafts are not public read surfaces and do not authorize forecast execution.",
    ]
    if rejected:
        required_actions.append("Remove rejected files or provide caller-approved supported CSV/JSON sources.")
    if confirmation_required:
        required_actions.append("Confirm proposed agent-inferred mappings before source intake can allow forecast execution.")
    build = {
        "sourceManifestBuildId": f"sourcemanifestbuild-{case_number:03d}",
        "generatedAt": GENERATED_AT,
        "domainSetupId": "domainsetup-001",
        "domain": WEATHER_DOMAIN,
        "buildStatus": "rejected" if rejected else "draft_ready",
        "forecastGenerationAllowed": False,
        "canEnterSourceIntake": not rejected,
        "confirmationRequired": confirmation_required,
        "inputFiles": [decision_for(inspection) for inspection in inspections],
        "draftArtifacts": draft_artifacts,
        "requiredActions": required_actions,
        "warnings": warnings,
    }
    validate_or_raise(build, BUILD_SCHEMA, "source manifest build")
    return build, manifest, field_mapping


def validate_or_raise(record: dict[str, Any], schema: Path, label: str) -> None:
    errors = validate_record(record, schema)
    if errors:
        raise AssertionError(f"{label} schema validation failed: {errors[0]}")


def write_case(case: str, build: dict[str, Any], manifest: dict[str, Any] | None, field_mapping: dict[str, Any] | None) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    build_path, manifest_path, mapping_path = build_paths(case)
    build_path.write_text(render_json(build), encoding="utf-8")
    if manifest is not None:
        manifest_path.write_text(render_json(manifest), encoding="utf-8")
    if field_mapping is not None:
        mapping_path.write_text(render_json(field_mapping), encoding="utf-8")


def check_case(case: str, build: dict[str, Any], manifest: dict[str, Any] | None, field_mapping: dict[str, Any] | None) -> None:
    build_path, manifest_path, mapping_path = build_paths(case)
    expected = {
        build_path: render_json(build),
    }
    if manifest is not None:
        expected[manifest_path] = render_json(manifest)
    if field_mapping is not None:
        expected[mapping_path] = render_json(field_mapping)
    for path, expected_text in expected.items():
        if not path.exists():
            print(f"missing source builder fixture: {path}", file=sys.stderr)
            print("run `python3 scripts/build_source_manifest.py --write`", file=sys.stderr)
            raise SystemExit(1)
        actual = path.read_text(encoding="utf-8")
        if actual != expected_text:
            print(f"source builder fixture drift: {path}", file=sys.stderr)
            print("run `python3 scripts/build_source_manifest.py --write`", file=sys.stderr)
            raise SystemExit(1)


def parse_inputs(raw_inputs: list[str]) -> list[tuple[str, Path]]:
    parsed = []
    for item in raw_inputs:
        if "=" not in item:
            raise SourceBuildError("--input values must use source_role=path")
        role, path = item.split("=", 1)
        parsed.append((normalize_field(role), (ROOT / path).resolve() if not Path(path).is_absolute() else Path(path)))
    return parsed


def parse_mapping_hints(raw_hints: list[str]) -> dict[tuple[str, str], str]:
    parsed: dict[tuple[str, str], str] = {}
    for item in raw_hints:
        if "=" not in item or "." not in item.split("=", 1)[0]:
            raise SourceBuildError("--mapping-hint values must use source_role.source_field=target_field")
        source, target = item.split("=", 1)
        role, field = source.split(".", 1)
        parsed[(normalize_field(role), normalize_field(field))] = normalize_field(target)
    return parsed


def print_summary() -> None:
    builds = []
    for case in CASE_ORDER:
        build, _manifest, _mapping = build_case(case)
        builds.append(
            {
                "case": case,
                "sourceManifestBuildId": build["sourceManifestBuildId"],
                "buildStatus": build["buildStatus"],
                "canEnterSourceIntake": build["canEnterSourceIntake"],
                "confirmationRequired": build["confirmationRequired"],
                "forecastGenerationAllowed": build["forecastGenerationAllowed"],
            }
        )
    print(render_json({"count": len(builds), "builds": builds}), end="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print, check, or write one generated builder case")
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="inspect a caller-approved local file as source_role=path",
    )
    parser.add_argument(
        "--mapping-hint",
        action="append",
        default=[],
        help="mark a caller-provided mapping hint as source_role.source_field=target_field",
    )
    parser.add_argument("--output-dir", default=str(GENERATED), help="directory for generic --input draft outputs")
    parser.add_argument("--check", action="store_true", help="check generated builder fixtures")
    parser.add_argument("--write", action="store_true", help="write generated builder fixtures or generic draft outputs")
    args = parser.parse_args()

    if args.input:
        output_dir = Path(args.output_dir) if args.output_dir else GENERATED
        build, manifest, field_mapping = build_from_inputs(
            999,
            "local-input",
            parse_inputs(args.input),
            output_dir,
            mapping_hints=parse_mapping_hints(args.mapping_hint),
        )
        if args.write:
            output_dir.mkdir(parents=True, exist_ok=True)
            build_path = output_dir / "weather-logistics-local-input-source-manifest-build.generated.json"
            build_path.write_text(render_json(build), encoding="utf-8")
            if manifest is not None:
                (output_dir / "weather-logistics-local-input-source-manifest.json").write_text(render_json(manifest), encoding="utf-8")
            if field_mapping is not None:
                (output_dir / "weather-logistics-local-input-field-mapping.json").write_text(render_json(field_mapping), encoding="utf-8")
        else:
            print(render_json(build), end="")
        return

    if args.case:
        build, manifest, field_mapping = build_case(args.case)
        if args.write:
            write_case(args.case, build, manifest, field_mapping)
            print(f"generated source builder fixture for {args.case}")
        elif args.check:
            check_case(args.case, build, manifest, field_mapping)
            print(f"checked source builder fixture for {args.case}")
        else:
            print(render_json(build), end="")
        return

    if args.write:
        for case in CASE_ORDER:
            write_case(case, *build_case(case))
        print("generated source builder fixtures")
    elif args.check:
        for case in CASE_ORDER:
            check_case(case, *build_case(case))
        print("checked source builder fixtures")
    else:
        print_summary()


if __name__ == "__main__":
    main()
