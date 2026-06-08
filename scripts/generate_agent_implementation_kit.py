#!/usr/bin/env python3
"""Generate a checked agent prediction implementation kit readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-implementation-kit"
OUTPUT_PATH = GENERATED / "ope-agent-implementation-kit.generated.json"
SCHEMA = SPEC / "agent-implementation-kit.schema.json"
GENERATED_AT = "2026-06-04T19:15:00Z"


class AgentImplementationKitError(Exception):
    pass


MANUAL_STEP_KEYS = [
    "detect_decision_under_uncertainty",
    "describe_app_goal",
    "bind_approved_sources",
    "discover_candidate_contracts",
    "validate_candidate_contracts",
    "create_prediction",
    "start_prediction",
    "run_tick_or_worker",
    "read_forecast_card",
    "resolve_outcome",
    "append_evidence_and_score",
    "inspect_calibration",
]

VALIDATION_CHECKS = [
    "schema_validity",
    "future_boundary",
    "resolvability",
    "source_policy_binding",
    "leakage_risk",
    "outcome_availability",
    "mapping_confidence",
    "baseline_feasibility",
    "method_eligibility",
    "scoring_readiness",
    "calibration_readiness_boundary",
]


def quickstart_step(order: int, key: str, command: str, expected: str, blocked: str) -> dict[str, Any]:
    return {
        "order": order,
        "stepKey": key,
        "command": command,
        "expected": expected,
        "blockedAlternative": blocked,
    }


def quickstart_front_door() -> dict[str, Any]:
    steps = [
        quickstart_step(
            1,
            "start_with_setup_engine",
            'python3 scripts/ope.py setup-engine --goal "add predictions to my app"',
            "Return the canonical setup plan; use prediction-goal-catalog when the host goal needs generic examples.",
            "If this command fails, run setup-engine and prediction-goal-catalog checks before attempting forecast setup.",
        ),
        quickstart_step(
            2,
            "render_host_wrapper_setup_plan",
            "python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json",
            "Render setupEnginePlan before forecast-card reads; blocked host inputs stop before forecast setup.",
            "If setupEnginePlan reports missing roles or vague outcomes, fix host inputs before reading cards.",
        ),
        quickstart_step(
            3,
            "run_guided_forecast",
            "python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output",
            "Return forecast and question IDs plus forecast-card and lifecycle-bundle readback commands.",
            "If the guided case is blocked, do not invent forecast IDs; fix the source or question blocker first.",
        ),
        quickstart_step(
            4,
            "read_forecast_card",
            "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "Read the compact claim-safe forecast card for host decision support.",
            "If the card cannot be read, inspect the guided forecast output and record binding before retrying.",
        ),
        quickstart_step(
            5,
            "inspect_lifecycle_bundle",
            "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
            "Read the lifecycle bundle when the host feature needs provenance, method, or scoring context.",
            "If the bundle is too large for context, keep the forecast card as the compact readback.",
        ),
    ]
    return {
        "frontDoorId": "agentimplementationfrontdoor-001",
        "frontDoorStatus": "implementation_follow_up_entrypoint",
        "entryCommand": 'python3 scripts/ope.py setup-engine --goal "add predictions to my app"',
        "targetTimeToFirstCommandMinutes": 10,
        "steps": steps,
        "copyableWrapper": {
            "wrapperStatus": "outline_only_uses_existing_surfaces",
            "callSequence": [
                "setup_engine",
                "render_setup_engine_host_wrapper",
                "prediction_feature_setup_response",
                "forecast_card_readback",
                "lifecycle_bundle_readback",
            ],
            "storesCredentialValues": False,
            "acceptsRawPrivateRows": False,
            "acceptsRawSql": False,
            "opensNetworkListener": False,
        },
        "createsNewForecastPath": False,
        "hostedRuntimeRequired": False,
        "qualityClaimUpgraded": False,
    }


def manual_step(index: int, key: str, command: str, action: str, creates_artifacts: bool = False) -> dict[str, Any]:
    return {
        "stepId": f"predictionmanualstep-{index:03d}",
        "order": index,
        "stepKey": key,
        "action": action,
        "exampleCommand": command,
        "requiresApprovedSources": True,
        "createsForecastArtifacts": creates_artifacts,
        "claimBoundaryReminder": "Keep setup, forecast, scoring, and calibration claims tied to checked OPE readbacks.",
    }


def prediction_manual() -> dict[str, Any]:
    actions = {
        "detect_decision_under_uncertainty": "Confirm the host feature depends on a future uncertain outcome, not a static lookup.",
        "describe_app_goal": "Record the host app goal, user decision, safety impact, and forecast value.",
        "bind_approved_sources": "Bind caller-approved source references, source roles, and source policies before discovery.",
        "discover_candidate_contracts": "Ask OPE for candidate forecast contracts from the app goal and approved source context.",
        "validate_candidate_contracts": "Run mechanical validation before any forecast artifact can be created.",
        "create_prediction": "Create the prediction configuration through the internal API and lifecycle receipts.",
        "start_prediction": "Start the accepted prediction so normal lifecycle records can be produced.",
        "run_tick_or_worker": "Run one foreground tick or bounded worker loop using the shared internal API semantics.",
        "read_forecast_card": "Read the compact forecast card for host decision support.",
        "resolve_outcome": "Resolve due outcomes through checked resolution rules and source policies.",
        "append_evidence_and_score": "Append comparable evidence, create scores, and preserve exclusions.",
        "inspect_calibration": "Inspect calibration and track-record gates without making premature quality claims.",
    }
    commands = {
        "detect_decision_under_uncertainty": "python3 scripts/ope.py agent-implementation-kit --view manual",
        "describe_app_goal": "python3 scripts/ope.py agent-implementation-kit --view intake",
        "bind_approved_sources": "python3 scripts/ope.py source-bindings",
        "discover_candidate_contracts": "python3 scripts/ope.py agent-implementation-kit --view candidates",
        "validate_candidate_contracts": "python3 scripts/ope.py agent-implementation-kit --view validation",
        "create_prediction": "python3 scripts/ope.py internal-api --operation create_prediction",
        "start_prediction": "python3 scripts/ope.py internal-api --operation start_prediction",
        "run_tick_or_worker": "python3 scripts/ope.py background-worker --view tick",
        "read_forecast_card": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
        "resolve_outcome": "python3 scripts/ope.py resolve-source-handoff",
        "append_evidence_and_score": "python3 scripts/ope.py prediction-campaign append-ready",
        "inspect_calibration": "python3 scripts/ope.py transit-track-record-gate",
    }
    steps = [
        manual_step(index, key, commands[key], actions[key], creates_artifacts=key == "start_prediction")
        for index, key in enumerate(MANUAL_STEP_KEYS, start=1)
    ]
    return {
        "manualId": "agentpredictionmanual-001",
        "manualStatus": "compact_local_manual_checked",
        "summary": "Shortest checked path from a host app prediction need to OPE forecast, resolution, score, and calibration readbacks.",
        "steps": steps,
    }


def intake_field(name: str, field_type: str, purpose: str, max_items: int = 1) -> dict[str, Any]:
    return {
        "fieldName": name,
        "fieldType": field_type,
        "purpose": purpose,
        "maxItems": max_items,
        "credentialValueAllowed": False,
        "rawPrivateRowsAllowed": False,
    }


def question_discovery_intake_contract() -> dict[str, Any]:
    return {
        "contractId": "questiondiscoveryintake-001",
        "contractStatus": "checked_local_intake_contract",
        "requiredFields": [
            intake_field("appGoal", "string", "What host feature or workflow should the prediction support?"),
            intake_field("decisionToSupport", "string", "What user or system decision changes if the forecast is informative?"),
            intake_field("approvedSourceRefs", "array", "Caller-approved source references, not credential values.", max_items=8),
            intake_field("sourceRoles", "array", "Forecast-time, resolution-only, historical, or context roles.", max_items=8),
            intake_field("forecastTimeEvidencePolicy", "string", "Evidence allowed before forecast close time."),
            intake_field("resolutionEvidencePolicy", "string", "Evidence allowed only for outcome resolution."),
            intake_field("candidateOutcomeWindows", "array", "Candidate close and resolve windows.", max_items=6),
            intake_field("resolutionSourceHints", "array", "Potential outcome source references and availability notes.", max_items=6),
            intake_field("safetyImpact", "string", "Safety or privacy sensitivity of the host decision."),
        ],
        "optionalFields": ["existingSetupId", "domainHint", "methodPreferenceHint"],
        "credentialValuesAccepted": False,
        "rawPrivateRowsAccepted": False,
        "normalizesToExistingSetupContracts": True,
        "createsForecastArtifacts": False,
    }


def candidate_contract(
    index: int,
    status: str,
    canonical_question: str,
    blocker_code: str,
    source_readiness: str,
    baseline_feasible: bool,
    routes: bool,
    next_commands: list[str],
) -> dict[str, Any]:
    return {
        "candidateId": f"candidateforecast-{index:03d}",
        "candidateStatus": status,
        "canonicalQuestion": canonical_question,
        "outputType": "binary",
        "closeTime": "2026-06-12T06:00:00Z",
        "resolveTime": "2026-06-12T10:00:00Z",
        "resolutionRule": "Resolve from approved resolution source rows after the outcome window closes.",
        "allowedEvidence": [
            "approved forecast-time source bindings",
            "historical comparable rows before close time",
            "declared setup context",
        ],
        "forbiddenEvidence": [
            "post-close outcome rows before forecast creation",
            "raw private rows",
            "credential values",
            "unapproved live fetches",
        ],
        "baselineFeasible": baseline_feasible,
        "sourceReadiness": source_readiness,
        "methodBoundary": "Baseline-first unless setup benchmark and method gate approve another method.",
        "claimBoundary": "No quality or calibration claim until comparable resolved evidence reaches thresholds.",
        "blockerCode": blocker_code,
        "routesToExistingSurfaces": routes,
        "nextSurfaceCommands": next_commands,
    }


def candidate_contract_readbacks() -> list[dict[str, Any]]:
    return [
        candidate_contract(
            1,
            "forecastable",
            "Will morning peak tram delay exceed 10 minutes in the approved service area on 2026-06-12?",
            "none",
            "ready",
            True,
            True,
            ["source-intake", "setup-benchmark", "setup-method", "setup-forecast", "read forecast-card"],
        ),
        candidate_contract(
            2,
            "needs_clarification",
            "Will the delivery arrive late next week?",
            "ambiguous_resolution_window",
            "partial",
            True,
            False,
            ["agent-implementation-kit --view intake"],
        ),
        candidate_contract(
            3,
            "blocked",
            "Will a private customer churn based on unapproved CRM rows?",
            "source_policy_or_safety_blocker",
            "blocked",
            False,
            False,
            ["source-bindings", "runtime-security --view boundary"],
        ),
        candidate_contract(
            4,
            "rejected",
            "Did yesterday's shipment miss its SLA?",
            "post_outcome_or_unresolvable",
            "rejected",
            False,
            False,
            ["forecast-question-discovery.md"],
        ),
    ]


def validation_check(name: str, status: str, blocker: str = "none") -> dict[str, Any]:
    return {
        "checkName": name,
        "checkStatus": status,
        "blockerCode": blocker,
        "message": f"{name} is {status} for this candidate.",
    }


def validation_report(candidate: dict[str, Any]) -> dict[str, Any]:
    status = candidate["candidateStatus"]
    checks: list[dict[str, Any]] = []
    for name in VALIDATION_CHECKS:
        check_status = "pass"
        blocker = "none"
        if status == "needs_clarification" and name in {"resolvability", "outcome_availability"}:
            check_status = "needs_clarification"
            blocker = "ambiguous_resolution_window"
        elif status == "blocked" and name in {"source_policy_binding", "leakage_risk", "mapping_confidence"}:
            check_status = "blocked"
            blocker = "source_policy_or_safety_blocker"
        elif status == "rejected" and name in {"future_boundary", "resolvability", "scoring_readiness"}:
            check_status = "rejected"
            blocker = "post_outcome_or_unresolvable"
        checks.append(validation_check(name, check_status, blocker))
    return {
        "validationReportId": f"candidatevalidation-{candidate['candidateId'].split('-')[-1]}",
        "candidateId": candidate["candidateId"],
        "candidateStatus": status,
        "checks": checks,
        "createsForecastArtifacts": False,
        "rawSourceDataExposed": False,
        "nextAction": "route_to_existing_surfaces" if status == "forecastable" else "stop_before_forecast_artifact",
    }


def mechanical_validation_reports(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [validation_report(candidate) for candidate in candidates]


def source_path(path_key: str, source_kind: str, immediate_action: str, command: str) -> dict[str, Any]:
    return {
        "pathKey": path_key,
        "sourceKind": source_kind,
        "immediateAction": immediate_action,
        "entryCommand": command,
        "credentialValuesStored": False,
        "createsForecastArtifacts": False,
    }


def first_run_source_paths() -> list[dict[str, Any]]:
    return [
        source_path("approved_local_files_now", "local_files", "run_source_builder", "python3 scripts/ope.py source-builder"),
        source_path(
            "sanitized_adapter_output_now",
            "source_adapter_output",
            "run_source_adapter_intake",
            "python3 scripts/ope.py source-adapter-intake",
        ),
        source_path(
            "database_or_private_api_waits",
            "private_api_or_database",
            "wait_for_checked_runtime",
            "python3 scripts/ope.py private-source-kind-selection --source-kind private_database",
        ),
    ]


def adapter_readback(name: str, status: str, command: str, notes: str) -> dict[str, Any]:
    return {
        "adapterName": name,
        "implementedStatus": status,
        "exampleCommand": command,
        "sharesInternalApiSemantics": True,
        "rawSqlExposed": False,
        "hiddenServiceRequired": False,
        "notes": notes,
    }


def adapter_readbacks() -> list[dict[str, Any]]:
    return [
        adapter_readback(
            "in_process",
            "local_embedding_guidance",
            "from scripts.generate_agent_implementation_kit import build_agent_implementation_kit",
            "Host apps can embed OPE by calling checked internal operation functions.",
        ),
        adapter_readback("cli", "implemented_local", "python3 scripts/ope.py agent-implementation-kit", "CLI emits compact JSON readbacks."),
        adapter_readback(
            "agent_call",
            "local_envelope_guidance",
            "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
            "Agent-call wrappers should reuse existing read operations and compact envelopes.",
        ),
        adapter_readback("local_mcp_stdio", "local_scaffold_guidance", "python3 scripts/ope.py mcp-stdio", "Local MCP remains a wrapper over the dispatcher."),
        adapter_readback("future_http_queue", "future_transport_only", "spec/agent-adapter-protocol-map.md", "HTTP and queue transports stay future wrappers."),
    ]


def do_not_implement_guidance() -> list[dict[str, Any]]:
    rows = [
        ("free_form_oracle", "Do not let agents produce forecasts without OPE contracts and resolution rules."),
        ("raw_crud_writes", "Do not bypass lifecycle operation receipts, idempotency, leases, or read models."),
        ("unbounded_background_loops", "Do not start long-running loops without explicit bounds and control state."),
        ("silent_deletion", "Use archive tombstones or redaction receipts instead of physical delete."),
        ("hidden_live_fetches", "Do not fetch live sources unless an explicit checked command allows it."),
        ("credential_storage_in_records", "Store credential references, not credential values."),
        ("automatic_method_upgrades", "Do not upgrade methods without benchmark evidence, approvals, and rollback plans."),
    ]
    return [{"behaviorKey": key, "allowed": False, "guidance": guidance} for key, guidance in rows]


def starter_templates() -> list[dict[str, Any]]:
    return [
        {
            "templateKey": "embedded_service",
            "templateName": "Embedded OPE service wrapper",
            "templatePath": "spec/agent-implementation-kit.md#embedded-service-template",
            "usesExistingSurfaces": True,
            "createsHostedService": False,
            "storesCredentials": False,
        },
        {
            "templateKey": "cli_flow",
            "templateName": "CLI prediction setup flow",
            "templatePath": "spec/agent-prediction-manual.md#cli-flow-template",
            "usesExistingSurfaces": True,
            "createsHostedService": False,
            "storesCredentials": False,
        },
        {
            "templateKey": "mcp_host_wrapper",
            "templateName": "Local MCP host wrapper",
            "templatePath": "spec/forecast-question-discovery.md#mcp-host-wrapper-template",
            "usesExistingSurfaces": True,
            "createsHostedService": False,
            "storesCredentials": False,
        },
    ]


def conformance_fixture_pack() -> dict[str, Any]:
    return {
        "fixturePackId": "agentimplementationkitfixtures-001",
        "questionDiscoveryIntakeCount": 1,
        "candidateReadbackCount": 4,
        "validationReportCount": 4,
        "embeddedApiCallExampleCount": 2,
        "operationReceiptExampleCount": 2,
        "sourceConfigurationExampleCount": 2,
        "workerTickExampleCount": 1,
        "blockedPathExampleCount": 4,
        "normalChecksCreateForecastArtifacts": False,
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "freeFormOracleAllowed": False,
        "questionDiscoveryCreatesForecastArtifacts": False,
        "rawCrudWritesAllowed": False,
        "unboundedBackgroundLoopsAllowed": False,
        "silentDeletionAllowed": False,
        "hiddenLiveFetchAllowed": False,
        "credentialValuesStored": False,
        "automaticMethodUpgradeAllowed": False,
        "hostedRuntimeRequired": False,
    }


def build_agent_implementation_kit() -> dict[str, Any]:
    quickstart = quickstart_front_door()
    candidates = candidate_contract_readbacks()
    validation_reports = mechanical_validation_reports(candidates)
    adapters = adapter_readbacks()
    templates = starter_templates()
    return {
        "agentImplementationKitId": "agentimplementationkit-001",
        "generatedAt": GENERATED_AT,
        "kitStatus": "agent_prediction_implementation_kit_checked",
        "kitScope": "local_agent_readback_and_templates",
        "quickstartFrontDoor": quickstart,
        "predictionManual": prediction_manual(),
        "questionDiscoveryIntakeContract": question_discovery_intake_contract(),
        "candidateContractReadbacks": candidates,
        "mechanicalValidationReports": validation_reports,
        "firstRunSourcePaths": first_run_source_paths(),
        "adapterReadbacks": adapters,
        "doNotImplementGuidance": do_not_implement_guidance(),
        "starterTemplates": templates,
        "conformanceFixturePack": conformance_fixture_pack(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "quickstartStepCount": len(quickstart["steps"]),
            "manualStepCount": len(MANUAL_STEP_KEYS),
            "candidateReadbackCount": len(candidates),
            "validationReportCount": len(validation_reports),
            "adapterReadbackCount": len(adapters),
            "starterTemplateCount": len(templates),
        },
        "warnings": [
            "The implementation kit is guidance and conformance readback, not a new forecast execution path.",
            "Question discovery never creates forecast artifacts; accepted candidates route to existing OPE lifecycle surfaces.",
            "Private API and database source execution remains blocked until checked runtimes are added.",
        ],
    }


def validate_agent_implementation_kit(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise AgentImplementationKitError("agent implementation kit failed schema validation")
    if record["summary"]["manualStepCount"] != len(record["predictionManual"]["steps"]):
        raise AgentImplementationKitError("manual step count drifted")
    if record["summary"]["candidateReadbackCount"] != len(record["candidateContractReadbacks"]):
        raise AgentImplementationKitError("candidate readback count drifted")
    if record["summary"]["validationReportCount"] != len(record["mechanicalValidationReports"]):
        raise AgentImplementationKitError("validation report count drifted")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "quickstart":
        return record["quickstartFrontDoor"]
    if view == "manual":
        return record["predictionManual"]
    if view == "intake":
        return record["questionDiscoveryIntakeContract"]
    if view == "candidates":
        return record["candidateContractReadbacks"]
    if view == "validation":
        return record["mechanicalValidationReports"]
    if view == "adapters":
        return record["adapterReadbacks"]
    if view == "templates":
        return record["starterTemplates"]
    if view == "blocked":
        return record["doNotImplementGuidance"]
    if view == "boundary":
        return record["executionBoundary"]
    raise AgentImplementationKitError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated agent implementation kit fixture")
    parser.add_argument("--check", action="store_true", help="check generated agent implementation kit fixture")
    parser.add_argument(
        "--view",
        choices=["full", "quickstart", "manual", "intake", "candidates", "validation", "adapters", "templates", "blocked", "boundary"],
        default="full",
        help="emit a focused agent implementation kit view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_agent_implementation_kit()
    validate_agent_implementation_kit(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="agent implementation kit",
            regen="python3 scripts/generate_agent_implementation_kit.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="agent implementation kit",
            regen="python3 scripts/generate_agent_implementation_kit.py --write",
        )
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
