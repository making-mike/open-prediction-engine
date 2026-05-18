# Open Prediction Engine Agent Guide

This file gives coding agents the minimum reliable context needed to work in this repository.

## Project Purpose

Open Prediction Engine (OPE) is an open, agent-native forecasting package and standard for setting up evidence-producing prediction engines from connected source data. It helps agents and supervised automated workflows turn future-facing questions into resolvable forecast contracts, gather or accept allowed evidence under a declared source policy, normalize sources, build features, run baseline and model forecasts, preserve forecast histories, produce probabilistic forecast artifacts, record provenance, recalculate when evidence changes, resolve outcomes, score forecasts, and update calibration over time.

OPE should remain domain-agnostic in product vision while using one narrow reference domain to prove measurable value before broad public quality claims.

OPE is not a universal prediction oracle, a generic agent protocol, a web crawler that claims to know all available internet evidence, a pooled-demand service, a payment settlement layer, or an independent trust authority. It should produce portable records and evidence without depending on any specific external transport, funding, settlement, or audit system.

The target product direction is agent-native private prediction setup: a caller may connect files, APIs, databases, manual mappings, or policy-bound auto-evidence sources, and OPE should help agents produce OPE-standard forecast artifacts that record what was connected, how it was interpreted, which method was justified, how forecasts changed, and how outcomes were scored.

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
- `PRODUCT.md`: compact product direction, audience, agent requirements, claim boundaries, and product metrics.
- `whitepaper.md`: public positioning and architecture narrative for OPE.
- `research/whitepaper-evaluation.md`: research-backed critique of the whitepaper and recommended next implementation priorities.
- `spec/README.md`: index of the first machine-readable OPE contracts.
- `spec/domains/weather-logistics.md`: reference wedge and domain-specific resolution rules.
- `spec/live-outcome-resolution.md`: fixture-mode live outcome resolution and provisional claim boundary.
- `spec/auto-evidence.md`: `data: auto` dry-run, fixture-replay, forecast, resolution, and source-policy boundary.
- `spec/source-connectors.md`: checked connector registry, result-set, evidence-plan binding, and source-set binding boundary for policy-bound evidence gathering.
- `spec/live-connector-readiness.md`: policy-bound readiness gate for explicit Open-Meteo integration live checks outside normal release checks.
- `spec/live-capture-workspace.md`: ignored local workspace for sanitized opt-in live connector captures and source-set drafts.
- `spec/domain-setup.md`: domain-agnostic setup contract, maturity labels, and candidate private setup guardrails.
- `spec/source-manifest-builder.md`: local CSV/JSON inspection and draft manifest/mapping boundary before intake.
- `spec/source-intake-handoff.md`: checked handoff from builder drafts to source intake next actions.
- `spec/source-handoff-method-gate.md`: checked bridge from source-intake handoffs to setup benchmark and method decisions.
- `spec/source-intake.md`: bounded source manifest, field mapping, and pre-forecast usability report.
- `spec/setup-benchmark-gate.md`: setup-specific benchmark gate for non-baseline method execution without broader quality claims.
- `spec/setup-method-decision.md`: setup-aware method decision and claim boundary before forecast execution.
- `spec/setup-forecast-execution.md`: setup-aware forecast execution boundary from accepted intake to setup-bound forecast artifacts.
- `spec/source-handoff-forecast.md`: explicit fixture-mode forecast execution from accepted source-handoff method gates.
- `spec/source-handoff-resolution.md`: fixture-mode resolution and scoring for the source-handoff forecast.
- `spec/source-handoff-setup-runbook.md`: checked agent workflow from source-builder handoff to resolved forecast read surfaces.
- `spec/private-setup-workflow.md`: domain-agnostic private setup workflow and source-runtime boundary.
- `spec/private-source-adapters.md`: checked private source adapter capability declarations and non-execution boundary.
- `spec/private-source-adapter-outcomes.md`: checked outcome matrix for private source adapter next actions.
- `spec/private-source-adapter-bridge.md`: checked bridge from adapter outcomes to allowed source-intake entrypoints.
- `spec/recalculation-history.md`: append-only recalculation trigger, run, and history boundary.
- `spec/evidence-trace.schema.json`: compact read-only trace linking forecasts to evidence and connector records.
- `spec/method-registry.md`: supported method registry, benchmark binding, and method-selection boundary.
- `spec/agent-adapter.md`: transport-neutral envelope, exit-code, capability, and transcript boundary for agent callers.
- `spec/agent-adapter-protocol-map.md`: local MCP stdio mapping and future HTTP/queue adapter plan for the local dispatcher.
- `spec/agent-forecast-run.md`: local fixture-safe forecast-run summary, intake matrix, and failure boundary for agents.
- `spec/agent-forecast-runbook.md`: checked local runbook for agent forecast-run next actions and read surfaces.
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

For OPE, keep the reusable contract-first, security, review, commit, and decision-logging rules, but replace source-project assumptions with OPE-specific boundaries:

- engine-owned forecast generation, provenance, resolution, scoring, and calibration
- question governance and forecast histories before track-record claims
- narrow reference wedges before broad public quality claims
- flexible private domain setup with explicit maturity labels
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
python3 scripts/check_method_registry.py
python3 scripts/compare_forecasting_methods.py --check
python3 scripts/check_method_comparison.py
python3 scripts/select_forecasting_method.py --check
python3 scripts/check_method_selection.py
python3 scripts/build_agent_adapter_fixtures.py --check
python3 scripts/check_agent_adapter.py
python3 scripts/check_agent_adapter_dispatcher.py
python3 scripts/generate_agent_adapter_protocol_map.py --check
python3 scripts/check_agent_adapter_protocol_map.py
python3 scripts/check_mcp_adapter.py
python3 scripts/run_agent_forecast.py --check
python3 scripts/check_agent_forecast_run.py
python3 scripts/generate_forecast_run_intake_matrix.py --check
python3 scripts/check_forecast_run_intake_matrix.py
python3 scripts/generate_agent_forecast_runbook.py --check
python3 scripts/check_agent_forecast_runbook.py
python3 scripts/check_live_weather_connector.py
python3 scripts/check_live_weather_baseline.py
python3 scripts/check_live_weather_evidence.py
python3 scripts/resolve_live_weather_outcome.py
python3 scripts/plan_auto_evidence.py --check
python3 scripts/gather_auto_evidence.py --check
python3 scripts/generate_source_connectors.py --check
python3 scripts/check_source_connectors.py
python3 scripts/generate_live_connector_readiness.py --check
python3 scripts/check_live_connector_readiness.py
python3 scripts/check_live_capture_workspace.py
python3 scripts/generate_domain_setups.py --check
python3 scripts/check_domain_setups.py
python3 scripts/build_source_manifest.py --check
python3 scripts/check_source_manifest_builder.py
python3 scripts/generate_source_intake_handoff.py --check
python3 scripts/check_source_intake_handoff.py
python3 scripts/generate_source_handoff_method_gate.py --check
python3 scripts/check_source_handoff_method_gate.py
python3 scripts/generate_source_intake.py --check
python3 scripts/check_source_intake.py
python3 scripts/generate_setup_benchmark_gate.py --check
python3 scripts/check_setup_benchmark_gate.py
python3 scripts/select_setup_method.py --check
python3 scripts/check_setup_method_decision.py
python3 scripts/run_setup_forecast.py --check
python3 scripts/check_setup_forecast.py
python3 scripts/run_source_handoff_forecast.py --check
python3 scripts/check_source_handoff_forecast.py
python3 scripts/resolve_source_handoff_outcome.py
python3 scripts/check_source_handoff_resolution.py
python3 scripts/generate_source_handoff_setup_runbook.py --check
python3 scripts/check_source_handoff_setup_runbook.py
python3 scripts/generate_private_setup_workflow.py --check
python3 scripts/check_private_setup_workflow.py
python3 scripts/generate_private_source_adapter_capabilities.py --check
python3 scripts/check_private_source_adapter_capabilities.py
python3 scripts/generate_private_source_adapter_outcome_matrix.py --check
python3 scripts/check_private_source_adapter_outcome_matrix.py
python3 scripts/generate_private_source_adapter_intake_bridge.py --check
python3 scripts/check_private_source_adapter_intake_bridge.py
python3 scripts/generate_recalculation_history.py --check
python3 scripts/check_recalculation_history.py
python3 scripts/run_auto_evidence_forecast.py
python3 scripts/resolve_auto_evidence_outcome.py
python3 scripts/run_historical_baseline_forecast.py
python3 scripts/check_historical_baseline_forecast.py
python3 scripts/run_forecast_pipeline.py
python3 scripts/resolve_pipeline_outcome.py
python3 scripts/generate_release_manifest.py
python3 scripts/check_read_access.py
python3 scripts/check_read_contracts.py
python3 scripts/check_forecast_requests.py
python3 scripts/check_auto_evidence_plan.py
python3 scripts/check_auto_evidence_gathering.py
python3 scripts/check_auto_evidence_forecast.py
python3 scripts/check_auto_evidence_resolution.py
python3 scripts/check_forecast_pipeline.py
python3 scripts/check_pipeline_resolution.py
python3 scripts/check_ci_workflow.py
python3 scripts/check_hardening.py
python3 scripts/check_cli.py
python3 scripts/check_fixtures.py
python3 scripts/release_check.py
```

These commands validate JSON syntax, schema-bound fixtures, the reusable contract validator, generated report drift, scoring semantics, fixture evidence loops, benchmark leakage controls, method registry bindings, transport-neutral agent envelope examples, the local agent-call dispatcher, the local MCP stdio adapter scaffold and future protocol map, the local forecast-run summary, intake matrix, and runbook, controlled live-source fixture mode, live outcome resolution, local auto-evidence planning, connector-aware gathering, source connector boundaries, live connector readiness without network access, local source manifest building, source-builder to source-intake handoffs, source-handoff method gates, setup benchmark gates, setup-aware method decisions, setup-aware deterministic and baseline forecast execution, explicit source-handoff forecast execution, resolution, setup runbook guidance, private setup workflows, private source adapter capability declarations, outcome matrix, and intake bridge, append-only recalculation history, forecasting and resolution, historical-only baseline forecasting, local forecast pipeline generation and resolution, the release manifest, the CI workflow, read-only artifact, card, evidence-trace, bundle, source-set, connector-result, and track-record access, read-surface contracts, request intake, and hardening guardrails.

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

Read a connector-bound evidence trace:

```bash
python3 scripts/ope.py read --record-type evidence-trace --id forecast-602 --question-id question-601
```

Read the no-API historical baseline forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-702 --question-id question-701
```

Run the local forecast pipeline scaffold:

```bash
python3 scripts/ope.py evidence-plan
python3 scripts/ope.py gather-evidence
python3 scripts/ope.py source-connectors
python3 scripts/ope.py live-readiness
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check
python3 scripts/ope.py domain-setups
python3 scripts/ope.py source-builder
python3 scripts/ope.py source-handoff
python3 scripts/ope.py source-handoff-method
python3 scripts/ope.py source-intake
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-method
python3 scripts/ope.py setup-forecast
python3 scripts/ope.py source-handoff-forecast
python3 scripts/ope.py resolve-source-handoff
python3 scripts/ope.py source-handoff-runbook
python3 scripts/ope.py private-setup-workflow
python3 scripts/ope.py private-source-adapters
python3 scripts/ope.py private-source-adapter-outcomes
python3 scripts/ope.py private-source-adapter-bridge
python3 scripts/ope.py auto-forecast
python3 scripts/ope.py resolve-auto-evidence
python3 scripts/ope.py historical-forecast
python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json
python3 scripts/ope.py method-comparison
python3 scripts/ope.py method-selection
python3 scripts/ope.py recalculation
python3 scripts/ope.py forecast-run
python3 scripts/ope.py forecast-run-matrix
python3 scripts/ope.py forecast-runbook
python3 scripts/ope.py agent-envelopes
python3 scripts/ope.py agent-protocol-map
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-602 --question-id question-601
python3 scripts/ope.py pipeline
python3 scripts/ope.py resolve-pipeline
python3 scripts/ope.py manifest
```

Run the opt-in Open-Meteo integration readiness probe only when a developer intentionally asks for it:

```bash
python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
```

Run the local MCP stdio scaffold for an MCP-capable host:

```bash
python3 scripts/ope.py mcp-stdio
```

Update generated fixture reports after scoring changes with:

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
python3 scripts/generate_private_source_adapter_capabilities.py --write
python3 scripts/generate_private_source_adapter_outcome_matrix.py --write
python3 scripts/generate_private_source_adapter_intake_bridge.py --write
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

Still needed before any hosted or service release:

- generated language-specific validators if the project moves beyond the current OPE-scoped Python validator
- unit test runner
- fixture evidence-loop and live outcome commands backed by any future service runtime
- live auto-evidence commands backed by policy-bound connectors beyond the current dry-run planner
- production agent adapter runtime beyond the current schema-bound envelope fixtures, local dispatcher, local forecast-run orchestrator, and local MCP stdio scaffold
- release check backed by any future service runtime

## Implementation Rules

- Keep OPE domain-agnostic in standards and domain-specific in implementation evidence. Do not build or market "predict anything" behavior.
- Treat candidate private domain setups as descriptive contracts until source manifests, field mappings, benchmarks, and resolved outcomes justify stronger labels.
- Treat source intake as a pre-forecast gate. It may classify usable data and eligible methods, but it must not create forecast artifacts.
- Treat source manifest builder outputs as drafts. Local file inspection can propose manifests and mappings, but it must not create public read records or forecast artifacts.
- Treat source intake handoffs as next-action guidance. They may route accepted intake toward method gates, but they must not bypass setup benchmark or method decisions.
- Treat source-handoff method gates as method-selection guidance, not forecast outputs. Accepted cases still require explicit setup forecast execution.
- Treat source-handoff forecast execution as the first artifact-generating handoff step. It must preserve handoff, source intake, benchmark, and method-decision bindings.
- Treat source-handoff resolution as fixture scoring only; one resolved source-handoff outcome is not a calibration or quality claim.
- Treat source-handoff setup runbooks as guidance over checked local fixtures, not a general private API/database parser.
- Treat private setup workflow records as domain-agnostic contracts. They may describe future manual upload, private API, or database source kinds, but they must label them as not implemented until a runtime exists.
- Treat private source adapter capability records as declarations, not source execution. They must not imply credential access, live fetching, arbitrary parsing, or forecast evidence creation.
- Treat private source adapter outcome matrices as next-action guidance only. They must not create source manifests, forecast artifacts, scoring records, or credential records.
- Treat private source adapter bridges as routing guidance only. They may point to checked local commands, but they must not execute source reads or produce forecast and scoring artifacts.
- Keep agent-inferred field or alias mappings as proposals until deterministic validation or user confirmation accepts them.
- Treat setup benchmark gates as execution gates, not quality claims. A stronger method needs confirmed source roles, clean anti-leakage controls, positive baseline lift, and explicit sample-size boundaries.
- Treat setup method decisions as method-policy explanations, not forecast outputs. A stronger method needs confirmed source roles and a setup-specific benchmark gate.
- Setup forecast execution may create artifacts only after source intake and setup method decisions allow it. Blocked setup outcomes must not bind forecast IDs or artifact paths.
- Keep OPE agent-accessible. Prefer schema-bound JSON inputs and outputs, deterministic command behavior, sanitized errors, compact forecast cards, evidence traces, and lifecycle bundles that agents can inspect without hidden side effects.
- Keep adapters thin. Adapter envelopes may expose OPE records and state summaries, but they must not redefine forecast, evidence, resolution, or scoring semantics.
- Treat `data: auto` as policy-bound evidence gathering, not unbounded internet search. Every auto-evidence path must declare source policy, allowed connectors, freshness rules, provenance, unavailable evidence, and connector registry/result bindings.
- Define the forecast question, lifecycle state, horizon, close time, resolution criteria, resolution source, fallback sources, and output type before building model logic.
- Build simple baseline forecasts before complex models, and compare OPE outputs against those baselines.
- Preserve historical-only requests as baseline-only unless the request explicitly allows forecast-time evidence sources; do not use weather API signals in `committed_fixture`-only forecasts.
- Introduce stronger forecasting methods only with benchmark, leakage, provenance, and baseline-lift controls. Do not describe a method as state of the art until OPE has local evidence for that claim.
- Every serious forecast artifact should bind forecast ID, question ID, question status, domain, horizon, forecast timestamp, close time, model version, input source classes, provenance references, probability or distribution, baseline forecast, optional aggregate forecast, calibration band, resolution criteria, resolution source, fallback sources, and scheduled resolution time.
- Forecast histories must be logged before the outcome is known. Do not allow retroactive edits to silently change pre-resolution records.
- Recalculation must append forecast-history states instead of overwriting prior forecasts. Post-outcome evidence, resolution sources, or records received after forecast close must not alter forecast-time probabilities.
- Ambiguous and annulled questions must be explicit and must not silently pollute normal scoring summaries.
- Use proper scoring rules where appropriate, such as Brier score for binary or categorical forecasts and log score when the domain supports it.
- Report calibration and quality by domain, horizon, output type, resolution source, coverage period, and sample size. Do not generalize narrow results into universal trust claims.
- Keep source credibility and provenance explicit. Distinguish raw source data, normalized features, model outputs, baseline outputs, and scored outcomes.
- Keep public error messages sanitized by default and route raw diagnostics to trusted logs.
- Do not put secrets into forecast artifacts, provenance metadata, discovery metadata, prompt-visible tool arguments, examples, or long-lived agent memory.
- External network calls in tests must be mocked, skipped, allow-listed, or explicitly integration-scoped.
- Open-Meteo live readiness checks must stay opt-in through `live-readiness --live`; normal release checks must remain offline.
- Ignored `.ope/live/` captures are development drafts only. They must not enter public read indexes, release checks, track records, calibration, or forecast artifacts until a future explicit forecast command consumes and binds them.
- Treat paid, effectful, or privacy-sensitive forecast requests as approval-gated actions.
- Preserve request/result binding across the full lifecycle: caller identity, forecast question, domain, horizon, model version, evidence packet, resolution record, score, and terminal status must not drift apart.

## Commit Rules

- Commit only when the user explicitly asks for a commit or the task clearly includes publishing the work.
- Keep each commit to one coherent, reviewable slice.
- Before staging, inspect `git status` and relevant `git diff`; stage only files that belong to the current change.
- Include required schemas, fixtures, generated reports, docs, roadmap updates, and decision-log entries with the behavior that requires them.
- Run `python3 scripts/run_checks.py` and `python3 scripts/ope.py check` before committing. Run release-readiness checks when the change touches release surfaces, public claims, schemas, generated records, or CI.
- If a check cannot be run, say which one and why in the handoff or pull request notes.
- Use a concise imperative commit subject that names the changed contract, behavior, or documentation surface.
- Never commit raw live fetches, credentials, private source data, local `.ope/live/` drafts, unrelated local changes, or artifacts that overstate implemented behavior.

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
