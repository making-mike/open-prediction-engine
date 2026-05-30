# Open Prediction Engine Product Context

Last updated: 2026-05-27

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

OPE is currently fixture-ready with an initial auto-evidence dry-run, fixture-replay, forecast-generation, resolution, and scoring surface. The repository already has contracts, fixtures, scoring, fixture-mode live-source handling, request intake, source-policy, connector-bound evidence-plan, connector-aware evidence-source-set, source-connector contracts, an opt-in live connector readiness gate, an ignored local live-capture workspace for sanitized connector results and source-set drafts, domain setup records for a fixture-ready weather-logistics reference setup and a candidate seaport berth-availability private setup, a local source manifest builder for small caller-approved CSV/JSON files, source-builder to source-intake handoff records that guide agent next actions, source-handoff method gates that route confirmed builder handoffs into benchmark-gated method decisions without creating forecasts, explicit source-handoff forecast execution that creates `forecast-1102` only for the confirmed handoff, source-handoff resolution and scoring for that forecast with quality claims still sample-size-blocked, a checked source-quality and mapping-confidence readback over builder, adapter-intake, source-intake, and setup-method surfaces, a checked approved local-folder source runtime that requires caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics before reading the existing `forecast-1102` card, a checked developer adoption surface with quickstart, complete local setup scenario, CLI/agent-call/MCP integration notes, release-note boundaries, and deferred generated-types decision, a checked expansion-readiness gate that keeps hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types blocked or deferred until real pilot, corpus, and adoption evidence justify them, a checked source-handoff setup runbook for agents, a domain-agnostic private setup workflow contract that labels manual uploads, private APIs, and databases as planned-only runtimes, a checked private setup request contract that classifies setup intent before source reads, a checked private setup first-action dispatcher that returns one compact non-executing action from a request ID or request JSON, a checked private setup first-action runbook that maps dispatcher statuses to safe caller-visible next steps, a checked private setup agent bundle that joins request, action, and runbook guidance into one read-only response, a checked local private setup orchestrator summary that joins request, first-action, source intake, method gate, explicit forecast execution, and normal readback outcomes without executing commands, a checked agent pilot validation pack for 3-5 local MVP sessions with task scenarios, feedback dimensions, comprehension rubrics, and sanitized synthetic example summaries, a checked pilot evidence ledger with sanitized intake examples, raw-transcript/private-data blockers, claim-confusion signals, and zero real sessions counted so far, a checked pilot session packet with real-session task cards, sanitization review, ledger-ready summary shape, and stop conditions, a checked pilot summary intake classifier for ledger-ready, redaction-needed, and blocked sanitized summaries, a checked local usage trace read model with synthetic MVP event rows, response sizes, elapsed times, sanitized error classes, and aggregate product-metric readbacks, a private setup bundle adapter operation that returns the same guidance through the transport-neutral envelope and local MCP scaffold without executing setup commands, a private setup source-builder adapter operation that inspects caller-approved local CSV/JSON paths and returns draft manifest/mapping guidance without creating forecast or score records, a private setup source-handoff adapter operation that returns checked handoff status, mapping confirmation, intake binding, and method-gate readiness without creating forecast or score records, a private setup method-gate adapter operation that returns setup benchmark and method-decision guidance without creating forecast or score records, a private setup forecast-execution adapter operation that returns setup forecast runs and forecast artifacts only for the confirmed checked handoff while leaving blocked cases non-generating, generated private setup forecast readback examples through normal card, bundle, resolution, and scoring adapter operations, a checked private setup adapter-chain runbook that lists the local-file setup operation sequence and readback path without executing adapter calls, a private setup adapter-chain runbook adapter operation that returns that sequence guidance through the transport-neutral envelope and local MCP scaffold without executing adapter calls, a checked private setup adapter conformance matrix and compact summary that let agents inspect setup adapter behavior without loading every embedded envelope, a checked private source adapter capability contract that declares adapter permissions and non-execution boundaries, a checked private source adapter outcome matrix that maps adapter states to safe agent next actions, a checked private source adapter intake bridge that maps those outcomes to source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop entrypoints without executing private sources, a private source adapter guidance operation that joins capability, outcome, and intake-bridge records through the transport-neutral envelope and local MCP scaffold without executing source reads, checked private source-kind selection examples that bind source guidance, first-action records, and adapter-chain runbook guidance without executing the selected path, a private source-kind selection adapter operation that returns those examples through the transport-neutral envelope and local MCP scaffold without running the selected path, source manifest and field mapping intake reports for accepted, partial, needs-confirmation, and rejected data, setup benchmark gates that separate stronger-method execution from quality claims, setup-aware method decisions that select a benchmark-gated deterministic method or fall back/block before artifacts are created, setup-aware deterministic and baseline forecast execution for accepted and accepted-partial intake, append-only recalculation history fixtures, no-API historical baseline forecasts, read-only forecast cards, evidence traces, and bundles, a local forecast-run summary, intake matrix, and runbook for agents, transport-neutral agent envelope examples, a local `agent-call` dispatcher, a local MCP stdio scaffold for the same sixteen adapter operations plus the forecast-run tool, a checked protocol map for MCP plus future HTTP and queue adapters, a release manifest with a local MVP runtime section and smoke checks, and a CI release gate.

OPE now also has a checked source adapter output contract and intake gate for the core connector vision: external agent-built connectors can live outside OPE core if they emit a sanitized OPE source manifest, field mapping, provenance summary, and handoff boundary before source intake. The intake gate validates adapter-provided manifests, mappings, provenance, freshness, source roles, and leakage boundaries; accepted outputs continue to method gates, while needs-confirmation, insufficient-data, rejected, and unsafe outputs get explicit next actions. A checked source-quality readback joins builder, adapter-intake, source-intake, and method-decision records so agents can see whether to proceed, confirm mappings, collect more data, replace a source, or stop unsafe connector output without executing source reads or creating artifacts. This keeps connectors flexible while keeping connector execution, credentials, forecast semantics, method gates, resolution, scoring, and quality claims inside OPE boundaries. As the first concrete beta connector, OPE has an opt-in HSL GTFS-RT TripUpdates capture, minimal decoder, and static GTFS schedule join that writes local transit delay CSV rows and source-adapter output while keeping normal checks offline. The transit wedge also has a checked forward-run workflow that records the pre-window forecast, preserves run state, accepts or captures outcome rows later, resolves the threshold event, scores against the baseline, and keeps quality/calibration claims blocked. A checked corpus growth loop classifies append-ready resolved runs, exclusion-ledger rows, due-run and post-resolution checklist status, and threshold progress without mutating the canonical corpus during normal checks. A checked baseline track-record gate reports current Brier, baseline, lift, sample-size, and horizon/window coverage while refusing calibration summaries below threshold. Checked transit method options keep baseline-only execution as the default, record the transparent weather-adjustment method as evidence-only, and keep historical-conditioned, trained ML, retrieval-assisted, ensemble, and external-reference methods proposed-only. A checked live evidence promotion gate binds an approved local live weather draft to a sanitized forecast-time source set while keeping post-close and resolution-only captures out of forecast provenance. A checked prediction campaign manifest now expands the repeating setup into unique dry-run campaign, cycle, run, question, forecast, resolution, and scoring IDs with duplicate keys and status readbacks, while keeping normal checks from writing live state or creating forecast artifacts. A checked prediction campaign runner readback now exposes `prediction-campaign start` command semantics, recurrence flags, dry-run run decisions, JSONL output expectations, and the local non-execution boundary before effectful forecast creation exists. A checked prediction campaign forecast-creation handoff now binds the ready runner decision to planned forecast artifact IDs and pre-creation checks without creating artifacts, fetching live data, or writing campaign state. A checked prediction campaign forecast artifact now materializes `forecast-1301` as an unresolved baseline-only fixture using the existing question, evidence, artifact, and history contracts, while leaving live fetches, `.ope/live` writes, resolver execution, scoring, corpus append, and quality claims out of normal checks. A checked prediction campaign forecast-write plan now binds those lifecycle records to ignored `.ope/live` target paths and guard checks without executing local writes during normal checks. A checked prediction campaign resume readback now joins the campaign manifest, write plan, open forecast, and resolution queue into safe recovery actions without reading or writing ignored live state. A checked resolution job registry gives agents read-only next-action guidance over pending runs, a foreground terminal scheduler lets agents poll and optionally execute due jobs on their own machine, and a checked local resolver-agent command can explicitly execute due resolver commands.

The repository does not yet implement arbitrary manual upload, private API, or database parsing beyond checked setup fixtures, the approved local-folder runtime, and capability declarations, generated language-specific runtime types, additional setup-aware methods beyond the current deterministic fixture path, source-quality-driven source execution or artifact creation, canonical corpus mutation from the checked transit corpus growth loop, forecast execution from ignored local live drafts outside the explicit transit forward-run workflow, general source-builder forecast execution beyond the checked source-handoff fixture path, production forecast use of live connector results, hosted polling or hosted scheduling of transit captures or resolver execution, repeated live transit calibration runs, live auto-evidence gathering, unrestricted live evidence gathering, a hosted service, an HTTP API, production agent adapter runtime, production source discovery, OS scheduler installation, or live calibration claims. The expansion-readiness gate keeps those areas blocked or deferred until real pilot sessions, corpus growth, and adoption evidence justify a specific next runtime investment.

## Reference Wedge

The first reference wedge remains `weather-logistics`: short-horizon probability of declared weather-linked last-mile logistics disruption.

This wedge is useful because it can start with public weather data, declared source policies, simple baselines, frequent outcomes, and relatively low risk. It also exposes a hard product truth: evidence may be enough to estimate risk, but declared outcome or proxy sources are still needed for fair resolution.

The product vision remains domain-agnostic. Weather-logistics is the reference implementation used to prove the OPE standard, not the identity or limit of the product. A seaport berth-availability setup, demand-risk setup, field-operations setup, or other private engine should follow the same OPE-standard loop: domain setup, source connection, method selection, forecast artifacts, recalculation history, resolution, scoring, and calibration.

## Public Beta Candidate

The selected public beta candidate wedge is `weather-transit-delays`: short-horizon probability that a declared public transport network exceeds a delay threshold during a declared service window, using forecast-time weather and transit evidence.

This is not a quality claim yet. OPE now has a local custom-file prototype for this wedge: `python3 scripts/ope.py transit-delay-forecast` reads approved CSV/JSON weather, historical delay, and optional trip-update outcome files, then emits schema-bound forecast, resolution, and scoring records. OPE also has `python3 scripts/ope.py transit-api-connector`, which captures HSL GTFS-RT TripUpdates only when explicitly run with `--live` and can derive local delay rows with `--schedule-join`. The connector-backed forward-run surface is now available through `python3 scripts/ope.py transit-delay-forward-run`: fixture mode runs forecast, resolution, and scoring end to end, while explicit local live phases can save a pre-window forecast and later resolve it from HSL TripUpdates. `python3 scripts/ope.py transit-forward-run-corpus` reports the checked corpus count, one comparable scored run, six exclusion examples, and sample-size claim boundary. `python3 scripts/ope.py transit-corpus-growth` reports append-ready comparable candidates, exclusion-ledger rows, due-run and post-resolution checklists, and progress toward 30-run track-record and 100-run calibration thresholds. `python3 scripts/ope.py transit-track-record-gate` reports the current below-threshold Brier, baseline score, lift, sample sizes, and horizon/window coverage while keeping calibration summaries withheld. `python3 scripts/ope.py transit-method-options` explains why baseline-only execution remains the default and why the weather-adjustment candidate is evidence-only below threshold. `python3 scripts/ope.py transit-live-evidence-promotion` records the gate for turning an approved ignored live weather draft into a sanitized forecast-time source set, while rejecting post-close and resolution-only captures as forecast evidence. `python3 scripts/ope.py resolution-jobs` gives agents the safe read-only job queue, and `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001` adds the checked campaign forecast wait state without executing campaign resolvers. `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001` adds that campaign wait action to the checked scheduler tick, while `python3 scripts/ope.py resolution-scheduler --live --watch` gives agents a local foreground polling loop. `python3 scripts/ope.py resolve-due-forward-runs` provides the explicit execution path for due saved runs, and `python3 scripts/ope.py resolution-runtime-reliability` records the checked failure taxonomy, retry guidance, provenance ledger, and live-capture boundary. The remaining public beta work is repeated comparable live windows and enough resolved outcomes to make any calibration claim. Hosted scheduling can remain optional later rather than a beta prerequisite.

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
