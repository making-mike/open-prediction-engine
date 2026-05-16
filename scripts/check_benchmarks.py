#!/usr/bin/env python3
"""Check benchmark anti-leakage fixtures without external deps."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / "spec" / "fixtures" / "benchmark"
FIXTURE_LOOP = ROOT / "spec" / "fixtures" / "generated" / "fixture-loop"
VALID_BENCHMARKS = ["clean-pre-outcome-run.json"]
INVALID_BENCHMARKS = ["post-outcome-leakage-run.json"]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def load_questions() -> dict[str, dict[str, Any]]:
    questions: dict[str, dict[str, Any]] = {}
    for path in sorted(FIXTURE_LOOP.glob("*-question.generated.json")):
        question = load_json(path)
        questions[question["questionId"]] = question
    if not questions:
        raise AssertionError("benchmark checks require generated fixture-loop questions")
    return questions


def resolution_source_ids(question: dict[str, Any]) -> set[str]:
    source_ids = {question["primaryResolutionSource"]["sourceId"]}
    source_ids.update(
        source["sourceId"]
        for source in question.get("fallbackResolutionSources", [])
    )
    return source_ids


def validate_benchmark_run(run: dict[str, Any], questions: dict[str, dict[str, Any]]) -> None:
    retrieval_end = parse_time(run["retrievalWindow"]["endsAt"])
    controls = run["leakageControls"]

    for control_name in [
        "knownAnswerExcluded",
        "postOutcomeDataBlocked",
        "sourceTimestampsRecorded",
    ]:
        if controls[control_name] is not True:
            raise AssertionError(f"{run['benchmarkRunId']} failed leakage control {control_name}")

    training_cutoff = run["model"].get("trainingCutoff")
    if training_cutoff and parse_time(training_cutoff) > retrieval_end:
        raise AssertionError(f"{run['benchmarkRunId']} model training cutoff is after retrieval window")

    blocked_source_ids: set[str] = set()
    close_times: list[datetime] = []
    for question_id in run["questionIds"]:
        if question_id not in questions:
            raise AssertionError(f"{run['benchmarkRunId']} references unknown question {question_id}")
        question = questions[question_id]
        blocked_source_ids.update(resolution_source_ids(question))
        close_times.append(parse_time(question["closeAt"]))

    if retrieval_end > min(close_times):
        raise AssertionError(f"{run['benchmarkRunId']} retrieval window extends past question close")

    for source in run.get("sourceFetches", []):
        source_id = source["sourceId"]
        if source_id in blocked_source_ids:
            raise AssertionError(f"{run['benchmarkRunId']} fetched resolution source {source_id}")
        if "retrievedAt" not in source:
            raise AssertionError(f"{run['benchmarkRunId']} source {source_id} is missing retrievedAt")
        if "contentHash" not in source:
            raise AssertionError(f"{run['benchmarkRunId']} source {source_id} is missing contentHash")
        if parse_time(source["retrievedAt"]) > retrieval_end:
            raise AssertionError(f"{run['benchmarkRunId']} source {source_id} was fetched after retrieval window")


def expect_failure(path: Path, questions: dict[str, dict[str, Any]]) -> None:
    run = load_json(path)
    try:
        validate_benchmark_run(run, questions)
    except AssertionError:
        return
    raise AssertionError(f"{path.name} should fail anti-leakage validation")


def main() -> None:
    questions = load_questions()
    for filename in VALID_BENCHMARKS:
        validate_benchmark_run(load_json(BENCHMARKS / filename), questions)
    for filename in INVALID_BENCHMARKS:
        expect_failure(BENCHMARKS / filename, questions)
    print(
        f"checked {len(VALID_BENCHMARKS)} clean and "
        f"{len(INVALID_BENCHMARKS)} contaminated benchmark fixtures"
    )


if __name__ == "__main__":
    main()
