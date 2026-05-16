# Architecture Patterns Reference

Detailed reference for single-agent and multi-agent architecture patterns in the agentic economy.

Transfer rule: keep these patterns as design vocabulary, not as a mandate. A new repository should choose the smallest orchestration pattern that fits its actual contract, latency, audit, and failure-isolation needs.

---

## Single-Agent Reasoning Loops

### ReAct (Reason and Act)

```
┌─────────────┐
│   Observe    │◄──────────────┐
│  (input/env) │               │
└──────┬───────┘               │
       ▼                       │
┌─────────────┐               │
│   Reason    │               │
│ (analyze +  │               │
│  identify   │               │
│    gaps)    │               │
└──────┬───────┘               │
       ▼                       │
┌─────────────┐               │
│     Act     │               │
│ (tool call  │───────────────┘
│  or query)  │
└─────────────┘
```

**When to use:** Tasks requiring an audit trail, debugging visibility, or when the action space is uncertain.

**Token cost:** 5-7 LLM calls per task cycle.

---

### Planning-Based

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Decompose  │────▶│   Execute   │────▶│  Synthesize  │
│  full plan  │     │  each step  │     │   results    │
└─────────────┘     └─────────────┘     └─────────────┘
```

**When to use:** Well-defined tasks where the goal structure is predictable.

**Token cost:** 3-4 LLM calls (lower than ReAct).

---

### Reflection

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Generate   │────▶│   Critique  │────▶│   Refine    │
│   draft     │     │  (self-eval │     │  (improved  │
│             │     │   mode)     │     │   output)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

**When to use:** Quality-critical outputs (code review, document generation, analysis).

**Token cost:** 2-3× single-pass.

---

### Reflexion

Same as Reflection, but adds **external evaluation signals** (test results, user feedback, metric checks) to the critique loop.

**When to use:** Iterative problem-solving where ground truth can be measured.

---

## Multi-Agent Patterns

### Orchestrator-Worker

```
                ┌──────────────┐
                │ Orchestrator │
                └──────┬───────┘
           ┌───────────┼───────────┐
           ▼           ▼           ▼
      ┌─────────┐ ┌─────────┐ ┌─────────┐
      │Worker A │ │Worker B │ │Worker C │
      │(search) │ │(analyze)│ │(write)  │
      └─────────┘ └─────────┘ └─────────┘
```

- Central supervisor routes sub-tasks
- Workers are specialized and stateless
- Orchestrator aggregates results

---

### Sequential Workflow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│Agent A  │────▶│Agent B  │────▶│Agent C  │────▶│ Output  │
│(extract)│     │(transform)    │(validate)│     │         │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
```

- Each agent builds on previous output
- Predictable, debuggable flow
- Best for ETL and data pipelines

---

### Hierarchical Teams

```
            ┌────────────────┐
            │ Top Supervisor │
            └───────┬────────┘
        ┌───────────┴───────────┐
        ▼                       ▼
  ┌───────────┐          ┌───────────┐
  │Supervisor │          │Supervisor │
  │  Team A   │          │  Team B   │
  └─────┬─────┘          └─────┬─────┘
    ┌───┴───┐              ┌───┴───┐
    ▼       ▼              ▼       ▼
 Agent    Agent          Agent    Agent
  A1       A2             B1       B2
```

- Multiple supervisors manage specialized clusters
- Best for complex multi-domain projects

---

### Parallel Workflows

```
           ┌─────────┐
     ┌────▶│Agent A  │────┐
     │     └─────────┘    │
┌────┴───┐                ▼    ┌─────────┐
│Splitter│          ┌─────────┐│ Merger  │
└────┬───┘     ┌───▶│Agent B  │└────┬────┘
     │         │    └─────────┘     │
     └─────────┘                    ▼
               ┌───▶┌─────────┐  Output
               │    │Agent C  │
               │    └─────────┘
               └────────────────────┘
```

- Independent tasks processed simultaneously
- Results merged at the end
- Best for high-volume independent processing

---

### Collaborative Swarms

- Distributed reasoning with no central controller
- Agents negotiate resource allocation
- Emergent coordination through shared protocols
- Best for real-time supply chain or market optimization

---

## Decision Guide

```
Is the task simple and linear?
  ├── YES → Single-agent (ReAct or Planning)
  └── NO → Is output quality critical?
        ├── YES → Reflection / Reflexion loop
        └── NO → Multi-agent needed?
              ├── Predictable pipeline → Sequential
              ├── Independent sub-tasks → Parallel
              ├── General task routing → Orchestrator-Worker
              ├── Multi-domain complexity → Hierarchical
              └── Real-time negotiation → Swarm
```

---

## Performance Degradation Warning

Single-agent loops can degrade materially on long, multi-step, or adversarial tasks. Monitor task completion rates, validation failures, retry counts, and human-review reversals; switch to multi-agent coordination only when the measured failure mode justifies the added complexity.

## Coordination Best Practices

1. **Shared data layer** — All agents read/write to common state
2. **Explicit handoff protocols** — State machines or orchestrators manage transitions
3. **Small, distributed agents** — Keep decision scope narrow for transparency
4. **JSON schema validation** — Validate data at every agent-to-agent boundary
5. **Failure isolation** — Single agent failure must not collapse the workflow
