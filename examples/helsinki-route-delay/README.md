# Helsinki Most-Popular-Route Delay-Risk App

A small CLI dashboard built **on top of** the Open Prediction Engine (OPE). It is
a host app — it brings presentation and one piece of domain logic (route
popularity) and lets OPE own the forecast lifecycle.

## What one run does

1. **Finds the most popular route.** Pulls the live HSL GTFS-RT TripUpdates feed
   and ranks routes by number of active trips right now, using OPE's own
   GTFS-RT decoder (`scripts/connect_transit_api.py`).
2. **Forecasts delay risk.** Delegates to OPE's checked
   `transit-delay-forward-run --phase forecast --live-weather`, which fetches
   live Open-Meteo weather, produces a probabilistic delay-risk forecast for the
   next morning-peak window, and **logs it as a resolvable forward-run** with a
   `resolveAt` timestamp.
3. **Renders a claim-safe dashboard.** Shows the busiest route, the weather lift
   over baseline, the forecast probability, the claim boundary, and the exact
   command to resolve + score the forecast after the window passes.

## Run it

```bash
python3 examples/helsinki-route-delay/app.py              # scan + forecast + log
python3 examples/helsinki-route-delay/app.py --no-forecast # just the busiest route
python3 examples/helsinki-route-delay/app.py --json        # machine-readable
```

Network access is used only for the explicit live HSL feed and weather fetch,
mirroring OPE's opt-in live posture. Forecast state is written under
`.ope/live/helsinki-route-app/` (ignored, not a committed fixture).

## Closing the loop (the part that takes real time)

The app *starts* the evidence loop; it cannot finish it in one run, by design —
a window has to physically pass before it can be resolved. After `resolveAt`:

```bash
python3 scripts/ope.py transit-delay-forward-run --phase resolve \
  --run-state .ope/live/helsinki-route-app/<date>-morning_peak/forward-run-state.json \
  --download-static-gtfs
```

Resolve promptly: a live capture only counts within 60 minutes after
`resolveAt`. Later attempts are blocked with reason `stale_capture_window`,
because a live GTFS-RT snapshot taken that late can no longer contain the
window's trips; a blocked run can still be resolved from an on-time saved
capture passed with `--trip-updates`.

Run the app daily and resolve each window. After ~30–100 resolved windows OPE
can begin reporting baseline lift and calibration — the only evidence that
shows whether the forecast is actually better than the base rate.

## Honest scope

- **What's real:** live route popularity, live weather, a real logged forecast,
  a real resolution/scoring path.
- **What this app does NOT claim:** OPE's forward-run currently forecasts at the
  HSL surface-network + window level. The busiest *route* is detected live and
  shown as context; the forecast is for the network/window that route runs in.
  Route-isolated resolution is a clear next step, not a claim made here.
- **No quality or calibration claim** is made until enough windows resolve —
  the dashboard surfaces OPE's own `qualityClaimAllowed=false` boundary.

## Note on HSL route IDs

The feed exposes GTFS route IDs (e.g. `4560`, `31M1`, `1040`), not the
human-facing line numbers. Mapping IDs to friendly names needs the static GTFS
`routes.txt`; that join is intentionally out of scope for this small app.
