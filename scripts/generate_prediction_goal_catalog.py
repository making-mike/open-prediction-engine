#!/usr/bin/env python3
"""Generate the checked domain-agnostic prediction goal catalog."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-goal-catalog"
OUTPUT_PATH = GENERATED / "ope-prediction-goal-catalog.generated.json"
SCHEMA = SPEC / "prediction-goal-catalog.schema.json"
GENERATED_AT = "2026-06-07T13:10:00Z"
CATALOG_GOAL_KEYS = [
    "delivery_delay_risk",
    "stockout_risk",
    "sla_breach_risk",
    "demand_risk",
    "churn_risk",
    "seaport_berth_availability",
    "weather_sensitive_operations",
    "public_transit_disruption_risk",
]
CATALOG_VIEWS = ["full", "summary", "goals", "classifications", "boundary"]


class PredictionGoalCatalogError(Exception):
    pass


def baseline_candidate(execution_allowed: bool = True) -> dict[str, Any]:
    return {
        "methodId": "historical_frequency_baseline",
        "methodClass": "historical_baseline" if execution_allowed else "blocked",
        "executionAllowed": execution_allowed,
        "qualityClaimAllowed": False,
        "notes": "Use the baseline until resolved comparable outcomes justify stronger methods.",
    }


def resolution_source(rule: str, *, available_before_forecast: bool = False) -> dict[str, Any]:
    return {
        "sourceRole": "resolution_outcome",
        "resolutionRule": rule,
        "availableBeforeForecast": available_before_forecast,
    }


def goal_example(
    goal_key: str,
    title: str,
    host_goal: str,
    classification: str,
    reason_codes: list[str],
    required_roles: list[str],
    resolution_rule: str,
    forecast_card_fields: list[str],
    first_safe_action: str,
    preferred_view: str,
    *,
    blocked_reason: str = "",
    execution_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "goalKey": goal_key,
        "goalTitle": title,
        "hostGoal": host_goal,
        "classification": classification,
        "reasonCodes": reason_codes,
        "requiredSourceRoles": required_roles,
        "baselineCandidate": baseline_candidate(execution_allowed),
        "resolutionSource": resolution_source(resolution_rule),
        "forecastCardFields": forecast_card_fields,
        "firstSafeHostAction": first_safe_action,
        "blockedReason": blocked_reason,
        "setupEnginePreferredView": preferred_view,
        "qualityClaimAllowed": False,
        "createsForecastArtifacts": False,
        "hostedRuntimeRequired": False,
    }


def classification_vocabulary() -> list[dict[str, str]]:
    return [
        {
            "classification": "forecastable",
            "meaning": "The goal can be rewritten as a measurable future question with declared evidence and resolution roles.",
            "firstSafeAction": "Choose the candidate contract and bind approved source references.",
        },
        {
            "classification": "needs_clarification",
            "meaning": "The goal is prediction-shaped but lacks a threshold, horizon, decision, or resolution rule.",
            "firstSafeAction": "Ask for the missing threshold, service window, decision, or outcome source.",
        },
        {
            "classification": "blocked",
            "meaning": "The goal includes unsafe inputs or source handling that OPE must not accept.",
            "firstSafeAction": "Replace raw credentials, raw rows, raw SQL, or unapproved sources with approved references.",
        },
        {
            "classification": "rejected",
            "meaning": "The goal is not a future-facing resolvable forecast contract.",
            "firstSafeAction": "Rewrite it as a future measurable outcome or use a non-forecast analysis path.",
        },
    ]


def goal_examples() -> list[dict[str, Any]]:
    return [
        goal_example(
            "delivery_delay_risk",
            "Delivery Delay Risk",
            "Predict whether a delivery lane will exceed a late-arrival threshold during a future dispatch window.",
            "forecastable",
            ["future_window_present", "threshold_present", "resolution_source_required"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve from the approved delivery outcome source after the dispatch window closes.",
            ["forecastId", "questionId", "probability", "threshold", "baselineMethod", "claimWarning"],
            "Bind approved dispatch, historical arrival, and outcome source references before source intake.",
            "contracts",
        ),
        goal_example(
            "stockout_risk",
            "Inventory Stockout Risk",
            "Predict whether a product will stock out before the next replenishment window.",
            "forecastable",
            ["future_event", "historical_outcome_needed", "resolution_source_required"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve from approved inventory snapshots after the replenishment window closes.",
            ["forecastId", "probability", "stockoutThreshold", "baselineMethod", "sourceSummary"],
            "Bind approved demand, inventory, replenishment, and outcome source references.",
            "sources",
        ),
        goal_example(
            "sla_breach_risk",
            "SLA Breach Risk",
            "Predict whether an operational queue will breach a declared SLA threshold during a future service window.",
            "forecastable",
            ["threshold_present", "baseline_needed", "resolution_window_present"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve from the approved SLA outcome source after the service window closes.",
            ["forecastId", "probability", "serviceWindow", "slaThreshold", "baselineMethod", "claimWarning"],
            "Bind approved queue state, historical breach, and outcome source references.",
            "baseline",
        ),
        goal_example(
            "demand_risk",
            "Demand Risk",
            "Predict whether future demand will be risky next month.",
            "needs_clarification",
            ["ambiguous_outcome_definition", "missing_threshold"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve only after the caller defines the demand metric, threshold, and outcome source.",
            ["forecastId", "probability", "demandMetric", "threshold", "baselineMethod", "claimWarning"],
            "Ask for the demand metric, threshold, forecast horizon, and resolution source before source intake.",
            "contracts",
        ),
        goal_example(
            "churn_risk",
            "Churn Risk With Unsafe Payload",
            "Use this API token and raw customer table to predict which accounts will churn next quarter.",
            "blocked",
            ["raw_credential_value", "raw_private_rows", "unapproved_source"],
            [],
            "Blocked inputs cannot define a resolution source until replaced with approved references.",
            [],
            "",
            "claim-boundary",
            blocked_reason="Credential values and raw private rows must be replaced with opaque source and credential references.",
            execution_allowed=False,
        ),
        goal_example(
            "seaport_berth_availability",
            "Seaport Berth Availability",
            "Predict whether a berth will be unavailable during a future vessel arrival window.",
            "forecastable",
            ["future_window_present", "threshold_present", "resolution_source_required"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve from approved berth occupancy or port-call outcome records after the arrival window.",
            ["forecastId", "probability", "berthWindow", "baselineMethod", "sourceSummary", "claimWarning"],
            "Bind approved arrival schedule, berth state, historical outcome, and resolution source references.",
            "sources",
        ),
        goal_example(
            "weather_sensitive_operations",
            "Weather-Sensitive Operations Attribution",
            "Explain whether yesterday's weather caused the operations disruption.",
            "rejected",
            ["past_tense_question", "not_future_facing"],
            [],
            "Past attribution is not a future forecast resolution path.",
            [],
            "",
            "examples",
            blocked_reason="The prompt asks for past attribution, not a resolvable future forecast.",
            execution_allowed=False,
        ),
        goal_example(
            "public_transit_disruption_risk",
            "Public Transit Disruption Risk",
            "Predict whether a public transit service window will exceed a delay or disruption threshold in the future.",
            "forecastable",
            ["future_window_present", "threshold_required", "resolution_source_required"],
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            "Resolve from an approved transit outcome source after the service window closes.",
            ["forecastId", "probability", "serviceWindow", "delayThreshold", "baselineMethod", "claimWarning"],
            "Bind approved schedule, service-state, historical outcome, and resolution source references.",
            "contracts",
        ),
    ]


def setup_engine_binding() -> dict[str, str]:
    return {
        "setupEngineId": "setupengine-001",
        "setupEngineCommand": 'python3 scripts/ope.py setup-engine --goal "add predictions to my app"',
        "examplesViewCommand": "python3 scripts/ope.py setup-engine --view examples",
        "relationship": "Setup-engine projects this catalog into its examples view so agents see reusable goal shapes before domain-specific examples.",
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "createsForecastArtifacts": False,
        "hostedRuntimeRequired": False,
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "fetchesLiveData": False,
        "storesCredentialValues": False,
        "acceptsRawPrivateRows": False,
        "acceptsRawSql": False,
    }


def build_summary(examples: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "goalExampleCount": len(examples),
        "forecastableCount": sum(1 for item in examples if item["classification"] == "forecastable"),
        "needsClarificationCount": sum(1 for item in examples if item["classification"] == "needs_clarification"),
        "blockedCount": sum(1 for item in examples if item["classification"] == "blocked"),
        "rejectedCount": sum(1 for item in examples if item["classification"] == "rejected"),
        "classificationCount": 4,
        "helsinkiDefaultNarrative": False,
        "qualityClaimAllowed": False,
    }


def build_prediction_goal_catalog() -> dict[str, Any]:
    examples = goal_examples()
    return {
        "predictionGoalCatalogId": "predictiongoalcatalog-001",
        "generatedAt": GENERATED_AT,
        "catalogStatus": "checked_domain_agnostic_goal_catalog",
        "setupEngineBinding": setup_engine_binding(),
        "classificationVocabulary": classification_vocabulary(),
        "goalExamples": examples,
        "executionBoundary": execution_boundary(),
        "summary": build_summary(examples),
        "warnings": [
            "Prediction goal catalog examples teach setup shape, not domain quality.",
            "Forecastable examples still require approved source references, resolver sources, and later scoring before claims.",
            "Blocked and rejected examples stop before source intake, forecast execution, hosted runtime, or quality claims.",
        ],
        "qualityClaimAllowed": False,
        "createsForecastArtifacts": False,
        "hostedRuntimeRequired": False,
    }


def validate_prediction_goal_catalog(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise PredictionGoalCatalogError("prediction goal catalog failed schema validation")


def goal_by_key(record: dict[str, Any], goal_key: str) -> dict[str, Any]:
    for item in record["goalExamples"]:
        if item["goalKey"] == goal_key:
            return item
    raise PredictionGoalCatalogError(f"unsupported catalog goal {goal_key}")


def compact_setup_engine_examples(record: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    catalog = record or build_prediction_goal_catalog()
    return [
        {
            "goalKey": item["goalKey"],
            "goal": item["hostGoal"],
            "classification": item["classification"],
            "reasonCodes": item["reasonCodes"],
            "preferredView": item["setupEnginePreferredView"],
        }
        for item in catalog["goalExamples"]
    ]


def view_payload(record: dict[str, Any], view: str, goal_key: str | None) -> Any:
    if goal_key:
        return goal_by_key(record, goal_key)
    if view == "full":
        return record
    if view == "summary":
        return {
            "view": "summary",
            "predictionGoalCatalogId": record["predictionGoalCatalogId"],
            "catalogStatus": record["catalogStatus"],
            "setupEngineBinding": record["setupEngineBinding"],
            "summary": record["summary"],
            "warnings": record["warnings"],
        }
    if view == "goals":
        return {
            "view": "goals",
            "predictionGoalCatalogId": record["predictionGoalCatalogId"],
            "goalExamples": record["goalExamples"],
            "summary": record["summary"],
        }
    if view == "classifications":
        return {
            "view": "classifications",
            "predictionGoalCatalogId": record["predictionGoalCatalogId"],
            "classificationVocabulary": record["classificationVocabulary"],
        }
    if view == "boundary":
        return {
            "view": "boundary",
            "predictionGoalCatalogId": record["predictionGoalCatalogId"],
            "executionBoundary": record["executionBoundary"],
            "qualityClaimAllowed": record["qualityClaimAllowed"],
            "createsForecastArtifacts": record["createsForecastArtifacts"],
            "hostedRuntimeRequired": record["hostedRuntimeRequired"],
        }
    raise PredictionGoalCatalogError(f"unsupported catalog view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", choices=CATALOG_VIEWS, default="full", help="print a focused catalog view")
    parser.add_argument("--goal", choices=CATALOG_GOAL_KEYS, help="print one catalog goal example")
    parser.add_argument("--write", action="store_true", help="write generated prediction-goal catalog fixture")
    parser.add_argument("--check", action="store_true", help="check generated prediction-goal catalog fixture")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_prediction_goal_catalog()
    validate_prediction_goal_catalog(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="prediction goal catalog",
            regen="python3 scripts/generate_prediction_goal_catalog.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="prediction goal catalog",
            regen="python3 scripts/generate_prediction_goal_catalog.py --write",
        )
        return
    print(render_json(view_payload(record, args.view, args.goal)), end="")


if __name__ == "__main__":
    main()
