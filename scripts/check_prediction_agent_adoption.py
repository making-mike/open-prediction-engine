#!/usr/bin/env python3
"""Check general agent adoption surfaces for prediction-project builders."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ope_schema import validate_record

try:
    from generate_prediction_agent_adoption import build_prediction_agent_adoption
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until the generator exists
    raise AssertionError("prediction agent adoption generator is missing") from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "spec" / "prediction-agent-adoption.schema.json"
CAPABILITIES = ROOT / "ope.capabilities.json"
AGENT_QUICKSTART = ROOT / "AGENT_QUICKSTART.md"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )


def main() -> None:
    adoption = build_prediction_agent_adoption()
    errors = validate_record(adoption, SCHEMA)
    require(not errors, f"prediction agent adoption schema errors: {errors[:3]}")

    summary = adoption["summary"]
    require(summary["primaryValue"] == "engine_setup_shortcut", "primary value should be engine setup shortcut")
    require(summary["firstCommand"] == "python3 scripts/ope.py setup-engine --goal \"add predictions to my app\"", "first command drifted")
    require(summary["compactDefaultOutput"] is True, "agent-facing default output should be compact")
    require(summary["hostedRuntimeProvided"] is False, "adoption surface must not claim hosted runtime")
    require(summary["trainedModelProvided"] is False, "adoption surface must not claim trained model")
    require(summary["frontendProvided"] is False, "adoption surface must not claim frontend")

    helps = {item["capabilityKey"] for item in adoption["capabilityManifest"]["helpsWith"]}
    for key in [
        "forecast_contracts",
        "engine_setup_shortcut",
        "evidence_provenance",
        "baseline_scoring",
        "resolution_and_scoring",
        "calibration_gates",
        "agent_safe_readbacks",
    ]:
        require(key in helps, f"capability manifest missing {key}")

    non_goals = {item["nonGoalKey"] for item in adoption["capabilityManifest"]["doesNotProvide"]}
    for key in ["frontend", "hosted_api", "trained_model", "generic_web_crawler", "production_scheduler"]:
        require(key in non_goals, f"capability manifest should block {key}")

    extension_points = {item["extensionKey"]: item for item in adoption["extensionPoints"]}
    for key in ["source_adapter", "forecast_method", "resolver", "scorer", "host_app_wrapper"]:
        require(key in extension_points, f"missing extension point {key}")
        require(extension_points[key]["createsHostedRuntime"] is False, f"{key} should not create hosted runtime")

    byo = adoption["bringYourOwnModel"]
    require(byo["modelFrameworkRequired"] is False, "bring-your-own-model path should be framework-neutral")
    require(byo["baselineComparisonRequired"] is True, "BYO model must require baseline comparison")
    require(byo["leakageChecksRequired"] is True, "BYO model must require leakage checks")
    require(byo["qualityClaimBeforeEvidenceAllowed"] is False, "BYO model must block premature quality claims")

    fit = adoption["fitDecision"]
    require(
        fit["useOpeFor"] == ["engine_setup", "contracts", "evidence", "baselines", "resolution", "scoring", "calibration_gates"],
        "fit use list drifted",
    )
    require(fit["bringYourOwn"] == ["frontend", "host_runtime", "data_connectors", "custom_models", "notifications"], "fit BYO list drifted")
    require(fit["recommendedFirstAction"] == summary["firstCommand"], "fit first action drifted")

    entry_points = {item["entryKey"]: item for item in adoption["compactEntryPoints"]}
    require("prediction_goal_catalog" in entry_points, "compact entry points should include prediction goal catalog")
    require(
        entry_points["prediction_goal_catalog"]["command"] == "python3 scripts/ope.py prediction-goal-catalog --view summary",
        "prediction goal catalog entry command drifted",
    )
    require(entry_points["prediction_goal_catalog"]["mutatesState"] is False, "prediction goal catalog entry must be read-only")

    eval_surface = adoption["adoptionEvaluation"]
    require(eval_surface["targetMinutes"] == 5, "adoption eval should target first five minutes")
    require(eval_surface["passesWithoutNetwork"] is True, "adoption eval should be offline")
    require(eval_surface["writesState"] is False, "adoption eval should be non-mutating")
    eval_checks = {item["checkKey"] for item in eval_surface["checks"]}
    for key in [
        "understand_fit",
        "find_first_command",
        "read_capabilities",
        "inspect_extension_points",
        "avoid_overclaiming",
        "setup_engine_before_parallel_risk_engine",
        "avoid_audit_layer_only_framing",
    ]:
        require(key in eval_checks, f"adoption eval missing {key}")

    require(CAPABILITIES.exists(), "root ope.capabilities.json is missing")
    capabilities = json.loads(CAPABILITIES.read_text(encoding="utf-8"))
    require(capabilities == adoption["capabilityManifest"], "root capability manifest drifted from generated adoption surface")

    require(AGENT_QUICKSTART.exists(), "root AGENT_QUICKSTART.md is missing")
    quickstart_text = AGENT_QUICKSTART.read_text(encoding="utf-8")
    for phrase in [
        "Use OPE when",
        "Do not use OPE when",
        "Bring your own model",
        "Extension points",
        "python3 scripts/ope.py setup-engine",
        "python3 scripts/ope.py prediction-goal-catalog",
        "python3 scripts/ope.py explain-fit",
    ]:
        require(phrase in quickstart_text, f"AGENT_QUICKSTART.md missing {phrase!r}")

    fit_text = run_cli("explain-fit", "--goal", "add predictions to my app").stdout
    require("Use OPE for:" in fit_text, "explain-fit text should name OPE use cases")
    require("Bring yourself:" in fit_text, "explain-fit text should name bring-your-own parts")
    require(len(fit_text.splitlines()) <= 12, "explain-fit default output should stay compact")

    capabilities_json = json.loads(run_cli("capabilities").stdout)
    require(capabilities_json == capabilities, "capabilities command should emit the root manifest")

    eval_json = json.loads(run_cli("adoption-eval", "--output-format", "json").stdout)
    require(eval_json["targetMinutes"] == 5, "adoption-eval CLI target drifted")
    require(eval_json["writesState"] is False, "adoption-eval CLI should be non-mutating")

    print("checked prediction agent adoption")


if __name__ == "__main__":
    main()
