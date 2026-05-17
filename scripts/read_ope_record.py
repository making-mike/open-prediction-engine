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
    "evidence-source-set": {
        "glob": "**/*source-set.generated.json",
        "id_field": "evidenceSourceSetId",
    },
    "evidence-trace": {
        "glob": "**/*artifact*.json",
        "id_field": "forecastId",
    },
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
    "source-connector-results": {
        "glob": "**/*source-connector-results.generated.json",
        "id_field": "sourceConnectorResultSetId",
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
        if record_type == "evidence-trace" and not evidence_trace_available(data):
            continue
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


def evidence_trace_available(artifact: dict[str, Any]) -> bool:
    forecast_id = artifact.get("forecastId")
    if not isinstance(forecast_id, str):
        return False
    for path in sorted(GENERATED.glob("**/*pipeline-run.generated.json")):
        data = load_json(path)
        outputs = data.get("outputs", {})
        if outputs.get("forecastId") == forecast_id and outputs.get("evidencePlanId") and outputs.get("evidenceSourceSetId"):
            return True
    return False


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


def find_setup_forecast_run(forecast_id: str) -> tuple[Path, dict[str, Any]] | None:
    return find_optional_related_record(
        "Setup forecast run",
        "**/*setup-forecast-run.generated.json",
        lambda item: item.get("recordBinding", {}).get("forecastId") == forecast_id,
    )


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
    setup_forecast_run = assert_related_public(find_setup_forecast_run(artifact["forecastId"]))

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

    status = resolution.get("status") if resolution else artifact["questionStatus"]
    return {
        "bundleId": f"forecastbundle-{artifact['forecastId']}",
        "forecastId": artifact["forecastId"],
        "questionId": artifact["questionId"],
        "domain": artifact["domain"],
        "status": status,
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
            "setupForecastRun": setup_forecast_run["setupForecastRunId"] if setup_forecast_run else None,
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
            "setupForecastRun": setup_forecast_run,
        },
    }


def compact_connector(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "connectorId": item["connectorId"],
        "connectorKey": item["connectorKey"],
        "status": item["status"],
        "sourceClass": item["sourceClass"],
        "allowedFor": item["allowedFor"],
        "allowedBySourcePolicy": item["policyBinding"]["allowedBySourcePolicy"],
        "retrievalMode": item["capability"]["retrievalMode"],
        "networkAccessInNormalChecks": item["capability"]["networkAccessInNormalChecks"],
        "liveFetchRequiresApproval": item["capability"]["liveFetchRequiresApproval"],
        "acceptsPromptVisibleCredentials": item["credentialBoundary"]["acceptsPromptVisibleCredentials"],
        "rawStackTracesExposed": item["diagnosticsBoundary"]["exposesRawStackTraces"],
        "allEvidenceClaimed": item["provenanceBoundary"]["allEvidenceClaimed"],
        "risk": item["risk"],
    }


def compact_connector_result(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "connectorResultId": item["connectorResultId"],
        "connectorKey": item["connectorKey"],
        "sourceClass": item["sourceClass"],
        "sourceRole": item["sourceRole"],
        "resultStatus": item["resultStatus"],
        "plannedIntentIds": item["plannedIntentIds"],
        "unavailableEvidence": item["unavailableEvidence"],
        "retrievalDiagnostics": {
            "diagnosticLevel": item["retrievalDiagnostics"]["diagnosticLevel"],
            "publicMessage": item["retrievalDiagnostics"]["publicMessage"],
            "rawStackTraceExposed": item["retrievalDiagnostics"]["rawStackTraceExposed"],
        },
        "provenance": {
            "retrievedAt": item["provenance"]["retrievedAt"],
            "storesContentHash": item["provenance"]["storesContentHash"],
            "allEvidenceClaimed": item["provenance"]["allEvidenceClaimed"],
        },
        "controls": item["controls"],
    }


def compact_source_record(item: dict[str, Any]) -> dict[str, Any]:
    source_ref = item["sourceRef"]
    return {
        "recordId": item["recordId"],
        "sourceRole": item["sourceRole"],
        "connector": item["connector"],
        "connectorBinding": item["connectorBinding"],
        "plannedIntentIds": item["plannedIntentIds"],
        "sourceRef": {
            "sourceId": source_ref["sourceId"],
            "name": source_ref["name"],
            "sourceType": source_ref["sourceType"],
            "uri": source_ref.get("uri"),
            "retrievedAt": source_ref.get("retrievedAt"),
            "contentHash": source_ref.get("contentHash"),
        },
        "sourceQuality": item["sourceQuality"],
        "normalizedFieldNames": sorted(item["normalizedFields"]),
    }


def find_required_generated(label: str, glob_pattern: str, field: str, expected: str) -> dict[str, Any]:
    return assert_related_public(
        find_generated_record(
            label,
            glob_pattern,
            lambda item: item.get(field) == expected,
            required=True,
        )
    )


def build_evidence_trace(path: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    bundle = build_forecast_bundle(path, artifact)
    records = bundle["records"]
    evidence = records["evidencePacket"]
    pipeline_run = records["pipelineRun"]
    resolution = records["resolutionRecord"]
    scoring = records["scoringReport"]
    if pipeline_run is None:
        raise PublicError("not_found", "Pipeline run was not found for evidence trace.")

    outputs = pipeline_run["outputs"]
    evidence_plan_id = outputs.get("evidencePlanId")
    evidence_source_set_id = outputs.get("evidenceSourceSetId")
    source_policy_id = outputs.get("sourcePolicyId")
    if not evidence_plan_id or not evidence_source_set_id or not source_policy_id:
        raise PublicError("not_found", "Evidence trace records were not found.")

    plan = find_required_generated("Evidence plan", "**/*plan.generated.json", "evidencePlanId", evidence_plan_id)
    source_set = find_required_generated(
        "Evidence source set",
        "**/*source-set.generated.json",
        "evidenceSourceSetId",
        evidence_source_set_id,
    )
    registry = find_required_generated(
        "Source connector registry",
        "**/*source-connector-registry.generated.json",
        "sourceConnectorRegistryId",
        source_set["sourceConnectorRegistryId"],
    )
    result_set = find_required_generated(
        "Source connector result set",
        "**/*source-connector-results.generated.json",
        "sourceConnectorResultSetId",
        source_set["sourceConnectorResultSetId"],
    )

    validate_evidence_trace_bindings(artifact, evidence, pipeline_run, plan, source_set, registry, result_set)
    connector_results = {item["connectorResultId"]: item for item in result_set["connectorResults"]}
    used_result_ids = {
        record["connectorBinding"]["connectorResultId"]
        for record in source_set["records"]
    }
    used_results = [
        compact_connector_result(connector_results[result_id])
        for result_id in sorted(used_result_ids)
    ]
    unavailable_results = [
        compact_connector_result(item)
        for item in result_set["connectorResults"]
        if item["connectorResultId"] not in used_result_ids and item["resultStatus"] != "succeeded_fixture_replay"
    ]

    return {
        "evidenceTraceId": f"evidencetrace-{artifact['forecastId'].split('-')[-1]}",
        "forecastId": artifact["forecastId"],
        "questionId": artifact["questionId"],
        "domain": artifact["domain"],
        "traceStatus": "complete_fixture_trace",
        "generatedAt": pipeline_run["generatedAt"],
        "recordBinding": {
            "requestId": pipeline_run["requestId"],
            "pipelineRunId": pipeline_run["pipelineRunId"],
            "questionId": artifact["questionId"],
            "forecastId": artifact["forecastId"],
            "forecastArtifactId": artifact["forecastId"],
            "evidencePacketId": evidence["evidencePacketId"],
            "evidencePlanId": plan["evidencePlanId"],
            "evidenceSourceSetId": source_set["evidenceSourceSetId"],
            "sourcePolicyId": plan["sourcePolicy"]["sourcePolicyId"],
            "sourceConnectorRegistryId": source_set["sourceConnectorRegistryId"],
            "sourceConnectorResultSetId": source_set["sourceConnectorResultSetId"],
            "resolutionRecordId": resolution["resolutionRecordId"] if resolution else None,
            "scoringReportId": scoring["scoringReportId"] if scoring else None,
        },
        "sourcePolicy": plan["sourcePolicy"],
        "connectorPolicyChecks": plan["connectorPolicyChecks"],
        "connectorRegistry": {
            "sourceConnectorRegistryId": registry["sourceConnectorRegistryId"],
            "defaultExecutionMode": registry["defaultExecutionMode"],
            "connectors": [compact_connector(item) for item in registry["connectors"]],
            "unsupportedSourceClasses": registry["unsupportedSourceClasses"],
        },
        "sourceConnectorResults": {
            "sourceConnectorResultSetId": result_set["sourceConnectorResultSetId"],
            "usedResults": used_results,
            "unavailableOrSkippedResults": unavailable_results,
        },
        "gatheredSourceRecords": [compact_source_record(item) for item in source_set["records"]],
        "provenanceSummary": source_set["provenanceSummary"],
        "controls": {
            "readOnly": True,
            "networkAccess": source_set["controls"]["networkAccess"],
            "liveFetch": source_set["controls"]["liveFetch"],
            "effectfulGeneration": source_set["controls"]["effectfulGeneration"],
            "rawStackTracesExposed": False,
            "promptVisibleCredentialsAccepted": False,
        },
        "warnings": [
            "Evidence trace is read-only and built from generated local records.",
            "Trace excludes raw fixture contents and raw diagnostics.",
            "Connector results do not claim all possible internet evidence was gathered.",
            "Fixture-mode evidence must not be generalized to live calibration quality.",
        ],
        "links": {
            "forecastCard": f"forecastcard-{artifact['forecastId']}",
            "forecastBundle": bundle["bundleId"],
            "forecastArtifact": artifact["forecastId"],
            "evidencePacket": evidence["evidencePacketId"],
            "evidencePlan": plan["evidencePlanId"],
            "evidenceSourceSet": source_set["evidenceSourceSetId"],
            "sourceConnectorRegistry": registry["sourceConnectorRegistryId"],
            "sourceConnectorResultSet": result_set["sourceConnectorResultSetId"],
        },
    }


def validate_evidence_trace_bindings(
    artifact: dict[str, Any],
    evidence: dict[str, Any],
    pipeline_run: dict[str, Any],
    plan: dict[str, Any],
    source_set: dict[str, Any],
    registry: dict[str, Any],
    result_set: dict[str, Any],
) -> None:
    outputs = pipeline_run["outputs"]
    if outputs["forecastId"] != artifact["forecastId"]:
        raise PublicError("binding_mismatch", "Evidence trace forecast binding failed.")
    if outputs["evidencePlanId"] != plan["evidencePlanId"]:
        raise PublicError("binding_mismatch", "Evidence trace plan binding failed.")
    if outputs["evidenceSourceSetId"] != source_set["evidenceSourceSetId"]:
        raise PublicError("binding_mismatch", "Evidence trace source-set binding failed.")
    if evidence["forecastId"] != artifact["forecastId"] or evidence["questionId"] != artifact["questionId"]:
        raise PublicError("binding_mismatch", "Evidence trace evidence-packet binding failed.")
    if plan["requestId"] != source_set["requestId"] or plan["requestId"] != pipeline_run["requestId"]:
        raise PublicError("binding_mismatch", "Evidence trace request binding failed.")
    if plan["sourcePolicy"]["sourcePolicyId"] != source_set["sourcePolicyId"]:
        raise PublicError("binding_mismatch", "Evidence trace source-policy binding failed.")
    if plan["sourceConnectorRegistryId"] != registry["sourceConnectorRegistryId"]:
        raise PublicError("binding_mismatch", "Evidence trace connector registry binding failed.")
    if plan["expectedSourceConnectorResultSetId"] != result_set["sourceConnectorResultSetId"]:
        raise PublicError("binding_mismatch", "Evidence trace connector result-set binding failed.")
    if source_set["sourceConnectorRegistryId"] != registry["sourceConnectorRegistryId"]:
        raise PublicError("binding_mismatch", "Evidence trace source-set registry binding failed.")
    if source_set["sourceConnectorResultSetId"] != result_set["sourceConnectorResultSetId"]:
        raise PublicError("binding_mismatch", "Evidence trace source-set result binding failed.")

    connectors = {item["connectorId"]: item for item in registry["connectors"]}
    results = {item["connectorResultId"]: item for item in result_set["connectorResults"]}
    forecast_time = set(plan["connectorPolicyChecks"]["forecastTimeConnectors"])
    for record in source_set["records"]:
        binding = record["connectorBinding"]
        connector = connectors.get(binding["connectorId"])
        result = results.get(binding["connectorResultId"])
        if connector is None or result is None:
            raise PublicError("binding_mismatch", "Evidence trace connector binding failed.")
        if connector["connectorKey"] != record["connector"] or result["connectorKey"] != record["connector"]:
            raise PublicError("binding_mismatch", "Evidence trace connector key binding failed.")
        if record["connector"] not in forecast_time:
            raise PublicError("binding_mismatch", "Evidence trace contains a non-forecast-time connector.")
        if result["resultStatus"] != "succeeded_fixture_replay":
            raise PublicError("binding_mismatch", "Evidence trace gathered record does not bind to a successful connector result.")


def build_forecast_card(path: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    bundle = build_forecast_bundle(path, artifact)
    records = bundle["records"]
    question = records["forecastQuestion"]
    resolution = records["resolutionRecord"]
    scoring = records["scoringReport"]
    outcome_summary = records["outcomeSummary"]
    pipeline_run = records["pipelineRun"]
    setup_forecast_run = records["setupForecastRun"]
    track_record = records["trackRecordReport"]
    calibration = records["calibrationSummary"]

    resolved_status = resolution.get("status") if resolution else None
    if outcome_summary:
        quality_claim_status = outcome_summary.get("qualityClaimStatus")
        minimum_sample_size = outcome_summary.get("minimumCalibrationSampleSize")
        resolved_comparable = None
        for key in [
            "resolvedComparablePipelineOutcomes",
            "resolvedComparableLiveOutcomes",
            "resolvedComparableAutoEvidenceOutcomes",
            "resolvedComparableSourceHandoffOutcomes",
        ]:
            if key in outcome_summary:
                resolved_comparable = outcome_summary[key]
                break
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
            "sourceMode": pipeline_run.get("controls", {}).get("sourceMode") if pipeline_run else None,
            "evidencePlanId": pipeline_run.get("outputs", {}).get("evidencePlanId") if pipeline_run else None,
            "evidenceSourceSetId": pipeline_run.get("outputs", {}).get("evidenceSourceSetId") if pipeline_run else None,
            "sourcePolicyId": pipeline_run.get("outputs", {}).get("sourcePolicyId") if pipeline_run else None,
        },
        "setupBinding": {
            "setupForecastRunId": setup_forecast_run.get("setupForecastRunId") if setup_forecast_run else None,
            "domainSetupId": setup_forecast_run.get("domainSetupId") if setup_forecast_run else None,
            "sourceManifestId": setup_forecast_run.get("sourceManifestId") if setup_forecast_run else None,
            "fieldMappingId": setup_forecast_run.get("fieldMappingId") if setup_forecast_run else None,
            "sourceIntakeReportId": setup_forecast_run.get("sourceIntakeReportId") if setup_forecast_run else None,
            "sourceIntakeHandoffId": setup_forecast_run.get("sourceIntakeHandoffId") if setup_forecast_run else None,
            "sourceHandoffMethodGateId": setup_forecast_run.get("sourceHandoffMethodGateId") if setup_forecast_run else None,
            "setupMethodDecisionId": setup_forecast_run.get("setupMethodDecisionId") if setup_forecast_run else None,
            "setupBenchmarkGateId": setup_forecast_run.get("setupBenchmarkGateId") if setup_forecast_run else None,
            "runStatus": setup_forecast_run.get("runStatus") if setup_forecast_run else None,
            "selectedMethodClass": setup_forecast_run.get("selectedMethodClass") if setup_forecast_run else None,
            "selectedForecastMode": setup_forecast_run.get("selectedForecastMode") if setup_forecast_run else None,
        },
        "warnings": [
            "Fixture-mode record; do not generalize to live performance.",
            "Calibration and quality claims require the declared minimum comparable resolved outcomes.",
        ],
        "links": {
            "forecastBundle": f"forecastbundle-{artifact['forecastId']}",
            "evidenceTrace": f"evidencetrace-{artifact['forecastId'].split('-')[-1]}" if evidence_trace_available(artifact) else None,
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
    if record_type == "evidence-trace":
        record = build_evidence_trace(path, record)
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
