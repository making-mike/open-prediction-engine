#!/usr/bin/env python3
"""Generate or check the general prediction-agent adoption surface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-agent-adoption"
OUTPUT_PATH = GENERATED / "ope-prediction-agent-adoption.generated.json"
CAPABILITIES_PATH = ROOT / "ope.capabilities.json"
SCHEMA = SPEC / "prediction-agent-adoption.schema.json"
GENERATED_AT = "2026-06-06T12:00:00Z"
FIRST_COMMAND = 'python3 scripts/ope.py explain-fit --goal "add predictions to my app"'


class PredictionAgentAdoptionError(Exception):
    pass


def capability(key: str, label: str, why: str) -> dict[str, Any]:
    return {
        "capabilityKey": key,
        "label": label,
        "whyItMatters": why,
    }


def non_goal(key: str, label: str, replacement: str) -> dict[str, Any]:
    return {
        "nonGoalKey": key,
        "label": label,
        "replacement": replacement,
    }


def capability_manifest() -> dict[str, Any]:
    return {
        "manifestVersion": "1.0",
        "manifestStatus": "checked",
        "projectName": "Open Prediction Engine",
        "tagline": "A prediction credibility layer for agents building forecast features.",
        "firstCommand": FIRST_COMMAND,
        "fitCommand": "python3 scripts/ope.py explain-fit --goal <host prediction goal>",
        "adoptionEvalCommand": "python3 scripts/ope.py adoption-eval",
        "helpsWith": [
            capability(
                "forecast_contracts",
                "Resolvable forecast contracts",
                "Turns vague prediction ideas into future-facing questions with horizons and resolution rules.",
            ),
            capability(
                "evidence_provenance",
                "Evidence provenance",
                "Records which source roles and forecast-time evidence supported a prediction.",
            ),
            capability(
                "baseline_scoring",
                "Baseline comparison",
                "Keeps new methods honest by comparing them against simple baselines before stronger claims.",
            ),
            capability(
                "resolution_and_scoring",
                "Resolution and scoring",
                "Separates forecast-time evidence from outcome evidence and scores resolved forecasts.",
            ),
            capability(
                "calibration_gates",
                "Calibration gates",
                "Blocks calibration and quality claims until enough comparable resolved outcomes exist.",
            ),
            capability(
                "agent_safe_readbacks",
                "Agent-safe readbacks",
                "Gives agents compact commands and schema-bound records instead of free-form oracle output.",
            ),
        ],
        "doesNotProvide": [
            non_goal("frontend", "Frontend or dashboard", "Build UI in the host app and render OPE forecast cards."),
            non_goal("hosted_api", "Hosted API", "Use local CLI, in-process calls, agent-call, or local MCP until a transport is checked."),
            non_goal("trained_model", "Trained model out of the box", "Bring a model and compare it through OPE method and scoring gates."),
            non_goal("generic_web_crawler", "Generic web crawler", "Provide approved sources or checked adapters under source policy."),
            non_goal("production_scheduler", "Production scheduler", "Use host scheduling; OPE only exposes checked local readbacks today."),
        ],
        "extensionPointKeys": [
            "source_adapter",
            "forecast_method",
            "resolver",
            "scorer",
            "host_app_wrapper",
        ],
        "boundary": {
            "normalChecksOffline": True,
            "defaultOutputCompact": True,
            "qualityClaimRequiresResolvedEvidence": True,
            "credentialsStored": False,
            "rawPrivateRowsAccepted": False,
        },
    }


def extension_point(key: str, description: str, host_provides: str, ope_checks: str, command: str) -> dict[str, Any]:
    return {
        "extensionKey": key,
        "description": description,
        "hostProvides": host_provides,
        "opeChecks": ope_checks,
        "firstReadbackCommand": command,
        "createsHostedRuntime": False,
    }


def extension_points() -> list[dict[str, Any]]:
    return [
        extension_point(
            "source_adapter",
            "A host or agent converts an external data source into sanitized OPE source-adapter output.",
            "Approved source refs, field mappings, and sanitized rows or manifests.",
            "Source policy, mapping confidence, leakage, freshness, and role fit.",
            "python3 scripts/ope.py source-adapter-intake",
        ),
        extension_point(
            "forecast_method",
            "A host plugs in deterministic or model-assisted forecast output for OPE comparison.",
            "Method metadata, forecast output, training cutoff, and feature provenance.",
            "Baseline comparison, benchmark binding, anti-leakage, and method eligibility.",
            "python3 scripts/ope.py setup-method",
        ),
        extension_point(
            "resolver",
            "A host supplies outcome evidence after the resolution window closes.",
            "Resolution-only source rows and outcome observation timestamps.",
            "Forecast-before-outcome boundary, declared resolution rule, and unscorable status.",
            "python3 scripts/ope.py resolution-jobs",
        ),
        extension_point(
            "scorer",
            "A host reads or extends scoring reports after outcomes are resolved.",
            "Resolved outcomes, forecast IDs, and accepted scoring rule choices.",
            "Score binding, baseline lift, exclusion reasons, and comparable sample boundaries.",
            "python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102",
        ),
        extension_point(
            "host_app_wrapper",
            "A host app wraps OPE readbacks in its own API, UI, worker, or product flow.",
            "Product UI, auth, runtime, scheduling, notifications, and user workflow.",
            "Claim boundaries, forecast-card readbacks, lifecycle bundles, and safe blocked paths.",
            "python3 scripts/ope.py prediction-feature-setup --view response --case accepted",
        ),
    ]


def entry_point(key: str, command: str, default_format: str, purpose: str) -> dict[str, Any]:
    return {
        "entryKey": key,
        "command": command,
        "defaultFormat": default_format,
        "purpose": purpose,
        "mutatesState": False,
    }


def compact_entry_points() -> list[dict[str, Any]]:
    return [
        entry_point(
            "explain_fit",
            FIRST_COMMAND,
            "compact_text",
            "Tell an agent whether OPE fits a host prediction goal and which parts the host must bring.",
        ),
        entry_point(
            "capabilities",
            "python3 scripts/ope.py capabilities",
            "json",
            "Emit the machine-readable capability manifest for automated tool selection.",
        ),
        entry_point(
            "adoption_eval",
            "python3 scripts/ope.py adoption-eval",
            "compact_text",
            "Run the first-five-minutes adoption checklist without live network access or writes.",
        ),
        entry_point(
            "implementation_kit",
            "python3 scripts/ope.py agent-implementation-kit --view quickstart",
            "json",
            "Return the checked quickstart sequence for agents embedding OPE in a host project.",
        ),
    ]


def bring_your_own_model() -> dict[str, Any]:
    return {
        "pathStatus": "framework_neutral_checked_guidance",
        "modelFrameworkRequired": False,
        "baselineComparisonRequired": True,
        "leakageChecksRequired": True,
        "qualityClaimBeforeEvidenceAllowed": False,
        "steps": [
            "Define the forecast contract and close/resolution windows before training.",
            "Bind forecast-time features and keep outcome rows resolution-only.",
            "Run or register a baseline before selecting the custom model.",
            "Compare the model against the baseline on comparable resolved outcomes.",
            "Report quality or calibration only after OPE gates show enough evidence.",
        ],
    }


def adoption_check(key: str, command: str, expected: str, blocks: bool = True) -> dict[str, Any]:
    return {
        "checkKey": key,
        "command": command,
        "expected": expected,
        "blocksAdoptionIfMissing": blocks,
    }


def adoption_evaluation() -> dict[str, Any]:
    return {
        "evaluationId": "predictionagentadoptioneval-001",
        "targetMinutes": 5,
        "passesWithoutNetwork": True,
        "writesState": False,
        "checks": [
            adoption_check(
                "understand_fit",
                FIRST_COMMAND,
                "Agent can explain that OPE is the prediction credibility layer, not the full app stack.",
            ),
            adoption_check(
                "find_first_command",
                "python3 scripts/ope.py explain-fit --goal <host prediction goal>",
                "Agent can identify the first command without reading the whole README.",
            ),
            adoption_check(
                "read_capabilities",
                "python3 scripts/ope.py capabilities",
                "Agent can read machine-readable helps-with and does-not-provide lists.",
            ),
            adoption_check(
                "inspect_extension_points",
                "python3 scripts/ope.py explain-fit --view extension-points --output-format json",
                "Agent can find where to plug in sources, methods, resolvers, scorers, and host wrappers.",
            ),
            adoption_check(
                "avoid_overclaiming",
                "python3 scripts/ope.py explain-fit --view boundary --output-format json",
                "Agent can see hosted runtime, trained-model, frontend, and quality-claim boundaries.",
            ),
        ],
    }


def fit_decision() -> dict[str, Any]:
    return {
        "fitStatus": "use_as_prediction_credibility_layer",
        "useOpeFor": ["contracts", "evidence", "baselines", "resolution", "scoring", "calibration_gates"],
        "bringYourOwn": ["frontend", "host_runtime", "data_connectors", "custom_models", "notifications"],
        "recommendedFirstAction": FIRST_COMMAND,
        "claimBoundary": "Use OPE to make predictions auditable; do not claim quality before resolved comparable evidence exists.",
    }


def execution_boundary() -> dict[str, bool]:
    return {
        "readOnlySurface": True,
        "normalChecksOffline": True,
        "createsForecastArtifacts": False,
        "fetchesLiveData": False,
        "startsHostedRuntime": False,
        "storesCredentials": False,
        "storesPrivateRows": False,
        "qualityClaimUpgraded": False,
    }


def build_prediction_agent_adoption() -> dict[str, Any]:
    manifest = capability_manifest()
    extensions = extension_points()
    evaluation = adoption_evaluation()
    return {
        "predictionAgentAdoptionId": "predictionagentadoption-001",
        "generatedAt": GENERATED_AT,
        "surfaceStatus": "general_agent_adoption_ready",
        "capabilityManifest": manifest,
        "fitDecision": fit_decision(),
        "compactEntryPoints": compact_entry_points(),
        "extensionPoints": extensions,
        "bringYourOwnModel": bring_your_own_model(),
        "adoptionEvaluation": evaluation,
        "executionBoundary": execution_boundary(),
        "summary": {
            "primaryValue": "prediction_credibility_layer",
            "firstCommand": FIRST_COMMAND,
            "compactDefaultOutput": True,
            "extensionPointCount": len(extensions),
            "adoptionEvalMinutes": evaluation["targetMinutes"],
            "hostedRuntimeProvided": False,
            "trainedModelProvided": False,
            "frontendProvided": False,
        },
        "warnings": [
            "This surface is an adoption guide, not a new prediction execution path.",
            "OPE remains local and read-only by default; hosted runtime and live effects require separate checked gates.",
            "Bring custom models and app runtime from the host project, then compare them through OPE records.",
        ],
    }


def validate_prediction_agent_adoption(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise PredictionAgentAdoptionError("prediction agent adoption schema validation failed")
    if record["capabilityManifest"]["firstCommand"] != record["summary"]["firstCommand"]:
        raise PredictionAgentAdoptionError("capability manifest and summary first command drifted")
    if record["summary"]["extensionPointCount"] != len(record["extensionPoints"]):
        raise PredictionAgentAdoptionError("extension point count drifted")
    boundary = record["executionBoundary"]
    if not boundary["readOnlySurface"] or not boundary["normalChecksOffline"]:
        raise PredictionAgentAdoptionError("adoption surface must stay read-only and offline")
    blocked = [
        "createsForecastArtifacts",
        "fetchesLiveData",
        "startsHostedRuntime",
        "storesCredentials",
        "storesPrivateRows",
        "qualityClaimUpgraded",
    ]
    if any(boundary[key] for key in blocked):
        raise PredictionAgentAdoptionError("adoption surface must not upgrade runtime or claim boundaries")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "summary":
        return {
            "summary": record["summary"],
            "fitDecision": record["fitDecision"],
            "compactEntryPoints": record["compactEntryPoints"],
            "warnings": record["warnings"],
        }
    if view == "capabilities":
        return record["capabilityManifest"]
    if view == "fit":
        return record["fitDecision"]
    if view == "extension-points":
        return record["extensionPoints"]
    if view == "byo-model":
        return record["bringYourOwnModel"]
    if view == "adoption-eval":
        return record["adoptionEvaluation"]
    if view == "boundary":
        return record["executionBoundary"]
    raise PredictionAgentAdoptionError(f"unsupported view {view}")


def compact_fit_text(record: dict[str, Any], goal: str) -> str:
    fit = record["fitDecision"]
    lines = [
        f"Goal: {goal}",
        "Fit: use OPE as the prediction credibility layer.",
        f"Use OPE for: {', '.join(fit['useOpeFor'])}.",
        f"Bring yourself: {', '.join(fit['bringYourOwn'])}.",
        "First command: python3 scripts/ope.py agent-implementation-kit --view quickstart",
        "Capabilities: python3 scripts/ope.py capabilities",
        "Extension points: source_adapter, forecast_method, resolver, scorer, host_app_wrapper.",
        "Claim boundary: no quality/calibration claim before comparable resolved evidence.",
    ]
    return "\n".join(lines) + "\n"


def compact_eval_text(record: dict[str, Any]) -> str:
    evaluation = record["adoptionEvaluation"]
    checks = ", ".join(item["checkKey"] for item in evaluation["checks"])
    return (
        f"adoptionEval targetMinutes={evaluation['targetMinutes']} "
        f"offline={evaluation['passesWithoutNetwork']} writesState={evaluation['writesState']}\n"
        f"checks={checks}\n"
    )


def write_capabilities(record: dict[str, Any]) -> None:
    CAPABILITIES_PATH.write_text(render_json(record["capabilityManifest"]), encoding="utf-8")


def check_capabilities(record: dict[str, Any]) -> None:
    if not CAPABILITIES_PATH.exists():
        raise PredictionAgentAdoptionError("ope.capabilities.json is missing; run python3 scripts/generate_prediction_agent_adoption.py --write")
    current = json.loads(CAPABILITIES_PATH.read_text(encoding="utf-8"))
    if current != record["capabilityManifest"]:
        raise PredictionAgentAdoptionError("ope.capabilities.json drifted; run python3 scripts/generate_prediction_agent_adoption.py --write")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--view",
        choices=["full", "summary", "capabilities", "fit", "extension-points", "byo-model", "adoption-eval", "boundary"],
        default="full",
        help="print one adoption surface view",
    )
    parser.add_argument("--goal", default="add predictions to my app", help="host prediction goal for compact fit output")
    parser.add_argument("--output-format", choices=["text", "json"], default="json", help="output format")
    parser.add_argument("--check", action="store_true", help="check generated adoption surface and capability manifest drift")
    parser.add_argument("--write", action="store_true", help="refresh generated adoption fixture and root capability manifest")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_prediction_agent_adoption()
    try:
        validate_prediction_agent_adoption(record)
        if args.write:
            write_generated(
                OUTPUT_PATH,
                record,
                label="prediction agent adoption",
                regen="python3 scripts/generate_prediction_agent_adoption.py --write",
            )
            write_capabilities(record)
            return
        if args.check:
            check_generated(
                OUTPUT_PATH,
                record,
                label="prediction agent adoption",
                regen="python3 scripts/generate_prediction_agent_adoption.py --write",
            )
            check_capabilities(record)
            print("checked prediction agent adoption")
            return
        if args.output_format == "text":
            if args.view == "adoption-eval":
                print(compact_eval_text(record), end="")
            else:
                print(compact_fit_text(record, args.goal), end="")
            return
        print(render_json(view_payload(record, args.view)), end="")
    except PredictionAgentAdoptionError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
