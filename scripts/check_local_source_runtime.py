#!/usr/bin/env python3
"""Check the narrow approved local-source runtime invariants."""

from __future__ import annotations

from generate_local_source_runtime import CASE_ORDER, build_runtime


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runtime = build_runtime()
    cases = {item["case"]: item for item in runtime["runtimeCases"]}
    summary = runtime["summary"]
    boundary = runtime["executionBoundary"]
    readback = runtime["forecastCardReadback"]

    require([item["case"] for item in runtime["runtimeCases"]] == CASE_ORDER, "runtime case order drifted")
    require(runtime["runtimeMode"] == "approved_local_folder_runtime", "runtime mode drifted")
    require(runtime["runtimePolicy"]["approvalRequired"] is True, "runtime must require caller approval")
    require(runtime["runtimePolicy"]["allowNetworkAccess"] is False, "runtime must not allow network access")
    require(runtime["runtimePolicy"]["credentialStorageImplemented"] is False, "runtime must not store credentials")
    require(runtime["runtimePolicy"]["rawRetention"] == "metadata_only", "runtime must keep metadata-only retention")

    accepted = cases["approved_local_folder"]
    require(accepted["runtimeStatus"] == "forecast_card_ready", "accepted local folder should be forecast-card ready")
    require(accepted["nextAction"] == "read_forecast_card", "accepted local folder next action drifted")
    require(accepted["bindings"]["forecastId"] == "forecast-1102", "accepted local folder forecast binding drifted")
    require(accepted["bindings"]["forecastCardId"] == "forecastcard-forecast-1102", "accepted card binding drifted")
    for key in [
        "sourceBuilderInspected",
        "sourceIntakeValidated",
        "methodGateValidated",
        "explicitForecastExecutionValidated",
    ]:
        require(accepted["controls"][key] is True, f"accepted case should validate {key}")
    require(accepted["controls"]["runtimeCreatedForecastArtifacts"] is False, "runtime must not create forecast artifacts directly")

    blocked_expectations = {
        "missing_approval": ("blocked_missing_approval", "confirm_approval", "caller_approval_missing"),
        "credentials_detected": ("blocked_credentials", "remove_credentials", "source_contains_secrets"),
        "unsafe_path": ("blocked_unsafe_path", "choose_allowlisted_path", "path_not_allowlisted"),
        "oversized_response": ("blocked_oversized", "reduce_file_size", "file_too_large"),
        "schema_mismatch": ("blocked_schema_mismatch", "replace_with_supported_schema", "unsupported_format"),
        "leakage_indicator": ("blocked_leakage", "remove_leakage_source", "post_outcome_leakage_indicator"),
    }
    for case, (status, next_action, reason) in blocked_expectations.items():
        row = cases[case]
        require(row["runtimeStatus"] == status, f"{case} status drifted")
        require(row["nextAction"] == next_action, f"{case} next action drifted")
        require(reason in row["blockedReasons"], f"{case} missing reason {reason}")
        require(row["bindings"]["forecastId"] is None, f"{case} must not bind a forecast")
        require(row["controls"]["explicitForecastExecutionValidated"] is False, f"{case} must not reach forecast execution")

    require(cases["missing_approval"]["controls"]["sourceBuilderInspected"] is False, "missing approval must not inspect files")
    require(cases["unsafe_path"]["allowlistStatus"] == "failed", "unsafe path should fail allow-listing")
    require(cases["unsafe_path"]["controls"]["pathAllowlistPassed"] is False, "unsafe path control should fail")

    require(summary["caseCount"] == 7, "runtime should expose seven cases")
    require(summary["forecastCardReadyCount"] == 1, "runtime should expose one accepted forecast card")
    require(summary["blockedCount"] == 6, "runtime should expose six blocked examples")
    require(summary["qualityClaimAllowed"] is False, "runtime must not allow quality claims")
    require(summary["productionConnectorClaimAllowed"] is False, "runtime must not allow production connector claims")

    require(readback["forecastId"] == "forecast-1102", "forecast readback binding drifted")
    require(readback["claimStatus"] == "not_enough_resolved_source_handoff_outcomes", "readback claim status drifted")
    require(readback["sourceRuntimeCaseId"] == accepted["caseId"], "readback should point to accepted runtime case")

    for key, value in boundary.items():
        if key in {
            "runtimeReadsAllowlistedLocalFiles",
            "runtimeRequiresCallerApproval",
            "normalChecksDeterministicOffline",
            "explicitForecastExecutionRequired",
        }:
            require(value is True, f"boundary {key} should remain true")
        else:
            require(value is False, f"boundary {key} should remain false")

    print("checked local source runtime")


if __name__ == "__main__":
    main()
