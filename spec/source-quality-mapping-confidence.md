# Source Quality And Mapping Confidence

Milestone 84 adds a checked source-quality and mapping-confidence read model for agents deciding whether connected data is forecast-usable, baseline-only usable, needs mapping confirmation, needs more data, should be replaced, or should be stopped as unsafe.

The generated read model covers:

- freshness, coverage, role fit, entity scope, leakage risk, missingness, outcome availability, and mapping confidence;
- bindings to source-builder drafts, source-adapter intake rows, source-intake reports, and setup method decisions;
- next actions for confirming mappings, collecting more data, replacing sources, stopping unsafe adapter output, or proceeding to method gates;
- compact agent-facing readback size checks;
- an execution boundary that prevents source reads, adapter execution, live fetches, artifact creation, scoring, and quality or production-readiness claims.

Run it locally with:

```bash
python3 scripts/ope.py source-quality
python3 scripts/ope.py source-quality --check
python3 scripts/ope.py source-quality --case source_intake_accepted
```

The source-quality read model is guidance over existing checked records. It does not create source manifests, forecast artifacts, resolution records, scoring records, telemetry, credentials, or private-source runtime behavior.
