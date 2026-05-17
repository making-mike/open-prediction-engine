# Source Intake Handoff

Status: implemented as checked local handoff records.

The source intake handoff connects the local source manifest builder to source intake. It lets an agent inspect whether a builder draft should ask for mapping confirmation, proceed to setup method gates, collect more source data, or replace rejected files.

It does not produce forecast artifacts. Even when a confirmed builder draft produces an accepted source-intake report, setup benchmark and method gates still decide whether forecast execution may run.

## Contracts

- `source-intake-handoff.schema.json`: handoff status, next action, builder binding, source-intake binding, mapping summary, builder rejection summary, and draft-artifact paths.
- `source-manifest-build.schema.json`: local file inspection result produced by the builder.
- `source-manifest.schema.json`: draft source manifest passed into source intake when builder inspection succeeds.
- `field-mapping.schema.json`: draft or confirmed field mapping passed into source intake.
- `source-intake-report.schema.json`: source intake classification produced from the handoff inputs when available.

## Cases

- `unconfirmed_builder_draft`: source intake returns `needs_confirmation`; next action is `ask_mapping_confirmation`.
- `confirmed_builder_draft`: source intake returns `accepted`; next action is `proceed_to_method_gating`.
- `insufficient_confirmed_builder_draft`: source intake returns `rejected` due sample-size limits; next action is `collect_more_data`.
- `contains_secret`, `unsupported_format`, `oversized`, and `leakage`: builder rejection blocks source intake; next action is `replace_rejected_sources`.

## Commands

Inspect handoff summaries:

```bash
python3 scripts/ope.py source-handoff
```

Inspect one handoff:

```bash
python3 scripts/ope.py source-handoff --case unconfirmed_builder_draft
python3 scripts/ope.py source-handoff --case confirmed_builder_draft
python3 scripts/ope.py source-handoff --case insufficient_confirmed_builder_draft
python3 scripts/ope.py source-handoff --case contains_secret
```

Check generated handoff fixtures:

```bash
python3 scripts/generate_source_intake_handoff.py --check
python3 scripts/check_source_intake_handoff.py
```

Refresh generated handoff fixtures:

```bash
python3 scripts/generate_source_intake_handoff.py --write
```

## Guardrails

Builder rejection reasons are preserved in the handoff record and rejected builder drafts do not enter source intake. Unconfirmed builder mappings remain proposed and block forecast generation. Confirmed and accepted source intake can proceed only to setup benchmark and method gates; it still does not create a forecast artifact.
