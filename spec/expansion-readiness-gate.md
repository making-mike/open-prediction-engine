# Expansion Readiness Gate

`expansion-readiness-gate.schema.json` defines a read-only post-MVP decision surface for deciding when OPE should expand beyond the local MVP.

The gate binds current checked evidence from the release manifest, developer adoption surface, agent pilot validation pack, pilot evidence ledger, local usage trace, public transit corpus growth loop, public transit track-record gate, and approved local-folder source runtime.

The gate does not start a hosted service, run live fetches, execute private source adapters, store credentials, store raw private rows, create forecast artifacts, generate runtime types, or make quality claims.

Use:

```bash
python3 scripts/ope.py expansion-readiness
python3 scripts/ope.py expansion-readiness --section options
python3 scripts/ope.py expansion-readiness --check
```

The current gate intentionally keeps hosted runtime, broader private sources, live forecast evidence, stronger methods, and generated runtime types blocked or deferred until real pilot evidence, comparable transit samples, and local usage friction justify the next investment.
