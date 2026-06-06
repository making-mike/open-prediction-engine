# Pilot Findings

Status: checked readback; agent-only simulation is recorded separately and real supervised sessions are still needed.

`pilot-findings` summarizes the current adoption evidence state from the pilot evidence ledger, pilot session packet, pilot summary-intake classifier, and simulated agent pilot readback. It is intentionally honest about the current count: the checked repository has five simulated agent sessions and zero accepted real sessions.

Run it with:

```bash
python3 scripts/ope.py pilot-findings
python3 scripts/ope.py pilot-findings --section summary
python3 scripts/ope.py simulated-agent-pilot --section summary
python3 scripts/check_pilot_findings.py
```

## What It Reports

- accepted real-session count
- accepted simulated-agent-session count
- minimum and target real-session thresholds
- friction classes seen in checked synthetic and simulated examples
- required next actions before evidence can count
- boundaries for raw transcripts, private data, credentials, host-project secrets, quality claims, calibration claims, hosted runtime, and generated types

## Boundary

This readback does not store raw transcripts, private data, credential values, or host-project secrets. It does not upgrade forecast quality, calibration, hosted runtime, live-source production use, generated runtime types, or method-performance claims.

Simulated agent sessions can guide adoption-copy and setup-scope work, but they do not count as real pilot evidence. Real pilot summaries must pass `pilot-summary-intake` before they can be considered ledger-ready evidence.
