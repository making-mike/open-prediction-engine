#!/usr/bin/env python3
"""Check local MVP usage trace invariants."""

from __future__ import annotations

from generate_local_usage_trace import EVENT_ORDER, build_local_usage_trace


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    trace_model = build_local_usage_trace()
    events = trace_model["eventLog"]
    aggregate = trace_model["aggregateReadbacks"]

    require([item["recordBinding"]["sourceCase"] for item in events] == EVENT_ORDER, "usage events should stay in checked order")
    require(aggregate["totalEvents"] == 20, "usage trace should expose twenty checked events")
    require(aggregate["successfulEvents"] == 18, "usage trace success count drifted")
    require(aggregate["blockedEvents"] == 2, "usage trace blocked count drifted")
    require(aggregate["sanitizedErrorEvents"] == 2, "usage trace sanitized error count drifted")
    require(aggregate["forecastCompletionRate"] == 1.0, "forecast completion rate drifted")
    require(aggregate["agentReadSuccessRate"] == 0.6667, "agent read success rate drifted")
    require(aggregate["blockedPathFrequency"] == 0.1, "blocked path frequency drifted")
    require(aggregate["hostedTelemetryEnabled"] is False, "hosted telemetry must remain disabled")
    require(aggregate["normalChecksUseLiveNetwork"] is False, "normal checks should stay offline")

    interfaces = {row["interface"] for row in trace_model["traceSummary"]}
    require(interfaces == {"cli", "agent_call", "mcp_stdio", "checker"}, "trace summary interface coverage drifted")

    metrics = {row["metricId"]: row for row in trace_model["productMetricReadbacks"]}
    require(metrics["agent_forecast_completion_rate"]["value"] == 1.0, "forecast completion metric drifted")
    require(metrics["agent_read_success_rate"]["value"] == 0.6667, "read success metric drifted")
    require(metrics["blocked_path_frequency"]["value"] == 0.1, "blocked path metric drifted")
    require(metrics["local_only_privacy_rate"]["value"] == 1.0, "privacy metric drifted")

    blocked = [item for item in events if item["outcome"] == "blocked"]
    require({item["trace"]["sanitizedErrorClass"] for item in blocked} == {"blocked_unsafe", "response_too_large"}, "blocked events should have sanitized classes")
    campaign_events = [item for item in events if item["eventClass"] == "campaign"]
    require(len(campaign_events) == 10, "usage trace should include ten campaign lifecycle events")
    require(
        [item["recordBinding"]["sourceCase"] for item in campaign_events]
        == [
            "campaign_start",
            "campaign_forecast_created",
            "campaign_resolve_due",
            "campaign_resolver_executed",
            "campaign_append_ready",
            "campaign_appended",
            "campaign_calibration_threshold_met",
            "campaign_paused",
            "campaign_resumed",
            "campaign_stopped",
        ],
        "campaign usage event order drifted",
    )
    for item in events:
        privacy = item["privacy"]
        require(privacy["localOnly"] is True, "events should be local-only")
        for key in ("liveFetch", "rawPromptStored", "rawTranscriptStored", "privateRowsStored", "credentialsStored"):
            require(privacy[key] is False, f"privacy flag {key} should remain false")
        require(item["deterministicFixture"] is True, "events should be deterministic fixtures")
        require(item["command"].startswith("python3 scripts/") or item["command"].startswith("python3 scripts/check_"), "events should use local commands")

    boundary = trace_model["executionBoundary"]
    require(boundary["usesSyntheticCheckedEventsOnly"] is True, "trace should use synthetic checked events")
    require(boundary["normalChecksDeterministicOffline"] is True, "trace should be deterministic offline")
    require(boundary["localOnly"] is True, "trace should be local-only")
    for key in [
        "executesCommands",
        "collectsHostedTelemetry",
        "writesRuntimeLog",
        "readsPrivateData",
        "storesPrompts",
        "storesRawTranscripts",
        "storesCredentials",
        "fetchesLiveData",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should remain false")

    print("checked local usage trace")


if __name__ == "__main__":
    main()
