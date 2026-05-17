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

## DEC-016: Make OPE Agent-Native With Policy-Bound Auto-Evidence

- Date: 2026-05-16
- Status: Accepted

### Context

The product direction is sharper than a local CLI or developer-provided dataset tool. The desired use case is that a human asks an agent to do something under uncertainty, and the agent can call OPE as a credible open-source forecasting engine. In that mode, the caller may not provide a prepared dataset. OPE should be able to gather the best available allowed evidence for a future-facing question, while preserving forecast discipline, provenance, baselines, resolution, scoring, and calibration boundaries.

### Decision

OPE will be productized as an agent-native forecasting engine with policy-bound auto-evidence gathering. The first target mode is `data: auto`, where OPE uses declared source policies and allow-listed connectors to gather public or approved evidence, records what it used and what it could not verify, and emits machine-readable forecast artifacts for agents.

This does not authorize unbounded internet crawling or claims that OPE used all available evidence. The core contract remains domain-specific, source-policy-bound, benchmarked against baselines, and claim-safe.

### Rationale

Agents need forecasts they can inspect before acting, waiting, escalating, or gathering more evidence. A credible forecasting engine must therefore own more than a probability output: it must normalize the question, gather evidence, preserve provenance, compare against baselines, schedule resolution, score outcomes, and report calibration over comparable samples.

### Consequences

- `PRODUCT.md` records the compact product context for future agents and maintainers.
- The roadmap now prioritizes Agent-Native Auto-Evidence Forecasting before hosted API work.
- `data: auto` requires source-policy, evidence-plan, provenance, freshness, and unavailable-evidence records.
- State-of-the-art method claims require a method registry, benchmark evidence, leakage controls, and baseline comparison.
- Public docs must avoid implying universal prediction, unrestricted web search, live calibration, or agent-protocol support before those capabilities are implemented and tested.

## DEC-017: Keep Agent Adapters As Thin Envelopes Over OPE Records

- Date: 2026-05-17
- Status: Accepted

### Context

OPE is becoming agent-native, but it should not bind itself too early to one transport such as MCP, HTTP, or a queue worker. The local engine already has schema-bound records for requests, evidence plans, forecast cards, lifecycle bundles, resolution, and scoring.

### Decision

Define a transport-neutral `agent-envelope` contract and generated examples before implementing a production adapter. The envelope exposes stable operation names, record bindings, lifecycle state summaries, standardized exit codes, sanitized errors, payloads, and warnings. It wraps existing OPE records and local commands without redefining forecast, evidence, resolution, or scoring semantics.

### Rationale

Agents need predictable JSON and safe errors more than they need an early network surface. A thin envelope lets future MCP, HTTP, or queue adapters share the same behavior while keeping OPE's core contracts authoritative.

### Consequences

- `spec/agent-envelope.schema.json` and `spec/agent-adapter.md` are part of the spec package.
- `scripts/build_agent_adapter_fixtures.py`, `scripts/check_agent_adapter.py`, and `python3 scripts/ope.py agent-envelopes` are part of local checks.
- Future adapters should wrap the envelope contract and preserve exit-code, state, warning, and binding behavior.

## DEC-018: Add A Local Agent-Call Dispatcher Before Protocol Adapters

- Date: 2026-05-17
- Status: Accepted

### Context

The agent envelope contract defines examples, but agents need a direct terminal-call surface that returns one envelope per operation. Jumping directly to MCP, HTTP, or queue infrastructure would add transport concerns before the record contract and error semantics are proven locally.

### Decision

Add `python3 scripts/ope.py agent-call` as a local single-operation dispatcher over the existing request validation, evidence plan, forecast card, lifecycle bundle, resolution status, and scoring summary surfaces. The dispatcher returns one `agent-envelope.schema.json` response, exits with the envelope `exitCode`, and preserves sanitized error behavior for not found, binding mismatch, approval-required, and response-too-large cases.

### Rationale

This gives terminal agents a stable, low-friction integration point now, while keeping MCP, HTTP, and queue adapters as future wrappers over the same envelope semantics.

### Consequences

- `scripts/agent_adapter_dispatcher.py` and `scripts/check_agent_adapter_dispatcher.py` are part of local checks.
- `agent-call` must remain a thin wrapper over existing OPE records and must not introduce new forecast semantics.
- Future protocol adapters should call or mirror this dispatcher one operation at a time.

## DEC-019: Check Protocol Mapping Before Implementing Protocol Runtimes

- Date: 2026-05-17
- Status: Accepted

### Context

The local `agent-call` dispatcher is usable by terminal agents, and OPE's roadmap now needs a path toward MCP, HTTP, and queue adapters. Implementing a protocol runtime too early would risk mixing transport behavior with forecast semantics, credentials, approval gates, or hosted-service claims.

### Decision

Add a schema-bound agent adapter protocol map before implementing any MCP, HTTP, or queue runtime. The map lists each operation, local CLI command, future MCP tool name, future HTTP endpoint, future queue message type, input fields, output envelope schema, exit-code mapping, side-effect level, approval gate, credential boundary, and agent choice examples.

At this stage, the map is documentation and checked fixture data only. It must clearly state that MCP, HTTP, and queue runtimes are not implemented until a later decision implements one of them.

### Rationale

Agents and future adapter implementers need deterministic names and boundaries. A checked map lets OPE design those boundaries now while preserving the local dispatcher as the behavioral source of truth.

### Consequences

- `spec/agent-adapter-protocol-map.schema.json` and `spec/agent-adapter-protocol-map.md` are part of the spec package.
- `scripts/generate_agent_adapter_protocol_map.py`, `scripts/check_agent_adapter_protocol_map.py`, and `python3 scripts/ope.py agent-protocol-map` are part of local checks.
- Future protocol adapters must preserve the agent envelope and must not expose secrets in prompt-visible arguments, queued payloads, artifacts, or provenance records.
- DEC-020 implements the MCP stdio portion locally; HTTP and queue remain mapping-only.

## DEC-020: Add A Local MCP Stdio Scaffold Over Agent Envelopes

- Date: 2026-05-17
- Status: Accepted

### Context

OPE has a local `agent-call` dispatcher and a checked protocol map. The next useful agent-facing step is to let MCP-capable local hosts discover and call the same operations without adding a hosted service, HTTP API, SDK dependency, or production live-fetch workflow.

### Decision

Add a small Python standard-library MCP stdio scaffold that supports `initialize`, `tools/list`, and `tools/call`. It exposes one tool per mapped operation and returns the existing OPE agent envelope as structured content and serialized text content.

The scaffold wraps the existing local dispatcher behavior. It does not introduce new forecast semantics, live fetching, paid actions, private-source access, or credentials in prompt-visible tool arguments.

### Rationale

This makes OPE easier for local agents to use while preserving the envelope contract as the source of truth. A stdio scaffold keeps the runtime small and deterministic enough for release checks.

### Consequences

- `scripts/ope_mcp_stdio.py`, `scripts/check_mcp_adapter.py`, and `python3 scripts/ope.py mcp-stdio` are part of the local adapter surface.
- The protocol map now marks MCP stdio as locally implemented while HTTP and queue remain mapping-only.
- Public docs must describe this as local MCP stdio scaffold support, not hosted service readiness or production agent adapter readiness.

## DEC-021: Add A Fixture-Safe Agent Forecast Run Summary

- Date: 2026-05-17
- Status: Accepted

### Context

Agents can call individual OPE operations, but the default `data: auto` flow still requires callers to know which local commands and read surfaces to chain. That is inconvenient for agent hosts and increases the chance that a caller loses request/source/forecast/resolution/scoring bindings.

### Decision

Add a schema-bound forecast-run summary and a local `python3 scripts/ope.py forecast-run` command for the checked weather-logistics auto-evidence fixture path. The summary binds request, source policy, evidence plan, source set, method selection, pipeline run, question, forecast, card, bundle, resolution, and scoring IDs.

Rejected, blocked, canceled, unsupported, and response-too-large requests return sanitized failure summaries with no generated forecast IDs. The local MCP stdio scaffold also exposes `ope_forecast_run`, returning the same forecast-run summary contract.

### Rationale

Agents need a single compact result for the common safe path, plus enough links to read the card or lifecycle bundle. A summary contract reduces orchestration mistakes without adding a hosted service, live fetch workflow, or new forecasting semantics.

### Consequences

- `spec/forecast-run-summary.schema.json` and `spec/agent-forecast-run.md` are part of the spec package.
- `scripts/run_agent_forecast.py`, `scripts/check_agent_forecast_run.py`, and `python3 scripts/ope.py forecast-run` are part of local checks.
- MCP `ope_forecast_run` returns a forecast-run summary, not an agent envelope.
- Future expansion beyond the default fixture-safe path should first add an intake outcome matrix and checked failure fixtures.

## DEC-022: Check Forecast-Run Intake Outcomes Before Runtime Expansion

- Date: 2026-05-17
- Status: Accepted

### Context

The forecast-run command gives agents one convenient entry point, but agents also need deterministic behavior when a request is rejected, approval-gated, canceled, unsupported by the current fixture runtime, or too large for the caller's response budget.

### Decision

Add a schema-bound forecast-run intake matrix covering accepted, rejected, blocked, canceled, unsupported-fixture-path, and response-too-large outcomes. Generate checked summaries for each class, expose the matrix through `python3 scripts/ope.py forecast-run-matrix`, and extend the MCP stdio check so `ope_forecast_run` preserves the same outcome classes as the CLI.

### Rationale

Agents should be able to choose a safe next action without reading raw diagnostics or inferring policy from prose. A checked matrix makes retry, approval, stop, and size-aware recovery behavior explicit while keeping non-default paths non-generating until a broader runtime exists.

### Consequences

- `spec/forecast-run-intake-matrix.schema.json` and the generated matrix fixture are part of the spec package.
- `scripts/generate_forecast_run_intake_matrix.py`, `scripts/check_forecast_run_intake_matrix.py`, and `python3 scripts/ope.py forecast-run-matrix` are part of local checks.
- Non-completed forecast-run outcomes must not bind forecast records, cards, bundles, resolutions, scoring reports, or quality-claim outputs.
- Future runtime expansion should preserve the matrix contract or intentionally version it.

## DEC-023: Add A Checked Agent Forecast Runbook

- Date: 2026-05-17
- Status: Accepted

### Context

The forecast-run summary and intake matrix make the local orchestration callable, but agents still need one stable workflow that explains which command or tool to call next after a completed run or a failed intake outcome.

### Decision

Add a schema-bound agent forecast runbook that maps request validation, forecast-run execution, intake outcome inspection, forecast card reads, lifecycle bundle reads, resolution status, and scoring summary into one local caller workflow. The runbook includes machine-readable next-action labels aligned to the forecast-run intake matrix and is exposed through `python3 scripts/ope.py forecast-runbook`.

### Rationale

Agents should not infer control flow from scattered prose or duplicate command knowledge. A checked runbook keeps local CLI behavior, MCP tool names, read-surface choices, and failure next actions aligned without introducing a hosted runtime or new forecast semantics.

### Consequences

- `spec/agent-forecast-runbook.schema.json`, `spec/agent-forecast-runbook.md`, and the generated runbook fixture are part of the spec package.
- `scripts/generate_agent_forecast_runbook.py`, `scripts/check_agent_forecast_runbook.py`, and `python3 scripts/ope.py forecast-runbook` are part of local checks.
- The runbook remains scoped to local fixture-safe CLI and MCP stdio behavior until a future runtime decision expands it.
- Future agent-facing docs should preserve the runbook's next-action labels or version the contract intentionally.

## DEC-024: Add Policy-Bound Source Connector Contracts

- Date: 2026-05-17
- Status: Accepted

### Context

OPE's `data: auto` path declares source policies and gathers fixture evidence, but agents need an explicit way to inspect which connectors are allowed, which are resolution-only, and which source classes remain unsupported before asking OPE to gather evidence.

### Decision

Add schema-bound source connector registry and source connector result-set records. The registry declares connector capability, allowed source class, allowed purpose, freshness, rate limit, credential boundary, provenance boundary, diagnostic boundary, and risk posture. The result set separates raw source metadata, normalized fields, unavailable evidence, retrieval diagnostics, provenance, and controls.

Expose the registry through `python3 scripts/ope.py source-connectors`, with `--results` for the fixture-safe result set.

### Rationale

Agents should not infer connector permission from source-policy prose alone. A checked connector contract makes Open-Meteo and committed fixtures usable in the first weather-logistics wedge while keeping broad web search, market-price feeds, live fetching, prompt-visible credentials, raw stack traces, and all-evidence claims out of the normal path.

### Consequences

- `spec/source-connector-registry.schema.json`, `spec/source-connector-result-set.schema.json`, and `spec/source-connectors.md` are part of the spec package.
- `scripts/generate_source_connectors.py`, `scripts/check_source_connectors.py`, and `python3 scripts/ope.py source-connectors` are part of local checks.
- Normal checks must remain fixture-safe and must fail if connector fixtures imply unrestricted internet access, hidden credentials, raw diagnostics, or live calibration quality.
- Future evidence planning should bind requested connectors to the registry before expanding live source gathering.

## DEC-025: Bind Evidence Plans To Source Connector Policy

- Date: 2026-05-17
- Status: Accepted

### Context

The source connector registry makes connector capabilities explicit, but evidence plans still need to bind requested source-policy connectors to that registry before any gatherer or future live runtime can use them.

### Decision

Add connector-policy checks to the evidence-gathering plan. Plans now bind to `sourceConnectorRegistryId` and `expectedSourceConnectorResultSetId`, list requested, registered, unregistered, unsupported, resolution-only, and forecast-time connectors, and report whether all requested connectors are registered.

Request intake and planning now fail closed or explain requests that use unregistered auto connectors, registered-but-unsupported connectors, or resolution-only connectors as forecast-time evidence. Forecast-time search intents exclude resolution-only connectors.

### Rationale

Agents should know whether a source policy is executable before evidence gathering starts. Binding the plan to the checked registry prevents future gatherers from treating unsupported or resolution-only connectors as usable by accident.

### Consequences

- `spec/evidence-gathering-plan.schema.json` includes connector registry/result-set bindings and `connectorPolicyChecks`.
- `scripts/source_connector_catalog.py` is the local shared catalog for request intake, planning, and connector fixtures.
- `scripts/check_auto_evidence_plan.py` covers unregistered, unsupported, and resolution-only connector cases.
- Future evidence gatherers should consume `connectorPolicyChecks` directly before reading source fixtures or live connectors.

## DEC-026: Enforce Connector Policy At Evidence Gathering

- Date: 2026-05-17
- Status: Accepted

### Context

Evidence plans now bind requested connectors to the checked registry, but the fixture gatherer still needed to consume those checks directly before producing normalized source records.

### Decision

Require the auto-evidence gatherer to reject plans whose connector policy includes unregistered, unsupported, or resolution-only connectors. Evidence source sets now bind to the same connector registry and expected connector result set as the plan, and each gathered record carries a `connectorBinding` with registry, connector, result-set, and connector-result IDs.

### Rationale

Agents should not receive partially gathered evidence from a mixed valid and invalid connector policy. Enforcing connector executability at gathering time keeps future live connectors, fixture replay, and source provenance aligned around the same fail-closed boundary.

### Consequences

- `spec/evidence-source-set.schema.json` includes source connector registry/result-set IDs and record-level connector bindings.
- `scripts/gather_auto_evidence.py` fails before reading source fixtures when the plan is not connector-executable.
- `scripts/check_auto_evidence_gathering.py` covers unsupported, unregistered, and resolution-only connector policies.
- `scripts/check_source_connectors.py` verifies source-set record bindings against connector registry and result-set records.
- Future read surfaces should expose these bindings in a compact evidence trace for agent inspection.

## DEC-027: Add Agent-Readable Evidence Traces

- Date: 2026-05-17
- Status: Accepted

### Context

Forecast cards are compact enough for action context, and lifecycle bundles are complete enough for audit context, but agents also need a smaller provenance surface focused on source policy, evidence plans, connector registry entries, connector results, and gathered source records.

### Decision

Add a schema-bound `evidence-trace` read surface keyed by `forecastId`. The trace is assembled read-only from existing generated forecast, evidence-plan, source-set, connector-registry, connector-result, and pipeline records. It exposes connector and source bindings without raw fixture contents, raw diagnostics, prompt-visible credentials, or any claim that all possible internet evidence was gathered.

Expose the trace through `python3 scripts/ope.py read --record-type evidence-trace`, the local `agent-call` dispatcher as `evidence_trace`, and the local MCP stdio scaffold as `ope_evidence_trace`. Also expose direct read types for evidence source sets and source connector result sets.

### Rationale

Agents should be able to inspect exactly which connectors and source records supported a forecast without parsing a full lifecycle bundle or re-running generation. A dedicated trace keeps provenance inspection compact while preserving binding checks against the authoritative records.

### Consequences

- `spec/evidence-trace.schema.json` is part of the spec package.
- `scripts/read_ope_record.py` supports `evidence-trace`, `evidence-source-set`, and `source-connector-results`.
- `spec/forecast-card.schema.json`, `spec/forecast-run-summary.schema.json`, and the checked runbook now link the evidence trace.
- `agent-envelope` and protocol-map contracts include the `evidence_trace` operation.
- Future live connector work should preserve the same evidence trace shape across fixture replay and explicitly gated integration live fetches.

## DEC-028: Add Historical-Only Baseline Forecasts

- Date: 2026-05-17
- Status: Accepted

### Context

OPE's agent-native direction includes `data: auto`, but callers may also restrict a request to historical data only. Before expanding live connectors, OPE needs a clean no-API path that does not quietly depend on weather forecast fixtures, live source calls, or model-adjusted probabilities.

### Decision

Add a historical-only fixture forecast path using `dataMode: provided`, `committed_fixture`, zero network calls, and one historical baseline source. The generated forecast output equals the historical-frequency baseline probability. The path emits question, feature snapshot, evidence packet, forecast artifact, forecast history, and pipeline-run records, and is exposed through `python3 scripts/ope.py historical-forecast` plus `forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json`.

### Rationale

Agents need to know what OPE does when no forecast-time API evidence is allowed. Making this path explicit separates a safe historical reference forecast from a weather-adjusted auto-evidence forecast, and prevents future code from smuggling live or API-derived signals into a baseline-only request.

### Consequences

- `spec/fixtures/requests/historical-weather-logistics-request.json` is the canonical no-API request fixture.
- `scripts/run_historical_baseline_forecast.py` and `scripts/check_historical_baseline_forecast.py` are part of local checks.
- Historical-only forecast cards and bundles are readable, but they do not link evidence traces because no connector-bound evidence gathering ran.
- Forecast-run summaries now allow `sourceMode: committed_fixture`.
- Future method-selection and live connector work should preserve the distinction between baseline-only forecasts and evidence-adjusted model forecasts.

## DEC-029: Add A Policy-Bound Live Connector Readiness Gate

- Date: 2026-05-17
- Status: Accepted

### Context

OPE has fixture-safe auto-evidence and connector contracts, but the next live-source step needs to test Open-Meteo intentionally without making normal release checks network-dependent or implying broad internet search.

### Decision

Add a schema-bound live connector readiness record for the Open-Meteo weather connector. The record separates `fixture_replay`, explicit `integration_live_fetch`, and future `hosted_live_fetch`, and states approval, network, timeout, freshness, retention, diagnostic, credential, trace-binding, and claim boundaries.

Expose the offline readiness record through `python3 scripts/ope.py live-readiness`. Expose the opt-in integration probe through `python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD`, but keep that path out of `run_checks.py`, `release_check.py`, generated read indexes, track records, and calibration claims.

### Rationale

Agents and developers need to know when a connector is safe to inspect in fixture mode, when a live probe is being run intentionally, and when a hosted runtime is still absent. A checked readiness contract preserves connector/result/evidence-trace bindings while preventing a live-source experiment from becoming a hidden dependency or an overclaim.

### Consequences

- `spec/live-connector-readiness.schema.json`, `spec/live-connector-readiness.md`, and the generated readiness fixture are part of the spec package.
- `scripts/generate_live_connector_readiness.py`, `scripts/check_live_connector_readiness.py`, and `python3 scripts/ope.py live-readiness` are part of local checks.
- Normal release checks remain offline and deterministic.
- The opt-in live probe returns sanitized connector-bound data only; it does not create production forecast evidence, a hosted runtime, a public read record, or a live calibration claim.

## DEC-030: Make Private Engine Setup The Domain-Agnostic Product Direction

- Date: 2026-05-17
- Status: Accepted

### Context

The reference weather-logistics work proves OPE's record discipline, but the product vision should not be limited to one domain or one centrally approved source set. The intended user is a developer asking an agent to add a prediction feature to an operational app. The agent should be able to use OPE to set up a private prediction engine from project-specific data while preserving OPE-standard forecast records.

### Decision

Frame OPE as a domain-agnostic forecasting package and standard for private prediction engine setup. Agents may connect caller-approved files, APIs, databases, mappings, and policy-bound auto-evidence sources. OPE should guide setup through resolvable question templates, source policies, source manifests, field mappings, method policies, maturity labels, forecast artifacts, recalculation history, resolution, scoring, and calibration.

Weather-logistics remains the reference wedge for proving end-to-end behavior. It is not the product boundary.

### Rationale

This direction matches the strongest product use case: an agent adding a prediction feature to an existing operational product without inventing a forecasting pipeline from scratch. Flexibility should apply to private setup; strictness should apply to records, provenance, method selection, scoring, and public claims.

### Consequences

- `PRODUCT.md`, `AGENTS.md`, and `roadmap.md` should describe OPE as domain-agnostic while keeping reference wedges for proof.
- The next roadmap milestone becomes the domain-agnostic engine setup contract instead of more live-source capture work.
- Future milestones should prioritize setup contracts, source manifests, field mappings, method eligibility, and recalculation history.
- Candidate private setups must not claim production readiness, calibration, or state-of-the-art performance until evidence supports those labels.

## DEC-031: Add Domain Setup Contracts For Reference And Candidate Engines

- Date: 2026-05-17
- Status: Accepted

### Context

OPE needs a concrete record that lets an agent inspect or create a private prediction-engine setup before connecting data or requesting a forecast. The product direction is domain-agnostic, but quality claims still need domain-specific evidence and maturity labels.

### Decision

Add a `domain-setup.schema.json` contract and generated setup records for:

- `weather-logistics` as a fixture-ready reference setup with a runnable local forecast path.
- `seaport-berth-availability` as a candidate private setup with source roles, fields, resolution rules, scoring policy, baseline policy, method policy, and claim boundaries, but no runnable forecast command.

Expose the setup records through `python3 scripts/ope.py domain-setups` and add checks that candidate setups cannot claim calibration, benchmarked quality, production readiness, state-of-the-art performance, or universal domain coverage.

### Rationale

Agents need more than prose guidance when setting up forecasts in private operational domains. A setup record gives them a structured checklist for question templates, source roles, field requirements, outcome resolution, method eligibility, recalculation, and claim boundaries while keeping OPE flexible about caller-provided data.

### Consequences

- Weather-logistics remains the reference proof, not the product boundary.
- Candidate private setups can be described before they are runnable, but must remain claim-safe.
- The next roadmap milestone can focus on source manifests and field mappings that satisfy a selected setup.

## DEC-032: Add Source Intake Before Forecast Execution

- Date: 2026-05-17
- Status: Accepted

### Context

After adding domain setup records, OPE needs a way for agents to connect caller-approved source data without immediately producing forecasts. The project needs to answer whether provided sources and mappings satisfy a setup, what is missing, what requires confirmation, and which methods are currently eligible.

### Decision

Add schema-bound source intake records:

- `source-manifest.schema.json` for bounded caller-provided sources, roles, connector type, retrieval metadata, coverage, field inventory, and privacy posture.
- `field-mapping.schema.json` for user-provided, registry-backed, deterministic, or agent-inferred mappings from source fields to setup-required fields.
- `source-intake-report.schema.json` for deterministic pre-forecast usability decisions.

Expose checked reports through `python3 scripts/ope.py source-intake` with accepted, accepted-partial, needs-confirmation, and rejected fixture cases. Keep source intake separate from forecast execution: accepted intake can say which methods are eligible, but it must not create forecast artifacts.

### Rationale

Agents need flexible setup from project-specific data, but flexibility should not weaken OPE's provenance and leakage boundaries. A source intake report gives agents a structured answer before forecasting and lets OPE block post-outcome evidence, secrets, insufficient samples, stale sources, and unconfirmed agent-inferred mappings.

### Consequences

- Source intake becomes the gate between domain setup and setup-aware method policy.
- Agent-inferred mappings remain proposals until confirmed by deterministic validation or the user.
- The next roadmap milestone can connect method selection to domain setup plus source intake instead of only request/source-policy fixtures.

## DEC-033: Add Setup-Aware Method Decisions

- Date: 2026-05-17
- Status: Accepted

### Context

OPE had a request and registry based method-selection record, but private engine setup needs a decision record that consumes the selected domain setup and source-intake report. Agents need to know why a forecast receives a baseline, why stronger methods are blocked, or why method selection cannot proceed.

### Decision

Add `setup-method-decision.schema.json` and generated decisions for the four source-intake fixture outcomes. The decision combines:

- domain setup method policy
- source-intake role coverage and mapping status
- sample-size, leakage, freshness, and privacy outcomes
- setup-specific benchmark and claim boundaries

Expose the decisions through `python3 scripts/ope.py setup-method`. Keep the record pre-forecast: it can select a method class or block execution, but it must not create forecast artifacts.

### Rationale

"Best justified method" must mean best justified for this setup, this data, and this evidence boundary. Source eligibility alone is not enough; stronger methods also need benchmark support and claim-safe boundaries. Baseline fallback should be explicit rather than hidden inside forecast generation.

### Consequences

- Accepted and accepted-partial fixture intake currently select the historical baseline.
- Deterministic source eligibility can pass while final eligibility remains blocked by missing setup-specific benchmark evidence.
- Needs-confirmation and rejected intake produce no selected method.
- State-of-the-art, benchmark, calibration, and production claims remain blocked until future evidence supports them.

## DEC-034: Add Append-Only Recalculation History

- Date: 2026-05-17
- Status: Accepted

### Context

OPE needs to update forecasts when new forecast-time evidence arrives, but it cannot overwrite prior probability records without weakening provenance, calibration, and later scoring. Agents also need a clear distinction between forecast-time updates and post-outcome resolution data.

### Decision

Add schema-bound recalculation records:

- `recalculation-trigger.schema.json` for accepted or rejected evidence-change events.
- `recalculation-run.schema.json` for the update decision, previous probability, updated probability, changed evidence refs, method version, and history append state.
- generated fixture records under `spec/fixtures/generated/recalculation/` showing an accepted pre-close update and a rejected post-outcome resolution-source update.

Expose the flow through `python3 scripts/ope.py recalculation` and keep forecast history append-only: the old forecast becomes `superseded`, the updated forecast is appended as `active`, and rejected triggers append no forecast state.

### Rationale

Recalculation is core to agent-native prediction engines because connected source data can change. Append-only history preserves the belief trail and lets downstream agents inspect what changed without confusing forecast updates with outcome resolution.

### Consequences

- Recalculation can change a forecast probability only from allowed forecast-time evidence available before forecast close.
- Post-outcome evidence, resolution-primary sources, and records received after close are rejected as forecast inputs.
- `scripts/generate_recalculation_history.py`, `scripts/check_recalculation_history.py`, and `python3 scripts/ope.py recalculation` are part of local checks.
- Future watch or scheduler runtimes must keep the same trigger, run, and history boundaries before becoming production behavior.

## DEC-035: Add Ignored Local Live Capture Workspace

- Date: 2026-05-17
- Status: Accepted

### Context

OPE can run an explicit Open-Meteo integration live probe, but the result previously only printed to stdout. Developers need a way to inspect sanitized live connector results locally without committing raw live data or implying production live evidence, release readiness, track-record evidence, or calibration.

### Decision

Add an ignored `.ope/live/` workspace and a `--save-local` mode for `python3 scripts/ope.py live-readiness --live`. Saved live captures are schema-bound `source-connector-result-set` records with `executionMode: integration_live_fetch`, live network controls, no raw previews, no raw diagnostics, no prompt-visible credentials, and no all-evidence claims.

Add `python3 scripts/ope.py live-capture` to validate saved captures and convert one successful Open-Meteo result into a local `evidence-source-set` draft. The draft remains ignored local development data and does not create forecast artifacts, histories, read-index records, track records, scoring reports, or calibration summaries.

### Rationale

This gives developers a concrete bridge between fixture replay and future live evidence without weakening release boundaries. Agents can inspect local live drafts when a developer intentionally creates them, while still seeing explicit controls that the draft is not committed forecast evidence.

### Consequences

- `.ope/live/` remains git ignored.
- `spec/source-connector-result-set.schema.json` now supports ignored local integration-live result sets while committed connector fixtures remain fixture-replay.
- `spec/evidence-source-set.schema.json` allows live source-set drafts without fake fixture paths.
- `scripts/live_capture_workspace.py`, `scripts/check_live_capture_workspace.py`, and `python3 scripts/ope.py live-capture` are part of local checks.
- Normal release checks remain offline and do not consume `.ope/live/`.
- A future live-draft execution milestone must explicitly decide when and how local live drafts can become forecast evidence.

## DEC-036: Add Setup-Aware Baseline Forecast Execution

- Date: 2026-05-17
- Status: Accepted

### Context

OPE had domain setup records, source intake reports, and setup-aware method decisions, but those records stopped before forecast generation. Agents need a checked path from accepted setup intake to a forecast card while preserving blocked behavior for unconfirmed mappings, rejected intake, and methods that lack setup-specific benchmark evidence.

### Decision

Add `setup-forecast-run.schema.json` and generated setup forecast records under `spec/fixtures/generated/setup-forecast/`. The generator consumes domain setup, source intake, and setup method decisions. Accepted and accepted-partial cases produce a question, feature snapshot, evidence packet, forecast artifact, forecast history, card, and bundle through the normal read surface. Needs-confirmation and rejected cases produce blocked run summaries without binding forecast outputs.

Expose the flow through `python3 scripts/ope.py setup-forecast`. Forecast cards now include `setupBinding` so agents can inspect the setup run, source manifest, field mapping, source-intake report, and method decision behind setup-generated forecasts.

### Rationale

This closes the first private-setup loop without overclaiming method quality. The current execution path is baseline-only because stronger methods still need setup-specific benchmark evidence and anti-leakage controls.

### Consequences

- Setup forecast execution is fixture-mode only.
- Accepted setup intake can generate claim-safe baseline or benchmark-gated deterministic forecast artifacts.
- Blocked setup outcomes remain non-generating and preserve next-action guidance.
- Normal checks assert no network access, live fetch, effectful generation, or ignored local live draft consumption.
- Future additional method work must preserve setup benchmark gates before producing non-baseline forecasts.

## DEC-037: Add Setup Benchmark Gates For Stronger Method Execution

- Date: 2026-05-17
- Status: Accepted

### Context

OPE could execute setup-aware baseline forecasts, but "best justified method" still needed a concrete gate before a setup could move to a non-baseline method. The weather-logistics deterministic method had clean benchmark fixtures and positive baseline lift, but the sample remains too small for quality, calibration, production, or state-of-the-art claims.

### Decision

Add `setup-benchmark-gate.schema.json` and generated setup benchmark gates under `spec/fixtures/generated/setup-benchmark/`. The gate binds:

- domain setup
- source intake report
- method class
- baseline and candidate benchmark run IDs
- source policy and retrieval window checks
- anti-leakage controls
- execution and quality sample thresholds
- baseline lift
- claim boundaries

Expose the gates through `python3 scripts/ope.py setup-benchmark`. Extend setup method decisions so accepted intake selects `deterministic_statistical` only when `setupbenchmarkgate-001` approves provisional fixture execution. Extend setup forecast execution so accepted intake emits a non-baseline deterministic probability, while accepted-partial intake remains baseline-only and blocked intake remains non-generating.

### Rationale

This makes stronger method selection inspectable and claim-safe. OPE can demonstrate a non-baseline method path without pretending one fixture benchmark is enough for public quality or calibration claims.

### Consequences

- Setup benchmark gates are execution gates, not quality claims.
- Forecast cards expose baseline probability, deterministic forecast probability, method class, and setup benchmark binding.
- Quality, calibration, production, benchmark, and state-of-the-art claims remain blocked.
- Normal checks fail if deterministic setup execution loses benchmark binding, anti-leakage controls, or source provenance separation.
- The next roadmap milestone can focus on drafting source manifests from caller-approved local files.

## DEC-038: Add A Local Source Manifest Builder

- Date: 2026-05-17
- Status: Accepted

### Context

OPE's source intake contracts expect a bounded source manifest and field mapping, but an agent working with local project files needs help drafting those records before intake. That draft step must not treat inferred mappings as verified facts or turn arbitrary private files into forecast evidence.

### Decision

Add a local, read-only source manifest builder for small caller-approved CSV and JSON files. The builder inspects explicit file paths, records field inventories, row counts, hashes, timestamp coverage, privacy flags, and sanitized feature summaries, then emits a draft source manifest and draft field mapping when inspection succeeds.

The builder rejects secrets, unsupported formats, oversized files, and post-outcome leakage indicators. Agent-inferred field and alias mappings are emitted as `proposed` and `requiresConfirmation: true`. The builder always reports `forecastGenerationAllowed: false`.

### Rationale

Agents should be able to prepare OPE-standard intake records from local files without hand-writing schema details. Keeping this as a draft-only step preserves the source-intake and setup-method gates as the authority for whether a forecast can run.

### Consequences

- `spec/source-manifest-build.schema.json` and `spec/source-manifest-builder.md` are part of the spec package.
- `scripts/build_source_manifest.py`, `scripts/check_source_manifest_builder.py`, and `python3 scripts/ope.py source-builder` are part of local checks.
- Generated source-builder drafts remain outside public read surfaces.
- Forecast execution remains blocked until source intake and setup method gates approve the setup.
- The next milestone should make the handoff from builder drafts to source intake explicit.

## DEC-039: Add Builder Draft Intake Handoffs

- Date: 2026-05-17
- Status: Accepted

### Context

The local source manifest builder can draft manifests and mappings from approved CSV/JSON files, but agents still need a deterministic bridge from those drafts to source intake. Without an explicit handoff, callers would have to infer whether to confirm mappings, collect more data, replace unsafe sources, or continue to method selection.

### Decision

Add `source-intake-handoff.schema.json` and generated handoff records under `spec/fixtures/generated/source-handoff/`. The handoff binds a source-manifest build to optional source manifest, field mapping, and source-intake report records. It exposes a compact `nextAction` for agents:

- `ask_mapping_confirmation`
- `proceed_to_method_gating`
- `collect_more_data`
- `replace_rejected_sources`

Rejected builder inputs do not enter source intake. Unconfirmed builder mappings produce `needs_confirmation`. Confirmed drafts can produce accepted source intake or rejected intake when sample-size limits fail.

### Rationale

This makes the private setup workflow safer and easier for agents. Agents can now move from local file inspection to a deterministic next action without treating inferred mappings as facts or turning rejected files into forecast evidence.

### Consequences

- `scripts/generate_source_intake_handoff.py`, `scripts/check_source_intake_handoff.py`, and `python3 scripts/ope.py source-handoff` are part of local checks.
- Source-handoff records are not public read surfaces and do not create forecast artifacts.
- Accepted handoffs route only to setup benchmark and method gates.
- Future setup method work should consume accepted handoff-bound source-intake reports without bypassing benchmark gates.

## DEC-040: Add Source-Handoff Method Gates

- Date: 2026-05-17
- Status: Accepted

### Context

Source-intake handoffs tell agents whether local builder drafts need mapping confirmation, more data, source replacement, or method gating. The accepted handoff path still needed an explicit, inspectable bridge into setup benchmark gates and setup method decisions without accidentally creating forecast artifacts.

### Decision

Add `source-handoff-method-gate.schema.json` and generated handoff-method records under `spec/fixtures/generated/source-handoff-method/`. The generator consumes source-intake handoffs and, only when a source-intake report exists, creates handoff-bound setup benchmark gates and setup method decisions.

The summary record preserves:

- source-intake handoff binding
- optional source-intake report, setup benchmark gate, and setup method decision IDs
- handoff next action and method-gate next action
- selected method class or `none`
- benchmark execution eligibility, method-decision status, baseline eligibility, deterministic eligibility, and quality-claim boundary
- `forecastArtifactsCreated: false`

### Rationale

This keeps the agent setup workflow explicit. Agents can see that a confirmed builder draft reaches `deterministic_statistical` through benchmark-gated method selection, while unconfirmed, insufficient, and builder-rejected cases remain blocked with deterministic next actions.

### Consequences

- `scripts/generate_source_handoff_method_gate.py`, `scripts/check_source_handoff_method_gate.py`, and `python3 scripts/ope.py source-handoff-method` are part of local checks.
- Source-handoff method gates are not public read surfaces and do not create forecast artifacts.
- Handoff-bound setup benchmark and method decisions include the source-intake handoff ID.
- The next milestone should add an explicit setup forecast execution path that consumes an accepted handoff method decision without bypassing source intake or benchmark gates.

## DEC-041: Add Explicit Source-Handoff Forecast Execution

- Date: 2026-05-17
- Status: Accepted

### Context

Source-handoff method gates can now show that a confirmed builder draft reaches a benchmark-gated deterministic method decision. Agents still needed an explicit execution step that turns only the accepted handoff path into forecast artifacts, while preserving blocked handoff outcomes as non-generating records.

### Decision

Add `scripts/run_source_handoff_forecast.py`, `scripts/check_source_handoff_forecast.py`, and `python3 scripts/ope.py source-handoff-forecast`. The execution path consumes the source-intake handoff, source-handoff method gate, handoff-bound source-intake report, setup benchmark gate, and setup method decision.

Only `confirmed_builder_draft` generates artifacts. It produces `forecast-1102`, `question-1102`, `evidence-1102`, `history-1102`, and `setupforecastrun-1102` under `spec/fixtures/generated/source-handoff-forecast/`. Unconfirmed, insufficient-data, secret, unsupported-format, oversized, and leakage cases produce blocked setup forecast run summaries with no forecast IDs or artifact paths.

Extend setup forecast run and forecast card setup bindings with:

- `sourceIntakeHandoffId`
- `sourceHandoffMethodGateId`

Existing setup forecasts set those fields to `null`; handoff-bound forecasts bind them to concrete records.

### Rationale

This completes the first artifact-generating path from caller-approved local files through OPE standards. It keeps execution explicit, preserves the distinction between method readiness and forecast generation, and keeps blocked handoff cases out of forecast artifacts.

### Consequences

- `forecast-1102` is available through the normal forecast artifact, card, and bundle read surfaces.
- Source-handoff forecast execution is fixture-mode only and does not use network access, live fetches, ignored local live drafts, or effectful generation.
- Blocked handoff cases remain non-generating and non-scored.
- The next milestone should resolve and score `forecast-1102` while keeping claim boundaries unchanged.

## DEC-042: Resolve And Score Source-Handoff Forecasts Separately

- Date: 2026-05-17
- Status: Accepted

### Context

The confirmed source-builder handoff can now generate `forecast-1102`, but forecast creation should not imply outcome resolution, scoring, track-record updates, or calibration claims. The handoff path needed the same lifecycle separation as the pipeline and auto-evidence paths.

### Decision

Add `scripts/resolve_source_handoff_outcome.py`, `scripts/check_source_handoff_resolution.py`, and `python3 scripts/ope.py resolve-source-handoff`. The resolver consumes the generated source-handoff forecast records and resolves only `forecast-1102` from the declared local outcome source bound through the handoff source manifest.

The resolver emits a resolved question, resolution record, scoring report, calibration summary, track-record report, and outcome summary under `spec/fixtures/generated/source-handoff-resolution/`. Blocked handoff runs remain non-generating and non-scored.

### Rationale

Separating resolution from forecast execution preserves auditability and prevents future outcome data from entering forecast-time evidence. It also gives agents a complete local-file setup lifecycle to inspect while keeping quality and calibration claims tied to resolved sample size.

### Consequences

- `forecast-1102` now appears through normal forecast card and lifecycle bundle reads with resolved status, Brier score, baseline score, baseline lift, track-record binding, and source-handoff setup bindings.
- Source-handoff outcome summaries report one comparable resolved source-handoff outcome, below the minimum threshold for quality or calibration claims.
- Normal checks fail if blocked handoff cases are scored, if forecast provenance includes the declared outcome source, or if source-handoff bindings drift across resolution and scoring.
- The next milestone should make this private source setup lifecycle easier for agents to follow through a checked setup runbook.

## DEC-043: Add A Source-Handoff Setup Runbook For Agents

- Date: 2026-05-17
- Status: Accepted

### Context

OPE now has a complete local source-builder handoff fixture path: local source inspection, source intake handoff, method gating, explicit forecast execution, resolution, scoring, card reads, bundle reads, and track-record reads. Agents still had to infer the correct sequence and safe next actions from scattered command docs.

### Decision

Add `source-handoff-setup-runbook.schema.json`, `scripts/generate_source_handoff_setup_runbook.py`, `scripts/check_source_handoff_setup_runbook.py`, and `python3 scripts/ope.py source-handoff-runbook`.

The runbook maps each handoff case to a safe next action:

- confirmed builder draft: read the resolved `forecast-1102` card, bundle, or track record
- unconfirmed builder draft: ask for mapping confirmation
- insufficient confirmed draft: collect more data
- builder-rejected sources: replace rejected sources

It also records the workflow steps from `source-builder` through `resolve-source-handoff`, read-surface choices, and guardrails for non-generating and non-scored blocked cases.

### Rationale

The private setup direction depends on agents understanding OPE's setup discipline without hand-authoring schema details or bypassing gates. A checked runbook improves agent ergonomics while preserving the boundaries that unconfirmed mappings cannot forecast, blocked cases cannot score, and one resolved outcome cannot justify quality or calibration claims.

### Consequences

- `spec/source-handoff-setup-runbook.md` documents the runbook boundary.
- `spec/fixtures/generated/source-handoff-runbook/weather-logistics-source-handoff-setup-runbook.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests cover source-handoff runbook drift and case next-action alignment.
- The next milestone should define a general private setup workflow contract that can later cover more source types without implying arbitrary private API/database parsing is implemented now.

## DEC-044: Define A Domain-Agnostic Private Setup Workflow Contract

- Date: 2026-05-17
- Status: Accepted

### Context

The source-handoff setup runbook proves one local fixture path from caller-approved files to a resolved and scored forecast card. The product direction is broader: agents should eventually set up private prediction engines from chosen sources. OPE needed a general workflow contract that can guide future source types without overstating implemented private API or database support.

### Decision

Add `private-setup-workflow.schema.json`, `scripts/generate_private_setup_workflow.py`, `scripts/check_private_setup_workflow.py`, and `python3 scripts/ope.py private-setup-workflow`.

The workflow is domain-agnostic and separates setup into:

- source discovery
- mapping confirmation
- source intake
- method gating
- forecast execution
- recalculation
- resolution
- scoring

It defines outcome classes for `setup_ready`, `needs_confirmation`, `needs_more_data`, `rejected_source`, `unsupported_source`, and `runtime_not_implemented`. It references the weather-logistics source-handoff runbook as the current fixture implementation, while private APIs and private databases remain planned contract surfaces.

### Rationale

Agents need a stable way to understand the private setup lifecycle before choosing a concrete setup path. A general workflow contract preserves OPE's agent-native direction while keeping source execution, credentials, and live private data access behind future explicit runtime decisions.

### Consequences

- `spec/private-setup-workflow.md` documents the workflow boundary.
- `spec/fixtures/generated/private-setup-workflow/ope-private-setup-workflow.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests cover phase order, outcome classes, source-kind implementation status, reference fixture binding, and claim boundaries.
- Generic private API and database parsing remains unimplemented and is now named as a release non-goal.
- The next milestone should define source adapter capability records so future private source support can declare capabilities without implying execution.

## DEC-045: Add Private Source Adapter Capability Declarations

- Date: 2026-05-17
- Status: Accepted

### Context

The private setup workflow names local files, manual mappings, auto-evidence connectors, private APIs, and private databases as setup source kinds. Agents also need to know whether each source kind can actually be inspected, whether it requires approval, whether it can execute in normal checks, and whether it can touch credentials or live private data.

### Decision

Add `private-source-adapter-capability.schema.json`, `scripts/generate_private_source_adapter_capabilities.py`, `scripts/check_private_source_adapter_capabilities.py`, and `python3 scripts/ope.py private-source-adapters`.

The capability record binds to `privatesetupworkflow-001` and covers:

- `local_file` as a fixture-implemented source-builder path
- `manual_mapping` as an approval-gated fixture confirmation path
- `auto_evidence_connector` as fixture replay, not production live fetching
- `manual_upload` as planned contract only
- `private_api` as planned contract only
- `private_database` as planned contract only

It also adds `manual_upload` to the private setup workflow source-kind list as planned-only. The capability contract records approval, credential, prompt-visibility, privacy, freshness, rate-limit, audit-log, and blocked-action boundaries.

### Rationale

OPE should be flexible about sources in private setups, but flexibility needs a precise pre-execution boundary. A capability declaration lets agents reason about what is available or planned without inventing connector behavior, exposing credentials, or treating unsupported sources as forecast evidence.

### Consequences

- `spec/private-source-adapters.md` documents the adapter capability boundary.
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-capabilities.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests verify source-kind binding, declaration-only behavior, offline normal checks, no secret storage, and runtime-not-implemented manual-upload/private-API/private-database adapters.
- Generic manual upload, private API, and private database execution remain release non-goals.
- The next milestone should define an outcome matrix that turns adapter capability states into deterministic agent next actions before setup execution.

## DEC-046: Add Private Source Adapter Outcome Matrix

- Date: 2026-05-17
- Status: Accepted

### Context

The adapter capability contract tells agents what each source kind can or cannot do, but agents still need a deterministic answer to "what do I do next?" before setup execution. The answer should be source-safe and must not create manifests, forecasts, credentials, or scores by implication.

### Decision

Add `private-source-adapter-outcome-matrix.schema.json`, `scripts/generate_private_source_adapter_outcome_matrix.py`, `scripts/check_private_source_adapter_outcome_matrix.py`, and `python3 scripts/ope.py private-source-adapter-outcomes`.

The matrix binds to `privatesourceadaptercapability-001` and `privatesetupworkflow-001`. It defines outcome classes for:

- `available_fixture`
- `approval_required_fixture`
- `planned_runtime`
- `unsupported_source`
- `credential_missing`
- `rejected_unsafe_source`

It maps local files to `run_source_builder`, manual mappings to `request_mapping_confirmation`, auto-evidence connectors to `use_auto_evidence_fixture`, manual uploads to `wait_for_runtime`, private APIs and databases to `request_credentials_after_runtime`, unregistered sources to `replace_source`, and unsafe sources to `reject_source`.

### Rationale

OPE should help agents proceed without guesswork, but only through explicit gates. A checked outcome matrix turns source capability states into next-action guidance while preserving the separation between inspection, setup intake, forecast execution, and scoring.

### Consequences

- `spec/private-source-adapter-outcomes.md` documents the outcome matrix boundary.
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-outcome-matrix.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests verify capability binding, workflow outcome binding, non-execution, blocked artifact creation, planned runtime boundaries, credential runtime absence, and unsafe-source rejection.
- The matrix remains next-action guidance only. It does not create source manifests, field mappings, forecast artifacts, forecast cards, scoring records, live fetch results, or credential records.
- The next milestone should bridge adapter outcome decisions to the exact allowed source-intake entrypoints and blocked-output conditions.

## DEC-047: Add Private Source Adapter Intake Bridge

- Date: 2026-05-17
- Status: Accepted

### Context

The private source adapter outcome matrix tells agents whether a source kind is available, approval-gated, planned, unsupported, credential-blocked, or unsafe. Agents still need the next safe entrypoint for each outcome: when to run source-builder, when to ask for mapping confirmation, when to use fixture evidence, and when to wait, replace, or stop.

### Decision

Add `private-source-adapter-intake-bridge.schema.json`, `scripts/generate_private_source_adapter_intake_bridge.py`, `scripts/check_private_source_adapter_intake_bridge.py`, and `python3 scripts/ope.py private-source-adapter-bridge`.

The bridge binds to `privateadapteroutcomematrix-001`, `privatesourceadaptercapability-001`, and `privatesetupworkflow-001`. It routes:

- `local_file` to `python3 scripts/ope.py source-builder`
- `manual_mapping` to caller confirmation, then `python3 scripts/ope.py source-handoff --case confirmed_builder_draft`
- `auto_evidence_connector` to fixture `python3 scripts/ope.py gather-evidence`
- `manual_upload`, `private_api`, and `private_database` to no current entrypoint until a checked runtime exists
- `unregistered_source` and `unsafe_source` to replace or stop actions

### Rationale

OPE should be flexible about private setup sources while remaining precise about what is actually implemented. A checked bridge removes guesswork for agents without turning adapter guidance into source execution, forecast generation, scoring, live fetching, or credential handling.

### Consequences

- `spec/private-source-adapter-bridge.md` documents the bridge boundary.
- `spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-intake-bridge.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests verify outcome-matrix binding, checked entrypoints, caller confirmation before source-handoff, planned-runtime blocking, unsupported and unsafe source stops, and no source, forecast, score, live-fetch, or credential artifact creation.
- The bridge remains routing guidance only. Forecast artifacts and scoring records still require source intake, method gates, and explicit forecast execution.
- The next milestone should define the private setup request contract that starts this routing flow from one agent-facing setup-intent record.
