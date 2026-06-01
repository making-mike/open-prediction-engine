#!/usr/bin/env python3
"""Check the weather-transit-delay baseline track-record and calibration gate."""

from __future__ import annotations

from generate_transit_baseline_track_record_gate import build_gate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    gate = build_gate()
    samples = gate["sampleSummary"]
    track = gate["trackRecordSummary"]
    calibration = gate["calibrationGate"]
    coverage = gate["coverageSummary"]["horizonWindowCoverage"]
    campaign_ledger = gate["campaignLedger"]
    boundary = gate["claimBoundary"]
    read_surface = gate["readSurface"]

    require(gate["gateMode"] == "checked_fixture_gate", "gate should be a checked fixture read model")
    require(campaign_ledger["included"] is False, "default gate should not include campaign ledger rows")
    require(samples["resolvedComparableSampleSize"] == 1, "gate should expose one comparable resolved run")
    require(samples["scoredSampleSize"] == 1, "gate should expose one scored run")
    require(samples["excludedSampleSize"] == 6, "gate should expose six excluded runs")
    require(samples["pendingSampleSize"] == 0, "fixture gate should have no pending runs")
    require(samples["minimumComparableResolvedForTrackRecord"] == 30, "track-record threshold should remain 30")
    require(samples["minimumComparableResolvedForCalibration"] == 100, "calibration threshold should remain 100")
    require(
        samples["trackRecordStatus"] == "not_enough_resolved_comparable_outcomes",
        "one comparable run should not unlock a baseline track record",
    )
    require(
        samples["calibrationStatus"] == "not_enough_resolved_comparable_outcomes",
        "one comparable run should not unlock calibration",
    )

    require(track["summaryGenerated"] is True, "gate should generate a bounded track-record summary")
    require(track["status"] == samples["trackRecordStatus"], "track summary should preserve below-threshold status")
    require(track["scoringRule"] == "brier", "track summary should use Brier score")
    require(track["higherIsBetter"] is False, "Brier score should preserve lower-is-better convention")
    require(track["primaryScore"] == 0.4489, "track summary should expose the fixture Brier score")
    require(track["baselineScore"] == 0.5625, "track summary should expose the baseline Brier score")
    require(track["baselineLift"] == 0.1136, "track summary should expose baseline lift")
    require(track["resolvedSampleSize"] == 1, "track summary should expose resolved sample size")
    require(track["excludedSampleSize"] == 6, "track summary should expose excluded sample size")
    require(len(track["scoreRows"]) == 1, "track summary should include one scored row")
    require(track["scoreRows"][0]["outcomeLabel"] == "yes", "score row should preserve the resolved outcome")

    require(coverage["comparableWindowCount"] == 1, "coverage should expose one comparable horizon window")
    require(coverage["excludedWindowCount"] == 6, "coverage should expose six excluded windows")
    require(coverage["comparableServiceDates"] == ["2026-06-10"], "coverage should preserve comparable service date")
    require(coverage["horizonStartsAt"] == "2026-06-10T03:00:00Z", "coverage should preserve horizon start")
    require(coverage["horizonEndsAt"] == "2026-06-10T07:00:00Z", "coverage should preserve horizon end")

    require(calibration["summaryGenerated"] is False, "below-threshold gate must not generate calibration summaries")
    require(calibration["calibrationSummary"] is None, "below-threshold gate must not attach calibration summary")
    require(
        calibration["reasonCode"] == "not_enough_resolved_comparable_outcomes",
        "below-threshold calibration reason should be explicit",
    )

    require(boundary["qualityClaimAllowed"] is False, "gate should block quality claims below threshold")
    require(boundary["baselineTrackRecordAllowed"] is False, "gate should block track-record claims below threshold")
    require(boundary["calibrationClaimAllowed"] is False, "gate should block calibration claims below threshold")
    require(
        boundary["oneOffForwardRunCanCreateCalibrationEvidence"] is False,
        "one-off forward runs must not create calibration evidence",
    )
    require(boundary["normalChecksUseLiveNetwork"] is False, "normal checks should remain offline")
    require(boundary["liveCapturesCommitted"] is False, "live captures should remain ignored and local")

    require(not read_surface["createsForecastArtifacts"], "gate must not create forecast artifacts")
    require(not read_surface["createsResolutionArtifacts"], "gate must not create resolution artifacts")
    require(not read_surface["createsScoringRecords"], "gate must not create scoring records")
    require(
        not read_surface["createsCalibrationSummariesBelowThreshold"],
        "gate must not create below-threshold calibration summaries",
    )
    require(not read_surface["fetchesLiveData"], "gate must not fetch live data")
    require(not read_surface["storesCredentials"], "gate must not store credentials")

    campaign_gate = build_gate(campaign="predictioncampaign-001")
    campaign_samples = campaign_gate["sampleSummary"]
    campaign_coverage = campaign_gate["coverageSummary"]["horizonWindowCoverage"]
    campaign_ledger = campaign_gate["campaignLedger"]
    require(
        campaign_gate["gateMode"] == "checked_fixture_plus_campaign_ledger",
        "campaign gate should declare explicit campaign-ledger mode",
    )
    require(campaign_ledger["included"] is True, "campaign gate should include campaign ledger rows")
    require(campaign_ledger["excludedRowCount"] == 1, "campaign gate should include one excluded campaign row")
    require(
        campaign_samples["resolvedComparableSampleSize"] == 1,
        "excluded-only campaign ledger must not increase comparable sample size",
    )
    require(campaign_samples["excludedSampleSize"] == 7, "campaign gate should include campaign exclusion rows")
    require(
        campaign_coverage["excludedServiceDates"].count("2026-06-11") == 2,
        "campaign gate should include campaign excluded service date",
    )

    comparable_campaign_gate = build_gate(campaign="predictioncampaign-001", ledger_case="comparable_scored")
    comparable_samples = comparable_campaign_gate["sampleSummary"]
    comparable_track = comparable_campaign_gate["trackRecordSummary"]
    comparable_ledger = comparable_campaign_gate["campaignLedger"]
    require(comparable_ledger["comparableRowCount"] == 1, "comparable campaign gate should include one campaign row")
    require(comparable_samples["resolvedComparableSampleSize"] == 2, "comparable campaign gate should increase sample size")
    require(len(comparable_track["scoreRows"]) == 2, "comparable campaign gate should include campaign score row")
    require(
        comparable_campaign_gate["claimBoundary"]["calibrationClaimAllowed"] is False,
        "campaign ledger below threshold must not unlock calibration claims",
    )
    print("checked transit baseline track-record gate")


if __name__ == "__main__":
    main()
