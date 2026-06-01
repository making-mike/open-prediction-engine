#!/usr/bin/env python3
"""Check developer adoption surface invariants."""

from __future__ import annotations

from generate_developer_adoption_surface import SCENARIO_PHASES, build_developer_adoption_surface


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    surface = build_developer_adoption_surface()
    quickstart = surface["quickstart"]
    scenario = surface["exampleScenario"]
    integrations = {item["interface"]: item for item in surface["integrationNotes"]}
    notes = {item["category"]: item["items"] for item in surface["releaseNotes"]}
    boundary = surface["executionBoundary"]
    summary = surface["summary"]

    require(surface["surfaceStatus"] == "local_mvp_adoption_ready", "adoption surface status drifted")
    require(surface["bindings"]["forecastId"] == "forecast-1102", "adoption surface should bind forecast-1102")
    require(surface["bindings"]["forecastBundleId"] == "forecastbundle-forecast-1102", "adoption bundle binding drifted")
    require([item["order"] for item in quickstart] == [1, 2, 3, 4, 5, 6, 7], "quickstart order drifted")
    require(quickstart[0]["command"] == "python3 --version", "quickstart should start with Python setup")
    require(quickstart[1]["command"] == "python3 scripts/run_checks.py", "quickstart should include canonical checks")
    require("local-source-runtime" in quickstart[2]["command"], "quickstart should expose local source runtime")
    require("prediction-campaign explain" in quickstart[-1]["command"], "quickstart should evaluate recurring campaigns")

    require([item["phase"] for item in scenario["steps"]] == SCENARIO_PHASES, "scenario phase order drifted")
    require(scenario["expectedFinalState"]["forecastCardAvailable"] is True, "scenario should reach forecast card")
    require(scenario["expectedFinalState"]["lifecycleBundleAvailable"] is True, "scenario should reach lifecycle bundle")
    require(scenario["expectedFinalState"]["scoreStatus"] == "scored", "scenario should include scoring readback")
    require(scenario["expectedFinalState"]["qualityClaimAllowed"] is False, "scenario must block quality claims")
    for step in scenario["steps"]:
        require(step["qualityClaimAllowed"] is False, "scenario steps must not allow quality claims")
        require(step["createsArtifacts"] is False, "adoption guide should not create artifacts")

    require(set(integrations) == {"cli", "agent_call", "mcp_stdio"}, "integration coverage drifted")
    require(integrations["cli"]["implementedStatus"] == "implemented_local", "CLI should be implemented locally")
    require(integrations["agent_call"]["implementedStatus"] == "implemented_local", "agent-call should be implemented locally")
    require(integrations["mcp_stdio"]["implementedStatus"] == "local_scaffold", "MCP stdio should remain a local scaffold")

    require(set(notes) == {"implemented", "fixture_only", "non_goal"}, "release-note categories drifted")
    require(any("Local CLI" in item for item in notes["implemented"]), "implemented notes should mention local CLI")
    require(any("fixture" in item.lower() for item in notes["fixture_only"]), "fixture-only notes should be explicit")
    require(any("No hosted service" in item for item in notes["non_goal"]), "non-goal notes should block hosted service claims")
    require(any("No generated language-specific" in item for item in notes["non_goal"]), "non-goal notes should defer generated types")
    require(
        any("hosted scheduling" in item for item in notes["non_goal"]),
        "non-goal notes should defer hosted scheduling before recurring setup evidence",
    )

    decision = surface["typeGenerationDecision"]
    require(decision["decisionStatus"] == "defer_until_adoption_evidence", "type-generation decision drifted")
    require(decision["generatedTypesIncluded"] is False, "generated runtime types should not be included yet")

    require(summary["quickstartStepCount"] == 7, "quickstart count drifted")
    require(summary["scenarioStepCount"] == 6, "scenario count drifted")
    require(summary["integrationCount"] == 3, "integration count drifted")
    require(summary["qualityClaimAllowed"] is False, "summary must block quality claims")
    require(summary["generatedTypesIncluded"] is False, "summary must defer generated types")

    require(boundary["readOnlyGuide"] is True, "adoption surface should be read-only")
    require(boundary["normalChecksDeterministicOffline"] is True, "adoption surface should be deterministic offline")
    for key, value in boundary.items():
        if key in {"readOnlyGuide", "normalChecksDeterministicOffline"}:
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked developer adoption surface")


if __name__ == "__main__":
    main()
