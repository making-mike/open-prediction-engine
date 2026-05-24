#!/usr/bin/env python3
"""Check private setup first-action runbook boundaries."""

from __future__ import annotations

from generate_private_setup_first_action_runbook import build_runbook
from generate_private_setup_first_actions import build_actions


EXPECTED_STATUSES = {
    "ready_to_run_checked_command",
    "confirmation_required",
    "fixture_ready",
    "runtime_not_implemented",
    "source_replacement_required",
    "rejected_unsafe_source",
    "bad_request",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    actions = {item["sourceKind"]: item for item in build_actions()}
    runbook = build_runbook()
    rows = {item["sourceKind"]: item for item in runbook["casePlaybooks"]}

    require(runbook["scope"] == "domain_agnostic", "runbook should stay domain agnostic")
    require(runbook["runtimeStatus"] == "runbook_guidance_only", "runbook should remain guidance-only")
    require(set(runbook["statusCoverage"]) == EXPECTED_STATUSES, "runbook should cover every first-action status")
    require(set(rows) == set(actions), "runbook should cover every generated first-action fixture")

    for source_kind, row in rows.items():
        action = actions[source_kind]
        require(
            row["boundPrivateSetupFirstActionId"] == action["privateSetupFirstActionId"],
            f"{source_kind} should bind first-action id",
        )
        require(
            row["boundPrivateSetupRequestId"] == action["requestBinding"]["privateSetupRequestId"],
            f"{source_kind} should bind private setup request id",
        )
        require(row["commandToRun"] == action["commandToRun"], f"{source_kind} command drifted")
        require(row["allowedEntrypoint"] == action["allowedEntrypoint"], f"{source_kind} entrypoint drifted")
        require(row["forecastExecutionAllowed"] is False, f"{source_kind} should not allow forecast execution")
        require(row["scoringAllowed"] is False, f"{source_kind} should not allow scoring")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]:
            require(blocked in row["blockedOutputs"], f"{source_kind} should block {blocked}")

    require(rows["local_file"]["nextActionLabel"] == "run_source_builder", "local files should route to source-builder")
    require(
        rows["local_file"]["expectedOutputClass"] == "source_manifest_build",
        "local files should expect source manifest build output",
    )
    require(
        rows["local_file"]["mayEnterSourceIntakeAfterRequiredAction"] is True,
        "local files may proceed toward source intake after required actions",
    )
    require(
        rows["manual_mapping"]["nextActionLabel"] == "ask_mapping_confirmation",
        "manual mapping should ask confirmation",
    )
    require(rows["manual_mapping"]["requiresCallerConfirmation"] is True, "manual mapping should require confirmation")
    require(
        rows["manual_mapping"]["expectedOutputClass"] == "source_intake_handoff",
        "manual mapping should expect source handoff output after confirmation",
    )
    require(
        rows["auto_evidence_connector"]["nextActionLabel"] == "run_fixture_evidence",
        "auto evidence should route to fixture evidence",
    )
    require(
        rows["auto_evidence_connector"]["expectedOutputClass"] == "evidence_source_set",
        "auto evidence should expect an evidence source set",
    )
    require(
        rows["auto_evidence_connector"]["mayEnterSourceIntakeAfterRequiredAction"] is False,
        "auto evidence should not enter source intake",
    )

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row = rows[source_kind]
        require(row["nextActionLabel"] == "wait_for_runtime", f"{source_kind} should wait for runtime")
        require(row["commandToRun"] == "none", f"{source_kind} should expose no command")
        require(row["expectedOutputClass"] == "none", f"{source_kind} should produce no output")
        require(
            row["mayEnterSourceIntakeAfterRequiredAction"] is False,
            f"{source_kind} should not enter source intake",
        )
    require(rows["unregistered_source"]["nextActionLabel"] == "replace_source", "unregistered source should be replaced")
    require(
        rows["unregistered_source"]["mayEnterSourceIntakeAfterRequiredAction"] is False,
        "unregistered source should not enter source intake",
    )
    require(rows["unsafe_source"]["nextActionLabel"] == "stop_unsafe_source", "unsafe source should stop")
    require(rows["unsafe_source"]["commandToRun"] == "none", "unsafe source should expose no command")
    require(
        rows["unsafe_source"]["mayEnterSourceIntakeAfterRequiredAction"] is False,
        "unsafe source should not enter source intake",
    )

    bad_rows = {item["errorCode"]: item for item in runbook["badRequestPlaybooks"]}
    require({"unknown_source_kind", "missing_approval"} <= set(bad_rows), "runbook should cover bad request classes")
    for error_code, row in bad_rows.items():
        require(row["actionStatus"] == "bad_request", f"{error_code} should be bad_request")
        require(row["commandToRun"] == "none", f"{error_code} should expose no command")
        require(row["allowedEntrypoint"] == "no_current_entrypoint", f"{error_code} should block entrypoint")
        require(row["expectedOutputClass"] == "none", f"{error_code} should produce no output")
        require(row["mayEnterSourceIntakeAfterRequiredAction"] is False, f"{error_code} should not enter intake")
        require(row["forecastExecutionAllowed"] is False, f"{error_code} should not forecast")
        require(row["scoringAllowed"] is False, f"{error_code} should not score")

    boundary = runbook["executionBoundary"]
    require(boundary["runbookDoesNotExecute"] is True, "runbook should not execute")
    require(boundary["runsSuggestedCommand"] is False, "runbook should not run suggested commands")
    require(boundary["normalChecksOffline"] is True, "normal checks should stay offline")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    guard_names = {item["name"] for item in runbook["guards"]}
    require("first_action_binding" in guard_names, "runbook should guard first-action binding")
    require("non_execution" in guard_names, "runbook should guard non-execution")
    require("blocked_sources_do_not_enter_intake" in guard_names, "runbook should guard blocked source intake")
    require("bad_request_sanitized" in guard_names, "runbook should guard bad-request handling")

    print("checked private setup first-action runbook")


if __name__ == "__main__":
    main()
