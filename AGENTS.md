# Open Prediction Engine Agent Guide

This file gives coding agents the minimum reliable context needed to work in this repository.

## Project Purpose

Open Prediction Engine (OPE) is an open forecasting engine for evidence-producing probabilistic forecasts. It governs resolvable forecast questions, ingests signals, normalizes sources, builds features, runs baseline and model forecasts, preserves forecast histories, produces probabilistic forecast artifacts, records provenance, resolves outcomes, scores forecasts, and updates calibration over time.

OPE should start with one narrow forecast domain and prove measurable value before expanding.

OPE is not a universal prediction oracle, a generic agent protocol, a pooled-demand service, a payment settlement layer, or an independent trust authority. It should produce portable records and evidence without depending on any specific external transport, funding, settlement, or audit system.

## Important Documents

- `.agents/rules.md`: detailed repo operating rules.
- `.agents/resources/transferable-agent-baseline.md`: instructions for transferring this agent baseline to another repo.
- `.agents/resources/architecture_patterns.md`: agent architecture reference material.
- `.agents/resources/protocols_reference.md`: A2A, MCP, x402, and adjacent protocol reference material.
- `.agents/resources/security_checklist.md`: security review checklist for agent-facing systems.
- `.agents/resources/compliance_guide.md`: compliance framing and risk guidance.
- `.agents/workflows/log-decision.md`: decision log workflow.
- `.agents/workflows/protocol-development.md`: contract-first development workflow.
- `.agents/workflows/schema-change-checklist.md`: schema and contract change checklist.
- `README.md`: human onboarding and current repository status.
- `CONTRIBUTING.md`: local setup and contribution checks.
- `whitepaper.md`: public positioning and architecture narrative for OPE.
- `research/whitepaper-evaluation.md`: research-backed critique of the whitepaper and recommended next implementation priorities.
- `spec/README.md`: index of the first machine-readable OPE contracts.
- `spec/domains/weather-logistics.md`: selected first wedge and domain-specific resolution rules.
- `spec/live-outcome-resolution.md`: fixture-mode live outcome resolution and provisional claim boundary.
- `spec/runtime-validation.md`: local contract validation surface and supported schema subset.
- `spec/forecast-pipeline.md`: local fixture-mode forecast pipeline scaffold.
- `spec/pipeline-resolution.md`: fixture-mode resolution of request-bound pipeline forecasts.
- `spec/release-manifest.md`: generated local release manifest and claim boundary summary.
- `spec/ci-release-gate.md`: CI release workflow boundary and local guard.

Expected project documents as implementation lands:

- `roadmap.md`: execution plan and domain wedge status.
- `spec/`: machine-readable contracts for question lifecycle, forecast artifacts, evidence packets, forecast histories, aggregate forecasts, resolution records, scoring reports, track records, calibration summaries, and benchmark runs.
- `.agents/decisions.md`: durable architectural decision log. Create it fresh for OPE before logging the first non-trivial decision.

## Transferable Agent Materials

The `.agents/` directory is maintained as a reusable baseline for protocol-first, schema-first, agent-facing infrastructure repositories.

For OPE, keep the reusable contract-first, security, review, and decision-logging rules, but replace source-project assumptions with OPE-specific boundaries:

- engine-owned forecast generation, provenance, resolution, scoring, and calibration
- question governance and forecast histories before track-record claims
- narrow domain wedges before broad coverage
- baseline comparisons before stronger model-quality claims
- evidence packets before trust claims
- clear separation from transport, funding, settlement, and independent audit systems

## Development Commands

The current project runtime is Python 3.12+ standard library. There is no required package install step and no third-party dependency.

Canonical setup check:

```bash
python3 --version
```

Canonical test command:

```bash
python3 scripts/run_checks.py
python3 scripts/ope.py check
```

Canonical release-readiness command:

```bash
python3 scripts/release_check.py
python3 scripts/ope.py release-check
```

Individual checks:

```bash
python3 scripts/check_json.py
python3 scripts/check_schema_contracts.py
python3 scripts/check_contract_validator.py
python3 scripts/generate_fixture_reports.py
python3 scripts/run_fixture_loop.py
python3 scripts/generate_record_index.py
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
python3 scripts/release_check.py
```

These commands validate JSON syntax, schema-bound fixtures, the reusable contract validator, generated report drift, scoring semantics, fixture evidence loops, benchmark leakage controls, controlled live-source fixture mode, live outcome resolution, local forecast pipeline generation and resolution, the release manifest, the CI workflow, read-only artifact, card, bundle, and track-record access, read-surface contracts, request intake, and hardening guardrails.

Validate a single contract record with the local CLI:

```bash
python3 scripts/ope.py validate --input spec/fixtures/valid/binary-weather-logistics-question.json
```

Read a bound forecast lifecycle bundle:

```bash
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-502 --question-id question-501
```

Read a compact forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-502 --question-id question-501
```

Run the local forecast pipeline scaffold:

```bash
python3 scripts/ope.py pipeline
python3 scripts/ope.py resolve-pipeline
python3 scripts/ope.py manifest
```

Update generated fixture reports after scoring changes with:

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

Still needed before any hosted or service release:

- generated language-specific validators if the project moves beyond the current OPE-scoped Python validator
- unit test runner
- fixture evidence-loop and live outcome commands backed by any future service runtime
- release check backed by any future service runtime

## Implementation Rules

- Keep OPE domain-specific. Do not build or market "predict anything" behavior.
- Define the forecast question, lifecycle state, horizon, close time, resolution criteria, resolution source, fallback sources, and output type before building model logic.
- Build simple baseline forecasts before complex models, and compare OPE outputs against those baselines.
- Every serious forecast artifact should bind forecast ID, question ID, question status, domain, horizon, forecast timestamp, close time, model version, input source classes, provenance references, probability or distribution, baseline forecast, optional aggregate forecast, calibration band, resolution criteria, resolution source, fallback sources, and scheduled resolution time.
- Forecast histories must be logged before the outcome is known. Do not allow retroactive edits to silently change pre-resolution records.
- Ambiguous and annulled questions must be explicit and must not silently pollute normal scoring summaries.
- Use proper scoring rules where appropriate, such as Brier score for binary or categorical forecasts and log score when the domain supports it.
- Report calibration and quality by domain, horizon, output type, resolution source, coverage period, and sample size. Do not generalize narrow results into universal trust claims.
- Keep source credibility and provenance explicit. Distinguish raw source data, normalized features, model outputs, baseline outputs, and scored outcomes.
- Keep public error messages sanitized by default and route raw diagnostics to trusted logs.
- Do not put secrets into forecast artifacts, provenance metadata, discovery metadata, prompt-visible tool arguments, examples, or long-lived agent memory.
- External network calls in tests must be mocked, skipped, allow-listed, or explicitly integration-scoped.
- Treat paid, effectful, or privacy-sensitive forecast requests as approval-gated actions.
- Preserve request/result binding across the full lifecycle: caller identity, forecast question, domain, horizon, model version, evidence packet, resolution record, score, and terminal status must not drift apart.

## Release Expectations

Before calling OPE release-ready, the repository should have an explicit release check and at least one end-to-end forecast pipeline check covering:

1. input ingestion or fixture loading
2. baseline forecast generation
3. model forecast generation
4. evidence packet creation
5. forecast history logging
6. resolution fixture or source lookup
7. ambiguous or annulled status handling
8. scoring
9. track-record and calibration reporting

For changes touching public claims, review README, roadmap, examples, schemas, and agent-facing docs so they do not overstate implemented behavior.
