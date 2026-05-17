# Private Setup Workflow

Status: implemented as a checked domain-agnostic local contract.

The private setup workflow is OPE's general agent-facing contract for setting up a prediction engine from caller-approved sources. It describes the phases an agent should move through before a private setup can forecast, recalculate, resolve, and score outcomes.

The workflow is intentionally broader than the current implementation. It can represent local files now and future caller-approved uploads, APIs, or databases later, but it does not claim those generic private source runtimes are implemented.

The workflow is schema-bound by:

```text
spec/private-setup-workflow.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/private-setup-workflow/
```

## Commands

Inspect the workflow:

```bash
python3 scripts/ope.py private-setup-workflow
```

Check drift:

```bash
python3 scripts/ope.py private-setup-workflow --check
python3 scripts/check_private_setup_workflow.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_workflow.py --write
```

## Phases

The contract separates setup into:

1. source discovery
2. mapping confirmation
3. source intake
4. method gating
5. forecast execution
6. recalculation
7. resolution
8. scoring

The current reference implementation is the weather-logistics source-handoff setup runbook. It binds to `forecast-1102`, `question-1102`, and `trackrecord-1102`.

## Outcome Classes

The general outcome classes are:

- `setup_ready`
- `needs_confirmation`
- `needs_more_data`
- `rejected_source`
- `unsupported_source`
- `runtime_not_implemented`

Only `setup_ready` can continue toward forecast and scoring. All other outcomes block forecast and score creation until the required next action is complete.

## Guardrails

- The workflow is domain-agnostic; weather-logistics is only the current reference fixture.
- Manual uploads, private APIs, and private databases are planned contract surfaces, not implemented generic runtimes.
- Every setup path must preserve source policy, mapping, provenance, and unavailable-evidence boundaries.
- Rejected, unsupported, unconfirmed, and runtime-not-implemented outcomes must not bind forecast or scoring outputs.
- Fixture scores do not create calibration, production, or state-of-the-art claims.
