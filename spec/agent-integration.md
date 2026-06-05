# Agent Integration Golden Path

`agent-integrate` is the checked local surface for agents that want to incorporate OPE into another project and ask what can be forecasted from approved source context.

The first scenario is `helsinki_bus_disruption`: a Helsinki bus/tram traffic app attaches approved files or sanitized adapter outputs and asks OPE to rank forecastable disruption questions.

## Local Commands

```bash
python3 scripts/ope.py agent-integrate --scenario helsinki_bus_disruption
python3 scripts/ope.py agent-integrate --view candidates
python3 scripts/ope.py agent-integrate --view validation
python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output
```

The accepted guided case returns:

- `forecastId`
- `questionId`
- `forecastCardCommand`
- `lifecycleBundleCommand`
- `toolCallCount`
- blocker codes for non-accepted cases

## How OPE Answers "What Can Be Forecasted"

OPE returns candidate contracts, not free-form oracle prose. Each candidate has:

- a normalized future-facing question
- one of `forecastable`, `needs_clarification`, `blocked`, or `rejected`
- exact reason codes
- required source roles
- next action guidance
- whether forecast artifacts are allowed

For the Helsinki starter pack, this candidate is forecastable:

```text
Will HSL surface transit exceed the beta delay threshold during morning peak on {service_date}?
```

Vague prompts such as `Will transit be bad next week?` return `needs_clarification` because geography, threshold, and service window are underspecified.

## Validation

Candidate validation checks:

- future boundary
- resolvability
- source policy
- source roles
- leakage
- baseline feasibility
- claim boundary

The checked reason-code set includes missing threshold, ambiguous service window, vague geography, missing resolution source, unapproved source, raw credential value, raw SQL query, unsafe adapter output, private row exposure, post-outcome evidence, past-tense question, and unresolvable outcome.

## Starter Source Roles

The Helsinki starter pack binds three required source roles:

- `weather_forecast`
- `historical_delay_baseline`
- `transit_delay_outcome`

`transit_delay_outcome` is resolution-only. It must not be accepted as forecast-time evidence.

## MCP Tools

The local MCP stdio scaffold exposes equivalent envelope-backed tools:

- `ope_agent_integration_readiness`
- `ope_agent_integration_candidates`
- `ope_agent_integration_guided_forecast`

These tools accept only safe selector arguments such as scenario and guided case. They do not accept credentials, raw private rows, raw SQL, hidden live fetches, hosted runtime behavior, or private-source execution.

## Claim Boundary

The integration surface is local CLI/MCP only. It does not upgrade quality, calibration, hosted runtime, production-readiness, or generated-runtime-type claims. The first success target is a fast first forecast card, not a calibrated forecasting claim.
