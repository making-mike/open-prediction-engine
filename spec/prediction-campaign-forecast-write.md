# Prediction Campaign Forecast Write Plan

`prediction-campaign-forecast-write.schema.json` defines the checked plan for copying campaign forecast lifecycle records into ignored local campaign state.

The default surface is non-mutating. It binds `forecast-1301` question, evidence, artifact, and history records to their intended `.ope/live/prediction-campaigns/...` target paths, records content hashes and schema files, and lists the guards that must pass before local write execution.

Explicit local execution is available with `--write-local`. It copies the checked lifecycle records into ignored local campaign state, writes minimal campaign/run state files with the idempotency key, refuses mismatched overwrites, rejects symlink escapes from the campaign state root, and reports `already_present` on safe repeats. It does not fetch live data, run a resolver, create scores, append corpus evidence, or allow quality and calibration claims.

Run it locally with:

```bash
python3 scripts/ope.py prediction-campaign forecast-write
python3 scripts/ope.py prediction-campaign forecast-write --check
python3 scripts/ope.py prediction-campaign forecast-write --write-local --output-format jsonl
```

Required boundaries:

- source lifecycle records must validate against the standard OPE schemas before any local write;
- target paths must stay relative, under ignored `.ope/live/prediction-campaigns/` after symlink resolution, and free of credentials or private rows;
- the run must remain bound to the ready forecast-creation decision, source policy, duplicate key, and forecast-before-close window;
- normal checks must never execute the local write path;
- explicit local writes must be idempotent and must refuse mismatched existing target files;
- resolution, scoring, corpus append, and quality claims remain separate later milestones.
