#!/usr/bin/env python3
"""Generate the weather-transit-delay baseline track-record and calibration gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_transit_forward_run_corpus import OUTPUT_PATH as CORPUS_PATH
from generate_transit_forward_run_corpus import build_corpus
from ope_schema import SPEC, validate_record
from ope_scoring import calibration_buckets, track_record_summary
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-baseline-track-record-gate"
OUTPUT_PATH = GENERATED / "transit-baseline-track-record-gate.generated.json"
SCHEMA = SPEC / "transit-baseline-track-record-gate.schema.json"
GENERATED_AT = "2026-05-27T14:00:00Z"


class TransitBaselineTrackRecordGateError(Exception):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def round_float(value: float | None) -> float:
    if value is None:
        return 0.0
    return round(value, 10)


def expected_calibration_error(buckets: list[dict[str, Any]], sample_size: int) -> float:
    if sample_size == 0:
        return 0.0
    total = 0.0
    for bucket in buckets:
        total += (
            bucket["count"]
            / sample_size
            * abs(bucket["meanForecastProbability"] - bucket["observedFrequency"])
        )
    return total


def status_for(sample_size: int, minimum: int) -> str:
    if sample_size >= minimum:
        return "ready"
    return "not_enough_resolved_comparable_outcomes"


def score_rows(corpus: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in corpus["comparableRuns"]:
        score = run["scoreBinding"]
        forecast = run["forecastBinding"]
        resolution = run["resolutionBinding"]
        rows.append(
            {
                "corpusRunId": run["corpusRunId"],
                "forwardRunId": run["forwardRunId"],
                "forecastId": forecast["forecastId"],
                "questionId": forecast["questionId"],
                "serviceDate": run["serviceDate"],
                "outcomeLabel": resolution["outcomeLabel"],
                "primaryScore": score["primaryScore"],
                "baselineScore": score["baselineScore"],
                "baselineLift": score["baselineLift"],
            }
        )
    return rows


def maybe_calibration_summary(corpus: dict[str, Any], status: str) -> dict[str, Any] | None:
    if status != "ready":
        return None

    pairs: list[tuple[float, bool]] = []
    for run in corpus["comparableRuns"]:
        paths = run["artifactPaths"]
        artifact = load_json(ROOT / paths["forecastArtifactPath"])
        resolution = load_json(ROOT / paths["resolutionRecordPath"])
        pairs.append((artifact["forecastOutput"]["probability"], bool(resolution["resolvedOutcome"]["value"])))

    buckets = calibration_buckets(pairs, bucket_count=10)
    starts = [run["forecastBinding"]["horizonStart"] for run in corpus["comparableRuns"]]
    ends = [run["resolutionBinding"]["resolvedAt"] for run in corpus["comparableRuns"]]
    return {
        "calibrationSummaryId": "calibration-1201",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "horizonBucket": "same-day-morning-peak",
        "outputType": "binary",
        "coveragePeriod": {
            "startsAt": min(starts),
            "endsAt": max(ends),
        },
        "sampleSize": len(pairs),
        "expectedCalibrationError": round_float(expected_calibration_error(buckets, len(pairs))),
        "buckets": [
            {
                "lowerProbability": round_float(bucket["lowerProbability"]),
                "upperProbability": round_float(bucket["upperProbability"]),
                "count": bucket["count"],
                "meanForecastProbability": round_float(bucket["meanForecastProbability"]),
                "observedFrequency": round_float(bucket["observedFrequency"]),
            }
            for bucket in buckets
        ],
    }


def build_gate() -> dict[str, Any]:
    corpus = build_corpus()
    comparable_runs = corpus["comparableRuns"]
    excluded_runs = corpus["excludedRuns"]
    summary = corpus["summary"]
    policy = corpus["comparableWindowPolicy"]
    minimum_track_record = policy["minimumComparableResolvedForTrackRecord"]
    minimum_calibration = policy["minimumComparableResolvedForCalibration"]
    resolved_sample_size = summary["comparableResolvedCount"]
    track_record_status = status_for(resolved_sample_size, minimum_track_record)
    calibration_status = status_for(resolved_sample_size, minimum_calibration)
    rows = score_rows(corpus)
    scores = [row["primaryScore"] for row in rows]
    baseline_scores = [row["baselineScore"] for row in rows]
    excluded_reasons = [run["exclusionReason"] for run in excluded_runs]
    performance = track_record_summary(
        domain="weather-transit-delays",
        horizon_bucket="same-day-morning-peak",
        output_type="binary",
        scoring_rule="brier",
        scores=scores,
        baseline_scores=baseline_scores,
        n_ambiguous=excluded_reasons.count("ambiguous"),
        n_annulled=excluded_reasons.count("annulled"),
        n_forecasts=summary["corpusCount"],
    )
    horizon_starts = [run["forecastBinding"]["horizonStart"] for run in comparable_runs]
    horizon_ends = [run["forecastBinding"]["horizonEnd"] for run in comparable_runs]
    calibration_summary = maybe_calibration_summary(corpus, calibration_status)
    gate = {
        "transitBaselineTrackRecordGateId": "transitbaselinetrackrecordgate-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "gateMode": "checked_fixture_gate",
        "sourceCorpus": {
            "transitForwardRunCorpusId": corpus["transitForwardRunCorpusId"],
            "corpusPath": rel(CORPUS_PATH),
            "corpusMode": corpus["corpusMode"],
            "policyId": policy["policyId"],
            "sourceCommand": "python3 scripts/ope.py transit-forward-run-corpus",
        },
        "coverageSummary": {
            "network": corpus["corpusScope"]["network"],
            "geography": corpus["corpusScope"]["geography"],
            "serviceWindow": corpus["corpusScope"]["serviceWindow"],
            "horizonWindowCoverage": {
                "horizonStartsAt": min(horizon_starts),
                "horizonEndsAt": max(horizon_ends),
                "comparableWindowCount": len(comparable_runs),
                "excludedWindowCount": len(excluded_runs),
                "comparableServiceDates": sorted(run["serviceDate"] for run in comparable_runs),
                "excludedServiceDates": sorted(run["serviceDate"] for run in excluded_runs),
            },
        },
        "sampleSummary": {
            "resolvedComparableSampleSize": resolved_sample_size,
            "scoredSampleSize": summary["scoredCount"],
            "excludedSampleSize": summary["excludedCount"],
            "pendingSampleSize": summary["pendingCount"],
            "minimumComparableResolvedForTrackRecord": minimum_track_record,
            "minimumComparableResolvedForCalibration": minimum_calibration,
            "trackRecordStatus": track_record_status,
            "calibrationStatus": calibration_status,
        },
        "trackRecordSummary": {
            "summaryGenerated": True,
            "status": track_record_status,
            "scoringRule": "brier",
            "higherIsBetter": False,
            "primaryScore": round_float(performance["summary"]["primaryScore"]),
            "baselineScore": round_float(performance["summary"]["baselineScore"]),
            "baselineLift": round_float(performance["summary"]["baselineLift"]),
            "resolvedSampleSize": resolved_sample_size,
            "excludedSampleSize": summary["excludedCount"],
            "scoreRows": rows,
        },
        "calibrationGate": {
            "summaryGenerated": calibration_summary is not None,
            "status": calibration_status,
            "reasonCode": "threshold_met" if calibration_summary is not None else calibration_status,
            "minimumComparableResolved": minimum_calibration,
            "resolvedComparableSampleSize": resolved_sample_size,
            "calibrationSummary": calibration_summary,
        },
        "claimBoundary": {
            "qualityClaimAllowed": track_record_status == "ready",
            "baselineTrackRecordAllowed": track_record_status == "ready",
            "calibrationClaimAllowed": calibration_status == "ready",
            "reasonCode": "threshold_met" if track_record_status == "ready" else track_record_status,
            "oneOffForwardRunCanCreateCalibrationEvidence": False,
            "normalChecksUseLiveNetwork": False,
            "liveCapturesCommitted": False,
        },
        "readSurface": {
            "command": "python3 scripts/ope.py transit-track-record-gate",
            "sourceCommand": "python3 scripts/ope.py transit-forward-run-corpus",
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "createsCalibrationSummariesBelowThreshold": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
        },
        "warnings": [
            "This gate reads the checked forward-run corpus and does not execute new forecasts, resolutions, or scores.",
            "One comparable scored transit run is implementation evidence, not a baseline track record or calibration claim.",
            "Calibration summaries are withheld until the declared comparable resolved sample threshold is met.",
            "Excluded corpus rows are audit evidence and do not count toward resolved comparable samples.",
        ],
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    errors = validate_record(gate, SCHEMA)
    if errors:
        raise TransitBaselineTrackRecordGateError(f"transit baseline track-record gate schema validation failed: {errors[0]}")
    samples = gate["sampleSummary"]
    track_summary = gate["trackRecordSummary"]
    calibration_gate = gate["calibrationGate"]
    boundary = gate["claimBoundary"]
    read_surface = gate["readSurface"]
    if track_summary["resolvedSampleSize"] != samples["resolvedComparableSampleSize"]:
        raise TransitBaselineTrackRecordGateError("track-record sample size must match resolved comparable sample size")
    if len(track_summary["scoreRows"]) != samples["scoredSampleSize"]:
        raise TransitBaselineTrackRecordGateError("track-record score rows must match scored sample size")
    if samples["resolvedComparableSampleSize"] < samples["minimumComparableResolvedForTrackRecord"]:
        if samples["trackRecordStatus"] != "not_enough_resolved_comparable_outcomes":
            raise TransitBaselineTrackRecordGateError("below-threshold track-record status must be explicit")
        if boundary["baselineTrackRecordAllowed"] or boundary["qualityClaimAllowed"]:
            raise TransitBaselineTrackRecordGateError("below-threshold gate must block quality and track-record claims")
    if samples["resolvedComparableSampleSize"] < samples["minimumComparableResolvedForCalibration"]:
        if samples["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
            raise TransitBaselineTrackRecordGateError("below-threshold calibration status must be explicit")
        if calibration_gate["summaryGenerated"] or calibration_gate["calibrationSummary"] is not None:
            raise TransitBaselineTrackRecordGateError("below-threshold gate must not generate calibration summaries")
        if boundary["calibrationClaimAllowed"]:
            raise TransitBaselineTrackRecordGateError("below-threshold gate must block calibration claims")
    if boundary["oneOffForwardRunCanCreateCalibrationEvidence"]:
        raise TransitBaselineTrackRecordGateError("one-off forward runs must not create calibration evidence")
    if (
        read_surface["createsForecastArtifacts"]
        or read_surface["createsResolutionArtifacts"]
        or read_surface["createsScoringRecords"]
        or read_surface["createsCalibrationSummariesBelowThreshold"]
        or read_surface["fetchesLiveData"]
        or read_surface["storesCredentials"]
    ):
        raise TransitBaselineTrackRecordGateError("track-record gate read surface must not create artifacts or fetch data")


def write_gate(gate: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(gate), encoding="utf-8")
    print("generated transit baseline track-record gate")


def check_gate(gate: dict[str, Any]) -> None:
    expected = render_json(gate)
    if not OUTPUT_PATH.exists():
        print(f"missing transit baseline track-record gate: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_baseline_track_record_gate.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"transit baseline track-record gate drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_baseline_track_record_gate.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked transit baseline track-record gate")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        gate = build_gate()
        if args.write:
            write_gate(gate)
        elif args.check:
            check_gate(gate)
        else:
            sys.stdout.write(render_json(gate))
    except (OSError, json.JSONDecodeError, TransitBaselineTrackRecordGateError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
