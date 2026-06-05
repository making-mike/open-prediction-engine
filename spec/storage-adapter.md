# Storage Adapter

Status: checked local SQLite boundary with Postgres-compatible semantics checkpoint.

Last reviewed: 2026-06-04.

The storage adapter keeps OPE lifecycle semantics independent from the backing store. File fixtures, ignored JSON state, local SQLite, and future Postgres should all expose the same operation/readback behavior.

## Adapter Responsibilities

- Validate operation preflight records before mutation.
- Reserve or reject leases for race-prone operations.
- Enforce idempotency keys and return existing receipts for safe retries.
- Insert immutable records and operation receipts.
- Update rebuildable read models from committed operation receipts.
- Refuse raw forecast probability edits, history rewrites, and silent deletes.
- Return sanitized diagnostics and claim boundaries to agent callers.

## First Backends

`ignored_json_compat` preserves the current local MVP and fixture workflows. It remains useful for checked readbacks and migration testing but is weak for multi-agent coordination.

`local_sqlite` is the first checked effectful runtime backend. It gives local agents transactions, indexes, idempotency tables, and leases without requiring hosted infrastructure. The checked scenarios run in an ephemeral SQLite database so normal repository checks do not create persistent local state.

Persistent SQLite file paths are governed separately by `spec/persistent-sqlite-policy.md` and `python3 scripts/ope.py persistent-sqlite-policy`. A persistent path is ready only after caller approval, workspace-state allowlisting, traversal and symlink checks, backup and lock guards, and explicit write mode. Normal checks keep using ephemeral SQLite.

Operation lease requirements are governed separately by `spec/lifecycle-lease-policy.md` and `python3 scripts/ope.py lifecycle-lease-policy`. Race-prone lifecycle writes use strict leases, retry-safe operations use idempotency-only guards, and the policy readback does not acquire locks or expose raw lock CRUD.

`postgres_design` is the production-compatible schema target. `spec/postgres-compatibility.md` checks the table mappings, adapter semantics, lifecycle scenario matrix, SQLite-only assumption guards, and migration boundary. It should support the same lifecycle operation contract, not a separate API that exposes generic CRUD.

Postgres compatibility is currently a storage-semantics claim only. Normal checks do not open a Postgres connection, run migrations, require hosted storage, expose raw SQL to agents, or store credential values.

## Non-Goals

The adapter is not a source connector, hosted service, scheduler, credential vault, model registry replacement, or trust authority. It stores OPE records and operation state; it does not decide which evidence is true or which method is high quality.
