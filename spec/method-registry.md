# Method Registry

Status: implemented as a schema-bound fixture registry for the first weather-logistics wedge.

The method registry makes forecasting methods explicit before OPE can claim stronger forecast quality. A method must declare its class, model identity, compatible domain and output types, input requirements, uncertainty method, known limitations, and benchmark status.

## Current Registry

The first registry fixture is:

```text
spec/fixtures/methods/weather-logistics-method-registry.json
```

It defines these method classes:

- baseline
- deterministic statistical
- model-assisted
- retrieval-assisted
- ensemble
- external-reference

Only the baseline and deterministic statistical fixture methods are enabled. Model-assisted, retrieval-assisted, ensemble, and external-reference methods remain proposed until benchmark and leakage evidence supports selection.

The historical-only forecast path uses the baseline method directly. Its forecast probability must equal the historical-frequency baseline probability and must not include forecast-time weather API adjustments.

## Checks

Validate the registry and benchmark bindings:

```bash
python3 scripts/check_method_registry.py
```

Generate or check the current method-selection explanation:

```bash
python3 scripts/compare_forecasting_methods.py
python3 scripts/compare_forecasting_methods.py --check
python3 scripts/ope.py method-comparison
python3 scripts/select_forecasting_method.py
python3 scripts/select_forecasting_method.py --check
python3 scripts/ope.py method-selection
```

Normal release checks verify that enabled non-baseline methods:

- bind to a baseline method
- reference clean comparable benchmark runs
- use the same question set, source policy, and retrieval window as the baseline benchmark
- pass benchmark leakage validation
- produce a method-comparison report that covers every non-baseline registry method
- remain below quality-claim threshold until the minimum comparable sample size is reached
- produce a method-selection explanation that falls back to the baseline when no non-baseline method has comparable evidence for the request source policy

## Quality Boundary

Method-selection quality is reported only by:

- domain
- horizon bucket
- output type
- source policy
- coverage period
- sample size

## Boundary

The registry does not claim state-of-the-art performance. It only records which methods exist, which are enabled, and what benchmark evidence is available.
