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
from ope_fixtures import check_generated, render_json, write_generated
from prediction_campaign_forecast_write_runtime import (
    PredictionCampaignForecastWriteError,
    ensure_safe_local_path,
    read_json,
)


ROOT = Path(__file__).resolve().parents[1]
LOCAL_WORKSPACE_ROOT = ROOT
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-baseline-track-record-gate"
OUTPUT_PATH = GENERATED / "transit-baseline-track-record-gate.generated.json"
SCHEMA = SPEC / "transit-baseline-track-record-gate.schema.json"
GENERATED_AT = "2026-05-27T14:00:00Z"
DEFAULT_LEDGER_CASE = "excluded_missing_outcome"
LEDGER_CASES = ["excluded_missing_outcome", "comparable_scored"]


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


def campaign_score_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in ledger["comparableRows"]:
        rows.append(
            {
                "corpusRunId": row["rowId"],
                "forwardRunId": row["runId"],
                "forecastId": row["forecastId"],
                "questionId": row["questionId"],
                "serviceDate": row["serviceDate"],
                "outcomeLabel": row["outcomeLabel"],
                "primaryScore": row["primaryScore"],
                "baselineScore": row["baselineScore"],
                "baselineLift": round_float(row["baselineScore"] - row["primaryScore"]),
            }
        )
    return rows


def load_local_campaign_ledger(campaign: str) -> dict[str, Any]:
    path_value = f".ope/live/prediction-campaigns/{campaign}/evidence-ledger.json"
    path = ensure_safe_local_path(path_value, workspace_root=LOCAL_WORKSPACE_ROOT)
    if not path.exists():
        raise TransitBaselineTrackRecordGateError(f"local campaign evidence ledger is missing: {path_value}")
    state = read_json(path)
    if state.get("stateType") != "prediction_campaign_evidence_ledger":
        raise TransitBaselineTrackRecordGateError(f"local campaign evidence ledger state type mismatch: {path_value}")
    if state.get("campaignId") != campaign:
        raise TransitBaselineTrackRecordGateError(f"local campaign evidence ledger campaign mismatch: {path_value}")
    comparable_rows = state.get("comparableRows", [])
    excluded_rows = state.get("excludedRows", [])
    if not isinstance(comparable_rows, list) or not isinstance(excluded_rows, list):
        raise TransitBaselineTrackRecordGateError(f"local campaign evidence ledger row lists are invalid: {path_value}")
    return {
        "bindings": {
            "campaignId": campaign,
            "cycleId": str(state.get("cycleId", "predictioncycle-001")),
            "ledgerPath": path_value,
        },
        "comparableRows": comparable_rows,
        "excludedRows": excluded_rows,
    }


def campaign_ledger_summary(
    campaign: str | None,
    ledger_case: str,
    *,
    from_local_ledger: bool = False,
    ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if campaign is None:
        return {
            "included": False,
            "campaignId": "none",
            "ledgerCase": "none",
            "ledgerPath": "none",
            "comparableRowCount": 0,
            "excludedRowCount": 0,
            "sourceCommand": "none",
        }
    if ledger is None:
        if from_local_ledger:
            ledger = load_local_campaign_ledger(campaign)
        else:
            from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger

            ledger = build_prediction_campaign_evidence_ledger(mode="append-ready", ledger_case=ledger_case)
    if campaign != ledger["bindings"]["campaignId"]:
        raise TransitBaselineTrackRecordGateError(f"unsupported campaign ledger: {campaign}")
    source_command = (
        f"python3 scripts/ope.py transit-track-record-gate --campaign {campaign} --from-local-ledger"
        if from_local_ledger
        else f"python3 scripts/ope.py prediction-campaign append-ready --ledger-case {ledger_case}"
    )
    return {
        "included": True,
        "campaignId": ledger["bindings"]["campaignId"],
        "ledgerCase": "local_evidence_ledger" if from_local_ledger else ledger_case,
        "ledgerPath": ledger["bindings"]["ledgerPath"],
        "comparableRowCount": len(ledger["comparableRows"]),
        "excludedRowCount": len(ledger["excludedRows"]),
        "sourceCommand": source_command,
    }


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


def build_gate(
    *,
    campaign: str | None = None,
    ledger_case: str = DEFAULT_LEDGER_CASE,
    from_local_ledger: bool = False,
) -> dict[str, Any]:
    if from_local_ledger and campaign is None:
        raise TransitBaselineTrackRecordGateError("--from-local-ledger requires --campaign")
    corpus = build_corpus()
    ledger = None
    if campaign:
        if from_local_ledger:
            ledger = load_local_campaign_ledger(campaign)
        else:
            from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger

            ledger = build_prediction_campaign_evidence_ledger(mode="append-ready", ledger_case=ledger_case)
    if ledger and campaign != ledger["bindings"]["campaignId"]:
        raise TransitBaselineTrackRecordGateError(f"unsupported campaign ledger: {campaign}")
    comparable_runs = corpus["comparableRuns"]
    excluded_runs = corpus["excludedRuns"]
    summary = corpus["summary"]
    policy = corpus["comparableWindowPolicy"]
    minimum_track_record = policy["minimumComparableResolvedForTrackRecord"]
    minimum_calibration = policy["minimumComparableResolvedForCalibration"]
    campaign_comparable_rows = ledger["comparableRows"] if ledger else []
    campaign_excluded_rows = ledger["excludedRows"] if ledger else []
    resolved_sample_size = summary["comparableResolvedCount"] + len(campaign_comparable_rows)
    track_record_status = status_for(resolved_sample_size, minimum_track_record)
    calibration_status = status_for(resolved_sample_size, minimum_calibration)
    rows = score_rows(corpus) + (campaign_score_rows(ledger) if ledger else [])
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
        n_forecasts=summary["corpusCount"] + len(campaign_comparable_rows) + len(campaign_excluded_rows),
    )
    horizon_starts = [run["forecastBinding"]["horizonStart"] for run in comparable_runs] + [
        row["horizonStartsAt"] for row in campaign_comparable_rows
    ]
    horizon_ends = [run["forecastBinding"]["horizonEnd"] for run in comparable_runs] + [
        row["horizonEndsAt"] for row in campaign_comparable_rows
    ]
    campaign_summary = campaign_ledger_summary(
        campaign,
        ledger_case,
        from_local_ledger=from_local_ledger,
        ledger=ledger,
    )
    excluded_service_dates = sorted(
        [run["serviceDate"] for run in excluded_runs]
        + [row["serviceDate"] for row in campaign_excluded_rows]
    )
    calibration_summary = maybe_calibration_summary(corpus, calibration_status)
    gate = {
        "transitBaselineTrackRecordGateId": "transitbaselinetrackrecordgate-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "gateMode": "checked_fixture_plus_campaign_ledger" if campaign else "checked_fixture_gate",
        "sourceCorpus": {
            "transitForwardRunCorpusId": corpus["transitForwardRunCorpusId"],
            "corpusPath": rel(CORPUS_PATH),
            "corpusMode": corpus["corpusMode"],
            "policyId": policy["policyId"],
            "sourceCommand": "python3 scripts/ope.py transit-forward-run-corpus",
        },
        "campaignLedger": campaign_summary,
        "coverageSummary": {
            "network": corpus["corpusScope"]["network"],
            "geography": corpus["corpusScope"]["geography"],
            "serviceWindow": corpus["corpusScope"]["serviceWindow"],
            "horizonWindowCoverage": {
                "horizonStartsAt": min(horizon_starts),
                "horizonEndsAt": max(horizon_ends),
                "comparableWindowCount": len(comparable_runs) + len(campaign_comparable_rows),
                "excludedWindowCount": len(excluded_runs) + len(campaign_excluded_rows),
                "comparableServiceDates": sorted(run["serviceDate"] for run in comparable_runs)
                + sorted(row["serviceDate"] for row in campaign_comparable_rows),
                "excludedServiceDates": excluded_service_dates,
            },
        },
        "sampleSummary": {
            "resolvedComparableSampleSize": resolved_sample_size,
            "scoredSampleSize": summary["scoredCount"] + len(campaign_comparable_rows),
            "excludedSampleSize": summary["excludedCount"] + len(campaign_excluded_rows),
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
            "excludedSampleSize": summary["excludedCount"] + len(campaign_excluded_rows),
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
            "campaignLedgerCommand": campaign_summary["sourceCommand"],
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
            "Campaign ledgers are included only when --campaign is explicit; ignored local ledgers also require --from-local-ledger.",
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
    write_generated(OUTPUT_PATH, gate, label="transit baseline track-record gate", regen="python3 scripts/generate_transit_baseline_track_record_gate.py --write")


def check_gate(gate: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, gate, label="transit baseline track-record gate", regen="python3 scripts/generate_transit_baseline_track_record_gate.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--campaign", help="explicit campaign ledger id to include in the readback")
    parser.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="explicitly read the ignored local campaign evidence ledger",
    )
    parser.add_argument(
        "--ledger-case",
        choices=LEDGER_CASES,
        default=DEFAULT_LEDGER_CASE,
        help="checked campaign ledger case to include when --campaign is explicit",
    )
    args = parser.parse_args()
    if (args.write or args.check) and (args.campaign or args.from_local_ledger):
        raise SystemExit("--campaign and --from-local-ledger cannot be combined with --write or --check")
    try:
        gate = build_gate(
            campaign=args.campaign,
            ledger_case=args.ledger_case,
            from_local_ledger=args.from_local_ledger,
        )
        if args.write:
            write_gate(gate)
        elif args.check:
            check_gate(gate)
        else:
            sys.stdout.write(render_json(gate))
    except (OSError, json.JSONDecodeError, PredictionCampaignForecastWriteError, TransitBaselineTrackRecordGateError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
