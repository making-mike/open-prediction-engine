#!/usr/bin/env python3
"""Generate or check the Helsinki traffic pilot launch-readiness readback."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from generate_helsinki_traffic_pilot_runbook import build_helsinki_traffic_pilot_runbook
from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_prediction_campaign_runner import build_prediction_campaign_runner, default_args
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "helsinki-traffic-pilot-readiness"
OUTPUT_PATH = GENERATED / "helsinki-traffic-pilot-readiness.generated.json"
SCHEMA = SPEC / "helsinki-traffic-pilot-readiness.schema.json"
GENERATED_AT = "2026-06-01T00:00:00Z"


def launch_command(
    index: int,
    *,
    key: str,
    command: str,
    expected: str,
    mutates_state: bool,
) -> dict[str, Any]:
    return {
        "commandId": f"helsinkireadinesscommand-{index:03d}",
        "commandKey": key,
        "command": command,
        "expected": expected,
        "mutatesState": mutates_state,
        "requiresOperatorSupervision": mutates_state,
    }


def readiness_check(
    index: int,
    *,
    key: str,
    status: str,
    blocks_launch: bool,
    message: str,
    evidence_command: str,
) -> dict[str, Any]:
    return {
        "checkId": f"helsinkireadinesscheck-{index:03d}",
        "checkKey": key,
        "checkStatus": status,
        "blocksLaunch": blocks_launch,
        "message": message,
        "evidenceCommand": evidence_command,
    }


def manual_prerequisite(index: int, *, key: str, requirement: str, confirmation: str, why_manual: str) -> dict[str, Any]:
    return {
        "prerequisiteId": f"helsinkireadinessprereq-{index:03d}",
        "prerequisiteKey": key,
        "requirement": requirement,
        "confirmation": confirmation,
        "whyManual": why_manual,
    }


def blocked_action(index: int, *, key: str, reason: str, safe_alternative: str) -> dict[str, Any]:
    return {
        "blockedActionId": f"helsinkireadinessblocked-{index:03d}",
        "actionKey": key,
        "reason": reason,
        "safeAlternative": safe_alternative,
    }


def mini_runner() -> dict[str, Any]:
    args = default_args()
    args.plan_count = 3
    args.count = 3
    return build_prediction_campaign_runner(args)


def build_checks(runbook: dict[str, Any], full_manifest: dict[str, Any], mini: dict[str, Any]) -> list[dict[str, Any]]:
    duplicate_conflicts = int(full_manifest["materialization"]["duplicateConflictCount"])
    smoke_rows = mini["forecastSchedule"]["scheduleRows"]
    return [
        readiness_check(
            1,
            key="runbook_ready",
            status="pass" if runbook["summary"]["runbookReady"] else "manual_required",
            blocks_launch=not runbook["summary"]["runbookReady"],
            message="The checked operations runbook is available.",
            evidence_command="python3 scripts/ope.py prediction-campaign pilot-runbook --view summary",
        ),
        readiness_check(
            2,
            key="mini_smoke_ready",
            status="pass" if len(smoke_rows) == 3 else "manual_required",
            blocks_launch=len(smoke_rows) != 3,
            message="The 3-run smoke schedule exposes ready, waiting, and missed-run policies.",
            evidence_command="python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke",
        ),
        readiness_check(
            3,
            key="full_materialization_unique",
            status="pass" if duplicate_conflicts == 0 else "manual_required",
            blocks_launch=duplicate_conflicts != 0,
            message="The full 100-run materialization has no duplicate campaign date/window keys.",
            evidence_command="python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization",
        ),
        readiness_check(
            4,
            key="baseline_method_default",
            status="pass" if runbook["summary"]["bestAvailableMethodId"] == "transitmethod-100" else "manual_required",
            blocks_launch=runbook["summary"]["bestAvailableMethodId"] != "transitmethod-100",
            message="The launch path stays on the baseline method until an approved prospective method update exists.",
            evidence_command="python3 scripts/ope.py prediction-campaign method-update-gate",
        ),
        readiness_check(
            5,
            key="forecast_before_close_policy",
            status="pass",
            blocks_launch=False,
            message="The runner policy marks missed windows instead of backfilling forecasts after forecastCloseAt.",
            evidence_command="python3 scripts/ope.py prediction-campaign start --view missed-run-policy",
        ),
        readiness_check(
            6,
            key="operator_source_confirmation",
            status="manual_required",
            blocks_launch=False,
            message="The operator must confirm opt-in source availability and outcome evidence location before effectful writes.",
            evidence_command="python3 scripts/ope.py prediction-campaign pilot-readiness --view manual",
        ),
    ]


def build_manual_prerequisites() -> list[dict[str, Any]]:
    return [
        manual_prerequisite(
            1,
            key="terminal_supervision",
            requirement="Run the pilot from a supervised terminal session with logs retained outside the generated fixture tree.",
            confirmation="Operator confirms foreground terminal supervision before using --write-local.",
            why_manual="Normal checks cannot supervise a long-running local terminal.",
        ),
        manual_prerequisite(
            2,
            key="clock_sync",
            requirement="Confirm the local clock is synchronized before each forecast creation window.",
            confirmation="Operator confirms the clock before running the launch command.",
            why_manual="Clock drift is environmental and cannot be asserted by committed fixtures.",
        ),
        manual_prerequisite(
            3,
            key="source_availability",
            requirement="Confirm opt-in weather and HSL transit outcome sources are available under the declared source policy.",
            confirmation="Operator confirms source availability and policy fit before effectful forecast or resolution commands.",
            why_manual="Normal checks stay offline and do not fetch live source data.",
        ),
        manual_prerequisite(
            4,
            key="outcome_path",
            requirement="Prepare the approved outcome CSV/JSON path for each due resolution.",
            confirmation="Operator confirms outcome files contain only resolution-time evidence.",
            why_manual="Outcome evidence is local pilot data and must not be committed as a generated fixture.",
        ),
        manual_prerequisite(
            5,
            key="workspace_capacity",
            requirement="Confirm the ignored .ope/live workspace has enough local disk headroom for 100 run states and logs.",
            confirmation="Operator confirms capacity before starting the 100-run pilot.",
            why_manual="Disk capacity is machine-local and not stable enough for committed fixture assertions.",
        ),
    ]


def build_launch_commands() -> list[dict[str, Any]]:
    return [
        launch_command(
            1,
            key="readiness",
            command="python3 scripts/ope.py prediction-campaign pilot-readiness",
            expected="Read the launch gate and manual prerequisites.",
            mutates_state=False,
        ),
        launch_command(
            2,
            key="mini_smoke",
            command="python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
            expected="Run one non-mutating 3-run smoke tick.",
            mutates_state=False,
        ),
        launch_command(
            3,
            key="full_plan",
            command="python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization",
            expected="Inspect all 100 planned runs and duplicate keys.",
            mutates_state=False,
        ),
        launch_command(
            4,
            key="launch_first_write",
            command="python3 scripts/ope.py prediction-campaign start --count 100 --full-materialization --write-local --output-format jsonl",
            expected="Create exactly one next-due local campaign forecast before forecastCloseAt.",
            mutates_state=True,
        ),
        launch_command(
            5,
            key="operator_status",
            command="python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status",
            expected="Inspect next forecast, next resolution, append readiness, ledger counts, and calibration progress.",
            mutates_state=False,
        ),
    ]


def build_blocked_actions() -> list[dict[str, Any]]:
    return [
        blocked_action(
            1,
            key="normal_check_launch",
            reason="Normal checks must remain offline and non-mutating.",
            safe_alternative="Use pilot-readiness and mini-smoke readbacks during normal checks.",
        ),
        blocked_action(
            2,
            key="forecast_after_close",
            reason="Backfilled forecasts would violate forecast-before-outcome evidence boundaries.",
            safe_alternative="Record the run as missed and continue with the next eligible service window.",
        ),
        blocked_action(
            3,
            key="method_switch_without_gate",
            reason="Changing methods before calibration, benchmark, approval, and rollback gates would rewrite the pilot premise.",
            safe_alternative="Continue with transitmethod-100 until apply-method-update is explicitly approved and written prospectively.",
        ),
        blocked_action(
            4,
            key="ledger_append_without_resolution",
            reason="Unresolved or unscored rows cannot be comparable evidence.",
            safe_alternative="Resolve and score the local run first, or append only an explicit exclusion audit row.",
        ),
    ]


def build_helsinki_traffic_pilot_readiness() -> dict[str, Any]:
    runbook = build_helsinki_traffic_pilot_runbook()
    manifest = build_prediction_campaign_manifest()
    full_manifest = build_prediction_campaign_manifest(target_count=100, full_materialization=True)
    runner = build_prediction_campaign_runner()
    mini = mini_runner()
    summary = runbook["summary"]
    checks = build_checks(runbook, full_manifest, mini)
    manual = build_manual_prerequisites()
    launch_command_value = (
        "python3 scripts/ope.py prediction-campaign start --count 100 "
        "--full-materialization --write-local --output-format jsonl"
    )
    return {
        "helsinkiTrafficPilotReadinessId": "helsinkireadiness-001",
        "generatedAt": GENERATED_AT,
        "readinessStatus": "checked_ready_for_operator_launch",
        "domain": manifest["domain"],
        "bindings": {
            "helsinkiTrafficDisturbancePilotRunbookId": runbook["helsinkiTrafficDisturbancePilotRunbookId"],
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "predictionCampaignRunnerId": runner["predictionCampaignRunnerId"],
            "campaignId": manifest["campaign"]["campaignId"],
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
        },
        "readinessSummary": {
            "targetRunCount": 100,
            "miniSmokeRunCount": 3,
            "plannedRunCount": len(full_manifest["plannedRuns"]),
            "duplicateConflictCount": full_manifest["materialization"]["duplicateConflictCount"],
            "bestAvailableMethodId": summary["bestAvailableMethodId"],
            "bestAvailableMethodName": runbook["pilotScope"]["bestAvailableMethodName"],
            "localWorkspace": ".ope/live/prediction-campaigns/predictioncampaign-001",
            "launchCommand": launch_command_value,
            "nextRecommendedCommand": "python3 scripts/ope.py prediction-campaign pilot-readiness --view commands",
            "explicitWriteRequired": True,
            "manualLivePrerequisitesRequired": True,
            "normalChecksMutateState": False,
            "qualityClaimAllowed": False,
        },
        "readinessChecks": checks,
        "manualPrerequisites": manual,
        "launchCommands": build_launch_commands(),
        "blockedActions": build_blocked_actions(),
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign pilot-readiness",
            "acceptedViews": [
                "readiness",
                "checks",
                "manual",
                "commands",
                "blocked",
                "summary",
                "boundary",
            ],
            "defaultView": "readiness",
            "capturedStdoutMode": "json",
            "normalChecksWriteLiveState": False,
        },
        "summary": {
            "pilotReadinessImplemented": True,
            "checkedPrerequisitesPassed": all(not item["blocksLaunch"] for item in checks),
            "manualPrerequisitesRequired": True,
            "launchCommandReady": True,
            "miniSmokeFirst": True,
            "bestAvailableMethodId": summary["bestAvailableMethodId"],
            "qualityClaimAllowed": False,
            "recommendedNextCommand": "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
        },
        "executionBoundary": {
            "readOnlyReadback": True,
            "normalChecksWriteLiveState": False,
            "normalChecksUseLiveNetwork": False,
            "startsPilot": False,
            "createsForecastArtifacts": False,
            "executesResolvers": False,
            "appendsLedgerRows": False,
            "changesForecastMethod": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This readiness readback does not start the pilot; effectful launch still requires --write-local.",
            "Manual source, clock, terminal, outcome-path, and workspace-capacity confirmations remain outside normal checks.",
            "The pilot starts on transitmethod-100; method updates remain prospective and approval-gated.",
        ],
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "readiness": record,
        "checks": record["readinessChecks"],
        "manual": record["manualPrerequisites"],
        "commands": record["launchCommands"],
        "blocked": record["blockedActions"],
        "summary": record["summary"],
        "boundary": record["executionBoundary"],
    }
    selected = views[view]
    if output_format == "human":
        summary = record["readinessSummary"]
        print(
            f"pilot readiness {record['readinessStatus']} "
            f"target={summary['targetRunCount']} method={summary['bestAvailableMethodId']}"
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
        label="Helsinki traffic pilot readiness",
        regen="python3 scripts/generate_helsinki_traffic_pilot_readiness.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated Helsinki pilot readiness")
    parser.add_argument("--check", action="store_true", help="check generated Helsinki pilot readiness drift")
    parser.add_argument(
        "--view",
        choices=["readiness", "checks", "manual", "commands", "blocked", "summary", "boundary"],
        default="readiness",
        help="print one Helsinki pilot readiness view",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for readback output",
    )
    args = parser.parse_args()

    record = build_helsinki_traffic_pilot_readiness()
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
