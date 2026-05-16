#!/usr/bin/env python3
"""Dependency-free scoring helpers for OPE fixtures."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


EPSILON = 1e-15
EXCLUDED_RESOLUTION_STATUSES = {"ambiguous", "annulled", "disputed", "stale_source"}
SCORABLE_HISTORY_STATES = {"active", "superseded", "reaffirmed", "benchmark_hidden"}


def parse_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def clamp_probability(value: float) -> float:
    return min(1 - EPSILON, max(EPSILON, value))


def binary_brier(probability: float, outcome: bool) -> float:
    target = 1.0 if outcome else 0.0
    return (probability - target) ** 2


def binary_log_loss(probability: float, outcome: bool) -> float:
    p = clamp_probability(probability)
    return -math.log(p if outcome else 1 - p)


def multiclass_brier(probabilities: list[dict[str, Any]], outcome_label: str) -> float:
    total = 0.0
    for item in probabilities:
        target = 1.0 if item["label"] == outcome_label else 0.0
        total += (item["probability"] - target) ** 2
    return total


def multiclass_log_loss(probabilities: list[dict[str, Any]], outcome_label: str) -> float:
    for item in probabilities:
        if item["label"] == outcome_label:
            return -math.log(clamp_probability(item["probability"]))
    raise ValueError(f"outcome label {outcome_label!r} is not in forecast probabilities")


def pinball_loss(q: float, value: float, outcome: float) -> float:
    delta = outcome - value
    return max(q * delta, (q - 1) * delta)


def interval_score(lower: float, upper: float, coverage: float, outcome: float) -> float:
    if lower > upper:
        raise ValueError("interval lower bound must be <= upper bound")
    alpha = 1 - coverage
    if alpha <= 0 or alpha >= 1:
        raise ValueError("coverage must be between 0 and 1")
    score = upper - lower
    if outcome < lower:
        score += (2 / alpha) * (lower - outcome)
    if outcome > upper:
        score += (2 / alpha) * (outcome - upper)
    return score


def score_forecast_output(
    forecast_output: dict[str, Any],
    resolved_outcome: dict[str, Any],
    scoring_rule: str,
) -> float:
    output_type = forecast_output["outputType"]
    if output_type != resolved_outcome["outputType"]:
        raise ValueError(
            f"forecast output type {output_type!r} does not match outcome "
            f"type {resolved_outcome['outputType']!r}"
        )

    if scoring_rule == "brier" and output_type == "binary":
        return binary_brier(forecast_output["probability"], bool(resolved_outcome["value"]))

    if scoring_rule == "log_score" and output_type == "binary":
        return binary_log_loss(forecast_output["probability"], bool(resolved_outcome["value"]))

    if scoring_rule == "multiclass_brier" and output_type == "categorical":
        return multiclass_brier(forecast_output["probabilities"], str(resolved_outcome["value"]))

    if scoring_rule == "log_score" and output_type == "categorical":
        return multiclass_log_loss(forecast_output["probabilities"], str(resolved_outcome["value"]))

    if scoring_rule == "interval_score" and output_type == "interval":
        return interval_score(
            float(forecast_output["lower"]),
            float(forecast_output["upper"]),
            float(forecast_output["coverage"]),
            float(resolved_outcome["value"]),
        )

    if scoring_rule == "pinball_loss" and output_type == "quantile":
        losses = [
            pinball_loss(float(item["q"]), float(item["value"]), float(resolved_outcome["value"]))
            for item in forecast_output["quantiles"]
        ]
        return sum(losses) / len(losses)

    raise ValueError(f"unsupported scoring rule {scoring_rule!r} for output type {output_type!r}")


def time_weighted_history_score(
    history: dict[str, Any],
    resolved_outcome: dict[str, Any],
    scoring_rule: str,
    close_at: str,
) -> float:
    entries = [
        entry
        for entry in history["entries"]
        if entry["state"] in SCORABLE_HISTORY_STATES
    ]
    if not entries:
        raise ValueError("history contains no scorable entries")

    entries = sorted(entries, key=lambda entry: entry["forecastedAt"])
    close_time = parse_timestamp(close_at)
    weighted_total = 0.0
    duration_total = 0.0

    for index, entry in enumerate(entries):
        start = parse_timestamp(entry["forecastedAt"])
        if index + 1 < len(entries):
            end = parse_timestamp(entries[index + 1]["forecastedAt"])
        else:
            end = close_time
        duration = max(0.0, (end - start).total_seconds())
        if duration == 0:
            continue
        score = score_forecast_output(entry["forecastOutput"], resolved_outcome, scoring_rule)
        weighted_total += score * duration
        duration_total += duration

    if duration_total == 0:
        raise ValueError("history entries have zero scoring duration")
    return weighted_total / duration_total


def should_exclude_resolution(resolution: dict[str, Any]) -> bool:
    return resolution["status"] in EXCLUDED_RESOLUTION_STATUSES


def baseline_lift(forecast_score: float, baseline_score: float) -> float:
    return baseline_score - forecast_score


def calibration_buckets(
    pairs: list[tuple[float, bool]],
    bucket_count: int = 10,
) -> list[dict[str, float | int]]:
    if bucket_count <= 0:
        raise ValueError("bucket_count must be positive")
    buckets: list[dict[str, float | int]] = []
    for bucket_index in range(bucket_count):
        lower = bucket_index / bucket_count
        upper = (bucket_index + 1) / bucket_count
        items = []
        for probability, outcome in pairs:
            if bucket_index == bucket_count - 1:
                in_bucket = lower <= probability <= upper
            else:
                in_bucket = lower <= probability < upper
            if in_bucket:
                items.append((probability, outcome))
        count = len(items)
        mean_probability = sum(probability for probability, _ in items) / count if count else 0.0
        observed_frequency = sum(1 for _, outcome in items if outcome) / count if count else 0.0
        buckets.append(
            {
                "lowerProbability": lower,
                "upperProbability": upper,
                "count": count,
                "meanForecastProbability": mean_probability,
                "observedFrequency": observed_frequency,
            }
        )
    return buckets


def track_record_summary(
    *,
    domain: str,
    horizon_bucket: str,
    output_type: str,
    scoring_rule: str,
    scores: list[float],
    baseline_scores: list[float],
    n_ambiguous: int,
    n_annulled: int,
    n_forecasts: int | None = None,
) -> dict[str, Any]:
    n_resolved = len(scores)
    total_forecasts = n_forecasts if n_forecasts is not None else n_resolved + n_ambiguous + n_annulled
    primary_score = sum(scores) / n_resolved if n_resolved else None
    baseline_score = sum(baseline_scores) / len(baseline_scores) if baseline_scores else None
    lift = (
        baseline_lift(primary_score, baseline_score)
        if primary_score is not None and baseline_score is not None
        else None
    )
    return {
        "domain": domain,
        "horizonBucket": horizon_bucket,
        "outputType": output_type,
        "counts": {
            "nForecasts": total_forecasts,
            "nResolved": n_resolved,
            "nAmbiguous": n_ambiguous,
            "nAnnulled": n_annulled,
        },
        "summary": {
            "primaryScoringRule": scoring_rule,
            "primaryScore": primary_score,
            "baselineScore": baseline_score,
            "baselineLift": lift,
        },
    }
