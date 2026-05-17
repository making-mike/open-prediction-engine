#!/usr/bin/env python3
"""Check private source adapter capability boundaries."""

from __future__ import annotations

from generate_private_source_adapter_capabilities import build_capabilities
from generate_private_setup_workflow import build_workflow


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    workflow = build_workflow()
    capability = build_capabilities()

    require(capability["scope"] == "domain_agnostic", "private source adapters should be domain agnostic")
    require(
        capability["runtimeStatus"] == "capability_contract_only",
        "private source adapters should remain declaration-only",
    )
    require(
        capability["boundPrivateSetupWorkflowId"] == workflow["privateSetupWorkflowId"],
        "private source adapters should bind the private setup workflow",
    )

    workflow_source_kinds = [item["sourceKind"] for item in workflow["supportedSourceKinds"]]
    require(capability["supportedSourceKinds"] == workflow_source_kinds, "source kind binding drifted")

    adapters = {item["sourceKind"]: item for item in capability["adapters"]}
    require(set(adapters) == set(workflow_source_kinds), "adapter source kind set drifted")

    local_file = adapters["local_file"]
    require(local_file["implementationStatus"] == "implemented_fixture", "local files should be fixture implemented")
    require(local_file["availabilityStatus"] == "available_fixture", "local file adapter should be fixture available")
    require(local_file["canInspect"] is True, "local file adapter should inspect approved fixture files")
    require(local_file["canFetchLive"] is False, "local file adapter should not live-fetch")
    require(local_file["canParseGeneric"] is False, "local file adapter should not claim generic parsing")
    require(local_file["nextAction"] == "use_source_builder", "local file adapter should route to source builder")

    manual_mapping = adapters["manual_mapping"]
    require(manual_mapping["availabilityStatus"] == "approval_gated_fixture", "manual mapping should be approval-gated")
    require(manual_mapping["approvalRequired"] is True, "manual mapping should require confirmation")
    require(
        manual_mapping["nextAction"] == "use_manual_mapping_confirmation",
        "manual mapping should route to mapping confirmation",
    )

    auto_evidence = adapters["auto_evidence_connector"]
    require(auto_evidence["implementationStatus"] == "implemented_fixture", "auto evidence should be fixture implemented")
    require(auto_evidence["canExecuteInNormalChecks"] is True, "auto evidence fixtures should run in normal checks")
    require(auto_evidence["canFetchLive"] is False, "auto evidence fixtures should not live-fetch in normal checks")
    require(auto_evidence["nextAction"] == "use_auto_evidence_fixture", "auto evidence should route to fixture mode")

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        item = adapters[source_kind]
        require(item["implementationStatus"] == "planned_contract_only", f"{source_kind} should stay planned only")
        require(item["availabilityStatus"] == "planned_contract_only", f"{source_kind} should stay planned only")
        require(item["setupOutcomeIfRequested"] == "runtime_not_implemented", f"{source_kind} should not enter setup")
        require(item["canInspect"] is False, f"{source_kind} should not inspect data yet")
        require(item["canFetchLive"] is False, f"{source_kind} should not fetch live data yet")
        require(item["canParseGeneric"] is False, f"{source_kind} should not parse arbitrary schemas yet")
        require(item["canExecuteInNormalChecks"] is False, f"{source_kind} should not execute in normal checks")
        require(item["approvalRequired"] is True, f"{source_kind} should require approval")
        require(item["nextAction"] == "wait_for_runtime", f"{source_kind} should wait for an explicit runtime")

    for source_kind, item in adapters.items():
        require(item["canStoreSecrets"] is False, f"{source_kind} must not store secrets")
        require("include_secrets_in_artifacts" in item["blockedActions"], f"{source_kind} must block secret artifacts")
        require(
            "create_forecast_without_intake" in item["blockedActions"],
            f"{source_kind} must block forecasts without intake",
        )

    boundary = capability["executionBoundary"]
    require(boundary["declarationsDoNotExecute"] is True, "capability declarations should not execute")
    require(boundary["normalChecksOffline"] is True, "normal checks should remain offline")
    require(boundary["credentialStorageImplemented"] is False, "credential storage should not be implemented")
    require(boundary["genericPrivateApiRuntimeImplemented"] is False, "private API runtime should not be implemented")
    require(
        boundary["genericPrivateDatabaseRuntimeImplemented"] is False,
        "private database runtime should not be implemented",
    )
    require(boundary["manualUploadRuntimeImplemented"] is False, "manual upload runtime should not be implemented")
    require(
        boundary["arbitraryPrivateSchemaParsingImplemented"] is False,
        "arbitrary private schema parsing should not be implemented",
    )

    guard_names = {item["name"] for item in capability["guards"]}
    require("declaration_only" in guard_names, "adapter capability should guard declaration-only behavior")
    require("workflow_source_binding" in guard_names, "adapter capability should guard workflow source binding")
    require("no_secret_storage" in guard_names, "adapter capability should guard secrets")
    require("normal_checks_offline" in guard_names, "adapter capability should guard offline checks")
    require("planned_private_runtimes" in guard_names, "adapter capability should guard planned private runtimes")

    print("checked private source adapter capabilities")


if __name__ == "__main__":
    main()
