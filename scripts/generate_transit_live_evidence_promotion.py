#!/usr/bin/env python3
"""Generate a checked gate for policy-bound transit live evidence promotion."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from source_connector_catalog import SOURCE_CONNECTOR_REGISTRY_ID, SOURCE_CONNECTOR_RESULT_SET_ID, connector_binding
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-live-evidence-promotion"
PROMOTION_PATH = GENERATED / "transit-live-evidence-promotion.generated.json"
SOURCE_SET_PATH = GENERATED / "weather-transit-delays-promoted-source-set.generated.json"
PROMOTION_SCHEMA = SPEC / "transit-live-evidence-promotion.schema.json"
SOURCE_SET_SCHEMA = SPEC / "evidence-source-set.schema.json"

GENERATED_AT = "2026-06-10T02:12:00Z"
FORECAST_ID = "forecast-1201"
QUESTION_ID = "question-1201"
REQUEST_ID = "request-1201"
EVIDENCE_PLAN_ID = "evidenceplan-1201"
SOURCE_POLICY_ID = "sourcepolicy-1201"
PROMOTED_SOURCE_SET_ID = "evidencesourceset-1201"
MAX_FRESHNESS_SECONDS = 7200

FORECASTED_AT = "2026-06-10T02:00:00Z"
FORECAST_CLOSE_AT = "2026-06-10T02:30:00Z"
HORIZON_START = "2026-06-10T03:00:00Z"
HORIZON_END = "2026-06-10T07:00:00Z"
SERVICE_DATE = "2026-06-10"
NETWORK = "hsl-surface"
GEOGRAPHY = "helsinki"
SERVICE_WINDOW = "morning_peak"

COMMITTED_FIXTURE_PATH = "spec/fixtures/local-source-files/transit-weather-forecast.json"
PENDING_DRAFT_PATH = ".ope/live/transit-forward-run/2026-06-10T020500Z/weather/transit-weather-forecast.json"
PROMOTED_DRAFT_PATH = ".ope/live/transit-forward-run/2026-06-10T020000Z/weather/transit-weather-forecast.json"
POST_CLOSE_DRAFT_PATH = ".ope/live/transit-forward-run/2026-06-10T041500Z/weather/transit-weather-forecast.json"
RESOLUTION_CAPTURE_PATH = ".ope/live/transit-api/hsl-2026-06-10-trip-updates.csv"
PROMOTED_CONTENT_HASH = hashlib.sha256(PROMOTED_DRAFT_PATH.encode("utf-8")).hexdigest()


class TransitLiveEvidencePromotionError(Exception):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def freshness_seconds(capture_timestamp: str, forecast_close_at: str = FORECAST_CLOSE_AT) -> int:
    return int(abs((parse_time(forecast_close_at) - parse_time(capture_timestamp)).total_seconds()))


def source_input(
    *,
    source_path: str,
    source_path_committed: bool,
    local_live_workspace: bool,
    capture_timestamp: str,
) -> dict[str, Any]:
    return {
        "sourcePath": source_path,
        "sourcePathCommitted": source_path_committed,
        "localLiveWorkspace": local_live_workspace,
        "captureTimestamp": capture_timestamp,
        "forecastCloseAt": FORECAST_CLOSE_AT,
        "sourcePolicyId": SOURCE_POLICY_ID,
    }


def gate_checks(
    *,
    source_policy_status: str,
    capture_timing_status: str,
    freshness_status: str,
    freshness: int,
    retention_status: str,
    source_role_status: str,
    leakage_status: str,
    provenance_status: str,
) -> dict[str, Any]:
    return {
        "sourcePolicyStatus": source_policy_status,
        "captureTimingStatus": capture_timing_status,
        "freshnessStatus": freshness_status,
        "freshnessSeconds": freshness,
        "maxFreshnessSeconds": MAX_FRESHNESS_SECONDS,
        "retentionStatus": retention_status,
        "sourceRoleStatus": source_role_status,
        "leakageStatus": leakage_status,
        "provenanceStatus": provenance_status,
        "allEvidenceClaimed": False,
    }


def sanitized_binding(
    *,
    binding_status: str,
    forecast_time_source_set_bound: bool,
    normalized_record_count: int,
    raw_local_path_committed: bool,
    sanitized_artifact_committed: bool,
    content_hash_stored: bool,
    source_set: bool = False,
) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "bindingStatus": binding_status,
        "forecastTimeSourceSetBound": forecast_time_source_set_bound,
        "normalizedRecordCount": normalized_record_count,
        "rawRowsIncluded": False,
        "rawLocalPathCommitted": raw_local_path_committed,
        "sanitizedArtifactCommitted": sanitized_artifact_committed,
        "contentHashStored": content_hash_stored,
        "normalChecksReadRawLocalPath": False,
    }
    if source_set:
        binding["evidenceSourceSetId"] = PROMOTED_SOURCE_SET_ID
        binding["sourceSetPath"] = rel(SOURCE_SET_PATH)
    return binding


def promotion_case(
    *,
    case_id: str,
    surface_type: str,
    source_role: str,
    connector: str,
    promotion_status: str,
    input_binding: dict[str, Any],
    checks: dict[str, Any],
    binding: dict[str, Any],
    rejection_reasons: list[str],
    agent_next_action: str,
) -> dict[str, Any]:
    return {
        "promotionCaseId": case_id,
        "surfaceType": surface_type,
        "sourceRole": source_role,
        "connector": connector,
        "promotionStatus": promotion_status,
        "inputBinding": input_binding,
        "gateChecks": checks,
        "sanitizedBinding": binding,
        "rejectionReasons": rejection_reasons,
        "agentNextAction": agent_next_action,
    }


def build_promoted_source_set() -> dict[str, Any]:
    source_set = {
        "evidenceSourceSetId": PROMOTED_SOURCE_SET_ID,
        "requestId": REQUEST_ID,
        "evidencePlanId": EVIDENCE_PLAN_ID,
        "generatedAt": GENERATED_AT,
        "executionMode": "live_fetch",
        "dataMode": "hybrid",
        "sourcePolicyId": SOURCE_POLICY_ID,
        "sourceConnectorRegistryId": SOURCE_CONNECTOR_REGISTRY_ID,
        "sourceConnectorResultSetId": SOURCE_CONNECTOR_RESULT_SET_ID,
        "domain": "weather-transit-delays",
        "geography": GEOGRAPHY,
        "serviceDate": SERVICE_DATE,
        "records": [
            {
                "recordId": "sourcerecord-1201",
                "sourceRole": "forecast_input",
                "connector": "open_meteo_weather",
                "connectorBinding": connector_binding("open_meteo_weather"),
                "plannedIntentIds": ["searchintent-1201"],
                "sourceRef": {
                    "sourceId": "source-1201",
                    "name": "Promoted Open-Meteo Helsinki weather forecast",
                    "sourceType": "public_dataset",
                    "uri": f"local://{PROMOTED_DRAFT_PATH}",
                    "retrievedAt": FORECASTED_AT,
                    "contentHash": PROMOTED_CONTENT_HASH,
                },
                "rawSourceMetadata": {
                    "mode": "live_fetch",
                    "fixturePath": None,
                    "contentHash": PROMOTED_CONTENT_HASH,
                },
                "sourceQuality": {
                    "status": "current",
                    "coverage": "complete",
                    "freshnessStatus": "within_policy",
                    "notes": "Promoted from an approved ignored local live draft; raw file remains outside git.",
                },
                "normalizedFields": {
                    "sourceRole": "weather_forecast",
                    "network": NETWORK,
                    "geography": GEOGRAPHY,
                    "serviceDate": SERVICE_DATE,
                    "serviceWindow": SERVICE_WINDOW,
                    "capturedAt": FORECASTED_AT,
                    "forecastCloseAt": FORECAST_CLOSE_AT,
                    "forecastPrecipitationMm": 4.8,
                    "forecastSnowfallMm": 0.0,
                    "forecastWindGustKmh": 31.2,
                    "temperatureC": 7.4,
                    "sourceStatus": "current",
                },
            }
        ],
        "provenanceSummary": {
            "sourceCount": 1,
            "connectorsUsed": ["open_meteo_weather"],
            "sourceClassesUsed": ["public_dataset"],
            "unavailableEvidenceCount": 0,
            "allEvidenceClaimed": False,
        },
        "controls": {
            "networkAccess": True,
            "liveFetch": True,
            "effectfulGeneration": False,
        },
        "warnings": [
            "This is a sanitized promoted source set; the raw .ope/live capture remains ignored.",
            "The record is forecast-time evidence only, not a forecast, resolution, score, or quality claim.",
            "Normal checks validate this committed sanitized artifact without reading .ope/live or fetching live data.",
        ],
    }
    validate_promoted_source_set(source_set)
    return source_set


def build_promotion() -> dict[str, Any]:
    source_set_path = rel(SOURCE_SET_PATH)
    promotion = {
        "transitLiveEvidencePromotionId": "transitliveevidencepromotion-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "promotionMode": "checked_policy_bound_live_evidence_promotion",
        "forecastWindow": {
            "forecastId": FORECAST_ID,
            "questionId": QUESTION_ID,
            "forecastedAt": FORECASTED_AT,
            "forecastCloseAt": FORECAST_CLOSE_AT,
            "horizon": {
                "startsAt": HORIZON_START,
                "endsAt": HORIZON_END,
                "label": "same-day-morning-peak",
            },
            "network": NETWORK,
            "geography": GEOGRAPHY,
            "serviceDate": SERVICE_DATE,
            "serviceWindow": SERVICE_WINDOW,
        },
        "policyBinding": {
            "sourcePolicyId": SOURCE_POLICY_ID,
            "approvalRequired": True,
            "allowedForecastTimeRoles": [
                "weather_forecast",
                "historical_delay_rows",
                "static_schedule",
                "planned_service_alerts",
            ],
            "resolutionOnlyRoles": [
                "transit_delay_outcome",
                "feed_health",
                "trip_updates_after_window",
                "post_window_delay_rows",
                "resolution_outcome",
            ],
            "allowedConnectors": ["committed_fixture", "open_meteo_weather", "manual_upload", "local_file"],
            "maxFreshnessSeconds": MAX_FRESHNESS_SECONDS,
            "retention": {
                "rawLocalWorkspace": ".ope/live/",
                "rawLocalArtifactsCommitted": False,
                "rawPreviewStored": False,
                "sanitizedNormalizedRecordsCommitted": True,
                "contentHashesStored": True,
            },
            "credentialUseAllowed": False,
            "normalChecksMayReadLiveWorkspace": False,
            "normalChecksMayFetchLiveNetwork": False,
        },
        "intakeGate": {
            "gateId": "transitlivepromotiongate-001",
            "requiredChecksBeforePromotion": [
                "source_policy",
                "capture_timestamp",
                "forecast_close_time",
                "freshness",
                "retention",
                "source_role",
                "leakage",
                "provenance_binding",
            ],
            "rejectedAsForecastTimeEvidence": [
                "post_close_capture",
                "resolution_only_source_role",
                "missing_source_policy",
                "failed_freshness_check",
                "raw_rows_committed",
                "credential_bearing_capture",
            ],
            "rawLocalWorkspace": ".ope/live/",
            "promotedSourceSetPath": source_set_path,
        },
        "promotionCases": [
            promotion_case(
                case_id="transitlivepromotioncase-001",
                surface_type="committed_fixture",
                source_role="weather_forecast",
                connector="committed_fixture",
                promotion_status="already_committed_fixture",
                input_binding=source_input(
                    source_path=COMMITTED_FIXTURE_PATH,
                    source_path_committed=True,
                    local_live_workspace=False,
                    capture_timestamp=FORECASTED_AT,
                ),
                checks=gate_checks(
                    source_policy_status="not_required_committed_fixture",
                    capture_timing_status="not_applicable",
                    freshness_status="not_applicable",
                    freshness=0,
                    retention_status="passed_metadata_only",
                    source_role_status="fixture_reference",
                    leakage_status="not_applicable",
                    provenance_status="fixture_reference",
                ),
                binding=sanitized_binding(
                    binding_status="fixture_reference",
                    forecast_time_source_set_bound=False,
                    normalized_record_count=1,
                    raw_local_path_committed=False,
                    sanitized_artifact_committed=True,
                    content_hash_stored=True,
                ),
                rejection_reasons=[],
                agent_next_action="Use the committed fixture path for fixture-mode runs; no local live promotion is needed.",
            ),
            promotion_case(
                case_id="transitlivepromotioncase-002",
                surface_type="local_live_draft",
                source_role="weather_forecast",
                connector="open_meteo_weather",
                promotion_status="pending_approval",
                input_binding=source_input(
                    source_path=PENDING_DRAFT_PATH,
                    source_path_committed=False,
                    local_live_workspace=True,
                    capture_timestamp="2026-06-10T02:05:00Z",
                ),
                checks=gate_checks(
                    source_policy_status="pending_approval",
                    capture_timing_status="pre_close",
                    freshness_status="pending_approval",
                    freshness=freshness_seconds("2026-06-10T02:05:00Z"),
                    retention_status="pending_approval",
                    source_role_status="pending_approval",
                    leakage_status="pending_approval",
                    provenance_status="not_bound_pending_approval",
                ),
                binding=sanitized_binding(
                    binding_status="draft_not_bound",
                    forecast_time_source_set_bound=False,
                    normalized_record_count=0,
                    raw_local_path_committed=False,
                    sanitized_artifact_committed=False,
                    content_hash_stored=False,
                ),
                rejection_reasons=[],
                agent_next_action="Confirm source policy, freshness, retention, and role before producing a sanitized source set.",
            ),
            promotion_case(
                case_id="transitlivepromotioncase-003",
                surface_type="promoted_forecast_time_evidence",
                source_role="weather_forecast",
                connector="open_meteo_weather",
                promotion_status="promoted",
                input_binding=source_input(
                    source_path=PROMOTED_DRAFT_PATH,
                    source_path_committed=False,
                    local_live_workspace=True,
                    capture_timestamp=FORECASTED_AT,
                ),
                checks=gate_checks(
                    source_policy_status="passed",
                    capture_timing_status="pre_close",
                    freshness_status="within_policy",
                    freshness=freshness_seconds(FORECASTED_AT),
                    retention_status="passed_metadata_only",
                    source_role_status="forecast_time_allowed",
                    leakage_status="passed",
                    provenance_status="bound",
                ),
                binding=sanitized_binding(
                    binding_status="bound_promoted_source_set",
                    forecast_time_source_set_bound=True,
                    normalized_record_count=1,
                    raw_local_path_committed=False,
                    sanitized_artifact_committed=True,
                    content_hash_stored=True,
                    source_set=True,
                ),
                rejection_reasons=[],
                agent_next_action="Use the promoted evidence source-set binding for forecast-time weather evidence.",
            ),
            promotion_case(
                case_id="transitlivepromotioncase-004",
                surface_type="local_live_draft",
                source_role="weather_forecast",
                connector="open_meteo_weather",
                promotion_status="rejected",
                input_binding=source_input(
                    source_path=POST_CLOSE_DRAFT_PATH,
                    source_path_committed=False,
                    local_live_workspace=True,
                    capture_timestamp="2026-06-10T04:15:00Z",
                ),
                checks=gate_checks(
                    source_policy_status="rejected",
                    capture_timing_status="post_close",
                    freshness_status="outside_policy",
                    freshness=freshness_seconds("2026-06-10T04:15:00Z"),
                    retention_status="passed_metadata_only",
                    source_role_status="forecast_time_allowed",
                    leakage_status="rejected_post_close",
                    provenance_status="not_bound_rejected",
                ),
                binding=sanitized_binding(
                    binding_status="rejected_not_bound",
                    forecast_time_source_set_bound=False,
                    normalized_record_count=0,
                    raw_local_path_committed=False,
                    sanitized_artifact_committed=False,
                    content_hash_stored=True,
                ),
                rejection_reasons=["capture_after_forecast_close", "post_close_forecast_evidence_blocked"],
                agent_next_action="Keep the capture as local diagnostics or resolution support; do not use it as forecast-time evidence.",
            ),
            promotion_case(
                case_id="transitlivepromotioncase-005",
                surface_type="resolution_only_evidence",
                source_role="transit_delay_outcome",
                connector="hsl_gtfs_rt_trip_updates",
                promotion_status="rejected",
                input_binding=source_input(
                    source_path=RESOLUTION_CAPTURE_PATH,
                    source_path_committed=False,
                    local_live_workspace=True,
                    capture_timestamp="2026-06-10T07:20:00Z",
                ),
                checks=gate_checks(
                    source_policy_status="rejected",
                    capture_timing_status="post_close",
                    freshness_status="outside_policy",
                    freshness=freshness_seconds("2026-06-10T07:20:00Z"),
                    retention_status="passed_metadata_only",
                    source_role_status="resolution_only_rejected",
                    leakage_status="rejected_resolution_only",
                    provenance_status="not_bound_rejected",
                ),
                binding=sanitized_binding(
                    binding_status="rejected_not_bound",
                    forecast_time_source_set_bound=False,
                    normalized_record_count=0,
                    raw_local_path_committed=False,
                    sanitized_artifact_committed=False,
                    content_hash_stored=True,
                ),
                rejection_reasons=[
                    "source_role_resolution_only",
                    "same_window_outcome_leakage",
                    "capture_after_forecast_close",
                ],
                agent_next_action="Use this evidence only through resolution and scoring paths after the service window.",
            ),
        ],
        "readbackSummary": {
            "surfaceCounts": {
                "committedFixtures": 1,
                "localLiveDrafts": 2,
                "promotedForecastTimeEvidence": 1,
                "resolutionOnlyEvidence": 1,
                "postCloseRejected": 2,
                "resolutionOnlyRejected": 1,
            },
            "promotedEvidenceSourceSetId": PROMOTED_SOURCE_SET_ID,
            "promotedEvidenceSourceSetPath": source_set_path,
            "promotedEvidenceReadCommand": (
                f"python3 scripts/ope.py read --record-type evidence-source-set --id {PROMOTED_SOURCE_SET_ID}"
            ),
            "distinctionRules": [
                "Committed fixtures are already checked inputs and do not require live promotion.",
                "Local live drafts remain ignored under .ope/live/ until an explicit approval binds sanitized fields.",
                "Promoted forecast-time evidence must be captured before close and bound to a source policy.",
                "Resolution-only evidence can resolve or score an outcome, but must not become forecast-time evidence.",
            ],
        },
        "claimBoundary": {
            "normalChecksUseLiveNetwork": False,
            "normalChecksReadLiveWorkspace": False,
            "rawLiveCapturesCommitted": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "promotesPostCloseEvidence": False,
            "promotesResolutionOnlyEvidence": False,
            "productionLiveRuntimeClaimAllowed": False,
            "allEvidenceClaimAllowed": False,
        },
        "readSurface": {
            "command": "python3 scripts/ope.py transit-live-evidence-promotion",
            "distinguishesEvidenceSurfaces": True,
            "returnsPromotedSourceSetBinding": True,
            "executesPromotion": False,
            "readsIgnoredLiveWorkspace": False,
            "fetchesLiveData": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
        },
        "warnings": [
            "This read surface defines the gate and checked examples; it does not fetch or inspect live files.",
            "Only sanitized normalized fields may be committed; raw .ope/live captures remain ignored.",
            "Post-close and resolution-only transit captures must not be promoted as forecast-time evidence.",
            "The promoted source set is local evidence plumbing, not a production live connector or quality claim.",
        ],
    }
    validate_promotion(promotion)
    return promotion


def validate_promoted_source_set(source_set: dict[str, Any]) -> None:
    errors = validate_record(source_set, SOURCE_SET_SCHEMA)
    if errors:
        raise TransitLiveEvidencePromotionError(f"promoted transit source-set schema validation failed: {errors[0]}")
    if source_set["evidenceSourceSetId"] != PROMOTED_SOURCE_SET_ID:
        raise TransitLiveEvidencePromotionError("promoted source set ID mismatch")
    if source_set["sourcePolicyId"] != SOURCE_POLICY_ID:
        raise TransitLiveEvidencePromotionError("promoted source set must bind the live evidence policy")
    if source_set["executionMode"] != "live_fetch":
        raise TransitLiveEvidencePromotionError("promoted source set should preserve live_fetch execution mode")
    if source_set["controls"]["effectfulGeneration"]:
        raise TransitLiveEvidencePromotionError("promoted source set must not generate forecasts")
    if source_set["provenanceSummary"]["allEvidenceClaimed"]:
        raise TransitLiveEvidencePromotionError("promoted source set must not claim all evidence coverage")
    record = source_set["records"][0]
    if record["sourceRole"] != "forecast_input":
        raise TransitLiveEvidencePromotionError("promoted source set must contain forecast-time evidence")
    if record["connector"] != "open_meteo_weather":
        raise TransitLiveEvidencePromotionError("promoted source set should bind Open-Meteo weather")
    if record["sourceQuality"]["freshnessStatus"] != "within_policy":
        raise TransitLiveEvidencePromotionError("promoted source set must pass source freshness")
    if parse_time(record["sourceRef"]["retrievedAt"]) > parse_time(FORECAST_CLOSE_AT):
        raise TransitLiveEvidencePromotionError("promoted source set must be captured before forecast close")
    if record["rawSourceMetadata"]["fixturePath"] is not None:
        raise TransitLiveEvidencePromotionError("promoted source set must not point raw metadata at a committed fixture")


def validate_promotion(promotion: dict[str, Any]) -> None:
    errors = validate_record(promotion, PROMOTION_SCHEMA)
    if errors:
        raise TransitLiveEvidencePromotionError(f"transit live evidence promotion schema validation failed: {errors[0]}")
    policy = promotion["policyBinding"]
    if policy["normalChecksMayReadLiveWorkspace"] or policy["normalChecksMayFetchLiveNetwork"]:
        raise TransitLiveEvidencePromotionError("promotion policy must keep normal checks out of live workspace/network")
    if policy["retention"]["rawLocalArtifactsCommitted"] or policy["retention"]["rawPreviewStored"]:
        raise TransitLiveEvidencePromotionError("promotion policy must not commit raw live artifacts")
    cases = {case["promotionCaseId"]: case for case in promotion["promotionCases"]}
    surfaces = {case["surfaceType"] for case in cases.values()}
    expected_surfaces = {
        "committed_fixture",
        "local_live_draft",
        "promoted_forecast_time_evidence",
        "resolution_only_evidence",
    }
    if surfaces != expected_surfaces:
        raise TransitLiveEvidencePromotionError("promotion readback must distinguish all evidence surfaces")
    for case in cases.values():
        input_binding = case["inputBinding"]
        binding = case["sanitizedBinding"]
        if input_binding["localLiveWorkspace"]:
            if not input_binding["sourcePath"].startswith(".ope/live/"):
                raise TransitLiveEvidencePromotionError("local live cases must stay under .ope/live/")
            if input_binding["sourcePathCommitted"] or binding["rawLocalPathCommitted"]:
                raise TransitLiveEvidencePromotionError("local live cases must not commit raw local paths")
        if case["gateChecks"]["allEvidenceClaimed"]:
            raise TransitLiveEvidencePromotionError("promotion cases must not claim all available evidence")
    promoted = cases["transitlivepromotioncase-003"]
    if promoted["promotionStatus"] != "promoted":
        raise TransitLiveEvidencePromotionError("selected live weather case should be promoted")
    if promoted["gateChecks"]["captureTimingStatus"] != "pre_close":
        raise TransitLiveEvidencePromotionError("promoted case must be pre-close")
    if promoted["gateChecks"]["freshnessStatus"] != "within_policy":
        raise TransitLiveEvidencePromotionError("promoted case must pass freshness")
    if promoted["gateChecks"]["freshnessSeconds"] > promoted["gateChecks"]["maxFreshnessSeconds"]:
        raise TransitLiveEvidencePromotionError("promoted case exceeds freshness policy")
    if promoted["gateChecks"]["sourceRoleStatus"] != "forecast_time_allowed":
        raise TransitLiveEvidencePromotionError("promoted case must use an allowed forecast-time source role")
    if promoted["gateChecks"]["leakageStatus"] != "passed":
        raise TransitLiveEvidencePromotionError("promoted case must pass leakage checks")
    promoted_binding = promoted["sanitizedBinding"]
    if (
        promoted_binding["bindingStatus"] != "bound_promoted_source_set"
        or not promoted_binding["forecastTimeSourceSetBound"]
        or promoted_binding["evidenceSourceSetId"] != PROMOTED_SOURCE_SET_ID
        or promoted_binding["sourceSetPath"] != rel(SOURCE_SET_PATH)
    ):
        raise TransitLiveEvidencePromotionError("promoted case must bind the generated source set")
    post_close = cases["transitlivepromotioncase-004"]
    if post_close["gateChecks"]["captureTimingStatus"] != "post_close":
        raise TransitLiveEvidencePromotionError("post-close case must be explicitly post-close")
    if "capture_after_forecast_close" not in post_close["rejectionReasons"]:
        raise TransitLiveEvidencePromotionError("post-close case must cite forecast close rejection")
    if post_close["sanitizedBinding"]["forecastTimeSourceSetBound"]:
        raise TransitLiveEvidencePromotionError("post-close case must not bind forecast-time evidence")
    resolution_only = cases["transitlivepromotioncase-005"]
    if resolution_only["gateChecks"]["sourceRoleStatus"] != "resolution_only_rejected":
        raise TransitLiveEvidencePromotionError("resolution-only case must be rejected by role")
    if "source_role_resolution_only" not in resolution_only["rejectionReasons"]:
        raise TransitLiveEvidencePromotionError("resolution-only case must cite source-role rejection")
    if resolution_only["sanitizedBinding"]["forecastTimeSourceSetBound"]:
        raise TransitLiveEvidencePromotionError("resolution-only case must not bind forecast-time evidence")
    boundary = promotion["claimBoundary"]
    blocked = [
        "normalChecksUseLiveNetwork",
        "normalChecksReadLiveWorkspace",
        "rawLiveCapturesCommitted",
        "createsForecastArtifacts",
        "createsResolutionArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "promotesPostCloseEvidence",
        "promotesResolutionOnlyEvidence",
        "productionLiveRuntimeClaimAllowed",
        "allEvidenceClaimAllowed",
    ]
    if any(boundary[item] for item in blocked):
        raise TransitLiveEvidencePromotionError("promotion claim boundary must keep blocked claims false")
    if promotion["readSurface"]["executesPromotion"] or promotion["readSurface"]["readsIgnoredLiveWorkspace"]:
        raise TransitLiveEvidencePromotionError("promotion read surface must be checked and non-executing")


def write_artifacts(source_set: dict[str, Any], promotion: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    SOURCE_SET_PATH.write_text(render_json(source_set), encoding="utf-8")
    PROMOTION_PATH.write_text(render_json(promotion), encoding="utf-8")
    print("generated transit live evidence promotion")


def check_artifact(path: Path, expected: dict[str, Any], label: str) -> None:
    expected_text = render_json(expected)
    if not path.exists():
        print(f"missing {label}: {path}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_live_evidence_promotion.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = path.read_text(encoding="utf-8")
    if actual != expected_text:
        print(f"{label} drift: {path}", file=sys.stderr)
        print("run `python3 scripts/generate_transit_live_evidence_promotion.py --write`", file=sys.stderr)
        raise SystemExit(1)


def check_artifacts(source_set: dict[str, Any], promotion: dict[str, Any]) -> None:
    check_artifact(SOURCE_SET_PATH, source_set, "promoted transit source set")
    check_artifact(PROMOTION_PATH, promotion, "transit live evidence promotion")
    print("checked transit live evidence promotion")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    try:
        source_set = build_promoted_source_set()
        promotion = build_promotion()
        if args.write:
            write_artifacts(source_set, promotion)
        elif args.check:
            check_artifacts(source_set, promotion)
        else:
            sys.stdout.write(render_json(promotion))
    except (OSError, json.JSONDecodeError, TransitLiveEvidencePromotionError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
