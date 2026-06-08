#!/usr/bin/env python3
"""Check the generic prediction-goal catalog readbacks."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

try:
    from generate_prediction_goal_catalog import (
        CATALOG_GOAL_KEYS,
        build_prediction_goal_catalog,
        validate_prediction_goal_catalog,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until generator exists
    raise AssertionError("prediction goal catalog generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GOALS = {
    "delivery_delay_risk",
    "stockout_risk",
    "sla_breach_risk",
    "demand_risk",
    "churn_risk",
    "seaport_berth_availability",
    "weather_sensitive_operations",
    "public_transit_disruption_risk",
}
CLASSIFICATIONS = {"forecastable", "needs_clarification", "blocked", "rejected"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def load_cli_json(*args: str) -> dict[str, object]:
    completed = run_cli(*args)
    require(completed.returncode == 0, f"CLI failed for {' '.join(args)}: {completed.stderr or completed.stdout}")
    payload = json.loads(completed.stdout)
    require(isinstance(payload, dict), "CLI payload should be a JSON object")
    return payload


def main() -> None:
    require(set(CATALOG_GOAL_KEYS) == REQUIRED_GOALS, "catalog goal-key constant drifted")

    record = build_prediction_goal_catalog()
    validate_prediction_goal_catalog(record)

    require(record["predictionGoalCatalogId"] == "predictiongoalcatalog-001", "catalog id drifted")
    require(record["catalogStatus"] == "checked_domain_agnostic_goal_catalog", "catalog status drifted")
    require(record["setupEngineBinding"]["setupEngineId"] == "setupengine-001", "catalog should bind setup-engine")
    require(record["setupEngineBinding"]["examplesViewCommand"] == "python3 scripts/ope.py setup-engine --view examples", "setup-engine examples command drifted")
    require(record["qualityClaimAllowed"] is False, "catalog must not allow quality claims")
    require(record["createsForecastArtifacts"] is False, "catalog must not create forecast artifacts")
    require(record["hostedRuntimeRequired"] is False, "catalog must not require hosted runtime")

    examples = {item["goalKey"]: item for item in record["goalExamples"]}
    require(set(examples) == REQUIRED_GOALS, "catalog should cover the required generic goals")
    classifications = {item["classification"] for item in examples.values()}
    require(classifications == CLASSIFICATIONS, "catalog should cover all setup-engine classifications")

    transit = examples["public_transit_disruption_risk"]
    require(transit["classification"] == "forecastable", "public transit should be one forecastable catalog example")
    require("Helsinki" not in transit["goalTitle"], "transit catalog title should not default to Helsinki")
    require("public transit" in transit["goalTitle"].lower(), "transit example should remain legible as transit")

    for key, example in examples.items():
        require(example["qualityClaimAllowed"] is False, f"{key} must block quality claims")
        require(example["createsForecastArtifacts"] is False, f"{key} must not create forecast artifacts")
        require(example["hostedRuntimeRequired"] is False, f"{key} must not require hosted runtime")
        require(example["classification"] in CLASSIFICATIONS, f"{key} classification drifted")
        if example["classification"] in {"forecastable", "needs_clarification"}:
            require(example["requiredSourceRoles"], f"{key} should list required source roles")
            require(example["baselineCandidate"]["methodId"] == "historical_frequency_baseline", f"{key} baseline drifted")
            require(example["resolutionSource"]["sourceRole"] == "resolution_outcome", f"{key} resolution source drifted")
            require(example["forecastCardFields"], f"{key} should list forecast-card fields")
            require(example["firstSafeHostAction"], f"{key} should expose the first safe host action")
        else:
            require(example["blockedReason"], f"{key} should explain why setup stops")

    summary = record["summary"]
    require(summary["goalExampleCount"] == len(REQUIRED_GOALS), "summary example count drifted")
    require(summary["forecastableCount"] >= 5, "catalog should mostly show forecastable reusable patterns")
    require(summary["helsinkiDefaultNarrative"] is False, "Helsinki must not be the default catalog narrative")
    require(summary["qualityClaimAllowed"] is False, "summary must block quality claims")

    cli = load_cli_json("prediction-goal-catalog")
    require(cli["summary"]["goalExampleCount"] == len(REQUIRED_GOALS), "catalog CLI count drifted")
    require(cli["setupEngineBinding"]["setupEngineId"] == "setupengine-001", "catalog CLI setup-engine binding drifted")

    goal_view = load_cli_json("prediction-goal-catalog", "--goal", "stockout_risk")
    require(goal_view["goalKey"] == "stockout_risk", "goal view should return requested example")
    require(goal_view["classification"] == "forecastable", "stockout should be forecastable")

    summary_view = load_cli_json("prediction-goal-catalog", "--view", "summary")
    require(summary_view["view"] == "summary", "summary view should identify itself")
    require(summary_view["summary"]["classificationCount"] == 4, "summary view classification count drifted")

    setup_examples = load_cli_json("setup-engine", "--view", "examples")
    require(setup_examples["catalogBinding"]["predictionGoalCatalogId"] == "predictiongoalcatalog-001", "setup-engine examples should bind catalog")
    setup_goal_keys = {item["goalKey"] for item in setup_examples["exampleGoals"]}
    require(REQUIRED_GOALS <= setup_goal_keys, "setup-engine examples should expose catalog goals")

    check = run_cli("prediction-goal-catalog", "--check")
    require(check.returncode == 0, f"catalog --check failed: {check.stderr or check.stdout}")
    require("checked prediction goal catalog" in check.stdout, "catalog --check output drifted")

    print("checked prediction goal catalog")


if __name__ == "__main__":
    main()
