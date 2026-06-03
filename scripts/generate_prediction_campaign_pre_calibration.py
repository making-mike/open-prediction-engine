#!/usr/bin/env python3
"""Generate, check, or execute optional campaign pre-calibration from historical data."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_transit_method_options import BASELINE_METHOD_ID
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record
from prediction_campaign_forecast_write_runtime import ensure_safe_local_path, read_json
from run_transit_delay_forecast import (
    DEFAULT_HISTORY,
    EVENT_THRESHOLD,
    GEOGRAPHY,
    NETWORK,
    SERVICE_WINDOW,
    baseline_from_history,
    historical_outcome,
    load_rows,
    local_uri,
    matches_scope,
    sha256,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-pre-calibration"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-pre-calibration.generated.json"
SCHEMA = SPEC / "prediction-campaign-pre-calibration.schema.json"
GENERATED_AT = "2026-06-01T00:30:00Z"
MINIMUM_HISTORICAL_ROWS = 30


class PredictionCampaignPreCalibrationError(Exception):
    pass


def resolve_source_path(path_value: str | None) -> Path:
    if path_value is None:
        return DEFAULT_HISTORY
    path = Path(path_value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def round_float(value: float) -> float:
    return round(value, 10)


def content_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(render_json(data).encode("utf-8")).hexdigest()


def write_result_empty() -> dict[str, Any]:
    return {
        "writeStatus": "not_run",
        "artifactWrites": [],
        "stateWrites": [],
        "newFileWriteCount": 0,
        "alreadyPresentCount": 0,
        "sanitizedDiagnostics": "Dry-run readback only; add --write-local to write ignored local pre-calibration state.",
    }


def preflight_check(
    index: int,
    *,
    status: str,
    required: bool,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"precalibrationcheck-{index:03d}",
        "checkStatus": status,
        "requiredBeforeWrite": required,
        "blocksWrite": blocks,
        "message": message,
    }


def scoped_history(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if matches_scope(row, NETWORK, GEOGRAPHY, SERVICE_WINDOW)
    ]


def service_dates(rows: list[dict[str, Any]]) -> list[str]:
    return sorted(
        str(row["service_date"]).strip()
        for row in rows
        if str(row.get("service_date", "")).strip()
    )


def status_for(*, resolved_count: int, minimum_rows: int, last_date: str, first_pilot_date: str) -> str:
    if resolved_count == 0:
        return "blocked_unresolved_historical_outcomes"
    if resolved_count < minimum_rows:
        return "blocked_insufficient_historical_rows"
    if last_date != "none" and last_date >= first_pilot_date:
        return "blocked_future_or_pilot_window_rows"
    return "ready"


def build_preflight_checks(status: str, *, resolved_count: int, last_date: str, first_pilot_date: str) -> list[dict[str, Any]]:
    enough_rows = resolved_count >= MINIMUM_HISTORICAL_ROWS
    no_leakage = last_date == "none" or last_date < first_pilot_date
    return [
        preflight_check(
            1,
            status="pass" if resolved_count > 0 else "block",
            required=True,
            blocks=resolved_count == 0,
            message="Historical source must contain resolvable binary delay outcomes for the campaign scope.",
        ),
        preflight_check(
            2,
            status="pass" if enough_rows else "block",
            required=True,
            blocks=not enough_rows,
            message=f"At least {MINIMUM_HISTORICAL_ROWS} scoped historical rows are required before pre-calibration.",
        ),
        preflight_check(
            3,
            status="pass" if no_leakage else "block",
            required=True,
            blocks=not no_leakage,
            message="Historical pre-calibration rows must end before the first pilot service date.",
        ),
        preflight_check(
            4,
            status="pass" if status == "ready" else "block",
            required=True,
            blocks=status != "ready",
            message="Pre-calibration may bind only the historical-frequency baseline method before pilot launch.",
        ),
    ]


def build_prediction_campaign_pre_calibration(
    *,
    history_source: str | None = None,
    write_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    first_run = manifest["plannedRuns"][0]
    campaign_id = manifest["campaign"]["campaignId"]
    root = f".ope/live/prediction-campaigns/{campaign_id}"
    history_path = resolve_source_path(history_source)
    rows = load_rows(history_path)
    scoped_rows = scoped_history(rows)
    outcomes = [historical_outcome(row, EVENT_THRESHOLD) for row in scoped_rows]
    outcomes = [outcome for outcome in outcomes if outcome is not None]
    dates = service_dates(scoped_rows)
    first_date = dates[0] if dates else "none"
    last_date = dates[-1] if dates else "none"
    positive_count = sum(1 for outcome in outcomes if outcome)
    negative_count = len(outcomes) - positive_count
    if outcomes:
        baseline = baseline_from_history(scoped_rows, NETWORK, GEOGRAPHY, SERVICE_WINDOW, EVENT_THRESHOLD)
        probability = float(baseline["probability"])
        raw_event_rate = positive_count / len(outcomes)
    else:
        probability = 0.5
        raw_event_rate = 0.0
    ready_status = status_for(
        resolved_count=len(outcomes),
        minimum_rows=MINIMUM_HISTORICAL_ROWS,
        last_date=last_date,
        first_pilot_date=first_run["serviceDate"],
    )
    result = write_result or write_result_empty()
    status = result["writeStatus"] if result["writeStatus"] != "not_run" else ready_status
    source_path = rel(history_path)
    target_path = f"{root}/pre-calibration/predictioncampaignprecalibration-001.json"
    method_binding_path = f"{root}/method-binding.json"
    return {
        "predictionCampaignPreCalibrationId": "predictioncampaignprecalibration-001",
        "generatedAt": GENERATED_AT,
        "preCalibrationStatus": status,
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "campaignId": campaign_id,
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
            "methodId": BASELINE_METHOD_ID,
            "firstPilotRunId": first_run["runId"],
            "firstPilotServiceDate": first_run["serviceDate"],
        },
        "historySource": {
            "sourceId": "source-prec-001",
            "sourceType": "public_dataset",
            "sourcePath": source_path,
            "uri": local_uri(history_path),
            "contentHash": sha256(history_path),
            "rowCount": len(rows),
            "scopedRowCount": len(scoped_rows),
            "resolvedOutcomeRowCount": len(outcomes),
            "minimumHistoricalRows": MINIMUM_HISTORICAL_ROWS,
            "firstHistoricalServiceDate": first_date,
            "lastHistoricalServiceDate": last_date,
            "leakageCheckStatus": "pass" if last_date == "none" or last_date < first_run["serviceDate"] else "block",
            "sourceCommand": (
                "python3 scripts/ope.py prediction-campaign pre-calibration"
                if history_source is None
                else f"python3 scripts/ope.py prediction-campaign pre-calibration --history-source {history_source}"
            ),
        },
        "calibrationMethod": {
            "methodName": "historical_frequency_laplace_pre_calibration",
            "outputType": "binary",
            "eventThreshold": EVENT_THRESHOLD,
            "positiveOutcomeCount": positive_count,
            "negativeOutcomeCount": negative_count,
            "rawEventRate": round_float(raw_event_rate),
            "priorPositiveCount": 1.0,
            "priorNegativeCount": 1.0,
            "smoothing": "laplace_add_one",
            "calibratedProbability": probability,
            "calibrationChangesMethodClass": False,
            "automaticProbabilityUpdateAllowed": False,
        },
        "engineBinding": {
            "activeMethodId": BASELINE_METHOD_ID,
            "calibratedProbability": probability,
            "preCalibrationArtifactPath": target_path,
            "methodBindingPath": method_binding_path,
            "effectiveScope": "future_campaign_forecasts_only",
            "forecastArtifactCanUseBeforePilot": ready_status == "ready",
            "normalChecksReadLocalBinding": False,
            "prospectiveOnly": True,
            "priorForecastHistoryRewriteAllowed": False,
            "changesForecastMethod": False,
        },
        "preflightChecks": build_preflight_checks(
            ready_status,
            resolved_count=len(outcomes),
            last_date=last_date,
            first_pilot_date=first_run["serviceDate"],
        ),
        "writePlan": {
            "requiresWriteLocal": True,
            "writeLocalRequested": result["writeStatus"] != "not_run",
            "preCalibrationArtifactPath": target_path,
            "methodBindingPath": method_binding_path,
            "idempotent": True,
            "normalChecksWriteLocal": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
        },
        "writeResult": result,
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign pre-calibration",
            "acceptedFlags": [
                "--history-source",
                "--write-local",
                "--output-format",
                "--view",
            ],
            "defaultMode": "historical_pre_calibration_readback",
            "capturedStdoutMode": "json",
            "explicitWriteFlagRequired": True,
            "normalChecksMutateState": False,
        },
        "summary": {
            "preCalibrationImplemented": True,
            "historicalOnly": True,
            "localWriteEligible": ready_status == "ready",
            "calibratedProbability": probability,
            "writesMethodBinding": result["writeStatus"] != "not_run",
            "changesForecastMethod": False,
            "qualityClaimAllowed": False,
            "recommendedNextAction": (
                "Run the pilot launch with --pre-calibrate and --write-local after reviewing the historical-only binding."
                if ready_status == "ready" and result["writeStatus"] == "not_run"
                else "Use prediction-campaign start --pre-calibrate --write-local so the ready run uses this calibrated baseline."
                if result["writeStatus"] != "not_run"
                else "Fix the historical source before requesting pre-calibration."
            ),
        },
        "executionBoundary": {
            "readsHistoricalSource": True,
            "readsIgnoredLiveState": False,
            "writesIgnoredLiveState": result["writeStatus"] != "not_run",
            "writesCampaignState": result["writeStatus"] != "not_run",
            "fetchesLiveData": False,
            "createsForecastArtifacts": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "updatesPriorForecastProbabilities": False,
            "changesForecastMethod": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "Pre-calibration is optional and historical-only; it does not fetch live sources.",
            "The binding stays on the baseline method and changes only the prospective baseline probability.",
            "Pre-calibration does not create quality, track-record, or live calibration claims.",
        ],
    }


def artifact_record(record: dict[str, Any]) -> dict[str, Any]:
    artifact = dict(record)
    artifact["preCalibrationStatus"] = "ready"
    artifact["writeResult"] = write_result_empty()
    artifact["writePlan"] = dict(record["writePlan"])
    artifact["writePlan"]["writeLocalRequested"] = False
    artifact["executionBoundary"] = dict(record["executionBoundary"])
    artifact["executionBoundary"]["writesIgnoredLiveState"] = False
    artifact["executionBoundary"]["writesCampaignState"] = False
    artifact["summary"] = dict(record["summary"])
    artifact["summary"]["writesMethodBinding"] = False
    return artifact


def method_binding_state(record: dict[str, Any], written_at: str) -> dict[str, Any]:
    binding = record["engineBinding"]
    source = record["historySource"]
    return {
        "stateType": "prediction_campaign_method_binding",
        "stateVersion": 1,
        "writtenAt": written_at,
        "campaignId": record["bindings"]["campaignId"],
        "cycleId": record["bindings"]["cycleId"],
        "activeMethodId": binding["activeMethodId"],
        "calibratedProbability": binding["calibratedProbability"],
        "sourcePreCalibrationArtifactPath": binding["preCalibrationArtifactPath"],
        "sourceHistoryPath": source["sourcePath"],
        "sourceHistoryContentHash": source["contentHash"],
        "effectiveScope": binding["effectiveScope"],
        "prospectiveOnly": True,
        "priorForecastHistoryRewriteAllowed": False,
        "priorForecastProbabilityRewriteAllowed": False,
        "writesMethodRegistry": False,
    }


def write_json_if_safe(path_value: str, data: dict[str, Any], *, record_type: str) -> dict[str, Any]:
    path = ensure_safe_local_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_json(data)
    new_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if path.exists():
        existing_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_hash != new_hash:
            raise PredictionCampaignPreCalibrationError(f"Refusing to overwrite different pre-calibration state: {path_value}")
        status = "already_present"
    else:
        path.write_text(rendered, encoding="utf-8")
        status = "written"
    return {
        "recordType": record_type,
        "targetPath": path_value,
        "writeStatus": status,
        "contentHash": new_hash,
    }


def write_method_binding_if_safe(record: dict[str, Any], written_at: str) -> dict[str, Any]:
    path_value = record["engineBinding"]["methodBindingPath"]
    path = ensure_safe_local_path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    binding = method_binding_state(record, written_at)
    rendered = render_json(binding)
    new_hash = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    if path.exists():
        existing = read_json(path)
        if existing.get("activeMethodId") != record["engineBinding"]["activeMethodId"]:
            raise PredictionCampaignPreCalibrationError(
                f"Refusing to replace non-baseline method binding during pre-calibration: {path_value}"
            )
        existing_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_hash != new_hash:
            raise PredictionCampaignPreCalibrationError(
                f"Refusing to overwrite different baseline method binding: {path_value}"
            )
        status = "already_present"
    else:
        path.write_text(rendered, encoding="utf-8")
        status = "written"
    return {
        "recordType": "prediction_campaign_method_binding",
        "targetPath": path_value,
        "writeStatus": status,
        "contentHash": new_hash,
    }


def execute_local_pre_calibration(record: dict[str, Any]) -> dict[str, Any]:
    blocking = [check for check in record["preflightChecks"] if check["blocksWrite"]]
    if blocking:
        ids = ", ".join(check["checkId"] for check in blocking)
        raise PredictionCampaignPreCalibrationError(f"Pre-calibration blocked by preflight checks: {ids}")

    written_at = GENERATED_AT
    artifact_write = write_json_if_safe(
        record["engineBinding"]["preCalibrationArtifactPath"],
        artifact_record(record),
        record_type="prediction_campaign_pre_calibration",
    )
    binding_write = write_method_binding_if_safe(record, written_at)
    rows = [artifact_write, binding_write]
    new_count = len([row for row in rows if row["writeStatus"] in {"written", "updated"}])
    already_count = len([row for row in rows if row["writeStatus"] == "already_present"])
    return {
        "writeStatus": "local_pre_calibration_completed" if new_count else "local_pre_calibration_already_present",
        "artifactWrites": [artifact_write],
        "stateWrites": [binding_write],
        "newFileWriteCount": new_count,
        "alreadyPresentCount": already_count,
        "sanitizedDiagnostics": "Pre-calibration wrote only ignored local campaign state from a historical source.",
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "pre-calibration": record,
        "source": record["historySource"],
        "method": record["calibrationMethod"],
        "binding": record["engineBinding"],
        "checks": record["preflightChecks"],
        "write": record["writePlan"],
        "result": record["writeResult"],
        "summary": record["summary"],
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        print(
            f"{record['preCalibrationStatus']} probability={record['calibrationMethod']['calibratedProbability']} "
            f"rows={record['historySource']['resolvedOutcomeRowCount']}"
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
        label="prediction campaign pre-calibration",
        regen="python3 scripts/generate_prediction_campaign_pre_calibration.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated pre-calibration readback")
    parser.add_argument("--check", action="store_true", help="check generated pre-calibration drift")
    parser.add_argument("--write-local", action="store_true", help="write ignored local pre-calibration state")
    parser.add_argument("--history-source", help="approved historical delay CSV/JSON source")
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["pre-calibration", "source", "method", "binding", "checks", "write", "result", "summary", "boundary"],
        default="pre-calibration",
        help="print one pre-calibration view",
    )
    args = parser.parse_args()
    if (args.write or args.check) and (args.write_local or args.history_source):
        raise SystemExit("custom pre-calibration inputs cannot be combined with --write or --check")
    try:
        record = build_prediction_campaign_pre_calibration(history_source=args.history_source)
        if args.write or args.check:
            check_or_write(record, write=args.write)
            return
        if args.write_local:
            result = execute_local_pre_calibration(record)
            record = build_prediction_campaign_pre_calibration(
                history_source=args.history_source,
                write_result=result,
            )
    except PredictionCampaignPreCalibrationError as exc:
        raise SystemExit(str(exc)) from exc
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
