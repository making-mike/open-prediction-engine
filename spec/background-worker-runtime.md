# Background Worker Runtime

Status: checked local readback and dry-run loop.

Last reviewed: 2026-06-04.

This contract defines the first Milestone 116 worker surface: a bounded local worker or sidecar readback plus a one-tick dry-run loop over the existing lifecycle operation store, embedded internal API, and prediction workspace registry. It is intentionally not a daemon, hosted worker, network listener, OS scheduler, or source-fetch runtime in normal checks.

Checked readback:

```bash
python3 scripts/ope.py background-worker
python3 scripts/ope.py background-worker --view health
python3 scripts/ope.py background-worker --view tick
python3 scripts/ope.py background-worker --view loop
python3 scripts/ope.py background-worker --view commit
python3 scripts/ope.py background-worker --view control
python3 scripts/ope.py background-worker --view sidecar
python3 scripts/ope.py background-worker --view blocked
python3 scripts/ope.py background-worker --view boundary
python3 scripts/ope.py background-worker --check
```

The worker commands are `health`, `pause`, `resume`, `drain`, `shutdown`, `run_one_tick`, and `run_bounded_loop`. The current surface defines their bounded semantics and readbacks; it does not install a background service or mutate runtime state during normal checks.

The worker queue reads prediction workspace read models such as active predictions, due forecasts, due resolution jobs, append readiness, failed operations, recovery actions, and source-health blockers. The queue readback exposes no raw SQL and no raw file layout.

One-tick execution is bound to the embedded internal API `run_tick` operation. The checked readback reports the next operation, prediction and campaign IDs, receipt placeholder, idempotency key, lease ID, lease scope, preflight status, read-model refs, blocking guards, and safe next action. This is the deterministic foreground-equivalent path that future effectful loops must preserve.

The bounded loop readback calls the shared `internal_api_runtime.call_internal_api()` helper for one dry-run `run_tick`, preserving the same idempotency key, lease ID, receipt placeholder, lifecycle operation, and non-mutation boundary as the foreground path. It also reports queue polling, cancellation checks, bounded retry/backoff policy, resource usage, termination reason, and source-fetch status.

The approved commit readback exercises the lifecycle operation store in an ephemeral SQLite database. It maps the worker `run_tick` path to a `forecast.create` lifecycle operation, writes an operation receipt, idempotency key, immutable forecast records, and read-model rows, reserves and releases the worker lease, and reports that normal checks write no persistent state.

The control-state readback exercises pause, resume, drain, and shutdown as lifecycle-backed `state.import_json` projection upserts into a `worker_control_state` read model. Each control write returns an operation receipt, idempotency key, lease reservation/release, read-model effect, and raw-control-mutation block. The health readback reads the resulting control state without writing state.

The durable sidecar readback defines the local activation semantics for embedded in-process use and an explicit future local sidecar process. It reads worker control state before ticks, uses the bounded loop and approved commit path, emits heartbeat and clean shutdown readbacks, keeps the host event loop unowned, and does not start a process during normal checks.

The sidecar boundary keeps the first worker local-only: no network listener, no OS scheduler installation, no hosted worker requirement, no credential values in records, no raw SQL exposure, no raw file-layout exposure, no automatic live-source execution, and no automatic method upgrade.

Blocked readbacks cover paused predictions, lease conflicts, resource limits, and source policies that block automatic live fetches. These cases stop before worker execution and return sanitized diagnostics plus safe next actions.

Future work may add an explicit local sidecar process command, but it must continue to use the same internal API and lifecycle operation receipts, preserve one-tick equivalence, honor resource limits, and keep live-source execution explicit and opt-in.
