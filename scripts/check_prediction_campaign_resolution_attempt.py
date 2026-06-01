#!/usr/bin/env python3
"""Check prediction campaign resolution-attempt invariants."""

from __future__ import annotations

from pathlib import Path
import tempfile

from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact
from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from generate_prediction_campaign_resolution_attempt import build_prediction_campaign_resolution_attempt
from ope_fixtures import render_json
import prediction_campaign_resolution_runtime as resolution_runtime
from prediction_campaign_forecast_write_runtime import build_campaign_state, build_run_state


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    attempt = build_prediction_campaign_resolution_attempt()
    bindings = attempt["bindings"]
    target = attempt["resolverTarget"]
    guards = attempt["attemptGuards"]
    result = attempt["attemptResult"]
    source = attempt["sourceFetchMetadata"]
    command = attempt["commandSurface"]
    summary = attempt["summary"]
    duplicate = attempt["duplicateSafety"]
    boundary = attempt["executionBoundary"]

    require(attempt["attemptCase"]["caseKey"] == "due_open", "default attempt case drifted")
    require(attempt["attemptStatus"] == "dry_run_due_ready", "default attempt should select a due dry-run")
    require(attempt["executionMode"] == "dry_run", "default attempt must remain dry-run")
    require(attempt["domain"] == "weather-transit-delays", "resolution attempt domain drifted")
    require(
        attempt["predictionCampaignResolutionAttemptId"] == "predictioncampaignresolutionattempt-1301",
        "resolution attempt id should bind to the selected run",
    )
    require(bindings["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(bindings["runId"] == "predictionrun-1301", "run binding drifted")
    require(bindings["forecastId"] == "forecast-1301", "forecast binding drifted")
    require(bindings["questionId"] == "question-1301", "question binding drifted")
    require(bindings["resolutionId"] == "resolution-1301", "resolution binding drifted")
    require(bindings["scoringReportId"] == "scoring-1301", "scoring binding drifted")

    require(target["due"] is True, "default resolution attempt should be due")
    require(target["runStatus"] == "due_resolution", "default run status drifted")
    require(target["questionStatus"] == "open", "campaign forecast should be unresolved")
    require(target["resolutionEligibleAt"] == "2026-06-11T07:15:00Z", "resolution due time drifted")
    require(target["runStatePath"].startswith(".ope/live/prediction-campaigns/"), "run state path drifted")
    require(target["forecastArtifactPath"].endswith("/forecast-1301.json"), "forecast artifact path drifted")

    require(len(guards) == 6, "resolution attempt guard count drifted")
    require(sum(1 for guard in guards if guard["guardStatus"] == "pass") == 4, "dry-run due attempt pass guards drifted")
    require(any(guard["guardStatus"] == "warn" for guard in guards), "dry-run due attempt should warn about execution")
    require(not any(guard["blocksResolve"] for guard in guards), "dry-run due attempt should not block readback")

    require(result["resultStatus"] == "dry_run_ready", "dry-run due result status drifted")
    require(result["failureCategory"] == "none", "dry-run due result should not record a failure")
    require(result["retryable"] is True, "dry-run due result should be retryable with explicit execution")
    require(result["resolutionArtifactsCreated"] is False, "dry-run must not create resolution artifacts")
    require(result["scoringRecordsCreated"] is False, "dry-run must not create scoring records")

    require(source["fetchAttempted"] is False, "default attempt must not fetch outcome sources")
    require(source["liveNetworkUsed"] is False, "default attempt must not use live network")
    require(source["sanitizedOnly"] is True, "source metadata must stay sanitized")
    require(command["command"] == "python3 scripts/ope.py prediction-campaign resolve", "command drifted")
    for flag in ["--run-id", "--now", "--attempt-case", "--execute-resolvers", "--output-format", "--view"]:
        require(flag in command["acceptedFlags"], f"{flag} should be documented by the resolution-attempt surface")
    for flag in ["--write-local", "--outcome-csv", "--missing-outcome"]:
        require(flag in command["acceptedFlags"], f"{flag} should be documented by the effectful resolver surface")
    require(command["explicitResolverFlagRequired"] is True, "resolver flag should be explicit")
    require(command["normalChecksExecuteResolver"] is False, "normal checks must not execute resolvers")

    require(summary["resolutionAttemptReadbackImplemented"] is True, "attempt readback should be implemented")
    require(summary["dueRunSelected"] is True, "default attempt should select a due run")
    require(summary["resolverExecutionRequested"] is False, "default attempt should not request resolver execution")
    require(summary["resolverExecutionImplemented"] is True, "resolver execution runtime should be implemented")
    require(summary["duplicateSafetyImplemented"] is True, "duplicate safety summary drifted")
    require(duplicate["terminalResolutionBlocked"] is True, "terminal resolution should be blocked")
    require(duplicate["terminalScoringBlocked"] is True, "terminal scoring should be blocked")
    require(duplicate["excludedResolutionBlocked"] is True, "excluded resolution should be blocked")
    require(duplicate["duplicateResolutionBlocked"] is True, "duplicate resolution should be blocked")
    require(duplicate["duplicateScoringBlocked"] is True, "duplicate scoring should be blocked")
    require(duplicate["priorEvidenceOverwriteAllowed"] is False, "prior evidence overwrite must stay blocked")

    require(boundary["requiresExplicitResolverFlag"] is True, "execution boundary should require explicit resolver flag")
    for key, value in boundary.items():
        if key == "requiresExplicitResolverFlag":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    execute_attempt = build_prediction_campaign_resolution_attempt(execute_resolvers=True)
    require(
        execute_attempt["attemptStatus"] == "blocked_missing_outcome_source",
        "execute-requested attempt should block on missing outcome source",
    )
    require(execute_attempt["executionMode"] == "execute_requested", "execute-requested mode drifted")
    require(
        execute_attempt["attemptResult"]["failureCategory"] == "source_unavailable",
        "execute-requested failure category drifted",
    )
    require(
        any(guard["blocksResolve"] for guard in execute_attempt["attemptGuards"]),
        "execute-requested attempt should include a blocking guard",
    )
    require(
        execute_attempt["executionBoundary"]["executesResolvers"] is False,
        "execute-requested checked attempt without --write-local still must not execute resolvers",
    )

    source_ready = build_prediction_campaign_resolution_attempt(
        execute_resolvers=True,
        outcome_csv=".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv",
    )
    require(
        source_ready["attemptStatus"] == "dry_run_execute_ready",
        "declared outcome source should make explicit execution ready for --write-local",
    )
    require(source_ready["attemptResult"]["retryAfter"] == "with_explicit_write_local", "source-ready retry drifted")
    require(source_ready["summary"]["resolutionArtifactsCreated"] is False, "source-ready dry-run must not write")

    waiting_attempt = build_prediction_campaign_resolution_attempt(now="2026-06-11T07:14:59Z")
    require(waiting_attempt["attemptStatus"] == "not_due_wait", "not-due attempt status drifted")
    require(waiting_attempt["resolverTarget"]["due"] is False, "not-due target should not be due")
    require(waiting_attempt["attemptResult"]["failureCategory"] == "not_due", "not-due failure category drifted")

    later_run = build_prediction_campaign_resolution_attempt(run_id="predictionrun-1302", now="2026-06-12T07:15:00Z")
    require(later_run["bindings"]["runId"] == "predictionrun-1302", "custom run binding drifted")
    require(
        later_run["predictionCampaignResolutionAttemptId"] == "predictioncampaignresolutionattempt-1302",
        "custom run attempt id drifted",
    )
    require(later_run["bindings"]["forecastId"] == "forecast-1302", "custom run forecast binding drifted")

    terminal_cases = {
        "already_resolved": ("blocked_already_terminal", "already_terminal", "resolved"),
        "ambiguous": ("blocked_already_terminal", "already_terminal", "ambiguous"),
        "annulled": ("blocked_already_terminal", "already_terminal", "annulled"),
        "missed": ("blocked_excluded_run", "excluded_run", "missed"),
        "blocked_duplicate": ("blocked_duplicate_run", "duplicate_blocked", "blocked_duplicate"),
    }
    for case, (expected_status, expected_failure, expected_run_status) in terminal_cases.items():
        case_attempt = build_prediction_campaign_resolution_attempt(case=case, execute_resolvers=True)
        require(case_attempt["attemptCase"]["simulatedReadback"] is True, f"{case} should be a simulated checked readback")
        require(case_attempt["attemptStatus"] == expected_status, f"{case} attempt status drifted")
        require(case_attempt["attemptResult"]["failureCategory"] == expected_failure, f"{case} failure category drifted")
        require(case_attempt["attemptResult"]["retryable"] is False, f"{case} must not be retryable")
        require(case_attempt["resolverTarget"]["runStatus"] == expected_run_status, f"{case} run status drifted")
        require(case_attempt["attemptResult"]["resolutionArtifactsCreated"] is False, f"{case} must not create resolution")
        require(case_attempt["attemptResult"]["scoringRecordsCreated"] is False, f"{case} must not create scoring")
        require(
            any(guard["blocksResolve"] for guard in case_attempt["attemptGuards"]),
            f"{case} should include a blocking duplicate/terminal/excluded guard",
        )

    check_effectful_runtime()
    print("checked prediction campaign resolution attempt")


def write_json(root: Path, relative_path: str, data: dict) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")


def outcome_rows() -> str:
    rows = ["service_date,network,geography,service_window,captured_at,trip_id,stop_id,delay_seconds"]
    for index in range(1, 19):
        delay = 340 if index in {2, 7} else 120
        rows.append(
            "2026-06-11,hsl-surface,helsinki,morning_peak,"
            f"2026-06-11T05:{index:02d}:00Z,trip-{index:03d},stop-{index:03d},{delay}"
        )
    return "\n".join(rows) + "\n"


def seed_local_forecast(root: Path) -> str:
    plan = build_prediction_campaign_forecast_write(embed_source_records=True)
    records = build_prediction_campaign_forecast_artifact()
    target = plan["targetState"]
    write_json(root, target["questionPath"], records["question"])
    write_json(root, target["evidencePacketPath"], records["evidence"])
    write_json(root, target["forecastArtifactPath"], records["artifact"])
    write_json(root, target["forecastHistoryPath"], records["history"])
    write_json(root, target["runStatePath"], build_run_state(plan, "2026-06-11T00:01:00Z"))
    write_json(root, target["campaignStatePath"], build_campaign_state(plan, "2026-06-11T00:01:00Z"))
    outcome_path = root / ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv"
    outcome_path.parent.mkdir(parents=True, exist_ok=True)
    outcome_path.write_text(outcome_rows(), encoding="utf-8")
    return ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv"


def check_effectful_runtime() -> None:
    original_root = resolution_runtime.ROOT
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        resolution_runtime.ROOT = root
        try:
            outcome_csv = seed_local_forecast(root)
            result = resolution_runtime.execute_local_resolution_write(
                run_id="predictionrun-1301",
                now="2026-06-11T07:15:00Z",
                outcome_csv=outcome_csv,
            )
            require(result["resolutionWriteStatus"] == "local_resolution_scored", "effectful resolution status drifted")
            require(result["outcomeSummary"]["scoreStatus"] == "scored", "effectful scoring status drifted")
            require(result["outcomeSummary"]["outcomeLabel"] == "no", "effectful outcome label drifted")
            require(result["outcomeSummary"]["observationCount"] == 18, "effectful observation count drifted")
            require(result["summary"]["resolutionArtifactsCreated"] is True, "runtime should create resolution records")
            require(result["summary"]["scoringRecordsCreated"] is True, "runtime should create scoring records")
            require(result["executionBoundary"]["appendsCorpusEvidence"] is False, "runtime must not append evidence")
            repeat = resolution_runtime.execute_local_resolution_write(
                run_id="predictionrun-1301",
                now="2026-06-11T07:15:00Z",
                outcome_csv=outcome_csv,
            )
            require(
                repeat["resolutionWriteStatus"] == "local_resolution_scored_already_present",
                "effectful resolution should be idempotent",
            )
        finally:
            resolution_runtime.ROOT = original_root


if __name__ == "__main__":
    main()
