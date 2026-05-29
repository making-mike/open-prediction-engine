#!/usr/bin/env python3
"""Small local CLI for OPE repository workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    try:
        if sys.stdout.isatty():
            completed = subprocess.run(command, cwd=ROOT, check=False)
            if completed.returncode in (130, -2):
                raise SystemExit(130)
            completed.check_returncode()
            return
        run_forwarding_output(command, check=True)
    except KeyboardInterrupt as exc:
        raise SystemExit(130) from exc
    except subprocess.CalledProcessError as exc:
        if exc.returncode in (130, -2):
            raise SystemExit(130) from exc
        raise


def run_forwarding_output(command: list[str], *, check: bool) -> int:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        sys.stdout.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            command,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    return completed.returncode


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
    transit_api_connector_command = [sys.executable, "scripts/connect_transit_api.py"]
    domain_setups_command = [sys.executable, "scripts/generate_domain_setups.py"]
    transit_delay_forecast_command = [sys.executable, "scripts/run_transit_delay_forecast.py"]
    transit_delay_forward_command = [sys.executable, "scripts/run_transit_delay_forward.py"]
    transit_forward_resolver_command = [sys.executable, "scripts/resolve_due_transit_forward_runs.py"]
    resolution_jobs_command = [sys.executable, "scripts/generate_resolution_jobs.py"]
    resolution_scheduler_command = [sys.executable, "scripts/run_resolution_scheduler.py"]
    resolution_runtime_reliability_command = [sys.executable, "scripts/generate_resolution_runtime_reliability.py"]
    transit_forward_run_corpus_command = [sys.executable, "scripts/generate_transit_forward_run_corpus.py"]
    transit_corpus_growth_command = [sys.executable, "scripts/generate_transit_corpus_growth_loop.py"]
    transit_track_record_gate_command = [sys.executable, "scripts/generate_transit_baseline_track_record_gate.py"]
    transit_method_options_command = [sys.executable, "scripts/generate_transit_method_options.py"]
    transit_live_evidence_promotion_command = [sys.executable, "scripts/generate_transit_live_evidence_promotion.py"]
    source_intake_command = [sys.executable, "scripts/generate_source_intake.py"]
    source_builder_command = [sys.executable, "scripts/build_source_manifest.py"]
    source_adapter_output_command = [sys.executable, "scripts/generate_source_adapter_output.py"]
    source_adapter_intake_command = [sys.executable, "scripts/generate_source_adapter_intake.py"]
    source_quality_command = [sys.executable, "scripts/generate_source_quality_mapping_confidence.py"]
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
    local_source_runtime_command = [sys.executable, "scripts/generate_local_source_runtime.py"]
    source_handoff_resolution_command = [sys.executable, "scripts/resolve_source_handoff_outcome.py"]
    source_handoff_runbook_command = [sys.executable, "scripts/generate_source_handoff_setup_runbook.py"]
    private_setup_workflow_command = [sys.executable, "scripts/generate_private_setup_workflow.py"]
    private_source_adapters_command = [sys.executable, "scripts/generate_private_source_adapter_capabilities.py"]
    private_source_adapter_outcomes_command = [sys.executable, "scripts/generate_private_source_adapter_outcome_matrix.py"]
    private_source_adapter_bridge_command = [sys.executable, "scripts/generate_private_source_adapter_intake_bridge.py"]
    private_source_kind_selection_command = [sys.executable, "scripts/generate_private_source_kind_selection_examples.py"]
    private_setup_requests_command = [sys.executable, "scripts/generate_private_setup_requests.py"]
    private_setup_actions_command = [sys.executable, "scripts/generate_private_setup_first_actions.py"]
    private_setup_action_runbook_command = [sys.executable, "scripts/generate_private_setup_first_action_runbook.py"]
    private_setup_agent_bundles_command = [sys.executable, "scripts/generate_private_setup_agent_bundles.py"]
    private_setup_orchestrator_command = [sys.executable, "scripts/generate_private_setup_orchestrator.py"]
    agent_pilot_validation_command = [sys.executable, "scripts/generate_agent_pilot_validation.py"]
    pilot_evidence_command = [sys.executable, "scripts/generate_pilot_evidence_ledger.py"]
    pilot_session_packet_command = [sys.executable, "scripts/generate_pilot_session_packet.py"]
    pilot_summary_intake_command = [sys.executable, "scripts/generate_pilot_summary_intake.py"]
    local_usage_trace_command = [sys.executable, "scripts/generate_local_usage_trace.py"]
    developer_adoption_command = [sys.executable, "scripts/generate_developer_adoption_surface.py"]
    expansion_readiness_command = [sys.executable, "scripts/generate_expansion_readiness_gate.py"]
    repeating_prediction_setup_command = [sys.executable, "scripts/generate_repeating_prediction_setup.py"]
    prediction_campaign_manifest_command = [sys.executable, "scripts/generate_prediction_campaign_manifest.py"]
    prediction_campaign_runner_command = [sys.executable, "scripts/generate_prediction_campaign_runner.py"]
    prediction_campaign_forecast_creation_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_forecast_creation.py",
    ]
    prediction_campaign_forecast_artifact_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_forecast_artifact.py",
    ]
    prediction_campaign_forecast_write_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_forecast_write.py",
    ]
    prediction_campaign_resume_command = [sys.executable, "scripts/generate_prediction_campaign_resume.py"]
    private_setup_adapter_runbook_command = [sys.executable, "scripts/generate_private_setup_adapter_chain_runbook.py"]
    private_setup_adapter_conformance_command = [sys.executable, "scripts/generate_private_setup_adapter_conformance_matrix.py"]
    private_setup_adapter_conformance_summary_command = [sys.executable, "scripts/generate_private_setup_adapter_conformance_summary.py"]
    private_source_kind_query_matrix_command = [sys.executable, "scripts/generate_private_source_kind_query_matrix.py"]
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
        transit_api_connector_command.append("--write")
        domain_setups_command.append("--write")
        transit_delay_forecast_command.append("--write")
        transit_delay_forward_command.append("--write")
        transit_forward_resolver_command.append("--write")
        resolution_jobs_command.append("--write")
        resolution_scheduler_command.append("--write")
        resolution_runtime_reliability_command.append("--write")
        transit_forward_run_corpus_command.append("--write")
        transit_corpus_growth_command.append("--write")
        transit_track_record_gate_command.append("--write")
        transit_method_options_command.append("--write")
        transit_live_evidence_promotion_command.append("--write")
        source_intake_command.append("--write")
        source_builder_command.append("--write")
        source_adapter_output_command.append("--write")
        source_adapter_intake_command.append("--write")
        source_quality_command.append("--write")
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
        local_source_runtime_command.append("--write")
        source_handoff_resolution_command.append("--write")
        source_handoff_runbook_command.append("--write")
        private_setup_workflow_command.append("--write")
        private_source_adapters_command.append("--write")
        private_source_adapter_outcomes_command.append("--write")
        private_source_adapter_bridge_command.append("--write")
        private_source_kind_selection_command.append("--write")
        private_setup_requests_command.append("--write")
        private_setup_actions_command.append("--write")
        private_setup_action_runbook_command.append("--write")
        private_setup_agent_bundles_command.append("--write")
        private_setup_orchestrator_command.append("--write")
        agent_pilot_validation_command.append("--write")
        pilot_evidence_command.append("--write")
        pilot_session_packet_command.append("--write")
        pilot_summary_intake_command.append("--write")
        local_usage_trace_command.append("--write")
        developer_adoption_command.append("--write")
        expansion_readiness_command.append("--write")
        repeating_prediction_setup_command.append("--write")
        prediction_campaign_manifest_command.append("--write")
        prediction_campaign_runner_command.append("--write")
        prediction_campaign_forecast_creation_command.append("--write")
        prediction_campaign_forecast_artifact_command.append("--write")
        prediction_campaign_forecast_write_command.append("--write")
        prediction_campaign_resume_command.append("--write")
        private_setup_adapter_runbook_command.append("--write")
        private_setup_adapter_conformance_command.append("--write")
        private_setup_adapter_conformance_summary_command.append("--write")
        private_source_kind_query_matrix_command.append("--write")
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
        transit_api_connector_command.append("--check")
        domain_setups_command.append("--check")
        transit_delay_forecast_command.append("--check")
        transit_delay_forward_command.append("--check")
        transit_forward_resolver_command.append("--check")
        resolution_jobs_command.append("--check")
        resolution_scheduler_command.append("--check")
        resolution_runtime_reliability_command.append("--check")
        transit_forward_run_corpus_command.append("--check")
        transit_corpus_growth_command.append("--check")
        transit_track_record_gate_command.append("--check")
        transit_method_options_command.append("--check")
        transit_live_evidence_promotion_command.append("--check")
        source_intake_command.append("--check")
        source_builder_command.append("--check")
        source_adapter_output_command.append("--check")
        source_adapter_intake_command.append("--check")
        source_quality_command.append("--check")
        source_handoff_command.append("--check")
        source_handoff_method_command.append("--check")
        method_comparison_command.append("--check")
        method_selection_command.append("--check")
        setup_benchmark_command.append("--check")
        setup_method_command.append("--check")
        setup_forecast_command.append("--check")
        source_handoff_forecast_command.append("--check")
        local_source_runtime_command.append("--check")
        source_handoff_runbook_command.append("--check")
        private_setup_workflow_command.append("--check")
        private_source_adapters_command.append("--check")
        private_source_adapter_outcomes_command.append("--check")
        private_source_adapter_bridge_command.append("--check")
        private_source_kind_selection_command.append("--check")
        private_setup_requests_command.append("--check")
        private_setup_actions_command.append("--check")
        private_setup_action_runbook_command.append("--check")
        private_setup_agent_bundles_command.append("--check")
        private_setup_orchestrator_command.append("--check")
        agent_pilot_validation_command.append("--check")
        pilot_evidence_command.append("--check")
        pilot_session_packet_command.append("--check")
        pilot_summary_intake_command.append("--check")
        local_usage_trace_command.append("--check")
        developer_adoption_command.append("--check")
        expansion_readiness_command.append("--check")
        repeating_prediction_setup_command.append("--check")
        prediction_campaign_manifest_command.append("--check")
        prediction_campaign_runner_command.append("--check")
        prediction_campaign_forecast_creation_command.append("--check")
        prediction_campaign_forecast_artifact_command.append("--check")
        prediction_campaign_forecast_write_command.append("--check")
        prediction_campaign_resume_command.append("--check")
        private_setup_adapter_runbook_command.append("--check")
        private_setup_adapter_conformance_command.append("--check")
        private_setup_adapter_conformance_summary_command.append("--check")
        private_source_kind_query_matrix_command.append("--check")
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
    run(transit_api_connector_command)
    run(domain_setups_command)
    run(transit_delay_forecast_command)
    run(transit_delay_forward_command)
    run(transit_forward_resolver_command)
    run(resolution_jobs_command)
    run(resolution_scheduler_command)
    run(resolution_runtime_reliability_command)
    run(transit_forward_run_corpus_command)
    run(transit_corpus_growth_command)
    run(transit_track_record_gate_command)
    run(transit_method_options_command)
    run(transit_live_evidence_promotion_command)
    run(source_intake_command)
    run(source_builder_command)
    run(source_adapter_output_command)
    run(source_adapter_intake_command)
    run(source_quality_command)
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
    run(local_source_runtime_command)
    run(source_handoff_resolution_command)
    run(source_handoff_runbook_command)
    run(private_setup_workflow_command)
    run(private_source_adapters_command)
    run(private_source_adapter_outcomes_command)
    run(private_source_adapter_bridge_command)
    run(private_setup_requests_command)
    run(private_setup_actions_command)
    run(private_setup_action_runbook_command)
    run(private_setup_agent_bundles_command)
    run(private_setup_orchestrator_command)
    run(agent_pilot_validation_command)
    run(pilot_evidence_command)
    run(pilot_session_packet_command)
    run(pilot_summary_intake_command)
    run(local_usage_trace_command)
    run(developer_adoption_command)
    run(expansion_readiness_command)
    run(repeating_prediction_setup_command)
    run(prediction_campaign_manifest_command)
    run(prediction_campaign_runner_command)
    run(prediction_campaign_forecast_creation_command)
    run(prediction_campaign_forecast_artifact_command)
    run(prediction_campaign_forecast_write_command)
    run(prediction_campaign_resume_command)
    run(private_setup_adapter_runbook_command)
    run(private_setup_adapter_conformance_command)
    run(private_setup_adapter_conformance_summary_command)
    run(private_source_kind_selection_command)
    run(private_source_kind_query_matrix_command)
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


def cmd_transit_api_connector(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/connect_transit_api.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    if args.live:
        command.append("--live")
    if args.save_local:
        command.append("--save-local")
    if args.input_protobuf:
        command.extend(["--input-protobuf", args.input_protobuf])
    if args.schedule_join:
        command.append("--schedule-join")
    if args.static_gtfs:
        command.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        command.append("--download-static-gtfs")
    if args.workspace:
        command.extend(["--workspace", args.workspace])
    if args.timeout is not None:
        command.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        command.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    if args.network:
        command.extend(["--network", args.network])
    if args.geography:
        command.extend(["--geography", args.geography])
    if args.service_window:
        command.extend(["--service-window", args.service_window])
    if args.service_date:
        command.extend(["--service-date", args.service_date])
    if args.forecast_close_time:
        command.extend(["--forecast-close-time", args.forecast_close_time])
    if args.late_seconds is not None:
        command.extend(["--late-seconds", str(args.late_seconds)])
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


def cmd_transit_delay_forecast(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_transit_delay_forecast.py"]
    if args.weather_forecast:
        command.extend(["--weather-forecast", args.weather_forecast])
    if args.historical_delays:
        command.extend(["--historical-delays", args.historical_delays])
    if args.trip_updates:
        command.extend(["--trip-updates", args.trip_updates])
    if args.unresolved:
        command.append("--unresolved")
    if args.network:
        command.extend(["--network", args.network])
    if args.geography:
        command.extend(["--geography", args.geography])
    if args.service_window:
        command.extend(["--service-window", args.service_window])
    if args.service_date:
        command.extend(["--service-date", args.service_date])
    if args.late_seconds is not None:
        command.extend(["--late-seconds", str(args.late_seconds)])
    if args.event_threshold is not None:
        command.extend(["--event-threshold", str(args.event_threshold)])
    if args.min_observations is not None:
        command.extend(["--min-observations", str(args.min_observations)])
    if args.generated_at:
        command.extend(["--generated-at", args.generated_at])
    if args.forecasted_at:
        command.extend(["--forecasted-at", args.forecasted_at])
    if args.forecast_close_time:
        command.extend(["--forecast-close-time", args.forecast_close_time])
    if args.horizon_start:
        command.extend(["--horizon-start", args.horizon_start])
    if args.horizon_end:
        command.extend(["--horizon-end", args.horizon_end])
    if args.resolve_at:
        command.extend(["--resolve-at", args.resolve_at])
    if args.output_dir:
        command.extend(["--output-dir", args.output_dir])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_delay_forward_run(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_transit_delay_forward.py"]
    if args.phase:
        command.extend(["--phase", args.phase])
    if args.run_dir:
        command.extend(["--run-dir", args.run_dir])
    if args.run_state:
        command.extend(["--run-state", args.run_state])
    if args.weather_forecast:
        command.extend(["--weather-forecast", args.weather_forecast])
    if args.historical_delays:
        command.extend(["--historical-delays", args.historical_delays])
    if args.trip_updates:
        command.extend(["--trip-updates", args.trip_updates])
    if args.live_weather:
        command.append("--live-weather")
    if args.input_protobuf:
        command.extend(["--input-protobuf", args.input_protobuf])
    if args.static_gtfs:
        command.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        command.append("--download-static-gtfs")
    if args.timeout is not None:
        command.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        command.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    if args.network:
        command.extend(["--network", args.network])
    if args.geography:
        command.extend(["--geography", args.geography])
    if args.service_window:
        command.extend(["--service-window", args.service_window])
    if args.service_date:
        command.extend(["--service-date", args.service_date])
    if args.late_seconds is not None:
        command.extend(["--late-seconds", str(args.late_seconds)])
    if args.event_threshold is not None:
        command.extend(["--event-threshold", str(args.event_threshold)])
    if args.min_observations is not None:
        command.extend(["--min-observations", str(args.min_observations)])
    if args.generated_at:
        command.extend(["--generated-at", args.generated_at])
    if args.forecasted_at:
        command.extend(["--forecasted-at", args.forecasted_at])
    if args.forecast_close_time:
        command.extend(["--forecast-close-time", args.forecast_close_time])
    if args.horizon_start:
        command.extend(["--horizon-start", args.horizon_start])
    if args.horizon_end:
        command.extend(["--horizon-end", args.horizon_end])
    if args.resolve_at:
        command.extend(["--resolve-at", args.resolve_at])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolve_due_forward_runs(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/resolve_due_transit_forward_runs.py"]
    if args.live:
        command.append("--live")
    if args.execute:
        command.append("--execute")
    if args.workspace:
        command.extend(["--workspace", args.workspace])
    for run_state in args.run_state or []:
        command.extend(["--run-state", run_state])
    if args.now:
        command.extend(["--now", args.now])
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.trip_updates:
        command.extend(["--trip-updates", args.trip_updates])
    if args.input_protobuf:
        command.extend(["--input-protobuf", args.input_protobuf])
    if args.static_gtfs:
        command.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        command.append("--download-static-gtfs")
    if args.timeout is not None:
        command.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        command.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolution_jobs(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_resolution_jobs.py"]
    if args.live:
        command.append("--live")
    if args.workspace:
        command.extend(["--workspace", args.workspace])
    for run_state in args.run_state or []:
        command.extend(["--run-state", run_state])
    if args.campaign:
        command.extend(["--campaign", args.campaign])
    if args.now:
        command.extend(["--now", args.now])
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolution_scheduler(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/run_resolution_scheduler.py"]
    if args.live:
        command.append("--live")
    if args.watch:
        command.append("--watch")
    if args.execute:
        command.append("--execute")
    if args.workspace:
        command.extend(["--workspace", args.workspace])
    for run_state in args.run_state or []:
        command.extend(["--run-state", run_state])
    if args.campaign:
        command.extend(["--campaign", args.campaign])
    if args.limit is not None:
        command.extend(["--limit", str(args.limit)])
    if args.poll_seconds is not None:
        command.extend(["--poll-seconds", str(args.poll_seconds)])
    if args.max_ticks is not None:
        command.extend(["--max-ticks", str(args.max_ticks)])
    if args.log_file:
        command.extend(["--log-file", args.log_file])
    if args.output_format:
        command.extend(["--output-format", args.output_format])
    if args.trip_updates:
        command.extend(["--trip-updates", args.trip_updates])
    if args.input_protobuf:
        command.extend(["--input-protobuf", args.input_protobuf])
    if args.static_gtfs:
        command.extend(["--static-gtfs", args.static_gtfs])
    if args.download_static_gtfs:
        command.append("--download-static-gtfs")
    if args.timeout is not None:
        command.extend(["--timeout", str(args.timeout)])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.static_gtfs_max_bytes is not None:
        command.extend(["--static-gtfs-max-bytes", str(args.static_gtfs_max_bytes)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_resolution_runtime_reliability(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_resolution_runtime_reliability.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_forward_run_corpus(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_transit_forward_run_corpus.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_corpus_growth(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_transit_corpus_growth_loop.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_track_record_gate(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_transit_baseline_track_record_gate.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_method_options(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_transit_method_options.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_transit_live_evidence_promotion(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_transit_live_evidence_promotion.py"]
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


def cmd_source_adapter_output(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_adapter_output.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_adapter_intake(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_adapter_intake.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_quality(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_quality_mapping_confidence.py"]
    if args.case:
        command.extend(["--case", args.case])
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


def cmd_local_source_runtime(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_local_source_runtime.py"]
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


def cmd_private_source_kind_selection(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_source_kind_selection_examples.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_source_kind_query_matrix(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_source_kind_query_matrix.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_requests(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_requests.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_actions(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_first_actions.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_action(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/private_setup_action_dispatcher.py"]
    if args.request_id:
        command.extend(["--request-id", args.request_id])
    if args.input:
        command.extend(["--input", args.input])
    raise SystemExit(run_forwarding_output(command, check=False))


def cmd_private_setup_action_runbook(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_first_action_runbook.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_bundles(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_agent_bundles.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_orchestrator(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_orchestrator.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_pilot_validation(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_pilot_validation.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_evidence(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_evidence_ledger.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_session_packet(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_session_packet.py"]
    if args.task:
        command.extend(["--task", args.task])
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_summary_intake(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_summary_intake.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_local_usage_trace(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_local_usage_trace.py"]
    if args.event:
        command.extend(["--event", args.event])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_developer_adoption(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_developer_adoption_surface.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_expansion_readiness(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_expansion_readiness_gate.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_repeating_prediction_setup(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_repeating_prediction_setup.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_prediction_campaign(args: argparse.Namespace) -> None:
    if args.action == "start":
        command = [sys.executable, "scripts/generate_prediction_campaign_runner.py"]
        if args.check:
            command.append("--check")
        if args.write:
            command.append("--write")
        run(command)
        return
    if args.action == "forecast-create":
        command = [sys.executable, "scripts/generate_prediction_campaign_forecast_creation.py"]
        if args.check:
            command.append("--check")
        if args.write:
            command.append("--write")
        run(command)
        return
    if args.action == "forecast-artifact":
        command = [sys.executable, "scripts/generate_prediction_campaign_forecast_artifact.py"]
        if args.check:
            command.append("--check")
        if args.write:
            command.append("--write")
        run(command)
        return
    if args.action == "forecast-write":
        command = [sys.executable, "scripts/generate_prediction_campaign_forecast_write.py"]
        if args.check:
            command.append("--check")
        if args.write:
            command.append("--write")
        run(command)
        return
    if args.action == "resume":
        command = [sys.executable, "scripts/generate_prediction_campaign_resume.py"]
        if args.check:
            command.append("--check")
        if args.write:
            command.append("--write")
        run(command)
        return

    command = [sys.executable, "scripts/generate_prediction_campaign_manifest.py"]
    if args.action != "manifest":
        command.extend(["--view", args.action])
    if args.case:
        command.extend(["--case", args.case])
    if args.plan_count is not None:
        command.extend(["--plan-count", str(args.plan_count)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_adapter_runbook(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_adapter_chain_runbook.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_adapter_conformance(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_adapter_conformance_matrix.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_adapter_conformance_summary(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_adapter_conformance_summary.py"]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_setup_bundle(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_setup_agent_bundles.py"]
    if args.request_id:
        command.extend(["--request-id", args.request_id])
    if args.case:
        command.extend(["--case", args.case])
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
    if args.private_setup_request_id:
        command.extend(["--private-setup-request-id", args.private_setup_request_id])
    if args.private_setup_case:
        command.extend(["--private-setup-case", args.private_setup_case])
    if args.source_builder_case:
        command.extend(["--source-builder-case", args.source_builder_case])
    for item in args.source_builder_input or []:
        command.extend(["--source-builder-input", item])
    for item in args.source_builder_mapping_hint or []:
        command.extend(["--source-builder-mapping-hint", item])
    if args.source_kind:
        command.extend(["--source-kind", args.source_kind])
    if args.source_handoff_case:
        command.extend(["--source-handoff-case", args.source_handoff_case])
    if args.method_gate_case:
        command.extend(["--method-gate-case", args.method_gate_case])
    if args.forecast_execution_case:
        command.extend(["--forecast-execution-case", args.forecast_execution_case])
    raise SystemExit(run_forwarding_output(command, check=False))


def cmd_mcp_stdio(_args: argparse.Namespace) -> None:
    subprocess.run([sys.executable, "scripts/ope_mcp_stdio.py"], cwd=ROOT, check=True)


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

    transit_api_connector = subparsers.add_parser(
        "transit-api-connector",
        help="check, print, or explicitly run the HSL GTFS-RT transit API connector",
    )
    transit_api_connector.add_argument("--check", action="store_true", help="check generated connector drift")
    transit_api_connector.add_argument("--write", action="store_true", help="refresh generated connector fixture")
    transit_api_connector.add_argument("--live", action="store_true", help="perform an opt-in HSL GTFS-RT fetch")
    transit_api_connector.add_argument("--save-local", action="store_true", help="save live capture under .ope/live")
    transit_api_connector.add_argument("--input-protobuf", help="decode a local GTFS-RT protobuf capture")
    transit_api_connector.add_argument("--schedule-join", action="store_true", help="join TripUpdates to static GTFS and derive delay seconds")
    transit_api_connector.add_argument("--static-gtfs", help="path to an HSL static GTFS zip for --schedule-join")
    transit_api_connector.add_argument("--download-static-gtfs", action="store_true", help="download HSL static GTFS into the ignored workspace cache")
    transit_api_connector.add_argument("--workspace", help="ignored local live workspace")
    transit_api_connector.add_argument("--timeout", type=int)
    transit_api_connector.add_argument("--max-bytes", type=int)
    transit_api_connector.add_argument("--static-gtfs-max-bytes", type=int)
    transit_api_connector.add_argument("--network")
    transit_api_connector.add_argument("--geography")
    transit_api_connector.add_argument("--service-window")
    transit_api_connector.add_argument("--service-date")
    transit_api_connector.add_argument("--forecast-close-time")
    transit_api_connector.add_argument("--late-seconds", type=int)
    transit_api_connector.set_defaults(func=cmd_transit_api_connector)

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
        choices=["weather-logistics", "seaport-berth-availability", "weather-transit-delays"],
        help="print one setup record",
    )
    domain_setups.add_argument("--check", action="store_true", help="check generated domain setup drift")
    domain_setups.add_argument("--write", action="store_true", help="refresh generated domain setup records")
    domain_setups.set_defaults(func=cmd_domain_setups)

    transit_delay_forecast = subparsers.add_parser(
        "transit-delay-forecast",
        help="run a local weather-transit-delay forecast from approved CSV/JSON files",
    )
    transit_delay_forecast.add_argument("--weather-forecast", help="approved CSV/JSON weather forecast source")
    transit_delay_forecast.add_argument("--historical-delays", help="approved CSV/JSON historical delay source")
    transit_delay_forecast.add_argument("--trip-updates", help="approved CSV/JSON transit outcome rows")
    transit_delay_forecast.add_argument("--unresolved", action="store_true", help="forecast without resolution/scoring")
    transit_delay_forecast.add_argument("--network")
    transit_delay_forecast.add_argument("--geography")
    transit_delay_forecast.add_argument("--service-window")
    transit_delay_forecast.add_argument("--service-date")
    transit_delay_forecast.add_argument("--late-seconds", type=int)
    transit_delay_forecast.add_argument("--event-threshold", type=float)
    transit_delay_forecast.add_argument("--min-observations", type=int)
    transit_delay_forecast.add_argument("--generated-at")
    transit_delay_forecast.add_argument("--forecasted-at")
    transit_delay_forecast.add_argument("--forecast-close-time")
    transit_delay_forecast.add_argument("--horizon-start")
    transit_delay_forecast.add_argument("--horizon-end")
    transit_delay_forecast.add_argument("--resolve-at")
    transit_delay_forecast.add_argument("--output-dir")
    transit_delay_forecast.add_argument("--check", action="store_true", help="check generated transit forecast drift")
    transit_delay_forecast.add_argument("--write", action="store_true", help="refresh generated transit forecast outputs")
    transit_delay_forecast.set_defaults(func=cmd_transit_delay_forecast)

    transit_delay_forward_run = subparsers.add_parser(
        "transit-delay-forward-run",
        help="run the weather-transit-delay forecast-to-resolution workflow",
    )
    transit_delay_forward_run.add_argument("--phase", choices=["fixture", "forecast", "resolve", "full"], default="fixture")
    transit_delay_forward_run.add_argument("--run-dir", help="ignored local run directory for live phases")
    transit_delay_forward_run.add_argument("--run-state", help="saved forward-run-state.json for resolve phase")
    transit_delay_forward_run.add_argument("--weather-forecast", help="approved CSV/JSON weather forecast source")
    transit_delay_forward_run.add_argument("--historical-delays", help="approved CSV/JSON historical delay source")
    transit_delay_forward_run.add_argument("--trip-updates", help="approved CSV/JSON transit outcome rows")
    transit_delay_forward_run.add_argument("--live-weather", action="store_true", help="fetch Open-Meteo Helsinki weather for live phases")
    transit_delay_forward_run.add_argument("--input-protobuf", help="decode a local GTFS-RT protobuf capture for resolution")
    transit_delay_forward_run.add_argument("--static-gtfs", help="path to an HSL static GTFS zip for resolution schedule join")
    transit_delay_forward_run.add_argument("--download-static-gtfs", action="store_true", help="download HSL static GTFS into the ignored live workspace")
    transit_delay_forward_run.add_argument("--timeout", type=int)
    transit_delay_forward_run.add_argument("--max-bytes", type=int)
    transit_delay_forward_run.add_argument("--static-gtfs-max-bytes", type=int)
    transit_delay_forward_run.add_argument("--network")
    transit_delay_forward_run.add_argument("--geography")
    transit_delay_forward_run.add_argument("--service-window")
    transit_delay_forward_run.add_argument("--service-date")
    transit_delay_forward_run.add_argument("--late-seconds", type=int)
    transit_delay_forward_run.add_argument("--event-threshold", type=float)
    transit_delay_forward_run.add_argument("--min-observations", type=int)
    transit_delay_forward_run.add_argument("--generated-at")
    transit_delay_forward_run.add_argument("--forecasted-at")
    transit_delay_forward_run.add_argument("--forecast-close-time")
    transit_delay_forward_run.add_argument("--horizon-start")
    transit_delay_forward_run.add_argument("--horizon-end")
    transit_delay_forward_run.add_argument("--resolve-at")
    transit_delay_forward_run.add_argument("--check", action="store_true", help="check generated forward-run fixture drift")
    transit_delay_forward_run.add_argument("--write", action="store_true", help="refresh generated forward-run fixture")
    transit_delay_forward_run.set_defaults(func=cmd_transit_delay_forward_run)

    resolve_due_forward_runs = subparsers.add_parser(
        "resolve-due-forward-runs",
        help="scan and optionally resolve due weather-transit-delay forward runs",
    )
    resolve_due_forward_runs.add_argument("--live", action="store_true", help="scan ignored local live forward-run states")
    resolve_due_forward_runs.add_argument("--execute", action="store_true", help="execute checked resolver commands for due live runs")
    resolve_due_forward_runs.add_argument("--workspace", help="ignored local forward-run workspace")
    resolve_due_forward_runs.add_argument("--run-state", action="append", help="specific forward-run-state.json to scan")
    resolve_due_forward_runs.add_argument("--now", help="override current timestamp for deterministic scans")
    resolve_due_forward_runs.add_argument("--limit", type=int)
    resolve_due_forward_runs.add_argument("--trip-updates", help="approved CSV/JSON transit outcome rows for execution")
    resolve_due_forward_runs.add_argument("--input-protobuf", help="decode a local GTFS-RT protobuf capture for execution")
    resolve_due_forward_runs.add_argument("--static-gtfs", help="path to an HSL static GTFS zip for execution schedule join")
    resolve_due_forward_runs.add_argument("--download-static-gtfs", action="store_true", help="download HSL static GTFS during execution")
    resolve_due_forward_runs.add_argument("--timeout", type=int)
    resolve_due_forward_runs.add_argument("--max-bytes", type=int)
    resolve_due_forward_runs.add_argument("--static-gtfs-max-bytes", type=int)
    resolve_due_forward_runs.add_argument("--check", action="store_true", help="check generated resolver fixture drift")
    resolve_due_forward_runs.add_argument("--write", action="store_true", help="refresh generated resolver fixture")
    resolve_due_forward_runs.set_defaults(func=cmd_resolve_due_forward_runs)

    resolution_jobs = subparsers.add_parser(
        "resolution-jobs",
        help="inspect agent-facing resolution jobs without executing resolvers",
    )
    resolution_jobs.add_argument("--live", action="store_true", help="read ignored local forward-run state files")
    resolution_jobs.add_argument("--workspace", help="ignored local forward-run workspace")
    resolution_jobs.add_argument("--run-state", action="append", help="specific forward-run-state.json to inspect")
    resolution_jobs.add_argument("--campaign", help="include a checked prediction campaign in the registry")
    resolution_jobs.add_argument("--now", help="override current timestamp for deterministic scans")
    resolution_jobs.add_argument("--limit", type=int)
    resolution_jobs.add_argument("--check", action="store_true", help="check generated resolution-job fixture drift")
    resolution_jobs.add_argument("--write", action="store_true", help="refresh generated resolution-job fixture")
    resolution_jobs.set_defaults(func=cmd_resolution_jobs)

    resolution_scheduler = subparsers.add_parser(
        "resolution-scheduler",
        help="run a foreground terminal scheduler for due resolution jobs",
    )
    resolution_scheduler.add_argument("--live", action="store_true", help="read ignored local resolution jobs")
    resolution_scheduler.add_argument("--watch", action="store_true", help="keep polling in the foreground terminal")
    resolution_scheduler.add_argument("--execute", action="store_true", help="execute due jobs through the checked resolver")
    resolution_scheduler.add_argument("--workspace", help="ignored local forward-run workspace")
    resolution_scheduler.add_argument("--run-state", action="append", help="specific forward-run-state.json to watch")
    resolution_scheduler.add_argument("--campaign", help="include a checked prediction campaign in scheduler ticks")
    resolution_scheduler.add_argument("--limit", type=int)
    resolution_scheduler.add_argument("--poll-seconds", type=int)
    resolution_scheduler.add_argument("--max-ticks", type=int)
    resolution_scheduler.add_argument("--log-file")
    resolution_scheduler.add_argument(
        "--output-format",
        choices=["auto", "text", "jsonl"],
        help="watch stdout format; auto uses text for terminals and jsonl when captured",
    )
    resolution_scheduler.add_argument("--trip-updates", help="approved CSV/JSON transit outcome rows for resolver execution")
    resolution_scheduler.add_argument("--input-protobuf", help="decode a local GTFS-RT protobuf capture for resolver execution")
    resolution_scheduler.add_argument("--static-gtfs", help="path to an HSL static GTFS zip for resolver execution")
    resolution_scheduler.add_argument("--download-static-gtfs", action="store_true", help="download HSL static GTFS during resolver execution")
    resolution_scheduler.add_argument("--timeout", type=int)
    resolution_scheduler.add_argument("--max-bytes", type=int)
    resolution_scheduler.add_argument("--static-gtfs-max-bytes", type=int)
    resolution_scheduler.add_argument("--check", action="store_true", help="check generated scheduler fixture drift")
    resolution_scheduler.add_argument("--write", action="store_true", help="refresh generated scheduler fixture")
    resolution_scheduler.set_defaults(func=cmd_resolution_scheduler)

    resolution_runtime_reliability = subparsers.add_parser(
        "resolution-runtime-reliability",
        help="print checked resolution runtime failure and provenance guidance",
    )
    resolution_runtime_reliability.add_argument(
        "--check",
        action="store_true",
        help="check generated resolution runtime reliability drift",
    )
    resolution_runtime_reliability.add_argument(
        "--write",
        action="store_true",
        help="refresh generated resolution runtime reliability fixture",
    )
    resolution_runtime_reliability.set_defaults(func=cmd_resolution_runtime_reliability)

    transit_forward_run_corpus = subparsers.add_parser(
        "transit-forward-run-corpus",
        help="print checked public transport forward-run corpus counts and exclusions",
    )
    transit_forward_run_corpus.add_argument(
        "--check",
        action="store_true",
        help="check generated transit forward-run corpus drift",
    )
    transit_forward_run_corpus.add_argument(
        "--write",
        action="store_true",
        help="refresh generated transit forward-run corpus fixture",
    )
    transit_forward_run_corpus.set_defaults(func=cmd_transit_forward_run_corpus)

    transit_corpus_growth = subparsers.add_parser(
        "transit-corpus-growth",
        help="check, refresh, or print the transit corpus append-readiness loop",
    )
    transit_corpus_growth.add_argument(
        "--case",
        choices=[
            "comparable_resolved",
            "missing_outcome",
            "stale_evidence",
            "leakage_risk",
            "post_close_source",
            "incomparable_window",
        ],
        help="print one corpus growth candidate",
    )
    transit_corpus_growth.add_argument(
        "--check",
        action="store_true",
        help="check generated transit corpus growth loop drift",
    )
    transit_corpus_growth.add_argument(
        "--write",
        action="store_true",
        help="refresh generated transit corpus growth loop fixture",
    )
    transit_corpus_growth.set_defaults(func=cmd_transit_corpus_growth)

    transit_track_record_gate = subparsers.add_parser(
        "transit-track-record-gate",
        help="print checked public transport baseline track-record and calibration gate",
    )
    transit_track_record_gate.add_argument(
        "--check",
        action="store_true",
        help="check generated transit baseline track-record gate drift",
    )
    transit_track_record_gate.add_argument(
        "--write",
        action="store_true",
        help="refresh generated transit baseline track-record gate fixture",
    )
    transit_track_record_gate.set_defaults(func=cmd_transit_track_record_gate)

    transit_method_options = subparsers.add_parser(
        "transit-method-options",
        help="print checked public transport MVP method options and selection boundary",
    )
    transit_method_options.add_argument(
        "--check",
        action="store_true",
        help="check generated transit method options drift",
    )
    transit_method_options.add_argument(
        "--write",
        action="store_true",
        help="refresh generated transit method options fixture",
    )
    transit_method_options.set_defaults(func=cmd_transit_method_options)

    transit_live_evidence_promotion = subparsers.add_parser(
        "transit-live-evidence-promotion",
        help="print checked policy-bound live evidence promotion gate for transit runs",
    )
    transit_live_evidence_promotion.add_argument(
        "--check",
        action="store_true",
        help="check generated transit live evidence promotion drift",
    )
    transit_live_evidence_promotion.add_argument(
        "--write",
        action="store_true",
        help="refresh generated transit live evidence promotion fixtures",
    )
    transit_live_evidence_promotion.set_defaults(func=cmd_transit_live_evidence_promotion)

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

    source_adapter_output = subparsers.add_parser(
        "source-adapter-output",
        help="check, refresh, or print an external connector handoff into OPE source intake",
    )
    source_adapter_output.add_argument("--check", action="store_true", help="check generated source-adapter output drift")
    source_adapter_output.add_argument("--write", action="store_true", help="refresh generated source-adapter output")
    source_adapter_output.set_defaults(func=cmd_source_adapter_output)

    source_adapter_intake = subparsers.add_parser(
        "source-adapter-intake",
        help="check, refresh, or print external source-adapter intake routing",
    )
    source_adapter_intake.add_argument(
        "--case",
        choices=["accepted", "needs_confirmation", "insufficient_data", "rejected", "unsafe"],
        help="print one source adapter intake case",
    )
    source_adapter_intake.add_argument("--check", action="store_true", help="check generated source-adapter intake drift")
    source_adapter_intake.add_argument("--write", action="store_true", help="refresh generated source-adapter intake fixtures")
    source_adapter_intake.set_defaults(func=cmd_source_adapter_intake)

    source_quality = subparsers.add_parser(
        "source-quality",
        help="check, refresh, or print source quality and mapping confidence readbacks",
    )
    source_quality.add_argument(
        "--case",
        choices=[
            "builder_local_draft",
            "source_intake_accepted",
            "source_intake_partial",
            "source_intake_needs_confirmation",
            "adapter_insufficient_data",
            "source_intake_rejected",
            "adapter_unsafe",
        ],
        help="print one source quality case row",
    )
    source_quality.add_argument("--check", action="store_true", help="check generated source-quality drift")
    source_quality.add_argument("--write", action="store_true", help="refresh generated source-quality readback")
    source_quality.set_defaults(func=cmd_source_quality)

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

    local_source_runtime = subparsers.add_parser(
        "local-source-runtime",
        help="check, refresh, or print the approved local-folder source runtime",
    )
    local_source_runtime.add_argument(
        "--case",
        choices=[
            "approved_local_folder",
            "missing_approval",
            "credentials_detected",
            "unsafe_path",
            "oversized_response",
            "schema_mismatch",
            "leakage_indicator",
        ],
        help="print one local source runtime case",
    )
    local_source_runtime.add_argument("--check", action="store_true", help="check generated local source runtime drift")
    local_source_runtime.add_argument("--write", action="store_true", help="refresh generated local source runtime")
    local_source_runtime.set_defaults(func=cmd_local_source_runtime)

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

    private_source_kind_selection = subparsers.add_parser(
        "private-source-kind-selection",
        help="check, refresh, or print private source-kind selection examples",
    )
    private_source_kind_selection.add_argument(
        "--check",
        action="store_true",
        help="check generated private source-kind selection examples",
    )
    private_source_kind_selection.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private source-kind selection examples",
    )
    private_source_kind_selection.set_defaults(func=cmd_private_source_kind_selection)

    private_source_kind_query_matrix = subparsers.add_parser(
        "private-source-kind-query-matrix",
        help="check, refresh, or print private source-kind adapter query examples",
    )
    private_source_kind_query_matrix.add_argument(
        "--check",
        action="store_true",
        help="check generated private source-kind query matrix",
    )
    private_source_kind_query_matrix.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private source-kind query matrix",
    )
    private_source_kind_query_matrix.set_defaults(func=cmd_private_source_kind_query_matrix)

    private_setup_requests = subparsers.add_parser(
        "private-setup-requests",
        help="check, refresh, or print private setup request routing decisions",
    )
    private_setup_requests.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup request drift",
    )
    private_setup_requests.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup requests",
    )
    private_setup_requests.set_defaults(func=cmd_private_setup_requests)

    private_setup_actions = subparsers.add_parser(
        "private-setup-actions",
        help="check, refresh, or print generated private setup first-action fixtures",
    )
    private_setup_actions.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup first-action drift",
    )
    private_setup_actions.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup first actions",
    )
    private_setup_actions.set_defaults(func=cmd_private_setup_actions)

    private_setup_action = subparsers.add_parser(
        "private-setup-action",
        help="return the first safe action for one private setup request without execution",
    )
    private_setup_action.add_argument("--request-id", help="generated private setup request id")
    private_setup_action.add_argument("--input", help="JSON object containing one private setup request")
    private_setup_action.set_defaults(func=cmd_private_setup_action)

    private_setup_action_runbook = subparsers.add_parser(
        "private-setup-action-runbook",
        help="check, refresh, or print first-action runbook guidance for private setup",
    )
    private_setup_action_runbook.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup first-action runbook drift",
    )
    private_setup_action_runbook.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup first-action runbook",
    )
    private_setup_action_runbook.set_defaults(func=cmd_private_setup_action_runbook)

    private_setup_bundles = subparsers.add_parser(
        "private-setup-bundles",
        help="check, refresh, or print generated private setup agent bundles",
    )
    private_setup_bundles.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup agent bundle drift",
    )
    private_setup_bundles.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup agent bundles",
    )
    private_setup_bundles.set_defaults(func=cmd_private_setup_bundles)

    private_setup_orchestrator = subparsers.add_parser(
        "private-setup-orchestrator",
        help="check, refresh, or print the local private setup orchestrator summary",
    )
    private_setup_orchestrator.add_argument(
        "--case",
        choices=[
            "local_file_confirmed",
            "source_adapter_output_accepted",
            "missing_approval",
            "unconfirmed_mapping",
            "insufficient_data",
            "rejected_source",
            "unsafe_source",
            "response_too_large",
        ],
        help="print one orchestrator run",
    )
    private_setup_orchestrator.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup orchestrator drift",
    )
    private_setup_orchestrator.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup orchestrator",
    )
    private_setup_orchestrator.set_defaults(func=cmd_private_setup_orchestrator)

    agent_pilot_validation = subparsers.add_parser(
        "agent-pilot-validation",
        help="check, refresh, or print the local agent pilot validation pack",
    )
    agent_pilot_validation.add_argument(
        "--case",
        choices=[
            "local_file_setup_readback",
            "accepted_adapter_output_ready",
            "unsafe_source_block",
            "forecast_run_readback",
            "claim_gate_readback",
        ],
        help="print one pilot task scenario",
    )
    agent_pilot_validation.add_argument(
        "--check",
        action="store_true",
        help="check generated agent pilot validation pack drift",
    )
    agent_pilot_validation.add_argument(
        "--write",
        action="store_true",
        help="refresh generated agent pilot validation pack",
    )
    agent_pilot_validation.set_defaults(func=cmd_agent_pilot_validation)

    pilot_evidence = subparsers.add_parser(
        "pilot-evidence",
        help="check, refresh, or print the sanitized pilot evidence ledger",
    )
    pilot_evidence.add_argument(
        "--case",
        choices=[
            "accepted_sanitized_summary",
            "needs_redaction",
            "raw_transcript_blocked",
            "private_data_blocked",
            "claim_boundary_confusion",
        ],
        help="print one pilot evidence case",
    )
    pilot_evidence.add_argument(
        "--section",
        choices=["policy", "cases", "summary", "next-actions", "boundary"],
        help="print one pilot evidence ledger section",
    )
    pilot_evidence.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot evidence ledger drift",
    )
    pilot_evidence.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot evidence ledger",
    )
    pilot_evidence.set_defaults(func=cmd_pilot_evidence)

    pilot_session_packet = subparsers.add_parser(
        "pilot-session-packet",
        help="check, refresh, or print the real pilot-session collection packet",
    )
    pilot_session_packet.add_argument(
        "--task",
        choices=[
            "local_file_setup_readback",
            "accepted_adapter_output_ready",
            "unsafe_source_block",
            "forecast_run_readback",
            "claim_gate_readback",
        ],
        help="print one pilot session task card",
    )
    pilot_session_packet.add_argument(
        "--section",
        choices=["plan", "tasks", "template", "sanitization", "summary", "boundary"],
        help="print one pilot session packet section",
    )
    pilot_session_packet.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot session packet drift",
    )
    pilot_session_packet.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot session packet",
    )
    pilot_session_packet.set_defaults(func=cmd_pilot_session_packet)

    pilot_summary_intake = subparsers.add_parser(
        "pilot-summary-intake",
        help="check, refresh, or print the sanitized pilot-summary intake classifier",
    )
    pilot_summary_intake.add_argument(
        "--case",
        choices=[
            "accepted_local_setup_summary",
            "accepted_claim_confusion_summary",
            "needs_redaction_source_detail",
            "blocked_raw_transcript",
            "blocked_private_rows",
            "blocked_quality_claim",
        ],
        help="print one pilot summary intake case",
    )
    pilot_summary_intake.add_argument(
        "--section",
        choices=["policy", "cases", "rules", "summary", "boundary"],
        help="print one pilot summary intake section",
    )
    pilot_summary_intake.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot summary intake drift",
    )
    pilot_summary_intake.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot summary intake",
    )
    pilot_summary_intake.set_defaults(func=cmd_pilot_summary_intake)

    local_usage_trace = subparsers.add_parser(
        "local-usage-trace",
        help="check, refresh, or print the local MVP usage trace read model",
    )
    local_usage_trace.add_argument(
        "--event",
        choices=[
            "local_file_setup_readback",
            "unsafe_source_block",
            "forecast_run_readback",
            "forecast_card_read",
            "agent_call_forecast_card",
            "mcp_protocol_map_read",
            "release_surface_smoke",
            "response_too_large_readback",
            "claim_gate_readback",
            "agent_pilot_validation_read",
        ],
        help="print one usage trace event",
    )
    local_usage_trace.add_argument(
        "--check",
        action="store_true",
        help="check generated local usage trace drift",
    )
    local_usage_trace.add_argument(
        "--write",
        action="store_true",
        help="refresh generated local usage trace",
    )
    local_usage_trace.set_defaults(func=cmd_local_usage_trace)

    developer_adoption = subparsers.add_parser(
        "developer-adoption",
        help="check, refresh, or print the local MVP developer adoption surface",
    )
    developer_adoption.add_argument(
        "--section",
        choices=["quickstart", "scenario", "integrations", "release-notes", "type-decision"],
        help="print one developer adoption surface section",
    )
    developer_adoption.add_argument(
        "--check",
        action="store_true",
        help="check generated developer adoption surface drift",
    )
    developer_adoption.add_argument(
        "--write",
        action="store_true",
        help="refresh generated developer adoption surface",
    )
    developer_adoption.set_defaults(func=cmd_developer_adoption)

    expansion_readiness = subparsers.add_parser(
        "expansion-readiness",
        help="check, refresh, or print the post-MVP expansion readiness gate",
    )
    expansion_readiness.add_argument(
        "--section",
        choices=["evidence", "options", "sequence", "criteria", "boundary"],
        help="print one expansion readiness gate section",
    )
    expansion_readiness.add_argument(
        "--check",
        action="store_true",
        help="check generated expansion readiness gate drift",
    )
    expansion_readiness.add_argument(
        "--write",
        action="store_true",
        help="refresh generated expansion readiness gate",
    )
    expansion_readiness.set_defaults(func=cmd_expansion_readiness)

    repeating_prediction_setup = subparsers.add_parser(
        "repeating-prediction-setup",
        help="check, refresh, or print the repeating prediction setup contract",
    )
    repeating_prediction_setup.add_argument(
        "--case",
        choices=[
            "daily_100_run_transit_calibration",
            "hourly_short_horizon_count",
            "weekly_until_date_campaign",
            "open_ended_monitoring_campaign",
            "weekday_peak_window_campaign",
            "post_calibration_restart_campaign",
        ],
        help="print one repeating prediction setup example",
    )
    repeating_prediction_setup.add_argument(
        "--section",
        choices=["template", "schedules", "examples", "requirements", "boundary", "summary"],
        help="print one repeating prediction setup section",
    )
    repeating_prediction_setup.add_argument(
        "--check",
        action="store_true",
        help="check generated repeating prediction setup drift",
    )
    repeating_prediction_setup.add_argument(
        "--write",
        action="store_true",
        help="refresh generated repeating prediction setup",
    )
    repeating_prediction_setup.set_defaults(func=cmd_repeating_prediction_setup)

    prediction_campaign = subparsers.add_parser(
        "prediction-campaign",
        help="check, refresh, or print the local prediction campaign manifest",
    )
    prediction_campaign.add_argument(
        "action",
        nargs="?",
        choices=[
            "manifest",
            "plan",
            "status",
            "summary",
            "boundary",
            "start",
            "forecast-create",
            "forecast-artifact",
            "forecast-write",
            "resume",
        ],
        default="manifest",
        help="print the full manifest, one campaign readback, or a dry-run runner/forecast artifact readback",
    )
    prediction_campaign.add_argument(
        "--case",
        choices=[
            "daily_100_run_transit_calibration",
            "hourly_short_horizon_count",
            "weekly_until_date_campaign",
            "open_ended_monitoring_campaign",
            "weekday_peak_window_campaign",
            "post_calibration_restart_campaign",
        ],
        help="expand one repeating prediction setup example",
    )
    prediction_campaign.add_argument(
        "--plan-count",
        type=int,
        help="number of dry-run candidate runs to plan",
    )
    prediction_campaign.add_argument("--domain", help="dry-run runner domain selector")
    prediction_campaign.add_argument("--service-window", help="dry-run runner service window selector")
    prediction_campaign.add_argument("--interval", help="dry-run runner recurrence interval")
    prediction_campaign.add_argument("--count", type=int, help="dry-run runner finite run count")
    prediction_campaign.add_argument("--until", help="dry-run runner until-date boundary")
    prediction_campaign.add_argument("--calibration-target", type=int, help="dry-run runner calibration target")
    prediction_campaign.add_argument("--post-calibration-action", help="dry-run runner post-calibration action")
    prediction_campaign.add_argument("--post-calibration-delay", help="dry-run runner post-calibration delay")
    prediction_campaign.add_argument("--setup-json", help="dry-run runner setup JSON input path")
    prediction_campaign.add_argument("--manifest-json", help="dry-run runner manifest JSON input path")
    prediction_campaign.add_argument("--run-id", help="dry-run forecast creation run ID")
    prediction_campaign.add_argument(
        "--write-local",
        action="store_true",
        help="future explicit local forecast write flag; checked readbacks remain non-mutating",
    )
    prediction_campaign.add_argument(
        "--live-weather",
        action="store_true",
        help="dry-run flag for future explicit live weather fetching",
    )
    prediction_campaign.add_argument(
        "--execute-resolvers",
        action="store_true",
        help="dry-run flag for future explicit resolver execution",
    )
    prediction_campaign.add_argument(
        "--output-format",
        choices=["jsonl", "human"],
        help="dry-run runner output format",
    )
    prediction_campaign.add_argument(
        "--check",
        action="store_true",
        help="check generated prediction campaign manifest or runner drift",
    )
    prediction_campaign.add_argument(
        "--write",
        action="store_true",
        help="refresh generated prediction campaign manifest or runner",
    )
    prediction_campaign.set_defaults(func=cmd_prediction_campaign)

    private_setup_adapter_runbook = subparsers.add_parser(
        "private-setup-adapter-runbook",
        help="check, refresh, or print adapter-chain runbook guidance for private setup",
    )
    private_setup_adapter_runbook.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup adapter-chain runbook drift",
    )
    private_setup_adapter_runbook.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup adapter-chain runbook",
    )
    private_setup_adapter_runbook.set_defaults(func=cmd_private_setup_adapter_runbook)

    private_setup_adapter_conformance = subparsers.add_parser(
        "private-setup-adapter-conformance",
        help="check, refresh, or print private setup adapter conformance examples",
    )
    private_setup_adapter_conformance.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup adapter conformance matrix",
    )
    private_setup_adapter_conformance.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup adapter conformance matrix",
    )
    private_setup_adapter_conformance.set_defaults(func=cmd_private_setup_adapter_conformance)

    private_setup_adapter_conformance_summary = subparsers.add_parser(
        "private-setup-adapter-conformance-summary",
        help="check, refresh, or print compact private setup adapter conformance summary",
    )
    private_setup_adapter_conformance_summary.add_argument(
        "--check",
        action="store_true",
        help="check generated private setup adapter conformance summary",
    )
    private_setup_adapter_conformance_summary.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private setup adapter conformance summary",
    )
    private_setup_adapter_conformance_summary.set_defaults(func=cmd_private_setup_adapter_conformance_summary)

    private_setup_bundle = subparsers.add_parser(
        "private-setup-bundle",
        help="print one private setup agent bundle by request id or bad-request case",
    )
    private_setup_bundle.add_argument("--request-id", help="private setup request id")
    private_setup_bundle.add_argument(
        "--case",
        choices=["unknown_source_kind", "missing_approval"],
        help="bad-request example case",
    )
    private_setup_bundle.set_defaults(func=cmd_private_setup_bundle)

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
            "private_setup_bundle",
            "private_setup_adapter_runbook",
            "private_setup_adapter_conformance_summary",
            "private_source_adapter_guidance",
            "private_source_kind_selection",
            "private_setup_source_builder",
            "private_setup_source_handoff",
            "private_setup_method_gate",
            "private_setup_forecast_execution",
            "resolution_jobs",
            "resolution_scheduler_status",
            "resolution_status",
            "scoring_summary",
        ],
        required=True,
    )
    agent_call.add_argument("--request", default="spec/fixtures/requests/auto-weather-logistics-request.json")
    agent_call.add_argument("--forecast-id", default="forecast-602")
    agent_call.add_argument("--question-id", default="question-601")
    agent_call.add_argument("--private-setup-request-id")
    agent_call.add_argument(
        "--private-setup-case",
        choices=["unknown_source_kind", "missing_approval"],
    )
    agent_call.add_argument(
        "--source-builder-case",
        choices=["local_draft", "contains_secret", "unsupported_format", "oversized", "leakage"],
    )
    agent_call.add_argument(
        "--source-builder-input",
        action="append",
        help="caller-approved local source_role=path input for private setup source-builder adapter",
    )
    agent_call.add_argument(
        "--source-builder-mapping-hint",
        action="append",
        help="caller-provided source_role.source_field=target_field mapping hint",
    )
    agent_call.add_argument(
        "--source-kind",
        help="optional source kind for private_source_kind_selection selected-example reads",
    )
    agent_call.add_argument(
        "--source-handoff-case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="checked source-handoff fixture case for private setup source-handoff adapter",
    )
    agent_call.add_argument(
        "--method-gate-case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="checked source-handoff method-gate fixture case for private setup method-gate adapter",
    )
    agent_call.add_argument(
        "--forecast-execution-case",
        choices=[
            "unconfirmed_builder_draft",
            "confirmed_builder_draft",
            "insufficient_confirmed_builder_draft",
            "contains_secret",
            "unsupported_format",
            "oversized",
            "leakage",
        ],
        help="checked source-handoff forecast-execution fixture case for private setup forecast adapter",
    )
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
