# Private Setup First-Action Runbook

Status: implemented as checked guidance over private setup first-action results.

The private setup first-action runbook maps each dispatcher outcome to the next safe caller-visible step. It is designed for agents that need to decide whether to run source-builder, ask for mapping confirmation, use fixture evidence, wait for a future runtime, replace a source, stop unsafe input, or fix a bad request.

The runbook is schema-bound by:

```text
spec/private-setup-first-action-runbook.schema.json
```

Generated output lives at:

```text
spec/fixtures/generated/private-setup-actions/ope-private-setup-first-action-runbook.generated.json
```

## Commands

Inspect the runbook:

```bash
python3 scripts/ope.py private-setup-action-runbook
```

Read the joined bundle for one setup request:

```bash
python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-setup-action-runbook --check
python3 scripts/check_private_setup_first_action_runbook.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_first_action_runbook.py --write
```

## Guardrails

- The runbook binds generated first-action fixtures but does not execute them.
- The runbook may name `source-builder`, `source-handoff`, or fixture evidence commands, but it never runs them.
- Planned runtimes, unknown sources, unsafe sources, and missing approvals cannot enter source intake through the runbook.
- Agent bundles may join this runbook with request and first-action records, but remain read-only guidance.
- Forecast execution and scoring remain blocked until later setup intake, benchmark, method, forecast, resolution, and scoring steps explicitly allow them.
