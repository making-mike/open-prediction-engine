# Open Prediction Engine Roadmap

Last updated: 2026-05-16

## Purpose

This roadmap turns the OPE whitepaper into an execution plan.

The project should advance in this order:

1. Define machine-readable contracts.
2. Prove scoring and resolution on fixtures.
3. Choose one narrow forecast domain.
4. Build one complete evidence loop.
5. Add benchmark and anti-leakage controls.
6. Expose agent-facing access only after the core records are stable.

The roadmap is intentionally contract-first. OPE should not start as a generic LLM forecast endpoint.

## Current Status

Done:

- Standalone OPE positioning in `AGENTS.md`.
- Public narrative in `whitepaper.md`.
- Research-backed whitepaper evaluation in `research/whitepaper-evaluation.md`.
- Agent baseline and decision log under `.agents/`.
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

Not started:

- Hosted service runtime and network API.
- Generated language-specific runtime types, if needed later.

In progress:

- None.

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

## Open Decisions

- When should OPE introduce a hosted service runtime beyond local file and CLI surfaces?
- How should TypeScript or other language-specific validators be generated from the JSON Schema-first contracts if a service runtime is added?
- Should track-record reports use Brier score as the default public metric for binary forecasts, or log score with Brier as supporting metric?
- Should benchmark mode support LLM forecasters in the first implementation, or only deterministic/statistical models?

## Claim Discipline

Do not claim:

- OPE predicts anything.
- OPE is calibrated in domains without resolved sample evidence.
- OPE is better than baselines before baseline-lift reports exist.
- OPE supports agent protocol compatibility before an implemented adapter exists.
- OPE provides independent verification or legal compliance.

Allowed near-term claim:

> OPE is building a contract-first forecasting engine that records forecast histories, resolves outcomes, scores predictions, and reports calibration by domain and horizon.
