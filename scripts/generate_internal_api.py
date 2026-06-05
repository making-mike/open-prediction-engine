#!/usr/bin/env python3
"""Generate a checked embedded internal OPE API surface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "internal-api"
OUTPUT_PATH = GENERATED / "ope-internal-api.generated.json"
SCHEMA = SPEC / "internal-api.schema.json"
GENERATED_AT = "2026-06-03T01:10:00Z"

OPERATION_ORDER = [
    "create_prediction",
    "update_prediction",
    "start_prediction",
    "pause_prediction",
    "resume_prediction",
    "run_tick",
    "resolve_due",
    "append_evidence",
    "read_status",
    "database_source_adapter_status",
    "read_forecast_card",
    "read_lifecycle_bundle",
    "archive_record",
    "redact_record",
]


class InternalApiError(Exception):
    pass


def operation(
    name: str,
    kind: str,
    status: str,
    side_effect: str,
    lifecycle_operations: list[str],
    read_models: list[str],
    notes: str,
    *,
    receipt: bool,
    lease: bool,
) -> dict[str, Any]:
    return {
        "operationName": name,
        "operationKind": kind,
        "implementationStatus": status,
        "sideEffectLevel": side_effect,
        "inProcessFunctionName": name,
        "cliCommand": f"python3 scripts/ope.py internal-api --operation {name}",
        "agentCallOperation": name,
        "lifecycleOperations": lifecycle_operations,
        "requiresOperationReceipt": receipt,
        "returnsOperationReceipt": receipt,
        "requiresIdempotencyKey": receipt,
        "requiresLease": lease,
        "returnsReadModels": read_models,
        "returnsSanitizedDiagnostics": True,
        "rawFileLayoutExposed": False,
        "rawSqlExposed": False,
        "notes": notes,
    }


def operation_surface() -> list[dict[str, Any]]:
    return [
        operation(
            "create_prediction",
            "effectful",
            "defined_surface",
            "receipt_backed_mutation",
            ["prediction.config_create"],
            ["campaign_status", "next_due_forecast", "recovery_actions"],
            "Create a prediction configuration through a receipt-backed operation, not raw file or SQL writes.",
            receipt=True,
            lease=True,
        ),
        operation(
            "update_prediction",
            "effectful",
            "defined_surface",
            "receipt_backed_mutation",
            ["prediction.config_update"],
            ["campaign_status", "recovery_actions"],
            "Update prediction configuration through audited lifecycle state, preserving prior configuration history.",
            receipt=True,
            lease=True,
        ),
        operation(
            "start_prediction",
            "effectful",
            "mapped_to_existing_lifecycle_operation",
            "receipt_backed_mutation",
            ["forecast.create"],
            ["campaign_status", "next_due_forecast", "unresolved_forecasts"],
            "Start or create the next due forecast through the forecast.create lifecycle operation.",
            receipt=True,
            lease=True,
        ),
        operation(
            "pause_prediction",
            "effectful",
            "defined_surface",
            "receipt_backed_mutation",
            ["prediction.pause"],
            ["campaign_status", "recovery_actions"],
            "Pause future ticks without deleting existing forecasts, histories, scores, or evidence rows.",
            receipt=True,
            lease=True,
        ),
        operation(
            "resume_prediction",
            "effectful",
            "defined_surface",
            "receipt_backed_mutation",
            ["prediction.resume"],
            ["campaign_status", "next_due_forecast", "recovery_actions"],
            "Resume a paused prediction through a receipt-backed operation with bounded next actions.",
            receipt=True,
            lease=True,
        ),
        operation(
            "run_tick",
            "bounded_tick",
            "defined_surface",
            "bounded_tick",
            ["prediction.tick"],
            ["campaign_status", "next_due_forecast", "due_resolution_jobs", "recovery_actions"],
            "Run one bounded foreground tick; background worker loops must preserve the same semantics later.",
            receipt=True,
            lease=True,
        ),
        operation(
            "resolve_due",
            "effectful",
            "mapped_to_existing_lifecycle_operation",
            "receipt_backed_mutation",
            ["resolution.record", "score.create"],
            ["campaign_status", "due_resolution_jobs", "append_readiness"],
            "Resolve due forecasts through resolution and scoring lifecycle operations.",
            receipt=True,
            lease=True,
        ),
        operation(
            "append_evidence",
            "effectful",
            "mapped_to_existing_lifecycle_operation",
            "receipt_backed_mutation",
            ["evidence.append"],
            ["campaign_status", "append_readiness", "calibration_status", "track_record_progress"],
            "Append comparable or excluded evidence rows through the append-only evidence operation.",
            receipt=True,
            lease=True,
        ),
        operation(
            "read_status",
            "read_only",
            "mapped_to_existing_read_surface",
            "read_only",
            [],
            ["campaign_status", "next_due_forecast", "due_resolution_jobs", "append_readiness"],
            "Read prediction and campaign status from read models without mutating state.",
            receipt=False,
            lease=False,
        ),
        operation(
            "database_source_adapter_status",
            "read_only",
            "mapped_to_existing_read_surface",
            "read_only",
            [],
            ["source_adapter_runtime_status"],
            "Read approved database source-adapter runtime status and blocked-case diagnostics without opening database connections.",
            receipt=False,
            lease=False,
        ),
        operation(
            "read_forecast_card",
            "read_only",
            "mapped_to_existing_read_surface",
            "read_only",
            [],
            ["forecast_card"],
            "Read compact forecast-card output for downstream decisions.",
            receipt=False,
            lease=False,
        ),
        operation(
            "read_lifecycle_bundle",
            "read_only",
            "mapped_to_existing_read_surface",
            "read_only",
            [],
            ["lifecycle_bundle"],
            "Read lifecycle bundle output for audit context without exposing raw storage layout.",
            receipt=False,
            lease=False,
        ),
        operation(
            "archive_record",
            "retention",
            "mapped_to_existing_lifecycle_operation",
            "retention_mutation",
            ["record.archive"],
            ["campaign_status", "append_readiness", "recovery_actions"],
            "Archive records from active views with tombstone receipts instead of physical deletion.",
            receipt=True,
            lease=True,
        ),
        operation(
            "redact_record",
            "retention",
            "mapped_to_existing_lifecycle_operation",
            "retention_mutation",
            ["record.redact"],
            ["campaign_status", "append_readiness", "recovery_actions"],
            "Redact unsafe or private fields through redaction receipts, preserving audit metadata.",
            receipt=True,
            lease=True,
        ),
    ]


def adapter_surfaces() -> list[dict[str, Any]]:
    return [
        {
            "adapterName": "in_process_python",
            "adapterStatus": "defined_required",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "Host applications should call these operation functions directly when embedding OPE.",
        },
        {
            "adapterName": "cli",
            "adapterStatus": "defined_required",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "The CLI wrapper should call the same operation functions as in-process use.",
        },
        {
            "adapterName": "agent_call",
            "adapterStatus": "defined_required",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "Agent-call wrappers should return compact envelopes over the same semantics.",
        },
        {
            "adapterName": "mcp_stdio",
            "adapterStatus": "planned_wrapper",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "Local MCP remains a wrapper over internal operations, not a separate behavior layer.",
        },
        {
            "adapterName": "http",
            "adapterStatus": "future_transport",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "HTTP is a future transport over the internal API, not an independent runtime.",
        },
        {
            "adapterName": "queue",
            "adapterStatus": "future_transport",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "Queue execution is deferred until worker semantics and resource bounds are checked.",
        },
        {
            "adapterName": "hosted_service",
            "adapterStatus": "future_transport",
            "sharesInternalSemantics": True,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "notes": "Hosted service runtime is a future deployment adapter over the internal API, not a separate behavior layer.",
        },
    ]


def build_internal_api() -> dict[str, Any]:
    operations = operation_surface()
    effectful = [item for item in operations if item["operationKind"] != "read_only"]
    read_only = [item for item in operations if item["operationKind"] == "read_only"]
    record = {
        "internalApiId": "internalapi-001",
        "generatedAt": GENERATED_AT,
        "apiStatus": "stable_surface_defined",
        "designScope": "embedded_internal_api",
        "operationSurface": operations,
        "adapterSurfaces": adapter_surfaces(),
        "requestEnvelope": {
            "requiredFields": ["operationName", "callerId", "predictionId", "input"],
            "optionalFields": ["idempotencyKey", "maxBytes", "dryRun", "callerIntent", "sourcePolicyId", "domainId"],
            "maxBytesRequired": True,
            "credentialValuesAllowed": False,
            "rawSqlAllowed": False,
            "rawPathMutationAllowed": False,
        },
        "responseEnvelope": {
            "requiredFields": ["operationName", "status", "exitCode", "payload", "warnings"],
            "effectfulFields": [
                "operationReceiptId",
                "idempotencyStatus",
                "blockingGuards",
                "leaseStatus",
                "nextActions",
                "sanitizedDiagnostics",
            ],
            "readOnlyFields": ["readModelRefs", "recordRefs", "claimBoundary"],
            "sanitizedErrorsRequired": True,
            "responseTooLargeStatus": "response_too_large",
        },
        "nonInterferenceBoundary": {
            "surpriseNetworkCallsAllowed": False,
            "unboundedLoopsAllowed": False,
            "hiddenSchedulerInstallationAllowed": False,
            "automaticMethodUpgradesAllowed": False,
            "storesCredentialValues": False,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "hostedRuntimeRequired": False,
        },
        "summary": {
            "operationCount": len(operations),
            "effectfulOperationCount": len(effectful),
            "readOnlyOperationCount": len(read_only),
            "allEffectfulOperationsReceiptBacked": all(item["returnsOperationReceipt"] for item in effectful),
            "allEffectfulOperationsIdempotent": all(item["requiresIdempotencyKey"] for item in effectful),
            "allEffectfulOperationsLeaseAware": all(item["requiresLease"] for item in effectful),
            "allEffectfulCallsReturnReceiptFields": True,
            "inProcessSurfaceDefined": True,
            "cliSurfaceDefined": True,
            "agentCallSurfaceDefined": True,
            "httpAndQueueAreFutureTransports": True,
            "hostedServiceIsFutureAdapter": True,
            "compactRequestResponseEnvelopesDefined": True,
            "nonInterferenceBoundaryDefined": True,
        },
        "warnings": [
            "This is a stable internal API surface definition, not a hosted service runtime.",
            "Effectful calls must return operation receipts and never expose raw SQL or raw local file paths.",
            "Read-only calls return compact read models and record references without mutating state.",
            "HTTP, queue, and hosted service adapters remain future transports over the same internal semantics.",
        ],
    }
    validate_internal_api(record)
    return record


def validate_internal_api(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise InternalApiError(f"internal API schema validation failed: {errors[0]}")
    operations = {item["operationName"]: item for item in record["operationSurface"]}
    if list(operations) != OPERATION_ORDER:
        raise InternalApiError("internal API operation order drifted")
    effectful = [item for item in operations.values() if item["operationKind"] != "read_only"]
    read_only = [item for item in operations.values() if item["operationKind"] == "read_only"]
    for item in effectful:
        if not item["requiresOperationReceipt"] or not item["returnsOperationReceipt"]:
            raise InternalApiError(f"effectful operation must be receipt-backed: {item['operationName']}")
        if not item["requiresIdempotencyKey"] or not item["requiresLease"]:
            raise InternalApiError(f"effectful operation must require idempotency and leases: {item['operationName']}")
        if not item["lifecycleOperations"]:
            raise InternalApiError(f"effectful operation must map to lifecycle semantics: {item['operationName']}")
    for item in read_only:
        if item["requiresOperationReceipt"] or item["returnsOperationReceipt"]:
            raise InternalApiError(f"read-only operation must not require receipts: {item['operationName']}")
        if item["requiresIdempotencyKey"] or item["requiresLease"]:
            raise InternalApiError(f"read-only operation must not require idempotency or leases: {item['operationName']}")
    for item in operations.values():
        if item["rawFileLayoutExposed"] or item["rawSqlExposed"]:
            raise InternalApiError("internal API operations must not expose raw storage")
        if not item["returnsSanitizedDiagnostics"]:
            raise InternalApiError("internal API operations must return sanitized diagnostics")
    adapters = {item["adapterName"]: item for item in record["adapterSurfaces"]}
    if set(adapters) != {"in_process_python", "cli", "agent_call", "mcp_stdio", "http", "queue", "hosted_service"}:
        raise InternalApiError("adapter surface coverage drifted")
    for item in adapters.values():
        if not item["sharesInternalSemantics"] or item["rawSqlExposed"] or item["rawFileLayoutExposed"]:
            raise InternalApiError("adapters must share internal semantics without raw storage exposure")
    boundary = record["nonInterferenceBoundary"]
    if any(boundary.values()):
        raise InternalApiError("non-interference boundary must keep all risk flags false")
    summary = record["summary"]
    if summary["operationCount"] != len(OPERATION_ORDER):
        raise InternalApiError("internal API operation count drifted")
    if not summary["allEffectfulOperationsReceiptBacked"]:
        raise InternalApiError("all effectful operations must be receipt-backed")
    if not summary["allEffectfulOperationsIdempotent"] or not summary["allEffectfulOperationsLeaseAware"]:
        raise InternalApiError("all effectful operations must be idempotent and lease-aware")


def write_internal_api(record: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        record,
        label="internal API",
        regen="python3 scripts/generate_internal_api.py --write",
    )


def check_internal_api(record: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        record,
        label="internal API",
        regen="python3 scripts/generate_internal_api.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--operation", choices=OPERATION_ORDER, help="print one internal API operation")
    parser.add_argument("--call", action="store_true", help="call the internal API operation in non-mutating dry-run mode")
    parser.add_argument("--caller-id", default="agent-alpha")
    parser.add_argument("--prediction-id", default="predictioncampaign-001")
    parser.add_argument("--idempotency-key")
    parser.add_argument("--max-bytes", type=int, default=65536)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        record = build_internal_api()
        if args.call:
            if not args.operation:
                raise InternalApiError("--call requires --operation")
            from internal_api_runtime import call_internal_api

            sys.stdout.write(
                render_json(
                    call_internal_api(
                        args.operation,
                        caller_id=args.caller_id,
                        prediction_id=args.prediction_id,
                        idempotency_key=args.idempotency_key,
                        max_bytes=args.max_bytes,
                    )
                )
            )
        elif args.operation:
            item = next(item for item in record["operationSurface"] if item["operationName"] == args.operation)
            sys.stdout.write(render_json(item))
        elif args.write:
            write_internal_api(record)
        elif args.check:
            check_internal_api(record)
        else:
            sys.stdout.write(render_json(record))
    except InternalApiError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
