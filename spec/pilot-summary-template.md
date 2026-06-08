# Pilot Summary Template

`pilot-summary-template.schema.json` defines a read-only template for creating sanitized supervised pilot summaries.

Use it when an operator needs a schema-shaped draft before running `pilot-summary-intake --input <summary.json>`.

```bash
python3 scripts/ope.py pilot-summary-template
python3 scripts/ope.py pilot-summary-template --section summary
python3 scripts/ope.py pilot-summary-template --section draft
python3 scripts/ope.py pilot-summary-template --section commands
python3 scripts/ope.py pilot-summary-template --task engine_setup_shortcut_comprehension
python3 scripts/ope.py pilot-summary-template --check
```

The included draft is intentionally not ledger-ready unchanged. It has no dimension ratings and keeps `unredactedSourceDetailDetected` true, so `pilot-summary-intake --input <draft.json>` classifies it as `needs_redaction` until an operator fills real sanitized ratings, findings, friction classes, expansion signals, next action, and clears risk signals after review.

The template does not run pilot sessions, write checked fixtures, append local evidence, store raw transcripts, store private data, store credentials, create forecast artifacts, unblock expansion, or upgrade quality/calibration/runtime claims. The only mutating command in its command sequence remains the explicit `pilot-evidence --input-summary <summary.json> --write-local` path after intake accepts a filled summary.
