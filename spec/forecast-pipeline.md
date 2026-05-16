# Local Forecast Pipeline

Status: implemented as a fixture-mode scaffold.

The local forecast pipeline connects controlled request intake to generated forecast records. It is intentionally not a hosted service, network API, SDK, or live model runtime.

## Command

Check committed pipeline outputs:

```bash
python3 scripts/run_forecast_pipeline.py
python3 scripts/ope.py pipeline
```

Refresh generated pipeline outputs:

```bash
python3 scripts/run_forecast_pipeline.py --write
python3 scripts/ope.py pipeline --write
```

Use a specific request fixture:

```bash
python3 scripts/ope.py pipeline --request spec/fixtures/requests/generate-weather-logistics-request.json
```

## Current Flow

The fixture-mode pipeline:

1. validates a forecast request against `forecast-request.schema.json`
2. applies request intake policy
3. rejects blocked, rejected, canceled, or validation-only requests
4. normalizes committed weather fixture input
5. builds the deterministic baseline
6. emits a provisional forecast question, feature snapshot, evidence packet, forecast artifact, forecast history, and pipeline-run summary
7. avoids network access and live fetches
8. keeps `effectfulGeneration` false because this is a local dry-run scaffold

Generated outputs live under `spec/fixtures/generated/pipeline/`.

## Boundary

The pipeline does not resolve or score the generated forecast. Resolution and scoring remain separate lifecycle steps, handled by the fixture loop or live outcome resolver when matching declared outcome sources exist.

The pipeline also does not expose:

- a network API
- background job processing
- persistent storage beyond checked generated fixtures
- non-deterministic model calls
- paid provider calls
- live weather fetches unless a future explicitly scoped integration adds them

## Guardrails

Normal release checks verify that:

- accepted generation requests produce the checked pipeline outputs
- blocked requests do not generate outputs
- forecast-time provenance excludes future resolution sources
- generated forecast artifacts remain readable through the read-only record interface
- the public record index includes the generated pipeline artifact
