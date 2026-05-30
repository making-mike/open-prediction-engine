# Prediction Campaign Runner

`prediction-campaign-runner.schema.json` defines the checked terminal-runner readback for repeated prediction campaigns.

The current runner surface is intentionally dry-run only. It lets an agent call the command shape that will later start a local foreground campaign runner, inspect supported recurrence flags, confirm JSONL versus human terminal output behavior, and see what the runner would do for planned runs before any forecast artifact or live campaign state is created.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --check
```

Required boundaries:

- `start` is a checked readback until the later execution slice lands;
- normal checks do not sleep, poll, write `.ope/live/`, fetch live data, run resolvers, or create forecast artifacts;
- `--live-weather` and resolver execution remain explicit future flags, not default behavior;
- missed forecast close times are skipped rather than backfilled;
- captured stdout should use JSONL, while interactive terminals can print compact human status lines.

This contract is the bridge from campaign planning to a future foreground runner. It does not yet implement the effectful runner loop.

The next handoff is `prediction-campaign-forecast-creation.schema.json`, exposed through:

```bash
python3 scripts/ope.py prediction-campaign forecast-create
```

That handoff binds the ready runner decision to planned forecast artifact IDs while still keeping normal checks read-only.
