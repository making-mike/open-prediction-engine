# Prediction Campaign Explain

Status: checked pilot readback.

Last reviewed: 2026-05-31.

The prediction campaign explain readback gives agents one compact way to answer
the pilot-session questions for a repeating prediction campaign: what forecast
is next, when resolution becomes eligible, how much comparable evidence is
needed, whether append-readiness is satisfied, and which quality or calibration
claims remain blocked.

```bash
python3 scripts/ope.py prediction-campaign explain
python3 scripts/ope.py prediction-campaign explain --view task
python3 scripts/ope.py prediction-campaign explain --view workflow
python3 scripts/ope.py prediction-campaign explain --view agent
python3 scripts/ope.py prediction-campaign explain --view errors
python3 scripts/ope.py prediction-campaign explain --check
```

The checked readback binds the campaign manifest, runner, doctor, evidence
ledger, and calibration-status records for `predictioncampaign-001`. It also
contains the repeating prediction pilot task card, a short local workflow
runbook, five campaign agent-adapter readbacks, and sanitized error-envelope
examples for invalid interval, missed forecast close, unavailable live source,
duplicate campaign, unsafe source policy, and unsupported post-calibration
action.

## Boundary

This command is read-only. It does not create forecast artifacts, write or read
ignored live campaign state, fetch live data, execute resolvers, append corpus
evidence, update calibration, change methods, or start a hosted runtime. It is
pilot UX evidence, not forecast-quality or calibration evidence.
