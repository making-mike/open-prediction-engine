# Prediction Campaign Method Update Action

Status: checked guarded apply/rollback command.

Last reviewed: 2026-05-31.

The prediction campaign method-update action exposes the explicit commands that can apply or roll back a local campaign method binding after the method-update gate and plan are ready.

```bash
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign apply-method-update --check
```

`--write-local` is required before any ignored local campaign state changes. Apply writes a prospective `method-binding.json` for future campaign forecasts and an audit artifact under `.ope/live/prediction-campaigns/{campaign}/method-updates/`. Rollback restores the baseline method binding and writes a rollback audit artifact. Both paths preserve prior forecast histories and do not rewrite old probabilities.

## Boundary

Normal checks do not read or write ignored method bindings. The action command does not fetch live data, execute resolvers, create forecast artifacts, rewrite histories, change method weights, write the method registry, start cycles, or allow quality claims. The default method remains `transitmethod-100` until a plan-ready action is run with `--write-local`; the first allowed non-baseline candidate is the transparent weather adjustment method `transitmethod-101`.
