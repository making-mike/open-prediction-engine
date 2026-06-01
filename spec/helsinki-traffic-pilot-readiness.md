# Helsinki Traffic Pilot Readiness

Status: checked local launch-readiness readback.

`prediction-campaign pilot-readiness` tells an operator whether the checked local surfaces are ready to start the 100-run Helsinki traffic disturbance pilot. It does not start the pilot, fetch live sources, write `.ope/live`, execute resolvers, append ledger rows, change methods, or make quality claims.

## Command

```bash
python3 scripts/ope.py prediction-campaign pilot-readiness
python3 scripts/ope.py prediction-campaign pilot-readiness --view checks
python3 scripts/ope.py prediction-campaign pilot-readiness --view manual
python3 scripts/ope.py prediction-campaign pilot-readiness --view commands
```

## Readiness Meaning

`checked_ready_for_operator_launch` means the committed checks can see:

- the 100-run pilot runbook is present
- the 3-run mini smoke path is present
- full 100-run materialization has no duplicate date/window keys
- the baseline method remains the launch method
- missed windows are not backfilled

Manual launch prerequisites still remain outside normal checks:

- supervised terminal session
- synchronized local clock
- opt-in source availability and source-policy fit
- approved outcome file path for due resolution
- enough local workspace capacity under `.ope/live`

## Launch Sequence

Use readiness as the gate, then run the smoke path before the first effectful write:

```bash
python3 scripts/ope.py prediction-campaign pilot-readiness
python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization
python3 scripts/ope.py prediction-campaign start --count 100 --full-materialization --write-local --output-format jsonl
python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status
```

The first effectful launch command creates only one next-due local campaign forecast. Resolution, append, calibration, and method update remain separate explicit steps.

## Blocked Actions

- Do not start the pilot from normal checks.
- Do not backfill forecasts after `forecastCloseAt`.
- Do not switch methods without the method-update gate, plan, approvals, benchmark evidence, and rollback record.
- Do not append comparable ledger evidence before resolution and scoring records exist.
