# Resolution Scheduler

Status: checked foreground terminal scheduler.

Last reviewed: 2026-05-27.

The resolution scheduler is the local "keep working later" loop for OPE agents. It polls the checked resolution job registry and, only when explicitly allowed, asks the checked resolver to execute due transit forward runs.

It is intentionally not Trigger.dev, `launchd`, cron, GitHub Actions, Vercel Cron, or a hosted worker. An agent or developer starts it in a terminal on their own machine.

Default checked fixture:

```bash
python3 scripts/ope.py resolution-scheduler
python3 scripts/ope.py resolution-scheduler --check
```

One live dry-run tick:

```bash
python3 scripts/ope.py resolution-scheduler --live
```

Watch live jobs in the foreground without executing:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --poll-seconds 60
```

Watch and execute due jobs:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --execute \
  --download-static-gtfs \
  --poll-seconds 60
```

Target one saved run:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json
```

Every watch tick appends a JSONL record under `.ope/live/resolution-scheduler/scheduler-runs.jsonl`. The `.ope/live/` workspace is ignored, so local scheduling logs do not become public fixtures.

Agents can read the latest checked scheduler status through the adapter without starting the scheduler:

```bash
python3 scripts/ope.py agent-call --operation resolution_scheduler_status
```

That readback includes the last tick, shutdown reason, scheduler log path, execution mode, compact queue-state readbacks, and next recommended action. It is read-only and cannot execute due jobs.

Generated adapter error examples cover malformed scheduler logs and oversized scheduler readbacks. Those envelopes expose stable error codes and safe plan status only; they do not reveal absolute local paths, log contents, raw diagnostics, or stack traces.

For a human terminal, watch mode prints one compact status line per tick:

```text
2026-05-26T20:48:31Z | Waiting | 1 job, 0 due, 1 waiting, 0 resolved, 0 invalid | resolver not run | next check in 60s
```

When stdout is captured, watch mode prints JSONL by default so agents can parse it. Agents can force machine-readable output explicitly:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --output-format jsonl
```

Humans can force text explicitly:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --output-format text
```

When watch mode is stopped with `Ctrl+C`, the scheduler exits with code 130 and emits a clean shutdown summary instead of a Python traceback. JSONL mode emits one final schema-bound report with a `shutdown` object, including `shutdownReason`, `lastTickNumber`, and the scheduler log path. Text mode prints the same useful state as a short terminal line.

## Boundary

Normal checks perform one offline fixture tick. Live watching requires `--live --watch`. Resolver execution additionally requires `--execute`.

The scheduler can execute due resolver commands only through `resolve-due-forward-runs`, preserving the existing source policy, resolution logic, scoring boundary, and sample-size claim boundary. It does not create hosted schedulers, OS scheduler files, forecast artifacts, calibration claims, or production runtime claims.
