# Transit API Connector

Status: implemented as an opt-in HSL GTFS-RT TripUpdates capture, minimal decoder, and static GTFS schedule join.

The transit API connector is the first concrete OPE-native connector for the public transport delay beta wedge. It connects to HSL's public GTFS-RT TripUpdates endpoint, decodes explicit delay fields when the feed supplies them, or derives delay seconds by joining predicted stop times to HSL's static GTFS schedule package. It writes local CSV rows compatible with the existing transit-delay forecast/resolution command.

The normal repository checks stay offline. Live API calls run only with `--live`.

## Provider

The first provider is HSL GTFS-RT TripUpdates:

```text
https://realtime.hsl.fi/realtime/trip-updates/v2/hsl
```

HSL documents this as a GET-only GTFS-RT v2.0 protobuf feed with no filtering parameters. The feed is updated every 15 seconds. GTFS-RT TripUpdates contain predicted stop-time changes, including delay fields when supplied.

HSL also documents that trip IDs are not available in the realtime feed and that realtime data complements the static GTFS package. If a live capture provides predicted stop times but no explicit delay seconds, OPE joins the capture against HSL's static GTFS schedule package when `--schedule-join` is enabled.

## Commands

Inspect the offline connector contract:

```bash
python3 scripts/ope.py transit-api-connector
```

Check the connector contract and built-in protobuf decoder fixture:

```bash
python3 scripts/ope.py transit-api-connector --check
python3 scripts/check_transit_api_connector.py
```

Capture live HSL TripUpdates into the ignored local workspace:

```bash
python3 scripts/ope.py transit-api-connector --live --save-local --service-window morning_peak
```

Capture live HSL TripUpdates and derive `delay_seconds` with the static GTFS schedule join:

```bash
python3 scripts/ope.py transit-api-connector \
  --live \
  --schedule-join \
  --download-static-gtfs \
  --save-local \
  --service-window morning_peak
```

The live command writes under:

```text
.ope/live/transit-api/
```

It stores:

- raw protobuf capture (`.pb`)
- decoded OPE-compatible delay rows (`.csv`)
- sanitized capture metadata (`.json`)
- source-adapter output (`-source-adapter-output.json`) only when delay rows are actually decoded or derived

Use the decoded CSV as an outcome source:

```bash
python3 scripts/ope.py transit-delay-forecast \
  --trip-updates .ope/live/transit-api/HSL_CAPTURE.csv
```

## Boundary

The connector decodes only the fields currently needed by the beta wedge:

- `service_date`
- `network`
- `geography`
- `service_window`
- `captured_at`
- `trip_id`
- `stop_id`
- `delay_seconds`

The schedule join matches realtime updates to static trips by route, direction, start time, service date, and stop order, then computes:

```text
delay_seconds = predicted_stop_time - scheduled_stop_time
```

It does not yet implement route filtering, stop filtering, vehicle-position matching, service-alert reasoning, hosted polling, credential handling, or calibration claims. A live capture with zero decoded or derived delay rows is a successful API capture but not an intake-ready delay source.

Live captures are local developer artifacts and must not be committed as public generated fixtures.
