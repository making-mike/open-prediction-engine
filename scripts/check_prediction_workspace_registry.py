#!/usr/bin/env python3
"""Check multi-prediction workspace registry invariants."""

from __future__ import annotations

from generate_prediction_workspace_registry import build_prediction_workspace_registry


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    registry = build_prediction_workspace_registry()
    predictions = registry["predictions"]
    by_prediction = {item["predictionId"]: item for item in predictions}

    require(registry["registryStatus"] == "stable_registry_defined", "registry status drifted")
    require(len(predictions) == 2, "registry should include two checked prediction examples")
    require(len(by_prediction) == len(predictions), "prediction IDs should be unique")
    require(
        {item["domainId"] for item in predictions}
        == {"domainweathertransitdelays-001", "domainseaportberthavailability-001"},
        "registry should cover two domain bindings",
    )
    for field_name in ["campaignId", "sourceBindingId", "scheduleId"]:
        require(
            len({item[field_name] for item in predictions}) == len(predictions),
            f"{field_name} values should be unique",
        )

    active = by_prediction["prediction-001"]
    paused = by_prediction["prediction-002"]
    require(active["status"] == "active", "weather-transit prediction should be active")
    require(paused["status"] == "paused", "private berth prediction should be paused")
    require(active["campaignId"] == "predictioncampaign-001", "active campaign binding drifted")
    require(paused["campaignId"] == "predictioncampaign-002", "paused campaign binding drifted")
    require(active["sourceBindingId"] == "sourcebinding-001", "active source binding drifted")
    require(paused["sourceBindingId"] == "sourcebinding-002", "paused source binding drifted")

    for item in predictions:
        require(item["owner"]["ownerId"], "registry entries should include owner IDs")
        require(item["callerMetadata"]["createdBy"], "registry entries should include caller metadata")
        require(item["lifecycleOperationSummary"]["operationCount"] >= 1, "entries should summarize lifecycle operations")
        require(item["lifecycleOperationSummary"]["lastOperationReceiptId"], "entries should include receipt IDs")
        require("all_predictions" in item["readModelRefs"], "entries should be visible in all_predictions")
        require(item["rawFileLayoutExposed"] is False, "registry entries must not expose raw file layout")
        require(item["rawSqlExposed"] is False, "registry entries must not expose raw SQL")

    read_models = registry["readModels"]
    require(
        set(read_models)
        == {
            "allPredictions",
            "activePredictions",
            "dueForecasts",
            "dueResolutions",
            "blockedOperations",
            "failedOperations",
            "sourceHealthBlockers",
            "calibrationProgress",
            "trackRecordProgress",
        },
        "workspace read model coverage drifted",
    )
    require(
        {item["predictionId"] for item in read_models["allPredictions"]} == set(by_prediction),
        "allPredictions should cover every registry entry",
    )
    require(
        {item["predictionId"] for item in read_models["activePredictions"]} == {"prediction-001"},
        "activePredictions should expose the active registry entry",
    )
    require(read_models["activePredictions"][0]["nextAction"] == "run_tick", "active next action drifted")
    require(read_models["dueForecasts"][0]["forecastId"] == "forecast-1301", "due forecast binding drifted")
    require(read_models["dueForecasts"][0]["dueStatus"] == "due_ready", "due forecast status drifted")
    require(
        read_models["dueResolutions"][0]["resolutionJobId"] == "resolutionjob-1301",
        "due resolution job binding drifted",
    )
    require(read_models["dueResolutions"][0]["dueStatus"] == "due_ready", "due resolution status drifted")
    require(
        read_models["blockedOperations"][0]["operationStatus"] == "blocked",
        "blocked operation readback drifted",
    )
    require(
        read_models["blockedOperations"][0]["predictionId"] == "prediction-002",
        "blocked operation should bind paused prediction",
    )
    require(read_models["failedOperations"][0]["operationStatus"] == "failed", "failed operation readback drifted")
    require(
        read_models["sourceHealthBlockers"][0]["sourceBindingId"] == "sourcebinding-002",
        "source-health blocker should bind paused prediction source",
    )
    require(
        {item["predictionId"] for item in read_models["calibrationProgress"]} == set(by_prediction),
        "calibration progress should cover every prediction",
    )
    require(
        all(item["claimAllowed"] is False for item in read_models["calibrationProgress"]),
        "calibration progress must keep claims blocked",
    )
    require(
        {item["predictionId"] for item in read_models["trackRecordProgress"]} == set(by_prediction),
        "track-record progress should cover every prediction",
    )

    config_operations = {
        item["operationName"]: item for item in registry["configurationLifecycleOperations"]
    }
    require(
        set(config_operations)
        == {
            "prediction.config_create",
            "prediction.config_update",
            "prediction.config_archive",
            "prediction.config_redact",
        },
        "configuration lifecycle operation coverage drifted",
    )
    require(
        config_operations["prediction.config_create"]["apiOperation"] == "create_prediction",
        "config create should bind internal create operation",
    )
    require(
        config_operations["prediction.config_update"]["apiOperation"] == "update_prediction",
        "config update should bind internal update operation",
    )
    require(
        config_operations["prediction.config_archive"]["apiOperation"] == "archive_record",
        "config archive should bind internal archive operation",
    )
    require(
        config_operations["prediction.config_redact"]["apiOperation"] == "redact_record",
        "config redact should bind internal redact operation",
    )
    for item in config_operations.values():
        require(item["operationReceiptId"], "configuration operations should include receipt IDs")
        require(item["idempotencyRequired"] is True, "configuration operations should require idempotency")
        require(item["leaseRequired"] is True, "configuration operations should require leases")
        require(item["auditHistoryPreserved"] is True, "configuration operations should preserve audit history")
        require(item["rawConfigMutationAllowed"] is False, "configuration operations must not mutate raw config")
        require(item["physicalDeleteAllowed"] is False, "configuration operations must not delete physically")
        require("all_predictions" in item["readModelsUpdated"], "configuration operations should update all_predictions")
    require(
        config_operations["prediction.config_archive"]["auditRecordKind"] == "archive_tombstone",
        "config archive should write a tombstone",
    )
    require(
        config_operations["prediction.config_redact"]["auditRecordKind"] == "redaction_receipt",
        "config redact should write a redaction receipt",
    )

    concurrency_controls = {
        item["predictionId"]: item for item in registry["perPredictionConcurrencyControls"]
    }
    require(set(concurrency_controls) == set(by_prediction), "concurrency controls should cover every prediction")
    require(
        len({item["idempotencyNamespaceId"] for item in concurrency_controls.values()}) == len(concurrency_controls),
        "idempotency namespaces should be unique per prediction",
    )
    require(
        len({item["leaseId"] for item in concurrency_controls.values()}) == len(concurrency_controls),
        "lease IDs should be unique per prediction",
    )
    require(
        concurrency_controls["prediction-001"]["leaseScope"] == "prediction_execution",
        "active prediction lease scope drifted",
    )
    require(
        concurrency_controls["prediction-002"]["leaseScope"] == "prediction_config",
        "paused prediction lease scope drifted",
    )
    for item in concurrency_controls.values():
        require(
            item["crossPredictionConcurrencyAllowed"] is True,
            "different predictions should allow concurrent management",
        )
        require(
            item["samePredictionConcurrentMutationBlocked"] is True,
            "same prediction concurrent mutation should be blocked",
        )
        require(item["staleLeaseRecoveryAction"], "lease controls should include recovery action guidance")

    resource_controls = registry["workspaceResourceControls"]
    require(resource_controls["maximumActivePredictions"] == 8, "maximum active prediction limit drifted")
    require(resource_controls["currentActivePredictionCount"] == 1, "current active prediction count drifted")
    require(
        resource_controls["currentActivePredictionCount"] <= resource_controls["maximumActivePredictions"],
        "active prediction count should stay within limit",
    )
    require(resource_controls["maximumQueuedOperations"] == 32, "maximum queued operation limit drifted")
    require(
        resource_controls["currentQueuedOperationCount"] <= resource_controls["maximumQueuedOperations"],
        "queued operation count should stay within limit",
    )
    require(resource_controls["maximumReadbackBytes"] == 65536, "maximum readback bytes drifted")
    require(
        resource_controls["currentReadbackBytes"] <= resource_controls["maximumReadbackBytes"],
        "readback bytes should stay within limit",
    )
    budget_rows = {
        item["predictionId"]: item for item in resource_controls["perPredictionExecutionBudgets"]
    }
    require(set(budget_rows) == set(by_prediction), "execution budgets should cover every prediction")
    require(budget_rows["prediction-001"]["budgetStatus"] == "within_budget", "active budget status drifted")
    require(budget_rows["prediction-002"]["budgetStatus"] == "blocked", "paused budget status drifted")
    for item in budget_rows.values():
        require(item["maxTicksPerRun"] >= 1, "execution budgets should allow bounded ticks")
        require(item["maxResolverAttempts"] >= 1, "execution budgets should allow bounded resolver attempts")
        require(
            item["maxReadbackBytes"] <= resource_controls["maximumReadbackBytes"],
            "prediction readback budget should not exceed workspace budget",
        )
    require(resource_controls["resourceStatus"] == "within_limits", "resource status drifted")

    isolation_checks = {item["checkName"]: item for item in registry["isolationChecks"]}
    require(
        set(isolation_checks)
        == {
            "record_write_scope",
            "source_binding_scope",
            "method_binding_scope",
            "read_model_scope",
        },
        "isolation check coverage drifted",
    )
    require(
        isolation_checks["record_write_scope"]["attemptedWriteKind"] == "forecast_record",
        "record isolation write kind drifted",
    )
    require(
        isolation_checks["source_binding_scope"]["attemptedWriteKind"] == "source_binding",
        "source-binding isolation write kind drifted",
    )
    require(
        isolation_checks["method_binding_scope"]["attemptedWriteKind"] == "method_binding",
        "method-binding isolation write kind drifted",
    )
    require(
        isolation_checks["read_model_scope"]["attemptedWriteKind"] == "read_model",
        "read-model isolation write kind drifted",
    )
    for item in isolation_checks.values():
        require(item["sourcePredictionId"] in by_prediction, "isolation source prediction should be known")
        require(item["targetPredictionId"] in by_prediction, "isolation target prediction should be known")
        require(
            item["sourcePredictionId"] != item["targetPredictionId"],
            "isolation checks should model cross-prediction attempts",
        )
        require(item["crossPredictionWriteAllowed"] is False, "cross-prediction writes should be blocked")
        require(item["samePredictionWriteAllowed"] is True, "same-prediction writes should be lease-gated")
        require(item["auditRecordRequired"] is True, "blocked cross-prediction writes should require audit")
        require(item["sanitizedDiagnosticCode"].endswith("_blocked"), "diagnostic should be sanitized and blocked")

    summary = registry["summary"]
    require(summary["predictionCount"] == 2, "registry prediction count drifted")
    require(summary["activePredictionCount"] == 1, "registry active count drifted")
    require(summary["stablePredictionIds"] is True, "registry should declare stable prediction IDs")
    require(summary["campaignIdsBound"] is True, "registry should bind campaign IDs")
    require(summary["domainIdsBound"] is True, "registry should bind domain IDs")
    require(summary["sourceBindingIdsBound"] is True, "registry should bind source IDs")
    require(summary["scheduleIdsBound"] is True, "registry should bind schedule IDs")
    require(summary["ownerMetadataPresent"] is True, "registry should include owner metadata")
    require(summary["lifecycleSummariesPresent"] is True, "registry should include lifecycle summaries")
    require(summary["readModelsPresent"] is True, "registry should include read models")
    require(summary["dueForecastReadbackPresent"] is True, "registry should include due forecast readback")
    require(summary["blockedAndFailedReadbacksPresent"] is True, "registry should include blocked and failed readbacks")
    require(
        summary["calibrationAndTrackRecordReadbacksPresent"] is True,
        "registry should include calibration and track-record readbacks",
    )
    require(
        summary["configurationLifecycleOperationsPresent"] is True,
        "registry should include configuration lifecycle operations",
    )
    require(summary["configurationOperationsAuditBacked"] is True, "configuration operations should be audit-backed")
    require(
        summary["configurationDeleteReplacedByArchive"] is True,
        "configuration delete should be replaced by archive",
    )
    require(summary["perPredictionIdempotencyPresent"] is True, "registry should include idempotency namespaces")
    require(summary["perPredictionLeasesPresent"] is True, "registry should include per-prediction leases")
    require(summary["crossPredictionConcurrencyAllowed"] is True, "registry should allow different prediction concurrency")
    require(summary["samePredictionRaceBlocked"] is True, "registry should block same-prediction races")
    require(summary["resourceControlsPresent"] is True, "registry should include resource controls")
    require(summary["activePredictionLimitEnforced"] is True, "active prediction limit should be enforced")
    require(summary["queuedOperationLimitEnforced"] is True, "queued operation limit should be enforced")
    require(summary["readbackSizeLimitEnforced"] is True, "readback size limit should be enforced")
    require(summary["perPredictionExecutionBudgetsPresent"] is True, "execution budgets should be present")
    require(summary["isolationChecksPresent"] is True, "registry should include isolation checks")
    require(summary["recordIsolationEnforced"] is True, "record isolation should be enforced")
    require(summary["sourceBindingIsolationEnforced"] is True, "source-binding isolation should be enforced")
    require(summary["methodBindingIsolationEnforced"] is True, "method-binding isolation should be enforced")
    require(summary["readModelIsolationEnforced"] is True, "read-model isolation should be enforced")

    boundary = registry["executionBoundary"]
    require(boundary["readbackOnly"] is True, "registry should be readback-only in this step")
    require(boundary["writesRegistryState"] is False, "registry should not write state")
    require(boundary["rawSqlExposed"] is False, "registry should not expose raw SQL")
    require(boundary["rawFileLayoutExposed"] is False, "registry should not expose raw file layout")
    require(boundary["startsPredictions"] is False, "registry should not start predictions")
    print("checked prediction workspace registry")


if __name__ == "__main__":
    main()
