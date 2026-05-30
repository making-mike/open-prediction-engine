#!/usr/bin/env python3
"""Generate or check the local agent pilot validation pack."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_orchestrator import build_orchestrator
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-pilot-validation"
PILOT_PATH = GENERATED / "ope-agent-pilot-validation.generated.json"
SCHEMA = SPEC / "agent-pilot-validation.schema.json"
GENERATED_AT = "2026-06-10T06:15:00Z"

CASE_ORDER = [
    "local_file_setup_readback",
    "accepted_adapter_output_ready",
    "unsafe_source_block",
    "forecast_run_readback",
    "claim_gate_readback",
]

REQUIRED_DIMENSIONS = [
    "task_completion",
    "forecast_card_comprehension",
    "lifecycle_bundle_comprehension",
    "source_intake_comprehension",
    "blocked_path_comprehension",
    "claim_boundary_comprehension",
    "trust_for_agent_decision_support",
    "setup_friction",
    "runtime_gap_classification",
]


class AgentPilotValidationError(Exception):
    pass


def expected_readback(
    *,
    status_path: str,
    expected_status: str | None,
    forecast_id: str | None,
    question_id: str | None,
    next_action: str | None,
    quality_claim_allowed: bool | None,
    forecast_artifacts_created: bool,
) -> dict[str, Any]:
    return {
        "statusPath": status_path,
        "expectedStatus": expected_status,
        "forecastId": forecast_id,
        "questionId": question_id,
        "nextAction": next_action,
        "qualityClaimAllowed": quality_claim_allowed,
        "forecastArtifactsCreated": forecast_artifacts_created,
    }


def task(
    *,
    index: int,
    scenario_key: str,
    title: str,
    command: str,
    prompt: str,
    outcome_class: str,
    readback: dict[str, Any],
    measures: list[str],
    criteria: list[str],
    interface: str = "cli",
) -> dict[str, Any]:
    return {
        "taskId": f"agentpilottask-{index:03d}",
        "scenarioKey": scenario_key,
        "title": title,
        "interface": interface,
        "command": command,
        "participantPrompt": prompt,
        "expectedOutcomeClass": outcome_class,
        "expectedReadback": readback,
        "measures": measures,
        "successCriteria": criteria,
    }


def build_task_scenarios() -> list[dict[str, Any]]:
    return [
        task(
            index=1,
            scenario_key="local_file_setup_readback",
            title="Approved local-file setup readback",
            command="python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
            prompt="Use the local MVP to inspect an approved local-file setup path. Explain what forecast was produced, how it was scored, and why the quality claim is still blocked.",
            outcome_class="completed_forecast_readback",
            readback=expected_readback(
                status_path="orchestratorStatus",
                expected_status="completed_forecast_readback",
                forecast_id="forecast-1102",
                question_id="question-1102",
                next_action="read_forecast_card",
                quality_claim_allowed=False,
                forecast_artifacts_created=True,
            ),
            measures=[
                "task_completion",
                "forecast_card_comprehension",
                "lifecycle_bundle_comprehension",
                "claim_boundary_comprehension",
                "trust_for_agent_decision_support",
            ],
            criteria=[
                "Participant identifies forecast-1102 and question-1102.",
                "Participant can state that the readback is resolved and scored.",
                "Participant does not convert the scored fixture into a calibration or quality claim.",
            ],
        ),
        task(
            index=2,
            scenario_key="accepted_adapter_output_ready",
            title="Accepted adapter output stops before forecast execution",
            command="python3 scripts/ope.py private-setup-orchestrator --case source_adapter_output_accepted",
            prompt="Inspect the accepted source-adapter-output path. Decide whether forecast artifacts already exist and name the next safe step.",
            outcome_class="ready_for_forecast_execution",
            readback=expected_readback(
                status_path="orchestratorStatus",
                expected_status="ready_for_forecast_execution",
                forecast_id=None,
                question_id=None,
                next_action="run_explicit_setup_forecast_execution",
                quality_claim_allowed=False,
                forecast_artifacts_created=False,
            ),
            measures=[
                "task_completion",
                "source_intake_comprehension",
                "lifecycle_bundle_comprehension",
                "runtime_gap_classification",
            ],
            criteria=[
                "Participant sees source intake and method gate as complete.",
                "Participant explains that explicit setup forecast execution is still required.",
                "Participant does not invent forecast IDs for the ready-but-not-run path.",
            ],
        ),
        task(
            index=3,
            scenario_key="unsafe_source_block",
            title="Unsafe source is stopped before intake",
            command="python3 scripts/ope.py private-setup-orchestrator --case unsafe_source",
            prompt="Inspect the unsafe-source path. Explain why OPE stops and what should happen before any source intake or forecast work.",
            outcome_class="blocked_unsafe",
            readback=expected_readback(
                status_path="orchestratorStatus",
                expected_status="blocked_unsafe",
                forecast_id=None,
                question_id=None,
                next_action="stop_unsafe_connector",
                quality_claim_allowed=False,
                forecast_artifacts_created=False,
            ),
            measures=[
                "task_completion",
                "blocked_path_comprehension",
                "source_intake_comprehension",
                "claim_boundary_comprehension",
            ],
            criteria=[
                "Participant names the unsafe connector boundary.",
                "Participant sees that no source-intake report, forecast, or score is created.",
                "Participant routes to source replacement or safety review rather than repair inside OPE.",
            ],
        ),
        task(
            index=4,
            scenario_key="forecast_run_readback",
            title="Fixture-safe forecast-run readback",
            command="python3 scripts/ope.py forecast-run",
            prompt="Run the fixture-safe forecast-run summary. Explain the produced forecast card, evidence trace, lifecycle bundle, resolution, and scoring bindings.",
            outcome_class="completed_forecast_run",
            readback=expected_readback(
                status_path="runStatus",
                expected_status="completed",
                forecast_id="forecast-602",
                question_id="question-601",
                next_action=None,
                quality_claim_allowed=False,
                forecast_artifacts_created=True,
            ),
            measures=[
                "task_completion",
                "forecast_card_comprehension",
                "lifecycle_bundle_comprehension",
                "trust_for_agent_decision_support",
            ],
            criteria=[
                "Participant identifies the completed forecast-run binding.",
                "Participant can find forecast card, evidence trace, bundle, resolution, and score links.",
                "Participant recognizes the quality claim remains provisional.",
            ],
        ),
        task(
            index=5,
            scenario_key="claim_gate_readback",
            title="Transit claim gate stays below threshold",
            command="python3 scripts/ope.py transit-track-record-gate",
            prompt="Inspect the public transport baseline track-record gate. Decide whether OPE may claim calibration or broad method quality yet.",
            outcome_class="claim_gate_readback",
            readback=expected_readback(
                status_path="claimBoundary.qualityClaimAllowed",
                expected_status="false",
                forecast_id=None,
                question_id=None,
                next_action=None,
                quality_claim_allowed=False,
                forecast_artifacts_created=False,
            ),
            measures=[
                "task_completion",
                "claim_boundary_comprehension",
                "trust_for_agent_decision_support",
                "runtime_gap_classification",
            ],
            criteria=[
                "Participant states that calibration and broad quality claims are blocked.",
                "Participant can separate one scored run from a claim-ready corpus.",
                "Participant names more comparable resolved outcomes as the evidence needed.",
            ],
        ),
    ]


def build_feedback_schema() -> dict[str, Any]:
    questions = {
        "task_completion": ("Could the participant complete the task without moderator correction?", "rating_1_to_5"),
        "forecast_card_comprehension": ("Can the participant explain probability, baseline, resolution, score, and quality-claim fields?", "rating_1_to_5"),
        "lifecycle_bundle_comprehension": ("Can the participant explain the record bindings and provenance trail?", "rating_1_to_5"),
        "source_intake_comprehension": ("Can the participant distinguish accepted, ready, blocked, and rejected source-intake paths?", "rating_1_to_5"),
        "blocked_path_comprehension": ("Can the participant explain why a blocked path creates no forecast artifacts?", "rating_1_to_5"),
        "claim_boundary_comprehension": ("Can the participant state what OPE is not allowed to claim from the local MVP?", "rating_1_to_5"),
        "trust_for_agent_decision_support": ("Would the participant trust this output enough for supervised agent decision support?", "rating_1_to_5"),
        "setup_friction": ("How much friction did the participant encounter while moving from setup to readback?", "rating_1_to_5"),
        "runtime_gap_classification": ("Was the issue a usability gap, a missing runtime feature, a data gap, or no issue?", "short_text"),
    }
    return {
        "feedbackSchemaId": "agentpilotfeedback-001",
        "ratingScale": {
            "minimumScore": 1,
            "maximumScore": 5,
            "anchors": [
                "1 means blocked or misunderstood.",
                "3 means completed with notable help or uncertainty.",
                "5 means completed independently with correct claim-boundary understanding.",
            ],
        },
        "dimensions": [
            {
                "dimensionId": dimension,
                "question": question,
                "responseType": response_type,
                "required": True,
            }
            for dimension, (question, response_type) in questions.items()
        ],
    }


def build_rubric() -> list[dict[str, Any]]:
    return [
        {
            "rubricId": "agentpilotrubric-001",
            "surface": "forecast_card",
            "passingScore": 4,
            "taskRefs": ["agentpilottask-001", "agentpilottask-004"],
            "passingSignals": [
                "Identifies forecast ID, question ID, probability, baseline, resolution status, and score status.",
                "Explains that a forecast card is compact readback, not the full provenance trail.",
                "Notices quality claim status before recommending agent use.",
            ],
            "failureSignals": [
                "Treats the probability as deterministic advice.",
                "Misses the baseline or quality-claim status.",
            ],
        },
        {
            "rubricId": "agentpilotrubric-002",
            "surface": "lifecycle_bundle",
            "passingScore": 4,
            "taskRefs": ["agentpilottask-001", "agentpilottask-002", "agentpilottask-004"],
            "passingSignals": [
                "Can name the linked source, method, forecast, resolution, and scoring records.",
                "Understands that accepted adapter output still needs explicit forecast execution before readback.",
                "Separates generated read surfaces from private source data.",
            ],
            "failureSignals": [
                "Assumes every accepted source path already has a lifecycle bundle.",
                "Cannot distinguish readback records from execution steps.",
            ],
        },
        {
            "rubricId": "agentpilotrubric-003",
            "surface": "source_intake",
            "passingScore": 4,
            "taskRefs": ["agentpilottask-002", "agentpilottask-003"],
            "passingSignals": [
                "Explains accepted, needs-confirmation, insufficient-data, rejected, and unsafe outcomes.",
                "Keeps source intake as a pre-forecast gate.",
                "Does not let adapter output bypass mapping, provenance, or method-gate checks.",
            ],
            "failureSignals": [
                "Lets accepted adapter output create forecasts directly.",
                "Tries to repair unsafe connector output inside OPE.",
            ],
        },
        {
            "rubricId": "agentpilotrubric-004",
            "surface": "blocked_path",
            "passingScore": 4,
            "taskRefs": ["agentpilottask-002", "agentpilottask-003"],
            "passingSignals": [
                "Can state the blocked reason and the next safe action.",
                "Confirms no forecast, resolution, or scoring artifacts were created.",
                "Distinguishes usability confusion from a missing runtime feature.",
            ],
            "failureSignals": [
                "Reads a blocked path as a failed forecast.",
                "Asks OPE to fetch private data or store credentials to continue.",
            ],
        },
        {
            "rubricId": "agentpilotrubric-005",
            "surface": "claim_boundary",
            "passingScore": 4,
            "taskRefs": ["agentpilottask-001", "agentpilottask-003", "agentpilottask-005"],
            "passingSignals": [
                "States that one scored fixture is not calibration evidence.",
                "Explains sample-size, comparable-outcome, and live-source boundaries.",
                "Keeps public transport method quality claims blocked below threshold.",
            ],
            "failureSignals": [
                "Turns local fixture success into a production or quality claim.",
                "Treats live connector availability as live calibration.",
            ],
        },
    ]


def rating(dimension_id: str, score: int) -> dict[str, Any]:
    return {"dimensionId": dimension_id, "score": score}


def build_example_summaries() -> list[dict[str, Any]]:
    return [
        {
            "exampleId": "agentpilotexample-001",
            "taskId": "agentpilottask-001",
            "participantType": "agent_developer",
            "isSyntheticExample": True,
            "rawTranscriptStored": False,
            "privateDataStored": False,
            "sanitizedSummary": "Synthetic participant completed the local-file readback, identified forecast-1102, and correctly kept the quality claim blocked after seeing the scored fixture.",
            "observedSignals": [
                "Found forecast and question bindings without file browsing.",
                "Explained score status and quality claim status separately.",
            ],
            "ratings": [
                rating("task_completion", 5),
                rating("forecast_card_comprehension", 5),
                rating("claim_boundary_comprehension", 5),
                rating("trust_for_agent_decision_support", 4),
            ],
            "followUpClassification": "passed",
        },
        {
            "exampleId": "agentpilotexample-002",
            "taskId": "agentpilottask-002",
            "participantType": "supervising_developer",
            "isSyntheticExample": True,
            "rawTranscriptStored": False,
            "privateDataStored": False,
            "sanitizedSummary": "Synthetic participant understood the accepted adapter output was source-intake ready, but first expected a forecast ID until the explicit forecast-execution gate was pointed out.",
            "observedSignals": [
                "Classified the issue as a comprehension gap, not a missing connector runtime.",
                "After correction, named run_explicit_setup_forecast_execution as the next action.",
            ],
            "ratings": [
                rating("task_completion", 4),
                rating("source_intake_comprehension", 4),
                rating("lifecycle_bundle_comprehension", 3),
                rating("runtime_gap_classification", 4),
            ],
            "followUpClassification": "usability_gap",
        },
        {
            "exampleId": "agentpilotexample-003",
            "taskId": "agentpilottask-003",
            "participantType": "agent_developer",
            "isSyntheticExample": True,
            "rawTranscriptStored": False,
            "privateDataStored": False,
            "sanitizedSummary": "Synthetic participant stopped at the unsafe source boundary and correctly refused to route unsafe connector output into source intake or forecast execution.",
            "observedSignals": [
                "Named stop_unsafe_connector as the safe next action.",
                "Confirmed no source-intake, forecast, or scoring artifacts should exist.",
            ],
            "ratings": [
                rating("task_completion", 5),
                rating("blocked_path_comprehension", 5),
                rating("source_intake_comprehension", 5),
                rating("claim_boundary_comprehension", 5),
            ],
            "followUpClassification": "passed",
        },
    ]


def build_agent_pilot_validation() -> dict[str, Any]:
    manifest = build_manifest()
    orchestrator = build_orchestrator()
    pack = {
        "agentPilotValidationId": "agentpilotvalidation-001",
        "generatedAt": GENERATED_AT,
        "scope": "local_mvp_validation",
        "runtimeStatus": "checked_pilot_protocol_only",
        "bindings": {
            "mvpRunbookPath": manifest["mvpLocalRuntime"]["runbookPath"],
            "releaseManifestId": manifest["releaseManifestId"],
            "privateSetupOrchestratorId": orchestrator["privateSetupOrchestratorId"],
            "forecastRunCommand": "python3 scripts/ope.py forecast-run",
            "claimGateCommand": "python3 scripts/ope.py transit-track-record-gate",
        },
        "pilotProtocol": {
            "protocolId": "agentpilotprotocol-001",
            "minimumSessions": 3,
            "targetSessions": 5,
            "participantProfiles": [
                "Agent developer integrating an OPE-compatible forecasting loop.",
                "Supervising developer deciding whether an agent can use OPE output for decision support.",
            ],
            "sessionLengthMinutes": 45,
            "setupMode": "moderated_local_cli",
            "moderationSteps": [
                "Start with the local MVP runbook and no product explanation beyond repository docs.",
                "Ask the participant to complete task scenarios using CLI output or agent-call readbacks.",
                "Ask the participant to explain source, forecast, resolution, scoring, and claim-boundary fields aloud.",
                "Record only sanitized notes, dimension scores, and follow-up classification.",
                "Separate usability confusion from missing runtime capability before changing the roadmap.",
            ],
            "privacyBoundary": {
                "storesRawTranscripts": False,
                "storesPrivateData": False,
                "storesCredentials": False,
                "storesPromptLogs": False,
                "requiresSanitizedSummaries": True,
                "usesSyntheticExamplesOnly": True,
            },
        },
        "taskScenarios": build_task_scenarios(),
        "feedbackSchema": build_feedback_schema(),
        "comprehensionRubric": build_rubric(),
        "examplePilotSummaries": build_example_summaries(),
        "successMetrics": {
            "minimumSessions": 3,
            "targetSessions": 5,
            "minimumTaskCompletionRate": 0.8,
            "minimumMedianTrustScore": 4,
            "minimumClaimBoundaryMedianScore": 4,
            "usabilityGapReviewThreshold": 3,
        },
        "decisionRules": [
            {
                "decisionRuleId": "agentpilotdecision-001",
                "signal": "Task completion and claim-boundary scores meet thresholds with no repeated confusion.",
                "decision": "continue_mvp_validation",
                "nextAction": "Run more sessions or proceed to local usage and trace events.",
            },
            {
                "decisionRuleId": "agentpilotdecision-002",
                "signal": "Participants complete tasks but misunderstand forecast card, lifecycle bundle, or blocked path semantics.",
                "decision": "fix_comprehension_gap",
                "nextAction": "Improve read surfaces, labels, examples, or runbook wording before adding runtime scope.",
            },
            {
                "decisionRuleId": "agentpilotdecision-003",
                "signal": "Participants understand the surfaces but cannot finish because an explicitly planned runtime is missing.",
                "decision": "prioritize_runtime_gap",
                "nextAction": "Use pilot notes to rank local usage events, corpus growth, source quality, or narrow real-source runtime work.",
            },
            {
                "decisionRuleId": "agentpilotdecision-004",
                "signal": "Any participant reads scored fixture output as calibration, production readiness, or broad quality proof.",
                "decision": "pause_quality_claims",
                "nextAction": "Tighten claim-boundary copy and gates before publishing stronger MVP messaging.",
            },
        ],
        "executionBoundary": {
            "runsPilotSessions": False,
            "recruitsParticipants": False,
            "recordsRawTranscripts": False,
            "storesPrivateData": False,
            "storesCredentials": False,
            "createsForecastArtifacts": False,
            "claimsForecastQuality": False,
            "usesExistingCheckedFixturesOnly": True,
            "storesSyntheticExamplesOnly": True,
        },
        "warnings": [
            "The pilot validation pack is a checked protocol and rubric; it does not run sessions or collect telemetry.",
            "Example pilot summaries are synthetic and sanitized; do not replace them with raw private transcripts.",
            "Pilot success may support usability confidence, but it is not calibration or broad forecast-quality evidence.",
            "Missing arbitrary private API/database parsing should be classified as runtime scope, not hidden MVP failure.",
        ],
    }
    validate_agent_pilot_validation(pack)
    return pack


def validate_agent_pilot_validation(pack: dict[str, Any]) -> None:
    errors = validate_record(pack, SCHEMA)
    if errors:
        raise AgentPilotValidationError(f"agent pilot validation schema validation failed: {errors[0]}")
    scenarios = {scenario["scenarioKey"]: scenario for scenario in pack["taskScenarios"]}
    if list(scenarios) != CASE_ORDER:
        raise AgentPilotValidationError("agent pilot task scenario coverage drifted")
    dimensions = [dimension["dimensionId"] for dimension in pack["feedbackSchema"]["dimensions"]]
    if dimensions != REQUIRED_DIMENSIONS:
        raise AgentPilotValidationError("agent pilot feedback dimensions drifted")
    protocol_boundary = pack["pilotProtocol"]["privacyBoundary"]
    for key in ("storesRawTranscripts", "storesPrivateData", "storesCredentials", "storesPromptLogs"):
        if protocol_boundary[key] is not False:
            raise AgentPilotValidationError(f"privacy boundary {key} should be false")
    if protocol_boundary["requiresSanitizedSummaries"] is not True:
        raise AgentPilotValidationError("pilot protocol should require sanitized summaries")
    if protocol_boundary["usesSyntheticExamplesOnly"] is not True:
        raise AgentPilotValidationError("checked examples should remain synthetic")
    execution_boundary = pack["executionBoundary"]
    for key, value in execution_boundary.items():
        if key in {"usesExistingCheckedFixturesOnly", "storesSyntheticExamplesOnly"}:
            if value is not True:
                raise AgentPilotValidationError(f"execution boundary {key} should be true")
        elif value is not False:
            raise AgentPilotValidationError(f"execution boundary {key} should be false")
    for summary in pack["examplePilotSummaries"]:
        if summary["isSyntheticExample"] is not True:
            raise AgentPilotValidationError("example summaries should remain synthetic")
        if summary["rawTranscriptStored"] is not False:
            raise AgentPilotValidationError("raw transcripts must not be stored")
        if summary["privateDataStored"] is not False:
            raise AgentPilotValidationError("private data must not be stored")
    rubric_surfaces = {item["surface"] for item in pack["comprehensionRubric"]}
    if rubric_surfaces != {"forecast_card", "lifecycle_bundle", "source_intake", "blocked_path", "claim_boundary"}:
        raise AgentPilotValidationError("pilot rubric surface coverage drifted")


def summary(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "agentPilotValidationId": pack["agentPilotValidationId"],
        "minimumSessions": pack["pilotProtocol"]["minimumSessions"],
        "targetSessions": pack["pilotProtocol"]["targetSessions"],
        "taskCount": len(pack["taskScenarios"]),
        "taskScenarios": [
            {
                "scenarioKey": scenario["scenarioKey"],
                "command": scenario["command"],
                "expectedOutcomeClass": scenario["expectedOutcomeClass"],
            }
            for scenario in pack["taskScenarios"]
        ],
        "feedbackDimensions": [
            dimension["dimensionId"]
            for dimension in pack["feedbackSchema"]["dimensions"]
        ],
        "exampleSummaryCount": len(pack["examplePilotSummaries"]),
    }


def write_pack(pack: dict[str, Any]) -> None:
    write_generated(PILOT_PATH, pack, label="agent pilot validation pack", regen="python3 scripts/generate_agent_pilot_validation.py --write")


def check_pack(pack: dict[str, Any]) -> None:
    check_generated(PILOT_PATH, pack, label="agent pilot validation pack", regen="python3 scripts/generate_agent_pilot_validation.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one pilot task scenario")
    parser.add_argument("--check", action="store_true", help="check generated pilot validation pack drift")
    parser.add_argument("--write", action="store_true", help="write generated pilot validation pack")
    args = parser.parse_args()
    try:
        pack = build_agent_pilot_validation()
    except AgentPilotValidationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_pack(pack)
    elif args.check:
        check_pack(pack)
    elif args.case:
        scenario = next(item for item in pack["taskScenarios"] if item["scenarioKey"] == args.case)
        sys.stdout.write(render_json(scenario))
    else:
        sys.stdout.write(render_json(summary(pack)))


if __name__ == "__main__":
    main()
