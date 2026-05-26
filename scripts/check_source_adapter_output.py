#!/usr/bin/env python3
"""Check source adapter output handoff invariants."""

from __future__ import annotations

from generate_source_adapter_output import build_output


def main() -> None:
    output = build_output()
    manifest = output["sourceManifest"]
    mapping = output["fieldMapping"]
    sources = {item["sourceRole"]: item for item in manifest["sources"]}

    if output["outputStatus"] != "intake_ready":
        raise AssertionError("source adapter output fixture should be intake-ready")
    if output["adapter"]["implementationLocation"] != "external_agent":
        raise AssertionError("fixture should model an external agent connector")
    if output["adapter"]["ownsForecastSemantics"] is not False:
        raise AssertionError("source adapters must not own forecast semantics")
    if output["handoffBoundary"]["sourceIntakeRequired"] is not True:
        raise AssertionError("source adapter outputs must route through source intake")
    if output["controls"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("source adapter output must not allow forecast generation directly")
    if output["controls"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("source adapter output must not create forecast artifacts")
    if output["controls"]["sourceIntakeAlreadyRun"] is not False:
        raise AssertionError("source adapter output must precede source intake")
    if output["execution"]["normalChecksOffline"] is not True:
        raise AssertionError("source adapter fixture must keep normal checks offline")
    if output["execution"]["liveFetchPerformed"] is not False:
        raise AssertionError("source adapter fixture must not live-fetch")
    if output["execution"]["credentialsUsed"] or output["execution"]["credentialsStored"]:
        raise AssertionError("source adapter fixture must not use or store credentials")
    if output["provenanceSummary"]["rawRowsIncluded"] is not False:
        raise AssertionError("source adapter output must not include raw rows")
    if output["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("source adapter output must not claim all evidence")

    expected_roles = {
        "weather_forecast",
        "historical_delay_baseline",
        "transit_delay_outcome",
    }
    if set(sources) != expected_roles:
        raise AssertionError("source adapter output should bind the transit delay source roles")
    if sources["weather_forecast"]["retrieval"]["availableBeforeForecastClose"] is not True:
        raise AssertionError("weather source should be available before forecast close")
    if sources["historical_delay_baseline"]["positiveOutcomeCount"] != 7:
        raise AssertionError("history source should expose the comparable positive outcome count")
    if sources["transit_delay_outcome"]["retrieval"]["availableBeforeForecastClose"] is not False:
        raise AssertionError("outcome rows must not be marked forecast-time available")
    if sources["transit_delay_outcome"]["positiveOutcomeCount"] != 5:
        raise AssertionError("outcome source should expose late observation count as metadata")

    source_ids = {item["sourceId"] for item in manifest["sources"]}
    for item in mapping["mappings"]:
        if item["sourceId"] not in source_ids:
            raise AssertionError("field mapping references an unknown source")
        if item["mappingStatus"] != "confirmed" or item["requiresConfirmation"]:
            raise AssertionError("fixture mappings should be confirmed")

    if mapping["sourceManifestId"] != manifest["sourceManifestId"]:
        raise AssertionError("field mapping should bind the embedded manifest")
    if output["nextAction"] != "run_source_intake":
        raise AssertionError("confirmed source adapter output should route to source intake")

    print("checked source adapter output invariants")


if __name__ == "__main__":
    main()
