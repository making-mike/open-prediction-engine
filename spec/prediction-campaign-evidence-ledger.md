# Prediction Campaign Evidence Ledger

Status: checked append-only ledger readback.

Last reviewed: 2026-05-31.

The prediction campaign evidence ledger readback defines how campaign runs become local comparable evidence or excluded audit rows without hand-editing corpus JSON.

```bash
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign append
python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary
python3 scripts/ope.py prediction-campaign append-ready --from-local --run-id predictionrun-1301
python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001 --from-local-ledger
python3 scripts/ope.py prediction-campaign append-ready --check
```

`append-ready` is the dry-run inspection surface. In the current checked campaign fixture, `forecast-1301` has forecast-before-close and source-policy checks, but no checked outcome or score, so it is appendable only as an excluded `missing_outcome` audit row. The `comparable_scored` case records the comparable-row shape and append checks expected once a campaign run has checked resolution and scoring records.

When `--from-local` is explicit, the readback derives the candidate row from ignored local campaign state: forecast artifact, evidence packet, forecast history, resolution record, scoring report, source policy, and run-state paths must all bind to the selected run. Comparable scored rows count toward later track-record thresholds only after `prediction-campaign append --from-local --write-local` writes the ignored ledger and `transit-track-record-gate --campaign ... --from-local-ledger` is explicitly selected.

## Boundary

Normal checks do not read or write `.ope/live`, fetch live data, execute resolvers, create resolution or scoring artifacts, append corpus evidence, overwrite prior evidence, or allow track-record or calibration claims. `prediction-campaign append --from-local --write-local` is explicit and writes only to the ignored local campaign ledger with stable campaign/run/forecast/scoring row keys that skip already-present rows.
