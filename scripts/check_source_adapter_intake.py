#!/usr/bin/env python3
"""Check external source-adapter intake invariants."""

from __future__ import annotations

from generate_source_adapter_intake import build_records


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    outputs, reports, gates, decisions, matrix = build_records()
    rows = {row["case"]: row for row in matrix["intakeCases"]}

    require(set(outputs) == {"accepted", "needs_confirmation", "insufficient_data", "rejected", "unsafe"}, "case coverage drifted")
    require(set(rows) == {"accepted", "needs_confirmation", "insufficient_data", "rejected", "unsafe_blocked"}, "matrix status coverage drifted")

    for case, output in outputs.items():
        require(output["adapter"]["implementationLocation"] == "external_agent", f"{case} should model an external adapter")
        require(output["adapter"]["ownsForecastSemantics"] is False, f"{case} adapter must not own forecast semantics")
        require(output["controls"]["forecastGenerationAllowed"] is False, f"{case} adapter must not allow forecasts")
        require(output["controls"]["forecastArtifactsCreated"] is False, f"{case} adapter must not create forecasts")
        require(output["controls"]["sourceIntakeAlreadyRun"] is False, f"{case} adapter output should precede source intake")
        require(output["execution"]["liveFetchPerformed"] is False, f"{case} adapter output should not live fetch")
        require(output["execution"]["credentialsStored"] is False, f"{case} adapter output should not store credentials")
        require(output["provenanceSummary"]["allEvidenceClaimed"] is False, f"{case} adapter output must not claim all evidence")

    accepted = rows["accepted"]
    require(accepted["intakeRoute"]["sourceIntakeStatus"] == "accepted", "accepted output should pass source intake")
    require(accepted["intakeRoute"]["nextAction"] == "proceed_to_method_gating", "accepted output should route to method gates")
    require(accepted["methodGateSummary"]["methodGateStatus"] == "method_selected", "accepted output should select a method")
    require(accepted["methodGateSummary"]["selectedMethodClass"] == "deterministic_statistical", "accepted output should select deterministic method")
    require(reports["accepted"] is not None, "accepted output should produce source intake report")
    require(gates["accepted"] is not None, "accepted output should produce setup benchmark gate")
    require(decisions["accepted"] is not None, "accepted output should produce setup method decision")

    needs = rows["needs_confirmation"]
    require(needs["intakeRoute"]["sourceIntakeStatus"] == "needs_confirmation", "needs-confirmation output should stay pending")
    require(needs["intakeRoute"]["nextAction"] == "ask_mapping_confirmation", "needs-confirmation output should ask for mapping confirmation")
    require(needs["methodGateSummary"]["methodGateStatus"] == "needs_mapping_confirmation", "needs-confirmation output should block method selection")

    insufficient = rows["insufficient_data"]
    require(insufficient["intakeRoute"]["sourceIntakeStatus"] == "rejected", "insufficient data should fail source intake")
    require(insufficient["intakeRoute"]["nextAction"] == "collect_more_data", "insufficient data should route to data collection")
    require("insufficient_comparable_rows" in insufficient["rejectionReasons"], "insufficient data should name comparable rows")
    require("insufficient_positive_outcomes" in insufficient["rejectionReasons"], "insufficient data should name positive outcomes")
    require(insufficient["methodGateSummary"]["methodGateStatus"] == "needs_more_data", "insufficient data should not select method")

    rejected = rows["rejected"]
    require(rejected["intakeRoute"]["nextAction"] == "replace_source", "rejected output should route to source replacement")
    require(rejected["methodGateSummary"]["methodGateStatus"] == "rejected", "rejected output should not select method")

    unsafe = rows["unsafe_blocked"]
    require(outputs["unsafe"]["execution"]["credentialsUsed"] is True, "unsafe example should cross credential boundary")
    require(outputs["unsafe"]["controls"]["promptVisibleCredentialsAccepted"] is True, "unsafe example should expose prompt credential flag")
    require(outputs["unsafe"]["provenanceSummary"]["rawRowsIncluded"] is True, "unsafe example should expose raw-row flag")
    require(unsafe["intakeRoute"]["canEnterSourceIntake"] is False, "unsafe output must not enter source intake")
    require(unsafe["intakeRoute"]["sourceIntakeReportId"] is None, "unsafe output must not produce intake report")
    require(unsafe["intakeRoute"]["nextAction"] == "stop_unsafe_connector", "unsafe output should stop connector handoff")
    require(unsafe["methodGateSummary"]["methodGateStatus"] == "blocked_unsafe", "unsafe output must not reach method gate")

    boundary = matrix["claimBoundary"]
    for key, value in boundary.items():
        require(value is False, f"claim boundary {key} should remain false")

    require(matrix["summary"]["caseCount"] == 5, "matrix should cover five conformance cases")
    require(matrix["summary"]["acceptedCount"] == 1, "matrix should have one accepted case")
    require(matrix["summary"]["needsConfirmationCount"] == 1, "matrix should have one needs-confirmation case")
    require(matrix["summary"]["insufficientDataCount"] == 1, "matrix should have one insufficient-data case")
    require(matrix["summary"]["rejectedCount"] == 1, "matrix should have one rejected case")
    require(matrix["summary"]["unsafeBlockedCount"] == 1, "matrix should have one unsafe-blocked case")
    require(matrix["summary"]["sourceIntakeReportsGenerated"] == 4, "unsafe case should be the only one without source intake report")
    require(matrix["summary"]["methodDecisionsGenerated"] == 4, "unsafe case should be the only one without method decision")

    print("checked source adapter intake invariants")


if __name__ == "__main__":
    main()
