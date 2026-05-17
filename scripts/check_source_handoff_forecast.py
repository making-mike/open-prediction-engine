#!/usr/bin/env python3
"""Check explicit source-handoff setup forecast execution boundaries."""

from __future__ import annotations

from read_ope_record import read_record
from run_source_handoff_forecast import build_outputs, output_prefix


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_for(outputs: dict[str, dict], case: str) -> dict:
    return outputs[f"{output_prefix(case)}-setup-forecast-run.generated.json"]


def artifact_for(outputs: dict[str, dict], case: str) -> dict:
    return outputs[f"{output_prefix(case)}-artifact.generated.json"]


def evidence_for(outputs: dict[str, dict], case: str) -> dict:
    return outputs[f"{output_prefix(case)}-evidence.generated.json"]


def main() -> None:
    outputs = build_outputs()
    confirmed = run_for(outputs, "confirmed_builder_draft")
    unconfirmed = run_for(outputs, "unconfirmed_builder_draft")
    insufficient = run_for(outputs, "insufficient_confirmed_builder_draft")

    require(confirmed["runStatus"] == "generated", "confirmed handoff should generate explicit setup forecast")
    require(confirmed["sourceIntakeHandoffId"] == "sourceintakehandoff-002", "confirmed run should bind source intake handoff")
    require(confirmed["sourceHandoffMethodGateId"] == "sourcehandoffmethodgate-002", "confirmed run should bind handoff method gate")
    require(confirmed["sourceIntakeReportId"] == "sourceintakereport-102", "confirmed run should bind handoff source intake report")
    require(confirmed["setupMethodDecisionId"] == "setupmethoddecision-102", "confirmed run should bind handoff method decision")
    require(confirmed["setupBenchmarkGateId"] == "setupbenchmarkgate-102", "confirmed run should bind handoff benchmark gate")
    require(confirmed["selectedMethodClass"] == "deterministic_statistical", "confirmed run should select deterministic method")
    require(confirmed["sourceMode"] == "source_handoff_fixture", "confirmed run should use source handoff fixture mode")
    require(confirmed["controls"]["forecastArtifactsCreated"] is True, "confirmed run should create artifacts")
    require(confirmed["controls"]["networkAccess"] is False, "confirmed run must not use network")
    require(confirmed["controls"]["liveFetch"] is False, "confirmed run must not live-fetch")
    require(confirmed["controls"]["localLiveDraftConsumed"] is False, "confirmed run must not use local live drafts")

    artifact = artifact_for(outputs, "confirmed_builder_draft")
    evidence = evidence_for(outputs, "confirmed_builder_draft")
    require(artifact["forecastId"] == "forecast-1102", "confirmed handoff forecast should use forecast-1102")
    require(artifact["forecastOutput"]["probability"] > artifact["baselineForecast"]["probability"], "deterministic handoff forecast should exceed baseline")
    require(evidence["forecastId"] == artifact["forecastId"], "evidence should bind handoff forecast")
    require(
        {source["sourceType"] for source in evidence["provenanceReferences"]} == {"internal_dataset", "public_dataset"},
        "confirmed handoff forecast should use baseline and forecast-time weather provenance",
    )
    require(
        not any(source["sourceId"] == artifact["resolutionPlan"]["primaryResolutionSource"]["sourceId"] for source in evidence["provenanceReferences"]),
        "confirmed handoff forecast provenance must exclude resolution source",
    )

    require(unconfirmed["runStatus"] == "blocked", "unconfirmed handoff should block")
    require(unconfirmed["recordBinding"]["forecastId"] is None, "unconfirmed handoff must not bind forecast")
    require("mapping_confirmation_required" in unconfirmed["blockedReasons"], "unconfirmed handoff should explain mapping confirmation")
    require("source_intake_needs_confirmation" in unconfirmed["blockedReasons"], "unconfirmed handoff should explain source intake status")

    require(insufficient["runStatus"] == "blocked", "insufficient handoff should block")
    require(insufficient["recordBinding"]["forecastId"] is None, "insufficient handoff must not bind forecast")
    require("more_data_required" in insufficient["blockedReasons"], "insufficient handoff should ask for more data")
    require("source_intake_rejected" in insufficient["blockedReasons"], "insufficient handoff should preserve rejected intake")

    for case in ("contains_secret", "unsupported_format", "oversized", "leakage"):
        run = run_for(outputs, case)
        require(run["runStatus"] == "blocked", f"{case} should block")
        require(run["sourceIntakeReportId"] is None, f"{case} should not bind source intake")
        require(run["setupMethodDecisionId"] is None, f"{case} should not bind method decision")
        require(run["setupBenchmarkGateId"] is None, f"{case} should not bind benchmark gate")
        require(run["recordBinding"]["forecastId"] is None, f"{case} should not bind forecast")
        require(run["controls"]["forecastArtifactsCreated"] is False, f"{case} should not create artifacts")
        require("builder_rejection" in run["blockedReasons"], f"{case} should explain builder rejection")

    card_response = read_record("forecast-card", "forecast-1102", "question-1102")
    card = card_response["record"]
    setup = card["setupBinding"]
    require(setup["setupForecastRunId"] == "setupforecastrun-1102", "forecast card should bind handoff setup run")
    require(setup["sourceIntakeHandoffId"] == "sourceintakehandoff-002", "forecast card should expose handoff binding")
    require(setup["sourceHandoffMethodGateId"] == "sourcehandoffmethodgate-002", "forecast card should expose method gate binding")
    require(setup["setupBenchmarkGateId"] == "setupbenchmarkgate-102", "forecast card should expose handoff benchmark gate")
    require(card["links"]["evidenceTrace"] is None, "handoff setup forecast should not expose connector evidence trace")

    print("checked source-handoff setup forecast execution")


if __name__ == "__main__":
    main()
