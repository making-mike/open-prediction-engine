#!/usr/bin/env python3
"""Check SQLite-to-Postgres lifecycle compatibility invariants."""

from __future__ import annotations

try:
    from generate_lifecycle_operation_store import SCENARIO_NAMES
    from generate_postgres_compatibility import build_postgres_compatibility
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until the generator exists
    raise AssertionError("postgres compatibility generator is missing") from exc


REQUIRED_TABLES = {
    "operation_receipts",
    "operation_idempotency_keys",
    "operation_leases",
    "ope_records",
    "forecast_history_events",
    "operation_audit_records",
    "evidence_ledger_rows",
    "read_model_rows",
}

REQUIRED_CONTRACT_SEMANTICS = {
    "json_payloads",
    "content_hashes",
    "unique_idempotency_keys",
    "lease_acquisition",
    "lease_expiry",
    "append_only_records",
    "read_model_upserts",
}

REQUIRED_SQLITE_ONLY_GUARDS = {
    "rowid_dependence",
    "loose_typing_dependence",
    "nonportable_upsert_behavior",
    "missing_timestamp_normalization",
    "sqlite_only_json_query_behavior",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    compatibility = build_postgres_compatibility()

    require(
        compatibility["compatibilityStatus"] == "sqlite_to_postgres_semantics_checked",
        "compatibility status drifted",
    )
    require(compatibility["runtimeScope"] == "storage_semantics_only", "runtime scope drifted")
    require(compatibility["normalChecksConnectToPostgres"] is False, "normal checks must not connect to Postgres")
    require(compatibility["sqliteRuntimeRemainsDefault"] is True, "SQLite should remain the default local runtime")
    require(compatibility["postgresRuntimeImplemented"] is False, "Postgres runtime should remain unimplemented")

    tables = {item["tableName"]: item for item in compatibility["tableCompatibility"]}
    require(set(tables) == REQUIRED_TABLES, "table compatibility coverage drifted")
    for table in tables.values():
        require(table["sqliteTableExists"] is True, f"{table['tableName']} should exist in SQLite plan")
        require(table["postgresTablePlanned"] is True, f"{table['tableName']} should have planned Postgres mapping")
        require(table["jsonPayloadPortable"] is True, f"{table['tableName']} JSON payload should be portable")
        require(table["contentHashPortable"] is True, f"{table['tableName']} content hash should be portable")
        require(table["timestampNormalized"] is True, f"{table['tableName']} timestamp normalization missing")
        require(table["rawCrudExposed"] is False, f"{table['tableName']} must not expose raw CRUD")
        require(table["hostedRuntimeRequired"] is False, f"{table['tableName']} should not require hosted runtime")
    require(tables["operation_idempotency_keys"]["uniqueConstraintPortable"] is True, "idempotency unique key must be portable")
    require(tables["operation_leases"]["leaseExpiryPortable"] is True, "lease expiry must be portable")
    require(tables["read_model_rows"]["upsertPortable"] is True, "read-model upsert must be portable")
    require(tables["ope_records"]["appendOnlyPortable"] is True, "immutable record append semantics must be portable")

    contract = {item["semanticName"]: item for item in compatibility["dialectNeutralAdapterContract"]}
    require(set(contract) == REQUIRED_CONTRACT_SEMANTICS, "dialect-neutral contract coverage drifted")
    for item in contract.values():
        require(item["sqliteMapping"], f"{item['semanticName']} should name SQLite mapping")
        require(item["postgresMapping"], f"{item['semanticName']} should name Postgres mapping")
        require(item["portable"] is True, f"{item['semanticName']} should be portable")
        require(item["normalChecksRequirePostgres"] is False, f"{item['semanticName']} must not require Postgres")

    scenarios = {item["scenarioName"]: item for item in compatibility["scenarioCompatibilityMatrix"]}
    require(list(scenarios) == SCENARIO_NAMES, "scenario compatibility matrix order drifted")
    for scenario_name in SCENARIO_NAMES:
        row = scenarios[scenario_name]
        require(row["sqliteScenarioExists"] is True, f"{scenario_name} should map from an existing SQLite scenario")
        require(row["postgresCompatible"] is True, f"{scenario_name} should be Postgres-compatible")
        require(row["sameOperationSemantics"] is True, f"{scenario_name} operation semantics drifted")
        require(row["sameIdempotencySemantics"] is True, f"{scenario_name} idempotency semantics drifted")
        require(row["sameLeaseSemantics"] is True, f"{scenario_name} lease semantics drifted")
        require(row["sameAppendOnlySemantics"] is True, f"{scenario_name} append-only semantics drifted")
        require(row["sameReadModelSemantics"] is True, f"{scenario_name} read-model semantics drifted")
        require(row["normalChecksConnectToPostgres"] is False, f"{scenario_name} must not require Postgres")
        require(row["hostedRuntimeClaimAllowed"] is False, f"{scenario_name} must not claim hosted runtime")
    require(scenarios["retry-idempotent"]["expectedPostgresBehavior"] == "return_existing_receipt", "retry behavior drifted")
    require(scenarios["lease-conflict"]["expectedPostgresBehavior"] == "blocked_lease_conflict", "lease behavior drifted")
    require(scenarios["json-state-import"]["migrationBoundary"] == "explicit_receipt_backed_import", "JSON import boundary drifted")

    guards = {item["guardName"]: item for item in compatibility["sqliteOnlyAssumptionChecks"]}
    require(set(guards) == REQUIRED_SQLITE_ONLY_GUARDS, "SQLite-only guard coverage drifted")
    for guard in guards.values():
        require(guard["guardStatus"] == "checked", f"{guard['guardName']} should be checked")
        require(guard["sqliteOnlyAssumptionDetected"] is False, f"{guard['guardName']} should detect no active assumption")
        require(guard["blocksPostgresClaimIfFailed"] is True, f"{guard['guardName']} should block portability claims")
        require(guard["checkedBy"], f"{guard['guardName']} should name checking evidence")

    migration = compatibility["migrationBoundary"]
    require(migration["automaticMigrationAllowed"] is False, "automatic migration must stay blocked")
    require(migration["explicitOperationRequired"] is True, "migration should require explicit operation")
    require(migration["migrationReceiptRequired"] is True, "migration should require receipt")
    require(migration["normalChecksRunMigrations"] is False, "normal checks must not run migrations")
    require(migration["historicalForecastRewriteAllowed"] is False, "migration must not rewrite history")

    boundary = compatibility["executionBoundary"]
    for key in [
        "postgresConnectionOpened",
        "postgresRuntimeImplemented",
        "hostedStorageClaimAllowed",
        "productionDatabaseOperationAllowed",
        "normalChecksRequireDatabase",
        "rawSqlExposedToAgents",
        "schemaMigrationExecuted",
        "credentialValuesStored",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = compatibility["summary"]
    require(summary["tableCount"] == len(REQUIRED_TABLES), "table count drifted")
    require(summary["scenarioCount"] == len(SCENARIO_NAMES), "scenario count drifted")
    require(summary["sqliteOnlyGuardCount"] == len(REQUIRED_SQLITE_ONLY_GUARDS), "guard count drifted")
    require(summary["postgresRuntimeImplemented"] is False, "summary should keep Postgres unimplemented")

    print("checked postgres compatibility")


if __name__ == "__main__":
    main()
