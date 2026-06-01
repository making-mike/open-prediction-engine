#!/usr/bin/env python3
"""Check Helsinki traffic pilot readiness invariants."""

from __future__ import annotations

from generate_helsinki_traffic_pilot_readiness import build_helsinki_traffic_pilot_readiness


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_helsinki_traffic_pilot_readiness()
    bindings = record["bindings"]
    readiness = record["readinessSummary"]
    summary = record["summary"]
    boundary = record["executionBoundary"]

    require(record["readinessStatus"] == "checked_ready_for_operator_launch", "readiness status drifted")
    require(record["domain"] == "weather-transit-delays", "readiness domain drifted")
    require(bindings["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")

    require(readiness["targetRunCount"] == 100, "target run count drifted")
    require(readiness["miniSmokeRunCount"] == 3, "mini smoke run count drifted")
    require(readiness["plannedRunCount"] == 100, "planned run count drifted")
    require(readiness["duplicateConflictCount"] == 0, "duplicate conflict count drifted")
    require(readiness["bestAvailableMethodId"] == "transitmethod-100", "best available method drifted")
    require(readiness["explicitWriteRequired"] is True, "pilot launch should require explicit write")
    require(readiness["manualLivePrerequisitesRequired"] is True, "manual prerequisites should be required")
    require(readiness["normalChecksMutateState"] is False, "normal checks must not mutate state")
    require(readiness["qualityClaimAllowed"] is False, "quality claim must stay blocked")

    check_keys = {item["checkKey"]: item for item in record["readinessChecks"]}
    require(
        set(check_keys)
        == {
            "runbook_ready",
            "mini_smoke_ready",
            "full_materialization_unique",
            "baseline_method_default",
            "forecast_before_close_policy",
            "operator_source_confirmation",
        },
        "readiness check coverage drifted",
    )
    for key in [
        "runbook_ready",
        "mini_smoke_ready",
        "full_materialization_unique",
        "baseline_method_default",
        "forecast_before_close_policy",
    ]:
        require(check_keys[key]["checkStatus"] == "pass", f"{key} should pass")
        require(check_keys[key]["blocksLaunch"] is False, f"{key} should not block launch")
    require(
        check_keys["operator_source_confirmation"]["checkStatus"] == "manual_required",
        "operator source confirmation should remain manual",
    )
    require(
        check_keys["operator_source_confirmation"]["blocksLaunch"] is False,
        "manual source confirmation should not make checked prerequisites fail",
    )

    prereq_keys = {item["prerequisiteKey"] for item in record["manualPrerequisites"]}
    require(
        prereq_keys
        == {
            "terminal_supervision",
            "clock_sync",
            "source_availability",
            "outcome_path",
            "workspace_capacity",
        },
        "manual prerequisite coverage drifted",
    )
    launch_keys = {item["commandKey"]: item for item in record["launchCommands"]}
    require(
        set(launch_keys)
        == {
            "readiness",
            "mini_smoke",
            "full_plan",
            "launch_first_write",
            "operator_status",
        },
        "launch command coverage drifted",
    )
    require(launch_keys["launch_first_write"]["mutatesState"] is True, "launch command should be marked effectful")
    require(launch_keys["mini_smoke"]["mutatesState"] is False, "mini smoke should be non-mutating")

    blocked_keys = {item["actionKey"] for item in record["blockedActions"]}
    require(
        blocked_keys
        == {
            "normal_check_launch",
            "forecast_after_close",
            "method_switch_without_gate",
            "ledger_append_without_resolution",
        },
        "blocked action coverage drifted",
    )

    require(summary["pilotReadinessImplemented"] is True, "readiness should be implemented")
    require(summary["checkedPrerequisitesPassed"] is True, "checked prerequisites should pass")
    require(summary["manualPrerequisitesRequired"] is True, "manual prerequisites should be visible")
    require(summary["launchCommandReady"] is True, "launch command should be ready")
    require(summary["miniSmokeFirst"] is True, "mini smoke should come first")
    require(summary["qualityClaimAllowed"] is False, "summary quality claim must stay blocked")

    require(boundary["readOnlyReadback"] is True, "readiness boundary should be read-only")
    for key, value in boundary.items():
        if key == "readOnlyReadback":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked Helsinki traffic pilot readiness")


if __name__ == "__main__":
    main()
