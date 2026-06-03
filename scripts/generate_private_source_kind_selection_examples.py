#!/usr/bin/env python3
"""Generate or check private source-kind selection examples."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from build_agent_adapter_fixtures import build_private_source_adapter_guidance_envelope
from generate_private_setup_adapter_chain_runbook import build_runbook
from generate_private_setup_first_actions import build_actions
from generate_private_setup_requests import build_request_set
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-source-kind-selection"
EXAMPLES_PATH = GENERATED / "ope-private-source-kind-selection-examples.generated.json"
SCHEMA = SPEC / "private-source-kind-selection-examples.schema.json"
GENERATED_AT = "2026-06-07T11:35:00Z"
NO_COMMAND = "none"
SOURCE_KIND_ORDER = [
    "local_file",
    "manual_mapping",
    "manual_upload",
    "auto_evidence_connector",
    "private_api",
    "private_database",
    "unregistered_source",
    "unsafe_source",
]


class PrivateSourceKindSelectionExamplesError(Exception):
    pass


def agent_call_command(operation: str, *args: str) -> str:
    return " ".join(["python3", "scripts/ope.py", "agent-call", "--operation", operation, *args])


def guidance_binding(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceKind": summary["sourceKind"],
        "outcomeClass": summary["outcomeClass"],
        "setupOutcomeClass": summary["setupOutcomeClass"],
        "allowedEntrypoint": summary["allowedEntrypoint"],
        "currentCommand": summary["currentCommand"],
        "agentNextAction": summary["agentNextAction"],
    }


def first_action_binding(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "privateSetupFirstActionId": action["privateSetupFirstActionId"],
        "privateSetupRequestId": action["requestBinding"]["privateSetupRequestId"],
        "actionStatus": action["actionStatus"],
        "routeDecision": action["routeDecision"],
        "allowedEntrypoint": action["allowedEntrypoint"],
        "commandToRun": action["commandToRun"],
    }


def runbook_lookups(runbook: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    steps = {item["operation"]: item for item in runbook["operationSequence"]}
    branches = {item["branchName"]: item for item in runbook["branchPlaybooks"]}
    return steps, branches


def chain_binding(
    source_kind: str,
    steps: dict[str, dict[str, Any]],
    branches: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if source_kind == "local_file":
        step = steps["private_setup_source_builder"]
        return {
            "applicability": "current_local_file_chain",
            "runbookStepId": step["runbookStepId"],
            "branchId": None,
            "nextOperationAfterPrerequisites": "private_setup_source_builder",
            "adapterCommandAfterPrerequisites": agent_call_command(
                "private_setup_source_builder",
                "--private-setup-request-id",
                "privatesetuprequest-001",
                "--source-builder-case",
                "local_draft",
            ),
        }
    if source_kind == "manual_mapping":
        step = steps["private_setup_source_handoff"]
        branch = branches["mapping_confirmation_required"]
        return {
            "applicability": "mapping_confirmation_branch",
            "runbookStepId": step["runbookStepId"],
            "branchId": branch["branchId"],
            "nextOperationAfterPrerequisites": "private_setup_source_handoff",
            "adapterCommandAfterPrerequisites": agent_call_command(
                "private_setup_source_handoff",
                "--private-setup-request-id",
                "privatesetuprequest-001",
                "--source-handoff-case",
                "confirmed_builder_draft",
            ),
        }
    if source_kind == "auto_evidence_connector":
        return {
            "applicability": "outside_current_adapter_chain",
            "runbookStepId": None,
            "branchId": None,
            "nextOperationAfterPrerequisites": None,
            "adapterCommandAfterPrerequisites": "python3 scripts/ope.py gather-evidence",
        }
    if source_kind in {"manual_upload", "private_api", "private_database"}:
        return {
            "applicability": "planned_runtime_blocked",
            "runbookStepId": None,
            "branchId": None,
            "nextOperationAfterPrerequisites": None,
            "adapterCommandAfterPrerequisites": NO_COMMAND,
        }
    if source_kind == "unregistered_source":
        return {
            "applicability": "source_replacement_stop",
            "runbookStepId": None,
            "branchId": None,
            "nextOperationAfterPrerequisites": None,
            "adapterCommandAfterPrerequisites": NO_COMMAND,
        }
    if source_kind == "unsafe_source":
        return {
            "applicability": "unsafe_source_stop",
            "runbookStepId": None,
            "branchId": None,
            "nextOperationAfterPrerequisites": None,
            "adapterCommandAfterPrerequisites": NO_COMMAND,
        }
    raise PrivateSourceKindSelectionExamplesError(f"unsupported source kind: {source_kind}")


def recommendation(source_kind: str, action: dict[str, Any]) -> dict[str, Any]:
    if source_kind == "local_file":
        return {
            "immediateAction": "call_source_builder_adapter",
            "requiresCallerConfirmation": False,
            "requiresFutureRuntime": False,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Call the source-builder adapter only for caller-approved CSV/JSON files, then continue through handoff and method gates.",
        }
    if source_kind == "manual_mapping":
        return {
            "immediateAction": "request_mapping_confirmation",
            "requiresCallerConfirmation": True,
            "requiresFutureRuntime": False,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Ask the caller to confirm proposed mappings before using source-handoff confirmation.",
        }
    if source_kind == "auto_evidence_connector":
        return {
            "immediateAction": "call_fixture_evidence",
            "requiresCallerConfirmation": False,
            "requiresFutureRuntime": False,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Use policy-bound fixture evidence only; do not treat it as production live evidence gathering.",
        }
    if source_kind in {"manual_upload", "private_api", "private_database"}:
        return {
            "immediateAction": "wait_for_runtime",
            "requiresCallerConfirmation": False,
            "requiresFutureRuntime": True,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Wait for an explicit checked runtime before asking OPE to ingest this source kind.",
        }
    if source_kind == "unregistered_source":
        return {
            "immediateAction": "replace_source",
            "requiresCallerConfirmation": False,
            "requiresFutureRuntime": False,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Replace the source kind with one declared in the private source adapter capability contract.",
        }
    if source_kind == "unsafe_source":
        return {
            "immediateAction": "reject_source",
            "requiresCallerConfirmation": False,
            "requiresFutureRuntime": False,
            "stopBeforeForecast": True,
            "forecastArtifactsAllowed": False,
            "scoringAllowed": False,
            "agentInstruction": "Reject unsafe source input and keep it out of setup, intake, forecasts, and scoring.",
        }
    raise PrivateSourceKindSelectionExamplesError(f"unsupported source kind: {source_kind}")


def selection_example(
    index: int,
    source_kind: str,
    summary: dict[str, Any],
    action: dict[str, Any],
    steps: dict[str, dict[str, Any]],
    branches: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "selectionExampleId": f"sourcekindselectionexample-{index:03d}",
        "sourceKind": source_kind,
        "guidanceBinding": guidance_binding(summary),
        "firstActionBinding": first_action_binding(action),
        "adapterChainBinding": chain_binding(source_kind, steps, branches),
        "recommendation": recommendation(source_kind, action),
    }


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "sourcekindselectionguard-001",
            "name": "guidance_binding",
            "rule": "Every selection example must bind one source-kind summary from the private source adapter guidance envelope.",
            "checkedBy": ["scripts/check_private_source_kind_selection_examples.py"],
        },
        {
            "guardId": "sourcekindselectionguard-002",
            "name": "first_action_binding",
            "rule": "Every selection example must bind the matching private setup first-action result.",
            "checkedBy": ["scripts/check_private_source_kind_selection_examples.py"],
        },
        {
            "guardId": "sourcekindselectionguard-003",
            "name": "adapter_chain_binding",
            "rule": "Examples must point to the adapter-chain runbook when the current local-file chain applies and mark other source kinds as outside or blocked.",
            "checkedBy": ["scripts/check_private_source_kind_selection_examples.py"],
        },
        {
            "guardId": "sourcekindselectionguard-004",
            "name": "non_generating_examples",
            "rule": "Selection examples must not execute commands, read private data, create manifests, forecasts, scores, credentials, live fetches, or hosted runtime surfaces.",
            "checkedBy": ["scripts/check_private_source_kind_selection_examples.py"],
        },
        {
            "guardId": "sourcekindselectionguard-005",
            "name": "planned_and_unsafe_stop_paths",
            "rule": "Planned runtimes, unsupported sources, and unsafe sources must remain stop or replacement guidance before any forecast path.",
            "checkedBy": ["scripts/check_private_source_kind_selection_examples.py"],
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "examplesDoNotExecute": True,
        "normalChecksOffline": True,
        "readsPrivateData": False,
        "runsCommands": False,
        "createsSourceManifests": False,
        "createsFieldMappings": False,
        "createsForecastArtifacts": False,
        "createsScoringRecords": False,
        "fetchesLiveData": False,
        "storesCredentials": False,
        "createsHostedRuntime": False,
    }


def build_examples() -> dict[str, Any]:
    guidance_envelope = build_private_source_adapter_guidance_envelope()
    guidance = guidance_envelope["payload"]
    request_set = build_request_set()
    actions = {item["sourceKind"]: item for item in build_actions()}
    runbook = build_runbook()
    steps, branches = runbook_lookups(runbook)
    summaries = {item["sourceKind"]: item for item in guidance["sourceKindSummary"]}

    examples = [
        selection_example(index, source_kind, summaries[source_kind], actions[source_kind], steps, branches)
        for index, source_kind in enumerate(SOURCE_KIND_ORDER, start=1)
    ]
    record = {
        "privateSourceKindSelectionExamplesId": "privatesourcekindselectionexamples-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "selection_examples_only",
        "bindings": {
            "agentEnvelopeId": guidance_envelope["agentEnvelopeId"],
            "privateSourceAdapterGuidanceId": guidance["privateSourceAdapterGuidanceId"],
            "privateSourceAdapterCapabilityId": guidance["bindingSummary"]["privateSourceAdapterCapabilityId"],
            "privateSourceAdapterOutcomeMatrixId": guidance["bindingSummary"]["privateSourceAdapterOutcomeMatrixId"],
            "privateSourceAdapterIntakeBridgeId": guidance["bindingSummary"]["privateSourceAdapterIntakeBridgeId"],
            "privateSetupRequestSetId": request_set["privateSetupRequestSetId"],
            "privateSetupAdapterChainRunbookId": runbook["privateSetupAdapterChainRunbookId"],
        },
        "selectionExamples": examples,
        "executionBoundary": execution_boundary(),
        "guards": guards(),
        "warnings": [
            "These examples help agents choose a next setup path; they do not execute the chosen path.",
            "Forecast artifacts and scoring records still require source intake, method gates, explicit forecast execution, resolution, and scoring.",
            "Manual upload, private API, and private database source kinds remain planned-only until checked runtimes exist.",
            "Unsafe and unregistered sources must not enter setup, source intake, forecasts, or scoring.",
        ],
    }
    validate_examples(record, guidance_envelope, actions, runbook)
    return record


def validate_examples(
    record: dict[str, Any],
    guidance_envelope: dict[str, Any],
    actions: dict[str, dict[str, Any]],
    runbook: dict[str, Any],
) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PrivateSourceKindSelectionExamplesError(
            f"private source-kind selection examples schema validation failed: {errors[0]}"
        )
    bindings = record["bindings"]
    guidance = guidance_envelope["payload"]
    if bindings["agentEnvelopeId"] != guidance_envelope["agentEnvelopeId"]:
        raise PrivateSourceKindSelectionExamplesError("selection examples must bind guidance envelope")
    if bindings["privateSourceAdapterGuidanceId"] != guidance["privateSourceAdapterGuidanceId"]:
        raise PrivateSourceKindSelectionExamplesError("selection examples must bind guidance payload")
    if bindings["privateSetupAdapterChainRunbookId"] != runbook["privateSetupAdapterChainRunbookId"]:
        raise PrivateSourceKindSelectionExamplesError("selection examples must bind adapter-chain runbook")

    summaries = {item["sourceKind"]: item for item in guidance["sourceKindSummary"]}
    examples = {item["sourceKind"]: item for item in record["selectionExamples"]}
    if list(examples) != SOURCE_KIND_ORDER:
        raise PrivateSourceKindSelectionExamplesError("selection examples should preserve source-kind order")
    if set(examples) != set(summaries) or set(examples) != set(actions):
        raise PrivateSourceKindSelectionExamplesError("selection examples should cover guidance and first actions")

    for source_kind, example in examples.items():
        summary = summaries[source_kind]
        action = actions[source_kind]
        if example["guidanceBinding"]["outcomeClass"] != summary["outcomeClass"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} outcome class drift")
        if example["guidanceBinding"]["allowedEntrypoint"] != summary["allowedEntrypoint"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} entrypoint drift")
        if example["firstActionBinding"]["privateSetupFirstActionId"] != action["privateSetupFirstActionId"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} first-action binding drift")
        if example["firstActionBinding"]["routeDecision"] != action["routeDecision"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} route decision drift")
        if example["firstActionBinding"]["allowedEntrypoint"] != action["allowedEntrypoint"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} first-action entrypoint drift")
        recommendation_item = example["recommendation"]
        if recommendation_item["forecastArtifactsAllowed"] or recommendation_item["scoringAllowed"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} examples must not allow forecast or scoring")
        if not recommendation_item["stopBeforeForecast"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} should stop before forecast execution")

    if examples["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise PrivateSourceKindSelectionExamplesError("local file should select source-builder adapter")
    if examples["local_file"]["adapterChainBinding"]["nextOperationAfterPrerequisites"] != "private_setup_source_builder":
        raise PrivateSourceKindSelectionExamplesError("local file should bind source-builder operation")
    if examples["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise PrivateSourceKindSelectionExamplesError("manual mapping should require confirmation")
    if examples["manual_mapping"]["adapterChainBinding"]["branchId"] != "adapterchainbranch-001":
        raise PrivateSourceKindSelectionExamplesError("manual mapping should bind confirmation branch")
    if examples["auto_evidence_connector"]["adapterChainBinding"]["applicability"] != "outside_current_adapter_chain":
        raise PrivateSourceKindSelectionExamplesError("auto evidence should remain outside the local-file adapter chain")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        example = examples[source_kind]
        if example["recommendation"]["immediateAction"] != "wait_for_runtime":
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} should wait for runtime")
        if example["adapterChainBinding"]["adapterCommandAfterPrerequisites"] != NO_COMMAND:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} should expose no adapter command")
    if examples["unregistered_source"]["recommendation"]["immediateAction"] != "replace_source":
        raise PrivateSourceKindSelectionExamplesError("unregistered source should require replacement")
    if examples["unsafe_source"]["recommendation"]["immediateAction"] != "reject_source":
        raise PrivateSourceKindSelectionExamplesError("unsafe source should be rejected")

    boundary = record["executionBoundary"]
    if boundary["examplesDoNotExecute"] is not True or boundary["runsCommands"] is not False:
        raise PrivateSourceKindSelectionExamplesError("selection examples must remain non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        if boundary[key] is not False:
            raise PrivateSourceKindSelectionExamplesError(f"{key} must remain false")


def validate_generated_examples(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise PrivateSourceKindSelectionExamplesError(
            f"private source-kind selection examples schema validation failed: {errors[0]}"
        )
    examples = {item["sourceKind"]: item for item in record["selectionExamples"]}
    if list(examples) != SOURCE_KIND_ORDER:
        raise PrivateSourceKindSelectionExamplesError("selection examples should preserve source-kind order")
    for source_kind, example in examples.items():
        recommendation_item = example["recommendation"]
        if recommendation_item["forecastArtifactsAllowed"] or recommendation_item["scoringAllowed"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} examples must not allow forecast or scoring")
        if not recommendation_item["stopBeforeForecast"]:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} should stop before forecast execution")
    if examples["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise PrivateSourceKindSelectionExamplesError("local file should select source-builder adapter")
    if examples["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise PrivateSourceKindSelectionExamplesError("manual mapping should require confirmation")
    if examples["auto_evidence_connector"]["adapterChainBinding"]["applicability"] != "outside_current_adapter_chain":
        raise PrivateSourceKindSelectionExamplesError("auto evidence should remain outside the local-file adapter chain")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        if examples[source_kind]["adapterChainBinding"]["adapterCommandAfterPrerequisites"] != NO_COMMAND:
            raise PrivateSourceKindSelectionExamplesError(f"{source_kind} should expose no adapter command")
    if examples["unregistered_source"]["recommendation"]["immediateAction"] != "replace_source":
        raise PrivateSourceKindSelectionExamplesError("unregistered source should require replacement")
    if examples["unsafe_source"]["recommendation"]["immediateAction"] != "reject_source":
        raise PrivateSourceKindSelectionExamplesError("unsafe source should be rejected")

    boundary = record["executionBoundary"]
    if boundary["examplesDoNotExecute"] is not True or boundary["runsCommands"] is not False:
        raise PrivateSourceKindSelectionExamplesError("selection examples must remain non-executing")
    for key in [
        "readsPrivateData",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        if boundary[key] is not False:
            raise PrivateSourceKindSelectionExamplesError(f"{key} must remain false")


def write_examples(record: dict[str, Any]) -> None:
    write_generated(EXAMPLES_PATH, record, label="private source-kind selection examples", regen="python3 scripts/generate_private_source_kind_selection_examples.py --write")


def check_examples(record: dict[str, Any]) -> None:
    check_generated(EXAMPLES_PATH, record, label="private source-kind selection examples", regen="python3 scripts/generate_private_source_kind_selection_examples.py --write")


def load_generated_examples() -> dict[str, Any] | None:
    if not EXAMPLES_PATH.exists():
        return None
    record = json.loads(EXAMPLES_PATH.read_text(encoding="utf-8"))
    validate_generated_examples(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private source-kind selection examples")
    parser.add_argument("--write", action="store_true", help="write generated private source-kind selection examples")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    record = build_examples() if args.write or args.check or args.rebuild else (load_generated_examples() or build_examples())
    if args.write:
        write_examples(record)
    elif args.check:
        check_examples(record)
    else:
        sys.stdout.write(render_json(record))


if __name__ == "__main__":
    main()
