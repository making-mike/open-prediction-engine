#!/usr/bin/env python3
"""Generate or check the local MVP usage trace read model."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from generate_agent_pilot_validation import build_agent_pilot_validation
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "local-usage-trace"
TRACE_PATH = GENERATED / "ope-local-usage-trace.generated.json"
SCHEMA = SPEC / "local-usage-trace.schema.json"
GENERATED_AT = "2026-06-10T06:45:00Z"

EVENT_ORDER = [
    "local_file_setup_readback",
    "unsafe_source_block",
    "forecast_run_readback",
    "forecast_card_read",
    "agent_call_forecast_card",
    "mcp_protocol_map_read",
    "release_surface_smoke",
    "response_too_large_readback",
    "claim_gate_readback",
    "agent_pilot_validation_read",
]


class LocalUsageTraceError(Exception):
    pass


def record_binding(
    *,
    forecast_id: str | None = None,
    question_id: str | None = None,
    record_type: str | None = None,
    record_id: str | None = None,
    source_case: str | None = None,
) -> dict[str, Any]:
    return {
        "forecastId": forecast_id,
        "questionId": question_id,
        "recordType": record_type,
        "recordId": record_id,
        "sourceCase": source_case,
    }


def trace(
    *,
    elapsed_ms: int,
    exit_code: int,
    response_bytes: int,
    response_size_class: str,
    sanitized_error_class: str | None = None,
) -> dict[str, Any]:
    return {
        "elapsedMs": elapsed_ms,
        "exitCode": exit_code,
        "responseBytes": response_bytes,
        "responseSizeClass": response_size_class,
        "sanitizedErrorClass": sanitized_error_class,
    }


def privacy() -> dict[str, bool]:
    return {
        "localOnly": True,
        "liveFetch": False,
        "rawPromptStored": False,
        "rawTranscriptStored": False,
        "privateRowsStored": False,
        "credentialsStored": False,
    }


def event(
    *,
    index: int,
    source_case: str,
    actor: str,
    interface: str,
    event_class: str,
    command: str,
    outcome: str,
    binding: dict[str, Any],
    trace_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "eventId": f"localusageevent-{index:03d}",
        "occurredAt": GENERATED_AT,
        "actor": actor,
        "interface": interface,
        "eventClass": event_class,
        "command": command,
        "outcome": outcome,
        "recordBinding": {**binding, "sourceCase": source_case},
        "trace": trace_row,
        "privacy": privacy(),
        "deterministicFixture": True,
    }


def build_events() -> list[dict[str, Any]]:
    return [
        event(
            index=1,
            source_case="local_file_setup_readback",
            actor="agent",
            interface="cli",
            event_class="setup",
            command="python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
            outcome="success",
            binding=record_binding(
                forecast_id="forecast-1102",
                question_id="question-1102",
                record_type="private-setup-orchestrator",
                record_id="privatesetuporchestratorrun-001",
            ),
            trace_row=trace(elapsed_ms=420, exit_code=0, response_bytes=1850, response_size_class="standard"),
        ),
        event(
            index=2,
            source_case="unsafe_source_block",
            actor="agent",
            interface="cli",
            event_class="blocked_path",
            command="python3 scripts/ope.py private-setup-orchestrator --case unsafe_source",
            outcome="blocked",
            binding=record_binding(record_type="private-setup-orchestrator", record_id="privatesetuporchestratorrun-007"),
            trace_row=trace(
                elapsed_ms=390,
                exit_code=0,
                response_bytes=1450,
                response_size_class="standard",
                sanitized_error_class="blocked_unsafe",
            ),
        ),
        event(
            index=3,
            source_case="forecast_run_readback",
            actor="agent",
            interface="cli",
            event_class="forecast_run",
            command="python3 scripts/ope.py forecast-run",
            outcome="success",
            binding=record_binding(
                forecast_id="forecast-602",
                question_id="question-601",
                record_type="forecast-run-summary",
                record_id="forecast-run-601",
            ),
            trace_row=trace(elapsed_ms=260, exit_code=0, response_bytes=2600, response_size_class="standard"),
        ),
        event(
            index=4,
            source_case="forecast_card_read",
            actor="developer",
            interface="cli",
            event_class="readback",
            command="python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            outcome="success",
            binding=record_binding(
                forecast_id="forecast-1102",
                question_id="question-1102",
                record_type="forecast-card",
                record_id="forecastcard-1102",
            ),
            trace_row=trace(elapsed_ms=95, exit_code=0, response_bytes=3200, response_size_class="standard"),
        ),
        event(
            index=5,
            source_case="agent_call_forecast_card",
            actor="agent",
            interface="agent_call",
            event_class="agent_call",
            command="python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
            outcome="success",
            binding=record_binding(
                forecast_id="forecast-1102",
                question_id="question-1102",
                record_type="agent-envelope",
                record_id="agentenvelope-forecast-card-1102",
            ),
            trace_row=trace(elapsed_ms=130, exit_code=0, response_bytes=3800, response_size_class="standard"),
        ),
        event(
            index=6,
            source_case="mcp_protocol_map_read",
            actor="mcp_host",
            interface="mcp_stdio",
            event_class="mcp_stdio",
            command="python3 scripts/ope.py agent-protocol-map",
            outcome="success",
            binding=record_binding(record_type="agent-adapter-protocol-map", record_id="agentadapterprotocolmap-001"),
            trace_row=trace(elapsed_ms=120, exit_code=0, response_bytes=2400, response_size_class="standard"),
        ),
        event(
            index=7,
            source_case="release_surface_smoke",
            actor="local_check",
            interface="checker",
            event_class="release_surface_smoke",
            command="python3 scripts/check_mvp_release_surface.py",
            outcome="success",
            binding=record_binding(record_type="release-manifest", record_id="releasemanifest-001"),
            trace_row=trace(elapsed_ms=1900, exit_code=0, response_bytes=36, response_size_class="compact"),
        ),
        event(
            index=8,
            source_case="response_too_large_readback",
            actor="agent",
            interface="cli",
            event_class="blocked_path",
            command="python3 scripts/ope.py private-setup-orchestrator --case response_too_large",
            outcome="blocked",
            binding=record_binding(record_type="private-setup-orchestrator", record_id="privatesetuporchestratorrun-008"),
            trace_row=trace(
                elapsed_ms=380,
                exit_code=0,
                response_bytes=720,
                response_size_class="oversized_blocked",
                sanitized_error_class="response_too_large",
            ),
        ),
        event(
            index=9,
            source_case="claim_gate_readback",
            actor="developer",
            interface="cli",
            event_class="claim_gate",
            command="python3 scripts/ope.py transit-track-record-gate",
            outcome="success",
            binding=record_binding(record_type="transit-baseline-track-record-gate", record_id="transitbaselinetrackrecordgate-001"),
            trace_row=trace(elapsed_ms=210, exit_code=0, response_bytes=4200, response_size_class="standard"),
        ),
        event(
            index=10,
            source_case="agent_pilot_validation_read",
            actor="local_check",
            interface="checker",
            event_class="validation_pack",
            command="python3 scripts/ope.py agent-pilot-validation",
            outcome="success",
            binding=record_binding(record_type="agent-pilot-validation", record_id="agentpilotvalidation-001"),
            trace_row=trace(elapsed_ms=520, exit_code=0, response_bytes=2200, response_size_class="standard"),
        ),
    ]


def build_trace_summary(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in events:
        rows[item["interface"]].append(item)
    summary = []
    for interface in ["cli", "agent_call", "mcp_stdio", "checker"]:
        group = rows[interface]
        total_elapsed = sum(item["trace"]["elapsedMs"] for item in group)
        summary.append(
            {
                "interface": interface,
                "eventCount": len(group),
                "successCount": sum(1 for item in group if item["outcome"] == "success"),
                "blockedCount": sum(1 for item in group if item["outcome"] == "blocked"),
                "sanitizedErrorCount": sum(1 for item in group if item["trace"]["sanitizedErrorClass"] not in {None, "none"}),
                "averageElapsedMs": int(total_elapsed / len(group)) if group else 0,
                "maxResponseBytes": max((item["trace"]["responseBytes"] for item in group), default=0),
            }
        )
    return summary


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def build_aggregate(events: list[dict[str, Any]]) -> dict[str, Any]:
    success = sum(1 for item in events if item["outcome"] == "success")
    blocked = sum(1 for item in events if item["outcome"] == "blocked")
    sanitized_errors = sum(1 for item in events if item["trace"]["sanitizedErrorClass"] not in {None, "none"})
    forecast_capable = [item for item in events if item["eventClass"] in {"setup", "forecast_run"}]
    forecast_success = [item for item in forecast_capable if item["outcome"] == "success" and item["recordBinding"]["forecastId"]]
    read_events = [item for item in events if item["eventClass"] in {"readback", "agent_call", "mcp_stdio", "blocked_path", "claim_gate"}]
    read_success = [item for item in read_events if item["outcome"] == "success"]
    return {
        "totalEvents": len(events),
        "successfulEvents": success,
        "blockedEvents": blocked,
        "sanitizedErrorEvents": sanitized_errors,
        "localOnlyEvents": sum(1 for item in events if item["privacy"]["localOnly"]),
        "forecastCompletionRate": rate(len(forecast_success), len(forecast_capable)),
        "agentReadSuccessRate": rate(len(read_success), len(read_events)),
        "blockedPathFrequency": rate(blocked, len(events)),
        "normalChecksUseLiveNetwork": False,
        "hostedTelemetryEnabled": False,
    }


def build_metric_readbacks(aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "metricId": "agent_forecast_completion_rate",
            "description": "Share of forecast-capable local MVP events that produced a forecast binding.",
            "numerator": 2,
            "denominator": 2,
            "value": aggregate["forecastCompletionRate"],
            "interpretation": "Checked MVP setup and forecast-run examples both produce forecast bindings.",
        },
        {
            "metricId": "agent_read_success_rate",
            "description": "Share of readback-like local events that returned usable output instead of a blocked path.",
            "numerator": 4,
            "denominator": 6,
            "value": aggregate["agentReadSuccessRate"],
            "interpretation": "Successful readbacks are visible while unsafe and oversized paths remain explicit blocked signals.",
        },
        {
            "metricId": "blocked_path_frequency",
            "description": "Share of checked local events that intentionally stop before forecast or readback completion.",
            "numerator": aggregate["blockedEvents"],
            "denominator": aggregate["totalEvents"],
            "value": aggregate["blockedPathFrequency"],
            "interpretation": "Blocked path frequency is a usability signal, not a runtime failure rate.",
        },
        {
            "metricId": "local_only_privacy_rate",
            "description": "Share of checked trace events that stay local-only and store no private rows, credentials, prompts, or transcripts.",
            "numerator": aggregate["localOnlyEvents"],
            "denominator": aggregate["totalEvents"],
            "value": rate(aggregate["localOnlyEvents"], aggregate["totalEvents"]),
            "interpretation": "The checked trace model remains local-only and privacy-preserving.",
        },
    ]


def build_local_usage_trace() -> dict[str, Any]:
    manifest = build_manifest()
    pilot = build_agent_pilot_validation()
    events = build_events()
    aggregate = build_aggregate(events)
    trace_model = {
        "localUsageTraceId": "localusagetrace-001",
        "generatedAt": GENERATED_AT,
        "scope": "local_mvp_usage_trace",
        "traceMode": "checked_synthetic_local_trace",
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "agentPilotValidationId": pilot["agentPilotValidationId"],
            "mvpRunbookPath": manifest["mvpLocalRuntime"]["runbookPath"],
            "normalCheckCommand": "python3 scripts/run_checks.py",
        },
        "eventLog": events,
        "traceSummary": build_trace_summary(events),
        "aggregateReadbacks": aggregate,
        "productMetricReadbacks": build_metric_readbacks(aggregate),
        "executionBoundary": {
            "executesCommands": False,
            "collectsHostedTelemetry": False,
            "writesRuntimeLog": False,
            "readsPrivateData": False,
            "storesPrompts": False,
            "storesRawTranscripts": False,
            "storesCredentials": False,
            "fetchesLiveData": False,
            "usesSyntheticCheckedEventsOnly": True,
            "normalChecksDeterministicOffline": True,
            "localOnly": True,
        },
        "warnings": [
            "The local usage trace is a checked synthetic read model; it does not collect telemetry or write runtime logs.",
            "Elapsed time and response-size fields are bounded examples for product metrics, not measured analytics.",
            "Blocked unsafe and response-too-large rows are expected usability signals, not hidden forecast failures.",
            "Normal checks stay deterministic and offline; live connector captures remain explicit opt-in commands.",
        ],
    }
    validate_local_usage_trace(trace_model)
    return trace_model


def validate_local_usage_trace(trace_model: dict[str, Any]) -> None:
    errors = validate_record(trace_model, SCHEMA)
    if errors:
        raise LocalUsageTraceError(f"local usage trace schema validation failed: {errors[0]}")
    events = trace_model["eventLog"]
    if [item["recordBinding"]["sourceCase"] for item in events] != EVENT_ORDER:
        raise LocalUsageTraceError("local usage trace event coverage drifted")
    interfaces = {item["interface"] for item in events}
    if interfaces != {"cli", "agent_call", "mcp_stdio", "checker"}:
        raise LocalUsageTraceError("local usage trace interface coverage drifted")
    classes = {item["eventClass"] for item in events}
    required_classes = {"setup", "forecast_run", "readback", "blocked_path", "release_surface_smoke", "agent_call", "mcp_stdio", "claim_gate", "validation_pack"}
    if classes != required_classes:
        raise LocalUsageTraceError("local usage trace event class coverage drifted")
    for item in events:
        privacy_flags = item["privacy"]
        if privacy_flags["localOnly"] is not True:
            raise LocalUsageTraceError("local usage trace events should be local-only")
        for key in ("liveFetch", "rawPromptStored", "rawTranscriptStored", "privateRowsStored", "credentialsStored"):
            if privacy_flags[key] is not False:
                raise LocalUsageTraceError(f"privacy flag {key} should be false")
        if item["deterministicFixture"] is not True:
            raise LocalUsageTraceError("local usage trace events should be deterministic fixtures")
    boundary = trace_model["executionBoundary"]
    for key, value in boundary.items():
        if key in {"usesSyntheticCheckedEventsOnly", "normalChecksDeterministicOffline", "localOnly"}:
            if value is not True:
                raise LocalUsageTraceError(f"execution boundary {key} should be true")
        elif value is not False:
            raise LocalUsageTraceError(f"execution boundary {key} should be false")
    aggregate = trace_model["aggregateReadbacks"]
    if aggregate["totalEvents"] != len(events):
        raise LocalUsageTraceError("aggregate total event count drifted")
    if aggregate["hostedTelemetryEnabled"] is not False:
        raise LocalUsageTraceError("hosted telemetry should remain disabled")
    if aggregate["normalChecksUseLiveNetwork"] is not False:
        raise LocalUsageTraceError("normal checks should stay offline")


def summary(trace_model: dict[str, Any]) -> dict[str, Any]:
    aggregate = trace_model["aggregateReadbacks"]
    return {
        "localUsageTraceId": trace_model["localUsageTraceId"],
        "traceMode": trace_model["traceMode"],
        "totalEvents": aggregate["totalEvents"],
        "forecastCompletionRate": aggregate["forecastCompletionRate"],
        "agentReadSuccessRate": aggregate["agentReadSuccessRate"],
        "blockedPathFrequency": aggregate["blockedPathFrequency"],
        "hostedTelemetryEnabled": aggregate["hostedTelemetryEnabled"],
        "events": [
            {
                "sourceCase": item["recordBinding"]["sourceCase"],
                "interface": item["interface"],
                "eventClass": item["eventClass"],
                "outcome": item["outcome"],
                "forecastId": item["recordBinding"]["forecastId"],
                "sanitizedErrorClass": item["trace"]["sanitizedErrorClass"],
            }
            for item in trace_model["eventLog"]
        ],
    }


def write_trace(trace_model: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    TRACE_PATH.write_text(render_json(trace_model), encoding="utf-8")
    print("generated local usage trace")


def check_trace(trace_model: dict[str, Any]) -> None:
    expected = render_json(trace_model)
    if not TRACE_PATH.exists():
        print(f"missing local usage trace: {TRACE_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_local_usage_trace.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = TRACE_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"local usage trace drift: {TRACE_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_local_usage_trace.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked local usage trace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", choices=EVENT_ORDER, help="print one local usage trace event")
    parser.add_argument("--check", action="store_true", help="check generated local usage trace drift")
    parser.add_argument("--write", action="store_true", help="write generated local usage trace")
    args = parser.parse_args()
    try:
        trace_model = build_local_usage_trace()
    except LocalUsageTraceError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_trace(trace_model)
    elif args.check:
        check_trace(trace_model)
    elif args.event:
        event_row = next(item for item in trace_model["eventLog"] if item["recordBinding"]["sourceCase"] == args.event)
        sys.stdout.write(render_json(event_row))
    else:
        sys.stdout.write(render_json(summary(trace_model)))


if __name__ == "__main__":
    main()
