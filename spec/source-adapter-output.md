# Source Adapter Output

Status: implemented as a checked fixture contract for external connector handoff.

The source adapter output contract is the OPE-native way for agents to connect data from any source without adding every connector to OPE core. A connector can live outside this repository, in any language or agent runtime, as long as its output is an OPE-compatible adapter handoff.

The boundary is:

```text
Any approved source
  -> external connector or agent adapter
  -> source-adapter-output
  -> source intake
  -> benchmark and method decision
  -> forecast execution
  -> resolution and scoring
```

The adapter output may describe source metadata, sanitized provenance, source manifests, and field mappings. It must not create forecast artifacts, scoring reports, credential records, or quality claims.

`spec/source-adapter-intake.md` defines the checked MVP intake path that validates sanitized adapter outputs, runs safe outputs through source intake and method gates, and blocks unsafe outputs before intake.

## Contract

The schema is:

```text
spec/source-adapter-output.schema.json
```

Generated fixture output lives under:

```text
spec/fixtures/generated/source-adapter-output/
```

The first fixture is a weather-transit-delay adapter handoff. It binds the local public beta transit-delay setup to an external-agent-style connector output that contains:

- an embedded `sourceManifest`
- an embedded `fieldMapping`
- source role and domain setup bindings
- sanitized provenance and diagnostics
- explicit controls showing that source intake and forecast generation have not run yet

## Commands

Inspect the checked adapter output:

```bash
python3 scripts/ope.py source-adapter-output
python3 scripts/ope.py source-adapter-intake
```

Check drift and invariants:

```bash
python3 scripts/ope.py source-adapter-output --check
python3 scripts/check_source_adapter_output.py
```

Refresh generated output:

```bash
python3 scripts/generate_source_adapter_output.py --write
```

## Agent Connector Rules

External connectors should:

- emit OPE `sourceManifest` and `fieldMapping` records
- store content hashes and sanitized metadata instead of raw private rows
- mark inferred mappings as needing confirmation
- declare whether data was available before forecast close
- keep outcome/resolution rows separate from forecast-time evidence
- route through source intake before any forecast can be created

External connectors must not:

- store prompt-visible credentials
- claim all possible evidence was gathered
- bypass source intake, benchmark gates, or method decisions
- create forecast artifacts or scoring records
- imply calibrated quality before enough resolved comparable outcomes exist
