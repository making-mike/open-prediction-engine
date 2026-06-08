# Generated Runtime Types Decision

Status: deferred until adoption evidence shows type-specific friction.

OPE currently does not generate language-specific runtime types. The checked decision record is available through:

```bash
python3 scripts/ope.py generated-types-decision
python3 scripts/ope.py generated-types-decision --section summary
python3 scripts/check_generated_runtime_types_decision.py
```

## Decision

The current decision is `defer_until_adoption_evidence`.

No TypeScript or Python files are generated because:

- `pilot-findings` reports zero accepted real sessions.
- `pilot-findings` reports eight simulated agent sessions, including three non-Helsinki setup-comprehension prompts, but they are agent-only adoption-friction evidence and not real pilot evidence.
- Current smoke and adoption traces do not show type-specific integration failures.
- Generating a broad SDK would imply more stability than the full spec package currently claims.
- Hosted service, private-source runtime, and production source parsing remain out of scope.

## JSON Fallback

Agents should use stable JSON examples and validators for now:

```bash
python3 scripts/ope.py prediction-feature-setup --view response --case accepted
python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json
python3 scripts/ope.py mcp-adoption --view summary
python3 scripts/ope.py validate --input <record.json>
python3 scripts/ope.py smoke
```

## Next Review

Review generated types after sanitized pilot findings show repeated schema-copying, validation, or integration friction that a narrow type surface would directly reduce. If accepted later, the first scope should be limited to prediction-feature setup request/response and forecast-card readback.

Generated types must not imply hosted runtime, SDK stability for the whole spec package, production source parsing, or forecast-quality claims.
