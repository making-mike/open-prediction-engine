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

The current checks are dependency-free. They parse JSON, validate schema-bound fixtures, smoke-test the reusable contract validator, regenerate fixture reports in check mode, verify scoring semantics, check the fixture evidence loop, resolve the fixture-mode live outcome, check historical-only baseline forecasting, check setup benchmark gates, check setup-aware deterministic and baseline forecast execution, check explicit source-handoff forecast execution, resolution, setup runbook guidance, private setup workflow boundaries, private setup request routing, first-action dispatch, first-action runbook guidance, private setup agent bundles, local private setup orchestrator summaries, and private setup adapter-chain runbook guidance and conformance matrices, private source adapter capability declarations, outcome matrix, intake bridge, guidance envelopes, and source-kind selection examples, check append-only recalculation history and post-outcome evidence rejection, check and resolve the local forecast pipeline scaffold, check source connector boundaries, check the live connector readiness gate without network access, check ignored local live-capture workspace guardrails, check resolution jobs, scheduler, and runtime reliability guardrails, check the transit forward-run corpus, baseline track-record gate, method options, and live evidence promotion gate, check domain setup records and candidate claim boundaries, check local source manifest builder boundaries, check external source adapter output and intake boundaries, check source-builder to source-intake handoff boundaries, check source-handoff method-gate boundaries, check source manifest and field mapping intake boundaries, check setup-aware method decisions, check agent adapter envelope examples including private setup bundle, adapter-chain runbook, source adapter guidance, source-builder, source-handoff, method-gate, forecast-execution, and generated readback surfaces, the local agent-call dispatcher, the local forecast-run summary, intake matrix, and runbook, the local MCP stdio adapter scaffold, and the protocol mapping for future adapters, check the release manifest, MVP release surface, and CI workflow, run benchmark anti-leakage checks, validate read-only record access and read-surface contracts, validate controlled request intake, and run hardening guardrails.

Read-only access includes forecast artifacts, track records, synthetic forecast bundles, compact forecast cards, private setup agent bundles, adapter-chain runbook envelopes, private source adapter guidance envelopes, transport-neutral agent envelope examples, the forecast-run summary, intake matrix, and runbook, the adapter protocol map, local MCP tool results, and one-operation agent-call responses assembled from existing public generated records.

## Development Rules

- Keep public claims scoped to implemented records and checks.
- Do not add network calls to normal checks.
- Do not commit raw live fetches; `.ope/live/` is ignored for local experiments.
- Keep live connector probes opt-in with `python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD`.
- Treat `.ope/live/` source-set drafts as local development inputs, not public forecast evidence.
- Treat source-builder outputs as draft local development inputs until source intake and setup gates accept them.
- Treat source adapter intake as a non-executing gate over sanitized external connector outputs; it must not execute connectors, store credentials, retain raw private rows, create forecast artifacts, or bypass source intake and method gates.
- Treat source-handoff records as next-action guidance, not forecast outputs.
- Treat source-handoff method gates as non-generating setup decisions until setup forecast execution is explicitly run.
- Treat source-handoff forecast execution as fixture-mode only until a service runtime exists.
- Treat source-handoff resolution as fixture scoring only; one resolved handoff forecast is not a quality or calibration claim.
- Treat source-handoff setup runbooks as checked local guidance, not broad private source ingestion support.
- Treat private setup workflows as contracts; generic manual upload, private API, and database runtimes remain unimplemented until a future runtime lands.
- Treat private setup requests as setup-intent classification only; they must not read private data, execute source commands, or create forecast and scoring artifacts.
- Treat private setup first-action dispatch as a compact non-executing read surface; it may name a checked command but must not run source-builder, source-handoff, gather-evidence, forecast execution, or scoring.
- Treat private setup first-action runbooks as guidance only; they must not execute named commands or move planned, unsafe, unknown, or approval-missing sources into intake.
- Treat private setup agent bundles as read-only joins over request, action, and runbook records; they must not create artifacts or weaken source-intake, forecast, or scoring gates.
- Treat private setup orchestrator summaries as read-only joins over checked local fixtures; they must not execute commands, read private data, create source manifests, create forecasts, score forecasts, store credentials, or bypass intake and method gates.
- Treat private setup adapter-chain runbooks as guidance only; they may name adapter operations and readback order, but must not execute adapter calls or create source, forecast, resolution, scoring, live-fetch, or credential artifacts.
- Treat private setup adapter-runbook envelopes as read-only guidance; they may expose the checked operation sequence through agent-call or MCP, but must not execute adapter calls or create source, forecast, resolution, scoring, live-fetch, or credential artifacts.
- Treat private setup adapter conformance matrices as examples over checked envelopes only; they must not execute adapter calls, read private data, or create source, forecast, resolution, scoring, live-fetch, credential, or hosted-runtime artifacts.
- Treat private setup adapter conformance summaries as compact read-only guidance over checked matrices; they must not embed full envelopes or execute adapter calls, read private data, or create source, forecast, resolution, scoring, live-fetch, credential, or hosted-runtime artifacts.
- Treat private source adapter capabilities as declarations only; they must not imply live fetching, credential access, or arbitrary private schema parsing.
- Treat private source adapter outcome matrices as next-action guidance only; they must not create source, forecast, score, or credential artifacts.
- Treat private source adapter bridges as routing guidance only; they must not execute source reads or create forecast and scoring artifacts.
- Treat private source adapter guidance envelopes as read-only joins over capability, outcome, and bridge records; they must not execute source reads, adapter calls, source-manifest creation, forecasts, scoring, live fetching, credential handling, or hosted runtime work.
- Treat private source-kind selection examples as non-executing guidance; they may point to the next setup path, but must not run commands, create manifests, forecasts, scores, credentials, live fetches, or hosted runtime work.
- Treat private source-kind selection envelopes as read-only exposure of those examples; optional source-kind queries may return one selected recommendation, but they must not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, source reads, credentials, live fetches, or hosted runtime work.
- Treat private source-kind query matrices as adapter conformance examples only; they must not create source-intake evidence, forecast artifacts, scoring records, credentials, live fetches, or execution logs.
- Add or update fixtures when changing schemas, scoring, lifecycle behavior, request intake, or read access.
- Prefer small, deterministic scripts over long-running services until the runtime decision changes.

## Commit Rules

- Commit only coherent, reviewable slices of work.
- Do not mix unrelated fixes, formatting churn, generated outputs, or exploratory edits in one commit.
- Before staging, inspect `git status` and the relevant `git diff`; stage only files that belong to the current change.
- Include required schemas, fixtures, generated reports, docs, roadmap updates, and decision-log entries with the behavior that requires them.
- Run `python3 scripts/run_checks.py` and `python3 scripts/ope.py check` before committing. Run the release-readiness commands too when the change affects release surfaces, public claims, schemas, generated records, or CI.
- If a check cannot be run, say which one and why in the handoff or pull request notes.
- Use a concise imperative commit subject that names the changed contract, behavior, or documentation surface.
- Never commit raw live fetches, credentials, private source data, local `.ope/live/` drafts, or artifacts that overstate implemented behavior.

## Generated Fixtures

Refresh generated reports only when source fixtures or scoring logic intentionally changes:

```bash
python3 scripts/generate_fixture_reports.py --write
python3 scripts/run_fixture_loop.py --write
python3 scripts/resolve_live_weather_outcome.py --write
python3 scripts/plan_auto_evidence.py --write
python3 scripts/gather_auto_evidence.py --write
python3 scripts/generate_source_connectors.py --write
python3 scripts/generate_live_connector_readiness.py --write
python3 scripts/generate_domain_setups.py --write
python3 scripts/build_source_manifest.py --write
python3 scripts/generate_source_adapter_output.py --write
python3 scripts/generate_source_adapter_intake.py --write
python3 scripts/generate_source_intake_handoff.py --write
python3 scripts/generate_source_handoff_method_gate.py --write
python3 scripts/generate_source_intake.py --write
python3 scripts/run_auto_evidence_forecast.py --write
python3 scripts/resolve_auto_evidence_outcome.py --write
python3 scripts/run_historical_baseline_forecast.py --write
python3 scripts/compare_forecasting_methods.py --write
python3 scripts/select_forecasting_method.py --write
python3 scripts/generate_setup_benchmark_gate.py --write
python3 scripts/select_setup_method.py --write
python3 scripts/run_setup_forecast.py --write
python3 scripts/run_source_handoff_forecast.py --write
python3 scripts/resolve_source_handoff_outcome.py --write
python3 scripts/generate_source_handoff_setup_runbook.py --write
python3 scripts/generate_private_setup_workflow.py --write
python3 scripts/generate_private_setup_requests.py --write
python3 scripts/generate_private_setup_first_actions.py --write
python3 scripts/generate_private_setup_first_action_runbook.py --write
python3 scripts/generate_private_setup_agent_bundles.py --write
python3 scripts/generate_private_setup_orchestrator.py --write
python3 scripts/generate_private_setup_adapter_chain_runbook.py --write
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write
python3 scripts/generate_private_setup_adapter_conformance_summary.py --write
python3 scripts/generate_resolution_runtime_reliability.py --write
python3 scripts/generate_transit_forward_run_corpus.py --write
python3 scripts/generate_transit_baseline_track_record_gate.py --write
python3 scripts/generate_transit_method_options.py --write
python3 scripts/generate_transit_live_evidence_promotion.py --write
python3 scripts/generate_private_source_adapter_capabilities.py --write
python3 scripts/generate_private_source_adapter_outcome_matrix.py --write
python3 scripts/generate_private_source_adapter_intake_bridge.py --write
python3 scripts/generate_private_source_kind_selection_examples.py --write
python3 scripts/generate_private_source_kind_query_matrix.py --write
python3 scripts/generate_recalculation_history.py --write
python3 scripts/run_agent_forecast.py --write
python3 scripts/generate_forecast_run_intake_matrix.py --write
python3 scripts/generate_agent_forecast_runbook.py --write
python3 scripts/build_agent_adapter_fixtures.py --write
python3 scripts/generate_agent_adapter_protocol_map.py --write
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
python3 scripts/ope.py setup-forecast
```

## CI

The GitHub Actions release gate runs:

```bash
python3 scripts/release_check.py
python3 -m py_compile scripts/*.py
```

The workflow itself is checked locally by `python3 scripts/check_ci_workflow.py`.
