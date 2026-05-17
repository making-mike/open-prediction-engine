# Agent Forecast Runbook

Status: implemented as a checked local runbook.

The agent forecast runbook tells a supervised agent how to request the local fixture-safe forecast run, branch on the forecast-run intake outcome, and choose the next read surface without guessing.

The runbook schema is `spec/agent-forecast-runbook.schema.json`. The generated fixture lives at `spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-runbook.generated.json`.

## Commands

Print the runbook:

```bash
python3 scripts/ope.py forecast-runbook
```

Check committed output:

```bash
python3 scripts/ope.py forecast-runbook --check
python3 scripts/check_agent_forecast_runbook.py
```

Refresh committed output:

```bash
python3 scripts/ope.py forecast-runbook --write
```

## Caller Flow

The checked workflow is:

1. validate the request
2. run `forecast-run`
3. inspect the intake outcome
4. read the forecast card for compact action context
5. read the evidence trace for connector-bound source provenance
6. read the lifecycle bundle for audit context
7. check resolution status
8. read scoring summary before quality-sensitive use

## Next Actions

The runbook aligns with the forecast-run intake matrix:

- `accepted`: `read_forecast_card`
- `rejected`: `revise_request`
- `blocked`: `request_approval`
- `canceled`: `stop_terminal`
- `unsupported_fixture_path`: `use_supported_fixture_or_wait`
- `response_too_large`: `increase_max_bytes_or_read_smaller_output`

Non-completed outcomes must not bind forecast outputs.

## Boundary

The runbook covers local CLI and local MCP stdio behavior only. It is not a hosted API guide, production runtime guide, live internet evidence workflow, or claim that OPE has searched all possible evidence.
