# Private Source Adapter Bridge

Status: implemented as a checked domain-agnostic intake bridge.

The private source adapter bridge maps adapter outcome decisions to the first allowed local entrypoint. It tells agents whether they can run source-builder, ask for mapping confirmation, use fixture evidence, wait for a future runtime, replace a source, or stop.

The bridge is schema-bound by:

```text
spec/private-source-adapter-intake-bridge.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/private-source-adapters/
```

## Commands

Inspect the bridge:

```bash
python3 scripts/ope.py private-source-adapter-bridge
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-source-adapter-bridge --check
python3 scripts/check_private_source_adapter_intake_bridge.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_source_adapter_intake_bridge.py --write
```

## Entrypoints

- `local_file` routes to `python3 scripts/ope.py source-builder`.
- `manual_mapping` waits for caller confirmation, then routes to `python3 scripts/ope.py source-handoff --case confirmed_builder_draft`.
- `auto_evidence_connector` routes to `python3 scripts/ope.py gather-evidence` in fixture mode.
- `manual_upload`, `private_api`, and `private_database` have no current entrypoint.
- `unregistered_source` and `unsafe_source` cannot enter setup.

## Guardrails

- The bridge does not execute source reads.
- The bridge does not create source manifests, field mappings, forecast artifacts, forecast cards, scoring records, live fetch results, or credential records.
- Planned private runtimes stay non-generating.
- Forecast and scoring records still require source intake, method gates, and explicit forecast execution.
