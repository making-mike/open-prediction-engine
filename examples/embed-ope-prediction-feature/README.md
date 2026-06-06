# Embed OPE Prediction Feature Example

This example shows a host project how to call OPE locally as an embedded prediction feature. It uses the stable `prediction-feature-setup` contract, then reads an existing `forecast-card` when OPE returns an accepted setup response.

It is intentionally small and copyable:

```bash
python3 examples/embed-ope-prediction-feature/host_wrapper.py \
  --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json \
  --output-format json
```

The accepted path calls:

```bash
python3 scripts/ope.py prediction-feature-setup --view response --case accepted
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

The wrapper treats host input as a feature-intent readback, not as private data intake. It accepts approved source references and resolution hints, then lets OPE return the compact setup response and forecast-card command.

## Boundaries

This example has no hosted service, no network listener, no hidden worker, no credential values, no raw private rows, no raw SQL, no post-outcome evidence as forecast evidence, and no production forecast-quality claim. It does not create forecast artifacts; the accepted sample reads the existing checked `forecast-1102` card.

Blocked fixtures show unsafe host inputs:

- `blocked_raw_credentials.json`
- `blocked_raw_private_rows.json`
- `blocked_raw_sql.json`
- `blocked_unapproved_source.json`
- `blocked_post_outcome_evidence.json`
- `blocked_hosted_runtime.json`

Run one blocked path:

```bash
python3 examples/embed-ope-prediction-feature/host_wrapper.py \
  --request examples/embed-ope-prediction-feature/fixtures/blocked_raw_credentials.json \
  --output-format json
```

The blocked response stops before any OPE command is executed and returns no forecast card.

## Copying Into A Host App

Use `host_wrapper.py` as the minimal shape for an embedded local integration:

1. Convert host app intent into `hostFeatureIntent`, `decisionToSupport`, approved source references, resolution hints, and a response-size budget.
2. Reject inline credentials, raw rows, raw SQL, unapproved sources, post-outcome forecast evidence, and hosted-runtime assumptions before calling OPE.
3. Call `prediction-feature-setup` for a compact setup response.
4. When accepted, read the returned forecast card and lifecycle bundle commands.
5. Keep downstream UI labels honest: current quality claims remain sample-size-blocked.

The expected summary fixtures pin the accepted and blocked shapes without requiring a package install or a hosted OPE runtime.
