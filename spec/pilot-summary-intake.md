# Pilot Summary Intake

`pilot-summary-intake.schema.json` defines the checked classifier for sanitized pilot-session summaries before they can be reviewed for the pilot evidence ledger.

The classifier sits between `pilot-session-packet` and `pilot-evidence`. It shows which summaries are ledger-ready, which need redaction, and which must be blocked because they contain raw transcripts, private rows, credentials, participant identity, or claim overreach. It does not run pilot sessions, read real session files, write ledger rows, store raw/private data, create forecast artifacts, or unblock expansion.

Use:

```bash
python3 scripts/ope.py pilot-summary-intake
python3 scripts/ope.py pilot-summary-intake --case accepted_local_setup_summary
python3 scripts/ope.py pilot-summary-intake --case blocked_raw_transcript
python3 scripts/ope.py pilot-summary-intake --section rules
python3 scripts/ope.py pilot-summary-intake --check
```

Ledger-ready means safe for moderator review. It does not mean the checked fixture contains real pilot evidence, and it does not allow quality, calibration, hosted-runtime, generated-type, or broader private-source claims.
