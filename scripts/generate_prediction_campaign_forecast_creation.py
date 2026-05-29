#!/usr/bin/env python3
"""Generate or check the local prediction campaign forecast-creation handoff."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-creation"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-forecast-creation.generated.json"
SCHEMA = SPEC / "prediction-campaign-forecast-creation.schema.json"
GENERATED_AT = "2026-05-29T00:30:00Z"


def readiness_check(
    index: int,
    status: str,
    *,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"forecastcreationcheck-{index:03d}",
        "checkStatus": status,
        "requiredBeforeCreation": required,
        "blocksCreation": blocks,
        "message": message,
    }


def build_readiness_checks(run: dict[str, Any], decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        readiness_check(
            1,
            "pass",
            required=True,
            blocks=False,
            message=f"{run['runId']} is bound to ready runner decision {decision['decisionId']}.",
        ),
        readiness_check(
            2,
            "pass",
            required=True,
            blocks=False,
            message=f"Forecast creation is planned before forecastCloseAt {run['forecastCloseAt']}.",
        ),
        readiness_check(
            3,
            "pass",
            required=True,
            blocks=False,
            message="Duplicate key is reserved for one campaign run and must block later duplicates.",
        ),
        readiness_check(
            4,
            "pass",
            required=True,
            blocks=False,
            message="Source policy is bound before any live or fixture evidence can be used.",
        ),
        readiness_check(
            5,
            "pass",
            required=True,
            blocks=False,
            message="Baseline-default method policy is preserved until track-record gates allow stronger methods.",
        ),
        readiness_check(
            6,
            "pass",
            required=False,
            blocks=False,
            message="Normal checks keep live fetch, resolver execution, and campaign-state writes disabled.",
        ),
    ]


def find_ready_decision(runner: dict[str, Any]) -> dict[str, Any]:
    for decision in runner["runnerDecisions"]:
        if decision["decisionStatus"] == "ready_to_create_forecast":
            return decision
    raise SystemExit("prediction campaign runner has no ready forecast creation decision")


def find_run(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in manifest["plannedRuns"]:
        if run["runId"] == run_id:
            return run
    raise SystemExit(f"prediction campaign manifest has no planned run {run_id}")


def build_prediction_campaign_forecast_creation() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    decision = find_ready_decision(runner)
    run = find_run(manifest, decision["runId"])
    run_root = f".ope/live/prediction-campaigns/predictioncampaign-001/{run['runId']}"
    return {
        "predictionCampaignForecastCreationId": "predictioncampaignforecastcreation-001",
        "generatedAt": GENERATED_AT,
        "creationStatus": "ready_dry_run_creation_request",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "repeatingPredictionSetupId": manifest["bindings"]["repeatingPredictionSetupId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": run["runId"],
            "runnerDecisionId": decision["decisionId"],
            "sourcePolicyId": run["sourcePolicyId"],
            "manifestPath": "spec/fixtures/generated/prediction-campaign-manifest/weather-transit-delay-campaign-manifest.generated.json",
            "runnerPath": "spec/fixtures/generated/prediction-campaign-runner/weather-transit-delay-campaign-runner.generated.json",
        },
        "readyRun": {
            "runId": run["runId"],
            "sequenceNumber": run["sequenceNumber"],
            "serviceDate": run["serviceDate"],
            "serviceWindow": run["serviceWindow"],
            "forecastCreateAt": run["forecastCreateAt"],
            "forecastCloseAt": run["forecastCloseAt"],
            "horizonStartsAt": run["horizonStartsAt"],
            "horizonEndsAt": run["horizonEndsAt"],
            "questionId": run["questionId"],
            "forecastId": run["forecastId"],
            "duplicateKey": run["duplicateKey"],
            "runStatus": run["runStatus"],
            "runnerDecisionStatus": decision["decisionStatus"],
        },
        "readinessChecks": build_readiness_checks(run, decision),
        "artifactPlan": {
            "questionId": run["questionId"],
            "forecastId": run["forecastId"],
            "forecastArtifactPath": f"{run_root}/{run['forecastId']}.json",
            "forecastCardPath": f"{run_root}/{run['forecastId']}-card.json",
            "lifecycleBundlePath": f"{run_root}/{run['forecastId']}-bundle.json",
            "campaignStatePath": manifest["localStatePolicy"]["campaignStatePath"],
            "writesCheckedFixtures": False,
            "writesIgnoredLiveState": False,
            "createsForecastArtifacts": False,
        },
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign forecast-create",
            "acceptedFlags": [
                "--run-id",
                "--manifest-json",
                "--setup-json",
                "--live-weather",
                "--output-format",
            ],
            "defaultMode": "dry_run_readback",
            "capturedStdoutMode": "json",
            "explicitExecutionRequired": True,
        },
        "summary": {
            "forecastCreationReadbackImplemented": True,
            "effectfulForecastCreationImplemented": False,
            "readyRunCount": 1,
            "blockedRunCount": 0,
            "artifactCreationAllowedInNormalChecks": False,
            "normalChecksUseLiveNetwork": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": "Implement explicit local artifact creation for the ready run while preserving forecast-before-close and source-policy boundaries.",
        },
        "executionBoundary": {
            "readOnlyPlanning": True,
            "createsForecastArtifacts": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesForecastMethod": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This handoff validates the ready run and planned artifact IDs only; it does not create forecast artifacts.",
            "Effectful forecast creation must still check forecastCloseAt before writing ignored local campaign state.",
            "Live evidence and resolver execution require explicit future execution flags and remain disabled in normal checks.",
            "No track-record, calibration, or quality claim is allowed from a forecast-creation request.",
        ],
    }


def print_view(creation: dict[str, Any], view: str) -> None:
    views = {
        "creation": creation,
        "run": creation["readyRun"],
        "checks": creation["readinessChecks"],
        "summary": creation["summary"],
        "boundary": creation["executionBoundary"],
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
        raise SystemExit(f"Missing generated prediction campaign forecast-creation fixture: {OUTPUT_PATH}")
    existing = OUTPUT_PATH.read_text(encoding="utf-8")
    if existing != rendered:
        raise SystemExit("prediction campaign forecast-creation fixture drifted; run with --write")
    print("checked prediction campaign forecast creation")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign forecast creation")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign forecast creation drift")
    parser.add_argument(
        "--view",
        choices=["creation", "run", "checks", "summary", "boundary"],
        default="creation",
        help="print one prediction campaign forecast creation view",
    )
    args = parser.parse_args()

    creation = build_prediction_campaign_forecast_creation()
    if args.write or args.check:
        check_or_write(creation, write=args.write)
        return
    errors = validate_record(creation, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(creation, args.view)


if __name__ == "__main__":
    main()
