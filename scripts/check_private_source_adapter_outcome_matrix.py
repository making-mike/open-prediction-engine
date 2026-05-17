#!/usr/bin/env python3
"""Check private source adapter outcome matrix boundaries."""

from __future__ import annotations

from generate_private_source_adapter_capabilities import build_capabilities
from generate_private_source_adapter_outcome_matrix import build_matrix
from generate_private_setup_workflow import build_workflow


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    workflow = build_workflow()
    capability = build_capabilities()
    matrix = build_matrix()

    require(matrix["scope"] == "domain_agnostic", "adapter outcome matrix should be domain agnostic")
    require(
        matrix["runtimeStatus"] == "decision_matrix_contract_only",
        "adapter outcome matrix should remain contract-only",
    )
    require(
        matrix["boundPrivateSourceAdapterCapabilityId"] == capability["privateSourceAdapterCapabilityId"],
        "adapter outcome matrix should bind capabilities",
    )
    require(
        matrix["boundPrivateSetupWorkflowId"] == workflow["privateSetupWorkflowId"],
        "adapter outcome matrix should bind private setup workflow",
    )

    workflow_outcomes = {item["outcomeClass"] for item in workflow["outcomeClasses"]}
    outcome_classes = {item["outcomeClass"]: item for item in matrix["outcomeClasses"]}
    expected_classes = {
        "available_fixture",
        "approval_required_fixture",
        "planned_runtime",
        "unsupported_source",
        "credential_missing",
        "rejected_unsafe_source",
    }
    require(set(outcome_classes) == expected_classes, "adapter outcome class set drifted")
    for item in outcome_classes.values():
        require(item["setupOutcomeClass"] in workflow_outcomes, "outcome class should bind workflow outcome")
    require(outcome_classes["available_fixture"]["canEnterSetup"] is True, "available fixtures should enter setup")
    for name in expected_classes - {"available_fixture"}:
        require(outcome_classes[name]["canEnterSetup"] is False, f"{name} should not enter setup")

    rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    capability_adapters = {item["sourceKind"]: item for item in capability["adapters"]}
    for source_kind, adapter in capability_adapters.items():
        row = rows[source_kind]
        require(row["capabilityBindingStatus"] == "bound_adapter", f"{source_kind} should bind a capability adapter")
        require(row["adapterId"] == adapter["adapterId"], f"{source_kind} adapter id drifted")
        require(row["requiresApproval"] == adapter["approvalRequired"], f"{source_kind} approval drifted")

    require(rows["local_file"]["outcomeClass"] == "available_fixture", "local file should be available fixture")
    require(rows["local_file"]["canCreateSourceManifest"] is True, "local file can route to source manifest builder")
    require(rows["local_file"]["agentNextAction"] == "run_source_builder", "local file should route to source builder")

    require(
        rows["manual_mapping"]["outcomeClass"] == "approval_required_fixture",
        "manual mapping should require confirmation",
    )
    require(rows["manual_mapping"]["requiresApproval"] is True, "manual mapping should require approval")
    require(
        rows["manual_mapping"]["agentNextAction"] == "request_mapping_confirmation",
        "manual mapping should request confirmation",
    )

    require(
        rows["auto_evidence_connector"]["outcomeClass"] == "available_fixture",
        "auto evidence should be available fixture",
    )
    require(
        rows["auto_evidence_connector"]["agentNextAction"] == "use_auto_evidence_fixture",
        "auto evidence should route to fixture replay",
    )

    require(rows["manual_upload"]["outcomeClass"] == "planned_runtime", "manual upload should be planned runtime")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row = rows[source_kind]
        require(row["setupOutcomeClass"] == "runtime_not_implemented", f"{source_kind} should be runtime-not-implemented")
        require(row["canEnterSetup"] is False, f"{source_kind} should not enter setup")
        require(row["canExecuteSourceRead"] is False, f"{source_kind} should not execute source reads")
        require(row["canCreateSourceManifest"] is False, f"{source_kind} should not create source manifests")

    for source_kind in ["private_api", "private_database"]:
        row = rows[source_kind]
        require(row["outcomeClass"] == "credential_missing", f"{source_kind} should surface credential_missing")
        require(row["requiresCredential"] is True, f"{source_kind} should require credentials in a future runtime")
        require(row["hasCredentialRuntime"] is False, f"{source_kind} should not have credential runtime")
        require(
            row["agentNextAction"] == "request_credentials_after_runtime",
            f"{source_kind} should wait for credential-safe runtime",
        )

    require(rows["unregistered_source"]["outcomeClass"] == "unsupported_source", "unregistered sources should be unsupported")
    require(
        rows["unregistered_source"]["capabilityBindingStatus"] == "not_in_capability_contract",
        "unregistered sources should not bind a capability",
    )
    require(rows["unsafe_source"]["outcomeClass"] == "rejected_unsafe_source", "unsafe sources should be rejected")
    require(rows["unsafe_source"]["setupOutcomeClass"] == "rejected_source", "unsafe sources should bind rejected_source")

    for source_kind, row in rows.items():
        require(row["canCreateForecastArtifacts"] is False, f"{source_kind} must not create forecast artifacts")
        require(row["canCreateScoringRecords"] is False, f"{source_kind} must not create scoring records")
        for artifact in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record"]:
            require(artifact in row["blockedArtifacts"], f"{source_kind} should block {artifact}")

    boundary = matrix["executionBoundary"]
    require(boundary["matrixDoesNotExecute"] is True, "matrix should not execute source reads")
    require(boundary["normalChecksOffline"] is True, "matrix checks should remain offline")
    require(boundary["createsSourceManifests"] is False, "matrix should not create source manifests")
    require(boundary["createsForecastArtifacts"] is False, "matrix should not create forecasts")
    require(boundary["createsScoringRecords"] is False, "matrix should not create scoring records")
    require(boundary["storesCredentials"] is False, "matrix should not store credentials")
    require(boundary["privateAdapterRuntimeImplemented"] is False, "private adapter runtime should not be implemented")

    guard_names = {item["name"] for item in matrix["guards"]}
    require("capability_binding" in guard_names, "matrix should guard capability binding")
    require("workflow_outcome_binding" in guard_names, "matrix should guard workflow outcome binding")
    require("no_execution" in guard_names, "matrix should guard no-execution behavior")
    require("no_artifacts" in guard_names, "matrix should guard artifact creation")
    require("planned_runtimes_blocked" in guard_names, "matrix should guard planned runtimes")

    print("checked private source adapter outcome matrix")


if __name__ == "__main__":
    main()
