#!/usr/bin/env python3
"""Generate or check the generated runtime types decision record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from generate_pilot_findings import build_pilot_findings
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "spec" / "fixtures" / "generated" / "generated-types" / "ope-generated-runtime-types-decision.generated.json"
SCHEMA = SPEC / "generated-runtime-types-decision.schema.json"
GENERATED_AT = "2026-06-05T16:10:00Z"


def evidence_review(pilot_findings: dict[str, Any]) -> dict[str, Any]:
    summary = pilot_findings["summary"]
    return {
        "pilotFindingsId": pilot_findings["pilotFindingsId"],
        "acceptedRealSessionCount": summary["acceptedRealSessionCount"],
        "acceptedSimulatedAgentSessionCount": summary["acceptedSimulatedAgentSessionCount"],
        "minimumRealSessions": summary["minimumRealSessions"],
        "agentSimulationEvidenceReady": summary["agentSimulationEvidenceReady"],
        "typeRelatedFrictionObserved": False,
        "smokeFailuresTypeRelated": False,
        "adoptionTraceTypeNeedObserved": False,
        "rationale": (
            "Eight simulated agent sessions exist, including three non-Helsinki setup-comprehension prompts, "
            "but no accepted real pilot sessions exist yet, and the "
            "checked smoke/adoption paths do not show type-specific friction. Stable JSON examples and "
            "validators remain the right default until real agent adoption evidence identifies a "
            "language-specific bottleneck."
        ),
    }


def json_fallback() -> dict[str, Any]:
    return {
        "stableJsonExamples": [
            "spec/fixtures/generated/prediction-feature-setup/ope-prediction-feature-setup.generated.json",
            "examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json",
            "examples/embed-ope-prediction-feature/fixtures/expected_accepted_summary.json",
            "spec/fixtures/generated/mcp-adoption/ope-mcp-adoption-path.generated.json",
            "spec/fixtures/generated/pilot-findings/ope-pilot-findings.generated.json",
        ],
        "validatorCommand": "python3 scripts/ope.py validate --input <record.json>",
        "smokeCommand": "python3 scripts/ope.py smoke",
    }


def blocked_cases() -> list[dict[str, str]]:
    return [
        {
            "caseKey": "full_spec_sdk",
            "blockedReason": "The full spec package is still evolving and should not be represented as a stable SDK surface.",
        },
        {
            "caseKey": "private_source_runtime_types",
            "blockedReason": "Private API/database source runtimes remain planned or bounded, so generated types would overstate runtime support.",
        },
        {
            "caseKey": "hosted_client_sdk",
            "blockedReason": "No hosted service or HTTP API is implemented, so client SDK types would imply an unsupported transport.",
        },
        {
            "caseKey": "forecast_quality_model_types",
            "blockedReason": "Generated method or quality types would not create benchmark, track-record, or calibration evidence.",
        },
    ]


def follow_up_gates() -> list[dict[str, Any]]:
    return [
        {
            "gateKey": "real_pilot_type_friction",
            "requiredEvidence": "Three to five sanitized pilot summaries show repeated schema-copying or validation friction that types would directly reduce.",
            "ready": False,
        },
        {
            "gateKey": "compact_scope_confirmed",
            "requiredEvidence": "The first generated surface is limited to prediction-feature setup request/response and forecast-card readback.",
            "ready": False,
        },
        {
            "gateKey": "drift_checker_defined",
            "requiredEvidence": "A generated-type drift checker exists for the accepted target language before files are emitted.",
            "ready": False,
        },
    ]


def execution_boundary() -> dict[str, bool]:
    return {
        "hostedRuntimeImplied": False,
        "fullSpecSdkStabilityClaimed": False,
        "productionSourceParsingImplied": False,
        "qualityClaimsUpgraded": False,
        "generatedFilesWritten": False,
    }


def build_generated_runtime_types_decision() -> dict[str, Any]:
    pilot_findings = build_pilot_findings()
    review = evidence_review(pilot_findings)
    return {
        "generatedRuntimeTypesDecisionId": "generatedtypesdecision-001",
        "generatedAt": GENERATED_AT,
        "decisionStatus": "defer_until_adoption_evidence",
        "selectedLanguageTargets": [],
        "firstAcceptedScope": [],
        "evidenceReview": review,
        "jsonFallback": json_fallback(),
        "blockedBroaderGenerationCases": blocked_cases(),
        "followUpGates": follow_up_gates(),
        "executionBoundary": execution_boundary(),
        "summary": {
            "decisionStatus": "defer_until_adoption_evidence",
            "generatedTypesIncluded": False,
            "selectedLanguageTargetCount": 0,
            "acceptedRealSessionCount": review["acceptedRealSessionCount"],
            "acceptedSimulatedAgentSessionCount": review["acceptedSimulatedAgentSessionCount"],
            "nextReviewTrigger": "Review after sanitized pilot findings show repeated type-related integration friction.",
        },
    }


def validate_generated_runtime_types_decision(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise AssertionError(f"generated runtime types decision validation failed: {errors[0]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--section",
        choices=["summary", "evidence", "json-fallback", "blocked", "gates", "boundary"],
        help="print one generated-types decision section",
    )
    args = parser.parse_args()

    record = build_generated_runtime_types_decision()
    validate_generated_runtime_types_decision(record)
    rendered = render_json(record)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(rendered, encoding="utf-8")
        print(f"generated {OUT.relative_to(ROOT)}")
        return
    if args.check:
        if not OUT.exists():
            raise SystemExit(f"missing generated runtime types decision: {OUT}")
        current = OUT.read_text(encoding="utf-8")
        if current != rendered:
            raise SystemExit(
                f"generated runtime types decision drift: {OUT}\n"
                "run `python3 scripts/generate_generated_runtime_types_decision.py --write`"
            )
        print("checked generated runtime types decision")
        return

    if args.section == "summary":
        payload: Any = record["summary"]
    elif args.section == "evidence":
        payload = record["evidenceReview"]
    elif args.section == "json-fallback":
        payload = record["jsonFallback"]
    elif args.section == "blocked":
        payload = record["blockedBroaderGenerationCases"]
    elif args.section == "gates":
        payload = record["followUpGates"]
    elif args.section == "boundary":
        payload = record["executionBoundary"]
    else:
        payload = record
    print(json.dumps(payload, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
