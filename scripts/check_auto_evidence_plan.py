#!/usr/bin/env python3
"""Check the first agent-native auto-evidence planning surface."""

from __future__ import annotations

import copy
import tempfile
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_file
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from source_connector_catalog import SOURCE_CONNECTOR_REGISTRY_ID, SOURCE_CONNECTOR_RESULT_SET_ID
from validate_forecast_request import load_json, validate_request


def check_default_plan() -> None:
    plan = build_plan(DEFAULT_REQUEST)
    if plan["planStatus"] != "planned":
        raise AssertionError("auto-evidence request should produce a planned dry run")
    if plan["dataMode"] != "auto":
        raise AssertionError("auto-evidence plan should preserve dataMode auto")
    if plan["controls"]["networkAccess"] is not False:
        raise AssertionError("dry-run evidence plan must not perform network access")
    if plan["controls"]["liveFetch"] is not False:
        raise AssertionError("dry-run evidence plan must not live-fetch")
    if plan["controls"]["effectfulGeneration"] is not False:
        raise AssertionError("dry-run evidence plan must not generate an effectful forecast")
    if plan["sourcePolicy"]["allowNetworkAccess"] is not True:
        raise AssertionError("source policy should declare future network permission explicitly")
    if plan["sourceConnectorRegistryId"] != SOURCE_CONNECTOR_REGISTRY_ID:
        raise AssertionError("auto-evidence plan should bind the source connector registry")
    if plan["expectedSourceConnectorResultSetId"] != SOURCE_CONNECTOR_RESULT_SET_ID:
        raise AssertionError("auto-evidence plan should bind the expected connector result set")
    if plan["connectorPolicyChecks"]["allRequestedConnectorsRegistered"] is not True:
        raise AssertionError("default connector policy should use registered connectors")
    if plan["connectorPolicyChecks"]["unsupportedConnectors"]:
        raise AssertionError("default connector policy should not use unsupported connectors")
    if plan["connectorPolicyChecks"]["resolutionOnlyConnectors"]:
        raise AssertionError("default connector policy should not use resolution-only connectors")
    if "web_search" in plan["sourcePolicy"]["allowedConnectors"]:
        raise AssertionError("first auto-evidence fixture must not enable broad web search")
    if any(intent["connector"] == "declared_operations_fixture" for intent in plan["searchIntents"]):
        raise AssertionError("forecast-time search intents must exclude resolution-only connectors")
    if not plan["unavailableEvidence"]:
        raise AssertionError("auto-evidence plan should name unavailable evidence")
    if any("all available" in warning.lower() for warning in plan["warnings"]):
        raise AssertionError("auto-evidence plan must not claim all evidence coverage")


def write_temp_request(request: dict[str, Any]) -> Path:
    tmp = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
    try:
        import json

        json.dump(request, tmp)
        tmp.write("\n")
        return Path(tmp.name)
    finally:
        tmp.close()


def check_unsupported_auto_connector() -> None:
    request = copy.deepcopy(load_json(DEFAULT_REQUEST))
    request["sourcePolicy"]["allowedConnectors"] = ["web_search"]
    decision = validate_request(request)
    if decision["decisionStatus"] != "rejected":
        raise AssertionError("unsupported auto connector should be rejected")
    if "unsupported_connector" not in decision["reasonCodes"]:
        raise AssertionError("unsupported auto connector should identify connector policy")
    path = write_temp_request(request)
    try:
        plan = build_plan(path)
    finally:
        path.unlink()
    if plan["planStatus"] != "rejected":
        raise AssertionError("unsupported connector plan should be marked rejected")
    if plan["connectorPolicyChecks"]["unsupportedConnectors"] != ["web_search"]:
        raise AssertionError("unsupported connector plan should preserve registry status")


def check_unregistered_auto_connector() -> None:
    request = copy.deepcopy(load_json(DEFAULT_REQUEST))
    request["sourcePolicy"]["allowedConnectors"] = ["manual_upload"]
    decision = validate_request(request)
    if decision["decisionStatus"] != "rejected":
        raise AssertionError("unregistered auto connector should be rejected")
    if "connector_not_registered" not in decision["reasonCodes"]:
        raise AssertionError("unregistered auto connector should identify registry miss")
    path = write_temp_request(request)
    try:
        plan = build_plan(path)
    finally:
        path.unlink()
    if plan["connectorPolicyChecks"]["unregisteredConnectors"] != ["manual_upload"]:
        raise AssertionError("unregistered connector plan should preserve registry miss")
    if plan["connectorPolicyChecks"]["allRequestedConnectorsRegistered"] is not False:
        raise AssertionError("unregistered connector plan should fail registry completeness")


def check_resolution_only_auto_connector() -> None:
    request = copy.deepcopy(load_json(DEFAULT_REQUEST))
    request["sourcePolicy"]["allowedConnectors"] = ["declared_operations_fixture"]
    decision = validate_request(request)
    if decision["decisionStatus"] != "rejected":
        raise AssertionError("resolution-only auto connector should be rejected")
    if "resolution_only_connector" not in decision["reasonCodes"]:
        raise AssertionError("resolution-only connector should identify forecast-time misuse")
    path = write_temp_request(request)
    try:
        plan = build_plan(path)
    finally:
        path.unlink()
    if plan["connectorPolicyChecks"]["resolutionOnlyConnectors"] != ["declared_operations_fixture"]:
        raise AssertionError("resolution-only connector plan should preserve connector role")
    if any(intent["connector"] == "declared_operations_fixture" for intent in plan["searchIntents"]):
        raise AssertionError("resolution-only connector must not become a forecast-time search intent")


def check_stale_policy_schema_guard() -> None:
    request = copy.deepcopy(load_json(DEFAULT_REQUEST))
    request["sourcePolicy"]["freshness"]["maxSourceAgeHours"] = 0
    path = write_temp_request(request)
    try:
        _schema, errors = validate_file(path, SPEC / "forecast-request.schema.json")
    finally:
        path.unlink()
    if not errors:
        raise AssertionError("stale source policy should fail schema validation")


def check_provided_mode_network_guard() -> None:
    request = copy.deepcopy(load_json(DEFAULT_REQUEST))
    request["dataMode"] = "provided"
    request["sourcePolicy"]["allowedConnectors"] = ["committed_fixture"]
    request["sourcePolicy"]["allowNetworkAccess"] = True
    request["sourcePolicy"]["maxNetworkCalls"] = 1
    decision = validate_request(request)
    if "provided_data_network_disallowed" not in decision["reasonCodes"]:
        raise AssertionError("provided data mode should reject network access")


def main() -> None:
    check_default_plan()
    check_unsupported_auto_connector()
    check_unregistered_auto_connector()
    check_resolution_only_auto_connector()
    check_stale_policy_schema_guard()
    check_provided_mode_network_guard()
    print("checked auto-evidence planning surface")


if __name__ == "__main__":
    main()
