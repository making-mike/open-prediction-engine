#!/usr/bin/env python3
"""Generate checked MVP method options for weather-transit-delay forecasts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_transit_baseline_track_record_gate import OUTPUT_PATH as TRACK_GATE_PATH
from generate_transit_baseline_track_record_gate import build_gate
from generate_transit_forward_run_corpus import OUTPUT_PATH as CORPUS_PATH
from generate_transit_forward_run_corpus import build_corpus
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-method-options"
OUTPUT_PATH = GENERATED / "transit-method-options.generated.json"
SCHEMA = SPEC / "transit-method-options.schema.json"
GENERATED_AT = "2026-05-27T15:00:00Z"

BASELINE_METHOD_ID = "transitmethod-100"
WEATHER_ADJUSTMENT_METHOD_ID = "transitmethod-101"
HISTORICAL_CONDITIONED_METHOD_ID = "transitmethod-201"
TRAINED_ML_METHOD_ID = "transitmethod-301"
RETRIEVAL_METHOD_ID = "transitmethod-401"
ENSEMBLE_METHOD_ID = "transitmethod-501"
EXTERNAL_REFERENCE_METHOD_ID = "transitmethod-601"


class TransitMethodOptionsError(Exception):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def round_float(value: float) -> float:
    return round(value, 10)


def method_option(
    *,
    method_id: str,
    method_class: str,
    method_kind: str,
    status: str,
    selection_eligibility: str,
    benchmark_status: str,
    sample_size: int,
    minimum_required: int,
    source_evidence_status: str,
    leakage_status: str,
    same_window_outcome: bool,
    rejection_reasons: list[str],
    primary_score: float | None = None,
    baseline_score: float | None = None,
    baseline_lift: float | None = None,
) -> dict[str, Any]:
    option: dict[str, Any] = {
        "methodId": method_id,
        "methodClass": method_class,
        "methodKind": method_kind,
        "status": status,
        "selectionEligibility": selection_eligibility,
        "benchmarkStatus": benchmark_status,
        "sampleSize": sample_size,
        "minimumComparableResolvedRequired": minimum_required,
        "sourceEvidenceStatus": source_evidence_status,
        "leakageStatus": leakage_status,
        "sameWindowOutcomeUsedAsForecastEvidence": same_window_outcome,
        "rejectionReasons": rejection_reasons,
    }
    if primary_score is not None:
        option["primaryScore"] = round_float(primary_score)
    if baseline_score is not None:
        option["baselineScore"] = round_float(baseline_score)
    if baseline_lift is not None:
        option["baselineLift"] = round_float(baseline_lift)
    return option


def build_options() -> dict[str, Any]:
    corpus = build_corpus()
    gate = build_gate()
    samples = gate["sampleSummary"]
    track = gate["trackRecordSummary"]
    policy = corpus["comparableWindowPolicy"]
    resolved = samples["resolvedComparableSampleSize"]
    minimum_selection = samples["minimumComparableResolvedForTrackRecord"]
    baseline_score = track["baselineScore"]
    candidate_score = track["primaryScore"]
    candidate_lift = track["baselineLift"]
    method_options = [
        method_option(
            method_id=BASELINE_METHOD_ID,
            method_class="baseline",
            method_kind="historical_frequency_baseline",
            status="enabled",
            selection_eligibility="eligible_default",
            benchmark_status="baseline_reference",
            sample_size=resolved,
            minimum_required=0,
            source_evidence_status="available_forecast_time_only",
            leakage_status="passed_fixture_boundary",
            same_window_outcome=False,
            rejection_reasons=[],
            primary_score=baseline_score,
            baseline_score=baseline_score,
            baseline_lift=0.0,
        ),
        method_option(
            method_id=WEATHER_ADJUSTMENT_METHOD_ID,
            method_class="deterministic_statistical",
            method_kind="transparent_weather_adjustment",
            status="evidence_only",
            selection_eligibility="rejected",
            benchmark_status="benchmarked_fixture_only",
            sample_size=resolved,
            minimum_required=minimum_selection,
            source_evidence_status="available_forecast_time_only",
            leakage_status="passed_fixture_boundary",
            same_window_outcome=False,
            rejection_reasons=[
                "resolved_comparable_sample_below_threshold",
                "quality_claim_blocked",
                "baseline_only_default_for_early_corpus_runs",
            ],
            primary_score=candidate_score,
            baseline_score=baseline_score,
            baseline_lift=candidate_lift,
        ),
        method_option(
            method_id=HISTORICAL_CONDITIONED_METHOD_ID,
            method_class="model_assisted",
            method_kind="historical_conditioned_statistical",
            status="proposed",
            selection_eligibility="proposed_only",
            benchmark_status="not_benchmarked",
            sample_size=resolved,
            minimum_required=samples["minimumComparableResolvedForCalibration"],
            source_evidence_status="insufficient_corpus",
            leakage_status="not_checked",
            same_window_outcome=False,
            rejection_reasons=[
                "insufficient_weather_weekday_season_window_buckets",
                "benchmark_missing",
                "method_not_enabled",
            ],
        ),
        method_option(
            method_id=TRAINED_ML_METHOD_ID,
            method_class="model_assisted",
            method_kind="trained_ml",
            status="proposed",
            selection_eligibility="proposed_only",
            benchmark_status="not_benchmarked",
            sample_size=0,
            minimum_required=samples["minimumComparableResolvedForCalibration"],
            source_evidence_status="not_implemented",
            leakage_status="not_checked",
            same_window_outcome=False,
            rejection_reasons=["clean_benchmark_missing", "method_not_enabled"],
        ),
        method_option(
            method_id=RETRIEVAL_METHOD_ID,
            method_class="retrieval_assisted",
            method_kind="retrieval_assisted",
            status="proposed",
            selection_eligibility="proposed_only",
            benchmark_status="not_benchmarked",
            sample_size=0,
            minimum_required=minimum_selection,
            source_evidence_status="not_implemented",
            leakage_status="not_checked",
            same_window_outcome=False,
            rejection_reasons=["retrieval_policy_missing", "clean_benchmark_missing", "method_not_enabled"],
        ),
        method_option(
            method_id=ENSEMBLE_METHOD_ID,
            method_class="ensemble",
            method_kind="ensemble",
            status="proposed",
            selection_eligibility="proposed_only",
            benchmark_status="not_benchmarked",
            sample_size=0,
            minimum_required=minimum_selection,
            source_evidence_status="not_implemented",
            leakage_status="not_checked",
            same_window_outcome=False,
            rejection_reasons=["component_methods_not_eligible", "clean_benchmark_missing", "method_not_enabled"],
        ),
        method_option(
            method_id=EXTERNAL_REFERENCE_METHOD_ID,
            method_class="external_reference",
            method_kind="external_reference",
            status="proposed",
            selection_eligibility="proposed_only",
            benchmark_status="not_benchmarked",
            sample_size=0,
            minimum_required=minimum_selection,
            source_evidence_status="not_implemented",
            leakage_status="not_checked",
            same_window_outcome=False,
            rejection_reasons=["external_provider_policy_missing", "clean_benchmark_missing", "method_not_enabled"],
        ),
    ]
    options = {
        "transitMethodOptionsId": "transitmethodoptions-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "optionsMode": "checked_fixture_method_options",
        "sourceBindings": {
            "transitForwardRunCorpusId": corpus["transitForwardRunCorpusId"],
            "transitBaselineTrackRecordGateId": gate["transitBaselineTrackRecordGateId"],
            "corpusPath": rel(CORPUS_PATH),
            "trackRecordGatePath": rel(TRACK_GATE_PATH),
        },
        "defaultSelection": {
            "baselineOnlyDefault": True,
            "selectedMethodId": BASELINE_METHOD_ID,
            "selectedMethodClass": "baseline",
            "selectionStatus": "baseline_selected",
            "reasonCode": "insufficient_comparable_method_evidence",
            "selectionReason": "Use the historical-frequency baseline until a non-baseline method has enough comparable resolved transit windows and clean anti-leakage evidence.",
        },
        "corpusEvidence": {
            "resolvedComparableSampleSize": resolved,
            "excludedSampleSize": samples["excludedSampleSize"],
            "minimumComparableResolvedForTrackRecord": samples["minimumComparableResolvedForTrackRecord"],
            "minimumComparableResolvedForCalibration": samples["minimumComparableResolvedForCalibration"],
            "minimumComparableResolvedForNonBaselineSelection": minimum_selection,
            "trackRecordStatus": samples["trackRecordStatus"],
            "calibrationStatus": samples["calibrationStatus"],
        },
        "methodComparison": {
            "comparisonStatus": "below_threshold_evidence_only",
            "scoringRule": "brier",
            "higherIsBetter": False,
            "baselineScore": baseline_score,
            "bestCandidateScore": candidate_score,
            "bestCandidateBaselineLift": candidate_lift,
            "sameWindowOutcomeUsedAsForecastEvidence": False,
            "forecastTimeEvidenceRoles": policy["forecastTimeEvidenceMayInclude"],
            "resolutionOnlyEvidenceRoles": policy["resolutionOnlyEvidenceRoles"],
            "antiLeakageStatus": "passed_fixture_boundary",
            "comparisonRows": [
                {
                    "methodId": BASELINE_METHOD_ID,
                    "methodKind": "historical_frequency_baseline",
                    "comparisonStatus": "baseline_reference",
                    "score": baseline_score,
                    "sampleSize": resolved,
                    "baselineLift": 0.0,
                },
                {
                    "methodId": WEATHER_ADJUSTMENT_METHOD_ID,
                    "methodKind": "transparent_weather_adjustment",
                    "comparisonStatus": "fixture_comparable",
                    "score": candidate_score,
                    "sampleSize": resolved,
                    "baselineLift": candidate_lift,
                },
            ],
        },
        "methodOptions": method_options,
        "claimBoundary": {
            "nonBaselineSelectionAllowed": False,
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "trainedMlAllowed": False,
            "ensembleAllowed": False,
            "retrievalAssistedAllowed": False,
            "externalReferenceAllowed": False,
            "sameWindowOutcomeAsForecastEvidenceAllowed": False,
            "normalChecksUseLiveNetwork": False,
            "liveCapturesCommitted": False,
        },
        "readSurface": {
            "command": "python3 scripts/ope.py transit-method-options",
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "selectsNonBaselineMethod": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
        },
        "warnings": [
            "This read surface explains method eligibility; it does not execute or select a new forecast method.",
            "The weather-adjustment candidate has one fixture comparison and remains evidence-only below threshold.",
            "Historical-conditioned, trained ML, retrieval-assisted, ensemble, and external-reference methods remain proposed-only.",
            "Resolution-only transit outcome rows must not become forecast-time evidence.",
        ],
    }
    validate_options(options)
    return options


def validate_options(options: dict[str, Any]) -> None:
    errors = validate_record(options, SCHEMA)
    if errors:
        raise TransitMethodOptionsError(f"transit method options schema validation failed: {errors[0]}")
    default = options["defaultSelection"]
    evidence = options["corpusEvidence"]
    comparison = options["methodComparison"]
    boundary = options["claimBoundary"]
    read_surface = options["readSurface"]
    methods = {item["methodId"]: item for item in options["methodOptions"]}
    if not default["baselineOnlyDefault"] or default["selectedMethodId"] != BASELINE_METHOD_ID:
        raise TransitMethodOptionsError("transit method options must keep the baseline as the default selection")
    if evidence["resolvedComparableSampleSize"] >= evidence["minimumComparableResolvedForNonBaselineSelection"]:
        raise TransitMethodOptionsError("fixture should remain below non-baseline selection threshold")
    deterministic = methods[WEATHER_ADJUSTMENT_METHOD_ID]
    if deterministic["status"] != "evidence_only" or deterministic["selectionEligibility"] != "rejected":
        raise TransitMethodOptionsError("weather adjustment must remain evidence-only below threshold")
    if deterministic["baselineLift"] <= 0:
        raise TransitMethodOptionsError("weather adjustment fixture should preserve positive baseline lift")
    if "resolved_comparable_sample_below_threshold" not in deterministic["rejectionReasons"]:
        raise TransitMethodOptionsError("weather adjustment rejection should cite sample threshold")
    proposed_ids = {
        HISTORICAL_CONDITIONED_METHOD_ID,
        TRAINED_ML_METHOD_ID,
        RETRIEVAL_METHOD_ID,
        ENSEMBLE_METHOD_ID,
        EXTERNAL_REFERENCE_METHOD_ID,
    }
    for method_id in proposed_ids:
        method = methods[method_id]
        if method["selectionEligibility"] != "proposed_only" or method["benchmarkStatus"] != "not_benchmarked":
            raise TransitMethodOptionsError(f"{method_id} must remain proposed-only without benchmarks")
    if comparison["sameWindowOutcomeUsedAsForecastEvidence"]:
        raise TransitMethodOptionsError("method comparison must not use same-window outcome data as forecast evidence")
    if any(method["sameWindowOutcomeUsedAsForecastEvidence"] for method in methods.values()):
        raise TransitMethodOptionsError("method options must not use same-window outcomes as forecast evidence")
    if boundary["nonBaselineSelectionAllowed"] or boundary["qualityClaimAllowed"] or boundary["calibrationClaimAllowed"]:
        raise TransitMethodOptionsError("method options must block non-baseline, quality, and calibration claims")
    if (
        boundary["trainedMlAllowed"]
        or boundary["ensembleAllowed"]
        or boundary["retrievalAssistedAllowed"]
        or boundary["externalReferenceAllowed"]
        or boundary["sameWindowOutcomeAsForecastEvidenceAllowed"]
    ):
        raise TransitMethodOptionsError("richer method families must remain disabled")
    if (
        read_surface["createsForecastArtifacts"]
        or read_surface["createsResolutionArtifacts"]
        or read_surface["createsScoringRecords"]
        or read_surface["selectsNonBaselineMethod"]
        or read_surface["fetchesLiveData"]
        or read_surface["storesCredentials"]
    ):
        raise TransitMethodOptionsError("method options read surface must be non-executing")


def write_options(options: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(options), encoding="utf-8")
    print("generated transit method options")


def check_options(options: dict[str, Any]) -> None:
    expected = render_json(options)
    if not OUTPUT_PATH.exists():
        print(f"missing transit method options: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_method_options.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"transit method options drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_method_options.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked transit method options")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        options = build_options()
        if args.write:
            write_options(options)
        elif args.check:
            check_options(options)
        else:
            sys.stdout.write(render_json(options))
    except (OSError, json.JSONDecodeError, TransitMethodOptionsError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
