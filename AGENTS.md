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
- `docs/agents-and-humans.html`: compact shared orientation page for human contributors and coding agents.
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
- `spec/source-adapter-output.md`: checked external connector output handoff contract before source intake.
- `spec/source-adapter-intake.md`: checked external connector intake path from sanitized adapter output to source intake and method gates.
- `spec/source-quality-mapping-confidence.md`: checked source-quality and mapping-confidence read model over builder, adapter-intake, source-intake, and method-decision surfaces.
- `spec/local-source-runtime.md`: checked approved local-folder source runtime with caller approval, path allow-listing, size limits, sanitized diagnostics, and blocked examples.
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
- `spec/private-setup-request.md`: checked private setup request routing contract.
- `spec/private-setup-first-action.md`: checked private setup first-action dispatcher boundary.
- `spec/private-setup-first-action-runbook.md`: checked private setup first-action runbook boundary.
- `spec/private-setup-agent-bundle.md`: checked private setup agent bundle boundary.
- `spec/private-setup-orchestrator.md`: checked local private setup orchestration summary and non-execution boundary.
- `spec/agent-pilot-validation.md`: checked local MVP pilot protocol, task scenarios, feedback schema, rubric, and sanitized example-summary boundary.
- `spec/pilot-evidence-ledger.md`: checked sanitized pilot evidence intake ledger and real-session evidence boundary.
- `spec/pilot-session-packet.md`: checked real pilot-session task packet, sanitization review, and ledger-ready summary boundary.
- `spec/pilot-summary-intake.md`: checked sanitized pilot summary intake classifier before ledger review.
- `spec/local-usage-trace.md`: checked local-only MVP usage trace read model and aggregate product metrics.
- `spec/developer-adoption-surface.md`: checked local MVP quickstart, example scenario, integration notes, release notes, and generated-types decision.
- `spec/expansion-readiness-gate.md`: checked post-MVP readiness gate for hosted runtime, broader private sources, live evidence, stronger methods, and generated runtime types.
- `spec/repeating-prediction-setup.md`: checked local-first repeating prediction setup contract, recurrence examples, post-calibration policies, and non-execution boundary.
- `spec/prediction-campaign-manifest.md`: checked local dry-run campaign manifest with unique run IDs, duplicate prevention, local-state path policy, and status readbacks.
- `spec/prediction-campaign-runner.md`: checked dry-run terminal runner readback for campaign start command semantics and non-execution boundary.
- `spec/prediction-campaign-pre-calibration.md`: optional historical-only campaign pre-calibration boundary before pilot launch.
- `spec/prediction-campaign-forecast-creation.md`: checked dry-run handoff from a ready campaign runner decision to planned forecast artifact IDs.
- `spec/prediction-campaign-forecast-artifact.md`: checked unresolved campaign forecast artifact using the standard lifecycle contracts.
- `spec/prediction-campaign-forecast-write.md`: checked non-mutating campaign forecast lifecycle write plan and local-state guard boundary.
- `spec/prediction-campaign-resume.md`: checked non-mutating campaign resume readback and recovery boundary.
- `spec/lifecycle-operation-store.md`: checked local SQLite lifecycle operation store, storage adapter boundary, idempotency, leases, read models, and delete replacements for multi-agent execution.
- `spec/storage-adapter.md`: checked storage adapter responsibilities for ignored JSON compatibility, local SQLite, and Postgres-compatible backends.
- `spec/private-setup-adapter-chain-runbook.md`: checked guidance for the private setup adapter operation sequence and readback path.
- `spec/private-setup-adapter-conformance-matrix.md`: checked private setup adapter conformance matrix over existing generated envelopes.
- `spec/private-setup-adapter-conformance-summary.md`: compact read surface over the private setup adapter conformance matrix.
- `spec/private-source-adapters.md`: checked private source adapter capability declarations and non-execution boundary.
- `spec/private-source-adapter-outcomes.md`: checked outcome matrix for private source adapter next actions.
- `spec/private-source-adapter-bridge.md`: checked bridge from adapter outcomes to allowed source-intake entrypoints.
- `spec/private-source-kind-selection-examples.md`: checked examples for choosing private setup source-kind paths without execution.
- `spec/private-source-kind-query-matrix.md`: checked adapter query matrix for full-list, selected, and unsupported source-kind selection responses.
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
- `spec/transit-forward-run-corpus.md`: checked public transport forward-run corpus counts, exclusions, and claim boundary.
- `spec/transit-corpus-growth-loop.md`: checked append-readiness loop, exclusion ledger, and threshold progress readback for growing the transit corpus.
- `spec/transit-baseline-track-record-gate.md`: checked baseline track-record and calibration gate for the transit corpus.
- `spec/transit-method-options.md`: checked public transport MVP method options and baseline-default boundary.
- `spec/transit-live-evidence-promotion.md`: checked policy-bound promotion gate for ignored local transit live drafts.
- `spec/resolution-jobs.md`: checked agent-facing resolution job registry, including campaign-aware next-action readbacks.
- `spec/resolution-scheduler.md`: checked foreground terminal scheduler, including campaign-aware dry-run ticks.
- `spec/resolution-runtime-reliability.md`: checked failure taxonomy, retry guidance, provenance ledger, and live-source boundary for the resolution runtime.
- `spec/release-manifest.md`: generated local release manifest and claim boundary summary.
- `spec/mvp-local-runtime.md`: compact local MVP runtime runbook, machine interfaces, smoke checks, and claim boundary.
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

The current project runtime is Python 3.12+ standard library. There is no required package install step for normal checks and no third-party runtime dependency. Release readiness also runs dev-only static analysis with `ruff` and `mypy`; install them in an activated virtual environment for local release checks when the system Python is externally managed.

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
python3 -m pip install "ruff>=0.8,<1" "mypy>=1.13,<2"
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
python3 scripts/run_transit_delay_forward.py --check
python3 scripts/check_transit_delay_forward.py
python3 scripts/generate_transit_forward_run_corpus.py --check
python3 scripts/check_transit_forward_run_corpus.py
python3 scripts/generate_transit_corpus_growth_loop.py --check
python3 scripts/check_transit_corpus_growth_loop.py
python3 scripts/generate_transit_baseline_track_record_gate.py --check
python3 scripts/check_transit_baseline_track_record_gate.py
python3 scripts/generate_transit_method_options.py --check
python3 scripts/check_transit_method_options.py
python3 scripts/generate_transit_live_evidence_promotion.py --check
python3 scripts/check_transit_live_evidence_promotion.py
python3 scripts/generate_domain_setups.py --check
python3 scripts/check_domain_setups.py
python3 scripts/build_source_manifest.py --check
python3 scripts/check_source_manifest_builder.py
python3 scripts/generate_source_adapter_output.py --check
python3 scripts/check_source_adapter_output.py
python3 scripts/generate_source_adapter_intake.py --check
python3 scripts/check_source_adapter_intake.py
python3 scripts/generate_source_quality_mapping_confidence.py --check
python3 scripts/check_source_quality_mapping_confidence.py
python3 scripts/generate_local_source_runtime.py --check
python3 scripts/check_local_source_runtime.py
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
python3 scripts/generate_private_setup_requests.py --check
python3 scripts/check_private_setup_requests.py
python3 scripts/generate_private_setup_first_actions.py --check
python3 scripts/check_private_setup_first_actions.py
python3 scripts/generate_private_setup_first_action_runbook.py --check
python3 scripts/check_private_setup_first_action_runbook.py
python3 scripts/generate_private_setup_agent_bundles.py --check
python3 scripts/check_private_setup_agent_bundles.py
python3 scripts/generate_private_setup_orchestrator.py --check
python3 scripts/check_private_setup_orchestrator.py
python3 scripts/generate_agent_pilot_validation.py --check
python3 scripts/check_agent_pilot_validation.py
python3 scripts/generate_pilot_evidence_ledger.py --check
python3 scripts/check_pilot_evidence_ledger.py
python3 scripts/generate_pilot_session_packet.py --check
python3 scripts/check_pilot_session_packet.py
python3 scripts/generate_pilot_summary_intake.py --check
python3 scripts/check_pilot_summary_intake.py
python3 scripts/generate_local_usage_trace.py --check
python3 scripts/check_local_usage_trace.py
python3 scripts/generate_developer_adoption_surface.py --check
python3 scripts/check_developer_adoption_surface.py
python3 scripts/generate_expansion_readiness_gate.py --check
python3 scripts/check_expansion_readiness_gate.py
python3 scripts/generate_repeating_prediction_setup.py --check
python3 scripts/check_repeating_prediction_setup.py
python3 scripts/generate_prediction_campaign_manifest.py --check
python3 scripts/check_prediction_campaign_manifest.py
python3 scripts/generate_prediction_campaign_runner.py --check
python3 scripts/check_prediction_campaign_runner.py
python3 scripts/generate_prediction_campaign_forecast_creation.py --check
python3 scripts/check_prediction_campaign_forecast_creation.py
python3 scripts/generate_prediction_campaign_forecast_artifact.py --check
python3 scripts/check_prediction_campaign_forecast_artifact.py
python3 scripts/generate_prediction_campaign_forecast_write.py --check
python3 scripts/check_prediction_campaign_forecast_write.py
python3 scripts/generate_prediction_campaign_resume.py --check
python3 scripts/check_prediction_campaign_resume.py
python3 scripts/generate_resolution_jobs.py --check
python3 scripts/generate_resolution_jobs.py --campaign predictioncampaign-001 --check
python3 scripts/check_resolution_jobs.py
python3 scripts/run_resolution_scheduler.py --campaign predictioncampaign-001 --check
python3 scripts/check_resolution_scheduler.py
python3 scripts/generate_private_setup_adapter_chain_runbook.py --check
python3 scripts/check_private_setup_adapter_chain_runbook.py
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --check
python3 scripts/check_private_setup_adapter_conformance_matrix.py
python3 scripts/generate_private_setup_adapter_conformance_summary.py --check
python3 scripts/check_private_setup_adapter_conformance_summary.py
python3 scripts/generate_resolution_runtime_reliability.py --check
python3 scripts/check_resolution_runtime_reliability.py
python3 scripts/generate_private_source_adapter_capabilities.py --check
python3 scripts/check_private_source_adapter_capabilities.py
python3 scripts/generate_private_source_adapter_outcome_matrix.py --check
python3 scripts/check_private_source_adapter_outcome_matrix.py
python3 scripts/generate_private_source_adapter_intake_bridge.py --check
python3 scripts/check_private_source_adapter_intake_bridge.py
python3 scripts/generate_private_source_kind_selection_examples.py --check
python3 scripts/check_private_source_kind_selection_examples.py
python3 scripts/generate_private_source_kind_query_matrix.py --check
python3 scripts/check_private_source_kind_query_matrix.py
python3 scripts/generate_recalculation_history.py --check
python3 scripts/check_recalculation_history.py
python3 scripts/run_auto_evidence_forecast.py
python3 scripts/resolve_auto_evidence_outcome.py
python3 scripts/run_historical_baseline_forecast.py
python3 scripts/check_historical_baseline_forecast.py
python3 scripts/run_forecast_pipeline.py
python3 scripts/resolve_pipeline_outcome.py
python3 scripts/generate_release_manifest.py
python3 scripts/check_mvp_release_surface.py
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

These commands validate JSON syntax, schema-bound fixtures, the reusable contract validator, generated report drift, scoring semantics, fixture evidence loops, benchmark leakage controls, method registry bindings, transport-neutral agent envelope examples including private setup bundle, adapter-chain runbook, private source adapter guidance, source-builder, source-handoff, method-gate, forecast-execution, and generated readback surfaces, the local agent-call dispatcher, the local MCP stdio adapter scaffold and future protocol map, the local forecast-run summary, intake matrix, and runbook, controlled live-source fixture mode, live outcome resolution, local auto-evidence planning, connector-aware gathering, source connector boundaries, live connector readiness without network access, local source manifest building, source-adapter outputs, source-adapter intake gates, source-quality and mapping-confidence readbacks, approved local-source runtime boundaries, source-builder to source-intake handoffs, source-handoff method gates, setup benchmark gates, setup-aware method decisions, setup-aware deterministic and baseline forecast execution, explicit source-handoff forecast execution, resolution, setup runbook guidance, private setup workflows, private setup request routing, first-action dispatch, first-action runbook guidance, private setup agent bundles, local private setup orchestrator summaries, agent pilot validation protocol/rubric boundaries, pilot evidence intake boundaries, pilot session packet and summary-intake boundaries, local usage trace metric boundaries, developer adoption quickstart/readback boundaries, expansion readiness gating, private setup adapter-chain runbook guidance, and private setup adapter conformance matrices, private source adapter capability declarations, outcome matrix, intake bridge, guidance envelope, and source-kind selection examples, append-only recalculation history, forecasting and resolution, historical-only baseline forecasting, local forecast pipeline generation and resolution, resolution runtime reliability, transit corpus growth, transit live evidence promotion, the release manifest, MVP release-surface smoke checks, the CI workflow, read-only artifact, card, evidence-trace, bundle, source-set, connector-result, and track-record access, read-surface contracts, request intake, and hardening guardrails.

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
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-corpus-growth
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py transit-method-options
python3 scripts/ope.py transit-live-evidence-promotion
python3 scripts/ope.py domain-setups
python3 scripts/ope.py source-builder
python3 scripts/ope.py source-adapter-output
python3 scripts/ope.py source-adapter-intake
python3 scripts/ope.py source-quality
python3 scripts/ope.py local-source-runtime
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
python3 scripts/ope.py private-setup-requests
python3 scripts/ope.py private-setup-actions
python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001
python3 scripts/ope.py private-setup-action-runbook
python3 scripts/ope.py private-setup-bundles
python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001
python3 scripts/ope.py private-setup-orchestrator
python3 scripts/ope.py agent-pilot-validation
python3 scripts/ope.py pilot-evidence
python3 scripts/ope.py pilot-session-packet
python3 scripts/ope.py pilot-summary-intake
python3 scripts/ope.py local-usage-trace
python3 scripts/ope.py developer-adoption
python3 scripts/ope.py expansion-readiness
python3 scripts/ope.py repeating-prediction-setup
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign status
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign pre-calibration
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001
python3 scripts/ope.py private-setup-adapter-runbook
python3 scripts/ope.py private-setup-adapter-conformance
python3 scripts/ope.py private-setup-adapter-conformance-summary
python3 scripts/ope.py private-source-kind-selection
python3 scripts/ope.py private-source-kind-query-matrix
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
python3 scripts/ope.py resolution-runtime-reliability
python3 scripts/ope.py transit-corpus-growth
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py transit-method-options
python3 scripts/ope.py transit-live-evidence-promotion
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-602 --question-id question-601
python3 scripts/ope.py agent-call --operation private_setup_bundle --private-setup-request-id privatesetuprequest-001
python3 scripts/ope.py agent-call --operation private_setup_adapter_runbook
python3 scripts/ope.py agent-call --operation private_source_adapter_guidance
python3 scripts/ope.py agent-call --operation private_source_kind_selection
python3 scripts/ope.py agent-call --operation private_source_kind_selection --source-kind private_api
python3 scripts/ope.py agent-call --operation private_setup_source_builder --private-setup-request-id privatesetuprequest-001 --source-builder-case local_draft
python3 scripts/ope.py agent-call --operation private_setup_source_handoff --private-setup-request-id privatesetuprequest-001 --source-handoff-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation private_setup_method_gate --private-setup-request-id privatesetuprequest-001 --method-gate-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation private_setup_forecast_execution --private-setup-request-id privatesetuprequest-001 --forecast-execution-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation lifecycle_bundle --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation resolution_status --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102
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
python3 scripts/generate_transit_forward_run_corpus.py --write
python3 scripts/generate_transit_corpus_growth_loop.py --write
python3 scripts/generate_transit_baseline_track_record_gate.py --write
python3 scripts/generate_transit_method_options.py --write
python3 scripts/generate_transit_live_evidence_promotion.py --write
python3 scripts/generate_domain_setups.py --write
python3 scripts/build_source_manifest.py --write
python3 scripts/generate_source_adapter_output.py --write
python3 scripts/generate_source_adapter_intake.py --write
python3 scripts/generate_source_quality_mapping_confidence.py --write
python3 scripts/generate_local_source_runtime.py --write
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
python3 scripts/generate_agent_pilot_validation.py --write
python3 scripts/generate_pilot_evidence_ledger.py --write
python3 scripts/generate_pilot_session_packet.py --write
python3 scripts/generate_pilot_summary_intake.py --write
python3 scripts/generate_local_usage_trace.py --write
python3 scripts/generate_developer_adoption_surface.py --write
python3 scripts/generate_expansion_readiness_gate.py --write
python3 scripts/generate_repeating_prediction_setup.py --write
python3 scripts/generate_prediction_campaign_manifest.py --write
python3 scripts/generate_prediction_campaign_runner.py --write
python3 scripts/generate_prediction_campaign_forecast_creation.py --write
python3 scripts/generate_prediction_campaign_forecast_artifact.py --write
python3 scripts/generate_prediction_campaign_forecast_write.py --write
python3 scripts/generate_prediction_campaign_resume.py --write
python3 scripts/generate_resolution_jobs.py --write
python3 scripts/generate_resolution_jobs.py --campaign predictioncampaign-001 --write
python3 scripts/run_resolution_scheduler.py --campaign predictioncampaign-001 --write
python3 scripts/generate_private_setup_adapter_chain_runbook.py --write
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write
python3 scripts/generate_private_setup_adapter_conformance_summary.py --write
python3 scripts/generate_resolution_runtime_reliability.py --write
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
- Treat source adapter intake as a non-executing handoff gate for sanitized external connector outputs. It may validate manifests, mappings, provenance, source roles, freshness, and leakage boundaries, but it must not execute connector code, read credentials, store raw private rows, create forecast artifacts, create scoring records, or bypass source intake and method gates.
- Treat source-quality and mapping-confidence readbacks as compact guidance only. They may summarize freshness, coverage, role fit, entity scope, leakage risk, missingness, outcome availability, and mapping confidence over checked records, but they must not execute source reads or adapters, create source manifests, create forecast/resolution/scoring artifacts, store raw rows or credentials, or imply quality and production-readiness claims.
- Treat local source runtime records as one narrow approved local-folder boundary. They may require approval, enforce path and size limits, route accepted files through existing gates, and expose a forecast-card readback, but they must not parse arbitrary private APIs/databases, store credentials or raw rows, fetch live data, host watchers, create forecast artifacts directly, or imply production connector support.
- Treat source intake handoffs as next-action guidance. They may route accepted intake toward method gates, but they must not bypass setup benchmark or method decisions.
- Treat source-handoff method gates as method-selection guidance, not forecast outputs. Accepted cases still require explicit setup forecast execution.
- Treat source-handoff forecast execution as the first artifact-generating handoff step. It must preserve handoff, source intake, benchmark, and method-decision bindings.
- Treat source-handoff resolution as fixture scoring only; one resolved source-handoff outcome is not a calibration or quality claim.
- Treat source-handoff setup runbooks as guidance over checked local fixtures, not a general private API/database parser.
- Treat transit corpus growth loops as append-readiness read models. They may classify append-ready, excluded, and rejected candidate rows and report threshold progress, but normal checks must not mutate the canonical corpus, read ignored live workspaces, create forecast/resolution/scoring artifacts, or imply quality and calibration claims.
- Treat transit live evidence promotion as a policy gate over ignored local captures. Raw `.ope/live/` files must remain uncommitted; only sanitized normalized source-set records may become forecast-time evidence, and post-close or resolution-only captures must stay out of forecast provenance.
- Treat private setup workflow records as domain-agnostic contracts. They may describe future manual upload, private API, or database source kinds, but they must label them as not implemented until a runtime exists.
- Treat private source adapter capability records as declarations, not source execution. They must not imply credential access, live fetching, arbitrary parsing, or forecast evidence creation.
- Treat private source adapter outcome matrices as next-action guidance only. They must not create source manifests, forecast artifacts, scoring records, or credential records.
- Treat private source adapter bridges as routing guidance only. They may point to checked local commands, but they must not execute source reads or produce forecast and scoring artifacts.
- Treat private source adapter guidance envelopes as read-only joins over capability, outcome, and bridge records. They must not execute source reads, adapter calls, manifest creation, forecast creation, scoring, credential handling, live fetching, or hosted runtime work.
- Treat private source-kind selection examples as guidance only. They may recommend source-builder, mapping confirmation, fixture evidence, wait, replace, or stop paths, but they must not run commands or create source, forecast, scoring, credential, live-fetch, or hosted-runtime artifacts.
- Treat private source-kind selection envelopes as read-only exposure of those examples through `agent-call` or MCP. Optional source-kind queries may return one selected recommendation, but they must not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, source reads, credentials, live fetches, or hosted runtime work.
- Treat private source-kind query matrices as adapter conformance examples only. They may store checked full-list, selected, and unsupported envelopes, but they must not be treated as source-intake evidence, forecast artifacts, scoring records, or execution logs.
- Treat private setup requests as setup-intent classification only. They must not read private data, execute source commands, or produce forecast and scoring artifacts.
- Treat private setup first-action dispatch as a non-executing read surface. It may name checked local commands, but it must not run source-builder, source-handoff, gather-evidence, forecast execution, resolution, or scoring.
- Treat private setup first-action runbooks as non-executing guidance. They may explain next steps, but planned, unsafe, unknown, and approval-missing sources must not enter source intake through the runbook.
- Treat private setup agent bundles as read-only joins over request, action, and runbook records. They must not create source, forecast, scoring, live-fetch, or credential artifacts.
- Treat private setup orchestrator summaries as read-only joins over checked local fixtures. They must not execute commands, read private data, create source manifests, create forecasts, score forecasts, store credentials, fetch live data, or bypass source intake, mapping confirmation, benchmark gates, method decisions, and explicit forecast execution boundaries.
- Treat agent pilot validation packs as checked usability protocols only. They must not run pilot sessions, recruit participants, store raw transcripts, store private data, collect credentials, create forecast artifacts, or imply forecast-quality evidence.
- Treat pilot evidence ledgers as checked sanitized intake guidance only. They must not store raw transcripts, private data, credentials, prompt logs, or participant identity; checked examples do not count as real pilot evidence or unblock expansion.
- Treat pilot summary intake classifiers as checked examples only. They may classify sanitized summaries as ledger-ready, redaction-needed, or blocked, but they must not write ledger rows, record real sessions, store raw/private data, or unblock expansion.
- Treat local usage traces as checked local synthetic read models only. They must not collect hosted telemetry, write runtime logs, read private data, store prompts, store transcripts, store credentials, fetch live data, or imply real usage analytics.
- Treat developer adoption surfaces as read-only onboarding guidance only. They may name quickstart, scenario, integration, and release-boundary commands, but they must not execute commands, create artifacts, fetch live data, generate runtime types, store credentials, or imply production/runtime maturity.
- Treat expansion readiness gates as read-only decision surfaces only. They must not start hosted runtimes, execute private sources, fetch live data, create artifacts, generate runtime types, or imply quality claims.
- Treat private setup adapter-chain runbooks as non-executing guidance. They may name adapter operations and readback order, but they must not execute calls or create source, forecast, resolution, scoring, live-fetch, or credential artifacts.
- Treat private setup adapter-runbook envelopes as read-only guidance. They may expose the checked operation sequence through agent-call or MCP, but they must not execute adapter calls or create source, forecast, resolution, scoring, live-fetch, or credential artifacts.
- Treat private setup adapter conformance matrices as examples over checked envelopes only. They must not execute adapter calls, read private data, or create source, forecast, resolution, scoring, live-fetch, credential, or hosted-runtime artifacts.
- Treat private setup adapter conformance summaries as compact read-only guidance over the checked matrix. They must not embed full envelopes or execute adapter calls, read private data, or create source, forecast, resolution, scoring, live-fetch, credential, or hosted-runtime artifacts.
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
- For multi-milestone work, commit after each completed milestone once the relevant checks pass, unless the user explicitly asks not to commit.
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
