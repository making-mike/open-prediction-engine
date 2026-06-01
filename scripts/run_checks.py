#!/usr/bin/env python3
"""Run dependency-free repository checks."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]


def py(script: str, *args: str) -> list[str]:
    return [sys.executable, script, *args]


CHECKS: list[list[str]] = [
    py("scripts/check_json.py"),
    py("scripts/check_schema_contracts.py"),
    py("scripts/check_ope_fixtures.py"),
    py("scripts/check_contract_validator.py"),
    py("scripts/generate_fixture_reports.py"),
    py("scripts/run_fixture_loop.py"),
    py("scripts/check_live_weather_connector.py"),
    py("scripts/check_live_weather_baseline.py"),
    py("scripts/check_live_weather_evidence.py"),
    py("scripts/resolve_live_weather_outcome.py"),
    py("scripts/plan_auto_evidence.py", "--check"),
    py("scripts/gather_auto_evidence.py", "--check"),
    py("scripts/generate_source_connectors.py", "--check"),
    py("scripts/check_source_connectors.py"),
    py("scripts/generate_live_connector_readiness.py", "--check"),
    py("scripts/check_live_connector_readiness.py"),
    py("scripts/connect_transit_api.py", "--check"),
    py("scripts/check_transit_api_connector.py"),
    py("scripts/check_live_capture_workspace.py"),
    py("scripts/generate_domain_setups.py", "--check"),
    py("scripts/check_domain_setups.py"),
    py("scripts/run_transit_delay_forecast.py", "--check"),
    py("scripts/check_transit_delay_forecast.py"),
    py("scripts/run_transit_delay_forward.py", "--check"),
    py("scripts/check_transit_delay_forward.py"),
    py("scripts/resolve_due_transit_forward_runs.py", "--check"),
    py("scripts/check_transit_forward_resolver.py"),
    py("scripts/generate_resolution_jobs.py", "--check"),
    py("scripts/generate_resolution_jobs.py", "--campaign", "predictioncampaign-001", "--check"),
    py("scripts/check_resolution_jobs.py"),
    py("scripts/run_resolution_scheduler.py", "--check"),
    py("scripts/run_resolution_scheduler.py", "--campaign", "predictioncampaign-001", "--check"),
    py("scripts/check_resolution_scheduler.py"),
    py("scripts/generate_resolution_runtime_reliability.py", "--check"),
    py("scripts/check_resolution_runtime_reliability.py"),
    py("scripts/generate_transit_forward_run_corpus.py", "--check"),
    py("scripts/check_transit_forward_run_corpus.py"),
    py("scripts/generate_transit_corpus_growth_loop.py", "--check"),
    py("scripts/check_transit_corpus_growth_loop.py"),
    py("scripts/generate_transit_baseline_track_record_gate.py", "--check"),
    py("scripts/check_transit_baseline_track_record_gate.py"),
    py("scripts/generate_transit_method_options.py", "--check"),
    py("scripts/check_transit_method_options.py"),
    py("scripts/generate_transit_live_evidence_promotion.py", "--check"),
    py("scripts/check_transit_live_evidence_promotion.py"),
    py("scripts/generate_source_intake.py", "--check"),
    py("scripts/check_source_intake.py"),
    py("scripts/build_source_manifest.py", "--check"),
    py("scripts/check_source_manifest_builder.py"),
    py("scripts/generate_source_adapter_output.py", "--check"),
    py("scripts/check_source_adapter_output.py"),
    py("scripts/generate_source_adapter_intake.py", "--check"),
    py("scripts/check_source_adapter_intake.py"),
    py("scripts/generate_source_quality_mapping_confidence.py", "--check"),
    py("scripts/check_source_quality_mapping_confidence.py"),
    py("scripts/generate_source_intake_handoff.py", "--check"),
    py("scripts/check_source_intake_handoff.py"),
    py("scripts/generate_source_handoff_method_gate.py", "--check"),
    py("scripts/check_source_handoff_method_gate.py"),
    py("scripts/run_auto_evidence_forecast.py"),
    py("scripts/resolve_auto_evidence_outcome.py"),
    py("scripts/run_historical_baseline_forecast.py"),
    py("scripts/check_historical_baseline_forecast.py"),
    py("scripts/run_forecast_pipeline.py"),
    py("scripts/resolve_pipeline_outcome.py"),
    py("scripts/generate_record_index.py"),
    py("scripts/generate_release_manifest.py"),
    py("scripts/check_mvp_release_surface.py"),
    py("scripts/check_benchmarks.py"),
    py("scripts/check_method_registry.py"),
    py("scripts/compare_forecasting_methods.py", "--check"),
    py("scripts/check_method_comparison.py"),
    py("scripts/select_forecasting_method.py", "--check"),
    py("scripts/check_method_selection.py"),
    py("scripts/generate_setup_benchmark_gate.py", "--check"),
    py("scripts/check_setup_benchmark_gate.py"),
    py("scripts/select_setup_method.py", "--check"),
    py("scripts/check_setup_method_decision.py"),
    py("scripts/run_setup_forecast.py", "--check"),
    py("scripts/check_setup_forecast.py"),
    py("scripts/run_source_handoff_forecast.py", "--check"),
    py("scripts/check_source_handoff_forecast.py"),
    py("scripts/generate_local_source_runtime.py", "--check"),
    py("scripts/check_local_source_runtime.py"),
    py("scripts/resolve_source_handoff_outcome.py"),
    py("scripts/check_source_handoff_resolution.py"),
    py("scripts/generate_source_handoff_setup_runbook.py", "--check"),
    py("scripts/check_source_handoff_setup_runbook.py"),
    py("scripts/generate_private_setup_workflow.py", "--check"),
    py("scripts/check_private_setup_workflow.py"),
    py("scripts/generate_private_source_adapter_capabilities.py", "--check"),
    py("scripts/check_private_source_adapter_capabilities.py"),
    py("scripts/generate_private_source_adapter_outcome_matrix.py", "--check"),
    py("scripts/check_private_source_adapter_outcome_matrix.py"),
    py("scripts/generate_private_source_adapter_intake_bridge.py", "--check"),
    py("scripts/check_private_source_adapter_intake_bridge.py"),
    py("scripts/generate_private_setup_requests.py", "--check"),
    py("scripts/check_private_setup_requests.py"),
    py("scripts/generate_private_setup_first_actions.py", "--check"),
    py("scripts/check_private_setup_first_actions.py"),
    py("scripts/generate_private_setup_first_action_runbook.py", "--check"),
    py("scripts/check_private_setup_first_action_runbook.py"),
    py("scripts/generate_private_setup_agent_bundles.py", "--check"),
    py("scripts/check_private_setup_agent_bundles.py"),
    py("scripts/generate_private_setup_orchestrator.py", "--check"),
    py("scripts/check_private_setup_orchestrator.py"),
    py("scripts/generate_agent_pilot_validation.py", "--check"),
    py("scripts/check_agent_pilot_validation.py"),
    py("scripts/generate_pilot_evidence_ledger.py", "--check"),
    py("scripts/check_pilot_evidence_ledger.py"),
    py("scripts/generate_pilot_session_packet.py", "--check"),
    py("scripts/check_pilot_session_packet.py"),
    py("scripts/generate_pilot_summary_intake.py", "--check"),
    py("scripts/check_pilot_summary_intake.py"),
    py("scripts/generate_local_usage_trace.py", "--check"),
    py("scripts/check_local_usage_trace.py"),
    py("scripts/generate_developer_adoption_surface.py", "--check"),
    py("scripts/check_developer_adoption_surface.py"),
    py("scripts/generate_expansion_readiness_gate.py", "--check"),
    py("scripts/check_expansion_readiness_gate.py"),
    py("scripts/generate_repeating_prediction_setup.py", "--check"),
    py("scripts/check_repeating_prediction_setup.py"),
    py("scripts/generate_prediction_campaign_manifest.py", "--check"),
    py("scripts/check_prediction_campaign_manifest.py"),
    py("scripts/generate_prediction_campaign_runner.py", "--check"),
    py("scripts/check_prediction_campaign_runner.py"),
    py("scripts/generate_prediction_campaign_forecast_creation.py", "--check"),
    py("scripts/check_prediction_campaign_forecast_creation.py"),
    py("scripts/generate_prediction_campaign_forecast_artifact.py", "--check"),
    py("scripts/check_prediction_campaign_forecast_artifact.py"),
    py("scripts/generate_prediction_campaign_forecast_write.py", "--check"),
    py("scripts/check_prediction_campaign_forecast_write.py"),
    py("scripts/generate_prediction_campaign_resolution_attempt.py", "--check"),
    py("scripts/check_prediction_campaign_resolution_attempt.py"),
    py("scripts/generate_prediction_campaign_doctor.py", "--check"),
    py("scripts/check_prediction_campaign_doctor.py"),
    py("scripts/generate_prediction_campaign_resume.py", "--check"),
    py("scripts/check_prediction_campaign_resume.py"),
    py("scripts/generate_prediction_campaign_evidence_ledger.py", "--check"),
    py("scripts/check_prediction_campaign_evidence_ledger.py"),
    py("scripts/generate_prediction_campaign_calibration_status.py", "--check"),
    py("scripts/check_prediction_campaign_calibration_status.py"),
    py("scripts/generate_prediction_campaign_method_update_gate.py", "--check"),
    py("scripts/check_prediction_campaign_method_update_gate.py"),
    py("scripts/generate_prediction_campaign_method_update_plan.py", "--check"),
    py("scripts/check_prediction_campaign_method_update_plan.py"),
    py("scripts/generate_prediction_campaign_method_update_action.py", "--check"),
    py("scripts/check_prediction_campaign_method_update_action.py"),
    py("scripts/generate_prediction_campaign_explain.py", "--check"),
    py("scripts/check_prediction_campaign_explain.py"),
    py("scripts/generate_helsinki_traffic_pilot_runbook.py", "--check"),
    py("scripts/check_helsinki_traffic_pilot_runbook.py"),
    py("scripts/generate_helsinki_traffic_pilot_readiness.py", "--check"),
    py("scripts/check_helsinki_traffic_pilot_readiness.py"),
    py("scripts/generate_recalculation_history.py", "--check"),
    py("scripts/check_recalculation_history.py"),
    py("scripts/run_agent_forecast.py", "--check"),
    py("scripts/check_agent_forecast_run.py"),
    py("scripts/generate_forecast_run_intake_matrix.py", "--check"),
    py("scripts/check_forecast_run_intake_matrix.py"),
    py("scripts/generate_agent_forecast_runbook.py", "--check"),
    py("scripts/check_agent_forecast_runbook.py"),
    py("scripts/build_agent_adapter_fixtures.py", "--check"),
    py("scripts/check_agent_adapter.py"),
    py("scripts/check_agent_adapter_dispatcher.py"),
    py("scripts/generate_agent_adapter_protocol_map.py", "--check"),
    py("scripts/check_agent_adapter_protocol_map.py"),
    py("scripts/generate_private_setup_adapter_chain_runbook.py", "--check"),
    py("scripts/check_private_setup_adapter_chain_runbook.py"),
    py("scripts/generate_private_setup_adapter_conformance_matrix.py", "--check"),
    py("scripts/check_private_setup_adapter_conformance_matrix.py"),
    py("scripts/generate_private_setup_adapter_conformance_summary.py", "--check"),
    py("scripts/check_private_setup_adapter_conformance_summary.py"),
    py("scripts/generate_private_source_kind_selection_examples.py", "--check"),
    py("scripts/check_private_source_kind_selection_examples.py"),
    py("scripts/generate_private_source_kind_query_matrix.py", "--check"),
    py("scripts/check_private_source_kind_query_matrix.py"),
    py("scripts/check_mcp_adapter.py"),
    py("scripts/check_read_access.py"),
    py("scripts/check_read_contracts.py"),
    py("scripts/check_forecast_requests.py"),
    py("scripts/check_auto_evidence_plan.py"),
    py("scripts/check_auto_evidence_gathering.py"),
    py("scripts/check_auto_evidence_forecast.py"),
    py("scripts/check_auto_evidence_resolution.py"),
    py("scripts/check_forecast_pipeline.py"),
    py("scripts/check_pipeline_resolution.py"),
    py("scripts/check_ci_workflow.py"),
    py("scripts/check_hardening.py"),
    py("scripts/check_cli.py"),
    py("scripts/check_fixtures.py"),
]


@dataclass(frozen=True)
class CheckResult:
    index: int
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float


def display_command(command: list[str]) -> str:
    return shlex.join(command)


def default_workers() -> int:
    value = os.environ.get("OPE_CHECK_WORKERS")
    if value:
        try:
            return max(1, int(value))
        except ValueError:
            return 8
    return max(1, min(8, os.cpu_count() or 1))


def run_check(index: int, command: list[str]) -> CheckResult:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    return CheckResult(
        index=index,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        elapsed_seconds=time.perf_counter() - started,
    )


def run_checks(workers: int) -> list[CheckResult]:
    results: list[CheckResult | None] = [None] * len(CHECKS)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(run_check, index, command): index
            for index, command in enumerate(CHECKS, start=1)
        }
        for future in as_completed(futures):
            result = future.result()
            results[result.index - 1] = result
    return [result for result in results if result is not None]


def print_failures(failures: list[CheckResult]) -> None:
    for result in failures:
        print(f"\nFAILED [{result.index}/{len(CHECKS)}] {display_command(result.command)}")
        print(f"exit={result.returncode} elapsed={result.elapsed_seconds:.2f}s")
        if result.stdout:
            print("\nstdout:")
            print(result.stdout.rstrip())
        if result.stderr:
            print("\nstderr:")
            print(result.stderr.rstrip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers(),
        help="number of checks to run concurrently (default: min(8, CPU count), or OPE_CHECK_WORKERS)",
    )
    parser.add_argument("--list", action="store_true", help="list checks without running them")
    args = parser.parse_args()

    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.list:
        for index, command in enumerate(CHECKS, start=1):
            print(f"{index:03d} {display_command(command)}")
        print(f"{len(CHECKS)} checks")
        return

    started = time.perf_counter()
    results = run_checks(args.workers)
    failures = [result for result in results if result.returncode != 0]
    elapsed = time.perf_counter() - started
    if failures:
        print_failures(failures)
        print(f"\n{len(failures)} of {len(CHECKS)} checks failed with {args.workers} workers in {elapsed:.2f}s")
        raise SystemExit(1)
    print(f"ran {len(CHECKS)} checks with {args.workers} workers in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
