#!/usr/bin/env python3
"""Check the weather-transit-delay forward-run corpus index."""

from __future__ import annotations

from generate_transit_forward_run_corpus import EXCLUSION_REASONS, build_corpus


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    corpus = build_corpus()
    summary = corpus["summary"]
    policy = corpus["comparableWindowPolicy"]
    comparable_runs = corpus["comparableRuns"]
    excluded_runs = corpus["excludedRuns"]
    boundary = corpus["claimBoundary"]
    read_surface = corpus["readSurface"]

    require(corpus["corpusMode"] == "checked_fixture_index", "corpus should be a checked fixture index")
    require(summary["corpusCount"] == 7, "corpus should expose one comparable run plus six excluded examples")
    require(summary["comparableResolvedCount"] == 1, "corpus should expose one comparable resolved run")
    require(summary["scoredCount"] == 1, "corpus should expose one scored run")
    require(summary["excludedCount"] == 6, "corpus should expose six excluded examples")
    require(summary["pendingCount"] == 0, "fixture corpus should not include pending runs")
    require(policy["minimumComparableResolvedForTrackRecord"] == 30, "track-record threshold should be 30 comparable runs")
    require(policy["minimumComparableResolvedForCalibration"] == 100, "calibration threshold should be 100 comparable runs")
    require(set(policy["excludedReasonCodes"]) == EXCLUSION_REASONS, "policy should declare all exclusion reasons")
    require(
        set(run["exclusionReason"] for run in excluded_runs) == EXCLUSION_REASONS,
        "excluded rows should cover every required reason",
    )

    run = comparable_runs[0]
    require(run["runStatus"] == "scored", "comparable run should be scored")
    require(run["forecastBinding"]["forecastBeforeClose"] is True, "comparable run must forecast before close")
    require(run["resolutionBinding"]["resolvedAfterHorizon"] is True, "comparable run must resolve after horizon")
    require(run["resolutionBinding"]["observationCount"] >= corpus["corpusScope"]["minimumObservationCount"], "comparable run should meet coverage")
    require(run["scoreBinding"]["scoreStatus"] == "scored", "comparable run should bind scored report")
    require(run["scoreBinding"]["baselineLift"] > 0, "fixture comparable run should beat the baseline")
    require(run["comparability"]["comparable"] is True, "comparable run should be marked comparable")
    require(run["comparability"]["reasonCodes"] == [], "comparable run should have no exclusion reasons")

    require(boundary["qualityClaimAllowed"] is False, "corpus should block quality claims")
    require(boundary["calibrationClaimAllowed"] is False, "corpus should block calibration claims")
    require(boundary["baselineTrackRecordAllowed"] is False, "corpus should block track-record claims below threshold")
    require(boundary["normalChecksUseLiveNetwork"] is False, "normal corpus checks should not use live network")
    require(boundary["liveCapturesCommitted"] is False, "corpus should not commit local live captures")
    require(boundary["resolvedComparableOutcomes"] == 1, "claim boundary should expose one comparable outcome")

    require(not read_surface["createsForecastArtifacts"], "corpus read surface must not create forecasts")
    require(not read_surface["createsResolutionArtifacts"], "corpus read surface must not create resolutions")
    require(not read_surface["createsScoringRecords"], "corpus read surface must not create scores")
    require(not read_surface["fetchesLiveData"], "corpus read surface must not fetch live data")
    require(not read_surface["storesCredentials"], "corpus read surface must not store credentials")
    print("checked transit forward-run corpus")


if __name__ == "__main__":
    main()
