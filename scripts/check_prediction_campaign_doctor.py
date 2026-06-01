#!/usr/bin/env python3
"""Check prediction campaign doctor readback invariants."""

from __future__ import annotations

from generate_prediction_campaign_doctor import build_prediction_campaign_doctor


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def queue_by_name(doctor: dict, name: str) -> dict:
    queues = {queue["queueName"]: queue for queue in doctor["queueReadbacks"]}
    if name not in queues:
        raise AssertionError(f"missing queue {name}")
    return queues[name]


def main() -> None:
    doctor = build_prediction_campaign_doctor()
    health = doctor["health"]
    duplicate = doctor["duplicateProtection"]
    recovery = doctor["recoveryPosture"]
    summary = doctor["summary"]
    boundary = doctor["executionBoundary"]

    require(doctor["doctorStatus"] == "actionable_due_run", "doctor should expose a due campaign run")
    require(doctor["domain"] == "weather-transit-delays", "doctor domain drifted")
    require(doctor["bindings"]["campaignId"] == "predictioncampaign-001", "campaign binding drifted")
    require(doctor["bindings"]["runId"] == "predictionrun-1301", "run binding drifted")
    require(doctor["bindings"]["forecastId"] == "forecast-1301", "forecast binding drifted")
    require(
        doctor["bindings"]["predictionCampaignResolutionAttemptId"] == "predictioncampaignresolutionattempt-1301",
        "resolution-attempt binding drifted",
    )

    require(health["now"] == "2026-06-11T07:15:00Z", "doctor default clock drifted")
    require(health["plannedRunCount"] == 4, "planned run count drifted")
    require(health["checkedRunCount"] == 1, "checked campaign job count drifted")
    require(health["dueRunCount"] == 1, "due run count drifted")
    require(health["waitingRunCount"] == 0, "waiting run count drifted")
    require(health["failedRunCount"] == 0, "failed run count drifted")
    require(health["blockedRunCount"] == 1, "blocked run count drifted")
    require(health["appendReadyRunCount"] == 0, "append-ready run count drifted")
    require(health["qualityClaimAllowed"] is False, "doctor must block quality claims")

    due = queue_by_name(doctor, "due_runs")
    require(due["queueStatus"] == "actionable", "due queue status drifted")
    require(due["runIds"] == ["predictionrun-1301"], "due queue run binding drifted")
    require(any("prediction-campaign resolve" in command for command in due["commands"]), "due queue should point to resolve")

    blocked = queue_by_name(doctor, "blocked_runs")
    require(blocked["queueStatus"] == "blocked", "blocked queue status drifted")
    require(blocked["runIds"] == ["predictionrun-1301"], "blocked queue run binding drifted")

    for name in ["failed_runs", "append_ready_runs"]:
        queue = queue_by_name(doctor, name)
        require(queue["queueStatus"] == "empty", f"{name} should be empty")
        require(queue["runCount"] == 0, f"{name} count should be zero")

    for queue in doctor["queueReadbacks"]:
        require(queue["mutatesState"] is False, "doctor queues must not mutate state")
        require(queue["executesResolver"] is False, "doctor queues must not execute resolvers")
        require(queue["createsResolutionArtifacts"] is False, "doctor queues must not create resolutions")
        require(queue["createsScoringRecords"] is False, "doctor queues must not create scoring records")
        require(queue["appendsCorpusEvidence"] is False, "doctor queues must not append corpus evidence")

    require(duplicate["duplicateRiskCount"] == 0, "duplicate risk count drifted")
    require(duplicate["duplicateResolutionBlocked"] is True, "duplicate resolution should stay blocked")
    require(duplicate["duplicateScoringBlocked"] is True, "duplicate scoring should stay blocked")
    require(duplicate["priorEvidenceOverwriteAllowed"] is False, "prior evidence overwrite must stay blocked")

    require(recovery["resumeReadbackAvailable"] is True, "resume readback should be available")
    require(recovery["effectfulResumeImplemented"] is False, "effectful resume should remain blocked")
    require(recovery["interruptedRunStateFound"] is False, "normal checks must not find ignored interrupted state")

    require(summary["doctorReadbackImplemented"] is True, "doctor readback should be implemented")
    require(summary["agentQueueReadbacksImplemented"] is True, "agent queue readbacks should be implemented")
    require(summary["dueRunReadbackImplemented"] is True, "due run readback should be implemented")
    require(summary["failedRunReadbackImplemented"] is True, "failed run readback should be implemented")
    require(summary["appendReadyReadbackImplemented"] is True, "append-ready readback should be implemented")
    require(summary["effectfulResolutionImplemented"] is True, "effectful resolution runtime should be implemented")

    for key, value in boundary.items():
        require(value is False, f"execution boundary {key} should remain false")

    waiting = build_prediction_campaign_doctor(now="2026-06-11T07:14:59Z")
    require(waiting["doctorStatus"] == "waiting", "pre-resolution doctor should wait")
    require(waiting["health"]["dueRunCount"] == 0, "pre-resolution doctor should have no due runs")
    require(waiting["health"]["waitingRunCount"] == 1, "pre-resolution doctor should expose one waiting run")
    require(queue_by_name(waiting, "waiting_runs")["runIds"] == ["predictionrun-1301"], "waiting queue run drifted")

    print("checked prediction campaign doctor")


if __name__ == "__main__":
    main()
