#!/usr/bin/env python3
"""Generate an agent-facing resolution job registry."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
import resolve_due_transit_forward_runs as resolver
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "resolution-jobs"
OUTPUT_PATH = GENERATED / "resolution-jobs.generated.json"
CAMPAIGN_OUTPUT_PATH = GENERATED / "resolution-jobs-campaign.generated.json"
SCHEMA = SPEC / "resolution-job-registry.schema.json"


class ResolutionJobsError(Exception):
    pass


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def resolver_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
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


def campaign_action_for_job(
    status: str,
    *,
    campaign_id: str,
    run_id: str,
    forecast_id: str,
    question_id: str,
    reason: str,
) -> dict[str, Any]:
    scan = f"python3 scripts/ope.py resolution-jobs --campaign {campaign_id}"
    attempt = f"python3 scripts/ope.py prediction-campaign resolve --run-id {run_id}"
    execute_attempt = f"{attempt} --execute-resolvers"
    execute_write = (
        f"{execute_attempt} --outcome-csv "
        f".ope/live/prediction-campaigns/{campaign_id}/{run_id}/outcome.csv --write-local"
    )
    read_forecast = (
        "python3 scripts/ope.py read --record-type forecast-card "
        f"--id {forecast_id} --question-id {question_id}"
    )
    if status == "pending_due":
        return {
            "recommendedAction": "call_campaign_resolver_attempt",
            "reason": "campaign forecast is due; inspect the readback, then run the explicit local resolver write with a declared outcome source",
            "commands": [scan, attempt, execute_attempt, execute_write, read_forecast],
        }
    if status == "pending_not_due":
        return {
            "recommendedAction": "wait",
            "reason": reason,
            "commands": [scan, read_forecast],
        }
    if status == "already_resolved":
        return {
            "recommendedAction": "read_resolved_outputs",
            "reason": reason,
            "commands": [scan, read_forecast],
        }
    return {
        "recommendedAction": "inspect_invalid_state",
        "reason": reason,
        "commands": [scan, f"python3 scripts/ope.py prediction-campaign status --run-id {run_id}"],
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


def build_campaign_job(index: int, *, campaign_id: str, now: str) -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    if campaign_id != manifest["campaign"]["campaignId"]:
        raise ResolutionJobsError(f"unknown checked campaign id: {campaign_id}")
    write_plan = build_prediction_campaign_forecast_write()
    records = build_prediction_campaign_forecast_artifact()
    run_id = write_plan["bindings"]["runId"]
    runs = {run["runId"]: run for run in manifest["plannedRuns"]}
    if run_id not in runs:
        raise ResolutionJobsError(f"campaign run {run_id} is not present in the manifest")
    run = runs[run_id]
    artifact = records["artifact"]
    due = parse_utc(now) >= parse_utc(run["resolutionEligibleAt"])
    if artifact["questionStatus"] == "open":
        status = "pending_due" if due else "pending_not_due"
        run_status = "due_resolution" if due else "waiting_resolution"
        reason = (
            f"campaign run {run_id} has forecast {artifact['forecastId']} and "
            f"resolutionEligibleAt {run['resolutionEligibleAt']}"
        )
    else:
        status = "already_resolved"
        run_status = "resolved"
        reason = f"campaign forecast {artifact['forecastId']} is no longer open"
    return {
        "resolutionJobId": f"resolutionjob-{index:03d}",
        "jobStatus": status,
        "due": due,
        "target": {
            "forwardRunId": "none",
            "campaignId": campaign_id,
            "campaignRunId": run_id,
            "forecastId": artifact["forecastId"],
            "questionId": artifact["questionId"],
            "resolutionId": run["resolutionId"],
            "scoringReportId": run["scoringReportId"],
            "runStatus": run_status,
            "statePath": write_plan["targetState"]["runStatePath"],
            "resolveAt": run["resolutionEligibleAt"],
            "serviceDate": run["serviceDate"],
            "serviceWindow": run["serviceWindow"],
        },
        "agentAction": campaign_action_for_job(
            status,
            campaign_id=campaign_id,
            run_id=run_id,
            forecast_id=artifact["forecastId"],
            question_id=artifact["questionId"],
            reason=reason,
        ),
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
    campaign_id = getattr(args, "campaign", None)
    if campaign_id:
        jobs.append(build_campaign_job(len(jobs) + 1, campaign_id=campaign_id, now=args.now or scan["generatedAt"]))
    source_binding = {
        "sourceKind": "forward_run_state_and_campaign_manifest" if campaign_id else "forward_run_state",
        "workspace": scan["workspace"],
        "resolverOperation": "resolve-due-forward-runs",
        "stateFilesCommitted": False,
    }
    if campaign_id:
        write_plan = build_prediction_campaign_forecast_write()
        source_binding.update(
            {
                "campaignId": campaign_id,
                "campaignManifestPath": "spec/fixtures/generated/prediction-campaign-manifest/weather-transit-delay-campaign-manifest.generated.json",
                "campaignRunStatePath": write_plan["targetState"]["runStatePath"],
                "forecastWritePlanPath": "spec/fixtures/generated/prediction-campaign-forecast-write/weather-transit-delay-campaign-forecast-write.generated.json",
            }
        )
    warnings = [
        "This registry is an agent-facing read model; it does not execute resolver commands.",
        "Live state scanning requires --live and reads ignored local forward-run state files.",
        "Agents should call resolve-due-forward-runs for execution instead of writing scheduler files.",
        "Resolution jobs do not create calibration claims by themselves.",
    ]
    if campaign_id:
        warnings.append(
            "Campaign jobs are read from checked campaign fixtures and do not execute campaign resolvers or write campaign state."
        )
    registry = {
        "resolutionJobRegistryId": "resolutionjobregistry-001",
        "generatedAt": scan["generatedAt"],
        "registryMode": (
            "campaign_live_registry"
            if args.live and campaign_id
            else "campaign_fixture_registry"
            if campaign_id
            else "live_registry"
            if args.live
            else "fixture_registry"
        ),
        "domain": "weather-transit-delays",
        "sourceBinding": source_binding,
        "jobs": jobs,
        "summary": summary(jobs),
        "executionBoundary": {
            "registryExecutesResolvers": False,
            "liveScanRequiresExplicitFlag": True,
            "executeRequiresResolveDueCommand": True,
            "hostedSchedulerCreated": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": warnings,
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


def output_path(args: argparse.Namespace) -> Path:
    if getattr(args, "campaign", None):
        return CAMPAIGN_OUTPUT_PATH
    return OUTPUT_PATH


def write_registry(registry: dict[str, Any], args: argparse.Namespace) -> None:
    write_generated(output_path(args), registry, label="resolution jobs", regen="python3 scripts/generate_resolution_jobs.py --write")


def check_registry(registry: dict[str, Any], args: argparse.Namespace) -> None:
    check_generated(output_path(args), registry, label="resolution jobs", regen="python3 scripts/generate_resolution_jobs.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="read ignored local forward-run state files")
    parser.add_argument("--workspace", default=str(resolver.LIVE_WORKSPACE))
    parser.add_argument("--run-state", action="append", default=[])
    parser.add_argument("--campaign", help="include a checked prediction campaign in the registry")
    parser.add_argument("--now")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        registry = build_registry(args)
        if args.write:
            write_registry(registry, args)
        elif args.check:
            check_registry(registry, args)
        else:
            sys.stdout.write(render_json(registry))
    except (OSError, json.JSONDecodeError, resolver.TransitForwardRunResolverError, ResolutionJobsError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
