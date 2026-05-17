#!/usr/bin/env python3
"""Check method comparison coverage and claim boundaries."""

from __future__ import annotations

from compare_forecasting_methods import build_comparison


def main() -> None:
    comparison = build_comparison()
    if comparison["baselineMethodId"] != "method-100":
        raise AssertionError("method comparison should use the registered baseline")
    comparisons = {item["methodId"]: item for item in comparison["comparisons"]}
    expected = {"method-101", "method-201", "method-301", "method-401", "method-501"}
    if set(comparisons) != expected:
        raise AssertionError("method comparison should cover every non-baseline method")

    deterministic = comparisons["method-101"]
    if deterministic["comparisonStatus"] != "comparable_checked":
        raise AssertionError("deterministic method should have a checked baseline comparison")
    if deterministic["sameSourcePolicy"] is not True:
        raise AssertionError("deterministic comparison should share baseline source policy")
    if deterministic["sameRetrievalWindow"] is not True:
        raise AssertionError("deterministic comparison should share baseline retrieval window")
    if deterministic["baselineLift"] != 0.2603:
        raise AssertionError("deterministic method should preserve checked baseline lift")
    if "sample_below_quality_threshold" not in deterministic["reasons"]:
        raise AssertionError("deterministic comparison should remain below quality threshold")

    for method_id in ["method-201", "method-301", "method-401", "method-501"]:
        item = comparisons[method_id]
        if item["comparisonStatus"] != "not_comparable":
            raise AssertionError(f"{method_id} should not be comparable yet")
        if "benchmark_missing" not in item["reasons"]:
            raise AssertionError(f"{method_id} should explain missing benchmark evidence")

    if comparison["qualityBoundary"]["qualityClaimStatus"] != "not_enough_comparable_benchmarks":
        raise AssertionError("comparison report must not make stronger quality claims")

    print("checked method comparison")


if __name__ == "__main__":
    main()
