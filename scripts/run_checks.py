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
from threading import Event, Lock, Thread
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
    py("scripts/generate_domain_configs.py", "--check"),
    py("scripts/check_domain_configs.py"),
    py("scripts/generate_source_bindings.py", "--check"),
    py("scripts/check_source_bindings.py"),
    py("scripts/generate_domain_source_field_policy.py", "--check"),
    py("scripts/check_domain_source_field_policy.py"),
    py("scripts/generate_credential_reference_policy.py", "--check"),
    py("scripts/check_credential_reference_policy.py"),
    py("scripts/generate_retention_redaction_policy.py", "--check"),
    py("scripts/check_retention_redaction_policy.py"),
    py("scripts/generate_private_auto_evidence_policy.py", "--check"),
    py("scripts/check_private_auto_evidence_policy.py"),
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
    py("scripts/generate_lifecycle_operation_store.py", "--check"),
    py("scripts/check_lifecycle_operation_store.py"),
    py("scripts/generate_internal_api.py", "--check"),
    py("scripts/check_internal_api.py"),
    py("scripts/generate_prediction_workspace_registry.py", "--check"),
    py("scripts/check_prediction_workspace_registry.py"),
    py("scripts/generate_background_worker_runtime.py", "--check"),
    py("scripts/check_background_worker_runtime.py"),
    py("scripts/generate_runtime_security.py", "--check"),
    py("scripts/check_runtime_security.py"),
    py("scripts/generate_prediction_agent_adoption.py", "--check"),
    py("scripts/check_prediction_agent_adoption.py"),
    py("scripts/generate_agent_implementation_kit.py", "--check"),
    py("scripts/check_agent_implementation_kit.py"),
    py("scripts/check_agent_smoke.py"),
    py("scripts/generate_agent_integration.py", "--check"),
    py("scripts/check_agent_integration.py"),
    py("scripts/generate_prediction_feature_setup.py", "--check"),
    py("scripts/check_prediction_feature_setup.py"),
    py("scripts/generate_agent_guidance.py", "--check"),
    py("scripts/check_agent_guidance.py"),
    py("scripts/check_embed_prediction_feature_example.py"),
    py("scripts/generate_mcp_adoption_path.py", "--check"),
    py("scripts/check_mcp_adoption_path.py"),
    py("scripts/generate_postgres_compatibility.py", "--check"),
    py("scripts/check_postgres_compatibility.py"),
    py("scripts/generate_database_source_adapter_runtime.py", "--check"),
    py("scripts/check_database_source_adapter_runtime.py"),
    py("scripts/generate_opp_provider_adapter.py", "--check"),
    py("scripts/check_opp_provider_adapter.py"),
    py("scripts/generate_persistent_sqlite_policy.py", "--check"),
    py("scripts/check_persistent_sqlite_policy.py"),
    py("scripts/generate_lifecycle_lease_policy.py", "--check"),
    py("scripts/check_lifecycle_lease_policy.py"),
    py("scripts/generate_runtime_transport_readiness.py", "--check"),
    py("scripts/check_runtime_transport_readiness.py"),
    py("scripts/generate_workspace_tenant_isolation.py", "--check"),
    py("scripts/check_workspace_tenant_isolation.py"),
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
    py("scripts/generate_simulated_agent_pilot.py", "--check"),
    py("scripts/check_simulated_agent_pilot.py"),
    py("scripts/generate_pilot_findings.py", "--check"),
    py("scripts/check_pilot_findings.py"),
    py("scripts/generate_generated_runtime_types_decision.py", "--check"),
    py("scripts/check_generated_runtime_types_decision.py"),
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
    py("scripts/generate_prediction_campaign_pre_calibration.py", "--check"),
    py("scripts/check_prediction_campaign_pre_calibration.py"),
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


@dataclass(frozen=True)
class ActiveCheck:
    index: int
    command: list[str]
    started_at: float


class ProgressReporter:
    def __init__(self, total: int, interval_seconds: float) -> None:
        self.total = total
        self.interval_seconds = interval_seconds
        self.active: dict[int, ActiveCheck] = {}
        self.completed = 0
        self.lock = Lock()
        self.stop_event = Event()
        self.thread = Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        self.stop_event.set()
        self.thread.join(timeout=1.0)

    def mark_started(self, index: int, command: list[str], started_at: float) -> None:
        with self.lock:
            self.active[index] = ActiveCheck(index=index, command=command, started_at=started_at)

    def mark_finished(self, index: int) -> None:
        with self.lock:
            self.active.pop(index, None)
            self.completed += 1

    def _run(self) -> None:
        while not self.stop_event.wait(self.interval_seconds):
            self.report()

    def report(self) -> None:
        now = time.perf_counter()
        with self.lock:
            active = list(self.active.values())
            completed = self.completed
        if not active:
            return
        active.sort(key=lambda item: now - item.started_at, reverse=True)
        slowest = "; ".join(
            f"[{item.index}/{self.total}] {now - item.started_at:.1f}s {display_command(item.command)}"
            for item in active[:5]
        )
        print(
            f"[checks] {completed}/{self.total} done; {len(active)} running; slowest: {slowest}",
            file=sys.stderr,
            flush=True,
        )


def display_command(command: list[str]) -> str:
    return shlex.join(command)


def filter_checks(
    checks: list[list[str]],
    *,
    matches: list[str] | None,
    excludes: list[str] | None,
) -> list[list[str]]:
    selected: list[list[str]] = []
    for command in checks:
        rendered = display_command(command)
        if matches and not any(pattern in rendered for pattern in matches):
            continue
        if excludes and any(pattern in rendered for pattern in excludes):
            continue
        selected.append(command)
    return selected


def default_workers() -> int:
    value = os.environ.get("OPE_CHECK_WORKERS")
    if value:
        try:
            return max(1, int(value))
        except ValueError:
            return 8
    return max(1, min(8, os.cpu_count() or 1))


def default_progress_interval() -> float:
    value = os.environ.get("OPE_CHECK_PROGRESS_INTERVAL")
    if value is None:
        return 30.0
    try:
        return max(0.0, float(value))
    except ValueError:
        return 30.0


def run_check(index: int, command: list[str], progress: ProgressReporter | None = None) -> CheckResult:
    started = time.perf_counter()
    if progress is not None:
        progress.mark_started(index, command, started)
    try:
        completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        return CheckResult(
            index=index,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.perf_counter() - started,
        )
    except Exception as exc:
        return CheckResult(
            index=index,
            command=command,
            returncode=1,
            stdout="",
            stderr=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=time.perf_counter() - started,
        )
    finally:
        if progress is not None:
            progress.mark_finished(index)


def run_checks(checks: list[list[str]], workers: int, progress_interval: float) -> list[CheckResult]:
    results: list[CheckResult | None] = [None] * len(checks)
    progress = ProgressReporter(len(checks), progress_interval) if progress_interval > 0 else None
    if progress is not None:
        progress.start()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        try:
            futures = {
                executor.submit(run_check, index, command, progress): index
                for index, command in enumerate(checks, start=1)
            }
            for future in as_completed(futures):
                result = future.result()
                results[result.index - 1] = result
        finally:
            if progress is not None:
                progress.stop()
    return [result for result in results if result is not None]


def print_failures(failures: list[CheckResult], total: int) -> None:
    for result in failures:
        print(f"\nFAILED [{result.index}/{total}] {display_command(result.command)}")
        print(f"exit={result.returncode} elapsed={result.elapsed_seconds:.2f}s")
        if result.stdout:
            print("\nstdout:")
            print(result.stdout.rstrip())
        if result.stderr:
            print("\nstderr:")
            print(result.stderr.rstrip())


def print_slowest(results: list[CheckResult], count: int) -> None:
    if count <= 0:
        return
    slowest = sorted(results, key=lambda item: item.elapsed_seconds, reverse=True)[:count]
    if not slowest:
        return
    print("\nslowest checks:")
    for result in slowest:
        print(f"{result.elapsed_seconds:8.2f}s [{result.index}] {display_command(result.command)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers(),
        help="number of checks to run concurrently (default: min(8, CPU count), or OPE_CHECK_WORKERS)",
    )
    parser.add_argument(
        "--progress-interval",
        type=float,
        default=default_progress_interval(),
        help="seconds between active-check progress reports to stderr; use 0 to disable",
    )
    parser.add_argument(
        "--match",
        action="append",
        help="run only checks whose rendered command contains this text; can be repeated",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="skip checks whose rendered command contains this text; can be repeated",
    )
    parser.add_argument(
        "--slowest",
        type=int,
        default=0,
        help="print the N slowest completed checks",
    )
    parser.add_argument("--list", action="store_true", help="list checks without running them")
    args = parser.parse_args()

    checks = filter_checks(CHECKS, matches=args.match, excludes=args.exclude)
    if not checks:
        raise SystemExit("no checks selected")
    if args.workers < 1:
        raise SystemExit("--workers must be at least 1")
    if args.progress_interval < 0:
        raise SystemExit("--progress-interval must be non-negative")
    if args.list:
        for index, command in enumerate(checks, start=1):
            print(f"{index:03d} {display_command(command)}")
        print(f"{len(checks)} checks")
        return

    started = time.perf_counter()
    results = run_checks(checks, args.workers, args.progress_interval)
    failures = [result for result in results if result.returncode != 0]
    elapsed = time.perf_counter() - started
    print_slowest(results, args.slowest)
    if failures:
        print_failures(failures, len(checks))
        print(f"\n{len(failures)} of {len(checks)} checks failed with {args.workers} workers in {elapsed:.2f}s")
        raise SystemExit(1)
    print(f"ran {len(checks)} checks with {args.workers} workers in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
