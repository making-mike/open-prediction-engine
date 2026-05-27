#!/usr/bin/env python3
"""Generate or check the local private setup orchestrator summary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_first_actions import build_actions
from generate_private_setup_requests import build_request_set, render_json
from generate_source_adapter_intake import build_records as build_source_adapter_intake_records
from generate_source_handoff_method_gate import build_records as build_source_handoff_method_records
from generate_source_intake_handoff import build_handoffs
from ope_schema import SPEC, validate_record
from read_ope_record import read_record
from run_source_handoff_forecast import build_outputs as build_source_handoff_forecast_outputs


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-orchestrator"
ORCHESTRATOR_PATH = GENERATED / "ope-private-setup-orchestrator.generated.json"
SCHEMA = SPEC / "private-setup-orchestrator.schema.json"
GENERATED_AT = "2026-06-10T05:10:00Z"

CASE_ORDER = [
    "local_file_confirmed",
    "source_adapter_output_accepted",
    "missing_approval",
    "unconfirmed_mapping",
    "insufficient_data",
    "rejected_source",
    "unsafe_source",
    "response_too_large",
]


class PrivateSetupOrchestratorError(Exception):
    pass


def null_readback() -> dict[str, None]:
    return {
        "forecastCardStatus": None,
        "forecastBundleStatus": None,
        "resolutionStatus": None,
        "scoreStatus": None,
        "qualityClaimStatus": None,
    }


def chain(
    *,
    request: bool,
    first_action: bool,
    intake: bool,
    method: bool,
    forecast: bool,
    readback: bool,
) -> dict[str, bool]:
    return {
        "requestClassified": request,
        "firstActionRead": first_action,
        "sourceIntakeValidated": intake,
        "methodDecisionValidated": method,
        "forecastExecutionRun": forecast,
        "normalReadbackRun": readback,
    }


def request_rows() -> dict[str, dict[str, Any]]:
    return {row["selectedSourceKind"]: row for row in build_request_set()["requestRows"]}


def action_rows() -> dict[str, dict[str, Any]]:
    return {row["sourceKind"]: row for row in build_actions()}


def adapter_rows(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["case"]: row for row in matrix["intakeCases"]}


def local_file_confirmed_run() -> dict[str, Any]:
    requests = request_rows()
    actions = action_rows()
    handoffs = build_handoffs()
    method_records = build_source_handoff_method_records()
    forecast_outputs = build_source_handoff_forecast_outputs()
    handoff, _build, _manifest, _field_mapping, _report = handoffs["confirmed_builder_draft"]
    method_summary, _gate, _decision = method_records["confirmed_builder_draft"]
    forecast_run = forecast_outputs[
        "weather-logistics-confirmed-builder-draft-source-handoff-setup-forecast-run.generated.json"
    ]
    card = read_record("forecast-card", "forecast-1102", "question-1102")["record"]
    bundle = read_record("forecast-bundle", "forecast-1102", "question-1102")["record"]
    request = requests["local_file"]
    action = actions["local_file"]
    return {
        "orchestratorRunId": "privatesetuporchestratorrun-001",
        "runCase": "local_file_confirmed",
        "sourceKind": "local_file",
        "privateSetupRequestId": request["privateSetupRequestId"],
        "sourceAdapterOutputId": None,
        "sourceAdapterIntakeCaseId": None,
        "sourceIntakeReportId": handoff["sourceIntakeReportId"],
        "sourceIntakeStatus": handoff["sourceIntakeStatus"],
        "setupMethodDecisionId": method_summary["setupMethodDecisionId"],
        "setupBenchmarkGateId": method_summary["setupBenchmarkGateId"],
        "setupForecastRunId": forecast_run["setupForecastRunId"],
        "forecastId": forecast_run["recordBinding"]["forecastId"],
        "questionId": forecast_run["recordBinding"]["questionId"],
        "forecastCardId": card["cardId"],
        "forecastBundleId": bundle["bundleId"],
        "orchestratorStatus": "completed_forecast_readback",
        "nextAction": "read_forecast_card",
        "chain": chain(request=True, first_action=True, intake=True, method=True, forecast=True, readback=True),
        "readbackSummary": {
            "forecastCardStatus": card["status"],
            "forecastBundleStatus": bundle["status"],
            "resolutionStatus": card["resolution"]["status"],
            "scoreStatus": card["score"]["scoreStatus"] if card["score"] else None,
            "qualityClaimStatus": card["qualityClaim"]["status"],
        },
        "forecastArtifactsPresent": True,
        "qualityClaimAllowed": False,
        "blockedReasons": [],
        "requiredActions": [
            action["error"]["message"],
            "Read the generated forecast card or lifecycle bundle; do not infer quality claims from one resolved handoff outcome.",
        ],
    }


def source_adapter_accepted_run(adapter_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "orchestratorRunId": "privatesetuporchestratorrun-002",
        "runCase": "source_adapter_output_accepted",
        "sourceKind": "source_adapter_output",
        "privateSetupRequestId": None,
        "sourceAdapterOutputId": adapter_row["sourceAdapterOutputId"],
        "sourceAdapterIntakeCaseId": adapter_row["caseId"],
        "sourceIntakeReportId": adapter_row["intakeRoute"]["sourceIntakeReportId"],
        "sourceIntakeStatus": adapter_row["intakeRoute"]["sourceIntakeStatus"],
        "setupMethodDecisionId": adapter_row["methodGateSummary"]["setupMethodDecisionId"],
        "setupBenchmarkGateId": adapter_row["methodGateSummary"]["setupBenchmarkGateId"],
        "setupForecastRunId": None,
        "forecastId": None,
        "questionId": None,
        "forecastCardId": None,
        "forecastBundleId": None,
        "orchestratorStatus": "ready_for_forecast_execution",
        "nextAction": "run_explicit_setup_forecast_execution",
        "chain": chain(request=True, first_action=True, intake=True, method=True, forecast=False, readback=False),
        "readbackSummary": null_readback(),
        "forecastArtifactsPresent": False,
        "qualityClaimAllowed": False,
        "blockedReasons": [],
        "requiredActions": [
            "Run an explicit setup forecast execution step for the accepted source-adapter output before reading forecast artifacts."
        ],
    }


def blocked_run(
    *,
    index: int,
    run_case: str,
    source_kind: str,
    status: str,
    next_action: str,
    reasons: list[str],
    actions: list[str],
    adapter_row: dict[str, Any] | None = None,
    private_setup_request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "orchestratorRunId": f"privatesetuporchestratorrun-{index:03d}",
        "runCase": run_case,
        "sourceKind": source_kind,
        "privateSetupRequestId": private_setup_request_id,
        "sourceAdapterOutputId": adapter_row["sourceAdapterOutputId"] if adapter_row else None,
        "sourceAdapterIntakeCaseId": adapter_row["caseId"] if adapter_row else None,
        "sourceIntakeReportId": adapter_row["intakeRoute"]["sourceIntakeReportId"] if adapter_row else None,
        "sourceIntakeStatus": adapter_row["intakeRoute"]["sourceIntakeStatus"] if adapter_row else None,
        "setupMethodDecisionId": adapter_row["methodGateSummary"]["setupMethodDecisionId"] if adapter_row else None,
        "setupBenchmarkGateId": adapter_row["methodGateSummary"]["setupBenchmarkGateId"] if adapter_row else None,
        "setupForecastRunId": None,
        "forecastId": None,
        "questionId": None,
        "forecastCardId": None,
        "forecastBundleId": None,
        "orchestratorStatus": status,
        "nextAction": next_action,
        "chain": chain(
            request=True,
            first_action=True,
            intake=adapter_row is not None and adapter_row["intakeRoute"]["sourceIntakeReportId"] is not None,
            method=adapter_row is not None and adapter_row["methodGateSummary"]["setupMethodDecisionId"] is not None,
            forecast=False,
            readback=False,
        ),
        "readbackSummary": null_readback(),
        "forecastArtifactsPresent": False,
        "qualityClaimAllowed": False,
        "blockedReasons": reasons,
        "requiredActions": actions,
    }


def build_orchestrator() -> dict[str, Any]:
    request_set = build_request_set()
    _outputs, _reports, _gates, _decisions, source_adapter_matrix = build_source_adapter_intake_records()
    rows = adapter_rows(source_adapter_matrix)
    runs = [
        local_file_confirmed_run(),
        source_adapter_accepted_run(rows["accepted"]),
        blocked_run(
            index=3,
            run_case="missing_approval",
            source_kind="private_api",
            status="missing_approval",
            next_action="confirm_approval",
            reasons=["missing_caller_approval", "credential_runtime_not_available"],
            actions=["Confirm caller approval and wait for a checked credential-safe runtime before setup can continue."],
            private_setup_request_id="privatesetuprequest-005",
        ),
        blocked_run(
            index=4,
            run_case="unconfirmed_mapping",
            source_kind="source_adapter_output",
            status="needs_confirmation",
            next_action="confirm_mapping",
            reasons=rows["needs_confirmation"]["rejectionReasons"],
            actions=rows["needs_confirmation"]["requiredActions"],
            adapter_row=rows["needs_confirmation"],
        ),
        blocked_run(
            index=5,
            run_case="insufficient_data",
            source_kind="source_adapter_output",
            status="needs_more_data",
            next_action="collect_more_data",
            reasons=rows["insufficient_data"]["rejectionReasons"],
            actions=rows["insufficient_data"]["requiredActions"],
            adapter_row=rows["insufficient_data"],
        ),
        blocked_run(
            index=6,
            run_case="rejected_source",
            source_kind="source_adapter_output",
            status="rejected_source",
            next_action="replace_source",
            reasons=rows["rejected"]["rejectionReasons"],
            actions=rows["rejected"]["requiredActions"],
            adapter_row=rows["rejected"],
        ),
        blocked_run(
            index=7,
            run_case="unsafe_source",
            source_kind="unsafe_source",
            status="blocked_unsafe",
            next_action="stop_unsafe_connector",
            reasons=rows["unsafe_blocked"]["rejectionReasons"],
            actions=rows["unsafe_blocked"]["requiredActions"],
            adapter_row=rows["unsafe_blocked"],
        ),
        blocked_run(
            index=8,
            run_case="response_too_large",
            source_kind="local_file",
            status="response_too_large",
            next_action="retry_with_smaller_readback",
            reasons=["readback_response_too_large"],
            actions=["Retry the forecast readback with a smaller record or higher caller-approved max-bytes limit."],
            private_setup_request_id="privatesetuprequest-001",
        ),
    ]
    orchestrator = {
        "privateSetupOrchestratorId": "privatesetuporchestrator-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "checked_local_summary_only",
        "bindings": {
            "privateSetupRequestSetId": request_set["privateSetupRequestSetId"],
            "privateSetupWorkflowId": request_set["boundPrivateSetupWorkflowId"],
            "sourceAdapterIntakeId": source_adapter_matrix["sourceAdapterIntakeId"],
            "sourceHandoffForecastId": "forecast-1102",
            "sourceHandoffQuestionId": "question-1102",
        },
        "orchestratorRuns": runs,
        "summary": {
            "runCount": len(runs),
            "completedForecastReadbacks": sum(1 for run in runs if run["orchestratorStatus"] == "completed_forecast_readback"),
            "readyForForecastExecution": sum(1 for run in runs if run["orchestratorStatus"] == "ready_for_forecast_execution"),
            "blockedRuns": sum(1 for run in runs if run["orchestratorStatus"] not in {"completed_forecast_readback", "ready_for_forecast_execution"}),
            "localFileSupported": True,
            "sourceAdapterOutputSupported": True,
            "plannedRuntimeRuns": 1,
        },
        "executionBoundary": {
            "orchestratorExecutesCommands": False,
            "readsPrivateData": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "createsSourceManifests": False,
            "createsFieldMappings": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "bypassesSourceIntake": False,
            "bypassesMethodGate": False,
            "usesExistingCheckedFixturesOnly": True,
        },
        "warnings": [
            "The orchestrator summary does not execute commands; it joins existing checked local fixtures.",
            "Forecast artifacts referenced by completed rows come from explicit forecast execution fixtures.",
            "Source-adapter output rows must still run explicit forecast execution before forecast readback exists.",
            "Private API, database, manual upload, and credentialed connectors remain planned-only unless represented by accepted sanitized adapter output.",
        ],
    }
    validate_orchestrator(orchestrator)
    return orchestrator


def validate_orchestrator(orchestrator: dict[str, Any]) -> None:
    errors = validate_record(orchestrator, SCHEMA)
    if errors:
        raise PrivateSetupOrchestratorError(f"private setup orchestrator schema validation failed: {errors[0]}")
    statuses = {run["runCase"]: run["orchestratorStatus"] for run in orchestrator["orchestratorRuns"]}
    expected = {
        "local_file_confirmed": "completed_forecast_readback",
        "source_adapter_output_accepted": "ready_for_forecast_execution",
        "missing_approval": "missing_approval",
        "unconfirmed_mapping": "needs_confirmation",
        "insufficient_data": "needs_more_data",
        "rejected_source": "rejected_source",
        "unsafe_source": "blocked_unsafe",
        "response_too_large": "response_too_large",
    }
    if statuses != expected:
        raise PrivateSetupOrchestratorError("orchestrator run status coverage drifted")
    local = next(run for run in orchestrator["orchestratorRuns"] if run["runCase"] == "local_file_confirmed")
    if local["forecastId"] != "forecast-1102" or local["readbackSummary"]["scoreStatus"] != "scored":
        raise PrivateSetupOrchestratorError("local file path should expose resolved forecast-1102 readback")
    adapter = next(run for run in orchestrator["orchestratorRuns"] if run["runCase"] == "source_adapter_output_accepted")
    if adapter["sourceIntakeStatus"] != "accepted" or adapter["forecastId"] is not None:
        raise PrivateSetupOrchestratorError("adapter accepted path should stop before forecast execution")
    boundary = orchestrator["executionBoundary"]
    for key, value in boundary.items():
        if key == "usesExistingCheckedFixturesOnly":
            if value is not True:
                raise PrivateSetupOrchestratorError("orchestrator should use existing checked fixtures")
        elif value is not False:
            raise PrivateSetupOrchestratorError(f"execution boundary {key} should be false")


def summary(orchestrator: dict[str, Any]) -> dict[str, Any]:
    return {
        "privateSetupOrchestratorId": orchestrator["privateSetupOrchestratorId"],
        "runCount": orchestrator["summary"]["runCount"],
        "runs": [
            {
                "runCase": run["runCase"],
                "sourceKind": run["sourceKind"],
                "orchestratorStatus": run["orchestratorStatus"],
                "forecastId": run["forecastId"],
                "nextAction": run["nextAction"],
            }
            for run in orchestrator["orchestratorRuns"]
        ],
    }


def write_orchestrator(orchestrator: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    ORCHESTRATOR_PATH.write_text(render_json(orchestrator), encoding="utf-8")
    print("generated private setup orchestrator")


def check_orchestrator(orchestrator: dict[str, Any]) -> None:
    expected = render_json(orchestrator)
    if not ORCHESTRATOR_PATH.exists():
        print(f"missing private setup orchestrator: {ORCHESTRATOR_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_orchestrator.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = ORCHESTRATOR_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private setup orchestrator drift: {ORCHESTRATOR_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_orchestrator.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private setup orchestrator")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one orchestrator run")
    parser.add_argument("--check", action="store_true", help="check generated private setup orchestrator drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup orchestrator")
    args = parser.parse_args()
    try:
        orchestrator = build_orchestrator()
    except PrivateSetupOrchestratorError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_orchestrator(orchestrator)
    elif args.check:
        check_orchestrator(orchestrator)
    elif args.case:
        run = next(item for item in orchestrator["orchestratorRuns"] if item["runCase"] == args.case)
        sys.stdout.write(render_json(run))
    else:
        sys.stdout.write(render_json(summary(orchestrator)))


if __name__ == "__main__":
    main()
