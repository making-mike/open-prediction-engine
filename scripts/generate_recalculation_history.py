#!/usr/bin/env python3
"""Generate or check fixture-safe recalculation history records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "recalculation"
SOURCE_EVIDENCE = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "auto-evidence"
    / "weather-logistics-auto-evidence-evidence.generated.json"
)
SOURCE_ARTIFACT = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "auto-evidence"
    / "weather-logistics-auto-evidence-artifact.generated.json"
)
SOURCE_HISTORY = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "auto-evidence"
    / "weather-logistics-auto-evidence-history.generated.json"
)

ACCEPTED_TRIGGER_PATH = GENERATED / "weather-logistics-recalculation-trigger.generated.json"
REJECTED_TRIGGER_PATH = GENERATED / "weather-logistics-recalculation-rejected-trigger.generated.json"
ACCEPTED_RUN_PATH = GENERATED / "weather-logistics-recalculation-run.generated.json"
REJECTED_RUN_PATH = GENERATED / "weather-logistics-recalculation-rejected-run.generated.json"
EVIDENCE_PATH = GENERATED / "weather-logistics-recalculated-evidence.generated.json"
ARTIFACT_PATH = GENERATED / "weather-logistics-recalculated-artifact.generated.json"
HISTORY_PATH = GENERATED / "weather-logistics-recalculated-history.generated.json"
FEATURE_SNAPSHOT_PATH = GENERATED / "weather-logistics-recalculated-feature-snapshot.generated.json"

GENERATED_AT = "2026-06-02T18:21:00Z"
RECALCULATED_AT = "2026-06-02T18:20:00Z"
FORECAST_CLOSE = "2026-06-03T00:00:00Z"


class RecalculationError(Exception):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_ref(
    source_id: str,
    name: str,
    source_type: str,
    uri: str | None = None,
    retrieved_at: str | None = None,
    content_hash: str | None = None,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "sourceId": source_id,
        "name": name,
        "sourceType": source_type,
    }
    if uri is not None:
        ref["uri"] = uri
    if retrieved_at is not None:
        ref["retrievedAt"] = retrieved_at
    if content_hash is not None:
        ref["contentHash"] = content_hash
    return ref


def updated_weather_ref() -> dict[str, Any]:
    return source_ref(
        "source-801",
        "Updated Open-Meteo weather forecast for Warsaw",
        "public_dataset",
        "https://api.open-meteo.com/v1/forecast?latitude=52.2297&longitude=21.0122&daily=precipitation_sum&timezone=Europe%2FWarsaw&precipitation_unit=mm&start_date=2026-06-03&end_date=2026-06-03",
        "2026-06-02T18:00:00Z",
        "sha256-updated-weather-source-801",
    )


def resolution_outcome_ref() -> dict[str, Any]:
    return source_ref(
        "source-402",
        "Declared Warsaw operations event source",
        "internal_dataset",
        "https://example.test/fixtures/live/declared-warsaw-operations-outcome.json",
        "2026-06-04T10:00:00Z",
        "sha256-declared-outcome-source-402",
    )


def build_accepted_trigger() -> dict[str, Any]:
    return {
        "recalculationTriggerId": "recalculationtrigger-001",
        "createdAt": "2026-06-02T18:05:00Z",
        "domainSetupId": "domainsetup-001",
        "domain": "weather-logistics",
        "questionId": "question-601",
        "previousForecastId": "forecast-602",
        "previousEvidencePacketId": "evidence-601",
        "triggerType": "api_event",
        "triggerStatus": "accepted",
        "sourceRole": "forecast_input",
        "forecastCloseTime": FORECAST_CLOSE,
        "receivedAt": "2026-06-02T18:00:00Z",
        "availableBeforeForecastClose": True,
        "postOutcomeEvidence": False,
        "changedSourceRefs": [updated_weather_ref()],
        "triggerReason": "Updated forecast-time precipitation evidence arrived before the forecast close time.",
        "guardrailReasons": ["pre_close_forecast_input", "append_history_required"],
    }


def build_rejected_trigger() -> dict[str, Any]:
    return {
        "recalculationTriggerId": "recalculationtrigger-002",
        "createdAt": "2026-06-04T10:05:00Z",
        "domainSetupId": "domainsetup-001",
        "domain": "weather-logistics",
        "questionId": "question-601",
        "previousForecastId": "forecast-801",
        "previousEvidencePacketId": "evidence-801",
        "triggerType": "agent_submitted_evidence",
        "triggerStatus": "rejected",
        "sourceRole": "resolution_primary",
        "forecastCloseTime": FORECAST_CLOSE,
        "receivedAt": "2026-06-04T10:00:00Z",
        "availableBeforeForecastClose": False,
        "postOutcomeEvidence": True,
        "changedSourceRefs": [resolution_outcome_ref()],
        "triggerReason": "Post-outcome resolution evidence cannot alter forecast-time probabilities.",
        "guardrailReasons": [
            "post_outcome_evidence",
            "received_after_forecast_close",
            "resolution_source_not_forecast_input",
        ],
    }


def build_feature_snapshot(source_evidence: dict[str, Any]) -> dict[str, Any]:
    previous_probability = source_evidence["forecastOutput"]["probability"]
    return {
        "featureSnapshotId": "featuresnapshot-801",
        "questionId": "question-601",
        "generatedAt": RECALCULATED_AT,
        "domain": "weather-logistics",
        "horizon": source_evidence["horizon"],
        "sourceIds": ["source-801", "source-103"],
        "features": {
            "previousForecastProbability": previous_probability,
            "updatedForecastDailyPrecipitationMm": 34,
            "previousForecastDailyPrecipitationMm": 24,
            "precipitationThresholdMm": 20,
            "baselineDisruptionRate": source_evidence["baselineForecast"]["probability"],
            "comparableServiceDays": 64,
            "reasonForUpdate": "forecast_time_weather_update",
        },
    }


def build_recalculated_evidence(source_evidence: dict[str, Any]) -> dict[str, Any]:
    baseline_ref = source_evidence["provenanceReferences"][1]
    return {
        "evidencePacketId": "evidence-801",
        "forecastId": "forecast-801",
        "questionId": source_evidence["questionId"],
        "questionStatus": source_evidence["questionStatus"],
        "domain": source_evidence["domain"],
        "horizon": source_evidence["horizon"],
        "forecastedAt": RECALCULATED_AT,
        "model": {
            "modelId": "model-801",
            "version": "weather-logistics-auto-evidence-recalculation-fixture-v1",
            "configurationHash": "sha256-recalculation-model-001",
        },
        "inputSourceClasses": ["internal_dataset", "public_dataset"],
        "provenanceReferences": [updated_weather_ref(), baseline_ref],
        "featureSnapshotRef": "https://example.test/fixtures/generated/recalculation/weather-logistics-recalculated-feature-snapshot.generated.json",
        "forecastOutput": {
            "outputType": "binary",
            "probability": 0.57,
        },
        "baselineForecast": source_evidence["baselineForecast"],
        "calibrationBand": {
            "lower": 0.48,
            "upper": 0.66,
            "coverage": 0.8,
            "sampleSize": 64,
        },
        "rationaleSummary": "Recalculation appended a new forecast after updated pre-close precipitation evidence increased forecast severity.",
        "keyFactors": [
            "updated forecast precipitation 34.0 mm",
            "previous forecast precipitation 24.0 mm",
            "threshold 20 mm",
            "previous probability 0.41",
            "updated probability 0.57",
            "append-only history; no post-outcome evidence",
        ],
        "resolutionCriteria": source_evidence["resolutionCriteria"],
        "resolutionSource": source_evidence["resolutionSource"],
        "fallbackResolutionSources": source_evidence["fallbackResolutionSources"],
        "scheduledResolutionAt": source_evidence["scheduledResolutionAt"],
    }


def build_recalculated_artifact(source_artifact: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "forecastId": evidence["forecastId"],
        "questionId": source_artifact["questionId"],
        "questionStatus": source_artifact["questionStatus"],
        "domain": source_artifact["domain"],
        "horizon": source_artifact["horizon"],
        "forecastedAt": evidence["forecastedAt"],
        "closedAt": source_artifact["closedAt"],
        "outputType": source_artifact["outputType"],
        "forecastOutput": evidence["forecastOutput"],
        "baselineForecast": evidence["baselineForecast"],
        "model": evidence["model"],
        "evidencePacketId": evidence["evidencePacketId"],
        "resolutionPlan": source_artifact["resolutionPlan"],
    }


def build_recalculated_history(source_history: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for entry in source_history["entries"]:
        copied = dict(entry)
        if copied["forecastId"] == "forecast-602":
            copied["state"] = "superseded"
        entries.append(copied)
    entries.append(
        {
            "forecastId": evidence["forecastId"],
            "forecastedAt": evidence["forecastedAt"],
            "state": "active",
            "sourceClass": "model",
            "model": evidence["model"],
            "forecastOutput": evidence["forecastOutput"],
            "supersedesForecastId": "forecast-602",
            "rationaleSummary": evidence["rationaleSummary"],
            "evidencePacketId": evidence["evidencePacketId"],
        }
    )
    return {
        "historyId": "history-801",
        "questionId": source_history["questionId"],
        "entries": entries,
        "createdAt": source_history["createdAt"],
        "updatedAt": evidence["forecastedAt"],
    }


def forecast_pointer(forecast_id: str, evidence_packet_id: str, forecasted_at: str, model_version: str, probability: float) -> dict[str, Any]:
    return {
        "forecastId": forecast_id,
        "evidencePacketId": evidence_packet_id,
        "forecastedAt": forecasted_at,
        "modelVersion": model_version,
        "probability": probability,
    }


def build_accepted_run(trigger: dict[str, Any], source_evidence: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "recalculationRunId": "recalculationrun-001",
        "generatedAt": GENERATED_AT,
        "domainSetupId": trigger["domainSetupId"],
        "domain": trigger["domain"],
        "questionId": trigger["questionId"],
        "triggerId": trigger["recalculationTriggerId"],
        "runStatus": "updated",
        "previousForecast": forecast_pointer(
            "forecast-602",
            "evidence-601",
            source_evidence["forecastedAt"],
            source_evidence["model"]["version"],
            source_evidence["forecastOutput"]["probability"],
        ),
        "updatedForecast": forecast_pointer(
            evidence["forecastId"],
            evidence["evidencePacketId"],
            evidence["forecastedAt"],
            evidence["model"]["version"],
            evidence["forecastOutput"]["probability"],
        ),
        "changedEvidence": {
            "changedSourceRefs": trigger["changedSourceRefs"],
            "previousEvidencePacketId": "evidence-601",
            "updatedEvidencePacketId": evidence["evidencePacketId"],
            "reasonForUpdate": "Updated forecast-time weather evidence increased daily precipitation before forecast close.",
        },
        "historyAppend": {
            "historyId": "history-801",
            "appendOnly": True,
            "previousEntryState": "superseded",
            "updatedEntryState": "active",
            "supersedesForecastId": "forecast-602",
            "appendedForecastId": evidence["forecastId"],
        },
        "rejectionReasons": [],
        "warnings": [
            "Recalculation is fixture-safe and append-only.",
            "Updated probability remains provisional and unresolved.",
            "No post-outcome evidence was used in this recalculation.",
        ],
    }


def build_rejected_run(trigger: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "recalculationRunId": "recalculationrun-002",
        "generatedAt": "2026-06-04T10:06:00Z",
        "domainSetupId": trigger["domainSetupId"],
        "domain": trigger["domain"],
        "questionId": trigger["questionId"],
        "triggerId": trigger["recalculationTriggerId"],
        "runStatus": "rejected",
        "previousForecast": forecast_pointer(
            evidence["forecastId"],
            evidence["evidencePacketId"],
            evidence["forecastedAt"],
            evidence["model"]["version"],
            evidence["forecastOutput"]["probability"],
        ),
        "updatedForecast": None,
        "changedEvidence": {
            "changedSourceRefs": trigger["changedSourceRefs"],
            "previousEvidencePacketId": evidence["evidencePacketId"],
            "updatedEvidencePacketId": None,
            "reasonForUpdate": "Rejected because resolution evidence arrived after close and after the outcome window.",
        },
        "historyAppend": {
            "historyId": "history-801",
            "appendOnly": True,
            "previousEntryState": "active",
            "updatedEntryState": "none",
            "supersedesForecastId": None,
            "appendedForecastId": None,
        },
        "rejectionReasons": trigger["guardrailReasons"],
        "warnings": [
            "Post-outcome evidence must be used for resolution and scoring, not forecast-time recalculation.",
            "Rejected recalculation does not append a new forecast state.",
        ],
    }


def build_outputs() -> dict[Path, dict[str, Any]]:
    source_evidence = load_json(SOURCE_EVIDENCE)
    source_artifact = load_json(SOURCE_ARTIFACT)
    source_history = load_json(SOURCE_HISTORY)
    accepted_trigger = build_accepted_trigger()
    rejected_trigger = build_rejected_trigger()
    feature_snapshot = build_feature_snapshot(source_evidence)
    evidence = build_recalculated_evidence(source_evidence)
    artifact = build_recalculated_artifact(source_artifact, evidence)
    history = build_recalculated_history(source_history, evidence)
    accepted_run = build_accepted_run(accepted_trigger, source_evidence, evidence)
    rejected_run = build_rejected_run(rejected_trigger, evidence)
    outputs = {
        ACCEPTED_TRIGGER_PATH: accepted_trigger,
        REJECTED_TRIGGER_PATH: rejected_trigger,
        ACCEPTED_RUN_PATH: accepted_run,
        REJECTED_RUN_PATH: rejected_run,
        EVIDENCE_PATH: evidence,
        ARTIFACT_PATH: artifact,
        HISTORY_PATH: history,
        FEATURE_SNAPSHOT_PATH: feature_snapshot,
    }
    validate_outputs(outputs)
    return outputs


def validate_outputs(outputs: dict[Path, dict[str, Any]]) -> None:
    schemas = {
        ACCEPTED_TRIGGER_PATH: SPEC / "recalculation-trigger.schema.json",
        REJECTED_TRIGGER_PATH: SPEC / "recalculation-trigger.schema.json",
        ACCEPTED_RUN_PATH: SPEC / "recalculation-run.schema.json",
        REJECTED_RUN_PATH: SPEC / "recalculation-run.schema.json",
        EVIDENCE_PATH: SPEC / "evidence-packet.schema.json",
        ARTIFACT_PATH: SPEC / "forecast-artifact.schema.json",
        HISTORY_PATH: SPEC / "forecast-history.schema.json",
    }
    for path, schema in schemas.items():
        errors = validate_record(outputs[path], schema)
        if errors:
            raise RecalculationError(f"{path.name} schema validation failed: {errors[0]}")

    accepted_trigger = outputs[ACCEPTED_TRIGGER_PATH]
    rejected_trigger = outputs[REJECTED_TRIGGER_PATH]
    accepted_run = outputs[ACCEPTED_RUN_PATH]
    rejected_run = outputs[REJECTED_RUN_PATH]
    evidence = outputs[EVIDENCE_PATH]
    artifact = outputs[ARTIFACT_PATH]
    history = outputs[HISTORY_PATH]

    if artifact["forecastId"] != evidence["forecastId"] or artifact["evidencePacketId"] != evidence["evidencePacketId"]:
        raise RecalculationError("recalculated artifact/evidence binding mismatch")
    if accepted_run["updatedForecast"]["forecastId"] != evidence["forecastId"]:
        raise RecalculationError("accepted recalculation run should bind updated forecast")
    if history["entries"][-1]["forecastId"] != evidence["forecastId"]:
        raise RecalculationError("recalculated history must append the updated forecast")
    if history["entries"][-1]["supersedesForecastId"] != "forecast-602":
        raise RecalculationError("recalculated history must supersede the previous forecast")
    if accepted_trigger["postOutcomeEvidence"]:
        raise RecalculationError("accepted trigger must not use post-outcome evidence")
    if not rejected_trigger["postOutcomeEvidence"]:
        raise RecalculationError("rejected trigger should demonstrate post-outcome guardrail")
    if rejected_run["updatedForecast"] is not None:
        raise RecalculationError("rejected recalculation must not produce an updated forecast")

    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    if forecast_source_ids.intersection(resolution_source_ids):
        raise RecalculationError("recalculated evidence must not include resolution source provenance")


def write_outputs(outputs: dict[Path, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    expected_paths = set(outputs)
    for path in GENERATED.glob("*.generated.json"):
        if path not in expected_paths:
            path.unlink()
    for path, output in outputs.items():
        path.write_text(render_json(output), encoding="utf-8")
    print("generated recalculation history records")


def check_outputs(outputs: dict[Path, dict[str, Any]]) -> None:
    errors: list[str] = []
    for path, output in outputs.items():
        expected = render_json(output)
        if not path.exists():
            errors.append(f"missing recalculation output: {path}")
            continue
        if path.read_text(encoding="utf-8") != expected:
            errors.append(f"recalculation drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_recalculation_history.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked recalculation history records")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated recalculation records")
    parser.add_argument("--write", action="store_true", help="write generated recalculation records")
    args = parser.parse_args()
    try:
        outputs = build_outputs()
    except RecalculationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(outputs)
    else:
        check_outputs(outputs)


if __name__ == "__main__":
    main()
