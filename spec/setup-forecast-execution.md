# Setup Forecast Execution

Setup forecast execution is the first bridge from private engine setup records to actual forecast artifacts.

The current implementation is fixture-mode only. It consumes:

- a `domain-setup` record
- a `source-manifest` and `field-mapping`
- a generated `source-intake-report`
- a generated `setup-benchmark-gate`, when a non-baseline method is selected
- a generated `setup-method-decision`

For accepted and accepted-partial intake, `scripts/run_setup_forecast.py` emits a `setup-forecast-run` summary plus the generated question, feature snapshot, evidence packet, forecast artifact, and forecast history. The read layer then exposes the same forecast through the normal forecast card and lifecycle bundle surfaces, including a `setupBinding` that links the card back to the setup run, source intake report, benchmark gate, and method decision.

For needs-confirmation and rejected intake, the setup forecast run is blocked. Blocked runs do not bind question IDs, forecast IDs, evidence packet IDs, forecast cards, bundles, or artifact paths.

`scripts/run_source_handoff_forecast.py` applies the same execution boundary to source-builder handoffs. It generates `forecast-1102` only for the confirmed builder-draft handoff that already passed source intake, source-handoff method gating, setup benchmark gating, and setup method selection. Unconfirmed, insufficient-data, and builder-rejected handoff cases remain blocked run summaries.

## Current Method Boundary

Two execution paths are currently implemented:

- `historical_baseline` for accepted-partial intake where only baseline data is usable.
- `deterministic_statistical` for accepted intake when a setup benchmark gate approves provisional fixture execution.

Generated baseline forecasts use Laplace add-one smoothing over the accepted historical baseline source:

```text
probability = (positive_outcome_count + 1) / (row_count + 2)
```

The deterministic fixture path uses the historical baseline plus the accepted forecast-time precipitation feature. It may differ from the baseline only when the setup method decision binds an approved setup benchmark gate. This allows non-baseline execution while keeping quality claims blocked until sample-size and outcome evidence support them.

## Guardrails

- Normal checks stay offline and deterministic.
- No network access, live fetch, effectful generation, or ignored local live draft consumption is allowed.
- Forecast provenance uses forecast-time historical baseline sources and, for deterministic execution, accepted forecast-time weather sources.
- Resolution sources are kept out of forecast provenance.
- Non-baseline execution requires a setup benchmark gate and does not create calibration, production, or state-of-the-art claims.
- Blocked setup decisions remain non-generating and include reason codes plus next actions.
- Source-handoff execution must bind `sourceIntakeHandoffId` and `sourceHandoffMethodGateId` before creating artifacts.
- Forecast cards include setup bindings but do not expose evidence traces unless a full auto-evidence pipeline trace exists.

## Commands

```bash
python3 scripts/run_setup_forecast.py --check
python3 scripts/check_setup_forecast.py
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-forecast
python3 scripts/ope.py read --record-type forecast-card --id forecast-901 --question-id question-901
python3 scripts/ope.py source-handoff-forecast
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

Refresh generated setup forecast records with:

```bash
python3 scripts/run_setup_forecast.py --write
python3 scripts/run_source_handoff_forecast.py --write
```
