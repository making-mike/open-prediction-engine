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
    "method.apply",
    "method.rollback",
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
                "recordType": "evidence_packet",
                "recordId": request["targetRecordId"],
                "writeMode": "append_only",
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
        payload_hash = content_hash(payload)
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
                    request.get("schemaFile", "spec/lifecycle-operation.schema.json"),
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
        else:
            raise LifecycleOperationRuntimeError(f"unsupported write table: {write['tableName']}")


def record_payload(request: dict[str, Any], write: dict[str, str], *, receipt_id: str, now: str) -> dict[str, Any]:
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
    if request["operationName"] in {"method.apply", "method.rollback"}:
        put_read_model(
            conn,
            "calibration_status",
            campaign_id,
            {
                "campaignId": campaign_id,
                "methodOperation": request["operationName"],
                "prospectiveOnly": True,
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
    return {
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
        "message": message,
    }


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
        "schemaFile": "spec/lifecycle-operation.schema.json",
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
    return {
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
    if operation_name in {"method.apply", "method.rollback"}:
        effects.extend(["calibration_status", "track_record_progress"])
    if status != "committed" and status != "idempotent_replay":
        effects.extend(["failed_operations", "recovery_actions"])
    if operation_name == "resolution.record":
        effects.append("due_resolution_jobs")
    return list(dict.fromkeys(effects))


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
    recovery_request = base_request(
        operation_name="score.create",
        receipt_id="operationreceipt-2601",
        target_record_id="scoringreport-2601",
        run_id="predictionrun-2601",
        forecast_id="forecast-2601",
        idempotency_key="predictioncampaign-2101:score:forecast-2601",
        force_preflight_block="Resolution record is missing, so scoring cannot commit yet.",
        recovery_path="record_resolution_then_retry_score_create_with_same_idempotency_key",
    )
    recovery_result = execute_operation(conn, recovery_request)
    scenarios.append(scenario_summary("lifecyclescenario-007", "recovery", recovery_result))

    return scenarios
