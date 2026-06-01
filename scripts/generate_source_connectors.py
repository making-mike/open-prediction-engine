#!/usr/bin/env python3
"""Generate or check policy-bound source connector registry and result fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from gather_auto_evidence import build_source_set
from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from source_connector_catalog import (
    CONNECTOR_IDS,
    CONNECTOR_RESULT_IDS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
)
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-connectors"
REGISTRY_PATH = GENERATED / "weather-logistics-source-connector-registry.generated.json"
RESULTS_PATH = GENERATED / "weather-logistics-source-connector-results.generated.json"
REGISTRY_SCHEMA = SPEC / "source-connector-registry.schema.json"
RESULT_SET_SCHEMA = SPEC / "source-connector-result-set.schema.json"
GENERATED_AT = "2026-06-06T13:45:00Z"
OPERATIONS_OUTCOME_FIXTURE = (
    ROOT / "spec" / "fixtures" / "live" / "weather-logistics-warsaw-2026-06-03-operations-outcome.json"
)


class SourceConnectorError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def connector(
    *,
    connector_id: str,
    connector_key: str,
    display_name: str,
    status: str,
    source_class: str,
    allowed_for: list[str],
    allowed_by_policy: bool,
    source_policy_id: str | None,
    approval_required: bool,
    retrieval_mode: str,
    max_network_calls: int,
    max_cost_usd: int | float,
    max_source_age_hours: int | None,
    require_retrieved_at: bool,
    raw_source_retention: str,
    agent_use: str,
) -> dict[str, Any]:
    return {
        "connectorId": connector_id,
        "connectorKey": connector_key,
        "displayName": display_name,
        "status": status,
        "sourceClass": source_class,
        "allowedFor": allowed_for,
        "policyBinding": {
            "allowedBySourcePolicy": allowed_by_policy,
            "sourcePolicyId": source_policy_id,
            "approvalRequired": approval_required,
        },
        "capability": {
            "retrievalMode": retrieval_mode,
            "networkAccessInNormalChecks": False,
            "liveFetchRequiresApproval": retrieval_mode == "live_fetch_gated",
            "maxNetworkCalls": max_network_calls,
            "maxCostUsd": max_cost_usd,
        },
        "freshness": {
            "maxSourceAgeHours": max_source_age_hours,
            "requireRetrievedAt": require_retrieved_at,
        },
        "rateLimit": {
            "maxRequestsPerRun": max_network_calls,
            "cooldownSeconds": 0,
            "enforcedInNormalChecks": True,
        },
        "credentialBoundary": {
            "acceptsPromptVisibleCredentials": False,
            "credentialLocation": "none",
            "notes": "No prompt-visible credentials are accepted for this local fixture-safe connector.",
        },
        "provenanceBoundary": {
            "rawSourceRetention": raw_source_retention,
            "storesContentHash": raw_source_retention != "none",
            "storesRetrievedAt": require_retrieved_at,
            "allEvidenceClaimed": False,
        },
        "diagnosticsBoundary": {
            "sanitizedErrors": True,
            "exposesRawStackTraces": False,
        },
        "risk": {
            "effectful": False,
            "paid": False,
            "privacySensitive": False,
        },
        "agentUse": agent_use,
    }


def build_registry(request_path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    plan = build_plan(request_path)
    policy = plan["sourcePolicy"]
    allowed_connectors = set(policy["allowedConnectors"])
    source_policy_id = policy["sourcePolicyId"]
    freshness_hours = int(policy["freshness"]["maxSourceAgeHours"])
    registry = {
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "generatedAt": GENERATED_AT,
        "domain": plan["domain"],
        "sourcePolicyId": source_policy_id,
        "defaultExecutionMode": "fixture_replay",
        "connectors": [
            connector(
                connector_id=CONNECTOR_IDS["open_meteo_weather"],
                connector_key="open_meteo_weather",
                display_name="Open-Meteo Weather Forecast",
                status="enabled_fixture_replay",
                source_class="public_dataset",
                allowed_for=["forecast_time_evidence"],
                allowed_by_policy="open_meteo_weather" in allowed_connectors,
                source_policy_id=source_policy_id if "open_meteo_weather" in allowed_connectors else None,
                approval_required=False,
                retrieval_mode="fixture_replay",
                max_network_calls=int(policy["maxNetworkCalls"]),
                max_cost_usd=float(policy["maxCostUsd"]),
                max_source_age_hours=freshness_hours,
                require_retrieved_at=True,
                raw_source_retention=policy["retention"]["rawSourceRetention"],
                agent_use="Use for forecast-time public weather evidence in the weather-logistics wedge.",
            ),
            connector(
                connector_id=CONNECTOR_IDS["committed_fixture"],
                connector_key="committed_fixture",
                display_name="Committed Baseline Fixture",
                status="enabled_fixture_replay",
                source_class="internal_dataset",
                allowed_for=["baseline_input"],
                allowed_by_policy="committed_fixture" in allowed_connectors,
                source_policy_id=source_policy_id if "committed_fixture" in allowed_connectors else None,
                approval_required=False,
                retrieval_mode="committed_fixture",
                max_network_calls=0,
                max_cost_usd=0,
                max_source_age_hours=freshness_hours,
                require_retrieved_at=True,
                raw_source_retention="fixture_only",
                agent_use="Use for transparent baseline comparison from committed local fixtures.",
            ),
            connector(
                connector_id=CONNECTOR_IDS["declared_operations_fixture"],
                connector_key="declared_operations_fixture",
                display_name="Declared Operations Outcome Fixture",
                status="resolution_only",
                source_class="internal_dataset",
                allowed_for=["resolution_only"],
                allowed_by_policy=False,
                source_policy_id=None,
                approval_required=False,
                retrieval_mode="committed_fixture",
                max_network_calls=0,
                max_cost_usd=0,
                max_source_age_hours=None,
                require_retrieved_at=False,
                raw_source_retention="fixture_only",
                agent_use="Use only after the service window for resolution and scoring, never as forecast-time evidence.",
            ),
            connector(
                connector_id=CONNECTOR_IDS["web_search"],
                connector_key="web_search",
                display_name="General Web Search",
                status="unsupported",
                source_class="other",
                allowed_for=["not_allowed"],
                allowed_by_policy=False,
                source_policy_id=None,
                approval_required=True,
                retrieval_mode="unsupported",
                max_network_calls=0,
                max_cost_usd=0,
                max_source_age_hours=None,
                require_retrieved_at=False,
                raw_source_retention="none",
                agent_use="Do not use; broad web search is outside the first fixture-safe auto-evidence milestone.",
            ),
            connector(
                connector_id=CONNECTOR_IDS["market_price_feed"],
                connector_key="market_price_feed",
                display_name="Market Price Feed",
                status="unsupported",
                source_class="market_price",
                allowed_for=["not_allowed"],
                allowed_by_policy=False,
                source_policy_id=None,
                approval_required=True,
                retrieval_mode="unsupported",
                max_network_calls=0,
                max_cost_usd=0,
                max_source_age_hours=None,
                require_retrieved_at=False,
                raw_source_retention="none",
                agent_use="Do not use for weather-logistics; market-price sources are unsupported in this domain wedge.",
            ),
        ],
        "unsupportedSourceClasses": ["human_judgment", "model_output", "market_price", "aggregate", "other"],
        "warnings": [
            "Normal checks use fixture replay and do not perform live network calls.",
            "The registry does not authorize unbounded internet search.",
            "Unsupported source classes must not be silently used for forecast-time evidence.",
        ],
    }
    validate_registry(registry)
    return registry


def empty_controls() -> dict[str, bool]:
    return {
        "networkAccess": False,
        "liveFetch": False,
        "effectfulGeneration": False,
        "credentialUsed": False,
        "promptVisibleCredentialAccepted": False,
    }


def succeeded_result(
    result_id: str,
    record: dict[str, Any],
) -> dict[str, Any]:
    if result_id != record["connectorBinding"]["connectorResultId"]:
        raise SourceConnectorError("source record connector result binding mismatch")
    return {
        "connectorResultId": result_id,
        "connectorKey": record["connector"],
        "sourceClass": record["sourceRef"]["sourceType"],
        "sourceRole": record["sourceRole"],
        "resultStatus": "succeeded_fixture_replay",
        "plannedIntentIds": record["plannedIntentIds"],
        "rawSourceMetadata": {
            "mode": "fixture_replay",
            "fixturePath": record["rawSourceMetadata"]["fixturePath"],
            "sourceUri": record["sourceRef"].get("uri"),
            "contentHash": record["rawSourceMetadata"]["contentHash"],
            "rawPreviewStored": False,
        },
        "normalizedFields": record["normalizedFields"],
        "unavailableEvidence": [],
        "retrievalDiagnostics": {
            "diagnosticLevel": "none",
            "publicMessage": "Fixture replay succeeded.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
        "provenance": {
            "sourceRef": record["sourceRef"],
            "retrievedAt": record["sourceRef"].get("retrievedAt"),
            "storesContentHash": True,
            "allEvidenceClaimed": False,
        },
        "controls": empty_controls(),
    }


def skipped_resolution_result() -> dict[str, Any]:
    return {
        "connectorResultId": CONNECTOR_RESULT_IDS["declared_operations_fixture"],
        "connectorKey": "declared_operations_fixture",
        "sourceClass": "internal_dataset",
        "sourceRole": "resolution_primary",
        "resultStatus": "skipped_resolution_only",
        "plannedIntentIds": [],
        "rawSourceMetadata": {
            "mode": "not_fetched",
            "fixturePath": rel(OPERATIONS_OUTCOME_FIXTURE),
            "sourceUri": None,
            "contentHash": None,
            "rawPreviewStored": False,
        },
        "normalizedFields": None,
        "unavailableEvidence": [
            {
                "label": "Declared operations outcome",
                "reason": "Outcome evidence is only valid after the service day and must not enter forecast-time evidence.",
                "agentNextAction": "Wait for resolution time before reading resolution or scoring outputs.",
            }
        ],
        "retrievalDiagnostics": {
            "diagnosticLevel": "sanitized",
            "publicMessage": "Resolution-only connector skipped during forecast-time gathering.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
        "provenance": {
            "sourceRef": None,
            "retrievedAt": None,
            "storesContentHash": False,
            "allEvidenceClaimed": False,
        },
        "controls": empty_controls(),
    }


def unsupported_result(
    *,
    result_id: str,
    connector_key: str,
    source_class: str,
    label: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "connectorResultId": result_id,
        "connectorKey": connector_key,
        "sourceClass": source_class,
        "sourceRole": "unsupported",
        "resultStatus": "unsupported",
        "plannedIntentIds": [],
        "rawSourceMetadata": {
            "mode": "unsupported",
            "fixturePath": None,
            "sourceUri": None,
            "contentHash": None,
            "rawPreviewStored": False,
        },
        "normalizedFields": None,
        "unavailableEvidence": [
            {
                "label": label,
                "reason": reason,
                "agentNextAction": "Use only source classes and connectors allowed by the source policy.",
            }
        ],
        "retrievalDiagnostics": {
            "diagnosticLevel": "sanitized",
            "publicMessage": "Connector is unsupported for the current fixture-safe source policy.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
        "provenance": {
            "sourceRef": None,
            "retrievedAt": None,
            "storesContentHash": False,
            "allEvidenceClaimed": False,
        },
        "controls": empty_controls(),
    }


def build_result_set(request_path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    plan = build_plan(request_path)
    source_set = build_source_set(request_path)
    results = [
        succeeded_result(CONNECTOR_RESULT_IDS["open_meteo_weather"], source_set["records"][0]),
        succeeded_result(CONNECTOR_RESULT_IDS["committed_fixture"], source_set["records"][1]),
        skipped_resolution_result(),
        unsupported_result(
            result_id=CONNECTOR_RESULT_IDS["web_search"],
            connector_key="web_search",
            source_class="other",
            label="General web search",
            reason="Broad web search is not enabled for this fixture-safe auto-evidence path.",
        ),
        unsupported_result(
            result_id=CONNECTOR_RESULT_IDS["market_price_feed"],
            connector_key="market_price_feed",
            source_class="market_price",
            label="Market price source class",
            reason="Market-price evidence is unsupported for the weather-logistics wedge.",
        ),
    ]
    result_set = {
        "sourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "generatedAt": GENERATED_AT,
        "requestId": plan["requestId"],
        "evidencePlanId": plan["evidencePlanId"],
        "sourcePolicyId": plan["sourcePolicy"]["sourcePolicyId"],
        "domain": plan["domain"],
        "executionMode": "fixture_replay",
        "connectorResults": results,
        "controls": empty_controls(),
        "warnings": [
            "Connector results are fixture-safe and do not fetch live internet sources.",
            "Unsupported connector results explain unavailable evidence without raw diagnostics.",
            "No connector result claims complete coverage of all possible evidence.",
        ],
    }
    validate_result_set(result_set)
    return result_set


def validate_registry(registry: dict[str, Any]) -> None:
    errors = validate_record(registry, REGISTRY_SCHEMA)
    if errors:
        raise SourceConnectorError(f"source connector registry schema validation failed: {errors[0]}")


def validate_result_set(result_set: dict[str, Any]) -> None:
    errors = validate_record(result_set, RESULT_SET_SCHEMA)
    if errors:
        raise SourceConnectorError(f"source connector result set schema validation failed: {errors[0]}")


def build_outputs(request_path: Path = DEFAULT_REQUEST) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = build_registry(request_path)
    result_set = build_result_set(request_path)
    return registry, result_set


def write_outputs(registry: dict[str, Any], result_set: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(render_json(registry), encoding="utf-8")
    RESULTS_PATH.write_text(render_json(result_set), encoding="utf-8")
    print("generated source connector registry and results")


def check_outputs(registry: dict[str, Any], result_set: dict[str, Any]) -> None:
    expected = {
        REGISTRY_PATH: render_json(registry),
        RESULTS_PATH: render_json(result_set),
    }
    errors: list[str] = []
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing source connector output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"source connector drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_source_connectors.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source connector registry and results")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--results", action="store_true", help="print connector result set instead of registry")
    parser.add_argument("--check", action="store_true", help="check generated source connector drift")
    parser.add_argument("--write", action="store_true", help="write generated source connector fixtures")
    args = parser.parse_args()
    try:
        registry, result_set = build_outputs(args.request)
    except SourceConnectorError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(registry, result_set)
    elif args.check:
        check_outputs(registry, result_set)
    elif args.results:
        sys.stdout.write(render_json(result_set))
    else:
        sys.stdout.write(render_json(registry))


if __name__ == "__main__":
    main()
