#!/usr/bin/env python3
"""Run lightweight hardening checks for release readiness."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

from read_ope_record import PublicError, render_response, validate_artifact_binding
from validate_forecast_request import validate_request


ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "PRODUCT.md",
    ROOT / "roadmap.md",
    ROOT / "whitepaper.md",
    ROOT / "research",
    ROOT / "spec",
    ROOT / "scripts",
    ROOT / ".agents",
    ROOT / ".github",
]
SECRET_PATTERNS = [
    re.compile(r"OPENAI_API_KEY\s*="),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
]


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix in {".md", ".json", ".py", ".toml", ".yaml", ".yml"}:
                yield child


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_secrets() -> None:
    for path in iter_text_files(SCAN_ROOTS):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(ROOT)
                raise AssertionError(f"potential secret pattern in {rel}")


def assert_malformed_artifact_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "broken-artifact.generated.json"
        evidence = root / "broken-evidence.generated.json"
        artifact.write_text(
            json.dumps(
                {
                    "forecastId": "forecast-999",
                    "questionId": "question-999",
                    "evidencePacketId": "evidence-999",
                }
            ),
            encoding="utf-8",
        )
        evidence.write_text(
            json.dumps(
                {
                    "forecastId": "forecast-998",
                    "questionId": "question-999",
                    "evidencePacketId": "evidence-999",
                }
            ),
            encoding="utf-8",
        )
        try:
            validate_artifact_binding(artifact, load_json(artifact))
        except PublicError as exc:
            if exc.code != "binding_mismatch":
                raise
        else:
            raise AssertionError("malformed artifact/evidence binding should fail")


def assert_oversized_io_fails() -> None:
    try:
        render_response({"record": {"large": "x" * 100}}, max_bytes=20)
    except PublicError as exc:
        if exc.code != "response_too_large":
            raise
    else:
        raise AssertionError("oversized read response should fail")

    request = load_json(ROOT / "spec" / "fixtures" / "requests" / "valid-weather-logistics-request.json")
    request["questionText"] = "Will " + ("very " * 160) + "large request pass?"
    decision = validate_request(request)
    if "oversized_input" not in decision["reasonCodes"]:
        raise AssertionError("oversized request text should be rejected")


def assert_unique_ids(label: str, paths: Iterable[Path], id_field: str) -> None:
    seen: dict[str, Path] = {}
    for path in paths:
        data = load_json(path)
        if id_field not in data:
            continue
        value = data[id_field]
        if value in seen:
            first = seen[value].relative_to(ROOT)
            second = path.relative_to(ROOT)
            raise AssertionError(f"duplicate {label} id {value}: {first} and {second}")
        seen[value] = path


def assert_no_duplicate_records() -> None:
    generated = ROOT / "spec" / "fixtures" / "generated"
    requests = ROOT / "spec" / "fixtures" / "requests"
    benchmarks = ROOT / "spec" / "fixtures" / "benchmark"
    assert_unique_ids("forecast artifact", generated.glob("**/*artifact*.json"), "forecastId")
    assert_unique_ids("track record", generated.glob("**/*track-record*.json"), "trackRecordReportId")
    assert_unique_ids("forecast request", requests.glob("*.json"), "requestId")
    assert_unique_ids("benchmark run", benchmarks.glob("*.json"), "benchmarkRunId")


def assert_aggregate_dependency_review() -> None:
    aggregate = load_json(ROOT / "spec" / "fixtures" / "valid" / "weather-logistics-aggregate-forecast.json")
    included = [item for item in aggregate["includedForecasts"] if item.get("included", True)]
    if len({item["forecastId"] for item in included}) != len(included):
        raise AssertionError("aggregate fixture includes duplicate forecast ids")
    if sum(float(item["weight"]) for item in included) <= 0:
        raise AssertionError("aggregate fixture must have positive included weight")
    source_classes = {item["sourceClass"] for item in included}
    independence = aggregate["dependencyAssessment"]["independenceLevel"]
    if {"baseline", "model"}.issubset(source_classes) and independence == "high":
        raise AssertionError("baseline/model aggregate must not claim high independence")


def assert_claim_review_exists() -> None:
    checklist = ROOT / "spec" / "claim-review.md"
    text = checklist.read_text(encoding="utf-8")
    required = ["sample size", "baseline-lift", "fixture", "provisional live"]
    for phrase in required:
        if phrase not in text:
            raise AssertionError(f"claim review checklist missing {phrase!r}")


def main() -> None:
    assert_no_secrets()
    assert_malformed_artifact_fails()
    assert_oversized_io_fails()
    assert_no_duplicate_records()
    assert_aggregate_dependency_review()
    assert_claim_review_exists()
    print("checked hardening guardrails")


if __name__ == "__main__":
    main()
