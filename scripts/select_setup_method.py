#!/usr/bin/env python3
"""Generate or check setup-aware forecast method decisions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_domain_setups import build_setups
from generate_source_intake import CASE_ORDER, build_reports
from generate_setup_benchmark_gate import build_gates
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "setup-method-decision"
SCHEMA = SPEC / "setup-method-decision.schema.json"
GENERATED_AT = "2026-06-06T17:05:00Z"

DECISION_IDS = {
    "accepted": "setupmethoddecision-001",
    "accepted_partial": "setupmethoddecision-002",
    "needs_confirmation": "setupmethoddecision-003",
    "rejected": "setupmethoddecision-004",
}

METHOD_ORDER = [
    "historical_baseline",
    "historical_conditioned_frequency",
    "deterministic_statistical",
    "model_assisted",
    "external_reference",
    "ensemble",
]

REQUIRED_ROLES_BY_METHOD = {
    "historical_baseline": ["historical_baseline"],
    "historical_conditioned_frequency": ["historical_baseline"],
    "deterministic_statistical": ["historical_baseline", "weather_forecast"],
    "model_assisted": ["historical_baseline", "weather_forecast"],
    "external_reference": ["weather_forecast"],
    "ensemble": ["historical_baseline", "weather_forecast"],
}


class SetupMethodDecisionError(Exception):
    pass


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def decision_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-setup-method-decision.generated.json"


def source_intake_summary(report: dict[str, Any]) -> dict[str, Any]:
    usable_roles = sorted(
        item["sourceRole"]
        for item in report["roleCoverage"]
        if item["status"] == "present"
    )
    missing_required = sorted(
        item["sourceRole"]
        for item in report["roleCoverage"]
        if item["requiredForForecast"] and item["status"] == "missing"
    )
    rejected_roles = sorted(
        item["sourceRole"]
        for item in report["roleCoverage"]
        if item["status"] == "rejected"
    )
    proposed_mapping_count = sum(
        1 for item in report["mappingDecisions"] if item["decision"] == "proposed"
    )
    source_rejection_reasons = sorted(
        {
            reason
            for source in report["sourceDecisions"]
            if source["decision"] == "rejected"
            for reason in source["reasonCodes"]
        }
    )
    return {
        "canProduceForecast": report["canProduceForecast"],
        "forecastGenerationAllowed": report["forecastGenerationAllowed"],
        "usableSourceRoles": usable_roles,
        "missingRequiredRoles": missing_required,
        "rejectedSourceRoles": rejected_roles,
        "proposedMappingCount": proposed_mapping_count,
        "sourceRejectionReasonCodes": source_rejection_reasons,
    }


def candidate_for_method(
    method_class: str,
    setup: dict[str, Any],
    summary: dict[str, Any],
    intake_status: str,
    setup_benchmark_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    enabled = method_class in setup["methodPolicy"]["enabledMethodClasses"]
    required_roles = REQUIRED_ROLES_BY_METHOD[method_class]
    usable_roles = set(summary["usableSourceRoles"])
    missing_roles = sorted(set(required_roles) - usable_roles)
    reason_codes: list[str] = []

    if not enabled:
        reason_codes.append("method_not_enabled_by_setup_policy")
    if summary["rejectedSourceRoles"]:
        reason_codes.append("source_rejected")
        reason_codes.extend(summary["sourceRejectionReasonCodes"])
    if summary["proposedMappingCount"] > 0:
        reason_codes.append("mapping_confirmation_required")
    if missing_roles:
        reason_codes.extend(f"missing_{role}" for role in missing_roles)
    if intake_status == "rejected":
        reason_codes.append("source_intake_rejected")
    if intake_status == "needs_confirmation":
        reason_codes.append("source_intake_needs_confirmation")

    if reason_codes and summary["proposedMappingCount"] > 0 and not summary["rejectedSourceRoles"]:
        source_status = "needs_confirmation"
    elif reason_codes:
        source_status = "rejected"
    else:
        source_status = "eligible"

    setup_benchmark_gate_id = None
    benchmark_quality_claim_status = None
    if method_class == "historical_baseline":
        benchmark_status = "not_required"
    elif not enabled:
        benchmark_status = "rejected"
    elif setup_benchmark_gate is not None:
        setup_benchmark_gate_id = setup_benchmark_gate["setupBenchmarkGateId"]
        benchmark_quality_claim_status = setup_benchmark_gate["benchmarkEvidence"]["qualityClaimStatus"]
        reason_codes.extend(setup_benchmark_gate["reasonCodes"])
        if setup_benchmark_gate["decision"]["executionAllowed"]:
            benchmark_status = "eligible"
        else:
            benchmark_status = "rejected"
    else:
        benchmark_status = "not_benchmarked"
        reason_codes.append("setup_comparable_benchmark_missing")

    if source_status == "needs_confirmation":
        final_status = "needs_confirmation"
    elif source_status == "rejected" or benchmark_status in {"not_benchmarked", "rejected"}:
        final_status = "rejected"
    else:
        final_status = "eligible"

    if final_status == "eligible":
        reason_codes.append("method_eligible_for_setup")

    return {
        "methodClass": method_class,
        "sourceEligibilityStatus": source_status,
        "benchmarkEligibilityStatus": benchmark_status,
        "finalEligibilityStatus": final_status,
        "setupBenchmarkGateId": setup_benchmark_gate_id,
        "benchmarkQualityClaimStatus": benchmark_quality_claim_status,
        "requiredSourceRoles": required_roles,
        "reasonCodes": sorted(set(reason_codes)),
    }


def select_decision_status(candidates: list[dict[str, Any]], report: dict[str, Any]) -> tuple[str, str, str]:
    if report["intakeStatus"] == "rejected":
        return "rejected", "none", "blocked"
    if report["intakeStatus"] == "needs_confirmation":
        return "needs_confirmation", "none", "blocked"

    stronger_candidates = [
        candidate
        for candidate in candidates
        if candidate["methodClass"] != "historical_baseline"
        and candidate["finalEligibilityStatus"] == "eligible"
    ]
    if stronger_candidates:
        selected = stronger_candidates[0]["methodClass"]
        mode = selected if selected != "historical_conditioned_frequency" else "historical_conditioned"
        return "method_selected", selected, mode

    baseline = next(candidate for candidate in candidates if candidate["methodClass"] == "historical_baseline")
    if baseline["finalEligibilityStatus"] == "eligible":
        return "baseline_selected", "historical_baseline", "baseline_only"
    return "rejected", "none", "blocked"


def build_required_actions(
    decision_status: str,
    report: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[str]:
    actions = list(report["requiredActions"])
    if decision_status == "baseline_selected":
        rejected_stronger = [
            candidate for candidate in candidates
            if candidate["methodClass"] != "historical_baseline"
            and candidate["finalEligibilityStatus"] == "rejected"
        ]
        if rejected_stronger:
            actions.append("Use the baseline until stronger methods have confirmed source roles and comparable benchmarks.")
    if decision_status == "needs_confirmation":
        actions.append("Confirm proposed mappings before selecting any forecast method.")
    if decision_status == "rejected":
        actions.append("Resolve rejected source-intake checks before selecting a forecast method.")
    return actions


def quality_boundary(setup: dict[str, Any]) -> dict[str, Any]:
    policy = setup["claimPolicy"]
    return {
        "qualityClaimAllowed": policy["qualityClaimAllowed"],
        "benchmarkClaimAllowed": policy["benchmarkClaimAllowed"],
        "calibrationClaimAllowed": policy["calibrationClaimAllowed"],
        "productionReadinessClaimAllowed": policy["productionReadinessClaimAllowed"],
        "stateOfTheArtClaimAllowed": policy["stateOfTheArtClaimAllowed"],
        "blockedClaims": policy["blockedClaims"],
    }


def gate_for_method(setup_benchmark_gate: dict[str, Any] | None, method_class: str) -> dict[str, Any] | None:
    if setup_benchmark_gate is None:
        return None
    if setup_benchmark_gate["methodClass"] != method_class:
        return None
    return setup_benchmark_gate


def build_decision(
    case: str,
    report: dict[str, Any],
    setup_benchmark_gate: dict[str, Any] | None,
    decision_id: str | None = None,
    source_intake_handoff_id: str | None = None,
) -> dict[str, Any]:
    setup = build_setups()[report["domain"]]
    summary = source_intake_summary(report)
    candidates = [
        candidate_for_method(
            method_class,
            setup,
            summary,
            report["intakeStatus"],
            gate_for_method(setup_benchmark_gate, method_class),
        )
        for method_class in METHOD_ORDER
    ]
    decision_status, selected_method_class, selected_forecast_mode = select_decision_status(candidates, report)
    selected_candidate = next(
        (candidate for candidate in candidates if candidate["methodClass"] == selected_method_class),
        None,
    )
    decision = {
        "setupMethodDecisionId": decision_id or DECISION_IDS[case],
        "generatedAt": GENERATED_AT,
        "domainSetupId": report["domainSetupId"],
        "domain": report["domain"],
        "sourceIntakeReportId": report["sourceIntakeReportId"],
        "sourceManifestId": report["sourceManifestId"],
        "fieldMappingId": report["fieldMappingId"],
        "intakeStatus": report["intakeStatus"],
        "decisionStatus": decision_status,
        "selectedMethodClass": selected_method_class,
        "selectedForecastMode": selected_forecast_mode,
        "selectedSetupBenchmarkGateId": selected_candidate["setupBenchmarkGateId"] if selected_candidate else None,
        "setupPolicy": {
            "baselineRequired": setup["baselinePolicy"]["baselineRequired"],
            "enabledMethodClasses": setup["methodPolicy"]["enabledMethodClasses"],
            "baselineComparisonRequired": setup["methodPolicy"]["baselineComparisonRequired"],
            "leakageCheckRequired": setup["methodPolicy"]["leakageCheckRequired"],
            "methodDecisionRecordRequired": setup["methodPolicy"]["methodDecisionRecordRequired"],
        },
        "sourceIntakeSummary": summary,
        "methodCandidates": candidates,
        "requiredActions": build_required_actions(decision_status, report, candidates),
        "qualityClaimBoundary": quality_boundary(setup),
        "warnings": [
            "Setup method decisions do not create forecast artifacts.",
            "State-of-the-art and best-performance claims remain blocked until benchmark and resolved-outcome evidence meet claim thresholds.",
            "Candidate eligibility is scoped to this domain setup and source intake report.",
        ],
    }
    if source_intake_handoff_id is not None:
        decision["sourceIntakeHandoffId"] = source_intake_handoff_id
    errors = validate_record(decision, SCHEMA)
    if errors:
        raise SetupMethodDecisionError(f"{case} setup method decision schema validation failed: {errors[0]}")
    return decision


def build_decisions() -> dict[str, dict[str, Any]]:
    reports = build_reports()
    gates = build_gates()
    return {
        case: build_decision(case, reports[case], gates.get(case))
        for case in CASE_ORDER
    }


def summary(decisions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(decisions),
        "decisions": [
            {
                "case": case,
                "setupMethodDecisionId": decision["setupMethodDecisionId"],
                "domain": decision["domain"],
                "intakeStatus": decision["intakeStatus"],
                "decisionStatus": decision["decisionStatus"],
                "selectedMethodClass": decision["selectedMethodClass"],
                "selectedForecastMode": decision["selectedForecastMode"],
            }
            for case, decision in decisions.items()
        ],
    }


def write_decisions(decisions: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for case, decision in decisions.items():
        decision_path(case).write_text(render_json(decision), encoding="utf-8")
    print("generated setup method decisions")


def check_decisions(decisions: dict[str, dict[str, Any]]) -> None:
    errors: list[str] = []
    for case, decision in decisions.items():
        path = decision_path(case)
        if not path.exists():
            errors.append(f"missing setup method decision: {path}")
            continue
        if path.read_text(encoding="utf-8") != render_json(decision):
            errors.append(f"setup method decision drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/select_setup_method.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked setup method decisions")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one setup method decision")
    parser.add_argument("--check", action="store_true", help="check generated setup method decision drift")
    parser.add_argument("--write", action="store_true", help="write generated setup method decisions")
    args = parser.parse_args()
    try:
        decisions = build_decisions()
    except SetupMethodDecisionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_decisions(decisions)
    elif args.check:
        check_decisions(decisions)
    elif args.case:
        sys.stdout.write(render_json(decisions[args.case]))
    else:
        sys.stdout.write(render_json(summary(decisions)))


if __name__ == "__main__":
    main()
