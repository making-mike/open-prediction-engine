# Lifecycle Operation Store

Status: checked local SQLite runtime.

Last reviewed: 2026-06-03.

OPE is record/lifecycle-first, not CRUD-first. The lifecycle operation store defines the database-backed runtime shape needed for multi-agent prediction execution while preserving immutable forecast records and append-only histories.

Default checked readback:

```bash
python3 scripts/ope.py lifecycle-operation-store
python3 scripts/ope.py lifecycle-operation-store --scenario create
python3 scripts/ope.py lifecycle-operation-store --scenario retry-idempotent
python3 scripts/ope.py lifecycle-operation-store --scenario lease-conflict
python3 scripts/ope.py lifecycle-operation-store --scenario archive
python3 scripts/ope.py lifecycle-operation-store --scenario redaction
python3 scripts/ope.py lifecycle-operation-store --scenario method-rollback
python3 scripts/ope.py lifecycle-operation-store --scenario recovery
python3 scripts/ope.py lifecycle-operation-store --check
```

The default readback runs checked scenarios against an ephemeral SQLite database. It does not create a persistent SQLite file, open Postgres, migrate `.ope/live`, fetch live data, create live forecast artifacts, resolve outcomes, score forecasts in live state, store credentials, or expose raw database CRUD.

## Storage Shape

The first implementation target is local SQLite behind a storage adapter, and the checked fixture now exercises that adapter. The production design target is Postgres-compatible tables behind the same lifecycle semantics. The existing ignored JSON state remains a compatibility source until a migration operation imports it with content hashes and operation receipts.

The database stores:

- immutable OPE records, such as forecast questions, evidence packets, forecast artifacts, histories, resolutions, scores, calibration summaries, and method-update audit records;
- lifecycle operation receipts;
- idempotency keys for safe agent retries;
- short leases for due forecast creation, resolution, scoring, ledger append, and method updates;
- read models for next actions, queues, recovery, calibration status, and track-record progress.

The checked SQLite schema plan covers `operation_receipts`, `operation_idempotency_keys`, `operation_leases`, `ope_records`, `forecast_history_events`, `operation_audit_records`, `evidence_ledger_rows`, and `read_model_rows`.

## Operation Model

Agents should call lifecycle operations, not raw SQL updates:

- `campaign.create_run`
- `forecast.create`
- `forecast.recalculate`
- `question.cancel`
- `question.annul`
- `resolution.record`
- `score.create`
- `evidence.append`
- `method.apply`
- `method.rollback`
- `record.archive`
- `record.redact`

Every effectful operation needs a preflight, idempotency key, planned-write list, blocking-guard list, operation receipt, and safe retry behavior. Operations that can race across agents also need a lease.

The checked runtime scenarios cover create, retry-idempotent, lease-conflict, archive, redaction, method-rollback, and recovery. Scenario readbacks expose planned writes, blocking guards, idempotency keys, lease plans, claim boundaries, and recovery paths before mutation.

## Migration Rules

Ignored `.ope/live` JSON state remains the compatibility source until a migration operation imports it into SQLite. Migration must append a migration receipt, preserve original content hashes, preserve forecast probabilities and source provenance exactly, and avoid rewriting historical forecast histories. Normal checks do not run migration or require a persistent database.

## Delete Replacement

Forecast records are not silently deleted. Delete-like requests resolve to lifecycle operations:

- cancel a not-yet-forecast question;
- annul a defective forecast contract;
- archive records from active read models while preserving audit metadata;
- redact private or unsafe fields with a redaction receipt;
- roll back prospective method bindings without rewriting historical forecasts.

Rare physical deletion remains a retention/privacy policy decision outside the default prediction lifecycle.

## Agent Read Models

Agents need queryable read models instead of file guessing:

- campaign status;
- next due forecast;
- due resolution jobs;
- unresolved forecasts;
- append readiness;
- calibration status;
- track-record progress;
- failed operations;
- recovery actions.

These read models are projections. OPE semantics stay in the immutable records and lifecycle operation receipts.

## Boundary

This milestone defines and checks the local SQLite storage/runtime boundary. It does not claim hosted runtime readiness, network API support, production live-source execution, production private database parsing, calibration, or state-of-the-art forecasting quality.
