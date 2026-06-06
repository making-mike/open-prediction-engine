# OPE Agent Quickstart

Use this file when you are a coding agent deciding whether Open Prediction Engine belongs in a project that needs prediction.

## What OPE Is

OPE is a prediction credibility layer. It helps a host project turn a prediction idea into a resolvable forecast contract, bind approved evidence, compare against a baseline, preserve forecast history, resolve outcomes, score forecasts, and gate quality or calibration claims until enough comparable evidence exists.

## Use OPE When

Use OPE when the host project needs prediction credibility, not a full product stack.

- You need a future-facing forecast question with a close time, resolution source, and scoring rule.
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

```bash
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
python3 scripts/ope.py capabilities
python3 scripts/ope.py adoption-eval
python3 scripts/ope.py agent-implementation-kit --view quickstart
```

The first command is intentionally compact. Use `--output-format json` or the focused views when you need machine-readable detail.

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

Use OPE for contracts, evidence, baselines, resolution, scoring, and calibration gates. Bring the frontend, host runtime, source connectors, custom model, and notifications yourself.
