#!/usr/bin/env python3
"""Generate a checked weather-transit-delay forward-run corpus index."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import run_transit_delay_forecast as transit_forecast
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-forward-run-corpus"
OUTPUT_PATH = GENERATED / "transit-forward-run-corpus.generated.json"
SCHEMA = SPEC / "transit-forward-run-corpus.schema.json"
GENERATED_AT = "2026-05-27T13:00:00Z"

FORWARD_RUN_SUMMARY = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "transit-delay-forward-run"
    / "weather-transit-delays-forward-run.generated.json"
)
FORECAST_ARTIFACT = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "transit-delay-forecast"
    / "weather-transit-delays-artifact.generated.json"
)
RESOLUTION_RECORD = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "transit-delay-forecast"
    / "weather-transit-delays-resolution.generated.json"
)
SCORING_REPORT = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "transit-delay-forecast"
    / "weather-transit-delays-scoring.generated.json"
)

EXCLUSION_REASONS = {
    "ambiguous",
    "annulled",
    "low_coverage",
    "invalid_window",
    "feed_unavailable",
    "non_comparable",
}


class TransitForwardRunCorpusError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def forecast_before_close(forecasted_at: str, close_at: str) -> bool:
    return parse_timestamp(forecasted_at) <= parse_timestamp(close_at)


def resolved_after_horizon(resolved_at: str, horizon_end: str) -> bool:
    return parse_timestamp(resolved_at) >= parse_timestamp(horizon_end)


def build_comparable_run() -> dict[str, Any]:
    forward = load_json(FORWARD_RUN_SUMMARY)
    artifact = load_json(FORECAST_ARTIFACT)
    resolution = load_json(RESOLUTION_RECORD)
    scoring = load_json(SCORING_REPORT)
    forecast_stage = forward["forecastStage"]
    resolution_stage = forward["resolutionStage"]
    score_stage = forward["scoreStage"]
    return {
        "corpusRunId": "transitforwardruncorpusrun-001",
        "forwardRunId": forward["forwardRunId"],
        "runStatus": "scored",
        "serviceDate": forecast_stage["serviceDate"],
        "serviceWindow": forecast_stage["serviceWindow"],
        "forecastBinding": {
            "forecastId": artifact["forecastId"],
            "questionId": artifact["questionId"],
            "forecastedAt": forecast_stage["forecastedAt"],
            "closeAt": forecast_stage["closeAt"],
            "horizonStart": forecast_stage["horizon"]["startsAt"],
            "horizonEnd": forecast_stage["horizon"]["endsAt"],
            "forecastBeforeClose": forecast_before_close(
                forecast_stage["forecastedAt"],
                forecast_stage["closeAt"],
            ),
        },
        "resolutionBinding": {
            "resolutionRecordId": resolution["resolutionRecordId"],
            "resolvedAt": resolution["resolvedAt"],
            "resolutionStatus": resolution["status"],
            "resolvedAfterHorizon": resolved_after_horizon(
                resolution["resolvedAt"],
                forecast_stage["horizon"]["endsAt"],
            ),
            "outcomeLabel": resolution_stage["outcomeLabel"],
            "observationCount": resolution_stage["observationCount"],
            "lateCount": resolution_stage["lateCount"],
            "lateRatio": resolution_stage["lateRatio"],
        },
        "scoreBinding": {
            "scoringReportId": scoring["scoringReportId"],
            "scoreStatus": scoring["scoreStatus"],
            "scoringRule": scoring["scoringRule"],
            "primaryScore": score_stage["primaryScore"],
            "baselineScore": score_stage["baselineScore"],
            "baselineLift": score_stage["baselineLift"],
        },
        "artifactPaths": {
            "forwardRunSummaryPath": rel(FORWARD_RUN_SUMMARY),
            "forecastArtifactPath": rel(FORECAST_ARTIFACT),
            "resolutionRecordPath": rel(RESOLUTION_RECORD),
            "scoringReportPath": rel(SCORING_REPORT),
        },
        "comparability": {
            "comparable": True,
            "reasonCodes": [],
        },
    }


def excluded_run(
    index: int,
    reason: str,
    status: str,
    service_date: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "corpusRunId": f"transitforwardruncorpusrun-{index:03d}",
        "forwardRunId": f"transitdelayforwardrun-{900 + index:03d}",
        "serviceDate": service_date,
        "serviceWindow": transit_forecast.SERVICE_WINDOW,
        "exclusionReason": reason,
        "runStatus": status,
        "artifactPaths": [],
        "nextAction": next_action,
    }


def build_excluded_runs() -> list[dict[str, Any]]:
    return [
        excluded_run(
            2,
            "ambiguous",
            "ambiguous",
            "2026-06-11",
            "exclude from scoring until the outcome can be resolved under declared criteria",
        ),
        excluded_run(
            3,
            "annulled",
            "annulled",
            "2026-06-12",
            "preserve the annulment reason and keep the run out of comparable counts",
        ),
        excluded_run(
            4,
            "low_coverage",
            "blocked",
            "2026-06-13",
            "do not score until the delay rows meet the minimum observation count",
        ),
        excluded_run(
            5,
            "invalid_window",
            "blocked",
            "2026-06-14",
            "repair the service window binding before adding the run to the corpus",
        ),
        excluded_run(
            6,
            "feed_unavailable",
            "blocked",
            "2026-06-15",
            "retry capture under the source policy or mark the window unavailable",
        ),
        excluded_run(
            7,
            "non_comparable",
            "excluded",
            "2026-06-16",
            "keep the run for audit but exclude it from morning-peak comparable counts",
        ),
    ]


def build_corpus() -> dict[str, Any]:
    comparable_runs = [build_comparable_run()]
    excluded_runs = build_excluded_runs()
    minimum_track_record = 30
    minimum_calibration = 100
    corpus = {
        "transitForwardRunCorpusId": "transitforwardruncorpus-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "corpusMode": "checked_fixture_index",
        "corpusScope": {
            "network": transit_forecast.NETWORK,
            "geography": transit_forecast.GEOGRAPHY,
            "serviceWindow": transit_forecast.SERVICE_WINDOW,
            "lateThresholdSeconds": transit_forecast.LATE_SECONDS,
            "eventThresholdLateRatio": transit_forecast.EVENT_THRESHOLD,
            "minimumObservationCount": transit_forecast.MIN_OBSERVATIONS,
        },
        "comparableWindowPolicy": {
            "policyId": "transitforwardruncorpuspolicy-001",
            "forecastTimingRule": "forecasted_at_must_be_at_or_before_close_at",
            "resolutionTimingRule": "resolved_at_must_be_after_horizon_end",
            "scoreTimingRule": "score_requires_resolved_outcome_and_baseline",
            "minimumComparableResolvedForTrackRecord": minimum_track_record,
            "minimumComparableResolvedForCalibration": minimum_calibration,
            "acceptedRunStatuses": ["scored"],
            "requiredArtifactBindings": [
                "forward_run_state",
                "forecast_artifact",
                "resolution_record",
                "scoring_report",
            ],
            "excludedReasonCodes": [
                "ambiguous",
                "annulled",
                "low_coverage",
                "invalid_window",
                "feed_unavailable",
                "non_comparable",
            ],
            "forecastTimeEvidenceMayInclude": [
                "weather_forecast",
                "historical_delay_rows",
                "static_schedule",
                "planned_service_alerts",
            ],
            "resolutionOnlyEvidenceRoles": [
                "trip_updates_after_window",
                "post_window_delay_rows",
                "resolution_outcome",
            ],
        },
        "summary": {
            "corpusCount": len(comparable_runs) + len(excluded_runs),
            "comparableResolvedCount": len(comparable_runs),
            "scoredCount": len(comparable_runs),
            "excludedCount": len(excluded_runs),
            "pendingCount": 0,
            "minimumComparableResolvedForTrackRecord": minimum_track_record,
            "minimumComparableResolvedForCalibration": minimum_calibration,
            "qualityClaimStatus": "not_enough_resolved_comparable_outcomes",
            "calibrationClaimStatus": "not_enough_resolved_comparable_outcomes",
        },
        "comparableRuns": comparable_runs,
        "excludedRuns": excluded_runs,
        "claimBoundary": {
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "baselineTrackRecordAllowed": False,
            "normalChecksUseLiveNetwork": False,
            "liveCapturesCommitted": False,
            "resolvedComparableOutcomes": len(comparable_runs),
        },
        "readSurface": {
            "command": "python3 scripts/ope.py transit-forward-run-corpus",
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
        },
        "warnings": [
            "This corpus is a checked local index and does not execute forward runs or fetch live sources.",
            "One comparable scored run is useful implementation evidence, not a calibration or quality claim.",
            "Excluded runs preserve audit reasons but do not count toward comparable resolved windows.",
            "Resolution outcome rows are resolution-only evidence and must not become forecast-time provenance.",
        ],
    }
    validate_corpus(corpus)
    return corpus


def validate_corpus(corpus: dict[str, Any]) -> None:
    errors = validate_record(corpus, SCHEMA)
    if errors:
        raise TransitForwardRunCorpusError(f"transit forward-run corpus schema validation failed: {errors[0]}")
    summary = corpus["summary"]
    comparable_runs = corpus["comparableRuns"]
    excluded_runs = corpus["excludedRuns"]
    if summary["corpusCount"] != len(comparable_runs) + len(excluded_runs):
        raise TransitForwardRunCorpusError("corpus count must equal comparable plus excluded runs")
    if summary["comparableResolvedCount"] != len(comparable_runs):
        raise TransitForwardRunCorpusError("comparable resolved count must match comparable runs")
    if summary["excludedCount"] != len(excluded_runs):
        raise TransitForwardRunCorpusError("excluded count must match excluded runs")
    reasons = {run["exclusionReason"] for run in excluded_runs}
    if reasons != EXCLUSION_REASONS:
        raise TransitForwardRunCorpusError("corpus must include every required exclusion reason")
    for run in comparable_runs:
        if not run["forecastBinding"]["forecastBeforeClose"]:
            raise TransitForwardRunCorpusError("comparable runs must be forecast before close")
        if not run["resolutionBinding"]["resolvedAfterHorizon"]:
            raise TransitForwardRunCorpusError("comparable runs must resolve after horizon end")
        if not run["comparability"]["comparable"]:
            raise TransitForwardRunCorpusError("comparable run rows must be marked comparable")
        for path in run["artifactPaths"].values():
            if not (ROOT / path).exists():
                raise TransitForwardRunCorpusError(f"corpus artifact path does not exist: {path}")
    boundary = corpus["claimBoundary"]
    if boundary["qualityClaimAllowed"] or boundary["calibrationClaimAllowed"] or boundary["baselineTrackRecordAllowed"]:
        raise TransitForwardRunCorpusError("corpus must keep quality, calibration, and track-record claims blocked")
    read_surface = corpus["readSurface"]
    if (
        read_surface["createsForecastArtifacts"]
        or read_surface["createsResolutionArtifacts"]
        or read_surface["createsScoringRecords"]
        or read_surface["fetchesLiveData"]
        or read_surface["storesCredentials"]
    ):
        raise TransitForwardRunCorpusError("corpus read surface must not create artifacts or fetch data")


def write_corpus(corpus: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(corpus), encoding="utf-8")
    print("generated transit forward-run corpus")


def check_corpus(corpus: dict[str, Any]) -> None:
    expected = render_json(corpus)
    if not OUTPUT_PATH.exists():
        print(f"missing transit forward-run corpus: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_forward_run_corpus.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"transit forward-run corpus drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_forward_run_corpus.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked transit forward-run corpus")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        corpus = build_corpus()
        if args.write:
            write_corpus(corpus)
        elif args.check:
            check_corpus(corpus)
        else:
            sys.stdout.write(render_json(corpus))
    except (OSError, json.JSONDecodeError, TransitForwardRunCorpusError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
