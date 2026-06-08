# Agent Implementation Kit

Status: checked local readback for coding agents adding OPE-backed prediction features.

The kit gives agents a compact path from "this host feature needs prediction" to existing OPE lifecycle surfaces. It does not create a new forecast execution path. Question discovery stops at candidate and validation readbacks; accepted candidates route into existing source intake, setup benchmark, method decision, forecast execution, resolution, scoring, and calibration surfaces.

For external coding agents, start with the setup-engine front door:

```bash
python3 scripts/ope.py setup-engine --goal "add predictions to my app"
```

Then use the implementation-kit quickstart when the host app is ready to wire the returned setup shape into local OPE surfaces:

```bash
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 scripts/ope.py agent-implementation-kit --view quickstart
```

The catalog readback shows generic forecastable, needs-clarification, blocked, and rejected host goals. The implementation-kit readback returns the minimum safe follow-up sequence: render the setup-first host wrapper, run the guided accepted path, read the forecast card, and inspect the lifecycle bundle only when the host feature needs provenance or method context.

## Commands

```bash
python3 scripts/ope.py agent-implementation-kit
python3 scripts/ope.py agent-implementation-kit --view quickstart
python3 scripts/ope.py agent-implementation-kit --view manual
python3 scripts/ope.py agent-implementation-kit --view intake
python3 scripts/ope.py agent-implementation-kit --view candidates
python3 scripts/ope.py agent-implementation-kit --view validation
python3 scripts/ope.py agent-implementation-kit --view adapters
python3 scripts/ope.py agent-implementation-kit --view templates
python3 scripts/ope.py agent-implementation-kit --view blocked
python3 scripts/ope.py agent-implementation-kit --view boundary
python3 scripts/ope.py agent-implementation-kit --check
```

The checked fixture is:

```text
spec/fixtures/generated/agent-implementation-kit/ope-agent-implementation-kit.generated.json
```

## Embedded Service Template

Use this shape when a host application wants to keep OPE inside one small local module:

```text
host feature intent
approved source refs
setup-engine readback
setupEnginePlan rendered in the host wrapper
prediction-feature setup response
forecast-card readback
lifecycle-bundle readback when provenance or method context is needed
```

The wrapper should call existing CLI, in-process, agent-call, or local MCP surfaces. It should render OPE setup readbacks, pass approved source references, and keep OPE scoring and calibration semantics inside OPE. It should not open a network listener, store credential values, start an unbounded worker, write raw CRUD rows, or implement an untracked host risk engine.

The quickstart wrapper outline uses this call sequence:

```text
setup_engine
render_setup_engine_host_wrapper
prediction_feature_setup_response
forecast_card_readback
lifecycle_bundle_readback
```
