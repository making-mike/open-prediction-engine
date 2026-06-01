# Repeating Prediction Pilot Runbook

This runbook gives agents and supervised developers a checked local path for
testing repeating prediction setup comprehension. It is a readback workflow, not
a hosted scheduler, background worker, live-source fetch, forecast-quality claim,
or calibration claim.

## Start 100 Calibration Sessions In A Terminal

Use the checked campaign runner surface to inspect the 100-run calibration shape:

```bash
python3 scripts/ope.py prediction-campaign start --count 100 --calibration-target 100 --output-format jsonl
```

Expected readback:

- The runner prints bounded forecast-scheduling decisions.
- Forecast creation is still non-mutating unless a later command explicitly opts
  into ignored local state writes.
- The calibration target is a future evidence threshold, not evidence that
  calibration exists.

Then explain the current campaign state:

```bash
python3 scripts/ope.py prediction-campaign explain
```

The participant should be able to name the next forecast, next resolution
eligible time, append-readiness state, calibration threshold, and claim boundary.

## Open-Ended Campaign With Pause And Resume

Inspect the post-calibration restart example:

```bash
python3 scripts/ope.py repeating-prediction-setup --case post_calibration_restart_campaign
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle
```

Expected readback:

- The campaign reaches the measurement threshold in the checked scenario.
- The post-calibration policy schedules a pause/resume readback.
- No forecast method, model probability, campaign state, or hosted schedule is
  changed automatically.

For local recovery comprehension, inspect resume only when the caller explicitly
allows ignored local state inspection:

```bash
python3 scripts/ope.py prediction-campaign resume --from-local
```

## Pilot Task Card

Use the checked pilot-session packet task:

```bash
python3 scripts/ope.py pilot-session-packet --task repeating_prediction_campaign
```

Record only sanitized task completion, claim-boundary comprehension, trust, and
runtime-gap observations. Do not store raw transcripts, private source rows,
credentials, participant identity, or prompt logs.

## Claim Boundary

These commands can support local MVP usability evidence. They do not prove
forecast quality, calibration, hosted scheduling readiness, live-source
reliability, or stronger method readiness. Recurring prediction setup must be
evaluated before hosted scheduling or broader runtime work is promoted.
