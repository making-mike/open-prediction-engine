# Repo Rules

These rules apply to implementation work in this repository.

They are also designed as a transferable baseline for future protocol, SDK, engine, or agent-facing infrastructure repositories. When copied into a new repository, keep the reusable rules and replace the OPE-specific project overlay with the new project's purpose, non-goals, command set, and contract documents.

See `.agents/resources/transferable-agent-baseline.md` before porting this rule set.

## Source Hierarchy

When repo documents disagree, use this hierarchy:

1. Root `AGENTS.md` and `.agents/rules.md` for agent operating rules.
2. Normative contracts, schemas, scoring definitions, and pipeline invariants for interoperable behavior.
3. `.agents/decisions.md` for durable architectural rationale.
4. Tests, smoke checks, and evaluation fixtures for executable interpretation of the contract.
5. README, roadmap, memos, examples, and guides for onboarding and non-normative context.

For OPE specifically, question lifecycle, forecast artifact, evidence packet, forecast history, aggregate forecast, resolution record, scoring report, track-record report, and calibration report contracts should become the normative engine surface once they are committed. Until then, avoid claims that depend on unimplemented contracts.

## 1. Forecast Or Evidence Contract First

Treat OPE as a forecast generation and calibration engine repository.

- Prefer engine-level abstractions over app-level abstractions.
- Do not introduce generic marketplace or demand-aggregation logic.
- Do not turn OPE into a generic agent transport protocol.
- Keep the repository focused on question governance, ingestion, normalization, feature construction, baseline forecasts, model forecasts, forecast histories, evidence packets, resolution records, scoring, track records, calibration, and benchmark comparison.

Transfer rule: in a new repository, state the equivalent contract boundary and non-goals before adding implementation behavior.

## 2. Schema And Record Discipline

The engine contract should be explicit and machine-readable wherever practical.

- Define or update schemas before building SDK or service behavior around them.
- Prefer additive schema changes.
- Do not make breaking schema changes casually.
- If a schema change is meaningfully architectural, log it in `.agents/decisions.md`.

Core OPE records should include:

- forecast questions
- question lifecycle records
- source and provenance records
- feature snapshots or feature references
- baseline forecast outputs
- model forecast outputs
- aggregate forecast outputs
- evidence packets
- forecast history entries
- resolution records
- scoring reports
- track-record reports
- calibration summaries

Transfer rule: if the new repository uses OpenAPI, protobuf, GraphQL SDL, SQL migrations, JSON Schema, or another contract format, name that format as the source of truth and update the workflows accordingly.

## 3. Evaluation Before Ambition

For forecast quality and lifecycle semantics:

- define the question, lifecycle status, horizon, close time, resolution source, fallback sources, output type, unscorable statuses, and scoring rule first
- implement or fixture the baseline before adding complex model behavior
- then implement model forecasts, forecast histories, resolution, unscorable status handling, scoring, track records, and calibration
- then build client, server, or agent-facing behavior on top

Full TDD is not required for every small utility, but forecast-facing behavior should be evaluation-led.

## 4. Field Discipline

Every new question, forecast, evidence, history, resolution, or scoring field should have a clear answer to:

- What problem does it solve?
- Is it engine-level, protocol-level, scorer-level, or product-specific?
- Is it required or optional?
- How is it validated?
- Does it need to be stable across model versions?
- Is it safe for public artifacts?
- Does it create future compatibility or privacy risk?

If those answers are unclear, the field is probably premature.

## 5. Examples Are Not Evidence

- Example forecasts and payloads should validate against the schemas.
- Do not treat examples as authoritative if schemas, tests, and evaluation fixtures do not enforce the same behavior.
- Keep examples simple enough to teach the engine lifecycle, not to imply broad forecasting quality.

## 6. Trust Metadata Must Stay Honest

- Distinguish self-reported, logged, resolved, scored, independently scored, and audited claims.
- Do not encode stronger trust claims in docs, examples, or artifacts than the implementation actually supports.
- Preserve domain-, horizon-, output-, and resolution-source-specific quality semantics.
- Include sample size and coverage period with calibration or score summaries.

## 7. Keep Scope Narrow

When in doubt, prefer:

- one narrow forecast domain
- explicit question lifecycle
- clear resolution criteria
- explicit ambiguous and annulled statuses
- simple baseline first
- smaller schema surface
- explicit provenance over broad claims
- measured calibration over trust language

Do not expand domains until the first wedge has a working evidence loop.

## 8. Update The Roadmap When Work Lands

The roadmap is a working execution document once it exists.

- When a roadmap task is completed, update `roadmap.md` in the same workstream.
- Mark tasks accurately as done, in progress, or not started.
- Do not mark roadmap items complete unless the code, docs, tests, or evaluation reports actually support that status.
- If implementation changes the meaning or sequencing of roadmap work, update the roadmap text as well.

## 9. Log Decisions

Every non-trivial technical or architectural decision must be logged.

- Follow the `/log-decision` workflow (`.agents/workflows/log-decision.md`) for format and criteria.
- Append entries to `.agents/decisions.md`; never edit or remove past entries.
- If `.agents/decisions.md` does not exist yet, create a fresh OPE decision log before the first entry.
- Read existing decisions before making a related choice to ensure consistency.
- When in doubt about whether something is non-trivial, log it; a short entry costs less than a lost rationale.

## 10. Review Each Slice

Every completed implementation slice should be followed by a focused code review before moving to the next slice.

- Review the code with a bug-risk, data-leakage-risk, evaluation-risk, and regression-risk mindset.
- Findings should be concrete, severity-ordered, and tied to file references.
- Fix issues that are small and clearly worth doing immediately.
- Fix review findings immediately when they are correctness-critical, evidence-breaking, security-relevant, privacy-relevant, or likely to cause behavioural regressions.
- If a review finding is real but not worth fixing in the current slice, add it to `roadmap.md` instead of leaving it implicit.
- Do not proceed to the next slice until each review finding is either fixed, explicitly rejected with rationale, or added to `roadmap.md`.

## 11. Review Before Each Milestone

Before starting a new milestone, do a broader consistency review of the current repository state.

- Compare the implementation against README, roadmap, `.agents/decisions.md`, and current schemas or evaluation fixtures.
- Check that docs and examples do not overclaim beyond what the code, tests, scores, and calibration reports actually support.
- Verify that completed roadmap items are genuinely implemented and tested.
- Capture any gaps either as immediate fixes or as explicit roadmap follow-ups.

## 12. Commit Deliberately

Commits should be small, reviewable snapshots of completed work.

- Do not create a commit unless the user explicitly asks for one or the current task clearly includes publishing or committing the work.
- Commit one coherent implementation slice at a time; do not mix unrelated fixes, formatting churn, generated output, or exploratory edits into the same commit.
- Before staging, inspect `git status` and the relevant `git diff` so unrelated local changes, user work, ignored live captures, secrets, and scratch files are not staged accidentally.
- Include required schema, fixture, generated report, documentation, roadmap, and decision-log updates in the same commit as the behavior that requires them.
- Run the normal checks before committing. If a broader release check is relevant, run it too; if a check cannot be run, note that explicitly in the handoff.
- Resolve review findings before committing unless they are explicitly rejected with rationale or captured as roadmap follow-ups.
- Use a concise imperative commit subject that names the changed contract, behavior, or documentation surface.
- Never commit raw live fetches, credentials, private source data, local-only `.ope/live/` drafts, or artifacts that would make public claims stronger than the checked implementation supports.

## 13. Keep Adjacent-Standard Claims Exact

Agent-facing projects often touch adjacent standards such as agent-discovery protocols, tool protocols, payment rails, DID, OAuth, OpenAPI, and sector compliance frameworks.

- Do not claim compatibility with a standard unless the implemented surface supports the required operations.
- If OPE only emits portable forecast artifacts, say that; do not imply it implements a full provider protocol or server surface.
- If A2A or MCP adapters are added, keep them scoped to the exact supported skills, tools, resources, prompts, and task operations.
- Treat payment metadata as compatibility hooks unless settlement, authorization, and audit behavior are implemented and tested.
- Treat compliance metadata as policy input, not as a legal guarantee.

## 14. Transfer This Rule Set Deliberately

When creating a new repository with the same assumptions:

- copy `.agents/` and root `AGENTS.md`
- replace the project purpose, non-goals, normative docs, commands, and release checks
- reset or archive `.agents/decisions.md`
- keep the review, commit, decision logging, security, contract-first, and evidence-first rules
- remove OPE-only forecast, scoring, calibration, and engine details unless the new project actually implements them
- add one initial decision explaining adoption of the transferred baseline and any deviations
