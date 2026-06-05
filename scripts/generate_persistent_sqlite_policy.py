#!/usr/bin/env python3
"""Generate a checked persistent SQLite path policy readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "persistent-sqlite-policy"
OUTPUT_PATH = GENERATED / "ope-persistent-sqlite-policy.generated.json"
SCHEMA = SPEC / "persistent-sqlite-policy.schema.json"
GENERATED_AT = "2026-06-04T23:40:00Z"

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

BLOCKED_SPECS = [
    ("missing_approval", "blocked_missing_approval", "ask_for_persistent_path_approval", "approval_missing"),
    ("outside_workspace", "blocked_path_not_allowlisted", "choose_workspace_state_path", "path_not_allowlisted"),
    ("symlink_escape", "blocked_symlink_escape", "replace_with_real_workspace_path", "symlink_escape"),
    (
        "existing_unmigrated_json_state",
        "blocked_needs_migration_plan",
        "run_json_state_import_dry_run",
        "unmigrated_json_state",
    ),
    (
        "schema_version_mismatch",
        "blocked_schema_version_mismatch",
        "run_schema_compatibility_check",
        "schema_version_mismatch",
    ),
    ("backup_missing", "blocked_backup_missing", "create_backup_before_migration", "backup_missing"),
    ("lock_conflict", "blocked_lock_conflict", "wait_or_recover_stale_lock", "lock_conflict"),
    ("readonly_filesystem", "blocked_readonly_filesystem", "choose_writable_state_path", "readonly_filesystem"),
]


class PersistentSqlitePolicyError(Exception):
    pass


def path_policy() -> dict[str, Any]:
    return {
        "pathPolicyStatus": "checked",
        "defaultPathTemplate": ".ope/state/{workspaceId}/ope.sqlite3",
        "allowedRelativeRoots": [".ope/state"],
        "allowedFileExtensions": [".sqlite", ".sqlite3", ".db"],
        "workspaceRootRequired": True,
        "callerApprovalRequired": True,
        "absolutePathRequiresApproval": True,
        "pathTraversalBlocked": True,
        "symlinkEscapeBlocked": True,
        "parentDirectoryCreatedOnlyWithExplicitWrite": True,
        "credentialValuesAccepted": False,
        "rawSqlPathParametersAllowed": False,
        "normalChecksUseEphemeralSqlite": True,
    }


def path_case(
    *,
    case_name: str,
    status: str,
    next_action: str,
    requested_path: str,
    approved: bool,
    ready_for_explicit_write: bool,
    reason: str = "none",
) -> dict[str, Any]:
    return {
        "caseName": case_name,
        "caseStatus": status,
        "requestedPath": requested_path,
        "callerApprovalStatus": "approved" if approved else "not_requested",
        "readyForExplicitWrite": ready_for_explicit_write,
        "requiresExplicitWriteFlag": True,
        "persistentDatabaseCreated": False,
        "normalChecksCreatePersistentDatabase": False,
        "operationReceiptsWritten": False,
        "sanitizedDiagnosticsOnly": True,
        "blockedReason": reason,
        "nextAction": next_action,
    }


def path_cases() -> list[dict[str, Any]]:
    cases = [
        path_case(
            case_name="ephemeral_default",
            status="ephemeral_runtime_ready",
            next_action="continue_ephemeral_runtime",
            requested_path=":memory:",
            approved=False,
            ready_for_explicit_write=False,
        ),
        path_case(
            case_name="approved_workspace_path",
            status="persistent_path_ready_for_explicit_write",
            next_action="run_with_explicit_write_local",
            requested_path=".ope/state/workspace-001/ope.sqlite3",
            approved=True,
            ready_for_explicit_write=True,
        ),
    ]
    requested_paths = {
        "missing_approval": ".ope/state/workspace-001/ope.sqlite3",
        "outside_workspace": "../outside/ope.sqlite3",
        "symlink_escape": ".ope/state/workspace-symlink/ope.sqlite3",
        "existing_unmigrated_json_state": ".ope/state/workspace-with-json/ope.sqlite3",
        "schema_version_mismatch": ".ope/state/workspace-old-schema/ope.sqlite3",
        "backup_missing": ".ope/state/workspace-needs-backup/ope.sqlite3",
        "lock_conflict": ".ope/state/workspace-locked/ope.sqlite3",
        "readonly_filesystem": ".ope/state/workspace-readonly/ope.sqlite3",
    }
    for case_name, status, next_action, reason in BLOCKED_SPECS:
        cases.append(
            path_case(
                case_name=case_name,
                status=status,
                next_action=next_action,
                requested_path=requested_paths[case_name],
                approved=case_name != "missing_approval",
                ready_for_explicit_write=False,
                reason=reason,
            )
        )
    return cases


def migration_policy() -> dict[str, Any]:
    return {
        "migrationPolicyStatus": "explicit_receipt_backed_import_only",
        "automaticMigrationAllowed": False,
        "migrationOperationName": "state.import_json",
        "dryRunRequiredBeforeWrite": True,
        "backupRequiredBeforeWrite": True,
        "migrationReceiptRequired": True,
        "contentHashesPreserved": True,
        "sourceRecordHashesPreserved": True,
        "forecastProbabilitiesPreserved": True,
        "sourceProvenancePreserved": True,
        "historicalForecastRewriteAllowed": False,
        "normalChecksRunMigration": False,
        "ignoredLiveStateReadByDefault": False,
    }


def backup_and_lock_policy() -> dict[str, Any]:
    return {
        "backupPolicyStatus": "checked_before_effectful_persistence",
        "backupBeforeMigrationRequired": True,
        "backupPathTemplate": ".ope/state/{workspaceId}/backups/{timestamp}-ope.sqlite3",
        "backupContentHashRequired": True,
        "sqliteBusyTimeoutMs": 5000,
        "operationLeaseAlignmentRequired": True,
        "staleLockRecoveryRequiresReceipt": True,
        "walModeAllowedAfterExplicitWrite": True,
        "normalChecksEnableWalMode": False,
    }


def operation_guard(
    operation_name: str,
    lease_required: bool,
    receipt_required: bool = True,
) -> dict[str, Any]:
    return {
        "operationName": operation_name,
        "preflightRequired": True,
        "idempotencyKeyRequired": True,
        "leaseRequired": lease_required,
        "operationReceiptRequired": receipt_required,
        "persistentPathPolicyChecked": True,
        "rawSqlExposedToAgents": False,
    }


def operation_guards() -> list[dict[str, Any]]:
    return [
        operation_guard("campaign.create_run", True),
        operation_guard("forecast.create", True),
        operation_guard("resolution.record", True),
        operation_guard("score.create", True),
        operation_guard("evidence.append", True),
        operation_guard("state.import_json", True),
        operation_guard("method.apply", True),
        operation_guard("method.rollback", True),
        operation_guard("record.archive", False),
        operation_guard("record.redact", False),
    ]


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py persistent-sqlite-policy",
            "operationName": "persistent_sqlite_policy",
            "mutatesState": False,
            "createsPersistentDatabase": False,
        },
        {
            "readbackSurface": "lifecycle_operation_store",
            "command": "python3 scripts/ope.py lifecycle-operation-store",
            "operationName": "lifecycle_operation_store",
            "mutatesState": False,
            "createsPersistentDatabase": False,
        },
        {
            "readbackSurface": "runtime_security",
            "command": "python3 scripts/ope.py runtime-security",
            "operationName": "runtime_security",
            "mutatesState": False,
            "createsPersistentDatabase": False,
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "persistentDatabaseCreatedByDefault": False,
        "normalChecksCreatePersistentDatabase": False,
        "normalChecksReadIgnoredLiveState": False,
        "hostedRuntimeImplemented": False,
        "postgresConnectionOpened": False,
        "rawSqlExposedToAgents": False,
        "credentialValuesStored": False,
        "destructiveMigrationAllowed": False,
        "physicalDeleteAllowed": False,
        "qualityClaimsUpgraded": False,
    }


def build_persistent_sqlite_policy() -> dict[str, Any]:
    cases = path_cases()
    return {
        "persistentSqlitePolicyId": "persistentsqlitepolicy-001",
        "generatedAt": GENERATED_AT,
        "policyStatus": "persistent_sqlite_path_policy_checked",
        "decisionStatus": "explicit_opt_in_ready_not_default",
        "normalChecksUseEphemeralSqlite": True,
        "persistentSqliteDefaultEnabled": False,
        "hostedRuntimeRequired": False,
        "pathPolicy": path_policy(),
        "pathCases": cases,
        "migrationPolicy": migration_policy(),
        "backupAndLockPolicy": backup_and_lock_policy(),
        "operationGuards": operation_guards(),
        "readbacks": readbacks(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "caseCount": len(cases),
            "blockedCaseCount": len(BLOCKED_SPECS),
            "readyCaseCount": 2,
            "operationGuardCount": 10,
            "persistentSqliteDefaultEnabled": False,
            "normalChecksUseEphemeralSqlite": True,
        },
        "warnings": [
            "Persistent SQLite paths are ready only as an explicit opt-in local policy; normal checks continue using ephemeral SQLite.",
            "Approved persistent paths must live under the workspace state root, pass symlink and traversal checks, and require caller approval.",
            "Existing ignored JSON state must migrate through an explicit dry-run and receipt-backed state.import_json operation with backups and preserved hashes.",
        ],
    }


def validate_persistent_sqlite_policy(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise PersistentSqlitePolicyError("persistent SQLite policy failed schema validation")
    if [item["caseName"] for item in record["pathCases"]] != CASE_ORDER:
        raise PersistentSqlitePolicyError("persistent SQLite case order drifted")
    for key, value in record["executionBoundary"].items():
        if value is not False:
            raise PersistentSqlitePolicyError(f"execution boundary {key} should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "path":
        return record["pathPolicy"]
    if view == "cases":
        return record["pathCases"]
    if view == "ready":
        return record["pathCases"][:2]
    if view == "blocked":
        return record["pathCases"][2:]
    if view == "migration":
        return record["migrationPolicy"]
    if view == "backup-lock":
        return record["backupAndLockPolicy"]
    if view == "guards":
        return record["operationGuards"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "boundary":
        return record["executionBoundary"]
    if view == "summary":
        return record["summary"]
    raise PersistentSqlitePolicyError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated persistent SQLite policy fixture")
    parser.add_argument("--check", action="store_true", help="check generated persistent SQLite policy fixture")
    parser.add_argument("--case", choices=CASE_ORDER, help="print one checked persistent SQLite policy case")
    parser.add_argument(
        "--view",
        choices=[
            "full",
            "path",
            "cases",
            "ready",
            "blocked",
            "migration",
            "backup-lock",
            "guards",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="emit a focused persistent SQLite policy view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_persistent_sqlite_policy()
    validate_persistent_sqlite_policy(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="persistent SQLite policy",
            regen="python3 scripts/generate_persistent_sqlite_policy.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="persistent SQLite policy",
            regen="python3 scripts/generate_persistent_sqlite_policy.py --write",
        )
        return
    if args.case:
        print(render_json(next(item for item in record["pathCases"] if item["caseName"] == args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
