# Agent Implementation Kit

Status: checked local readback for coding agents adding OPE-backed prediction features.

The kit gives agents a compact path from "this host feature needs prediction" to existing OPE lifecycle surfaces. It does not create a new forecast execution path. Question discovery stops at candidate and validation readbacks; accepted candidates route into existing source intake, setup benchmark, method decision, forecast execution, resolution, scoring, and calibration surfaces.

## Commands

```bash
python3 scripts/ope.py agent-implementation-kit
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
question-discovery intake
candidate validation
existing OPE lifecycle commands
forecast-card readback
```

The wrapper should call existing CLI, in-process, agent-call, or local MCP surfaces. It should not open a network listener, store credential values, start an unbounded worker, or write raw CRUD rows.
