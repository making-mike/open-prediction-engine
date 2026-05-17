#!/usr/bin/env python3
"""Check forecasting method registry and comparable benchmark bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from check_benchmarks import load_json, load_questions, validate_benchmark_run
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "spec" / "fixtures" / "methods" / "weather-logistics-method-registry.json"
BENCHMARKS = ROOT / "spec" / "fixtures" / "benchmark"
EXPECTED_METHOD_CLASSES = {
    "baseline",
    "deterministic_statistical",
    "model_assisted",
    "retrieval_assisted",
    "ensemble",
    "external_reference",
}


def benchmark_runs() -> dict[str, dict[str, Any]]:
    return {
        run["benchmarkRunId"]: run
        for run in (
            load_json(path)
            for path in sorted(BENCHMARKS.glob("*.json"))
        )
    }


def assert_registry_shape(registry: dict[str, Any]) -> None:
    errors = validate_record(registry, SPEC / "method-registry.schema.json")
    if errors:
        raise AssertionError(f"method registry schema validation failed: {errors[0]}")

    methods = registry["methods"]
    method_ids = [method["methodId"] for method in methods]
    if len(method_ids) != len(set(method_ids)):
        raise AssertionError("method registry must not contain duplicate method IDs")
    classes = {method["methodClass"] for method in methods}
    if classes != EXPECTED_METHOD_CLASSES:
        raise AssertionError("method registry must define every supported method class")

    available_ids = set(method_ids)
    selection = registry["selectionPolicy"]
    if selection["defaultMethodId"] not in available_ids:
        raise AssertionError("selection default method must exist in registry")
    if selection["fallbackMethodId"] not in available_ids:
        raise AssertionError("selection fallback method must exist in registry")

    baseline_methods = [method for method in methods if method["methodClass"] == "baseline"]
    if len(baseline_methods) != 1:
        raise AssertionError("method registry must define exactly one baseline reference method")


def assert_method_declarations(registry: dict[str, Any]) -> None:
    for method in registry["methods"]:
        model = method["model"]
        if not model.get("modelId") or not model.get("version"):
            raise AssertionError("method must declare model identity and version")
        if method["methodClass"] == "model_assisted" and "trainingCutoff" not in model:
            raise AssertionError("model-assisted methods must declare training cutoff")
        if not method["compatibleDomains"]:
            raise AssertionError("method must declare compatible domains")
        if not method["inputs"]["inputSourceClasses"]:
            raise AssertionError("method must declare input source classes")
        if not method["uncertaintyMethod"]["description"]:
            raise AssertionError("method must declare uncertainty method")
        if not method["knownLimitations"]:
            raise AssertionError("method must declare known limitations")


def assert_enabled_benchmark_bindings(registry: dict[str, Any], runs: dict[str, dict[str, Any]]) -> None:
    questions = load_questions()
    methods = {method["methodId"]: method for method in registry["methods"]}
    minimum = registry["selectionPolicy"]["minimumComparableBenchmarks"]

    for method in registry["methods"]:
        if method["status"] != "enabled" or method["methodClass"] == "baseline":
            continue
        benchmark = method["benchmarkStatus"]
        if benchmark["status"] != "benchmarked":
            raise AssertionError("enabled non-baseline methods must be benchmarked")
        for field in [
            "baselineMethodId",
            "baselineBenchmarkRunId",
            "candidateBenchmarkRunId",
            "sameSourcePolicy",
            "sameRetrievalWindow",
            "leakageValidated",
            "sampleSize",
            "baselineLift",
        ]:
            if field not in benchmark:
                raise AssertionError(f"enabled benchmark status missing {field}")
        if benchmark["baselineMethodId"] not in methods:
            raise AssertionError("benchmark baseline method must exist")
        if benchmark["sameSourcePolicy"] is not True:
            raise AssertionError("enabled method benchmark must use the same source policy as baseline")
        if benchmark["sameRetrievalWindow"] is not True:
            raise AssertionError("enabled method benchmark must use the same retrieval window as baseline")
        if benchmark["leakageValidated"] is not True:
            raise AssertionError("enabled method benchmark must pass leakage validation")

        baseline_run = runs[benchmark["baselineBenchmarkRunId"]]
        candidate_run = runs[benchmark["candidateBenchmarkRunId"]]
        validate_benchmark_run(baseline_run, questions)
        validate_benchmark_run(candidate_run, questions)
        if baseline_run["methodId"] != benchmark["baselineMethodId"]:
            raise AssertionError("baseline benchmark run/method binding mismatch")
        if candidate_run["methodId"] != method["methodId"]:
            raise AssertionError("candidate benchmark run/method binding mismatch")
        if baseline_run["sourcePolicyId"] != candidate_run["sourcePolicyId"]:
            raise AssertionError("candidate benchmark must share source policy with baseline")
        if baseline_run["retrievalWindow"] != candidate_run["retrievalWindow"]:
            raise AssertionError("candidate benchmark must share retrieval window with baseline")
        if baseline_run["questionIds"] != candidate_run["questionIds"]:
            raise AssertionError("candidate benchmark must use same question set as baseline")
        if benchmark["sampleSize"] != len(candidate_run["questionIds"]):
            raise AssertionError("benchmark sample size must match comparable question count")
        if benchmark["sampleSize"] < minimum and benchmark["qualityClaimStatus"] != "not_enough_comparable_benchmarks":
            raise AssertionError("below-threshold methods must not make quality claims")


def main() -> None:
    registry = load_json(REGISTRY_PATH)
    runs = benchmark_runs()
    assert_registry_shape(registry)
    assert_method_declarations(registry)
    assert_enabled_benchmark_bindings(registry, runs)
    print("checked forecasting method registry")


if __name__ == "__main__":
    main()
