# Prediction Campaign Doctor

Status: checked compact campaign health readback.

Last reviewed: 2026-05-31.

The prediction campaign doctor readback gives agents one compact answer for campaign health, due runs, waiting runs, failed runs, blocked runs, append-ready runs, duplicate protection, recovery posture, and next action.

```bash
python3 scripts/ope.py prediction-campaign doctor
python3 scripts/ope.py prediction-campaign doctor --view health
python3 scripts/ope.py prediction-campaign doctor --view queues
python3 scripts/ope.py prediction-campaign doctor --check
```

The checked fixture uses the campaign resolution clock `2026-06-11T07:15:00Z`, so `predictionrun-1301` is due. The doctor routes that run to the checked `prediction-campaign resolve` readback and records that effectful resolver execution is still blocked until a checked outcome source exists.

## Boundary

This is not a live-state inspector or repair tool. It does not read ignored campaign state, write `.ope/live`, execute resolvers, fetch live data, create resolution artifacts, create scoring records, append corpus evidence, overwrite prior evidence, or allow quality claims.

Future effectful doctor or repair commands must preserve duplicate-key blocking, already-terminal run handling, idempotency keys, and the forecast-before-outcome trail before writing campaign state.
