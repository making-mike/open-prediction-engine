# Embedded Internal API

Status: stable surface defined.

Last reviewed: 2026-06-03.

The embedded internal API is the operation surface host software and agents should call instead of raw files, raw SQL, or direct scheduler control. It is a semantics layer over lifecycle operations and read models; transports such as CLI, agent-call, MCP, HTTP, or queue wrappers must not redefine behavior.

Checked readback:

```bash
python3 scripts/ope.py internal-api
python3 scripts/ope.py internal-api --operation start_prediction
python3 scripts/ope.py internal-api --operation start_prediction --call
python3 scripts/ope.py agent-call --operation internal_api --internal-operation start_prediction
python3 scripts/ope.py internal-api --check
```

The stable operation names are `create_prediction`, `update_prediction`, `start_prediction`, `pause_prediction`, `resume_prediction`, `run_tick`, `resolve_due`, `append_evidence`, `read_status`, `read_forecast_card`, `read_lifecycle_bundle`, `archive_record`, and `redact_record`.

Effectful operations must return operation receipts, idempotency status, lease status, blocking guards, next actions, and sanitized diagnostics. Read-only operations return compact read models or record references and do not require receipts, idempotency keys, or leases.

`python3 scripts/check_internal_api.py` calls every effectful operation through `call_internal_api()` and verifies those receipt/readback fields are present.

The request envelope requires operation name, caller ID, prediction ID, and input, with optional idempotency key, max bytes, dry-run, caller intent, source policy ID, and domain ID. The response envelope separates required status fields, effectful receipt fields, and read-only record/read-model refs. The checker keeps a representative effectful response under 4096 bytes.

In-process functions in `scripts/internal_api_runtime.py`, the `internal-api --call` CLI wrapper, and the `agent-call --operation internal_api` wrapper all use the same `call_internal_api()` function. The current wrapper mode is non-mutating dry-run; commits still belong behind lifecycle operation receipts.

HTTP, queue, and hosted service adapters are declared only as future transports over this same internal API. They must share internal semantics, return the same envelopes, and avoid raw SQL or raw file-layout exposure.

The internal API does not permit surprise network calls, unbounded loops, hidden scheduler installation, automatic method upgrades, credential values in records, raw SQL exposure, raw file-layout exposure, or hosted-runtime requirements.
