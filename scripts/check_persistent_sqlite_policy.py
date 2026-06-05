#!/usr/bin/env python3
"""Check persistent SQLite path policy and readiness boundaries."""

from __future__ import annotations

try:
    from generate_persistent_sqlite_policy import build_persistent_sqlite_policy
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("persistent SQLite policy generator is missing") from exc


CASE_ORDER = [
    "ephemeral_default",
    "approved_workspace_path",
    "missing_approval",
    "outside_workspace",
    "symlink_escape",
    "existing_unmigrated_json_state",
    "schema_version_mismatch",
    "backup_missing",
    "lock_conflict",
    "readonly_filesystem",
]

BLOCKED_EXPECTED = {
    "missing_approval": ("blocked_missing_approval", "ask_for_persistent_path_approval"),
    "outside_workspace": ("blocked_path_not_allowlisted", "choose_workspace_state_path"),
    "symlink_escape": ("blocked_symlink_escape", "replace_with_real_workspace_path"),
    "existing_unmigrated_json_state": ("blocked_needs_migration_plan", "run_json_state_import_dry_run"),
    "schema_version_mismatch": ("blocked_schema_version_mismatch", "run_schema_compatibility_check"),
    "backup_missing": ("blocked_backup_missing", "create_backup_before_migration"),
    "lock_conflict": ("blocked_lock_conflict", "wait_or_recover_stale_lock"),
    "readonly_filesystem": ("blocked_readonly_filesystem", "choose_writable_state_path"),
}

REQUIRED_BOUNDARY_FALSE = [
    "persistentDatabaseCreatedByDefault",
    "normalChecksCreatePersistentDatabase",
    "normalChecksReadIgnoredLiveState",
    "hostedRuntimeImplemented",
    "postgresConnectionOpened",
    "rawSqlExposedToAgents",
    "credentialValuesStored",
    "destructiveMigrationAllowed",
    "physicalDeleteAllowed",
    "qualityClaimsUpgraded",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    policy = build_persistent_sqlite_policy()

    require(policy["policyStatus"] == "persistent_sqlite_path_policy_checked", "policy status drifted")
    require(policy["decisionStatus"] == "explicit_opt_in_ready_not_default", "decision status drifted")
    require(policy["normalChecksUseEphemeralSqlite"] is True, "normal checks should keep ephemeral SQLite")
    require(policy["persistentSqliteDefaultEnabled"] is False, "persistent SQLite must not become default")
    require(policy["hostedRuntimeRequired"] is False, "persistent SQLite policy must not require hosted runtime")

    path_policy = policy["pathPolicy"]
    require(path_policy["defaultPathTemplate"] == ".ope/state/{workspaceId}/ope.sqlite3", "default path template drifted")
    require(path_policy["workspaceRootRequired"] is True, "workspace root should be required")
    require(path_policy["callerApprovalRequired"] is True, "caller approval should be required")
    require(path_policy["absolutePathRequiresApproval"] is True, "absolute paths should require approval")
    require(path_policy["pathTraversalBlocked"] is True, "path traversal should be blocked")
    require(path_policy["symlinkEscapeBlocked"] is True, "symlink escape should be blocked")
    require(path_policy["credentialValuesAccepted"] is False, "path policy must not accept credentials")
    require(".ope/state" in path_policy["allowedRelativeRoots"], "state root should be allowlisted")

    cases = {item["caseName"]: item for item in policy["pathCases"]}
    require(list(cases) == CASE_ORDER, "persistent SQLite case order drifted")
    require(cases["ephemeral_default"]["caseStatus"] == "ephemeral_runtime_ready", "ephemeral default status drifted")
    require(cases["ephemeral_default"]["persistentDatabaseCreated"] is False, "ephemeral default must not create persistent DB")
    require(cases["approved_workspace_path"]["caseStatus"] == "persistent_path_ready_for_explicit_write", "approved path status drifted")
    require(cases["approved_workspace_path"]["requiresExplicitWriteFlag"] is True, "approved path should require explicit write")
    require(cases["approved_workspace_path"]["normalChecksCreatePersistentDatabase"] is False, "normal checks must not create approved DB")
    for case_name, (status, next_action) in BLOCKED_EXPECTED.items():
        case = cases[case_name]
        require(case["caseStatus"] == status, f"{case_name} status drifted")
        require(case["nextAction"] == next_action, f"{case_name} next action drifted")
        require(case["persistentDatabaseCreated"] is False, f"{case_name} must not create persistent DB")
        require(case["operationReceiptsWritten"] is False, f"{case_name} must not write receipts")
        require(case["sanitizedDiagnosticsOnly"] is True, f"{case_name} should keep diagnostics sanitized")

    migration = policy["migrationPolicy"]
    require(migration["automaticMigrationAllowed"] is False, "automatic migration must stay blocked")
    require(migration["migrationOperationName"] == "state.import_json", "migration operation drifted")
    require(migration["dryRunRequiredBeforeWrite"] is True, "migration dry-run should be required")
    require(migration["backupRequiredBeforeWrite"] is True, "backup should be required before migration")
    require(migration["contentHashesPreserved"] is True, "migration should preserve content hashes")
    require(migration["historicalForecastRewriteAllowed"] is False, "migration must not rewrite forecast history")

    locking = policy["backupAndLockPolicy"]
    require(locking["backupBeforeMigrationRequired"] is True, "backup-before-migration should be required")
    require(locking["sqliteBusyTimeoutMs"] == 5000, "SQLite busy timeout drifted")
    require(locking["operationLeaseAlignmentRequired"] is True, "operation lease alignment should be required")
    require(locking["staleLockRecoveryRequiresReceipt"] is True, "stale lock recovery should require receipt")

    boundary = policy["executionBoundary"]
    for key in REQUIRED_BOUNDARY_FALSE:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    readbacks = {item["readbackSurface"]: item for item in policy["readbacks"]}
    require(set(readbacks) == {"cli", "lifecycle_operation_store", "runtime_security"}, "readback coverage drifted")
    require(readbacks["cli"]["command"] == "python3 scripts/ope.py persistent-sqlite-policy", "CLI readback drifted")
    for readback in readbacks.values():
        require(readback["mutatesState"] is False, "readbacks must not mutate state")
        require(readback["createsPersistentDatabase"] is False, "readbacks must not create persistent databases")

    summary = policy["summary"]
    require(summary["caseCount"] == len(CASE_ORDER), "case count drifted")
    require(summary["blockedCaseCount"] == len(BLOCKED_EXPECTED), "blocked case count drifted")
    require(summary["readyCaseCount"] == 2, "ready case count drifted")
    require(summary["persistentSqliteDefaultEnabled"] is False, "summary default flag drifted")
    require(summary["normalChecksUseEphemeralSqlite"] is True, "summary normal-check SQLite mode drifted")

    print("checked persistent SQLite policy")


if __name__ == "__main__":
    main()
