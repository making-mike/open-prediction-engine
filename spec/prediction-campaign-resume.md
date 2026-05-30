# Prediction Campaign Resume

Status: checked non-mutating resume readback.

Last reviewed: 2026-05-29.

The prediction campaign resume readback joins the checked campaign manifest, runner readback, forecast-write plan, unresolved forecast fixture, and campaign-aware resolution queue into one recovery surface for agents.

```bash
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --check
```

It answers whether the current checked campaign state can be safely inspected after interruption, which run IDs and ignored target paths are bound, which recovery commands are safe to call, and which future effectful steps remain blocked.

## Boundary

This is not an effectful resume loop. It does not read ignored live state, write `.ope/live`, create forecast artifacts, execute campaign resolvers, create resolution or scoring records, append corpus evidence, overwrite prior evidence, or allow quality claims.

Future effectful resume work must preserve the idempotency key and forecast-before-outcome trail before writing campaign state or running resolvers.
