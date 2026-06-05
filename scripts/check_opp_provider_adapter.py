#!/usr/bin/env python3
"""Check optional Open Prediction Protocol provider adapter boundaries."""

from __future__ import annotations

try:
    from generate_opp_provider_adapter import build_opp_provider_adapter
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("OPP provider adapter generator is missing") from exc


REQUIRED_REQUEST_FIELDS = [
    "predictionRequestId",
    "marketOrQuestion",
    "domain",
    "horizon",
    "outputType",
    "sourcePolicy",
    "callerIdentity",
    "constraints",
]

REQUIRED_RESPONSE_REFS = {
    "forecastId",
    "questionId",
    "evidenceTraceId",
    "lifecycleBundleId",
    "forecastCardRecordType",
    "forecastArtifactRecordType",
}

REQUIRED_CASES = [
    "accepted_forecast_card",
    "unsupported_market",
    "malformed_outcome_spec",
    "missing_source_policy",
    "provider_timeout",
    "response_too_large",
]

BLOCKED_EXPECTED = {
    "unsupported_market": ("blocked_unsupported_market", "choose_supported_domain"),
    "malformed_outcome_spec": ("blocked_malformed_outcome_spec", "repair_resolution_rule"),
    "missing_source_policy": ("blocked_missing_source_policy", "provide_source_policy"),
    "provider_timeout": ("blocked_provider_timeout", "retry_or_use_ope_readback"),
    "response_too_large": ("blocked_response_too_large", "request_compact_response"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    adapter = build_opp_provider_adapter()

    require(adapter["providerAdapterStatus"] == "optional_opp_provider_adapter_checked", "adapter status drifted")
    require(adapter["adapterScope"] == "interop_mapping_over_ope_lifecycle_records", "adapter scope drifted")
    require(adapter["normalChecksOffline"] is True, "normal checks must stay offline")
    require(adapter["localMcpStdioTested"] is True, "local MCP stdio should remain the tested current protocol")
    require(adapter["httpProviderRuntimeImplemented"] is False, "OPP HTTP runtime must remain future work")
    require(adapter["sseStreamingImplemented"] is False, "OPP SSE streaming must remain future work")
    require(adapter["paymentSettlementImplemented"] is False, "OPP payment settlement must remain future work")
    require(adapter["aggregationImplemented"] is False, "OPP aggregation must remain future work")
    require(adapter["hostedServiceRequired"] is False, "OPP adapter must not require hosted service")

    request_rows = adapter["requestMapping"]["mappingRows"]
    require([item["oppField"] for item in request_rows] == REQUIRED_REQUEST_FIELDS, "OPP request mapping order drifted")
    for item in request_rows:
        require(item["mappingStatus"] == "mapped_to_ope_contract", f"{item['oppField']} mapping should be checked")
        require(item["rawPromptStored"] is False, f"{item['oppField']} must not store raw prompt text")
        require(item["credentialValuesAccepted"] is False, f"{item['oppField']} must not accept credential values")
    require(
        adapter["requestMapping"]["mapsToOpeForecastRequest"] is True,
        "OPP request mapping should map into OPE forecast request semantics",
    )
    require(adapter["requestMapping"]["createsOpeRecordsDirectly"] is False, "request mapping must not create OPE records directly")

    response = adapter["responseMapping"]
    require(response["mapsFromForecastCard"] is True, "OPP response should map from forecast cards")
    require(response["mapsFromForecastArtifact"] is True, "OPP response should map from forecast artifacts")
    require(response["auditMetadataChannel"] in {"audit", "provenance"}, "OPP audit metadata channel drifted")
    require(set(response["requiredOpeRecordRefs"]) == REQUIRED_RESPONSE_REFS, "OPP response record refs drifted")
    require(response["claimBoundaryCarried"] is True, "OPP response must carry claim boundaries")
    require(response["scoreStatusCarried"] is True, "OPP response must carry score status")
    require(response["rawLifecycleBundleEmbedded"] is False, "OPP response must not embed full lifecycle bundles by default")

    card = adapter["agentCard"]
    require(card["agentCardStatus"] == "checked_fixture", "OPP Agent Card status drifted")
    require(card["providerId"] == "ope-local-fixture-provider", "OPP provider id drifted")
    require(card["advertisedRuntime"] == "local_cli_fixture_only", "OPP Agent Card runtime claim drifted")
    require(card["httpEndpointAdvertised"] is False, "OPP Agent Card must not advertise a live HTTP endpoint")
    require(card["sseEndpointAdvertised"] is False, "OPP Agent Card must not advertise SSE")
    require(card["aggregationAdvertised"] is False, "OPP Agent Card must not advertise aggregation")
    require(card["supportedPricingModes"] == ["free_local_fixture"], "OPP Agent Card pricing modes drifted")
    domains = {item["domain"]: item for item in card["domainCapabilities"]}
    require({"weather-logistics", "weather-transit-delays", "seaport-berth-availability"} <= set(domains), "OPP Agent Card domain coverage drifted")
    for item in domains.values():
        require(item["liveCalibrationClaimAllowed"] is False, "OPP Agent Card must not advertise live calibration")
        require(item["paidProviderRequired"] is False, "OPP Agent Card must not require paid providers")
        require(item["complianceStatus"] == "policy_boundary_only", "OPP Agent Card compliance status drifted")

    cases = {item["caseName"]: item for item in adapter["conformanceCases"]}
    require(list(cases) == REQUIRED_CASES, "OPP conformance case order drifted")
    accepted = cases["accepted_forecast_card"]
    require(accepted["caseStatus"] == "response_ready", "accepted OPP case status drifted")
    require(accepted["predictionRequest"]["sourcePolicy"]["mode"] == "fixture", "accepted OPP case should bind fixture source policy")
    require(accepted["predictionResponse"]["predictionResponseId"] == "opppredictionresponse-001", "accepted OPP response id drifted")
    require(accepted["predictionResponse"]["probability"] == accepted["opeForecastCard"]["probability"], "OPP probability should come from forecast card")
    require(accepted["predictionResponse"]["audit"]["forecastId"] == accepted["opeForecastCard"]["forecastId"], "OPP audit forecast binding drifted")
    require(accepted["predictionResponse"]["audit"]["evidenceTraceId"] == "forecast-602", "OPP evidence-trace binding drifted")
    require(accepted["forecastArtifactsCreated"] is False, "OPP accepted response must not create forecast artifacts")
    require(accepted["usesExistingOpeRecords"] is True, "OPP accepted response should use existing OPE records")
    require(accepted["claimBoundaryPreserved"] is True, "OPP accepted response should preserve claim boundary")
    for case_name, (status, next_action) in BLOCKED_EXPECTED.items():
        case = cases[case_name]
        require(case["caseStatus"] == status, f"{case_name} status drifted")
        require(case["nextAction"] == next_action, f"{case_name} next action drifted")
        require(case["forecastArtifactsCreated"] is False, f"{case_name} must not create forecast artifacts")
        require(case["opeRecordsMutated"] is False, f"{case_name} must not mutate OPE records")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case_name} should keep diagnostics sanitized")

    conformance = adapter["conformancePlan"]
    require(conformance["minimalSurfaceStatus"] == "plan_checked_no_http_listener", "OPP conformance plan status drifted")
    require(conformance["normalChecksStartHttpServer"] is False, "OPP normal checks must not start HTTP")
    require(conformance["providerCardChecked"] is True, "OPP conformance should check provider card")
    require(conformance["requestResponseFixturesChecked"] is True, "OPP conformance should check request/response fixtures")
    require(conformance["errorFixturesChecked"] is True, "OPP conformance should check error fixtures")
    require(conformance["requiredFutureEndpoints"] == ["/opp/v1/agent-card", "/opp/v1/predictions"], "OPP future endpoints drifted")

    boundary = adapter["protocolBoundary"]
    for key in [
        "opeRecordsAuthoritative",
        "oppOptionalInterop",
        "localMcpStdioCurrentTestedProtocol",
        "preservesForecastSemantics",
        "preservesEvidenceSemantics",
        "preservesResolutionScoringCalibrationSemantics",
    ]:
        require(boundary[key] is True, f"OPP boundary {key} should stay true")
    for key in [
        "oppReplacesOpeLifecycleRecords",
        "httpRuntimeImplemented",
        "sseRuntimeImplemented",
        "paymentSettlementImplemented",
        "aggregationRuntimeImplemented",
        "hostedServiceImplemented",
        "networkListenerStarted",
        "normalChecksUseNetwork",
        "rawLifecycleBundleEmbeddedByDefault",
        "qualityClaimsUpgraded",
    ]:
        require(boundary[key] is False, f"OPP boundary {key} should stay false")

    readbacks = {item["readbackSurface"]: item for item in adapter["readbacks"]}
    require(set(readbacks) == {"cli", "agent_card", "accepted_response"}, "OPP readback coverage drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py opp-provider-adapter", "OPP CLI readback drifted")
    for readback in readbacks.values():
        require(readback["mutatesState"] is False, "OPP readbacks must not mutate state")
        require(readback["startsNetworkListener"] is False, "OPP readbacks must not start network listeners")

    summary = adapter["summary"]
    require(summary["requestMappingCount"] == len(REQUIRED_REQUEST_FIELDS), "OPP request mapping count drifted")
    require(summary["conformanceCaseCount"] == len(REQUIRED_CASES), "OPP case count drifted")
    require(summary["blockedCaseCount"] == len(BLOCKED_EXPECTED), "OPP blocked case count drifted")
    require(summary["supportedDomainCount"] >= 3, "OPP supported domain count drifted")
    require(summary["httpRuntimeImplemented"] is False, "OPP summary should keep HTTP runtime future")
    require(summary["oppReplacesOpeRecords"] is False, "OPP summary must not replace OPE records")

    print("checked OPP provider adapter")


if __name__ == "__main__":
    main()
