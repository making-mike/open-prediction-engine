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
GENERATED_AT = "2026-06-07T12:00:00Z"
DEFAULT_GOAL = "add predictions to my app"
SETUP_ENGINE_VIEWS = [
    "full",
    "summary",
    "contracts",
    "sources",
    "baseline",
    "host-wrapper",
    "claim-boundary",
    "examples",
]


class SetupEngineError(Exception):
    pass


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


def host_wrapper() -> dict[str, Any]:
    return {
        "wrapperStatus": "ready_for_host_render",
        "renderBeforeForecastArtifacts": True,
        "renderSections": [
            "candidateForecastContracts",
            "requiredSourceRoles",
            "baselineGuidance",
            "claimBoundary",
            "followUpSurfaces",
        ],
        "recommendedDataShape": "Render this setup-engine JSON directly as the host prediction setup plan before forecast cards exist.",
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


def interface_bindings(goal: str) -> list[dict[str, Any]]:
    quoted_goal = json.dumps(goal)
    return [
        {
            "interface": "cli",
            "implementedStatus": "implemented_local",
            "command": f"python3 scripts/ope.py setup-engine --goal {quoted_goal}",
            "boundary": "CLI returns a checked setup plan and does not create forecast artifacts.",
        },
        {
            "interface": "agent_call",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py agent-call --operation setup_engine",
            "boundary": "Agent-call wraps the same setup plan in one transport-neutral envelope.",
        },
        {
            "interface": "local_mcp",
            "implementedStatus": "implemented_local",
            "command": "python3 scripts/ope.py mcp-stdio",
            "toolName": "ope_setup_engine",
            "boundary": "MCP exposes goal and view arguments only; it rejects hidden raw payload fields.",
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


def build_setup_engine(goal: str = DEFAULT_GOAL) -> dict[str, Any]:
    warnings = [
        "Setup-engine is the preferred first readback for agents adding prediction to a host project.",
        "It returns contracts, source roles, baseline guidance, host-wrapper shape, and claim boundaries before forecast artifacts exist.",
        "It does not execute source reads, store credentials, accept raw private rows, create hosted runtime, or claim model quality.",
    ]
    return {
        "setupEngineId": "setupengine-001",
        "generatedAt": GENERATED_AT,
        "goal": goal,
        "engineSetupStatus": "checked_readback",
        "recommendedFirstCommand": f"python3 scripts/ope.py setup-engine --goal {json.dumps(goal)}",
        "candidateForecastContracts": candidate_forecast_contracts(),
        "requiredSourceRoles": required_source_roles(),
        "baselineGuidance": baseline_guidance(),
        "hostWrapper": host_wrapper(),
        "claimBoundary": claim_boundary(),
        "exampleGoals": example_goals(),
        "interfaceBindings": interface_bindings(goal),
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
            "goal": record["goal"],
            "engineSetupStatus": record["engineSetupStatus"],
            "recommendedFirstCommand": record["recommendedFirstCommand"],
            "candidateCount": len(record["candidateForecastContracts"]),
            "forecastableCandidateCount": sum(
                1 for item in record["candidateForecastContracts"] if item["contractStatus"] == "forecastable"
            ),
            "hostWrapper": record["hostWrapper"],
            "claimBoundary": record["claimBoundary"],
            "warnings": record["warnings"],
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
    if view == "host-wrapper":
        return {
            "view": "host-wrapper",
            "setupEngineId": record["setupEngineId"],
            "goal": record["goal"],
            "hostWrapper": record["hostWrapper"],
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
    parser.add_argument("--view", choices=SETUP_ENGINE_VIEWS, default="full", help="print a focused setup-engine view")
    parser.add_argument("--write", action="store_true", help="write generated setup-engine fixture")
    parser.add_argument("--check", action="store_true", help="check generated setup-engine fixture")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_setup_engine(args.goal)
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
