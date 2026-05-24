#!/usr/bin/env python3
"""Check private source-kind selection example boundaries."""

from __future__ import annotations

from generate_private_source_kind_selection_examples import SOURCE_KIND_ORDER, build_examples
from generate_private_setup_adapter_chain_runbook import build_runbook
from generate_private_setup_first_actions import build_actions


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    record = build_examples()
    runbook = build_runbook()
    actions = {item["sourceKind"]: item for item in build_actions()}
    examples = {item["sourceKind"]: item for item in record["selectionExamples"]}
    sequence = {item["operation"]: item for item in runbook["operationSequence"]}

    require(list(examples) == SOURCE_KIND_ORDER, "selection examples should preserve source-kind order")
    require(set(examples) == set(actions), "selection examples should cover every first-action source kind")
    require(
        record["bindings"]["privateSetupAdapterChainRunbookId"] == runbook["privateSetupAdapterChainRunbookId"],
        "selection examples should bind adapter-chain runbook",
    )

    for source_kind, example in examples.items():
        action = actions[source_kind]
        first_action = example["firstActionBinding"]
        require(
            first_action["privateSetupFirstActionId"] == action["privateSetupFirstActionId"],
            f"{source_kind} should bind first action",
        )
        require(first_action["routeDecision"] == action["routeDecision"], f"{source_kind} route drift")
        require(first_action["allowedEntrypoint"] == action["allowedEntrypoint"], f"{source_kind} entrypoint drift")
        require(first_action["commandToRun"] == action["commandToRun"], f"{source_kind} command drift")
        recommendation = example["recommendation"]
        require(recommendation["stopBeforeForecast"] is True, f"{source_kind} should stop before forecast execution")
        require(
            recommendation["forecastArtifactsAllowed"] is False,
            f"{source_kind} should not allow forecast artifacts",
        )
        require(recommendation["scoringAllowed"] is False, f"{source_kind} should not allow scoring")

    local_file = examples["local_file"]
    require(
        local_file["adapterChainBinding"]["runbookStepId"]
        == sequence["private_setup_source_builder"]["runbookStepId"],
        "local file should bind source-builder step",
    )
    require(
        local_file["adapterChainBinding"]["nextOperationAfterPrerequisites"] == "private_setup_source_builder",
        "local file should select source-builder operation",
    )
    require(
        local_file["recommendation"]["immediateAction"] == "call_source_builder_adapter",
        "local file immediate action should call source-builder adapter",
    )

    manual_mapping = examples["manual_mapping"]
    require(
        manual_mapping["recommendation"]["requiresCallerConfirmation"] is True,
        "manual mapping should require caller confirmation",
    )
    require(
        manual_mapping["adapterChainBinding"]["branchId"] == "adapterchainbranch-001",
        "manual mapping should bind mapping-confirmation branch",
    )
    require(
        manual_mapping["adapterChainBinding"]["nextOperationAfterPrerequisites"] == "private_setup_source_handoff",
        "manual mapping should route to source-handoff after confirmation",
    )

    auto_evidence = examples["auto_evidence_connector"]
    require(
        auto_evidence["recommendation"]["immediateAction"] == "call_fixture_evidence",
        "auto evidence should choose fixture evidence",
    )
    require(
        auto_evidence["adapterChainBinding"]["applicability"] == "outside_current_adapter_chain",
        "auto evidence should stay outside the local-file adapter chain",
    )
    require(
        auto_evidence["adapterChainBinding"]["adapterCommandAfterPrerequisites"] == "python3 scripts/ope.py gather-evidence",
        "auto evidence should point to fixture gather command",
    )

    for source_kind in ["manual_upload", "private_api", "private_database"]:
        example = examples[source_kind]
        require(
            example["recommendation"]["immediateAction"] == "wait_for_runtime",
            f"{source_kind} should wait for runtime",
        )
        require(
            example["recommendation"]["requiresFutureRuntime"] is True,
            f"{source_kind} should require future runtime",
        )
        require(
            example["adapterChainBinding"]["applicability"] == "planned_runtime_blocked",
            f"{source_kind} should be blocked as planned runtime",
        )
        require(
            example["adapterChainBinding"]["adapterCommandAfterPrerequisites"] == "none",
            f"{source_kind} should expose no command",
        )

    require(
        examples["unregistered_source"]["recommendation"]["immediateAction"] == "replace_source",
        "unregistered source should require replacement",
    )
    require(
        examples["unregistered_source"]["adapterChainBinding"]["applicability"] == "source_replacement_stop",
        "unregistered source should stop for replacement",
    )
    require(
        examples["unsafe_source"]["recommendation"]["immediateAction"] == "reject_source",
        "unsafe source should be rejected",
    )
    require(
        examples["unsafe_source"]["adapterChainBinding"]["applicability"] == "unsafe_source_stop",
        "unsafe source should bind unsafe stop path",
    )

    boundary = record["executionBoundary"]
    require(boundary["examplesDoNotExecute"] is True, "selection examples should not execute")
    require(boundary["runsCommands"] is False, "selection examples should not run commands")
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
        require(boundary[key] is False, f"{key} should remain false")

    print("checked private source-kind selection examples")


if __name__ == "__main__":
    main()
