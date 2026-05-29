#!/usr/bin/env python3
"""Generate or check source quality and mapping confidence readbacks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_source_manifest import build_case as build_source_builder_case
from generate_source_adapter_intake import build_records as build_source_adapter_intake_records
from generate_source_intake import build_reports as build_source_intake_reports
from ope_schema import SPEC, validate_record
from select_setup_method import build_decisions as build_setup_method_decisions
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-quality-mapping-confidence"
OUTPUT_PATH = GENERATED / "weather-logistics-source-quality-mapping-confidence.generated.json"
SCHEMA = SPEC / "source-quality-mapping-confidence.schema.json"
GENERATED_AT = "2026-06-10T08:35:00Z"
COMPACT_MAX_BYTES = 12000

CASE_ORDER = [
    "builder_local_draft",
    "source_intake_accepted",
    "source_intake_partial",
    "source_intake_needs_confirmation",
    "adapter_insufficient_data",
    "source_intake_rejected",
    "adapter_unsafe",
]
DIMENSION_KEYS = [
    "freshness",
    "coverage",
    "roleFit",
    "entityScope",
    "leakageRisk",
    "missingness",
    "outcomeAvailability",
    "mappingConfidence",
]


class SourceQualityMappingConfidenceError(Exception):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def dimension(status: str, reason_codes: list[str], summary: str) -> dict[str, Any]:
    return {
        "status": status,
        "reasonCodes": sorted(set(reason_codes)),
        "summary": summary,
    }


def statuses_for_check(report: dict[str, Any], check_name: str) -> tuple[list[str], list[str]]:
    statuses = []
    reasons = []
    for source in report["sourceDecisions"]:
        check = source["checks"][check_name]
        statuses.append(check["status"])
        reasons.extend(check["reasonCodes"])
    return statuses, reasons


def aggregate_check(
    report: dict[str, Any],
    check_name: str,
    passed_summary: str,
    needs_summary: str,
    failed_summary: str,
) -> dict[str, Any]:
    statuses, reasons = statuses_for_check(report, check_name)
    applicable = [status for status in statuses if status != "not_applicable"]
    if any(status == "failed" for status in applicable):
        return dimension("failed", reasons, failed_summary)
    if any(status == "needs_confirmation" for status in applicable):
        return dimension("needs_confirmation", reasons, needs_summary)
    if applicable and all(status == "passed" for status in applicable):
        return dimension("passed", reasons, passed_summary)
    if applicable:
        return dimension("partial", reasons, needs_summary)
    return dimension("not_applicable", reasons or ["no_applicable_sources"], needs_summary)


def role_summary_from_report(report: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "presentRoles": sorted(
            item["sourceRole"]
            for item in report["roleCoverage"]
            if item["status"] == "present"
        ),
        "partialRoles": sorted(
            item["sourceRole"]
            for item in report["roleCoverage"]
            if item["status"] == "partial"
        ),
        "missingRequiredRoles": sorted(
            item["sourceRole"]
            for item in report["roleCoverage"]
            if item["requiredForForecast"] and item["status"] == "missing"
        ),
        "rejectedRoles": sorted(
            item["sourceRole"]
            for item in report["roleCoverage"]
            if item["status"] == "rejected"
        ),
    }


def role_summary_from_manifest(manifest: dict[str, Any] | None) -> dict[str, list[str]]:
    if manifest is None:
        return {
            "presentRoles": [],
            "partialRoles": [],
            "missingRequiredRoles": [],
            "rejectedRoles": [],
        }
    return {
        "presentRoles": sorted(source["sourceRole"] for source in manifest["sources"]),
        "partialRoles": [],
        "missingRequiredRoles": [],
        "rejectedRoles": [],
    }


def mapping_summary_from_report(report: dict[str, Any]) -> dict[str, Any]:
    decisions = report["mappingDecisions"]
    accepted = sum(1 for item in decisions if item["decision"] == "accepted")
    proposed = sum(1 for item in decisions if item["decision"] == "proposed")
    rejected = sum(1 for item in decisions if item["decision"] == "rejected")
    total = accepted + proposed + rejected
    score = 0.0 if total == 0 else round((accepted + proposed * 0.7) / total, 2)
    return {
        "acceptedMappings": accepted,
        "proposedMappings": proposed,
        "rejectedMappings": rejected,
        "averageConfidence": score,
    }


def mapping_summary_from_field_mapping(field_mapping: dict[str, Any] | None) -> dict[str, Any]:
    if field_mapping is None:
        return {
            "acceptedMappings": 0,
            "proposedMappings": 0,
            "rejectedMappings": 0,
            "averageConfidence": 0.0,
        }
    items = field_mapping["mappings"] + field_mapping["aliasMappings"]
    accepted = sum(1 for item in items if item["mappingStatus"] == "confirmed")
    proposed = sum(1 for item in items if item["mappingStatus"] == "proposed")
    rejected = sum(1 for item in items if item["mappingStatus"] == "rejected")
    confidences = [
        item.get("confidence", 1.0 if item["mappingStatus"] == "confirmed" else 0.7)
        for item in items
    ]
    score = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    return {
        "acceptedMappings": accepted,
        "proposedMappings": proposed,
        "rejectedMappings": rejected,
        "averageConfidence": score,
    }


def mapping_dimension(summary: dict[str, Any]) -> dict[str, Any]:
    if summary["rejectedMappings"]:
        return dimension(
            "failed",
            ["mapping_rejected"],
            "One or more mappings were rejected and the source should be replaced or corrected.",
        )
    if summary["proposedMappings"]:
        return dimension(
            "needs_confirmation",
            ["mapping_requires_confirmation"],
            "Agent-inferred or draft mappings must be confirmed before method gates.",
        )
    if summary["acceptedMappings"]:
        return dimension(
            "passed",
            ["mappings_confirmed"],
            "Mappings are confirmed enough for the checked intake or method-decision surface.",
        )
    return dimension("not_applicable", ["no_mappings_available"], "No mapping record is available for this row.")


def role_fit_dimension(summary: dict[str, list[str]], can_produce_forecast: bool) -> dict[str, Any]:
    if summary["rejectedRoles"]:
        return dimension(
            "failed",
            ["source_role_rejected"],
            "One or more source roles are rejected and cannot proceed to method gates.",
        )
    if summary["partialRoles"]:
        return dimension(
            "needs_confirmation",
            ["source_role_needs_confirmation"],
            "Source roles are present but need mapping or alias confirmation.",
        )
    if summary["missingRequiredRoles"]:
        return dimension(
            "partial" if can_produce_forecast else "failed",
            ["missing_required_source_role"],
            "A required role is missing; only methods whose role needs are still met can proceed.",
        )
    if summary["presentRoles"]:
        return dimension("passed", ["source_roles_present"], "Source roles fit the declared domain setup.")
    return dimension("failed", ["source_roles_missing"], "No usable source roles are bound.")


def outcome_availability_dimension(summary: dict[str, list[str]]) -> dict[str, Any]:
    if "declared_operations_outcome" in summary["rejectedRoles"]:
        return dimension(
            "failed",
            ["outcome_source_rejected"],
            "The declared outcome source is rejected or unsafe.",
        )
    if "declared_operations_outcome" in summary["partialRoles"]:
        return dimension(
            "needs_confirmation",
            ["outcome_mapping_needs_confirmation"],
            "The outcome role is present but its mappings need confirmation.",
        )
    if "declared_operations_outcome" in summary["presentRoles"]:
        return dimension(
            "passed",
            ["outcome_source_declared"],
            "A declared resolution/outcome source is present for later scoring.",
        )
    return dimension(
        "partial",
        ["outcome_source_missing"],
        "Forecast setup may continue only if resolution is declared or supplied later.",
    )


def missingness_dimension(report: dict[str, Any], role_summary: dict[str, list[str]]) -> dict[str, Any]:
    required_fields = aggregate_check(
        report,
        "requiredFields",
        "Required mapped fields are present.",
        "Required fields or mappings need confirmation.",
        "Required fields are missing or rejected.",
    )
    sample_size = aggregate_check(
        report,
        "sampleSize",
        "Comparable baseline sample coverage is sufficient for checked setup gates.",
        "Sample-size coverage is only partially applicable.",
        "Comparable rows or positive outcomes are insufficient.",
    )
    if required_fields["status"] == "failed" or sample_size["status"] == "failed":
        return dimension(
            "failed",
            required_fields["reasonCodes"] + sample_size["reasonCodes"],
            "Missing fields, rows, or outcomes block method selection.",
        )
    if required_fields["status"] == "needs_confirmation":
        return dimension(
            "needs_confirmation",
            required_fields["reasonCodes"],
            "Missingness cannot be finalized until proposed mappings are confirmed.",
        )
    if role_summary["missingRequiredRoles"]:
        return dimension(
            "partial",
            ["missing_required_source_role"],
            "Some role-level evidence is missing even though a baseline path may remain usable.",
        )
    return dimension(
        "passed",
        required_fields["reasonCodes"] + sample_size["reasonCodes"],
        "Required fields and comparable samples are sufficient for the allowed setup path.",
    )


def coverage_dimension(report: dict[str, Any], role_summary: dict[str, list[str]]) -> dict[str, Any]:
    sample = aggregate_check(
        report,
        "sampleSize",
        "Comparable historical coverage is sufficient for checked setup decisions.",
        "Coverage is partial for the current setup path.",
        "Historical coverage is too thin for method selection.",
    )
    if sample["status"] == "failed":
        return sample
    if role_summary["missingRequiredRoles"]:
        return dimension(
            "partial",
            ["missing_required_source_role"],
            "Coverage is enough for baseline-only use but not for all configured methods.",
        )
    return dimension(sample["status"], sample["reasonCodes"], sample["summary"])


def dimensions_from_report(report: dict[str, Any], role_summary: dict[str, list[str]], mapping_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "freshness": aggregate_check(
            report,
            "sourceFreshness",
            "Forecast-time sources are fresh enough for the declared close time.",
            "Freshness depends on confirmation or a narrower path.",
            "At least one forecast-time source is stale or retrieved after close.",
        ),
        "coverage": coverage_dimension(report, role_summary),
        "roleFit": role_fit_dimension(role_summary, report["canProduceForecast"]),
        "entityScope": aggregate_check(
            report,
            "entityMatch",
            "Source entity scope matches the requested setup.",
            "Entity aliases or mappings need confirmation.",
            "Source entity scope does not match the requested setup.",
        ),
        "leakageRisk": aggregate_check(
            report,
            "leakageRisk",
            "No post-outcome or post-close evidence is present in forecast-time sources.",
            "Leakage risk cannot be finalized until mappings are confirmed.",
            "Leakage or post-close source evidence blocks this source path.",
        ),
        "missingness": missingness_dimension(report, role_summary),
        "outcomeAvailability": outcome_availability_dimension(role_summary),
        "mappingConfidence": mapping_dimension(mapping_summary),
    }


def builder_dimensions(build: dict[str, Any], manifest: dict[str, Any] | None, mapping_summary: dict[str, Any]) -> dict[str, Any]:
    confirmation_required = build["confirmationRequired"]
    mapping_status = "needs_confirmation" if confirmation_required else "passed"
    return {
        "freshness": dimension(
            "passed",
            ["builder_inputs_available_before_close"],
            "Local builder inspected caller-approved files with forecast-time availability metadata.",
        ),
        "coverage": dimension(
            "passed" if manifest else "failed",
            ["builder_draft_sources_inspected"] if manifest else ["builder_draft_rejected"],
            "Draft sources have enough inspected metadata for source intake." if manifest else "Rejected builder inputs cannot enter intake.",
        ),
        "roleFit": dimension(
            "passed" if manifest else "failed",
            ["builder_source_roles_declared"] if manifest else ["builder_source_roles_rejected"],
            "Draft source roles are declared before source intake." if manifest else "No usable draft roles are available.",
        ),
        "entityScope": dimension(
            mapping_status,
            ["entity_alias_requires_confirmation"] if confirmation_required else ["entity_scope_declared"],
            "Entity aliases require caller confirmation." if confirmation_required else "Entity scope is declared.",
        ),
        "leakageRisk": dimension(
            "passed" if manifest else "failed",
            ["no_post_outcome_leakage_indicator"] if manifest else ["builder_leakage_or_privacy_rejection"],
            "Builder inputs did not show post-outcome leakage indicators." if manifest else "Builder rejection blocks leakage-safe use.",
        ),
        "missingness": dimension(
            mapping_status,
            ["draft_mapping_requires_confirmation"] if confirmation_required else ["draft_fields_mapped"],
            "Field completeness is draft-only until mappings are confirmed." if confirmation_required else "Draft fields are mapped.",
        ),
        "outcomeAvailability": dimension(
            mapping_status,
            ["outcome_role_draft_present"],
            "A draft outcome role is present but cannot be treated as confirmed until intake.",
        ),
        "mappingConfidence": mapping_dimension(mapping_summary),
    }


def source_intake_case_row(
    index: int,
    case: str,
    report: dict[str, Any],
    decision: dict[str, Any],
    quality_status: str,
    next_action: str,
    agent_summary: str,
) -> dict[str, Any]:
    roles = role_summary_from_report(report)
    mappings = mapping_summary_from_report(report)
    can_proceed = decision["decisionStatus"] in {"method_selected", "baseline_selected"}
    return {
        "caseId": f"sourcequalitycase-{index:03d}",
        "case": case,
        "inputSurface": "source_intake",
        "boundRecordIds": {
            "sourceManifestBuildId": None,
            "sourceAdapterOutputId": None,
            "sourceAdapterIntakeCaseId": None,
            "sourceIntakeReportId": report["sourceIntakeReportId"],
            "setupMethodDecisionId": decision["setupMethodDecisionId"],
            "sourceManifestId": report["sourceManifestId"],
            "fieldMappingId": report["fieldMappingId"],
        },
        "qualityStatus": quality_status,
        "recommendedNextAction": next_action,
        "dimensions": dimensions_from_report(report, roles, mappings),
        "roleSummary": roles,
        "mappingSummary": mappings,
        "forecastImpact": {
            "canEnterSourceIntake": True,
            "canProceedToMethodGate": can_proceed,
            "canProduceForecast": report["canProduceForecast"],
            "selectedMethodClass": decision["selectedMethodClass"],
            "forecastArtifactsCreated": False,
            "qualityClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
        },
        "agentSummary": agent_summary,
    }


def adapter_case_row(
    index: int,
    case: str,
    adapter_row: dict[str, Any],
    output: dict[str, Any],
    report: dict[str, Any] | None,
    decision: dict[str, Any] | None,
    quality_status: str,
    next_action: str,
    agent_summary: str,
) -> dict[str, Any]:
    if report is None:
        roles = role_summary_from_manifest(output.get("sourceManifest"))
        mappings = mapping_summary_from_field_mapping(output.get("fieldMapping"))
        dimensions = {
            key: dimension(
                "blocked",
                ["unsafe_adapter_output"],
                "Unsafe adapter output is blocked before source intake and quality scoring.",
            )
            for key in DIMENSION_KEYS
        }
        can_proceed = False
        can_produce = False
        source_intake_report_id = None
        setup_method_decision_id = None
    else:
        roles = role_summary_from_report(report)
        mappings = mapping_summary_from_report(report)
        dimensions = dimensions_from_report(report, roles, mappings)
        can_proceed = decision is not None and decision["decisionStatus"] in {"method_selected", "baseline_selected"}
        can_produce = report["canProduceForecast"]
        source_intake_report_id = report["sourceIntakeReportId"]
        setup_method_decision_id = decision["setupMethodDecisionId"] if decision is not None else None

    return {
        "caseId": f"sourcequalitycase-{index:03d}",
        "case": case,
        "inputSurface": "source_adapter_intake",
        "boundRecordIds": {
            "sourceManifestBuildId": None,
            "sourceAdapterOutputId": output["sourceAdapterOutputId"],
            "sourceAdapterIntakeCaseId": adapter_row["caseId"],
            "sourceIntakeReportId": source_intake_report_id,
            "setupMethodDecisionId": setup_method_decision_id,
            "sourceManifestId": output["sourceManifest"]["sourceManifestId"],
            "fieldMappingId": output["fieldMapping"]["fieldMappingId"],
        },
        "qualityStatus": quality_status,
        "recommendedNextAction": next_action,
        "dimensions": dimensions,
        "roleSummary": roles,
        "mappingSummary": mappings,
        "forecastImpact": {
            "canEnterSourceIntake": adapter_row["intakeRoute"]["canEnterSourceIntake"],
            "canProceedToMethodGate": can_proceed,
            "canProduceForecast": can_produce,
            "selectedMethodClass": adapter_row["methodGateSummary"]["selectedMethodClass"],
            "forecastArtifactsCreated": False,
            "qualityClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
        },
        "agentSummary": agent_summary,
    }


def builder_case_row(index: int, build: dict[str, Any], manifest: dict[str, Any] | None, field_mapping: dict[str, Any] | None) -> dict[str, Any]:
    roles = role_summary_from_manifest(manifest)
    mappings = mapping_summary_from_field_mapping(field_mapping)
    return {
        "caseId": f"sourcequalitycase-{index:03d}",
        "case": "builder_local_draft",
        "inputSurface": "source_builder",
        "boundRecordIds": {
            "sourceManifestBuildId": build["sourceManifestBuildId"],
            "sourceAdapterOutputId": None,
            "sourceAdapterIntakeCaseId": None,
            "sourceIntakeReportId": None,
            "setupMethodDecisionId": None,
            "sourceManifestId": build["draftArtifacts"]["sourceManifestId"],
            "fieldMappingId": build["draftArtifacts"]["fieldMappingId"],
        },
        "qualityStatus": "needs_mapping_confirmation" if build["confirmationRequired"] else "forecast_usable",
        "recommendedNextAction": "confirm_mappings" if build["confirmationRequired"] else "proceed_to_method_gate",
        "dimensions": builder_dimensions(build, manifest, mappings),
        "roleSummary": roles,
        "mappingSummary": mappings,
        "forecastImpact": {
            "canEnterSourceIntake": build["canEnterSourceIntake"],
            "canProceedToMethodGate": False,
            "canProduceForecast": False,
            "selectedMethodClass": None,
            "forecastArtifactsCreated": False,
            "qualityClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
        },
        "agentSummary": "Local builder drafts can enter source intake only after caller confirmation of proposed mappings.",
    }


def surface_bindings(
    builder_build: dict[str, Any],
    adapter_matrix: dict[str, Any],
    reports: dict[str, dict[str, Any]],
    decisions: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "surface": "source_builder",
            "command": "python3 scripts/ope.py source-builder --case local_draft",
            "recordId": builder_build["sourceManifestBuildId"],
            "status": builder_build["buildStatus"],
            "artifactPath": "spec/fixtures/generated/source-builder/weather-logistics-local-draft-source-manifest-build.generated.json",
        },
        {
            "surface": "source_adapter_intake",
            "command": "python3 scripts/ope.py source-adapter-intake",
            "recordId": adapter_matrix["sourceAdapterIntakeId"],
            "status": "checked_adapter_intake_matrix",
            "artifactPath": "spec/fixtures/generated/source-adapter-intake/weather-logistics-source-adapter-intake.generated.json",
        },
        {
            "surface": "source_intake_report",
            "command": "python3 scripts/ope.py source-intake",
            "recordId": reports["accepted"]["sourceIntakeReportId"],
            "status": "four_checked_source_intake_reports",
            "artifactPath": "spec/fixtures/generated/source-intake/",
        },
        {
            "surface": "setup_method_decision",
            "command": "python3 scripts/ope.py setup-method",
            "recordId": decisions["accepted"]["setupMethodDecisionId"],
            "status": "four_checked_setup_method_decisions",
            "artifactPath": "spec/fixtures/generated/setup-method-decision/",
        },
    ]


def count_status(rows: list[dict[str, Any]], status: str) -> int:
    return sum(1 for row in rows if row["qualityStatus"] == status)


def compact_payload(model: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceQualityMappingConfidenceId": model["sourceQualityMappingConfidenceId"],
        "domain": model["domain"],
        "qualityMode": model["qualityMode"],
        "summary": model["summary"],
        "caseRows": [
            {
                "case": row["case"],
                "inputSurface": row["inputSurface"],
                "qualityStatus": row["qualityStatus"],
                "recommendedNextAction": row["recommendedNextAction"],
                "agentSummary": row["agentSummary"],
            }
            for row in model["caseRows"]
        ],
    }


def build_model() -> dict[str, Any]:
    builder_build, builder_manifest, builder_mapping = build_source_builder_case("local_draft")
    reports = build_source_intake_reports()
    decisions = build_setup_method_decisions()
    adapter_outputs, adapter_reports, _adapter_gates, adapter_decisions, adapter_matrix = build_source_adapter_intake_records()
    adapter_rows = {row["case"]: row for row in adapter_matrix["intakeCases"]}

    rows = [
        builder_case_row(1, builder_build, builder_manifest, builder_mapping),
        source_intake_case_row(
            2,
            "source_intake_accepted",
            reports["accepted"],
            decisions["accepted"],
            "forecast_usable",
            "proceed_to_method_gate",
            "Confirmed source roles and mappings can proceed to setup method gates.",
        ),
        source_intake_case_row(
            3,
            "source_intake_partial",
            reports["accepted_partial"],
            decisions["accepted_partial"],
            "baseline_only_usable",
            "proceed_to_method_gate",
            "The baseline path remains usable, but missing weather evidence blocks stronger configured methods.",
        ),
        source_intake_case_row(
            4,
            "source_intake_needs_confirmation",
            reports["needs_confirmation"],
            decisions["needs_confirmation"],
            "needs_mapping_confirmation",
            "confirm_mappings",
            "Agent-inferred field and alias mappings need caller confirmation before method gates.",
        ),
        adapter_case_row(
            5,
            "adapter_insufficient_data",
            adapter_rows["insufficient_data"],
            adapter_outputs["insufficient_data"],
            adapter_reports["insufficient_data"],
            adapter_decisions["insufficient_data"],
            "needs_more_data",
            "collect_more_data",
            "Adapter output is sanitized, but comparable rows and positive outcomes are too sparse.",
        ),
        source_intake_case_row(
            6,
            "source_intake_rejected",
            reports["rejected"],
            decisions["rejected"],
            "replace_source",
            "replace_source",
            "Rejected source intake has leakage, freshness, privacy, mapping, or sample-size failures.",
        ),
        adapter_case_row(
            7,
            "adapter_unsafe",
            adapter_rows["unsafe_blocked"],
            adapter_outputs["unsafe"],
            adapter_reports["unsafe"],
            adapter_decisions["unsafe"],
            "stop_unsafe_connector",
            "stop_unsafe_connector",
            "Unsafe adapter output is blocked before source intake because credential or raw-row boundaries were crossed.",
        ),
    ]
    model = {
        "sourceQualityMappingConfidenceId": "sourcequalitymappingconfidence-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "qualityMode": "checked_source_quality_mapping_confidence",
        "surfaceBindings": surface_bindings(builder_build, adapter_matrix, reports, decisions),
        "caseRows": rows,
        "summary": {
            "caseCount": len(rows),
            "forecastUsableCount": count_status(rows, "forecast_usable"),
            "baselineOnlyCount": count_status(rows, "baseline_only_usable"),
            "needsMappingConfirmationCount": count_status(rows, "needs_mapping_confirmation"),
            "needsMoreDataCount": count_status(rows, "needs_more_data"),
            "replaceSourceCount": count_status(rows, "replace_source"),
            "stopUnsafeConnectorCount": count_status(rows, "stop_unsafe_connector"),
            "qualityClaimAllowed": False,
            "productionReadinessClaimAllowed": False,
        },
        "compactReadback": {
            "maxBytes": COMPACT_MAX_BYTES,
            "measuredBytes": 0,
            "fitsBudget": False,
            "includesRawRows": False,
            "includesRawPrompts": False,
            "includesCredentials": False,
            "includedCaseCount": len(rows),
        },
        "executionBoundary": {
            "readOnly": True,
            "executesSourceBuilder": False,
            "executesSourceAdapter": False,
            "readsPrivateRows": False,
            "storesRawRows": False,
            "storesCredentials": False,
            "fetchesLiveData": False,
            "createsSourceManifest": False,
            "createsForecastArtifacts": False,
            "createsResolutionRecords": False,
            "createsScoringRecords": False,
            "allowsQualityClaims": False,
            "allowsProductionReadinessClaims": False,
            "normalChecksDeterministicOffline": True,
        },
        "warnings": [
            "Source quality is a read model over checked local records, not a private source runtime.",
            "Quality and mapping confidence cannot create forecast, resolution, or scoring artifacts.",
            "Proceeding still requires source intake, setup benchmark gates, setup method decisions, and explicit forecast execution.",
            "No raw rows, prompts, credentials, or live fetches are included in normal checks.",
        ],
    }
    compact_bytes = len(render_json(compact_payload(model)).encode("utf-8"))
    model["compactReadback"]["measuredBytes"] = compact_bytes
    model["compactReadback"]["fitsBudget"] = compact_bytes <= COMPACT_MAX_BYTES
    validate_model(model)
    return model


def validate_model(model: dict[str, Any]) -> None:
    errors = validate_record(model, SCHEMA)
    if errors:
        raise SourceQualityMappingConfidenceError(f"source quality mapping confidence schema validation failed: {errors[0]}")
    if [row["case"] for row in model["caseRows"]] != CASE_ORDER:
        raise SourceQualityMappingConfidenceError("source quality case coverage drifted")
    for row in model["caseRows"]:
        if set(row["dimensions"]) != set(DIMENSION_KEYS):
            raise SourceQualityMappingConfidenceError(f"{row['case']} dimension coverage drifted")
        impact = row["forecastImpact"]
        if impact["forecastArtifactsCreated"] or impact["qualityClaimAllowed"] or impact["productionReadinessClaimAllowed"]:
            raise SourceQualityMappingConfidenceError(f"{row['case']} must not create artifacts or claims")

    rows_by_case = {row["case"]: row for row in model["caseRows"]}
    accepted = rows_by_case["source_intake_accepted"]
    if accepted["qualityStatus"] != "forecast_usable" or accepted["recommendedNextAction"] != "proceed_to_method_gate":
        raise SourceQualityMappingConfidenceError("accepted source-intake row should proceed to method gate")
    if accepted["dimensions"]["mappingConfidence"]["status"] != "passed":
        raise SourceQualityMappingConfidenceError("accepted source-intake row should have confirmed mappings")

    builder = rows_by_case["builder_local_draft"]
    if builder["qualityStatus"] != "needs_mapping_confirmation" or builder["forecastImpact"]["canProduceForecast"]:
        raise SourceQualityMappingConfidenceError("builder drafts should require confirmation and not allow forecasts")

    needs = rows_by_case["source_intake_needs_confirmation"]
    if needs["recommendedNextAction"] != "confirm_mappings" or needs["dimensions"]["mappingConfidence"]["status"] != "needs_confirmation":
        raise SourceQualityMappingConfidenceError("needs-confirmation row should ask for mapping confirmation")

    insufficient = rows_by_case["adapter_insufficient_data"]
    if insufficient["recommendedNextAction"] != "collect_more_data" or insufficient["dimensions"]["coverage"]["status"] != "failed":
        raise SourceQualityMappingConfidenceError("insufficient-data adapter row should collect more data")

    rejected = rows_by_case["source_intake_rejected"]
    if rejected["recommendedNextAction"] != "replace_source" or rejected["dimensions"]["leakageRisk"]["status"] != "failed":
        raise SourceQualityMappingConfidenceError("rejected source-intake row should replace source after leakage failure")

    unsafe = rows_by_case["adapter_unsafe"]
    if unsafe["recommendedNextAction"] != "stop_unsafe_connector":
        raise SourceQualityMappingConfidenceError("unsafe adapter row should stop unsafe connector output")
    if any(dimension["status"] != "blocked" for dimension in unsafe["dimensions"].values()):
        raise SourceQualityMappingConfidenceError("unsafe adapter row should keep all dimensions blocked")

    summary = model["summary"]
    expected_count = len(model["caseRows"])
    if summary["caseCount"] != expected_count:
        raise SourceQualityMappingConfidenceError("source quality summary count drifted")
    if summary["qualityClaimAllowed"] or summary["productionReadinessClaimAllowed"]:
        raise SourceQualityMappingConfidenceError("source quality must not allow quality or production-readiness claims")

    compact = model["compactReadback"]
    if not compact["fitsBudget"] or compact["measuredBytes"] > compact["maxBytes"]:
        raise SourceQualityMappingConfidenceError("compact source quality readback exceeds budget")
    if compact["includesRawRows"] or compact["includesRawPrompts"] or compact["includesCredentials"]:
        raise SourceQualityMappingConfidenceError("compact source quality readback must stay sanitized")

    boundary = model["executionBoundary"]
    if boundary["readOnly"] is not True or boundary["normalChecksDeterministicOffline"] is not True:
        raise SourceQualityMappingConfidenceError("source quality boundary should be read-only and offline")
    for key, value in boundary.items():
        if key in {"readOnly", "normalChecksDeterministicOffline"}:
            continue
        if value is not False:
            raise SourceQualityMappingConfidenceError(f"source quality boundary {key} should be false")


def summary(model: dict[str, Any]) -> dict[str, Any]:
    return compact_payload(model)


def write_model(model: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(model), encoding="utf-8")
    print("generated source quality mapping confidence")


def check_model(model: dict[str, Any]) -> None:
    expected = render_json(model)
    if not OUTPUT_PATH.exists():
        print(f"missing source quality mapping confidence: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_source_quality_mapping_confidence.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"source quality mapping confidence drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_source_quality_mapping_confidence.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source quality mapping confidence")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source quality case row")
    parser.add_argument("--check", action="store_true", help="check generated source quality drift")
    parser.add_argument("--write", action="store_true", help="write generated source quality readback")
    args = parser.parse_args()
    try:
        model = build_model()
    except SourceQualityMappingConfidenceError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_model(model)
    elif args.check:
        check_model(model)
    elif args.case:
        row = next(item for item in model["caseRows"] if item["case"] == args.case)
        sys.stdout.write(render_json(row))
    else:
        sys.stdout.write(render_json(summary(model)))


if __name__ == "__main__":
    main()
