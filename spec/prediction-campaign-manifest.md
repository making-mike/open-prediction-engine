# Prediction Campaign Manifest

`prediction-campaign-manifest.schema.json` defines the first checked local campaign manifest for repeated forecasts.

The manifest is a dry-run planning surface. It expands the checked repeating prediction setup into a local campaign ID, cycle ID, unique planned run IDs, forecast/question/resolution/scoring ID placeholders, candidate windows, duplicate keys, and status readbacks before any runner creates forecast artifacts.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign status
python3 scripts/ope.py prediction-campaign --check
```

Required boundaries:

- campaign state paths are relative and rooted under ignored `.ope/live/prediction-campaigns/`;
- normal checks do not write ignored campaign state;
- planned runs mint unique run, question, forecast, resolution, and scoring IDs instead of reusing fixture IDs;
- duplicate service date/window keys are explicit before any runner exists;
- skipped, missed, canceled, failed, manually stopped, and duplicate-blocked states have safe next actions;
- forecast-time source policy, resolution-only evidence roles, and claim boundaries are preserved at campaign and run level.

This manifest does not create forecast artifacts, mutate campaign state, start a runner, start a scheduler, fetch live data, resolve outcomes, append corpus evidence, store credentials, store private rows, or allow quality/calibration claims.
