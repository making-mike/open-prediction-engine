#!/usr/bin/env python3
"""Check source-handoff to setup-method gate boundaries."""

from __future__ import annotations

from generate_source_intake_handoff import CASE_ORDER
from generate_source_handoff_method_gate import build_records
from read_ope_record import RECORD_TYPES


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def method_candidate(decision: dict, method_class: str) -> dict:
    return next(item for item in decision["methodCandidates"] if item["methodClass"] == method_class)


def main() -> None:
    records = build_records()
    require(set(records) == set(CASE_ORDER), "source-handoff method gates should cover every handoff case")

    for case, (summary, _gate, _decision) in records.items():
        require(summary["forecastArtifactsCreated"] is False, f"{case} must not create forecast artifacts")
        require(summary["sourceIntakeHandoffId"].startswith("sourceintakehandoff-"), f"{case} should bind handoff")

    unconfirmed, unconfirmed_gate, unconfirmed_decision = records["unconfirmed_builder_draft"]
    require(unconfirmed["methodGateStatus"] == "needs_mapping_confirmation", "unconfirmed draft should wait for mappings")
    require(unconfirmed["nextAction"] == "ask_mapping_confirmation", "unconfirmed draft should ask for confirmation")
    require(unconfirmed["selectedMethodClass"] == "none", "unconfirmed draft must not select a method")
    require(unconfirmed_gate is not None, "unconfirmed draft should still expose a blocked benchmark gate")
    require(unconfirmed_gate["gateStatus"] == "blocked", "unconfirmed benchmark gate should block execution")
    require(unconfirmed_decision is not None, "unconfirmed draft should expose a blocked method decision")
    require(unconfirmed_decision["decisionStatus"] == "needs_confirmation", "unconfirmed decision should need confirmation")
    require(
        unconfirmed_gate["sourceIntakeHandoffId"] == unconfirmed["sourceIntakeHandoffId"],
        "unconfirmed benchmark gate should bind the handoff",
    )
    require(
        unconfirmed_decision["sourceIntakeHandoffId"] == unconfirmed["sourceIntakeHandoffId"],
        "unconfirmed method decision should bind the handoff",
    )

    confirmed, confirmed_gate, confirmed_decision = records["confirmed_builder_draft"]
    require(confirmed["methodGateStatus"] == "method_selected", "confirmed draft should select a method")
    require(confirmed["nextAction"] == "await_explicit_setup_forecast_execution", "confirmed draft should wait for explicit forecast execution")
    require(confirmed["selectedMethodClass"] == "deterministic_statistical", "confirmed draft should select deterministic method")
    require(confirmed["eligibilitySummary"]["benchmarkExecutionAllowed"] is True, "confirmed draft should pass execution gate")
    require(confirmed_gate is not None, "confirmed draft should expose benchmark gate")
    require(confirmed_gate["gateStatus"] == "approved_provisional", "confirmed benchmark gate should approve provisional execution")
    require(confirmed_gate["decision"]["qualityClaimAllowed"] is False, "confirmed benchmark gate should not allow quality claims")
    require(confirmed_decision is not None, "confirmed draft should expose method decision")
    require(confirmed_decision["decisionStatus"] == "method_selected", "confirmed method decision should select method")
    require(confirmed_decision["selectedSetupBenchmarkGateId"] == confirmed_gate["setupBenchmarkGateId"], "confirmed method should bind benchmark gate")

    insufficient, insufficient_gate, insufficient_decision = records["insufficient_confirmed_builder_draft"]
    require(insufficient["methodGateStatus"] == "needs_more_data", "insufficient draft should request more data")
    require(insufficient["nextAction"] == "collect_more_data", "insufficient draft should collect more data")
    require(insufficient["selectedMethodClass"] == "none", "insufficient draft must not select a method")
    require(insufficient_gate is not None, "insufficient draft should expose blocked benchmark gate")
    require(insufficient_gate["gateStatus"] == "blocked", "insufficient benchmark gate should block execution")
    require(insufficient_decision is not None, "insufficient draft should expose rejected method decision")
    require(insufficient_decision["decisionStatus"] == "rejected", "insufficient method decision should reject")
    baseline = method_candidate(insufficient_decision, "historical_baseline")
    require(
        "insufficient_comparable_rows" in baseline["reasonCodes"],
        "insufficient draft should explain insufficient comparable rows",
    )

    for case in ("contains_secret", "unsupported_format", "oversized", "leakage"):
        summary, gate, decision = records[case]
        require(summary["methodGateStatus"] == "not_entered_source_intake", f"{case} should not enter source intake")
        require(summary["nextAction"] == "replace_rejected_sources", f"{case} should ask for source replacement")
        require(summary["sourceIntakeReportId"] is None, f"{case} should not bind a source-intake report")
        require(summary["setupBenchmarkGateId"] is None, f"{case} should not create a benchmark gate")
        require(summary["setupMethodDecisionId"] is None, f"{case} should not create a method decision")
        require(summary["selectedMethodClass"] == "none", f"{case} must not select a method")
        require(gate is None, f"{case} should not expose benchmark gate")
        require(decision is None, f"{case} should not expose method decision")

    require(
        "source-handoff-method-gate" not in RECORD_TYPES,
        "source-handoff method gates should not become public read surfaces",
    )
    print("checked source handoff method gates")


if __name__ == "__main__":
    main()
