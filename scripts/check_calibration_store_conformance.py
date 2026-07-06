#!/usr/bin/env python3
"""Conformance check for automatic per-run calibration.

Feeds synthetic resolved runs through the REAL calibration_store append +
recompute code (no mocking of the scoring math) and asserts that a predictor's
claim boundary advances automatically and only at the declared thresholds:

  - below 30 comparable resolved: no claims, explicit not-enough status
  - at >= 30: baseline track-record + quality claims unlock; calibration still blocked
  - at >= 100: calibration claim unlocks with a generated calibration summary
  - dedup: re-appending the same resolved run never double-counts
  - exclusions: ambiguous / low-coverage / etc. rows never advance the count

Also cross-checks that the store thresholds stay in sync with the forward-run
corpus policy, so the two surfaces cannot silently diverge.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import calibration_store as cs
from generate_transit_forward_run_corpus import build_corpus


DOMAIN = "weather-transit-delays"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def scored_row(index: int, *, source: str = "single") -> dict:
    """A deterministic, well-spread scored comparable row.

    Probabilities sweep the unit interval so calibration buckets are populated,
    and the outcome roughly tracks the forecast so the summary is meaningful.
    """
    probability = 0.05 + (index % 19) * 0.05
    probability = min(0.95, probability)
    outcome = 1 if (index % 10) < round(probability * 10) else 0
    primary = cs.round_float((probability - outcome) ** 2, 6)
    baseline = cs.round_float((0.25 - outcome) ** 2, 6)
    return cs.build_row(
        domain=DOMAIN,
        run_source=source,
        run_id=f"run-{index:04d}",
        question_id=f"question-{index:04d}",
        forecast_id=f"forecast-{index:04d}",
        scoring_report_id=f"scoring-{index:04d}",
        service_date="2026-06-11",
        service_window="rolling-24h",
        horizon_starts_at="2026-06-11T13:42:09Z",
        horizon_ends_at="2026-06-12T13:42:09Z",
        forecast_probability=probability,
        baseline_probability=0.25,
        score_status="scored",
        primary_score=primary,
        baseline_score=baseline,
        outcome_value=outcome,
        observation_count=900,
        late_count=outcome * 200,
        late_ratio=0.22 if outcome else 0.03,
    )


def excluded_row(index: int, reason: str) -> dict:
    return cs.build_row(
        domain=DOMAIN,
        run_source="campaign",
        run_id=f"exrun-{index:04d}",
        question_id=f"question-ex-{index:04d}",
        forecast_id=f"forecast-ex-{index:04d}",
        scoring_report_id=f"scoring-ex-{index:04d}",
        service_date="2026-06-13",
        service_window="rolling-24h",
        horizon_starts_at="2026-06-13T13:42:09Z",
        horizon_ends_at="2026-06-14T13:42:09Z",
        forecast_probability=0.4,
        baseline_probability=0.25,
        score_status="excluded",
        exclusion_reason=reason,
    )


def fresh_store_path(tmp: Path) -> Path:
    return tmp / "calibration-store.json"


def assert_below_threshold(gate: dict, n: int) -> None:
    samples = gate["sampleSummary"]
    boundary = gate["claimBoundary"]
    require(samples["resolvedComparableSampleSize"] == n, f"expected {n} comparable, got {samples['resolvedComparableSampleSize']}")
    require(samples["trackRecordStatus"] == cs.NOT_ENOUGH, "below-threshold track record must be explicit not-enough")
    require(samples["calibrationStatus"] == cs.NOT_ENOUGH, "below-threshold calibration must be explicit not-enough")
    require(boundary["qualityClaimAllowed"] is False, "below-threshold gate must block quality claims")
    require(boundary["baselineTrackRecordAllowed"] is False, "below-threshold gate must block track-record claims")
    require(boundary["calibrationClaimAllowed"] is False, "below-threshold gate must block calibration claims")
    require(gate["calibrationGate"]["calibrationSummary"] is None, "below-threshold gate must withhold calibration summary")


def test_thresholds_in_sync_with_corpus() -> None:
    corpus = build_corpus()
    policy = corpus["comparableWindowPolicy"]
    require(
        cs.MINIMUM_COMPARABLE_RESOLVED_FOR_TRACK_RECORD == policy["minimumComparableResolvedForTrackRecord"],
        "store track-record threshold drifted from corpus policy",
    )
    require(
        cs.MINIMUM_COMPARABLE_RESOLVED_FOR_CALIBRATION == policy["minimumComparableResolvedForCalibration"],
        "store calibration threshold drifted from corpus policy",
    )
    require(cs.EXCLUSION_REASONS == set(policy["excludedReasonCodes"]), "store exclusion vocabulary drifted from corpus policy")


def test_thresholds_flip_automatically() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))

        # Empty predictor: no evidence, no claims.
        gate = cs.recompute_gate(cs.load_store(path, DOMAIN))
        assert_below_threshold(gate, 0)

        last_gate = None
        for index in range(1, 30):
            result = cs.append_resolved_run(domain=DOMAIN, row=scored_row(index), store_path=path)
            last_gate = result["gate"]
            require(result["appended"] == 1, f"row {index} should append exactly once")
        assert_below_threshold(last_gate, 29)

        # The 30th comparable resolved run unlocks the baseline track record.
        result = cs.append_resolved_run(domain=DOMAIN, row=scored_row(30), store_path=path)
        gate = result["gate"]
        samples = gate["sampleSummary"]
        boundary = gate["claimBoundary"]
        require(samples["resolvedComparableSampleSize"] == 30, "30th run should reach the track-record threshold")
        require(samples["trackRecordStatus"] == "ready", "track record should be ready at 30")
        require(boundary["baselineTrackRecordAllowed"] is True, "track-record claim should unlock at 30")
        require(boundary["qualityClaimAllowed"] is True, "quality claim should unlock at 30")
        require(boundary["calibrationClaimAllowed"] is False, "calibration must stay blocked at 30")
        require(gate["calibrationGate"]["calibrationSummary"] is None, "calibration summary must stay withheld at 30")
        require(gate["trackRecordSummary"]["primaryScore"] is not None, "track-record Brier score should be computed at 30")

        for index in range(31, 100):
            result = cs.append_resolved_run(domain=DOMAIN, row=scored_row(index), store_path=path)
        require(result["gate"]["claimBoundary"]["calibrationClaimAllowed"] is False, "calibration must stay blocked at 99")

        # The 100th comparable resolved run unlocks calibration.
        result = cs.append_resolved_run(domain=DOMAIN, row=scored_row(100), store_path=path)
        gate = result["gate"]
        require(gate["sampleSummary"]["resolvedComparableSampleSize"] == 100, "100th run should reach the calibration threshold")
        require(gate["sampleSummary"]["calibrationStatus"] == "ready", "calibration should be ready at 100")
        require(gate["claimBoundary"]["calibrationClaimAllowed"] is True, "calibration claim should unlock at 100")
        summary = gate["calibrationGate"]["calibrationSummary"]
        require(summary is not None, "calibration summary should be generated at 100")
        require(summary["sampleSize"] == 100, "calibration summary sample size should be 100")
        require(len(summary["buckets"]) == 10, "calibration summary should expose ten buckets")
        require(sum(b["count"] for b in summary["buckets"]) == 100, "calibration buckets should cover every sample")
        require(summary["expectedCalibrationError"] is not None, "calibration summary should expose an ECE")


def test_dedup_does_not_double_count() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))
        first = cs.append_resolved_run(domain=DOMAIN, row=scored_row(1), store_path=path)
        require(first["appended"] == 1 and first["alreadyPresent"] == 0, "first append should add the row")
        again = cs.append_resolved_run(domain=DOMAIN, row=scored_row(1), store_path=path)
        require(again["appended"] == 0 and again["alreadyPresent"] == 1, "re-appending the same run must be a no-op")
        require(
            again["gate"]["sampleSummary"]["resolvedComparableSampleSize"] == 1,
            "dedup must keep the comparable sample size at one",
        )


def test_exclusions_never_advance_the_count() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))
        reasons = sorted(cs.EXCLUSION_REASONS)
        gate = None
        for index, reason in enumerate(reasons, 1):
            result = cs.append_resolved_run(domain=DOMAIN, row=excluded_row(index, reason), store_path=path)
            gate = result["gate"]
            require(result["appended"] == 1, f"excluded row {reason} should append for audit")
        require(gate["sampleSummary"]["resolvedComparableSampleSize"] == 0, "excluded rows must not advance comparable count")
        require(gate["sampleSummary"]["excludedSampleSize"] == len(reasons), "every excluded row should be retained for audit")
        require(gate["claimBoundary"]["qualityClaimAllowed"] is False, "exclusions alone must not unlock any claim")

        store = cs.load_store(path, DOMAIN)
        seen = {code for row in store["excludedRows"] for code in row["reasonCodes"]}
        require(seen == cs.EXCLUSION_REASONS, f"excluded rows should cover every reason code, saw {seen}")


def test_mixed_sources_share_one_predictor() -> None:
    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))
        cs.append_resolved_run(domain=DOMAIN, row=scored_row(1, source="single"), store_path=path)
        result = cs.append_resolved_run(domain=DOMAIN, row=scored_row(2, source="campaign"), store_path=path)
        store_summary = result["gate"]["storeSummary"]
        require(store_summary["comparableRowCount"] == 2, "both single and campaign runs should land in one store")
        require(store_summary["singleRowCount"] == 1, "single-run source should be tracked")
        require(store_summary["campaignRowCount"] == 1, "campaign-run source should be tracked")


def test_campaign_ledger_projection() -> None:
    ledger = {
        "comparableRows": [
            {
                "runId": "predictionrun-1302",
                "questionId": "question-1302",
                "forecastId": "forecast-1302",
                "scoringReportId": "scoring-1302",
                "serviceDate": "2026-06-12",
                "serviceWindow": "morning_peak",
                "horizonStartsAt": "2026-06-12T04:00:00Z",
                "horizonEndsAt": "2026-06-12T07:00:00Z",
                "forecastProbability": 0.46,
                "baselineProbability": 0.25,
                "outcomeLabel": "no",
                "outcomeValue": 0,
                "observationCount": 40,
                "lateCount": 3,
                "lateRatio": 0.075,
                "scoreStatus": "scored",
                "primaryScore": 0.2116,
                "baselineScore": 0.0625,
                "exclusionReason": "none",
            }
        ],
        "excludedRows": [
            {
                "runId": "predictionrun-1303",
                "questionId": "question-1303",
                "forecastId": "forecast-1303",
                "scoringReportId": "none",
                "serviceDate": "2026-06-13",
                "serviceWindow": "morning_peak",
                "horizonStartsAt": "2026-06-13T04:00:00Z",
                "horizonEndsAt": "2026-06-13T07:00:00Z",
                "forecastProbability": 0.4,
                "baselineProbability": 0.25,
                "outcomeLabel": "unknown",
                "outcomeValue": None,
                "scoreStatus": "not_scored",
                "exclusionReason": "missing_outcome",
            }
        ],
    }
    rows = cs.rows_from_campaign_ledger(ledger, DOMAIN)
    require(len(rows) == 2, "projection should yield one row per ledger row")
    comparable = [r for r in rows if r["comparable"]]
    excluded = [r for r in rows if not r["comparable"]]
    require(len(comparable) == 1 and comparable[0]["runSource"] == "campaign", "scored ledger row should project to a comparable campaign row")
    require(comparable[0]["primaryScore"] == 0.2116, "projection should carry the campaign Brier score")
    require(len(excluded) == 1 and excluded[0]["reasonCodes"] == ["feed_unavailable"], "missing_outcome should map to feed_unavailable")

    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))
        cs.append_resolved_run(domain=DOMAIN, row=scored_row(1, source="single"), store_path=path)
        store = cs.load_store(path, DOMAIN)
        cs.append_rows(store, rows)
        cs.save_store(path, store)
        gate = cs.recompute_gate(store)
        require(gate["storeSummary"]["comparableRowCount"] == 2, "campaign + single comparable rows should share the predictor store")
        require(gate["storeSummary"]["campaignRowCount"] == 1, "campaign comparable row should be counted")
        require(gate["storeSummary"]["singleRowCount"] == 1, "single comparable row should be counted")
        require(gate["sampleSummary"]["excludedSampleSize"] == 1, "projected excluded row should be retained for audit")


def test_reused_ids_distinct_windows_not_deduped() -> None:
    """Regression: the forward-run prototype reuses fixed ids across every daily
    run. Runs that share ids but cover different service dates must each count;
    only a genuine re-record of the same run deduplicates."""
    def prototype_row(service_date: str, horizon_start: str) -> dict:
        return cs.build_row(
            domain=DOMAIN,
            run_source="single",
            run_id="transitdelayforwardrun-001",   # identical across runs (the bug's trigger)
            question_id="question-1201",
            forecast_id="forecast-1201",
            scoring_report_id="score-forecast-1201",
            service_date=service_date,
            service_window="rolling-24h",
            horizon_starts_at=horizon_start,
            horizon_ends_at="2026-06-30T00:00:00Z",
            forecast_probability=0.2,
            baseline_probability=0.2,
            score_status="scored",
            primary_score=0.04,
            baseline_score=0.04,
            outcome_value=0,
        )

    with tempfile.TemporaryDirectory() as raw:
        path = fresh_store_path(Path(raw))
        cs.append_resolved_run(domain=DOMAIN, row=prototype_row("2026-06-18", "2026-06-18T21:00:00Z"), store_path=path)
        r2 = cs.append_resolved_run(domain=DOMAIN, row=prototype_row("2026-06-19", "2026-06-19T21:00:00Z"), store_path=path)
        require(r2["gate"]["sampleSummary"]["resolvedComparableSampleSize"] == 2, "same-id runs on different dates must both count")
        # re-recording the 06-18 run is still an idempotent no-op
        r3 = cs.append_resolved_run(domain=DOMAIN, row=prototype_row("2026-06-18", "2026-06-18T21:00:00Z"), store_path=path)
        require(r3["appended"] == 0, "re-recording the same run must still dedupe")
        require(r3["gate"]["sampleSummary"]["resolvedComparableSampleSize"] == 2, "dedupe must not drop the distinct run")


def main() -> None:
    test_thresholds_in_sync_with_corpus()
    test_thresholds_flip_automatically()
    test_dedup_does_not_double_count()
    test_exclusions_never_advance_the_count()
    test_mixed_sources_share_one_predictor()
    test_campaign_ledger_projection()
    test_reused_ids_distinct_windows_not_deduped()
    print("checked calibration store conformance")


if __name__ == "__main__":
    main()
