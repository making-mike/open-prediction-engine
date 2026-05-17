# Private Source Adapter Outcomes

Status: implemented as a checked domain-agnostic outcome matrix.

The private source adapter outcome matrix turns adapter capabilities into deterministic agent next actions before setup execution. It lets an agent distinguish fixture-available sources, approval-gated fixture steps, planned runtimes, unsupported sources, missing credential runtime, and unsafe sources without reading private data or creating forecast records.

The matrix is schema-bound by:

```text
spec/private-source-adapter-outcome-matrix.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/private-source-adapters/
```

The companion intake bridge is documented in `spec/private-source-adapter-bridge.md`.

## Commands

Inspect the outcome matrix:

```bash
python3 scripts/ope.py private-source-adapter-outcomes
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-source-adapter-outcomes --check
python3 scripts/check_private_source_adapter_outcome_matrix.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_source_adapter_outcome_matrix.py --write
```

## Outcome Classes

- `available_fixture`: proceed to the row-specific checked fixture command.
- `approval_required_fixture`: request caller confirmation before setup continues.
- `planned_runtime`: wait for an explicit runtime implementation.
- `unsupported_source`: replace the source kind before setup.
- `credential_missing`: wait for a credential-safe runtime before asking for or using credentials.
- `rejected_unsafe_source`: reject the source and keep it out of setup, forecasts, and scoring.

## Guardrails

- The matrix does not execute source reads.
- The matrix does not create source manifests, forecast artifacts, cards, scoring records, or credential records.
- Manual uploads, private APIs, and private databases remain runtime-not-implemented.
- Unregistered and unsafe sources cannot enter source intake, method gates, forecast execution, resolution, or scoring.
