#!/usr/bin/env python3
"""Generate or check the local prediction campaign forecast write plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
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
from ope_fixtures import check_generated, compact_json, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-write"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-forecast-write.generated.json"
FORECAST_ARTIFACT_FIXTURE_DIR = (
    ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-artifact"
)
SCHEMA = SPEC / "prediction-campaign-forecast-write.schema.json"
GENERATED_AT = "2026-05-29T01:00:00Z"
LOCAL_STATE_ROOT = ".ope/live/prediction-campaigns"


class PredictionCampaignForecastWriteError(Exception):
    pass


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


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_safe_local_path(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        raise PredictionCampaignForecastWriteError(f"Refusing absolute local campaign path: {path_value}")
    if ".." in path.parts:
        raise PredictionCampaignForecastWriteError(f"Refusing parent traversal in local campaign path: {path_value}")
    root_parts = Path(LOCAL_STATE_ROOT).parts
    if path.parts[: len(root_parts)] != root_parts:
        raise PredictionCampaignForecastWriteError(
            f"Refusing path outside {LOCAL_STATE_ROOT}: {path_value}"
        )
    return ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PredictionCampaignForecastWriteError(f"Invalid JSON at {rel(path)}") from exc
    if not isinstance(data, dict):
        raise PredictionCampaignForecastWriteError(f"Expected JSON object at {rel(path)}")
    return data


def validate_source_artifact(artifact: dict[str, Any]) -> str:
    fixture_path = ROOT / artifact["fixturePath"]
    if not fixture_path.exists():
        raise PredictionCampaignForecastWriteError(f"Missing source artifact fixture: {artifact['fixturePath']}")
    data = read_json(fixture_path)
    expected_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    if expected_hash != artifact["contentHash"]:
        raise PredictionCampaignForecastWriteError(
            f"Source artifact hash drifted for {artifact['fixturePath']}"
        )
    schema_path = ROOT / artifact["schemaFile"]
    errors = validate_record(data, schema_path)
    if errors:
        joined = "; ".join(errors)
        raise PredictionCampaignForecastWriteError(
            f"Source artifact {artifact['fixturePath']} failed schema validation: {joined}"
        )
    return fixture_path.read_text(encoding="utf-8")


def preflight_artifact_target(artifact: dict[str, Any]) -> None:
    validate_source_artifact(artifact)
    target_path = ensure_safe_local_path(artifact["targetPath"])
    if target_path.exists():
        existing_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        if existing_hash != artifact["contentHash"]:
            raise PredictionCampaignForecastWriteError(
                f"Refusing to overwrite different existing artifact: {artifact['targetPath']}"
            )


def write_artifact_if_safe(artifact: dict[str, Any]) -> dict[str, Any]:
    rendered = validate_source_artifact(artifact)
    target_path = ensure_safe_local_path(artifact["targetPath"])
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        existing_hash = hashlib.sha256(target_path.read_bytes()).hexdigest()
        if existing_hash != artifact["contentHash"]:
            raise PredictionCampaignForecastWriteError(
                f"Refusing to overwrite different existing artifact: {artifact['targetPath']}"
            )
        status = "already_present"
    else:
        target_path.write_text(rendered, encoding="utf-8")
        status = "written"
    return {
        "recordType": artifact["recordType"],
        "recordId": artifact["recordId"],
        "targetPath": artifact["targetPath"],
        "writeStatus": status,
        "contentHash": artifact["contentHash"],
    }


def build_run_state(plan: dict[str, Any], written_at: str) -> dict[str, Any]:
    bindings = plan["bindings"]
    target = plan["targetState"]
    return {
        "stateType": "prediction_campaign_run_state",
        "stateVersion": 1,
        "writtenAt": written_at,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "runId": bindings["runId"],
        "questionId": bindings["questionId"],
        "forecastId": bindings["forecastId"],
        "evidencePacketId": bindings["evidencePacketId"],
        "historyId": bindings["historyId"],
        "sourcePolicyId": bindings["sourcePolicyId"],
        "idempotencyKey": target["idempotencyKey"],
        "runStatus": "waiting_resolution",
        "artifactPaths": {
            "questionPath": target["questionPath"],
            "evidencePacketPath": target["evidencePacketPath"],
            "forecastArtifactPath": target["forecastArtifactPath"],
            "forecastHistoryPath": target["forecastHistoryPath"],
        },
        "executionBoundary": {
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
    }


def build_campaign_state(plan: dict[str, Any], written_at: str) -> dict[str, Any]:
    bindings = plan["bindings"]
    target = plan["targetState"]
    return {
        "stateType": "prediction_campaign_state",
        "stateVersion": 1,
        "writtenAt": written_at,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "sourceManifestPath": plan["bindings"]["manifestPath"],
        "runStatePaths": [target["runStatePath"]],
        "createdRunIdempotencyKeys": [target["idempotencyKey"]],
        "forecastArtifactsCreated": 1,
        "resolvedComparableOutcomes": 0,
        "nextAction": "Wait until the campaign forecast is eligible for resolution.",
        "executionBoundary": {
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
    }


def preflight_state_target(path_value: str, idempotency_key: str) -> None:
    target_path = ensure_safe_local_path(path_value)
    if target_path.exists():
        existing = read_json(target_path)
        existing_key = existing.get("idempotencyKey")
        existing_keys = existing.get("createdRunIdempotencyKeys", [])
        if existing_key != idempotency_key and idempotency_key not in existing_keys:
            raise PredictionCampaignForecastWriteError(
                f"Refusing to overwrite different existing campaign state: {path_value}"
            )


def write_state_if_safe(path_value: str, state: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
    target_path = ensure_safe_local_path(path_value)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        existing = read_json(target_path)
        existing_key = existing.get("idempotencyKey")
        existing_keys = existing.get("createdRunIdempotencyKeys", [])
        if existing_key != idempotency_key and idempotency_key not in existing_keys:
            raise PredictionCampaignForecastWriteError(
                f"Refusing to overwrite different existing campaign state: {path_value}"
            )
        status = "already_present"
    else:
        target_path.write_text(render_json(state), encoding="utf-8")
        status = "written"
    return {
        "stateType": state["stateType"],
        "targetPath": path_value,
        "writeStatus": status,
    }


def preflight_local_write(plan: dict[str, Any]) -> None:
    target = plan["targetState"]
    for artifact in plan["sourceArtifacts"]:
        preflight_artifact_target(artifact)
    preflight_state_target(target["runStatePath"], target["idempotencyKey"])
    preflight_state_target(target["campaignStatePath"], target["idempotencyKey"])


def execute_local_forecast_write(plan: dict[str, Any] | None = None) -> dict[str, Any]:
    if plan is None:
        plan = build_prediction_campaign_forecast_write()
    blocking_guards = [guard for guard in plan["writeGuards"] if guard["blocksWrite"]]
    if blocking_guards:
        guard_ids = ", ".join(guard["guardId"] for guard in blocking_guards)
        raise PredictionCampaignForecastWriteError(f"Forecast write blocked by guards: {guard_ids}")

    preflight_local_write(plan)
    written_at = now_timestamp()
    artifact_writes = [write_artifact_if_safe(artifact) for artifact in plan["sourceArtifacts"]]
    run_state = build_run_state(plan, written_at)
    campaign_state = build_campaign_state(plan, written_at)
    target = plan["targetState"]
    state_writes = [
        write_state_if_safe(target["runStatePath"], run_state, target["idempotencyKey"]),
        write_state_if_safe(target["campaignStatePath"], campaign_state, target["idempotencyKey"]),
    ]
    write_rows = artifact_writes + state_writes
    written_count = len([item for item in write_rows if item["writeStatus"] == "written"])
    already_count = len([item for item in write_rows if item["writeStatus"] == "already_present"])
    write_status = "local_write_completed" if written_count else "local_write_already_present"
    return {
        "predictionCampaignForecastWriteId": plan["predictionCampaignForecastWriteId"],
        "generatedAt": written_at,
        "writeStatus": write_status,
        "domain": plan["domain"],
        "bindings": plan["bindings"],
        "idempotencyKey": target["idempotencyKey"],
        "artifactWrites": artifact_writes,
        "stateWrites": state_writes,
        "summary": {
            "effectfulLocalWriteImplemented": True,
            "forecastArtifactsCreated": 1,
            "lifecycleRecordCount": len(artifact_writes),
            "stateRecordCount": len(state_writes),
            "newFileWriteCount": written_count,
            "alreadyPresentCount": already_count,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "qualityClaimAllowed": False,
            "nextAction": "Wait for the campaign forecast resolution window, then inspect campaign-aware resolution jobs.",
        },
        "executionBoundary": {
            "writesIgnoredLiveState": True,
            "writesCampaignState": True,
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
    }


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
    errors = validate_record(data, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    if write:
        write_generated(OUTPUT_PATH, data, label="prediction campaign forecast write", regen="python3 scripts/generate_prediction_campaign_forecast_write.py --write")
    else:
        check_generated(OUTPUT_PATH, data, label="prediction campaign forecast write", regen="python3 scripts/generate_prediction_campaign_forecast_write.py --write")


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

    plan = build_prediction_campaign_forecast_write()
    if args.run_id and args.run_id != plan["bindings"]["runId"]:
        raise SystemExit(f"Unsupported campaign run ID for checked write plan: {args.run_id}")
    if args.manifest_json:
        raise SystemExit("--manifest-json is reserved for a later campaign runner slice")
    if args.write or args.check:
        if args.write_local:
            raise SystemExit("--write-local cannot be combined with --write or --check")
        check_or_write(plan, write=args.write)
        return
    if args.write_local:
        try:
            result = execute_local_forecast_write(plan)
        except PredictionCampaignForecastWriteError as exc:
            raise SystemExit(str(exc)) from exc
        print_write_result(result, args.output_format)
        return
    errors = validate_record(plan, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(plan, args.view)


if __name__ == "__main__":
    main()
