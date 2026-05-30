# Prediction Campaign Forecast Creation

`prediction-campaign-forecast-creation.schema.json` defines the checked handoff from a ready campaign runner decision to the forecast artifact creation step.

The current surface is still read-only. It identifies the next ready campaign run, binds the question and forecast IDs reserved by the campaign manifest, checks the pre-creation gates, and shows where a later local runner may write ignored campaign artifacts. It does not create a forecast artifact, fetch live data, write `.ope/live/`, run a resolver, or append evidence.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-create --check
```

Required boundaries:

- the run must come from a ready runner decision and a unique manifest duplicate key;
- forecast creation must happen before `forecastCloseAt`;
- live source fetches remain explicit future behavior, never part of normal checks;
- normal checks only validate the creation request and planned artifact paths;
- quality, track-record, and calibration claims remain blocked until resolved comparable evidence exists.

This contract is the last read-only handoff before an effectful local runner can create a campaign forecast artifact.
