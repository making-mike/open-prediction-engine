#!/usr/bin/env python3
"""Generate or check prediction campaign calibration-status readbacks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from generate_prediction_campaign_manifest import build_prediction_campaign_manifest
from generate_repeating_prediction_setup import build_repeating_prediction_setup
from generate_transit_baseline_track_record_gate import (
    TransitBaselineTrackRecordGateError,
    build_gate,
    load_local_campaign_ledger,
)
from ope_fixtures import compact_json, render_json, validate_and_emit
from ope_schema import SPEC, validate_record
from ope_scoring import calibration_buckets


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "prediction-campaign-calibration-status"
OUTPUT_PATH = GENERATED / "weather-transit-delay-campaign-calibration-status.generated.json"
SCHEMA = SPEC / "prediction-campaign-calibration-status.schema.json"
GENERATED_AT = "2026-05-31T03:00:00Z"
DEFAULT_CASE = "below_threshold"
CALIBRATION_CASES = [
    "below_threshold",
    "threshold_met",
    "too_many_exclusions",
    "post_calibration_restart",
]


def round_float(value: float) -> float:
    return round(value, 10)


def expected_calibration_error(buckets: list[dict[str, Any]], sample_size: int) -> float:
    if sample_size == 0:
        return 0.0
    total = 0.0
    for bucket in buckets:
        total += (
            bucket["count"]
            / sample_size
            * abs(bucket["meanForecastProbability"] - bucket["observedFrequency"])
        )
    return round_float(total)


def selected_campaign_example(setup: dict[str, Any], case_key: str) -> dict[str, Any]:
    matches = [example for example in setup["campaignExamples"] if example["caseKey"] == case_key]
    if len(matches) != 1:
        raise ValueError(f"expected one repeating setup example for {case_key}, found {len(matches)}")
    return matches[0]


def scenario_values(gate: dict[str, Any], calibration_case: str) -> dict[str, Any]:
    samples = gate["sampleSummary"]
    if calibration_case == "below_threshold":
        comparable = samples["resolvedComparableSampleSize"]
        excluded = samples["excludedSampleSize"]
    elif calibration_case == "threshold_met":
        comparable = 100
        excluded = 8
    elif calibration_case == "too_many_exclusions":
        comparable = 100
        excluded = 60
    elif calibration_case == "post_calibration_restart":
        comparable = 100
        excluded = 10
    else:
        raise ValueError(f"unknown calibration case: {calibration_case}")
    total = comparable + excluded
    exclusion_rate = round_float(excluded / total) if total else 0
    return {
        "resolvedComparableSampleSize": comparable,
        "scoredSampleSize": comparable,
        "excludedSampleSize": excluded,
        "minimumComparableResolvedForTrackRecord": samples["minimumComparableResolvedForTrackRecord"],
        "minimumComparableResolvedForCalibration": samples["minimumComparableResolvedForCalibration"],
        "maxExclusionRateForCalibrationClaim": 0.25,
        "exclusionRate": exclusion_rate,
        "sourceOutcomeProvenanceComplete": True,
        "campaignLedgerPath": gate["campaignLedger"]["ledgerPath"],
    }


def provenance_complete(row: dict[str, Any]) -> bool:
    required_keys = [
        "runStatePath",
        "forecastArtifactPath",
        "evidencePacketPath",
        "forecastHistoryPath",
        "resolutionRecordPath",
        "scoringReportPath",
        "sourcePolicyId",
        "evidencePacketId",
        "historyId",
        "resolutionRecordId",
        "scoringReportId",
    ]
    return all(isinstance(row.get(key), str) and row[key] not in {"", "none"} for key in required_keys)


def local_ledger_values(gate: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
    comparable_rows = ledger["comparableRows"]
    excluded_rows = ledger["excludedRows"]
    comparable = len(comparable_rows)
    excluded = len(excluded_rows)
    total = comparable + excluded
    exclusion_rate = round_float(excluded / total) if total else 0
    samples = gate["sampleSummary"]
    return {
        "resolvedComparableSampleSize": comparable,
        "scoredSampleSize": len([row for row in comparable_rows if row.get("scoreStatus") == "scored"]),
        "excludedSampleSize": excluded,
        "minimumComparableResolvedForTrackRecord": samples["minimumComparableResolvedForTrackRecord"],
        "minimumComparableResolvedForCalibration": samples["minimumComparableResolvedForCalibration"],
        "maxExclusionRateForCalibrationClaim": 0.25,
        "exclusionRate": exclusion_rate,
        "sourceOutcomeProvenanceComplete": all(provenance_complete(row) for row in comparable_rows),
        "campaignLedgerPath": ledger["bindings"]["ledgerPath"],
    }


def calibration_status_for(values: dict[str, Any], calibration_case: str) -> str:
    if values["resolvedComparableSampleSize"] < values["minimumComparableResolvedForCalibration"]:
        return "not_enough_resolved_comparable_outcomes"
    if values["exclusionRate"] > values["maxExclusionRateForCalibrationClaim"]:
        return "blocked_too_many_exclusions"
    if not values["sourceOutcomeProvenanceComplete"]:
        return "blocked_incomplete_provenance"
    if calibration_case == "post_calibration_restart":
        return "post_calibration_restart_ready"
    return "ready"


def synthetic_pairs(sample_size: int) -> list[tuple[float, bool]]:
    event_count = max(0, min(sample_size, round(sample_size * 0.29)))
    return [(0.25, True)] * event_count + [(0.25, False)] * (sample_size - event_count)


def rows_to_pairs(rows: list[dict[str, Any]]) -> list[tuple[float, bool]]:
    return [
        (float(row["forecastProbability"]), row["outcomeLabel"] == "yes")
        for row in rows
        if row.get("scoreStatus") == "scored" and row.get("outcomeLabel") in {"yes", "no"}
    ]


def score_average(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if row.get(key) is not None]
    return round_float(sum(values) / len(values)) if values else 0.0


def summary_buckets(pairs: list[tuple[float, bool]]) -> list[dict[str, Any]]:
    return [
        {
            "lowerProbability": round_float(float(bucket["lowerProbability"])),
            "upperProbability": round_float(float(bucket["upperProbability"])),
            "count": int(bucket["count"]),
            "meanForecastProbability": round_float(float(bucket["meanForecastProbability"])),
            "observedFrequency": round_float(float(bucket["observedFrequency"])),
        }
        for bucket in calibration_buckets(pairs, bucket_count=10)
    ]


def calibration_summary(
    status: str,
    values: dict[str, Any],
    *,
    comparable_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if status not in {"ready", "post_calibration_restart_ready"}:
        return None
    rows = comparable_rows or []
    pairs = rows_to_pairs(rows) if rows else synthetic_pairs(values["resolvedComparableSampleSize"])
    buckets = summary_buckets(pairs)
    event_rate = round_float(sum(1 for _, outcome in pairs if outcome) / len(pairs)) if pairs else 0.0
    if rows:
        primary_score = score_average(rows, "primaryScore")
        baseline_score = score_average(rows, "baselineScore")
    else:
        primary_score = round_float(
            sum((probability - (1.0 if outcome else 0.0)) ** 2 for probability, outcome in pairs) / len(pairs)
        )
        baseline_score = primary_score
    return {
        "calibrationSummaryId": "calibration-1301",
        "sampleSize": values["resolvedComparableSampleSize"],
        "expectedCalibrationError": expected_calibration_error(buckets, len(pairs)),
        "bucketCount": 10,
        "primaryScore": primary_score,
        "baselineScore": baseline_score,
        "baselineLift": round_float(baseline_score - primary_score),
        "eventRate": event_rate,
        "buckets": buckets,
        "confidenceCaveats": [
            "Calibration is measured on local campaign evidence only and does not update probabilities.",
            "Horizon, source-policy, and outcome provenance must remain complete before any claim is made.",
        ],
        "measurementOnly": True,
        "automaticProbabilityUpdateAllowed": False,
    }


def cycle_state(status: str, policy: dict[str, Any], calibration_case: str) -> dict[str, Any]:
    threshold_reached = status in {"ready", "post_calibration_restart_ready", "blocked_too_many_exclusions"}
    if status == "not_enough_resolved_comparable_outcomes":
        state = "collecting_evidence"
        action = "continue_collecting_until_threshold"
        pause_until = "none"
        next_cycle_id = "none"
    elif status == "blocked_too_many_exclusions":
        state = "needs_review"
        action = "review_exclusions_before_claim"
        pause_until = "none"
        next_cycle_id = "none"
    elif calibration_case == "post_calibration_restart":
        state = "pause_scheduled"
        action = policy["action"]
        pause_until = "2026-06-25T07:30:00Z"
        next_cycle_id = "predictioncycle-002"
    else:
        state = "threshold_met_pending_policy"
        action = policy["action"]
        pause_until = "none"
        next_cycle_id = "none"
    return {
        "cycleState": state,
        "thresholdReached": threshold_reached,
        "thresholdReachedAt": "2026-06-11T07:30:00Z" if threshold_reached else "none",
        "postCalibrationAction": action,
        "pauseUntil": pause_until,
        "nextCycleId": next_cycle_id,
        "writesCampaignState": False,
    }


def warnings_for(status: str) -> list[str]:
    warnings = [
        "Calibration status is a readback and does not tune, retrain, or update forecast probabilities.",
        "Normal checks do not read ignored local ledgers or mutate campaign cycle state.",
        "Stronger method selection remains behind a later explicit method-update gate.",
    ]
    if status == "not_enough_resolved_comparable_outcomes":
        warnings.append("Comparable resolved sample size is below the declared calibration threshold.")
    if status == "blocked_too_many_exclusions":
        warnings.append("Exclusion rate is too high for a calibration claim even though the comparable threshold is met.")
    if status == "blocked_incomplete_provenance":
        warnings.append("At least one comparable row is missing source or outcome provenance required for calibration.")
    return warnings


def pilot_summary(status: str, values: dict[str, Any]) -> dict[str, Any]:
    track_ready = values["resolvedComparableSampleSize"] >= values["minimumComparableResolvedForTrackRecord"]
    calibration_ready = status in {"ready", "post_calibration_restart_ready"}
    return {
        "implementationEvidence": "Campaign execution evidence exists only as local implementation evidence until appended rows are reviewed.",
        "trackRecordEvidence": (
            "Track-record sample threshold is met for the selected local campaign ledger."
            if track_ready
            else "Track-record sample threshold is not met for the selected campaign evidence."
        ),
        "calibrationEvidence": (
            "Calibration evidence is measurement-ready and remains read-only."
            if calibration_ready
            else f"Calibration evidence is blocked with status {status}."
        ),
        "qualityClaim": (
            "Quality claims still require human review and the separate method-update gate."
            if calibration_ready
            else "Quality and calibration claims remain blocked."
        ),
    }


def build_prediction_campaign_calibration_status(
    *,
    calibration_case: str = DEFAULT_CASE,
    campaign: str | None = None,
    from_local_ledger: bool = False,
) -> dict[str, Any]:
    if calibration_case not in CALIBRATION_CASES:
        raise ValueError(f"unknown calibration status case: {calibration_case}")
    if from_local_ledger and campaign is None:
        raise ValueError("--from-local-ledger requires --campaign")
    manifest = build_prediction_campaign_manifest()
    campaign_id = campaign or manifest["campaign"]["campaignId"]
    if campaign_id != manifest["campaign"]["campaignId"]:
        raise ValueError(f"unsupported campaign: {campaign_id}")
    setup = build_repeating_prediction_setup()
    case_key = (
        "post_calibration_restart_campaign"
        if calibration_case == "post_calibration_restart"
        else manifest["campaign"]["recurrenceCaseKey"]
    )
    example = selected_campaign_example(setup, case_key)
    policy = example["postCalibrationPolicy"]
    local_ledger = None
    if from_local_ledger:
        gate = build_gate()
        local_ledger = load_local_campaign_ledger(campaign_id)
        values = local_ledger_values(gate, local_ledger)
        ledger_case = "local_evidence_ledger"
    else:
        ledger_case = "comparable_scored" if calibration_case != "below_threshold" else "excluded_missing_outcome"
        gate = build_gate(campaign=campaign_id, ledger_case=ledger_case)
        values = scenario_values(gate, calibration_case)
    status = calibration_status_for(values, calibration_case)
    comparable_rows = local_ledger["comparableRows"] if local_ledger else None
    summary = calibration_summary(status, values, comparable_rows=comparable_rows)
    cycle = cycle_state(status, policy, calibration_case)
    return {
        "predictionCampaignCalibrationStatusId": "predictioncampaigncalibrationstatus-001",
        "generatedAt": GENERATED_AT,
        "calibrationStatus": status,
        "calibrationCase": "local_ledger" if from_local_ledger else calibration_case,
        "domain": manifest["domain"],
        "bindings": {
            "predictionCampaignManifestId": manifest["predictionCampaignManifestId"],
            "repeatingPredictionSetupId": manifest["bindings"]["repeatingPredictionSetupId"],
            "transitBaselineTrackRecordGateId": gate["transitBaselineTrackRecordGateId"],
            "campaignId": campaign_id,
            "cycleId": manifest["campaign"]["cycleId"],
            "sourcePolicyId": manifest["bindings"]["sourcePolicyId"],
            "recurrenceCaseKey": case_key,
        },
        "thresholdReadback": {
            **values,
            "trackRecordStatus": (
                "ready"
                if values["resolvedComparableSampleSize"] >= values["minimumComparableResolvedForTrackRecord"]
                else "not_enough_resolved_comparable_outcomes"
            ),
            "calibrationStatus": status,
            "campaignLedgerIncluded": from_local_ledger or gate["campaignLedger"]["included"],
            "campaignLedgerCase": ledger_case,
        },
        "calibrationReadback": {
            "summaryGenerated": summary is not None,
            "reasonCode": "threshold_met" if summary is not None else status,
            "calibrationSummary": summary,
            "measurementOnly": True,
            "automaticModelTuningAllowed": False,
            "automaticMethodChangeAllowed": False,
        },
        "pilotSummary": pilot_summary(status, values),
        "postCalibrationPolicy": {
            "action": policy["action"],
            "delay": policy["delay"],
            "nextCycleRule": policy["nextCycleRule"],
            "automaticMethodChangeAllowed": policy["automaticMethodChangeAllowed"],
        },
        "cycleState": cycle,
        "commandSurface": {
            "command": "python3 scripts/ope.py prediction-campaign calibration-status",
            "acceptedFlags": ["--campaign", "--from-local-ledger", "--calibration-case", "--output-format", "--view"],
            "defaultMode": "checked_calibration_status_readback",
            "capturedStdoutMode": "json",
            "normalChecksMutateState": False,
        },
        "summary": {
            "calibrationStatusReadbackImplemented": True,
            "calibrationSummaryGenerated": summary is not None,
            "postCalibrationContinuationDecisionImplemented": True,
            "methodUpdateImplemented": False,
            "writesCampaignState": False,
            "qualityClaimAllowed": status in {"ready", "post_calibration_restart_ready"},
            "calibrationClaimAllowed": status in {"ready", "post_calibration_restart_ready"},
            "recommendedNextAction": (
                "Continue collecting comparable resolved outcomes."
                if status == "not_enough_resolved_comparable_outcomes"
                else "Review exclusions before making any calibration claim."
                if status == "blocked_too_many_exclusions"
                else "Apply the post-calibration policy explicitly; do not change forecast method behavior automatically."
            ),
        },
        "executionBoundary": {
            "readsIgnoredLiveState": from_local_ledger,
            "writesIgnoredLiveState": False,
            "writesCampaignState": False,
            "fetchesLiveData": False,
            "executesResolvers": False,
            "createsCalibrationSummaryBelowThreshold": False,
            "updatesForecastProbabilities": False,
            "changesForecastMethod": False,
            "startsNextCycle": False,
        },
        "warnings": warnings_for(status),
    }


def print_view(record: dict[str, Any], view: str, output_format: str) -> None:
    views = {
        "calibration": record,
        "thresholds": record["thresholdReadback"],
        "readback": record["calibrationReadback"],
        "pilot": record["pilotSummary"],
        "policy": record["postCalibrationPolicy"],
        "cycle": record["cycleState"],
        "summary": record["summary"],
        "boundary": record["executionBoundary"],
    }
    data = views[view]
    if output_format == "human":
        thresholds = record["thresholdReadback"]
        print(
            f"{record['calibrationStatus']} comparable={thresholds['resolvedComparableSampleSize']} "
            f"excluded={thresholds['excludedSampleSize']} action={record['cycleState']['postCalibrationAction']}"
        )
        return
    if output_format == "jsonl":
        print(compact_json(data), end="")
        return
    print(render_json(data), end="")


def check_or_write(data: dict[str, Any], *, write: bool) -> None:
    validate_and_emit(
        data,
        SCHEMA,
        OUTPUT_PATH,
        write=write,
        label="prediction campaign calibration status",
        regen="python3 scripts/generate_prediction_campaign_calibration_status.py --write",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="refresh generated calibration status")
    parser.add_argument("--check", action="store_true", help="check generated calibration status drift")
    parser.add_argument(
        "--calibration-case",
        choices=CALIBRATION_CASES,
        default=DEFAULT_CASE,
        help="checked calibration-status case",
    )
    parser.add_argument("--campaign", help="explicit campaign id when reading a local evidence ledger")
    parser.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="read the ignored local campaign evidence ledger for calibration status",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        default="json",
        help="format for command output",
    )
    parser.add_argument(
        "--view",
        choices=["calibration", "thresholds", "readback", "pilot", "policy", "cycle", "summary", "boundary"],
        default="calibration",
        help="print one prediction campaign calibration-status view",
    )
    args = parser.parse_args()
    if (args.write or args.check) and (
        args.calibration_case != DEFAULT_CASE or args.campaign or args.from_local_ledger
    ):
        raise SystemExit("custom calibration inputs cannot be combined with --write or --check")
    try:
        record = build_prediction_campaign_calibration_status(
            calibration_case=args.calibration_case,
            campaign=args.campaign,
            from_local_ledger=args.from_local_ledger,
        )
    except (ValueError, TransitBaselineTrackRecordGateError) as exc:
        raise SystemExit(str(exc)) from exc
    if args.write or args.check:
        check_or_write(record, write=args.write)
        return
    errors = validate_record(record, SCHEMA)
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print_view(record, args.view, args.output_format)


if __name__ == "__main__":
    main()
