#!/usr/bin/env python3
"""Unified per-predictor calibration store.

Both campaign runs and single forward-runs append their resolved outcome to one
append-only, dedup-by-rowKey store per predictor (keyed by domain). The store
recomputes the baseline track-record and calibration gate on every append, so a
predictor's claim boundary advances automatically as comparable resolved
outcomes accumulate toward the declared 30 (track record) / 100 (calibration)
thresholds. The thresholds are never lowered here; "automatic" means the
accumulation and recompute are automatic, not the claim.

Design posture, consistent with the rest of OPE:

- Pure standard library; all scoring math is reused from ``ope_scoring``.
- The store lives under ``.ope/live/calibration/<domain>/`` and is a local
  developer artifact, not a committed fixture (same posture as the campaign
  evidence ledger read by the track-record gate).
- Only comparable *scored* rows advance the sample size; excluded rows are kept
  for audit with an explicit reason code and never inflate the count.
- Recompute withholds calibration summaries below threshold, mirroring
  ``generate_transit_baseline_track_record_gate``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ope_scoring import baseline_lift, calibration_buckets, track_record_summary


ROOT = Path(__file__).resolve().parents[1]

STATE_TYPE = "ope_calibration_store"

# Declared evidence thresholds. These mirror the forward-run corpus policy
# (generate_transit_forward_run_corpus.build_corpus) and the campaign evidence
# ledger policy; the conformance check cross-asserts they stay in sync.
MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD = 30
MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION = 100

# Exclusion vocabulary shared with the forward-run corpus / track-record gate.
EXCLUSION_REASONS = {
    "ambiguous",
    "annulled",
    "low_coverage",
    "invalid_window",
    "feed_unavailable",
    "non_comparable",
}

NOT_ENOUGH = "not_enough_resolved_comparable_outcomes"
RUN_SOURCES = {"campaign", "single"}


class CalibrationStoreError(Exception):
    pass


def store_path_for(domain: str) -> Path:
    """Return the live store path for a predictor domain."""
    safe = domain.replace("/", "_").replace("..", "_")
    return ROOT / ".ope" / "live" / "calibration" / safe / "calibration-store.json"


def round_float(value: float | None, places: int = 10) -> float | None:
    if value is None:
        return None
    return round(value, places)


def status_for(sample_size: int, minimum: int) -> str:
    return "ready" if sample_size >= minimum else NOT_ENOUGH


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


def classify_exclusion_reason(reason: str | None) -> str:
    """Map a free-text resolver reason onto the shared exclusion vocabulary."""
    normalized = (reason or "").lower()
    if normalized in EXCLUSION_REASONS:
        return normalized
    if "missing_outcome" in normalized or "no declared" in normalized or "unavailable" in normalized:
        return "feed_unavailable"
    if "minimum" in normalized or "coverage" in normalized or "observation" in normalized:
        return "low_coverage"
    if "window" in normalized:
        return "invalid_window"
    if "annul" in normalized:
        return "annulled"
    if "ambig" in normalized:
        return "ambiguous"
    return "non_comparable"


def row_key(
    *,
    domain: str,
    run_id: str,
    forecast_id: str,
    scoring_report_id: str,
    row_kind: str,
    service_date: str = "",
    horizon_starts_at: str = "",
) -> str:
    # service_date + horizon_starts_at distinguish otherwise-identical runs: the
    # forward-run prototype reuses fixed ids (forecast-1201, etc.) across every
    # daily run, so keying on ids alone collapses a whole rolling series into one
    # deduplicated row. The per-run window makes each resolved run distinct while
    # still deduping a genuine re-record of the same run.
    raw = "|".join(
        [domain, str(run_id), str(forecast_id), str(scoring_report_id), row_kind, str(service_date), str(horizon_starts_at)]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def build_row(
    *,
    domain: str,
    run_source: str,
    run_id: str,
    question_id: str,
    forecast_id: str,
    scoring_report_id: str,
    service_date: str,
    service_window: str,
    horizon_starts_at: str,
    horizon_ends_at: str,
    forecast_probability: float,
    baseline_probability: float,
    score_status: str,
    primary_score: float | None = None,
    baseline_score: float | None = None,
    outcome_value: int | bool | None = None,
    observation_count: int = 0,
    late_count: int = 0,
    late_ratio: float = 0.0,
    exclusion_reason: str = "none",
) -> dict[str, Any]:
    """Build a calibration-store row from one resolved run's facts.

    A row is *comparable* only when the run was scored (a definite, in-window
    binary outcome under the declared resolution criteria). Anything else is
    kept as an excluded audit row carrying a shared-vocabulary reason code.
    """
    if run_source not in RUN_SOURCES:
        raise CalibrationStoreError(f"unknown run source: {run_source!r}")
    comparable = score_status == "scored"
    row_kind = "comparable" if comparable else "excluded"
    if comparable:
        if primary_score is None or baseline_score is None:
            raise CalibrationStoreError("scored comparable row requires primary and baseline scores")
        if outcome_value is None:
            raise CalibrationStoreError("scored comparable row requires a definite outcome value")
        reason_codes: list[str] = []
    else:
        reason_codes = [classify_exclusion_reason(exclusion_reason)]
    outcome_label = "unknown" if outcome_value is None else ("yes" if outcome_value else "no")
    return {
        "rowKind": row_kind,
        "rowKey": row_key(
            domain=domain,
            run_id=run_id,
            forecast_id=forecast_id,
            scoring_report_id=scoring_report_id,
            row_kind=row_kind,
            service_date=service_date,
            horizon_starts_at=horizon_starts_at,
        ),
        "runSource": run_source,
        "domain": domain,
        "runId": run_id,
        "questionId": question_id,
        "forecastId": forecast_id,
        "scoringReportId": scoring_report_id,
        "serviceDate": service_date,
        "serviceWindow": service_window,
        "horizonStartsAt": horizon_starts_at,
        "horizonEndsAt": horizon_ends_at,
        "forecastProbability": forecast_probability,
        "baselineProbability": baseline_probability,
        "outcomeLabel": outcome_label,
        "outcomeValue": None if outcome_value is None else int(bool(outcome_value)),
        "observationCount": observation_count,
        "lateCount": late_count,
        "lateRatio": late_ratio,
        "scoreStatus": score_status,
        "primaryScore": round_float(primary_score, 6),
        "baselineScore": round_float(baseline_score, 6),
        "reasonCodes": reason_codes,
        "comparable": comparable,
    }


def row_from_forward_run_state(state: dict[str, Any], *, run_source: str = "single") -> dict[str, Any]:
    """Build a calibration row from a resolved single forward-run state.

    Reads the well-known ``forward-run-state.json`` shape written by
    ``run_transit_delay_forward`` (and the route-scoped 24h ticker). A scored
    run becomes a comparable row; an ambiguous/blocked run becomes an excluded
    audit row with a reason code derived from the resolution stage.
    """
    forecast = state["forecastStage"]
    resolution = state.get("resolutionStage") or {}
    score = state.get("scoreStage") or {}
    horizon = forecast["horizon"]
    score_status = score.get("scoreStatus", "not_scored")
    outcome_label = resolution.get("outcomeLabel", "unknown")
    outcome_value: int | None
    if outcome_label == "yes":
        outcome_value = 1
    elif outcome_label == "no":
        outcome_value = 0
    else:
        outcome_value = None
    exclusion_reason = "none"
    if score_status != "scored":
        status = resolution.get("status", "")
        exclusion_reason = "ambiguous" if status == "ambiguous" else status or "non_comparable"
    return build_row(
        domain=state["domain"],
        run_source=run_source,
        run_id=state.get("forwardRunId", forecast["forecastId"]),
        question_id=forecast["questionId"],
        forecast_id=forecast["forecastId"],
        scoring_report_id=state.get("scoringReportId") or f"score-{forecast['forecastId']}",
        service_date=forecast["serviceDate"],
        service_window=forecast["serviceWindow"],
        horizon_starts_at=horizon["startsAt"],
        horizon_ends_at=horizon["endsAt"],
        forecast_probability=forecast["probability"],
        baseline_probability=forecast["baselineProbability"],
        score_status=score_status,
        primary_score=score.get("primaryScore"),
        baseline_score=score.get("baselineScore"),
        outcome_value=outcome_value,
        observation_count=resolution.get("observationCount", 0),
        late_count=resolution.get("lateCount", 0),
        late_ratio=resolution.get("lateRatio", 0.0),
        exclusion_reason=exclusion_reason,
    )


def row_from_campaign_ledger_row(ledger_row: dict[str, Any], domain: str) -> dict[str, Any]:
    """Project one campaign evidence-ledger row into a calibration-store row.

    The campaign path keeps its existing explicit ``prediction-campaign append``
    flow into the evidence ledger; this projects those audited rows into the
    unified per-predictor store so campaign and single runs calibrate the same
    predictor. Comparable ledger rows carry scores and a definite outcome;
    excluded rows carry an exclusion reason.
    """
    score_status = ledger_row.get("scoreStatus", "not_scored")
    score_status = "scored" if score_status == "scored" else "excluded"
    return build_row(
        domain=domain,
        run_source="campaign",
        run_id=ledger_row["runId"],
        question_id=ledger_row["questionId"],
        forecast_id=ledger_row["forecastId"],
        scoring_report_id=str(ledger_row.get("scoringReportId") or f"score-{ledger_row['forecastId']}"),
        service_date=ledger_row["serviceDate"],
        service_window=ledger_row["serviceWindow"],
        horizon_starts_at=ledger_row["horizonStartsAt"],
        horizon_ends_at=ledger_row["horizonEndsAt"],
        forecast_probability=ledger_row["forecastProbability"],
        baseline_probability=ledger_row["baselineProbability"],
        score_status=score_status,
        primary_score=ledger_row.get("primaryScore"),
        baseline_score=ledger_row.get("baselineScore"),
        outcome_value=ledger_row.get("outcomeValue"),
        observation_count=ledger_row.get("observationCount", 0),
        late_count=ledger_row.get("lateCount", 0),
        late_ratio=ledger_row.get("lateRatio", 0.0),
        exclusion_reason=str(ledger_row.get("exclusionReason") or "none"),
    )


def rows_from_campaign_ledger(ledger: dict[str, Any], domain: str) -> list[dict[str, Any]]:
    rows = ledger.get("comparableRows", []) + ledger.get("excludedRows", [])
    return [row_from_campaign_ledger_row(row, domain) for row in rows]


def empty_store(domain: str) -> dict[str, Any]:
    return {
        "stateType": STATE_TYPE,
        "domain": domain,
        "comparableRows": [],
        "excludedRows": [],
        "rowKeys": [],
    }


def load_store(path: Path, domain: str) -> dict[str, Any]:
    if not path.exists():
        return empty_store(domain)
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("stateType") != STATE_TYPE:
        raise CalibrationStoreError(f"calibration store state type mismatch: {path}")
    if state.get("domain") != domain:
        raise CalibrationStoreError(f"calibration store domain mismatch: {path}")
    state.setdefault("comparableRows", [])
    state.setdefault("excludedRows", [])
    state.setdefault("rowKeys", [])
    return state


def append_rows(store: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[int, int]:
    """Append rows, deduplicated by rowKey. Returns (appended, already_present)."""
    existing_keys = set(store.get("rowKeys", []))
    appended = 0
    already = 0
    for row in rows:
        if row["rowKey"] in existing_keys:
            already += 1
            continue
        bucket = "comparableRows" if row["rowKind"] == "comparable" else "excludedRows"
        store[bucket].append(row)
        existing_keys.add(row["rowKey"])
        appended += 1
    store["rowKeys"] = [r["rowKey"] for r in store["comparableRows"] + store["excludedRows"]]
    return appended, already


def save_store(path: Path, store: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def recompute_gate(
    store: dict[str, Any],
    *,
    horizon_bucket: str = "rolling-24h",
    generated_at: str = "1970-01-01T00:00:00Z",
) -> dict[str, Any]:
    """Recompute the predictor's track-record / calibration gate from the store.

    This is the automatic recompute: a pure function of the accumulated store,
    re-runnable after every append. It flips the claim flags exactly at the
    declared thresholds and withholds the calibration summary below threshold.
    """
    domain = store["domain"]
    comparable = store["comparableRows"]
    excluded = store["excludedRows"]
    n_comparable = len(comparable)

    track_status = status_for(n_comparable, MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD)
    calibration_status = status_for(n_comparable, MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION)

    scores = [r["primaryScore"] for r in comparable if r["primaryScore"] is not None]
    baseline_scores = [r["baselineScore"] for r in comparable if r["baselineScore"] is not None]
    reason_codes = [code for r in excluded for code in r["reasonCodes"]]

    performance = track_record_summary(
        domain=domain,
        horizon_bucket=horizon_bucket,
        output_type="binary",
        scoring_rule="brier",
        scores=scores,
        baseline_scores=baseline_scores,
        n_ambiguous=reason_codes.count("ambiguous"),
        n_annulled=reason_codes.count("annulled"),
        n_forecasts=n_comparable + len(excluded),
    )

    calibration_summary = None
    if calibration_status == "ready":
        pairs = [(r["forecastProbability"], bool(r["outcomeValue"])) for r in comparable]
        buckets = calibration_buckets(pairs, bucket_count=10)
        starts = [r["horizonStartsAt"] for r in comparable]
        ends = [r["horizonEndsAt"] for r in comparable]
        calibration_summary = {
            "domain": domain,
            "horizonBucket": horizon_bucket,
            "outputType": "binary",
            "coveragePeriod": {"startsAt": min(starts), "endsAt": max(ends)},
            "sampleSize": len(pairs),
            "expectedCalibrationError": round_float(expected_calibration_error(buckets, len(pairs))),
            "buckets": [
                {
                    "lowerProbability": round_float(b["lowerProbability"]),
                    "upperProbability": round_float(b["upperProbability"]),
                    "count": b["count"],
                    "meanForecastProbability": round_float(b["meanForecastProbability"]),
                    "observedFrequency": round_float(b["observedFrequency"]),
                }
                for b in buckets
            ],
        }

    return {
        "calibrationGateId": "calibrationgate-001",
        "generatedAt": generated_at,
        "gateMode": "live_calibration_store",
        "domain": domain,
        "storeSummary": {
            "comparableRowCount": n_comparable,
            "excludedRowCount": len(excluded),
            "campaignRowCount": sum(1 for r in comparable if r["runSource"] == "campaign"),
            "singleRowCount": sum(1 for r in comparable if r["runSource"] == "single"),
        },
        "sampleSummary": {
            "resolvedComparableSampleSize": n_comparable,
            "excludedSampleSize": len(excluded),
            "minimumComparableResolvedForTrackRecord": MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD,
            "minimumComparableResolvedForCalibration": MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION,
            "trackRecordStatus": track_status,
            "calibrationStatus": calibration_status,
        },
        "progress": {
            "towardTrackRecord": min(n_comparable, MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD),
            "remainingForTrackRecord": max(0, MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD - n_comparable),
            "towardCalibration": min(n_comparable, MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION),
            "remainingForCalibration": max(0, MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION - n_comparable),
        },
        "trackRecordSummary": {
            "summaryGenerated": True,
            "status": track_status,
            "scoringRule": "brier",
            "higherIsBetter": False,
            "primaryScore": round_float(performance["summary"]["primaryScore"]),
            "baselineScore": round_float(performance["summary"]["baselineScore"]),
            "baselineLift": round_float(performance["summary"]["baselineLift"]),
            "resolvedSampleSize": n_comparable,
        },
        "calibrationGate": {
            "summaryGenerated": calibration_summary is not None,
            "status": calibration_status,
            "reasonCode": "threshold_met" if calibration_summary is not None else calibration_status,
            "calibrationSummary": calibration_summary,
        },
        "claimBoundary": {
            "qualityClaimAllowed": track_status == "ready",
            "baselineTrackRecordAllowed": track_status == "ready",
            "calibrationClaimAllowed": calibration_status == "ready",
            "reasonCode": "threshold_met" if track_status == "ready" else track_status,
            "thresholdsLowered": False,
            "normalChecksUseLiveNetwork": False,
            "liveCapturesCommitted": False,
        },
    }


def append_resolved_run(
    *,
    domain: str,
    row: dict[str, Any],
    store_path: Path | None = None,
    horizon_bucket: str = "rolling-24h",
    generated_at: str = "1970-01-01T00:00:00Z",
) -> dict[str, Any]:
    """Append one resolved-run row to the predictor's store and recompute.

    Idempotent on rowKey: re-appending the same resolved run does not
    double-count. Returns the append result plus the freshly recomputed gate.
    """
    path = store_path or store_path_for(domain)
    store = load_store(path, domain)
    appended, already = append_rows(store, [row])
    save_store(path, store)
    gate = recompute_gate(store, horizon_bucket=horizon_bucket, generated_at=generated_at)
    return {
        "storePath": str(path),
        "appended": appended,
        "alreadyPresent": already,
        "gate": gate,
    }
