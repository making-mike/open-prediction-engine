#!/usr/bin/env python3
"""Bounded local background worker loop helpers."""

from __future__ import annotations

import json
from typing import Any

from generate_prediction_workspace_registry import build_prediction_workspace_registry
from internal_api_runtime import call_internal_api
from lifecycle_operation_store_runtime import (
    campaign_forecast_create_request,
    execute_operation,
    lease_key,
    open_sqlite,
    read_model_effects_for_result,
    table_counts,
)
from ope_fixtures import render_json


WORKER_ID = "backgroundworker-001"
GENERATED_AT = "2026-06-04T16:30:00Z"


class BackgroundWorkerLoopError(Exception):
    pass


def queue_poll_readback(worker_runtime: dict[str, Any]) -> dict[str, Any]:
    queue = worker_runtime["operationQueue"]
    return {
        "queueSource": queue["queueSource"],
        "readModelsPolled": queue["polledReadModels"],
        "candidateOperationNames": [
            "recover_stale_lease",
            "resolve_due",
            "append_evidence",
            "run_tick",
            "maintenance_readback",
        ],
        "selectedOperationName": "run_tick",
        "selectedReadModel": "due_forecasts",
        "rawSqlExposed": False,
        "rawFileLayoutExposed": False,
    }


def cancellation_readback() -> dict[str, bool]:
    return {
        "supported": True,
        "cancellationRequested": False,
        "checkedBeforeTick": True,
        "checkedBetweenOperations": True,
        "stopsBeforeMutation": True,
    }


def retry_backoff_readback() -> dict[str, Any]:
    return {
        "policy": "bounded_exponential",
        "maxAttemptsPerOperation": 2,
        "initialDelayMilliseconds": 100,
        "maxDelayMilliseconds": 1000,
        "sameIdempotencyKeyOnRetry": True,
        "sanitizedDiagnosticsOnly": True,
    }


def run_bounded_worker_loop(
    worker_runtime: dict[str, Any],
    *,
    max_ticks: int = 1,
    dry_run: bool = True,
) -> dict[str, Any]:
    if max_ticks < 1:
        raise BackgroundWorkerLoopError("bounded worker loop requires max_ticks >= 1")

    limits = worker_runtime["resourceLimits"]
    if max_ticks > limits["maxTicksPerLoop"]:
        raise BackgroundWorkerLoopError("bounded worker loop cannot exceed configured maxTicksPerLoop")

    registry = build_prediction_workspace_registry()
    active = registry["readModels"]["activePredictions"][0]
    one_tick = worker_runtime["oneTickReadback"]
    next_operation = one_tick["nextOperation"]
    api_call = call_internal_api(
        "run_tick",
        caller_id=WORKER_ID,
        prediction_id=active["predictionId"],
        idempotency_key=next_operation["idempotencyKey"],
        dry_run=dry_run,
        max_bytes=limits["maxReadbackBytes"],
    )
    rendered_bytes = len(render_json(api_call).encode("utf-8"))
    tick_execution = {
        "tickId": "workertick-001",
        "tickStatus": "completed_dry_run",
        "foregroundEquivalent": True,
        "internalApiOperation": "run_tick",
        "predictionId": active["predictionId"],
        "campaignId": active["campaignId"],
        "operationReceiptId": api_call["operationReceiptId"],
        "idempotencyKey": next_operation["idempotencyKey"],
        "leaseId": next_operation["leaseId"],
        "leaseScope": next_operation["leaseScope"],
        "preflightStatus": "pass",
        "internalApiCall": api_call,
    }
    return {
        "loopId": "workerloop-001",
        "workerId": WORKER_ID,
        "loopStatus": "completed_dry_run",
        "dryRun": dry_run,
        "writesState": False,
        "maxTicksRequested": max_ticks,
        "ticksExecuted": 1,
        "operationsAttempted": 1,
        "queuePoll": queue_poll_readback(worker_runtime),
        "tickExecutions": [tick_execution],
        "cancellation": cancellation_readback(),
        "retryBackoff": retry_backoff_readback(),
        "resourceUsage": {
            "withinLimits": True,
            "ticksAttempted": 1,
            "operationsAttempted": 1,
            "maxOperationsPerTick": limits["maxOperationsPerTick"],
            "wallClockSecondsBudgeted": limits["maxWallClockSecondsPerTick"],
            "readbackBytes": rendered_bytes,
            "maxReadbackBytes": limits["maxReadbackBytes"],
            "sourceFetchAttempted": False,
        },
        "terminationReason": "max_ticks_reached",
        "sourceFetchAttempted": False,
        "sidecarBoundary": worker_runtime["sidecarBoundary"],
    }


def run_approved_worker_commit(worker_runtime: dict[str, Any]) -> dict[str, Any]:
    conn = open_sqlite()
    try:
        one_tick = worker_runtime["oneTickReadback"]
        next_operation = one_tick["nextOperation"]
        request = campaign_forecast_create_request()
        request["callerId"] = WORKER_ID
        request["operationReceiptId"] = "operationreceipt-worker-commit-001"
        request["idempotencyKey"] = next_operation["idempotencyKey"].replace(":run_tick:", ":forecast.create:")
        request["leaseSeconds"] = 60
        request["payload"]["backgroundWorkerCommitPath"] = True
        result = execute_operation(conn, request, now=GENERATED_AT)
        lease_count_after_commit = result["tableCountsAfter"]["operation_leases"]
        current_lease_key = lease_key(request)
        with conn:
            conn.execute(
                "DELETE FROM operation_leases WHERE lease_key = ? AND owner_id = ?",
                (current_lease_key, WORKER_ID),
            )
        counts_after_release = table_counts(conn)
        return {
            "commitId": "workercommit-001",
            "approvalRequired": True,
            "approvalStatus": "fixture_approved",
            "stateWritingMode": "ephemeral_sqlite_check",
            "normalChecksWritePersistentState": False,
            "workerOperationName": next_operation["operationName"],
            "internalApiOperation": one_tick["internalApiOperation"],
            "lifecycleOperationName": request["operationName"],
            "operationReceiptId": result["operationReceiptId"],
            "idempotencyKey": request["idempotencyKey"],
            "sameIdempotencyKeyOnRetry": True,
            "leaseLifecycle": {
                "leaseKey": current_lease_key,
                "leaseReserved": result["sqliteWrites"]["leasesWritten"] == 1,
                "leaseReleased": counts_after_release["operation_leases"] == 0,
                "leaseCountAfterCommit": lease_count_after_commit,
                "leaseCountAfterRelease": counts_after_release["operation_leases"],
                "releasePolicy": "release_after_receipt_or_expiry",
            },
            "lifecycleResult": {
                "operationName": result["operationName"],
                "operationReceiptId": result["operationReceiptId"],
                "operationStatus": result["operationStatus"],
                "preflightStatus": result["preflight"]["preflightStatus"],
                "idempotencyStatus": result["preflight"]["idempotencyStatus"],
                "leaseStatus": result["preflight"]["leaseStatus"],
                "plannedWriteCount": len(result["preflight"]["plannedWrites"]),
                "sqliteWrites": result["sqliteWrites"],
                "readModelEffects": read_model_effects_for_result(result),
                "recoveryPath": result["preflight"]["recoveryPath"],
                "claimBoundary": result["preflight"]["claimBoundary"],
                "message": result["message"],
            },
            "executionBoundary": {
                "persistentStateWritten": False,
                "ephemeralSqliteOnly": True,
                "rawSqlExposed": False,
                "rawFileLayoutExposed": False,
                "networkAccessed": False,
                "sourceFetchAttempted": False,
                "automaticMethodUpgrade": False,
                "qualityClaimCreated": False,
            },
        }
    finally:
        conn.close()


CONTROL_ACTIONS = [
    ("pause", "paused", False, True),
    ("resume", "running", True, False),
    ("drain", "draining", False, True),
    ("shutdown", "stopped", False, True),
]


def worker_control_state_payload(
    *,
    action: str,
    worker_state: str,
    accepts_new_operations: bool,
    cancellation_requested: bool,
    receipt_id: str,
) -> dict[str, Any]:
    return {
        "stateType": "worker_control_state",
        "stateVersion": 1,
        "workerId": WORKER_ID,
        "controlAction": action,
        "workerState": worker_state,
        "acceptsNewOperations": accepts_new_operations,
        "cancellationRequested": cancellation_requested,
        "updatedByOperationReceiptId": receipt_id,
        "updatedAt": GENERATED_AT,
        "rawControlMutationAllowed": False,
        "claimBoundary": {
            "createsQualityClaim": False,
            "allowsPostOutcomeRewrite": False,
            "allowsSilentDelete": False,
            "allowsRawCrud": False,
        },
    }


def worker_control_request(
    *,
    action: str,
    worker_state: str,
    accepts_new_operations: bool,
    cancellation_requested: bool,
    index: int,
) -> dict[str, Any]:
    receipt_id = f"operationreceipt-worker-control-{index:03d}"
    state_payload = worker_control_state_payload(
        action=action,
        worker_state=worker_state,
        accepts_new_operations=accepts_new_operations,
        cancellation_requested=cancellation_requested,
        receipt_id=receipt_id,
    )
    return {
        "operationName": "state.import_json",
        "operationReceiptId": receipt_id,
        "campaignId": "workercontrolcampaign-001",
        "runId": f"workercontrolrun-{index:03d}",
        "forecastId": f"workercontrolforecast-{index:03d}",
        "callerId": WORKER_ID,
        "idempotencyKey": f"{WORKER_ID}:{action}:control:{GENERATED_AT}",
        "sourceRecordHash": f"sha256-worker-control-{action}",
        "targetRecordId": WORKER_ID,
        "leaseResourceId": f"{WORKER_ID}:control-state",
        "leaseSeconds": 30,
        "payload": {
            "backgroundWorkerControlState": True,
            "controlAction": action,
            "workerState": worker_state,
            "qualityClaimAllowed": False,
        },
        "recordPayloads": {
            WORKER_ID: state_payload,
            "worker_control_state": state_payload,
        },
        "migrationWrites": [
            {
                "tableName": "read_model_rows",
                "recordType": "worker_control_state",
                "recordId": WORKER_ID,
                "writeMode": "projection_upsert",
            },
        ],
    }


def control_command_readback(
    *,
    action: str,
    worker_state: str,
    accepts_new_operations: bool,
    result: dict[str, Any],
    lease_released: bool,
) -> dict[str, Any]:
    return {
        "commandName": action,
        "commandKind": "write",
        "lifecycleOperationName": result["operationName"],
        "operationReceiptId": result["operationReceiptId"],
        "idempotencyKey": result["preflight"]["idempotencyKey"],
        "leaseReserved": result["sqliteWrites"]["leasesWritten"] == 1,
        "leaseReleased": lease_released,
        "writesState": True,
        "workerStateAfter": worker_state,
        "acceptsNewOperationsAfter": accepts_new_operations,
        "readModelUpdated": result["sqliteWrites"]["readModelRowsWritten"] >= 1,
        "rawControlMutationAllowed": False,
    }


def run_worker_control_state(worker_runtime: dict[str, Any]) -> dict[str, Any]:
    del worker_runtime
    conn = open_sqlite()
    try:
        control_commands: list[dict[str, Any]] = [
            {
                "commandName": "health",
                "commandKind": "read",
                "lifecycleOperationName": "read_model",
                "operationReceiptId": "",
                "idempotencyKey": "",
                "leaseReserved": False,
                "leaseReleased": False,
                "writesState": False,
                "readsControlState": True,
                "rawControlMutationAllowed": False,
            }
        ]
        control_writes: list[dict[str, Any]] = []
        releases = 0
        for index, (action, worker_state, accepts_new_operations, cancellation_requested) in enumerate(CONTROL_ACTIONS, start=1):
            request = worker_control_request(
                action=action,
                worker_state=worker_state,
                accepts_new_operations=accepts_new_operations,
                cancellation_requested=cancellation_requested,
                index=index,
            )
            result = execute_operation(conn, request, now=GENERATED_AT)
            current_lease_key = lease_key(request)
            with conn:
                conn.execute(
                    "DELETE FROM operation_leases WHERE lease_key = ? AND owner_id = ?",
                    (current_lease_key, WORKER_ID),
                )
            lease_released = table_counts(conn)["operation_leases"] == 0
            if lease_released:
                releases += 1
            control_commands.append(
                control_command_readback(
                    action=action,
                    worker_state=worker_state,
                    accepts_new_operations=accepts_new_operations,
                    result=result,
                    lease_released=lease_released,
                )
            )
            control_writes.append(
                {
                    "commandName": action,
                    "lifecycleOperationName": result["operationName"],
                    "operationReceiptId": result["operationReceiptId"],
                    "operationStatus": result["operationStatus"],
                    "preflightStatus": result["preflight"]["preflightStatus"],
                    "idempotencyStatus": result["preflight"]["idempotencyStatus"],
                    "leaseStatus": result["preflight"]["leaseStatus"],
                    "sqliteWrites": result["sqliteWrites"],
                    "readModelEffects": ["worker_control_state", *read_model_effects_for_result(result)],
                    "leaseKey": current_lease_key,
                    "leaseReleased": lease_released,
                    "claimBoundary": result["preflight"]["claimBoundary"],
                }
            )
        row = conn.execute(
            "SELECT row_json FROM read_model_rows WHERE read_model_name = ? AND row_key = ?",
            ("worker_control_state", WORKER_ID),
        ).fetchone()
        if row is None:
            raise BackgroundWorkerLoopError("worker control state read model was not written")
        state = json.loads(row["row_json"])
        receipt_count = sum(item["sqliteWrites"]["operationReceiptsWritten"] for item in control_writes)
        idempotency_count = sum(item["sqliteWrites"]["idempotencyKeysWritten"] for item in control_writes)
        lease_count = sum(item["sqliteWrites"]["leasesWritten"] for item in control_writes)
        return {
            "controlStateExecutionId": "workercontrolstate-001",
            "controlStateStatus": "lifecycle_backed_control_state_checked",
            "persistentStateSemantics": True,
            "stateWritingMode": "ephemeral_sqlite_check",
            "normalChecksWritePersistentState": False,
            "controlReadModelName": "worker_control_state",
            "controlCommands": control_commands,
            "controlWrites": control_writes,
            "healthReadback": {
                "workerId": state["workerId"],
                "readsControlState": True,
                "lastControlCommand": state["controlAction"],
                "workerState": state["workerState"],
                "acceptsNewOperations": state["acceptsNewOperations"],
                "cancellationRequested": state["cancellationRequested"],
                "updatedByOperationReceiptId": state["updatedByOperationReceiptId"],
                "rawControlMutationAllowed": state["rawControlMutationAllowed"],
            },
            "summary": {
                "controlWriteCount": len(control_writes),
                "lifecycleReceiptsWritten": receipt_count,
                "idempotencyKeysWritten": idempotency_count,
                "leasesReserved": lease_count,
                "leasesReleased": releases,
                "rawControlMutationAllowed": False,
            },
            "executionBoundary": {
                "persistentStateWritten": False,
                "ephemeralSqliteOnly": True,
                "rawSqlExposed": False,
                "rawFileLayoutExposed": False,
                "networkAccessed": False,
                "sourceFetchAttempted": False,
                "hiddenSchedulerInstallation": False,
            },
        }
    finally:
        conn.close()


def sidecar_launch_mode(
    mode_name: str,
    implementation_status: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "modeName": mode_name,
        "implementationStatus": implementation_status,
        "localOnly": True,
        "networkListenerStarted": False,
        "osSchedulerInstalled": False,
        "hiddenDaemon": False,
        "hostedWorkerRequired": False,
        "notes": notes,
    }


def sidecar_sequence_step(
    step_name: str,
    command: str,
    expected_readback: str,
    *,
    lifecycle_backed: bool,
) -> dict[str, Any]:
    return {
        "stepName": step_name,
        "command": command,
        "expectedReadback": expected_readback,
        "bounded": True,
        "lifecycleBacked": lifecycle_backed,
        "rawStateMutationAllowed": False,
    }


def build_durable_sidecar_execution(worker_runtime: dict[str, Any]) -> dict[str, Any]:
    control = worker_runtime["controlStateExecution"]
    loop = worker_runtime["boundedLoopExecution"]
    commit = worker_runtime["approvedCommitExecution"]
    return {
        "sidecarExecutionId": "workersidecar-001",
        "sidecarStatus": "checked_local_sidecar_semantics",
        "controlStateReadModel": control["controlReadModelName"],
        "defaultLaunchMode": "embedded_in_process",
        "normalChecksStartProcess": False,
        "bounded": True,
        "maxTicksPerActivation": loop["maxTicksRequested"],
        "launchModes": [
            sidecar_launch_mode(
                "embedded_in_process",
                "checked_default",
                "Host calls the worker loop in-process for one bounded activation and keeps control state in read models.",
            ),
            sidecar_launch_mode(
                "local_sidecar_process",
                "planned_explicit_local_process",
                "A future explicit local process may wrap the same commands without installing a daemon or listener.",
            ),
        ],
        "hostNonInterference": {
            "hostCanContinueWhileWorkerIdle": True,
            "hostCanInspectHealthWithoutBlocking": True,
            "workerDoesNotOwnHostEventLoop": True,
            "activationRequiresExplicitCall": True,
            "maxReadbackBytes": worker_runtime["resourceLimits"]["maxReadbackBytes"],
        },
        "activationReadback": {
            "activationId": "workersidecaractivation-001",
            "activationStatus": "ready_for_bounded_activation",
            "readsControlStateBeforeTick": True,
            "runsBoundedLoop": True,
            "usesApprovedCommitPath": True,
            "stopsOnControlState": True,
            "boundedLoopId": loop["loopId"],
            "commitId": commit["commitId"],
            "heartbeatReadback": {
                "heartbeatId": "workerheartbeat-001",
                "heartbeatStatus": "healthy_idle",
                "workerState": "running",
                "controlReadModelName": control["controlReadModelName"],
                "queueSource": worker_runtime["operationQueue"]["queueSource"],
                "rawStorageExposed": False,
            },
            "shutdownReadback": {
                "shutdownId": "workershutdown-001",
                "shutdownStatus": "clean_shutdown_readback",
                "workerState": control["healthReadback"]["workerState"],
                "lastControlCommand": control["healthReadback"]["lastControlCommand"],
                "acceptsNewOperations": control["healthReadback"]["acceptsNewOperations"],
            },
        },
        "executionSequence": [
            sidecar_sequence_step(
                "start",
                "python3 scripts/ope.py background-worker --view control",
                "Read lifecycle-backed worker control state before accepting a tick.",
                lifecycle_backed=True,
            ),
            sidecar_sequence_step(
                "heartbeat",
                "python3 scripts/ope.py background-worker --view sidecar",
                "Return compact healthy-idle heartbeat without raw storage access.",
                lifecycle_backed=False,
            ),
            sidecar_sequence_step(
                "run_tick",
                "python3 scripts/ope.py background-worker --view loop",
                "Run one foreground-equivalent bounded dry-run tick.",
                lifecycle_backed=True,
            ),
            sidecar_sequence_step(
                "commit",
                "python3 scripts/ope.py background-worker --view commit",
                "Commit through ephemeral SQLite operation receipts in normal checks.",
                lifecycle_backed=True,
            ),
            sidecar_sequence_step(
                "drain",
                "python3 scripts/ope.py background-worker --view control",
                "Observe drain control state and stop taking new operations.",
                lifecycle_backed=True,
            ),
            sidecar_sequence_step(
                "shutdown",
                "python3 scripts/ope.py background-worker --view control",
                "Observe shutdown control state and return clean shutdown readback.",
                lifecycle_backed=True,
            ),
        ],
        "executionBoundary": {
            "networkListenerStarted": False,
            "osSchedulerInstalled": False,
            "hostedWorkerRequired": False,
            "hiddenDaemonStarted": False,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "automaticLiveSourceExecution": False,
            "automaticMethodUpgrade": False,
            "normalChecksStartProcess": False,
            "normalChecksWritePersistentState": False,
        },
    }
