# Domain Config

Status: first readback contract defined.

Last reviewed: 2026-06-03.

Domain config records are reusable OPE configuration records for prediction domains. They define question templates, horizons, resolution criteria, baseline method, accepted source roles, exclusion rules, sample thresholds, and claim boundaries before any source binding or forecast execution occurs.

Checked readbacks:

```bash
python3 scripts/ope.py domain-configs
python3 scripts/ope.py domain-configs --domain weather-transit-delays
python3 scripts/ope.py domain-configs --domain seaport-berth-availability
python3 scripts/ope.py domain-configs --check
```

Current records cover the weather-transit-delay reference wedge and a candidate private seaport berth-availability domain. The command is non-mutating: it does not read private data, store credentials, execute live fetches, create forecasts, or allow raw SQL.

Source binding records are checked through `python3 scripts/ope.py source-bindings`. Domain configs only declare accepted source roles and source kinds; they do not contain credentials or concrete private source connection details.
