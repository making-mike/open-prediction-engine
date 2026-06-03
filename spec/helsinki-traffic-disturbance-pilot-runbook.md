# Helsinki Traffic Disturbance Pilot Runbook

Status: checked local operations runbook.

This runbook describes how to run the local Helsinki traffic disturbance pilot for 100 forecastable morning-peak service windows. It is an operations procedure, not a quality claim. Normal checks do not start the pilot, fetch live data, write `.ope/live` campaign state, execute resolvers, append ledger rows, update calibration, or change methods.

Best available method for the pilot is `transitmethod-100`, the transparent baseline historical transit-delay frequency. `transitmethod-101` may be used only prospectively after the campaign ledger, calibration status, benchmark evidence, anti-leakage checks, source-policy review, approvals, method-update plan, and rollback record are ready.

## Scope

- Domain: `weather-transit-delays`
- Network/geography: HSL surface transit in Helsinki
- Service window: `morning_peak`
- Target: 100 comparable resolved outcomes
- Mini smoke target: 3 planned runs
- Full plan command: `python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization`
- Optional pre-calibration command: `python3 scripts/ope.py prediction-campaign pre-calibration`
- Checked readback: `python3 scripts/ope.py prediction-campaign pilot-runbook`

## Mini Smoke Before The Real Pilot

Run the three-run smoke before any 100-run local writes:

```bash
python3 scripts/ope.py prediction-campaign plan --plan-count 3 --count 3
python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --limit 3
python3 scripts/ope.py prediction-campaign append-ready --view candidate
```

Pass condition: the commands return valid JSON or JSONL, expose `predictionrun-1301` through `predictionrun-1303`, preserve forecast-before-close boundaries, and do not write campaign state unless `--write-local` is explicit.

## 100-Run Command Sequence

1. Review scope and gates.

```bash
python3 scripts/ope.py prediction-campaign pilot-runbook --view scope
python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke
```

2. Review full materialization.

```bash
python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization
```

3. Review optional historical pre-calibration before the first local write.

```bash
python3 scripts/ope.py prediction-campaign pre-calibration
```

4. Create the next due forecast only during the forecast window. Include `--pre-calibrate` when the historical-only pre-calibration readback is ready and you want the pilot to use it.

```bash
python3 scripts/ope.py prediction-campaign start --count 100 --full-materialization --pre-calibrate --write-local --output-format jsonl
```

5. Check operator status daily or before each action.

```bash
python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status
python3 scripts/ope.py prediction-campaign doctor
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
```

6. Resolve a due run only after the horizon ends and only with eligible outcome evidence.

```bash
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local
```

7. Append the scored local row.

```bash
python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local
```

8. Review calibration progress.

```bash
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot
```

9. After 100 comparable outcomes, review method update readiness. Do not change methods unless the explicit plan-ready apply command is approved.

```bash
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-plan
```

## Operator Status

Use `python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status` for one readback that points to:

- next forecast
- next resolution
- due resolver jobs
- append readiness
- ledger counts
- exclusion rate
- calibration threshold progress

## Success Criteria

- At least 100 comparable resolved and scored outcomes.
- Exclusion rate is at or below `0.25`.
- No forecast-after-close or backfilled forecast is counted as comparable.
- No duplicate campaign date/window forecast is created.
- Every comparable row has complete forecast, evidence, history, resolution, scoring, and source-policy provenance.
- The method remains `transitmethod-100` unless an explicit method-update apply is approved and written prospectively.

## Abort Criteria

Abort or pause the current cycle when any of these happen:

- Required weather or transit outcome sources are unavailable for repeated due windows.
- Evidence policy would allow post-close evidence, private rows, credentials, or unapproved inputs.
- Clock drift repeatedly misses forecast windows or risks forecast-after-close creation.
- A local write target escapes the ignored `.ope/live/prediction-campaigns` workspace.
- Duplicate keys, duplicate row keys, or overwrite attempts appear.
- Repeated missed windows prevent a meaningful 100-comparable-outcome pilot.

Restart only after a clean three-run smoke and an explicit resume/readback sequence.
