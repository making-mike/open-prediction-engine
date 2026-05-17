#!/usr/bin/env python3
"""Check live connector readiness policy boundaries."""

from __future__ import annotations

from generate_live_connector_readiness import build_readiness
from source_connector_catalog import (
    CONNECTOR_IDS,
    CONNECTOR_RESULT_IDS,
    SOURCE_CONNECTOR_REGISTRY_ID,
    SOURCE_CONNECTOR_RESULT_SET_ID,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    readiness = build_readiness()
    modes = readiness["executionModes"]
    fixture = modes["fixtureReplay"]
    integration = modes["integrationLiveFetch"]
    hosted = modes["hostedLiveFetch"]

    require(readiness["readinessStatus"] == "ready_for_explicit_integration_check", "Open-Meteo should be ready for opt-in integration check")
    require(readiness["connector"]["connectorId"] == CONNECTOR_IDS["open_meteo_weather"], "readiness should bind Open-Meteo connector ID")
    require(readiness["connector"]["sourceClass"] == "public_dataset", "readiness should keep Open-Meteo as public_dataset")

    binding = readiness["recordBinding"]
    require(binding["sourceConnectorRegistryId"] == SOURCE_CONNECTOR_REGISTRY_ID, "registry binding should match catalog")
    require(binding["sourceConnectorResultSetId"] == SOURCE_CONNECTOR_RESULT_SET_ID, "result set binding should match catalog")
    require(binding["connectorResultId"] == CONNECTOR_RESULT_IDS["open_meteo_weather"], "connector result binding should match catalog")
    require(binding["fixtureEvidenceTraceId"] == "evidencetrace-602", "readiness should preserve fixture evidence trace binding")
    require(binding["fixtureForecastId"] == "forecast-602", "readiness should preserve fixture forecast binding")
    require(binding["fixtureQuestionId"] == "question-601", "readiness should preserve fixture question binding")

    require(fixture["implemented"] is True, "fixture replay should be implemented")
    require(fixture["enabledInNormalChecks"] is True, "fixture replay should stay in normal checks")
    require(fixture["networkAccess"] is False, "fixture replay must not use network")
    require(fixture["liveFetch"] is False, "fixture replay must not live fetch")
    require(fixture["requiresExplicitFlag"] is False, "fixture replay should not require integration flag")

    require(integration["implemented"] is True, "integration live fetch should have an opt-in command")
    require(integration["enabledInNormalChecks"] is False, "integration live fetch must stay out of normal checks")
    require(integration["networkAccess"] is True, "integration live fetch should use network")
    require(integration["liveFetch"] is True, "integration live fetch should be live")
    require(integration["requiresExplicitFlag"] is True, "integration live fetch must require an explicit flag")
    require("--live" in integration["command"], "integration command should expose --live")

    require(hosted["implemented"] is False, "hosted live fetch must remain unimplemented")
    require(hosted["enabledInNormalChecks"] is False, "hosted live fetch must stay out of normal checks")
    require(hosted["resultStatus"] == "not_implemented", "hosted mode should be marked not implemented")

    network = readiness["networkBoundary"]
    require(network["allowedEndpoint"] == "https://api.open-meteo.com/v1/forecast", "network allow-list should be Open-Meteo only")
    require(network["allowBroadWebSearch"] is False, "live readiness must not allow broad web search")
    require(network["maxNetworkCalls"] == 1, "integration check should allow one network call")
    require(network["timeoutSeconds"] == 20, "integration check should keep bounded timeout")
    require(network["maxCostUsd"] == 0, "integration check should remain free")
    require(network["normalChecksNetworkAccess"] is False, "normal checks must stay offline")

    approval = readiness["approvalBoundary"]
    require(approval["operatorExplicitFlagRequired"] is True, "live readiness should require explicit operator intent")
    require(approval["approvalRecordRequiredBeforeForecastUse"] is True, "live result should require approval record before forecast use")
    require(approval["paid"] is False, "Open-Meteo readiness should be unpaid")
    require(approval["effectful"] is False, "Open-Meteo readiness should be read-only")
    require(approval["privacySensitive"] is False, "Open-Meteo readiness should avoid private data")

    retention = readiness["retentionBoundary"]
    require(retention["rawSourceRetention"] == "metadata_only", "live readiness should retain metadata only")
    require(retention["storeContentHash"] is True, "live readiness should preserve content hash")
    require(retention["rawPreviewStored"] is False, "live readiness should not store raw previews")

    diagnostics = readiness["diagnosticsBoundary"]
    require(diagnostics["sanitizedErrors"] is True, "live readiness should sanitize errors")
    require(diagnostics["rawDiagnosticStored"] is False, "live readiness should not store raw diagnostics")
    require(diagnostics["rawStackTraceExposed"] is False, "live readiness should not expose stack traces")

    credentials = readiness["credentialBoundary"]
    require(credentials["promptVisibleCredentialsAccepted"] is False, "live readiness must reject prompt-visible credentials")
    require(credentials["credentialUsed"] is False, "Open-Meteo readiness should not use credentials")

    trace = readiness["traceBinding"]
    require(trace["fixtureTracePreserved"] is True, "fixture trace should be preserved")
    require(trace["integrationTraceMustBeCompatible"] is True, "live trace should be compatible before forecast use")
    require(trace["requestResultBindingRequired"] is True, "request/result binding should be required")
    require(trace["forecastUseRequiresConnectorResult"] is True, "forecast use should require connector result")
    require(trace["forecastUseRequiresEvidenceTrace"] is True, "forecast use should require evidence trace")

    claims = readiness["claimBoundary"]
    require(claims["normalReleaseChecksOffline"] is True, "normal release checks should remain offline")
    require(claims["integrationLiveFetchPartOfRelease"] is False, "integration live fetch should not be part of release checks")
    require(claims["hostedRuntimeImplemented"] is False, "hosted runtime should remain unimplemented")
    require(claims["allEvidenceClaimed"] is False, "readiness should not claim all evidence")
    require(claims["liveCalibrationClaimAllowed"] is False, "readiness should not allow live calibration claims")
    require(claims["forecastQualityClaimAllowed"] is False, "readiness should not allow quality claims")

    print("checked live connector readiness boundaries")


if __name__ == "__main__":
    main()
