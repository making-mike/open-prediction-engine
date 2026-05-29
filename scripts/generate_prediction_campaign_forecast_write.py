#!/usr/bin/env python3
"""Generate or check the local prediction campaign forecast write plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import (
    OUTPUT_NAMES as FORECAST_ARTIFACT_OUTPUT_NAMES,
    build_prediction_campaign_forecast_artifact,
)
from generate_prediction_campaign_forecast_creation import build_prediction_campaign_forecast_creation
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-write"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-forecast-write.generated.json"
FORECAST_ARTIFACT_FIXTURE_DIR = (
    ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-artifact"
)
SCHEMA = SPEC / "prediction-campaign-forecast-write.schema.json"
GENERATED_AT = "2026-05-29T01:00:00Z"


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def content_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(render_json(data).encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def write_guard(
    index: int,
    *,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "guardId": f"forecastwriteguard-{index:03d}",
        "guardStatus": status,
        "requiredBeforeWrite": required,
        "blocksWrite": blocks,
        "message": message,
    }


def build_source_artifact(
    record_type: str,
    record_id: str,
    fixture_name: str,
    target_path: str,
    schema_file: str,
    data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "recordType": record_type,
        "recordId": record_id,
        "fixturePath": rel(FORECAST_ARTIFACT_FIXTURE_DIR / fixture_name),
        "targetPath": target_path,
        "contentHash": content_hash(data),
        "schemaFile": schema_file,
    }


def build_prediction_campaign_forecast_write() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    creation = build_prediction_campaign_forecast_creation()
    records = build_prediction_campaign_forecast_artifact()
    run = creation["readyRun"]
    bindings = creation["bindings"]
    campaign = manifest["campaign"]
    run_root = f".ope/live/prediction-campaigns/{campaign['campaignId']}/{run['runId']}"
    target_state = {
        "workspaceRoot": manifest["localStatePolicy"]["workspaceRoot"],
        "campaignStatePath": manifest["localStatePolicy"]["campaignStatePath"],
        "runStatePath": f".ope/live/prediction-campaigns/{campaign['campaignId']}/{run['runId']}.json",
        "artifactDirectory": run_root,
        "questionPath": f"{run_root}/{run['questionId']}.json",
        "evidencePacketPath": f"{run_root}/{records['evidence']['evidencePacketId']}.json",
        "forecastArtifactPath": f"{run_root}/{run['forecastId']}.json",
        "forecastHistoryPath": f"{run_root}/{records['history']['historyId']}.json",
        "idempotencyKey": f"{campaign['campaignId']}:{run['runId']}:{run['forecastId']}",
        "relativePathsOnly": True,
        "gitIgnored": True,
        "normalChecksWriteLiveState": False,
        "credentialsStored": False,
        "privateRowsStored": False,
        "sanitizedDiagnosticsOnly": True,
    }
    source_artifacts = [
        build_source_artifact(
            "forecast_question",
            run["questionId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["question"],
            target_state["questionPath"],
            "spec/forecast-question.schema.json",
            records["question"],
        ),
        build_source_artifact(
            "evidence_packet",
            records["evidence"]["evidencePacketId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["evidence"],
            target_state["evidencePacketPath"],
            "spec/evidence-packet.schema.json",
            records["evidence"],
        ),
        build_source_artifact(
            "forecast_artifact",
            run["forecastId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["artifact"],
            target_state["forecastArtifactPath"],
            "spec/forecast-artifact.schema.json",
            records["artifact"],
        ),
        build_source_artifact(
            "forecast_history",
            records["history"]["historyId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["history"],
            target_state["forecastHistoryPath"],
            "spec/forecast-history.schema.json",
            records["history"],
        ),
    ]
    guards = [
        write_guard(
            1,
            status="pass",
            required=True,
            blocks=False,
            message="All source lifecycle records validate against the standard OPE schemas.",
        ),
        write_guard(
            2,
            status="pass",
            required=True,
            blocks=False,
            message=f"{run['runId']} is bound to ready forecast-creation decision {bindings['runnerDecisionId']}.",
        ),
        write_guard(
            3,
            status="pass",
            required=True,
            blocks=False,
            message=f"Forecast artifact {run['forecastId']} is forecasted before close time {run['forecastCloseAt']}.",
        ),
        write_guard(
            4,
            status="pass",
            required=True,
            blocks=False,
            message="Forecast close time remains before the horizon starts, preserving forecast-before-outcome evidence.",
        ),
        write_guard(
            5,
            status="pass",
            required=True,
            blocks=False,
            message=f"Source policy {bindings['sourcePolicyId']} is bound before local campaign artifacts can be written.",
        ),
        write_guard(
            6,
            status="pass",
            required=True,
            blocks=False,
            message="Duplicate key is already reserved by the campaign manifest and must block later duplicate writes.",
        ),
        write_guard(
            7,
            status="pass",
            required=True,
            blocks=False,
            message="Target paths are relative ignored .ope/live paths and normal checks do not write them.",
        ),
        write_guard(
            8,
            status="pass",
            required=False,
            blocks=False,
            message="The write plan does not fetch live data, execute resolvers, create scores, or append corpus evidence.",
        ),
    ]
    return {
        "predictionCampaignForecastWriteId": "predictioncampaignforecastwrite-001",
        "generatedAt": GENERATED_AT,
        "writeStatus": "ready_for_explicit_local_write",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "predictionCampaignForecastCreationId": creation["predictionCampaignForecastCreationId"],
            "repeatingPredictionSetupId": bindings["repeatingPredictionSetupId"],
            "campaignId": campaign["campaignId"],
            "cycleId": campaign["cycleId"],
            "runId": run["runId"],
            "runnerDecisionId": bindings["runnerDecisionId"],
            "questionId": run["questionId"],
            "forecastId": run["forecastId"],
            "evidencePacketId": records["evidence"]["evidencePacketId"],
            "historyId": records["history"]["historyId"],
            "sourcePolicyId": bindings["sourcePolicyId"],
            "manifestPath": bindings["manifestPath"],
            "forecastCreationPath": "spec/fixtures/generated/prediction-campaign-forecast-creation/weather-transit-delay-campaign-forecast-creation.generated.json",
            "forecastArtifactFixtureDirectory": rel(FORECAST_ARTIFACT_FIXTURE_DIR),
        },
        "sourceArtifacts": source_artifacts,
        "targetState": target_state,
        "writeGuards": guards,
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign forecast-write",
            "acceptedFlags": [
                "--run-id",
                "--manifest-json",
                "--write-local",
                "--output-format",
            ],
            "defaultMode": "checked_write_plan",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "normalChecksExecuteWrite": False,
        },
        "summary": {
            "forecastWritePlanImplemented": True,
            "effectfulLocalWriteImplemented": False,
            "lifecycleRecordCount": len(source_artifacts),
            "writeGuardCount": len(guards),
            "writesIgnoredLiveStateInNormalChecks": False,
            "normalChecksUseLiveNetwork": False,
            "resolverExecutionImplemented": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": "Implement guarded --write-local artifact copy and campaign state update with idempotency checks.",
        },
        "executionBoundary": {
            "readOnlyWritePlan": True,
            "createsCheckedLifecycleFixtures": False,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesForecastMethod": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This write plan validates source and target bindings only; it does not write .ope/live state.",
            "Effectful local writes must require an explicit future --write-local path and preserve idempotency.",
            "Resolution, scoring, corpus append, and quality claims remain separate later steps.",
            "Normal checks validate checked fixtures without live network access or ignored state mutation.",
        ],
    }


def print_view(plan: dict[str, Any], view: str) -> None:
    views = {
        "plan": plan,
        "artifacts": plan["sourceArtifacts"],
        "target": plan["targetState"],
        "guards": plan["writeGuards"],
        "summary": plan["summary"],
        "boundary": plan["executionBoundary"],
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
        raise SystemExit(f"Missing generated prediction campaign forecast write fixture: {OUTPUT_PATH}")
    existing = OUTPUT_PATH.read_text(encoding="utf-8")
    if existing != rendered:
        raise SystemExit("prediction campaign forecast write fixture drifted; run with --write")
    print("checked prediction campaign forecast write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign forecast write plan")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign forecast write drift")
    parser.add_argument(
        "--view",
        choices=["plan", "artifacts", "target", "guards", "summary", "boundary"],
        default="plan",
        help="print one prediction campaign forecast write view",
    )
    args = parser.parse_args()

    plan = build_prediction_campaign_forecast_write()
    if args.write or args.check:
        check_or_write(plan, write=args.write)
        return
    errors = validate_record(plan, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(plan, args.view)


if __name__ == "__main__":
    main()
