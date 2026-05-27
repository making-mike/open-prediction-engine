# Transit Method Options

The transit method options record explains which forecasting methods are available for the weather-transit-delay MVP loop and why early public transport runs remain baseline-first.

Generate the checked read surface with:

```bash
python3 scripts/ope.py transit-method-options
```

This command reads the checked forward-run corpus and baseline track-record gate. It does not execute forecasts, resolve outcomes, score runs, select a non-baseline method, fetch live data, read ignored `.ope/live/` captures, or store credentials.

## Default Selection

The current default is `transitmethod-100`, a historical-frequency baseline. Baseline-only execution remains the default because the checked corpus has one comparable resolved run and six excluded examples. The non-baseline selection threshold is 30 comparable resolved runs.

## Candidate Evidence

The transparent weather-adjustment method, `transitmethod-101`, is recorded as evidence-only:

- Brier score: `0.4489`
- baseline Brier score: `0.5625`
- baseline lift: `0.1136`
- sample size: `1`

This is a fixture comparison, not a quality claim. The method is rejected for selection until enough comparable transit windows resolve and anti-leakage checks continue to pass.

## Proposed Methods

These methods remain proposed-only:

- historical-conditioned statistical buckets over weather, weekday, season, and service window
- trained ML
- retrieval-assisted methods
- ensembles
- external-reference methods

They require clean benchmark evidence before selection. Same-window transit outcome rows are resolution-only evidence and must not become forecast-time evidence for any method.
