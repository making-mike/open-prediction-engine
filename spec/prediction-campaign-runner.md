# Prediction Campaign Runner

`prediction-campaign-runner.schema.json` defines the checked terminal-runner readback for repeated prediction campaigns.

The default runner surface is intentionally dry-run. It lets an agent call the command shape, inspect supported recurrence flags, review normalized campaign creation input from flags or a checked setup JSON file, confirm JSONL versus human terminal output behavior, and see what the runner would do for planned runs before any forecast artifact or live campaign state is created.

Explicit local execution is available with `--write-local`. The current execution slice performs one foreground creation tick for the ready run, writes the checked lifecycle records plus minimal campaign/run state under ignored `.ope/live/prediction-campaigns/`, and remains idempotent on repeat calls. It does not sleep, poll future windows, fetch live data, execute resolvers, append corpus evidence, or make quality claims.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --check
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --setup-json spec/fixtures/generated/repeating-prediction-setup/ope-repeating-prediction-setup.generated.json --view campaign-creation
python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl
```

Required boundaries:

- `start` is a checked readback unless `--write-local` is explicit;
- normal checks do not sleep, poll, write `.ope/live/`, fetch live data, run resolvers, or create forecast artifacts;
- `--domain`, recurrence flags, and `--setup-json` are normalized into a dry-run campaign creation request before any local state mutation;
- the current explicit execution slice creates only the ready forecast and does not schedule later forecast windows yet;
- `--live-weather` and resolver execution remain explicit future flags, not default behavior;
- missed forecast close times are skipped rather than backfilled, with `missed_forecast_close` recorded as the exclusion reason and no comparable evidence append;
- captured stdout should use JSONL, while interactive terminals can print compact human status lines.

This contract is the bridge from campaign planning to a fuller foreground runner. It now implements normalized flag/setup-JSON campaign input, the first explicit local creation tick, and a schema-bound missed-run policy, while scheduling future forecasts, missed-run state mutation, resolver execution, and calibration-ledger append remain later slices.

The next handoff is `prediction-campaign-forecast-creation.schema.json`, exposed through:

```bash
python3 scripts/ope.py prediction-campaign forecast-create
```

That handoff binds the ready runner decision to planned forecast artifact IDs while still keeping normal checks read-only.
