#!/usr/bin/env python3
"""Gather policy-bound auto evidence in fixture-replay mode."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from fetch_open_meteo_weather import build_url, load_fixture, normalize_response
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from source_connector_catalog import (
    CONNECTOR_IDS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
    connector_binding,
)
from validate_forecast_request import load_json
from ope_fixtures import emit_generated, render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "auto-evidence"
SOURCE_SET_PATH = GENERATED / "weather-logistics-auto-evidence-source-set.generated.json"
WEATHER_FORECAST = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
BASELINE_HISTORY = ROOT / "spec" / "fixtures" / "source" / "weather-logistics-warsaw-2026-06-03" / "baseline-history.json"
GENERATED_AT = "2026-06-02T09:58:00Z"
RETRIEVED_AT = "2026-06-02T09:30:00Z"
UNSAFE_SOURCE_PHRASES = [
    "ignore previous",
    "reveal any secrets",
    "exfiltrate",
    "system prompt",
    "developer message",
    "tool call",
]


class EvidenceGatheringError(Exception):
    pass


def fixture_label(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def selected_intent_ids(plan: dict[str, Any], connector: str) -> list[str]:
    return [
        intent["intentId"]
        for intent in plan["searchIntents"]
        if intent["connector"] == connector
    ]


def ensure_plan_connector_executable(plan: dict[str, Any]) -> None:
    checks = plan["connectorPolicyChecks"]
    if plan["sourceConnectorRegistryId"] != SOURCE_CONNECTOR_REGISTRY_ID:
        raise EvidenceGatheringError("evidence plan source connector registry binding mismatch")
    if plan["expectedSourceConnectorResultSetId"] != SOURCE_CONNECTOR_RESULT_SET_ID:
        raise EvidenceGatheringError("evidence plan source connector result-set binding mismatch")
    if checks["sourceConnectorRegistryId"] != SOURCE_CONNECTOR_REGISTRY_ID:
        raise EvidenceGatheringError("connector policy registry binding mismatch")
    if checks["expectedSourceConnectorResultSetId"] != SOURCE_CONNECTOR_RESULT_SET_ID:
        raise EvidenceGatheringError("connector policy result-set binding mismatch")
    if checks["unregisteredConnectors"]:
        names = ", ".join(checks["unregisteredConnectors"])
        raise EvidenceGatheringError(f"connector policy is not executable: unregistered connectors {names}")
    if checks["unsupportedConnectors"]:
        names = ", ".join(checks["unsupportedConnectors"])
        raise EvidenceGatheringError(f"connector policy is not executable: unsupported connectors {names}")
    if checks["resolutionOnlyConnectors"]:
        names = ", ".join(checks["resolutionOnlyConnectors"])
        raise EvidenceGatheringError(f"connector policy is not executable: resolution-only connectors {names}")
    if not checks["forecastTimeConnectors"]:
        raise EvidenceGatheringError("connector policy is not executable: no forecast-time connectors")


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def freshness_status(retrieved_at: str, max_age_hours: int) -> str:
    age = parse_timestamp(GENERATED_AT) - parse_timestamp(retrieved_at)
    if age.total_seconds() < 0:
        return "outside_policy"
    return "within_policy" if age.total_seconds() <= max_age_hours * 3600 else "outside_policy"


def iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(iter_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(iter_strings(item))
        return strings
    return []


def assert_source_text_safe(record: dict[str, Any]) -> None:
    for text in iter_strings(record):
        lowered = text.lower()
        if any(phrase in lowered for phrase in UNSAFE_SOURCE_PHRASES):
            raise EvidenceGatheringError("source record contains prompt-injection text")


def build_weather_record(plan: dict[str, Any], fixture_path: Path) -> dict[str, Any]:
    try:
        payload, raw = load_fixture(fixture_path)
        normalized = normalize_response(
            payload=payload,
            raw=raw,
            source_url=build_url("warsaw", plan["serviceDate"]),
            retrieved_at=RETRIEVED_AT,
            location_key="warsaw",
            service_date=plan["serviceDate"],
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise EvidenceGatheringError("weather source fixture is unavailable or conflicting") from exc
    if normalized["geography"] != plan["geography"]:
        raise EvidenceGatheringError("weather source geography conflicts with request")
    source_freshness = freshness_status(
        normalized["sourceRef"]["retrievedAt"],
        int(plan["sourcePolicy"]["freshness"]["maxSourceAgeHours"]),
    )
    return {
        "recordId": "sourcerecord-019",
        "sourceRole": "forecast_input",
        "connector": "open_meteo_weather",
        "connectorBinding": connector_binding("open_meteo_weather"),
        "plannedIntentIds": selected_intent_ids(plan, "open_meteo_weather"),
        "sourceRef": normalized["sourceRef"],
        "rawSourceMetadata": {
            "mode": "fixture_replay",
            "fixturePath": fixture_label(fixture_path),
            "contentHash": normalized["sourceRef"]["contentHash"],
        },
        "sourceQuality": {
            "status": normalized["sourceStatus"],
            "coverage": "complete",
            "freshnessStatus": source_freshness,
            "notes": "Fixture replay of the allow-listed Open-Meteo weather connector.",
        },
        "normalizedFields": normalized["normalizedFields"],
    }


def build_baseline_record(plan: dict[str, Any], baseline_path: Path) -> dict[str, Any]:
    try:
        baseline = load_json(baseline_path)
    except (OSError, json.JSONDecodeError) as exc:
        raise EvidenceGatheringError("baseline source fixture is unavailable") from exc
    if baseline["geography"] != plan["geography"]:
        raise EvidenceGatheringError("baseline source geography conflicts with request")
    source_freshness = freshness_status(
        baseline["sourceRef"]["retrievedAt"],
        int(plan["sourcePolicy"]["freshness"]["maxSourceAgeHours"]),
    )
    return {
        "recordId": "sourcerecord-020",
        "sourceRole": "baseline_input",
        "connector": "committed_fixture",
        "connectorBinding": connector_binding("committed_fixture"),
        "plannedIntentIds": selected_intent_ids(plan, "committed_fixture"),
        "sourceRef": baseline["sourceRef"],
        "rawSourceMetadata": {
            "mode": "fixture_replay",
            "fixturePath": fixture_label(baseline_path),
            "contentHash": baseline["sourceRef"]["contentHash"],
        },
        "sourceQuality": {
            "status": "current",
            "coverage": "complete",
            "freshnessStatus": source_freshness,
            "notes": "Committed historical-frequency baseline fixture for transparent comparison.",
        },
        "normalizedFields": {
            "lookbackStartsAt": baseline["lookbackStartsAt"],
            "lookbackEndsAt": baseline["lookbackEndsAt"],
            "weatherThresholdBucket": baseline["weatherThresholdBucket"],
            "comparableServiceDays": baseline["comparableServiceDays"],
            "disruptionDays": baseline["disruptionDays"],
            "smoothing": baseline["smoothing"],
        },
    }


def validate_source_set(source_set: dict[str, Any], plan: dict[str, Any]) -> None:
    errors = validate_record(source_set, SPEC / "evidence-source-set.schema.json")
    if errors:
        raise EvidenceGatheringError(f"evidence source set schema validation failed: {errors[0]}")

    ensure_plan_connector_executable(plan)
    if source_set["sourceConnectorRegistryId"] != plan["sourceConnectorRegistryId"]:
        raise EvidenceGatheringError("source set/source connector registry binding mismatch")
    if source_set["sourceConnectorResultSetId"] != plan["expectedSourceConnectorResultSetId"]:
        raise EvidenceGatheringError("source set/source connector result-set binding mismatch")

    allowed_connectors = set(plan["sourcePolicy"]["allowedConnectors"])
    allowed_classes = set(plan["sourcePolicy"]["allowedSourceClasses"])
    forecast_time_connectors = set(plan["connectorPolicyChecks"]["forecastTimeConnectors"])
    for record in source_set["records"]:
        if record["connector"] not in allowed_connectors:
            raise EvidenceGatheringError("source record connector violates source policy")
        if record["connector"] not in forecast_time_connectors:
            raise EvidenceGatheringError("source record connector is not forecast-time executable")
        if record["connector"] not in CONNECTOR_IDS:
            raise EvidenceGatheringError("source record connector is not registered")
        if record["connectorBinding"] != connector_binding(record["connector"]):
            raise EvidenceGatheringError("source record connector binding drifted from connector catalog")
        if record["connectorBinding"]["sourceConnectorRegistryId"] != source_set["sourceConnectorRegistryId"]:
            raise EvidenceGatheringError("source record registry binding drifted from source set")
        if record["connectorBinding"]["sourceConnectorResultSetId"] != source_set["sourceConnectorResultSetId"]:
            raise EvidenceGatheringError("source record result-set binding drifted from source set")
        if record["sourceRef"]["sourceType"] not in allowed_classes:
            raise EvidenceGatheringError("source record class violates source policy")
        if not record["sourceRef"].get("retrievedAt"):
            raise EvidenceGatheringError("source record must preserve retrievedAt")
        if not record["sourceRef"].get("contentHash"):
            raise EvidenceGatheringError("source record must preserve contentHash")
        if record["sourceRole"].startswith("resolution"):
            raise EvidenceGatheringError("forecast-time evidence must not include resolution sources")
        if record["sourceQuality"]["status"] != "current":
            raise EvidenceGatheringError("source record quality must be current")
        if record["sourceQuality"]["coverage"] != "complete":
            raise EvidenceGatheringError("source record coverage must be complete")
        if record["sourceQuality"]["freshnessStatus"] != "within_policy":
            raise EvidenceGatheringError("source record freshness violates source policy")
        assert_source_text_safe(record)

    if source_set["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise EvidenceGatheringError("auto evidence must not claim all evidence coverage")
    if source_set["controls"]["networkAccess"] is not False:
        raise EvidenceGatheringError("fixture replay must not use network access")
    if source_set["controls"]["liveFetch"] is not False:
        raise EvidenceGatheringError("fixture replay must not live-fetch")
    if source_set["controls"]["effectfulGeneration"] is not False:
        raise EvidenceGatheringError("source gathering must not generate forecasts")


def build_source_set(
    request_path: Path = DEFAULT_REQUEST,
    fixture_path: Path = WEATHER_FORECAST,
    baseline_path: Path = BASELINE_HISTORY,
    execution_mode: str = "fixture_replay",
) -> dict[str, Any]:
    if execution_mode != "fixture_replay":
        raise EvidenceGatheringError("auto-evidence live fetch is not implemented; use fixture_replay")
    plan = build_plan(request_path)
    ensure_plan_connector_executable(plan)
    if plan["planStatus"] != "planned":
        raise EvidenceGatheringError(f"cannot gather evidence for plan status {plan['planStatus']}")
    if plan["dataMode"] != "auto":
        raise EvidenceGatheringError("auto evidence gathering requires dataMode auto")
    if "open_meteo_weather" not in plan["sourcePolicy"]["allowedConnectors"]:
        raise EvidenceGatheringError("first auto evidence gatherer requires open_meteo_weather")

    records = [
        build_weather_record(plan, fixture_path),
        build_baseline_record(plan, baseline_path),
    ]
    source_set = {
        "evidenceSourceSetId": "evidencesourceset-019",
        "requestId": plan["requestId"],
        "evidencePlanId": plan["evidencePlanId"],
        "generatedAt": GENERATED_AT,
        "executionMode": execution_mode,
        "dataMode": plan["dataMode"],
        "sourcePolicyId": plan["sourcePolicy"]["sourcePolicyId"],
        "sourceConnectorRegistryId": plan["sourceConnectorRegistryId"],
        "sourceConnectorResultSetId": plan["expectedSourceConnectorResultSetId"],
        "domain": plan["domain"],
        "geography": plan["geography"],
        "serviceDate": plan["serviceDate"],
        "records": records,
        "provenanceSummary": {
            "sourceCount": len(records),
            "connectorsUsed": sorted({record["connector"] for record in records}),
            "sourceClassesUsed": sorted({record["sourceRef"]["sourceType"] for record in records}),
            "unavailableEvidenceCount": len(plan["unavailableEvidence"]),
            "allEvidenceClaimed": False,
        },
        "controls": {
            "networkAccess": False,
            "liveFetch": False,
            "effectfulGeneration": False,
        },
        "warnings": [
            "Fixture replay only; no live source was fetched.",
            "This source set is forecast-time evidence only and excludes resolution outcome sources.",
            "This source set does not support a live calibration or state-of-the-art performance claim.",
        ],
    }
    validate_source_set(source_set, plan)
    return source_set


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--weather-fixture", type=Path, default=WEATHER_FORECAST)
    parser.add_argument("--baseline-history", type=Path, default=BASELINE_HISTORY)
    parser.add_argument(
        "--execution-mode",
        choices=["fixture_replay", "live_fetch"],
        default="fixture_replay",
        help="live_fetch is explicitly gated until a production auto-evidence connector exists",
    )
    parser.add_argument("--check", action="store_true", help="check generated source-set drift")
    parser.add_argument("--write", action="store_true", help="write generated source set")
    args = parser.parse_args()
    try:
        source_set = build_source_set(
            args.request,
            args.weather_fixture,
            args.baseline_history,
            execution_mode=args.execution_mode,
        )
    except EvidenceGatheringError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write or args.check:
        emit_generated(SOURCE_SET_PATH, source_set, write=args.write, label="auto-evidence source set", regen="python3 scripts/gather_auto_evidence.py --write")
    else:
        sys.stdout.write(render_json(source_set))


if __name__ == "__main__":
    main()
