# Credential Reference Policy

Status: credential-reference policy readback checked.

Last reviewed: 2026-06-05.

The credential-reference policy answers what kind of credential reference is acceptable for private API and database source bindings without storing secrets in OPE records.

Checked readback:

```bash
python3 scripts/ope.py credential-reference-policy
python3 scripts/ope.py credential-reference-policy --view mechanisms
python3 scripts/ope.py credential-reference-policy --view scope
python3 scripts/ope.py credential-reference-policy --view lifecycle
python3 scripts/ope.py credential-reference-policy --view consumers
python3 scripts/ope.py credential-reference-policy --case database_password_in_connection_string
python3 scripts/ope.py credential-reference-policy --mechanism host_runtime_secret_handle
python3 scripts/ope.py credential-reference-policy --scope-key tenant_id
python3 scripts/ope.py credential-reference-policy --state redaction_required
python3 scripts/ope.py credential-reference-policy --consumer database_adapter
python3 scripts/ope.py credential-reference-policy --view boundary
python3 scripts/ope.py credential-reference-policy --check
```

The accepted mechanism is an opaque caller-owned reference, not a secret value. OPE may store a `credentialRef` only when it is scoped to tenant, workspace, source binding, source role, adapter reference, source kind, source policy, and credential purpose.

Accepted reference mechanisms:

- `caller_secret_store_alias`: a caller-managed secret-store alias for private API or database sources.
- `host_runtime_secret_handle`: a host-managed handle resolved outside OPE during explicit runtime execution.
- `local_operator_session_ref`: an ephemeral local session reference for an explicit operator-approved command.
- `public_no_credential`: an explicit no-credential sentinel for public or fixture sources whose source policy does not require credentials.

Lifecycle states distinguish proposed, approved, active, rotation-due, revoked, and redaction-required references. The `active` state allows explicit approved runtime use, but no state allows normal-check secret resolution or credential-value storage.

Consumer rules allow source-binding validation, runtime readbacks, and agent envelopes to mention scoped reference IDs and blockers, but they cannot receive credential values. Normal checks may validate fixtures and drift only; they may not use credential references to resolve secrets.

The checked cases accept scoped private API and database references plus public no-credential sources. They block missing private-source references, raw API tokens, database passwords in connection strings, cross-tenant references, unscoped references, adapter mismatches, revoked references, and normal-check secret-resolution attempts.

This milestone is a readback policy. It does not implement a secret resolver, hosted secret manager, environment-secret reader, database connection, API call, secret-store write, cross-tenant credential reuse, raw connection-string acceptance, credential storage, or stronger forecast-quality claims.
