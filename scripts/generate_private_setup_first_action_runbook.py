#!/usr/bin/env python3
"""Generate or check the private setup first-action runbook."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_first_actions import action_path, build_actions
from generate_private_setup_requests import render_json
from ope_fixtures import check_generated, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-actions"
RUNBOOK_PATH = GENERATED / "ope-private-setup-first-action-runbook.generated.json"
SCHEMA = SPEC / "private-setup-first-action-runbook.schema.json"
GENERATED_AT = "2026-06-07T10:20:00Z"
FORECAST_SCORE_BLOCKS = ["forecast_artifact", "forecast_card", "scoring_report", "credential_record", "live_fetch_result"]
NO_COMMAND = "none"


class PrivateSetupActionRunbookError(Exception):
    pass


def next_action_for(action: dict[str, Any]) -> str:
    status = action["actionStatus"]
    if status == "ready_to_run_checked_command":
        return "run_source_builder"
    if status == "confirmation_required":
        return "ask_mapping_confirmation"
    if status == "fixture_ready":
        return "run_fixture_evidence"
    if status == "runtime_not_implemented":
        return "wait_for_runtime"
    if status == "source_replacement_required":
        return "replace_source"
    if status == "rejected_unsafe_source":
        return "stop_unsafe_source"
    if status == "bad_request":
        return "fix_bad_request"
    raise PrivateSetupActionRunbookError(f"unsupported action status: {status}")


def expected_output_for(action: dict[str, Any]) -> str:
    if action["sourceKind"] == "local_file":
        return "source_manifest_build"
    if action["sourceKind"] == "manual_mapping":
        return "source_intake_handoff"
    if action["sourceKind"] == "auto_evidence_connector":
        return "evidence_source_set"
    return "none"


def source_intake_after_action(action: dict[str, Any]) -> bool:
    return action["sourceKind"] in {"local_file", "manual_mapping"}


def stop_condition_for(action: dict[str, Any]) -> str:
    source_kind = action["sourceKind"]
    status = action["actionStatus"]
    if source_kind == "local_file":
        return "Stop before source intake until source-builder drafts are reviewed and handed off."
    if source_kind == "manual_mapping":
        return "Stop until the caller confirms source roles, field mappings, and aliases."
    if source_kind == "auto_evidence_connector":
        return "Stop before treating fixture evidence as production live gathering."
    if status == "runtime_not_implemented":
        return "Stop until a checked runtime exists for this source kind."
    if status == "source_replacement_required":
        return "Stop until the caller replaces the source kind with a declared adapter."
    if status == "rejected_unsafe_source":
        return "Stop permanently for this source input; require a safe replacement."
    return "Stop until the request is corrected."


def instruction_for(action: dict[str, Any]) -> str:
    source_kind = action["sourceKind"]
    status = action["actionStatus"]
    if source_kind == "local_file":
        return "Run source-builder only for caller-approved local files, then route drafts through source-handoff."
    if source_kind == "manual_mapping":
        return "Ask for caller confirmation before running the source-handoff confirmation command."
    if source_kind == "auto_evidence_connector":
        return "Run fixture evidence gathering only for an accepted source policy; keep live fetching out of normal checks."
    if status == "runtime_not_implemented":
        return "Tell the caller this source kind needs a future checked runtime before OPE can inspect it."
    if status == "source_replacement_required":
        return "Ask the caller to replace the source with a declared source kind before retrying setup."
    if status == "rejected_unsafe_source":
        return "Reject the unsafe source and do not pass it to source intake or forecast execution."
    return "Fix the setup request before any source or forecast step."


def blocked_outputs_for(action: dict[str, Any]) -> list[str]:
    source_kind = action["sourceKind"]
    if source_kind == "local_file":
        return FORECAST_SCORE_BLOCKS
    if source_kind == "manual_mapping":
        return ["source_manifest"] + FORECAST_SCORE_BLOCKS
    if source_kind == "auto_evidence_connector":
        return ["source_manifest", "field_mapping"] + FORECAST_SCORE_BLOCKS
    return ["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_BLOCKS


def case_playbook(index: int, action: dict[str, Any]) -> dict[str, Any]:
    return {
        "runbookRowId": f"privatesetupactionrunbookrow-{index:03d}",
        "sourceKind": action["sourceKind"],
        "actionStatus": action["actionStatus"],
        "boundPrivateSetupFirstActionId": action["privateSetupFirstActionId"],
        "boundPrivateSetupRequestId": action["requestBinding"]["privateSetupRequestId"],
        "actionFixturePath": str(action_path(action["sourceKind"]).relative_to(ROOT)),
        "allowedEntrypoint": action["allowedEntrypoint"],
        "commandToRun": action["commandToRun"],
        "nextActionLabel": next_action_for(action),
        "expectedOutputClass": expected_output_for(action),
        "requiresCallerConfirmation": action["actionStatus"] == "confirmation_required",
        "mayEnterSourceIntakeAfterRequiredAction": source_intake_after_action(action),
        "forecastExecutionAllowed": False,
        "scoringAllowed": False,
        "stopCondition": stop_condition_for(action),
        "blockedOutputs": blocked_outputs_for(action),
        "agentInstruction": instruction_for(action),
    }


def bad_request_playbooks() -> list[dict[str, Any]]:
    blocked = ["source_manifest", "field_mapping", "source_intake_report"] + FORECAST_SCORE_BLOCKS
    return [
        {
            "runbookRowId": "privatesetupactionbadrequestrow-001",
            "errorCode": "unknown_source_kind",
            "actionStatus": "bad_request",
            "sourceKindPattern": "not_declared_in_private_source_adapter_capabilities",
            "nextActionLabel": "replace_source",
            "allowedEntrypoint": "no_current_entrypoint",
            "commandToRun": NO_COMMAND,
            "expectedOutputClass": "none",
            "mayEnterSourceIntakeAfterRequiredAction": False,
            "forecastExecutionAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Stop until the caller replaces the source kind with a declared adapter.",
            "blockedOutputs": blocked,
            "agentInstruction": "Do not infer a connector for unknown source kinds; ask for a declared source replacement.",
        },
        {
            "runbookRowId": "privatesetupactionbadrequestrow-002",
            "errorCode": "missing_approval",
            "actionStatus": "bad_request",
            "sourceKindPattern": "approval_or_credential_policy_not_confirmed",
            "nextActionLabel": "fix_bad_request",
            "allowedEntrypoint": "no_current_entrypoint",
            "commandToRun": NO_COMMAND,
            "expectedOutputClass": "none",
            "mayEnterSourceIntakeAfterRequiredAction": False,
            "forecastExecutionAllowed": False,
            "scoringAllowed": False,
            "stopCondition": "Stop until caller approval and source policy are explicit and confirmed.",
            "blockedOutputs": blocked,
            "agentInstruction": "Ask for explicit approval; never put credentials or private source details into artifacts.",
        },
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privatesetupactionrunbookguard-001",
            "name": "first_action_binding",
            "rule": "Every case playbook must bind one generated private setup first-action fixture.",
            "checkedBy": ["scripts/check_private_setup_first_action_runbook.py"],
        },
        {
            "guardId": "privatesetupactionrunbookguard-002",
            "name": "non_execution",
            "rule": "The runbook may name commands but must not execute source-builder, source-handoff, fixture gathering, forecasting, or scoring.",
            "checkedBy": ["scripts/check_private_setup_first_action_runbook.py"],
        },
        {
            "guardId": "privatesetupactionrunbookguard-003",
            "name": "blocked_sources_do_not_enter_intake",
            "rule": "Planned runtimes, unknown sources, unsafe sources, and missing approvals must not enter source intake.",
            "checkedBy": ["scripts/check_private_setup_first_action_runbook.py"],
        },
        {
            "guardId": "privatesetupactionrunbookguard-004",
            "name": "forecast_and_scoring_blocked",
            "rule": "First-action runbook rows must not allow forecast execution or scoring.",
            "checkedBy": ["scripts/check_private_setup_first_action_runbook.py"],
        },
        {
            "guardId": "privatesetupactionrunbookguard-005",
            "name": "bad_request_sanitized",
            "rule": "Unknown source kinds and missing approvals must resolve to sanitized caller actions with no command.",
            "checkedBy": ["scripts/check_private_setup_first_action_runbook.py"],
        },
    ]


def build_runbook() -> dict[str, Any]:
    actions = build_actions()
    playbooks = [case_playbook(index, action) for index, action in enumerate(actions, start=1)]
    status_coverage = sorted({item["actionStatus"] for item in playbooks} | {"bad_request"})
    runbook = {
        "privateSetupFirstActionRunbookId": "privatesetupactionrunbook-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "runbook_guidance_only",
        "entrypoints": {
            "requestSetCommand": "python3 scripts/ope.py private-setup-requests",
            "firstActionsCommand": "python3 scripts/ope.py private-setup-actions",
            "singleActionCommand": "python3 scripts/ope.py private-setup-action --request-id privatesetuprequest-001",
            "runbookCommand": "python3 scripts/ope.py private-setup-action-runbook",
            "runbookSchema": "spec/private-setup-first-action-runbook.schema.json",
        },
        "statusCoverage": status_coverage,
        "casePlaybooks": playbooks,
        "badRequestPlaybooks": bad_request_playbooks(),
        "executionBoundary": {
            "runbookDoesNotExecute": True,
            "normalChecksOffline": True,
            "readsPrivateData": False,
            "runsSuggestedCommand": False,
            "createsSourceManifests": False,
            "createsFieldMappings": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
        },
        "guards": guards(),
        "warnings": [
            "This runbook is guidance over first-action results; it does not execute the named commands.",
            "Private setup source intake remains gated by caller approval, source manifests, field mappings, and method decisions.",
            "Forecast artifacts and scoring records require later explicit forecast execution, resolution, and scoring.",
            "Planned private source runtimes remain unimplemented.",
        ],
    }
    validate_runbook(runbook)
    return runbook


def validate_runbook(runbook: dict[str, Any]) -> None:
    errors = validate_record(runbook, SCHEMA)
    if errors:
        raise PrivateSetupActionRunbookError(f"private setup first-action runbook schema validation failed: {errors[0]}")
    actions = {action["privateSetupFirstActionId"]: action for action in build_actions()}
    rows = runbook["casePlaybooks"]
    if len(rows) != len(actions):
        raise PrivateSetupActionRunbookError("runbook should cover every generated first-action fixture")
    for row in rows:
        action = actions.get(row["boundPrivateSetupFirstActionId"])
        if action is None:
            raise PrivateSetupActionRunbookError(f"unknown action binding: {row['boundPrivateSetupFirstActionId']}")
        if row["sourceKind"] != action["sourceKind"]:
            raise PrivateSetupActionRunbookError(f"{row['sourceKind']} source binding drift")
        if row["commandToRun"] != action["commandToRun"]:
            raise PrivateSetupActionRunbookError(f"{row['sourceKind']} command drift")
        if row["forecastExecutionAllowed"] or row["scoringAllowed"]:
            raise PrivateSetupActionRunbookError(f"{row['sourceKind']} must not allow forecast execution or scoring")
    for row in rows + runbook["badRequestPlaybooks"]:
        if row["nextActionLabel"] in {"wait_for_runtime", "replace_source", "stop_unsafe_source", "fix_bad_request"}:
            if row["mayEnterSourceIntakeAfterRequiredAction"]:
                raise PrivateSetupActionRunbookError(f"{row['runbookRowId']} must not enter source intake")
        for blocked in FORECAST_SCORE_BLOCKS:
            if blocked not in row["blockedOutputs"]:
                raise PrivateSetupActionRunbookError(f"{row['runbookRowId']} should block {blocked}")
    boundary = runbook["executionBoundary"]
    if boundary["runbookDoesNotExecute"] is not True or boundary["runsSuggestedCommand"] is not False:
        raise PrivateSetupActionRunbookError("runbook must stay non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "storesCredentials",
    ]:
        if boundary[key] is not False:
            raise PrivateSetupActionRunbookError(f"{key} must remain false")


def write_runbook(runbook: dict[str, Any]) -> None:
    write_generated(RUNBOOK_PATH, runbook, label="private setup first-action runbook", regen="python3 scripts/generate_private_setup_first_action_runbook.py --write")


def check_runbook(runbook: dict[str, Any]) -> None:
    check_generated(RUNBOOK_PATH, runbook, label="private setup first-action runbook", regen="python3 scripts/generate_private_setup_first_action_runbook.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup first-action runbook drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup first-action runbook")
    args = parser.parse_args()
    try:
        runbook = build_runbook()
    except PrivateSetupActionRunbookError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_runbook(runbook)
    elif args.check:
        check_runbook(runbook)
    else:
        sys.stdout.write(render_json(runbook))


if __name__ == "__main__":
    main()
