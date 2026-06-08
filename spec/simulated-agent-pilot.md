# Simulated Agent Pilot

This checked readback records one user-authorized simulated developer-agent prompt plus seven generated prompts against the stable `prediction-feature-setup` and `setup-engine` adoption paths.

It is adoption-friction evidence only. It is not a real human pilot session, does not write pilot-ledger rows, and does not upgrade forecast quality, calibration, hosted-runtime, generated-types, or private-source execution claims.

Read the summary:

```bash
python3 scripts/ope.py simulated-agent-pilot --section summary
```

Read the user-provided prompt simulation:

```bash
python3 scripts/ope.py simulated-agent-pilot --section user-prompt
```

The eight simulated sessions cover the current compact setup outcomes and the engine setup shortcut comprehension gate:

- `needs_clarification`: the user-provided Helsinki bus-by-stop late request is normalized to `2026-06-06` but needs stop/route/window scope and approved planned-work source references.
- `accepted`: an approved-source Helsinki transit dashboard prompt reaches `forecast-1102` / `question-1102`.
- `blocked`: raw credential, raw private row, and raw SQL-style source handling is blocked.
- `rejected`: a retrospective/non-resolvable question is rejected as an OPE forecast request.
- `response_too_large`: an oversized all-routes/all-stops request is redirected to a narrower readback or larger approved budget.
- non-Helsinki setup prompts: retail stockout, support SLA breach, and seaport berth availability prompts test whether agents run `setup-engine` before custom risk-engine work.
- comprehension confusion: one prompt records a parallel-risk-engine-first signal, and one records an audit-layer-only signal.

The setup comprehension fields report whether the simulated agent used setup-engine before proposing a custom engine, whether it framed OPE as audit-only, and whether it could separate OPE-owned contracts, evidence roles, baselines, forecast-card shape, resolver, scorer, and calibration gate from host-owned UI, sources, runtime, notifications, and optional custom methods.

Token counts use approximate whitespace tokens. Time is a deterministic estimate for stable fixture checks, not a measured benchmark.

Normal checks:

```bash
python3 scripts/generate_simulated_agent_pilot.py --check
python3 scripts/check_simulated_agent_pilot.py
```
