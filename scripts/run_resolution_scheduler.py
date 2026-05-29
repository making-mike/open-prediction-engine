#!/usr/bin/env python3
"""Run a local terminal scheduler for due resolution jobs."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import generate_resolution_jobs
import resolve_due_transit_forward_runs as resolver
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "resolution-scheduler"
OUTPUT_PATH = GENERATED / "resolution-scheduler-run.generated.json"
CAMPAIGN_OUTPUT_PATH = GENERATED / "resolution-scheduler-campaign-run.generated.json"
SCHEMA = SPEC / "resolution-scheduler-run.schema.json"
DEFAULT_LOG = ROOT / ".ope" / "live" / "resolution-scheduler" / "scheduler-runs.jsonl"


class ResolutionSchedulerError(Exception):
    pass


class SchedulerInterrupted(Exception):
    def __init__(self, report: dict[str, Any] | None) -> None:
        super().__init__("resolution scheduler interrupted")
        self.report = report


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def compact_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=False) + "\n"


def plural(count: int, noun: str) -> str:
    suffix = "" if count == 1 else "s"
    return f"{count} {noun}{suffix}"


def resolved_output_format(args: argparse.Namespace) -> str:
    output_format = getattr(args, "output_format", "auto")
    if output_format == "auto":
        return "text" if args.watch and sys.stdout.isatty() else "jsonl"
    return output_format


def format_human_tick(report: dict[str, Any]) -> str:
    tick = report["ticks"][-1]
    jobs = tick["jobSummary"]
    resolver_summary = tick["resolverSummary"]
    status_labels = {
        "idle": "Idle",
        "waiting": "Waiting",
        "due_pending": "Due pending",
        "executed": "Executed",
        "failed": "Failed",
    }
    job_bits = [
        plural(jobs["jobCount"], "job"),
        f"{jobs['pendingDueCount']} due",
        f"{jobs['pendingNotDueCount']} waiting",
        f"{jobs['alreadyResolvedCount']} resolved",
        f"{jobs['invalidCount']} invalid",
    ]
    if resolver_summary["ranResolver"]:
        resolver_text = (
            f"resolver executed {resolver_summary['executedCount']}, "
            f"failed {resolver_summary['failedCount']}"
        )
    else:
        resolver_text = "resolver not run"
    action_hint = ""
    if tick["tickStatus"] == "due_pending" and report["executionMode"] == "dry_run":
        action_hint = " | pass --execute to resolve due jobs"
    next_text = (
        f"next check in {tick['nextPollSeconds']}s"
        if tick["nextPollSeconds"]
        else "done"
    )
    return (
        f"{tick['startedAt']} | {status_labels[tick['tickStatus']]} | "
        f"{', '.join(job_bits)} | {resolver_text} | {next_text}{action_hint}\n"
    )


def format_human_shutdown(report: dict[str, Any] | None) -> str:
    if report is None:
        return "\nresolution scheduler stopped before first tick\n"
    tick_line = format_human_tick(report).strip()
    shutdown = report.get("shutdown", {})
    log_file = shutdown.get("logFile")
    log_text = f" | log: {log_file}" if log_file else ""
    return f"\nresolution scheduler stopped | last tick: {tick_line}{log_text}\n"


def workspace_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def registry_args(args: argparse.Namespace, now: str | None) -> SimpleNamespace:
    return SimpleNamespace(
        live=args.live,
        workspace=args.workspace,
        run_state=args.run_state or [],
        campaign=args.campaign,
        now=now,
        limit=args.limit,
    )


def resolver_args(args: argparse.Namespace, now: str | None, execute: bool) -> SimpleNamespace:
    return SimpleNamespace(
        live=args.live,
        execute=execute,
        workspace=args.workspace,
        run_state=args.run_state or [],
        now=now,
        limit=args.limit,
        trip_updates=args.trip_updates,
        input_protobuf=args.input_protobuf,
        static_gtfs=args.static_gtfs,
        download_static_gtfs=args.download_static_gtfs,
        timeout=args.timeout,
        max_bytes=args.max_bytes,
        static_gtfs_max_bytes=args.static_gtfs_max_bytes,
    )


def scheduler_action(job: dict[str, Any], execute_due: bool) -> str:
    status = job["jobStatus"]
    if job["target"].get("campaignId") and status == "pending_due":
        return "campaign_resolver_not_implemented"
    if status == "pending_due":
        return "resolver_execute_requested" if execute_due else "due_waiting_for_execute_flag"
    if status == "pending_not_due":
        return "wait_until_due"
    if status == "already_resolved":
        return "skip_already_resolved"
    return "inspect_invalid_state"


def tick_status(job_summary: dict[str, int], resolver_summary: dict[str, Any]) -> str:
    if resolver_summary["failedCount"] > 0:
        return "failed"
    if resolver_summary["executedCount"] > 0:
        return "executed"
    if job_summary["pendingDueCount"] > 0:
        return "due_pending"
    if job_summary["pendingNotDueCount"] > 0:
        return "waiting"
    return "idle"


def build_tick(args: argparse.Namespace, tick_number: int) -> dict[str, Any]:
    now = None if args.live else resolver.FIXTURE_NOW
    registry = generate_resolution_jobs.build_registry(registry_args(args, now))
    executable_due = [
        job for job in registry["jobs"]
        if job["jobStatus"] == "pending_due" and not job["target"].get("campaignId")
    ]
    execute_due = bool(args.execute and executable_due)
    resolver_report = resolver.build_report(resolver_args(args, registry["generatedAt"], execute_due)) if execute_due else None
    resolver_summary = {
        "ranResolver": resolver_report is not None,
        "executedCount": resolver_report["scanSummary"]["executedCount"] if resolver_report else 0,
        "failedCount": resolver_report["scanSummary"]["failedCount"] if resolver_report else 0,
    }
    actions = [
        {
            "resolutionJobId": job["resolutionJobId"],
            "jobStatus": job["jobStatus"],
            "schedulerAction": scheduler_action(job, execute_due),
            "statePath": job["target"]["statePath"],
        }
        for job in registry["jobs"]
    ]
    return {
        "tickNumber": tick_number,
        "startedAt": registry["generatedAt"],
        "tickStatus": tick_status(registry["summary"], resolver_summary),
        "jobSummary": registry["summary"],
        "resolverSummary": resolver_summary,
        "actions": actions,
        "nextPollSeconds": args.poll_seconds if args.watch else 0,
    }


def build_report(
    args: argparse.Namespace,
    ticks: list[dict[str, Any]],
    shutdown_reason: str | None = None,
) -> dict[str, Any]:
    if not ticks:
        raise ResolutionSchedulerError("scheduler report requires at least one tick")
    report = {
        "resolutionSchedulerRunId": "resolutionschedulerrun-001",
        "generatedAt": ticks[-1]["startedAt"],
        "schedulerMode": (
            "campaign_live_watch"
            if args.watch and args.campaign
            else "live_watch"
            if args.watch
            else "campaign_live_once"
            if args.live and args.campaign
            else "live_once"
            if args.live
            else "campaign_fixture_once"
            if args.campaign
            else "fixture_once"
        ),
        "executionMode": "execute" if args.execute else "dry_run",
        "pollSeconds": args.poll_seconds,
        "tickCount": len(ticks),
        "ticks": ticks,
        "executionBoundary": {
            "normalChecksUseLiveNetwork": False,
            "watchRequiresExplicitFlag": True,
            "executeRequiresExplicitFlag": True,
            "hostedSchedulerCreated": False,
            "osSchedulerCreated": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": [
            "This is a foreground terminal scheduler, not a hosted service or OS scheduler.",
            "Default and check modes perform one offline fixture tick.",
            "Live watching requires --live --watch; resolver execution additionally requires --execute.",
            "Agents that require machine-readable watch stdout should pass --output-format jsonl.",
            "Scheduler execution may resolve due runs, but it never creates calibration claims.",
        ],
    }
    if args.campaign:
        report["warnings"].append(
            "Campaign-aware scheduler ticks read checked campaign jobs but do not execute campaign resolvers or write campaign state."
        )
    if shutdown_reason is not None:
        report["shutdown"] = {
            "shutdownReason": shutdown_reason,
            "message": "resolution scheduler stopped by caller",
            "lastTickNumber": ticks[-1]["tickNumber"],
            "logFile": workspace_path(Path(args.log_file)),
        }
    validate_report(report)
    return report


def validate_report(report: dict[str, Any]) -> None:
    errors = validate_record(report, SCHEMA)
    if errors:
        raise ResolutionSchedulerError(f"resolution scheduler schema validation failed: {errors[0]}")
    boundary = report["executionBoundary"]
    if boundary["normalChecksUseLiveNetwork"]:
        raise ResolutionSchedulerError("normal checks must not use live network")
    if boundary["hostedSchedulerCreated"] or boundary["osSchedulerCreated"]:
        raise ResolutionSchedulerError("terminal scheduler must not create hosted or OS schedulers")
    if boundary["calibrationClaimAllowed"]:
        raise ResolutionSchedulerError("scheduler must not allow calibration claims")
    if report["executionMode"] == "dry_run":
        for tick in report["ticks"]:
            if tick["resolverSummary"]["executedCount"] or tick["resolverSummary"]["failedCount"]:
                raise ResolutionSchedulerError("dry-run scheduler must not execute resolvers")


def output_path(args: argparse.Namespace) -> Path:
    if args.campaign:
        return CAMPAIGN_OUTPUT_PATH
    return OUTPUT_PATH


def write_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    output_path(args).write_text(render_json(report), encoding="utf-8")
    print("generated resolution scheduler")


def check_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    expected = render_json(report)
    path = output_path(args)
    if not path.exists():
        print(f"missing resolution scheduler: {path}", file=sys.stderr)
        print("run `python3 scripts/run_resolution_scheduler.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        print(f"resolution scheduler drift: {path}", file=sys.stderr)
        print("run `python3 scripts/run_resolution_scheduler.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked resolution scheduler")


def append_log(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(compact_json(report))


def run_scheduler(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.execute and not args.live:
        raise ResolutionSchedulerError("--execute requires --live")
    if args.watch and not args.live:
        raise ResolutionSchedulerError("--watch requires --live")
    if args.poll_seconds < 1:
        raise ResolutionSchedulerError("--poll-seconds must be at least 1")
    ticks: list[dict[str, Any]] = []
    max_ticks = args.max_ticks if args.max_ticks is not None else (None if args.watch else 1)
    output_format = resolved_output_format(args)
    report: dict[str, Any] | None = None
    tick_number = 1
    try:
        while True:
            tick = build_tick(args, tick_number)
            ticks.append(tick)
            report = build_report(args, [tick] if args.watch and max_ticks is None else ticks)
            if args.watch:
                append_log(Path(args.log_file), report)
                sys.stdout.write(format_human_tick(report) if output_format == "text" else compact_json(report))
                sys.stdout.flush()
            if max_ticks is not None and tick_number >= max_ticks:
                return report
            if not args.watch:
                return report
            tick_number += 1
            time.sleep(args.poll_seconds)
    except KeyboardInterrupt as exc:
        if args.watch and report is not None:
            report = build_report(
                args,
                report["ticks"],
                shutdown_reason="keyboard_interrupt",
            )
            append_log(Path(args.log_file), report)
        raise SchedulerInterrupted(report) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="read ignored local resolution jobs")
    parser.add_argument("--watch", action="store_true", help="keep polling in the foreground terminal")
    parser.add_argument("--execute", action="store_true", help="execute due jobs through the checked resolver")
    parser.add_argument("--workspace", default=str(resolver.LIVE_WORKSPACE))
    parser.add_argument("--run-state", action="append", default=[])
    parser.add_argument("--campaign", help="include a checked prediction campaign in scheduler ticks")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--max-ticks", type=int)
    parser.add_argument("--log-file", default=str(DEFAULT_LOG))
    parser.add_argument(
        "--output-format",
        choices=["auto", "text", "jsonl"],
        default="auto",
        help="watch stdout format; auto uses text for terminals and jsonl when captured",
    )
    parser.add_argument("--trip-updates")
    parser.add_argument("--input-protobuf")
    parser.add_argument("--static-gtfs")
    parser.add_argument("--download-static-gtfs", action="store_true")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--max-bytes", type=int)
    parser.add_argument("--static-gtfs-max-bytes", type=int)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        if args.write or args.check:
            args.live = False
            args.watch = False
            args.execute = False
            args.max_ticks = 1
            report = run_scheduler(args)
            if report is None:
                raise ResolutionSchedulerError("scheduler did not produce a report")
            if args.write:
                write_report(report, args)
            else:
                check_report(report, args)
            return
        report = run_scheduler(args)
        if report is not None and not args.watch:
            sys.stdout.write(render_json(report))
    except SchedulerInterrupted as exc:
        output_format = resolved_output_format(args)
        if args.watch:
            if output_format == "jsonl" and exc.report is not None:
                if sys.stdout.isatty():
                    sys.stdout.write("\n")
                sys.stdout.write(compact_json(exc.report))
                sys.stdout.flush()
            else:
                print(format_human_shutdown(exc.report), file=sys.stderr, end="")
        raise SystemExit(130)
    except (
        OSError,
        json.JSONDecodeError,
        generate_resolution_jobs.ResolutionJobsError,
        resolver.TransitForwardRunResolverError,
        ResolutionSchedulerError,
        ValueError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
