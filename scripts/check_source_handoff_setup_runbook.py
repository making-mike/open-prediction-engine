#!/usr/bin/env python3
"""Check source-handoff setup runbook workflow and guard alignment."""

from __future__ import annotations

from generate_source_intake_handoff import CASE_ORDER
from generate_source_handoff_setup_runbook import build_runbook


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runbook = build_runbook()
    playbooks = {item["case"]: item for item in runbook["casePlaybooks"]}
    require(list(playbooks) == CASE_ORDER, "source-handoff setup runbook should preserve case order")

    confirmed = playbooks["confirmed_builder_draft"]
    require(confirmed["forecastId"] == "forecast-1102", "confirmed handoff should bind forecast-1102")
    require(confirmed["questionId"] == "question-1102", "confirmed handoff should bind question-1102")
    require(confirmed["generatesForecastOutputs"] is True, "confirmed handoff should generate forecast outputs")
    require(confirmed["scored"] is True, "confirmed handoff should be scored after resolution")
    require(
        confirmed["qualityClaimStatus"] == "not_enough_resolved_source_handoff_outcomes",
        "confirmed handoff should preserve source-handoff quality boundary",
    )

    for case, playbook in playbooks.items():
        if case == "confirmed_builder_draft":
            continue
        require(playbook["forecastId"] is None, f"{case} must not bind a forecast")
        require(playbook["questionId"] is None, f"{case} must not bind a question")
        require(playbook["generatesForecastOutputs"] is False, f"{case} must not generate outputs")
        require(playbook["scored"] is False, f"{case} must not be scored")
        require(playbook["mustNotForecast"] is True, f"{case} must explicitly forbid forecasting")
        require(playbook["mustNotScore"] is True, f"{case} must explicitly forbid scoring")

    require(
        playbooks["unconfirmed_builder_draft"]["nextActionLabel"] == "ask_mapping_confirmation",
        "unconfirmed draft should ask for mapping confirmation",
    )
    require(
        playbooks["insufficient_confirmed_builder_draft"]["nextActionLabel"] == "collect_more_data",
        "insufficient draft should collect more data",
    )
    for case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        require(
            playbooks[case]["nextActionLabel"] == "replace_rejected_sources",
            f"{case} should replace rejected sources",
        )

    workflow_names = [item["name"] for item in runbook["workflow"]]
    require(workflow_names[0] == "inspect_sources", "runbook should start with source inspection")
    require("handoff_to_source_intake" in workflow_names, "runbook should include source intake handoff")
    require("run_method_gate" in workflow_names, "runbook should include method gating")
    require("execute_forecast" in workflow_names, "runbook should include explicit forecast execution")
    require("resolve_forecast" in workflow_names, "runbook should include source-handoff resolution")
    require(workflow_names[-1] == "read_track_record", "runbook should end at track-record boundary")

    read_operations = {item["operation"] for item in runbook["readSurfaceChoices"]}
    require(
        read_operations
        == {
            "source_handoff_summaries",
            "resolution_outputs",
            "forecast_card",
            "lifecycle_bundle",
            "track_record",
        },
        "runbook should expose source-handoff read choices",
    )
    require(
        runbook["exampleSequence"]["forecastId"] == "forecast-1102",
        "example sequence should use forecast-1102",
    )
    require(
        runbook["exampleSequence"]["questionId"] == "question-1102",
        "example sequence should use question-1102",
    )

    print("checked source-handoff setup runbook")


if __name__ == "__main__":
    main()
