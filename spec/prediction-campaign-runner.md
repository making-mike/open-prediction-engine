# Prediction Campaign Runner

`prediction-campaign-runner.schema.json` defines the checked terminal-runner readback for repeated prediction campaigns.

The default runner surface is intentionally dry-run. It lets an agent call the command shape, inspect supported recurrence flags, review normalized campaign creation input from flags or a checked setup JSON file, inspect the forecast scheduling plan, confirm JSONL versus human terminal output behavior, and see what the runner would do for planned runs before any forecast artifact or live campaign state is created.

Explicit local forecast creation is available with `--write-local`. The current execution slice performs a bounded foreground scheduling tick, uses `--now` as the runner clock when supplied, writes standard lifecycle records plus minimal campaign/run state for the next due run under ignored `.ope/live/prediction-campaigns/`, and remains idempotent on repeat calls. With `--execute-resolvers`, the runner calls the checked campaign resolution-attempt readback for due runs. It also exposes the prospective method-binding path used after an approved `apply-method-update` command, but the dry-run default remains baseline-only and does not read ignored local method bindings. It does not fetch live data, create resolution records, create scoring records, append corpus evidence, or make quality claims. Long-running polling across later future windows remains a later slice.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --check
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-09-18T00:00:00Z --count 100 --full-materialization --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-11T07:15:00Z --execute-resolvers --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --setup-json spec/fixtures/generated/repeating-prediction-setup/ope-repeating-prediction-setup.generated.json --view campaign-creation
python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl
```

Required boundaries:

- `start` is a checked readback unless `--write-local` is explicit;
- normal checks do not sleep, poll, write `.ope/live/`, fetch live data, run resolvers, or create forecast artifacts;
- `--domain`, recurrence flags, and `--setup-json` are normalized into a dry-run campaign creation request before any local state mutation;
- the forecast schedule view maps ready, waiting, missed, and duplicate candidate states to the explicit local write command or non-mutating next action;
- the method-selection binding names `.ope/live/prediction-campaigns/{campaign}/method-binding.json` for future approved local method updates while keeping normal checks baseline-only;
- `--watch --max-ticks` runs bounded foreground forecast scheduling ticks, and `--write-local` is still required before any tick writes a due forecast;
- `--now` moves the runner clock for deterministic next-due scheduling checks; for example, `2026-06-12T00:00:00Z` selects `predictionrun-1302`;
- `--full-materialization --count 100` lets the runner inspect the full Helsinki pilot plan; for example, `2026-09-18T00:00:00Z` selects `predictionrun-1400`;
- the current explicit execution slice creates one due forecast per tick and skips already-created run state;
- `--execute-resolvers` calls the checked non-mutating campaign resolution-attempt readback for due runs and still cannot create resolution or scoring records;
- `--live-weather` remains an explicit future flag, not default behavior;
- missed forecast close times are skipped rather than backfilled, with `missed_forecast_close` recorded as the exclusion reason and no comparable evidence append;
- captured stdout should use JSONL, while interactive terminals can print compact human status lines.

This contract is the bridge from campaign planning to a fuller foreground runner. It now implements normalized flag/setup-JSON campaign input, a checked forecast scheduling plan, bounded foreground ticks, next-due local forecast creation, checked due-run resolver-attempt calls, and a schema-bound missed-run policy, while long-running future-window polling, missed-run state mutation, effectful resolver execution, and calibration-ledger append remain later slices.

The next handoff is `prediction-campaign-forecast-creation.schema.json`, exposed through:

```bash
python3 scripts/ope.py prediction-campaign forecast-create
```

That handoff binds the ready runner decision to planned forecast artifact IDs while still keeping normal checks read-only.
