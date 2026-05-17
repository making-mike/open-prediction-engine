#!/usr/bin/env python3
"""Check setup-aware forecast execution boundaries."""

from __future__ import annotations

from run_setup_forecast import build_outputs, output_prefix


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

    accepted = run_for(outputs, "accepted")
    partial = run_for(outputs, "accepted_partial")
    needs = run_for(outputs, "needs_confirmation")
    rejected = run_for(outputs, "rejected")

    require(accepted["runStatus"] == "generated", "accepted setup forecast should generate")
    require(partial["runStatus"] == "generated", "accepted_partial setup forecast should generate")
    require(needs["runStatus"] == "blocked", "needs_confirmation setup forecast should block")
    require(rejected["runStatus"] == "blocked", "rejected setup forecast should block")

    for case, run in {"accepted": accepted, "accepted_partial": partial}.items():
        require(run["controls"]["networkAccess"] is False, f"{case} must not use network")
        require(run["controls"]["liveFetch"] is False, f"{case} must not live-fetch")
        require(run["controls"]["localLiveDraftConsumed"] is False, f"{case} must not consume local live drafts")
        require(run["controls"]["forecastArtifactsCreated"] is True, f"{case} should create artifacts")

        artifact = artifact_for(outputs, case)
        evidence = evidence_for(outputs, case)
        require(artifact["forecastId"] == run["recordBinding"]["forecastId"], f"{case} run should bind forecast")
        require(evidence["evidencePacketId"] == run["recordBinding"]["evidencePacketId"], f"{case} run should bind evidence")

    accepted_artifact = artifact_for(outputs, "accepted")
    accepted_evidence = evidence_for(outputs, "accepted")
    require(accepted["selectedMethodClass"] == "deterministic_statistical", "accepted should use deterministic method")
    require(accepted["selectedForecastMode"] == "deterministic_statistical", "accepted should use deterministic mode")
    require(accepted["setupBenchmarkGateId"] == "setupbenchmarkgate-001", "accepted should bind setup benchmark gate")
    require(
        accepted_artifact["forecastOutput"]["probability"] > accepted_artifact["baselineForecast"]["probability"],
        "accepted deterministic forecast should exceed baseline for heavy-rain signal",
    )
    require(
        {source["sourceType"] for source in accepted_evidence["provenanceReferences"]} == {"internal_dataset", "public_dataset"},
        "accepted deterministic forecast should use baseline and forecast-time weather provenance",
    )

    partial_artifact = artifact_for(outputs, "accepted_partial")
    partial_evidence = evidence_for(outputs, "accepted_partial")
    require(partial["selectedMethodClass"] == "historical_baseline", "partial should use historical baseline")
    require(partial["selectedForecastMode"] == "baseline_only", "partial should be baseline-only")
    require(partial["setupBenchmarkGateId"] is None, "partial baseline should not bind selected setup benchmark gate")
    require(partial_artifact["forecastOutput"] == partial_artifact["baselineForecast"], "partial forecast should equal baseline")
    require(partial_evidence["forecastOutput"] == partial_evidence["baselineForecast"], "partial evidence should equal baseline")
    require(
        all(source["sourceType"] == "internal_dataset" for source in partial_evidence["provenanceReferences"]),
        "partial setup forecast should use historical baseline provenance only",
    )

    require(accepted["sourceManifestId"] == "sourcemanifest-001", "accepted run should bind source manifest")
    require(partial["sourceIntakeReportId"] == "sourceintakereport-002", "partial run should bind source intake")
    require(
        "source_intake_needs_confirmation" in needs["blockedReasons"],
        "needs-confirmation run should explain source intake confirmation",
    )
    require(
        "source_intake_rejected" in rejected["blockedReasons"],
        "rejected run should explain source intake rejection",
    )
    for run in [needs, rejected]:
        require(run["controls"]["forecastArtifactsCreated"] is False, "blocked runs must not create artifacts")
        require(run["recordBinding"]["forecastId"] is None, "blocked runs must not bind forecast IDs")
        require(run["outputs"]["forecastArtifactPath"] is None, "blocked runs must not bind artifact paths")

    print("checked setup forecast execution")


if __name__ == "__main__":
    main()
