#!/usr/bin/env python3
"""Connect to a public transit API and decode GTFS-RT TripUpdate delays."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "transit-api-connector"
CONNECTOR_PATH = GENERATED / "hsl-transit-api-connector.generated.json"
SCHEMA = SPEC / "transit-api-connector.schema.json"
SOURCE_ADAPTER_OUTPUT_SCHEMA = SPEC / "source-adapter-output.schema.json"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"

GENERATED_AT = "2026-06-10T02:10:00Z"
HSL_TRIP_UPDATES_URL = "https://realtime.hsl.fi/realtime/trip-updates/v2/hsl"
HSL_DOCS_URL = "https://hsldevcom.github.io/gtfs_rt/"
HSL_STATIC_GTFS_URL = "https://infopalvelut.storage.hsldev.com/gtfs/hsl.zip"
DEFAULT_WORKSPACE = ROOT / ".ope" / "live" / "transit-api"
HSL_TIMEZONE = ZoneInfo("Europe/Helsinki")
CSV_COLUMNS = [
    "service_date",
    "network",
    "geography",
    "service_window",
    "captured_at",
    "trip_id",
    "stop_id",
    "delay_seconds",
]


class TransitApiConnectorError(Exception):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def compact_timestamp(value: datetime) -> str:
    return format_timestamp(value).replace("-", "").replace(":", "").replace("Z", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_uri(path: Path) -> str:
    try:
        return f"local://{path.resolve().relative_to(ROOT)}"
    except ValueError:
        return f"local://{path.resolve()}"


def connector_record() -> dict[str, Any]:
    record = {
        "transitApiConnectorId": "transitapiconnector-001",
        "generatedAt": GENERATED_AT,
        "provider": {
            "providerId": "hsl_gtfs_rt_trip_updates",
            "displayName": "HSL GTFS-RT TripUpdates",
            "network": "hsl-surface",
            "geography": "helsinki",
        },
        "connectorStatus": "offline_ready",
        "api": {
            "endpoint": HSL_TRIP_UPDATES_URL,
            "method": "GET",
            "requiresCredentials": False,
            "requestParametersSupported": False,
            "responseFormat": "gtfs_rt_protobuf",
            "updateIntervalSeconds": 15,
            "sourceDocumentation": HSL_DOCS_URL,
            "companionStaticGtfsPackage": HSL_STATIC_GTFS_URL,
        },
        "decoder": {
            "decoderStatus": "minimal_delay_decoder_checked",
            "dependencyPolicy": "python_standard_library_only",
            "scheduleJoinStatus": "implemented_opt_in",
            "scheduleJoinMatchKeys": [
                "route_id",
                "direction_id",
                "start_time",
                "start_date",
                "stop_id",
            ],
            "decodedFields": CSV_COLUMNS,
            "unsupportedFields": [
                "route_filtering",
                "stop_filtering",
                "vehicle_position_matching",
                "service_alert_reasoning",
            ],
        },
        "outputMapping": {
            "decodedCsvColumns": CSV_COLUMNS,
            "opeSourceRole": "transit_delay_outcome",
            "compatibleCommand": "python3 scripts/ope.py transit-delay-forecast --trip-updates .ope/live/transit-api/<capture>.csv",
        },
        "sourceAdapterBoundary": {
            "canProduceSourceAdapterOutput": True,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "storesCredentials": False,
            "rawRowsIncludedInGeneratedFixtures": False,
        },
        "liveBoundary": {
            "normalChecksOffline": True,
            "liveFetchRequiresExplicitFlag": True,
            "localCaptureWorkspace": ".ope/live/transit-api",
            "liveCapturesCommitted": False,
        },
        "checks": [
            {
                "checkId": "transitapicheck-001",
                "status": "passed",
                "description": "Synthetic GTFS-RT protobuf fixtures decode explicit and schedule-joined delay rows.",
            },
            {
                "checkId": "transitapicheck-002",
                "status": "passed",
                "description": "Connector contract keeps normal repository checks offline.",
            },
            {
                "checkId": "transitapicheck-003",
                "status": "not_run_in_normal_checks",
                "description": "Live HSL fetch is available only with --live and optional --save-local.",
            },
        ],
        "warnings": [
            "Live HSL capture is opt-in and writes only to the ignored local workspace.",
            "The stdlib decoder can derive delay rows through an opt-in static GTFS schedule join.",
            "HSL TripUpdates can provide predicted stop times without explicit delay fields; deriving delay seconds then requires --schedule-join and the companion static GTFS package.",
            "Decoded live rows are source handoff inputs, not forecast or quality claims.",
        ],
    }
    validate_connector_record(record)
    return record


def validate_connector_record(record: dict[str, Any]) -> None:
    errors = validate_record(record, SCHEMA)
    if errors:
        raise TransitApiConnectorError(f"transit API connector schema validation failed: {errors[0]}")
    if record["liveBoundary"]["normalChecksOffline"] is not True:
        raise TransitApiConnectorError("transit API connector must keep normal checks offline")
    if record["sourceAdapterBoundary"]["createsForecastArtifacts"]:
        raise TransitApiConnectorError("transit API connector must not create forecast artifacts")
    if record["sourceAdapterBoundary"]["storesCredentials"]:
        raise TransitApiConnectorError("transit API connector must not store credentials")


def read_varint(data: bytes, index: int) -> tuple[int, int]:
    shift = 0
    result = 0
    while index < len(data):
        byte = data[index]
        index += 1
        result |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return result, index
        shift += 7
        if shift >= 70:
            break
    raise TransitApiConnectorError("invalid protobuf varint")


def decode_fields(data: bytes) -> list[tuple[int, int, Any]]:
    fields: list[tuple[int, int, Any]] = []
    index = 0
    while index < len(data):
        key, index = read_varint(data, index)
        field_number = key >> 3
        wire_type = key & 0x07
        if field_number <= 0:
            raise TransitApiConnectorError("invalid protobuf field number")
        if wire_type == 0:
            value, index = read_varint(data, index)
        elif wire_type == 1:
            if index + 8 > len(data):
                raise TransitApiConnectorError("truncated protobuf fixed64")
            value = data[index:index + 8]
            index += 8
        elif wire_type == 2:
            size, index = read_varint(data, index)
            if index + size > len(data):
                raise TransitApiConnectorError("truncated protobuf length-delimited field")
            value = data[index:index + size]
            index += size
        elif wire_type == 5:
            if index + 4 > len(data):
                raise TransitApiConnectorError("truncated protobuf fixed32")
            value = data[index:index + 4]
            index += 4
        else:
            raise TransitApiConnectorError(f"unsupported protobuf wire type {wire_type}")
        fields.append((field_number, wire_type, value))
    return fields


def as_string(value: bytes) -> str:
    return value.decode("utf-8", errors="replace")


def as_int32(value: int) -> int:
    value = value & 0xFFFFFFFF
    if value >= 0x80000000:
        value -= 0x100000000
    return value


def service_date_from_gtfs(value: str | None, fallback_timestamp: int | None) -> str:
    if value and len(value) == 8 and value.isdigit():
        return f"{value[:4]}-{value[4:6]}-{value[6:8]}"
    if fallback_timestamp is not None:
        return datetime.fromtimestamp(fallback_timestamp, tz=timezone.utc).date().isoformat()
    return utc_now().date().isoformat()


def timestamp_to_iso(value: int | None) -> str:
    if value is None:
        return format_timestamp(utc_now())
    return format_timestamp(datetime.fromtimestamp(value, tz=timezone.utc))


def parse_header(data: bytes) -> dict[str, Any]:
    header: dict[str, Any] = {}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 2:
            header["gtfsRealtimeVersion"] = as_string(value)
        elif field_number == 3 and wire_type == 0:
            header["timestamp"] = int(value)
    return header


def parse_trip_descriptor(data: bytes) -> dict[str, Any]:
    trip: dict[str, Any] = {}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 2:
            trip["tripId"] = as_string(value)
        elif field_number == 2 and wire_type == 2:
            trip["startTime"] = as_string(value)
        elif field_number == 3 and wire_type == 2:
            trip["startDate"] = as_string(value)
        elif field_number == 5 and wire_type == 2:
            trip["routeId"] = as_string(value)
        elif field_number == 6 and wire_type == 0:
            trip["directionId"] = int(value)
    return trip


def parse_stop_time_event(data: bytes) -> dict[str, Any]:
    event: dict[str, Any] = {}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 0:
            event["delay"] = as_int32(int(value))
        elif field_number == 2 and wire_type == 0:
            event["time"] = int(value)
    return event


def parse_stop_time_update(data: bytes) -> dict[str, Any]:
    update: dict[str, Any] = {}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 0:
            update["stopSequence"] = int(value)
        elif field_number == 2 and wire_type == 2:
            update["arrival"] = parse_stop_time_event(value)
        elif field_number == 3 and wire_type == 2:
            update["departure"] = parse_stop_time_event(value)
        elif field_number == 4 and wire_type == 2:
            update["stopId"] = as_string(value)
    return update


def parse_trip_update(data: bytes) -> dict[str, Any]:
    update: dict[str, Any] = {"stopTimeUpdates": []}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 2:
            update["trip"] = parse_trip_descriptor(value)
        elif field_number == 2 and wire_type == 2:
            update["stopTimeUpdates"].append(parse_stop_time_update(value))
        elif field_number == 4 and wire_type == 0:
            update["timestamp"] = int(value)
        elif field_number == 5 and wire_type == 0:
            update["delay"] = as_int32(int(value))
    return update


def parse_entity(data: bytes) -> dict[str, Any]:
    entity: dict[str, Any] = {}
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 2:
            entity["id"] = as_string(value)
        elif field_number == 3 and wire_type == 2:
            entity["tripUpdate"] = parse_trip_update(value)
    return entity


def delay_from_stop_update(stop_update: dict[str, Any], trip_delay: int | None) -> int | None:
    departure = stop_update.get("departure") or {}
    arrival = stop_update.get("arrival") or {}
    if "delay" in departure:
        return int(departure["delay"])
    if "delay" in arrival:
        return int(arrival["delay"])
    return trip_delay


def trip_identity(entity_id: str | None, trip: dict[str, Any]) -> str:
    trip_id = trip.get("tripId")
    if trip_id:
        return str(trip_id)
    route_id = trip.get("routeId")
    start_date = trip.get("startDate")
    start_time = trip.get("startTime")
    direction_id = trip.get("directionId")
    if route_id and start_date and start_time and direction_id is not None:
        return f"{route_id}:{start_date}:{start_time}:{direction_id}"
    return entity_id or ""


def parse_feed(data: bytes) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    header: dict[str, Any] = {}
    entities: list[dict[str, Any]] = []
    for field_number, wire_type, value in decode_fields(data):
        if field_number == 1 and wire_type == 2:
            header = parse_header(value)
        elif field_number == 2 and wire_type == 2:
            entity = parse_entity(value)
            if "tripUpdate" in entity:
                entities.append(entity)
    return header, entities


def parse_gtfs_time(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.split(":")
    if len(parts) != 3:
        return None
    try:
        hours, minutes, seconds = (int(part) for part in parts)
    except ValueError:
        return None
    if minutes < 0 or minutes > 59 or seconds < 0 or seconds > 59:
        return None
    return hours * 3600 + minutes * 60 + seconds


def seconds_to_gtfs_time(value: int) -> str:
    hours, remainder = divmod(value, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def gtfs_date_to_iso(value: str) -> str:
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


def gtfs_local_epoch(service_date: str, scheduled_seconds: int) -> int:
    if len(service_date) == 8 and service_date.isdigit():
        iso_date = gtfs_date_to_iso(service_date)
    else:
        iso_date = service_date
    service_day = datetime.fromisoformat(iso_date).date()
    local_time = datetime.combine(service_day, datetime.min.time(), tzinfo=HSL_TIMEZONE)
    scheduled_local = local_time + timedelta(seconds=scheduled_seconds)
    return int(scheduled_local.astimezone(timezone.utc).timestamp())


def feed_schedule_keys(entities: list[dict[str, Any]]) -> set[tuple[str, str, str, str]]:
    keys: set[tuple[str, str, str, str]] = set()
    for entity in entities:
        trip = (entity.get("tripUpdate") or {}).get("trip") or {}
        route_id = trip.get("routeId")
        direction_id = trip.get("directionId")
        start_time = trip.get("startTime")
        start_date = trip.get("startDate")
        if route_id and direction_id is not None and start_time and start_date:
            keys.add((str(route_id), str(direction_id), str(start_time), str(start_date)))
    return keys


def read_gtfs_table(package: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    try:
        with package.open(name) as raw:
            handle = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            return [dict(row) for row in csv.DictReader(handle)]
    except KeyError as exc:
        raise TransitApiConnectorError(f"static GTFS package missing {name}") from exc


def active_service_ids(package: zipfile.ZipFile, service_dates: set[str]) -> dict[str, set[str]]:
    active_by_date: dict[str, set[str]] = {service_date: set() for service_date in service_dates}
    try:
        calendar_rows = read_gtfs_table(package, "calendar.txt")
    except TransitApiConnectorError:
        calendar_rows = []
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for row in calendar_rows:
        service_id = row.get("service_id")
        start_date = row.get("start_date", "")
        end_date = row.get("end_date", "")
        if not service_id:
            continue
        for service_date in service_dates:
            if start_date and service_date < start_date:
                continue
            if end_date and service_date > end_date:
                continue
            weekday = datetime.strptime(service_date, "%Y%m%d").weekday()
            if row.get(weekdays[weekday]) == "1":
                active_by_date[service_date].add(service_id)

    try:
        exception_rows = read_gtfs_table(package, "calendar_dates.txt")
    except TransitApiConnectorError:
        exception_rows = []
    for row in exception_rows:
        service_date = row.get("date")
        service_id = row.get("service_id")
        exception_type = row.get("exception_type")
        if service_date not in active_by_date or not service_id:
            continue
        if exception_type == "1":
            active_by_date[service_date].add(service_id)
        elif exception_type == "2":
            active_by_date[service_date].discard(service_id)
    return active_by_date


def load_static_schedules(
    static_gtfs_path: Path,
    keys: set[tuple[str, str, str, str]],
) -> tuple[dict[tuple[str, str, str], list[dict[str, Any]]], dict[str, Any]]:
    if not static_gtfs_path.exists():
        raise TransitApiConnectorError(f"missing static GTFS package: {static_gtfs_path}")
    route_direction_pairs = {(route_id, direction_id) for route_id, direction_id, _start_time, _start_date in keys}
    service_dates = {start_date for _route_id, _direction_id, _start_time, start_date in keys}
    if not route_direction_pairs or not service_dates:
        return {}, {
            "staticGtfsPath": local_uri(static_gtfs_path),
            "candidateTripCount": 0,
            "scheduleTripCount": 0,
            "activeServiceDates": sorted(service_dates),
        }

    with zipfile.ZipFile(static_gtfs_path) as package:
        active_by_date = active_service_ids(package, service_dates)
        active_services = set().union(*active_by_date.values()) if active_by_date else set()
        trip_meta_by_id: dict[str, dict[str, str]] = {}
        for row in read_gtfs_table(package, "trips.txt"):
            trip_id = row.get("trip_id")
            route_id = row.get("route_id")
            direction_id = row.get("direction_id", "0")
            service_id = row.get("service_id")
            if not trip_id or not route_id or service_id is None:
                continue
            if (route_id, direction_id) not in route_direction_pairs:
                continue
            if active_services and service_id not in active_services:
                continue
            trip_meta_by_id[trip_id] = {
                "trip_id": trip_id,
                "route_id": route_id,
                "direction_id": direction_id,
                "service_id": service_id,
            }

        stops_by_trip: dict[str, list[dict[str, Any]]] = {trip_id: [] for trip_id in trip_meta_by_id}
        with package.open("stop_times.txt") as raw:
            handle = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
            for row in csv.DictReader(handle):
                trip_id = row.get("trip_id")
                if trip_id not in stops_by_trip:
                    continue
                arrival_seconds = parse_gtfs_time(row.get("arrival_time"))
                departure_seconds = parse_gtfs_time(row.get("departure_time"))
                stop_id = row.get("stop_id")
                try:
                    stop_sequence = int(row.get("stop_sequence") or "0")
                except ValueError:
                    stop_sequence = 0
                if not stop_id or (arrival_seconds is None and departure_seconds is None):
                    continue
                stops_by_trip[trip_id].append(
                    {
                        "stop_id": stop_id,
                        "stop_sequence": stop_sequence,
                        "arrival_seconds": arrival_seconds,
                        "departure_seconds": departure_seconds,
                    }
                )

    schedules_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for trip_id, stops in stops_by_trip.items():
        if not stops:
            continue
        stops.sort(key=lambda item: item["stop_sequence"])
        first_stop = stops[0]
        start_seconds = first_stop["departure_seconds"]
        if start_seconds is None:
            start_seconds = first_stop["arrival_seconds"]
        if start_seconds is None:
            continue
        meta = trip_meta_by_id[trip_id]
        schedule = {
            **meta,
            "start_time": seconds_to_gtfs_time(start_seconds),
            "stops": stops,
        }
        key = (meta["route_id"], meta["direction_id"], schedule["start_time"])
        schedules_by_key.setdefault(key, []).append(schedule)

    return schedules_by_key, {
        "staticGtfsPath": local_uri(static_gtfs_path),
        "candidateTripCount": len(trip_meta_by_id),
        "scheduleTripCount": sum(len(items) for items in schedules_by_key.values()),
        "activeServiceDates": sorted(service_dates),
    }


def event_time(stop_update: dict[str, Any]) -> tuple[str, int] | None:
    departure = stop_update.get("departure") or {}
    arrival = stop_update.get("arrival") or {}
    if "time" in departure:
        return "departure", int(departure["time"])
    if "time" in arrival:
        return "arrival", int(arrival["time"])
    return None


def schedule_seconds(schedule_stop: dict[str, Any], event_kind: str) -> int | None:
    if event_kind == "departure" and schedule_stop["departure_seconds"] is not None:
        return int(schedule_stop["departure_seconds"])
    if event_kind == "arrival" and schedule_stop["arrival_seconds"] is not None:
        return int(schedule_stop["arrival_seconds"])
    if schedule_stop["departure_seconds"] is not None:
        return int(schedule_stop["departure_seconds"])
    if schedule_stop["arrival_seconds"] is not None:
        return int(schedule_stop["arrival_seconds"])
    return None


def score_schedule_match(schedule: dict[str, Any], stop_updates: list[dict[str, Any]]) -> int:
    stops = schedule["stops"]
    search_index = 0
    score = 0
    for stop_update in stop_updates:
        stop_id = str(stop_update.get("stopId", ""))
        if not stop_id:
            continue
        for index in range(search_index, len(stops)):
            if stops[index]["stop_id"] == stop_id:
                score += 1
                search_index = index + 1
                break
    return score


def best_schedule(
    schedules: list[dict[str, Any]],
    stop_updates: list[dict[str, Any]],
    active_service_ids_for_date: set[str] | None,
) -> dict[str, Any] | None:
    filtered = [
        schedule for schedule in schedules
        if not active_service_ids_for_date or schedule["service_id"] in active_service_ids_for_date
    ]
    if not filtered:
        filtered = schedules
    scored = [(score_schedule_match(schedule, stop_updates), schedule) for schedule in filtered]
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return None
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[0][1]


def schedule_derived_rows(
    entities: list[dict[str, Any]],
    *,
    static_gtfs_path: Path,
    network: str,
    geography: str,
    service_window: str,
    service_date: str | None,
    header_timestamp: int | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    keys = feed_schedule_keys(entities)
    schedules_by_key, load_metadata = load_static_schedules(static_gtfs_path, keys)
    active_by_date: dict[str, set[str]] = {}
    with zipfile.ZipFile(static_gtfs_path) as package:
        active_by_date = active_service_ids(package, {key[3] for key in keys})

    rows: list[dict[str, Any]] = []
    matched_trip_updates = 0
    unmatched_trip_updates = 0
    matched_stop_updates = 0
    unmatched_stop_updates = 0
    for entity in entities:
        trip_update = entity["tripUpdate"]
        trip = trip_update.get("trip") or {}
        route_id = trip.get("routeId")
        direction_id = trip.get("directionId")
        start_time = trip.get("startTime")
        start_date = trip.get("startDate")
        if not route_id or direction_id is None or not start_time or not start_date:
            unmatched_trip_updates += 1
            unmatched_stop_updates += len(trip_update.get("stopTimeUpdates", []))
            continue
        lookup_key = (str(route_id), str(direction_id), str(start_time))
        schedule = best_schedule(
            schedules_by_key.get(lookup_key, []),
            trip_update.get("stopTimeUpdates", []),
            active_by_date.get(str(start_date)),
        )
        if schedule is None:
            unmatched_trip_updates += 1
            unmatched_stop_updates += len(trip_update.get("stopTimeUpdates", []))
            continue
        matched_trip_updates += 1
        stops = schedule["stops"]
        search_index = 0
        capture_timestamp = trip_update.get("timestamp", header_timestamp)
        captured_at = timestamp_to_iso(capture_timestamp)
        row_service_date = service_date or service_date_from_gtfs(str(start_date), capture_timestamp)
        for stop_update in trip_update.get("stopTimeUpdates", []):
            stop_id = str(stop_update.get("stopId", ""))
            event = event_time(stop_update)
            if not stop_id or event is None:
                unmatched_stop_updates += 1
                continue
            event_kind, predicted_epoch = event
            matched_stop = None
            for index in range(search_index, len(stops)):
                if stops[index]["stop_id"] == stop_id:
                    matched_stop = stops[index]
                    search_index = index + 1
                    break
            if matched_stop is None:
                unmatched_stop_updates += 1
                continue
            scheduled_seconds = schedule_seconds(matched_stop, event_kind)
            if scheduled_seconds is None:
                unmatched_stop_updates += 1
                continue
            scheduled_epoch = gtfs_local_epoch(str(start_date), scheduled_seconds)
            rows.append(
                {
                    "service_date": row_service_date,
                    "network": network,
                    "geography": geography,
                    "service_window": service_window,
                    "captured_at": captured_at,
                    "trip_id": str(schedule["trip_id"]),
                    "stop_id": stop_id,
                    "delay_seconds": int(predicted_epoch - scheduled_epoch),
                }
            )
            matched_stop_updates += 1

    metadata = {
        **load_metadata,
        "attempted": True,
        "matchedTripUpdateCount": matched_trip_updates,
        "unmatchedTripUpdateCount": unmatched_trip_updates,
        "matchedStopTimeUpdateCount": matched_stop_updates,
        "unmatchedStopTimeUpdateCount": unmatched_stop_updates,
        "scheduleDerivedDelayRowCount": len(rows),
    }
    return rows, metadata


def decode_trip_update_rows(
    data: bytes,
    *,
    network: str,
    geography: str,
    service_window: str,
    service_date: str | None = None,
    schedule_join: bool = False,
    static_gtfs_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    header, entities = parse_feed(data)

    header_timestamp = header.get("timestamp")
    rows: list[dict[str, Any]] = []
    stop_update_count = 0
    for entity in entities:
        trip_update = entity["tripUpdate"]
        trip = trip_update.get("trip") or {}
        trip_id = trip_identity(entity.get("id"), trip)
        capture_timestamp = trip_update.get("timestamp", header_timestamp)
        captured_at = timestamp_to_iso(capture_timestamp)
        row_service_date = service_date or service_date_from_gtfs(trip.get("startDate"), capture_timestamp)
        trip_delay = trip_update.get("delay")
        for stop_update in trip_update.get("stopTimeUpdates", []):
            stop_update_count += 1
            delay = delay_from_stop_update(stop_update, trip_delay)
            if delay is None:
                continue
            rows.append(
                {
                    "service_date": row_service_date,
                    "network": network,
                    "geography": geography,
                    "service_window": service_window,
                    "captured_at": captured_at,
                    "trip_id": str(trip_id),
                    "stop_id": str(stop_update.get("stopId", "")),
                    "delay_seconds": int(delay),
                }
            )
    explicit_rows = rows
    schedule_join_metadata: dict[str, Any] = {"attempted": False}
    if schedule_join:
        if static_gtfs_path is None:
            raise TransitApiConnectorError("schedule join requires --static-gtfs or --download-static-gtfs")
        schedule_rows, schedule_join_metadata = schedule_derived_rows(
            entities,
            static_gtfs_path=static_gtfs_path,
            network=network,
            geography=geography,
            service_window=service_window,
            service_date=service_date,
            header_timestamp=header_timestamp,
        )
        rows = explicit_rows + schedule_rows
    metadata = {
        "gtfsRealtimeVersion": header.get("gtfsRealtimeVersion"),
        "feedTimestamp": timestamp_to_iso(header_timestamp) if header_timestamp is not None else None,
        "entityCount": len(entities),
        "stopTimeUpdateCount": stop_update_count,
        "explicitDelayRowCount": len(explicit_rows),
        "decodedDelayRowCount": len(rows),
        "scheduleJoin": schedule_join_metadata,
    }
    return rows, metadata


def fetch_hsl_trip_updates(timeout: int, max_bytes: int) -> bytes:
    request = Request(
        HSL_TRIP_UPDATES_URL,
        headers={"User-Agent": "open-prediction-engine/0.1 transit-api-connector"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TransitApiConnectorError(f"HSL TripUpdates fetch failed: {exc}") from exc
    if len(data) > max_bytes:
        raise TransitApiConnectorError(f"HSL TripUpdates response exceeded max bytes: {max_bytes}")
    if not data:
        raise TransitApiConnectorError("HSL TripUpdates response was empty")
    return data


def download_static_gtfs(path: Path, timeout: int, max_bytes: int) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    request = Request(
        HSL_STATIC_GTFS_URL,
        headers={"User-Agent": "open-prediction-engine/0.1 transit-api-connector"},
    )
    try:
        with urlopen(request, timeout=timeout) as response, path.open("wb") as handle:
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise TransitApiConnectorError(f"HSL static GTFS response exceeded max bytes: {max_bytes}")
                handle.write(chunk)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TransitApiConnectorError(f"HSL static GTFS fetch failed: {exc}") from exc
    if not path.exists() or path.stat().st_size == 0:
        raise TransitApiConnectorError("HSL static GTFS response was empty")
    return path


def resolve_static_gtfs_path(
    *,
    static_gtfs: str | None,
    download_static_gtfs_flag: bool,
    workspace: Path,
    timeout: int,
    max_bytes: int,
) -> Path | None:
    if static_gtfs:
        path = Path(static_gtfs)
        if not path.exists():
            raise TransitApiConnectorError(f"missing static GTFS package: {path}")
        return path
    if not download_static_gtfs_flag:
        return None
    path = workspace / "cache" / "hsl.zip"
    if path.exists() and path.stat().st_size > 0:
        return path
    return download_static_gtfs(path, timeout, max_bytes)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in CSV_COLUMNS})


def delay_summary(rows: list[dict[str, Any]], late_seconds: int) -> dict[str, Any]:
    delays = [int(row["delay_seconds"]) for row in rows]
    late = sum(1 for delay in delays if delay >= late_seconds)
    if not delays:
        return {
            "rowCount": 0,
            "lateSeconds": late_seconds,
            "lateCount": 0,
            "lateRatio": 0.0,
            "minDelaySeconds": None,
            "maxDelaySeconds": None,
        }
    return {
        "rowCount": len(delays),
        "lateSeconds": late_seconds,
        "lateCount": late,
        "lateRatio": round(late / len(delays), 4),
        "minDelaySeconds": min(delays),
        "maxDelaySeconds": max(delays),
    }


def field_mapping_row(mapping_id: str, source_field: str, target_field: str, field_type: str) -> dict[str, Any]:
    return {
        "mappingId": mapping_id,
        "sourceId": "source-1301",
        "sourceRole": "transit_delay_outcome",
        "sourceField": source_field,
        "targetField": target_field,
        "targetFieldType": field_type,
        "mappingOrigin": "deterministic_exact_match" if source_field == target_field else "user_provided",
        "mappingStatus": "confirmed",
        "confidence": 1.0,
        "requiresConfirmation": False,
        "validationNotes": ["GTFS-RT connector emits this column explicitly for OPE transit delay outcome use."],
    }


def build_source_adapter_output(
    *,
    csv_path: Path,
    rows: list[dict[str, Any]],
    capture_id: str,
    captured_at: str,
    network: str,
    geography: str,
    service_window: str,
    forecast_close_time: str,
    late_seconds: int,
    delay_source: str,
) -> dict[str, Any]:
    service_dates = sorted({str(row["service_date"]) for row in rows}) or [None]
    stats = delay_summary(rows, late_seconds)
    source_manifest = {
        "sourceManifestId": "sourcemanifest-1301",
        "createdAt": captured_at,
        "domainSetupId": "domainsetup-003",
        "domain": "weather-transit-delays",
        "forecastParameters": {
            "questionTemplateId": "template-003",
            "horizonLabel": "same-day-morning-peak",
            "forecastCloseTime": forecast_close_time,
            "geography": geography,
            "serviceDate": service_dates[-1],
            "assetIdentifier": network,
            "location": geography,
            "targetWindow": service_window,
        },
        "sources": [
            {
                "sourceId": "source-1301",
                "sourceRole": "transit_delay_outcome",
                "displayName": "HSL GTFS-RT decoded TripUpdates",
                "connectorType": "public_api",
                "sourceClass": "public_dataset",
                "sourceRef": local_uri(csv_path),
                "contentHash": sha256_file(csv_path),
                "rowCount": len(rows),
                "positiveOutcomeCount": stats["lateCount"],
                "retrieval": {
                    "retrievedAt": captured_at,
                    "availableBeforeForecastClose": False,
                    "maxSourceAgeHours": 24,
                },
                "coverage": {
                    "geographies": [geography],
                    "serviceDateStart": service_dates[0],
                    "serviceDateEnd": service_dates[-1],
                    "entityIdentifiers": [network],
                },
                "privacy": {
                    "privacyClass": "public",
                    "containsSecrets": False,
                    "containsPersonalData": False,
                    "approvalRequired": False,
                    "rawRetention": "metadata_only",
                },
                "featureSummary": {
                    "numericValues": [
                        {"fieldName": "delay_seconds", "value": float(stats["lateSeconds"]), "unit": "seconds"}
                    ],
                    "categoricalValues": [
                        {"fieldName": "service_window", "value": service_window}
                    ],
                },
                "fieldInventory": [
                    {"fieldName": "service_date", "observedType": "date", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "network", "observedType": "string", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "geography", "observedType": "string", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "service_window", "observedType": "categorical", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "captured_at", "observedType": "date_time", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "trip_id", "observedType": "id", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "stop_id", "observedType": "id", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                    {"fieldName": "delay_seconds", "observedType": "number", "sampleCount": len(rows), "nonNullCount": len(rows), "exampleValuesStored": False},
                ],
            }
        ],
    }
    field_mapping = {
        "fieldMappingId": "fieldmapping-1301",
        "createdAt": captured_at,
        "domainSetupId": source_manifest["domainSetupId"],
        "domain": source_manifest["domain"],
        "sourceManifestId": source_manifest["sourceManifestId"],
        "mappings": [
            field_mapping_row("mapping-130101", "service_date", "service_date", "date"),
            field_mapping_row("mapping-130102", "network", "transit_network", "string"),
            field_mapping_row("mapping-130103", "geography", "geography", "string"),
            field_mapping_row("mapping-130104", "service_window", "service_window", "categorical"),
            field_mapping_row("mapping-130105", "captured_at", "captured_at", "date_time"),
            field_mapping_row("mapping-130106", "trip_id", "trip_id", "id"),
            field_mapping_row("mapping-130107", "stop_id", "stop_id", "id"),
            field_mapping_row("mapping-130108", "delay_seconds", "delay_seconds", "number"),
        ],
        "aliasMappings": [
            {
                "aliasMappingId": "aliasmapping-1301",
                "entityType": "transit_network",
                "sourceValue": network,
                "canonicalValue": network,
                "mappingOrigin": "user_provided",
                "mappingStatus": "confirmed",
                "requiresConfirmation": False,
            }
        ],
    }
    output = {
        "sourceAdapterOutputId": "sourceadapteroutput-1301",
        "generatedAt": captured_at,
        "outputStatus": "intake_ready",
        "adapter": {
            "adapterId": "sourceadapter-1301",
            "displayName": "HSL GTFS-RT TripUpdates connector",
            "adapterVersion": f"hsl-gtfs-rt-{delay_source}-v0",
            "implementationLocation": "ope_core_fixture",
            "sourceKind": "public_api",
            "ownsForecastSemantics": False,
        },
        "execution": {
            "adapterRunId": capture_id,
            "executionMode": "external_runtime_capture",
            "startedAt": captured_at,
            "completedAt": captured_at,
            "normalChecksOffline": False,
            "liveFetchPerformed": True,
            "credentialsUsed": False,
            "credentialsStored": False,
        },
        "domainBinding": {
            "domainSetupId": source_manifest["domainSetupId"],
            "domain": source_manifest["domain"],
            "questionTemplateId": source_manifest["forecastParameters"]["questionTemplateId"],
            "sourceRoles": ["transit_delay_outcome"],
        },
        "sourceManifest": source_manifest,
        "fieldMapping": field_mapping,
        "handoffBoundary": {
            "canEnterSourceIntake": True,
            "sourceIntakeRequired": True,
            "mappingConfirmationRequired": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "allowedNextCommands": [
                f"python3 scripts/ope.py transit-delay-forecast --trip-updates {csv_path}",
                "python3 scripts/ope.py source-intake --case accepted",
            ],
        },
        "provenanceSummary": {
            "sourceCount": 1,
            "rowCount": len(rows),
            "contentHashesStored": True,
            "rawRowsIncluded": False,
            "allEvidenceClaimed": False,
            "diagnostics": [
                {
                    "diagnosticId": "diagnostic-1301",
                    "level": "info",
                    "message": f"Decoded HSL GTFS-RT TripUpdates into OPE-compatible delay rows using {delay_source}.",
                    "rawDetailIncluded": False,
                }
            ],
        },
        "controls": {
            "readOnly": True,
            "forecastGenerationAllowed": False,
            "forecastArtifactsCreated": False,
            "sourceIntakeAlreadyRun": False,
            "credentialStorageImplemented": False,
            "promptVisibleCredentialsAccepted": False,
            "rawPrivateRowsStored": False,
            "sanitizedErrorsOnly": True,
        },
        "nextAction": "run_source_intake",
        "warnings": [
            "Live capture output is a local handoff artifact, not a public generated fixture.",
            "Transit delay outcome rows are for resolution/scoring and must not be treated as forecast-time evidence.",
            "No route filtering or calibration claim is included.",
        ]
        + (
            ["Delay seconds were derived from a static GTFS schedule join; review match counts before source intake."]
            if delay_source == "static_gtfs_schedule_join"
            else ["No static GTFS schedule join was needed because explicit delay fields were present."]
        ),
    }
    for label, record, schema in [
        ("source adapter output", output, SOURCE_ADAPTER_OUTPUT_SCHEMA),
        ("source manifest", source_manifest, SOURCE_MANIFEST_SCHEMA),
        ("field mapping", field_mapping, FIELD_MAPPING_SCHEMA),
    ]:
        errors = validate_record(record, schema)
        if errors:
            raise TransitApiConnectorError(f"{label} schema validation failed: {errors[0]}")
    return output


def capture_summary(
    *,
    capture_id: str,
    provider_id: str,
    captured_at: str,
    raw_path: str | None,
    csv_path: str | None,
    adapter_output_path: str | None,
    raw_sha256: str,
    raw_byte_count: int,
    metadata: dict[str, Any],
    rows: list[dict[str, Any]],
    late_seconds: int,
    delay_source: str,
) -> dict[str, Any]:
    schedule_join = metadata.get("scheduleJoin") or {}
    return {
        "captureId": capture_id,
        "providerId": provider_id,
        "capturedAt": captured_at,
        "endpoint": HSL_TRIP_UPDATES_URL,
        "rawProtobufPath": raw_path,
        "decodedCsvPath": csv_path,
        "sourceAdapterOutputPath": adapter_output_path,
        "rawSha256": raw_sha256,
        "rawByteCount": raw_byte_count,
        "feed": metadata,
        "delaySummary": delay_summary(rows, late_seconds),
        "delayDerivation": delay_source,
        "sourceAdapterOutputAvailable": adapter_output_path is not None,
        "claimBoundary": {
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "normalChecksOffline": False,
            "liveCaptureCommitted": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "This is an opt-in local live capture, not a committed release fixture.",
            "Decoded rows can be passed to transit-delay-forecast as an outcome file.",
            "No calibration or production connector claim is implied by one capture.",
        ]
        + (
            [
                "No explicit delay fields were decoded; this capture needs a static GTFS schedule join before it can enter transit-delay source intake.",
            ]
            if not rows and not schedule_join.get("attempted")
            else []
        )
        + (
            [
                "Static GTFS schedule join ran but produced no delay rows; inspect unmatched trip and stop counts before using this source.",
            ]
            if not rows and schedule_join.get("attempted")
            else []
        )
        + (
            [
                "Delay seconds were derived with a static GTFS schedule join; this is intake-ready only within the recorded match-count boundary.",
            ]
            if rows and delay_source == "static_gtfs_schedule_join"
            else []
        ),
    }


def save_capture(
    *,
    raw: bytes,
    rows: list[dict[str, Any]],
    metadata: dict[str, Any],
    workspace: Path,
    network: str,
    geography: str,
    service_window: str,
    service_date: str | None,
    forecast_close_time: str,
    late_seconds: int,
    delay_source: str,
) -> dict[str, Any]:
    captured_at = format_timestamp(utc_now())
    stem = f"hsl-trip-updates-{compact_timestamp(utc_now())}"
    workspace.mkdir(parents=True, exist_ok=True)
    raw_path = workspace / f"{stem}.pb"
    csv_path = workspace / f"{stem}.csv"
    metadata_path = workspace / f"{stem}.json"
    raw_path.write_bytes(raw)
    write_csv(csv_path, rows)
    adapter_path: Path | None = None
    if rows:
        adapter_path = workspace / f"{stem}-source-adapter-output.json"
        adapter_output = build_source_adapter_output(
            csv_path=csv_path,
            rows=rows,
            capture_id="adapterrun-1301",
            captured_at=captured_at,
            network=network,
            geography=geography,
            service_window=service_window,
            forecast_close_time=forecast_close_time,
            late_seconds=late_seconds,
            delay_source=delay_source,
        )
        adapter_path.write_text(render_json(adapter_output), encoding="utf-8")
    summary = capture_summary(
        capture_id="transitapicapture-1301",
        provider_id="hsl_gtfs_rt_trip_updates",
        captured_at=captured_at,
        raw_path=str(raw_path.relative_to(ROOT)),
        csv_path=str(csv_path.relative_to(ROOT)),
        adapter_output_path=str(adapter_path.relative_to(ROOT)) if adapter_path else None,
        raw_sha256=sha256_bytes(raw),
        raw_byte_count=len(raw),
        metadata=metadata,
        rows=rows,
        late_seconds=late_seconds,
        delay_source=delay_source,
    )
    if service_date is not None:
        summary["serviceDateOverride"] = service_date
    metadata_path.write_text(render_json(summary), encoding="utf-8")
    return summary


def encode_varint(value: int) -> bytes:
    if value < 0:
        value += 1 << 64
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            break
    return bytes(out)


def pb_varint(field_number: int, value: int) -> bytes:
    return encode_varint((field_number << 3) | 0) + encode_varint(value)


def pb_bytes(field_number: int, value: bytes) -> bytes:
    return encode_varint((field_number << 3) | 2) + encode_varint(len(value)) + value


def pb_string(field_number: int, value: str) -> bytes:
    return pb_bytes(field_number, value.encode("utf-8"))


def synthetic_gtfs_rt() -> bytes:
    header = pb_string(1, "2.0") + pb_varint(3, 1781000000)
    trip = pb_string(1, "trip-fixture-001") + pb_string(3, "20260610")
    arrival = pb_varint(1, 120)
    departure = pb_varint(1, 340)
    stop_update_1 = pb_bytes(2, arrival) + pb_bytes(3, departure) + pb_string(4, "stop-fixture-001")
    stop_update_2 = pb_bytes(2, pb_varint(1, 60)) + pb_string(4, "stop-fixture-002")
    trip_update = (
        pb_bytes(1, trip)
        + pb_bytes(2, stop_update_1)
        + pb_bytes(2, stop_update_2)
        + pb_varint(4, 1781000015)
    )
    entity = pb_string(1, "entity-fixture-001") + pb_bytes(3, trip_update)
    return pb_bytes(1, header) + pb_bytes(2, entity)


def synthetic_gtfs_rt_without_delay() -> bytes:
    header = pb_string(1, "2.0") + pb_varint(3, 1781070000)
    trip = (
        pb_string(2, "08:00:00")
        + pb_string(3, "20260610")
        + pb_varint(4, 0)
        + pb_string(5, "route-fixture-001")
        + pb_varint(6, 1)
    )
    stop_1_departure = pb_varint(2, gtfs_local_epoch("20260610", parse_gtfs_time("08:05:00") or 0))
    stop_2_arrival = pb_varint(2, gtfs_local_epoch("20260610", parse_gtfs_time("08:12:00") or 0))
    stop_update_1 = pb_bytes(3, stop_1_departure) + pb_string(4, "stop-fixture-001")
    stop_update_2 = pb_bytes(2, stop_2_arrival) + pb_string(4, "stop-fixture-002")
    trip_update = pb_bytes(1, trip) + pb_bytes(2, stop_update_1) + pb_bytes(2, stop_update_2)
    entity = pb_string(1, "entity-fixture-joined") + pb_bytes(3, trip_update)
    return pb_bytes(1, header) + pb_bytes(2, entity)


def write_synthetic_static_gtfs(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as package:
        package.writestr(
            "calendar.txt",
            "\n".join(
                [
                    "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date",
                    "service-fixture-001,1,1,1,1,1,1,1,20260601,20260630",
                ]
            )
            + "\n",
        )
        package.writestr(
            "calendar_dates.txt",
            "service_id,date,exception_type\n",
        )
        package.writestr(
            "trips.txt",
            "\n".join(
                [
                    "route_id,service_id,trip_id,direction_id",
                    "route-fixture-001,service-fixture-001,trip-static-fixture-001,1",
                ]
            )
            + "\n",
        )
        package.writestr(
            "stop_times.txt",
            "\n".join(
                [
                    "trip_id,arrival_time,departure_time,stop_id,stop_sequence",
                    "trip-static-fixture-001,08:00:00,08:00:00,stop-fixture-001,1",
                    "trip-static-fixture-001,08:10:00,08:10:00,stop-fixture-002,2",
                ]
            )
            + "\n",
        )


def check_decoder() -> None:
    rows, metadata = decode_trip_update_rows(
        synthetic_gtfs_rt(),
        network="hsl-surface",
        geography="helsinki",
        service_window="morning_peak",
    )
    if metadata["entityCount"] != 1:
        raise TransitApiConnectorError("synthetic GTFS-RT decoder missed entity count")
    if metadata["stopTimeUpdateCount"] != 2:
        raise TransitApiConnectorError("synthetic GTFS-RT decoder missed stop updates")
    if len(rows) != 2:
        raise TransitApiConnectorError("synthetic GTFS-RT decoder should emit two delay rows")
    if rows[0]["delay_seconds"] != 340:
        raise TransitApiConnectorError("decoder should prefer departure delay over arrival delay")
    if rows[1]["delay_seconds"] != 60:
        raise TransitApiConnectorError("decoder should use arrival delay when departure is absent")
    if rows[0]["service_date"] != "2026-06-10":
        raise TransitApiConnectorError("decoder should convert GTFS start_date to ISO date")
    with tempfile.TemporaryDirectory() as temp_dir:
        static_gtfs_path = Path(temp_dir) / "synthetic-gtfs.zip"
        write_synthetic_static_gtfs(static_gtfs_path)
        joined_rows, joined_metadata = decode_trip_update_rows(
            synthetic_gtfs_rt_without_delay(),
            network="hsl-surface",
            geography="helsinki",
            service_window="morning_peak",
            schedule_join=True,
            static_gtfs_path=static_gtfs_path,
        )
    if joined_metadata["explicitDelayRowCount"] != 0:
        raise TransitApiConnectorError("schedule-join fixture should not contain explicit delay rows")
    if joined_metadata["scheduleJoin"]["scheduleDerivedDelayRowCount"] != 2:
        raise TransitApiConnectorError("schedule join should emit two delay rows")
    if joined_rows[0]["trip_id"] != "trip-static-fixture-001":
        raise TransitApiConnectorError("schedule join should bind the static GTFS trip id")
    if joined_rows[0]["delay_seconds"] != 300:
        raise TransitApiConnectorError("schedule join should compute first stop delay")
    if joined_rows[1]["delay_seconds"] != 120:
        raise TransitApiConnectorError("schedule join should compute second stop delay")


def write_connector(record: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    CONNECTOR_PATH.write_text(render_json(record), encoding="utf-8")
    print("generated transit API connector")


def check_connector(record: dict[str, Any]) -> None:
    check_decoder()
    expected = render_json(record)
    if not CONNECTOR_PATH.exists():
        print(f"missing transit API connector: {CONNECTOR_PATH}", file=sys.stderr)
        print("run `python3 scripts/connect_transit_api.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = CONNECTOR_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"transit API connector drift: {CONNECTOR_PATH}", file=sys.stderr)
        print("run `python3 scripts/connect_transit_api.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked transit API connector")


def load_raw_input(path: Path) -> bytes:
    if not path.exists():
        raise TransitApiConnectorError(f"missing protobuf input: {path}")
    return path.read_bytes()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated connector and synthetic decoder fixture")
    parser.add_argument("--write", action="store_true", help="write generated offline connector contract")
    parser.add_argument("--live", action="store_true", help="perform an opt-in HSL GTFS-RT TripUpdates fetch")
    parser.add_argument("--save-local", action="store_true", help="save raw protobuf, decoded CSV, metadata, and source-adapter output")
    parser.add_argument("--input-protobuf", help="decode a local GTFS-RT protobuf capture instead of fetching live")
    parser.add_argument("--schedule-join", action="store_true", help="derive delay seconds by joining TripUpdates to static GTFS")
    parser.add_argument("--static-gtfs", help="path to an HSL static GTFS zip for --schedule-join")
    parser.add_argument("--download-static-gtfs", action="store_true", help="download HSL static GTFS into the ignored local workspace cache")
    parser.add_argument("--workspace", default=str(DEFAULT_WORKSPACE), help="ignored local live capture workspace")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--max-bytes", type=int, default=25_000_000)
    parser.add_argument("--static-gtfs-max-bytes", type=int, default=120_000_000)
    parser.add_argument("--network", default="hsl-surface")
    parser.add_argument("--geography", default="helsinki")
    parser.add_argument("--service-window", default="api_capture")
    parser.add_argument("--service-date", help="override decoded GTFS service date")
    parser.add_argument("--forecast-close-time", default=GENERATED_AT)
    parser.add_argument("--late-seconds", type=int, default=300)
    args = parser.parse_args()

    try:
        record = connector_record()
        if args.write:
            write_connector(record)
            return
        if args.check:
            check_connector(record)
            return
        if not args.live and not args.input_protobuf:
            check_decoder()
            sys.stdout.write(render_json(record))
            return

        if args.live and args.input_protobuf:
            raise TransitApiConnectorError("use either --live or --input-protobuf, not both")
        raw = (
            fetch_hsl_trip_updates(args.timeout, args.max_bytes)
            if args.live
            else load_raw_input(Path(args.input_protobuf))
        )
        workspace = Path(args.workspace)
        static_gtfs_path = (
            resolve_static_gtfs_path(
                static_gtfs=args.static_gtfs,
                download_static_gtfs_flag=args.download_static_gtfs,
                workspace=workspace,
                timeout=args.timeout,
                max_bytes=args.static_gtfs_max_bytes,
            )
            if args.schedule_join
            else None
        )
        rows, metadata = decode_trip_update_rows(
            raw,
            network=args.network,
            geography=args.geography,
            service_window=args.service_window,
            service_date=args.service_date,
            schedule_join=args.schedule_join,
            static_gtfs_path=static_gtfs_path,
        )
        delay_source = (
            "static_gtfs_schedule_join"
            if metadata.get("scheduleJoin", {}).get("scheduleDerivedDelayRowCount", 0) > 0
            else "explicit_gtfs_rt_delay"
        )
        if args.save_local:
            summary = save_capture(
                raw=raw,
                rows=rows,
                metadata=metadata,
                workspace=workspace,
                network=args.network,
                geography=args.geography,
                service_window=args.service_window,
                service_date=args.service_date,
                forecast_close_time=args.forecast_close_time,
                late_seconds=args.late_seconds,
                delay_source=delay_source,
            )
        else:
            summary = capture_summary(
                capture_id="transitapicapture-1301",
                provider_id="hsl_gtfs_rt_trip_updates",
                captured_at=format_timestamp(utc_now()),
                raw_path=None,
                csv_path=None,
                adapter_output_path=None,
                raw_sha256=sha256_bytes(raw),
                raw_byte_count=len(raw),
                metadata=metadata,
                rows=rows,
                late_seconds=args.late_seconds,
                delay_source=delay_source,
            )
        sys.stdout.write(render_json(summary))
    except (OSError, json.JSONDecodeError, TransitApiConnectorError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
