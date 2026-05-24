# Private Setup Adapter Conformance Matrix

Status: checked local adapter conformance fixture.

The private setup adapter conformance matrix summarizes checked envelope behavior for:

- source-builder cases
- source-handoff cases
- method-gate cases
- setup forecast-execution cases
- generated forecast readback through normal forecast operations
- one sanitized source-builder input error

The generated record lives at:

```text
spec/fixtures/generated/private-setup-adapter-conformance/ope-private-setup-adapter-conformance-matrix.generated.json
```

Generate or check it with:

```bash
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --check
python3 scripts/check_private_setup_adapter_conformance_matrix.py
python3 scripts/ope.py private-setup-adapter-conformance --check
```

## Boundary

This matrix is adapter conformance evidence only. It reuses existing generated envelopes and must not execute source reads, source-builder commands, source-handoff commands, forecast execution, resolution, scoring, credential handling, live fetching, or hosted runtime work.

Rows may record that a referenced envelope created fixture forecast artifacts, but the matrix itself does not create those artifacts. Forecast readback rows must continue to use normal `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary` operations instead of introducing a private setup read API.
