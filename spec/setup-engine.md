# Setup Engine Front Door

Status: checked.

Milestone 147 implements the domain-agnostic front door for agents that want OPE to set up a reliable prediction engine instead of building an ad hoc risk engine first.

The canonical command shape is:

```bash
python3 scripts/ope.py setup-engine --goal "<host prediction goal>"
```

The same readback is available through the local adapter surfaces:

```bash
python3 scripts/ope.py agent-call --operation setup_engine --goal "<host prediction goal>"
python3 scripts/ope.py mcp-stdio
```

The checked focused views are:

- `summary`
- `contracts`
- `sources`
- `baseline`
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
- `candidateForecastContracts`: future-facing forecast contract candidates with close-time and resolution-rule hints.
- `requiredSourceRoles`: forecast-time, baseline, and resolution-only source roles the host must provide or approve.
- `baselineGuidance`: the simplest baseline OPE can start with before any stronger method is promoted.
- `hostWrapper`: the shape a host app should render before forecast artifacts exist.
- `exampleGoals`: compact projections from the generic prediction-goal catalog.
- `followUpSurfaces`: compatible next commands such as `explain-fit`, `capabilities`, `agent-implementation-kit`, and `prediction-feature-setup`.
- `claimBoundary`: what the readback does not prove yet.

## Domain Boundary

The readback must stay domain-agnostic. Domain examples may use transit, logistics, stockouts, demand risk, SLA breach risk, churn risk, berth availability, or weather-sensitive operations, but those examples must use the same reusable setup fields.

Domain-specific details belong in extension containers or example records. They must not become required top-level setup-engine fields unless they apply across prediction domains.

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
- `spec/prediction-goal-catalog.schema.json`
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
