# Domain/Source Field Policy

Status: domain/source field policy readback checked.

Last reviewed: 2026-06-04.

The domain/source field policy answers which configuration fields are required for every domain and source binding, which fields may vary by domain, and which fields are blocked from OPE setup records.

Checked readback:

```bash
python3 scripts/ope.py domain-source-field-policy
python3 scripts/ope.py domain-source-field-policy --view domain-fields
python3 scripts/ope.py domain-source-field-policy --view source-fields
python3 scripts/ope.py domain-source-field-policy --view extensions
python3 scripts/ope.py domain-source-field-policy --view blocked
python3 scripts/ope.py domain-source-field-policy --view source-kinds
python3 scripts/ope.py domain-source-field-policy --case raw_sql_query_as_binding_field
python3 scripts/ope.py domain-source-field-policy --field role_required_fields
python3 scripts/ope.py domain-source-field-policy --view boundary
python3 scripts/ope.py domain-source-field-policy --check
```

Every domain config must keep these universal containers: identity, question templates, horizons, resolution criteria, baseline method, accepted source roles, exclusion rules, sample thresholds, claim boundaries, and an execution boundary.

Every source binding must keep these universal containers: identity, binding mode, credential policy, role bindings, pre-forecast checks, setup operations, configuration input boundary, execution boundary, next action, and summary.

Domain-specific extensions are allowed only inside approved containers. Examples include question parameters, role keys, role-required fields, resolution prose, exclusion reason codes, horizon labels, baseline thresholds, and source-quality threshold values.

The blocked field set rejects credential values, raw SQL query text, raw private rows, post-outcome evidence as forecast-time evidence, production quality claims, and hosted runtime flags. Source-kind rules require source and adapter references for fixture, local-file, adapter-output, API, and database bindings; private API and database bindings also require caller-owned credential references. Credential values and raw payload storage remain blocked for every source kind.

The checked decision cases accept the current weather-transit core fields and seaport extension fields, and block missing resolution criteria, credential values in source bindings, raw SQL fields, premature quality claims, and resolution-only outcome roles marked as forecast-time evidence.

This milestone is a readback policy. It does not create forecasts, execute private APIs or databases, store credentials, store raw private data, generate runtime types, implement hosted runtime behavior, or upgrade quality claims.
