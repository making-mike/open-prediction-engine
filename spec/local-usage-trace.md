# Local Usage Trace

Milestone 82 adds a checked local-only usage and trace read model for the MVP. It gives agents and developers product-metric vocabulary for setup, forecast-run, readback, blocked-path, agent-call, MCP, release-surface, pilot-validation, campaign, agent-integration, and setup-comprehension events without adding hosted telemetry.

The generated trace pack covers:

- twenty-seven synthetic checked local events across CLI, `agent-call`, MCP stdio mapping, checker, campaign, Helsinki starter integration, and non-Helsinki setup-comprehension surfaces;
- trace fields for elapsed time, exit code, response size, record binding, and sanitized error class;
- aggregate readbacks for agent forecast completion rate, agent read success rate, blocked-path frequency, setup-engine-first rate, local-only privacy rate, and agent-integration first-forecast-fast success;
- an execution boundary that keeps command execution, hosted telemetry, prompt storage, raw transcripts, private rows, credentials, and live fetches disabled.

Run it locally with:

```bash
python3 scripts/ope.py local-usage-trace
python3 scripts/ope.py local-usage-trace --check
python3 scripts/ope.py local-usage-trace --event forecast_run_readback
python3 scripts/ope.py local-usage-trace --event agent_integration_guided_forecast
python3 scripts/ope.py local-usage-trace --event setup_engine_stockout_comprehension
```

The local usage trace is not analytics collection. The checked event rows are deterministic examples so OPE can discuss and test product metrics before any opt-in runtime logging or hosted service exists.
