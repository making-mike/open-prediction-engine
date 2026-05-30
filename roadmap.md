# Open Prediction Engine Roadmap

Last updated: 2026-05-28

## Purpose

This roadmap turns the OPE whitepaper and product context into an execution plan.

The project should advance in this order:

1. Define machine-readable contracts.
2. Prove scoring and resolution on fixtures.
3. Choose one narrow reference forecast domain.
4. Build one complete evidence loop for that reference domain.
5. Add benchmark and anti-leakage controls.
6. Expose agent-facing access only after the core records are stable.
7. Add domain-agnostic private engine setup contracts.
8. Add source manifests, field mappings, method policies, and recalculation history.
9. Add policy-bound auto-evidence gathering for `data: auto`.
10. Add local repeating prediction setup so agents can start, resume, resolve, score, and measure forecast campaigns from a terminal.
11. Add stronger forecasting methods only after baseline, benchmark, track-record, and calibration controls exist.

The roadmap is intentionally contract-first, agent-native, and domain-agnostic. OPE should not start as a generic LLM forecast endpoint or an unbounded web crawler. Weather-logistics is the reference wedge used to prove the standard, not the product's long-term boundary.

## Current Status

Done:

- Standalone OPE positioning in `AGENTS.md`.
- Public narrative in `whitepaper.md`.
- Research-backed whitepaper evaluation in `research/whitepaper-evaluation.md`.
- Agent baseline and decision log under `.agents/`.
- Compact product context in `PRODUCT.md`.
- Decision to treat question governance and forecast histories as core contracts.
- Weather-linked logistics selected as the first domain wedge.
- Fixture-only evidence loop for the selected wedge.
- Ambiguous and annulled fixture-loop cases excluded from scoring.
- First benchmark anti-leakage fixtures and checker.
- Human-facing README.
- Allow-listed Open-Meteo weather connector in fixture-checked mode.
- Provisional live weather baseline and evidence bundle builders.
- Read-only local record access for artifacts and track records.
- Validation-only controlled forecast request intake.
- Release-readiness wrapper and hardening guardrails.
- Python standard-library runtime and schema-bound fixture validation.
- Local CLI wrapper for common workflows.
- Fixture-mode live outcome resolution, scoring, and provisional claim gating.
- Reusable local contract validator and single-record validation command.
- Local deterministic forecast pipeline scaffold for accepted fixture requests.
- Fixture-mode resolution and scoring for request-bound pipeline forecasts.
- Read-only forecast lifecycle bundles assembled from bound generated records.
- Compact claim-safe forecast cards for agent-facing reads.
- Schema-bound forecast cards and public record index contracts.
- Generated release manifest with local surface and claim-boundary summary.
- CI release gate for local fixture-ready checks.
- Initial `data: auto` request, source-policy contract, evidence-gathering plan contract, evidence-source-set contract, dry-run planner, fixture-replay source gatherer, request-bound auto-evidence forecast outputs, and fixture-mode auto-evidence resolution/scoring.
- Auto-evidence guardrails for source injection, prompt injection, stale sources, unavailable sources, conflicting sources, and gated live-fetch mode.
- First weather-logistics method registry with clean baseline comparison and expanded model-assisted leakage fixtures.
- Method-comparison report covering every non-baseline method.
- Method-selection explanation that falls back to the baseline when comparable method evidence is insufficient.
- Transport-neutral agent envelope contract with generated local examples for request validation, evidence planning, forecast card reads, lifecycle bundle reads, resolution status, scoring summary, and sanitized errors.
- Local single-operation agent adapter dispatcher exposed as `python3 scripts/ope.py agent-call`.
- Checked mapping from the local agent dispatcher to the local MCP stdio scaffold plus future HTTP and queue adapters.
- Local MCP stdio scaffold exposed as `python3 scripts/ope.py mcp-stdio` with eleven checked agent tools returning OPE envelopes.
- Local forecast-run orchestrator exposed as `python3 scripts/ope.py forecast-run` and MCP tool `ope_forecast_run`.
- Checked forecast-run intake matrix and agent runbook exposed as `python3 scripts/ope.py forecast-run-matrix` and `python3 scripts/ope.py forecast-runbook`.
- Checked source connector registry and result set exposed as `python3 scripts/ope.py source-connectors`.
- Evidence plans now bind to connector registry/result-set IDs and explain unregistered, unsupported, and resolution-only connectors before gathering.
- The auto-evidence gatherer now rejects non-executable connector policies and binds source-set records to connector registry/result entries.
- Read-only evidence traces now link forecasts to source policy, evidence plan, source set, connector registry, connector results, and gathered source records.
- Historical-only baseline forecasts now run without API evidence, live fetches, or auto-evidence connectors, returning a baseline-equal forecast for agents that provide or restrict OPE to historical data.
- Live connector readiness now separates normal fixture replay, explicit integration live fetch, and future hosted live fetch for the Open-Meteo connector without adding network access to release checks.
- Product context now frames OPE as a domain-agnostic package and standard for agents setting up private prediction engines from connected source data.
- Domain setup contracts now describe a fixture-ready weather-logistics reference setup and a candidate seaport berth-availability private setup with maturity labels and claim boundaries.
- Source manifest and field mapping intake reports now classify bounded data as accepted, accepted-partial, needs-confirmation, or rejected before any forecast is produced.
- Local source manifest builder now inspects small caller-approved CSV/JSON files, emits draft source manifests and field mappings, rejects secrets, oversized files, unsupported formats, and leakage indicators, and keeps drafts out of public read surfaces.
- Source-builder to source-intake handoffs now classify unconfirmed, confirmed, insufficient-sample, and rejected builder drafts into deterministic next actions for agents.
- Setup-aware method decisions now explain benchmark-gated deterministic selection, baseline fallback, missing forecast-time evidence, unconfirmed mappings, rejected intake, and benchmark boundaries before forecast artifacts are created.
- Setup-aware forecast execution now creates deterministic or baseline forecast artifacts, evidence packets, histories, cards, and bundles from accepted setup intake while keeping blocked setup outcomes non-generating.
- Setup benchmark gates now let accepted setup intake use a deterministic statistical fixture method only when source roles, benchmark bindings, anti-leakage controls, positive lift, and execution sample thresholds pass, while quality claims remain blocked.
- Recalculation history now appends updated forecast states when new pre-close evidence arrives and rejects post-outcome resolution evidence as forecast input.
- Ignored local live capture workspace now saves sanitized opt-in connector result sets and converts successful captures into local source-set drafts without changing release artifacts.
- Builder handoffs now flow into setup benchmark and method decisions through a non-generating source-handoff method gate.
- Confirmed builder handoffs can now explicitly generate `forecast-1102`; blocked handoff cases remain non-generating.
- Source-handoff forecasts can now resolve and score `forecast-1102` from the declared outcome source while keeping blocked handoff cases non-scored and quality claims sample-size-blocked.
- A checked source-handoff setup runbook now gives agents one local workflow from source inspection to resolved forecast card and track-record boundary.
- A domain-agnostic private setup workflow contract now separates setup phases and source-kind boundaries before future private API/database runtimes exist.
- A checked private source adapter intake bridge now routes adapter outcomes to source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop actions without executing private sources or creating forecast records.
- A checked private setup request contract now starts setup routing from one agent-facing setup-intent record without reading private data or creating forecast records.
- A checked private setup first-action dispatcher now accepts one generated request ID or request-shaped JSON object and returns the first safe non-executing action.
- A checked private setup first-action runbook now maps dispatcher statuses to next safe caller-visible steps while keeping blocked sources out of source intake.
- Checked private setup agent bundles now join request, first-action, and runbook guidance into one read-only agent response.
- Checked private setup source-handoff adapter envelopes now expose mapping confirmation, source-intake binding, and method-gate readiness through the same agent adapter surface without creating forecast or score records.
- Checked private setup method-gate adapter envelopes now expose setup benchmark and method-decision guidance through the same agent adapter surface without creating forecast or score records.
- Checked private setup forecast-execution adapter envelopes now create forecast artifacts only for the confirmed checked handoff and keep blocked cases non-generating.
- Generated private setup forecast readback envelopes now read `forecast-1102` through normal card, bundle, resolution, and scoring adapter operations.
- Compact adapter conformance summaries now declare and enforce byte-size budgets, keep full matrices opt-in, and return sanitized `response_too_large` envelopes for undersized `maxBytes` reads.
- Resolution job and scheduler status readbacks now expose read-only agent adapter and MCP surfaces, including sanitized error-envelope examples for missing workspaces, unreadable state files, malformed scheduler logs, and oversized readbacks.
- Weather-conditioned public transport delays selected as the public beta candidate wedge and documented in `spec/domains/weather-transit-delays.md`.
- Local weather-transit-delay custom-file prototype now emits schema-bound forecast, resolution, and scoring records through `python3 scripts/ope.py transit-delay-forecast`.
- Source adapter output contract now lets external agent-built connectors hand OPE a sanitized source manifest, field mapping, provenance summary, and intake boundary without living in core or creating forecast records.
- Source adapter intake now validates external adapter outputs, routes accepted handoffs through source intake and method gates, and blocks unsafe connector outputs before intake through `python3 scripts/ope.py source-adapter-intake`.
- Source-quality and mapping-confidence readbacks now summarize freshness, coverage, role fit, entity scope, leakage risk, missingness, outcome availability, and mapping confidence through `python3 scripts/ope.py source-quality`.
- Local private setup orchestrator summaries now join setup request, first-action, source intake, method gate, explicit forecast execution, and normal readback outcomes for approved local-file and accepted source-adapter cases through `python3 scripts/ope.py private-setup-orchestrator`.
- The release manifest now declares the local MVP runtime surface, CLI/agent-call/MCP machine interfaces, smoke checks, blocked-path examples, and non-goal claim review, with a compact runbook in `spec/mvp-local-runtime.md`.
- Agent pilot validation now has a checked local pack for 3-5 agent/developer sessions, task scenarios, feedback dimensions, comprehension rubrics, and sanitized synthetic example summaries through `python3 scripts/ope.py agent-pilot-validation`.
- Local usage trace readbacks now expose checked synthetic CLI, agent-call, MCP, blocked-path, release-smoke, and pilot-validation events with aggregate product metrics through `python3 scripts/ope.py local-usage-trace`.
- Opt-in HSL GTFS-RT transit API connector now captures TripUpdates, derives delay rows through a static GTFS schedule join, and writes source-adapter output through `python3 scripts/ope.py transit-api-connector --schedule-join`.
- Weather-transit-delay forward-run workflow now records a pre-window forecast, preserves run state, resolves from declared transit outcome rows, scores against baseline, and exposes explicit local live forecast/resolve phases through `python3 scripts/ope.py transit-delay-forward-run`.
- Weather-transit-delay resolver-agent command now scans saved forward-run states, classifies due/not-due/already-resolved runs, and can explicitly execute the checked resolver command through `python3 scripts/ope.py resolve-due-forward-runs`.
- Resolution job registry now gives agents read-only next-action guidance for pending, due, already-resolved, and invalid resolution states through `python3 scripts/ope.py resolution-jobs`.
- Foreground terminal resolution scheduler now lets agents poll resolution jobs and optionally execute due checked resolvers locally through `python3 scripts/ope.py resolution-scheduler`, without Trigger.dev, cron, `launchd`, or hosted workers.
- Resolution runtime reliability now has a checked failure taxonomy, retry/next-action guidance, provenance ledger, and live-capture boundary through `python3 scripts/ope.py resolution-runtime-reliability`.
- Public transport forward-run corpus now reports one comparable scored transit run, six exclusion examples, sample thresholds, and claim boundaries through `python3 scripts/ope.py transit-forward-run-corpus`.
- Public transport corpus growth now reports append-ready candidates, exclusion-ledger rows, due-run and post-resolution checklists, and threshold progress through `python3 scripts/ope.py transit-corpus-growth`.
- Public transport baseline track-record gate now reports current Brier, baseline, lift, sample-size, and horizon/window coverage while blocking below-threshold calibration through `python3 scripts/ope.py transit-track-record-gate`.
- Public transport method options now keep baseline-only execution as the default, record transparent weather adjustment as evidence-only, and keep richer methods proposed-only through `python3 scripts/ope.py transit-method-options`.
- Policy-bound transit live evidence promotion now distinguishes committed fixtures, ignored live drafts, promoted forecast-time evidence, and resolution-only captures through `python3 scripts/ope.py transit-live-evidence-promotion`.
- One narrow approved local-folder source runtime now requires caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics before binding accepted files to `forecast-1102` through `python3 scripts/ope.py local-source-runtime`.
- Developer adoption surface now exposes a checked quickstart, complete local setup scenario, CLI/agent-call/MCP integration notes, release-note boundaries, and deferred generated-types decision through `python3 scripts/ope.py developer-adoption`.
- Pilot evidence ledger now exposes checked sanitized intake examples, raw/private-data blockers, claim-confusion signals, and zero real sessions recorded through `python3 scripts/ope.py pilot-evidence`.
- Pilot session packet now exposes checked real-session task cards, sanitization review, ledger-ready summary shape, and stop conditions through `python3 scripts/ope.py pilot-session-packet`.
- Pilot summary intake now classifies sanitized summary examples as ledger-ready, redaction-needed, or blocked through `python3 scripts/ope.py pilot-summary-intake`.
- Expansion readiness now exposes a checked post-MVP gate over hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types through `python3 scripts/ope.py expansion-readiness`.
- Repeating prediction setup now exposes a checked non-executing recurrence contract with finite, until-date, open-ended, interval, weekday/window, calibration-threshold, and post-calibration restart examples through `python3 scripts/ope.py repeating-prediction-setup`.
- Prediction campaign manifests now expose a checked dry-run campaign plan with unique campaign, cycle, run, question, forecast, resolution, and scoring IDs, duplicate keys, ignored local-state path policy, and status readbacks through `python3 scripts/ope.py prediction-campaign plan` and `python3 scripts/ope.py prediction-campaign status`.
- Prediction campaign runner readbacks now expose `python3 scripts/ope.py prediction-campaign start` command semantics, recurrence flags, normalized campaign creation from flags or setup JSON, output modes, dry-run run decisions, a checked missed-run policy, and an explicit guarded `--write-local` creation tick for the ready run.
- Prediction campaign forecast-creation handoffs now bind a ready runner decision to planned question, forecast, card, and bundle IDs through `python3 scripts/ope.py prediction-campaign forecast-create`, without creating artifacts or writing campaign state.
- Prediction campaign forecast artifacts now materialize `forecast-1301` as an unresolved baseline-only checked fixture through `python3 scripts/ope.py prediction-campaign forecast-artifact`, using the standard question, evidence, artifact, and history contracts without live fetches, resolver execution, scoring, or campaign-state writes.
- Prediction campaign forecast-write plans now bind the checked `forecast-1301` lifecycle records to ignored `.ope/live` target paths and required guards through `python3 scripts/ope.py prediction-campaign forecast-write`; explicit `--write-local` copies those records and minimal campaign/run state idempotently while normal checks stay non-mutating.
- Prediction campaign resume readbacks now join the checked campaign manifest, forecast-write plan, open forecast, and campaign resolution queue through `python3 scripts/ope.py prediction-campaign resume`, without reading or writing ignored live state.
- Resolution job registries now have a campaign-aware readback through `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001`, adding the checked `forecast-1301` wait state without executing campaign resolvers or mutating campaign state.
- Resolution scheduler readbacks now have a campaign-aware dry-run tick through `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001`, adding the checked `forecast-1301` wait action without executing campaign resolvers or writing campaign state.

Not started:

- Arbitrary private API/database parsing beyond checked setup, local source-builder fixtures, and the approved local-folder runtime.
- Additional setup-aware method classes beyond the current deterministic fixture path.
- Repeated public transport delay forward runs across enough comparable windows for calibration evidence.
- Effectful agent-facing repeating prediction runner that schedules future forecasts automatically beyond the current explicit one-tick checked forecast creation.
- Local campaign runner execution for finite count, until-date, open-ended, threshold-targeted, and post-calibration restart policies.
- Append-only local corpus mutation from resolved live campaign runs into a calibration evidence ledger.
- Runtime forecast execution that consumes newly provided ignored local live drafts beyond the checked promotion fixture.
- Hosted watch or scheduler runtime beyond the local foreground scheduler.
- OS scheduler installation.
- Production hosted, HTTP, or queue agent adapter runtime.
- Hosted service runtime and network API.
- Production forecast use of live connector results.
- Generated language-specific runtime types remain deferred until pilot/adoption evidence shows they reduce setup friction.

In progress:

- Milestone 93 terminal campaign runner: explicit one-tick local forecast creation, normalized flag/setup-JSON campaign input, and the missed-run skip policy exist; forecast scheduling across future recurrence windows remains in progress.

Next:

1. Extend the current explicit `prediction-campaign start --write-local` creation tick into a foreground runner that can schedule future forecasts, wait for due resolution, score outcomes, and report progress toward track-record and calibration thresholds.
2. Run real agent/developer pilot sessions against that campaign flow using the checked pilot session packet, classify summaries through pilot summary intake, and record sanitized accepted summaries through the pilot evidence ledger before hosted or broad runtime work.
3. Continue public transit forward-run corpus growth toward track-record and calibration thresholds.
4. Revisit one next source runtime, generated runtime types, hosted service boundaries, or stronger methods only when the expansion-readiness gate has evidence to unblock them.

MVP path:

- Milestones 72-80 define the minimum local, agent-native OPE product: connect approved or adapter-provided data, forecast before the outcome, preserve provenance, recalculate from pre-close evidence, resolve later, score against a baseline, and expose the whole loop through agent-readable surfaces.
- Milestones 81-90 should validate that product with real agent/developer use, add local measurement, grow evidence toward claim thresholds, and improve adoption before expanding into hosted or broad private-source runtimes.
- Milestones 91-97 should make repeated prediction setup easy for agents: one local campaign manifest, one foreground terminal loop, flexible recurrence policy, unique run state, resolver execution, append-only corpus evidence, and calibration readbacks without hosted scheduling.
- Hosted services, arbitrary private API/database parsing, provider optimization, and broad source-quality work remain post-MVP unless a milestone below explicitly narrows them to a local, policy-bound boundary.

## Milestone 0: Project Baseline

Status: Complete.

Goal: make the repository understandable and safe for future implementation work.

Tasks:

- [x] Add root `AGENTS.md`.
- [x] Add reusable `.agents/` baseline.
- [x] Add OPE whitepaper.
- [x] Add research evaluation of the whitepaper.
- [x] Add decision log with initial OPE decisions.
- [x] Add `README.md` that summarizes OPE for humans.
- [x] Add `CONTRIBUTING.md` once a runtime and commands exist.
- [x] Choose final package manager and application runtime.
- [x] Document bootstrap check commands in `AGENTS.md`.
- [x] Document canonical install, test, and release commands in `AGENTS.md`.

Exit criteria:

- A new contributor can explain OPE's scope, non-goals, and next implementation step from committed docs alone.

## Milestone 1: Core Contract Package

Status: Complete.

Goal: define the normative records before model or service code exists.

Tasks:

- [x] Create `spec/forecast-question.schema.json`.
- [x] Create `spec/question-lifecycle.md`.
- [x] Create `spec/forecast-history.schema.json`.
- [x] Create `spec/forecast-artifact.schema.json`.
- [x] Create `spec/evidence-packet.schema.json`.
- [x] Create `spec/aggregate-forecast.schema.json`.
- [x] Create `spec/resolution-record.schema.json`.
- [x] Create `spec/scoring-report.schema.json`.
- [x] Create `spec/track-record-report.schema.json`.
- [x] Create `spec/calibration-summary.schema.json`.
- [x] Create `spec/benchmark-run.schema.json`.
- [x] Add JSON fixtures for one binary question.
- [x] Add JSON fixtures for one numeric or interval question.
- [x] Add invalid fixtures for ambiguous, annulled, and mismatched request/result cases.
- [x] Add field-purpose and public/private safety review notes for core schemas.
- [x] Add a schema validation command once runtime/package tooling exists.

Key design requirements:

- Questions must have absolute open, close, and resolution timestamps.
- Resolution criteria must stand independently from background context.
- Resolution authority, primary source, and fallback sources must be explicit.
- Forecast histories must preserve active, withdrawn, superseded, and reaffirmed states.
- Ambiguous and annulled outcomes must be explicit and excluded from normal scoring summaries.
- Aggregate forecasts must declare source class, weighting method, recency method, and dependency assumptions.

Exit criteria:

- Schemas and fixtures describe a complete forecast lifecycle without needing implementation code.
- Every field has a validation purpose and a public/private safety assessment.

## Milestone 2: Scoring And Evaluation Harness

Status: Complete.

Goal: make forecast quality measurable before adding complex models.

Tasks:

- [x] Add `spec/scoring.md` with formulas and sign conventions.
- [x] Implement Brier score for binary forecasts.
- [x] Implement multiclass Brier or log score for categorical forecasts.
- [x] Implement log score where probability mass/density supports it.
- [x] Implement interval or pinball scoring only if the first wedge needs it.
- [x] Implement time-weighted scoring for forecast histories.
- [x] Implement exclusion handling for ambiguous and annulled questions.
- [x] Add calibration bucket calculation.
- [x] Add baseline-lift calculation.
- [x] Add track-record summary generation.
- [x] Add tests for all scoring fixtures.
- [x] Emit scoring, calibration, and track-record JSON reports from fixture inputs.
- [x] Add schema validation for generated reports once validator tooling exists.

Exit criteria:

- A fixture-only forecast set can produce scoring reports, calibration summaries, and track-record summaries.
- Incorrect handling of ambiguous or annulled questions fails tests.

## Milestone 3: First Wedge Decision

Status: Complete.

Goal: pick one domain and record why it is suitable.

Recommended wedge: weather-linked logistics disruption probability.

Why this wedge:

- Frequent resolution.
- Public or controllable weather and operations data.
- Clear operational value.
- Lower legal risk than finance, employment, healthcare, credit, or public-safety automation.
- Simple baselines are available.
- Agent use cases are concrete without requiring private downstream intent.

Tasks:

- [x] Add `.agents/decisions.md` entry selecting the first wedge.
- [x] Define the first question template.
- [x] Define supported geography and horizon.
- [x] Define accepted source classes.
- [x] Define primary and fallback resolution sources.
- [x] Define the baseline method.
- [x] Define minimum sample size for any calibration claim.
- [x] Define what is out of scope for the wedge.
- [x] Add `docs/first-wedge.md` or `spec/domains/weather-logistics.md`.

Exit criteria:

- The project has one explicit initial domain and does not invite broad forecasting claims.

## Milestone 4: Fixture-Based Evidence Loop

Status: Complete.

Goal: prove the full lifecycle without live external dependencies.

Tasks:

- [x] Add fixture ingestion.
- [x] Add normalized source records.
- [x] Add feature snapshot fixtures.
- [x] Generate baseline forecasts from fixtures.
- [x] Generate model forecast placeholders from deterministic fixture logic.
- [x] Generate evidence packets.
- [x] Append forecast history entries.
- [x] Close questions.
- [x] Resolve questions from fixtures.
- [x] Mark ambiguous and annulled fixture cases.
- [x] Score resolved forecasts.
- [x] Generate calibration and track-record reports.
- [x] Add a single command that runs the fixture evidence loop end to end.

Exit criteria:

- One command turns fixtures into evidence packets, forecast histories, resolution records, scoring reports, and track-record reports.
- No external network calls are required.

## Milestone 5: Benchmark And Anti-Leakage Mode

Status: Complete.

Goal: make model-quality claims defensible.

Tasks:

- [x] Define benchmark-run records.
- [x] Record model identity and version.
- [x] Record model training cutoff when known.
- [x] Record retrieval window and source timestamps.
- [x] Record source document hashes where feasible.
- [x] Add known-answer exclusion checks.
- [x] Add post-resolution leakage audit checklist.
- [x] Add benchmark fixtures that simulate pre-outcome and post-outcome data.
- [x] Add tests that fail if post-outcome data enters a pre-outcome forecast run.

Exit criteria:

- Benchmark runs can distinguish legitimate pre-outcome forecasts from contaminated runs.

## Milestone 6: Live Data Prototype

Status: Complete.

Goal: connect the first wedge to controlled real data without broad public claims.

Tasks:

- [x] Add allow-listed source connector for the selected wedge.
- [x] Add source fetch timestamps and raw source retention policy.
- [x] Add normalization for source data.
- [x] Add stale-source and corrected-source handling.
- [x] Add deterministic baseline for live data.
- [x] Add a simple domain model only after the baseline path works.
- [x] Generate live evidence packets.
- [x] Keep live forecasts in provisional status until enough outcomes resolve.

Exit criteria:

- The live path produces the same record types as the fixture path.
- Public docs still avoid quality claims beyond observed sample size.

## Milestone 7: Agent-Facing Read Access

Status: Complete.

Goal: expose artifacts safely after records stabilize.

Tasks:

- [x] Add read-only API or file interface for forecast artifacts.
- [x] Add read-only API or file interface for track-record summaries.
- [x] Add request/result binding validation.
- [x] Add public error sanitization.
- [x] Add rate limits and response size limits.
- [x] Add access policy for private or embargoed artifacts.
- [x] Add API docs only for implemented surfaces.

Exit criteria:

- Agents can retrieve artifacts and track records without triggering effectful forecast generation.

## Milestone 8: Controlled Forecast Request Access

Status: Complete.

Goal: allow agents or services to request forecasts under policy controls.

Tasks:

- [x] Add forecast request intake.
- [x] Validate question resolvability before accepting a request.
- [x] Add approval gates for high-impact, paid, external, or privacy-sensitive requests.
- [x] Add cancellation and timeout handling.
- [x] Add audit-safe request logging.
- [x] Add spend/cost controls if any paid provider or model call is introduced.
- [x] Add adversarial request tests.

Exit criteria:

- Effectful forecast generation is policy-gated, bounded, auditable, and tied to the originating request.

## Milestone 9: Hardening And Release Check

Status: Complete.

Goal: define what "release-ready" means.

Tasks:

- [x] Add secret scanning for docs, examples, fixtures, and generated artifacts.
- [x] Add malformed artifact tests.
- [x] Add prompt/source injection tests if LLM calls are introduced.
- [x] Add oversized input/output tests.
- [x] Add replay and duplicate forecast tests.
- [x] Add dependency/source-correlation tests for aggregate forecasts.
- [x] Add claim-review checklist.
- [x] Add `release:check` or equivalent command.
- [x] Update `AGENTS.md` with actual commands.

Exit criteria:

- A release check validates schemas, fixtures, scoring, evidence loop, security checks, and documentation claims.

## Milestone 10: Resolved Live Outcome Loop

Status: Complete.

Goal: close the first controlled live-style loop by resolving and scoring a declared outcome without making premature quality claims.

Tasks:

- [x] Add declared operations outcome fixture for the first weather-logistics live-style question.
- [x] Add declared post-event weather observation fixture.
- [x] Generate a resolved live forecast question, evidence packet, forecast artifact, history, resolution record, scoring report, calibration summary, track record, and outcome summary.
- [x] Exclude future resolution sources from forecast-time evidence provenance.
- [x] Add unscorable handling checks for missing operations coverage, corrected weather sources, and conflicting weather observations.
- [x] Keep the generated live track-record claim provisional while comparable resolved outcomes are below the minimum sample threshold.
- [x] Add `python3 scripts/resolve_live_weather_outcome.py` and `python3 scripts/ope.py resolve-live`.
- [x] Include live outcome resolution in the normal release check and public record index.

Exit criteria:

- One command checks the committed live outcome artifacts without network calls.
- The generated record index exposes the resolved live artifact and track record through the read-only local interface.
- Public docs still avoid live calibration claims until enough comparable outcomes exist.

## Milestone 11: Reusable Contract Validation

Status: Complete.

Goal: make OPE contract validation callable by future runtime code instead of keeping it embedded in one repository check.

Tasks:

- [x] Extract the local JSON Schema subset validator into `scripts/ope_schema.py`.
- [x] Keep `python3 scripts/check_schema_contracts.py` as a behavior-preserving all-fixture check.
- [x] Add single-record validation with inferred or explicit schema selection.
- [x] Add `python3 scripts/ope.py validate`.
- [x] Add validator smoke tests for schema inference, valid records, invalid required fields, and CLI output.
- [x] Include the validator smoke test in normal release checks.
- [x] Document the supported schema subset and boundary in `spec/runtime-validation.md`.

Exit criteria:

- Future scripts can import one validator module instead of duplicating schema-check logic.
- One command can validate a single OPE record and return machine-readable validation output.
- Release checks fail if the reusable validation surface drifts from committed contract behavior.

## Milestone 12: Local Forecast Pipeline Scaffold

Status: Complete.

Goal: connect controlled request intake to generated forecast records without introducing a hosted service or live network dependency.

Tasks:

- [x] Add a valid `generate_forecast` request fixture for the weather-logistics wedge.
- [x] Add `pipeline-run.schema.json` for request-to-forecast execution summaries.
- [x] Add `python3 scripts/run_forecast_pipeline.py` to produce deterministic fixture-mode pipeline outputs.
- [x] Generate request-bound question, feature snapshot, evidence packet, forecast artifact, forecast history, and pipeline-run records.
- [x] Keep pipeline execution in `fixture_dry_run` mode with no network access, no live fetch, and `effectfulGeneration: false`.
- [x] Reject blocked requests before output generation.
- [x] Exclude future resolution sources from forecast-time provenance.
- [x] Expose `python3 scripts/ope.py pipeline`.
- [x] Include pipeline checks in release checks and generated public record index.
- [x] Document the local pipeline boundary in `spec/forecast-pipeline.md`.

Exit criteria:

- One command checks the committed request-to-forecast pipeline outputs without network calls.
- The generated pipeline forecast artifact is readable through the local read-only record interface.
- Public docs continue to distinguish local fixture generation from a hosted service, SDK, or live model runtime.

## Milestone 13: Pipeline Resolution And Scoring

Status: Complete.

Goal: close the request-bound local pipeline lifecycle as a separate checked resolution step.

Tasks:

- [x] Add `python3 scripts/resolve_pipeline_outcome.py` to resolve the generated pipeline forecast from declared outcome fixtures.
- [x] Generate resolved question, resolution record, scoring report, calibration summary, track record, and outcome summary for the pipeline forecast.
- [x] Preserve request, pipeline-run, question, forecast, evidence, artifact, history, resolution, scoring, and track-record bindings.
- [x] Add unscorable handling checks for missing operations coverage, corrected weather sources, and conflicting weather observations.
- [x] Keep the generated pipeline outcome claim provisional while comparable resolved outcomes are below the minimum sample threshold.
- [x] Expose `python3 scripts/ope.py resolve-pipeline`.
- [x] Include pipeline resolution in release checks and the public record index.
- [x] Document the pipeline resolution boundary in `spec/pipeline-resolution.md`.

Exit criteria:

- One command checks the committed pipeline resolution outputs without network calls.
- The generated pipeline track record is readable through the local read-only record interface.
- Public docs keep generation, resolution, scoring, and live calibration claims separate.

## Milestone 14: Lifecycle Bundle Read Access

Status: Complete.

Goal: let agents inspect a bound forecast lifecycle without manually stitching generated files together.

Tasks:

- [x] Add `forecast-bundle` as a synthetic read-only record type keyed by `forecastId`.
- [x] Assemble forecast artifact, evidence packet, question, history, resolution, scoring, calibration, track-record, outcome-summary, and pipeline-run records when present.
- [x] Preserve existing read-only access limits, public access checks, response-size limits, and sanitized error behavior.
- [x] Validate bundle bindings across artifact, evidence, history, resolution, scoring, outcome summary, and pipeline run records.
- [x] Expose bundle reads through `python3 scripts/read_ope_record.py` and `python3 scripts/ope.py read`.
- [x] Include `forecast-bundle` in the generated public record index.
- [x] Add read-access and CLI smoke tests for the request-bound pipeline bundle.
- [x] Document the bundle read boundary in `spec/read-access.md`.

Exit criteria:

- One command returns a public lifecycle bundle for `forecast-502` without generating, resolving, scoring, fetching, or mutating anything.
- The public record index lists forecast bundles separately from raw forecast artifacts.
- Bundle access remains a local read-only convenience layer, not a new network API or persistence layer.

## Milestone 15: Claim-Safe Forecast Cards

Status: Complete.

Goal: give agents a compact forecast summary that preserves claim discipline without requiring a full lifecycle bundle read.

Tasks:

- [x] Add `forecast-card` as a synthetic read-only record type keyed by `forecastId`.
- [x] Build cards from the bound lifecycle bundle without generating or mutating records.
- [x] Include forecast probability, baseline probability, model identity, resolution status, score summary, request binding, and quality-claim boundary.
- [x] Include sample-size and fixture-mode warnings on the card.
- [x] Omit source hashes, supporting evidence URIs, raw provenance arrays, and full rationale text.
- [x] Expose card reads through `python3 scripts/read_ope_record.py` and `python3 scripts/ope.py read`.
- [x] Include `forecast-card` in the generated public record index.
- [x] Add read-access and CLI smoke tests for the request-bound pipeline card.
- [x] Document the card read boundary in `spec/read-access.md`.

Exit criteria:

- One command returns a compact card for `forecast-502` with probability, score, request binding, and claim boundary.
- The public record index lists forecast cards separately from bundles and artifacts.
- Card access remains a local read-only summary layer, not a substitute for full lifecycle records.

## Milestone 16: Read Surface Contracts

Status: Complete.

Goal: make agent-facing read summaries and discovery outputs explicit contracts, not just behavior checked JSON.

Tasks:

- [x] Add `forecast-card.schema.json`.
- [x] Add `record-index.schema.json`.
- [x] Validate `record-index.generated.json` through the schema contract checker.
- [x] Add `python3 scripts/check_read_contracts.py` for real read-surface output validation.
- [x] Validate the live `forecast-card` output for `forecast-502`.
- [x] Add a negative card schema check for missing warnings.
- [x] Include read contract checks in the release path.
- [x] Document the read-surface schema boundary in `spec/read-access.md` and `spec/runtime-validation.md`.

Exit criteria:

- The public record index is schema-bound.
- The compact forecast card read output is schema-bound and still carries claim warnings.
- Release checks fail if read-surface contracts drift from implemented output.

## Milestone 17: Release Manifest

Status: Complete.

Goal: provide one machine-readable summary of the implemented local OPE surface, commands, read counts, contracts, and claim boundaries.

Tasks:

- [x] Add `release-manifest.schema.json`.
- [x] Add `python3 scripts/generate_release_manifest.py`.
- [x] Generate `spec/fixtures/generated/release-manifest.generated.json`.
- [x] Include schema-file count and paths.
- [x] Include public read-surface counts from the generated record index.
- [x] Include canonical setup, test, release, and CLI commands.
- [x] Include explicit non-goals for network API, hosted service, production live data, live calibration claim, and universal prediction behavior.
- [x] Include claim-boundary counters for resolved pipeline and live outcomes.
- [x] Expose `python3 scripts/ope.py manifest`.
- [x] Include manifest drift and schema checks in the release path.
- [x] Document the manifest boundary in `spec/release-manifest.md`.

Exit criteria:

- One command checks the committed release manifest without running a hosted service or network call.
- The manifest validates against its schema.
- The manifest states fixture-ready status without implying live calibration or hosted-service readiness.

## Milestone 18: CI Release Gate

Status: Complete.

Goal: make the local release check repeatable in automation without adding deployment, publishing, or live-data behavior.

Tasks:

- [x] Add `.github/workflows/release-check.yml`.
- [x] Run the release gate on pull requests and pushes to `main`.
- [x] Use read-only repository permissions.
- [x] Set up Python 3.12.
- [x] Run `python3 scripts/release_check.py`.
- [x] Run `python3 -m py_compile scripts/*.py`.
- [x] Add `python3 scripts/check_ci_workflow.py` to validate workflow drift locally.
- [x] Guard against secrets, deploy, publish, push, package-upload, and arbitrary network command snippets in the workflow.
- [x] Include the CI checker in the release path.
- [x] Add the CI workflow path and commands to the generated release manifest.
- [x] Document the CI boundary in `spec/ci-release-gate.md`.

Exit criteria:

- One local command checks the CI workflow shape.
- Normal release checks fail if the CI workflow stops running the canonical release command.
- The CI workflow remains a release-readiness gate, not a hosted deployment pipeline.

## Milestone 19: Agent-Native Auto-Evidence Forecasting

Status: Complete.

Goal: let an agent request a forecast with `data: auto`, gather allowed public evidence under a declared source policy, and receive an agent-readable probabilistic forecast artifact with provenance, baseline comparison, uncertainty, and resolution metadata.

Product direction:

- Primary runtime actor: an agent or automated workflow.
- Primary adopter: a human developer supervising or integrating that agent.
- First domain: `weather-logistics`.
- First output type: binary probability.
- First evidence mode: best available allowed public evidence, not unbounded internet crawling.
- First interface: local CLI and JSON records, designed so MCP, HTTP, queue, or hosted adapters can wrap it later.

Tasks:

- [x] Add `PRODUCT.md` to persistent repo context.
- [x] Extend or add request contracts for `dataMode`: `provided`, `auto`, and `hybrid`.
- [x] Define `sourcePolicy` fields: allowed source classes, allowed connectors, retrieval window, freshness requirements, licensing constraints, max cost, max network calls, and approval gates.
- [x] Add an evidence-gathering plan record that captures search intent, connector plan, inclusion rules, exclusion rules, and unavailable evidence.
- [x] Add an auto-evidence dry-run command that returns the proposed question contract and evidence plan before fetching live sources.
- [x] Add an allow-listed fixture-replay evidence path for the weather-logistics wedge, starting with public weather evidence already compatible with existing Open-Meteo fixture mode.
- [x] Record raw source metadata, normalized source records, source quality, fetch timestamps, and provenance references for fixture-replay auto-evidence runs.
- [x] Add source injection, prompt injection, stale source, unavailable source, and conflicting source tests.
- [x] Keep effectful live fetches explicitly mode-gated and fixture-replayable in tests.
- [x] Generate a forecast card and lifecycle bundle from an auto-evidence request.
- [x] Preserve request, source policy, evidence plan, evidence packet, forecast artifact, history, resolution, score, and track-record bindings.
- [x] Update release manifest and read index with implemented auto-evidence capability only after commands and checks exist.
- [x] Document the current claim boundary: OPE gathered allowed evidence under a declared policy, not all possible evidence.

Exit criteria:

- One local command can validate an agent forecast request with `data: auto` and produce a machine-readable evidence plan.
- One checked command can run the weather-logistics auto-evidence path in fixture-replay mode without unbounded network access.
- One generated forecast card shows the forecast probability, baseline comparison, source policy, evidence mode, and claim warnings.
- Release checks fail if auto-evidence output loses source policy, provenance, request binding, or claim warnings.
- Public docs still avoid state-of-the-art or live calibration claims until benchmark and outcome evidence support them.

## Milestone 20: Forecasting Method Registry And Benchmark Upgrade

Status: Complete.

Goal: make "best available methods" concrete, comparable, and claim-safe before OPE advertises stronger forecasting quality.

Tasks:

- [x] Define a method registry for baseline, deterministic statistical, model-assisted, retrieval-assisted, ensemble, and external-reference methods.
- [x] Require every method to declare model identity, version, training cutoff when applicable, inputs, uncertainty method, known limitations, and compatible domains.
- [x] Add benchmark fixtures for method comparison in the first wedge.
- [x] Compare every non-baseline method against the baseline under the same source policy and retrieval window.
- [x] Add temporal leakage, known-answer, source-contamination, and post-resolution retrieval checks for model-assisted methods.
- [x] Add method-selection rules that favor simpler baselines when evidence quality is insufficient.
- [x] Report method quality only by domain, horizon, output type, source policy, coverage period, and sample size.

Exit criteria:

- OPE can explain why a method was selected for a forecast.
- OPE can show whether the method has beaten the baseline in comparable checked conditions.
- Documentation can describe supported methods without claiming state-of-the-art performance prematurely.

## Milestone 21: Agent Adapter Contract

Status: Complete.

Goal: make OPE easy for agents to call without coupling the engine to one transport.

Tasks:

- [x] Define stable JSON input and output envelopes for forecast request, evidence plan, forecast card, lifecycle bundle, resolution status, and scoring summary.
- [x] Standardize exit codes and sanitized error payloads for agent callers.
- [x] Add a read/write capability matrix for local CLI, future MCP, future HTTP, and future queue adapters.
- [x] Add transcript-style examples showing an agent requesting a forecast, reading the card, inspecting the bundle, and deciding whether to act or escalate.
- [x] Keep adapters thin: they may expose OPE records, but they must not redefine forecast, evidence, resolution, or scoring semantics.

Exit criteria:

- A future MCP or HTTP implementation can wrap the local engine without changing record contracts.
- Agents can distinguish validation, dry-run, live-fetch, resolved, scored, ambiguous, annulled, and approval-required states from JSON alone.

Implemented artifacts:

- `spec/agent-envelope.schema.json`
- `spec/agent-adapter.md`
- `spec/fixtures/generated/agent-adapter/`
- `scripts/build_agent_adapter_fixtures.py`
- `scripts/check_agent_adapter.py`
- `python3 scripts/ope.py agent-envelopes`

## Milestone 22: Local Agent Adapter Dispatcher

Status: Complete.

Goal: turn the envelope contract into a narrow local dispatcher that terminal agents can call operation by operation.

Tasks:

- [x] Add a local `agent-call` or equivalent command that accepts an operation, IDs, and max-byte limit and returns one `agent-envelope.schema.json` response.
- [x] Support the implemented read and validation operations: forecast request validation, evidence plan, forecast card, lifecycle bundle, resolution status, and scoring summary.
- [x] Return the standardized exit codes and sanitized error payloads from the dispatcher, not only from generated examples.
- [x] Add request binding checks for forecast ID, question ID, request ID, source-policy ID, resolution record ID, and scoring report ID.
- [x] Add CLI smoke tests for success, not-found, binding mismatch, approval-required, and response-too-large cases.
- [x] Keep the dispatcher local and transport-neutral so MCP, HTTP, or queue adapters can wrap it later.

Exit criteria:

- A terminal agent can request exactly one adapter operation and receive one schema-bound JSON envelope.
- The dispatcher remains a thin wrapper over OPE contracts and local records, not a new forecasting semantic layer.

Implemented artifacts:

- `scripts/agent_adapter_dispatcher.py`
- `scripts/check_agent_adapter_dispatcher.py`
- `python3 scripts/ope.py agent-call`

## Milestone 23: Agent Adapter Protocol Mapping

Status: Complete.

Goal: define how the local dispatcher maps onto MCP stdio and future HTTP or queue adapters without implementing a hosted service too early.

Tasks:

- [x] Add a machine-readable adapter capability document that lists operations, input fields, output envelope schema, exit-code mapping, and side-effect level.
- [x] Define MCP tool names and argument shapes that wrap `agent-call` one operation at a time.
- [x] Define HTTP endpoint and status-code mapping for the same operations without changing OPE record semantics.
- [x] Define queue message and result-envelope mapping for asynchronous future forecast runs.
- [x] Add approval-gate and credential-boundary notes for each transport.
- [x] Add examples showing how an agent should choose card, bundle, resolution, or scoring reads before taking downstream action.
- [x] Keep protocol mapping as documentation and checked fixtures until each adapter runtime is introduced.

Exit criteria:

- MCP, HTTP, or queue adapters can be implemented from a checked mapping document without changing the local dispatcher.
- Public docs still avoid claiming HTTP, queue, or hosted-service support before those runtimes exist.

Implemented artifacts:

- `spec/agent-adapter-protocol-map.schema.json`
- `spec/agent-adapter-protocol-map.md`
- `spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json`
- `scripts/generate_agent_adapter_protocol_map.py`
- `scripts/check_agent_adapter_protocol_map.py`
- `python3 scripts/ope.py agent-protocol-map`

## Milestone 24: MCP Adapter Scaffold

Status: Complete.

Goal: implement the first non-local protocol wrapper over the existing agent envelope without changing forecast, evidence, resolution, or scoring semantics.

Tasks:

- [x] Choose the smallest MCP runtime shape compatible with the repository's no-service local workflow.
- [x] Expose one MCP tool per mapped operation: request validation, evidence plan, forecast card, lifecycle bundle, resolution status, and scoring summary.
- [x] Preserve the `agent-envelope.schema.json` response shape, sanitized errors, standardized exit codes, warnings, and record bindings.
- [x] Keep all tools read-only or validation/dry-run; do not add production live fetching, paid actions, or private-source access.
- [x] Keep credentials out of prompt-visible tool arguments and returned OPE records.
- [x] Add a local MCP smoke checker that calls each tool through the scaffold or a deterministic equivalent.
- [x] Update docs to claim only local MCP scaffold support, not hosted service support.

Exit criteria:

- An agent host can call the six existing local adapter operations through an MCP-shaped surface and receive the same schema-bound envelopes.
- Release checks fail if MCP mappings drift from `agent-call` behavior or claim broader runtime capability than implemented.

Implemented artifacts:

- `scripts/ope_mcp_stdio.py`
- `scripts/check_mcp_adapter.py`
- `python3 scripts/ope.py mcp-stdio`
- updated `spec/agent-adapter-protocol-map.schema.json`
- updated `spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json`

## Milestone 25: Agent Forecast Run Orchestrator

Status: Complete.

Goal: give agents one local, schema-bound way to turn an accepted fixture-mode forecast request into the bound forecast outputs they need, without forcing every caller to manually chain the internal commands.

Tasks:

- [x] Define a forecast-run summary contract that binds request ID, source policy ID, evidence plan ID, source-set ID, method-selection ID, forecast ID, question ID, card ID, bundle ID, resolution status, and scoring status.
- [x] Add a local `forecast-run` command that validates a request and runs only the already-checked fixture-safe path for the first weather-logistics wedge.
- [x] Return a compact run summary plus links to the forecast card, lifecycle bundle, resolution status, and scoring summary.
- [x] Add failure summaries for rejected, approval-required, unresolvable, and response-too-large requests.
- [x] Add an MCP tool that wraps the run orchestrator only after the CLI summary is schema-bound and checked.
- [x] Keep live fetching, paid actions, private-source access, and hosted execution out of scope.

Exit criteria:

- An agent can submit the fixture-mode `data: auto` request and receive one bound summary that points to the forecast card and lifecycle bundle.
- Release checks fail if the run summary loses request/result binding or overstates live evidence, calibration, or method quality.

Implemented artifacts:

- `spec/forecast-run-summary.schema.json`
- `spec/agent-forecast-run.md`
- `spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-run.generated.json`
- `scripts/run_agent_forecast.py`
- `scripts/check_agent_forecast_run.py`
- `python3 scripts/ope.py forecast-run`
- MCP tool `ope_forecast_run`

## Milestone 26: Forecast Run Intake Matrix

Status: Complete.

Goal: make every forecast-run request outcome explicit before expanding orchestration beyond the default fixture-safe path.

Tasks:

- [x] Add checked forecast-run summaries for accepted, rejected, blocked, canceled, unsupported-fixture-path, and response-too-large requests.
- [x] Define which request decisions are terminal and which are retryable after approval, clarification, or policy changes.
- [x] Add a compact request outcome matrix for agents choosing whether to wait, ask for approval, revise the request, or stop.
- [x] Ensure MCP `ope_forecast_run` preserves the same outcome classes as the CLI.
- [x] Keep all non-default paths non-generating until a broader runtime decision is made.

Exit criteria:

- Agents can inspect a forecast-run failure summary and decide the next safe action without reading raw diagnostics.
- Release checks fail if a rejected or approval-gated request accidentally binds generated forecast outputs.

Implemented artifacts:

- `spec/forecast-run-intake-matrix.schema.json`
- `spec/fixtures/generated/forecast-run/weather-logistics-forecast-run-intake-matrix.generated.json`
- checked failure summaries under `spec/fixtures/generated/forecast-run/`
- `scripts/generate_forecast_run_intake_matrix.py`
- `scripts/check_forecast_run_intake_matrix.py`
- `python3 scripts/ope.py forecast-run-matrix`
- MCP parity checks for every `ope_forecast_run` intake class

## Milestone 27: Agent Forecast Runbook

Status: Complete.

Goal: give human developers and agents a compact operational guide for requesting a forecast, interpreting the run summary, choosing the next read surface, and handling every intake outcome.

Tasks:

- [x] Add a checked agent runbook that maps request validation, forecast run, forecast card, lifecycle bundle, resolution status, and scoring summary into one safe caller workflow.
- [x] Include examples for default `data: auto`, approval-required, rejected, canceled, unsupported, and response-too-large paths.
- [x] Define machine-readable next-action labels that align with the intake matrix without inventing new runtime behavior.
- [x] Add a local check that fails if the runbook examples drift from committed fixtures or MCP tool expectations.
- [x] Keep the runbook scoped to local CLI and MCP stdio behavior until a hosted runtime exists.

Exit criteria:

- A supervised agent can follow the runbook from request to forecast card without guessing which command or MCP tool to call next.
- Release checks fail if the documented next action contradicts the schema-bound intake matrix.

Implemented artifacts:

- `spec/agent-forecast-runbook.schema.json`
- `spec/agent-forecast-runbook.md`
- `spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-runbook.generated.json`
- `scripts/generate_agent_forecast_runbook.py`
- `scripts/check_agent_forecast_runbook.py`
- `python3 scripts/ope.py forecast-runbook`
- CLI and release checks covering runbook drift and outcome/action alignment

## Milestone 28: Policy-Bound Source Connector Contract

Status: Complete.

Goal: define the first reusable connector contract for `data: auto` evidence discovery and retrieval before adding broader live evidence gathering.

Tasks:

- [x] Add a schema for connector capability, allowed source class, freshness, rate-limit, credential, and provenance boundaries.
- [x] Add fixture connector records for the current weather source and at least one explicitly unsupported source class.
- [x] Define connector result records that separate raw source metadata, normalized fields, unavailable evidence, and retrieval diagnostics.
- [x] Add checks that prevent connector records from exposing secrets, raw stack traces, or prompt-visible credentials.
- [x] Keep normal checks fixture-safe and avoid unbounded web search or live network dependency.

Exit criteria:

- Agents can inspect which source connectors are allowed for the first domain before asking OPE to gather evidence.
- Release checks fail if a connector fixture implies unrestricted internet access, hidden credentials, or live calibration quality.

Implemented artifacts:

- `spec/source-connector-registry.schema.json`
- `spec/source-connector-result-set.schema.json`
- `spec/source-connectors.md`
- `spec/fixtures/generated/source-connectors/weather-logistics-source-connector-registry.generated.json`
- `spec/fixtures/generated/source-connectors/weather-logistics-source-connector-results.generated.json`
- `scripts/generate_source_connectors.py`
- `scripts/check_source_connectors.py`
- `python3 scripts/ope.py source-connectors`

## Milestone 29: Connector-Bound Evidence Plan Validation

Status: Complete.

Goal: make evidence planning validate every requested connector against the checked connector registry before any gatherer or future live runtime can use it.

Tasks:

- [x] Bind evidence-gathering plans to connector registry IDs and connector result-set IDs.
- [x] Reject or explain any request whose source policy names a connector missing from the registry.
- [x] Fail closed when a source policy allows an unsupported connector or unsupported source class.
- [x] Add checks that keep resolution-only connectors out of forecast-time search intents.
- [x] Preserve fixture-safe behavior while preparing the path for future allow-listed live connectors.

Exit criteria:

- Agents can see whether a request source policy is executable before OPE attempts evidence gathering.
- Release checks fail if the evidence plan drifts from the connector registry or silently treats unsupported connectors as usable.

Implemented artifacts:

- `scripts/source_connector_catalog.py`
- `connectorPolicyChecks` in `spec/evidence-gathering-plan.schema.json`
- generated evidence plan binding to `sourceconnectorregistry-001` and `sourceconnectorresults-001`
- request-intake reasons for unregistered, unsupported, and resolution-only auto connectors
- expanded `scripts/check_auto_evidence_plan.py` connector validation cases

## Milestone 30: Connector-Aware Evidence Gathering Gate

Status: Complete.

Goal: make the fixture gatherer consume connector-policy checks directly so no source result can be gathered unless the evidence plan marks its connector forecast-time executable.

Tasks:

- [x] Require gatherers to read `connectorPolicyChecks` and reject plans with unregistered, unsupported, or resolution-only forecast-time connectors.
- [x] Bind each source-set record to a connector registry entry and connector result entry.
- [x] Add checks that source-set connectors are a subset of `forecastTimeConnectors`.
- [x] Add a fixture for a mixed valid plus unsupported connector request and verify supported evidence is not partially gathered without an explicit rejected status.
- [x] Preserve the current fixture-replay path for the default weather-logistics request.

Exit criteria:

- Evidence gathering cannot proceed from a plan that is not connector-executable.
- Release checks fail if source-set records drift from connector registry and result-set bindings.

Implemented artifacts:

- `ensure_plan_connector_executable()` in `scripts/gather_auto_evidence.py`
- `connectorBinding` in `spec/evidence-source-set.schema.json`
- generated source-set binding to `sourceconnectorregistry-001` and `sourceconnectorresults-001`
- expanded `scripts/check_auto_evidence_gathering.py` connector-policy rejection cases
- expanded `scripts/check_source_connectors.py` source-set/result-set binding checks

## Milestone 31: Agent-Readable Evidence Trace Surface

Status: Complete.

Goal: make connector-bound evidence trace records easy for agents to inspect without reading unrelated forecast artifacts or raw source fixtures.

Tasks:

- [x] Add read-only record types for evidence source sets and source connector result sets.
- [x] Add a compact evidence-trace view that links request, evidence plan, source policy, connector registry, connector results, gathered source records, and forecast artifact IDs.
- [x] Expose the trace through the local CLI and, if consistent with the current adapter boundary, through the agent dispatcher/MCP scaffold.
- [x] Keep trace output sanitized: no raw stack traces, no prompt-visible credentials, and no claim that all internet evidence was gathered.
- [x] Update runbook and forecast-card links so agents can choose between compact cards, full lifecycle bundles, and evidence traces.

Exit criteria:

- Agents can inspect exactly which connectors and source records supported a forecast without re-running generation.
- Release checks fail if evidence trace bindings drift from request, plan, source set, connector result set, or forecast artifact IDs.

Implemented artifacts:

- `spec/evidence-trace.schema.json`
- `evidence-trace`, `evidence-source-set`, and `source-connector-results` read types in `scripts/read_ope_record.py`
- `python3 scripts/ope.py read --record-type evidence-trace --id forecast-602 --question-id question-601`
- `evidence_trace` agent operation in the local dispatcher, protocol map, and MCP stdio scaffold
- forecast-card evidence-trace links and forecast-run evidence-trace output refs
- expanded read, agent, CLI, MCP, runbook, and protocol-map checks

## Milestone 32: Historical-Only Baseline Forecast Path

Status: Complete.

Goal: let an agent or developer request a forecast using only committed historical data, without relying on a weather API, live source connector, or model-adjusted forecast signal.

Tasks:

- [x] Add a historical-only request fixture using `dataMode: provided`, `committed_fixture`, zero network calls, and no external source access.
- [x] Add a no-API forecast generator that produces question, feature snapshot, evidence packet, forecast artifact, forecast history, and pipeline-run records.
- [x] Make the forecast output equal the historical-frequency baseline and explicitly mark that no forecast-time weather signal was used.
- [x] Expose the path through the local CLI and forecast-run wrapper.
- [x] Keep read surfaces claim-safe: forecast cards and lifecycle bundles are available, evidence traces are not linked because no connector-bound evidence gathering ran.
- [x] Add checks so release validation fails if the historical-only path uses network access, live fetches, weather forecast features, or a non-baseline forecast probability.

Exit criteria:

- A developer can run a no-API historical forecast and receive probability `0.22` from `14 / 64` comparable historical disruption days.
- Agents can distinguish the historical-only forecast from the auto-evidence forecast: `forecast-702` uses `committed_fixture`, has no evidence trace, and has forecast probability equal to baseline probability.

Implemented artifacts:

- `spec/fixtures/requests/historical-weather-logistics-request.json`
- `scripts/run_historical_baseline_forecast.py`
- `scripts/check_historical_baseline_forecast.py`
- `python3 scripts/ope.py historical-forecast`
- `python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json`
- generated records under `spec/fixtures/generated/historical-baseline/`

## Milestone 33: Policy-Bound Live Connector Readiness Gate

Status: Complete.

Goal: prepare the first live evidence connector path without making normal checks network-dependent or implying unrestricted internet search.

Tasks:

- [x] Split connector execution modes into normal fixture replay, explicit integration live fetch, and future hosted live fetch.
- [x] Add a live-connector readiness contract that states approval, network, timeout, source freshness, raw retention, and diagnostic boundaries.
- [x] Add an integration-scoped Open-Meteo live-fetch check that is skipped by normal release checks unless explicitly requested.
- [x] Preserve the same evidence plan, source set, connector result, and evidence trace bindings for fixture and live modes.
- [x] Update docs so agents know when to use fixture-safe traces, integration live checks, or wait for a hosted runtime.

Exit criteria:

- Normal release checks remain offline and deterministic.
- A developer can intentionally run an integration-scoped live connector check and receive the same sanitized connector-bound records without expanding OPE into unbounded web search.

Implemented artifacts:

- `spec/live-connector-readiness.schema.json`
- `spec/live-connector-readiness.md`
- `spec/fixtures/generated/live-readiness/weather-logistics-open-meteo-live-readiness.generated.json`
- `scripts/generate_live_connector_readiness.py`
- `scripts/check_live_connector_readiness.py`
- `python3 scripts/ope.py live-readiness`

## Milestone 34: Domain-Agnostic Engine Setup Contract

Status: Complete.

Goal: define the OPE-standard setup record that lets an agent create or use a private prediction engine for any operational domain while preserving resolvable questions, source policies, method policies, maturity labels, and claim boundaries.

Tasks:

- [x] Add `domain-setup.schema.json` for candidate and reference engine setups.
- [x] Include question templates, output types, horizons, source roles, required fields, resolution rules, scoring rules, baseline policy, method policy, and maturity status.
- [x] Add a generated reference setup for `weather-logistics` without making weather-logistics the product boundary.
- [x] Add a candidate setup fixture for a second domain-like scenario, such as seaport berth availability, to prove domain-agnostic shape without implementing the full model.
- [x] Add checks that candidate setups cannot claim calibration, benchmarked quality, or production readiness.
- [x] Expose setup inspection through the local CLI for agents.
- [x] Update docs so agents understand setup statuses: candidate, fixture-ready, benchmarked, live-provisional, calibrated.

Exit criteria:

- Agents can inspect a domain-agnostic setup contract before connecting data or requesting a forecast.
- Weather-logistics is represented as a reference setup, while at least one non-weather-logistics candidate fixture proves OPE can describe new private prediction engines without overclaiming support.

Implemented artifacts:

- `spec/domain-setup.schema.json`
- `spec/domain-setup.md`
- `spec/fixtures/generated/domain-setups/weather-logistics-domain-setup.generated.json`
- `spec/fixtures/generated/domain-setups/seaport-berth-availability-domain-setup.generated.json`
- `scripts/generate_domain_setups.py`
- `scripts/check_domain_setups.py`
- `python3 scripts/ope.py domain-setups`

## Milestone 35: Source Manifest And Field Mapping Intake

Status: Complete.

Goal: let an agent provide a bounded manifest of files, APIs, or databases and have OPE classify, map, validate, and explain source usability before forecasting.

Tasks:

- [x] Add `source-manifest.schema.json` for caller-provided sources, connector type, source role, retrieval metadata, and privacy posture.
- [x] Add `field-mapping.schema.json` for user-provided, registry-backed, and agent-inferred mappings.
- [x] Add deterministic checks for required fields, type parsing, entity/geography matching, timestamp availability, source freshness, leakage risk, and sample size.
- [x] Add fixtures for accepted, accepted-partial, needs-confirmation, and rejected source manifests.
- [x] Add a local CLI command that returns a source intake report without producing a forecast.
- [x] Keep LLM or agent-inferred mappings as proposals until deterministic validation or user confirmation accepts them.

Exit criteria:

- An agent can pass a bounded source manifest and receive a machine-readable answer to: what can be used, what is missing, what needs confirmation, and which forecast methods are possible.

Implemented artifacts:

- `spec/source-manifest.schema.json`
- `spec/field-mapping.schema.json`
- `spec/source-intake-report.schema.json`
- `spec/source-intake.md`
- `spec/fixtures/source-intake/`
- `spec/fixtures/generated/source-intake/`
- `scripts/generate_source_intake.py`
- `scripts/check_source_intake.py`
- `python3 scripts/ope.py source-intake`

## Milestone 36: Setup-Aware Forecast Method Policy

Status: Complete.

Goal: make "best justified method" concrete for any engine setup by selecting among baseline, historical-conditioned, model-assisted, external-reference, and ensemble methods based on available data and benchmark evidence.

Tasks:

- [x] Extend method selection to read domain setup, source manifest, field mappings, sample-size checks, and method policy.
- [x] Add method eligibility reasons for insufficient data, missing outcome labels, missing forecast-time evidence, or leakage risk.
- [x] Add setup-aware baseline fallback rules.
- [x] Emit a method-decision record that agents can inspect before or with the forecast card.
- [x] Keep state-of-the-art and best-performance claims blocked unless benchmark and track-record evidence justify them.

Exit criteria:

- OPE can explain why a private setup received a baseline forecast, historical-conditioned forecast, model-assisted forecast, or rejection.

Implemented artifacts:

- `spec/setup-method-decision.schema.json`
- `spec/setup-method-decision.md`
- `spec/fixtures/generated/setup-method-decision/`
- `scripts/select_setup_method.py`
- `scripts/check_setup_method_decision.py`
- `python3 scripts/ope.py setup-method`

## Milestone 37: Recalculation History For New Evidence

Status: Complete.

Goal: make OPE update probabilities when new source data arrives without overwriting prior forecasts.

Tasks:

- [x] Add a recalculation trigger contract for changed files, API events, scheduled refreshes, or agent-submitted new evidence.
- [x] Add forecast-history append rules for recalculated forecasts.
- [x] Preserve previous probability, new probability, changed evidence refs, method version, and reason for update.
- [x] Add checks that post-outcome resolution data cannot enter forecast-time recalculation.
- [x] Add a fixture showing an operational forecast whose probability changes after new evidence arrives.

Exit criteria:

- Agents can distinguish original forecast, updated forecast, withdrawn forecast, and resolved outcome without losing the historical belief trail.

Implemented artifacts:

- `spec/recalculation-trigger.schema.json`
- `spec/recalculation-run.schema.json`
- `spec/recalculation-history.md`
- `spec/fixtures/generated/recalculation/`
- `scripts/generate_recalculation_history.py`
- `scripts/check_recalculation_history.py`
- `python3 scripts/ope.py recalculation`

## Milestone 38: Opt-In Live Evidence Capture Workspace

Status: Complete.

Goal: let a developer intentionally capture a sanitized live connector result into a local ignored workspace while preserving the same connector/result/evidence-trace boundaries used by fixture replay.

Tasks:

- [x] Add a `--save-local` mode for explicit live readiness checks that writes only sanitized connector-bound JSON under `.ope/live/`.
- [x] Validate saved live connector outputs against the same public result and readiness boundaries before they can be read by development tools.
- [x] Add a local command that converts one saved live connector result into a non-committed evidence source-set draft.
- [x] Keep saved live outputs out of git, normal release checks, public record index, track records, and calibration reports.
- [x] Document when an agent may inspect a local live draft and why it is not yet forecast evidence.

Exit criteria:

- A developer can intentionally run one live connector fetch, store a sanitized local draft, and validate it without committing raw live data or changing release checks.
- Agents can distinguish committed fixture evidence, ignored local live drafts, and future hosted live evidence.

Implemented artifacts:

- `spec/live-capture-workspace.md`
- `.ope/live/` git ignore boundary
- `scripts/live_capture_workspace.py`
- `scripts/check_live_capture_workspace.py`
- `python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD`
- `python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check`
- `python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --draft-source-set --write`

## Milestone 39: Setup-Aware Forecast Execution

Status: Complete.

Goal: let OPE create forecast artifacts from a domain setup, accepted source intake, and setup-aware method decision while preserving the existing forecast card, evidence trace, and lifecycle bundle boundaries.

Tasks:

- [x] Add a setup-bound forecast execution summary that consumes `domain-setup`, `source-intake-report`, and `setup-method-decision` records.
- [x] Generate a forecast only for accepted or accepted-partial intake with a selected enabled method.
- [x] Preserve blocked behavior for needs-confirmation, rejected intake, missing mappings, missing forecast-time evidence, and missing benchmark support.
- [x] Emit forecast artifact, evidence packet, history, card, and bundle records with setup, source-intake, and method-decision bindings.
- [x] Add checks that local live drafts cannot be consumed unless an explicit future source policy allows them.

Exit criteria:

- An agent can move from private setup intake to a claim-safe forecast artifact when the method decision allows execution.
- Blocked setup decisions remain non-generating and explain the next safe action.

Implemented artifacts:

- `spec/setup-forecast-run.schema.json`
- `spec/setup-forecast-execution.md`
- `spec/fixtures/generated/setup-forecast/`
- `scripts/run_setup_forecast.py`
- `scripts/check_setup_forecast.py`
- `python3 scripts/ope.py setup-forecast`
- forecast-card and lifecycle-bundle setup bindings for setup-generated forecasts

## Milestone 40: Setup-Specific Stronger Method Benchmark Gate

Status: Complete.

Goal: let OPE promote a setup from baseline-only execution to a stronger method only when the setup has clean, comparable benchmark evidence and explicit anti-leakage controls.

Tasks:

- [x] Add setup-bound benchmark references that connect a `domain-setup`, source-intake profile, method class, and comparable historical outcome set.
- [x] Extend setup method decisions so `deterministic_statistical` can become eligible only when benchmark evidence beats the baseline under the setup policy.
- [x] Add checks for temporal leakage, resolution-source contamination, sample-size thresholds, and missing benchmark references at the setup level.
- [x] Extend setup forecast execution to generate a non-baseline method only when the method decision is benchmark-approved.
- [x] Keep forecast cards explicit about baseline probability, model probability, method class, and claim status.

Exit criteria:

- Agents can see exactly why a setup remains baseline-only or why a stronger method is allowed.
- OPE still blocks state-of-the-art, calibration, and production claims unless benchmark and resolved-outcome evidence support them.

Implemented artifacts:

- `spec/setup-benchmark-gate.schema.json`
- `spec/fixtures/generated/setup-benchmark/`
- `scripts/generate_setup_benchmark_gate.py`
- `scripts/check_setup_benchmark_gate.py`
- `python3 scripts/ope.py setup-benchmark`
- setup method decisions with selected benchmark-gate bindings
- setup forecast execution that emits deterministic forecast probability only for benchmark-approved intake

## Milestone 41: Local Source Manifest Builder

Status: Complete.

Goal: let an agent inspect caller-approved local files and draft an OPE source manifest plus field-mapping proposal without producing forecasts or treating inferred mappings as verified facts.

Tasks:

- [x] Add a local read-only source inspection command for small CSV and JSON files.
- [x] Emit a draft source manifest with field inventory, row counts, timestamps, privacy flags, and sanitized feature summaries.
- [x] Emit a draft field mapping with explicit `user_provided`, `registry_backed`, or `agent_inferred` origins.
- [x] Mark agent-inferred mappings as proposed and require confirmation before forecast execution.
- [x] Add checks that the builder rejects secrets, oversized files, unsupported formats, and post-outcome leakage indicators.
- [x] Keep generated drafts out of public read surfaces until source intake accepts them.

Exit criteria:

- A developer or agent can point OPE at local fixture files and receive a draft manifest/mapping pair suitable for source intake.
- OPE still does not forecast from arbitrary private files until intake and method gates approve the setup.

Implemented artifacts:

- `spec/source-manifest-build.schema.json`
- `spec/source-manifest-builder.md`
- `spec/fixtures/local-source-files/`
- `spec/fixtures/generated/source-builder/`
- `scripts/build_source_manifest.py`
- `scripts/check_source_manifest_builder.py`
- `python3 scripts/ope.py source-builder`
- source-builder checks in normal repository and CLI checks

## Milestone 42: Builder Draft Intake Handoff

Status: Complete.

Goal: make the path from local source-builder drafts to source intake explicit, including confirmation of proposed mappings, without allowing unconfirmed drafts to generate forecasts.

Tasks:

- [x] Add a checked handoff record that binds a source-manifest build to source intake inputs.
- [x] Add an unconfirmed-builder-draft case that source intake classifies as `needs_confirmation`.
- [x] Add a confirmed-builder-draft case that source intake can classify according to available source roles and sample-size limits.
- [x] Preserve source-builder rejection reasons when drafts cannot enter source intake.
- [x] Add CLI output that tells agents whether to ask for mapping confirmation, collect more data, or proceed to method gating.
- [x] Keep draft source-builder artifacts out of public read surfaces until source intake and later gates accept them.

Exit criteria:

- An agent can inspect local files, draft source manifest inputs, submit those draft inputs to source intake, and receive a deterministic next action.
- Forecast execution remains blocked unless source intake and setup method gates approve the resulting setup.

Implemented artifacts:

- `spec/source-intake-handoff.schema.json`
- `spec/source-intake-handoff.md`
- `spec/fixtures/generated/source-handoff/`
- `scripts/generate_source_intake_handoff.py`
- `scripts/check_source_intake_handoff.py`
- `python3 scripts/ope.py source-handoff`
- handoff cases for unconfirmed, confirmed, insufficient-sample, secret, unsupported-format, oversized, and leakage outcomes

## Milestone 43: Builder Handoff Method Gate

Status: Complete.

Goal: let accepted source-handoff records flow into setup benchmark and setup method decisions without creating forecast artifacts.

Tasks:

- [x] Add setup benchmark gates for confirmed builder-handoff intake reports.
- [x] Add setup method decisions that consume handoff-bound source-intake reports.
- [x] Preserve `ask_mapping_confirmation`, `collect_more_data`, and `replace_rejected_sources` handoff outcomes as non-method-selecting cases.
- [x] Add CLI output that shows whether a builder-handoff accepted draft reaches baseline or deterministic method eligibility.
- [x] Keep forecast execution separate until a later explicit setup forecast run consumes a method decision.

Exit criteria:

- An agent can inspect files, confirm mappings, pass accepted source intake into method gates, and see the selected method or blocking reason.
- No handoff path creates forecast artifacts before setup forecast execution explicitly allows it.

Implemented artifacts:

- `spec/source-handoff-method-gate.schema.json`
- `spec/source-handoff-method-gate.md`
- `spec/fixtures/generated/source-handoff-method/`
- `scripts/generate_source_handoff_method_gate.py`
- `scripts/check_source_handoff_method_gate.py`
- `python3 scripts/ope.py source-handoff-method`
- handoff-bound setup benchmark gates and setup method decisions for unconfirmed, confirmed, insufficient, and builder-rejected outcomes

## Milestone 44: Explicit Setup Forecast From Handoff Method Decision

Status: Complete.

Goal: let an agent explicitly execute a setup forecast from an accepted source-handoff method decision, while keeping blocked handoff outcomes non-generating.

Tasks:

- [x] Add a handoff-bound setup forecast execution path that consumes `sourcehandoffmethodgate-002`.
- [x] Bind the resulting forecast run to the handoff, source-intake report, setup benchmark gate, and setup method decision.
- [x] Keep unconfirmed, insufficient, and builder-rejected handoff method gates as blocked run summaries with no forecast IDs.
- [x] Add CLI output that distinguishes method-gate readiness from actual forecast execution.
- [x] Preserve the existing setup forecast claim boundary: deterministic execution can run in fixtures, but quality, calibration, production, and state-of-the-art claims stay blocked.

Exit criteria:

- An agent can go from approved local-file sources to an explicit setup forecast command without bypassing source intake, benchmark gates, or method decisions.
- Every blocked handoff method outcome remains non-generating and explains the next action.

Implemented artifacts:

- `spec/source-handoff-forecast.md`
- `spec/fixtures/generated/source-handoff-forecast/`
- `scripts/run_source_handoff_forecast.py`
- `scripts/check_source_handoff_forecast.py`
- `python3 scripts/ope.py source-handoff-forecast`
- forecast card and lifecycle bundle read support for `forecast-1102`
- setup forecast run bindings for `sourceIntakeHandoffId` and `sourceHandoffMethodGateId`

## Milestone 45: Source-Handoff Forecast Resolution And Scoring

Status: Complete.

Goal: resolve and score the handoff-bound forecast so the source-builder-to-forecast path has the same lifecycle coverage as other generated forecast paths.

Tasks:

- [x] Add a fixture resolver for `forecast-1102` using the declared outcome source bound through the handoff source manifest.
- [x] Emit resolution, scoring, calibration, track-record, and outcome-summary records for the handoff-bound forecast.
- [x] Keep unresolved and blocked handoff runs out of scoring summaries.
- [x] Extend forecast card and bundle checks so `forecast-1102` exposes resolution and score once resolved.
- [x] Preserve claim boundaries: quality and calibration claims remain blocked until declared comparable sample thresholds are met.

Exit criteria:

- An agent can inspect the full handoff-bound lifecycle from local source files through forecast, resolution, score, and read surfaces.
- Blocked handoff cases remain non-generating and non-scored.

Implemented artifacts:

- `spec/source-handoff-resolution.md`
- `spec/fixtures/generated/source-handoff-resolution/`
- `scripts/resolve_source_handoff_outcome.py`
- `scripts/check_source_handoff_resolution.py`
- `python3 scripts/ope.py resolve-source-handoff`
- resolved and scored forecast card, lifecycle bundle, track-record, and outcome summary for `forecast-1102`

## Milestone 46: Source-Handoff Agent Setup Runbook

Status: Complete.

Goal: give agents one compact, checked workflow for private source setup that spans local file inspection, source intake handoff, method gating, explicit forecast execution, resolution, scoring, and safe next actions.

Tasks:

- [x] Add an agent-facing source-handoff setup runbook that maps each lifecycle step to existing CLI commands and future adapter surfaces.
- [x] Include next-action labels for confirmed, unconfirmed, insufficient-data, builder-rejected, forecast-generated, resolved, and sample-size-blocked cases.
- [x] Bind the runbook to existing source-builder, handoff, method-gate, forecast, resolution, card, bundle, and track-record records.
- [x] Add checks that the runbook does not imply unconfirmed mappings can forecast, blocked cases can score, or one resolved outcome can justify calibration claims.
- [x] Expose the runbook through the local CLI and document how agents should use it before building a broader private engine workflow.

Exit criteria:

- An agent can follow one checked local guide from caller-approved source files to a claim-safe resolved forecast card.
- The guide preserves OPE's domain-agnostic setup vision without advertising arbitrary private API/database parsing, hosted runtime behavior, or live calibration.

Implemented artifacts:

- `spec/source-handoff-setup-runbook.schema.json`
- `spec/source-handoff-setup-runbook.md`
- `spec/fixtures/generated/source-handoff-runbook/weather-logistics-source-handoff-setup-runbook.generated.json`
- `scripts/generate_source_handoff_setup_runbook.py`
- `scripts/check_source_handoff_setup_runbook.py`
- `python3 scripts/ope.py source-handoff-runbook`
- CLI and repository checks covering case next actions, blocked case boundaries, and sample-size claim boundaries

## Milestone 47: General Private Setup Workflow Contract

Status: Complete.

Goal: turn the source-handoff fixture path into a domain-agnostic private setup workflow contract without claiming arbitrary private API/database parsing or hosted runtime support.

Tasks:

- [x] Define a setup workflow summary that can represent local files now and future caller-approved APIs or databases later.
- [x] Separate setup phases into source discovery, mapping confirmation, source intake, method gating, forecast execution, recalculation, resolution, and scoring.
- [x] Add outcome classes for setup-ready, needs-confirmation, needs-more-data, rejected-source, unsupported-source, and runtime-not-implemented.
- [x] Preserve current source-handoff runbook as the weather-logistics fixture example of the general workflow.
- [x] Add checks that the general workflow remains domain-agnostic, source-policy-bound, and claim-safe.

Exit criteria:

- Agents can inspect one domain-agnostic setup workflow contract before choosing a concrete setup path.
- The contract guides future private source support without implying OPE already parses arbitrary APIs, databases, or live private systems.

Implemented artifacts:

- `spec/private-setup-workflow.schema.json`
- `spec/private-setup-workflow.md`
- `spec/fixtures/generated/private-setup-workflow/ope-private-setup-workflow.generated.json`
- `scripts/generate_private_setup_workflow.py`
- `scripts/check_private_setup_workflow.py`
- `python3 scripts/ope.py private-setup-workflow`
- repository and CLI checks covering phase order, outcome classes, source-kind implementation status, reference fixture binding, and claim boundaries

## Milestone 48: Private Source Adapter Capability Contract

Status: Complete.

Goal: define how local-file, manual-upload, private API, and private database adapters declare capabilities, permissions, credentials, freshness, privacy, and effect boundaries before any generic connector runtime is implemented.

Tasks:

- [x] Add a source adapter capability contract for local files, private APIs, private databases, and manual uploads.
- [x] Separate capability declaration from source execution, so planned adapters cannot fetch or parse data by implication.
- [x] Include approval, credential, prompt-visibility, privacy, freshness, rate-limit, and audit-log boundaries.
- [x] Bind the capability contract to the private setup workflow source kinds.
- [x] Add checks that private API and database adapters remain non-executable until an explicit runtime lands.

Exit criteria:

- Agents can inspect whether a private source kind is available, planned, unsupported, or approval-gated before attempting setup.
- No private source adapter claims execution, credential access, or live data use without an implemented and checked runtime.

Implemented artifacts:

- `spec/private-source-adapter-capability.schema.json`
- `spec/private-source-adapters.md`
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-capabilities.generated.json`
- `scripts/generate_private_source_adapter_capabilities.py`
- `scripts/check_private_source_adapter_capabilities.py`
- `python3 scripts/ope.py private-source-adapters`
- private setup workflow source-kind expansion for planned `manual_upload`
- repository and CLI checks covering source-kind binding, declaration-only behavior, offline normal checks, secret-storage bans, manual-upload/private-API/private-database runtime-not-implemented status, and local-file/manual-mapping/auto-evidence fixture boundaries

## Milestone 49: Private Source Adapter Outcome Matrix

Status: Complete.

Goal: define the agent-facing outcome matrix for source adapter attempts before any setup execution, so callers can see whether a source should proceed, request approval, wait for runtime, or be replaced.

Tasks:

- [x] Add a checked outcome matrix for private source adapter decisions.
- [x] Cover at least available fixture, approval-required fixture, planned runtime, unsupported source, credential-missing, and rejected unsafe source outcomes.
- [x] Bind each outcome to the private source adapter capability contract and private setup workflow outcome classes.
- [x] Add CLI output that lets agents inspect next actions without executing source reads.
- [x] Preserve the rule that planned private adapters cannot create source manifests, forecast artifacts, or scoring records.

Exit criteria:

- Agents can turn adapter capabilities into deterministic next actions before attempting setup.
- Planned private adapters remain non-executing and claim-safe while still giving useful setup guidance.

Implemented artifacts:

- `spec/private-source-adapter-outcome-matrix.schema.json`
- `spec/private-source-adapter-outcomes.md`
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-outcome-matrix.generated.json`
- `scripts/generate_private_source_adapter_outcome_matrix.py`
- `scripts/check_private_source_adapter_outcome_matrix.py`
- `python3 scripts/ope.py private-source-adapter-outcomes`
- repository and CLI checks covering capability binding, workflow outcome binding, available fixture, approval-required fixture, planned runtime, unsupported source, credential-missing, rejected unsafe source, non-execution, and blocked artifact creation

## Milestone 50: Adapter Outcome To Source Intake Bridge

Status: Complete.

Goal: define the checked bridge from adapter outcome decisions into the first allowed source-intake entrypoint, so agents know when to run source builder, ask confirmation, use fixture evidence, wait for runtime, or stop.

Tasks:

- [x] Add a bridge contract that consumes the private source adapter outcome matrix.
- [x] Map outcome rows to allowed commands, required inputs, blocked outputs, and retry conditions.
- [x] Bind `available_fixture` local files to source-builder and `approval_required_fixture` mappings to source-handoff confirmation.
- [x] Keep planned, unsupported, unsafe, and credential-missing cases non-generating.
- [x] Add CLI and checks for bridge drift and source-artifact boundaries.

Exit criteria:

- Agents can move from adapter outcome decisions to the correct next local command without guessing.
- No bridge path creates forecast artifacts or scoring records before source intake, method gates, and explicit forecast execution allow it.

Implemented artifacts:

- `spec/private-source-adapter-intake-bridge.schema.json`
- `spec/private-source-adapter-bridge.md`
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-intake-bridge.generated.json`
- `scripts/generate_private_source_adapter_intake_bridge.py`
- `scripts/check_private_source_adapter_intake_bridge.py`
- `python3 scripts/ope.py private-source-adapter-bridge`
- repository and CLI checks covering outcome-matrix binding, checked entrypoints, caller confirmation before source-handoff, planned-runtime blocking, unsupported and unsafe source stops, and no source, forecast, score, live-fetch, or credential artifact creation

## Milestone 51: Private Setup Request Contract

Status: Complete.

Goal: define the agent-facing request record that starts private engine setup before adapter routing, so a caller can declare the forecast intent, setup mode, source policy, selected source kinds, approval state, and expected outputs without OPE guessing or reading private data.

Tasks:

- [x] Add a private setup request schema with forecast-question draft, domain setup reference, requested source kinds, setup mode, source policy, approval state, and desired output surface.
- [x] Add fixture requests for local files, confirmed/manual mappings, fixture auto-evidence, planned manual upload, planned private API/database, unregistered source, and unsafe source.
- [x] Map request rows to adapter capabilities, adapter outcomes, and bridge entrypoints without executing source reads.
- [x] Preserve approval and credential boundaries for private sources, manual mappings, effectful actions, and unsafe inputs.
- [x] Add CLI and checks that classify requests into proceed, confirm, fixture, wait, replace, reject, or stop actions before source intake.

Exit criteria:

- Agents can hand OPE one setup-intent record and receive the safe first setup action without reverse-engineering capability, outcome, and bridge contracts separately.
- The request contract remains domain-agnostic and does not imply arbitrary API/database parsing, live private fetching, forecast execution, or scoring.

Implemented artifacts:

- `spec/private-setup-request.schema.json`
- `spec/private-setup-request.md`
- `spec/fixtures/generated/private-setup-requests/ope-private-setup-requests.generated.json`
- `scripts/generate_private_setup_requests.py`
- `scripts/check_private_setup_requests.py`
- `python3 scripts/ope.py private-setup-requests`
- repository and CLI checks covering bridge binding, local-file source-builder routing, manual mapping confirmation, fixture auto-evidence routing, planned-runtime waits, unsupported-source replacement, unsafe-source stops, and no private reads, source outputs, forecast artifacts, scoring records, live fetches, or credential records

## Milestone 52: Private Setup Request First-Action Dispatcher

Status: Complete.

Goal: expose a small local dispatcher that accepts one private setup request row or request JSON and returns the first safe setup action as a compact agent-facing response.

Tasks:

- [x] Add a dispatcher input contract for one private setup request.
- [x] Accept a request object or generated request ID and return the bound route decision.
- [x] Return sanitized errors for unknown source kinds, unsafe sources, missing approvals, and planned runtimes.
- [x] Keep dispatcher output non-executing; it may name commands but must not run source-builder, source-handoff, or gather-evidence.
- [x] Add CLI and checks for every current request outcome.

Exit criteria:

- Agents can ask OPE for the next private setup action from one request without reading the full request set.
- The dispatcher preserves the same non-execution and claim boundaries as the request contract.

Implemented artifacts:

- `spec/private-setup-first-action.schema.json`
- `spec/private-setup-first-action.md`
- `spec/fixtures/generated/private-setup-actions/`
- `scripts/private_setup_action_dispatcher.py`
- `scripts/generate_private_setup_first_actions.py`
- `scripts/check_private_setup_first_actions.py`
- `python3 scripts/ope.py private-setup-actions`
- `python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001`
- repository and CLI checks covering generated request binding, local-file command suggestions, manual mapping confirmation, fixture auto-evidence routing, planned-runtime waits, unsupported-source replacement, unsafe-source rejection, sanitized unknown-source and missing-approval errors, and no private reads, command execution, forecast artifacts, scoring records, or credential storage

## Milestone 53: Private Setup First-Action Runbook

Status: Complete.

Goal: give agents a checked runbook that turns private setup first-action statuses into the next safe caller-visible step, expected command, expected output class, and stop condition without executing source commands.

Tasks:

- [x] Add a runbook schema covering every first-action status.
- [x] Bind runbook rows to generated private setup first-action fixtures.
- [x] Explain the allowed next command, expected output, caller confirmation requirement, and blocked outputs for each status.
- [x] Keep planned runtimes, unknown sources, unsafe sources, and missing approvals out of source intake.
- [x] Add CLI and checks for runbook drift and non-execution boundaries.

Exit criteria:

- Agents can move from one first-action response to the correct next step without reading all lower-level setup contracts.
- The runbook remains guidance only and does not execute source-builder, source-handoff, fixture gathering, forecast execution, resolution, or scoring.

Implemented artifacts:

- `spec/private-setup-first-action-runbook.schema.json`
- `spec/private-setup-first-action-runbook.md`
- `spec/fixtures/generated/private-setup-actions/ope-private-setup-first-action-runbook.generated.json`
- `scripts/generate_private_setup_first_action_runbook.py`
- `scripts/check_private_setup_first_action_runbook.py`
- `python3 scripts/ope.py private-setup-action-runbook`
- repository and CLI checks covering first-action binding, full status coverage, local-file source-builder guidance, manual mapping confirmation, fixture evidence guidance, planned runtime waits, source replacement, unsafe-source stops, sanitized bad-request playbooks, source-intake blocking, and no command execution, forecast artifacts, scoring records, or credential storage

## Milestone 54: Private Setup Agent Bundle

Status: Complete.

Goal: expose one compact agent-facing bundle that joins a private setup request row, its first-action response, and the matching runbook row so agents can inspect setup state without reading three separate generated surfaces.

Tasks:

- [x] Add a bundle schema that binds private setup request, first-action, and runbook row IDs.
- [x] Generate bundle examples for every current private setup source kind plus sanitized bad-request cases.
- [x] Include the next safe command, expected output class, blocked outputs, caller confirmation requirement, and claim boundary in one response.
- [x] Keep bundle generation read-only and non-executing.
- [x] Add CLI and checks for bundle drift, binding integrity, and blocked source boundaries.

Exit criteria:

- Agents can ask for one compact setup guidance bundle for a request ID and know what to do next.
- The bundle does not create source manifests, field mappings, forecast artifacts, scoring records, live fetches, or credential records.

Implemented artifacts:

- `spec/private-setup-agent-bundle.schema.json`
- `spec/private-setup-agent-bundle.md`
- `spec/fixtures/generated/private-setup-agent-bundles/`
- `scripts/generate_private_setup_agent_bundles.py`
- `scripts/check_private_setup_agent_bundles.py`
- `python3 scripts/ope.py private-setup-bundles`
- `python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001`
- repository and CLI checks covering request/action/runbook binding, local-file source-builder guidance, manual mapping confirmation, fixture evidence guidance, planned runtime waits, unsupported and unsafe source blocking, bad-request examples, claim boundaries, and no source, forecast, score, live-fetch, or credential artifact creation

## Milestone 55: Private Setup Bundle Adapter Envelope

Status: Complete.

Goal: expose private setup bundle reads through the existing transport-neutral agent envelope pattern so future MCP/HTTP/queue adapters can return setup guidance with the same status, exit-code, and sanitized-error behavior as forecast read surfaces.

Tasks:

- [x] Add a private setup bundle operation to the local agent adapter dispatcher contract.
- [x] Return one envelope for `private_setup_bundle` by request ID or bad-request case.
- [x] Add generated success and sanitized error envelope fixtures.
- [x] Map the operation into the local MCP stdio scaffold and protocol map.
- [x] Add checks that the adapter remains read-only and does not execute source setup commands.

Exit criteria:

- Agents using the adapter surface can request private setup guidance without shelling out to lower-level bundle commands.
- The envelope preserves the same no-execution, no-credential, no-forecast, and no-scoring boundaries as the bundle.

Implemented artifacts:

- `spec/agent-envelope.schema.json`
- `spec/agent-adapter-protocol-map.schema.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-bundle-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-bundle-sanitized-error-envelope.generated.json`
- `scripts/agent_adapter_dispatcher.py`
- `scripts/build_agent_adapter_fixtures.py`
- `scripts/generate_agent_adapter_protocol_map.py`
- `scripts/ope_mcp_stdio.py`
- `python3 scripts/ope.py agent-call --operation private_setup_bundle --private-setup-request-id privatesetuprequest-001`
- repository and CLI checks covering request binding, bad-request bundle reads, sanitized missing-bundle errors, MCP tool exposure, protocol-map drift, and no source setup command execution

## Milestone 56: Private Setup Local-File Builder Adapter

Status: Complete.

Goal: let an agent continue from `private_setup_bundle` into the checked local-file source-builder path through an agent-facing adapter operation that accepts caller-approved CSV/JSON paths and mapping hints, inspects only those files, and returns draft source manifest/mapping guidance without creating forecast or scoring artifacts.

Tasks:

- [x] Add a source-builder adapter operation with explicit approval and file-path inputs.
- [x] Return schema-bound envelopes for accepted drafts, mapping-confirmation-needed drafts, rejected secret/unsupported/oversized/leakage cases, and sanitized errors.
- [x] Keep field and alias mappings proposed until deterministic validation or caller confirmation accepts them.
- [x] Add MCP/protocol-map support without exposing credential arguments or arbitrary file discovery.
- [x] Add checks that source-builder adapter outputs cannot enter forecast execution without source intake, method gate, and benchmark decisions.

Exit criteria:

- Agents can follow the private setup guidance for local files from adapter call to draft source manifest guidance without using lower-level CLI surfaces directly.
- The adapter can inspect only caller-approved local files, cannot read arbitrary private data, and cannot create forecast, score, live-fetch, or credential records.

Implemented artifacts:

- `spec/agent-envelope.schema.json`
- `spec/agent-adapter-protocol-map.schema.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-contains-secret-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-unsupported-format-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-oversized-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-leakage-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-builder-sanitized-error-envelope.generated.json`
- `scripts/agent_adapter_dispatcher.py`
- `scripts/build_agent_adapter_fixtures.py`
- `scripts/generate_agent_adapter_protocol_map.py`
- `scripts/ope_mcp_stdio.py`
- `python3 scripts/ope.py agent-call --operation private_setup_source_builder --private-setup-request-id privatesetuprequest-001 --source-builder-case local_draft`
- repository and CLI checks covering caller-approved file inputs, checked source-builder cases, proposed inferred mappings, rejected secret/unsupported/oversized/leakage cases, sanitized malformed-input errors, MCP tool exposure, protocol-map drift, and no forecast, score, live-fetch, credential, or public read-record creation

## Milestone 57: Private Setup Source-Handoff Adapter Envelope

Status: Complete.

Goal: let an agent continue from source-builder draft guidance into checked source-handoff next actions through the same agent adapter surface, while keeping unconfirmed mappings, insufficient data, rejected sources, and leakage cases blocked before method gates or forecast execution.

Tasks:

- [x] Add a source-handoff adapter operation that reads checked source-builder handoff cases and returns one envelope.
- [x] Preserve source-builder, source-intake, and mapping-confirmation bindings in the payload.
- [x] Return separate envelopes for unconfirmed draft, confirmed draft, insufficient data, secret, unsupported, oversized, and leakage cases.
- [x] Add MCP/protocol-map support without accepting raw private data, credentials, or forecast inputs.
- [x] Add checks that only confirmed accepted handoffs can proceed toward setup method gates, and none create forecast or score artifacts.

Exit criteria:

- Agents can move from private setup source-builder guidance to source-handoff next actions without using lower-level CLI surfaces directly.
- The adapter preserves the confirmation-before-intake boundary and cannot bypass setup benchmark or method decisions.

Implemented artifacts:

- `spec/agent-envelope.schema.json`
- `spec/agent-adapter-protocol-map.schema.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-unconfirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-confirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-insufficient-confirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-contains-secret-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-unsupported-format-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-oversized-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-source-handoff-leakage-envelope.generated.json`
- `scripts/agent_adapter_dispatcher.py`
- `scripts/build_agent_adapter_fixtures.py`
- `scripts/generate_agent_adapter_protocol_map.py`
- `scripts/ope_mcp_stdio.py`
- `python3 scripts/ope.py agent-call --operation private_setup_source_handoff --private-setup-request-id privatesetuprequest-001 --source-handoff-case confirmed_builder_draft`
- repository and CLI checks covering confirmed, unconfirmed, insufficient-data, rejected source cases, source-builder/source-intake/mapping bindings, MCP tool exposure, protocol-map drift, and no forecast, score, live-fetch, credential, or public read-record creation

## Milestone 58: Private Setup Method-Gate Adapter Envelope

Status: Complete.

Goal: let an agent continue from a confirmed source-handoff into checked setup benchmark and method-decision guidance through the same adapter surface, while keeping blocked handoffs, failed benchmarks, and baseline fallbacks explicit before forecast execution.

Tasks:

- [x] Add a setup method-gate adapter operation that reads checked source-handoff method-gate cases and returns one envelope.
- [x] Preserve source-handoff, source-intake, benchmark, and method-decision bindings in the payload.
- [x] Return separate envelopes for confirmed accepted handoff, unconfirmed mapping, insufficient data, rejected sources, and leakage cases.
- [x] Add MCP/protocol-map support without accepting raw private data, credentials, or forecast inputs.
- [x] Add checks that the adapter can recommend setup forecast execution only when the benchmark and method decision allow it, while still creating no forecast or score artifacts itself.

Exit criteria:

- Agents can move from source-handoff guidance to setup benchmark and method-decision guidance without using lower-level CLI surfaces directly.
- The adapter cannot bypass benchmark gates, method decisions, or explicit forecast execution.

Implemented artifacts:

- `spec/agent-envelope.schema.json`
- `spec/agent-adapter-protocol-map.schema.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-unconfirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-confirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-insufficient-confirmed-builder-draft-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-contains-secret-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-unsupported-format-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-oversized-envelope.generated.json`
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-method-gate-leakage-envelope.generated.json`
- `scripts/agent_adapter_dispatcher.py`
- `scripts/build_agent_adapter_fixtures.py`
- `scripts/generate_agent_adapter_protocol_map.py`
- `scripts/ope_mcp_stdio.py`
- `python3 scripts/ope.py agent-call --operation private_setup_method_gate --private-setup-request-id privatesetuprequest-001 --method-gate-case confirmed_builder_draft`
- repository and CLI checks covering confirmed, unconfirmed, insufficient-data, rejected source cases, source-handoff/source-intake/benchmark/method-decision bindings, MCP tool exposure, protocol-map drift, explicit setup forecast recommendation only for the allowed confirmed handoff, and no forecast, score, live-fetch, credential, or public read-record creation

## Milestone 59: Private Setup Forecast Execution Adapter Envelope

Status: Completed.

Goal: let an agent explicitly run the checked setup forecast execution step from an accepted method gate through the adapter surface, while keeping blocked method gates non-generating and preserving all setup bindings in generated forecast artifacts.

Tasks:

- [x] Add a private setup forecast execution adapter operation for checked source-handoff forecast cases.
- [x] Preserve source-handoff, source-intake, benchmark, method-decision, setup-forecast-run, forecast, and question bindings in the payload.
- [x] Return separate envelopes for confirmed accepted handoff, unconfirmed mapping, insufficient data, rejected sources, and leakage cases.
- [x] Add MCP/protocol-map support with explicit approval and no raw private data or credential arguments.
- [x] Add checks that only the confirmed method-gate case can create fixture forecast artifacts and all blocked cases remain non-generating.

Exit criteria:

- Agents can run the explicit checked setup forecast execution step without using lower-level CLI surfaces directly.
- The adapter cannot create forecasts unless source intake, benchmark, method decision, and method-gate records allow it.

Completed outputs:

- `private_setup_forecast_execution` operation in the local dispatcher, envelope schema, protocol-map schema, CLI, and MCP stdio scaffold
- generated forecast-execution envelopes for confirmed, unconfirmed, insufficient-data, secret, unsupported-format, oversized, and leakage cases
- `python3 scripts/ope.py agent-call --operation private_setup_forecast_execution --private-setup-request-id privatesetuprequest-001 --forecast-execution-case confirmed_builder_draft`
- checks covering generated `forecast-1102`, null forecast bindings for blocked cases, preserved setup bindings, MCP/protocol-map exposure, no raw private data or credential arguments, and no resolution/scoring/live-fetch side effects

## Milestone 60: Private Setup Forecast Readback Adapter Examples

Status: Accepted.

Goal: let agents continue from a generated private setup forecast to the existing forecast card, lifecycle bundle, resolution status, and scoring summary adapter reads without guessing which IDs or boundaries apply.

Tasks:

- [x] Add generated adapter envelope examples for reading the source-handoff forecast `forecast-1102` through `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary`.
- [x] Preserve source-handoff setup bindings in the readback payload checks, including setup forecast run, handoff, method gate, benchmark gate, and method decision IDs.
- [x] Add dispatcher and CLI checks showing `agent-call` can read `forecast-1102` with `question-1102` after forecast execution.
- [x] Update protocol-map and agent-adapter guidance to route generated private setup forecasts into normal read operations instead of a private read API.
- [x] Keep quality claims sample-size-blocked and resolution/scoring separate from forecast execution.

Exit criteria:

- Agents can run forecast execution, take the returned forecast ID, and read card, bundle, resolution, and score summaries through existing adapter operations.
- Readback examples do not imply a new hosted API, production adapter runtime, or calibration claim.

Completed outputs:

- generated readback adapter envelopes for `forecast-1102` using `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary`
- dispatcher and CLI checks showing the same `forecast-1102`/`question-1102` IDs work through existing read operations after setup forecast execution
- protocol-map and agent-adapter guidance that tells agents to reuse normal read operations instead of a private setup forecast read API
- checks preserving setup forecast run, source-handoff, method-gate, benchmark, method-decision, resolution, scoring, and sample-size-blocked quality-claim bindings

## Milestone 61: Agent Adapter Fixture Performance Cleanup

Status: Accepted.

Goal: keep the now-larger private setup adapter fixture suite fast and maintainable without changing adapter semantics.

Tasks:

- [x] Cache or share repeated source-handoff forecast-output construction inside adapter fixture generation.
- [x] Reduce duplicated private setup readback assembly in dispatcher and CLI checks while preserving explicit assertions.
- [x] Add a small timing or structure guard if runtime begins to drift.
- [x] Keep generated envelope contents deterministic and schema-bound.

Exit criteria:

- `agent-envelopes`, dispatcher, and CLI checks remain equivalent but do less repeated setup work.
- No adapter operation, schema, readback payload, or claim boundary changes as part of the cleanup.

Completed outputs:

- cached source-handoff forecast output construction for adapter fixture generation
- cache reuse assertion in the agent adapter invariant check
- shared setup forecast readback helpers in dispatcher and CLI smoke checks
- no generated envelope, schema, or adapter contract semantic changes

## Milestone 62: Private Setup Adapter Chain Runbook

Status: Accepted.

Goal: give agents one checked adapter-level runbook for moving from private setup request guidance through source-builder, source-handoff, method-gate, forecast execution, and normal forecast readback.

Tasks:

- [x] Add a compact runbook record that lists the adapter operation sequence for the local-file private setup path.
- [x] Bind each step to existing operation names, required input IDs, expected status, allowed next operation, and stop conditions.
- [x] Cover confirmed, mapping-confirmation, insufficient-data, rejected-source, and generated-forecast readback outcomes.
- [x] Keep the runbook guidance-only and non-executing.

Exit criteria:

- Agents can inspect one adapter-chain runbook before calling setup operations.
- The runbook does not create source, forecast, resolution, scoring, credential, hosted API, or production runtime claims.

Completed outputs:

- `spec/private-setup-adapter-chain-runbook.schema.json`
- `spec/private-setup-adapter-chain-runbook.md`
- `scripts/generate_private_setup_adapter_chain_runbook.py`
- `scripts/check_private_setup_adapter_chain_runbook.py`
- `spec/fixtures/generated/private-setup-adapter-chain/ope-private-setup-adapter-chain-runbook.generated.json`
- `python3 scripts/ope.py private-setup-adapter-runbook`
- docs, release manifest, CLI, and normal check wiring for the adapter-chain runbook

## Milestone 63: Private Setup Adapter Chain Envelope

Status: Accepted.

Goal: expose the checked private setup adapter-chain runbook through the transport-neutral agent adapter and local MCP scaffold so agents can request setup-sequence guidance without using a lower-level CLI command.

Tasks:

- [x] Add a read-only `private_setup_adapter_runbook` adapter operation that returns the generated runbook in the existing envelope format.
- [x] Add schema, dispatcher, MCP stdio, protocol-map, CLI smoke, and generated envelope coverage for the new operation.
- [x] Preserve that the operation is guidance-only and does not execute source-builder, handoff, method-gate, forecast execution, resolution, scoring, or private source access.
- [x] Keep readback guidance routed to normal forecast card, lifecycle bundle, resolution status, and scoring summary operations.

Exit criteria:

- Agents can request the full private setup adapter chain through the same envelope, exit-code, and sanitized-error surface as other adapter calls.
- The new operation adds no source reads, forecast artifacts, scoring artifacts, live fetches, credentials, hosted API, or production runtime claims.

Completed outputs:

- `private_setup_adapter_runbook` operation in the local dispatcher, envelope schema, protocol-map schema, CLI, and MCP stdio scaffold
- `ope_private_setup_adapter_runbook` MCP tool and protocol-map entry
- `spec/fixtures/generated/agent-adapter/ope-agent-private-setup-adapter-runbook-envelope.generated.json`
- `python3 scripts/ope.py agent-call --operation private_setup_adapter_runbook`
- protocol map expanded to thirteen envelope-returning adapter operations plus the separate forecast-run tool
- repository, CLI, protocol-map, MCP, release-manifest, and documentation checks preserving non-execution and normal forecast readback routing

## Milestone 64: Private Source Adapter Guidance Envelope

Status: Accepted.

Goal: expose existing private source adapter capability, outcome, and intake-bridge guidance through the transport-neutral agent adapter so agents can inspect source-kind support before setup without calling lower-level guidance commands.

Tasks:

- [x] Add a read-only adapter operation that returns the private source adapter capability declaration, outcome matrix, and intake bridge as guidance.
- [x] Bind the operation to existing private setup workflow source kinds and existing generated private source adapter records.
- [x] Add dispatcher, MCP stdio, protocol-map, CLI smoke, and generated envelope coverage.
- [x] Preserve that private API, database, and manual-upload adapters remain planned-only and do not execute credentials, live fetches, source reads, source manifests, forecasts, or scores.

Exit criteria:

- Agents can ask OPE what private source kinds are available, planned, approval-gated, unsupported, or unsafe through the same envelope surface as other adapter reads.
- The new operation does not weaken the private setup first-action, source-builder, source-handoff, benchmark, method, or forecast-execution gates.

Completed outputs:

- `private_source_adapter_guidance` operation in the local dispatcher, envelope schema, protocol-map schema, CLI, and MCP stdio scaffold
- `ope_private_source_adapter_guidance` MCP tool and protocol-map entry
- `spec/fixtures/generated/agent-adapter/ope-agent-private-source-adapter-guidance-envelope.generated.json`
- `python3 scripts/ope.py agent-call --operation private_source_adapter_guidance`
- protocol map expanded to fourteen envelope-returning adapter operations plus the separate forecast-run tool
- repository, CLI, protocol-map, MCP, release-manifest, and documentation checks preserving read-only capability/outcome/bridge guidance boundaries

## Milestone 65: Private Source-Kind Selection Examples

Status: Accepted.

Goal: give agents compact checked examples for choosing the next setup operation after reading private source adapter guidance, without executing source reads or weakening setup gates.

Tasks:

- [x] Add fixture examples that map source kinds and guidance outcomes to the next safe adapter operation or stop path.
- [x] Cover local-file, manual-mapping, auto-evidence fixture, planned runtime, unsupported source, unsafe source, and credential-runtime-missing cases.
- [x] Bind every example to the private source adapter guidance envelope, first-action records, and adapter-chain runbook.
- [x] Keep examples non-generating: no source manifests, forecasts, scores, credentials, live fetches, hosted runtime, or production adapter claims.

Exit criteria:

- Agents can see small source-kind choice examples before deciding whether to call source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop.
- The examples remain descriptive guidance and do not replace private setup request routing, source-builder validation, source-handoff confirmation, method gates, or forecast execution.

Completed outputs:

- `spec/private-source-kind-selection-examples.schema.json`
- `spec/private-source-kind-selection-examples.md`
- `spec/fixtures/generated/private-source-kind-selection/ope-private-source-kind-selection-examples.generated.json`
- `scripts/generate_private_source_kind_selection_examples.py`
- `scripts/check_private_source_kind_selection_examples.py`
- `python3 scripts/ope.py private-source-kind-selection`
- repository, CLI, schema, release-manifest, and documentation checks preserving guidance-only source-kind selection boundaries

## Milestone 66: Private Source-Kind Selection Envelope

Status: Accepted.

Goal: expose the checked private source-kind selection examples through the transport-neutral agent adapter and local MCP scaffold so agents can request next-path guidance without lower-level fixture commands.

Tasks:

- [x] Add a read-only `private_source_kind_selection` adapter operation that returns the generated selection examples.
- [x] Bind the operation to the existing private source adapter guidance envelope, first-action records, and adapter-chain runbook.
- [x] Add dispatcher, MCP stdio, protocol-map, CLI smoke, schema, and generated envelope coverage.
- [x] Preserve that the operation is guidance-only and does not run source-builder, source-handoff, fixture evidence, forecast execution, scoring, live fetches, or credential handling.

Exit criteria:

- Agents can ask OPE which private source-kind path to choose through the same envelope surface as other adapter reads.
- The new operation does not weaken request routing, source validation, confirmation, method gates, forecast execution, or planned-runtime boundaries.

Completed outputs:

- `private_source_kind_selection` operation in the local dispatcher, envelope schema, protocol-map schema, CLI, and MCP stdio scaffold
- `ope_private_source_kind_selection` MCP tool and protocol-map entry
- `spec/fixtures/generated/agent-adapter/ope-agent-private-source-kind-selection-envelope.generated.json`
- `python3 scripts/ope.py agent-call --operation private_source_kind_selection`
- protocol map expanded to fifteen envelope-returning adapter operations plus the separate forecast-run tool
- repository, CLI, protocol-map, MCP, release-manifest, and documentation checks preserving source-kind selection as read-only path guidance

## Milestone 67: Source-Kind Selection Query Argument

Status: Accepted.

Goal: let agents request one private source-kind recommendation from the `private_source_kind_selection` operation without parsing the full examples list, while keeping the full list available by default.

Tasks:

- [x] Add an optional `sourceKind` argument to the local dispatcher, protocol map, and MCP tool schema for `private_source_kind_selection`.
- [x] Return the full examples record by default and add a compact selected-example view when `sourceKind` is provided.
- [x] Reject unknown source-kind inputs with sanitized adapter errors that do not execute setup or source reads.
- [x] Keep selected recommendations non-executing and non-generating: no source-builder, source-handoff, fixture evidence, forecasts, scoring, live fetches, credentials, or hosted runtime work.

Exit criteria:

- Agents can ask OPE for a single source-kind path recommendation such as `local_file`, `private_api`, or `unsafe_source` through CLI and MCP.
- The filtered operation remains a read-only guidance surface and does not weaken setup request routing, source validation, confirmation, method gates, forecast execution, or planned-runtime boundaries.

Completed outputs:

- `private_source_kind_selection --source-kind ...` support in the local dispatcher and `python3 scripts/ope.py agent-call`
- optional `sourceKind` protocol-map and MCP tool argument
- compact selected-example payload with `runtimeStatus: selected_example_only`, `requestedSourceKind`, `availableSourceKinds`, and `selectedExample`
- sanitized `bad_request` envelopes for unknown source kinds
- dispatcher, CLI, MCP, protocol-map, runtime-validation, and documentation checks preserving guidance-only boundaries

## Milestone 68: Source-Kind Query Fixture Matrix

Status: Accepted.

Goal: add checked fixture coverage for selected source-kind query outcomes so future adapters can compare full-list, selected-example, and unsupported-source responses without re-deriving behavior from ad hoc CLI smoke checks.

Tasks:

- [x] Generate selected-response examples for the supported source kinds and one unsupported source-kind error envelope.
- [x] Add a small matrix that records expected response shape, exit code, next action, and non-execution boundary for each selected query.
- [x] Validate the matrix against the agent envelope schema and existing source-kind selection examples.
- [x] Document that the matrix is adapter conformance evidence, not execution evidence or source-intake evidence.

Exit criteria:

- Agents and adapter implementers can inspect checked examples for full-list selection, one selected source kind, and an unsupported source kind.
- The matrix preserves the boundary that source-kind selection only recommends the next safe setup path and never creates source, forecast, resolution, scoring, credential, live-fetch, or hosted-runtime artifacts.

Completed outputs:

- `spec/private-source-kind-query-matrix.schema.json`
- `spec/private-source-kind-query-matrix.md`
- `spec/fixtures/generated/private-source-kind-selection/ope-private-source-kind-query-matrix.generated.json`
- `scripts/generate_private_source_kind_query_matrix.py`
- `scripts/check_private_source_kind_query_matrix.py`
- `python3 scripts/ope.py private-source-kind-query-matrix`
- CLI, schema, release-manifest, runtime-validation, and documentation checks preserving query-matrix-as-conformance-evidence boundaries

## Milestone 69: Private Setup Adapter Conformance Matrix

Status: Accepted.

Goal: summarize the checked private setup adapter operation cases in one conformance matrix so agents and future adapters can compare source-builder, source-handoff, method-gate, forecast-execution, and readback response shapes without treating examples as live execution.

Tasks:

- [x] Generate a matrix over private setup adapter operations and representative happy, blocked, rejected, and sanitized-error cases.
- [x] Record expected status, exit code, primary payload shape, forecast-artifact creation permission, and next safe action for each case.
- [x] Bind every matrix row to existing generated envelopes and operation specs instead of creating new semantics.
- [x] Document that the matrix is adapter conformance evidence only and does not execute source reads, setup commands, forecast execution, resolution, or scoring.

Exit criteria:

- Agents can inspect one checked matrix before choosing a private setup adapter call.
- Future MCP/HTTP/queue adapters have a compact local conformance reference for private setup operation behavior.
- The matrix does not broaden OPE claims beyond local fixture and schema-bound adapter behavior.

Completed outputs:

- `spec/private-setup-adapter-conformance-matrix.schema.json`
- `spec/private-setup-adapter-conformance-matrix.md`
- `spec/fixtures/generated/private-setup-adapter-conformance/ope-private-setup-adapter-conformance-matrix.generated.json`
- `scripts/generate_private_setup_adapter_conformance_matrix.py`
- `scripts/check_private_setup_adapter_conformance_matrix.py`
- `python3 scripts/ope.py private-setup-adapter-conformance`
- CLI, schema, release-manifest, runtime-validation, and documentation checks preserving conformance-matrix-as-examples-only boundaries

## Milestone 70: Compact Adapter Conformance Read Surface

Status: Accepted.

Goal: expose a compact agent-readable summary of the private setup adapter conformance matrix so callers can inspect expected operation behavior without loading the full embedded-envelope matrix.

Tasks:

- [x] Define a compact conformance summary schema that references the full matrix and records phase counts, supported operations, artifact-creation boundaries, and sanitized-error coverage.
- [x] Add a read-only local command and adapter operation that return the compact summary through the existing envelope semantics.
- [x] Map the compact summary operation into the local MCP scaffold and protocol map without introducing new forecast, source, resolution, or scoring behavior.
- [x] Keep the full matrix available for implementers while steering normal agents toward the smaller read surface.

Exit criteria:

- Agents can ask OPE for private setup adapter conformance status through a compact `agent-call`/MCP response.
- The read surface references the generated full matrix but does not embed every large envelope by default.
- The operation remains read-only and cannot execute setup calls or create forecast artifacts.

Completed outputs:

- `spec/private-setup-adapter-conformance-summary.schema.json`
- `spec/private-setup-adapter-conformance-summary.md`
- `spec/fixtures/generated/private-setup-adapter-conformance/ope-private-setup-adapter-conformance-summary.generated.json`
- `scripts/generate_private_setup_adapter_conformance_summary.py`
- `scripts/check_private_setup_adapter_conformance_summary.py`
- `python3 scripts/ope.py private-setup-adapter-conformance-summary`
- `python3 scripts/ope.py agent-call --operation private_setup_adapter_conformance_summary`
- `ope_private_setup_adapter_conformance_summary` MCP tool and protocol-map entry
- CLI, schema, release-manifest, runtime-validation, and documentation checks preserving compact-summary-as-read-only-boundary behavior

## Milestone 71: Adapter Read Surface Size Guard

Status: Accepted.

Goal: keep routine agent adapter reads compact and predictable as conformance fixtures grow, so agents can rely on small guidance surfaces before loading heavyweight implementation evidence.

Tasks:

- [x] Add explicit byte-size and payload-shape checks for the compact conformance summary envelope versus the full private setup adapter conformance matrix.
- [x] Document when agents should use the compact summary, full matrix, and generated envelope fixtures.
- [x] Add CLI and adapter checks that preserve `maxBytes` behavior for compact summary reads and return sanitized size-limit errors when callers request oversized responses.
- [x] Update release and hardening checks so future adapter read surfaces cannot silently embed large matrices by default.

Exit criteria:

- Routine agents have a checked compact read path with a documented size budget.
- Implementers can still inspect the full matrix, but full conformance evidence is opt-in rather than the default agent-call path.
- Size guard failures remain sanitized and do not execute setup calls, source reads, forecasts, resolution, or scoring.

Completed outputs:

- `sizeBudget` in `spec/private-setup-adapter-conformance-summary.schema.json`
- compact summary payload budget, compact agent-envelope budget, and full matrix reference budget in `spec/fixtures/generated/private-setup-adapter-conformance/ope-private-setup-adapter-conformance-summary.generated.json`
- adapter envelope fixture refresh for `private_setup_adapter_conformance_summary`
- checks for compact payload shape, matrix-size contrast, declared `maxBytes` success, undersized `response_too_large`, and hardening guardrails
- documentation in `spec/private-setup-adapter-conformance-summary.md`

## Milestone 72: Resolution Runtime Reliability And Provenance

Status: Accepted.

Goal: make every transit forward-run, scheduler tick, resolver attempt, live capture, and shutdown inspectable, retryable, and provenance-bound before improving data-source quality or forecasting sophistication.

Tasks:

- [x] Add agent adapter and readback surfaces for resolution jobs and scheduler status.
- [x] Add a runtime failure taxonomy covering source availability, empty sources, decode failures, schedule-join failures, coverage gaps, resolver failures, stale state, invalid state, network timeouts, and rate limits.
- [x] Add planned retryability and next-action fields for runtime failures: `retryable`, `retryAfter`, `nextAction`, and sanitized diagnostics.
- [x] Add a provenance ledger for forecast and resolution runtime actions, including command, timestamp, source provider, source role, forecast-time versus resolution-only classification, allowed artifact paths or hashes, and diagnostics.
- [x] Preserve the boundary that outcome data is resolution-only and must not enter forecast-time provenance.
- [x] Keep live captures local and opt-in until source policy, retention, freshness, and failure behavior are reliable.

Exit criteria:

- Agents can inspect pending jobs, last scheduler tick, last shutdown, due jobs, failed attempts, and recommended next action without reading internal files.
- Every runtime failure has a sanitized category, retryability decision, and next action.
- Runtime provenance is enough to explain what command ran, which source it touched, when it ran, what artifacts were produced, and whether the evidence was forecast-time or resolution-only.
- HSL/source optimization, production live connector claims, richer methods, and calibration claims remain deferred until the current loop is reliable and auditable.

Completed outputs:

- `spec/resolution-runtime-reliability.schema.json`
- `spec/resolution-runtime-reliability.md`
- `scripts/generate_resolution_runtime_reliability.py`
- `scripts/check_resolution_runtime_reliability.py`
- checked fixture at `spec/fixtures/generated/resolution-runtime-reliability/resolution-runtime-reliability.generated.json`
- CLI command `python3 scripts/ope.py resolution-runtime-reliability`
- run-check, CLI, release-manifest, and schema-validation wiring for the new read model
- provenance rows that keep resolution outcome evidence out of forecast-time provenance and keep live captures ignored/local

## Milestone 73: Resolution Jobs Agent Adapter And Scheduler Readback

Status: Accepted.

Goal: expose resolution jobs, scheduler state, last tick, last shutdown, and retry guidance through the transport-neutral agent adapter and local MCP scaffold without forcing agents to inspect local files or terminal output.

Tasks:

- [x] Add read-only adapter operations for resolution job registry and scheduler status.
- [x] Return compact payloads for pending, due, resolved, invalid, failed, and empty queues.
- [x] Include last scheduler tick, last shutdown reason, log path, execution mode, and next recommended action.
- [x] Add sanitized error envelopes for missing live workspace, unreadable state files, malformed scheduler logs, and oversized readbacks.
- [x] Map the operations into the local MCP scaffold and protocol map while preserving local-only runtime claims.

Exit criteria:

- Agents can decide whether to wait, execute a resolver, inspect a failure, or read resolved outputs through `agent-call` or MCP.
- Scheduler and resolution readback remain read-only and cannot execute resolvers, fetch live sources, create forecasts, or create scores.

Completed outputs:

- `resolution_jobs` agent adapter operation and `ope_resolution_jobs` MCP tool for the checked resolution job registry.
- `resolution_scheduler_status` agent adapter operation and `ope_resolution_scheduler_status` MCP tool for the checked scheduler status readback.
- compact scheduler payload fields for `lastTick`, `lastShutdown`, `logPath`, `executionMode`, `queueStatusReadbacks`, and `nextRecommendedAction`.
- generated agent-envelope fixtures and protocol-map entries for the two read-only operations.
- CLI, dispatcher, MCP, schema, and adapter invariant checks for read-only behavior and resolver non-execution.
- generated sanitized error-envelope examples for missing live workspaces, unreadable state files, malformed scheduler logs, and oversized scheduler readbacks.

## Milestone 74: Public Transport Forward-Run Corpus

Status: Accepted.

Goal: run and preserve repeated comparable HSL morning-peak forward predictions so OPE has real resolved examples before making method-quality or calibration claims.

Tasks:

- [x] Define the minimum comparable-window policy for the HSL public transport beta corpus.
- [x] Add a local corpus index over forward-run states, forecast artifacts, resolution records, scoring reports, and excluded/ambiguous runs.
- [x] Preserve one forecast-before-window, one resolution-after-window, and one score-against-baseline record per comparable run.
- [x] Add exclusion reasons for ambiguous, annulled, low-coverage, invalid-window, feed-unavailable, and non-comparable runs.
- [x] Add a checked read surface that reports corpus count, resolved count, excluded count, and claim boundary.

Exit criteria:

- OPE can show how many comparable public transport windows have been forecast, resolved, scored, or excluded.
- The corpus is useful for baseline comparison but still blocks calibration claims until the declared sample threshold is met.

Completed outputs:

- `spec/transit-forward-run-corpus.schema.json`
- `spec/transit-forward-run-corpus.md`
- `scripts/generate_transit_forward_run_corpus.py`
- `scripts/check_transit_forward_run_corpus.py`
- checked fixture at `spec/fixtures/generated/transit-forward-run-corpus/transit-forward-run-corpus.generated.json`
- CLI command `python3 scripts/ope.py transit-forward-run-corpus`
- schema-validation, run-check, CLI, and release-manifest wiring for the corpus index
- exclusion examples for `ambiguous`, `annulled`, `low_coverage`, `invalid_window`, `feed_unavailable`, and `non_comparable`

## Milestone 75: Baseline Track Record And Calibration Gate

Status: Accepted.

Goal: turn the repeated forward-run corpus into a baseline-first track record that reports performance only when enough comparable outcomes exist.

Tasks:

- [x] Generate track-record summaries from the public transport forward-run corpus.
- [x] Report Brier score, baseline score, baseline lift, resolved sample size, excluded sample size, and horizon/window coverage.
- [x] Add calibration summaries only when the minimum comparable sample threshold is met.
- [x] Keep below-threshold outputs explicit: `not_enough_resolved_comparable_outcomes`.
- [x] Add checks that one-off forward runs cannot be treated as calibration evidence.

Exit criteria:

- Agents can inspect whether OPE has enough resolved outcomes to make any quality or calibration claim.
- Public docs and release manifests continue to block live calibration claims until the corpus threshold is met.

Completed outputs:

- `spec/transit-baseline-track-record-gate.schema.json`
- `spec/transit-baseline-track-record-gate.md`
- `scripts/generate_transit_baseline_track_record_gate.py`
- `scripts/check_transit_baseline_track_record_gate.py`
- checked fixture at `spec/fixtures/generated/transit-baseline-track-record-gate/transit-baseline-track-record-gate.generated.json`
- CLI command `python3 scripts/ope.py transit-track-record-gate`
- Brier, baseline, lift, sample-size, and horizon/window coverage readback over the checked transit forward-run corpus
- explicit below-threshold calibration gate with `calibrationSummary: null` and `not_enough_resolved_comparable_outcomes`
- schema-validation, run-check, CLI, docs, and release-manifest wiring for the gate

## Milestone 76: Forecasting Method Options For MVP

Status: Accepted.

Goal: define and compare the first MVP method choices after the baseline loop is reliable, while keeping richer methods disabled until benchmark and corpus evidence support them.

Tasks:

- [x] Keep baseline-only execution as the default method for early public transport corpus runs.
- [x] Add a transparent deterministic weather-adjustment candidate only as benchmarked, claim-bounded method evidence.
- [x] Add a historical-conditioned statistical method candidate once enough resolved corpus rows exist for weather, weekday, season, and service-window buckets.
- [x] Extend method comparison to public transport delay runs without using same-window outcome data as forecast evidence.
- [x] Keep trained ML, ensemble, retrieval-assisted, and external-reference methods proposed-only until clean benchmark evidence exists.

Exit criteria:

- OPE can explain why a public transport run stayed baseline-only or why a simple non-baseline method became eligible.
- Any non-baseline public transport method must show comparable baseline lift and anti-leakage checks before selection.

Completed outputs:

- `spec/transit-method-options.schema.json`
- `spec/transit-method-options.md`
- `scripts/generate_transit_method_options.py`
- `scripts/check_transit_method_options.py`
- checked fixture at `spec/fixtures/generated/transit-method-options/transit-method-options.generated.json`
- CLI command `python3 scripts/ope.py transit-method-options`
- baseline-default selection readback with `transitmethod-100`
- evidence-only transparent weather-adjustment method with Brier `0.4489`, baseline score `0.5625`, and lift `0.1136`
- proposed-only historical-conditioned, trained ML, retrieval-assisted, ensemble, and external-reference method options
- anti-leakage boundary that keeps same-window transit outcomes out of forecast-time method evidence
- schema-validation, run-check, CLI, docs, and release-manifest wiring for the method-options gate

## Milestone 77: Policy-Bound Live Evidence Promotion

Status: Accepted.

Goal: allow selected ignored local live captures to become forecast-time evidence only through an explicit source policy, freshness check, leakage check, and provenance binding.

Tasks:

- [x] Define the intake gate for promoting local live draft captures into forecast-time source sets.
- [x] Require source policy, capture timestamp, forecast close time, freshness, retention, and source role checks before promotion.
- [x] Reject post-close or resolution-only captures as forecast-time evidence.
- [x] Preserve raw local artifacts as ignored workspace files while binding sanitized normalized records into OPE artifacts.
- [x] Add readback that distinguishes committed fixtures, local live drafts, promoted forecast-time evidence, and resolution-only evidence.

Exit criteria:

- OPE can use approved live captures as forecast-time evidence without weakening provenance or leakage boundaries.
- Live connector output remains non-production and local until a later runtime milestone explicitly changes that claim.

Completed outputs:

- `spec/transit-live-evidence-promotion.schema.json`
- `spec/transit-live-evidence-promotion.md`
- `scripts/generate_transit_live_evidence_promotion.py`
- `scripts/check_transit_live_evidence_promotion.py`
- checked promotion fixture at `spec/fixtures/generated/transit-live-evidence-promotion/transit-live-evidence-promotion.generated.json`
- checked sanitized source-set fixture at `spec/fixtures/generated/transit-live-evidence-promotion/weather-transit-delays-promoted-source-set.generated.json`
- CLI command `python3 scripts/ope.py transit-live-evidence-promotion`
- readback for committed fixtures, local live drafts, promoted forecast-time evidence, and resolution-only evidence
- source-policy, freshness, retention, source-role, leakage, and provenance checks for the promoted weather evidence case
- explicit rejection examples for post-close weather captures and resolution-only HSL TripUpdates captures
- schema-validation, run-check, CLI, docs, and release-manifest wiring for the promotion gate

## Milestone 78: External Connector Intake MVP

Status: Accepted.

Goal: make the external connector vision usable for MVP: agent-built connectors can live outside OPE core if they hand OPE a sanitized source-adapter output that passes source intake and method gates.

Tasks:

- [x] Add a checked intake path from source-adapter output into source manifest builder/source intake without requiring connector code inside OPE core.
- [x] Validate adapter-provided manifests, mappings, provenance summaries, source roles, freshness, and leakage boundaries.
- [x] Route accepted adapter outputs to method gates and blocked outputs to explicit next actions.
- [x] Keep credentials, live fetching, connector execution, and arbitrary parsing outside OPE core for MVP.
- [x] Add adapter conformance examples for accepted, needs-confirmation, insufficient-data, rejected, and unsafe connector outputs.

Exit criteria:

- Agents can prepare a custom connector outside OPE and hand OPE a standard source-adapter output for forecast setup.
- OPE can accept or reject that output without taking responsibility for connector execution or credential handling.

Completed outputs:

- `spec/source-adapter-intake.schema.json`
- `spec/source-adapter-intake.md`
- checked fixtures under `spec/fixtures/generated/source-adapter-intake/`
- `scripts/generate_source_adapter_intake.py`
- `scripts/check_source_adapter_intake.py`
- CLI command `python3 scripts/ope.py source-adapter-intake`
- five conformance cases: accepted, needs-confirmation, insufficient-data, rejected, and unsafe-blocked
- source-intake, setup-benchmark, and setup-method-decision bindings for all safe handoff cases
- schema-validation, run-check, CLI, docs, and release-manifest wiring for the external connector intake boundary

## Milestone 79: Local Private Setup MVP Orchestrator

Status: Accepted.

Goal: provide one local agent-facing orchestration path from a private setup request to source intake, method decision, forecast execution, and normal readback for approved local or adapter-provided sources.

Tasks:

- [x] Add a local orchestrator that chains existing checked setup phases only when each gate allows the next step.
- [x] Support local files and source-adapter outputs as MVP source kinds.
- [x] Keep private API, database, manual upload, and credentialed connectors planned-only unless represented through accepted adapter outputs.
- [x] Return one compact run summary with setup request, source intake, method decision, forecast IDs, card, bundle, resolution status, score status, and next action.
- [x] Add blocked summaries for missing approval, unconfirmed mappings, insufficient data, rejected sources, failed method gates, and response-too-large reads.

Exit criteria:

- Agents can run one local OPE setup workflow for approved source inputs without manually chaining every lower-level command.
- The orchestrator cannot bypass source intake, mapping confirmation, benchmark gates, method decisions, or explicit forecast execution boundaries.

Completed outputs:

- `spec/private-setup-orchestrator.schema.json`
- `spec/private-setup-orchestrator.md`
- checked fixture under `spec/fixtures/generated/private-setup-orchestrator/`
- `scripts/generate_private_setup_orchestrator.py`
- `scripts/check_private_setup_orchestrator.py`
- CLI command `python3 scripts/ope.py private-setup-orchestrator`
- eight run summaries: local-file confirmed, source-adapter accepted, missing approval, unconfirmed mapping, insufficient data, rejected source, unsafe source, and response-too-large
- schema-validation, run-check, CLI, docs, and release-manifest wiring for the local private setup MVP orchestrator summary

## Milestone 80: MVP Release Surface And Claim Review

Status: Accepted.

Goal: package the local MVP as a clear agent-native release surface with repeatable checks, examples, docs, and honest claim boundaries.

Tasks:

- [x] Add a compact MVP runbook covering setup, forecast, recalculation, resolution, scoring, corpus readback, and failure recovery.
- [x] Add a release manifest section that labels the MVP local runtime surface and lists non-goals.
- [x] Add end-to-end smoke checks for the MVP happy path and representative blocked/failure paths.
- [x] Document minimum machine-readable interfaces for CLI, agent-call, and MCP use.
- [x] Keep HTTP, queue, hosted service, arbitrary private API/database parsing, broad provider optimization, and live calibration claims out of MVP.

Exit criteria:

- A developer or agent can install the repo, run the local MVP loop, inspect forecast artifacts, resolve outcomes, score them, and understand exactly what is and is not claimed.
- The MVP is release-checkable without live network dependency in normal checks.

Completed outputs:

- `spec/mvp-local-runtime.md`
- `mvpLocalRuntime` section in `spec/fixtures/generated/release-manifest.generated.json`
- release-manifest schema support for MVP local runtime surface, smoke checks, machine interfaces, blocked paths, and claim review
- `scripts/check_mvp_release_surface.py`
- normal check wiring for the MVP release-surface smoke check
- docs, roadmap, and decision-log wiring for the local MVP release boundary

## Milestone 81: Agent Pilot Validation Pack

Status: Accepted.

Goal: validate the local MVP with realistic agent/developer setup sessions before expanding runtime scope.

Tasks:

- [x] Add a compact pilot protocol for 3-5 agent/developer setup sessions.
- [x] Add task scenarios that ask an agent to set up an OPE-compatible engine from connected source data.
- [x] Add a feedback schema for comprehension, trust, task completion, and claim-boundary understanding.
- [x] Add a rubric for forecast-card, lifecycle-bundle, source-intake, and blocked-path comprehension.
- [x] Add checked example pilot notes or transcript summaries without storing private data.

Exit criteria:

- OPE has a repeatable way to test whether a developer can trust the local MVP output enough for agent decision support.
- Pilot evidence can distinguish usability gaps from missing runtime features.

Completed outputs:

- `spec/agent-pilot-validation.md`
- `spec/agent-pilot-validation.schema.json`
- checked fixture under `spec/fixtures/generated/agent-pilot-validation/`
- CLI command `python3 scripts/ope.py agent-pilot-validation`
- `scripts/check_agent_pilot_validation.py`
- normal check, release manifest, docs, roadmap, and decision-log wiring for the pilot validation pack

## Milestone 82: Local Usage And Trace Events

Status: Accepted.

Goal: make local MVP usage measurable without hosted telemetry.

Tasks:

- [x] Add a schema-bound local event log for CLI, `agent-call`, MCP, setup, forecast-run, readback, blocked path, and release-surface smoke events.
- [x] Add local trace summaries for elapsed time, command outcome, record binding, response size, and sanitized error class.
- [x] Add aggregate readbacks for agent forecast completion rate, read success rate, and blocked-path frequency.
- [x] Keep telemetry opt-in or local-only, with no credential, private row, prompt, or raw source capture.
- [x] Add checks that normal release runs remain deterministic and offline.

Exit criteria:

- The product metrics in `PRODUCT.md` have a local measurement surface that agents and developers can inspect.
- Usage instrumentation does not weaken privacy, source, or claim boundaries.

Completed outputs:

- `spec/local-usage-trace.md`
- `spec/local-usage-trace.schema.json`
- checked fixture under `spec/fixtures/generated/local-usage-trace/`
- CLI command `python3 scripts/ope.py local-usage-trace`
- `scripts/check_local_usage_trace.py`
- normal check, release manifest, docs, roadmap, and decision-log wiring for the local usage trace boundary

## Milestone 83: Public Transit Corpus Growth Loop

Status: Accepted.

Goal: grow comparable public transit forward-run evidence toward real track-record and calibration thresholds.

Tasks:

- [x] Add an append-only corpus update command for new resolved transit forward runs.
- [x] Add due-run and post-resolution checklists that preserve forecast-time versus resolution-time evidence boundaries.
- [x] Add an exclusion ledger for missing outcomes, stale evidence, leakage risk, post-close sources, and incomparable windows.
- [x] Add a progress readback toward track-record and calibration sample thresholds.
- [x] Keep quality, calibration, and method-performance claims blocked until thresholds and clean evidence support them.

Exit criteria:

- OPE can repeatedly add comparable resolved transit runs without manual corpus editing.
- Agents can see whether the public beta wedge is moving toward or away from claim-ready evidence.

Completed outputs:

- `spec/transit-corpus-growth-loop.schema.json`
- `spec/transit-corpus-growth-loop.md`
- `scripts/generate_transit_corpus_growth_loop.py`
- `scripts/check_transit_corpus_growth_loop.py`
- checked fixture at `spec/fixtures/generated/transit-corpus-growth/transit-corpus-growth-loop.generated.json`
- CLI command `python3 scripts/ope.py transit-corpus-growth`
- six candidate classifications: append-ready comparable resolved, missing outcome, stale evidence, leakage risk, post-close source, and incomparable window
- due-run checklist, post-resolution checklist, exclusion ledger, threshold progress readback, and non-mutating execution boundary
- schema-validation, run-check, CLI, docs, release-manifest, and decision-log wiring for the checked corpus growth loop

## Milestone 84: Source Quality And Mapping Confidence

Status: Accepted.

Goal: help agents understand whether connected data is merely accepted or actually useful for forecasting.

Tasks:

- [x] Add source-quality and mapping-confidence records over freshness, coverage, role fit, entity scope, leakage risk, missingness, and outcome availability.
- [x] Bind source-quality readbacks to source-builder, source-adapter intake, source-intake reports, and setup method decisions.
- [x] Add guidance for when to confirm mappings, collect more data, replace sources, or proceed to method gates.
- [x] Add checks that source quality cannot by itself create forecast, score, calibration, or production-readiness claims.
- [x] Add compact agent-facing summaries that fit readback size budgets.

Exit criteria:

- Agents can explain why a source is forecast-usable, needs confirmation, needs more data, or should be rejected.
- Source quality improves setup trust without broadening into arbitrary private parsing.

Completed outputs:

- `spec/source-quality-mapping-confidence.schema.json`
- `spec/source-quality-mapping-confidence.md`
- `scripts/generate_source_quality_mapping_confidence.py`
- `scripts/check_source_quality_mapping_confidence.py`
- checked fixture at `spec/fixtures/generated/source-quality-mapping-confidence/weather-logistics-source-quality-mapping-confidence.generated.json`
- CLI command `python3 scripts/ope.py source-quality`
- seven source-quality cases: builder draft, accepted intake, partial baseline-only intake, needs-confirmation intake, insufficient adapter data, rejected intake, and unsafe adapter output
- freshness, coverage, role-fit, entity-scope, leakage-risk, missingness, outcome-availability, mapping-confidence, compact-readback, and non-generating execution-boundary checks
- schema-validation, run-check, CLI, docs, release-manifest, and decision-log wiring for the checked source-quality read model

## Milestone 85: One Narrow Real Source Runtime

Status: Accepted.

Goal: add one carefully bounded non-fixture source runtime based on pilot evidence, not broad connector ambition.

Tasks:

- [x] Choose one narrow source runtime from pilot evidence, such as approved local SQLite, approved HTTP JSON, or watched local folder input.
- [x] Add explicit caller approval, path/endpoint allow-listing, size limits, source-policy binding, and sanitized diagnostics.
- [x] Route accepted runtime output through source manifest, mapping, source intake, benchmark gate, method decision, and explicit forecast execution.
- [x] Add blocked examples for missing approval, credentials, unsafe locations, oversized responses, schema mismatch, and leakage indicators.
- [x] Keep arbitrary private API/database parsing, credential storage, live fetching, hosted runtime, and production connector claims out of scope.

Exit criteria:

- One real source runtime can produce a checked forecast card through the existing gates.
- The runtime proves a repeatable pattern without implying general private-source support.

Completed outputs:

- `spec/local-source-runtime.schema.json`
- `spec/local-source-runtime.md`
- `scripts/generate_local_source_runtime.py`
- `scripts/check_local_source_runtime.py`
- checked fixture at `spec/fixtures/generated/local-source-runtime/weather-logistics-local-source-runtime.generated.json`
- CLI command `python3 scripts/ope.py local-source-runtime`
- one accepted approved-local-folder case binding to `forecast-1102`
- blocked examples for missing approval, credential-like fields, unsafe path, oversized file, unsupported schema, and leakage indicator
- source-policy binding, path allow-list, size limit, sanitized diagnostics, non-goal boundary, schema-validation, run-check, CLI, docs, release-manifest, and decision-log wiring

## Milestone 86: Developer Adoption Surface

Status: Accepted.

Goal: make the local MVP easier for developers and agents to try, understand, and integrate.

Tasks:

- [x] Add a compact quickstart from clone to first forecast card and lifecycle bundle.
- [x] Add one complete example scenario for local source setup, forecast, readback, resolution, scoring, and claim review.
- [x] Add integration notes for CLI, `agent-call`, and MCP stdio with minimum expected inputs and outputs.
- [x] Add release notes that state what is implemented, what is fixture-only, and what remains non-goal.
- [x] Consider generated language-specific types only if pilot/adoption evidence shows they reduce setup friction.

Exit criteria:

- A new developer or agent can reach a valid forecast card quickly and understand the product boundaries.
- Adoption work improves time-to-first-forecast-card without overstating runtime maturity.

Completed outputs:

- `spec/developer-adoption-surface.schema.json`
- `spec/developer-adoption-surface.md`
- `scripts/generate_developer_adoption_surface.py`
- `scripts/check_developer_adoption_surface.py`
- checked fixture at `spec/fixtures/generated/developer-adoption/ope-developer-adoption-surface.generated.json`
- CLI command `python3 scripts/ope.py developer-adoption`
- quickstart from Python setup to local checks, approved local runtime, forecast card, lifecycle bundle, and claim gate
- complete scenario from local setup through runtime gate, forecast readback, lifecycle bundle, resolution/scoring, and claim review
- CLI, `agent-call`, and MCP stdio integration notes with boundaries
- release-note sections for implemented, fixture-only, and non-goal surfaces, plus a deferred generated-types decision
- schema-validation, run-check, CLI, docs, release-manifest, MVP-smoke, and decision-log wiring for the checked developer adoption surface

## Milestone 87: Expansion Readiness Gate

Status: Accepted.

Goal: prevent post-MVP expansion from outrunning pilot, usage, corpus, and adoption evidence.

Tasks:

- [x] Add a checked gate over hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types.
- [x] Bind the gate to release manifest, developer adoption, pilot validation, usage trace, transit corpus growth, transit track-record, and local source runtime evidence.
- [x] Distinguish met local MVP evidence from synthetic-only pilot evidence, below-threshold corpus evidence, and explicit non-goal blockers.
- [x] Add a recommended post-MVP sequence that starts with real pilot sessions and corpus growth before hosted or broader runtime work.
- [x] Keep the gate read-only: no hosted runtime, live fetch, private source execution, artifact creation, runtime type generation, or quality claim.

Exit criteria:

- Agents and maintainers can see why major expansion paths are blocked or deferred.
- The next roadmap work is evidence-gathering and corpus growth, not premature production-runtime construction.

Completed outputs:

- `spec/expansion-readiness-gate.schema.json`
- `spec/expansion-readiness-gate.md`
- `scripts/generate_expansion_readiness_gate.py`
- `scripts/check_expansion_readiness_gate.py`
- checked fixture at `spec/fixtures/generated/expansion-readiness/ope-expansion-readiness-gate.generated.json`
- CLI command `python3 scripts/ope.py expansion-readiness`
- five expansion options: hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types
- evidence bindings over release manifest, developer adoption, agent pilot validation, pilot evidence ledger, local usage trace, transit corpus growth, transit track-record gate, and approved local-folder runtime
- schema-validation, run-check, CLI, docs, release-manifest, MVP-smoke, and decision-log wiring for the checked expansion readiness gate

## Milestone 88: Pilot Evidence Ledger

Status: Accepted.

Goal: give real pilot sessions a safe sanitized evidence intake path before post-MVP expansion decisions.

Tasks:

- [x] Add a checked pilot evidence ledger for sanitized session summaries, dimension scores, friction classes, and expansion signals.
- [x] Add intake examples for accepted sanitized summaries, notes needing redaction, raw transcript blockers, private data blockers, and claim-boundary confusion.
- [x] Bind the ledger to the pilot validation pack, developer adoption surface, release manifest, and expansion-readiness gate.
- [x] Keep checked examples from counting as real pilot evidence or unblocking hosted runtime, broader private-source runtime, generated types, stronger methods, or quality claims.
- [x] Add CLI, normal-check, release-manifest, MVP-smoke, docs, and decision-log wiring.

Exit criteria:

- Real pilot sessions have a checked repository-safe format for sanitized summaries.
- Raw transcripts, private data, credentials, prompt logs, and participant identity are blocked before aggregation.
- Expansion remains blocked until enough real sanitized sessions are recorded.

Completed outputs:

- `spec/pilot-evidence-ledger.schema.json`
- `spec/pilot-evidence-ledger.md`
- `scripts/generate_pilot_evidence_ledger.py`
- `scripts/check_pilot_evidence_ledger.py`
- checked fixture at `spec/fixtures/generated/pilot-evidence/ope-pilot-evidence-ledger.generated.json`
- CLI command `python3 scripts/ope.py pilot-evidence`
- five intake cases: accepted sanitized summary, needs redaction, raw transcript blocked, private data blocked, and claim-boundary confusion
- aggregate summary with accepted real session count `0`, target session count `5`, blocked-case count `2`, and expansion evidence still not ready
- expansion-readiness binding that keeps post-MVP runtime and type-generation work blocked pending real pilot evidence

## Milestone 89: Pilot Session Packet

Status: Accepted.

Goal: give agents and moderators one checked way to run real local MVP pilot sessions and produce ledger-ready sanitized summaries.

Tasks:

- [x] Add a checked pilot session packet that binds the pilot validation tasks to the pilot evidence ledger.
- [x] Add task cards, moderator checklist, participant brief, session steps, and capture fields for the five existing pilot scenarios.
- [x] Add a sanitized evidence template and required sanitization review before any ledger submission.
- [x] Add stop conditions for raw transcripts, private rows, credentials, participant identity, and quality/hosted-runtime claim confusion.
- [x] Keep the packet read-only: it must not run sessions, write ledger rows, store raw/private data, create forecast artifacts, fetch live data, or unblock expansion.

Exit criteria:

- A real pilot session can start from a checked task card and end with a safe summary shape ready for `pilot-evidence`.
- Moderators have explicit stop conditions before private or raw notes enter repository evidence.
- The packet itself records zero real sessions and does not change expansion readiness.

Completed outputs:

- `spec/pilot-session-packet.schema.json`
- `spec/pilot-session-packet.md`
- `scripts/generate_pilot_session_packet.py`
- `scripts/check_pilot_session_packet.py`
- checked fixture at `spec/fixtures/generated/pilot-session-packet/ope-pilot-session-packet.generated.json`
- CLI command `python3 scripts/ope.py pilot-session-packet`
- five task cards over local setup readback, accepted adapter output, unsafe source block, forecast-run readback, and claim-gate readback
- sanitization review with seven required checks and a ledger-ready summary template
- release-manifest, MVP-smoke, CLI, docs, roadmap, and decision-log wiring for the checked pilot collection packet

## Milestone 90: Pilot Summary Intake Validator

Status: Accepted.

Goal: classify sanitized real-session pilot summaries before they can be reviewed for the pilot evidence ledger.

Tasks:

- [x] Add a checked summary intake classifier that binds the pilot validation pack, pilot evidence ledger, and pilot session packet.
- [x] Add ledger-ready, claim-confusion, redaction-needed, raw-transcript-blocked, private-data-blocked, and claim-overreach-blocked examples.
- [x] Add decision rules for accepting, redacting, or blocking submitted summaries before repository storage.
- [x] Keep the classifier read-only: it must not run sessions, write ledger rows, record real sessions, store raw/private data, create artifacts, fetch live data, or unblock expansion.
- [x] Add CLI, normal-check, release-manifest, MVP-smoke, docs, roadmap, and decision-log wiring.

Exit criteria:

- A moderator can tell whether a sanitized session summary is ledger-ready, needs redaction, or must be blocked.
- Raw transcripts, private rows, credentials, participant identity, and quality/hosted-runtime overclaims are stopped before ledger review.
- The classifier records zero real sessions and writes zero ledger rows.

Completed outputs:

- `spec/pilot-summary-intake.schema.json`
- `spec/pilot-summary-intake.md`
- `scripts/generate_pilot_summary_intake.py`
- `scripts/check_pilot_summary_intake.py`
- checked fixture at `spec/fixtures/generated/pilot-summary-intake/ope-pilot-summary-intake.generated.json`
- CLI command `python3 scripts/ope.py pilot-summary-intake`
- six intake cases: ledger-ready local setup summary, ledger-ready claim-confusion product signal, redaction-needed source detail, blocked raw transcript, blocked private rows, and blocked quality claim
- summary with accepted ledger-ready count `2`, needs-redaction count `1`, blocked count `3`, real sessions recorded `0`, and ledger rows written `0`
- release-manifest, MVP-smoke, CLI, docs, roadmap, and decision-log wiring for the checked intake classifier

## Milestone 91: Repeating Prediction Setup Contract

Status: Accepted.

Goal: define the contract that lets an agent set up repeated forecasts without inventing shell loops or scheduler semantics.

Tasks:

- [x] Add a repeating prediction setup schema and spec that binds domain setup, source policy, forecast template, resolution policy, schedule policy, end conditions, and claim boundaries.
- [x] Support flexible schedule policies: fixed count, until date, open-ended, every interval, selected weekdays/windows, and threshold-targeted runs such as "run until 100 comparable resolved outcomes."
- [x] Support interval durations beyond daily runs, including hourly, multi-hour, daily, weekly, and custom ISO-8601-like duration intervals, while keeping timezone and close-time rules explicit.
- [x] Add a post-calibration policy with at least `stop`, `continue`, `pause_then_resume_after`, and `start_next_cycle_after` options so a setup can run without a count and restart after a configured delay once calibration is reached.
- [x] Require forecast-before-close, resolve-after-horizon, source-policy, and resolution-only evidence boundaries for every generated run.
- [x] Add examples for a 100-run daily transit calibration campaign, an hourly short-horizon campaign, a weekly until-date campaign, and an open-ended campaign that restarts after calibration.
- [x] Keep the contract local-first and transport-neutral: no hosted scheduler, OS scheduler, cron file, credentials, or live quality claim.

Exit criteria:

- An agent can read one setup record and know when the next forecast should be created, when it should be resolved, when to stop, and what happens after calibration is reached.
- A campaign can be finite, date-bounded, interval-based, threshold-targeted, or open-ended without changing the forecast artifact contracts.

Completed outputs:

- `spec/repeating-prediction-setup.schema.json`
- `spec/repeating-prediction-setup.md`
- `scripts/generate_repeating_prediction_setup.py`
- `scripts/check_repeating_prediction_setup.py`
- checked fixture at `spec/fixtures/generated/repeating-prediction-setup/ope-repeating-prediction-setup.generated.json`
- CLI command `python3 scripts/ope.py repeating-prediction-setup`
- checked examples for finite, until-date, interval, open-ended, selected weekday/window, calibration-threshold, and post-calibration restart policies
- post-calibration policies for `stop`, `continue`, `pause_then_resume_after`, and `start_next_cycle_after`
- release-manifest, CLI, docs, roadmap, and decision-log wiring for the checked non-executing recurrence contract

## Milestone 92: Local Prediction Campaign Manifest

Status: Accepted.

Goal: give agents one local campaign state file that records a repeating prediction setup, unique run identities, planned windows, and resume-safe progress.

Tasks:

- [x] Add a campaign manifest schema that wraps a repeating prediction setup with local runtime state.
- [x] Generate unique campaign, cycle, run, question, forecast, resolution, and scoring IDs instead of reusing fixture IDs across live runs.
- [x] Reserve ignored local campaign state paths under `.ope/live/prediction-campaigns/` with sanitized relative paths and no credentials; normal checks do not write those paths.
- [x] Add a dry-run planner that expands the next N candidate runs without fetching live sources or creating forecast artifacts.
- [x] Add duplicate prevention for already planned service dates/windows and explicit handling for skipped, missed, canceled, failed, and manually stopped runs.
- [x] Preserve source-policy and claim-boundary metadata at campaign, cycle, and run level.

Exit criteria:

- An agent can start or inspect a campaign without knowing OPE's internal file layout.
- The campaign manifest is resumable and can answer "what is planned, what already ran, what is due, and what is blocked?"

Expected outputs:

- `spec/prediction-campaign-manifest.schema.json`
- `spec/prediction-campaign-manifest.md`
- `python3 scripts/ope.py prediction-campaign plan`
- `python3 scripts/ope.py prediction-campaign status`

Completed outputs:

- `spec/prediction-campaign-manifest.schema.json`
- `spec/prediction-campaign-manifest.md`
- `scripts/generate_prediction_campaign_manifest.py`
- `scripts/check_prediction_campaign_manifest.py`
- checked fixture at `spec/fixtures/generated/prediction-campaign-manifest/weather-transit-delay-campaign-manifest.generated.json`
- CLI command `python3 scripts/ope.py prediction-campaign`
- CLI readbacks `python3 scripts/ope.py prediction-campaign plan` and `python3 scripts/ope.py prediction-campaign status`
- unique dry-run IDs for campaign, cycle, run, question, forecast, resolution, and scoring records
- duplicate-key, skipped, missed, canceled, failed, manually stopped, and duplicate-blocked status boundaries
- release-manifest, MVP-smoke, CLI, docs, roadmap, and decision-log wiring for the checked dry-run campaign manifest

## Milestone 93: Terminal Campaign Runner

Status: In Progress.

Goal: make one foreground terminal command create future forecasts on schedule, then leave due resolutions to the checked resolver path.

Tasks:

- [x] Add a checked dry-run `python3 scripts/ope.py prediction-campaign start` readback before effectful foreground execution.
- [ ] Turn `python3 scripts/ope.py prediction-campaign start` into local foreground execution.
- [x] Support dry-run campaign creation input from flags and from a setup JSON file.
- [x] Expose finite count, until date, open-ended, interval, and calibration-threshold modes from the same command surface in the dry-run readback.
- [x] Expose `--interval`, `--count`, `--until`, `--calibration-target`, `--post-calibration-action`, and `--post-calibration-delay` without requiring agents to write raw scheduler syntax.
- [x] Add a checked forecast-creation handoff for the ready run before effectful artifact creation.
- [x] Add a checked unresolved campaign forecast artifact for the ready run using the standard lifecycle contracts.
- [x] Add a checked non-mutating campaign forecast write plan before effectful ignored-state mutation.
- [x] Add explicit guarded `--write-local` execution for the ready run that writes lifecycle records plus minimal campaign/run state under ignored `.ope/live/prediction-campaigns/`.
- [ ] Add forecast scheduling, not only resolution scheduling: the runner must create the next forecast before close when the recurrence policy says it is due.
- [x] Add a missed-run policy: default to skip if the forecast close time has passed, and record why the missed run is excluded from comparable evidence.
- [x] Document JSONL captured output and compact human status line expectations in the dry-run runner readback.
- [x] Keep dry-run execution local and explicit: live fetches and resolver execution are named future flags, not normal-check behavior.

Exit criteria:

- A developer or agent can start a 100-run transit campaign from one terminal command.
- The same command shape can run hourly, daily, weekly, count-bounded, until-date, or open-ended campaigns.

Example target commands:

```bash
python3 scripts/ope.py prediction-campaign start \
  --domain weather-transit-delays \
  --service-window morning_peak \
  --interval P1D \
  --count 100 \
  --live-weather \
  --execute-resolvers \
  --output-format jsonl
```

```bash
python3 scripts/ope.py prediction-campaign start \
  --domain weather-transit-delays \
  --service-window morning_peak \
  --interval P1D \
  --calibration-target 100 \
  --post-calibration-action pause_then_resume_after \
  --post-calibration-delay P14D
```

Completed outputs so far:

- `spec/prediction-campaign-runner.schema.json`
- `spec/prediction-campaign-runner.md`
- `scripts/generate_prediction_campaign_runner.py`
- `scripts/check_prediction_campaign_runner.py`
- checked fixture at `spec/fixtures/generated/prediction-campaign-runner/weather-transit-delay-campaign-runner.generated.json`
- CLI readback `python3 scripts/ope.py prediction-campaign start`
- CLI normalized campaign input view `python3 scripts/ope.py prediction-campaign start --view campaign-creation`
- CLI missed-run policy view `python3 scripts/ope.py prediction-campaign start --view missed-run-policy`
- `spec/prediction-campaign-forecast-creation.schema.json`
- `spec/prediction-campaign-forecast-creation.md`
- `scripts/generate_prediction_campaign_forecast_creation.py`
- `scripts/check_prediction_campaign_forecast_creation.py`
- checked fixture at `spec/fixtures/generated/prediction-campaign-forecast-creation/weather-transit-delay-campaign-forecast-creation.generated.json`
- CLI readback `python3 scripts/ope.py prediction-campaign forecast-create`
- `spec/prediction-campaign-forecast-artifact.md`
- `scripts/generate_prediction_campaign_forecast_artifact.py`
- `scripts/check_prediction_campaign_forecast_artifact.py`
- checked lifecycle fixtures under `spec/fixtures/generated/prediction-campaign-forecast-artifact/`
- CLI readback `python3 scripts/ope.py prediction-campaign forecast-artifact`
- `spec/prediction-campaign-forecast-write.schema.json`
- `spec/prediction-campaign-forecast-write.md`
- `scripts/generate_prediction_campaign_forecast_write.py`
- `scripts/check_prediction_campaign_forecast_write.py`
- checked write-plan fixture under `spec/fixtures/generated/prediction-campaign-forecast-write/`
- CLI readback `python3 scripts/ope.py prediction-campaign forecast-write`
- explicit local write commands `python3 scripts/ope.py prediction-campaign forecast-write --write-local --output-format jsonl` and `python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl`
- idempotent ignored local state under `.ope/live/prediction-campaigns/predictioncampaign-001/` when a developer explicitly runs `--write-local`
- release-manifest, MVP-smoke, read-surface, CLI, docs, roadmap, and decision-log wiring for the checked dry-run runner, forecast-creation, forecast-artifact, and forecast-write readbacks

## Milestone 94: Campaign Resolution, Scoring, And Recovery

Status: Planned.

Goal: connect campaign-created forecasts to due resolution, scoring, retry, and recovery without manual per-run commands.

Tasks:

- [x] Extend the existing resolution job registry to read campaign manifests as well as standalone forward-run states.
- [ ] Let the campaign runner call the checked resolver for due runs when `--execute-resolvers` is explicit.
- [ ] Record per-run resolver attempts, failure categories, retry eligibility, source fetch metadata, and sanitized diagnostics.
- [ ] Avoid duplicate resolution and duplicate scoring for runs that are already resolved, ambiguous, annulled, blocked, or excluded.
- [ ] Add resume behavior after terminal interruption: the runner should continue from campaign state and never overwrite prior run evidence.
- [ ] Add compact agent readbacks for campaign health, due runs, failed runs, append-ready runs, and next action.

Exit criteria:

- A terminal campaign can survive interruption and resume without losing the forecast-before-outcome trail.
- Agents can tell whether to wait, retry, resolve, append, or stop without reading raw state files.

Expected outputs:

- campaign-aware `python3 scripts/ope.py resolution-jobs --campaign ...`
- campaign-aware `python3 scripts/ope.py resolution-scheduler --campaign ...`
- `python3 scripts/ope.py prediction-campaign resume`
- `python3 scripts/ope.py prediction-campaign doctor`

Completed outputs so far:

- `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001`
- `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001`
- `python3 scripts/ope.py prediction-campaign resume`
- checked campaign-aware fixture at `spec/fixtures/generated/resolution-jobs/resolution-jobs-campaign.generated.json`
- checked campaign-aware scheduler fixture at `spec/fixtures/generated/resolution-scheduler/resolution-scheduler-campaign-run.generated.json`
- checked campaign resume fixture at `spec/fixtures/generated/prediction-campaign-resume/weather-transit-delay-campaign-resume.generated.json`
- source binding from forward-run state plus checked campaign manifest, campaign forecast artifact, and forecast-write plan
- release-manifest, MVP-smoke, CLI, docs, roadmap, and decision-log wiring for campaign-aware resolution job, scheduler, and resume readbacks

## Milestone 95: Append-Only Calibration Evidence Ledger

Status: Planned.

Goal: turn resolved campaign runs into local comparable evidence without manual corpus editing.

Tasks:

- [ ] Add an append-only local campaign evidence ledger that stores comparable scored rows and exclusion rows separately.
- [ ] Add append checks for forecast-before-close, resolution-after-horizon, score binding, source-policy binding, observation coverage, comparable scope, and no post-close evidence leakage.
- [ ] Make append idempotent: the same resolved run can be inspected repeatedly without creating duplicate corpus rows.
- [ ] Preserve excluded rows for audit with reason codes such as missed close, missing outcome, low coverage, feed unavailable, invalid window, leakage risk, ambiguous, annulled, and non-comparable.
- [ ] Add `prediction-campaign append-ready` and `prediction-campaign append` commands, with dry-run default and explicit mutation for ignored local ledgers.
- [ ] Let track-record and calibration gates read the checked fixture corpus plus selected local campaign ledgers when `--live` or `--campaign` is explicit.
- [ ] Keep normal release checks deterministic and offline.

Exit criteria:

- A resolved campaign can grow local comparable evidence toward 30-run track-record and 100-run calibration thresholds without hand-editing JSON.
- Append operations are local, append-only, auditable, and safe to rerun.

Expected outputs:

- `spec/prediction-campaign-evidence-ledger.schema.json`
- `spec/prediction-campaign-evidence-ledger.md`
- `python3 scripts/ope.py prediction-campaign append-ready`
- `python3 scripts/ope.py prediction-campaign append`

## Milestone 96: Calibration Gate And Post-Calibration Continuation

Status: Planned.

Goal: once a campaign reaches enough comparable outcomes, generate calibration readbacks and follow the configured continuation policy.

Tasks:

- [ ] Extend the transit track-record and calibration gate to read campaign evidence ledgers and produce threshold-aware local readbacks.
- [ ] Generate calibration summaries only when the declared comparable resolved threshold is met.
- [ ] Distinguish calibration measurement from automatic model tuning: the first implementation reports calibration and does not silently change method behavior.
- [ ] Add campaign cycle state so post-calibration policies can stop, continue collecting evidence, pause, or start the next cycle after a configured delay.
- [ ] Support open-ended campaigns that have no count but pause and resume after calibration according to `postCalibrationPolicy`.
- [ ] Add warnings when a campaign has enough runs but too many exclusions, horizon gaps, source failures, or non-comparable windows to support a calibration claim.
- [ ] Keep stronger method selection, recalibration of probabilities, and model updates behind a later explicit method-update gate.

Exit criteria:

- A campaign that reaches 100 comparable resolved outcomes can produce a local calibration readback.
- A campaign without a count can automatically decide whether to stop, continue, pause, or start the next cycle after the configured post-calibration delay.

Expected outputs:

- `python3 scripts/ope.py prediction-campaign calibration-status`
- `python3 scripts/ope.py transit-track-record-gate --campaign ...`
- checked examples for below-threshold, threshold-met, too-many-exclusions, and post-calibration-restart cases

## Milestone 97: Repeating Prediction Pilot Experience

Status: Planned.

Goal: make repeated prediction setup simple enough for Codex or another agent to run during pilot sessions without custom glue code.

Tasks:

- [ ] Add a pilot task card for starting a repeating prediction campaign and explaining the next forecast, next resolution, evidence threshold, and claim boundary.
- [ ] Add a short runbook for "start 100 calibration sessions in a terminal" and "start an open-ended campaign that pauses after calibration and resumes later."
- [ ] Add agent adapter and MCP readbacks for campaign plan, status, health, append-readiness, and calibration status.
- [ ] Add sanitized error envelopes for invalid interval, missed forecast close, unavailable live source, duplicate campaign, unsafe source policy, and unsupported post-calibration action.
- [ ] Add local usage trace events for campaign start, forecast-created, resolve-due, resolver-executed, append-ready, appended, calibration-threshold-met, paused, resumed, and stopped.
- [ ] Update developer adoption and expansion-readiness surfaces so recurring prediction setup is evaluated before hosted scheduling or broader runtime work.

Exit criteria:

- A pilot agent can start, monitor, explain, stop, and resume a repeating prediction campaign using documented commands and machine-readable readbacks.
- Pilot feedback can distinguish agent UX issues from forecast-quality or calibration evidence.

Expected outputs:

- `spec/repeating-prediction-pilot-runbook.md`
- `python3 scripts/ope.py prediction-campaign explain`
- agent adapter operations for campaign plan/status/calibration readbacks
- pilot-session-packet task card for repeating prediction setup

## Milestone 98: Codebase Quality And Tooling Hardening

Status: In progress.

Goal: act on the comprehensive repository review — finish consolidating the residual fixture-scaffold duplication, add automated lint/type and a security hardening, and improve check-suite developer experience, without changing runtime behavior or generated fixtures.

Tasks:

- [ ] Deduplicate the remaining `compact_json` copy: import it from `ope_fixtures` in `run_resolution_scheduler.py` instead of redefining it (so `render_json` and `compact_json` each live once, in `ope_fixtures.py`).
- [ ] Harden `ensure_safe_local_path` in `generate_prediction_campaign_forecast_write.py` to resolve the target and confirm it stays under `.ope/live/prediction-campaigns`, defeating symlink escape (the path already rejects absolute paths and `..`).
- [ ] Parallelize `run_checks.py` so the ~170 subprocess checks fan out across workers, cutting local wall-time without losing coverage.
- [ ] Add a dev-only lint and type gate (`ruff` + `mypy`) to `release_check.py` and CI, enforcing the existing type hints while keeping the runtime stdlib-only.
- [ ] Extract a shared validate+write/check helper so the delegating `check_or_write` wrappers and similar single-output generators share one path.
- [ ] Split oversized modules: lift the `--write-local` runtime out of `generate_prediction_campaign_forecast_write.py`, and group `ope.py` command handlers.
- [ ] Reduce documentation lockstep churn: convert the monolithic README/PRODUCT wedge paragraphs to additive bullet lists or generated sections.

Exit criteria:

- `def render_json` and `def compact_json` each appear exactly once (in `ope_fixtures.py`).
- `ensure_safe_local_path` rejects symlinked targets that resolve outside the campaign state root.
- `python3 scripts/run_checks.py` stays green and completes substantially faster.
- `python3 scripts/release_check.py` runs lint and type checks and stays green; CI enforces them.

Expected outputs:

- shared `ope_fixtures` helper covering validate+write/check
- a parallel `run_checks.py`
- `ruff`/`mypy` configuration and a CI step
- a smaller `generate_prediction_campaign_forecast_write.py`

## Open Decisions

- When should OPE introduce a hosted service runtime beyond local file and CLI surfaces?
- What is the smallest domain setup contract that remains useful across private operational domains?
- Which source-manifest and mapping format should agents use for local files, APIs, and databases?
- How should OPE represent agent-inferred mappings without treating them as verified facts?
- Which source-policy contract should govern `data: auto` in private engine setups?
- Which live public sources are acceptable for the reference weather-logistics setup beyond Open-Meteo fixture replay?
- Should the first auto-evidence implementation include web search, or only allow-listed APIs and feeds?
- What minimum benchmark evidence is required before OPE can describe a method as state of the art for a domain?
- How should TypeScript or other language-specific validators be generated from the JSON Schema-first contracts if a service runtime is added?
- Should track-record reports use Brier score as the default public metric for binary forecasts, or log score with Brier as supporting metric?
- Should benchmark mode support LLM forecasters in the first implementation, or only deterministic/statistical models?
- What minimal recurrence syntax should OPE expose so agents can express hourly, daily, weekly, until-date, count-bounded, threshold-targeted, and open-ended campaigns without writing raw scheduler configuration?
- Should local campaign evidence ledgers remain ignored artifacts only, or should sanitized append summaries have a committed promotion path?
- After calibration is measured, what explicit gate should be required before OPE updates forecast probabilities, changes method weights, or selects stronger methods automatically?

## Claim Discipline

Do not claim:

- OPE predicts anything.
- OPE has searched all internet evidence.
- OPE is calibrated in domains without resolved sample evidence.
- OPE is better than baselines before baseline-lift reports exist.
- OPE uses state-of-the-art methods before benchmark and method-registry evidence exists.
- OPE private candidate setups are production-ready or calibrated before evidence supports that label.
- OPE supports agent protocol compatibility beyond the tested local MCP stdio scaffold.
- OPE provides independent verification or legal compliance.

Allowed near-term claim:

> OPE is building a contract-first forecasting engine that records forecast histories, resolves outcomes, scores predictions, and reports calibration by domain and horizon.

Allowed product-direction claim:

> OPE is being designed as an agent-native forecasting package and standard that helps agents set up private prediction engines from connected source data and return auditable probabilistic forecast artifacts.
