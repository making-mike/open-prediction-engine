#!/usr/bin/env python3
"""Check private setup agent bundle bindings and boundaries."""

from __future__ import annotations

from generate_private_setup_agent_bundles import build_bundles, bundle_by_case, bundle_by_request_id
from generate_private_setup_first_action_runbook import build_runbook
from generate_private_setup_first_actions import build_actions
from generate_private_setup_requests import build_request_set


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    request_set = build_request_set()
    request_rows = {row["selectedSourceKind"]: row for row in request_set["requestRows"]}
    actions = {row["sourceKind"]: row for row in build_actions()}
    runbook = build_runbook()
    runbook_rows = {row["sourceKind"]: row for row in runbook["casePlaybooks"]}
    bad_rows = {row["errorCode"]: row for row in runbook["badRequestPlaybooks"]}
    bundles = build_bundles()
    known = {row["sourceKind"]: row for row in bundles if row["bundleKind"] == "known_request"}
    bad = {row["actionSummary"]["errorCode"]: row for row in bundles if row["bundleKind"] == "bad_request_example"}

    require(len(bundles) == 10, "bundles should cover eight known requests and two bad-request examples")
    require(set(known) == set(request_rows), "known bundles should cover every private setup request row")
    require({"unknown_source_kind", "missing_approval"} <= set(bad), "bundles should cover bad-request examples")

    for source_kind, bundle in known.items():
        request = request_rows[source_kind]
        action = actions[source_kind]
        guidance = runbook_rows[source_kind]
        require(bundle["scope"] == "domain_agnostic", f"{source_kind} should stay domain agnostic")
        require(bundle["runtimeStatus"] == "bundle_guidance_only", f"{source_kind} should be guidance-only")
        require(
            bundle["requestSummary"]["privateSetupRequestId"] == request["privateSetupRequestId"],
            f"{source_kind} request id binding drift",
        )
        require(
            bundle["requestSummary"]["requestRowId"] == request["requestRowId"],
            f"{source_kind} request row binding drift",
        )
        require(
            bundle["actionSummary"]["privateSetupFirstActionId"] == action["privateSetupFirstActionId"],
            f"{source_kind} first-action binding drift",
        )
        require(bundle["actionSummary"]["commandToRun"] == action["commandToRun"], f"{source_kind} command drift")
        require(
            bundle["runbookGuidance"]["runbookRowId"] == guidance["runbookRowId"],
            f"{source_kind} runbook row binding drift",
        )
        require(
            bundle["runbookGuidance"]["nextActionLabel"] == guidance["nextActionLabel"],
            f"{source_kind} next action drift",
        )
        require(
            bundle["runbookGuidance"]["expectedOutputClass"] == guidance["expectedOutputClass"],
            f"{source_kind} expected output drift",
        )
        require(
            bundle["runbookGuidance"]["forecastExecutionAllowed"] is False,
            f"{source_kind} should not allow forecast execution",
        )
        require(bundle["runbookGuidance"]["scoringAllowed"] is False, f"{source_kind} should not allow scoring")

    require(known["local_file"]["runbookGuidance"]["nextActionLabel"] == "run_source_builder", "local file next action drift")
    require(
        known["local_file"]["runbookGuidance"]["expectedOutputClass"] == "source_manifest_build",
        "local file expected output drift",
    )
    require(
        known["manual_mapping"]["runbookGuidance"]["requiresCallerConfirmation"] is True,
        "manual mapping should require confirmation",
    )
    require(
        known["auto_evidence_connector"]["runbookGuidance"]["nextActionLabel"] == "run_fixture_evidence",
        "auto evidence next action drift",
    )
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        guidance = known[source_kind]["runbookGuidance"]
        require(guidance["nextActionLabel"] == "wait_for_runtime", f"{source_kind} should wait for runtime")
        require(guidance["mayEnterSourceIntakeAfterRequiredAction"] is False, f"{source_kind} should not enter intake")
        require(known[source_kind]["actionSummary"]["commandToRun"] == "none", f"{source_kind} should expose no command")
    require(known["unregistered_source"]["runbookGuidance"]["nextActionLabel"] == "replace_source", "unregistered next action drift")
    require(
        known["unsafe_source"]["runbookGuidance"]["nextActionLabel"] == "stop_unsafe_source",
        "unsafe source next action drift",
    )

    for error_code, bundle in bad.items():
        guidance = bad_rows[error_code]
        require(bundle["bundleKind"] == "bad_request_example", f"{error_code} should be a bad request example")
        require(bundle["actionSummary"]["actionStatus"] == "bad_request", f"{error_code} action should be bad_request")
        require(bundle["actionSummary"]["errorCode"] == error_code, f"{error_code} error code drift")
        require(bundle["actionSummary"]["commandToRun"] == "none", f"{error_code} should expose no command")
        require(
            bundle["runbookGuidance"]["runbookRowId"] == guidance["runbookRowId"],
            f"{error_code} bad-request row binding drift",
        )
        require(
            bundle["runbookGuidance"]["mayEnterSourceIntakeAfterRequiredAction"] is False,
            f"{error_code} should not enter intake",
        )
        require(bundle["runbookGuidance"]["forecastExecutionAllowed"] is False, f"{error_code} should not forecast")
        require(bundle["runbookGuidance"]["scoringAllowed"] is False, f"{error_code} should not score")

    for bundle in bundles:
        claim = bundle["claimBoundary"]
        boundary = bundle["executionBoundary"]
        require(claim["bundleDoesNotPredict"] is True, "bundle should not predict")
        require(claim["qualityClaimAllowed"] is False, "bundle should not allow quality claims")
        require(claim["forecastExecutionAllowed"] is False, "bundle claim boundary should not forecast")
        require(claim["scoringAllowed"] is False, "bundle claim boundary should not score")
        require(boundary["bundleDoesNotExecute"] is True, "bundle should not execute")
        require(boundary["runsSuggestedCommand"] is False, "bundle should not run commands")
        for key in [
            "readsPrivateData",
            "createsSourceManifests",
            "createsFieldMappings",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "storesCredentials",
        ]:
            require(boundary[key] is False, f"{key} should remain false")
        for blocked in ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]:
            require(blocked in bundle["runbookGuidance"]["blockedOutputs"], f"bundle should block {blocked}")

    require(
        bundle_by_request_id("privatesetuprequest-001")["sourceKind"] == "local_file",
        "bundle lookup by request id should return local file",
    )
    require(
        bundle_by_case("unknown_source_kind")["actionSummary"]["errorCode"] == "unknown_source_kind",
        "bundle lookup by bad-request case should return unknown source example",
    )

    print("checked private setup agent bundles")


if __name__ == "__main__":
    main()
