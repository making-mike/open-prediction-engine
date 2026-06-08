# Pilot Summary Intake

`pilot-summary-intake.schema.json` defines the checked classifier for sanitized pilot-session summaries before they can be reviewed for the pilot evidence ledger. `pilot-summary-submission.schema.json` defines the caller-supplied sanitized summary input shape, and `pilot-summary-intake-result.schema.json` defines the read-only classification result.

The classifier sits between `pilot-session-packet` and `pilot-evidence`. It shows which summaries are ledger-ready, which need redaction, and which must be blocked because they contain raw transcripts, private rows, credentials, participant identity, or claim overreach. It can also classify one caller-supplied sanitized summary JSON file so a moderator can decide whether the summary is ready for ledger review. It does not run pilot sessions, write ledger rows, count real sessions, store raw/private data, create forecast artifacts, or unblock expansion.

Use:

```bash
python3 scripts/ope.py pilot-summary-intake
python3 scripts/ope.py pilot-summary-intake --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-summary-intake --case accepted_local_setup_summary
python3 scripts/ope.py pilot-summary-intake --case blocked_raw_transcript
python3 scripts/ope.py pilot-summary-intake --section rules
python3 scripts/ope.py pilot-summary-intake --check
```

Ledger-ready means safe for moderator review. It does not mean the checked fixture contains real pilot evidence, and it does not allow quality, calibration, hosted-runtime, generated-type, or broader private-source claims.

After moderator approval, `pilot-evidence --input-summary <summary.json>` prints a dry-run append plan. Add `--write-local` only when the approved summary should be appended to the ignored local ledger under `.ope/live/`.
