#!/usr/bin/env python3
"""Generate or check the local prediction campaign forecast write plan."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import (
    OUTPUT_NAMES as FORECAST_ARTIFACT_OUTPUT_NAMES,
    build_prediction_campaign_forecast_artifact,
)
from generate_prediction_campaign_forecast_creation import build_prediction_campaign_forecast_creation
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner, parse_utc
from ope_schema import SPEC, validate_record
from ope_fixtures import compact_json, render_json, validate_and_emit
from prediction_campaign_forecast_write_runtime import (
    PredictionCampaignForecastWriteError,
    execute_local_forecast_write,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-write"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-forecast-write.generated.json"
FORECAST_ARTIFACT_FIXTURE_DIR = (
    ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-artifact"
)
SCHEMA = SPEC / "prediction-campaign-forecast-write.schema.json"
GENERATED_AT = "2026-05-29T01:00:00Z"


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
    fixture_name: str | None,
    target_path: str,
    schema_file: str,
    data: dict[str, Any],
    *,
    embed_source_record: bool = False,
) -> dict[str, Any]:
    artifact: dict[str, Any] = {
        "recordType": record_type,
        "recordId": record_id,
        "fixturePath": rel(FORECAST_ARTIFACT_FIXTURE_DIR / fixture_name) if fixture_name else f"runtime://{record_type}/{record_id}",
        "targetPath": target_path,
        "contentHash": content_hash(data),
        "schemaFile": schema_file,
    }
    if embed_source_record:
        artifact["sourceRecord"] = data
    return artifact


def build_prediction_campaign_forecast_write(
    *,
    run_id: str | None = None,
    embed_source_records: bool = False,
    manifest: dict[str, Any] | None = None,
    runner: dict[str, Any] | None = None,
    pre_calibration: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if manifest is None:
        manifest = build_prediction_campaign_manifest()
    if runner is None:
        runner = build_prediction_campaign_runner()
    creation = build_prediction_campaign_forecast_creation(run_id=run_id, manifest=manifest, runner=runner)
    run = creation["readyRun"]
    bindings = creation["bindings"]
    campaign = manifest["campaign"]
    checked_fixture_run = run["runId"] == "predictionrun-1301" and not embed_source_records
    records = build_prediction_campaign_forecast_artifact(
        run_id=run_id,
        creation=creation,
        pre_calibration=pre_calibration,
        forecasted_at=None if checked_fixture_run else runner["forecastSchedule"]["runnerClock"],
    )
    forecasted_at_value = records["artifact"]["forecastedAt"]
    forecast_before_close = parse_utc(forecasted_at_value) <= parse_utc(run["forecastCloseAt"])
    write_suffix = run["runId"].split("-")[-1]
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
            FORECAST_ARTIFACT_OUTPUT_NAMES["question"] if checked_fixture_run else None,
            target_state["questionPath"],
            "spec/forecast-question.schema.json",
            records["question"],
            embed_source_record=embed_source_records,
        ),
        build_source_artifact(
            "evidence_packet",
            records["evidence"]["evidencePacketId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["evidence"] if checked_fixture_run else None,
            target_state["evidencePacketPath"],
            "spec/evidence-packet.schema.json",
            records["evidence"],
            embed_source_record=embed_source_records,
        ),
        build_source_artifact(
            "forecast_artifact",
            run["forecastId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["artifact"] if checked_fixture_run else None,
            target_state["forecastArtifactPath"],
            "spec/forecast-artifact.schema.json",
            records["artifact"],
            embed_source_record=embed_source_records,
        ),
        build_source_artifact(
            "forecast_history",
            records["history"]["historyId"],
            FORECAST_ARTIFACT_OUTPUT_NAMES["history"] if checked_fixture_run else None,
            target_state["forecastHistoryPath"],
            "spec/forecast-history.schema.json",
            records["history"],
            embed_source_record=embed_source_records,
        ),
    ]
    pre_calibration_binding = None
    if pre_calibration is not None:
        pre_calibration_binding = {
            "predictionCampaignPreCalibrationId": pre_calibration["predictionCampaignPreCalibrationId"],
            "preCalibrationStatus": pre_calibration["preCalibrationStatus"],
            "activeMethodId": pre_calibration["engineBinding"]["activeMethodId"],
            "calibratedProbability": pre_calibration["engineBinding"]["calibratedProbability"],
            "preCalibrationArtifactPath": pre_calibration["engineBinding"]["preCalibrationArtifactPath"],
            "methodBindingPath": pre_calibration["engineBinding"]["methodBindingPath"],
            "historySourcePath": pre_calibration["historySource"]["sourcePath"],
            "historySourceContentHash": pre_calibration["historySource"]["contentHash"],
            "forecastProbabilitySource": "historical_pre_calibration",
            "prospectiveOnly": True,
            "priorForecastHistoryRewriteAllowed": False,
        }
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
            status="pass" if forecast_before_close else "block",
            required=True,
            blocks=not forecast_before_close,
            message=(
                f"Forecast artifact {run['forecastId']} is forecasted at {forecasted_at_value} "
                f"before close time {run['forecastCloseAt']}."
                if forecast_before_close
                else f"Forecast artifact {run['forecastId']} would be forecasted at {forecasted_at_value} "
                f"after close time {run['forecastCloseAt']}; record the run as missed instead of backdating."
            ),
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
    plan = {
        "predictionCampaignForecastWriteId": "predictioncampaignforecastwrite-001" if checked_fixture_run else f"predictioncampaignforecastwrite-{write_suffix}",
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
            "forecastCreationPath": (
                "spec/fixtures/generated/prediction-campaign-forecast-creation/weather-transit-delay-campaign-forecast-creation.generated.json"
                if checked_fixture_run
                else "runtime://prediction-campaign-forecast-creation"
            ),
            "forecastArtifactFixtureDirectory": rel(FORECAST_ARTIFACT_FIXTURE_DIR) if checked_fixture_run else "runtime://prediction-campaign-forecast-artifact",
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
            "recommendedNextAction": "Use --write-local only when an explicit local campaign forecast write is intended.",
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
            "Effectful local writes require explicit --write-local and preserve idempotency.",
            "Resolution, scoring, corpus append, and quality claims remain separate later steps.",
            "Normal checks validate checked fixtures without live network access or ignored state mutation.",
        ],
    }
    if pre_calibration_binding is not None:
        plan["preCalibrationBinding"] = pre_calibration_binding
    return plan


def print_write_result(result: dict[str, Any], output_format: str | None) -> None:
    if output_format == "human":
        print(
            f"{result['bindings']['runId']} {result['writeStatus']} "
            f"forecastId={result['bindings']['forecastId']} newFiles={result['summary']['newFileWriteCount']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(result), end="")
        return
    print(render_json(result), end="")


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
    validate_and_emit(data, SCHEMA, OUTPUT_PATH, write=write, label="prediction campaign forecast write", regen="python3 scripts/generate_prediction_campaign_forecast_write.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign forecast write plan")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign forecast write drift")
    parser.add_argument("--run-id", help="run ID to write; only the checked ready run is supported")
    parser.add_argument("--manifest-json", help="reserved explicit manifest JSON input path")
    parser.add_argument(
        "--write-local",
        action="store_true",
        help="explicitly write the checked lifecycle records into ignored local campaign state",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for --write-local output",
    )
    parser.add_argument(
        "--view",
        choices=["plan", "artifacts", "target", "guards", "summary", "boundary"],
        default="plan",
        help="print one prediction campaign forecast write view",
    )
    args = parser.parse_args()

    if args.manifest_json:
        raise SystemExit("--manifest-json is reserved for a later campaign runner slice")
    if args.write or args.check:
        if args.write_local:
            raise SystemExit("--write-local cannot be combined with --write or --check")
        if args.run_id:
            raise SystemExit("--run-id cannot be combined with --write or --check")
        plan = build_prediction_campaign_forecast_write()
        check_or_write(plan, write=args.write)
        return
    if args.write_local:
        try:
            if args.run_id:
                from generate_prediction_campaign_runner import default_args as runner_default_args

                write_args = runner_default_args()
                write_args.write_local = True
                result = execute_local_forecast_write(
                    run_id=args.run_id,
                    manifest=build_prediction_campaign_manifest(),
                    runner=build_prediction_campaign_runner(write_args),
                )
            else:
                result = execute_local_forecast_write()
        except PredictionCampaignForecastWriteError as exc:
            raise SystemExit(str(exc)) from exc
        print_write_result(result, args.output_format)
        return
    plan = build_prediction_campaign_forecast_write()
    if args.run_id and args.run_id != plan["bindings"]["runId"]:
        raise SystemExit(f"Non-default campaign run ID requires --write-local in this runner slice: {args.run_id}")
    errors = validate_record(plan, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(plan, args.view)


if __name__ == "__main__":
    main()
