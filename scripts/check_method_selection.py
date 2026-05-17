#!/usr/bin/env python3
"""Check method selection fallback and quality-scope invariants."""

from __future__ import annotations

from select_forecasting_method import DEFAULT_REQUEST, build_selection


def main() -> None:
    selection = build_selection(DEFAULT_REQUEST)
    if selection["selectionStatus"] != "fallback_selected":
        raise AssertionError("auto-evidence fixture should fall back to baseline method")
    if selection["selectedMethodId"] != "method-100":
        raise AssertionError("method selection should choose the baseline fallback")
    if selection["qualityBoundary"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("quality boundary should use the request source policy")
    if selection["qualityBoundary"]["sampleSize"] != 0:
        raise AssertionError("source-policy-specific method quality should have zero comparable samples")
    if selection["qualityBoundary"]["qualityClaimStatus"] != "baseline_selected_due_to_insufficient_method_evidence":
        raise AssertionError("method selection should not make a stronger quality claim")

    candidates = {candidate["methodId"]: candidate for candidate in selection["candidateMethods"]}
    expected_non_baseline = {"method-101", "method-201", "method-301", "method-401", "method-501"}
    if set(candidates) != expected_non_baseline:
        raise AssertionError("method selection should evaluate every non-baseline method")
    if "benchmark_source_policy_mismatch" not in candidates["method-101"]["rejectionReasons"]:
        raise AssertionError("deterministic method should be rejected for source-policy mismatch")
    if "benchmark_sample_below_threshold" not in candidates["method-101"]["rejectionReasons"]:
        raise AssertionError("deterministic method should be rejected for insufficient samples")
    for method_id in ["method-201", "method-301", "method-401", "method-501"]:
        if "method_not_enabled" not in candidates[method_id]["rejectionReasons"]:
            raise AssertionError(f"{method_id} should remain disabled for selection")

    print("checked method selection")


if __name__ == "__main__":
    main()
