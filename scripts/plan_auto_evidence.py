#!/usr/bin/env python3
"""Generate or check an auto-evidence dry-run plan for an OPE forecast request."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_file, validate_record
from source_connector_catalog import (
    FORECAST_TIME_CONNECTORS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
    connector_policy_checks,
)
from validate_forecast_request import load_json, question_hash, validate_request
from ope_fixtures import emit_generated, render_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "spec" / "fixtures" / "requests" / "auto-weather-logistics-request.json"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "auto-evidence"
PLAN_PATH = GENERATED / "weather-logistics-auto-evidence-plan.generated.json"
GENERATED_AT = "2026-06-02T09:57:30Z"


class EvidencePlanError(Exception):
    pass


def plan_status(request: dict[str, Any], decision: dict[str, Any]) -> str:
    if decision["decisionStatus"] == "blocked":
        return "blocked"
    if decision["decisionStatus"] != "accepted":
        return "rejected"
    if request["dataMode"] != "auto":
        return "rejected"
    return "planned"


def build_connector_plan(request: dict[str, Any]) -> list[dict[str, Any]]:
    planned: list[dict[str, Any]] = []
    checks = connector_policy_checks(request["sourcePolicy"])
    for connector in request["sourcePolicy"]["allowedConnectors"]:
        if connector == "open_meteo_weather":
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Fetch public weather forecast evidence for the declared geography and service date.",
                    "networkAccess": True,
                }
            )
        elif connector == "committed_fixture":
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Read committed fixture evidence without a live source call.",
                    "networkAccess": False,
                }
            )
        elif connector in checks["resolutionOnlyConnectors"]:
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Connector is resolution-only and must not be used for forecast-time evidence.",
                    "networkAccess": False,
                }
            )
        elif connector in checks["unregisteredConnectors"]:
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Connector is missing from the checked source connector registry.",
                    "networkAccess": False,
                }
            )
        elif connector in checks["unsupportedConnectors"]:
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Connector is registered as unsupported for the first auto-evidence milestone.",
                    "networkAccess": False,
                }
            )
        else:
            planned.append(
                {
                    "connector": connector,
                    "purpose": "Connector is not enabled for the first auto-evidence milestone.",
                    "networkAccess": bool(request["sourcePolicy"]["allowNetworkAccess"]),
                }
            )
    return planned


def build_search_intents(request: dict[str, Any]) -> list[dict[str, Any]]:
    geography = request["geography"]
    service_date = request["serviceDate"]
    intents = [
        {
            "intentId": "intent-019",
            "connector": "open_meteo_weather",
            "sourceClass": "public_dataset",
            "purpose": "Forecast-time precipitation evidence for the weather-logistics disruption baseline and model.",
            "query": f"daily precipitation forecast for {geography} on {service_date}",
            "expectedEvidence": "Daily precipitation forecast, source retrieval timestamp, and source URL.",
        },
        {
            "intentId": "intent-020",
            "connector": "committed_fixture",
            "sourceClass": "internal_dataset",
            "purpose": "Historical baseline evidence for transparent comparison before stronger forecast methods.",
            "query": f"weather-logistics baseline history for {geography} and 1-day heavy-rain disruption",
            "expectedEvidence": "Comparable service-day count, disruption-day count, weather threshold bucket, and lookback window.",
        },
        {
            "intentId": "intent-021",
            "connector": "declared_operations_fixture",
            "sourceClass": "internal_dataset",
            "purpose": "Future resolution source only; not allowed in forecast-time evidence.",
            "query": f"declared operations disruption outcome for {geography} on {service_date}",
            "expectedEvidence": "Post-event operations outcome for resolution and scoring.",
        },
    ]
    allowed_classes = set(request["sourcePolicy"]["allowedSourceClasses"])
    allowed_connectors = set(request["sourcePolicy"]["allowedConnectors"])
    return [
        intent
        for intent in intents
        if (
            intent["sourceClass"] in allowed_classes
            and intent["connector"] in allowed_connectors
            and intent["connector"] in FORECAST_TIME_CONNECTORS
        )
    ]


def build_unavailable_evidence(request: dict[str, Any]) -> list[dict[str, str]]:
    checks = connector_policy_checks(request["sourcePolicy"])
    unavailable = [
        {
            "label": "Live operations outcome",
            "reason": "Outcome evidence is only valid after the service day and must not enter forecast-time provenance.",
            "impact": "Forecast may estimate weather-linked risk, but final disruption resolution waits for declared outcome sources.",
        }
    ]
    if "web_search" not in request["sourcePolicy"]["allowedConnectors"]:
        unavailable.append(
            {
                "label": "General web search",
                "reason": "The first auto-evidence policy does not allow broad web search.",
                "impact": "The plan is limited to allow-listed weather evidence and declared resolution sources.",
            }
        )
    for connector in checks["unregisteredConnectors"]:
        unavailable.append(
            {
                "label": f"Unregistered connector: {connector}",
                "reason": "The connector is not present in the checked source connector registry.",
                "impact": "OPE must reject or revise the request before evidence gathering.",
            }
        )
    for connector in checks["unsupportedConnectors"]:
        unavailable.append(
            {
                "label": f"Unsupported connector: {connector}",
                "reason": "The connector is registered as unsupported for the first auto-evidence milestone.",
                "impact": "OPE must not gather evidence from this connector in normal checks.",
            }
        )
    for connector in checks["resolutionOnlyConnectors"]:
        unavailable.append(
            {
                "label": f"Resolution-only connector: {connector}",
                "reason": "The connector may only be used after the service window for resolution and scoring.",
                "impact": "Forecast-time search intents must exclude this connector.",
            }
        )
    return unavailable


def build_plan(request_path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    _schema_path, schema_errors = validate_file(request_path, SPEC / "forecast-request.schema.json")
    if schema_errors:
        raise EvidencePlanError(f"request contract validation failed: {schema_errors[0]}")
    request = load_json(request_path)
    decision = validate_request(request)
    status = plan_status(request, decision)
    checks = connector_policy_checks(request["sourcePolicy"])
    plan = {
        "evidencePlanId": "evidenceplan-019",
        "requestId": request["requestId"],
        "generatedAt": GENERATED_AT,
        "planStatus": status,
        "executionMode": "dry_run",
        "dataMode": request["dataMode"],
        "domain": request["domain"],
        "geography": request["geography"],
        "serviceDate": request["serviceDate"],
        "horizonLabel": request["horizonLabel"],
        "questionHash": question_hash(request["questionText"]),
        "sourcePolicy": request["sourcePolicy"],
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "expectedSourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "connectorPolicyChecks": checks,
        "plannedConnectors": build_connector_plan(request),
        "searchIntents": build_search_intents(request),
        "inclusionRules": [
            "Use only evidence available before the forecast close time.",
            "Use only connectors allowed by the request source policy.",
            "Preserve source retrieval timestamps and provenance references.",
        ],
        "exclusionRules": [
            "Do not use post-outcome operations records as forecast-time evidence.",
            "Do not use broad web search unless the source policy explicitly enables it.",
            "Do not use paid, private, or high-impact sources without approval.",
        ],
        "unavailableEvidence": build_unavailable_evidence(request),
        "controls": {
            "networkAccess": False,
            "liveFetch": False,
            "effectfulGeneration": False,
        },
        "warnings": [
            "Dry-run evidence plan only; no live source was fetched.",
            "Current auto-evidence support is limited to the weather-logistics wedge.",
            "This plan does not support a live calibration or state-of-the-art performance claim.",
        ],
    }
    errors = validate_record(plan, SPEC / "evidence-gathering-plan.schema.json")
    if errors:
        raise EvidencePlanError(f"evidence plan schema validation failed: {errors[0]}")
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--check", action="store_true", help="check generated auto-evidence plan drift")
    parser.add_argument("--write", action="store_true", help="write generated auto-evidence plan")
    args = parser.parse_args()
    try:
        plan = build_plan(args.request)
    except EvidencePlanError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write or args.check:
        emit_generated(PLAN_PATH, plan, write=args.write, label="auto-evidence plan", regen="python3 scripts/plan_auto_evidence.py --write")
    else:
        sys.stdout.write(render_json(plan))


if __name__ == "__main__":
    main()
