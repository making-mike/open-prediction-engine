# Repeating Prediction Setup

`repeating-prediction-setup.schema.json` defines the first checked contract for repeated forecast campaigns.

The contract is intentionally non-executing. It lets an agent describe recurrence, stop conditions, source policy, forecast template, resolution timing, and post-calibration behavior before OPE has a campaign manifest, runner, scheduler, or append-only campaign evidence ledger.

Run it locally with:

```bash
python3 scripts/ope.py repeating-prediction-setup
python3 scripts/ope.py repeating-prediction-setup --section schedules
python3 scripts/ope.py repeating-prediction-setup --section examples
python3 scripts/ope.py repeating-prediction-setup --case daily_100_run_transit_calibration
python3 scripts/ope.py repeating-prediction-setup --case post_calibration_restart_campaign
python3 scripts/ope.py repeating-prediction-setup --check
```

The checked examples cover finite count, until-date, open-ended, interval, selected weekday/window, calibration-threshold, and post-calibration restart policies.

Required boundaries:

- every generated run must forecast before close;
- resolution can happen only after the declared horizon;
- forecast-time source roles and resolution-only source roles stay separate;
- source policy, provenance, and unique run/question/forecast/resolution/scoring IDs are required by future campaign manifests;
- calibration thresholds produce readbacks only, not automatic method tuning or public quality claims.

This contract does not create forecast artifacts, mutate campaign state, install an OS scheduler, write cron files, start hosted workers, fetch live data, store credentials, store private rows, append corpus evidence, or allow quality/calibration claims.
