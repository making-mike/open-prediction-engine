#!/usr/bin/env python3
"""Generate or check the Helsinki traffic disturbance pilot operations runbook."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from generate_prediction_campaign_calibration_status import build_prediction_campaign_calibration_status
from generate_prediction_campaign_doctor import build_prediction_campaign_doctor
from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_method_update_plan import build_prediction_campaign_method_update_plan
from generate_prediction_campaign_runner import build_prediction_campaign_runner, default_args
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "helsinki-traffic-pilot-runbook"
OUTPUT_PATH = GENERATED / "helsinki-traffic-disturbance-pilot-runbook.generated.json"
SCHEMA = SPEC / "helsinki-traffic-disturbance-pilot-runbook.schema.json"
GENERATED_AT = "2026-05-31T05:00:00Z"
MINI_RUN_COUNT = 3
TARGET_RUN_COUNT = 100


def status_command(
    index: int,
    *,
    key: str,
    command: str,
    answers: str,
    status_path: str,
    requires_live_opt_in: bool = False,
    mutates_state: bool = False,
) -> dict[str, Any]:
    return {
        "commandId": f"helsinkipilotcommand-{index:03d}",
        "commandKey": key,
        "command": command,
        "answers": answers,
        "statusPath": status_path,
        "mutatesState": mutates_state,
        "requiresLiveOptIn": requires_live_opt_in,
    }


def runbook_step(
    index: int,
    *,
    key: str,
    phase: str,
    command: str,
    operator_check: str,
    success_signal: str,
    recovery_action: str,
    claim_boundary: str,
    mutates_state: bool = False,
    requires_live_opt_in: bool = False,
) -> dict[str, Any]:
    return {
        "stepId": f"helsinkipilotstep-{index:03d}",
        "stepNumber": index,
        "stepKey": key,
        "phase": phase,
        "command": command,
        "operatorCheck": operator_check,
        "successSignal": success_signal,
        "recoveryAction": recovery_action,
        "mutatesState": mutates_state,
        "requiresLiveOptIn": requires_live_opt_in,
        "claimBoundary": claim_boundary,
    }


def smoke_check(index: int, *, key: str, expected: str, source_command: str) -> dict[str, Any]:
    return {
        "checkId": f"helsinkipilotsmokecheck-{index:03d}",
        "checkKey": key,
        "expected": expected,
        "sourceCommand": source_command,
    }


def criterion(
    index: int,
    *,
    key: str,
    requirement: str,
    measurement_command: str,
    pass_condition: str,
    blocks_claim: bool = True,
) -> dict[str, Any]:
    return {
        "criterionId": f"helsinkipilotcriterion-{index:03d}",
        "criterionKey": key,
        "requirement": requirement,
        "measurementCommand": measurement_command,
        "passCondition": pass_condition,
        "blocksClaim": blocks_claim,
    }


def abort_criterion(
    index: int,
    *,
    key: str,
    trigger: str,
    detection_command: str,
    required_action: str,
    restart_allowed: bool,
) -> dict[str, Any]:
    return {
        "criterionId": f"helsinkipilotabort-{index:03d}",
        "criterionKey": key,
        "trigger": trigger,
        "detectionCommand": detection_command,
        "requiredAction": required_action,
        "restartAllowed": restart_allowed,
    }


def mini_runner_args() -> argparse.Namespace:
    args = default_args()
    args.plan_count = MINI_RUN_COUNT
    args.count = MINI_RUN_COUNT
    return args


def calibration_progress_percent(comparable: int, threshold: int) -> float:
    return round(min(100.0, comparable / threshold * 100), 2)


def build_operator_status(
    *,
    runner: dict[str, Any],
    doctor: dict[str, Any],
    ledger: dict[str, Any],
    calibration: dict[str, Any],
) -> dict[str, Any]:
    schedule = runner["forecastSchedule"]
    thresholds = calibration["thresholdReadback"]
    comparable = int(thresholds["resolvedComparableSampleSize"])
    excluded = int(thresholds["excludedSampleSize"])
    total = comparable + excluded
    exclusion_rate = round(excluded / total, 6) if total else 0.0
    return {
        "status": "ready_for_three_run_smoke_before_real_pilot",
        "nextForecastRunId": schedule["readyRunId"],
        "nextForecastCreateAt": schedule["nextForecastCreateAt"],
        "nextResolutionRunId": ledger["bindings"]["runId"],
        "nextResolutionEligibleAt": build_prediction_campaign_manifest()["plannedRuns"][0]["resolutionEligibleAt"],
        "dueResolverJobCount": doctor["health"]["dueRunCount"],
        "appendReadyRunCount": doctor["health"]["appendReadyRunCount"],
        "ledgerComparableRowCount": int(ledger["summary"]["comparableRowCount"]),
        "ledgerExcludedRowCount": int(ledger["summary"]["excludedRowCount"]),
        "exclusionRate": exclusion_rate,
        "calibrationComparableCount": comparable,
        "calibrationThreshold": int(thresholds["minimumComparableResolvedForCalibration"]),
        "calibrationProgressPercent": calibration_progress_percent(
            comparable,
            int(thresholds["minimumComparableResolvedForCalibration"]),
        ),
        "statusCommands": [
            status_command(
                1,
                key="next_forecast",
                command="python3 scripts/ope.py prediction-campaign start --view forecast-schedule",
                answers="Next forecast run, create time, close time, and dry-run schedule action.",
                status_path="forecastSchedule",
            ),
            status_command(
                2,
                key="next_resolution",
                command="python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001",
                answers="Next campaign run waiting for or due for resolution.",
                status_path="jobs[*].target.campaignRunId",
            ),
            status_command(
                3,
                key="due_resolver_jobs",
                command="python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z",
                answers="Due resolver jobs and the exact checked resolve command to inspect before execution.",
                status_path="jobs[*].jobStatus",
            ),
            status_command(
                4,
                key="append_readiness",
                command="python3 scripts/ope.py prediction-campaign append-ready",
                answers="Whether a run can append comparable evidence or only an exclusion audit row.",
                status_path="appendCandidate",
            ),
            status_command(
                5,
                key="ledger_counts",
                command="python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary",
                answers="Comparable and excluded row counts for the checked append row shape.",
                status_path="summary",
            ),
            status_command(
                6,
                key="exclusion_rate",
                command="python3 scripts/ope.py prediction-campaign calibration-status --view thresholds",
                answers="Current exclusion rate and maximum exclusion rate allowed before calibration claims.",
                status_path="thresholdReadback.exclusionRate",
            ),
            status_command(
                7,
                key="calibration_threshold_progress",
                command="python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot",
                answers="Comparable resolved count against the 100-outcome calibration threshold when local ledger review is explicit.",
                status_path="pilotReadback",
            ),
        ],
    }


def build_mini_campaign_smoke(mini_runner: dict[str, Any]) -> dict[str, Any]:
    expected_run_ids = [row["runId"] for row in mini_runner["forecastSchedule"]["scheduleRows"]]
    return {
        "smokeStatus": "checked_three_run_smoke_ready",
        "runCount": MINI_RUN_COUNT,
        "targetRunCount": MINI_RUN_COUNT,
        "expectedRunIds": expected_run_ids,
        "commands": [
            status_command(
                101,
                key="mini_plan",
                command="python3 scripts/ope.py prediction-campaign plan --plan-count 3 --count 3",
                answers="Three planned Helsinki morning-peak runs with unique duplicate keys.",
                status_path="plannedRuns",
            ),
            status_command(
                102,
                key="mini_runner_schedule",
                command="python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --view forecast-schedule",
                answers="Three schedule rows covering ready, waiting, and missed-run policies.",
                status_path="forecastSchedule.scheduleRows",
            ),
            status_command(
                103,
                key="mini_foreground_tick",
                command=(
                    "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 "
                    "--watch --max-ticks 1 --output-format jsonl"
                ),
                answers="One bounded foreground tick that does not write state without --write-local.",
                status_path="ticks[0].actions",
            ),
            status_command(
                104,
                key="mini_resolution_queue",
                command="python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --limit 3",
                answers="Campaign-aware resolver queue readback before any resolver execution.",
                status_path="jobs",
            ),
            status_command(
                105,
                key="mini_append_readiness",
                command="python3 scripts/ope.py prediction-campaign append-ready --view candidate",
                answers="Append-readiness gate for the first checked campaign run.",
                status_path="appendCandidate",
            ),
        ],
        "checks": [
            smoke_check(
                1,
                key="three_run_materialization",
                expected="Mini plan contains exactly predictionrun-1301 through predictionrun-1303.",
                source_command="python3 scripts/ope.py prediction-campaign plan --plan-count 3 --count 3",
            ),
            smoke_check(
                2,
                key="forecast_before_close",
                expected="Ready forecast action is only available before forecastCloseAt.",
                source_command="python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --view forecast-schedule",
            ),
            smoke_check(
                3,
                key="no_normal_write",
                expected="Mini smoke commands do not write ignored campaign state unless --write-local is explicit.",
                source_command="python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
            ),
            smoke_check(
                4,
                key="resolution_queue_visible",
                expected="Resolver jobs are visible before outcome execution and remain non-executing.",
                source_command="python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --limit 3",
            ),
            smoke_check(
                5,
                key="append_gate_visible",
                expected="Append readiness is visible and cannot count evidence without resolution and scoring records.",
                source_command="python3 scripts/ope.py prediction-campaign append-ready --view candidate",
            ),
        ],
        "passCondition": "All five mini-smoke commands return valid JSON or JSONL and no command writes campaign state without --write-local.",
        "normalChecksMutateState": False,
    }


def build_runbook_steps() -> list[dict[str, Any]]:
    return [
        runbook_step(
            1,
            key="review_scope",
            phase="setup",
            command="python3 scripts/ope.py prediction-campaign pilot-runbook --view scope",
            operator_check="Confirm geography, service window, 100-run target, source policy, and baseline method boundary.",
            success_signal="Runbook scope reports targetRunCount=100 and bestAvailableMethodId=transitmethod-100.",
            recovery_action="Stop and review source policy or domain setup before any campaign write.",
            claim_boundary="Scope review is not forecast evidence.",
        ),
        runbook_step(
            2,
            key="run_three_run_smoke_plan",
            phase="smoke",
            command="python3 scripts/ope.py prediction-campaign plan --plan-count 3 --count 3",
            operator_check="Confirm exactly three planned runs and no duplicate keys.",
            success_signal="predictionrun-1301 through predictionrun-1303 are present.",
            recovery_action="Fix planning input before the real 100-run campaign.",
            claim_boundary="Mini smoke records are operational checks, not calibration evidence.",
        ),
        runbook_step(
            3,
            key="run_three_run_smoke_tick",
            phase="smoke",
            command=(
                "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 "
                "--watch --max-ticks 1 --output-format jsonl"
            ),
            operator_check="Confirm the foreground tick reports dry_run_ready and zero forecast artifacts created.",
            success_signal="JSONL tick returns without writing state.",
            recovery_action="Do not start the real pilot until the mini tick passes.",
            claim_boundary="Dry-run smoke output must not be counted as pilot evidence.",
        ),
        runbook_step(
            4,
            key="review_full_100_plan",
            phase="setup",
            command="python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization",
            operator_check="Confirm 100 unique planned runs, first/final service dates, and duplicate audit status.",
            success_signal="materializationMode is full_100_run_pilot and duplicateConflictCount is zero.",
            recovery_action="Do not write local state; repair plan inputs first.",
            claim_boundary="A full plan is not evidence until forecasts are created before close and later resolved.",
        ),
        runbook_step(
            5,
            key="create_next_forecast",
            phase="forecast",
            command="python3 scripts/ope.py prediction-campaign start --count 100 --full-materialization --write-local --output-format jsonl",
            operator_check="Run only inside the forecast creation window and keep stdout/logs.",
            success_signal="One ready forecast is created idempotently in .ope/live for the next due run.",
            recovery_action="If close time has passed, record missed and advance; never backfill.",
            claim_boundary="Forecast creation still uses the baseline method until method-update gates permit otherwise.",
            mutates_state=True,
        ),
        runbook_step(
            6,
            key="daily_operator_status",
            phase="monitor",
            command="python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status",
            operator_check="Read next forecast, next resolution, due resolver jobs, append readiness, ledger counts, exclusion rate, and calibration progress.",
            success_signal="Operator status remains internally consistent and below-threshold claims stay blocked.",
            recovery_action="Use doctor/resume when queues disagree or an interrupted state is reported.",
            claim_boundary="Status readbacks do not mutate campaign state or imply model quality.",
        ),
        runbook_step(
            7,
            key="resolve_due_run",
            phase="resolve",
            command=(
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 "
                "--execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local"
            ),
            operator_check="Attach only outcome evidence that is eligible after the horizon ends.",
            success_signal="Resolution and scoring artifacts are written for the due run.",
            recovery_action="If outcome evidence is missing, write an explicit missing-outcome exclusion instead of inventing data.",
            claim_boundary="Outcome rows must be resolution-only and must not change the original forecast.",
            mutates_state=True,
        ),
        runbook_step(
            8,
            key="append_scored_row",
            phase="append",
            command="python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local",
            operator_check="Confirm comparable append checks and provenance are complete.",
            success_signal="Append-only ledger has one more comparable or exclusion row with a stable row key.",
            recovery_action="If checks fail, append an exclusion audit row or leave the run out of comparable evidence.",
            claim_boundary="Ledger append grows evidence but does not itself allow a calibration claim.",
            mutates_state=True,
        ),
        runbook_step(
            9,
            key="review_calibration_threshold",
            phase="calibrate",
            command="python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot",
            operator_check="Confirm comparable count, exclusion rate, provenance completeness, reliability buckets, and confidence caveats.",
            success_signal="At 100 comparable outcomes with acceptable exclusions and provenance, measurement-only calibration is ready.",
            recovery_action="Continue collecting or review exclusions until the threshold is met without unsafe evidence.",
            claim_boundary="Calibration readback is measurement-only and does not update probabilities.",
        ),
        runbook_step(
            10,
            key="review_method_update_after_threshold",
            phase="calibrate",
            command="python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command",
            operator_check="Only after calibration, benchmark, anti-leakage, source-policy, approval, and rollback checks pass.",
            success_signal="Plan-ready command targets transitmethod-101 prospectively and keeps rollback available.",
            recovery_action="If evidence is weak or approvals are missing, continue on transitmethod-100.",
            claim_boundary="The best available method is baseline until an explicit local apply command is approved.",
        ),
        runbook_step(
            11,
            key="recover_or_resume",
            phase="recover",
            command="python3 scripts/ope.py prediction-campaign resume --from-local",
            operator_check="Inspect interrupted state, idempotency keys, queue state, and next safe action.",
            success_signal="Resume readback points to one safe next command without overwriting prior evidence.",
            recovery_action="Escalate manually if duplicate keys, unsafe paths, or malformed local state are present.",
            claim_boundary="Recovery must preserve prior forecasts and append-only evidence.",
        ),
        runbook_step(
            12,
            key="stop_or_abort",
            phase="stop",
            command="python3 scripts/ope.py prediction-campaign pilot-runbook --view abort",
            operator_check="Apply abort criteria for source outages, unsafe evidence, clock drift, path failures, and repeated missed windows.",
            success_signal="Stop condition is documented before any restart.",
            recovery_action="Restart only from a clean mini smoke and explicit resume/readback sequence.",
            claim_boundary="An aborted pilot cannot support quality or calibration claims.",
        ),
    ]


def build_success_criteria() -> list[dict[str, Any]]:
    return [
        criterion(
            1,
            key="hundred_comparable_outcomes",
            requirement="The pilot has at least 100 comparable resolved and scored outcomes.",
            measurement_command="python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot",
            pass_condition="resolvedComparableSampleSize >= 100.",
        ),
        criterion(
            2,
            key="acceptable_exclusion_rate",
            requirement="The exclusion rate is at or below the declared 0.25 maximum.",
            measurement_command="python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback",
            pass_condition="exclusionRate <= maxExclusionRateForCalibrationClaim.",
        ),
        criterion(
            3,
            key="forecast_before_close",
            requirement="Every counted forecast was created before forecastCloseAt.",
            measurement_command="python3 scripts/ope.py prediction-campaign doctor --view duplicates",
            pass_condition="No missed-close or backfilled forecast is counted as comparable evidence.",
        ),
        criterion(
            4,
            key="no_duplicate_forecasts",
            requirement="No campaign date/window duplicate key produced a second forecast.",
            measurement_command="python3 scripts/ope.py prediction-campaign doctor --view duplicates",
            pass_condition="duplicateRiskCount == 0 and duplicateAppendBlocked remains true.",
        ),
        criterion(
            5,
            key="complete_provenance",
            requirement="Every comparable row has forecast, evidence, history, resolution, scoring, and source-policy paths.",
            measurement_command="python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback",
            pass_condition="sourceOutcomeProvenanceComplete is true.",
        ),
        criterion(
            6,
            key="baseline_until_gate",
            requirement="The pilot uses transitmethod-100 until a method-update plan is explicitly approved and applied.",
            measurement_command="python3 scripts/ope.py prediction-campaign method-update-gate",
            pass_condition="methodUpdateAllowed remains false unless plan-ready evidence and approvals exist.",
        ),
    ]


def build_abort_criteria() -> list[dict[str, Any]]:
    return [
        abort_criterion(
            1,
            key="source_outage",
            trigger="Required weather or transit outcome sources are unavailable for repeated due windows.",
            detection_command="python3 scripts/ope.py prediction-campaign doctor --view queues",
            required_action="Pause new writes, append explicit exclusions where appropriate, and resume only after source readiness is restored.",
            restart_allowed=True,
        ),
        abort_criterion(
            2,
            key="unsafe_evidence",
            trigger="A source policy would allow post-close evidence, private rows, credentials, or unapproved inputs.",
            detection_command="python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status",
            required_action="Stop the pilot and replace the source policy before any further forecast or resolution work.",
            restart_allowed=False,
        ),
        abort_criterion(
            3,
            key="clock_drift",
            trigger="Runner clock drift causes repeated missed forecast windows or forecast-after-close risk.",
            detection_command="python3 scripts/ope.py prediction-campaign start --view forecast-schedule",
            required_action="Stop foreground execution and restart only after time synchronization and a clean mini smoke.",
            restart_allowed=True,
        ),
        abort_criterion(
            4,
            key="path_safety_failure",
            trigger="Any local write target escapes the ignored .ope/live prediction-campaign workspace.",
            detection_command="python3 scripts/ope.py prediction-campaign forecast-write",
            required_action="Stop immediately; do not write or append until path safety is repaired.",
            restart_allowed=False,
        ),
        abort_criterion(
            5,
            key="duplicate_or_overwrite_attempt",
            trigger="Duplicate keys, duplicate row keys, or overwrite attempts appear in campaign state.",
            detection_command="python3 scripts/ope.py prediction-campaign doctor --view duplicates",
            required_action="Preserve existing records, block the duplicate, and resume only from the next unique window.",
            restart_allowed=True,
        ),
        abort_criterion(
            6,
            key="repeated_missed_windows",
            trigger="Repeated missed forecast-close windows prevent a meaningful 100-comparable-outcome pilot.",
            detection_command="python3 scripts/ope.py prediction-campaign resume --from-local",
            required_action="Stop the current cycle, summarize exclusions, and restart a fresh cycle after fixing scheduling.",
            restart_allowed=True,
        ),
    ]


def build_helsinki_traffic_pilot_runbook() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    full_manifest = build_prediction_campaign_manifest(target_count=TARGET_RUN_COUNT, full_materialization=True)
    runner = build_prediction_campaign_runner()
    mini_runner = build_prediction_campaign_runner(mini_runner_args())
    doctor = build_prediction_campaign_doctor()
    ledger = build_prediction_campaign_evidence_ledger()
    calibration = build_prediction_campaign_calibration_status()
    method_plan = build_prediction_campaign_method_update_plan()
    first_run = full_manifest["plannedRuns"][0]
    final_run = full_manifest["plannedRuns"][-1]
    success = build_success_criteria()
    abort = build_abort_criteria()
    return {
        "helsinkiTrafficDisturbancePilotRunbookId": "helsinkipilotrunbook-001",
        "generatedAt": GENERATED_AT,
        "runbookStatus": "checked_local_pilot_operations_runbook",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "predictionCampaignDoctorId": doctor["predictionCampaignDoctorId"],
            "predictionCampaignEvidenceLedgerId": ledger["predictionCampaignEvidenceLedgerId"],
            "predictionCampaignCalibrationStatusId": calibration["predictionCampaignCalibrationStatusId"],
            "predictionCampaignMethodUpdatePlanId": method_plan["predictionCampaignMethodUpdatePlanId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
        },
        "pilotScope": {
            "geography": "helsinki",
            "network": "hsl-surface",
            "serviceWindow": first_run["serviceWindow"],
            "timezone": manifest["campaign"]["timezone"],
            "targetRunCount": TARGET_RUN_COUNT,
            "miniSmokeRunCount": MINI_RUN_COUNT,
            "firstServiceDate": first_run["serviceDate"],
            "finalServiceDate": final_run["serviceDate"],
            "bestAvailableMethodId": "transitmethod-100",
            "bestAvailableMethodName": "baseline historical transit-delay frequency",
            "nonBaselineMethodGate": "Use transitmethod-101 only after the method-update gate, plan, approvals, benchmark evidence, and rollback record are ready.",
            "fullMaterializationCommand": "python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization",
            "miniSmokeCommand": "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
            "normalChecksUseLiveNetwork": False,
            "normalChecksWriteLocalState": False,
        },
        "operatorStatus": build_operator_status(
            runner=runner,
            doctor=doctor,
            ledger=ledger,
            calibration=calibration,
        ),
        "runbookSteps": build_runbook_steps(),
        "miniCampaignSmoke": build_mini_campaign_smoke(mini_runner),
        "successCriteria": success,
        "abortCriteria": abort,
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign pilot-runbook",
            "acceptedViews": [
                "runbook",
                "scope",
                "operator-status",
                "smoke",
                "steps",
                "success",
                "abort",
                "summary",
                "boundary",
            ],
            "defaultView": "runbook",
            "capturedStdoutMode": "json",
            "normalChecksWriteLiveState": False,
        },
        "summary": {
            "runbookReady": True,
            "miniCampaignSmokeReady": True,
            "operatorStatusReady": True,
            "successCriteriaCount": len(success),
            "abortCriteriaCount": len(abort),
            "bestAvailableMethodId": "transitmethod-100",
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "recommendedNextCommand": "python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke",
        },
        "executionBoundary": {
            "readOnlyRunbook": True,
            "normalChecksWriteLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "startsLongRunningRunner": False,
            "executesResolvers": False,
            "appendsLedgerRows": False,
            "changesForecastMethod": False,
            "hostedRuntimeAllowed": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This runbook is a checked local operations readback; it does not start the real pilot by itself.",
            "The three-run smoke path must pass before the 100-run pilot is started with explicit local writes.",
            "The best available method remains transitmethod-100 until evidence and approvals explicitly permit a prospective method update.",
            "Calibration after 100 comparable outcomes is measurement-only and does not rewrite historical forecasts or probabilities.",
        ],
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "runbook": record,
        "scope": record["pilotScope"],
        "operator-status": record["operatorStatus"],
        "smoke": record["miniCampaignSmoke"],
        "steps": record["runbookSteps"],
        "success": record["successCriteria"],
        "abort": record["abortCriteria"],
        "summary": record["summary"],
        "boundary": record["executionBoundary"],
    }
    selected = views[view]
    if output_format == "human":
        summary = record["summary"]
        print(
            f"helsinki pilot {record['runbookStatus']} "
            f"target=100 smoke=3 method={summary['bestAvailableMethodId']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(selected), end="")
        return
    print(render_json(selected), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="Helsinki traffic pilot runbook",
        regen="python3 scripts/generate_helsinki_traffic_pilot_runbook.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated Helsinki pilot runbook")
    parser.add_argument("--check", action="store_true", help="check generated Helsinki pilot runbook drift")
    parser.add_argument(
        "--view",
        choices=["runbook", "scope", "operator-status", "smoke", "steps", "success", "abort", "summary", "boundary"],
        default="runbook",
        help="print one Helsinki pilot runbook view",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for readback output",
    )
    args = parser.parse_args()

    record = build_helsinki_traffic_pilot_runbook()
    if args.write or args.check:
        check_or_write(record, write=args.write)
        return
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
