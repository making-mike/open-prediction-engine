#!/usr/bin/env python3
"""Generate or check the agent-facing source-handoff setup runbook."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_source_handoff_method_gate import build_records as build_method_gate_records
from generate_source_intake_handoff import CASE_ORDER, build_handoffs
from ope_schema import SPEC, validate_record
from resolve_source_handoff_outcome import build_outputs as build_resolution_outputs
from run_source_handoff_forecast import build_outputs as build_forecast_outputs
from run_source_handoff_forecast import output_prefix
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-handoff-runbook"
RUNBOOK_PATH = GENERATED / "weather-logistics-source-handoff-setup-runbook.generated.json"
SCHEMA = SPEC / "source-handoff-setup-runbook.schema.json"
GENERATED_AT = "2026-06-06T19:35:00Z"


class SourceHandoffSetupRunbookError(Exception):
    pass


def workflow_steps() -> list[dict[str, Any]]:
    return [
        {
            "stepId": "sourcehandoffsetupstep-001",
            "order": 1,
            "name": "inspect_sources",
            "purpose": "Inspect caller-approved local files and draft manifest and mapping records.",
            "cliCommand": "python3 scripts/ope.py source-builder",
            "expectedSchema": "spec/source-manifest-build.schema.json",
            "sideEffectLevel": "draft_only",
            "nextActionLabel": "inspect_sources",
            "stopCondition": "Stop if the builder rejects secrets, unsupported formats, oversized files, or leakage indicators.",
        },
        {
            "stepId": "sourcehandoffsetupstep-002",
            "order": 2,
            "name": "handoff_to_source_intake",
            "purpose": "Classify builder drafts into confirmation, more-data, replacement, or method-gating next actions.",
            "cliCommand": "python3 scripts/ope.py source-handoff",
            "expectedSchema": "spec/source-intake-handoff.schema.json",
            "sideEffectLevel": "non_generating_gate",
            "nextActionLabel": "proceed_to_method_gating",
            "stopCondition": "Do not continue to method gates unless the handoff says proceed_to_method_gating.",
        },
        {
            "stepId": "sourcehandoffsetupstep-003",
            "order": 3,
            "name": "run_method_gate",
            "purpose": "Bind accepted source intake to setup benchmark and method decisions without creating forecasts.",
            "cliCommand": "python3 scripts/ope.py source-handoff-method",
            "expectedSchema": "spec/source-handoff-method-gate.schema.json",
            "sideEffectLevel": "non_generating_gate",
            "nextActionLabel": "run_explicit_forecast",
            "stopCondition": "Do not create artifacts unless the method gate awaits explicit setup forecast execution.",
        },
        {
            "stepId": "sourcehandoffsetupstep-004",
            "order": 4,
            "name": "execute_forecast",
            "purpose": "Run explicit setup forecast execution for the confirmed handoff only.",
            "cliCommand": "python3 scripts/ope.py source-handoff-forecast --case confirmed_builder_draft",
            "expectedSchema": "spec/setup-forecast-run.schema.json",
            "sideEffectLevel": "fixture_generation",
            "nextActionLabel": "resolve_source_handoff",
            "stopCondition": "Blocked setup forecast runs must not bind forecast IDs or artifact paths.",
        },
        {
            "stepId": "sourcehandoffsetupstep-005",
            "order": 5,
            "name": "resolve_forecast",
            "purpose": "Resolve and score the generated handoff forecast from declared outcome sources.",
            "cliCommand": "python3 scripts/ope.py resolve-source-handoff",
            "expectedSchema": "spec/resolution-record.schema.json",
            "sideEffectLevel": "fixture_resolution",
            "nextActionLabel": "read_resolved_forecast_card",
            "stopCondition": "Do not score blocked handoff cases or use resolution sources as forecast-time evidence.",
        },
        {
            "stepId": "sourcehandoffsetupstep-006",
            "order": 6,
            "name": "read_forecast_card",
            "purpose": "Read compact probability, baseline, resolution, score, and claim-boundary fields.",
            "cliCommand": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "expectedSchema": "spec/forecast-card.schema.json",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "read_lifecycle_bundle",
            "stopCondition": "Stop if the card does not preserve handoff and method-gate bindings.",
        },
        {
            "stepId": "sourcehandoffsetupstep-007",
            "order": 7,
            "name": "read_lifecycle_bundle",
            "purpose": "Read the bound forecast lifecycle for audit context and provenance review.",
            "cliCommand": "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
            "expectedSchema": "synthetic forecast-bundle read view",
            "sideEffectLevel": "read_only",
            "nextActionLabel": "read_track_record",
            "stopCondition": "Use the bundle for audit context, not as a new source of forecast semantics.",
        },
        {
            "stepId": "sourcehandoffsetupstep-008",
            "order": 8,
            "name": "read_track_record",
            "purpose": "Inspect the one-outcome track record and sample-size claim boundary.",
            "cliCommand": "python3 scripts/ope.py read --record-type track-record --id trackrecord-1102",
            "expectedSchema": "spec/track-record-report.schema.json",
            "sideEffectLevel": "scoring_read",
            "nextActionLabel": "stop_terminal",
            "stopCondition": "Do not generalize one resolved handoff outcome into a calibration or quality claim.",
        },
    ]


def next_action_for_case(
    case: str,
    handoff: dict[str, Any],
    method_gate: dict[str, Any],
    forecast_run: dict[str, Any],
    scored: bool,
) -> str:
    if scored:
        return "read_resolved_forecast_card"
    if forecast_run["controls"]["forecastArtifactsCreated"]:
        return "resolve_source_handoff"
    if method_gate["nextAction"] == "await_explicit_setup_forecast_execution":
        return "run_explicit_forecast"
    if handoff["nextAction"] == "ask_mapping_confirmation":
        return "ask_mapping_confirmation"
    if handoff["nextAction"] == "collect_more_data":
        return "collect_more_data"
    if handoff["nextAction"] == "replace_rejected_sources":
        return "replace_rejected_sources"
    raise SourceHandoffSetupRunbookError(f"unsupported next action for {case}")


def instruction_for_case(case: str, next_action: str) -> str:
    if next_action == "read_resolved_forecast_card":
        return "Read forecast-1102 card, bundle, or track record; keep quality claims sample-size-blocked."
    if next_action == "ask_mapping_confirmation":
        return "Ask the caller to confirm proposed mappings before method gates or forecast execution."
    if next_action == "collect_more_data":
        return "Collect enough pre-close source rows before retrying source intake and method gates."
    if next_action == "replace_rejected_sources":
        return "Replace rejected sources before source intake; do not pass rejected files to forecast execution."
    if next_action == "run_explicit_forecast":
        return "Run explicit forecast execution before reading any forecast card or bundle."
    return "Stop and inspect the source-handoff setup state."


def case_playbooks() -> list[dict[str, Any]]:
    handoffs = build_handoffs()
    method_gates = build_method_gate_records()
    forecast_outputs = build_forecast_outputs()
    resolution_outputs = build_resolution_outputs()
    outcome_summary = resolution_outputs[
        "weather-logistics-source-handoff-resolution-outcome-summary.generated.json"
    ]
    scoring = resolution_outputs["weather-logistics-source-handoff-resolution-scoring.generated.json"]

    playbooks = []
    for case in CASE_ORDER:
        handoff = handoffs[case][0]
        method_gate = method_gates[case][0]
        forecast_run = forecast_outputs[f"{output_prefix(case)}-setup-forecast-run.generated.json"]
        generated = forecast_run["controls"]["forecastArtifactsCreated"]
        scored = bool(generated and scoring["scoreStatus"] == "scored")
        next_action = next_action_for_case(case, handoff, method_gate, forecast_run, scored)
        playbooks.append(
            {
                "case": case,
                "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
                "sourceHandoffMethodGateId": method_gate["sourceHandoffMethodGateId"],
                "setupForecastRunId": forecast_run["setupForecastRunId"],
                "forecastId": forecast_run["recordBinding"]["forecastId"],
                "questionId": forecast_run["recordBinding"]["questionId"],
                "sourceIntakeStatus": handoff["sourceIntakeStatus"],
                "sourceHandoffNextAction": handoff["nextAction"],
                "methodGateNextAction": method_gate["nextAction"],
                "forecastRunStatus": forecast_run["runStatus"],
                "selectedMethodClass": forecast_run["selectedMethodClass"],
                "generatesForecastOutputs": generated,
                "scored": scored,
                "qualityClaimStatus": outcome_summary["qualityClaimStatus"] if scored else "not_applicable",
                "nextActionLabel": next_action,
                "mustNotForecast": not generated,
                "mustNotScore": not scored,
                "agentInstruction": instruction_for_case(case, next_action),
            }
        )
    return playbooks


def read_surface_choices() -> list[dict[str, Any]]:
    return [
        {
            "operation": "source_handoff_summaries",
            "whenToUse": "Use before execution to inspect source-builder handoff, method-gate, and forecast-run state.",
            "cliCommand": "python3 scripts/ope.py source-handoff",
            "requires": [],
            "agentRule": "Treat source-handoff and method-gate summaries as guidance, not generated forecasts.",
        },
        {
            "operation": "resolution_outputs",
            "whenToUse": "Use after forecast execution to check source-handoff resolution fixture drift.",
            "cliCommand": "python3 scripts/ope.py resolve-source-handoff",
            "requires": ["forecast-1102", "question-1102"],
            "agentRule": "Only generated forecast-1102 is resolved; blocked handoff cases stay non-scored.",
        },
        {
            "operation": "forecast_card",
            "whenToUse": "Use for compact probability, baseline, resolved outcome, score, and claim boundary.",
            "cliCommand": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "requires": ["forecastId", "questionId"],
            "agentRule": "Do not hide sample-size warnings or source-handoff setup bindings from downstream agents.",
        },
        {
            "operation": "lifecycle_bundle",
            "whenToUse": "Use when the caller needs the bound forecast lifecycle and provenance context.",
            "cliCommand": "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
            "requires": ["forecastId", "questionId"],
            "agentRule": "Use for audit context without redefining forecast, evidence, resolution, or scoring semantics.",
        },
        {
            "operation": "track_record",
            "whenToUse": "Use after resolution to inspect Brier score, baseline comparison, and one-outcome boundary.",
            "cliCommand": "python3 scripts/ope.py read --record-type track-record --id trackrecord-1102",
            "requires": ["trackRecordReportId"],
            "agentRule": "One resolved source-handoff outcome is not a calibration or quality claim.",
        },
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "sourcehandoffsetupguard-001",
            "name": "mapping_confirmation_gate",
            "rule": "Unconfirmed builder mappings must ask for confirmation before method gates or forecast execution.",
            "checkedBy": ["scripts/check_source_intake_handoff.py", "scripts/check_source_handoff_setup_runbook.py"],
        },
        {
            "guardId": "sourcehandoffsetupguard-002",
            "name": "blocked_cases_no_forecast",
            "rule": "Blocked source-handoff cases must not bind forecast IDs, question IDs, cards, bundles, or artifacts.",
            "checkedBy": ["scripts/check_source_handoff_forecast.py", "scripts/check_source_handoff_setup_runbook.py"],
        },
        {
            "guardId": "sourcehandoffsetupguard-003",
            "name": "blocked_cases_no_score",
            "rule": "Blocked source-handoff cases must not create resolution, scoring, calibration, or track-record outputs.",
            "checkedBy": ["scripts/check_source_handoff_resolution.py", "scripts/check_source_handoff_setup_runbook.py"],
        },
        {
            "guardId": "sourcehandoffsetupguard-004",
            "name": "resolution_source_boundary",
            "rule": "Declared outcome sources may resolve outcomes but must not enter forecast-time provenance.",
            "checkedBy": ["scripts/resolve_source_handoff_outcome.py", "scripts/check_source_handoff_resolution.py"],
        },
        {
            "guardId": "sourcehandoffsetupguard-005",
            "name": "sample_size_boundary",
            "rule": "One resolved source-handoff outcome must keep quality and calibration claims blocked.",
            "checkedBy": ["scripts/check_source_handoff_resolution.py", "scripts/check_source_handoff_setup_runbook.py"],
        },
        {
            "guardId": "sourcehandoffsetupguard-006",
            "name": "local_fixture_boundary",
            "rule": "The source-handoff setup runbook describes local fixture behavior, not hosted private API parsing.",
            "checkedBy": ["scripts/check_source_handoff_setup_runbook.py", "scripts/generate_release_manifest.py"],
        },
    ]


def example_sequence() -> dict[str, Any]:
    return {
        "case": "confirmed_builder_draft",
        "forecastId": "forecast-1102",
        "questionId": "question-1102",
        "commands": [
            {
                "order": 1,
                "command": "python3 scripts/ope.py source-builder --case local_draft",
                "expectedSignal": "draft manifest and mapping from caller-approved local files",
            },
            {
                "order": 2,
                "command": "python3 scripts/ope.py source-handoff --case confirmed_builder_draft",
                "expectedSignal": "nextAction proceed_to_method_gating",
            },
            {
                "order": 3,
                "command": "python3 scripts/ope.py source-handoff-method --case confirmed_builder_draft",
                "expectedSignal": "methodGateStatus method_selected without forecast artifacts",
            },
            {
                "order": 4,
                "command": "python3 scripts/ope.py source-handoff-forecast --case confirmed_builder_draft",
                "expectedSignal": "runStatus generated with forecastId forecast-1102",
            },
            {
                "order": 5,
                "command": "python3 scripts/ope.py resolve-source-handoff",
                "expectedSignal": "checked six source-handoff resolution outputs",
            },
            {
                "order": 6,
                "command": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
                "expectedSignal": "resolved scored forecast card with source-handoff setup binding",
            },
            {
                "order": 7,
                "command": "python3 scripts/ope.py read --record-type track-record --id trackrecord-1102",
                "expectedSignal": "one resolved outcome with sample-size claim boundary",
            },
        ],
    }


def build_runbook() -> dict[str, Any]:
    runbook = {
        "sourceHandoffSetupRunbookId": "sourcehandoffsetuprunbook-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "runtimeStatus": "local_fixture_safe",
        "entrypoints": {
            "sourceBuilderCommand": "python3 scripts/ope.py source-builder",
            "sourceHandoffCommand": "python3 scripts/ope.py source-handoff",
            "methodGateCommand": "python3 scripts/ope.py source-handoff-method",
            "forecastCommand": "python3 scripts/ope.py source-handoff-forecast",
            "resolutionCommand": "python3 scripts/ope.py resolve-source-handoff",
            "runbookCommand": "python3 scripts/ope.py source-handoff-runbook",
            "runbookSchema": "spec/source-handoff-setup-runbook.schema.json",
        },
        "workflow": workflow_steps(),
        "casePlaybooks": case_playbooks(),
        "readSurfaceChoices": read_surface_choices(),
        "guards": guards(),
        "exampleSequence": example_sequence(),
        "warnings": [
            "Runbook describes local fixture-safe CLI behavior only.",
            "Source-builder drafts remain proposals until source intake and setup gates accept them.",
            "Unconfirmed mappings, insufficient data, and builder-rejected sources must not generate forecasts.",
            "Only forecast-1102 resolves and scores in this fixture path.",
            "One resolved source-handoff outcome is not a quality, calibration, production, or state-of-the-art claim.",
        ],
    }
    validate_runbook(runbook)
    return runbook


def validate_runbook(runbook: dict[str, Any]) -> None:
    errors = validate_record(runbook, SCHEMA)
    if errors:
        raise SourceHandoffSetupRunbookError(f"source-handoff setup runbook schema validation failed: {errors[0]}")

    playbooks = {item["case"]: item for item in runbook["casePlaybooks"]}
    if list(playbooks) != CASE_ORDER:
        raise SourceHandoffSetupRunbookError("source-handoff setup runbook case order drift")
    confirmed = playbooks["confirmed_builder_draft"]
    if confirmed["forecastId"] != "forecast-1102" or confirmed["questionId"] != "question-1102":
        raise SourceHandoffSetupRunbookError("confirmed source-handoff runbook must bind forecast-1102/question-1102")
    if confirmed["scored"] is not True or confirmed["nextActionLabel"] != "read_resolved_forecast_card":
        raise SourceHandoffSetupRunbookError("confirmed source-handoff runbook should end at resolved forecast card")
    if confirmed["qualityClaimStatus"] != "not_enough_resolved_source_handoff_outcomes":
        raise SourceHandoffSetupRunbookError("source-handoff runbook must preserve sample-size claim boundary")

    for case, playbook in playbooks.items():
        if case == "confirmed_builder_draft":
            if playbook["mustNotForecast"] or playbook["mustNotScore"]:
                raise SourceHandoffSetupRunbookError("confirmed source-handoff case should forecast and score")
            continue
        if playbook["forecastId"] is not None or playbook["questionId"] is not None:
            raise SourceHandoffSetupRunbookError(f"{case} must not bind forecast or question outputs")
        if playbook["generatesForecastOutputs"] or playbook["scored"]:
            raise SourceHandoffSetupRunbookError(f"{case} must not generate or score")
        if not playbook["mustNotForecast"] or not playbook["mustNotScore"]:
            raise SourceHandoffSetupRunbookError(f"{case} must forbid forecast and score use")
        if case == "unconfirmed_builder_draft" and playbook["nextActionLabel"] != "ask_mapping_confirmation":
            raise SourceHandoffSetupRunbookError("unconfirmed case should ask mapping confirmation")
        if case == "insufficient_confirmed_builder_draft" and playbook["nextActionLabel"] != "collect_more_data":
            raise SourceHandoffSetupRunbookError("insufficient case should collect more data")
        if case in {"contains_secret", "unsupported_format", "oversized", "leakage"}:
            if playbook["nextActionLabel"] != "replace_rejected_sources":
                raise SourceHandoffSetupRunbookError(f"{case} should replace rejected sources")

    orders = [item["order"] for item in runbook["workflow"]]
    if orders != sorted(orders):
        raise SourceHandoffSetupRunbookError("source-handoff setup workflow order drift")
    operations = {item["operation"] for item in runbook["readSurfaceChoices"]}
    expected_operations = {
        "source_handoff_summaries",
        "forecast_card",
        "lifecycle_bundle",
        "track_record",
        "resolution_outputs",
    }
    if operations != expected_operations:
        raise SourceHandoffSetupRunbookError("source-handoff setup read choices drift")


def write_runbook(runbook: dict[str, Any]) -> None:
    write_generated(RUNBOOK_PATH, runbook, label="source-handoff setup runbook", regen="python3 scripts/generate_source_handoff_setup_runbook.py --write")


def check_runbook(runbook: dict[str, Any]) -> None:
    check_generated(RUNBOOK_PATH, runbook, label="source-handoff setup runbook", regen="python3 scripts/generate_source_handoff_setup_runbook.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated source-handoff setup runbook drift")
    parser.add_argument("--write", action="store_true", help="write generated source-handoff setup runbook")
    args = parser.parse_args()
    try:
        runbook = build_runbook()
    except SourceHandoffSetupRunbookError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_runbook(runbook)
    elif args.check:
        check_runbook(runbook)
    else:
        sys.stdout.write(render_json(runbook))


if __name__ == "__main__":
    main()
