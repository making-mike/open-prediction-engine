# Agent Pilot Validation Pack

Milestone 81 adds a checked local pilot protocol for validating whether agents and supervised developers understand the MVP setup, readback, and claim boundaries before OPE expands runtime scope.

The generated pack covers:

- a 3-5 session moderated local CLI protocol;
- five task scenarios for local-file setup readback, accepted adapter output, unsafe source blocking, fixture-safe forecast-run readback, and transit claim-gate readback;
- feedback dimensions for task completion, trust, setup friction, comprehension, and runtime-gap classification;
- a rubric for forecast-card, lifecycle-bundle, source-intake, blocked-path, and claim-boundary understanding;
- sanitized synthetic example summaries that store no raw transcripts, private data, credentials, or prompt logs.

Run it locally with:

```bash
python3 scripts/ope.py agent-pilot-validation
python3 scripts/ope.py agent-pilot-validation --check
python3 scripts/ope.py agent-pilot-validation --case local_file_setup_readback
```

The pilot validation pack is a protocol and rubric only. It does not recruit participants, run pilot sessions, collect telemetry, store raw transcripts, store private source data, create forecast artifacts, or claim forecast quality. Passing pilot sessions can support usability confidence for the local MVP, but not calibration or broad forecasting-quality claims.
