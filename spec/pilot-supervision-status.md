# Pilot Supervision Status

`pilot-supervision-status.schema.json` defines a read-only operator status for the supervised local pilot loop.

Use it when an agent or moderator needs to know which checked pilot task to run next, how many accepted real sessions remain before the minimum or target threshold, and which commands move a sanitized session summary from classification to explicit ignored-local evidence append.

```bash
python3 scripts/ope.py pilot-supervision-status
python3 scripts/ope.py pilot-supervision-status --section summary
python3 scripts/ope.py pilot-supervision-status --section commands
python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary
python3 scripts/ope.py pilot-supervision-status --check
```

The default readback does not inspect `.ope/live` and keeps accepted real sessions at zero in checked fixtures. Use `--from-local-ledger` only when intentionally reading ignored local pilot evidence.

The recommended task is currently `engine_setup_shortcut_comprehension`, because OPE needs real supervised evidence that agents understand `setup-engine` as the first prediction-engine setup surface before inventing a parallel lightweight risk engine.

The readback itself does not run pilot sessions, write checked fixtures, append local evidence, store raw transcripts, store private data, store credentials, create forecast artifacts, unblock hosted runtime, unblock generated types, or upgrade forecast quality or calibration claims. The only mutating command in the displayed sequence remains the existing explicit `pilot-evidence --input-summary <summary.json> --write-local` path.
