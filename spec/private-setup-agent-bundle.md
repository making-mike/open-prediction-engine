# Private Setup Agent Bundle

Status: implemented as checked compact guidance over private setup request, first-action, and runbook records.

The private setup agent bundle gives agents one small response for setup guidance. It joins:

- the private setup request summary
- the first-action dispatcher result
- the matching first-action runbook row
- the claim and execution boundary

The bundle is schema-bound by:

```text
spec/private-setup-agent-bundle.schema.json
```

Generated bundle fixtures live under:

```text
spec/fixtures/generated/private-setup-agent-bundles/
```

## Commands

Inspect all generated bundles:

```bash
python3 scripts/ope.py private-setup-bundles
```

Read one bundle by request ID:

```bash
python3 scripts/ope.py private-setup-bundle --request-id privatesetuprequest-001
```

Read one bundle through the agent adapter envelope:

```bash
python3 scripts/ope.py agent-call --operation private_setup_bundle --private-setup-request-id privatesetuprequest-001
```

Read a bad-request example:

```bash
python3 scripts/ope.py private-setup-bundle --case unknown_source_kind
python3 scripts/ope.py private-setup-bundle --case missing_approval
```

Check drift and invariants:

```bash
python3 scripts/ope.py private-setup-bundles --check
python3 scripts/check_private_setup_agent_bundles.py
```

Refresh generated output:

```bash
python3 scripts/generate_private_setup_agent_bundles.py --write
```

## Guardrails

- Bundles are read-only guidance and do not run suggested commands.
- Adapter envelope reads preserve the same non-execution boundary.
- Bundles do not read private data, create source manifests, create mappings, forecast, score, fetch live data, or store credentials.
- Bundles preserve bad-request handling for unknown source kinds and missing approvals.
- Forecast execution and scoring remain separate explicit later steps.
