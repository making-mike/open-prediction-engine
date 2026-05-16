# Decision Log

## DEC-001: Position OPE As A Standalone Evidence-Producing Forecast Engine

- Date: 2026-05-16
- Status: Accepted

### Context

The repository needs a public project narrative before implementation begins. Local planning material describes OPE as the engine responsible for forecast generation, evidence, resolution, scoring, and calibration, but it also includes broader ecosystem context that should not be copied into public OPE documentation.

### Decision

OPE will be documented as a standalone forecasting engine. Public project docs should describe OPE in terms of its own responsibilities: domain-specific forecast generation, evidence packets, provenance, pre-resolution logging, outcome resolution, scoring, baseline comparison, and calibration reporting.

Public OPE docs should not depend on or directly name adjacent projects. Integrations with transports, tool systems, funding systems, payment systems, and audit systems should be described generically unless an implementation actually supports a specific surface.

### Rationale

This keeps the project independently understandable and prevents the engine from inheriting claims that belong to other layers or future products. It also makes the first implementation wedge clearer: prove one measurable forecasting loop before expanding scope.

### Consequences

- `whitepaper.md` is the canonical public narrative for OPE.
- Agent rules and transferable materials should avoid source-project-specific names.
- Future docs must keep claim boundaries tied to implemented forecast, evidence, scoring, and calibration behavior.

## DEC-002: Add Question Governance And Forecast Histories To OPE's Core Contract

- Date: 2026-05-16
- Status: Accepted

### Context

Reviewing mature forecasting platforms showed that their accuracy discipline depends on more than probability outputs. They use clear question contracts, explicit resolution criteria, lifecycle states, timestamped forecast histories, ambiguous or annulled outcomes, time-aware scoring, and track-record reporting.

### Decision

OPE's core contract will include question lifecycle and resolution governance, forecast history records, aggregate or ensemble forecast records where used, explicit ambiguous and annulled statuses, and track-record reports in addition to evidence packets, resolution records, scoring reports, and calibration summaries.

### Rationale

Without question governance, a forecast can be technically well-formed but impossible to score fairly. Without forecast histories, the engine cannot distinguish stale forecasts from timely updates or support time-weighted scoring. Without track-record reports, calibration evidence remains too hard for agents and operators to inspect.

### Consequences

- `whitepaper.md` treats question governance and forecast history as first-class design elements.
- Future schemas should cover question lifecycle, forecast history, aggregate forecasts, unscorable statuses, and track-record reports.
- The local stack memo reflects the same evidence-loop correction.

## DEC-003: Start With JSON Schema Contracts Before Runtime Code

- Date: 2026-05-16
- Status: Accepted

### Context

The roadmap identifies the contract package as the first implementation priority. The repository still has no selected runtime, package manager, or validation library.

### Decision

OPE will begin with JSON Schema records under `spec/` before choosing TypeScript, Zod, Python, or another runtime representation. Runtime validators and generated types can be added later, but the initial source of truth is the schema package plus fixtures.

### Rationale

JSON Schema keeps the first milestone independent of runtime choice and makes record boundaries reviewable before model or API behavior exists. This also matches the whitepaper's contract-first posture and prevents implementation code from implicitly defining the forecast lifecycle.

### Consequences

- `spec/` now contains the first contract skeleton.
- Future runtime work should consume or generate from these schemas rather than redefine records ad hoc.
- The roadmap keeps schema validation tooling open until runtime/package decisions are made.

## DEC-004: Use Python Standard Library For Bootstrap Checks

- Date: 2026-05-16
- Status: Accepted

### Context

Milestone 2 needs executable scoring checks, but the project still has no final runtime, package manager, or dependency policy. Waiting for that decision would block validation of the fixture scoring semantics.

### Decision

Use Python 3 standard library scripts under `scripts/` for bootstrap JSON and scoring checks. This is a temporary implementation harness, not a final application runtime decision.

### Rationale

Python 3 is available locally, requires no package installation, and is sufficient for deterministic scoring formulas, fixture parsing, and semantic checks. This keeps the project moving while preserving the open decision about final runtime and generated validators.

### Consequences

- `python3 scripts/run_checks.py` is the current bootstrap check command.
- The final package manager and application runtime remain open.
- Future implementation may replace or wrap these scripts if the project standardizes on another runtime.

## DEC-005: Select Weather-Linked Logistics Disruption As The First Domain Wedge

- Date: 2026-05-16
- Status: Accepted

### Context

OPE needs one narrow, resolvable forecast domain before it can make useful implementation progress. The domain should have frequent outcomes, clear resolution criteria, simple baselines, manageable risk, and enough operational value to test the evidence loop.

### Decision

Use `weather-logistics` as the first wedge. The first question shape asks whether qualifying weather will disrupt declared last-mile delivery operations in a specific geography and service-day window.

The first implementation will remain fixture-based until ingestion, evidence packets, forecast histories, resolution, scoring, calibration, and track-record reporting work end to end. Live data may follow only through allow-listed sources and the same record contracts.

### Rationale

Weather-linked logistics disruption is frequent enough to resolve, concrete enough to score, and safer than domains such as finance, healthcare, employment, credit, legal outcomes, or public-safety automation. It also supports simple historical-frequency baselines, which makes baseline lift reviewable before model complexity is added.

### Consequences

- `spec/domains/weather-logistics.md` defines the initial wedge contract.
- Milestone 4 should implement the fixture evidence loop for this wedge before adding live connectors.
- Public claims about quality must remain scoped to this domain, horizon, source policy, sample size, and coverage period.

## DEC-006: Use Python Standard Library As The Current Project Runtime

- Date: 2026-05-16
- Status: Accepted

### Context

OPE now has schemas, fixtures, scoring checks, fixture-loop generation, live-source fixture mode, read access, request intake, and release hardening. The local environment has Python 3 available, but no installed `jsonschema` package and no `uv` command. Introducing a mandatory third-party package manager at this point would make the current deterministic checks less portable.

### Decision

Use Python 3.12+ standard-library scripts as the current project runtime and command surface. The project has no mandatory package install step and no third-party runtime dependency. `pyproject.toml` records this as project metadata, with `python3 scripts/run_checks.py` as the canonical test command and `python3 scripts/release_check.py` as the release-readiness command.

### Rationale

The current implementation is contract and fixture heavy. Python standard library support is enough for JSON parsing, local schema-subset validation, deterministic scoring, fixture generation, anti-leakage checks, read access, request intake, and hardening checks. Avoiding third-party dependencies keeps the repository easy to run while the engine is still pre-service.

### Consequences

- `CONTRIBUTING.md` documents the no-install setup.
- Schema validation is implemented by an OPE-scoped validator covering the JSON Schema subset used by the committed contracts.
- A future service runtime may supersede this decision with a new decision-log entry.

## DEC-007: Keep First Live Outcome Resolution Fixture-Mode And Provisional

- Date: 2026-05-16
- Status: Accepted

### Context

OPE now has a controlled live-source fixture path for the weather-logistics wedge. The next useful step is to close the loop with an outcome, but one resolved live-style example is not enough to support a public calibration or quality claim.

### Decision

Resolve the first live-style weather-logistics outcome in fixture mode from declared operations and weather observation records. Generate normal OPE records for the resolved question, evidence packet, forecast artifact, forecast history, resolution, scoring report, calibration summary, and track record, but keep the public outcome summary provisional until the minimum comparable-outcome threshold is met.

The resolver must reject future resolution sources from forecast-time evidence and must exercise unscorable paths for missing operations coverage, corrected weather sources, and conflicting weather observations.

### Rationale

This closes the engine loop without creating a network dependency or overstating live performance. It gives agents a concrete resolved artifact and track record to read while preserving the project rule that calibration claims require sufficient resolved samples.

### Consequences

- `spec/live-outcome-resolution.md` documents the fixture-mode resolution rules.
- `python3 scripts/resolve_live_weather_outcome.py` is part of normal release checks.
- Public docs should distinguish a resolved live-style fixture from a live calibration corpus.

## DEC-008: Expose Local Contract Validation As A Reusable Runtime Surface

- Date: 2026-05-16
- Status: Accepted

### Context

The repository has an OPE-scoped JSON Schema subset validator, but it was embedded in the all-fixture check. Future forecast pipeline or service code will need to validate individual records without duplicating that checker.

### Decision

Move the validator into `scripts/ope_schema.py`, keep the all-fixture schema checker as a thin wrapper, and add a single-record validation command exposed through `python3 scripts/ope.py validate`.

### Rationale

This preserves the current no-dependency runtime while creating a clear contract gate for future scripts. It also lets agents validate one generated or incoming record and receive machine-readable errors.

### Consequences

- `spec/runtime-validation.md` documents the supported schema subset.
- `python3 scripts/check_contract_validator.py` is part of normal release checks.
- Language-specific generated validators remain a future decision if OPE grows beyond local Python scripts.

## DEC-009: Keep The First Request-To-Forecast Pipeline Local And Deterministic

- Date: 2026-05-16
- Status: Accepted

### Context

OPE has controlled request intake, local contract validation, live-source fixture mode, evidence generation, and live outcome resolution. The next useful step is to connect an accepted request to forecast records, but adding a hosted API, queue, database, or non-deterministic model runtime would widen the surface before the local lifecycle is fully stable.

### Decision

Add a fixture-mode forecast pipeline scaffold that accepts an approved `generate_forecast` request fixture, validates policy, normalizes committed source fixtures, builds a deterministic baseline and model forecast, and emits request-bound OPE records. The pipeline remains a local dry-run with no network access, no live fetch, and `effectfulGeneration: false`.

### Rationale

This proves the request-to-forecast binding while preserving the project rule that hosted service behavior, live data operations, and quality claims come only after deterministic record contracts are stable.

### Consequences

- `spec/forecast-pipeline.md` documents the boundary.
- `pipeline-run.schema.json` records local pipeline execution summaries.
- `python3 scripts/run_forecast_pipeline.py` and `python3 scripts/ope.py pipeline` are part of normal checks.
- A future hosted service should reuse these contracts rather than silently redefining request, evidence, artifact, and history bindings.

## DEC-010: Resolve Pipeline Forecasts As A Separate Lifecycle Step

- Date: 2026-05-16
- Status: Accepted

### Context

The local forecast pipeline now generates request-bound forecast records, but generation should not silently imply resolution or scoring. Mature forecast systems keep forecast creation, outcome resolution, scoring, and track-record updates as distinct lifecycle events.

### Decision

Add a separate fixture-mode resolver for pipeline forecasts. It reads generated pipeline records and declared outcome fixtures, then emits resolution, scoring, calibration, track-record, and outcome-summary records while preserving request/result bindings.

### Rationale

Keeping resolution separate makes it easier to audit timing, prevent forecast-time evidence from including future outcome sources, and avoid accidental quality claims from unresolved forecasts.

### Consequences

- `spec/pipeline-resolution.md` documents the boundary.
- `python3 scripts/resolve_pipeline_outcome.py` and `python3 scripts/ope.py resolve-pipeline` are part of normal checks.
- Pipeline output summaries remain provisional until enough comparable resolved outcomes exist.

## DEC-011: Expose Forecast Lifecycle Bundles As Synthetic Read-Only Views

- Date: 2026-05-16
- Status: Accepted

### Context

Agents can read forecast artifacts and track records, but inspecting a complete lifecycle requires manually finding related evidence, history, resolution, scoring, outcome-summary, and pipeline-run files. That makes binding mistakes harder to spot.

### Decision

Add `forecast-bundle` as a synthetic local read type keyed by `forecastId`. The bundle is assembled from already generated public records and does not create, mutate, resolve, score, fetch, or persist anything.

### Rationale

This improves agent ergonomics while preserving the local read-only boundary. The bundle also gives release checks one place to verify that lifecycle bindings remain coherent after generation and resolution.

### Consequences

- `spec/read-access.md` documents bundle access.
- `python3 scripts/ope.py read --record-type forecast-bundle` is part of CLI smoke coverage.
- The public record index lists forecast bundles separately from raw artifacts.

## DEC-012: Add Forecast Cards For Claim-Safe Agent Summaries

- Date: 2026-05-16
- Status: Accepted

### Context

Forecast bundles are useful for audit-style inspection, but they are verbose and include detailed lifecycle records. Agents often need a smaller summary that carries the forecast, baseline, resolution/scoring status, and claim boundary without pulling raw provenance details into the immediate context.

### Decision

Add `forecast-card` as a synthetic read-only view over the lifecycle bundle. It is keyed by `forecastId`, omits source hashes and supporting evidence URIs, and includes explicit fixture-mode and sample-size warnings.

### Rationale

This gives agents a lower-friction, lower-exposure read surface while preserving the deeper bundle for audit workflows. It also reinforces OPE's claim discipline at the point where forecast outputs are most likely to be consumed.

### Consequences

- `spec/read-access.md` documents card access.
- `python3 scripts/ope.py read --record-type forecast-card` is part of CLI smoke coverage.
- The public record index lists forecast cards separately from bundles and artifacts.

## DEC-013: Make Read Surfaces Schema-Bound

- Date: 2026-05-16
- Status: Accepted

### Context

The local read surface now includes artifacts, bundles, cards, track records, and a generated public index. The behavior is tested, but agent-facing summaries and discovery outputs should have explicit contracts too.

### Decision

Add schemas for forecast cards and the public record index, then validate real read outputs against those schemas in release checks.

### Rationale

This keeps OPE contract-first even for synthetic read views. It also prevents accidental removal of claim warnings, sample-size boundaries, or read-index fields that agents depend on.

### Consequences

- `spec/forecast-card.schema.json` and `spec/record-index.schema.json` are part of the spec package.
- `python3 scripts/check_read_contracts.py` is part of normal release checks.
- Read-surface changes should update schemas, docs, and checks together.

## DEC-014: Add A Schema-Bound Local Release Manifest

- Date: 2026-05-16
- Status: Accepted

### Context

OPE now has many generated local surfaces: fixture reports, fixture loops, live outcome records, pipeline records, read indexes, cards, and bundles. Agents and maintainers need one compact artifact that summarizes what is implemented without overstating readiness.

### Decision

Add a generated release manifest with an explicit schema. The manifest summarizes project runtime, canonical commands, schema files, read-surface counts, current claim boundaries, and non-goals.

### Rationale

This keeps release communication machine-readable and claim-safe. It also creates a stable local artifact that future CI, service packaging, or agent workflows can inspect before assuming a capability exists.

### Consequences

- `spec/release-manifest.schema.json` and `spec/release-manifest.md` are part of the spec package.
- `python3 scripts/generate_release_manifest.py` and `python3 scripts/ope.py manifest` are part of normal checks.
- The manifest must remain clear that OPE is fixture-ready locally, not a hosted service or live calibration product.

## DEC-015: Add CI As A Release Gate, Not A Deployment Pipeline

- Date: 2026-05-16
- Status: Accepted

### Context

OPE has a deterministic local release check and a release manifest, but nothing yet records how the same gate should run in automation. Adding CI should not imply that OPE has a hosted service, deployment process, or production live-data workflow.

### Decision

Add a GitHub Actions workflow that checks out the repository, sets up Python 3.12, runs `python3 scripts/release_check.py`, and compiles scripts. Add a local checker that verifies the workflow still runs the expected commands and does not include deployment, publishing, secret, push, or arbitrary network command snippets.

### Rationale

This makes the fixture-ready release gate repeatable while preserving the current no-install, no-service boundary.

### Consequences

- `.github/workflows/release-check.yml` is the CI release gate.
- `python3 scripts/check_ci_workflow.py` is part of normal release checks.
- CI changes should remain aligned with `spec/ci-release-gate.md` and the release manifest.
