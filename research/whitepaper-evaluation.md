# OPE Whitepaper Research Evaluation

Date: 2026-05-16

## Executive Verdict

The `whitepaper.md` is directionally strong and now matches the core lessons from mature forecasting systems: questions must be resolvable, forecasts must be logged before outcomes, scoring must be proper, track records must be sliced by domain and horizon, and broad "predict anything" claims must be avoided.

My evaluation: **8.1 / 10 as a strategic whitepaper**, but only **5.8 / 10 as an implementation specification**.

The next major upgrade should not be more narrative. It should be a concrete contract package: question lifecycle schema, forecast history schema, resolution schema, scoring schema, calibration report schema, and benchmark protocol.

## Research Basis

This evaluation compared the OPE whitepaper against:

- Metaculus' question, resolution, scoring, aggregation, and track-record documentation.
- Good Judgment and IARPA ACE materials on elicitation, aggregation, and representation of probabilistic judgments.
- Prediction market documentation and research on market prices, resolution rules, and contract design.
- Forecast evaluation literature on proper scoring rules, calibration, and sharpness.
- AI forecasting benchmark work, especially temporal leakage and contamination-free dynamic evaluation.
- AI risk/security guidance for agentic and LLM-enabled systems.

Primary references:

- Metaculus FAQ: https://www.metaculus.com/faq/
- Metaculus Scores FAQ: https://www.metaculus.com/help/scores-faq/
- Metaculus Question Approval Checklist: https://www.metaculus.com/help/question-checklist/
- Metaculus Track Record: https://www.metaculus.com/questions/track-record/
- IARPA ACE program: https://www.iarpa.gov/research-programs/ace
- Gneiting and Raftery, proper scoring rules: https://www.tandfonline.com/doi/abs/10.1198/016214506000001437
- Polymarket resolution docs: https://docs.polymarket.com/concepts/resolution
- Kalshi market rules: https://help.kalshi.com/en/articles/13823822-market-rules
- Kalshi market FAQs: https://help.kalshi.com/en/articles/13823821-market-faqs
- Wolfers and Zitzewitz, Prediction Markets: https://www.aeaweb.org/articles?id=10.1257/0895330041371321
- Metaculus FutureEval methodology: https://www.metaculus.com/futureeval/methodology/
- ForecastBench: https://www.forecastbench.org/about/
- Pitfalls in Evaluating Language Model Forecasters: https://arxiv.org/abs/2506.00723
- ForecastBench paper: https://arxiv.org/abs/2409.19839
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications
- OWASP MCP Top 10: https://owasp.org/www-project-mcp-top-10/

## What Mature Forecasting Systems Teach

### 1. Question Contracts Are The Product Boundary

Metaculus treats resolution criteria as a scoring contract. Its checklist emphasizes absolute dates, authority for resolution, fallback sources, headline-to-resolution alignment, and careful handling of source-vs-truth questions. It also uses Ambiguous and Annulled resolutions to preserve scoring fairness when the real world or the written criteria do not support a clean outcome.

OPE now captures this in principle. The whitepaper should next turn it into machine-readable fields and validation rules.

Recommended contract additions:

- `question.status`: draft, approved, open, closed, resolved, ambiguous, annulled, re_resolved
- `openAt`, `closeAt`, `resolveAt`
- `resolutionAuthority`
- `primaryResolutionSource`
- `fallbackResolutionSources`
- `resolutionMode`: source_behavior | true_answer | admin_judgment | automated_measurement
- `clarificationHistory`
- `unscorableReason`
- `incentiveRiskReview`

### 2. Forecast Histories Matter More Than Final Forecasts

Metaculus uses time-aware scoring and a time-weighted Community Prediction. This is important because forecast quality includes whether a forecaster updates when evidence changes, not only where the final estimate lands.

OPE already added forecast histories. The whitepaper should go one step further and define history semantics:

- active forecast
- withdrawn forecast
- superseded forecast
- reaffirmed forecast
- forecast made during hidden or benchmark period
- forecast made after close but before resolution, if allowed for internal analysis only

### 3. Proper Scoring Needs Formal Per-Output Definitions

The whitepaper correctly names Brier score, log score, interval coverage, and pinball loss. It should not stop there. Gneiting and Raftery emphasize proper scoring rules as the disciplined basis for ranking probabilistic forecasts while balancing calibration and sharpness.

OPE needs a scoring matrix:

| Output type | Recommended primary score | Supporting diagnostics |
|---|---|---|
| Binary | Brier or log score | calibration buckets, sharpness, base rate |
| Categorical | multiclass Brier or log score | probability mass on resolved class, entropy |
| Numeric distribution | CRPS or log score when density is available | PIT histogram, coverage, interval width |
| Quantiles | pinball loss | quantile coverage |
| Intervals | interval score | empirical coverage and width |
| Date/time | transformed numeric distribution score | horizon error, interval coverage |

### 4. Aggregation Is Useful But Dangerous Without Dependency Tracking

IARPA ACE explicitly focused on elicitation, mathematical aggregation, and representation of aggregate forecast distributions. Metaculus aggregation is time-weighted and historically used calibrated/weighted models. Good Judgment evidence suggests elite forecasters and aggregation can materially improve accuracy.

Prediction markets add another useful signal, but market prices are not pure probabilities. They include liquidity, fees, risk preference, trader constraints, manipulation risk, and resolution-governance risk.

OPE's aggregation section is good, but it needs a dependency and source-correlation model:

- human forecast
- model forecast
- market price
- statistical baseline
- external aggregate
- duplicate or derivative source
- shared upstream data
- shared model family

Aggregation should produce not just a probability but an `independenceAssessment` and `dependencyGraphRef`.

### 5. AI Forecasting Needs Temporal Leakage Controls

FutureEval and ForecastBench show where AI forecasting evaluation is going: dynamic, real-world questions, human baselines, and continuously updated leaderboards. ForecastBench explicitly frames future-event questions as a way to avoid contamination. Recent work on LLM forecasters warns that temporal leakage and extrapolation problems can make AI forecasting claims unreliable.

OPE should add a benchmark mode before making model-quality claims:

- question created before outcome is knowable
- model version and training cutoff recorded
- retrieval window recorded
- all source fetches timestamped
- no post-outcome data in prompts, features, caches, or retrieved documents
- benchmark run manifest saved
- human, baseline, market, and model comparison groups separated

### 6. Resolution Governance Is A Product Risk, Not A Detail

Polymarket and Kalshi reinforce the same lesson as Metaculus: titles do not resolve markets; rules do. Polymarket's docs explicitly distinguish market title from resolution rules and include resolution source, end date, and edge cases. Kalshi market rules similarly define conditions for contract settlement and may wait for official source agencies.

OPE should treat resolution governance as a first-class risk category:

- unclear source
- late source
- source corrected after initial publication
- conflicting sources
- source no longer exists
- source behavior differs from real-world truth
- outcome manipulability
- high incentive to influence the outcome

## Whitepaper Strengths

- Strong claim discipline: it rejects "predict anything."
- Correctly separates engine responsibilities from marketplaces, transports, payments, and independent audit.
- Correctly puts baselines before complex models.
- Correctly treats calibration as local to domain, horizon, output type, resolution source, and sample size.
- Strong addition of question lifecycle, forecast histories, ambiguous and annulled statuses, aggregation, and track records.
- Strong security posture: request/result binding, source allow-lists, public error sanitization, approval gates, and privacy minimization.
- Good first-wedge strategy: narrow domain, frequent resolution, simple baseline, measurable value.

## Whitepaper Gaps

### P0: No Concrete First Wedge

The whitepaper lists candidate domains but does not choose one. That is fine for a whitepaper, but it blocks implementation.

Recommendation: pick one initial wedge and add a domain appendix.

Best initial wedge from the current options: **weather-linked logistics disruption probability**.

Why:

- frequent resolution
- public data sources
- low legal risk compared with finance, employment, healthcare, or credit
- clear operational value
- simple baselines available
- reasonable agent use cases

### P0: No Contract Schema Yet

The narrative is contract-first but no contract exists.

Recommendation: create `spec/` with:

- `forecast-question.schema.json`
- `forecast-history.schema.json`
- `forecast-artifact.schema.json`
- `evidence-packet.schema.json`
- `aggregate-forecast.schema.json`
- `resolution-record.schema.json`
- `scoring-report.schema.json`
- `track-record-report.schema.json`
- `calibration-summary.schema.json`
- `benchmark-run.schema.json`

### P0: Scoring Is Named But Not Specified

The whitepaper names scoring rules, but implementers need exact formulas, sign conventions, missing-data rules, and aggregation windows.

Recommendation: add `spec/scoring.md` with formulas, examples, and a test fixture for each supported output type.

### P1: Benchmark Mode Is Missing

OPE needs explicit anti-leakage controls before it can credibly compare models or claim improvement.

Recommendation: add a benchmark protocol:

- frozen model identity
- model training cutoff
- retrieval source list
- retrieval timestamp
- source document hashes where possible
- benchmark start and end time
- known-answer exclusion checks
- post-resolution audit

### P1: Aggregation Needs Guardrails

The whitepaper allows aggregation of humans, models, market prices, and external probabilities. That is powerful but easy to overclaim.

Recommendation: require every aggregate to declare:

- source class
- source independence
- weighting method
- recency method
- liquidity or sample-size proxy where relevant
- dependency graph
- whether the aggregate is used as baseline, feature, or final forecast

### P1: Resolution Governance Needs Failure Modes

The whitepaper mentions ambiguous and annulled statuses, but should specify when to use them.

Recommendation:

- ambiguous: reality unclear or conflicting
- annulled: reality clear but question contract failed
- disputed: provisional status before final resolution
- corrected: prior resolution changed because source corrected itself
- stale_source: resolution source unavailable by deadline

### P1: Track Records Need Consumer-Friendly Shape

Agents need compact track-record summaries, not only full reports.

Recommendation: define two levels:

- compact `trackRecordSummary` for routing/filtering
- full `trackRecordReport` for audit and analysis

Compact fields:

- domain
- horizon bucket
- output type
- coverage period
- nForecasts
- nResolved
- nAmbiguous
- nAnnulled
- primary score
- baseline score
- baseline lift
- calibration error
- lastUpdated

### P2: Human Rationale Is Underspecified

Metaculus-style platforms use comments and essays because reasons matter for decision-makers. OPE mentions rationale, but it should structure it.

Recommendation:

- `rationaleSummary`
- `keyDrivers`
- `counterEvidence`
- `whatWouldChangeForecast`
- `sourceNotes`
- `modelLimitations`

### P2: Security Section Should Include Forecast-Specific Abuse

The security section is good for agentic systems, but forecasting creates special incentives.

Add:

- question manipulation risk
- source manipulation risk
- outcome manipulation risk
- market/forecast feedback loops
- private demand leakage
- adversarial source injection
- benchmark leakage

## Recommended Whitepaper Edits

The whitepaper is already good enough to keep as public narrative. I recommend adding three short sections, not rewriting it:

1. **Benchmark And Anti-Leakage Mode**
   Describe dynamic future-event benchmarks, model training cutoff, retrieval timestamping, and post-resolution audit.

2. **Resolution Failure Modes**
   Define ambiguous, annulled, disputed, corrected, and stale-source statuses.

3. **Implementation Contract Package**
   List the first schemas and fixtures that must exist before the project claims release readiness.

## Proposed Near-Term Roadmap

### Milestone 1: Contract Skeleton

- Add `spec/forecast-question.schema.json`.
- Add `spec/forecast-history.schema.json`.
- Add `spec/resolution-record.schema.json`.
- Add `spec/scoring-report.schema.json`.
- Add `spec/track-record-report.schema.json`.
- Add fixtures for one binary question and one numeric question.

### Milestone 2: First Wedge Decision

- Pick the first domain.
- Record why the domain was chosen.
- Record rejected alternatives.
- Define accepted data sources and resolution source.
- Define the baseline.

### Milestone 3: Scoring Harness

- Implement Brier score.
- Implement log score.
- Implement interval or numeric score only if the first wedge needs it.
- Add time-weighted scoring for forecast histories.
- Add tests for ambiguous and annulled exclusions.

### Milestone 4: Benchmark Protocol

- Define benchmark-run records.
- Add model/run provenance.
- Add source timestamp and hash fields.
- Add leakage checks.

### Milestone 5: Public Claim Review

- Review README and whitepaper against implemented behavior.
- Do not claim model quality until at least one resolved sample exists.
- Do not claim calibration until sample size is meaningful.

## Bottom Line

The whitepaper is honest and architecturally sound. It correctly positions OPE as a measurable forecasting engine rather than a generic prediction oracle.

The biggest risk is now execution drift: building model logic before the question, history, resolution, scoring, and benchmark contracts are nailed down. If the next commit is `spec/` plus fixtures, the project will stay on the right rails. If the next commit is a generic LLM forecast endpoint, the project will recreate the exact failure mode the whitepaper warns against.
