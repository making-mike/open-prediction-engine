# Pilot Session Packet

`pilot-session-packet.schema.json` defines the checked collection kit for running real local MVP pilot sessions.

The packet bridges the existing `agent-pilot-validation` task scenarios to the `pilot-evidence` ledger. It provides task cards, moderator and participant checklists, a sanitized evidence template, required sanitization checks, and stop conditions. It does not run sessions, write ledger rows, store raw transcripts, store private data, create forecast artifacts, fetch live data, start hosted runtime, or unblock expansion.

Use:

```bash
python3 scripts/ope.py pilot-session-packet
python3 scripts/ope.py pilot-session-packet --task local_file_setup_readback
python3 scripts/ope.py pilot-session-packet --section sanitization
python3 scripts/ope.py pilot-session-packet --check
```

Real pilot summaries should be recorded only after the sanitization review passes. Accepted summaries may include task references, dimension scores, sanitized findings, friction classes, expansion signals, and a next action. Raw transcripts, recordings, prompt logs, credentials, private source rows, participant identity, and quality or hosted-runtime claims must be blocked before ledger submission.
