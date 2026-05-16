# Pipeline Resolution

Status: implemented in fixture mode.

Pipeline resolution closes the local request-bound forecast lifecycle after `python3 scripts/ope.py pipeline` has produced forecast records. It reads the generated pipeline forecast and declared outcome fixtures, then emits resolution, scoring, calibration, track-record, and outcome-summary records.

## Commands

Check committed outputs:

```bash
python3 scripts/resolve_pipeline_outcome.py
python3 scripts/ope.py resolve-pipeline
```

Refresh generated outputs:

```bash
python3 scripts/resolve_pipeline_outcome.py --write
python3 scripts/ope.py resolve-pipeline --write
```

Generated outputs live under `spec/fixtures/generated/pipeline-resolution/`.

## Current Flow

The fixture-mode resolver:

1. reads the request-bound pipeline question, evidence packet, forecast artifact, history, and pipeline-run summary
2. reads declared operations and weather observation outcome fixtures
3. resolves the question from the same criteria declared in the forecast artifact
4. scores the pipeline forecast against its baseline
5. emits calibration and track-record records for the resolved pipeline outcome
6. records request, pipeline-run, question, forecast, evidence, and resolution ids in the outcome summary

## Guardrails

Normal release checks verify that:

- pipeline resolution preserves request, forecast, evidence, artifact, history, and resolution bindings
- unscorable paths remain explicit for missing operations coverage, corrected weather sources, and conflicting weather observations
- scoring is excluded for unscorable outcomes
- forecast-time provenance does not include future resolution sources
- the generated pipeline track record is readable through the local read-only record interface

## Claim Boundary

This is still a fixture-mode lifecycle check. It produces one resolved pipeline outcome, which is not enough for a live calibration claim. The generated outcome summary remains provisional until the minimum comparable-outcome threshold is met.
