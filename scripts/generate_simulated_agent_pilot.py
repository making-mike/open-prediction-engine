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
OPE_SUPPLIES = [
    "contract",
    "evidence_roles",
    "baseline",
    "forecast_card_shape",
    "resolver",
    "scorer",
    "calibration_gate",
]
HOST_SUPPLIES = ["ui", "sources", "runtime", "notifications", "optional_custom_methods"]


def approx_tokens(text: str) -> int:
    return len(text.split())


def elapsed_estimate_ms(prompt_tokens: int, response_tokens: int, tool_call_count: int) -> int:
    return 140 + (prompt_tokens + response_tokens) * 7 + tool_call_count * 85


def simulated_reply(case_key: str, domain_context: str, confusion_signal: str) -> str:
    if confusion_signal == "parallel_risk_engine_first":
        return (
            "This simulated agent first proposed a separate lightweight risk engine, then corrected course to setup-engine. "
            "Record that as a comprehension gap: OPE should be the first setup readback for contracts, source roles, baseline, resolver, scorer, and calibration gate."
        )
    if confusion_signal == "audit_layer_only":
        return (
            "This simulated agent ran setup-engine but still described OPE as mainly an audit layer. Record the gap: OPE is the engine setup shortcut, while the host supplies UI, sources, runtime, notifications, and optional custom methods."
        )
    if domain_context != "helsinki_transit":
        return (
            "I would start with setup-engine for this host prediction goal, render the candidate contract and source roles, "
            "then ask for missing thresholds or approved sources before any custom model or app-specific method work."
        )
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


def setup_comprehension(confusion_signal: str = "none") -> dict[str, Any]:
    return {
        "usesSetupEngineBeforeCustomEngine": confusion_signal != "parallel_risk_engine_first",
        "customRiskEngineProposedBeforeOpe": confusion_signal == "parallel_risk_engine_first",
        "auditLayerOnlyDescription": confusion_signal == "audit_layer_only",
        "confusionSignal": confusion_signal,
        "opeSupplies": OPE_SUPPLIES,
        "hostSupplies": HOST_SUPPLIES,
    }


def prompt_rows() -> list[dict[str, Any]]:
    return [
        {
            "sessionId": "simulatedagentsession-001",
            "promptSource": "user_provided",
            "domainContext": "helsinki_transit",
            "prompt": USER_PROMPT,
            "setupGoal": "Helsinki stop-level bus lateness risk tomorrow",
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Identify Helsinki bus trips expected to be 2+ minutes late at a stop using planned-work context.",
            "expectedCase": "needs_clarification",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["readback_navigation", "source_runtime_gap"],
            "nextActionKey": "ask_for_stop_route_window_and_approved_source_refs",
        },
        {
            "sessionId": "simulatedagentsession-002",
            "promptSource": "generated",
            "domainContext": "helsinki_transit",
            "prompt": (
                "In our Helsinki operations dashboard, estimate whether HSL surface transit will exceed the beta delay threshold "
                "tomorrow morning. Approved source refs are weather_forecast_ref, historical_delay_baseline_ref, and outcome_adapter_ref."
            ),
            "setupGoal": "Helsinki surface transit delay threshold risk",
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Get the checked local forecast card for the existing Helsinki transit delay setup.",
            "expectedCase": "accepted",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 2,
            "frictionClasses": ["none"],
            "nextActionKey": "read_forecast_card_and_lifecycle_bundle",
        },
        {
            "sessionId": "simulatedagentsession-003",
            "promptSource": "generated",
            "domainContext": "helsinki_transit",
            "prompt": (
                "Predict late Helsinki buses tomorrow using this API token and these raw passenger rows from our database; "
                "you can query whatever SQL you need."
            ),
            "setupGoal": "Helsinki bus lateness risk with unsafe private source inputs",
            "normalizedHorizonDate": TOMORROW_DATE,
            "targetUserNeed": "Attempt private-source prediction with unsafe credential, row, and SQL handling.",
            "expectedCase": "blocked",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["privacy_redaction_needed"],
            "nextActionKey": "replace_raw_inputs_with_policy_bound_references",
        },
        {
            "sessionId": "simulatedagentsession-004",
            "promptSource": "generated",
            "domainContext": "helsinki_transit",
            "prompt": "Which Helsinki bus operator was best last winter, and can OPE prove it from whatever public evidence exists?",
            "setupGoal": "past Helsinki bus operator performance proof",
            "normalizedHorizonDate": "not_applicable",
            "targetUserNeed": "Ask a retrospective and non-resolvable question as though it were an OPE forecast.",
            "expectedCase": "rejected",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["claim_boundary_confusion"],
            "nextActionKey": "rewrite_as_future_resolvable_forecast_contract",
        },
        {
            "sessionId": "simulatedagentsession-005",
            "promptSource": "generated",
            "domainContext": "helsinki_transit",
            "prompt": (
                "Return every Helsinki route, stop, vehicle, and departure for the next seven days with a separate lateness forecast "
                "and evidence explanation for each row inside one agent response."
            ),
            "setupGoal": "oversized Helsinki transit lateness matrix",
            "normalizedHorizonDate": "2026-06-06/2026-06-12",
            "targetUserNeed": "Request a forecast matrix too large for the compact setup response budget.",
            "expectedCase": "response_too_large",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["readback_navigation"],
            "nextActionKey": "narrow_scope_or_raise_response_budget",
        },
        {
            "sessionId": "simulatedagentsession-006",
            "promptSource": "generated",
            "domainContext": "retail_stockout",
            "prompt": (
                "Add a stockout-risk prediction to an inventory dashboard so planners know whether a SKU is likely to hit zero "
                "available units within seven days."
            ),
            "setupGoal": "retail stockout risk within seven days",
            "normalizedHorizonDate": "2026-06-06/2026-06-13",
            "targetUserNeed": "Start a non-Helsinki setup from a retail stockout prediction goal.",
            "expectedCase": "needs_clarification",
            "setupComprehension": setup_comprehension(),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["source_runtime_gap"],
            "nextActionKey": "run_setup_engine_then_request_approved_inventory_sources",
        },
        {
            "sessionId": "simulatedagentsession-007",
            "promptSource": "generated",
            "domainContext": "sla_breach",
            "prompt": (
                "For our support app, should I build a lightweight SLA breach risk engine first and use OPE afterward to audit it?"
            ),
            "setupGoal": "support SLA breach risk for open tickets",
            "normalizedHorizonDate": "future_window_missing",
            "targetUserNeed": "Test whether an agent avoids building a separate SLA risk engine before OPE setup.",
            "expectedCase": "needs_clarification",
            "setupComprehension": setup_comprehension("parallel_risk_engine_first"),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["parallel_risk_engine_confusion", "source_runtime_gap"],
            "nextActionKey": "run_setup_engine_before_custom_sla_method_design",
        },
        {
            "sessionId": "simulatedagentsession-008",
            "promptSource": "generated",
            "domainContext": "seaport_berth_availability",
            "prompt": (
                "We already plan to code berth-availability predictions. Is OPE just the audit framework we attach after the app works?"
            ),
            "setupGoal": "seaport berth availability prediction setup",
            "normalizedHorizonDate": "future_window_missing",
            "targetUserNeed": "Test whether an agent understands OPE as setup shortcut rather than only a post-hoc audit layer.",
            "expectedCase": "rejected",
            "setupComprehension": setup_comprehension("audit_layer_only"),
            "toolCallCountEstimate": 1,
            "frictionClasses": ["audit_layer_only_confusion", "claim_boundary_confusion"],
            "nextActionKey": "explain_engine_setup_shortcut_and_host_responsibility_split",
        },
    ]


def simulated_sessions(prediction_feature_setup: dict[str, Any]) -> list[dict[str, Any]]:
    sessions: list[dict[str, Any]] = []
    for row in prompt_rows():
        case_key = row["expectedCase"]
        response = response_by_case(prediction_feature_setup, case_key)
        reply = simulated_reply(case_key, row["domainContext"], row["setupComprehension"]["confusionSignal"])
        prompt_tokens = approx_tokens(row["prompt"])
        response_tokens = approx_tokens(reply)
        emitted_row = {key: value for key, value in row.items() if key != "setupGoal"}
        sessions.append(
            {
                **emitted_row,
                "decision": response["decision"],
                "setupEngineCommand": f"python3 scripts/ope.py setup-engine --goal {json.dumps(row['setupGoal'])}",
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
        "parallel_risk_engine_confusion": "One non-Helsinki prompt proposed a separate risk engine before setup-engine, so first-command guidance needs validation.",
        "audit_layer_only_confusion": "One non-Helsinki prompt described OPE as post-hoc audit only even after setup-engine entered the flow.",
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
    setup_first_count = sum(
        1 for session in sessions if session["setupComprehension"]["usesSetupEngineBeforeCustomEngine"]
    )
    parallel_count = sum(
        1 for session in sessions if session["setupComprehension"]["customRiskEngineProposedBeforeOpe"]
    )
    audit_count = sum(
        1 for session in sessions if session["setupComprehension"]["auditLayerOnlyDescription"]
    )
    non_helsinki_count = sum(1 for session in sessions if session["domainContext"] != "helsinki_transit")
    setup_first_rate = round(setup_first_count / len(sessions), 4)
    return {
        "simulatedAgentPilotId": "simulatedagentpilot-001",
        "generatedAt": GENERATED_AT,
        "simulationStatus": "checked_agent_only_simulation",
        "simulationPurpose": (
            "Exercise the external-agent prediction-feature setup and setup-engine comprehension experience with one user-provided "
            "prompt and seven generated prompts while preserving the boundary that this is simulated adoption evidence, not real human pilot evidence."
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
            "nonHelsinkiSessionCount": non_helsinki_count,
            "caseCoverage": sorted({session["expectedCase"] for session in sessions}),
            "setupEngineFirstCount": setup_first_count,
            "setupEngineFirstRate": setup_first_rate,
            "parallelRiskEngineProposalCount": parallel_count,
            "auditLayerConfusionCount": audit_count,
            "engineSetupComprehensionReady": non_helsinki_count >= 3 and setup_first_rate >= 0.8,
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
