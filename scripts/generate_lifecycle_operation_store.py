#!/usr/bin/env python3
"""Generate a checked lifecycle operation store readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from lifecycle_operation_store_runtime import run_runtime_scenarios, sqlite_schema_plan
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "lifecycle-operation-store"
OUTPUT_PATH = GENERATED / "ope-lifecycle-operation-store.generated.json"
SCHEMA = SPEC / "lifecycle-operation.schema.json"
GENERATED_AT = "2026-06-03T00:30:00Z"
SCENARIO_NAMES = [
    "create",
    "retry-idempotent",
    "lease-conflict",
    "archive",
    "redaction",
    "method-rollback",
    "recovery",
]


class LifecycleOperationStoreError(Exception):
    pass


def claim_boundary() -> dict[str, bool]:
    return {
        "createsQualityClaim": False,
        "allowsPostOutcomeRewrite": False,
        "allowsSilentDelete": False,
        "allowsRawCrud": False,
    }


def storage_backends() -> list[dict[str, Any]]:
    return [
        {
            "backendId": "storagebackend-001",
            "backendName": "ignored_json_compat",
            "implementationStatus": "current_compatibility",
            "role": "Preserve checked fixtures and existing ignored .ope/live JSON state while the database backend is planned.",
            "writesRuntimeState": True,
            "supportsTransactions": False,
            "supportsLeases": False,
            "supportsJsonRecords": True,
            "hostedRuntimeRequired": False,
            "notes": "Useful for local compatibility, but weak for concurrent multi-agent execution.",
        },
        {
            "backendId": "storagebackend-002",
            "backendName": "local_sqlite",
            "implementationStatus": "implemented_local_runtime",
            "role": "First database-backed local runtime for durable operations, idempotency, leases, and queryable read models.",
            "writesRuntimeState": True,
            "supportsTransactions": True,
            "supportsLeases": True,
            "supportsJsonRecords": True,
            "hostedRuntimeRequired": False,
            "notes": "SQLite runs through a checked local adapter and ephemeral scenario fixture without hosted infrastructure.",
        },
        {
            "backendId": "storagebackend-003",
            "backendName": "postgres_design",
            "implementationStatus": "planned_production_design",
            "role": "Production-compatible schema target for hosted or shared deployments after readiness gates unblock them.",
            "writesRuntimeState": True,
            "supportsTransactions": True,
            "supportsLeases": True,
            "supportsJsonRecords": True,
            "hostedRuntimeRequired": True,
            "notes": "Postgres remains a design target here, not an implemented hosted service claim.",
        },
    ]


def operation(
    name: str,
    operation_class: str,
    phase: str,
    *,
    lease: bool,
    writes_records: bool,
    write_mode: str,
    delete_replacement: str = "not_delete",
) -> dict[str, Any]:
    return {
        "operationName": name,
        "operationClass": operation_class,
        "lifecyclePhase": phase,
        "requiresPreflight": True,
        "requiresIdempotencyKey": True,
        "requiresLease": lease,
        "writesImmutableRecords": writes_records,
        "updatesReadModels": True,
        "deleteReplacement": delete_replacement,
        "allowedWriteMode": write_mode,
        "retrySafety": "lease_and_idempotent_required" if lease else "idempotent_required",
        "claimBoundary": claim_boundary(),
    }


def operation_catalog() -> list[dict[str, Any]]:
    return [
        operation("campaign.create_run", "create", "planning", lease=True, writes_records=True, write_mode="insert_once"),
        operation("forecast.create", "create", "forecasting", lease=True, writes_records=True, write_mode="insert_once"),
        operation("forecast.recalculate", "append_update", "recalculation", lease=False, writes_records=True, write_mode="append_only"),
        operation("question.cancel", "terminal_state", "governance", lease=False, writes_records=True, write_mode="append_only"),
        operation("question.annul", "terminal_state", "governance", lease=False, writes_records=True, write_mode="append_only"),
        operation("resolution.record", "create", "resolution", lease=True, writes_records=True, write_mode="insert_once"),
        operation("score.create", "create", "scoring", lease=True, writes_records=True, write_mode="insert_once"),
        operation("evidence.append", "append_update", "evidence", lease=True, writes_records=True, write_mode="append_only"),
        operation("method.apply", "method_state", "method_update", lease=True, writes_records=True, write_mode="prospective_binding"),
        operation("method.rollback", "method_state", "method_update", lease=True, writes_records=True, write_mode="prospective_binding"),
        operation(
            "record.archive",
            "delete_replacement",
            "retention",
            lease=False,
            writes_records=True,
            write_mode="tombstone_append",
            delete_replacement="archive_tombstone",
        ),
        operation(
            "record.redact",
            "delete_replacement",
            "retention",
            lease=False,
            writes_records=True,
            write_mode="redaction_append",
            delete_replacement="redaction_receipt",
        ),
    ]


def record_class(record_type: str, schema_file: str, table: str, write_mode: str) -> dict[str, Any]:
    return {
        "recordType": record_type,
        "schemaFile": schema_file,
        "storageTable": table,
        "mutableAfterWrite": False,
        "writeMode": write_mode,
        "hashRequired": True,
        "provenanceRequired": True,
    }


def immutable_record_store() -> list[dict[str, Any]]:
    return [
        record_class("forecast_question", "spec/forecast-question.schema.json", "ope_records", "insert_once"),
        record_class("evidence_packet", "spec/evidence-packet.schema.json", "ope_records", "insert_once"),
        record_class("forecast_artifact", "spec/forecast-artifact.schema.json", "ope_records", "insert_once"),
        record_class("forecast_history", "spec/forecast-history.schema.json", "forecast_history_events", "append_only"),
        record_class("resolution_record", "spec/resolution-record.schema.json", "ope_records", "insert_once"),
        record_class("scoring_report", "spec/scoring-report.schema.json", "ope_records", "insert_once"),
        record_class("calibration_summary", "spec/calibration-summary.schema.json", "ope_records", "insert_once"),
        record_class("method_update_audit", "spec/prediction-campaign-method-update-action.schema.json", "operation_audit_records", "append_only"),
        record_class("operation_receipt", "spec/lifecycle-operation.schema.json", "operation_receipts", "append_only"),
        record_class("archive_tombstone", "spec/lifecycle-operation.schema.json", "operation_audit_records", "append_only"),
        record_class("redaction_receipt", "spec/lifecycle-operation.schema.json", "operation_audit_records", "append_only"),
    ]


def read_model(name: str, purpose: str, sources: list[str], question: str, policy: str = "transactional_projection") -> dict[str, Any]:
    return {
        "readModelName": name,
        "purpose": purpose,
        "sourceTables": sources,
        "agentQuestion": question,
        "readOnly": True,
        "stalenessPolicy": policy,
    }


def read_models() -> list[dict[str, Any]]:
    return [
        read_model("campaign_status", "Summarize campaign progress, current method binding, blockers, and next safe actions.", ["campaign_state", "operation_receipts"], "What is this campaign doing now?"),
        read_model("next_due_forecast", "Find the next forecast that can be created before close without duplicating a run.", ["planned_runs", "operation_receipts", "operation_leases"], "Which forecast is due next?"),
        read_model("due_resolution_jobs", "List forecasts whose resolution window is due and whose resolver operation can be preflighted.", ["ope_records", "operation_receipts"], "Which resolutions are due now?"),
        read_model("unresolved_forecasts", "List open or closed forecasts without resolution records for recovery and monitoring.", ["ope_records", "forecast_history_events"], "Which forecasts are unresolved?"),
        read_model("append_readiness", "Classify resolved scoring records as comparable, excluded, duplicate, or blocked before ledger append.", ["ope_records", "operation_receipts"], "Can this outcome enter evidence?"),
        read_model("calibration_status", "Report sample-size, exclusion, provenance, and threshold status before calibration or method changes.", ["ope_records", "evidence_ledger_rows"], "Is calibration evidence ready?"),
        read_model("track_record_progress", "Track baseline lift, Brier summaries, comparable sample counts, and claim boundaries.", ["ope_records", "evidence_ledger_rows"], "What is the track-record state?"),
        read_model("failed_operations", "Expose failed or blocked operation receipts with sanitized recovery categories.", ["operation_receipts"], "Which operations need attention?", "rebuildable_projection"),
        read_model("recovery_actions", "Map interrupted, stale, lease-conflicted, or idempotent-repeat states to safe next commands.", ["operation_receipts", "operation_leases"], "What should the agent do next?", "rebuildable_projection"),
    ]


def build_lifecycle_operation_store() -> dict[str, Any]:
    operations = operation_catalog()
    records = immutable_record_store()
    models = read_models()
    runtime_scenarios = run_runtime_scenarios()
    schema_plan = sqlite_schema_plan()
    store = {
        "lifecycleOperationStoreId": "lifecycleoperationstore-001",
        "generatedAt": GENERATED_AT,
        "storeStatus": "local_sqlite_runtime_checked",
        "designScope": "database_backed_lifecycle_operations",
        "storageBackends": storage_backends(),
        "sqliteSchemaPlan": schema_plan,
        "operationCatalog": operations,
        "immutableRecordStore": records,
        "idempotencyModel": {
            "tableName": "operation_idempotency_keys",
            "requiredForAllEffectfulOperations": True,
            "keyFields": ["operationName", "campaignId", "runId", "forecastId", "callerId", "idempotencyKey", "sourceRecordHash"],
            "conflictPolicy": "return_existing_receipt_or_block_mismatch",
            "storesOperationReceipt": True,
            "storesSourceRecordHashes": True,
            "retryBehavior": "safe_repeat_returns_same_receipt",
        },
        "leaseModel": {
            "tableName": "operation_leases",
            "leaseRequiredFor": ["campaign.create_run", "forecast.create", "resolution.record", "score.create", "evidence.append", "method.apply", "method.rollback"],
            "leaseOwnerField": "agentOrWorkerId",
            "expiresAtRequired": True,
            "conflictStatus": "blocked_lease_conflict",
            "renewalPolicy": "explicit_renewal_before_expiry",
            "releasePolicy": "release_after_receipt_or_expiry",
        },
        "readModels": models,
        "mutationSemantics": {
            "rawCrudExposed": False,
            "forecastArtifactsMutable": False,
            "forecastHistoriesMutable": False,
            "updatesAppendHistory": True,
            "deleteAllowedAsPhysicalDefault": False,
            "deleteReplacementOperations": ["question.cancel", "question.annul", "record.archive", "record.redact", "method.rollback"],
            "prospectiveMethodBindingsOnly": True,
            "postOutcomeForecastRewriteAllowed": False,
        },
        "migrationPlan": {
            "fromState": "ignored_json_live_state",
            "firstTarget": "local_sqlite",
            "importsIgnoredJsonState": True,
            "rewritesHistoricalForecasts": False,
            "preservesContentHashes": True,
            "migrationReceiptRequired": True,
            "normalChecksRequireDatabase": False,
        },
        "agentPreflightSurface": {
            "preflightRequired": True,
            "plannedWritesListed": True,
            "blockingGuardsListed": True,
            "idempotencyKeyEchoed": True,
            "leasePlanListed": True,
            "operationReceiptReturned": True,
            "safeRetryAdviceReturned": True,
            "claimBoundaryReturned": True,
        },
        "runtimeScenarios": runtime_scenarios,
        "executionBoundary": {
            "readbackExecutesDatabaseWrites": False,
            "sqliteRuntimeImplemented": True,
            "sqliteScenarioUsesEphemeralDatabase": True,
            "postgresRuntimeImplemented": False,
            "hostedRuntimeImplemented": False,
            "networkApiImplemented": False,
            "osSchedulerInstalled": False,
            "rawCrudExposedToAgents": False,
            "normalChecksRequireDatabase": False,
            "storesCredentials": False,
            "fetchesLiveData": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "qualityClaimAllowed": False,
        },
        "summary": {
            "databaseBackendPlanned": True,
            "databaseBackendImplemented": True,
            "firstBackend": "local_sqlite",
            "productionDesignBackend": "postgres_design",
            "operationCount": len(operations),
            "readModelCount": len(models),
            "immutableRecordClassCount": len(records),
            "sqliteTableCount": len(schema_plan),
            "runtimeScenarioCount": len(runtime_scenarios),
            "deleteReplacedByLifecycleOperations": True,
            "agentImplementationReady": True,
            "sqliteRuntimeChecked": True,
            "runtimeImplementationStatus": "local_sqlite_runtime_checked",
        },
        "warnings": [
            "Default readback uses an ephemeral SQLite scenario and does not create a persistent database file.",
            "Agents should call lifecycle operations and read models, not raw forecast CRUD.",
            "Forecast artifacts and histories remain immutable after creation.",
            "Delete-like requests become cancel, annul, archive, redact, or rollback records.",
            "Postgres remains a schema-compatible design target; hosted runtime support is still out of scope.",
        ],
    }
    validate_lifecycle_operation_store(store)
    return store


def validate_lifecycle_operation_store(store: dict[str, Any]) -> None:
    errors = validate_record(store, SCHEMA)
    if errors:
        raise LifecycleOperationStoreError(f"lifecycle operation store schema validation failed: {errors[0]}")
    boundary = store["executionBoundary"]
    forbidden = [
        "readbackExecutesDatabaseWrites",
        "postgresRuntimeImplemented",
        "hostedRuntimeImplemented",
        "networkApiImplemented",
        "osSchedulerInstalled",
        "rawCrudExposedToAgents",
        "normalChecksRequireDatabase",
        "storesCredentials",
        "fetchesLiveData",
        "createsForecastArtifacts",
        "createsResolutionArtifacts",
        "createsScoringRecords",
        "qualityClaimAllowed",
    ]
    for flag in forbidden:
        if boundary[flag]:
            raise LifecycleOperationStoreError(f"lifecycle operation store readback must keep {flag} false")
    if not boundary["sqliteRuntimeImplemented"] or not boundary["sqliteScenarioUsesEphemeralDatabase"]:
        raise LifecycleOperationStoreError("lifecycle operation store must exercise an ephemeral SQLite runtime")
    semantics = store["mutationSemantics"]
    if semantics["rawCrudExposed"] or semantics["forecastArtifactsMutable"] or semantics["forecastHistoriesMutable"]:
        raise LifecycleOperationStoreError("lifecycle operation store must not expose mutable forecast CRUD")
    if semantics["deleteAllowedAsPhysicalDefault"] or semantics["postOutcomeForecastRewriteAllowed"]:
        raise LifecycleOperationStoreError("lifecycle operation store must block silent delete and post-outcome rewrites")
    if not store["idempotencyModel"]["requiredForAllEffectfulOperations"]:
        raise LifecycleOperationStoreError("effectful operations must require idempotency")
    lease_required = set(store["leaseModel"]["leaseRequiredFor"])
    for item in store["operationCatalog"]:
        if not item["requiresPreflight"] or not item["requiresIdempotencyKey"]:
            raise LifecycleOperationStoreError("all lifecycle operations must require preflight and idempotency")
        claims = item["claimBoundary"]
        if any(claims.values()):
            raise LifecycleOperationStoreError("operation catalog must not allow quality, rewrite, silent delete, or raw CRUD claims")
        if item["requiresLease"] and item["operationName"] not in lease_required:
            raise LifecycleOperationStoreError(f"leased operation missing from lease model: {item['operationName']}")
        if item["operationClass"] == "delete_replacement" and item["deleteReplacement"] == "not_delete":
            raise LifecycleOperationStoreError("delete replacement operations must declare archive or redaction behavior")
    for record in store["immutableRecordStore"]:
        if record["mutableAfterWrite"]:
            raise LifecycleOperationStoreError("stored OPE record classes must be immutable after write")
    scenarios = {item["scenarioName"]: item for item in store["runtimeScenarios"]}
    if list(scenarios) != SCENARIO_NAMES:
        raise LifecycleOperationStoreError("lifecycle operation store runtime scenario coverage drifted")
    for item in scenarios.values():
        if not item["sqliteRuntimeExercised"]:
            raise LifecycleOperationStoreError("runtime scenarios must exercise SQLite")
        if item["rawCrudExposed"] or item["physicalDeletes"] or item["historyRewriteCount"]:
            raise LifecycleOperationStoreError("runtime scenarios must not expose CRUD, physical delete, or history rewrites")
        if any(item["preflight"]["claimBoundary"].values()):
            raise LifecycleOperationStoreError("runtime scenarios must preserve claim boundaries")
        if not item["preflight"]["plannedWrites"] or not item["preflight"]["blockingGuards"]:
            raise LifecycleOperationStoreError("runtime scenarios must expose planned writes and blocking guards")


def write_lifecycle_operation_store(store: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        store,
        label="lifecycle operation store",
        regen="python3 scripts/generate_lifecycle_operation_store.py --write",
    )


def check_lifecycle_operation_store(store: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        store,
        label="lifecycle operation store",
        regen="python3 scripts/generate_lifecycle_operation_store.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIO_NAMES, help="print one checked SQLite runtime scenario")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        store = build_lifecycle_operation_store()
        if args.scenario:
            scenario = next(item for item in store["runtimeScenarios"] if item["scenarioName"] == args.scenario)
            sys.stdout.write(render_json(scenario))
        elif args.write:
            write_lifecycle_operation_store(store)
        elif args.check:
            check_lifecycle_operation_store(store)
        else:
            sys.stdout.write(render_json(store))
    except LifecycleOperationStoreError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
