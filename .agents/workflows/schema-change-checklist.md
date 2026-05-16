---
description: Checklist for evaluating schema changes in engine contracts
---

# Schema Change Checklist

Use this checklist before introducing or modifying contract fields.

Transfer rule: keep the checklist for any machine-readable contract. If the new repository uses OpenAPI, protobuf, GraphQL SDL, database migrations, or another contract source instead of JSON Schema, adjust the wording but keep the same discipline.

## Purpose

- Is this field solving a real engine or interoperability problem?
- Is the field needed for interoperability, or only for one implementation?
- Can the same goal be achieved with a simpler structure?

## Scope

- Is the field part of a public engine record rather than private model internals?
- Does it belong in a forecast, evidence, resolution, scoring, or calibration contract?
- Does it avoid introducing funding, marketplace, or unrelated application concerns?

## Optionality

- Should this be required in all payloads, or optional for bootstrap deployments?
- If optional, is the absence of the field still semantically clear?
- If required, are we sure it will not block early adoption unnecessarily?

## Validation

- Can the field be validated mechanically?
- Are valid and invalid values easy to specify in tests?
- Does the field require additional constraints on sibling fields?

## Compatibility

- Is the change additive?
- Will existing implementations break?
- Would a more extensible representation avoid future schema churn?

## Trust and Semantics

- Does the field interact with identity, provenance, calibration, or payment metadata?
- Could the field accidentally imply stronger guarantees than the implementation supports?
- If the field is trust-relevant, does it distinguish provisional vs verified states where needed?

## Composition

- Does the field work with chained predictions and upstream dependencies?
- Does it preserve reuse of shared upstream forecast artifacts?
- Could it leak unnecessary private downstream information?

## Decision Logging

- Is this change important enough to log in `.agents/decisions.md`?
- If yes, has the rationale and rejected alternative been captured clearly?
