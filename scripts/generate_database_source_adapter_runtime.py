#!/usr/bin/env python3
"""Generate a checked approved database source-adapter runtime readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_source_bindings import PARTIAL, build_source_bindings
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "database-source-adapter-runtime"
OUTPUT_PATH = GENERATED / "ope-database-source-adapter-runtime.generated.json"
SCHEMA = SPEC / "database-source-adapter-runtime.schema.json"
GENERATED_AT = "2026-06-04T22:10:00Z"

CASE_ORDER = [
    "approved_fixture",
    "missing_approval",
    "missing_credential_reference",
    "unsafe_query_boundary",
    "oversized_result",
    "stale_source",
    "leakage_risk",
    "missing_outcome_source",
    "insufficient_comparable_history",
]


class DatabaseSourceAdapterRuntimeError(Exception):
    pass


def runtime_request(
    *,
    source_binding_id: str,
    source_role: str,
    query_ref: str,
    credential_ref: str,
    approval_status: str,
    row_limit: int = 250,
    time_limit_seconds: int = 15,
    freshness_window_hours: int = 12,
) -> dict[str, Any]:
    return {
        "sourceBindingId": source_binding_id,
        "sourceRole": source_role,
        "approvedQueryManifestRef": query_ref,
        "credentialRef": credential_ref,
        "rowLimit": row_limit,
        "timeLimitSeconds": time_limit_seconds,
        "freshnessWindowHours": freshness_window_hours,
        "leakageWindow": {
            "forecastCloseTime": "2026-06-12T08:00:00Z",
            "resolutionEvidenceAfter": "2026-06-12T18:00:00Z",
        },
        "callerApprovalStatus": approval_status,
    }


def approved_sanitized_output() -> dict[str, Any]:
    return {
        "sourceManifest": {
            "sourceManifestId": "sourcemanifest-1501",
            "domainSetupId": "domainsetup-002",
            "domain": "seaport-berth-availability",
            "sourceRole": "vessel_schedule",
            "sourceKind": "private_database",
            "rowCount": 42,
            "rawRowsIncluded": False,
        },
        "fieldMapping": {
            "fieldMappingId": "fieldmapping-1501",
            "sourceManifestId": "sourcemanifest-1501",
            "mappingStatus": "confirmed",
            "mappedFieldCount": 8,
            "agentInferredFieldsRequireConfirmation": False,
        },
        "provenanceSummary": {
            "adapterRunId": "databaseadapterrun-1501",
            "contentHashesStored": True,
            "credentialValuesIncluded": False,
            "rawRowsIncluded": False,
            "stackTraceIncluded": False,
            "diagnosticsSanitized": True,
        },
        "sourceQualitySignals": {
            "freshnessStatus": "pass",
            "coverageStatus": "pass",
            "sourceQualityScore": 0.86,
            "minimumSourceQualityScore": 0.75,
        },
        "mappingConfidenceSignals": {
            "mappingStatus": "confirmed",
            "mappingConfidence": 0.91,
            "minimumMappingConfidence": 0.8,
        },
        "outcomeAvailabilityStatus": {
            "status": "available_resolution_only",
            "forecastTimeOutcomeEvidenceAllowed": False,
            "resolutionSourceBound": True,
        },
        "queryBoundarySummary": {
            "queryManifestRef": "querymanifest-seaport-vessel-schedule-001",
            "readOnly": True,
            "rawSqlIncluded": False,
            "rawSqlWithSecretsIncluded": False,
            "unapprovedSchemaScan": False,
            "rowLimitApplied": True,
            "timeLimitApplied": True,
        },
    }


def blocked_output(reason: str) -> dict[str, Any]:
    return {
        "sourceManifest": {
            "sourceManifestId": "none",
            "domainSetupId": "domainsetup-002",
            "domain": "seaport-berth-availability",
            "sourceRole": "vessel_schedule",
            "sourceKind": "private_database",
            "rowCount": 0,
            "rawRowsIncluded": False,
        },
        "fieldMapping": {
            "fieldMappingId": "none",
            "sourceManifestId": "none",
            "mappingStatus": "not_created",
            "mappedFieldCount": 0,
            "agentInferredFieldsRequireConfirmation": False,
        },
        "provenanceSummary": {
            "adapterRunId": "none",
            "contentHashesStored": False,
            "credentialValuesIncluded": False,
            "rawRowsIncluded": False,
            "stackTraceIncluded": False,
            "diagnosticsSanitized": True,
        },
        "sourceQualitySignals": {
            "freshnessStatus": "not_evaluated",
            "coverageStatus": "not_evaluated",
            "sourceQualityScore": 0.0,
            "minimumSourceQualityScore": 0.75,
        },
        "mappingConfidenceSignals": {
            "mappingStatus": "not_evaluated",
            "mappingConfidence": 0.0,
            "minimumMappingConfidence": 0.8,
        },
        "outcomeAvailabilityStatus": {
            "status": reason,
            "forecastTimeOutcomeEvidenceAllowed": False,
            "resolutionSourceBound": False,
        },
        "queryBoundarySummary": {
            "queryManifestRef": "blocked",
            "readOnly": True,
            "rawSqlIncluded": False,
            "rawSqlWithSecretsIncluded": False,
            "unapprovedSchemaScan": False,
            "rowLimitApplied": True,
            "timeLimitApplied": True,
        },
    }


def runtime_case(
    *,
    case_name: str,
    status: str,
    next_action: str,
    request: dict[str, Any],
    can_enter_intake: bool,
    output: dict[str, Any],
    source_adapter_output_compatible: bool = False,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": status,
        "runtimeRequest": request,
        "sanitizedAdapterOutput": output,
        "sourceAdapterOutputCompatible": source_adapter_output_compatible,
        "canEnterSourceAdapterIntake": can_enter_intake,
        "databaseSpecificForecastPathCreated": False,
        "forecastArtifactsCreated": False,
        "rawPrivateRowsStored": False,
        "credentialValuesStored": False,
        "sanitizedDiagnosticsOnly": True,
        "nextAction": next_action,
    }


def runtime_cases(source_binding_id: str) -> list[dict[str, Any]]:
    approved_request = runtime_request(
        source_binding_id=source_binding_id,
        source_role="vessel_schedule",
        query_ref="querymanifest-seaport-vessel-schedule-001",
        credential_ref="credentialref-seaport-readonly-001",
        approval_status="approved",
    )
    cases = [
        runtime_case(
            case_name="approved_fixture",
            status="adapter_output_ready",
            next_action="run_source_adapter_intake",
            request=approved_request,
            can_enter_intake=True,
            output=approved_sanitized_output(),
            source_adapter_output_compatible=True,
        )
    ]
    blocked_specs = [
        ("missing_approval", "blocked_missing_approval", "confirm_caller_approval", "not_requested", "missing_approval"),
        (
            "missing_credential_reference",
            "blocked_missing_credential_reference",
            "provide_credential_reference",
            "approved",
            "missing_credential_reference",
        ),
        ("unsafe_query_boundary", "blocked_unsafe_query_boundary", "replace_query_manifest", "approved", "unsafe_query_boundary"),
        ("oversized_result", "blocked_oversized_result", "reduce_row_or_time_limits", "approved", "oversized_result"),
        ("stale_source", "blocked_stale_source", "refresh_source_within_policy", "approved", "stale_source"),
        ("leakage_risk", "blocked_leakage_risk", "separate_resolution_evidence", "approved", "leakage_risk"),
        (
            "missing_outcome_source",
            "blocked_missing_outcome_source",
            "bind_resolution_only_outcome",
            "approved",
            "missing_outcome_source",
        ),
        (
            "insufficient_comparable_history",
            "blocked_insufficient_comparable_history",
            "collect_more_history",
            "approved",
            "insufficient_comparable_history",
        ),
    ]
    for case_name, status, next_action, approval_status, reason in blocked_specs:
        credential_ref = "none" if case_name == "missing_credential_reference" else "credentialref-seaport-readonly-001"
        query_ref = "unsafe-raw-sql-detected" if case_name == "unsafe_query_boundary" else "querymanifest-seaport-vessel-schedule-001"
        cases.append(
            runtime_case(
                case_name=case_name,
                status=status,
                next_action=next_action,
                request=runtime_request(
                    source_binding_id=source_binding_id,
                    source_role="vessel_schedule",
                    query_ref=query_ref,
                    credential_ref=credential_ref,
                    approval_status=approval_status,
                    row_limit=10000 if case_name == "oversized_result" else 250,
                    freshness_window_hours=72 if case_name == "stale_source" else 12,
                ),
                can_enter_intake=False,
                output=blocked_output(reason),
            )
        )
    return cases


def routing() -> dict[str, Any]:
    return {
        "acceptedOutputRoutesToSourceAdapterIntake": True,
        "routesToSourceIntake": True,
        "routesToSourceHandoff": True,
        "routesToSetupBenchmark": True,
        "routesToSetupMethodDecision": True,
        "routesToForecastExecutionGate": True,
        "databaseSpecificForecastPathCreated": False,
        "commands": [
            "python3 scripts/ope.py database-source-adapter-runtime --case approved_fixture",
            "python3 scripts/ope.py source-adapter-intake --check",
            "python3 scripts/ope.py source-intake --check",
            "python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
            "python3 scripts/ope.py setup-benchmark --check",
            "python3 scripts/ope.py setup-method --check",
        ],
    }


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py database-source-adapter-runtime",
            "operationName": "database_source_adapter_runtime",
            "mutatesState": False,
            "requiresCredentialValues": False,
        },
        {
            "readbackSurface": "internal_api",
            "command": "python3 scripts/ope.py internal-api --operation database_source_adapter_status",
            "operationName": "database_source_adapter_status",
            "mutatesState": False,
            "requiresCredentialValues": False,
        },
        {
            "readbackSurface": "agent_call",
            "command": "python3 scripts/ope.py agent-call --operation database_source_adapter_runtime_status",
            "operationName": "database_source_adapter_runtime_status",
            "mutatesState": False,
            "requiresCredentialValues": False,
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "productionDatabaseConnectionOpened": False,
        "normalChecksConnectToDatabase": False,
        "credentialValuesStored": False,
        "rawSqlWithSecretsAccepted": False,
        "rawPrivateRowsStored": False,
        "stackTracesExposed": False,
        "unapprovedSchemaScansAllowed": False,
        "arbitraryDatabaseAccessAllowed": False,
        "forecastArtifactsCreated": False,
        "scoringRecordsCreated": False,
        "hostedRuntimeRequired": False,
    }


def build_database_source_adapter_runtime() -> dict[str, Any]:
    bindings = build_source_bindings()
    database_binding = bindings[PARTIAL]
    source_binding_id = database_binding["sourceBindingId"]
    cases = runtime_cases(source_binding_id)
    return {
        "databaseSourceAdapterRuntimeId": "databasesourceadapterruntime-001",
        "generatedAt": GENERATED_AT,
        "runtimeStatus": "approved_database_source_adapter_runtime_checked",
        "runtimeScope": "bounded_caller_approved_database_adapter",
        "normalChecksOffline": True,
        "sourceBindingId": source_binding_id,
        "domainKey": database_binding["domainKey"],
        "runtimeCases": cases,
        "routing": routing(),
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "caseCount": len(cases),
            "blockedCaseCount": len(cases) - 1,
            "approvedExecutionPathCount": 1,
            "sourceAdapterOutputCompatibleCount": sum(1 for item in cases if item["sourceAdapterOutputCompatible"]),
            "forecastArtifactsCreated": False,
            "credentialsStored": False,
        },
        "warnings": [
            "This runtime readback uses a controlled local fixture and sanitized adapter output, not a production database connection.",
            "Credential values, raw SQL with secrets, raw private rows, stack traces, and unapproved schema scans remain blocked.",
            "Accepted database adapter output still routes through source-adapter intake, source intake, source handoff, setup benchmark, method decision, and forecast execution gates.",
        ],
    }


def validate_database_source_adapter_runtime(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise DatabaseSourceAdapterRuntimeError("database source-adapter runtime failed schema validation")
    if [item["caseName"] for item in record["runtimeCases"]] != CASE_ORDER:
        raise DatabaseSourceAdapterRuntimeError("database source-adapter case order drifted")
    for key, value in record["executionBoundary"].items():
        if value is not False:
            raise DatabaseSourceAdapterRuntimeError(f"execution boundary {key} should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "cases":
        return record["runtimeCases"]
    if view == "approved":
        return record["runtimeCases"][0]
    if view == "blocked":
        return record["runtimeCases"][1:]
    if view == "routing":
        return record["routing"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise DatabaseSourceAdapterRuntimeError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated database source-adapter runtime fixture")
    parser.add_argument("--check", action="store_true", help="check generated database source-adapter runtime fixture")
    parser.add_argument("--case", choices=CASE_ORDER, help="print one runtime case")
    parser.add_argument(
        "--view",
        choices=["full", "cases", "approved", "blocked", "routing", "readbacks", "boundary", "summary"],
        default="full",
        help="emit a focused runtime view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_database_source_adapter_runtime()
    validate_database_source_adapter_runtime(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="database source-adapter runtime",
            regen="python3 scripts/generate_database_source_adapter_runtime.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="database source-adapter runtime",
            regen="python3 scripts/generate_database_source_adapter_runtime.py --write",
        )
        return
    if args.case:
        print(render_json(next(item for item in record["runtimeCases"] if item["caseName"] == args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
