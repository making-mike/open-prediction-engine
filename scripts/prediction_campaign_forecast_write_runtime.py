#!/usr/bin/env python3
"""Runtime helpers for explicit local prediction campaign forecast writes."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from ope_fixtures import render_json
from ope_schema import validate_record


ROOT = Path(__file__).resolve().parents[1]
LOCAL_STATE_ROOT = ".ope/live/prediction-campaigns"


class PredictionCampaignForecastWriteError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise PredictionCampaignForecastWriteError(f"Invalid UTC timestamp: {value}") from exc


def forecast_close_passed(forecast_close_at: str, clock_value: str) -> bool:
    return parse_utc_timestamp(clock_value) > parse_utc_timestamp(forecast_close_at)


def plan_forecast_close_at(plan: dict[str, Any]) -> str:
    for artifact in plan["sourceArtifacts"]:
        if artifact["recordType"] != "forecast_artifact":
            continue
        record = artifact.get("sourceRecord")
        if record is None:
            record = read_json(ROOT / artifact["fixturePath"])
        return str(record["closedAt"])
    raise PredictionCampaignForecastWriteError("Forecast write plan binds no forecast artifact record")


def ensure_safe_local_path(
    path_value: str,
    *,
    workspace_root: Path = ROOT,
    local_state_root: str = LOCAL_STATE_ROOT,
) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        raise PredictionCampaignForecastWriteError(f"Refusing absolute local campaign path: {path_value}")
    if ".." in path.parts:
        raise PredictionCampaignForecastWriteError(f"Refusing parent traversal in local campaign path: {path_value}")
    root_parts = Path(local_state_root).parts
    if path.parts[: len(root_parts)] != root_parts:
        raise PredictionCampaignForecastWriteError(f"Refusing path outside {local_state_root}: {path_value}")
    target = workspace_root / path
    state_root = workspace_root.resolve() / local_state_root
    if not target.resolve().is_relative_to(state_root):
        raise PredictionCampaignForecastWriteError(
            f"Refusing symlinked local campaign path outside {local_state_root}: {path_value}"
        )
    return target


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PredictionCampaignForecastWriteError(f"Invalid JSON at {rel(path)}") from exc
    if not isinstance(data, dict):
        raise PredictionCampaignForecastWriteError(f"Expected JSON object at {rel(path)}")
    return data


def validate_source_artifact(artifact: dict[str, Any]) -> str:
    if "sourceRecord" in artifact:
        data = artifact["sourceRecord"]
        if not isinstance(data, dict):
            raise PredictionCampaignForecastWriteError(f"Runtime source artifact must be an object: {artifact['recordId']}")
        schema_path = ROOT / artifact["schemaFile"]
        errors = validate_record(data, schema_path)
        if errors:
            joined = "; ".join(errors)
            raise PredictionCampaignForecastWriteError(
                f"Runtime source artifact {artifact['recordId']} failed schema validation: {joined}"
            )
        rendered = render_json(data)
        expected_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if expected_hash != artifact["contentHash"]:
            raise PredictionCampaignForecastWriteError(
                f"Runtime source artifact hash drifted for {artifact['recordId']}"
            )
        return rendered

    fixture_path = ROOT / artifact["fixturePath"]
    if not fixture_path.exists():
        raise PredictionCampaignForecastWriteError(f"Missing source artifact fixture: {artifact['fixturePath']}")
    data = read_json(fixture_path)
    expected_hash = hashlib.sha256(fixture_path.read_bytes()).hexdigest()
    if expected_hash != artifact["contentHash"]:
        raise PredictionCampaignForecastWriteError(f"Source artifact hash drifted for {artifact['fixturePath']}")
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


def write_missed_run_state(
    *,
    campaign_id: str,
    cycle_id: str,
    run_id: str,
    question_id: str,
    forecast_id: str,
    source_policy_id: str,
    forecast_close_at: str,
    runner_clock: str,
    workspace_root: Path = ROOT,
) -> dict[str, Any]:
    """Record one missed campaign run per the skip_if_forecast_close_passed policy.

    Missed runs never create forecast artifacts and never count as created
    idempotency keys; an existing run state of any status is kept untouched.
    """
    state_path_value = f"{LOCAL_STATE_ROOT}/{campaign_id}/{run_id}.json"
    target_path = ensure_safe_local_path(state_path_value, workspace_root=workspace_root)
    if target_path.exists():
        existing = read_json(target_path)
        existing_status = str(existing.get("runStatus", "unknown"))
        return {
            "stateType": "prediction_campaign_run_state",
            "runId": run_id,
            "targetPath": state_path_value,
            "runStatus": existing_status,
            "writeStatus": "already_present" if existing_status == "missed" else "kept_existing_state",
        }
    state = {
        "stateType": "prediction_campaign_run_state",
        "stateVersion": 1,
        "writtenAt": now_timestamp(),
        "campaignId": campaign_id,
        "cycleId": cycle_id,
        "runId": run_id,
        "questionId": question_id,
        "forecastId": forecast_id,
        "sourcePolicyId": source_policy_id,
        "runStatus": "missed",
        "missedRunPolicy": "skip_if_forecast_close_passed",
        "exclusionReasonCode": "missed_forecast_close",
        "excludedFromComparableEvidence": True,
        "forecastCloseAt": forecast_close_at,
        "runnerClock": runner_clock,
        "artifactPaths": {},
        "executionBoundary": {
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
    }
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(render_json(state), encoding="utf-8")
    return {
        "stateType": "prediction_campaign_run_state",
        "runId": run_id,
        "targetPath": state_path_value,
        "runStatus": "missed",
        "writeStatus": "written",
    }


def build_campaign_state(plan: dict[str, Any], written_at: str) -> dict[str, Any]:
    bindings = plan["bindings"]
    target = plan["targetState"]
    state = {
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
    pre_calibration = plan.get("preCalibrationBinding")
    if isinstance(pre_calibration, dict):
        state.update(
            {
                "activeMethodId": pre_calibration["activeMethodId"],
                "calibratedProbability": pre_calibration["calibratedProbability"],
                "preCalibrationPath": pre_calibration["preCalibrationArtifactPath"],
                "methodBindingPath": pre_calibration["methodBindingPath"],
                "forecastProbabilitySource": pre_calibration["forecastProbabilitySource"],
            }
        )
    return state


def preflight_state_target(path_value: str, idempotency_key: str, *, allow_campaign_append: bool = False) -> None:
    target_path = ensure_safe_local_path(path_value)
    if target_path.exists():
        existing = read_json(target_path)
        existing_key = existing.get("idempotencyKey")
        existing_keys = existing.get("createdRunIdempotencyKeys", [])
        if allow_campaign_append and existing.get("stateType") == "prediction_campaign_state":
            return
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
        if state["stateType"] == "prediction_campaign_state" and existing.get("stateType") == "prediction_campaign_state":
            if idempotency_key not in existing_keys:
                merged = dict(existing)
                merged["writtenAt"] = state["writtenAt"]
                merged["runStatePaths"] = list(dict.fromkeys(existing.get("runStatePaths", []) + state["runStatePaths"]))
                merged["createdRunIdempotencyKeys"] = list(
                    dict.fromkeys(existing.get("createdRunIdempotencyKeys", []) + state["createdRunIdempotencyKeys"])
                )
                merged["forecastArtifactsCreated"] = len(merged["createdRunIdempotencyKeys"])
                merged["nextAction"] = state["nextAction"]
                for key in [
                    "activeMethodId",
                    "calibratedProbability",
                    "preCalibrationPath",
                    "methodBindingPath",
                    "forecastProbabilitySource",
                ]:
                    if key in state:
                        merged[key] = state[key]
                target_path.write_text(render_json(merged), encoding="utf-8")
                return {
                    "stateType": state["stateType"],
                    "targetPath": path_value,
                    "writeStatus": "updated",
                }
            return {
                "stateType": state["stateType"],
                "targetPath": path_value,
                "writeStatus": "already_present",
            }
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
    preflight_state_target(target["campaignStatePath"], target["idempotencyKey"], allow_campaign_append=True)


def execute_local_forecast_write(
    plan: dict[str, Any] | None = None,
    *,
    run_id: str | None = None,
    manifest: dict[str, Any] | None = None,
    runner: dict[str, Any] | None = None,
    plan_builder: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if plan is None:
        if plan_builder is None:
            from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write

            plan_builder = build_prediction_campaign_forecast_write
        plan = plan_builder(
            run_id=run_id,
            embed_source_records=run_id is not None,
            manifest=manifest,
            runner=runner,
        )
    blocking_guards = [guard for guard in plan["writeGuards"] if guard["blocksWrite"]]
    if blocking_guards:
        guard_ids = ", ".join(guard["guardId"] for guard in blocking_guards)
        raise PredictionCampaignForecastWriteError(f"Forecast write blocked by guards: {guard_ids}")

    # Forecast-before-close is enforced against real UTC now regardless of how
    # the plan's runner clock was derived; a late write is recorded as missed.
    forecast_close_at = plan_forecast_close_at(plan)
    clock_now = now_timestamp()
    if forecast_close_passed(forecast_close_at, clock_now):
        bindings = plan["bindings"]
        missed = write_missed_run_state(
            campaign_id=bindings["campaignId"],
            cycle_id=bindings["cycleId"],
            run_id=bindings["runId"],
            question_id=bindings["questionId"],
            forecast_id=bindings["forecastId"],
            source_policy_id=bindings["sourcePolicyId"],
            forecast_close_at=forecast_close_at,
            runner_clock=clock_now,
        )
        raise PredictionCampaignForecastWriteError(
            f"Refusing forecast write for {bindings['runId']}: real UTC now {clock_now} is after "
            f"forecastCloseAt {forecast_close_at}; run state recorded as missed "
            f"({missed['writeStatus']}) per skip_if_forecast_close_passed instead of backdating."
        )

    preflight_local_write(plan)
    written_at = clock_now
    artifact_writes = [write_artifact_if_safe(artifact) for artifact in plan["sourceArtifacts"]]
    run_state = build_run_state(plan, written_at)
    campaign_state = build_campaign_state(plan, written_at)
    target = plan["targetState"]
    state_writes = [
        write_state_if_safe(target["runStatePath"], run_state, target["idempotencyKey"]),
        write_state_if_safe(target["campaignStatePath"], campaign_state, target["idempotencyKey"]),
    ]
    write_rows = artifact_writes + state_writes
    written_count = len([item for item in write_rows if item["writeStatus"] in ("written", "updated")])
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
