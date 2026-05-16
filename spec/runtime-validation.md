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
