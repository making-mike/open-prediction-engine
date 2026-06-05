# Agent Prediction Manual

Status: checked compact manual surfaced through `agent-implementation-kit`.

This manual is for coding agents asked to add prediction behavior to host software. The shortest correct path is:

1. Detect a decision under uncertainty.
2. Describe the app goal and decision to support.
3. Bind approved source references and source roles.
4. Discover candidate forecast contracts.
5. Validate candidate contracts mechanically.
6. Create a prediction through lifecycle-backed operations.
7. Start the prediction only after validation passes.
8. Run a foreground tick or bounded worker loop.
9. Read a forecast card.
10. Resolve the outcome.
11. Append evidence and score.
12. Inspect calibration and track-record gates.

Every step keeps claim boundaries attached to checked OPE readbacks. The manual does not permit free-form oracle forecasts, raw CRUD writes, hidden live fetches, credential storage, silent deletion, unbounded background loops, or automatic method upgrades.

## CLI Flow Template

```bash
python3 scripts/ope.py agent-implementation-kit --view intake
python3 scripts/ope.py agent-implementation-kit --view candidates
python3 scripts/ope.py agent-implementation-kit --view validation
python3 scripts/ope.py source-bindings
python3 scripts/ope.py source-intake
python3 scripts/ope.py setup-benchmark
python3 scripts/ope.py setup-method
python3 scripts/ope.py setup-forecast
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
```

The concrete forecast IDs above are fixture readbacks. Host integrations should use accepted candidate IDs and lifecycle receipts from their own checked setup.
