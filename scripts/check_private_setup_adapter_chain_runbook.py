#!/usr/bin/env python3
"""Check private setup adapter-chain runbook invariants."""

from __future__ import annotations

from generate_agent_adapter_protocol_map import build_protocol_map
from generate_private_setup_adapter_chain_runbook import build_runbook


EXPECTED_SEQUENCE = [
    "private_setup_bundle",
    "private_setup_source_builder",
    "private_setup_source_handoff",
    "private_setup_method_gate",
    "private_setup_forecast_execution",
    "forecast_card",
    "lifecycle_bundle",
    "resolution_status",
    "scoring_summary",
]

EXPECTED_BRANCHES = {
    "mapping_confirmation_required",
    "confirmed_handoff_ready",
    "insufficient_data",
    "rejected_source",
    "generated_forecast_readback",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runbook = build_runbook()
    operations = {item["operation"]: item for item in build_protocol_map()["operations"]}
    sequence = runbook["operationSequence"]
    sequence_ops = [item["operation"] for item in sequence]

    require(runbook["scope"] == "private_setup_local_file_adapter_chain", "runbook should cover local-file setup path")
    require(runbook["runtimeStatus"] == "runbook_guidance_only", "runbook should remain guidance-only")
    require(sequence_ops == EXPECTED_SEQUENCE, "adapter-chain runbook should preserve expected operation sequence")
    require(
        runbook["sourcePath"]["privateSetupRequestId"] == "privatesetuprequest-001",
        "runbook should bind the checked local-file setup request",
    )
    require(runbook["sourcePath"]["sourceKind"] == "local_file", "runbook should bind local_file source kind")
    require(runbook["sourcePath"]["allowLiveFetch"] is False, "runbook should not allow live fetch")
    require(runbook["sourcePath"]["allowCredentialUse"] is False, "runbook should not allow credential use")

    for item in sequence:
        operation = item["operation"]
        require(operation in operations, f"{operation} should exist in protocol map")
        require(item["mcpTool"] == operations[operation]["mcp"]["toolName"], f"{operation} MCP tool drift")
        require(
            item["sideEffectLevel"] == operations[operation]["sideEffectLevel"],
            f"{operation} side-effect level drift",
        )
        require(item["expectedEnvelopeStatus"] == "ok", f"{operation} should expect ok envelope status")
        require(item["createsScoringRecords"] is False, f"{operation} should not create scoring records")

    step_by_operation = {item["operation"]: item for item in sequence}
    require(
        step_by_operation["private_setup_bundle"]["expectedPayloadStatusValue"] == "ready_to_run_checked_command",
        "bundle step should start from a ready local-file request",
    )
    require(
        step_by_operation["private_setup_source_builder"]["expectedPayloadStatusValue"] == "draft_ready",
        "source-builder step should expect draft-ready output",
    )
    require(
        step_by_operation["private_setup_source_handoff"]["expectedPayloadStatusValue"] == "ready_for_method_gating",
        "source-handoff step should expect method-gate readiness",
    )
    require(
        step_by_operation["private_setup_method_gate"]["expectedPayloadStatusValue"] == "method_selected",
        "method-gate step should expect method selection",
    )
    require(
        step_by_operation["private_setup_forecast_execution"]["expectedPayloadStatusValue"] == "generated",
        "forecast-execution step should expect generated status",
    )
    require(
        step_by_operation["private_setup_forecast_execution"]["createsForecastArtifacts"] is True,
        "only confirmed forecast execution should create forecast artifacts",
    )
    for operation in EXPECTED_SEQUENCE:
        if operation != "private_setup_forecast_execution":
            require(
                step_by_operation[operation]["createsForecastArtifacts"] is False,
                f"{operation} should not create forecast artifacts",
            )

    readback_ops = [item["operation"] for item in sequence if item["phase"] == "forecast_readback"]
    require(
        readback_ops == ["forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"],
        "readback should use normal forecast read operations",
    )
    for operation in readback_ops:
        inputs = {item["name"]: item["value"] for item in step_by_operation[operation]["requiredInputs"]}
        require(inputs["forecastId"] == "forecast-1102", f"{operation} should bind forecast-1102")
        require(inputs["questionId"] == "question-1102", f"{operation} should bind question-1102")

    branches = {item["branchName"]: item for item in runbook["branchPlaybooks"]}
    require(set(branches) == EXPECTED_BRANCHES, "runbook should cover expected adapter branches")
    require(
        branches["mapping_confirmation_required"]["triggerStatus"] == "needs_mapping_confirmation",
        "mapping branch should bind needs_mapping_confirmation",
    )
    require(
        branches["mapping_confirmation_required"]["allowedNextOperation"] is None,
        "mapping branch should stop before another adapter operation",
    )
    require(
        branches["confirmed_handoff_ready"]["allowedNextOperation"] == "private_setup_method_gate",
        "confirmed handoff should route to method gate",
    )
    require(
        branches["insufficient_data"]["allowedNextOperation"] == "private_setup_source_builder",
        "insufficient data should route back to source-builder",
    )
    require(
        branches["rejected_source"]["allowedNextOperation"] == "private_setup_source_builder",
        "rejected sources should route to replacement source-builder guidance",
    )
    require(
        branches["generated_forecast_readback"]["allowedNextOperation"] == "forecast_card",
        "generated forecast should route to normal forecast-card readback",
    )
    for name, branch in branches.items():
        if name != "generated_forecast_readback":
            require(branch["forecastArtifactsAllowed"] is False, f"{name} should not allow forecast artifacts")
        require(branch["scoringAllowed"] is False, f"{name} should not directly allow scoring")

    boundary = runbook["executionBoundary"]
    require(boundary["runbookDoesNotExecute"] is True, "runbook should not execute")
    require(boundary["runsAdapterCalls"] is False, "runbook should not run adapter calls")
    require(boundary["normalChecksOffline"] is True, "normal checks should stay offline")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    guard_names = {item["name"] for item in runbook["guards"]}
    for guard in [
        "operation_binding",
        "local_file_path_only",
        "confirmation_before_method_gate",
        "blocked_cases_do_not_forecast",
        "normal_readback_operations",
        "guidance_only_boundary",
    ]:
        require(guard in guard_names, f"runbook should include {guard} guard")

    print("checked private setup adapter-chain runbook")


if __name__ == "__main__":
    main()
