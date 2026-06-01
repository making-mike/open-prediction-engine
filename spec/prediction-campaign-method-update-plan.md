# Prediction Campaign Method Update Plan

Status: checked method-update plan before explicit apply/rollback.

Last reviewed: 2026-05-31.

The prediction campaign method-update plan records the approval artifact, guarded effectful command shape, rollback record, and preflight checks that are required after `prediction-campaign method-update-gate` reports readiness.

```bash
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case approval_missing --view approval
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case rollback_missing --view rollback
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case regression_risk --view preflight
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command
python3 scripts/ope.py prediction-campaign method-update-plan --check
```

The checked cases cover a gate-blocked default, candidate regression risk, missing approval artifact, missing rollback record, and a plan-ready readback. A plan-ready readback still does not apply the update; it declares the explicit apply/rollback command shape and the audit material required before the action command can mutate ignored local state.

## Boundary

This readback does not write a plan artifact, write campaign state, write method registries, update forecast probabilities, change forecast methods, change method weights, fetch live data, execute resolvers, create forecast artifacts, or start campaign cycles. Automatic method updates remain disallowed; the apply/rollback runtime is separate and requires `--write-local`.
