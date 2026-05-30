#!/usr/bin/env python3
"""Check local private setup orchestrator invariants."""

from __future__ import annotations

from generate_private_setup_orchestrator import build_orchestrator


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    orchestrator = build_orchestrator()
    runs = {run["runCase"]: run for run in orchestrator["orchestratorRuns"]}

    require(set(runs) == {
        "local_file_confirmed",
        "source_adapter_output_accepted",
        "missing_approval",
        "unconfirmed_mapping",
        "insufficient_data",
        "rejected_source",
        "unsafe_source",
        "response_too_large",
    }, "orchestrator should cover success, ready, and blocked cases")

    local = runs["local_file_confirmed"]
    require(local["orchestratorStatus"] == "completed_forecast_readback", "local file should complete readback")
    require(local["forecastId"] == "forecast-1102", "local file path should bind forecast-1102")
    require(local["readbackSummary"]["resolutionStatus"] == "resolved", "local file path should read resolved status")
    require(local["readbackSummary"]["scoreStatus"] == "scored", "local file path should read scored status")
    require(local["chain"]["forecastExecutionRun"] is True, "local file path should include explicit forecast execution")
    require(local["chain"]["normalReadbackRun"] is True, "local file path should include normal readback")

    adapter = runs["source_adapter_output_accepted"]
    require(adapter["orchestratorStatus"] == "ready_for_forecast_execution", "accepted adapter output should be forecast-ready")
    require(adapter["sourceAdapterOutputId"] == "sourceadapteroutput-1301", "accepted adapter output binding drifted")
    require(adapter["sourceIntakeStatus"] == "accepted", "accepted adapter output should pass source intake")
    require(adapter["setupMethodDecisionId"] == "setupmethoddecision-1301", "accepted adapter output should bind method decision")
    require(adapter["forecastId"] is None, "accepted adapter output should not invent forecast artifacts")
    require(adapter["nextAction"] == "run_explicit_setup_forecast_execution", "accepted adapter output should route to explicit forecast execution")

    require(runs["missing_approval"]["orchestratorStatus"] == "missing_approval", "missing approval should be explicit")
    require(runs["unconfirmed_mapping"]["orchestratorStatus"] == "needs_confirmation", "unconfirmed mapping should block")
    require(runs["insufficient_data"]["orchestratorStatus"] == "needs_more_data", "insufficient data should block")
    require("insufficient_comparable_rows" in runs["insufficient_data"]["blockedReasons"], "insufficient data should name row gap")
    require(runs["rejected_source"]["orchestratorStatus"] == "rejected_source", "rejected source should block")
    require(runs["unsafe_source"]["orchestratorStatus"] == "blocked_unsafe", "unsafe source should block before intake")
    require(runs["unsafe_source"]["sourceIntakeReportId"] is None, "unsafe source must not bind source intake report")
    require(runs["response_too_large"]["orchestratorStatus"] == "response_too_large", "oversized readback should be explicit")

    boundary = orchestrator["executionBoundary"]
    require(boundary["usesExistingCheckedFixturesOnly"] is True, "orchestrator should use existing checked fixtures")
    for key, value in boundary.items():
        if key != "usesExistingCheckedFixturesOnly":
            require(value is False, f"execution boundary {key} should remain false")

    summary = orchestrator["summary"]
    require(summary["runCount"] == 8, "orchestrator should summarize eight runs")
    require(summary["completedForecastReadbacks"] == 1, "orchestrator should have one completed readback")
    require(summary["readyForForecastExecution"] == 1, "orchestrator should have one ready adapter path")
    require(summary["blockedRuns"] == 6, "orchestrator should have six blocked runs")
    require(summary["localFileSupported"] is True, "local file source kind should be supported")
    require(summary["sourceAdapterOutputSupported"] is True, "source adapter output should be supported")

    print("checked private setup orchestrator")


if __name__ == "__main__":
    main()
