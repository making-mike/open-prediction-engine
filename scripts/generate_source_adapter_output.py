#!/usr/bin/env python3
"""Generate or check source adapter output handoff fixtures."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
LOCAL_FIXTURES = ROOT / "spec" / "fixtures" / "local-source-files"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-adapter-output"
OUTPUT_PATH = GENERATED / "weather-transit-delays-source-adapter-output.generated.json"
SCHEMA = SPEC / "source-adapter-output.schema.json"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"
GENERATED_AT = "2026-06-10T02:05:00Z"
FORECAST_CLOSE = "2026-06-10T02:30:00Z"

WEATHER = LOCAL_FIXTURES / "transit-weather-forecast.json"
HISTORY = LOCAL_FIXTURES / "transit-delay-history.csv"
TRIP_UPDATES = LOCAL_FIXTURES / "transit-trip-updates.csv"


class SourceAdapterOutputError(Exception):
    pass


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_uri(path: Path) -> str:
    return f"local://{path.relative_to(ROOT)}"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_json_rows(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
        raise SourceAdapterOutputError("JSON source must be an array of objects")
    return data


def bool_count(rows: list[dict[str, str]], field: str) -> int:
    return sum(1 for row in rows if str(row.get(field, "")).strip().lower() in {"true", "1", "yes"})


def late_count(rows: list[dict[str, str]], late_seconds: int) -> int:
    count = 0
    for row in rows:
        try:
            if float(row.get("delay_seconds", "")) >= late_seconds:
                count += 1
        except ValueError:
            pass
    return count


def field(field_name: str, observed_type: str, sample_count: int, non_null_count: int | None = None) -> dict[str, Any]:
    return {
        "fieldName": field_name,
        "observedType": observed_type,
        "sampleCount": sample_count,
        "nonNullCount": sample_count if non_null_count is None else non_null_count,
        "exampleValuesStored": False,
    }


def source_entry(
    *,
    source_id: str,
    source_role: str,
    display_name: str,
    path: Path,
    row_count: int,
    positive_outcome_count: int | None,
    retrieved_at: str | None,
    available_before_close: bool,
    max_source_age_hours: int,
    service_date_start: str | None,
    service_date_end: str | None,
    fields: list[dict[str, Any]],
    feature_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "sourceId": source_id,
        "sourceRole": source_role,
        "displayName": display_name,
        "connectorType": "agent_extraction",
        "sourceClass": "public_dataset",
        "sourceRef": local_uri(path),
        "contentHash": sha256(path),
        "rowCount": row_count,
        "positiveOutcomeCount": positive_outcome_count,
        "retrieval": {
            "retrievedAt": retrieved_at,
            "availableBeforeForecastClose": available_before_close,
            "maxSourceAgeHours": max_source_age_hours,
        },
        "coverage": {
            "geographies": ["helsinki"],
            "serviceDateStart": service_date_start,
            "serviceDateEnd": service_date_end,
            "entityIdentifiers": ["hsl-surface"],
        },
        "privacy": {
            "privacyClass": "public",
            "containsSecrets": False,
            "containsPersonalData": False,
            "approvalRequired": False,
            "rawRetention": "metadata_only",
        },
        "fieldInventory": fields,
    }
    if feature_summary is not None:
        entry["featureSummary"] = feature_summary
    return entry


def build_source_manifest() -> dict[str, Any]:
    weather_rows = load_json_rows(WEATHER)
    history_rows = load_csv(HISTORY)
    update_rows = load_csv(TRIP_UPDATES)
    weather_row = weather_rows[0]
    return {
        "sourceManifestId": "sourcemanifest-1201",
        "createdAt": GENERATED_AT,
        "domainSetupId": "domainsetup-003",
        "domain": "weather-transit-delays",
        "forecastParameters": {
            "questionTemplateId": "template-003",
            "horizonLabel": "same-day-morning-peak",
            "forecastCloseTime": FORECAST_CLOSE,
            "geography": "helsinki",
            "serviceDate": "2026-06-10",
            "assetIdentifier": "hsl-surface",
            "location": "helsinki",
            "targetWindow": "morning_peak",
        },
        "sources": [
            source_entry(
                source_id="source-1201",
                source_role="weather_forecast",
                display_name="Transit weather forecast adapter output",
                path=WEATHER,
                row_count=len(weather_rows),
                positive_outcome_count=None,
                retrieved_at=str(weather_row["retrieved_at"]),
                available_before_close=True,
                max_source_age_hours=6,
                service_date_start="2026-06-10",
                service_date_end="2026-06-10",
                fields=[
                    field("network", "string", 1),
                    field("geography", "string", 1),
                    field("service_date", "date", 1),
                    field("service_window", "categorical", 1),
                    field("retrieved_at", "date_time", 1),
                    field("forecast_precipitation_mm", "number", 1),
                    field("forecast_snowfall_mm", "number", 1),
                    field("forecast_wind_gust_kmh", "number", 1),
                    field("temperature_c", "number", 1),
                    field("source_status", "categorical", 1),
                ],
                feature_summary={
                    "numericValues": [
                        {"fieldName": "forecast_precipitation_mm", "value": 8.5, "unit": "mm"},
                        {"fieldName": "forecast_snowfall_mm", "value": 0.0, "unit": "mm"},
                        {"fieldName": "forecast_wind_gust_kmh", "value": 42.0, "unit": "kmh"},
                    ],
                    "categoricalValues": [
                        {"fieldName": "service_window", "value": "morning_peak"},
                        {"fieldName": "source_status", "value": "fixture"},
                    ],
                },
            ),
            source_entry(
                source_id="source-1202",
                source_role="historical_delay_baseline",
                display_name="Historical transit delay adapter output",
                path=HISTORY,
                row_count=len(history_rows),
                positive_outcome_count=bool_count(history_rows, "delay_event"),
                retrieved_at=GENERATED_AT,
                available_before_close=True,
                max_source_age_hours=8760,
                service_date_start="2026-05-01",
                service_date_end="2026-05-30",
                fields=[
                    field("service_date", "date", len(history_rows)),
                    field("network", "string", len(history_rows)),
                    field("geography", "string", len(history_rows)),
                    field("service_window", "categorical", len(history_rows)),
                    field("late_observation_ratio", "number", len(history_rows)),
                    field("delay_event", "boolean", len(history_rows)),
                ],
                feature_summary={
                    "numericValues": [
                        {"fieldName": "late_observation_ratio", "value": 0.23, "unit": "ratio"}
                    ],
                    "categoricalValues": [
                        {"fieldName": "service_window", "value": "morning_peak"}
                    ],
                },
            ),
            source_entry(
                source_id="source-1203",
                source_role="transit_delay_outcome",
                display_name="Transit delay outcome adapter output",
                path=TRIP_UPDATES,
                row_count=len(update_rows),
                positive_outcome_count=late_count(update_rows, 300),
                retrieved_at="2026-06-10T08:15:00Z",
                available_before_close=False,
                max_source_age_hours=24,
                service_date_start="2026-06-10",
                service_date_end="2026-06-10",
                fields=[
                    field("service_date", "date", len(update_rows)),
                    field("network", "string", len(update_rows)),
                    field("geography", "string", len(update_rows)),
                    field("service_window", "categorical", len(update_rows)),
                    field("captured_at", "date_time", len(update_rows)),
                    field("trip_id", "id", len(update_rows)),
                    field("stop_id", "id", len(update_rows)),
                    field("delay_seconds", "number", len(update_rows)),
                ],
                feature_summary={
                    "numericValues": [
                        {"fieldName": "delay_seconds", "value": 300.0, "unit": "seconds"}
                    ],
                    "categoricalValues": [
                        {"fieldName": "service_window", "value": "morning_peak"}
                    ],
                },
            ),
        ],
    }


def mapping(
    mapping_id: str,
    source_id: str,
    source_role: str,
    source_field: str,
    target_field: str,
    target_type: str,
) -> dict[str, Any]:
    return {
        "mappingId": mapping_id,
        "sourceId": source_id,
        "sourceRole": source_role,
        "sourceField": source_field,
        "targetField": target_field,
        "targetFieldType": target_type,
        "mappingOrigin": "deterministic_exact_match" if source_field == target_field else "user_provided",
        "mappingStatus": "confirmed",
        "confidence": 1.0,
        "requiresConfirmation": False,
        "validationNotes": ["Fixture mapping is explicit and confirmed for the adapter-output handoff."],
    }


def build_field_mapping(source_manifest: dict[str, Any]) -> dict[str, Any]:
    mapping_rows = [
        ("mapping-120101", "source-1201", "weather_forecast", "geography", "geography", "string"),
        ("mapping-120102", "source-1201", "weather_forecast", "service_date", "service_date", "date"),
        ("mapping-120103", "source-1201", "weather_forecast", "service_window", "service_window", "categorical"),
        ("mapping-120104", "source-1201", "weather_forecast", "retrieved_at", "retrieved_at", "date_time"),
        ("mapping-120105", "source-1201", "weather_forecast", "forecast_precipitation_mm", "forecast_precipitation_mm", "number"),
        ("mapping-120106", "source-1201", "weather_forecast", "forecast_snowfall_mm", "forecast_snowfall_mm", "number"),
        ("mapping-120107", "source-1201", "weather_forecast", "forecast_wind_gust_kmh", "forecast_wind_gust_kmh", "number"),
        ("mapping-120108", "source-1202", "historical_delay_baseline", "network", "transit_network", "string"),
        ("mapping-120109", "source-1202", "historical_delay_baseline", "service_date", "service_date", "date"),
        ("mapping-120110", "source-1202", "historical_delay_baseline", "service_window", "service_window", "categorical"),
        ("mapping-120111", "source-1202", "historical_delay_baseline", "late_observation_ratio", "late_observation_ratio", "number"),
        ("mapping-120112", "source-1202", "historical_delay_baseline", "delay_event", "delay_event", "boolean"),
        ("mapping-120113", "source-1203", "transit_delay_outcome", "network", "transit_network", "string"),
        ("mapping-120114", "source-1203", "transit_delay_outcome", "service_date", "service_date", "date"),
        ("mapping-120115", "source-1203", "transit_delay_outcome", "service_window", "service_window", "categorical"),
        ("mapping-120116", "source-1203", "transit_delay_outcome", "delay_seconds", "delay_seconds", "number"),
        ("mapping-120117", "source-1203", "transit_delay_outcome", "trip_id", "trip_id", "id"),
        ("mapping-120118", "source-1203", "transit_delay_outcome", "stop_id", "stop_id", "id"),
    ]
    return {
        "fieldMappingId": "fieldmapping-1201",
        "createdAt": GENERATED_AT,
        "domainSetupId": source_manifest["domainSetupId"],
        "domain": source_manifest["domain"],
        "sourceManifestId": source_manifest["sourceManifestId"],
        "mappings": [mapping(*item) for item in mapping_rows],
        "aliasMappings": [
            {
                "aliasMappingId": "aliasmapping-1201",
                "entityType": "transit_network",
                "sourceValue": "hsl-surface",
                "canonicalValue": "hsl-surface",
                "mappingOrigin": "user_provided",
                "mappingStatus": "confirmed",
                "requiresConfirmation": False,
            }
        ],
    }


def build_output() -> dict[str, Any]:
    source_manifest = build_source_manifest()
    field_mapping = build_field_mapping(source_manifest)
    output = {
        "sourceAdapterOutputId": "sourceadapteroutput-1201",
        "generatedAt": GENERATED_AT,
        "outputStatus": "intake_ready",
        "adapter": {
            "adapterId": "sourceadapter-1201",
            "displayName": "Weather transit delay external adapter fixture",
            "adapterVersion": "external-handoff-v0",
            "implementationLocation": "external_agent",
            "sourceKind": "agent_extraction",
            "ownsForecastSemantics": False,
        },
        "execution": {
            "adapterRunId": "adapterrun-1201",
            "executionMode": "fixture_replay",
            "startedAt": GENERATED_AT,
            "completedAt": GENERATED_AT,
            "normalChecksOffline": True,
            "liveFetchPerformed": False,
            "credentialsUsed": False,
            "credentialsStored": False,
        },
        "domainBinding": {
            "domainSetupId": source_manifest["domainSetupId"],
            "domain": source_manifest["domain"],
            "questionTemplateId": source_manifest["forecastParameters"]["questionTemplateId"],
            "sourceRoles": [item["sourceRole"] for item in source_manifest["sources"]],
        },
        "sourceManifest": source_manifest,
        "fieldMapping": field_mapping,
        "handoffBoundary": {
            "canEnterSourceIntake": True,
            "sourceIntakeRequired": True,
            "mappingConfirmationRequired": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "allowedNextCommands": [
                "python3 scripts/ope.py source-intake --case accepted",
                "python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
            ],
        },
        "provenanceSummary": {
            "sourceCount": len(source_manifest["sources"]),
            "rowCount": sum(item["rowCount"] for item in source_manifest["sources"]),
            "contentHashesStored": True,
            "rawRowsIncluded": False,
            "allEvidenceClaimed": False,
            "diagnostics": [
                {
                    "diagnosticId": "diagnostic-1201",
                    "level": "info",
                    "message": "Fixture adapter emitted sanitized source metadata and confirmed mappings.",
                    "rawDetailIncluded": False,
                }
            ],
        },
        "controls": {
            "readOnly": True,
            "forecastGenerationAllowed": False,
            "forecastArtifactsCreated": False,
            "sourceIntakeAlreadyRun": False,
            "credentialStorageImplemented": False,
            "promptVisibleCredentialsAccepted": False,
            "rawPrivateRowsStored": False,
            "sanitizedErrorsOnly": True,
        },
        "nextAction": "run_source_intake",
        "warnings": [
            "External adapter output is a handoff into source intake, not a forecast.",
            "Resolution rows are declared for outcome use and are not forecast-time evidence.",
            "The adapter does not store credentials or raw private rows.",
            "No live connector, calibration, or production quality claim is implied.",
        ],
    }
    validate_output(output)
    return output


def validate_output(output: dict[str, Any]) -> None:
    errors = validate_record(output, SCHEMA)
    if errors:
        raise SourceAdapterOutputError(f"source adapter output schema validation failed: {errors[0]}")
    for key, schema in [
        ("sourceManifest", SOURCE_MANIFEST_SCHEMA),
        ("fieldMapping", FIELD_MAPPING_SCHEMA),
    ]:
        nested_errors = validate_record(output[key], schema)
        if nested_errors:
            raise SourceAdapterOutputError(f"{key} schema validation failed: {nested_errors[0]}")
    manifest = output["sourceManifest"]
    mapping_record = output["fieldMapping"]
    if output["adapter"]["ownsForecastSemantics"]:
        raise SourceAdapterOutputError("source adapter must not own forecast semantics")
    if output["controls"]["forecastArtifactsCreated"] or output["handoffBoundary"]["createsForecastArtifacts"]:
        raise SourceAdapterOutputError("source adapter output must not create forecast artifacts")
    if output["controls"]["credentialStorageImplemented"] or output["execution"]["credentialsStored"]:
        raise SourceAdapterOutputError("source adapter output must not store credentials")
    if output["provenanceSummary"]["rawRowsIncluded"]:
        raise SourceAdapterOutputError("source adapter output must not include raw rows")
    if mapping_record["sourceManifestId"] != manifest["sourceManifestId"]:
        raise SourceAdapterOutputError("field mapping must bind the embedded source manifest")
    if mapping_record["domainSetupId"] != manifest["domainSetupId"]:
        raise SourceAdapterOutputError("field mapping must bind the source manifest setup")
    if output["domainBinding"]["domain"] != manifest["domain"]:
        raise SourceAdapterOutputError("domain binding must match source manifest")
    if any(item["requiresConfirmation"] for item in mapping_record["mappings"]):
        if output["nextAction"] != "ask_mapping_confirmation":
            raise SourceAdapterOutputError("proposed mappings must route to confirmation")
    else:
        if output["nextAction"] != "run_source_intake":
            raise SourceAdapterOutputError("confirmed mappings should route to source intake")


def write_output(output: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(output), encoding="utf-8")
    print("generated source adapter output")


def check_output(output: dict[str, Any]) -> None:
    expected = render_json(output)
    if not OUTPUT_PATH.exists():
        print(f"missing source adapter output: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_source_adapter_output.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"source adapter output drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_source_adapter_output.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source adapter output")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated source adapter output drift")
    parser.add_argument("--write", action="store_true", help="write generated source adapter output")
    args = parser.parse_args()
    try:
        output = build_output()
    except (OSError, json.JSONDecodeError, csv.Error, SourceAdapterOutputError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_output(output)
    elif args.check:
        check_output(output)
    else:
        sys.stdout.write(render_json(output))


if __name__ == "__main__":
    main()
