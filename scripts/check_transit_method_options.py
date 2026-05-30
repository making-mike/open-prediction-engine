#!/usr/bin/env python3
"""Check public transport MVP method options and boundaries."""

from __future__ import annotations

from generate_transit_method_options import (
    BASELINE_METHOD_ID,
    ENSEMBLE_METHOD_ID,
    EXTERNAL_REFERENCE_METHOD_ID,
    HISTORICAL_CONDITIONED_METHOD_ID,
    RETRIEVAL_METHOD_ID,
    TRAINED_ML_METHOD_ID,
    WEATHER_ADJUSTMENT_METHOD_ID,
    build_options,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    options = build_options()
    default = options["defaultSelection"]
    evidence = options["corpusEvidence"]
    comparison = options["methodComparison"]
    methods = {item["methodId"]: item for item in options["methodOptions"]}
    boundary = options["claimBoundary"]
    read_surface = options["readSurface"]

    require(options["optionsMode"] == "checked_fixture_method_options", "options should be fixture method options")
    require(default["baselineOnlyDefault"] is True, "baseline should remain the default")
    require(default["selectedMethodId"] == BASELINE_METHOD_ID, "default selection should be transit baseline")
    require(default["selectionStatus"] == "baseline_selected", "selection status should be baseline selected")
    require(
        default["reasonCode"] == "insufficient_comparable_method_evidence",
        "baseline selection should cite insufficient method evidence",
    )
    require(evidence["resolvedComparableSampleSize"] == 1, "method options should see one comparable run")
    require(evidence["excludedSampleSize"] == 6, "method options should see six excluded runs")
    require(evidence["minimumComparableResolvedForNonBaselineSelection"] == 30, "non-baseline threshold should be 30")
    require(evidence["trackRecordStatus"] == "not_enough_resolved_comparable_outcomes", "track record should be below threshold")
    require(evidence["calibrationStatus"] == "not_enough_resolved_comparable_outcomes", "calibration should be below threshold")

    baseline = methods[BASELINE_METHOD_ID]
    require(baseline["methodKind"] == "historical_frequency_baseline", "baseline kind should be historical frequency")
    require(baseline["selectionEligibility"] == "eligible_default", "baseline should be eligible by default")
    require(baseline["benchmarkStatus"] == "baseline_reference", "baseline should be a reference")

    deterministic = methods[WEATHER_ADJUSTMENT_METHOD_ID]
    require(deterministic["methodKind"] == "transparent_weather_adjustment", "weather adjustment method should be transparent")
    require(deterministic["status"] == "evidence_only", "weather adjustment should be evidence-only")
    require(deterministic["selectionEligibility"] == "rejected", "weather adjustment should be rejected below threshold")
    require(deterministic["benchmarkStatus"] == "benchmarked_fixture_only", "weather adjustment should expose fixture benchmark only")
    require(deterministic["sampleSize"] == 1, "weather adjustment should expose one sample")
    require(deterministic["primaryScore"] == 0.4489, "weather adjustment should expose fixture Brier score")
    require(deterministic["baselineScore"] == 0.5625, "weather adjustment should expose baseline score")
    require(deterministic["baselineLift"] == 0.1136, "weather adjustment should expose baseline lift")
    require(
        "resolved_comparable_sample_below_threshold" in deterministic["rejectionReasons"],
        "weather adjustment should cite below-threshold sample",
    )
    require(
        deterministic["sameWindowOutcomeUsedAsForecastEvidence"] is False,
        "weather adjustment must not use same-window outcome as forecast evidence",
    )

    proposed_ids = {
        HISTORICAL_CONDITIONED_METHOD_ID,
        TRAINED_ML_METHOD_ID,
        RETRIEVAL_METHOD_ID,
        ENSEMBLE_METHOD_ID,
        EXTERNAL_REFERENCE_METHOD_ID,
    }
    for method_id in proposed_ids:
        method = methods[method_id]
        require(method["status"] == "proposed", f"{method_id} should remain proposed")
        require(method["selectionEligibility"] == "proposed_only", f"{method_id} should be proposed-only")
        require(method["benchmarkStatus"] == "not_benchmarked", f"{method_id} should not have benchmark evidence")
        require(not method["sameWindowOutcomeUsedAsForecastEvidence"], f"{method_id} must not use outcome evidence")

    historical = methods[HISTORICAL_CONDITIONED_METHOD_ID]
    require(
        historical["sourceEvidenceStatus"] == "insufficient_corpus",
        "historical-conditioned method should wait for bucketed corpus evidence",
    )
    require(
        historical["minimumComparableResolvedRequired"] == 100,
        "historical-conditioned method should require enough bucketed outcomes",
    )

    require(comparison["comparisonStatus"] == "below_threshold_evidence_only", "comparison should be evidence-only below threshold")
    require(comparison["scoringRule"] == "brier", "method comparison should use Brier score")
    require(comparison["higherIsBetter"] is False, "Brier comparison should be lower-is-better")
    require(comparison["baselineScore"] == 0.5625, "comparison should expose baseline score")
    require(comparison["bestCandidateScore"] == 0.4489, "comparison should expose best candidate score")
    require(comparison["bestCandidateBaselineLift"] == 0.1136, "comparison should expose best candidate lift")
    require(
        comparison["sameWindowOutcomeUsedAsForecastEvidence"] is False,
        "comparison must not use same-window outcome as forecast evidence",
    )
    require("trip_updates_after_window" in comparison["resolutionOnlyEvidenceRoles"], "comparison should preserve resolution-only roles")
    require("weather_forecast" in comparison["forecastTimeEvidenceRoles"], "comparison should preserve forecast-time roles")

    require(boundary["nonBaselineSelectionAllowed"] is False, "non-baseline selection should be blocked")
    require(boundary["qualityClaimAllowed"] is False, "quality claims should be blocked")
    require(boundary["calibrationClaimAllowed"] is False, "calibration claims should be blocked")
    require(boundary["trainedMlAllowed"] is False, "trained ML should be blocked")
    require(boundary["ensembleAllowed"] is False, "ensembles should be blocked")
    require(boundary["retrievalAssistedAllowed"] is False, "retrieval-assisted methods should be blocked")
    require(boundary["externalReferenceAllowed"] is False, "external-reference methods should be blocked")
    require(
        boundary["sameWindowOutcomeAsForecastEvidenceAllowed"] is False,
        "same-window outcome must not be allowed as forecast evidence",
    )
    require(boundary["normalChecksUseLiveNetwork"] is False, "normal checks should stay offline")
    require(boundary["liveCapturesCommitted"] is False, "live captures should stay local")

    require(not read_surface["createsForecastArtifacts"], "method options must not create forecasts")
    require(not read_surface["createsResolutionArtifacts"], "method options must not create resolutions")
    require(not read_surface["createsScoringRecords"], "method options must not create scores")
    require(not read_surface["selectsNonBaselineMethod"], "method options must not select a non-baseline method")
    require(not read_surface["fetchesLiveData"], "method options must not fetch live data")
    require(not read_surface["storesCredentials"], "method options must not store credentials")
    print("checked transit method options")


if __name__ == "__main__":
    main()
