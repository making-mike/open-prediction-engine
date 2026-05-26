#!/usr/bin/env python3
"""Generate or check domain-agnostic OPE engine setup records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "domain-setups"
SCHEMA = SPEC / "domain-setup.schema.json"
GENERATED_AT = "2026-06-06T15:10:00Z"

WEATHER_DOMAIN = "weather-logistics"
SEAPORT_DOMAIN = "seaport-berth-availability"
TRANSIT_DOMAIN = "weather-transit-delays"

SETUP_PATHS = {
    WEATHER_DOMAIN: GENERATED / "weather-logistics-domain-setup.generated.json",
    SEAPORT_DOMAIN: GENERATED / "seaport-berth-availability-domain-setup.generated.json",
    TRANSIT_DOMAIN: GENERATED / "weather-transit-delays-domain-setup.generated.json",
}


class DomainSetupError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def field(
    name: str,
    field_type: str,
    required_for: list[str],
    validation_rules: list[str],
) -> dict[str, Any]:
    return {
        "fieldName": name,
        "fieldType": field_type,
        "requiredFor": required_for,
        "validationRules": validation_rules,
    }


def build_weather_setup() -> dict[str, Any]:
    return {
        "domainSetupId": "domainsetup-001",
        "generatedAt": GENERATED_AT,
        "domain": WEATHER_DOMAIN,
        "displayName": "Weather Logistics Reference Setup",
        "setupKind": "reference_setup",
        "maturityStatus": "fixture_ready",
        "domainPurpose": (
            "Forecast binary operational disruption risk from weather signals, historical baselines, "
            "and declared post-window outcomes in a local fixture-safe reference domain."
        ),
        "questionTemplates": [
            {
                "templateId": "template-001",
                "template": "Will heavy rain disrupt last-mile delivery operations in {geography} on {service_date}?",
                "outputType": "binary",
                "horizonLabels": ["1-day", "same-day"],
                "requiredParameters": ["geography", "service_date"],
                "resolvabilityRules": [
                    "The service date must be known before forecast close.",
                    "The geography must map to an allowed location in the source policy.",
                    "The disruption outcome must be declared after the service window closes.",
                ],
            }
        ],
        "sourceRoles": [
            {
                "roleId": "sourcerole-001",
                "roleKey": "weather_forecast",
                "displayName": "Forecast-Time Weather Evidence",
                "timing": "forecast_time",
                "purpose": "Provides weather features available before forecast close for the requested geography and date.",
                "requiredFields": [
                    field("geography", "string", ["forecast"], ["Must match the requested geography."]),
                    field("service_date", "date", ["forecast"], ["Must match the requested service date."]),
                    field(
                        "retrieved_at",
                        "date_time",
                        ["forecast"],
                        ["Must be before forecast close and inside the retrieval window."],
                    ),
                    field(
                        "forecast_daily_precipitation_mm",
                        "number",
                        ["forecast", "classification"],
                        ["Must be a non-negative millimeter value."],
                    ),
                ],
                "optionalFields": [
                    field("source_status", "categorical", ["forecast"], ["Use current or corrected source status."])
                ],
                "allowedSourceClasses": ["official", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-002",
                "roleKey": "historical_baseline",
                "displayName": "Historical Baseline Inputs",
                "timing": "baseline",
                "purpose": "Provides comparable prior outcomes for baseline frequency and method comparison.",
                "requiredFields": [
                    field("service_date", "date", ["baseline"], ["Must predate the forecast target date."]),
                    field("geography", "string", ["baseline"], ["Must match or map to the requested geography."]),
                    field("disruption_observed", "boolean", ["baseline", "scoring"], ["Must be a resolved binary outcome."]),
                ],
                "optionalFields": [
                    field("precipitation_mm", "number", ["baseline"], ["Use when historical weather severity is available."])
                ],
                "allowedSourceClasses": ["internal_dataset", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-003",
                "roleKey": "declared_operations_outcome",
                "displayName": "Declared Operations Outcome",
                "timing": "resolution",
                "purpose": "Provides post-window resolution and scoring evidence after the delivery operations window closes.",
                "requiredFields": [
                    field("service_date", "date", ["resolution"], ["Must match the forecast service date."]),
                    field("geography", "string", ["resolution"], ["Must match the forecast geography."]),
                    field("disruption_observed", "boolean", ["resolution", "scoring"], ["Must resolve to true or false."]),
                ],
                "optionalFields": [
                    field("resolution_notes", "string", ["resolution"], ["Use only for sanitized resolution notes."])
                ],
                "allowedSourceClasses": ["internal_dataset", "human_judgment"],
                "forecastTimeAllowed": False,
            },
        ],
        "entityRequirements": [
            {
                "entityType": "geography",
                "canonicalField": "geography",
                "aliasPolicy": "user_provided_registry",
                "required": True,
            }
        ],
        "resolutionPolicy": {
            "primarySourceRole": "declared_operations_outcome",
            "fallbackSourceRoles": [],
            "yesOutcomeDefinition": "Declared operations outcome says disruption_observed is true for the target date.",
            "noOutcomeDefinition": "Declared operations outcome says disruption_observed is false for the target date.",
            "ambiguousIf": [
                "Outcome source reports conflicting disruption states.",
                "The operations window changed after forecast close in a way that changes the question meaning.",
            ],
            "annulledIf": [
                "The delivery operation did not occur for reasons unrelated to weather.",
                "The requested geography or service date was invalid before forecast close.",
            ],
            "resolutionTiming": "Resolve after the service date operations window closes and before scoring.",
            "scoringRule": "brier",
        },
        "scoringPolicy": {
            "primaryScoringRule": "brier",
            "baselineComparisonRequired": True,
            "excludeAmbiguousOutcomes": True,
            "excludeAnnulledOutcomes": True,
            "reportingSlices": [
                "domain",
                "domain_setup",
                "horizon",
                "output_type",
                "resolution_source",
                "source_policy",
                "method_class",
                "coverage_period",
                "sample_size",
            ],
            "minimumResolvedForecastsForQualityClaim": 100,
        },
        "baselinePolicy": {
            "baselineRequired": True,
            "allowedBaselineMethods": ["historical_frequency", "climatology_frequency"],
            "minimumComparableRows": 30,
            "minimumPositiveOutcomes": 1,
            "fallbackWhenInsufficientData": "baseline_only",
        },
        "methodPolicy": {
            "enabledMethodClasses": ["historical_baseline", "deterministic_statistical"],
            "selectionRule": (
                "Select the strongest enabled method with clean comparable benchmark evidence for the request source "
                "policy; otherwise fall back to the historical baseline."
            ),
            "baselineComparisonRequired": True,
            "leakageCheckRequired": True,
            "methodDecisionRecordRequired": True,
        },
        "recalculationPolicy": {
            "supported": True,
            "triggerTypes": ["source_file_changed", "schedule", "agent_submitted_evidence", "manual"],
            "appendHistoryRequired": True,
            "postOutcomeEvidenceAllowed": False,
        },
        "localImplementation": {
            "forecastRunnable": True,
            "generatedForecastRecords": True,
            "cliForecastCommand": "python3 scripts/ope.py forecast-run",
            "readSurfaceAvailable": True,
            "implementationNotes": "Reference setup is fixture-ready through local CLI and generated forecast records.",
        },
        "claimPolicy": {
            "allowedClaims": [
                "Fixture-ready reference setup for local weather-logistics forecast records.",
                "Baseline comparison and evidence provenance are available for generated fixture records.",
            ],
            "blockedClaims": [
                "Live calibration claim",
                "Production readiness claim",
                "State-of-the-art performance claim",
                "Universal domain coverage claim",
            ],
            "minimumResolvedForecastsForCalibration": 100,
            "qualityClaimAllowed": False,
            "benchmarkClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
            "universalDomainClaimAllowed": False,
        },
        "agentSetupGuidance": {
            "setupQuestions": [
                "Which geography and service date are being forecast?",
                "Which source policy allows forecast-time weather evidence?",
                "Which outcome source will resolve the disruption state after the service window?",
            ],
            "requiredBeforeForecast": [
                "A resolvable binary question with forecast close and service date.",
                "Allowed forecast-time weather evidence or committed fixture evidence.",
                "A baseline input source and resolution source binding.",
            ],
            "safeFailureModes": [
                "Reject if the requested source policy allows unbounded web search.",
                "Fall back to baseline when stronger methods lack clean benchmark evidence.",
                "Do not score ambiguous, annulled, or unresolved outcomes as normal forecasts.",
            ],
        },
        "warnings": [
            "Weather-logistics is a reference setup, not the product boundary.",
            "Fixture-ready does not mean calibrated, production-ready, or live-source forecast-ready.",
            "Resolution data must not be used as forecast-time evidence.",
        ],
    }


def build_seaport_setup() -> dict[str, Any]:
    return {
        "domainSetupId": "domainsetup-002",
        "generatedAt": GENERATED_AT,
        "domain": SEAPORT_DOMAIN,
        "displayName": "Seaport Berth Availability Candidate Setup",
        "setupKind": "candidate_private_setup",
        "maturityStatus": "candidate",
        "domainPurpose": (
            "Describe a private operational setup for forecasting whether a scheduled asset will fail to occupy "
            "capacity on a target date, leaving capacity potentially available."
        ),
        "questionTemplates": [
            {
                "templateId": "template-002",
                "template": (
                    "Will {asset_identifier} fail to occupy {location} during {service_date}, "
                    "leaving capacity available?"
                ),
                "outputType": "binary",
                "horizonLabels": ["same-day", "1-day", "3-day"],
                "requiredParameters": ["asset_identifier", "location", "service_date"],
                "resolvabilityRules": [
                    "The scheduled asset, location, and target date must be known before forecast close.",
                    "The capacity-occupation rule must state the exact time window and threshold.",
                    "Outcome evidence must be unavailable to the forecast-time method until after close.",
                ],
            }
        ],
        "sourceRoles": [
            {
                "roleId": "sourcerole-004",
                "roleKey": "vessel_schedule",
                "displayName": "Scheduled Asset Plan",
                "timing": "forecast_time",
                "purpose": "Provides planned arrival, departure, asset identity, and requested capacity before forecast close.",
                "requiredFields": [
                    field("asset_identifier", "id", ["forecast"], ["Must be stable across schedule and outcome data."]),
                    field("location", "string", ["forecast"], ["Must map to the requested capacity location."]),
                    field("scheduled_eta", "date_time", ["forecast"], ["Must be available before forecast close."]),
                    field("service_date", "date", ["forecast"], ["Must match the forecast target date."]),
                ],
                "optionalFields": [
                    field("operator", "string", ["classification"], ["Use only when allowed by the private source policy."])
                ],
                "allowedSourceClasses": ["internal_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-005",
                "roleKey": "historical_arrivals",
                "displayName": "Historical Arrival Outcomes",
                "timing": "historical_training",
                "purpose": "Provides prior planned and actual capacity occupation outcomes for baseline and conditioned methods.",
                "requiredFields": [
                    field("asset_identifier", "id", ["baseline"], ["Must be joinable to schedule records when available."]),
                    field("scheduled_eta", "date_time", ["baseline"], ["Must predate the target forecast close."]),
                    field("actual_arrival_at", "date_time", ["baseline", "resolution"], ["Must be null-free for resolved rows."]),
                    field("occupied_capacity", "boolean", ["baseline", "scoring"], ["Must resolve to true or false."]),
                ],
                "optionalFields": [
                    field("delay_minutes", "number", ["classification"], ["Use non-negative values when available."])
                ],
                "allowedSourceClasses": ["internal_dataset", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-006",
                "roleKey": "berth_occupancy",
                "displayName": "Capacity Occupancy Snapshot",
                "timing": "forecast_time",
                "purpose": "Provides current capacity status and constraints that may affect availability before forecast close.",
                "requiredFields": [
                    field("location", "string", ["forecast"], ["Must map to the requested capacity location."]),
                    field("observed_at", "date_time", ["forecast"], ["Must be before forecast close."]),
                    field("capacity_available", "boolean", ["classification"], ["Must be a forecast-time status value."]),
                ],
                "optionalFields": [
                    field("constraint_code", "categorical", ["classification"], ["Use caller-defined constraint taxonomy."])
                ],
                "allowedSourceClasses": ["internal_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-007",
                "roleKey": "ais_position",
                "displayName": "Position Or Movement Evidence",
                "timing": "supporting",
                "purpose": "Provides optional forecast-time movement or position signals when the private setup allows them.",
                "requiredFields": [
                    field("asset_identifier", "id", ["forecast"], ["Must map to the scheduled asset."]),
                    field("observed_at", "date_time", ["forecast"], ["Must be before forecast close."]),
                    field("distance_to_location_km", "number", ["classification"], ["Must be non-negative."]),
                ],
                "optionalFields": [
                    field("speed_knots", "number", ["classification"], ["Use non-negative values when available."])
                ],
                "allowedSourceClasses": ["public_dataset", "internal_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-008",
                "roleKey": "marine_weather",
                "displayName": "Weather Or Conditions Evidence",
                "timing": "supporting",
                "purpose": "Provides optional weather, sea state, or operational conditions for conditioned methods.",
                "requiredFields": [
                    field("location", "string", ["forecast"], ["Must map to the requested geography or route segment."]),
                    field("forecast_valid_at", "date_time", ["forecast"], ["Must be relevant to the target window."]),
                    field("condition_severity", "categorical", ["classification"], ["Use the setup-defined severity taxonomy."]),
                ],
                "optionalFields": [
                    field("wind_speed", "number", ["classification"], ["Use units declared by the source manifest."])
                ],
                "allowedSourceClasses": ["official", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-009",
                "roleKey": "operations_outcome",
                "displayName": "Post-Window Occupancy Outcome",
                "timing": "resolution",
                "purpose": "Provides post-window resolution evidence for whether the asset occupied the capacity slot.",
                "requiredFields": [
                    field("asset_identifier", "id", ["resolution"], ["Must match the forecasted asset."]),
                    field("location", "string", ["resolution"], ["Must match the forecasted location."]),
                    field("service_date", "date", ["resolution"], ["Must match the forecasted service date."]),
                    field("occupied_capacity", "boolean", ["resolution", "scoring"], ["Must resolve to true or false."]),
                ],
                "optionalFields": [
                    field("outcome_notes", "string", ["resolution"], ["Use only sanitized outcome notes."])
                ],
                "allowedSourceClasses": ["internal_dataset", "human_judgment"],
                "forecastTimeAllowed": False,
            },
        ],
        "entityRequirements": [
            {
                "entityType": "asset",
                "canonicalField": "asset_identifier",
                "aliasPolicy": "user_provided_registry",
                "required": True,
            },
            {
                "entityType": "location",
                "canonicalField": "location",
                "aliasPolicy": "agent_proposed_requires_confirmation",
                "required": True,
            },
        ],
        "resolutionPolicy": {
            "primarySourceRole": "operations_outcome",
            "fallbackSourceRoles": [],
            "yesOutcomeDefinition": "The target asset did not occupy the target capacity slot during the target window.",
            "noOutcomeDefinition": "The target asset occupied the target capacity slot during the target window.",
            "ambiguousIf": [
                "Outcome records disagree about whether the asset occupied the slot.",
                "The capacity slot or time window cannot be matched to the forecast question.",
            ],
            "annulledIf": [
                "The scheduled operation was canceled before forecast close.",
                "The caller cannot define the target asset, location, or outcome window.",
            ],
            "resolutionTiming": "Resolve only after the target capacity window closes.",
            "scoringRule": "brier",
        },
        "scoringPolicy": {
            "primaryScoringRule": "brier",
            "baselineComparisonRequired": True,
            "excludeAmbiguousOutcomes": True,
            "excludeAnnulledOutcomes": True,
            "reportingSlices": [
                "domain",
                "domain_setup",
                "horizon",
                "output_type",
                "resolution_source",
                "source_policy",
                "method_class",
                "coverage_period",
                "sample_size",
            ],
            "minimumResolvedForecastsForQualityClaim": 200,
        },
        "baselinePolicy": {
            "baselineRequired": True,
            "allowedBaselineMethods": ["historical_frequency", "conditioned_historical_frequency"],
            "minimumComparableRows": 100,
            "minimumPositiveOutcomes": 10,
            "fallbackWhenInsufficientData": "needs_more_data",
        },
        "methodPolicy": {
            "enabledMethodClasses": [
                "historical_baseline",
                "historical_conditioned_frequency",
                "deterministic_statistical",
                "model_assisted",
                "external_reference",
                "ensemble",
            ],
            "selectionRule": (
                "Start from the baseline, then enable stronger methods only after source manifests, field mappings, "
                "sample-size checks, leakage checks, and comparable benchmarks pass for this private setup."
            ),
            "baselineComparisonRequired": True,
            "leakageCheckRequired": True,
            "methodDecisionRecordRequired": True,
        },
        "recalculationPolicy": {
            "supported": True,
            "triggerTypes": ["source_file_changed", "api_event", "schedule", "agent_submitted_evidence", "manual"],
            "appendHistoryRequired": True,
            "postOutcomeEvidenceAllowed": False,
        },
        "localImplementation": {
            "forecastRunnable": False,
            "generatedForecastRecords": False,
            "cliForecastCommand": None,
            "readSurfaceAvailable": False,
            "implementationNotes": "Candidate setup is descriptive only until source manifests, field mappings, and checks land.",
        },
        "claimPolicy": {
            "allowedClaims": [
                "Candidate private setup shape can be inspected by agents.",
                "Required source roles, fields, method policy, and resolution policy are explicit.",
            ],
            "blockedClaims": [
                "Calibrated forecast quality claim",
                "Benchmarked forecast quality claim",
                "Production readiness claim",
                "State-of-the-art performance claim",
                "Universal domain coverage claim",
            ],
            "minimumResolvedForecastsForCalibration": 200,
            "qualityClaimAllowed": False,
            "benchmarkClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
            "universalDomainClaimAllowed": False,
        },
        "agentSetupGuidance": {
            "setupQuestions": [
                "What exact asset, location, target window, and outcome definition should be forecast?",
                "Which private files, APIs, or databases can be used before forecast close?",
                "Which source resolves the outcome after the target window and how is leakage prevented?",
            ],
            "requiredBeforeForecast": [
                "A confirmed source manifest for schedule, historical outcome, and resolution data.",
                "Field mappings for asset, location, scheduled time, actual outcome, and forecast close.",
                "Enough comparable historical rows or an explicit needs-more-data decision.",
            ],
            "safeFailureModes": [
                "Return needs_more_data when required source roles are missing.",
                "Treat agent-proposed aliases or mappings as pending until confirmed.",
                "Block calibration, benchmark, production, and state-of-the-art claims for candidate setups.",
            ],
        },
        "warnings": [
            "Candidate setup does not implement a runnable seaport forecasting model.",
            "Private source mappings must be supplied or confirmed before forecasting.",
            "No calibration, benchmark, production, or state-of-the-art claim is allowed for this setup.",
        ],
    }


def build_transit_setup() -> dict[str, Any]:
    return {
        "domainSetupId": "domainsetup-003",
        "generatedAt": GENERATED_AT,
        "domain": TRANSIT_DOMAIN,
        "displayName": "Weather Transit Delays Local Prototype Setup",
        "setupKind": "reference_setup",
        "maturityStatus": "fixture_ready",
        "domainPurpose": (
            "Forecast whether a declared public transport network exceeds a delay threshold during a service "
            "window, using local forecast-time weather files and historical transit delay outcomes."
        ),
        "questionTemplates": [
            {
                "templateId": "template-003",
                "template": (
                    "Will {transit_network} in {geography} exceed the beta delay threshold during "
                    "{service_window} on {service_date}?"
                ),
                "outputType": "binary",
                "horizonLabels": ["same-day-morning-peak", "1-day"],
                "requiredParameters": ["transit_network", "geography", "service_window", "service_date"],
                "resolvabilityRules": [
                    "The transit network, geography, service window, and service date must be fixed before forecast close.",
                    "The late observation threshold and event threshold must be declared before forecast close.",
                    "Outcome rows from the target service window must be excluded from forecast-time evidence.",
                ],
            }
        ],
        "sourceRoles": [
            {
                "roleId": "sourcerole-010",
                "roleKey": "weather_forecast",
                "displayName": "Forecast-Time Weather Evidence",
                "timing": "forecast_time",
                "purpose": "Provides weather features available before forecast close for the target geography and window.",
                "requiredFields": [
                    field("geography", "string", ["forecast"], ["Must match the requested geography."]),
                    field("service_date", "date", ["forecast"], ["Must match the requested service date."]),
                    field("retrieved_at", "date_time", ["forecast"], ["Must be before forecast close."]),
                    field(
                        "forecast_precipitation_mm",
                        "number",
                        ["forecast", "classification"],
                        ["Use non-negative millimeter values for the service window or day."],
                    ),
                ],
                "optionalFields": [
                    field("forecast_snowfall_mm", "number", ["classification"], ["Use non-negative millimeter values."]),
                    field("forecast_wind_gust_kmh", "number", ["classification"], ["Use non-negative km/h values."]),
                    field("temperature_c", "number", ["classification"], ["Use degrees Celsius."]),
                ],
                "allowedSourceClasses": ["official", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-011",
                "roleKey": "historical_delay_baseline",
                "displayName": "Historical Transit Delay Outcomes",
                "timing": "baseline",
                "purpose": "Provides comparable prior delay-threshold outcomes for baseline frequency.",
                "requiredFields": [
                    field("service_date", "date", ["baseline"], ["Must predate the target forecast close."]),
                    field("transit_network", "string", ["baseline"], ["Must map to the requested transit network."]),
                    field("service_window", "categorical", ["baseline"], ["Must map to the requested service window."]),
                    field("delay_event", "boolean", ["baseline", "scoring"], ["Must resolve to true or false."]),
                ],
                "optionalFields": [
                    field(
                        "late_observation_ratio",
                        "number",
                        ["baseline", "classification"],
                        ["Use values between 0 and 1 when direct event flags are absent."],
                    )
                ],
                "allowedSourceClasses": ["public_dataset", "internal_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-012",
                "roleKey": "transit_schedule",
                "displayName": "Transit Schedule Context",
                "timing": "supporting",
                "purpose": "Provides optional static schedule or route context for later connector-backed delay reconstruction.",
                "requiredFields": [
                    field("transit_network", "string", ["classification"], ["Must map to the requested network."]),
                    field("service_date", "date", ["classification"], ["Must cover the target service date."]),
                    field("service_window", "categorical", ["classification"], ["Must cover the target service window."]),
                ],
                "optionalFields": [
                    field("route_id", "id", ["classification"], ["Use stable public route identifiers when available."])
                ],
                "allowedSourceClasses": ["official", "public_dataset"],
                "forecastTimeAllowed": True,
            },
            {
                "roleId": "sourcerole-013",
                "roleKey": "transit_delay_outcome",
                "displayName": "Transit Delay Outcome",
                "timing": "resolution",
                "purpose": "Provides post-window trip-stop delay observations for resolving the threshold event.",
                "requiredFields": [
                    field("service_date", "date", ["resolution"], ["Must match the forecast service date."]),
                    field("transit_network", "string", ["resolution"], ["Must match the forecast transit network."]),
                    field("service_window", "categorical", ["resolution"], ["Must match the forecast service window."]),
                    field("delay_seconds", "number", ["resolution", "scoring"], ["Use signed delay seconds from the outcome feed."]),
                ],
                "optionalFields": [
                    field("trip_id", "id", ["resolution"], ["Use public trip identifiers when available."]),
                    field("stop_id", "id", ["resolution"], ["Use public stop identifiers when available."]),
                ],
                "allowedSourceClasses": ["official", "public_dataset"],
                "forecastTimeAllowed": False,
            },
        ],
        "entityRequirements": [
            {
                "entityType": "geography",
                "canonicalField": "geography",
                "aliasPolicy": "user_provided_registry",
                "required": True,
            },
            {
                "entityType": "transit_network",
                "canonicalField": "transit_network",
                "aliasPolicy": "user_provided_registry",
                "required": True,
            },
        ],
        "resolutionPolicy": {
            "primarySourceRole": "transit_delay_outcome",
            "fallbackSourceRoles": [],
            "yesOutcomeDefinition": "Coverage checks pass and the late-observation ratio meets or exceeds the declared threshold.",
            "noOutcomeDefinition": "Coverage checks pass and the late-observation ratio is below the declared threshold.",
            "ambiguousIf": [
                "The outcome feed has too few eligible observations.",
                "Outcome rows cannot be mapped to the declared network, geography, service date, or service window.",
            ],
            "annulledIf": [
                "The transit service window was invalid before forecast close.",
                "The service was suspended before forecast close for an explicitly predeclared incomparable reason.",
            ],
            "resolutionTiming": "Resolve after the service window closes and outcome rows are collected.",
            "scoringRule": "brier",
        },
        "scoringPolicy": {
            "primaryScoringRule": "brier",
            "baselineComparisonRequired": True,
            "excludeAmbiguousOutcomes": True,
            "excludeAnnulledOutcomes": True,
            "reportingSlices": [
                "domain",
                "domain_setup",
                "horizon",
                "output_type",
                "resolution_source",
                "source_policy",
                "method_class",
                "coverage_period",
                "sample_size",
            ],
            "minimumResolvedForecastsForQualityClaim": 100,
        },
        "baselinePolicy": {
            "baselineRequired": True,
            "allowedBaselineMethods": ["historical_frequency", "conditioned_historical_frequency"],
            "minimumComparableRows": 30,
            "minimumPositiveOutcomes": 1,
            "fallbackWhenInsufficientData": "needs_more_data",
        },
        "methodPolicy": {
            "enabledMethodClasses": ["historical_baseline", "deterministic_statistical"],
            "selectionRule": (
                "Start with a smoothed historical delay-event baseline and allow only transparent local beta "
                "weather adjustments until comparable transit-delay benchmarks exist."
            ),
            "baselineComparisonRequired": True,
            "leakageCheckRequired": True,
            "methodDecisionRecordRequired": True,
        },
        "recalculationPolicy": {
            "supported": True,
            "triggerTypes": ["source_file_changed", "schedule", "agent_submitted_evidence", "manual"],
            "appendHistoryRequired": True,
            "postOutcomeEvidenceAllowed": False,
        },
        "localImplementation": {
            "forecastRunnable": True,
            "generatedForecastRecords": True,
            "cliForecastCommand": "python3 scripts/ope.py transit-delay-forecast",
            "readSurfaceAvailable": False,
            "implementationNotes": (
                "Local custom-file prototype emits schema-bound question, evidence, artifact, history, resolution, "
                "and scoring records, but it is not a live connector or calibrated production workflow."
            ),
        },
        "claimPolicy": {
            "allowedClaims": [
                "Local custom-file prototype can run a weather-transit-delay forecast from checked fixture inputs.",
                "Forecast, resolution, and scoring artifacts preserve baseline comparison and leakage boundaries.",
            ],
            "blockedClaims": [
                "Live transit connector claim",
                "Calibrated forecast quality claim",
                "Production readiness claim",
                "State-of-the-art performance claim",
                "Universal transit-agency coverage claim",
            ],
            "minimumResolvedForecastsForCalibration": 100,
            "qualityClaimAllowed": False,
            "benchmarkClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
            "universalDomainClaimAllowed": False,
        },
        "agentSetupGuidance": {
            "setupQuestions": [
                "Which public transit network, geography, service window, and date should be forecast?",
                "Which local weather forecast and historical delay files are approved for forecast-time use?",
                "Which trip-update or equivalent delay outcome file will resolve the threshold event after the window?",
            ],
            "requiredBeforeForecast": [
                "A weather forecast file retrieved before forecast close.",
                "A historical delay file with comparable delay-event outcomes.",
                "A declared late-seconds threshold, event-ratio threshold, and minimum observation count.",
            ],
            "safeFailureModes": [
                "Reject weather rows retrieved after forecast close.",
                "Block or mark ambiguous outcomes when delay coverage is too sparse.",
                "Do not include target-window delay rows in forecast-time provenance.",
            ],
        },
        "warnings": [
            "Local custom-file prototype is not a live connector runtime.",
            "Weather adjustment is transparent beta logic, not a calibrated causal claim.",
            "No calibration, production, or universal transit-agency claim is allowed for this setup.",
        ],
    }


def build_setups() -> dict[str, dict[str, Any]]:
    setups = {
        WEATHER_DOMAIN: build_weather_setup(),
        SEAPORT_DOMAIN: build_seaport_setup(),
        TRANSIT_DOMAIN: build_transit_setup(),
    }
    for domain, setup in setups.items():
        errors = validate_record(setup, SCHEMA)
        if errors:
            raise DomainSetupError(f"{domain} domain setup schema validation failed: {errors[0]}")
    return setups


def summary(setups: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(setups),
        "domainSetups": [
            {
                "domainSetupId": setup["domainSetupId"],
                "domain": setup["domain"],
                "displayName": setup["displayName"],
                "setupKind": setup["setupKind"],
                "maturityStatus": setup["maturityStatus"],
                "forecastRunnable": setup["localImplementation"]["forecastRunnable"],
                "generatedForecastRecords": setup["localImplementation"]["generatedForecastRecords"],
            }
            for setup in setups.values()
        ],
    }


def write_setups(setups: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for domain, setup in setups.items():
        SETUP_PATHS[domain].write_text(render_json(setup), encoding="utf-8")
    print("generated domain setup records")


def check_setups(setups: dict[str, dict[str, Any]]) -> None:
    errors: list[str] = []
    for domain, setup in setups.items():
        path = SETUP_PATHS[domain]
        if not path.exists():
            errors.append(f"missing domain setup output: {path}")
            continue
        if path.read_text(encoding="utf-8") != render_json(setup):
            errors.append(f"domain setup drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_domain_setups.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked domain setup records")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", choices=[WEATHER_DOMAIN, SEAPORT_DOMAIN, TRANSIT_DOMAIN], help="print one setup record")
    parser.add_argument("--check", action="store_true", help="check generated setup drift")
    parser.add_argument("--write", action="store_true", help="write generated setup records")
    args = parser.parse_args()
    try:
        setups = build_setups()
    except DomainSetupError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_setups(setups)
    elif args.check:
        check_setups(setups)
    elif args.setup:
        sys.stdout.write(render_json(setups[args.setup]))
    else:
        sys.stdout.write(render_json(summary(setups)))


if __name__ == "__main__":
    main()
