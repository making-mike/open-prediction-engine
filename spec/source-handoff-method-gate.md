# Source Handoff Method Gate

Status: implemented as checked local summary records.

The source handoff method gate connects builder-to-intake handoffs with setup benchmark gates and setup method decisions. It lets an agent see whether a confirmed local-file draft can reach a baseline or deterministic method decision, while keeping forecast execution as a separate explicit step.

It does not produce forecast artifacts.

## Contract

`source-handoff-method-gate.schema.json` records:

- source-intake handoff, source-intake report, setup benchmark gate, and setup method decision bindings
- handoff status and next action from the builder-to-intake step
- method gate status and next action for the setup-method step
- selected method class and selected forecast mode, when one is justified
- benchmark execution eligibility, method decision status, baseline eligibility, deterministic eligibility, and quality-claim boundary
- required actions and warnings for agent callers

## Cases

- `unconfirmed_builder_draft`: source intake exists but method selection waits for mapping confirmation.
- `confirmed_builder_draft`: source intake is accepted, setup benchmark gate approves provisional deterministic execution, and setup method decision selects `deterministic_statistical`.
- `insufficient_confirmed_builder_draft`: source intake exists but method selection asks for more data.
- `contains_secret`, `unsupported_format`, `oversized`, and `leakage`: builder rejection prevents source intake, benchmark gates, and method decisions.

## Commands

Inspect method-gate summaries:

```bash
python3 scripts/ope.py source-handoff-method
```

Inspect one method-gate summary:

```bash
python3 scripts/ope.py source-handoff-method --case confirmed_builder_draft
python3 scripts/ope.py source-handoff-method --case insufficient_confirmed_builder_draft
python3 scripts/ope.py source-handoff-method --case contains_secret
```

Run the explicit forecast step after a confirmed method gate:

```bash
python3 scripts/ope.py source-handoff-forecast --case confirmed_builder_draft
```

Check generated fixtures:

```bash
python3 scripts/generate_source_handoff_method_gate.py --check
python3 scripts/check_source_handoff_method_gate.py
```

Refresh generated fixtures:

```bash
python3 scripts/generate_source_handoff_method_gate.py --write
```

## Guardrails

Only handoffs with a source-intake report can create handoff-bound setup benchmark and method decision records. Builder-rejected cases remain outside source intake. `forecastArtifactsCreated` is always false; accepted method gates require a later explicit setup forecast execution before any forecast card, bundle, or artifact can exist.
