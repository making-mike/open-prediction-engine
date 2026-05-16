# EU AI Act Compliance Guide

Compliance reference for deploying agentic AI systems under the European Union's Artificial Intelligence Act.

Last reviewed against the EU AI Act Service Desk timeline: 2026-05-16.

This document is deployment guidance, not legal advice. Verify dates and obligations before release because implementing rules, standards, and national enforcement guidance can change.

Transfer rule: for a new repository, keep the risk-classification workflow but replace examples and controls with the new product's actual domain, users, geography, and autonomy level.

---

## Risk Classification

The EU AI Act classifies AI systems by risk level. Most obligations target **High-Risk** systems.

```
┌─────────────────────────────────────────────┐
│              UNACCEPTABLE RISK               │  ← Banned
│  (social scoring, real-time biometric ID     │
│   in public spaces, manipulation)            │
├─────────────────────────────────────────────┤
│                HIGH RISK                     │  ← Heavy regulation
│  (safety-critical, fundamental rights)       │
├─────────────────────────────────────────────┤
│              LIMITED RISK                    │  ← Transparency obligations
│  (chatbots, deepfakes, emotion detection)    │
├─────────────────────────────────────────────┤
│              MINIMAL RISK                    │  ← No specific obligations
│  (spam filters, AI in games)                 │
└─────────────────────────────────────────────┘
```

---

## High-Risk System Criteria

A system is **high-risk** if it:

1. Performs **safety-critical functions** (e.g., vehicle braking/steering, medical devices)
2. Impacts **fundamental rights** (e.g., credit scoring, employment decisions, law enforcement)
3. Is listed in **Annex III** of the Act (biometric identification, critical infrastructure, education, employment, essential services, law enforcement, migration, justice)

---

## Provider Obligations (High-Risk)

### Before Market Placement

- [ ] **Risk Management System** — Comprehensive, covering the full system lifecycle
- [ ] **Data Governance** — Training/test data must be relevant, representative, and free of errors/bias
- [ ] **Technical Documentation** — Demonstrates compliance with all requirements
- [ ] **Record-Keeping** — Automatic logging of system activity with meticulous detail
- [ ] **Conformity Assessment** — Rigorous evaluation (self-assessment or third-party, depending on category)
- [ ] **EU Database Registration** — Register in EU or national AI system database
- [ ] **CE Marking** — Affix CE marking upon successful conformity assessment

### Ongoing Obligations

- [ ] **Quality Management System** — Maintained throughout the system's lifecycle
- [ ] **Post-Market Monitoring** — Continuous monitoring of system performance
- [ ] **Incident Reporting** — Report serious incidents to competent authorities
- [ ] **Documentation Updates** — Keep technical documentation current

---

## GPAI (General-Purpose AI) Obligations

Agents often rely on underlying GPAI models. Providers must:

- [ ] Publish a **summary of training content**
- [ ] Establish a **copyright policy**
- [ ] Provide **technical documentation** to downstream providers (agent developers)

### Systemic Risk Models (>10²⁵ FLOPs)

Additional requirements for models with training compute exceeding 10²⁵ floating-point operations:

- [ ] **Model evaluations** using standardized protocols
- [ ] **Adversarial testing** (red-teaming)
- [ ] **Serious incident reporting** to the AI Office
- [ ] **Cybersecurity protections** appropriate to the risk level

---

## Human Oversight (Article 14)

High-risk AI systems must be designed for effective human oversight.

### Required Capabilities for Overseers

The system must enable the overseer to:

| Requirement | Description |
|---|---|
| **Understanding** | Fully comprehend system capacities and limitations |
| **Anti-Automation Bias** | Tools to avoid over-reliance on AI output |
| **Override** | Ability to disregard, override, or reverse agent output |
| **Intervention** | Stop operation via "stop" button or similar procedure |

### Implementation Patterns

| Pattern | Use Case |
|---|---|
| **Human-in-the-Loop (HITL)** | Control gates for high-stakes actions |
| **Human-on-the-Loop** | Monitoring with intervention capability |
| **Human-over-the-Loop** | Policy setting and exception management |

### Special Requirements

- **Biometric identification systems:** Actions must be verified by **at least two** competent individuals
- **Real-time systems:** Override mechanisms must be accessible with minimal latency

---

## Transparency Obligations (All Risk Levels)

- [ ] Users must be informed when interacting with an AI system
- [ ] AI-generated content (deepfakes, synthetic text) must be labeled
- [ ] Emotion recognition and biometric categorization systems require explicit notification

---

## Penalties

| Violation | Maximum Fine |
|---|---|
| Prohibited AI practices | €35M or 7% of global annual turnover |
| High-risk system non-compliance | €15M or 3% of global annual turnover |
| Incorrect information to authorities | €7.5M or 1% of global annual turnover |

> For SMEs and startups, fines are capped at the lower of the two thresholds (fixed amount vs. turnover percentage).

---

## Timeline

| Date | Milestone |
|---|---|
| **02 Aug 2024** | Act entered into force |
| **02 Feb 2025** | General provisions, AI literacy duties, and prohibited-practice rules apply |
| **02 Aug 2025** | GPAI model rules apply and EU/member-state governance obligations begin |
| **02 Aug 2026** | Most AI Act rules apply; Annex III high-risk rules and Article 50 transparency rules start applying |
| **02 Aug 2027** | Rules for high-risk AI embedded in regulated products apply |

The European Commission has proposed tying some high-risk application dates to the availability of support tools such as harmonised standards. Treat the table as a release-review trigger, not as hard-coded application logic.

---

## Compliance Checklist for Agent Developers

1. **Classify your system** — Determine risk level using Annex III criteria
2. **If high-risk:** implement full risk management, data governance, documentation, and conformity assessment
3. **If using GPAI models:** obtain technical documentation from model providers to understand limitations
4. **Implement human oversight** — Design HITL mechanisms appropriate to the risk level
5. **Establish transparency** — Inform users of AI interaction; label generated content
6. **Set up monitoring** — Post-market surveillance and incident reporting
7. **Document everything** — Maintain audit trails for all agent decisions and actions

## Transfer Checklist

- [ ] Identify whether the new project is an AI system, GPAI model provider, deployer, distributor, importer, or only protocol/tooling infrastructure.
- [ ] Classify likely risk level before adding autonomous action paths.
- [ ] Decide whether outputs are advisory, decision-support, or action-executing.
- [ ] Add human oversight, override, stop, and audit hooks before high-impact automation.
- [ ] Keep compliance metadata honest: declared controls do not prove legal compliance by themselves.
- [ ] Record compliance posture and rejected assumptions in the decision log.

## Primary Reference

- EU AI Act implementation timeline: https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act
