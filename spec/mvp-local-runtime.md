# MVP Local Runtime

Milestone 80 defines the local MVP release surface as a fixture-ready, agent-readable runtime. The MVP is a local CLI and generated-record surface, not a hosted service, network API, production connector runtime, or calibration claim.

## Happy Path

1. Check setup and release readiness:

```bash
python3 --version
python3 scripts/run_checks.py
python3 scripts/ope.py check
python3 scripts/ope.py developer-adoption --section quickstart
python3 scripts/ope.py pilot-evidence --section summary
python3 scripts/ope.py pilot-session-packet --section sanitization
python3 scripts/ope.py pilot-summary-intake --section rules
python3 scripts/ope.py expansion-readiness --section options
python3 scripts/ope.py repeating-prediction-setup --section summary
python3 scripts/ope.py prediction-campaign plan
```

2. Run the private setup summary for the checked local-file path:

```bash
python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed
python3 scripts/ope.py local-source-runtime
```

3. Run the fixture-safe forecast path or read the already generated source-handoff forecast:

```bash
python3 scripts/ope.py forecast-run
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102
```

4. Resolve, score, and inspect the checked source-handoff outcome:

```bash
python3 scripts/ope.py resolve-source-handoff
python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102
```

5. Read corpus and claim gates:

```bash
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py resolution-jobs
python3 scripts/ope.py resolution-runtime-reliability
```

## Machine Interfaces

- CLI: `python3 scripts/ope.py` is the minimum local interface for checks, setup summaries, forecast runs, reads, resolution, scoring, corpus gates, and release manifests.
- Agent envelope: `python3 scripts/ope.py agent-call` returns one schema-bound envelope with status, exit code, record binding, and payload.
- MCP stdio: `python3 scripts/ope.py mcp-stdio` exposes the local dispatcher as MCP tools for MCP-capable hosts.

## Blocked Paths

The MVP intentionally exposes blocked summaries rather than repairing or executing unsafe setup paths:

- `missing_approval` asks for caller approval and creates no forecast artifacts.
- `unconfirmed_mapping` asks for mapping confirmation before method selection.
- `insufficient_data` asks for more comparable rows and positive outcomes.
- `rejected_source` asks for a replacement source.
- `unsafe_source` stops unsafe connector output before source intake.
- `response_too_large` asks the caller to retry with a smaller readback or approved byte budget.
- `local-source-runtime --case credentials_detected` blocks credential-like fields before source intake.
- `local-source-runtime --case unsafe_path` blocks paths outside the approved local source folder.

## Claim Boundary

The local MVP can produce and read checked forecast, resolution, scoring, and corpus artifacts. It cannot claim calibration, broad forecast quality, production live-source use, hosted scheduler execution, arbitrary private API/database parsing beyond the approved local-folder runtime, or a production agent adapter runtime. Normal release checks must remain offline and deterministic.
