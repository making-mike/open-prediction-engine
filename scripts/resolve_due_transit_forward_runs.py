#!/usr/bin/env python3
"""Scan and optionally resolve due weather-transit-delay forward runs."""

from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_transit_delay_forward as forward_run
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-forward-run-resolver"
OUTPUT_PATH = GENERATED / "resolve-due-forward-runs.generated.json"
SCHEMA = SPEC / "transit-forward-run-resolver.schema.json"
LIVE_WORKSPACE = ROOT / ".ope" / "live" / "transit-forward-run"
FIXTURE_NOW = "2026-06-10T08:30:00Z"


class TransitForwardRunResolverError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def absolutize(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else ROOT / value


def workspace_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path.resolve())


def state_summary(state: dict[str, Any]) -> dict[str, str]:
    forecast = state.get("forecastStage")
    if not isinstance(forecast, dict):
        return {
            "runStatus": str(state.get("runStatus", "unknown")),
            "resolveAt": "unknown",
            "forecastId": "unknown",
            "questionId": "unknown",
            "serviceDate": "unknown",
            "serviceWindow": "unknown",
        }
    return {
        "runStatus": str(state.get("runStatus", "unknown")),
        "resolveAt": str(forecast.get("resolveAt", "unknown")),
        "forecastId": str(forecast.get("forecastId", "unknown")),
        "questionId": str(forecast.get("questionId", "unknown")),
        "serviceDate": str(forecast.get("serviceDate", "unknown")),
        "serviceWindow": str(forecast.get("serviceWindow", "unknown")),
    }


def fixture_state(run_status: str, resolve_at: str, service_date: str, state_path: str) -> tuple[str, dict[str, Any]]:
    state = copy.deepcopy(forward_run.fixture_forward_run())
    state["runMode"] = "live_forecast" if run_status == "forecast_recorded" else state["runMode"]
    state["runStatus"] = run_status
    state["generatedAt"] = "2026-06-10T02:00:00Z"
    state["forecastStage"]["resolveAt"] = resolve_at
    state["forecastStage"]["serviceDate"] = service_date
    state["artifacts"] = {
        "forecastDirectory": f".ope/live/transit-forward-run/{service_date}-morning_peak-fixture/forecast",
        "runStatePath": state_path,
    }
    if run_status == "forecast_recorded":
        state.pop("captureStage", None)
        state.pop("resolutionStage", None)
        state.pop("scoreStage", None)
        state["claimBoundary"]["resolvedComparableOutcomes"] = 0
        state["nextAction"] = (
            f"After {state['forecastStage']['horizon']['endsAt']}, run transit-delay-forward-run "
            f"--phase resolve --run-state {state_path} --download-static-gtfs"
        )
    return state_path, state


def fixture_states() -> list[tuple[str, dict[str, Any]]]:
    return [
        fixture_state(
            "forecast_recorded",
            "2026-06-10T08:00:00Z",
            "2026-06-10",
            ".ope/live/transit-forward-run/fixture-due/forward-run-state.json",
        ),
        fixture_state(
            "forecast_recorded",
            "2026-06-11T08:00:00Z",
            "2026-06-11",
            ".ope/live/transit-forward-run/fixture-not-due/forward-run-state.json",
        ),
        fixture_state(
            "scored",
            "2026-06-09T08:00:00Z",
            "2026-06-09",
            ".ope/live/transit-forward-run/fixture-scored/forward-run-state.json",
        ),
    ]


def command_string(path: str, args: argparse.Namespace) -> str:
    parts = [
        "python3",
        "scripts/ope.py",
        "transit-delay-forward-run",
        "--phase",
        "resolve",
        "--run-state",
        path,
    ]
    if args.trip_updates:
        parts.extend(["--trip-updates", args.trip_updates])
    if args.input_protobuf:
        parts.extend(["--input-protobuf", args.input_protobuf])
    if args.static_gtfs:
        parts.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        parts.append("--download-static-gtfs")
    if args.timeout is not None:
        parts.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        parts.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        parts.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    return " ".join(parts)


def execute_resolver(path: str, args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        "scripts/run_transit_delay_forward.py",
        "--phase",
        "resolve",
        "--run-state",
        path,
    ]
    if args.trip_updates:
        command.extend(["--trip-updates", args.trip_updates])
    if args.input_protobuf:
        command.extend(["--input-protobuf", args.input_protobuf])
    if args.static_gtfs:
        command.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        command.append("--download-static-gtfs")
    if args.timeout is not None:
        command.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        command.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "resolver command failed").strip().splitlines()
        return {
            "status": "failed",
            "exitCode": completed.returncode,
            "errorMessage": message[-1][:500] if message else "resolver command failed",
        }
    try:
        summary = json.loads(completed.stdout)
    except json.JSONDecodeError:
        summary = {}
    return {
        "status": "succeeded",
        "exitCode": 0,
        "resolvedStatePath": path,
        "resolvedRunStatus": str(summary.get("runStatus", "unknown")),
    }


def decide(path: str, state: dict[str, Any], args: argparse.Namespace, now: str) -> dict[str, Any]:
    summary = state_summary(state)
    command = command_string(path, args)
    notes: list[str] = []
    try:
        resolve_at = parse_timestamp(summary["resolveAt"])
        due = parse_timestamp(now) >= resolve_at
    except ValueError:
        return {
            **summary,
            "statePath": path,
            "decision": "invalid_state",
            "due": False,
            "command": command,
            "executionResult": {"status": "not_run", "exitCode": 0},
            "notes": ["state is missing a valid forecastStage.resolveAt timestamp"],
        }

    status = summary["runStatus"]
    if status != "forecast_recorded":
        return {
            **summary,
            "statePath": path,
            "decision": "already_resolved",
            "due": due,
            "command": command,
            "executionResult": {"status": "not_run", "exitCode": 0},
            "notes": [f"run status is {status}; resolver will not execute it again"],
        }
    if not due:
        return {
            **summary,
            "statePath": path,
            "decision": "not_due",
            "due": False,
            "command": command,
            "executionResult": {"status": "not_run", "exitCode": 0},
            "notes": [f"resolveAt {summary['resolveAt']} is still in the future"],
        }

    if not args.execute:
        return {
            **summary,
            "statePath": path,
            "decision": "due_pending",
            "due": True,
            "command": command,
            "executionResult": {"status": "not_run", "exitCode": 0},
            "notes": ["dry-run only; pass --execute to run the checked resolver command"],
        }

    result = execute_resolver(path, args)
    decision = "executed" if result["status"] == "succeeded" else "failed"
    if result["status"] == "succeeded":
        notes.append("checked resolver command completed and rewrote the forward-run state")
    else:
        notes.append("checked resolver command failed; inspect errorMessage before retrying")
    return {
        **summary,
        "statePath": path,
        "decision": decision,
        "due": True,
        "command": command,
        "executionResult": result,
        "notes": notes,
    }


def scan_live_states(args: argparse.Namespace) -> list[tuple[str, dict[str, Any]]]:
    paths = [absolutize(path) for path in args.run_state] if args.run_state else sorted(absolutize(args.workspace).rglob("forward-run-state.json"))
    states: list[tuple[str, dict[str, Any]]] = []
    for path in paths:
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            states.append((workspace_path(path), {"runStatus": "invalid"}))
            continue
        states.append((workspace_path(path), state))
    return states[: args.limit]


def scan_summary(decisions: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "scannedCount": len(decisions),
        "dueCount": sum(1 for item in decisions if item["decision"] in {"due_pending", "executed", "failed"}),
        "notDueCount": sum(1 for item in decisions if item["decision"] == "not_due"),
        "alreadyResolvedCount": sum(1 for item in decisions if item["decision"] == "already_resolved"),
        "invalidCount": sum(1 for item in decisions if item["decision"] == "invalid_state"),
        "executedCount": sum(1 for item in decisions if item["decision"] == "executed"),
        "failedCount": sum(1 for item in decisions if item["decision"] == "failed"),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    if args.execute and not args.live:
        raise TransitForwardRunResolverError("--execute requires --live")
    now = args.now or (utc_now() if args.live else FIXTURE_NOW)
    states = scan_live_states(args) if args.live else fixture_states()
    decisions = [decide(path, state, args, now) for path, state in states]
    resolver_commands_ran = any(item["decision"] in {"executed", "failed"} for item in decisions)
    report = {
        "transitForwardRunResolverId": "transitforwardrunresolver-001",
        "generatedAt": now,
        "runMode": "live_execute" if args.execute else "live_scan" if args.live else "fixture_scan",
        "executionMode": "execute" if args.execute else "dry_run",
        "workspace": workspace_path(absolutize(args.workspace)) if args.live else "fixture://transit-forward-run-resolver",
        "now": now,
        "scanSummary": scan_summary(decisions),
        "runDecisions": decisions,
        "executionBoundary": {
            "normalChecksUseLiveNetwork": False,
            "liveScanRequiresExplicitFlag": True,
            "executeRequiresExplicitFlag": True,
            "resolverCommandsExecuted": resolver_commands_ran,
            "sourceFetchPerformed": bool(resolver_commands_ran and not args.trip_updates and not args.input_protobuf),
            "resolvedArtifactsCreated": any(item["decision"] == "executed" for item in decisions),
            "hostedSchedulerCreated": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": [
            "Default and check modes are offline fixture scans; live workspace scanning requires --live.",
            "Dry-run decisions do not fetch outcome sources or create resolution records.",
            "Executing a due run calls the checked transit-delay-forward-run resolver and may fetch HSL TripUpdates.",
            "Resolved runs still do not create a calibration claim by themselves.",
        ],
    }
    validate_report(report)
    return report


def validate_report(report: dict[str, Any]) -> None:
    errors = validate_record(report, SCHEMA)
    if errors:
        raise TransitForwardRunResolverError(f"transit forward-run resolver schema validation failed: {errors[0]}")
    boundary = report["executionBoundary"]
    if boundary["normalChecksUseLiveNetwork"]:
        raise TransitForwardRunResolverError("normal checks must not use live network")
    if boundary["calibrationClaimAllowed"]:
        raise TransitForwardRunResolverError("resolver must not allow calibration claims")
    if report["executionMode"] == "dry_run" and report["scanSummary"]["executedCount"] != 0:
        raise TransitForwardRunResolverError("dry-run resolver must not execute runs")


def write_report(report: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, report, label="transit forward-run resolver", regen="python3 scripts/resolve_due_transit_forward_runs.py --write")


def check_report(report: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, report, label="transit forward-run resolver", regen="python3 scripts/resolve_due_transit_forward_runs.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="scan ignored local live forward-run states")
    parser.add_argument("--execute", action="store_true", help="execute checked resolver commands for due live runs")
    parser.add_argument("--workspace", default=str(LIVE_WORKSPACE))
    parser.add_argument("--run-state", action="append", default=[], help="specific forward-run-state.json to scan")
    parser.add_argument("--now", help="override current timestamp for deterministic scans")
    parser.add_argument("--limit", type=int, default=50)
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
        report = build_report(args)
        if args.write:
            write_report(report)
        elif args.check:
            check_report(report)
        else:
            sys.stdout.write(render_json(report))
    except (OSError, json.JSONDecodeError, TransitForwardRunResolverError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
