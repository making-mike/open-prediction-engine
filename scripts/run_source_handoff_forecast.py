#!/usr/bin/env python3
"""Generate or check explicit setup forecasts from source-handoff method gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_live_weather_evidence import horizon_for_service_date, resolution_criteria, resolution_time_for_service_date
from generate_source_handoff_method_gate import build_records as build_method_gate_records
from generate_source_intake_handoff import CASE_ORDER, build_handoffs
from ope_schema import SPEC, validate_record
from run_setup_forecast import (
    HEAVY_RAIN_PROBABILITY_ADJUSTMENT,
    PRECIPITATION_THRESHOLD_MM,
    baseline_features,
    baseline_probability,
    deterministic_probability,
    source_by_role,
    source_ref,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-handoff-forecast"
GENERATED_AT = "2026-06-06T19:05:00Z"
FORECASTED_AT = "2026-06-02T10:45:00Z"

CASE_SUFFIX = {
    "unconfirmed_builder_draft": "1101",
    "confirmed_builder_draft": "1102",
    "insufficient_confirmed_builder_draft": "1103",
    "contains_secret": "1104",
    "unsupported_format": "1105",
    "oversized": "1106",
    "leakage": "1107",
}


class SourceHandoffForecastError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def output_prefix(case: str) -> str:
    return f"weather-logistics-{case_slug(case)}-source-handoff"


def rel_output(case: str, suffix: str) -> str:
    return f"spec/fixtures/generated/source-handoff-forecast/{output_prefix(case)}-{suffix}.generated.json"


def model_identity(case: str, selected_method_class: str) -> dict[str, Any]:
    if selected_method_class == "deterministic_statistical":
        return {
            "modelId": "model-101",
            "version": "weather-logistics-fixture-loop-v0",
            "trainingCutoff": "2026-05-30T00:00:00Z",
            "configurationHash": "sha256-fixture-loop-model-001",
        }
    return {
        "modelId": f"model-{CASE_SUFFIX[case]}",
        "version": "source-handoff-historical-baseline-fixture-v1",
        "configurationHash": f"sha256-source-handoff-forecast-model-{CASE_SUFFIX[case]}",
    }


def run_output_paths(case: str, generated: bool) -> dict[str, str | None]:
    if not generated:
        return {
            "questionPath": None,
            "featureSnapshotPath": None,
            "evidencePacketPath": None,
            "forecastArtifactPath": None,
            "forecastHistoryPath": None,
        }
    return {
        "questionPath": rel_output(case, "question"),
        "featureSnapshotPath": rel_output(case, "feature-snapshot"),
        "evidencePacketPath": rel_output(case, "evidence"),
        "forecastArtifactPath": rel_output(case, "artifact"),
        "forecastHistoryPath": rel_output(case, "history"),
    }


def run_record_binding(case: str, generated: bool) -> dict[str, str | None]:
    if not generated:
        return {
            "questionId": None,
            "forecastId": None,
            "evidencePacketId": None,
            "historyId": None,
            "forecastCardId": None,
            "forecastBundleId": None,
        }
    suffix = CASE_SUFFIX[case]
    return {
        "questionId": f"question-{suffix}",
        "forecastId": f"forecast-{suffix}",
        "evidencePacketId": f"evidence-{suffix}",
        "historyId": f"history-{suffix}",
        "forecastCardId": f"forecastcard-forecast-{suffix}",
        "forecastBundleId": f"forecastbundle-forecast-{suffix}",
    }


def blocked_reasons(handoff: dict[str, Any], summary: dict[str, Any], decision: dict[str, Any] | None) -> list[str]:
    reasons: set[str] = set()
    if summary["sourceIntakeReportId"] is None:
        reasons.add("source_intake_not_entered")
    if summary["methodGateStatus"] == "needs_mapping_confirmation":
        reasons.add("mapping_confirmation_required")
        reasons.add("source_intake_needs_confirmation")
    if summary["methodGateStatus"] == "needs_more_data":
        reasons.add("more_data_required")
    if summary["methodGateStatus"] == "not_entered_source_intake":
        reasons.add("builder_rejection")
    if summary["sourceIntakeStatus"] == "rejected":
        reasons.add("source_intake_rejected")
    if summary["sourceIntakeStatus"] == "needs_confirmation":
        reasons.add("forecast_generation_not_allowed")
    method_status = summary["eligibilitySummary"]["methodDecisionStatus"]
    if method_status in {"needs_confirmation", "rejected"}:
        reasons.add(f"method_decision_{method_status}")
    reasons.update(handoff["builderRejectionSummary"]["reasonCodes"])
    if decision is not None:
        for candidate in decision["methodCandidates"]:
            if candidate["methodClass"] in {"historical_baseline", "deterministic_statistical"}:
                reasons.update(candidate["reasonCodes"])
    return sorted(reasons)[:24]


def can_generate(report: dict[str, Any] | None, summary: dict[str, Any], decision: dict[str, Any] | None) -> bool:
    return (
        report is not None
        and decision is not None
        and report["forecastGenerationAllowed"] is True
        and summary["methodGateStatus"] in {"baseline_selected", "method_selected"}
        and summary["selectedMethodClass"] != "none"
    )


def build_run_summary(
    case: str,
    handoff: dict[str, Any],
    report: dict[str, Any] | None,
    summary: dict[str, Any],
    decision: dict[str, Any] | None,
    generated: bool,
) -> dict[str, Any]:
    return {
        "setupForecastRunId": f"setupforecastrun-{CASE_SUFFIX[case]}",
        "generatedAt": GENERATED_AT,
        "case": case,
        "domainSetupId": handoff["domainSetupId"],
        "domain": handoff["domain"],
        "sourceManifestId": handoff["sourceManifestId"],
        "fieldMappingId": handoff["fieldMappingId"],
        "sourceIntakeReportId": handoff["sourceIntakeReportId"],
        "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
        "sourceHandoffMethodGateId": summary["sourceHandoffMethodGateId"],
        "setupMethodDecisionId": summary["setupMethodDecisionId"],
        "setupBenchmarkGateId": summary["setupBenchmarkGateId"] if generated else None,
        "intakeStatus": handoff["sourceIntakeStatus"],
        "methodDecisionStatus": summary["eligibilitySummary"]["methodDecisionStatus"],
        "selectedMethodClass": summary["selectedMethodClass"],
        "selectedForecastMode": summary["selectedForecastMode"],
        "runStatus": "generated" if generated else "blocked",
        "executionMode": "fixture_dry_run" if generated else "not_started",
        "sourceMode": "source_handoff_fixture" if generated else "none",
        "controls": {
            "sourceIntakeValidated": report is not None,
            "methodDecisionValidated": decision is not None,
            "networkAccess": False,
            "liveFetch": False,
            "effectfulGeneration": False,
            "localLiveDraftConsumed": False,
            "forecastArtifactsCreated": generated,
        },
        "recordBinding": run_record_binding(case, generated),
        "outputs": run_output_paths(case, generated),
        "blockedReasons": [] if generated else blocked_reasons(handoff, summary, decision),
        "nextActions": [] if generated else summary["requiredActions"],
        "warnings": [
            "Source-handoff setup forecast execution is fixture-mode only.",
            "Execution requires a prior source-intake handoff, source-handoff method gate, setup benchmark gate, and setup method decision.",
            (
                "Generated forecast uses a handoff-bound deterministic method; quality claims remain blocked."
                if generated and summary["selectedMethodClass"] == "deterministic_statistical"
                else "Blocked handoff outcomes do not bind forecast IDs or artifact paths."
            ),
        ],
    }


def build_question(case: str, manifest: dict[str, Any], outcome_source: dict[str, Any]) -> dict[str, Any]:
    params = manifest["forecastParameters"]
    service_date = params["serviceDate"]
    geography = params["geography"]
    title = f"Will heavy rain disrupt last-mile delivery operations in {geography} on {service_date}?"
    horizon = horizon_for_service_date(service_date)
    return {
        "questionId": f"question-{CASE_SUFFIX[case]}",
        "title": title,
        "background": "Generated by explicit source-handoff setup forecast execution after accepted source intake and method gating.",
        "domain": manifest["domain"],
        "outputType": "binary",
        "status": "open",
        "openAt": FORECASTED_AT,
        "closeAt": params["forecastCloseTime"],
        "resolveAt": resolution_time_for_service_date(service_date),
        "horizon": horizon,
        "resolutionCriteria": resolution_criteria(geography, service_date, PRECIPITATION_THRESHOLD_MM),
        "resolutionAuthority": "OPE prototype resolver",
        "resolutionMode": "automated_measurement",
        "primaryResolutionSource": source_ref(outcome_source),
        "fallbackResolutionSources": [],
        "validOutcomeSpace": {
            "description": "Binary outcome: Yes if declared operations outcome says disruption_observed is true; No otherwise.",
            "labels": ["yes", "no"],
        },
        "clarificationHistory": [],
        "incentiveRiskReview": {
            "riskLevel": "minimal",
            "notes": "Handoff-bound fixture forecast with no network access, live fetch, local live draft, or private-source runtime.",
        },
        "createdAt": FORECASTED_AT,
        "updatedAt": FORECASTED_AT,
    }


def build_feature_snapshot(
    case: str,
    manifest: dict[str, Any],
    report: dict[str, Any],
    summary: dict[str, Any],
    decision: dict[str, Any],
    question: dict[str, Any],
    baseline_source: dict[str, Any],
    baseline_probability_value: float,
    forecast_probability: float,
    weather_source: dict[str, Any] | None,
    precipitation_mm: float | None,
) -> dict[str, Any]:
    features = baseline_features(baseline_source)
    features["sourceManifestId"] = manifest["sourceManifestId"]
    features["sourceIntakeHandoffId"] = summary["sourceIntakeHandoffId"]
    features["sourceHandoffMethodGateId"] = summary["sourceHandoffMethodGateId"]
    features["selectedMethodClass"] = decision["selectedMethodClass"]
    features["setupBenchmarkGateId"] = decision["selectedSetupBenchmarkGateId"]
    features["baselineProbability"] = baseline_probability_value
    features["forecastProbability"] = forecast_probability
    if weather_source is not None and precipitation_mm is not None:
        features["forecastSignalUsed"] = True
        features["weatherForecastSourceId"] = weather_source["sourceId"]
        features["forecastDailyPrecipitationMm"] = precipitation_mm
        features["precipitationThresholdMm"] = PRECIPITATION_THRESHOLD_MM
        features["heavyRainAdjustment"] = HEAVY_RAIN_PROBABILITY_ADJUSTMENT
    return {
        "featureSnapshotId": f"featuresnapshot-{CASE_SUFFIX[case]}",
        "domainSetupId": manifest["domainSetupId"],
        "sourceManifestId": manifest["sourceManifestId"],
        "sourceIntakeReportId": report["sourceIntakeReportId"],
        "sourceIntakeHandoffId": summary["sourceIntakeHandoffId"],
        "sourceHandoffMethodGateId": summary["sourceHandoffMethodGateId"],
        "setupMethodDecisionId": decision["setupMethodDecisionId"],
        "questionId": question["questionId"],
        "generatedAt": FORECASTED_AT,
        "domain": question["domain"],
        "horizon": question["horizon"],
        "sourceIds": [baseline_source["sourceId"], *([weather_source["sourceId"]] if weather_source else [])],
        "features": features,
    }


def build_evidence_packet(
    case: str,
    manifest: dict[str, Any],
    report: dict[str, Any],
    summary: dict[str, Any],
    decision: dict[str, Any],
    question: dict[str, Any],
    baseline_source: dict[str, Any],
    baseline_probability_value: float,
    forecast_probability: float,
    weather_source: dict[str, Any] | None,
    precipitation_mm: float | None,
) -> dict[str, Any]:
    provenance = [source_ref(baseline_source), *([source_ref(weather_source)] if weather_source else [])]
    input_source_classes: list[str] = []
    for source in [baseline_source, *([weather_source] if weather_source else [])]:
        if source["sourceClass"] not in input_source_classes:
            input_source_classes.append(source["sourceClass"])
    key_factors = [
        f"source intake handoff {summary['sourceIntakeHandoffId']}",
        f"source handoff method gate {summary['sourceHandoffMethodGateId']}",
        f"source intake report {report['sourceIntakeReportId']}",
        f"setup method decision {decision['setupMethodDecisionId']}",
        f"selected method {decision['selectedMethodClass']}",
        f"historical disruption days {baseline_source['positiveOutcomeCount']}",
        f"comparable service days {baseline_source['rowCount']}",
    ]
    if decision["selectedSetupBenchmarkGateId"] is not None:
        key_factors.append(f"setup benchmark gate {decision['selectedSetupBenchmarkGateId']}")
    if precipitation_mm is not None:
        key_factors.append(f"forecast precipitation {precipitation_mm:g} mm")
    key_factors.append("explicit source-handoff setup execution")
    return {
        "evidencePacketId": f"evidence-{CASE_SUFFIX[case]}",
        "forecastId": f"forecast-{CASE_SUFFIX[case]}",
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": question["domain"],
        "horizon": question["horizon"],
        "forecastedAt": FORECASTED_AT,
        "model": model_identity(case, decision["selectedMethodClass"]),
        "inputSourceClasses": input_source_classes,
        "provenanceReferences": provenance,
        "featureSnapshotRef": f"https://example.test/fixtures/generated/source-handoff-forecast/{output_prefix(case)}-feature-snapshot.generated.json",
        "forecastOutput": {
            "outputType": "binary",
            "probability": forecast_probability,
        },
        "baselineForecast": {
            "outputType": "binary",
            "probability": baseline_probability_value,
        },
        "calibrationBand": {
            "lower": round(max(0.0, forecast_probability - 0.1), 4),
            "upper": round(min(1.0, forecast_probability + 0.1), 4),
            "coverage": 0.8,
            "sampleSize": baseline_source["rowCount"],
        },
        "rationaleSummary": "Explicit handoff-bound execution selected the benchmark-gated setup method; quality claims remain blocked.",
        "keyFactors": key_factors,
        "resolutionCriteria": question["resolutionCriteria"],
        "resolutionSource": question["primaryResolutionSource"],
        "fallbackResolutionSources": question["fallbackResolutionSources"],
        "scheduledResolutionAt": question["resolveAt"],
    }


def build_forecast_artifact(question: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "forecastId": evidence["forecastId"],
        "questionId": question["questionId"],
        "questionStatus": "open",
        "domain": question["domain"],
        "horizon": question["horizon"],
        "forecastedAt": evidence["forecastedAt"],
        "closedAt": question["closeAt"],
        "outputType": question["outputType"],
        "forecastOutput": evidence["forecastOutput"],
        "baselineForecast": evidence["baselineForecast"],
        "model": evidence["model"],
        "evidencePacketId": evidence["evidencePacketId"],
        "resolutionPlan": {
            "resolutionCriteria": question["resolutionCriteria"],
            "resolutionAuthority": question["resolutionAuthority"],
            "primaryResolutionSource": question["primaryResolutionSource"],
            "fallbackResolutionSources": question["fallbackResolutionSources"],
            "scheduledResolutionAt": question["resolveAt"],
        },
    }


def build_history(case: str, question: dict[str, Any], evidence: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "historyId": f"history-{CASE_SUFFIX[case]}",
        "questionId": question["questionId"],
        "entries": [
            {
                "forecastId": evidence["forecastId"],
                "forecastedAt": evidence["forecastedAt"],
                "state": "active",
                "sourceClass": "baseline" if decision["selectedMethodClass"] == "historical_baseline" else "model",
                "model": evidence["model"],
                "forecastOutput": evidence["forecastOutput"],
                "rationaleSummary": evidence["rationaleSummary"],
                "evidencePacketId": evidence["evidencePacketId"],
            }
        ],
        "createdAt": evidence["forecastedAt"],
        "updatedAt": evidence["forecastedAt"],
    }


def build_case_outputs(
    case: str,
    handoff: dict[str, Any],
    manifest: dict[str, Any] | None,
    report: dict[str, Any] | None,
    summary: dict[str, Any],
    decision: dict[str, Any] | None,
) -> dict[str, Any]:
    generated = can_generate(report, summary, decision)
    outputs: dict[str, Any] = {
        f"{output_prefix(case)}-setup-forecast-run.generated.json": build_run_summary(
            case,
            handoff,
            report,
            summary,
            decision,
            generated,
        )
    }
    if not generated:
        validate_case_outputs(case, outputs)
        return outputs
    if manifest is None or report is None or decision is None:
        raise SourceHandoffForecastError(f"{case} generated run requires manifest, report, and decision")

    baseline_source = source_by_role(manifest, "historical_baseline")
    outcome_source = source_by_role(manifest, "declared_operations_outcome")
    if baseline_source is None or outcome_source is None:
        raise SourceHandoffForecastError("generated source-handoff forecast requires baseline and outcome source roles")
    baseline_probability_value = baseline_probability(baseline_source)
    forecast_probability = baseline_probability_value
    weather_source = None
    precipitation_mm = None
    if decision["selectedMethodClass"] == "deterministic_statistical":
        weather_source = source_by_role(manifest, "weather_forecast")
        if weather_source is None:
            raise SourceHandoffForecastError("deterministic source-handoff forecast requires weather forecast source")
        if decision["selectedSetupBenchmarkGateId"] is None:
            raise SourceHandoffForecastError("deterministic source-handoff forecast requires setup benchmark gate binding")
        forecast_probability, precipitation_mm = deterministic_probability(baseline_probability_value, weather_source)
    elif decision["selectedMethodClass"] != "historical_baseline":
        raise SourceHandoffForecastError(f"unsupported source-handoff setup forecast method {decision['selectedMethodClass']}")

    question = build_question(case, manifest, outcome_source)
    feature_snapshot = build_feature_snapshot(
        case,
        manifest,
        report,
        summary,
        decision,
        question,
        baseline_source,
        baseline_probability_value,
        forecast_probability,
        weather_source,
        precipitation_mm,
    )
    evidence = build_evidence_packet(
        case,
        manifest,
        report,
        summary,
        decision,
        question,
        baseline_source,
        baseline_probability_value,
        forecast_probability,
        weather_source,
        precipitation_mm,
    )
    artifact = build_forecast_artifact(question, evidence)
    history = build_history(case, question, evidence, decision)
    outputs.update(
        {
            f"{output_prefix(case)}-question.generated.json": question,
            f"{output_prefix(case)}-feature-snapshot.generated.json": feature_snapshot,
            f"{output_prefix(case)}-evidence.generated.json": evidence,
            f"{output_prefix(case)}-artifact.generated.json": artifact,
            f"{output_prefix(case)}-history.generated.json": history,
        }
    )
    validate_case_outputs(case, outputs)
    return outputs


def validate_case_outputs(case: str, outputs: dict[str, Any]) -> None:
    prefix = output_prefix(case)
    schemas = {
        f"{prefix}-setup-forecast-run.generated.json": "setup-forecast-run.schema.json",
        f"{prefix}-question.generated.json": "forecast-question.schema.json",
        f"{prefix}-evidence.generated.json": "evidence-packet.schema.json",
        f"{prefix}-artifact.generated.json": "forecast-artifact.schema.json",
        f"{prefix}-history.generated.json": "forecast-history.schema.json",
    }
    for filename, schema_name in schemas.items():
        if filename not in outputs:
            continue
        errors = validate_record(outputs[filename], SPEC / schema_name)
        if errors:
            raise SourceHandoffForecastError(f"{filename} failed schema validation: {errors[0]}")

    run = outputs[f"{prefix}-setup-forecast-run.generated.json"]
    if run["runStatus"] == "blocked":
        if any(run["recordBinding"][field] is not None for field in run["recordBinding"]):
            raise SourceHandoffForecastError("blocked source-handoff setup forecast must not bind forecast outputs")
        if run["controls"]["forecastArtifactsCreated"] is not False:
            raise SourceHandoffForecastError("blocked source-handoff setup forecast must not create artifacts")
        return

    question = outputs[f"{prefix}-question.generated.json"]
    evidence = outputs[f"{prefix}-evidence.generated.json"]
    artifact = outputs[f"{prefix}-artifact.generated.json"]
    history = outputs[f"{prefix}-history.generated.json"]
    if run["sourceIntakeHandoffId"] is None or run["sourceHandoffMethodGateId"] is None:
        raise SourceHandoffForecastError("generated source-handoff setup forecast must bind handoff and method gate")
    if artifact["forecastId"] != evidence["forecastId"]:
        raise SourceHandoffForecastError("artifact/evidence forecast binding mismatch")
    if artifact["questionId"] != question["questionId"] or evidence["questionId"] != question["questionId"]:
        raise SourceHandoffForecastError("source-handoff setup forecast question binding mismatch")
    if artifact["evidencePacketId"] != evidence["evidencePacketId"]:
        raise SourceHandoffForecastError("source-handoff setup forecast evidence binding mismatch")
    if run["selectedMethodClass"] == "historical_baseline":
        if artifact["forecastOutput"] != artifact["baselineForecast"]:
            raise SourceHandoffForecastError("source-handoff baseline forecast must equal baseline output")
    elif run["selectedMethodClass"] == "deterministic_statistical":
        if artifact["forecastOutput"] == artifact["baselineForecast"]:
            raise SourceHandoffForecastError("source-handoff deterministic forecast must differ from baseline output")
        if run["setupBenchmarkGateId"] is None:
            raise SourceHandoffForecastError("source-handoff deterministic forecast must bind setup benchmark gate")
        source_types = {source["sourceType"] for source in evidence["provenanceReferences"]}
        if source_types != {"internal_dataset", "public_dataset"}:
            raise SourceHandoffForecastError("source-handoff deterministic forecast must use baseline and forecast-time weather provenance")
    else:
        raise SourceHandoffForecastError(f"unsupported generated source-handoff method {run['selectedMethodClass']}")
    if history["entries"][-1]["forecastId"] != artifact["forecastId"]:
        raise SourceHandoffForecastError("source-handoff forecast history must end with active forecast")
    if run["recordBinding"]["forecastId"] != artifact["forecastId"]:
        raise SourceHandoffForecastError("source-handoff run/forecast binding mismatch")
    if run["controls"]["networkAccess"] or run["controls"]["liveFetch"] or run["controls"]["localLiveDraftConsumed"]:
        raise SourceHandoffForecastError("source-handoff forecast must not use network, live fetch, or local live drafts")
    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        question["primaryResolutionSource"]["sourceId"],
        *[source["sourceId"] for source in question.get("fallbackResolutionSources", [])],
    }
    if forecast_source_ids.intersection(resolution_source_ids):
        raise SourceHandoffForecastError("source-handoff forecast provenance must not include resolution sources")


def build_outputs() -> dict[str, Any]:
    handoff_records = build_handoffs()
    method_gate_records = build_method_gate_records()
    outputs: dict[str, Any] = {}
    for case in CASE_ORDER:
        handoff, _build, manifest, _field_mapping, report = handoff_records[case]
        summary, _benchmark_gate, decision = method_gate_records[case]
        outputs.update(build_case_outputs(case, handoff, manifest, report, summary, decision))
    return outputs


def write_outputs(outputs: dict[str, Any]) -> None:
    expected_names = set(outputs)
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path in GENERATED.glob("*.generated.json"):
        if path.name not in expected_names:
            path.unlink()
    for filename, output in outputs.items():
        write_json(GENERATED / filename, output)
    print(f"generated {len(outputs)} source-handoff setup forecast outputs")


def check_outputs(outputs: dict[str, Any]) -> None:
    expected_names = set(outputs)
    errors: list[str] = []
    for path in sorted(GENERATED.glob("*.generated.json")):
        if path.name not in expected_names:
            errors.append(f"stale source-handoff setup forecast output: {path}")
    for filename, output in outputs.items():
        path = GENERATED / filename
        expected = render_json(output)
        if not path.exists():
            errors.append(f"missing source-handoff setup forecast output: {path}")
            continue
        if path.read_text(encoding="utf-8") != expected:
            errors.append(f"source-handoff setup forecast drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/run_source_handoff_forecast.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {len(outputs)} source-handoff setup forecast outputs")


def summary(outputs: dict[str, Any]) -> dict[str, Any]:
    runs = [
        record
        for name, record in outputs.items()
        if name.endswith("-setup-forecast-run.generated.json")
    ]
    return {
        "count": len(runs),
        "runs": [
            {
                "case": run["case"],
                "setupForecastRunId": run["setupForecastRunId"],
                "sourceIntakeHandoffId": run["sourceIntakeHandoffId"],
                "sourceHandoffMethodGateId": run["sourceHandoffMethodGateId"],
                "runStatus": run["runStatus"],
                "selectedMethodClass": run["selectedMethodClass"],
                "forecastId": run["recordBinding"]["forecastId"],
                "forecastArtifactsCreated": run["controls"]["forecastArtifactsCreated"],
            }
            for run in sorted(runs, key=lambda item: item["setupForecastRunId"])
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source-handoff setup forecast run")
    parser.add_argument("--check", action="store_true", help="check generated source-handoff setup forecast drift")
    parser.add_argument("--write", action="store_true", help="write generated source-handoff setup forecast outputs")
    args = parser.parse_args()
    try:
        outputs = build_outputs()
    except SourceHandoffForecastError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(outputs)
    elif args.check:
        check_outputs(outputs)
    elif args.case:
        key = f"{output_prefix(args.case)}-setup-forecast-run.generated.json"
        sys.stdout.write(render_json(outputs[key]))
    else:
        sys.stdout.write(render_json(summary(outputs)))


if __name__ == "__main__":
    main()
