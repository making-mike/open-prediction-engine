# Prediction Campaign Resume

Status: checked non-mutating resume readback with local-state inspection.

Last reviewed: 2026-05-29.

The prediction campaign resume readback joins the checked campaign manifest, runner readback, forecast-write plan, unresolved forecast fixture, and campaign-aware resolution queue into one recovery surface for agents.

```bash
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign resume --from-local --view state
python3 scripts/ope.py prediction-campaign resume --check
```

It answers whether the current checked campaign state can be safely inspected after interruption, which run IDs and ignored target paths are bound, how many local run-state and idempotency-key records already exist, which recovery commands are safe to call, and which future effectful steps remain blocked.

## Boundary

This is not an effectful resume loop. Normal checks do not read ignored live state. `--from-local` may explicitly inspect ignored `.ope/live` campaign state, but it still does not write `.ope/live`, create forecast artifacts, execute campaign resolvers, create resolution or scoring records, append corpus evidence, overwrite prior evidence, or allow quality claims.

Future effectful resume work must preserve the idempotency keys and forecast-before-outcome trail before writing campaign state or running resolvers.
