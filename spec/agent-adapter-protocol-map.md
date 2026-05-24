# Agent Adapter Protocol Map

Status: local MCP stdio scaffold implemented; HTTP and queue runtime mappings remain documentation-only.

The protocol map records how the local `agent-call` dispatcher is wrapped by the local MCP stdio scaffold and how future HTTP or queue transports can wrap it without changing OPE record semantics. The generated JSON lives at `spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json` and is validated by `spec/agent-adapter-protocol-map.schema.json`.

## Current Contract

The local dispatcher is the behavioral source of truth:

```bash
python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-602 --question-id question-601
```

The local MCP stdio scaffold exposes the same operation set through `initialize`, `tools/list`, and `tools/call`:

```bash
python3 scripts/ope.py mcp-stdio
```

The protocol map is checked with:

```bash
python3 scripts/ope.py agent-protocol-map --check
python3 scripts/check_agent_adapter_protocol_map.py
python3 scripts/check_mcp_adapter.py
```

Every mapped operation returns `spec/agent-envelope.schema.json`. The local MCP scaffold and future HTTP endpoints or queue workers must preserve the envelope `status`, `exitCode`, `recordBinding`, `state`, `payload`, `error`, and `warnings` fields.

## Operations

| Operation | Side-effect level | Local runtime | MCP tool |
| --- | --- | --- | --- |
| `forecast_request_validation` | validation-only | Implemented | `ope_forecast_request_validation` |
| `evidence_plan` | dry-run generation | Implemented | `ope_evidence_plan` |
| `evidence_trace` | read-only | Implemented | `ope_evidence_trace` |
| `forecast_card` | read-only | Implemented | `ope_forecast_card` |
| `lifecycle_bundle` | read-only | Implemented | `ope_lifecycle_bundle` |
| `private_setup_bundle` | read-only | Implemented | `ope_private_setup_bundle` |
| `private_setup_adapter_runbook` | read-only | Implemented | `ope_private_setup_adapter_runbook` |
| `private_setup_adapter_conformance_summary` | read-only | Implemented | `ope_private_setup_adapter_conformance_summary` |
| `private_source_adapter_guidance` | read-only | Implemented | `ope_private_source_adapter_guidance` |
| `private_source_kind_selection` | read-only | Implemented | `ope_private_source_kind_selection` |
| `private_setup_source_builder` | dry-run generation | Implemented | `ope_private_setup_source_builder` |
| `private_setup_source_handoff` | dry-run generation | Implemented | `ope_private_setup_source_handoff` |
| `private_setup_method_gate` | dry-run generation | Implemented | `ope_private_setup_method_gate` |
| `private_setup_forecast_execution` | forecast execution | Implemented | `ope_private_setup_forecast_execution` |
| `resolution_status` | status-read | Implemented | `ope_resolution_status` |
| `scoring_summary` | scoring-read | Implemented | `ope_scoring_summary` |

## MCP Stdio Scaffold

The generated map assigns deterministic tool names such as `ope_forecast_card` and `ope_scoring_summary`. The local MCP stdio scaffold exposes one tool per operation, keeps arguments minimal, and returns the same agent envelope object as `structuredContent` plus serialized JSON text content.

The scaffold also exposes `ope_forecast_run` for the local fixture-safe run orchestrator. Unlike the sixteen mapped adapter operations, this tool returns `spec/forecast-run-summary.schema.json` instead of an agent envelope.

Credentials must remain in MCP server configuration or host-controlled credential stores. They must not appear in prompt-visible tool arguments, forecast artifacts, provenance metadata, warnings, or returned records. The current scaffold exposes only validation, dry-run, read, status, scoring, setup-guidance, and fixture-safe orchestration tools; it does not expose paid, private-source execution, or production live-fetch work.

## Future HTTP Mapping

The generated map assigns future `POST /agent/...` paths and maps HTTP status from the envelope exit code:

| Envelope exit code | Future HTTP status | Meaning |
| --- | --- | --- |
| `0` | `200` | Success |
| `1` | `500` | Internal adapter failure |
| `2` | `400` | Bad or invalid caller input |
| `3` | `403` | Approval or policy gate |
| `4` | `404` | Missing, denied, conflicting, or mismatched record |
| `5` | `429` | Size, quota, or rate limit |

The envelope remains authoritative even when HTTP status is available. HTTP credentials should stay in transport metadata, not OPE records.

## Future Queue Mapping

The generated map assigns request message types such as `ope.forecast_card.requested` and a common result message type, `ope.agent_envelope.ready`. Future queue workers should carry correlation IDs for operation, request, question, forecast, and envelope records, then emit the same envelope schema.

Queued work must persist approval state. Stale, unapproved, effectful, paid, or privacy-sensitive jobs should fail with an approval or validation envelope instead of silently executing.

## Agent Choice Rules

Use `forecast_card` first when an agent needs a compact probability for a reversible downstream action, including a generated private setup forecast.

Use `evidence_trace` when the caller needs connector-bound source provenance without raw fixture contents or raw diagnostics.

Use `lifecycle_bundle` when the caller needs audit context, provenance, evidence records, forecast history, resolution, and scoring context for normal or setup-generated forecasts.

Use `private_setup_bundle` when an agent needs the next safe setup step for a private setup request without executing source setup or creating forecast records.

Use `private_setup_adapter_runbook` when an agent needs the checked private setup adapter operation sequence, branch playbooks, stop conditions, and readback path without executing adapter calls.

Use `private_setup_adapter_conformance_summary` when an agent needs compact private setup adapter conformance status, phase counts, operation coverage, and artifact boundaries before deciding whether to load the full embedded-envelope matrix.

Use `private_source_adapter_guidance` when an agent needs capability, outcome, and intake-bridge guidance for private source kinds before choosing source-builder, source-handoff confirmation, fixture evidence, wait, replace, or stop paths.

Use `private_source_kind_selection` when an agent needs compact checked examples for choosing the next private source-kind path through the adapter surface without executing that path. Pass optional `sourceKind` to return one selected recommendation; omit it to return the full checked examples list.

Use `private_setup_source_builder` when the private setup bundle routes a local-file setup to caller-approved CSV/JSON inspection and draft manifest/mapping guidance.

Use `private_setup_source_handoff` when source-builder guidance needs checked handoff status, mapping confirmation, source-intake binding, and method-gate readiness without creating forecasts.

Use `private_setup_method_gate` when a confirmed handoff needs setup benchmark, method-decision, selected-method, and explicit forecast-execution readiness guidance without creating forecasts.

Use `private_setup_forecast_execution` when a method gate explicitly allows setup forecast execution. Only the confirmed checked handoff returns forecast artifacts; blocked cases return null forecast bindings and setup next actions.

After `private_setup_forecast_execution` returns a generated forecast, use the returned `forecastId` and `questionId` with `forecast_card`, `lifecycle_bundle`, `resolution_status`, and `scoring_summary`. Do not add a private setup read API for forecast records.

Use `resolution_status` before treating a forecast as resolved or before normal scoring.

Use `scoring_summary` before making quality, baseline-lift, or calibration-sensitive decisions.

## Boundary

This document and the generated map claim only local MCP stdio scaffold support for the sixteen mapped tools. They do not claim HTTP API support, queue support, hosted service support, production live fetching, production agent adapter readiness, private source execution, or state-of-the-art forecast quality. They are implementation instructions for future adapters and a checked guard against protocol drift.
