# Prediction Campaign Pre-Calibration

Status: optional historical-only pre-pilot readback and guarded local binding.

`prediction-campaign pre-calibration` computes a baseline probability from approved historical transit delay rows before the Helsinki pilot starts. It stays on `transitmethod-100`; it does not select a stronger method, fetch live sources, create forecasts, resolve outcomes, append ledger rows, or make quality claims.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign pre-calibration
python3 scripts/ope.py prediction-campaign pre-calibration --view method
python3 scripts/ope.py prediction-campaign pre-calibration --history-source spec/fixtures/local-source-files/transit-delay-history.csv
python3 scripts/ope.py prediction-campaign pre-calibration --write-local
python3 scripts/ope.py prediction-campaign start --count 100 --full-materialization --pre-calibrate --write-local --output-format jsonl
```

Required boundaries:

- pre-calibration is opt-in through `pre-calibration` or `start --pre-calibrate`;
- the history source must contain scoped, resolved historical outcomes before the first pilot service date;
- default checked history requires at least 30 scoped resolved rows and uses Laplace add-one smoothing;
- `--write-local` is required before any `.ope/live` pre-calibration artifact or method binding is written;
- the binding is prospective-only and may affect future campaign forecast artifacts, not prior forecast histories;
- pre-calibration keeps the baseline method class and does not bypass the later method-update gate.
