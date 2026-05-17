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
    auto_evidence_command = [sys.executable, "scripts/plan_auto_evidence.py"]
    auto_evidence_gather_command = [sys.executable, "scripts/gather_auto_evidence.py"]
    source_connectors_command = [sys.executable, "scripts/generate_source_connectors.py"]
    live_readiness_command = [sys.executable, "scripts/generate_live_connector_readiness.py"]
    domain_setups_command = [sys.executable, "scripts/generate_domain_setups.py"]
    source_intake_command = [sys.executable, "scripts/generate_source_intake.py"]
    source_builder_command = [sys.executable, "scripts/build_source_manifest.py"]
    source_handoff_command = [sys.executable, "scripts/generate_source_intake_handoff.py"]
    source_handoff_method_command = [sys.executable, "scripts/generate_source_handoff_method_gate.py"]
    auto_evidence_forecast_command = [sys.executable, "scripts/run_auto_evidence_forecast.py"]
    auto_evidence_resolution_command = [sys.executable, "scripts/resolve_auto_evidence_outcome.py"]
    historical_forecast_command = [sys.executable, "scripts/run_historical_baseline_forecast.py"]
    method_comparison_command = [sys.executable, "scripts/compare_forecasting_methods.py"]
    method_selection_command = [sys.executable, "scripts/select_forecasting_method.py"]
    setup_benchmark_command = [sys.executable, "scripts/generate_setup_benchmark_gate.py"]
    setup_method_command = [sys.executable, "scripts/select_setup_method.py"]
    setup_forecast_command = [sys.executable, "scripts/run_setup_forecast.py"]
    source_handoff_forecast_command = [sys.executable, "scripts/run_source_handoff_forecast.py"]
    source_handoff_resolution_command = [sys.executable, "scripts/resolve_source_handoff_outcome.py"]
    source_handoff_runbook_command = [sys.executable, "scripts/generate_source_handoff_setup_runbook.py"]
    private_setup_workflow_command = [sys.executable, "scripts/generate_private_setup_workflow.py"]
    private_source_adapters_command = [sys.executable, "scripts/generate_private_source_adapter_capabilities.py"]
    private_source_adapter_outcomes_command = [sys.executable, "scripts/generate_private_source_adapter_outcome_matrix.py"]
    private_source_adapter_bridge_command = [sys.executable, "scripts/generate_private_source_adapter_intake_bridge.py"]
    recalculation_command = [sys.executable, "scripts/generate_recalculation_history.py"]
    forecast_run_command = [sys.executable, "scripts/run_agent_forecast.py"]
    forecast_run_matrix_command = [sys.executable, "scripts/generate_forecast_run_intake_matrix.py"]
    forecast_runbook_command = [sys.executable, "scripts/generate_agent_forecast_runbook.py"]
    agent_envelopes_command = [sys.executable, "scripts/build_agent_adapter_fixtures.py"]
    agent_protocol_map_command = [sys.executable, "scripts/generate_agent_adapter_protocol_map.py"]
    pipeline_command = [sys.executable, "scripts/run_forecast_pipeline.py"]
    pipeline_resolution_command = [sys.executable, "scripts/resolve_pipeline_outcome.py"]
    index_command = [sys.executable, "scripts/generate_record_index.py"]
    manifest_command = [sys.executable, "scripts/generate_release_manifest.py"]
    if args.write:
        reports_command.append("--write")
        loop_command.append("--write")
        live_outcome_command.append("--write")
        auto_evidence_command.append("--write")
        auto_evidence_gather_command.append("--write")
        source_connectors_command.append("--write")
        live_readiness_command.append("--write")
        domain_setups_command.append("--write")
        source_intake_command.append("--write")
        source_builder_command.append("--write")
        source_handoff_command.append("--write")
        source_handoff_method_command.append("--write")
        auto_evidence_forecast_command.append("--write")
        auto_evidence_resolution_command.append("--write")
        historical_forecast_command.append("--write")
        method_comparison_command.append("--write")
        method_selection_command.append("--write")
        setup_benchmark_command.append("--write")
        setup_method_command.append("--write")
        setup_forecast_command.append("--write")
        source_handoff_forecast_command.append("--write")
        source_handoff_resolution_command.append("--write")
        source_handoff_runbook_command.append("--write")
        private_setup_workflow_command.append("--write")
        private_source_adapters_command.append("--write")
        private_source_adapter_outcomes_command.append("--write")
        private_source_adapter_bridge_command.append("--write")
        recalculation_command.append("--write")
        forecast_run_command.append("--write")
        forecast_run_matrix_command.append("--write")
        forecast_runbook_command.append("--write")
        agent_envelopes_command.append("--write")
        agent_protocol_map_command.append("--write")
        pipeline_command.append("--write")
        pipeline_resolution_command.append("--write")
        index_command.append("--write")
        manifest_command.append("--write")
    else:
        auto_evidence_command.append("--check")
        auto_evidence_gather_command.append("--check")
        source_connectors_command.append("--check")
        live_readiness_command.append("--check")
        domain_setups_command.append("--check")
        source_intake_command.append("--check")
        source_builder_command.append("--check")
        source_handoff_command.append("--check")
        source_handoff_method_command.append("--check")
        method_comparison_command.append("--check")
        method_selection_command.append("--check")
        setup_benchmark_command.append("--check")
        setup_method_command.append("--check")
        setup_forecast_command.append("--check")
        source_handoff_forecast_command.append("--check")
        source_handoff_runbook_command.append("--check")
        private_setup_workflow_command.append("--check")
        private_source_adapters_command.append("--check")
        private_source_adapter_outcomes_command.append("--check")
        private_source_adapter_bridge_command.append("--check")
        recalculation_command.append("--check")
        forecast_run_command.append("--check")
        forecast_run_matrix_command.append("--check")
        forecast_runbook_command.append("--check")
        agent_envelopes_command.append("--check")
        agent_protocol_map_command.append("--check")
    run(reports_command)
    run(loop_command)
    run(live_outcome_command)
    run(auto_evidence_command)
    run(auto_evidence_gather_command)
    run(source_connectors_command)
    run(live_readiness_command)
    run(domain_setups_command)
    run(source_intake_command)
    run(source_builder_command)
    run(source_handoff_command)
    run(source_handoff_method_command)
    run(auto_evidence_forecast_command)
    run(auto_evidence_resolution_command)
    run(historical_forecast_command)
    run(method_comparison_command)
    run(method_selection_command)
    run(setup_benchmark_command)
    run(setup_method_command)
    run(setup_forecast_command)
    run(source_handoff_forecast_command)
    run(source_handoff_resolution_command)
    run(source_handoff_runbook_command)
    run(private_setup_workflow_command)
    run(private_source_adapters_command)
    run(private_source_adapter_outcomes_command)
    run(private_source_adapter_bridge_command)
    run(recalculation_command)
    run(forecast_run_command)
    run(forecast_run_matrix_command)
    run(forecast_runbook_command)
    run(agent_envelopes_command)
    run(agent_protocol_map_command)
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


def cmd_evidence_plan(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/plan_auto_evidence.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_gather_evidence(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/gather_auto_evidence.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.weather_fixture:
        command.extend(["--weather-fixture", args.weather_fixture])
    if args.baseline_history:
        command.extend(["--baseline-history", args.baseline_history])
    if args.execution_mode:
        command.extend(["--execution-mode", args.execution_mode])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_connectors(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_connectors.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.results:
        command.append("--results")
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_live_readiness(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_live_connector_readiness.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    if args.live:
        command.append("--live")
    if args.save_local:
        command.append("--save-local")
    if args.workspace:
        command.extend(["--workspace", args.workspace])
    if args.location:
        command.extend(["--location", args.location])
    if args.service_date:
        command.extend(["--service-date", args.service_date])
    run(command)


def cmd_live_capture(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/live_capture_workspace.py", "--input", args.input]
    if args.request:
        command.extend(["--request", args.request])
    if args.check:
        command.append("--check")
    if args.draft_source_set:
        command.append("--draft-source-set")
    if args.write:
        command.append("--write")
    if args.output:
        command.extend(["--output", args.output])
    run(command)


def cmd_domain_setups(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_domain_setups.py"]
    if args.setup:
        command.extend(["--setup", args.setup])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_intake(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_intake.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_builder(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/build_source_manifest.py"]
    if args.case:
        command.extend(["--case", args.case])
    for item in args.input or []:
        command.extend(["--input", item])
    for item in args.mapping_hint or []:
        command.extend(["--mapping-hint", item])
    if args.output_dir:
        command.extend(["--output-dir", args.output_dir])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_handoff(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_intake_handoff.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_handoff_method(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_handoff_method_gate.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_auto_forecast(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_auto_evidence_forecast.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolve_auto_evidence(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/resolve_auto_evidence_outcome.py"]
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolve_source_handoff(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/resolve_source_handoff_outcome.py"]
    if args.write:
        command.append("--write")
    run(command)


def cmd_historical_forecast(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_historical_baseline_forecast.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.write:
        command.append("--write")
    run(command)


def cmd_method_selection(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/select_forecasting_method.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_setup_benchmark(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_setup_benchmark_gate.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_setup_method(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/select_setup_method.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_setup_forecast(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_setup_forecast.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_handoff_forecast(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_source_handoff_forecast.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_recalculation(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_recalculation_history.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_method_comparison(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/compare_forecasting_methods.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_envelopes(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/build_agent_adapter_fixtures.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_protocol_map(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_adapter_protocol_map.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_forecast_run(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_agent_forecast.py"]
    if args.request:
        command.extend(["--request", args.request])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_forecast_run_matrix(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_forecast_run_intake_matrix.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_forecast_runbook(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_forecast_runbook.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_handoff_runbook(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_handoff_setup_runbook.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_workflow(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_workflow.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_source_adapters(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_source_adapter_capabilities.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_source_adapter_outcomes(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_source_adapter_outcome_matrix.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_source_adapter_bridge(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_source_adapter_intake_bridge.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_call(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/agent_adapter_dispatcher.py",
        "--operation",
        args.operation,
        "--request",
        args.request,
        "--forecast-id",
        args.forecast_id,
        "--question-id",
        args.question_id,
        "--max-bytes",
        str(args.max_bytes),
        "--caller-intent",
        args.caller_intent,
    ]
    completed = subprocess.run(command, cwd=ROOT)
    raise SystemExit(completed.returncode)


def cmd_mcp_stdio(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/ope_mcp_stdio.py"])


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
        choices=[
            "evidence-source-set",
            "evidence-trace",
            "forecast-artifact",
            "forecast-bundle",
            "forecast-card",
            "source-connector-results",
            "track-record",
        ],
        required=True,
    )
    read.add_argument("--id", required=True)
    read.add_argument("--question-id")
    read.add_argument("--max-bytes", type=int)
    read.set_defaults(func=cmd_read)

    list_records = subparsers.add_parser("list", help="list public generated records")
    list_records.add_argument(
        "--record-type",
        choices=[
            "evidence-source-set",
            "evidence-trace",
            "forecast-artifact",
            "forecast-bundle",
            "forecast-card",
            "source-connector-results",
            "track-record",
        ],
        required=True,
    )
    list_records.add_argument("--domain")
    list_records.add_argument("--limit", type=int)
    list_records.add_argument("--max-bytes", type=int)
    list_records.set_defaults(func=cmd_list)

    request = subparsers.add_parser("request", help="validate a forecast request without execution")
    request.add_argument("--input", required=True)
    request.set_defaults(func=cmd_request)

    evidence_plan = subparsers.add_parser("evidence-plan", help="check or refresh the auto-evidence dry-run plan")
    evidence_plan.add_argument("--request")
    evidence_plan.add_argument("--check", action="store_true", help="check generated evidence-plan drift")
    evidence_plan.add_argument("--write", action="store_true", help="refresh the generated evidence plan")
    evidence_plan.set_defaults(func=cmd_evidence_plan)

    gather_evidence = subparsers.add_parser("gather-evidence", help="check or refresh auto-evidence fixture gathering")
    gather_evidence.add_argument("--request")
    gather_evidence.add_argument("--weather-fixture")
    gather_evidence.add_argument("--baseline-history")
    gather_evidence.add_argument(
        "--execution-mode",
        choices=["fixture_replay", "live_fetch"],
        default="fixture_replay",
    )
    gather_evidence.add_argument("--check", action="store_true", help="check generated source-set drift")
    gather_evidence.add_argument("--write", action="store_true", help="refresh the generated source set")
    gather_evidence.set_defaults(func=cmd_gather_evidence)

    source_connectors = subparsers.add_parser(
        "source-connectors",
        help="check, refresh, or print policy-bound source connector registry and results",
    )
    source_connectors.add_argument("--request")
    source_connectors.add_argument("--results", action="store_true", help="print connector result set")
    source_connectors.add_argument("--check", action="store_true", help="check generated source connector drift")
    source_connectors.add_argument("--write", action="store_true", help="refresh generated source connector fixtures")
    source_connectors.set_defaults(func=cmd_source_connectors)

    live_readiness = subparsers.add_parser(
        "live-readiness",
        help="check, refresh, or explicitly run the Open-Meteo live connector readiness gate",
    )
    live_readiness.add_argument("--request")
    live_readiness.add_argument("--check", action="store_true", help="check generated live-readiness drift")
    live_readiness.add_argument("--write", action="store_true", help="refresh generated live-readiness fixture")
    live_readiness.add_argument("--live", action="store_true", help="perform an opt-in integration live fetch")
    live_readiness.add_argument("--save-local", action="store_true", help="save sanitized live connector output under .ope/live")
    live_readiness.add_argument("--workspace", help="ignored local live workspace")
    live_readiness.add_argument("--location", choices=["warsaw"])
    live_readiness.add_argument("--service-date")
    live_readiness.set_defaults(func=cmd_live_readiness)

    live_capture = subparsers.add_parser(
        "live-capture",
        help="validate or draft evidence from an ignored local live connector capture",
    )
    live_capture.add_argument("--input", required=True, help="local live connector result-set JSON")
    live_capture.add_argument("--request")
    live_capture.add_argument("--check", action="store_true", help="validate the saved live connector result")
    live_capture.add_argument("--draft-source-set", action="store_true", help="convert a successful capture to a draft source set")
    live_capture.add_argument("--write", action="store_true", help="write the draft source set")
    live_capture.add_argument("--output", help="draft source-set output path")
    live_capture.set_defaults(func=cmd_live_capture)

    domain_setups = subparsers.add_parser(
        "domain-setups",
        help="check, refresh, or print domain-agnostic OPE engine setup records",
    )
    domain_setups.add_argument(
        "--setup",
        choices=["weather-logistics", "seaport-berth-availability"],
        help="print one setup record",
    )
    domain_setups.add_argument("--check", action="store_true", help="check generated domain setup drift")
    domain_setups.add_argument("--write", action="store_true", help="refresh generated domain setup records")
    domain_setups.set_defaults(func=cmd_domain_setups)

    source_intake = subparsers.add_parser(
        "source-intake",
        help="check, refresh, or print source-manifest and field-mapping intake reports",
    )
    source_intake.add_argument(
        "--case",
        choices=["accepted", "accepted_partial", "needs_confirmation", "rejected"],
        help="print one source intake report",
    )
    source_intake.add_argument("--check", action="store_true", help="check generated source intake drift")
    source_intake.add_argument("--write", action="store_true", help="refresh source intake fixtures and reports")
    source_intake.set_defaults(func=cmd_source_intake)

    source_builder = subparsers.add_parser(
        "source-builder",
        help="inspect approved local CSV/JSON files and draft source manifest inputs",
    )
    source_builder.add_argument(
        "--case",
        choices=["local_draft", "contains_secret", "unsupported_format", "oversized", "leakage"],
        help="print one local source-builder case",
    )
    source_builder.add_argument(
        "--input",
        action="append",
        help="inspect a caller-approved local file as source_role=path",
    )
    source_builder.add_argument(
        "--mapping-hint",
        action="append",
        help="mark a caller-provided mapping hint as source_role.source_field=target_field",
    )
    source_builder.add_argument("--output-dir", help="directory for generic --input draft outputs")
    source_builder.add_argument("--check", action="store_true", help="check generated source-builder drift")
    source_builder.add_argument("--write", action="store_true", help="refresh generated source-builder fixtures")
    source_builder.set_defaults(func=cmd_source_builder)

    source_handoff = subparsers.add_parser(
        "source-handoff",
        help="check, refresh, or print source-builder to source-intake handoff records",
    )
    source_handoff.add_argument(
        "--case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="print one source intake handoff case",
    )
    source_handoff.add_argument("--check", action="store_true", help="check generated source-handoff drift")
    source_handoff.add_argument("--write", action="store_true", help="refresh generated source-handoff records")
    source_handoff.set_defaults(func=cmd_source_handoff)

    source_handoff_method = subparsers.add_parser(
        "source-handoff-method",
        help="check, refresh, or print method-gate summaries for source handoffs",
    )
    source_handoff_method.add_argument(
        "--case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="print one source handoff method-gate case",
    )
    source_handoff_method.add_argument("--check", action="store_true", help="check generated source-handoff method gates")
    source_handoff_method.add_argument("--write", action="store_true", help="refresh generated source-handoff method gates")
    source_handoff_method.set_defaults(func=cmd_source_handoff_method)

    auto_forecast = subparsers.add_parser("auto-forecast", help="check or refresh auto-evidence forecast outputs")
    auto_forecast.add_argument("--request")
    auto_forecast.add_argument("--write", action="store_true", help="refresh generated auto-evidence forecast outputs")
    auto_forecast.set_defaults(func=cmd_auto_forecast)

    resolve_auto_evidence = subparsers.add_parser(
        "resolve-auto-evidence",
        help="check or refresh resolved auto-evidence outputs",
    )
    resolve_auto_evidence.add_argument(
        "--write",
        action="store_true",
        help="refresh generated auto-evidence resolution records",
    )
    resolve_auto_evidence.set_defaults(func=cmd_resolve_auto_evidence)

    resolve_source_handoff = subparsers.add_parser(
        "resolve-source-handoff",
        help="check or refresh resolved source-handoff forecast outputs",
    )
    resolve_source_handoff.add_argument(
        "--write",
        action="store_true",
        help="refresh generated source-handoff resolution records",
    )
    resolve_source_handoff.set_defaults(func=cmd_resolve_source_handoff)

    historical_forecast = subparsers.add_parser(
        "historical-forecast",
        help="check or refresh the no-API historical baseline forecast outputs",
    )
    historical_forecast.add_argument("--request")
    historical_forecast.add_argument("--write", action="store_true", help="refresh generated historical baseline outputs")
    historical_forecast.set_defaults(func=cmd_historical_forecast)

    method_comparison = subparsers.add_parser(
        "method-comparison",
        help="check or refresh baseline method comparisons",
    )
    method_comparison.add_argument("--check", action="store_true", help="check generated method-comparison drift")
    method_comparison.add_argument("--write", action="store_true", help="refresh generated method comparison")
    method_comparison.set_defaults(func=cmd_method_comparison)

    method_selection = subparsers.add_parser(
        "method-selection",
        help="check or refresh forecast method selection",
    )
    method_selection.add_argument("--request")
    method_selection.add_argument("--check", action="store_true", help="check generated method-selection drift")
    method_selection.add_argument("--write", action="store_true", help="refresh generated method selection")
    method_selection.set_defaults(func=cmd_method_selection)

    setup_benchmark = subparsers.add_parser(
        "setup-benchmark",
        help="check, refresh, or print setup-specific benchmark gates",
    )
    setup_benchmark.add_argument(
        "--case",
        choices=["accepted", "accepted_partial", "needs_confirmation", "rejected"],
        help="print one setup benchmark gate",
    )
    setup_benchmark.add_argument("--check", action="store_true", help="check generated setup benchmark gate drift")
    setup_benchmark.add_argument("--write", action="store_true", help="refresh setup benchmark gate fixtures")
    setup_benchmark.set_defaults(func=cmd_setup_benchmark)

    setup_method = subparsers.add_parser(
        "setup-method",
        help="check, refresh, or print setup-aware forecast method decisions",
    )
    setup_method.add_argument(
        "--case",
        choices=["accepted", "accepted_partial", "needs_confirmation", "rejected"],
        help="print one setup method decision",
    )
    setup_method.add_argument("--check", action="store_true", help="check generated setup method decision drift")
    setup_method.add_argument("--write", action="store_true", help="refresh setup method decision fixtures")
    setup_method.set_defaults(func=cmd_setup_method)

    setup_forecast = subparsers.add_parser(
        "setup-forecast",
        help="check or refresh setup-aware forecast execution records",
    )
    setup_forecast.add_argument("--check", action="store_true", help="check generated setup forecast drift")
    setup_forecast.add_argument("--write", action="store_true", help="refresh setup forecast execution records")
    setup_forecast.set_defaults(func=cmd_setup_forecast)

    source_handoff_forecast = subparsers.add_parser(
        "source-handoff-forecast",
        help="check, refresh, or print explicit setup forecasts from source handoff method gates",
    )
    source_handoff_forecast.add_argument(
        "--case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="print one source-handoff setup forecast run",
    )
    source_handoff_forecast.add_argument("--check", action="store_true", help="check generated source-handoff forecast drift")
    source_handoff_forecast.add_argument("--write", action="store_true", help="refresh source-handoff forecast records")
    source_handoff_forecast.set_defaults(func=cmd_source_handoff_forecast)

    recalculation = subparsers.add_parser(
        "recalculation",
        help="check or refresh fixture-safe recalculation history records",
    )
    recalculation.add_argument("--check", action="store_true", help="check generated recalculation records")
    recalculation.add_argument("--write", action="store_true", help="refresh recalculation history records")
    recalculation.set_defaults(func=cmd_recalculation)

    agent_envelopes = subparsers.add_parser(
        "agent-envelopes",
        help="check, refresh, or print transport-neutral agent adapter envelopes",
    )
    agent_envelopes.add_argument("--check", action="store_true", help="check generated agent-envelope drift")
    agent_envelopes.add_argument("--write", action="store_true", help="refresh generated agent envelopes")
    agent_envelopes.set_defaults(func=cmd_agent_envelopes)

    agent_protocol_map = subparsers.add_parser(
        "agent-protocol-map",
        help="check, refresh, or print the mapping for future agent protocol adapters",
    )
    agent_protocol_map.add_argument("--check", action="store_true", help="check generated protocol-map drift")
    agent_protocol_map.add_argument("--write", action="store_true", help="refresh generated protocol map")
    agent_protocol_map.set_defaults(func=cmd_agent_protocol_map)

    forecast_run = subparsers.add_parser(
        "forecast-run",
        help="check, refresh, or print the fixture-safe agent forecast run summary",
    )
    forecast_run.add_argument("--request")
    forecast_run.add_argument("--max-bytes", type=int)
    forecast_run.add_argument("--check", action="store_true", help="check generated forecast-run drift")
    forecast_run.add_argument("--write", action="store_true", help="refresh generated forecast-run summary")
    forecast_run.set_defaults(func=cmd_forecast_run)

    forecast_run_matrix = subparsers.add_parser(
        "forecast-run-matrix",
        help="check, refresh, or print forecast-run outcome classes and agent next actions",
    )
    forecast_run_matrix.add_argument("--check", action="store_true", help="check generated forecast-run matrix drift")
    forecast_run_matrix.add_argument("--write", action="store_true", help="refresh generated forecast-run matrix")
    forecast_run_matrix.set_defaults(func=cmd_forecast_run_matrix)

    forecast_runbook = subparsers.add_parser(
        "forecast-runbook",
        help="check, refresh, or print the agent forecast-run runbook",
    )
    forecast_runbook.add_argument("--check", action="store_true", help="check generated forecast-runbook drift")
    forecast_runbook.add_argument("--write", action="store_true", help="refresh generated forecast-runbook")
    forecast_runbook.set_defaults(func=cmd_forecast_runbook)

    source_handoff_runbook = subparsers.add_parser(
        "source-handoff-runbook",
        help="check, refresh, or print the agent source-handoff setup runbook",
    )
    source_handoff_runbook.add_argument(
        "--check",
        action="store_true",
        help="check generated source-handoff setup runbook drift",
    )
    source_handoff_runbook.add_argument(
        "--write",
        action="store_true",
        help="refresh generated source-handoff setup runbook",
    )
    source_handoff_runbook.set_defaults(func=cmd_source_handoff_runbook)

    private_setup_workflow = subparsers.add_parser(
        "private-setup-workflow",
        help="check, refresh, or print the domain-agnostic private setup workflow",
    )
    private_setup_workflow.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup workflow drift",
    )
    private_setup_workflow.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup workflow",
    )
    private_setup_workflow.set_defaults(func=cmd_private_setup_workflow)

    private_source_adapters = subparsers.add_parser(
        "private-source-adapters",
        help="check, refresh, or print private source adapter capability declarations",
    )
    private_source_adapters.add_argument(
        "--check",
        action="store_true",
        help="check generated private source adapter capability drift",
    )
    private_source_adapters.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private source adapter capability declarations",
    )
    private_source_adapters.set_defaults(func=cmd_private_source_adapters)

    private_source_adapter_outcomes = subparsers.add_parser(
        "private-source-adapter-outcomes",
        help="check, refresh, or print private source adapter outcome decisions",
    )
    private_source_adapter_outcomes.add_argument(
        "--check",
        action="store_true",
        help="check generated private source adapter outcome matrix drift",
    )
    private_source_adapter_outcomes.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private source adapter outcome matrix",
    )
    private_source_adapter_outcomes.set_defaults(func=cmd_private_source_adapter_outcomes)

    private_source_adapter_bridge = subparsers.add_parser(
        "private-source-adapter-bridge",
        help="check, refresh, or print private source adapter intake bridge decisions",
    )
    private_source_adapter_bridge.add_argument(
        "--check",
        action="store_true",
        help="check generated private source adapter intake bridge drift",
    )
    private_source_adapter_bridge.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private source adapter intake bridge",
    )
    private_source_adapter_bridge.set_defaults(func=cmd_private_source_adapter_bridge)

    agent_call = subparsers.add_parser(
        "agent-call",
        help="run one local agent adapter operation and return one envelope",
    )
    agent_call.add_argument(
        "--operation",
        choices=[
            "forecast_request_validation",
            "evidence_plan",
            "evidence_trace",
            "forecast_card",
            "lifecycle_bundle",
            "resolution_status",
            "scoring_summary",
        ],
        required=True,
    )
    agent_call.add_argument("--request", default="spec/fixtures/requests/auto-weather-logistics-request.json")
    agent_call.add_argument("--forecast-id", default="forecast-602")
    agent_call.add_argument("--question-id", default="question-601")
    agent_call.add_argument("--max-bytes", type=int, default=65536)
    agent_call.add_argument("--caller-intent", default="Call one local OPE agent adapter operation.")
    agent_call.set_defaults(func=cmd_agent_call)

    mcp_stdio = subparsers.add_parser(
        "mcp-stdio",
        help="run the local MCP stdio scaffold for OPE agent adapter tools",
    )
    mcp_stdio.set_defaults(func=cmd_mcp_stdio)

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
