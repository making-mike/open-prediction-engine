#!/usr/bin/env python3
"""Check lifecycle operation store invariants."""

from __future__ import annotations

from generate_lifecycle_operation_store import build_lifecycle_operation_store


REQUIRED_OPERATIONS = {
    "campaign.create_run",
    "forecast.create",
    "forecast.recalculate",
    "question.cancel",
    "question.annul",
    "resolution.record",
    "score.create",
    "evidence.append",
    "method.apply",
    "method.rollback",
    "record.archive",
    "record.redact",
}

REQUIRED_READ_MODELS = {
    "campaign_status",
    "next_due_forecast",
    "due_resolution_jobs",
    "unresolved_forecasts",
    "append_readiness",
    "calibration_status",
    "track_record_progress",
    "failed_operations",
    "recovery_actions",
}

REQUIRED_SCENARIOS = [
    "create",
    "retry-idempotent",
    "lease-conflict",
    "archive",
    "redaction",
    "method-rollback",
    "recovery",
]

REQUIRED_SQLITE_TABLES = {
    "operation_receipts",
    "operation_idempotency_keys",
    "operation_leases",
    "ope_records",
    "forecast_history_events",
    "operation_audit_records",
    "evidence_ledger_rows",
    "read_model_rows",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    store = build_lifecycle_operation_store()
    operations = {item["operationName"]: item for item in store["operationCatalog"]}
    require(set(operations) == REQUIRED_OPERATIONS, "operation catalog should cover the planned lifecycle operations")

    for item in operations.values():
        require(item["requiresPreflight"] is True, "every operation should require preflight")
        require(item["requiresIdempotencyKey"] is True, "every operation should require idempotency")
        require(item["updatesReadModels"] is True, "every operation should update read models")
        require(item["writesImmutableRecords"] is True, "every operation should write immutable records or receipts")
        require(item["claimBoundary"]["createsQualityClaim"] is False, "operations must not create quality claims")
        require(item["claimBoundary"]["allowsPostOutcomeRewrite"] is False, "operations must not allow post-outcome rewrites")
        require(item["claimBoundary"]["allowsSilentDelete"] is False, "operations must not allow silent delete")
        require(item["claimBoundary"]["allowsRawCrud"] is False, "operations must not allow raw CRUD")

    leased = {item["operationName"] for item in operations.values() if item["requiresLease"]}
    require(
        {"campaign.create_run", "forecast.create", "resolution.record", "score.create", "evidence.append", "method.apply", "method.rollback"}.issubset(leased),
        "racing operations should require leases",
    )
    require(operations["forecast.recalculate"]["allowedWriteMode"] == "append_only", "forecast recalculation should append history")
    require(operations["method.apply"]["allowedWriteMode"] == "prospective_binding", "method apply should be prospective")
    require(operations["method.rollback"]["allowedWriteMode"] == "prospective_binding", "method rollback should be prospective")
    require(operations["record.archive"]["deleteReplacement"] == "archive_tombstone", "archive should replace delete with tombstone")
    require(operations["record.redact"]["deleteReplacement"] == "redaction_receipt", "redaction should replace delete with receipt")

    backends = {item["backendName"]: item for item in store["storageBackends"]}
    require(backends["ignored_json_compat"]["implementationStatus"] == "current_compatibility", "ignored JSON compatibility status drifted")
    require(backends["local_sqlite"]["implementationStatus"] == "implemented_local_runtime", "SQLite should be the implemented local runtime")
    require(backends["local_sqlite"]["supportsTransactions"] is True, "SQLite backend should require transactions")
    require(backends["local_sqlite"]["supportsLeases"] is True, "SQLite backend should require leases")
    require(backends["postgres_design"]["implementationStatus"] == "planned_production_design", "Postgres should remain a production design target")

    sqlite_tables = {item["tableName"]: item for item in store["sqliteSchemaPlan"]}
    require(set(sqlite_tables) == REQUIRED_SQLITE_TABLES, "SQLite schema plan should cover operation runtime tables")
    for item in sqlite_tables.values():
        require(item["postgresCompatible"] is True, "SQLite table plans should preserve Postgres compatibility")
        require(item["rawCrudExposed"] is False, "SQLite table plans must not expose raw CRUD")
    require(sqlite_tables["operation_leases"]["mutableProjection"] is True, "leases should be mutable expiring coordination rows")
    require(sqlite_tables["read_model_rows"]["mutableProjection"] is True, "read models should be rebuildable projections")
    require(sqlite_tables["ope_records"]["storesImmutableRecords"] is True, "ope_records should store immutable records")

    records = store["immutableRecordStore"]
    require(any(item["recordType"] == "forecast_artifact" for item in records), "immutable store should include forecast artifacts")
    require(any(item["recordType"] == "forecast_history" for item in records), "immutable store should include forecast history")
    for item in records:
        require(item["mutableAfterWrite"] is False, "record classes must be immutable after write")
        require(item["hashRequired"] is True, "record classes should require content hashes")
        require(item["provenanceRequired"] is True, "record classes should require provenance")

    idempotency = store["idempotencyModel"]
    require(idempotency["requiredForAllEffectfulOperations"] is True, "idempotency should be universal")
    require(idempotency["conflictPolicy"] == "return_existing_receipt_or_block_mismatch", "idempotency conflict policy drifted")
    require(idempotency["storesOperationReceipt"] is True, "idempotency should store operation receipts")

    lease_model = store["leaseModel"]
    require(set(lease_model["leaseRequiredFor"]) == leased, "lease model should match leased operations")
    require(lease_model["expiresAtRequired"] is True, "leases must expire")
    require(lease_model["conflictStatus"] == "blocked_lease_conflict", "lease conflict status drifted")

    read_models = {item["readModelName"]: item for item in store["readModels"]}
    require(set(read_models) == REQUIRED_READ_MODELS, "read models should cover agent workflow questions")
    for item in read_models.values():
        require(item["readOnly"] is True, "read models must be read-only")
        require(item["sourceTables"], "read models should declare source tables")
        require(item["agentQuestion"], "read models should answer an agent question")

    semantics = store["mutationSemantics"]
    require(semantics["rawCrudExposed"] is False, "raw CRUD must not be exposed")
    require(semantics["forecastArtifactsMutable"] is False, "forecast artifacts must not be mutable")
    require(semantics["forecastHistoriesMutable"] is False, "forecast histories must not be mutable")
    require(semantics["updatesAppendHistory"] is True, "updates should append lifecycle history")
    require(semantics["deleteAllowedAsPhysicalDefault"] is False, "physical delete must not be default")
    require(semantics["postOutcomeForecastRewriteAllowed"] is False, "post-outcome forecast rewrite must be blocked")
    require(
        {"question.cancel", "question.annul", "record.archive", "record.redact", "method.rollback"}.issubset(semantics["deleteReplacementOperations"]),
        "delete replacements should cover cancel, annul, archive, redact, and rollback",
    )

    migration = store["migrationPlan"]
    require(migration["firstTarget"] == "local_sqlite", "migration should target local SQLite first")
    require(migration["rewritesHistoricalForecasts"] is False, "migration must not rewrite historical forecasts")
    require(migration["preservesContentHashes"] is True, "migration should preserve content hashes")
    require(migration["normalChecksRequireDatabase"] is False, "normal checks should not require a database")

    boundary = store["executionBoundary"]
    for flag in [
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
    ]:
        require(boundary[flag] is False, f"execution boundary should keep {flag} false")
    require(boundary["sqliteRuntimeImplemented"] is True, "SQLite runtime should be implemented")
    require(boundary["sqliteScenarioUsesEphemeralDatabase"] is True, "normal readback should use ephemeral SQLite scenarios")

    scenarios = {item["scenarioName"]: item for item in store["runtimeScenarios"]}
    require(list(scenarios) == REQUIRED_SCENARIOS, "runtime scenarios should cover the expected lifecycle cases in order")
    for item in scenarios.values():
        require(item["sqliteRuntimeExercised"] is True, "runtime scenario should exercise SQLite")
        require(item["rawCrudExposed"] is False, "runtime scenario must not expose raw CRUD")
        require(item["forecastArtifactMutable"] is False, "runtime scenario must keep forecast artifacts immutable")
        require(item["physicalDeletes"] == 0, "runtime scenario must not perform physical deletes")
        require(item["historyRewriteCount"] == 0, "runtime scenario must not rewrite history")
        require(item["duplicateRecordsCreated"] == 0, "runtime scenario must not create duplicate immutable records")
        require(item["preflight"]["plannedWrites"], "runtime scenario should list planned writes")
        require(item["preflight"]["blockingGuards"], "runtime scenario should list blocking guards")
        require(item["preflight"]["idempotencyKey"], "runtime scenario should echo idempotency key")
        require(all(value is False for value in item["preflight"]["claimBoundary"].values()), "scenario claim boundary should stay false")
    require(scenarios["create"]["executionStatus"] == "committed", "create scenario should commit")
    require(scenarios["create"]["immutableRecordsInserted"] >= 2, "create scenario should insert forecast artifact and history")
    require(scenarios["retry-idempotent"]["executionStatus"] == "idempotent_replay", "retry scenario should return existing receipt")
    require(scenarios["retry-idempotent"]["operationReceiptsWritten"] == 0, "retry scenario should not write another receipt")
    require(scenarios["lease-conflict"]["executionStatus"] == "blocked_lease_conflict", "lease conflict should block")
    require(scenarios["lease-conflict"]["immutableRecordsInserted"] == 0, "lease conflict should not insert records")
    require(scenarios["archive"]["auditRecordsInserted"] == 1, "archive should append an audit/tombstone record")
    require(scenarios["redaction"]["auditRecordsInserted"] == 1, "redaction should append a redaction receipt")
    require(scenarios["method-rollback"]["executionStatus"] == "committed", "method rollback should commit prospectively")
    require("calibration_status" in scenarios["method-rollback"]["readModelEffects"], "method rollback should update calibration status")
    require(scenarios["recovery"]["executionStatus"] == "failed_preflight_guard", "recovery scenario should record a failed preflight")
    require("failed_operations" in scenarios["recovery"]["readModelEffects"], "recovery scenario should expose failed operations")
    require("recovery_actions" in scenarios["recovery"]["readModelEffects"], "recovery scenario should expose recovery actions")

    summary = store["summary"]
    require(summary["databaseBackendPlanned"] is True, "database backend should be planned")
    require(summary["databaseBackendImplemented"] is True, "database backend should be implemented locally")
    require(summary["firstBackend"] == "local_sqlite", "first backend should be SQLite")
    require(summary["productionDesignBackend"] == "postgres_design", "production design backend should be Postgres")
    require(summary["sqliteTableCount"] == len(REQUIRED_SQLITE_TABLES), "SQLite table count drifted")
    require(summary["runtimeScenarioCount"] == len(REQUIRED_SCENARIOS), "runtime scenario count drifted")
    require(summary["deleteReplacedByLifecycleOperations"] is True, "delete should be replaced by lifecycle operations")
    require(summary["agentImplementationReady"] is True, "contract should be ready for agent implementation planning")
    require(summary["sqliteRuntimeChecked"] is True, "SQLite runtime should be checked")
    require(summary["runtimeImplementationStatus"] == "local_sqlite_runtime_checked", "runtime implementation status drifted")
    print("checked lifecycle operation store")


if __name__ == "__main__":
    main()
