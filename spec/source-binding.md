# Source Binding

Source binding records connect a configured OPE domain to concrete data sources without storing credentials, raw SQL, or private records in OPE artifacts.

The checked surface is:

```bash
python3 scripts/ope.py source-bindings
python3 scripts/ope.py source-bindings --case accepted
python3 scripts/ope.py source-bindings --case partial
python3 scripts/ope.py source-bindings --case rejected
python3 scripts/ope.py source-bindings --case blocked
python3 scripts/ope.py source-bindings --check
```

The records cover approved local files, source-adapter outputs, public APIs, and database adapter manifests. Database and private API cases use credential references and sanitized query boundaries only; OPE does not parse arbitrary private APIs or databases directly.

Every binding carries mapping-confidence, source-quality, leakage, freshness, privacy, and outcome-availability checks before forecast generation can proceed. Only the accepted case allows forecast generation, and even then the next write must go through lifecycle operation preflight and receipts.

Setup operations are draft, validate, confirm, update, archive, and redact. They map to the embedded internal API operation names and prediction configuration lifecycle operations, require idempotency and leases, and replace physical delete with archive/redaction records.
