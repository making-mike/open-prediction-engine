#!/usr/bin/env python3
"""Check private setup adapter conformance matrix boundaries."""

from __future__ import annotations

from generate_private_setup_adapter_conformance_matrix import build_matrix


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    matrix = build_matrix()
    cases = matrix["operationCases"]
    by_phase = {}
    for case in cases:
        by_phase.setdefault(case["phase"], []).append(case)

    require(len(cases) == 31, "matrix should include 31 private setup adapter rows")
    require(len(by_phase["source_builder"]) == 6, "matrix should include five source-builder payloads and one error")
    require(len(by_phase["source_handoff"]) == 7, "matrix should include seven source-handoff rows")
    require(len(by_phase["method_gate"]) == 7, "matrix should include seven method-gate rows")
    require(len(by_phase["forecast_execution"]) == 7, "matrix should include seven forecast-execution rows")
    require(len(by_phase["forecast_readback"]) == 4, "matrix should include four normal readback rows")

    source_builder = {case["adapterCase"]: case for case in by_phase["source_builder"]}
    require(source_builder["local_draft"]["payloadStatus"] == "draft_ready", "local draft should be draft-ready")
    require(source_builder["local_draft"]["forecastArtifactsCreated"] is False, "source-builder should not forecast")
    for adapter_case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        require(source_builder[adapter_case]["payloadStatus"] == "rejected", f"{adapter_case} should be rejected")
        require(source_builder[adapter_case]["forecastArtifactsCreated"] is False, f"{adapter_case} should not forecast")
    require(source_builder["malformed_input"]["expectedStatus"] == "error", "malformed input should be error")
    require(source_builder["malformed_input"]["expectedErrorCode"] == "validation_failed", "malformed input should sanitize validation failure")
    require(source_builder["malformed_input"]["payloadShape"] == "sanitized_error", "malformed input should have no payload")

    source_handoff = {case["adapterCase"]: case for case in by_phase["source_handoff"]}
    require(
        source_handoff["confirmed_builder_draft"]["payloadStatus"] == "ready_for_method_gating",
        "confirmed handoff should be ready for method gating",
    )
    require(
        source_handoff["unconfirmed_builder_draft"]["nextAction"] == "ask_mapping_confirmation",
        "unconfirmed handoff should ask mapping confirmation",
    )
    require(
        source_handoff["insufficient_confirmed_builder_draft"]["nextAction"] == "collect_more_data",
        "insufficient handoff should collect more data",
    )
    for adapter_case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        require(
            source_handoff[adapter_case]["nextAction"] == "replace_rejected_sources",
            f"{adapter_case} handoff should replace rejected sources",
        )
        require(source_handoff[adapter_case]["forecastArtifactsCreated"] is False, f"{adapter_case} handoff should not forecast")

    method_gate = {case["adapterCase"]: case for case in by_phase["method_gate"]}
    require(
        method_gate["confirmed_builder_draft"]["payloadStatus"] == "method_selected",
        "confirmed method gate should select method",
    )
    require(
        method_gate["confirmed_builder_draft"]["nextAction"] == "await_explicit_setup_forecast_execution",
        "confirmed method gate should route to explicit forecast execution",
    )
    require(
        method_gate["unconfirmed_builder_draft"]["nextAction"] == "ask_mapping_confirmation",
        "unconfirmed method gate should ask mapping confirmation",
    )
    require(
        method_gate["insufficient_confirmed_builder_draft"]["nextAction"] == "collect_more_data",
        "insufficient method gate should collect more data",
    )
    for row in by_phase["method_gate"]:
        require(row["forecastArtifactsCreated"] is False, "method gate rows should not create forecast artifacts")

    forecast_execution = {case["adapterCase"]: case for case in by_phase["forecast_execution"]}
    confirmed = forecast_execution["confirmed_builder_draft"]
    require(confirmed["payloadStatus"] == "generated", "confirmed forecast execution should generate")
    require(confirmed["forecastArtifactsCreated"] is True, "confirmed forecast execution should create forecast artifacts")
    require(confirmed["publicReadRecordsCreated"] is True, "confirmed forecast execution should create read records")
    require(confirmed["nextAction"] == "read_forecast_card", "confirmed forecast execution should route to forecast card")
    for adapter_case, row in forecast_execution.items():
        if adapter_case == "confirmed_builder_draft":
            continue
        require(row["payloadStatus"] == "blocked", f"{adapter_case} forecast execution should be blocked")
        require(row["forecastArtifactsCreated"] is False, f"{adapter_case} forecast execution should not create artifacts")
        require(row["publicReadRecordsCreated"] is False, f"{adapter_case} forecast execution should not create read records")

    readback_operations = {case["operation"]: case for case in by_phase["forecast_readback"]}
    require(set(readback_operations) == {"forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"}, "readbacks should use normal forecast operations")
    require(readback_operations["forecast_card"]["nextAction"] == "inspect_forecast_card", "forecast-card readback action drift")
    require(readback_operations["lifecycle_bundle"]["nextAction"] == "inspect_lifecycle_bundle", "lifecycle readback action drift")
    require(readback_operations["resolution_status"]["payloadStatus"] == "resolved", "resolution readback should be resolved")
    require(readback_operations["scoring_summary"]["payloadStatus"] == "scored", "scoring readback should be scored")
    for row in by_phase["forecast_readback"]:
        require(row["forecastArtifactsCreated"] is False, "readback rows should not create forecast artifacts")
        require(row["scoringRecordsCreated"] is False, "readback rows should not create scoring records")
        require(row["qualityClaimAllowed"] is False, "readback rows should not allow quality claims")

    boundary = matrix["executionBoundary"]
    require(boundary["matrixDoesNotExecute"] is True, "matrix should not execute")
    require(boundary["usesExistingGeneratedEnvelopes"] is True, "matrix should use generated envelopes")
    for key in [
        "readsPrivateData",
        "runsCommands",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "resolvesOutcomes",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    print("checked private setup adapter conformance matrix")


if __name__ == "__main__":
    main()
