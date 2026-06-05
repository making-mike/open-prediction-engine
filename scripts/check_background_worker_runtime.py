#!/usr/bin/env python3
"""Check background worker runtime invariants."""

from __future__ import annotations

try:
    from generate_background_worker_runtime import build_background_worker_runtime
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until the generator exists
    raise AssertionError("background worker runtime generator is missing") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runtime = build_background_worker_runtime()

    require(runtime["runtimeStatus"] == "bounded_local_worker_defined", "worker runtime status drifted")
    require(runtime["runtimeScope"] == "embedded_or_local_sidecar", "worker runtime scope drifted")

    commands = {item["commandName"]: item for item in runtime["workerCommands"]}
    require(
        set(commands) == {"health", "pause", "resume", "drain", "shutdown", "run_one_tick", "run_bounded_loop"},
        "worker command coverage drifted",
    )
    require(commands["run_one_tick"]["bounded"] is True, "one-tick command should be bounded")
    require(commands["run_bounded_loop"]["requiresMaxTicks"] is True, "bounded loop should require max ticks")
    for name in ["health", "pause", "resume", "drain", "shutdown"]:
        require(commands[name]["exposesRawStorage"] is False, f"{name} must not expose raw storage")
        require(commands[name]["startsNetworkListener"] is False, f"{name} must not start a network listener")

    queue = runtime["operationQueue"]
    require(queue["queueSource"] == "prediction_workspace_read_models", "worker queue source drifted")
    require("due_forecasts" in queue["polledReadModels"], "worker should poll due forecasts")
    require("due_resolution_jobs" in queue["polledReadModels"], "worker should poll due resolutions")
    require("recovery_actions" in queue["polledReadModels"], "worker should poll recovery actions")
    require(queue["rawSqlExposed"] is False, "worker queue must not expose raw SQL")
    require(queue["rawFileLayoutExposed"] is False, "worker queue must not expose raw file layout")

    guards = runtime["executionGuards"]
    for key in [
        "operationPreflightRequired",
        "idempotencyKeyRequired",
        "leaseRequired",
        "cancellationFlagSupported",
        "retryBackoffRequired",
        "responseSizeLimitRequired",
        "sourceFetchPolicyRequired",
    ]:
        require(guards[key] is True, f"worker guard {key} should be required")

    limits = runtime["resourceLimits"]
    require(limits["maxTicksPerLoop"] == 1, "default bounded loop should run one tick in checks")
    require(limits["maxOperationsPerTick"] <= 4, "worker tick should cap operations")
    require(limits["maxWallClockSecondsPerTick"] <= 5, "worker tick should cap wall-clock time")
    require(limits["maxReadbackBytes"] <= 65536, "worker readback should stay compact")
    require(limits["sourceFetchPolicy"] == "disabled_by_default", "worker must not fetch sources by default")

    tick = runtime["oneTickReadback"]
    require(tick["tickStatus"] in {"would_run", "blocked"}, "one-tick status drifted")
    require(tick["foregroundEquivalent"] is True, "one-tick readback should match foreground run_tick semantics")
    require(tick["internalApiOperation"] == "run_tick", "one tick should bind internal API run_tick")
    require(tick["writesState"] is False, "checked one-tick readback should not write state")
    require(tick["nextOperation"]["operationName"], "one tick should report next operation")
    require(tick["nextOperation"]["idempotencyKey"], "one tick should report idempotency key")
    require(tick["nextOperation"]["leaseId"], "one tick should report lease id")

    loop = runtime["boundedLoopExecution"]
    require(loop["loopStatus"] == "completed_dry_run", "bounded loop should complete in dry-run checks")
    require(loop["dryRun"] is True, "bounded loop should run in dry-run mode for normal checks")
    require(loop["writesState"] is False, "bounded loop check must not write state")
    require(loop["maxTicksRequested"] == 1, "bounded loop check should request one tick")
    require(loop["ticksExecuted"] == 1, "bounded loop check should execute one bounded tick")
    require(loop["operationsAttempted"] == 1, "bounded loop check should attempt one operation")
    require(loop["terminationReason"] == "max_ticks_reached", "bounded loop should stop at max tick limit")
    require(loop["sourceFetchAttempted"] is False, "bounded loop must not fetch sources by default")

    poll = loop["queuePoll"]
    for read_model in ["due_forecasts", "due_resolution_jobs", "append_readiness", "failed_operations", "recovery_actions"]:
        require(read_model in poll["readModelsPolled"], f"bounded loop should poll {read_model}")
    for operation_name in ["run_tick", "resolve_due", "append_evidence", "recover_stale_lease", "maintenance_readback"]:
        require(operation_name in poll["candidateOperationNames"], f"bounded loop should consider {operation_name}")
    require(poll["selectedOperationName"] == "run_tick", "bounded loop should select foreground-equivalent run_tick")
    require(poll["rawSqlExposed"] is False, "bounded loop poll must not expose raw SQL")
    require(poll["rawFileLayoutExposed"] is False, "bounded loop poll must not expose raw file layout")

    execution = loop["tickExecutions"][0]
    require(execution["foregroundEquivalent"] is True, "bounded loop tick should preserve foreground equivalence")
    require(execution["internalApiOperation"] == "run_tick", "bounded loop tick should call run_tick")
    require(execution["preflightStatus"] == "pass", "bounded loop tick should pass preflight")
    require(execution["idempotencyKey"] == tick["nextOperation"]["idempotencyKey"], "bounded loop should reuse one-tick idempotency")
    require(execution["leaseId"] == tick["nextOperation"]["leaseId"], "bounded loop should reuse one-tick lease")
    api_call = execution["internalApiCall"]
    require(api_call["operationName"] == "run_tick", "bounded loop should call internal API run_tick")
    require(api_call["dryRun"] is True, "bounded loop internal API call should be dry-run")
    require(api_call["operationReceiptId"], "bounded loop internal API call should expose receipt placeholder")
    require(api_call["executionBoundary"]["writesState"] is False, "bounded loop internal API call must not write state")
    require(api_call["executionBoundary"]["surpriseNetworkCalls"] is False, "bounded loop internal API call must not fetch network data")

    cancellation = loop["cancellation"]
    require(cancellation["supported"] is True, "bounded loop should support cancellation")
    require(cancellation["checkedBeforeTick"] is True, "bounded loop should check cancellation before ticks")
    require(cancellation["checkedBetweenOperations"] is True, "bounded loop should check cancellation between operations")
    require(cancellation["stopsBeforeMutation"] is True, "bounded loop cancellation should stop before mutation")

    backoff = loop["retryBackoff"]
    require(backoff["policy"] == "bounded_exponential", "bounded loop should declare bounded retry backoff")
    require(backoff["maxAttemptsPerOperation"] <= 2, "bounded loop should cap retry attempts")
    require(backoff["sameIdempotencyKeyOnRetry"] is True, "bounded loop retries should preserve idempotency key")

    resources = loop["resourceUsage"]
    require(resources["withinLimits"] is True, "bounded loop should remain within resource limits")
    require(resources["operationsAttempted"] <= limits["maxOperationsPerTick"], "bounded loop should honor operation cap")
    require(resources["readbackBytes"] <= limits["maxReadbackBytes"], "bounded loop should honor readback cap")

    commit = runtime["approvedCommitExecution"]
    require(commit["approvalRequired"] is True, "worker commit path should require explicit approval")
    require(commit["approvalStatus"] == "fixture_approved", "checked worker commit path should use fixture approval")
    require(commit["stateWritingMode"] == "ephemeral_sqlite_check", "normal worker commit checks should use ephemeral SQLite")
    require(commit["normalChecksWritePersistentState"] is False, "worker commit checks must not write persistent state")
    require(commit["workerOperationName"] == "run_tick", "worker commit path should originate from run_tick")
    require(commit["internalApiOperation"] == "run_tick", "worker commit path should preserve internal API run_tick")
    require(commit["lifecycleOperationName"] == "forecast.create", "worker commit path should commit forecast.create")
    require(commit["idempotencyKey"], "worker commit path should expose idempotency key")
    require(commit["sameIdempotencyKeyOnRetry"] is True, "worker commit retries should preserve idempotency key")

    lease_lifecycle = commit["leaseLifecycle"]
    require(lease_lifecycle["leaseReserved"] is True, "worker commit path should reserve a lease")
    require(lease_lifecycle["leaseReleased"] is True, "worker commit path should release the lease")
    require(lease_lifecycle["leaseCountAfterRelease"] == 0, "worker commit path should release ephemeral leases")

    commit_result = commit["lifecycleResult"]
    require(commit_result["operationStatus"] == "committed", "worker commit path should commit through lifecycle store")
    require(commit_result["preflightStatus"] == "preflight_pass", "worker commit path should pass preflight")
    require(commit_result["leaseStatus"] == "available", "worker commit path should have an available lease")
    require(commit_result["idempotencyStatus"] == "new_key_available", "worker commit path should reserve a new idempotency key")
    require(commit_result["sqliteWrites"]["operationReceiptsWritten"] == 1, "worker commit path should write one receipt")
    require(commit_result["sqliteWrites"]["idempotencyKeysWritten"] == 1, "worker commit path should write one idempotency key")
    require(commit_result["sqliteWrites"]["leasesWritten"] == 1, "worker commit path should reserve one lease")
    require(commit_result["sqliteWrites"]["immutableRecordsInserted"] >= 3, "worker commit path should insert forecast records")
    require(commit_result["sqliteWrites"]["readModelRowsWritten"] >= 2, "worker commit path should update read models")
    require(commit_result["sqliteWrites"]["rawCrudExposed"] is False, "worker commit path must not expose raw CRUD")
    require(commit_result["sqliteWrites"]["physicalDeletes"] == 0, "worker commit path must not physically delete records")
    require("next_due_forecast" in commit_result["readModelEffects"], "worker commit should update due forecast read model")
    require("unresolved_forecasts" in commit_result["readModelEffects"], "worker commit should update unresolved forecast read model")

    commit_boundary = commit["executionBoundary"]
    require(commit_boundary["persistentStateWritten"] is False, "worker commit check must not write persistent state")
    require(commit_boundary["rawSqlExposed"] is False, "worker commit check must not expose raw SQL")
    require(commit_boundary["networkAccessed"] is False, "worker commit check must not access the network")

    control = runtime["controlStateExecution"]
    require(
        control["controlStateStatus"] == "lifecycle_backed_control_state_checked",
        "worker control state status drifted",
    )
    require(control["persistentStateSemantics"] is True, "worker control state should define persistent semantics")
    require(control["stateWritingMode"] == "ephemeral_sqlite_check", "normal control checks should use ephemeral SQLite")
    require(control["normalChecksWritePersistentState"] is False, "control checks must not write persistent state")
    require(control["controlReadModelName"] == "worker_control_state", "worker control read model drifted")

    control_commands = {item["commandName"]: item for item in control["controlCommands"]}
    require(set(control_commands) == {"health", "pause", "resume", "drain", "shutdown"}, "control command coverage drifted")
    require(control_commands["health"]["commandKind"] == "read", "health should be a read command")
    require(control_commands["health"]["writesState"] is False, "health must not write state")
    require(control_commands["health"]["readsControlState"] is True, "health should read worker control state")
    for command_name in ["pause", "resume", "drain", "shutdown"]:
        command = control_commands[command_name]
        require(command["commandKind"] == "write", f"{command_name} should be a write command")
        require(command["lifecycleOperationName"] == "state.import_json", f"{command_name} should use a lifecycle operation")
        require(command["writesState"] is True, f"{command_name} should write control state")
        require(command["rawControlMutationAllowed"] is False, f"{command_name} must not allow raw control mutation")
        require(command["operationReceiptId"], f"{command_name} should expose operation receipt")
        require(command["idempotencyKey"], f"{command_name} should expose idempotency key")
        require(command["leaseReserved"] is True, f"{command_name} should reserve a lease")
        require(command["leaseReleased"] is True, f"{command_name} should release its lease")
        require(command["readModelUpdated"] is True, f"{command_name} should update worker control read model")

    control_writes = control["controlWrites"]
    require(len(control_writes) == 4, "worker control should include four lifecycle writes")
    for item in control_writes:
        require(item["operationStatus"] == "committed", "control write should commit through lifecycle store")
        require(item["preflightStatus"] == "preflight_pass", "control write should pass preflight")
        require(item["sqliteWrites"]["operationReceiptsWritten"] == 1, "control write should write one receipt")
        require(item["sqliteWrites"]["idempotencyKeysWritten"] == 1, "control write should write one idempotency key")
        require(item["sqliteWrites"]["leasesWritten"] == 1, "control write should reserve one lease")
        require(item["sqliteWrites"]["readModelRowsWritten"] >= 1, "control write should update read models")
        require(item["sqliteWrites"]["rawCrudExposed"] is False, "control write must not expose raw CRUD")

    health = control["healthReadback"]
    require(health["workerId"] == "backgroundworker-001", "health readback worker drifted")
    require(health["readsControlState"] is True, "health readback should read control state")
    require(health["lastControlCommand"] == "shutdown", "health readback should show final shutdown command")
    require(health["workerState"] == "stopped", "health readback should show stopped state after shutdown")
    require(health["acceptsNewOperations"] is False, "stopped worker should not accept new operations")

    control_summary = control["summary"]
    require(control_summary["controlWriteCount"] == 4, "control write count drifted")
    require(control_summary["lifecycleReceiptsWritten"] == 4, "control receipt count drifted")
    require(control_summary["idempotencyKeysWritten"] == 4, "control idempotency count drifted")
    require(control_summary["leasesReserved"] == 4, "control lease reserve count drifted")
    require(control_summary["leasesReleased"] == 4, "control lease release count drifted")
    require(control_summary["rawControlMutationAllowed"] is False, "raw control mutation should stay blocked")

    control_boundary = control["executionBoundary"]
    require(control_boundary["persistentStateWritten"] is False, "control checks must not write persistent state")
    require(control_boundary["ephemeralSqliteOnly"] is True, "control checks should stay ephemeral")
    require(control_boundary["rawSqlExposed"] is False, "control checks must not expose raw SQL")
    require(control_boundary["networkAccessed"] is False, "control checks must not access network")

    sidecar_execution = runtime["durableSidecarExecution"]
    require(
        sidecar_execution["sidecarStatus"] == "checked_local_sidecar_semantics",
        "durable sidecar status drifted",
    )
    require(sidecar_execution["controlStateReadModel"] == "worker_control_state", "sidecar should use worker control state")
    require(sidecar_execution["defaultLaunchMode"] == "embedded_in_process", "default sidecar launch mode drifted")
    require(sidecar_execution["normalChecksStartProcess"] is False, "normal checks must not start a sidecar process")
    require(sidecar_execution["bounded"] is True, "sidecar execution should be bounded")
    require(sidecar_execution["maxTicksPerActivation"] == 1, "sidecar activation should be one tick in checks")
    require(sidecar_execution["hostNonInterference"]["hostCanContinueWhileWorkerIdle"] is True, "host should continue while worker is idle")
    require(sidecar_execution["hostNonInterference"]["hostCanInspectHealthWithoutBlocking"] is True, "host should inspect health without blocking")
    require(sidecar_execution["hostNonInterference"]["workerDoesNotOwnHostEventLoop"] is True, "worker must not own host event loop")

    launch_modes = {item["modeName"]: item for item in sidecar_execution["launchModes"]}
    require(set(launch_modes) == {"embedded_in_process", "local_sidecar_process"}, "sidecar launch mode coverage drifted")
    for mode in launch_modes.values():
        require(mode["localOnly"] is True, "sidecar launch modes should stay local")
        require(mode["networkListenerStarted"] is False, "sidecar launch modes must not start network listeners")
        require(mode["osSchedulerInstalled"] is False, "sidecar launch modes must not install OS schedulers")
        require(mode["hiddenDaemon"] is False, "sidecar launch modes must not be hidden daemons")

    activation = sidecar_execution["activationReadback"]
    require(activation["activationStatus"] == "ready_for_bounded_activation", "sidecar activation status drifted")
    require(activation["readsControlStateBeforeTick"] is True, "sidecar should read control state before tick")
    require(activation["runsBoundedLoop"] is True, "sidecar should run bounded loop")
    require(activation["usesApprovedCommitPath"] is True, "sidecar should use approved commit path")
    require(activation["stopsOnControlState"] is True, "sidecar should stop on control state")
    require(activation["heartbeatReadback"]["heartbeatStatus"] == "healthy_idle", "sidecar heartbeat drifted")
    require(activation["shutdownReadback"]["shutdownStatus"] == "clean_shutdown_readback", "sidecar shutdown drifted")

    sequence = sidecar_execution["executionSequence"]
    require([item["stepName"] for item in sequence] == ["start", "heartbeat", "run_tick", "commit", "drain", "shutdown"], "sidecar sequence drifted")
    for item in sequence:
        require(item["bounded"] is True, f"sidecar step {item['stepName']} should be bounded")
        require(item["rawStateMutationAllowed"] is False, f"sidecar step {item['stepName']} must not allow raw mutation")

    sidecar_execution_boundary = sidecar_execution["executionBoundary"]
    for key in [
        "networkListenerStarted",
        "osSchedulerInstalled",
        "hostedWorkerRequired",
        "hiddenDaemonStarted",
        "rawSqlExposed",
        "rawFileLayoutExposed",
        "automaticLiveSourceExecution",
        "automaticMethodUpgrade",
    ]:
        require(sidecar_execution_boundary[key] is False, f"sidecar execution boundary should keep {key} false")

    blocked = {item["caseId"]: item for item in runtime["blockedOperationReadbacks"]}
    require(
        set(blocked) == {
            "paused_prediction",
            "lease_conflict",
            "resource_limit",
            "source_policy_blocks_live_fetch",
        },
        "blocked operation readback coverage drifted",
    )
    for item in blocked.values():
        require(item["blocked"] is True, "blocked cases should be marked blocked")
        require(item["safeNextAction"], "blocked cases should expose safe next action")
        require(item["sanitizedDiagnosticCode"], "blocked cases should expose sanitized diagnostics")

    boundary = runtime["sidecarBoundary"]
    for key in [
        "localOnly",
        "networkListenerStarted",
        "osSchedulerInstalled",
        "hostedWorkerRequired",
        "credentialValuesStored",
        "rawSqlExposed",
        "rawFileLayoutExposed",
        "automaticLiveSourceExecution",
        "automaticMethodUpgrade",
    ]:
        expected = True if key == "localOnly" else False
        require(boundary[key] is expected, f"sidecar boundary {key} drifted")

    summary = runtime["summary"]
    require(summary["commandCount"] == 7, "worker command count drifted")
    require(summary["boundedLoopDefined"] is True, "bounded loop should be defined")
    require(summary["oneTickEquivalenceDefined"] is True, "one-tick equivalence should be defined")
    require(summary["workerReadbacksPresent"] is True, "worker readbacks should be present")
    require(summary["nonNetworkedByDefault"] is True, "worker should be non-networked by default")
    print("checked background worker runtime")


if __name__ == "__main__":
    main()
