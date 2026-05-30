#!/usr/bin/env python3
"""Resolve and score the explicit source-handoff setup forecast."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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
SOURCE_HANDOFF_FORECAST = ROOT / "spec" / "fixtures" / "generated" / "source-handoff-forecast"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-handoff-resolution"
PREFIX = "weather-logistics-source-handoff-resolution"
RESOLVED_AT = "2026-06-04T12:30:00Z"
GENERATED_AT = "2026-06-04T12:35:00Z"
MIN_CALIBRATION_SAMPLE_SIZE = 30


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 10)


def forecast_path(name: str) -> Path:
    return SOURCE_HANDOFF_FORECAST / f"weather-logistics-confirmed-builder-draft-source-handoff-{name}.generated.json"


def path_from_local_uri(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme != "local":
        raise AssertionError("source-handoff resolution only supports local:// declared outcome sources")
    relative = parsed.netloc + parsed.path
    if relative.startswith("/"):
        relative = relative[1:]
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise AssertionError("declared outcome source must stay inside the repository")
    return path


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return True
    if normalized in {"false", "0", "no", "n"}:
        return False
    raise AssertionError(f"unsupported boolean outcome value {value!r}")


def declared_outcome(question: dict[str, Any], evidence: dict[str, Any]) -> tuple[bool, str]:
    source = evidence["resolutionSource"]
    path = path_from_local_uri(source["uri"])
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise AssertionError("declared outcome source is empty")
    expected_date = question["horizon"]["startsAt"][:10]
    expected_city = "warsaw"
    matches = [
        row
        for row in rows
        if row.get("date") == expected_date
        and row.get("city", "").strip().lower() == expected_city
    ]
    if len(matches) != 1:
        raise AssertionError("declared outcome source must contain exactly one matching row")
    return parse_bool(matches[0]["disrupted"]), source["uri"]


def build_resolution(question: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    disrupted, source_uri = declared_outcome(question, evidence)
    return {
        "resolutionRecordId": "resolution-1102",
        "questionId": question["questionId"],
        "status": "resolved",
        "resolvedAt": RESOLVED_AT,
        "resolutionSource": evidence["resolutionSource"],
        "resolutionAuthority": question["resolutionAuthority"],
        "resolvedOutcome": {
            "outputType": "binary",
            "value": disrupted,
        },
        "supportingEvidence": [source_uri],
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
                "scoringReportId": "scoring-1102",
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
            "scoringReportId": "scoring-1102",
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
            "calibrationSummaryId": "calibration-1102",
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
            "trackRecordReportId": "trackrecord-1102",
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
    setup_run = load_json(forecast_path("setup-forecast-run"))
    question = load_json(forecast_path("question"))
    evidence = load_json(forecast_path("evidence"))
    artifact = load_json(forecast_path("artifact"))
    history = load_json(forecast_path("history"))

    resolution = build_resolution(question, evidence)
    resolved_question = deepcopy(question)
    resolved_question["status"] = resolution["status"]
    resolved_question["updatedAt"] = resolution["resolvedAt"]
    outputs: dict[str, Any] = {
        f"{PREFIX}-question.generated.json": resolved_question,
        f"{PREFIX}-resolution.generated.json": resolution,
        f"{PREFIX}-outcome-summary.generated.json": {
            "publicationStatus": "provisional",
            "qualityClaimStatus": "not_enough_resolved_source_handoff_outcomes",
            "minimumCalibrationSampleSize": MIN_CALIBRATION_SAMPLE_SIZE,
            "resolvedComparableSourceHandoffOutcomes": 1 if resolution["status"] == "resolved" else 0,
            "setupForecastRunId": setup_run["setupForecastRunId"],
            "sourceIntakeHandoffId": setup_run["sourceIntakeHandoffId"],
            "sourceHandoffMethodGateId": setup_run["sourceHandoffMethodGateId"],
            "sourceIntakeReportId": setup_run["sourceIntakeReportId"],
            "setupMethodDecisionId": setup_run["setupMethodDecisionId"],
            "setupBenchmarkGateId": setup_run["setupBenchmarkGateId"],
            "questionId": question["questionId"],
            "forecastId": evidence["forecastId"],
            "evidencePacketId": evidence["evidencePacketId"],
            "resolutionRecordId": resolution["resolutionRecordId"],
            "forecastArtifactPath": setup_run["outputs"]["forecastArtifactPath"],
            "generatedAt": GENERATED_AT,
        },
    }
    outputs.update(build_reports(question, evidence, history, resolution))
    validate_outputs(outputs, setup_run, question, evidence, artifact, history)
    return outputs


def validate_outputs(
    outputs: dict[str, Any],
    setup_run: dict[str, Any],
    question: dict[str, Any],
    evidence: dict[str, Any],
    artifact: dict[str, Any],
    history: dict[str, Any],
) -> None:
    resolution = outputs[f"{PREFIX}-resolution.generated.json"]
    scoring = outputs[f"{PREFIX}-scoring.generated.json"]
    summary = outputs[f"{PREFIX}-outcome-summary.generated.json"]
    if setup_run["recordBinding"]["forecastId"] != evidence["forecastId"]:
        raise AssertionError("source-handoff setup run/evidence forecast binding mismatch")
    if artifact["forecastId"] != evidence["forecastId"]:
        raise AssertionError("source-handoff artifact/evidence forecast binding mismatch")
    if history["questionId"] != question["questionId"]:
        raise AssertionError("source-handoff history/question binding mismatch")
    if resolution["questionId"] != question["questionId"]:
        raise AssertionError("source-handoff resolution/question binding mismatch")
    if scoring["forecastId"] != evidence["forecastId"]:
        raise AssertionError("source-handoff scoring/evidence forecast binding mismatch")
    if summary["setupForecastRunId"] != setup_run["setupForecastRunId"]:
        raise AssertionError("source-handoff outcome summary/setup run binding mismatch")
    if summary["sourceIntakeHandoffId"] != setup_run["sourceIntakeHandoffId"]:
        raise AssertionError("source-handoff outcome summary/handoff binding mismatch")
    if summary["sourceHandoffMethodGateId"] != setup_run["sourceHandoffMethodGateId"]:
        raise AssertionError("source-handoff outcome summary/method gate binding mismatch")
    if resolution["status"] == "resolved" and scoring["scoreStatus"] != "scored":
        raise AssertionError("resolved source-handoff outcome must be scored")
    if should_exclude_resolution(resolution) and scoring["scoreStatus"] != "excluded":
        raise AssertionError("unscorable source-handoff outcome must be excluded")
    if summary["resolvedComparableSourceHandoffOutcomes"] >= summary["minimumCalibrationSampleSize"]:
        raise AssertionError("source-handoff fixture should remain below calibration threshold")

    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    if forecast_source_ids.intersection(resolution_source_ids):
        raise AssertionError("source-handoff forecast evidence must not include future resolution sources")


def write_outputs(outputs: dict[str, Any]) -> None:
    expected_names = set(outputs)
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path in GENERATED.glob("*.generated.json"):
        if path.name not in expected_names:
            path.unlink()
    for filename, output in outputs.items():
        write_json(GENERATED / filename, output)
    print(f"generated {len(outputs)} source-handoff resolution outputs")


def check_outputs(outputs: dict[str, Any]) -> None:
    errors: list[str] = []
    expected_names = set(outputs)
    for path in sorted(GENERATED.glob("*.generated.json")):
        if path.name not in expected_names:
            errors.append(f"stale source-handoff resolution output: {path}")
    for filename, output in outputs.items():
        path = GENERATED / filename
        expected = render_json(output)
        if not path.exists():
            errors.append(f"missing source-handoff resolution output: {path}")
            continue
        if path.read_text(encoding="utf-8") != expected:
            errors.append(f"source-handoff resolution drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/resolve_source_handoff_outcome.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(outputs)} source-handoff resolution outputs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated source-handoff resolution outputs")
    args = parser.parse_args()
    outputs = build_outputs()
    if args.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)


if __name__ == "__main__":
    main()
