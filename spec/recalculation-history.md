# Recalculation History

Status: implemented as fixture-safe trigger, run, evidence, artifact, and appended history records.

Recalculation lets OPE update a probability when new forecast-time evidence arrives without rewriting the prior forecast. The previous forecast remains in the history as `superseded`; the updated forecast is appended as `active` and points back to the forecast it supersedes.

It does not resolve or score the outcome.

## Contracts

- `recalculation-trigger.schema.json`: event that asks OPE to reconsider a forecast because a source changed, an API event arrived, a schedule fired, an agent submitted evidence, or a manual update occurred.
- `recalculation-run.schema.json`: result of accepting or rejecting the trigger, including previous probability, updated probability, changed evidence refs, method version, history append state, and rejection reasons.
- `forecast-history.schema.json`: append-only belief trail that keeps original, superseded, reaffirmed, withdrawn, and active forecast states.

## Current Fixture

Generated records live under:

```text
spec/fixtures/generated/recalculation/
```

The accepted fixture starts from `forecast-602` at probability `0.41`. A pre-close weather update arrives before `2026-06-03T00:00:00Z`, creating `forecast-801` at probability `0.57`. The generated `history-801` keeps the baseline, marks `forecast-602` as superseded, and appends `forecast-801` as active.

The rejected fixture submits post-outcome resolution evidence as a recalculation trigger. It is rejected and does not append a forecast state.

## Commands

Check generated recalculation records:

```bash
python3 scripts/ope.py recalculation
python3 scripts/ope.py recalculation --check
python3 scripts/check_recalculation_history.py
```

Refresh generated recalculation records:

```bash
python3 scripts/generate_recalculation_history.py --write
python3 scripts/ope.py recalculation --write
```

## Guardrails

Recalculation may use only evidence available before forecast close and appropriate for forecast-time roles. Resolution sources, post-outcome records, and evidence received after forecast close must be rejected for forecast-time recalculation. Those records belong in resolution and scoring, not in forecast updates.
