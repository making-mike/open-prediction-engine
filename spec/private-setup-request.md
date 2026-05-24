# Private Setup Request

Status: implemented as checked domain-agnostic setup request examples.

The private setup request contract is the first agent-facing setup-intent surface before adapter routing. It lets an agent declare a future-facing forecast intent, setup mode, selected source kind, source policy, approval state, and desired next action without reading private data.

The request set is schema-bound by:

```text
spec/private-setup-request.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/private-setup-requests/
```

## Commands

Inspect private setup request routing:

```bash
python3 scripts/ope.py private-setup-requests
```

Ask for the first safe action from one request:

```bash
python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001
python3 scripts/ope.py private-setup-action-runbook
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-setup-requests --check
python3 scripts/check_private_setup_requests.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_requests.py --write
```

## Routing

- `local_file` requests route to `python3 scripts/ope.py source-builder`.
- `manual_mapping` requests require caller confirmation, then route to `python3 scripts/ope.py source-handoff --case confirmed_builder_draft`.
- `auto_evidence_connector` requests route to fixture `python3 scripts/ope.py gather-evidence`.
- `manual_upload`, `private_api`, and `private_database` requests wait for future checked runtimes.
- `unregistered_source` requests require source replacement.
- `unsafe_source` requests stop before source intake.

## Guardrails

- Request classification does not execute source reads.
- Request classification does not create source manifests, field mappings, forecast artifacts, forecast cards, scoring records, live fetch results, or credential records.
- First-action dispatch over one request remains non-executing even when it names a checked local command.
- Private API, private database, and manual-upload support remain planned-only runtimes.
- Forecast and scoring still require source intake, method gates, explicit forecast execution, resolution, and sample-size-bound reporting.
