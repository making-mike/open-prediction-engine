# Transferable Agent Baseline

This resource packages the repo's agent rules, workflows, resources, and skill assumptions so they can be copied into another repository without carrying project-specific product claims.

Last reviewed: 2026-05-16.

## What To Copy

Copy these files as the reusable baseline:

- `AGENTS.md`
- `.agents/rules.md`
- `.agents/workflows/log-decision.md`
- `.agents/workflows/protocol-development.md`
- `.agents/workflows/schema-change-checklist.md`
- `.agents/resources/architecture_patterns.md`
- `.agents/resources/protocols_reference.md`
- `.agents/resources/security_checklist.md`
- `.agents/resources/compliance_guide.md`
- `.agents/resources/transferable-agent-baseline.md`
- `.agents/skills/agentic-economy/SKILL.md`

Treat `.agents/decisions.md` differently. For a new project, either start a fresh decision log at `DEC-001` or move the imported history into an archival note. Do not mix old project decisions with new project decisions unless the new repository is explicitly continuing the same lineage.

## Reusable Assumptions

Carry these assumptions into any protocol, SDK, engine, or agent-facing infrastructure project:

- The contract is the product. Schemas, normative docs, conformance checks, and runtime validators are more authoritative than examples.
- Keep the repo scoped. Do not let an engine repository quietly become a marketplace, scheduler, generic protocol, or product application unless that is the explicit project purpose.
- Prefer additive contract evolution. Breaking changes need a versioning story, migration path, and decision-log entry.
- Public interoperability claims must match implemented behavior. Discovery adapters, tool protocols, payment integrations, and API surfaces should say exactly what they support.
- Bind every runtime result to the originating request. IDs, domain/task intent, desired output, caller identity, provider identity, and terminal result metadata must not drift apart.
- Treat trust signals as evidence with provenance. Distinguish self-reported, provisional, logged, resolved, scored, independently scored, and audited claims.
- Keep public errors sanitized by default. Preserve raw diagnostics only in trusted logs or explicit debug paths.
- Bound remote input and output. Use body limits, event limits, timeouts, abort signals, allow-lists, and rate/spend controls.
- Do not put secrets into discovery metadata, prompt-visible tool arguments, examples, or long-lived agent memory.
- External network calls in tests must be controlled, skipped, mocked, or explicitly integration-scoped.
- Log durable architecture decisions. If future maintainers will ask "why this shape?", record the answer.
- Review each implementation slice before moving on. Fix correctness-critical, evidence-breaking, security-relevant, privacy-relevant, and regression-prone findings immediately.

## Project Overlay

When transferring this baseline, replace the project overlay with the target project's overlay.

For this repository, the overlay is:

- Project name: Open Prediction Engine.
- Project scope: evidence-producing probabilistic forecast generation, question governance, forecast histories, resolution, scoring, track records, and calibration.
- Non-goals: universal prediction oracle, generic agent protocol, pooled-demand service, payment settlement layer, independent audit authority.
- Core contract directory: `spec/` once committed.
- Canonical public narrative: `whitepaper.md`.
- Decision log: `.agents/decisions.md`.
- Package manager: not selected yet.
- Release check: not selected yet.
- Forecast invariants: every serious forecast should bind question, question lifecycle state, domain, horizon, forecast timestamp, close time, model version, provenance, baseline, evidence packet, forecast history, resolution criteria, resolution source, fallback sources, score, track-record context, and calibration context.

For a new repository, define the same fields before implementation starts:

- Project name and one-sentence purpose.
- Explicit non-goals.
- Normative source-of-truth documents.
- Machine-readable contract files.
- Discovery paths and compatibility adapters, if any.
- Development, test, build, release, and conformance commands.
- Runtime binding invariants.
- Security and privacy defaults.
- Compliance posture and risk classification.

## Transfer Workflow

1. Copy the baseline files.
2. Replace project name, purpose, non-goals, commands, and normative document list in `AGENTS.md`.
3. Update `.agents/rules.md` so the reusable rules remain and the project overlay describes the new repository only.
4. Reset or archive `.agents/decisions.md`.
5. Update resource references that are project-specific.
6. Run a claim review: README, roadmap, whitepaper, examples, schemas, and conformance docs must not overstate implemented behavior.
7. Add the first new project decision that records adoption of this baseline and any deviations.

## Adaptation Checklist

- [ ] Does the new project have a clear contract boundary?
- [ ] Are schemas or machine-readable contracts identified as canonical where appropriate?
- [ ] Are examples explicitly non-normative?
- [ ] Is adjacent-standard compatibility scoped honestly?
- [ ] Are public discovery documents free of secrets?
- [ ] Are remote calls bounded and allow-listed?
- [ ] Are paid or effectful tools approval-gated?
- [ ] Are request/result binding invariants written down and tested?
- [ ] Are trust and evidence labels precise?
- [ ] Are compliance statements framed as deployment guidance, not legal guarantees?
- [ ] Is the decision log fresh and project-specific?

## Current Standards Anchors

These anchors were checked during the 2026-05-16 refresh:

- A2A Agent Cards use `/.well-known/agent-card.json` when using the well-known URI strategy: https://a2a-protocol.org/v0.3.0/specification/
- MCP servers expose tools, resources, and prompts; tool listings should be deterministic when the underlying set is unchanged: https://modelcontextprotocol.io/specification/draft/server/tools
- MCP resources support annotations such as audience, priority, and last-modified metadata: https://modelcontextprotocol.io/specification/2025-06-18/server/resources
- OWASP treats prompt injection as the first LLM application risk in its 2025 LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- OWASP MCP Top 10 highlights token/secret exposure, prompt injection via context payloads, shadow MCP servers, and context over-sharing: https://owasp.org/www-project-mcp-top-10/
- EU AI Act obligations apply progressively; verify dates and obligations before release: https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act
- x402 uses HTTP `402 Payment Required` with payment requirement, signature, and settlement response metadata over normal HTTP flows: https://docs.x402.org/core-concepts/http-402
