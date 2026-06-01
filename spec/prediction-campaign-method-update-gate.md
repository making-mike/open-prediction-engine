# Prediction Campaign Method Update Gate

Status: checked read-only method-update gate.

Last reviewed: 2026-05-31.

The prediction campaign method-update gate reports whether campaign calibration evidence is sufficient to consider a stronger method, whether approval and anti-leakage checks are present, and whether an explicit method-update plan can be prepared.

```bash
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case threshold_met_needs_approval --view decision
python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view proposal
python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case regression_risk --view evidence
python3 scripts/ope.py prediction-campaign method-update-gate --check
```

The checked cases cover below-threshold evidence, threshold-met-but-unapproved review, approved plan readiness, and regression risk. A plan-ready readback still does not execute a method update; it only says the next safe action is a separate explicit update command with an audit trail.

## Boundary

This readback does not mutate campaign state, update forecast probabilities, change forecast methods, change method weights, write a method registry, start a next cycle, fetch live data, execute resolvers, or create forecast artifacts. Automatic method updates remain disallowed.
