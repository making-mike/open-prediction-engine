#!/usr/bin/env python3
"""In-process embedded internal API call helpers."""

from __future__ import annotations

from typing import Any

from generate_internal_api import OPERATION_ORDER, build_internal_api


DEFAULT_CALLER_ID = "agent-alpha"
DEFAULT_PREDICTION_ID = "predictioncampaign-001"


class InternalApiRuntimeError(Exception):
    pass


def operation_spec(operation_name: str) -> dict[str, Any]:
    api = build_internal_api()
    for item in api["operationSurface"]:
        if item["operationName"] == operation_name:
            return item
    raise InternalApiRuntimeError(f"unsupported internal API operation: {operation_name}")


def call_internal_api(
    operation_name: str,
    *,
    caller_id: str = DEFAULT_CALLER_ID,
    prediction_id: str = DEFAULT_PREDICTION_ID,
    idempotency_key: str | None = None,
    dry_run: bool = True,
    max_bytes: int = 65536,
) -> dict[str, Any]:
    spec = operation_spec(operation_name)
    effectful = spec["operationKind"] != "read_only"
    if operation_name not in OPERATION_ORDER:
        raise InternalApiRuntimeError(f"unsupported internal API operation: {operation_name}")
    if effectful and not idempotency_key:
        idempotency_key = f"{prediction_id}:{operation_name}:dry-run"
    status = "dry_run_ready" if effectful else "read_ready"
    receipt_id = f"operationreceipt-internal-{OPERATION_ORDER.index(operation_name) + 401:03d}" if effectful else None
    blocking_guards = [
        {
            "guardId": "internalapiguard-001",
            "guardStatus": "pass",
            "blocksOperation": False,
            "message": "Internal API call uses lifecycle semantics, not raw files or raw SQL.",
        },
        {
            "guardId": "internalapiguard-002",
            "guardStatus": "pass",
            "blocksOperation": False,
            "message": "Dry-run wrapper does not mutate state; effectful adapters must commit through operation receipts.",
        },
    ]
    return {
        "internalApiCallId": f"internalapicall-{OPERATION_ORDER.index(operation_name) + 1:03d}",
        "operationName": operation_name,
        "callerId": caller_id,
        "predictionId": prediction_id,
        "callStatus": status,
        "dryRun": dry_run,
        "operationKind": spec["operationKind"],
        "lifecycleOperations": spec["lifecycleOperations"],
        "operationReceiptId": receipt_id,
        "idempotencyKey": idempotency_key,
        "idempotencyStatus": "required" if effectful else "not_required",
        "leaseStatus": "required" if effectful else "not_required",
        "blockingGuards": blocking_guards,
        "readModelRefs": spec["returnsReadModels"],
        "nextActions": [
            "use_same_internal_operation_for_in_process_cli_and_agent_call",
            "commit_effectful_call_only_through_lifecycle_operation_store",
        ]
        if effectful
        else ["read_returned_payload_without_mutation"],
        "sanitizedDiagnostics": "Internal API wrapper executed in non-mutating dry-run mode.",
        "maxBytes": max_bytes,
        "executionBoundary": {
            "writesState": False,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "surpriseNetworkCalls": False,
            "unboundedLoop": False,
            "hiddenSchedulerInstallation": False,
            "automaticMethodUpgrade": False,
        },
    }


def create_prediction(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("create_prediction", **kwargs)


def update_prediction(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("update_prediction", **kwargs)


def start_prediction(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("start_prediction", **kwargs)


def pause_prediction(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("pause_prediction", **kwargs)


def resume_prediction(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("resume_prediction", **kwargs)


def run_tick(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("run_tick", **kwargs)


def resolve_due(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("resolve_due", **kwargs)


def append_evidence(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("append_evidence", **kwargs)


def read_status(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("read_status", **kwargs)


def read_forecast_card(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("read_forecast_card", **kwargs)


def read_lifecycle_bundle(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("read_lifecycle_bundle", **kwargs)


def archive_record(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("archive_record", **kwargs)


def redact_record(**kwargs: Any) -> dict[str, Any]:
    return call_internal_api("redact_record", **kwargs)
