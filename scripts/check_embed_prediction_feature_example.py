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
        "prediction-feature-setup",
        "forecast-card",
        "no hosted service",
        "no credential values",
        "raw private rows",
        "raw SQL",
        "post-outcome evidence",
        "quality claim",
    ]:
        require(phrase in readme, f"example README missing {phrase!r}")

    expected_fixture_names = {
        "approved_feature_request.json",
        "blocked_raw_credentials.json",
        "blocked_raw_private_rows.json",
        "blocked_raw_sql.json",
        "blocked_unapproved_source.json",
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
    require(accepted["exampleStatus"] == "forecast_card_ready", "accepted example status drifted")
    require(accepted["setupResponse"]["forecastId"] == "forecast-1102", "accepted setup forecast binding drifted")
    require(accepted["forecastCard"]["record"]["forecastId"] == "forecast-1102", "forecast-card binding drifted")
    require(accepted["forecastCard"]["record"]["qualityClaim"]["status"] != "calibrated", "example must not imply calibration")
    require(accepted["executionBoundary"]["createsForecastArtifacts"] is False, "example must not create forecast artifacts")
    require(accepted["executionBoundary"]["storesCredentialValues"] is False, "example must not store credentials")
    require(accepted["executionBoundary"]["opensNetworkListener"] is False, "example must not open a network listener")
    require(accepted["executionBoundary"]["qualityClaimAllowed"] is False, "example must not allow quality claims")

    expected_accepted = load_json(FIXTURES / "expected_accepted_summary.json")
    for key, value in expected_accepted.items():
        require(accepted["summary"][key] == value, f"accepted summary field {key} drifted")

    blocked = run_wrapper("blocked_raw_credentials.json")
    require(blocked["exampleStatus"] == "blocked", "blocked credential example status drifted")
    require("raw_credentials" in blocked["reasonCodes"], "blocked credential reason code drifted")
    require(blocked["opeCommandExecuted"] is False, "blocked unsafe examples must stop before OPE calls")
    require(blocked["forecastCard"] is None, "blocked unsafe examples must not read forecast cards")

    expected_blocked = load_json(FIXTURES / "expected_blocked_summary.json")
    for key, value in expected_blocked.items():
        require(blocked["summary"][key] == value, f"blocked summary field {key} drifted")

    for fixture_name in expected_fixture_names:
        if not fixture_name.startswith("blocked_"):
            continue
        blocked_payload = run_wrapper(fixture_name)
        require(blocked_payload["exampleStatus"] == "blocked", f"{fixture_name} should be blocked")
        require(blocked_payload["opeCommandExecuted"] is False, f"{fixture_name} should not call OPE")
        require(blocked_payload["forecastCard"] is None, f"{fixture_name} should not read a card")

    print("checked embedded prediction feature example")


if __name__ == "__main__":
    main()
