#!/usr/bin/env python3
"""Resolve and score the auto-evidence fixture-replay forecast."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from build_live_weather_baseline import load_json
from generate_fixture_reports import expected_calibration_error
from ope_scoring import (
    baseline_lift,
    calibration_buckets,
    score_forecast_output,
    should_exclude_resolution,
    track_record_summary,
)
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
AUTO_EVIDENCE = ROOT / "spec" / "fixtures" / "generated" / "auto-evidence"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "auto-evidence-resolution"
OPERATIONS_OUTCOME = ROOT / "spec" / "fixtures" / "live" / "weather-logistics-warsaw-2026-06-03-operations-outcome.json"
WEATHER_OBSERVATION = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-observation-response.json"
PREFIX = "weather-logistics-auto-evidence-resolution"
RESOLVED_AT = "2026-06-04T12:10:00Z"
GENERATED_AT = "2026-06-04T12:15:00Z"
MIN_CALIBRATION_SAMPLE_SIZE = 30


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 10)


def auto_evidence_path(name: str) -> Path:
    return AUTO_EVIDENCE / f"weather-logistics-auto-evidence-{name}.generated.json"


def unscorable_resolution(
    question: dict[str, Any],
    status: str,
    reason: str,
    operations: dict[str, Any],
    weather_observation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "resolutionRecordId": "resolution-601",
        "questionId": question["questionId"],
        "status": status,
        "resolvedAt": RESOLVED_AT,
        "resolutionSource": operations["sourceRef"],
        "resolutionAuthority": question["resolutionAuthority"],
        "unscorableReason": reason,
        "supportingEvidence": [
            operations["sourceRef"]["uri"],
            weather_observation["sourceRef"]["uri"],
        ],
    }


def build_resolution(
    question: dict[str, Any],
    feature_snapshot: dict[str, Any],
    operations: dict[str, Any],
    weather_observation: dict[str, Any],
) -> dict[str, Any]:
    if operations.get("coverageStatus") != "complete":
        return unscorable_resolution(
            question,
            "annulled",
            "Operations outcome source does not cover the auto-evidence question geography and service date.",
            operations,
            weather_observation,
        )
    observation = weather_observation["observation"]
    if weather_observation.get("sourceStatus") == "corrected":
        return unscorable_resolution(
            question,
            "stale_source",
            "Weather observation source was corrected after the auto-evidence forecast and requires review.",
            operations,
            weather_observation,
        )
    if observation.get("qualityFlag") != "complete":
        return unscorable_resolution(
            question,
            "ambiguous",
            "Weather observation source quality does not support a normal auto-evidence resolution.",
            operations,
            weather_observation,
        )

    threshold = float(feature_snapshot["features"]["precipitationThresholdMm"])
    disruption_seen = any(event["weatherCoded"] for event in operations["events"])
    threshold_met = float(observation["dailyPrecipitationMm"]) >= threshold
    return {
        "resolutionRecordId": "resolution-601",
        "questionId": question["questionId"],
        "status": "resolved",
        "resolvedAt": RESOLVED_AT,
        "resolutionSource": operations["sourceRef"],
        "resolutionAuthority": question["resolutionAuthority"],
        "resolvedOutcome": {
            "outputType": "binary",
            "value": bool(disruption_seen and threshold_met),
        },
        "supportingEvidence": [
            operations["sourceRef"]["uri"],
            weather_observation["sourceRef"]["uri"],
        ],
    }


def build_reports(
    question: dict[str, Any],
    evidence: dict[str, Any],
    history: dict[str, Any],
    resolution: dict[str, Any],
) -> dict[str, Any]:
    if should_exclude_resolution(resolution):
        return {
            f"{PREFIX}-scoring.generated.json": {
                "scoringReportId": "scoring-601",
                "questionId": question["questionId"],
                "forecastId": evidence["forecastId"],
                "historyId": history["historyId"],
                "resolutionRecordId": resolution["resolutionRecordId"],
                "scoreStatus": "excluded",
                "scoringRule": "not_scored",
                "excludedReason": resolution["unscorableReason"],
                "generatedAt": GENERATED_AT,
            }
        }

    forecast_score = score_forecast_output(evidence["forecastOutput"], resolution["resolvedOutcome"], "brier")
    baseline_score = score_forecast_output(evidence["baselineForecast"], resolution["resolvedOutcome"], "brier")
    lift = baseline_lift(forecast_score, baseline_score)
    probability = evidence["forecastOutput"]["probability"]
    outcome = bool(resolution["resolvedOutcome"]["value"])
    buckets = calibration_buckets([(probability, outcome)], bucket_count=10)
    calibration_error = expected_calibration_error(buckets, 1)
    summary = track_record_summary(
        domain=question["domain"],
        horizon_bucket=question["horizon"]["label"],
        output_type=question["outputType"],
        scoring_rule="brier",
        scores=[forecast_score],
        baseline_scores=[baseline_score],
        n_ambiguous=0,
        n_annulled=0,
        n_forecasts=len(history["entries"]),
    )

    return {
        f"{PREFIX}-scoring.generated.json": {
            "scoringReportId": "scoring-601",
            "questionId": question["questionId"],
            "forecastId": evidence["forecastId"],
            "historyId": history["historyId"],
            "resolutionRecordId": resolution["resolutionRecordId"],
            "scoreStatus": "scored",
            "scoringRule": "brier",
            "primaryScore": round_float(forecast_score),
            "higherIsBetter": False,
            "timeWeighting": {
                "method": "latest_only",
                "totalWeight": 1,
            },
            "baselineScore": round_float(baseline_score),
            "baselineLift": round_float(lift),
            "generatedAt": GENERATED_AT,
        },
        f"{PREFIX}-calibration.generated.json": {
            "calibrationSummaryId": "calibration-601",
            "generatedAt": GENERATED_AT,
            "domain": question["domain"],
            "horizonBucket": question["horizon"]["label"],
            "outputType": question["outputType"],
            "coveragePeriod": {
                "startsAt": question["openAt"],
                "endsAt": resolution["resolvedAt"],
            },
            "sampleSize": 1,
            "expectedCalibrationError": round_float(calibration_error),
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
        },
        f"{PREFIX}-track-record.generated.json": {
            "trackRecordReportId": "trackrecord-601",
            "generatedAt": GENERATED_AT,
            "coveragePeriod": {
                "startsAt": question["openAt"],
                "endsAt": resolution["resolvedAt"],
            },
            "domain": summary["domain"],
            "horizonBucket": summary["horizonBucket"],
            "outputType": summary["outputType"],
            "counts": summary["counts"],
            "summary": {
                "primaryScoringRule": summary["summary"]["primaryScoringRule"],
                "primaryScore": round_float(summary["summary"]["primaryScore"]),
                "baselineScore": round_float(summary["summary"]["baselineScore"]),
                "baselineLift": round_float(summary["summary"]["baselineLift"]),
                "calibrationError": round_float(calibration_error),
                "lastUpdated": GENERATED_AT,
            },
            "scoreHistogram": [
                {
                    "lower": 0,
                    "upper": 0.5,
                    "count": 1,
                }
            ],
            "slices": [],
        },
    }


def build_outputs() -> dict[str, Any]:
    source_set = load_json(auto_evidence_path("source-set"))
    pipeline_run = load_json(auto_evidence_path("pipeline-run"))
    question = load_json(auto_evidence_path("question"))
    feature_snapshot = load_json(auto_evidence_path("feature-snapshot"))
    evidence = load_json(auto_evidence_path("evidence"))
    artifact = load_json(auto_evidence_path("artifact"))
    history = load_json(auto_evidence_path("history"))
    operations = load_json(OPERATIONS_OUTCOME)
    weather_observation = load_json(WEATHER_OBSERVATION)

    resolution = build_resolution(question, feature_snapshot, operations, weather_observation)
    resolved_question = deepcopy(question)
    resolved_question["status"] = resolution["status"]
    resolved_question["updatedAt"] = resolution["resolvedAt"]
    outputs: dict[str, Any] = {
        f"{PREFIX}-question.generated.json": resolved_question,
        f"{PREFIX}-resolution.generated.json": resolution,
        f"{PREFIX}-outcome-summary.generated.json": {
            "publicationStatus": "provisional",
            "qualityClaimStatus": "not_enough_resolved_auto_evidence_outcomes",
            "minimumCalibrationSampleSize": MIN_CALIBRATION_SAMPLE_SIZE,
            "resolvedComparableAutoEvidenceOutcomes": 1 if resolution["status"] == "resolved" else 0,
            "requestId": pipeline_run["requestId"],
            "pipelineRunId": pipeline_run["pipelineRunId"],
            "evidencePlanId": pipeline_run["outputs"]["evidencePlanId"],
            "evidenceSourceSetId": pipeline_run["outputs"]["evidenceSourceSetId"],
            "sourcePolicyId": pipeline_run["outputs"]["sourcePolicyId"],
            "sourceMode": pipeline_run["controls"]["sourceMode"],
            "questionId": question["questionId"],
            "forecastId": evidence["forecastId"],
            "evidencePacketId": evidence["evidencePacketId"],
            "resolutionRecordId": resolution["resolutionRecordId"],
            "forecastArtifactPath": pipeline_run["outputs"]["forecastArtifactPath"],
            "generatedAt": GENERATED_AT,
        },
    }
    outputs.update(build_reports(question, evidence, history, resolution))
    validate_outputs(outputs, source_set, pipeline_run, question, evidence, artifact, history)
    return outputs


def validate_outputs(
    outputs: dict[str, Any],
    source_set: dict[str, Any],
    pipeline_run: dict[str, Any],
    question: dict[str, Any],
    evidence: dict[str, Any],
    artifact: dict[str, Any],
    history: dict[str, Any],
) -> None:
    resolution = outputs[f"{PREFIX}-resolution.generated.json"]
    scoring = outputs[f"{PREFIX}-scoring.generated.json"]
    summary = outputs[f"{PREFIX}-outcome-summary.generated.json"]
    if pipeline_run["outputs"]["forecastId"] != evidence["forecastId"]:
        raise AssertionError("auto-evidence pipeline/evidence forecast binding mismatch")
    if artifact["forecastId"] != evidence["forecastId"]:
        raise AssertionError("auto-evidence artifact/evidence forecast binding mismatch")
    if history["questionId"] != question["questionId"]:
        raise AssertionError("auto-evidence history/question binding mismatch")
    if resolution["questionId"] != question["questionId"]:
        raise AssertionError("auto-evidence resolution/question binding mismatch")
    if scoring["forecastId"] != evidence["forecastId"]:
        raise AssertionError("auto-evidence scoring/evidence forecast binding mismatch")
    if summary["requestId"] != pipeline_run["requestId"]:
        raise AssertionError("auto-evidence outcome summary/request binding mismatch")
    if summary["evidenceSourceSetId"] != source_set["evidenceSourceSetId"]:
        raise AssertionError("auto-evidence outcome summary/source-set binding mismatch")
    if summary["sourcePolicyId"] != source_set["sourcePolicyId"]:
        raise AssertionError("auto-evidence outcome summary/source-policy binding mismatch")
    if resolution["status"] == "resolved" and scoring["scoreStatus"] != "scored":
        raise AssertionError("resolved auto-evidence outcome must be scored")
    if should_exclude_resolution(resolution) and scoring["scoreStatus"] != "excluded":
        raise AssertionError("unscorable auto-evidence outcome must be excluded")
    if summary["resolvedComparableAutoEvidenceOutcomes"] >= summary["minimumCalibrationSampleSize"]:
        raise AssertionError("auto-evidence fixture should remain below calibration threshold")

    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    if forecast_source_ids.intersection(resolution_source_ids):
        raise AssertionError("auto-evidence forecast provenance must not include future resolution sources")

    gathered_source_ids = {record["sourceRef"]["sourceId"] for record in source_set["records"]}
    if gathered_source_ids.intersection(resolution_source_ids):
        raise AssertionError("auto-evidence source set must not include future resolution sources")


def write_outputs(outputs: dict[str, Any]) -> None:
    expected_names = set(outputs)
    for path in GENERATED.glob("*.generated.json"):
        if path.name not in expected_names:
            path.unlink()
    for filename, output in outputs.items():
        write_json(GENERATED / filename, output)
    print(f"generated {len(outputs)} auto-evidence resolution outputs")


def check_outputs(outputs: dict[str, Any]) -> None:
    errors: list[str] = []
    expected_names = set(outputs)
    for path in sorted(GENERATED.glob("*.generated.json")):
        if path.name not in expected_names:
            errors.append(f"stale auto-evidence resolution output: {path}")
    for filename, output in outputs.items():
        path = GENERATED / filename
        expected = render_json(output)
        if not path.exists():
            errors.append(f"missing auto-evidence resolution output: {path}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            errors.append(f"auto-evidence resolution drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/resolve_auto_evidence_outcome.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(outputs)} auto-evidence resolution outputs")


def check_unscorable_variants() -> None:
    question = load_json(auto_evidence_path("question"))
    feature_snapshot = load_json(auto_evidence_path("feature-snapshot"))
    operations = load_json(OPERATIONS_OUTCOME)
    weather_observation = load_json(WEATHER_OBSERVATION)

    missing_ops = deepcopy(operations)
    missing_ops["coverageStatus"] = "missing_declared_geography"
    if build_resolution(question, feature_snapshot, missing_ops, weather_observation)["status"] != "annulled":
        raise AssertionError("missing operations coverage should annul the auto-evidence outcome")

    conflicting_weather = deepcopy(weather_observation)
    conflicting_weather["observation"]["qualityFlag"] = "conflicting_station_reports"
    if build_resolution(question, feature_snapshot, operations, conflicting_weather)["status"] != "ambiguous":
        raise AssertionError("conflicting weather observations should be ambiguous")

    corrected_weather = deepcopy(weather_observation)
    corrected_weather["sourceStatus"] = "corrected"
    if build_resolution(question, feature_snapshot, operations, corrected_weather)["status"] != "stale_source":
        raise AssertionError("corrected weather observations should be treated as stale_source")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated auto-evidence resolution outputs")
    args = parser.parse_args()
    outputs = build_outputs()
    check_unscorable_variants()
    if args.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)


if __name__ == "__main__":
    main()
