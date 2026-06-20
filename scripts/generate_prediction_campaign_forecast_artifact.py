#!/usr/bin/env python3
"""Generate or check the checked prediction campaign forecast artifact."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

from generate_prediction_campaign_pre_calibration import artifact_record
from generate_prediction_campaign_forecast_creation import build_prediction_campaign_forecast_creation
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-forecast-artifact"
MANIFEST_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "prediction-campaign-manifest"
    / "weather-transit-delay-campaign-manifest.generated.json"
)
CREATION_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "prediction-campaign-forecast-creation"
    / "weather-transit-delay-campaign-forecast-creation.generated.json"
)
HISTORY_SOURCE_PATH = ROOT / "spec" / "fixtures" / "local-source-files" / "transit-delay-history.csv"
OUTPUT_NAMES = {
    "question": "weather-transit-delay-campaign-forecast-question.generated.json",
    "evidence": "weather-transit-delay-campaign-forecast-evidence.generated.json",
    "artifact": "weather-transit-delay-campaign-forecast-artifact.generated.json",
    "history": "weather-transit-delay-campaign-forecast-history.generated.json",
}
SCHEMAS = {
    "question": SPEC / "forecast-question.schema.json",
    "evidence": SPEC / "evidence-packet.schema.json",
    "artifact": SPEC / "forecast-artifact.schema.json",
    "history": SPEC / "forecast-history.schema.json",
}
GENERATED_AT = "2026-05-29T00:45:00Z"
NETWORK = "hsl-surface"
GEOGRAPHY = "helsinki"
EVENT_THRESHOLD = 0.2
LATE_SECONDS = 300
MIN_OBSERVATIONS = 10
BASELINE_PROBABILITY = 0.25


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_uri(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT)
    except ValueError:
        rel = path.resolve()
    normalized = str(rel).replace("\\", "/")
    return f"local://{normalized}"


def source_ref(
    source_id: str,
    name: str,
    source_type: str,
    path: Path | None = None,
    retrieved_at: str | None = None,
    uri: str | None = None,
    content_hash: str | None = None,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "sourceId": source_id,
        "name": name,
        "sourceType": source_type,
    }
    if path is not None:
        ref["uri"] = local_uri(path)
        ref["contentHash"] = sha256(path)
    if uri is not None:
        ref["uri"] = uri
    if content_hash is not None:
        ref["contentHash"] = content_hash
    if retrieved_at is not None:
        ref["retrievedAt"] = retrieved_at
    return ref


def record_suffix(run: dict[str, Any]) -> str:
    return run["forecastId"].split("-")[-1]


def run_record_id(prefix: str, run: dict[str, Any]) -> str:
    return f"{prefix}-{record_suffix(run)}"


def run_source_id(run: dict[str, Any], index: int) -> str:
    suffix = record_suffix(run)
    if suffix == "1301":
        return f"source-{1300 + index}"
    return f"source-{suffix}{index:02d}"


def horizon(run: dict[str, Any]) -> dict[str, Any]:
    label = f"same-day-{run['serviceWindow'].replace('_', '-')}"
    return {
        "startsAt": run["horizonStartsAt"],
        "endsAt": run["horizonEndsAt"],
        "label": label,
    }


def resolution_criteria(run: dict[str, Any]) -> str:
    threshold_percent = int(EVENT_THRESHOLD * 100)
    return (
        f"Resolve Yes if collected GTFS-RT TripUpdates or equivalent transit delay rows for {NETWORK} "
        f"in {GEOGRAPHY} during {run['serviceWindow']} on {run['serviceDate']} include at least "
        f"{MIN_OBSERVATIONS} eligible trip-stop observations and at least {threshold_percent}% have "
        f"delay_seconds >= {LATE_SECONDS}. Resolve No if coverage passes and the ratio is below threshold. "
        "Resolve Ambiguous if coverage fails."
    )


def build_prediction_campaign_forecast_artifact(
    run_id: str | None = None,
    *,
    creation: dict[str, Any] | None = None,
    pre_calibration: dict[str, Any] | None = None,
    forecasted_at: str | None = None,
) -> dict[str, dict[str, Any]]:
    if creation is None:
        creation = build_prediction_campaign_forecast_creation(run_id=run_id)
    run = creation["readyRun"]
    bindings = creation["bindings"]
    # Checked fixtures keep the scheduled create time; effectful writes pass the
    # actual runner clock so forecastedAt never backdates a live launch.
    forecasted_at_value = forecasted_at or run["forecastCreateAt"]
    horizon_record = horizon(run)
    criteria = resolution_criteria(run)
    creation_path = (
        CREATION_PATH
        if creation["predictionCampaignForecastCreationId"] == "predictioncampaignforecastcreation-001"
        else None
    )
    outcome_ref = source_ref(
        run_source_id(run, 4),
        "Future transit delay outcome capture",
        "public_dataset",
    )
    provenance_refs = [
        source_ref(
            run_source_id(run, 1),
            "Historical transit delay fixture",
            "public_dataset",
            HISTORY_SOURCE_PATH,
            forecasted_at_value,
        ),
        source_ref(
            run_source_id(run, 2),
            "Prediction campaign manifest fixture",
            "other",
            MANIFEST_PATH,
            GENERATED_AT,
        ),
        source_ref(
            run_source_id(run, 3),
            "Prediction campaign forecast-creation handoff",
            "other",
            creation_path,
            GENERATED_AT,
        ),
    ]
    forecast_probability_value = BASELINE_PROBABILITY
    model_version = "weather-transit-delay-campaign-baseline-v0"
    configuration_hash = "sha256-campaign-baseline-v0"
    pre_calibration_factor = None
    if pre_calibration is not None:
        forecast_probability_value = pre_calibration["calibrationMethod"]["calibratedProbability"]
        model_version = "weather-transit-delay-campaign-precalibrated-baseline-v0"
        configuration_hash = "sha256-campaign-precalibrated-baseline-v0"
        pre_calibration_factor = (
            f"pre-calibrated baseline probability {forecast_probability_value:g} from "
            f"{pre_calibration['historySource']['resolvedOutcomeRowCount']} historical rows"
        )
        provenance_refs.append(
            source_ref(
                run_source_id(run, 5),
                "Historical pre-calibration binding",
                "other",
                retrieved_at=pre_calibration["generatedAt"],
                uri=f"local://{pre_calibration['engineBinding']['preCalibrationArtifactPath']}",
                content_hash=hashlib.sha256(render_json(artifact_record(pre_calibration)).encode("utf-8")).hexdigest(),
            )
        )
    model = {
        "modelId": run_record_id("model", run),
        "version": model_version,
        "trainingCutoff": run["forecastCloseAt"],
        "configurationHash": configuration_hash,
    }
    forecast_output = {"outputType": "binary", "probability": forecast_probability_value}
    question = {
        "questionId": run["questionId"],
        "title": (
            f"Will {NETWORK} in {GEOGRAPHY} exceed the beta delay threshold during "
            f"{run['serviceWindow']} on {run['serviceDate']}?"
        ),
        "background": (
            "Created as a checked prediction campaign fixture from the ready runner decision. "
            "It uses the baseline-only campaign method because transit method options still block "
            "non-baseline selection below the comparable-outcome threshold."
        ),
        "domain": creation["domain"],
        "outputType": "binary",
        "status": "open",
        "openAt": run["forecastCreateAt"],
        "closeAt": run["forecastCloseAt"],
        "resolveAt": run["horizonEndsAt"],
        "horizon": horizon_record,
        "resolutionCriteria": criteria,
        "resolutionAuthority": "OPE local transit delay resolver",
        "resolutionMode": "automated_measurement",
        "primaryResolutionSource": outcome_ref,
        "fallbackResolutionSources": [],
        "validOutcomeSpace": {
            "description": "Binary outcome: Yes if the network late-observation ratio meets the declared threshold; No otherwise.",
            "labels": ["yes", "no"],
        },
        "clarificationHistory": [],
        "incentiveRiskReview": {
            "riskLevel": "minimal",
            "notes": "Local transit delay campaign fixture; no passenger-level, fare, enforcement, or public-safety use.",
        },
        "createdAt": forecasted_at_value,
        "updatedAt": forecasted_at_value,
    }
    evidence = {
        "evidencePacketId": run_record_id("evidence", run),
        "forecastId": run["forecastId"],
        "questionId": run["questionId"],
        "questionStatus": "open",
        "domain": creation["domain"],
        "horizon": horizon_record,
        "forecastedAt": forecasted_at_value,
        "model": model,
        "inputSourceClasses": ["public_dataset", "other"],
        "provenanceReferences": provenance_refs,
        "forecastOutput": forecast_output,
        "baselineForecast": forecast_output,
        "rationaleSummary": (
            "The checked campaign fixture creates an unresolved baseline-only forecast artifact from "
            "the ready runner decision. It binds the campaign manifest, forecast-creation handoff, "
            "source policy, and historical delay fixture without live fetches or resolver execution."
        ),
        "keyFactors": [
            f"campaign run {run['runId']}",
            f"runner decision {bindings['runnerDecisionId']}",
            f"source policy {bindings['sourcePolicyId']}",
            "baseline-only default selected below transit comparable-outcome threshold",
            pre_calibration_factor or "no optional pre-calibration binding requested",
            f"forecast closes at {run['forecastCloseAt']} before horizon start {run['horizonStartsAt']}",
            "normal checks do not write .ope/live campaign state",
            "resolution and scoring remain pending until post-window evidence is explicitly resolved",
        ],
        "resolutionCriteria": criteria,
        "resolutionSource": outcome_ref,
        "fallbackResolutionSources": [],
        "scheduledResolutionAt": run["horizonEndsAt"],
    }
    artifact = {
        "forecastId": run["forecastId"],
        "questionId": run["questionId"],
        "questionStatus": "open",
        "domain": creation["domain"],
        "horizon": horizon_record,
        "forecastedAt": forecasted_at_value,
        "closedAt": run["forecastCloseAt"],
        "outputType": "binary",
        "forecastOutput": forecast_output,
        "baselineForecast": forecast_output,
        "model": model,
        "evidencePacketId": evidence["evidencePacketId"],
        "resolutionPlan": {
            "resolutionCriteria": criteria,
            "resolutionAuthority": question["resolutionAuthority"],
            "primaryResolutionSource": outcome_ref,
            "fallbackResolutionSources": [],
            "scheduledResolutionAt": run["horizonEndsAt"],
        },
    }
    history = {
        "historyId": run_record_id("history", run),
        "questionId": run["questionId"],
        "entries": [
            {
                "forecastId": run["forecastId"],
                "forecastedAt": forecasted_at_value,
                "state": "active",
                "sourceClass": "baseline",
                "model": model,
                "forecastOutput": forecast_output,
                "rationaleSummary": evidence["rationaleSummary"],
                "evidencePacketId": evidence["evidencePacketId"],
            }
        ],
        "createdAt": forecasted_at_value,
        "updatedAt": forecasted_at_value,
    }
    return {
        "question": question,
        "evidence": evidence,
        "artifact": artifact,
        "history": history,
    }


def validate_records(records: dict[str, dict[str, Any]]) -> None:
    for key, record in records.items():
        errors = validate_record(record, SCHEMAS[key])
        if errors:
            for error in errors:
                print(f"{key}: {error}")
            raise SystemExit(1)


def check_or_write(records: dict[str, dict[str, Any]], *, write: bool) -> None:
    validate_records(records)
    if write:
        GENERATED.mkdir(parents=True, exist_ok=True)
        for key, record in records.items():
            (GENERATED / OUTPUT_NAMES[key]).write_text(render_json(record), encoding="utf-8")
        return

    for key, record in records.items():
        path = GENERATED / OUTPUT_NAMES[key]
        if not path.exists():
            raise SystemExit(f"Missing generated prediction campaign forecast artifact record: {path}")
        if path.read_text(encoding="utf-8") != render_json(record):
            raise SystemExit("prediction campaign forecast artifact fixture drifted; run with --write")
    print("checked prediction campaign forecast artifact")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated campaign forecast artifact records")
    parser.add_argument("--check", action="store_true", help="check generated campaign forecast artifact drift")
    parser.add_argument(
        "--view",
        choices=sorted(OUTPUT_NAMES),
        default="artifact",
        help="print one campaign forecast artifact record",
    )
    args = parser.parse_args()

    records = build_prediction_campaign_forecast_artifact()
    if args.write or args.check:
        check_or_write(records, write=args.write)
        return
    validate_records(records)
    print(render_json(records[args.view]), end="")


if __name__ == "__main__":
    main()
