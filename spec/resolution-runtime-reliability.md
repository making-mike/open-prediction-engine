# Resolution Runtime Reliability

Status: checked fixture read model.

Last reviewed: 2026-06-11.

This contract records the failure taxonomy, retry guidance, and provenance boundary for the local resolution runtime around transit forward runs, resolution jobs, foreground scheduler ticks, resolver attempts, local live captures, and shutdown readbacks.

Default checked fixture:

```bash
python3 scripts/ope.py resolution-runtime-reliability
python3 scripts/ope.py resolution-runtime-reliability --check
```

The generated record is descriptive. It does not execute resolver commands, start the scheduler, read ignored live files, fetch live data, create forecasts, create resolutions, create scores, store credentials, or create hosted or OS scheduler state.

## Failure Taxonomy

The checked taxonomy covers:

- `source_availability`
- `empty_sources`
- `decode_failures`
- `schedule_join_failures`
- `coverage_gaps`
- `late_capture_window`
- `resolver_failures`
- `stale_state`
- `invalid_state`
- `network_timeouts`
- `rate_limits`

`late_capture_window` records an outcome capture attempted so long after the scheduled resolution time that a live snapshot can no longer contain the forecast window's trips. It is not retryable against the live feed; the run is marked `blocked` with reason `stale_capture_window` and may only resolve later from an on-time saved capture.

Every failure row declares `retryable`, `retryAfter`, `nextAction`, sanitized diagnostics, safe signals, affected runtime stages, and artifact/claim boundaries. Raw diagnostics, stack traces, absolute paths, forecast artifacts, resolution artifacts, scoring records, and calibration claims remain blocked.

## Provenance Ledger

The ledger records compact runtime actions for forecast-time live capture, forward forecast execution, resolution job scans, scheduler ticks, resolver attempts, and shutdown readbacks. Each row records the local command, timestamp, source provider, source role, forecast-time versus resolution-only classification, allowed artifact paths, hash status, and sanitized diagnostics.

Resolution outcome rows are marked `resolutionOnlyEvidence: true` and `forecastTimeEvidence: false`. They must not be moved into forecast-time provenance, benchmark inputs, model inputs, recalculation triggers, or source manifests.

## Live Boundary

Live captures stay local and opt-in under `.ope/live/`. Normal checks use checked fixtures and do not use live network access. A future hosted runtime still needs explicit source policy, retention, freshness, and failure behavior before OPE can make production live connector or calibration claims.
