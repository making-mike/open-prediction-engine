# Prediction Workspace Registry

Status: stable registry readback defined.

Last reviewed: 2026-06-03.

The prediction workspace registry is the first multi-prediction read model for embedded OPE usage. It gives agents stable `predictionId`, `campaignId`, `domainId`, `sourceBindingId`, and `scheduleId` bindings without exposing raw database tables or local file layout.

Checked readback:

```bash
python3 scripts/ope.py prediction-workspace-registry
python3 scripts/ope.py prediction-workspace-registry --prediction-id prediction-001
python3 scripts/ope.py prediction-workspace-registry --check
```

The checked fixture includes one active weather-transit-delay prediction and one paused private berth-availability setup. Each entry includes owner metadata, caller metadata, lifecycle operation summary fields, read-model references, and raw-storage exposure flags.

The `readModels` section exposes compact rows for all predictions, active predictions, due forecasts, due resolutions, blocked operations, failed operations, source-health blockers, calibration progress, and track-record progress. These are readbacks for agents; they are not effectful queues yet.

The `configurationLifecycleOperations` section defines the registry mutation semantics for creating, updating, archiving, and redacting prediction configuration. Each operation requires receipts, idempotency, and leases; preserves audit history; blocks raw config mutation; and replaces physical delete with archive tombstones or redaction receipts.

The `perPredictionConcurrencyControls` section gives each prediction its own idempotency namespace and lease row. It allows concurrent work on different predictions while blocking concurrent mutation of the same prediction and exposing stale-lease recovery guidance.

The `workspaceResourceControls` section declares maximum active predictions, queued operations, readback bytes, and per-prediction execution budgets. Current counts stay within limits in the checked fixture.

The `isolationChecks` section covers cross-prediction writes to forecast records, source bindings, method bindings, and read models. Each cross-prediction attempt is blocked and requires an audit record, while same-prediction writes remain allowed only through normal lease-gated operations.

This registry step is readback-only. It does not create, update, start, pause, resume, archive, redact, or delete predictions. Those effectful operations remain behind the embedded internal API and lifecycle operation receipts.

The next roadmap step is the domain and source configuration package.
