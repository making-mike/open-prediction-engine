#!/usr/bin/env python3
"""Generate or check setup method gates for source-intake handoffs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_setup_benchmark_gate import build_gate
from generate_source_intake_handoff import CASE_ORDER, build_handoffs
from ope_schema import SPEC, validate_record
from select_setup_method import build_decision
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-handoff-method"
SUMMARY_SCHEMA = SPEC / "source-handoff-method-gate.schema.json"
BENCHMARK_SCHEMA = SPEC / "setup-benchmark-gate.schema.json"
DECISION_SCHEMA = SPEC / "setup-method-decision.schema.json"
GENERATED_AT = "2026-06-06T18:35:00Z"

SUMMARY_IDS = {
    "unconfirmed_builder_draft": "sourcehandoffmethodgate-001",
    "confirmed_builder_draft": "sourcehandoffmethodgate-002",
    "insufficient_confirmed_builder_draft": "sourcehandoffmethodgate-003",
    "contains_secret": "sourcehandoffmethodgate-004",
    "unsupported_format": "sourcehandoffmethodgate-005",
    "oversized": "sourcehandoffmethodgate-006",
    "leakage": "sourcehandoffmethodgate-007",
}

BENCHMARK_IDS = {
    "unconfirmed_builder_draft": "setupbenchmarkgate-101",
    "confirmed_builder_draft": "setupbenchmarkgate-102",
    "insufficient_confirmed_builder_draft": "setupbenchmarkgate-103",
}

DECISION_IDS = {
    "unconfirmed_builder_draft": "setupmethoddecision-101",
    "confirmed_builder_draft": "setupmethoddecision-102",
    "insufficient_confirmed_builder_draft": "setupmethoddecision-103",
}


class SourceHandoffMethodGateError(Exception):
    pass


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def paths_for(case: str) -> dict[str, Path]:
    slug = case_slug(case)
    return {
        "summary": GENERATED / f"weather-logistics-{slug}-source-handoff-method-gate.generated.json",
        "benchmark": GENERATED / f"weather-logistics-{slug}-setup-benchmark-gate.generated.json",
        "decision": GENERATED / f"weather-logistics-{slug}-setup-method-decision.generated.json",
    }


def validate_or_raise(record: dict[str, Any], schema: Path, label: str) -> None:
    errors = validate_record(record, schema)
    if errors:
        raise SourceHandoffMethodGateError(f"{label} schema validation failed: {errors[0]}")


def candidate_status(decision: dict[str, Any] | None, method_class: str) -> str | None:
    if decision is None:
        return None
    for candidate in decision["methodCandidates"]:
        if candidate["methodClass"] == method_class:
            return candidate["finalEligibilityStatus"]
    return None


def method_gate_status(handoff: dict[str, Any], decision: dict[str, Any] | None) -> str:
    if handoff["sourceIntakeReportId"] is None:
        return "not_entered_source_intake"
    if handoff["nextAction"] == "ask_mapping_confirmation":
        return "needs_mapping_confirmation"
    if handoff["nextAction"] == "collect_more_data":
        return "needs_more_data"
    if decision is None:
        return "rejected"
    if decision["decisionStatus"] in {"method_selected", "baseline_selected", "rejected"}:
        return decision["decisionStatus"]
    if decision["decisionStatus"] == "needs_confirmation":
        return "needs_mapping_confirmation"
    return "rejected"


def next_action_for(status: str, handoff: dict[str, Any]) -> str:
    if status == "not_entered_source_intake":
        return "replace_rejected_sources"
    if status == "needs_mapping_confirmation":
        return "ask_mapping_confirmation"
    if status == "needs_more_data":
        return "collect_more_data"
    if status in {"method_selected", "baseline_selected"}:
        return "await_explicit_setup_forecast_execution"
    if handoff["nextAction"] == "replace_rejected_sources":
        return "replace_rejected_sources"
    return "review_method_rejection"


def actions_for(status: str, next_action: str, handoff: dict[str, Any], decision: dict[str, Any] | None) -> list[str]:
    if next_action == "await_explicit_setup_forecast_execution":
        return ["Method gate passed; run an explicit setup forecast execution step before any forecast artifact is created."]
    if decision is not None and decision["requiredActions"]:
        return decision["requiredActions"]
    if handoff["requiredActions"]:
        return handoff["requiredActions"]
    return [f"Resolve source handoff method gate status {status}."]


def warnings_for(handoff: dict[str, Any], decision: dict[str, Any] | None) -> list[str]:
    warnings = [
        "Source-handoff method gates do not create forecast artifacts.",
        "Accepted method decisions still require an explicit setup forecast execution step.",
    ]
    warnings.extend(handoff["warnings"])
    if decision is not None:
        warnings.extend(decision["warnings"])
    return list(dict.fromkeys(warnings))


def build_case(case: str) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    handoff = build_handoffs()[case][0]
    benchmark_gate = None
    decision = None
    if handoff["sourceIntakeReportId"] is not None:
        report = build_handoffs()[case][4]
        if report is None:
            raise SourceHandoffMethodGateError(f"{case} handoff expected a source intake report")
        benchmark_gate = build_gate(
            case,
            report,
            gate_id=BENCHMARK_IDS[case],
            source_intake_handoff_id=handoff["sourceIntakeHandoffId"],
        )
        decision = build_decision(
            case,
            report,
            benchmark_gate,
            decision_id=DECISION_IDS[case],
            source_intake_handoff_id=handoff["sourceIntakeHandoffId"],
        )
    status = method_gate_status(handoff, decision)
    next_action = next_action_for(status, handoff)
    summary = {
        "sourceHandoffMethodGateId": SUMMARY_IDS[case],
        "generatedAt": GENERATED_AT,
        "case": case,
        "domainSetupId": handoff["domainSetupId"],
        "domain": handoff["domain"],
        "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
        "sourceIntakeReportId": handoff["sourceIntakeReportId"],
        "setupBenchmarkGateId": benchmark_gate["setupBenchmarkGateId"] if benchmark_gate is not None else None,
        "setupMethodDecisionId": decision["setupMethodDecisionId"] if decision is not None else None,
        "handoffStatus": handoff["handoffStatus"],
        "handoffNextAction": handoff["nextAction"],
        "methodGateStatus": status,
        "nextAction": next_action,
        "sourceIntakeStatus": handoff["sourceIntakeStatus"],
        "selectedMethodClass": decision["selectedMethodClass"] if decision is not None else "none",
        "selectedForecastMode": decision["selectedForecastMode"] if decision is not None else "blocked",
        "forecastArtifactsCreated": False,
        "eligibilitySummary": {
            "benchmarkGateStatus": benchmark_gate["gateStatus"] if benchmark_gate is not None else None,
            "benchmarkExecutionAllowed": benchmark_gate["decision"]["executionAllowed"] if benchmark_gate is not None else None,
            "methodDecisionStatus": decision["decisionStatus"] if decision is not None else None,
            "baselineFinalEligibilityStatus": candidate_status(decision, "historical_baseline"),
            "deterministicFinalEligibilityStatus": candidate_status(decision, "deterministic_statistical"),
            "qualityClaimAllowed": decision["qualityClaimBoundary"]["qualityClaimAllowed"] if decision is not None else None,
        },
        "requiredActions": actions_for(status, next_action, handoff, decision),
        "warnings": warnings_for(handoff, decision),
    }
    validate_or_raise(summary, SUMMARY_SCHEMA, "source handoff method gate")
    if benchmark_gate is not None:
        validate_or_raise(benchmark_gate, BENCHMARK_SCHEMA, "setup benchmark gate")
    if decision is not None:
        validate_or_raise(decision, DECISION_SCHEMA, "setup method decision")
    return summary, benchmark_gate, decision


def build_records() -> dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]]:
    return {case: build_case(case) for case in CASE_ORDER}


def load_generated_records() -> dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]] | None:
    records: dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]] = {}
    for case in CASE_ORDER:
        paths = paths_for(case)
        if not paths["summary"].exists():
            return None
        summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
        validate_or_raise(summary, SUMMARY_SCHEMA, "source handoff method gate")

        benchmark_gate = None
        if paths["benchmark"].exists():
            benchmark_gate = json.loads(paths["benchmark"].read_text(encoding="utf-8"))
            validate_or_raise(benchmark_gate, BENCHMARK_SCHEMA, "setup benchmark gate")

        decision = None
        if paths["decision"].exists():
            decision = json.loads(paths["decision"].read_text(encoding="utf-8"))
            validate_or_raise(decision, DECISION_SCHEMA, "setup method decision")

        records[case] = (summary, benchmark_gate, decision)
    return records


def write_outputs(records: dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for case, (summary, benchmark_gate, decision) in records.items():
        paths = paths_for(case)
        paths["summary"].write_text(render_json(summary), encoding="utf-8")
        if benchmark_gate is not None:
            paths["benchmark"].write_text(render_json(benchmark_gate), encoding="utf-8")
        if decision is not None:
            paths["decision"].write_text(render_json(decision), encoding="utf-8")
    print("generated source handoff method gates")


def check_outputs(records: dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]]) -> None:
    expected: dict[Path, str] = {}
    for case, (summary, benchmark_gate, decision) in records.items():
        paths = paths_for(case)
        expected[paths["summary"]] = render_json(summary)
        if benchmark_gate is not None:
            expected[paths["benchmark"]] = render_json(benchmark_gate)
        if decision is not None:
            expected[paths["decision"]] = render_json(decision)
    errors = []
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing source handoff method gate output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"source handoff method gate drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_source_handoff_method_gate.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source handoff method gates")


def summary(records: dict[str, tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]]) -> dict[str, Any]:
    return {
        "count": len(records),
        "methodGates": [
            {
                "case": case,
                "sourceHandoffMethodGateId": record["sourceHandoffMethodGateId"],
                "handoffNextAction": record["handoffNextAction"],
                "methodGateStatus": record["methodGateStatus"],
                "nextAction": record["nextAction"],
                "sourceIntakeStatus": record["sourceIntakeStatus"],
                "selectedMethodClass": record["selectedMethodClass"],
                "forecastArtifactsCreated": record["forecastArtifactsCreated"],
            }
            for case, (record, _benchmark_gate, _decision) in records.items()
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source handoff method gate summary")
    parser.add_argument("--check", action="store_true", help="check generated source handoff method gate drift")
    parser.add_argument("--write", action="store_true", help="write generated source handoff method gate records")
    args = parser.parse_args()
    try:
        if args.write or args.check:
            records = build_records()
        else:
            records = load_generated_records() or build_records()
    except SourceHandoffMethodGateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(records)
    elif args.check:
        check_outputs(records)
    elif args.case:
        sys.stdout.write(render_json(records[args.case][0]))
    else:
        sys.stdout.write(render_json(summary(records)))


if __name__ == "__main__":
    main()
