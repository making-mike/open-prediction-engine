# Optional OPP Provider Adapter

Status: checked local interoperability fixture.

This document defines the current Open Prediction Protocol (OPP) provider-adapter boundary for OPE. The adapter is optional interoperability over OPE records. It is not a replacement for OPE forecast artifacts, forecast cards, evidence traces, lifecycle bundles, operation receipts, scoring records, calibration gates, or claim-boundary checks.

The checked readback is:

```bash
python3 scripts/ope.py opp-provider-adapter
```

## Current Scope

The checked fixture maps a compact OPP-style provider request and response to existing OPE semantics:

- OPP `PredictionRequest` fields map into OPE domain config, forecast request, source policy, horizon, output type, caller identity, and response constraints.
- OPP `PredictionResponse` fields map from OPE forecast cards and forecast artifacts.
- OPE `forecastId`, `questionId`, evidence-trace read ID, lifecycle-bundle read ID, score status, and claim boundary are carried through OPP `audit` metadata.
- The OPP Agent Card fixture advertises only checked local fixture capabilities, supported domains, output types, horizons, compliance boundary, and pricing mode.
- OPE records remain authoritative; OPP is only a discovery and response-shape adapter.

Normal checks do not start HTTP, SSE, payment, aggregation, hosted service, or network listener behavior.

## Request Mapping

The checked request mapping covers these OPP-style fields:

- `predictionRequestId`: OPE request ID and internal API idempotency metadata.
- `marketOrQuestion`: OPE forecast request question and resolution criteria after validation.
- `domain`: OPE domain config or setup domain label.
- `horizon`: OPE horizon, close time, and scheduled resolution timing.
- `outputType`: OPE output type, currently fixture-checked through binary forecasts.
- `sourcePolicy`: OPE source-policy contract and fixture/provided/approved-source boundary.
- `callerIdentity`: internal API caller identity; credential values remain outside OPE records.
- `constraints`: compact response size, audit metadata, and supported output constraints.

Every mapping row is checked as `mapped_to_ope_contract`, with `rawPromptStored: false` and `credentialValuesAccepted: false`.

## Response Mapping

The checked response maps from existing OPE read surfaces:

- forecast card: compact probability, title, horizon, score status, and claim boundary
- forecast artifact: authoritative forecast output and record binding
- evidence trace: evidence/source provenance read ID
- lifecycle bundle: full lifecycle read ID, not embedded by default

The accepted fixture response uses `forecast-602` / `question-601` and returns probability `0.41` from the OPE forecast card. Its OPP `audit` object points back to the OPE forecast card/artifact record types, evidence-trace read ID, lifecycle-bundle read ID, score status, and claim boundary.

## Agent Card

The checked Agent Card fixture advertises:

- provider ID `ope-local-fixture-provider`
- runtime `local_cli_fixture_only`
- pricing mode `free_local_fixture`
- domains `weather-logistics`, `weather-transit-delays`, and `seaport-berth-availability`
- binary output support only in the checked fixture
- compliance status `policy_boundary_only`
- no live calibration claim
- no paid provider requirement
- no HTTP, SSE, or aggregation endpoint advertisement

## Conformance Cases

The checked conformance cases are:

- `accepted_forecast_card`: returns an OPP-style response from existing OPE records.
- `unsupported_market`: blocked with next action `choose_supported_domain`.
- `malformed_outcome_spec`: blocked with next action `repair_resolution_rule`.
- `missing_source_policy`: blocked with next action `provide_source_policy`.
- `provider_timeout`: blocked with next action `retry_or_use_ope_readback`.
- `response_too_large`: blocked with next action `request_compact_response`.

Blocked cases do not create forecast artifacts, mutate OPE records, or expose unsafe diagnostics.

## Future HTTP Boundary

A future minimal OPP HTTP provider surface may expose:

- `/opp/v1/agent-card`
- `/opp/v1/predictions`

Those endpoints should call OPE's internal API and read OPE records. They should not redefine forecast generation, evidence semantics, resolution, scoring, calibration, payment settlement, aggregation, or hosted runtime behavior.

Until that runtime is implemented and checked, OPE should describe OPP support as optional provider-adapter planning over local fixtures. Local MCP stdio remains the tested current agent protocol.
