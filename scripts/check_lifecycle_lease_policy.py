#!/usr/bin/env python3
"""Check lifecycle operation lease and idempotency policy boundaries."""

from __future__ import annotations

try:
    from generate_lifecycle_lease_policy import build_lifecycle_lease_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("lifecycle lease policy generator is missing") from exc


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

IDEMPOTENCY_ONLY_OPERATIONS = {
    "forecast.recalculate",
    "question.cancel",
    "question.annul",
    "record.archive",
    "record.redact",
}

CONFLICT_CASES = [
    "same_due_forecast",
    "duplicate_forecast_retry",
    "recalculate_same_evidence",
    "cancel_after_forecast_created",
    "resolution_record_race",
    "method_apply_race",
    "stale_import_lease",
    "archive_repeat",
]

REQUIRED_BOUNDARY_FALSE = [
    "normalChecksWriteState",
    "leasesAcquiredByReadback",
    "persistentDatabaseCreated",
    "hostedRuntimeImplemented",
    "postgresConnectionOpened",
    "rawCrudExposed",
    "credentialValuesStored",
    "physicalDeleteAllowed",
    "forecastHistoryRewriteAllowed",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_lifecycle_lease_policy()

    require(policy["policyStatus"] == "lifecycle_operation_lease_policy_checked", "policy status drifted")
    require(
        policy["decisionStatus"] == "strict_leases_for_race_prone_writes_idempotency_for_append_only_receipts",
        "decision status drifted",
    )
    require(policy["normalChecksAcquireLeases"] is False, "normal checks must not acquire leases")
    require(policy["allEffectfulOperationsRequireIdempotency"] is True, "idempotency should cover all effectful operations")

    source = policy["sourceBinding"]
    require(source["sourceSurface"] == "lifecycle_operation_store", "source surface drifted")
    require(source["sourceCommand"] == "python3 scripts/ope.py lifecycle-operation-store", "source command drifted")
    require(source["sourceStoreStatus"] == "local_sqlite_runtime_checked", "source store status drifted")

    operations = {item["operationName"]: item for item in policy["operationPolicies"]}
    require(list(operations) == OPERATION_ORDER, "operation policy order drifted")
    require(
        {name for name, item in operations.items() if item["guardMode"] == "strict_lease"} == STRICT_LEASE_OPERATIONS,
        "strict lease operation set drifted",
    )
    require(
        {name for name, item in operations.items() if item["guardMode"] == "idempotency_only"}
        == IDEMPOTENCY_ONLY_OPERATIONS,
        "idempotency-only operation set drifted",
    )

    for name, item in operations.items():
        require(item["preflightRequired"] is True, f"{name} should require preflight")
        require(item["idempotencyKeyRequired"] is True, f"{name} should require idempotency")
        require(item["operationReceiptRequired"] is True, f"{name} should require operation receipts")
        require(item["normalChecksAcquireLease"] is False, f"{name} readback must not acquire leases")
        require(item["rawCrudExposed"] is False, f"{name} must not expose raw CRUD")
        require(item["qualityClaimAllowed"] is False, f"{name} must not allow quality claims")
        if name in STRICT_LEASE_OPERATIONS:
            require(item["leaseRequired"] is True, f"{name} should require a lease")
            require(item["guardMode"] == "strict_lease", f"{name} guard mode drifted")
            require(item["blockedConflictStatus"] == "blocked_lease_conflict", f"{name} conflict status drifted")
            require(item["leaseKeyTemplate"] != "none", f"{name} should declare a lease key template")
            require(item["staleRecoveryAction"] == "inspect_failed_operations_or_recover_stale_lease", f"{name} stale recovery drifted")
        else:
            require(item["leaseRequired"] is False, f"{name} should not require a strict lease")
            require(item["guardMode"] == "idempotency_only", f"{name} guard mode drifted")
            require(item["blockedConflictStatus"] == "return_existing_receipt_or_block_mismatch", f"{name} conflict policy drifted")
            require(item["leaseKeyTemplate"] == "none", f"{name} should not declare a lease key")
            require(item["staleRecoveryAction"] == "not_applicable", f"{name} stale recovery should not apply")

    require(
        operations["forecast.recalculate"]["policyReason"] == "append_history_entries_are_idempotent_by_source_hash",
        "forecast recalculation policy reason drifted",
    )
    require(operations["record.archive"]["deleteReplacement"] == "archive_tombstone", "archive delete replacement drifted")
    require(operations["record.redact"]["deleteReplacement"] == "redaction_receipt", "redaction delete replacement drifted")

    cases = {item["caseName"]: item for item in policy["conflictCases"]}
    require(list(cases) == CONFLICT_CASES, "conflict case order drifted")
    require(cases["same_due_forecast"]["caseStatus"] == "blocked_lease_conflict", "same due forecast should block on lease")
    require(cases["duplicate_forecast_retry"]["caseStatus"] == "idempotent_replay", "duplicate forecast retry should replay")
    require(cases["recalculate_same_evidence"]["caseStatus"] == "idempotent_replay", "same evidence recalculation should replay")
    require(cases["cancel_after_forecast_created"]["caseStatus"] == "blocked_terminal_state_conflict", "late cancel should block")
    require(cases["resolution_record_race"]["caseStatus"] == "blocked_lease_conflict", "resolution race should block")
    require(cases["method_apply_race"]["caseStatus"] == "blocked_lease_conflict", "method apply race should block")
    require(cases["stale_import_lease"]["caseStatus"] == "stale_lease_recovery_required", "stale import should require recovery")
    require(cases["archive_repeat"]["caseStatus"] == "idempotent_replay", "archive repeat should replay")
    for case in cases.values():
        require(case["operationReceiptsWritten"] is False, f"{case['caseName']} must not write receipts in readback")
        require(case["immutableRecordsWritten"] is False, f"{case['caseName']} must not write records in readback")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case['caseName']} should keep diagnostics sanitized")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(
        set(readbacks) == {"cli", "lifecycle_operation_store", "background_worker", "persistent_sqlite_policy"},
        "readback coverage drifted",
    )
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py lifecycle-lease-policy", "CLI readback drifted")
    for readback in readbacks.values():
        require(readback["mutatesState"] is False, "readbacks must not mutate state")
        require(readback["acquiresLeases"] is False, "readbacks must not acquire leases")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = policy["summary"]
    require(summary["operationCount"] == len(OPERATION_ORDER), "operation count drifted")
    require(summary["strictLeaseCount"] == len(STRICT_LEASE_OPERATIONS), "strict lease count drifted")
    require(summary["idempotencyOnlyCount"] == len(IDEMPOTENCY_ONLY_OPERATIONS), "idempotency-only count drifted")
    require(summary["conflictCaseCount"] == len(CONFLICT_CASES), "conflict case count drifted")
    require(summary["allEffectfulOperationsRequireIdempotency"] is True, "summary idempotency flag drifted")
    require(summary["normalChecksAcquireLeases"] is False, "summary normal-check lease flag drifted")

    print("checked lifecycle lease policy")


if __name__ == "__main__":
    main()
