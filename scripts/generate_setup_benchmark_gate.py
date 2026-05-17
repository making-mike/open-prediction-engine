#!/usr/bin/env python3
"""Generate or check setup-specific benchmark gates."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from check_benchmarks import load_questions, validate_benchmark_run
from check_method_registry import REGISTRY_PATH, benchmark_runs
from generate_source_intake import CASE_ORDER, build_reports
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "setup-benchmark"
SCHEMA = SPEC / "setup-benchmark-gate.schema.json"
GENERATED_AT = "2026-06-06T17:40:00Z"
METHOD_CLASS = "deterministic_statistical"
EXECUTION_MINIMUM_SAMPLE_SIZE = 1
MINIMUM_BASELINE_LIFT = 0.0
REQUIRED_ROLES_BY_METHOD = {
    METHOD_CLASS: ["historical_baseline", "weather_forecast"],
}

GATE_IDS = {
    "accepted": "setupbenchmarkgate-001",
    "accepted_partial": "setupbenchmarkgate-002",
    "needs_confirmation": "setupbenchmarkgate-003",
    "rejected": "setupbenchmarkgate-004",
}


class SetupBenchmarkGateError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def gate_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-setup-benchmark-gate.generated.json"


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def method_by_class(registry: dict[str, Any], method_class: str) -> dict[str, Any]:
    matches = [method for method in registry["methods"] if method["methodClass"] == method_class]
    if len(matches) != 1:
        raise SetupBenchmarkGateError(f"expected one method for class {method_class}")
    return matches[0]


def source_summary(report: dict[str, Any]) -> dict[str, Any]:
    usable_roles = sorted(
        item["sourceRole"]
        for item in report["roleCoverage"]
        if item["status"] == "present"
    )
    proposed_mapping_count = sum(
        1 for item in report["mappingDecisions"] if item["decision"] == "proposed"
    )
    rejected_reasons = sorted(
        {
            reason
            for source in report["sourceDecisions"]
            if source["decision"] == "rejected"
            for reason in source["reasonCodes"]
        }
    )
    required_roles = REQUIRED_ROLES_BY_METHOD[METHOD_CLASS]
    missing_roles = sorted(set(required_roles) - set(usable_roles))
    if proposed_mapping_count > 0:
        status = "needs_confirmation"
    elif report["intakeStatus"] == "rejected" or missing_roles or rejected_reasons:
        status = "rejected"
    else:
        status = "eligible"
    return {
        "status": status,
        "requiredSourceRoles": required_roles,
        "usableSourceRoles": usable_roles,
        "missingSourceRoles": missing_roles,
        "mappingConfirmationRequired": proposed_mapping_count > 0,
        "rejectedReasonCodes": rejected_reasons,
    }


def benchmark_evidence(
    registry: dict[str, Any],
    method: dict[str, Any],
    runs: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, bool], dict[str, Any]]:
    benchmark = method["benchmarkStatus"]
    if benchmark["status"] != "benchmarked":
        return (
            {
                "methodRegistryId": registry["methodRegistryId"],
                "baselineBenchmarkRunId": None,
                "candidateBenchmarkRunId": None,
                "sourcePolicyId": None,
                "retrievalWindow": None,
                "questionSetSize": 0,
                "qualityClaimStatus": benchmark["qualityClaimStatus"],
            },
            {
                "sameQuestionSet": False,
                "sameSourcePolicy": False,
                "sameRetrievalWindow": False,
                "leakageValidated": False,
                "sourceTimestampsRecorded": False,
                "resolutionSourcesExcluded": False,
                "trainingCutoffBeforeRetrievalEnd": False,
            },
            benchmark,
        )

    baseline_run = runs[benchmark["baselineBenchmarkRunId"]]
    candidate_run = runs[benchmark["candidateBenchmarkRunId"]]
    validate_benchmark_run(baseline_run, questions)
    validate_benchmark_run(candidate_run, questions)
    retrieval_end = parse_time(candidate_run["retrievalWindow"]["endsAt"])
    training_cutoff = candidate_run["model"].get("trainingCutoff")
    training_ok = training_cutoff is None or parse_time(training_cutoff) <= retrieval_end
    same_question_set = baseline_run["questionIds"] == candidate_run["questionIds"]
    same_source_policy = baseline_run["sourcePolicyId"] == candidate_run["sourcePolicyId"]
    same_retrieval_window = baseline_run["retrievalWindow"] == candidate_run["retrievalWindow"]
    leakage = candidate_run["leakageControls"]
    controls = {
        "sameQuestionSet": same_question_set,
        "sameSourcePolicy": same_source_policy,
        "sameRetrievalWindow": same_retrieval_window,
        "leakageValidated": bool(benchmark["leakageValidated"]),
        "sourceTimestampsRecorded": leakage["sourceTimestampsRecorded"],
        "resolutionSourcesExcluded": leakage["sourceContaminationBlocked"],
        "trainingCutoffBeforeRetrievalEnd": training_ok,
    }
    return (
        {
            "methodRegistryId": registry["methodRegistryId"],
            "baselineBenchmarkRunId": baseline_run["benchmarkRunId"],
            "candidateBenchmarkRunId": candidate_run["benchmarkRunId"],
            "sourcePolicyId": candidate_run["sourcePolicyId"],
            "retrievalWindow": candidate_run["retrievalWindow"],
            "questionSetSize": len(candidate_run["questionIds"]),
            "qualityClaimStatus": benchmark["qualityClaimStatus"],
        },
        controls,
        benchmark,
    )


def reason_codes(
    report: dict[str, Any],
    source: dict[str, Any],
    controls: dict[str, bool],
    metrics: dict[str, Any],
    benchmark: dict[str, Any],
) -> list[str]:
    reasons: set[str] = set()
    if report["intakeStatus"] == "needs_confirmation":
        reasons.add("source_intake_needs_confirmation")
    if report["intakeStatus"] == "rejected":
        reasons.add("source_intake_rejected")
    if source["mappingConfirmationRequired"]:
        reasons.add("mapping_confirmation_required")
    for role in source["missingSourceRoles"]:
        reasons.add(f"missing_{role}")
    reasons.update(source["rejectedReasonCodes"])
    if benchmark["status"] != "benchmarked":
        reasons.add("setup_comparable_benchmark_missing")
    for key, value in controls.items():
        if not value:
            reasons.add(f"{key}_failed")
    if not metrics["executionSampleThresholdMet"]:
        reasons.add("execution_sample_threshold_not_met")
    if metrics["executionSampleThresholdMet"]:
        reasons.add("execution_sample_threshold_met")
    if not metrics["qualitySampleThresholdMet"]:
        reasons.add("quality_sample_threshold_not_met")
    if metrics["baselineLiftPositive"]:
        reasons.add("baseline_lift_positive")
    else:
        reasons.add("baseline_lift_not_positive")
    if source["status"] == "eligible" and all(controls.values()) and metrics["executionSampleThresholdMet"] and metrics["baselineLiftPositive"]:
        reasons.add("setup_benchmark_approved_provisional")
    return sorted(reasons)


def build_gate(
    case: str,
    report: dict[str, Any],
    gate_id: str | None = None,
    source_intake_handoff_id: str | None = None,
) -> dict[str, Any]:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    runs = benchmark_runs()
    questions = load_questions()
    baseline = method_by_class(registry, "baseline")
    method = method_by_class(registry, METHOD_CLASS)
    evidence, controls, benchmark = benchmark_evidence(registry, method, runs, questions)
    source = source_summary(report)
    sample_size = int(benchmark.get("sampleSize", 0))
    baseline_lift = benchmark.get("baselineLift")
    quality_minimum = registry["selectionPolicy"]["minimumComparableBenchmarks"]
    metrics = {
        "sampleSize": sample_size,
        "executionMinimumSampleSize": EXECUTION_MINIMUM_SAMPLE_SIZE,
        "qualityMinimumSampleSize": quality_minimum,
        "baselineLift": baseline_lift,
        "minimumBaselineLift": MINIMUM_BASELINE_LIFT,
        "executionSampleThresholdMet": sample_size >= EXECUTION_MINIMUM_SAMPLE_SIZE,
        "qualitySampleThresholdMet": sample_size >= quality_minimum,
        "baselineLiftPositive": baseline_lift is not None and baseline_lift > MINIMUM_BASELINE_LIFT,
    }
    reasons = reason_codes(report, source, controls, metrics, benchmark)
    execution_allowed = (
        source["status"] == "eligible"
        and all(controls.values())
        and benchmark["status"] == "benchmarked"
        and metrics["executionSampleThresholdMet"]
        and metrics["baselineLiftPositive"]
    )
    gate = {
        "setupBenchmarkGateId": gate_id or GATE_IDS[case],
        "generatedAt": GENERATED_AT,
        "case": case,
        "domainSetupId": report["domainSetupId"],
        "domain": report["domain"],
        "sourceIntakeReportId": report["sourceIntakeReportId"],
        "sourceManifestId": report["sourceManifestId"],
        "fieldMappingId": report["fieldMappingId"],
        "methodClass": METHOD_CLASS,
        "gateStatus": "approved_provisional" if execution_allowed else "blocked",
        "baselineMethodId": baseline["methodId"],
        "candidateMethodId": method["methodId"],
        "benchmarkEvidence": evidence,
        "sourceEligibility": {
            key: source[key]
            for key in [
                "status",
                "requiredSourceRoles",
                "usableSourceRoles",
                "missingSourceRoles",
                "mappingConfirmationRequired",
            ]
        },
        "antiLeakageControls": controls,
        "metricThresholds": metrics,
        "decision": {
            "executionAllowed": execution_allowed,
            "strongerMethodAllowed": execution_allowed,
            "qualityClaimAllowed": False,
            "benchmarkClaimAllowed": False,
            "stateOfTheArtClaimAllowed": False,
        },
        "reasonCodes": reasons,
        "warnings": [
            "Setup benchmark gates may allow fixture execution without allowing quality claims.",
            "Quality, calibration, production, and state-of-the-art claims remain blocked.",
            "Gate status is scoped to this setup, source intake report, method class, and fixture benchmark evidence.",
        ],
    }
    if source_intake_handoff_id is not None:
        gate["sourceIntakeHandoffId"] = source_intake_handoff_id
    errors = validate_record(gate, SCHEMA)
    if errors:
        raise SetupBenchmarkGateError(f"{case} setup benchmark gate schema validation failed: {errors[0]}")
    return gate


def build_gates() -> dict[str, dict[str, Any]]:
    reports = build_reports()
    return {
        case: build_gate(case, reports[case])
        for case in CASE_ORDER
    }


def summary(gates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(gates),
        "gates": [
            {
                "case": case,
                "setupBenchmarkGateId": gate["setupBenchmarkGateId"],
                "domain": gate["domain"],
                "methodClass": gate["methodClass"],
                "gateStatus": gate["gateStatus"],
                "executionAllowed": gate["decision"]["executionAllowed"],
                "qualityClaimAllowed": gate["decision"]["qualityClaimAllowed"],
            }
            for case, gate in gates.items()
        ],
    }


def write_gates(gates: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    expected = {gate_path(case).name for case in gates}
    for path in GENERATED.glob("*.generated.json"):
        if path.name not in expected:
            path.unlink()
    for case, gate in gates.items():
        gate_path(case).write_text(render_json(gate), encoding="utf-8")
    print("generated setup benchmark gates")


def check_gates(gates: dict[str, dict[str, Any]]) -> None:
    errors: list[str] = []
    for case, gate in gates.items():
        path = gate_path(case)
        if not path.exists():
            errors.append(f"missing setup benchmark gate: {path}")
            continue
        if path.read_text(encoding="utf-8") != render_json(gate):
            errors.append(f"setup benchmark gate drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_setup_benchmark_gate.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked setup benchmark gates")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one setup benchmark gate")
    parser.add_argument("--check", action="store_true", help="check generated setup benchmark gate drift")
    parser.add_argument("--write", action="store_true", help="write generated setup benchmark gates")
    args = parser.parse_args()
    try:
        gates = build_gates()
    except SetupBenchmarkGateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_gates(gates)
    elif args.check:
        check_gates(gates)
    elif args.case:
        sys.stdout.write(render_json(gates[args.case]))
    else:
        sys.stdout.write(render_json(summary(gates)))


if __name__ == "__main__":
    main()
