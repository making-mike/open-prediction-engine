# OPE Fixtures

Fixtures are split into:

- `valid/`: schema-valid examples for the first lifecycle records.
- `invalid/`: intentionally bad semantic examples for future validation harnesses.
- `source/`: fixture-loop inputs that simulate pre-forecast, baseline, and resolution sources for resolved, ambiguous, and annulled cases.
- `live/`: fixture-mode weather source and declared operations records for the controlled live path.
- `benchmark/`: clean and contaminated benchmark-run fixtures for anti-leakage checks.
- `requests/`: controlled request intake fixtures for accepted, blocked, canceled, rejected, and adversarial cases.
- `generated/`: deterministic reports produced from valid fixtures.

The `invalid/` fixtures may still be valid JSON and may pass an isolated JSON Schema check. They are meant to fail cross-record lifecycle validation, such as:

- scoring an ambiguous question
- scoring an annulled question
- returning a forecast artifact whose `questionId` does not match the originating request

Those checks require a contract test harness and are tracked in the roadmap.

Update generated reports with:

```bash
python3 scripts/generate_fixture_reports.py --write
python3 scripts/run_fixture_loop.py --write
python3 scripts/resolve_live_weather_outcome.py --write
python3 scripts/run_forecast_pipeline.py --write
python3 scripts/resolve_pipeline_outcome.py --write
python3 scripts/generate_record_index.py --write
python3 scripts/generate_release_manifest.py --write
```

The normal check command compares committed generated reports without rewriting them:

```bash
python3 scripts/run_checks.py
```

The fixture loop emits normal scored reports for resolved outcomes and `excluded` scoring reports for ambiguous or annulled outcomes.

The live outcome resolver emits resolved live fixture records under `generated/live-outcome/`, but marks public quality claims provisional until the minimum comparable-outcome threshold is met.

The local forecast pipeline emits provisional request-bound forecast records under `generated/pipeline/`. It rejects blocked requests and does not resolve or score the forecast.

The pipeline resolver emits request-bound resolution, scoring, calibration, and track-record records under `generated/pipeline-resolution/`.

The release manifest emits a schema-bound local surface summary at `generated/release-manifest.generated.json`.

The benchmark checker expects `clean-pre-outcome-run.json` to pass and `post-outcome-leakage-run.json` to fail.

Aggregate fixtures are included in `valid/` for dependency and source-correlation hardening checks.
