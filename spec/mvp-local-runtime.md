# MVP Local Runtime

Milestone 80 defines the local MVP release surface as a fixture-ready, agent-readable runtime. The MVP is a local CLI and generated-record surface, not a hosted service, network API, production connector runtime, or calibration claim.

## Happy Path

1. Check setup and release readiness:

```bash
python3 --version
python3 scripts/ope.py smoke
python3 scripts/run_checks.py
python3 scripts/ope.py check
python3 scripts/ope.py agent-implementation-kit --view quickstart
python3 scripts/ope.py developer-adoption --section quickstart
python3 scripts/ope.py agent-integrate --view candidates
python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output
python3 scripts/ope.py pilot-evidence --section summary
python3 scripts/ope.py pilot-session-packet --section sanitization
python3 scripts/ope.py pilot-summary-intake --section rules
python3 scripts/ope.py expansion-readiness --section options
python3 scripts/ope.py repeating-prediction-setup --section summary
python3 scripts/ope.py prediction-campaign plan
python3 scripts/ope.py prediction-campaign plan --count 100 --full-materialization
python3 scripts/ope.py prediction-campaign start
python3 scripts/ope.py prediction-campaign start --view campaign-creation
python3 scripts/ope.py prediction-campaign start --view forecast-schedule
python3 scripts/ope.py prediction-campaign start --view missed-run-policy
python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign start --now 2026-09-18T00:00:00Z --count 100 --full-materialization --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py prediction-campaign forecast-create
python3 scripts/ope.py prediction-campaign forecast-artifact
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign forecast-write --write-local --output-format jsonl
python3 scripts/ope.py prediction-campaign resolve
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers
python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers --outcome-csv .ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv --write-local
python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers
python3 scripts/ope.py prediction-campaign doctor
python3 scripts/ope.py prediction-campaign resume
python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state
python3 scripts/ope.py prediction-campaign append-ready
python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary
python3 scripts/ope.py prediction-campaign append-ready --from-local --run-id predictionrun-1301
python3 scripts/ope.py prediction-campaign append --from-local --run-id predictionrun-1301 --write-local
python3 scripts/ope.py prediction-campaign calibration-status
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view readback
python3 scripts/ope.py prediction-campaign calibration-status --campaign predictioncampaign-001 --from-local-ledger --view pilot
python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle
python3 scripts/ope.py prediction-campaign method-update-gate
python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view decision
python3 scripts/ope.py prediction-campaign method-update-plan
python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command
python3 scripts/ope.py prediction-campaign apply-method-update
python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary
python3 scripts/ope.py prediction-campaign explain
python3 scripts/ope.py prediction-campaign pilot-runbook
python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke
python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status
python3 scripts/ope.py prediction-campaign pilot-readiness
python3 scripts/ope.py prediction-campaign pilot-readiness --view commands
python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001
python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001 --from-local-ledger
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001
python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001
python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z
```

2. Run the private setup summary for the checked local-file path:

```bash
python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed
python3 scripts/ope.py local-source-runtime
```

3. Run the fixture-safe forecast path or read the already generated source-handoff forecast:

```bash
python3 scripts/ope.py forecast-run
python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102
```

4. Resolve, score, and inspect the checked source-handoff outcome:

```bash
python3 scripts/ope.py resolve-source-handoff
python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102
```

5. Read corpus and claim gates:

```bash
python3 scripts/ope.py transit-forward-run-corpus
python3 scripts/ope.py transit-track-record-gate
python3 scripts/ope.py resolution-jobs
python3 scripts/ope.py resolution-runtime-reliability
```

## Machine Interfaces

- CLI: `python3 scripts/ope.py` is the minimum local interface for checks, setup summaries, forecast runs, reads, resolution, scoring, corpus gates, and release manifests.
- Agent envelope: `python3 scripts/ope.py agent-call` returns one schema-bound envelope with status, exit code, record binding, and payload, including campaign plan/status/health/append-readiness/calibration-status readbacks.
- Agent incorporation: `python3 scripts/ope.py agent-integrate` answers what can be forecasted from approved starter context and returns the guided first forecast-card command for the accepted Helsinki case.
- Campaign method-update gate: `python3 scripts/ope.py prediction-campaign method-update-gate` reports method-update readiness without changing probabilities, methods, method weights, registries, or campaign state.
- Campaign method-update plan: `python3 scripts/ope.py prediction-campaign method-update-plan` reports approval, guarded command, rollback, and preflight requirements without mutating state.
- Campaign method-update action: `python3 scripts/ope.py prediction-campaign apply-method-update` and `rollback-method-update` expose guarded local method-binding writes only when `--write-local` is explicit.
- Helsinki pilot runbook: `python3 scripts/ope.py prediction-campaign pilot-runbook` reports the 100-run local pilot sequence, 3-run smoke path, operator status commands, success criteria, abort criteria, and baseline-first method boundary.
- Helsinki pilot readiness: `python3 scripts/ope.py prediction-campaign pilot-readiness` reports checked launch prerequisites, manual operator confirmations, launch commands, and blocked actions before any effectful local pilot write.
- MCP stdio: `python3 scripts/ope.py mcp-stdio` exposes the local dispatcher as MCP tools for MCP-capable hosts.

## Blocked Paths

The MVP intentionally exposes blocked summaries rather than repairing or executing unsafe setup paths:

- `missing_approval` asks for caller approval and creates no forecast artifacts.
- `unconfirmed_mapping` asks for mapping confirmation before method selection.
- `insufficient_data` asks for more comparable rows and positive outcomes.
- `rejected_source` asks for a replacement source.
- `unsafe_source` stops unsafe connector output before source intake.
- `response_too_large` asks the caller to retry with a smaller readback or approved byte budget.
- `local-source-runtime --case credentials_detected` blocks credential-like fields before source intake.
- `local-source-runtime --case unsafe_path` blocks paths outside the approved local source folder.

## Claim Boundary

The local MVP can produce and read checked forecast, resolution, scoring, and corpus artifacts. It cannot claim calibration, broad forecast quality, production live-source use, hosted scheduler execution, arbitrary private API/database parsing beyond the approved local-folder runtime, or a production agent adapter runtime. Normal release checks must remain offline and deterministic.
