#!/usr/bin/env python3
"""SQLite runtime helpers for lifecycle operation store checks."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import sqlite3
from typing import Any

from ope_fixtures import render_json


DEFAULT_NOW = "2026-06-03T00:30:00Z"

LEASED_OPERATIONS = {
    "campaign.create_run",
    "forecast.create",
    "resolution.record",
    "score.create",
    "evidence.append",
    "pre_calibration.bind",
    "method.apply",
    "method.rollback",
    "state.import_json",
}

DELETE_REPLACEMENT_OPERATIONS = {
    "question.cancel",
    "question.annul",
    "record.archive",
    "record.redact",
}

SQLITE_SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS operation_receipts (
        operation_receipt_id TEXT PRIMARY KEY,
        operation_name TEXT NOT NULL,
        operation_status TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        campaign_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        forecast_id TEXT NOT NULL,
        caller_id TEXT NOT NULL,
        source_record_hash TEXT NOT NULL,
        target_record_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        planned_writes_json TEXT NOT NULL,
        blocking_guards_json TEXT NOT NULL,
        lease_key TEXT NOT NULL,
        recovery_path TEXT NOT NULL,
        claim_boundary_json TEXT NOT NULL,
        message TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_idempotency_keys (
        operation_name TEXT NOT NULL,
        campaign_id TEXT NOT NULL,
        run_id TEXT NOT NULL,
        forecast_id TEXT NOT NULL,
        caller_id TEXT NOT NULL,
        idempotency_key TEXT NOT NULL,
        source_record_hash TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (
            operation_name,
            campaign_id,
            run_id,
            forecast_id,
            caller_id,
            idempotency_key,
            source_record_hash
        )
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_leases (
        lease_key TEXT PRIMARY KEY,
        operation_name TEXT NOT NULL,
        resource_id TEXT NOT NULL,
        owner_id TEXT NOT NULL,
        acquired_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ope_records (
        record_id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        schema_file TEXT NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        source_record_hash TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        provenance_json TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS forecast_history_events (
        history_event_id TEXT PRIMARY KEY,
        forecast_id TEXT NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        source_record_hash TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS operation_audit_records (
        audit_record_id TEXT PRIMARY KEY,
        record_type TEXT NOT NULL,
        target_record_id TEXT NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS evidence_ledger_rows (
        ledger_row_id TEXT PRIMARY KEY,
        forecast_id TEXT NOT NULL,
        content_json TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        operation_receipt_id TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS read_model_rows (
        read_model_name TEXT NOT NULL,
        row_key TEXT NOT NULL,
        row_json TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        PRIMARY KEY (read_model_name, row_key)
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_operation_receipts_status
        ON operation_receipts(operation_status, operation_name)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_ope_records_type
        ON ope_records(record_type, created_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_read_model_rows_name
        ON read_model_rows(read_model_name)
    """,
]


class LifecycleOperationRuntimeError(Exception):
    pass


def claim_boundary() -> dict[str, bool]:
    return {
        "createsQualityClaim": False,
        "allowsPostOutcomeRewrite": False,
        "allowsSilentDelete": False,
        "allowsRawCrud": False,
    }


def sqlite_schema_plan() -> list[dict[str, Any]]:
    return [
        sqlite_table(
            "operation_receipts",
            "Append-only receipt log for effectful lifecycle operation attempts and commits.",
            ["operation_receipt_id"],
            "append_only",
            stores_immutable_records=False,
            mutable_projection=False,
        ),
        sqlite_table(
            "operation_idempotency_keys",
            "Unique retry keys keyed by operation, campaign/run/forecast, caller key, and source hash.",
            ["operation_name", "campaign_id", "run_id", "forecast_id", "caller_id", "idempotency_key", "source_record_hash"],
            "insert_once",
            stores_immutable_records=False,
            mutable_projection=False,
        ),
        sqlite_table(
            "operation_leases",
            "Short coordination leases for operations that can race across agents.",
            ["lease_key"],
            "upsert_expiring_lease",
            stores_immutable_records=False,
            mutable_projection=True,
        ),
        sqlite_table(
            "ope_records",
            "Immutable JSON record payloads and hashes for core OPE records.",
            ["record_id"],
            "insert_once",
            stores_immutable_records=True,
            mutable_projection=False,
        ),
        sqlite_table(
            "forecast_history_events",
            "Append-only forecast history events rather than mutable forecast rewrites.",
            ["history_event_id"],
            "append_only",
            stores_immutable_records=True,
            mutable_projection=False,
        ),
        sqlite_table(
            "operation_audit_records",
            "Archive, redaction, annulment, cancellation, and method-update audit records.",
            ["audit_record_id"],
            "append_only",
            stores_immutable_records=True,
            mutable_projection=False,
        ),
        sqlite_table(
            "evidence_ledger_rows",
            "Append-only comparable evidence rows for later calibration and track-record readbacks.",
            ["ledger_row_id"],
            "append_only",
            stores_immutable_records=True,
            mutable_projection=False,
        ),
        sqlite_table(
            "read_model_rows",
            "Rebuildable projections for agent queues, status, calibration, and recovery readbacks.",
            ["read_model_name", "row_key"],
            "projection_upsert",
            stores_immutable_records=False,
            mutable_projection=True,
        ),
    ]


def sqlite_table(
    table_name: str,
    purpose: str,
    primary_key: list[str],
    write_mode: str,
    *,
    stores_immutable_records: bool,
    mutable_projection: bool,
) -> dict[str, Any]:
    return {
        "tableName": table_name,
        "purpose": purpose,
        "primaryKey": primary_key,
        "writeMode": write_mode,
        "postgresCompatible": True,
        "storesImmutableRecords": stores_immutable_records,
        "mutableProjection": mutable_projection,
        "rawCrudExposed": False,
    }


def open_sqlite(path: str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(path or ":memory:")
    conn.row_factory = sqlite3.Row
    initialize_sqlite(conn)
    return conn


def initialize_sqlite(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    for statement in SQLITE_SCHEMA_STATEMENTS:
        conn.execute(statement)
    conn.commit()


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def content_hash(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def rendered_content_hash(data: Any) -> str:
    return hashlib.sha256(render_json(data).encode("utf-8")).hexdigest()


def request_hash(request: dict[str, Any]) -> str:
    excluded = {"operationReceiptId", "scenarioName", "scenarioId"}
    canonical = {key: value for key, value in request.items() if key not in excluded}
    return content_hash(canonical)


def idempotency_fields(request: dict[str, Any]) -> tuple[str, str, str, str, str, str, str]:
    return (
        request["operationName"],
        request["campaignId"],
        request["runId"],
        request["forecastId"],
        request["callerId"],
        request["idempotencyKey"],
        request["sourceRecordHash"],
    )


def lease_key(request: dict[str, Any]) -> str:
    resource_id = request.get("leaseResourceId") or request["runId"] or request["forecastId"] or request["targetRecordId"]
    return f"{request['operationName']}:{resource_id}"


def lease_expires_at(now: str, seconds: int) -> str:
    parsed = datetime.fromisoformat(now.replace("Z", "+00:00"))
    expires = parsed + timedelta(seconds=seconds)
    return expires.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def planned_writes(request: dict[str, Any]) -> list[dict[str, str]]:
    receipt_write = {
        "tableName": "operation_receipts",
        "recordType": "operation_receipt",
        "recordId": request["operationReceiptId"],
        "writeMode": "append_only",
    }
    operation_name = request["operationName"]
    if operation_name == "forecast.create":
        return [
            receipt_write,
            {
                "tableName": "ope_records",
                "recordType": "forecast_question",
                "recordId": request.get("questionRecordId", "question-2101"),
                "writeMode": "insert_once",
            },
            {
                "tableName": "ope_records",
                "recordType": "evidence_packet",
                "recordId": request.get("evidencePacketId", "evidence-2101"),
                "writeMode": "insert_once",
            },
            {
                "tableName": "ope_records",
                "recordType": "forecast_artifact",
                "recordId": request["targetRecordId"],
                "writeMode": "insert_once",
            },
            {
                "tableName": "forecast_history_events",
                "recordType": "forecast_history",
                "recordId": request.get("historyRecordId", "forecasthistory-2101"),
                "writeMode": "append_only",
            },
        ]
    if operation_name == "resolution.record":
        return [
            receipt_write,
            {
                "tableName": "ope_records",
                "recordType": "resolution_record",
                "recordId": request["targetRecordId"],
                "writeMode": "insert_once",
            },
        ]
    if operation_name == "score.create":
        return [
            receipt_write,
            {
                "tableName": "ope_records",
                "recordType": "scoring_report",
                "recordId": request["targetRecordId"],
                "writeMode": "insert_once",
            },
        ]
    if operation_name == "evidence.append":
        return [
            receipt_write,
            {
                "tableName": "evidence_ledger_rows",
                "recordType": "evidence_ledger_row",
                "recordId": request["targetRecordId"],
                "writeMode": "append_only",
            },
        ]
    if operation_name == "pre_calibration.bind":
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "pre_calibration_binding",
                "recordId": request.get("auditRecordId", "precalibrationbinding-2101"),
                "writeMode": "prospective_binding",
            },
        ]
    if operation_name in {"method.apply", "method.rollback"}:
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "method_update_audit",
                "recordId": request.get("auditRecordId", "methodaudit-2101"),
                "writeMode": "prospective_binding",
            },
        ]
    if operation_name == "state.import_json":
        migration_writes = request.get("migrationWrites")
        if not isinstance(migration_writes, list) or not migration_writes:
            raise LifecycleOperationRuntimeError("state.import_json requires migrationWrites")
        return [receipt_write, *migration_writes]
    if operation_name == "record.archive":
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "archive_tombstone",
                "recordId": request.get("auditRecordId", "archive-2101"),
                "writeMode": "tombstone_append",
            },
        ]
    if operation_name == "record.redact":
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "redaction_receipt",
                "recordId": request.get("auditRecordId", "redaction-2101"),
                "writeMode": "redaction_append",
            },
        ]
    if operation_name in {"question.cancel", "question.annul"}:
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "archive_tombstone",
                "recordId": request.get("auditRecordId", "questionaudit-2101"),
                "writeMode": "append_only",
            },
        ]
    if operation_name == "forecast.recalculate":
        return [
            receipt_write,
            {
                "tableName": "forecast_history_events",
                "recordType": "forecast_history",
                "recordId": request.get("historyRecordId", "forecasthistory-2102"),
                "writeMode": "append_only",
            },
        ]
    if operation_name == "campaign.create_run":
        return [
            receipt_write,
            {
                "tableName": "operation_audit_records",
                "recordType": "operation_receipt",
                "recordId": request.get("auditRecordId", "campaignrun-2101"),
                "writeMode": "append_only",
            },
        ]
    raise LifecycleOperationRuntimeError(f"unsupported lifecycle operation: {operation_name}")


def blocking_guard(guard_id: str, status: str, blocks: bool, message: str) -> dict[str, Any]:
    return {
        "guardId": guard_id,
        "guardStatus": status,
        "blocksOperation": blocks,
        "message": message,
    }


def preflight_operation(conn: sqlite3.Connection, request: dict[str, Any], *, now: str = DEFAULT_NOW) -> dict[str, Any]:
    operation_name = request["operationName"]
    if not request.get("idempotencyKey"):
        raise LifecycleOperationRuntimeError("idempotencyKey is required")
    req_hash = request_hash(request)
    writes = planned_writes(request)
    guards = [
        blocking_guard("lifecycleguard-001", "pass", False, "Operation is represented as a lifecycle operation, not raw CRUD."),
        blocking_guard("lifecycleguard-002", "pass", False, "Forecast artifacts and histories are append-only or insert-once."),
        blocking_guard("lifecycleguard-003", "pass", False, "Idempotency key is present and bound to source record hash."),
    ]
    status = "preflight_pass"
    idempotency_status = "new_key_available"
    recovery_path = request.get("recoveryPath", "retry_with_same_idempotency_key_or_inspect_receipt")

    existing_idempotency = conn.execute(
        """
        SELECT request_hash, operation_receipt_id
        FROM operation_idempotency_keys
        WHERE operation_name = ?
          AND campaign_id = ?
          AND run_id = ?
          AND forecast_id = ?
          AND caller_id = ?
          AND idempotency_key = ?
          AND source_record_hash = ?
        """,
        idempotency_fields(request),
    ).fetchone()
    if existing_idempotency is not None:
        if existing_idempotency["request_hash"] == req_hash:
            status = "idempotent_replay_available"
            idempotency_status = "return_existing_receipt"
            guards.append(
                blocking_guard(
                    "lifecycleguard-004",
                    "idempotent_repeat",
                    False,
                    "Matching idempotency key and request hash return the existing receipt without duplicate writes.",
                )
            )
        else:
            status = "blocked_idempotency_mismatch"
            idempotency_status = "block_mismatched_retry"
            recovery_path = "inspect_existing_receipt_or_choose_a_new_idempotency_key_for_a_new_operation"
            guards.append(
                blocking_guard(
                    "lifecycleguard-004",
                    "fail",
                    True,
                    "Idempotency key already exists with a different request hash.",
                )
            )

    requires_lease = operation_name in LEASED_OPERATIONS
    current_lease_key = lease_key(request) if requires_lease else ""
    lease_status = "not_required"
    lease_plan = {
        "requiresLease": requires_lease,
        "leaseKey": current_lease_key,
        "ownerId": request["callerId"] if requires_lease else "",
        "expiresAt": lease_expires_at(now, int(request.get("leaseSeconds", 120))) if requires_lease else "",
    }
    if requires_lease and status == "preflight_pass":
        existing_lease = conn.execute(
            "SELECT owner_id, expires_at FROM operation_leases WHERE lease_key = ?",
            (current_lease_key,),
        ).fetchone()
        if existing_lease and existing_lease["owner_id"] != request["callerId"] and existing_lease["expires_at"] > now:
            status = "blocked_lease_conflict"
            lease_status = "blocked_lease_conflict"
            recovery_path = "wait_for_lease_expiry_or_inspect_recovery_actions_read_model"
            guards.append(
                blocking_guard(
                    "lifecycleguard-005",
                    "fail",
                    True,
                    f"Lease is held by {existing_lease['owner_id']} until {existing_lease['expires_at']}.",
                )
            )
        else:
            lease_status = "available"
            guards.append(
                blocking_guard(
                    "lifecycleguard-005",
                    "pass",
                    False,
                    "Lease is available or already owned by this caller.",
                )
            )

    if request.get("forcePreflightBlock") and status == "preflight_pass":
        status = "failed_preflight_guard"
        recovery_path = request.get("recoveryPath", "fix_blocking_guard_and_retry_with_same_idempotency_key")
        guards.append(
            blocking_guard(
                "lifecycleguard-006",
                "fail",
                True,
                str(request["forcePreflightBlock"]),
            )
        )

    return {
        "operationName": operation_name,
        "preflightStatus": status,
        "idempotencyStatus": idempotency_status,
        "idempotencyKey": request["idempotencyKey"],
        "requestHash": req_hash,
        "existingReceiptId": existing_idempotency["operation_receipt_id"] if existing_idempotency else "",
        "plannedWrites": writes,
        "blockingGuards": guards,
        "leasePlan": lease_plan,
        "leaseStatus": lease_status,
        "recoveryPath": recovery_path,
        "claimBoundary": claim_boundary(),
    }


def execute_operation(conn: sqlite3.Connection, request: dict[str, Any], *, now: str = DEFAULT_NOW) -> dict[str, Any]:
    before = table_counts(conn)
    preflight = preflight_operation(conn, request, now=now)

    if preflight["preflightStatus"] == "idempotent_replay_available":
        after = table_counts(conn)
        return execution_result(
            request,
            preflight,
            operation_status="idempotent_replay",
            receipt_id=preflight["existingReceiptId"],
            before=before,
            after=after,
            message="Safe retry returned the existing receipt without duplicate immutable writes.",
        )

    if preflight["preflightStatus"] in {
        "blocked_idempotency_mismatch",
        "blocked_lease_conflict",
        "failed_preflight_guard",
    }:
        with conn:
            receipt_id = request["operationReceiptId"]
            insert_receipt(conn, request, preflight, receipt_id=receipt_id, status=preflight["preflightStatus"], now=now)
            update_read_models(conn, request, receipt_id, preflight["preflightStatus"], now=now)
        after = table_counts(conn)
        return execution_result(
            request,
            preflight,
            operation_status=preflight["preflightStatus"],
            receipt_id=request["operationReceiptId"],
            before=before,
            after=after,
            message="Operation was blocked before mutation and recorded for recovery readback.",
        )

    with conn:
        receipt_id = request["operationReceiptId"]
        if request["operationName"] in LEASED_OPERATIONS:
            acquire_lease(conn, request, receipt_id, now=now)
        insert_receipt(conn, request, preflight, receipt_id=receipt_id, status="committed", now=now)
        insert_idempotency(conn, request, preflight, receipt_id=receipt_id, now=now)
        insert_planned_records(conn, request, preflight, receipt_id=receipt_id, now=now)
        update_read_models(conn, request, receipt_id, "committed", now=now)
    after = table_counts(conn)
    return execution_result(
        request,
        preflight,
        operation_status="committed",
        receipt_id=request["operationReceiptId"],
        before=before,
        after=after,
        message="Operation committed through SQLite adapter.",
    )


def acquire_lease(conn: sqlite3.Connection, request: dict[str, Any], receipt_id: str, *, now: str) -> None:
    key = lease_key(request)
    conn.execute(
        "DELETE FROM operation_leases WHERE lease_key = ? AND (owner_id = ? OR expires_at <= ?)",
        (key, request["callerId"], now),
    )
    conn.execute(
        """
        INSERT INTO operation_leases (
            lease_key,
            operation_name,
            resource_id,
            owner_id,
            acquired_at,
            expires_at,
            operation_receipt_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            request["operationName"],
            request.get("leaseResourceId") or request["runId"],
            request["callerId"],
            now,
            lease_expires_at(now, int(request.get("leaseSeconds", 120))),
            receipt_id,
        ),
    )


def insert_receipt(
    conn: sqlite3.Connection,
    request: dict[str, Any],
    preflight: dict[str, Any],
    *,
    receipt_id: str,
    status: str,
    now: str,
) -> None:
    conn.execute(
        """
        INSERT INTO operation_receipts (
            operation_receipt_id,
            operation_name,
            operation_status,
            idempotency_key,
            request_hash,
            campaign_id,
            run_id,
            forecast_id,
            caller_id,
            source_record_hash,
            target_record_id,
            created_at,
            planned_writes_json,
            blocking_guards_json,
            lease_key,
            recovery_path,
            claim_boundary_json,
            message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            receipt_id,
            request["operationName"],
            status,
            request["idempotencyKey"],
            preflight["requestHash"],
            request["campaignId"],
            request["runId"],
            request["forecastId"],
            request["callerId"],
            request["sourceRecordHash"],
            request["targetRecordId"],
            now,
            render_json(preflight["plannedWrites"]),
            render_json(preflight["blockingGuards"]),
            preflight["leasePlan"]["leaseKey"],
            preflight["recoveryPath"],
            render_json(preflight["claimBoundary"]),
            f"{request['operationName']} {status}",
        ),
    )


def insert_idempotency(
    conn: sqlite3.Connection,
    request: dict[str, Any],
    preflight: dict[str, Any],
    *,
    receipt_id: str,
    now: str,
) -> None:
    conn.execute(
        """
        INSERT INTO operation_idempotency_keys (
            operation_name,
            campaign_id,
            run_id,
            forecast_id,
            caller_id,
            idempotency_key,
            source_record_hash,
            request_hash,
            operation_receipt_id,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (*idempotency_fields(request), preflight["requestHash"], receipt_id, now),
    )


def insert_planned_records(
    conn: sqlite3.Connection,
    request: dict[str, Any],
    preflight: dict[str, Any],
    *,
    receipt_id: str,
    now: str,
) -> None:
    for write in preflight["plannedWrites"]:
        if write["tableName"] == "operation_receipts":
            continue
        payload = record_payload(request, write, receipt_id=receipt_id, now=now)
        payload_hash = rendered_content_hash(payload)
        if write["tableName"] == "ope_records":
            conn.execute(
                """
                INSERT INTO ope_records (
                    record_id,
                    record_type,
                    schema_file,
                    content_json,
                    content_hash,
                    source_record_hash,
                    operation_receipt_id,
                    created_at,
                    provenance_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    write["recordId"],
                    write["recordType"],
                    schema_file_for_record_type(write["recordType"]),
                    render_json(payload),
                    payload_hash,
                    request["sourceRecordHash"],
                    receipt_id,
                    now,
                    render_json({"callerId": request["callerId"], "operationName": request["operationName"]}),
                ),
            )
        elif write["tableName"] == "forecast_history_events":
            conn.execute(
                """
                INSERT INTO forecast_history_events (
                    history_event_id,
                    forecast_id,
                    content_json,
                    content_hash,
                    source_record_hash,
                    operation_receipt_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    write["recordId"],
                    request["forecastId"],
                    render_json(payload),
                    payload_hash,
                    request["sourceRecordHash"],
                    receipt_id,
                    now,
                ),
            )
        elif write["tableName"] == "operation_audit_records":
            conn.execute(
                """
                INSERT INTO operation_audit_records (
                    audit_record_id,
                    record_type,
                    target_record_id,
                    content_json,
                    content_hash,
                    operation_receipt_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    write["recordId"],
                    write["recordType"],
                    request["targetRecordId"],
                    render_json(payload),
                    payload_hash,
                    receipt_id,
                    now,
                ),
            )
        elif write["tableName"] == "evidence_ledger_rows":
            conn.execute(
                """
                INSERT INTO evidence_ledger_rows (
                    ledger_row_id,
                    forecast_id,
                    content_json,
                    content_hash,
                    operation_receipt_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    write["recordId"],
                    request["forecastId"],
                    render_json(payload),
                    payload_hash,
                    receipt_id,
                    now,
                ),
            )
        elif write["tableName"] == "read_model_rows":
            put_read_model(
                conn,
                write["recordType"],
                write["recordId"],
                payload,
                now=now,
            )
        else:
            raise LifecycleOperationRuntimeError(f"unsupported write table: {write['tableName']}")


def record_payload(request: dict[str, Any], write: dict[str, str], *, receipt_id: str, now: str) -> dict[str, Any]:
    record_payloads = request.get("recordPayloads", {})
    if write["recordId"] in record_payloads:
        payload = record_payloads[write["recordId"]]
        if isinstance(payload, dict):
            return payload
    if write["recordType"] in record_payloads:
        payload = record_payloads[write["recordType"]]
        if isinstance(payload, dict):
            return payload
    return {
        "recordId": write["recordId"],
        "recordType": write["recordType"],
        "operationName": request["operationName"],
        "operationReceiptId": receipt_id,
        "campaignId": request["campaignId"],
        "runId": request["runId"],
        "forecastId": request["forecastId"],
        "targetRecordId": request["targetRecordId"],
        "createdAt": now,
        "sourceRecordHash": request["sourceRecordHash"],
        "payload": request.get("payload", {}),
        "claimBoundary": claim_boundary(),
    }


def schema_file_for_record_type(record_type: str) -> str:
    return {
        "forecast_question": "spec/forecast-question.schema.json",
        "evidence_packet": "spec/evidence-packet.schema.json",
        "forecast_artifact": "spec/forecast-artifact.schema.json",
        "forecast_history": "spec/forecast-history.schema.json",
        "resolution_record": "spec/resolution-record.schema.json",
        "scoring_report": "spec/scoring-report.schema.json",
        "calibration_summary": "spec/calibration-summary.schema.json",
        "pre_calibration_binding": "spec/prediction-campaign-pre-calibration.schema.json",
        "method_update_audit": "spec/prediction-campaign-method-update-action.schema.json",
        "evidence_ledger_row": "spec/prediction-campaign-evidence-ledger.schema.json",
        "run_state_projection": "spec/lifecycle-operation.schema.json",
        "campaign_state_projection": "spec/lifecycle-operation.schema.json",
        "method_binding_state": "spec/lifecycle-operation.schema.json",
        "json_state_migration_receipt": "spec/lifecycle-operation.schema.json",
        "operation_receipt": "spec/lifecycle-operation.schema.json",
        "archive_tombstone": "spec/lifecycle-operation.schema.json",
        "redaction_receipt": "spec/lifecycle-operation.schema.json",
    }.get(record_type, "spec/lifecycle-operation.schema.json")


def update_read_models(
    conn: sqlite3.Connection,
    request: dict[str, Any],
    receipt_id: str,
    operation_status: str,
    *,
    now: str,
) -> None:
    campaign_id = request["campaignId"]
    put_read_model(
        conn,
        "campaign_status",
        campaign_id,
        {
            "campaignId": campaign_id,
            "lastOperationName": request["operationName"],
            "lastOperationReceiptId": receipt_id,
            "lastOperationStatus": operation_status,
            "rawCrudExposed": False,
        },
        now=now,
    )
    if request["operationName"] == "forecast.create" and operation_status == "committed":
        put_read_model(
            conn,
            "unresolved_forecasts",
            request["forecastId"],
            {
                "forecastId": request["forecastId"],
                "campaignId": campaign_id,
                "status": "waiting_resolution",
                "forecastArtifactMutable": False,
                "historyRewriteAllowed": False,
            },
            now=now,
        )
        put_read_model(
            conn,
            "next_due_forecast",
            campaign_id,
            {
                "campaignId": campaign_id,
                "nextAction": "no_duplicate_due_run_for_same_idempotency_key",
                "lastForecastReceiptId": receipt_id,
            },
            now=now,
        )
    if request["operationName"] in {"record.archive", "record.redact", "question.cancel", "question.annul"}:
        put_read_model(
            conn,
            "append_readiness",
            request["targetRecordId"],
            {
                "targetRecordId": request["targetRecordId"],
                "operationName": request["operationName"],
                "activeProjectionState": "removed_from_active_view",
                "physicalDeletePerformed": False,
                "auditReceiptId": receipt_id,
            },
            now=now,
        )
    if request["operationName"] in {"pre_calibration.bind", "method.apply", "method.rollback"}:
        put_read_model(
            conn,
            "calibration_status",
            campaign_id,
            {
                "campaignId": campaign_id,
                "methodOperation": request["operationName"],
                "prospectiveOnly": True,
                "preCalibrationBinding": request["operationName"] == "pre_calibration.bind",
                "historicalForecastRewriteCount": 0,
                "operationReceiptId": receipt_id,
            },
            now=now,
        )
        put_read_model(
            conn,
            "track_record_progress",
            campaign_id,
            {
                "campaignId": campaign_id,
                "methodOperation": request["operationName"],
                "qualityClaimAllowed": False,
                "preCalibrationBinding": request["operationName"] == "pre_calibration.bind",
                "sampleSizeChangedByMethodRollback": False,
            },
            now=now,
        )
    if operation_status != "committed":
        put_read_model(
            conn,
            "failed_operations",
            receipt_id,
            {
                "operationReceiptId": receipt_id,
                "operationName": request["operationName"],
                "operationStatus": operation_status,
                "recoveryCategory": recovery_category(operation_status),
            },
            now=now,
        )
        put_read_model(
            conn,
            "recovery_actions",
            receipt_id,
            {
                "operationReceiptId": receipt_id,
                "operationName": request["operationName"],
                "nextSafeAction": recovery_action(operation_status),
                "claimBoundary": claim_boundary(),
            },
            now=now,
        )
    if request["operationName"] == "resolution.record":
        put_read_model(
            conn,
            "due_resolution_jobs",
            request["forecastId"],
            {
                "forecastId": request["forecastId"],
                "resolutionStatus": operation_status,
                "operationReceiptId": receipt_id,
            },
            now=now,
        )
    if request["operationName"] == "score.create" and operation_status == "committed":
        put_read_model(
            conn,
            "append_readiness",
            request["targetRecordId"],
            {
                "campaignId": campaign_id,
                "runId": request["runId"],
                "forecastId": request["forecastId"],
                "scoringReportId": request["targetRecordId"],
                "appendDecision": "review_scored_or_excluded_row_before_append",
                "operationReceiptId": receipt_id,
            },
            now=now,
        )
    if request["operationName"] == "evidence.append" and operation_status == "committed":
        put_read_model(
            conn,
            "append_readiness",
            request["targetRecordId"],
            {
                "campaignId": campaign_id,
                "runId": request["runId"],
                "forecastId": request["forecastId"],
                "ledgerRowId": request["targetRecordId"],
                "appendDecision": "already_appended_or_duplicate_check_before_retry",
                "operationReceiptId": receipt_id,
            },
            now=now,
        )
        put_read_model(
            conn,
            "calibration_status",
            campaign_id,
            {
                "campaignId": campaign_id,
                "lastLedgerOperationReceiptId": receipt_id,
                "sampleSizeChangedByAppend": True,
                "qualityClaimAllowed": False,
            },
            now=now,
        )
        put_read_model(
            conn,
            "track_record_progress",
            campaign_id,
            {
                "campaignId": campaign_id,
                "lastLedgerOperationReceiptId": receipt_id,
                "trackRecordProgressChangedByAppend": True,
                "qualityClaimAllowed": False,
            },
            now=now,
        )
    if request["operationName"] == "state.import_json":
        put_read_model(
            conn,
            "recovery_actions",
            receipt_id,
            {
                "operationReceiptId": receipt_id,
                "operationName": request["operationName"],
                "nextSafeAction": "continue_with_sqlite_read_models_after_hash_preserving_import",
                "claimBoundary": claim_boundary(),
            },
            now=now,
        )


def put_read_model(
    conn: sqlite3.Connection,
    read_model_name: str,
    row_key: str,
    row: dict[str, Any],
    *,
    now: str,
) -> None:
    conn.execute(
        """
        INSERT INTO read_model_rows (read_model_name, row_key, row_json, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(read_model_name, row_key) DO UPDATE SET
            row_json = excluded.row_json,
            updated_at = excluded.updated_at
        """,
        (read_model_name, row_key, render_json(row), now),
    )


def recovery_category(operation_status: str) -> str:
    if operation_status == "blocked_lease_conflict":
        return "lease_conflict"
    if operation_status == "blocked_idempotency_mismatch":
        return "idempotency_mismatch"
    return "failed_preflight_guard"


def recovery_action(operation_status: str) -> str:
    if operation_status == "blocked_lease_conflict":
        return "wait_for_lease_expiry_then_preflight_again"
    if operation_status == "blocked_idempotency_mismatch":
        return "inspect_existing_receipt_before_new_operation"
    return "fix_blocking_guard_then_retry_same_idempotency_key"


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    tables = [
        "operation_receipts",
        "operation_idempotency_keys",
        "operation_leases",
        "ope_records",
        "forecast_history_events",
        "operation_audit_records",
        "evidence_ledger_rows",
        "read_model_rows",
    ]
    return {table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]) for table in tables}


def read_model_names(conn: sqlite3.Connection, before: dict[str, int] | None = None) -> list[str]:
    rows = conn.execute("SELECT DISTINCT read_model_name FROM read_model_rows ORDER BY read_model_name").fetchall()
    return [str(row["read_model_name"]) for row in rows]


def execution_result(
    request: dict[str, Any],
    preflight: dict[str, Any],
    *,
    operation_status: str,
    receipt_id: str,
    before: dict[str, int],
    after: dict[str, int],
    message: str,
) -> dict[str, Any]:
    records_inserted = (
        after["ope_records"]
        + after["forecast_history_events"]
        + after["operation_audit_records"]
        + after["evidence_ledger_rows"]
        - before["ope_records"]
        - before["forecast_history_events"]
        - before["operation_audit_records"]
        - before["evidence_ledger_rows"]
    )
    result = {
        "operationName": request["operationName"],
        "operationReceiptId": receipt_id,
        "operationStatus": operation_status,
        "preflight": preflight,
        "tableCountsBefore": before,
        "tableCountsAfter": after,
        "sqliteWrites": {
            "operationReceiptsWritten": after["operation_receipts"] - before["operation_receipts"],
            "idempotencyKeysWritten": after["operation_idempotency_keys"] - before["operation_idempotency_keys"],
            "leasesWritten": after["operation_leases"] - before["operation_leases"],
            "immutableRecordsInserted": records_inserted,
            "auditRecordsInserted": after["operation_audit_records"] - before["operation_audit_records"],
            "readModelRowsWritten": after["read_model_rows"] - before["read_model_rows"],
            "physicalDeletes": 0,
            "rawCrudExposed": False,
            "historyRewriteCount": 0,
        },
        "payloadHashBindings": payload_hash_bindings(request, preflight, receipt_id=receipt_id),
        "message": message,
    }
    if "migrationImportSummary" in request:
        result["migrationImportSummary"] = request["migrationImportSummary"]
    return result


def payload_hash_bindings(
    request: dict[str, Any],
    preflight: dict[str, Any],
    *,
    receipt_id: str,
) -> list[dict[str, Any]]:
    expected_hashes = request.get("recordContentHashes", {})
    bindings = []
    for write in preflight["plannedWrites"]:
        if write["tableName"] == "operation_receipts":
            continue
        payload = record_payload(request, write, receipt_id=receipt_id, now=DEFAULT_NOW)
        sqlite_hash = rendered_content_hash(payload)
        source_hash = expected_hashes.get(write["recordId"]) or expected_hashes.get(write["recordType"]) or sqlite_hash
        bindings.append(
            {
                "recordType": write["recordType"],
                "recordId": write["recordId"],
                "sourceContentHash": source_hash,
                "sqliteContentHash": sqlite_hash,
                "matchesSourceHash": source_hash == sqlite_hash,
            }
        )
    return bindings


def base_request(
    *,
    operation_name: str,
    receipt_id: str,
    target_record_id: str,
    run_id: str,
    forecast_id: str,
    idempotency_key: str,
    caller_id: str = "agent-alpha",
    source_hash: str = "sha256-source-2101",
    audit_record_id: str | None = None,
    force_preflight_block: str | None = None,
    recovery_path: str | None = None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "operationName": operation_name,
        "operationReceiptId": receipt_id,
        "campaignId": "predictioncampaign-2101",
        "runId": run_id,
        "forecastId": forecast_id,
        "callerId": caller_id,
        "idempotencyKey": idempotency_key,
        "sourceRecordHash": source_hash,
        "targetRecordId": target_record_id,
        "leaseSeconds": 120,
        "payload": {
            "domain": "transit-delay",
            "syntheticRuntimeFixture": True,
            "historicalForecastRewriteAllowed": False,
            "qualityClaimAllowed": False,
        },
    }
    if audit_record_id:
        request["auditRecordId"] = audit_record_id
    if force_preflight_block:
        request["forcePreflightBlock"] = force_preflight_block
    if recovery_path:
        request["recoveryPath"] = recovery_path
    return request


def source_hash_for_hashes(*hashes: str) -> str:
    return "sha256-" + content_hash(list(hashes))


def attach_record_payloads(request: dict[str, Any], records: list[tuple[str, str, dict[str, Any]]]) -> dict[str, Any]:
    request["recordPayloads"] = {record_id: payload for _, record_id, payload in records}
    request["recordContentHashes"] = {record_id: rendered_content_hash(payload) for _, record_id, payload in records}
    request["payload"]["sourceRecordIds"] = [record_id for _, record_id, _ in records]
    request["payload"]["sourceContentHashes"] = [request["recordContentHashes"][record_id] for _, record_id, _ in records]
    return request


def scenario_summary(
    scenario_id: str,
    scenario_name: str,
    result: dict[str, Any],
    *,
    duplicate_records_created: int = 0,
    setup_operation_count: int = 0,
) -> dict[str, Any]:
    preflight = result["preflight"]
    writes = result["sqliteWrites"]
    summary = {
        "scenarioId": scenario_id,
        "scenarioName": scenario_name,
        "operationName": result["operationName"],
        "sqliteRuntimeExercised": True,
        "setupOperationCount": setup_operation_count,
        "preflightStatus": preflight["preflightStatus"],
        "executionStatus": result["operationStatus"],
        "idempotencyStatus": preflight["idempotencyStatus"],
        "leaseStatus": preflight["leaseStatus"],
        "operationReceiptId": result["operationReceiptId"],
        "plannedWriteCount": len(preflight["plannedWrites"]),
        "operationReceiptsWritten": writes["operationReceiptsWritten"],
        "immutableRecordsInserted": writes["immutableRecordsInserted"],
        "auditRecordsInserted": writes["auditRecordsInserted"],
        "duplicateRecordsCreated": duplicate_records_created,
        "physicalDeletes": writes["physicalDeletes"],
        "historyRewriteCount": writes["historyRewriteCount"],
        "rawCrudExposed": writes["rawCrudExposed"],
        "forecastArtifactMutable": False,
        "payloadHashBindings": result["payloadHashBindings"],
        "migrationImportSummary": result.get("migrationImportSummary"),
        "readModelEffects": read_model_effects_for_result(result),
        "recoveryPath": preflight["recoveryPath"],
        "preflight": {
            "plannedWrites": preflight["plannedWrites"],
            "blockingGuards": preflight["blockingGuards"],
            "idempotencyKey": result_request_idempotency_key(result),
            "leasePlan": preflight["leasePlan"],
            "claimBoundary": preflight["claimBoundary"],
        },
        "message": result["message"],
    }
    return summary


def result_request_idempotency_key(result: dict[str, Any]) -> str:
    return str(result["preflight"]["idempotencyKey"])


def read_model_effects_for_result(result: dict[str, Any]) -> list[str]:
    operation_name = result["operationName"]
    status = result["operationStatus"]
    effects = ["campaign_status"]
    if operation_name == "forecast.create" and status == "committed":
        effects.extend(["next_due_forecast", "unresolved_forecasts"])
    if operation_name in {"record.archive", "record.redact", "question.cancel", "question.annul"}:
        effects.append("append_readiness")
    if operation_name in {"pre_calibration.bind", "method.apply", "method.rollback"}:
        effects.extend(["calibration_status", "track_record_progress"])
    if operation_name == "state.import_json":
        effects.extend(["next_due_forecast", "append_readiness", "calibration_status", "track_record_progress", "recovery_actions"])
    if status != "committed" and status != "idempotent_replay":
        effects.extend(["failed_operations", "recovery_actions"])
    if operation_name == "resolution.record":
        effects.append("due_resolution_jobs")
    if operation_name == "score.create" and status == "committed":
        effects.append("append_readiness")
    if operation_name == "evidence.append" and status == "committed":
        effects.extend(["append_readiness", "calibration_status", "track_record_progress"])
    return list(dict.fromkeys(effects))


def campaign_forecast_create_request() -> dict[str, Any]:
    from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write

    plan = build_prediction_campaign_forecast_write(embed_source_records=True)
    bindings = plan["bindings"]
    target = plan["targetState"]
    records = [
        (artifact["recordType"], artifact["recordId"], artifact["sourceRecord"])
        for artifact in plan["sourceArtifacts"]
        if isinstance(artifact.get("sourceRecord"), dict)
    ]
    request = base_request(
        operation_name="forecast.create",
        receipt_id="operationreceipt-3001",
        target_record_id=bindings["forecastId"],
        run_id=bindings["runId"],
        forecast_id=bindings["forecastId"],
        idempotency_key=target["idempotencyKey"],
        source_hash=source_hash_for_hashes(*(rendered_content_hash(payload) for _, _, payload in records)),
    )
    request["questionRecordId"] = bindings["questionId"]
    request["evidencePacketId"] = bindings["evidencePacketId"]
    request["historyRecordId"] = bindings["historyId"]
    request["payload"] = {
        "predictionCampaignForecastWriteId": plan["predictionCampaignForecastWriteId"],
        "campaignId": bindings["campaignId"],
        "runId": bindings["runId"],
        "forecastId": bindings["forecastId"],
        "targetState": target,
        "historicalForecastRewriteAllowed": False,
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, records)


def campaign_resolution_and_score_records() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
    from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
    from prediction_campaign_resolution_runtime import (
        build_resolution_and_scoring,
        outcome_from_source,
        run_for_id,
    )

    manifest = build_prediction_campaign_manifest()
    run = run_for_id(manifest, "predictionrun-1301")
    plan = build_prediction_campaign_forecast_write(embed_source_records=True)
    source_records = {artifact["recordType"]: artifact["sourceRecord"] for artifact in plan["sourceArtifacts"]}
    outcome_summary = outcome_from_source(run=run, outcome_csv=None, missing_outcome=True)
    resolution, scoring = build_resolution_and_scoring(
        run=run,
        question=source_records["forecast_question"],
        artifact=source_records["forecast_artifact"],
        history=source_records["forecast_history"],
        outcome_summary=outcome_summary,
        outcome_csv=None,
        resolved_at=run["resolutionEligibleAt"],
    )
    return manifest, run, resolution, scoring


def campaign_resolution_record_request() -> dict[str, Any]:
    manifest, run, resolution, _ = campaign_resolution_and_score_records()
    request = base_request(
        operation_name="resolution.record",
        receipt_id="operationreceipt-3101",
        target_record_id=run["resolutionId"],
        run_id=run["runId"],
        forecast_id=run["forecastId"],
        idempotency_key=f"{manifest['campaign']['campaignId']}:{run['runId']}:{run['resolutionId']}",
        source_hash=source_hash_for_hashes(rendered_content_hash(resolution)),
    )
    request["payload"] = {
        "campaignId": manifest["campaign"]["campaignId"],
        "runId": run["runId"],
        "forecastId": run["forecastId"],
        "resolutionId": run["resolutionId"],
        "resolutionStatus": resolution["status"],
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, [("resolution_record", run["resolutionId"], resolution)])


def campaign_score_create_request() -> dict[str, Any]:
    manifest, run, _, scoring = campaign_resolution_and_score_records()
    request = base_request(
        operation_name="score.create",
        receipt_id="operationreceipt-3201",
        target_record_id=run["scoringReportId"],
        run_id=run["runId"],
        forecast_id=run["forecastId"],
        idempotency_key=f"{manifest['campaign']['campaignId']}:{run['runId']}:{run['scoringReportId']}",
        source_hash=source_hash_for_hashes(rendered_content_hash(scoring)),
    )
    request["payload"] = {
        "campaignId": manifest["campaign"]["campaignId"],
        "runId": run["runId"],
        "forecastId": run["forecastId"],
        "scoringReportId": run["scoringReportId"],
        "scoreStatus": scoring["scoreStatus"],
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, [("scoring_report", run["scoringReportId"], scoring)])


def campaign_evidence_append_request() -> dict[str, Any]:
    from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger

    ledger = build_prediction_campaign_evidence_ledger(mode="append", ledger_case="comparable_scored")
    row = ledger["comparableRows"][0]
    request = base_request(
        operation_name="evidence.append",
        receipt_id="operationreceipt-3301",
        target_record_id=row["rowId"],
        run_id=row["runId"],
        forecast_id=row["forecastId"],
        idempotency_key=row["rowKey"],
        source_hash=source_hash_for_hashes(rendered_content_hash(row)),
    )
    request["payload"] = {
        "predictionCampaignEvidenceLedgerId": ledger["predictionCampaignEvidenceLedgerId"],
        "campaignId": row["campaignId"],
        "runId": row["runId"],
        "forecastId": row["forecastId"],
        "rowKind": row["rowKind"],
        "appendOnly": True,
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, [("evidence_ledger_row", row["rowId"], row)])


def campaign_method_operation_request(operation: str) -> dict[str, Any]:
    from generate_prediction_campaign_method_update_action import build_prediction_campaign_method_update_action

    action = build_prediction_campaign_method_update_action(operation=operation, method_update_plan_case="plan_ready")
    bindings = action["bindings"]
    record_id = "methodaudit-3401" if operation == "apply" else "methodaudit-3501"
    payload = {
        "artifactType": "prediction_campaign_method_update_action",
        "operation": operation,
        "predictionCampaignMethodUpdateActionId": action["predictionCampaignMethodUpdateActionId"],
        "bindings": bindings,
        "approvalArtifact": action["approvalArtifact"],
        "rollbackRecord": action["rollbackRecord"],
        "methodBinding": action["methodBinding"],
        "effectiveScope": "future_campaign_forecasts_only",
        "priorForecastHistoryRewriteAllowed": False,
        "priorForecastProbabilityRewriteAllowed": False,
        "qualityClaimAllowed": False,
    }
    operation_name = "method.apply" if operation == "apply" else "method.rollback"
    request = base_request(
        operation_name=operation_name,
        receipt_id="operationreceipt-3401" if operation == "apply" else "operationreceipt-3501",
        target_record_id=action["methodBinding"]["methodBindingPath"].rsplit("/", 1)[-1].replace(".json", ""),
        run_id="predictionrun-method-update",
        forecast_id="forecast-method-update",
        idempotency_key=f"{bindings['campaignId']}:{operation}:method-binding",
        source_hash=source_hash_for_hashes(rendered_content_hash(payload)),
        audit_record_id=record_id,
    )
    request["leaseResourceId"] = f"{bindings['campaignId']}:method-binding"
    request["payload"] = {
        "predictionCampaignMethodUpdateActionId": action["predictionCampaignMethodUpdateActionId"],
        "operation": operation,
        "campaignId": bindings["campaignId"],
        "targetMethodId": action["methodBinding"]["targetMethodId"],
        "prospectiveOnly": True,
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, [("method_update_audit", record_id, payload)])


def json_state_import_request() -> dict[str, Any]:
    from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger
    from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write

    plan = build_prediction_campaign_forecast_write(embed_source_records=True)
    bindings = plan["bindings"]
    target = plan["targetState"]
    source_records = {artifact["recordType"]: artifact["sourceRecord"] for artifact in plan["sourceArtifacts"]}
    artifact = source_records["forecast_artifact"]
    history = source_records["forecast_history"]
    ledger = build_prediction_campaign_evidence_ledger(mode="append", ledger_case="comparable_scored")
    ledger_row = ledger["comparableRows"][0]
    run_state = {
        "stateType": "prediction_campaign_run_state",
        "stateVersion": 1,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "runId": bindings["runId"],
        "forecastId": bindings["forecastId"],
        "idempotencyKey": target["idempotencyKey"],
        "runStatus": "waiting_resolution",
        "artifactPaths": {
            "forecastArtifactPath": target["forecastArtifactPath"],
            "forecastHistoryPath": target["forecastHistoryPath"],
        },
        "importedFrom": target["runStatePath"],
    }
    campaign_state = {
        "stateType": "prediction_campaign_state",
        "stateVersion": 1,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "createdRunIdempotencyKeys": [target["idempotencyKey"]],
        "forecastArtifactsCreated": 1,
        "resolvedComparableOutcomes": 0,
        "importedFrom": target["campaignStatePath"],
    }
    method_binding = {
        "stateType": "prediction_campaign_method_binding",
        "stateVersion": 1,
        "campaignId": bindings["campaignId"],
        "cycleId": bindings["cycleId"],
        "activeMethodId": "transitmethod-100",
        "effectiveScope": "future_campaign_forecasts_only",
        "prospectiveOnly": True,
        "priorForecastHistoryRewriteAllowed": False,
        "priorForecastProbabilityRewriteAllowed": False,
        "importedFrom": f".ope/live/prediction-campaigns/{bindings['campaignId']}/method-binding.json",
    }
    migration_receipt = {
        "receiptType": "json_state_migration_receipt",
        "sourceRoot": ".ope/live/prediction-campaigns",
        "campaignId": bindings["campaignId"],
        "operationName": "state.import_json",
        "preservesForecastProbabilities": True,
        "preservesSourceProvenance": True,
        "rewritesHistoricalForecasts": False,
        "importedStateClasses": [
            "forecast_lifecycle_records",
            "run_state",
            "campaign_state",
            "evidence_ledger",
            "method_binding",
        ],
    }
    records = [
        ("forecast_artifact", bindings["forecastId"], artifact),
        ("forecast_history", bindings["historyId"], history),
        ("evidence_ledger_row", ledger_row["rowId"], ledger_row),
        ("run_state_projection", "runstateprojection-1301", run_state),
        ("campaign_state_projection", "campaignstateprojection-001", campaign_state),
        ("method_binding_state", "methodbindingstate-001", method_binding),
        ("json_state_migration_receipt", "jsonmigration-001", migration_receipt),
    ]
    request = base_request(
        operation_name="state.import_json",
        receipt_id="operationreceipt-3701",
        target_record_id="jsonmigration-001",
        run_id=bindings["runId"],
        forecast_id=bindings["forecastId"],
        idempotency_key=f"{bindings['campaignId']}:import-json-state:001",
        source_hash=source_hash_for_hashes(*(rendered_content_hash(payload) for _, _, payload in records)),
    )
    request["leaseResourceId"] = f"{bindings['campaignId']}:json-state-import"
    request["migrationWrites"] = [
        {"tableName": "ope_records", "recordType": "forecast_artifact", "recordId": bindings["forecastId"], "writeMode": "insert_once"},
        {"tableName": "forecast_history_events", "recordType": "forecast_history", "recordId": bindings["historyId"], "writeMode": "append_only"},
        {"tableName": "evidence_ledger_rows", "recordType": "evidence_ledger_row", "recordId": ledger_row["rowId"], "writeMode": "append_only"},
        {"tableName": "read_model_rows", "recordType": "run_state_projection", "recordId": "runstateprojection-1301", "writeMode": "projection_upsert"},
        {"tableName": "read_model_rows", "recordType": "campaign_state_projection", "recordId": "campaignstateprojection-001", "writeMode": "projection_upsert"},
        {"tableName": "operation_audit_records", "recordType": "method_binding_state", "recordId": "methodbindingstate-001", "writeMode": "prospective_binding"},
        {"tableName": "operation_audit_records", "recordType": "json_state_migration_receipt", "recordId": "jsonmigration-001", "writeMode": "append_only"},
    ]
    request["migrationImportSummary"] = {
        "sourceRoot": ".ope/live/prediction-campaigns",
        "stateClassCount": 5,
        "sourceFileCount": len(records),
        "contentHashesPreserved": True,
        "forecastProbabilitiesPreserved": True,
        "sourceProvenancePreserved": True,
        "historicalForecastRewriteCount": 0,
        "methodBindingsPreserved": True,
        "migrationReceiptRequired": True,
        "automaticMigrationAllowed": False,
    }
    request["payload"] = {
        "campaignId": bindings["campaignId"],
        "sourceRoot": ".ope/live/prediction-campaigns",
        "migrationReceiptRequired": True,
        "contentHashCheckRequired": True,
        "historicalForecastRewriteAllowed": False,
        "qualityClaimAllowed": False,
    }
    return attach_record_payloads(request, records)


def database_idempotency_replay_check(
    *,
    check_id: str,
    record_class: str,
    command_path: str,
    scenario_name: str,
    request: dict[str, Any],
    file_mode_repeat_status: str,
) -> dict[str, Any]:
    conn = open_sqlite()
    first_result = execute_operation(conn, request)
    replay_result = execute_operation(conn, dict(request))
    replay_writes = replay_result["sqliteWrites"]
    duplicate_records = (
        replay_writes["immutableRecordsInserted"]
        + replay_writes["auditRecordsInserted"]
    )
    return {
        "compatibilityCheckId": check_id,
        "recordClass": record_class,
        "commandPath": command_path,
        "scenarioName": scenario_name,
        "lifecycleOperation": request["operationName"],
        "fileModeRepeatStatus": file_mode_repeat_status,
        "fileModeDuplicatePrevented": True,
        "databaseFirstExecutionStatus": first_result["operationStatus"],
        "databaseReplayExecutionStatus": replay_result["operationStatus"],
        "databaseReplayIdempotencyStatus": replay_result["preflight"]["idempotencyStatus"],
        "databaseReplayOperationReceiptsWritten": replay_writes["operationReceiptsWritten"],
        "databaseDuplicateRecordsCreated": duplicate_records,
        "contentHashComparisonRequired": True,
        "historyRewriteCount": replay_writes["historyRewriteCount"],
        "physicalDeletes": replay_writes["physicalDeletes"],
        "rawCrudExposed": replay_writes["rawCrudExposed"],
        "compatible": (
            first_result["operationStatus"] == "committed"
            and replay_result["operationStatus"] == "idempotent_replay"
            and replay_result["preflight"]["idempotencyStatus"] == "return_existing_receipt"
            and replay_writes["operationReceiptsWritten"] == 0
            and duplicate_records == 0
            and replay_writes["historyRewriteCount"] == 0
            and replay_writes["physicalDeletes"] == 0
            and replay_writes["rawCrudExposed"] is False
        ),
    }


def file_database_compatibility_checks() -> list[dict[str, Any]]:
    return [
        database_idempotency_replay_check(
            check_id="compatibilitycheck-001",
            record_class="forecast_lifecycle_records",
            command_path="prediction-campaign forecast-write --write-local",
            scenario_name="campaign-forecast-create",
            request=campaign_forecast_create_request(),
            file_mode_repeat_status="local_write_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-002",
            record_class="resolution_records",
            command_path="prediction-campaign resolve --execute-resolvers --write-local",
            scenario_name="campaign-resolution-record",
            request=campaign_resolution_record_request(),
            file_mode_repeat_status="local_resolution_scored_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-003",
            record_class="scoring_reports",
            command_path="prediction-campaign resolve --execute-resolvers --write-local",
            scenario_name="campaign-score-create",
            request=campaign_score_create_request(),
            file_mode_repeat_status="local_resolution_scored_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-004",
            record_class="evidence_ledger_rows",
            command_path="prediction-campaign append --write-local",
            scenario_name="campaign-evidence-append",
            request=campaign_evidence_append_request(),
            file_mode_repeat_status="local_append_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-005",
            record_class="pre_calibration_method_binding",
            command_path="prediction-campaign pre-calibration --write-local",
            scenario_name="pre-calibration-bind",
            request=base_request(
                operation_name="pre_calibration.bind",
                receipt_id="operationreceipt-3901",
                target_record_id="methodbinding-3901",
                run_id="predictionrun-3901",
                forecast_id="forecast-3901",
                idempotency_key="predictioncampaign-2101:pre-calibration:methodbinding-3901",
                source_hash="sha256-history-3901",
                audit_record_id="precalibrationbinding-3901",
            ),
            file_mode_repeat_status="local_pre_calibration_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-006",
            record_class="method_apply_binding",
            command_path="prediction-campaign apply-method-update --write-local",
            scenario_name="campaign-method-apply",
            request=campaign_method_operation_request("apply"),
            file_mode_repeat_status="local_apply_already_present",
        ),
        database_idempotency_replay_check(
            check_id="compatibilitycheck-007",
            record_class="method_rollback_binding",
            command_path="prediction-campaign rollback-method-update --write-local",
            scenario_name="campaign-method-rollback",
            request=campaign_method_operation_request("rollback"),
            file_mode_repeat_status="local_rollback_already_present",
        ),
    ]


def run_runtime_scenarios() -> list[dict[str, Any]]:
    scenarios: list[dict[str, Any]] = []

    conn = open_sqlite()
    create_request = base_request(
        operation_name="forecast.create",
        receipt_id="operationreceipt-2101",
        target_record_id="forecast-2101",
        run_id="predictionrun-2101",
        forecast_id="forecast-2101",
        idempotency_key="predictioncampaign-2101:predictionrun-2101:forecast-2101",
    )
    create_result = execute_operation(conn, create_request)
    scenarios.append(scenario_summary("lifecyclescenario-001", "create", create_result))

    retry_request = dict(create_request)
    retry_request["operationReceiptId"] = "operationreceipt-2102"
    retry_result = execute_operation(conn, retry_request)
    duplicate_records_created = (
        retry_result["tableCountsAfter"]["ope_records"]
        + retry_result["tableCountsAfter"]["forecast_history_events"]
        - create_result["tableCountsAfter"]["ope_records"]
        - create_result["tableCountsAfter"]["forecast_history_events"]
    )
    scenarios.append(
        scenario_summary(
            "lifecyclescenario-002",
            "retry-idempotent",
            retry_result,
            duplicate_records_created=duplicate_records_created,
        )
    )

    conn = open_sqlite()
    lease_owner_request = base_request(
        operation_name="forecast.create",
        receipt_id="operationreceipt-2201",
        target_record_id="forecast-2201",
        run_id="predictionrun-2201",
        forecast_id="forecast-2201",
        idempotency_key="predictioncampaign-2101:predictionrun-2201:forecast-2201:alpha",
    )
    execute_operation(conn, lease_owner_request)
    lease_conflict_request = base_request(
        operation_name="forecast.create",
        receipt_id="operationreceipt-2202",
        target_record_id="forecast-2201",
        run_id="predictionrun-2201",
        forecast_id="forecast-2201",
        idempotency_key="predictioncampaign-2101:predictionrun-2201:forecast-2201:beta",
        caller_id="agent-beta",
        source_hash="sha256-source-2202",
    )
    lease_conflict_result = execute_operation(conn, lease_conflict_request)
    scenarios.append(
        scenario_summary(
            "lifecyclescenario-003",
            "lease-conflict",
            lease_conflict_result,
            setup_operation_count=1,
        )
    )

    conn = open_sqlite()
    archive_request = base_request(
        operation_name="record.archive",
        receipt_id="operationreceipt-2301",
        target_record_id="forecast-2301",
        run_id="predictionrun-2301",
        forecast_id="forecast-2301",
        idempotency_key="predictioncampaign-2101:archive:forecast-2301",
        audit_record_id="archive-2301",
    )
    archive_result = execute_operation(conn, archive_request)
    scenarios.append(scenario_summary("lifecyclescenario-004", "archive", archive_result))

    conn = open_sqlite()
    redaction_request = base_request(
        operation_name="record.redact",
        receipt_id="operationreceipt-2401",
        target_record_id="forecast-2401",
        run_id="predictionrun-2401",
        forecast_id="forecast-2401",
        idempotency_key="predictioncampaign-2101:redact:forecast-2401",
        audit_record_id="redaction-2401",
    )
    redaction_result = execute_operation(conn, redaction_request)
    scenarios.append(scenario_summary("lifecyclescenario-005", "redaction", redaction_result))

    conn = open_sqlite()
    rollback_request = base_request(
        operation_name="method.rollback",
        receipt_id="operationreceipt-2501",
        target_record_id="methodbinding-2501",
        run_id="predictionrun-2501",
        forecast_id="forecast-2501",
        idempotency_key="predictioncampaign-2101:method-rollback:methodbinding-2501",
        audit_record_id="methodaudit-2501",
    )
    rollback_result = execute_operation(conn, rollback_request)
    scenarios.append(scenario_summary("lifecyclescenario-006", "method-rollback", rollback_result))

    conn = open_sqlite()
    pre_calibration_request = base_request(
        operation_name="pre_calibration.bind",
        receipt_id="operationreceipt-2701",
        target_record_id="methodbinding-2701",
        run_id="predictionrun-2701",
        forecast_id="forecast-2701",
        idempotency_key="predictioncampaign-2101:pre-calibration:methodbinding-2701",
        source_hash="sha256-history-2701",
        audit_record_id="precalibrationbinding-2701",
    )
    pre_calibration_request["leaseResourceId"] = "predictioncampaign-2101:method-binding"
    pre_calibration_request["payload"] = {
        "domain": "transit-delay",
        "syntheticRuntimeFixture": True,
        "historySourceContentHash": "sha256-history-2701",
        "calibratedProbability": 0.25,
        "historicalForecastRewriteAllowed": False,
        "prospectiveOnly": True,
        "qualityClaimAllowed": False,
    }
    pre_calibration_result = execute_operation(conn, pre_calibration_request)
    scenarios.append(scenario_summary("lifecyclescenario-007", "pre-calibration-bind", pre_calibration_result))

    conn = open_sqlite()
    campaign_forecast_result = execute_operation(conn, campaign_forecast_create_request())
    scenarios.append(scenario_summary("lifecyclescenario-008", "campaign-forecast-create", campaign_forecast_result))

    conn = open_sqlite()
    campaign_resolution_result = execute_operation(conn, campaign_resolution_record_request())
    scenarios.append(scenario_summary("lifecyclescenario-009", "campaign-resolution-record", campaign_resolution_result))

    conn = open_sqlite()
    campaign_score_result = execute_operation(conn, campaign_score_create_request())
    scenarios.append(scenario_summary("lifecyclescenario-010", "campaign-score-create", campaign_score_result))

    conn = open_sqlite()
    campaign_append_result = execute_operation(conn, campaign_evidence_append_request())
    scenarios.append(scenario_summary("lifecyclescenario-011", "campaign-evidence-append", campaign_append_result))

    conn = open_sqlite()
    campaign_apply_result = execute_operation(conn, campaign_method_operation_request("apply"))
    scenarios.append(scenario_summary("lifecyclescenario-012", "campaign-method-apply", campaign_apply_result))

    conn = open_sqlite()
    campaign_rollback_result = execute_operation(conn, campaign_method_operation_request("rollback"))
    scenarios.append(scenario_summary("lifecyclescenario-013", "campaign-method-rollback", campaign_rollback_result))

    conn = open_sqlite()
    json_import_result = execute_operation(conn, json_state_import_request())
    scenarios.append(scenario_summary("lifecyclescenario-014", "json-state-import", json_import_result))

    conn = open_sqlite()
    recovery_request = base_request(
        operation_name="score.create",
        receipt_id="operationreceipt-3801",
        target_record_id="scoringreport-3801",
        run_id="predictionrun-3801",
        forecast_id="forecast-3801",
        idempotency_key="predictioncampaign-2101:score:forecast-3801",
        force_preflight_block="Resolution record is missing, so scoring cannot commit yet.",
        recovery_path="record_resolution_then_retry_score_create_with_same_idempotency_key",
    )
    recovery_result = execute_operation(conn, recovery_request)
    scenarios.append(scenario_summary("lifecyclescenario-015", "recovery", recovery_result))

    return scenarios
