# Contributing

OPE is currently a Python 3 standard-library project. There is no required package install step and no third-party runtime dependency.

## Setup

Use Python 3.12 or newer:

```bash
python3 --version
```

Optional local isolation:

```bash
python3 -m venv .venv
. .venv/bin/activate
```

## Checks

Run the normal repository checks:

```bash
python3 scripts/run_checks.py
python3 scripts/ope.py check
```

Run the release-readiness wrapper:

```bash
python3 scripts/release_check.py
python3 scripts/ope.py release-check
```

The current checks are dependency-free. They parse JSON, validate schema-bound fixtures, smoke-test the reusable contract validator, regenerate fixture reports in check mode, verify scoring semantics, check the fixture evidence loop, resolve the fixture-mode live outcome, check and resolve the local forecast pipeline scaffold, check the release manifest and CI workflow, run benchmark anti-leakage checks, validate read-only record access and read-surface contracts, validate controlled request intake, and run hardening guardrails.

Read-only access includes forecast artifacts, track records, synthetic forecast bundles, and compact forecast cards assembled from existing public generated records.

## Development Rules

- Keep public claims scoped to implemented records and checks.
- Do not add network calls to normal checks.
- Do not commit raw live fetches; `.ope/live/` is ignored for local experiments.
- Add or update fixtures when changing schemas, scoring, lifecycle behavior, request intake, or read access.
- Prefer small, deterministic scripts over long-running services until the runtime decision changes.

## Generated Fixtures

Refresh generated reports only when source fixtures or scoring logic intentionally changes:

```bash
python3 scripts/generate_fixture_reports.py --write
python3 scripts/run_fixture_loop.py --write
python3 scripts/resolve_live_weather_outcome.py --write
python3 scripts/run_forecast_pipeline.py --write
python3 scripts/resolve_pipeline_outcome.py --write
python3 scripts/generate_record_index.py --write
python3 scripts/generate_release_manifest.py --write
python3 scripts/ope.py generate-fixtures --write
```

## Contract Validation

Validate one record against an inferred or explicit schema:

```bash
python3 scripts/ope.py validate --input spec/fixtures/valid/binary-weather-logistics-question.json
python3 scripts/validate_contract_record.py --input spec/fixtures/valid/binary-weather-logistics-question.json --schema spec/forecast-question.schema.json
```

## Local Pipeline

Check the deterministic fixture-mode pipeline:

```bash
python3 scripts/ope.py pipeline
python3 scripts/ope.py resolve-pipeline
```

## CI

The GitHub Actions release gate runs:

```bash
python3 scripts/release_check.py
python3 -m py_compile scripts/*.py
```

The workflow itself is checked locally by `python3 scripts/check_ci_workflow.py`.
