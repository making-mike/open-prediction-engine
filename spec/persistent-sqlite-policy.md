# Persistent SQLite Path Policy

Status: checked opt-in readiness policy.

Last reviewed: 2026-06-04.

OPE's local lifecycle runtime can use SQLite semantics, but normal checks continue to use ephemeral SQLite. A persistent SQLite file is allowed only as an explicit caller-approved local runtime choice, not as the default repository behavior.

Default checked readback:

```bash
python3 scripts/ope.py persistent-sqlite-policy
python3 scripts/ope.py persistent-sqlite-policy --view summary
python3 scripts/ope.py persistent-sqlite-policy --view blocked
python3 scripts/ope.py persistent-sqlite-policy --view migration
python3 scripts/ope.py persistent-sqlite-policy --view backup-lock
python3 scripts/ope.py persistent-sqlite-policy --check
```

## Path Policy

The checked policy keeps the default persistent path template under `.ope/state/{workspaceId}/ope.sqlite3`. Persistent paths must be rooted in the workspace, use an allowlisted local state root, block path traversal, block symlink escapes, and require caller approval before any write-capable path is accepted.

Absolute paths require explicit approval. Credential values are never accepted as path material, and raw SQL is not exposed to agents through the path policy.

## Readiness Cases

The generated record covers ten cases:

- `ephemeral_default`: ready for normal checks, creates no persistent database.
- `approved_workspace_path`: ready for explicit local write mode, still non-mutating in normal checks.
- `missing_approval`: blocked until caller approval is collected.
- `outside_workspace`: blocked until the path is replaced with an allowlisted workspace state path.
- `symlink_escape`: blocked until the symlink escape is removed.
- `existing_unmigrated_json_state`: blocked until a JSON-state import dry-run is performed.
- `schema_version_mismatch`: blocked until schema compatibility is checked.
- `backup_missing`: blocked until a backup is created before migration.
- `lock_conflict`: blocked until the lease conflict clears or stale-lock recovery is receipted.
- `readonly_filesystem`: blocked until the caller chooses a writable state path.

Blocked cases create no persistent database, write no operation receipts, and expose only sanitized diagnostics.

## Migration Policy

Ignored JSON state may enter SQLite only through an explicit `state.import_json` operation. Migration must run a dry-run first, require a backup before write, preserve content hashes, preserve source record hashes, preserve forecast probabilities and provenance, and avoid rewriting historical forecast histories.

There is no automatic JSON-state migration. Normal checks do not read ignored live state or run migration.

## Backup And Lock Policy

Effectful persistent writes require backup and lock discipline before migration or recovery:

- backup before migration;
- backup content hash;
- SQLite busy timeout of 5000 ms;
- lifecycle lease alignment for race-prone operations;
- stale-lock recovery receipt.

The policy allows WAL mode only after explicit write mode. Normal checks do not enable WAL mode or create local database files.

## Boundary

This policy does not implement hosted runtime, Postgres connections, raw SQL access, production database parsing, destructive migration, physical delete, credential storage, or stronger forecast-quality claims. It records when a persistent local SQLite path is ready for an explicit local write command and when an agent must stop and ask for safer input.
