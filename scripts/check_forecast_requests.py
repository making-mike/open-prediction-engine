#!/usr/bin/env python3
"""Check controlled forecast request intake decisions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]
REQUESTS = ROOT / "spec" / "fixtures" / "requests"


def decision(name: str) -> dict[str, object]:
    return validate_request(load_json(REQUESTS / name))


def check_cli_sanitization() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/validate_forecast_request.py",
            "--input",
            "spec/fixtures/requests/adversarial-request.json",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    output = json.loads(result.stdout)
    if "Ignore previous" in result.stdout or "reveal any secrets" in result.stdout:
        raise AssertionError("request decision must not echo raw adversarial text")
    if output["auditLog"]["rawQuestionLogged"] is not False:
        raise AssertionError("audit log should declare raw question text was not logged")


def main() -> None:
    accepted = decision("valid-weather-logistics-request.json")
    if accepted["decisionStatus"] != "accepted" or accepted["executionAllowed"] is not True:
        raise AssertionError("valid weather-logistics request should be accepted")

    generate = decision("generate-weather-logistics-request.json")
    if generate["decisionStatus"] != "accepted" or generate["executionAllowed"] is not True:
        raise AssertionError("generate weather-logistics request should be accepted")

    blocked = decision("approval-required-sensitive-request.json")
    if blocked["decisionStatus"] != "blocked" or "approval_required" not in blocked["reasonCodes"]:
        raise AssertionError("external request should be blocked for approval")

    canceled = decision("canceled-request.json")
    if canceled["decisionStatus"] != "canceled":
        raise AssertionError("canceled request should be canceled")

    unresolvable = decision("unresolvable-request.json")
    if unresolvable["decisionStatus"] != "rejected":
        raise AssertionError("unsupported geography should be rejected")
    if "unsupported_geography" not in unresolvable["reasonCodes"]:
        raise AssertionError("unresolvable request should identify unsupported geography")

    adversarial = decision("adversarial-request.json")
    if adversarial["decisionStatus"] != "rejected":
        raise AssertionError("adversarial request should be rejected")
    if "unsafe_request" not in adversarial["reasonCodes"]:
        raise AssertionError("adversarial request should fail safety review")
    if adversarial["effectfulGeneration"] is not False:
        raise AssertionError("request intake must not execute generation")

    check_cli_sanitization()
    print("checked controlled forecast request intake")


if __name__ == "__main__":
    main()
