# Live Outcome Resolution

Status: implemented in fixture mode.

The first live outcome loop resolves provisional `weather-logistics` evidence bundles from declared operations and weather observation sources. It does not make live calibration claims.

## Command

Check committed generated outputs:

```bash
python3 scripts/resolve_live_weather_outcome.py
```

Refresh generated outputs:

```bash
python3 scripts/resolve_live_weather_outcome.py --write
```

The local CLI wrapper exposes the same check-mode command:

```bash
python3 scripts/ope.py resolve-live
```

## Resolution Rules

For the selected wedge, a `yes` outcome requires:

- a complete declared operations outcome source
- at least one weather-coded delivery disruption in the declared geography and service date
- a complete declared weather observation source
- observed daily precipitation meeting the predeclared threshold

The resolver marks an outcome unscorable when:

- the operations source does not cover the declared geography or service date
- the weather observation source was corrected after scoring or has conflicting quality flags

## Claim Boundary

Generated live track-record output remains provisional while resolved comparable live outcomes are below the domain threshold. The current threshold is 30 outcomes for any calibration claim.
