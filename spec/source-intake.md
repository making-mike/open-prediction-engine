# Source Intake

Status: implemented as schema-bound fixture manifests, field mappings, and deterministic intake reports.

Source intake is the pre-forecast gate between a domain setup and forecast execution. It lets an agent provide a bounded source manifest and field mapping, then receive a machine-readable report explaining whether the data is usable, partially usable, needs confirmation, or rejected.

It does not produce forecast artifacts.

The local source manifest builder can draft those inputs from small caller-approved CSV/JSON files, but its output is still only a draft. The source intake handoff records the next action between builder output and intake. Source intake remains the first gate that can classify a manifest/mapping pair as accepted, partially accepted, needing confirmation, or rejected.

## Contracts

- `source-manifest.schema.json`: caller-provided sources, source role, connector type, retrieval metadata, coverage, field inventory, optional sanitized feature summary, and privacy posture.
- `field-mapping.schema.json`: mappings from source fields to setup-required fields, including user-provided, registry-backed, deterministic, and agent-inferred mappings.
- `source-intake-report.schema.json`: deterministic usability report covering required fields, type parsing, entity matching, timestamp availability, source freshness, leakage risk, sample size, privacy, role coverage, and method eligibility.
- `source-manifest-build.schema.json`: pre-intake local file inspection result and draft-artifact boundary.
- `source-intake-handoff.schema.json`: builder-to-intake binding, next action, and confirmation boundary.

## Fixtures

Input fixtures live under:

```text
spec/fixtures/source-intake/
```

Generated reports live under:

```text
spec/fixtures/generated/source-intake/
```

Current outcome examples:

- `accepted`: enough confirmed pre-close evidence and sanitized forecast-time feature summary for baseline and deterministic methods.
- `accepted_partial`: enough confirmed historical data for baseline only.
- `needs_confirmation`: agent-inferred mappings are present but must be confirmed before forecasting.
- `rejected`: post-close/leaking evidence, secrets, or insufficient historical sample makes the intake unusable.

## Commands

Inspect intake summaries:

```bash
python3 scripts/ope.py source-intake
```

Inspect one report:

```bash
python3 scripts/ope.py source-intake --case accepted
python3 scripts/ope.py source-intake --case accepted_partial
python3 scripts/ope.py source-intake --case needs_confirmation
python3 scripts/ope.py source-intake --case rejected
```

Check generated fixtures and semantic boundaries:

```bash
python3 scripts/generate_source_intake.py --check
python3 scripts/check_source_intake.py
python3 scripts/ope.py source-intake --check
```

## Guardrails

Agent-inferred mappings remain proposals until confirmed. Rejected intake reports must not bind forecast outputs. Post-outcome or unavailable data cannot be used as forecast-time evidence. Sources that contain secrets are rejected by the fixture checker rather than surfaced into forecast artifacts.

Builder-generated drafts are not public read surfaces and do not allow forecast execution. They must pass through source intake and any later setup method gates before a forecast artifact can be generated.
