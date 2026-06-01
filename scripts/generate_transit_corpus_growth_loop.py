#!/usr/bin/env python3
"""Generate or check the transit forward-run corpus growth loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generate_transit_forward_run_corpus import OUTPUT_PATH as CORPUS_PATH
from generate_transit_forward_run_corpus import build_corpus
from ope_schema import SPEC, validate_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-corpus-growth"
GROWTH_PATH = GENERATED / "transit-corpus-growth-loop.generated.json"
SCHEMA = SPEC / "transit-corpus-growth-loop.schema.json"
GENERATED_AT = "2026-06-10T07:15:00Z"

CASE_ORDER = [
    "comparable_resolved",
    "missing_outcome",
    "stale_evidence",
    "leakage_risk",
    "post_close_source",
    "incomparable_window",
]


class TransitCorpusGrowthLoopError(Exception):
    pass


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def append_only_write(*, append: bool) -> dict[str, bool]:
    return {
        "wouldAppendCorpusRow": append,
        "wouldModifyExistingRows": False,
        "wouldCreateForecastArtifacts": False,
        "wouldCreateResolutionRecords": False,
        "wouldCreateScoringRecords": False,
        "requiresManualCorpusEditing": False,
    }


def candidate(
    *,
    index: int,
    candidate_case: str,
    service_date: str,
    append_decision: str,
    reason_code: str,
    bindings_present: bool,
    forecast_before_close: bool,
    resolved_after_horizon: bool,
    score_present: bool,
    forecast_boundary: bool,
    resolution_boundary: bool,
    next_action: str,
) -> dict[str, Any]:
    append_ready = append_decision == "append_ready"
    return {
        "candidateId": f"transitcorpusgrowthcandidate-{index:03d}",
        "candidateCase": candidate_case,
        "forwardRunId": f"transitdelayforwardrun-{1300 + index:03d}",
        "forecastId": f"forecast-{1300 + index}" if bindings_present else None,
        "questionId": f"question-{1300 + index}" if bindings_present else None,
        "serviceDate": service_date,
        "appendDecision": append_decision,
        "reasonCode": reason_code,
        "requiredBindingsPresent": bindings_present,
        "forecastBeforeClose": forecast_before_close,
        "resolvedAfterHorizon": resolved_after_horizon,
        "scorePresent": score_present,
        "forecastTimeEvidenceBoundaryPreserved": forecast_boundary,
        "resolutionOnlyEvidenceBoundaryPreserved": resolution_boundary,
        "appendOnlyWrite": append_only_write(append=append_ready),
        "nextAction": next_action,
    }


def build_candidates() -> list[dict[str, Any]]:
    return [
        candidate(
            index=1,
            candidate_case="comparable_resolved",
            service_date="2026-06-17",
            append_decision="append_ready",
            reason_code="none",
            bindings_present=True,
            forecast_before_close=True,
            resolved_after_horizon=True,
            score_present=True,
            forecast_boundary=True,
            resolution_boundary=True,
            next_action="Append one new comparable row after the checked forward-run, resolution, and scoring records are present.",
        ),
        candidate(
            index=2,
            candidate_case="missing_outcome",
            service_date="2026-06-18",
            append_decision="exclude_from_comparable",
            reason_code="missing_outcome",
            bindings_present=True,
            forecast_before_close=True,
            resolved_after_horizon=False,
            score_present=False,
            forecast_boundary=True,
            resolution_boundary=True,
            next_action="Keep the run pending or excluded until the declared resolution source yields an outcome.",
        ),
        candidate(
            index=3,
            candidate_case="stale_evidence",
            service_date="2026-06-19",
            append_decision="exclude_from_comparable",
            reason_code="stale_evidence",
            bindings_present=True,
            forecast_before_close=True,
            resolved_after_horizon=True,
            score_present=False,
            forecast_boundary=False,
            resolution_boundary=True,
            next_action="Exclude the run and collect a fresh pre-close evidence set before another forecast attempt.",
        ),
        candidate(
            index=4,
            candidate_case="leakage_risk",
            service_date="2026-06-20",
            append_decision="reject_from_corpus",
            reason_code="leakage_risk",
            bindings_present=True,
            forecast_before_close=False,
            resolved_after_horizon=True,
            score_present=False,
            forecast_boundary=False,
            resolution_boundary=False,
            next_action="Reject the candidate because post-outcome or same-window outcome evidence may have entered forecast provenance.",
        ),
        candidate(
            index=5,
            candidate_case="post_close_source",
            service_date="2026-06-21",
            append_decision="exclude_from_comparable",
            reason_code="post_close_source",
            bindings_present=True,
            forecast_before_close=False,
            resolved_after_horizon=True,
            score_present=False,
            forecast_boundary=False,
            resolution_boundary=True,
            next_action="Retain for audit only; do not count the run as forecast-time comparable evidence.",
        ),
        candidate(
            index=6,
            candidate_case="incomparable_window",
            service_date="2026-06-22",
            append_decision="exclude_from_comparable",
            reason_code="incomparable_window",
            bindings_present=True,
            forecast_before_close=True,
            resolved_after_horizon=True,
            score_present=True,
            forecast_boundary=True,
            resolution_boundary=True,
            next_action="Keep the run outside the morning-peak comparable corpus and start a separate corpus if the window matters.",
        ),
    ]


def checklist_item(index: int, check: str, required: bool, boundary: bool, next_action: str) -> dict[str, Any]:
    return {
        "checkId": f"transitcorpusgrowthcheck-{index:03d}",
        "check": check,
        "requiredForAppend": required,
        "preservesForecastTimeEvidenceBoundary": boundary,
        "nextAction": next_action,
    }


def build_due_checklist() -> list[dict[str, Any]]:
    return [
        checklist_item(1, "Forward run state exists and has not already been resolved.", True, True, "Read resolution jobs before attempting resolver execution."),
        checklist_item(2, "Forecast timestamp is at or before the declared close time.", True, True, "Reject candidates whose forecast was created after close."),
        checklist_item(3, "Resolution due time is reached after the horizon end.", True, True, "Wait until the due time before resolving."),
        checklist_item(4, "Resolver command uses declared resolution-only sources.", True, True, "Keep TripUpdates and outcome rows out of forecast-time provenance."),
        checklist_item(5, "Saved state and resolver output are sanitized and path-bounded.", True, True, "Stop if ignored live workspace paths or raw payloads would be committed."),
    ]


def build_post_resolution_checklist() -> list[dict[str, Any]]:
    return [
        checklist_item(6, "Resolution record status is resolved and after horizon end.", True, True, "Exclude ambiguous, annulled, or premature outcomes."),
        checklist_item(7, "Scoring report is present and binds the forecast, question, resolution, and baseline.", True, True, "Do not append comparable rows without score bindings."),
        checklist_item(8, "Observation coverage meets the corpus minimum.", True, True, "Route low-coverage runs to the exclusion ledger."),
        checklist_item(9, "Forecast evidence excludes post-close outcome rows.", True, True, "Reject leakage-risk candidates from the corpus."),
        checklist_item(10, "Service window, network, geography, and threshold match the corpus scope.", True, True, "Exclude incomparable windows from this corpus."),
        checklist_item(11, "Append operation adds a new row without modifying existing corpus rows.", True, True, "Preserve append-only corpus history."),
    ]


def build_exclusion_ledger(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for index, item in enumerate([candidate for candidate in candidates if candidate["reasonCode"] != "none"], start=1):
        rows.append(
            {
                "ledgerRowId": f"transitcorpusgrowthledger-{index:03d}",
                "candidateCase": item["candidateCase"],
                "reasonCode": item["reasonCode"],
                "countsTowardComparableResolved": False,
                "countsTowardCalibration": False,
                "safeToRetainForAudit": item["appendDecision"] != "reject_from_corpus",
                "nextAction": item["nextAction"],
            }
        )
    return rows


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(min(numerator / denominator, 1.0), 4)


def build_growth_loop() -> dict[str, Any]:
    corpus = build_corpus()
    summary = corpus["summary"]
    policy = corpus["comparableWindowPolicy"]
    current = summary["comparableResolvedCount"]
    minimum_track_record = policy["minimumComparableResolvedForTrackRecord"]
    minimum_calibration = policy["minimumComparableResolvedForCalibration"]
    candidates = build_candidates()
    append_ready = sum(1 for item in candidates if item["appendDecision"] == "append_ready")
    projected = current + append_ready
    growth_loop = {
        "transitCorpusGrowthLoopId": "transitcorpusgrowthloop-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-transit-delays",
        "growthMode": "checked_append_readiness_loop",
        "sourceCorpus": {
            "transitForwardRunCorpusId": corpus["transitForwardRunCorpusId"],
            "sourceCommand": "python3 scripts/ope.py transit-forward-run-corpus",
            "corpusPath": rel(CORPUS_PATH),
            "currentComparableResolved": current,
            "currentExcluded": summary["excludedCount"],
            "minimumComparableResolvedForTrackRecord": minimum_track_record,
            "minimumComparableResolvedForCalibration": minimum_calibration,
        },
        "appendProtocol": {
            "appendProtocolId": "transitcorpusgrowthprotocol-001",
            "appendReadinessCommand": "python3 scripts/ope.py transit-corpus-growth --case comparable_resolved",
            "appendOnly": True,
            "manualCorpusEditingRequired": False,
            "canonicalCorpusMutationImplemented": False,
            "normalChecksMutateCorpus": False,
            "requiredBindings": [
                "forward_run_state",
                "forecast_artifact",
                "resolution_record",
                "scoring_report",
                "source_policy",
                "corpus_policy",
            ],
            "acceptanceChecks": [
                "Forecast exists and was produced before close time.",
                "Resolution exists and was produced after horizon end.",
                "Scoring report binds forecast, question, resolution, and baseline.",
                "Observation coverage satisfies the corpus policy.",
                "Forecast-time evidence excludes post-close outcome rows.",
                "Append action adds a row and does not edit existing corpus rows.",
            ],
        },
        "candidateUpdates": candidates,
        "dueRunChecklist": build_due_checklist(),
        "postResolutionChecklist": build_post_resolution_checklist(),
        "exclusionLedger": build_exclusion_ledger(candidates),
        "progressReadback": {
            "currentComparableResolved": current,
            "appendReadyComparableCount": append_ready,
            "projectedComparableResolved": projected,
            "remainingForTrackRecord": max(minimum_track_record - projected, 0),
            "remainingForCalibration": max(minimum_calibration - projected, 0),
            "progressToTrackRecord": ratio(projected, minimum_track_record),
            "progressToCalibration": ratio(projected, minimum_calibration),
            "qualityClaimAllowed": False,
            "calibrationClaimAllowed": False,
            "baselineTrackRecordAllowed": False,
        },
        "executionBoundary": {
            "executesAppend": False,
            "appendOnlyContractDeclared": True,
            "modifiesExistingCorpusRows": False,
            "readsIgnoredLiveWorkspace": False,
            "fetchesLiveData": False,
            "createsForecastArtifacts": False,
            "createsResolutionRecords": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
            "allowsQualityClaims": False,
            "normalChecksDeterministicOffline": True,
        },
        "warnings": [
            "The growth loop is an append-readiness read model; normal checks do not mutate the canonical corpus.",
            "Comparable candidates require forecast, resolution, score, source-policy, and corpus-policy bindings before append.",
            "Excluded candidates preserve audit reasons but do not count toward track-record or calibration thresholds.",
            "Projected progress remains below quality, baseline track-record, and calibration claim thresholds.",
        ],
    }
    validate_growth_loop(growth_loop)
    return growth_loop


def validate_growth_loop(growth_loop: dict[str, Any]) -> None:
    errors = validate_record(growth_loop, SCHEMA)
    if errors:
        raise TransitCorpusGrowthLoopError(f"transit corpus growth loop schema validation failed: {errors[0]}")
    candidates = growth_loop["candidateUpdates"]
    if [item["candidateCase"] for item in candidates] != CASE_ORDER:
        raise TransitCorpusGrowthLoopError("growth loop candidate coverage drifted")
    append_ready = [item for item in candidates if item["appendDecision"] == "append_ready"]
    if len(append_ready) != 1:
        raise TransitCorpusGrowthLoopError("growth loop should expose one append-ready example")
    ready = append_ready[0]
    if not all(
        ready[key] is True
        for key in [
            "requiredBindingsPresent",
            "forecastBeforeClose",
            "resolvedAfterHorizon",
            "scorePresent",
            "forecastTimeEvidenceBoundaryPreserved",
            "resolutionOnlyEvidenceBoundaryPreserved",
        ]
    ):
        raise TransitCorpusGrowthLoopError("append-ready candidate should satisfy all required checks")
    for item in candidates:
        write = item["appendOnlyWrite"]
        if write["wouldModifyExistingRows"] or write["wouldCreateForecastArtifacts"] or write["wouldCreateResolutionRecords"] or write["wouldCreateScoringRecords"]:
            raise TransitCorpusGrowthLoopError("candidate append writes must not mutate existing rows or create artifacts")
        if write["requiresManualCorpusEditing"]:
            raise TransitCorpusGrowthLoopError("candidate append writes should not require manual corpus editing")
        if item["appendDecision"] != "append_ready" and write["wouldAppendCorpusRow"]:
            raise TransitCorpusGrowthLoopError("only append-ready candidates should append corpus rows")
    ledger_reasons = {row["reasonCode"] for row in growth_loop["exclusionLedger"]}
    expected_reasons = {item["reasonCode"] for item in candidates if item["reasonCode"] != "none"}
    if ledger_reasons != expected_reasons:
        raise TransitCorpusGrowthLoopError("exclusion ledger should cover every excluded or rejected reason")
    progress = growth_loop["progressReadback"]
    if progress["projectedComparableResolved"] != progress["currentComparableResolved"] + progress["appendReadyComparableCount"]:
        raise TransitCorpusGrowthLoopError("projected comparable count drifted")
    if progress["qualityClaimAllowed"] or progress["calibrationClaimAllowed"] or progress["baselineTrackRecordAllowed"]:
        raise TransitCorpusGrowthLoopError("growth loop must keep quality and calibration claims blocked")
    boundary = growth_loop["executionBoundary"]
    if boundary["appendOnlyContractDeclared"] is not True or boundary["normalChecksDeterministicOffline"] is not True:
        raise TransitCorpusGrowthLoopError("growth loop should declare append-only and deterministic offline boundaries")
    for key, value in boundary.items():
        if key in {"appendOnlyContractDeclared", "normalChecksDeterministicOffline"}:
            continue
        if value is not False:
            raise TransitCorpusGrowthLoopError(f"execution boundary {key} should be false")


def summary(growth_loop: dict[str, Any]) -> dict[str, Any]:
    progress = growth_loop["progressReadback"]
    return {
        "transitCorpusGrowthLoopId": growth_loop["transitCorpusGrowthLoopId"],
        "growthMode": growth_loop["growthMode"],
        "currentComparableResolved": progress["currentComparableResolved"],
        "appendReadyComparableCount": progress["appendReadyComparableCount"],
        "projectedComparableResolved": progress["projectedComparableResolved"],
        "remainingForTrackRecord": progress["remainingForTrackRecord"],
        "remainingForCalibration": progress["remainingForCalibration"],
        "candidateUpdates": [
            {
                "candidateCase": item["candidateCase"],
                "appendDecision": item["appendDecision"],
                "reasonCode": item["reasonCode"],
                "nextAction": item["nextAction"],
            }
            for item in growth_loop["candidateUpdates"]
        ],
    }


def write_growth_loop(growth_loop: dict[str, Any]) -> None:
    write_generated(GROWTH_PATH, growth_loop, label="transit corpus growth loop", regen="python3 scripts/generate_transit_corpus_growth_loop.py --write")


def check_growth_loop(growth_loop: dict[str, Any]) -> None:
    check_generated(GROWTH_PATH, growth_loop, label="transit corpus growth loop", regen="python3 scripts/generate_transit_corpus_growth_loop.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one corpus growth candidate")
    parser.add_argument("--check", action="store_true", help="check generated transit corpus growth loop drift")
    parser.add_argument("--write", action="store_true", help="write generated transit corpus growth loop")
    args = parser.parse_args()
    try:
        growth_loop = build_growth_loop()
    except TransitCorpusGrowthLoopError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_growth_loop(growth_loop)
    elif args.check:
        check_growth_loop(growth_loop)
    elif args.case:
        candidate_row = next(item for item in growth_loop["candidateUpdates"] if item["candidateCase"] == args.case)
        sys.stdout.write(render_json(candidate_row))
    else:
        sys.stdout.write(render_json(summary(growth_loop)))


if __name__ == "__main__":
    main()
