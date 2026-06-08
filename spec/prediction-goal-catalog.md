# Prediction Goal Catalog

Status: checked.

Milestone 148 adds a compact catalog of generic host prediction goals so agents can see OPE's reusable setup pattern before they read any reference-domain detail.

Run it locally with:

```bash
python3 scripts/ope.py prediction-goal-catalog
python3 scripts/ope.py prediction-goal-catalog --view summary
python3 scripts/ope.py prediction-goal-catalog --view goals
python3 scripts/ope.py prediction-goal-catalog --goal stockout_risk
python3 scripts/ope.py setup-engine --view examples
python3 scripts/ope.py prediction-goal-catalog --check
```

The catalog includes examples for delivery delay risk, stockout risk, SLA breach risk, demand risk, churn risk, seaport berth availability, weather-sensitive operations, and public transit disruption risk. Each example uses the same classification vocabulary as `setup-engine`: `forecastable`, `needs_clarification`, `blocked`, or `rejected`.

Forecastable and needs-clarification examples list required source roles, a baseline candidate, resolution source, forecast-card fields, and the first safe host action. Blocked and rejected examples stop before source intake or forecast execution and explain the blocker.

This catalog teaches setup shape. It does not create forecast artifacts, fetch live data, provide a hosted runtime, store credentials or raw private rows, or make calibration or forecast-quality claims.
