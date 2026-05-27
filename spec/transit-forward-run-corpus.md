# Transit Forward-Run Corpus

Status: checked fixture index.

Last reviewed: 2026-05-27.

The transit forward-run corpus is the local read surface for weather-transit-delay forward-run evidence. It records comparable scored runs, excluded runs, corpus counts, minimum sample thresholds, and claim boundaries before OPE starts reporting public transport calibration.

Default checked fixture:

```bash
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-forward-run-corpus --check
```

The corpus index is read-only. It does not execute forward runs, resolve outcomes, create forecast artifacts, create scoring reports, fetch live data, store credentials, or commit ignored `.ope/live/` captures.

## Comparable Policy

A comparable HSL morning-peak run must preserve:

- a forecast recorded at or before `closeAt`
- a resolution recorded after the forecast horizon ends
- a forecast artifact, resolution record, and Brier scoring report
- a baseline score so lift can be inspected without making a quality claim
- enough observations to meet the declared minimum coverage rule

The checked policy starts with the weather-transit-delay domain thresholds: at least 10 outcome observations for one run, at least 30 comparable resolved windows before baseline track-record claims, and at least 100 comparable resolved windows before calibration summaries.

## Exclusions

The fixture index includes one example row for each exclusion reason:

- `ambiguous`
- `annulled`
- `low_coverage`
- `invalid_window`
- `feed_unavailable`
- `non_comparable`

Excluded runs can remain useful audit evidence, but they do not count toward comparable resolved windows or calibration claims.

## Claim Boundary

The current corpus has one comparable scored run. It is implementation evidence only. Quality, calibration, baseline track-record, production, and live connector claims remain blocked until enough comparable forward windows are forecast, resolved, and scored under the declared policy.
