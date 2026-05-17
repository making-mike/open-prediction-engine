# Setup Benchmark Gate

Status: implemented as schema-bound generated gates over the current source-intake fixtures.

A setup benchmark gate decides whether a non-baseline method may execute for one setup and source-intake profile. It is not a quality claim.

The current gate covers `deterministic_statistical` for the weather-logistics reference setup. Accepted intake receives `approved_provisional` because it has confirmed forecast-time weather evidence, clean comparable benchmark bindings, anti-leakage controls, and positive baseline lift. Quality, calibration, production, benchmark, and state-of-the-art claims remain blocked because the comparable sample is below the quality threshold.

## Contract

`setup-benchmark-gate.schema.json` records:

- setup, source-intake, source-manifest, and field-mapping bindings
- method class, baseline method ID, and candidate method ID
- baseline and candidate benchmark run IDs
- source policy, retrieval window, and comparable question-set checks
- anti-leakage controls
- execution and quality sample thresholds
- baseline lift
- execution and claim decisions
- reason codes and warnings

## Commands

```bash
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-benchmark --case accepted
python3 scripts/generate_setup_benchmark_gate.py --check
python3 scripts/check_setup_benchmark_gate.py
```

Refresh generated gates with:

```bash
python3 scripts/generate_setup_benchmark_gate.py --write
```

## Guardrails

- A gate can allow fixture execution while blocking public quality claims.
- A non-baseline forecast must bind the selected setup benchmark gate.
- Missing forecast-time source roles, proposed mappings, rejected intake, failed leakage checks, or non-positive baseline lift block execution.
- Resolution sources must remain excluded from forecast provenance.
