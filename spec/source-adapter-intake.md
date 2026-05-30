# Source Adapter Intake

Milestone 78 defines the MVP handoff from external connector work into OPE core. An agent-built connector may live outside this repository if it produces a sanitized `source-adapter-output` record that embeds a source manifest, field mapping, provenance summary, and boundary flags.

The checked intake path is:

1. validate the adapter output, embedded source manifest, and field mapping;
2. block unsafe outputs before source intake when credentials, raw private rows, or prompt-visible secrets cross the boundary;
3. run safe adapter outputs through source intake;
4. route accepted source intake reports through setup benchmark and setup method decisions;
5. route needs-confirmation, insufficient-data, rejected, and unsafe outputs to explicit next actions.

The generated matrix is available at `spec/fixtures/generated/source-adapter-intake/weather-logistics-source-adapter-intake.generated.json`.

Run it locally with:

```bash
python3 scripts/ope.py source-adapter-intake
python3 scripts/ope.py source-adapter-intake --check
python3 scripts/ope.py source-adapter-intake --write
```

This path does not execute connector code, fetch live data, store credentials, parse arbitrary private data, create forecast artifacts, create scoring records, or claim connector safety. It checks whether a sanitized external connector output can enter OPE's existing setup workflow.
