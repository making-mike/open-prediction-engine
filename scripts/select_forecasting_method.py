#!/usr/bin/env python3
"""Select a forecast method from the registry for the auto-evidence fixture request."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from check_method_registry import REGISTRY_PATH, benchmark_runs
from ope_schema import SPEC, validate_record
from validate_forecast_request import load_json


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REQUEST = ROOT / "spec" / "fixtures" / "requests" / "auto-weather-logistics-request.json"
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "method-selection"
SELECTION_PATH = GENERATED / "weather-logistics-method-selection.generated.json"
GENERATED_AT = "2026-06-06T12:05:00Z"


class MethodSelectionError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def compatible(method: dict[str, Any], request: dict[str, Any]) -> bool:
    for item in method["compatibleDomains"]:
        if item["domain"] != request["domain"]:
            continue
        if request["horizonLabel"] not in item["horizonBuckets"]:
            continue
        if request["outputType"] not in item["outputTypes"]:
            continue
        return True
    return False


def method_candidates(
    registry: dict[str, Any],
    request: dict[str, Any],
    runs: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = []
    minimum = registry["selectionPolicy"]["minimumComparableBenchmarks"]
    source_policy_id = request["sourcePolicy"]["sourcePolicyId"]
    for method in registry["methods"]:
        if method["methodClass"] == "baseline" or not compatible(method, request):
            continue

        benchmark = method["benchmarkStatus"]
        rejection_reasons: list[str] = []
        candidate: dict[str, Any] = {
            "methodId": method["methodId"],
            "methodClass": method["methodClass"],
            "status": method["status"],
            "eligibilityStatus": "eligible",
            "benchmarkStatus": "not_benchmarked"
            if benchmark["status"] == "not_required"
            else benchmark["status"],
            "sampleSize": int(benchmark.get("sampleSize", 0)),
            "rejectionReasons": rejection_reasons,
        }

        if method["status"] != "enabled":
            rejection_reasons.append("method_not_enabled")
        if benchmark["status"] != "benchmarked":
            rejection_reasons.append("benchmark_missing")

        run_id = benchmark.get("candidateBenchmarkRunId")
        if run_id:
            candidate["candidateBenchmarkRunId"] = run_id
            run = runs[run_id]
            candidate["benchmarkSourcePolicyId"] = run["sourcePolicyId"]
            if run["sourcePolicyId"] != source_policy_id:
                rejection_reasons.append("benchmark_source_policy_mismatch")
        if "baselineLift" in benchmark:
            candidate["baselineLift"] = benchmark["baselineLift"]
        if benchmark.get("sameSourcePolicy") is not True and benchmark["status"] == "benchmarked":
            rejection_reasons.append("baseline_comparison_policy_mismatch")
        if benchmark.get("sameRetrievalWindow") is not True and benchmark["status"] == "benchmarked":
            rejection_reasons.append("baseline_comparison_window_mismatch")
        if benchmark.get("leakageValidated") is not True and benchmark["status"] == "benchmarked":
            rejection_reasons.append("leakage_not_validated")
        if candidate["sampleSize"] < minimum:
            rejection_reasons.append("benchmark_sample_below_threshold")
        if rejection_reasons:
            candidate["eligibilityStatus"] = "rejected"
        candidates.append(candidate)
    return candidates


def select_method(registry: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    eligible = [candidate for candidate in candidates if candidate["eligibilityStatus"] == "eligible"]
    if not eligible:
        return registry["selectionPolicy"]["fallbackMethodId"]
    eligible.sort(key=lambda item: item.get("baselineLift", 0), reverse=True)
    return eligible[0]["methodId"]


def build_selection(request_path: Path = DEFAULT_REQUEST) -> dict[str, Any]:
    request = load_json(request_path)
    registry = load_json(REGISTRY_PATH)
    runs = benchmark_runs()
    methods = {method["methodId"]: method for method in registry["methods"]}
    candidates = method_candidates(registry, request, runs)
    selected_method_id = select_method(registry, candidates)
    selected = methods[selected_method_id]
    fallback_id = registry["selectionPolicy"]["fallbackMethodId"]
    selected_is_fallback = selected_method_id == fallback_id
    source_policy = request["sourcePolicy"]
    selection = {
        "methodSelectionId": "methodselection-001",
        "generatedAt": GENERATED_AT,
        "requestId": request["requestId"],
        "methodRegistryId": registry["methodRegistryId"],
        "domain": request["domain"],
        "horizonBucket": request["horizonLabel"],
        "outputType": request["outputType"],
        "sourcePolicyId": source_policy["sourcePolicyId"],
        "selectionStatus": "fallback_selected" if selected_is_fallback else "candidate_selected",
        "selectedMethodId": selected["methodId"],
        "selectedMethodClass": selected["methodClass"],
        "selectedModel": selected["model"],
        "fallbackMethodId": fallback_id,
        "candidateMethods": candidates,
        "qualityBoundary": {
            "domain": request["domain"],
            "horizonBucket": request["horizonLabel"],
            "outputType": request["outputType"],
            "sourcePolicyId": source_policy["sourcePolicyId"],
            "coveragePeriod": source_policy["retrievalWindow"],
            "sampleSize": 0 if selected_is_fallback else max(item["sampleSize"] for item in candidates),
            "minimumComparableBenchmarks": registry["selectionPolicy"]["minimumComparableBenchmarks"],
            "qualityClaimStatus": "baseline_selected_due_to_insufficient_method_evidence"
            if selected_is_fallback
            else "not_enough_comparable_benchmarks",
        },
        "selectionReasons": [
            registry["selectionPolicy"]["insufficientEvidenceRule"]
            if selected_is_fallback
            else "Selected the eligible non-baseline method with the strongest checked baseline lift.",
            "No enabled non-baseline method has enough comparable benchmark evidence for this source policy.",
        ],
        "warnings": [
            "Method selection is fixture-only and does not make a live performance claim.",
            "Quality is scoped to domain, horizon, output type, source policy, coverage period, and sample size.",
        ],
    }
    validate_selection(selection)
    return selection


def validate_selection(selection: dict[str, Any]) -> None:
    errors = validate_record(selection, SPEC / "method-selection.schema.json")
    if errors:
        raise MethodSelectionError(f"method selection schema validation failed: {errors[0]}")


def write_selection(selection: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    SELECTION_PATH.write_text(render_json(selection), encoding="utf-8")
    print("generated method selection")


def check_selection(selection: dict[str, Any]) -> None:
    expected = render_json(selection)
    if not SELECTION_PATH.exists():
        print(f"missing method selection: {SELECTION_PATH}", file=sys.stderr)
        print("run `python3 scripts/select_forecasting_method.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = SELECTION_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"method selection drift: {SELECTION_PATH}", file=sys.stderr)
        print("run `python3 scripts/select_forecasting_method.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked method selection")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, default=DEFAULT_REQUEST)
    parser.add_argument("--check", action="store_true", help="check generated method-selection drift")
    parser.add_argument("--write", action="store_true", help="write generated method selection")
    args = parser.parse_args()
    try:
        selection = build_selection(args.request)
    except MethodSelectionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_selection(selection)
    elif args.check:
        check_selection(selection)
    else:
        sys.stdout.write(render_json(selection))


if __name__ == "__main__":
    main()
