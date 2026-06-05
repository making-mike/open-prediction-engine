# Lifecycle Operation Store

Status: checked local SQLite runtime.

Last reviewed: 2026-06-04.

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
python3 scripts/ope.py lifecycle-operation-store --scenario pre-calibration-bind
python3 scripts/ope.py lifecycle-operation-store --scenario campaign-forecast-create
python3 scripts/ope.py lifecycle-operation-store --scenario campaign-evidence-append
python3 scripts/ope.py lifecycle-operation-store --scenario json-state-import
python3 scripts/ope.py lifecycle-operation-store --scenario recovery
python3 scripts/ope.py lifecycle-operation-store --check
python3 scripts/ope.py persistent-sqlite-policy
python3 scripts/ope.py lifecycle-lease-policy
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

## JSON Compatibility Adapter

Ignored `.ope/live/prediction-campaigns` state remains an explicit compatibility adapter while the database bridge is introduced. Compatibility reads and explicit local writes remain available for existing campaign workflows, but normal checks do not write ignored state and migration is never automatic.

Persistent local database files are gated by `spec/persistent-sqlite-policy.md`. The policy requires caller approval, an allowlisted workspace state path, traversal and symlink blockers, dry-run JSON-state import, backup-before-migration, lease alignment, and stale-lock recovery receipts before a persistent SQLite path is ready for explicit local writes.

Lease requirements are classified by `spec/lifecycle-lease-policy.md`. That readback marks `campaign.create_run`, `forecast.create`, `resolution.record`, `score.create`, `evidence.append`, `pre_calibration.bind`, `method.apply`, `method.rollback`, and `state.import_json` as strict-lease operations, while retry-style operations such as `forecast.recalculate`, cancel/annul, archive, and redact remain idempotency-only. The policy readback itself does not acquire leases or mutate lifecycle state.

The adapter covers forecast lifecycle records, run state, campaign state, evidence ledger rows, method bindings, and method-update audit artifacts. Importing any of those files into SQLite must use an explicit migration operation, preserve source content hashes and forecast probabilities, retain source provenance, and append a migration receipt.

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
- `pre_calibration.bind`
- `method.apply`
- `method.rollback`
- `record.archive`
- `record.redact`

Every effectful operation needs a preflight, idempotency key, planned-write list, blocking-guard list, operation receipt, and safe retry behavior. Operations that can race across agents also need a lease.

The checked runtime scenarios cover create, retry-idempotent, lease-conflict, archive, redaction, method-rollback, pre-calibration-bind, campaign forecast creation, campaign resolution, campaign scoring, campaign evidence append, campaign method apply/rollback, JSON state import, and recovery. Scenario readbacks expose planned writes, blocking guards, idempotency keys, lease plans, source payload hash bindings, migration summaries, claim boundaries, and recovery paths before mutation.

The generated `writeLocalOperationCoverage` table maps the current explicit local mutation commands to lifecycle operations: `start --write-local`, `start --pre-calibrate --write-local`, `forecast-write --write-local`, `resolve --execute-resolvers --write-local`, `append --write-local`, `pre-calibration --write-local`, `apply-method-update --write-local`, and `rollback-method-update --write-local`. Each mapping requires operation receipts, idempotency, leases, and the read models agents need after the mutation.

The generated `fileDatabaseCompatibilityChecks` table compares local file-mode repeat statuses with SQLite idempotent replay for forecast lifecycle records, resolution records, scoring reports, evidence ledger rows, pre-calibration method bindings, method apply bindings, and method rollback bindings. Replays must return existing receipts, create no duplicate records, perform no physical deletes, and never rewrite forecast history.

## Migration Rules

Ignored `.ope/live` JSON state remains the compatibility source until a migration operation imports it into SQLite. Migration must append a migration receipt, preserve original content hashes, preserve forecast probabilities and source provenance exactly, and avoid rewriting historical forecast histories. Normal checks do not run migration or require a persistent database.

The checked `json-state-import` scenario exercises the migration operation shape against an ephemeral SQLite database. It imports representative forecast lifecycle, run-state, campaign-state, evidence-ledger, method-binding, and migration-receipt payloads with matching source and SQLite content hashes. This proves the migration receipt contract without creating a persistent database file or changing ignored local state.

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
