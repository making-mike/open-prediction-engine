#!/usr/bin/env python3
"""Generate a checked multi-prediction workspace registry readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-workspace-registry"
OUTPUT_PATH = GENERATED / "ope-prediction-workspace-registry.generated.json"
SCHEMA = SPEC / "prediction-workspace-registry.schema.json"
GENERATED_AT = "2026-06-03T02:20:00Z"


class PredictionWorkspaceRegistryError(Exception):
    pass


def prediction_entry(
    *,
    prediction_id: str,
    campaign_id: str,
    domain_id: str,
    source_binding_id: str,
    schedule_id: str,
    status: str,
    owner_id: str,
    owner_type: str,
    contact_ref: str,
    created_by: str,
    last_updated_by: str,
    caller_intent: str,
    operation_count: int,
    last_operation_name: str,
    last_operation_receipt_id: str,
    last_operation_status: str,
    read_model_refs: list[str],
) -> dict[str, Any]:
    return {
        "predictionId": prediction_id,
        "campaignId": campaign_id,
        "domainId": domain_id,
        "sourceBindingId": source_binding_id,
        "scheduleId": schedule_id,
        "status": status,
        "owner": {
            "ownerId": owner_id,
            "ownerType": owner_type,
            "contactRef": contact_ref,
        },
        "callerMetadata": {
            "createdBy": created_by,
            "lastUpdatedBy": last_updated_by,
            "callerIntent": caller_intent,
        },
        "lifecycleOperationSummary": {
            "operationCount": operation_count,
            "lastOperationName": last_operation_name,
            "lastOperationReceiptId": last_operation_receipt_id,
            "lastOperationStatus": last_operation_status,
        },
        "readModelRefs": read_model_refs,
        "rawFileLayoutExposed": False,
        "rawSqlExposed": False,
    }


def configuration_lifecycle_operations() -> list[dict[str, Any]]:
    shared_read_models = [
        "all_predictions",
        "active_predictions",
        "blocked_operations",
        "failed_operations",
    ]
    return [
        {
            "operationName": "prediction.config_create",
            "apiOperation": "create_prediction",
            "operationReceiptId": "operationreceipt-005",
            "idempotencyRequired": True,
            "leaseRequired": True,
            "auditHistoryPreserved": True,
            "rawConfigMutationAllowed": False,
            "physicalDeleteAllowed": False,
            "auditRecordKind": "create_record",
            "readModelsUpdated": [
                "all_predictions",
                "active_predictions",
                "due_forecasts",
                "calibration_progress",
                "track_record_progress",
            ],
        },
        {
            "operationName": "prediction.config_update",
            "apiOperation": "update_prediction",
            "operationReceiptId": "operationreceipt-006",
            "idempotencyRequired": True,
            "leaseRequired": True,
            "auditHistoryPreserved": True,
            "rawConfigMutationAllowed": False,
            "physicalDeleteAllowed": False,
            "auditRecordKind": "update_revision",
            "readModelsUpdated": [
                *shared_read_models,
                "source_health_blockers",
                "calibration_progress",
                "track_record_progress",
            ],
        },
        {
            "operationName": "prediction.config_archive",
            "apiOperation": "archive_record",
            "operationReceiptId": "operationreceipt-007",
            "idempotencyRequired": True,
            "leaseRequired": True,
            "auditHistoryPreserved": True,
            "rawConfigMutationAllowed": False,
            "physicalDeleteAllowed": False,
            "auditRecordKind": "archive_tombstone",
            "readModelsUpdated": [
                "all_predictions",
                "active_predictions",
                "due_forecasts",
                "due_resolutions",
                "blocked_operations",
                "failed_operations",
            ],
        },
        {
            "operationName": "prediction.config_redact",
            "apiOperation": "redact_record",
            "operationReceiptId": "operationreceipt-008",
            "idempotencyRequired": True,
            "leaseRequired": True,
            "auditHistoryPreserved": True,
            "rawConfigMutationAllowed": False,
            "physicalDeleteAllowed": False,
            "auditRecordKind": "redaction_receipt",
            "readModelsUpdated": [
                "all_predictions",
                "blocked_operations",
                "failed_operations",
                "source_health_blockers",
            ],
        },
    ]


def per_prediction_concurrency_controls() -> list[dict[str, Any]]:
    return [
        {
            "predictionId": "prediction-001",
            "idempotencyNamespaceId": "idempotencynamespace-001",
            "leaseId": "predictionlease-001",
            "leaseScope": "prediction_execution",
            "leaseStatus": "available",
            "heldBy": "agentalpha-001",
            "expiresAt": "2026-06-11T06:35:00Z",
            "crossPredictionConcurrencyAllowed": True,
            "samePredictionConcurrentMutationBlocked": True,
            "staleLeaseRecoveryAction": "release expired execution lease before retrying the same prediction",
        },
        {
            "predictionId": "prediction-002",
            "idempotencyNamespaceId": "idempotencynamespace-002",
            "leaseId": "predictionlease-002",
            "leaseScope": "prediction_config",
            "leaseStatus": "blocked",
            "heldBy": "agentbeta-001",
            "expiresAt": "2026-06-11T06:40:00Z",
            "crossPredictionConcurrencyAllowed": True,
            "samePredictionConcurrentMutationBlocked": True,
            "staleLeaseRecoveryAction": "ask the holder to finish source confirmation or expire the config lease",
        },
    ]


def workspace_resource_controls() -> dict[str, Any]:
    return {
        "maximumActivePredictions": 8,
        "currentActivePredictionCount": 1,
        "maximumQueuedOperations": 32,
        "currentQueuedOperationCount": 4,
        "maximumReadbackBytes": 65536,
        "currentReadbackBytes": 12288,
        "perPredictionExecutionBudgets": [
            {
                "predictionId": "prediction-001",
                "maxTicksPerRun": 1,
                "maxResolverAttempts": 2,
                "maxRuntimeSeconds": 30,
                "maxReadbackBytes": 32768,
                "budgetStatus": "within_budget",
            },
            {
                "predictionId": "prediction-002",
                "maxTicksPerRun": 1,
                "maxResolverAttempts": 1,
                "maxRuntimeSeconds": 15,
                "maxReadbackBytes": 16384,
                "budgetStatus": "blocked",
            },
        ],
        "resourceStatus": "within_limits",
    }


def isolation_checks() -> list[dict[str, Any]]:
    base = {
        "sourcePredictionId": "prediction-001",
        "targetPredictionId": "prediction-002",
        "crossPredictionWriteAllowed": False,
        "samePredictionWriteAllowed": True,
        "auditRecordRequired": True,
    }
    return [
        {
            "isolationCheckId": "isolationcheck-001",
            "checkName": "record_write_scope",
            "attemptedWriteKind": "forecast_record",
            "sanitizedDiagnosticCode": "cross_prediction_record_write_blocked",
            **base,
        },
        {
            "isolationCheckId": "isolationcheck-002",
            "checkName": "source_binding_scope",
            "attemptedWriteKind": "source_binding",
            "sanitizedDiagnosticCode": "cross_prediction_source_binding_write_blocked",
            **base,
        },
        {
            "isolationCheckId": "isolationcheck-003",
            "checkName": "method_binding_scope",
            "attemptedWriteKind": "method_binding",
            "sanitizedDiagnosticCode": "cross_prediction_method_binding_write_blocked",
            **base,
        },
        {
            "isolationCheckId": "isolationcheck-004",
            "checkName": "read_model_scope",
            "attemptedWriteKind": "read_model",
            "sanitizedDiagnosticCode": "cross_prediction_read_model_write_blocked",
            **base,
        },
    ]


def build_prediction_workspace_registry() -> dict[str, Any]:
    predictions = [
        prediction_entry(
            prediction_id="prediction-001",
            campaign_id="predictioncampaign-001",
            domain_id="domainweathertransitdelays-001",
            source_binding_id="sourcebinding-001",
            schedule_id="schedule-001",
            status="active",
            owner_id="operatorlocal-001",
            owner_type="team",
            contact_ref="local-operator-record",
            created_by="agentalpha-001",
            last_updated_by="agentalpha-001",
            caller_intent=(
                "Run the weather-transit-delay campaign with baseline method execution until "
                "calibration thresholds and approvals pass."
            ),
            operation_count=8,
            last_operation_name="start_prediction",
            last_operation_receipt_id="operationreceipt-001",
            last_operation_status="committed",
            read_model_refs=[
                "all_predictions",
                "active_predictions",
                "due_forecasts",
                "due_resolutions",
                "calibration_progress",
                "track_record_progress",
            ],
        ),
        prediction_entry(
            prediction_id="prediction-002",
            campaign_id="predictioncampaign-002",
            domain_id="domainseaportberthavailability-001",
            source_binding_id="sourcebinding-002",
            schedule_id="schedule-002",
            status="paused",
            owner_id="serviceops-001",
            owner_type="service",
            contact_ref="ops-service-record",
            created_by="agentbeta-001",
            last_updated_by="agentbeta-001",
            caller_intent=(
                "Hold a private berth-availability setup until source bindings are confirmed "
                "and leakage checks pass."
            ),
            operation_count=3,
            last_operation_name="pause_prediction",
            last_operation_receipt_id="operationreceipt-002",
            last_operation_status="paused",
            read_model_refs=[
                "all_predictions",
                "blocked_operations",
                "source_health_blockers",
                "calibration_progress",
            ],
        ),
    ]
    record = {
        "predictionWorkspaceRegistryId": "workspace-registry-001",
        "generatedAt": GENERATED_AT,
        "registryStatus": "stable_registry_defined",
        "workspaceId": "opeworkspace-001",
        "predictions": predictions,
        "readModels": {
            "allPredictions": [
                {
                    "predictionId": "prediction-001",
                    "campaignId": "predictioncampaign-001",
                    "domainId": "domainweathertransitdelays-001",
                    "status": "active",
                    "lastOperationStatus": "committed",
                },
                {
                    "predictionId": "prediction-002",
                    "campaignId": "predictioncampaign-002",
                    "domainId": "domainseaportberthavailability-001",
                    "status": "paused",
                    "lastOperationStatus": "paused",
                },
            ],
            "activePredictions": [
                {
                    "predictionId": "prediction-001",
                    "campaignId": "predictioncampaign-001",
                    "nextAction": "run_tick",
                    "nextDueAt": "2026-06-11T06:30:00Z",
                    "budgetStatus": "within_budget",
                }
            ],
            "dueForecasts": [
                {
                    "predictionId": "prediction-001",
                    "campaignId": "predictioncampaign-001",
                    "runId": "predictionrun-1301",
                    "forecastId": "forecast-1301",
                    "dueAt": "2026-06-11T06:30:00Z",
                    "dueStatus": "due_ready",
                }
            ],
            "dueResolutions": [
                {
                    "predictionId": "prediction-001",
                    "campaignId": "predictioncampaign-001",
                    "runId": "predictionrun-1301",
                    "resolutionJobId": "resolutionjob-1301",
                    "dueAt": "2026-06-11T07:15:00Z",
                    "dueStatus": "due_ready",
                }
            ],
            "blockedOperations": [
                {
                    "predictionId": "prediction-002",
                    "operationName": "resume_prediction",
                    "operationReceiptId": "operationreceipt-003",
                    "operationStatus": "blocked",
                    "reasonCode": "source_binding_unconfirmed",
                    "retryable": True,
                }
            ],
            "failedOperations": [
                {
                    "predictionId": "prediction-002",
                    "operationName": "start_prediction",
                    "operationReceiptId": "operationreceipt-004",
                    "operationStatus": "failed",
                    "reasonCode": "mapping_confidence_below_threshold",
                    "retryable": True,
                }
            ],
            "sourceHealthBlockers": [
                {
                    "predictionId": "prediction-002",
                    "sourceBindingId": "sourcebinding-002",
                    "healthStatus": "blocked_unconfirmed_mapping",
                    "reasonCode": "mapping_confirmation_required",
                    "nextAction": "confirm source mapping before resume",
                }
            ],
            "calibrationProgress": [
                {
                    "predictionId": "prediction-001",
                    "comparableCount": 1,
                    "threshold": 100,
                    "calibrationStatus": "below_threshold",
                    "claimAllowed": False,
                },
                {
                    "predictionId": "prediction-002",
                    "comparableCount": 0,
                    "threshold": 100,
                    "calibrationStatus": "blocked",
                    "claimAllowed": False,
                },
            ],
            "trackRecordProgress": [
                {
                    "predictionId": "prediction-001",
                    "scoredCount": 1,
                    "excludedCount": 6,
                    "trackRecordStatus": "below_threshold",
                    "baselineComparisonReady": True,
                },
                {
                    "predictionId": "prediction-002",
                    "scoredCount": 0,
                    "excludedCount": 0,
                    "trackRecordStatus": "blocked",
                    "baselineComparisonReady": False,
                },
            ],
        },
        "configurationLifecycleOperations": configuration_lifecycle_operations(),
        "perPredictionConcurrencyControls": per_prediction_concurrency_controls(),
        "workspaceResourceControls": workspace_resource_controls(),
        "isolationChecks": isolation_checks(),
        "summary": {
            "predictionCount": len(predictions),
            "activePredictionCount": sum(1 for item in predictions if item["status"] == "active"),
            "stablePredictionIds": True,
            "campaignIdsBound": True,
            "domainIdsBound": True,
            "sourceBindingIdsBound": True,
            "scheduleIdsBound": True,
            "ownerMetadataPresent": True,
            "lifecycleSummariesPresent": True,
            "readModelsPresent": True,
            "dueForecastReadbackPresent": True,
            "blockedAndFailedReadbacksPresent": True,
            "calibrationAndTrackRecordReadbacksPresent": True,
            "configurationLifecycleOperationsPresent": True,
            "configurationOperationsAuditBacked": True,
            "configurationDeleteReplacedByArchive": True,
            "perPredictionIdempotencyPresent": True,
            "perPredictionLeasesPresent": True,
            "crossPredictionConcurrencyAllowed": True,
            "samePredictionRaceBlocked": True,
            "resourceControlsPresent": True,
            "activePredictionLimitEnforced": True,
            "queuedOperationLimitEnforced": True,
            "readbackSizeLimitEnforced": True,
            "perPredictionExecutionBudgetsPresent": True,
            "isolationChecksPresent": True,
            "recordIsolationEnforced": True,
            "sourceBindingIsolationEnforced": True,
            "methodBindingIsolationEnforced": True,
            "readModelIsolationEnforced": True,
        },
        "executionBoundary": {
            "readbackOnly": True,
            "writesRegistryState": False,
            "rawSqlExposed": False,
            "rawFileLayoutExposed": False,
            "startsPredictions": False,
        },
        "warnings": [
            "This registry is a checked readback contract and does not start, pause, or mutate predictions.",
            "Agents should use stable prediction IDs and internal API calls instead of raw files or raw SQL.",
            "Domain and source configuration records remain separate milestone work before new domains execute.",
            "Concurrent write safety still depends on lifecycle operation receipts, idempotency keys, and leases.",
        ],
    }
    validate_prediction_workspace_registry(record)
    return record


def _require_unique(record: dict[str, Any], field_name: str) -> None:
    values = [item[field_name] for item in record["predictions"]]
    if len(values) != len(set(values)):
        raise PredictionWorkspaceRegistryError(f"duplicate {field_name} in prediction registry")


def validate_prediction_workspace_registry(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PredictionWorkspaceRegistryError(f"prediction workspace registry schema validation failed: {errors[0]}")

    for field_name in ["predictionId", "campaignId", "domainId", "sourceBindingId", "scheduleId"]:
        _require_unique(record, field_name)

    predictions = record["predictions"]
    if len(predictions) < 2:
        raise PredictionWorkspaceRegistryError("registry must include at least two predictions")
    if not any(item["status"] == "active" for item in predictions):
        raise PredictionWorkspaceRegistryError("registry must include an active prediction")
    if not any(item["status"] != "active" for item in predictions):
        raise PredictionWorkspaceRegistryError("registry must include a non-active prediction")
    if len({item["domainId"] for item in predictions}) < 2:
        raise PredictionWorkspaceRegistryError("registry must cover at least two domains")

    prediction_ids = {item["predictionId"] for item in predictions}
    for item in predictions:
        if item["rawFileLayoutExposed"] or item["rawSqlExposed"]:
            raise PredictionWorkspaceRegistryError("registry entries must not expose raw storage")
        summary = item["lifecycleOperationSummary"]
        if summary["operationCount"] < 1 or not summary["lastOperationReceiptId"]:
            raise PredictionWorkspaceRegistryError("registry entries must include lifecycle operation summaries")
        if "all_predictions" not in item["readModelRefs"]:
            raise PredictionWorkspaceRegistryError("each registry entry must be visible in all_predictions")

    read_models = record["readModels"]
    expected_read_model_keys = {
        "allPredictions",
        "activePredictions",
        "dueForecasts",
        "dueResolutions",
        "blockedOperations",
        "failedOperations",
        "sourceHealthBlockers",
        "calibrationProgress",
        "trackRecordProgress",
    }
    if set(read_models) != expected_read_model_keys:
        raise PredictionWorkspaceRegistryError("workspace read model coverage drifted")
    if {item["predictionId"] for item in read_models["allPredictions"]} != prediction_ids:
        raise PredictionWorkspaceRegistryError("allPredictions read model must cover every registry prediction")
    if {item["predictionId"] for item in read_models["activePredictions"]} != {
        item["predictionId"] for item in predictions if item["status"] == "active"
    }:
        raise PredictionWorkspaceRegistryError("activePredictions read model must match active registry entries")
    for key in [
        "dueForecasts",
        "dueResolutions",
        "blockedOperations",
        "failedOperations",
        "sourceHealthBlockers",
        "calibrationProgress",
        "trackRecordProgress",
    ]:
        for row in read_models[key]:
            if row["predictionId"] not in prediction_ids:
                raise PredictionWorkspaceRegistryError(f"{key} contains an unknown prediction id")
    if not read_models["dueForecasts"] or not read_models["dueResolutions"]:
        raise PredictionWorkspaceRegistryError("registry must expose due forecast and resolution readbacks")
    if not read_models["blockedOperations"] or not read_models["failedOperations"]:
        raise PredictionWorkspaceRegistryError("registry must expose blocked and failed operation readbacks")
    if not read_models["sourceHealthBlockers"]:
        raise PredictionWorkspaceRegistryError("registry must expose source-health blockers")
    if {item["predictionId"] for item in read_models["calibrationProgress"]} != prediction_ids:
        raise PredictionWorkspaceRegistryError("calibration progress read model must cover every prediction")
    if {item["predictionId"] for item in read_models["trackRecordProgress"]} != prediction_ids:
        raise PredictionWorkspaceRegistryError("track-record progress read model must cover every prediction")

    config_operations = record["configurationLifecycleOperations"]
    expected_config_operations = {
        "prediction.config_create",
        "prediction.config_update",
        "prediction.config_archive",
        "prediction.config_redact",
    }
    operations_by_name = {item["operationName"]: item for item in config_operations}
    if set(operations_by_name) != expected_config_operations:
        raise PredictionWorkspaceRegistryError("configuration lifecycle operation coverage drifted")
    for item in config_operations:
        if not item["idempotencyRequired"] or not item["leaseRequired"]:
            raise PredictionWorkspaceRegistryError("configuration operations must require idempotency and leases")
        if not item["auditHistoryPreserved"]:
            raise PredictionWorkspaceRegistryError("configuration operations must preserve audit history")
        if item["rawConfigMutationAllowed"] or item["physicalDeleteAllowed"]:
            raise PredictionWorkspaceRegistryError("configuration operations must not mutate raw config or delete")
        if "all_predictions" not in item["readModelsUpdated"]:
            raise PredictionWorkspaceRegistryError("configuration operations must update all_predictions")
    if operations_by_name["prediction.config_archive"]["auditRecordKind"] != "archive_tombstone":
        raise PredictionWorkspaceRegistryError("archive operation must create an archive tombstone")
    if operations_by_name["prediction.config_redact"]["auditRecordKind"] != "redaction_receipt":
        raise PredictionWorkspaceRegistryError("redact operation must create a redaction receipt")

    concurrency_controls = record["perPredictionConcurrencyControls"]
    if {item["predictionId"] for item in concurrency_controls} != prediction_ids:
        raise PredictionWorkspaceRegistryError("per-prediction concurrency controls must cover every prediction")
    if len({item["idempotencyNamespaceId"] for item in concurrency_controls}) != len(concurrency_controls):
        raise PredictionWorkspaceRegistryError("idempotency namespaces must be unique per prediction")
    if len({item["leaseId"] for item in concurrency_controls}) != len(concurrency_controls):
        raise PredictionWorkspaceRegistryError("lease ids must be unique per prediction")
    for item in concurrency_controls:
        if not item["crossPredictionConcurrencyAllowed"]:
            raise PredictionWorkspaceRegistryError("different predictions should be concurrently manageable")
        if not item["samePredictionConcurrentMutationBlocked"]:
            raise PredictionWorkspaceRegistryError("same prediction concurrent mutations must be blocked")
        if len(item["staleLeaseRecoveryAction"]) < 8:
            raise PredictionWorkspaceRegistryError("lease recovery actions must be agent-readable")

    resource_controls = record["workspaceResourceControls"]
    if resource_controls["currentActivePredictionCount"] != summary_active_count(record):
        raise PredictionWorkspaceRegistryError("resource active prediction count must match registry summary")
    if resource_controls["currentActivePredictionCount"] > resource_controls["maximumActivePredictions"]:
        raise PredictionWorkspaceRegistryError("active prediction resource limit exceeded")
    if resource_controls["currentQueuedOperationCount"] > resource_controls["maximumQueuedOperations"]:
        raise PredictionWorkspaceRegistryError("queued operation resource limit exceeded")
    if resource_controls["currentReadbackBytes"] > resource_controls["maximumReadbackBytes"]:
        raise PredictionWorkspaceRegistryError("readback byte resource limit exceeded")
    budget_rows = resource_controls["perPredictionExecutionBudgets"]
    if {item["predictionId"] for item in budget_rows} != prediction_ids:
        raise PredictionWorkspaceRegistryError("per-prediction execution budgets must cover every prediction")
    for item in budget_rows:
        if item["maxTicksPerRun"] < 1 or item["maxResolverAttempts"] < 1:
            raise PredictionWorkspaceRegistryError("execution budgets must allow at least one bounded attempt")
        if item["maxReadbackBytes"] > resource_controls["maximumReadbackBytes"]:
            raise PredictionWorkspaceRegistryError("prediction readback budget cannot exceed workspace budget")

    isolation_rows = record["isolationChecks"]
    expected_isolation_checks = {
        "record_write_scope": "forecast_record",
        "source_binding_scope": "source_binding",
        "method_binding_scope": "method_binding",
        "read_model_scope": "read_model",
    }
    isolation_by_name = {item["checkName"]: item for item in isolation_rows}
    if set(isolation_by_name) != set(expected_isolation_checks):
        raise PredictionWorkspaceRegistryError("isolation check coverage drifted")
    if len({item["isolationCheckId"] for item in isolation_rows}) != len(isolation_rows):
        raise PredictionWorkspaceRegistryError("isolation check ids must be unique")
    for check_name, write_kind in expected_isolation_checks.items():
        item = isolation_by_name[check_name]
        if item["attemptedWriteKind"] != write_kind:
            raise PredictionWorkspaceRegistryError(f"{check_name} attempted write kind drifted")
        if item["sourcePredictionId"] == item["targetPredictionId"]:
            raise PredictionWorkspaceRegistryError("isolation checks must model cross-prediction attempts")
        if item["sourcePredictionId"] not in prediction_ids or item["targetPredictionId"] not in prediction_ids:
            raise PredictionWorkspaceRegistryError("isolation checks must bind known predictions")
        if item["crossPredictionWriteAllowed"]:
            raise PredictionWorkspaceRegistryError("cross-prediction writes must be blocked")
        if not item["samePredictionWriteAllowed"]:
            raise PredictionWorkspaceRegistryError("same-prediction writes should remain allowed through leases")
        if not item["auditRecordRequired"]:
            raise PredictionWorkspaceRegistryError("blocked cross-prediction writes should require audit records")

    summary = record["summary"]
    if summary["predictionCount"] != len(predictions):
        raise PredictionWorkspaceRegistryError("registry prediction count summary drifted")
    if summary["activePredictionCount"] != sum(1 for item in predictions if item["status"] == "active"):
        raise PredictionWorkspaceRegistryError("registry active prediction count summary drifted")
    for key in [
        "stablePredictionIds",
        "campaignIdsBound",
        "domainIdsBound",
        "sourceBindingIdsBound",
        "scheduleIdsBound",
        "ownerMetadataPresent",
        "lifecycleSummariesPresent",
        "readModelsPresent",
        "dueForecastReadbackPresent",
        "blockedAndFailedReadbacksPresent",
        "calibrationAndTrackRecordReadbacksPresent",
        "configurationLifecycleOperationsPresent",
        "configurationOperationsAuditBacked",
        "configurationDeleteReplacedByArchive",
        "perPredictionIdempotencyPresent",
        "perPredictionLeasesPresent",
        "crossPredictionConcurrencyAllowed",
        "samePredictionRaceBlocked",
        "resourceControlsPresent",
        "activePredictionLimitEnforced",
        "queuedOperationLimitEnforced",
        "readbackSizeLimitEnforced",
        "perPredictionExecutionBudgetsPresent",
        "isolationChecksPresent",
        "recordIsolationEnforced",
        "sourceBindingIsolationEnforced",
        "methodBindingIsolationEnforced",
        "readModelIsolationEnforced",
    ]:
        if summary[key] is not True:
            raise PredictionWorkspaceRegistryError(f"registry summary must keep {key} true")

    boundary = record["executionBoundary"]
    if boundary["readbackOnly"] is not True:
        raise PredictionWorkspaceRegistryError("registry readback should stay read-only for this milestone step")
    for key in ["writesRegistryState", "rawSqlExposed", "rawFileLayoutExposed", "startsPredictions"]:
        if boundary[key] is not False:
            raise PredictionWorkspaceRegistryError(f"registry execution boundary must keep {key} false")


def summary_active_count(record: dict[str, Any]) -> int:
    return sum(1 for item in record["predictions"] if item["status"] == "active")


def write_prediction_workspace_registry(record: dict[str, Any]) -> None:
    write_generated(
        OUTPUT_PATH,
        record,
        label="prediction workspace registry",
        regen="python3 scripts/generate_prediction_workspace_registry.py --write",
    )


def check_prediction_workspace_registry(record: dict[str, Any]) -> None:
    check_generated(
        OUTPUT_PATH,
        record,
        label="prediction workspace registry",
        regen="python3 scripts/generate_prediction_workspace_registry.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prediction-id", help="print one registry entry")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        record = build_prediction_workspace_registry()
        if args.prediction_id:
            matches = [item for item in record["predictions"] if item["predictionId"] == args.prediction_id]
            if not matches:
                raise PredictionWorkspaceRegistryError(f"unknown prediction id: {args.prediction_id}")
            sys.stdout.write(render_json(matches[0]))
        elif args.write:
            write_prediction_workspace_registry(record)
        elif args.check:
            check_prediction_workspace_registry(record)
        else:
            sys.stdout.write(render_json(record))
    except PredictionWorkspaceRegistryError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
