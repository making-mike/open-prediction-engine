#!/usr/bin/env python3
"""Generate or check the post-MVP expansion readiness gate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_agent_pilot_validation import build_agent_pilot_validation
from generate_developer_adoption_surface import build_developer_adoption_surface
from generate_local_source_runtime import build_runtime
from generate_local_usage_trace import build_local_usage_trace
from generate_pilot_evidence_ledger import build_pilot_evidence_ledger
from generate_prediction_campaign_explain import build_prediction_campaign_explain
from generate_release_manifest import build_manifest
from generate_transit_baseline_track_record_gate import build_gate
from generate_transit_corpus_growth_loop import build_growth_loop
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "expansion-readiness"
OUTPUT_PATH = GENERATED / "ope-expansion-readiness-gate.generated.json"
SCHEMA = SPEC / "expansion-readiness-gate.schema.json"
GENERATED_AT = "2026-06-10T10:45:00Z"

OPTION_ORDER = [
    "hosted_runtime",
    "broader_private_sources",
    "live_forecast_evidence",
    "stronger_methods",
    "generated_runtime_types",
]


class ExpansionReadinessGateError(Exception):
    pass


def evidence_input(
    index: int,
    source: str,
    observed_value: str,
    threshold: str,
    status: str,
    implication: str,
) -> dict[str, Any]:
    return {
        "inputId": f"expansionevidence-{index:03d}",
        "source": source,
        "observedValue": observed_value,
        "threshold": threshold,
        "status": status,
        "implication": implication,
    }


def expansion_option(
    area: str,
    status: str,
    evidence_required: list[str],
    blocked_by: list[str],
    next_local_step: str,
) -> dict[str, Any]:
    return {
        "area": area,
        "status": status,
        "evidenceRequired": evidence_required,
        "blockedBy": blocked_by,
        "nextLocalStep": next_local_step,
    }


def sequence_step(
    order: int,
    milestone_name: str,
    trigger: str,
    work_boundary: str,
    creates_production_runtime: bool,
) -> dict[str, Any]:
    return {
        "order": order,
        "milestoneName": milestone_name,
        "trigger": trigger,
        "workBoundary": work_boundary,
        "createsProductionRuntime": creates_production_runtime,
    }


def success_criterion(
    index: int,
    area: str,
    current_status: str,
    target: str,
    ready: bool,
) -> dict[str, Any]:
    return {
        "criterionId": f"expansioncriterion-{index:03d}",
        "area": area,
        "currentStatus": current_status,
        "target": target,
        "ready": ready,
    }


def build_evidence_inputs(
    manifest: dict[str, Any],
    adoption: dict[str, Any],
    pilot: dict[str, Any],
    pilot_evidence: dict[str, Any],
    usage: dict[str, Any],
    growth: dict[str, Any],
    track_gate: dict[str, Any],
    runtime: dict[str, Any],
    campaign_explain: dict[str, Any],
) -> list[dict[str, Any]]:
    sample = track_gate["sampleSummary"]
    return [
        evidence_input(
            1,
            "release manifest",
            f"surfaceStatus={manifest['mvpLocalRuntime']['surfaceStatus']}",
            "local MVP fixture-ready release surface",
            "met",
            "The local MVP is coherent enough to guide adoption and pilot work.",
        ),
        evidence_input(
            2,
            "developer adoption surface",
            f"quickstartSteps={adoption['summary']['quickstartStepCount']}; scenarioSteps={adoption['summary']['scenarioStepCount']}",
            "checked quickstart and full scenario",
            "met",
            "Developers and agents have a local path to first forecast card and lifecycle bundle.",
        ),
        evidence_input(
            3,
            "agent pilot validation",
            f"syntheticSummaries={len(pilot['examplePilotSummaries'])}; targetSessions={pilot['pilotProtocol']['targetSessions']}",
            "3-5 real pilot sessions with sanitized notes",
            "synthetic_only",
            "Real pilot evidence is still needed before adding hosted or broad runtime surfaces.",
        ),
        evidence_input(
            4,
            "pilot evidence ledger",
            f"acceptedRealSessions={pilot_evidence['summary']['acceptedRealSessionCount']}; acceptedSyntheticSummaries={pilot_evidence['summary']['acceptedSyntheticSummaryCount']}",
            "3-5 real sanitized pilot sessions accepted for aggregation",
            "below_threshold",
            "The ledger can accept sanitized summaries, but the checked fixture records no real sessions yet.",
        ),
        evidence_input(
            5,
            "local usage trace",
            f"events={usage['aggregateReadbacks']['totalEvents']}; forecastCompletionRate={usage['aggregateReadbacks']['forecastCompletionRate']}",
            "local deterministic usage signals without hosted telemetry",
            "met",
            "Local measurement exists, but it is not a substitute for real hosted telemetry or support evidence.",
        ),
        evidence_input(
            6,
            "transit corpus growth loop",
            f"projectedComparableResolved={growth['progressReadback']['projectedComparableResolved']}",
            "30 comparable resolved runs for track record; 100 for calibration",
            "below_threshold",
            "Public transport quality and stronger-method claims remain blocked by sample size.",
        ),
        evidence_input(
            7,
            "transit baseline track-record gate",
            f"resolvedComparableSampleSize={sample['resolvedComparableSampleSize']}; trackRecordStatus={sample['trackRecordStatus']}",
            "track-record and calibration thresholds reached with clean evidence",
            "below_threshold",
            "Baseline track-record and calibration readbacks remain below threshold.",
        ),
        evidence_input(
            8,
            "approved local-folder source runtime",
            f"forecastCardReadyCount={runtime['summary']['forecastCardReadyCount']}",
            "one narrow real source runtime reaches forecast card through existing gates",
            "met",
            "A repeatable local runtime pattern exists, but it does not justify arbitrary private API or database parsing.",
        ),
        evidence_input(
            9,
            "release non-goals",
            "hosted service, network API, production agent runtime, and generic private API/database runtime are listed non-goals",
            "explicit non-goals remain enforced before expansion work",
            "blocked",
            "Expansion must start with readiness gates and narrow specs, not production runtime claims.",
        ),
        evidence_input(
            10,
            "repeating prediction campaign explain",
            f"nextForecastId={campaign_explain['campaignSnapshot']['nextForecastId']}; pilotTaskReady={campaign_explain['summary']['pilotTaskCardReady']}",
            "recurring setup can explain next forecast, next resolution, evidence threshold, and claim boundary before hosted scheduling",
            "met",
            "Recurring prediction setup has a checked local readback and pilot task before hosted scheduling or broader runtime work.",
        ),
    ]


def build_options(growth: dict[str, Any], track_gate: dict[str, Any]) -> list[dict[str, Any]]:
    sample = track_gate["sampleSummary"]
    projected = growth["progressReadback"]["projectedComparableResolved"]
    return [
        expansion_option(
            "hosted_runtime",
            "blocked_pending_evidence",
            [
                "3-5 real pilot sessions identify a hosted-runtime need that local CLI cannot satisfy.",
                "Recurring prediction setup pilot evidence shows local terminal scheduling is insufficient.",
                "Hosted auth, tenancy, job state, scheduler, and provenance boundaries are specified before implementation.",
            ],
            ["hosted_service", "network_api", "production_agent_adapter_runtime"],
            "Run the repeating prediction pilot task and real pilot sessions before designing a hosted scheduler.",
        ),
        expansion_option(
            "broader_private_sources",
            "blocked_pending_evidence",
            [
                "Repeated pilot or usage evidence shows the approved local-folder runtime is insufficient.",
                "Recurring campaign source-policy and append-readiness readbacks identify a bounded source gap.",
                "One next source kind can be bounded with approval, allow-listing, size limits, and sanitized diagnostics.",
            ],
            ["generic_private_api_database_runtime", "credential_storage", "raw_private_row_retention"],
            "Choose at most one next source runtime from observed pilot friction, such as approved HTTP JSON, and keep it non-general.",
        ),
        expansion_option(
            "live_forecast_evidence",
            "blocked_pending_evidence",
            [
                "Forecast-time live captures are promoted through policy-bound source sets before the forecast closes.",
                "Resolution-only and post-close captures remain excluded from forecast provenance.",
            ],
            ["production_forecast_use_of_live_connector_results", "public_forecast_use_of_local_live_drafts"],
            "Keep collecting ignored local live drafts and promote only sanitized forecast-time source sets through the existing gate.",
        ),
        expansion_option(
            "stronger_methods",
            "blocked_pending_evidence",
            [
                f"Comparable resolved transit runs reach 30 for track record; current projected count is {projected}.",
                f"Calibration needs 100 comparable resolved runs; current resolved sample is {sample['resolvedComparableSampleSize']}.",
            ],
            ["not_enough_resolved_comparable_outcomes", "method_quality_claim_blocked"],
            "Grow the transit forward-run corpus and keep baseline-only execution until method lift is supported by clean samples.",
        ),
        expansion_option(
            "generated_runtime_types",
            "deferred_pending_adoption_evidence",
            [
                "Pilot notes or usage traces show repeated schema integration friction.",
                "Generated types can be checked against JSON Schema without becoming the source of truth.",
            ],
            ["generated_language_specific_runtime_types_deferred"],
            "Keep JSON Schema as the contract source and revisit generated TypeScript only after adoption evidence shows clear friction.",
        ),
    ]


def build_sequence() -> list[dict[str, Any]]:
    return [
        sequence_step(
            1,
            "Real Agent Pilot Sessions",
            "Developer adoption surface can guide first forecast-card readback.",
            "Run 3-5 local sessions and record sanitized summaries only.",
            False,
        ),
        sequence_step(
            2,
            "Recurring Prediction Setup Pilot",
            "Campaign explain and pilot-session task card are checked.",
            "Evaluate next forecast, next resolution, evidence threshold, and claim boundary before hosted scheduling.",
            False,
        ),
        sequence_step(
            3,
            "Transit Corpus Growth",
            "Public transport corpus has append-ready candidate guidance.",
            "Add comparable forward runs without broad quality or calibration claims.",
            False,
        ),
        sequence_step(
            4,
            "One Next Source Runtime Choice",
            "Pilot evidence shows a repeated source-kind blocker.",
            "Specify one bounded runtime path before writing execution code.",
            False,
        ),
        sequence_step(
            5,
            "Generated Types Decision",
            "Adoption evidence shows repeated schema friction.",
            "Generate checked helper types only if JSON Schema remains the source of truth.",
            False,
        ),
        sequence_step(
            6,
            "Hosted Runtime Boundary",
            "Local pilots and corpus evidence justify service work.",
            "Write hosted runtime contracts and threat boundaries before hosted implementation.",
            False,
        ),
    ]


def build_success_criteria(
    pilot: dict[str, Any],
    pilot_evidence: dict[str, Any],
    usage: dict[str, Any],
    growth: dict[str, Any],
    track_gate: dict[str, Any],
    runtime: dict[str, Any],
) -> list[dict[str, Any]]:
    sample = track_gate["sampleSummary"]
    return [
        success_criterion(
            1,
            "local MVP adoption",
            f"quickstart validated; usage events={usage['aggregateReadbacks']['totalEvents']}",
            "A new developer or agent reaches forecast-1102 card and bundle locally.",
            True,
        ),
        success_criterion(
            2,
            "real pilot evidence",
            f"accepted real sessions={pilot_evidence['summary']['acceptedRealSessionCount']}; synthetic summaries={len(pilot['examplePilotSummaries'])}",
            "At least 3 real pilot sessions with sanitized findings.",
            False,
        ),
        success_criterion(
            3,
            "public transit track record",
            f"projected comparable resolved={growth['progressReadback']['projectedComparableResolved']}",
            "At least 30 comparable resolved public transit runs.",
            False,
        ),
        success_criterion(
            4,
            "calibration evidence",
            f"resolved comparable sample size={sample['resolvedComparableSampleSize']}",
            "At least 100 comparable resolved runs before calibration claims.",
            False,
        ),
        success_criterion(
            5,
            "source runtime evidence",
            f"forecast-card-ready cases={runtime['summary']['forecastCardReadyCount']}",
            "One additional source runtime chosen from real friction and bounded before execution.",
            False,
        ),
        success_criterion(
            6,
            "generated type evidence",
            "no recurring real adoption friction recorded yet",
            "Repeated integration friction that generated types would directly reduce.",
            False,
        ),
        success_criterion(
            7,
            "recurring prediction setup",
            "campaign explain, pilot task card, adapter readbacks, and usage trace events are checked locally",
            "Agents can explain recurring campaign state before hosted scheduling or broader runtime work.",
            True,
        ),
    ]


def build_expansion_readiness_gate() -> dict[str, Any]:
    manifest = build_manifest()
    adoption = build_developer_adoption_surface()
    pilot = build_agent_pilot_validation()
    pilot_evidence = build_pilot_evidence_ledger()
    usage = build_local_usage_trace()
    growth = build_growth_loop()
    track_gate = build_gate()
    runtime = build_runtime()
    campaign_explain = build_prediction_campaign_explain()
    evidence = build_evidence_inputs(
        manifest,
        adoption,
        pilot,
        pilot_evidence,
        usage,
        growth,
        track_gate,
        runtime,
        campaign_explain,
    )
    options = build_options(growth, track_gate)
    criteria = build_success_criteria(pilot, pilot_evidence, usage, growth, track_gate, runtime)
    gate = {
        "expansionReadinessGateId": "expansionreadinessgate-001",
        "generatedAt": GENERATED_AT,
        "gateStatus": "blocked_pending_evidence",
        "decision": {
            "currentPosture": "hold_local_mvp_and_gather_evidence",
            "nextAction": "run_real_pilots_and_grow_corpus",
            "reason": "The local MVP is coherent, but hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types need real pilot, usage, and comparable outcome evidence before implementation.",
        },
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "developerAdoptionSurfaceId": adoption["developerAdoptionSurfaceId"],
            "agentPilotValidationId": pilot["agentPilotValidationId"],
            "pilotEvidenceLedgerId": pilot_evidence["pilotEvidenceLedgerId"],
            "localUsageTraceId": usage["localUsageTraceId"],
            "transitCorpusGrowthLoopId": growth["transitCorpusGrowthLoopId"],
            "transitBaselineTrackRecordGateId": track_gate["transitBaselineTrackRecordGateId"],
            "localSourceRuntimeId": runtime["localSourceRuntimeId"],
        },
        "evidenceInputs": evidence,
        "expansionOptions": options,
        "recommendedSequence": build_sequence(),
        "successCriteria": criteria,
        "summary": {
            "evidenceInputCount": len(evidence),
            "optionCount": len(options),
            "readyOptionCount": 0,
            "blockedOptionCount": len(options),
            "recommendedNextMilestone": "Milestone 97: repeating prediction pilot evidence, then real pilot sessions and transit corpus growth before hosted or broader runtime work.",
            "qualityClaimAllowed": False,
            "hostedRuntimeAllowed": False,
            "generatedTypesIncluded": False,
        },
        "executionBoundary": {
            "readOnlyGate": True,
            "deterministicOffline": True,
            "executesCommands": False,
            "createsForecastArtifacts": False,
            "fetchesLiveData": False,
            "startsHostedRuntime": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "generatesRuntimeTypes": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "Expansion readiness is a read-only decision surface over checked local records.",
            "The gate does not execute commands named in recommendations.",
            "Hosted runtime, production network APIs, and broad private-source runtimes remain non-goals until evidence unblocks them.",
            "Stronger methods and calibration claims remain blocked by comparable resolved sample thresholds.",
            "Generated runtime types remain deferred until adoption evidence shows they reduce integration friction.",
            "Recurring prediction setup must be evaluated with the local pilot task before hosted scheduling is designed.",
        ],
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    errors = validate_record(gate, SCHEMA)
    if errors:
        raise ExpansionReadinessGateError(f"expansion readiness gate schema validation failed: {errors[0]}")
    if gate["gateStatus"] != "blocked_pending_evidence":
        raise ExpansionReadinessGateError("expansion readiness gate must remain blocked pending evidence")
    if gate["decision"]["currentPosture"] != "hold_local_mvp_and_gather_evidence":
        raise ExpansionReadinessGateError("expansion posture drifted")
    option_areas = [item["area"] for item in gate["expansionOptions"]]
    if option_areas != OPTION_ORDER:
        raise ExpansionReadinessGateError("expansion option order drifted")
    if any(item["status"] == "ready_now" for item in gate["expansionOptions"]):
        raise ExpansionReadinessGateError("no expansion option should be ready now")
    evidence_statuses = {item["status"] for item in gate["evidenceInputs"]}
    if "synthetic_only" not in evidence_statuses or "below_threshold" not in evidence_statuses:
        raise ExpansionReadinessGateError("readiness evidence must include synthetic-only and below-threshold blockers")
    if gate["summary"]["readyOptionCount"] != 0:
        raise ExpansionReadinessGateError("ready option count must remain zero")
    if gate["summary"]["qualityClaimAllowed"] or gate["summary"]["hostedRuntimeAllowed"]:
        raise ExpansionReadinessGateError("expansion summary must block quality and hosted runtime claims")
    boundary = gate["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyGate", "deterministicOffline"}:
            if value is not True:
                raise ExpansionReadinessGateError(f"execution boundary {key} should be true")
        elif value is not False:
            raise ExpansionReadinessGateError(f"execution boundary {key} should be false")
    if any(item["createsProductionRuntime"] for item in gate["recommendedSequence"]):
        raise ExpansionReadinessGateError("recommended sequence must not create production runtime")


def summary(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "expansionReadinessGateId": gate["expansionReadinessGateId"],
        "gateStatus": gate["gateStatus"],
        "decision": gate["decision"],
        "bindings": gate["bindings"],
        "summary": gate["summary"],
        "evidenceInputs": gate["evidenceInputs"],
        "expansionOptions": [
            {
                "area": item["area"],
                "status": item["status"],
                "nextLocalStep": item["nextLocalStep"],
            }
            for item in gate["expansionOptions"]
        ],
    }


def section(gate: dict[str, Any], section_name: str) -> Any:
    if section_name == "evidence":
        return gate["evidenceInputs"]
    if section_name == "options":
        return gate["expansionOptions"]
    if section_name == "sequence":
        return gate["recommendedSequence"]
    if section_name == "criteria":
        return gate["successCriteria"]
    if section_name == "boundary":
        return gate["executionBoundary"]
    raise ExpansionReadinessGateError(f"unsupported section {section_name}")


def write_gate(gate: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, gate, label="expansion readiness gate", regen="python3 scripts/generate_expansion_readiness_gate.py --write")


def check_gate(gate: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, gate, label="expansion readiness gate", regen="python3 scripts/generate_expansion_readiness_gate.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section",
        choices=["evidence", "options", "sequence", "criteria", "boundary"],
        help="print one expansion readiness section",
    )
    parser.add_argument("--check", action="store_true", help="check generated expansion readiness gate drift")
    parser.add_argument("--write", action="store_true", help="refresh generated expansion readiness gate")
    args = parser.parse_args()
    try:
        gate = build_expansion_readiness_gate()
    except ExpansionReadinessGateError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_gate(gate)
    elif args.check:
        check_gate(gate)
    elif args.section:
        sys.stdout.write(render_json(section(gate, args.section)))
    else:
        sys.stdout.write(render_json(summary(gate)))


if __name__ == "__main__":
    main()
