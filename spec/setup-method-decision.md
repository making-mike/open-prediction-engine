# Setup Method Decision

Status: implemented as schema-bound generated decisions over the current source-intake fixtures.

The setup method decision is the bridge between source intake, setup benchmark gates, and forecast execution. It reads a domain setup, the source-intake report, setup method policy, and any setup-specific benchmark gate, then explains which method is justified for the current data and why other methods are blocked.

It does not produce forecast artifacts.

## Contract

`setup-method-decision.schema.json` records:

- domain setup and source-intake bindings
- intake status and final method decision status
- selected method class or `none`
- setup policy flags for baseline, benchmark, leakage, and method-decision requirements
- selected setup benchmark gate ID, when a stronger method is chosen
- source-intake summary, including missing roles, rejected roles, proposed mappings, and source rejection reasons
- candidate method decisions for baseline, historical-conditioned, deterministic-statistical, model-assisted, external-reference, and ensemble methods
- claim boundaries that keep benchmark, calibration, production, and state-of-the-art claims blocked unless evidence supports them

## Current Decisions

Generated decisions live under:

```text
spec/fixtures/generated/setup-method-decision/
```

Current fixture outcomes:

- `accepted`: selects `deterministic_statistical` through a provisional setup benchmark gate; quality, calibration, production, and state-of-the-art claims remain blocked.
- `accepted_partial`: selects `historical_baseline`; stronger methods are blocked by missing forecast-time evidence.
- `needs_confirmation`: selects no method until proposed mappings are confirmed.
- `rejected`: selects no method because source intake detected rejected data, such as leakage, secrets, or insufficient historical sample.

## Commands

Inspect decision summaries:

```bash
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-method
```

Inspect one decision:

```bash
python3 scripts/ope.py setup-method --case accepted
python3 scripts/ope.py setup-method --case accepted_partial
python3 scripts/ope.py setup-method --case needs_confirmation
python3 scripts/ope.py setup-method --case rejected
```

Check generated decisions and semantic boundaries:

```bash
python3 scripts/generate_setup_benchmark_gate.py --check
python3 scripts/check_setup_benchmark_gate.py
python3 scripts/select_setup_method.py --check
python3 scripts/check_setup_method_decision.py
python3 scripts/ope.py setup-benchmark --check
python3 scripts/ope.py setup-method --check
```

## Guardrails

Baseline selection is allowed when the setup requires a baseline and source intake confirms enough historical data. Stronger methods must have confirmed source roles, clean leakage checks, positive baseline lift, and a setup-specific benchmark gate. A provisional benchmark gate can allow fixture execution while still blocking quality claims when sample-size thresholds are not met. Agent-inferred mappings, rejected sources, post-outcome leakage, and missing forecast-time evidence block method selection before forecast artifacts are created.
