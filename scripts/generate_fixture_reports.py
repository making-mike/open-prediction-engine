#!/usr/bin/env python3
"""Generate deterministic report fixtures from OPE input fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_scoring import (
    baseline_lift,
    calibration_buckets,
    score_forecast_output,
    track_record_summary,
)


ROOT = Path(__file__).resolve().parents[1]
VALID = ROOT / "spec" / "fixtures" / "valid"
GENERATED = ROOT / "spec" / "fixtures" / "generated"
GENERATED_AT = "2026-06-04T10:20:00Z"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 10)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n")


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


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


def build_binary_weather_reports() -> dict[str, Any]:
    question = load_json(VALID / "binary-weather-logistics-question.json")
    history = load_json(VALID / "binary-weather-logistics-history.json")
    evidence = load_json(VALID / "binary-weather-logistics-evidence.json")
    resolution = load_json(VALID / "binary-weather-logistics-resolution.json")

    if resolution["status"] != "resolved":
        raise ValueError("generated fixture reports require a resolved question")

    forecast_score = score_forecast_output(
        evidence["forecastOutput"],
        resolution["resolvedOutcome"],
        "brier",
    )
    baseline_score = score_forecast_output(
        evidence["baselineForecast"],
        resolution["resolvedOutcome"],
        "brier",
    )
    lift = baseline_lift(forecast_score, baseline_score)

    scoring_report = {
        "scoringReportId": "scoring-generated-001",
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
            "totalWeight": 1
        },
        "baselineScore": round_float(baseline_score),
        "baselineLift": round_float(lift),
        "generatedAt": GENERATED_AT
    }

    probability = evidence["forecastOutput"]["probability"]
    outcome = bool(resolution["resolvedOutcome"]["value"])
    buckets = calibration_buckets([(probability, outcome)], bucket_count=10)
    calibration_summary = {
        "calibrationSummaryId": "calibration-generated-001",
        "generatedAt": GENERATED_AT,
        "domain": question["domain"],
        "horizonBucket": question["horizon"]["label"],
        "outputType": question["outputType"],
        "coveragePeriod": {
            "startsAt": question["openAt"],
            "endsAt": resolution["resolvedAt"]
        },
        "sampleSize": 1,
        "expectedCalibrationError": round_float(expected_calibration_error(buckets, 1)),
        "buckets": [
            {
                "lowerProbability": round_float(bucket["lowerProbability"]),
                "upperProbability": round_float(bucket["upperProbability"]),
                "count": bucket["count"],
                "meanForecastProbability": round_float(bucket["meanForecastProbability"]),
                "observedFrequency": round_float(bucket["observedFrequency"])
            }
            for bucket in buckets
        ]
    }

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
    track_record_report = {
        "trackRecordReportId": "trackrecord-generated-001",
        "generatedAt": GENERATED_AT,
        "coveragePeriod": {
            "startsAt": question["openAt"],
            "endsAt": resolution["resolvedAt"]
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
            "calibrationError": calibration_summary["expectedCalibrationError"],
            "lastUpdated": GENERATED_AT
        },
        "scoreHistogram": [
            {
                "lower": 0,
                "upper": 0.5,
                "count": 1
            }
        ],
        "slices": []
    }

    return {
        "binary-weather-logistics-scoring.generated.json": scoring_report,
        "binary-weather-logistics-calibration.generated.json": calibration_summary,
        "binary-weather-logistics-track-record.generated.json": track_record_report,
    }


def build_reports() -> dict[str, Any]:
    return build_binary_weather_reports()


def write_reports(reports: dict[str, Any]) -> None:
    for filename, report in reports.items():
        write_json(GENERATED / filename, report)
    print(f"generated {len(reports)} fixture reports")


def check_reports(reports: dict[str, Any]) -> None:
    errors: list[str] = []
    for filename, report in reports.items():
        path = GENERATED / filename
        expected = render_json(report)
        if not path.exists():
            errors.append(f"missing generated report: {path}")
            continue
        actual = path.read_text()
        if actual != expected:
            errors.append(f"generated report drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_fixture_reports.py --write` to update reports", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(reports)} generated fixture reports")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write generated reports instead of checking committed reports",
    )
    args = parser.parse_args()
    reports = build_reports()
    if args.write:
        write_reports(reports)
    else:
        check_reports(reports)


if __name__ == "__main__":
    main()
