# Live Connector Readiness

Status: implemented as a policy-bound readiness gate for the Open-Meteo weather connector.

This contract prepares OPE for intentional live connector testing without making normal release checks depend on network access. It separates three modes:

- `fixture_replay`: deterministic normal-check mode using committed fixtures
- `integration_live_fetch`: explicit developer-run mode for one allow-listed Open-Meteo request
- `hosted_live_fetch`: future service-runtime mode, not implemented

The schema is `spec/live-connector-readiness.schema.json`. The generated readiness record lives at `spec/fixtures/generated/live-readiness/weather-logistics-open-meteo-live-readiness.generated.json`.

## Commands

Check the committed readiness record:

```bash
python3 scripts/generate_live_connector_readiness.py --check
python3 scripts/check_live_connector_readiness.py
python3 scripts/ope.py live-readiness --check
```

Print the readiness record:

```bash
python3 scripts/ope.py live-readiness
```

Run the opt-in integration live fetch:

```bash
python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD
```

Save a sanitized connector-bound result into the ignored local workspace:

```bash
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
```

The live command is intentionally not part of `python3 scripts/run_checks.py` or `python3 scripts/release_check.py`.

## Boundaries

The readiness record states:

- the allow-listed endpoint: `https://api.open-meteo.com/v1/forecast`
- maximum one network call per integration check
- 20-second timeout boundary
- zero-cost, read-only, non-private source posture
- no broad web search
- no prompt-visible credentials
- metadata-only raw source retention with content hash
- sanitized public diagnostics
- no raw stack traces or raw diagnostic storage in public records
- no live calibration, all-evidence, forecast-quality, hosted-runtime, or release-readiness claim

## Trace Binding

The readiness record binds the live connector to the same first auto-evidence request, source policy, evidence plan, source connector registry, source connector result set, connector result, fixture evidence trace, forecast, and question IDs used by the fixture-safe path.

A successful integration live fetch proves only that the connector can return a sanitized, connector-bound result for the allow-listed source. It does not make the result part of a forecast run, track record, release gate, or hosted runtime until a future milestone adds those records explicitly.

## Local Capture

When `--save-local` is used, OPE writes a schema-bound connector result set under `.ope/live/`. That directory is ignored by git. A developer can validate the saved result and convert a successful result into a local evidence source-set draft:

```bash
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --draft-source-set --write
```

Local captures and drafts are not public read records, forecast artifacts, track-record inputs, calibration inputs, or release-check inputs.
