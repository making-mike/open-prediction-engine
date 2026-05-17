"""Shared source connector catalog for local fixture-safe auto-evidence checks."""

from __future__ import annotations

from typing import Any


SOURCE_CONNECTOR_REGISTRY_ID = "sourceconnectorregistry-001"
SOURCE_CONNECTOR_RESULT_SET_ID = "sourceconnectorresults-001"

FORECAST_TIME_CONNECTORS = {"open_meteo_weather", "committed_fixture"}
RESOLUTION_ONLY_CONNECTORS = {"declared_operations_fixture"}
UNSUPPORTED_CONNECTORS = {"web_search", "market_price_feed"}
REGISTERED_CONNECTORS = FORECAST_TIME_CONNECTORS | RESOLUTION_ONLY_CONNECTORS | UNSUPPORTED_CONNECTORS

CONNECTOR_IDS = {
    "open_meteo_weather": "sourceconnector-001",
    "committed_fixture": "sourceconnector-002",
    "declared_operations_fixture": "sourceconnector-003",
    "web_search": "sourceconnector-004",
    "market_price_feed": "sourceconnector-005",
}

CONNECTOR_RESULT_IDS = {
    "open_meteo_weather": "connectorresult-001",
    "committed_fixture": "connectorresult-002",
    "declared_operations_fixture": "connectorresult-003",
    "web_search": "connectorresult-004",
    "market_price_feed": "connectorresult-005",
}


def connector_policy_checks(source_policy: dict[str, Any]) -> dict[str, Any]:
    requested = set(source_policy["allowedConnectors"])
    registered = requested & REGISTERED_CONNECTORS
    unregistered = requested - REGISTERED_CONNECTORS
    unsupported = requested & UNSUPPORTED_CONNECTORS
    resolution_only = requested & RESOLUTION_ONLY_CONNECTORS
    forecast_time = requested & FORECAST_TIME_CONNECTORS
    return {
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "expectedSourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "requestedConnectors": sorted(requested),
        "registeredConnectors": sorted(registered),
        "unregisteredConnectors": sorted(unregistered),
        "unsupportedConnectors": sorted(unsupported),
        "resolutionOnlyConnectors": sorted(resolution_only),
        "forecastTimeConnectors": sorted(forecast_time),
        "allRequestedConnectorsRegistered": not unregistered,
    }


def connector_binding(connector_key: str) -> dict[str, str]:
    return {
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "connectorId": CONNECTOR_IDS[connector_key],
        "sourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "connectorResultId": CONNECTOR_RESULT_IDS[connector_key],
    }
