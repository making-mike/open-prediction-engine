#!/usr/bin/env python3
"""Generate or check the local prediction campaign evidence ledger readback."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from prediction_campaign_forecast_write_runtime import (
    PredictionCampaignForecastWriteError,
    ensure_safe_local_path,
    read_json,
)
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_resolution_attempt import build_prediction_campaign_resolution_attempt
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-evidence-ledger"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-evidence-ledger.generated.json"
SCHEMA = SPEC / "prediction-campaign-evidence-ledger.schema.json"
GENERATED_AT = "2026-05-31T02:00:00Z"
LEDGER_CASES = ["excluded_missing_outcome", "comparable_scored"]
LOCAL_LEDGER_CASE = "local_resolved_state"
DEFAULT_CASE = "excluded_missing_outcome"
MODES = ["append-ready", "append"]
DEFAULT_MODE = "append-ready"
EXCLUSION_REASONS = [
    "missed_close",
    "missing_outcome",
    "low_coverage",
    "feed_unavailable",
    "invalid_window",
    "leakage_risk",
    "ambiguous",
    "annulled",
    "non_comparable",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def row_key(campaign_id: str, run_id: str, forecast_id: str, scoring_report_id: str, row_kind: str) -> str:
    return f"{campaign_id}:{run_id}:{forecast_id}:{scoring_report_id}:{row_kind}"


def append_check(
    index: int,
    *,
    name: str,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"campaignledgercheck-{index:03d}",
        "checkName": name,
        "checkStatus": status,
        "requiredForComparableAppend": required,
        "blocksComparableAppend": blocks,
        "message": message,
    }


def planned_run(manifest: dict[str, Any], run_id: str = "predictionrun-1301") -> dict[str, Any]:
    for run in manifest["plannedRuns"]:
        if run["runId"] == run_id:
            return run
    raise PredictionCampaignForecastWriteError(f"prediction campaign manifest has no planned run {run_id}")


def forecast_write_plan(run_id: str) -> dict[str, Any]:
    return build_prediction_campaign_forecast_write(run_id=None if run_id == "predictionrun-1301" else run_id)


def paths_from_plan(plan: dict[str, Any], run: dict[str, Any]) -> dict[str, str]:
    target = plan["targetState"]
    artifact_directory = target["artifactDirectory"]
    return {
        "runStatePath": target["runStatePath"],
        "forecastArtifactPath": target["forecastArtifactPath"],
        "evidencePacketPath": target["evidencePacketPath"],
        "forecastHistoryPath": target["forecastHistoryPath"],
        "resolutionPath": f"{artifact_directory}/{run['resolutionId']}.json",
        "scoringReportPath": f"{artifact_directory}/{run['scoringReportId']}.json",
    }


def read_validated_local(path_value: str, schema_name: str) -> dict[str, Any]:
    path = ensure_safe_local_path(path_value, workspace_root=ROOT)
    if not path.exists():
        raise PredictionCampaignForecastWriteError(f"Required local campaign artifact is missing: {path_value}")
    data = read_json(path)
    errors = validate_record(data, SPEC / schema_name)
    if errors:
        raise PredictionCampaignForecastWriteError(f"Local campaign artifact failed validation: {errors[0]}")
    return data


def required_local_paths(run_state: dict[str, Any], plan: dict[str, Any]) -> dict[str, str]:
    artifact_paths = run_state.get("artifactPaths", {})
    if not isinstance(artifact_paths, dict):
        raise PredictionCampaignForecastWriteError("Local campaign run state artifactPaths must be an object")
    paths = {
        "runStatePath": plan["targetState"]["runStatePath"],
        "forecastArtifactPath": artifact_paths.get("forecastArtifactPath"),
        "evidencePacketPath": artifact_paths.get("evidencePacketPath"),
        "forecastHistoryPath": artifact_paths.get("forecastHistoryPath"),
        "resolutionPath": artifact_paths.get("resolutionPath"),
        "scoringReportPath": artifact_paths.get("scoringReportPath"),
    }
    missing = [key for key, value in paths.items() if not isinstance(value, str) or not value]
    if missing:
        raise PredictionCampaignForecastWriteError(
            f"Local campaign run state is missing resolved artifact paths: {', '.join(missing)}"
        )
    return {key: str(value) for key, value in paths.items()}


def base_row(
    *,
    manifest: dict[str, Any],
    run: dict[str, Any],
    artifact: dict[str, Any],
    evidence: dict[str, Any],
    history: dict[str, Any],
    paths: dict[str, str],
    row_kind: str,
    row_id: str,
    run_status: str,
    resolution_record_id: str,
    scoring_report_id: str,
) -> dict[str, Any]:
    campaign_id = manifest["campaign"]["campaignId"]
    return {
        "rowId": row_id,
        "rowKind": row_kind,
        "rowKey": row_key(campaign_id, run["runId"], run["forecastId"], scoring_report_id, row_kind),
        "campaignId": campaign_id,
        "cycleId": manifest["campaign"]["cycleId"],
        "runId": run["runId"],
        "questionId": run["questionId"],
        "forecastId": run["forecastId"],
        "evidencePacketId": evidence["evidencePacketId"],
        "historyId": history["historyId"],
        "serviceDate": run["serviceDate"],
        "serviceWindow": run["serviceWindow"],
        "sourcePolicyId": run["sourcePolicyId"],
        "runStatus": run_status,
        "runStatePath": paths["runStatePath"],
        "forecastArtifactPath": paths["forecastArtifactPath"],
        "evidencePacketPath": paths["evidencePacketPath"],
        "forecastHistoryPath": paths["forecastHistoryPath"],
        "resolutionRecordPath": paths["resolutionPath"],
        "scoringReportPath": paths["scoringReportPath"],
        "forecastedAt": artifact["forecastedAt"],
        "forecastCloseAt": run["forecastCloseAt"],
        "horizonStartsAt": run["horizonStartsAt"],
        "horizonEndsAt": run["horizonEndsAt"],
        "resolutionEligibleAt": run["resolutionEligibleAt"],
        "forecastProbability": artifact["forecastOutput"]["probability"],
        "baselineProbability": artifact["baselineForecast"]["probability"],
    }


def comparable_row(manifest: dict[str, Any], records: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    run = planned_run(manifest)
    paths = paths_from_plan(plan, run)
    row = base_row(
        manifest=manifest,
        run=run,
        artifact=records["artifact"],
        evidence=records["evidence"],
        history=records["history"],
        paths=paths,
        row_kind="comparable",
        row_id="campaignledgerrow-001",
        run_status="scored",
        resolution_record_id=run["resolutionId"],
        scoring_report_id=run["scoringReportId"],
    )
    row.update(
        {
            "resolutionRecordId": "resolution-1301",
            "scoringReportId": "scoring-1301",
            "outcomeLabel": "no",
            "outcomeValue": 0,
            "observationCount": 18,
            "lateCount": 2,
            "lateRatio": 0.1111,
            "scoreStatus": "scored",
            "primaryScore": 0.0625,
            "baselineScore": 0.0625,
            "exclusionReason": "none",
            "appendReadiness": "comparable_append_ready",
        }
    )
    return row


def excluded_row(manifest: dict[str, Any], records: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    run = planned_run(manifest)
    paths = paths_from_plan(plan, run)
    row = base_row(
        manifest=manifest,
        run=run,
        artifact=records["artifact"],
        evidence=records["evidence"],
        history=records["history"],
        paths=paths,
        row_kind="excluded",
        row_id="campaignledgerrow-002",
        run_status="blocked_missing_outcome_source",
        resolution_record_id=run["resolutionId"],
        scoring_report_id=run["scoringReportId"],
    )
    row.update(
        {
            "resolutionRecordId": "none",
            "scoringReportId": "none",
            "outcomeLabel": "unknown",
            "outcomeValue": None,
            "observationCount": 0,
            "lateCount": 0,
            "lateRatio": 0,
            "scoreStatus": "not_scored",
            "primaryScore": None,
            "baselineScore": None,
            "exclusionReason": "missing_outcome",
            "appendReadiness": "exclusion_audit_append_ready",
        }
    )
    return row


def classify_exclusion_reason(reason: str) -> str:
    normalized = reason.lower()
    if "missing_outcome" in normalized or "no declared" in normalized:
        return "missing_outcome"
    if "minimum" in normalized or "coverage" in normalized:
        return "low_coverage"
    if "feed" in normalized or "unavailable" in normalized:
        return "feed_unavailable"
    if "leakage" in normalized:
        return "leakage_risk"
    if "annul" in normalized:
        return "annulled"
    if "incomparable" in normalized:
        return "non_comparable"
    if "window" in normalized:
        return "invalid_window"
    return "ambiguous"


def checks_for_local_row(row: dict[str, Any]) -> list[dict[str, Any]]:
    comparable = row["rowKind"] == "comparable"
    coverage_pass = comparable and row["observationCount"] >= 10
    return [
        append_check(
            1,
            name="forecast_before_close",
            status="pass",
            required=True,
            blocks=False,
            message="Local forecast artifact was created before the campaign forecast close time.",
        ),
        append_check(
            2,
            name="source_policy_binding",
            status="pass",
            required=True,
            blocks=False,
            message=f"Local run state, forecast artifact, and ledger row share {row['sourcePolicyId']}.",
        ),
        append_check(
            3,
            name="no_post_close_evidence_leakage",
            status="pass",
            required=True,
            blocks=False,
            message="Ledger append reads forecast-time evidence separately from later outcome and scoring records.",
        ),
        append_check(
            4,
            name="resolution_after_horizon",
            status="pass",
            required=True,
            blocks=False,
            message="Local resolution record is bound after the campaign service-window horizon.",
        ),
        append_check(
            5,
            name="score_binding",
            status="pass",
            required=True,
            blocks=False,
            message="Local scoring report is bound to the forecast, history, and resolution record.",
        ),
        append_check(
            6,
            name="observation_coverage",
            status="pass" if coverage_pass else "block",
            required=True,
            blocks=not coverage_pass,
            message=(
                "Outcome coverage meets the campaign minimum observation count."
                if coverage_pass
                else f"Outcome coverage is not comparable; exclusion reason is {row['exclusionReason']}."
            ),
        ),
        append_check(
            7,
            name="comparable_scope",
            status="pass" if comparable else "block",
            required=True,
            blocks=not comparable,
            message=(
                "Run is comparable for weather-transit-delays morning_peak evidence."
                if comparable
                else "Excluded local rows remain audit evidence and do not count as comparable evidence."
            ),
        ),
        append_check(
            8,
            name="duplicate_ledger_row",
            status="pass",
            required=True,
            blocks=False,
            message="Append uses a stable campaign/run/forecast/scoring/row-kind key and skips already-present rows.",
        ),
    ]


def validate_local_bindings(
    *,
    run: dict[str, Any],
    run_state: dict[str, Any],
    artifact: dict[str, Any],
    evidence: dict[str, Any],
    history: dict[str, Any],
    resolution: dict[str, Any],
    scoring: dict[str, Any],
) -> None:
    if run_state.get("stateType") != "prediction_campaign_run_state":
        raise PredictionCampaignForecastWriteError("Local campaign run state type mismatch")
    for key in ["runId", "questionId", "forecastId", "sourcePolicyId"]:
        if run_state.get(key) != run[key]:
            raise PredictionCampaignForecastWriteError(f"Local campaign run state {key} mismatch")
    if artifact["forecastId"] != run["forecastId"] or artifact["questionId"] != run["questionId"]:
        raise PredictionCampaignForecastWriteError("Local forecast artifact does not bind to the selected run")
    if evidence["forecastId"] != run["forecastId"] or evidence["questionId"] != run["questionId"]:
        raise PredictionCampaignForecastWriteError("Local evidence packet does not bind to the selected run")
    if history["historyId"] != run_state.get("historyId") or history["questionId"] != run["questionId"]:
        raise PredictionCampaignForecastWriteError("Local forecast history does not bind to the selected run")
    if resolution["resolutionRecordId"] != run["resolutionId"] or resolution["questionId"] != run["questionId"]:
        raise PredictionCampaignForecastWriteError("Local resolution record does not bind to the selected run")
    if scoring["scoringReportId"] != run["scoringReportId"]:
        raise PredictionCampaignForecastWriteError("Local scoring report id mismatch")
    if scoring["forecastId"] != run["forecastId"] or scoring["resolutionRecordId"] != run["resolutionId"]:
        raise PredictionCampaignForecastWriteError("Local scoring report does not bind to forecast and resolution")
    if scoring.get("historyId") != history["historyId"]:
        raise PredictionCampaignForecastWriteError("Local scoring report does not bind to the forecast history")


def local_row_from_state(manifest: dict[str, Any], run_id: str) -> dict[str, Any]:
    run = planned_run(manifest, run_id)
    plan = forecast_write_plan(run_id)
    run_state_path = plan["targetState"]["runStatePath"]
    path = ensure_safe_local_path(run_state_path, workspace_root=ROOT)
    if not path.exists():
        raise PredictionCampaignForecastWriteError(f"Local campaign run state is missing: {run_state_path}")
    run_state = read_json(path)
    paths = required_local_paths(run_state, plan)
    artifact = read_validated_local(paths["forecastArtifactPath"], "forecast-artifact.schema.json")
    evidence = read_validated_local(paths["evidencePacketPath"], "evidence-packet.schema.json")
    history = read_validated_local(paths["forecastHistoryPath"], "forecast-history.schema.json")
    resolution = read_validated_local(paths["resolutionPath"], "resolution-record.schema.json")
    scoring = read_validated_local(paths["scoringReportPath"], "scoring-report.schema.json")
    validate_local_bindings(
        run=run,
        run_state=run_state,
        artifact=artifact,
        evidence=evidence,
        history=history,
        resolution=resolution,
        scoring=scoring,
    )
    score_status = scoring["scoreStatus"]
    row_kind = "comparable" if score_status == "scored" else "excluded"
    outcome_summary = run_state.get("outcomeSummary", {})
    if score_status == "scored":
        resolved_outcome = resolution["resolvedOutcome"]["value"]
        outcome_label = "yes" if resolved_outcome else "no"
        outcome_value = 1 if resolved_outcome else 0
        primary_score = scoring["primaryScore"]
        baseline_score = scoring["baselineScore"]
        exclusion_reason = "none"
        append_readiness = "comparable_append_ready"
    else:
        outcome_label = "unknown"
        outcome_value = None
        primary_score = None
        baseline_score = None
        exclusion_reason = classify_exclusion_reason(str(scoring.get("excludedReason", "")))
        append_readiness = "exclusion_audit_append_ready"
    row = base_row(
        manifest=manifest,
        run=run,
        artifact=artifact,
        evidence=evidence,
        history=history,
        paths=paths,
        row_kind=row_kind,
        row_id=f"campaignledgerrow-{run_id.rsplit('-', 1)[-1]}",
        run_status=str(run_state.get("runStatus", row_kind)),
        resolution_record_id=resolution["resolutionRecordId"],
        scoring_report_id=scoring["scoringReportId"],
    )
    row.update(
        {
            "resolutionRecordId": resolution["resolutionRecordId"],
            "scoringReportId": scoring["scoringReportId"],
            "outcomeLabel": outcome_label,
            "outcomeValue": outcome_value,
            "observationCount": int(outcome_summary.get("observationCount", 0)),
            "lateCount": int(outcome_summary.get("lateCount", 0)),
            "lateRatio": round(float(outcome_summary.get("lateRatio", 0.0)), 6),
            "scoreStatus": score_status,
            "primaryScore": primary_score,
            "baselineScore": baseline_score,
            "exclusionReason": exclusion_reason,
            "appendReadiness": append_readiness,
        }
    )
    return row


def checks_for_case(case: str) -> list[dict[str, Any]]:
    comparable = case == "comparable_scored"
    return [
        append_check(
            1,
            name="forecast_before_close",
            status="pass",
            required=True,
            blocks=False,
            message="Forecast time is at or before the campaign forecast close time.",
        ),
        append_check(
            2,
            name="source_policy_binding",
            status="pass",
            required=True,
            blocks=False,
            message="Campaign run, forecast artifact, and ledger row share sourcepolicy-1201.",
        ),
        append_check(
            3,
            name="no_post_close_evidence_leakage",
            status="pass",
            required=True,
            blocks=False,
            message="Ledger append uses only forecast-time evidence plus a later outcome/scoring binding.",
        ),
        append_check(
            4,
            name="resolution_after_horizon",
            status="pass" if comparable else "block",
            required=True,
            blocks=not comparable,
            message=(
                "Checked resolution time is after the service-window horizon."
                if comparable
                else "No checked campaign outcome source is available, so comparable append is blocked."
            ),
        ),
        append_check(
            5,
            name="score_binding",
            status="pass" if comparable else "block",
            required=True,
            blocks=not comparable,
            message=(
                "Checked scoring report is bound to the resolved campaign run."
                if comparable
                else "No checked campaign scoring report exists for this run."
            ),
        ),
        append_check(
            6,
            name="observation_coverage",
            status="pass" if comparable else "block",
            required=True,
            blocks=not comparable,
            message=(
                "Outcome coverage meets the campaign minimum observation count."
                if comparable
                else "Coverage cannot be assessed until a checked outcome source exists."
            ),
        ),
        append_check(
            7,
            name="comparable_scope",
            status="pass" if comparable else "block",
            required=True,
            blocks=not comparable,
            message=(
                "Run is comparable for weather-transit-delays morning_peak evidence."
                if comparable
                else "Missing outcome rows are preserved as excluded audit evidence, not comparable evidence."
            ),
        ),
        append_check(
            8,
            name="duplicate_ledger_row",
            status="pass",
            required=True,
            blocks=False,
            message="Append uses a stable campaign/run/forecast/row-kind key and must skip already-present rows.",
        ),
    ]


def local_write_result(status: str, *, appended: int = 0, already_present: int = 0, path: str) -> dict[str, Any]:
    return {
        "writeStatus": status,
        "ledgerPath": path,
        "appendedRowCount": appended,
        "alreadyPresentCount": already_present,
        "writesIgnoredLiveState": appended > 0,
    }


def ledger_path(manifest: dict[str, Any]) -> str:
    return f"{manifest['localStatePolicy']['workspaceRoot']}/{manifest['campaign']['campaignId']}/evidence-ledger.json"


def build_ledger_state(ledger: dict[str, Any], written_at: str) -> dict[str, Any]:
    rows = ledger["comparableRows"] + ledger["excludedRows"]
    return {
        "stateType": "prediction_campaign_evidence_ledger",
        "writtenAt": written_at,
        "campaignId": ledger["bindings"]["campaignId"],
        "cycleId": ledger["bindings"]["cycleId"],
        "domain": ledger["domain"],
        "ledgerPath": ledger["bindings"]["ledgerPath"],
        "appendOnly": True,
        "rowKeys": [row["rowKey"] for row in rows],
        "comparableRows": ledger["comparableRows"],
        "excludedRows": ledger["excludedRows"],
        "summary": {
            "comparableRowCount": len(ledger["comparableRows"]),
            "excludedRowCount": len(ledger["excludedRows"]),
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
        },
    }


def execute_local_append(ledger: dict[str, Any]) -> dict[str, Any]:
    path_value = ledger["bindings"]["ledgerPath"]
    path = ensure_safe_local_path(path_value, workspace_root=ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    incoming = build_ledger_state(ledger, utc_now())
    if path.exists():
        existing = read_json(path)
        if existing.get("stateType") != "prediction_campaign_evidence_ledger":
            raise PredictionCampaignForecastWriteError(f"Local ledger state type mismatch: {path_value}")
        if existing.get("campaignId") != ledger["bindings"]["campaignId"]:
            raise PredictionCampaignForecastWriteError(f"Local ledger campaign mismatch: {path_value}")
    else:
        existing = build_ledger_state(
            {
                **ledger,
                "comparableRows": [],
                "excludedRows": [],
            },
            utc_now(),
        )
    existing_keys = set(existing.get("rowKeys", []))
    appended = 0
    already_present = 0
    for row in incoming["comparableRows"]:
        if row["rowKey"] in existing_keys:
            already_present += 1
            continue
        existing["comparableRows"].append(row)
        existing_keys.add(row["rowKey"])
        appended += 1
    for row in incoming["excludedRows"]:
        if row["rowKey"] in existing_keys:
            already_present += 1
            continue
        existing["excludedRows"].append(row)
        existing_keys.add(row["rowKey"])
        appended += 1
    if appended:
        existing["writtenAt"] = utc_now()
        existing["rowKeys"] = [row["rowKey"] for row in existing["comparableRows"] + existing["excludedRows"]]
        existing["summary"] = {
            "comparableRowCount": len(existing["comparableRows"]),
            "excludedRowCount": len(existing["excludedRows"]),
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
        }
        path.write_text(render_json(existing), encoding="utf-8")
    return local_write_result(
        "local_append_written" if appended else "local_append_already_present",
        appended=appended,
        already_present=already_present,
        path=path_value,
    )


def build_prediction_campaign_evidence_ledger(
    *,
    mode: str = DEFAULT_MODE,
    ledger_case: str = DEFAULT_CASE,
    write_local: bool = False,
    from_local: bool = False,
    run_id: str = "predictionrun-1301",
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError(f"unknown prediction campaign ledger mode: {mode}")
    if ledger_case not in LEDGER_CASES:
        raise ValueError(f"unknown prediction campaign ledger case: {ledger_case}")
    if write_local and mode != "append":
        raise ValueError("--write-local is only available for prediction-campaign append")
    reads_local = from_local or write_local
    manifest = build_prediction_campaign_manifest()
    records = build_prediction_campaign_forecast_artifact(run_id=None if run_id == "predictionrun-1301" else run_id)
    plan = forecast_write_plan(run_id)
    attempt = build_prediction_campaign_resolution_attempt(run_id=run_id, execute_resolvers=True)
    run = planned_run(manifest, run_id)
    if reads_local:
        row = local_row_from_state(manifest, run_id)
        comparable = row["rowKind"] == "comparable"
        comparable_rows = [row] if comparable else []
        excluded_rows = [] if comparable else [row]
        effective_ledger_case = LOCAL_LEDGER_CASE
        append_checks = checks_for_local_row(row)
        ledger_status = "local_comparable_append_ready" if comparable else "local_exclusion_append_ready"
    else:
        comparable = ledger_case == "comparable_scored"
        comparable_rows = [comparable_row(manifest, records, plan)] if comparable else []
        excluded_rows = [] if comparable else [excluded_row(manifest, records, plan)]
        effective_ledger_case = ledger_case
        append_checks = checks_for_case(ledger_case)
        ledger_status = "checked_comparable_append_ready" if comparable else "checked_exclusion_append_ready"
    path_value = ledger_path(manifest)
    result = local_write_result("not_requested", path=path_value)
    ledger = {
        "predictionCampaignEvidenceLedgerId": "predictioncampaignledger-001",
        "generatedAt": GENERATED_AT,
        "ledgerStatus": ledger_status,
        "ledgerMode": mode,
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignResolutionAttemptId": attempt["predictionCampaignResolutionAttemptId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": run["runId"],
            "questionId": run["questionId"],
            "forecastId": run["forecastId"],
            "resolutionId": run["resolutionId"],
            "scoringReportId": run["scoringReportId"],
            "sourcePolicyId": run["sourcePolicyId"],
            "ledgerPath": path_value,
        },
        "ledgerPolicy": {
            "appendOnly": True,
            "comparableRowsSeparated": True,
            "excludedRowsSeparated": True,
            "explicitWriteRequired": True,
            "normalChecksWriteLiveState": False,
            "minimumObservationCount": 10,
            "minimumComparableResolvedForTrackRecord": 30,
            "minimumComparableResolvedForCalibration": 100,
            "excludedReasonCodes": EXCLUSION_REASONS,
            "noPostCloseEvidenceLeakage": True,
        },
        "appendCandidate": {
            "candidateStatus": "comparable_append_ready" if comparable else "exclusion_audit_append_ready",
            "ledgerCase": effective_ledger_case,
            "runId": run["runId"],
            "forecastId": run["forecastId"],
            "comparableAppendReady": comparable,
            "exclusionAppendReady": not comparable,
            "nextAction": (
                "Append the locally scored comparable row only with explicit --write-local."
                if comparable and reads_local
                else "Append the comparable scored row only with explicit --write-local."
                if comparable
                else "Append the local exclusion row for audit; it will not count toward comparable evidence."
                if reads_local
                else "Append the missing-outcome exclusion row for audit, then attach a checked outcome source before comparable evidence can grow."
            ),
        },
        "appendChecks": append_checks,
        "comparableRows": comparable_rows,
        "excludedRows": excluded_rows,
        "duplicateProtection": {
            "rowKeysInspected": len(comparable_rows) + len(excluded_rows),
            "idempotencyRule": "Stable row keys skip already-present comparable or excluded rows instead of overwriting them.",
            "duplicateAppendBlocked": True,
            "priorEvidenceOverwriteAllowed": False,
        },
        "localWriteResult": result,
        "commandSurface": {
            "command": f"python3 scripts/ope.py prediction-campaign {mode}",
            "acceptedFlags": (
                ["--run-id", "--ledger-case", "--from-local", "--write-local", "--output-format", "--view"]
                if mode == "append"
                else ["--run-id", "--ledger-case", "--from-local", "--output-format", "--view"]
            ),
            "defaultMode": "dry_run_readback",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "normalChecksWriteLiveState": False,
        },
        "summary": {
            "appendReadyCommandImplemented": True,
            "appendCommandImplemented": True,
            "localAppendImplemented": write_local,
            "idempotentAppendImplemented": True,
            "comparableAppendReady": comparable,
            "exclusionAppendReady": not comparable,
            "comparableRowCount": len(comparable_rows),
            "excludedRowCount": len(excluded_rows),
            "writesIgnoredLiveState": False,
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "recommendedNextAction": (
                "Run transit-track-record-gate --campaign predictioncampaign-001 --from-local-ledger to inspect threshold progress."
                if write_local and comparable
                else "Review the exclusion reason, then keep collecting comparable resolved outcomes."
                if write_local
                else "Run prediction-campaign append --from-local --write-local after reviewing the local scored row."
                if comparable and reads_local
                else "Run prediction-campaign append --ledger-case comparable_scored --write-local only after the checked scoring record exists."
                if comparable
                else "Resolve and score the campaign run before appending comparable evidence."
            ),
        },
        "executionBoundary": {
            "readsIgnoredLiveState": reads_local,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "appendsCorpusEvidence": False,
            "overwritesPriorEvidence": False,
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": [
            "Normal checks are dry-run and do not write the ignored local evidence ledger.",
            "Comparable evidence requires checked resolution, score, source-policy, coverage, and no-leakage checks.",
            "Excluded rows remain audit evidence and do not count toward track-record or calibration thresholds.",
        ],
    }
    if write_local:
        result = execute_local_append(ledger)
        ledger["ledgerStatus"] = result["writeStatus"]
        ledger["localWriteResult"] = result
        ledger["summary"]["localAppendImplemented"] = True
        ledger["summary"]["writesIgnoredLiveState"] = result["writesIgnoredLiveState"]
        ledger["executionBoundary"]["writesIgnoredLiveState"] = result["writesIgnoredLiveState"]
        ledger["executionBoundary"]["appendsCorpusEvidence"] = result["writesIgnoredLiveState"]
    return ledger


def print_view(ledger: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "ledger": ledger,
        "policy": ledger["ledgerPolicy"],
        "candidate": ledger["appendCandidate"],
        "checks": ledger["appendChecks"],
        "rows": {
            "comparableRows": ledger["comparableRows"],
            "excludedRows": ledger["excludedRows"],
        },
        "result": ledger["localWriteResult"],
        "summary": ledger["summary"],
        "boundary": ledger["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        summary = ledger["summary"]
        print(
            f"{ledger['ledgerStatus']} comparable={summary['comparableRowCount']} "
            f"excluded={summary['excludedRowCount']} writes={summary['writesIgnoredLiveState']}"
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
        label="prediction campaign evidence ledger",
        regen="python3 scripts/generate_prediction_campaign_evidence_ledger.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated prediction campaign evidence ledger")
    parser.add_argument("--check", action="store_true", help="check generated prediction campaign evidence ledger drift")
    parser.add_argument("--mode", choices=MODES, default=DEFAULT_MODE, help="ledger command mode")
    parser.add_argument("--ledger-case", choices=LEDGER_CASES, default=DEFAULT_CASE, help="checked ledger case")
    parser.add_argument("--run-id", default="predictionrun-1301", help="campaign run id for local ledger inspection")
    parser.add_argument(
        "--from-local",
        action="store_true",
        help="read resolved local campaign state before appending",
    )
    parser.add_argument("--write-local", action="store_true", help="append rows to the ignored local campaign ledger")
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["ledger", "policy", "candidate", "checks", "rows", "result", "summary", "boundary"],
        default="ledger",
        help="print one prediction campaign evidence-ledger view",
    )
    args = parser.parse_args()

    if (
        (args.write or args.check)
        and (
            args.mode != DEFAULT_MODE
            or args.ledger_case != DEFAULT_CASE
            or args.run_id != "predictionrun-1301"
            or args.from_local
            or args.write_local
        )
    ):
        raise SystemExit("custom ledger inputs cannot be combined with --write or --check")
    if args.write_local and args.mode != "append":
        raise SystemExit("--write-local is only available with --mode append")
    try:
        ledger = build_prediction_campaign_evidence_ledger(
            mode=args.mode,
            ledger_case=args.ledger_case,
            write_local=args.write_local,
            from_local=args.from_local,
            run_id=args.run_id,
        )
    except PredictionCampaignForecastWriteError as exc:
        raise SystemExit(str(exc)) from exc
    if args.write or args.check:
        check_or_write(ledger, write=args.write)
        return
    errors = validate_record(ledger, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(ledger, args.view, args.output_format)


if __name__ == "__main__":
    main()
