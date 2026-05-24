# Release Manifest

Status: implemented as a generated local artifact.

The release manifest summarizes the current local OPE surface in one machine-readable file:

```text
spec/fixtures/generated/release-manifest.generated.json
```

It is generated from committed schemas, generated read indexes, and generated outcome summaries. It does not certify a hosted service, network API, SDK, production live-data workflow, or live calibration claim.

## Commands

Check committed manifest output:

```bash
python3 scripts/generate_release_manifest.py
python3 scripts/ope.py manifest
```

Refresh the manifest:

```bash
python3 scripts/generate_release_manifest.py --write
python3 scripts/ope.py manifest --write
```

## Contents

The manifest records:

- project runtime and package-manager posture
- CI release workflow and commands
- canonical setup, test, release, and CLI commands
- schema file count and schema file paths, including source-policy, source-connector, live-connector-readiness, domain-setup, source-manifest-build, source-intake-handoff, source-handoff-method-gate, source-handoff setup runbook, private setup workflow, private setup request, private setup first-action, first-action runbook, agent bundle, adapter-chain runbook, private source adapter capability, outcome matrix, intake bridge, source-kind selection examples, and source-kind query matrix, source-manifest, field-mapping, source-intake-report, setup-benchmark-gate, setup-method-decision, setup-forecast-run, recalculation-trigger, recalculation-run, evidence-plan, method-registry, method-comparison, method-selection, agent-envelope, adapter protocol-map, forecast-run summary, intake matrix, and runbook contracts
- public read-surface counts from the generated record index
- claim boundaries for the first weather-logistics wedge, including live, pipeline, auto-evidence, and source-handoff fixture outcome counters, and read surfaces that include historical-only baseline forecasts
- explicit non-goals such as network API, hosted service, production agent adapter runtime beyond the local MCP stdio scaffold, production live-data workflow, and live calibration claims
- the live connector readiness schema as an offline contract, without making the integration live probe part of release readiness
- ignored local live captures under `.ope/live/` remaining outside release checks, public read surfaces, track records, and calibration
- source-builder and source-handoff drafts remaining outside forecast artifacts until later setup gates explicitly consume them
- source-handoff method gates remaining non-generating until explicit setup forecast execution consumes an accepted method decision
- source-handoff forecast execution creating artifacts only for confirmed handoff method decisions and blocking all other handoff outcomes
- source-handoff resolution recording one resolved source-handoff outcome without creating a calibration or quality claim
- source-handoff setup runbook guidance remaining local and fixture-bound
- private setup workflow remaining a contract for future source runtimes, not an implemented generic upload/API/database connector
- private setup request routing remaining setup-intent classification without executing source reads
- private setup first-action dispatch remaining a compact non-executing response that may name commands but never runs them
- private setup first-action runbook guidance remaining non-executing and blocked from moving planned, unsafe, unknown, or approval-missing sources into intake
- private setup agent bundles remaining read-only joins over request, action, and runbook records without executing or generating artifacts
- private setup bundle adapter envelopes remaining read-only setup guidance without running source-builder or creating forecast artifacts
- private setup source-builder adapter envelopes remaining caller-approved local-file draft guidance without creating public read, forecast, score, live-fetch, or credential artifacts
- private setup source-handoff adapter envelopes remaining checked next-action guidance without creating public read, forecast, score, live-fetch, or credential artifacts
- private setup method-gate adapter envelopes remaining benchmark and method-decision guidance without creating public read, forecast, score, live-fetch, or credential artifacts
- private setup forecast-execution adapter envelopes creating forecast artifacts only for the confirmed checked handoff, with blocked cases remaining non-generating and no resolution, scoring, live-fetch, or credential artifacts
- private setup forecast readback adapter envelopes using normal forecast card, lifecycle bundle, resolution status, and scoring summary reads rather than a private setup read API
- private setup adapter-chain runbook guidance remaining non-executing and not a source, forecast, resolution, scoring, credential, hosted API, or production runtime surface
- private setup adapter-runbook envelopes remaining read-only guidance and not adapter execution, source reads, forecast creation, resolution, scoring, credential, hosted API, or production runtime support
- private setup adapter conformance matrices remaining checked examples over generated envelopes without executing adapter calls, reading private data, or creating source, forecast, resolution, scoring, credential, live-fetch, hosted API, or production runtime artifacts
- private setup adapter conformance summaries remaining compact read-only guidance without embedding full envelopes, executing adapter calls, or creating source, forecast, resolution, scoring, credential, live-fetch, hosted API, or production runtime artifacts
- private source adapter capability declarations remaining non-executing and credential-free
- private source adapter outcome decisions remaining next-action guidance without creating source, forecast, score, or credential artifacts
- private source adapter intake bridge remaining routing guidance without executing source reads or creating forecast and score artifacts
- private source adapter guidance envelopes remaining read-only joins without source reads, adapter calls, source manifests, forecasts, scores, credentials, live fetches, hosted APIs, or production runtime support
- private source-kind selection examples remaining non-executing guidance without commands, manifests, forecasts, scores, credentials, live fetches, hosted APIs, or production runtime support
- private source-kind selection envelopes remaining read-only selection guidance without executing source-builder, source-handoff, fixture evidence, forecast execution, scoring, source reads, credentials, live fetches, hosted APIs, or production runtime support
- private source-kind query matrices remaining adapter conformance examples without source-intake evidence, forecast artifacts, scoring records, source reads, credentials, live fetches, hosted APIs, or production runtime support

## Guardrails

Normal release checks verify:

- the manifest matches deterministic generated output
- the manifest validates against `spec/release-manifest.schema.json`
- the manifest names the CI workflow and release-check command
- live calibration remains disallowed while comparable resolved outcomes are below the declared threshold
- domain setup contracts are present without turning candidate private setups into production or calibration claims
- source-builder drafts inspect local files without creating public read surfaces or forecast artifacts
- source intake handoffs preserve builder rejection reasons and route accepted drafts only to method gates
- source-handoff method gates bind accepted builder handoffs to setup benchmark and method decisions without creating forecast artifacts
- source-handoff forecast execution preserves handoff, source-intake, benchmark, and method-decision bindings before artifacts are created
- source-handoff resolution preserves those bindings through resolution, scoring, track-record, and forecast-card outputs while comparable outcomes remain below the claim threshold
- source-handoff setup runbook checks preserve safe next actions for confirmed, unconfirmed, insufficient-data, and rejected source cases
- private setup workflow checks preserve domain-agnostic phases, planned-only manual upload/private API/database support, and claim boundaries
- private setup request checks preserve bridge binding, pre-source-read classification, planned-runtime blocking, unsafe-source rejection, and no forecast or score outputs
- private setup first-action checks preserve request binding, sanitized unknown-source and missing-approval errors, non-execution, planned-runtime blocking, and no forecast or score outputs
- private setup first-action runbook checks preserve action binding, status coverage, bad-request playbooks, planned-runtime blocking, source-intake blocking, and no forecast or score outputs
- private setup agent bundle checks preserve request/action/runbook binding, bad-request examples, claim boundaries, source-intake blocking, and no source, forecast, score, live-fetch, or credential outputs
- private setup bundle adapter checks preserve envelope status, request binding, MCP/protocol-map exposure, sanitized missing-bundle errors, and no setup command execution
- private setup source-builder adapter checks preserve caller-approved file inputs, proposed inferred mappings, rejected source cases, sanitized malformed-input errors, MCP/protocol-map exposure, and no forecast, score, live-fetch, credential, or public read-record outputs
- private setup source-handoff adapter checks preserve mapping confirmation, source-intake binding, blocked source cases, MCP/protocol-map exposure, and no forecast, score, live-fetch, credential, or public read-record outputs
- private setup method-gate adapter checks preserve source-handoff, benchmark, and method-decision binding, explicit forecast-execution recommendation only for allowed confirmed handoffs, MCP/protocol-map exposure, and no forecast, score, live-fetch, credential, or public read-record outputs
- private setup forecast-execution adapter checks preserve source-handoff, source-intake, benchmark, method-decision, setup-run, question, evidence, and forecast bindings, generate only the confirmed checked forecast, expose blocked cases through null forecast bindings, and avoid resolution, scoring, live-fetch, and credential outputs
- private setup forecast readback checks preserve `forecast-1102` setup run, source-handoff, method-gate, benchmark, method-decision, resolution, scoring, and sample-size-blocked quality bindings through existing read operations
- private setup adapter-chain runbook checks preserve operation sequence, branch playbooks, readback routing, stop conditions, and no adapter-call execution
- private setup adapter-runbook envelope checks preserve the same operation sequence and readback routing through `agent-call` and MCP without executing adapter calls
- private setup adapter conformance matrix checks preserve phase coverage, payload shapes, sanitized error behavior, artifact-creation boundaries, normal readback routing, and no matrix execution
- private setup adapter conformance summary checks preserve compact counts, operation coverage, matrix binding, artifact boundary, normal readback routing, and no summary execution
- private source adapter checks preserve declaration-only behavior, no secret storage, offline normal checks, and runtime-not-implemented private adapters
- private source adapter outcome checks preserve capability binding, workflow outcome binding, non-execution, and blocked artifact creation
- private source adapter bridge checks preserve outcome-matrix binding, checked entrypoints, confirmation-before-handoff, planned-runtime blocking, unsafe-source rejection, and no forecast or score outputs
- private source adapter guidance envelope checks preserve capability/outcome/bridge bindings, source-kind summary routing, and no source reads, manifests, forecasts, scores, credentials, live fetches, or hosted runtime support
- private source-kind selection checks preserve guidance, first-action, and adapter-chain bindings while keeping planned runtimes, unsupported sources, and unsafe sources out of forecast paths
- private source-kind selection envelope checks preserve the same selection examples through `agent-call` and MCP without executing the recommended path
- private source-kind query matrix checks preserve default full-list, selected source-kind, and unsupported-source adapter response shapes without turning them into execution evidence
- source intake reports classify source and mapping usability without producing forecast artifacts
- setup benchmark gates separate stronger-method fixture execution from quality, calibration, production, and state-of-the-art claims
- setup method decisions explain benchmark-gated stronger selection, baseline fallback, blocked mappings, and rejected intake before forecast artifacts are created
- setup forecast execution creates artifacts only for allowed setup intake and keeps blocked intake non-generating
- recalculation records append updated forecast states for pre-close evidence and reject post-outcome evidence as forecast input
- local live-capture checks validate ignored connector results and source-set drafts without adding them to release artifacts
