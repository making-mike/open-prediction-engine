#!/usr/bin/env python3
"""Check private setup workflow phases, outcomes, and claim boundaries."""

from __future__ import annotations

from generate_private_setup_workflow import build_workflow


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    workflow = build_workflow()

    require(workflow["scope"] == "domain_agnostic", "private setup workflow should be domain agnostic")
    require(
        workflow["runtimeStatus"] == "local_fixture_contract",
        "private setup workflow should remain a local fixture contract",
    )

    phases = [item["phase"] for item in workflow["phases"]]
    require(
        phases
        == [
            "source_discovery",
            "mapping_confirmation",
            "source_intake",
            "method_gating",
            "forecast_execution",
            "recalculation",
            "resolution",
            "scoring",
        ],
        "private setup workflow phase order drifted",
    )

    outcomes = {item["outcomeClass"]: item for item in workflow["outcomeClasses"]}
    require(outcomes["setup_ready"]["canForecast"] is True, "setup_ready should allow forecast continuation")
    require(outcomes["setup_ready"]["canScore"] is True, "setup_ready should allow scoring continuation")
    for outcome in [
        "needs_confirmation",
        "needs_more_data",
        "rejected_source",
        "unsupported_source",
        "runtime_not_implemented",
    ]:
        require(outcomes[outcome]["canForecast"] is False, f"{outcome} must not allow forecasting")
        require(outcomes[outcome]["canScore"] is False, f"{outcome} must not allow scoring")

    source_support = {item["sourceKind"]: item for item in workflow["supportedSourceKinds"]}
    require(source_support["local_file"]["implementationStatus"] == "implemented_fixture", "local files should be fixture implemented")
    require(source_support["private_api"]["implementationStatus"] == "planned_contract_only", "private API should stay planned only")
    require(
        source_support["private_database"]["implementationStatus"] == "planned_contract_only",
        "private database should stay planned only",
    )
    require(
        source_support["manual_upload"]["implementationStatus"] == "planned_contract_only",
        "manual upload should stay planned only",
    )
    require(source_support["private_api"]["allowedInCurrentFixture"] is False, "private API should not be fixture-allowed")
    require(
        source_support["private_database"]["allowedInCurrentFixture"] is False,
        "private database should not be fixture-allowed",
    )
    require(source_support["manual_upload"]["allowedInCurrentFixture"] is False, "manual upload should not be fixture-allowed")

    reference = workflow["referenceImplementation"]
    require(reference["referenceDomain"] == "weather-logistics", "reference implementation should use weather-logistics")
    require(reference["forecastId"] == "forecast-1102", "reference implementation should bind forecast-1102")
    require(reference["questionId"] == "question-1102", "reference implementation should bind question-1102")
    require(reference["trackRecordReportId"] == "trackrecord-1102", "reference implementation should bind trackrecord-1102")
    require(reference["implementedNow"] is True, "reference implementation should be implemented now")
    require(
        "quality and calibration claim thresholds" in reference["claimBoundary"],
        "reference claim boundary should mention quality and calibration thresholds",
    )

    guard_names = {item["name"] for item in workflow["guards"]}
    require("private_runtime_boundary" in guard_names, "workflow should guard private runtime boundary")
    require("claim_boundary" in guard_names, "workflow should guard claim boundaries")
    require("source_policy_boundary" in guard_names, "workflow should guard source policy boundaries")

    print("checked private setup workflow")


if __name__ == "__main__":
    main()
