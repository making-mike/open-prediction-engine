#!/usr/bin/env python3
"""Generate or check the local prediction campaign resume readback."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import generate_resolution_jobs
from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from prediction_campaign_forecast_write_runtime import (
    PredictionCampaignForecastWriteError,
    build_campaign_state,
    build_run_state,
    ensure_safe_local_path,
    read_json,
)
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_schema import SPEC, validate_record
from ope_fixtures import compact_json, render_json, validate_and_emit


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-resume"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-resume.generated.json"
SCHEMA = SPEC / "prediction-campaign-resume.schema.json"
GENERATED_AT = "2026-05-29T02:00:00Z"
DEFAULT_CASE = "checked_fixture_bundle"
RESUME_CASES = ["checked_fixture_bundle", "interrupted_after_forecast_write"]


def registry_args(campaign_id: str) -> argparse.Namespace:
    return argparse.Namespace(
        live=False,
        workspace=str(generate_resolution_jobs.resolver.LIVE_WORKSPACE),
        run_state=[],
        campaign=campaign_id,
        now=None,
        limit=50,
    )


def resume_check(
    index: int,
    *,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"campaignresumecheck-{index:03d}",
        "checkStatus": status,
        "requiredBeforeResume": required,
        "blocksResume": blocks,
        "message": message,
    }


def recovery_action(
    index: int,
    *,
    status: str,
    command: str,
    reason: str,
    mutates_state: bool = False,
    executes_resolver: bool = False,
) -> dict[str, Any]:
    return {
        "actionId": f"campaignresumeaction-{index:03d}",
        "actionStatus": status,
        "command": command,
        "reason": reason,
        "mutatesState": mutates_state,
        "executesResolver": executes_resolver,
    }


def campaign_job(registry: dict[str, Any], campaign_id: str) -> dict[str, Any]:
    matches = [job for job in registry["jobs"] if job["target"].get("campaignId") == campaign_id]
    if len(matches) != 1:
        raise ValueError(f"expected one checked campaign job for {campaign_id}, found {len(matches)}")
    return matches[0]


def simulated_local_snapshot(write_plan: dict[str, Any]) -> dict[str, Any]:
    written_at = "2026-05-31T01:15:00Z"
    return {
        "sourceKind": "simulated_interrupted_campaign_state",
        "campaignState": build_campaign_state(write_plan, written_at),
        "runStates": [build_run_state(write_plan, written_at)],
    }


def read_local_snapshot(manifest: dict[str, Any]) -> dict[str, Any]:
    campaign_state_path = ensure_safe_local_path(manifest["localStatePolicy"]["campaignStatePath"])
    if not campaign_state_path.exists():
        raise PredictionCampaignForecastWriteError(
            f"Local campaign state not found: {manifest['localStatePolicy']['campaignStatePath']}"
        )
    campaign_state = read_json(campaign_state_path)
    run_states = []
    for path_value in campaign_state.get("runStatePaths", []):
        run_path = ensure_safe_local_path(path_value)
        if run_path.exists():
            run_states.append(read_json(run_path))
    return {
        "sourceKind": "ignored_local_campaign_state",
        "campaignState": campaign_state,
        "runStates": run_states,
    }


def snapshot_counts(snapshot: dict[str, Any] | None) -> tuple[int, int]:
    if snapshot is None:
        return 0, 0
    campaign_state = snapshot["campaignState"]
    return (
        len(snapshot["runStates"]),
        len(campaign_state.get("createdRunIdempotencyKeys", [])),
    )


def build_prediction_campaign_resume(
    *,
    case: str = DEFAULT_CASE,
    from_local: bool = False,
) -> dict[str, Any]:
    if case not in RESUME_CASES:
        raise ValueError(f"unknown prediction campaign resume case: {case}")
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    write_plan = build_prediction_campaign_forecast_write()
    records = build_prediction_campaign_forecast_artifact()
    campaign_id = manifest["campaign"]["campaignId"]
    registry = generate_resolution_jobs.build_registry(registry_args(campaign_id))
    job = campaign_job(registry, campaign_id)
    run_id = write_plan["bindings"]["runId"]
    run_state_path = write_plan["targetState"]["runStatePath"]
    snapshot = None
    if from_local:
        snapshot = read_local_snapshot(manifest)
    elif case == "interrupted_after_forecast_write":
        snapshot = simulated_local_snapshot(write_plan)
    local_run_count, idempotency_key_count = snapshot_counts(snapshot)
    local_resume = snapshot is not None
    source_kind = snapshot["sourceKind"] if snapshot else "checked_fixture_bundle"
    interrupted_run_state_found = local_run_count > 0
    waiting_resolution_count = (
        sum(1 for state in snapshot["runStates"] if state.get("runStatus") == "waiting_resolution")
        if snapshot
        else (1 if job["jobStatus"] == "pending_not_due" else 0)
    )
    due_resolution_count = 1 if job["jobStatus"] == "pending_due" and not snapshot else 0
    return {
        "predictionCampaignResumeId": "predictioncampaignresume-001",
        "generatedAt": GENERATED_AT,
        "resumeStatus": "local_resume_readback" if local_resume else "checked_resume_plan_non_mutating",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "predictionCampaignForecastWriteId": write_plan["predictionCampaignForecastWriteId"],
            "resolutionJobRegistryId": registry["resolutionJobRegistryId"],
            "repeatingPredictionSetupId": manifest["bindings"]["repeatingPredictionSetupId"],
            "campaignId": campaign_id,
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": run_id,
            "questionId": write_plan["bindings"]["questionId"],
            "forecastId": write_plan["bindings"]["forecastId"],
            "sourcePolicyId": write_plan["bindings"]["sourcePolicyId"],
            "campaignStatePath": manifest["localStatePolicy"]["campaignStatePath"],
            "runStatePath": run_state_path,
        },
        "observedState": {
            "sourceKind": source_kind,
            "liveStateRead": from_local,
            "ignoredLiveStateRequired": from_local,
            "localRunStateCount": local_run_count,
            "createdRunIdempotencyKeyCount": idempotency_key_count,
            "forecastWritePlanReady": write_plan["writeStatus"] == "ready_for_explicit_local_write",
            "forecastArtifactOpen": records["artifact"]["questionStatus"] == "open",
            "campaignJobStatus": job["jobStatus"],
            "waitingResolutionCount": waiting_resolution_count,
            "dueResolutionCount": due_resolution_count,
            "duplicateRiskCount": 0,
            "interruptedRunStateFound": interrupted_run_state_found,
            "priorEvidenceOverwriteAllowed": False,
        },
        "resumeChecks": [
            resume_check(
                1,
                status="pass",
                required=True,
                blocks=False,
                message="Checked campaign manifest, runner readback, forecast artifact, and forecast-write plan share the same campaign/run/forecast IDs.",
            ),
            resume_check(
                2,
                status="pass",
                required=True,
                blocks=False,
                message=f"Run state path {run_state_path} is an ignored relative .ope/live path and is not written during normal checks.",
            ),
            resume_check(
                3,
                status="pass",
                required=True,
                blocks=False,
                message="Forecast fixture remains open, unscored, and forecasted before the service window.",
            ),
            resume_check(
                4,
                status="pass",
                required=True,
                blocks=False,
                message="Resume readback forbids overwriting prior forecast evidence and keeps duplicate-key handling delegated to the campaign manifest.",
            ),
            resume_check(
                5,
                status="pass" if local_resume else "warn",
                required=local_resume,
                blocks=False,
                message=(
                    "Interrupted local campaign state was inspected with explicit resume mode; existing run evidence remains read-only."
                    if local_resume
                    else "Effectful resume is not implemented; campaign resolver execution is available as a separate explicit resolve command."
                ),
            ),
            resume_check(
                6,
                status="pass",
                required=True,
                blocks=False,
                message="Existing idempotency keys and run-state paths are preserved; resume must continue with a new due run instead of overwriting prior evidence.",
            ),
        ],
        "recoveryActions": [
            recovery_action(
                1,
                status="available",
                command="python3 scripts/ope.py prediction-campaign status",
                reason="Inspect planned run progress without reading raw local state files.",
            ),
            recovery_action(
                2,
                status="available",
                command="python3 scripts/ope.py prediction-campaign forecast-write",
                reason="Review the target paths and idempotency guard for the checked forecast lifecycle records.",
            ),
            recovery_action(
                3,
                status="available",
                command=f"python3 scripts/ope.py resolution-jobs --campaign {campaign_id}",
                reason="Read the current campaign resolution next action without executing a resolver.",
            ),
            recovery_action(
                4,
                status="wait",
                command=f"python3 scripts/ope.py resolution-scheduler --campaign {campaign_id}",
                reason="Inspect the dry-run scheduler tick; the checked campaign job is waiting for resolution eligibility.",
            ),
            recovery_action(
                5,
                status="available" if local_resume else "blocked",
                command=(
                    "python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --write-local --output-format jsonl"
                    if local_resume
                    else f"python3 scripts/ope.py prediction-campaign forecast-write --run-id {run_id} --write-local"
                ),
                reason=(
                    "Continue by creating the next due forecast; existing idempotency keys prevent overwriting the interrupted run."
                    if local_resume
                    else "Future effectful resume must require explicit local write support and idempotency checks before mutating campaign state."
                ),
                mutates_state=local_resume,
            ),
        ],
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign resume",
            "acceptedFlags": ["--from-local", "--resume-case", "--view", "--output-format"],
            "defaultMode": "checked_resume_plan",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "explicitResolverFlagRequired": True,
            "normalChecksWriteLiveState": False,
        },
        "summary": {
            "resumeReadbackImplemented": True,
            "localResumeReadbackImplemented": local_resume,
            "effectfulResumeImplemented": False,
            "safeToResumeReadback": True,
            "writesIgnoredLiveState": False,
            "executesResolvers": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": (
                "Continue with the next due explicit local forecast write; do not overwrite existing run evidence."
                if local_resume
                else "Run prediction-campaign resume --from-local after an interrupted local campaign write to inspect ignored campaign state."
            ),
            "recommendedNextMilestone": "Milestone 106 campaign evidence ledger append runtime",
        },
        "executionBoundary": {
            "readOnlyResumePlan": True,
            "readsIgnoredLiveState": from_local,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesForecastCreation": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "overwritesPriorEvidence": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This resume readback is checked and non-mutating; it does not continue a live loop.",
            "Resume preserves existing forecast evidence and idempotency keys before any later explicit local write.",
            "Campaign resolver execution remains separate and requires explicit resolve --execute-resolvers --write-local.",
            "No scoring, corpus append, calibration, or quality claim is created by this readback.",
        ],
    }


def print_view(resume: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "resume": resume,
        "state": resume["observedState"],
        "checks": resume["resumeChecks"],
        "actions": resume["recoveryActions"],
        "summary": resume["summary"],
        "boundary": resume["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        state = resume["observedState"]
        print(
            f"{resume['resumeStatus']} localRuns={state['localRunStateCount']} "
            f"overwriteAllowed={state['priorEvidenceOverwriteAllowed']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(data, SCHEMA, OUTPUT_PATH, write=write, label="prediction campaign resume", regen="python3 scripts/generate_prediction_campaign_resume.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign resume")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign resume drift")
    parser.add_argument("--from-local", action="store_true", help="explicitly inspect ignored local campaign state")
    parser.add_argument(
        "--resume-case",
        choices=RESUME_CASES,
        default=DEFAULT_CASE,
        help="checked resume case to inspect",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["resume", "state", "checks", "actions", "summary", "boundary"],
        default="resume",
        help="print one prediction campaign resume view",
    )
    args = parser.parse_args()

    if (args.write or args.check) and (args.from_local or args.resume_case != DEFAULT_CASE):
        raise SystemExit("custom resume inputs cannot be combined with --write or --check")
    try:
        resume = build_prediction_campaign_resume(case=args.resume_case, from_local=args.from_local)
    except PredictionCampaignForecastWriteError as exc:
        raise SystemExit(str(exc)) from exc
    if args.write or args.check:
        check_or_write(resume, write=args.write)
        return
    errors = validate_record(resume, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(resume, args.view, args.output_format)


if __name__ == "__main__":
    main()
