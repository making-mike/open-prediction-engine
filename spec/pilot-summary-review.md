# Pilot Summary Review

`pilot-summary-review.schema.json` defines a read-only post-session review bundle for one sanitized pilot summary file.

Review a summary:

```bash
python3 scripts/ope.py pilot-summary-review --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-summary-review --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json --section summary
python3 scripts/ope.py pilot-summary-review --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json --section commands
python3 scripts/ope.py pilot-summary-review --check
```

## What It Joins

- the read-only `pilot-summary-intake --input <summary.json>` classification
- the read-only `pilot-evidence --input-summary <summary.json>` append plan
- the decision whether explicit moderator-approved `--write-local` is allowed
- the next commands for append, findings review, and supervision-status review
- the claim boundary that keeps pilot usability evidence separate from forecast quality and calibration evidence

## Boundary

This review does not run sessions, write checked fixtures, append ignored local evidence, count real sessions, store raw transcripts, store private data, store credentials, store prompt logs, store participant identity, create forecast artifacts, unblock hosted runtime, or upgrade quality, calibration, generated-type, or expansion claims.

Only the command it reports for accepted summaries is mutating, and it still requires explicit operator approval:

```bash
python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local
```

Normal checks:

```bash
python3 scripts/generate_pilot_summary_review.py --check
python3 scripts/check_pilot_summary_review.py
```
