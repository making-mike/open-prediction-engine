# Agent Adapter Contract

Status: local contract, fixture examples, local dispatcher, and local MCP stdio scaffold.

OPE should be easy for agents to call without coupling the engine to a single transport. The adapter contract is therefore a thin JSON envelope over existing OPE records and local commands. It does not redefine forecast, evidence, resolution, scoring, or calibration semantics.

## Envelope

The envelope schema is `spec/agent-envelope.schema.json`. Generated examples live under `spec/fixtures/generated/agent-adapter/`.

Each envelope carries:

- adapter identity: local CLI and local MCP stdio now, future HTTP/queue surfaces later
- operation: forecast request validation, evidence plan, evidence trace, forecast card, lifecycle bundle, private setup bundle, private setup adapter runbook, private source adapter guidance, private source-kind selection, private setup source-builder, private setup source-handoff, private setup method-gate, private setup forecast execution, resolution status, or scoring summary
- input reference and record binding fields
- lifecycle state fields that agents can read without parsing every nested record
- status and standardized exit code
- payload for successful calls or a sanitized error object for failed calls
- warnings that preserve fixture-mode and claim-boundary context

The current local examples bind to the `data: auto` weather-logistics fixture request and the resolved auto-evidence forecast `forecast-602`.

## Protocol Mapping

The checked protocol mapping is `spec/agent-adapter-protocol-map.md` plus the generated record `spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json`.

It lists the local CLI operation, MCP tool name, future HTTP endpoint, future queue message type, input fields, side-effect level, exit-code mapping, approval gate, and credential boundary for each adapter operation. The local MCP stdio scaffold implements the mapped MCP tools. HTTP and queue remain mapping-only.

Validate it with:

```bash
python3 scripts/ope.py agent-protocol-map --check
python3 scripts/check_agent_adapter_protocol_map.py
```

## Exit Codes

Adapter implementations should preserve these meanings across transports:

| Exit code | Meaning | Typical error codes |
| --- | --- | --- |
| `0` | Success | none |
| `1` | Internal adapter failure | `internal_error` |
| `2` | Bad or invalid caller input | `bad_request`, `validation_failed` |
| `3` | Policy or approval gate blocks execution | `approval_required` |
| `4` | Missing, denied, conflicting, or mismatched record | `not_found`, `access_denied`, `binding_mismatch`, `conflict` |
| `5` | Local limit exceeded | `response_too_large`, `rate_limited` |

Error payloads must be sanitized. They may expose stable error codes and safe messages, but not absolute local paths, raw stack traces, secrets, prompt text, provider diagnostics, or hidden tool arguments.

The schema enforces the basic status shape: successful envelopes use `status: ok`, `exitCode: 0`, an object payload, and `error: null`; error envelopes use `status: error`, a nonzero exit code, `payload: null`, and an error object. Local checks also verify duplicated operation names and key record bindings so a valid-looking envelope cannot silently point to a different forecast or question.

## Capability Matrix

| Capability | Local CLI | Local MCP stdio | Future HTTP | Future queue |
| --- | --- | --- | --- | --- |
| Validate forecast request | Implemented, validation-only | Implemented as stdio tool | Wrap same contract | Accept validation task |
| Build evidence plan | Implemented, dry-run | Implemented as stdio tool | Wrap same contract | Accept dry-run task |
| Gather auto evidence | Fixture replay only | Not exposed as production live fetch | Future policy-bound endpoint | Future controlled job |
| Generate forecast | Fixture-mode local scripts | Not exposed as production live forecast | Future bounded endpoint | Future controlled job |
| Read evidence trace | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read forecast card | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read lifecycle bundle | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read private setup bundle | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read private setup adapter runbook | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read private source adapter guidance | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read private source-kind selection | Implemented, read-only | Implemented as stdio tool | GET/read wrapper | Read result message |
| Draft local-file source setup | Implemented, caller-approved files only | Implemented as stdio tool | Future approval-gated wrapper | Future controlled draft task |
| Read source-handoff next actions | Implemented, checked handoff cases only | Implemented as stdio tool | Future confirmation-gated wrapper | Future controlled handoff task |
| Read setup method-gate guidance | Implemented, checked method-gate cases only | Implemented as stdio tool | Future benchmark-gated wrapper | Future controlled method-gate task |
| Run setup forecast execution | Implemented, checked fixture cases only | Implemented as stdio tool | Future approval-gated wrapper | Future controlled forecast task |
| Read resolution status | Implemented through envelope fixture | Implemented as stdio tool | GET/read wrapper | Read result message |
| Read scoring summary | Implemented through envelope fixture | Implemented as stdio tool | GET/read wrapper | Read result message |
| Live fetch | Not implemented for production | Must be approval and source-policy gated | Must be approval and source-policy gated | Must be approval and source-policy gated |
| Paid or privacy-sensitive action | Not implemented | Must be approval gated | Must be approval gated | Must be approval gated |

## Transcript Example

An agent validates a request:

```bash
python3 scripts/ope.py request --input spec/fixtures/requests/auto-weather-logistics-request.json
```

It then inspects the adapter envelope examples:

```bash
python3 scripts/ope.py agent-envelopes
```

An MCP-capable local host can launch the stdio scaffold:

```bash
python3 scripts/ope.py mcp-stdio
```

The scaffold supports MCP `initialize`, `tools/list`, and `tools/call`. Each mapped tool returns the OPE agent envelope as structured content and serialized text content.

The scaffold also exposes `ope_forecast_run`, which returns `spec/forecast-run-summary.schema.json` for the fixture-safe run orchestrator. That tool is a compact workflow summary, not a replacement for the single-operation envelope contract.

For one terminal-agent operation, it calls the dispatcher:

```bash
python3 scripts/ope.py agent-call \
  --operation forecast_card \
  --forecast-id forecast-602 \
  --question-id question-601
```

The dispatcher returns exactly one `agent-envelope.schema.json` response and exits with the envelope's `exitCode`. Error cases such as missing records, binding mismatches, approval-required requests, and response-size limits return sanitized error envelopes on stdout.

For private setup guidance, an agent can read the bundle through the same envelope contract:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_bundle \
  --private-setup-request-id privatesetuprequest-001
```

The payload is the private setup agent bundle. It remains guidance-only: it does not read private source files, run source-builder, fetch live data, create forecast artifacts, score outcomes, or store credentials.

For the full private setup adapter sequence, an agent can read the checked adapter-chain runbook through the envelope surface:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_adapter_runbook
```

The payload is the generated private setup adapter-chain runbook. It lists operation order, branch playbooks, stop conditions, and normal forecast readback routing, but it does not execute adapter calls, read private sources, create forecast artifacts, resolve outcomes, score forecasts, fetch live data, or store credentials.

For compact adapter conformance status, an agent can read the summary before loading the full embedded-envelope matrix:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_adapter_conformance_summary
```

The payload is the compact private setup adapter conformance summary. It references the full matrix, records phase counts, operation coverage, artifact boundaries, sanitized-error coverage, and read-surface details, but it does not embed every envelope or execute adapter calls.

Before choosing a source-kind path, an agent can read private source adapter guidance through the same envelope surface:

```bash
python3 scripts/ope.py agent-call \
  --operation private_source_adapter_guidance
```

The payload joins the private source adapter capability declaration, outcome matrix, and intake bridge. It summarizes which source kinds are available, approval-gated, planned-only, unsupported, or unsafe, but it does not execute source reads, adapter calls, manifest creation, forecast creation, scoring, live fetching, credential handling, or hosted runtime work.

For compact next-path examples, an agent can read private source-kind selection through the same envelope surface:

```bash
python3 scripts/ope.py agent-call \
  --operation private_source_kind_selection
```

The payload returns the checked source-kind selection examples. It binds source adapter guidance, private setup first actions, and the adapter-chain runbook, but it does not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, live fetching, credential handling, or hosted runtime work.

To avoid parsing the full examples list, the agent may ask for one selected recommendation:

```bash
python3 scripts/ope.py agent-call \
  --operation private_source_kind_selection \
  --source-kind private_api
```

That response returns `runtimeStatus: selected_example_only`, `requestedSourceKind`, `availableSourceKinds`, and one `selectedExample`. Unknown source kinds return a sanitized `bad_request` envelope with `payload: null`.

For local-file setup, the agent can ask the adapter to inspect only caller-approved files or a checked fixture case:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_source_builder \
  --private-setup-request-id privatesetuprequest-001 \
  --source-builder-case local_draft
```

The payload includes `sourceManifestBuild`, and when inspection succeeds, draft `sourceManifest` and `fieldMapping` objects. Rejected inputs such as secrets, unsupported formats, oversized files, or leakage indicators return an ok envelope with a rejected build payload, not forecast artifacts. Malformed adapter inputs return sanitized errors.

After source-builder guidance, the agent can inspect checked source-handoff next actions:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_source_handoff \
  --private-setup-request-id privatesetuprequest-001 \
  --source-handoff-case confirmed_builder_draft
```

The payload includes `sourceIntakeHandoff`, source-builder and source-intake bindings, mapping confirmation state, and method-gate readiness. Only the confirmed accepted handoff may proceed toward setup benchmark and method gates. The adapter still does not run source intake, create forecasts, score outcomes, fetch live data, or store credentials.

After a confirmed source-handoff, the agent can inspect setup benchmark and method-decision guidance:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_method_gate \
  --private-setup-request-id privatesetuprequest-001 \
  --method-gate-case confirmed_builder_draft
```

The payload includes `sourceHandoffMethodGate`, `setupBenchmarkGate`, `setupMethodDecision`, and a compact `adapterGuidance` object. It may recommend explicit setup forecast execution only when the checked benchmark and method decision allow it. The adapter still does not create forecast artifacts, score outcomes, fetch live data, or store credentials.

When method gates allow execution, the agent can run the checked setup forecast execution step through the same envelope surface:

```bash
python3 scripts/ope.py agent-call \
  --operation private_setup_forecast_execution \
  --private-setup-request-id privatesetuprequest-001 \
  --forecast-execution-case confirmed_builder_draft
```

The payload includes `setupForecastRun`, source-handoff/method-decision bindings, and forecast artifacts only for the confirmed handoff case. Blocked cases return `runStatus: blocked`, null forecast IDs, and next-action guidance. The operation does not resolve outcomes, score forecasts, fetch live data, accept raw private data, or store credentials.

After a generated setup forecast, agents read the returned forecast through the normal forecast operations:

```bash
python3 scripts/ope.py agent-call \
  --operation forecast_card \
  --forecast-id forecast-1102 \
  --question-id question-1102
```

The same `forecastId` and `questionId` may be used with `lifecycle_bundle`, `resolution_status`, and `scoring_summary`. Those reads preserve setup forecast run, source-handoff, benchmark, method-decision, resolution, scoring, and quality-claim bindings without adding a private setup read API.

If `forecast_request_validation` returns `decisionStatus: accepted`, the agent can inspect the dry-run plan:

```bash
python3 scripts/ope.py evidence-plan
```

After fixture-mode forecast generation and resolution are checked, the agent reads the compact card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-602 --question-id question-601
```

If the agent needs source provenance, it reads the connector-bound evidence trace:

```bash
python3 scripts/ope.py read --record-type evidence-trace --id forecast-602 --question-id question-601
```

If the card is enough for the downstream decision, the agent uses the card's probability, baseline, resolution status, score, request binding, and quality warnings. If it needs full lifecycle audit context, it reads the lifecycle bundle:

```bash
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-602 --question-id question-601
```

If `qualityClaim.status` is `not_enough_resolved_auto_evidence_outcomes`, the agent should avoid claiming live calibration or state-of-the-art performance. It may act only if the caller's policy allows provisional fixture-mode evidence, or escalate to a human or a richer evidence-gathering workflow.

## Boundary

The adapter contract, local dispatcher, and local MCP stdio scaffold are not an HTTP API, SDK, hosted service, production queue worker, production live-fetch workflow, or production agent adapter runtime. They are thin local JSON boundaries that future adapters can wrap without changing OPE's record contracts.
