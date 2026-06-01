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
    if resume["observedState"]["localRunStateCount"] != 0:
        raise AssertionError("prediction campaign resume should not see local run state in normal checks")
    if not resume["observedState"]["forecastWritePlanReady"]:
        raise AssertionError("prediction campaign resume should see the forecast-write plan")
    if resume["observedState"]["priorEvidenceOverwriteAllowed"]:
        raise AssertionError("prediction campaign resume must not allow overwriting prior evidence")
    if resume["summary"]["localResumeReadbackImplemented"]:
        raise AssertionError("default prediction campaign resume should not claim local resume readback")
    if resume["summary"]["effectfulResumeImplemented"]:
        raise AssertionError("prediction campaign resume should remain non-effectful")
    if resume["executionBoundary"]["writesIgnoredLiveState"] or resume["executionBoundary"]["executesResolvers"]:
        raise AssertionError("prediction campaign resume must not write state or execute resolvers")
    blocked = [action for action in resume["recoveryActions"] if action["actionStatus"] == "blocked"]
    if not blocked:
        raise AssertionError("prediction campaign resume should block future effectful write until implemented")
    if any(action["mutatesState"] or action["executesResolver"] for action in resume["recoveryActions"]):
        raise AssertionError("prediction campaign resume recovery actions must stay read-only")

    interrupted = build_prediction_campaign_resume(case="interrupted_after_forecast_write")
    if interrupted["resumeStatus"] != "local_resume_readback":
        raise AssertionError("interrupted prediction campaign resume should expose local readback status")
    if interrupted["observedState"]["sourceKind"] != "simulated_interrupted_campaign_state":
        raise AssertionError("interrupted prediction campaign resume source kind drifted")
    if interrupted["observedState"]["localRunStateCount"] != 1:
        raise AssertionError("interrupted prediction campaign resume should find one run state")
    if interrupted["observedState"]["createdRunIdempotencyKeyCount"] != 1:
        raise AssertionError("interrupted prediction campaign resume should preserve one idempotency key")
    if not interrupted["observedState"]["interruptedRunStateFound"]:
        raise AssertionError("interrupted prediction campaign resume should detect run state")
    if interrupted["observedState"]["priorEvidenceOverwriteAllowed"]:
        raise AssertionError("interrupted prediction campaign resume must not allow overwriting prior evidence")
    if not interrupted["summary"]["localResumeReadbackImplemented"]:
        raise AssertionError("interrupted prediction campaign resume should claim local resume readback")
    if interrupted["summary"]["effectfulResumeImplemented"]:
        raise AssertionError("interrupted prediction campaign resume should remain non-effectful")
    if interrupted["executionBoundary"]["writesIgnoredLiveState"] or interrupted["executionBoundary"]["executesResolvers"]:
        raise AssertionError("interrupted prediction campaign resume must not write state or execute resolvers")
    continuation_actions = [
        action for action in interrupted["recoveryActions"] if action["mutatesState"] and not action["executesResolver"]
    ]
    if len(continuation_actions) != 1:
        raise AssertionError("interrupted prediction campaign resume should expose one explicit continuation action")
    print("checked prediction campaign resume")


if __name__ == "__main__":
    main()
