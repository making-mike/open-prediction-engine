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
- schema file count and schema file paths, including source-policy, source-connector, live-connector-readiness, domain-setup, source-manifest-build, source-intake-handoff, source-handoff-method-gate, source-handoff setup runbook, private setup workflow, private source adapter capability, outcome matrix, and intake bridge, source-manifest, field-mapping, source-intake-report, setup-benchmark-gate, setup-method-decision, setup-forecast-run, recalculation-trigger, recalculation-run, evidence-plan, method-registry, method-comparison, method-selection, agent-envelope, adapter protocol-map, forecast-run summary, intake matrix, and runbook contracts
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
- private source adapter capability declarations remaining non-executing and credential-free
- private source adapter outcome decisions remaining next-action guidance without creating source, forecast, score, or credential artifacts
- private source adapter intake bridge remaining routing guidance without executing source reads or creating forecast and score artifacts

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
- private source adapter checks preserve declaration-only behavior, no secret storage, offline normal checks, and runtime-not-implemented private adapters
- private source adapter outcome checks preserve capability binding, workflow outcome binding, non-execution, and blocked artifact creation
- private source adapter bridge checks preserve outcome-matrix binding, checked entrypoints, confirmation-before-handoff, planned-runtime blocking, unsafe-source rejection, and no forecast or score outputs
- source intake reports classify source and mapping usability without producing forecast artifacts
- setup benchmark gates separate stronger-method fixture execution from quality, calibration, production, and state-of-the-art claims
- setup method decisions explain benchmark-gated stronger selection, baseline fallback, blocked mappings, and rejected intake before forecast artifacts are created
- setup forecast execution creates artifacts only for allowed setup intake and keeps blocked intake non-generating
- recalculation records append updated forecast states for pre-close evidence and reject post-outcome evidence as forecast input
- local live-capture checks validate ignored connector results and source-set drafts without adding them to release artifacts
