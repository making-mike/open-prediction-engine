#!/usr/bin/env python3
"""Generate a checked lifecycle operation lease policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_lifecycle_operation_store import build_lifecycle_operation_store
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "lifecycle-lease-policy"
OUTPUT_PATH = GENERATED / "ope-lifecycle-lease-policy.generated.json"
SCHEMA = SPEC / "lifecycle-lease-policy.schema.json"
GENERATED_AT = "2026-06-04T23:55:00Z"

OPERATION_ORDER = [
    "campaign.create_run",
    "forecast.create",
    "forecast.recalculate",
    "question.cancel",
    "question.annul",
    "resolution.record",
    "score.create",
    "evidence.append",
    "pre_calibration.bind",
    "method.apply",
    "method.rollback",
    "state.import_json",
    "record.archive",
    "record.redact",
]

STRICT_LEASE_OPERATIONS = {
    "campaign.create_run",
    "forecast.create",
    "resolution.record",
    "score.create",
    "evidence.append",
    "pre_calibration.bind",
    "method.apply",
    "method.rollback",
    "state.import_json",
}

POLICY_REASONS = {
    "campaign.create_run": "prevents_duplicate_due_run_selection_across_agents",
    "forecast.create": "prevents_duplicate_forecast_artifact_creation",
    "forecast.recalculate": "append_history_entries_are_idempotent_by_source_hash",
    "question.cancel": "terminal_state_append_is_guarded_by_preflight_and_idempotency",
    "question.annul": "annulment_append_is_guarded_by_preflight_and_idempotency",
    "resolution.record": "prevents_double_resolution_for_same_forecast",
    "score.create": "prevents_double_scoring_for_same_resolution",
    "evidence.append": "prevents_duplicate_ledger_append_and_threshold_race",
    "pre_calibration.bind": "prevents_conflicting_pre_calibration_binding",
    "method.apply": "prevents_conflicting_method_binding",
    "method.rollback": "prevents_conflicting_method_rollback",
    "state.import_json": "prevents_concurrent_state_import_and_hash_mismatch",
    "record.archive": "archive_tombstone_replay_is_idempotent",
    "record.redact": "redaction_receipt_replay_is_idempotent",
}


class LifecycleLeasePolicyError(Exception):
    pass


def lease_key_template(operation_name: str) -> str:
    if operation_name == "campaign.create_run":
        return "campaign.create_run:{campaignId}:{runId}"
    if operation_name == "forecast.create":
        return "forecast.create:{forecastId}"
    if operation_name == "resolution.record":
        return "resolution.record:{forecastId}"
    if operation_name == "score.create":
        return "score.create:{forecastId}:{resolutionId}"
    if operation_name == "evidence.append":
        return "evidence.append:{campaignId}:{ledgerRowId}"
    if operation_name == "pre_calibration.bind":
        return "pre_calibration.bind:{campaignId}"
    if operation_name == "method.apply":
        return "method.apply:{campaignId}:{methodBindingId}"
    if operation_name == "method.rollback":
        return "method.rollback:{campaignId}:{rollbackId}"
    if operation_name == "state.import_json":
        return "state.import_json:{workspaceId}:{sourceStateHash}"
    return "none"


def operation_policy(operation: dict[str, Any]) -> dict[str, Any]:
    operation_name = operation["operationName"]
    strict_lease = operation_name in STRICT_LEASE_OPERATIONS
    return {
        "operationName": operation_name,
        "operationClass": operation["operationClass"],
        "lifecyclePhase": operation["lifecyclePhase"],
        "guardMode": "strict_lease" if strict_lease else "idempotency_only",
        "policyReason": POLICY_REASONS[operation_name],
        "preflightRequired": True,
        "idempotencyKeyRequired": True,
        "leaseRequired": strict_lease,
        "operationReceiptRequired": True,
        "normalChecksAcquireLease": False,
        "leaseKeyTemplate": lease_key_template(operation_name),
        "blockedConflictStatus": "blocked_lease_conflict"
        if strict_lease
        else "return_existing_receipt_or_block_mismatch",
        "staleRecoveryAction": "inspect_failed_operations_or_recover_stale_lease"
        if strict_lease
        else "not_applicable",
        "allowedWriteMode": operation["allowedWriteMode"],
        "deleteReplacement": operation["deleteReplacement"],
        "rawCrudExposed": False,
        "qualityClaimAllowed": False,
    }


def operation_policies(store: dict[str, Any]) -> list[dict[str, Any]]:
    operations = {item["operationName"]: item for item in store["operationCatalog"]}
    return [operation_policy(operations[name]) for name in OPERATION_ORDER]


def conflict_case(
    case_name: str,
    operation_name: str,
    guard_mode: str,
    case_status: str,
    expected_result: str,
    safe_next_action: str,
    *,
    lease_acquired: bool = False,
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "operationName": operation_name,
        "guardMode": guard_mode,
        "caseStatus": case_status,
        "expectedResult": expected_result,
        "safeNextAction": safe_next_action,
        "leaseAcquired": lease_acquired,
        "operationReceiptsWritten": False,
        "immutableRecordsWritten": False,
        "sanitizedDiagnosticsOnly": True,
    }


def conflict_cases() -> list[dict[str, Any]]:
    return [
        conflict_case(
            "same_due_forecast",
            "forecast.create",
            "strict_lease",
            "blocked_lease_conflict",
            "no_duplicate_forecast_artifact",
            "wait_or_inspect_active_lease",
        ),
        conflict_case(
            "duplicate_forecast_retry",
            "forecast.create",
            "strict_lease",
            "idempotent_replay",
            "return_existing_receipt",
            "reuse_existing_forecast_readback",
        ),
        conflict_case(
            "recalculate_same_evidence",
            "forecast.recalculate",
            "idempotency_only",
            "idempotent_replay",
            "no_duplicate_history_event",
            "reuse_existing_recalculation_receipt",
        ),
        conflict_case(
            "cancel_after_forecast_created",
            "question.cancel",
            "idempotency_only",
            "blocked_terminal_state_conflict",
            "no_forecast_delete",
            "read_resolution_or_archive_path",
        ),
        conflict_case(
            "resolution_record_race",
            "resolution.record",
            "strict_lease",
            "blocked_lease_conflict",
            "no_duplicate_resolution",
            "wait_or_inspect_active_lease",
        ),
        conflict_case(
            "method_apply_race",
            "method.apply",
            "strict_lease",
            "blocked_lease_conflict",
            "no_conflicting_method_binding",
            "wait_or_inspect_active_lease",
        ),
        conflict_case(
            "stale_import_lease",
            "state.import_json",
            "strict_lease",
            "stale_lease_recovery_required",
            "no_automatic_import_retry",
            "inspect_failed_operations_or_recover_stale_lease",
        ),
        conflict_case(
            "archive_repeat",
            "record.archive",
            "idempotency_only",
            "idempotent_replay",
            "return_existing_tombstone_receipt",
            "reuse_existing_archive_readback",
        ),
    ]


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py lifecycle-lease-policy",
            "mutatesState": False,
            "acquiresLeases": False,
            "notes": "Prints the checked lease/idempotency policy matrix.",
        },
        {
            "readbackSurface": "lifecycle_operation_store",
            "command": "python3 scripts/ope.py lifecycle-operation-store",
            "mutatesState": False,
            "acquiresLeases": False,
            "notes": "Source operation catalog and lease model remain authoritative.",
        },
        {
            "readbackSurface": "background_worker",
            "command": "python3 scripts/ope.py background-worker",
            "mutatesState": False,
            "acquiresLeases": False,
            "notes": "Worker readbacks report required guards without starting a sidecar.",
        },
        {
            "readbackSurface": "persistent_sqlite_policy",
            "command": "python3 scripts/ope.py persistent-sqlite-policy",
            "mutatesState": False,
            "acquiresLeases": False,
            "notes": "Persistent path readiness requires lease alignment before explicit writes.",
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "normalChecksWriteState": False,
        "leasesAcquiredByReadback": False,
        "persistentDatabaseCreated": False,
        "hostedRuntimeImplemented": False,
        "postgresConnectionOpened": False,
        "rawCrudExposed": False,
        "credentialValuesStored": False,
        "physicalDeleteAllowed": False,
        "forecastHistoryRewriteAllowed": False,
        "qualityClaimsUpgraded": False,
    }


def build_lifecycle_lease_policy() -> dict[str, Any]:
    store = build_lifecycle_operation_store()
    policies = operation_policies(store)
    strict_count = len([item for item in policies if item["guardMode"] == "strict_lease"])
    idempotency_only_count = len([item for item in policies if item["guardMode"] == "idempotency_only"])
    record = {
        "lifecycleLeasePolicyId": "lifecycleleasepolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "lifecycle_operation_lease_policy_checked",
        "decisionStatus": "strict_leases_for_race_prone_writes_idempotency_for_append_only_receipts",
        "normalChecksAcquireLeases": False,
        "allEffectfulOperationsRequireIdempotency": True,
        "sourceBinding": {
            "sourceSurface": "lifecycle_operation_store",
            "sourceCommand": "python3 scripts/ope.py lifecycle-operation-store",
            "sourceStoreStatus": store["storeStatus"],
            "sourceLeaseModelTable": store["leaseModel"]["tableName"],
            "sourceIdempotencyModelTable": store["idempotencyModel"]["tableName"],
        },
        "operationPolicies": policies,
        "conflictCases": conflict_cases(),
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "operationCount": len(policies),
            "strictLeaseCount": strict_count,
            "idempotencyOnlyCount": idempotency_only_count,
            "conflictCaseCount": len(conflict_cases()),
            "allEffectfulOperationsRequireIdempotency": True,
            "normalChecksAcquireLeases": False,
        },
        "warnings": [
            "Strict leases are reserved for operations that can race across agents and mutate active forecast, resolution, ledger, method, or migration state.",
            "Idempotency-only operations still require preflight, receipt-backed retries, and mismatch blockers; they are not raw CRUD shortcuts.",
            "The policy readback does not acquire leases, write state, create persistent databases, or upgrade quality claims.",
        ],
    }
    validate_lifecycle_lease_policy(record)
    return record


def validate_lifecycle_lease_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise LifecycleLeasePolicyError(f"lifecycle lease policy schema validation failed: {errors[0]}")
    if [item["operationName"] for item in record["operationPolicies"]] != OPERATION_ORDER:
        raise LifecycleLeasePolicyError("operation policy order drifted")
    for item in record["operationPolicies"]:
        expected_strict = item["operationName"] in STRICT_LEASE_OPERATIONS
        if item["leaseRequired"] != expected_strict:
            raise LifecycleLeasePolicyError(f"lease requirement drifted for {item['operationName']}")
        if item["normalChecksAcquireLease"] or item["rawCrudExposed"] or item["qualityClaimAllowed"]:
            raise LifecycleLeasePolicyError("operation policy readbacks must remain non-mutating and claim-safe")
    if any(record["executionBoundary"].values()):
        raise LifecycleLeasePolicyError("execution boundary flags should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "source":
        return record["sourceBinding"]
    if view == "operations":
        return record["operationPolicies"]
    if view == "strict":
        return [item for item in record["operationPolicies"] if item["guardMode"] == "strict_lease"]
    if view == "idempotency":
        return [item for item in record["operationPolicies"] if item["guardMode"] == "idempotency_only"]
    if view == "cases":
        return record["conflictCases"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise LifecycleLeasePolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated lifecycle lease policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated lifecycle lease policy fixture")
    parser.add_argument("--operation", choices=OPERATION_ORDER, help="print one lifecycle operation policy")
    parser.add_argument(
        "--view",
        choices=["full", "source", "operations", "strict", "idempotency", "cases", "readbacks", "boundary", "summary"],
        default="full",
        help="emit a focused lifecycle lease policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_lifecycle_lease_policy()
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="lifecycle lease policy",
            regen="python3 scripts/generate_lifecycle_lease_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="lifecycle lease policy",
            regen="python3 scripts/generate_lifecycle_lease_policy.py --write",
        )
        return
    if args.operation:
        print(render_json(next(item for item in record["operationPolicies"] if item["operationName"] == args.operation)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
