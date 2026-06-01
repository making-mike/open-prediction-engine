# Resolution Jobs

Status: checked agent-facing read model.

Last reviewed: 2026-05-27.

Resolution jobs are the agent-friendly layer above saved forecast state and resolver commands. They let an agent ask OPE what needs resolving without knowing operating-system schedulers, `launchd`, cron syntax, or internal file conventions.

Default checked fixture:

```bash
python3 scripts/ope.py resolution-jobs
python3 scripts/ope.py resolution-jobs --check
```

Inspect ignored local live forward-run state:

```bash
python3 scripts/ope.py resolution-jobs --live
```

Inspect the checked prediction campaign forecast alongside forward-run jobs:

```bash
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z
```

Inspect one saved run:

```bash
python3 scripts/ope.py resolution-jobs \
  --live \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json
```

Run a local foreground scheduler over the same jobs:

```bash
python3 scripts/ope.py resolution-scheduler --live --watch --poll-seconds 60
```

Read the same checked registry through the transport-neutral agent adapter:

```bash
python3 scripts/ope.py agent-call --operation resolution_jobs
```

The registry is a read model. It never resolves forecasts, fetches live sources, writes resolution artifacts, or creates calibration claims. It tells the caller which checked command to run next.

Generated adapter error examples cover missing live workspaces and unreadable state files. Those envelopes expose stable error codes and safe plan status only; they do not reveal absolute local paths, state-file contents, raw diagnostics, or stack traces.

## Job Status

- `pending_due`: the resolution time has passed and an agent may call `resolve-due-forward-runs --execute` if live execution is approved.
- `pending_due` with `campaignId`: the campaign run has reached `resolutionEligibleAt`; the agent should inspect `prediction-campaign resolve` and may pass `--execute-resolvers --outcome-csv ... --write-local` or `--missing-outcome --write-local` for explicit local execution.
- `pending_not_due`: the resolution time is still in the future; the agent should wait or schedule a later check.
- `pending_not_due` with `campaignId`: a checked campaign forecast exists, but `resolutionEligibleAt` has not arrived; the agent should wait and must not run a campaign resolver yet.
- `already_resolved`: the forward run is no longer pending; the agent should read resolved outputs instead of resolving again.
- `invalid_state`: the saved state is missing required resolution metadata and should be inspected.

## Relationship To Resolvers

`resolution-jobs` answers "what should an agent do?"

`resolve-due-forward-runs` performs the checked dry-run scan and, with explicit `--execute`, can run due resolvers.

`resolution-scheduler` repeatedly asks the registry the same question in a foreground terminal and can call the checked resolver when both `--watch` and `--execute` are explicit.

`resolution-jobs --campaign predictioncampaign-001` reads the checked campaign manifest, forecast artifact, and forecast-write plan to expose the next resolution wait state for `forecast-1301`. With `--now 2026-06-11T07:15:00Z`, it routes the due campaign job to `prediction-campaign resolve` and includes the guarded local `--write-local` command shape. The registry itself does not write campaign state, execute a campaign resolver, create resolution/scoring records, or append corpus evidence.

This split keeps the default agent UX safe and inspectable while still allowing local scheduled or supervised execution through narrow commands.
