#!/usr/bin/env python3
"""Generate an agent-facing resolution job registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import resolve_due_transit_forward_runs as resolver
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "resolution-jobs"
OUTPUT_PATH = GENERATED / "resolution-jobs.generated.json"
SCHEMA = SPEC / "resolution-job-registry.schema.json"


class ResolutionJobsError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def resolver_args(args: argparse.Namespace) -> SimpleNamespace:
    return SimpleNamespace(
        live=args.live,
        execute=False,
        workspace=args.workspace,
        run_state=args.run_state or [],
        now=args.now,
        limit=args.limit,
        trip_updates=None,
        input_protobuf=None,
        static_gtfs=None,
        download_static_gtfs=False,
        timeout=None,
        max_bytes=None,
        static_gtfs_max_bytes=None,
    )


def job_status(decision: str) -> str:
    if decision == "due_pending":
        return "pending_due"
    if decision == "not_due":
        return "pending_not_due"
    if decision == "already_resolved":
        return "already_resolved"
    return "invalid_state"


def action_for_job(status: str, path: str, reason: str) -> dict[str, Any]:
    scan = f"python3 scripts/ope.py resolve-due-forward-runs --live --run-state {path}"
    execute = f"{scan} --execute --download-static-gtfs"
    if status == "pending_due":
        return {
            "recommendedAction": "call_resolver_execute",
            "reason": "resolution time has passed; call the checked resolver command when live execution is approved",
            "commands": [scan, execute],
        }
    if status == "pending_not_due":
        return {
            "recommendedAction": "wait",
            "reason": reason,
            "commands": [scan],
        }
    if status == "already_resolved":
        return {
            "recommendedAction": "read_resolved_outputs",
            "reason": reason,
            "commands": [scan],
        }
    return {
        "recommendedAction": "inspect_invalid_state",
        "reason": reason,
        "commands": [scan],
    }


def build_job(index: int, decision: dict[str, Any]) -> dict[str, Any]:
    status = job_status(decision["decision"])
    reason = "; ".join(decision["notes"])
    return {
        "resolutionJobId": f"resolutionjob-{index:03d}",
        "jobStatus": status,
        "due": decision["due"],
        "target": {
            "forwardRunId": "unknown" if decision["forecastId"] == "unknown" else "transitdelayforwardrun-001",
            "forecastId": decision["forecastId"],
            "questionId": decision["questionId"],
            "runStatus": decision["runStatus"],
            "statePath": decision["statePath"],
            "resolveAt": decision["resolveAt"],
            "serviceDate": decision["serviceDate"],
            "serviceWindow": decision["serviceWindow"],
        },
        "agentAction": action_for_job(status, decision["statePath"], reason),
        "claimBoundary": {
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "normalChecksUseLiveNetwork": False,
            "calibrationClaimAllowed": False,
        },
    }


def summary(jobs: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "jobCount": len(jobs),
        "pendingDueCount": sum(1 for job in jobs if job["jobStatus"] == "pending_due"),
        "pendingNotDueCount": sum(1 for job in jobs if job["jobStatus"] == "pending_not_due"),
        "alreadyResolvedCount": sum(1 for job in jobs if job["jobStatus"] == "already_resolved"),
        "invalidCount": sum(1 for job in jobs if job["jobStatus"] == "invalid_state"),
    }


def build_registry(args: argparse.Namespace) -> dict[str, Any]:
    scan = resolver.build_report(resolver_args(args))
    jobs = [build_job(index, decision) for index, decision in enumerate(scan["runDecisions"], start=1)]
    registry = {
        "resolutionJobRegistryId": "resolutionjobregistry-001",
        "generatedAt": scan["generatedAt"],
        "registryMode": "live_registry" if args.live else "fixture_registry",
        "domain": "weather-transit-delays",
        "sourceBinding": {
            "sourceKind": "forward_run_state",
            "workspace": scan["workspace"],
            "resolverOperation": "resolve-due-forward-runs",
            "stateFilesCommitted": False,
        },
        "jobs": jobs,
        "summary": summary(jobs),
        "executionBoundary": {
            "registryExecutesResolvers": False,
            "liveScanRequiresExplicitFlag": True,
            "executeRequiresResolveDueCommand": True,
            "hostedSchedulerCreated": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": [
            "This registry is an agent-facing read model; it does not execute resolver commands.",
            "Live state scanning requires --live and reads ignored local forward-run state files.",
            "Agents should call resolve-due-forward-runs for execution instead of writing scheduler files.",
            "Resolution jobs do not create calibration claims by themselves.",
        ],
    }
    validate_registry(registry)
    return registry


def validate_registry(registry: dict[str, Any]) -> None:
    errors = validate_record(registry, SCHEMA)
    if errors:
        raise ResolutionJobsError(f"resolution job registry schema validation failed: {errors[0]}")
    boundary = registry["executionBoundary"]
    if boundary["registryExecutesResolvers"]:
        raise ResolutionJobsError("resolution job registry must not execute resolver commands")
    if boundary["calibrationClaimAllowed"]:
        raise ResolutionJobsError("resolution job registry must not allow calibration claims")
    for job in registry["jobs"]:
        claims = job["claimBoundary"]
        if claims["createsForecastArtifacts"] or claims["createsResolutionArtifacts"] or claims["calibrationClaimAllowed"]:
            raise ResolutionJobsError("resolution jobs are read models and must not create artifacts or claims")


def write_registry(registry: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(registry), encoding="utf-8")
    print("generated resolution jobs")


def check_registry(registry: dict[str, Any]) -> None:
    expected = render_json(registry)
    if not OUTPUT_PATH.exists():
        print(f"missing resolution jobs: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_resolution_jobs.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"resolution jobs drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_resolution_jobs.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked resolution jobs")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="read ignored local forward-run state files")
    parser.add_argument("--workspace", default=str(resolver.LIVE_WORKSPACE))
    parser.add_argument("--run-state", action="append", default=[])
    parser.add_argument("--now")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        registry = build_registry(args)
        if args.write:
            write_registry(registry)
        elif args.check:
            check_registry(registry)
        else:
            sys.stdout.write(render_json(registry))
    except (OSError, json.JSONDecodeError, resolver.TransitForwardRunResolverError, ResolutionJobsError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
