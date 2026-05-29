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

## DEC-048: Add Private Setup Request Contract

- Date: 2026-05-18
- Status: Accepted

### Context

The private setup workflow, adapter capability contract, outcome matrix, and intake bridge make setup routing explicit, but an agent still needs a single setup-intent surface to start from. Without a request contract, callers must reverse-engineer several lower-level records before knowing whether to run source-builder, ask for confirmation, use fixture evidence, wait for runtime, replace a source, or stop.

### Decision

Add `private-setup-request.schema.json`, `scripts/generate_private_setup_requests.py`, `scripts/check_private_setup_requests.py`, and `python3 scripts/ope.py private-setup-requests`.

The request set binds to `privateadapterintakebridge-001`, `privateadapteroutcomematrix-001`, `privatesourceadaptercapability-001`, and `privatesetupworkflow-001`. It includes request rows for:

- `local_file` routed to source-builder
- `manual_mapping` routed to caller confirmation and source-handoff confirmation
- `auto_evidence_connector` routed to fixture evidence gathering
- `manual_upload`, `private_api`, and `private_database` routed to wait-for-runtime outcomes
- `unregistered_source` routed to replacement
- `unsafe_source` routed to stop

### Rationale

OPE should be easy for agents to start, but the first setup step must remain explicit and non-effectful. A setup request contract turns forecast intent, setup mode, source policy, selected source kind, and approval state into a safe first action without reading private data or creating downstream artifacts.

### Consequences

- `spec/private-setup-request.md` documents the request contract boundary.
- `spec/fixtures/generated/private-setup-requests/ope-private-setup-requests.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests verify bridge binding, local-file source-builder routing, manual mapping confirmation, fixture auto-evidence routing, planned-runtime waits, unsupported-source replacement, unsafe-source stops, and no private reads, source outputs, forecast artifacts, scoring records, live fetches, or credential records.
- Request classification remains routing guidance only. It does not execute source reads, source-builder, source-handoff, fixture gathering, forecast execution, resolution, or scoring.
- The next milestone should expose a compact first-action dispatcher over this request contract.

## DEC-049: Add Private Setup First-Action Dispatcher

- Date: 2026-05-18
- Status: Accepted

### Context

The private setup request contract gives agents a request set, but a caller often needs a compact answer for one setup request: what should happen first, whether a checked command can be run, and why the request may be blocked. Agents should not need to read the full request set or infer error handling from lower-level setup contracts.

### Decision

Add `private-setup-first-action.schema.json`, `scripts/private_setup_action_dispatcher.py`, `scripts/generate_private_setup_first_actions.py`, `scripts/check_private_setup_first_actions.py`, and CLI commands:

- `python3 scripts/ope.py private-setup-actions`
- `python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001`
- `python3 scripts/ope.py private-setup-action --input path/to/request.json`

The dispatcher accepts one generated request ID or one request-shaped JSON object. It returns a schema-bound action with request and bridge bindings, source policy, action status, route decision, suggested checked command, required caller action, sanitized error, exit code, and execution boundary.

### Rationale

OPE should be easy for agents to call without weakening the setup gates. A first-action dispatcher gives agents a direct next step while preserving the rule that OPE does not read private data, run source-builder or source-handoff, gather fixture evidence, forecast, score, or store credentials merely because a request was classified.

### Consequences

- `spec/private-setup-first-action.md` documents the dispatcher boundary.
- `spec/fixtures/generated/private-setup-actions/` contains schema-bound action fixtures for every current private setup request outcome.
- Normal checks and CLI smoke tests verify generated request binding, local-file command suggestions, manual mapping confirmation, fixture auto-evidence routing, planned-runtime waits, unsupported-source replacement, unsafe-source rejection, sanitized unknown-source and missing-approval errors, and no private reads, command execution, forecast artifacts, scoring records, or credential storage.
- The dispatcher remains a non-executing read surface. It may name checked local commands, but it does not run them.
- The next milestone should add a checked runbook that maps first-action statuses to next safe caller-visible steps.

## DEC-050: Add Private Setup First-Action Runbook

- Date: 2026-05-18
- Status: Accepted

### Context

The first-action dispatcher gives agents a compact action for one private setup request. Agents still need a deterministic interpretation of each action status: which step is safe next, whether caller confirmation is required, what output class to expect, and where execution must stop.

### Decision

Add `private-setup-first-action-runbook.schema.json`, `scripts/generate_private_setup_first_action_runbook.py`, `scripts/check_private_setup_first_action_runbook.py`, and `python3 scripts/ope.py private-setup-action-runbook`.

The runbook binds every generated first-action fixture and covers bad-request classes for unknown source kinds and missing approvals. It maps:

- `ready_to_run_checked_command` to source-builder guidance
- `confirmation_required` to caller mapping confirmation
- `fixture_ready` to fixture evidence guidance
- `runtime_not_implemented` to wait-for-runtime guidance
- `source_replacement_required` to source replacement
- `rejected_unsafe_source` to stop
- `bad_request` to sanitized request repair guidance

### Rationale

OPE should be agent-accessible without encouraging agents to improvise around setup gates. A checked runbook turns first-action statuses into stable next-step guidance while preserving the distinction between guidance, source intake, forecast execution, resolution, and scoring.

### Consequences

- `spec/private-setup-first-action-runbook.md` documents the runbook boundary.
- `spec/fixtures/generated/private-setup-actions/ope-private-setup-first-action-runbook.generated.json` is schema-bound and checked.
- Normal checks and CLI smoke tests verify first-action binding, full status coverage, planned-runtime blocking, source-intake blocking for unsafe/unknown/missing-approval cases, bad-request playbooks, and no command execution, forecast artifacts, scoring records, or credential storage.
- The runbook remains guidance only. It may name commands, but it does not run them or create downstream artifacts.
- The next milestone should expose a compact private setup agent bundle that joins request, first-action, and runbook guidance for one request ID.

## DEC-051: Add Private Setup Agent Bundles

- Date: 2026-05-18
- Status: Accepted

### Context

Private setup request rows, first-action dispatcher results, and runbook guidance are each useful, but an agent asking "what should I do next for this setup request?" should not have to join those records manually. The next surface should preserve all bindings and guardrails while giving one compact response per request.

### Decision

Add `private-setup-agent-bundle.schema.json`, `scripts/generate_private_setup_agent_bundles.py`, `scripts/check_private_setup_agent_bundles.py`, and CLI commands:

- `python3 scripts/ope.py private-setup-bundles`
- `python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001`
- `python3 scripts/ope.py private-setup-bundle --case unknown_source_kind`
- `python3 scripts/ope.py private-setup-bundle --case missing_approval`

The bundle joins request summary, first-action summary, runbook guidance, claim boundary, and execution boundary. It includes checked examples for all eight current source kinds plus sanitized bad-request examples for unknown source kind and missing approval.

### Rationale

OPE is intended to be agent-native. A joined bundle reduces agent-side bookkeeping while preserving the strict lifecycle separation between setup guidance, source intake, forecast execution, resolution, and scoring.

### Consequences

- `spec/private-setup-agent-bundle.md` documents the bundle boundary.
- `spec/fixtures/generated/private-setup-agent-bundles/` contains schema-bound bundle fixtures.
- Normal checks and CLI smoke tests verify request/action/runbook binding, bad-request examples, planned-runtime blocking, source-intake blocking, claim boundaries, and no source, forecast, score, live-fetch, or credential artifact creation.
- Bundles remain read-only guidance. They do not execute suggested commands or create downstream artifacts.
- The next milestone should expose bundle reads through the existing transport-neutral agent envelope pattern.

## DEC-052: Expose Private Setup Bundles Through Agent Envelopes

- Date: 2026-05-18
- Status: Accepted

### Context

Private setup agent bundles give a compact read surface, but agents using the transport-neutral adapter still had to call lower-level bundle commands. To keep OPE agent-native, setup guidance should be available through the same envelope, exit-code, sanitized-error, and MCP mapping pattern as forecast cards, evidence traces, lifecycle bundles, resolution status, and scoring summaries.

### Decision

Add `private_setup_bundle` to the local agent adapter operation set, the agent envelope schema, the protocol-map schema, the local dispatcher, generated envelope fixtures, local MCP stdio tool map, and CLI smoke checks.

The operation reads a private setup bundle by request ID or a checked bad-request case. Successful calls return the private setup agent bundle as the envelope payload. Missing bundle reads return a sanitized `not_found` envelope with exit code 4.

### Rationale

Agents should be able to ask OPE for private setup guidance without learning separate CLI surfaces or bypassing setup gates. Reusing the existing envelope contract keeps status handling, max-byte limits, read-only boundaries, and future MCP/HTTP/queue adapter mappings coherent.

### Consequences

- `spec/fixtures/generated/agent-adapter/` now includes success and sanitized-error private setup bundle envelope examples.
- `python3 scripts/ope.py agent-call --operation private_setup_bundle --private-setup-request-id privatesetuprequest-001` returns a schema-bound envelope.
- The local MCP stdio scaffold exposes `ope_private_setup_bundle`.
- Normal checks verify request binding, bad-request bundle reads, sanitized missing-bundle errors, protocol-map coverage, MCP tool exposure, and no source setup command execution.
- The operation remains guidance-only. It does not read private source data, run source-builder, create source manifests, forecast, score, fetch live data, or store credentials.
- The next milestone should let agents continue from local-file setup guidance into a caller-approved source-builder adapter path without weakening intake, method, benchmark, forecast, or scoring gates.

## DEC-053: Expose Local-File Source Builder Through Agent Envelopes

- Date: 2026-05-18
- Status: Accepted

### Context

After `private_setup_bundle`, the local-file setup path still required agents to call the lower-level source-builder CLI directly. That made the agent-facing path uneven: setup guidance was envelope-shaped, but the next draft-manifest step was not. The source-builder also has important boundaries that should be preserved at the adapter layer: explicit caller-approved files only, small CSV/JSON parsing, secret/oversize/leakage rejection, proposed inferred mappings, and no forecast artifacts.

### Decision

Add `private_setup_source_builder` to the local agent adapter operation set, agent envelope schema, protocol-map schema, local dispatcher, local MCP stdio scaffold, generated envelope fixtures, and CLI smoke checks.

The operation supports checked fixture cases and explicit caller-approved `source_role=path` inputs with optional mapping hints. Successful calls return one envelope containing `sourceManifestBuild` plus draft `sourceManifest` and `fieldMapping` objects when inspection succeeds. Rejected source inputs return ok envelopes with rejected build payloads. Malformed source-builder arguments return sanitized `validation_failed` envelopes.

### Rationale

OPE should let agents continue through private setup without improvising lower-level commands or weakening safety gates. The source-builder adapter turns local-file inspection into a transport-neutral, schema-bound step while preserving that drafts are not forecasts and inferred mappings are not verified facts.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_setup_source_builder --private-setup-request-id privatesetuprequest-001 --source-builder-case local_draft` returns a schema-bound envelope.
- The local MCP stdio scaffold exposes `ope_private_setup_source_builder`.
- Generated adapter fixtures cover draft-ready local files, secret rejection, unsupported-format rejection, oversized-file rejection, leakage rejection, and sanitized malformed-input errors.
- Normal checks verify caller-approved file inputs, proposed inferred mappings, rejected draft behavior, protocol-map coverage, MCP tool exposure, and no forecast, score, live-fetch, credential, or public read-record creation.
- The operation may draft source manifests and mappings, but it does not enter source intake, select methods, run forecasts, resolve outcomes, score forecasts, or store credentials.
- The next milestone should expose source-handoff next actions through agent envelopes so confirmed drafts can proceed toward method gates without bypassing confirmation or benchmark controls.

## DEC-054: Expose Source-Handoff Next Actions Through Agent Envelopes

- Date: 2026-05-18
- Status: Accepted

### Context

After `private_setup_source_builder`, agents could get draft source manifests and mappings through the adapter, but still had to call lower-level source-handoff surfaces to learn whether mappings needed confirmation, data was insufficient, rejected sources had to be replaced, or a confirmed handoff could proceed toward setup method gates.

### Decision

Add `private_setup_source_handoff` to the local agent adapter operation set, agent envelope schema, protocol-map schema, local dispatcher, local MCP stdio scaffold, generated envelope fixtures, and CLI smoke checks.

The operation reads checked source-handoff fixture cases and returns one envelope containing `sourceIntakeHandoff`, source-builder and source-intake bindings, mapping confirmation state, method-gate readiness, and execution boundaries. It covers unconfirmed, confirmed, insufficient-data, secret, unsupported, oversized, and leakage cases.

### Rationale

OPE should let agents continue through private setup through one transport-neutral surface while preserving confirmation-before-intake and benchmark-before-forecast rules. The handoff adapter makes the next action explicit without letting agents treat draft or blocked source records as forecast inputs.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_setup_source_handoff --private-setup-request-id privatesetuprequest-001 --source-handoff-case confirmed_builder_draft` returns a schema-bound envelope.
- The local MCP stdio scaffold exposes `ope_private_setup_source_handoff`.
- Generated adapter fixtures cover confirmed, unconfirmed, insufficient-data, and rejected source-handoff cases.
- Normal checks verify mapping confirmation, source-builder/source-intake binding, method-gate readiness only for the confirmed accepted handoff, protocol-map coverage, MCP tool exposure, and no forecast, score, live-fetch, credential, or public read-record creation.
- The operation may guide agents toward setup method gates, but it does not run source intake, select methods, run forecasts, resolve outcomes, score forecasts, or store credentials.
- The next milestone should expose setup method-gate guidance through agent envelopes so confirmed handoffs can reach benchmark and method decisions without bypassing explicit forecast execution.

## DEC-055: Expose Setup Method Gates Through Agent Envelopes

- Date: 2026-05-18
- Status: Accepted

### Context

After `private_setup_source_handoff`, agents could inspect mapping confirmation and source-handoff next actions through the adapter, but still had to call lower-level method-gate surfaces to learn whether setup benchmark and method decisions allowed explicit forecast execution.

### Decision

Add `private_setup_method_gate` to the local agent adapter operation set, agent envelope schema, protocol-map schema, local dispatcher, local MCP stdio scaffold, generated envelope fixtures, and CLI smoke checks.

The operation reads checked source-handoff method-gate cases and returns one envelope containing `sourceHandoffMethodGate`, `sourceIntakeHandoff`, optional `setupBenchmarkGate`, optional `setupMethodDecision`, binding summaries, method-gate status, selected method, and explicit setup forecast-execution readiness.

### Rationale

OPE should make the private setup lifecycle easy for agents to follow while preserving every gate. Method-gate guidance is the last non-forecast step before explicit forecast execution, so the adapter must make "allowed to run a forecast next" visible without creating the forecast itself.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_setup_method_gate --private-setup-request-id privatesetuprequest-001 --method-gate-case confirmed_builder_draft` returns a schema-bound envelope.
- The local MCP stdio scaffold exposes `ope_private_setup_method_gate`.
- Generated adapter fixtures cover confirmed, unconfirmed, insufficient-data, and rejected method-gate cases.
- Normal checks verify source-handoff, source-intake, setup benchmark, and method-decision binding; explicit setup forecast recommendation only for the confirmed accepted handoff; protocol-map coverage; MCP tool exposure; and no forecast, score, live-fetch, credential, or public read-record creation.
- The operation may recommend explicit setup forecast execution when the checked benchmark and method decision allow it, but it does not run forecasts, resolve outcomes, score forecasts, fetch live data, or store credentials.
- The next milestone should expose the explicit setup forecast execution step through agent envelopes while keeping blocked method-gate cases non-generating.

## DEC-056: Expose Private Setup Forecast Execution Through Agent Envelopes

- Date: 2026-05-18
- Status: Accepted

### Context

After `private_setup_method_gate`, agents could see that a confirmed handoff was allowed to run explicit setup forecast execution, but still needed lower-level source-handoff forecast commands to create or inspect the actual setup forecast run and generated forecast artifacts.

### Decision

Add `private_setup_forecast_execution` to the local agent adapter operation set, agent envelope schema, protocol-map schema, local dispatcher, local MCP stdio scaffold, generated envelope fixtures, and CLI smoke checks.

The operation reads checked source-handoff forecast execution cases and returns one envelope containing `setupForecastRun`, source-handoff and method-decision bindings, optional forecast artifacts, a binding summary, adapter guidance, and execution boundaries. It generates artifacts only for `confirmed_builder_draft`; unconfirmed, insufficient-data, rejected-source, and leakage cases remain blocked with null forecast bindings.

### Rationale

OPE's private setup path should let agents move from setup guidance to a forecast without improvising commands or bypassing gates. This operation is the first adapter step in the private setup chain that may return forecast artifacts, so it must make the allowed case explicit and preserve source intake, benchmark, method decision, and method-gate boundaries.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_setup_forecast_execution --private-setup-request-id privatesetuprequest-001 --forecast-execution-case confirmed_builder_draft` returns a schema-bound envelope for `setupforecastrun-1102` and `forecast-1102`.
- The local MCP stdio scaffold exposes `ope_private_setup_forecast_execution`.
- Generated adapter fixtures cover confirmed, unconfirmed, insufficient-data, and rejected forecast-execution cases.
- Normal checks verify `forecast-1102` artifact binding only for the confirmed case, blocked cases with null forecast IDs, protocol-map coverage, MCP tool exposure, and no raw private data, credential, resolution, scoring, or live-fetch side effects.
- The operation may return fixture forecast artifacts, but it does not resolve outcomes, score forecasts, claim calibration, fetch live data, store credentials, or create forecasts from blocked setup cases.
- The next milestone should add private setup forecast readback examples through the existing forecast card, lifecycle bundle, resolution status, and scoring summary adapter operations.

## DEC-057: Read Generated Private Setup Forecasts Through Existing Adapter Operations

- Date: 2026-05-18
- Status: Accepted

### Context

After `private_setup_forecast_execution`, the confirmed checked handoff can return `setupforecastrun-1102` and `forecast-1102`. Agents then need a clear way to continue into normal forecast reads without guessing whether private setup forecasts require a separate read API.

### Decision

Add generated adapter envelope examples for reading `forecast-1102` through the existing `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary` operations. Update dispatcher, CLI, protocol-map, and agent-adapter guidance so generated setup forecasts are read with the returned `forecastId` and `questionId`.

Do not add a private setup forecast read API. Normal read operations must preserve setup forecast run, source-handoff, method-gate, benchmark, method-decision, resolution, scoring, and quality-claim bindings.

### Rationale

OPE's adapter surface should stay small and predictable for agents. A generated private setup forecast is still an OPE forecast record, so a separate read API would duplicate semantics and increase the chance of binding drift.

### Consequences

- `spec/fixtures/generated/agent-adapter/` includes readback envelopes for `forecast-1102` card, lifecycle bundle, resolution status, and scoring summary.
- `python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102` returns the setup-bound forecast card.
- Dispatcher and CLI checks verify setup forecast run, source-handoff, method-gate, resolution, scoring, and source-handoff outcome sample-count bindings.
- Quality and calibration claims remain blocked by the source-handoff sample-size boundary.
- The next milestone should reduce repeated fixture construction cost in the now-larger adapter check suite without changing adapter semantics.

## DEC-058: Cache Adapter Fixture Forecast Execution Inputs

- Date: 2026-05-18
- Status: Accepted

### Context

The private setup adapter suite now emits source-builder, source-handoff, method-gate, forecast-execution, and readback envelopes. Forecast-execution envelope generation repeatedly rebuilt the same source-handoff forecast output set once per checked execution case, which made the expanded local checks slower without adding coverage.

### Decision

Cache source-handoff forecast output construction inside `scripts/build_agent_adapter_fixtures.py` for the lifetime of the process. Add an invariant check that verifies adapter fixture generation reuses the cached output set across forecast-execution cases.

Also factor the private setup forecast readback calls in dispatcher and CLI smoke checks through small helpers while preserving the same explicit assertions for setup run, source-handoff, resolution, scoring, and quality-claim bindings.

### Rationale

This is a maintenance and performance cleanup, not a contract change. Reusing deterministic fixture outputs keeps checks faster and easier to read while preserving the same generated envelope contents and guardrails.

### Consequences

- Agent adapter fixture generation builds source-handoff forecast outputs once per process instead of once per forecast-execution case.
- `scripts/check_agent_adapter.py` guards that cache reuse remains in place.
- Dispatcher and CLI smoke checks keep the same readback coverage with less duplicated setup call assembly.
- No schema, generated fixture, adapter operation, readback payload, claim boundary, hosted API, or production runtime semantics changed.
- The next milestone should add a checked adapter-chain runbook so agents can inspect the complete private setup operation sequence before executing it.

## DEC-059: Add a Private Setup Adapter Chain Runbook

- Date: 2026-05-18
- Status: Accepted

### Context

The private setup adapter path now has several checked operations: setup bundle, source-builder, source-handoff, method-gate, forecast execution, and normal forecast readback. Agents can call each step, but without a single checked chain record they still have to infer the intended order, branch handling, stop conditions, and readback path from separate contracts.

### Decision

Add `private-setup-adapter-chain-runbook.schema.json`, `spec/private-setup-adapter-chain-runbook.md`, `scripts/generate_private_setup_adapter_chain_runbook.py`, `scripts/check_private_setup_adapter_chain_runbook.py`, and `python3 scripts/ope.py private-setup-adapter-runbook`.

The generated runbook lists the local-file private setup adapter sequence from `private_setup_bundle` through `private_setup_forecast_execution`, then routes generated forecasts into the existing `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary` operations. It also includes branch playbooks for mapping confirmation, confirmed handoff, insufficient data, rejected sources, and generated forecast readback.

### Rationale

OPE should be easy for agents to follow without letting them improvise around gates. A checked adapter-chain runbook makes the happy path and stop paths inspectable while preserving that the runbook is guidance only, not an execution surface.

### Consequences

- `spec/fixtures/generated/private-setup-adapter-chain/ope-private-setup-adapter-chain-runbook.generated.json` is schema-bound and checked.
- `python3 scripts/ope.py private-setup-adapter-runbook` returns the runbook without executing adapter calls.
- Normal checks verify sequence order, expected status values, branch playbooks, readback routing, and non-execution boundaries.
- The runbook does not create source, forecast, resolution, scoring, credential, hosted API, or production runtime artifacts.
- The next milestone should expose the runbook through the transport-neutral agent adapter and local MCP scaffold.

## DEC-060: Expose the Adapter Chain Runbook Through Agent Adapter

- Date: 2026-05-18
- Status: Accepted

### Context

The checked private setup adapter-chain runbook exists as a local CLI/generated artifact, but agents using OPE through the transport-neutral adapter still had to know the lower-level `private-setup-adapter-runbook` command. That made the agent-facing setup path less consistent than forecast cards, lifecycle bundles, private setup bundles, and other envelope reads.

### Decision

Add `private_setup_adapter_runbook` to the agent adapter operation set, the agent envelope schema, the protocol-map schema, the local dispatcher, generated envelope fixtures, local MCP stdio scaffold, and CLI smoke checks.

The operation returns the generated private setup adapter-chain runbook in an agent envelope. It is read-only guidance: it may expose operation order, branch playbooks, stop conditions, and normal readback routing, but it must not execute adapter calls or create source, forecast, resolution, scoring, live-fetch, credential, hosted-service, or production-runtime artifacts.

### Rationale

Agents should be able to ask OPE for the full setup adapter sequence through one predictable envelope surface before choosing which operation to call next. Reusing the existing adapter contract keeps status handling, exit codes, max-byte limits, MCP mapping, and future HTTP/queue mapping coherent.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_setup_adapter_runbook` returns a schema-bound envelope for `privatesetupadapterchainrunbook-001`.
- The local MCP stdio scaffold exposes `ope_private_setup_adapter_runbook`.
- The protocol map now contains thirteen envelope-returning adapter operations plus the separate forecast-run tool.
- Normal checks verify request binding, operation sequence, branch stop conditions, normal readback routing, protocol-map coverage, MCP tool exposure, and no adapter-call execution.
- The next milestone should expose private source adapter capability and outcome guidance through the same read-only envelope pattern.

## DEC-061: Expose Private Source Adapter Guidance Through Agent Adapter

- Date: 2026-05-18
- Status: Accepted

### Context

OPE now has checked private source adapter capability declarations, an outcome matrix, and an intake bridge. Agents could inspect these lower-level records, but they still lacked one transport-neutral read for deciding whether a source kind is available, approval-gated, planned-only, unsupported, unsafe, or credential-runtime-blocked before choosing a setup path.

### Decision

Add `private_source_adapter_guidance` to the agent adapter operation set, the agent envelope schema, the protocol-map schema, the local dispatcher, generated envelope fixtures, local MCP stdio scaffold, and CLI smoke checks.

The operation returns a read-only guidance payload that joins capability, outcome, and intake-bridge records with a compact source-kind summary. It may route an agent toward source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop guidance, but it must not execute source reads, adapter calls, source-manifest creation, forecasts, scoring, live fetching, credential handling, hosted-service work, or production runtime behavior.

### Rationale

Agents need flexibility when a private setup can start from files, manual mappings, future uploads, private APIs, databases, or policy-bound evidence. A single checked guidance envelope makes that flexibility inspectable without turning source-kind advice into execution.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_source_adapter_guidance` returns a schema-bound envelope for `privatesourceadaptercapability-001`.
- The local MCP stdio scaffold exposes `ope_private_source_adapter_guidance`.
- The protocol map now contains fourteen envelope-returning adapter operations plus the separate forecast-run tool.
- Normal checks verify capability/outcome/bridge bindings, source-kind routing, planned-runtime boundaries, unsupported and unsafe stop paths, protocol-map coverage, MCP tool exposure, and no source reads or artifact creation.
- The next milestone should add compact private source-kind selection examples so agents can choose the next setup operation without inferring from the full guidance payload.

## DEC-062: Add Private Source-Kind Selection Examples

- Date: 2026-05-18
- Status: Accepted

### Context

The private source adapter guidance envelope tells agents which source kinds are available, approval-gated, planned-only, unsupported, unsafe, or credential-runtime-blocked. The payload is intentionally complete, but agents still benefit from compact examples that map each source kind to the next safe path without inferring from capability, outcome, bridge, first-action, and adapter-chain records separately.

### Decision

Add `private-source-kind-selection-examples.schema.json`, `spec/private-source-kind-selection-examples.md`, `scripts/generate_private_source_kind_selection_examples.py`, `scripts/check_private_source_kind_selection_examples.py`, and `python3 scripts/ope.py private-source-kind-selection`.

The generated examples bind the private source adapter guidance envelope, private setup first-action records, and the private setup adapter-chain runbook. They cover local files, manual mappings, fixture auto-evidence, manual uploads, private APIs, private databases, unregistered sources, and unsafe sources. Each example recommends one of: call source-builder adapter, request mapping confirmation, call fixture evidence, wait for runtime, replace source, or reject source.

### Rationale

OPE should be flexible about private setup inputs while strict about execution gates. Compact source-kind examples make agent choice easier without letting examples become source reads, adapter calls, source manifests, forecasts, scores, credentials, live fetches, hosted-service work, or production runtime behavior.

### Consequences

- `python3 scripts/ope.py private-source-kind-selection` returns a schema-bound non-executing guidance record.
- Normal checks verify guidance-envelope, first-action, and adapter-chain bindings.
- Local-file examples route to `private_setup_source_builder`; manual-mapping examples require confirmation before source-handoff; fixture auto-evidence stays outside the local-file adapter chain.
- Manual upload, private API, and private database examples wait for future runtimes; unregistered and unsafe sources stop before source intake.
- The next milestone should expose these examples through the transport-neutral agent adapter and local MCP scaffold.

## DEC-063: Expose Private Source-Kind Selection Through Agent Adapter

- Date: 2026-05-18
- Status: Accepted

### Context

OPE has checked private source-kind selection examples that bind source adapter guidance, first-action records, and the private setup adapter-chain runbook. Agents could read those examples through a lower-level local command, but not yet through the same transport-neutral envelope and MCP tool surface used for forecast cards, setup bundles, adapter runbooks, and private source adapter guidance.

### Decision

Add `private_source_kind_selection` to the agent adapter operation set, the agent envelope schema, the protocol-map schema, the local dispatcher, generated envelope fixtures, local MCP stdio scaffold, and CLI smoke checks.

The operation returns the generated source-kind selection examples as read-only path guidance. It may recommend source-builder, mapping confirmation, fixture evidence, wait, replace, or reject paths, but it must not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, source reads, credentials, live fetches, hosted-service work, or production runtime behavior.

### Rationale

Agents should be able to ask OPE which private source-kind path to choose through one stable adapter operation before deciding whether to call lower-level setup operations. Returning the checked examples through the envelope keeps status handling, exit codes, MCP mapping, future HTTP/queue mapping, and non-execution boundaries consistent with the rest of the agent-facing surface.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_source_kind_selection` returns a schema-bound envelope for `privatesourcekindselectionexamples-001`.
- The local MCP stdio scaffold exposes `ope_private_source_kind_selection`.
- The protocol map now contains fifteen envelope-returning adapter operations plus the separate forecast-run tool.
- Normal checks verify guidance, first-action, adapter-chain bindings, source-kind recommendations, protocol-map coverage, MCP tool exposure, and no command execution or artifact creation.
- The next milestone should add an optional source-kind query argument so agents can request one recommendation without parsing the full example set.

## DEC-064: Add Source-Kind Selection Query Argument

- Date: 2026-05-18
- Status: Accepted

### Context

The `private_source_kind_selection` adapter operation exposed the full checked selection examples through CLI and MCP. That kept behavior transparent, but an agent that already knows the candidate source kind still had to parse the full list before deciding the next path.

### Decision

Add optional `sourceKind` support to `private_source_kind_selection` across the local dispatcher, `python3 scripts/ope.py agent-call`, MCP argument normalization, and the generated protocol map.

When omitted, the operation still returns the full checked examples record. When provided, it returns a compact selected-example payload with `runtimeStatus: selected_example_only`, `requestedSourceKind`, `availableSourceKinds`, and one `selectedExample`. Unknown source kinds return a sanitized `bad_request` envelope with `payload: null`.

### Rationale

OPE should be easy for agents to call in small, deterministic steps. A single-source-kind query lets callers ask for the one path they need while preserving the same checked guidance source, exit-code semantics, and non-execution boundary as the full examples record.

### Consequences

- `python3 scripts/ope.py agent-call --operation private_source_kind_selection --source-kind private_api` returns the private API recommendation without returning the full examples list.
- The local MCP tool accepts optional `sourceKind` and returns the same selected envelope.
- Unknown source kinds return `bad_request` without raw diagnostics, source reads, setup execution, forecasts, scoring, credentials, live fetches, or hosted runtime work.
- Normal checks verify default full-list behavior, selected private API behavior, unknown-source error behavior, protocol-map field exposure, MCP parity, and read-only guidance boundaries.
- The next milestone should add a generated query fixture matrix so adapter implementers can inspect checked selected and unsupported examples directly.

## DEC-065: Add Private Source-Kind Query Matrix

- Date: 2026-05-19
- Status: Accepted

### Context

The source-kind selection operation can now return the full examples record, one selected source-kind recommendation, or a sanitized unsupported-source error. Those behaviors were covered by smoke tests, but future adapter work benefits from a generated conformance fixture that records the exact response shapes.

### Decision

Add `private-source-kind-query-matrix.schema.json`, `spec/private-source-kind-query-matrix.md`, `scripts/generate_private_source_kind_query_matrix.py`, `scripts/check_private_source_kind_query_matrix.py`, and `python3 scripts/ope.py private-source-kind-query-matrix`.

The matrix stores one full-list adapter envelope, selected envelopes for all checked source kinds, and one unsupported `spreadsheet_macro` bad-request envelope. Each row records expected status, exit code, payload shape, immediate action, selected example ID, and non-execution boundaries.

### Rationale

OPE should make adapter behavior inspectable without requiring agents or implementers to re-run ad hoc calls. A matrix gives future MCP, HTTP, and queue adapters a compact reference while preserving that source-kind selection is recommendation-only.

### Consequences

- `python3 scripts/ope.py private-source-kind-query-matrix` returns a schema-bound conformance record.
- Normal checks validate the matrix against `agent-envelope.schema.json` and the existing source-kind selection examples.
- The matrix covers default full-list, every supported selected source kind, and an unsupported bad-request case.
- The matrix does not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, source reads, credential handling, live fetching, or hosted runtime work.
- The next milestone should add a broader private setup adapter conformance matrix across source-builder, source-handoff, method-gate, forecast-execution, and readback cases.

## DEC-066: Add Private Setup Adapter Conformance Matrix

- Date: 2026-05-19
- Status: Accepted

### Context

Private setup now has generated agent-envelope examples for local-file source-builder, source-handoff, method-gate, forecast-execution, and generated forecast readback operations. Those examples are individually checked, but agents and future adapter implementers need one place to compare expected response shape, status, exit code, next action, and artifact-creation boundaries across the whole setup chain.

### Decision

Add `private-setup-adapter-conformance-matrix.schema.json`, `spec/private-setup-adapter-conformance-matrix.md`, `scripts/generate_private_setup_adapter_conformance_matrix.py`, `scripts/check_private_setup_adapter_conformance_matrix.py`, and `python3 scripts/ope.py private-setup-adapter-conformance`.

The matrix embeds the existing generated envelopes for 31 checked cases: source-builder happy/rejected/error cases, source-handoff cases, method-gate cases, forecast-execution cases, and normal forecast card, lifecycle bundle, resolution status, and scoring summary readbacks for `forecast-1102`.

### Rationale

OPE should let agents and adapter authors inspect private setup adapter behavior without inventing side effects or manually stitching many generated envelope files together. A schema-bound matrix gives a stable conformance reference while preserving that only the confirmed forecast-execution case references generated forecast artifacts, and the matrix itself creates nothing.

### Consequences

- `python3 scripts/ope.py private-setup-adapter-conformance` returns a schema-bound conformance matrix.
- Normal checks validate phase counts, payload shapes, sanitized validation errors, artifact-creation permissions, normal forecast readback routing, and non-execution boundaries.
- The matrix may record that referenced generated envelopes created fixture forecast artifacts, but the matrix itself does not execute adapter calls, read private data, create source manifests, create forecasts, resolve outcomes, score forecasts, fetch live data, store credentials, or create hosted runtime state.
- The next milestone should add a compact agent-readable conformance read surface so normal `agent-call` and MCP callers do not need to load the full embedded-envelope matrix.

## DEC-067: Add Compact Private Setup Adapter Conformance Summary

- Date: 2026-05-19
- Status: Accepted

### Context

The full private setup adapter conformance matrix is useful implementation evidence, but it embeds many generated envelopes. Routine agents need to know operation coverage, phase counts, readback support, sanitized-error coverage, and artifact boundaries without loading that heavier matrix by default.

### Decision

Add `private-setup-adapter-conformance-summary.schema.json`, `spec/private-setup-adapter-conformance-summary.md`, `scripts/generate_private_setup_adapter_conformance_summary.py`, `scripts/check_private_setup_adapter_conformance_summary.py`, and `python3 scripts/ope.py private-setup-adapter-conformance-summary`.

Expose the summary through the existing agent adapter surface as `private_setup_adapter_conformance_summary` and through the local MCP stdio scaffold as `ope_private_setup_adapter_conformance_summary`. The summary references the full matrix path and ID, records compact counts and boundaries, and does not embed the full envelope rows.

### Rationale

OPE should be agent-native without making every normal read carry implementation-sized evidence. A compact conformance summary gives agents a small first read surface while preserving the full matrix for implementers who need exact case-by-case envelopes.

### Consequences

- `python3 scripts/ope.py private-setup-adapter-conformance-summary` returns a schema-bound compact summary.
- `python3 scripts/ope.py agent-call --operation private_setup_adapter_conformance_summary` returns the same summary in a transport-neutral envelope.
- The local MCP stdio scaffold exposes `ope_private_setup_adapter_conformance_summary`.
- The protocol map now contains sixteen envelope-returning adapter operations plus the separate forecast-run tool.
- The summary is read-only and must not execute adapter calls, read private data, create source manifests, create forecasts, resolve outcomes, score forecasts, fetch live data, store credentials, or create hosted runtime state.
- The next milestone should add explicit size-budget checks for compact read surfaces so future generated evidence cannot silently become default agent payload.

### DEC-068 — Add Adapter Read-Surface Size Budgets
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Declare byte budgets in the compact private setup adapter conformance summary and enforce them in summary, adapter, dispatcher, and hardening checks.
- **Why:** Routine agent reads should stay compact and predictable while the full embedded-envelope matrix remains available only through an explicit implementer command.
- **Alternatives rejected:** Relying only on generic `maxBytes` behavior, embedding full matrix excerpts in the compact summary.

### DEC-069 — Add Resolution Readbacks To Agent Adapter
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Expose `resolution_jobs` and `resolution_scheduler_status` as read-only agent adapter and MCP operations backed by checked local fixtures.
- **Why:** Agents need to decide whether to wait, execute an approved resolver, inspect invalid or failed work, or read resolved outputs without parsing local files or terminal scheduler output.
- **Alternatives rejected:** Making agents read `.ope/live` state directly, starting the scheduler from a status read, or adding hosted/OS scheduler claims before the local loop is reliable.

### DEC-070 — Add Resolution Readback Error Envelopes
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Represent missing live workspaces, unreadable state files, malformed scheduler logs, and oversized scheduler readbacks as generated sanitized agent-envelope error examples.
- **Why:** Future adapters need checked failure shapes before OPE expands live scheduler/runtime behavior, and agents need safe next-action signals without raw local paths, state contents, log contents, or stack traces.
- **Alternatives rejected:** Adding live workspace arguments to the read-only adapter operations, probing ignored local files during normal checks, or treating scheduler status reads as a scheduler runtime.

### DEC-071 — Add Resolution Runtime Reliability Read Model
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `resolution-runtime-reliability` contract, generated fixture, CLI command, and checker for runtime failure taxonomy, retry and next-action guidance, provenance ledger rows, and live-capture/source-policy boundaries.
- **Why:** Before expanding the public transport corpus, live source usage, or forecasting methods, agents need one deterministic read model that explains runtime failures and provenance without executing resolvers or reading ignored local files.
- **Alternatives rejected:** Encoding failure semantics only in prose, treating scheduler logs as the provenance ledger, or allowing resolution outcome evidence to appear in forecast-time provenance.

### DEC-072 — Add Transit Forward-Run Corpus Index
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `transit-forward-run-corpus` contract, generated fixture, CLI command, and checker over one comparable scored weather-transit-delay run plus explicit exclusion examples.
- **Why:** OPE needs to report how many public transport forward windows are comparable, scored, excluded, or below claim thresholds before producing track-record or calibration surfaces.
- **Alternatives rejected:** Treating the single forward-run summary as a corpus, creating calibration output from one scored run, or reading ignored `.ope/live/` captures during normal checks.

### DEC-073 — Add Transit Baseline Track-Record Gate
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `transit-track-record-gate` contract, generated fixture, CLI command, and checker over the transit forward-run corpus.
- **Why:** Agents need a compact way to inspect current Brier score, baseline score, lift, sample size, exclusions, and horizon coverage while knowing whether baseline track-record or calibration claims are allowed.
- **Alternatives rejected:** Emitting a normal calibration summary from one scored run, treating below-threshold performance as a public quality claim, or hiding the one-off score until thresholds are met.

### DEC-074 — Add Transit MVP Method Options
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `transit-method-options` contract, generated fixture, CLI command, and checker over the transit corpus and baseline track-record gate.
- **Why:** OPE needs to explain why early public transport runs stay baseline-only, while still preserving evidence for the transparent weather-adjustment candidate and clearly parking richer method families until clean benchmarks exist.
- **Alternatives rejected:** Enabling the weather-adjustment method from one positive fixture lift, adding trained or retrieval-assisted methods without benchmark evidence, or allowing same-window transit outcome rows into forecast-time method evidence.

### DEC-075 — Add Policy-Bound Transit Live Evidence Promotion
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `transit-live-evidence-promotion` contract, generated promotion fixture, sanitized promoted source-set fixture, CLI command, and checker for promoting selected ignored live weather drafts into forecast-time evidence.
- **Why:** OPE needs a narrow way to use approved local live captures without committing raw `.ope/live/` artifacts, weakening provenance, or letting post-close and resolution-only captures leak into forecast evidence.
- **Alternatives rejected:** Reading `.ope/live/` during normal checks, committing raw live captures, treating HSL TripUpdates outcome rows as forecast-time evidence, or adding a production live connector runtime before the local policy gate is explicit.

### DEC-076 — Add Source Adapter Intake Gate
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `source-adapter-intake` contract, generated conformance fixtures, CLI command, and checker for routing sanitized external connector outputs into source intake and method decisions.
- **Why:** Agent-built connectors should be able to live outside OPE core while still handing OPE a standard manifest, mapping, provenance, and boundary record that OPE can accept, reject, or block without executing connector code.
- **Alternatives rejected:** Moving connector implementations into OPE core for MVP, letting source-adapter outputs bypass source intake, or trying to repair unsafe credential/raw-row handoffs inside OPE.

### DEC-077 — Add Local Private Setup Orchestrator Summary
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `private-setup-orchestrator` contract, generated summary fixture, CLI command, and checker that joins setup request, first-action, source-intake, method-gate, explicit forecast-execution, and normal readback outcomes over existing checked local records.
- **Why:** Agents need one compact local MVP read surface for approved local-file and accepted source-adapter paths without manually chaining every lower-level command or losing the source-intake, benchmark, method-decision, and forecast-execution gates.
- **Alternatives rejected:** Creating a runtime that executes private setup commands, letting adapter outputs produce forecasts directly, or hiding blocked paths such as missing approval, unconfirmed mappings, insufficient data, rejected sources, unsafe sources, and oversized readbacks.

### DEC-078 — Declare The Local MVP Release Surface
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add an `mvpLocalRuntime` section to the release manifest, a compact `spec/mvp-local-runtime.md` runbook, and `scripts/check_mvp_release_surface.py` smoke checks for the local MVP happy path, blocked setup paths, agent-call readback, MCP protocol-map exposure, resolution jobs, and corpus claim gates.
- **Why:** The MVP should be understandable and release-checkable as a local agent-native surface, with exact machine interfaces and claim boundaries recorded in a schema-bound artifact.
- **Alternatives rejected:** Treating the README as the only MVP contract, declaring a hosted or HTTP/queue runtime before implementation, or allowing one-off resolved examples to imply calibration or broad quality claims.

### DEC-079 — Add Agent Pilot Validation Pack
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `agent-pilot-validation` contract, generated fixture, CLI command, and checker for local MVP pilot protocol, task scenarios, feedback dimensions, comprehension rubrics, and sanitized synthetic example summaries.
- **Why:** Before adding runtime scope, OPE needs repeatable usability evidence that agents and supervising developers can understand setup paths, readbacks, blocked states, and claim boundaries without storing private data or raw transcripts.
- **Alternatives rejected:** Treating roadmap text as the pilot protocol, storing raw interview transcripts in the repo, or expanding private-source/runtime behavior before measuring MVP comprehension.

### DEC-080 — Add Local Usage Trace Read Model
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `local-usage-trace` contract, generated fixture, CLI command, and checker with synthetic local MVP event rows, trace fields, aggregate product metrics, and privacy boundaries.
- **Why:** OPE needs a measurable local vocabulary for forecast completion, read success, blocked paths, response sizes, and elapsed times before adding opt-in runtime logs or hosted telemetry.
- **Alternatives rejected:** Adding hosted analytics, writing runtime logs during normal checks, or treating synthetic local trace rows as real usage evidence.

### DEC-081 — Add Transit Corpus Growth Loop
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `transit-corpus-growth` contract, generated fixture, CLI command, and checker for append-ready candidates, exclusion-ledger rows, due-run and post-resolution checklists, and threshold progress readback.
- **Why:** The public transport wedge needs a repeatable way to inspect whether new resolved forward runs can grow the comparable corpus while preserving forecast-time versus resolution-only evidence boundaries and keeping quality claims blocked below threshold.
- **Alternatives rejected:** Mutating the canonical corpus during normal checks, treating excluded runs as calibration evidence, or allowing one append-ready example to imply track-record or calibration quality.

### DEC-082 — Add Source Quality Mapping Confidence Readback
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `source-quality` read model, generated fixture, CLI command, and checker over builder drafts, source-adapter intake, source-intake reports, and setup method decisions.
- **Why:** Agents need compact guidance that explains whether connected data is forecast-usable, baseline-only usable, mapping-confirmation blocked, data-sparse, rejected, or unsafe before they proceed to method gates or explicit forecast execution.
- **Alternatives rejected:** Letting source quality create forecast artifacts, executing source-builder or adapter code from the readback, or treating quality summaries as production-readiness or forecast-quality claims.

### DEC-083 — Add Approved Local Source Runtime
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `local-source-runtime` contract, generated fixture, CLI command, and checker for one caller-approved local-folder runtime that routes accepted files through existing builder, intake, benchmark, method, and explicit forecast-execution gates to the `forecast-1102` card.
- **Why:** The roadmap needs one concrete source runtime pattern that proves approved local data can reach a forecast readback while preserving approval, allow-list, size-limit, source-policy, and sanitized-diagnostic boundaries.
- **Alternatives rejected:** Adding arbitrary private API or database parsing, storing credentials or raw rows, installing a hosted/local watcher, letting the runtime create forecast artifacts directly, or treating the narrow runtime as production connector support.

### DEC-084 — Add Developer Adoption Surface
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `developer-adoption` contract, generated fixture, CLI command, and checker for quickstart steps, one complete local setup scenario, CLI/agent-call/MCP stdio integration notes, release-note boundaries, and a deferred generated-types decision.
- **Why:** The local MVP needs a fast, testable path to the first forecast card and lifecycle bundle so developers and agents can try OPE without misreading fixture-mode examples as hosted runtime or quality claims.
- **Alternatives rejected:** Leaving onboarding only in prose, adding generated language-specific runtime types before adoption evidence justifies them, or letting an adoption guide execute setup commands, fetch live data, or create forecast artifacts.

### DEC-085 — Add Expansion Readiness Gate
- **Date:** 2026-05-27
- **Status:** accepted
- **Choice:** Add a checked `expansion-readiness` contract, generated fixture, CLI command, and checker over hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types.
- **Why:** After the local MVP adoption surface, OPE needs a disciplined way to decide what not to build yet, using pilot, usage, source-runtime, corpus, and track-record evidence before widening runtime scope.
- **Alternatives rejected:** Starting hosted service work from roadmap enthusiasm alone, treating synthetic pilot notes or one comparable transit run as enough evidence for stronger methods, or generating runtime types before adoption friction shows they are worth maintaining.

### DEC-086 — Add Pilot Evidence Ledger
- **Date:** 2026-05-28
- **Status:** accepted
- **Choice:** Add a checked `pilot-evidence` contract, generated fixture, CLI command, and checker for sanitized pilot-session summary intake.
- **Why:** The next roadmap step needs real agent/developer pilot evidence, but the repository needs a safe format first: dimension scores, sanitized findings, friction classes, and expansion signals without raw transcripts, private data, credentials, prompt logs, or participant identities.
- **Alternatives rejected:** Storing raw pilot transcripts, counting synthetic examples as real adoption evidence, allowing private session details into checked fixtures, or letting pilot notes unblock hosted/runtime/type-generation work before real sanitized session thresholds are met.

### DEC-087 — Add Pilot Session Packet
- **Date:** 2026-05-28
- **Status:** accepted
- **Choice:** Add a checked `pilot-session-packet` contract, generated fixture, CLI command, and checker for running real local MVP pilot sessions safely.
- **Why:** The pilot evidence ledger defines what can be stored, but agents and moderators also need a checked task packet, sanitization review, and stop conditions before real sessions begin.
- **Alternatives rejected:** Running pilot sessions from ad hoc notes, storing raw transcripts for later redaction, letting the packet write ledger rows, or treating session collection readiness as expansion evidence.

### DEC-088 — Add Pilot Summary Intake Classifier
- **Date:** 2026-05-28
- **Status:** accepted
- **Choice:** Add a checked `pilot-summary-intake` contract, generated fixture, CLI command, and checker for classifying sanitized pilot summaries before ledger review.
- **Why:** Real pilot sessions need one safe pre-ledger decision point that can accept ledger-ready summaries, request redaction, or block raw transcripts, private rows, credentials, participant identity, and quality overclaims.
- **Alternatives rejected:** Letting moderators copy summaries directly into the ledger, storing unsafe notes for later cleanup, counting checked examples as real sessions, or letting accepted pilot summaries unblock expansion.

### DEC-089 — Add Repeating Prediction Setup Contract
- **Date:** 2026-05-28
- **Status:** accepted
- **Choice:** Add a checked `repeating-prediction-setup` contract, generated fixture, CLI command, and checker for recurrence policies, end conditions, and post-calibration behavior before campaign execution exists.
- **Why:** Agents need a stable local-first way to describe finite, until-date, interval, open-ended, weekday/window, and calibration-threshold campaigns without inventing shell loops or implying a scheduler, hosted runtime, or quality claim.
- **Alternatives rejected:** Starting with a foreground runner before the manifest contract, writing cron or OS scheduler configuration, mutating local campaign state during normal checks, or letting calibration thresholds auto-tune methods.

### DEC-090 — Add Prediction Campaign Manifest
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Add a checked `prediction-campaign-manifest` contract, generated fixture, CLI command, and checker that expands one repeating setup into unique dry-run campaign, cycle, run, question, forecast, resolution, and scoring IDs.
- **Why:** Before a terminal runner exists, agents need a resumable local manifest shape that can answer what is planned, what is due later, which duplicate keys are blocked, and where ignored local state will live without creating artifacts.
- **Alternatives rejected:** Letting the first runner invent campaign IDs, writing `.ope/live/` campaign state during normal checks, reusing fixture forecast IDs for live campaign plans, or starting scheduler work before duplicate and status boundaries are checked.

### DEC-091 — Add Prediction Campaign Runner Dry-Run Surface
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Add a checked `prediction-campaign-runner` contract, generated fixture, CLI command, and checker for `prediction-campaign start` command semantics, recurrence flags, output modes, dry-run decisions, and non-execution boundaries.
- **Why:** Agents need to see how a terminal campaign runner will behave before OPE creates forecast artifacts, sleeps or polls, writes ignored live state, fetches live data, runs resolvers, or implies calibration quality.
- **Alternatives rejected:** Starting with an effectful foreground loop, letting normal checks write campaign state, hiding missed-run and duplicate policies in prose, or treating dry-run runner decisions as forecast or calibration evidence.

### DEC-092 — Add Prediction Campaign Forecast Creation Handoff
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Add a checked `prediction-campaign-forecast-creation` contract, generated fixture, CLI command, and checker that binds a ready campaign runner decision to planned question, forecast, card, and lifecycle-bundle IDs.
- **Why:** Before implementing artifact mutation, OPE needs a stable handoff that proves the next forecast can be selected, checked before close, bound to source policy and duplicate-key rules, and kept separate from live fetches, resolver execution, and quality claims.
- **Alternatives rejected:** Creating ignored campaign artifacts during normal checks, letting the runner invent forecast paths at execution time, backfilling missed forecasts, or mixing forecast creation with due resolution and corpus append behavior.

### DEC-093 — Add Checked Campaign Forecast Artifact Fixture
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Add a checked `prediction-campaign forecast-artifact` generator, fixture set, CLI readback, and checker that materializes `forecast-1301` as unresolved baseline-only question, evidence, artifact, and history records using existing lifecycle schemas.
- **Why:** Agents need to see the actual OPE-standard forecast records that follow the campaign handoff before OPE implements ignored live-state mutation, live evidence capture, resolver execution, scoring, or corpus append behavior.
- **Alternatives rejected:** Adding a campaign-specific forecast schema, writing `.ope/live/` campaign artifacts during normal checks, resolving and scoring the future run immediately, or selecting a non-baseline method before comparable transit evidence clears the gate.

### DEC-094 — Add Prediction Campaign Forecast Write Plan
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Add a checked `prediction-campaign forecast-write` contract, generated fixture, CLI readback, and checker that bind the `forecast-1301` lifecycle records to intended ignored `.ope/live` target paths and write guards without executing the local write.
- **Why:** Before effectful campaign state mutation exists, agents need a stable target-path, idempotency, source-policy, duplicate-key, and forecast-before-close plan they can inspect and validate.
- **Alternatives rejected:** Copying fixtures into `.ope/live/` during normal checks, letting the future runner invent write paths at execution time, storing private rows or credentials, or mixing local writes with live fetch, resolution, scoring, corpus append, or quality claims.

### DEC-095 — Add Campaign-Aware Resolution Job Readback
- **Date:** 2026-05-29
- **Status:** accepted
- **Choice:** Extend the checked `resolution-jobs` registry with `--campaign predictioncampaign-001`, a campaign fixture, CLI checks, and release-smoke wiring that add the `forecast-1301` campaign wait state alongside existing forward-run jobs.
- **Why:** Campaign-created forecasts need to appear in the same agent-facing resolution queue before campaign resolver execution, scheduler integration, resume, or corpus append behavior exists.
- **Alternatives rejected:** Executing campaign resolvers from the registry, writing `.ope/live` campaign state during normal checks, inventing a separate campaign-only queue, or treating the waiting campaign forecast as resolution, scoring, corpus, or calibration evidence.
