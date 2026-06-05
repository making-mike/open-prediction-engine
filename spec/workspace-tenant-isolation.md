# Workspace Tenant Isolation

Status: tenant isolation policy readback checked.

Last reviewed: 2026-06-04.

The workspace tenant isolation readback answers how OPE should separate resources, source bindings, operation queues, credential references, and idempotency namespaces when a host application manages multiple tenants or users.

Checked readback:

```bash
python3 scripts/ope.py workspace-tenant-isolation
python3 scripts/ope.py workspace-tenant-isolation --tenant-id tenant-001
python3 scripts/ope.py workspace-tenant-isolation --case cross_tenant_prediction_read
python3 scripts/ope.py workspace-tenant-isolation --view boundary
python3 scripts/ope.py workspace-tenant-isolation --check
```

The checked fixture layers tenant scope over the existing `prediction-workspace-registry` readback. Each tenant workspace has its own `tenantId`, `workspaceId`, prediction IDs, source binding IDs, operation queue references, idempotency namespace prefix, resource policy, and credential scope.

The `isolationModel` and `scopeKeys` sections require tenant, workspace, prediction, source-binding, and idempotency namespace scope for lookups and audit. Raw scope values are not public read surface fields.

The `tenantResourceControls` section keeps active prediction counts, queued operation counts, readback bytes, source binding counts, and tick runtime budgets tenant-local.

The `operationQueuePolicies` section keeps active, due, blocked, failed, source-health, calibration, and track-record read models scoped to a tenant workspace. Cross-tenant queue peeks and raw queue CRUD are blocked.

The `sourceBindingPolicies` section blocks raw cross-tenant source reuse. A target tenant needs a new sanitized binding and caller-owned credential reference; credential values and raw private rows remain outside OPE records.

The `accessCases` section includes one accepted same-tenant workspace read and blocked examples for cross-tenant prediction reads, cross-workspace source binding reuse, queue peeks, idempotency namespace collisions, credential references owned by another tenant, and unaudited admin overrides. Blocked cases write no receipts or immutable records and return sanitized diagnostics only.

This milestone is a readback policy. It does not implement hosted multitenancy, a network listener, tenant administration APIs, raw CRUD, credential storage, raw private row storage, cross-tenant read access, cross-tenant queue scans, or stronger forecast-quality claims.
