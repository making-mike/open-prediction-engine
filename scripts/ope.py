#!/usr/bin/env python3
"""Small local CLI for OPE repository workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def cmd_check(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/run_checks.py"])


def cmd_release_check(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/release_check.py"])


def cmd_generate_fixtures(args: argparse.Namespace) -> None:
    reports_command = [sys.executable, "scripts/generate_fixture_reports.py"]
    loop_command = [sys.executable, "scripts/run_fixture_loop.py"]
    live_outcome_command = [sys.executable, "scripts/resolve_live_weather_outcome.py"]
    pipeline_command = [sys.executable, "scripts/run_forecast_pipeline.py"]
    pipeline_resolution_command = [sys.executable, "scripts/resolve_pipeline_outcome.py"]
    index_command = [sys.executable, "scripts/generate_record_index.py"]
    manifest_command = [sys.executable, "scripts/generate_release_manifest.py"]
    if args.write:
        reports_command.append("--write")
        loop_command.append("--write")
        live_outcome_command.append("--write")
        pipeline_command.append("--write")
        pipeline_resolution_command.append("--write")
        index_command.append("--write")
        manifest_command.append("--write")
    run(reports_command)
    run(loop_command)
    run(live_outcome_command)
    run(pipeline_command)
    run(pipeline_resolution_command)
    run(index_command)
    run(manifest_command)


def cmd_read(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/read_ope_record.py",
        "--record-type",
        args.record_type,
        "--id",
        args.id,
    ]
    if args.question_id:
        command.extend(["--question-id", args.question_id])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    run(command)


def cmd_list(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/read_ope_record.py",
        "--record-type",
        args.record_type,
        "--list",
    ]
    if args.domain:
        command.extend(["--domain", args.domain])
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    run(command)


def cmd_request(args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/validate_forecast_request.py", "--input", args.input])


def cmd_validate(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/validate_contract_record.py", "--input", args.input]
    if args.schema:
        command.extend(["--schema", args.schema])
    run(command)


def cmd_weather(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/fetch_open_meteo_weather.py",
        "--location",
        args.location,
        "--service-date",
        args.service_date,
    ]
    if args.fixture:
        command.extend(["--fixture", args.fixture])
    if args.live:
        command.append("--live")
    if args.retrieved_at:
        command.extend(["--retrieved-at", args.retrieved_at])
    if args.source_status:
        command.extend(["--source-status", args.source_status])
    if args.output:
        command.extend(["--output", args.output])
    run(command)


def cmd_resolve_live(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/resolve_live_weather_outcome.py"]
    if args.write:
        command.append("--write")
    run(command)


def cmd_pipeline(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_forecast_pipeline.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolve_pipeline(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/resolve_pipeline_outcome.py"]
    if args.write:
        command.append("--write")
    run(command)


def cmd_manifest(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_release_manifest.py"]
    if args.write:
        command.append("--write")
    run(command)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="run normal repository checks")
    check.set_defaults(func=cmd_check)

    release_check = subparsers.add_parser("release-check", help="run release-readiness checks")
    release_check.set_defaults(func=cmd_release_check)

    generate = subparsers.add_parser("generate-fixtures", help="check or refresh generated fixtures")
    generate.add_argument("--write", action="store_true", help="refresh generated fixtures")
    generate.set_defaults(func=cmd_generate_fixtures)

    resolve_live = subparsers.add_parser("resolve-live", help="check or refresh the fixture-mode live outcome")
    resolve_live.add_argument("--write", action="store_true", help="refresh generated live outcome records")
    resolve_live.set_defaults(func=cmd_resolve_live)

    pipeline = subparsers.add_parser("pipeline", help="check or refresh the local forecast pipeline scaffold")
    pipeline.add_argument("--request")
    pipeline.add_argument("--write", action="store_true", help="refresh generated pipeline records")
    pipeline.set_defaults(func=cmd_pipeline)

    resolve_pipeline = subparsers.add_parser("resolve-pipeline", help="check or refresh resolved pipeline outputs")
    resolve_pipeline.add_argument("--write", action="store_true", help="refresh generated pipeline resolution records")
    resolve_pipeline.set_defaults(func=cmd_resolve_pipeline)

    manifest = subparsers.add_parser("manifest", help="check or refresh the local release manifest")
    manifest.add_argument("--write", action="store_true", help="refresh the generated release manifest")
    manifest.set_defaults(func=cmd_manifest)

    read = subparsers.add_parser("read", help="read a public generated record")
    read.add_argument(
        "--record-type",
        choices=["forecast-artifact", "forecast-bundle", "forecast-card", "track-record"],
        required=True,
    )
    read.add_argument("--id", required=True)
    read.add_argument("--question-id")
    read.add_argument("--max-bytes", type=int)
    read.set_defaults(func=cmd_read)

    list_records = subparsers.add_parser("list", help="list public generated records")
    list_records.add_argument(
        "--record-type",
        choices=["forecast-artifact", "forecast-bundle", "forecast-card", "track-record"],
        required=True,
    )
    list_records.add_argument("--domain")
    list_records.add_argument("--limit", type=int)
    list_records.add_argument("--max-bytes", type=int)
    list_records.set_defaults(func=cmd_list)

    request = subparsers.add_parser("request", help="validate a forecast request without execution")
    request.add_argument("--input", required=True)
    request.set_defaults(func=cmd_request)

    validate = subparsers.add_parser("validate", help="validate one OPE contract record")
    validate.add_argument("--input", required=True)
    validate.add_argument("--schema")
    validate.set_defaults(func=cmd_validate)

    weather = subparsers.add_parser("weather", help="normalize allow-listed weather input")
    weather.add_argument("--location", choices=["warsaw"], required=True)
    weather.add_argument("--service-date", required=True)
    weather.add_argument("--fixture")
    weather.add_argument("--live", action="store_true")
    weather.add_argument("--retrieved-at")
    weather.add_argument("--source-status", choices=["current", "corrected"])
    weather.add_argument("--output")
    weather.set_defaults(func=cmd_weather)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
