#!/usr/bin/env python3
"""Check the local transit forward-run resolver-agent fixture."""

from __future__ import annotations

from resolve_due_transit_forward_runs import build_report


class Args:
    live = False
    execute = False
    workspace = ".ope/live/transit-forward-run"
    run_state: list[str] = []
    now = None
    limit = 50
    trip_updates = None
    input_protobuf = None
    static_gtfs = None
    download_static_gtfs = False
    timeout = None
    max_bytes = None
    static_gtfs_max_bytes = None


def main() -> None:
    report = build_report(Args())
    summary = report["scanSummary"]
    decisions = {item["decision"]: item for item in report["runDecisions"]}
    boundary = report["executionBoundary"]

    if report["runMode"] != "fixture_scan" or report["executionMode"] != "dry_run":
        raise AssertionError("resolver fixture should be an offline dry run")
    if summary["scannedCount"] != 3:
        raise AssertionError("resolver fixture should scan three representative states")
    if summary["dueCount"] != 1 or summary["notDueCount"] != 1 or summary["alreadyResolvedCount"] != 1:
        raise AssertionError("resolver fixture should classify due, not-due, and already-resolved states")
    if summary["executedCount"] != 0 or boundary["resolverCommandsExecuted"]:
        raise AssertionError("resolver fixture must not execute commands")
    if boundary["sourceFetchPerformed"] or boundary["resolvedArtifactsCreated"]:
        raise AssertionError("resolver fixture must not fetch sources or create resolution artifacts")
    if boundary["calibrationClaimAllowed"]:
        raise AssertionError("resolver must keep calibration claims blocked")
    if "--phase resolve" not in decisions["due_pending"]["command"]:
        raise AssertionError("due pending state should expose the checked resolve command")
    if "dry-run only" not in decisions["due_pending"]["notes"][0]:
        raise AssertionError("due pending state should explain execute is required")
    print("checked transit forward-run resolver")


if __name__ == "__main__":
    main()
