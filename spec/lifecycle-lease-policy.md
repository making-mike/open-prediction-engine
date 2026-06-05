# Lifecycle Lease Policy

Status: checked lifecycle operation guard policy.

Last reviewed: 2026-06-04.

OPE lifecycle operations all require idempotency, preflight checks, and operation receipts. This policy adds the next guard decision: which effectful operations also need strict leases because concurrent agents could otherwise create duplicate or conflicting lifecycle records.

Default checked readback:

```bash
python3 scripts/ope.py lifecycle-lease-policy
python3 scripts/ope.py lifecycle-lease-policy --view summary
python3 scripts/ope.py lifecycle-lease-policy --view strict
python3 scripts/ope.py lifecycle-lease-policy --view idempotency
python3 scripts/ope.py lifecycle-lease-policy --view cases
python3 scripts/ope.py lifecycle-lease-policy --view boundary
python3 scripts/ope.py lifecycle-lease-policy --operation forecast.recalculate
python3 scripts/ope.py lifecycle-lease-policy --check
```

## Guard Modes

The checked policy covers fourteen lifecycle operations from the operation store.

Strict leases are required for race-prone writes:

- `campaign.create_run`
- `forecast.create`
- `resolution.record`
- `score.create`
- `evidence.append`
- `pre_calibration.bind`
- `method.apply`
- `method.rollback`
- `state.import_json`

Idempotency-only guards are used for operations where retries can safely return an existing receipt or blocked terminal-state readback without acquiring a lease:

- `forecast.recalculate`
- `question.cancel`
- `question.annul`
- `record.archive`
- `record.redact`

Every operation still requires preflight validation, an idempotency key, an operation receipt, sanitized diagnostics, no raw CRUD exposure, and no forecast-quality claim upgrade.

## Conflict Cases

The generated readback includes eight conflict and retry examples:

- `same_due_forecast`
- `duplicate_forecast_retry`
- `recalculate_same_evidence`
- `cancel_after_forecast_created`
- `resolution_record_race`
- `method_apply_race`
- `stale_import_lease`
- `archive_repeat`

These cases acquire no leases, write no operation receipts, write no immutable records, and return safe next actions such as waiting on an active lease, reusing an existing readback, or inspecting stale-lease recovery.

## Readbacks

The policy binds back to:

- `python3 scripts/ope.py lifecycle-operation-store`
- `python3 scripts/ope.py background-worker`
- `python3 scripts/ope.py persistent-sqlite-policy`

Those readbacks describe where leases are needed when effectful write paths are explicitly run. The lifecycle lease policy readback itself is non-mutating and does not reserve locks.

## Boundary

This policy does not create a persistent database, open Postgres, implement hosted queues, expose raw lock CRUD, acquire leases during normal checks, rewrite forecast history, physically delete records, store credentials, or upgrade quality claims. It is a schema-bound decision surface for agents that need to choose between strict lease handling and idempotent retry handling before running explicit local write operations.
