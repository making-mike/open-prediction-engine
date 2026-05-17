# Source Manifest Builder

Status: implemented as a local read-only builder for small caller-approved CSV and JSON files.

The source manifest builder is the step before source intake. It lets an agent inspect local files, draft an OPE source manifest, and draft a field mapping without producing forecasts or treating inferred mappings as verified facts.

It is intentionally conservative:

- it only reads explicit local file paths supplied by the caller or checked fixtures
- it supports small CSV and JSON object-array files
- it stores field names, counts, hashes, privacy flags, coverage, timestamps, and sanitized feature summaries
- it does not store raw example values
- it rejects secrets, unsupported formats, oversized files, and post-outcome leakage indicators
- it keeps all generated drafts out of public read surfaces

## Contracts

- `source-manifest-build.schema.json`: source inspection result, rejection reasons, draft-artifact bindings, and confirmation boundary.
- `source-manifest.schema.json`: draft source manifest emitted after inspection succeeds.
- `field-mapping.schema.json`: draft mapping emitted after inspection succeeds.

## Commands

Inspect checked builder cases:

```bash
python3 scripts/ope.py source-builder
python3 scripts/ope.py source-builder --case local_draft
python3 scripts/ope.py source-builder --case contains_secret
python3 scripts/ope.py source-builder --case unsupported_format
python3 scripts/ope.py source-builder --case oversized
python3 scripts/ope.py source-builder --case leakage
```

Inspect caller-approved local files:

```bash
python3 scripts/ope.py source-builder \
  --input weather_forecast=spec/fixtures/local-source-files/weather-forecast.json \
  --input historical_baseline=spec/fixtures/local-source-files/history.csv \
  --input declared_operations_outcome=spec/fixtures/local-source-files/outcome.csv \
  --mapping-hint declared_operations_outcome.date=service_date
```

Refresh checked builder fixtures:

```bash
python3 scripts/build_source_manifest.py --write
python3 scripts/build_source_manifest.py --check
python3 scripts/check_source_manifest_builder.py
```

## Mapping Boundary

The builder can produce `user_provided` mappings from caller hints, `registry_backed` mappings for exact local registry matches, and `agent_inferred` mappings for plausible aliases such as `city -> geography`, `date -> service_date`, or `rain_mm -> forecast_daily_precipitation_mm`.

Agent-inferred field and alias mappings are always emitted with:

```json
{
  "mappingOrigin": "agent_inferred",
  "mappingStatus": "proposed",
  "requiresConfirmation": true
}
```

Those proposed mappings can be sent to source intake, but source intake must return `needs_confirmation` until a caller confirms them. The builder's own `forecastGenerationAllowed` value is always `false`.

Use `python3 scripts/ope.py source-handoff` to inspect the checked next action after a builder draft is passed toward source intake.
