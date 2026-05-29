#!/usr/bin/env python3
"""Generate or check the domain-agnostic private setup workflow contract."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_source_handoff_setup_runbook import build_runbook as build_source_handoff_runbook
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-workflow"
WORKFLOW_PATH = GENERATED / "ope-private-setup-workflow.generated.json"
SCHEMA = SPEC / "private-setup-workflow.schema.json"
GENERATED_AT = "2026-06-06T20:00:00Z"


class PrivateSetupWorkflowError(Exception):
    pass


def supported_source_kinds() -> list[dict[str, Any]]:
    return [
        {
            "sourceKind": "local_file",
            "implementationStatus": "implemented_fixture",
            "currentBoundary": "Small caller-approved CSV and JSON files are supported only through the checked local source-builder fixture path.",
            "allowedInCurrentFixture": True,
            "requiresApproval": False,
        },
        {
            "sourceKind": "manual_mapping",
            "implementationStatus": "implemented_fixture",
            "currentBoundary": "Manual confirmation can turn proposed mappings into source-intake inputs in checked fixtures.",
            "allowedInCurrentFixture": True,
            "requiresApproval": True,
        },
        {
            "sourceKind": "manual_upload",
            "implementationStatus": "planned_contract_only",
            "currentBoundary": "Manual upload setup can be represented by the workflow, but no generic upload intake runtime is implemented.",
            "allowedInCurrentFixture": False,
            "requiresApproval": True,
        },
        {
            "sourceKind": "auto_evidence_connector",
            "implementationStatus": "implemented_fixture",
            "currentBoundary": "Policy-bound fixture replay is implemented; production live auto-evidence gathering is not.",
            "allowedInCurrentFixture": True,
            "requiresApproval": False,
        },
        {
            "sourceKind": "private_api",
            "implementationStatus": "planned_contract_only",
            "currentBoundary": "Private API setup can be represented by the workflow, but no generic API connector runtime is implemented.",
            "allowedInCurrentFixture": False,
            "requiresApproval": True,
        },
        {
            "sourceKind": "private_database",
            "implementationStatus": "planned_contract_only",
            "currentBoundary": "Private database setup can be represented by the workflow, but no generic database connector runtime is implemented.",
            "allowedInCurrentFixture": False,
            "requiresApproval": True,
        },
    ]


def phases() -> list[dict[str, Any]]:
    return [
        {
            "phaseId": "privatesetupphase-001",
            "order": 1,
            "phase": "source_discovery",
            "purpose": "Inspect or declare caller-approved sources before creating source manifests or mappings.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py source-builder",
            "inputContracts": ["spec/domain-setup.schema.json"],
            "outputContracts": ["spec/source-manifest-build.schema.json"],
            "allowedSourceKinds": ["local_file"],
            "possibleOutcomes": ["setup_ready", "rejected_source", "unsupported_source"],
            "guardrail": "Discovery drafts source records only; it must not create forecasts or public read surfaces.",
        },
        {
            "phaseId": "privatesetupphase-002",
            "order": 2,
            "phase": "mapping_confirmation",
            "purpose": "Confirm or reject agent-inferred source roles, field mappings, and alias mappings.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py source-handoff",
            "inputContracts": ["spec/source-manifest-build.schema.json", "spec/field-mapping.schema.json"],
            "outputContracts": ["spec/source-intake-handoff.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping"],
            "possibleOutcomes": ["setup_ready", "needs_confirmation", "rejected_source"],
            "guardrail": "Agent-inferred mappings remain proposals until deterministic validation or caller confirmation accepts them.",
        },
        {
            "phaseId": "privatesetupphase-003",
            "order": 3,
            "phase": "source_intake",
            "purpose": "Classify source manifests and mappings as usable, partial, confirmation-needed, or rejected.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py source-intake",
            "inputContracts": ["spec/source-manifest.schema.json", "spec/field-mapping.schema.json"],
            "outputContracts": ["spec/source-intake-report.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping", "auto_evidence_connector"],
            "possibleOutcomes": ["setup_ready", "needs_confirmation", "needs_more_data", "rejected_source"],
            "guardrail": "Source intake may classify data, but it must not create forecast artifacts.",
        },
        {
            "phaseId": "privatesetupphase-004",
            "order": 4,
            "phase": "method_gating",
            "purpose": "Select the best justified enabled method for the accepted setup and preserve baseline fallback.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py source-handoff-method",
            "inputContracts": ["spec/source-intake-report.schema.json", "spec/setup-benchmark-gate.schema.json"],
            "outputContracts": ["spec/setup-method-decision.schema.json", "spec/source-handoff-method-gate.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping", "auto_evidence_connector"],
            "possibleOutcomes": ["setup_ready", "needs_confirmation", "needs_more_data", "rejected_source"],
            "guardrail": "Method gates explain eligibility; they must not create forecast outputs.",
        },
        {
            "phaseId": "privatesetupphase-005",
            "order": 5,
            "phase": "forecast_execution",
            "purpose": "Create forecast artifacts only after source intake and method decisions allow execution.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py source-handoff-forecast",
            "inputContracts": ["spec/setup-forecast-run.schema.json", "spec/setup-method-decision.schema.json"],
            "outputContracts": ["spec/forecast-question.schema.json", "spec/evidence-packet.schema.json", "spec/forecast-artifact.schema.json", "spec/forecast-history.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping", "auto_evidence_connector"],
            "possibleOutcomes": ["setup_ready", "needs_confirmation", "needs_more_data", "rejected_source"],
            "guardrail": "Blocked execution outcomes must not bind forecast IDs, cards, bundles, or artifact paths.",
        },
        {
            "phaseId": "privatesetupphase-006",
            "order": 6,
            "phase": "recalculation",
            "purpose": "Append forecast updates when new pre-close evidence arrives without overwriting history.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py recalculation",
            "inputContracts": ["spec/recalculation-trigger.schema.json", "spec/recalculation-run.schema.json"],
            "outputContracts": ["spec/forecast-history.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping", "auto_evidence_connector"],
            "possibleOutcomes": ["setup_ready", "rejected_source", "runtime_not_implemented"],
            "guardrail": "Post-outcome evidence and resolution sources must not alter forecast-time probabilities.",
        },
        {
            "phaseId": "privatesetupphase-007",
            "order": 7,
            "phase": "resolution",
            "purpose": "Resolve outcomes from declared resolution sources after the forecast closes.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py resolve-source-handoff",
            "inputContracts": ["spec/resolution-record.schema.json"],
            "outputContracts": ["spec/resolution-record.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping"],
            "possibleOutcomes": ["setup_ready", "needs_more_data", "runtime_not_implemented"],
            "guardrail": "Resolution sources may resolve outcomes but must not enter forecast-time evidence.",
        },
        {
            "phaseId": "privatesetupphase-008",
            "order": 8,
            "phase": "scoring",
            "purpose": "Score resolved forecasts and update track-record and calibration summaries with sample-size boundaries.",
            "implementedNow": True,
            "currentSurface": "python3 scripts/ope.py read --record-type track-record --id trackrecord-1102",
            "inputContracts": ["spec/scoring-report.schema.json", "spec/track-record-report.schema.json", "spec/calibration-summary.schema.json"],
            "outputContracts": ["spec/scoring-report.schema.json", "spec/track-record-report.schema.json", "spec/calibration-summary.schema.json"],
            "allowedSourceKinds": ["local_file", "manual_mapping"],
            "possibleOutcomes": ["setup_ready", "needs_more_data"],
            "guardrail": "Quality and calibration claims require enough comparable resolved outcomes.",
        },
    ]


def outcome_classes() -> list[dict[str, Any]]:
    return [
        {
            "outcomeClass": "setup_ready",
            "terminal": False,
            "canForecast": True,
            "canScore": True,
            "nextAction": "run_method_gate",
            "agentInstruction": "Continue through method gating, explicit forecast execution, resolution, and read surfaces.",
        },
        {
            "outcomeClass": "needs_confirmation",
            "terminal": False,
            "canForecast": False,
            "canScore": False,
            "nextAction": "confirm_mapping",
            "agentInstruction": "Ask the caller to confirm proposed mappings before continuing.",
        },
        {
            "outcomeClass": "needs_more_data",
            "terminal": False,
            "canForecast": False,
            "canScore": False,
            "nextAction": "collect_more_data",
            "agentInstruction": "Collect enough pre-close source rows or outcome evidence before retrying the phase.",
        },
        {
            "outcomeClass": "rejected_source",
            "terminal": True,
            "canForecast": False,
            "canScore": False,
            "nextAction": "replace_source",
            "agentInstruction": "Replace rejected sources before source intake, method gates, forecast execution, or scoring.",
        },
        {
            "outcomeClass": "unsupported_source",
            "terminal": True,
            "canForecast": False,
            "canScore": False,
            "nextAction": "use_supported_source",
            "agentInstruction": "Use a supported fixture source or wait for a future connector runtime.",
        },
        {
            "outcomeClass": "runtime_not_implemented",
            "terminal": True,
            "canForecast": False,
            "canScore": False,
            "nextAction": "wait_for_runtime",
            "agentInstruction": "Do not simulate hosted upload, private API, or database behavior as implemented OPE support.",
        },
    ]


def guards() -> list[dict[str, Any]]:
    return [
        {
            "guardId": "privatesetupguard-001",
            "name": "domain_agnostic_contract",
            "rule": "The workflow must describe phases and outcomes without hard-coding weather-logistics as the product boundary.",
            "checkedBy": ["scripts/check_private_setup_workflow.py"],
        },
        {
            "guardId": "privatesetupguard-002",
            "name": "reference_wedge_boundary",
            "rule": "Weather-logistics remains a reference fixture implementation, not proof of broad domain coverage.",
            "checkedBy": ["scripts/check_private_setup_workflow.py", "scripts/generate_release_manifest.py"],
        },
        {
            "guardId": "privatesetupguard-003",
            "name": "private_runtime_boundary",
            "rule": "Manual uploads, private APIs, and databases are planned contract surfaces until a future runtime implements them.",
            "checkedBy": ["scripts/check_private_setup_workflow.py"],
        },
        {
            "guardId": "privatesetupguard-004",
            "name": "source_policy_boundary",
            "rule": "Every setup path must declare source policy, mappings, provenance, and unavailable evidence before forecasting.",
            "checkedBy": ["scripts/check_source_intake.py", "scripts/check_private_setup_workflow.py"],
        },
        {
            "guardId": "privatesetupguard-005",
            "name": "blocked_outputs_boundary",
            "rule": "Rejected, unsupported, unconfirmed, and runtime-not-implemented outcomes must not bind forecast or scoring outputs.",
            "checkedBy": ["scripts/check_source_handoff_setup_runbook.py", "scripts/check_private_setup_workflow.py"],
        },
        {
            "guardId": "privatesetupguard-006",
            "name": "claim_boundary",
            "rule": "Setup-ready or scored fixture outcomes do not create calibration, production, or state-of-the-art claims.",
            "checkedBy": ["scripts/check_source_handoff_resolution.py", "scripts/check_private_setup_workflow.py"],
        },
    ]


def build_workflow() -> dict[str, Any]:
    reference = build_source_handoff_runbook()
    workflow = {
        "privateSetupWorkflowId": "privatesetupworkflow-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "local_fixture_contract",
        "supportedSourceKinds": supported_source_kinds(),
        "phases": phases(),
        "outcomeClasses": outcome_classes(),
        "referenceImplementation": {
            "referenceDomain": reference["domain"],
            "referenceRunbookId": reference["sourceHandoffSetupRunbookId"],
            "referenceRunbookPath": "spec/fixtures/generated/source-handoff-runbook/weather-logistics-source-handoff-setup-runbook.generated.json",
            "referenceRunbookCommand": reference["entrypoints"]["runbookCommand"],
            "implementedFixturePath": "spec/fixtures/generated/source-handoff-runbook/",
            "forecastId": reference["exampleSequence"]["forecastId"],
            "questionId": reference["exampleSequence"]["questionId"],
            "trackRecordReportId": "trackrecord-1102",
            "implementedNow": True,
            "claimBoundary": "The reference implementation is local fixture-safe and has one resolved source-handoff outcome, below quality and calibration claim thresholds.",
        },
        "guards": guards(),
        "warnings": [
            "This workflow is a domain-agnostic contract, not a hosted service runtime.",
            "Manual uploads, private API setup, and private database setup are represented as planned contract surfaces, not implemented connectors.",
            "The weather-logistics source-handoff runbook is the current fixture implementation, not a universal setup proof.",
            "Quality and calibration claims remain tied to comparable resolved outcome counts.",
        ],
    }
    validate_workflow(workflow)
    return workflow


def validate_workflow(workflow: dict[str, Any]) -> None:
    errors = validate_record(workflow, SCHEMA)
    if errors:
        raise PrivateSetupWorkflowError(f"private setup workflow schema validation failed: {errors[0]}")

    phases_by_name = {item["phase"]: item for item in workflow["phases"]}
    expected_phases = [
        "source_discovery",
        "mapping_confirmation",
        "source_intake",
        "method_gating",
        "forecast_execution",
        "recalculation",
        "resolution",
        "scoring",
    ]
    if list(phases_by_name) != expected_phases:
        raise PrivateSetupWorkflowError("private setup workflow phase order drift")

    outcomes = {item["outcomeClass"]: item for item in workflow["outcomeClasses"]}
    expected_outcomes = {
        "setup_ready",
        "needs_confirmation",
        "needs_more_data",
        "rejected_source",
        "unsupported_source",
        "runtime_not_implemented",
    }
    if set(outcomes) != expected_outcomes:
        raise PrivateSetupWorkflowError("private setup workflow outcome class drift")
    if not outcomes["setup_ready"]["canForecast"] or not outcomes["setup_ready"]["canScore"]:
        raise PrivateSetupWorkflowError("setup_ready should allow forecast and scoring continuation")
    for name in expected_outcomes - {"setup_ready"}:
        if outcomes[name]["canForecast"] or outcomes[name]["canScore"]:
            raise PrivateSetupWorkflowError(f"{name} must not allow forecasting or scoring")

    source_support = {item["sourceKind"]: item for item in workflow["supportedSourceKinds"]}
    if source_support["private_api"]["implementationStatus"] != "planned_contract_only":
        raise PrivateSetupWorkflowError("private API support should remain planned contract only")
    if source_support["private_database"]["implementationStatus"] != "planned_contract_only":
        raise PrivateSetupWorkflowError("private database support should remain planned contract only")
    if source_support["manual_upload"]["implementationStatus"] != "planned_contract_only":
        raise PrivateSetupWorkflowError("manual upload support should remain planned contract only")
    if (
        source_support["private_api"]["allowedInCurrentFixture"]
        or source_support["private_database"]["allowedInCurrentFixture"]
        or source_support["manual_upload"]["allowedInCurrentFixture"]
    ):
        raise PrivateSetupWorkflowError("private API/database/manual upload should not be allowed in current fixture")

    reference = workflow["referenceImplementation"]
    if reference["referenceDomain"] != "weather-logistics":
        raise PrivateSetupWorkflowError("reference workflow should bind the weather-logistics fixture")
    if reference["forecastId"] != "forecast-1102" or reference["questionId"] != "question-1102":
        raise PrivateSetupWorkflowError("reference workflow should bind forecast-1102/question-1102")
    if "local fixture-safe" not in reference["claimBoundary"]:
        raise PrivateSetupWorkflowError("reference claim boundary must preserve fixture scope")


def write_workflow(workflow: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    WORKFLOW_PATH.write_text(render_json(workflow), encoding="utf-8")
    print("generated private setup workflow")


def check_workflow(workflow: dict[str, Any]) -> None:
    expected = render_json(workflow)
    if not WORKFLOW_PATH.exists():
        print(f"missing private setup workflow: {WORKFLOW_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_workflow.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = WORKFLOW_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"private setup workflow drift: {WORKFLOW_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_private_setup_workflow.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked private setup workflow")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup workflow drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup workflow")
    args = parser.parse_args()
    try:
        workflow = build_workflow()
    except PrivateSetupWorkflowError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_workflow(workflow)
    elif args.check:
        check_workflow(workflow)
    else:
        sys.stdout.write(render_json(workflow))


if __name__ == "__main__":
    main()
