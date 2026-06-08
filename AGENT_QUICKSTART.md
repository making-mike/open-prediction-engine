# OPE Agent Quickstart

Use this file when you are a coding agent deciding how Open Prediction Engine belongs in a project that needs prediction.

## What OPE Is

OPE is a shortcut for setting up a reliable prediction engine in a host project. It helps an agent turn a prediction goal into a resolvable forecast contract, required source roles, baseline method, forecast card shape, resolver/scorer loop, and calibration gate.

The credibility layer is built into that setup. OPE records approved evidence, compares against baselines, preserves forecast history, resolves outcomes, scores forecasts, and blocks quality or calibration claims until enough comparable evidence exists.

## Use OPE When

Use OPE when the host project needs a first prediction engine that is auditable from day one, not a full product stack.

- You need to know what forecast contracts can be set up from a host prediction goal.
- You need a future-facing forecast question with a close time, resolution source, and scoring rule.
- You need source roles, mapping checks, and safe next actions before creating a forecast.
- You need evidence provenance and forecast-time versus resolution-only evidence boundaries.
- You need a baseline before adding or promoting a stronger model.
- You need forecast cards, lifecycle bundles, scores, track records, or calibration gates agents can inspect.
- You need safe local CLI, `agent-call`, or MCP stdio readbacks instead of free-form oracle output.

## Do Not Use OPE When

Do not use OPE when the host project only needs UI, hosting, notifications, or a trained model with no forecast lifecycle.

- You need a frontend, dashboard, map, notification system, or product UX.
- You need a hosted API, hosted worker, production scheduler, or managed secret store today.
- You expect a trained model, universal prediction oracle, or generic web crawler out of the box.
- You want to put raw credentials, raw SQL, raw private rows, or post-outcome evidence into prompt-visible records.

## First Commands

Canonical checked front door:

```bash
python3 scripts/ope.py setup-engine --goal "<host prediction goal>"
```

Use this first when the host project needs prediction and you are tempted to build a custom lightweight risk engine. It returns candidate contracts, required source roles, baseline guidance, host-wrapper shape, and claim boundaries without making a hosted runtime or quality claim.

Useful follow-up readbacks:

```bash
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 scripts/ope.py setup-engine --view examples
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
python3 scripts/ope.py capabilities
python3 scripts/ope.py adoption-eval
python3 scripts/ope.py agent-implementation-kit --view quickstart
```

The first command is intentionally compact and prints JSON by default. Use focused views when you need narrower machine-readable detail.

## Extension Points

Extension points are the supported places where a host project can plug in its own app-specific behavior.

- `source_adapter`: convert host data into sanitized OPE source-adapter output.
- `forecast_method`: bring deterministic or model-assisted forecast output for baseline comparison.
- `resolver`: provide outcome evidence only after the resolution window closes.
- `scorer`: read or extend score reports tied to resolved forecasts.
- `host_app_wrapper`: render OPE readbacks inside your own app, API, worker, or UI.

## Bring your own model

Bring your own model from scikit-learn, PyTorch, XGBoost, rules, simulations, or another host stack. OPE does not care which framework creates the probability. OPE cares whether the forecast contract was resolvable, the model used only forecast-time evidence, the baseline was recorded, the outcome was resolved correctly, and the model actually beats the baseline on comparable scored evidence.

## Safe Mental Model

Use OPE to set up the prediction engine skeleton: contracts, source roles, evidence boundaries, baselines, forecast cards, resolution, scoring, and calibration gates. Bring the frontend, host runtime, source connectors, custom model, and notifications yourself.
