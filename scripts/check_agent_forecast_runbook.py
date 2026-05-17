#!/usr/bin/env python3
"""Check agent forecast runbook workflow and matrix alignment."""

from __future__ import annotations

from generate_agent_forecast_runbook import NEXT_ACTION_BY_OUTCOME, build_runbook
from generate_forecast_run_intake_matrix import build_matrix


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    runbook = build_runbook()
    matrix, summaries = build_matrix()
    outcomes = {item["outcomeClass"]: item for item in matrix["outcomes"]}
    playbooks = {item["outcomeClass"]: item for item in runbook["outcomePlaybooks"]}

    require(set(playbooks) == set(outcomes), "runbook should cover every forecast-run intake class")
    for outcome_class, outcome in outcomes.items():
        playbook = playbooks[outcome_class]
        require(playbook["retryPolicy"] == outcome["retryPolicy"], f"{outcome_class} retry policy drifted")
        require(
            playbook["nextActionLabel"] == NEXT_ACTION_BY_OUTCOME[outcome_class],
            f"{outcome_class} next-action label drifted",
        )
        require(
            playbook["mcpIsError"] == outcome["mcpExpectation"]["isError"],
            f"{outcome_class} MCP expectation drifted",
        )
        summary = summaries[outcome_class]
        if outcome_class == "accepted":
            require(playbook["generatesForecastOutputs"] is True, "accepted should generate outputs")
            require(playbook["mustNotBindForecastOutputs"] is False, "accepted should allow output bindings")
            require(summary["recordBinding"]["forecastId"] == "forecast-602", "accepted should bind forecast-602")
        else:
            require(playbook["generatesForecastOutputs"] is False, f"{outcome_class} must not generate outputs")
            require(playbook["mustNotBindForecastOutputs"] is True, f"{outcome_class} must forbid output bindings")
            require(summary["recordBinding"]["forecastId"] is None, f"{outcome_class} must not bind a forecast")

    workflow = runbook["workflow"]
    orders = [item["order"] for item in workflow]
    require(orders == sorted(orders), "runbook workflow should be ordered")
    names = [item["name"] for item in workflow]
    require(names[0] == "validate_request", "runbook should start with request validation")
    require("run_forecast" in names, "runbook should include forecast-run entrypoint")
    require("inspect_intake_outcome" in names, "runbook should include intake matrix inspection")
    require("read_evidence_trace" in names, "runbook should include evidence trace inspection")
    require(names[-1] == "read_scoring_summary", "runbook should end with scoring boundary inspection")

    read_operations = {item["operation"] for item in runbook["readSurfaceChoices"]}
    require(
        read_operations == {"forecast_card", "evidence_trace", "lifecycle_bundle", "resolution_status", "scoring_summary"},
        "runbook should expose the five post-run read choices",
    )
    require(
        runbook["exampleSequence"]["forecastId"] == "forecast-602",
        "runbook example should use the accepted forecast-run forecastId",
    )
    require(
        runbook["exampleSequence"]["questionId"] == "question-601",
        "runbook example should use the accepted forecast-run questionId",
    )

    print("checked agent forecast runbook")


if __name__ == "__main__":
    main()
