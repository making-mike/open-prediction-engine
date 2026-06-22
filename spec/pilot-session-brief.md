# Pilot Session Brief

`pilot-session-brief.schema.json` defines a read-only moderator brief for one supervised local pilot session.

Read the joined brief:

```bash
python3 scripts/ope.py pilot-session-brief
python3 scripts/ope.py pilot-session-brief --section summary
python3 scripts/ope.py pilot-session-brief --section commands
python3 scripts/ope.py pilot-session-brief --section guidance
python3 scripts/ope.py pilot-session-brief --check
```

## What It Joins

- the checked setup-comprehension task from `pilot-session-packet`
- the domain-agnostic setup questions from `agent-guide --section generic`
- the non-ledger-ready draft status from `pilot-summary-template`
- the explicit local classify, append, findings, and status-review command loop
- the sanitization and claim-boundary rules that keep real-session evidence separate from forecast quality claims

## Boundary

This brief does not run pilot sessions, write checked fixtures, append ignored local evidence, store raw transcripts, store private data, store credentials, store prompt logs, store participant identity, create forecast artifacts, unblock hosted runtime, or upgrade quality, calibration, generated-type, or expansion claims.

The only mutating command it names is the explicit, moderator-approved local append:

```bash
python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local
```

Normal checks:

```bash
python3 scripts/generate_pilot_session_brief.py --check
python3 scripts/check_pilot_session_brief.py
```
