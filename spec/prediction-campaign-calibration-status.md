# Prediction Campaign Calibration Status

Status: checked calibration-status and continuation readback.

Last reviewed: 2026-05-31.

The prediction campaign calibration-status readback reports whether a campaign has enough comparable resolved evidence for calibration, whether exclusion risk blocks a claim, and which post-calibration policy would apply.

```bash
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case threshold_met --view readback
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case too_many_exclusions --view summary
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot
python3 scripts/ope.py prediction-campaign calibration-status --check
```

The checked cases cover below-threshold, threshold-met, too-many-exclusions, and post-calibration restart paths. Calibration summaries are generated only for threshold-met cases and remain measurement-only.

When `--from-local-ledger` is explicit, the readback uses the ignored local campaign evidence ledger and reports comparable count, exclusion rate, source/outcome provenance completeness, Brier score, baseline score, baseline lift, event rate, reliability buckets, and confidence caveats. Below-threshold, too-many-exclusions, and incomplete-provenance states block calibration claims.

## Boundary

This readback does not mutate campaign state, start a next cycle, fetch live data, execute resolvers, update forecast probabilities, change forecast methods, or tune a model. Normal checks do not read ignored local ledgers. Stronger method selection and probability recalibration stay behind a later explicit method-update gate.
