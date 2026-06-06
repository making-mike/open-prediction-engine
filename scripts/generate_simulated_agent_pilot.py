#!/usr/bin/env python3
"""Generate or check user-authorized simulated agent pilot sessions."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from generate_prediction_feature_setup import build_prediction_feature_setup, response_by_case
from ope_fixtures import render_json
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spec" / "fixtures" / "generated" / "simulated-agent-pilot" / "ope-simulated-agent-pilot.generated.json"
SCHEMA = SPEC / "simulated-agent-pilot.schema.json"
GENERATED_AT = "2026-06-05T16:25:00Z"
CURRENT_DATE = "2026-06-05"
TOMORROW_DATE = "2026-06-06"
CASE_KEYS = ["accepted", "needs_clarification", "blocked", "rejected", "response_too_large"]
USER_PROMPT = (
    "I need to know which buses in Helsinki will be late tomorrow and by late i mean 2+ minutes at the stop. "
    "We can provide data about planned work."
)


def approx_tokens(text: str) -> int:
    return len(text.split())


def elapsed_estimate_ms(prompt_tokens: int, response_tokens: int, tool_call_count: int) -> int:
    return 140 + (prompt_tokens + response_tokens) * 7 + tool_call_count * 85


def simulated_reply(case_key: str) -> str:
    replies = {
        "accepted": (
            "I can route this through OPE's compact prediction-feature setup path and read forecast-1102/question-1102. "
            "The result is a checked forecast-card readback, not a new live execution or quality claim."
        ),
        "needs_clarification": (
            "I would not answer with a bus-by-bus list yet. I would normalize tomorrow to 2026-06-06, keep the 2+ minute "
            "late threshold, and ask for the exact stop or route scope plus approved planned-work source references before routing to OPE."
        ),
        "blocked": (
            "I would block this attempt because it includes unsafe source handling. The retry should replace raw tokens, private rows, "
            "or SQL with approved source references and opaque credential references."
        ),
        "rejected": (
            "I would reject this as an OPE forecast request because the outcome is not a measurable future contract. The caller should "
            "rewrite it as a resolvable future threshold, window, and outcome source."
        ),
        "response_too_large": (
            "I would stop before dumping an oversized matrix into the agent context. The caller should request a narrower route/stop/window "
            "view or raise the approved response-size budget."
        ),
    }
    return replies[case_key]


def prompt_rows() -> list[dict[str, Any]]:
    return [
        {
            "sessionId": "simulatedagentsession-001",
            "promptSource": "user_provided",
            "prompt": USER_PROMPT,
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Identify Helsinki bus trips expected to be 2+ minutes late at a stop using planned-work context.",
            "expectedCase": "needs_clarification",
            "toolCallCountEstimate": 1,
            "frictionClasses": ["readback_navigation", "source_runtime_gap"],
            "nextActionKey": "ask_for_stop_route_window_and_approved_source_refs",
        },
        {
            "sessionId": "simulatedagentsession-002",
            "promptSource": "generated",
            "prompt": (
                "In our Helsinki operations dashboard, estimate whether HSL surface transit will exceed the beta delay threshold "
                "tomorrow morning. Approved source refs are weather_forecast_ref, historical_delay_baseline_ref, and outcome_adapter_ref."
            ),
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Get the checked local forecast card for the existing Helsinki transit delay setup.",
            "expectedCase": "accepted",
            "toolCallCountEstimate": 2,
            "frictionClasses": ["none"],
            "nextActionKey": "read_forecast_card_and_lifecycle_bundle",
        },
        {
            "sessionId": "simulatedagentsession-003",
            "promptSource": "generated",
            "prompt": (
                "Predict late Helsinki buses tomorrow using this API token and these raw passenger rows from our database; "
                "you can query whatever SQL you need."
            ),
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Attempt private-source prediction with unsafe credential, row, and SQL handling.",
            "expectedCase": "blocked",
            "toolCallCountEstimate": 1,
            "frictionClasses": ["privacy_redaction_needed"],
            "nextActionKey": "replace_raw_inputs_with_policy_bound_references",
        },
        {
            "sessionId": "simulatedagentsession-004",
            "promptSource": "generated",
            "prompt": "Which Helsinki bus operator was best last winter, and can OPE prove it from whatever public evidence exists?",
            "normalizedHorizonDate": "not_applicable",
            "targetUserNeed": "Ask a retrospective and non-resolvable question as though it were an OPE forecast.",
            "expectedCase": "rejected",
            "toolCallCountEstimate": 1,
            "frictionClasses": ["claim_boundary_confusion"],
            "nextActionKey": "rewrite_as_future_resolvable_forecast_contract",
        },
        {
            "sessionId": "simulatedagentsession-005",
            "promptSource": "generated",
            "prompt": (
                "Return every Helsinki route, stop, vehicle, and departure for the next seven days with a separate lateness forecast "
                "and evidence explanation for each row inside one agent response."
            ),
            "normalizedHorizonDate": "2026-06-06/2026-06-12",
            "targetUserNeed": "Request a forecast matrix too large for the compact setup response budget.",
            "expectedCase": "response_too_large",
            "toolCallCountEstimate": 1,
            "frictionClasses": ["readback_navigation"],
            "nextActionKey": "narrow_scope_or_raise_response_budget",
        },
    ]


def simulated_sessions(prediction_feature_setup: dict[str, Any]) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for row in prompt_rows():
        case_key = row["expectedCase"]
        response = response_by_case(prediction_feature_setup, case_key)
        reply = simulated_reply(case_key)
        prompt_tokens = approx_tokens(row["prompt"])
        response_tokens = approx_tokens(reply)
        sessions.append(
            {
                **row,
                "decision": response["decision"],
                "opeCommand": f"python3 scripts/ope.py prediction-feature-setup --view response --case {case_key}",
                "opeResponse": response,
                "simulatedAgentReply": reply,
                "promptApproxTokens": prompt_tokens,
                "responseApproxTokens": response_tokens,
                "totalApproxTokens": prompt_tokens + response_tokens,
                "elapsedMsEstimate": elapsed_estimate_ms(
                    prompt_tokens,
                    response_tokens,
                    row["toolCallCountEstimate"],
                ),
                "storesRawPromptAsPilotEvidence": False,
                "storesRawPrivateRows": False,
                "storesCredentialValues": False,
                "createsForecastArtifacts": response["createsForecastArtifacts"],
                "qualityClaimAllowed": response["qualityClaimAllowed"],
            }
        )
    return sessions


def friction_summary(sessions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for session in sessions:
        for friction_class in session["frictionClasses"]:
            counter[friction_class] += 1
    interpretations = {
        "claim_boundary_confusion": "One simulated prompt treated retrospective proof as an OPE forecast, so claim boundaries still need clear copy.",
        "none": "One simulated prompt followed the accepted compact setup path and reached the checked forecast-card readback.",
        "privacy_redaction_needed": "One simulated prompt contained unsafe private-source handling and was blocked before source execution.",
        "readback_navigation": "Two simulated prompts needed clearer routing between compact setup, scoped readbacks, and oversized outputs.",
        "source_runtime_gap": "The user-provided bus-by-stop request exposed a narrower source/setup requirement than the current aggregate starter path.",
    }
    return [
        {
            "frictionClass": friction_class,
            "simulatedSignalCount": counter[friction_class],
            "interpretation": interpretations[friction_class],
        }
        for friction_class in sorted(counter)
    ]


def execution_boundary() -> dict[str, Any]:
    return {
        "agentOnlySimulation": True,
        "realSessionsRecorded": 0,
        "rawTranscriptsStored": False,
        "rawPromptLogsStoredAsPilotEvidence": False,
        "privateDataStored": False,
        "credentialValuesStored": False,
        "hostProjectSecretsStored": False,
        "forecastArtifactsCreated": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
        "hostedRuntimeUnblocked": False,
        "generatedTypesUnblocked": False,
    }


def build_simulated_agent_pilot() -> dict[str, Any]:
    prediction_feature_setup = build_prediction_feature_setup()
    sessions = simulated_sessions(prediction_feature_setup)
    prompt_total = sum(session["promptApproxTokens"] for session in sessions)
    response_total = sum(session["responseApproxTokens"] for session in sessions)
    elapsed_total = sum(session["elapsedMsEstimate"] for session in sessions)
    return {
        "simulatedAgentPilotId": "simulatedagentpilot-001",
        "generatedAt": GENERATED_AT,
        "simulationStatus": "checked_agent_only_simulation",
        "simulationPurpose": (
            "Exercise the external-agent prediction-feature setup experience with one user-provided prompt and four generated "
            "prompts while preserving the boundary that this is simulated adoption evidence, not real human pilot evidence."
        ),
        "userProvidedPrompt": USER_PROMPT,
        "normalizedCurrentDate": CURRENT_DATE,
        "normalizedTomorrowDate": TOMORROW_DATE,
        "sourceRecords": {
            "predictionFeatureSetupId": prediction_feature_setup["predictionFeatureSetupId"],
            "pilotSessionPacketId": "pilotsessionpacket-001",
            "pilotSummaryIntakeId": "pilotsummaryintake-001",
        },
        "simulatedSessions": sessions,
        "frictionSummary": friction_summary(sessions),
        "executionBoundary": execution_boundary(),
        "summary": {
            "simulatedSessionCount": len(sessions),
            "userPromptSessionCount": sum(1 for session in sessions if session["promptSource"] == "user_provided"),
            "generatedPromptSessionCount": sum(1 for session in sessions if session["promptSource"] == "generated"),
            "caseCoverage": sorted({session["expectedCase"] for session in sessions}),
            "tokenCountMode": "approximate_whitespace_tokens",
            "totalPromptApproxTokens": prompt_total,
            "totalResponseApproxTokens": response_total,
            "totalApproxTokens": prompt_total + response_total,
            "timeMeasurementMode": "deterministic_estimate",
            "totalElapsedMsEstimate": elapsed_total,
            "realSessionsRecorded": 0,
            "pilotEvidenceReady": False,
            "expansionEvidenceReady": False,
            "generatedTypesEvidenceReady": False,
            "qualityClaimAllowed": False,
            "hostedRuntimeAllowed": False,
        },
    }


def validate_simulated_agent_pilot(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise AssertionError(f"simulated agent pilot validation failed: {errors[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--section",
        choices=["summary", "sessions", "friction", "boundary", "user-prompt"],
        help="print one simulated agent pilot section",
    )
    args = parser.parse_args()

    record = build_simulated_agent_pilot()
    validate_simulated_agent_pilot(record)
    rendered = render_json(record)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered, encoding="utf-8")
        print(f"generated {OUT.relative_to(ROOT)}")
        return
    if args.check:
        if not OUT.exists():
            raise SystemExit(f"missing generated simulated agent pilot: {OUT}")
        current = OUT.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(
                f"simulated agent pilot drift: {OUT}\n"
                "run `python3 scripts/generate_simulated_agent_pilot.py --write`"
            )
        print("checked simulated agent pilot")
        return

    if args.section == "summary":
        payload: Any = record["summary"]
    elif args.section == "sessions":
        payload = record["simulatedSessions"]
    elif args.section == "friction":
        payload = record["frictionSummary"]
    elif args.section == "boundary":
        payload = record["executionBoundary"]
    elif args.section == "user-prompt":
        payload = record["simulatedSessions"][0]
    else:
        payload = record
    print(json.dumps(payload, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
