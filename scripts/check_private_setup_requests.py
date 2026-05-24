#!/usr/bin/env python3
"""Check private setup request routing boundaries."""

from __future__ import annotations

from generate_private_setup_requests import build_request_set
from generate_private_source_adapter_intake_bridge import build_bridge


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    bridge = build_bridge()
    request_set = build_request_set()

    require(request_set["scope"] == "domain_agnostic", "private setup requests should be domain agnostic")
    require(request_set["runtimeStatus"] == "request_contract_only", "private setup requests should be contract-only")
    require(
        request_set["boundPrivateSourceAdapterIntakeBridgeId"] == bridge["privateSourceAdapterIntakeBridgeId"],
        "private setup requests should bind the adapter bridge",
    )

    bridge_rows = {row["sourceKind"]: row for row in bridge["bridgeRows"]}
    request_rows = {row["selectedSourceKind"]: row for row in request_set["requestRows"]}
    require(set(request_rows) == set(bridge_rows), "private setup requests should cover every bridge row")

    for source_kind, row in request_rows.items():
        bridge_row = bridge_rows[source_kind]
        require(row["boundBridgeRowId"] == bridge_row["bridgeRowId"], f"{source_kind} bridge binding drifted")
        require(row["boundOutcomeRowId"] == bridge_row["outcomeRowId"], f"{source_kind} outcome binding drifted")
        require(row["allowedEntrypoint"] == bridge_row["allowedEntrypoint"], f"{source_kind} entrypoint drifted")
        require(row["createsOutputs"] is False, f"{source_kind} request should not create outputs")
        require(row["canReadPrivateData"] is False, f"{source_kind} request should not read private data")
        require(row["canCreateForecastArtifacts"] is False, f"{source_kind} request should not create forecasts")
        require(row["canCreateScoringRecords"] is False, f"{source_kind} request should not create scoring records")
        require(row["canStoreCredentials"] is False, f"{source_kind} request should not store credentials")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]:
            require(blocked in row["blockedOutputs"], f"{source_kind} should block {blocked}")

    require(request_rows["local_file"]["routeDecision"] == "run_source_builder", "local files should route to source builder")
    require(
        request_rows["local_file"]["commandToRun"] == "python3 scripts/ope.py source-builder",
        "local file request command drifted",
    )
    require(
        request_rows["manual_mapping"]["routeDecision"] == "request_mapping_confirmation",
        "manual mapping should require confirmation",
    )
    require(
        request_rows["manual_mapping"]["commandToRun"] == "python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
        "manual mapping retry command drifted",
    )
    require(
        request_rows["auto_evidence_connector"]["routeDecision"] == "use_fixture_evidence",
        "auto evidence should route to fixture evidence",
    )
    require(
        request_rows["auto_evidence_connector"]["commandToRun"] == "python3 scripts/ope.py gather-evidence",
        "auto evidence command drifted",
    )
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row = request_rows[source_kind]
        require(row["routeDecision"] == "wait_for_runtime", f"{source_kind} should wait for runtime")
        require(row["commandToRun"] == "none", f"{source_kind} should not expose a command")
    require(request_rows["unregistered_source"]["routeDecision"] == "replace_source", "unregistered source should be replaced")
    require(request_rows["unsafe_source"]["routeDecision"] == "stop", "unsafe source should stop")

    boundary = request_set["executionBoundary"]
    require(boundary["requestSetDoesNotExecute"] is True, "request set should not execute")
    require(boundary["normalChecksOffline"] is True, "request checks should remain offline")
    require(boundary["routesOnlyThroughAdapterBridge"] is True, "request rows should route through bridge")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    guard_names = {item["name"] for item in request_set["guards"]}
    require("bridge_binding" in guard_names, "request set should guard bridge binding")
    require("request_before_source_read" in guard_names, "request set should guard pre-read classification")
    require("planned_runtimes_wait" in guard_names, "request set should guard planned runtimes")
    require("unsafe_sources_stop" in guard_names, "request set should guard unsafe sources")

    print("checked private setup requests")


if __name__ == "__main__":
    main()
