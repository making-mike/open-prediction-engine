#!/usr/bin/env python3
"""Check policy-bound source connector registry and result invariants."""

from __future__ import annotations

from gather_auto_evidence import build_source_set
from generate_source_connectors import build_outputs
from source_connector_catalog import connector_binding


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry, result_set = build_outputs()
    source_set = build_source_set()
    connectors = {item["connectorKey"]: item for item in registry["connectors"]}
    results = {item["connectorKey"]: item for item in result_set["connectorResults"]}

    require("open_meteo_weather" in connectors, "registry should include Open-Meteo connector")
    require("committed_fixture" in connectors, "registry should include committed fixture connector")
    require("web_search" in connectors, "registry should explicitly include unsupported web search")
    require("market_price_feed" in connectors, "registry should explicitly include unsupported source class")
    require("market_price" in registry["unsupportedSourceClasses"], "registry should mark market_price unsupported")

    for key in ["open_meteo_weather", "committed_fixture"]:
        connector = connectors[key]
        require(connector["status"] == "enabled_fixture_replay", f"{key} should be fixture-replay enabled")
        require(connector["policyBinding"]["allowedBySourcePolicy"] is True, f"{key} should bind to source policy")
        require(connector["capability"]["networkAccessInNormalChecks"] is False, f"{key} must not network in checks")
        require(connector["credentialBoundary"]["acceptsPromptVisibleCredentials"] is False, f"{key} must reject prompt-visible credentials")
        require(connector["diagnosticsBoundary"]["exposesRawStackTraces"] is False, f"{key} must sanitize diagnostics")
        require(connector["provenanceBoundary"]["allEvidenceClaimed"] is False, f"{key} must not claim all evidence")

    for key in ["web_search", "market_price_feed"]:
        connector = connectors[key]
        require(connector["status"] == "unsupported", f"{key} should be unsupported")
        require(connector["allowedFor"] == ["not_allowed"], f"{key} should not be allowed for forecast evidence")
        require(connector["policyBinding"]["allowedBySourcePolicy"] is False, f"{key} must not bind to source policy")
        require(connector["capability"]["maxNetworkCalls"] == 0, f"{key} should not make network calls")

    require(result_set["executionMode"] == "fixture_replay", "committed result set must remain fixture replay")
    require(result_set["controls"]["networkAccess"] is False, "result set must be fixture-safe")
    require(result_set["controls"]["liveFetch"] is False, "result set must not live-fetch")
    require(result_set["controls"]["promptVisibleCredentialAccepted"] is False, "result set must reject prompt-visible credentials")

    for record in source_set["records"]:
        binding = record["connectorBinding"]
        key = record["connector"]
        require(binding == connector_binding(key), f"{key} source record should bind to connector catalog IDs")
        require(binding["sourceConnectorRegistryId"] == registry["sourceConnectorRegistryId"], f"{key} registry binding should match registry")
        require(binding["sourceConnectorResultSetId"] == result_set["sourceConnectorResultSetId"], f"{key} result-set binding should match result set")
        require(binding["connectorId"] == connectors[key]["connectorId"], f"{key} connector ID should match registry")
        require(binding["connectorResultId"] == results[key]["connectorResultId"], f"{key} connector result ID should match result set")

    for key in ["open_meteo_weather", "committed_fixture"]:
        result = results[key]
        require(result["resultStatus"] == "succeeded_fixture_replay", f"{key} result should succeed in fixture replay")
        require(result["rawSourceMetadata"]["mode"] == "fixture_replay", f"{key} should preserve raw fixture metadata")
        require(result["rawSourceMetadata"]["contentHash"] is not None, f"{key} should preserve content hash")
        require(result["normalizedFields"] is not None, f"{key} should expose normalized fields")
        require(result["provenance"]["sourceRef"] is not None, f"{key} should preserve sourceRef")
        require(result["provenance"]["retrievedAt"] is not None, f"{key} should preserve retrievedAt")
        require(result["provenance"]["allEvidenceClaimed"] is False, f"{key} should not claim all evidence")
        require(result["controls"]["networkAccess"] is False, f"{key} result must be fixture-safe")
        require(result["retrievalDiagnostics"]["rawStackTraceExposed"] is False, f"{key} must not expose stack traces")

    resolution = results["declared_operations_fixture"]
    require(resolution["resultStatus"] == "skipped_resolution_only", "resolution connector should be skipped")
    require(resolution["normalizedFields"] is None, "resolution connector must not normalize forecast-time fields")
    require(resolution["unavailableEvidence"], "resolution connector should explain unavailable outcome evidence")

    market = results["market_price_feed"]
    require(market["sourceClass"] == "market_price", "unsupported result should preserve source class")
    require(market["resultStatus"] == "unsupported", "market source should be unsupported")
    require(market["normalizedFields"] is None, "unsupported market source must not normalize fields")
    require(market["retrievalDiagnostics"]["rawStackTraceExposed"] is False, "unsupported source must sanitize diagnostics")

    web = results["web_search"]
    require(web["resultStatus"] == "unsupported", "web search should be unsupported")
    require(web["controls"]["networkAccess"] is False, "unsupported web search must not use network")

    print("checked source connector registry and results")


if __name__ == "__main__":
    main()
