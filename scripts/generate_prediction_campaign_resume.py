#!/usr/bin/env python3
"""Generate or check the local prediction campaign resume readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import generate_resolution_jobs
from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-resume"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-resume.generated.json"
SCHEMA = SPEC / "prediction-campaign-resume.schema.json"
GENERATED_AT = "2026-05-29T02:00:00Z"


def registry_args(campaign_id: str) -> SimpleNamespace:
    return SimpleNamespace(
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


def build_prediction_campaign_resume() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    write_plan = build_prediction_campaign_forecast_write()
    records = build_prediction_campaign_forecast_artifact()
    campaign_id = manifest["campaign"]["campaignId"]
    registry = generate_resolution_jobs.build_registry(registry_args(campaign_id))
    job = campaign_job(registry, campaign_id)
    run_id = write_plan["bindings"]["runId"]
    run_state_path = write_plan["targetState"]["runStatePath"]
    return {
        "predictionCampaignResumeId": "predictioncampaignresume-001",
        "generatedAt": GENERATED_AT,
        "resumeStatus": "checked_resume_plan_non_mutating",
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
            "sourceKind": "checked_fixture_bundle",
            "liveStateRead": False,
            "ignoredLiveStateRequired": False,
            "forecastWritePlanReady": write_plan["writeStatus"] == "ready_for_explicit_local_write",
            "forecastArtifactOpen": records["artifact"]["questionStatus"] == "open",
            "campaignJobStatus": job["jobStatus"],
            "waitingResolutionCount": 1 if job["jobStatus"] == "pending_not_due" else 0,
            "dueResolutionCount": 1 if job["jobStatus"] == "pending_due" else 0,
            "duplicateRiskCount": 0,
            "interruptedRunStateFound": False,
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
                status="warn",
                required=False,
                blocks=False,
                message="Effectful resume and campaign resolver execution are not implemented yet; this readback only tells agents the safe next action.",
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
                status="blocked",
                command=f"python3 scripts/ope.py prediction-campaign forecast-write --run-id {run_id} --write-local",
                reason="Future effectful resume must require explicit local write support and idempotency checks before mutating campaign state.",
            ),
        ],
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign resume",
            "acceptedFlags": ["--manifest-json", "--run-id", "--execute-resolvers", "--output-format"],
            "defaultMode": "checked_resume_plan",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "explicitResolverFlagRequired": True,
            "normalChecksWriteLiveState": False,
        },
        "summary": {
            "resumeReadbackImplemented": True,
            "effectfulResumeImplemented": False,
            "safeToResumeReadback": True,
            "writesIgnoredLiveState": False,
            "executesResolvers": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": "Implement guarded local campaign state writes before enabling effectful resume after interruption.",
            "recommendedNextMilestone": "Milestone 94 effectful campaign resume and resolver attempts",
        },
        "executionBoundary": {
            "readOnlyResumePlan": True,
            "readsIgnoredLiveState": False,
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
            "Future effectful resume must preserve existing forecast evidence and idempotency keys before writing .ope/live state.",
            "Campaign resolver execution remains separate and requires explicit future resolver support.",
            "No scoring, corpus append, calibration, or quality claim is created by this readback.",
        ],
    }


def print_view(resume: dict[str, Any], view: str) -> None:
    views = {
        "resume": resume,
        "state": resume["observedState"],
        "checks": resume["resumeChecks"],
        "actions": resume["recoveryActions"],
        "summary": resume["summary"],
        "boundary": resume["executionBoundary"],
    }
    print(render_json(views[view]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    errors = validate_record(data, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    if write:
        write_generated(OUTPUT_PATH, data, label="prediction campaign resume", regen="python3 scripts/generate_prediction_campaign_resume.py --write")
    else:
        check_generated(OUTPUT_PATH, data, label="prediction campaign resume", regen="python3 scripts/generate_prediction_campaign_resume.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign resume")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign resume drift")
    parser.add_argument(
        "--view",
        choices=["resume", "state", "checks", "actions", "summary", "boundary"],
        default="resume",
        help="print one prediction campaign resume view",
    )
    args = parser.parse_args()

    resume = build_prediction_campaign_resume()
    if args.write or args.check:
        check_or_write(resume, write=args.write)
        return
    errors = validate_record(resume, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(resume, args.view)


if __name__ == "__main__":
    main()
