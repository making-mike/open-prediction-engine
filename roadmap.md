# Open Prediction Engine Roadmap

Last updated: 2026-06-07

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
12. Turn the lifecycle operation store into a database-native local runtime for the existing campaign write paths.
13. Add an embedded internal OPE API so host software can manage many predictions without exposing raw files or raw SQL.
14. Add domain and source configuration contracts so agents can set up new prediction domains from approved files, APIs, or databases.
15. Add background worker coordination only after idempotency, leases, recovery read models, and resource limits are enforced.
16. Harden the embedded runtime so local agents can run it safely without hidden services, raw SQL, or credential leakage.
17. Publish an agent prediction implementation kit that gives coding agents a prediction manual, question-discovery intake, and the shortest correct path from "this feature needs prediction" to validated OPE records.
18. Promote a domain-agnostic engine setup shortcut so coding agents understand OPE as the fastest safe way to create the first prediction engine for a host app, not only as an audit layer after another engine exists.
19. Prove the SQLite operation-store semantics map cleanly to a Postgres-compatible backend before making production storage claims.
20. Add a bounded, approved database source-adapter runtime only after source bindings, credential references, leakage checks, and runtime hardening are stable.
21. Add optional Open Prediction Protocol provider interoperability only as a transport adapter over OPE records, not as a replacement for OPE engine semantics.
22. Gate persistent local SQLite paths behind explicit caller approval, allowlisted workspace state paths, and migration/backup/lock checks before any durable local database file is used.
23. Classify lifecycle operations into strict-lease and idempotency-only guard modes before broadening local worker or hosted runtime behavior.
24. Gate runtime transport promotion before implementing local HTTP, queue, hosted service, or OPP HTTP provider behavior.
25. Scope multi-tenant workspace resources, source bindings, operation queues, credential references, and idempotency namespaces before hosted tenant runtime behavior.
26. Classify universal domain/source fields, domain-specific extension containers, and blocked raw/credential/claim fields before broadening domain setup behavior.
27. Define scoped opaque credential references for private APIs and databases before any richer private-source runtime resolves secrets.
28. Define retention, redaction, tombstone, sanitized projection, and physical-delete exception gates before any hosted erasure or broader private-source retention behavior.
29. Define private `data: auto` source-policy gates before allowing broader private-source discovery, web search, raw SQL, or secret resolution.
30. Keep hosted service, broader private-source parsing, and stronger methods behind explicit readiness gates.

The roadmap is intentionally contract-first, agent-native, and domain-agnostic. OPE should not start as a generic LLM forecast endpoint or an unbounded web crawler. Weather-logistics is the reference wedge used to prove the standard, not the product's long-term boundary.

The agent-facing shortcut should also be domain-agnostic. Helsinki transit, weather-logistics, seaport berth availability, demand risk, stockout risk, SLA breach risk, and similar examples should demonstrate the same reusable OPE setup loop rather than becoming the product identity.

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
- Pilot summary intake now classifies sanitized summary examples and caller-supplied sanitized summary files as ledger-ready, redaction-needed, or blocked through `python3 scripts/ope.py pilot-summary-intake` and `python3 scripts/ope.py pilot-summary-intake --input <summary.json>`.
- Pilot summary template now gives operators a schema-valid sanitized draft that is intentionally not ledger-ready unchanged, plus field guidance, sanitization checklist, and classify/append commands through `python3 scripts/ope.py pilot-summary-template`.
- Simulated agent pilot readbacks now cover one user-provided Helsinki bus prompt plus seven generated prompts, including three non-Helsinki setup-comprehension prompts, across accepted, clarification, blocked, rejected, response-too-large, setup-engine-first, parallel-risk-engine, and audit-layer-only signals through `python3 scripts/ope.py simulated-agent-pilot --section summary`.
- Pilot findings now report eight simulated agent sessions, three non-Helsinki setup-comprehension prompts, setup-engine-first rate, parallel-risk-engine and audit-layer-only confusion counts, and zero real sessions separately, keeping broader adoption, hosted runtime, generated types, and quality claims blocked until real sanitized sessions exist.
- Pilot supervision status now gives agents and moderators one read-only operator loop for the next setup-comprehension task, remaining real-session counts, local summary classification, explicit ignored-local append, findings review, and status review through `python3 scripts/ope.py pilot-supervision-status`.
- Agent guidance readbacks now tell calling agents how to classify messy prompts, ask reusable setup questions for any host prediction goal, keep Helsinki as one narrowing example, use approved source references, and stop at OPE boundaries through `python3 scripts/ope.py agent-guide --section generic`.
- Expansion readiness now exposes a checked post-MVP gate over hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types through `python3 scripts/ope.py expansion-readiness`.
- Repeating prediction setup now exposes a checked non-executing recurrence contract with finite, until-date, open-ended, interval, weekday/window, calibration-threshold, and post-calibration restart examples through `python3 scripts/ope.py repeating-prediction-setup`.
- Prediction campaign manifests now expose a checked dry-run campaign plan with unique campaign, cycle, run, question, forecast, resolution, and scoring IDs, duplicate keys, ignored local-state path policy, and status readbacks through `python3 scripts/ope.py prediction-campaign plan` and `python3 scripts/ope.py prediction-campaign status`.
- Prediction campaign runner readbacks now expose `python3 scripts/ope.py prediction-campaign start` command semantics, recurrence flags, normalized campaign creation from flags or setup JSON, a checked forecast scheduling plan, bounded foreground forecast ticks, runner-clock `--now` scheduling, output modes, dry-run run decisions, a checked missed-run policy, and explicit guarded `--write-local` creation for the next due run.
- Prediction campaign forecast-creation handoffs now bind a ready runner decision to planned question, forecast, card, and bundle IDs through `python3 scripts/ope.py prediction-campaign forecast-create`, without creating artifacts or writing campaign state.
- Prediction campaign forecast artifacts now materialize `forecast-1301` as an unresolved baseline-only checked fixture through `python3 scripts/ope.py prediction-campaign forecast-artifact`, using the standard question, evidence, artifact, and history contracts without live fetches, resolver execution, scoring, or campaign-state writes.
- Prediction campaign forecast-write plans now bind the checked `forecast-1301` lifecycle records to ignored `.ope/live` target paths and required guards through `python3 scripts/ope.py prediction-campaign forecast-write`; explicit `--write-local` copies those records and minimal campaign/run state idempotently while normal checks stay non-mutating.
- Prediction campaign resume readbacks now join the checked campaign manifest, forecast-write plan, open forecast, and campaign resolution queue through `python3 scripts/ope.py prediction-campaign resume`, without reading or writing ignored live state.
- Resolution job registries now have a campaign-aware readback through `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001`, adding the checked `forecast-1301` wait state without executing campaign resolvers or mutating campaign state.
- Resolution scheduler readbacks now have a campaign-aware dry-run tick through `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001`, adding the checked `forecast-1301` wait action without executing campaign resolvers or writing campaign state.
- Prediction campaign resolution-attempt, doctor, evidence-ledger, calibration-status, and explain readbacks now give agents checked campaign due-resolution, health, append-readiness, threshold, pilot-task, error-envelope, and claim-boundary surfaces.
- Campaign plan, status, health, append-readiness, and calibration-status now have checked transport-neutral agent adapter and local MCP readbacks.
- Local usage trace, developer adoption, expansion-readiness, pilot-session packet, and MVP runtime surfaces now include recurring prediction campaign pilot evaluation before hosted scheduling or broader runtime promotion.
- Prediction campaign method-update gate readbacks now block automatic method updates by default, expose approval-needed and approved-plan-ready cases, and keep probability updates, method changes, method weights, method registry writes, and campaign state mutation non-effectful.
- Prediction campaign method-update plan readbacks now define the approval artifact, future effectful command shape, rollback record, and preflight checks needed after the method-update gate, without implementing or running the update.
- Scoped static analysis now includes the campaign method-update, resolution-attempt, resolver runtime, doctor, evidence-ledger, calibration-status, and explain generator/checker surfaces, with type-shape fixes for imported transit and resolution helpers; the gate reports 26 checked source files.
- Prediction campaign manifests now support explicit full 100-run Helsinki pilot materialization through `python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization`, while default previews remain bounded and non-mutating.
- The prediction campaign foreground runner now accepts the full 100-run materialized Helsinki plan, selects the due run by runner clock, exposes `predictionrun-1400` scheduling for the final pilot window, and keeps explicit local forecast writes guarded behind `--write-local`.
- Prediction campaign resolver execution now supports explicit local resolution/scoring writes through `prediction-campaign resolve --execute-resolvers --outcome-csv ... --write-local` or `--missing-outcome`, while keeping outcome rows resolution-only.
- Campaign evidence ledger append now writes idempotent ignored local ledger rows from resolved campaign outcomes through `python3 scripts/ope.py prediction-campaign append --from-local --run-id ... --write-local`.
- Campaign calibration status now reads explicit local campaign ledgers and reports below-threshold, threshold-met, and blocked calibration states through `python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger`.
- Campaign method-update apply and rollback now exist as guarded explicit local commands that require plan-ready evidence and approvals before writing ignored method-binding/audit state.
- The Helsinki 100-run pilot operations runbook now defines setup review, 3-run smoke, foreground runner operation, daily checks, resolution, append, calibration readback, recovery, success criteria, and abort criteria through `python3 scripts/ope.py prediction-campaign pilot-runbook`.
- The Helsinki pilot launch-readiness gate now joins the runbook, mini-smoke path, full 100-run materialization, baseline method boundary, manual prerequisites, launch commands, and blocked actions through `python3 scripts/ope.py prediction-campaign pilot-readiness`.
- The lifecycle operation store now defines and checks a local SQLite runtime boundary for immutable records, operation receipts, idempotency keys, leases, operation audit records, read models, ignored `.ope/live` JSON migration rules, write-local command coverage, and file/database duplicate-prevention compatibility.
- The embedded internal API now has a checked stable operation surface through `python3 scripts/ope.py internal-api`, plus shared in-process, CLI dry-run, and agent-call wrappers over one `call_internal_api()` function; effectful calls return receipt/readback fields, request/response envelopes stay compact, and HTTP, queue, and hosted service are explicit future transports over the same semantics.
- The multi-prediction workspace registry now has a checked readback through `python3 scripts/ope.py prediction-workspace-registry`, binding stable prediction, campaign, domain, source-binding, and schedule IDs with owner/caller metadata, lifecycle operation summaries, workspace read models for active, due, blocked, failed, source-health, calibration, and track-record status, audit-backed configuration lifecycle operation definitions for create, update, archive, and redact, per-prediction idempotency namespaces and leases, workspace resource controls, and cross-prediction isolation checks.
- The background worker runtime now has a checked local readback, bounded dry-run loop, approved ephemeral SQLite commit path, lifecycle-backed control-state readback, and durable local sidecar execution semantics through `python3 scripts/ope.py background-worker`, defining health, pause, resume, drain, shutdown, one-tick, and bounded-loop command semantics, workspace read-model polling, `run_tick` foreground equivalence through the shared internal API, receipt-backed `forecast.create` commits with idempotency keys and lease reserve/release readbacks, pause/resume/drain/shutdown control writes into a worker control read model, host non-interference, heartbeat/shutdown readbacks, operation guards, cancellation/backoff policy, resource limits, blocked operation readbacks, and a non-networked sidecar boundary without starting a daemon or writing persistent state.
- Lightweight runtime security now has a checked hardening readback through `python3 scripts/ope.py runtime-security`, declaring the stdlib-only dependency budget, module and adapter boundaries, path/symlink/database guards, input and response byte limits, credential-reference-only policy, threat-model notes, blocked examples, and local execution boundary without hidden services, live source fetches, credential storage, or hosted runtime claims.
- The agent prediction implementation kit now has a checked readback through `python3 scripts/ope.py agent-implementation-kit`, exposing the compact prediction manual, question-discovery intake, forecastable/needs-clarification/blocked/rejected candidate readbacks, mechanical validation reports, first-run source paths, in-process/CLI/agent-call/local MCP/future transport guidance, starter-template descriptors, conformance counts, and disallowed behavior boundaries without creating forecast artifacts or adding a question-discovery-specific forecast path.
- Postgres compatibility now has a checked storage-semantics readback through `python3 scripts/ope.py postgres-compatibility`, mapping all eight lifecycle operation-store tables, dialect-neutral adapter semantics, all fifteen lifecycle runtime scenarios, SQLite-only assumption guards, and migration/execution boundaries without opening Postgres, running migrations, or making hosted-storage claims.
- Domain/source setup now has checked `domain-configs` and `source-bindings` readbacks: reusable weather-transit and seaport domain configs, accepted/partial/rejected/blocked source-binding cases, approved local-file/source-adapter/API/database coverage, mapping-confidence/source-quality/leakage/freshness/privacy/outcome-availability pre-forecast checks, setup operation lifecycle mappings, credential-reference-only policy, and adapter boundaries that keep private API/database parsing outside OPE records.
- Domain/source field policy now has a checked readback through `python3 scripts/ope.py domain-source-field-policy`, classifying universal domain fields, universal source-binding fields, domain-specific extension containers, source-kind credential-reference rules, blocked raw/credential/claim fields, decision cases, and non-mutating no-runtime-types boundaries.
- Credential reference policy now has a checked readback through `python3 scripts/ope.py credential-reference-policy`, defining opaque caller-owned references, tenant/workspace/source/adapter/source-policy scope, lifecycle and consumer rules, blocked raw token, connection-string, cross-scope, and revoked-reference cases, and a no secret resolution or storage boundary.
- Retention/redaction policy now has a checked readback through `python3 scripts/ope.py retention-redaction-policy`, defining append-only retention classes, archive tombstones, redaction receipts, sanitized projection rebuilds, physical-delete exception gates, blocked forecast-history deletion, and a no silent or normal-check physical deletion boundary.
- Private auto-evidence policy now has a checked readback through `python3 scripts/ope.py private-auto-evidence-policy`, defining the private `data: auto` source-policy overlay for source kinds, policy gates, manifest-only API/database boundaries, blocked web search/raw SQL/raw payload cases, and a no private-source read or secret-resolution normal-check boundary.
- Approved database source-adapter runtime now has a checked readback through `python3 scripts/ope.py database-source-adapter-runtime`, defining a caller-approved database request, sanitized adapter output, eight blocked cases, source-intake/method-gate routing, CLI/internal API/agent-call readbacks, and boundaries that keep production database connections, credentials, raw rows, stack traces, unapproved schema scans, and database-specific forecast paths out of normal checks.
- Optional OPP provider adapter now has a checked readback through `python3 scripts/ope.py opp-provider-adapter`, defining OPP-style request/response mappings, a local fixture Agent Card, one accepted response bound to existing OPE records, five blocked conformance cases, future endpoint guidance, and boundaries that keep HTTP, SSE, payment, aggregation, hosted service, and network listeners out of normal checks.
- Persistent SQLite path policy now has a checked readback through `python3 scripts/ope.py persistent-sqlite-policy`, defining caller approval, `.ope/state` allowlisting, traversal and symlink blockers, explicit JSON-state import dry-run, backup-before-migration, lease alignment, stale-lock receipts, and the boundary that normal checks keep using ephemeral SQLite without creating a persistent database.
- Lifecycle lease policy now has a checked readback through `python3 scripts/ope.py lifecycle-lease-policy`, classifying fourteen lifecycle operations into nine strict-lease operations and five idempotency-only operations, with conflict cases and a boundary that normal checks acquire no leases, write no state, expose no raw lock CRUD, and make no hosted-runtime claims.
- Runtime transport readiness now has a checked readback through `python3 scripts/ope.py runtime-transport-readiness`, preserving in-process internal API, CLI, `agent-call`, and local MCP stdio as current surfaces while local HTTP, queue, hosted service, and OPP HTTP provider behavior remain deferred behind explicit readiness gates.
- Workspace tenant isolation now has a checked readback through `python3 scripts/ope.py workspace-tenant-isolation`, layering tenant/workspace scope over the prediction workspace registry with tenant-local resources, operation queues, source bindings, credential scopes, idempotency namespaces, blocked cross-tenant access cases, and a non-mutating boundary before hosted tenant runtime behavior.
- Setup-engine now has a checked domain-agnostic front door through `python3 scripts/ope.py setup-engine --goal "<host prediction goal>"`, `agent-call --operation setup_engine`, and local MCP tool `ope_setup_engine`, returning candidate forecast contracts, source roles, baseline guidance, host-wrapper shape, examples, and claim boundaries without creating forecast artifacts or hosted runtime.
- Prediction-goal catalog now exposes eight compact non-authoritative host-goal examples through `python3 scripts/ope.py prediction-goal-catalog --view summary` and the setup-engine examples view, keeping Helsinki transit as one reusable setup example rather than the default adoption narrative.
- The embedded host wrapper example now calls setup-engine first, renders `setupEnginePlan` before forecast-card reads, shows host-facing setup status, contracts, source roles, baseline status, forecast-card preview, required inputs, warnings, setup-only blockers, and method-extension guidance without implementing OPE scoring, calibration, hosted runtime, or an untracked risk engine.
- The engine setup adoption comprehension gate now adds non-Helsinki simulated prompts and a real-session task card that measure whether agents run setup-engine before inventing a parallel risk engine, whether they misread OPE as audit-only, and whether they separate OPE-owned contracts/evidence/baseline/forecast-card/resolver/scorer/calibration gates from host-owned UI/sources/runtime/notifications/custom methods.

Not started:

- Arbitrary private API parsing and arbitrary database parsing beyond checked setup, local source-builder fixtures, the approved local-folder runtime, and the approved database source-adapter fixture path.
- Persistent SQLite as the default runtime, normal-check persistent database creation, and automatic ignored-JSON state migration.
- Raw lock control, lease acquisition during normal checks, and hosted queue coordination beyond checked policy readbacks.
- Additional setup-aware method classes beyond the current deterministic fixture path.
- Repeated public transport delay forward runs across enough comparable windows for calibration evidence.
- Actual supervised 100-run Helsinki traffic-disturbance pilot execution and real outcome collection beyond the checked launch-readiness surfaces.
- Long-running automatic future-window polling beyond bounded local foreground ticks.
- Local campaign runner execution for automated resolver attempts, resume mutation, finite count completion, until-date stopping, threshold-targeted stopping, and post-calibration restart policies.
- Runtime forecast execution that consumes newly provided ignored local live drafts beyond the checked promotion fixture.
- Hosted watch or scheduler runtime beyond the local foreground scheduler.
- OS scheduler installation.
- Production hosted, HTTP, or queue agent adapter runtime.
- Local HTTP listeners, queue runtime, hosted service runtime, and OPP HTTP provider runtime beyond checked readiness-gate readbacks.
- Hosted service runtime and network API.
- Hosted tenant runtime, tenant administration APIs, and cross-tenant workspace operations beyond the checked isolation policy readback.
- Production forecast use of live connector results.
- Effectful workspace queues beyond the checked stable-ID, read-model, configuration-lifecycle, idempotency, lease, resource-control, and isolation registry readback.
- Explicit local sidecar process command beyond the checked embedded/default sidecar semantics.
- Direct question-discovery agent-call, HTTP, or queue operations beyond the checked agent implementation kit adapter guidance.
- OPP HTTP/SSE/payment/aggregation provider runtime beyond the checked optional adapter fixture.
- Generated language-specific runtime types remain deferred until pilot/adoption evidence shows they reduce setup friction.

In progress:

- Milestone 140 and Milestone 150 now have accepted agent-only simulation evidence through eight checked simulated sessions, including three non-Helsinki setup-comprehension prompts. They still have zero accepted real supervised sessions; 3-5 real sanitized sessions are required before broader adoption evidence can be claimed.
- Milestones 152, 153, 154, 155, and 156 now provide the ignored local pilot-evidence append path, lifecycle operation coverage, supervised pilot operator status, non-ledger-ready summary template, and domain-agnostic agent guidance needed to collect real session evidence without committing it or upgrading quality claims.

Next:

1. Run `python3 scripts/ope.py pilot-supervision-status --section commands`, then run 3-5 supervised local pilot sessions using the checked pilot session packet, including the `engine_setup_shortcut_comprehension` task.
2. Start each sanitized summary from `python3 scripts/ope.py pilot-summary-template --section draft`, fill it outside checked fixtures, classify it through `pilot-summary-intake --input <summary.json>`, append accepted summaries with `pilot-evidence --input-summary <summary.json> --write-local`, review `pilot-findings --from-local-ledger --section summary`, and recheck `pilot-supervision-status --from-local-ledger --section summary`.
3. Use `agent-guide --section generic` during the real sessions to test whether agents ask reusable setup questions before specializing to an example domain, and use `agent-guide --case needs_clarification` only for the Helsinki example prompt.
4. Keep generated runtime types deferred until real pilot evidence shows type-specific friction.
5. Keep any future HTTP, OPP provider runtime, hosted service, richer private-source execution, or non-baseline method behavior behind explicit readiness gates.
6. Keep `transitmethod-100` historical-frequency baseline as the default method until comparable evidence, approvals, benchmark evidence, and method-update plans allow stronger methods.

MVP path:

- Milestones 72-80 define the minimum local, agent-native OPE product: connect approved or adapter-provided data, forecast before the outcome, preserve provenance, recalculate from pre-close evidence, resolve later, score against a baseline, and expose the whole loop through agent-readable surfaces.
- Milestones 81-90 should validate that product with real agent/developer use, add local measurement, grow evidence toward claim thresholds, and improve adoption before expanding into hosted or broad private-source runtimes.
- Milestones 91-102 should make repeated prediction setup easy for agents: one local campaign manifest, one foreground terminal loop, flexible recurrence policy, unique run state, resolver execution, append-only corpus evidence, calibration readbacks, a non-effectful method-update gate, a non-effectful update plan, and release-time static coverage for the campaign readbacks without hosted scheduling.
- Milestones 103-110 turn the Helsinki campaign from checked readbacks into a local pilot that can materialize 100 planned baseline predictions, collect them, resolve and score them, append evidence, report calibration readiness, and pass a launch-readiness gate before any hosted scheduler or default non-baseline method exists.
- Milestone 111 defined the storage/runtime architecture for real multi-agent execution: a lifecycle operation log, immutable record store, idempotency table, leases, read models, and tombstone/archive rules, starting with local SQLite and leaving Postgres/hosted service implementation behind explicit readiness gates.
- Milestones 112-118 should move from checked database architecture to an embedded, database-native, multi-prediction OPE runtime: first migrate current campaign operations into lifecycle operations, then add a stable internal API, multi-prediction registry, domain/source configuration package, background worker loop, lightweight security hardening, and an agent prediction implementation kit with question discovery.
- Milestone 119 should prove that the SQLite-first operation store does not bake in SQLite-only semantics before OPE makes stronger storage portability claims.
- Milestone 120 turned database source bindings into one bounded approved source-adapter runtime, with credentials outside OPE records and query execution behind caller approval.
- Milestone 121 exposes OPE through Open Prediction Protocol only as an optional provider adapter fixture over OPE's internal API, forecast cards, evidence traces, and lifecycle bundles.
- Milestone 122 gates persistent SQLite file paths behind explicit caller approval, workspace-state allowlisting, migration dry-runs, backup/lock guards, and normal-check ephemeral runtime boundaries.
- Milestone 123 classifies lifecycle operation guard modes into strict leases for race-prone writes and idempotency-only guards for retry-safe operations, without letting readbacks acquire leases or expose raw lock controls.
- Milestone 124 gates runtime transport promotion: local in-process API, CLI, agent-call, and MCP remain current while local HTTP, queue, hosted service, and OPP HTTP provider runtimes stay deferred until checked readiness evidence exists.
- Milestone 125 defines tenant-scoped workspace isolation for multi-prediction host contexts: resource controls, source bindings, operation queues, credential references, and idempotency namespaces are tenant/workspace-scoped while hosted tenant runtime behavior remains unimplemented.
- Milestone 126 classifies universal domain and source-binding fields versus domain-specific extensions, with blocked raw/credential/claim/hosted-runtime fields and no generated runtime types.
- Milestone 127 defines scoped opaque credential references for private API and database source bindings without storing secrets or resolving them in normal checks.
- Milestone 128 defines retention/redaction policy for append-only records, archive tombstones, redaction receipts, sanitized projection rebuilds, and future physical-delete exception gates without implementing silent deletion or normal-check erasure.
- Milestone 129 defines the private `data: auto` source-policy overlay for source kinds, required policy gates, manifest-only private API/database paths, and blocked web search, raw SQL, raw payload retention, private-source reads, and secret resolution in normal checks.
- Milestones 130-134 added the first checked agent incorporation path: question discovery, Helsinki starter context, guided first forecast, local MCP integration tools, and a first-forecast efficiency gate.
- Milestones 135-141 should convert that checked path into a copyable external-agent adoption kit: front-door quickstart, fast smoke check, stable prediction-feature contract, host wrapper example, MCP adoption transcript, real pilot evidence, and a generated-types decision.
- Milestones 142-145 and 156 added prompt guidance, prompt-to-question planning, a domain-agnostic setup flow, a Helsinki narrowing example, and an instruction pack so agents see OPE as the first engine setup path for any host prediction goal, with Helsinki only as one example.
- Milestone 146 reframed the checked adoption front door around a domain-agnostic engine setup shortcut and added the planned setup-engine spec; Milestones 147-150 should add the canonical command/readback, generic example goal catalog, host wrapper guidance that renders setup results, adoption tests that check whether agents choose OPE before inventing their own risk engine, and pilot evidence that measures this comprehension.
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

Status: Complete.

Goal: make one foreground terminal command create future forecasts on schedule, then leave due resolutions to the checked resolver path.

Tasks:

- [x] Add a checked dry-run `python3 scripts/ope.py prediction-campaign start` readback before effectful foreground execution.
- [x] Turn `python3 scripts/ope.py prediction-campaign start` into local foreground execution.
- [x] Support dry-run campaign creation input from flags and from a setup JSON file.
- [x] Expose finite count, until date, open-ended, interval, and calibration-threshold modes from the same command surface in the dry-run readback.
- [x] Expose `--interval`, `--count`, `--until`, `--calibration-target`, `--post-calibration-action`, and `--post-calibration-delay` without requiring agents to write raw scheduler syntax.
- [x] Add a checked forecast-creation handoff for the ready run before effectful artifact creation.
- [x] Add a checked unresolved campaign forecast artifact for the ready run using the standard lifecycle contracts.
- [x] Add a checked non-mutating campaign forecast write plan before effectful ignored-state mutation.
- [x] Add explicit guarded `--write-local` execution for the ready run that writes lifecycle records plus minimal campaign/run state under ignored `.ope/live/prediction-campaigns/`.
- [x] Add forecast scheduling, not only resolution scheduling: the runner must create the next forecast before close when the recurrence policy says it is due.
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
- CLI forecast scheduling view `python3 scripts/ope.py prediction-campaign start --view forecast-schedule`
- bounded foreground tick `python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl`
- next-due foreground tick `python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl`
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

Status: Complete.

Goal: connect campaign-created forecasts to due resolution, scoring, retry, and recovery without manual per-run commands.

Tasks:

- [x] Extend the existing resolution job registry to read campaign manifests as well as standalone forward-run states.
- [x] Let the campaign runner call the checked resolver-attempt readback for due runs when `--execute-resolvers` is explicit.
- [x] Record per-run resolver attempts, failure categories, retry eligibility, source fetch metadata, and sanitized diagnostics.
- [x] Avoid duplicate resolution and duplicate scoring for runs that are already resolved, ambiguous, annulled, blocked, or excluded.
- [x] Add resume behavior after terminal interruption: the runner should continue from campaign state and never overwrite prior run evidence.
- [x] Add compact agent readbacks for campaign health, due runs, failed runs, append-ready runs, and next action.

Exit criteria:

- A terminal campaign can survive interruption and resume without losing the forecast-before-outcome trail.
- Agents can tell whether to wait, retry, resolve, append, or stop without reading raw state files.

Expected outputs:

- campaign-aware `python3 scripts/ope.py resolution-jobs --campaign ...`
- campaign-aware `python3 scripts/ope.py resolution-scheduler --campaign ...`
- `python3 scripts/ope.py prediction-campaign resolve`
- `python3 scripts/ope.py prediction-campaign resume`
- `python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state`
- `python3 scripts/ope.py prediction-campaign doctor`

Completed outputs so far:

- `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001`
- `python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z`
- `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001`
- `python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z`
- `python3 scripts/ope.py prediction-campaign resolve`
- `python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers`
- `python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers`
- `python3 scripts/ope.py prediction-campaign doctor`
- `python3 scripts/ope.py prediction-campaign doctor --view queues`
- `python3 scripts/ope.py prediction-campaign start --now 2026-06-11T07:15:00Z --execute-resolvers --max-ticks 1 --output-format jsonl`
- `python3 scripts/ope.py prediction-campaign resume`
- `python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state`
- checked campaign-aware fixture at `spec/fixtures/generated/resolution-jobs/resolution-jobs-campaign.generated.json`
- checked campaign-aware scheduler fixture at `spec/fixtures/generated/resolution-scheduler/resolution-scheduler-campaign-run.generated.json`
- checked campaign resolution-attempt fixture at `spec/fixtures/generated/prediction-campaign-resolution-attempt/weather-transit-delay-campaign-resolution-attempt.generated.json`
- checked campaign doctor fixture at `spec/fixtures/generated/prediction-campaign-doctor/weather-transit-delay-campaign-doctor.generated.json`
- checked campaign resume fixture at `spec/fixtures/generated/prediction-campaign-resume/weather-transit-delay-campaign-resume.generated.json`
- source binding from forward-run state plus checked campaign manifest, campaign forecast artifact, and forecast-write plan
- due campaign resolution jobs route to the checked `prediction-campaign resolve` command instead of a generic future placeholder
- bounded campaign foreground ticks call the checked resolution-attempt readback for due runs when `--execute-resolvers` is explicit
- checked resolution-attempt safety cases block already resolved, ambiguous, annulled, missed, and duplicate runs from duplicate resolution or duplicate scoring
- compact doctor readback joins campaign health, due/waiting/failed/blocked/append-ready queues, duplicate protection, recovery posture, and next action without ignored-state reads
- resume readback can inspect simulated interrupted state or explicit ignored local state, reports local run-state/idempotency counts, and keeps continuation behind explicit local writes
- release-manifest, MVP-smoke, CLI, docs, roadmap, and decision-log wiring for campaign-aware resolution job, scheduler, resolution-attempt, doctor, and resume readbacks

## Milestone 95: Append-Only Calibration Evidence Ledger

Status: Complete.

Goal: turn resolved campaign runs into local comparable evidence without manual corpus editing.

Tasks:

- [x] Add an append-only local campaign evidence ledger that stores comparable scored rows and exclusion rows separately.
- [x] Add append checks for forecast-before-close, resolution-after-horizon, score binding, source-policy binding, observation coverage, comparable scope, and no post-close evidence leakage.
- [x] Make append idempotent: the same resolved run can be inspected repeatedly without creating duplicate corpus rows.
- [x] Preserve excluded rows for audit with reason codes such as missed close, missing outcome, low coverage, feed unavailable, invalid window, leakage risk, ambiguous, annulled, and non-comparable.
- [x] Add `prediction-campaign append-ready` and `prediction-campaign append` commands, with dry-run default and explicit mutation for ignored local ledgers.
- [x] Let track-record and calibration gates read the checked fixture corpus plus selected local campaign ledgers when `--live` or `--campaign` is explicit.
- [x] Keep normal release checks deterministic and offline.

Exit criteria:

- A resolved campaign can grow local comparable evidence toward 30-run track-record and 100-run calibration thresholds without hand-editing JSON.
- Append operations are local, append-only, auditable, and safe to rerun.

Expected outputs:

- `spec/prediction-campaign-evidence-ledger.schema.json`
- `spec/prediction-campaign-evidence-ledger.md`
- `python3 scripts/ope.py prediction-campaign append-ready`
- `python3 scripts/ope.py prediction-campaign append`
- `python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001`

Completed outputs so far:

- checked campaign evidence-ledger fixture at `spec/fixtures/generated/prediction-campaign-evidence-ledger/weather-transit-delay-campaign-evidence-ledger.generated.json`
- `python3 scripts/ope.py prediction-campaign append-ready`
- `python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary`
- `python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001`
- `python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001 --ledger-case comparable_scored`
- `python3 scripts/generate_prediction_campaign_evidence_ledger.py --check`
- `python3 scripts/check_prediction_campaign_evidence_ledger.py`
- append checks for forecast timing, source policy, no-leakage, resolution timing, score binding, coverage, comparable scope, and duplicate row keys
- explicit append-only `--write-local` path under ignored `.ope/live/prediction-campaigns/.../evidence-ledger.json`, with stable row keys that skip already-present rows
- transit track-record gate campaign mode includes excluded or comparable campaign ledger rows while preserving below-threshold claim boundaries

## Milestone 96: Calibration Gate And Post-Calibration Continuation

Status: Complete.

Goal: once a campaign reaches enough comparable outcomes, generate calibration readbacks and follow the configured continuation policy.

Tasks:

- [x] Extend the transit track-record and calibration gate to read campaign evidence ledgers and produce threshold-aware local readbacks.
- [x] Generate calibration summaries only when the declared comparable resolved threshold is met.
- [x] Distinguish calibration measurement from automatic model tuning: the first implementation reports calibration and does not silently change method behavior.
- [x] Add campaign cycle state so post-calibration policies can stop, continue collecting evidence, pause, or start the next cycle after a configured delay.
- [x] Support open-ended campaigns that have no count but pause and resume after calibration according to `postCalibrationPolicy`.
- [x] Add warnings when a campaign has enough runs but too many exclusions, horizon gaps, source failures, or non-comparable windows to support a calibration claim.
- [x] Keep stronger method selection, recalibration of probabilities, and model updates behind a later explicit method-update gate.

Exit criteria:

- A campaign that reaches 100 comparable resolved outcomes can produce a local calibration readback.
- A campaign without a count can automatically decide whether to stop, continue, pause, or start the next cycle after the configured post-calibration delay.

Expected outputs:

- `python3 scripts/ope.py prediction-campaign calibration-status`
- `python3 scripts/ope.py transit-track-record-gate --campaign ...`
- checked examples for below-threshold, threshold-met, too-many-exclusions, and post-calibration-restart cases

Completed outputs:

- `spec/prediction-campaign-calibration-status.schema.json`
- `spec/prediction-campaign-calibration-status.md`
- checked calibration-status fixture at `spec/fixtures/generated/prediction-campaign-calibration-status/weather-transit-delay-campaign-calibration-status.generated.json`
- `python3 scripts/ope.py prediction-campaign calibration-status`
- `python3 scripts/ope.py prediction-campaign calibration-status --calibration-case threshold_met --view readback`
- `python3 scripts/ope.py prediction-campaign calibration-status --calibration-case too_many_exclusions --view summary`
- `python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle`
- `python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001`
- checked below-threshold, threshold-met, too-many-exclusions, and post-calibration-restart cases
- explicit method-update boundary: calibration readbacks never tune, retrain, update probabilities, change forecast methods, or start cycles during normal checks

## Milestone 97: Repeating Prediction Pilot Experience

Status: Complete.

Goal: make repeated prediction setup simple enough for Codex or another agent to run during pilot sessions without custom glue code.

Tasks:

- [x] Add a pilot task card for starting a repeating prediction campaign and explaining the next forecast, next resolution, evidence threshold, and claim boundary.
- [x] Add a short runbook for "start 100 calibration sessions in a terminal" and "start an open-ended campaign that pauses after calibration and resumes later."
- [x] Add agent adapter and MCP readbacks for campaign plan, status, health, append-readiness, and calibration status.
- [x] Add sanitized error envelopes for invalid interval, missed forecast close, unavailable live source, duplicate campaign, unsafe source policy, and unsupported post-calibration action.
- [x] Add local usage trace events for campaign start, forecast-created, resolve-due, resolver-executed, append-ready, appended, calibration-threshold-met, paused, resumed, and stopped.
- [x] Update developer adoption and expansion-readiness surfaces so recurring prediction setup is evaluated before hosted scheduling or broader runtime work.

Exit criteria:

- A pilot agent can start, monitor, explain, stop, and resume a repeating prediction campaign using documented commands and machine-readable readbacks.
- Pilot feedback can distinguish agent UX issues from forecast-quality or calibration evidence.

Expected outputs:

- `spec/repeating-prediction-pilot-runbook.md`
- `spec/prediction-campaign-explain.schema.json`
- `spec/prediction-campaign-explain.md`
- checked campaign explain fixture at `spec/fixtures/generated/prediction-campaign-explain/weather-transit-delay-campaign-explain.generated.json`
- `python3 scripts/ope.py prediction-campaign explain`
- `python3 scripts/ope.py prediction-campaign explain --view task`
- `python3 scripts/ope.py prediction-campaign explain --view errors`
- agent adapter operations for campaign plan/status/health/append-readiness/calibration-status readbacks
- pilot-session-packet task card for repeating prediction setup
- local usage trace campaign lifecycle events
- developer-adoption, expansion-readiness, release-manifest, MVP runtime, docs, roadmap, and decision-log wiring for recurring prediction pilot evaluation

## Milestone 98: Codebase Quality And Tooling Hardening

Status: Complete.

Goal: act on the comprehensive repository review — finish consolidating the residual fixture-scaffold duplication, add automated lint/type and a security hardening, and improve check-suite developer experience, without changing runtime behavior or generated fixtures.

Tasks:

- [x] Deduplicate the remaining `compact_json` copy: import it from `ope_fixtures` in `run_resolution_scheduler.py` instead of redefining it (so `render_json` and `compact_json` each live once, in `ope_fixtures.py`).
- [x] Harden `ensure_safe_local_path` in `generate_prediction_campaign_forecast_write.py` to resolve the target and confirm it stays under `.ope/live/prediction-campaigns`, defeating symlink escape (the path already rejects absolute paths and `..`).
- [x] Parallelize `run_checks.py` so the ~170 subprocess checks fan out across workers, cutting local wall-time without losing coverage.
- [x] Add a dev-only lint and scoped type gate (`ruff` + `mypy`) to `release_check.py` and CI, enforcing the current quality-tooling/campaign-write type surface while keeping the runtime stdlib-only.
- [x] Extract a shared validate+write/check helper so the delegating `check_or_write` wrappers and similar single-output generators share one path.
- [x] Split oversized modules: lift the `--write-local` runtime out of `generate_prediction_campaign_forecast_write.py`, and group `ope.py` command handlers.
- [x] Reduce documentation lockstep churn: convert the monolithic README/PRODUCT wedge paragraphs to additive bullet lists or generated sections.

Exit criteria:

- `def render_json` and `def compact_json` each appear exactly once (in `ope_fixtures.py`).
- `ensure_safe_local_path` rejects symlinked targets that resolve outside the campaign state root.
- `python3 scripts/run_checks.py` stays green and completes substantially faster.
- `python3 scripts/release_check.py` runs lint and type checks and stays green; CI enforces them.

Expected outputs:

- shared `ope_fixtures` helper covering validate+write/check
- a parallel `run_checks.py`
- `python3 scripts/run_checks.py --workers 8` passes 181 checks in 754.19 seconds
- `python3 scripts/ope.py generate-fixtures --list` provides a cheap aggregate fixture command inventory for CLI smoke tests
- `python3 scripts/release_check.py` passes 181 checks with 8 workers in 746.26 seconds, then passes `ruff` over `scripts/` and scoped `mypy`; the current scoped mypy surface now covers 15 source files
- `ruff`/`mypy` configuration, `scripts/check_static_analysis.py`, and a CI install step
- `emit_generated` in `ope_fixtures.py` backs `write_generated`, `check_generated`, and `validate_and_emit`, with direct migrations for auto-evidence, transit method options, private setup orchestrator, and local usage trace single-output generators
- `prediction_campaign_forecast_write_runtime.py` owns guarded local campaign forecast writes, leaving `generate_prediction_campaign_forecast_write.py` at 377 lines for plan generation and CLI views
- shared `ope.py` command-building helpers reduce repeated prediction-campaign subcommand flag plumbing
- README and PRODUCT public-beta/current-state surfaces are additive bullet lists instead of monolithic status paragraphs

## Milestone 99: Campaign Method Update Gate

Status: Complete.

Goal: close the post-calibration method-update boundary with a checked read-only gate before any forecast probabilities, method weights, method selections, or method registries can change.

Tasks:

- [x] Add a schema-bound method-update gate record that binds campaign manifest, calibration status, and transit method options.
- [x] Cover below-threshold, threshold-met-needs-approval, approved-plan-ready, and regression-risk cases.
- [x] Add CLI views for evidence, proposal, approval, decision, summary, and execution boundary.
- [x] Keep automatic updates, effectful updates, probability recalibration, method changes, method-weight changes, method-registry writes, live fetches, resolver execution, and campaign-state writes disabled.
- [x] Wire schema coverage, generator checks, CLI checks, MVP release-surface checks, release manifest, docs, roadmap, and decision log.

Exit criteria:

- `python3 scripts/ope.py prediction-campaign method-update-gate` blocks below-threshold updates.
- `python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view decision` can report a plan-ready case while still requiring a future explicit effectful command.
- Normal checks validate the generated gate fixture against `spec/prediction-campaign-method-update-gate.schema.json`.

Expected outputs:

- `spec/prediction-campaign-method-update-gate.schema.json`
- `spec/prediction-campaign-method-update-gate.md`
- checked fixture at `spec/fixtures/generated/prediction-campaign-method-update-gate/weather-transit-delay-campaign-method-update-gate.generated.json`
- `scripts/generate_prediction_campaign_method_update_gate.py`
- `scripts/check_prediction_campaign_method_update_gate.py`
- `python3 scripts/ope.py prediction-campaign method-update-gate`
- `python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case threshold_met_needs_approval --view decision`
- `python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view proposal`
- `python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case regression_risk --view evidence`
- release-manifest, MVP-smoke, CLI, spec docs, README/PRODUCT, roadmap, and decision-log wiring for the method-update gate

## Milestone 100: Campaign Method Update Plan

Status: Complete.

Goal: define the approval artifact, future effectful command shape, rollback record, and preflight checks required after a method-update gate is plan-ready, without applying any method update.

Tasks:

- [x] Add a schema-bound method-update plan record that binds the campaign manifest and method-update gate.
- [x] Cover gate-blocked, approval-missing, rollback-missing, and plan-ready cases.
- [x] Add CLI views for plan, approval, future command, rollback, preflight, decision, summary, and execution boundary.
- [x] Keep the future effectful command unimplemented and out of normal checks.
- [x] Keep plan reads from writing plan artifacts, campaign state, method registries, probabilities, method weights, forecast methods, live data, resolver outputs, or campaign cycles.
- [x] Wire schema coverage, generator checks, CLI checks, MVP release-surface checks, release manifest, docs, roadmap, and decision log.

Exit criteria:

- `python3 scripts/ope.py prediction-campaign method-update-plan` blocks when the method-update gate is not ready.
- `python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command` returns the future command shape while marking it unimplemented and unavailable to normal checks.
- Normal checks validate the generated plan fixture against `spec/prediction-campaign-method-update-plan.schema.json`.

Expected outputs:

- `spec/prediction-campaign-method-update-plan.schema.json`
- `spec/prediction-campaign-method-update-plan.md`
- checked fixture at `spec/fixtures/generated/prediction-campaign-method-update-plan/weather-transit-delay-campaign-method-update-plan.generated.json`
- `scripts/generate_prediction_campaign_method_update_plan.py`
- `scripts/check_prediction_campaign_method_update_plan.py`
- `python3 scripts/ope.py prediction-campaign method-update-plan`
- `python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case approval_missing --view approval`
- `python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case rollback_missing --view rollback`
- `python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command`
- release-manifest, MVP-smoke, CLI, spec docs, README/PRODUCT, roadmap, and decision-log wiring for the method-update plan

## Milestone 101: Static Coverage For Method Update Surfaces

Status: Complete.

Goal: make the new campaign method-update gate and plan scripts part of the release-time scoped type gate instead of leaving them covered only by runtime checks.

Tasks:

- [x] Add `scripts/generate_prediction_campaign_method_update_gate.py` to the scoped mypy files.
- [x] Add `scripts/generate_prediction_campaign_method_update_plan.py` to the scoped mypy files.
- [x] Add `scripts/check_prediction_campaign_method_update_gate.py` to the scoped mypy files.
- [x] Add `scripts/check_prediction_campaign_method_update_plan.py` to the scoped mypy files.
- [x] Verify the dev-only static gate still passes.

Exit criteria:

- `python3 scripts/check_static_analysis.py` passes with the expanded scoped mypy file list.
- The static gate reports 15 checked source files.

Expected outputs:

- `pyproject.toml` scoped mypy file list includes the method-update gate and plan generator/checker scripts.
- `.venv-static/bin/python scripts/check_static_analysis.py` reports `Success: no issues found in 15 source files`.

## Milestone 102: Static Coverage For Campaign Readbacks

Status: Complete.

Goal: make the campaign resolution-attempt, doctor, evidence-ledger, calibration-status, and explain scripts part of the release-time scoped type gate, and fix the imported helper type shapes that gate exposes.

Tasks:

- [x] Add the campaign resolution-attempt, doctor, evidence-ledger, calibration-status, and explain generators to the scoped mypy files.
- [x] Add the matching campaign semantic checker scripts to the scoped mypy files.
- [x] Replace ad hoc local argument objects with `argparse.Namespace` where typed helper APIs require it.
- [x] Clarify transit connector protobuf, service-date, schedule-key, and source-adapter-output types without changing generated contract semantics.
- [x] Verify the dev-only static gate and targeted runtime checks still pass.

Exit criteria:

- `python3 scripts/check_static_analysis.py` passes with the expanded scoped mypy file list.
- The static gate reports 25 checked source files.
- Transit connector, transit forward-run, resolution jobs, campaign resume, and campaign doctor checks pass.

Expected outputs:

- `pyproject.toml` scoped mypy file list includes the campaign readback generator/checker scripts.
- `scripts/connect_transit_api.py` has explicit type shapes for decoded protobuf values, exception dates, schedule keys, and generated adapter outputs.
- `scripts/run_transit_delay_forward.py`, `scripts/generate_resolution_jobs.py`, `scripts/generate_prediction_campaign_resume.py`, and `scripts/generate_prediction_campaign_doctor.py` use `argparse.Namespace` for typed helper argument objects.
- `.venv-static/bin/python scripts/check_static_analysis.py` reports `Success: no issues found in 25 source files`.

## Milestone 103: Full Helsinki 100-Run Campaign Materialization

Status: Complete.

Goal: materialize the full local 100-run Helsinki traffic-disturbance pilot plan instead of only previewing bounded 4-12 run windows.

Tasks:

- [x] Treat the existing `daily_100_run_transit_calibration` setup as the pilot target for `weather-transit-delays`, `hsl-surface`, `helsinki`, `morning_peak`, and `Europe/Helsinki`.
- [x] Add a checked full-count campaign manifest view that can enumerate all 100 planned service dates, run IDs, question IDs, forecast IDs, resolution IDs, scoring IDs, duplicate keys, and local-state paths.
- [x] Keep the default CLI preview bounded, but add an explicit full-materialization command for the pilot so agents can inspect all 100 planned runs before any forecast artifact is created.
- [x] Add duplicate detection across the full 100-run manifest and expose duplicate conflicts before later local-state overlap checks.
- [x] Preserve the forecast-before-close boundary, missed-run policy, and source-policy binding for every run.

Exit criteria:

- `python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization` prints a 100-run local pilot manifest without creating forecast, resolution, scoring, or ledger records.
- The generated manifest exposes the first, next, and final planned run and makes duplicate keys auditable.
- Normal checks continue to use bounded fixture previews and do not write ignored local state.

Expected outputs:

- Full 100-run Helsinki campaign manifest readback and schema/checker coverage.
- CLI docs for bounded preview versus explicit full materialization.
- Updated pilot runbook step for reviewing the full 100-run plan.

## Milestone 104: Effectful Local Campaign Forecast Runner

Status: Complete.

Goal: create due forecast artifacts for the Helsinki pilot from local campaign state, one run at a time or through bounded foreground ticks, while preserving forecast-before-outcome guarantees.

Tasks:

- [x] Extend `prediction-campaign start --watch --write-local` so it can read the materialized local 100-run campaign, select the next due forecast before `forecastCloseAt`, and update campaign/run state idempotently through the existing safe write path.
- [x] Keep default runner readbacks non-mutating while exposing bounded foreground ticks over the full materialized plan.
- [x] Keep the default pilot method as `transitmethod-100` historical-frequency baseline until method gates allow otherwise.
- [x] Record sanitized runner diagnostics for waiting, ready, missed, duplicate, already-created, and dry-run actions.
- [x] Keep live forecast-time source fetching optional and explicit; baseline-only forecast creation works without live network access.

Exit criteria:

- A foreground local runner can select a due `forecast-N` artifact from the materialized Helsinki campaign and create it only with `--write-local`.
- The runner never backfills forecasts after close time and does not create a second forecast when matching run state already exists.
- Dry-run foreground ticks can inspect all 100 planned Helsinki actions and select the final planned run, `predictionrun-1400`, at its forecast window.

Expected outputs:

- Effectful local campaign forecast runner command with `--full-materialization` support.
- Updated runner schema/checks for 100-row forecast schedules and runner decisions.
- Regression checks for full-plan due-run selection, dry-run non-mutation, missed-run blocking, and explicit local-write availability.

## Milestone 105: Campaign Outcome Resolver Execution

Status: Complete.

Goal: resolve Helsinki pilot forecasts after their service windows using declared resolution-only outcome sources, then write resolution and scoring records for each campaign run.

Tasks:

- [x] Add an effectful `prediction-campaign resolve --execute-resolvers --write-local` path that only runs after `resolutionEligibleAt`.
- [x] Bind each resolution to declared HSL/transit outcome rows or a checked missing-outcome exclusion, never to forecast-time evidence.
- [x] Write resolution records, scoring reports, and sanitized provenance into ignored local campaign state.
- [x] Preserve ambiguous, annulled, missing-outcome, duplicate, and missed-run exclusion cases as audit rows instead of comparable evidence.
- [x] Update resolution jobs and scheduler readbacks so due campaign jobs can execute locally when explicitly approved.

Exit criteria:

- A due campaign run can be resolved and scored locally from an allowed outcome source.
- Missing or unsafe outcome sources produce excluded audit records, not fabricated comparable outcomes.
- Resolution-only trip updates and post-window delay rows are blocked from becoming forecast-time evidence.

Expected outputs:

- Effectful campaign resolver runtime with schema/checker coverage.
- Campaign resolution and scoring local-state records.
- Updated doctor, resume, resolution-jobs, and scheduler readbacks for executed resolver outcomes.

## Milestone 106: Campaign Evidence Ledger Append Runtime

Status: Complete.

Goal: append resolved Helsinki campaign outcomes into a local evidence ledger so the pilot can count toward track-record and calibration thresholds.

Tasks:

- [x] Implement explicit `prediction-campaign append --write-local` for comparable scored rows and excluded audit rows.
- [x] Keep the ledger append-only, idempotent by campaign/run/forecast/scoring IDs, and stored under ignored local state unless a sanitized promotion path is explicitly added later.
- [x] Include enough provenance to trace every row back to the forecast, evidence packet, resolution record, scoring report, source policy, and runner state.
- [x] Update `transit-track-record-gate --campaign` so it can read the local ledger only when explicitly requested.
- [x] Keep excluded rows out of comparable sample counts and report exclusion rate.

Exit criteria:

- Resolved and scored campaign runs can be appended locally without overwriting prior evidence.
- Track-record gates count comparable campaign rows only when the campaign ledger is explicitly selected.
- Excluded rows remain visible for audit and blocker diagnosis but do not unlock quality or calibration claims.

Expected outputs:

- Local campaign evidence ledger writer.
- Ledger schema/checker updates for comparable and excluded rows.
- Track-record gate readback with campaign-ledger inclusion and threshold progress.

Completed outputs:

- `python3 scripts/ope.py prediction-campaign append-ready --from-local --run-id predictionrun-1301`
- `python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local`
- `python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001 --from-local-ledger`
- local evidence-ledger rows now include run-state, forecast-artifact, evidence-packet, forecast-history, resolution-record, and scoring-report paths
- temp-state checker coverage for comparable scored appends, missing-outcome excluded appends, idempotent repeated appends, and explicit local-ledger track-record inclusion

## Milestone 107: Helsinki Calibration Readback From 100 Comparable Outcomes

Status: Complete.

Goal: generate a calibration and track-record readback once the Helsinki pilot reaches 100 comparable resolved outcomes, without automatically changing methods or probabilities.

Tasks:

- [x] Add a calibration summary over the explicit campaign ledger once `resolvedComparableSampleSize >= 100`.
- [x] Report Brier score, baseline score, baseline lift, reliability bins, event rate, forecast probability buckets, exclusion rate, and confidence caveats.
- [x] Keep calibration summaries measurement-only until a separate method-update approval gate passes.
- [x] Block calibration claims when comparable sample size is below 100, exclusion rate is above policy, or source/outcome provenance is incomplete.
- [x] Add a human-readable pilot summary that distinguishes implementation evidence, track-record evidence, calibration evidence, and quality claims.

Exit criteria:

- `python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger` can report below-threshold, threshold-met, and blocked calibration states from local pilot evidence.
- Calibration summaries do not mutate forecast probabilities, method registry entries, or future campaign methods.
- The default method remains baseline unless a later explicit method-update command is approved.

Expected outputs:

- Local campaign calibration summary readback.
- Updated calibration-status schema/checker coverage.
- Pilot summary docs explaining what can and cannot be claimed after 100 comparable outcomes.

Completed outputs:

- `python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback`
- `python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot`
- local-ledger calibration status blocks below-threshold, high-exclusion-rate, and incomplete-provenance evidence
- measurement-only local calibration summaries include Brier score, baseline score, baseline lift, event rate, 10 reliability/probability buckets, and confidence caveats
- checker coverage for 99 comparable rows, 100 comparable rows, too many exclusions, and incomplete provenance

## Milestone 108: Evidence-Backed Method Update Apply And Rollback

Status: Complete.

Goal: allow a non-baseline method only after the campaign ledger, calibration summary, benchmark evidence, source-policy review, and explicit approvals make the existing method-update gate plan-ready.

Tasks:

- [x] Implement an explicit `prediction-campaign apply-method-update` command only after `method-update-gate` and `method-update-plan` return plan-ready.
- [x] Require method-owner approval, calibration-review approval, source-policy review, benchmark evidence, anti-leakage checks, and a rollback record.
- [x] Start with the transparent weather-adjustment candidate only if evidence remains favorable after the threshold is met.
- [x] Preserve prior forecast histories and keep method changes prospective; never rewrite old forecasts.
- [x] Implement `rollback-method-update` for the approved update artifact before enabling any stronger method in the runner.

Exit criteria:

- The baseline remains the default until evidence and approvals explicitly allow a method update.
- Method updates are auditable, reversible, prospective-only, and blocked in normal checks.
- If evidence does not support the candidate, the pilot continues on `transitmethod-100`.

Expected outputs:

- Effectful method update and rollback command designs with schema/checker coverage.
- Updated runner method-selection binding for future campaign runs after approval.
- Decision-log entry documenting the first approved or rejected method update.

Completed outputs:

- `python3 scripts/ope.py prediction-campaign apply-method-update` blocks by default.
- `python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary` reports the eligible `transitmethod-101` weather-adjustment target without writing local state.
- `python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary` reports the baseline rollback target.
- `--write-local` apply/rollback writes only ignored local campaign method-binding and audit artifacts, requires local campaign state with at least 100 comparable resolved outcomes for apply, and remains idempotent in checker coverage.
- The runner now reports the future `.ope/live/prediction-campaigns/{campaign}/method-binding.json` path while keeping normal checks baseline-only.

## Milestone 109: 100-Run Helsinki Pilot Operations Runbook

Status: Complete.

Goal: give a human or agent the exact local procedure to run, monitor, recover, resolve, score, append, and summarize the Helsinki 100-prediction pilot.

Tasks:

- [x] Write a step-by-step runbook for the local pilot covering setup review, full materialization, foreground runner operation, daily checks, resolution, append, calibration readback, and stop/restart conditions.
- [x] Add smoke checks that exercise a miniature local campaign with two or three runs before running the real 100-run pilot.
- [x] Add operator-facing status commands for next forecast, next resolution, due resolver jobs, append readiness, ledger counts, exclusion rate, and calibration threshold progress.
- [x] Define pilot success criteria: 100 comparable outcomes, acceptable exclusion rate, no forecast-after-close violations, no duplicate forecasts, and complete provenance.
- [x] Define abort criteria for source outages, unsafe evidence, clock drift, path-safety failures, or repeated missed windows.

Exit criteria:

- A developer can run a miniature campaign end to end locally before starting the 100-run Helsinki pilot.
- The 100-run pilot has one documented command sequence and one recovery sequence.
- The runbook states that the best available method is baseline until gates permit otherwise.

Expected outputs:

- `spec/helsinki-traffic-disturbance-pilot-runbook.md`
- Mini-campaign smoke fixture and checks.
- Updated README/PRODUCT/MVP-runtime references for the local 100-run pilot boundary.

Completed outputs:

- `python3 scripts/ope.py prediction-campaign pilot-runbook`
- `python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke`
- `python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status`
- `python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl`
- checked schema/fixture coverage for `spec/fixtures/generated/helsinki-traffic-pilot-runbook/helsinki-traffic-disturbance-pilot-runbook.generated.json`
- documented baseline-first pilot method boundary: `transitmethod-100` remains best available until method-update gates, approvals, benchmark evidence, and rollback are ready.

## Milestone 110: Helsinki Pilot Launch Readiness Gate

Status: Complete.

Goal: give operators a final read-only gate that answers whether the checked local surfaces are ready to start the 100-run Helsinki pilot and which manual confirmations remain outside normal checks.

Tasks:

- [x] Add a `prediction-campaign pilot-readiness` readback that joins the runbook, 3-run smoke path, full 100-run materialization, and baseline method boundary.
- [x] Report checked launch prerequisites, manual prerequisites, launch command sequence, and blocked actions.
- [x] Keep live source availability, local clock, terminal supervision, outcome paths, and workspace capacity as explicit manual confirmations.
- [x] Keep the readiness gate non-mutating: no pilot start, no live fetches, no resolver execution, no ledger append, no method change, and no quality claim.
- [x] Add schema, generated fixture, checker, CLI, release surface, and documentation coverage.

Exit criteria:

- A developer can run one command to see the launch status and the next safe command before the 100-run pilot.
- The gate confirms checked prerequisites while refusing to overclaim machine-local live readiness.
- The launch command remains explicit and supervised through `--write-local`.

Expected outputs:

- `spec/helsinki-traffic-pilot-readiness.md`
- `python3 scripts/ope.py prediction-campaign pilot-readiness`
- `python3 scripts/ope.py prediction-campaign pilot-readiness --view commands`

Completed outputs:

- `python3 scripts/ope.py prediction-campaign pilot-readiness`
- `python3 scripts/ope.py prediction-campaign pilot-readiness --view checks`
- `python3 scripts/ope.py prediction-campaign pilot-readiness --view manual`
- `python3 scripts/ope.py prediction-campaign pilot-readiness --view commands`
- checked schema/fixture coverage for `spec/fixtures/generated/helsinki-traffic-pilot-readiness/helsinki-traffic-pilot-readiness.generated.json`

## Milestone 111: Lifecycle Operation Store And Database Backend

Status: Completed 2026-06-03.

Goal: define the database-backed runtime architecture OPE needs for real multi-agent repeated predictions while preserving the record/lifecycle-first model. The database must provide durability, idempotency, leases, operation auditability, and queryable read models; it must not turn forecast artifacts into mutable CRUD rows.

Tasks:

- [x] Add a lifecycle operation model that represents effectful work as explicit operations such as `campaign.create_run`, `forecast.create`, `forecast.recalculate`, `question.cancel`, `question.annul`, `resolution.record`, `score.create`, `evidence.append`, `method.apply`, `method.rollback`, `record.archive`, and `record.redact`.
- [x] Define immutable record storage for forecast questions, evidence packets, forecast artifacts, forecast histories, resolution records, scoring reports, calibration summaries, method-update audit records, and operation receipts.
- [x] Define idempotency storage keyed by operation type, campaign/run identifiers, caller-provided idempotency key, and source record hashes so agent retries cannot duplicate forecasts, resolutions, scores, or ledger rows.
- [x] Define lease/lock semantics for due-run creation, resolver execution, ledger append, calibration readback, and method-update application so multiple agents can coordinate without racing.
- [x] Define read models for campaign status, next due forecast, due resolution jobs, unresolved forecasts, append readiness, calibration status, track-record progress, failed operations, and recovery actions.
- [x] Define tombstone/archive/redaction records as the replacement for generic delete, preserving audit metadata while allowing privacy or safety cleanup when policy requires it.
- [x] Specify a local SQLite backend as the first implementation target and a Postgres-compatible schema as the production design target, behind a storage adapter that keeps OPE record semantics independent from the database.
- [x] Add migration rules from the current ignored `.ope/live` JSON state into the operation store without rewriting historical forecast probabilities or source provenance.
- [x] Add agent-facing operation preflight/readback commands that show planned writes, blocking guards, idempotency keys, leases, rollback/tombstone behavior, and claim boundaries before mutation.
- [x] Keep hosted service, network API, OS scheduler, private-source credential storage, and production live-source execution out of scope unless a later readiness gate explicitly unblocks them.

Exit criteria:

- OPE has a documented storage adapter boundary that can run locally with SQLite while preserving the existing fixture and ignored-file workflows.
- Every effectful operation has a preflight, idempotency rule, operation receipt, and recovery path.
- Forecast artifacts and histories remain immutable after creation; updates are represented as appended lifecycle records or prospective state changes.
- Delete-like requests resolve to cancel, annul, archive, tombstone, or redact operations with audit records instead of silent physical deletion.
- Multi-agent execution has a clear lease model for forecast creation, resolution, scoring, ledger append, and method-update actions.

Expected outputs:

- `spec/lifecycle-operation-store.md`
- `spec/lifecycle-operation.schema.json`
- `spec/storage-adapter.md`
- SQLite schema notes and Postgres compatibility notes.
- Checked fixtures for create, retry-idempotent, lease-conflict, archive, redaction, method-rollback, pre-calibration-bind, campaign operation bridge, JSON state import, and recovery scenarios.
- CLI/readback surface for inspecting lifecycle operations without requiring a hosted runtime.

## Milestone 112: Database-Native Campaign Operation Bridge

Status: Complete.

Goal: migrate the current effectful local campaign paths from file-first writes into lifecycle operations backed by the local SQLite operation store, while preserving `.ope/live` compatibility during migration.

Tasks:

- [x] Add a database-native pre-calibration binding operation, such as `method.pre_calibrate` or `pre_calibration.bind`, with preflight checks, idempotency, a campaign method-binding lease, source-history hash binding, and prospective-only write semantics.
- [x] Add database-backed operation execution for `forecast.create`, `resolution.record`, `score.create`, `evidence.append`, `method.apply`, and `method.rollback` using the same record payloads and content hashes as the current ignored JSON runtime.
- [x] Keep `.ope/live` JSON as a compatibility adapter until migration is explicit, content-hash checked, and receipt-backed.
- [x] Add migration receipts that import existing ignored JSON state into SQLite without rewriting forecast probabilities, histories, source provenance, or method bindings.
- [x] Add operation receipts and read-model updates for every write path agents currently trigger with `--write-local`.
- [x] Add compatibility checks that prove repeated file-mode and database-mode calls do not duplicate forecasts, resolutions, scores, ledger rows, or method bindings.

Exit criteria:

- Current campaign write commands can run through the local SQLite operation store behind an adapter.
- Pre-calibration is database-native and can be consumed by forecast creation without agents managing raw method-binding files.
- File compatibility remains available but is no longer the only effectful runtime.

Expected outputs:

- Database-backed campaign operation adapter.
- `pre_calibration.bind` or equivalent lifecycle operation schema/readback.
- Migration command or readback for ignored `.ope/live` campaign state.
- Regression checks for idempotent retries, lease conflicts, and file/database compatibility.

## Milestone 113: Embedded Internal API Surface

Status: Complete.

Goal: expose OPE as an internal API that host applications and agents can use like a small embedded service, without requiring raw file manipulation, raw SQL, or direct scheduler control.

Tasks:

- [x] Define a stable internal command/API surface for `create_prediction`, `update_prediction`, `start_prediction`, `pause_prediction`, `resume_prediction`, `run_tick`, `resolve_due`, `append_evidence`, `read_status`, `read_forecast_card`, `read_lifecycle_bundle`, `archive_record`, and `redact_record`.
- [x] Support at least in-process Python calls and CLI/agent-call wrappers over the same operation functions.
- [x] Keep HTTP, queue, and hosted service adapters transport layers over the same internal API, not separate behavior.
- [x] Return operation receipts, idempotency status, blocking guards, next actions, and sanitized diagnostics for every effectful call.
- [x] Add request/response envelopes that are compact enough for agents and explicit enough for host software.
- [x] Document non-interference boundaries: no surprise network calls, no unbounded loops, no hidden scheduler installation, and no automatic method upgrades.

Exit criteria:

- A host application can call OPE as an internal library or local command surface without knowing the file layout.
- Agents can implement OPE integration through a small set of stable operations and readbacks.
- All transports share one semantics layer.

Expected outputs:

- `spec/internal-api.md`
- Internal API schema or typed request records.
- `python3 scripts/ope.py internal-api`
- In-process adapter and CLI compatibility checks.
- Agent-facing examples for creating and managing one prediction through the API.

## Milestone 114: Multi-Prediction Workspace Registry

Status: Complete.

Goal: allow agents to set up and manage any number of predictions, campaigns, domains, schedules, and source bindings in one isolated OPE workspace.

Tasks:

- [x] Add a prediction registry with stable prediction IDs, campaign IDs, domain IDs, source-binding IDs, schedule IDs, status, owner/caller metadata, and lifecycle operation summaries.
- [x] Add read models for all predictions, active predictions, due forecasts, due resolutions, blocked operations, failed operations, source-health blockers, and calibration/track-record progress.
- [x] Add lifecycle operations for prediction configuration create/update/archive/redact that preserve audit history instead of mutating raw config silently.
- [x] Add per-prediction idempotency keys and leases so concurrent agents can manage different predictions without racing.
- [x] Add workspace-level resource controls, including maximum active predictions, maximum queued operations, maximum readback size, and per-prediction execution budgets.
- [x] Add isolation checks so one prediction cannot write another prediction's records, source bindings, method binding, or read models.

Exit criteria:

- One OPE workspace can contain multiple independent predictions and campaigns.
- Agents can list, inspect, start, pause, resume, and archive predictions without reading raw database tables or files.
- Concurrent agents can operate on separate predictions safely.

Expected outputs:

- Prediction registry schema and checked fixtures.
- Workspace status and queue readbacks.
- Multi-prediction smoke checks with at least two domains or two campaigns.
- Isolation and idempotency regression checks.

## Milestone 115: Domain And Source Configuration Package

Status: Complete.

Goal: make OPE configurable for new domains and data sources while keeping setup safe, understandable, and policy-bound.

Tasks:

- [x] Define domain configuration records for question templates, horizons, resolution criteria, baseline method, accepted source roles, exclusion rules, sample thresholds, and claim boundaries.
- [x] Define source binding records for approved local files, source-adapter outputs, APIs, and databases without storing credentials in OPE records.
- [x] Add mapping-confidence, source-quality, leakage, freshness, privacy, and outcome-availability checks before any forecast generation.
- [x] Add setup operations for draft, validate, confirm, update, archive, and redact domain/source configurations.
- [x] Add small examples for at least weather-transit-delay plus one non-transit private operational domain.
- [x] Keep arbitrary private API/database parsing behind adapters and caller approval; OPE receives sanitized manifests, mappings, provenance, and query boundaries.

Exit criteria:

- Agents can configure a new prediction domain without editing generator code.
- Unsafe or low-confidence source bindings are blocked before forecast artifacts are created.
- Domain configs are understandable records, not hidden plugin behavior.

Expected outputs:

- `spec/domain-config.schema.json`
- `spec/source-binding.schema.json`
- Domain/source setup CLI and internal API commands.
- Checked setup fixtures for accepted, partial, rejected, and blocked configurations.

## Milestone 116: Background Worker And Sidecar Runtime

Status: Complete.

Goal: run OPE in the background as a bounded embedded worker or small local sidecar so host software can keep operating while predictions are scheduled, resolved, and monitored.

Tasks:

- [x] Add a checked local worker runtime readback over the lifecycle operation store, internal API, and workspace registry.
- [x] Add a bounded dry-run worker loop that polls database read models for due forecast, resolution, append, recovery, and maintenance operations.
- [x] Use leases, idempotency keys, cancellation flags, and retry/backoff policies for every checked worker-executed dry-run operation.
- [x] Add an approved ephemeral SQLite worker commit path that reserves and releases leases, writes operation receipts, and reports idempotency/read-model effects without writing persistent state in normal checks.
- [x] Add persistent worker control-state read/write semantics for pause, resume, drain, shutdown, and health only through lifecycle operations.
- [x] Add durable sidecar execution semantics over the checked control state without installing hidden daemons, OS schedulers, hosted workers, or network listeners.
- [x] Add health, pause, resume, drain, shutdown, and one-tick command readbacks.
- [x] Keep foreground `run_tick` behavior equivalent to worker behavior for deterministic checks and coding-agent integration examples.
- [x] Add resource limits for CPU time, wall-clock time, queue size, operation count, output size, and source fetch policy.
- [x] Keep the first worker local and non-networked by default: no OS scheduler installation, hosted workers, network listeners, hidden daemons, or automatic live-source execution.
- [x] Add worker readbacks that show which operation would run next, which lease/idempotency guard applies, and why an operation is blocked.

Exit criteria:

- OPE can run one bounded background loop without blocking or interfering with host application workflows.
- A host can stop, pause, resume, or inspect the worker safely.
- Worker execution cannot bypass operation preflight, leases, idempotency, or claim boundaries.
- Normal checks can verify one-tick worker behavior without starting a long-running process or writing persistent local state.

Expected outputs:

- Checked local worker runtime readback module.
- Worker status and recovery readbacks.
- One-tick and bounded-loop checks.
- Sidecar boundary documentation.

## Milestone 117: Lightweight Security And Runtime Hardening

Status: Complete.

Goal: keep OPE small, secure, and understandable for agents and developers before expanding sources, transports, or hosted runtime.

Tasks:

- [x] Define a dependency budget and keep the core runtime on the Python standard library where practical.
- [x] Separate core lifecycle logic, storage adapters, source adapters, method adapters, and transport adapters into small modules with clear boundaries.
- [x] Add path allow-listing, symlink escape checks, database path checks, response-size limits, input-size limits, and sanitized diagnostics to every new runtime surface.
- [x] Keep credentials out of OPE records; store only credential references, source policy IDs, and sanitized provenance.
- [x] Add threat-model notes for malicious source data, prompt/source injection, path traversal, idempotency replay, lease abuse, oversized responses, and accidental private-data exposure.
- [x] Add static and runtime checks that agents can read and run locally without hidden services.

Exit criteria:

- The embedded runtime remains lightweight enough to vendor or run locally in host software.
- Security boundaries are explicit in code, specs, and checks.
- Agents can understand the core implementation without needing a large framework or generated service stack.

Expected outputs:

- `spec/runtime-security.md`
- Dependency and module-boundary checklist through `python3 scripts/ope.py runtime-security --view budget` and `--view modules`.
- Runtime hardening checks for the embedded API, database adapter, worker, and domain/source setup through `python3 scripts/check_runtime_security.py`, `python3 scripts/check_hardening.py`, and `python3 scripts/ope.py runtime-security --check`.
- Updated contributor and agent implementation guidance through the spec index, fixture index, release manifest smoke check, and roadmap status.

## Milestone 118: Agent Prediction Implementation Kit And Question Discovery

Status: Complete.

Goal: make it easy for coding agents to add OPE-backed prediction features in host software by turning an app goal and approved source context into candidate forecast contracts, mechanical validation reports, and normal OPE lifecycle records while preserving the same database and safety semantics.

Tasks:

- [x] Add a compact prediction manual that explains the minimal OPE integration path for a coding agent prompted to add a prediction feature: detect the decision under uncertainty, describe the app goal, bind approved sources, discover candidate forecast contracts, validate one or more contracts, create prediction, start, run tick or worker, read forecast card, resolve, append evidence, score, and inspect calibration.
- [x] Add a question-discovery intake contract that carries app goal, decision to support, approved source references, source roles, forecast-time versus resolution-only evidence, candidate outcome windows, resolution-source hints, safety impact, and optional existing setup/domain hints.
- [x] Add candidate forecast contract readbacks that can return forecastable, needs-clarification, blocked, and rejected candidates with canonical question wording, output type, close time, resolve time, resolution rule, allowed and forbidden evidence, baseline feasibility, source readiness, method boundary, and claim boundary.
- [x] Add a mechanical validation report for candidate contracts covering schema validity, future boundary, resolvability, source-policy binding, leakage risk, outcome availability, mapping confidence, baseline feasibility, method eligibility, scoring readiness, calibration-readiness boundary, and blocker explanations.
- [x] Add a first-run recipe that distinguishes three source paths: approved local files now, sanitized source-adapter output now, and database/API source bindings that wait for a checked runtime.
- [x] Add conformance fixtures for question-discovery intake, candidate contract readbacks, validation reports, embedded API calls, operation receipts, source configuration, multi-prediction registry, worker ticks, and blocked-path examples.
- [x] Add adapter examples for in-process use, CLI use, local MCP use, and future HTTP/queue transports over the same internal API.
- [x] Add "do not implement" guidance for free-form oracle behavior, raw CRUD writes, unbounded background loops, silent deletion, hidden live fetches, credential storage in records, and automatic method upgrades.
- [x] Add small starter templates that keep OPE encapsulated from the host application's main business logic.
- [x] Keep OPE's core role clear: caller agents provide app context and may draft intent, while OPE mechanically validates, canonicalizes, routes, forecasts through registered methods, resolves, scores, and calibrates. Optional agent-assisted question drafting must be explicit, labeled, and kept outside default forecast execution.
- [x] Keep generated language-specific SDKs deferred until conformance evidence shows agents need them.

Exit criteria:

- An agent can add OPE to a host application as an encapsulated internal service without re-learning the full repository.
- An agent can ask "given this app goal and these approved sources, what forecast contracts are valid?" and receive compact candidate and validation readbacks without requiring a domain to be chosen first.
- Accepted candidates can route into existing source-intake, source-handoff, setup benchmark, method decision, forecast execution, resolution, scoring, and calibration surfaces without a question-discovery-specific forecast path.
- Ambiguous, unresolvable, post-outcome, leaky, low-confidence, unsupported-source, or safety-sensitive candidates stop before forecast artifacts are created.
- Conformance checks catch lifecycle, storage, safety, and claim-boundary drift.
- Domains remain reusable setup memory and stricter validation templates, not a hard product boundary that prevents agents from trying to forecast from approved data in a new setup.
- OPE remains a standard plus runtime surface, not a one-off application script or autonomous prediction oracle.

Expected outputs:

- `spec/agent-implementation-kit.md`
- `spec/agent-prediction-manual.md`
- `spec/forecast-question-discovery.md`
- Candidate forecast contract schema and fixture pack through `spec/agent-implementation-kit.schema.json` and `spec/fixtures/generated/agent-implementation-kit/`.
- Question-discovery CLI readbacks and internal API, agent-call, local MCP, and future HTTP/queue adapter guidance through `python3 scripts/ope.py agent-implementation-kit --view adapters`.
- Conformance fixture pack through `python3 scripts/ope.py agent-implementation-kit --view validation`, `--view candidates`, and the generated kit summary.
- Minimal embedded-runtime examples through `python3 scripts/ope.py agent-implementation-kit --view templates`.
- Updated local agent implementation guidance through the spec index, fixture index, release manifest smoke check, MVP release-surface check, and roadmap status.

## Milestone 119: Postgres Compatibility Checkpoint

Status: Complete.

Goal: prove that the SQLite-first lifecycle operation store can map to a Postgres-compatible backend without changing OPE record semantics or making hosted-service claims.

Tasks:

- [x] Add a Postgres compatibility document for `operation_receipts`, `operation_idempotency_keys`, `operation_leases`, `ope_records`, `forecast_history_events`, `operation_audit_records`, `evidence_ledger_rows`, and `read_model_rows`.
- [x] Define the dialect-neutral storage adapter contract for JSON payloads, content hashes, unique idempotency keys, lease acquisition, lease expiry, append-only records, and read-model upserts.
- [x] Add a SQLite-to-Postgres compatibility matrix for every checked lifecycle scenario: create, retry-idempotent, lease-conflict, archive, redaction, method-rollback, pre-calibration-bind, campaign forecast creation, resolution, scoring, evidence append, method apply/rollback, JSON state import, and recovery.
- [x] Add checks that detect SQLite-only assumptions such as rowid dependence, loose typing dependence, non-portable upsert behavior, missing timestamp normalization, or JSON query behavior that cannot be represented in Postgres.
- [x] Keep actual Postgres connection, migrations, hosted storage, and production database operations optional and outside normal checks.

Exit criteria:

- OPE can explain how each lifecycle operation maps from the local SQLite runtime to a Postgres-compatible schema.
- Postgres compatibility is checked as a storage-semantics claim, not as a hosted-service or production-readiness claim.
- The SQLite runtime remains the default local agent runtime while Postgres remains the production-compatible target.

Expected outputs:

- `spec/postgres-compatibility.md`
- Postgres compatibility readback and checker.
- Updated storage-adapter documentation.
- Compatibility fixture or generated matrix covering every lifecycle operation-store scenario.

## Milestone 120: Approved Database Source Adapter Runtime

Status: Accepted.

Goal: turn checked database source bindings into one bounded, caller-approved source-adapter runtime path without giving OPE arbitrary database access or storing credentials/raw private rows.

Tasks:

- [x] Define a database source-adapter runtime request that carries a source-binding ID, source role, approved query-manifest reference, credential reference, row/time limits, freshness window, leakage window, and caller approval state.
- [x] Define the sanitized database adapter output shape that can enter existing source-adapter intake: source manifest, field mapping, provenance summary, source-quality signals, mapping-confidence signals, outcome-availability status, and query-boundary summary.
- [x] Keep credential values, raw SQL with secrets, raw private rows, stack traces, and unapproved schema scans out of OPE records and agent-visible diagnostics.
- [x] Add dry-run and blocked cases for missing approval, missing credential reference, unsafe query boundary, oversized result, stale source, leakage risk, missing outcome source, and insufficient comparable history.
- [x] Add one explicit approved execution path using a controlled local fixture or caller-provided adapter output, while keeping arbitrary private API/database parsing and live production database connections outside normal checks.
- [x] Route accepted database adapter outputs through existing source-intake, source-handoff, setup benchmark, method decision, and forecast execution gates instead of creating a database-specific forecast path.

Exit criteria:

- A coding agent can use an approved database source binding without inventing its own OPE source records.
- OPE records show what database source was connected, how it was mapped, what was rejected or unavailable, and whether forecast execution is allowed.
- Unsafe, unapproved, or low-confidence database cases stop before forecast artifacts are created.

Expected outputs:

- `spec/database-source-adapter-runtime.md`
- Database source-adapter runtime schema and checked fixtures.
- Agent-call/internal API readback for database adapter runtime status.
- Source-intake and method-gate examples for accepted and blocked database adapter outputs.

Completed outputs:

- `spec/database-source-adapter-runtime.schema.json`
- `spec/database-source-adapter-runtime.md`
- `scripts/generate_database_source_adapter_runtime.py`
- `scripts/check_database_source_adapter_runtime.py`
- checked fixture at `spec/fixtures/generated/database-source-adapter-runtime/ope-database-source-adapter-runtime.generated.json`
- CLI command `python3 scripts/ope.py database-source-adapter-runtime`
- internal API operation `database_source_adapter_status`
- agent-call operation `database_source_adapter_runtime_status`
- release, schema, hardening, CLI, and normal-check wiring for the runtime boundary

## Milestone 121: Optional Open Prediction Protocol Provider Adapter

Status: Accepted.

Goal: expose OPE through Open Prediction Protocol as an optional provider adapter for external agent interoperability while keeping OPE's internal API and lifecycle records authoritative.

Tasks:

- [x] Define an OPP-to-OPE request mapping from OPP `PredictionRequest` fields to OPE domain config, forecast request, source policy, horizon, output type, and caller identity fields.
- [x] Define an OPE-to-OPP response mapping from OPE forecast cards and forecast artifacts to OPP `PredictionResponse`, with OPE `forecastId`, `questionId`, evidence-trace ID, lifecycle-bundle ID, score status, and claim boundaries carried through OPP `audit` or `provenance` metadata.
- [x] Add an OPP Agent Card fixture that advertises only domains, horizons, output types, calibration status, compliance status, and pricing modes that OPE can honestly support.
- [x] Keep OPP HTTP, SSE, payment, and aggregation behavior as adapter surfaces over OPE's internal API; do not redefine OPE forecast generation, evidence, resolution, scoring, or calibration semantics.
- [x] Add conformance guidance for the minimal OPP provider surface, while keeping hosted network listeners out of normal OPE checks unless explicitly enabled.
- [x] Document that OPP is optional interoperability and not a replacement for OPE's schema-bound lifecycle bundles, evidence traces, operation receipts, or claim-boundary gates.

Exit criteria:

- OPE has a clear adapter plan for speaking OPP without weakening OPE records or overclaiming protocol support.
- External agents can discover the planned OPE provider capabilities and receive a compact forecast response that points back to auditable OPE records.
- OPE docs remain clear that local MCP stdio is the tested current agent protocol, and OPP/HTTP support is future adapter work until implemented and checked.

Expected outputs:

- `spec/opp-provider-adapter.md`
- `spec/opp-provider-adapter.schema.json`
- `spec/fixtures/generated/opp-provider-adapter/ope-opp-provider-adapter.generated.json`
- `python3 scripts/ope.py opp-provider-adapter`
- `scripts/generate_opp_provider_adapter.py` and `scripts/check_opp_provider_adapter.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the optional OPP provider-adapter boundary

## Milestone 122: Persistent SQLite Path Policy

Status: Accepted.

Goal: decide when and how OPE may use a user-selected persistent SQLite path beyond checked ephemeral SQLite scenarios, while keeping normal checks ephemeral and making durable local state an explicit opt-in runtime choice.

Tasks:

- [x] Define a persistent SQLite path policy with caller approval, workspace root requirements, `.ope/state` allowlisting, path traversal blockers, symlink escape blockers, and credential-value rejection.
- [x] Define ready and blocked cases for ephemeral default, approved workspace path, missing approval, outside-workspace path, symlink escape, existing unmigrated JSON state, schema mismatch, missing backup, lock conflict, and read-only filesystem.
- [x] Define JSON-state migration as explicit `state.import_json` only, with dry-run, backup, receipt, content-hash, source-provenance, and no-history-rewrite requirements.
- [x] Define backup and lock guards for persistent local writes, including SQLite busy timeout, lifecycle lease alignment, and stale-lock recovery receipts.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks create no persistent database and do not read ignored live state.

Exit criteria:

- OPE can tell agents when a persistent local SQLite path is ready for explicit local write mode and when the agent must stop for safer input.
- Normal repository checks remain offline, non-mutating, and ephemeral for SQLite runtime validation.
- Persistent local state is not conflated with hosted runtime, Postgres execution, production database parsing, automatic migration, or stronger forecast-quality claims.

Expected outputs:

- `spec/persistent-sqlite-policy.md`
- `spec/persistent-sqlite-policy.schema.json`
- `spec/fixtures/generated/persistent-sqlite-policy/ope-persistent-sqlite-policy.generated.json`
- `python3 scripts/ope.py persistent-sqlite-policy`
- `scripts/generate_persistent_sqlite_policy.py` and `scripts/check_persistent_sqlite_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the opt-in persistent SQLite path policy

## Milestone 123: Lifecycle Operation Lease Policy

Status: Accepted.

Goal: decide which lifecycle operations require strict leases and which can rely on idempotency-only guards, while keeping the policy readback non-mutating and avoiding hosted/runtime lock-control claims.

Tasks:

- [x] Define a lifecycle lease policy over the fourteen checked lifecycle operations from the operation store.
- [x] Mark `campaign.create_run`, `forecast.create`, `resolution.record`, `score.create`, `evidence.append`, `pre_calibration.bind`, `method.apply`, `method.rollback`, and `state.import_json` as strict-lease operations.
- [x] Mark `forecast.recalculate`, `question.cancel`, `question.annul`, `record.archive`, and `record.redact` as idempotency-only operations.
- [x] Add conflict and replay cases that show no leases acquired, no operation receipts written, no immutable records written, and sanitized diagnostics only.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks and readbacks acquire no leases, write no state, expose no raw lock CRUD, and make no hosted-runtime or quality claims.

Exit criteria:

- OPE can tell agents which lifecycle writes need strict lease handling before explicit local mutation commands run.
- Retry-safe lifecycle operations have idempotency-only behavior with safe existing-readback or blocked terminal-state responses.
- The policy does not implement a hosted queue, Postgres runtime, raw lock-control API, physical delete path, forecast-history rewrite, or stronger forecast-quality claim.

Expected outputs:

- `spec/lifecycle-lease-policy.md`
- `spec/lifecycle-lease-policy.schema.json`
- `spec/fixtures/generated/lifecycle-lease-policy/ope-lifecycle-lease-policy.generated.json`
- `python3 scripts/ope.py lifecycle-lease-policy`
- `scripts/generate_lifecycle_lease_policy.py` and `scripts/check_lifecycle_lease_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the lifecycle operation lease policy

## Milestone 124: Runtime Transport Readiness Gate

Status: Accepted.

Goal: decide when OPE should introduce local HTTP, queue, hosted service, or OPP HTTP provider runtime behavior beyond current local surfaces, while keeping normal checks non-networked and non-mutating.

Tasks:

- [x] Define current runtime transport surfaces as in-process internal API, CLI, `agent-call`, and local MCP stdio.
- [x] Define future/deferred surfaces for local HTTP, queue adapter, hosted service runtime, and OPP HTTP provider behavior.
- [x] Add readiness criteria that distinguish local-readback readiness from hosted or HTTP runtime readiness.
- [x] Add blocked cases for normal-check HTTP servers, implicit hosted service startup, OPP HTTP endpoint requests, queue workers without readiness, credential values in records, default live fetches, and unbounded background daemons.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks start no listeners, hosted services, queues, OPP HTTP providers, live-fetch defaults, or unbounded background daemons.

Exit criteria:

- OPE can tell agents and contributors that the first embedded runtime remains in-process/CLI/agent-call/local MCP.
- Local HTTP, queue, hosted service, and OPP HTTP provider behavior remain blocked or deferred until explicit readiness criteria are met.
- The checked gate does not implement a network listener, hosted service, queue worker, payment settlement, credential storage, production live fetch, or stronger quality claim.

Expected outputs:

- `spec/runtime-transport-readiness.md`
- `spec/runtime-transport-readiness.schema.json`
- `spec/fixtures/generated/runtime-transport-readiness/ope-runtime-transport-readiness.generated.json`
- `python3 scripts/ope.py runtime-transport-readiness`
- `scripts/generate_runtime_transport_readiness.py` and `scripts/check_runtime_transport_readiness.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the runtime transport readiness gate

## Milestone 125: Workspace Tenant Isolation Policy

Status: Accepted.

Goal: decide how the multi-prediction workspace isolates resources, source bindings, operation queues, credential references, and idempotency namespaces across host application tenants or users while keeping the policy readback non-mutating.

Tasks:

- [x] Define tenant and workspace scope over the checked prediction workspace registry.
- [x] Add tenant-local workspace bindings with unique prediction IDs, source binding IDs, operation queue refs, idempotency namespace prefixes, resource policies, and credential scopes.
- [x] Define required scope keys for tenant, workspace, prediction, source binding, and operation idempotency namespace lookup and audit.
- [x] Add tenant resource controls for active predictions, queued operations, readback bytes, source bindings, and tick runtime budgets.
- [x] Add queue policies for active, due, blocked, failed, source-health, calibration, and track-record read models that block cross-tenant queue peeks and raw queue CRUD.
- [x] Add source-binding policies that block cross-tenant raw source reuse, require a new sanitized binding for target tenants, and keep credential values and raw private rows outside OPE records.
- [x] Add one accepted same-tenant read and blocked cases for cross-tenant prediction reads, cross-workspace source binding reuse, cross-tenant queue peeks, idempotency namespace collisions, foreign credential references, and unaudited admin overrides.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks write no state, implement no hosted tenant runtime, allow no cross-tenant reads, store no credential values or raw private rows, expose no raw CRUD, and make no stronger forecast-quality claims.

Exit criteria:

- OPE can tell agents how tenant/workspace scope should be applied before host software manages multiple tenants or users.
- Cross-tenant reads, source binding reuse, queue peeks, idempotency namespace collisions, foreign credential references, and unaudited admin overrides have explicit blocked readbacks.
- The checked policy does not implement hosted multitenancy, tenant admin APIs, raw CRUD, network listeners, credential storage, raw private row storage, cross-tenant queue scans, or quality-claim upgrades.

Expected outputs:

- `spec/workspace-tenant-isolation.md`
- `spec/workspace-tenant-isolation.schema.json`
- `spec/fixtures/generated/workspace-tenant-isolation/ope-workspace-tenant-isolation.generated.json`
- `python3 scripts/ope.py workspace-tenant-isolation`
- `scripts/generate_workspace_tenant_isolation.py` and `scripts/check_workspace_tenant_isolation.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for tenant-scoped workspace isolation

## Milestone 126: Domain/Source Field Policy

Status: Accepted.

Goal: decide which domain and source-binding fields are universal, which are domain-specific extensions, and which are blocked before OPE broadens private setup behavior, generated runtime types, or richer private-source parsing.

Tasks:

- [x] Define universal domain config fields for identity, question templates, horizons, resolution criteria, baseline method, accepted source roles, exclusion rules, sample thresholds, claim boundaries, and execution boundary.
- [x] Define universal source-binding fields for identity, binding mode, credential policy, source role bindings, pre-forecast checks, setup operations, configuration input boundary, execution boundary, next action, and summary.
- [x] Define domain-specific extension-safe fields for question parameters, role vocabulary, role-required fields, resolution prose, exclusion reason codes, horizon labels, baseline thresholds, and source-quality threshold values.
- [x] Define blocked fields for credential values, raw SQL query text, raw private rows, post-outcome forecast evidence, production quality claims, and hosted runtime flags.
- [x] Add source-kind field rules for fixture, local-file, source-adapter-output, API, and database bindings, including credential-reference requirements for private API/database bindings while blocking credential values and raw payload storage.
- [x] Add decision cases for accepted core fields, accepted extension fields, missing required fields, credential values, raw SQL fields, premature quality claims, and resolution-only outcome roles marked as forecast-time evidence.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks write no state, create no forecasts, read no private data, store no credential values, allow no raw SQL, perform no arbitrary private API/database parsing, implement no hosted runtime, generate no runtime types, and make no stronger forecast-quality claims.

Exit criteria:

- OPE can tell agents which domain/source fields must exist for every setup and which values stay inside domain-specific extension containers.
- Credential values, raw SQL, raw private rows, resolution-only evidence as forecast input, hosted runtime flags, and premature quality claims have explicit blocked readbacks.
- The checked policy does not execute private sources, create forecast artifacts, generate language-specific runtime types, implement hosted behavior, store credentials, store raw rows, or upgrade quality claims.

Expected outputs:

- `spec/domain-source-field-policy.md`
- `spec/domain-source-field-policy.schema.json`
- `spec/fixtures/generated/domain-source-field-policy/ope-domain-source-field-policy.generated.json`
- `python3 scripts/ope.py domain-source-field-policy`
- `scripts/generate_domain_source_field_policy.py` and `scripts/check_domain_source_field_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the domain/source field policy

## Milestone 127: Credential Reference Policy

Status: Accepted.

Goal: decide which credential-reference mechanism is acceptable for private APIs and databases without storing secrets in OPE records or resolving them during normal checks.

Tasks:

- [x] Define accepted reference mechanisms for caller secret-store aliases, host runtime secret handles, local operator session references, and public no-credential sources.
- [x] Define required scope keys for tenant, workspace, source binding, source role, adapter, source kind, source policy, and credential purpose.
- [x] Define credential lifecycle states for proposed, approved, active, rotation-due, revoked, and redaction-required references.
- [x] Define consumer rules for private API adapters, database adapters, source-binding validation, runtime readbacks, agent envelopes, and normal checks.
- [x] Add accepted and blocked policy cases for private API references, database references, public no-credential sources, missing references, raw tokens, password-bearing connection strings, cross-tenant reuse, unscoped references, adapter mismatches, revoked references, and normal-check resolution attempts.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks write no state, store no credential values, print no credential values, resolve no secrets, read no environment secrets, open no database connections, call no APIs, implement no hosted secret manager, and upgrade no quality claims.

Exit criteria:

- Private API and database setup can refer to credentials only through scoped opaque caller-owned references.
- Raw API tokens, passwords in connection strings, cross-tenant references, unscoped references, adapter mismatches, revoked references, and normal-check secret resolution have explicit blocked readbacks.
- The checked policy does not implement a secret resolver, secret store, hosted credential manager, database connection, API call, or production private-source runtime.

Expected outputs:

- `spec/credential-reference-policy.md`
- `spec/credential-reference-policy.schema.json`
- `spec/fixtures/generated/credential-reference-policy/ope-credential-reference-policy.generated.json`
- `python3 scripts/ope.py credential-reference-policy`
- `scripts/generate_credential_reference_policy.py` and `scripts/check_credential_reference_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the credential-reference policy

## Milestone 128: Retention Redaction Policy

Status: Accepted.

Goal: decide how OPE distinguishes audit-preserving tombstones and redaction receipts from rare physical deletion while preserving forecast lifecycle integrity, provenance, idempotency, and private-data boundaries.

Tasks:

- [x] Define retention classes for forecast lifecycle records, evidence traces, source connector results, source-binding configs, credential references, pilot summaries, local usage traces, and operation receipts.
- [x] Define policy actions for append-only retention, archive tombstones, redaction receipts, sanitized projection rebuilds, and physical-delete exception preflight.
- [x] Define physical-delete exception gates for erasure basis, tenant/workspace scope, record-class eligibility, legal or safety review, retained audit tombstone, retained redaction receipt, forecast-history integrity, and operator approval.
- [x] Add decision cases for normal lifecycle retention, inactive prediction archive, private source-detail redaction, credential-like redaction, pilot-summary redaction, usage aggregation, raw connector preview blocking, missing erasure basis, authorized erasure preflight, forecast-history physical-delete blocking, redaction replay, and tombstone read-model rebuild.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks write no state, physically delete no records, allow no silent delete, rewrite no forecast histories, retain no credential values, raw private rows, or raw pilot transcripts, implement no hosted erasure workflow, and upgrade no quality claims.

Exit criteria:

- OPE can tell agents when to retain records, archive with tombstones, redact with receipts, rebuild sanitized projections, or stop for physical-delete exception preflight.
- Physical deletion is blocked by default and requires every checked gate before any future effectful runtime can attempt it.
- Forecast lifecycle records are not physically deleted; affected forecasts must become explicitly unscorable rather than silently rewritten if required evidence is removed.

Expected outputs:

- `spec/retention-redaction-policy.md`
- `spec/retention-redaction-policy.schema.json`
- `spec/fixtures/generated/retention-redaction-policy/ope-retention-redaction-policy.generated.json`
- `python3 scripts/ope.py retention-redaction-policy`
- `scripts/generate_retention_redaction_policy.py` and `scripts/check_retention_redaction_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the retention/redaction policy

## Milestone 129: Private Auto-Evidence Policy

Status: Accepted.

Goal: decide which source-policy boundary governs `data: auto` in private engine setups without allowing broad private-source discovery, web search, secret resolution, raw SQL execution, raw payload retention, or hosted/runtime claims.

Tasks:

- [x] Define private `data: auto` source-kind policy rows for local files, manual mappings, auto-evidence connectors, sanitized source-adapter outputs, database query manifests, private API manifests, manual uploads, and web search.
- [x] Define required policy gates for domain config, source binding, source policy, tenant/workspace scope, caller approval, credential reference scope, adapter capability, freshness, retention, leakage checks, forecast-before-close timing, and non-effectful normal checks.
- [x] Add decision cases for approved local files, approved adapter outputs, database query manifests, private API manifests, manual mappings, manual upload blockers, missing credential references, raw SQL, private web search, cross-tenant binding, post-outcome forecast evidence, raw payload retention, and unregistered private connectors.
- [x] Add schema, fixture, generator, checker, CLI, release manifest, hardening, MVP smoke, docs, roadmap, and decision-log wiring.
- [x] Preserve the boundary that normal checks read no private sources, resolve no secrets, call no networks, write no state, allow no arbitrary web search, parse no arbitrary private API/database source, execute no raw SQL, retain no raw private payload, treat no post-outcome evidence as forecast evidence, implement no hosted runtime, generate no runtime types, and upgrade no quality claims.

Exit criteria:

- OPE can tell agents which private `data: auto` source kinds are policy-ready, manifest-only, planned, or blocked.
- Private API and database manifests can describe future runtime boundaries only through scoped credential references, source-policy bindings, freshness, retention, and adapter gates.
- Broad web search, raw SQL, raw private payload retention, post-outcome forecast evidence, cross-tenant source reuse, and unregistered private connectors have explicit blocked readbacks.

Expected outputs:

- `spec/private-auto-evidence-policy.md`
- `spec/private-auto-evidence-policy.schema.json`
- `spec/fixtures/generated/private-auto-evidence-policy/ope-private-auto-evidence-policy.generated.json`
- `python3 scripts/ope.py private-auto-evidence-policy`
- `scripts/generate_private_auto_evidence_policy.py` and `scripts/check_private_auto_evidence_policy.py`
- release, schema, hardening, CLI, documentation, decision-log, and normal-check wiring for the private auto-evidence policy

## Milestone 130: Agent Integration Question Discovery

Status: Accepted.

Goal: give agents one checked surface that validates and ranks forecastable candidate questions from app intent and approved source context.

Tasks:

- [x] Add `agent-integrate` readback with `summary`, `intake`, `candidates`, `validation`, `blocked`, `boundary`, `commands`, and `efficiency` views.
- [x] Define candidate statuses: `forecastable`, `needs_clarification`, `blocked`, and `rejected`.
- [x] Validate candidates against future boundary, resolvability, source policy, source roles, leakage, baseline feasibility, and claim boundary.
- [x] Reuse existing domain/source setup boundaries and normal forecast-card readbacks instead of creating a new forecast path.
- [x] Add schema, generated fixture, generator, checker, CLI, hardening, release, docs, roadmap, and decision-log wiring.

Exit criteria:

- `python3 scripts/ope.py agent-integrate --view candidates` returns forecastable and non-forecastable candidate contracts with exact reason codes.
- The Helsinki candidate is forecastable: `Will HSL surface transit exceed the beta delay threshold during morning peak on {service_date}?`
- Vague questions such as `Will transit be bad next week?` return `needs_clarification`.

Expected outputs:

- `spec/agent-integration.md`
- `spec/agent-integration.schema.json`
- `spec/fixtures/generated/agent-integration/ope-agent-integration.generated.json`
- `python3 scripts/ope.py agent-integrate --view candidates`
- `scripts/generate_agent_integration.py` and `scripts/check_agent_integration.py`

## Milestone 131: Helsinki Bus Disruption Starter Pack

Status: Accepted.

Goal: provide a reusable starter scenario for agents building Helsinki traffic apps.

Tasks:

- [x] Add `--scenario helsinki_bus_disruption` to `agent-integrate`.
- [x] Bind required source roles: `weather_forecast`, `historical_delay_baseline`, and `transit_delay_outcome`.
- [x] Use approved files and sanitized adapter outputs only.
- [x] Include source readiness, required fields, missing-field blockers, and resolution-only boundaries.
- [x] Keep HSL outcome evidence resolution-only.

Exit criteria:

- `python3 scripts/ope.py agent-integrate --scenario helsinki_bus_disruption` returns the ready starter pack.
- Missing weather, baseline, or outcome source roles produce clear blockers.
- No private rows, raw credentials, raw SQL, or unapproved live fetches are accepted.

## Milestone 132: Guided First Forecast Path

Status: Accepted.

Goal: let an agent reach a forecast card in no more than three OPE tool calls after approved sources are available.

Tasks:

- [x] Add `python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output`.
- [x] Reuse the checked source-adapter intake, source handoff, method gate, setup forecast, and normal forecast-card readback boundary.
- [x] Return `forecastId`, `questionId`, `forecastCardCommand`, and `lifecycleBundleCommand`.
- [x] Preserve normal claim warnings and the baseline-first method boundary.

Exit criteria:

- Accepted guided case returns a forecast-card read command for `forecast-1102` and `question-1102`.
- Blocked guided cases do not return forecast IDs or forecast-card commands.
- Guided output tells the agent exactly what to do next.

## Milestone 133: MCP Agent Integration Tools

Status: Accepted.

Goal: expose the same integration flow through local MCP stdio for agent hosts.

Tasks:

- [x] Add MCP/agent operations `ope_agent_integration_readiness`, `ope_agent_integration_candidates`, and `ope_agent_integration_guided_forecast`.
- [x] Preserve the same schema-bound readback through transport-neutral agent envelopes.
- [x] Update protocol map and MCP checks.
- [x] Keep credential, raw row, raw SQL, hidden live fetch, hosted runtime, and private-source execution boundaries blocked.

Exit criteria:

- MCP and CLI expose equivalent candidate, validation, and guided forecast outputs.
- MCP tools do not expose credentials, raw source rows, hidden live fetches, hosted runtime behavior, or private-source execution.

## Milestone 134: Agent Incorporation Efficiency Gate

Status: Accepted.

Goal: measure whether OPE is easier than an agent building the forecast workflow itself.

Tasks:

- [x] Add efficiency metrics to the integration readback: OPE tool call count, elapsed local readback time, decisions avoided, forecast-card success status, and blockers encountered.
- [x] Add local usage trace rows for the Helsinki starter flow.
- [x] Add release-surface checks that report whether the first-forecast-fast target is met.
- [x] Keep calibration, quality, hosted, and production-readiness claims blocked below thresholds.

Exit criteria:

- Release surface reports whether the starter flow reaches a forecast-card command in no more than three routine agent tool calls.
- Usage trace shows why a flow failed, including missing source, ambiguous question, unsafe source, leakage, or unsupported runtime categories.
- No quality, calibration, hosted, or production-readiness claims are upgraded.

## Milestone 135: Agent Implementation Kit Front Door

Status: Accepted.

Goal: make the agent implementation kit the canonical starting point for coding agents adding an OPE-backed prediction feature to another project.

Tasks:

- [x] Promote `spec/agent-implementation-kit.md` and `python3 scripts/ope.py agent-implementation-kit` as the first external-agent adoption path in README, product, and developer-adoption surfaces.
- [x] Add a compact `quickstart` view that returns the minimum safe sequence from host feature intent to forecast-card readback.
- [x] Add a copyable local wrapper outline that calls candidate discovery, validation, guided forecast, and forecast-card readback through existing OPE surfaces.
- [x] Cross-link the quickstart to `agent-integrate`, `developer-adoption`, `mvp-local-runtime`, and MCP stdio docs without duplicating long runbooks.
- [x] Preserve the boundary that this milestone does not add a new forecast path, hosted service, live-source behavior, raw credential handling, raw row handling, raw SQL, generated runtime types, or stronger quality claims.

Exit criteria:

- A fresh coding agent can identify the first OPE command for implementing a prediction feature without reading the full roadmap or spec index.
- `python3 scripts/ope.py agent-implementation-kit --view quickstart` returns a compact, machine-readable path to a forecast-card command.
- The quickstart explains blocked outcomes with reason codes and next actions instead of free-form advice.

Expected outputs:

- Updated `spec/agent-implementation-kit.md`
- Updated `spec/developer-adoption-surface.md`
- Updated `README.md` and `PRODUCT.md` references if needed
- Updated generated agent implementation kit fixture and checker
- `python3 scripts/ope.py agent-implementation-kit --view quickstart`

## Milestone 136: Fast Agent Smoke Check

Status: Accepted.

Goal: give external agents a fast, visible confidence check for the adoption path before they run the full local release surface.

Tasks:

- [x] Add `python3 scripts/ope.py smoke` as the first short validation command for agent adoption.
- [x] Run only the essential adoption checks: schema sanity needed for the path, developer adoption check, agent implementation kit check, agent-integrate candidates, guided accepted forecast, and forecast-card read.
- [x] Emit progress messages before each smoke step so long-running checks are not silent.
- [x] Return a compact JSON or text summary with pass/fail status, elapsed time, failed step, and next command.
- [x] Keep `python3 scripts/ope.py check` as the comprehensive check and document when agents should use each command.
- [x] Preserve the boundary that smoke writes no state, performs no live fetches, creates no forecasts beyond existing checked fixture readbacks, and upgrades no quality claims.

Exit criteria:

- `python3 scripts/ope.py smoke` completes quickly on a normal checkout and shows progress.
- A failed smoke run tells an agent the exact failed step and whether to rerun `agent-implementation-kit`, `agent-integrate`, or the full check.
- The full check remains available for release readiness.

Expected outputs:

- Updated `scripts/ope.py`
- Smoke helper/checker code following existing script patterns
- Updated `spec/mvp-local-runtime.md`
- Updated `spec/developer-adoption-surface.md`
- Release manifest and hardening wiring for the new smoke surface

## Milestone 137: Stable Prediction Feature Contract

Status: Accepted.

Goal: give host projects one compact machine contract for prediction-feature setup instead of requiring agents to compose many repo-specific commands.

Tasks:

- [x] Define a `prediction-feature-setup-request` contract for host feature intent, allowed source references, forecast decision context, resolution hints, and response-size budget.
- [x] Define a `prediction-feature-setup-response` contract that returns candidates, validation results, blocker codes, required source roles, next actions, and forecast-card/lifecycle-bundle commands when available.
- [x] Bind the response to existing candidate discovery, validation, guided forecast, and readback surfaces rather than creating a separate execution path.
- [x] Add CLI and `agent-call` operations for the compact contract.
- [x] Add local MCP guidance for the same contract if it fits the existing stdio tool boundary.
- [x] Preserve the boundary that the contract accepts no credential values, raw private rows, raw SQL, hidden live fetch requests, hosted runtime flags, or private-source execution instructions.

Exit criteria:

- An external agent can submit one prediction-feature setup request and decide whether to proceed, clarify, block, reject, or read a forecast card.
- The response is small enough for routine agent tool context and has exact reason codes for non-accepted outcomes.
- The contract reuses existing OPE records and does not create a new forecast artifact path.

Expected outputs:

- `spec/prediction-feature-setup.md`
- `spec/prediction-feature-setup-request.schema.json`
- `spec/prediction-feature-setup-response.schema.json`
- Generated fixtures for accepted, needs-clarification, blocked, rejected, and response-too-large cases
- CLI, `agent-call`, checker, release, docs, and hardening wiring

## Milestone 138: Copyable Host Integration Example

Status: Accepted.

Goal: show another project how to embed OPE locally as a prediction feature without treating OPE as a hosted service or generic oracle.

Tasks:

- [x] Add `examples/embed-ope-prediction-feature/` with a minimal host wrapper.
- [x] Include a README that explains the local sequence from host feature intent to forecast-card readback.
- [x] Include sample approved source references and expected JSON outputs.
- [x] Include blocked examples for raw credentials, raw private rows, raw SQL, unapproved sources, post-outcome evidence, and hosted-runtime assumptions.
- [x] Use the stable prediction-feature setup contract when Milestone 137 is available; otherwise route through the existing `agent-integrate` and forecast-card readback commands.
- [x] Preserve the boundary that the example stores no credentials, exposes no network listener, starts no hidden worker, and creates no production forecast-quality claim.

Exit criteria:

- A coding agent can copy the example into a host app and understand which OPE calls to make.
- The example demonstrates both a successful local forecast-card path and at least one blocked unsafe path.
- The example remains dependency-light and does not require a package install beyond the repository's current local runtime assumptions.

Expected outputs:

- `examples/embed-ope-prediction-feature/README.md`
- `examples/embed-ope-prediction-feature/host_wrapper.py`
- `examples/embed-ope-prediction-feature/fixtures/`
- Example smoke/check command wired into local checks if feasible

## Milestone 139: MCP Adoption Path Fixtures

Status: Accepted.

Goal: make the local MCP stdio adoption path as clear and testable as the CLI path for MCP-capable agent hosts.

Tasks:

- [x] Document the minimal MCP tool sequence for readiness, candidate discovery, guided forecast, and forecast-card readback.
- [x] Add transcript fixtures for a successful forecast-card path.
- [x] Add transcript fixtures for blocked unsafe cases, including credential value, raw SQL, private row exposure, unapproved source, and response-too-large.
- [x] Check that MCP tool outputs match the equivalent CLI/agent-call envelope semantics for the adoption path.
- [x] Keep MCP arguments selector-only and compact; do not accept raw source payloads, secrets, SQL, hidden live fetches, hosted runtime behavior, or private-source execution.

Exit criteria:

- An MCP-capable host can expose OPE adoption tools without guessing call order or accepted arguments.
- Success and blocked transcripts are schema-bound and checked.
- MCP readbacks remain equivalent to CLI/agent-call readbacks for the same adoption cases.

Expected outputs:

- Updated `spec/agent-adapter-protocol-map.md`
- Updated `spec/agent-integration.md`
- MCP adoption transcript fixtures
- Updated MCP checker and release wiring

## Milestone 140: Real Agent Pilot Evidence Loop

Status: Partially accepted with agent-only simulation; real supervised sessions still pending.

Goal: validate the adoption path with supervised real agent/developer sessions before broadening runtime or packaging claims.

Tasks:

- [x] Run five user-authorized simulated agent sessions using one user-provided prompt and four generated prompts.
- [x] Count approximate prompt/response tokens and deterministic elapsed-time estimates for the simulated sessions.
- [x] Cover accepted, needs-clarification, blocked, rejected, and response-too-large prediction-feature setup outcomes.
- [ ] Run 3-5 real supervised local pilot sessions using the checked pilot session packet.
- [ ] Collect sanitized real-session summaries through `pilot-summary-intake` before anything is counted as real evidence.
- [x] Add a checked pilot findings readback that reports session count, task success, confusion points, blocked-path comprehension, forecast-card trust, and next improvement candidates.
- [x] Keep raw transcripts, private data, credentials, and host-project secrets out of committed records.
- [x] Update adoption metrics only with sanitized, ledger-ready summaries.
- [x] Preserve the boundary that pilot evidence may improve adoption claims but does not upgrade forecast quality, calibration, hosted runtime, live-source production use, or method-performance claims.

Exit criteria:

- The repo can report how many real adoption sessions were run and what friction they exposed.
- The repo can separately report simulated agent-session friction without counting it as real adoption evidence.
- Sanitized pilot summaries distinguish successful completion, clarification-needed, blocked unsafe path, and abandoned setup cases.
- The next adoption milestone is chosen from observed friction, not speculation.

Expected outputs:

- `spec/pilot-findings.md`
- `spec/pilot-findings.schema.json`
- `spec/simulated-agent-pilot.md`
- `spec/simulated-agent-pilot.schema.json`
- Generated simulated agent pilot fixture
- Generated sanitized pilot findings fixture
- CLI/checker wiring for `python3 scripts/ope.py simulated-agent-pilot`
- CLI/checker wiring for `python3 scripts/ope.py pilot-findings`
- Updated `spec/pilot-evidence-ledger.md` and `spec/local-usage-trace.md` as needed

## Milestone 141: Generated Runtime Types Decision

Status: Accepted.

Goal: decide whether generated language-specific runtime types are necessary for external agent adoption, and if so start with the compact adoption contracts.

Tasks:

- [x] Review pilot findings, smoke failures, and adoption traces for type-related friction.
- [x] Decide whether to generate TypeScript, Python, both, or neither for the compact adoption contracts.
- [x] If generating types, scope the first generator to the prediction-feature setup request/response and forecast-card readback surfaces only.
- [x] If deferring types, document the stable JSON examples and validator commands agents should use instead.
- [x] Add a generated-types decision record with rationale, scope, blocked broader generation cases, and follow-up gates.
- [x] Preserve the boundary that generated types do not imply hosted runtime, SDK stability for the entire spec package, production source parsing, or broader quality claims.

Exit criteria:

- The roadmap has a clear generated-types decision based on adoption evidence.
- If types are accepted, the first type surface is narrow, checked, and tied to external-agent adoption.
- If types are deferred, host agents still have stable JSON examples and validation commands.

Expected outputs:

- `spec/generated-runtime-types-decision.md`
- Optional generated TypeScript/Python files for compact adoption contracts
- Checker for generated type drift if types are accepted
- Updated developer adoption and agent implementation kit docs

## Milestone 142: Agent Guidance Contract

Status: Accepted.

Goal: give calling agents a compact OPE readback that classifies messy prediction-feature prompts and returns the next safe move.

Tasks:

- [x] Define a checked `agent-guidance` contract with accepted, needs-clarification, blocked, rejected, and response-too-large cases.
- [x] Return `agentNextMove`, reason codes, required source roles, safe commands, and claim boundaries for each case.
- [x] Bind guidance to the existing prediction-feature setup and simulated pilot records rather than creating a new forecast path.
- [x] Add CLI, checker, schema, fixture, docs, release, and hardening wiring.
- [x] Preserve the boundary that guidance readbacks do not execute sources, fetch live data, create forecast artifacts, or upgrade quality claims.

Exit criteria:

- A calling agent can ask OPE what to do next for each compact prediction-feature setup outcome.
- Accepted guidance routes to existing forecast-card/lifecycle readbacks.
- Non-accepted guidance stops at a concrete question, replacement step, rewrite, or scope/budget action.

Expected outputs:

- `spec/agent-guidance.md`
- `spec/agent-guidance.schema.json`
- Generated agent guidance fixture
- CLI/checker wiring for `python3 scripts/ope.py agent-guide`

## Milestone 143: Prompt-to-Question Planner

Status: Accepted.

Goal: turn a broad developer prompt into the focused clarification questions a capable calling agent should ask.

Tasks:

- [x] Add a prompt planner section to `agent-guidance`.
- [x] Allow bounded raw prompt text while explicitly blocking credential values, raw private rows, and raw SQL.
- [x] Return four Helsinki bus clarification questions covering route/stop/scope, time window, planned-work source ref, and outcome source.
- [x] Return required source roles and a safe retry command after clarification.
- [x] Keep the planner read-only and non-effectful.

Exit criteria:

- The planner tells an external agent what to ask next instead of forcing the agent to infer OPE's missing setup fields.
- The planner distinguishes useful prompt text from unsafe source payloads.

Expected outputs:

- `agent-guide --section planner`
- Checker coverage in `scripts/check_agent_guidance.py`

## Milestone 144: Helsinki Bus Narrowing Flow

Status: Accepted.

Goal: make the user's Helsinki bus prompt a checked narrowing example from broad natural language to scoped forecast setup.

Tasks:

- [x] Normalize the broad prompt horizon to `2026-06-06`.
- [x] Keep the broad prompt classified as `needs_clarification`.
- [x] Add a clarified example that supplies route/stop/window/source refs.
- [x] Route the clarified example toward the accepted prediction-feature setup case.
- [x] Preserve the boundary that this is guidance only, not route-level forecast execution.

Exit criteria:

- Agents can see exactly why the broad Helsinki prompt is not ready.
- Agents can see the minimum shape that would make the prompt routable.

Expected outputs:

- `agent-guide --section helsinki`
- `agent-guide --case needs_clarification`

## Milestone 145: Agent Instruction Pack

Status: Accepted.

Goal: document the minimum safe loop for external agents using OPE as a prediction-feature guide.

Tasks:

- [x] Add do/don't rules for classification, clarification, approved source refs, forecast-card reads, and claim boundaries.
- [x] Add a minimum loop: classify prompt, ask or block, retry with refs, then read or stop.
- [x] Include safe commands for each loop step where a command exists.
- [x] Keep instructions aligned with OPE boundaries: no secrets, raw rows, raw SQL, hosted runtime claims, or quality overclaims.

Exit criteria:

- External agents have a compact instruction surface without reading the full spec package.
- The instruction pack teaches agents to use their own intelligence while letting OPE provide rails.

Expected outputs:

- `agent-guide --section instructions`
- README, PRODUCT, release, CLI, and hardening coverage

## Milestone 146: Domain-Agnostic Engine Setup Front Door

Status: Accepted.

Goal: make the first agent-facing OPE path explain how OPE helps set up a reliable prediction engine for any host prediction goal, not only how OPE audits a prediction feature after another engine exists.

Tasks:

- [x] Reframe the adoption language from "prediction credibility layer" alone to "engine setup shortcut with credibility built in."
- [x] Define the canonical first question OPE answers for agents: "Given this host prediction goal and source constraints, what OPE-compatible prediction engine can be set up safely?"
- [x] Add a planned `setup-engine` readback shape that returns candidate forecast contracts, required source roles, baseline method guidance, enabled method extension points, forecast-card shape, resolver/scorer loop, calibration gate, and host responsibilities.
- [x] Keep the readback domain-agnostic by using generic setup fields and example-specific extension containers rather than transit-specific fields.
- [x] Preserve non-goals: no frontend, no hosted service claim, no generic crawler, no trained model claim, no raw secrets, no raw SQL, no raw private rows, and no quality claim before resolved evidence.

Exit criteria:

- A coding agent can understand within one compact readback that OPE can set up the first safe prediction engine skeleton.
- The readback makes clear what OPE creates or validates versus what the host app still provides.
- The front door does not require the agent to understand Helsinki, weather-logistics, or any other reference wedge first.

Expected outputs:

- Updated `AGENT_QUICKSTART.md`
- Updated `README.md`
- Updated `PRODUCT.md`
- Updated `ope.capabilities.json`
- Planned spec for the engine setup readback
- Roadmap and release-surface notes for the claim-boundary change

## Milestone 147: Setup-Engine CLI And Adapter Readbacks

Status: Accepted.

Goal: expose the domain-agnostic engine setup shortcut through the same checked local surfaces agents already use.

Tasks:

- [x] Add `python3 scripts/ope.py setup-engine --goal "<host prediction goal>"` as the preferred compact first command for new prediction-engine setup.
- [x] Add focused views for `contracts`, `sources`, `baseline`, `host-wrapper`, `claim-boundary`, and `examples`.
- [x] Add `agent-call` and local MCP readbacks for the same setup-engine operation without accepting raw source payloads, credentials, raw SQL, live fetch instructions, or hosted-runtime requests.
- [x] Return a stable JSON shape that a host wrapper can render before any forecast artifacts exist.
- [x] Keep the existing `explain-fit`, `capabilities`, `agent-implementation-kit`, and `prediction-feature-setup` surfaces as compatible aliases or follow-up paths rather than competing front doors.

Exit criteria:

- Agents have one obvious first command for setting up an OPE-backed prediction engine.
- CLI, `agent-call`, and MCP outputs agree on statuses, reason codes, and blocked-path semantics.
- The operation is read-only and non-effectful until a later explicit setup or forecast command is chosen.

Expected outputs:

- `spec/setup-engine.md`
- `spec/setup-engine.schema.json`
- Generated setup-engine fixtures
- CLI/checker wiring for `python3 scripts/ope.py setup-engine`
- Agent adapter and MCP fixture updates
- README, quickstart, capabilities, release-manifest, and hardening updates

## Milestone 148: Generic Prediction Goal Catalog

Status: Accepted.

Goal: show agents that OPE's setup loop applies across domains before they see any Helsinki-specific example.

Tasks:

- [x] Add a compact catalog of generic host goals such as delivery delay risk, stockout risk, SLA breach risk, demand risk, churn risk, seaport berth availability, weather-sensitive operations, and public transit disruption risk.
- [x] For each example, classify the output as forecastable, needs-clarification, blocked, or rejected using the same reason-code vocabulary as the setup-engine front door.
- [x] For each forecastable or needs-clarification example, list required source roles, baseline candidate, resolution source, forecast-card fields, and the first safe host action.
- [x] Keep examples small and non-authoritative; they teach setup shape, not broad domain quality.
- [x] Move Helsinki transit language into the catalog as one example rather than the default adoption narrative.

Exit criteria:

- External agents can see the reusable pattern across several domains without reading the full spec package.
- The examples help agents map their own app goal to OPE setup fields instead of inventing a parallel risk engine.
- The catalog does not imply OPE has calibrated performance in any domain without resolved evidence.

Expected outputs:

- `spec/prediction-goal-catalog.md`
- `spec/prediction-goal-catalog.schema.json`
- Generated catalog fixture
- CLI/checker wiring for a focused setup-engine examples view
- Updated quickstart and implementation kit links

## Milestone 149: Host App Wrapper Guidance For Engine Setup

Status: Accepted.

Goal: make the output of setup-engine immediately usable by host-app builders without turning OPE into the host app.

Tasks:

- [x] Update the embedded host example so it starts from setup-engine and renders the returned engine setup plan before reading any forecast card.
- [x] Show the host-facing data shape for setup status, candidate contracts, source roles, baseline status, forecast-card preview, required host inputs, and warnings.
- [x] Include blocked examples for missing source roles, vague outcomes, credential values, raw SQL, raw private rows, post-outcome evidence, and requests for hosted runtime.
- [x] Keep the host wrapper thin: it should call OPE, render readbacks, and pass approved source references, not implement OPE scoring or calibration semantics itself.
- [x] Document how a host app can later plug in a custom forecast method as an OPE method extension instead of building an untracked route-risk engine.

Exit criteria:

- A coding agent building any host app can see where OPE ends and the host app begins.
- The example nudges agents to implement app-specific prediction logic as OPE-compatible methods or adapters.
- The wrapper guidance stays domain-agnostic and does not depend on Helsinki route-risk fields.

Expected outputs:

- Updated `examples/embed-ope-prediction-feature/README.md`
- Optional new `examples/setup-engine-host-wrapper/` if the existing example becomes too crowded
- Updated developer adoption surface
- Updated agent implementation kit quickstart

## Milestone 150: Engine Setup Adoption Comprehension Gate

Status: Accepted.

Goal: measure whether external agents understand OPE as the shortcut for setting up the first reliable prediction engine before they choose to build an ad hoc risk engine.

Tasks:

- [x] Add simulated and real pilot prompts that are not Helsinki-specific.
- [x] Measure whether agents run setup-engine or equivalent OPE setup readbacks before proposing a separate lightweight prediction engine.
- [x] Record confusion signals when agents describe OPE only as an audit framework, reference repo, or post-hoc credibility layer.
- [x] Add success criteria for agents explaining that OPE supplies the contract, evidence roles, baseline, forecast-card shape, resolver, scorer, and calibration gate while the host supplies UI, sources, runtime, and optional custom methods.
- [x] Keep adoption evidence separate from forecast-quality evidence.

Exit criteria:

- Pilot findings can report whether the new front door changes agent behavior.
- The next adoption milestone is based on observed comprehension gaps, not intuition.
- OPE still avoids quality, hosted-runtime, source-execution, and method-performance overclaims.

Expected outputs:

- Updated `spec/agent-pilot-validation.md`
- Updated `spec/simulated-agent-pilot.md`
- Updated `spec/pilot-findings.md`
- Updated local usage trace readbacks
- Updated `adoption-eval` or setup-engine smoke coverage

Accepted implementation:

- `simulated-agent-pilot` now reports eight simulated sessions, including retail stockout, support SLA breach, and seaport berth availability setup-comprehension prompts.
- `agent-pilot-validation` and `pilot-session-packet` now include an `engine_setup_shortcut_comprehension` real-session task card.
- `pilot-findings` now reports non-Helsinki simulated-session count, setup-engine-first rate, parallel-risk-engine proposal count, and audit-layer-only confusion count while keeping real-session evidence at zero.
- `local-usage-trace` now includes setup-comprehension events and a setup-engine-first product metric.
- `adoption-eval` now includes setup-engine-before-parallel-risk-engine and audit-layer-only framing checks.

## Milestone 151: Pilot Summary File Intake Classifier

Status: Accepted.

Goal: let a moderator classify caller-supplied sanitized pilot summaries after real supervised sessions without writing ledger rows or counting real evidence automatically.

Tasks:

- [x] Add schema-bound sanitized summary input and classification result shapes.
- [x] Add checked accepted and blocked sample summary submissions for setup-engine comprehension.
- [x] Add `python3 scripts/ope.py pilot-summary-intake --input <summary.json>` to classify one sanitized summary file.
- [x] Preserve the boundary that file classification is read-only, records zero real sessions, writes zero ledger rows, stores no raw transcripts/private data/credentials/prompt logs/participant identity, and does not unblock expansion or quality claims.
- [x] Wire focused checks, CLI smoke coverage, release manifest, docs, roadmap, and decision log.

Exit criteria:

- A moderator can classify a sanitized real-session summary file as candidate real-session evidence, redaction-needed, or blocked before any manual ledger review.
- Accepted input classification does not itself count as real pilot evidence.
- Raw transcript or unsafe input signals are blocked before repository storage.

Expected outputs:

- `spec/pilot-summary-submission.schema.json`
- `spec/pilot-summary-intake-result.schema.json`
- sample sanitized summary fixtures under `spec/fixtures/pilot-summary-intake/`
- `python3 scripts/ope.py pilot-summary-intake --input spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json`
- checker, CLI, MVP release-surface, docs, release-manifest, roadmap, and decision-log wiring for read-only file classification

## Milestone 152: Supervised Pilot Local Evidence Ledger Runtime

Status: Accepted.

Goal: let a moderator turn approved sanitized real-session summaries into ignored local pilot evidence without committing real-session rows or changing normal check behavior.

Tasks:

- [x] Add a schema-bound dry-run append plan for `python3 scripts/ope.py pilot-evidence --input-summary <summary.json>`.
- [x] Require explicit `--write-local` before any accepted sanitized summary is appended to `.ope/live/pilot-evidence/pilot-evidence-ledger.json`.
- [x] Keep the append path idempotent by source summary ID so repeated writes do not duplicate real-session evidence.
- [x] Add `pilot-evidence --from-local-ledger` and `pilot-findings --from-local-ledger` readbacks for ignored local pilot evidence.
- [x] Preserve normal-check behavior: checked fixtures still report zero accepted real sessions and do not inspect ignored local state by default.
- [x] Preserve safety boundaries: no raw transcripts, private rows, credential values, prompt logs, participant identity, forecast artifacts, hosted runtime, expansion, quality-claim, or calibration-claim upgrades.
- [x] Wire focused checks, CLI smoke coverage, MVP release-surface checks, release manifest, docs, roadmap, and decision log.

Exit criteria:

- A moderator can run a read-only append plan after `pilot-summary-intake --input <summary.json>` accepts a sanitized summary.
- A moderator can explicitly append that summary to ignored local state only after review.
- Pilot findings can count ignored local accepted real sessions only when `--from-local-ledger` is explicitly requested.
- Checked examples and normal CI still count zero real sessions.

Expected outputs:

- `spec/pilot-evidence-local-append.schema.json`
- `spec/pilot-evidence-local-readback.schema.json`
- `python3 scripts/ope.py pilot-evidence --input-summary spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json`
- `python3 scripts/ope.py pilot-evidence --input-summary <summary.json> --write-local`
- `python3 scripts/ope.py pilot-findings --from-local-ledger --section summary`
- checker, CLI, MVP release-surface, docs, release-manifest, roadmap, and decision-log wiring for ignored local pilot evidence

## Milestone 153: Pilot Evidence Lifecycle Operation Coverage

Status: Accepted.

Goal: make the explicit ignored-local pilot evidence write path visible to the same lifecycle operation store agents use for campaign writes.

Tasks:

- [x] Add a checked `pilot-evidence-append` SQLite runtime scenario for `evidence.append`.
- [x] Store the pilot evidence row as `pilot_evidence_ledger_row` through the immutable evidence ledger table with payload hash binding.
- [x] Add `pilot_findings` as the read model updated by pilot evidence appends.
- [x] Keep pilot evidence appends from updating `append_readiness`, `calibration_status`, or `track_record_progress`.
- [x] Add write-local coverage and file/database idempotent replay coverage for `pilot-evidence --input-summary --write-local`.
- [x] Extend the ignored `.ope/live` JSON compatibility adapter to include `.ope/live/pilot-evidence/pilot-evidence-ledger.json`.
- [x] Regenerate the lifecycle operation store fixture and update docs, schema, roadmap, and decision log.

Exit criteria:

- Agents can inspect `lifecycle-operation-store --scenario pilot-evidence-append` to see the receipts, lease, idempotency, planned writes, read-model effects, and claim boundary for local pilot evidence writes.
- The lifecycle coverage proves pilot evidence is adoption/product evidence only and does not become forecast-quality, calibration, or track-record evidence.
- Normal checks remain non-mutating and do not read ignored local pilot ledgers by default.

Expected outputs:

- `spec/lifecycle-operation.schema.json`
- `spec/lifecycle-operation-store.md`
- `spec/fixtures/generated/lifecycle-operation-store/ope-lifecycle-operation-store.generated.json`
- `python3 scripts/ope.py lifecycle-operation-store --scenario pilot-evidence-append`
- checker, schema, generated fixture, docs, roadmap, and decision-log wiring for pilot evidence lifecycle coverage

## Milestone 154: Supervised Pilot Operator Status

Status: Accepted.

Goal: give agents and moderators a checked, read-only operator status for collecting the next real supervised pilot sessions without fabricating evidence or hiding the local write boundary.

Tasks:

- [x] Add a schema-bound `pilot-supervision-status` readback that joins the pilot session packet, pilot findings, ignored-local evidence mode, and remaining real-session thresholds.
- [x] Recommend the `engine_setup_shortcut_comprehension` task so real sessions test whether agents use OPE setup-engine before inventing a parallel lightweight risk engine.
- [x] Show the safe command sequence from task packet to `agent-guide`, `pilot-summary-intake --input`, explicit `pilot-evidence --input-summary --write-local`, `pilot-findings --from-local-ledger`, and status review.
- [x] Keep the status read-only: it does not run sessions, write checked fixtures, append ignored local evidence, store raw/private data, or upgrade expansion, quality, calibration, hosted-runtime, or generated-type claims.
- [x] Add CLI, schema coverage, generated fixture, checker, release-surface smoke coverage, docs, roadmap, and decision-log wiring.

Exit criteria:

- Agents can run `python3 scripts/ope.py pilot-supervision-status --section summary` to see zero checked real sessions, three remaining minimum sessions, five remaining target sessions, and the recommended setup-comprehension task.
- Agents can run `python3 scripts/ope.py pilot-supervision-status --section commands` to see the full local pilot evidence command loop.
- Agents can run `python3 scripts/ope.py pilot-supervision-status --from-local-ledger --section summary` to include ignored local evidence only when explicitly requested.
- Normal checks remain non-mutating and do not inspect ignored local pilot ledgers by default.

Expected outputs:

- `spec/pilot-supervision-status.schema.json`
- `spec/pilot-supervision-status.md`
- `spec/fixtures/generated/pilot-supervision-status/ope-pilot-supervision-status.generated.json`
- `python3 scripts/ope.py pilot-supervision-status`
- checker, schema, generated fixture, docs, roadmap, and decision-log wiring for supervised pilot operator status

## Milestone 155: Sanitized Pilot Summary Template

Status: Accepted.

Goal: give operators a checked summary draft shape for real supervised pilot sessions without making unchanged placeholders count as evidence.

Tasks:

- [x] Add a schema-bound `pilot-summary-template` readback that joins the pilot session packet, summary-intake contract, evidence ledger, and supervision status.
- [x] Emit a schema-valid `draftSubmission` for the recommended setup-comprehension task.
- [x] Make the unchanged draft classify as `needs_redaction`, with no dimension ratings and `unredactedSourceDetailDetected` true, so it cannot be appended as real evidence by accident.
- [x] Include field guidance, sanitization checklist, and a command sequence from draft print to `pilot-summary-intake --input`, explicit `pilot-evidence --input-summary --write-local`, and supervision status review.
- [x] Keep the template read-only: it does not run sessions, write checked fixtures, append ignored local evidence, store raw/private data, or upgrade expansion, quality, calibration, hosted-runtime, or generated-type claims.
- [x] Add CLI, schema coverage, generated fixture, checker, release-surface smoke coverage, docs, roadmap, and decision-log wiring.

Exit criteria:

- Agents can run `python3 scripts/ope.py pilot-summary-template --section draft` to get a schema-valid draft summary for local operator editing.
- The unchanged draft classifies as `needs_redaction` and is not ledger-ready.
- Agents can run `python3 scripts/ope.py pilot-summary-template --section commands` to see the classify and explicit local append sequence.
- Normal checks remain non-mutating and do not inspect or write ignored local pilot ledgers by default.

Expected outputs:

- `spec/pilot-summary-template.schema.json`
- `spec/pilot-summary-template.md`
- `spec/fixtures/generated/pilot-summary-template/ope-pilot-summary-template.generated.json`
- `python3 scripts/ope.py pilot-summary-template`
- checker, schema, generated fixture, docs, roadmap, and decision-log wiring for sanitized pilot summary templates

## Milestone 156: Domain-Agnostic Agent Guidance Flow

Status: Accepted.

Goal: make `agent-guide` useful in supervised adoption sessions for any host prediction goal, not only the Helsinki transit example.

Tasks:

- [x] Add a schema-bound domain-agnostic setup flow to `agent-guidance` with reusable decision, outcome, horizon, source, baseline, and resolution questions.
- [x] Update the prompt planner so its default questions are generic setup questions rather than Helsinki-specific narrowing questions.
- [x] Keep the Helsinki bus guidance as one checked narrowing example instead of the default adoption path.
- [x] Add `python3 scripts/ope.py agent-guide --section generic` and protect it with CLI, MVP release-surface, schema, generated-fixture, and focused checker coverage.
- [x] Preserve the read-only boundary: no source execution, forecast artifact creation, raw private data storage, hosted runtime, or quality/calibration claim upgrades.
- [x] Update docs, roadmap, release-manifest wording, and decision log.

Exit criteria:

- Agents can run `python3 scripts/ope.py agent-guide --section generic` to get reusable setup questions for arbitrary host prediction goals.
- Agents can still run `python3 scripts/ope.py agent-guide --case needs_clarification` for the Helsinki worked example.
- The summary advertises both the generic setup flow and the Helsinki example.
- Normal checks remain non-mutating and do not count simulated or template guidance as real pilot evidence.

Expected outputs:

- Updated `spec/agent-guidance.schema.json`
- Updated `spec/agent-guidance.md`
- Updated generated `agent-guidance` fixture
- `python3 scripts/ope.py agent-guide --section generic`
- checker, CLI, MVP release-surface, docs, release-manifest, roadmap, and decision-log wiring for domain-agnostic agent guidance

## Open Decisions

- What is the minimum domain-agnostic setup-engine input shape: goal text only, or goal plus decision context, source hints, horizon, and resolution hints?
- Should `setup-engine` become the canonical first command, or should it be an alias layered over `agent-implementation-kit` and `prediction-feature-setup` until real pilot evidence confirms the naming?
- How should setup-engine rank candidate contracts without implying forecast quality before resolved outcomes exist?
- What fields are safe and useful in a forecast-card preview before any forecast artifact exists?
- What is the smallest domain setup contract that remains useful across private operational domains?
- What minimum app-goal, decision, source, and resolution-hint fields are required before OPE can answer "what can be forecasted from these approved sources?"
- How much candidate question synthesis should OPE core perform from structured inputs and setup templates versus leaving to the caller's agent or an optional labeled helper agent?
- Should candidate forecast contract confidence be represented separately from source quality and mapping confidence, or derived from those existing gates?
- Which source-manifest and mapping format should agents use for local files, APIs, and databases?
- How should OPE represent agent-inferred mappings without treating them as verified facts?
- What is the smallest approved database query-manifest shape that is useful to coding agents without allowing arbitrary raw SQL execution?
- Which live public sources are acceptable for the reference weather-logistics setup beyond Open-Meteo fixture replay?
- Should the first auto-evidence implementation include web search, or only allow-listed APIs and feeds?
- What minimum benchmark evidence is required before OPE can describe a method as state of the art for a domain?
- How should TypeScript or other language-specific validators be generated from the JSON Schema-first contracts if a service runtime is added?
- Should track-record reports use Brier score as the default public metric for binary forecasts, or log score with Brier as supporting metric?
- Should benchmark mode support LLM forecasters in the first implementation, or only deterministic/statistical models?
- What minimal recurrence syntax should OPE expose so agents can express hourly, daily, weekly, until-date, count-bounded, threshold-targeted, and open-ended campaigns without writing raw scheduler configuration?
- Should local campaign evidence ledgers remain ignored artifacts only, or should sanitized append summaries have a committed promotion path?
- When, if ever, should OPE implement the future effectful `apply-method-update` and `rollback-method-update` commands after real campaign evidence and approvals exist?

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
