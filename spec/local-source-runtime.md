# Local Source Runtime

Milestone 85 adds one narrow non-fixture source runtime: an approved local-folder input path for the weather-logistics setup.

The runtime is intentionally small. It only accepts caller-approved files from an allow-listed local fixture folder, applies size and format limits, routes the accepted file set through the existing source builder, source-intake handoff, setup benchmark, setup method decision, and explicit source-handoff forecast execution records, then exposes the resulting forecast-card readback.

The generated runtime covers:

- one accepted approved-local-folder case that binds to `forecast-1102`;
- blocked cases for missing approval, credential-like fields, unsafe paths, oversized files, schema mismatch, and leakage indicators;
- source-policy binding, path allow-listing, size limits, sanitized diagnostics, and non-goal boundaries;
- explicit confirmation that normal checks stay deterministic and offline.

Run it locally with:

```bash
python3 scripts/ope.py local-source-runtime
python3 scripts/ope.py local-source-runtime --check
python3 scripts/ope.py local-source-runtime --case approved_local_folder
```

This is not a general private API, database parser, hosted watcher, credential store, or production connector runtime. It is one local pattern for approved file ingestion through the existing OPE gates.
