# Controlled Forecast Request Access

Status: implemented as validation-only intake with source-policy checks.

OPE currently supports controlled request intake through `scripts/validate_forecast_request.py`. The script validates the request contract before semantic policy checks, including `dataMode` and `sourcePolicy`, but it does not generate forecasts, call models, fetch live sources, or spend money.

## Supported Request

The first supported request shape is limited to:

- domain: `weather-logistics`
- geography: `Warsaw`
- output type: `binary`
- horizon: `1-day`
- requested action: `validate_only` or policy-gated `generate_forecast`
- data mode: `provided` or first-step `auto`
- source policy: committed fixtures for provided mode, or allow-listed Open-Meteo weather evidence for auto mode

## Decisions

The intake decision can be:

- `accepted`: request is resolvable and policy permits it
- `blocked`: request may be valid but needs approval
- `canceled`: caller requested cancellation before execution
- `rejected`: request is contract-invalid, unresolvable, unsafe, expired, or violates policy

Decision output includes an audit-safe log with request ID, decision status, reason codes, and a question hash. It does not echo raw prompt-like request text in logs.

For `dataMode: auto`, accepted requests are still only eligible for evidence planning. Live source fetching and effectful forecast generation remain separate future steps.

For `dataMode: provided` with only `committed_fixture`, OPE now has a checked historical-only forecast path. It produces a baseline forecast without network access or forecast-time API evidence.

## Approval Gates

Approval is required for requests marked:

- high impact
- paid
- external
- privacy sensitive
- source-policy approval required

Paid requests must also include a positive cost cap within the schema maximum. Non-paid requests must use `maxCostUsd: 0`.

## Auto-Evidence Boundary

The first auto-evidence request is limited to:

- `dataMode: auto`
- free public evidence only
- `open_meteo_weather` as the only enabled auto connector
- no broad web search
- no live fetch during dry-run planning
- no effectful forecast generation

See `spec/auto-evidence.md` for the dry-run planning surface.

## Historical-Only Boundary

The first historical-only request is limited to:

- `dataMode: provided`
- `committed_fixture` as the only connector
- `allowNetworkAccess: false`
- `maxNetworkCalls: 0`
- no evidence trace, because no connector-bound auto-evidence run occurs
- forecast probability equal to the historical-frequency baseline

Run it with:

```bash
python3 scripts/ope.py historical-forecast
python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json
```

## Non-Goals

This interface is not a live execution engine. Forecast generation and live auto-evidence fetching remain future steps after policy gates, source-policy checks, runtime selection, and release checks exist.
