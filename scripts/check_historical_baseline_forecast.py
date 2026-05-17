#!/usr/bin/env python3
"""Check the no-API historical baseline forecast path."""

from __future__ import annotations

from pathlib import Path

from ope_schema import SPEC, validate_record
from read_ope_record import read_record
from run_agent_forecast import build_summary
from run_historical_baseline_forecast import DEFAULT_REQUEST, build_outputs, output_prefix
from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    request = load_json(DEFAULT_REQUEST)
    decision = validate_request(request)
    require(decision["decisionStatus"] == "accepted", "historical-only request should be accepted")
    require(decision["auditLog"]["dataMode"] == "provided", "historical-only request should preserve provided mode")
    require(decision["auditLog"]["sourcePolicyId"] == "sourcepolicy-701", "historical request should bind source policy")

    outputs = build_outputs(DEFAULT_REQUEST)
    prefix = output_prefix()
    pipeline_run = outputs[f"{prefix}-pipeline-run.generated.json"]
    feature_snapshot = outputs[f"{prefix}-feature-snapshot.generated.json"]
    evidence = outputs[f"{prefix}-evidence.generated.json"]
    artifact = outputs[f"{prefix}-artifact.generated.json"]
    history = outputs[f"{prefix}-history.generated.json"]

    for filename, schema_name in {
        f"{prefix}-pipeline-run.generated.json": "pipeline-run.schema.json",
        f"{prefix}-question.generated.json": "forecast-question.schema.json",
        f"{prefix}-evidence.generated.json": "evidence-packet.schema.json",
        f"{prefix}-artifact.generated.json": "forecast-artifact.schema.json",
        f"{prefix}-history.generated.json": "forecast-history.schema.json",
    }.items():
        errors = validate_record(outputs[filename], SPEC / schema_name)
        require(not errors, f"{filename} should validate against {schema_name}: {errors[:1]}")

    require(artifact["forecastId"] == "forecast-702", "historical artifact should use forecast-702")
    require(artifact["forecastOutput"]["probability"] == 0.22, "historical forecast should expose 0.22")
    require(artifact["forecastOutput"] == artifact["baselineForecast"], "historical forecast should equal baseline")
    require(evidence["forecastOutput"] == evidence["baselineForecast"], "historical evidence should equal baseline")
    require(evidence["inputSourceClasses"] == ["internal_dataset"], "historical evidence should use internal dataset only")
    require(len(evidence["provenanceReferences"]) == 1, "historical evidence should have one provenance source")
    require(
        evidence["provenanceReferences"][0]["sourceId"] == "source-103",
        "historical evidence should bind baseline history source",
    )
    require(
        "forecastDailyPrecipitationMm" not in feature_snapshot["features"],
        "historical-only feature snapshot must not include weather forecast data",
    )
    require(feature_snapshot["features"]["forecastSignalUsed"] is False, "historical path should flag no forecast signal")
    require(pipeline_run["controls"]["sourceMode"] == "committed_fixture", "historical pipeline should use committed fixture")
    require(pipeline_run["controls"]["networkAccess"] is False, "historical pipeline should not use network")
    require(pipeline_run["controls"]["liveFetch"] is False, "historical pipeline should not live-fetch")
    require(history["entries"][0]["sourceClass"] == "baseline", "historical history should be baseline-sourced")

    card = read_record("forecast-card", "forecast-702", "question-701")["record"]
    require(card["forecast"]["probability"] == 0.22, "historical forecast card should expose 0.22")
    require(card["forecast"] == card["baseline"], "historical forecast card should show baseline equality")
    require(card["links"]["evidenceTrace"] is None, "historical card should not link an auto-evidence trace")
    require(card["requestBinding"]["sourceMode"] == "committed_fixture", "historical card should bind source mode")

    summary = build_summary(DEFAULT_REQUEST)
    require(summary["runStatus"] == "completed", "historical forecast-run should complete")
    require(summary["sourceMode"] == "committed_fixture", "historical forecast-run should use committed fixture")
    require(summary["recordBinding"]["forecastId"] == "forecast-702", "historical forecast-run should bind forecast")
    require(summary["forecast"]["probability"] == 0.22, "historical forecast-run should expose 0.22")
    require(summary["forecast"]["probability"] == summary["forecast"]["baselineProbability"], "forecast-run should show baseline equality")
    require(summary["outputs"]["evidenceTrace"] is None, "historical forecast-run should not expose evidence trace")
    require(summary["outputs"]["resolutionStatus"] is None, "historical forecast-run should not claim resolution")

    print("checked historical baseline forecast path")


if __name__ == "__main__":
    main()
