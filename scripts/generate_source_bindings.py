#!/usr/bin/env python3
"""Generate checked source binding setup records."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_domain_configs import (
    SEAPORT_DOMAIN,
    WEATHER_TRANSIT_DOMAIN,
    build_domain_configs,
)
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-bindings"
SCHEMA = SPEC / "source-binding.schema.json"
GENERATED_AT = "2026-06-03T03:45:00Z"

ACCEPTED = "accepted"
PARTIAL = "partial"
REJECTED = "rejected"
BLOCKED = "blocked"

CASE_PATHS = {
    ACCEPTED: GENERATED / "weather-transit-delays-accepted-source-binding.generated.json",
    PARTIAL: GENERATED / "seaport-berth-availability-partial-source-binding.generated.json",
    REJECTED: GENERATED / "weather-transit-delays-rejected-source-binding.generated.json",
    BLOCKED: GENERATED / "seaport-berth-availability-blocked-source-binding.generated.json",
}

CHECK_NAMES = {
    "mapping_confidence",
    "source_quality",
    "leakage",
    "freshness",
    "privacy",
    "outcome_availability",
}


class SourceBindingError(Exception):
    pass


def role_binding(
    index: int,
    role_key: str,
    source_kind: str,
    source_ref: str,
    adapter_ref: str,
    credential_ref: str,
    approval_status: str,
    binding_status: str,
    query_boundary: str,
    *,
    forecast_time_allowed: bool,
    sanitized_manifest: bool,
    raw_sql_allowed: bool = False,
    private_parsing_by_ope: bool = False,
) -> dict[str, Any]:
    return {
        "sourceRoleBindingId": f"sourcerolebinding-115{index:03d}",
        "roleKey": role_key,
        "sourceKind": source_kind,
        "sourceRef": source_ref,
        "adapterRef": adapter_ref,
        "credentialRef": credential_ref,
        "approvalStatus": approval_status,
        "bindingStatus": binding_status,
        "forecastTimeAllowed": forecast_time_allowed,
        "sanitizedManifestProvided": sanitized_manifest,
        "queryBoundary": query_boundary,
        "credentialValuesStored": False,
        "rawSqlAllowed": raw_sql_allowed,
        "privateParsingByOpe": private_parsing_by_ope,
    }


def pre_forecast_check(
    index: int,
    name: str,
    status: str,
    score: float,
    minimum: float,
    *,
    blocks: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "checkId": f"sourcebindingcheck-115{index:03d}",
        "checkName": name,
        "checkStatus": status,
        "score": score,
        "minimumScore": minimum,
        "blocksForecast": blocks,
        "message": message,
    }


def setup_operation(
    index: int,
    name: str,
    internal_operation: str,
    lifecycle_operation: str,
    binding_case: str,
) -> dict[str, Any]:
    return {
        "operationId": f"setupoperation-115{index:03d}",
        "operationName": name,
        "operationStatus": "available",
        "cliCommand": f"python3 scripts/ope.py source-bindings --case {binding_case}",
        "internalApiOperation": internal_operation,
        "lifecycleOperation": lifecycle_operation,
        "requiresReceipt": True,
        "requiresIdempotencyKey": True,
        "requiresLease": True,
        "writesRawConfig": False,
        "physicalDeleteAllowed": False,
    }


def setup_operations(binding_case: str) -> list[dict[str, Any]]:
    return [
        setup_operation(1, "source_binding.draft", "create_prediction", "prediction.config_create", binding_case),
        setup_operation(2, "source_binding.validate", "update_prediction", "prediction.config_update", binding_case),
        setup_operation(3, "source_binding.confirm", "update_prediction", "prediction.config_update", binding_case),
        setup_operation(4, "source_binding.update", "update_prediction", "prediction.config_update", binding_case),
        setup_operation(5, "source_binding.archive", "archive_record", "prediction.config_archive", binding_case),
        setup_operation(6, "source_binding.redact", "redact_record", "prediction.config_redact", binding_case),
    ]


def credential_policy(*, reference_required: bool, raw_detected: bool = False) -> dict[str, Any]:
    return {
        "credentialValuesStored": False,
        "credentialReferencesAllowed": True,
        "credentialReferenceRequired": reference_required,
        "secretScanningRequired": True,
        "rawCredentialValueDetected": raw_detected,
    }


def configuration_input_boundary() -> dict[str, bool]:
    return {
        "sanitizedManifestRequired": True,
        "sanitizedMappingRequired": True,
        "sanitizedProvenanceRequired": True,
        "queryBoundaryRequired": True,
        "arbitraryPrivateApiParsingByOpe": False,
        "arbitraryDatabaseParsingByOpe": False,
        "callerApprovalRequired": True,
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "createsForecasts": False,
        "writesSourceData": False,
        "readsPrivateData": False,
        "storesCredentialValues": False,
        "executesApiCalls": False,
        "executesDatabaseQueries": False,
        "rawSqlAllowed": False,
    }


def summary(
    *,
    approved_kinds: bool,
    safety_complete: bool,
    roles_bound: bool,
    forecast_allowed: bool,
) -> dict[str, bool]:
    return {
        "sourceBindingRecordsDefined": True,
        "approvedSourceKindsCovered": approved_kinds,
        "setupOperationsDefined": True,
        "safetyChecksComplete": safety_complete,
        "allRequiredRolesBound": roles_bound,
        "forecastGenerationAllowed": forecast_allowed,
        "credentialsExcluded": True,
        "privateParsingBehindAdapters": True,
        "normalChecksNonMutating": True,
    }


def build_accepted_weather_binding() -> dict[str, Any]:
    return {
        "sourceBindingId": "sourcebinding-115001",
        "generatedAt": GENERATED_AT,
        "bindingCase": ACCEPTED,
        "bindingStatus": "accepted_ready",
        "domainConfigId": "domainconfig-001",
        "domainKey": WEATHER_TRANSIT_DOMAIN,
        "predictionId": "prediction-001",
        "sourceBindingMode": "sanitized_manifest",
        "credentialPolicy": credential_policy(reference_required=False),
        "sourceRoleBindings": [
            role_binding(
                1,
                "weather_forecast",
                "api",
                "source-openmeteo-forecast-manifest-001",
                "adapter-openmeteo-public-001",
                "none",
                "approved",
                "confirmed",
                "bounded_public_weather_forecast_query",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                2,
                "historical_delay_baseline",
                "local_file",
                "spec/fixtures/transit/historical-delay-baseline.csv",
                "adapter-local-csv-001",
                "none",
                "approved",
                "confirmed",
                "approved_fixture_file_under_spec_fixtures",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                3,
                "transit_delay_outcome",
                "source_adapter_output",
                "spec/fixtures/generated/transit-api-connector/hsl-tripupdates-source-output.generated.json",
                "adapter-hsl-transit-output-001",
                "none",
                "approved",
                "confirmed",
                "resolution_only_adapter_output_after_service_window",
                forecast_time_allowed=False,
                sanitized_manifest=True,
            ),
        ],
        "preForecastChecks": [
            pre_forecast_check(1, "mapping_confidence", "pass", 0.98, 0.8, blocks=False, message="All source fields map to configured transit source roles."),
            pre_forecast_check(2, "source_quality", "pass", 0.94, 0.75, blocks=False, message="Source freshness, coverage, and provenance meet the domain policy."),
            pre_forecast_check(3, "leakage", "pass", 1.0, 1.0, blocks=False, message="Resolution-only transit outcome is excluded from forecast-time evidence."),
            pre_forecast_check(4, "freshness", "pass", 0.92, 0.7, blocks=False, message="Forecast-time weather source is inside the configured retrieval window."),
            pre_forecast_check(5, "privacy", "pass", 1.0, 1.0, blocks=False, message="No credential values or private records are present in OPE records."),
            pre_forecast_check(6, "outcome_availability", "pass", 0.9, 0.7, blocks=False, message="A post-window outcome source is bound for later resolution only."),
        ],
        "setupOperations": setup_operations(ACCEPTED),
        "configurationInputBoundary": configuration_input_boundary(),
        "executionBoundary": execution_boundary(),
        "nextAction": "forecast_generation_allowed",
        "summary": summary(approved_kinds=True, safety_complete=True, roles_bound=True, forecast_allowed=True),
        "warnings": [
            "Accepted binding permits forecast generation only through lifecycle preflight and operation receipts.",
            "Outcome adapter output remains resolution-only and is not forecast-time evidence.",
        ],
    }


def build_partial_seaport_binding() -> dict[str, Any]:
    return {
        "sourceBindingId": "sourcebinding-115002",
        "generatedAt": GENERATED_AT,
        "bindingCase": PARTIAL,
        "bindingStatus": "partial_needs_confirmation",
        "domainConfigId": "domainconfig-002",
        "domainKey": SEAPORT_DOMAIN,
        "predictionId": "prediction-002",
        "sourceBindingMode": "database_adapter_manifest",
        "credentialPolicy": credential_policy(reference_required=True),
        "sourceRoleBindings": [
            role_binding(
                4,
                "vessel_schedule",
                "database",
                "manifest-seaport-vessel-schedule-001",
                "adapter-seaport-database-sanitized-001",
                "credentialref-seaport-readonly-001",
                "approved",
                "confirmed",
                "approved_readonly_query_manifest_without_raw_sql",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                5,
                "historical_berth_baseline",
                "source_adapter_output",
                "adapter-output-seaport-berth-history-draft-001",
                "adapter-seaport-history-sanitized-001",
                "credentialref-seaport-readonly-001",
                "needs_confirmation",
                "draft",
                "candidate_history_window_requires_owner_confirmation",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                6,
                "berth_availability_outcome",
                "database",
                "missing-resolution-outcome-manifest",
                "adapter-seaport-outcome-sanitized-001",
                "credentialref-seaport-readonly-001",
                "needs_confirmation",
                "missing",
                "post_horizon_outcome_query_boundary_not_confirmed",
                forecast_time_allowed=False,
                sanitized_manifest=False,
            ),
        ],
        "preForecastChecks": [
            pre_forecast_check(7, "mapping_confidence", "warn", 0.78, 0.8, blocks=True, message="Baseline mapping is close but still needs owner confirmation."),
            pre_forecast_check(8, "source_quality", "warn", 0.73, 0.75, blocks=True, message="Historical berth coverage is not yet strong enough for forecast execution."),
            pre_forecast_check(9, "leakage", "pass", 1.0, 1.0, blocks=False, message="Outcome binding is not forecast-time evidence."),
            pre_forecast_check(10, "freshness", "pass", 0.85, 0.7, blocks=False, message="Vessel schedule freshness is within the configured retrieval window."),
            pre_forecast_check(11, "privacy", "pass", 1.0, 1.0, blocks=False, message="Only credential references and sanitized manifests are present."),
            pre_forecast_check(12, "outcome_availability", "fail", 0.2, 0.7, blocks=True, message="Resolution outcome binding is missing and must be confirmed first."),
        ],
        "setupOperations": setup_operations(PARTIAL),
        "configurationInputBoundary": configuration_input_boundary(),
        "executionBoundary": execution_boundary(),
        "nextAction": "collect_missing_source_binding",
        "summary": summary(approved_kinds=True, safety_complete=False, roles_bound=False, forecast_allowed=False),
        "warnings": [
            "Partial binding blocks forecast generation until missing source roles and mappings are confirmed.",
            "The database source is represented by an adapter manifest and credential reference, not raw SQL or credential values.",
        ],
    }


def build_rejected_weather_binding() -> dict[str, Any]:
    return {
        "sourceBindingId": "sourcebinding-115003",
        "generatedAt": GENERATED_AT,
        "bindingCase": REJECTED,
        "bindingStatus": "rejected_replace_source",
        "domainConfigId": "domainconfig-001",
        "domainKey": WEATHER_TRANSIT_DOMAIN,
        "predictionId": "prediction-003",
        "sourceBindingMode": "sanitized_manifest",
        "credentialPolicy": credential_policy(reference_required=False),
        "sourceRoleBindings": [
            role_binding(
                7,
                "weather_forecast",
                "local_file",
                "drafts/weather-summary-without-timestamps.csv",
                "adapter-local-csv-001",
                "none",
                "rejected",
                "rejected",
                "draft_file_missing_retrieval_and_geography_fields",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                8,
                "historical_delay_baseline",
                "local_file",
                "drafts/delay-baseline-too-small.csv",
                "adapter-local-csv-001",
                "none",
                "rejected",
                "rejected",
                "draft_file_below_minimum_baseline_rows",
                forecast_time_allowed=True,
                sanitized_manifest=True,
            ),
            role_binding(
                9,
                "transit_delay_outcome",
                "source_adapter_output",
                "adapter-output-transit-outcome-unscoped-001",
                "adapter-hsl-transit-output-001",
                "none",
                "rejected",
                "rejected",
                "outcome_adapter_output_missing_service_window_scope",
                forecast_time_allowed=False,
                sanitized_manifest=True,
            ),
        ],
        "preForecastChecks": [
            pre_forecast_check(13, "mapping_confidence", "fail", 0.32, 0.8, blocks=True, message="Source fields do not map reliably to the transit domain roles."),
            pre_forecast_check(14, "source_quality", "fail", 0.41, 0.75, blocks=True, message="Baseline file has too few comparable rows for the declared method."),
            pre_forecast_check(15, "leakage", "pass", 1.0, 1.0, blocks=False, message="No post-outcome evidence is admitted as forecast-time evidence."),
            pre_forecast_check(16, "freshness", "fail", 0.35, 0.7, blocks=True, message="Forecast-time source lacks retrieval timestamp evidence."),
            pre_forecast_check(17, "privacy", "pass", 1.0, 1.0, blocks=False, message="No private data or credential values were present."),
            pre_forecast_check(18, "outcome_availability", "fail", 0.4, 0.7, blocks=True, message="Outcome source cannot be scoped to the configured service window."),
        ],
        "setupOperations": setup_operations(REJECTED),
        "configurationInputBoundary": configuration_input_boundary(),
        "executionBoundary": execution_boundary(),
        "nextAction": "replace_source_binding",
        "summary": summary(approved_kinds=False, safety_complete=False, roles_bound=False, forecast_allowed=False),
        "warnings": [
            "Rejected binding is non-sensitive but does not meet mapping, quality, freshness, or outcome requirements.",
            "Agents should replace the source binding instead of forcing forecast generation.",
        ],
    }


def build_blocked_seaport_binding() -> dict[str, Any]:
    return {
        "sourceBindingId": "sourcebinding-115004",
        "generatedAt": GENERATED_AT,
        "bindingCase": BLOCKED,
        "bindingStatus": "blocked_safety_violation",
        "domainConfigId": "domainconfig-002",
        "domainKey": SEAPORT_DOMAIN,
        "predictionId": "prediction-004",
        "sourceBindingMode": "adapter_output",
        "credentialPolicy": credential_policy(reference_required=True, raw_detected=True),
        "sourceRoleBindings": [
            role_binding(
                10,
                "vessel_schedule",
                "api",
                "redacted-api-request-with-raw-token-detected",
                "adapter-seaport-api-unapproved-001",
                "redacted-credential-value-detected",
                "blocked",
                "blocked",
                "unapproved_private_api_request",
                forecast_time_allowed=True,
                sanitized_manifest=False,
                private_parsing_by_ope=True,
            ),
            role_binding(
                11,
                "historical_berth_baseline",
                "database",
                "redacted-raw-sql-query-detected",
                "adapter-seaport-database-unapproved-001",
                "redacted-credential-value-detected",
                "blocked",
                "blocked",
                "raw_sql_query_detected_and_rejected",
                forecast_time_allowed=True,
                sanitized_manifest=False,
                raw_sql_allowed=True,
                private_parsing_by_ope=True,
            ),
            role_binding(
                12,
                "berth_availability_outcome",
                "database",
                "post-outcome-rows-present-in-forecast-evidence",
                "adapter-seaport-outcome-unapproved-001",
                "redacted-credential-value-detected",
                "blocked",
                "blocked",
                "post_outcome_data_present_before_forecast_close",
                forecast_time_allowed=False,
                sanitized_manifest=False,
                raw_sql_allowed=True,
                private_parsing_by_ope=True,
            ),
        ],
        "preForecastChecks": [
            pre_forecast_check(19, "mapping_confidence", "block", 0.1, 0.8, blocks=True, message="Blocked source cannot be safely mapped while raw private inputs are present."),
            pre_forecast_check(20, "source_quality", "block", 0.1, 0.75, blocks=True, message="Source quality cannot be assessed from unsafe raw private data."),
            pre_forecast_check(21, "leakage", "block", 0.0, 1.0, blocks=True, message="Post-outcome rows were detected in forecast-time context."),
            pre_forecast_check(22, "freshness", "block", 0.0, 0.7, blocks=True, message="Freshness cannot be trusted for unapproved raw requests."),
            pre_forecast_check(23, "privacy", "block", 0.0, 1.0, blocks=True, message="Raw credential-like content was detected and redacted before storage."),
            pre_forecast_check(24, "outcome_availability", "block", 0.0, 0.7, blocks=True, message="Outcome source is unsafe and cannot be used for resolution."),
        ],
        "setupOperations": setup_operations(BLOCKED),
        "configurationInputBoundary": configuration_input_boundary(),
        "executionBoundary": execution_boundary(),
        "nextAction": "stop_unsafe_source_binding",
        "summary": summary(approved_kinds=False, safety_complete=False, roles_bound=False, forecast_allowed=False),
        "warnings": [
            "Blocked binding stores only redaction markers, never raw credential values.",
            "Private API and database parsing must stay behind caller-approved adapters that emit sanitized manifests.",
        ],
    }


def build_source_bindings() -> dict[str, dict[str, Any]]:
    # Keep role-key validation tied to current domain configs so examples cannot
    # drift into hidden plugin behavior.
    build_domain_configs()
    bindings = {
        ACCEPTED: build_accepted_weather_binding(),
        PARTIAL: build_partial_seaport_binding(),
        REJECTED: build_rejected_weather_binding(),
        BLOCKED: build_blocked_seaport_binding(),
    }
    for binding in bindings.values():
        validate_source_binding(binding)
    return bindings


def validate_source_binding(binding: dict[str, Any]) -> None:
    errors = validate_record(binding, SCHEMA)
    if errors:
        raise SourceBindingError(f"source binding schema validation failed: {errors[0]}")
    role_rows = binding["sourceRoleBindings"]
    if any(row["credentialValuesStored"] for row in role_rows):
        raise SourceBindingError("source bindings must not store credential values")
    if binding["credentialPolicy"]["credentialValuesStored"]:
        raise SourceBindingError("credential policy must block stored credential values")
    if binding["executionBoundary"]["createsForecasts"]:
        raise SourceBindingError("source binding readbacks must not create forecasts")
    if binding["executionBoundary"]["readsPrivateData"]:
        raise SourceBindingError("source binding checks must not read private data")
    if binding["configurationInputBoundary"]["arbitraryPrivateApiParsingByOpe"]:
        raise SourceBindingError("private API parsing must stay behind adapters")
    if binding["configurationInputBoundary"]["arbitraryDatabaseParsingByOpe"]:
        raise SourceBindingError("database parsing must stay behind adapters")
    check_names = {item["checkName"] for item in binding["preForecastChecks"]}
    if check_names != CHECK_NAMES:
        raise SourceBindingError("source binding must include all pre-forecast safety checks")
    operations = {item["operationName"]: item for item in binding["setupOperations"]}
    if set(operations) != {
        "source_binding.draft",
        "source_binding.validate",
        "source_binding.confirm",
        "source_binding.update",
        "source_binding.archive",
        "source_binding.redact",
    }:
        raise SourceBindingError("source binding setup operation coverage drifted")
    for item in operations.values():
        if item["writesRawConfig"] or item["physicalDeleteAllowed"]:
            raise SourceBindingError("setup operations must not write raw configs or physically delete")
        if not item["requiresReceipt"] or not item["requiresIdempotencyKey"] or not item["requiresLease"]:
            raise SourceBindingError("setup operations must be receipt-backed, idempotent, and lease-aware")
    forecast_allowed = binding["summary"]["forecastGenerationAllowed"]
    blocking_checks = [item for item in binding["preForecastChecks"] if item["blocksForecast"]]
    all_roles_confirmed = all(item["bindingStatus"] == "confirmed" for item in role_rows)
    if forecast_allowed and (blocking_checks or not all_roles_confirmed):
        raise SourceBindingError("forecast generation cannot be allowed with blockers or unconfirmed roles")
    if not forecast_allowed and binding["nextAction"] == "forecast_generation_allowed":
        raise SourceBindingError("blocked cases must not recommend forecast generation")
    if binding["bindingCase"] == BLOCKED:
        if not binding["credentialPolicy"]["rawCredentialValueDetected"]:
            raise SourceBindingError("blocked case should detect unsafe raw credential-like input")
        if not all(item["blocksForecast"] for item in binding["preForecastChecks"]):
            raise SourceBindingError("blocked case should block every pre-forecast check")


def source_binding_summary(bindings: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source_kinds = sorted(
        {
            role["sourceKind"]
            for binding in bindings.values()
            for role in binding["sourceRoleBindings"]
            if role["approvalStatus"] == "approved"
        }
    )
    return {
        "sourceBindingSummaryId": "sourcebindingsummary-115001",
        "generatedAt": GENERATED_AT,
        "bindingCaseCount": len(bindings),
        "approvedSourceKinds": source_kinds,
        "cases": [
            {
                "bindingCase": binding["bindingCase"],
                "bindingStatus": binding["bindingStatus"],
                "domainKey": binding["domainKey"],
                "predictionId": binding["predictionId"],
                "nextAction": binding["nextAction"],
                "forecastGenerationAllowed": binding["summary"]["forecastGenerationAllowed"],
                "blockingCheckCount": sum(
                    1 for item in binding["preForecastChecks"] if item["blocksForecast"]
                ),
                "credentialValuesStored": binding["credentialPolicy"]["credentialValuesStored"],
            }
            for binding in bindings.values()
        ],
        "setupOperations": [
            {
                "operationName": item["operationName"],
                "internalApiOperation": item["internalApiOperation"],
                "lifecycleOperation": item["lifecycleOperation"],
            }
            for item in next(iter(bindings.values()))["setupOperations"]
        ],
        "executionBoundary": execution_boundary(),
        "warnings": [
            "Source bindings are setup readbacks and do not execute private API calls or database queries.",
            "Only accepted bindings may proceed to forecast generation, and only through lifecycle operation preflight.",
        ],
    }


def write_source_bindings(bindings: dict[str, dict[str, Any]]) -> None:
    for case, binding in bindings.items():
        write_generated(
            CASE_PATHS[case],
            binding,
            label=f"{case} source binding",
            regen="python3 scripts/generate_source_bindings.py --write",
        )


def check_source_bindings(bindings: dict[str, dict[str, Any]]) -> None:
    for case, binding in bindings.items():
        check_generated(
            CASE_PATHS[case],
            binding,
            label=f"{case} source binding",
            regen="python3 scripts/generate_source_bindings.py --write",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASE_PATHS), help="print one full source binding case")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        bindings = build_source_bindings()
        if args.write:
            write_source_bindings(bindings)
        elif args.check:
            check_source_bindings(bindings)
        elif args.case:
            sys.stdout.write(render_json(bindings[args.case]))
        else:
            sys.stdout.write(render_json(source_binding_summary(bindings)))
    except SourceBindingError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
