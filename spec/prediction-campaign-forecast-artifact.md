# Prediction Campaign Forecast Artifact

The checked prediction campaign forecast artifact uses the existing OPE lifecycle contracts:

- `forecast-question.schema.json`
- `evidence-packet.schema.json`
- `forecast-artifact.schema.json`
- `forecast-history.schema.json`

It materializes `forecast-1301` from the ready campaign runner decision in fixture mode. The checked fixture artifact is unresolved, unscored, baseline-only, and bound to the campaign manifest and forecast-creation handoff as provenance. Runtime-created local artifacts can optionally include a historical pre-calibration binding when the runner is launched with `--pre-calibrate`; that changes only the prospective baseline probability source, not the method class. It does not write `.ope/live/`, fetch live data, run a resolver, append corpus evidence, or allow quality and calibration claims.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-artifact --check
python3 scripts/ope.py read --record-type forecast-card --id forecast-1301 --question-id question-1301
```

Required boundaries:

- the artifact must reuse the run, question, forecast, and source-policy IDs reserved by the campaign manifest and forecast-creation handoff;
- forecast creation must occur before `forecastCloseAt` and before the horizon starts;
- the forecast output must equal the baseline output until method gates allow stronger campaign methods;
- optional pre-calibration may update the prospective baseline probability for runtime-created local forecast artifacts only;
- resolution and scoring links remain empty until post-window outcome evidence is explicitly resolved;
- normal checks validate checked fixtures only and do not mutate ignored local campaign state.
