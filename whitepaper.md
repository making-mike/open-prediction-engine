# Open Prediction Engine Whitepaper

Date: May 17, 2026

## Abstract

Open Prediction Engine (OPE) is an open, agent-native forecasting package and standard for producing measurable probabilistic forecasts from connected source data. It helps agents and developers set up private prediction engines that preserve evidence, provenance, method selection, forecast histories, resolution records, scoring, and calibration feedback as portable OPE records.

The core claim is deliberately narrow:

> Agents and software systems need forecasts that can be set up from chosen data, requested, evidenced, inspected, updated, resolved, scored, and improved over time.

OPE does not attempt to be a universal oracle. It is not a generic agent runtime, a marketplace, a payment network, a web crawler claiming access to all internet knowledge, or a trust authority. It is a forecasting engine and record standard that lets agents connect source data, define or reuse resolvable forecast domains, produce auditable forecast artifacts, and later turn outcomes into calibration evidence.

The project is valid only when it can show, for a specific engine setup, domain, and horizon, that its questions are resolvable, forecasts are logged before outcomes are known, forecast histories are preserved, outcomes are resolved against stated sources, ambiguous cases are handled fairly, scores use appropriate rules, baselines are visible, and track records are reported with sample-size transparency.

## 1. The Problem

Autonomous agents increasingly need to act under uncertainty. They plan shipments, allocate budget, schedule work, monitor risk, and decide when to ask for human review. Many of those decisions depend on future events:

- Will a delivery route be disrupted tomorrow?
- Will demand exceed capacity next week?
- Will a public data release move outside an expected range?
- Will a monitored security indicator cross a threshold?

The common failure mode is not lack of prediction text. Models can always produce plausible prose. The failure mode is lack of measurable forecasting discipline.

Useful forecasts need:

- clear questions
- explicit horizons
- resolvable outcomes
- resolution governance
- declared source policies
- evidence gathering plans
- known data provenance
- uncertainty estimates
- baseline comparisons
- forecast histories
- pre-resolution logs
- proper scoring
- calibration reports
- sample-size transparency

Without this evidence loop, forecast claims become marketing language. Agents cannot tell whether a forecast was good, whether a provider is calibrated, or whether quality in one domain transfers to another.

## 2. Thesis

OPE should be built as an evidence-producing forecasting package and standard, not as a universal answer layer.

The engine should be flexible about private setup and strict about forecast quality records. An agent should be able to connect the data it is allowed to use, define a forecast domain, provide mappings or connectors, and ask OPE for a probability. OPE should then make the setup explicit: what question is being forecast, what sources were connected, which mappings or transformations were used, which method is justified, how the forecast changes when new data arrives, and what claim boundary applies.

The engine should:

- accept only questions that can be made specific enough to resolve
- manage question lifecycle states before accepting forecasts
- support candidate private domains while clearly labeling their maturity and claim boundaries
- support caller-provided data and policy-bound `data: auto` evidence gathering
- record what sources were searched, used, unavailable, stale, or rejected
- produce baseline forecasts before complex model forecasts
- select the best justified enabled method for the connected data rather than claiming universal best performance
- preserve provenance for every material input
- emit forecast artifacts that are portable across systems
- log forecast histories before resolution
- append updated forecast-history entries when new data arrives instead of silently overwriting earlier forecasts
- support optional rationale and key-factor capture
- resolve outcomes against declared sources
- mark unscorable questions without corrupting track records
- score forecasts using appropriate rules
- report calibration by domain, horizon, output type, and coverage period
- improve future forecasts through measured feedback

This makes OPE useful for agentic systems because it gives agents a disciplined way to ask not merely "what might happen?" but "what did this system predict, why, from what evidence, and how has it performed in comparable cases?"

The default long-term product mode should let an agent set up or use a prediction engine without hand-authoring every contract. OPE may accept caller-provided data, private files, private APIs, manual mappings, and agent-assisted extraction, but it should make each input's status explicit. Policy-bound auto-evidence gathering remains valuable, but the core standard should also support private, caller-chosen data as long as the resulting forecasts preserve source policy, provenance, resolution, scoring, and claim labels.

## 3. Scope

OPE owns the engine and forecast-standard layer:

- domain setup contracts
- source manifests, mappings, and connector policies
- signal ingestion
- evidence planning and source policy enforcement
- source discovery through caller-approved connectors
- source normalization
- source credibility metadata
- feature construction
- forecast question representation
- question lifecycle and resolution governance
- baseline forecast generation
- domain-specific model forecast generation
- method selection based on available data, benchmark evidence, and baseline comparison
- forecast history recording
- recalculation history when new data arrives
- forecast aggregation and ensemble comparison
- uncertainty quantification
- evidence packet generation
- provenance tracking
- pre-resolution logging
- outcome resolution
- proper scoring
- calibration reporting
- model and baseline comparison

OPE does not own:

- generic agent-to-agent communication
- broad task execution
- unbounded internet crawling as default behavior or an unqualified evidence claim
- pooled funding or demand aggregation
- payment settlement
- legal compliance certification
- independent external audit
- universal provider trust

The engine may integrate with external systems through APIs, files, queues, event streams, or agent-facing tools, but those integrations must remain adapters. The core project should stay focused on forecast setup, generation, update history, and evaluation.

## 4. Design Principles

### 4.1 Forecast Questions Must Be Governed

A forecast question is not ready until the engine can answer:

- What exactly is being predicted?
- What is the time horizon?
- What are the open, close, and scheduled resolution times?
- What output type is required?
- What source resolves the outcome?
- What fallback sources are acceptable?
- When will resolution happen?
- What makes the outcome true, false, or numeric?
- Who or what is allowed to resolve it?
- Is the question too vague, private, or high-risk to process automatically?

If these answers are missing, OPE should reject the question or request clarification.

OPE should model question lifecycle explicitly:

- draft
- approved
- open
- closed
- resolved
- ambiguous
- annulled
- re-resolved

Ambiguous questions are cases where reality cannot be determined clearly enough from the declared sources. Annulled questions are cases where reality may be clear, but the question contract was not. Neither should be silently folded into normal scores.

### 4.2 Private Setups Should Be Flexible, Claims Should Be Strict

OPE should allow private deployments to connect their own files, databases, APIs, mappings, and domain rules. A developer or agent may know the relevant sources better than the core OPE package does.

The strictness should apply to forecast records and claims:

- Was the question made resolvable?
- What source data was connected?
- Which mappings were user-provided, agent-inferred, or registry-backed?
- Which sources were used, rejected, stale, unavailable, or resolution-only?
- Which method was selected and why?
- What baseline is the forecast compared against?
- Is this domain candidate, fixture-ready, benchmarked, live-provisional, or calibrated?
- What evidence would change the forecast?

This lets private engines move quickly without giving every setup the same credibility label.

### 4.3 Baselines Come First

Every domain should start with simple baselines. A baseline may be historical frequency, persistence, seasonal average, consensus proxy, climatology, naive trend, or another transparent rule.

Complex models are only useful if they can beat or complement these baselines under comparable conditions.

When a caller provides only historical data or forbids forecast-time source access, the baseline may be the forecast. OPE should make that mode explicit rather than silently applying unavailable external signals.

### 4.4 Forecast Histories Matter

A forecast artifact is not only a final answer. Forecasts often update as new information arrives. OPE should preserve timestamped forecast histories, including whether a forecast was active, withdrawn, superseded, or re-affirmed.

This enables time-weighted scoring and lets downstream systems inspect how the engine responded to new information instead of seeing only the last prediction before resolution.

### 4.5 Evidence Is A First-Class Output

A forecast without evidence is not enough. Serious forecast outputs should include an evidence packet with:

- forecast id
- question id
- question status
- domain
- domain setup status
- horizon
- forecast timestamp
- close time
- model version
- baseline version
- input source classes
- provenance references
- source mapping and connector references
- feature snapshot reference
- forecast probability or distribution
- baseline forecast
- optional aggregate forecast or external reference forecast
- uncertainty or calibration band
- optional rationale
- optional key factors
- resolution criteria
- resolution source
- fallback resolution sources
- scheduled resolution time

The packet should be stable enough for later scoring and compact enough for external systems to store or reference.

### 4.6 Calibration Is Local

Calibration evidence should be reported by domain, horizon, output type, resolution source, coverage period, and sample size. A model that performs well for short-horizon logistics disruption should not inherit that credibility for long-horizon macro forecasts.

OPE should avoid broad claims such as "accurate predictions" unless the claim is tied to a measured domain, time period, scoring rule, and sample size.

### 4.7 Agents Need Deterministic Guardrails

Agentic systems can plan, call tools, and act across multiple steps. OPE should assume that some callers will be autonomous or semi-autonomous. Safety cannot depend on prompts alone.

The engine should use deterministic controls for:

- input validation
- schema validation
- source policy enforcement
- request/result binding
- timeouts and aborts
- rate limits
- spend or cost limits where relevant
- approval gates for high-impact requests
- public error sanitization
- audit-safe logging

### 4.8 Auto-Evidence Must Be Policy-Bound

OPE should make it easy for agents to request forecasts with `data: auto`, but auto-evidence gathering must remain bounded and inspectable.

Every auto-evidence run should declare:

- domain and question template
- source policy
- allowed connectors and source classes
- freshness requirements
- retrieval window
- evidence inclusion and exclusion rules
- source quality checks
- unavailable or unverifiable evidence
- provenance records and fetch timestamps

OPE should not claim to use all available internet information. The honest claim is that it gathered the best available allowed evidence under a declared policy and preserved enough context for later audit.

## 5. Reference Architecture

OPE should be composed as a pipeline with explicit records at each boundary:

```text
forecast need
  -> domain setup or candidate-domain proposal
  -> source manifest and mapping review
  -> question normalization
  -> question contract and resolution review
  -> approval
  -> source policy selection
  -> evidence gathering plan
  -> allowed source discovery
  -> source ingestion
  -> source normalization
  -> feature construction
  -> baseline forecast
  -> model forecast
  -> optional aggregation or ensemble comparison
  -> evidence packet
  -> forecast history log
  -> recalculation when new data arrives
  -> close
  -> resolution or unscorable status
  -> scoring
  -> track record and calibration report
  -> model and baseline review
```

### 5.1 Question Registry

The question registry stores the forecast question as a contract. It should include title, background, resolution criteria, absolute dates, accepted output type, valid outcome space, resolution authority, primary source, fallback sources, lifecycle status, and clarification history.

Background context may help forecasters or models, but resolution criteria should stand on their own.

### 5.2 Domain Setup Registry

The domain setup registry records the private or built-in configuration that makes a forecast family possible. It should include the domain name, question templates, supported horizons, output types, source roles, required fields, accepted mappings, baseline rules, method policy, resolution rules, scoring rules, and maturity status.

Agents may propose new domains or mappings, but OPE should label them as candidate until fixtures, benchmarks, resolution rules, and scoring checks justify stronger claims.

### 5.3 Source Connectors

Source connectors fetch or receive domain data. They should record source identity, fetch time, licensing or usage constraints where relevant, and enough metadata to reproduce the forecast context.

External data should be treated as untrusted input until validated.

For private engine setups, connectors may include caller-provided files, private databases, internal APIs, public APIs, or agent-assisted extraction outputs. For auto-evidence requests, connectors must be policy-scoped. Search, browsing, API calls, and feed ingestion should produce provenance records, not invisible prompt context.

### 5.4 Normalization Layer

Normalization converts raw source material into stable internal records. This layer should avoid hiding uncertainty. Missing values, stale data, conflicting observations, and source quality issues should remain visible downstream.

### 5.5 Feature Layer

Features should be versioned or reproducible. If a forecast later becomes part of a calibration report, maintainers need to know which feature definitions were used.

### 5.6 Baseline Module

The baseline module produces transparent comparison forecasts. Baselines should be simple, reproducible, and domain-appropriate.

For historical-only requests, this module can produce the primary forecast artifact, with clear warnings that no forecast-time API evidence was used.

### 5.7 Forecast Module

The forecast module produces probabilistic outputs. Depending on domain, this may be a binary probability, categorical distribution, numeric distribution, interval, quantile forecast, or structured scenario set.

The module should choose among enabled methods according to the domain setup, available data, benchmark evidence, sample size, and baseline comparison. "Best" should mean best justified for this setup, not globally best.

The model should expose enough metadata for audit:

- model id
- version
- training window or configuration
- feature set
- inference timestamp
- uncertainty method
- known limitations

### 5.8 Aggregation And Ensemble Module

OPE should treat aggregation as an engine primitive without becoming a crowd platform. Aggregates may combine model variants, baselines, human forecasts, external probabilities, market prices, or source-specific models when the provenance and weighting method are explicit.

Aggregates should record:

- included forecast ids
- inclusion and exclusion rules
- weights or aggregation method
- recency handling
- bot, human, model, or market-source labels where relevant
- calibration history of each component when available

Aggregates can be useful baselines, ensemble forecasts, or diagnostic comparisons, but they must not erase source dependency. Correlated forecasts should not be treated as independent evidence.

### 5.9 Evidence Packet Generator

The evidence packet generator binds the question, inputs, baseline, model forecast, provenance, and resolution plan into a single artifact.

This binding is critical. Forecast ID, question ID, domain setup, horizon, model version, evidence references, mappings, and expected resolution must not drift apart.

### 5.10 Forecast History Log

The forecast history log records timestamped forecast states before outcome information is known. It should preserve updates, withdrawals, re-affirmations, and superseded forecasts. It should prevent silent retroactive editing. Implementations can begin with append-only files or database rows and later move to stronger tamper-evident storage if needed.

### 5.11 Resolution Ingestor

The resolution ingestor records outcomes from declared sources. Resolutions should include:

- resolution source
- resolution timestamp
- resolved value
- method or query used
- uncertainty or dispute status where relevant
- link or hash for supporting evidence

If the question cannot be resolved fairly, the result should be marked ambiguous or annulled rather than forced into a normal score.

### 5.12 Scoring Module

The scoring module applies rules appropriate to the output type. Examples:

- Brier score for binary forecasts
- multiclass Brier score for categorical forecasts
- log score where outcome and probability support it
- interval coverage and width for interval forecasts
- pinball loss for quantile forecasts

Scoring rules should be declared before resolution when possible. For forecast histories, scoring should support time weighting so the system can distinguish early, stale, updated, and last-minute forecasts. Ambiguous or annulled questions should not distort calibration summaries.

### 5.13 Track Record And Calibration Reporter

Track record and calibration reports summarize performance across comparable forecast sets. Reports should include sample size, coverage period, domain, horizon, output type, resolution source, score distribution, baseline comparison, reliability curves, score histograms, forecast count, resolved count, ambiguous count, annulled count, and freshness measures where appropriate.

## 6. Agentic System Fit

OPE is designed for agents and automated systems that need decision support under uncertainty. It should expose forecasts in a way that is:

- machine-readable
- easy to initialize from caller-chosen data sources
- compact enough to route through tool calls or APIs
- explicit about uncertainty
- explicit about source policy, data mappings, and evidence-gathering mode
- explicit about provenance
- able to recalculate without erasing previous forecasts
- tied to later scoring
- able to expose forecast history and track records
- bounded by policy controls

OPE should not require callers to reveal more context than needed. Where possible, a caller should be able to request an upstream forecast primitive without exposing its full downstream strategy.

Adapter surfaces should remain thin envelopes over OPE records. A local CLI, MCP tool, HTTP endpoint, or queue worker may expose request validation, evidence plans, forecast cards, lifecycle bundles, resolution status, and scoring summaries, but those adapters should preserve the same record bindings, warnings, exit states, and claim boundaries.

The primary runtime actor may be an agent. The primary adopter may be a human developer who wants that agent to use a credible, open-source forecasting engine before acting, waiting, escalating, or gathering more evidence.

For high-impact domains, OPE should support human review before forecast generation, before disclosure, or before downstream action. The whitepaper treats forecasts as decision-support artifacts, not automatic decisions.

## 7. Security And Privacy Model

Forecasting systems can leak sensitive intent. A request for a forecast may reveal strategy, planned operations, financial exposure, supply-chain risk, or security posture.

OPE should therefore implement:

- data classification for requests, sources, features, and artifacts
- prompt and context minimization when model calls are used
- secret scanning for examples, fixtures, logs, and generated artifacts
- credential isolation from model-visible context
- provider and source policy registries
- audit-safe logging by default
- deterministic policy gates for paid, external, high-impact, or irreversible actions
- adversarial tests for prompt injection, malformed inputs, oversized outputs, replay, and request/result mismatch

Public artifacts should avoid secrets, private prompts, personal data, raw credentials, and unnecessary downstream intent. When raw diagnostics are needed, they should stay in trusted logs.

## 8. Compliance Posture

OPE should be treated as forecasting infrastructure whose risk profile depends on deployment context.

The same engine may be low-risk when forecasting internal operational demand and high-risk when used in safety-critical, employment, credit, medical, legal, or other rights-impacting settings.

The project should provide hooks for:

- audit logs
- model and data documentation
- human oversight
- override and stop procedures
- incident review
- data retention policy
- provenance export
- calibration and performance reporting

These hooks are not legal compliance by themselves. Deployment owners must classify their own use case, jurisdiction, autonomy level, and affected users before relying on OPE in high-impact environments.

## 9. Initial Wedge Strategy

OPE should launch with one narrow reference domain, not a broad quality claim.

The long-term product may let agents set up many private domains, but the open project still needs one complete reference implementation to prove the standard end to end.

A good initial domain has:

- frequent resolution
- clear ground truth
- measurable operational value
- low legal risk
- enough external data
- repeatable demand
- simple baseline availability

Strong candidates include:

- logistics disruption probability
- weather-linked operational forecasting
- energy demand nowcasting
- narrow public-release forecasting
- cyber indicator likelihood for clearly defined signals

The first public proof should show:

1. a documented domain and question template
2. source ingestion from controlled fixtures, caller-provided data, or policy-approved sources
3. at least one simple baseline
4. one model forecast path
5. question lifecycle states
6. evidence packet creation
7. forecast history logging
8. resolution records
9. ambiguous and annulled handling
10. scoring reports
11. calibration summary
12. track-record report
13. a claim review showing that documentation matches measured behavior

Private domains can exist earlier as candidate setups, but they should not inherit calibration or method-quality claims from the reference domain.

## 10. Quality Metrics

Forecast quality should be measured across several dimensions:

| Dimension | Example metrics |
|---|---|
| Calibration | reliability curve, expected calibration error, bucket-level observed frequency |
| Sharpness | interval width, distribution concentration, entropy where appropriate |
| Proper scoring | Brier score, log score, pinball loss |
| Baseline lift | improvement over historical, persistence, climatology, or consensus baseline |
| Aggregation quality | component contribution, ensemble lift, recency sensitivity, dependency overlap |
| Coverage | sample size by domain, horizon, and output type |
| Freshness | source age, feature age, resolution lag |
| Robustness | missing-data behavior, source disagreement, model-version drift |
| Track record health | resolved count, ambiguous count, annulled count, score histogram, calibration by slice |

No metric is universal. Each domain should define its own evaluation plan before strong claims are made.

## 11. Claim Boundaries

OPE may claim:

- domain-specific probabilistic forecast generation
- OPE-standard forecast setup from caller-provided or connector-provided data
- policy-bound evidence gathering for implemented domains
- forecast recalculation history when new evidence arrives
- evidence packet generation
- provenance-aware forecast artifacts
- forecast history logging
- outcome resolution for declared sources
- proper scoring for supported output types
- calibration reporting for measured forecast sets
- baseline comparison
- track-record reporting
- explicit ambiguous and annulled statuses

OPE must not claim:

- universal prediction ability
- access to all available internet evidence
- state-of-the-art performance without benchmark evidence
- best possible performance without tying the claim to connected data, enabled methods, baseline comparison, and track record
- general future knowledge
- domain-agnostic superiority
- independent trust certification
- legal compliance
- payment settlement
- crowd coordination
- generic agent protocol compatibility unless implemented and tested

The strongest honest near-term claim is:

> OPE helps software agents and operators produce evidence-backed forecasts that can be measured later.

## 12. Development Roadmap

### Phase 1: Contracts

- Define domain setup records.
- Define source manifest and mapping records.
- Define forecast question records.
- Define question lifecycle and resolution governance records.
- Define evidence packet records.
- Define forecast history records.
- Define baseline and model forecast output records.
- Define aggregate forecast records.
- Define resolution records.
- Define scoring report records.
- Define calibration summary records.

### Phase 2: First Domain

- Select one narrow reference domain.
- Add fixture data.
- Add caller-provided source examples.
- Add source normalization.
- Add baseline forecast generation.
- Add model forecast generation.
- Add evidence packet generation.
- Add forecast history logging.

### Phase 3: Evidence Loop

- Add pre-resolution logging.
- Add resolution ingestion.
- Add ambiguous and annulled status handling.
- Add scoring.
- Add calibration reporting.
- Add track-record reporting.
- Add baseline comparison report.

### Phase 4: Agent-Facing Access

- Expose read-only forecast artifact retrieval.
- Expose controlled forecast request execution.
- Add package-level engine setup commands or APIs for connecting sources and defining candidate domains.
- Add recalculation behavior that appends forecast-history entries when new source data arrives.
- Add policy-bound auto-evidence mode for the first domain.
- Record evidence-gathering plans, source-policy decisions, and unavailable evidence.
- Add approval gates for sensitive or costly requests.
- Add request/result binding checks.

### Phase 5: Forecasting Method Quality

- Add a method registry for baseline, statistical, model-assisted, and ensemble forecasting methods.
- Benchmark enabled methods against baselines.
- Add leakage and source-contamination controls for method comparison.
- Report method quality only by domain, horizon, sample size, and coverage period.

### Phase 6: Hardening

- Add adversarial input tests.
- Add malformed artifact tests.
- Add source and prompt injection tests for auto-evidence gathering.
- Add privacy and secret-scanning checks.
- Add domain-level claim review.
- Add release checks.

## 13. Conclusion

OPE should make forecasting boring in the best way: explicit questions, stated horizons, known sources, recorded forecasts, resolved outcomes, proper scores, and calibration reports.

Its value is not that it promises certainty. Its value is that it turns uncertainty into measurable, inspectable artifacts that agents and humans can improve over time.

The project should earn broader public quality claims only after narrow reference domains show complete evidence loops. Private candidate setups can be flexible earlier, but their maturity labels must remain honest.
