# Prediction Feature Setup

Status: checked compact contract for host projects adding an OPE-backed prediction feature.

This surface gives a coding agent one small request/response contract before it decides whether a host project can proceed to an OPE forecast-card readback. It is a bridge over existing agent integration, candidate validation, guided forecast, forecast-card, and lifecycle-bundle read surfaces. It is not a new execution path.

The generated fixture lives at `spec/fixtures/generated/prediction-feature-setup/ope-prediction-feature-setup.generated.json` and is validated by:

```bash
python3 scripts/generate_prediction_feature_setup.py --check
python3 scripts/check_prediction_feature_setup.py
python3 scripts/ope.py prediction-feature-setup --check
```

## Request Contract

`prediction-feature-setup-request.schema.json` describes the compact host intent an agent may submit:

- `hostFeatureIntent`: what the host app wants the prediction feature to support.
- `decisionToSupport`: the downstream decision that would use the forecast.
- `approvedSourceRefs`: references to caller-approved source manifests, adapter outputs, or source bindings.
- `resolutionHints`: the outcome or proxy source the host expects to use later.
- `responseSizeBudgetBytes`: the maximum response size the caller wants for routine tool context.

The request contract rejects credential values, raw private rows, and raw SQL. Source references must stay opaque and caller-owned.

## Response Cases

`prediction-feature-setup-response.schema.json` covers five checked cases:

- `accepted`: returns `forecast-1102` / `question-1102` plus forecast-card and lifecycle-bundle read commands.
- `needs_clarification`: asks for missing decision, source-role, or resolution details.
- `blocked`: stops unsafe source, credential, raw SQL, private-row, hosted-runtime, or post-outcome evidence paths.
- `rejected`: explains why the intent is not a resolvable forecast request.
- `response_too_large`: returns a compact retry path when the response budget is exceeded.

Each response carries exact reason codes, required source roles, next actions, and claim boundaries. Accepted responses reuse existing forecast records; they do not create forecast artifacts during this readback.

## Interfaces

The local CLI surface is:

```bash
python3 scripts/ope.py prediction-feature-setup
python3 scripts/ope.py prediction-feature-setup --view response --case accepted
```

The transport-neutral agent envelope is:

```bash
python3 scripts/ope.py agent-call --operation prediction_feature_setup
```

Local MCP support is guidance-only for this milestone. MCP-capable hosts should wrap the same `prediction_feature_setup` agent-call operation when the local stdio scaffold adds a dedicated tool; until then, `spec/agent-adapter-protocol-map.md` records the intended boundary.

## Boundary

This contract does not accept credential values, raw private rows, raw SQL, hidden live fetch requests, hosted runtime flags, or private-source execution instructions. It does not open a network listener, create a forecast artifact path, or upgrade quality/calibration claims.
