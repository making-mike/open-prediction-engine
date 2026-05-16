# Scoring Rules

This document defines the first scoring conventions for OPE.

All scores in the initial harness use **lower is better**. This keeps Brier score, log loss, pinball loss, interval score, and baseline-lift comparisons easy to interpret.

## Binary Brier Score

For binary forecasts:

```text
Brier = (p - y)^2
```

Where:

- `p` is the forecast probability for `true`
- `y` is `1` when the outcome is true and `0` otherwise

Example:

```text
p = 0.41
y = 1
Brier = (0.41 - 1)^2 = 0.3481
```

## Multiclass Brier Score

For categorical forecasts:

```text
Multiclass Brier = sum((p_i - y_i)^2)
```

Where:

- `p_i` is the forecast probability for category `i`
- `y_i` is `1` for the resolved category and `0` otherwise

OPE does not divide by category count in the first convention. If this changes, it must be a decision-log entry because scores would no longer be comparable.

## Log Loss

For binary forecasts:

```text
LogLoss = -log(p)     when y = 1
LogLoss = -log(1-p)   when y = 0
```

Probabilities are clipped to `[1e-15, 1 - 1e-15]` to avoid infinite scores in bootstrap tooling.

For categorical forecasts:

```text
LogLoss = -log(p_resolved)
```

## Pinball Loss

For quantile forecasts:

```text
Pinball(q, value, outcome) = max(q * (outcome - value), (q - 1) * (outcome - value))
```

The average pinball loss across reported quantiles is used when a forecast reports multiple quantiles.

## Interval Score

For central interval forecasts:

```text
alpha = 1 - coverage
score = upper - lower

if outcome < lower:
  score += (2 / alpha) * (lower - outcome)

if outcome > upper:
  score += (2 / alpha) * (outcome - upper)
```

Lower scores are better. Invalid intervals where `lower > upper` must fail validation.

## Baseline Lift

For lower-is-better scores:

```text
baselineLift = baselineScore - forecastScore
```

Positive lift means the forecast beat the baseline. Negative lift means the forecast underperformed the baseline.

## Time-Weighted Forecast Histories

The first harness supports a simple standing-forecast average:

```text
weightedScore = sum(score_i * duration_i) / sum(duration_i)
```

Duration is the time until the next forecast history entry, or until question close for the final standing forecast.

Forecast entries with states `withdrawn` or `analysis_only` are excluded from scoring unless a future decision explicitly includes them.

## Unscorable Questions

Questions with resolution status `ambiguous`, `annulled`, `disputed`, or `stale_source` must produce `scoreStatus: "excluded"` and `scoringRule: "not_scored"`.

They should still be counted in track-record reports.
