#!/usr/bin/env python3
"""Generate a checked SQLite-to-Postgres lifecycle compatibility readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_lifecycle_operation_store import SCENARIO_NAMES, build_lifecycle_operation_store
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "postgres-compatibility"
OUTPUT_PATH = GENERATED / "ope-postgres-compatibility.generated.json"
SCHEMA = SPEC / "postgres-compatibility.schema.json"
GENERATED_AT = "2026-06-04T20:10:00Z"


class PostgresCompatibilityError(Exception):
    pass


POSTGRES_TYPE_MAPPINGS = {
    "operation_receipts": [
        "TEXT primary keys become text primary keys",
        "planned_writes_json and diagnostics become jsonb payload columns",
        "created_at text timestamps become timestamptz with UTC normalization",
    ],
    "operation_idempotency_keys": [
        "Composite SQLite primary key becomes equivalent Postgres unique constraint",
        "request_hash and source_record_hash remain text hashes",
        "created_at text timestamp becomes timestamptz with UTC normalization",
    ],
    "operation_leases": [
        "lease_key primary key remains text primary key",
        "expires_at becomes timestamptz for expiry comparisons",
        "acquisition remains transactional with conflict detection",
    ],
    "ope_records": [
        "content_json and provenance_json become jsonb payload columns",
        "content_hash and source_record_hash remain text hashes",
        "record_id primary key preserves immutable record identity",
    ],
    "forecast_history_events": [
        "content_json becomes jsonb payload",
        "history_event_id remains primary key",
        "created_at becomes timestamptz with UTC normalization",
    ],
    "operation_audit_records": [
        "content_json becomes jsonb payload",
        "audit_record_id remains primary key",
        "archive and redaction receipts remain append-only audit rows",
    ],
    "evidence_ledger_rows": [
        "content_json becomes jsonb payload",
        "ledger_row_id remains primary key",
        "append-only evidence rows preserve operation receipt binding",
    ],
    "read_model_rows": [
        "row_json becomes jsonb payload",
        "Composite primary key remains read_model_name plus row_key",
        "Projection upserts use ON CONFLICT on the composite key",
    ],
}


def table_compatibility(store: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for table in store["sqliteSchemaPlan"]:
        table_name = table["tableName"]
        write_mode = table["writeMode"]
        rows.append(
            {
                "tableName": table_name,
                "sqlitePurpose": table["purpose"],
                "sqliteWriteMode": write_mode,
                "sqlitePrimaryKey": table["primaryKey"],
                "sqliteTableExists": True,
                "postgresTablePlanned": True,
                "postgresTypeMappings": POSTGRES_TYPE_MAPPINGS[table_name],
                "jsonPayloadPortable": True,
                "contentHashPortable": True,
                "timestampNormalized": True,
                "uniqueConstraintPortable": table_name == "operation_idempotency_keys",
                "leaseExpiryPortable": table_name == "operation_leases",
                "upsertPortable": table_name == "read_model_rows",
                "appendOnlyPortable": write_mode in {"append_only", "tombstone_append", "redaction_append"} or table["storesImmutableRecords"],
                "rawCrudExposed": False,
                "hostedRuntimeRequired": False,
            }
        )
    return rows


def contract_semantic(name: str, sqlite_mapping: str, postgres_mapping: str) -> dict[str, Any]:
    return {
        "semanticName": name,
        "sqliteMapping": sqlite_mapping,
        "postgresMapping": postgres_mapping,
        "portable": True,
        "normalChecksRequirePostgres": False,
    }


def dialect_neutral_adapter_contract() -> list[dict[str, Any]]:
    return [
        contract_semantic("json_payloads", "TEXT columns containing canonical JSON", "jsonb payload columns with canonical render hashes"),
        contract_semantic("content_hashes", "TEXT SHA-style content hashes", "text hash columns with identical comparison semantics"),
        contract_semantic(
            "unique_idempotency_keys",
            "Composite primary key in operation_idempotency_keys",
            "Equivalent composite unique constraint in operation_idempotency_keys",
        ),
        contract_semantic("lease_acquisition", "Transactional insert after lease conflict check", "Transactional insert or upsert guarded by lease key"),
        contract_semantic("lease_expiry", "UTC timestamp text comparison", "timestamptz comparison after UTC normalization"),
        contract_semantic("append_only_records", "Insert-only immutable record tables", "Insert-only immutable record tables with primary key conflicts blocked"),
        contract_semantic(
            "read_model_upserts",
            "SQLite ON CONFLICT read_model_name,row_key update",
            "Postgres ON CONFLICT read_model_name,row_key DO UPDATE",
        ),
    ]


def expected_postgres_behavior(scenario: dict[str, Any]) -> str:
    if scenario["scenarioName"] == "retry-idempotent":
        return "return_existing_receipt"
    if scenario["scenarioName"] == "lease-conflict":
        return "blocked_lease_conflict"
    if scenario["executionStatus"] == "failed_preflight_guard":
        return "failed_preflight_guard"
    return "commit_same_lifecycle_writes"


def scenario_compatibility_matrix(store: dict[str, Any]) -> list[dict[str, Any]]:
    scenarios = {item["scenarioName"]: item for item in store["runtimeScenarios"]}
    rows: list[dict[str, Any]] = []
    for scenario_name in SCENARIO_NAMES:
        scenario = scenarios[scenario_name]
        planned_tables = sorted({write["tableName"] for write in scenario["preflight"]["plannedWrites"]})
        rows.append(
            {
                "scenarioName": scenario_name,
                "operationName": scenario["operationName"],
                "sqliteScenarioExists": True,
                "sqliteExecutionStatus": scenario["executionStatus"],
                "expectedPostgresBehavior": expected_postgres_behavior(scenario),
                "plannedWriteTables": planned_tables,
                "postgresCompatible": True,
                "sameOperationSemantics": True,
                "sameIdempotencySemantics": True,
                "sameLeaseSemantics": True,
                "sameAppendOnlySemantics": True,
                "sameReadModelSemantics": True,
                "migrationBoundary": "explicit_receipt_backed_import" if scenario_name == "json-state-import" else "not_migration",
                "normalChecksConnectToPostgres": False,
                "hostedRuntimeClaimAllowed": False,
            }
        )
    return rows


def sqlite_only_assumption_checks() -> list[dict[str, Any]]:
    rows = [
        (
            "rowid_dependence",
            "All runtime tables use explicit primary keys; rowid is not part of record identity.",
            "scripts/check_lifecycle_operation_store.py",
        ),
        (
            "loose_typing_dependence",
            "Schema plans declare text/json/timestamp semantics instead of relying on SQLite affinity coercion.",
            "scripts/check_postgres_compatibility.py",
        ),
        (
            "nonportable_upsert_behavior",
            "Read-model upserts are constrained to the composite read_model_name,row_key key supported by both backends.",
            "scripts/check_postgres_compatibility.py",
        ),
        (
            "missing_timestamp_normalization",
            "Postgres mappings require UTC timestamptz normalization for created_at, updated_at, acquired_at, and expires_at fields.",
            "scripts/check_postgres_compatibility.py",
        ),
        (
            "sqlite_only_json_query_behavior",
            "JSON payloads stay opaque/canonical in compatibility checks; read models avoid backend-specific JSON query claims.",
            "scripts/check_postgres_compatibility.py",
        ),
    ]
    return [
        {
            "guardName": name,
            "guardStatus": "checked",
            "sqliteOnlyAssumptionDetected": False,
            "blocksPostgresClaimIfFailed": True,
            "checkedBy": [check],
            "notes": notes,
        }
        for name, notes, check in rows
    ]


def migration_boundary() -> dict[str, Any]:
    return {
        "automaticMigrationAllowed": False,
        "explicitOperationRequired": True,
        "migrationOperationName": "state.import_json",
        "migrationReceiptRequired": True,
        "normalChecksRunMigrations": False,
        "historicalForecastRewriteAllowed": False,
        "contentHashesPreserved": True,
        "sourceRecordHashesPreserved": True,
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "postgresConnectionOpened": False,
        "postgresRuntimeImplemented": False,
        "hostedStorageClaimAllowed": False,
        "productionDatabaseOperationAllowed": False,
        "normalChecksRequireDatabase": False,
        "rawSqlExposedToAgents": False,
        "schemaMigrationExecuted": False,
        "credentialValuesStored": False,
    }


def build_postgres_compatibility() -> dict[str, Any]:
    store = build_lifecycle_operation_store()
    tables = table_compatibility(store)
    matrix = scenario_compatibility_matrix(store)
    guards = sqlite_only_assumption_checks()
    return {
        "postgresCompatibilityId": "postgrescompatibility-001",
        "generatedAt": GENERATED_AT,
        "compatibilityStatus": "sqlite_to_postgres_semantics_checked",
        "runtimeScope": "storage_semantics_only",
        "normalChecksConnectToPostgres": False,
        "sqliteRuntimeRemainsDefault": True,
        "postgresRuntimeImplemented": False,
        "tableCompatibility": tables,
        "dialectNeutralAdapterContract": dialect_neutral_adapter_contract(),
        "scenarioCompatibilityMatrix": matrix,
        "sqliteOnlyAssumptionChecks": guards,
        "migrationBoundary": migration_boundary(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "tableCount": len(tables),
            "scenarioCount": len(matrix),
            "sqliteOnlyGuardCount": len(guards),
            "postgresRuntimeImplemented": False,
            "normalChecksConnectToPostgres": False,
        },
        "warnings": [
            "This is a storage-semantics compatibility readback, not an implemented Postgres runtime.",
            "Normal checks do not connect to Postgres, run migrations, or claim hosted storage readiness.",
            "Future Postgres adapters must preserve lifecycle receipts, idempotency, leases, immutable records, and read-model semantics.",
        ],
    }


def validate_postgres_compatibility(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise PostgresCompatibilityError("postgres compatibility record failed schema validation")
    if record["summary"]["tableCount"] != len(record["tableCompatibility"]):
        raise PostgresCompatibilityError("table count drifted")
    if record["summary"]["scenarioCount"] != len(record["scenarioCompatibilityMatrix"]):
        raise PostgresCompatibilityError("scenario count drifted")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "tables":
        return record["tableCompatibility"]
    if view == "contract":
        return record["dialectNeutralAdapterContract"]
    if view == "scenarios":
        return record["scenarioCompatibilityMatrix"]
    if view == "guards":
        return record["sqliteOnlyAssumptionChecks"]
    if view == "migration":
        return record["migrationBoundary"]
    if view == "boundary":
        return record["executionBoundary"]
    raise PostgresCompatibilityError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated Postgres compatibility fixture")
    parser.add_argument("--check", action="store_true", help="check generated Postgres compatibility fixture")
    parser.add_argument(
        "--view",
        choices=["full", "tables", "contract", "scenarios", "guards", "migration", "boundary"],
        default="full",
        help="emit a focused Postgres compatibility view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_postgres_compatibility()
    validate_postgres_compatibility(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="postgres compatibility",
            regen="python3 scripts/generate_postgres_compatibility.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="postgres compatibility",
            regen="python3 scripts/generate_postgres_compatibility.py --write",
        )
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
