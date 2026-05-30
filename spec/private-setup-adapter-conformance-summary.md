# Private Setup Adapter Conformance Summary

Status: checked compact read surface.

The private setup adapter conformance summary is the routine agent-facing view over the full private setup adapter conformance matrix. It records phase counts, operation coverage, artifact boundaries, sanitized-error coverage, and the read-surface boundary without embedding every generated adapter envelope.

The generated record lives at:

```text
spec/fixtures/generated/private-setup-adapter-conformance/ope-private-setup-adapter-conformance-summary.generated.json
```

Generate or check it with:

```bash
python3 scripts/generate_private_setup_adapter_conformance_summary.py --check
python3 scripts/check_private_setup_adapter_conformance_summary.py
python3 scripts/ope.py private-setup-adapter-conformance-summary --check
```

Read it through the agent adapter with:

```bash
python3 scripts/ope.py agent-call --operation private_setup_adapter_conformance_summary
```

## Size Budget

The compact summary declares a `sizeBudget` so routine agent reads stay bounded:

- `compactSummaryPayloadMaxBytes`: 12000
- `compactAgentEnvelopeMaxBytes`: 16000
- `fullMatrixReferenceMaxBytes`: 600000

The full matrix remains an implementer surface, read explicitly with:

```bash
python3 scripts/ope.py private-setup-adapter-conformance
```

Agents that request a smaller adapter envelope with `--max-bytes` receive a sanitized `response_too_large` error and no oversized payload:

```bash
python3 scripts/ope.py agent-call --operation private_setup_adapter_conformance_summary --max-bytes 1000
```

## Boundary

The summary is read-only conformance guidance. It may point to the full matrix for implementers, but it must not execute adapter calls, read private data, create source manifests, create field mappings, create forecast artifacts, resolve outcomes, score forecasts, fetch live data, store credentials, or create hosted runtime state.

Only the referenced full matrix embeds generated envelopes. Routine agents should prefer this compact summary before deciding whether to inspect the heavier matrix.
