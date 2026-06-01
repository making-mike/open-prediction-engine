# Open Prediction Engine Product Context

Last updated: 2026-05-31

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
- Domain setup and local source runtime: a fixture-ready weather-logistics setup, a candidate seaport berth-availability setup, setup benchmark gates, setup-aware method decisions, setup-aware deterministic and baseline forecast execution, and an approved local-folder runtime with caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics.
- Private setup guidance: private setup workflow, request routing, first-action dispatch, first-action runbook, agent bundle, local orchestrator summary, private adapter-chain runbook, adapter conformance matrix and compact summary, private source adapter capabilities, outcome matrix, intake bridge, guidance operation, source-kind examples, and source-kind selection/query readbacks. These surfaces guide agents without executing private sources.
- Agent interfaces: transport-neutral agent envelopes, local `agent-call`, local MCP stdio scaffold, protocol map for MCP plus future HTTP/queue adapters, private setup source-builder/source-handoff/method-gate/forecast-execution operations, forecast readback operations, campaign plan/status/health/append-readiness/calibration-status operations, method-update gate and plan readbacks, and the forecast-run tool.
- Pilot and adoption: agent pilot validation pack, pilot evidence ledger, pilot session packet, pilot summary intake classifier, local usage trace read model, developer adoption surface, expansion-readiness gate, release manifest, MVP local runtime runbook, CI release gate, hardening checks, and the local CLI wrapper.
- Public beta transit wedge: opt-in HSL GTFS-RT TripUpdates capture, static GTFS schedule join, transit forward-run workflow, transit corpus growth loop, baseline track-record gate, method options, live evidence promotion gate, resolution job registry, foreground scheduler, resolver-agent command, and runtime reliability readback.
- Repeating prediction campaigns: repeating setup contract, campaign manifest, terminal runner, forecast scheduling, bounded foreground ticks, runner-clock `--now`, missed-run policy, guarded `--write-local` creation, forecast-creation handoff, unresolved `forecast-1301` artifact, forecast-write plan and explicit local write runtime, resolution-attempt readback, doctor, resume, append-only evidence ledger, calibration-status readback, method-update gate/plan/apply/rollback, pilot explain readback, the 100-run Helsinki pilot operations runbook with a 3-run smoke path, and a pilot launch-readiness gate.

Normal checks remain fixture/dry-run oriented, offline, and non-mutating. Live captures, local writes, resolver execution, and ledger appends require explicit opt-in flags, and quality/calibration claims remain blocked until comparable outcome evidence supports them.

The repository does not yet implement:

- Arbitrary manual upload, private API, or database parsing beyond checked setup fixtures, the approved local-folder runtime, and capability declarations.
- Generated language-specific runtime types.
- Additional setup-aware methods beyond the current deterministic fixture path.
- Source-quality-driven source execution or artifact creation.
- Canonical corpus mutation from the checked transit corpus growth loop.
- Forecast execution from ignored local live drafts outside the explicit transit forward-run workflow.
- General source-builder forecast execution beyond the checked source-handoff fixture path.
- Production forecast use of live connector results.
- Hosted polling or hosted scheduling of transit captures or resolver execution.
- Repeated live transit calibration runs, live auto-evidence gathering, or unrestricted live evidence gathering.
- A hosted service, HTTP API, production agent adapter runtime, production source discovery, or OS scheduler installation.
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
- agent protocol compatibility beyond the tested local MCP stdio scaffold

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
```

The validation should measure whether a developer can trust the artifact enough to let an agent use it for decision support, while still understanding the uncertainty and claim boundaries.
