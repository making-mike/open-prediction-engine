# Pilot Evidence Ledger

`pilot-evidence-ledger.schema.json` defines the checked intake boundary for sanitized pilot-session evidence.

The ledger is meant to prepare OPE for real agent/developer pilot sessions without storing raw transcripts, private data, credentials, prompt logs, participant identity, or unredacted notes. The checked fixture contains synthetic intake examples only, so it does not count as real pilot evidence and does not unblock hosted runtime, broader private-source runtime, generated runtime types, stronger methods, or quality claims.

Use:

```bash
python3 scripts/ope.py pilot-evidence
python3 scripts/ope.py pilot-evidence --case accepted_sanitized_summary
python3 scripts/ope.py pilot-evidence --section summary
python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local
python3 scripts/ope.py pilot-evidence --from-local-ledger --section summary
python3 scripts/ope.py pilot-evidence --check
```

Accepted future real pilot summaries should contain only dimension scores, task references, sanitized findings, friction classes, expansion signals, and next actions. Raw transcripts and private or credential-bearing notes must be blocked before aggregation.

`--input-summary` produces a dry-run append plan by default. It can expose the candidate row that would be written, but it writes zero rows and records zero real sessions unless `--write-local` is also provided.

`--write-local` appends accepted sanitized summaries to `.ope/live/pilot-evidence/pilot-evidence-ledger.json`, which is ignored by git. The write is idempotent by source summary ID. This local evidence can inform adoption findings only; it does not upgrade forecast quality, calibration, hosted runtime, generated types, or expansion claims.
