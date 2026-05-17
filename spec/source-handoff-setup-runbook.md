# Source Handoff Setup Runbook

Status: implemented as a checked local fixture-mode runbook.

The source-handoff setup runbook is the agent-facing guide for the current private-source setup fixture path. It does not add new forecast behavior. It tells an agent how to move from caller-approved local source inspection to source intake handoff, method gating, explicit forecast execution, resolution, scoring, and safe read surfaces.

The runbook is schema-bound by:

```text
spec/source-handoff-setup-runbook.schema.json
```

Generated output lives under:

```text
spec/fixtures/generated/source-handoff-runbook/
```

## Commands

Inspect the runbook:

```bash
python3 scripts/ope.py source-handoff-runbook
```

Check drift:

```bash
python3 scripts/ope.py source-handoff-runbook --check
python3 scripts/check_source_handoff_setup_runbook.py
```

Refresh generated output:

```bash
python3 scripts/generate_source_handoff_setup_runbook.py --write
```

## Agent Flow

The checked example sequence is:

1. inspect local files with `source-builder`
2. inspect handoff state with `source-handoff`
3. inspect method eligibility with `source-handoff-method`
4. explicitly execute the confirmed handoff with `source-handoff-forecast`
5. resolve and score with `resolve-source-handoff`
6. read the resolved `forecast-1102` card, lifecycle bundle, or `trackrecord-1102`

## Guardrails

- Unconfirmed builder mappings must ask for confirmation before method gates or forecast execution.
- Insufficient confirmed drafts must collect more data before retrying setup gates.
- Builder-rejected sources must be replaced before source intake.
- Blocked cases must not bind forecast IDs, question IDs, cards, bundles, artifacts, resolution records, scoring reports, calibration summaries, or track records.
- Only `forecast-1102` resolves and scores in this fixture path.
- One resolved source-handoff outcome is not a quality, calibration, production, or state-of-the-art claim.
