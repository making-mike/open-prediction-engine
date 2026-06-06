# Simulated Agent Pilot

This checked readback records one user-authorized simulated developer-agent prompt plus four generated prompts against the stable `prediction-feature-setup` path.

It is adoption-friction evidence only. It is not a real human pilot session, does not write pilot-ledger rows, and does not upgrade forecast quality, calibration, hosted-runtime, generated-types, or private-source execution claims.

Read the summary:

```bash
python3 scripts/ope.py simulated-agent-pilot --section summary
```

Read the user-provided prompt simulation:

```bash
python3 scripts/ope.py simulated-agent-pilot --section user-prompt
```

The five simulated sessions cover the current compact setup outcomes:

- `needs_clarification`: the user-provided Helsinki bus-by-stop late request is normalized to `2026-06-06` but needs stop/route/window scope and approved planned-work source references.
- `accepted`: an approved-source Helsinki transit dashboard prompt reaches `forecast-1102` / `question-1102`.
- `blocked`: raw credential, raw private row, and raw SQL-style source handling is blocked.
- `rejected`: a retrospective/non-resolvable question is rejected as an OPE forecast request.
- `response_too_large`: an oversized all-routes/all-stops request is redirected to a narrower readback or larger approved budget.

Token counts use approximate whitespace tokens. Time is a deterministic estimate for stable fixture checks, not a measured benchmark.

Normal checks:

```bash
python3 scripts/generate_simulated_agent_pilot.py --check
python3 scripts/check_simulated_agent_pilot.py
```
