#!/usr/bin/env python3
"""Generate checked domain configuration records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "domain-configs"
SCHEMA = SPEC / "domain-config.schema.json"
GENERATED_AT = "2026-06-03T03:15:00Z"

WEATHER_TRANSIT_DOMAIN = "weather-transit-delays"
SEAPORT_DOMAIN = "seaport-berth-availability"

CONFIG_PATHS = {
    WEATHER_TRANSIT_DOMAIN: GENERATED / "weather-transit-delays-domain-config.generated.json",
    SEAPORT_DOMAIN: GENERATED / "seaport-berth-availability-domain-config.generated.json",
}


class DomainConfigError(Exception):
    pass


def role(
    role_id: str,
    role_key: str,
    timing: str,
    source_kinds: list[str],
    required_fields: list[str],
    *,
    forecast_time_allowed: bool,
) -> dict[str, Any]:
    return {
        "roleId": role_id,
        "roleKey": role_key,
        "timing": timing,
        "acceptedSourceKinds": source_kinds,
        "requiredFields": required_fields,
        "forecastTimeAllowed": forecast_time_allowed,
        "credentialValuesStored": False,
    }


def common_summary() -> dict[str, bool]:
    return {
        "questionTemplatesDefined": True,
        "horizonsDefined": True,
        "resolutionCriteriaDefined": True,
        "baselineMethodDefined": True,
        "acceptedSourceRolesDefined": True,
        "exclusionRulesDefined": True,
        "sampleThresholdsDefined": True,
        "claimBoundariesDefined": True,
        "normalChecksNonMutating": True,
        "credentialsExcluded": True,
    }


def common_execution_boundary() -> dict[str, bool]:
    return {
        "createsForecasts": False,
        "readsPrivateData": False,
        "storesCredentialValues": False,
        "liveFetchAllowed": False,
        "rawSqlAllowed": False,
    }


def build_weather_transit_config() -> dict[str, Any]:
    return {
        "domainConfigId": "domainconfig-001",
        "generatedAt": GENERATED_AT,
        "configStatus": "defined_readback",
        "domainId": "domainweathertransitdelays-001",
        "domainKey": WEATHER_TRANSIT_DOMAIN,
        "displayName": "Weather Transit Delay Domain Config",
        "version": "1.0",
        "questionTemplates": [
            {
                "templateId": "questiontemplate-115001",
                "templateKey": "transit_delay_threshold",
                "templateText": (
                    "Will {transit_network} in {geography} exceed the beta delay threshold "
                    "during {service_window} on {service_date}?"
                ),
                "outputType": "binary",
                "requiredParameters": ["transit_network", "geography", "service_window", "service_date"],
                "forecastClosePolicy": "Forecast must close before the service window starts.",
            }
        ],
        "horizons": [
            {
                "horizonId": "horizon-115001",
                "horizonKey": "same_day_service_window",
                "label": "Same-day service window",
                "startsAfter": "forecast close",
                "endsAfter": "declared service window end",
            }
        ],
        "resolutionCriteria": {
            "primaryOutcomeRole": "transit_delay_outcome",
            "resolutionTiming": "post_window",
            "yesCriteria": "Observed outcome rows show the beta delay threshold was exceeded in the service window.",
            "noCriteria": "Observed outcome rows show the beta delay threshold was not exceeded in the service window.",
            "ambiguousCriteria": [
                "Outcome rows conflict for the same network, geography, service date, and service window.",
                "Coverage is too low to classify threshold exceedance.",
            ],
            "annulledCriteria": [
                "The service window was canceled before forecast close.",
                "The configured network or geography was invalid before forecast close.",
            ],
        },
        "baselineMethod": {
            "methodId": "transitmethod-100",
            "methodKey": "historical_frequency",
            "methodClass": "historical_frequency",
            "minimumRows": 30,
            "minimumPositiveOutcomes": 1,
            "fallbackAllowed": True,
            "defaultUntilApprovedUpdate": True,
        },
        "acceptedSourceRoles": [
            role(
                "sourcerole-115001",
                "weather_forecast",
                "forecast_time",
                ["fixture", "local_file", "source_adapter_output", "api"],
                ["geography", "service_date", "retrieved_at", "precipitation_mm"],
                forecast_time_allowed=True,
            ),
            role(
                "sourcerole-115002",
                "historical_delay_baseline",
                "baseline",
                ["fixture", "local_file", "source_adapter_output", "database"],
                ["service_date", "service_window", "delay_threshold_exceeded"],
                forecast_time_allowed=True,
            ),
            role(
                "sourcerole-115003",
                "transit_delay_outcome",
                "resolution",
                ["fixture", "local_file", "source_adapter_output", "api"],
                ["service_date", "service_window", "delay_threshold_exceeded", "observed_after"],
                forecast_time_allowed=False,
            ),
        ],
        "exclusionRules": [
            {
                "ruleId": "exclusionrule-115001",
                "reasonCode": "ambiguous_outcome",
                "description": "Ambiguous outcomes are excluded from scoring and calibration.",
                "scoreTreatment": "exclude_from_scoring",
            },
            {
                "ruleId": "exclusionrule-115002",
                "reasonCode": "post_outcome_leakage",
                "description": "Sources retrieved after outcome availability cannot be used as forecast-time evidence.",
                "scoreTreatment": "manual_review_required",
            },
        ],
        "sampleThresholds": {
            "minimumComparableForecastsForCalibration": 100,
            "minimumComparableForecastsForQualityClaim": 100,
            "minimumBaselineRows": 30,
            "minimumPositiveOutcomes": 1,
        },
        "claimBoundaries": {
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
            "claimReviewRequired": True,
        },
        "executionBoundary": common_execution_boundary(),
        "summary": common_summary(),
        "warnings": [
            "Domain config defines allowed shape only; it does not bind concrete sources or create forecasts.",
            "The historical-frequency baseline remains default until approved method-update evidence exists.",
            "Outcome sources are resolution-only and must not enter forecast-time evidence.",
        ],
    }


def build_seaport_config() -> dict[str, Any]:
    return {
        "domainConfigId": "domainconfig-002",
        "generatedAt": GENERATED_AT,
        "configStatus": "candidate_readback",
        "domainId": "domainseaportberthavailability-001",
        "domainKey": SEAPORT_DOMAIN,
        "displayName": "Seaport Berth Availability Domain Config",
        "version": "0.1",
        "questionTemplates": [
            {
                "templateId": "questiontemplate-115002",
                "templateKey": "berth_availability_window",
                "templateText": (
                    "Will {port_area} have at least one qualifying berth available for {vessel_class} "
                    "during {arrival_window}?"
                ),
                "outputType": "binary",
                "requiredParameters": ["port_area", "vessel_class", "arrival_window"],
                "forecastClosePolicy": "Forecast must close before the arrival window starts.",
            }
        ],
        "horizons": [
            {
                "horizonId": "horizon-115002",
                "horizonKey": "arrival_window",
                "label": "Declared arrival window",
                "startsAfter": "forecast close",
                "endsAfter": "declared arrival window end",
            }
        ],
        "resolutionCriteria": {
            "primaryOutcomeRole": "berth_availability_outcome",
            "resolutionTiming": "post_horizon",
            "yesCriteria": "Confirmed operations outcome shows at least one qualifying berth was available.",
            "noCriteria": "Confirmed operations outcome shows no qualifying berth was available.",
            "ambiguousCriteria": [
                "Operations outcome conflicts with berth occupancy records.",
                "The arrival window changed after forecast close.",
            ],
            "annulledCriteria": [
                "The vessel call was canceled before forecast close.",
                "The configured port area or vessel class was invalid before forecast close.",
            ],
        },
        "baselineMethod": {
            "methodId": "seaportmethod-100",
            "methodKey": "historical_frequency",
            "methodClass": "historical_frequency",
            "minimumRows": 50,
            "minimumPositiveOutcomes": 1,
            "fallbackAllowed": True,
            "defaultUntilApprovedUpdate": True,
        },
        "acceptedSourceRoles": [
            role(
                "sourcerole-115004",
                "vessel_schedule",
                "forecast_time",
                ["local_file", "source_adapter_output", "api", "database"],
                ["vessel_id", "vessel_class", "arrival_window", "port_area"],
                forecast_time_allowed=True,
            ),
            role(
                "sourcerole-115005",
                "historical_berth_baseline",
                "baseline",
                ["local_file", "source_adapter_output", "database"],
                ["port_area", "arrival_window", "berth_available"],
                forecast_time_allowed=True,
            ),
            role(
                "sourcerole-115006",
                "berth_availability_outcome",
                "resolution",
                ["local_file", "source_adapter_output", "database"],
                ["port_area", "arrival_window", "berth_available", "observed_after"],
                forecast_time_allowed=False,
            ),
        ],
        "exclusionRules": [
            {
                "ruleId": "exclusionrule-115003",
                "reasonCode": "source_unconfirmed",
                "description": "Unconfirmed private source mappings block forecast execution.",
                "scoreTreatment": "manual_review_required",
            },
            {
                "ruleId": "exclusionrule-115004",
                "reasonCode": "non_comparable_window",
                "description": "Arrival windows outside the configured horizon are excluded from comparable scoring.",
                "scoreTreatment": "exclude_from_scoring",
            },
        ],
        "sampleThresholds": {
            "minimumComparableForecastsForCalibration": 100,
            "minimumComparableForecastsForQualityClaim": 100,
            "minimumBaselineRows": 50,
            "minimumPositiveOutcomes": 1,
        },
        "claimBoundaries": {
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
            "claimReviewRequired": True,
        },
        "executionBoundary": common_execution_boundary(),
        "summary": common_summary(),
        "warnings": [
            "Candidate domain config is not runnable until source bindings and mapping checks pass.",
            "Credential values must stay outside OPE records and be referenced only through approved adapters.",
            "Private database and API parsing remain behind caller-approved adapters.",
        ],
    }


def build_domain_configs() -> dict[str, dict[str, Any]]:
    configs = {
        WEATHER_TRANSIT_DOMAIN: build_weather_transit_config(),
        SEAPORT_DOMAIN: build_seaport_config(),
    }
    for config in configs.values():
        validate_domain_config(config)
    return configs


def validate_domain_config(config: dict[str, Any]) -> None:
    errors = validate_record(config, SCHEMA)
    if errors:
        raise DomainConfigError(f"domain config schema validation failed: {errors[0]}")
    if not config["questionTemplates"]:
        raise DomainConfigError("domain config must define question templates")
    if not config["horizons"]:
        raise DomainConfigError("domain config must define horizons")
    role_keys = {item["roleKey"] for item in config["acceptedSourceRoles"]}
    if config["resolutionCriteria"]["primaryOutcomeRole"] not in role_keys:
        raise DomainConfigError("resolution primary outcome role must be an accepted source role")
    if not any(item["timing"] == "forecast_time" for item in config["acceptedSourceRoles"]):
        raise DomainConfigError("domain config must include a forecast-time source role")
    if not any(item["timing"] == "resolution" for item in config["acceptedSourceRoles"]):
        raise DomainConfigError("domain config must include a resolution source role")
    for role_row in config["acceptedSourceRoles"]:
        if role_row["credentialValuesStored"]:
            raise DomainConfigError("domain config roles must not store credential values")
        if role_row["timing"] == "resolution" and role_row["forecastTimeAllowed"]:
            raise DomainConfigError("resolution roles must not be forecast-time evidence")
    baseline = config["baselineMethod"]
    if not baseline["fallbackAllowed"] or not baseline["defaultUntilApprovedUpdate"]:
        raise DomainConfigError("baseline method must remain the default fallback")
    thresholds = config["sampleThresholds"]
    if thresholds["minimumComparableForecastsForCalibration"] < thresholds["minimumComparableForecastsForQualityClaim"]:
        raise DomainConfigError("calibration threshold should not be below quality-claim threshold")
    if thresholds["minimumBaselineRows"] < baseline["minimumRows"]:
        raise DomainConfigError("sample threshold baseline rows should cover baseline minimum rows")
    claims = config["claimBoundaries"]
    if any(
        claims[key]
        for key in [
            "qualityClaimAllowed",
            "calibrationClaimAllowed",
            "stateOfTheArtClaimAllowed",
            "productionReadinessClaimAllowed",
        ]
    ):
        raise DomainConfigError("new domain configs must keep quality and readiness claims blocked")
    boundary = config["executionBoundary"]
    if any(boundary.values()):
        raise DomainConfigError("domain config readbacks must remain non-mutating and credential-free")
    if not all(config["summary"].values()):
        raise DomainConfigError("domain config summary flags must all be true")


def domain_config_summary(configs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "domainConfigSummaryId": "domainconfigsummary-001",
        "generatedAt": GENERATED_AT,
        "configCount": len(configs),
        "domains": [
            {
                "domainKey": config["domainKey"],
                "domainId": config["domainId"],
                "configStatus": config["configStatus"],
                "questionTemplateCount": len(config["questionTemplates"]),
                "sourceRoleCount": len(config["acceptedSourceRoles"]),
                "createsForecasts": config["executionBoundary"]["createsForecasts"],
                "credentialsExcluded": config["summary"]["credentialsExcluded"],
            }
            for config in configs.values()
        ],
        "warnings": [
            "Domain configs define setup shape only; source bindings are separate records.",
            "Normal domain config checks do not read private data, store credentials, or create forecasts.",
        ],
    }


def write_domain_configs(configs: dict[str, dict[str, Any]]) -> None:
    for domain, config in configs.items():
        write_generated(
            CONFIG_PATHS[domain],
            config,
            label=f"{domain} domain config",
            regen="python3 scripts/generate_domain_configs.py --write",
        )


def check_domain_configs(configs: dict[str, dict[str, Any]]) -> None:
    for domain, config in configs.items():
        check_generated(
            CONFIG_PATHS[domain],
            config,
            label=f"{domain} domain config",
            regen="python3 scripts/generate_domain_configs.py --write",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=sorted(CONFIG_PATHS), help="print one full domain config")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        configs = build_domain_configs()
        if args.write:
            write_domain_configs(configs)
        elif args.check:
            check_domain_configs(configs)
        elif args.domain:
            sys.stdout.write(render_json(configs[args.domain]))
        else:
            sys.stdout.write(render_json(domain_config_summary(configs)))
    except DomainConfigError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
