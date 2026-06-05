# Forecast Question Discovery

Status: checked candidate and validation readback boundary.

Question discovery turns a host app goal plus approved source context into candidate forecast contracts. It does not choose methods by itself, create forecast artifacts, resolve outcomes, score forecasts, fetch live sources, or store credentials.

The intake contract carries:

- app goal;
- decision to support;
- approved source references;
- source roles;
- forecast-time evidence policy;
- resolution evidence policy;
- candidate outcome windows;
- resolution-source hints;
- safety impact;
- optional setup, domain, and method hints.

Candidate readbacks can be:

- `forecastable`: route to existing source-intake, benchmark, method, forecast, read, resolution, scoring, and calibration surfaces;
- `needs_clarification`: stop until an agent or user clarifies ambiguous timing, resolution, or source scope;
- `blocked`: stop because source policy, safety, leakage, privacy, or runtime readiness blocks execution;
- `rejected`: stop because the question is post-outcome, unresolvable, unsupported, or otherwise invalid.

Mechanical validation covers schema validity, future boundary, resolvability, source-policy binding, leakage risk, outcome availability, mapping confidence, baseline feasibility, method eligibility, scoring readiness, and calibration-readiness boundary.

## MCP Host Wrapper Template

A local MCP-capable host should expose question discovery as a compact readback over the same internal API and CLI semantics:

```text
tool: ope_question_discovery
input: question-discovery intake JSON
output: agent-implementation-kit candidates and validation views
side effects: none
```

HTTP and queue transports remain future wrappers. The local MCP wrapper must not create a hosted service, store credential values, or turn discovery into forecast execution.
