# Open Prediction Engine Product Context

Last updated: 2026-06-07

## Product Direction

Open Prediction Engine (OPE) is an open-source, agent-native forecasting package and standard for setting up private, evidence-producing prediction engines. An agent or developer should be able to connect chosen source data, define a resolvable forecast domain, request a probability, update that probability when new evidence arrives, and preserve the forecast, evidence, method, provenance, resolution, score, and calibration trail as OPE-standard records.

OPE should be easy for agents to call and safe for developers to supervise. The primary runtime actor is an agent or automated workflow. The primary adopter is a developer building an agentic or operational system.

## Product Thesis

We believe agents and the developers who supervise them need a better way to set up prediction engines from their own source data, because agents can gather, connect, and act on data, but they need a disciplined forecasting standard that makes questions resolvable, evidence inspectable, methods explicit, predictions probabilistic, recalculations traceable, and performance measurable.

## User Need

The developer wants an agent to act under uncertainty without relying on unverifiable model prose or ad hoc probability logic, so the agent connects files, APIs, or private databases and asks for a forecast, but it needs OPE to validate the setup, choose the best justified method for the available data, return a probability, preserve recalculation history, and later resolve and score the result.

## Product Promise

OPE should let an agent ask:

```text
Given this future-facing question and these allowed sources, set up or use an OPE-compatible prediction engine that returns a probabilistic forecast I can inspect, update, resolve later, and score against a baseline.
```

The default product posture should be flexible about sources and strict about forecast records:

```text
connect chosen source data
declare source policy and resolution rules
produce OPE-standard forecast artifacts
label quality and claim boundaries honestly
```

That does not mean OPE only supports centrally approved data sources. A private OPE engine may use internal files, databases, APIs, manual mappings, or agent-assisted extraction when the caller permits them. It means OPE records what was connected, how it was interpreted, what method was selected, what changed between forecast updates, and what quality claim is justified.

The default data mode may eventually be `data: auto`, but auto-evidence should mean best available allowed evidence for that engine setup, not unbounded crawling or a claim to all internet knowledge.

OPE should also support a conservative no-API mode when a caller restricts the source policy to historical data only. In that case the forecast should remain a baseline or historical-model forecast, explicitly marked as not using forecast-time API evidence.

## Core Experience

The target loop is:

1. Agent or developer submits a future-facing forecast request.
2. OPE checks whether an existing domain setup applies or helps the agent create a candidate setup.
3. OPE normalizes the request into a resolvable forecast question and resolution rule.
4. OPE accepts or inspects caller-provided source data, connectors, and mappings under a declared source policy.
5. OPE creates an evidence plan and records what data is usable, missing, stale, inferred, or rejected.
6. OPE normalizes sources and records provenance, freshness, source quality, and mapping confidence.
7. OPE builds a transparent baseline forecast.
8. OPE selects the best justified enabled method for the connected data and compares it to the baseline.
9. OPE emits a forecast artifact, evidence packet, forecast card, evidence trace, and lifecycle bundle.
10. OPE recalculates by appending forecast-history entries when new data arrives.
11. OPE resolves the outcome from declared sources when available.
12. OPE scores the forecast and updates calibration and track-record summaries.

## Current State

OPE is currently fixture-ready with checked forecast-generation, resolution, scoring, source, setup, adapter, campaign, pilot, and release surfaces.

Current checked surfaces are grouped here so future milestones can add focused bullets instead of rewriting broad status prose:

- Core lifecycle: contracts, fixtures, scoring, request intake, source policy, evidence plans, evidence-source sets, forecast cards, evidence traces, lifecycle bundles, recalculation history, historical-only baseline forecasts, local forecast-run summaries, intake matrices, and runbooks.
- Source and connector gates: source connector contracts, opt-in live connector readiness, ignored live-capture workspace, source adapter output, source adapter intake, source-quality and mapping-confidence readbacks, source manifest builder, source-intake reports, source-builder handoffs, source-handoff method gates, confirmed source-handoff forecast execution for `forecast-1102`, and source-handoff resolution and scoring with quality claims still sample-size-blocked.
- Domain setup and local source runtime: a fixture-ready weather-logistics setup, a candidate seaport berth-availability setup, a checked domain/source field policy that separates universal fields from domain-specific extensions and blocked credential/raw/claim fields, checked credential-reference and private auto-evidence policies for opaque caller-owned private API/database references and private `data: auto` source-policy gates, setup benchmark gates, setup-aware method decisions, setup-aware deterministic and baseline forecast execution, and an approved local-folder runtime with caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics.
- Private setup guidance: private setup workflow, request routing, first-action dispatch, first-action runbook, agent bundle, local orchestrator summary, private adapter-chain runbook, adapter conformance matrix and compact summary, private source adapter capabilities, outcome matrix, intake bridge, guidance operation, source-kind examples, and source-kind selection/query readbacks. These surfaces guide agents without executing private sources.
- Agent interfaces: transport-neutral agent envelopes, local `agent-call`, local MCP stdio scaffold, protocol map for MCP plus future HTTP/queue adapters, checked MCP adoption transcripts, optional OPP provider-adapter fixture, runtime transport readiness gate, agent integration readiness/candidates/guided-forecast readbacks, agent guidance loop readbacks, stable prediction-feature setup request/response readbacks, private setup source-builder/source-handoff/method-gate/forecast-execution operations, forecast readback operations, campaign plan/status/health/append-readiness/calibration-status operations, method-update gate and plan readbacks, and the forecast-run tool.
- Runtime and storage: lifecycle operation store, storage adapter, Postgres compatibility checkpoint, approved database source-adapter runtime boundary, runtime hardening, an opt-in persistent SQLite path policy that requires caller approval and keeps normal checks ephemeral, a lifecycle lease policy that separates strict leases from idempotency-only retry guards, a runtime transport readiness gate that keeps HTTP, queue, hosted service, and OPP HTTP provider behavior deferred, a tenant-scoped workspace isolation readback for resources, queues, source bindings, credential references, and blocked cross-tenant access, a retention/redaction policy that keeps tombstones and receipts as default delete replacements while physical deletion remains an exception preflight, and a private auto-evidence policy that keeps private-source reads, raw SQL, broad web search, and secret resolution out of normal checks.
- Pilot and adoption: agent pilot validation pack, pilot evidence ledger, ignored-local receipt-backed pilot evidence append/readback path, pilot session packet, pilot summary intake classifier with caller-supplied sanitized-summary file classification, pilot summary review bundle, simulated agent pilot readback, pilot findings readback with optional ignored-local evidence inclusion, generated runtime types decision, local usage trace read model, general prediction-agent adoption surface, checked `setup-engine` front door with structured request input, checked prediction-goal catalog, root `AGENT_QUICKSTART.md`, root `ope.capabilities.json`, developer adoption surface, agent incorporation golden path, copyable embedded prediction-feature example, expansion-readiness gate, release manifest, MVP local runtime runbook, CI release gate, hardening checks, and the local CLI wrapper.
- Public beta transit wedge: opt-in HSL GTFS-RT TripUpdates capture, static GTFS schedule join, transit forward-run workflow, transit corpus growth loop, baseline track-record gate, method options, live evidence promotion gate, resolution job registry, foreground scheduler, resolver-agent command, and runtime reliability readback.
- Repeating prediction campaigns: repeating setup contract, campaign manifest, terminal runner, forecast scheduling, bounded foreground ticks, runner-clock `--now`, missed-run policy, guarded `--write-local` creation, forecast-creation handoff, unresolved `forecast-1301` artifact, forecast-write plan and explicit local write runtime, resolution-attempt readback, doctor, resume, append-only evidence ledger, calibration-status readback, method-update gate/plan/apply/rollback, pilot explain readback, the 100-run Helsinki pilot operations runbook with a 3-run smoke path, and a pilot launch-readiness gate.

Normal checks remain fixture/dry-run oriented, offline, and non-mutating. Live captures, local writes, resolver execution, and ledger appends require explicit opt-in flags, and quality/calibration claims remain blocked until comparable outcome evidence supports them.

For general host-project adoption, the compact front door is:

```bash
python3 scripts/ope.py setup-engine --goal "<host prediction goal>"
python3 scripts/ope.py setup-engine --request spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json --view request
python3 scripts/ope.py setup-engine --request spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json --view forecast-card-preview
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
python3 scripts/ope.py capabilities
python3 scripts/ope.py adoption-eval
```

These commands position OPE as the shortcut for setting up a reliable prediction engine with credibility gates built in. They should help agents identify candidate forecast contracts, source roles, baseline guidance, forecast-card preview shape, resolver/scorer loop, calibration gate, and host responsibilities before they invent an app-specific ad hoc risk engine.

`setup-engine` is the checked canonical command for that front door. It accepts goal text for fast orientation and a structured setup request when the caller can provide decision context, outcome, horizon, source hints, resolution hints, baseline hints, and explicit safety flags. Its forecast-card preview view shows card fields that are safe before forecast execution and explicitly blocks probabilities, forecast IDs, confidence labels, quality claims, calibration claims, credentials, raw rows, and raw SQL. `prediction-goal-catalog` is the checked generic example catalog for agents mapping a host goal before committing to a contract. The embedded host wrapper is the checked setup-first example for rendering `setupEnginePlan` before forecast-card reads. `explain-fit`, `capabilities`, `adoption-eval`, `agent-implementation-kit`, and `prediction-feature-setup` remain local follow-up surfaces. None of these add frontend, hosted API, trained model, scheduler, generic crawler, or notification claims.

The repository does not yet implement:

- Arbitrary manual upload, private API, or database parsing beyond checked setup fixtures, the approved local-folder runtime, and capability declarations.
- Generated language-specific runtime types.
- Additional setup-aware methods beyond the current deterministic fixture path.
- Source-quality-driven source execution or artifact creation.
- Canonical corpus mutation from the checked transit corpus growth loop.
- Persistent SQLite as the default runtime, persistent database creation during normal checks, or automatic ignored-JSON migration.
- Lease acquisition during normal readbacks or raw lock-control APIs for agents.
- Local HTTP listeners, hosted service runtime, queue runtime, or OPP HTTP provider runtime during normal checks.
- Forecast execution from ignored local live drafts outside the explicit transit forward-run workflow.
- General source-builder forecast execution beyond the checked source-handoff fixture path.
- Production forecast use of live connector results.
- Hosted polling or hosted scheduling of transit captures or resolver execution.
- Repeated live transit calibration runs, live auto-evidence gathering, or unrestricted live evidence gathering.
- A hosted service, HTTP API, OPP HTTP/SSE/payment/aggregation provider runtime, production agent adapter runtime, production source discovery, or OS scheduler installation.
- Live calibration claims.

The expansion-readiness gate keeps those areas blocked or deferred until real pilot sessions, corpus growth, and adoption evidence justify a specific next runtime investment.

## Reference Wedge

The first reference wedge remains `weather-logistics`: short-horizon probability of declared weather-linked last-mile logistics disruption.

This wedge is useful because it can start with public weather data, declared source policies, simple baselines, frequent outcomes, and relatively low risk. It also exposes a hard product truth: evidence may be enough to estimate risk, but declared outcome or proxy sources are still needed for fair resolution.

The product vision remains domain-agnostic. Weather-logistics is the reference implementation used to prove the OPE standard, not the identity or limit of the product. A seaport berth-availability setup, demand-risk setup, field-operations setup, or other private engine should follow the same OPE-standard loop: domain setup, source connection, method selection, forecast artifacts, recalculation history, resolution, scoring, and calibration.

## Public Beta Candidate

The selected public beta candidate wedge is `weather-transit-delays`: short-horizon probability that a declared public transport network exceeds a delay threshold during a declared service window, using forecast-time weather and transit evidence.

This is not a quality claim yet. Current checked beta-candidate surfaces are:

- `python3 scripts/ope.py transit-delay-forecast`: reads approved CSV/JSON weather, historical delay, and optional trip-update outcome files, then emits schema-bound forecast, resolution, and scoring records.
- `python3 scripts/ope.py transit-api-connector`: captures HSL GTFS-RT TripUpdates only when explicitly run with `--live`, and can derive local delay rows with `--schedule-join`.
- `python3 scripts/ope.py transit-delay-forward-run`: runs the connector-backed forward-run surface; fixture mode runs forecast, resolution, and scoring end to end, while explicit local live phases can save a pre-window forecast and later resolve it from HSL TripUpdates.
- `python3 scripts/ope.py transit-forward-run-corpus`: reports the checked corpus count, one comparable scored run, six exclusion examples, and the sample-size claim boundary.
- `python3 scripts/ope.py transit-corpus-growth`: reports append-ready comparable candidates, exclusion-ledger rows, due-run and post-resolution checklists, and progress toward 30-run track-record and 100-run calibration thresholds.
- `python3 scripts/ope.py transit-track-record-gate`: reports below-threshold Brier, baseline score, lift, sample sizes, and horizon/window coverage while withholding calibration summaries.
- `python3 scripts/ope.py transit-method-options`: explains why baseline-only execution remains the default and why the weather-adjustment candidate is evidence-only below threshold.
- `python3 scripts/ope.py prediction-campaign method-update-gate`: checks whether calibration evidence, approval, anti-leakage, and benchmark conditions are enough to prepare a future explicit method-update plan, while never changing methods or probabilities.
- `python3 scripts/ope.py prediction-campaign method-update-plan`: records the approval artifact, explicit apply/rollback command shape, rollback record, and preflight checks without running that command during normal checks.
- `python3 scripts/ope.py prediction-campaign pilot-runbook`: records the local 100-run Helsinki pilot procedure, 3-run smoke command sequence, operator status commands, success criteria, abort criteria, and baseline-first method boundary.
- `python3 scripts/ope.py prediction-campaign pilot-readiness`: records checked launch prerequisites, manual operator confirmations, launch commands, and blocked actions before any effectful 100-run pilot write.
- `python3 scripts/ope.py agent-integrate --view candidates`: answers what can be forecasted from the Helsinki starter context with forecastable, needs-clarification, blocked, and rejected candidate contracts and exact reason codes.
- `python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output`: returns the `forecast-1102` forecast-card command within the three-call target while blocked guided cases return no forecast IDs.
- `python3 scripts/ope.py prediction-goal-catalog --view summary`: shows generic delivery, inventory, SLA, demand, churn, seaport, weather-sensitive operations, and transit setup examples without implying calibrated domain quality.
- `python3 scripts/ope.py agent-implementation-kit --view quickstart`: gives external coding agents the first safe local sequence for adding an OPE-backed prediction feature, including the setup-first host wrapper, guided forecast, forecast-card readback, and lifecycle-bundle inspection without adding a hosted runtime.
- `python3 scripts/ope.py agent-guide --section generic`: tells the calling agent which reusable host-goal, outcome, horizon, approved-source, baseline, and resolution questions to ask before running setup-engine.
- `python3 scripts/ope.py agent-guide --case needs_clarification`: keeps the Helsinki bus-scope narrowing as one checked example, not the default adoption path.
- `python3 scripts/ope.py prediction-feature-setup --view response --case accepted`: returns one compact host-feature setup response with existing forecast-card and lifecycle-bundle read commands while keeping source execution, raw private payloads, hosted runtime, and quality claims blocked.
- `python3 scripts/ope.py simulated-agent-pilot --section summary`: reports the eight-session agent-only simulation with one user prompt, seven generated prompts, three non-Helsinki setup-comprehension prompts, approximate tokens, deterministic elapsed-time estimates, and zero real sessions counted.
- `python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json`: prints a dry-run ignored-local append plan for a sanitized pilot summary without writing rows or counting real sessions.
- `python3 scripts/ope.py pilot-session-brief --section summary`: joins the setup-comprehension task, generic agent guide, non-ledger-ready draft status, and local evidence command loop for one supervised session without running the session or writing evidence.
- `python3 scripts/ope.py pilot-summary-review --section summary`: joins one sanitized summary's intake classification, dry-run append eligibility, and explicit local evidence next action without writing evidence.
- `python3 scripts/ope.py pilot-summary-template --section draft`: prints a schema-valid draft summary that remains non-ledger-ready until an operator fills sanitized ratings and clears risk signals.
- `python3 scripts/ope.py lifecycle-operation-store --scenario pilot-evidence-append`: checks the operation receipt, idempotency, lease, planned write, and `pilot_findings` read-model effect for explicit pilot evidence local writes without upgrading calibration or track-record claims.
- `python3 scripts/ope.py pilot-findings --from-local-ledger --section summary`: explicitly includes ignored local pilot evidence when present while keeping quality, calibration, hosted-runtime, and generated-type claims blocked.
- `python3 scripts/ope.py pilot-supervision-status --section commands`: tells moderators and agents the next setup-comprehension task, remaining real-session thresholds, and the safe classify, explicit local append, findings, and status-review loop.
- `python3 scripts/ope.py transit-live-evidence-promotion`: records the gate for turning an approved ignored live weather draft into a sanitized forecast-time source set, while rejecting post-close and resolution-only captures as forecast evidence.
- `python3 scripts/ope.py resolution-jobs` and `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001`: expose the safe read-only job queue and the checked campaign forecast wait state without executing campaign resolvers.
- `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001` and `python3 scripts/ope.py resolution-scheduler --live --watch`: expose campaign-aware scheduler ticks and local foreground polling.
- `python3 scripts/ope.py resolve-due-forward-runs`: provides the explicit execution path for due saved runs.
- `python3 scripts/ope.py resolution-runtime-reliability`: records failure taxonomy, retry guidance, provenance ledger, and live-capture boundary.

The remaining public beta work is repeated comparable live windows and enough resolved outcomes to make any calibration claim. Hosted scheduling can remain optional later rather than a beta prerequisite.

## Agent Product Requirements

Agent-facing surfaces should be:

- JSON-first and schema-bound
- deterministic when run in fixture or dry-run mode
- explicit about mode: fixture, dry-run, live-fetch, or effectful
- explicit about source policy, connected sources, mappings, and allowed connectors
- clear about what evidence was used and what was unavailable
- clear about whether a domain is candidate, fixture-ready, benchmarked, live-provisional, or calibrated
- compact enough for tool-call context through forecast cards
- auditable through lifecycle bundles
- strict about request/result binding
- safe by default for secrets, private intent, and prompt/source injection
- honest about sample size and calibration boundaries

## Claim Boundaries

OPE may say it is building agent-native forecasting infrastructure.

OPE must not claim:

- access to all available internet evidence
- universal prediction ability
- state-of-the-art performance before benchmark evidence exists
- best possible performance without tying the claim to connected data, enabled methods, baseline comparisons, and observed track record
- live calibration before enough comparable outcomes resolve
- production service readiness before a service runtime exists
- agent protocol compatibility beyond the tested local MCP stdio scaffold and checked fixture-level OPP mapping

The stronger claim to earn is:

```text
For a declared engine setup, OPE can use connected source data, select the best justified enabled forecasting method, produce a probabilistic forecast, preserve provenance, recalculate as evidence changes, resolve outcomes, score performance, and report calibration with sample-size boundaries.
```

For historical-only requests, the honest claim is narrower: OPE can produce a baseline probabilistic forecast from committed historical data without live source access.

## Product Metrics

North-star metric:

```text
Agent forecast completion rate for resolvable requests with valid forecast cards and lifecycle bundles.
```

Supporting metrics:

- time from request to forecast card
- percentage of agent incorporation flows that reach a forecast-card command within the routine call-count target
- percentage of requests accepted, clarified, rejected, or approval-gated
- percentage of forecasts with valid source policy and provenance
- baseline coverage by domain and horizon
- resolved comparable outcome count
- baseline lift once enough outcomes exist
- calibration error once enough outcomes exist
- source freshness and source failure rates
- agent read success rate for cards, evidence traces, and bundles

The current local metric readback is:

```bash
python3 scripts/ope.py local-usage-trace
```

## Next Validation Step

Before expanding domains, OPE should validate one agent-native flow:

```text
Ask an agent to set up an OPE-compatible prediction engine for one operational app feature from connected source data, inspect whether OPE can explain what is predictable, produce a claim-safe forecast card, update the forecast when evidence changes, and later resolve and score the result.
```

The checked pilot pack is available through:

```bash
python3 scripts/ope.py agent-pilot-validation
python3 scripts/ope.py agent-pilot-validation --case local_file_setup_readback
python3 scripts/ope.py pilot-supervision-status --section summary
python3 scripts/ope.py pilot-session-brief --section commands
python3 scripts/ope.py pilot-summary-review --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json --section commands
python3 scripts/ope.py pilot-summary-template --section draft
```

The validation should measure whether a developer can trust the artifact enough to let an agent use it for decision support, while still understanding the uncertainty and claim boundaries.
