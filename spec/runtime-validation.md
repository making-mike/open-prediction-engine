# Runtime Contract Validation

Status: implemented as a local Python standard-library surface.

OPE contract validation currently uses the JSON Schema subset exercised by the committed schemas. The reusable implementation lives in `scripts/ope_schema.py`; repository checks and single-record validation both call that module.

## Commands

Validate all schema-bound fixtures:

```bash
python3 scripts/check_schema_contracts.py
```

Smoke-test the reusable validator surface:

```bash
python3 scripts/check_contract_validator.py
```

Validate one record with inferred schema:

```bash
python3 scripts/validate_contract_record.py --input spec/fixtures/valid/binary-weather-logistics-question.json
python3 scripts/ope.py validate --input spec/fixtures/valid/binary-weather-logistics-question.json
```

Validate a read-surface contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/record-index.generated.json \
  --schema spec/record-index.schema.json
python3 scripts/check_read_contracts.py
```

Validate the auto-evidence plan contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/auto-evidence/weather-logistics-auto-evidence-plan.generated.json \
  --schema spec/evidence-gathering-plan.schema.json
python3 scripts/plan_auto_evidence.py --check
```

Validate the auto-evidence source-set contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/auto-evidence/weather-logistics-auto-evidence-source-set.generated.json \
  --schema spec/evidence-source-set.schema.json
python3 scripts/gather_auto_evidence.py --check
```

Validate source connector contracts:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-connectors/weather-logistics-source-connector-registry.generated.json \
  --schema spec/source-connector-registry.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-connectors/weather-logistics-source-connector-results.generated.json \
  --schema spec/source-connector-result-set.schema.json
python3 scripts/ope.py source-connectors --check
python3 scripts/check_source_connectors.py
```

Validate the live connector readiness contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/live-readiness/weather-logistics-open-meteo-live-readiness.generated.json \
  --schema spec/live-connector-readiness.schema.json
python3 scripts/ope.py live-readiness --check
python3 scripts/check_live_connector_readiness.py
```

Validate ignored local live captures:

```bash
python3 scripts/check_live_capture_workspace.py
python3 scripts/ope.py live-readiness --live --save-local --service-date YYYY-MM-DD
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --check
python3 scripts/ope.py live-capture --input .ope/live/open-meteo-warsaw-YYYY-MM-DD-source-connector-results.json --draft-source-set --write
```

Saved live captures validate against `spec/source-connector-result-set.schema.json`. Draft source sets validate against `spec/evidence-source-set.schema.json`, but remain ignored local development artifacts under `.ope/live/`.

Validate domain setup contracts:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/domain-setups/weather-logistics-domain-setup.generated.json \
  --schema spec/domain-setup.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/domain-setups/seaport-berth-availability-domain-setup.generated.json \
  --schema spec/domain-setup.schema.json
python3 scripts/ope.py domain-setups --check
python3 scripts/check_domain_setups.py
```

Validate source intake contracts:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/source-intake/weather-logistics-accepted-source-manifest.json \
  --schema spec/source-manifest.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/source-intake/weather-logistics-accepted-field-mapping.json \
  --schema spec/field-mapping.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-intake/weather-logistics-accepted-source-intake-report.generated.json \
  --schema spec/source-intake-report.schema.json
python3 scripts/ope.py source-intake --check
python3 scripts/check_source_intake.py
```

Validate local source manifest builder contracts:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-builder/weather-logistics-local-draft-source-manifest-build.generated.json \
  --schema spec/source-manifest-build.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-builder/weather-logistics-local-draft-source-manifest.json \
  --schema spec/source-manifest.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-builder/weather-logistics-local-draft-field-mapping.json \
  --schema spec/field-mapping.schema.json
python3 scripts/ope.py source-builder --check
python3 scripts/check_source_manifest_builder.py
```

Validate source-builder to source-intake handoff contracts:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff/weather-logistics-confirmed-builder-draft-source-intake-handoff.generated.json \
  --schema spec/source-intake-handoff.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff/weather-logistics-confirmed-builder-draft-source-intake-report.generated.json \
  --schema spec/source-intake-report.schema.json
python3 scripts/ope.py source-handoff --check
python3 scripts/check_source_intake_handoff.py
```

Validate source-handoff method gates:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-method/weather-logistics-confirmed-builder-draft-source-handoff-method-gate.generated.json \
  --schema spec/source-handoff-method-gate.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-method/weather-logistics-confirmed-builder-draft-setup-benchmark-gate.generated.json \
  --schema spec/setup-benchmark-gate.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-method/weather-logistics-confirmed-builder-draft-setup-method-decision.generated.json \
  --schema spec/setup-method-decision.schema.json
python3 scripts/ope.py source-handoff-method --check
python3 scripts/check_source_handoff_method_gate.py
```

Validate setup benchmark gates and method decisions:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/setup-benchmark/weather-logistics-accepted-setup-benchmark-gate.generated.json \
  --schema spec/setup-benchmark-gate.schema.json
python3 scripts/ope.py setup-benchmark --check
python3 scripts/check_setup_benchmark_gate.py
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/setup-method-decision/weather-logistics-accepted-setup-method-decision.generated.json \
  --schema spec/setup-method-decision.schema.json
python3 scripts/ope.py setup-method --check
python3 scripts/check_setup_method_decision.py
```

Validate setup forecast execution records:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/setup-forecast/weather-logistics-accepted-setup-setup-forecast-run.generated.json \
  --schema spec/setup-forecast-run.schema.json
python3 scripts/ope.py setup-forecast --check
python3 scripts/check_setup_forecast.py
```

Validate source-handoff forecast execution records:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-forecast/weather-logistics-confirmed-builder-draft-source-handoff-setup-forecast-run.generated.json \
  --schema spec/setup-forecast-run.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-forecast/weather-logistics-confirmed-builder-draft-source-handoff-artifact.generated.json \
  --schema spec/forecast-artifact.schema.json
python3 scripts/ope.py source-handoff-forecast --check
python3 scripts/check_source_handoff_forecast.py
```

Validate source-handoff resolution records:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-resolution/weather-logistics-source-handoff-resolution-resolution.generated.json \
  --schema spec/resolution-record.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-resolution/weather-logistics-source-handoff-resolution-scoring.generated.json \
  --schema spec/scoring-report.schema.json
python3 scripts/ope.py resolve-source-handoff
python3 scripts/check_source_handoff_resolution.py
```

Validate the source-handoff setup runbook:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/source-handoff-runbook/weather-logistics-source-handoff-setup-runbook.generated.json \
  --schema spec/source-handoff-setup-runbook.schema.json
python3 scripts/ope.py source-handoff-runbook --check
python3 scripts/check_source_handoff_setup_runbook.py
```

Validate the private setup workflow:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/private-setup-workflow/ope-private-setup-workflow.generated.json \
  --schema spec/private-setup-workflow.schema.json
python3 scripts/ope.py private-setup-workflow --check
python3 scripts/check_private_setup_workflow.py
```

Validate private source adapter capabilities:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-capabilities.generated.json \
  --schema spec/private-source-adapter-capability.schema.json
python3 scripts/ope.py private-source-adapters --check
python3 scripts/check_private_source_adapter_capabilities.py
```

Validate private source adapter outcome decisions:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-outcome-matrix.generated.json \
  --schema spec/private-source-adapter-outcome-matrix.schema.json
python3 scripts/ope.py private-source-adapter-outcomes --check
python3 scripts/check_private_source_adapter_outcome_matrix.py
```

Validate the private source adapter intake bridge:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/private-source-adapters/ope-private-source-adapter-intake-bridge.generated.json \
  --schema spec/private-source-adapter-intake-bridge.schema.json
python3 scripts/ope.py private-source-adapter-bridge --check
python3 scripts/check_private_source_adapter_intake_bridge.py
```

Validate recalculation history records:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/recalculation/weather-logistics-recalculation-trigger.generated.json \
  --schema spec/recalculation-trigger.schema.json
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/recalculation/weather-logistics-recalculation-run.generated.json \
  --schema spec/recalculation-run.schema.json
python3 scripts/ope.py recalculation --check
python3 scripts/check_recalculation_history.py
```

Validate the synthetic evidence trace contract:

```bash
python3 scripts/ope.py read --record-type evidence-trace --id forecast-602 --question-id question-601
python3 scripts/check_read_contracts.py
```

Validate the method registry contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/methods/weather-logistics-method-registry.json \
  --schema spec/method-registry.schema.json
python3 scripts/check_method_registry.py
```

Validate the method-comparison contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/method-comparison/weather-logistics-method-comparison.generated.json \
  --schema spec/method-comparison.schema.json
python3 scripts/compare_forecasting_methods.py --check
```

Validate the method-selection contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/method-selection/weather-logistics-method-selection.generated.json \
  --schema spec/method-selection.schema.json
python3 scripts/select_forecasting_method.py --check
```

Validate the agent adapter envelope contract:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/agent-adapter/ope-agent-forecast-card-envelope.generated.json \
  --schema spec/agent-envelope.schema.json
python3 scripts/build_agent_adapter_fixtures.py --check
python3 scripts/check_agent_adapter_dispatcher.py
```

Validate the agent adapter protocol map:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/agent-adapter/ope-agent-adapter-protocol-map.generated.json \
  --schema spec/agent-adapter-protocol-map.schema.json
python3 scripts/ope.py agent-protocol-map --check
python3 scripts/check_agent_adapter_protocol_map.py
python3 scripts/check_mcp_adapter.py
```

Validate the agent forecast-run summary:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-run.generated.json \
  --schema spec/forecast-run-summary.schema.json
python3 scripts/ope.py forecast-run --check
python3 scripts/check_agent_forecast_run.py
```

Validate the historical-only no-API baseline forecast:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/historical-baseline/weather-logistics-historical-baseline-artifact.generated.json \
  --schema spec/forecast-artifact.schema.json
python3 scripts/ope.py historical-forecast
python3 scripts/check_historical_baseline_forecast.py
python3 scripts/ope.py forecast-run --request spec/fixtures/requests/historical-weather-logistics-request.json
```

Validate the forecast-run intake matrix:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/forecast-run/weather-logistics-forecast-run-intake-matrix.generated.json \
  --schema spec/forecast-run-intake-matrix.schema.json
python3 scripts/ope.py forecast-run-matrix --check
python3 scripts/check_forecast_run_intake_matrix.py
```

Validate the agent forecast-run runbook:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/forecast-run/weather-logistics-agent-forecast-runbook.generated.json \
  --schema spec/agent-forecast-runbook.schema.json
python3 scripts/ope.py forecast-runbook --check
python3 scripts/check_agent_forecast_runbook.py
```

Validate the release manifest:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/generated/release-manifest.generated.json \
  --schema spec/release-manifest.schema.json
```

Validate one record with an explicit schema:

```bash
python3 scripts/validate_contract_record.py \
  --input spec/fixtures/valid/binary-weather-logistics-question.json \
  --schema spec/forecast-question.schema.json
```

The single-record command returns JSON:

```json
{
  "valid": true,
  "input": "spec/fixtures/valid/binary-weather-logistics-question.json",
  "schema": "spec/forecast-question.schema.json",
  "errors": []
}
```

## Supported Schema Subset

The local validator supports the schema features used by the current OPE contracts:

- `$ref` across local schema files
- `type`, `const`, `enum`, `required`, `properties`, and `additionalProperties: false`
- `oneOf`, `allOf`, `if`, and `then`
- array `items`, `minItems`, and `maxItems`
- string `minLength`, `maxLength`, `pattern`, and `format` for `date-time`, `date`, and `uri`
- numeric `minimum`, `maximum`, `exclusiveMinimum`, and `exclusiveMaximum`

Unsupported JSON Schema features should not be added to OPE schemas until the validator is extended or replaced by a full JSON Schema implementation.

## Boundary

This is not yet generated type output for another language and it is not a hosted validation service. It is a stable local contract gate for scripts, fixtures, and future runtime work.
