#!/usr/bin/env python3
"""Check the copyable embedded prediction feature example."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "embed-ope-prediction-feature"
WRAPPER = EXAMPLE / "host_wrapper.py"
FIXTURES = EXAMPLE / "fixtures"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_wrapper(fixture: str) -> dict[str, Any]:
    command = [
        sys.executable,
        str(WRAPPER.relative_to(ROOT)),
        "--request",
        str((FIXTURES / fixture).relative_to(ROOT)),
        "--output-format",
        "json",
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(result.returncode == 0, f"wrapper failed for {fixture}: {result.stderr or result.stdout}")
    return json.loads(result.stdout)


def main() -> None:
    require(EXAMPLE.exists(), "embed prediction feature example directory is missing")
    require(WRAPPER.exists(), "host wrapper is missing")
    readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
    for phrase in [
        "setup-engine",
        "engine setup plan",
        "host-facing data shape",
        "prediction-feature-setup",
        "forecast-card",
        "no hosted service",
        "no credential values",
        "raw private rows",
        "raw SQL",
        "post-outcome evidence",
        "method extension",
        "untracked route-risk engine",
        "quality claim",
    ]:
        require(phrase in readme, f"example README missing {phrase!r}")

    expected_fixture_names = {
        "approved_feature_request.json",
        "blocked_raw_credentials.json",
        "blocked_raw_private_rows.json",
        "blocked_raw_sql.json",
        "blocked_unapproved_source.json",
        "blocked_missing_source_roles.json",
        "blocked_vague_outcome.json",
        "blocked_post_outcome_evidence.json",
        "blocked_hosted_runtime.json",
        "expected_accepted_summary.json",
        "expected_blocked_summary.json",
    }
    actual_fixture_names = {path.name for path in FIXTURES.glob("*.json")}
    require(expected_fixture_names.issubset(actual_fixture_names), "example fixture coverage drifted")

    approved = load_json(FIXTURES / "approved_feature_request.json")
    require(approved["hostFeatureIntent"], "approved fixture should include hostFeatureIntent")
    require(approved["approvedSourceRefs"], "approved fixture should include approved source refs")
    require(approved["responseSizeBudgetBytes"] <= 65536, "approved fixture should stay compact")

    accepted = run_wrapper("approved_feature_request.json")
    require(accepted["exampleStatus"] == "setup_plan_and_forecast_card_ready", "accepted example status drifted")
    require(
        accepted["opeCallSequence"][0].startswith("python3 scripts/ope.py setup-engine"),
        "host wrapper should call setup-engine before other OPE readbacks",
    )
    require(
        accepted["opeCallSequence"][1] == "python3 scripts/ope.py prediction-feature-setup --view response --case accepted",
        "host wrapper should call prediction-feature-setup after rendering setup-engine",
    )
    require(
        accepted["opeCallSequence"][2].startswith("python3 scripts/ope.py read --record-type forecast-card"),
        "host wrapper should read forecast-card only after setup response",
    )
    setup_plan = accepted["setupEnginePlan"]
    require(setup_plan["setupStatus"] == "checked_readback", "setup plan status drifted")
    require(setup_plan["renderBeforeForecastArtifacts"] is True, "setup plan must render before forecast cards")
    require(setup_plan["candidateContracts"][0]["status"] == "forecastable", "setup plan should expose forecastable candidate first")
    require(
        {"forecast_time_signal", "historical_outcome", "resolution_outcome"} <= set(setup_plan["sourceRoles"]),
        "setup plan should expose required source roles",
    )
    require(
        setup_plan["baselineStatus"]["defaultMethodId"] == "historical_frequency_baseline",
        "setup plan should expose baseline method guidance",
    )
    require(
        setup_plan["forecastCardPreview"]["qualityClaimAllowed"] is False,
        "setup plan forecast-card preview must keep quality claims blocked",
    )
    require(
        {"approvedSourceRefs", "outcomeDefinition", "resolutionHints"} <= set(setup_plan["requiredHostInputs"]),
        "setup plan should expose required host inputs",
    )
    require(setup_plan["warnings"], "setup plan should expose host-facing warnings")
    require(accepted["setupResponse"]["forecastId"] == "forecast-1102", "accepted setup forecast binding drifted")
    require(accepted["forecastCard"]["record"]["forecastId"] == "forecast-1102", "forecast-card binding drifted")
    require(accepted["forecastCard"]["record"]["qualityClaim"]["status"] != "calibrated", "example must not imply calibration")
    require(accepted["executionBoundary"]["createsForecastArtifacts"] is False, "example must not create forecast artifacts")
    require(accepted["executionBoundary"]["storesCredentialValues"] is False, "example must not store credentials")
    require(accepted["executionBoundary"]["opensNetworkListener"] is False, "example must not open a network listener")
    require(accepted["executionBoundary"]["implementsOpeScoring"] is False, "host wrapper must not implement OPE scoring")
    require(accepted["executionBoundary"]["implementsOpeCalibration"] is False, "host wrapper must not implement OPE calibration")
    require(accepted["executionBoundary"]["implementsCustomRiskEngine"] is False, "host wrapper must not implement an untracked risk engine")
    require(accepted["executionBoundary"]["qualityClaimAllowed"] is False, "example must not allow quality claims")

    expected_accepted = load_json(FIXTURES / "expected_accepted_summary.json")
    for key, value in expected_accepted.items():
        require(accepted["summary"][key] == value, f"accepted summary field {key} drifted")

    blocked = run_wrapper("blocked_raw_credentials.json")
    require(blocked["exampleStatus"] == "blocked", "blocked credential example status drifted")
    require("raw_credentials" in blocked["reasonCodes"], "blocked credential reason code drifted")
    require(blocked["opeCommandExecuted"] is False, "blocked unsafe examples must stop before OPE calls")
    require(blocked["opeCallSequence"] == [], "blocked unsafe examples should have no OPE call sequence")
    require(blocked["setupEnginePlan"] is None, "blocked unsafe examples should not render a setup plan")
    require(blocked["forecastCard"] is None, "blocked unsafe examples must not read forecast cards")

    expected_blocked = load_json(FIXTURES / "expected_blocked_summary.json")
    for key, value in expected_blocked.items():
        require(blocked["summary"][key] == value, f"blocked summary field {key} drifted")

    for fixture_name in expected_fixture_names:
        if not fixture_name.startswith("blocked_"):
            continue
        blocked_payload = run_wrapper(fixture_name)
        require(blocked_payload["exampleStatus"] == "blocked", f"{fixture_name} should be blocked")
        require(blocked_payload["forecastCard"] is None, f"{fixture_name} should not read a card")
        if fixture_name in {"blocked_missing_source_roles.json", "blocked_vague_outcome.json"}:
            require(blocked_payload["opeCommandExecuted"] is True, f"{fixture_name} should render setup-engine")
            require(blocked_payload["setupEnginePlan"] is not None, f"{fixture_name} should include setup plan")
            require(
                blocked_payload["opeCallSequence"][0].startswith("python3 scripts/ope.py setup-engine"),
                f"{fixture_name} should call setup-engine first",
            )
            require(blocked_payload["setupResponse"] is None, f"{fixture_name} should stop before setup response")
        else:
            require(blocked_payload["opeCommandExecuted"] is False, f"{fixture_name} should not call OPE")
            require(blocked_payload["opeCallSequence"] == [], f"{fixture_name} should not record OPE calls")
            require(blocked_payload["setupEnginePlan"] is None, f"{fixture_name} should not include setup plan")

    print("checked embedded prediction feature example")


if __name__ == "__main__":
    main()
