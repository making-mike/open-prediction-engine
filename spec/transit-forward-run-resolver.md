# Transit Forward Run Resolver

Status: checked local resolver-agent scan; optional live execution remains explicit.

Last reviewed: 2026-06-11.

This contract describes the local programmatic resolver for weather-transit-delay forward runs. It does not invent resolution logic. It scans saved `forward-run-state.json` files, classifies each run, and can call the checked `transit-delay-forward-run --phase resolve` command for runs that are due.

Default fixture scan:

```bash
python3 scripts/ope.py resolve-due-forward-runs
python3 scripts/ope.py resolve-due-forward-runs --check
```

Live local dry run:

```bash
python3 scripts/ope.py resolve-due-forward-runs --live
```

Execute due local runs:

```bash
python3 scripts/ope.py resolve-due-forward-runs \
  --live \
  --execute \
  --download-static-gtfs
```

To target one saved run:

```bash
python3 scripts/ope.py resolve-due-forward-runs \
  --live \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json
```

For the safer agent read model, inspect resolution jobs instead:

```bash
python3 scripts/ope.py resolution-jobs --live
```

For a local foreground polling loop, use the checked terminal scheduler:

```bash
python3 scripts/ope.py resolution-scheduler --live --watch --poll-seconds 60
```

## Decisions

The resolver emits one decision per state:

- `due_pending`: the run is still `forecast_recorded` and `now >= resolveAt`
- `due_stale_capture`: the run is due, but `now` is more than the capture-lag tolerance past `resolveAt`, so a live snapshot can no longer contain the forecast window's trips; executing it marks the run `blocked` with reason `stale_capture_window` instead of resolving
- `not_due`: the run is still pending but the resolution time is in the future
- `already_resolved`: the run is already `resolved`, `scored`, `ambiguous`, or `blocked`
- `executed`: the resolver command completed and rewrote the state
- `failed`: the resolver command failed and should be retried after inspection
- `invalid_state`: the state file cannot be parsed into a resolvable forward-run state

## Boundary

Normal checks do not scan `.ope/live/`, fetch HSL data, execute resolver commands, create resolution records, or create calibration claims. Live scanning requires `--live`; executing resolver commands additionally requires `--execute`.

The resolver is a local runtime scaffold, not a hosted scheduler. The repository now includes a foreground terminal scheduler for local polling, but it still does not create Trigger.dev jobs, cron entries, `launchd` plists, or hosted workers. Agents should prefer `resolution-jobs` for read-only planning, `resolution-scheduler` for local polling, and this resolver only when execution is approved.
