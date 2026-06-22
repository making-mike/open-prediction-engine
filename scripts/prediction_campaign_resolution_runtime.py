#!/usr/bin/env python3
"""Runtime helpers for explicit local prediction campaign resolution writes."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import (
    EVENT_THRESHOLD,
    GEOGRAPHY,
    LATE_SECONDS,
    MIN_OBSERVATIONS,
    NETWORK,
)
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from ope_fixtures import render_json
from ope_schema import SPEC, validate_record
from ope_scoring import baseline_lift, score_forecast_output
from prediction_campaign_forecast_write_runtime import ensure_safe_local_path, read_json
from run_transit_delay_forecast import load_rows, resolve_trip_updates


ROOT = Path(__file__).resolve().parents[1]


class PredictionCampaignResolutionError(Exception):
    pass


def now_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def run_for_id(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    for run in manifest["plannedRuns"]:
        if run["runId"] == run_id:
            return run
    raise PredictionCampaignResolutionError(f"prediction campaign manifest has no planned run {run_id}")


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def content_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(render_json(data).encode("utf-8")).hexdigest()


def local_uri(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        rel = path.resolve()
    normalized = str(rel).replace("\\", "/")
    return f"local://{normalized}"


def source_file(path_value: str) -> Path:
    path = Path(path_value)
    if ".." in path.parts:
        raise PredictionCampaignResolutionError(f"Refusing parent traversal in outcome source path: {path_value}")
    target = path if path.is_absolute() else ROOT / path
    try:
        target.resolve().relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PredictionCampaignResolutionError(
            f"Outcome source must be inside this workspace: {path_value}"
        ) from exc
    if not target.exists():
        raise PredictionCampaignResolutionError(f"Outcome source not found: {path_value}")
    return target


def read_validated_local(path_value: str, schema_name: str) -> dict[str, Any]:
    path = ensure_safe_local_path(path_value, workspace_root=ROOT)
    if not path.exists():
        raise PredictionCampaignResolutionError(f"Required campaign forecast artifact is missing: {path_value}")
    data = read_json(path)
    errors = validate_record(data, SPEC / schema_name)
    if errors:
        raise PredictionCampaignResolutionError(f"Local campaign artifact failed validation: {errors[0]}")
    return data


def build_resolution_source(
    *,
    source_template: dict[str, Any],
    outcome_csv: str | None,
    resolved_at: str,
) -> dict[str, Any]:
    if outcome_csv is None:
        return {
            "sourceId": source_template["sourceId"],
            "name": source_template["name"],
            "sourceType": source_template["sourceType"],
        }
    path = source_file(outcome_csv)
    ref = {
        "sourceId": source_template["sourceId"],
        "name": source_template["name"],
        "sourceType": source_template["sourceType"],
        "uri": local_uri(path),
        "contentHash": hashlib.sha256(path.read_bytes()).hexdigest(),
        "retrievedAt": resolved_at,
    }
    return ref


def outcome_from_source(
    *,
    run: dict[str, Any],
    outcome_csv: str | None,
    missing_outcome: bool,
) -> dict[str, Any]:
    if outcome_csv and missing_outcome:
        raise PredictionCampaignResolutionError("--outcome-csv cannot be combined with --missing-outcome")
    if missing_outcome:
        return {
            "status": "ambiguous",
            "observationCount": 0,
            "lateCount": 0,
            "lateRatio": 0.0,
            "outcome": None,
            "reason": "missing_outcome: no declared campaign outcome source was available for this service window",
        }
    if outcome_csv is None:
        raise PredictionCampaignResolutionError("--outcome-csv or --missing-outcome is required with --write-local")
    path = source_file(outcome_csv)
    return resolve_trip_updates(
        load_rows(path),
        NETWORK,
        GEOGRAPHY,
        run["serviceWindow"],
        run["serviceDate"],
        LATE_SECONDS,
        EVENT_THRESHOLD,
        MIN_OBSERVATIONS,
        horizon_start=run["horizonStartsAt"],
        resolve_at=run["resolutionEligibleAt"],
    )


def build_resolution_and_scoring(
    *,
    run: dict[str, Any],
    question: dict[str, Any],
    artifact: dict[str, Any],
    history: dict[str, Any],
    outcome_summary: dict[str, Any],
    outcome_csv: str | None,
    resolved_at: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_template = artifact["resolutionPlan"]["primaryResolutionSource"]
    source = build_resolution_source(source_template=source_template, outcome_csv=outcome_csv, resolved_at=resolved_at)
    supporting_evidence = [source["uri"]] if "uri" in source else []
    if outcome_summary["status"] == "resolved":
        resolved_outcome = {
            "outputType": "binary",
            "value": bool(outcome_summary["outcome"]),
        }
        resolution = {
            "resolutionRecordId": run["resolutionId"],
            "questionId": question["questionId"],
            "status": "resolved",
            "resolvedAt": resolved_at,
            "resolutionSource": source,
            "resolutionAuthority": question["resolutionAuthority"],
            "resolvedOutcome": resolved_outcome,
            "supportingEvidence": supporting_evidence,
        }
        primary_score = score_forecast_output(artifact["forecastOutput"], resolved_outcome, "brier")
        baseline_score = score_forecast_output(artifact["baselineForecast"], resolved_outcome, "brier")
        scoring = {
            "scoringReportId": run["scoringReportId"],
            "questionId": question["questionId"],
            "forecastId": artifact["forecastId"],
            "historyId": history["historyId"],
            "resolutionRecordId": resolution["resolutionRecordId"],
            "scoreStatus": "scored",
            "scoringRule": "brier",
            "primaryScore": round_float(primary_score),
            "higherIsBetter": False,
            "timeWeighting": {
                "method": "latest_only",
                "totalWeight": 1.0,
            },
            "baselineScore": round_float(baseline_score),
            "baselineLift": round_float(baseline_lift(primary_score, baseline_score)),
            "generatedAt": resolved_at,
        }
        return resolution, scoring

    reason = str(outcome_summary["reason"])
    resolution = {
        "resolutionRecordId": run["resolutionId"],
        "questionId": question["questionId"],
        "status": "ambiguous",
        "resolvedAt": resolved_at,
        "resolutionSource": source,
        "resolutionAuthority": question["resolutionAuthority"],
        "unscorableReason": reason,
        "supportingEvidence": supporting_evidence,
    }
    scoring = {
        "scoringReportId": run["scoringReportId"],
        "questionId": question["questionId"],
        "forecastId": artifact["forecastId"],
        "historyId": history["historyId"],
        "resolutionRecordId": resolution["resolutionRecordId"],
        "scoreStatus": "excluded",
        "scoringRule": "not_scored",
        "excludedReason": reason,
        "generatedAt": resolved_at,
    }
    return resolution, scoring


def validate_lifecycle_records(resolution: dict[str, Any], scoring: dict[str, Any]) -> None:
    for record, schema_name in [
        (resolution, "resolution-record.schema.json"),
        (scoring, "scoring-report.schema.json"),
    ]:
        errors = validate_record(record, SPEC / schema_name)
        if errors:
            raise PredictionCampaignResolutionError(f"Campaign resolution output failed validation: {errors[0]}")


def target_paths(plan: dict[str, Any], run: dict[str, Any]) -> dict[str, str]:
    artifact_dir = plan["targetState"]["artifactDirectory"]
    return {
        "resolutionPath": f"{artifact_dir}/{run['resolutionId']}.json",
        "scoringReportPath": f"{artifact_dir}/{run['scoringReportId']}.json",
    }


def preflight_record_target(path_value: str, data: dict[str, Any]) -> None:
    path = ensure_safe_local_path(path_value, workspace_root=ROOT)
    if path.exists():
        expected = content_hash(data)
        existing_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_hash != expected:
            raise PredictionCampaignResolutionError(f"Refusing to overwrite different existing record: {path_value}")


def write_record_if_safe(path_value: str, data: dict[str, Any], record_type: str, record_id: str) -> dict[str, Any]:
    preflight_record_target(path_value, data)
    path = ensure_safe_local_path(path_value, workspace_root=ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        status = "already_present"
    else:
        path.write_text(render_json(data), encoding="utf-8")
        status = "written"
    return {
        "recordType": record_type,
        "recordId": record_id,
        "targetPath": path_value,
        "writeStatus": status,
        "contentHash": content_hash(data),
    }


def update_run_state(
    *,
    plan: dict[str, Any],
    run: dict[str, Any],
    paths: dict[str, str],
    scoring: dict[str, Any],
    outcome_summary: dict[str, Any],
    written_at: str,
) -> dict[str, Any]:
    state_path = plan["targetState"]["runStatePath"]
    path = ensure_safe_local_path(state_path, workspace_root=ROOT)
    if not path.exists():
        raise PredictionCampaignResolutionError(
            f"Local run state is missing; write the forecast before resolving: {state_path}"
        )
    state = read_json(path)
    if state.get("runId") != run["runId"]:
        raise PredictionCampaignResolutionError(f"Local run state runId mismatch: {state_path}")
    updated = dict(state)
    artifact_paths = dict(updated.get("artifactPaths", {}))
    artifact_paths.update(paths)
    run_status = "scored" if scoring["scoreStatus"] == "scored" else "ambiguous"
    updated.update(
        {
            "writtenAt": written_at,
            "runStatus": run_status,
            "resolutionId": run["resolutionId"],
            "scoringReportId": run["scoringReportId"],
            "artifactPaths": artifact_paths,
            "outcomeSummary": {
                "scoreStatus": scoring["scoreStatus"],
                "observationCount": outcome_summary["observationCount"],
                "lateCount": outcome_summary["lateCount"],
                "lateRatio": outcome_summary["lateRatio"],
                "outcomeLabel": "unknown"
                if outcome_summary["outcome"] is None
                else "yes"
                if outcome_summary["outcome"]
                else "no",
            },
        }
    )
    boundary = dict(updated.get("executionBoundary", {}))
    boundary.update(
        {
            "executesResolvers": True,
            "createsResolutionArtifacts": True,
            "createsScoringRecords": True,
            "appendsCorpusEvidence": False,
            "qualityClaimAllowed": False,
        }
    )
    updated["executionBoundary"] = boundary
    if path.read_text(encoding="utf-8") == render_json(updated):
        status = "already_present"
    else:
        path.write_text(render_json(updated), encoding="utf-8")
        status = "updated"
    return {
        "stateType": "prediction_campaign_run_state",
        "targetPath": state_path,
        "writeStatus": status,
    }


def update_campaign_state(
    *,
    manifest: dict[str, Any],
    plan: dict[str, Any],
    scoring: dict[str, Any],
    written_at: str,
) -> dict[str, Any]:
    state_path = manifest["localStatePolicy"]["campaignStatePath"]
    path = ensure_safe_local_path(state_path, workspace_root=ROOT)
    if not path.exists():
        raise PredictionCampaignResolutionError(
            f"Local campaign state is missing; write the forecast before resolving: {state_path}"
        )
    state = read_json(path)
    if state.get("campaignId") != manifest["campaign"]["campaignId"]:
        raise PredictionCampaignResolutionError(f"Local campaign state campaignId mismatch: {state_path}")
    key = plan["targetState"]["idempotencyKey"]
    updated = dict(state)
    resolved_keys = list(updated.get("resolvedRunIdempotencyKeys", []))
    excluded_keys = list(updated.get("excludedRunIdempotencyKeys", []))
    if scoring["scoreStatus"] == "scored":
        if key not in resolved_keys:
            resolved_keys.append(key)
    elif key not in excluded_keys:
        excluded_keys.append(key)
    updated.update(
        {
            "writtenAt": written_at,
            "resolvedRunIdempotencyKeys": resolved_keys,
            "excludedRunIdempotencyKeys": excluded_keys,
            "resolvedComparableOutcomes": len(resolved_keys),
            "excludedOutcomeCount": len(excluded_keys),
            "nextAction": "Append the resolved campaign outcome to the evidence ledger when explicitly requested.",
        }
    )
    boundary = dict(updated.get("executionBoundary", {}))
    boundary.update(
        {
            "executesResolvers": True,
            "appendsCorpusEvidence": False,
            "qualityClaimAllowed": False,
        }
    )
    updated["executionBoundary"] = boundary
    if path.read_text(encoding="utf-8") == render_json(updated):
        status = "already_present"
    else:
        path.write_text(render_json(updated), encoding="utf-8")
        status = "updated"
    return {
        "stateType": "prediction_campaign_state",
        "targetPath": state_path,
        "writeStatus": status,
    }


def execute_local_resolution_write(
    *,
    run_id: str = "predictionrun-1301",
    now: str,
    outcome_csv: str | None = None,
    missing_outcome: bool = False,
) -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    run = run_for_id(manifest, run_id)
    if parse_utc(now) < parse_utc(run["resolutionEligibleAt"]):
        raise PredictionCampaignResolutionError(
            f"Campaign run {run_id} is not resolution-eligible until {run['resolutionEligibleAt']}"
        )
    plan = build_prediction_campaign_forecast_write(run_id=run_id if run_id != "predictionrun-1301" else None)
    target = plan["targetState"]
    question = read_validated_local(target["questionPath"], "forecast-question.schema.json")
    artifact = read_validated_local(target["forecastArtifactPath"], "forecast-artifact.schema.json")
    history = read_validated_local(target["forecastHistoryPath"], "forecast-history.schema.json")
    if artifact["questionStatus"] != "open":
        raise PredictionCampaignResolutionError(f"Campaign forecast is already terminal: {artifact['forecastId']}")
    if artifact["forecastId"] != run["forecastId"] or question["questionId"] != run["questionId"]:
        raise PredictionCampaignResolutionError(f"Local forecast artifacts do not bind to campaign run {run_id}")

    paths = target_paths(plan, run)
    existing_resolution_path = ensure_safe_local_path(paths["resolutionPath"], workspace_root=ROOT)
    if existing_resolution_path.exists():
        existing_resolution = read_json(existing_resolution_path)
        written_at = str(existing_resolution.get("resolvedAt") or now_timestamp())
    else:
        written_at = now_timestamp()
    outcome_summary = outcome_from_source(run=run, outcome_csv=outcome_csv, missing_outcome=missing_outcome)
    resolution, scoring = build_resolution_and_scoring(
        run=run,
        question=question,
        artifact=artifact,
        history=history,
        outcome_summary=outcome_summary,
        outcome_csv=outcome_csv,
        resolved_at=written_at,
    )
    validate_lifecycle_records(resolution, scoring)
    artifact_writes = [
        write_record_if_safe(paths["resolutionPath"], resolution, "resolution_record", resolution["resolutionRecordId"]),
        write_record_if_safe(paths["scoringReportPath"], scoring, "scoring_report", scoring["scoringReportId"]),
    ]
    state_writes = [
        update_run_state(
            plan=plan,
            run=run,
            paths=paths,
            scoring=scoring,
            outcome_summary=outcome_summary,
            written_at=written_at,
        ),
        update_campaign_state(
            manifest=manifest,
            plan=plan,
            scoring=scoring,
            written_at=written_at,
        ),
    ]
    rows = artifact_writes + state_writes
    new_count = len([row for row in rows if row["writeStatus"] in ("written", "updated")])
    already_count = len([row for row in rows if row["writeStatus"] == "already_present"])
    status = (
        "local_resolution_scored"
        if scoring["scoreStatus"] == "scored"
        else "local_resolution_excluded"
    )
    if new_count == 0:
        status = f"{status}_already_present"
    return {
        "predictionCampaignResolutionAttemptId": f"predictioncampaignresolutionattempt-{run_id.rsplit('-', 1)[-1]}",
        "generatedAt": written_at,
        "resolutionWriteStatus": status,
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignForecastWriteId": plan["predictionCampaignForecastWriteId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": run["runId"],
            "questionId": run["questionId"],
            "forecastId": run["forecastId"],
            "resolutionId": run["resolutionId"],
            "scoringReportId": run["scoringReportId"],
            "sourcePolicyId": run["sourcePolicyId"],
        },
        "sourceFetchMetadata": {
            "fetchAttempted": outcome_csv is not None,
            "sourceProvider": "local_transit_outcome_csv" if outcome_csv else "missing_outcome_exclusion",
            "sourceRole": "resolution_outcome",
            "liveNetworkUsed": False,
            "localOutcomePath": outcome_csv or "none",
            "sanitizedOnly": True,
        },
        "outcomeSummary": {
            "outcomeStatus": outcome_summary["status"],
            "scoreStatus": scoring["scoreStatus"],
            "observationCount": outcome_summary["observationCount"],
            "lateCount": outcome_summary["lateCount"],
            "lateRatio": outcome_summary["lateRatio"],
            "outcomeLabel": "unknown"
            if outcome_summary["outcome"] is None
            else "yes"
            if outcome_summary["outcome"]
            else "no",
        },
        "artifactWrites": artifact_writes,
        "stateWrites": state_writes,
        "summary": {
            "resolverExecutionImplemented": True,
            "resolutionArtifactsCreated": True,
            "scoringRecordsCreated": True,
            "scoreStatus": scoring["scoreStatus"],
            "newFileWriteCount": new_count,
            "alreadyPresentCount": already_count,
            "writesIgnoredLiveState": True,
            "appendsCorpusEvidence": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": "Run prediction-campaign append only after reviewing the scored or excluded resolution output.",
        },
        "executionBoundary": {
            "readsIgnoredLiveState": True,
            "writesIgnoredLiveState": True,
            "writesCampaignState": True,
            "fetchesLiveData": False,
            "executesResolvers": True,
            "createsResolutionArtifacts": True,
            "createsScoringRecords": True,
            "appendsCorpusEvidence": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
    }
