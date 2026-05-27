# OPE Fixtures

Fixtures are split into:

- `valid/`: schema-valid examples for the first lifecycle records.
- `invalid/`: intentionally bad semantic examples for future validation harnesses.
- `source/`: fixture-loop inputs that simulate pre-forecast, baseline, and resolution sources for resolved, ambiguous, and annulled cases.
- `live/`: fixture-mode weather source and declared operations records for the controlled live path.
- `local-source-files/`: small local CSV/JSON files and rejected examples for the source manifest builder.
- `benchmark/`: clean and contaminated benchmark-run fixtures for anti-leakage checks.
- `methods/`: method registry fixtures for enabled and proposed forecasting methods.
- `requests/`: controlled request intake fixtures for accepted, blocked, canceled, rejected, and adversarial cases.
- `generated/`: deterministic reports produced from valid fixtures.

The `invalid/` fixtures may still be valid JSON and may pass an isolated JSON Schema check. They are meant to fail cross-record lifecycle validation, such as:

- scoring an ambiguous question
- scoring an annulled question
- returning a forecast artifact whose `questionId` does not match the originating request

Those checks require a contract test harness and are tracked in the roadmap.

Update generated reports with:

```bash
python3 scripts/generate_fixture_reports.py --write
python3 scripts/run_fixture_loop.py --write
python3 scripts/resolve_live_weather_outcome.py --write
python3 scripts/plan_auto_evidence.py --write
python3 scripts/gather_auto_evidence.py --write
python3 scripts/generate_source_connectors.py --write
python3 scripts/generate_live_connector_readiness.py --write
python3 scripts/generate_transit_forward_run_corpus.py --write
python3 scripts/generate_transit_baseline_track_record_gate.py --write
python3 scripts/generate_transit_method_options.py --write
python3 scripts/generate_transit_live_evidence_promotion.py --write
python3 scripts/generate_domain_setups.py --write
python3 scripts/build_source_manifest.py --write
python3 scripts/generate_source_adapter_output.py --write
python3 scripts/generate_source_adapter_intake.py --write
python3 scripts/generate_source_intake_handoff.py --write
python3 scripts/generate_source_handoff_method_gate.py --write
python3 scripts/generate_source_intake.py --write
python3 scripts/run_auto_evidence_forecast.py --write
python3 scripts/resolve_auto_evidence_outcome.py --write
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
python3 scripts/generate_private_setup_adapter_chain_runbook.py --write
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write
python3 scripts/generate_private_setup_adapter_conformance_summary.py --write
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
```

The normal check command compares committed generated reports without rewriting them:

```bash
python3 scripts/run_checks.py
```

The fixture loop emits normal scored reports for resolved outcomes and `excluded` scoring reports for ambiguous or annulled outcomes.

The live outcome resolver emits resolved live fixture records under `generated/live-outcome/`, but marks public quality claims provisional until the minimum comparable-outcome threshold is met.

The auto-evidence fixture path emits request-bound plan, source-set, forecast, resolution, scoring, calibration, and track-record records under `generated/auto-evidence/` and `generated/auto-evidence-resolution/`.

The source connector generator emits a registry and result set under `generated/source-connectors/`.

The live connector readiness generator emits an offline readiness record under `generated/live-readiness/`.

Ignored local live captures and source-set drafts live under `.ope/live/`, not under `generated/`, and are excluded from fixture reports, public record indexes, track records, calibration, and release checks.

The transit forward-run corpus generator emits a checked corpus index under `generated/transit-forward-run-corpus/` with one comparable scored run, exclusion examples, sample thresholds, and claim boundaries. The transit baseline track-record gate emits a checked read model under `generated/transit-baseline-track-record-gate/` with current Brier, baseline, lift, sample-size, horizon/window coverage, and below-threshold calibration status. The transit method options generator emits a checked read model under `generated/transit-method-options/` that keeps baseline-only execution as the default, records weather adjustment as evidence-only, and keeps richer methods proposed-only. The transit live evidence promotion generator emits a checked gate and one sanitized promoted source set under `generated/transit-live-evidence-promotion/`; raw local captures remain ignored under `.ope/live/`.

The domain setup generator emits reference and candidate setup records under `generated/domain-setups/`.

The source manifest builder inspects caller-approved local CSV/JSON files under `local-source-files/` and emits checked build results plus draft source manifest and field mapping files under `generated/source-builder/`. Rejected examples cover secrets, unsupported formats, oversized files, and post-outcome leakage indicators. Drafts are excluded from public read surfaces until source intake accepts them.

The source adapter output generator emits a checked external connector handoff under `generated/source-adapter-output/`; the source adapter intake generator emits five checked external adapter conformance cases under `generated/source-adapter-intake/`, routing accepted, needs-confirmation, insufficient-data, rejected, and unsafe outputs without executing connector code or creating forecast records.

The source intake handoff generator emits checked builder-to-intake handoff records under `generated/source-handoff/`, including unconfirmed, confirmed, insufficient-sample, and builder-rejected cases with deterministic next actions.

The source handoff method gate generator emits checked handoff-bound setup benchmark gates, setup method decisions, and method-gate summaries under `generated/source-handoff-method/`. These records remain non-generating until setup forecast execution is explicitly run.

The source intake generator emits manifest and field mapping fixtures under `source-intake/` and source intake reports under `generated/source-intake/`.

The setup benchmark gate generator emits deterministic-method execution gates under `generated/setup-benchmark/`.

The setup method decision generator emits source-intake-bound method decisions under `generated/setup-method-decision/`.

The setup forecast execution generator emits run summaries and deterministic or baseline forecast artifacts under `generated/setup-forecast/`.

The source handoff forecast generator emits explicit handoff-bound run summaries and one confirmed deterministic forecast under `generated/source-handoff-forecast/`. Blocked handoff cases do not bind forecast outputs.

The source handoff resolver emits resolution, scoring, calibration, track-record, and outcome-summary records under `generated/source-handoff-resolution/`. It resolves only the generated confirmed forecast and keeps blocked handoff cases non-scored.

The source handoff setup runbook generator emits a checked agent workflow under `generated/source-handoff-runbook/` that maps local source setup cases to safe next actions and read surfaces.

The private setup workflow generator emits a checked domain-agnostic workflow contract under `generated/private-setup-workflow/` and preserves generic manual upload/private API/database runtimes as planned-only surfaces.

The private setup request generator emits checked request-routing examples under `generated/private-setup-requests/` and keeps setup intent classification non-executing.

The private setup first-action generator emits checked dispatcher examples under `generated/private-setup-actions/` and keeps each response non-executing even when it names a checked local command.

The private setup first-action runbook generator emits checked guidance under `generated/private-setup-actions/` and keeps planned, unknown, unsafe, and approval-missing sources out of source intake.

The private setup agent bundle generator emits checked request/action/runbook joins under `generated/private-setup-agent-bundles/` and keeps every bundle read-only and non-generating.

The private setup adapter-chain runbook generator emits checked operation-sequence guidance under `generated/private-setup-adapter-chain/` and keeps the runbook from executing adapter calls or creating artifacts.

The private source adapter capability generator emits checked non-executing adapter declarations under `generated/private-source-adapters/` and keeps manual uploads, private APIs, and private databases runtime-not-implemented.

The private source adapter outcome generator emits a checked next-action matrix under `generated/private-source-adapters/` and keeps planned, unsupported, unsafe, and credential-missing cases non-generating.

The private source adapter bridge generator emits a checked intake bridge under `generated/private-source-adapters/` and routes only to source-builder, source-handoff confirmation, fixture evidence, or no current entrypoint.

The private source adapter guidance envelope joins the capability, outcome, and bridge records under `generated/agent-adapter/` without executing source reads or creating manifests, forecasts, scores, credentials, live fetches, or hosted runtime work.

The private setup adapter conformance matrix embeds checked source-builder, source-handoff, method-gate, forecast-execution, and generated forecast readback envelopes under `generated/private-setup-adapter-conformance/` as conformance evidence only.

The private setup adapter conformance summary emits a compact read surface under `generated/private-setup-adapter-conformance/` for routine agents that need counts and boundaries without the full embedded-envelope matrix.

The private source-kind selection generator emits checked next-path examples under `generated/private-source-kind-selection/` and keeps every example non-executing and non-generating. The query-matrix generator in the same directory records full-list, selected, and unsupported adapter responses as conformance fixtures, not execution evidence.

The recalculation history generator emits trigger, run, evidence, artifact, feature snapshot, and appended forecast-history records under `generated/recalculation/`.

The local forecast pipeline emits provisional request-bound forecast records under `generated/pipeline/`. It rejects blocked requests and does not resolve or score the forecast.

The pipeline resolver emits request-bound resolution, scoring, calibration, and track-record records under `generated/pipeline-resolution/`.

The release manifest emits a schema-bound local surface summary at `generated/release-manifest.generated.json`.

The benchmark checker expects clean pre-outcome runs to pass and known-answer, post-outcome, source-contamination, and temporal-leakage runs to fail.

The method registry checker validates `methods/weather-logistics-method-registry.json` and requires enabled non-baseline methods to bind to clean comparable baseline benchmark runs.

The method-comparison generator emits a checked report under `generated/method-comparison/` covering every non-baseline registry method.

The method-selection generator emits a checked explanation under `generated/method-selection/` and falls back to the baseline when comparable method evidence is insufficient for the request source policy.

The historical-only baseline generator emits checked no-API forecast records under `generated/historical-baseline/`.

The forecast-run generators emit a checked run summary, intake matrix, and agent runbook under `generated/forecast-run/`.

The agent-adapter fixture and protocol-map generators emit checked transport-neutral envelopes and adapter mapping records under `generated/agent-adapter/` for request validation, evidence planning, card reads, lifecycle bundle reads, private setup bundle reads, private setup adapter-chain runbook reads, private source adapter guidance, local-file source-builder draft guidance, source-handoff next-action guidance, method-gate guidance, checked forecast execution, generated private setup forecast readback, resolution status, scoring summary, sanitized error behavior, local MCP stdio, and future adapters.

Aggregate fixtures are included in `valid/` for dependency and source-correlation hardening checks.
