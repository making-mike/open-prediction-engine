# Prediction Campaign Resolution Attempt

Status: checked resolver-attempt readback with guarded local execution.

Last reviewed: 2026-05-31.

The prediction campaign resolution-attempt readback records what would happen when an agent inspects or explicitly requests resolver execution for a campaign run.

```bash
python3 scripts/ope.py prediction-campaign resolve
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --missing-outcome --write-local
python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers
python3 scripts/ope.py prediction-campaign resolve --check
```

It reports the selected run, forecast, resolution, and scoring IDs; whether the run is due; guard status; terminal/excluded/duplicate safety; failure category; retry eligibility; source-fetch metadata; sanitized diagnostics; and next action. The default checked fixture selects `predictionrun-1301` at its resolution time and remains a dry-run readback. With `--execute-resolvers`, the readback records an explicit attempt and blocks with `source_unavailable` until a checked campaign outcome source or explicit missing-outcome exclusion is declared. With `--write-local`, the runtime reads the already-written campaign forecast artifacts from ignored local state, resolves only after `resolutionEligibleAt`, writes resolution and scoring records idempotently, and updates campaign/run state without appending ledger evidence.

`--attempt-case` exposes checked non-mutating safety cases for `already_resolved`, `ambiguous`, `annulled`, `missed`, and `blocked_duplicate`. These cases prove that already-terminal, excluded, or duplicate campaign runs cannot create a second resolution, a second scoring record, or append-ready evidence.

`prediction-campaign start --now ... --execute-resolvers` calls this checked readback for due campaign runs during bounded foreground ticks, but forecast runner ticks still do not create resolution or scoring records.

## Boundary

Normal readbacks are not campaign resolution execution. They do not read ignored live state, fetch live data, write `.ope/live`, execute resolvers, create resolution artifacts, create scoring records, append corpus evidence, store credentials, store private rows, or allow quality claims.

Effectful local execution requires `--execute-resolvers --write-local` plus either `--outcome-csv` or `--missing-outcome`. It preserves idempotency, avoids duplicate resolution and duplicate scoring, binds outcome rows as resolution-only evidence, keeps sanitized diagnostics, and still does not append corpus evidence or allow calibration/quality claims.
