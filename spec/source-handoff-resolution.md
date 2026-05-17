# Source Handoff Resolution

Status: implemented as checked fixture-mode resolution and scoring records.

Source handoff resolution closes the explicit source-builder-to-forecast lifecycle for `forecast-1102`. It reads the confirmed source-handoff forecast records, resolves the outcome from the declared local outcome source bound as `localsource-003`, scores the forecast, and emits calibration, track-record, and outcome-summary records.

The resolution uses the declared outcome file from the accepted handoff source manifest:

```text
spec/fixtures/local-source-files/outcome.csv
```

Blocked handoff runs are not resolved or scored.

## Generated Records

Generated records live under:

```text
spec/fixtures/generated/source-handoff-resolution/
```

The generator emits:

- resolved forecast question
- resolution record
- scoring report
- calibration summary
- track-record report
- outcome summary

The forecast card for `forecast-1102` exposes the resolved status, Brier score, baseline score, baseline lift, track-record link, and the provisional quality-claim boundary.

## Commands

Check source-handoff resolution records:

```bash
python3 scripts/ope.py resolve-source-handoff
python3 scripts/check_source_handoff_resolution.py
```

Read the resolved forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

Inspect the agent setup runbook that links source inspection, handoff, forecast execution, resolution, and read surfaces:

```bash
python3 scripts/ope.py source-handoff-runbook
```

Refresh generated resolution records:

```bash
python3 scripts/resolve_source_handoff_outcome.py --write
```

## Guardrails

- Only generated forecasts are resolved; blocked handoff runs remain non-generating and non-scored.
- Forecast provenance must not include the future declared outcome source.
- Resolution and scoring preserve the source-intake handoff, source-handoff method gate, source-intake report, setup benchmark gate, and setup method decision bindings through the outcome summary and forecast card.
- Quality and calibration claims remain blocked because there is only one comparable resolved source-handoff outcome.
