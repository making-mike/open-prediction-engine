# Transit Delay Forward Run

Status: checked fixture workflow plus opt-in local live phases.

Last reviewed: 2026-06-11.

This contract records one weather-transit-delay forecast-to-resolution run. It is the bridge between the local forecast prototype and a real public beta loop:

1. record a forecast before the service-window close time
2. save the forecast records and run state
3. later capture or provide transit delay outcome rows
4. resolve the declared delay-threshold event
5. score the forecast against the baseline

The checked fixture command is:

```bash
python3 scripts/ope.py transit-delay-forward-run
python3 scripts/ope.py transit-delay-forward-run --check
```

It writes the generated fixture summary under:

```text
spec/fixtures/generated/transit-delay-forward-run/
```

## Live Local Phases

Live phases are explicit and local. They may fetch Open-Meteo weather or HSL GTFS-RT TripUpdates only when a developer asks for them, and they write ignored artifacts under `.ope/live/transit-forward-run/`.

Start a forecast before the window:

```bash
python3 scripts/ope.py transit-delay-forward-run \
  --phase forecast \
  --service-date YYYY-MM-DD \
  --service-window morning_peak \
  --live-weather
```

Resolve after the window using the saved state:

```bash
python3 scripts/ope.py transit-delay-forward-run \
  --phase resolve \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json \
  --download-static-gtfs
```

Or let the local resolver-agent scan decide what is due:

```bash
python3 scripts/ope.py resolve-due-forward-runs --live
python3 scripts/ope.py resolve-due-forward-runs --live --execute --download-static-gtfs
```

The resolve phase preserves the original forecast timestamp, close time, horizon, source refs, and baseline inputs from the saved state. The transit outcome rows are resolution evidence only; they must not be added to forecast-time provenance.

## Resolution Integrity Guards

Outcome evidence must actually cover the declared forecast window before it may resolve a run:

- Decoded capture rows are stamped with the observed GTFS trip start date from the realtime trip descriptor. The requested service date is a scope filter; trips from another service date are rejected and counted, never restamped.
- The resolve-phase capture passes the forecast horizon to the decoder, and schedule-joined rows whose scheduled stop time falls outside the horizon are excluded and counted.
- Resolution additionally excludes rows whose `captured_at` lies outside the window from the horizon start to `resolveAt` plus the capture-lag tolerance (60 minutes); if the remaining rows fall below the minimum observation count, the run resolves ambiguous with an explicit reason.
- A live resolve attempted more than the capture-lag tolerance after `resolveAt` is blocked before any fetch: a live GTFS-RT snapshot taken that late cannot contain the past window's trips. The run state is rewritten with `runStatus: blocked` and a `resolutionGuard` carrying reason code `stale_capture_window`. Such a run can still be resolved later from an on-time saved capture passed with `--trip-updates`.

## Claim Boundary

One scored forward run is not calibration. The forward-run summary keeps `qualityClaimAllowed` and `calibrationClaimAllowed` false until enough comparable windows have resolved and scored against the declared baseline.

Normal repository checks remain offline. Local live files are not committed fixtures or public read records.
