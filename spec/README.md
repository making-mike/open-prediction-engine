# OPE Spec Package

This directory contains the first machine-readable contracts for OPE.

The contracts are intentionally record-first:

- `forecast-question.schema.json`: resolvable question contract.
- `forecast-request.schema.json`: controlled request intake contract.
- `source-policy.schema.json`: policy boundary for provided, hybrid, or auto evidence gathering.
- `source-connector-registry.schema.json`: policy-bound connector capabilities for auto-evidence gathering.
- `source-connector-result-set.schema.json`: connector result records for committed fixture replay and ignored local live captures, with raw metadata, normalized fields, unavailable evidence, diagnostics, and provenance.
- `live-connector-readiness.schema.json`: policy-bound readiness record for explicit integration live connector checks.
- `domain-setup.schema.json`: domain-agnostic setup record for reference and candidate private prediction engines.
- `source-manifest-build.schema.json`: local source inspection result for drafting source manifests and mappings before intake.
- `source-manifest.schema.json`: bounded caller-provided source manifest for setup intake.
- `field-mapping.schema.json`: source-field to setup-field mapping contract.
- `source-intake-handoff.schema.json`: checked handoff from builder drafts to source intake next actions.
- `source-intake-report.schema.json`: deterministic pre-forecast source usability report.
- `setup-benchmark-gate.schema.json`: setup-specific benchmark gate for non-baseline method execution.
- `setup-method-decision.schema.json`: setup-aware method decision over source-intake reports.
- `setup-forecast-run.schema.json`: setup-aware forecast execution summary binding setup intake, method decision, and generated forecast outputs.
- `recalculation-trigger.schema.json`: accepted or rejected trigger for forecast updates from changed evidence.
- `recalculation-run.schema.json`: append-only recalculation result with previous and updated forecast bindings.
- `evidence-gathering-plan.schema.json`: dry-run plan for policy-bound auto evidence.
- `evidence-source-set.schema.json`: normalized source and provenance records gathered under an evidence plan.
- `evidence-trace.schema.json`: compact read-only trace linking forecasts to evidence and connector records.
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
- `method-registry.schema.json`: forecasting method registry and benchmark boundary.
- `method-comparison.schema.json`: baseline comparison report for registered non-baseline methods.
- `method-selection.schema.json`: method-selection explanation and quality boundary.
- `agent-envelope.schema.json`: transport-neutral envelope for agent adapter calls.
- `agent-adapter-protocol-map.schema.json`: checked mapping from local agent calls to MCP stdio and future protocol adapters.
- `forecast-run-summary.schema.json`: compact agent-facing summary for the fixture-safe forecast run orchestrator.
- `forecast-run-intake-matrix.schema.json`: checked agent-facing outcome matrix for forecast-run request intake.
- `agent-forecast-runbook.schema.json`: checked agent workflow for forecast-run next actions and read surfaces.
- `source-handoff-setup-runbook.schema.json`: checked agent workflow for private source setup handoff next actions and read surfaces.
- `private-setup-workflow.schema.json`: domain-agnostic private setup workflow contract and runtime boundary.
- `private-source-adapter-capability.schema.json`: private source adapter capability declarations and non-execution boundary.
- `private-source-adapter-outcome-matrix.schema.json`: private source adapter outcome matrix and agent next-action boundary.
- `private-source-adapter-intake-bridge.schema.json`: checked bridge from adapter outcomes to allowed source-intake entrypoints.
- `pipeline-run.schema.json`: local forecast pipeline execution summary.
- `forecast-card.schema.json`: compact read-only forecast summary.
- `record-index.schema.json`: public generated record index.
- `release-manifest.schema.json`: local release surface and claim-boundary summary.
- `benchmarking.md`: benchmark and anti-leakage rules.
- `method-registry.md`: supported method registry and selection boundary.
- `agent-adapter.md`: transport-neutral agent envelope, exit-code, capability, and transcript boundary.
- `agent-adapter-protocol-map.md`: local MCP stdio mapping and future HTTP/queue adapter plan for the local dispatcher.
- `agent-forecast-run.md`: local fixture-safe forecast run summary and failure boundary for agents.
- `agent-forecast-runbook.md`: checked runbook for local agent forecast-run callers.
- `ci-release-gate.md`: CI release workflow boundary and local guard.
- `auto-evidence.md`: current `data: auto` dry-run planning surface and guardrails.
- `source-connectors.md`: policy-bound connector registry, result-set, and guardrails.
- `live-connector-readiness.md`: opt-in live connector readiness boundary for Open-Meteo.
- `live-capture-workspace.md`: ignored local workspace for sanitized opt-in live connector captures and source-set drafts.
- `domain-setup.md`: setup contract, maturity labels, and private candidate guardrails.
- `source-manifest-builder.md`: local CSV/JSON inspection and draft manifest/mapping boundary.
- `source-intake-handoff.md`: builder-draft handoff into source intake and agent next-action boundary.
- `source-handoff-method-gate.md`: source-handoff bridge into setup benchmark and method decisions.
- `source-handoff-setup-runbook.md`: checked source-handoff setup workflow for agents.
- `private-setup-workflow.md`: domain-agnostic private setup workflow and source-runtime boundary.
- `private-source-adapters.md`: checked private source adapter capability declarations.
- `private-source-adapter-outcomes.md`: checked private source adapter outcome matrix.
- `private-source-adapter-bridge.md`: checked private source adapter bridge into source-builder, source-handoff, and fixture evidence entrypoints.
- `source-intake.md`: bounded manifest, mapping, and pre-forecast usability report.
- `setup-benchmark-gate.md`: setup-specific stronger-method execution gate and claim boundary.
- `setup-method-decision.md`: setup-aware method decision and claim boundary.
- `setup-forecast-execution.md`: setup-aware deterministic/baseline forecast execution and blocked-run boundary.
- `source-handoff-forecast.md`: explicit source-handoff forecast execution and blocked-run boundary.
- `source-handoff-resolution.md`: fixture-mode resolution and scoring for the source-handoff forecast.
- `recalculation-history.md`: append-only recalculation trigger, run, and history boundary.
- `forecast-pipeline.md`: local fixture-mode forecast pipeline scaffold.
- `pipeline-resolution.md`: fixture-mode resolution of request-bound pipeline forecasts.
- `release-manifest.md`: generated release manifest and non-goal boundary.
- `live-source-policy.md`: first allow-listed live source and retention policy.
- `live-outcome-resolution.md`: fixture-mode live outcome resolution and provisional claim boundary.
- `runtime-validation.md`: local contract validation surface and supported JSON Schema subset.
- `read-access.md`: local read-only artifact, card, bundle, evidence-trace, source-set, connector-result, and track-record access surface.
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
The auto-evidence planner, fixture gatherer, and forecast generator read `spec/fixtures/requests/auto-weather-logistics-request.json` and write checked plan/source-set/forecast records under `spec/fixtures/generated/auto-evidence/`. The fixture gatherer rejects non-executable connector policies and binds source-set records to connector registry/result IDs.
The source connector generator writes checked connector registry and result-set records under `spec/fixtures/generated/source-connectors/`.
The live connector readiness generator writes a checked offline readiness record under `spec/fixtures/generated/live-readiness/`; the opt-in `--live` integration probe is not part of normal release checks.
The local live capture workspace writes ignored developer-only outputs under `.ope/live/`; those files are validated by local commands but are not generated fixtures or public read records.
The domain setup generator writes checked reference and candidate setup records under `spec/fixtures/generated/domain-setups/`.
The source manifest builder reads caller-approved local CSV/JSON fixtures under `spec/fixtures/local-source-files/` and writes checked draft build records, source manifests, and field mappings under `spec/fixtures/generated/source-builder/`; those drafts are not public read surfaces and cannot produce forecasts.
The source intake handoff generator writes checked builder-to-intake handoff records, source-intake reports, and next-action summaries under `spec/fixtures/generated/source-handoff/`.
The source handoff method gate generator writes checked handoff-bound setup benchmark gates, setup method decisions, and non-generating method-gate summaries under `spec/fixtures/generated/source-handoff-method/`.
The source intake generator writes checked manifest and mapping fixtures under `spec/fixtures/source-intake/` and checked intake reports under `spec/fixtures/generated/source-intake/`.
The setup benchmark gate generator writes checked stronger-method execution gates under `spec/fixtures/generated/setup-benchmark/`.
The setup method decision generator writes checked source-intake-bound method decisions under `spec/fixtures/generated/setup-method-decision/`.
The setup forecast execution generator writes checked run summaries and deterministic or baseline forecast records under `spec/fixtures/generated/setup-forecast/`.
The source handoff forecast generator writes checked explicit handoff-bound run summaries and one confirmed forecast record under `spec/fixtures/generated/source-handoff-forecast/`.
The source handoff resolver writes checked resolution, scoring, calibration, track-record, and outcome-summary records under `spec/fixtures/generated/source-handoff-resolution/`.
The source handoff setup runbook generator writes a checked agent workflow under `spec/fixtures/generated/source-handoff-runbook/`.
The private setup workflow generator writes a checked domain-agnostic workflow contract under `spec/fixtures/generated/private-setup-workflow/`.
The private source adapter capability generator writes checked non-executing adapter declarations under `spec/fixtures/generated/private-source-adapters/`.
The private source adapter outcome generator writes a checked next-action matrix under `spec/fixtures/generated/private-source-adapters/`.
The private source adapter bridge generator writes a checked intake bridge under `spec/fixtures/generated/private-source-adapters/`.
The recalculation generator writes checked trigger, run, evidence, artifact, and append-history records under `spec/fixtures/generated/recalculation/`.
The auto-evidence resolver reads those generated forecast records and writes checked resolution outputs under `spec/fixtures/generated/auto-evidence-resolution/`.
The historical-only baseline forecast reads `spec/fixtures/requests/historical-weather-logistics-request.json` and writes checked no-API forecast records under `spec/fixtures/generated/historical-baseline/`.
The method registry fixture lives under `spec/fixtures/methods/` and is checked against clean comparable benchmark runs.
The method-comparison generator writes checked baseline comparison records under `spec/fixtures/generated/method-comparison/`.
The method-selection generator writes a checked selection explanation under `spec/fixtures/generated/method-selection/`.
The forecast-run generator writes a checked agent-facing run summary under `spec/fixtures/generated/forecast-run/`.
The forecast-run intake matrix generator writes checked accepted, rejected, blocked, canceled, unsupported-fixture-path, and response-too-large examples under `spec/fixtures/generated/forecast-run/`.
The agent forecast runbook generator writes checked caller workflow examples under `spec/fixtures/generated/forecast-run/`.
The agent-adapter fixture generator writes checked transport-neutral envelope examples, including the evidence-trace operation, under `spec/fixtures/generated/agent-adapter/`.
The agent-adapter protocol-map generator writes a checked MCP stdio and future protocol plan under `spec/fixtures/generated/agent-adapter/`.
The local forecast pipeline reads an accepted request fixture and writes checked outputs under `spec/fixtures/generated/pipeline/`.
The pipeline resolver reads those generated forecast records and writes checked resolution outputs under `spec/fixtures/generated/pipeline-resolution/`.
The public read index is `spec/fixtures/generated/record-index.generated.json`.
Schema-bound fixtures are validated by `python3 scripts/check_schema_contracts.py`.

These schemas describe OPE records. The repository also includes local Python scripts for fixture generation, reusable contract validation, schema-bound read surfaces, read-only forecast card, evidence trace, and lifecycle bundle access, transport-neutral agent envelope examples, a local single-operation agent dispatcher, a local MCP stdio scaffold over that dispatcher, a local fixture-safe forecast-run orchestrator, intake matrix, and runbook, a checked mapping for MCP plus future HTTP and queue adapters, request intake, controlled live-source fixture mode, auto-evidence dry-run planning, fixture gathering, source connector boundary checks, live connector readiness and ignored live-capture workspace checks, domain setup inspection, local source manifest building for small approved CSV/JSON files, source-builder to source-intake handoffs, source-handoff method gates, explicit source-handoff forecast execution and resolution, a checked source-handoff setup runbook, a domain-agnostic private setup workflow contract, private source adapter capability declarations, outcome matrix, and intake bridge, source intake reports, setup benchmark gates, setup method decisions, setup-aware deterministic and baseline forecast execution, append-only recalculation history, forecast generation and resolution, historical-only baseline forecasting, method registry checks, fixture-mode live outcome resolution, a local deterministic forecast pipeline scaffold and resolver, a generated release manifest, a CI release gate, and a small local CLI wrapper. It does not yet expose a network API, SDK, hosted service, production auto-evidence fetching, production agent adapter runtime, production forecast use of live connector results or local live drafts, arbitrary private source parsing beyond the checked local builder boundary, generic manual upload, private API, or database connector runtimes, private source adapter bridge execution beyond routing guidance, additional setup methods beyond the current deterministic fixture path, live scheduler/watch recalculation, or live calibration claim.
