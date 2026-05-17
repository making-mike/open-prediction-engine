#!/usr/bin/env python3
"""Generate or check baseline comparisons for registered forecast methods."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from check_benchmarks import load_json, load_questions, validate_benchmark_run
from check_method_registry import REGISTRY_PATH, benchmark_runs
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "method-comparison"
COMPARISON_PATH = GENERATED / "weather-logistics-method-comparison.generated.json"
GENERATED_AT = "2026-06-06T12:03:00Z"


class MethodComparisonError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def baseline_method_id(registry: dict[str, Any]) -> str:
    baseline_methods = [method["methodId"] for method in registry["methods"] if method["methodClass"] == "baseline"]
    if len(baseline_methods) != 1:
        raise MethodComparisonError("method registry must define exactly one baseline method")
    return baseline_methods[0]


def benchmark_comparison(
    method: dict[str, Any],
    baseline_id: str,
    runs: dict[str, dict[str, Any]],
    questions: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    benchmark = method["benchmarkStatus"]
    item: dict[str, Any] = {
        "methodId": method["methodId"],
        "methodClass": method["methodClass"],
        "status": method["status"],
        "comparisonStatus": "not_comparable",
        "baselineMethodId": baseline_id,
        "sameQuestionSet": False,
        "sameSourcePolicy": False,
        "sameRetrievalWindow": False,
        "leakageValidated": False,
        "sampleSize": int(benchmark.get("sampleSize", 0)),
        "qualityClaimStatus": benchmark["qualityClaimStatus"],
        "reasons": [],
    }

    if benchmark["status"] != "benchmarked":
        item["reasons"].append("benchmark_missing")
        if method["status"] != "enabled":
            item["reasons"].append("method_not_enabled")
        return item

    baseline_run = runs[benchmark["baselineBenchmarkRunId"]]
    candidate_run = runs[benchmark["candidateBenchmarkRunId"]]
    validate_benchmark_run(baseline_run, questions)
    validate_benchmark_run(candidate_run, questions)
    same_question_set = baseline_run["questionIds"] == candidate_run["questionIds"]
    same_source_policy = baseline_run["sourcePolicyId"] == candidate_run["sourcePolicyId"]
    same_retrieval_window = baseline_run["retrievalWindow"] == candidate_run["retrievalWindow"]
    item.update(
        {
            "comparisonStatus": "comparable_checked"
            if same_question_set and same_source_policy and same_retrieval_window and benchmark["leakageValidated"]
            else "not_comparable",
            "baselineBenchmarkRunId": baseline_run["benchmarkRunId"],
            "candidateBenchmarkRunId": candidate_run["benchmarkRunId"],
            "sourcePolicyId": candidate_run["sourcePolicyId"],
            "retrievalWindow": candidate_run["retrievalWindow"],
            "sameQuestionSet": same_question_set,
            "sameSourcePolicy": same_source_policy,
            "sameRetrievalWindow": same_retrieval_window,
            "leakageValidated": bool(benchmark["leakageValidated"]),
            "baselineLift": benchmark["baselineLift"],
        }
    )
    if method["status"] != "enabled":
        item["reasons"].append("method_not_enabled")
    if not same_question_set:
        item["reasons"].append("question_set_mismatch")
    if not same_source_policy:
        item["reasons"].append("source_policy_mismatch")
    if not same_retrieval_window:
        item["reasons"].append("retrieval_window_mismatch")
    if not benchmark["leakageValidated"]:
        item["reasons"].append("leakage_not_validated")
    if item["sampleSize"] < 30:
        item["reasons"].append("sample_below_quality_threshold")
    return item


def build_comparison() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    runs = benchmark_runs()
    questions = load_questions()
    baseline_id = baseline_method_id(registry)
    comparisons = [
        benchmark_comparison(method, baseline_id, runs, questions)
        for method in registry["methods"]
        if method["methodClass"] != "baseline"
    ]
    comparison = {
        "methodComparisonId": "methodcomparison-001",
        "generatedAt": GENERATED_AT,
        "methodRegistryId": registry["methodRegistryId"],
        "domain": registry["domain"],
        "baselineMethodId": baseline_id,
        "comparisons": comparisons,
        "qualityBoundary": {
            "domain": registry["domain"],
            "minimumComparableBenchmarks": registry["selectionPolicy"]["minimumComparableBenchmarks"],
            "qualityClaimStatus": "not_enough_comparable_benchmarks",
        },
        "warnings": [
            "Method comparison is fixture-only and does not make a live performance claim.",
            "Only comparable clean benchmark runs may support baseline-lift claims.",
        ],
    }
    validate_comparison(comparison)
    return comparison


def validate_comparison(comparison: dict[str, Any]) -> None:
    errors = validate_record(comparison, SPEC / "method-comparison.schema.json")
    if errors:
        raise MethodComparisonError(f"method comparison schema validation failed: {errors[0]}")


def write_comparison(comparison: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(render_json(comparison), encoding="utf-8")
    print("generated method comparison")


def check_comparison(comparison: dict[str, Any]) -> None:
    expected = render_json(comparison)
    if not COMPARISON_PATH.exists():
        print(f"missing method comparison: {COMPARISON_PATH}", file=sys.stderr)
        print("run `python3 scripts/compare_forecasting_methods.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = COMPARISON_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"method comparison drift: {COMPARISON_PATH}", file=sys.stderr)
        print("run `python3 scripts/compare_forecasting_methods.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked method comparison")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated method-comparison drift")
    parser.add_argument("--write", action="store_true", help="write generated method comparison")
    args = parser.parse_args()
    try:
        comparison = build_comparison()
    except MethodComparisonError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_comparison(comparison)
    elif args.check:
        check_comparison(comparison)
    else:
        sys.stdout.write(render_json(comparison))


if __name__ == "__main__":
    main()
