# Agent Guidance Loop

Status: checked local readback.

`agent-guidance` turns the simulated pilot lesson into a concrete agent-facing loop: OPE does not replace the calling agent's intelligence; it gives the agent classifications, missing inputs, safe questions, required source roles, and next commands.

Read the summary:

```bash
python3 scripts/ope.py agent-guide --section summary
```

Read the domain-agnostic setup clarification flow:

```bash
python3 scripts/ope.py agent-guide --section generic
```

Read the Helsinki prompt example guidance:

```bash
python3 scripts/ope.py agent-guide --case needs_clarification
```

Read the instruction pack:

```bash
python3 scripts/ope.py agent-guide --section instructions
```

## What It Adds

- Milestone 142: a checked agent guidance contract over accepted, clarification, blocked, rejected, and response-too-large cases.
- Milestone 143: a prompt-to-question planner for messy developer prompts.
- Milestone 144: a Helsinki bus narrowing flow from broad request to scoped forecast setup.
- Milestone 145: an agent instruction pack with do/don't rules and a minimum safe loop.
- Milestone 156: a domain-agnostic setup flow that asks reusable host-goal, outcome, horizon, source, baseline, and resolution questions before agents specialize to an example domain.

## Generic Setup Flow

For any host prediction feature, OPE tells the calling agent to ask:

- What decision will this prediction support in the host app?
- What exact future outcome, threshold, entity scope, and horizon should resolve the forecast?
- Which approved source references can provide forecast-time evidence?
- Which approved historical source can define the baseline before stronger methods are considered?
- Which resolution source will confirm the outcome after the forecast window closes?

After those answers exist as approved source references, the agent should run `setup-engine` for the host goal instead of inventing an untracked risk engine.

## Helsinki Narrowing

The Helsinki flow remains a worked example. For the broad prompt asking which Helsinki buses will be 2+ minutes late on `2026-06-06`, OPE tells the calling agent to ask:

- Which route, stop, or bounded service area should this cover?
- What time window on `2026-06-06` should count for the 2+ minute lateness threshold?
- Which approved planned-work source reference can OPE use?
- Which outcome source will confirm whether each scoped bus was 2+ minutes late?

After those answers exist as approved source references, the agent can retry the compact prediction-feature setup path.

## Boundary

This surface does not execute sources, fetch live data, store credentials, store raw private rows, accept raw SQL, create forecast artifacts, start hosted runtime, or upgrade forecast-quality claims. It is a readback that helps the calling agent decide the next safe move.

Normal checks:

```bash
python3 scripts/generate_agent_guidance.py --check
python3 scripts/check_agent_guidance.py
```
