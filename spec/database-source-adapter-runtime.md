# Approved Database Source Adapter Runtime

This contract defines the first bounded database source-adapter runtime readback for OPE. It turns a checked database source binding into one caller-approved, fixture-safe adapter-output path while keeping production database access, credentials, raw rows, and database-specific forecast execution outside normal checks.

The runtime is represented by `database-source-adapter-runtime.schema.json` and the generated fixture at `spec/fixtures/generated/database-source-adapter-runtime/ope-database-source-adapter-runtime.generated.json`.

## Runtime Request

The runtime request must carry:

- `sourceBindingId`
- `sourceRole`
- `approvedQueryManifestRef`
- `credentialRef`
- `rowLimit`
- `timeLimitSeconds`
- `freshnessWindowHours`
- `leakageWindow`
- `callerApprovalStatus`

Credential references are identifiers only. Credential values, raw SQL with secrets, raw private rows, stack traces, and unapproved schema scans are not accepted into OPE records or diagnostics.

## Sanitized Output

The approved fixture emits a sanitized database adapter output with:

- source manifest summary
- field mapping summary
- provenance summary
- source-quality signals
- mapping-confidence signals
- outcome availability status
- query-boundary summary

The output is compatible with the existing source-adapter intake path. It then routes through source intake, source handoff, setup benchmark, setup method decision, and forecast execution gates. It does not create a database-specific forecast path.

## Blocked Cases

The checked runtime includes blocked readbacks for:

- missing caller approval
- missing credential reference
- unsafe query boundary
- oversized result
- stale source
- leakage risk
- missing outcome source
- insufficient comparable history

Blocked cases stop before source-adapter intake and do not create forecast artifacts or scoring records.

## Readbacks

Supported readbacks:

```bash
python3 scripts/ope.py database-source-adapter-runtime
python3 scripts/ope.py internal-api --operation database_source_adapter_status
python3 scripts/ope.py agent-call --operation database_source_adapter_runtime_status
```

Normal checks remain offline and deterministic. Live production database connections, arbitrary private database parsing, credential storage, raw private rows, hosted runtime behavior, and source-quality-driven artifact creation are still non-goals.
