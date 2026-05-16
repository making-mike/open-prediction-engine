# OPE Spec Package

This directory contains the first machine-readable contracts for OPE.

The contracts are intentionally record-first:

- `forecast-question.schema.json`: resolvable question contract.
- `forecast-request.schema.json`: controlled request intake contract.
- `question-lifecycle.md`: lifecycle and unscorable status rules.
- `forecast-history.schema.json`: timestamped forecast states.
- `forecast-artifact.schema.json`: portable forecast output.
- `evidence-packet.schema.json`: provenance and evidence bundle.
- `aggregate-forecast.schema.json`: aggregate or ensemble forecast record.
- `resolution-record.schema.json`: resolved or unscorable outcome.
- `scoring-report.schema.json`: score or exclusion report.
- `track-record-report.schema.json`: performance summary across comparable forecasts.
- `calibration-summary.schema.json`: calibration buckets and error summary.
- `benchmark-run.schema.json`: anti-leakage benchmark run record.
- `pipeline-run.schema.json`: local forecast pipeline execution summary.
- `forecast-card.schema.json`: compact read-only forecast summary.
- `record-index.schema.json`: public generated record index.
- `release-manifest.schema.json`: local release surface and claim-boundary summary.
- `benchmarking.md`: benchmark and anti-leakage rules.
- `ci-release-gate.md`: CI release workflow boundary and local guard.
- `forecast-pipeline.md`: local fixture-mode forecast pipeline scaffold.
- `pipeline-resolution.md`: fixture-mode resolution of request-bound pipeline forecasts.
- `release-manifest.md`: generated release manifest and non-goal boundary.
- `live-source-policy.md`: first allow-listed live source and retention policy.
- `live-outcome-resolution.md`: fixture-mode live outcome resolution and provisional claim boundary.
- `runtime-validation.md`: local contract validation surface and supported JSON Schema subset.
- `read-access.md`: local read-only artifact, card, bundle, and track-record access surface.
- `request-access.md`: validation-only controlled forecast request intake.
- `claim-review.md`: public claim review checklist.
- `scoring.md`: first scoring formulas and sign conventions.
- `common.schema.json`: shared definitions.
- `field-review.md`: first pass over field purpose and public/private safety posture.
- `domains/weather-logistics.md`: selected first domain wedge and its source, resolution, baseline, and scope rules.

Fixtures live under `spec/fixtures/`.
Generated fixture reports live under `spec/fixtures/generated/` and are checked by `python3 scripts/run_checks.py`.
The fixture-only evidence loop reads `spec/fixtures/source/` and writes checked outputs under `spec/fixtures/generated/fixture-loop/`.
The fixture-mode live outcome resolver reads declared live source fixtures and writes checked outputs under `spec/fixtures/generated/live-outcome/`.
The local forecast pipeline reads an accepted request fixture and writes checked outputs under `spec/fixtures/generated/pipeline/`.
The pipeline resolver reads those generated forecast records and writes checked resolution outputs under `spec/fixtures/generated/pipeline-resolution/`.
The public read index is `spec/fixtures/generated/record-index.generated.json`.
Schema-bound fixtures are validated by `python3 scripts/check_schema_contracts.py`.

These schemas describe OPE records. The repository also includes local Python scripts for fixture generation, reusable contract validation, schema-bound read surfaces, read-only forecast card and lifecycle bundle access, request intake, controlled live-source fixture mode, fixture-mode live outcome resolution, a local deterministic forecast pipeline scaffold and resolver, a generated release manifest, a CI release gate, and a small local CLI wrapper. It does not yet expose a network API, SDK, hosted service, or live calibration claim.
