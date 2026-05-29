#!/usr/bin/env python3
"""Generate or check bounded source intake fixtures and reports."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from generate_domain_setups import WEATHER_DOMAIN, build_setups
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "spec" / "fixtures" / "source-intake"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-intake"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"
REPORT_SCHEMA = SPEC / "source-intake-report.schema.json"
GENERATED_AT = "2026-06-06T16:20:00Z"
CREATED_AT = "2026-06-02T10:00:00Z"

CASE_ORDER = ["accepted", "accepted_partial", "needs_confirmation", "rejected"]
CASE_REPORT_IDS = {
    "accepted": "sourceintakereport-001",
    "accepted_partial": "sourceintakereport-002",
    "needs_confirmation": "sourceintakereport-003",
    "rejected": "sourceintakereport-004",
}


class SourceIntakeError(Exception):
    pass


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def source_manifest_path(case: str) -> Path:
    return FIXTURES / f"weather-logistics-{case_slug(case)}-source-manifest.json"


def field_mapping_path(case: str) -> Path:
    return FIXTURES / f"weather-logistics-{case_slug(case)}-field-mapping.json"


def report_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-source-intake-report.generated.json"


def normalize(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower().replace(" ", "-").replace("_", "-")


def parse_ts(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def source_entry(
    source_id: str,
    source_role: str,
    display_name: str,
    connector_type: str,
    source_class: str,
    source_ref: str | None,
    content_hash: str,
    row_count: int,
    positive_outcome_count: int | None,
    retrieved_at: str | None,
    available_before_close: bool,
    max_source_age_hours: int,
    geographies: list[str],
    service_start: str | None,
    service_end: str | None,
    fields: list[tuple[str, str, int, int]],
    privacy_class: str = "internal",
    contains_secrets: bool = False,
    contains_personal_data: bool = False,
    approval_required: bool = False,
    feature_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "sourceId": source_id,
        "sourceRole": source_role,
        "displayName": display_name,
        "connectorType": connector_type,
        "sourceClass": source_class,
        "sourceRef": source_ref,
        "contentHash": content_hash,
        "rowCount": row_count,
        "positiveOutcomeCount": positive_outcome_count,
        "retrieval": {
            "retrievedAt": retrieved_at,
            "availableBeforeForecastClose": available_before_close,
            "maxSourceAgeHours": max_source_age_hours,
        },
        "coverage": {
            "geographies": geographies,
            "serviceDateStart": service_start,
            "serviceDateEnd": service_end,
            "entityIdentifiers": [],
        },
        "privacy": {
            "privacyClass": privacy_class,
            "containsSecrets": contains_secrets,
            "containsPersonalData": contains_personal_data,
            "approvalRequired": approval_required,
            "rawRetention": "metadata_only",
        },
        "fieldInventory": [
            {
                "fieldName": name,
                "observedType": observed_type,
                "sampleCount": sample_count,
                "nonNullCount": non_null_count,
                "exampleValuesStored": False,
            }
            for name, observed_type, sample_count, non_null_count in fields
        ],
    }
    if feature_summary is not None:
        entry["featureSummary"] = feature_summary
    return entry


def feature_summary(
    numeric_values: list[tuple[str, float, str]] | None = None,
    categorical_values: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "numericValues": [
            {
                "fieldName": field_name,
                "value": value,
                "unit": unit,
            }
            for field_name, value, unit in numeric_values or []
        ],
        "categoricalValues": [
            {
                "fieldName": field_name,
                "value": value,
            }
            for field_name, value in categorical_values or []
        ],
    }


def mapping(
    mapping_id: str,
    source_id: str,
    source_role: str,
    source_field: str,
    target_field: str,
    target_type: str,
    origin: str = "user_provided",
    status: str = "confirmed",
    confidence: float = 1.0,
    requires_confirmation: bool = False,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "mappingId": mapping_id,
        "sourceId": source_id,
        "sourceRole": source_role,
        "sourceField": source_field,
        "targetField": target_field,
        "targetFieldType": target_type,
        "mappingOrigin": origin,
        "mappingStatus": status,
        "confidence": confidence,
        "requiresConfirmation": requires_confirmation,
        "validationNotes": notes or ["Mapping supplied for deterministic fixture intake."],
    }


def alias_mapping(
    alias_mapping_id: str,
    source_value: str,
    canonical_value: str,
    origin: str = "user_provided",
    status: str = "confirmed",
    requires_confirmation: bool = False,
) -> dict[str, Any]:
    return {
        "aliasMappingId": alias_mapping_id,
        "entityType": "geography",
        "sourceValue": source_value,
        "canonicalValue": canonical_value,
        "mappingOrigin": origin,
        "mappingStatus": status,
        "requiresConfirmation": requires_confirmation,
    }


def manifest_base(case_number: int, sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sourceManifestId": f"sourcemanifest-{case_number:03d}",
        "createdAt": CREATED_AT,
        "domainSetupId": "domainsetup-001",
        "domain": WEATHER_DOMAIN,
        "forecastParameters": {
            "questionTemplateId": "template-001",
            "horizonLabel": "1-day",
            "forecastCloseTime": "2026-06-02T12:00:00Z",
            "geography": "Warsaw",
            "serviceDate": "2026-06-03",
            "assetIdentifier": None,
            "location": None,
            "targetWindow": None,
        },
        "sources": sources,
    }


def field_mapping_base(case_number: int, source_manifest_id: str, mappings: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "fieldMappingId": f"fieldmapping-{case_number:03d}",
        "createdAt": CREATED_AT,
        "domainSetupId": "domainsetup-001",
        "domain": WEATHER_DOMAIN,
        "sourceManifestId": source_manifest_id,
        "mappings": mappings,
        "aliasMappings": aliases,
    }


def accepted_case() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = manifest_base(
        1,
        [
            source_entry(
                "manifestsource-001",
                "weather_forecast",
                "Open-Meteo Warsaw Forecast",
                "public_api",
                "public_dataset",
                "https://api.open-meteo.example/fixture/warsaw",
                "hash-weather-accepted-001",
                1,
                None,
                "2026-06-02T09:30:00Z",
                True,
                24,
                ["warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("geography", "string", 1, 1),
                    ("service_date", "date", 1, 1),
                    ("retrieved_at", "date_time", 1, 1),
                    ("forecast_daily_precipitation_mm", "number", 1, 1),
                    ("source_status", "categorical", 1, 1),
                ],
                privacy_class="public",
                feature_summary=feature_summary(
                    numeric_values=[("forecast_daily_precipitation_mm", 24.0, "mm")],
                    categorical_values=[("source_status", "current")],
                ),
            ),
            source_entry(
                "manifestsource-002",
                "historical_baseline",
                "Historical Delivery Disruption Rows",
                "local_file",
                "internal_dataset",
                "local://fixtures/weather-logistics/history.csv",
                "hash-history-accepted-001",
                90,
                12,
                "2026-06-01T18:00:00Z",
                True,
                8760,
                ["warsaw"],
                "2026-01-01",
                "2026-06-01",
                [
                    ("service_date", "date", 90, 90),
                    ("geography", "string", 90, 90),
                    ("disruption_observed", "boolean", 90, 90),
                    ("precipitation_mm", "number", 90, 90),
                ],
            ),
            source_entry(
                "manifestsource-003",
                "declared_operations_outcome",
                "Declared Post-Window Operations Outcome",
                "manual_upload",
                "internal_dataset",
                "local://fixtures/weather-logistics/outcome.csv",
                "hash-outcome-accepted-001",
                1,
                1,
                None,
                False,
                8760,
                ["warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("service_date", "date", 1, 1),
                    ("geography", "string", 1, 1),
                    ("disruption_observed", "boolean", 1, 1),
                    ("resolution_notes", "string", 1, 1),
                ],
            ),
        ],
    )
    mappings = [
        mapping("mapping-001", "manifestsource-001", "weather_forecast", "geography", "geography", "string"),
        mapping("mapping-002", "manifestsource-001", "weather_forecast", "service_date", "service_date", "date"),
        mapping("mapping-003", "manifestsource-001", "weather_forecast", "retrieved_at", "retrieved_at", "date_time"),
        mapping(
            "mapping-004",
            "manifestsource-001",
            "weather_forecast",
            "forecast_daily_precipitation_mm",
            "forecast_daily_precipitation_mm",
            "number",
        ),
        mapping("mapping-005", "manifestsource-002", "historical_baseline", "service_date", "service_date", "date"),
        mapping("mapping-006", "manifestsource-002", "historical_baseline", "geography", "geography", "string"),
        mapping(
            "mapping-007",
            "manifestsource-002",
            "historical_baseline",
            "disruption_observed",
            "disruption_observed",
            "boolean",
        ),
        mapping(
            "mapping-008",
            "manifestsource-003",
            "declared_operations_outcome",
            "service_date",
            "service_date",
            "date",
        ),
        mapping(
            "mapping-009",
            "manifestsource-003",
            "declared_operations_outcome",
            "geography",
            "geography",
            "string",
        ),
        mapping(
            "mapping-010",
            "manifestsource-003",
            "declared_operations_outcome",
            "disruption_observed",
            "disruption_observed",
            "boolean",
        ),
    ]
    field_mapping = field_mapping_base(1, manifest["sourceManifestId"], mappings, [alias_mapping("aliasmapping-001", "Warsaw", "warsaw")])
    return manifest, field_mapping


def accepted_partial_case() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = manifest_base(
        2,
        [
            source_entry(
                "manifestsource-004",
                "historical_baseline",
                "Historical Delivery Baseline Only",
                "local_file",
                "internal_dataset",
                "local://fixtures/weather-logistics/history-baseline-only.csv",
                "hash-history-partial-001",
                80,
                10,
                "2026-06-01T18:00:00Z",
                True,
                8760,
                ["warsaw"],
                "2026-01-01",
                "2026-06-01",
                [
                    ("service_date", "date", 80, 80),
                    ("geography", "string", 80, 80),
                    ("disruption_observed", "boolean", 80, 80),
                ],
            ),
            source_entry(
                "manifestsource-005",
                "declared_operations_outcome",
                "Declared Outcome Placeholder",
                "manual_upload",
                "internal_dataset",
                "local://fixtures/weather-logistics/outcome-placeholder.csv",
                "hash-outcome-partial-001",
                1,
                1,
                None,
                False,
                8760,
                ["warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("service_date", "date", 1, 1),
                    ("geography", "string", 1, 1),
                    ("disruption_observed", "boolean", 1, 1),
                ],
            ),
        ],
    )
    mappings = [
        mapping("mapping-011", "manifestsource-004", "historical_baseline", "service_date", "service_date", "date"),
        mapping("mapping-012", "manifestsource-004", "historical_baseline", "geography", "geography", "string"),
        mapping(
            "mapping-013",
            "manifestsource-004",
            "historical_baseline",
            "disruption_observed",
            "disruption_observed",
            "boolean",
        ),
        mapping(
            "mapping-014",
            "manifestsource-005",
            "declared_operations_outcome",
            "service_date",
            "service_date",
            "date",
        ),
        mapping(
            "mapping-015",
            "manifestsource-005",
            "declared_operations_outcome",
            "geography",
            "geography",
            "string",
        ),
        mapping(
            "mapping-016",
            "manifestsource-005",
            "declared_operations_outcome",
            "disruption_observed",
            "disruption_observed",
            "boolean",
        ),
    ]
    field_mapping = field_mapping_base(2, manifest["sourceManifestId"], mappings, [alias_mapping("aliasmapping-002", "Warsaw", "warsaw")])
    return manifest, field_mapping


def needs_confirmation_case() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = manifest_base(
        3,
        [
            source_entry(
                "manifestsource-006",
                "weather_forecast",
                "Agent Extracted Weather Table",
                "agent_extraction",
                "public_dataset",
                "local://agent-extraction/weather-table.json",
                "hash-weather-confirm-001",
                1,
                None,
                "2026-06-02T09:30:00Z",
                True,
                24,
                ["Warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("city", "string", 1, 1),
                    ("date", "date", 1, 1),
                    ("loaded_at", "date_time", 1, 1),
                    ("rain_mm", "number", 1, 1),
                ],
                privacy_class="public",
            ),
            source_entry(
                "manifestsource-007",
                "historical_baseline",
                "Agent Extracted Historical Rows",
                "agent_extraction",
                "internal_dataset",
                "local://agent-extraction/history-table.json",
                "hash-history-confirm-001",
                60,
                7,
                "2026-06-01T18:00:00Z",
                True,
                8760,
                ["Warsaw"],
                "2026-01-01",
                "2026-06-01",
                [
                    ("date", "date", 60, 60),
                    ("city", "string", 60, 60),
                    ("disrupted", "boolean", 60, 60),
                ],
            ),
            source_entry(
                "manifestsource-008",
                "declared_operations_outcome",
                "Agent Proposed Outcome Table",
                "agent_extraction",
                "internal_dataset",
                "local://agent-extraction/outcome-table.json",
                "hash-outcome-confirm-001",
                1,
                1,
                None,
                False,
                8760,
                ["Warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("date", "date", 1, 1),
                    ("city", "string", 1, 1),
                    ("disrupted", "boolean", 1, 1),
                ],
            ),
        ],
    )
    proposed = {
        "origin": "agent_inferred",
        "status": "proposed",
        "confidence": 0.76,
        "requires_confirmation": True,
        "notes": ["Agent-inferred mapping must be confirmed before forecast execution."],
    }
    mappings = [
        mapping("mapping-017", "manifestsource-006", "weather_forecast", "city", "geography", "string", **proposed),
        mapping("mapping-018", "manifestsource-006", "weather_forecast", "date", "service_date", "date", **proposed),
        mapping("mapping-019", "manifestsource-006", "weather_forecast", "loaded_at", "retrieved_at", "date_time", **proposed),
        mapping(
            "mapping-020",
            "manifestsource-006",
            "weather_forecast",
            "rain_mm",
            "forecast_daily_precipitation_mm",
            "number",
            **proposed,
        ),
        mapping("mapping-021", "manifestsource-007", "historical_baseline", "date", "service_date", "date", **proposed),
        mapping("mapping-022", "manifestsource-007", "historical_baseline", "city", "geography", "string", **proposed),
        mapping(
            "mapping-023",
            "manifestsource-007",
            "historical_baseline",
            "disrupted",
            "disruption_observed",
            "boolean",
            **proposed,
        ),
        mapping(
            "mapping-024",
            "manifestsource-008",
            "declared_operations_outcome",
            "date",
            "service_date",
            "date",
            **proposed,
        ),
        mapping(
            "mapping-025",
            "manifestsource-008",
            "declared_operations_outcome",
            "city",
            "geography",
            "string",
            **proposed,
        ),
        mapping(
            "mapping-026",
            "manifestsource-008",
            "declared_operations_outcome",
            "disrupted",
            "disruption_observed",
            "boolean",
            **proposed,
        ),
    ]
    aliases = [alias_mapping("aliasmapping-003", "Warsaw", "warsaw", "agent_inferred", "proposed", True)]
    field_mapping = field_mapping_base(3, manifest["sourceManifestId"], mappings, aliases)
    return manifest, field_mapping


def rejected_case() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = manifest_base(
        4,
        [
            source_entry(
                "manifestsource-009",
                "weather_forecast",
                "Leaked Post-Outcome Operations Export",
                "manual_upload",
                "internal_dataset",
                "local://private/leaked-post-outcome-export.csv",
                "hash-rejected-weather-001",
                1,
                1,
                "2026-06-04T08:00:00Z",
                False,
                24,
                ["warsaw"],
                "2026-06-03",
                "2026-06-03",
                [
                    ("service_date", "date", 1, 1),
                    ("geography", "string", 1, 1),
                    ("disruption_observed", "boolean", 1, 1),
                ],
                privacy_class="sensitive",
                contains_secrets=True,
                approval_required=True,
            ),
            source_entry(
                "manifestsource-010",
                "historical_baseline",
                "Tiny Historical Sample",
                "local_file",
                "internal_dataset",
                "local://fixtures/weather-logistics/tiny-history.csv",
                "hash-rejected-history-001",
                5,
                0,
                "2026-06-01T18:00:00Z",
                True,
                8760,
                ["warsaw"],
                "2026-05-01",
                "2026-06-01",
                [
                    ("service_date", "date", 5, 5),
                    ("geography", "string", 5, 5),
                    ("disruption_observed", "boolean", 5, 5),
                ],
            ),
        ],
    )
    mappings = [
        mapping(
            "mapping-027",
            "manifestsource-009",
            "weather_forecast",
            "disruption_observed",
            "forecast_daily_precipitation_mm",
            "number",
            origin="user_provided",
            status="rejected",
            confidence=0.1,
            notes=["Post-outcome field cannot be mapped to forecast-time weather evidence."],
        ),
        mapping("mapping-028", "manifestsource-010", "historical_baseline", "service_date", "service_date", "date"),
        mapping("mapping-029", "manifestsource-010", "historical_baseline", "geography", "geography", "string"),
        mapping(
            "mapping-030",
            "manifestsource-010",
            "historical_baseline",
            "disruption_observed",
            "disruption_observed",
            "boolean",
        ),
    ]
    field_mapping = field_mapping_base(4, manifest["sourceManifestId"], mappings, [alias_mapping("aliasmapping-004", "Warsaw", "warsaw")])
    return manifest, field_mapping


def build_fixture_cases() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    cases = {
        "accepted": accepted_case(),
        "accepted_partial": accepted_partial_case(),
        "needs_confirmation": needs_confirmation_case(),
        "rejected": rejected_case(),
    }
    for case, (manifest, field_mapping) in cases.items():
        validate_manifest_and_mapping(case, manifest, field_mapping)
    return cases


def validate_manifest_and_mapping(case: str, manifest: dict[str, Any], field_mapping: dict[str, Any]) -> None:
    manifest_errors = validate_record(manifest, SOURCE_MANIFEST_SCHEMA)
    if manifest_errors:
        raise SourceIntakeError(f"{case} source manifest schema validation failed: {manifest_errors[0]}")
    mapping_errors = validate_record(field_mapping, FIELD_MAPPING_SCHEMA)
    if mapping_errors:
        raise SourceIntakeError(f"{case} field mapping schema validation failed: {mapping_errors[0]}")
    if manifest["sourceManifestId"] != field_mapping["sourceManifestId"]:
        raise SourceIntakeError(f"{case} source manifest and field mapping are not bound")


def check_result(status: str, reason_codes: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "reasonCodes": reason_codes or []}


def source_role_map(setup: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {role["roleKey"]: role for role in setup["sourceRoles"]}


def mapping_decisions(field_mapping: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    for item in field_mapping["mappings"]:
        reason_codes: list[str] = []
        if item["mappingStatus"] == "rejected":
            decision = "rejected"
            reason_codes.append("mapping_rejected")
        elif item["requiresConfirmation"] or item["mappingStatus"] == "proposed" or item["mappingOrigin"] == "agent_inferred":
            decision = "proposed"
            reason_codes.append("mapping_requires_confirmation")
            if item["mappingOrigin"] == "agent_inferred":
                reason_codes.append("agent_inferred_mapping")
        else:
            decision = "accepted"
            reason_codes.append("mapping_confirmed")
        decisions.append(
            {
                "mappingId": item["mappingId"],
                "sourceId": item["sourceId"],
                "targetField": item["targetField"],
                "decision": decision,
                "mappingOrigin": item["mappingOrigin"],
                "requiresConfirmation": item["requiresConfirmation"],
                "reasonCodes": reason_codes,
            }
        )
    return decisions


def compatible_type(source_type: str, target_type: str) -> bool:
    if source_type == target_type:
        return True
    compatible = {
        ("string", "categorical"),
        ("categorical", "string"),
        ("id", "string"),
        ("string", "id"),
        ("integer", "number"),
    }
    return (source_type, target_type) in compatible


def date_covers(source: dict[str, Any], service_date: str | None) -> bool:
    if service_date is None:
        return True
    start = source["coverage"]["serviceDateStart"]
    end = source["coverage"]["serviceDateEnd"]
    if start is None or end is None:
        return True
    return start <= service_date <= end


def evaluate_source(
    source: dict[str, Any],
    role: dict[str, Any] | None,
    manifest: dict[str, Any],
    mappings: list[dict[str, Any]],
    mapping_decision_by_id: dict[str, dict[str, Any]],
    setup: dict[str, Any],
) -> dict[str, Any]:
    reason_codes: list[str] = []
    field_inventory = {field["fieldName"]: field for field in source["fieldInventory"]}
    mapping_by_target = {
        item["targetField"]: item
        for item in mappings
        if item["sourceId"] == source["sourceId"]
    }

    if role is None:
        checks = {
            name: check_result("failed", ["unknown_source_role"])
            for name in [
                "requiredFields",
                "typeParsing",
                "entityMatch",
                "timestampAvailability",
                "sourceFreshness",
                "leakageRisk",
                "sampleSize",
                "privacy",
            ]
        }
        return {
            "sourceId": source["sourceId"],
            "sourceRole": source["sourceRole"],
            "decision": "rejected",
            "reasonCodes": ["unknown_source_role"],
            "checks": checks,
        }

    missing_fields: list[str] = []
    proposed_fields: list[str] = []
    rejected_fields: list[str] = []
    type_mismatches: list[str] = []
    for required in role["requiredFields"]:
        target = required["fieldName"]
        item = mapping_by_target.get(target)
        if item is None:
            missing_fields.append(target)
            continue
        decision = mapping_decision_by_id[item["mappingId"]]
        if decision["decision"] == "rejected":
            rejected_fields.append(target)
        elif decision["decision"] == "proposed":
            proposed_fields.append(target)
        source_field = field_inventory.get(item["sourceField"])
        if source_field is None:
            missing_fields.append(target)
            continue
        if not compatible_type(source_field["observedType"], item["targetFieldType"]):
            type_mismatches.append(target)

    required_reason_codes: list[str] = []
    if missing_fields:
        required_reason_codes.append("missing_required_fields")
    if rejected_fields:
        required_reason_codes.append("rejected_required_mappings")
    if proposed_fields:
        required_reason_codes.append("proposed_required_mappings")
    if missing_fields or rejected_fields:
        required_fields = check_result("failed", required_reason_codes)
    elif proposed_fields:
        required_fields = check_result("needs_confirmation", required_reason_codes)
    else:
        required_fields = check_result("passed", ["all_required_fields_mapped"])

    if type_mismatches:
        type_parsing = check_result("failed", ["type_mismatch"])
    elif proposed_fields:
        type_parsing = check_result("needs_confirmation", ["type_parse_after_mapping_confirmation"])
    else:
        type_parsing = check_result("passed", ["types_compatible"])

    params = manifest["forecastParameters"]
    geography = normalize(params.get("geography"))
    source_geographies = {normalize(item) for item in source["coverage"]["geographies"]}
    if geography and source_geographies and geography not in source_geographies:
        entity_match = check_result("failed", ["geography_mismatch"])
    elif source["sourceRole"] != "historical_baseline" and not date_covers(source, params.get("serviceDate")):
        entity_match = check_result("failed", ["service_date_not_covered"])
    elif proposed_fields or any(alias["requiresConfirmation"] for alias in manifest.get("aliasMappings", [])):
        entity_match = check_result("needs_confirmation", ["alias_or_mapping_requires_confirmation"])
    else:
        entity_match = check_result("passed", ["entity_scope_matches"])

    close_time = parse_ts(params["forecastCloseTime"])
    retrieved_at = parse_ts(source["retrieval"]["retrievedAt"])
    if role["forecastTimeAllowed"]:
        if retrieved_at is None:
            timestamp_availability = check_result("failed", ["missing_retrieved_at"])
        elif not source["retrieval"]["availableBeforeForecastClose"]:
            timestamp_availability = check_result("failed", ["not_available_before_forecast_close"])
        elif close_time and retrieved_at > close_time:
            timestamp_availability = check_result("failed", ["retrieved_after_forecast_close"])
        else:
            timestamp_availability = check_result("passed", ["available_before_forecast_close"])
    else:
        timestamp_availability = check_result("not_applicable", ["resolution_role_not_forecast_time"])

    if role["forecastTimeAllowed"] and retrieved_at is not None and close_time is not None:
        source_age_hours = (close_time - retrieved_at).total_seconds() / 3600
        if source_age_hours < 0:
            source_freshness = check_result("failed", ["source_retrieved_after_forecast_close"])
        elif source_age_hours > source["retrieval"]["maxSourceAgeHours"]:
            source_freshness = check_result("failed", ["source_stale"])
        else:
            source_freshness = check_result("passed", ["source_fresh_enough"])
    elif role["forecastTimeAllowed"]:
        source_freshness = check_result("failed", ["freshness_unverifiable"])
    else:
        source_freshness = check_result("not_applicable", ["resolution_role_not_forecast_time"])

    if role["forecastTimeAllowed"] and timestamp_availability["status"] == "failed":
        leakage_risk = check_result("failed", ["post_close_or_unavailable_forecast_source"])
    elif not role["forecastTimeAllowed"]:
        leakage_risk = check_result("not_applicable", ["source_role_resolution_only"])
    else:
        leakage_risk = check_result("passed", ["no_post_outcome_evidence_detected"])

    if source["sourceRole"] == "historical_baseline":
        baseline = setup["baselinePolicy"]
        sample_reasons = []
        if source["rowCount"] < baseline["minimumComparableRows"]:
            sample_reasons.append("insufficient_comparable_rows")
        positive_count = source["positiveOutcomeCount"] or 0
        if positive_count < baseline["minimumPositiveOutcomes"]:
            sample_reasons.append("insufficient_positive_outcomes")
        if sample_reasons:
            sample_size = check_result("failed", sample_reasons)
        else:
            sample_size = check_result("passed", ["baseline_sample_sufficient"])
    else:
        sample_size = check_result("not_applicable", ["not_baseline_source"])

    privacy_info = source["privacy"]
    if privacy_info["containsSecrets"]:
        privacy = check_result("failed", ["source_contains_secrets"])
    elif privacy_info["approvalRequired"] or privacy_info["containsPersonalData"] or privacy_info["privacyClass"] in {"personal", "sensitive"}:
        privacy = check_result("needs_confirmation", ["privacy_or_approval_review_required"])
    else:
        privacy = check_result("passed", ["privacy_boundary_ok"])

    checks = {
        "requiredFields": required_fields,
        "typeParsing": type_parsing,
        "entityMatch": entity_match,
        "timestampAvailability": timestamp_availability,
        "sourceFreshness": source_freshness,
        "leakageRisk": leakage_risk,
        "sampleSize": sample_size,
        "privacy": privacy,
    }
    for result in checks.values():
        reason_codes.extend(result["reasonCodes"])
    statuses = {result["status"] for result in checks.values()}
    if "failed" in statuses:
        decision = "rejected"
    elif "needs_confirmation" in statuses:
        decision = "needs_confirmation"
    elif "warning" in statuses:
        decision = "usable_partial"
    else:
        decision = "usable"
    return {
        "sourceId": source["sourceId"],
        "sourceRole": source["sourceRole"],
        "decision": decision,
        "reasonCodes": sorted(set(reason_codes)),
        "checks": checks,
    }


def build_role_coverage(setup: dict[str, Any], source_decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions_by_role: dict[str, list[dict[str, Any]]] = {}
    for decision in source_decisions:
        decisions_by_role.setdefault(decision["sourceRole"], []).append(decision)
    coverage = []
    for role in setup["sourceRoles"]:
        role_decisions = decisions_by_role.get(role["roleKey"], [])
        usable = [item for item in role_decisions if item["decision"] in {"usable", "usable_partial"}]
        rejected = [item for item in role_decisions if item["decision"] == "rejected"]
        needs = [item for item in role_decisions if item["decision"] == "needs_confirmation"]
        if usable:
            status = "present"
        elif needs:
            status = "partial"
        elif rejected:
            status = "rejected"
        else:
            status = "missing"
        coverage.append(
            {
                "sourceRole": role["roleKey"],
                "requiredForForecast": role["timing"] in {"forecast_time", "baseline"},
                "status": status,
                "sourceIds": [item["sourceId"] for item in role_decisions],
            }
        )
    return coverage


def build_method_eligibility(
    setup: dict[str, Any],
    source_decisions: list[dict[str, Any]],
    mapping_decisions_list: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    usable_roles = {
        item["sourceRole"]
        for item in source_decisions
        if item["decision"] in {"usable", "usable_partial"}
    }
    rejected_roles = {
        item["sourceRole"]
        for item in source_decisions
        if item["decision"] == "rejected"
    }
    has_pending_mappings = any(item["decision"] == "proposed" for item in mapping_decisions_list)
    eligibility = []
    for method_class in setup["methodPolicy"]["enabledMethodClasses"]:
        reason_codes = []
        eligible = False
        if has_pending_mappings:
            reason_codes.append("mapping_confirmation_required")
        if rejected_roles:
            reason_codes.append("source_rejected")
        if method_class == "historical_baseline":
            eligible = "historical_baseline" in usable_roles and not has_pending_mappings and not rejected_roles
            if "historical_baseline" not in usable_roles:
                reason_codes.append("missing_usable_historical_baseline")
        elif method_class == "deterministic_statistical":
            required = {"historical_baseline", "weather_forecast"}
            eligible = required.issubset(usable_roles) and not has_pending_mappings and not rejected_roles
            missing = required - usable_roles
            if missing:
                reason_codes.extend(f"missing_usable_{role}" for role in sorted(missing))
        else:
            reason_codes.append("method_not_enabled_for_fixture_intake")
        if eligible:
            reason_codes.append("method_eligible")
        eligibility.append(
            {
                "methodClass": method_class,
                "eligible": eligible,
                "reasonCodes": sorted(set(reason_codes)),
            }
        )
    return eligibility


def report_actions_and_warnings(
    intake_status: str,
    role_coverage: list[dict[str, Any]],
    source_decisions: list[dict[str, Any]],
    mapping_decisions_list: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    actions: list[str] = []
    warnings = ["Source intake reports do not produce forecast artifacts."]
    for role in role_coverage:
        if role["status"] == "missing" and role["requiredForForecast"]:
            actions.append(f"Connect a usable source for required role {role['sourceRole']}.")
        elif role["status"] == "missing":
            actions.append(f"Declare how role {role['sourceRole']} will be resolved later.")
    if any(item["decision"] == "proposed" for item in mapping_decisions_list):
        actions.append("Confirm proposed field and alias mappings before forecast execution.")
    for source in source_decisions:
        if source["decision"] == "rejected":
            actions.append(f"Remove or replace rejected source {source['sourceId']} for role {source['sourceRole']}.")
    if intake_status == "accepted_partial":
        warnings.append("Forecast can proceed only with methods that remain eligible after missing-role checks.")
    if intake_status == "rejected":
        warnings.append("Rejected intake must not bind generated forecast outputs.")
    return actions, warnings


def evaluate_intake(case: str, manifest: dict[str, Any], field_mapping: dict[str, Any]) -> dict[str, Any]:
    setup = build_setups()[manifest["domain"]]
    roles = source_role_map(setup)
    mapping_decisions_list = mapping_decisions(field_mapping)
    mapping_decision_by_id = {item["mappingId"]: item for item in mapping_decisions_list}
    source_decisions = [
        evaluate_source(
            source,
            roles.get(source["sourceRole"]),
            manifest,
            field_mapping["mappings"],
            mapping_decision_by_id,
            setup,
        )
        for source in manifest["sources"]
    ]
    role_coverage = build_role_coverage(setup, source_decisions)
    method_eligibility = build_method_eligibility(setup, source_decisions, mapping_decisions_list)
    eligible_methods = {item["methodClass"] for item in method_eligibility if item["eligible"]}
    has_rejected_sources = any(item["decision"] == "rejected" for item in source_decisions)
    has_pending_mappings = any(item["decision"] == "proposed" for item in mapping_decisions_list)

    if has_rejected_sources:
        intake_status = "rejected"
    elif has_pending_mappings or any(item["decision"] == "needs_confirmation" for item in source_decisions):
        intake_status = "needs_confirmation"
    elif "historical_baseline" in eligible_methods and "deterministic_statistical" not in eligible_methods:
        intake_status = "accepted_partial"
    elif {"historical_baseline", "deterministic_statistical"}.issubset(eligible_methods):
        intake_status = "accepted"
    else:
        intake_status = "rejected"

    can_produce_forecast = intake_status in {"accepted", "accepted_partial"}
    required_actions, warnings = report_actions_and_warnings(
        intake_status,
        role_coverage,
        source_decisions,
        mapping_decisions_list,
    )
    report = {
        "sourceIntakeReportId": CASE_REPORT_IDS[case],
        "generatedAt": GENERATED_AT,
        "domainSetupId": manifest["domainSetupId"],
        "domain": manifest["domain"],
        "sourceManifestId": manifest["sourceManifestId"],
        "fieldMappingId": field_mapping["fieldMappingId"],
        "intakeStatus": intake_status,
        "canProduceForecast": can_produce_forecast,
        "forecastGenerationAllowed": can_produce_forecast,
        "roleCoverage": role_coverage,
        "sourceDecisions": source_decisions,
        "mappingDecisions": mapping_decisions_list,
        "methodEligibility": method_eligibility,
        "requiredActions": required_actions,
        "warnings": warnings,
    }
    errors = validate_record(report, REPORT_SCHEMA)
    if errors:
        raise SourceIntakeError(f"{case} source intake report schema validation failed: {errors[0]}")
    return report


def build_reports() -> dict[str, dict[str, Any]]:
    cases = build_fixture_cases()
    return {
        case: evaluate_intake(case, manifest, field_mapping)
        for case, (manifest, field_mapping) in cases.items()
    }


def summary(reports: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(reports),
        "reports": [
            {
                "case": case,
                "sourceIntakeReportId": report["sourceIntakeReportId"],
                "domain": report["domain"],
                "intakeStatus": report["intakeStatus"],
                "canProduceForecast": report["canProduceForecast"],
                "eligibleMethods": [
                    item["methodClass"]
                    for item in report["methodEligibility"]
                    if item["eligible"]
                ],
            }
            for case, report in reports.items()
        ],
    }


def write_outputs(cases: dict[str, tuple[dict[str, Any], dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    for case, (manifest, field_mapping) in cases.items():
        source_manifest_path(case).write_text(render_json(manifest), encoding="utf-8")
        field_mapping_path(case).write_text(render_json(field_mapping), encoding="utf-8")
        report_path(case).write_text(render_json(reports[case]), encoding="utf-8")
    print("generated source intake fixtures and reports")


def check_outputs(cases: dict[str, tuple[dict[str, Any], dict[str, Any]]], reports: dict[str, dict[str, Any]]) -> None:
    expected: dict[Path, str] = {}
    for case, (manifest, field_mapping) in cases.items():
        expected[source_manifest_path(case)] = render_json(manifest)
        expected[field_mapping_path(case)] = render_json(field_mapping)
        expected[report_path(case)] = render_json(reports[case])
    errors = []
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing source intake output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"source intake drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_source_intake.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source intake fixtures and reports")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source intake report")
    parser.add_argument("--check", action="store_true", help="check generated source intake drift")
    parser.add_argument("--write", action="store_true", help="write source intake fixtures and reports")
    args = parser.parse_args()
    try:
        cases = build_fixture_cases()
        reports = {
            case: evaluate_intake(case, manifest, field_mapping)
            for case, (manifest, field_mapping) in cases.items()
        }
    except SourceIntakeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(cases, reports)
    elif args.check:
        check_outputs(cases, reports)
    elif args.case:
        sys.stdout.write(render_json(reports[args.case]))
    else:
        sys.stdout.write(render_json(summary(reports)))


if __name__ == "__main__":
    main()
