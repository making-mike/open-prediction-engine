#!/usr/bin/env python3
"""Return the first safe non-executing action for one private setup request."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_requests import build_request_set, render_json
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = SPEC / "private-setup-first-action.schema.json"
GENERATED_AT = "2026-06-07T10:00:00Z"
NO_COMMAND = "none"
ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*-[0-9]{3,}$")
KNOWN_SOURCE_KINDS = {
    "local_file",
    "manual_mapping",
    "manual_upload",
    "auto_evidence_connector",
    "private_api",
    "private_database",
    "unregistered_source",
    "unsafe_source",
}


class PrivateSetupActionError(Exception):
    pass


def safe_id(value: Any, fallback: str) -> str:
    if isinstance(value, str) and ID_PATTERN.match(value):
        return value
    return fallback


def default_forecast_intent() -> dict[str, Any]:
    return {
        "questionText": "Estimate a future operational probability from caller-approved sources.",
        "outputType": "binary",
        "horizonLabel": "caller_declared",
        "resolutionNeeded": True,
    }


def normalize_forecast_intent(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return default_forecast_intent()
    output_type = value.get("outputType")
    allowed_outputs = {"binary", "categorical", "numeric", "distribution"}
    return {
        "questionText": str(value.get("questionText") or default_forecast_intent()["questionText"])[:280],
        "outputType": output_type if output_type in allowed_outputs else "unknown",
        "horizonLabel": str(value.get("horizonLabel") or "caller_declared")[:80],
        "resolutionNeeded": bool(value.get("resolutionNeeded", True)),
    }


def normalize_source_policy(value: Any, source_kind: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        value = {}
    data_mode = value.get("dataMode")
    if data_mode not in {"provided", "auto", "hybrid"}:
        data_mode = "unknown"
    approval_status = value.get("approvalStatus")
    if approval_status not in {"not_required", "requested", "confirmed", "rejected"}:
        approval_status = "unknown"
    allowed = value.get("allowedSourceKinds")
    if not isinstance(allowed, list):
        allowed = [source_kind] if source_kind != "unknown_source_kind" else []
    normalized_allowed = [
        str(item)[:80]
        for item in allowed
        if isinstance(item, str) and len(item) >= 3
    ][:12]
    return {
        "dataMode": data_mode,
        "allowedSourceKinds": normalized_allowed,
        "approvalStatus": approval_status,
        "allowLiveFetch": bool(value.get("allowLiveFetch", False)),
        "allowCredentialUse": bool(value.get("allowCredentialUse", False)),
    }


def minimal_request_from_input(data: dict[str, Any]) -> dict[str, Any]:
    source_kind = data.get("selectedSourceKind") or data.get("sourceKind") or "unknown_source_kind"
    if not isinstance(source_kind, str) or len(source_kind) < 3:
        source_kind = "unknown_source_kind"
    source_kind = source_kind[:80]
    return {
        "requestRowId": safe_id(data.get("requestRowId"), "privatesetuprequestrow-999"),
        "privateSetupRequestId": safe_id(data.get("privateSetupRequestId"), "privatesetuprequest-999"),
        "setupMode": data.get("setupMode") if data.get("setupMode") in {"new_setup", "extend_setup", "reuse_setup"} else "unknown",
        "forecastIntent": normalize_forecast_intent(data.get("forecastIntent")),
        "sourcePolicy": normalize_source_policy(data.get("sourcePolicy"), source_kind),
        "selectedSourceKind": source_kind,
        "setupRequestStatus": data.get("setupRequestStatus", "rejected"),
        "routeDecision": data.get("routeDecision", "reject_bad_request"),
        "boundBridgeRowId": safe_id(data.get("boundBridgeRowId"), "privateadapterbridge-999"),
        "boundOutcomeRowId": safe_id(data.get("boundOutcomeRowId"), "privateadapteroutcomerow-999"),
        "allowedEntrypoint": data.get("allowedEntrypoint", "no_current_entrypoint"),
        "commandToRun": data.get("commandToRun", NO_COMMAND),
        "requiredCallerAction": data.get("requiredCallerAction", "provide a valid private setup request"),
    }


def request_by_id(request_id: str, request_set: dict[str, Any]) -> dict[str, Any]:
    for row in request_set["requestRows"]:
        if row["privateSetupRequestId"] == request_id:
            return row
    raise PrivateSetupActionError(f"unknown private setup request id: {request_id}")


def request_from_input(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PrivateSetupActionError("request input could not be read") from exc
    except json.JSONDecodeError as exc:
        raise PrivateSetupActionError("request input is not valid JSON") from exc
    if not isinstance(data, dict):
        raise PrivateSetupActionError("request input must be a JSON object")
    if "privateSetupRequest" in data and isinstance(data["privateSetupRequest"], dict):
        data = data["privateSetupRequest"]
    return minimal_request_from_input(data)


def status_for_route(route_decision: str, source_kind: str) -> tuple[str, str, int, str]:
    if route_decision == "run_source_builder":
        return "ready_to_run_checked_command", "none", 0, "Ready to run the checked local source-builder command."
    if route_decision == "request_mapping_confirmation":
        return "confirmation_required", "confirmation_required", 0, "Caller confirmation is required before source handoff."
    if route_decision == "use_fixture_evidence":
        return "fixture_ready", "none", 0, "Ready to run fixture-mode policy-bound evidence gathering."
    if route_decision == "wait_for_runtime":
        return "runtime_not_implemented", "runtime_not_implemented", 0, "The requested source kind needs a future checked runtime."
    if route_decision == "replace_source":
        return "source_replacement_required", "unsupported_source", 0, "The requested source kind is not declared in current capabilities."
    if route_decision == "stop" or source_kind == "unsafe_source":
        return "rejected_unsafe_source", "rejected_unsafe_source", 0, "Unsafe source input is rejected before setup."
    return "bad_request", "bad_request", 2, "The request cannot be routed safely."


def approval_error(row: dict[str, Any]) -> str | None:
    source_kind = row["selectedSourceKind"]
    policy = row["sourcePolicy"]
    approval_status = policy["approvalStatus"]
    if source_kind == "unsafe_source":
        return None
    if approval_status == "rejected":
        return "source approval was rejected"
    if source_kind == "manual_mapping" and approval_status not in {"requested", "confirmed"}:
        return "manual mapping requires caller confirmation"
    if source_kind in {"manual_upload", "private_api", "private_database"} and approval_status != "confirmed":
        return "private source runtimes require confirmed caller approval"
    if policy["allowCredentialUse"] and approval_status != "confirmed":
        return "credential use requires confirmed caller approval"
    if policy["allowedSourceKinds"] and source_kind not in policy["allowedSourceKinds"]:
        return "selected source kind is outside the allowed source policy"
    return None


def execution_boundary() -> dict[str, bool]:
    return {
        "dispatcherDoesNotExecute": True,
        "normalChecksOffline": True,
        "readsPrivateData": False,
        "runsSuggestedCommand": False,
        "createsSourceManifests": False,
        "createsFieldMappings": False,
        "createsForecastArtifacts": False,
        "createsScoringRecords": False,
        "storesCredentials": False,
    }


def action_from_request_row(
    row: dict[str, Any],
    request_set: dict[str, Any],
    sequence: int = 1,
) -> dict[str, Any]:
    source_kind = row["selectedSourceKind"]
    if source_kind not in KNOWN_SOURCE_KINDS:
        action_status = "bad_request"
        error_code = "unknown_source_kind"
        exit_code = 2
        message = "Unknown source kind; replace it with a declared private source adapter."
        route_decision = "reject_bad_request"
        allowed_entrypoint = "no_current_entrypoint"
        command_to_run = NO_COMMAND
        required_action = "replace the source kind with a declared adapter"
        bound_bridge_row_id = None
        bound_outcome_row_id = None
    else:
        approval_problem = approval_error(row)
        if approval_problem:
            action_status = "bad_request"
            error_code = "missing_approval"
            exit_code = 2
            message = approval_problem
            route_decision = "reject_bad_request"
            allowed_entrypoint = "no_current_entrypoint"
            command_to_run = NO_COMMAND
            required_action = "confirm caller approval and retry the private setup request"
            bound_bridge_row_id = row.get("boundBridgeRowId")
            bound_outcome_row_id = row.get("boundOutcomeRowId")
        else:
            route_decision = row["routeDecision"]
            action_status, error_code, exit_code, message = status_for_route(route_decision, source_kind)
            allowed_entrypoint = row["allowedEntrypoint"]
            command_to_run = row["commandToRun"]
            required_action = row["requiredCallerAction"]
            bound_bridge_row_id = row.get("boundBridgeRowId")
            bound_outcome_row_id = row.get("boundOutcomeRowId")

    action = {
        "privateSetupFirstActionId": f"privatesetupfirstaction-{sequence:03d}",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "dispatcher_result_only",
        "requestBinding": {
            "privateSetupRequestSetId": request_set.get("privateSetupRequestSetId"),
            "privateSetupRequestId": row["privateSetupRequestId"],
            "requestRowId": row.get("requestRowId"),
            "boundPrivateSourceAdapterIntakeBridgeId": request_set.get("boundPrivateSourceAdapterIntakeBridgeId"),
            "boundBridgeRowId": bound_bridge_row_id,
            "boundOutcomeRowId": bound_outcome_row_id,
        },
        "setupMode": row["setupMode"],
        "sourceKind": source_kind,
        "sourcePolicy": row["sourcePolicy"],
        "forecastIntent": row["forecastIntent"],
        "actionStatus": action_status,
        "routeDecision": route_decision,
        "allowedEntrypoint": allowed_entrypoint,
        "commandToRun": command_to_run,
        "requiredCallerAction": required_action,
        "error": {
            "code": error_code,
            "message": message,
        },
        "exitCode": exit_code,
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This dispatcher returns the first safe action only; it does not run the suggested command.",
            "Forecast artifacts and scoring records require later intake, method, forecast, resolution, and scoring steps.",
            "Commands named in this response are checked local entrypoints, not hidden side effects.",
        ],
    }
    validate_action(action)
    return action


def bad_request_action(message: str) -> dict[str, Any]:
    request_set = {
        "privateSetupRequestSetId": None,
        "boundPrivateSourceAdapterIntakeBridgeId": None,
    }
    row = {
        "requestRowId": None,
        "privateSetupRequestId": "privatesetuprequest-999",
        "setupMode": "unknown",
        "forecastIntent": default_forecast_intent(),
        "sourcePolicy": normalize_source_policy({}, "unknown_source_kind"),
        "selectedSourceKind": "unknown_source_kind",
        "routeDecision": "reject_bad_request",
        "allowedEntrypoint": "no_current_entrypoint",
        "commandToRun": NO_COMMAND,
        "requiredCallerAction": "provide a valid private setup request",
    }
    action = action_from_request_row(row, request_set, sequence=999)
    action["error"] = {"code": "bad_request", "message": message}
    action["exitCode"] = 2
    validate_action(action)
    return action


def validate_action(action: dict[str, Any]) -> None:
    errors = validate_record(action, SCHEMA)
    if errors:
        raise PrivateSetupActionError(f"private setup first action schema validation failed: {errors[0]}")
    boundary = action["executionBoundary"]
    if boundary["dispatcherDoesNotExecute"] is not True or boundary["runsSuggestedCommand"] is not False:
        raise PrivateSetupActionError("private setup first action must stay non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        if boundary[key] is not False:
            raise PrivateSetupActionError(f"{key} must remain false")


def dispatch_action(request_id: str | None = None, input_path: Path | None = None) -> dict[str, Any]:
    request_set = build_request_set()
    if request_id and input_path:
        return bad_request_action("provide either --request-id or --input, not both")
    if request_id:
        try:
            row = request_by_id(request_id, request_set)
        except PrivateSetupActionError as exc:
            return bad_request_action(str(exc))
        sequence = int(request_id.rsplit("-", 1)[-1]) if request_id.rsplit("-", 1)[-1].isdigit() else 999
        return action_from_request_row(row, request_set, sequence=sequence)
    if input_path:
        try:
            row = request_from_input(input_path)
        except PrivateSetupActionError as exc:
            return bad_request_action(str(exc))
        return action_from_request_row(row, request_set, sequence=999)
    return bad_request_action("provide --request-id or --input")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", help="generated private setup request id")
    parser.add_argument("--input", type=Path, help="JSON object containing one private setup request")
    args = parser.parse_args()
    action = dispatch_action(request_id=args.request_id, input_path=args.input)
    sys.stdout.write(render_json(action))
    raise SystemExit(action["exitCode"])


if __name__ == "__main__":
    main()
