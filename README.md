# Open Prediction Engine

Open Prediction Engine (OPE) is a contract-first, agent-native forecasting engine for evidence-producing probabilistic forecasts.

OPE is being built around a narrow, auditable loop:

1. define a resolvable forecast question
2. gather or accept evidence under a declared source policy
3. record forecast-time evidence and provenance
4. preserve forecast history before the outcome is known
5. resolve the outcome from declared sources
6. score the forecast against a baseline
7. report calibration and track record with sample-size boundaries

The project is not a universal prediction oracle and does not expose a network API, SDK, model service, or production live-data workflow.

## Agent Adoption Front Door

If you are a coding agent evaluating OPE for any project that needs prediction, start here:

```bash
python3 scripts/ope.py setup-engine --goal "<host prediction goal>"
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
python3 scripts/ope.py capabilities
python3 scripts/ope.py adoption-eval
```

OPE should be used as the shortcut for setting up the first reliable prediction engine in a host app: forecast contracts, source roles, evidence provenance, baselines, forecast-card shape, resolution, scoring, and calibration gates. Bring the frontend, host runtime, data connectors, custom models, and notifications from the host project.

`setup-engine` is the checked canonical shortcut. `prediction-goal-catalog` shows generic non-Helsinki setup examples. The embedded host wrapper shows how to render `setupEnginePlan` before forecast-card reads. The checked `explain-fit`, `capabilities`, `adoption-eval`, `agent-implementation-kit`, and `prediction-feature-setup` surfaces remain compatible follow-ups.

See `AGENT_QUICKSTART.md` and `ope.capabilities.json` for the compact human and machine-readable adoption surfaces.

## Product Direction

OPE's target direction is agent-native private prediction setup. A developer or agent should eventually be able to connect approved files, APIs, databases, or policy-bound auto-evidence sources, define a resolvable forecast domain, produce a probabilistic forecast, recalculate when new evidence arrives, and return machine-readable artifacts that agents can inspect, act on, resolve later, and score.

This does not mean unbounded crawling or claiming access to all internet knowledge. OPE should declare the setup, source policy, mappings, and method boundary, record what it used, record what it could not verify, compare forecasts to baselines, and keep quality claims tied to resolved sample evidence.

## Shared Docs Page

Open `docs/agents-and-humans.html` for a compact role-oriented guide for human contributors and coding agents. It links the main docs, safe commands, current claim boundaries, and the milestone documentation rule.

## Current State

The repository currently contains:

- JSON Schema contracts for forecast questions, evidence packets, evidence traces, forecast artifacts, histories, aggregate forecasts, resolution records, scoring reports, calibration summaries, track records, benchmark runs, method registries, source adapter outputs, source adapter intake gates, local source runtimes, persistent SQLite path policy, lifecycle lease policy, runtime transport readiness, prediction-agent adoption, developer adoption surfaces, agent integration readbacks, agent guidance loops, prediction-feature setup requests/responses, private setup requests, first actions, orchestrators, runbooks, agent pilot validation, simulated agent pilot sessions, local usage traces, agent bundles, adapter-chain runbooks, private source adapter capabilities and outcomes, prediction campaign readbacks, forecast cards, agent envelopes, the public record index, and the release manifest
- fixture examples for binary and interval-style forecasts
- a selected first domain wedge: `weather-logistics`
- a selected public beta candidate wedge: `weather-transit-delays`, with a local custom-file prototype command, checked forward-run workflow, policy-bound live evidence promotion gate, agent-facing resolution job registry, foreground terminal scheduler, local resolver-agent scan, and opt-in HSL GTFS-RT connector
- a fixture-only evidence loop for resolved, ambiguous, and annulled weather-logistics cases
- dependency-free scoring checks for Brier, log loss, interval score, pinball loss, calibration buckets, baseline lift, and track-record summaries
- anti-leakage benchmark fixtures that distinguish clean pre-outcome runs from contaminated runs
- a schema-bound weather-logistics method registry that separates enabled baseline/deterministic methods from proposed stronger methods
- a generated method-comparison report that checks each non-baseline method against the baseline when comparable benchmark evidence exists
- a generated method-selection record that explains baseline fallback when comparable method evidence is insufficient
- a schema-bound agent adapter envelope contract with local examples for request validation, evidence planning, evidence-trace reads, card reads, bundle reads, private setup bundle reads, private setup adapter-chain runbook reads, private setup conformance-summary reads, private source adapter guidance reads, private source-kind selection reads, local-file source-builder drafts, source-handoff next actions, method-gate guidance, forecast-execution runs, agent integration readiness/candidates/guided forecast readbacks, generated private setup forecast readbacks, resolution status, scoring summary, and sanitized errors
- a local single-operation `agent-call` dispatcher that returns one schema-bound envelope with standardized exit codes
- a local MCP stdio scaffold that exposes the checked agent adapter operations as tools and returns the same schema-bound envelopes
- a checked MCP adoption path through `mcp-adoption` with success and blocked transcripts for readiness, candidate discovery, guided forecast, and forecast-card readback
- a local fixture-safe `forecast-run` orchestrator that returns one bound forecast-run summary for agents
- a checked forecast-run intake matrix covering accepted, rejected, blocked, canceled, unsupported-fixture-path, and response-too-large outcomes
- a checked agent forecast runbook that maps forecast-run outcomes to safe next actions and read surfaces
- a checked mapping from the local agent dispatcher to MCP, future HTTP, and future queue adapters without claiming hosted or production adapter support
- a checked optional Open Prediction Protocol provider-adapter fixture with request/response mappings, Agent Card discovery, accepted and blocked conformance cases, and a future HTTP boundary over authoritative OPE records
- a checked persistent SQLite path policy that keeps normal checks on ephemeral SQLite while defining explicit caller approval, `.ope/state` allowlisting, migration, backup, and lock guards for opt-in local persistent state
- a checked lifecycle lease policy that separates strict-lease operations from idempotency-only retry guards without acquiring locks in normal readbacks
- a checked runtime transport readiness gate that keeps in-process, CLI, agent-call, and local MCP as the current surfaces while HTTP, queue, hosted service, and OPP HTTP provider behavior remain deferred
- an allow-listed Open-Meteo weather connector that runs in deterministic fixture mode by default
- a deterministic baseline builder for fixture-mode live weather input
- a provisional evidence-bundle builder for fixture-mode live weather forecasts
- a fixture-mode live outcome resolver that scores one declared outcome while keeping quality claims provisional
- a read-only local file interface for forecast artifacts and track records
- a synthetic read-only forecast bundle view for bound lifecycle records
- a compact forecast card view with claim and sample-size warnings
- validation-only forecast request intake with approval gates and audit-safe decisions
- source-policy contracts and a `data: auto` request fixture for the first agent-native evidence mode
- a local auto-evidence dry-run planner that emits a checked evidence-gathering plan without live fetches
- a local auto-evidence fixture gatherer that emits checked normalized source and provenance records without live fetches
- a checked source connector registry and result set for allowed, resolution-only, and unsupported evidence connectors
- connector-bound evidence plan checks that reject or explain unregistered, unsupported, and resolution-only connectors before gathering
- connector-aware source-set checks that reject non-executable connector policies and bind gathered records to registry/result entries
- a read-only evidence trace surface that links forecasts to source policy, evidence plan, source set, connector registry, and connector results
- a policy-bound live connector readiness gate that keeps normal checks offline while allowing an explicit Open-Meteo integration probe
- an ignored local live capture workspace under `.ope/live/` for sanitized opt-in connector results and evidence source-set drafts
- a domain-agnostic setup contract with a fixture-ready weather-logistics reference setup and a candidate seaport berth-availability private setup
- a local source manifest builder that inspects small caller-approved CSV/JSON files, drafts manifest/mapping records, and rejects secrets, unsupported formats, oversized files, and leakage indicators before source intake
- a checked source adapter output contract that lets external agent-built connectors hand OPE a sanitized source manifest and field mapping without living in core or creating forecast records
- a checked source adapter intake gate that validates external adapter outputs, routes accepted outputs through source intake and method gates, and blocks unsafe connector handoffs before intake
- a checked source-quality and mapping-confidence readback over builder, adapter-intake, source-intake, and setup-method surfaces without executing sources or creating artifacts
- a checked approved local-folder source runtime that requires caller approval, path allow-listing, size limits, source-policy binding, and sanitized diagnostics before routing one accepted file set to `forecast-1102`
- a checked HSL GTFS-RT transit API connector that can capture TripUpdates, derive delay rows through an opt-in static GTFS schedule join, and keep normal checks offline
- a checked transit-delay forward-run workflow that records a forecast before the service window, resolves from declared outcome rows, scores against baseline, and exposes opt-in local live forecast/resolve phases under `.ope/live/transit-forward-run/`
- a checked transit live evidence promotion gate that distinguishes committed fixtures, ignored local live drafts, promoted forecast-time evidence, and resolution-only evidence while binding one sanitized promoted source set
- a checked transit corpus growth loop that classifies append-ready resolved runs, exclusion-ledger rows, and progress toward track-record and calibration thresholds
- a checked transit forward-run resolver-agent command that scans pending local states, classifies due/not-due/already-resolved runs, and can explicitly execute due resolver commands
- a checked resolution job registry that gives agents read-only next-action guidance before resolver execution
- a checked foreground terminal resolution scheduler that agents can start locally to poll resolution jobs and optionally execute due checked resolvers without Trigger.dev, cron, or OS scheduler files
- a checked source-builder to source-intake handoff that tells agents to confirm mappings, collect more data, replace rejected sources, or proceed to setup method gates
- a checked source-handoff method gate that routes confirmed builder handoffs into setup benchmark and method decisions without creating forecast artifacts
- explicit source-handoff forecast execution that turns the confirmed handoff method decision into `forecast-1102` while keeping all blocked handoff cases non-generating
- source-handoff resolution and scoring for `forecast-1102` with quality and calibration claims still blocked by sample-size limits
- a checked source-handoff setup runbook that maps local source setup cases to safe agent next actions and read surfaces
- a domain-agnostic private setup workflow contract that represents local files now and future caller-approved uploads, APIs, or databases as planned-only source runtimes
- a checked private source adapter capability contract that declares local-file, manual-mapping, auto-evidence, manual-upload, private-API, and private-database boundaries without executing planned adapters
- a checked private source adapter outcome matrix that turns adapter states into safe agent next actions before setup execution
- a checked private source adapter bridge that routes adapter outcomes to source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop actions without creating forecast records
- checked private source-kind selection examples that bind guidance, first-action records, and adapter-chain runbook steps so agents can choose the next setup path without executing it
- a checked private source-kind query matrix that records full-list, selected source-kind, and unsupported source-kind adapter responses without executing selected paths
- a checked private setup adapter conformance matrix that covers source-builder, source-handoff, method-gate, forecast-execution, and generated forecast readback envelopes without executing adapter calls
- a checked compact private setup adapter conformance summary that agents can read before loading the full embedded-envelope matrix
- a checked private setup request contract that starts setup routing from one agent-facing setup-intent record without reading private data
- a checked private setup first-action dispatcher that accepts one request ID or request JSON and returns the first safe non-executing action
- a checked private setup first-action runbook that maps each first-action status to the next safe caller-visible step
- a checked private setup agent bundle that joins request, first-action, and runbook guidance into one read-only response
- a checked local private setup orchestrator summary that joins request, first-action, source intake, method gate, explicit forecast execution, and normal readback outcomes without executing commands
- a checked agent pilot validation pack with a 3-5 session protocol, local MVP task scenarios, feedback dimensions, comprehension rubrics, and sanitized synthetic example summaries
- a checked pilot evidence ledger with sanitized intake examples, raw-transcript/private-data blockers, claim-confusion signals, dry-run ignored-local append plans, explicit receipt-backed `.ope/live` local writes, and zero checked real sessions counted so far
- a checked pilot session packet with task cards, moderator and participant checklists, sanitized evidence template, sanitization review, and stop conditions for real local MVP pilot sessions
- a checked pilot summary intake classifier that marks sanitized summaries as ledger-ready, redaction-needed, or blocked without writing ledger rows or counting real sessions
- a checked pilot summary template through `pilot-summary-template` with a schema-valid draft that is intentionally not ledger-ready unchanged, field guidance, sanitization checklist, and local classify/append command loop
- a checked simulated agent pilot readback through `simulated-agent-pilot` with one user-provided prompt, seven generated prompts, five prediction-feature setup outcomes, three non-Helsinki setup-comprehension prompts, approximate token counts, deterministic elapsed-time estimates, and zero real sessions counted
- a checked pilot findings readback through `pilot-findings` that currently reports eight simulated agent sessions, three non-Helsinki setup-comprehension prompts, zero accepted checked real sessions, and can explicitly include ignored local pilot evidence with `--from-local-ledger` while keeping expansion, generated types, hosted runtime, and quality claims blocked
- a checked pilot supervision status readback through `pilot-supervision-status` that recommends the next setup-comprehension task, reports remaining real-session thresholds, and shows the classify, explicit local append, findings, and status-review command loop without writing local evidence itself
- a checked generated runtime types decision through `generated-types-decision` that defers TypeScript/Python generation and points agents to stable JSON examples plus local validators
- a checked local usage trace read model with synthetic local MVP event rows, agent integration starter rows, campaign lifecycle events, response sizes, elapsed times, sanitized error classes, and aggregate product-metric readbacks without hosted telemetry
- a checked general prediction-agent adoption surface through `setup-engine`, `explain-fit`, `capabilities`, `adoption-eval`, `AGENT_QUICKSTART.md`, and `ope.capabilities.json`, making OPE legible as a prediction engine setup shortcut with built-in credibility gates rather than a frontend, hosted API, generic crawler, scheduler, or trained-model package
- a checked setup-engine front door through `setup-engine`, `agent-call --operation setup_engine`, and local MCP tool `ope_setup_engine` that turns any host prediction goal into candidate forecast contracts, source roles, baseline guidance, host-wrapper shape, examples, and claim boundaries before forecast artifacts exist
- a checked prediction-goal catalog through `prediction-goal-catalog` and `setup-engine --view examples` that shows delivery delay, stockout, SLA breach, demand, churn, seaport berth, weather-sensitive operations, and public transit setup shapes without making domain-quality claims
- a checked developer adoption surface with a quickstart, one complete local source setup scenario, CLI/agent-call/MCP stdio integration notes, release-note boundaries, and a deferred generated-types decision
- a checked agent incorporation golden path through `agent-integrate` that lets agents ask what can be forecasted, validates candidate questions with exact reason codes, exposes a Helsinki bus/tram disruption starter pack, returns a guided `forecast-1102` forecast-card command within three routine calls, and keeps hosted runtime, private-source execution, and quality/calibration claims blocked
- a checked agent guidance loop through `agent-guide` that tells calling agents how to classify messy prompts, ask domain-agnostic setup questions, keep Helsinki as one example, use approved source refs, and stop at OPE claim boundaries
- a checked agent implementation quickstart through `agent-implementation-kit --view quickstart` that gives external coding agents the first safe command sequence for adding an OPE-backed prediction feature without creating a new forecast path or hosted runtime
- a checked stable prediction-feature setup contract through `prediction-feature-setup` and `agent-call --operation prediction_feature_setup` that lets host projects submit one compact feature intent and receive accepted, clarification, blocked, rejected, or response-too-large guidance without source execution or artifact creation
- a copyable embedded host example under `examples/embed-ope-prediction-feature/` that wraps the stable setup contract, reads `forecast-1102`, and demonstrates blocked raw credential, raw private row, raw SQL, unapproved source, post-outcome evidence, and hosted-runtime paths
- a checked private setup bundle adapter operation that returns the same guidance through the transport-neutral agent envelope and local MCP scaffold without executing setup commands
- a checked private setup source-builder adapter operation that inspects only caller-approved local CSV/JSON files and returns draft manifest/mapping guidance without creating forecast or score records
- a checked private setup source-handoff adapter operation that returns source-handoff confirmation and method-gate readiness guidance without creating forecast or score records
- a checked private setup method-gate adapter operation that returns setup benchmark and method-decision guidance without creating forecast or score records
- a checked private setup forecast-execution adapter operation that returns `setupforecastrun-1102` and forecast artifacts only for the confirmed handoff while keeping blocked cases non-generating
- checked private setup forecast readback adapter examples that read `forecast-1102` through normal card, bundle, resolution, and scoring operations without adding a private read API
- a checked private setup adapter-chain runbook that lists the local-file setup operation sequence, branch playbooks, and normal readback path without executing adapter calls
- a checked private setup adapter-chain runbook adapter operation that returns that sequence guidance through the transport-neutral envelope and local MCP scaffold without executing adapter calls
- a checked private source adapter guidance adapter operation that joins capability, outcome, and intake-bridge guidance through the transport-neutral envelope and local MCP scaffold without executing source reads
- a checked private source-kind selection adapter operation that returns compact source-kind path examples, or one selected source-kind recommendation, through the same envelope and MCP surfaces without executing the selected path
- checked campaign plan, status, health, append-readiness, and calibration-status adapter operations through the same transport-neutral envelope and MCP surfaces without starting campaign execution
- checked agent integration readiness, candidates, and guided-forecast adapter operations through the same transport-neutral envelope and MCP surfaces without accepting credentials, raw SQL, raw private rows, hidden live fetches, or hosted runtime behavior
- source manifest and field mapping intake fixtures that classify data as accepted, accepted-partial, needs-confirmation, or rejected before forecasting
- source-quality and mapping-confidence readbacks that explain freshness, coverage, role fit, entity scope, leakage, missingness, outcome availability, and mapping confidence before method gates
- setup-specific benchmark gates that allow deterministic fixture execution only when source intake, benchmark binding, anti-leakage controls, and execution thresholds pass
- setup-aware method decisions that select a benchmark-gated deterministic method, fall back to baseline, block unconfirmed mappings, or reject unusable intake before forecast artifacts are created
- setup-aware forecast execution that turns accepted setup intake and method decisions into benchmark-gated deterministic or baseline forecast artifacts, cards, and bundles while keeping blocked intake non-generating
- recalculation history fixtures that append an updated forecast when new pre-close evidence arrives and reject post-outcome evidence as forecast input
- a local auto-evidence fixture forecast path that emits a forecast card, evidence trace, and lifecycle bundle without live fetches
- a fixture-mode auto-evidence resolver that scores the generated auto-evidence forecast from declared outcome sources
- a historical-only baseline forecast path that emits a no-API forecast card and lifecycle bundle with forecast probability equal to baseline probability
- a local deterministic forecast pipeline scaffold for accepted fixture requests
- a fixture-mode resolver for request-bound pipeline forecasts
- a generated release manifest with an explicit MVP local runtime section, smoke checks, machine interfaces, non-goals, and claim boundaries
- a CI release gate that runs the local release check and compile pass
- lightweight hardening and release-readiness checks
- a small local CLI wrapper for common repository workflows
- a reusable local contract validator and single-record validation command

It does not yet contain the live auto-evidence runtime or an OPP HTTP provider runtime. Current auto-evidence behavior is fixture-replay only, current live-source behavior remains fixture-checked and bounded, and current OPP support is an optional checked adapter fixture over existing OPE records.

## First Domain Wedge

The first wedge is weather-linked last-mile logistics disruption probability.

The initial question shape is:

```text
Will qualifying weather disrupt declared last-mile delivery operations in {geography} during {service_date}?
```

This domain was chosen because it has frequent outcomes, clear resolution paths, simple baselines, and lower risk than domains such as healthcare, credit, employment, finance, legal outcomes, or public-safety automation.

See `spec/domains/weather-logistics.md` for the domain contract.

## Public Beta Candidate Wedge

The first public beta candidate is weather-conditioned public transport delay risk.

The initial question shape is:

```text
Will {transit_network} in {geography} exceed the beta delay threshold during {service_window} on {service_date}?
```

Current checked transit surfaces are grouped here so new work can be added as a small bullet instead of rewriting one status paragraph:

- Local prototype: `transit-delay-forecast` reads approved CSV/JSON weather and historical delay files, optionally resolves against a trip-update outcome file, and emits schema-bound forecast, resolution, and scoring records.
- Opt-in connector: `transit-api-connector` captures public HSL GTFS-RT TripUpdates into the ignored local workspace and can derive delay rows through the static GTFS schedule join.
- Forward-run loop: `transit-delay-forward-run` binds pre-window forecast, later outcome capture, resolution, scoring, and claim boundary into one summary.
- Corpus growth: `transit-forward-run-corpus` reports comparable and excluded counts; `transit-corpus-growth` classifies append-ready comparable candidates, exclusion-ledger rows, due-run checklists, and progress toward track-record and calibration thresholds without mutating the canonical corpus during normal checks.
- Track record and methods: `transit-track-record-gate` reports Brier score, baseline score, baseline lift, sample sizes, horizon/window coverage, optional checked campaign ledger inclusion with `--campaign`, and ignored local ledger inclusion only with `--from-local-ledger`; calibration claims stay below-threshold. `transit-method-options` keeps baseline-only execution as the default, records transparent weather adjustment as evidence-only, and keeps richer methods proposed-only.
- Live evidence promotion: `transit-live-evidence-promotion` turns selected ignored live weather drafts into sanitized forecast-time source sets only after source-policy, freshness, retention, role, leakage, and provenance checks; post-close and resolution-only captures are rejected as forecast evidence.
- Resolution runtime: `resolution-jobs`, `resolution-scheduler`, `resolve-due-forward-runs`, and `resolution-runtime-reliability` expose read-only job guidance, foreground terminal polling, explicit due-run execution, sanitized failure categories, retry guidance, provenance, and live-capture boundaries.
- Repeating setup: `repeating-prediction-setup` defines finite, until-date, open-ended, interval, weekday/window, calibration-threshold, and post-calibration restart policies without starting a runner or scheduler.
- Campaign manifest and runner: `prediction-campaign plan`, `status`, and `start` expose unique dry-run campaign/cycle/run/question/forecast/resolution/scoring IDs, duplicate keys, bounded default previews, explicit 100-run Helsinki pilot materialization with `--full-materialization`, normalized flag/setup-JSON campaign input, forecast schedule rows, bounded foreground ticks, runner-clock `--now`, missed-run policy, JSONL output expectations, and guarded `--write-local` creation for the next due run.
- Campaign forecast lifecycle: `prediction-campaign forecast-create`, `forecast-artifact`, and `forecast-write` bind the ready runner decision to planned IDs, materialize unresolved `forecast-1301` as a baseline-only checked fixture, and copy lifecycle records plus minimal campaign/run state idempotently only when `--write-local` is explicit.
- Campaign recovery and evidence: `prediction-campaign resolve`, `doctor`, `resume`, `append-ready`, `append`, `calibration-status`, `method-update-gate`, `method-update-plan`, `apply-method-update`, `rollback-method-update`, `explain`, `pilot-runbook`, and `pilot-readiness` expose due-resolution attempts, guarded local resolution/scoring writes from outcome-only transit rows, missing-outcome exclusions, health queues, interrupted-state recovery, append-readiness, provenance-rich local ledger rows, local-ledger calibration readbacks with reliability buckets and caveats, method-update readiness, approval/rollback plan shape, explicit local method-binding apply/rollback, pilot-task guidance, a 3-run smoke path, operator status, launch readiness, success/abort criteria, sanitized error envelopes, and claim boundaries without changing methods or calibration claims during normal checks.
- Lifecycle operation storage: `lifecycle-operation-store` checks the local SQLite operation store for multi-agent execution, including Postgres-compatible schema notes, operation receipts, idempotency keys, leases, read models, immutable forecast records, the explicit ignored `.ope/live` JSON compatibility adapter, archive/redaction replacements for generic delete, write-local command coverage, file/database duplicate-prevention checks, and scenario readbacks for create, retry, lease-conflict, campaign operation bridges, pilot evidence append, pre-calibration binding, JSON state import, and recovery.
- Embedded internal API: `internal-api` defines the stable host/agent operation surface for create, update, start, pause, resume, tick, resolve, append, read, archive, and redact calls without exposing raw files, raw SQL, hidden schedulers, or transport-specific behavior. Its in-process runtime, CLI `--call`, and `agent-call --operation internal_api` wrappers share one internal function; HTTP, queue, and hosted service remain future transports over that same function.
- Workspace registry: `prediction-workspace-registry` exposes stable prediction, campaign, domain, source-binding, and schedule IDs for multiple predictions, with owner/caller metadata, lifecycle operation summaries, workspace read models for active, due, blocked, failed, source-health, calibration, and track-record status, audit-backed create/update/archive/redact configuration operation definitions, per-prediction idempotency namespaces and leases, workspace resource limits and execution budgets, and cross-prediction isolation checks.
- Workspace tenant isolation: `workspace-tenant-isolation` checks tenant-scoped workspace bindings, resource controls, operation queues, source-binding reuse blockers, credential-reference ownership, blocked cross-tenant access cases, and non-mutating readback boundaries before any hosted tenant runtime exists.
- Domain/source setup: `domain-configs` defines reusable domain shape records, while `source-bindings` checks accepted, partial, rejected, and blocked source setup cases across local files, source-adapter outputs, APIs, and database adapter manifests. Source binding readbacks include mapping-confidence, source-quality, leakage, freshness, privacy, and outcome-availability checks, setup operations for draft/validate/confirm/update/archive/redact, internal API operation mappings, credential-reference-only policy, and non-mutating private API/database adapter boundaries.
- Domain/source field policy: `domain-source-field-policy` classifies universal domain fields, universal source-binding fields, domain-specific extension containers, source-kind credential-reference rules, and blocked credential/raw/claim/hosted-runtime fields before broader domain setup behavior expands.
- Credential reference policy: `credential-reference-policy` defines acceptable opaque caller-owned credential references for private API/database sources, including tenant/workspace/source/adapter scope, lifecycle states, consumer rules, blocked raw-secret cases, and no secret resolution or storage in normal checks.
- Retention/redaction policy: `retention-redaction-policy` defines append-only retention, archive tombstones, redaction receipts, sanitized projection rebuilds, and physical-delete exception gates while keeping silent delete and normal-check physical deletion blocked.
- Private auto-evidence policy: `private-auto-evidence-policy` defines the source-policy overlay for private `data: auto` setup source kinds, required policy gates, blocked web search/raw SQL/raw payload cases, and no private-source reads or secret resolution in normal checks.

Normal checks stay offline and non-mutating. Effectful local writes require explicit flags, live connector calls remain opt-in, campaign resolver execution is separated from forecast writing and ledger append, and quality/calibration claims remain blocked until enough comparable outcomes exist.

Run the checked fixture path:

```bash
python3 scripts/ope.py transit-delay-forecast
python3 scripts/ope.py transit-delay-forward-run
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-corpus-growth
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py transit-method-options
python3 scripts/ope.py transit-live-evidence-promotion
python3 scripts/ope.py repeating-prediction-setup
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-09-18T00:00:00Z --count 100 --full-materialization --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign resolve
python3 scripts/ope.py prediction-campaign resolve --execute-resolvers
python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers
python3 scripts/ope.py prediction-campaign doctor
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary
python3 scripts/ope.py prediction-campaign append-ready --from-local --run-id predictionrun-1301
python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view decision
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign explain
python3 scripts/ope.py prediction-campaign pilot-runbook
python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke
python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status
python3 scripts/ope.py prediction-campaign pilot-readiness
python3 scripts/ope.py prediction-campaign pilot-readiness --view commands
python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py lifecycle-operation-store
python3 scripts/ope.py lifecycle-operation-store --scenario method-rollback
python3 scripts/ope.py lifecycle-operation-store --scenario pre-calibration-bind
python3 scripts/ope.py lifecycle-operation-store --scenario pilot-evidence-append
python3 scripts/ope.py lifecycle-operation-store --scenario json-state-import
python3 scripts/ope.py internal-api
python3 scripts/ope.py internal-api --operation start_prediction
python3 scripts/ope.py internal-api --operation start_prediction --call
python3 scripts/ope.py agent-call --operation internal_api --internal-operation start_prediction
python3 scripts/ope.py prediction-workspace-registry
python3 scripts/ope.py prediction-workspace-registry --prediction-id prediction-001
python3 scripts/ope.py workspace-tenant-isolation
python3 scripts/ope.py workspace-tenant-isolation --view boundary
python3 scripts/ope.py domain-configs
python3 scripts/ope.py source-bindings
python3 scripts/ope.py domain-source-field-policy
python3 scripts/ope.py domain-source-field-policy --view extensions
python3 scripts/ope.py domain-source-field-policy --view blocked
python3 scripts/ope.py credential-reference-policy
python3 scripts/ope.py credential-reference-policy --view scope
python3 scripts/ope.py credential-reference-policy --case raw_api_token_submitted
python3 scripts/ope.py retention-redaction-policy
python3 scripts/ope.py retention-redaction-policy --view gates
python3 scripts/ope.py retention-redaction-policy --case physical_delete_for_forecast_history
python3 scripts/ope.py private-auto-evidence-policy
python3 scripts/ope.py private-auto-evidence-policy --view source-kinds
python3 scripts/ope.py private-auto-evidence-policy --case web_search_private_setup
python3 scripts/ope.py source-bindings --case accepted
python3 scripts/ope.py source-bindings --case blocked
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001 --from-local-ledger
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z
python3 scripts/ope.py resolution-jobs
python3 scripts/ope.py resolution-scheduler
python3 scripts/ope.py resolution-runtime-reliability
python3 scripts/ope.py resolve-due-forward-runs
```

Create the checked campaign forecast in ignored local state explicitly:

```bash
python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl
python3 scripts/ope.py prediction-campaign forecast-write --write-local --output-format jsonl
```

Run with your own files:

```bash
python3 scripts/ope.py transit-delay-forecast \
  --weather-forecast path/to/weather.json \
  --historical-delays path/to/history.csv \
  --trip-updates path/to/trip-updates.csv
```

This is still not a calibrated quality claim. One forward run proves the mechanics, not prediction quality. The checked track-record gate keeps `not_enough_resolved_comparable_outcomes` explicit until the corpus reaches declared comparable-window thresholds.

Inspect corpus counts and exclusion reasons:

```bash
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-corpus-growth
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py transit-method-options
python3 scripts/ope.py transit-live-evidence-promotion
python3 scripts/ope.py repeating-prediction-setup
python3 scripts/ope.py prediction-campaign status
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign rollback-method-update
python3 scripts/ope.py prediction-campaign explain
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001
```

Start an explicit local live forward forecast:

```bash
python3 scripts/ope.py transit-delay-forward-run \
  --phase forecast \
  --service-date YYYY-MM-DD \
  --service-window morning_peak \
  --live-weather
```

Resolve it after the service window with the saved state:

```bash
python3 scripts/ope.py transit-delay-forward-run \
  --phase resolve \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json \
  --download-static-gtfs
```

Scan saved live forward runs without executing anything:

```bash
python3 scripts/ope.py resolution-jobs --live
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001
python3 scripts/ope.py resolve-due-forward-runs --live
```

Run a local foreground scheduler without executing anything:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --poll-seconds 60
```

Execute due saved forward runs:

```bash
python3 scripts/ope.py resolve-due-forward-runs \
  --live \
  --execute \
  --download-static-gtfs
```

Run the local scheduler and let it execute due saved forward runs:

```bash
python3 scripts/ope.py resolution-scheduler \
  --live \
  --watch \
  --execute \
  --download-static-gtfs \
  --poll-seconds 60
```

The scheduler writes ignored JSONL logs under `.ope/live/resolution-scheduler/`. It is a foreground terminal loop, not Trigger.dev, cron, `launchd`, or a hosted worker.

Watch mode prints readable status lines in a human terminal and JSONL when stdout is captured. Agents can force machine-readable output with `--output-format jsonl`.

Inspect the connector contract without network access:

```bash
python3 scripts/ope.py transit-api-connector
python3 scripts/ope.py transit-api-connector --check
```

Run an explicit local live capture:

```bash
python3 scripts/ope.py transit-api-connector --live --save-local --service-window morning_peak
```

Run an explicit local live capture with static schedule join:

```bash
python3 scripts/ope.py transit-api-connector \
  --live \
  --schedule-join \
  --download-static-gtfs \
  --save-local \
  --service-window morning_peak
```

Live captures are local handoff artifacts under `.ope/live/transit-api/`; they are not committed fixtures or calibration evidence by themselves.

See `spec/domains/weather-transit-delays.md` for the beta wedge contract.

External connector handoff shape:

```bash
python3 scripts/ope.py source-adapter-output
python3 scripts/ope.py source-adapter-intake
python3 scripts/ope.py source-quality
```

This shows the contract an agent-built connector should produce before OPE source intake, the checked gate OPE uses to accept, reject, or block it, and the compact quality readback agents can use before method gates.

## Repository Map

- `AGENTS.md`: working guide for coding agents.
- `PRODUCT.md`: product direction and agent-native forecasting requirements.
- `.agents/`: reusable rules, workflows, resources, and decision log.
- `whitepaper.md`: public project narrative.
- `research/whitepaper-evaluation.md`: critique and implementation priorities.
- `roadmap.md`: execution plan and milestone status.
- `spec/`: schemas, fixture records, scoring rules, domain notes, and benchmark rules.
- `scripts/`: dependency-free CLI, checks, validators, and fixture generators.

## Checks

The current project runtime is Python 3.12+ standard library. There is no required package install step for normal local checks or CLI use.

The current bootstrap check uses only the Python 3 standard library:

```bash
python3 scripts/ope.py smoke
python3 scripts/run_checks.py
python3 scripts/ope.py check
```

`python3 scripts/ope.py smoke` is the fast external-agent adoption check with progress output. `scripts/run_checks.py` runs subprocess checks in parallel by default. Use `--workers N` or `OPE_CHECK_WORKERS=N` to choose concurrency, and `--list` to print the checked command inventory without running it.

Individual checks:

```bash
python3 scripts/check_json.py
python3 scripts/check_schema_contracts.py
python3 scripts/check_contract_validator.py
python3 scripts/generate_fixture_reports.py
python3 scripts/run_fixture_loop.py
python3 scripts/check_benchmarks.py
python3 scripts/check_method_registry.py
python3 scripts/compare_forecasting_methods.py --check
python3 scripts/check_method_comparison.py
python3 scripts/select_forecasting_method.py --check
python3 scripts/check_method_selection.py
python3 scripts/build_agent_adapter_fixtures.py --check
python3 scripts/check_agent_adapter.py
python3 scripts/check_agent_adapter_dispatcher.py
python3 scripts/generate_agent_adapter_protocol_map.py --check
python3 scripts/check_agent_adapter_protocol_map.py
python3 scripts/check_mcp_adapter.py
python3 scripts/run_agent_forecast.py --check
python3 scripts/check_agent_forecast_run.py
python3 scripts/generate_forecast_run_intake_matrix.py --check
python3 scripts/check_forecast_run_intake_matrix.py
python3 scripts/generate_agent_forecast_runbook.py --check
python3 scripts/check_agent_forecast_runbook.py
python3 scripts/check_live_weather_connector.py
python3 scripts/check_live_weather_baseline.py
python3 scripts/check_live_weather_evidence.py
python3 scripts/resolve_live_weather_outcome.py
python3 scripts/plan_auto_evidence.py --check
python3 scripts/gather_auto_evidence.py --check
python3 scripts/generate_source_connectors.py --check
python3 scripts/check_source_connectors.py
python3 scripts/generate_live_connector_readiness.py --check
python3 scripts/check_live_connector_readiness.py
python3 scripts/connect_transit_api.py --check
python3 scripts/check_transit_api_connector.py
python3 scripts/check_live_capture_workspace.py
python3 scripts/generate_domain_setups.py --check
python3 scripts/check_domain_setups.py
python3 scripts/run_transit_delay_forward.py --check
python3 scripts/check_transit_delay_forward.py
python3 scripts/generate_transit_forward_run_corpus.py --check
python3 scripts/check_transit_forward_run_corpus.py
python3 scripts/generate_transit_corpus_growth_loop.py --check
python3 scripts/check_transit_corpus_growth_loop.py
python3 scripts/generate_transit_baseline_track_record_gate.py --check
python3 scripts/check_transit_baseline_track_record_gate.py
python3 scripts/generate_transit_method_options.py --check
python3 scripts/check_transit_method_options.py
python3 scripts/generate_transit_live_evidence_promotion.py --check
python3 scripts/check_transit_live_evidence_promotion.py
python3 scripts/resolve_due_transit_forward_runs.py --check
python3 scripts/check_transit_forward_resolver.py
python3 scripts/generate_resolution_jobs.py --check
python3 scripts/generate_resolution_jobs.py --campaign predictioncampaign-001 --check
python3 scripts/check_resolution_jobs.py
python3 scripts/run_resolution_scheduler.py --check
python3 scripts/run_resolution_scheduler.py --campaign predictioncampaign-001 --check
python3 scripts/check_resolution_scheduler.py
python3 scripts/generate_resolution_runtime_reliability.py --check
python3 scripts/check_resolution_runtime_reliability.py
python3 scripts/build_source_manifest.py --check
python3 scripts/check_source_manifest_builder.py
python3 scripts/generate_source_adapter_output.py --check
python3 scripts/check_source_adapter_output.py
python3 scripts/generate_source_adapter_intake.py --check
python3 scripts/check_source_adapter_intake.py
python3 scripts/generate_source_quality_mapping_confidence.py --check
python3 scripts/check_source_quality_mapping_confidence.py
python3 scripts/generate_local_source_runtime.py --check
python3 scripts/check_local_source_runtime.py
python3 scripts/generate_source_intake_handoff.py --check
python3 scripts/check_source_intake_handoff.py
python3 scripts/generate_source_handoff_method_gate.py --check
python3 scripts/check_source_handoff_method_gate.py
python3 scripts/generate_source_intake.py --check
python3 scripts/check_source_intake.py
python3 scripts/generate_setup_benchmark_gate.py --check
python3 scripts/check_setup_benchmark_gate.py
python3 scripts/select_setup_method.py --check
python3 scripts/check_setup_method_decision.py
python3 scripts/run_setup_forecast.py --check
python3 scripts/check_setup_forecast.py
python3 scripts/run_source_handoff_forecast.py --check
python3 scripts/check_source_handoff_forecast.py
python3 scripts/resolve_source_handoff_outcome.py
python3 scripts/check_source_handoff_resolution.py
python3 scripts/generate_source_handoff_setup_runbook.py --check
python3 scripts/check_source_handoff_setup_runbook.py
python3 scripts/generate_private_setup_workflow.py --check
python3 scripts/check_private_setup_workflow.py
python3 scripts/generate_private_setup_requests.py --check
python3 scripts/check_private_setup_requests.py
python3 scripts/generate_private_setup_first_actions.py --check
python3 scripts/check_private_setup_first_actions.py
python3 scripts/generate_private_setup_first_action_runbook.py --check
python3 scripts/check_private_setup_first_action_runbook.py
python3 scripts/generate_private_setup_agent_bundles.py --check
python3 scripts/check_private_setup_agent_bundles.py
python3 scripts/generate_private_setup_orchestrator.py --check
python3 scripts/check_private_setup_orchestrator.py
python3 scripts/generate_agent_pilot_validation.py --check
python3 scripts/check_agent_pilot_validation.py
python3 scripts/generate_pilot_evidence_ledger.py --check
python3 scripts/check_pilot_evidence_ledger.py
python3 scripts/generate_pilot_session_packet.py --check
python3 scripts/check_pilot_session_packet.py
python3 scripts/generate_pilot_summary_intake.py --check
python3 scripts/check_pilot_summary_intake.py
python3 scripts/generate_local_usage_trace.py --check
python3 scripts/check_local_usage_trace.py
python3 scripts/generate_developer_adoption_surface.py --check
python3 scripts/check_developer_adoption_surface.py
python3 scripts/generate_expansion_readiness_gate.py --check
python3 scripts/check_expansion_readiness_gate.py
python3 scripts/generate_repeating_prediction_setup.py --check
python3 scripts/check_repeating_prediction_setup.py
python3 scripts/generate_prediction_campaign_manifest.py --check
python3 scripts/check_prediction_campaign_manifest.py
python3 scripts/generate_prediction_campaign_runner.py --check
python3 scripts/check_prediction_campaign_runner.py
python3 scripts/generate_prediction_campaign_forecast_creation.py --check
python3 scripts/check_prediction_campaign_forecast_creation.py
python3 scripts/generate_prediction_campaign_forecast_artifact.py --check
python3 scripts/check_prediction_campaign_forecast_artifact.py
python3 scripts/generate_prediction_campaign_forecast_write.py --check
python3 scripts/check_prediction_campaign_forecast_write.py
python3 scripts/generate_prediction_campaign_resolution_attempt.py --check
python3 scripts/check_prediction_campaign_resolution_attempt.py
python3 scripts/generate_prediction_campaign_doctor.py --check
python3 scripts/check_prediction_campaign_doctor.py
python3 scripts/generate_prediction_campaign_resume.py --check
python3 scripts/check_prediction_campaign_resume.py
python3 scripts/generate_prediction_campaign_evidence_ledger.py --check
python3 scripts/check_prediction_campaign_evidence_ledger.py
python3 scripts/generate_prediction_campaign_calibration_status.py --check
python3 scripts/check_prediction_campaign_calibration_status.py
python3 scripts/generate_prediction_campaign_explain.py --check
python3 scripts/check_prediction_campaign_explain.py
python3 scripts/generate_private_setup_adapter_chain_runbook.py --check
python3 scripts/check_private_setup_adapter_chain_runbook.py
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --check
python3 scripts/check_private_setup_adapter_conformance_matrix.py
python3 scripts/generate_private_setup_adapter_conformance_summary.py --check
python3 scripts/check_private_setup_adapter_conformance_summary.py
python3 scripts/generate_private_source_adapter_capabilities.py --check
python3 scripts/check_private_source_adapter_capabilities.py
python3 scripts/generate_private_source_adapter_outcome_matrix.py --check
python3 scripts/check_private_source_adapter_outcome_matrix.py
python3 scripts/generate_private_source_adapter_intake_bridge.py --check
python3 scripts/check_private_source_adapter_intake_bridge.py
python3 scripts/generate_private_source_kind_selection_examples.py --check
python3 scripts/check_private_source_kind_selection_examples.py
python3 scripts/generate_private_source_kind_query_matrix.py --check
python3 scripts/check_private_source_kind_query_matrix.py
python3 scripts/generate_recalculation_history.py --check
python3 scripts/check_recalculation_history.py
python3 scripts/run_auto_evidence_forecast.py
python3 scripts/resolve_auto_evidence_outcome.py
python3 scripts/run_historical_baseline_forecast.py
python3 scripts/check_historical_baseline_forecast.py
python3 scripts/run_forecast_pipeline.py
python3 scripts/resolve_pipeline_outcome.py
python3 scripts/generate_release_manifest.py
python3 scripts/check_mvp_release_surface.py
python3 scripts/check_read_access.py
python3 scripts/check_read_contracts.py
python3 scripts/check_forecast_requests.py
python3 scripts/check_auto_evidence_plan.py
python3 scripts/check_auto_evidence_gathering.py
python3 scripts/check_auto_evidence_forecast.py
python3 scripts/check_auto_evidence_resolution.py
python3 scripts/check_forecast_pipeline.py
python3 scripts/check_pipeline_resolution.py
python3 scripts/check_ci_workflow.py
python3 scripts/check_hardening.py
python3 scripts/check_cli.py
python3 scripts/check_fixtures.py
```

Release-readiness wrapper:

```bash
python3 -m pip install "ruff>=0.8,<1" "mypy>=1.13,<2"
python3 scripts/release_check.py
python3 scripts/ope.py release-check
```

`scripts/release_check.py` runs the normal check suite and then `scripts/check_static_analysis.py`. The static gate is dev-only: CI installs `ruff` and `mypy`, while the runtime dependency list stays empty.
For local release checks, install the dev-only tools in an activated virtual environment if your Python install does not allow global package installs.

Read an artifact:

```bash
python3 scripts/ope.py read --record-type forecast-artifact --id forecast-101 --question-id question-101
```

Read a lifecycle bundle:

```bash
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-502 --question-id question-501
```

Read a compact forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-502 --question-id question-501
```

Read the historical-only no-API forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-702 --question-id question-701
```

Read the resolved source-handoff forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

List public generated records:

```bash
python3 scripts/ope.py list --record-type forecast-artifact --domain weather-logistics
python3 scripts/ope.py list --record-type forecast-bundle --domain weather-logistics
python3 scripts/ope.py list --record-type forecast-card --domain weather-logistics
python3 scripts/ope.py list --record-type evidence-trace --domain weather-logistics
```

Validate a request without executing it:

```bash
python3 scripts/ope.py request --input spec/fixtures/requests/valid-weather-logistics-request.json
```

Plan auto evidence without fetching live sources:

```bash
python3 scripts/ope.py evidence-plan
python3 scripts/ope.py evidence-plan --check
```

Gather auto evidence in fixture-replay mode:

```bash
python3 scripts/ope.py gather-evidence
python3 scripts/ope.py gather-evidence --check
```

Inspect source connector policy:

```bash
python3 scripts/ope.py source-connectors
python3 scripts/ope.py source-connectors --results
```

Inspect live connector readiness without network access:

```bash
python3 scripts/ope.py live-readiness
python3 scripts/ope.py live-readiness --check
```

Inspect the public transport API connector without network access, or run an explicit local capture:

```bash
python3 scripts/ope.py transit-api-connector
python3 scripts/ope.py transit-api-connector --check
python3 scripts/ope.py transit-api-connector --live --save-local --service-window morning_peak
python3 scripts/ope.py transit-api-connector --live --schedule-join --download-static-gtfs --save-local --service-window morning_peak
```

Inspect domain setup records:

```bash
python3 scripts/ope.py domain-setups
python3 scripts/ope.py domain-setups --setup weather-logistics
python3 scripts/ope.py domain-setups --setup seaport-berth-availability
```

Inspect source manifest and field mapping intake:

```bash
python3 scripts/ope.py source-intake
python3 scripts/ope.py source-intake --case accepted
python3 scripts/ope.py source-intake --case accepted_partial
python3 scripts/ope.py source-intake --case needs_confirmation
python3 scripts/ope.py source-intake --case rejected
```

Inspect local files and draft source manifest inputs:

```bash
python3 scripts/ope.py source-builder
python3 scripts/ope.py source-builder --case local_draft
python3 scripts/ope.py source-builder \
  --input weather_forecast=spec/fixtures/local-source-files/weather-forecast.json \
  --input historical_baseline=spec/fixtures/local-source-files/history.csv \
  --input declared_operations_outcome=spec/fixtures/local-source-files/outcome.csv \
  --mapping-hint declared_operations_outcome.date=service_date
```

Inspect external connector handoff output:

```bash
python3 scripts/ope.py source-adapter-output
python3 scripts/ope.py source-adapter-intake
python3 scripts/ope.py source-adapter-intake --case unsafe
```

Inspect source quality and mapping confidence:

```bash
python3 scripts/ope.py source-quality
python3 scripts/ope.py source-quality --case source_intake_accepted
python3 scripts/ope.py source-quality --case adapter_insufficient_data
```

Inspect the approved local-folder source runtime:

```bash
python3 scripts/ope.py local-source-runtime
python3 scripts/ope.py local-source-runtime --case approved_local_folder
python3 scripts/ope.py local-source-runtime --case unsafe_path
```

Inspect source-builder to source-intake handoffs:

```bash
python3 scripts/ope.py source-handoff
python3 scripts/ope.py source-handoff --case unconfirmed_builder_draft
python3 scripts/ope.py source-handoff --case confirmed_builder_draft
python3 scripts/ope.py source-handoff --case insufficient_confirmed_builder_draft
```

Inspect source-handoff method gates:

```bash
python3 scripts/ope.py source-handoff-method
python3 scripts/ope.py source-handoff-method --case confirmed_builder_draft
python3 scripts/ope.py source-handoff-method --case insufficient_confirmed_builder_draft
```

Inspect setup benchmark gates and setup-aware method decisions:

```bash
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-benchmark --case accepted
python3 scripts/ope.py setup-benchmark --case accepted_partial
python3 scripts/ope.py setup-benchmark --case needs_confirmation
python3 scripts/ope.py setup-benchmark --case rejected
python3 scripts/ope.py setup-method
python3 scripts/ope.py setup-method --case accepted
python3 scripts/ope.py setup-method --case accepted_partial
python3 scripts/ope.py setup-method --case needs_confirmation
python3 scripts/ope.py setup-method --case rejected
```

Check setup-aware forecast execution:

```bash
python3 scripts/ope.py setup-forecast
python3 scripts/ope.py setup-forecast --check
python3 scripts/ope.py read --record-type forecast-card --id forecast-901 --question-id question-901
```

Check explicit source-handoff forecast execution:

```bash
python3 scripts/ope.py source-handoff-forecast
python3 scripts/ope.py source-handoff-forecast --case confirmed_builder_draft
python3 scripts/ope.py local-source-runtime
python3 scripts/ope.py resolve-source-handoff
python3 scripts/ope.py source-handoff-runbook
python3 scripts/ope.py private-setup-workflow
python3 scripts/ope.py private-source-adapters
python3 scripts/ope.py private-source-adapter-outcomes
python3 scripts/ope.py private-source-adapter-bridge
python3 scripts/ope.py private-source-kind-selection
python3 scripts/ope.py private-source-kind-query-matrix
python3 scripts/ope.py private-setup-requests
python3 scripts/ope.py private-setup-actions
python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001
python3 scripts/ope.py private-setup-action-runbook
python3 scripts/ope.py private-setup-bundles
python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001
python3 scripts/ope.py private-setup-orchestrator
python3 scripts/ope.py agent-pilot-validation
python3 scripts/ope.py pilot-evidence
python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-session-packet
python3 scripts/ope.py pilot-summary-intake
python3 scripts/ope.py pilot-summary-template --section draft
python3 scripts/ope.py pilot-summary-intake --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-findings --from-local-ledger --section summary
python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary
python3 scripts/ope.py simulated-agent-pilot --section summary
python3 scripts/ope.py local-usage-trace
python3 scripts/ope.py setup-engine --goal "add predictions to my app"
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 scripts/ope.py setup-engine --view examples
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
python3 scripts/ope.py capabilities
python3 scripts/ope.py adoption-eval
python3 scripts/ope.py developer-adoption
python3 scripts/ope.py agent-implementation-kit --view quickstart
python3 scripts/ope.py smoke
python3 scripts/ope.py agent-guide --section summary
python3 scripts/ope.py agent-guide --section generic
python3 scripts/ope.py agent-guide --case needs_clarification
python3 scripts/ope.py prediction-feature-setup
python3 scripts/ope.py prediction-feature-setup --view response --case accepted
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py developer-adoption --section quickstart
python3 scripts/ope.py expansion-readiness
python3 scripts/ope.py expansion-readiness --section options
python3 scripts/ope.py repeating-prediction-setup
python3 scripts/ope.py repeating-prediction-setup --section examples
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign status
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-09-18T00:00:00Z --count 100 --full-materialization --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign rollback-method-update
python3 scripts/ope.py prediction-campaign explain
python3 scripts/ope.py prediction-campaign pilot-runbook
python3 scripts/ope.py prediction-campaign pilot-readiness
python3 scripts/ope.py private-setup-adapter-runbook
python3 scripts/ope.py private-setup-adapter-conformance
python3 scripts/ope.py private-setup-adapter-conformance-summary
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

Check recalculation history:

```bash
python3 scripts/ope.py recalculation
python3 scripts/ope.py recalculation --check
```

Run the opt-in Open-Meteo integration probe:

```bash
python3 scripts/ope.py live-readiness --live --service-date YYYY-MM-DD
```

Save a sanitized opt-in live connector result under the ignored local workspace:

```bash
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --draft-source-set --write
```

Read connector-bound evidence provenance:

```bash
python3 scripts/ope.py read --record-type evidence-trace --id forecast-602 --question-id question-601
python3 scripts/ope.py read --record-type evidence-source-set --id evidencesourceset-019
python3 scripts/ope.py read --record-type source-connector-results --id sourceconnectorresults-001
```

Generate the auto-evidence fixture forecast:

```bash
python3 scripts/ope.py auto-forecast
python3 scripts/ope.py resolve-auto-evidence
python3 scripts/ope.py method-comparison
python3 scripts/ope.py method-selection
python3 scripts/ope.py forecast-run
python3 scripts/ope.py forecast-run-matrix
python3 scripts/ope.py forecast-runbook
python3 scripts/ope.py agent-envelopes
python3 scripts/ope.py agent-protocol-map
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-602 --question-id question-601
python3 scripts/ope.py agent-call --operation evidence_trace --forecast-id forecast-602 --question-id question-601
python3 scripts/ope.py agent-call --operation private_setup_bundle --private-setup-request-id privatesetuprequest-001
python3 scripts/ope.py agent-call --operation private_setup_adapter_runbook
python3 scripts/ope.py agent-call --operation private_source_adapter_guidance
python3 scripts/ope.py agent-call --operation private_source_kind_selection
python3 scripts/ope.py agent-call --operation private_source_kind_selection --source-kind private_api
python3 scripts/ope.py agent-call --operation private_setup_source_builder --private-setup-request-id privatesetuprequest-001 --source-builder-case local_draft
python3 scripts/ope.py agent-call --operation private_setup_source_handoff --private-setup-request-id privatesetuprequest-001 --source-handoff-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation private_setup_method_gate --private-setup-request-id privatesetuprequest-001 --method-gate-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation private_setup_forecast_execution --private-setup-request-id privatesetuprequest-001 --forecast-execution-case confirmed_builder_draft
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation lifecycle_bundle --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation resolution_status --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102
python3 scripts/ope.py agent-call --operation campaign_plan
python3 scripts/ope.py agent-call --operation campaign_status
python3 scripts/ope.py agent-call --operation campaign_health
python3 scripts/ope.py agent-call --operation campaign_append_readiness
python3 scripts/ope.py agent-call --operation campaign_calibration_status
python3 scripts/ope.py read --record-type forecast-card --id forecast-602 --question-id question-601
```

Generate the no-API historical baseline forecast:

```bash
python3 scripts/ope.py historical-forecast
python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json
```

Run the local MCP stdio scaffold for an MCP-capable host:

```bash
python3 scripts/ope.py mcp-stdio
python3 scripts/ope.py mcp-adoption --view summary
python3 scripts/check_mcp_adoption_path.py
python3 scripts/ope.py simulated-agent-pilot --section user-prompt
```

Validate one contract record:

```bash
python3 scripts/ope.py validate --input spec/fixtures/valid/binary-weather-logistics-question.json
```

Run the local fixture-mode forecast pipeline:

```bash
python3 scripts/ope.py pipeline
```

Resolve the local pipeline forecast:

```bash
python3 scripts/ope.py resolve-pipeline
```

Check the release manifest:

```bash
python3 scripts/ope.py manifest
python3 scripts/ope.py generate-fixtures --list
python3 scripts/check_mvp_release_surface.py
python3 scripts/check_agent_pilot_validation.py
python3 scripts/check_pilot_session_packet.py
python3 scripts/check_pilot_summary_intake.py
python3 scripts/ope.py pilot-summary-intake --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-summary-template --section commands
python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json
python3 scripts/ope.py pilot-findings --from-local-ledger --section summary
python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section commands
python3 scripts/ope.py developer-adoption --section quickstart
python3 scripts/ope.py expansion-readiness --section options
python3 scripts/ope.py repeating-prediction-setup --section summary
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign rollback-method-update
python3 scripts/ope.py prediction-campaign explain
```

CI release gate:

```text
.github/workflows/release-check.yml
```

The workflow installs dev-only `ruff`/`mypy`, runs `python3 scripts/release_check.py`, and compiles `scripts/*.py`; it does not add runtime dependencies.

Generated fixture reports can be refreshed with:

```bash
python3 scripts/generate_fixture_reports.py --write
python3 scripts/run_fixture_loop.py --write
python3 scripts/resolve_live_weather_outcome.py --write
python3 scripts/plan_auto_evidence.py --write
python3 scripts/gather_auto_evidence.py --write
python3 scripts/generate_source_connectors.py --write
python3 scripts/generate_live_connector_readiness.py --write
python3 scripts/connect_transit_api.py --write
python3 scripts/generate_transit_forward_run_corpus.py --write
python3 scripts/generate_transit_corpus_growth_loop.py --write
python3 scripts/generate_transit_baseline_track_record_gate.py --write
python3 scripts/generate_transit_method_options.py --write
python3 scripts/generate_transit_live_evidence_promotion.py --write
python3 scripts/generate_domain_setups.py --write
python3 scripts/build_source_manifest.py --write
python3 scripts/generate_source_adapter_output.py --write
python3 scripts/generate_source_adapter_intake.py --write
python3 scripts/generate_source_quality_mapping_confidence.py --write
python3 scripts/generate_local_source_runtime.py --write
python3 scripts/generate_source_intake_handoff.py --write
python3 scripts/generate_source_handoff_method_gate.py --write
python3 scripts/generate_source_intake.py --write
python3 scripts/run_auto_evidence_forecast.py --write
python3 scripts/resolve_auto_evidence_outcome.py --write
python3 scripts/run_historical_baseline_forecast.py --write
python3 scripts/compare_forecasting_methods.py --write
python3 scripts/select_forecasting_method.py --write
python3 scripts/generate_setup_benchmark_gate.py --write
python3 scripts/select_setup_method.py --write
python3 scripts/run_setup_forecast.py --write
python3 scripts/run_source_handoff_forecast.py --write
python3 scripts/resolve_source_handoff_outcome.py --write
python3 scripts/generate_source_handoff_setup_runbook.py --write
python3 scripts/generate_private_setup_workflow.py --write
python3 scripts/generate_private_setup_requests.py --write
python3 scripts/generate_private_setup_first_actions.py --write
python3 scripts/generate_private_setup_first_action_runbook.py --write
python3 scripts/generate_private_setup_agent_bundles.py --write
python3 scripts/generate_private_setup_orchestrator.py --write
python3 scripts/generate_agent_pilot_validation.py --write
python3 scripts/generate_pilot_evidence_ledger.py --write
python3 scripts/generate_pilot_session_packet.py --write
python3 scripts/generate_pilot_summary_intake.py --write
python3 scripts/generate_local_usage_trace.py --write
python3 scripts/generate_developer_adoption_surface.py --write
python3 scripts/generate_expansion_readiness_gate.py --write
python3 scripts/generate_repeating_prediction_setup.py --write
python3 scripts/generate_prediction_campaign_manifest.py --write
python3 scripts/generate_prediction_campaign_runner.py --write
python3 scripts/generate_prediction_campaign_forecast_creation.py --write
python3 scripts/generate_prediction_campaign_forecast_artifact.py --write
python3 scripts/generate_prediction_campaign_forecast_write.py --write
python3 scripts/generate_prediction_campaign_resolution_attempt.py --write
python3 scripts/generate_prediction_campaign_doctor.py --write
python3 scripts/generate_prediction_campaign_resume.py --write
python3 scripts/generate_prediction_campaign_evidence_ledger.py --write
python3 scripts/generate_prediction_campaign_calibration_status.py --write
python3 scripts/generate_prediction_campaign_explain.py --write
python3 scripts/generate_private_setup_adapter_chain_runbook.py --write
python3 scripts/generate_private_setup_adapter_conformance_matrix.py --write
python3 scripts/generate_private_setup_adapter_conformance_summary.py --write
python3 scripts/generate_resolution_runtime_reliability.py --write
python3 scripts/generate_private_source_adapter_capabilities.py --write
python3 scripts/generate_private_source_adapter_outcome_matrix.py --write
python3 scripts/generate_private_source_adapter_intake_bridge.py --write
python3 scripts/generate_private_source_kind_selection_examples.py --write
python3 scripts/generate_private_source_kind_query_matrix.py --write
python3 scripts/generate_recalculation_history.py --write
python3 scripts/run_agent_forecast.py --write
python3 scripts/generate_forecast_run_intake_matrix.py --write
python3 scripts/generate_agent_forecast_runbook.py --write
python3 scripts/build_agent_adapter_fixtures.py --write
python3 scripts/generate_agent_adapter_protocol_map.py --write
python3 scripts/run_forecast_pipeline.py --write
python3 scripts/resolve_pipeline_outcome.py --write
python3 scripts/generate_record_index.py --write
python3 scripts/generate_release_manifest.py --write
python3 scripts/ope.py generate-fixtures --write
```

## Not Yet Implemented

OPE still needs:

- generated runtime types or non-Python validators if the project moves beyond local scripts
- a production service runtime if OPE grows beyond local file and CLI surfaces
- source manifest and field mapping intake for arbitrary manual uploads, private APIs, and databases beyond current checked local-file builder fixtures, approved local-folder runtime, and capability declarations
- source-quality-driven source execution, artifact creation, or production-readiness claims
- additional setup-aware method execution beyond the current deterministic fixture path
- forecast execution from ignored local live drafts
- live or scheduled recalculation beyond committed fixtures
- production live-data operations beyond the current allow-listed fixture-checked connector
- production forecast use of live connector results beyond the opt-in readiness probe
- policy-bound live auto-evidence gathering for `data: auto`
- a production agent adapter or hosted HTTP API beyond the local dispatcher, local forecast-run orchestrator, and local MCP stdio scaffold
- a network API, SDK, or hosted service
- a resolved live outcome corpus before any live calibration claim

Until those exist, quality claims should remain limited to the committed fixture harness.
