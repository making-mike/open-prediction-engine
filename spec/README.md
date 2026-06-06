# OPE Spec Package

This directory contains the first machine-readable contracts for OPE.

The contracts are intentionally record-first:

- `forecast-question.schema.json`: resolvable question contract.
- `forecast-request.schema.json`: controlled request intake contract.
- `source-policy.schema.json`: policy boundary for provided, hybrid, or auto evidence gathering.
- `source-connector-registry.schema.json`: policy-bound connector capabilities for auto-evidence gathering.
- `source-connector-result-set.schema.json`: connector result records for committed fixture replay and ignored local live captures, with raw metadata, normalized fields, unavailable evidence, diagnostics, and provenance.
- `live-connector-readiness.schema.json`: policy-bound readiness record for explicit integration live connector checks.
- `transit-api-connector.schema.json`: opt-in public transport API connector contract for GTFS-RT TripUpdates capture and decoded delay rows.
- `transit-delay-forward-run.schema.json`: checked weather-transit-delay forecast-to-resolution run summary.
- `transit-forward-run-corpus.schema.json`: checked corpus index over comparable and excluded weather-transit-delay forward runs.
- `transit-corpus-growth-loop.schema.json`: checked append-readiness loop, exclusion ledger, and progress readback for growing the transit corpus.
- `transit-baseline-track-record-gate.schema.json`: checked baseline track-record and calibration gate over the transit forward-run corpus, with explicit campaign-ledger inclusion.
- `transit-method-options.schema.json`: checked MVP method options and selection boundary for weather-transit-delay runs.
- `transit-live-evidence-promotion.schema.json`: checked policy-bound live evidence promotion gate for ignored transit live drafts.
- `transit-forward-run-resolver.schema.json`: checked local resolver-agent scan over transit forward-run states.
- `resolution-job-registry.schema.json`: agent-facing read model for pending, due, resolved, and invalid resolution jobs.
- `resolution-scheduler-run.schema.json`: foreground terminal scheduler run over resolution jobs, campaign-aware dry-run ticks, and checked resolver execution.
- `resolution-runtime-reliability.schema.json`: checked read model for resolution runtime failure taxonomy, retry guidance, provenance, and live-source boundaries.
- `domain-setup.schema.json`: domain-agnostic setup record for reference and candidate private prediction engines.
- `source-manifest-build.schema.json`: local source inspection result for drafting source manifests and mappings before intake.
- `source-adapter-output.schema.json`: portable handoff contract for external agent-built connectors that emit OPE source manifests and mappings.
- `source-adapter-intake.schema.json`: checked external adapter output intake matrix from sanitized handoff to source intake and method gates.
- `source-quality-mapping-confidence.schema.json`: checked source-quality and mapping-confidence readback over builder, adapter-intake, source-intake, and method-decision records.
- `local-source-runtime.schema.json`: checked approved local-folder source runtime, blocked-path examples, forecast-card readback, and non-goal boundary.
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
- `mcp-adoption-path.schema.json`: checked local MCP adoption transcript surface for readiness, candidates, guided forecast, forecast-card readback, blocked unsafe cases, and response-too-large.
- `forecast-run-summary.schema.json`: compact agent-facing summary for the fixture-safe forecast run orchestrator.
- `forecast-run-intake-matrix.schema.json`: checked agent-facing outcome matrix for forecast-run request intake.
- `agent-forecast-runbook.schema.json`: checked agent workflow for forecast-run next actions and read surfaces.
- `source-handoff-setup-runbook.schema.json`: checked agent workflow for private source setup handoff next actions and read surfaces.
- `private-setup-workflow.schema.json`: domain-agnostic private setup workflow contract and runtime boundary.
- `private-setup-request.schema.json`: agent-facing private setup request routing contract.
- `private-setup-first-action.schema.json`: compact non-executing first-action dispatcher result for one private setup request.
- `private-setup-first-action-runbook.schema.json`: checked runbook for first-action statuses and next safe agent steps.
- `private-setup-agent-bundle.schema.json`: compact read-only bundle joining request, first-action, and runbook guidance.
- `private-setup-orchestrator.schema.json`: checked local private setup orchestration summary over request, intake, method gate, forecast execution, and readback outcomes.
- `agent-pilot-validation.schema.json`: checked local pilot protocol, task scenarios, feedback dimensions, comprehension rubric, and sanitized example-summary boundary.
- `pilot-evidence-ledger.schema.json`: checked sanitized pilot evidence intake ledger with raw/private-data blockers and real-session threshold boundary.
- `pilot-session-packet.schema.json`: checked real pilot-session task packet, sanitized evidence template, stop conditions, and ledger-submission boundary.
- `pilot-summary-intake.schema.json`: checked sanitized pilot summary intake classifier before ledger review.
- `pilot-findings.schema.json`: checked pilot findings readback over sanitized real-session evidence, friction signals, next actions, and expansion/type/runtime claim boundaries.
- `simulated-agent-pilot.schema.json`: checked user-authorized simulated agent sessions over the prediction-feature setup path with approximate token/time counts and no real-session claim.
- `generated-runtime-types-decision.schema.json`: checked decision record for deferring or accepting language-specific generated runtime types.
- `local-usage-trace.schema.json`: checked local-only MVP usage and trace read model for CLI, agent-call, MCP, blocked-path, and release-surface events.
- `prediction-agent-adoption.schema.json`: checked general adoption surface, capability manifest, fit decision, extension points, bring-your-own-model guidance, and first-five-minutes adoption evaluation for agents building host prediction projects.
- `developer-adoption-surface.schema.json`: checked local MVP quickstart, example scenario, integration notes, release notes, and generated-types decision.
- `expansion-readiness-gate.schema.json`: checked post-MVP readiness gate over hosted runtime, broader private sources, live evidence, stronger methods, and generated runtime types.
- `repeating-prediction-setup.schema.json`: checked local-first repeating prediction setup contract with recurrence examples, end conditions, post-calibration policies, and non-execution boundary.
- `prediction-campaign-manifest.schema.json`: checked local dry-run campaign manifest with unique run IDs, duplicate prevention, local-state path policy, and status readbacks.
- `prediction-campaign-runner.schema.json`: checked terminal campaign runner readback with command semantics, output modes, dry-run decisions, and explicit guarded local forecast creation.
- `prediction-campaign-forecast-creation.schema.json`: checked dry-run handoff from ready campaign runner decision to planned forecast artifact IDs.
- Campaign forecast artifacts reuse `forecast-question.schema.json`, `evidence-packet.schema.json`, `forecast-artifact.schema.json`, and `forecast-history.schema.json` for the checked unresolved `forecast-1301` fixture.
- `prediction-campaign-forecast-write.schema.json`: checked plan and explicit guarded local write path for campaign forecast lifecycle records under ignored local campaign state.
- `prediction-campaign-resolution-attempt.schema.json`: checked due/not-due campaign resolver attempt readback with failure category, retry, source-fetch, diagnostics, and non-mutation boundary.
- `prediction-campaign-doctor.schema.json`: checked compact campaign health, queue, duplicate, recovery, and next-action readback for agents.
- `prediction-campaign-resume.schema.json`: checked non-mutating campaign resume readback with local-state inspection, recovery actions, and overwrite boundary.
- `prediction-campaign-evidence-ledger.schema.json`: checked append-only campaign evidence ledger readback with comparable/excluded row separation and idempotent local-write boundary.
- `prediction-campaign-calibration-status.schema.json`: checked campaign calibration-status readback, threshold cases, and post-calibration continuation boundary.
- `prediction-campaign-pre-calibration.schema.json`: optional historical-only pre-pilot calibration binding for campaign baseline probability.
- `prediction-campaign-method-update-gate.schema.json`: checked read-only gate before campaign calibration can influence method updates.
- `prediction-campaign-method-update-plan.schema.json`: checked non-effectful approval, command-shape, and rollback plan before future method updates.
- `prediction-campaign-method-update-action.schema.json`: guarded apply and rollback command readback for approved local campaign method bindings.
- `prediction-campaign-explain.schema.json`: checked pilot readback for next forecast, next resolution, evidence threshold, agent readbacks, sanitized error envelopes, and claim boundary.
- `helsinki-traffic-disturbance-pilot-runbook.schema.json`: checked local operations runbook for the 100-run Helsinki traffic disturbance pilot, including mini-smoke, operator status, success, and abort criteria.
- `helsinki-traffic-pilot-readiness.schema.json`: checked local launch-readiness readback for the 100-run Helsinki pilot before effectful local writes.
- `lifecycle-operation.schema.json`: checked lifecycle operation store readback for database-backed multi-agent execution, idempotency, leases, read models, SQLite scenarios, and delete replacements.
- `internal-api.schema.json`: checked embedded internal API operation surface for host and agent callers.
- `prediction-workspace-registry.schema.json`: checked multi-prediction workspace registry readback with stable prediction, campaign, domain, source-binding, schedule, workspace read-model, configuration-lifecycle, idempotency, lease, resource-control, and isolation statuses.
- `background-worker-runtime.schema.json`: checked bounded local worker and sidecar runtime readback with one-tick equivalence, resource limits, operation guards, blocked cases, and non-networked boundary.
- `runtime-security.schema.json`: checked lightweight runtime hardening readback for dependency budget, module boundaries, runtime surface controls, credential handling, threat notes, blocked examples, and execution boundaries.
- `agent-implementation-kit.schema.json`: checked agent prediction implementation kit with quickstart front door, compact manual, question-discovery intake, candidate contract readbacks, validation reports, adapter guidance, starter templates, and blocked-behavior boundary.
- `agent-integration.schema.json`: checked local agent incorporation golden path with Helsinki starter readiness, candidate discovery, validation reports, guided forecast-card command, MCP tools, and efficiency metrics.
- `agent-guidance.schema.json`: checked agent guidance loop for prompt classification, clarification questions, required source roles, safe next commands, Helsinki narrowing, and agent instruction rules.
- `prediction-feature-setup-request.schema.json`: compact host-project request contract for prediction-feature intent, decision context, approved source references, resolution hints, and response-size budget.
- `prediction-feature-setup-response.schema.json`: compact response contract for accepted, clarification, blocked, rejected, and response-too-large prediction-feature setup outcomes.
- `prediction-feature-setup.schema.json`: checked stable prediction-feature setup surface binding request, response examples, CLI, agent-call, MCP guidance, and non-execution boundaries.
- `postgres-compatibility.schema.json`: checked SQLite-to-Postgres lifecycle storage semantics readback with table mappings, adapter contract, scenario matrix, assumption guards, migration boundary, and non-execution boundary.
- `database-source-adapter-runtime.schema.json`: checked approved database source-adapter runtime readback with caller approval, credential references, query boundaries, sanitized adapter output, blocked cases, and non-execution boundary.
- `opp-provider-adapter.schema.json`: checked optional Open Prediction Protocol provider-adapter mapping over OPE forecast cards, artifacts, evidence traces, lifecycle bundles, Agent Card fixture, conformance cases, and protocol boundary.
- `persistent-sqlite-policy.schema.json`: checked opt-in persistent SQLite path policy readback with approval, allowlist, migration, backup, lock, blocked-case, and non-default runtime boundaries.
- `lifecycle-lease-policy.schema.json`: checked lifecycle operation lease policy readback splitting race-prone strict-lease operations from idempotency-only retry guards.
- `runtime-transport-readiness.schema.json`: checked runtime transport readiness gate for local surfaces versus deferred HTTP, queue, hosted service, and OPP HTTP provider surfaces.
- `workspace-tenant-isolation.schema.json`: checked tenant-scoped workspace isolation readback for resources, source bindings, operation queues, credential references, access cases, and runtime boundary flags.
- `domain-source-field-policy.schema.json`: checked policy readback for universal domain fields, universal source-binding fields, domain-specific extension containers, source-kind rules, and blocked fields.
- `credential-reference-policy.schema.json`: checked policy readback for acceptable opaque caller-owned credential references, scope keys, lifecycle states, consumer rules, cases, and non-resolution boundaries.
- `retention-redaction-policy.schema.json`: checked policy readback for retention classes, archive tombstones, redaction receipts, physical-delete exception gates, cases, and non-mutating boundaries.
- `private-auto-evidence-policy.schema.json`: checked source-policy overlay for private `data: auto` source kinds, policy gates, decision cases, readbacks, and non-execution boundaries.
- `domain-config.schema.json`: checked reusable domain configuration records for weather-transit and candidate seaport prediction setup.
- `source-binding.schema.json`: checked source binding setup records covering accepted, partial, rejected, and blocked configurations across local files, source-adapter outputs, APIs, and database adapter manifests.
- `private-setup-adapter-chain-runbook.schema.json`: checked adapter operation sequence and readback guidance for private setup callers.
- `private-setup-adapter-conformance-matrix.schema.json`: checked conformance examples across private setup adapter operation envelopes.
- `private-setup-adapter-conformance-summary.schema.json`: compact read surface over private setup adapter conformance.
- `private-source-adapter-capability.schema.json`: private source adapter capability declarations and non-execution boundary.
- `private-source-adapter-outcome-matrix.schema.json`: private source adapter outcome matrix and agent next-action boundary.
- `private-source-adapter-intake-bridge.schema.json`: checked bridge from adapter outcomes to allowed source-intake entrypoints.
- `private-source-kind-selection-examples.schema.json`: checked examples for selecting private setup source-kind paths without execution.
- `private-source-kind-query-matrix.schema.json`: checked adapter query examples for full-list, selected, and unsupported source-kind selection responses.
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
- `agent-integration.md`: checked local CLI/MCP golden path for agents asking what can be forecasted from approved source context.
- `prediction-feature-setup.md`: checked compact contract for host projects adding an OPE-backed prediction feature without creating a new execution path.
- `ci-release-gate.md`: CI release workflow boundary and local guard.
- `auto-evidence.md`: current `data: auto` dry-run planning surface and guardrails.
- `source-connectors.md`: policy-bound connector registry, result-set, and guardrails.
- `live-connector-readiness.md`: opt-in live connector readiness boundary for Open-Meteo.
- `transit-api-connector.md`: opt-in HSL GTFS-RT TripUpdates connector, decoder, and local handoff boundary.
- `transit-delay-forward-run.md`: checked transit-delay forecast, capture, resolution, scoring, and claim-boundary workflow.
- `transit-forward-run-corpus.md`: checked public transport forward-run corpus counts, exclusions, and claim boundary.
- `transit-corpus-growth-loop.md`: checked public transport corpus append-readiness loop and threshold progress readback.
- `transit-baseline-track-record-gate.md`: checked baseline track-record summary and calibration gate for the transit corpus.
- `transit-method-options.md`: checked public transport MVP method options and baseline-default selection boundary.
- `transit-live-evidence-promotion.md`: checked public transport live evidence promotion boundary.
- `transit-forward-run-resolver.md`: checked local resolver-agent scan and explicit execute boundary for due transit forward runs.
- `resolution-jobs.md`: agent-facing resolution job registry, campaign-aware readback, and next-action boundary.
- `resolution-scheduler.md`: foreground terminal scheduler for polling due resolution jobs, including campaign-aware dry-run ticks.
- `resolution-runtime-reliability.md`: checked failure taxonomy, retry guidance, provenance ledger, and resolution-only source boundary for the local runtime.
- `live-capture-workspace.md`: ignored local workspace for sanitized opt-in live connector captures and source-set drafts.
- `domain-setup.md`: setup contract, maturity labels, and private candidate guardrails.
- `source-manifest-builder.md`: local CSV/JSON inspection and draft manifest/mapping boundary.
- `source-adapter-output.md`: external connector output handoff contract before source intake.
- `source-adapter-intake.md`: checked external connector intake path and non-execution boundary.
- `source-quality-mapping-confidence.md`: checked source-quality and mapping-confidence read model.
- `local-source-runtime.md`: approved local-folder source runtime boundary.
- `source-intake-handoff.md`: builder-draft handoff into source intake and agent next-action boundary.
- `source-handoff-method-gate.md`: source-handoff bridge into setup benchmark and method decisions.
- `source-handoff-setup-runbook.md`: checked source-handoff setup workflow for agents.
- `private-setup-workflow.md`: domain-agnostic private setup workflow and source-runtime boundary.
- `private-setup-request.md`: checked private setup request routing contract.
- `private-setup-first-action.md`: checked private setup first-action dispatcher boundary.
- `private-setup-first-action-runbook.md`: checked private setup first-action runbook boundary.
- `private-setup-agent-bundle.md`: checked private setup agent bundle boundary.
- `private-setup-orchestrator.md`: checked local private setup orchestrator summary and non-execution boundary.
- `agent-pilot-validation.md`: checked local MVP pilot validation protocol, feedback schema, rubric, and privacy boundary.
- `agent-guidance.md`: checked guidance loop that helps calling agents turn messy developer prompts into safe OPE next moves.
- `pilot-evidence-ledger.md`: checked sanitized pilot evidence intake ledger.
- `pilot-session-packet.md`: checked real pilot-session packet and sanitization boundary.
- `pilot-summary-intake.md`: checked sanitized pilot summary intake classifier.
- `pilot-findings.md`: checked pilot findings readback for real-session evidence and current adoption blockers.
- `simulated-agent-pilot.md`: checked simulated agent pilot readback for one user prompt and four generated prompts, counted separately from real pilot evidence.
- `generated-runtime-types-decision.md`: checked generated runtime types decision and JSON fallback guidance.
- `local-usage-trace.md`: checked local-only usage trace read model and aggregate MVP product metrics.
- `prediction-agent-adoption.md`: checked general agent adoption front door, capability manifest, extension points, BYO-model path, and compact fit commands.
- `developer-adoption-surface.md`: checked local MVP developer and agent adoption guide.
- `expansion-readiness-gate.md`: checked post-MVP expansion readiness decision surface.
- `repeating-prediction-setup.md`: checked local-first repeating prediction setup contract and recurrence policy boundary.
- `prediction-campaign-manifest.md`: checked local dry-run campaign manifest and planned-run status boundary.
- `prediction-campaign-runner.md`: checked dry-run terminal campaign runner start boundary.
- `prediction-campaign-forecast-creation.md`: checked ready-run forecast creation handoff boundary.
- `prediction-campaign-forecast-artifact.md`: checked unresolved campaign forecast artifact boundary using the standard lifecycle contracts.
- `prediction-campaign-forecast-write.md`: checked forecast lifecycle write plan and local state mutation boundary.
- `prediction-campaign-resolution-attempt.md`: checked campaign resolver-attempt readback and non-mutation boundary.
- `prediction-campaign-doctor.md`: checked compact campaign doctor readback for health, due, failed, blocked, append-ready, duplicate, and recovery surfaces.
- `prediction-campaign-resume.md`: checked campaign resume readback and recovery boundary.
- `prediction-campaign-evidence-ledger.md`: checked append-ready and append readback boundary for local campaign evidence ledgers.
- `prediction-campaign-calibration-status.md`: checked campaign calibration status and post-calibration continuation readback.
- `prediction-campaign-pre-calibration.md`: optional historical-only campaign pre-calibration boundary.
- `prediction-campaign-method-update-gate.md`: checked campaign method-update gate and non-effectful update boundary.
- `prediction-campaign-method-update-plan.md`: checked campaign method-update approval, command-shape, rollback, and preflight plan.
- `prediction-campaign-method-update-action.md`: checked apply/rollback command boundary for approved local method bindings.
- `prediction-campaign-explain.md`: checked repeating campaign pilot explanation readback.
- `helsinki-traffic-disturbance-pilot-runbook.md`: checked local 100-run Helsinki traffic disturbance pilot operations runbook.
- `helsinki-traffic-pilot-readiness.md`: checked local launch-readiness gate for the 100-run Helsinki pilot.
- `lifecycle-operation-store.md`: checked local SQLite lifecycle operation store and multi-agent operation boundary.
- `internal-api.md`: checked embedded internal API surface and transport boundary.
- `prediction-workspace-registry.md`: checked multi-prediction workspace registry, workspace read-model, configuration-lifecycle, idempotency, lease, resource-control, and isolation readback boundary.
- `background-worker-runtime.md`: checked local worker and sidecar readback boundary for Milestone 116.
- `runtime-security.md`: checked lightweight runtime hardening boundary for Milestone 117.
- `agent-implementation-kit.md`: checked agent implementation kit and starter-template boundary for Milestone 118.
- `postgres-compatibility.md`: checked Postgres compatibility checkpoint for lifecycle storage semantics without runtime or hosted-storage claims.
- `database-source-adapter-runtime.md`: checked approved database source-adapter runtime boundary for one caller-approved fixture path without production database connections, credentials, raw rows, or DB-specific forecast paths.
- `opp-provider-adapter.md`: checked optional OPP provider adapter boundary for request/response mapping, Agent Card discovery, conformance guidance, and future HTTP provider surfaces over authoritative OPE records.
- `persistent-sqlite-policy.md`: checked opt-in persistent SQLite path policy for caller-approved local state files while normal checks keep using ephemeral SQLite.
- `lifecycle-lease-policy.md`: checked lifecycle operation lease policy for strict leases versus idempotency-only guards without lock acquisition in readbacks.
- `runtime-transport-readiness.md`: checked runtime transport gate that keeps local HTTP, queue, hosted service, and OPP HTTP provider behavior deferred.
- `workspace-tenant-isolation.md`: checked tenant-scoped workspace isolation policy for resources, source bindings, queues, credential references, and blocked cross-tenant access.
- `domain-source-field-policy.md`: checked domain/source field policy for required fields, extension containers, and blocked credential/raw/claim fields.
- `credential-reference-policy.md`: checked credential-reference mechanism policy for private API/database source bindings without storing secrets.
- `retention-redaction-policy.md`: checked retention, redaction, tombstone, sanitized projection, and physical-delete exception policy.
- `private-auto-evidence-policy.md`: checked private `data: auto` source-policy overlay without private-source execution.
- `agent-prediction-manual.md`: compact prediction manual for coding agents adding OPE-backed features.
- `forecast-question-discovery.md`: checked question-discovery intake, candidate, and validation readback boundary.
- `domain-config.md`: checked reusable domain configuration record boundary.
- `source-binding.md`: checked concrete source binding setup and pre-forecast safety boundary.
- `storage-adapter.md`: checked storage adapter boundary for ignored JSON compatibility, local SQLite, and Postgres-compatible backends.
- `repeating-prediction-pilot-runbook.md`: checked local pilot workflow for 100-run and open-ended repeating prediction campaigns.
- `private-setup-adapter-chain-runbook.md`: checked private setup adapter-chain runbook boundary.
- `private-setup-adapter-conformance-matrix.md`: checked private setup adapter conformance matrix.
- `private-setup-adapter-conformance-summary.md`: compact private setup adapter conformance summary.
- `private-source-adapters.md`: checked private source adapter capability declarations.
- `private-source-adapter-outcomes.md`: checked private source adapter outcome matrix.
- `private-source-adapter-bridge.md`: checked private source adapter bridge into source-builder, source-handoff, and fixture evidence entrypoints.
- `private-source-kind-selection-examples.md`: checked private source-kind selection examples.
- `private-source-kind-query-matrix.md`: checked private source-kind adapter query matrix.
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
- `mvp-local-runtime.md`: compact local MVP runtime runbook, machine interfaces, smoke checks, and claim boundary.
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
- `domains/weather-transit-delays.md`: selected public beta candidate wedge for weather-conditioned public transport delay forecasts.

Fixtures live under `spec/fixtures/`.
Generated fixture reports live under `spec/fixtures/generated/` and are checked by `python3 scripts/run_checks.py`.
The fixture-only evidence loop reads `spec/fixtures/source/` and writes checked outputs under `spec/fixtures/generated/fixture-loop/`.
The fixture-mode live outcome resolver reads declared live source fixtures and writes checked outputs under `spec/fixtures/generated/live-outcome/`.
The auto-evidence planner, fixture gatherer, and forecast generator read `spec/fixtures/requests/auto-weather-logistics-request.json` and write checked plan/source-set/forecast records under `spec/fixtures/generated/auto-evidence/`. The fixture gatherer rejects non-executable connector policies and binds source-set records to connector registry/result IDs.
The source connector generator writes checked connector registry and result-set records under `spec/fixtures/generated/source-connectors/`.
The live connector readiness generator writes a checked offline readiness record under `spec/fixtures/generated/live-readiness/`; the opt-in `--live` integration probe is not part of normal release checks.
The transit API connector generator writes a checked offline HSL GTFS-RT connector contract under `spec/fixtures/generated/transit-api-connector/`; the opt-in `--live` capture writes ignored local protobuf, CSV, and metadata files under `.ope/live/transit-api/`, plus source-adapter output when delay rows are decoded directly or derived with `--schedule-join`.
The local live capture workspace writes ignored developer-only outputs under `.ope/live/`; those files are validated by local commands but are not generated fixtures or public read records.
The domain setup generator writes checked reference and candidate setup records under `spec/fixtures/generated/domain-setups/`.
The local transit delay prototype reads approved CSV/JSON files under `spec/fixtures/local-source-files/` by default and writes checked forecast, resolution, and scoring records under `spec/fixtures/generated/transit-delay-forecast/`. The transit delay forward-run generator writes a checked forecast-to-resolution summary under `spec/fixtures/generated/transit-delay-forward-run/`; opt-in live phases write ignored local state, weather, forecast, capture, resolution, and scoring artifacts under `.ope/live/transit-forward-run/`. The transit forward-run corpus generator writes a checked index under `spec/fixtures/generated/transit-forward-run-corpus/` with one comparable scored fixture row, six exclusion examples, sample thresholds, and claim boundaries. The transit corpus growth loop writes a checked append-readiness model under `spec/fixtures/generated/transit-corpus-growth/` with comparable candidate, exclusion-ledger, due-run checklist, post-resolution checklist, and threshold progress readbacks. The transit baseline track-record gate writes a checked read model under `spec/fixtures/generated/transit-baseline-track-record-gate/` with Brier score, baseline score, baseline lift, sample sizes, horizon/window coverage, below-threshold calibration status, and explicit campaign-ledger inclusion through `--campaign`. The transit method options generator writes a checked read model under `spec/fixtures/generated/transit-method-options/` with baseline-default selection, evidence-only weather-adjustment comparison, proposed-only richer methods, and anti-leakage boundaries. The transit live evidence promotion generator writes a checked gate and sanitized promoted source set under `spec/fixtures/generated/transit-live-evidence-promotion/`, distinguishing committed fixtures, ignored local live drafts, promoted forecast-time evidence, and resolution-only evidence. The transit forward-run resolver writes a checked offline resolver-agent scan under `spec/fixtures/generated/transit-forward-run-resolver/`; opt-in live scans can inspect ignored local state and `--execute` can run due checked resolver commands. The resolution job registry writes checked agent next-action guidance under `spec/fixtures/generated/resolution-jobs/` without executing resolvers; its campaign fixture adds the checked `forecast-1301` campaign wait state from the campaign manifest, forecast artifact, and write plan, and due campaign scans route to `prediction-campaign resolve`. The resolution scheduler writes checked default and campaign-aware fixture ticks under `spec/fixtures/generated/resolution-scheduler/`; the campaign tick includes wait or resolver-attempt-ready actions without executing campaign resolvers or writing campaign state. Opt-in live watch mode is a foreground terminal loop that appends ignored JSONL logs under `.ope/live/resolution-scheduler/` and never creates hosted or OS scheduler files. The resolution runtime reliability generator writes a checked read model under `spec/fixtures/generated/resolution-runtime-reliability/` with failure taxonomy, retry guidance, provenance classification, and live-capture boundaries.
The source manifest builder reads caller-approved local CSV/JSON fixtures under `spec/fixtures/local-source-files/` and writes checked draft build records, source manifests, and field mappings under `spec/fixtures/generated/source-builder/`; those drafts are not public read surfaces and cannot produce forecasts.
The source adapter output generator writes a checked external-connector handoff under `spec/fixtures/generated/source-adapter-output/`; it embeds a source manifest and field mapping but cannot create forecast or scoring records.
The source adapter intake generator writes checked external adapter output, source-intake report, setup benchmark gate, setup method decision, and routing matrix fixtures under `spec/fixtures/generated/source-adapter-intake/`; it blocks unsafe handoffs before intake and does not execute connector code.
The source-quality mapping-confidence generator writes a checked read model under `spec/fixtures/generated/source-quality-mapping-confidence/`; it joins builder, adapter-intake, source-intake, and setup-method records into compact next-action guidance without source execution or artifact creation.
The local source runtime generator writes a checked approved local-folder runtime under `spec/fixtures/generated/local-source-runtime/`; it requires caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics, routes the accepted case to the existing source-handoff forecast card, and keeps blocked cases non-generating.
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
The private setup request generator writes checked request routing examples under `spec/fixtures/generated/private-setup-requests/`.
The private setup first-action generator writes checked non-executing dispatcher examples under `spec/fixtures/generated/private-setup-actions/`.
The private setup first-action runbook generator writes checked guidance under `spec/fixtures/generated/private-setup-actions/`.
The private setup agent bundle generator writes checked read-only guidance joins under `spec/fixtures/generated/private-setup-agent-bundles/`.
The private setup orchestrator generator writes a checked local summary under `spec/fixtures/generated/private-setup-orchestrator/`, joining request, first-action, source-intake, method-gate, explicit forecast-execution, and normal readback outcomes without executing commands.
The agent pilot validation generator writes a checked local protocol under `spec/fixtures/generated/agent-pilot-validation/` for 3-5 sessions, task scenarios, feedback dimensions, comprehension rubrics, and sanitized synthetic example summaries.
The agent guidance generator writes a checked guidance loop under `spec/fixtures/generated/agent-guidance/`, covering accepted, clarification, blocked, rejected, and response-too-large cases plus the Helsinki narrowing flow and instruction pack.
The pilot evidence ledger generator writes checked sanitized intake examples under `spec/fixtures/generated/pilot-evidence/`, blocking raw transcripts and private data while keeping accepted real-session evidence at zero until actual sanitized pilots are recorded.
The pilot session packet generator writes a checked collection kit under `spec/fixtures/generated/pilot-session-packet/`, providing task cards including repeating prediction campaign explanation, sanitization checks, a ledger-ready template, and stop conditions without running sessions or writing ledger rows.
The pilot summary intake generator writes checked classification examples under `spec/fixtures/generated/pilot-summary-intake/`, marking sanitized summaries as ledger-ready, redaction-needed, or blocked without writing ledger rows or counting real sessions.
The simulated agent pilot generator writes a checked user-authorized simulation under `spec/fixtures/generated/simulated-agent-pilot/`, covering one user prompt and four generated prompts across accepted, clarification, blocked, rejected, and response-too-large prediction-feature setup outcomes with approximate token counts and deterministic elapsed-time estimates.
The local usage trace generator writes a checked synthetic trace under `spec/fixtures/generated/local-usage-trace/` with local MVP event rows, campaign lifecycle events, response-size and elapsed-time fields, aggregate product metrics, and privacy boundaries.
The prediction-agent adoption generator writes a checked general adoption surface under `spec/fixtures/generated/prediction-agent-adoption/` and the root `ope.capabilities.json` manifest, exposing compact fit guidance, helps-with and does-not-provide lists, extension points, bring-your-own-model guidance, and a first-five-minutes adoption evaluation without adding runtime or quality claims.
The developer adoption surface generator writes a checked onboarding guide under `spec/fixtures/generated/developer-adoption/` with quickstart steps, one complete local setup scenario, recurring campaign explain guidance, CLI/agent-call/MCP stdio integration notes, release notes, and a deferred generated-types decision.
The expansion readiness generator writes a checked post-MVP decision gate under `spec/fixtures/generated/expansion-readiness/`; it keeps hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types blocked or deferred until real pilot, recurring setup, corpus, and adoption evidence justify them.
The repeating prediction setup generator writes a checked non-executing recurrence contract under `spec/fixtures/generated/repeating-prediction-setup/`, covering fixed-count, until-date, open-ended, interval, selected weekday/window, calibration-threshold, and post-calibration restart policies before any campaign manifest or runner exists.
The prediction campaign manifest generator writes a checked dry-run manifest under `spec/fixtures/generated/prediction-campaign-manifest/`, expanding the repeating setup into unique planned run IDs, duplicate keys, status readbacks, and ignored local-state path policy without creating artifacts or writing live campaign state.
The prediction campaign runner generator writes a checked dry-run terminal runner readback under `spec/fixtures/generated/prediction-campaign-runner/`, exposing `prediction-campaign start` command semantics, recurrence flags, normalized campaign creation input from flags or setup JSON, a forecast scheduling plan, bounded foreground ticks, runner-clock `--now` scheduling, output modes, non-execution decisions, and a `missed_forecast_close` policy that excludes missed windows from comparable evidence. `prediction-campaign start --now ... --write-local` performs explicit local creation for the next due run under ignored campaign state.
The prediction campaign forecast-creation generator writes a checked dry-run handoff under `spec/fixtures/generated/prediction-campaign-forecast-creation/`, binding the ready runner decision to planned question, forecast, card, and bundle IDs without creating artifacts or writing campaign state.
The prediction campaign forecast artifact generator writes checked lifecycle records under `spec/fixtures/generated/prediction-campaign-forecast-artifact/`, materializing `forecast-1301` as an unresolved baseline-only artifact without live fetches, resolver execution, scoring, or campaign-state writes.
The prediction campaign forecast write generator writes a checked non-mutating write plan under `spec/fixtures/generated/prediction-campaign-forecast-write/`, binding lifecycle records to ignored `.ope/live` target paths and required guards. `prediction-campaign forecast-write --write-local` executes that guarded copy idempotently and refuses mismatched overwrites.
The prediction campaign resolution-attempt generator writes a checked non-mutating readback under `spec/fixtures/generated/prediction-campaign-resolution-attempt/`, recording due/not-due status, explicit resolver requests, terminal/excluded/duplicate safety cases, failure category, retryability, source-fetch metadata, sanitized diagnostics, and duplicate-safe no-resolution/no-scoring boundaries. `prediction-campaign start --now ... --execute-resolvers` calls this checked readback for due campaign runs.
The prediction campaign doctor generator writes a checked compact readback under `spec/fixtures/generated/prediction-campaign-doctor/`, joining campaign health, due/waiting/failed/blocked/append-ready queues, duplicate protection, and recovery posture without reading or writing ignored campaign state.
The prediction campaign resume generator writes a checked non-mutating recovery readback under `spec/fixtures/generated/prediction-campaign-resume/`, joining the campaign manifest, write plan, open forecast, and resolution queue without reading or writing ignored live state during normal checks. `prediction-campaign resume --resume-case interrupted_after_forecast_write --view state` exposes the interrupted-state readback, and `--from-local` explicitly reads ignored local campaign state without writing or overwriting prior evidence.
The prediction campaign evidence ledger generator writes a checked append-only readback under `spec/fixtures/generated/prediction-campaign-evidence-ledger/`, separating comparable rows from excluded audit rows and checking forecast timing, source-policy, no-leakage, resolution, score, coverage, scope, and duplicate row keys. `prediction-campaign append --write-local` is explicit and writes only to ignored local ledger state.
The prediction campaign calibration-status generator writes a checked readback under `spec/fixtures/generated/prediction-campaign-calibration-status/`, covering below-threshold, threshold-met, too-many-exclusions, and post-calibration restart cases without tuning models or mutating campaign cycles.
The prediction campaign pre-calibration generator writes a checked readback under `spec/fixtures/generated/prediction-campaign-pre-calibration/`, using historical transit delay rows to prepare an optional baseline probability binding before pilot launch without live fetches or method changes.

The prediction workspace registry generator writes a checked readback under `spec/fixtures/generated/prediction-workspace-registry/`, showing multiple prediction definitions with stable IDs, compact workspace read models, audit-backed configuration operation definitions, per-prediction idempotency/lease controls, resource limits, and cross-prediction isolation checks.
The background worker runtime generator writes a checked readback under `spec/fixtures/generated/background-worker-runtime/`, defining local worker commands, workspace read-model polling, one-tick equivalence to internal API `run_tick`, a bounded dry-run loop over the shared internal API, an approved ephemeral SQLite commit path with operation receipt/idempotency/lease write and release readbacks, lifecycle-backed worker control-state writes for pause/resume/drain/shutdown plus health readback, durable local sidecar activation semantics, operation guards, cancellation/backoff policy, resource limits, blocked operation readbacks, and the non-networked sidecar boundary without starting a daemon or writing persistent state.
The runtime security generator writes a checked hardening readback under `spec/fixtures/generated/runtime-security/`, declaring the stdlib-only runtime dependency budget, module and adapter boundaries, path/symlink/database guards, input and response byte limits, credential-reference-only policy, threat-model notes, blocked examples, and local execution boundary without starting hidden services or fetching live sources.
The agent implementation kit generator writes a checked readback under `spec/fixtures/generated/agent-implementation-kit/`, exposing the quickstart front door, compact prediction manual, question-discovery intake contract, forecastable/needs-clarification/blocked/rejected candidate readbacks, mechanical validation reports, first-run source paths, adapter guidance for in-process/CLI/agent-call/local MCP/future transports, starter-template descriptors, and disallowed behavior boundaries without creating forecast artifacts. Agents should use `prediction-agent-adoption` first for general fit, then the implementation kit when they are ready to wire OPE into a host project.
The Postgres compatibility generator writes a checked readback under `spec/fixtures/generated/postgres-compatibility/`, mapping the eight lifecycle operation-store tables, dialect-neutral adapter semantics, all fifteen lifecycle runtime scenarios, SQLite-only assumption guards, and migration/execution boundaries without connecting to Postgres or running migrations.
The persistent SQLite policy generator writes a checked readback under `spec/fixtures/generated/persistent-sqlite-policy/`, covering caller approval, `.ope/state` allowlisting, traversal and symlink blockers, explicit JSON-state migration with backup and lock rules, and the boundary that normal checks create no persistent database.
The lifecycle lease policy generator writes a checked readback under `spec/fixtures/generated/lifecycle-lease-policy/`, classifying fourteen lifecycle operations into nine strict-lease operations and five idempotency-only operations with conflict cases and non-mutating readback boundaries.
The runtime transport readiness generator writes a checked readback under `spec/fixtures/generated/runtime-transport-readiness/`, keeping in-process, CLI, agent-call, and local MCP surfaces current while local HTTP, queue, hosted service, and OPP HTTP provider surfaces remain deferred behind explicit readiness gates.
The workspace tenant isolation generator writes a checked readback under `spec/fixtures/generated/workspace-tenant-isolation/`, layering tenant/workspace scope over the prediction workspace registry with resource controls, queue policies, source-binding blockers, credential-reference ownership, blocked cross-tenant access cases, and non-mutating runtime boundaries.
The domain/source field policy generator writes a checked readback under `spec/fixtures/generated/domain-source-field-policy/`, classifying required domain fields, required source-binding fields, domain-specific extension containers, source-kind credential-reference rules, blocked raw/credential/claim fields, decision cases, and non-mutating execution boundaries.
The credential-reference policy generator writes a checked readback under `spec/fixtures/generated/credential-reference-policy/`, defining opaque caller-owned references, required tenant/workspace/source/adapter scope, lifecycle states, consumer rules, accepted and blocked cases, and boundaries that normal checks do not resolve or store secrets.
The retention/redaction policy generator writes a checked readback under `spec/fixtures/generated/retention-redaction-policy/`, defining retention classes, archive tombstones, redaction receipts, sanitized projection rebuilds, physical-delete exception gates, decision cases, and boundaries that normal checks do not delete or mutate records.
The private auto-evidence policy generator writes a checked readback under `spec/fixtures/generated/private-auto-evidence-policy/`, defining private `data: auto` source kinds, policy gates, decision cases, readbacks, and boundaries that normal checks do not read private sources, resolve secrets, execute raw SQL, use broad web search, or retain raw private payloads.
The domain config generator writes checked reusable domain configs under `spec/fixtures/generated/domain-configs/` for weather-transit delays and a candidate seaport berth-availability domain.
The source binding generator writes checked setup cases under `spec/fixtures/generated/source-bindings/`, covering accepted, partial, rejected, and blocked bindings with mapping-confidence, source-quality, leakage, freshness, privacy, and outcome-availability gates before forecast generation.
The prediction campaign method-update gate generator writes a checked readback under `spec/fixtures/generated/prediction-campaign-method-update-gate/`, covering below-threshold, approval-needed, approved-plan-ready, and regression-risk cases without changing probabilities, forecast methods, method weights, method registries, or campaign state.
The prediction campaign method-update plan generator writes a checked readback under `spec/fixtures/generated/prediction-campaign-method-update-plan/`, covering gate-blocked, regression-risk, approval-missing, rollback-missing, and plan-ready cases before any explicit effectful command runs.
The prediction campaign method-update action generator writes a checked readback under `spec/fixtures/generated/prediction-campaign-method-update-action/`, covering default blocked apply semantics plus explicit apply/rollback command readiness and local-only method-binding writes behind `--write-local`.
The prediction campaign explain generator writes a checked pilot readback under `spec/fixtures/generated/prediction-campaign-explain/`, joining campaign plan, status, health, append-readiness, calibration threshold, sanitized error envelopes, pilot task card, and claim boundary without creating artifacts or writing campaign state.
The Helsinki traffic pilot runbook generator writes a checked operations readback under `spec/fixtures/generated/helsinki-traffic-pilot-runbook/`, binding a 3-run smoke path, 100-run materialization command sequence, operator status commands, success criteria, abort criteria, and the baseline-first method boundary.
The Helsinki traffic pilot readiness generator writes a checked launch gate under `spec/fixtures/generated/helsinki-traffic-pilot-readiness/`, confirming checked prerequisites, manual source/clock/workspace prerequisites, launch commands, blocked actions, and the baseline-first method boundary without starting the pilot.
The private setup adapter-chain runbook generator writes checked non-executing operation-sequence guidance under `spec/fixtures/generated/private-setup-adapter-chain/`.
The private setup adapter conformance generator writes checked source-builder, source-handoff, method-gate, forecast-execution, and generated forecast readback examples under `spec/fixtures/generated/private-setup-adapter-conformance/` without executing adapter calls.
The private setup adapter conformance summary generator writes a compact read surface under `spec/fixtures/generated/private-setup-adapter-conformance/` without embedding full envelopes.
The private source adapter capability generator writes checked non-executing adapter declarations under `spec/fixtures/generated/private-source-adapters/`.
The private source adapter outcome generator writes a checked next-action matrix under `spec/fixtures/generated/private-source-adapters/`.
The private source adapter bridge generator writes a checked intake bridge under `spec/fixtures/generated/private-source-adapters/`.
The private source-kind selection generator writes checked next-path examples under `spec/fixtures/generated/private-source-kind-selection/`. The same examples are also exposed through a read-only `private_source_kind_selection` agent-envelope operation, and the query matrix records checked full-list, selected, and unsupported adapter responses for conformance.
The recalculation generator writes checked trigger, run, evidence, artifact, and append-history records under `spec/fixtures/generated/recalculation/`.
The auto-evidence resolver reads those generated forecast records and writes checked resolution outputs under `spec/fixtures/generated/auto-evidence-resolution/`.
The historical-only baseline forecast reads `spec/fixtures/requests/historical-weather-logistics-request.json` and writes checked no-API forecast records under `spec/fixtures/generated/historical-baseline/`.
The method registry fixture lives under `spec/fixtures/methods/` and is checked against clean comparable benchmark runs.
The method-comparison generator writes checked baseline comparison records under `spec/fixtures/generated/method-comparison/`.
The method-selection generator writes a checked selection explanation under `spec/fixtures/generated/method-selection/`.
The forecast-run generator writes a checked agent-facing run summary under `spec/fixtures/generated/forecast-run/`.
The forecast-run intake matrix generator writes checked accepted, rejected, blocked, canceled, unsupported-fixture-path, and response-too-large examples under `spec/fixtures/generated/forecast-run/`.
The agent forecast runbook generator writes checked caller workflow examples under `spec/fixtures/generated/forecast-run/`.
The agent-adapter fixture generator writes checked transport-neutral envelope examples, including evidence-trace, private setup bundle, private setup adapter-chain runbook, private source adapter guidance, private setup source-builder, private setup source-handoff, private setup method-gate, private setup forecast-execution, generated private setup forecast readback operations, and campaign plan/status/health/append-readiness/calibration-status operations, under `spec/fixtures/generated/agent-adapter/`.
The agent-adapter protocol-map generator writes a checked MCP stdio and future protocol plan under `spec/fixtures/generated/agent-adapter/`.
The local forecast pipeline reads an accepted request fixture and writes checked outputs under `spec/fixtures/generated/pipeline/`.
The pipeline resolver reads those generated forecast records and writes checked resolution outputs under `spec/fixtures/generated/pipeline-resolution/`.
The public read index is `spec/fixtures/generated/record-index.generated.json`.
Schema-bound fixtures are validated by `python3 scripts/check_schema_contracts.py`.

These schemas describe OPE records. The repository also includes local Python scripts for fixture generation, reusable contract validation, schema-bound read surfaces, read-only forecast card, evidence trace, and lifecycle bundle access, transport-neutral agent envelope examples, a local single-operation agent dispatcher, a local MCP stdio scaffold over that dispatcher, a local fixture-safe forecast-run orchestrator, intake matrix, and runbook, a checked mapping for MCP plus future HTTP and queue adapters, request intake, controlled live-source fixture mode, auto-evidence dry-run planning, fixture gathering, source connector boundary checks, live connector readiness and ignored live-capture workspace checks, an opt-in HSL GTFS-RT transit API connector with static GTFS schedule join, a checked transit-delay forward-run workflow with opt-in local live forecast and resolve phases, a checked transit forward-run corpus index with exclusions and thresholds, a checked transit corpus growth loop with append-readiness, exclusion-ledger, checklist, and threshold-progress readbacks, a checked transit baseline track-record and calibration gate, checked transit MVP method options, a checked transit live evidence promotion gate with one sanitized promoted source set, a checked local resolver-agent scan and explicit execution command for due transit forward runs, a checked resolution job registry for agent next actions including a campaign-aware wait-state readback, a checked foreground terminal resolution scheduler for local polling and optional due-job execution, a checked resolution runtime reliability read model for sanitized failure and provenance guidance, domain setup inspection, local source manifest building for small approved CSV/JSON files, external source adapter output handoffs and intake gates for agent-built connectors, source-quality and mapping-confidence readbacks, an approved local-folder source runtime, a checked developer adoption surface, source-builder to source-intake handoffs, source-handoff method gates, explicit source-handoff forecast execution and resolution, a checked source-handoff setup runbook, a domain-agnostic private setup workflow contract, private setup request routing examples, private setup first-action dispatcher fixtures and runbook guidance, private setup agent bundles and local orchestrator summaries, read-only adapter envelopes for those bundles, private setup adapter-chain runbook envelopes, private source adapter guidance envelopes, private source-kind selection examples and their read-only adapter envelope, private setup source-builder adapter envelopes for caller-approved local CSV/JSON inspection, private setup source-handoff adapter envelopes for checked handoff next actions, private setup method-gate adapter envelopes for setup benchmark and method-decision guidance, private setup forecast-execution adapter envelopes for checked generated and blocked setup runs, private setup forecast readback envelopes through normal read operations, private source adapter capability declarations, outcome matrix, and intake bridge, source intake reports, setup benchmark gates, setup method decisions, setup-aware deterministic and baseline forecast execution, append-only recalculation history, forecast generation and resolution, historical-only baseline forecasting, method registry checks, fixture-mode live outcome resolution, a local deterministic forecast pipeline scaffold and resolver, a generated release manifest with an MVP local runtime section, a compact MVP runbook, a CI release gate, and a small local CLI wrapper. It does not yet expose a network API, SDK, hosted service, generated language-specific runtime types, production auto-evidence fetching, production agent adapter runtime beyond local envelopes, production forecast use of live connector results outside explicit local promotion gates, arbitrary private source parsing beyond the checked local builder, approved local-folder runtime, transit connector, source-adapter-output boundary, and source-adapter-intake boundary, source-quality-driven source execution or artifact creation, generic manual upload, private API, or database connector runtimes, private setup request execution, private setup first-action execution, private setup first-action runbook execution, private setup agent bundle execution, private setup orchestrator execution, private setup adapter-runbook execution, private source adapter guidance execution, private source-kind selection execution, private setup source-builder forecast execution, private setup source-handoff forecast execution, private setup method-gate forecast execution, private setup forecast-execution from blocked cases, private setup forecast-execution resolution or scoring, private setup forecast readback through a private read API, or private source adapter bridge execution beyond routing guidance, public transport non-baseline method selection, trained public transport ML, transit ensembles, hosted live scheduler/watch runtime, OS scheduler installation, campaign resolver execution from resolution jobs, canonical corpus mutation from the checked growth loop, below-threshold transit calibration summaries, post-close or resolution-only promotion into forecast evidence, or live calibration claim.
