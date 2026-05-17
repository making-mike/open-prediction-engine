# Source Connectors

Status: implemented as checked fixture-safe connector contracts.

Source connectors describe what OPE may use for `data: auto` evidence before a broader live retrieval runtime exists. The connector registry is agent-readable and separates allowed fixture-replay connectors from resolution-only and unsupported source classes.

Live connector readiness is tracked separately in `spec/live-connector-readiness.schema.json` so normal connector results remain fixture-safe while developers can intentionally run one allow-listed integration probe. Sanitized opt-in live captures can be saved under the ignored `.ope/live/` workspace and validated against the same connector result-set boundary.

The registry schema is `spec/source-connector-registry.schema.json`. The generated registry lives at `spec/fixtures/generated/source-connectors/weather-logistics-source-connector-registry.generated.json`.

The result-set schema is `spec/source-connector-result-set.schema.json`. The generated result set lives at `spec/fixtures/generated/source-connectors/weather-logistics-source-connector-results.generated.json`.

## Commands

Print the connector registry:

```bash
python3 scripts/ope.py source-connectors
```

Print fixture-safe connector results:

```bash
python3 scripts/ope.py source-connectors --results
```

Check committed connector outputs:

```bash
python3 scripts/ope.py source-connectors --check
python3 scripts/check_source_connectors.py
python3 scripts/ope.py live-readiness --check
python3 scripts/check_live_connector_readiness.py
```

Refresh committed connector outputs:

```bash
python3 scripts/ope.py source-connectors --write
```

## Current Connectors

The first registry includes:

- `open_meteo_weather`: enabled for fixture-replay forecast-time public weather evidence
- `committed_fixture`: enabled for fixture-replay baseline evidence
- `declared_operations_fixture`: resolution-only and excluded from forecast-time evidence
- `web_search`: unsupported in the first auto-evidence milestone
- `market_price_feed`: unsupported source class for the weather-logistics wedge

The Open-Meteo connector has three explicit execution-mode boundaries:

- `fixture_replay`: implemented and included in normal checks
- `integration_live_fetch`: implemented only behind `python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD`
- local live capture: implemented only behind `python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD`, written under `.ope/live/`, and excluded from public read surfaces
- `hosted_live_fetch`: not implemented

## Guardrails

Connector records must:

- declare source class, allowed purpose, freshness, rate limit, credential, provenance, diagnostic, and risk boundaries
- keep normal checks fixture-safe with no live network dependency
- keep integration live fetches explicit, allow-listed, bounded to one Open-Meteo call, and outside normal release checks
- reject prompt-visible credentials
- keep raw stack traces out of public connector diagnostics
- avoid claiming all possible evidence was gathered
- keep resolution-only outcome evidence out of forecast-time source sets

Evidence plans must bind to the checked connector registry and expected result set before gathering:

- `sourceConnectorRegistryId`
- `expectedSourceConnectorResultSetId`
- `connectorPolicyChecks`

The plan must explain unregistered connectors, unsupported connectors, and resolution-only connectors without converting them into forecast-time search intents.

Evidence source sets must preserve the same connector boundary:

- source sets bind to `sourceConnectorRegistryId` and `sourceConnectorResultSetId`
- each gathered record includes a `connectorBinding`
- record connectors must be a subset of `forecastTimeConnectors`
- gatherers must reject non-executable connector policies instead of partially gathering valid connectors from a mixed invalid request

## Boundary

This contract does not implement production live evidence gathering, unrestricted source discovery, hosted retrieval, private-source access, paid source access, production forecast use of live connector results, or live calibration quality. It only makes the first connector capability, readiness, and result boundaries explicit for agents.
