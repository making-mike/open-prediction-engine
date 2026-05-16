---
description: How to develop contract-facing features without drifting from schema-first implementation
---

# Contract Development Workflow

Use this workflow when implementing or changing any contract-facing part of the repository.

Transfer rule: in a new repository, replace the contract boundary and `spec/` location with the target repo's canonical contract location.

## Default Development Order

1. Clarify the contract concern.
2. Update or add schema definitions in `spec/`.
3. Add or update validation tests.
4. Add or update TypeScript types and validators.
5. Only then build provider, client, or example code that depends on the contract.

This repository should evolve from explicit records and contracts outward, not from server code inward.

## Step 1: Clarify the Concern

Before editing code, identify which category the change belongs to:

- forecast question contract
- source and provenance contract
- feature or fixture contract
- baseline forecast contract
- model forecast contract
- forecast history contract
- evidence packet contract
- aggregate forecast contract
- resolution record contract
- scoring report contract
- track-record report contract
- calibration summary contract
- benchmark run contract

If a change does not clearly fit one of these, it may be implementation-specific rather than contract-facing.

## Step 2: Update the Schema

When changing a schema:

- prefer additive changes
- keep bootstrap deployments in mind
- avoid fields that imply infrastructure the protocol does not yet have
- keep names descriptive and stable

If the change is significant, check `.agents/workflows/schema-change-checklist.md` before proceeding.

## Step 3: Write Contract Tests

Before building implementation behavior, add tests that cover:

- valid payloads
- invalid payloads
- required vs optional fields
- edge cases for enums, nested objects, and arrays
- any lifecycle constraints that can be validated mechanically

For contract work, tests are the first implementation of the contract.

## Step 4: Implement Validators and Types

After tests exist:

- wire schema validation
- add or update TypeScript types
- keep runtime validation behavior aligned with the schemas

Avoid letting TypeScript-only assumptions drift ahead of runtime validation.

## Step 5: Build Dependent Code

Only after the contract is stable should you add:

- engine behavior
- client helpers
- examples
- transport bindings

Dependent code should consume the contract, not define it implicitly.

## Decision Logging

Append to `.agents/decisions.md` when a change introduces a durable architectural decision, such as:

- contract shape
- required/optional behavior
- trust model changes
- payment model changes
- lifecycle changes

Do not log trivial implementation details.

## Anti-Patterns

Avoid these:

- building handlers before the request/response schema is settled
- adding fields "just in case" without a concrete contract use
- turning examples into de facto specification
- introducing funding, marketplace, or unrelated application concerns into engine contracts
- encoding stronger trust guarantees than the implementation supports
