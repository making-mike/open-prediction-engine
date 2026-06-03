#!/usr/bin/env python3
"""Generate or check private setup request routing examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_source_adapter_intake_bridge import build_bridge, load_generated_bridge
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-requests"
REQUESTS_PATH = GENERATED / "ope-private-setup-requests.generated.json"
SCHEMA = SPEC / "private-setup-request.schema.json"
BRIDGE_PATH = "spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-intake-bridge.generated.json"
GENERATED_AT = "2026-06-07T09:00:00Z"
NO_COMMAND = "none"
FORECAST_SCORE_BLOCKS = ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]


class PrivateSetupRequestError(Exception):
    pass


def forecast_intent(question: str) -> dict[str, Any]:
    return {
        "questionText": question,
        "outputType": "binary",
        "horizonLabel": "caller_declared",
        "resolutionNeeded": True,
    }


def route_for_bridge_row(row: dict[str, Any]) -> tuple[str, str, str]:
    source_kind = row["sourceKind"]
    if source_kind == "local_file":
        return "accepted_current_entrypoint", "run_source_builder", "provide caller-approved local file paths"
    if source_kind == "manual_mapping":
        return "needs_confirmation", "request_mapping_confirmation", "confirm source roles, field mappings, and aliases"
    if source_kind == "auto_evidence_connector":
        return "fixture_ready", "use_fixture_evidence", "provide an accepted auto-evidence fixture request"
    if source_kind in {"manual_upload", "private_api", "private_database"}:
        return "wait_for_runtime", "wait_for_runtime", "wait for a checked runtime before retrying"
    if source_kind == "unregistered_source":
        return "replace_source", "replace_source", "replace the source kind with a declared adapter"
    if source_kind == "unsafe_source":
        return "rejected", "stop", "remove unsafe source input and provide a safe replacement"
    raise PrivateSetupRequestError(f"unsupported bridge source kind: {source_kind}")


def request_policy_for(source_kind: str) -> dict[str, Any]:
    if source_kind == "auto_evidence_connector":
        return {
            "dataMode": "auto",
            "allowedSourceKinds": [source_kind],
            "approvalStatus": "not_required",
            "allowLiveFetch": False,
            "allowCredentialUse": False,
        }
    if source_kind in {"manual_mapping", "manual_upload", "private_api", "private_database"}:
        return {
            "dataMode": "provided",
            "allowedSourceKinds": [source_kind],
            "approvalStatus": "requested" if source_kind == "manual_mapping" else "confirmed",
            "allowLiveFetch": False,
            "allowCredentialUse": False,
        }
    if source_kind == "unsafe_source":
        return {
            "dataMode": "provided",
            "allowedSourceKinds": [source_kind],
            "approvalStatus": "rejected",
            "allowLiveFetch": False,
            "allowCredentialUse": False,
        }
    return {
        "dataMode": "provided",
        "allowedSourceKinds": [source_kind],
        "approvalStatus": "not_required",
        "allowLiveFetch": False,
        "allowCredentialUse": False,
    }


def setup_mode_for(source_kind: str) -> str:
    if source_kind in {"manual_mapping", "auto_evidence_connector"}:
        return "extend_setup"
    if source_kind == "unregistered_source":
        return "reuse_setup"
    return "new_setup"


def row_from_bridge(index: int, row: dict[str, Any]) -> dict[str, Any]:
    status, route, caller_action = route_for_bridge_row(row)
    selected = row["sourceKind"]
    return {
        "requestRowId": f"privatesetuprequestrow-{index:03d}",
        "privateSetupRequestId": f"privatesetuprequest-{index:03d}",
        "setupMode": setup_mode_for(selected),
        "forecastIntent": forecast_intent(
            f"Estimate a future operational probability from caller-approved {selected.replace('_', ' ')} sources."
        ),
        "sourcePolicy": request_policy_for(selected),
        "selectedSourceKind": selected,
        "setupRequestStatus": status,
        "routeDecision": route,
        "boundBridgeRowId": row["bridgeRowId"],
        "boundOutcomeRowId": row["outcomeRowId"],
        "allowedEntrypoint": row["allowedEntrypoint"],
        "commandToRun": row["currentCommand"] if row["currentCommand"] != NO_COMMAND else row["retryCommand"],
        "requiredCallerAction": caller_action,
        "blockedOutputs": sorted(set(row["blockedOutputs"] + FORECAST_SCORE_BLOCKS)),
        "createsOutputs": False,
        "canReadPrivateData": False,
        "canCreateForecastArtifacts": False,
        "canCreateScoringRecords": False,
        "canStoreCredentials": False,
        "agentInstruction": row["agentInstruction"],
    }


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privatesetuprequestguard-001",
            "name": "bridge_binding",
            "rule": "Every private setup request row must bind one private source adapter bridge row.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
        {
            "guardId": "privatesetuprequestguard-002",
            "name": "request_before_source_read",
            "rule": "Request classification must not read private data or execute source commands.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
        {
            "guardId": "privatesetuprequestguard-003",
            "name": "approval_before_mapping",
            "rule": "Manual mapping requests must require caller confirmation before source-handoff.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
        {
            "guardId": "privatesetuprequestguard-004",
            "name": "planned_runtimes_wait",
            "rule": "Manual upload, private API, and private database requests must wait for future runtimes.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
        {
            "guardId": "privatesetuprequestguard-005",
            "name": "no_forecast_or_score_outputs",
            "rule": "Private setup request classification must not create forecast artifacts or scoring records.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
        {
            "guardId": "privatesetuprequestguard-006",
            "name": "unsafe_sources_stop",
            "rule": "Unsafe and unregistered sources must not enter source intake through request classification.",
            "checkedBy": ["scripts/check_private_setup_requests.py"],
        },
    ]


def build_request_set() -> dict[str, Any]:
    bridge = build_bridge()
    rows = [row_from_bridge(index, row) for index, row in enumerate(bridge["bridgeRows"], start=1)]
    request_set = {
        "privateSetupRequestSetId": "privatesetuprequestset-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "request_contract_only",
        "boundPrivateSourceAdapterIntakeBridgeId": bridge["privateSourceAdapterIntakeBridgeId"],
        "boundPrivateSourceAdapterOutcomeMatrixId": bridge["boundPrivateSourceAdapterOutcomeMatrixId"],
        "boundPrivateSourceAdapterCapabilityId": bridge["boundPrivateSourceAdapterCapabilityId"],
        "boundPrivateSetupWorkflowId": bridge["boundPrivateSetupWorkflowId"],
        "boundPrivateSourceAdapterIntakeBridgePath": BRIDGE_PATH,
        "requestRows": rows,
        "executionBoundary": {
            "requestSetDoesNotExecute": True,
            "normalChecksOffline": True,
            "readsPrivateData": False,
            "createsSourceManifests": False,
            "createsFieldMappings": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
            "routesOnlyThroughAdapterBridge": True,
        },
        "guards": guards(),
        "warnings": [
            "Private setup requests classify setup intent before any source read.",
            "Routes are guidance into checked local entrypoints, not execution.",
            "Forecast artifacts and scoring records require later source intake, method gates, forecast execution, and resolution.",
            "Private API, database, and manual upload runtimes remain planned-only.",
        ],
    }
    validate_request_set(request_set, bridge)
    return request_set


def validate_request_set(request_set: dict[str, Any], bridge: dict[str, Any]) -> None:
    errors = validate_record(request_set, SCHEMA)
    if errors:
        raise PrivateSetupRequestError(f"private setup request schema validation failed: {errors[0]}")
    if request_set["boundPrivateSourceAdapterIntakeBridgeId"] != bridge["privateSourceAdapterIntakeBridgeId"]:
        raise PrivateSetupRequestError("request set must bind private source adapter bridge")

    bridge_rows = {row["sourceKind"]: row for row in bridge["bridgeRows"]}
    request_rows = {row["selectedSourceKind"]: row for row in request_set["requestRows"]}
    if set(request_rows) != set(bridge_rows):
        raise PrivateSetupRequestError("request rows must cover every bridge source kind")

    for source_kind, request_row in request_rows.items():
        bridge_row = bridge_rows[source_kind]
        if request_row["boundBridgeRowId"] != bridge_row["bridgeRowId"]:
            raise PrivateSetupRequestError(f"{source_kind} bridge row binding drift")
        if request_row["boundOutcomeRowId"] != bridge_row["outcomeRowId"]:
            raise PrivateSetupRequestError(f"{source_kind} outcome row binding drift")
        if request_row["allowedEntrypoint"] != bridge_row["allowedEntrypoint"]:
            raise PrivateSetupRequestError(f"{source_kind} entrypoint drift")
        if request_row["createsOutputs"] or request_row["canReadPrivateData"]:
            raise PrivateSetupRequestError(f"{source_kind} request classification must not execute or read")
        if request_row["canCreateForecastArtifacts"] or request_row["canCreateScoringRecords"]:
            raise PrivateSetupRequestError(f"{source_kind} request classification must not forecast or score")
        if request_row["canStoreCredentials"]:
            raise PrivateSetupRequestError(f"{source_kind} request classification must not store credentials")
        for blocked in FORECAST_SCORE_BLOCKS:
            if blocked not in request_row["blockedOutputs"]:
                raise PrivateSetupRequestError(f"{source_kind} should block {blocked}")

    if request_rows["local_file"]["routeDecision"] != "run_source_builder":
        raise PrivateSetupRequestError("local file request should route to source builder")
    if request_rows["manual_mapping"]["routeDecision"] != "request_mapping_confirmation":
        raise PrivateSetupRequestError("manual mapping request should require confirmation")
    if request_rows["auto_evidence_connector"]["routeDecision"] != "use_fixture_evidence":
        raise PrivateSetupRequestError("auto evidence request should route to fixture evidence")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        if request_rows[source_kind]["routeDecision"] != "wait_for_runtime":
            raise PrivateSetupRequestError(f"{source_kind} should wait for runtime")
    if request_rows["unregistered_source"]["routeDecision"] != "replace_source":
        raise PrivateSetupRequestError("unregistered source should be replaced")
    if request_rows["unsafe_source"]["routeDecision"] != "stop":
        raise PrivateSetupRequestError("unsafe source should stop")

    boundary = request_set["executionBoundary"]
    if boundary["requestSetDoesNotExecute"] is not True or boundary["routesOnlyThroughAdapterBridge"] is not True:
        raise PrivateSetupRequestError("request set should stay non-executing and bridge-routed")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        if boundary[key] is not False:
            raise PrivateSetupRequestError(f"{key} should remain false")


def write_request_set(request_set: dict[str, Any]) -> None:
    write_generated(REQUESTS_PATH, request_set, label="private setup requests", regen="python3 scripts/generate_private_setup_requests.py --write")


def check_request_set(request_set: dict[str, Any]) -> None:
    check_generated(REQUESTS_PATH, request_set, label="private setup requests", regen="python3 scripts/generate_private_setup_requests.py --write")


def load_generated_request_set() -> dict[str, Any] | None:
    if not REQUESTS_PATH.exists():
        return None
    request_set = json.loads(REQUESTS_PATH.read_text(encoding="utf-8"))
    bridge = load_generated_bridge() or build_bridge()
    validate_request_set(request_set, bridge)
    return request_set


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup request drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup requests")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.write or args.check or args.rebuild:
            request_set = build_request_set()
        else:
            request_set = load_generated_request_set() or build_request_set()
    except PrivateSetupRequestError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_request_set(request_set)
    elif args.check:
        check_request_set(request_set)
    else:
        sys.stdout.write(render_json(request_set))


if __name__ == "__main__":
    main()
