#!/usr/bin/env python3
"""Generate or check the repeating prediction setup contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_domain_setups import build_transit_setup
from generate_transit_baseline_track_record_gate import build_gate
from generate_transit_live_evidence_promotion import build_promotion
from generate_transit_method_options import build_options as build_transit_method_options
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json, validate_and_emit


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "repeating-prediction-setup"
OUTPUT_PATH = GENERATED / "ope-repeating-prediction-setup.generated.json"
SCHEMA = SPEC / "repeating-prediction-setup.schema.json"
GENERATED_AT = "2026-05-28T12:00:00Z"

SCHEDULE_POLICY_ORDER = [
    "fixed_count",
    "until_date",
    "open_ended",
    "interval",
    "selected_weekdays_window",
    "calibration_threshold",
]

EXAMPLE_ORDER = [
    "daily_100_run_transit_calibration",
    "hourly_short_horizon_count",
    "weekly_until_date_campaign",
    "open_ended_monitoring_campaign",
    "weekday_peak_window_campaign",
    "post_calibration_restart_campaign",
]

POST_CALIBRATION_ACTIONS = [
    "stop",
    "continue",
    "pause_then_resume_after",
    "start_next_cycle_after",
]


class RepeatingPredictionSetupError(Exception):
    pass


def supported_schedule_policy(
    kind: str,
    description: str,
    duration_examples: list[str],
    end_condition_kinds: list[str],
) -> dict[str, Any]:
    return {
        "policyKind": kind,
        "description": description,
        "durationExamples": duration_examples,
        "endConditionKinds": end_condition_kinds,
        "requiresExplicitTimezone": True,
    }


def build_supported_schedule_policies() -> list[dict[str, Any]]:
    return [
        supported_schedule_policy(
            "fixed_count",
            "Run until a declared number of forecast windows has been created or skipped with explicit reasons.",
            ["P1D", "P1W"],
            ["fixed_count", "manual_stop"],
        ),
        supported_schedule_policy(
            "until_date",
            "Run on the declared recurrence until the setup reaches a final timestamp.",
            ["P1D", "P1W", "P14D"],
            ["until_date", "manual_stop"],
        ),
        supported_schedule_policy(
            "open_ended",
            "Continue planning forecast windows until a caller stops, pauses, or a post-calibration policy applies.",
            ["PT1H", "P1D"],
            ["open_ended", "manual_stop", "calibration_threshold"],
        ),
        supported_schedule_policy(
            "interval",
            "Use an explicit ISO-8601-like duration interval for hourly, multi-hour, daily, weekly, or custom runs.",
            ["PT1H", "PT3H", "PT6H", "P1D", "P3D", "P1W"],
            ["fixed_count", "until_date", "manual_stop"],
        ),
        supported_schedule_policy(
            "selected_weekdays_window",
            "Run only on selected weekdays and named service windows while preserving explicit close and horizon rules.",
            ["P1D", "P1W"],
            ["fixed_count", "until_date", "manual_stop"],
        ),
        supported_schedule_policy(
            "calibration_threshold",
            "Run until a declared comparable resolved threshold is reached for track-record or calibration readback.",
            ["P1D", "P1W"],
            ["calibration_threshold", "track_record_threshold", "manual_stop"],
        ),
    ]


def post_calibration_policy(action: str, delay: str, next_cycle_rule: str, notes: str) -> dict[str, Any]:
    return {
        "action": action,
        "delay": delay,
        "nextCycleRule": next_cycle_rule,
        "automaticMethodChangeAllowed": False,
        "notes": notes,
    }


def build_post_calibration_policies() -> list[dict[str, Any]]:
    return [
        post_calibration_policy(
            "stop",
            "none",
            "Stop the setup after the declared calibration threshold is reached.",
            "Calibration measurement does not automatically tune or replace the forecasting method.",
        ),
        post_calibration_policy(
            "continue",
            "none",
            "Keep collecting comparable evidence after calibration without changing method behavior.",
            "Useful when the caller wants ongoing monitoring rather than a finite calibration campaign.",
        ),
        post_calibration_policy(
            "pause_then_resume_after",
            "P14D",
            "Pause the next cycle for the declared delay, then resume with a new cycle identifier.",
            "The campaign manifest milestone will define how pause and resume state is stored.",
        ),
        post_calibration_policy(
            "start_next_cycle_after",
            "P30D",
            "Close the current cycle and start the next cycle after the declared delay.",
            "This preserves calibration evidence by cycle instead of silently mixing cycles.",
        ),
    ]


def schedule_policy(
    index: int,
    kind: str,
    interval: str,
    next_candidate: str,
    forecast_create_rule: str,
    horizon_rule: str,
    *,
    target_count: int | None = None,
    until_date: str | None = None,
    selected_weekdays: list[str] | None = None,
    selected_windows: list[str] | None = None,
    threshold_metric: str | None = None,
    threshold_value: int | None = None,
    open_ended: bool | None = None,
) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "schedulePolicyId": f"repeatingschedulepolicy-{index:03d}",
        "policyKind": kind,
        "interval": interval,
        "timezone": "Europe/Helsinki",
        "forecastCreateRule": forecast_create_rule,
        "forecastCloseRule": "Create and close each forecast before the declared horizon starts; missed close times are skipped, not backfilled.",
        "horizonRule": horizon_rule,
        "resolutionDueRule": "Resolution is eligible only after the service window ends and resolution-only evidence is available.",
        "nextForecastCandidateAt": next_candidate,
    }
    if target_count is not None:
        policy["targetCount"] = target_count
    if until_date is not None:
        policy["untilDate"] = until_date
    if selected_weekdays is not None:
        policy["selectedWeekdays"] = selected_weekdays
    if selected_windows is not None:
        policy["selectedWindows"] = selected_windows
    if threshold_metric is not None:
        policy["thresholdMetric"] = threshold_metric
    if threshold_value is not None:
        policy["thresholdValue"] = threshold_value
    if open_ended is not None:
        policy["openEnded"] = open_ended
    return policy


def end_condition(
    kind: str,
    behavior: str,
    *,
    target_count: int | None = None,
    target_date: str | None = None,
    threshold_metric: str | None = None,
    threshold_value: int | None = None,
) -> dict[str, Any]:
    condition: dict[str, Any] = {
        "conditionKind": kind,
        "behaviorWhenReached": behavior,
    }
    if target_count is not None:
        condition["targetCount"] = target_count
    if target_date is not None:
        condition["targetDate"] = target_date
    if threshold_metric is not None:
        condition["thresholdMetric"] = threshold_metric
    if threshold_value is not None:
        condition["thresholdValue"] = threshold_value
    return condition


def campaign_example(
    index: int,
    case_key: str,
    title: str,
    schedule: dict[str, Any],
    end_conditions: list[dict[str, Any]],
    post_policy: dict[str, Any],
) -> dict[str, Any]:
    return {
        "exampleId": f"repeatingsetupexample-{index:03d}",
        "caseKey": case_key,
        "title": title,
        "schedulePolicy": schedule,
        "endConditions": end_conditions,
        "postCalibrationPolicy": post_policy,
        "requiredRunBoundaries": [
            "forecast_before_close",
            "resolve_after_horizon",
            "source_policy_binding",
            "resolution_only_evidence_excluded_from_forecast_inputs",
            "unique_run_question_forecast_resolution_score_ids",
        ],
        "nextAction": "Use Milestone 92 campaign manifest planning before any runner creates forecast artifacts.",
        "createsForecastArtifacts": False,
        "mutatesCampaignState": False,
    }


def build_campaign_examples(post_policies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_action = {policy["action"]: policy for policy in post_policies}
    return [
        campaign_example(
            1,
            "daily_100_run_transit_calibration",
            "Daily 100-run weather-transit-delay calibration campaign",
            schedule_policy(
                1,
                "fixed_count",
                "P1D",
                "2026-06-11T00:00:00Z",
                "Create one same-day morning-peak forecast at 02:00 local time for each service date.",
                "Horizon covers the same-day morning peak transit window.",
                target_count=100,
                selected_windows=["morning_peak"],
            ),
            [
                end_condition(
                    "fixed_count",
                    "Stop planning after 100 forecast windows are created or explicitly skipped.",
                    target_count=100,
                )
            ],
            by_action["stop"],
        ),
        campaign_example(
            2,
            "hourly_short_horizon_count",
            "Hourly short-horizon count-bounded campaign",
            schedule_policy(
                2,
                "interval",
                "PT1H",
                "2026-06-10T09:00:00Z",
                "Create the next forecast at the top of the hour when close time is still before the target horizon.",
                "Horizon covers the next one-hour operating window after forecast close.",
                target_count=24,
            ),
            [
                end_condition(
                    "fixed_count",
                    "Stop after 24 hourly windows or explicit manual stop.",
                    target_count=24,
                )
            ],
            by_action["continue"],
        ),
        campaign_example(
            3,
            "weekly_until_date_campaign",
            "Weekly until-date campaign",
            schedule_policy(
                3,
                "until_date",
                "P1W",
                "2026-06-17T00:00:00Z",
                "Create one weekly forecast before the declared weekly service window closes.",
                "Horizon covers the named weekly service window.",
                until_date="2026-09-30T20:59:59Z",
                selected_windows=["weekday_peak"],
            ),
            [
                end_condition(
                    "until_date",
                    "Stop after the final eligible forecast window at or before the until timestamp.",
                    target_date="2026-09-30T20:59:59Z",
                )
            ],
            by_action["stop"],
        ),
        campaign_example(
            4,
            "open_ended_monitoring_campaign",
            "Open-ended daily monitoring campaign",
            schedule_policy(
                4,
                "open_ended",
                "P1D",
                "2026-06-11T00:00:00Z",
                "Create a daily forecast until the caller stops or a post-calibration policy applies.",
                "Horizon covers the same-day service window chosen by the setup.",
                open_ended=True,
                selected_windows=["morning_peak"],
            ),
            [
                end_condition(
                    "open_ended",
                    "Continue until manual stop, campaign pause, or calibration policy transition.",
                )
            ],
            by_action["continue"],
        ),
        campaign_example(
            5,
            "weekday_peak_window_campaign",
            "Selected weekday morning-peak campaign",
            schedule_policy(
                5,
                "selected_weekdays_window",
                "P1D",
                "2026-06-11T00:00:00Z",
                "Create forecasts only for selected weekday service windows.",
                "Horizon covers the selected weekday morning peak window.",
                target_count=30,
                selected_weekdays=["monday", "tuesday", "wednesday", "thursday", "friday"],
                selected_windows=["morning_peak"],
            ),
            [
                end_condition(
                    "track_record_threshold",
                    "Stop when 30 comparable resolved outcomes are appended or when the caller stops.",
                    threshold_metric="comparable_resolved_outcomes",
                    threshold_value=30,
                )
            ],
            by_action["continue"],
        ),
        campaign_example(
            6,
            "post_calibration_restart_campaign",
            "Open-ended campaign that restarts after calibration",
            schedule_policy(
                6,
                "calibration_threshold",
                "P1D",
                "2026-06-11T00:00:00Z",
                "Create daily forecasts until the comparable calibration threshold is reached.",
                "Horizon covers the same-day morning peak transit window.",
                threshold_metric="comparable_resolved_outcomes",
                threshold_value=100,
                open_ended=True,
                selected_windows=["morning_peak"],
            ),
            [
                end_condition(
                    "calibration_threshold",
                    "Trigger the post-calibration restart policy after 100 comparable resolved outcomes.",
                    threshold_metric="comparable_resolved_outcomes",
                    threshold_value=100,
                )
            ],
            by_action["pause_then_resume_after"],
        ),
    ]


def build_contract_requirements() -> list[dict[str, Any]]:
    rows = [
        (
            "forecast_before_close",
            "Every run must create and close its forecast before the target horizon starts; missed windows are skipped rather than backfilled.",
        ),
        (
            "resolve_after_horizon",
            "Resolution is eligible only after the declared horizon ends and the resolution source is allowed by policy.",
        ),
        (
            "source_policy_binding",
            "Each run must preserve the source policy ID, allowed forecast-time roles, and resolution-only role boundary.",
        ),
        (
            "resolution_only_evidence_boundary",
            "Post-window transit outcomes and feed-health rows can resolve or explain runs but cannot become forecast inputs.",
        ),
        (
            "unique_run_id_boundary",
            "Campaign manifests must mint unique run, question, forecast, resolution, and scoring IDs instead of reusing fixture IDs.",
        ),
        (
            "local_transport_neutral_boundary",
            "The setup names recurrence semantics without creating cron files, OS scheduler jobs, hosted workers, or transport-specific tasks.",
        ),
    ]
    return [
        {
            "requirementId": f"repeatingsetuprequirement-{index:03d}",
            "requirementKey": key,
            "description": description,
            "enforcedByCurrentContract": True,
        }
        for index, (key, description) in enumerate(rows, start=1)
    ]


def build_repeating_prediction_setup() -> dict[str, Any]:
    domain_setup = build_transit_setup()
    method_options = build_transit_method_options()
    track_gate = build_gate()
    live_promotion = build_promotion()
    post_policies = build_post_calibration_policies()
    examples = build_campaign_examples(post_policies)
    setup = {
        "repeatingPredictionSetupId": "repeatingpredictionsetup-001",
        "generatedAt": GENERATED_AT,
        "setupStatus": "contract_ready_non_executing",
        "domain": "weather-transit-delays",
        "bindings": {
            "domainSetupId": domain_setup["domainSetupId"],
            "sourcePolicyId": live_promotion["policyBinding"]["sourcePolicyId"],
            "transitMethodOptionsId": method_options["transitMethodOptionsId"],
            "transitBaselineTrackRecordGateId": track_gate["transitBaselineTrackRecordGateId"],
            "transitLiveEvidencePromotionId": live_promotion["transitLiveEvidencePromotionId"],
            "referenceDomainSetupPath": "spec/fixtures/generated/domain-setups/weather-transit-delays-domain-setup.generated.json",
            "methodOptionsPath": "spec/fixtures/generated/transit-method-options/transit-method-options.generated.json",
            "trackRecordGatePath": "spec/fixtures/generated/transit-baseline-track-record-gate/transit-baseline-track-record-gate.generated.json",
            "liveEvidencePromotionPath": "spec/fixtures/generated/transit-live-evidence-promotion/transit-live-evidence-promotion.generated.json",
        },
        "forecastTemplate": {
            "templateId": "repeatforecasttemplate-001",
            "questionTemplate": "Will HSL surface transit delay risk exceed the declared threshold for {service_window} in {geography} on {service_date}?",
            "outputType": "binary",
            "domain": "weather-transit-delays",
            "entityScope": {
                "network": "hsl-surface",
                "geography": "helsinki",
                "serviceWindow": "morning_peak",
            },
            "forecastCloseRule": "Forecast must be created and closed before the target service window starts.",
            "methodBoundary": "Use baseline-only execution until comparable resolved evidence reaches method-selection thresholds.",
            "uniqueIdBoundary": "Milestone 92 campaign manifests must mint new IDs for every live campaign run.",
        },
        "sourcePolicyBinding": {
            "sourcePolicyId": live_promotion["policyBinding"]["sourcePolicyId"],
            "allowedForecastTimeRoles": live_promotion["policyBinding"]["allowedForecastTimeRoles"],
            "resolutionOnlyRoles": live_promotion["policyBinding"]["resolutionOnlyRoles"],
            "allowedConnectors": live_promotion["policyBinding"]["allowedConnectors"],
            "callerApprovalRequired": live_promotion["policyBinding"]["approvalRequired"],
            "provenanceRequired": True,
            "normalChecksMayFetchLiveNetwork": False,
            "rawLocalArtifactsCommitted": False,
        },
        "resolutionPolicy": {
            "resolutionRole": "transit_delay_outcome",
            "resolveAfterHorizon": True,
            "resolutionDueRule": "Resolve only after the service window ends, then score against the baseline using declared resolution-only evidence.",
            "resolverCommandBoundary": "Campaign runners may call checked resolver commands only after explicit local execution flags in later milestones.",
            "scoringRule": "brier",
            "ambiguousOutcomeHandling": "Ambiguous outcomes remain excluded from comparable track-record and calibration counts.",
            "annulledOutcomeHandling": "Annulled service windows remain excluded with explicit reason codes.",
        },
        "supportedSchedulePolicies": build_supported_schedule_policies(),
        "postCalibrationPolicies": post_policies,
        "campaignExamples": examples,
        "nextRunReadback": {
            "readbackStatus": "contract_only_example",
            "nextForecastCandidateAt": "2026-06-11T00:00:00Z",
            "nextResolutionEligibleAt": "2026-06-11T07:00:00Z",
            "stopDecisionAvailable": True,
            "requiresCampaignManifest": True,
            "requiresRunner": True,
        },
        "contractRequirements": build_contract_requirements(),
        "summary": {
            "supportedSchedulePolicyCount": len(SCHEDULE_POLICY_ORDER),
            "campaignExampleCount": len(examples),
            "postCalibrationActionCount": len(post_policies),
            "finiteCampaignSupported": True,
            "untilDateCampaignSupported": True,
            "openEndedCampaignSupported": True,
            "calibrationThresholdSupported": True,
            "runnerImplemented": False,
            "campaignManifestImplemented": False,
            "hostedSchedulerAllowed": False,
            "qualityClaimAllowed": False,
            "recommendedNextMilestone": "Milestone 92: Local Prediction Campaign Manifest",
        },
        "executionBoundary": {
            "readOnlyContract": True,
            "createsForecastArtifacts": False,
            "mutatesCampaignState": False,
            "startsScheduler": False,
            "installsOsScheduler": False,
            "writesCron": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This contract defines recurrence semantics only; it does not start forecasts, sleep, poll, resolve, score, or append evidence.",
            "Live forecast-time source use remains opt-in and policy-bound; normal checks stay deterministic and offline.",
            "Calibration thresholds describe when a readback may be generated, not permission to auto-tune methods or make public quality claims.",
            "Campaign state, duplicate prevention, resume behavior, and append-only ledgers are deferred to later milestones.",
        ],
    }
    return setup


def print_section(setup: dict[str, Any], section: str) -> None:
    sections = {
        "template": setup["forecastTemplate"],
        "schedules": setup["supportedSchedulePolicies"],
        "examples": setup["campaignExamples"],
        "requirements": setup["contractRequirements"],
        "boundary": setup["executionBoundary"],
        "summary": setup["summary"],
    }
    print(render_json(sections[section]), end="")


def print_case(setup: dict[str, Any], case_key: str) -> None:
    cases = {item["caseKey"]: item for item in setup["campaignExamples"]}
    if case_key not in cases:
        raise RepeatingPredictionSetupError(f"Unknown repeating setup case: {case_key}")
    print(render_json(cases[case_key]), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(data, SCHEMA, OUTPUT_PATH, write=write, label="repeating prediction setup", regen="python3 scripts/generate_repeating_prediction_setup.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated repeating prediction setup")
    parser.add_argument("--check", action="store_true", help="check generated repeating prediction setup drift")
    parser.add_argument(
        "--section",
        choices=["template", "schedules", "examples", "requirements", "boundary", "summary"],
        help="print one repeating prediction setup section",
    )
    parser.add_argument(
        "--case",
        choices=EXAMPLE_ORDER,
        help="print one checked repeating prediction setup example",
    )
    args = parser.parse_args()

    setup = build_repeating_prediction_setup()
    if args.write or args.check:
        check_or_write(setup, write=args.write)
        return
    if args.section:
        print_section(setup, args.section)
        return
    if args.case:
        print_case(setup, args.case)
        return
    errors = validate_record(setup, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(render_json(setup), end="")


if __name__ == "__main__":
    main()
