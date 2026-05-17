# Live Source Policy

Status: first controlled weather connector policy.

Normal repository checks must not make live network calls. Live source access is opt-in and must write only normalized records unless a caller explicitly chooses to retain raw responses outside committed fixtures.

The current opt-in readiness gate is:

```bash
python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
```

This command is integration-scoped and not part of normal release checks.

## Allow-Listed Weather Source

Provider: Open-Meteo Weather Forecast API

Endpoint:

```text
https://api.open-meteo.com/v1/forecast
```

Allowed first-use purpose:

- forecast-time weather input for the `weather-logistics` wedge

Allowed first location:

- Warsaw, Poland
- latitude `52.2297`
- longitude `21.0122`
- timezone `Europe/Warsaw`

Allowed request shape:

- `latitude`
- `longitude`
- `daily=precipitation_sum,precipitation_probability_max,weather_code,wind_gusts_10m_max`
- `timezone=Europe/Warsaw`
- `precipitation_unit=mm`
- `start_date={service_date}`
- `end_date={service_date}`

The connector must reject non-allow-listed locations and must not accept arbitrary endpoint URLs.

## Execution Modes

- `fixture_replay`: normal-check mode using committed fixtures; no network access.
- `integration_live_fetch`: explicit developer-run readiness mode; one allow-listed Open-Meteo call, 20-second timeout, sanitized diagnostics, metadata-only retention, optional ignored local save.
- `hosted_live_fetch`: future service runtime mode; not implemented.

## Retention

For live fetches:

- record fetch timestamp
- record request URL
- record content hash
- record provider name
- record provider response timezone
- normalize only the fields needed by the first wedge

Raw live responses should be kept out of the repository by default. Fixture responses under `spec/fixtures/live/` are synthetic examples used for deterministic checks.

The ignored local path for raw live fetch experiments is:

```text
.ope/live/
```

## Stale Or Corrected Sources

A source should be treated as stale or unusable when:

- the requested service date is absent from the response
- daily weather arrays are missing required variables
- the response timezone differs from the allow-listed timezone
- the source was fetched after a benchmark retrieval cutoff
- the provider later corrects or backfills the data used in a scored run

Corrected sources should not silently overwrite prior forecast-time evidence. They should create a new source record and trigger a correction or exclusion review when they affect resolution.
