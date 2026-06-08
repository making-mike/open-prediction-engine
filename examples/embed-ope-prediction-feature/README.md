# Embed OPE Prediction Feature Example

This example shows a host project how to call OPE locally as an embedded prediction feature. It starts with `setup-engine`, renders the returned engine setup plan, then uses the stable `prediction-feature-setup` contract and reads an existing `forecast-card` only after the setup plan has enough approved host inputs.

It is intentionally small and copyable:

```bash
python3 examples/embed-ope-prediction-feature/host_wrapper.py \
  --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json \
  --output-format json
```

The accepted path calls:

```bash
python3 scripts/ope.py setup-engine --goal "Show a dispatch-risk prediction in a logistics operations dashboard."
python3 scripts/ope.py prediction-feature-setup --view response --case accepted
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

The wrapper treats host input as a feature-intent readback, not as private data intake. It accepts approved source references, outcome definition, and resolution hints, then lets OPE return the setup plan, compact setup response, and forecast-card command.

## Host-Facing Data Shape

The wrapper output contains `setupEnginePlan` before `setupResponse` or `forecastCard`. This is the host-facing data shape. A host app should render this setup-engine readback as the prediction setup plan:

- `setupStatus`: checked setup-engine status.
- `candidateContracts`: candidate forecast contracts with status, required source roles, baseline method, and next action.
- `sourceRoles`: required OPE source roles such as `forecast_time_signal`, `historical_outcome`, and `resolution_outcome`.
- `baselineStatus`: default baseline, benchmark gate, calibration gate, and stronger-method prerequisites.
- `forecastCardPreview`: fields the app can expect after an accepted setup response, without claiming quality.
- `requiredHostInputs`: source references, outcome definition, resolution hints, and response-size budget the host must supply.
- `warnings`: claim, source, and method-extension boundaries.

## Boundaries

This example has no hosted service, no network listener, no hidden worker, no credential values, no raw private rows, no raw SQL, no post-outcome evidence as forecast evidence, and no production forecast-quality claim. It does not create forecast artifacts; the accepted sample reads the existing checked `forecast-1102` card.

Blocked fixtures show unsafe host inputs:

- `blocked_raw_credentials.json`
- `blocked_raw_private_rows.json`
- `blocked_raw_sql.json`
- `blocked_unapproved_source.json`
- `blocked_missing_source_roles.json`
- `blocked_vague_outcome.json`
- `blocked_post_outcome_evidence.json`
- `blocked_hosted_runtime.json`

Run one blocked path:

```bash
python3 examples/embed-ope-prediction-feature/host_wrapper.py \
  --request examples/embed-ope-prediction-feature/fixtures/blocked_raw_credentials.json \
  --output-format json
```

Credential values, raw private rows, raw SQL, unapproved sources, post-outcome forecast evidence, and hosted-runtime requests stop before any OPE command is executed. Missing source roles and vague outcomes render `setup-engine` first, then stop before `prediction-feature-setup` or any forecast-card read.

## Copying Into A Host App

Use `host_wrapper.py` as the minimal shape for an embedded local integration:

1. Convert host app intent into `hostFeatureIntent`, `decisionToSupport`, approved source references, resolution hints, and a response-size budget.
2. Reject inline credentials, raw rows, raw SQL, unapproved sources, post-outcome forecast evidence, and hosted-runtime assumptions before calling OPE.
3. Call `setup-engine` and render the setup plan before forecast artifacts exist.
4. Check whether the host supplied required source roles and a measurable outcome definition.
5. Call `prediction-feature-setup` for a compact setup response only after the setup plan is actionable.
6. When accepted, read the returned forecast card and lifecycle bundle commands.
7. Keep downstream UI labels honest: current quality claims remain sample-size-blocked.

## Custom Methods

If the host later needs app-specific prediction logic, add it as an OPE method extension behind the method registry, setup benchmark, leakage, approval, and rollback gates. Do not build an untracked route-risk engine in the host wrapper. The wrapper should call OPE, render readbacks, pass approved source references, and leave OPE scoring and calibration semantics inside OPE.

The expected summary fixtures pin the accepted and blocked shapes without requiring a package install or a hosted OPE runtime.
