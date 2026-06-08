# Postgres Compatibility Checkpoint

Status: checked storage-semantics readback.

Last reviewed: 2026-06-04.

This checkpoint explains how the checked local SQLite lifecycle operation store maps to a Postgres-compatible backend without implementing a Postgres runtime or making hosted-storage claims.

The machine-readable record is generated at `spec/fixtures/generated/postgres-compatibility/ope-postgres-compatibility.generated.json` and validated by `spec/postgres-compatibility.schema.json`.

## Scope

The checkpoint covers these lifecycle tables:

- `operation_receipts`
- `operation_idempotency_keys`
- `operation_leases`
- `ope_records`
- `forecast_history_events`
- `operation_audit_records`
- `evidence_ledger_rows`
- `read_model_rows`

Each table readback records the SQLite write mode, explicit primary key, planned Postgres type mapping, JSON payload portability, content-hash portability, timestamp normalization, raw-CRUD boundary, and whether a hosted runtime is required.

## Adapter Semantics

The dialect-neutral adapter contract covers:

- JSON payloads
- content hashes
- unique idempotency keys
- lease acquisition
- lease expiry
- append-only records
- read-model upserts

The compatibility claim is about OPE storage semantics, not SQL text identity. Future adapters can use backend-specific SQL only when they preserve operation receipts, idempotency behavior, lease conflicts, immutable record writes, append-only audit/history/evidence rows, and rebuildable read-model upserts.

## Scenario Matrix

The generated matrix covers every checked lifecycle operation-store scenario:

- `create`
- `retry-idempotent`
- `lease-conflict`
- `archive`
- `redaction`
- `method-rollback`
- `pre-calibration-bind`
- `campaign-forecast-create`
- `campaign-resolution-record`
- `campaign-score-create`
- `campaign-evidence-append`
- `pilot-evidence-append`
- `campaign-method-apply`
- `campaign-method-rollback`
- `json-state-import`
- `recovery`

The retry scenario must return the existing receipt, the lease-conflict scenario must stay blocked, and JSON state import must remain an explicit receipt-backed migration operation.

## SQLite-Only Assumption Guards

Normal checks detect whether the compatibility claim accidentally relies on:

- SQLite `rowid` identity
- loose typing
- non-portable upsert behavior
- missing timestamp normalization
- SQLite-only JSON query behavior

All current guards are checked with no active SQLite-only assumption detected.

## Execution Boundary

Normal checks do not open a Postgres connection, run migrations, require a production database, expose raw SQL to agents, store credential values, or claim hosted storage readiness. SQLite remains the default local runtime.

Useful commands:

```bash
python3 scripts/ope.py postgres-compatibility
python3 scripts/ope.py postgres-compatibility --view tables
python3 scripts/ope.py postgres-compatibility --view scenarios
python3 scripts/ope.py postgres-compatibility --view boundary
python3 scripts/ope.py postgres-compatibility --check
```
