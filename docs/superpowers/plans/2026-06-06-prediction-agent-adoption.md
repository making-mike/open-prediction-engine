# Prediction Agent Adoption Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make OPE easier for coding agents to evaluate and adopt when building prediction features in any host project.

**Architecture:** Add one checked, domain-agnostic adoption surface that projects to a root capability manifest, compact fit explanation, root agent quickstart, extension point guidance, bring-your-own-model guidance, and a five-minute adoption evaluation. Keep the surface read-only and local; do not add hosted runtime, frontend, scheduler, or trained-model claims.

**Tech Stack:** Python 3.12 standard library, JSON Schema contracts under `spec/`, generated fixtures under `spec/fixtures/generated/`, root Markdown/JSON docs, and local CLI wrappers in `scripts/ope.py`.

---

### Task 1: Checked Adoption Contract

**Files:**
- Create: `spec/prediction-agent-adoption.schema.json`
- Create: `scripts/generate_prediction_agent_adoption.py`
- Create: `scripts/check_prediction_agent_adoption.py`

- [x] **Step 1: Write failing check**

Run: `python3 scripts/check_prediction_agent_adoption.py`
Expected: FAIL with `prediction agent adoption generator is missing`.

- [x] **Step 2: Add schema and generator**

Implement `build_prediction_agent_adoption()` with capability manifest, fit decision, extension points, BYO-model path, compact entrypoints, adoption evaluation, summary, and execution boundary.

- [x] **Step 3: Verify check passes**

Run: `python3 scripts/check_prediction_agent_adoption.py`
Expected: PASS with `checked prediction agent adoption`.

### Task 2: Agent-Facing Artifacts And CLI

**Files:**
- Create: `AGENT_QUICKSTART.md`
- Create: `ope.capabilities.json`
- Modify: `scripts/ope.py`

- [x] **Step 1: Add root artifacts**

Create a concise root quickstart and checked capability manifest that match the generated adoption surface.

- [x] **Step 2: Add CLI front doors**

Add `explain-fit`, `capabilities`, and `adoption-eval` commands. Keep `explain-fit` compact by default and JSON output explicit.

- [x] **Step 3: Verify CLI**

Run:
`python3 scripts/ope.py explain-fit --goal "add predictions to my app"`
`python3 scripts/ope.py capabilities`
`python3 scripts/ope.py adoption-eval --output-format json`

### Task 3: Normal Checks And Documentation

**Files:**
- Modify: `scripts/run_checks.py`
- Modify: `scripts/check_cli.py`
- Modify: `README.md`
- Modify: `PRODUCT.md`
- Modify: `spec/README.md`
- Create: `spec/prediction-agent-adoption.md`
- Modify: `.agents/decisions.md`

- [x] **Step 1: Wire checks**

Add `scripts/check_prediction_agent_adoption.py` and generator drift checks to the canonical suite and CLI smoke checks.

- [x] **Step 2: Update docs and decision log**

Document the general adoption front door and append the architecture decision.

- [x] **Step 3: Run verification**

Run targeted checks, then `python3 scripts/run_checks.py` and `python3 scripts/ope.py check`.
