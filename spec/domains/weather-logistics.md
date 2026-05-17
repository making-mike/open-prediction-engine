# Weather Logistics Domain Wedge

Status: selected first wedge.

This note defines the first OPE domain narrow enough to build, resolve, and score end to end before broadening the engine. It is a domain contract note, not a public performance claim.

## Domain

`weather-logistics`

OPE will first forecast whether declared weather conditions disrupt last-mile logistics operations in a specific place and time window.

The first output type is binary probability:

- `yes`: the disruption criteria are satisfied.
- `no`: the disruption criteria are not satisfied.

## First Question Template

Template:

```text
Will qualifying weather disrupt declared last-mile delivery operations in {geography} during {service_date}?
```

Initial concrete fixture:

```text
Will heavy rain disrupt last-mile delivery operations in Warsaw on 2026-06-03?
```

Resolution must bind the event to both an operations condition and a weather condition. A question should not resolve `yes` from bad weather alone if no declared logistics disruption is observed.

## Initial Geography And Horizon

Initial geography:

- fixture-only Warsaw example already present in `spec/fixtures/valid/`
- future live prototype limited to one allow-listed metropolitan area until source quality is reviewed

Initial horizon:

- one service day
- forecasts close before the service day begins or at a predeclared cutoff
- resolution happens after source data for the service day is available

The canonical horizon label for the first wedge is `1-day`.

## Accepted Source Classes

Allowed source classes for the fixture stage:

- `internal_dataset`: synthetic or controlled operations fixtures
- `public_dataset`: public weather observations or forecasts when added
- `official`: official weather observations or warnings when added

Allowed later only after review:

- `human_judgment`: permitted for annotation or dispute review, not as the sole normal resolution source
- `model_output`: permitted as a forecast input, not as an outcome source

Out of scope source classes for the first wedge:

- `market_price`
- `aggregate`
- private operational feeds without a documented retention and redaction policy

## Resolution Sources

Primary resolution source:

- a declared operations event source showing whether weather-coded delivery disruption occurred in the selected geography and service day

Fallback resolution source:

- a declared weather observation source showing whether the qualifying weather threshold was met

For the current fixture, this means:

- primary: Warsaw logistics operations fixture
- fallback/supporting: Warsaw weather fixture

A normal `yes` resolution requires both:

- at least one declared weather-coded delivery disruption
- the predeclared weather threshold being met

If either source is unavailable, contradicted, materially corrected after scoring, or does not cover the declared geography and service day, the question should be marked `ambiguous` or `annulled` according to `spec/question-lifecycle.md`.

## Baseline Method

The first baseline is a historical-frequency baseline:

```text
P(disruption | geography, service-day seasonality, weather-threshold bucket)
```

When a caller restricts OPE to historical data only, this baseline is the forecast. OPE must not apply forecast-time weather API adjustments unless the source policy explicitly allows those evidence sources.

Fixture data may use a fixed baseline probability, but live data must record:

- lookback window
- sample count
- included geography
- weather-threshold bucket
- whether the baseline is smoothed
- source timestamps used to build the baseline

If the sample count is too small for a slice, the baseline should back off to a broader geography or broader seasonal bucket and record that backoff in the evidence packet.

## Calibration Claim Threshold

No calibration claim may be made for this wedge with fewer than 30 resolved, comparable questions.

Recommended claim levels:

- fewer than 30 resolved questions: show individual scores only
- 30 to 99 resolved questions: show provisional calibration buckets with strong sample-size warnings
- 100 or more resolved questions: allow domain-level calibration summaries for the same horizon and source policy

Calibration claims must remain scoped to `weather-logistics`, the `1-day` horizon, the source policy, the geography set, and the coverage period.

## Out Of Scope

The first wedge does not include:

- route optimization
- workforce scheduling
- carrier selection
- pricing or insurance decisions
- legal liability or SLA enforcement
- emergency response or public-safety automation
- private customer-level or driver-level analytics
- broad claims that OPE can forecast arbitrary operational outcomes

## Milestone Use

This wedge should drive the next implementation slice:

1. fixture ingestion
2. normalized source records
3. baseline forecast generation
4. deterministic placeholder model forecast
5. evidence packet generation
6. forecast history append
7. fixture resolution
8. scoring, calibration, and track-record reports

The live data prototype should not begin until the fixture evidence loop is complete.
