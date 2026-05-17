# Auto-Evidence Planning

Status: implemented as a local dry-run, fixture-replay, forecast, resolution, and scoring contract surface.

Auto-evidence is the first step toward agent-native forecasting with `data: auto`. It lets an agent or developer ask OPE to plan evidence gathering for a forecast request and, in fixture-replay mode, normalize allow-listed source evidence, generate a forecast, and later resolve and score it without any live source fetch.

## Current Boundary

The current implementation is a dry run:

- validates a forecast request with `dataMode: auto`
- validates a declared `sourcePolicy`
- emits an `evidence-gathering-plan` record
- emits an `evidence-source-set` record in fixture-replay mode
- emits a source connector registry and connector result set for allowed, resolution-only, and unsupported connectors
- emits a live connector readiness record for opt-in Open-Meteo integration checks outside normal release checks
- binds evidence plans to the checked source connector registry and expected connector result set
- emits request-bound forecast records in fixture-replay mode
- resolves and scores the generated auto-evidence forecast from declared fixture outcome sources
- names allowed connectors, search intents, inclusion rules, exclusion rules, unavailable evidence, and warnings
- normalizes Open-Meteo weather fixture evidence through the same allow-listed connector logic used by the live-source prototype
- generates a forecast artifact, evidence packet, question, history, and pipeline-run summary from the gathered fixture source set
- performs no network access
- performs no live fetch
- performs no effectful forecast generation
- makes no live calibration or state-of-the-art performance claim

## Commands

Return the dry-run plan as JSON:

```bash
python3 scripts/plan_auto_evidence.py
python3 scripts/ope.py evidence-plan
```

Return the fixture-replay source set as JSON:

```bash
python3 scripts/gather_auto_evidence.py
python3 scripts/gather_auto_evidence.py --execution-mode fixture_replay
python3 scripts/ope.py gather-evidence
```

Inspect source connector policy and fixture-safe connector results:

```bash
python3 scripts/generate_source_connectors.py
python3 scripts/generate_source_connectors.py --results
python3 scripts/ope.py source-connectors
python3 scripts/ope.py source-connectors --results
```

Inspect the live connector readiness gate without network access:

```bash
python3 scripts/generate_live_connector_readiness.py --check
python3 scripts/ope.py live-readiness --check
```

Run the optional Open-Meteo integration probe:

```bash
python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
```

Check the request-bound auto-evidence forecast outputs:

```bash
python3 scripts/run_auto_evidence_forecast.py
python3 scripts/ope.py auto-forecast
```

Check the resolved auto-evidence outcome outputs:

```bash
python3 scripts/resolve_auto_evidence_outcome.py
python3 scripts/ope.py resolve-auto-evidence
```

Check the committed generated plan:

```bash
python3 scripts/plan_auto_evidence.py --check
python3 scripts/ope.py evidence-plan --check
python3 scripts/gather_auto_evidence.py --check
python3 scripts/ope.py gather-evidence --check
python3 scripts/generate_source_connectors.py --check
python3 scripts/ope.py source-connectors --check
python3 scripts/generate_live_connector_readiness.py --check
python3 scripts/ope.py live-readiness --check
python3 scripts/run_auto_evidence_forecast.py
python3 scripts/ope.py auto-forecast
python3 scripts/resolve_auto_evidence_outcome.py
python3 scripts/ope.py resolve-auto-evidence
```

Refresh the generated plan:

```bash
python3 scripts/plan_auto_evidence.py --write
python3 scripts/ope.py evidence-plan --write
python3 scripts/gather_auto_evidence.py --write
python3 scripts/ope.py gather-evidence --write
python3 scripts/generate_source_connectors.py --write
python3 scripts/ope.py source-connectors --write
python3 scripts/generate_live_connector_readiness.py --write
python3 scripts/ope.py live-readiness --write
python3 scripts/run_auto_evidence_forecast.py --write
python3 scripts/ope.py auto-forecast --write
python3 scripts/resolve_auto_evidence_outcome.py --write
python3 scripts/ope.py resolve-auto-evidence --write
```

## Contracts

The request contract now includes:

- `dataMode`: `provided`, `auto`, or `hybrid`
- `sourcePolicy`: allowed source classes, allowed connectors, network/cost caps, freshness requirements, approval requirement, and retention posture

The generated evidence plan is validated by:

```text
spec/evidence-gathering-plan.schema.json
```

The evidence plan also binds:

- `sourceConnectorRegistryId`
- `expectedSourceConnectorResultSetId`
- `connectorPolicyChecks`

Those checks separate registered, unregistered, unsupported, resolution-only, and forecast-time connectors before any evidence gathering begins.

The generated source set is validated by:

```text
spec/evidence-source-set.schema.json
```

The source set also binds to the same connector registry and result set:

- `sourceConnectorRegistryId`
- `sourceConnectorResultSetId`
- record-level `connectorBinding`

The fixture gatherer rejects plans with unregistered, unsupported, or resolution-only connectors instead of partially gathering supported sources from a non-executable policy.

The source policy object is validated by:

```text
spec/source-policy.schema.json
```

The connector registry and result set are validated by:

```text
spec/source-connector-registry.schema.json
spec/source-connector-result-set.schema.json
```

The live connector readiness record is validated by:

```text
spec/live-connector-readiness.schema.json
```

Ignored local live captures are validated against:

```text
spec/source-connector-result-set.schema.json
spec/evidence-source-set.schema.json
```

Those captures live under `.ope/live/`, outside generated fixtures and public read records.

## First Supported Auto-Evidence Policy

The first checked auto-evidence fixture is limited to:

- domain: `weather-logistics`
- geography: `Warsaw`
- horizon: `1-day`
- output type: `binary`
- connector: `open_meteo_weather`
- connector: `committed_fixture` for the historical baseline fixture
- connector: `declared_operations_fixture` only after the service window for resolution and scoring
- unsupported connector: `web_search`
- unsupported source class: `market_price`
- source classes: `official`, `public_dataset`, `internal_dataset`
- source class: `internal_dataset` for committed baseline fixtures
- cost: free only
- integration live execution mode: opt-in readiness probe only
- ignored local live capture mode: opt-in, developer-only, not forecast evidence
- hosted live execution mode: not yet implemented
- fixture replay: implemented

Broad web search is not enabled in the first policy. OPE should not claim it used all available internet evidence.

## Guardrails

Normal checks verify that:

- `dataMode: auto` request validation is accepted only for the current allow-listed policy
- unsupported auto connectors are rejected
- stale source-policy freshness constraints fail schema validation
- provided-data mode cannot quietly enable network access
- dry-run controls keep `networkAccess`, `liveFetch`, and `effectfulGeneration` false
- fixture-replay source gathering keeps `networkAccess`, `liveFetch`, and `effectfulGeneration` false
- source connector records reject prompt-visible credentials, raw stack traces, all-evidence claims, and normal-check network access
- live connector readiness records keep integration live checks explicit, allow-listed, timeout-bounded, sanitized, and outside normal release checks
- unsupported source connectors expose unavailable evidence instead of normalized fields
- evidence plans reject or explain unregistered, unsupported, and resolution-only connectors before gathering
- forecast-time search intents exclude resolution-only connectors
- `live_fetch` source gathering is an explicit execution mode but fails closed until a production auto-evidence connector exists
- gathered source records preserve connector, source role, source ref, retrieval timestamp, content hash, source quality, raw fixture metadata, and normalized fields
- prompt-injected source fields and source metadata are rejected before they can become forecast evidence
- stale, unavailable, and conflicting fixture sources fail the source-gathering check
- forecast-time source sets exclude future resolution sources
- forecast outputs preserve request, evidence-plan, evidence-source-set, evidence-trace, and source-policy bindings through the pipeline-run summary
- outcome resolution preserves request, source-policy, evidence-plan, evidence-source-set, forecast, score, and track-record bindings
- the plan names unavailable evidence and avoids all-evidence coverage claims

## Claim Boundary

The current auto-evidence path proves one fixture-replay loop for one weather-logistics request. It may claim that OPE preserved source policy, provenance, forecast, resolution, score, and track-record bindings for that fixture. The live readiness gate may claim only an explicit allow-listed integration probe. OPE must not claim production live auto-evidence gathering, all-internet evidence coverage, live calibration, or state-of-the-art forecasting performance.
