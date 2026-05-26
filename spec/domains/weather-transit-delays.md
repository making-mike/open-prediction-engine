# Weather Transit Delays Public Beta Wedge

Status: local custom-file prototype, opt-in live connector, checked forward-run workflow, foreground terminal scheduler, and local resolver-agent scan implemented.

Last reviewed: 2026-05-26.

This note defines the next OPE wedge for making a real, checkable prediction loop from public source data. It is a domain contract and implementation target, not a live performance claim.

## Product Decision

OPE should use public transport delays as the first public beta outcome family after the current weather-logistics fixture loop.

The reason is practical: public transport has frequent outcomes, clear time windows, public schedule/realtime standards, simple baselines, and a visible weather story. It is easier to score weekly than flights, logistics disruptions, crop yields, or power outages.

The first beta should forecast delay risk, not claim direct weather causality. The honest question is:

```text
Given forecast-time weather and historical transit reliability evidence, will the monitored transit network exceed the declared delay threshold during {service_window} on {service_date}?
```

Weather is forecast evidence. The outcome is a declared delay threshold resolved from transit data.

## Domain

`weather-transit-delays`

First output type:

- binary probability

Initial maturity:

- `fixture_ready`
- runnable from approved local CSV/JSON files through `python3 scripts/ope.py transit-delay-forecast`
- checked forward-run fixture and opt-in local live phases through `python3 scripts/ope.py transit-delay-forward-run`
- checked local resolver-agent scan through `python3 scripts/ope.py resolve-due-forward-runs`
- checked agent-facing resolution job registry through `python3 scripts/ope.py resolution-jobs`
- checked foreground terminal scheduler through `python3 scripts/ope.py resolution-scheduler`
- no calibration, benchmark, production, or live quality claim

## First Beta Question Template

Template:

```text
Will {transit_network} in {geography} exceed the beta delay threshold during {service_window} on {service_date}?
```

Initial concrete target:

```text
Will HSL surface transit in Helsinki exceed the beta delay threshold during the morning peak on a selected service date?
```

Default service window:

- local morning peak, 06:00 to 10:00

Default beta delay threshold:

- a trip-stop observation is late when GTFS-RT delay is at least 300 seconds
- the network delay event resolves `yes` when at least 20% of eligible trip-stop observations in the service window are late
- the event resolves `no` when the threshold is not met and coverage checks pass
- the event is `ambiguous` or `annulled` when coverage checks fail, the feed is materially unavailable, the schedule cannot be matched, or the service window is invalid

These thresholds are beta defaults. They must be checked against the first captured data profile before any public quality claim.

## Source Research

The current best public beta starting point is Helsinki/HSL:

- HSL publishes GTFS-RT service alerts, trip updates, and vehicle positions, and its documentation lists a Trip Updates endpoint updated every 15 seconds: [HSL GTFS-RT feeds](https://hsldevcom.github.io/gtfs_rt/).
- GTFS-RT TripUpdates are a standard way to publish delays, cancellations, changed routes, and stop-time updates. The GTFS-RT reference defines delay as schedule deviation in seconds, where positive values are late and negative values are early: [GTFS Realtime reference](https://gtfs.org/documentation/realtime/reference/).
- Open-Meteo can provide forecast-time weather variables and past forecast runs for verification/training without a normal API key requirement for non-commercial use: [Open-Meteo forecast API](https://open-meteo.com/en/docs) and [Open-Meteo historical forecast API](https://open-meteo.com/en/docs/historical-forecast-api).

Warsaw should stay in the candidate list, but not as the first clean delay-resolution city:

- A public Warsaw GTFS source lists static GTFS plus realtime alerts and vehicle positions, with attribution and licensing notes: [mkuran.pl GTFS feeds](https://mkuran.pl/gtfs/).
- That is enough for a later route-position reconstruction prototype, but it is less direct than a TripUpdates delay feed. Use Warsaw after OPE can reconstruct delay from static schedules plus vehicle positions or after a direct delay feed is approved.

US-focused archive options can help historical experiments, but they should not replace a controlled forward beta:

- gtfsrt.io archives GTFS-RT feeds from US agencies and exposes raw protobuf snapshots plus Parquet files: [gtfsrt.io](https://gtfsrt.io/).

## Accepted Source Roles

Forecast-time roles:

- `weather_forecast`: forecast-time precipitation, snowfall, temperature, wind speed, wind gusts, weather code, and warning-like derived indicators for the target geography and service window
- `transit_schedule`: static GTFS schedule or equivalent route/stop/time table needed to understand expected service
- `historical_delay_baseline`: previously collected resolved delay outcomes for the same network, mode, weekday/time window, and season bucket
- `planned_service_alerts`: forecast-time service alerts or planned disruptions known before forecast close

Resolution-only roles:

- `transit_delay_outcome`: GTFS-RT TripUpdates snapshots collected during the service window, or a checked equivalent delay outcome feed
- `feed_health`: capture coverage and feed freshness records used to decide whether the outcome is scorable

Supporting roles, later:

- `vehicle_positions`: used for delay reconstruction only when TripUpdates are unavailable
- `traffic_conditions`: optional forecast-time feature after source policy and licensing review
- `special_events`: optional forecast-time feature for known public events, not outcome evidence

## Resolution Policy

Primary resolution source:

- collected GTFS-RT TripUpdates for the target network and service window

Fallback resolution source:

- none for the first beta unless a checked equivalent delay source is explicitly configured

Coverage checks:

- snapshots must cover the declared service window at a configured cadence
- eligible observations must meet a setup-specific minimum sample count
- source timestamps must be inside the service window
- post-window corrections must be recorded as resolution updates, not forecast-time evidence

`yes` outcome:

- coverage checks pass and the late-observation ratio meets or exceeds the declared threshold

`no` outcome:

- coverage checks pass and the late-observation ratio is below the declared threshold

`ambiguous` outcome:

- data coverage is partial, conflicting, stale, or impossible to map to the declared network/window

`annulled` outcome:

- the network/window was invalid, service was suspended before forecast close, or the service day became incomparable for a predeclared non-weather reason such as strike handling or emergency suspension

## Baseline Method

The first baseline should be historical frequency:

```text
P(network_delay_event | network, mode, weekday, service_window, season_bucket)
```

Optional conditioned baseline after enough data:

```text
P(network_delay_event | network, mode, weekday, service_window, season_bucket, weather_bucket)
```

Minimum baseline rules:

- start baseline-only until at least 30 comparable resolved windows exist
- show individual Brier scores before making quality claims
- require at least 100 comparable resolved windows before provisional calibration summaries
- back off to broader buckets when slices are too sparse

## Leakage Controls

Forecast-time evidence may include:

- weather forecasts available before close
- planned service alerts available before close
- historical delay outcomes that predate close
- static schedules available before close

Forecast-time evidence must not include:

- same-window GTFS-RT delay snapshots
- post-window observed weather used as if it were known before close
- alerts published after close
- retrospective outage explanations unless they are used only during resolution/scoring

For historical model development, use archived forecast runs where possible instead of observed weather. This keeps training closer to what a real forecast would have known.

## Current Local Interface

The first runnable local interface is:

```bash
python3 scripts/ope.py transit-delay-forecast \
  --weather-forecast spec/fixtures/local-source-files/transit-weather-forecast.json \
  --historical-delays spec/fixtures/local-source-files/transit-delay-history.csv \
  --trip-updates spec/fixtures/local-source-files/transit-trip-updates.csv
```

It emits OPE-standard forecast question, evidence packet, forecast artifact, forecast history, resolution, and scoring records under `spec/fixtures/generated/transit-delay-forecast/` in checked fixture mode.

The checked forward-run interface is:

```bash
python3 scripts/ope.py transit-delay-forward-run
```

It binds the forecast, later outcome capture or approved trip-update rows, resolution, scoring, and claim boundary into one summary under `spec/fixtures/generated/transit-delay-forward-run/`.

Explicit live local phases are available, but they write ignored developer artifacts and do not change normal release checks:

```bash
python3 scripts/ope.py transit-delay-forward-run \
  --phase forecast \
  --service-date YYYY-MM-DD \
  --service-window morning_peak \
  --live-weather

python3 scripts/ope.py transit-delay-forward-run \
  --phase resolve \
  --run-state .ope/live/transit-forward-run/.../forward-run-state.json \
  --download-static-gtfs

python3 scripts/ope.py resolve-due-forward-runs --live
python3 scripts/ope.py resolve-due-forward-runs --live --execute --download-static-gtfs

python3 scripts/ope.py resolution-jobs --live
python3 scripts/ope.py resolution-scheduler --live --watch --poll-seconds 60
python3 scripts/ope.py resolution-scheduler --live --watch --execute --download-static-gtfs --poll-seconds 60
```

The command accepts custom local CSV/JSON files with the same role shape:

- weather forecast rows with `geography`, `service_date`, `service_window`, `retrieved_at`, and forecast weather fields
- historical delay rows with `network`, `geography`, `service_window`, and either `delay_event` or `late_observation_ratio`
- optional trip-update outcome rows with `delay_seconds` for resolution and scoring

## First Implementation Slice

Current local prototype:

1. Done: add normalized transit delay fixture records for one HSL service window.
2. Done: add a local custom-file forecast command with schema-bound forecast, resolution, and scoring outputs.
3. Done: add a weather-transit-delay domain setup record exposed through `domain-setups`.
4. Done: add a source connector declaration for `hsl_gtfs_rt_trip_updates` in fixture-replay mode.
5. Done: add an opt-in live capture command that stores sanitized local snapshots under `.ope/live/` without changing release checks.
6. Done: add a forward-run workflow that forecasts before the window, captures or accepts outcome rows after the window, resolves, scores, and keeps claim boundaries blocked.
7. Done: add a local resolver-agent scan that finds due saved forward runs and can explicitly execute the checked resolver command.
8. Done: add an agent-facing resolution job registry that tells agents whether to wait, execute the resolver, read resolved outputs, or inspect invalid state.
9. Done: add a foreground terminal scheduler that agents can run locally to poll jobs and optionally execute due checked resolver commands.

Next useful build:

1. Run repeated comparable live forward windows and save their local state.
2. Expose resolution job and scheduler readback through the agent adapter surface.
3. Add calibration summaries only after enough comparable resolved outcomes exist.

The first public beta should not launch until OPE can repeat that loop without hand-editing forecast, outcome, or scoring records, and until the source coverage and retention policy for live captures is explicit.

## Out Of Scope

The public beta wedge does not include:

- passenger-level tracking
- fare, ticketing, or enforcement analytics
- public safety decisions
- route optimization
- operator performance enforcement
- rider-specific recommendations
- direct causality claims that weather caused the delay event
- production use of live feeds before source policy, retention, and licensing checks are documented

## Public Claim Boundary

Allowed now:

- OPE has selected `weather-transit-delays` as the public beta candidate wedge.
- The repository documents source roles, resolution rules, baselines, and leakage controls for this wedge.
- OPE can run a local custom-file weather-transit-delay prototype from approved CSV/JSON files and emit schema-bound forecast, resolution, and scoring records.
- OPE can run a local terminal scheduler that polls saved forward runs and optionally executes due checked resolver commands on the developer's machine.

Blocked now:

- OPE can forecast live public transport delays from a connector.
- OPE has proven weather affects transit delays.
- OPE is calibrated for transit delay risk.
- OPE has a production live transit connector.
- OPE has a hosted scheduler or production worker.
- OPE can support arbitrary transit agencies without setup review.

The stronger claim to earn is:

```text
For one declared transit network, OPE can forecast a future delay-threshold event before the service window, preserve forecast-time weather and schedule evidence, resolve the outcome from collected transit delay data, score against a baseline, and report calibration only after enough comparable windows resolve.
```
