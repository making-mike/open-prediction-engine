# Private Auto-Evidence Policy

Status: private data:auto source-policy readback checked.

Last reviewed: 2026-06-05.

The private auto-evidence policy answers which source-policy boundary governs `data: auto` in private engine setups. It is an overlay over the existing source-policy schema, private source adapter capabilities, domain/source field policy, credential-reference policy, retention/redaction policy, runtime security, workspace tenant isolation, and approved database source-adapter fixture.

Checked readback:

```bash
python3 scripts/ope.py private-auto-evidence-policy
python3 scripts/ope.py private-auto-evidence-policy --view source-kinds
python3 scripts/ope.py private-auto-evidence-policy --view gates
python3 scripts/ope.py private-auto-evidence-policy --case web_search_private_setup
python3 scripts/ope.py private-auto-evidence-policy --source-kind private_api_manifest
python3 scripts/ope.py private-auto-evidence-policy --view boundary
python3 scripts/ope.py private-auto-evidence-policy --check
```

The generated fixture lives at `spec/fixtures/generated/private-auto-evidence-policy/ope-private-auto-evidence-policy.generated.json` and is validated by `spec/private-auto-evidence-policy.schema.json`.

Private `data: auto` does not mean arbitrary private-source discovery. It requires a bound source policy, tenant/workspace scope, caller approval, checked source-kind capability, credential references where needed, freshness windows, retention/redaction policy, leakage checks, and a forecast-before-close boundary.

Current source-kind decisions:

- `local_file`: allowed only through approved local-source runtime and source-intake gates.
- `manual_mapping`: allowed only with caller confirmation and mapping-confidence separation.
- `auto_evidence_connector`: fixture-replay only, not production live fetching.
- `source_adapter_output`: allowed only through sanitized adapter-output handoff and source-adapter intake.
- `database_query_manifest`: manifest-only; no raw SQL execution in normal checks.
- `private_api_manifest`: manifest-only with scoped credential reference; no API call in normal checks.
- `manual_upload`: blocked until a checked manual-upload adapter contract exists.
- `web_search`: blocked for private `data: auto` until a separate allow-listed policy exists.

This milestone is a readback policy. It does not read private sources, resolve secrets, call networks, execute raw SQL, retain raw private payloads, treat post-outcome captures as forecast evidence, implement hosted runtime behavior, generate runtime types, or upgrade forecast-quality claims.
