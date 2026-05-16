#!/usr/bin/env python3
"""Read public OPE generated records without triggering forecast generation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated"
DEFAULT_MAX_BYTES = 65536
MAX_RECORDS_PER_REQUEST = 1
MAX_LIST_RECORDS = 100
RECORD_TYPES = {
    "forecast-bundle": {
        "glob": "**/*artifact*.json",
        "id_field": "forecastId",
    },
    "forecast-card": {
        "glob": "**/*artifact*.json",
        "id_field": "forecastId",
    },
    "forecast-artifact": {
        "glob": "**/*artifact*.json",
        "id_field": "forecastId",
    },
    "track-record": {
        "glob": "**/*track-record*.json",
        "id_field": "trackRecordReportId",
    },
}


class PublicError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_time(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def is_embargoed(access_policy: dict[str, Any], now: datetime) -> bool:
    embargo_until = access_policy.get("embargoUntil")
    return isinstance(embargo_until, str) and parse_time(embargo_until) > now


def assert_public_access(record: dict[str, Any], now: datetime | None = None) -> None:
    policy = record.get("accessPolicy", {"visibility": "public"})
    if not isinstance(policy, dict):
        raise PublicError("access_denied", "Record access policy is invalid.")
    visibility = policy.get("visibility", "public")
    if visibility not in {"public", "private", "embargoed"}:
        raise PublicError("access_denied", "Record access policy is invalid.")
    now = now or datetime.now(timezone.utc)
    if visibility == "private" or visibility == "embargoed" or is_embargoed(policy, now):
        raise PublicError("access_denied", "Record is not public.")


def candidate_records(record_type: str) -> list[tuple[Path, dict[str, Any]]]:
    if record_type not in RECORD_TYPES:
        raise PublicError("bad_request", "Unsupported record type.")
    config = RECORD_TYPES[record_type]
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(GENERATED.glob(str(config["glob"]))):
        data = load_json(path)
        if config["id_field"] in data:
            records.append((path, data))
    return records


def find_record(record_type: str, record_id: str) -> tuple[Path, dict[str, Any]]:
    config = RECORD_TYPES[record_type]
    matches = [
        (path, record)
        for path, record in candidate_records(record_type)
        if record.get(config["id_field"]) == record_id
    ]
    if not matches:
        raise PublicError("not_found", "Record was not found.")
    if len(matches) > 1:
        raise PublicError("conflict", "Record ID is not unique.")
    return matches[0]


def sibling(path: Path, suffix: str) -> Path:
    name = path.name
    marker = "-artifact.generated.json"
    if marker in name:
        return path.with_name(name.replace(marker, suffix))
    return path


def validate_artifact_binding(path: Path, artifact: dict[str, Any]) -> None:
    evidence_path = sibling(path, "-evidence.generated.json")
    if not evidence_path.exists():
        return
    evidence = load_json(evidence_path)
    if artifact["forecastId"] != evidence.get("forecastId"):
        raise PublicError("binding_mismatch", "Record binding validation failed.")
    if artifact["questionId"] != evidence.get("questionId"):
        raise PublicError("binding_mismatch", "Record binding validation failed.")
    if artifact["evidencePacketId"] != evidence.get("evidencePacketId"):
        raise PublicError("binding_mismatch", "Record binding validation failed.")


def find_generated_record(
    label: str,
    glob_pattern: str,
    predicate: Any,
    *,
    required: bool,
) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(GENERATED.glob(glob_pattern)):
        data = load_json(path)
        if predicate(data):
            matches.append((path, data))
    if not matches:
        if required:
            raise PublicError("not_found", f"{label} was not found.")
        return None
    if len(matches) > 1:
        raise PublicError("conflict", f"{label} is not unique.")
    return matches[0]


def find_optional_related_record(
    label: str,
    glob_pattern: str,
    predicate: Any,
) -> tuple[Path, dict[str, Any]] | None:
    try:
        return find_generated_record(label, glob_pattern, predicate, required=False)
    except PublicError as exc:
        if exc.code == "conflict":
            return None
        raise


def find_forecast_question(question_id: str) -> tuple[Path, dict[str, Any]] | None:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(GENERATED.glob("**/*question.generated.json")):
        data = load_json(path)
        if data.get("questionId") == question_id:
            matches.append((path, data))
    if not matches:
        return None
    terminal = [
        item
        for item in matches
        if item[1].get("status") in {"resolved", "ambiguous", "annulled", "re_resolved"}
    ]
    if len(terminal) == 1:
        return terminal[0]
    if len(matches) == 1:
        return matches[0]
    return None


def assert_related_public(path_record: tuple[Path, dict[str, Any]] | None) -> dict[str, Any] | None:
    if path_record is None:
        return None
    _path, record = path_record
    assert_public_access(record)
    return record


def build_forecast_bundle(path: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    validate_artifact_binding(path, artifact)
    evidence = assert_related_public(
        find_generated_record(
            "Evidence packet",
            "**/*evidence.generated.json",
            lambda item: (
                item.get("forecastId") == artifact["forecastId"]
                and item.get("questionId") == artifact["questionId"]
                and item.get("evidencePacketId") == artifact["evidencePacketId"]
            ),
            required=True,
        )
    )
    question = assert_related_public(find_forecast_question(artifact["questionId"]))
    history = assert_related_public(
        find_optional_related_record(
            "Forecast history",
            "**/*history.generated.json",
            lambda item: (
                item.get("questionId") == artifact["questionId"]
                and any(entry.get("forecastId") == artifact["forecastId"] for entry in item.get("entries", []))
            ),
        )
    )
    resolution = assert_related_public(
        find_optional_related_record(
            "Resolution record",
            "**/*resolution.generated.json",
            lambda item: item.get("questionId") == artifact["questionId"],
        )
    )
    scoring = assert_related_public(
        find_optional_related_record(
            "Scoring report",
            "**/*scoring.generated.json",
            lambda item: (
                item.get("forecastId") == artifact["forecastId"]
                and item.get("questionId") == artifact["questionId"]
            ),
        )
    )
    outcome_summary = assert_related_public(
        find_optional_related_record(
            "Outcome summary",
            "**/*outcome-summary.generated.json",
            lambda item: item.get("forecastId") == artifact["forecastId"],
        )
    )
    pipeline_run = assert_related_public(
        find_optional_related_record(
            "Pipeline run",
            "**/*pipeline-run.generated.json",
            lambda item: item.get("outputs", {}).get("forecastId") == artifact["forecastId"],
        )
    )

    calibration = None
    track_record = None
    if scoring is not None:
        calibration = assert_related_public(
            find_optional_related_record(
                "Calibration summary",
                "**/*calibration.generated.json",
                lambda item: (
                    item.get("generatedAt") == scoring.get("generatedAt")
                    and item.get("domain") == artifact["domain"]
                    and item.get("horizonBucket") == artifact["horizon"]["label"]
                    and item.get("outputType") == artifact["outputType"]
                ),
            )
        )
        track_record = assert_related_public(
            find_optional_related_record(
                "Track record",
                "**/*track-record.generated.json",
                lambda item: (
                    item.get("generatedAt") == scoring.get("generatedAt")
                    and item.get("domain") == artifact["domain"]
                    and item.get("horizonBucket") == artifact["horizon"]["label"]
                    and item.get("outputType") == artifact["outputType"]
                ),
            )
        )

    return {
        "bundleId": f"forecastbundle-{artifact['forecastId']}",
        "forecastId": artifact["forecastId"],
        "questionId": artifact["questionId"],
        "domain": artifact["domain"],
        "status": "resolved" if resolution and resolution.get("status") == "resolved" else artifact["questionStatus"],
        "includedRecords": {
            "forecastArtifact": artifact["forecastId"],
            "evidencePacket": evidence["evidencePacketId"],
            "forecastQuestion": question["questionId"] if question else None,
            "forecastHistory": history["historyId"] if history else None,
            "resolutionRecord": resolution["resolutionRecordId"] if resolution else None,
            "scoringReport": scoring["scoringReportId"] if scoring else None,
            "calibrationSummary": calibration["calibrationSummaryId"] if calibration else None,
            "trackRecordReport": track_record["trackRecordReportId"] if track_record else None,
            "outcomeSummary": outcome_summary["resolutionRecordId"] if outcome_summary else None,
            "pipelineRun": pipeline_run["pipelineRunId"] if pipeline_run else None,
        },
        "records": {
            "forecastArtifact": artifact,
            "evidencePacket": evidence,
            "forecastQuestion": question,
            "forecastHistory": history,
            "resolutionRecord": resolution,
            "scoringReport": scoring,
            "calibrationSummary": calibration,
            "trackRecordReport": track_record,
            "outcomeSummary": outcome_summary,
            "pipelineRun": pipeline_run,
        },
    }


def build_forecast_card(path: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    bundle = build_forecast_bundle(path, artifact)
    records = bundle["records"]
    question = records["forecastQuestion"]
    resolution = records["resolutionRecord"]
    scoring = records["scoringReport"]
    outcome_summary = records["outcomeSummary"]
    pipeline_run = records["pipelineRun"]
    track_record = records["trackRecordReport"]
    calibration = records["calibrationSummary"]

    resolved_status = resolution.get("status") if resolution else None
    if outcome_summary:
        quality_claim_status = outcome_summary.get("qualityClaimStatus")
        minimum_sample_size = outcome_summary.get("minimumCalibrationSampleSize")
        resolved_comparable = (
            outcome_summary.get("resolvedComparablePipelineOutcomes")
            or outcome_summary.get("resolvedComparableLiveOutcomes")
        )
    else:
        quality_claim_status = "unresolved"
        minimum_sample_size = None
        resolved_comparable = None

    score: dict[str, Any] | None = None
    if scoring:
        score = {
            "scoreStatus": scoring["scoreStatus"],
            "scoringRule": scoring["scoringRule"],
            "primaryScore": scoring.get("primaryScore"),
            "baselineScore": scoring.get("baselineScore"),
            "baselineLift": scoring.get("baselineLift"),
            "generatedAt": scoring["generatedAt"],
        }

    return {
        "cardId": f"forecastcard-{artifact['forecastId']}",
        "forecastId": artifact["forecastId"],
        "questionId": artifact["questionId"],
        "title": question["title"] if question else None,
        "domain": artifact["domain"],
        "horizon": artifact["horizon"],
        "status": bundle["status"],
        "forecastedAt": artifact["forecastedAt"],
        "closedAt": artifact.get("closedAt"),
        "scheduledResolutionAt": artifact["resolutionPlan"]["scheduledResolutionAt"],
        "forecast": artifact["forecastOutput"],
        "baseline": artifact["baselineForecast"],
        "model": {
            "modelId": artifact["model"]["modelId"],
            "version": artifact["model"]["version"],
        },
        "resolution": {
            "status": resolved_status,
            "resolvedAt": resolution.get("resolvedAt") if resolution else None,
            "resolvedOutcome": resolution.get("resolvedOutcome") if resolution else None,
        },
        "score": score,
        "qualityClaim": {
            "status": quality_claim_status,
            "minimumSampleSize": minimum_sample_size,
            "resolvedComparableOutcomes": resolved_comparable,
            "sampleSize": calibration.get("sampleSize") if calibration else None,
            "trackRecordReportId": track_record.get("trackRecordReportId") if track_record else None,
        },
        "requestBinding": {
            "pipelineRunId": pipeline_run.get("pipelineRunId") if pipeline_run else None,
            "requestId": pipeline_run.get("requestId") if pipeline_run else None,
            "effectfulGeneration": pipeline_run.get("effectfulGeneration") if pipeline_run else None,
            "executionMode": pipeline_run.get("executionMode") if pipeline_run else None,
        },
        "warnings": [
            "Fixture-mode record; do not generalize to live performance.",
            "Calibration and quality claims require the declared minimum comparable resolved outcomes.",
        ],
        "links": {
            "forecastBundle": f"forecastbundle-{artifact['forecastId']}",
            "forecastArtifact": artifact["forecastId"],
            "evidencePacket": artifact["evidencePacketId"],
            "resolutionRecord": resolution.get("resolutionRecordId") if resolution else None,
            "scoringReport": scoring.get("scoringReportId") if scoring else None,
            "trackRecordReport": track_record.get("trackRecordReportId") if track_record else None,
        },
    }


def read_record(record_type: str, record_id: str, question_id: str | None = None) -> dict[str, Any]:
    if len([record_id]) > MAX_RECORDS_PER_REQUEST:
        raise PublicError("rate_limited", "Only one record may be requested at a time.")
    path, record = find_record(record_type, record_id)
    assert_public_access(record)
    if question_id is not None and record.get("questionId") != question_id:
        raise PublicError("binding_mismatch", "Record does not match the requested question.")
    if record_type == "forecast-artifact":
        validate_artifact_binding(path, record)
    if record_type == "forecast-bundle":
        record = build_forecast_bundle(path, record)
    if record_type == "forecast-card":
        record = build_forecast_card(path, record)
    return {
        "recordType": record_type,
        "recordId": record_id,
        "access": {
            "mode": "read_only_file",
            "maxRecordsPerRequest": MAX_RECORDS_PER_REQUEST,
        },
        "record": record,
    }


def record_summary(record_type: str, record: dict[str, Any]) -> dict[str, Any]:
    config = RECORD_TYPES[record_type]
    summary: dict[str, Any] = {
        "recordType": record_type,
        "recordId": record[config["id_field"]],
    }
    for field in [
        "questionId",
        "domain",
        "horizonBucket",
        "outputType",
        "forecastedAt",
        "generatedAt",
    ]:
        if field in record:
            summary[field] = record[field]
    return summary


def list_records(record_type: str, domain: str | None = None, limit: int = MAX_LIST_RECORDS) -> dict[str, Any]:
    if limit < 1 or limit > MAX_LIST_RECORDS:
        raise PublicError("bad_request", f"Limit must be between 1 and {MAX_LIST_RECORDS}.")
    summaries: list[dict[str, Any]] = []
    for _path, record in candidate_records(record_type):
        assert_public_access(record)
        if domain is not None and record.get("domain") != domain:
            continue
        summaries.append(record_summary(record_type, record))
    summaries = sorted(
        summaries,
        key=lambda item: (
            str(item.get("domain", "")),
            str(item.get("questionId", "")),
            str(item.get("recordId", "")),
        ),
    )[:limit]
    return {
        "recordType": record_type,
        "access": {
            "mode": "read_only_file",
            "maxListRecords": MAX_LIST_RECORDS,
        },
        "count": len(summaries),
        "records": summaries,
    }


def render_response(response: dict[str, Any], max_bytes: int) -> str:
    output = json.dumps(response, indent=2, sort_keys=False) + "\n"
    if len(output.encode("utf-8")) > max_bytes:
        raise PublicError("response_too_large", "Response exceeds configured size limit.")
    return output


def public_error(error: PublicError) -> str:
    return json.dumps(
        {
            "error": {
                "code": error.code,
                "message": error.message,
            }
        },
        indent=2,
        sort_keys=False,
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-type", choices=sorted(RECORD_TYPES), required=True)
    parser.add_argument("--id", help="forecastId or trackRecordReportId")
    parser.add_argument("--list", action="store_true", help="list public records of this type")
    parser.add_argument("--domain", help="optional domain filter for --list")
    parser.add_argument("--question-id", help="optional binding check for question-scoped records")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--limit", type=int, default=MAX_LIST_RECORDS)
    args = parser.parse_args()

    try:
        if args.list:
            response = list_records(args.record_type, args.domain, args.limit)
        else:
            if not args.id:
                raise PublicError("bad_request", "Record id is required unless --list is used.")
            response = read_record(args.record_type, args.id, args.question_id)
        sys.stdout.write(render_response(response, args.max_bytes))
    except PublicError as exc:
        sys.stderr.write(public_error(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
