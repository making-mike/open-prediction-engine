# Setup Engine Front Door

Status: checked.

Milestone 147 implements the domain-agnostic front door for agents that want OPE to set up a reliable prediction engine instead of building an ad hoc risk engine first.

The canonical command shape is:

```bash
python3 scripts/ope.py setup-engine --goal "<host prediction goal>"
python3 scripts/ope.py setup-engine --request spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json --view request
```

The same readback is available through the local adapter surfaces:

```bash
python3 scripts/ope.py agent-call --operation setup_engine --goal "<host prediction goal>"
python3 scripts/ope.py agent-call --operation setup_engine --setup-engine-request spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json --view summary
python3 scripts/ope.py mcp-stdio
```

The checked focused views are:

- `summary`
- `request`
- `contracts`
- `sources`
- `baseline`
- `forecast-card-preview`
- `host-wrapper`
- `claim-boundary`
- `examples`

## Checked Readback

`setup-engine` should answer one question:

```text
Given this host prediction goal and source constraints, what OPE-compatible prediction engine can be set up safely?
```

The compact readback includes:

- `engineSetupStatus`: `checked_readback`.
- `inputMode`: `goal_text` or `structured_request`.
- `requestSummary`: whether the request is goal-only, source-intake-ready, needs approval, needs clarification, or blocked by unsafe inputs.
- `candidateForecastContracts`: future-facing forecast contract candidates with close-time and resolution-rule hints.
- `requiredSourceRoles`: forecast-time, baseline, and resolution-only source roles the host must provide or approve.
- `baselineGuidance`: the simplest baseline OPE can start with before any stronger method is promoted.
- `forecastCardPreview`: the safe card shape a host can render before a forecast exists, with probability, forecast IDs, confidence labels, quality claims, calibration claims, credentials, raw private rows, and raw SQL explicitly blocked.
- `hostWrapper`: the shape a host app should render before forecast artifacts exist.
- `exampleGoals`: compact projections from the generic prediction-goal catalog.
- `followUpSurfaces`: compatible next commands such as `explain-fit`, `capabilities`, `agent-implementation-kit`, and `prediction-feature-setup`.
- `claimBoundary`: what the readback does not prove yet.

## Domain Boundary

The readback must stay domain-agnostic. Domain examples may use transit, logistics, stockouts, demand risk, SLA breach risk, churn risk, berth availability, or weather-sensitive operations, but those examples must use the same reusable setup fields.

Domain-specific details belong in extension containers or example records. They must not become required top-level setup-engine fields unless they apply across prediction domains.

## Structured Request Input

When the caller has concrete host-app context, use `--request` instead of only `--goal`. The checked request schema accepts:

- `goal`
- `decisionContext`
- `outcome`
- `horizon`
- `sourceHints`
- `resolutionHint`
- `baselineHint`
- `executionBoundary`

The request path accepts source references and safety flags, not private rows, credential values, raw SQL, hidden live fetch instructions, or forecast-artifact creation requests. Accepted request examples report `ready_for_source_intake`; unsafe examples report `blocked_by_unsafe_inputs`.

## Forecast-Card Preview

The preview view is for host UIs and agents that need to know what they may render before forecast execution:

```bash
python3 scripts/ope.py setup-engine --request spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json --view forecast-card-preview
```

This returns question, outcome, horizon, resolution-rule, source-readiness, baseline-readiness, and claim-boundary fields. It does not return a forecast ID, probability, confidence label, model-quality claim, calibration claim, or hidden forecast artifact.

## Non-Goals

`setup-engine` must not:

- create forecast artifacts by default;
- fetch live data;
- start a hosted service or network listener;
- store credential values, raw SQL, or raw private rows;
- claim a trained model exists out of the box;
- claim forecast quality or calibration before resolved comparable evidence exists;
- replace the host app's UI, runtime, scheduler, notifications, or source connectors.

## Implementation Notes

`setup-engine` is a checked read-only surface. It keeps `explain-fit`, `capabilities`, `agent-implementation-kit`, and `prediction-feature-setup` compatible as setup-intent follow-up commands rather than competing front doors.

Use the catalog readback when an agent needs generic examples before mapping a host app goal:

```bash
python3 scripts/ope.py prediction-goal-catalog
python3 scripts/ope.py setup-engine --view examples
```

The checked artifacts are:

- `spec/setup-engine.schema.json`
- `spec/setup-engine-request.schema.json`
- `spec/prediction-goal-catalog.schema.json`
- `spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json`
- `spec/fixtures/setup-engine-requests/blocked-raw-crm-request.json`
- `spec/fixtures/generated/setup-engine/ope-setup-engine.generated.json`
- `spec/fixtures/generated/prediction-goal-catalog/ope-prediction-goal-catalog.generated.json`
- `scripts/generate_setup_engine.py`
- `scripts/generate_prediction_goal_catalog.py`
- `scripts/check_setup_engine.py`
- `scripts/check_prediction_goal_catalog.py`
- CLI: `python3 scripts/ope.py setup-engine`
- Catalog CLI: `python3 scripts/ope.py prediction-goal-catalog`
- Agent call: `python3 scripts/ope.py agent-call --operation setup_engine`
- Local MCP tool: `ope_setup_engine`
