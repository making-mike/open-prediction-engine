# Private Setup First Action

Status: implemented as a checked non-executing dispatcher result.

The private setup first-action contract gives agents a compact answer for one setup request: what is the first safe action, which request and bridge records it binds to, which checked command may be run by the caller, and why the action may be blocked.

The dispatcher accepts either a generated request ID or one request-shaped JSON object. It does not read private source data, execute source-builder, execute source-handoff, gather evidence, create forecast artifacts, score outcomes, or store credentials.

The action record is schema-bound by:

```text
spec/private-setup-first-action.schema.json
```

Generated action fixtures live under:

```text
spec/fixtures/generated/private-setup-actions/
```

## Commands

Inspect all generated first-action fixtures:

```bash
python3 scripts/ope.py private-setup-actions
```

Dispatch one generated request:

```bash
python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001
```

Dispatch one request JSON object:

```bash
python3 scripts/ope.py private-setup-action --input path/to/private-setup-request.json
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-setup-actions --check
python3 scripts/check_private_setup_first_actions.py
```

Read runbook guidance for first-action statuses:

```bash
python3 scripts/ope.py private-setup-action-runbook
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_first_actions.py --write
```

## Action Classes

- `local_file` returns `ready_to_run_checked_command` with `python3 scripts/ope.py source-builder`.
- `manual_mapping` returns `confirmation_required` before source handoff.
- `auto_evidence_connector` returns `fixture_ready` with `python3 scripts/ope.py gather-evidence`.
- `manual_upload`, `private_api`, and `private_database` return `runtime_not_implemented`.
- `unregistered_source` returns `source_replacement_required`.
- `unsafe_source` returns `rejected_unsafe_source`.
- Unknown source kinds and missing approvals return sanitized `bad_request` actions with exit code `2`.

## Guardrails

- The dispatcher may name a checked local command but never runs it.
- The runbook explains next steps for dispatcher outcomes, but it also remains non-executing.
- Dispatcher output remains domain-agnostic and non-generating.
- Planned private runtimes remain planned-only.
- Forecast artifacts and scoring records still require source intake, setup benchmark gates, method decisions, explicit forecast execution, resolution, and scoring.
