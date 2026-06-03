#!/usr/bin/env python3
"""Check embedded internal API invariants."""

from __future__ import annotations

from generate_internal_api import OPERATION_ORDER, build_internal_api
from internal_api_runtime import call_internal_api
from ope_fixtures import render_json


REQUIRED_EFFECTFUL = {
    "create_prediction",
    "update_prediction",
    "start_prediction",
    "pause_prediction",
    "resume_prediction",
    "run_tick",
    "resolve_due",
    "append_evidence",
    "archive_record",
    "redact_record",
}

REQUIRED_READS = {"read_status", "read_forecast_card", "read_lifecycle_bundle"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    api = build_internal_api()
    operations = {item["operationName"]: item for item in api["operationSurface"]}
    require(list(operations) == OPERATION_ORDER, "internal API operation order drifted")
    require(set(operations) == set(OPERATION_ORDER), "internal API should expose the required stable operations")

    effectful = {name for name, item in operations.items() if item["operationKind"] != "read_only"}
    reads = {name for name, item in operations.items() if item["operationKind"] == "read_only"}
    require(effectful == REQUIRED_EFFECTFUL, "effectful internal API operation set drifted")
    require(reads == REQUIRED_READS, "read-only internal API operation set drifted")

    for name in REQUIRED_EFFECTFUL:
        item = operations[name]
        require(item["requiresOperationReceipt"] is True, f"{name} should require operation receipts")
        require(item["returnsOperationReceipt"] is True, f"{name} should return operation receipts")
        require(item["requiresIdempotencyKey"] is True, f"{name} should require idempotency")
        require(item["requiresLease"] is True, f"{name} should require leases")
        require(item["lifecycleOperations"], f"{name} should map to lifecycle operations")
        require(item["returnsSanitizedDiagnostics"] is True, f"{name} should return sanitized diagnostics")
        require(item["rawFileLayoutExposed"] is False, f"{name} must not expose raw file layout")
        require(item["rawSqlExposed"] is False, f"{name} must not expose raw SQL")
        call = call_internal_api(name)
        require(call["operationReceiptId"], f"{name} call should return an operation receipt id")
        require(call["idempotencyStatus"] == "required", f"{name} call should return idempotency status")
        require(call["leaseStatus"] == "required", f"{name} call should return lease status")
        require(call["blockingGuards"], f"{name} call should return blocking guards")
        require(call["nextActions"], f"{name} call should return next actions")
        require(call["sanitizedDiagnostics"], f"{name} call should return sanitized diagnostics")
        require(call["executionBoundary"]["writesState"] is False, f"{name} dry-run call should not write state")

    for name in REQUIRED_READS:
        item = operations[name]
        require(item["requiresOperationReceipt"] is False, f"{name} should not require receipts")
        require(item["returnsOperationReceipt"] is False, f"{name} should not return receipts")
        require(item["requiresIdempotencyKey"] is False, f"{name} should not require idempotency")
        require(item["requiresLease"] is False, f"{name} should not require leases")
        require(item["returnsReadModels"], f"{name} should return read models")

    adapters = {item["adapterName"]: item for item in api["adapterSurfaces"]}
    require(
        set(adapters) == {"in_process_python", "cli", "agent_call", "mcp_stdio", "http", "queue", "hosted_service"},
        "internal API adapter surface coverage drifted",
    )
    for item in adapters.values():
        require(item["sharesInternalSemantics"] is True, "adapters should share internal semantics")
        require(item["rawSqlExposed"] is False, "adapters must not expose raw SQL")
        require(item["rawFileLayoutExposed"] is False, "adapters must not expose raw file layout")
    require(adapters["http"]["adapterStatus"] == "future_transport", "HTTP should remain a future transport")
    require(adapters["queue"]["adapterStatus"] == "future_transport", "queue should remain a future transport")
    require(adapters["hosted_service"]["adapterStatus"] == "future_transport", "hosted service should remain a future adapter")

    boundary = api["nonInterferenceBoundary"]
    for key, value in boundary.items():
        require(value is False, f"non-interference boundary should keep {key} false")

    request_envelope = api["requestEnvelope"]
    require("operationName" in request_envelope["requiredFields"], "request envelope should require operationName")
    require("predictionId" in request_envelope["requiredFields"], "request envelope should require predictionId")
    require(request_envelope["maxBytesRequired"] is True, "request envelope should expose maxBytes")
    require(request_envelope["credentialValuesAllowed"] is False, "request envelope must not allow credential values")
    require(request_envelope["rawSqlAllowed"] is False, "request envelope must not allow raw SQL")
    require(request_envelope["rawPathMutationAllowed"] is False, "request envelope must not allow raw path mutation")

    response_envelope = api["responseEnvelope"]
    for field_name in ["operationReceiptId", "idempotencyStatus", "blockingGuards", "nextActions", "sanitizedDiagnostics"]:
        require(field_name in response_envelope["effectfulFields"], f"response envelope should include {field_name}")
    require(response_envelope["sanitizedErrorsRequired"] is True, "response envelope should require sanitized errors")
    require(response_envelope["responseTooLargeStatus"] == "response_too_large", "response envelope should define response-too-large status")
    compact_response = render_json(call_internal_api("start_prediction"))
    require(len(compact_response.encode("utf-8")) < 4096, "representative internal API response should stay compact")

    summary = api["summary"]
    require(summary["operationCount"] == 13, "internal API operation count drifted")
    require(summary["effectfulOperationCount"] == 10, "internal API effectful count drifted")
    require(summary["readOnlyOperationCount"] == 3, "internal API read-only count drifted")
    require(summary["allEffectfulOperationsReceiptBacked"] is True, "effectful operations should be receipt-backed")
    require(summary["allEffectfulOperationsIdempotent"] is True, "effectful operations should be idempotent")
    require(summary["allEffectfulOperationsLeaseAware"] is True, "effectful operations should be lease-aware")
    require(summary["allEffectfulCallsReturnReceiptFields"] is True, "effectful calls should return receipt/readback fields")
    require(summary["httpAndQueueAreFutureTransports"] is True, "HTTP and queue should remain future transports")
    require(summary["hostedServiceIsFutureAdapter"] is True, "hosted service should remain a future adapter")
    require(summary["compactRequestResponseEnvelopesDefined"] is True, "compact request/response envelopes should be defined")
    require(summary["nonInterferenceBoundaryDefined"] is True, "non-interference boundary should be defined")
    print("checked internal API")


if __name__ == "__main__":
    main()
