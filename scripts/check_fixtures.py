#!/usr/bin/env python3
"""Check OPE fixture scoring and lifecycle semantics without external deps."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from ope_scoring import (
    baseline_lift,
    binary_brier,
    binary_log_loss,
    calibration_buckets,
    interval_score,
    score_forecast_output,
    should_exclude_resolution,
    time_weighted_history_score,
    track_record_summary,
)


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "spec" / "fixtures" / "valid"
INVALID = ROOT / "spec" / "fixtures" / "invalid"
GENERATED = ROOT / "spec" / "fixtures" / "generated"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-9) -> None:
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def check_binary_weather_logistics_fixture() -> None:
    question = load_json(VALID / "binary-weather-logistics-question.json")
    history = load_json(VALID / "binary-weather-logistics-history.json")
    evidence = load_json(VALID / "binary-weather-logistics-evidence.json")
    resolution = load_json(VALID / "binary-weather-logistics-resolution.json")
    scoring = load_json(VALID / "binary-weather-logistics-scoring.json")
    track_record = load_json(VALID / "binary-weather-logistics-track-record.json")
    generated_scoring = load_json(GENERATED / "binary-weather-logistics-scoring.generated.json")
    generated_calibration = load_json(GENERATED / "binary-weather-logistics-calibration.generated.json")
    generated_track_record = load_json(GENERATED / "binary-weather-logistics-track-record.generated.json")

    if question["questionId"] != history["questionId"]:
        raise AssertionError("question/history binding mismatch")
    if question["questionId"] != evidence["questionId"]:
        raise AssertionError("question/evidence binding mismatch")
    if question["questionId"] != resolution["questionId"]:
        raise AssertionError("question/resolution binding mismatch")
    if scoring["questionId"] != question["questionId"]:
        raise AssertionError("question/scoring binding mismatch")

    outcome = bool(resolution["resolvedOutcome"]["value"])
    forecast_probability = evidence["forecastOutput"]["probability"]
    baseline_probability = evidence["baselineForecast"]["probability"]

    forecast_score = binary_brier(forecast_probability, outcome)
    expected_forecast_score = scoring["primaryScore"]
    assert_close(forecast_score, expected_forecast_score, "binary Brier score")
    assert_close(forecast_score, generated_scoring["primaryScore"], "generated binary Brier score")

    baseline_score = binary_brier(baseline_probability, outcome)
    assert_close(baseline_score, scoring["baselineScore"], "baseline Brier score")
    assert_close(baseline_score, generated_scoring["baselineScore"], "generated baseline Brier score")

    lift = baseline_lift(forecast_score, baseline_score)
    assert_close(lift, scoring["baselineLift"], "baseline lift")
    assert_close(lift, generated_scoring["baselineLift"], "generated baseline lift")

    direct_score = score_forecast_output(
        evidence["forecastOutput"],
        resolution["resolvedOutcome"],
        "brier",
    )
    assert_close(direct_score, forecast_score, "score_forecast_output brier")

    weighted_score = time_weighted_history_score(
        history,
        resolution["resolvedOutcome"],
        "brier",
        question["closeAt"],
    )
    if weighted_score <= 0:
        raise AssertionError("time-weighted score should be positive for this fixture")

    log_loss = binary_log_loss(forecast_probability, outcome)
    if log_loss <= 0:
        raise AssertionError("binary log loss should be positive")

    buckets = calibration_buckets([(forecast_probability, outcome)], bucket_count=10)
    if sum(int(bucket["count"]) for bucket in buckets) != 1:
        raise AssertionError("calibration bucket count should equal input pair count")
    if generated_calibration["sampleSize"] != 1:
        raise AssertionError("generated calibration sample size should be 1")
    assert_close(
        generated_calibration["expectedCalibrationError"],
        0.59,
        "generated expected calibration error",
    )

    summary = track_record_summary(
        domain=question["domain"],
        horizon_bucket=question["horizon"]["label"],
        output_type=question["outputType"],
        scoring_rule="brier",
        scores=[forecast_score],
        baseline_scores=[baseline_score],
        n_ambiguous=0,
        n_annulled=0,
    )
    assert_close(
        summary["summary"]["primaryScore"],
        track_record["summary"]["primaryScore"],
        "track record primary score",
    )
    assert_close(
        generated_track_record["summary"]["primaryScore"],
        track_record["summary"]["primaryScore"],
        "generated track record primary score",
    )
    if generated_track_record["counts"]["nForecasts"] != len(history["entries"]):
        raise AssertionError("generated track record should count forecast history entries")


def check_numeric_interval_fixture() -> None:
    question = load_json(VALID / "numeric-energy-demand-question.json")
    artifact = load_json(VALID / "numeric-energy-demand-artifact.json")
    if question["questionId"] != artifact["questionId"]:
        raise AssertionError("numeric question/artifact binding mismatch")
    score = interval_score(
        artifact["forecastOutput"]["lower"],
        artifact["forecastOutput"]["upper"],
        artifact["forecastOutput"]["coverage"],
        19100,
    )
    assert_close(score, 1600, "interval score inside interval")


def check_invalid_semantic_fixtures() -> None:
    ambiguous_scored = load_json(INVALID / "ambiguous-scored-report.json")
    annulled_scored = load_json(INVALID / "annulled-scored-report.json")
    mismatch = load_json(INVALID / "mismatched-request-result-artifact.json")

    for label, report in [
        ("ambiguous", ambiguous_scored),
        ("annulled", annulled_scored),
    ]:
        if report["scoreStatus"] != "scored":
            raise AssertionError(f"{label} invalid fixture should demonstrate wrong scored status")
        expected_resolution = {
            "status": label,
            "resolutionRecordId": report["resolutionRecordId"],
            "questionId": report["questionId"],
            "resolvedAt": report["generatedAt"],
            "resolutionSource": {
                "sourceId": "source-999",
                "name": "invalid fixture source",
                "sourceType": "other",
            },
            "resolutionAuthority": "OPE fixture resolver",
            "unscorableReason": f"{label} fixture",
        }
        if not should_exclude_resolution(expected_resolution):
            raise AssertionError(f"{label} resolution should be excluded from scoring")

    expected_question_id = "question-001"
    if mismatch["questionId"] == expected_question_id:
        raise AssertionError("mismatch fixture no longer mismatches expected question id")


def main() -> None:
    check_binary_weather_logistics_fixture()
    check_numeric_interval_fixture()
    check_invalid_semantic_fixtures()
    print("fixture scoring checks passed")


if __name__ == "__main__":
    main()
