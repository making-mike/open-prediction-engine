#!/usr/bin/env python3
"""Generate the checked domain-agnostic setup-engine readback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_prediction_goal_catalog import build_prediction_goal_catalog, compact_setup_engine_examples
from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "setup-engine"
OUTPUT_PATH = GENERATED / "ope-setup-engine.generated.json"
SCHEMA = SPEC / "setup-engine.schema.json"
REQUEST_SCHEMA = SPEC / "setup-engine-request.schema.json"
GENERATED_AT = "2026-06-07T12:00:00Z"
DEFAULT_GOAL = "add predictions to my app"
REQUIRED_REQUEST_SOURCE_ROLES = {"forecast_time_signal", "historical_outcome", "resolution_outcome"}
SETUP_ENGINE_VIEWS = [
    "full",
    "summary",
    "request",
    "contracts",
    "sources",
    "baseline",
    "forecast-card-preview",
    "host-wrapper",
    "claim-boundary",
    "examples",
]


class SetupEngineError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_setup_engine_request(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SetupEngineError(f"could not read setup-engine request {path}") from exc
    except json.JSONDecodeError as exc:
        raise SetupEngineError(f"setup-engine request is not valid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise SetupEngineError("setup-engine request must be a JSON object")
    validate_setup_engine_request(value)
    return value


def validate_setup_engine_request(record: dict[str, Any]) -> None:
    errors = validate_record(record, REQUEST_SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SetupEngineError("setup-engine request failed schema validation")


def baseline_method(execution_allowed: bool = True) -> dict[str, Any]:
    return {
        "methodId": "historical_frequency_baseline",
        "methodClass": "historical_baseline" if execution_allowed else "blocked",
        "executionAllowed": execution_allowed,
        "qualityClaimAllowed": False,
        "notes": "Start with a baseline until resolved outcomes justify stronger methods.",
    }


def candidate_contract(
    contract_id: str,
    status: str,
    title: str,
    question_template: str,
    decision: str,
    horizon: str,
    resolution_rule: str,
    required_roles: list[str],
    reason_codes: list[str],
    next_action: str,
    *,
    execution_allowed: bool = True,
) -> dict[str, Any]:
    return {
        "contractId": contract_id,
        "contractStatus": status,
        "title": title,
        "questionTemplate": question_template,
        "decisionToSupport": decision,
        "horizon": horizon,
        "resolutionRule": resolution_rule,
        "requiredSourceRoles": required_roles,
        "baselineMethod": baseline_method(execution_allowed),
        "reasonCodes": reason_codes,
        "nextAction": next_action,
    }


def candidate_forecast_contracts() -> list[dict[str, Any]]:
    return [
        candidate_contract(
            "setupcontract-001",
            "forecastable",
            "Threshold event risk",
            "Will the named future operating window exceed the declared threshold before the resolution deadline?",
            "Prioritize, warn, defer, or allocate capacity based on a measurable future event.",
            "future window supplied by the host app",
            "Resolve from an approved outcome source after the close time using the declared threshold.",
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            ["future_window_present", "threshold_present", "resolution_source_required"],
            "Collect approved source references and run source intake before any forecast execution.",
        ),
        candidate_contract(
            "setupcontract-002",
            "needs_clarification",
            "Ambiguous threshold forecast",
            "Will the future event be bad enough to change the host decision?",
            "Support a host action only after the caller defines what bad enough means.",
            "future window is present but threshold is missing",
            "Resolution cannot be scored until the measurable threshold is supplied.",
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            ["missing_threshold", "ambiguous_outcome_definition"],
            "Ask for a numeric threshold, categorical threshold, or explicit yes/no outcome rule.",
        ),
        candidate_contract(
            "setupcontract-003",
            "blocked",
            "Unsafe private source setup",
            "Will records from a private source predict a future host outcome?",
            "Stop setup until private inputs are replaced with approved references.",
            "future window cannot be evaluated from unsafe inputs",
            "Blocked inputs cannot enter source intake or resolution setup.",
            ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
            ["raw_credential_value", "raw_private_rows", "unapproved_source"],
            "Replace raw payloads with source references, credential references, and caller approval records.",
            execution_allowed=False,
        ),
        candidate_contract(
            "setupcontract-004",
            "rejected",
            "Past outcome analysis",
            "Did the event happen yesterday?",
            "Historical analysis may be useful, but it is not a future forecast contract.",
            "past event",
            "Past-tense questions are not forecastable by the setup-engine path.",
            ["resolution_outcome"],
            ["past_tense_question", "not_future_facing"],
            "Rewrite the request as a future-facing measurable question or use a non-forecast analysis path.",
            execution_allowed=False,
        ),
    ]


def request_command(goal: str, request_path: Path | None) -> str:
    if request_path is not None:
        return f"python3 scripts/ope.py setup-engine --request {json.dumps(rel(request_path))}"
    return f"python3 scripts/ope.py setup-engine --goal {json.dumps(goal)}"


def blocked_input_flags(setup_request: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    boundary = setup_request["executionBoundary"]
    for key, flag in [
        ("containsCredentialValues", "contains_credential_values"),
        ("containsRawPrivateRows", "contains_raw_private_rows"),
        ("containsRawSql", "contains_raw_sql"),
        ("requestsForecastArtifacts", "requests_forecast_artifacts"),
        ("requestsLiveFetch", "requests_live_fetch"),
        ("allowsSourceReads", "allows_source_reads"),
        ("writesLocalState", "writes_local_state"),
    ]:
        if boundary[key]:
            flags.append(flag)
    for hint in setup_request["sourceHints"]:
        if hint["approvalStatus"] == "blocked_raw_payload":
            flags.append("blocked_raw_payload")
        if hint["containsCredentialValue"]:
            flags.append("source_hint_contains_credential_value")
        if hint["containsRawPrivateRows"]:
            flags.append("source_hint_contains_raw_private_rows")
        if hint["containsRawSql"]:
            flags.append("source_hint_contains_raw_sql")
    return sorted(set(flags))


def build_request_summary(
    goal: str,
    setup_request: dict[str, Any] | None,
    request_path: Path | None,
) -> dict[str, Any]:
    command = request_command(goal, request_path)
    if setup_request is None:
        return {
            "structuredRequestProvided": False,
            "completenessStatus": "goal_text_only",
            "providedSections": ["goal"],
            "approvedSourceHintCount": 0,
            "needsApprovalSourceHintCount": 0,
            "blockedInputFlags": [],
            "missingSourceRoles": sorted(REQUIRED_REQUEST_SOURCE_ROLES),
            "readyForSourceIntake": False,
            "safeToUseAsSetupInput": True,
            "requestCommand": command,
            "nextAction": "Provide a structured setup-engine request or choose one candidate contract and bind approved source references.",
        }

    approved_source_count = sum(
        1 for hint in setup_request["sourceHints"] if hint["approvalStatus"] == "approved_reference"
    )
    needs_approval_count = sum(
        1 for hint in setup_request["sourceHints"] if hint["approvalStatus"] == "needs_approval"
    )
    approved_roles = {
        hint["roleName"]
        for hint in setup_request["sourceHints"]
        if hint["approvalStatus"] == "approved_reference"
    }
    missing_roles = sorted(REQUIRED_REQUEST_SOURCE_ROLES - approved_roles)
    flags = blocked_input_flags(setup_request)
    baseline = setup_request["baselineHint"]
    resolution = setup_request["resolutionHint"]
    if flags:
        completeness_status = "blocked_by_unsafe_inputs"
        next_action = "Replace unsafe inputs with approved source references, credential references, and sanitized summaries before setup continues."
    elif needs_approval_count or missing_roles:
        completeness_status = "needs_source_approval"
        next_action = "Collect approved source references for the missing roles before source intake or forecast execution."
    elif not resolution["scoringReady"] or not baseline["historicalOutcomeAvailable"] or not baseline["minimumComparableRowsKnown"]:
        completeness_status = "needs_clarification"
        next_action = "Clarify baseline and resolution readiness before source intake or method selection."
    else:
        completeness_status = "ready_for_source_intake"
        next_action = "Run source intake with the approved source references before any forecast execution."

    return {
        "structuredRequestProvided": True,
        "setupEngineRequestId": setup_request["setupEngineRequestId"],
        "completenessStatus": completeness_status,
        "providedSections": [
            "goal",
            "decisionContext",
            "outcome",
            "horizon",
            "sourceHints",
            "resolutionHint",
            "baselineHint",
            "executionBoundary",
        ],
        "approvedSourceHintCount": approved_source_count,
        "needsApprovalSourceHintCount": needs_approval_count,
        "blockedInputFlags": flags,
        "missingSourceRoles": missing_roles,
        "readyForSourceIntake": completeness_status == "ready_for_source_intake",
        "safeToUseAsSetupInput": not flags,
        "requestCommand": command,
        "nextAction": next_action,
    }


def request_bound_candidate(
    setup_request: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    outcome = setup_request["outcome"]
    horizon = setup_request["horizon"]
    decision = setup_request["decisionContext"]
    title = f"{outcome['outcomeName']} risk".capitalize()
    if summary["readyForSourceIntake"]:
        status = "forecastable"
        reason_codes = [
            "structured_request",
            "future_window_present",
            "threshold_present",
            "resolution_source_declared",
            "approved_source_refs_present",
        ]
        next_action = "Run source intake with the approved source references before forecast execution."
    elif not summary["safeToUseAsSetupInput"]:
        status = "blocked"
        reason_codes = [
            "structured_request",
            "unsafe_input_blocked",
            "raw_private_or_secret_input",
        ]
        next_action = "Replace unsafe inputs with approved source references and rerun setup-engine."
    else:
        status = "needs_clarification"
        reason_codes = [
            "structured_request",
            "missing_source_approval",
            "baseline_or_resolution_not_ready",
        ]
        next_action = "Collect missing approvals and clarify baseline or resolution readiness."
    return candidate_contract(
        "setupcontract-001",
        status,
        title,
        f"Will {outcome['outcomeName']} meet {outcome['threshold']} during {horizon['forecastWindow']}?",
        decision["decisionToSupport"],
        horizon["forecastWindow"],
        setup_request["resolutionHint"]["resolutionRule"],
        ["forecast_time_signal", "historical_outcome", "resolution_outcome"],
        reason_codes,
        next_action,
        execution_allowed=summary["readyForSourceIntake"],
    )


def candidate_forecast_contracts_for_request(
    setup_request: dict[str, Any] | None,
    summary: dict[str, Any],
) -> list[dict[str, Any]]:
    generic_contracts = candidate_forecast_contracts()
    if setup_request is None:
        return generic_contracts
    return [
        request_bound_candidate(setup_request, summary),
        *generic_contracts[1:],
    ]


def source_role(
    role_name: str,
    purpose: str,
    accepted_source_kinds: list[str],
    required_for_forecast: bool,
    required_for_resolution: bool,
    next_action: str,
) -> dict[str, Any]:
    return {
        "roleName": role_name,
        "purpose": purpose,
        "acceptedSourceKinds": accepted_source_kinds,
        "requiredForForecast": required_for_forecast,
        "requiredForResolution": required_for_resolution,
        "acceptsCredentialValues": False,
        "acceptsRawPrivateRows": False,
        "acceptsRawSql": False,
        "nextAction": next_action,
    }


def required_source_roles() -> list[dict[str, Any]]:
    return [
        source_role(
            "forecast_time_signal",
            "Evidence known before close time that can support a forecast.",
            ["local_file", "source_adapter_output", "auto_evidence_connector", "manual_mapping"],
            True,
            False,
            "Bind approved forecast-time evidence through source intake or adapter output.",
        ),
        source_role(
            "historical_outcome",
            "Past comparable outcomes used for the baseline and benchmark gate.",
            ["local_file", "source_adapter_output", "manual_mapping"],
            True,
            False,
            "Provide comparable historical examples before selecting stronger methods.",
        ),
        source_role(
            "resolution_outcome",
            "Outcome evidence collected after close time to resolve and score forecasts.",
            ["local_file", "source_adapter_output", "auto_evidence_connector", "manual_mapping"],
            False,
            True,
            "Declare the resolver source and scoring rule before creating forecasts.",
        ),
        source_role(
            "source_policy",
            "Policy metadata that records approval, retention, tenant scope, and blocked source kinds.",
            ["source_manifest", "source_binding", "credential_reference"],
            True,
            True,
            "Record source policy before source intake, forecast execution, or resolution.",
        ),
    ]


def baseline_guidance() -> dict[str, Any]:
    return {
        "defaultMethodId": "historical_frequency_baseline",
        "defaultMethodClass": "historical_baseline",
        "strongerMethodsAllowedAfter": [
            "accepted_source_intake",
            "setup_benchmark_gate_passed",
            "leakage_controls_checked",
            "resolved_outcome_sample_threshold_met",
        ],
        "benchmarkGateRequired": True,
        "calibrationGateRequired": True,
        "notes": "The setup-engine path ranks contracts and source roles; it does not claim model lift before scored outcomes exist.",
    }


def forecast_card_preview(
    goal: str,
    setup_request: dict[str, Any] | None,
    summary: dict[str, Any],
) -> dict[str, Any]:
    if setup_request is None:
        question_preview = "Will the selected future operating window exceed the declared threshold?"
        outcome_label = "future threshold event"
        positive_class_label = "threshold exceeded"
        horizon_label = "future window supplied by the host app"
        resolution_rule = "Resolve from an approved outcome source after close time using the declared threshold."
        evidence_status = "source_intake_required"
        baseline_status = "baseline_required_before_model_claims"
        generated_from = "goal_text"
    else:
        outcome = setup_request["outcome"]
        horizon = setup_request["horizon"]
        question_preview = (
            f"Will {outcome['outcomeName']} reach the positive class "
            f"({outcome['positiveClass']}) during {horizon['forecastWindow']}?"
        )
        outcome_label = outcome["outcomeName"]
        positive_class_label = outcome["positiveClass"]
        horizon_label = horizon["forecastWindow"]
        resolution_rule = setup_request["resolutionHint"]["resolutionRule"]
        generated_from = "structured_request"
        if not summary["safeToUseAsSetupInput"]:
            evidence_status = "blocked_until_safe_sources"
            baseline_status = "blocked_until_safe_sources"
        elif summary["readyForSourceIntake"]:
            evidence_status = "structured_sources_ready_for_intake"
            baseline_status = "baseline_hint_ready"
        else:
            evidence_status = "source_approval_required"
            baseline_status = "baseline_required_before_model_claims"

    return {
        "previewStatus": "setup_only_not_forecast_artifact",
        "generatedFrom": generated_from,
        "forecastArtifactCreated": False,
        "probabilityAvailable": False,
        "questionPreview": question_preview,
        "outcomeLabel": outcome_label,
        "positiveClassLabel": positive_class_label,
        "horizonLabel": horizon_label,
        "resolutionRulePreview": resolution_rule,
        "evidenceStatus": evidence_status,
        "baselineStatus": baseline_status,
        "displaySections": [
            "questionPreview",
            "probabilityPlaceholder",
            "evidenceSummary",
            "baselineComparison",
            "resolutionRule",
            "claimBoundary",
        ],
        "allowedPreviewFields": [
            "questionPreview",
            "outcomeLabel",
            "positiveClassLabel",
            "horizonLabel",
            "resolutionRulePreview",
            "evidenceStatus",
            "baselineStatus",
            "claimBoundary",
        ],
        "blockedPreviewFields": [
            "forecastId",
            "probability",
            "confidenceLabel",
            "qualityClaim",
            "calibrationClaim",
            "credentialValues",
            "rawPrivateRows",
            "rawSql",
        ],
        "readCommandAfterForecast": (
            "python3 scripts/ope.py read --record-type forecast-card --id <forecast-id> --question-id <question-id>"
        ),
        "nextAction": summary["nextAction"],
    }


def host_wrapper() -> dict[str, Any]:
    return {
        "wrapperStatus": "ready_for_host_render",
        "renderBeforeForecastArtifacts": True,
        "renderSections": [
            "candidateForecastContracts",
            "requiredSourceRoles",
            "baselineGuidance",
            "forecastCardPreview",
            "claimBoundary",
            "followUpSurfaces",
        ],
        "recommendedDataShape": "Render this setup-engine JSON, including forecastCardPreview, before forecast cards exist.",
        "blockedHostResponsibilities": [
            "do_not_invent_parallel_risk_engine_before_setup_readback",
            "do_not_claim_prediction_quality_before_resolution_scoring",
            "do_not_submit_credentials_raw_rows_or_raw_sql",
            "do_not_treat_setup_engine_as_hosted_runtime",
        ],
        "nextAction": "Choose one forecastable contract, bind approved sources, then use source intake and method gates.",
    }


def claim_boundary() -> dict[str, Any]:
    return {
        "qualityClaimAllowed": False,
        "calibrationClaimAllowed": False,
        "hostedRuntimeProvided": False,
        "trainedModelProvided": False,
        "executesLiveFetch": False,
        "acceptsRawSql": False,
        "acceptsCredentialValues": False,
        "acceptsRawPrivateRows": False,
        "minimumResolvedOutcomesForQualityClaim": 30,
        "notes": "Setup-engine output is a planning and contract readback; quality claims require resolved comparable outcomes.",
    }


def example_goals() -> list[dict[str, Any]]:
    return compact_setup_engine_examples()


def interface_bindings(goal: str, request_path: Path | None = None) -> list[dict[str, Any]]:
    cli_command = request_command(goal, request_path)
    return [
        {
            "interface": "cli",
            "implementedStatus": "implemented_local",
            "command": cli_command,
            "boundary": "CLI returns a checked setup plan and does not create forecast artifacts.",
        },
        {
            "interface": "agent_call",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py agent-call --operation setup_engine",
            "boundary": "Agent-call wraps the same setup plan and may accept a structured setup request path.",
        },
        {
            "interface": "local_mcp",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py mcp-stdio",
            "toolName": "ope_setup_engine",
            "boundary": "MCP exposes goal, view, and structured request arguments while rejecting hidden raw payload fields.",
        },
    ]


def follow_up_surfaces() -> list[dict[str, str]]:
    return [
        {
            "surface": "explain-fit",
            "command": 'python3 scripts/ope.py explain-fit --goal "add predictions to my app"',
            "relationship": "Use for a short fit verdict after reading setup-engine summary.",
        },
        {
            "surface": "capabilities",
            "command": "python3 scripts/ope.py capabilities",
            "relationship": "Use for machine-readable helps-with and does-not-provide boundaries.",
        },
        {
            "surface": "agent-implementation-kit",
            "command": "python3 scripts/ope.py agent-implementation-kit --view quickstart",
            "relationship": "Use after choosing to wire OPE into a host project.",
        },
        {
            "surface": "prediction-feature-setup",
            "command": "python3 scripts/ope.py prediction-feature-setup --view response --case accepted",
            "relationship": "Use when a host feature needs compact accepted/blocked response examples.",
        },
        {
            "surface": "source-builder",
            "command": "python3 scripts/ope.py source-builder --check",
            "relationship": "Use only after approved source references or caller-approved local files exist.",
        },
    ]


def build_setup_engine(
    goal: str = DEFAULT_GOAL,
    setup_request: dict[str, Any] | None = None,
    request_path: Path | None = None,
) -> dict[str, Any]:
    if setup_request is not None:
        validate_setup_engine_request(setup_request)
        goal = setup_request["goal"]
    summary = build_request_summary(goal, setup_request, request_path)
    warnings = [
        "Setup-engine is the preferred first readback for agents adding prediction to a host project.",
        "It returns contracts, source roles, baseline guidance, host-wrapper shape, and claim boundaries before forecast artifacts exist.",
        "It does not execute source reads, store credentials, accept raw private rows, create hosted runtime, or claim model quality.",
    ]
    return {
        "setupEngineId": "setupengine-001",
        "generatedAt": GENERATED_AT,
        "inputMode": "structured_request" if setup_request is not None else "goal_text",
        "goal": goal,
        "engineSetupStatus": "checked_readback",
        "recommendedFirstCommand": summary["requestCommand"],
        "requestSummary": summary,
        "candidateForecastContracts": candidate_forecast_contracts_for_request(setup_request, summary),
        "requiredSourceRoles": required_source_roles(),
        "baselineGuidance": baseline_guidance(),
        "forecastCardPreview": forecast_card_preview(goal, setup_request, summary),
        "hostWrapper": host_wrapper(),
        "claimBoundary": claim_boundary(),
        "exampleGoals": example_goals(),
        "interfaceBindings": interface_bindings(goal, request_path),
        "followUpSurfaces": follow_up_surfaces(),
        "warnings": warnings,
        "createsForecastArtifacts": False,
        "hostedRuntimeRequired": False,
    }


def validate_setup_engine(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SetupEngineError("setup-engine failed schema validation")


def view_payload(record: dict[str, Any], view: str) -> dict[str, Any]:
    if view == "full":
        return record
    if view == "summary":
        return {
            "view": "summary",
            "setupEngineId": record["setupEngineId"],
            "inputMode": record["inputMode"],
            "goal": record["goal"],
            "engineSetupStatus": record["engineSetupStatus"],
            "recommendedFirstCommand": record["recommendedFirstCommand"],
            "requestSummary": record["requestSummary"],
            "candidateCount": len(record["candidateForecastContracts"]),
            "forecastableCandidateCount": sum(
                1 for item in record["candidateForecastContracts"] if item["contractStatus"] == "forecastable"
            ),
            "forecastCardPreview": record["forecastCardPreview"],
            "hostWrapper": record["hostWrapper"],
            "claimBoundary": record["claimBoundary"],
            "warnings": record["warnings"],
        }
    if view == "request":
        return {
            "view": "request",
            "setupEngineId": record["setupEngineId"],
            "inputMode": record["inputMode"],
            "goal": record["goal"],
            "requestSummary": record["requestSummary"],
            "recommendedFirstCommand": record["recommendedFirstCommand"],
        }
    if view == "contracts":
        return {
            "view": "contracts",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "candidateForecastContracts": record["candidateForecastContracts"],
        }
    if view == "sources":
        return {
            "view": "sources",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "requiredSourceRoles": record["requiredSourceRoles"],
            "claimBoundary": record["claimBoundary"],
        }
    if view == "baseline":
        return {
            "view": "baseline",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "baselineGuidance": record["baselineGuidance"],
            "candidateForecastContracts": record["candidateForecastContracts"],
        }
    if view == "forecast-card-preview":
        return {
            "view": "forecast-card-preview",
            "setupEngineId": record["setupEngineId"],
            "inputMode": record["inputMode"],
            "goal": record["goal"],
            "requestSummary": record["requestSummary"],
            "forecastCardPreview": record["forecastCardPreview"],
            "claimBoundary": record["claimBoundary"],
        }
    if view == "host-wrapper":
        return {
            "view": "host-wrapper",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "hostWrapper": record["hostWrapper"],
            "forecastCardPreview": record["forecastCardPreview"],
            "interfaceBindings": record["interfaceBindings"],
            "followUpSurfaces": record["followUpSurfaces"],
        }
    if view == "claim-boundary":
        return {
            "view": "claim-boundary",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "claimBoundary": record["claimBoundary"],
            "warnings": record["warnings"],
        }
    if view == "examples":
        catalog = build_prediction_goal_catalog()
        return {
            "view": "examples",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "catalogBinding": {
                "predictionGoalCatalogId": catalog["predictionGoalCatalogId"],
                "catalogStatus": catalog["catalogStatus"],
                "command": "python3 scripts/ope.py prediction-goal-catalog",
            },
            "exampleGoals": catalog["goalExamples"],
            "summary": catalog["summary"],
        }
    raise SetupEngineError(f"unsupported setup-engine view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="host prediction goal to turn into a setup-engine readback")
    parser.add_argument("--request", type=Path, help="structured setup-engine request JSON with host app context")
    parser.add_argument("--view", choices=SETUP_ENGINE_VIEWS, default="full", help="print a focused setup-engine view")
    parser.add_argument("--write", action="store_true", help="write generated setup-engine fixture")
    parser.add_argument("--check", action="store_true", help="check generated setup-engine fixture")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_request = load_setup_engine_request(args.request) if args.request else None
    record = build_setup_engine(args.goal, setup_request, args.request)
    validate_setup_engine(record)
    if args.write:
        fixture = build_setup_engine(DEFAULT_GOAL)
        validate_setup_engine(fixture)
        write_generated(
            OUTPUT_PATH,
            fixture,
            label="setup engine",
            regen="python3 scripts/generate_setup_engine.py --write",
        )
        return
    if args.check:
        fixture = build_setup_engine(DEFAULT_GOAL)
        validate_setup_engine(fixture)
        check_generated(
            OUTPUT_PATH,
            fixture,
            label="setup engine",
            regen="python3 scripts/generate_setup_engine.py --write",
        )
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
