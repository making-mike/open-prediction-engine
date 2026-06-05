# Retention Redaction Policy

Status: checked policy readback.

Last reviewed: 2026-06-04.

This policy answers how OPE distinguishes normal retention, archive tombstones, redaction receipts, sanitized projection rebuilds, and rare physical delete exceptions.

Default readback:

```bash
python3 scripts/ope.py retention-redaction-policy
python3 scripts/ope.py retention-redaction-policy --view classes
python3 scripts/ope.py retention-redaction-policy --view actions
python3 scripts/ope.py retention-redaction-policy --view gates
python3 scripts/ope.py retention-redaction-policy --case physical_delete_with_authorized_erasure
python3 scripts/ope.py retention-redaction-policy --case physical_delete_for_forecast_history
python3 scripts/ope.py retention-redaction-policy --view boundary
python3 scripts/ope.py retention-redaction-policy --check
```

The generated fixture lives at `spec/fixtures/generated/retention-redaction-policy/ope-retention-redaction-policy.generated.json` and is validated by `spec/retention-redaction-policy.schema.json`.

## Policy Shape

OPE records remain lifecycle-first rather than CRUD-first:

- Forecast lifecycle records, evidence traces, and operation receipts are retained append-only for audit, provenance, scoring, and idempotent retry.
- Source-binding configs can be archived with audit tombstones so active read models stop showing them without silently deleting history.
- Private source details, credential-like submissions, and unsafe pilot summaries use redaction receipts and sanitized projections.
- Local usage trace events can be reduced to aggregate projections after the local evidence window.
- Raw connector previews, raw pilot transcripts, credential values, and raw private rows are not retained in normal OPE records.

## Physical Delete Exceptions

Physical deletion is not the default and is not implemented by normal checks. A future exception path must satisfy every checked gate:

- authorized erasure basis
- tenant/workspace scope verification
- record class eligibility
- legal or safety review receipt
- retained audit tombstone
- retained redaction receipt
- preserved forecast-history integrity or explicit unscorable status
- operator approval receipt

Forecast lifecycle records are not physically deleted by this policy. If evidence removal would break lifecycle integrity, the affected forecast must become explicitly unscorable rather than having history silently rewritten.

## Boundary

This policy is readback-only. It does not write state, execute archive/redaction operations, physically delete records, implement a hosted erasure workflow, rewrite forecast histories, retain credential values, retain raw private rows, retain raw pilot transcripts, or upgrade quality claims.
