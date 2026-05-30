#!/usr/bin/env python3
"""Generate or run the policy-bound live connector readiness gate."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fetch_open_meteo_weather import OPEN_METEO_ENDPOINT, build_url, fetch_raw, normalize_response
from live_capture_workspace import build_live_result_set, rel, save_live_result_set
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from source_connector_catalog import (
    CONNECTOR_IDS,
    CONNECTOR_RESULT_IDS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
)
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "live-readiness"
READINESS_PATH = GENERATED / "weather-logistics-open-meteo-live-readiness.generated.json"
SCHEMA = SPEC / "live-connector-readiness.schema.json"
GENERATED_AT = "2026-06-06T14:25:00Z"


class LiveReadinessError(Exception):
    pass


def default_service_date() -> str:
    return (date.today() + timedelta(days=1)).isoformat()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_readiness(request_path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    plan = build_plan(request_path)
    source_policy = plan["sourcePolicy"]
    allowed_connectors = set(source_policy["allowedConnectors"])
    allowed_classes = set(source_policy["allowedSourceClasses"])
    connector_allowed = "open_meteo_weather" in allowed_connectors
    source_class_allowed = "public_dataset" in allowed_classes
    ready = (
        plan["planStatus"] == "planned"
        and connector_allowed
        and source_class_allowed
        and source_policy["allowNetworkAccess"] is True
    )
    record = {
        "liveConnectorReadinessId": "liveconnectorreadiness-001",
        "generatedAt": GENERATED_AT,
        "readinessStatus": "ready_for_explicit_integration_check" if ready else "blocked",
        "domain": plan["domain"],
        "connector": {
            "connectorId": CONNECTOR_IDS["open_meteo_weather"],
            "connectorKey": "open_meteo_weather",
            "displayName": "Open-Meteo weather forecast",
            "sourceClass": "public_dataset",
        },
        "recordBinding": {
            "requestId": plan["requestId"],
            "sourcePolicyId": source_policy["sourcePolicyId"],
            "evidencePlanId": plan["evidencePlanId"],
            "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
            "sourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
            "connectorResultId": CONNECTOR_RESULT_IDS["open_meteo_weather"],
            "fixtureEvidenceTraceId": "evidencetrace-602",
            "fixtureForecastId": "forecast-602",
            "fixtureQuestionId": "question-601",
        },
        "executionModes": {
            "fixtureReplay": {
                "mode": "fixture_replay",
                "implemented": True,
                "enabledInNormalChecks": True,
                "networkAccess": False,
                "liveFetch": False,
                "requiresExplicitFlag": False,
                "command": "python3 scripts/ope.py gather-evidence --check",
                "resultStatus": "succeeded_fixture_replay",
            },
            "integrationLiveFetch": {
                "mode": "integration_live_fetch",
                "implemented": True,
                "enabledInNormalChecks": False,
                "networkAccess": True,
                "liveFetch": True,
                "requiresExplicitFlag": True,
                "command": "python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD",
                "resultStatus": "not_run_by_default",
            },
            "hostedLiveFetch": {
                "mode": "hosted_live_fetch",
                "implemented": False,
                "enabledInNormalChecks": False,
                "networkAccess": True,
                "liveFetch": True,
                "requiresExplicitFlag": True,
                "command": "future hosted runtime connector execution",
                "resultStatus": "not_implemented",
            },
        },
        "approvalBoundary": {
            "operatorExplicitFlagRequired": True,
            "sourcePolicyApprovalRequired": False,
            "paid": False,
            "effectful": False,
            "privacySensitive": False,
            "approvalRecordRequiredBeforeForecastUse": True,
        },
        "networkBoundary": {
            "allowedEndpoint": OPEN_METEO_ENDPOINT,
            "allowBroadWebSearch": False,
            "maxNetworkCalls": 1,
            "timeoutSeconds": 20,
            "maxCostUsd": 0,
            "normalChecksNetworkAccess": False,
        },
        "freshnessBoundary": {
            "maxSourceAgeHours": source_policy["freshness"]["maxSourceAgeHours"],
            "requireRetrievedAt": True,
            "requireServiceDateBinding": True,
        },
        "retentionBoundary": {
            "rawSourceRetention": "metadata_only",
            "storeContentHash": True,
            "rawPreviewStored": False,
            "storeNormalizedFields": True,
        },
        "diagnosticsBoundary": {
            "sanitizedErrors": True,
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
            "publicFailureMessage": "Live connector check failed; inspect trusted local logs or rerun explicitly.",
        },
        "credentialBoundary": {
            "promptVisibleCredentialsAccepted": False,
            "credentialUsed": False,
            "credentialLocation": "none",
        },
        "traceBinding": {
            "fixtureTracePreserved": True,
            "integrationTraceMustBeCompatible": True,
            "requestResultBindingRequired": True,
            "forecastUseRequiresConnectorResult": True,
            "forecastUseRequiresEvidenceTrace": True,
        },
        "claimBoundary": {
            "normalReleaseChecksOffline": True,
            "integrationLiveFetchPartOfRelease": False,
            "hostedRuntimeImplemented": False,
            "allEvidenceClaimed": False,
            "liveCalibrationClaimAllowed": False,
            "forecastQualityClaimAllowed": False,
        },
        "warnings": [
            "Normal release checks remain offline and deterministic.",
            "Integration live fetch is opt-in and limited to the allow-listed Open-Meteo endpoint.",
            "Successful live readiness does not create a production hosted runtime or a live calibration claim.",
        ],
    }
    errors = validate_record(record, SCHEMA)
    if errors:
        raise LiveReadinessError(f"live connector readiness schema validation failed: {errors[0]}")
    return record


def integration_live_fetch(
    *,
    readiness: dict[str, Any],
    service_date: str,
    location: str,
) -> dict[str, Any]:
    source_url = build_url(location, service_date)
    result = {
        "mode": "integration_live_fetch",
        "serviceDate": service_date,
        "location": location,
        "connectorKey": readiness["connector"]["connectorKey"],
        "sourceConnectorRegistryId": readiness["recordBinding"]["sourceConnectorRegistryId"],
        "sourceConnectorResultSetId": readiness["recordBinding"]["sourceConnectorResultSetId"],
        "connectorResultId": readiness["recordBinding"]["connectorResultId"],
        "controls": {
            "networkAccess": True,
            "liveFetch": True,
            "effectfulGeneration": False,
            "credentialUsed": False,
            "promptVisibleCredentialAccepted": False,
        },
    }
    try:
        raw = fetch_raw(source_url)
        payload = json.loads(raw.decode("utf-8"))
        normalized = normalize_response(
            payload=payload,
            raw=raw,
            source_url=source_url,
            retrieved_at=utc_now(),
            location_key=location,
            service_date=service_date,
        )
    except SystemExit as exc:
        return {
            **result,
            "resultStatus": "failed_sanitized",
            "retrievalDiagnostics": {
                "diagnosticLevel": "sanitized",
                "publicMessage": str(exc)[:240],
                "rawDiagnosticStored": False,
                "rawStackTraceExposed": False,
            },
        }
    except Exception:
        return {
            **result,
            "resultStatus": "failed_sanitized",
            "retrievalDiagnostics": {
                "diagnosticLevel": "sanitized",
                "publicMessage": readiness["diagnosticsBoundary"]["publicFailureMessage"],
                "rawDiagnosticStored": False,
                "rawStackTraceExposed": False,
            },
        }
    return {
        **result,
        "resultStatus": "succeeded_live_fetch",
        "rawSourceMetadata": {
            "mode": "live_fetch",
            "sourceUri": normalized["sourceRef"]["uri"],
            "contentHash": normalized["sourceRef"]["contentHash"],
            "rawPreviewStored": False,
        },
        "provenance": {
            "sourceRef": normalized["sourceRef"],
            "retrievedAt": normalized["sourceRef"]["retrievedAt"],
            "storesContentHash": True,
            "allEvidenceClaimed": False,
        },
        "normalizedFields": normalized["normalizedFields"],
        "retrievalDiagnostics": {
            "diagnosticLevel": "none",
            "publicMessage": "Opt-in live Open-Meteo readiness fetch succeeded.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
    }


def write_readiness(record: dict[str, Any]) -> None:
    write_generated(READINESS_PATH, record, label="live connector readiness", regen="python3 scripts/generate_live_connector_readiness.py --write")


def check_readiness(record: dict[str, Any]) -> None:
    check_generated(READINESS_PATH, record, label="live connector readiness", regen="python3 scripts/generate_live_connector_readiness.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--check", action="store_true", help="check generated readiness drift")
    parser.add_argument("--write", action="store_true", help="refresh generated readiness fixture")
    parser.add_argument("--live", action="store_true", help="perform an opt-in integration live fetch")
    parser.add_argument("--save-local", action="store_true", help="save sanitized live connector output under .ope/live")
    parser.add_argument("--workspace", type=Path, default=ROOT / ".ope" / "live", help="ignored local live workspace")
    parser.add_argument("--location", choices=["warsaw"], default="warsaw")
    parser.add_argument("--service-date", default=default_service_date())
    args = parser.parse_args()

    readiness = build_readiness(args.request)
    if args.live and args.write:
        raise SystemExit("use either --live or --write, not both")
    if args.save_local and not args.live:
        raise SystemExit("--save-local requires --live")
    if args.live:
        result = integration_live_fetch(
            readiness=readiness,
            service_date=args.service_date,
            location=args.location,
        )
        response = {"readiness": readiness, "integrationResult": result}
        if args.save_local:
            result_set = build_live_result_set(
                readiness=readiness,
                integration_result=result,
                request_path=args.request,
            )
            path = save_live_result_set(
                result_set=result_set,
                workspace=args.workspace,
                location=args.location,
                service_date=args.service_date,
            )
            response["localCapture"] = {
                "written": rel(path),
                "sourceConnectorResultSetId": result_set["sourceConnectorResultSetId"],
                "executionMode": result_set["executionMode"],
                "resultStatus": result_set["connectorResults"][0]["resultStatus"],
                "publicReadSurface": False,
                "releaseCheckInput": False,
            }
        sys.stdout.write(render_json(response))
    elif args.write:
        write_readiness(readiness)
    elif args.check:
        check_readiness(readiness)
    else:
        sys.stdout.write(render_json(readiness))


if __name__ == "__main__":
    main()
