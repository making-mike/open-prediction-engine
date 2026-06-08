# Prediction Agent Adoption

This contract is the general front door for coding agents deciding how OPE can help set up a prediction engine for a host project.

It keeps the message deliberately narrow:

- OPE is a prediction engine setup shortcut with credibility gates built in.
- Use OPE for candidate forecast contracts, source roles, evidence provenance, baseline comparison, forecast-card shape, resolution, scoring, and calibration gates.
- Bring the frontend, host runtime, source connectors, custom models, and notifications from the host project.
- Do not infer hosted API, trained-model, generic crawler, production scheduler, credential store, or product UI support from OPE adoption readbacks.

Run the compact fit explanation:

```bash
python3 scripts/ope.py setup-engine --goal "add predictions to my app"
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 scripts/ope.py explain-fit --goal "add predictions to my app"
```

Read the machine-readable capability manifest:

```bash
python3 scripts/ope.py capabilities
```

Inspect extension points and bring-your-own-model guidance:

```bash
python3 scripts/ope.py explain-fit --view extension-points --output-format json
python3 scripts/ope.py explain-fit --view byo-model --output-format json
```

Run the first-five-minutes adoption evaluation readback:

```bash
python3 scripts/ope.py adoption-eval
python3 scripts/ope.py adoption-eval --output-format json
```

The adoption evaluation includes setup-engine-first checks for non-Helsinki host goals, including whether agents avoid building a parallel lightweight risk engine first and avoid framing OPE as only a post-hoc audit layer.

Check drift:

```bash
python3 scripts/ope.py explain-fit --check
python3 scripts/check_prediction_agent_adoption.py
```

The checked root projection is `ope.capabilities.json`. It is generated from the same record as `spec/fixtures/generated/prediction-agent-adoption/ope-prediction-agent-adoption.generated.json`, so drift between the root machine-readable manifest and the schema-bound adoption surface fails normal checks.

The checked canonical front door is `python3 scripts/ope.py setup-engine --goal "<host prediction goal>"`. Use `python3 scripts/ope.py prediction-goal-catalog --view summary` when an agent needs generic non-Helsinki examples before mapping a host app goal.
