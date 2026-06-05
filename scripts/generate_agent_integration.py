#!/usr/bin/env python3
"""Generate or check the agent incorporation golden-path readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-integration"
OUTPUT_PATH = GENERATED / "ope-agent-integration.generated.json"
SCHEMA = SPEC / "agent-integration.schema.json"
GENERATED_AT = "2026-06-11T09:30:00Z"
SCENARIOS = ["helsinki_bus_disruption"]
VIEWS = [
    "full",
    "summary",
    "intake",
    "candidates",
    "validation",
    "commands",
    "blocked",
    "boundary",
    "efficiency",
]
SOURCE_ROLES = [
    "weather_forecast",
    "historical_delay_baseline",
    "transit_delay_outcome",
]
REQUIRED_MCP_TOOLS = [
    "ope_agent_integration_readiness",
    "ope_agent_integration_candidates",
    "ope_agent_integration_guided_forecast",
]
GUIDED_CASES = [
    "accepted_adapter_output",
    "missing_weather_source",
    "missing_baseline_source",
    "missing_outcome_source",
    "ambiguous_service_window",
    "vague_geography",
    "missing_resolution_source",
    "unapproved_source",
    "raw_credential_value",
    "raw_sql_query",
    "unsafe_adapter_output",
    "private_row_exposure",
    "post_outcome_evidence",
]


class AgentIntegrationError(Exception):
    pass


def intake_field(field_name: str, field_type: str, purpose: str) -> dict[str, Any]:
    return {
        "fieldName": field_name,
        "fieldType": field_type,
        "purpose": purpose,
        "required": True,
        "credentialValueAllowed": False,
        "rawPrivateRowsAllowed": False,
    }


def build_intake() -> dict[str, Any]:
    return {
        "intakeContractId": "agentintegrationintake-001",
        "appIntent": "A Helsinki bus and tram traffic app wants to attach approved context sources and ask OPE what disruption outcomes can be forecasted.",
        "decisionToSupport": "Prioritize warnings, dispatch attention, and rider-facing disruption explanations before a future morning peak window.",
        "requiredFields": [
            intake_field("appIntent", "string", "Host app goal and decision under uncertainty."),
            intake_field("candidateQuestion", "string", "Future-facing question or question family to normalize."),
            intake_field("serviceArea", "string", "Bounded geography such as HSL surface transit in Helsinki."),
            intake_field("serviceWindow", "string", "Specific future window such as morning peak."),
            intake_field("threshold", "string", "Declared beta delay threshold or setup-specific threshold."),
            intake_field("approvedSourceRefs", "array", "Caller-approved file refs or sanitized adapter outputs."),
            intake_field("sourceRoles", "array", "Forecast-time, historical-baseline, and resolution-only roles."),
            intake_field("resolutionSource", "string", "Outcome source usable only after the outcome window closes."),
        ],
        "approvedSourceContext": [
            "Use existing domain configs for transit disruption and weather-transit delay setup fields.",
            "Use existing source-binding readbacks for role and policy checks.",
            "Use approved local files and sanitized source-adapter outputs only.",
        ],
        "forbiddenInputs": [
            "raw credential values",
            "raw SQL strings",
            "raw private source rows",
            "unapproved live fetches",
            "post-outcome evidence as forecast-time evidence",
        ],
        "normalizesToExistingSurfaces": True,
        "createsForecastArtifacts": False,
    }


def source_role(
    role_key: str,
    source_kind: str,
    purpose: str,
    forecast_time_allowed: bool,
    resolution_only: bool,
    required_fields: list[str],
) -> dict[str, Any]:
    return {
        "roleKey": role_key,
        "sourceKind": source_kind,
        "purpose": purpose,
        "required": True,
        "forecastTimeAllowed": forecast_time_allowed,
        "resolutionOnly": resolution_only,
        "approvedInputKinds": ["approved_local_file", "sanitized_adapter_output"],
        "requiredFields": required_fields,
    }


def source_readiness(role_key: str, status: str, missing_fields: list[str], blocker: str) -> dict[str, Any]:
    return {
        "roleKey": role_key,
        "readinessStatus": status,
        "missingFields": missing_fields,
        "blockerCode": blocker,
    }


def required_source_field(role_key: str, field_name: str, purpose: str) -> dict[str, Any]:
    return {
        "roleKey": role_key,
        "fieldName": field_name,
        "purpose": purpose,
    }


def blocker(blocker_code: str, source_role_key: str, message: str, next_action: str) -> dict[str, Any]:
    return {
        "blockerCode": blocker_code,
        "sourceRole": source_role_key,
        "message": message,
        "nextAction": next_action,
    }


def build_starter_pack() -> dict[str, Any]:
    return {
        "starterPackId": "helsinkistarterpack-001",
        "domainKey": "weather-transit-delays",
        "sourceRoles": [
            source_role(
                "weather_forecast",
                "source_adapter_output",
                "Forecast-time weather conditions that may affect surface transit delays.",
                True,
                False,
                ["valid_time", "temperature_c", "precipitation_mm", "wind_speed_mps"],
            ),
            source_role(
                "historical_delay_baseline",
                "approved_local_file",
                "Comparable historical delay rows used for the baseline-first method gate.",
                True,
                False,
                ["service_date", "route_family", "service_window", "delay_minutes"],
            ),
            source_role(
                "transit_delay_outcome",
                "sanitized_adapter_output",
                "HSL outcome rows used only after the outcome window closes.",
                False,
                True,
                ["service_date", "service_window", "surface_transit_delay_minutes", "outcome_observed_at"],
            ),
        ],
        "sourceReadiness": [
            source_readiness("weather_forecast", "ready", [], "none"),
            source_readiness("historical_delay_baseline", "ready", [], "none"),
            source_readiness("transit_delay_outcome", "ready_resolution_only", [], "none"),
        ],
        "requiredFields": [
            required_source_field("weather_forecast", "valid_time", "Forecast-time weather validity timestamp."),
            required_source_field("weather_forecast", "precipitation_mm", "Weather disruption feature."),
            required_source_field("weather_forecast", "wind_speed_mps", "Weather disruption feature."),
            required_source_field("historical_delay_baseline", "service_date", "Historical baseline date."),
            required_source_field("historical_delay_baseline", "service_window", "Comparable peak-window label."),
            required_source_field("historical_delay_baseline", "delay_minutes", "Comparable delay outcome value."),
            required_source_field("transit_delay_outcome", "surface_transit_delay_minutes", "Resolution outcome value."),
            required_source_field("transit_delay_outcome", "outcome_observed_at", "Resolution observation timestamp."),
        ],
        "missingFieldBlockers": [
            blocker(
                "missing_weather_source",
                "weather_forecast",
                "Weather forecast role is required before a weather-sensitive disruption candidate is forecastable.",
                "Attach an approved weather forecast file or sanitized adapter output.",
            ),
            blocker(
                "missing_baseline_source",
                "historical_delay_baseline",
                "Historical comparable delay rows are required for the baseline-first method boundary.",
                "Attach an approved baseline file with service_date, service_window, and delay_minutes.",
            ),
            blocker(
                "missing_outcome_source",
                "transit_delay_outcome",
                "A resolution-only HSL outcome source is required before the question is forecastable.",
                "Attach sanitized outcome adapter output and keep it resolution-only.",
            ),
        ],
        "resolutionBoundary": {
            "outcomeEvidenceResolutionOnly": True,
            "forecastTimeOutcomeRowsAllowed": False,
            "usesApprovedFilesAndSanitizedAdaptersOnly": True,
        },
    }


def candidate(
    index: int,
    case_key: str,
    status: str,
    question_text: str,
    reason_codes: list[str],
    next_action: str,
    *,
    service_area: str = "HSL surface transit in Helsinki",
    service_window: str = "morning peak",
    threshold: str = "beta delay threshold",
) -> dict[str, Any]:
    return {
        "candidateId": f"agentcandidate-{index:03d}",
        "caseKey": case_key,
        "status": status,
        "questionText": question_text,
        "outputType": "binary",
        "serviceArea": service_area,
        "serviceWindow": service_window,
        "threshold": threshold,
        "closeTimePolicy": "Forecast must be created before the service window begins.",
        "resolveTimePolicy": "Resolve only after the service window closes and HSL outcome rows are available.",
        "sourceRoles": SOURCE_ROLES,
        "reasonCodes": reason_codes,
        "nextAction": next_action,
        "routesToExistingSurfaces": status == "forecastable",
        "forecastArtifactsAllowed": status == "forecastable",
    }


def build_candidates() -> list[dict[str, Any]]:
    return [
        candidate(
            1,
            "helsinki_surface_transit_peak_delay",
            "forecastable",
            "Will HSL surface transit exceed the beta delay threshold during morning peak on {service_date}?",
            ["candidate_validated"],
            "Run the guided path from accepted sanitized adapter output, then read the forecast card.",
        ),
        candidate(
            2,
            "vague_next_week_transit",
            "needs_clarification",
            "Will transit be bad next week?",
            ["missing_threshold", "ambiguous_service_window", "vague_geography"],
            "Ask the caller for service area, threshold, and a specific future service window.",
            service_area="vague",
            service_window="next week",
            threshold="missing",
        ),
        candidate(
            3,
            "missing_threshold",
            "needs_clarification",
            "Will Helsinki bus traffic be disrupted tomorrow morning?",
            ["missing_threshold"],
            "Ask for the disruption threshold or bind the beta delay threshold.",
            threshold="missing",
        ),
        candidate(
            4,
            "missing_resolution_source",
            "needs_clarification",
            "Will HSL surface transit exceed the beta delay threshold during morning peak?",
            ["missing_resolution_source"],
            "Bind a resolution-only HSL outcome source before accepting the candidate.",
        ),
        candidate(
            5,
            "unapproved_source",
            "blocked",
            "Will HSL delays exceed threshold using an unapproved web scrape?",
            ["unapproved_source"],
            "Replace the source with an approved file or sanitized adapter output.",
        ),
        candidate(
            6,
            "raw_credential_value",
            "blocked",
            "Will HSL delays exceed threshold using this raw API token?",
            ["raw_credential_value"],
            "Replace credential material with a caller-owned credential reference outside prompt-visible records.",
        ),
        candidate(
            7,
            "raw_sql_query",
            "blocked",
            "Will HSL delays exceed threshold using this raw SQL query?",
            ["raw_sql_query"],
            "Use a checked adapter output or future query-manifest contract instead of raw SQL.",
        ),
        candidate(
            8,
            "unsafe_adapter_output",
            "blocked",
            "Will HSL delays exceed threshold from an adapter output with failed sanitization?",
            ["unsafe_adapter_output"],
            "Sanitize and validate the adapter output before intake.",
        ),
        candidate(
            9,
            "private_row_exposure",
            "blocked",
            "Will this specific passenger-linked transit row predict a disruption?",
            ["private_row_exposure"],
            "Use aggregate or sanitized source rows; do not expose raw private rows.",
        ),
        candidate(
            10,
            "post_outcome_evidence",
            "blocked",
            "Will HSL delays exceed threshold using outcome rows captured after the service window?",
            ["post_outcome_evidence"],
            "Keep outcome rows resolution-only and exclude them from forecast-time evidence.",
        ),
        candidate(
            11,
            "past_tense_transit_delay",
            "rejected",
            "Did HSL surface transit exceed the beta delay threshold yesterday morning?",
            ["past_tense_question"],
            "Use resolution or historical analysis surfaces, not forecast creation.",
        ),
        candidate(
            12,
            "unresolvable_outcome",
            "rejected",
            "Will Helsinki transit feel frustrating?",
            ["unresolvable_outcome"],
            "Rewrite as a measurable future outcome with a declared source and threshold.",
        ),
    ]


VALIDATION_CHECKS = [
    "future_boundary",
    "resolvability",
    "source_policy",
    "source_roles",
    "leakage",
    "baseline_feasibility",
    "claim_boundary",
]


def validation_check(check_key: str, result: str, reason_code: str) -> dict[str, Any]:
    return {
        "checkKey": check_key,
        "result": result,
        "reasonCode": reason_code,
        "message": f"{check_key} returned {result} with reason code {reason_code}.",
    }


def checks_for_candidate(item: dict[str, Any]) -> list[dict[str, Any]]:
    if item["status"] == "forecastable":
        return [validation_check(check, "passed", "candidate_validated") for check in VALIDATION_CHECKS]

    reason = item["reasonCodes"][0]
    results = {check: "passed" for check in VALIDATION_CHECKS}
    if item["status"] == "needs_clarification":
        results["resolvability"] = "needs_clarification"
        if "missing_resolution_source" in item["reasonCodes"]:
            results["source_roles"] = "needs_clarification"
    elif item["status"] == "blocked":
        results["source_policy"] = "blocked"
        if reason in {"raw_credential_value", "raw_sql_query", "unsafe_adapter_output", "private_row_exposure", "post_outcome_evidence"}:
            results["leakage"] = "blocked"
        if reason == "post_outcome_evidence":
            results["future_boundary"] = "blocked"
    else:
        results["future_boundary"] = "rejected" if reason == "past_tense_question" else "passed"
        results["resolvability"] = "rejected"
        results["baseline_feasibility"] = "rejected"

    return [
        validation_check(check, results[check], reason)
        for check in VALIDATION_CHECKS
    ]


def build_validation_reports(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "validationReportId": f"agentintegrationvalidation-{index:03d}",
            "candidateCaseKey": item["caseKey"],
            "status": item["status"],
            "checks": checks_for_candidate(item),
            "exactReasonCodes": item["reasonCodes"],
            "forecastArtifactsAllowed": item["forecastArtifactsAllowed"],
        }
        for index, item in enumerate(candidates, start=1)
    ]


def guided_case(
    index: int,
    case_key: str,
    status: str,
    blocker_codes: list[str],
    next_action: str,
    *,
    tool_call_count: int = 1,
    forecast_id: str | None = None,
    question_id: str | None = None,
) -> dict[str, Any]:
    ready = status == "forecast_card_ready"
    return {
        "guidedCaseId": f"guidedforecastcase-{index:03d}",
        "caseKey": case_key,
        "guidedStatus": status,
        "toolCallCount": tool_call_count,
        "forecastId": forecast_id,
        "questionId": question_id,
        "forecastCardCommand": (
            f"python3 scripts/ope.py read --record-type forecast-card --id {forecast_id} --question-id {question_id}"
            if ready and forecast_id and question_id
            else None
        ),
        "lifecycleBundleCommand": (
            f"python3 scripts/ope.py read --record-type forecast-bundle --id {forecast_id} --question-id {question_id}"
            if ready and forecast_id and question_id
            else None
        ),
        "nextAction": next_action,
        "blockerCodes": blocker_codes,
        "createsForecastArtifacts": False,
        "qualityClaimAllowed": False,
        "claimBoundary": "Baseline-first readback only; no quality or calibration claim is upgraded by agent integration.",
    }


def build_guided_cases() -> list[dict[str, Any]]:
    return [
        guided_case(
            1,
            "accepted_adapter_output",
            "forecast_card_ready",
            [],
            "Read the forecast card command returned by this payload, then inspect the lifecycle bundle if needed.",
            tool_call_count=3,
            forecast_id="forecast-1102",
            question_id="question-1102",
        ),
        guided_case(
            2,
            "missing_weather_source",
            "blocked",
            ["missing_weather_source"],
            "Attach weather_forecast source role before running guided forecast.",
        ),
        guided_case(
            3,
            "missing_baseline_source",
            "blocked",
            ["missing_baseline_source"],
            "Attach historical_delay_baseline source role before running guided forecast.",
        ),
        guided_case(
            4,
            "missing_outcome_source",
            "blocked",
            ["missing_outcome_source"],
            "Attach transit_delay_outcome role as resolution-only evidence.",
        ),
        guided_case(
            5,
            "ambiguous_service_window",
            "blocked",
            ["ambiguous_service_window"],
            "Clarify the service window before guided forecast execution.",
        ),
        guided_case(
            6,
            "vague_geography",
            "blocked",
            ["vague_geography"],
            "Clarify the geography before guided forecast execution.",
        ),
        guided_case(
            7,
            "missing_resolution_source",
            "blocked",
            ["missing_resolution_source"],
            "Bind a resolution source before guided forecast execution.",
        ),
        guided_case(
            8,
            "unapproved_source",
            "blocked",
            ["unapproved_source"],
            "Replace the source with an approved file or sanitized adapter output.",
        ),
        guided_case(
            9,
            "raw_credential_value",
            "blocked",
            ["raw_credential_value"],
            "Remove raw credentials and use caller-owned credential references outside OPE records.",
        ),
        guided_case(
            10,
            "raw_sql_query",
            "blocked",
            ["raw_sql_query"],
            "Use a checked adapter output instead of raw SQL.",
        ),
        guided_case(
            11,
            "unsafe_adapter_output",
            "blocked",
            ["unsafe_adapter_output"],
            "Regenerate the adapter output with the checked sanitized schema.",
        ),
        guided_case(
            12,
            "private_row_exposure",
            "blocked",
            ["private_row_exposure"],
            "Remove raw private rows from prompt-visible records.",
        ),
        guided_case(
            13,
            "post_outcome_evidence",
            "blocked",
            ["post_outcome_evidence"],
            "Keep outcome rows resolution-only and rerun candidate validation.",
        ),
    ]


def command(command_key: str, text: str, purpose: str, routine: bool) -> dict[str, Any]:
    return {
        "commandKey": command_key,
        "command": text,
        "purpose": purpose,
        "routineToolCall": routine,
    }


def build_commands() -> list[dict[str, Any]]:
    return [
        command(
            "readiness",
            "python3 scripts/ope.py agent-integrate --scenario helsinki_bus_disruption --view summary",
            "Check whether the starter pack is ready for agent incorporation.",
            True,
        ),
        command(
            "candidates",
            "python3 scripts/ope.py agent-integrate --view candidates",
            "Return forecastable and non-forecastable candidate contracts with reason codes.",
            True,
        ),
        command(
            "validation",
            "python3 scripts/ope.py agent-integrate --view validation",
            "Return mechanical validation reports for each candidate.",
            True,
        ),
        command(
            "guided_forecast",
            "python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output",
            "Return the first forecast-card command from accepted source context.",
            True,
        ),
        command(
            "forecast_card",
            "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "Read the compact forecast card returned by the guided case.",
            True,
        ),
        command(
            "lifecycle_bundle",
            "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
            "Inspect the lifecycle bundle after the card read.",
            False,
        ),
    ]


def mcp_tool(tool_name: str, cli_command: str, returns: str) -> dict[str, Any]:
    return {
        "toolName": tool_name,
        "equivalentCliCommand": cli_command,
        "returns": returns,
        "createsForecastArtifacts": False,
    }


def build_mcp_tools() -> list[dict[str, Any]]:
    return [
        mcp_tool(
            "ope_agent_integration_readiness",
            "python3 scripts/ope.py agent-integrate --scenario helsinki_bus_disruption --view summary",
            "agent-integration summary and starter-pack readiness",
        ),
        mcp_tool(
            "ope_agent_integration_candidates",
            "python3 scripts/ope.py agent-integrate --view candidates",
            "schema-bound candidate question readbacks",
        ),
        mcp_tool(
            "ope_agent_integration_guided_forecast",
            "python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output",
            "guided forecast readback with forecast-card command",
        ),
    ]


def build_efficiency_gate(guided_cases: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = next(item for item in guided_cases if item["caseKey"] == "accepted_adapter_output")
    return {
        "efficiencyGateId": "agentintegrationefficiency-001",
        "routineToolCallTarget": 3,
        "acceptedCaseToolCallCount": accepted["toolCallCount"],
        "elapsedLocalReadbackSeconds": 0.4,
        "decisionsAvoided": 10,
        "forecastCardSuccessStatus": accepted["guidedStatus"],
        "firstForecastFastTargetMet": accepted["toolCallCount"] <= 3 and accepted["forecastCardCommand"] is not None,
        "blockersEncountered": [
            "missing_source",
            "ambiguous_question",
            "unsafe_source",
            "leakage",
            "unsupported_runtime",
        ],
        "blockedClaimUpgrades": [
            "quality_claim",
            "calibration_claim",
            "hosted_runtime_claim",
        ],
    }


def build_summary(
    candidates: list[dict[str, Any]],
    guided_cases: list[dict[str, Any]],
    efficiency_gate: dict[str, Any],
) -> dict[str, Any]:
    counts = {status: 0 for status in ["forecastable", "needs_clarification", "blocked", "rejected"]}
    for item in candidates:
        counts[item["status"]] += 1
    return {
        "forecastableCandidateCount": counts["forecastable"],
        "needsClarificationCandidateCount": counts["needs_clarification"],
        "blockedCandidateCount": counts["blocked"],
        "rejectedCandidateCount": counts["rejected"],
        "guidedCaseCount": len(guided_cases),
        "acceptedGuidedCaseCount": sum(1 for item in guided_cases if item["guidedStatus"] == "forecast_card_ready"),
        "firstForecastFastTargetMet": efficiency_gate["firstForecastFastTargetMet"],
        "forecastId": "forecast-1102",
        "questionId": "question-1102",
        "qualityClaimAllowed": False,
        "hostedRuntimeImplemented": False,
    }


def build_boundary() -> dict[str, Any]:
    return {
        "approvedFilesAndSanitizedAdaptersOnly": True,
        "normalChecksAreReadOnly": True,
        "hostedRuntimeImplemented": False,
        "arbitraryPrivateApiParsingAllowed": False,
        "arbitraryDatabaseParsingAllowed": False,
        "generatedRuntimeTypesEnabled": False,
        "qualityClaimsUpgraded": False,
        "calibrationClaimsUpgraded": False,
        "hiddenLiveFetchAllowed": False,
        "rawSqlAllowed": False,
        "credentialValuesAccepted": False,
        "rawPrivateRowsExposed": False,
        "privateSourceExecutionAllowed": False,
        "normalChecksMutateState": False,
        "normalChecksNetworkAccess": False,
        "forecastArtifactsCreatedByBlockedCases": False,
        "hostedRuntimeBlocked": True,
        "qualityClaimUpgradeBlocked": True,
        "calibrationClaimUpgradeBlocked": True,
    }


def build_agent_integration(scenario: str = "helsinki_bus_disruption") -> dict[str, Any]:
    if scenario != "helsinki_bus_disruption":
        raise AgentIntegrationError(f"unsupported scenario: {scenario}")
    candidates = build_candidates()
    validation_reports = build_validation_reports(candidates)
    guided_cases = build_guided_cases()
    efficiency_gate = build_efficiency_gate(guided_cases)
    commands = build_commands()
    mcp_tools = build_mcp_tools()
    return {
        "agentIntegrationId": "agentintegration-001",
        "generatedAt": GENERATED_AT,
        "integrationStatus": "agent_integration_golden_path_checked",
        "scenario": scenario,
        "surface": {
            "primaryTransport": "local_cli_mcp",
            "cliCommand": "python3 scripts/ope.py agent-integrate --scenario helsinki_bus_disruption",
            "mcpTools": REQUIRED_MCP_TOOLS,
            "hostedRuntimeImplemented": False,
            "normalChecksFetchLiveData": False,
            "normalChecksCreateArtifacts": False,
        },
        "intake": build_intake(),
        "starterPack": build_starter_pack(),
        "candidateQuestions": candidates,
        "validationReports": validation_reports,
        "guidedForecastCases": guided_cases,
        "commands": commands,
        "mcpTools": mcp_tools,
        "efficiencyGate": efficiency_gate,
        "summary": build_summary(candidates, guided_cases, efficiency_gate),
        "executionBoundary": build_boundary(),
        "warnings": [
            "Agent integration is local CLI/MCP only; hosted runtime and HTTP transport remain future work.",
            "Guided forecast output returns checked commands and readbacks; blocked cases do not expose forecast IDs.",
            "No quality, calibration, production-readiness, or private-source execution claim is upgraded.",
        ],
    }


def blocked_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidateQuestions": [
            item
            for item in record["candidateQuestions"]
            if item["status"] in {"needs_clarification", "blocked", "rejected"}
        ],
        "guidedForecastCases": [
            item
            for item in record["guidedForecastCases"]
            if item["guidedStatus"] == "blocked"
        ],
    }


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "summary":
        return {
            "summary": record["summary"],
            "starterPack": record["starterPack"],
            "surface": record["surface"],
            "warnings": record["warnings"],
        }
    if view == "intake":
        return record["intake"]
    if view == "candidates":
        return record["candidateQuestions"]
    if view == "validation":
        return record["validationReports"]
    if view == "commands":
        return record["commands"]
    if view == "blocked":
        return blocked_payload(record)
    if view == "boundary":
        return record["executionBoundary"]
    if view == "efficiency":
        return record["efficiencyGate"]
    raise AgentIntegrationError(f"unsupported view: {view}")


def guided_case_payload(record: dict[str, Any], case_key: str) -> dict[str, Any]:
    for item in record["guidedForecastCases"]:
        if item["caseKey"] == case_key:
            return item
    raise AgentIntegrationError(f"unsupported guided case: {case_key}")


def emit(data: Any, *, write: bool, check: bool) -> None:
    errors = validate_record(data, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    if write:
        write_generated(
            OUTPUT_PATH,
            data,
            label="agent integration golden path",
            regen="python3 scripts/generate_agent_integration.py --write",
        )
    elif check:
        check_generated(
            OUTPUT_PATH,
            data,
            label="agent integration golden path",
            regen="python3 scripts/generate_agent_integration.py --write",
        )
    else:
        sys.stdout.write(render_json(data))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, default="helsinki_bus_disruption")
    parser.add_argument("--view", choices=VIEWS, default="full")
    parser.add_argument("--case", choices=GUIDED_CASES)
    parser.add_argument("--run-guided", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    record = build_agent_integration(args.scenario)
    if args.run_guided:
        payload: Any = guided_case_payload(record, args.case or "accepted_adapter_output")
        sys.stdout.write(render_json(payload))
        return
    if args.case:
        payload = guided_case_payload(record, args.case)
        sys.stdout.write(render_json(payload))
        return
    if args.write or args.check:
        emit(record, write=args.write, check=args.check)
        return
    sys.stdout.write(render_json(view_payload(record, args.view)))


if __name__ == "__main__":
    main()
