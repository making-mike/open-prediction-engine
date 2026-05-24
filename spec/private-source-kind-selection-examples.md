# Private Source-Kind Selection Examples

Status: checked local guidance; not execution.

This contract gives agents compact examples for choosing the next private setup path after reading private source adapter guidance.

The generated record lives at:

```text
spec/fixtures/generated/private-source-kind-selection/ope-private-source-kind-selection-examples.generated.json
```

Generate or check it with:

```bash
python3 scripts/ope.py private-source-kind-selection
python3 scripts/ope.py private-source-kind-selection --check
python3 scripts/check_private_source_kind_selection_examples.py
```

## Boundary

Selection examples bind the private source adapter guidance envelope, private setup first-action records, and the private setup adapter-chain runbook. They tell an agent whether to call source-builder, ask for mapping confirmation, use fixture evidence, wait for a future runtime, replace a source, or stop.

They do not:

- execute source reads or adapter calls
- inspect private files, uploads, APIs, or databases
- create source manifests, field mappings, forecasts, scores, credentials, live fetches, hosted APIs, or production runtime artifacts
- bypass private setup request routing, source-builder validation, source-handoff confirmation, setup benchmark gates, method decisions, or forecast execution

Manual upload, private API, and private database examples remain planned-runtime guidance only. Unsupported and unsafe source examples stop before source intake.
