# Open Prediction Engine

Open Prediction Engine (OPE) is a contract-first forecasting engine for evidence-producing probabilistic forecasts.

OPE is being built around a narrow, auditable loop:

1. define a resolvable forecast question
2. record forecast-time evidence and provenance
3. preserve forecast history before the outcome is known
4. resolve the outcome from declared sources
5. score the forecast against a baseline
6. report calibration and track record with sample-size boundaries

The project is not a universal prediction oracle and does not expose a network API, SDK, model service, or production live-data workflow.

## Current State

The repository currently contains:

- JSON Schema contracts for forecast questions, evidence packets, forecast artifacts, histories, aggregate forecasts, resolution records, scoring reports, calibration summaries, track records, benchmark runs, forecast cards, the public record index, and the release manifest
- fixture examples for binary and interval-style forecasts
- a selected first domain wedge: `weather-logistics`
- a fixture-only evidence loop for resolved, ambiguous, and annulled weather-logistics cases
- dependency-free scoring checks for Brier, log loss, interval score, pinball loss, calibration buckets, baseline lift, and track-record summaries
- anti-leakage benchmark fixtures that distinguish clean pre-outcome runs from contaminated runs
- an allow-listed Open-Meteo weather connector that runs in deterministic fixture mode by default
- a deterministic baseline builder for fixture-mode live weather input
- a provisional evidence-bundle builder for fixture-mode live weather forecasts
- a fixture-mode live outcome resolver that scores one declared outcome while keeping quality claims provisional
- a read-only local file interface for forecast artifacts and track records
- a synthetic read-only forecast bundle view for bound lifecycle records
- a compact forecast card view with claim and sample-size warnings
- validation-only forecast request intake with approval gates and audit-safe decisions
- a local deterministic forecast pipeline scaffold for accepted fixture requests
- a fixture-mode resolver for request-bound pipeline forecasts
- a generated release manifest that summarizes implemented local surfaces and claim boundaries
- a CI release gate that runs the local release check and compile pass
- lightweight hardening and release-readiness checks
- a small local CLI wrapper for common repository workflows
- a reusable local contract validator and single-record validation command

## First Domain Wedge

The first wedge is weather-linked last-mile logistics disruption probability.

The initial question shape is:

```text
Will qualifying weather disrupt declared last-mile delivery operations in {geography} during {service_date}?
```

This domain was chosen because it has frequent outcomes, clear resolution paths, simple baselines, and lower risk than domains such as healthcare, credit, employment, finance, legal outcomes, or public-safety automation.

See `spec/domains/weather-logistics.md` for the domain contract.

## Repository Map

- `AGENTS.md`: working guide for coding agents.
- `.agents/`: reusable rules, workflows, resources, and decision log.
- `whitepaper.md`: public project narrative.
- `research/whitepaper-evaluation.md`: critique and implementation priorities.
- `roadmap.md`: execution plan and milestone status.
- `spec/`: schemas, fixture records, scoring rules, domain notes, and benchmark rules.
- `scripts/`: dependency-free CLI, checks, validators, and fixture generators.

## Checks

The current project runtime is Python 3.12+ standard library. There is no required package install step.

The current bootstrap check uses only the Python 3 standard library:

```bash
python3 scripts/run_checks.py
python3 scripts/ope.py check
```

Individual checks:

```bash
python3 scripts/check_json.py
python3 scripts/check_schema_contracts.py
python3 scripts/check_contract_validator.py
python3 scripts/generate_fixture_reports.py
python3 scripts/run_fixture_loop.py
python3 scripts/check_benchmarks.py
python3 scripts/check_live_weather_connector.py
python3 scripts/check_live_weather_baseline.py
python3 scripts/check_live_weather_evidence.py
python3 scripts/resolve_live_weather_outcome.py
python3 scripts/run_forecast_pipeline.py
python3 scripts/resolve_pipeline_outcome.py
python3 scripts/generate_release_manifest.py
python3 scripts/check_read_access.py
python3 scripts/check_read_contracts.py
python3 scripts/check_forecast_requests.py
python3 scripts/check_forecast_pipeline.py
python3 scripts/check_pipeline_resolution.py
python3 scripts/check_ci_workflow.py
python3 scripts/check_hardening.py
python3 scripts/check_cli.py
python3 scripts/check_fixtures.py
```

Release-readiness wrapper:

```bash
python3 scripts/release_check.py
python3 scripts/ope.py release-check
```

Read an artifact:

```bash
python3 scripts/ope.py read --record-type forecast-artifact --id forecast-101 --question-id question-101
```

Read a lifecycle bundle:

```bash
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-502 --question-id question-501
```

Read a compact forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-502 --question-id question-501
```

List public generated records:

```bash
python3 scripts/ope.py list --record-type forecast-artifact --domain weather-logistics
python3 scripts/ope.py list --record-type forecast-bundle --domain weather-logistics
python3 scripts/ope.py list --record-type forecast-card --domain weather-logistics
```

Validate a request without executing it:

```bash
python3 scripts/ope.py request --input spec/fixtures/requests/valid-weather-logistics-request.json
```

Validate one contract record:

```bash
python3 scripts/ope.py validate --input spec/fixtures/valid/binary-weather-logistics-question.json
```

Run the local fixture-mode forecast pipeline:

```bash
python3 scripts/ope.py pipeline
```

Resolve the local pipeline forecast:

```bash
python3 scripts/ope.py resolve-pipeline
```

Check the release manifest:

```bash
python3 scripts/ope.py manifest
```

CI release gate:

```text
.github/workflows/release-check.yml
```

Generated fixture reports can be refreshed with:

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

## Not Yet Implemented

OPE still needs:

- generated runtime types or non-Python validators if the project moves beyond local scripts
- a production service runtime if OPE grows beyond local file and CLI surfaces
- production live-data operations beyond the current allow-listed fixture-checked connector
- a network API, SDK, or hosted service
- a resolved live outcome corpus before any live calibration claim

Until those exist, quality claims should remain limited to the committed fixture harness.
