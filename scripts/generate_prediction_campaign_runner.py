#!/usr/bin/env python3
"""Generate or check the local prediction campaign runner readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-runner"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-runner.generated.json"
SCHEMA = SPEC / "prediction-campaign-runner.schema.json"
GENERATED_AT = "2026-05-29T00:15:00Z"


def recurrence_mode(mode: str, flag: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "flagBinding": flag,
        "supportedByDryRun": True,
        "createsForecastArtifacts": False,
    }


def runner_decision(index: int, run: dict[str, Any], status: str, reason: str, next_action: str) -> dict[str, Any]:
    return {
        "decisionId": f"predictionrunnerdecision-{index:03d}",
        "runId": run["runId"],
        "decisionStatus": status,
        "reason": reason,
        "nextAction": next_action,
        "forecastArtifactsCreated": False,
        "liveFetchRequired": False,
        "resolverExecutionRequired": False,
        "writesLiveState": False,
    }


def build_runner_decisions(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    planned = manifest["plannedRuns"]
    return [
        runner_decision(
            1,
            planned[0],
            "ready_to_create_forecast",
            "Dry-run clock is at the first candidate create time and forecast close has not passed.",
            "A later effectful runner may create the forecast only with explicit local execution.",
        ),
        runner_decision(
            2,
            planned[1],
            "wait_until_create_time",
            "The second candidate is planned but not due at the dry-run readback time.",
            "Wait until forecastCreateAt before creating the run.",
        ),
        runner_decision(
            3,
            planned[2],
            "skip_missed_close",
            "The missed-run policy is defined for cases where forecastCloseAt has already passed.",
            "Record a skipped or missed state instead of backfilling a forecast.",
        ),
        runner_decision(
            4,
            planned[3],
            "blocked_duplicate",
            "The duplicate key policy blocks a second forecast for the same campaign date/window key.",
            "Keep the original run and do not create a duplicate forecast artifact.",
        ),
    ]


def build_prediction_campaign_runner() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    first_run = manifest["plannedRuns"][0]
    decisions = build_runner_decisions(manifest)
    return {
        "predictionCampaignRunnerId": "predictioncampaignrunner-001",
        "generatedAt": GENERATED_AT,
        "runnerStatus": "dry_run_ready_non_executing",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "repeatingPredictionSetupId": manifest["bindings"]["repeatingPredictionSetupId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
            "manifestPath": "spec/fixtures/generated/prediction-campaign-manifest/weather-transit-delay-campaign-manifest.generated.json",
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign start",
            "acceptsSetupJson": True,
            "acceptsManifestJson": True,
            "flags": [
                "--domain",
                "--service-window",
                "--interval",
                "--count",
                "--until",
                "--calibration-target",
                "--post-calibration-action",
                "--post-calibration-delay",
                "--setup-json",
                "--manifest-json",
                "--live-weather",
                "--execute-resolvers",
                "--output-format",
            ],
            "requiresExplicitLiveFetchFlag": True,
            "requiresExplicitResolverExecutionFlag": True,
            "defaultMissedRunPolicy": "skip_if_forecast_close_passed",
        },
        "supportedRecurrenceModes": [
            recurrence_mode("fixed_count", "--count"),
            recurrence_mode("until_date", "--until"),
            recurrence_mode("open_ended", "--count omitted with explicit stop policy"),
            recurrence_mode("interval", "--interval"),
            recurrence_mode("calibration_threshold", "--calibration-target"),
            recurrence_mode("post_calibration_restart", "--post-calibration-action pause_then_resume_after"),
        ],
        "runnerDecisions": decisions,
        "outputModes": {
            "interactiveTerminalMode": "compact_human_status_lines",
            "capturedStdoutMode": "jsonl",
            "jsonlExample": "{\"event\":\"campaign_runner_decision\",\"runId\":\"predictionrun-1301\",\"decisionStatus\":\"ready_to_create_forecast\"}",
            "humanLineExample": "predictionrun-1301 ready_to_create_forecast forecastCloseAt=2026-06-11T04:45:00Z",
        },
        "progress": {
            "plannedRunCount": manifest["progress"]["plannedRunCount"],
            "readyToCreateForecastCount": 1,
            "forecastArtifactsCreated": 0,
            "resolvedComparableOutcomes": 0,
            "nextForecastRunId": first_run["runId"],
            "nextAction": "Implement the effectful local runner loop that creates the next forecast before close.",
        },
        "summary": {
            "terminalRunnerSurfaceImplemented": True,
            "dryRunOnly": True,
            "forecastCreationImplemented": False,
            "resolverExecutionImplemented": False,
            "writesLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "qualityClaimAllowed": False,
            "recommendedNextMilestone": "Milestone 93 effectful local forecast creation",
        },
        "executionBoundary": {
            "readOnlyDryRun": True,
            "createsForecastArtifacts": False,
            "executesForecastRunner": False,
            "sleepsOrPolls": False,
            "writesIgnoredLiveState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This runner readback checks command semantics only; it does not start a foreground loop.",
            "Forecast creation remains a later effectful milestone and must preserve forecast-before-close boundaries.",
            "Live weather and resolver execution require explicit future flags and remain disabled in normal checks.",
            "No calibration or quality claim is allowed from dry-run runner decisions.",
        ],
    }


def print_view(runner: dict[str, Any], view: str) -> None:
    views = {
        "runner": runner,
        "decisions": runner["runnerDecisions"],
        "summary": runner["summary"],
        "boundary": runner["executionBoundary"],
    }
    print(render_json(views[view]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    errors = validate_record(data, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)

    rendered = render_json(data)
    if write:
        GENERATED.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(rendered, encoding="utf-8")
        return

    if not OUTPUT_PATH.exists():
        raise SystemExit(f"Missing generated prediction campaign runner fixture: {OUTPUT_PATH}")
    existing = OUTPUT_PATH.read_text(encoding="utf-8")
    if existing != rendered:
        raise SystemExit("prediction campaign runner fixture drifted; run with --write")
    print("checked prediction campaign runner")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign runner")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign runner drift")
    parser.add_argument(
        "--view",
        choices=["runner", "decisions", "summary", "boundary"],
        default="runner",
        help="print one prediction campaign runner view",
    )
    args = parser.parse_args()

    runner = build_prediction_campaign_runner()
    if args.write or args.check:
        check_or_write(runner, write=args.write)
        return
    errors = validate_record(runner, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(runner, args.view)


if __name__ == "__main__":
    main()
