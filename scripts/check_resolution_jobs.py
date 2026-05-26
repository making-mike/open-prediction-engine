#!/usr/bin/env python3
"""Check the agent-facing resolution job registry."""

from __future__ import annotations

from generate_resolution_jobs import build_registry


class Args:
    live = False
    workspace = ".ope/live/transit-forward-run"
    run_state: list[str] = []
    now = None
    limit = 50


def main() -> None:
    registry = build_registry(Args())
    summary = registry["summary"]
    jobs = {job["jobStatus"]: job for job in registry["jobs"]}
    if registry["registryMode"] != "fixture_registry":
        raise AssertionError("resolution job registry should default to fixture mode")
    if summary["jobCount"] != 3:
        raise AssertionError("resolution job registry should expose three fixture jobs")
    if summary["pendingDueCount"] != 1 or summary["pendingNotDueCount"] != 1:
        raise AssertionError("resolution job registry should expose due and not-due pending jobs")
    if summary["alreadyResolvedCount"] != 1:
        raise AssertionError("resolution job registry should expose one already-resolved job")
    if jobs["pending_due"]["agentAction"]["recommendedAction"] != "call_resolver_execute":
        raise AssertionError("due resolution job should route agents to resolver execution")
    if jobs["pending_not_due"]["agentAction"]["recommendedAction"] != "wait":
        raise AssertionError("not-due resolution job should tell agents to wait")
    if registry["executionBoundary"]["registryExecutesResolvers"]:
        raise AssertionError("resolution job registry must not execute resolver commands")
    if registry["executionBoundary"]["calibrationClaimAllowed"]:
        raise AssertionError("resolution job registry must keep calibration claims blocked")
    print("checked resolution jobs")


if __name__ == "__main__":
    main()
