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
- schema file count and schema file paths
- public read-surface counts from the generated record index
- claim boundaries for the first weather-logistics wedge
- explicit non-goals such as network API, hosted service, production live-data workflow, and live calibration claims

## Guardrails

Normal release checks verify:

- the manifest matches deterministic generated output
- the manifest validates against `spec/release-manifest.schema.json`
- the manifest names the CI workflow and release-check command
- live calibration remains disallowed while comparable resolved outcomes are below the declared threshold
