# Developer Adoption Surface

Milestone 86 adds a checked local adoption surface for the MVP.

The surface gives developers and agents a compact path from repository checkout to the first useful readbacks:

- setup check and normal local checks;
- approved local-folder source runtime readback;
- forecast card and lifecycle bundle for `forecast-1102`;
- resolution, scoring, and claim-boundary review;
- local integration notes for CLI, `agent-call`, and MCP stdio.
- the newer `agent-integrate` golden path for agents asking what can be forecasted from approved starter context.

Run it locally with:

```bash
python3 scripts/ope.py developer-adoption
python3 scripts/ope.py developer-adoption --section quickstart
python3 scripts/ope.py developer-adoption --section scenario
python3 scripts/ope.py developer-adoption --section integrations
python3 scripts/ope.py developer-adoption --section release-notes
python3 scripts/ope.py developer-adoption --check
python3 scripts/ope.py agent-integrate --view candidates
python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output
```

This record is a read-only guide over checked local commands and generated records. It does not execute the commands it names, generate language-specific runtime types, create forecast artifacts, fetch live data, store credentials, expose a hosted service, or turn fixture evidence into a quality claim.
