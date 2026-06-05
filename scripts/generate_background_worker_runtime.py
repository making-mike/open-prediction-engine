#!/usr/bin/env python3
"""Generate a checked background worker and sidecar runtime readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from background_worker_runtime import (
    build_durable_sidecar_execution,
    run_approved_worker_commit,
    run_bounded_worker_loop,
    run_worker_control_state,
)
from generate_internal_api import build_internal_api
from generate_prediction_workspace_registry import build_prediction_workspace_registry
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "background-worker-runtime"
OUTPUT_PATH = GENERATED / "ope-background-worker-runtime.generated.json"
SCHEMA = SPEC / "background-worker-runtime.schema.json"
GENERATED_AT = "2026-06-04T16:30:00Z"


class BackgroundWorkerRuntimeError(Exception):
    pass


def worker_command(
    name: str,
    status: str,
    notes: str,
    *,
    bounded: bool = True,
    requires_max_ticks: bool = False,
    writes_state: bool = False,
) -> dict[str, Any]:
    return {
        "commandName": name,
        "cliCommand": f"python3 scripts/ope.py background-worker {name.replace('_', '-')}",
        "commandStatus": status,
        "bounded": bounded,
        "requiresMaxTicks": requires_max_ticks,
        "writesState": writes_state,
        "exposesRawStorage": False,
        "startsNetworkListener": False,
        "notes": notes,
    }


def worker_commands() -> list[dict[str, Any]]:
    return [
        worker_command("health", "readback_defined", "Return compact worker health, queue, and boundary status."),
        worker_command("pause", "control_defined", "Request pause through lifecycle-aware control state, not raw mutation."),
        worker_command("resume", "control_defined", "Request resume through lifecycle-aware control state after pause is cleared."),
        worker_command("drain", "control_defined", "Stop taking new operations and finish only the bounded current tick."),
        worker_command("shutdown", "control_defined", "Return a clean shutdown readback without installing a hidden service."),
        worker_command("run_one_tick", "tick_defined", "Run or preview one deterministic foreground-equivalent worker tick."),
        worker_command(
            "run_bounded_loop",
            "tick_defined",
            "Run a local bounded loop with explicit max ticks; normal checks use one tick.",
            requires_max_ticks=True,
        ),
    ]


def operation_queue() -> dict[str, Any]:
    return {
        "queueSource": "prediction_workspace_read_models",
        "polledReadModels": [
            "active_predictions",
            "due_forecasts",
            "due_resolution_jobs",
            "append_readiness",
            "failed_operations",
            "recovery_actions",
            "source_health_blockers",
        ],
        "operationPriority": [
            "recover_stale_lease",
            "resolve_due",
            "append_evidence",
            "run_tick",
            "maintenance_readback",
        ],
        "rawSqlExposed": False,
        "rawFileLayoutExposed": False,
    }


def execution_guards() -> dict[str, bool]:
    return {
        "operationPreflightRequired": True,
        "idempotencyKeyRequired": True,
        "leaseRequired": True,
        "cancellationFlagSupported": True,
        "retryBackoffRequired": True,
        "responseSizeLimitRequired": True,
        "sourceFetchPolicyRequired": True,
    }


def resource_limits() -> dict[str, Any]:
    registry = build_prediction_workspace_registry()
    workspace_limits = registry["workspaceResourceControls"]
    return {
        "maxTicksPerLoop": 1,
        "maxOperationsPerTick": 3,
        "maxWallClockSecondsPerTick": 5,
        "maxQueueDepth": workspace_limits["maximumQueuedOperations"],
        "maxReadbackBytes": workspace_limits["maximumReadbackBytes"],
        "sourceFetchPolicy": "disabled_by_default",
    }


def one_tick_readback() -> dict[str, Any]:
    api = build_internal_api()
    operation = next(item for item in api["operationSurface"] if item["operationName"] == "run_tick")
    registry = build_prediction_workspace_registry()
    active = registry["readModels"]["activePredictions"][0]
    concurrency = next(
        item
        for item in registry["perPredictionConcurrencyControls"]
        if item["predictionId"] == active["predictionId"]
    )
    return {
        "tickId": "workertick-001",
        "tickStatus": "would_run",
        "foregroundEquivalent": True,
        "internalApiOperation": "run_tick",
        "writesState": False,
        "nextOperation": {
            "operationName": "run_tick",
            "predictionId": active["predictionId"],
            "campaignId": active["campaignId"],
            "operationReceiptId": "operationreceipt-worker-001",
            "idempotencyKey": f"{active['predictionId']}:run_tick:2026-06-04T16:30:00Z",
            "leaseId": concurrency["leaseId"],
            "leaseScope": concurrency["leaseScope"],
            "preflightStatus": "pass",
        },
        "readModelRefs": operation["returnsReadModels"],
        "blockingGuards": [
            {
                "guardName": "operation_preflight",
                "guardStatus": "pass",
                "blocksOperation": False,
                "message": "Worker tick uses the same run_tick preflight as the internal API.",
            },
            {
                "guardName": "lease_and_idempotency",
                "guardStatus": "pass",
                "blocksOperation": False,
                "message": "Worker tick reports the lease and idempotency key before execution.",
            },
            {
                "guardName": "source_fetch_policy",
                "guardStatus": "pass",
                "blocksOperation": False,
                "message": "Default worker tick does not perform automatic live-source execution.",
            },
        ],
        "safeNextAction": "Run the same operation through internal-api --operation run_tick --call or keep preview-only.",
    }


def blocked_case(
    case_id: str,
    operation_name: str,
    prediction_id: str,
    reason_code: str,
    safe_next_action: str,
) -> dict[str, Any]:
    return {
        "caseId": case_id,
        "operationName": operation_name,
        "predictionId": prediction_id,
        "blocked": True,
        "reasonCode": reason_code,
        "safeNextAction": safe_next_action,
        "sanitizedDiagnosticCode": f"{case_id}_blocked",
    }


def blocked_operation_readbacks() -> list[dict[str, Any]]:
    return [
        blocked_case(
            "paused_prediction",
            "run_tick",
            "prediction-002",
            "prediction_paused",
            "Resume the prediction through the internal API before worker execution.",
        ),
        blocked_case(
            "lease_conflict",
            "resolve_due",
            "prediction-001",
            "same_prediction_lease_active",
            "Wait for the active lease to expire or inspect stale-lease recovery.",
        ),
        blocked_case(
            "resource_limit",
            "append_evidence",
            "prediction-001",
            "operation_budget_exhausted",
            "Drain the worker and inspect workspace resource controls.",
        ),
        blocked_case(
            "source_policy_blocks_live_fetch",
            "run_tick",
            "prediction-001",
            "automatic_live_source_execution_disabled",
            "Provide approved source evidence or run an explicit opt-in connector command.",
        ),
    ]


def sidecar_boundary() -> dict[str, bool]:
    return {
        "localOnly": True,
        "networkListenerStarted": False,
        "osSchedulerInstalled": False,
        "hostedWorkerRequired": False,
        "credentialValuesStored": False,
        "rawSqlExposed": False,
        "rawFileLayoutExposed": False,
        "automaticLiveSourceExecution": False,
        "automaticMethodUpgrade": False,
    }


def build_background_worker_runtime() -> dict[str, Any]:
    commands = worker_commands()
    record = {
        "backgroundWorkerRuntimeId": "backgroundworker-001",
        "generatedAt": GENERATED_AT,
        "runtimeStatus": "bounded_local_worker_defined",
        "runtimeScope": "embedded_or_local_sidecar",
        "workerCommands": commands,
        "operationQueue": operation_queue(),
        "executionGuards": execution_guards(),
        "resourceLimits": resource_limits(),
        "oneTickReadback": one_tick_readback(),
        "blockedOperationReadbacks": blocked_operation_readbacks(),
        "sidecarBoundary": sidecar_boundary(),
        "summary": {
            "commandCount": len(commands),
            "boundedLoopDefined": True,
            "oneTickEquivalenceDefined": True,
            "workerReadbacksPresent": True,
            "allEffectfulWorkPreflighted": True,
            "idempotencyAndLeasesRequired": True,
            "resourceLimitsPresent": True,
            "nonNetworkedByDefault": True,
        },
        "warnings": [
            "This is a checked local worker readback, not a long-running daemon in normal checks.",
            "Worker execution must use the internal API and lifecycle operation receipts, never raw SQL or raw files.",
            "The default worker is local and non-networked; live source execution remains explicit and opt-in.",
            "Hosted workers, queue transports, and OS scheduler installation remain future adapter work.",
        ],
    }
    record["boundedLoopExecution"] = run_bounded_worker_loop(record, max_ticks=1, dry_run=True)
    record["approvedCommitExecution"] = run_approved_worker_commit(record)
    record["controlStateExecution"] = run_worker_control_state(record)
    record["durableSidecarExecution"] = build_durable_sidecar_execution(record)
    validate_background_worker_runtime(record)
    return record


def validate_background_worker_runtime(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise BackgroundWorkerRuntimeError(f"background worker runtime schema validation failed: {errors[0]}")
    commands = {item["commandName"]: item for item in record["workerCommands"]}
    expected_commands = {"health", "pause", "resume", "drain", "shutdown", "run_one_tick", "run_bounded_loop"}
    if set(commands) != expected_commands:
        raise BackgroundWorkerRuntimeError("worker command coverage drifted")
    if not commands["run_one_tick"]["bounded"] or not commands["run_bounded_loop"]["requiresMaxTicks"]:
        raise BackgroundWorkerRuntimeError("worker tick commands must be bounded")
    boundary = record["sidecarBoundary"]
    if not boundary["localOnly"]:
        raise BackgroundWorkerRuntimeError("worker must remain local-only by default")
    for key, value in boundary.items():
        if key != "localOnly" and value:
            raise BackgroundWorkerRuntimeError(f"sidecar boundary must keep {key} false")
    guards = record["executionGuards"]
    if not all(guards.values()):
        raise BackgroundWorkerRuntimeError("worker execution guards must all be enabled")
    tick = record["oneTickReadback"]
    if tick["internalApiOperation"] != "run_tick" or not tick["foregroundEquivalent"]:
        raise BackgroundWorkerRuntimeError("worker one-tick readback must bind foreground run_tick semantics")
    if tick["writesState"]:
        raise BackgroundWorkerRuntimeError("checked worker tick must not write state")
    loop = record["boundedLoopExecution"]
    if loop["loopStatus"] != "completed_dry_run" or not loop["dryRun"]:
        raise BackgroundWorkerRuntimeError("bounded worker loop must complete one dry-run tick")
    if loop["ticksExecuted"] != 1 or loop["operationsAttempted"] != 1:
        raise BackgroundWorkerRuntimeError("bounded worker loop checks must execute one bounded operation")
    if loop["tickExecutions"][0]["internalApiOperation"] != "run_tick":
        raise BackgroundWorkerRuntimeError("bounded worker loop must call foreground-equivalent run_tick")
    if loop["writesState"] or loop["sourceFetchAttempted"]:
        raise BackgroundWorkerRuntimeError("bounded worker loop must not write state or fetch sources in checks")
    commit = record["approvedCommitExecution"]
    if commit["lifecycleOperationName"] != "forecast.create" or commit["lifecycleResult"]["operationStatus"] != "committed":
        raise BackgroundWorkerRuntimeError("approved worker commit path must commit forecast.create")
    if commit["normalChecksWritePersistentState"] or not commit["executionBoundary"]["ephemeralSqliteOnly"]:
        raise BackgroundWorkerRuntimeError("approved worker commit checks must stay in ephemeral SQLite")
    if not commit["leaseLifecycle"]["leaseReserved"] or not commit["leaseLifecycle"]["leaseReleased"]:
        raise BackgroundWorkerRuntimeError("approved worker commit path must reserve and release its lease")
    control = record["controlStateExecution"]
    if control["controlStateStatus"] != "lifecycle_backed_control_state_checked":
        raise BackgroundWorkerRuntimeError("worker control state must be lifecycle-backed")
    if control["summary"]["controlWriteCount"] != 4 or control["summary"]["lifecycleReceiptsWritten"] != 4:
        raise BackgroundWorkerRuntimeError("worker control state must cover four lifecycle writes")
    if control["healthReadback"]["workerState"] != "stopped":
        raise BackgroundWorkerRuntimeError("worker control health readback must report final stopped state")
    sidecar = record["durableSidecarExecution"]
    if sidecar["sidecarStatus"] != "checked_local_sidecar_semantics":
        raise BackgroundWorkerRuntimeError("durable sidecar semantics must be checked")
    if sidecar["normalChecksStartProcess"] or sidecar["executionBoundary"]["hiddenDaemonStarted"]:
        raise BackgroundWorkerRuntimeError("durable sidecar checks must not start hidden processes")
    if record["resourceLimits"]["sourceFetchPolicy"] != "disabled_by_default":
        raise BackgroundWorkerRuntimeError("worker source fetch policy must be disabled by default")


def write_background_worker_runtime(record: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        record,
        label="background worker runtime",
        regen="python3 scripts/generate_background_worker_runtime.py --write",
    )


def check_background_worker_runtime(record: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        record,
        label="background worker runtime",
        regen="python3 scripts/generate_background_worker_runtime.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument(
        "--view",
        choices=["full", "health", "tick", "loop", "commit", "control", "sidecar", "blocked", "boundary"],
        default="full",
        help="print a compact worker readback view",
    )
    args = parser.parse_args()
    try:
        record = build_background_worker_runtime()
        if args.write:
            write_background_worker_runtime(record)
        elif args.check:
            check_background_worker_runtime(record)
        elif args.view == "health":
            sys.stdout.write(render_json({"runtimeStatus": record["runtimeStatus"], "summary": record["summary"]}))
        elif args.view == "tick":
            sys.stdout.write(render_json(record["oneTickReadback"]))
        elif args.view == "loop":
            sys.stdout.write(render_json(record["boundedLoopExecution"]))
        elif args.view == "commit":
            sys.stdout.write(render_json(record["approvedCommitExecution"]))
        elif args.view == "control":
            sys.stdout.write(render_json(record["controlStateExecution"]))
        elif args.view == "sidecar":
            sys.stdout.write(render_json(record["durableSidecarExecution"]))
        elif args.view == "blocked":
            sys.stdout.write(render_json(record["blockedOperationReadbacks"]))
        elif args.view == "boundary":
            sys.stdout.write(render_json(record["sidecarBoundary"]))
        else:
            sys.stdout.write(render_json(record))
    except BackgroundWorkerRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
