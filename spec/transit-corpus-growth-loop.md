# Transit Corpus Growth Loop

Milestone 83 adds a checked append-readiness loop for growing the weather-transit-delay forward-run corpus. It is designed for agents deciding whether a resolved transit forward run may be appended as comparable evidence, excluded for audit, or rejected because it breaks evidence boundaries.

The generated growth loop covers:

- one append-ready comparable resolved candidate;
- exclusion-ledger examples for missing outcomes, stale evidence, leakage risk, post-close sources, and incomparable windows;
- due-run and post-resolution checklists that keep forecast-time evidence separate from resolution-only outcome evidence;
- progress readback toward the 30-run baseline track-record threshold and 100-run calibration threshold;
- an execution boundary that keeps normal checks non-mutating, offline, and claim-blocked.

Run it locally with:

```bash
python3 scripts/ope.py transit-corpus-growth
python3 scripts/ope.py transit-corpus-growth --check
python3 scripts/ope.py transit-corpus-growth --case comparable_resolved
```

The growth loop is an append-readiness read model. It declares the append-only contract and required bindings, but normal checks do not mutate the canonical corpus, read ignored live workspaces, fetch live data, create forecasts, create resolutions, create scores, or allow quality and calibration claims below threshold.
