# Controlled Forecast Request Access

Status: implemented as validation-only intake.

OPE currently supports controlled request intake through `scripts/validate_forecast_request.py`. The script validates whether a request may proceed, but it does not generate forecasts, call models, fetch live sources, or spend money.

## Supported Request

The first supported request shape is limited to:

- domain: `weather-logistics`
- geography: `Warsaw`
- output type: `binary`
- horizon: `1-day`
- requested action: `validate_only` or policy-gated `generate_forecast`

## Decisions

The intake decision can be:

- `accepted`: request is resolvable and policy permits it
- `blocked`: request may be valid but needs approval
- `canceled`: caller requested cancellation before execution
- `rejected`: request is unresolvable, unsafe, expired, or violates policy

Decision output includes an audit-safe log with request ID, decision status, reason codes, and a question hash. It does not echo raw prompt-like request text in logs.

## Approval Gates

Approval is required for requests marked:

- high impact
- paid
- external
- privacy sensitive

Paid requests must also include a positive cost cap within the schema maximum. Non-paid requests must use `maxCostUsd: 0`.

## Non-Goals

This interface is not an execution engine. Forecast generation remains a future step after policy gates, runtime selection, and release checks exist.
