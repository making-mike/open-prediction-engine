# Private Source Adapter Capabilities

Status: implemented as a checked domain-agnostic capability contract.

The private source adapter capability contract tells agents what source kinds OPE can inspect now, what requires caller confirmation, and what is only planned. It is deliberately separate from source execution: declaring a private API, database, or upload adapter does not fetch, parse, store credentials, or create forecast evidence.

The contract is schema-bound by:

```text
spec/private-source-adapter-capability.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/private-source-adapters/
```

The companion outcome matrix is documented in `spec/private-source-adapter-outcomes.md`.

## Commands

Inspect adapter capabilities:

```bash
python3 scripts/ope.py private-source-adapters
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-source-adapters --check
python3 scripts/check_private_source_adapter_capabilities.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_source_adapter_capabilities.py --write
```

## Source Kinds

The contract binds to the source kinds from the private setup workflow:

- `local_file`: implemented as a fixture-safe local source-builder path.
- `manual_mapping`: implemented as an approval-gated fixture confirmation path.
- `auto_evidence_connector`: implemented as policy-bound fixture replay, not production live fetching.
- `manual_upload`: planned contract only.
- `private_api`: planned contract only.
- `private_database`: planned contract only.

## Guardrails

- Capability declarations do not execute source reads.
- Normal checks stay offline and fixture-safe.
- No adapter may store credentials or include secrets in generated artifacts.
- Private APIs, private databases, and manual uploads return `runtime_not_implemented` until an explicit runtime lands.
- Future runtimes must declare approval, credential, privacy, freshness, rate-limit, and audit-log boundaries before setup execution.
