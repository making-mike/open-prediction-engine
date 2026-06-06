# Prediction Agent Adoption

This contract is the general front door for coding agents deciding whether OPE is useful for a host project that needs prediction.

It keeps the message deliberately narrow:

- OPE is a prediction credibility layer.
- Use OPE for forecast contracts, evidence provenance, baseline comparison, resolution, scoring, and calibration gates.
- Bring the frontend, host runtime, source connectors, custom models, and notifications from the host project.
- Do not infer hosted API, trained-model, generic crawler, production scheduler, credential store, or product UI support from OPE adoption readbacks.

Run the compact fit explanation:

```bash
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

Check drift:

```bash
python3 scripts/ope.py explain-fit --check
python3 scripts/check_prediction_agent_adoption.py
```

The checked root projection is `ope.capabilities.json`. It is generated from the same record as `spec/fixtures/generated/prediction-agent-adoption/ope-prediction-agent-adoption.generated.json`, so drift between the root machine-readable manifest and the schema-bound adoption surface fails normal checks.
