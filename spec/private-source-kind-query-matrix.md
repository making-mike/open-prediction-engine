# Private Source-Kind Query Matrix

Status: checked local adapter conformance fixture.

The private source-kind query matrix records concrete `private_source_kind_selection` adapter responses for:

- the default full-list query
- one selected query for each checked source kind
- one unsupported source-kind query that returns a sanitized `bad_request` envelope

The generated record lives at:

```text
spec/fixtures/generated/private-source-kind-selection/ope-private-source-kind-query-matrix.generated.json
```

Generate or check it with:

```bash
python3 scripts/generate_private_source_kind_query_matrix.py --check
python3 scripts/check_private_source_kind_query_matrix.py
```

## Boundary

This matrix is adapter conformance evidence only. It does not execute source-builder, source-handoff, fixture evidence, forecast execution, scoring, private source reads, credential handling, live fetching, or hosted runtime work.

Selected cases must return `runtimeStatus: selected_example_only`, preserve the requested source kind in adapter state, and include exactly one `selectedExample`. Unsupported cases must return `status: error`, `exitCode: 2`, `error.code: bad_request`, and `payload: null`.
