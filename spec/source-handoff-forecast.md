# Source Handoff Forecast Execution

Status: implemented as checked fixture-mode execution records.

Source handoff forecast execution is the explicit step that turns an accepted source-handoff method gate into forecast artifacts. It consumes the source-intake handoff, source-handoff method gate, handoff-bound source-intake report, setup benchmark gate, and setup method decision.

It generates forecast outputs only for the confirmed builder-draft case. Unconfirmed, insufficient-data, and builder-rejected cases remain blocked run summaries.

## Contract

The execution records use `setup-forecast-run.schema.json` with source-handoff bindings:

- `sourceIntakeHandoffId`
- `sourceHandoffMethodGateId`
- `sourceIntakeReportId`
- `setupBenchmarkGateId`
- `setupMethodDecisionId`

Generated records live under:

```text
spec/fixtures/generated/source-handoff-forecast/
```

The confirmed builder-draft run emits:

- setup forecast run
- forecast question
- feature snapshot
- evidence packet
- forecast artifact
- forecast history

The read layer exposes `forecast-1102` through the normal forecast card and lifecycle bundle surfaces. The card setup binding includes the handoff and handoff-method gate IDs.

Once the separate source-handoff resolver runs, the same card exposes the resolved outcome, score, baseline score, baseline lift, and track-record link. Resolution is not implied by forecast execution.

## Commands

Inspect execution summaries:

```bash
python3 scripts/ope.py source-handoff-forecast
```

Inspect the generated confirmed handoff run:

```bash
python3 scripts/ope.py source-handoff-forecast --case confirmed_builder_draft
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

Resolve and score the generated handoff forecast:

```bash
python3 scripts/ope.py resolve-source-handoff
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

Inspect the agent setup runbook for the full source-handoff lifecycle:

```bash
python3 scripts/ope.py source-handoff-runbook
```

Check generated fixtures:

```bash
python3 scripts/run_source_handoff_forecast.py --check
python3 scripts/check_source_handoff_forecast.py
```

Refresh generated fixtures:

```bash
python3 scripts/run_source_handoff_forecast.py --write
```

## Guardrails

- Forecast execution is explicit; method-gate readiness alone does not create artifacts.
- Blocked handoff outcomes do not bind question IDs, forecast IDs, evidence packet IDs, forecast cards, bundles, or artifact paths.
- Normal checks stay offline and deterministic.
- No network access, live fetch, effectful generation, or ignored local live draft consumption is allowed.
- Generated handoff forecasts preserve source intake, handoff, benchmark, and method-decision bindings.
- Resolution and scoring are a separate lifecycle step and use only declared outcome sources.
- Quality, calibration, production, benchmark, and state-of-the-art claims remain blocked.
