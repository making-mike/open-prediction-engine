# Local Usage Trace

Milestone 82 adds a checked local-only usage and trace read model for the MVP. It gives agents and developers product-metric vocabulary for setup, forecast-run, readback, blocked-path, agent-call, MCP, release-surface, and pilot-validation events without adding hosted telemetry.

The generated trace pack covers:

- ten synthetic checked local events across CLI, `agent-call`, MCP stdio mapping, and checker surfaces;
- trace fields for elapsed time, exit code, response size, record binding, and sanitized error class;
- aggregate readbacks for agent forecast completion rate, agent read success rate, blocked-path frequency, and local-only privacy rate;
- an execution boundary that keeps command execution, hosted telemetry, prompt storage, raw transcripts, private rows, credentials, and live fetches disabled.

Run it locally with:

```bash
python3 scripts/ope.py local-usage-trace
python3 scripts/ope.py local-usage-trace --check
python3 scripts/ope.py local-usage-trace --event forecast_run_readback
```

The local usage trace is not analytics collection. The checked event rows are deterministic examples so OPE can discuss and test product metrics before any opt-in runtime logging or hosted service exists.
