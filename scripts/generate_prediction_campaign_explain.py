#!/usr/bin/env python3
"""Generate or check the prediction-campaign explain readback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_prediction_campaign_calibration_status import build_prediction_campaign_calibration_status
from generate_prediction_campaign_doctor import build_prediction_campaign_doctor
from generate_prediction_campaign_evidence_ledger import build_prediction_campaign_evidence_ledger
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-explain"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-explain.generated.json"
SCHEMA = SPEC / "prediction-campaign-explain.schema.json"
GENERATED_AT = "2026-05-31T04:00:00Z"


def workflow_step(
    index: int,
    *,
    step_key: str,
    command: str,
    expected_readback: str,
    claim_boundary: str,
) -> dict[str, Any]:
    return {
        "stepId": f"campaignexplainstep-{index:03d}",
        "stepKey": step_key,
        "command": command,
        "expectedReadback": expected_readback,
        "mutatesCampaignState": False,
        "fetchesLiveData": False,
        "executesResolvers": False,
        "claimBoundary": claim_boundary,
    }


def explanation_prompt(
    index: int,
    *,
    prompt_key: str,
    question: str,
    answer: str,
    source_command: str,
) -> dict[str, Any]:
    return {
        "promptId": f"campaignexplainprompt-{index:03d}",
        "promptKey": prompt_key,
        "question": question,
        "answer": answer,
        "sourceCommand": source_command,
    }


def error_envelope(index: int, code: str, message: str, next_action: str) -> dict[str, Any]:
    return {
        "errorEnvelopeId": f"campaignexplainerror-{index:03d}",
        "errorCode": code,
        "message": message,
        "sanitized": True,
        "storesPrivateData": False,
        "safeToShowCaller": True,
        "nextAction": next_action,
    }


def agent_readback(index: int, operation: str, command: str, status_path: str) -> dict[str, Any]:
    return {
        "readbackId": f"campaignagentreadback-{index:03d}",
        "operation": operation,
        "cliCommand": command,
        "statusPath": status_path,
        "agentAdapterOperation": f"campaign_{operation}",
        "implementedInAgentAdapter": True,
    }


def build_prediction_campaign_explain() -> dict[str, Any]:
    manifest = build_prediction_campaign_manifest()
    runner = build_prediction_campaign_runner()
    doctor = build_prediction_campaign_doctor()
    ledger = build_prediction_campaign_evidence_ledger()
    calibration = build_prediction_campaign_calibration_status()
    first_run = manifest["plannedRuns"][0]
    health = doctor["health"]
    thresholds = calibration["thresholdReadback"]
    append_candidate = ledger["appendCandidate"]
    return {
        "predictionCampaignExplainId": "predictioncampaignexplain-001",
        "generatedAt": GENERATED_AT,
        "explainStatus": "checked_pilot_readback",
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "predictionCampaignDoctorId": doctor["predictionCampaignDoctorId"],
            "predictionCampaignEvidenceLedgerId": ledger["predictionCampaignEvidenceLedgerId"],
            "predictionCampaignCalibrationStatusId": calibration["predictionCampaignCalibrationStatusId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "runId": first_run["runId"],
            "forecastId": first_run["forecastId"],
            "questionId": first_run["questionId"],
            "sourcePolicyId": first_run["sourcePolicyId"],
        },
        "campaignSnapshot": {
            "recurrenceCaseKey": manifest["campaign"]["recurrenceCaseKey"],
            "plannedRunCount": len(manifest["plannedRuns"]),
            "nextForecastRunId": first_run["runId"],
            "nextQuestionId": first_run["questionId"],
            "nextForecastId": first_run["forecastId"],
            "nextForecastCreateAt": first_run["forecastCreateAt"],
            "nextForecastCloseAt": first_run["forecastCloseAt"],
            "nextResolutionEligibleAt": first_run["resolutionEligibleAt"],
            "currentCampaignHealth": health["campaignHealth"],
            "appendReadiness": append_candidate["candidateStatus"],
            "resolvedComparableSampleSize": thresholds["resolvedComparableSampleSize"],
            "minimumComparableResolvedForCalibration": thresholds["minimumComparableResolvedForCalibration"],
            "postCalibrationAction": calibration["cycleState"]["postCalibrationAction"],
            "qualityClaimAllowed": calibration["summary"]["qualityClaimAllowed"],
            "calibrationClaimAllowed": calibration["summary"]["calibrationClaimAllowed"],
        },
        "explanationPrompts": [
            explanation_prompt(
                1,
                prompt_key="next_forecast",
                question="What is the next forecast the campaign would create?",
                answer=(
                    "The next checked candidate is predictionrun-1301 with forecast-1301/question-1301, "
                    "created no earlier than 2026-06-11T00:00:00Z and before 2026-06-11T04:45:00Z."
                ),
                source_command="python3 scripts/ope.py prediction-campaign status",
            ),
            explanation_prompt(
                2,
                prompt_key="next_resolution",
                question="When can the next forecast be resolved?",
                answer="Resolution for predictionrun-1301 is eligible at 2026-06-11T07:15:00Z, after the service window ends.",
                source_command="python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001",
            ),
            explanation_prompt(
                3,
                prompt_key="evidence_threshold",
                question="How much comparable evidence is needed before calibration claims?",
                answer="The checked calibration threshold is 100 comparable resolved outcomes; this readback has 1.",
                source_command="python3 scripts/ope.py prediction-campaign calibration-status --view thresholds",
            ),
            explanation_prompt(
                4,
                prompt_key="append_boundary",
                question="Can this run append comparable evidence yet?",
                answer="No. The default ledger case is an excluded audit row because checked outcome and scoring records are missing.",
                source_command="python3 scripts/ope.py prediction-campaign append-ready",
            ),
            explanation_prompt(
                5,
                prompt_key="claim_boundary",
                question="Can OPE claim forecast quality or calibration from this campaign?",
                answer="No. The campaign readbacks are local, fixture-safe, and below the declared calibration threshold.",
                source_command="python3 scripts/ope.py prediction-campaign explain --view claims",
            ),
        ],
        "workflowRunbook": [
            workflow_step(
                1,
                step_key="start_100_calibration_sessions",
                command="python3 scripts/ope.py prediction-campaign start --count 100 --calibration-target 100 --output-format jsonl",
                expected_readback="Print bounded runner decisions for a 100-run calibration campaign without writing local state.",
                claim_boundary="A planned 100-run campaign is not evidence; only later comparable resolved outcomes count.",
            ),
            workflow_step(
                2,
                step_key="explain_current_campaign",
                command="python3 scripts/ope.py prediction-campaign explain",
                expected_readback="Summarize next forecast, next resolution, append readiness, calibration threshold, and claim boundary.",
                claim_boundary="The explain readback is descriptive and cannot create forecasts, resolve outcomes, or append evidence.",
            ),
            workflow_step(
                3,
                step_key="inspect_append_readiness",
                command="python3 scripts/ope.py prediction-campaign append-ready --ledger-case comparable_scored",
                expected_readback="Show which checks must pass before a campaign run becomes comparable evidence.",
                claim_boundary="Comparable rows still require explicit append and do not by themselves prove calibration.",
            ),
            workflow_step(
                4,
                step_key="pause_after_calibration",
                command=(
                    "python3 scripts/ope.py prediction-campaign calibration-status "
                    "--calibration-case post_calibration_restart --view cycle"
                ),
                expected_readback="Show the post-calibration pause and next-cycle readback without mutating campaign state.",
                claim_boundary="Post-calibration restart planning does not tune models or change methods automatically.",
            ),
            workflow_step(
                5,
                step_key="resume_after_interruption",
                command="python3 scripts/ope.py prediction-campaign resume --from-local",
                expected_readback="Inspect ignored local campaign state only when explicitly requested by the caller.",
                claim_boundary="Resume is a recovery readback unless a later effectful command writes campaign state.",
            ),
        ],
        "pilotTaskCard": {
            "taskId": "pilotsessiontask-006",
            "scenarioKey": "repeating_prediction_campaign",
            "title": "Explain a repeating prediction campaign",
            "command": "python3 scripts/ope.py prediction-campaign explain",
            "expectedOutcomeClass": "campaign_explain_readback",
            "measures": [
                "task_completion",
                "claim_boundary_comprehension",
                "trust_for_agent_decision_support",
                "runtime_gap_classification",
            ],
            "moderatorPrompt": (
                "Use the campaign explain readback to identify the next forecast, next resolution, evidence threshold, "
                "and claim boundary without treating the campaign as quality or calibration evidence."
            ),
        },
        "agentReadbacks": [
            agent_readback(1, "plan", "python3 scripts/ope.py prediction-campaign plan", "plannedRuns"),
            agent_readback(2, "status", "python3 scripts/ope.py prediction-campaign status", "campaignSnapshot"),
            agent_readback(3, "health", "python3 scripts/ope.py prediction-campaign doctor --view health", "health"),
            agent_readback(4, "append_readiness", "python3 scripts/ope.py prediction-campaign append-ready", "appendCandidate"),
            agent_readback(5, "calibration_status", "python3 scripts/ope.py prediction-campaign calibration-status", "calibrationStatus"),
        ],
        "sanitizedErrorEnvelopes": [
            error_envelope(1, "invalid_interval", "The requested recurrence interval is not supported by the local campaign runner.", "Choose a checked ISO-8601 interval such as P1D."),
            error_envelope(2, "missed_forecast_close", "Forecast close time passed before a forecast artifact could be created.", "Mark the run missed and plan the next eligible run."),
            error_envelope(3, "unavailable_live_source", "The requested live source is unavailable or not enabled for normal checks.", "Use fixture mode or an explicit opt-in live readiness command."),
            error_envelope(4, "duplicate_campaign", "A campaign with the same duplicate key already exists in the checked cycle.", "Read the existing campaign or choose a distinct date/window key."),
            error_envelope(5, "unsafe_source_policy", "The source policy would allow unsafe or unapproved evidence.", "Stop intake and replace the source policy before forecast work."),
            error_envelope(6, "unsupported_post_calibration_action", "The requested post-calibration action is not supported by the local MVP.", "Use stop, continue, pause_then_resume_after, or start_next_cycle_after."),
        ],
        "claimBoundary": {
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "hostedRuntimeAllowed": False,
            "methodUpdateAllowed": False,
            "whyBlocked": (
                "Campaign readbacks are local and below the declared comparable-outcome threshold; "
                "they explain workflow state but do not establish forecast quality."
            ),
        },
        "summary": {
            "campaignExplainImplemented": True,
            "pilotTaskCardReady": True,
            "runbookReady": True,
            "agentAdapterReadbacksImplemented": True,
            "sanitizedErrorEnvelopeExamples": 6,
            "usageTraceEventsSpecified": 10,
            "writesCampaignState": False,
            "recommendedNextAction": "Use the pilot task card to test whether agents can explain campaign state and claim boundaries.",
        },
        "executionBoundary": {
            "readOnlyReadback": True,
            "createsForecastArtifacts": False,
            "writesCampaignState": False,
            "readsIgnoredLiveState": False,
            "writesIgnoredLiveState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "appendsCorpusEvidence": False,
            "updatesCalibration": False,
            "changesForecastMethod": False,
            "startsHostedRuntime": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "Campaign explain is a checked local readback; it does not start polling, create forecasts, or resolve outcomes.",
            "The default evidence ledger row is excluded until checked outcome and scoring records exist.",
            "Calibration summaries are measurement-only and cannot update probabilities or methods automatically.",
        ],
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "explain": record,
        "snapshot": record["campaignSnapshot"],
        "task": record["pilotTaskCard"],
        "workflow": record["workflowRunbook"],
        "errors": record["sanitizedErrorEnvelopes"],
        "agent": record["agentReadbacks"],
        "claims": record["claimBoundary"],
        "summary": record["summary"],
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        snapshot = record["campaignSnapshot"]
        print(
            f"{snapshot['nextForecastRunId']} nextForecast={snapshot['nextForecastId']} "
            f"close={snapshot['nextForecastCloseAt']} calibration={snapshot['resolvedComparableSampleSize']}/"
            f"{snapshot['minimumComparableResolvedForCalibration']} qualityClaimAllowed="
            f"{snapshot['qualityClaimAllowed']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign explain",
        regen="python3 scripts/generate_prediction_campaign_explain.py --write",
    )


def validate_explain(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)


def load_generated_explain() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    record = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_explain(record)
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated campaign explain readback")
    parser.add_argument("--check", action="store_true", help="check generated campaign explain drift")
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["explain", "snapshot", "task", "workflow", "errors", "agent", "claims", "summary", "boundary"],
        default="explain",
        help="print one prediction campaign explain view",
    )
    args = parser.parse_args()
    if args.write or args.check:
        record = build_prediction_campaign_explain()
    else:
        record = load_generated_explain() or build_prediction_campaign_explain()
    if args.write or args.check:
        check_or_write(record, write=args.write)
        return
    validate_explain(record)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
