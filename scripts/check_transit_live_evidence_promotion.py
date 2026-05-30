#!/usr/bin/env python3
"""Check the transit live evidence promotion gate and promoted source set."""

from __future__ import annotations

from generate_transit_live_evidence_promotion import (
    PROMOTED_SOURCE_SET_ID,
    build_promoted_source_set,
    build_promotion,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    source_set = build_promoted_source_set()
    promotion = build_promotion()
    policy = promotion["policyBinding"]
    cases = {item["promotionCaseId"]: item for item in promotion["promotionCases"]}
    boundary = promotion["claimBoundary"]
    read_surface = promotion["readSurface"]
    summary = promotion["readbackSummary"]

    require(
        promotion["promotionMode"] == "checked_policy_bound_live_evidence_promotion",
        "promotion mode should be checked policy-bound promotion",
    )
    require(policy["sourcePolicyId"] == "sourcepolicy-1201", "promotion should bind the source policy")
    require(policy["approvalRequired"] is True, "promotion should require explicit approval")
    require("weather_forecast" in policy["allowedForecastTimeRoles"], "weather should be forecast-time evidence")
    require("planned_service_alerts" in policy["allowedForecastTimeRoles"], "planned alerts should be forecast-time evidence")
    require("transit_delay_outcome" in policy["resolutionOnlyRoles"], "transit outcomes should be resolution-only")
    require("open_meteo_weather" in policy["allowedConnectors"], "Open-Meteo should be allowed by policy")
    require(policy["maxFreshnessSeconds"] == 7200, "freshness policy should be two hours")
    require(not policy["retention"]["rawLocalArtifactsCommitted"], "raw local artifacts should not be committed")
    require(policy["retention"]["sanitizedNormalizedRecordsCommitted"], "sanitized records should be committed")
    require(not policy["normalChecksMayReadLiveWorkspace"], "normal checks should not read .ope/live")
    require(not policy["normalChecksMayFetchLiveNetwork"], "normal checks should not fetch live data")

    require(summary["surfaceCounts"]["committedFixtures"] == 1, "readback should distinguish committed fixtures")
    require(summary["surfaceCounts"]["localLiveDrafts"] == 2, "readback should distinguish local live drafts")
    require(
        summary["surfaceCounts"]["promotedForecastTimeEvidence"] == 1,
        "readback should distinguish promoted forecast-time evidence",
    )
    require(
        summary["surfaceCounts"]["resolutionOnlyEvidence"] == 1,
        "readback should distinguish resolution-only evidence",
    )
    require(summary["surfaceCounts"]["postCloseRejected"] == 2, "post-close captures should be rejected")
    require(summary["surfaceCounts"]["resolutionOnlyRejected"] == 1, "resolution-only captures should be rejected")
    require(summary["promotedEvidenceSourceSetId"] == PROMOTED_SOURCE_SET_ID, "summary should bind promoted source set")

    committed = cases["transitlivepromotioncase-001"]
    require(committed["surfaceType"] == "committed_fixture", "first case should be a committed fixture")
    require(committed["promotionStatus"] == "already_committed_fixture", "fixture case should not need promotion")
    require(committed["inputBinding"]["sourcePathCommitted"], "fixture source path should be committed")
    require(not committed["inputBinding"]["localLiveWorkspace"], "fixture source should not be .ope/live")

    pending = cases["transitlivepromotioncase-002"]
    require(pending["surfaceType"] == "local_live_draft", "pending case should be a local live draft")
    require(pending["promotionStatus"] == "pending_approval", "draft should wait for approval")
    require(pending["inputBinding"]["sourcePath"].startswith(".ope/live/"), "draft should remain under .ope/live")
    require(not pending["sanitizedBinding"]["forecastTimeSourceSetBound"], "draft should not be bound")

    promoted = cases["transitlivepromotioncase-003"]
    checks = promoted["gateChecks"]
    binding = promoted["sanitizedBinding"]
    require(promoted["surfaceType"] == "promoted_forecast_time_evidence", "accepted case should be promoted evidence")
    require(promoted["promotionStatus"] == "promoted", "accepted case should be promoted")
    require(checks["sourcePolicyStatus"] == "passed", "accepted case should pass source policy")
    require(checks["captureTimingStatus"] == "pre_close", "accepted case should be captured before close")
    require(checks["freshnessStatus"] == "within_policy", "accepted case should pass freshness")
    require(checks["freshnessSeconds"] <= checks["maxFreshnessSeconds"], "accepted case should stay fresh")
    require(checks["sourceRoleStatus"] == "forecast_time_allowed", "accepted case should use forecast-time role")
    require(checks["leakageStatus"] == "passed", "accepted case should pass leakage")
    require(checks["provenanceStatus"] == "bound", "accepted case should bind provenance")
    require(binding["bindingStatus"] == "bound_promoted_source_set", "accepted case should bind a source set")
    require(binding["forecastTimeSourceSetBound"], "accepted case should be forecast-time source set evidence")
    require(binding["evidenceSourceSetId"] == PROMOTED_SOURCE_SET_ID, "accepted case should expose source set ID")
    require(not binding["rawRowsIncluded"], "promoted source set should not include raw rows")
    require(not binding["rawLocalPathCommitted"], "promoted source set should not commit raw path")
    require(binding["sanitizedArtifactCommitted"], "promoted source set should commit sanitized artifact")
    require(binding["contentHashStored"], "promoted source set should store content hash")

    post_close = cases["transitlivepromotioncase-004"]
    require(post_close["promotionStatus"] == "rejected", "post-close capture should be rejected")
    require(post_close["gateChecks"]["captureTimingStatus"] == "post_close", "post-close case should show timing")
    require(
        post_close["gateChecks"]["leakageStatus"] == "rejected_post_close",
        "post-close case should fail leakage",
    )
    require("capture_after_forecast_close" in post_close["rejectionReasons"], "post-close rejection should be explicit")
    require(not post_close["sanitizedBinding"]["forecastTimeSourceSetBound"], "post-close case should not bind source set")

    resolution = cases["transitlivepromotioncase-005"]
    require(resolution["surfaceType"] == "resolution_only_evidence", "final case should be resolution-only")
    require(resolution["sourceRole"] == "transit_delay_outcome", "resolution case should use outcome role")
    require(
        resolution["gateChecks"]["sourceRoleStatus"] == "resolution_only_rejected",
        "resolution-only case should fail role check",
    )
    require(
        resolution["gateChecks"]["leakageStatus"] == "rejected_resolution_only",
        "resolution-only case should fail leakage",
    )
    require(
        "source_role_resolution_only" in resolution["rejectionReasons"],
        "resolution-only rejection should be explicit",
    )
    require(not resolution["sanitizedBinding"]["forecastTimeSourceSetBound"], "resolution-only case should not bind source set")

    require(source_set["evidenceSourceSetId"] == PROMOTED_SOURCE_SET_ID, "source set ID should match readback")
    require(source_set["sourcePolicyId"] == policy["sourcePolicyId"], "source set should bind policy")
    require(source_set["executionMode"] == "live_fetch", "source set should preserve live_fetch mode")
    require(source_set["records"][0]["sourceRole"] == "forecast_input", "source set record should be forecast input")
    require(source_set["records"][0]["connector"] == "open_meteo_weather", "source set should use Open-Meteo")
    require(
        source_set["records"][0]["sourceQuality"]["freshnessStatus"] == "within_policy",
        "source set should pass freshness",
    )
    require(not source_set["provenanceSummary"]["allEvidenceClaimed"], "source set should not claim all evidence")
    require(source_set["controls"]["liveFetch"] is True, "source set should preserve live fetch provenance")
    require(source_set["controls"]["effectfulGeneration"] is False, "source set should not generate forecasts")

    for key, value in boundary.items():
        if key == "normalChecksUseLiveNetwork":
            require(value is False, "normal checks must stay offline")
        else:
            require(value is False, f"claim boundary should keep {key} false")
    require(read_surface["distinguishesEvidenceSurfaces"], "read surface should distinguish surfaces")
    require(read_surface["returnsPromotedSourceSetBinding"], "read surface should return source-set binding")
    require(not read_surface["executesPromotion"], "read surface should not execute promotion")
    require(not read_surface["readsIgnoredLiveWorkspace"], "read surface should not read .ope/live")
    require(not read_surface["fetchesLiveData"], "read surface should not fetch live data")

    print("checked transit live evidence promotion")


if __name__ == "__main__":
    main()
