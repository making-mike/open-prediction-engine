#!/usr/bin/env python3
"""Check prediction campaign resume readback semantics."""

from __future__ import annotations

from generate_prediction_campaign_resume import build_prediction_campaign_resume


def main() -> None:
    resume = build_prediction_campaign_resume()
    if resume["resumeStatus"] != "checked_resume_plan_non_mutating":
        raise AssertionError("prediction campaign resume status drifted")
    if resume["observedState"]["sourceKind"] != "checked_fixture_bundle":
        raise AssertionError("prediction campaign resume should use checked fixture inputs")
    if resume["observedState"]["liveStateRead"]:
        raise AssertionError("prediction campaign resume must not read ignored live state in normal checks")
    if not resume["observedState"]["forecastWritePlanReady"]:
        raise AssertionError("prediction campaign resume should see the forecast-write plan")
    if resume["observedState"]["priorEvidenceOverwriteAllowed"]:
        raise AssertionError("prediction campaign resume must not allow overwriting prior evidence")
    if resume["summary"]["effectfulResumeImplemented"]:
        raise AssertionError("prediction campaign resume should remain non-effectful")
    if resume["executionBoundary"]["writesIgnoredLiveState"] or resume["executionBoundary"]["executesResolvers"]:
        raise AssertionError("prediction campaign resume must not write state or execute resolvers")
    blocked = [action for action in resume["recoveryActions"] if action["actionStatus"] == "blocked"]
    if not blocked:
        raise AssertionError("prediction campaign resume should block future effectful write until implemented")
    if any(action["mutatesState"] or action["executesResolver"] for action in resume["recoveryActions"]):
        raise AssertionError("prediction campaign resume recovery actions must stay read-only")
    print("checked prediction campaign resume")


if __name__ == "__main__":
    main()
