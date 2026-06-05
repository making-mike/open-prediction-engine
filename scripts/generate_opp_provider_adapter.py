#!/usr/bin/env python3
"""Generate a checked optional Open Prediction Protocol provider-adapter readback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from ope_fixtures import check_generated, render_json, write_generated
from ope_schema import SPEC, validate_record
from read_ope_record import read_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "opp-provider-adapter"
OUTPUT_PATH = GENERATED / "ope-opp-provider-adapter.generated.json"
SCHEMA = SPEC / "opp-provider-adapter.schema.json"
GENERATED_AT = "2026-06-04T23:10:00Z"

REQUEST_FIELD_ORDER = [
    "predictionRequestId",
    "marketOrQuestion",
    "domain",
    "horizon",
    "outputType",
    "sourcePolicy",
    "callerIdentity",
    "constraints",
]

RESPONSE_RECORD_REFS = [
    "forecastId",
    "questionId",
    "evidenceTraceId",
    "lifecycleBundleId",
    "forecastCardRecordType",
    "forecastArtifactRecordType",
]

CASE_ORDER = [
    "accepted_forecast_card",
    "unsupported_market",
    "malformed_outcome_spec",
    "missing_source_policy",
    "provider_timeout",
    "response_too_large",
]

BLOCKED_CASES = [
    ("unsupported_market", "blocked_unsupported_market", "choose_supported_domain", "unsupported_market"),
    ("malformed_outcome_spec", "blocked_malformed_outcome_spec", "repair_resolution_rule", "malformed_outcome_spec"),
    ("missing_source_policy", "blocked_missing_source_policy", "provide_source_policy", "missing_source_policy"),
    ("provider_timeout", "blocked_provider_timeout", "retry_or_use_ope_readback", "provider_timeout"),
    ("response_too_large", "blocked_response_too_large", "request_compact_response", "response_too_large"),
]


class OppProviderAdapterError(Exception):
    pass


def request_mapping_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "predictionRequestId",
            "OPE forecast request requestId plus internal API idempotency metadata.",
            True,
        ),
        (
            "marketOrQuestion",
            "OPE forecast-request question text, resolution criteria, and domain setup hints after validation.",
            True,
        ),
        (
            "domain",
            "OPE domain-config domain key or setup domain label.",
            True,
        ),
        (
            "horizon",
            "OPE horizon startsAt, endsAt, close time, and scheduled resolution timing.",
            True,
        ),
        (
            "outputType",
            "OPE outputType contract, currently checked through binary forecast fixtures.",
            True,
        ),
        (
            "sourcePolicy",
            "OPE source-policy contract, including fixture, provided, or approved source boundaries.",
            True,
        ),
        (
            "callerIdentity",
            "Internal API caller identity and operation metadata; credential values remain outside OPE records.",
            True,
        ),
        (
            "constraints",
            "Adapter constraints such as max response bytes, requested audit metadata, and supported output modes.",
            False,
        ),
    ]
    return [
        {
            "oppField": opp_field,
            "opeMapping": ope_mapping,
            "requiredForFixtureAdapter": required,
            "mappingStatus": "mapped_to_ope_contract",
            "rawPromptStored": False,
            "credentialValuesAccepted": False,
        }
        for opp_field, ope_mapping, required in rows
    ]


def request_mapping() -> dict[str, Any]:
    return {
        "mappingStatus": "checked_mapping_fixture",
        "mapsToOpeForecastRequest": True,
        "createsOpeRecordsDirectly": False,
        "mappingRows": request_mapping_rows(),
    }


def response_mapping() -> dict[str, Any]:
    return {
        "mappingStatus": "checked_mapping_fixture",
        "mapsFromForecastCard": True,
        "mapsFromForecastArtifact": True,
        "predictionResponseShape": "compact_binary_probability_with_audit_refs",
        "auditMetadataChannel": "audit",
        "requiredOpeRecordRefs": RESPONSE_RECORD_REFS,
        "claimBoundaryCarried": True,
        "scoreStatusCarried": True,
        "rawLifecycleBundleEmbedded": False,
    }


def domain_capability(
    *,
    domain: str,
    horizons: list[str],
    evidence_modes: list[str],
    maturity: str,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "supportedHorizons": horizons,
        "supportedOutputTypes": ["binary"],
        "supportedEvidenceModes": evidence_modes,
        "maturityLabel": maturity,
        "calibrationStatus": "below_threshold_no_live_claim",
        "complianceStatus": "policy_boundary_only",
        "liveCalibrationClaimAllowed": False,
        "paidProviderRequired": False,
    }


def agent_card() -> dict[str, Any]:
    return {
        "agentCardStatus": "checked_fixture",
        "providerId": "ope-local-fixture-provider",
        "providerName": "Open Prediction Engine local fixture provider",
        "advertisedRuntime": "local_cli_fixture_only",
        "httpEndpointAdvertised": False,
        "sseEndpointAdvertised": False,
        "aggregationAdvertised": False,
        "supportedPricingModes": ["free_local_fixture"],
        "supportedOutputTypes": ["binary"],
        "supportedHorizons": ["1-day", "service-window", "campaign-window"],
        "domainCapabilities": [
            domain_capability(
                domain="weather-logistics",
                horizons=["1-day"],
                evidence_modes=["fixture", "auto_evidence_fixture_replay", "provided"],
                maturity="fixture_ready_reference",
            ),
            domain_capability(
                domain="weather-transit-delays",
                horizons=["service-window", "campaign-window"],
                evidence_modes=["fixture", "approved_local_live_capture", "campaign_ledger"],
                maturity="public_beta_candidate",
            ),
            domain_capability(
                domain="seaport-berth-availability",
                horizons=["service-window"],
                evidence_modes=["approved_local_file", "approved_database_adapter_fixture", "external_source_adapter_output"],
                maturity="candidate_private_setup",
            ),
        ],
    }


def opp_prediction_request(case_name: str, *, source_policy_mode: str = "fixture") -> dict[str, Any]:
    return {
        "predictionRequestId": f"opppredictionrequest-{CASE_ORDER.index(case_name) + 1:03d}",
        "marketOrQuestion": "Will heavy rain disrupt last-mile delivery operations in Warsaw on 2026-06-03?",
        "domain": "weather-logistics" if case_name != "unsupported_market" else "unsupported-election-market",
        "horizon": {
            "startsAt": "2026-06-03T00:00:00Z",
            "endsAt": "2026-06-03T23:59:59Z",
            "label": "1-day",
        },
        "outputType": "binary",
        "sourcePolicy": {
            "mode": source_policy_mode,
            "sourcePolicyId": "sourcepolicy-019" if source_policy_mode != "missing" else "none",
            "normalChecksOffline": True,
        },
        "callerIdentity": {
            "callerId": "caller-opp-fixture-001",
            "credentialValuesIncluded": False,
        },
        "constraints": {
            "maxResponseBytes": 8192,
            "requireAuditRefs": True,
            "requestedMetadataChannel": "audit",
        },
    }


def compact_ope_forecast_card() -> dict[str, Any]:
    card = read_record("forecast-card", "forecast-602", "question-601")["record"]
    probability = card["forecast"]["probability"]
    return {
        "forecastId": card["forecastId"],
        "questionId": card["questionId"],
        "forecastCardRecordType": "forecast-card",
        "forecastArtifactRecordType": "forecast-artifact",
        "title": card["title"],
        "domain": card["domain"],
        "horizon": card["horizon"],
        "outputType": card["forecast"]["outputType"],
        "probability": probability,
        "scoreStatus": card["score"]["scoreStatus"],
        "claimBoundary": card["qualityClaim"]["status"],
        "evidenceTraceId": card["forecastId"],
        "evidenceTraceLinkId": card["links"]["evidenceTrace"],
        "lifecycleBundleId": card["forecastId"],
        "lifecycleBundleLinkId": card["links"]["forecastBundle"],
    }


def prediction_response(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "predictionResponseId": "opppredictionresponse-001",
        "predictionRequestId": "opppredictionrequest-001",
        "providerId": "ope-local-fixture-provider",
        "responseStatus": "prediction_ready",
        "outputType": card["outputType"],
        "probability": card["probability"],
        "scoreStatus": card["scoreStatus"],
        "claimBoundary": card["claimBoundary"],
        "audit": {
            "forecastId": card["forecastId"],
            "questionId": card["questionId"],
            "evidenceTraceId": card["evidenceTraceId"],
            "evidenceTraceLinkId": card["evidenceTraceLinkId"],
            "lifecycleBundleId": card["lifecycleBundleId"],
            "lifecycleBundleLinkId": card["lifecycleBundleLinkId"],
            "forecastCardRecordType": "forecast-card",
            "forecastArtifactRecordType": "forecast-artifact",
            "scoreStatus": card["scoreStatus"],
            "claimBoundary": card["claimBoundary"],
            "responseGeneratedFromExistingOpeRecords": True,
            "rawLifecycleBundleEmbedded": False,
        },
    }


def accepted_case() -> dict[str, Any]:
    card = compact_ope_forecast_card()
    return {
        "caseName": "accepted_forecast_card",
        "caseStatus": "response_ready",
        "nextAction": "return_prediction_response",
        "predictionRequest": opp_prediction_request("accepted_forecast_card"),
        "opeForecastCard": card,
        "predictionResponse": prediction_response(card),
        "forecastArtifactsCreated": False,
        "opeRecordsMutated": False,
        "usesExistingOpeRecords": True,
        "claimBoundaryPreserved": True,
        "sanitizedDiagnosticsOnly": True,
    }


def blocked_case(case_name: str, status: str, next_action: str, reason: str) -> dict[str, Any]:
    source_mode = "missing" if case_name == "missing_source_policy" else "fixture"
    return {
        "caseName": case_name,
        "caseStatus": status,
        "nextAction": next_action,
        "predictionRequest": opp_prediction_request(case_name, source_policy_mode=source_mode),
        "blockedReason": reason,
        "diagnostic": {
            "code": reason,
            "message": f"OPP provider adapter fixture blocked {case_name} before OPE record mutation.",
            "safeForCaller": True,
        },
        "forecastArtifactsCreated": False,
        "opeRecordsMutated": False,
        "usesExistingOpeRecords": False,
        "claimBoundaryPreserved": True,
        "sanitizedDiagnosticsOnly": True,
    }


def conformance_cases() -> list[dict[str, Any]]:
    return [accepted_case()] + [
        blocked_case(case_name, status, next_action, reason)
        for case_name, status, next_action, reason in BLOCKED_CASES
    ]


def conformance_plan() -> dict[str, Any]:
    return {
        "minimalSurfaceStatus": "plan_checked_no_http_listener",
        "normalChecksStartHttpServer": False,
        "providerCardChecked": True,
        "requestResponseFixturesChecked": True,
        "errorFixturesChecked": True,
        "requiredFutureEndpoints": ["/opp/v1/agent-card", "/opp/v1/predictions"],
        "localFixtureCommand": "python3 scripts/ope.py opp-provider-adapter",
        "futureHttpBoundary": "HTTP provider endpoints should call the internal API and read OPE records; they should not redefine forecast semantics.",
    }


def protocol_boundary() -> dict[str, bool]:
    return {
        "opeRecordsAuthoritative": True,
        "oppOptionalInterop": True,
        "localMcpStdioCurrentTestedProtocol": True,
        "preservesForecastSemantics": True,
        "preservesEvidenceSemantics": True,
        "preservesResolutionScoringCalibrationSemantics": True,
        "oppReplacesOpeLifecycleRecords": False,
        "httpRuntimeImplemented": False,
        "sseRuntimeImplemented": False,
        "paymentSettlementImplemented": False,
        "aggregationRuntimeImplemented": False,
        "hostedServiceImplemented": False,
        "networkListenerStarted": False,
        "normalChecksUseNetwork": False,
        "rawLifecycleBundleEmbeddedByDefault": False,
        "qualityClaimsUpgraded": False,
    }


def readbacks() -> list[dict[str, Any]]:
    return [
        {
            "readbackSurface": "cli",
            "command": "python3 scripts/ope.py opp-provider-adapter",
            "operationName": "opp_provider_adapter",
            "mutatesState": False,
            "startsNetworkListener": False,
        },
        {
            "readbackSurface": "agent_card",
            "command": "python3 scripts/ope.py opp-provider-adapter --view agent-card",
            "operationName": "opp_provider_agent_card",
            "mutatesState": False,
            "startsNetworkListener": False,
        },
        {
            "readbackSurface": "accepted_response",
            "command": "python3 scripts/ope.py opp-provider-adapter --case accepted_forecast_card",
            "operationName": "opp_provider_prediction_response",
            "mutatesState": False,
            "startsNetworkListener": False,
        },
    ]


def build_opp_provider_adapter() -> dict[str, Any]:
    cases = conformance_cases()
    card = agent_card()
    return {
        "oppProviderAdapterId": "oppprovideradapter-001",
        "generatedAt": GENERATED_AT,
        "providerAdapterStatus": "optional_opp_provider_adapter_checked",
        "adapterScope": "interop_mapping_over_ope_lifecycle_records",
        "normalChecksOffline": True,
        "localMcpStdioTested": True,
        "httpProviderRuntimeImplemented": False,
        "sseStreamingImplemented": False,
        "paymentSettlementImplemented": False,
        "aggregationImplemented": False,
        "hostedServiceRequired": False,
        "requestMapping": request_mapping(),
        "responseMapping": response_mapping(),
        "agentCard": card,
        "conformanceCases": cases,
        "conformancePlan": conformance_plan(),
        "protocolBoundary": protocol_boundary(),
        "readbacks": readbacks(),
        "summary": {
            "requestMappingCount": len(REQUEST_FIELD_ORDER),
            "conformanceCaseCount": len(CASE_ORDER),
            "blockedCaseCount": len(BLOCKED_CASES),
            "supportedDomainCount": len(card["domainCapabilities"]),
            "httpRuntimeImplemented": False,
            "oppReplacesOpeRecords": False,
        },
        "warnings": [
            "This is an optional interoperability adapter fixture, not a claim that OPE currently runs an OPP HTTP provider.",
            "OPE forecast cards, artifacts, evidence traces, lifecycle bundles, scoring records, and claim gates remain authoritative.",
            "Normal checks stay offline and do not start HTTP, SSE, payment, aggregation, or hosted service runtimes.",
        ],
    }


def validate_opp_provider_adapter(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise OppProviderAdapterError("OPP provider adapter failed schema validation")
    if [item["oppField"] for item in record["requestMapping"]["mappingRows"]] != REQUEST_FIELD_ORDER:
        raise OppProviderAdapterError("OPP request mapping order drifted")
    if [item["caseName"] for item in record["conformanceCases"]] != CASE_ORDER:
        raise OppProviderAdapterError("OPP conformance case order drifted")
    boundary = record["protocolBoundary"]
    for key in [
        "oppReplacesOpeLifecycleRecords",
        "httpRuntimeImplemented",
        "sseRuntimeImplemented",
        "paymentSettlementImplemented",
        "aggregationRuntimeImplemented",
        "hostedServiceImplemented",
        "networkListenerStarted",
        "normalChecksUseNetwork",
        "rawLifecycleBundleEmbeddedByDefault",
        "qualityClaimsUpgraded",
    ]:
        if boundary[key] is not False:
            raise OppProviderAdapterError(f"OPP protocol boundary {key} should stay false")


def view_payload(record: dict[str, Any], view: str) -> Any:
    if view == "full":
        return record
    if view == "request":
        return record["requestMapping"]
    if view == "response":
        return record["responseMapping"]
    if view == "agent-card":
        return record["agentCard"]
    if view == "cases":
        return record["conformanceCases"]
    if view == "accepted":
        return record["conformanceCases"][0]
    if view == "blocked":
        return record["conformanceCases"][1:]
    if view == "conformance":
        return record["conformancePlan"]
    if view == "boundary":
        return record["protocolBoundary"]
    if view == "readbacks":
        return record["readbacks"]
    if view == "summary":
        return record["summary"]
    raise OppProviderAdapterError(f"unsupported view {view}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write generated OPP provider-adapter fixture")
    parser.add_argument("--check", action="store_true", help="check generated OPP provider-adapter fixture")
    parser.add_argument("--case", choices=CASE_ORDER, help="print one checked OPP conformance case")
    parser.add_argument(
        "--view",
        choices=[
            "full",
            "request",
            "response",
            "agent-card",
            "cases",
            "accepted",
            "blocked",
            "conformance",
            "boundary",
            "readbacks",
            "summary",
        ],
        default="full",
        help="emit a focused OPP provider-adapter view",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    record = build_opp_provider_adapter()
    validate_opp_provider_adapter(record)
    if args.write:
        write_generated(
            OUTPUT_PATH,
            record,
            label="OPP provider adapter",
            regen="python3 scripts/generate_opp_provider_adapter.py --write",
        )
        return
    if args.check:
        check_generated(
            OUTPUT_PATH,
            record,
            label="OPP provider adapter",
            regen="python3 scripts/generate_opp_provider_adapter.py --write",
        )
        return
    if args.case:
        print(render_json(next(item for item in record["conformanceCases"] if item["caseName"] == args.case)), end="")
        return
    print(render_json(view_payload(record, args.view)), end="")


if __name__ == "__main__":
    main()
