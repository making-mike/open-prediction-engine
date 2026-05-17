#!/usr/bin/env python3
"""Check private source adapter intake bridge boundaries."""

from __future__ import annotations

from generate_private_source_adapter_intake_bridge import build_bridge
from generate_private_source_adapter_outcome_matrix import build_matrix


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    matrix = build_matrix()
    bridge = build_bridge()

    require(bridge["scope"] == "domain_agnostic", "adapter bridge should be domain agnostic")
    require(bridge["runtimeStatus"] == "bridge_contract_only", "adapter bridge should remain contract-only")
    require(
        bridge["boundPrivateSourceAdapterOutcomeMatrixId"] == matrix["privateSourceAdapterOutcomeMatrixId"],
        "adapter bridge should bind outcome matrix",
    )
    require(
        bridge["boundPrivateSourceAdapterCapabilityId"] == matrix["boundPrivateSourceAdapterCapabilityId"],
        "adapter bridge should preserve capability binding",
    )
    require(
        bridge["boundPrivateSetupWorkflowId"] == matrix["boundPrivateSetupWorkflowId"],
        "adapter bridge should preserve workflow binding",
    )

    matrix_rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    bridge_rows = {item["sourceKind"]: item for item in bridge["bridgeRows"]}
    require(set(bridge_rows) == set(matrix_rows), "adapter bridge should cover every outcome row")

    for source_kind, row in bridge_rows.items():
        require(row["outcomeRowId"] == matrix_rows[source_kind]["outcomeRowId"], f"{source_kind} outcome binding drifted")
        require(row["bridgeCreatesOutputs"] is False, f"{source_kind} bridge should not create outputs")
        require(row["canCreateForecastArtifacts"] is False, f"{source_kind} bridge should not create forecasts")
        require(row["canCreateScoringRecords"] is False, f"{source_kind} bridge should not create scoring records")
        require(row["canStoreCredentials"] is False, f"{source_kind} bridge should not store credentials")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record"]:
            require(blocked in row["blockedOutputs"], f"{source_kind} should block {blocked}")

    local_file = bridge_rows["local_file"]
    require(local_file["allowedEntrypoint"] == "source_builder", "local files should route to source builder")
    require(local_file["currentCommand"] == "python3 scripts/ope.py source-builder", "local file command drifted")
    require("source_manifest_build" in local_file["allowedDownstreamOutputs"], "local files should allow build records")
    require("draft_source_manifest" in local_file["allowedDownstreamOutputs"], "local files should allow draft manifests")
    require("draft_field_mapping" in local_file["allowedDownstreamOutputs"], "local files should allow draft mappings")

    manual_mapping = bridge_rows["manual_mapping"]
    require(
        manual_mapping["allowedEntrypoint"] == "source_handoff_confirmation",
        "manual mapping should route to source-handoff confirmation",
    )
    require(manual_mapping["currentCommand"] == "none", "manual mapping should not run before confirmation")
    require(manual_mapping["retryCondition"] == "after_mapping_confirmation", "manual mapping retry condition drifted")
    require(
        manual_mapping["retryCommand"] == "python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
        "manual mapping should retry through confirmed source-handoff",
    )
    require(
        "caller_confirmed_field_mapping" in manual_mapping["requiredInputs"],
        "manual mapping should require caller confirmation",
    )

    auto_evidence = bridge_rows["auto_evidence_connector"]
    require(auto_evidence["allowedEntrypoint"] == "auto_evidence_fixture", "auto evidence should route to fixture")
    require(auto_evidence["currentCommand"] == "python3 scripts/ope.py gather-evidence", "auto evidence command drifted")
    require("evidence_source_set" in auto_evidence["allowedDownstreamOutputs"], "auto evidence should allow source-set output")
    require("source_manifest" in auto_evidence["blockedOutputs"], "auto evidence should not create source manifests")

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row = bridge_rows[source_kind]
        require(row["allowedEntrypoint"] == "no_current_entrypoint", f"{source_kind} should have no current entrypoint")
        require(row["currentCommand"] == "none", f"{source_kind} should have no current command")
        require(row["retryCommand"] == "none", f"{source_kind} should not expose retry command yet")
        require(row["allowedDownstreamOutputs"] == [], f"{source_kind} should not allow downstream outputs")
        require(
            row["bridgeStatus"] in {"runtime_not_implemented", "credential_runtime_missing"},
            f"{source_kind} should remain runtime blocked",
        )

    for source_kind in ["unregistered_source", "unsafe_source"]:
        row = bridge_rows[source_kind]
        require(row["allowedEntrypoint"] == "no_current_entrypoint", f"{source_kind} should have no entrypoint")
        require(row["allowedDownstreamOutputs"] == [], f"{source_kind} should not allow downstream outputs")
        require("source_intake_report" in row["blockedOutputs"], f"{source_kind} should block source intake")

    boundary = bridge["executionBoundary"]
    require(boundary["bridgeDoesNotExecute"] is True, "bridge should not execute")
    require(boundary["normalChecksOffline"] is True, "bridge checks should remain offline")
    require(boundary["createsSourceManifests"] is False, "bridge should not create source manifests")
    require(boundary["createsFieldMappings"] is False, "bridge should not create field mappings")
    require(boundary["createsForecastArtifacts"] is False, "bridge should not create forecasts")
    require(boundary["createsScoringRecords"] is False, "bridge should not create scores")
    require(boundary["storesCredentials"] is False, "bridge should not store credentials")
    require(boundary["privateAdapterRuntimeImplemented"] is False, "bridge should not implement private adapter runtime")
    require(boundary["onlyRoutesToCheckedEntrypoints"] is True, "bridge should only route to checked entrypoints")

    guard_names = {item["name"] for item in bridge["guards"]}
    require("outcome_matrix_binding" in guard_names, "bridge should guard matrix binding")
    require("checked_entrypoints_only" in guard_names, "bridge should guard checked entrypoints")
    require("confirmation_before_handoff" in guard_names, "bridge should guard mapping confirmation")
    require("planned_runtimes_non_generating" in guard_names, "bridge should guard planned runtimes")
    require("no_forecast_or_score_outputs" in guard_names, "bridge should guard forecast and score outputs")

    print("checked private source adapter intake bridge")


if __name__ == "__main__":
    main()
