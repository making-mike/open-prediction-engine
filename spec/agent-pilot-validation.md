# Agent Pilot Validation Pack

Milestone 81 adds a checked local pilot protocol for validating whether agents and supervised developers understand the MVP setup, readback, and claim boundaries before OPE expands runtime scope.

The generated pack covers:

- a 3-5 session moderated local CLI protocol;
- six task scenarios for local-file setup readback, accepted adapter output, unsafe source blocking, fixture-safe forecast-run readback, transit claim-gate readback, and domain-agnostic setup-engine shortcut comprehension;
- feedback dimensions for task completion, trust, setup friction, setup-engine shortcut comprehension, OPE/host responsibility split, parallel risk-engine avoidance, and runtime-gap classification;
- a rubric for forecast-card, lifecycle-bundle, source-intake, blocked-path, claim-boundary, and engine setup shortcut understanding;
- sanitized synthetic example summaries that store no raw transcripts, private data, credentials, or prompt logs.

Run it locally with:

```bash
python3 scripts/ope.py agent-pilot-validation
python3 scripts/ope.py agent-pilot-validation --check
python3 scripts/ope.py agent-pilot-validation --case local_file_setup_readback
python3 scripts/ope.py agent-pilot-validation --case engine_setup_shortcut_comprehension
```

The pilot validation pack is a protocol and rubric only. It does not recruit participants, run pilot sessions, collect telemetry, store raw transcripts, store private source data, create forecast artifacts, or claim forecast quality. Passing pilot sessions can support usability confidence for the local MVP, but not calibration or broad forecasting-quality claims.

The setup-engine comprehension task is explicitly non-Helsinki: it checks whether an agent starts with `setup-engine` for a host prediction goal before proposing a separate lightweight risk engine, and whether it can explain that OPE supplies the contract, evidence roles, baseline, forecast-card shape, resolver, scorer, and calibration gate while the host supplies UI, sources, runtime, notifications, and optional custom methods.
