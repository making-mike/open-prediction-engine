#!/usr/bin/env python3
"""Check source quality and mapping confidence readbacks."""

from __future__ import annotations

from generate_source_quality_mapping_confidence import CASE_ORDER, DIMENSION_KEYS, build_model


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    model = build_model()
    rows = model["caseRows"]
    rows_by_case = {row["case"]: row for row in rows}
    summary = model["summary"]
    compact = model["compactReadback"]
    boundary = model["executionBoundary"]

    require([row["case"] for row in rows] == CASE_ORDER, "source quality case order drifted")
    require(
        {binding["surface"] for binding in model["surfaceBindings"]} == {
            "source_builder",
            "source_adapter_intake",
            "source_intake_report",
            "setup_method_decision",
        },
        "source quality surface bindings should cover builder, adapter intake, source intake, and method decisions",
    )
    for row in rows:
        require(set(row["dimensions"]) == set(DIMENSION_KEYS), f"{row['case']} dimension coverage drifted")
        require(row["forecastImpact"]["forecastArtifactsCreated"] is False, "source quality must not create forecasts")
        require(row["forecastImpact"]["qualityClaimAllowed"] is False, "source quality must not allow quality claims")
        require(
            row["forecastImpact"]["productionReadinessClaimAllowed"] is False,
            "source quality must not allow production-readiness claims",
        )

    accepted = rows_by_case["source_intake_accepted"]
    require(accepted["qualityStatus"] == "forecast_usable", "accepted source intake should be forecast-usable")
    require(accepted["recommendedNextAction"] == "proceed_to_method_gate", "accepted source intake should proceed to method gate")
    require(accepted["dimensions"]["freshness"]["status"] == "passed", "accepted source freshness should pass")
    require(accepted["dimensions"]["mappingConfidence"]["status"] == "passed", "accepted source mappings should pass")
    require(accepted["forecastImpact"]["canProceedToMethodGate"] is True, "accepted source should proceed to method gate")

    partial = rows_by_case["source_intake_partial"]
    require(partial["qualityStatus"] == "baseline_only_usable", "partial source intake should be baseline-only usable")
    require(partial["dimensions"]["roleFit"]["status"] == "partial", "partial source intake should show role-fit gap")
    require(partial["forecastImpact"]["selectedMethodClass"] == "historical_baseline", "partial source should select baseline")

    builder = rows_by_case["builder_local_draft"]
    require(builder["qualityStatus"] == "needs_mapping_confirmation", "builder draft should require mapping confirmation")
    require(builder["forecastImpact"]["canProduceForecast"] is False, "builder draft should not produce forecasts")
    require(builder["boundRecordIds"]["sourceManifestBuildId"] is not None, "builder draft should bind source build record")

    needs = rows_by_case["source_intake_needs_confirmation"]
    require(needs["recommendedNextAction"] == "confirm_mappings", "needs-confirmation case should ask for mapping confirmation")
    require(
        needs["dimensions"]["mappingConfidence"]["status"] == "needs_confirmation",
        "needs-confirmation case should expose mapping confidence gap",
    )

    insufficient = rows_by_case["adapter_insufficient_data"]
    require(insufficient["recommendedNextAction"] == "collect_more_data", "insufficient adapter case should collect more data")
    require(insufficient["dimensions"]["coverage"]["status"] == "failed", "insufficient adapter case should fail coverage")
    require(
        insufficient["boundRecordIds"]["sourceAdapterIntakeCaseId"] is not None,
        "insufficient adapter case should bind adapter intake case",
    )

    rejected = rows_by_case["source_intake_rejected"]
    require(rejected["recommendedNextAction"] == "replace_source", "rejected source intake should replace source")
    require(rejected["dimensions"]["leakageRisk"]["status"] == "failed", "rejected source intake should fail leakage risk")

    unsafe = rows_by_case["adapter_unsafe"]
    require(unsafe["recommendedNextAction"] == "stop_unsafe_connector", "unsafe adapter should stop connector")
    require(
        all(dimension["status"] == "blocked" for dimension in unsafe["dimensions"].values()),
        "unsafe adapter dimensions should stay blocked",
    )
    require(unsafe["forecastImpact"]["canEnterSourceIntake"] is False, "unsafe adapter must not enter source intake")

    require(summary["caseCount"] == 7, "source quality should expose seven cases")
    require(summary["forecastUsableCount"] == 1, "source quality forecast-usable count drifted")
    require(summary["baselineOnlyCount"] == 1, "source quality baseline-only count drifted")
    require(summary["needsMappingConfirmationCount"] == 2, "source quality mapping-confirmation count drifted")
    require(summary["needsMoreDataCount"] == 1, "source quality needs-more-data count drifted")
    require(summary["replaceSourceCount"] == 1, "source quality replace-source count drifted")
    require(summary["stopUnsafeConnectorCount"] == 1, "source quality unsafe count drifted")
    require(summary["qualityClaimAllowed"] is False, "source quality must keep quality claims blocked")
    require(summary["productionReadinessClaimAllowed"] is False, "source quality must keep production claims blocked")

    require(compact["fitsBudget"] is True, "compact source quality readback should fit budget")
    require(compact["measuredBytes"] <= compact["maxBytes"], "compact source quality readback exceeded budget")
    require(compact["includesRawRows"] is False, "compact source quality readback must not include raw rows")
    require(compact["includesRawPrompts"] is False, "compact source quality readback must not include raw prompts")
    require(compact["includesCredentials"] is False, "compact source quality readback must not include credentials")

    require(boundary["readOnly"] is True, "source quality readback should be read-only")
    require(boundary["normalChecksDeterministicOffline"] is True, "source quality normal checks should be offline")
    for key, value in boundary.items():
        if key in {"readOnly", "normalChecksDeterministicOffline"}:
            continue
        require(value is False, f"source quality boundary {key} should remain false")

    print("checked source quality mapping confidence")


if __name__ == "__main__":
    main()
