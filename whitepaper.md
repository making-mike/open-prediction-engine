# Open Prediction Engine Whitepaper

Date: May 16, 2026

## Abstract

Open Prediction Engine (OPE) is an open forecasting engine for producing measurable probabilistic forecasts with evidence, provenance, resolution records, scoring, and calibration feedback.

The core claim is deliberately narrow:

> Agents and software systems need forecasts that can be inspected, resolved, scored, and improved over time.

OPE does not attempt to predict everything. It is not a generic agent runtime, a marketplace, a payment network, or a trust authority. It is a domain-oriented engine that turns forecast questions into auditable forecast artifacts and later turns outcomes into calibration evidence.

The project is valid only when it can show, for a specific domain and horizon, that its questions are resolvable, forecasts are logged before outcomes are known, forecast histories are preserved, outcomes are resolved against stated sources, ambiguous cases are handled fairly, scores use appropriate rules, baselines are visible, and track records are reported with sample-size transparency.

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

OPE should be built as an evidence-producing forecasting engine, not as a universal answer layer.

The engine should:

- accept only questions that can be made specific enough to resolve
- manage question lifecycle states before accepting forecasts
- start in one narrow domain with frequent outcomes
- produce baseline forecasts before complex model forecasts
- preserve provenance for every material input
- emit forecast artifacts that are portable across systems
- log forecast histories before resolution
- support optional rationale and key-factor capture
- resolve outcomes against declared sources
- mark unscorable questions without corrupting track records
- score forecasts using appropriate rules
- report calibration by domain, horizon, output type, and coverage period
- improve future forecasts through measured feedback

This makes OPE useful for agentic systems because it gives agents a disciplined way to ask not merely "what might happen?" but "what did this system predict, why, from what evidence, and how has it performed in comparable cases?"

## 3. Scope

OPE owns the engine layer:

- signal ingestion
- source normalization
- source credibility metadata
- feature construction
- forecast question representation
- question lifecycle and resolution governance
- baseline forecast generation
- domain-specific model forecast generation
- forecast history recording
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
- pooled funding or demand aggregation
- payment settlement
- legal compliance certification
- independent external audit
- universal provider trust

The engine may integrate with external systems through APIs, files, queues, event streams, or agent-facing tools, but those integrations must remain adapters. The core project should stay focused on forecast generation and evaluation.

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

### 4.2 Baselines Come First

Every domain should start with simple baselines. A baseline may be historical frequency, persistence, seasonal average, consensus proxy, climatology, naive trend, or another transparent rule.

Complex models are only useful if they can beat or complement these baselines under comparable conditions.

### 4.3 Forecast Histories Matter

A forecast artifact is not only a final answer. Forecasts often update as new information arrives. OPE should preserve timestamped forecast histories, including whether a forecast was active, withdrawn, superseded, or re-affirmed.

This enables time-weighted scoring and lets downstream systems inspect how the engine responded to new information instead of seeing only the last prediction before resolution.

### 4.4 Evidence Is A First-Class Output

A forecast without evidence is not enough. Serious forecast outputs should include an evidence packet with:

- forecast id
- question id
- question status
- domain
- horizon
- forecast timestamp
- close time
- model version
- baseline version
- input source classes
- provenance references
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

### 4.5 Calibration Is Local

Calibration evidence should be reported by domain, horizon, output type, resolution source, coverage period, and sample size. A model that performs well for short-horizon logistics disruption should not inherit that credibility for long-horizon macro forecasts.

OPE should avoid broad claims such as "accurate predictions" unless the claim is tied to a measured domain, time period, scoring rule, and sample size.

### 4.6 Agents Need Deterministic Guardrails

Agentic systems can plan, call tools, and act across multiple steps. OPE should assume that some callers will be autonomous or semi-autonomous. Safety cannot depend on prompts alone.

The engine should use deterministic controls for:

- input validation
- schema validation
- source allow-lists
- request/result binding
- timeouts and aborts
- rate limits
- spend or cost limits where relevant
- approval gates for high-impact requests
- public error sanitization
- audit-safe logging

## 5. Reference Architecture

OPE should be composed as a pipeline with explicit records at each boundary:

```text
forecast need
  -> question normalization
  -> question contract and resolution review
  -> approval
  -> source ingestion
  -> source normalization
  -> feature construction
  -> baseline forecast
  -> model forecast
  -> optional aggregation or ensemble comparison
  -> evidence packet
  -> forecast history log
  -> close
  -> resolution or unscorable status
  -> scoring
  -> track record and calibration report
  -> model and baseline review
```

### 5.1 Question Registry

The question registry stores the forecast question as a contract. It should include title, background, resolution criteria, absolute dates, accepted output type, valid outcome space, resolution authority, primary source, fallback sources, lifecycle status, and clarification history.

Background context may help forecasters or models, but resolution criteria should stand on their own.

### 5.2 Source Connectors

Source connectors fetch or receive domain data. They should record source identity, fetch time, licensing or usage constraints where relevant, and enough metadata to reproduce the forecast context.

External data should be treated as untrusted input until validated.

### 5.3 Normalization Layer

Normalization converts raw source material into stable internal records. This layer should avoid hiding uncertainty. Missing values, stale data, conflicting observations, and source quality issues should remain visible downstream.

### 5.4 Feature Layer

Features should be versioned or reproducible. If a forecast later becomes part of a calibration report, maintainers need to know which feature definitions were used.

### 5.5 Baseline Module

The baseline module produces transparent comparison forecasts. Baselines should be simple, reproducible, and domain-appropriate.

### 5.6 Forecast Module

The forecast module produces probabilistic outputs. Depending on domain, this may be a binary probability, categorical distribution, numeric distribution, interval, quantile forecast, or structured scenario set.

The model should expose enough metadata for audit:

- model id
- version
- training window or configuration
- feature set
- inference timestamp
- uncertainty method
- known limitations

### 5.7 Aggregation And Ensemble Module

OPE should treat aggregation as an engine primitive without becoming a crowd platform. Aggregates may combine model variants, baselines, human forecasts, external probabilities, market prices, or source-specific models when the provenance and weighting method are explicit.

Aggregates should record:

- included forecast ids
- inclusion and exclusion rules
- weights or aggregation method
- recency handling
- bot, human, model, or market-source labels where relevant
- calibration history of each component when available

Aggregates can be useful baselines, ensemble forecasts, or diagnostic comparisons, but they must not erase source dependency. Correlated forecasts should not be treated as independent evidence.

### 5.8 Evidence Packet Generator

The evidence packet generator binds the question, inputs, baseline, model forecast, provenance, and resolution plan into a single artifact.

This binding is critical. Forecast ID, question ID, domain, horizon, model version, evidence references, and expected resolution must not drift apart.

### 5.9 Forecast History Log

The forecast history log records timestamped forecast states before outcome information is known. It should preserve updates, withdrawals, re-affirmations, and superseded forecasts. It should prevent silent retroactive editing. Implementations can begin with append-only files or database rows and later move to stronger tamper-evident storage if needed.

### 5.10 Resolution Ingestor

The resolution ingestor records outcomes from declared sources. Resolutions should include:

- resolution source
- resolution timestamp
- resolved value
- method or query used
- uncertainty or dispute status where relevant
- link or hash for supporting evidence

If the question cannot be resolved fairly, the result should be marked ambiguous or annulled rather than forced into a normal score.

### 5.11 Scoring Module

The scoring module applies rules appropriate to the output type. Examples:

- Brier score for binary forecasts
- multiclass Brier score for categorical forecasts
- log score where outcome and probability support it
- interval coverage and width for interval forecasts
- pinball loss for quantile forecasts

Scoring rules should be declared before resolution when possible. For forecast histories, scoring should support time weighting so the system can distinguish early, stale, updated, and last-minute forecasts. Ambiguous or annulled questions should not distort calibration summaries.

### 5.12 Track Record And Calibration Reporter

Track record and calibration reports summarize performance across comparable forecast sets. Reports should include sample size, coverage period, domain, horizon, output type, resolution source, score distribution, baseline comparison, reliability curves, score histograms, forecast count, resolved count, ambiguous count, annulled count, and freshness measures where appropriate.

## 6. Agentic System Fit

OPE is designed for agents and automated systems that need decision support under uncertainty. It should expose forecasts in a way that is:

- machine-readable
- compact enough to route through tool calls or APIs
- explicit about uncertainty
- explicit about provenance
- tied to later scoring
- able to expose forecast history and track records
- bounded by policy controls

OPE should not require callers to reveal more context than needed. Where possible, a caller should be able to request an upstream forecast primitive without exposing its full downstream strategy.

For high-impact domains, OPE should support human review before forecast generation, before disclosure, or before downstream action. The whitepaper treats forecasts as decision-support artifacts, not automatic decisions.

## 7. Security And Privacy Model

Forecasting systems can leak sensitive intent. A request for a forecast may reveal strategy, planned operations, financial exposure, supply-chain risk, or security posture.

OPE should therefore implement:

- data classification for requests, sources, features, and artifacts
- prompt and context minimization when model calls are used
- secret scanning for examples, fixtures, logs, and generated artifacts
- credential isolation from model-visible context
- provider and source allow-lists
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

OPE should launch with one narrow domain, not a broad promise.

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
2. source ingestion from controlled fixtures or allow-listed sources
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
- general future knowledge
- domain-agnostic superiority
- independent trust certification
- legal compliance
- payment settlement
- crowd coordination
- generic agent protocol compatibility unless implemented and tested

The strongest honest near-term claim is:

> OPE helps software agents and operators produce forecasts that can be measured later.

## 12. Development Roadmap

### Phase 1: Contracts

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

- Select one narrow domain.
- Add fixture data.
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
- Add approval gates for sensitive or costly requests.
- Add request/result binding checks.

### Phase 5: Hardening

- Add adversarial input tests.
- Add malformed artifact tests.
- Add privacy and secret-scanning checks.
- Add domain-level claim review.
- Add release checks.

## 13. Conclusion

OPE should make forecasting boring in the best way: explicit questions, stated horizons, known sources, recorded forecasts, resolved outcomes, proper scores, and calibration reports.

Its value is not that it promises certainty. Its value is that it turns uncertainty into measurable, inspectable artifacts that agents and humans can improve over time.

The project should earn broader scope only after a narrow domain shows a complete evidence loop.
