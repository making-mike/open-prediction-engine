#!/usr/bin/env python3
"""Check the weather-transit-delay forward-run workflow fixture."""

from __future__ import annotations

from run_transit_delay_forward import fixture_forward_run


def main() -> None:
    summary = fixture_forward_run()
    forecast = summary["forecastStage"]
    resolution = summary["resolutionStage"]
    score = summary["scoreStage"]
    claims = summary["claimBoundary"]

    if summary["domain"] != "weather-transit-delays":
        raise AssertionError("forward run should use the transit delay domain")
    if summary["runMode"] != "fixture_replay" or summary["runStatus"] != "scored":
        raise AssertionError("fixture forward run should complete through scoring")
    if forecast["forecastedAt"] > forecast["closeAt"]:
        raise AssertionError("forward run forecast must be recorded before close")
    if forecast["probability"] <= forecast["baselineProbability"]:
        raise AssertionError("fixture forward run should lift above baseline")
    if resolution["status"] != "resolved" or resolution["outcomeLabel"] != "yes":
        raise AssertionError("fixture forward run should resolve to a Yes outcome")
    if score["scoreStatus"] != "scored" or score["baselineLift"] <= 0:
        raise AssertionError("fixture forward run should score with positive baseline lift")
    if claims["qualityClaimAllowed"] or claims["calibrationClaimAllowed"]:
        raise AssertionError("forward run must keep quality and calibration claims blocked")
    if claims["resolvedComparableOutcomes"] != 1:
        raise AssertionError("fixture forward run should expose exactly one comparable resolved outcome")
    if "append more comparable forward runs" not in summary["nextAction"]:
        raise AssertionError("forward run should require more comparable outcomes before stronger claims")
    print("checked transit delay forward run")


if __name__ == "__main__":
    main()
