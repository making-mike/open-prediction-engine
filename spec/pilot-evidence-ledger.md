# Pilot Evidence Ledger

`pilot-evidence-ledger.schema.json` defines the checked intake boundary for sanitized pilot-session evidence.

The ledger is meant to prepare OPE for real agent/developer pilot sessions without storing raw transcripts, private data, credentials, prompt logs, participant identity, or unredacted notes. The checked fixture contains synthetic intake examples only, so it does not count as real pilot evidence and does not unblock hosted runtime, broader private-source runtime, generated runtime types, stronger methods, or quality claims.

Use:

```bash
python3 scripts/ope.py pilot-evidence
python3 scripts/ope.py pilot-evidence --case accepted_sanitized_summary
python3 scripts/ope.py pilot-evidence --section summary
python3 scripts/ope.py pilot-evidence --check
```

Accepted future real pilot summaries should contain only dimension scores, task references, sanitized findings, friction classes, expansion signals, and next actions. Raw transcripts and private or credential-bearing notes must be blocked before aggregation.
