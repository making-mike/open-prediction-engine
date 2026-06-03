#!/usr/bin/env python3
"""Generate or check a compact prediction campaign doctor readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import generate_resolution_jobs
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_resolution_attempt import (
    DEFAULT_NOW,
    build_prediction_campaign_resolution_attempt,
)
from generate_prediction_campaign_resume import build_prediction_campaign_resume
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-doctor"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-doctor.generated.json"
SCHEMA = SPEC / "prediction-campaign-doctor.schema.json"
GENERATED_AT = "2026-05-31T01:00:00Z"


def registry_args(campaign_id: str, now: str) -> argparse.Namespace:
    return argparse.Namespace(
        live=False,
        workspace=str(generate_resolution_jobs.resolver.LIVE_WORKSPACE),
        run_state=[],
        campaign=campaign_id,
        now=now,
        limit=50,
    )


def campaign_jobs(registry: dict[str, Any], campaign_id: str) -> list[dict[str, Any]]:
    return [job for job in registry["jobs"] if job["target"].get("campaignId") == campaign_id]


def run_ids(jobs: list[dict[str, Any]]) -> list[str]:
    return [job["target"]["campaignRunId"] for job in jobs]


def queue_readback(
    *,
    name: str,
    status: str,
    ids: list[str],
    next_action: str,
    commands: list[str],
) -> dict[str, Any]:
    return {
        "queueName": name,
        "queueStatus": status,
        "runCount": len(ids),
        "runIds": ids,
        "nextAction": next_action,
        "commands": commands,
        "mutatesState": False,
        "executesResolver": False,
        "createsResolutionArtifacts": False,
        "createsScoringRecords": False,
        "appendsCorpusEvidence": False,
    }


def duplicate_risk_count(manifest: dict[str, Any]) -> int:
    keys = [run["duplicateKey"] for run in manifest["plannedRuns"]]
    return len(keys) - len(set(keys))


def build_queue_readbacks(
    *,
    campaign_id: str,
    due_jobs: list[dict[str, Any]],
    waiting_jobs: list[dict[str, Any]],
    blocked_ids: list[str],
) -> list[dict[str, Any]]:
    due_ids = run_ids(due_jobs)
    waiting_ids = run_ids(waiting_jobs)
    return [
        queue_readback(
            name="due_runs",
            status="actionable" if due_ids else "empty",
            ids=due_ids,
            next_action=(
                "Inspect the checked campaign resolution attempt, then execute with --write-local after attaching an outcome source."
                if due_ids
                else "No campaign runs are due for resolution."
            ),
            commands=[
                f"python3 scripts/ope.py resolution-jobs --campaign {campaign_id} --now {DEFAULT_NOW}",
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301",
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers",
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local",
            ],
        ),
        queue_readback(
            name="waiting_runs",
            status="waiting" if waiting_ids else "empty",
            ids=waiting_ids,
            next_action="Wait until resolutionEligibleAt before attempting campaign resolution.",
            commands=[f"python3 scripts/ope.py resolution-scheduler --campaign {campaign_id}"],
        ),
        queue_readback(
            name="failed_runs",
            status="empty",
            ids=[],
            next_action="No checked campaign failures are present in the fixture readback.",
            commands=["python3 scripts/ope.py prediction-campaign resume --view actions"],
        ),
        queue_readback(
            name="blocked_runs",
            status="blocked" if blocked_ids else "empty",
            ids=blocked_ids,
            next_action=(
                "Attach a checked campaign outcome source before resolution or scoring can proceed."
                if blocked_ids
                else "No checked campaign blockers are present."
            ),
            commands=["python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers"],
        ),
        queue_readback(
            name="append_ready_runs",
            status="empty",
            ids=[],
            next_action="No campaign run has both resolution and scoring records ready for ledger append.",
            commands=["python3 scripts/ope.py transit-corpus-growth"],
        ),
    ]


def doctor_status(*, due_count: int, blocked_count: int, waiting_count: int) -> str:
    if due_count:
        return "actionable_due_run"
    if blocked_count:
        return "blocked"
    if waiting_count:
        return "waiting"
    return "healthy_no_action"


def build_prediction_campaign_doctor(now: str = DEFAULT_NOW) -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    write_plan = build_prediction_campaign_forecast_write()
    resume = build_prediction_campaign_resume()
    campaign_id = manifest["campaign"]["campaignId"]
    registry = generate_resolution_jobs.build_registry(registry_args(campaign_id, now))
    attempt = build_prediction_campaign_resolution_attempt(now=now)
    execute_attempt = build_prediction_campaign_resolution_attempt(now=now, execute_resolvers=True)
    jobs = campaign_jobs(registry, campaign_id)
    due_jobs = [job for job in jobs if job["jobStatus"] == "pending_due"]
    waiting_jobs = [job for job in jobs if job["jobStatus"] == "pending_not_due"]
    blocked_ids = (
        [attempt["bindings"]["runId"]]
        if execute_attempt["attemptStatus"] == "blocked_missing_outcome_source"
        else []
    )
    duplicate_count = duplicate_risk_count(manifest)
    queue_readbacks = build_queue_readbacks(
        campaign_id=campaign_id,
        due_jobs=due_jobs,
        waiting_jobs=waiting_jobs,
        blocked_ids=blocked_ids,
    )
    due_count = len(due_jobs)
    waiting_count = len(waiting_jobs)
    blocked_count = len(blocked_ids)
    return {
        "predictionCampaignDoctorId": "predictioncampaigndoctor-001",
        "generatedAt": GENERATED_AT,
        "doctorStatus": doctor_status(
            due_count=due_count,
            blocked_count=blocked_count,
            waiting_count=waiting_count,
        ),
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "predictionCampaignForecastWriteId": write_plan["predictionCampaignForecastWriteId"],
            "predictionCampaignResolutionAttemptId": attempt["predictionCampaignResolutionAttemptId"],
            "predictionCampaignResumeId": resume["predictionCampaignResumeId"],
            "resolutionJobRegistryId": registry["resolutionJobRegistryId"],
            "campaignId": campaign_id,
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": write_plan["bindings"]["runId"],
            "forecastId": write_plan["bindings"]["forecastId"],
            "questionId": write_plan["bindings"]["questionId"],
            "sourcePolicyId": write_plan["bindings"]["sourcePolicyId"],
        },
        "health": {
            "campaignHealth": "due_run_requires_checked_outcome_source" if due_count else "waiting_for_resolution_window",
            "now": now,
            "plannedRunCount": len(manifest["plannedRuns"]),
            "checkedRunCount": len(jobs),
            "dueRunCount": due_count,
            "waitingRunCount": waiting_count,
            "failedRunCount": 0,
            "blockedRunCount": blocked_count,
            "appendReadyRunCount": 0,
            "qualityClaimAllowed": False,
        },
        "queueReadbacks": queue_readbacks,
        "duplicateProtection": {
            "duplicatePolicy": manifest["planningWindow"]["duplicatePolicy"],
            "duplicateKeysInspected": len(manifest["plannedRuns"]),
            "duplicateRiskCount": duplicate_count,
            "duplicateResolutionBlocked": True,
            "duplicateScoringBlocked": True,
            "priorEvidenceOverwriteAllowed": False,
            "alreadyTerminalRunHandling": "Already resolved, annulled, canceled, failed, missed, or blocked duplicate runs must be read, not resolved or scored again.",
        },
        "recoveryPosture": {
            "resumeReadbackAvailable": resume["summary"]["resumeReadbackImplemented"],
            "effectfulResumeImplemented": resume["summary"]["effectfulResumeImplemented"],
            "interruptedRunStateFound": resume["observedState"]["interruptedRunStateFound"],
            "safeReadbackCommands": [
                "python3 scripts/ope.py prediction-campaign resume",
                "python3 scripts/ope.py prediction-campaign status",
                f"python3 scripts/ope.py resolution-jobs --campaign {campaign_id}",
            ],
            "nextRecoveryAction": resume["summary"]["recommendedNextAction"],
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign doctor",
            "acceptedFlags": ["--now", "--output-format", "--view"],
            "defaultMode": "checked_campaign_health_readback",
            "capturedStdoutMode": "json",
            "normalChecksMutateState": False,
        },
        "summary": {
            "doctorReadbackImplemented": True,
            "agentQueueReadbacksImplemented": True,
            "dueRunReadbackImplemented": True,
            "failedRunReadbackImplemented": True,
            "appendReadyReadbackImplemented": True,
            "effectfulResolutionImplemented": True,
            "effectfulResumeImplemented": False,
            "nextRecommendedCommand": (
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local"
                if due_count
                else f"python3 scripts/ope.py resolution-scheduler --campaign {campaign_id}"
            ),
        },
        "executionBoundary": {
            "readsIgnoredLiveState": False,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "overwritesPriorEvidence": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This doctor readback is generated from checked fixtures and does not inspect ignored live campaign state.",
            "Due campaign runs route to checked resolver commands; normal doctor readbacks do not create resolution or scoring records.",
            "Append-ready campaign evidence remains empty until a run has checked resolution and scoring records.",
            "Duplicate resolution, duplicate scoring, and prior-evidence overwrite remain blocked by this readback.",
        ],
    }


def print_view(doctor: dict[str, Any], output_format: str, view: str) -> None:
    views = {
        "doctor": doctor,
        "health": doctor["health"],
        "queues": doctor["queueReadbacks"],
        "duplicates": doctor["duplicateProtection"],
        "recovery": doctor["recoveryPosture"],
        "summary": doctor["summary"],
        "boundary": doctor["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        health = doctor["health"]
        print(
            f"{doctor['doctorStatus']} due={health['dueRunCount']} "
            f"waiting={health['waitingRunCount']} blocked={health['blockedRunCount']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign doctor",
        regen="python3 scripts/generate_prediction_campaign_doctor.py --write",
    )


def validate_doctor(doctor: dict[str, Any]) -> None:
    errors = validate_record(doctor, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)


def load_generated_doctor() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    doctor = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_doctor(doctor)
    return doctor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign doctor")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign doctor drift")
    parser.add_argument("--now", default=DEFAULT_NOW, help="UTC doctor readback clock")
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["doctor", "health", "queues", "duplicates", "recovery", "summary", "boundary"],
        default="doctor",
        help="print one campaign doctor view",
    )
    args = parser.parse_args()

    if (args.write or args.check) and args.now != DEFAULT_NOW:
        raise SystemExit("custom doctor inputs cannot be combined with --write or --check")
    if args.write or args.check or args.now != DEFAULT_NOW:
        doctor = build_prediction_campaign_doctor(now=args.now)
    else:
        doctor = load_generated_doctor() or build_prediction_campaign_doctor(now=args.now)
    validate_doctor(doctor)
    if args.write or args.check:
        check_or_write(doctor, write=args.write)
        return
    print_view(doctor, args.output_format, args.view)


if __name__ == "__main__":
    main()
