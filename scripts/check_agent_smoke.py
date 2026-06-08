#!/usr/bin/env python3
"""Check the fast external-agent smoke command."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/ope.py", "smoke", "--output-format", "json"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(result.returncode == 0, f"smoke command failed: {result.stderr or result.stdout}")
    summary = json.loads(result.stdout)

    require(summary["smokeStatus"] == "passed", "smoke status drifted")
    require(summary["stepCount"] == 8, "smoke should run eight adoption steps")
    require(summary["failedStep"] is None, "passing smoke should not report a failed step")
    require(summary["writesState"] is False, "smoke must not write state")
    require(summary["fetchesLiveData"] is False, "smoke must not fetch live data")
    require(summary["qualityClaimUpgraded"] is False, "smoke must not upgrade quality claims")
    require(summary["nextCommandOnSuccess"] == "python3 scripts/ope.py setup-engine --goal \"<host prediction goal>\"", "success next command drifted")
    require("[smoke] start schema sanity" in result.stderr, "smoke should print schema sanity progress")
    require("[smoke] start forecast card read" in result.stderr, "smoke should print forecast-card progress")

    steps = {item["stepKey"]: item for item in summary["steps"]}
    expected = [
        "schema_sanity",
        "setup_engine_check",
        "prediction_goal_catalog_check",
        "developer_adoption_check",
        "agent_implementation_kit_check",
        "agent_integrate_candidates",
        "agent_integrate_guided_forecast",
        "forecast_card_read",
    ]
    require(list(steps) == expected, "smoke step order drifted")
    require(steps["agent_integrate_guided_forecast"]["forecastId"] == "forecast-1102", "guided smoke forecast binding drifted")
    require(steps["forecast_card_read"]["questionId"] == "question-1102", "forecast-card smoke question binding drifted")

    check_result = subprocess.run(
        [sys.executable, "scripts/ope.py", "smoke", "--check"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    require(check_result.returncode == 0, f"smoke --check failed: {check_result.stderr or check_result.stdout}")
    require("checked fast agent smoke" in check_result.stdout, "smoke --check output drifted")

    print("checked fast agent smoke")


if __name__ == "__main__":
    main()
