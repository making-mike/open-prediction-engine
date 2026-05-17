# Agent Forecast Run

Status: implemented as a local fixture-safe orchestrator.

The agent forecast run gives agents one compact result for the checked `data: auto` weather-logistics path. It validates the request, confirms the dry-run evidence plan, fixture-replays allowed evidence, uses the checked forecast and resolution outputs, and returns a schema-bound summary with the IDs an agent needs next.

It also supports the checked historical-only fixture request. That path uses `dataMode: provided`, `committed_fixture`, no network access, no evidence trace, and a forecast probability equal to the historical-frequency baseline.

The summary schema is `spec/forecast-run-summary.schema.json`. The generated fixture lives at `spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-run.generated.json`.

The intake matrix schema is `spec/forecast-run-intake-matrix.schema.json`. The generated matrix lives at `spec/fixtures/generated/forecast-run/weather-logistics-forecast-run-intake-matrix.generated.json`.

The caller runbook schema is `spec/agent-forecast-runbook.schema.json`. The generated runbook lives at `spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-runbook.generated.json`.

## Commands

Print the default run summary:

```bash
python3 scripts/ope.py forecast-run
```

Print the historical-only no-API run summary:

```bash
python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json
```

Check committed output:

```bash
python3 scripts/ope.py forecast-run --check
python3 scripts/check_agent_forecast_run.py
python3 scripts/ope.py forecast-run-matrix --check
python3 scripts/check_forecast_run_intake_matrix.py
python3 scripts/ope.py forecast-runbook --check
python3 scripts/check_agent_forecast_runbook.py
```

Refresh committed output:

```bash
python3 scripts/ope.py forecast-run --write
python3 scripts/ope.py forecast-run-matrix --write
python3 scripts/ope.py forecast-runbook --write
```

Run through the local MCP stdio scaffold:

```text
tool: ope_forecast_run
arguments: {}
```

Print the intake matrix:

```bash
python3 scripts/ope.py forecast-run-matrix
```

Print the caller runbook:

```bash
python3 scripts/ope.py forecast-runbook
```

## Included Bindings

The completed summary binds:

- request ID
- source policy ID
- evidence plan ID
- evidence source-set ID
- method-selection ID
- pipeline run ID
- question ID
- forecast ID
- forecast card ID
- evidence trace output
- forecast bundle ID
- resolution record ID
- scoring report ID

For the historical-only request, evidence-plan, source-set, method-selection, resolution, scoring, and evidence-trace bindings are `null`; the forecast card and lifecycle bundle remain available.

Agents should use the summary to choose the next read:

- `forecastCard` for compact action context
- `evidenceTrace` for connector-bound source provenance
- `lifecycleBundle` for audit and provenance context
- `resolutionStatus` before treating an outcome as resolved
- `scoringSummary` before making quality-sensitive claims

## Failure Summaries

Rejected, canceled, approval-required, unsupported, and response-too-large runs return a valid forecast-run summary with:

- `runStatus` set to `rejected`, `canceled`, `blocked`, or `failed`
- no forecast, card, evidence trace, bundle, resolution, or scoring IDs
- a sanitized `error.code`
- no raw diagnostics, stack traces, secrets, or hidden prompt/tool arguments

## Intake Matrix

The checked intake matrix covers:

- `accepted`: run completes and binds forecast outputs
- `rejected`: caller should revise the request before retrying
- `blocked`: caller must obtain approval before retrying
- `canceled`: terminal caller cancellation
- `unsupported_fixture_path`: no blind retry until the runtime supports the path
- `response_too_large`: retry with a larger `maxBytes` value or read smaller outputs

The CLI and MCP scaffold are checked against the same classes. Non-completed classes must not bind forecast IDs, forecast cards, evidence traces, lifecycle bundles, resolution records, scoring reports, forecasts, or quality claims.

## Runbook

The checked runbook maps the completed forecast-run path to:

- request validation
- forecast-run execution
- intake outcome inspection
- forecast card read
- evidence trace read
- lifecycle bundle read
- resolution status read
- scoring summary read

It also exposes stable next-action labels for each intake outcome so agents can revise, request approval, stop, retry with a larger size limit, or read the forecast card without inferring behavior from prose.

## Boundary

The orchestrator is not a production live-fetch workflow, hosted service, scheduler, unrestricted web search, or new forecasting method. It only wraps already checked fixture-safe local behavior for the first weather-logistics wedge, including the baseline-only no-API path. Live evidence gathering, private-source access, paid actions, and hosted execution remain out of scope.
