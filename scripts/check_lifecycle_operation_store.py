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
    "pre_calibration.bind",
    "method.apply",
    "method.rollback",
    "state.import_json",
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
    "pilot_findings",
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
    "pre-calibration-bind",
    "campaign-forecast-create",
    "campaign-resolution-record",
    "campaign-score-create",
    "campaign-evidence-append",
    "pilot-evidence-append",
    "campaign-method-apply",
    "campaign-method-rollback",
    "json-state-import",
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

REQUIRED_WRITE_LOCAL_COMMANDS = {
    "prediction-campaign start --write-local",
    "prediction-campaign start --pre-calibrate --write-local",
    "prediction-campaign forecast-write --write-local",
    "prediction-campaign resolve --execute-resolvers --write-local",
    "prediction-campaign append --write-local",
    "prediction-campaign pre-calibration --write-local",
    "prediction-campaign apply-method-update --write-local",
    "prediction-campaign rollback-method-update --write-local",
    "pilot-evidence --input-summary --write-local",
}

REQUIRED_COMPATIBILITY_CLASSES = {
    "forecast_lifecycle_records",
    "resolution_records",
    "scoring_reports",
    "evidence_ledger_rows",
    "pre_calibration_method_binding",
    "method_apply_binding",
    "method_rollback_binding",
    "pilot_evidence_ledger_rows",
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
        {
            "campaign.create_run",
            "forecast.create",
            "resolution.record",
            "score.create",
            "evidence.append",
            "pre_calibration.bind",
            "method.apply",
            "method.rollback",
            "state.import_json",
        }.issubset(leased),
        "racing operations should require leases",
    )
    require(operations["forecast.recalculate"]["allowedWriteMode"] == "append_only", "forecast recalculation should append history")
    require(operations["pre_calibration.bind"]["allowedWriteMode"] == "prospective_binding", "pre-calibration binding should be prospective")
    require(operations["method.apply"]["allowedWriteMode"] == "prospective_binding", "method apply should be prospective")
    require(operations["method.rollback"]["allowedWriteMode"] == "prospective_binding", "method rollback should be prospective")
    require(operations["state.import_json"]["operationClass"] == "migration", "JSON import should be a migration operation")
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
    require(any(item["recordType"] == "evidence_ledger_row" for item in records), "immutable store should include evidence ledger rows")
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

    compat = store["jsonCompatibilityAdapter"]
    require(compat["adapterName"] == "ignored_json_live_state", "JSON compatibility adapter name drifted")
    require(compat["adapterStatus"] == "current_compatibility_adapter", "JSON compatibility adapter status drifted")
    require(compat["sourceRoot"] == ".ope/live", "JSON compatibility source root drifted")
    require(compat["readCompatibilityAllowed"] is True, "ignored JSON reads should remain compatibility-allowed")
    require(compat["writeCompatibilityAllowed"] is True, "ignored JSON writes should remain compatibility-allowed during migration")
    require(compat["normalChecksWriteLiveState"] is False, "normal checks must not write ignored JSON state")
    require(compat["automaticMigrationAllowed"] is False, "migration must not be automatic")
    require(compat["explicitMigrationOperationRequired"] is True, "migration should require an explicit operation")
    require(compat["migrationReceiptRequired"] is True, "migration should require operation receipts")
    require(compat["contentHashCheckRequired"] is True, "migration should require content-hash checks")
    require(compat["sourceRecordHashRequired"] is True, "migration should require source record hashes")
    require(compat["preservesForecastProbabilities"] is True, "migration must preserve forecast probabilities")
    require(compat["preservesSourceProvenance"] is True, "migration must preserve source provenance")
    require(compat["rewritesHistoricalForecasts"] is False, "compatibility adapter must not rewrite historical forecasts")
    require(compat["rawCrudExposed"] is False, "compatibility adapter must not expose raw CRUD")
    compat_classes = {item["stateClass"]: item for item in compat["stateClasses"]}
    require(
        set(compat_classes) == {"forecast_lifecycle_records", "campaign_state", "run_state", "evidence_ledger", "method_binding", "operation_audit", "pilot_evidence_ledger"},
        "JSON compatibility adapter should cover current ignored live state classes",
    )
    for item in compat_classes.values():
        require(item["contentHashPreserved"] is True, "compatibility state classes should preserve content hashes")
        require(item["migrationReceiptRequired"] is True, "compatibility state classes should require receipts")
        require(item["rawCrudExposed"] is False, "compatibility state classes must not expose raw CRUD")

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
        require(item["payloadHashBindings"], "runtime scenario should expose payload hash bindings")
        require(all(row["matchesSourceHash"] is True for row in item["payloadHashBindings"]), "runtime payload hashes should match source hashes")
    require(scenarios["create"]["executionStatus"] == "committed", "create scenario should commit")
    require(scenarios["create"]["immutableRecordsInserted"] >= 4, "create scenario should insert forecast lifecycle records")
    require(scenarios["retry-idempotent"]["executionStatus"] == "idempotent_replay", "retry scenario should return existing receipt")
    require(scenarios["retry-idempotent"]["operationReceiptsWritten"] == 0, "retry scenario should not write another receipt")
    require(scenarios["lease-conflict"]["executionStatus"] == "blocked_lease_conflict", "lease conflict should block")
    require(scenarios["lease-conflict"]["immutableRecordsInserted"] == 0, "lease conflict should not insert records")
    require(scenarios["archive"]["auditRecordsInserted"] == 1, "archive should append an audit/tombstone record")
    require(scenarios["redaction"]["auditRecordsInserted"] == 1, "redaction should append a redaction receipt")
    require(scenarios["method-rollback"]["executionStatus"] == "committed", "method rollback should commit prospectively")
    require("calibration_status" in scenarios["method-rollback"]["readModelEffects"], "method rollback should update calibration status")
    require(scenarios["pre-calibration-bind"]["executionStatus"] == "committed", "pre-calibration binding should commit prospectively")
    require(scenarios["pre-calibration-bind"]["auditRecordsInserted"] == 1, "pre-calibration binding should write one audit record")
    require("calibration_status" in scenarios["pre-calibration-bind"]["readModelEffects"], "pre-calibration should update calibration status")
    require("track_record_progress" in scenarios["pre-calibration-bind"]["readModelEffects"], "pre-calibration should update track-record progress")
    require(
        scenarios["pre-calibration-bind"]["preflight"]["plannedWrites"][1]["recordType"] == "pre_calibration_binding",
        "pre-calibration should write a pre-calibration binding record",
    )
    require(scenarios["campaign-forecast-create"]["executionStatus"] == "committed", "campaign forecast create bridge should commit")
    require(scenarios["campaign-forecast-create"]["immutableRecordsInserted"] == 4, "campaign forecast bridge should insert four lifecycle records")
    require(
        {row["recordType"] for row in scenarios["campaign-forecast-create"]["payloadHashBindings"]}
        == {"forecast_question", "evidence_packet", "forecast_artifact", "forecast_history"},
        "campaign forecast bridge should bind the current forecast write payloads",
    )
    require(scenarios["campaign-resolution-record"]["operationName"] == "resolution.record", "campaign resolution bridge operation drifted")
    require(scenarios["campaign-score-create"]["operationName"] == "score.create", "campaign score bridge operation drifted")
    require("append_readiness" in scenarios["campaign-score-create"]["readModelEffects"], "campaign score bridge should update append readiness")
    require(scenarios["campaign-evidence-append"]["preflight"]["plannedWrites"][1]["recordType"] == "evidence_ledger_row", "campaign append bridge should write ledger rows")
    require("append_readiness" in scenarios["campaign-evidence-append"]["readModelEffects"], "campaign append bridge should update append readiness")
    require("calibration_status" in scenarios["campaign-evidence-append"]["readModelEffects"], "campaign append bridge should update calibration status")
    require("track_record_progress" in scenarios["campaign-evidence-append"]["readModelEffects"], "campaign append bridge should update track-record progress")
    require(scenarios["pilot-evidence-append"]["operationName"] == "evidence.append", "pilot evidence append operation drifted")
    require(scenarios["pilot-evidence-append"]["preflight"]["plannedWrites"][1]["recordType"] == "pilot_evidence_ledger_row", "pilot evidence append should write pilot ledger rows")
    require("pilot_findings" in scenarios["pilot-evidence-append"]["readModelEffects"], "pilot evidence append should update pilot findings")
    require("calibration_status" not in scenarios["pilot-evidence-append"]["readModelEffects"], "pilot evidence append must not update calibration status")
    require("track_record_progress" not in scenarios["pilot-evidence-append"]["readModelEffects"], "pilot evidence append must not update track-record progress")
    require(scenarios["campaign-method-apply"]["operationName"] == "method.apply", "campaign method apply bridge operation drifted")
    require(scenarios["campaign-method-rollback"]["operationName"] == "method.rollback", "campaign method rollback bridge operation drifted")
    require(scenarios["json-state-import"]["operationName"] == "state.import_json", "JSON state import operation drifted")
    require(scenarios["json-state-import"]["executionStatus"] == "committed", "JSON state import should commit")
    require(scenarios["json-state-import"]["operationReceiptsWritten"] == 1, "JSON state import should write a migration receipt")
    migration_summary = scenarios["json-state-import"]["migrationImportSummary"]
    require(migration_summary is not None, "JSON state import should expose migration summary")
    require(migration_summary["sourceRoot"] == ".ope/live/prediction-campaigns", "JSON state import source root drifted")
    require(migration_summary["contentHashesPreserved"] is True, "JSON state import should preserve content hashes")
    require(migration_summary["forecastProbabilitiesPreserved"] is True, "JSON state import should preserve forecast probabilities")
    require(migration_summary["sourceProvenancePreserved"] is True, "JSON state import should preserve source provenance")
    require(migration_summary["historicalForecastRewriteCount"] == 0, "JSON state import must not rewrite history")
    require(migration_summary["methodBindingsPreserved"] is True, "JSON state import should preserve method bindings")
    require(migration_summary["migrationReceiptRequired"] is True, "JSON state import should require receipts")
    require(migration_summary["automaticMigrationAllowed"] is False, "JSON state import must not be automatic")
    require(
        {write["tableName"] for write in scenarios["json-state-import"]["preflight"]["plannedWrites"]}
        >= {"operation_receipts", "ope_records", "forecast_history_events", "evidence_ledger_rows", "read_model_rows", "operation_audit_records"},
        "JSON state import should plan writes across imported state tables",
    )
    require(scenarios["recovery"]["executionStatus"] == "failed_preflight_guard", "recovery scenario should record a failed preflight")
    require("failed_operations" in scenarios["recovery"]["readModelEffects"], "recovery scenario should expose failed operations")
    require("recovery_actions" in scenarios["recovery"]["readModelEffects"], "recovery scenario should expose recovery actions")

    write_local_coverage = store["writeLocalOperationCoverage"]
    require(
        {item["commandPath"] for item in write_local_coverage} == REQUIRED_WRITE_LOCAL_COMMANDS,
        "write-local operation coverage should cover every current explicit local mutation path",
    )
    for item in write_local_coverage:
        require(item["allReceiptsChecked"] is True, "write-local coverage should check operation receipts")
        require(item["allReadModelsChecked"] is True, "write-local coverage should check read-model effects")
        require(item["idempotencyRequired"] is True, "write-local coverage should require idempotency")
        require(item["leaseRequired"] is True, "write-local coverage should require leases")
        require(item["rawCrudExposed"] is False, "write-local coverage must not expose raw CRUD")
        require(item["normalChecksWriteLiveState"] is False, "normal checks must not write ignored local state")
        require(item["compatibilityJsonWriteAllowed"] is True, "ignored JSON writes should remain explicitly compatibility-allowed")
        scenario_receipts = 0
        scenario_read_models = set()
        scenario_operations = set()
        for scenario_name in item["scenarioNames"]:
            scenario = scenarios[scenario_name]
            require(scenario["executionStatus"] == "committed", "write-local coverage scenarios should commit")
            scenario_receipts += scenario["operationReceiptsWritten"]
            scenario_read_models.update(scenario["readModelEffects"])
            scenario_operations.add(scenario["operationName"])
        require(
            scenario_receipts >= item["requiredOperationReceiptCount"],
            f"write-local command lacks operation receipts: {item['commandPath']}",
        )
        require(
            set(item["requiredReadModels"]).issubset(scenario_read_models),
            f"write-local command lacks read model coverage: {item['commandPath']}",
        )
        require(
            set(item["lifecycleOperations"]) == scenario_operations,
            f"write-local command operation mapping drifted: {item['commandPath']}",
        )

    compatibility_checks = store["fileDatabaseCompatibilityChecks"]
    require(
        {item["recordClass"] for item in compatibility_checks} == REQUIRED_COMPATIBILITY_CLASSES,
        "file/database compatibility checks should cover forecasts, resolutions, scores, ledger rows, and method bindings",
    )
    for item in compatibility_checks:
        scenario = scenarios[item["scenarioName"]]
        require(scenario["operationName"] == item["lifecycleOperation"], "compatibility check scenario mapping drifted")
        require(item["fileModeDuplicatePrevented"] is True, "file-mode duplicate prevention should be checked")
        require(item["databaseFirstExecutionStatus"] == "committed", "database compatibility first write should commit")
        require(item["databaseReplayExecutionStatus"] == "idempotent_replay", "database compatibility replay should be idempotent")
        require(item["databaseReplayIdempotencyStatus"] == "return_existing_receipt", "database replay should return the existing receipt")
        require(item["databaseReplayOperationReceiptsWritten"] == 0, "database replay should not write duplicate receipts")
        require(item["databaseDuplicateRecordsCreated"] == 0, "database replay should not create duplicate records")
        require(item["contentHashComparisonRequired"] is True, "compatibility checks should require content hashes")
        require(item["historyRewriteCount"] == 0, "compatibility checks must not rewrite forecast history")
        require(item["physicalDeletes"] == 0, "compatibility checks must not physically delete records")
        require(item["rawCrudExposed"] is False, "compatibility checks must not expose raw CRUD")
        require(item["compatible"] is True, "file/database compatibility check should pass")

    summary = store["summary"]
    require(summary["databaseBackendPlanned"] is True, "database backend should be planned")
    require(summary["databaseBackendImplemented"] is True, "database backend should be implemented locally")
    require(summary["firstBackend"] == "local_sqlite", "first backend should be SQLite")
    require(summary["productionDesignBackend"] == "postgres_design", "production design backend should be Postgres")
    require(summary["sqliteTableCount"] == len(REQUIRED_SQLITE_TABLES), "SQLite table count drifted")
    require(summary["runtimeScenarioCount"] == len(REQUIRED_SCENARIOS), "runtime scenario count drifted")
    require(summary["writeLocalOperationCoverageCount"] == len(REQUIRED_WRITE_LOCAL_COMMANDS), "write-local coverage count drifted")
    require(summary["allWriteLocalPathsReceiptBacked"] is True, "all write-local paths should be receipt-backed")
    require(summary["allWriteLocalPathsReadModelBacked"] is True, "all write-local paths should be read-model-backed")
    require(summary["fileDatabaseCompatibilityCheckCount"] == len(REQUIRED_COMPATIBILITY_CLASSES), "file/database compatibility count drifted")
    require(summary["fileDatabaseCompatibilityChecked"] is True, "file/database compatibility should be checked")
    require(summary["deleteReplacedByLifecycleOperations"] is True, "delete should be replaced by lifecycle operations")
    require(summary["agentImplementationReady"] is True, "contract should be ready for agent implementation planning")
    require(summary["sqliteRuntimeChecked"] is True, "SQLite runtime should be checked")
    require(summary["runtimeImplementationStatus"] == "local_sqlite_runtime_checked", "runtime implementation status drifted")
    print("checked lifecycle operation store")


if __name__ == "__main__":
    main()
