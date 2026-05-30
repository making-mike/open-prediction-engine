# Transit Live Evidence Promotion

The transit live evidence promotion gate defines when an ignored local live draft may become committed forecast-time evidence for the weather-transit-delay MVP.

Generate the checked read surface with:

```bash
python3 scripts/ope.py transit-live-evidence-promotion
```

This command does not fetch live data, read `.ope/live/`, create forecasts, resolve outcomes, score forecasts, store credentials, or execute a promotion against local files. It emits a schema-bound gate and references the committed sanitized source-set artifact at `spec/fixtures/generated/transit-live-evidence-promotion/weather-transit-delays-promoted-source-set.generated.json`.

## Promotion Rule

A local live draft may be promoted only when all of these checks pass:

- source policy approval
- capture timestamp before forecast close
- freshness within policy
- metadata-only retention with raw local files ignored
- forecast-time source role
- anti-leakage check
- provenance binding with content hash

Post-close captures and resolution-only transit outcome captures are rejected as forecast-time evidence.

## Evidence Surfaces

The checked readback distinguishes:

- committed fixtures already available for fixture-mode runs
- local live drafts still ignored under `.ope/live/`
- promoted forecast-time evidence bound to an evidence source set
- resolution-only evidence that can resolve or score outcomes but cannot enter forecast provenance

The promoted source set preserves `executionMode: live_fetch` and `liveFetch: true` as provenance about the original capture, while normal repository checks validate only the committed sanitized artifact.
