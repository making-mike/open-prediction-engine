# Private Setup Orchestrator

Milestone 79 adds a compact local orchestration summary for private setup callers. It does not introduce a hosted runtime or a new source parser. Instead, it joins existing checked fixtures for request classification, first action, source intake, method gates, explicit forecast execution, and normal forecast readback.

The checked summary covers:

- a completed local-file setup path with `forecast-1102` card and bundle readback;
- an accepted source-adapter-output path that is ready for explicit forecast execution;
- blocked paths for missing approval, unconfirmed mappings, insufficient data, rejected sources, unsafe connector output, and response-too-large readback.

Run it locally with:

```bash
python3 scripts/ope.py private-setup-orchestrator
python3 scripts/ope.py private-setup-orchestrator --check
python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed
```

The orchestrator summary does not execute commands, read private data, fetch live data, store credentials, create source manifests, create field mappings, create forecasts, create scores, or bypass source intake and method gates. Forecast artifacts referenced by the successful path come from existing checked explicit forecast execution fixtures.
