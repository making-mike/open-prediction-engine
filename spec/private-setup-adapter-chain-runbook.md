# Private Setup Adapter Chain Runbook

Status: implemented as checked guidance for the local private setup adapter chain.

This runbook shows agents how to move through the local-file private setup path using the transport-neutral adapter operations:

1. read private setup guidance
2. inspect caller-approved local files through source-builder guidance
3. route confirmed mappings through source-handoff guidance
4. inspect method-gate readiness
5. run explicit setup forecast execution only for the confirmed checked case
6. read the generated forecast through normal forecast card, lifecycle bundle, resolution status, and scoring summary operations

The runbook is schema-bound by:

```text
spec/private-setup-adapter-chain-runbook.schema.json
```

Generated output lives at:

```text
spec/fixtures/generated/private-setup-adapter-chain/ope-private-setup-adapter-chain-runbook.generated.json
```

## Commands

Inspect the runbook:

```bash
python3 scripts/ope.py private-setup-adapter-runbook
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-setup-adapter-runbook --check
python3 scripts/check_private_setup_adapter_chain_runbook.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_adapter_chain_runbook.py --write
```

## Guardrails

- The runbook is guidance only and does not call adapter operations.
- Mapping-confirmation, insufficient-data, and rejected-source branches stop before forecast artifacts.
- Only the confirmed checked handoff may reach setup forecast execution.
- Generated setup forecasts are read through normal `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary` operations.
- The runbook does not create source manifests, forecast artifacts, scoring records, credentials, hosted APIs, or production adapter runtime claims.
