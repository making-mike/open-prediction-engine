#!/usr/bin/env python3
"""Validate ignored local live captures and draft source sets."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fetch_open_meteo_weather import build_url
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from source_connector_catalog import (
    CONNECTOR_IDS,
    CONNECTOR_RESULT_IDS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
    connector_binding,
)
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKSPACE = ROOT / ".ope" / "live"
RESULT_SET_SCHEMA = SPEC / "source-connector-result-set.schema.json"
SOURCE_SET_SCHEMA = SPEC / "evidence-source-set.schema.json"


class LiveCaptureError(Exception):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def selected_intent_ids(plan: dict[str, Any], connector: str) -> list[str]:
    return [
        intent["intentId"]
        for intent in plan["searchIntents"]
        if intent["connector"] == connector
    ]


def freshness_status(generated_at: str, retrieved_at: str, max_age_hours: int) -> str:
    age = parse_timestamp(generated_at) - parse_timestamp(retrieved_at)
    if age.total_seconds() < 0:
        return "outside_policy"
    return "within_policy" if age.total_seconds() <= max_age_hours * 3600 else "outside_policy"


def default_capture_path(workspace: Path, location: str, service_date: str) -> Path:
    return workspace / f"open-meteo-{location}-{service_date}-source-connector-results.json"


def default_draft_path(workspace: Path, location: str, service_date: str) -> Path:
    return workspace / f"open-meteo-{location}-{service_date}-evidence-source-set.draft.json"


def result_controls(live: bool) -> dict[str, bool]:
    return {
        "networkAccess": live,
        "liveFetch": live,
        "effectfulGeneration": False,
        "credentialUsed": False,
        "promptVisibleCredentialAccepted": False,
    }


def unavailable_live_fetch(reason: str) -> list[dict[str, str]]:
    return [
        {
            "label": "Open-Meteo live fetch",
            "reason": reason,
            "agentNextAction": "Rerun the explicit live readiness check later or use committed fixture evidence.",
        }
    ]


def connector_result_from_integration(
    *,
    integration_result: dict[str, Any],
    plan: dict[str, Any],
) -> dict[str, Any]:
    source_url = build_url(integration_result["location"], integration_result["serviceDate"])
    status = integration_result["resultStatus"]
    if status == "succeeded_live_fetch":
        provenance = integration_result["provenance"]
        source_ref = provenance["sourceRef"]
        return {
            "connectorResultId": CONNECTOR_RESULT_IDS["open_meteo_weather"],
            "connectorKey": "open_meteo_weather",
            "sourceClass": source_ref["sourceType"],
            "sourceRole": "forecast_input",
            "resultStatus": "succeeded_live_fetch",
            "plannedIntentIds": selected_intent_ids(plan, "open_meteo_weather"),
            "rawSourceMetadata": {
                "mode": "live_fetch",
                "fixturePath": None,
                "sourceUri": source_ref["uri"],
                "contentHash": source_ref["contentHash"],
                "rawPreviewStored": False,
            },
            "normalizedFields": integration_result["normalizedFields"],
            "unavailableEvidence": [],
            "retrievalDiagnostics": integration_result["retrievalDiagnostics"],
            "provenance": provenance,
            "controls": integration_result["controls"],
        }
    return {
        "connectorResultId": CONNECTOR_RESULT_IDS["open_meteo_weather"],
        "connectorKey": "open_meteo_weather",
        "sourceClass": "public_dataset",
        "sourceRole": "forecast_input",
        "resultStatus": "failed_sanitized",
        "plannedIntentIds": selected_intent_ids(plan, "open_meteo_weather"),
        "rawSourceMetadata": {
            "mode": "not_fetched",
            "fixturePath": None,
            "sourceUri": source_url,
            "contentHash": None,
            "rawPreviewStored": False,
        },
        "normalizedFields": None,
        "unavailableEvidence": unavailable_live_fetch("The explicit live fetch failed with sanitized diagnostics."),
        "retrievalDiagnostics": integration_result["retrievalDiagnostics"],
        "provenance": {
            "sourceRef": None,
            "retrievedAt": None,
            "storesContentHash": False,
            "allEvidenceClaimed": False,
        },
        "controls": integration_result["controls"],
    }


def validate_live_result_set(result_set: dict[str, Any]) -> None:
    errors = validate_record(result_set, RESULT_SET_SCHEMA)
    if errors:
        raise LiveCaptureError(f"local live connector result set schema validation failed: {errors[0]}")
    if result_set["executionMode"] != "integration_live_fetch":
        raise LiveCaptureError("local live capture must use integration_live_fetch execution mode")
    if result_set["sourceConnectorResultSetId"] != SOURCE_CONNECTOR_RESULT_SET_ID:
        raise LiveCaptureError("local live capture must preserve the checked connector result-set binding")
    controls = result_set["controls"]
    if controls["networkAccess"] is not True or controls["liveFetch"] is not True:
        raise LiveCaptureError("local live capture must explicitly record live network access")
    if controls["credentialUsed"] is not False or controls["promptVisibleCredentialAccepted"] is not False:
        raise LiveCaptureError("local live capture must not use prompt-visible credentials")
    for result in result_set["connectorResults"]:
        if result["connectorKey"] != "open_meteo_weather":
            raise LiveCaptureError("local live capture currently supports only open_meteo_weather")
        if result["connectorResultId"] != CONNECTOR_RESULT_IDS["open_meteo_weather"]:
            raise LiveCaptureError("local live capture connector result binding mismatch")
        if result["controls"]["effectfulGeneration"] is not False:
            raise LiveCaptureError("local live capture must not generate forecasts")
        if result["controls"]["credentialUsed"] is not False:
            raise LiveCaptureError("local live capture must not use credentials")
        if result["retrievalDiagnostics"]["rawDiagnosticStored"] is not False:
            raise LiveCaptureError("local live capture must not store raw diagnostics")
        if result["retrievalDiagnostics"]["rawStackTraceExposed"] is not False:
            raise LiveCaptureError("local live capture must not expose raw stack traces")
        if result["provenance"]["allEvidenceClaimed"] is not False:
            raise LiveCaptureError("local live capture must not claim all evidence coverage")
        if result["rawSourceMetadata"]["rawPreviewStored"] is not False:
            raise LiveCaptureError("local live capture must not store raw source previews")


def build_live_result_set(
    *,
    readiness: dict[str, Any],
    integration_result: dict[str, Any],
    request_path: Path = DEFAULT_REQUEST,
    generated_at: str | None = None,
) -> dict[str, Any]:
    if readiness["readinessStatus"] != "ready_for_explicit_integration_check":
        raise LiveCaptureError("readiness record is not ready for explicit integration check")
    if readiness["claimBoundary"]["integrationLiveFetchPartOfRelease"] is not False:
        raise LiveCaptureError("live capture must stay outside release checks")
    if readiness["retentionBoundary"]["rawPreviewStored"] is not False:
        raise LiveCaptureError("live capture requires metadata-only retention")
    plan = build_plan(request_path)
    connector_result = connector_result_from_integration(integration_result=integration_result, plan=plan)
    result_set = {
        "sourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "generatedAt": generated_at or utc_now(),
        "requestId": plan["requestId"],
        "evidencePlanId": plan["evidencePlanId"],
        "sourcePolicyId": plan["sourcePolicy"]["sourcePolicyId"],
        "domain": plan["domain"],
        "executionMode": "integration_live_fetch",
        "connectorResults": [connector_result],
        "controls": result_controls(live=True),
        "warnings": [
            "Ignored local live capture only; do not commit .ope/live outputs.",
            "This connector result is not public forecast evidence until a future command promotes it explicitly.",
            "This connector result does not support live calibration, track-record, or all-evidence claims.",
        ],
    }
    validate_live_result_set(result_set)
    return result_set


def save_live_result_set(
    *,
    result_set: dict[str, Any],
    workspace: Path,
    location: str,
    service_date: str,
) -> Path:
    validate_live_result_set(result_set)
    path = default_capture_path(workspace, location, service_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(result_set), encoding="utf-8")
    return path


def successful_open_meteo_result(result_set: dict[str, Any]) -> dict[str, Any]:
    validate_live_result_set(result_set)
    matches = [
        result
        for result in result_set["connectorResults"]
        if result["connectorKey"] == "open_meteo_weather" and result["resultStatus"] == "succeeded_live_fetch"
    ]
    if len(matches) != 1:
        raise LiveCaptureError("draft source-set conversion requires exactly one successful Open-Meteo live result")
    return matches[0]


def build_draft_source_set(
    *,
    result_set: dict[str, Any],
    request_path: Path = DEFAULT_REQUEST,
) -> dict[str, Any]:
    plan = build_plan(request_path)
    result = successful_open_meteo_result(result_set)
    source_ref = result["provenance"]["sourceRef"]
    if source_ref is None:
        raise LiveCaptureError("successful live result must include sourceRef")
    max_age_hours = int(plan["sourcePolicy"]["freshness"]["maxSourceAgeHours"])
    source_set = {
        "evidenceSourceSetId": "evidencesourceset-901",
        "requestId": plan["requestId"],
        "evidencePlanId": plan["evidencePlanId"],
        "generatedAt": result_set["generatedAt"],
        "executionMode": "live_fetch",
        "dataMode": plan["dataMode"],
        "sourcePolicyId": plan["sourcePolicy"]["sourcePolicyId"],
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "sourceConnectorResultSetId": result_set["sourceConnectorResultSetId"],
        "domain": plan["domain"],
        "geography": plan["geography"],
        "serviceDate": plan["serviceDate"],
        "records": [
            {
                "recordId": "sourcerecord-901",
                "sourceRole": "forecast_input",
                "connector": "open_meteo_weather",
                "connectorBinding": connector_binding("open_meteo_weather"),
                "plannedIntentIds": result["plannedIntentIds"],
                "sourceRef": source_ref,
                "rawSourceMetadata": {
                    "mode": "live_fetch",
                    "fixturePath": None,
                    "contentHash": source_ref["contentHash"],
                },
                "sourceQuality": {
                    "status": "current",
                    "coverage": "complete",
                    "freshnessStatus": freshness_status(
                        result_set["generatedAt"],
                        source_ref["retrievedAt"],
                        max_age_hours,
                    ),
                    "notes": "Ignored local live capture draft; not committed forecast evidence.",
                },
                "normalizedFields": result["normalizedFields"],
            }
        ],
        "provenanceSummary": {
            "sourceCount": 1,
            "connectorsUsed": ["open_meteo_weather"],
            "sourceClassesUsed": [source_ref["sourceType"]],
            "unavailableEvidenceCount": 0,
            "allEvidenceClaimed": False,
        },
        "controls": {
            "networkAccess": True,
            "liveFetch": True,
            "effectfulGeneration": False,
        },
        "warnings": [
            "Ignored local live draft only; do not commit .ope/live outputs.",
            "This draft is not forecast evidence until a future forecast command consumes and binds it.",
            "This draft is excluded from public read indexes, track records, calibration, and release checks.",
        ],
    }
    validate_draft_source_set(source_set)
    return source_set


def validate_draft_source_set(source_set: dict[str, Any]) -> None:
    errors = validate_record(source_set, SOURCE_SET_SCHEMA)
    if errors:
        raise LiveCaptureError(f"local live evidence source-set draft schema validation failed: {errors[0]}")
    if source_set["executionMode"] != "live_fetch":
        raise LiveCaptureError("local live draft must use live_fetch execution mode")
    if source_set["controls"]["networkAccess"] is not True or source_set["controls"]["liveFetch"] is not True:
        raise LiveCaptureError("local live draft must preserve live fetch controls")
    if source_set["controls"]["effectfulGeneration"] is not False:
        raise LiveCaptureError("local live draft must not generate forecasts")
    if source_set["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise LiveCaptureError("local live draft must not claim all evidence coverage")
    for record in source_set["records"]:
        if record["connector"] != "open_meteo_weather":
            raise LiveCaptureError("local live draft currently supports only Open-Meteo")
        if record["sourceRole"] != "forecast_input":
            raise LiveCaptureError("local live draft must contain forecast-time evidence only")
        if record["connectorBinding"]["sourceConnectorRegistryId"] != SOURCE_CONNECTOR_REGISTRY_ID:
            raise LiveCaptureError("local live draft connector registry binding mismatch")
        if record["connectorBinding"]["connectorId"] != CONNECTOR_IDS["open_meteo_weather"]:
            raise LiveCaptureError("local live draft connector ID mismatch")
        if record["sourceRef"]["sourceType"] != "public_dataset":
            raise LiveCaptureError("local live draft should preserve Open-Meteo as public_dataset")
        if record["sourceQuality"]["freshnessStatus"] != "within_policy":
            raise LiveCaptureError("local live draft source freshness violates source policy")


def validate_live_capture_file(path: Path) -> dict[str, Any]:
    result_set = load_json(path)
    validate_live_result_set(result_set)
    return result_set


def write_draft_source_set(
    *,
    source_set: dict[str, Any],
    output: Path,
) -> Path:
    validate_draft_source_set(source_set)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_json(source_set), encoding="utf-8")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="local live connector result-set JSON")
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--check", action="store_true", help="validate the saved local live connector result")
    parser.add_argument("--draft-source-set", action="store_true", help="convert the saved result to a local source-set draft")
    parser.add_argument("--write", action="store_true", help="write the draft source set instead of printing it")
    parser.add_argument("--output", type=Path, help="draft source-set output path")
    args = parser.parse_args()

    try:
        result_set = validate_live_capture_file(args.input)
        if args.draft_source_set:
            draft = build_draft_source_set(result_set=result_set, request_path=args.request)
            if args.write:
                connector_result = successful_open_meteo_result(result_set)
                source_ref = connector_result["provenance"]["sourceRef"]
                location = "warsaw"
                service_date = draft["serviceDate"]
                output = args.output or default_draft_path(DEFAULT_WORKSPACE, location, service_date)
                path = write_draft_source_set(source_set=draft, output=output)
                sys.stdout.write(render_json({"written": rel(path), "record": draft}))
            else:
                sys.stdout.write(render_json(draft))
        elif args.check:
            print("checked local live capture")
        else:
            sys.stdout.write(render_json(result_set))
    except (OSError, json.JSONDecodeError, LiveCaptureError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
