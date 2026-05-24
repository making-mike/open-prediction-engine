#!/usr/bin/env python3
"""Generate, check, or print private setup agent guidance bundles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_first_action_runbook import build_runbook
from generate_private_setup_first_actions import build_actions
from generate_private_setup_requests import build_request_set, render_json
from ope_schema import SPEC, validate_record
from private_setup_action_dispatcher import action_from_request_row


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-agent-bundles"
SCHEMA = SPEC / "private-setup-agent-bundle.schema.json"
GENERATED_AT = "2026-06-07T10:40:00Z"
FORECAST_SCORE_BLOCKS = ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]
NO_COMMAND = "none"
BAD_REQUEST_CASES = ["unknown_source_kind", "missing_approval"]


class PrivateSetupAgentBundleError(Exception):
    pass


def bundle_path(slug: str) -> Path:
    return GENERATED / f"ope-private-setup-agent-bundle-{slug}.generated.json"


def slug_for_source(source_kind: str) -> str:
    return source_kind.replace("_", "-")


def request_summary(request_set: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    forecast_intent = row["forecastIntent"]
    return {
        "privateSetupRequestSetId": request_set["privateSetupRequestSetId"],
        "privateSetupRequestId": row["privateSetupRequestId"],
        "requestRowId": row.get("requestRowId"),
        "setupMode": row["setupMode"],
        "selectedSourceKind": row["selectedSourceKind"],
        "forecastQuestionText": forecast_intent["questionText"],
        "outputType": forecast_intent["outputType"],
        "sourcePolicy": row["sourcePolicy"],
    }


def action_summary(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "privateSetupFirstActionId": action["privateSetupFirstActionId"],
        "actionStatus": action["actionStatus"],
        "routeDecision": action["routeDecision"],
        "allowedEntrypoint": action["allowedEntrypoint"],
        "commandToRun": action["commandToRun"],
        "requiredCallerAction": action["requiredCallerAction"],
        "errorCode": action["error"]["code"],
        "exitCode": action["exitCode"],
    }


def runbook_guidance(runbook: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    return {
        "privateSetupFirstActionRunbookId": runbook["privateSetupFirstActionRunbookId"],
        "runbookRowId": row["runbookRowId"],
        "nextActionLabel": row["nextActionLabel"],
        "expectedOutputClass": row["expectedOutputClass"],
        "requiresCallerConfirmation": row.get("requiresCallerConfirmation", False),
        "mayEnterSourceIntakeAfterRequiredAction": row["mayEnterSourceIntakeAfterRequiredAction"],
        "forecastExecutionAllowed": row["forecastExecutionAllowed"],
        "scoringAllowed": row["scoringAllowed"],
        "blockedOutputs": row["blockedOutputs"],
        "stopCondition": row["stopCondition"],
        "agentInstruction": row["agentInstruction"],
    }


def claim_boundary(row: dict[str, Any]) -> dict[str, Any]:
    reason_codes = [
        "setup_guidance_only",
        "forecast_requires_later_gates",
        "quality_claim_requires_resolved_samples",
    ]
    if row["nextActionLabel"] in {"wait_for_runtime", "replace_source", "stop_unsafe_source", "fix_bad_request"}:
        reason_codes.append("source_not_eligible_for_intake")
    if row.get("requiresCallerConfirmation", False):
        reason_codes.append("caller_confirmation_required")
    return {
        "bundleDoesNotPredict": True,
        "qualityClaimAllowed": False,
        "forecastExecutionAllowed": False,
        "scoringAllowed": False,
        "reasonCodes": reason_codes,
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "bundleDoesNotExecute": True,
        "normalChecksOffline": True,
        "readsPrivateData": False,
        "runsSuggestedCommand": False,
        "createsSourceManifests": False,
        "createsFieldMappings": False,
        "createsForecastArtifacts": False,
        "createsScoringRecords": False,
        "storesCredentials": False,
    }


def bundle_from_parts(
    *,
    bundle_id: str,
    bundle_kind: str,
    request_set: dict[str, Any],
    request_row: dict[str, Any],
    action: dict[str, Any],
    runbook: dict[str, Any],
    runbook_row: dict[str, Any],
) -> dict[str, Any]:
    bundle = {
        "privateSetupAgentBundleId": bundle_id,
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "bundle_guidance_only",
        "bundleKind": bundle_kind,
        "sourceKind": request_row["selectedSourceKind"],
        "requestSummary": request_summary(request_set, request_row),
        "actionSummary": action_summary(action),
        "runbookGuidance": runbook_guidance(runbook, runbook_row),
        "claimBoundary": claim_boundary(runbook_row),
        "executionBoundary": execution_boundary(),
        "warnings": [
            "This bundle joins setup guidance records; it does not execute the suggested command.",
            "Source intake, forecast execution, resolution, and scoring remain separate explicit steps.",
            "The bundle does not predict, score, fetch live data, or store credentials.",
        ],
    }
    validate_bundle(bundle)
    return bundle


def known_bundles() -> list[dict[str, Any]]:
    request_set = build_request_set()
    request_rows = {row["selectedSourceKind"]: row for row in request_set["requestRows"]}
    actions = {row["sourceKind"]: row for row in build_actions()}
    runbook = build_runbook()
    runbook_rows = {row["sourceKind"]: row for row in runbook["casePlaybooks"]}
    bundles = []
    for index, source_kind in enumerate(request_rows, start=1):
        bundles.append(
            bundle_from_parts(
                bundle_id=f"privatesetupagentbundle-{index:03d}",
                bundle_kind="known_request",
                request_set=request_set,
                request_row=request_rows[source_kind],
                action=actions[source_kind],
                runbook=runbook,
                runbook_row=runbook_rows[source_kind],
            )
        )
    return bundles


def bad_request_rows(request_set: dict[str, Any]) -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    unknown = {
        "requestRowId": "privatesetuprequestrow-990",
        "privateSetupRequestId": "privatesetuprequest-990",
        "setupMode": "unknown",
        "forecastIntent": {
            "questionText": "Estimate a future operational probability from caller-approved sources.",
            "outputType": "binary",
            "horizonLabel": "caller_declared",
            "resolutionNeeded": True,
        },
        "sourcePolicy": {
            "dataMode": "provided",
            "allowedSourceKinds": ["spreadsheet_macro"],
            "approvalStatus": "confirmed",
            "allowLiveFetch": False,
            "allowCredentialUse": False,
        },
        "selectedSourceKind": "spreadsheet_macro",
        "routeDecision": "reject_bad_request",
        "allowedEntrypoint": "no_current_entrypoint",
        "commandToRun": NO_COMMAND,
        "requiredCallerAction": "replace the source kind with a declared adapter",
    }
    missing_approval = {
        "requestRowId": "privatesetuprequestrow-991",
        "privateSetupRequestId": "privatesetuprequest-991",
        "setupMode": "new_setup",
        "forecastIntent": {
            "questionText": "Estimate a future operational probability from caller-approved private api sources.",
            "outputType": "binary",
            "horizonLabel": "caller_declared",
            "resolutionNeeded": True,
        },
        "sourcePolicy": {
            "dataMode": "provided",
            "allowedSourceKinds": ["private_api"],
            "approvalStatus": "requested",
            "allowLiveFetch": False,
            "allowCredentialUse": True,
        },
        "selectedSourceKind": "private_api",
        "routeDecision": "wait_for_runtime",
        "boundBridgeRowId": "privateadapterbridge-005",
        "boundOutcomeRowId": "privateadapteroutcomerow-005",
        "allowedEntrypoint": "no_current_entrypoint",
        "commandToRun": NO_COMMAND,
        "requiredCallerAction": "confirm caller approval and retry the private setup request",
    }
    return [
        ("unknown_source_kind", unknown, action_from_request_row(unknown, request_set, sequence=990)),
        ("missing_approval", missing_approval, action_from_request_row(missing_approval, request_set, sequence=991)),
    ]


def bad_request_bundles() -> list[dict[str, Any]]:
    request_set = build_request_set()
    runbook = build_runbook()
    bad_rows = {row["errorCode"]: row for row in runbook["badRequestPlaybooks"]}
    bundles = []
    for index, (case, request_row, action) in enumerate(bad_request_rows(request_set), start=9):
        bundles.append(
            bundle_from_parts(
                bundle_id=f"privatesetupagentbundle-{index:03d}",
                bundle_kind="bad_request_example",
                request_set=request_set,
                request_row=request_row,
                action=action,
                runbook=runbook,
                runbook_row=bad_rows[case],
            )
        )
    return bundles


def build_bundles() -> list[dict[str, Any]]:
    return known_bundles() + bad_request_bundles()


def bundle_by_request_id(request_id: str) -> dict[str, Any]:
    request_set = build_request_set()
    actions = {row["sourceKind"]: row for row in build_actions()}
    runbook = build_runbook()
    runbook_rows = {row["sourceKind"]: row for row in runbook["casePlaybooks"]}
    for index, request_row in enumerate(request_set["requestRows"], start=1):
        if request_row["privateSetupRequestId"] == request_id:
            source_kind = request_row["selectedSourceKind"]
            return bundle_from_parts(
                bundle_id=f"privatesetupagentbundle-{index:03d}",
                bundle_kind="known_request",
                request_set=request_set,
                request_row=request_row,
                action=actions[source_kind],
                runbook=runbook,
                runbook_row=runbook_rows[source_kind],
            )
    bad_rows = {row["errorCode"]: row for row in runbook["badRequestPlaybooks"]}
    for index, (case, request_row, action) in enumerate(bad_request_rows(request_set), start=9):
        if request_row["privateSetupRequestId"] == request_id:
            return bundle_from_parts(
                bundle_id=f"privatesetupagentbundle-{index:03d}",
                bundle_kind="bad_request_example",
                request_set=request_set,
                request_row=request_row,
                action=action,
                runbook=runbook,
                runbook_row=bad_rows[case],
            )
    raise PrivateSetupAgentBundleError(f"unknown private setup request id: {request_id}")


def bundle_by_case(case: str) -> dict[str, Any]:
    if case not in BAD_REQUEST_CASES:
        raise PrivateSetupAgentBundleError(f"unknown private setup bundle case: {case}")
    request_set = build_request_set()
    runbook = build_runbook()
    bad_rows = {row["errorCode"]: row for row in runbook["badRequestPlaybooks"]}
    for index, (row_case, request_row, action) in enumerate(bad_request_rows(request_set), start=9):
        if row_case == case:
            return bundle_from_parts(
                bundle_id=f"privatesetupagentbundle-{index:03d}",
                bundle_kind="bad_request_example",
                request_set=request_set,
                request_row=request_row,
                action=action,
                runbook=runbook,
                runbook_row=bad_rows[case],
            )
    raise PrivateSetupAgentBundleError(f"missing private setup bundle case: {case}")


def validate_bundle(bundle: dict[str, Any]) -> None:
    errors = validate_record(bundle, SCHEMA)
    if errors:
        raise PrivateSetupAgentBundleError(f"private setup agent bundle schema validation failed: {errors[0]}")
    guidance = bundle["runbookGuidance"]
    claim = bundle["claimBoundary"]
    boundary = bundle["executionBoundary"]
    if claim["bundleDoesNotPredict"] is not True or claim["qualityClaimAllowed"] is not False:
        raise PrivateSetupAgentBundleError("bundle claim boundary must block prediction and quality claims")
    if guidance["forecastExecutionAllowed"] or guidance["scoringAllowed"]:
        raise PrivateSetupAgentBundleError("bundle guidance must not allow forecast execution or scoring")
    if claim["forecastExecutionAllowed"] or claim["scoringAllowed"]:
        raise PrivateSetupAgentBundleError("bundle claim boundary must not allow forecast execution or scoring")
    if boundary["bundleDoesNotExecute"] is not True or boundary["runsSuggestedCommand"] is not False:
        raise PrivateSetupAgentBundleError("bundle must stay non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        if boundary[key] is not False:
            raise PrivateSetupAgentBundleError(f"{key} must remain false")
    for blocked in FORECAST_SCORE_BLOCKS:
        if blocked not in guidance["blockedOutputs"]:
            raise PrivateSetupAgentBundleError(f"bundle should block {blocked}")


def write_bundles(bundles: list[dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for bundle in bundles:
        if bundle["bundleKind"] == "bad_request_example":
            slug = bundle["actionSummary"]["errorCode"].replace("_", "-")
        else:
            slug = slug_for_source(bundle["sourceKind"])
        bundle_path(slug).write_text(render_json(bundle), encoding="utf-8")
    print(f"generated {len(bundles)} private setup agent bundles")


def check_bundles(bundles: list[dict[str, Any]]) -> None:
    for bundle in bundles:
        if bundle["bundleKind"] == "bad_request_example":
            slug = bundle["actionSummary"]["errorCode"].replace("_", "-")
        else:
            slug = slug_for_source(bundle["sourceKind"])
        path = bundle_path(slug)
        expected = render_json(bundle)
        if not path.exists():
            print(f"missing private setup agent bundle: {path}", file=sys.stderr)
            print("run `python3 scripts/generate_private_setup_agent_bundles.py --write`", file=sys.stderr)
            raise SystemExit(1)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"private setup agent bundle drift: {path}", file=sys.stderr)
            print("run `python3 scripts/generate_private_setup_agent_bundles.py --write`", file=sys.stderr)
            raise SystemExit(1)
    print(f"checked {len(bundles)} private setup agent bundles")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", help="print one bundle by private setup request id")
    parser.add_argument("--case", choices=BAD_REQUEST_CASES, help="print one bad-request example bundle")
    parser.add_argument("--check", action="store_true", help="check generated private setup bundle drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup bundles")
    args = parser.parse_args()
    try:
        if args.request_id and args.case:
            raise PrivateSetupAgentBundleError("provide either --request-id or --case, not both")
        if args.request_id:
            sys.stdout.write(render_json(bundle_by_request_id(args.request_id)))
            return
        if args.case:
            sys.stdout.write(render_json(bundle_by_case(args.case)))
            return
        bundles = build_bundles()
    except PrivateSetupAgentBundleError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_bundles(bundles)
    elif args.check:
        check_bundles(bundles)
    else:
        sys.stdout.write(render_json({"count": len(bundles), "bundles": bundles}))


if __name__ == "__main__":
    main()
