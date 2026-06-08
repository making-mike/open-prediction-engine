#!/usr/bin/env python3
"""Small local CLI for OPE repository workflows."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from generate_lifecycle_operation_store import SCENARIO_NAMES


ROOT = Path(__file__).resolve().parents[1]

DOMAIN_SOURCE_FIELD_POLICY_FIELDS = [
    "domain_identity",
    "question_templates",
    "horizons",
    "resolution_criteria",
    "baseline_method",
    "accepted_source_roles",
    "exclusion_rules",
    "sample_thresholds",
    "claim_boundaries",
    "execution_boundary",
    "source_binding_identity",
    "source_binding_mode",
    "credential_policy",
    "source_role_bindings",
    "pre_forecast_checks",
    "setup_operations",
    "configuration_input_boundary",
    "next_action",
    "summary",
    "question_parameters",
    "role_keys",
    "role_required_fields",
    "resolution_text_criteria",
    "exclusion_reason_codes",
    "domain_specific_horizon_labels",
    "baseline_threshold_values",
    "source_quality_threshold_values",
    "credential_value",
    "raw_sql_query",
    "raw_private_row",
    "post_outcome_forecast_evidence",
    "production_quality_claim",
    "hosted_runtime_flag",
]

DOMAIN_SOURCE_FIELD_POLICY_CASES = [
    "weather_transit_core_ready",
    "seaport_extension_ready",
    "missing_resolution_criteria",
    "credential_value_in_source_binding",
    "raw_sql_query_as_binding_field",
    "domain_quality_claim_enabled",
    "outcome_role_marked_forecast_time",
]

DOMAIN_SOURCE_FIELD_POLICY_VIEWS = [
    "full",
    "source",
    "domain-fields",
    "source-fields",
    "extensions",
    "blocked",
    "source-kinds",
    "cases",
    "readbacks",
    "boundary",
    "summary",
]

CREDENTIAL_REFERENCE_POLICY_MECHANISMS = [
    "caller_secret_store_alias",
    "host_runtime_secret_handle",
    "local_operator_session_ref",
    "public_no_credential",
]

CREDENTIAL_REFERENCE_POLICY_SCOPE_KEYS = [
    "tenant_id",
    "workspace_id",
    "source_binding_id",
    "source_role",
    "adapter_ref",
    "source_kind",
    "source_policy_id",
    "credential_purpose",
]

CREDENTIAL_REFERENCE_POLICY_STATES = [
    "proposed",
    "approved",
    "active",
    "rotation_due",
    "revoked",
    "redaction_required",
]

CREDENTIAL_REFERENCE_POLICY_CONSUMERS = [
    "private_api_adapter",
    "database_adapter",
    "source_binding_validation",
    "runtime_readback",
    "agent_envelope",
    "normal_checks",
]

CREDENTIAL_REFERENCE_POLICY_CASES = [
    "accepted_private_api_reference",
    "accepted_database_reference",
    "public_source_no_credential",
    "missing_reference_for_private_api",
    "raw_api_token_submitted",
    "database_password_in_connection_string",
    "cross_tenant_reference",
    "unscoped_reference",
    "adapter_mismatch",
    "revoked_reference",
    "normal_check_resolution_attempt",
]

CREDENTIAL_REFERENCE_POLICY_VIEWS = [
    "full",
    "source",
    "mechanisms",
    "scope",
    "lifecycle",
    "consumers",
    "cases",
    "readbacks",
    "boundary",
    "summary",
]

RETENTION_REDACTION_POLICY_CLASSES = [
    "forecast_lifecycle_record",
    "evidence_trace_record",
    "source_connector_result",
    "source_binding_config",
    "credential_reference_record",
    "pilot_session_summary",
    "local_usage_trace_event",
    "operation_receipt",
]

RETENTION_REDACTION_POLICY_ACTIONS = [
    "retain_append_only",
    "archive_tombstone",
    "redaction_receipt",
    "sanitized_projection_rebuild",
    "physical_delete_exception",
]

RETENTION_REDACTION_POLICY_GATES = [
    "authorized_erasure_basis",
    "tenant_workspace_scope_verified",
    "record_class_allows_physical_delete",
    "legal_or_safety_review_recorded",
    "audit_tombstone_retained",
    "redaction_receipt_retained",
    "immutable_forecast_history_preserved_or_rendered_unscorable",
    "operator_approval_recorded",
]

RETENTION_REDACTION_POLICY_CASES = [
    "normal_forecast_lifecycle_retention",
    "archive_inactive_prediction",
    "redact_private_source_detail",
    "redact_credential_like_field",
    "pilot_summary_needs_redaction",
    "usage_trace_aggregate_only",
    "source_connector_raw_preview_requested",
    "physical_delete_missing_legal_basis",
    "physical_delete_with_authorized_erasure",
    "physical_delete_for_forecast_history",
    "redaction_receipt_replay",
    "tombstone_rebuild_read_model",
]

RETENTION_REDACTION_POLICY_VIEWS = [
    "full",
    "source",
    "classes",
    "actions",
    "gates",
    "cases",
    "readbacks",
    "boundary",
    "summary",
]

PRIVATE_AUTO_EVIDENCE_POLICY_SOURCE_KINDS = [
    "local_file",
    "manual_mapping",
    "auto_evidence_connector",
    "source_adapter_output",
    "database_query_manifest",
    "private_api_manifest",
    "manual_upload",
    "web_search",
]

PRIVATE_AUTO_EVIDENCE_POLICY_GATES = [
    "domain_config_bound",
    "source_binding_bound",
    "source_policy_bound",
    "tenant_workspace_scope_bound",
    "caller_approval_recorded",
    "credential_reference_scoped",
    "adapter_capability_checked",
    "freshness_window_declared",
    "retention_policy_bound",
    "leakage_checks_declared",
    "forecast_before_close_preserved",
    "normal_checks_non_effectful",
]

PRIVATE_AUTO_EVIDENCE_POLICY_CASES = [
    "approved_local_file_auto",
    "approved_adapter_output_auto",
    "approved_database_query_manifest",
    "private_api_manifest_with_scoped_credential",
    "manual_mapping_with_confirmation",
    "manual_upload_without_adapter_contract",
    "private_api_missing_credential_ref",
    "database_raw_sql_auto",
    "web_search_private_setup",
    "cross_tenant_source_binding",
    "post_outcome_capture_as_forecast_evidence",
    "raw_private_payload_retention",
    "unregistered_private_connector",
]

PRIVATE_AUTO_EVIDENCE_POLICY_VIEWS = [
    "full",
    "source",
    "source-kinds",
    "gates",
    "cases",
    "readbacks",
    "boundary",
    "summary",
]


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
        raise SystemExit(exc.returncode) from None


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


def append_flag(command: list[str], args: argparse.Namespace, attr: str, flag: str | None = None) -> None:
    if getattr(args, attr):
        command.append(flag or f"--{attr.replace('_', '-')}")


def append_value(command: list[str], args: argparse.Namespace, attr: str, flag: str | None = None) -> None:
    value = getattr(args, attr)
    if value is not None:
        command.extend([flag or f"--{attr.replace('_', '-')}", str(value)])


def script_command(
    script: str,
    args: argparse.Namespace,
    *,
    flags: tuple[str, ...] = (),
    values: tuple[str, ...] = (),
) -> list[str]:
    command = [sys.executable, script]
    for attr in flags:
        append_flag(command, args, attr)
    for attr in values:
        append_value(command, args, attr)
    return command


def cmd_check(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/run_checks.py"])


def cmd_release_check(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/release_check.py"])


def smoke_step(key: str, label: str, command: list[str]) -> dict[str, object]:
    print(f"[smoke] start {label}", file=sys.stderr, flush=True)
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    elapsed = round(time.perf_counter() - started, 3)
    print(f"[smoke] done {label} exit={completed.returncode} elapsed={elapsed:.3f}s", file=sys.stderr, flush=True)
    row: dict[str, object] = {
        "stepKey": key,
        "label": label,
        "command": " ".join(command),
        "exitCode": completed.returncode,
        "elapsedSeconds": elapsed,
        "status": "passed" if completed.returncode == 0 else "failed",
    }
    if completed.returncode != 0:
        row["errorPreview"] = (completed.stderr or completed.stdout).strip()[:300]
    return row | {"stdout": completed.stdout}


def build_smoke_summary() -> dict[str, object]:
    commands = [
        ("schema_sanity", "schema sanity", [sys.executable, "scripts/check_json.py"]),
        ("setup_engine_check", "setup engine check", [sys.executable, "scripts/ope.py", "setup-engine", "--check"]),
        (
            "prediction_goal_catalog_check",
            "prediction goal catalog check",
            [sys.executable, "scripts/ope.py", "prediction-goal-catalog", "--check"],
        ),
        ("developer_adoption_check", "developer adoption check", [sys.executable, "scripts/ope.py", "developer-adoption", "--check"]),
        ("agent_implementation_kit_check", "agent implementation kit check", [sys.executable, "scripts/ope.py", "agent-implementation-kit", "--check"]),
        ("agent_integrate_candidates", "agent integration candidates", [sys.executable, "scripts/ope.py", "agent-integrate", "--view", "candidates"]),
        (
            "agent_integrate_guided_forecast",
            "agent integration guided forecast",
            [sys.executable, "scripts/ope.py", "agent-integrate", "--run-guided", "--case", "accepted_adapter_output"],
        ),
        (
            "forecast_card_read",
            "forecast card read",
            [
                sys.executable,
                "scripts/ope.py",
                "read",
                "--record-type",
                "forecast-card",
                "--id",
                "forecast-1102",
                "--question-id",
                "question-1102",
            ],
        ),
    ]
    started = time.perf_counter()
    steps: list[dict[str, object]] = []
    failed_step: str | None = None
    for key, label, command in commands:
        row = smoke_step(key, label, command)
        stdout = str(row.pop("stdout"))
        if key == "agent_integrate_guided_forecast" and row["exitCode"] == 0:
            payload = json.loads(stdout)
            row["forecastId"] = payload.get("forecastId")
            row["questionId"] = payload.get("questionId")
            row["guidedStatus"] = payload.get("guidedStatus")
        elif key == "forecast_card_read" and row["exitCode"] == 0:
            payload = json.loads(stdout)
            record = payload.get("record", {})
            row["forecastId"] = record.get("forecastId")
            row["questionId"] = record.get("questionId")
            row["recordStatus"] = record.get("status")
        steps.append(row)
        if row["exitCode"] != 0:
            failed_step = key
            break
    smoke_status = "passed" if failed_step is None else "failed"
    return {
        "smokeId": "agentsmoke-001",
        "smokeStatus": smoke_status,
        "stepCount": len(steps),
        "failedStep": failed_step,
        "elapsedSeconds": round(time.perf_counter() - started, 3),
        "steps": steps,
        "writesState": False,
        "fetchesLiveData": False,
        "qualityClaimUpgraded": False,
        "nextCommandOnSuccess": "python3 scripts/ope.py setup-engine --goal \"<host prediction goal>\"",
        "nextCommandOnFailure": "Rerun the failed command shown in steps before running the full check.",
    }


def cmd_smoke(args: argparse.Namespace) -> None:
    summary = build_smoke_summary()
    if args.check:
        if summary["smokeStatus"] != "passed":
            print(json.dumps(summary, indent=2), file=sys.stderr)
            raise SystemExit(1)
        print("checked fast agent smoke")
        return
    if args.output_format == "json":
        print(json.dumps(summary, indent=2))
        return
    print(f"smokeStatus={summary['smokeStatus']} stepCount={summary['stepCount']} elapsedSeconds={summary['elapsedSeconds']}")
    if summary["failedStep"]:
        print(f"failedStep={summary['failedStep']}")
        raise SystemExit(1)
    print(f"next={summary['nextCommandOnSuccess']}")


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
    domain_configs_command = [sys.executable, "scripts/generate_domain_configs.py"]
    source_bindings_command = [sys.executable, "scripts/generate_source_bindings.py"]
    domain_source_field_policy_command = [sys.executable, "scripts/generate_domain_source_field_policy.py"]
    credential_reference_policy_command = [sys.executable, "scripts/generate_credential_reference_policy.py"]
    retention_redaction_policy_command = [sys.executable, "scripts/generate_retention_redaction_policy.py"]
    private_auto_evidence_policy_command = [sys.executable, "scripts/generate_private_auto_evidence_policy.py"]
    transit_delay_forecast_command = [sys.executable, "scripts/run_transit_delay_forecast.py"]
    transit_delay_forward_command = [sys.executable, "scripts/run_transit_delay_forward.py"]
    transit_forward_resolver_command = [sys.executable, "scripts/resolve_due_transit_forward_runs.py"]
    resolution_jobs_command = [sys.executable, "scripts/generate_resolution_jobs.py"]
    resolution_scheduler_command = [sys.executable, "scripts/run_resolution_scheduler.py"]
    resolution_runtime_reliability_command = [sys.executable, "scripts/generate_resolution_runtime_reliability.py"]
    lifecycle_operation_store_command = [sys.executable, "scripts/generate_lifecycle_operation_store.py"]
    internal_api_command = [sys.executable, "scripts/generate_internal_api.py"]
    prediction_workspace_registry_command = [sys.executable, "scripts/generate_prediction_workspace_registry.py"]
    background_worker_command = [sys.executable, "scripts/generate_background_worker_runtime.py"]
    runtime_security_command = [sys.executable, "scripts/generate_runtime_security.py"]
    agent_implementation_kit_command = [sys.executable, "scripts/generate_agent_implementation_kit.py"]
    agent_integration_command = [sys.executable, "scripts/generate_agent_integration.py"]
    prediction_goal_catalog_command = [sys.executable, "scripts/generate_prediction_goal_catalog.py"]
    setup_engine_command = [sys.executable, "scripts/generate_setup_engine.py"]
    postgres_compatibility_command = [sys.executable, "scripts/generate_postgres_compatibility.py"]
    database_source_adapter_runtime_command = [sys.executable, "scripts/generate_database_source_adapter_runtime.py"]
    opp_provider_adapter_command = [sys.executable, "scripts/generate_opp_provider_adapter.py"]
    persistent_sqlite_policy_command = [sys.executable, "scripts/generate_persistent_sqlite_policy.py"]
    lifecycle_lease_policy_command = [sys.executable, "scripts/generate_lifecycle_lease_policy.py"]
    runtime_transport_readiness_command = [sys.executable, "scripts/generate_runtime_transport_readiness.py"]
    workspace_tenant_isolation_command = [sys.executable, "scripts/generate_workspace_tenant_isolation.py"]
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
    prediction_campaign_resolution_attempt_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_resolution_attempt.py",
    ]
    prediction_campaign_doctor_command = [sys.executable, "scripts/generate_prediction_campaign_doctor.py"]
    prediction_campaign_resume_command = [sys.executable, "scripts/generate_prediction_campaign_resume.py"]
    prediction_campaign_evidence_ledger_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_evidence_ledger.py",
    ]
    prediction_campaign_calibration_status_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_calibration_status.py",
    ]
    prediction_campaign_pre_calibration_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_pre_calibration.py",
    ]
    prediction_campaign_method_update_gate_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_method_update_gate.py",
    ]
    prediction_campaign_method_update_plan_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_method_update_plan.py",
    ]
    prediction_campaign_method_update_action_command = [
        sys.executable,
        "scripts/generate_prediction_campaign_method_update_action.py",
    ]
    prediction_campaign_explain_command = [sys.executable, "scripts/generate_prediction_campaign_explain.py"]
    helsinki_pilot_runbook_command = [sys.executable, "scripts/generate_helsinki_traffic_pilot_runbook.py"]
    helsinki_pilot_readiness_command = [sys.executable, "scripts/generate_helsinki_traffic_pilot_readiness.py"]
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
        domain_configs_command.append("--write")
        source_bindings_command.append("--write")
        domain_source_field_policy_command.append("--write")
        credential_reference_policy_command.append("--write")
        retention_redaction_policy_command.append("--write")
        private_auto_evidence_policy_command.append("--write")
        transit_delay_forecast_command.append("--write")
        transit_delay_forward_command.append("--write")
        transit_forward_resolver_command.append("--write")
        resolution_jobs_command.append("--write")
        resolution_scheduler_command.append("--write")
        resolution_runtime_reliability_command.append("--write")
        lifecycle_operation_store_command.append("--write")
        internal_api_command.append("--write")
        prediction_workspace_registry_command.append("--write")
        background_worker_command.append("--write")
        runtime_security_command.append("--write")
        agent_implementation_kit_command.append("--write")
        agent_integration_command.append("--write")
        prediction_goal_catalog_command.append("--write")
        setup_engine_command.append("--write")
        postgres_compatibility_command.append("--write")
        database_source_adapter_runtime_command.append("--write")
        opp_provider_adapter_command.append("--write")
        persistent_sqlite_policy_command.append("--write")
        lifecycle_lease_policy_command.append("--write")
        runtime_transport_readiness_command.append("--write")
        workspace_tenant_isolation_command.append("--write")
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
        prediction_campaign_resolution_attempt_command.append("--write")
        prediction_campaign_doctor_command.append("--write")
        prediction_campaign_resume_command.append("--write")
        prediction_campaign_evidence_ledger_command.append("--write")
        prediction_campaign_calibration_status_command.append("--write")
        prediction_campaign_pre_calibration_command.append("--write")
        prediction_campaign_method_update_gate_command.append("--write")
        prediction_campaign_method_update_plan_command.append("--write")
        prediction_campaign_method_update_action_command.append("--write")
        prediction_campaign_explain_command.append("--write")
        helsinki_pilot_runbook_command.append("--write")
        helsinki_pilot_readiness_command.append("--write")
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
        domain_configs_command.append("--check")
        source_bindings_command.append("--check")
        domain_source_field_policy_command.append("--check")
        credential_reference_policy_command.append("--check")
        retention_redaction_policy_command.append("--check")
        private_auto_evidence_policy_command.append("--check")
        transit_delay_forecast_command.append("--check")
        transit_delay_forward_command.append("--check")
        transit_forward_resolver_command.append("--check")
        resolution_jobs_command.append("--check")
        resolution_scheduler_command.append("--check")
        resolution_runtime_reliability_command.append("--check")
        lifecycle_operation_store_command.append("--check")
        internal_api_command.append("--check")
        prediction_workspace_registry_command.append("--check")
        background_worker_command.append("--check")
        runtime_security_command.append("--check")
        agent_implementation_kit_command.append("--check")
        agent_integration_command.append("--check")
        prediction_goal_catalog_command.append("--check")
        setup_engine_command.append("--check")
        postgres_compatibility_command.append("--check")
        database_source_adapter_runtime_command.append("--check")
        opp_provider_adapter_command.append("--check")
        persistent_sqlite_policy_command.append("--check")
        lifecycle_lease_policy_command.append("--check")
        runtime_transport_readiness_command.append("--check")
        workspace_tenant_isolation_command.append("--check")
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
        prediction_campaign_resolution_attempt_command.append("--check")
        prediction_campaign_doctor_command.append("--check")
        prediction_campaign_resume_command.append("--check")
        prediction_campaign_evidence_ledger_command.append("--check")
        prediction_campaign_calibration_status_command.append("--check")
        prediction_campaign_pre_calibration_command.append("--check")
        prediction_campaign_method_update_gate_command.append("--check")
        prediction_campaign_method_update_plan_command.append("--check")
        prediction_campaign_method_update_action_command.append("--check")
        prediction_campaign_explain_command.append("--check")
        helsinki_pilot_runbook_command.append("--check")
        helsinki_pilot_readiness_command.append("--check")
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
    commands = [
        reports_command,
        loop_command,
        live_outcome_command,
        auto_evidence_command,
        auto_evidence_gather_command,
        source_connectors_command,
        live_readiness_command,
        transit_api_connector_command,
        domain_setups_command,
        domain_configs_command,
        source_bindings_command,
        domain_source_field_policy_command,
        credential_reference_policy_command,
        retention_redaction_policy_command,
        private_auto_evidence_policy_command,
        transit_delay_forecast_command,
        transit_delay_forward_command,
        transit_forward_resolver_command,
        resolution_jobs_command,
        resolution_scheduler_command,
        resolution_runtime_reliability_command,
        lifecycle_operation_store_command,
        internal_api_command,
        prediction_workspace_registry_command,
        background_worker_command,
        runtime_security_command,
        agent_implementation_kit_command,
        agent_integration_command,
        prediction_goal_catalog_command,
        setup_engine_command,
        postgres_compatibility_command,
        database_source_adapter_runtime_command,
        opp_provider_adapter_command,
        persistent_sqlite_policy_command,
        lifecycle_lease_policy_command,
        runtime_transport_readiness_command,
        workspace_tenant_isolation_command,
        transit_forward_run_corpus_command,
        transit_corpus_growth_command,
        transit_track_record_gate_command,
        transit_method_options_command,
        transit_live_evidence_promotion_command,
        source_intake_command,
        source_builder_command,
        source_adapter_output_command,
        source_adapter_intake_command,
        source_quality_command,
        source_handoff_command,
        source_handoff_method_command,
        auto_evidence_forecast_command,
        auto_evidence_resolution_command,
        historical_forecast_command,
        method_comparison_command,
        method_selection_command,
        setup_benchmark_command,
        setup_method_command,
        setup_forecast_command,
        source_handoff_forecast_command,
        local_source_runtime_command,
        source_handoff_resolution_command,
        source_handoff_runbook_command,
        private_setup_workflow_command,
        private_source_adapters_command,
        private_source_adapter_outcomes_command,
        private_source_adapter_bridge_command,
        private_setup_requests_command,
        private_setup_actions_command,
        private_setup_action_runbook_command,
        private_setup_agent_bundles_command,
        private_setup_orchestrator_command,
        agent_pilot_validation_command,
        pilot_evidence_command,
        pilot_session_packet_command,
        pilot_summary_intake_command,
        local_usage_trace_command,
        developer_adoption_command,
        expansion_readiness_command,
        repeating_prediction_setup_command,
        prediction_campaign_manifest_command,
        prediction_campaign_runner_command,
        prediction_campaign_forecast_creation_command,
        prediction_campaign_forecast_artifact_command,
        prediction_campaign_forecast_write_command,
        prediction_campaign_resolution_attempt_command,
        prediction_campaign_doctor_command,
        prediction_campaign_resume_command,
        prediction_campaign_evidence_ledger_command,
        prediction_campaign_calibration_status_command,
        prediction_campaign_pre_calibration_command,
        prediction_campaign_method_update_gate_command,
        prediction_campaign_method_update_plan_command,
        prediction_campaign_method_update_action_command,
        prediction_campaign_explain_command,
        helsinki_pilot_runbook_command,
        helsinki_pilot_readiness_command,
        private_setup_adapter_runbook_command,
        private_setup_adapter_conformance_command,
        private_setup_adapter_conformance_summary_command,
        private_source_kind_selection_command,
        private_source_kind_query_matrix_command,
        recalculation_command,
        forecast_run_command,
        forecast_run_matrix_command,
        forecast_runbook_command,
        agent_envelopes_command,
        agent_protocol_map_command,
        pipeline_command,
        pipeline_resolution_command,
        index_command,
        manifest_command,
    ]
    if args.list:
        for index, command in enumerate(commands, start=1):
            print(f"{index:03d} {' '.join(command)}")
        print(f"{len(commands)} fixture commands")
        return
    for command in commands:
        run(command)


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


def cmd_domain_configs(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_domain_configs.py"]
    if args.domain:
        command.extend(["--domain", args.domain])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_source_bindings(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_source_bindings.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_domain_source_field_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_domain_source_field_policy.py"]
    if args.field:
        command.extend(["--field", args.field])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_credential_reference_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_credential_reference_policy.py"]
    if args.mechanism:
        command.extend(["--mechanism", args.mechanism])
    if args.scope_key:
        command.extend(["--scope-key", args.scope_key])
    if args.state:
        command.extend(["--state", args.state])
    if args.consumer:
        command.extend(["--consumer", args.consumer])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_retention_redaction_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_retention_redaction_policy.py"]
    if args.record_class:
        command.extend(["--record-class", args.record_class])
    if args.action:
        command.extend(["--action", args.action])
    if args.gate:
        command.extend(["--gate", args.gate])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_private_auto_evidence_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_private_auto_evidence_policy.py"]
    if args.source_kind:
        command.extend(["--source-kind", args.source_kind])
    if args.gate:
        command.extend(["--gate", args.gate])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
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
    if args.now:
        command.extend(["--now", args.now])
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


def cmd_lifecycle_operation_store(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_lifecycle_operation_store.py"]
    if args.scenario:
        command.extend(["--scenario", args.scenario])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_internal_api(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_internal_api.py"]
    if args.operation:
        command.extend(["--operation", args.operation])
    if args.call:
        command.append("--call")
    if args.caller_id:
        command.extend(["--caller-id", args.caller_id])
    if args.prediction_id:
        command.extend(["--prediction-id", args.prediction_id])
    if args.idempotency_key:
        command.extend(["--idempotency-key", args.idempotency_key])
    if args.max_bytes is not None:
        command.extend(["--max-bytes", str(args.max_bytes)])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_prediction_workspace_registry(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_prediction_workspace_registry.py"]
    if args.prediction_id:
        command.extend(["--prediction-id", args.prediction_id])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_background_worker(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_background_worker_runtime.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_runtime_security(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_runtime_security.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_explain_fit(args: argparse.Namespace) -> None:
    command = [
        sys.executable,
        "scripts/generate_prediction_agent_adoption.py",
        "--view",
        args.view,
        "--goal",
        args.goal,
        "--output-format",
        args.output_format,
    ]
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_capabilities(_args: argparse.Namespace) -> None:
    run([sys.executable, "scripts/generate_prediction_agent_adoption.py", "--view", "capabilities"])


def cmd_adoption_eval(args: argparse.Namespace) -> None:
    run(
        [
            sys.executable,
            "scripts/generate_prediction_agent_adoption.py",
            "--view",
            "adoption-eval",
            "--output-format",
            args.output_format,
        ]
    )


def cmd_agent_implementation_kit(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_implementation_kit.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_integrate(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_integration.py"]
    if args.scenario:
        command.extend(["--scenario", args.scenario])
    if args.view:
        command.extend(["--view", args.view])
    if args.case:
        command.extend(["--case", args.case])
    if args.run_guided:
        command.append("--run-guided")
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_setup_engine(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_setup_engine.py"]
    if args.goal:
        command.extend(["--goal", args.goal])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_prediction_goal_catalog(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_prediction_goal_catalog.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.goal:
        command.extend(["--goal", args.goal])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_prediction_feature_setup(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_prediction_feature_setup.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_agent_guidance(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_agent_guidance.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.case:
        command.extend(["--case", args.case])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_postgres_compatibility(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_postgres_compatibility.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_database_source_adapter_runtime(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_database_source_adapter_runtime.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_opp_provider_adapter(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_opp_provider_adapter.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_persistent_sqlite_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_persistent_sqlite_policy.py"]
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_lifecycle_lease_policy(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_lifecycle_lease_policy.py"]
    if args.operation:
        command.extend(["--operation", args.operation])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_runtime_transport_readiness(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_runtime_transport_readiness.py"]
    if args.surface:
        command.extend(["--surface", args.surface])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_workspace_tenant_isolation(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_workspace_tenant_isolation.py"]
    if args.tenant_id:
        command.extend(["--tenant-id", args.tenant_id])
    if args.case:
        command.extend(["--case", args.case])
    if args.view:
        command.extend(["--view", args.view])
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
    if args.campaign:
        command.extend(["--campaign", args.campaign])
    if args.from_local_ledger:
        command.append("--from-local-ledger")
    if args.ledger_case:
        command.extend(["--ledger-case", args.ledger_case])
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


def cmd_mcp_adoption(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_mcp_adoption_path.py"]
    if args.view:
        command.extend(["--view", args.view])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_findings(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_findings.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.from_local_ledger:
        command.append("--from-local-ledger")
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_supervision_status(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_supervision_status.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.from_local_ledger:
        command.append("--from-local-ledger")
    if args.local_ledger:
        command.extend(["--local-ledger", args.local_ledger])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_simulated_agent_pilot(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_simulated_agent_pilot.py"]
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_generated_types_decision(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_generated_runtime_types_decision.py"]
    if args.section:
        command.extend(["--section", args.section])
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
    if args.input_summary:
        command.extend(["--input-summary", args.input_summary])
    if args.write_local:
        command.append("--write-local")
    if args.from_local_ledger:
        command.append("--from-local-ledger")
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
    if args.input:
        command.extend(["--input", args.input])
    if args.case:
        command.extend(["--case", args.case])
    if args.section:
        command.extend(["--section", args.section])
    if args.check:
        command.append("--check")
    if args.write:
        command.append("--write")
    run(command)


def cmd_pilot_summary_template(args: argparse.Namespace) -> None:
    command = [sys.executable, "scripts/generate_pilot_summary_template.py"]
    if args.task:
        command.extend(["--task", args.task])
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
        runner_views = {
            "runner",
            "campaign-creation",
            "forecast-schedule",
            "decisions",
            "pre-calibration",
            "missed-run-policy",
            "summary",
            "boundary",
        }
        if args.view and args.view not in runner_views:
            raise SystemExit(f"--view {args.view} is only available for prediction-campaign resolve")
        command = script_command(
            "scripts/generate_prediction_campaign_runner.py",
            args,
            flags=(
                "check",
                "write",
                "live_weather",
                "execute_resolvers",
                "pre_calibrate",
                "full_materialization",
                "watch",
                "write_local",
            ),
            values=(
                "case",
                "plan_count",
                "domain",
                "service_window",
                "interval",
                "count",
                "until",
                "calibration_target",
                "post_calibration_action",
                "post_calibration_delay",
                "setup_json",
                "manifest_json",
                "history_source",
                "max_ticks",
                "poll_seconds",
                "now",
                "output_format",
                "view",
            ),
        )
        run(command)
        return
    if args.action == "pre-calibration":
        pre_calibration_views = {
            "pre-calibration",
            "source",
            "method",
            "binding",
            "checks",
            "write",
            "result",
            "summary",
            "boundary",
        }
        if args.view and args.view not in pre_calibration_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign pre-calibration")
        command = script_command(
            "scripts/generate_prediction_campaign_pre_calibration.py",
            args,
            flags=("check", "write", "write_local"),
            values=("history_source", "output_format", "view"),
        )
        run(command)
        return
    if args.action == "forecast-create":
        command = script_command(
            "scripts/generate_prediction_campaign_forecast_creation.py",
            args,
            flags=("check", "write"),
        )
        run(command)
        return
    if args.action == "forecast-artifact":
        command = script_command(
            "scripts/generate_prediction_campaign_forecast_artifact.py",
            args,
            flags=("check", "write"),
        )
        run(command)
        return
    if args.action == "forecast-write":
        command = script_command(
            "scripts/generate_prediction_campaign_forecast_write.py",
            args,
            flags=("check", "write", "write_local"),
            values=("run_id", "manifest_json", "output_format"),
        )
        run(command)
        return
    if args.action == "resolve":
        attempt_views = {"attempt", "target", "guards", "result", "summary", "boundary"}
        if args.view and args.view not in attempt_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign resolve")
        command = script_command(
            "scripts/generate_prediction_campaign_resolution_attempt.py",
            args,
            flags=("check", "write", "execute_resolvers", "write_local", "missing_outcome"),
            values=("run_id", "now", "outcome_csv", "output_format", "view"),
        )
        append_value(command, args, "attempt_case", "--case")
        run(command)
        return
    if args.action == "doctor":
        doctor_views = {"doctor", "health", "queues", "duplicates", "recovery", "summary", "boundary"}
        if args.view and args.view not in doctor_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign doctor")
        command = script_command(
            "scripts/generate_prediction_campaign_doctor.py",
            args,
            flags=("check", "write"),
            values=("now", "output_format", "view"),
        )
        run(command)
        return
    if args.action == "resume":
        resume_views = {"resume", "state", "checks", "actions", "summary", "boundary"}
        if args.view and args.view not in resume_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign resume")
        command = script_command(
            "scripts/generate_prediction_campaign_resume.py",
            args,
            flags=("check", "write", "from_local"),
            values=("resume_case", "output_format", "view"),
        )
        run(command)
        return
    if args.action in {"append-ready", "append"}:
        ledger_views = {"ledger", "policy", "candidate", "checks", "rows", "result", "summary", "boundary"}
        if args.view and args.view not in ledger_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign {args.action}")
        command = script_command(
            "scripts/generate_prediction_campaign_evidence_ledger.py",
            args,
            flags=("check", "write", "from_local", "write_local"),
            values=("run_id", "ledger_case", "output_format", "view"),
        )
        if not args.check and not args.write:
            command.extend(["--mode", args.action])
        run(command)
        return
    if args.action == "calibration-status":
        calibration_views = {"calibration", "thresholds", "readback", "pilot", "policy", "cycle", "summary", "boundary"}
        if args.view and args.view not in calibration_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign calibration-status")
        command = script_command(
            "scripts/generate_prediction_campaign_calibration_status.py",
            args,
            flags=("check", "write", "from_local_ledger"),
            values=("campaign", "calibration_case", "output_format", "view"),
        )
        run(command)
        return
    if args.action == "method-update-gate":
        method_update_views = {"gate", "evidence", "proposal", "approval", "decision", "summary", "boundary"}
        if args.view and args.view not in method_update_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign method-update-gate")
        command = script_command(
            "scripts/generate_prediction_campaign_method_update_gate.py",
            args,
            flags=("check", "write"),
            values=("method_update_case", "output_format", "view"),
        )
        run(command)
        return
    if args.action == "method-update-plan":
        method_update_plan_views = {"plan", "approval", "command", "rollback", "preflight", "decision", "summary", "boundary"}
        if args.view and args.view not in method_update_plan_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign method-update-plan")
        command = script_command(
            "scripts/generate_prediction_campaign_method_update_plan.py",
            args,
            flags=("check", "write"),
            values=("method_update_plan_case", "output_format", "view"),
        )
        run(command)
        return
    if args.action in {"apply-method-update", "rollback-method-update"}:
        method_update_action_views = {"plan", "approval", "command", "rollback", "preflight", "decision", "summary", "boundary"}
        if args.view and args.view not in method_update_action_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign {args.action}")
        operation = "rollback" if args.action == "rollback-method-update" else "apply"
        command = script_command(
            "scripts/generate_prediction_campaign_method_update_action.py",
            args,
            flags=("check", "write", "write_local"),
            values=("method_update_plan_id", "method_update_plan_case", "output_format", "view"),
        )
        command.extend(["--operation", operation])
        run(command)
        return
    if args.action == "explain":
        explain_views = {"explain", "snapshot", "task", "workflow", "errors", "agent", "claims", "summary", "boundary"}
        if args.view and args.view not in explain_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign explain")
        command = script_command(
            "scripts/generate_prediction_campaign_explain.py",
            args,
            flags=("check", "write"),
            values=("output_format", "view"),
        )
        run(command)
        return
    if args.action == "pilot-runbook":
        pilot_runbook_views = {
            "runbook",
            "scope",
            "operator-status",
            "smoke",
            "steps",
            "success",
            "abort",
            "summary",
            "boundary",
        }
        if args.view and args.view not in pilot_runbook_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign pilot-runbook")
        command = script_command(
            "scripts/generate_helsinki_traffic_pilot_runbook.py",
            args,
            flags=("check", "write"),
            values=("output_format", "view"),
        )
        run(command)
        return
    if args.action == "pilot-readiness":
        pilot_readiness_views = {
            "readiness",
            "checks",
            "manual",
            "commands",
            "blocked",
            "summary",
            "boundary",
        }
        if args.view and args.view not in pilot_readiness_views:
            raise SystemExit(f"--view {args.view} is not available for prediction-campaign pilot-readiness")
        command = script_command(
            "scripts/generate_helsinki_traffic_pilot_readiness.py",
            args,
            flags=("check", "write"),
            values=("output_format", "view"),
        )
        run(command)
        return

    command = [sys.executable, "scripts/generate_prediction_campaign_manifest.py"]
    if args.action != "manifest":
        command.extend(["--view", args.action])
    if args.case:
        command.extend(["--case", args.case])
    if args.plan_count is not None:
        command.extend(["--plan-count", str(args.plan_count)])
    if args.count is not None:
        command.extend(["--count", str(args.count)])
    if args.full_materialization:
        command.append("--full-materialization")
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
    if args.scenario:
        command.extend(["--scenario", args.scenario])
    if args.goal:
        command.extend(["--goal", args.goal])
    if args.setup_engine_view:
        command.extend(["--view", args.setup_engine_view])
    if args.guided_case:
        command.extend(["--case", args.guided_case])
    if args.internal_operation:
        command.extend(["--internal-operation", args.internal_operation])
    if args.prediction_id:
        command.extend(["--prediction-id", args.prediction_id])
    if args.idempotency_key:
        command.extend(["--idempotency-key", args.idempotency_key])
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

    smoke = subparsers.add_parser("smoke", help="run a fast external-agent adoption smoke check")
    smoke.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="print a compact text or JSON smoke summary",
    )
    smoke.add_argument("--check", action="store_true", help="check the fast agent smoke path")
    smoke.set_defaults(func=cmd_smoke)

    generate = subparsers.add_parser("generate-fixtures", help="check or refresh generated fixtures")
    generate.add_argument("--list", action="store_true", help="list fixture generator commands without running them")
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

    domain_configs = subparsers.add_parser(
        "domain-configs",
        help="check, refresh, or print reusable domain configuration records",
    )
    domain_configs.add_argument(
        "--domain",
        choices=["weather-transit-delays", "seaport-berth-availability"],
        help="print one domain config record",
    )
    domain_configs.add_argument("--check", action="store_true", help="check generated domain config drift")
    domain_configs.add_argument("--write", action="store_true", help="refresh generated domain config records")
    domain_configs.set_defaults(func=cmd_domain_configs)

    source_bindings = subparsers.add_parser(
        "source-bindings",
        help="check, refresh, or print domain source binding setup records",
    )
    source_bindings.add_argument(
        "--case",
        choices=["accepted", "blocked", "partial", "rejected"],
        help="print one source binding setup case",
    )
    source_bindings.add_argument("--check", action="store_true", help="check generated source binding drift")
    source_bindings.add_argument("--write", action="store_true", help="refresh generated source binding records")
    source_bindings.set_defaults(func=cmd_source_bindings)

    domain_source_field_policy = subparsers.add_parser(
        "domain-source-field-policy",
        help="print checked domain/source field requirement policy readback",
    )
    domain_source_field_policy.add_argument(
        "--field",
        choices=DOMAIN_SOURCE_FIELD_POLICY_FIELDS,
        help="print one field policy row",
    )
    domain_source_field_policy.add_argument(
        "--case",
        choices=DOMAIN_SOURCE_FIELD_POLICY_CASES,
        help="print one field decision case",
    )
    domain_source_field_policy.add_argument(
        "--view",
        choices=DOMAIN_SOURCE_FIELD_POLICY_VIEWS,
        default="full",
        help="print a focused domain/source field policy view",
    )
    domain_source_field_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated domain/source field policy drift",
    )
    domain_source_field_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated domain/source field policy fixture",
    )
    domain_source_field_policy.set_defaults(func=cmd_domain_source_field_policy)

    credential_reference_policy = subparsers.add_parser(
        "credential-reference-policy",
        help="print checked credential-reference mechanism policy readback",
    )
    credential_reference_policy.add_argument(
        "--mechanism",
        choices=CREDENTIAL_REFERENCE_POLICY_MECHANISMS,
        help="print one accepted credential-reference mechanism",
    )
    credential_reference_policy.add_argument(
        "--scope-key",
        choices=CREDENTIAL_REFERENCE_POLICY_SCOPE_KEYS,
        help="print one required credential-reference scope key",
    )
    credential_reference_policy.add_argument(
        "--state",
        choices=CREDENTIAL_REFERENCE_POLICY_STATES,
        help="print one credential-reference lifecycle state",
    )
    credential_reference_policy.add_argument(
        "--consumer",
        choices=CREDENTIAL_REFERENCE_POLICY_CONSUMERS,
        help="print one credential-reference consumer rule",
    )
    credential_reference_policy.add_argument(
        "--case",
        choices=CREDENTIAL_REFERENCE_POLICY_CASES,
        help="print one credential-reference policy case",
    )
    credential_reference_policy.add_argument(
        "--view",
        choices=CREDENTIAL_REFERENCE_POLICY_VIEWS,
        default="full",
        help="print a focused credential-reference policy view",
    )
    credential_reference_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated credential-reference policy drift",
    )
    credential_reference_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated credential-reference policy fixture",
    )
    credential_reference_policy.set_defaults(func=cmd_credential_reference_policy)

    retention_redaction_policy = subparsers.add_parser(
        "retention-redaction-policy",
        help="print checked retention, redaction, tombstone, and physical-delete policy readback",
    )
    retention_redaction_policy.add_argument(
        "--record-class",
        choices=RETENTION_REDACTION_POLICY_CLASSES,
        help="print one retention class policy",
    )
    retention_redaction_policy.add_argument(
        "--action",
        choices=RETENTION_REDACTION_POLICY_ACTIONS,
        help="print one retention/redaction policy action",
    )
    retention_redaction_policy.add_argument(
        "--gate",
        choices=RETENTION_REDACTION_POLICY_GATES,
        help="print one physical-delete exception gate",
    )
    retention_redaction_policy.add_argument(
        "--case",
        choices=RETENTION_REDACTION_POLICY_CASES,
        help="print one retention/redaction policy case",
    )
    retention_redaction_policy.add_argument(
        "--view",
        choices=RETENTION_REDACTION_POLICY_VIEWS,
        default="full",
        help="print a focused retention/redaction policy view",
    )
    retention_redaction_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated retention/redaction policy drift",
    )
    retention_redaction_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated retention/redaction policy fixture",
    )
    retention_redaction_policy.set_defaults(func=cmd_retention_redaction_policy)

    private_auto_evidence_policy = subparsers.add_parser(
        "private-auto-evidence-policy",
        help="print checked private data:auto source-policy readback",
    )
    private_auto_evidence_policy.add_argument(
        "--source-kind",
        choices=PRIVATE_AUTO_EVIDENCE_POLICY_SOURCE_KINDS,
        help="print one private data:auto source-kind policy",
    )
    private_auto_evidence_policy.add_argument(
        "--gate",
        choices=PRIVATE_AUTO_EVIDENCE_POLICY_GATES,
        help="print one private data:auto policy gate",
    )
    private_auto_evidence_policy.add_argument(
        "--case",
        choices=PRIVATE_AUTO_EVIDENCE_POLICY_CASES,
        help="print one private data:auto policy case",
    )
    private_auto_evidence_policy.add_argument(
        "--view",
        choices=PRIVATE_AUTO_EVIDENCE_POLICY_VIEWS,
        default="full",
        help="print a focused private data:auto policy view",
    )
    private_auto_evidence_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated private data:auto policy drift",
    )
    private_auto_evidence_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated private data:auto policy fixture",
    )
    private_auto_evidence_policy.set_defaults(func=cmd_private_auto_evidence_policy)

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
    resolution_scheduler.add_argument("--now", help="override current timestamp for deterministic scheduler ticks")
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

    lifecycle_operation_store = subparsers.add_parser(
        "lifecycle-operation-store",
        help="print checked lifecycle operation store and database backend guidance",
    )
    lifecycle_operation_store.add_argument(
        "--scenario",
        choices=SCENARIO_NAMES,
        help="print one checked SQLite runtime preflight/readback scenario",
    )
    lifecycle_operation_store.add_argument(
        "--check",
        action="store_true",
        help="check generated lifecycle operation store drift",
    )
    lifecycle_operation_store.add_argument(
        "--write",
        action="store_true",
        help="refresh generated lifecycle operation store fixture",
    )
    lifecycle_operation_store.set_defaults(func=cmd_lifecycle_operation_store)

    internal_api = subparsers.add_parser(
        "internal-api",
        help="print checked embedded internal API operation surface",
    )
    internal_api.add_argument(
        "--operation",
        choices=[
            "create_prediction",
            "update_prediction",
            "start_prediction",
            "pause_prediction",
            "resume_prediction",
            "run_tick",
            "resolve_due",
            "append_evidence",
            "read_status",
            "database_source_adapter_status",
            "read_forecast_card",
            "read_lifecycle_bundle",
            "archive_record",
            "redact_record",
        ],
        help="print one stable internal API operation",
    )
    internal_api.add_argument(
        "--call",
        action="store_true",
        help="call one internal API operation in non-mutating dry-run mode",
    )
    internal_api.add_argument("--caller-id", help="caller id for --call")
    internal_api.add_argument("--prediction-id", help="prediction id for --call")
    internal_api.add_argument("--idempotency-key", help="idempotency key for effectful --call operations")
    internal_api.add_argument("--max-bytes", type=int, help="maximum response bytes for --call")
    internal_api.add_argument(
        "--check",
        action="store_true",
        help="check generated internal API drift",
    )
    internal_api.add_argument(
        "--write",
        action="store_true",
        help="refresh generated internal API fixture",
    )
    internal_api.set_defaults(func=cmd_internal_api)

    prediction_workspace_registry = subparsers.add_parser(
        "prediction-workspace-registry",
        help="print checked multi-prediction workspace registry readback",
    )
    prediction_workspace_registry.add_argument(
        "--prediction-id",
        help="print one prediction registry entry",
    )
    prediction_workspace_registry.add_argument(
        "--check",
        action="store_true",
        help="check generated prediction workspace registry drift",
    )
    prediction_workspace_registry.add_argument(
        "--write",
        action="store_true",
        help="refresh generated prediction workspace registry fixture",
    )
    prediction_workspace_registry.set_defaults(func=cmd_prediction_workspace_registry)

    background_worker = subparsers.add_parser(
        "background-worker",
        help="print checked bounded background worker and sidecar runtime readback",
    )
    background_worker.add_argument(
        "--view",
        choices=["full", "health", "tick", "loop", "commit", "control", "sidecar", "blocked", "boundary"],
        default="full",
        help="print a compact worker readback view",
    )
    background_worker.add_argument(
        "--check",
        action="store_true",
        help="check generated background worker runtime drift",
    )
    background_worker.add_argument(
        "--write",
        action="store_true",
        help="refresh generated background worker runtime fixture",
    )
    background_worker.set_defaults(func=cmd_background_worker)

    runtime_security = subparsers.add_parser(
        "runtime-security",
        help="print checked lightweight runtime security and hardening readback",
    )
    runtime_security.add_argument(
        "--view",
        choices=["full", "budget", "modules", "surfaces", "threats", "blocked", "boundary"],
        default="full",
        help="print a focused runtime-security readback view",
    )
    runtime_security.add_argument(
        "--check",
        action="store_true",
        help="check generated runtime security hardening drift",
    )
    runtime_security.add_argument(
        "--write",
        action="store_true",
        help="refresh generated runtime security hardening fixture",
    )
    runtime_security.set_defaults(func=cmd_runtime_security)

    explain_fit = subparsers.add_parser(
        "explain-fit",
        help="explain whether OPE fits a host prediction goal",
    )
    explain_fit.add_argument(
        "--goal",
        default="add predictions to my app",
        help="host prediction goal to evaluate",
    )
    explain_fit.add_argument(
        "--view",
        choices=["summary", "fit", "extension-points", "byo-model", "adoption-eval", "boundary"],
        default="summary",
        help="focused adoption view for JSON output",
    )
    explain_fit.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="compact text by default, or JSON for machine-readable detail",
    )
    explain_fit.add_argument(
        "--check",
        action="store_true",
        help="check generated prediction-agent adoption drift",
    )
    explain_fit.add_argument(
        "--write",
        action="store_true",
        help="refresh generated prediction-agent adoption fixture and capability manifest",
    )
    explain_fit.set_defaults(func=cmd_explain_fit)

    capabilities = subparsers.add_parser(
        "capabilities",
        help="print the checked OPE capability manifest for agents",
    )
    capabilities.set_defaults(func=cmd_capabilities)

    adoption_eval = subparsers.add_parser(
        "adoption-eval",
        help="print the first-five-minutes adoption evaluation checklist",
    )
    adoption_eval.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="compact text by default, or JSON for machine-readable detail",
    )
    adoption_eval.set_defaults(func=cmd_adoption_eval)

    agent_implementation_kit = subparsers.add_parser(
        "agent-implementation-kit",
        help="print checked agent prediction implementation kit and question-discovery readback",
    )
    agent_implementation_kit.add_argument(
        "--view",
        choices=["full", "quickstart", "manual", "intake", "candidates", "validation", "adapters", "templates", "blocked", "boundary"],
        default="full",
        help="print a focused agent implementation kit view",
    )
    agent_implementation_kit.add_argument(
        "--check",
        action="store_true",
        help="check generated agent implementation kit drift",
    )
    agent_implementation_kit.add_argument(
        "--write",
        action="store_true",
        help="refresh generated agent implementation kit fixture",
    )
    agent_implementation_kit.set_defaults(func=cmd_agent_implementation_kit)

    agent_integrate = subparsers.add_parser(
        "agent-integrate",
        help="print checked agent incorporation readiness, candidate discovery, and guided forecast readbacks",
    )
    agent_integrate.add_argument(
        "--scenario",
        choices=["helsinki_bus_disruption"],
        default="helsinki_bus_disruption",
        help="starter incorporation scenario",
    )
    agent_integrate.add_argument(
        "--view",
        choices=["full", "summary", "intake", "candidates", "validation", "commands", "blocked", "boundary", "efficiency"],
        default="full",
        help="print a focused agent integration readback view",
    )
    agent_integrate.add_argument(
        "--case",
        choices=[
            "accepted_adapter_output",
            "missing_weather_source",
            "missing_baseline_source",
            "missing_outcome_source",
            "ambiguous_service_window",
            "vague_geography",
            "missing_resolution_source",
            "unapproved_source",
            "raw_credential_value",
            "raw_sql_query",
            "unsafe_adapter_output",
            "private_row_exposure",
            "post_outcome_evidence",
        ],
        help="print one guided forecast case",
    )
    agent_integrate.add_argument(
        "--run-guided",
        action="store_true",
        help="return the guided first-forecast readback for the selected case",
    )
    agent_integrate.add_argument(
        "--check",
        action="store_true",
        help="check generated agent integration drift",
    )
    agent_integrate.add_argument(
        "--write",
        action="store_true",
        help="refresh generated agent integration fixture",
    )
    agent_integrate.set_defaults(func=cmd_agent_integrate)

    prediction_goal_catalog = subparsers.add_parser(
        "prediction-goal-catalog",
        help="print checked generic prediction-goal catalog examples",
    )
    prediction_goal_catalog.add_argument(
        "--view",
        choices=["full", "summary", "goals", "classifications", "boundary"],
        default="full",
        help="print a focused prediction-goal catalog view",
    )
    prediction_goal_catalog.add_argument(
        "--goal",
        choices=[
            "delivery_delay_risk",
            "stockout_risk",
            "sla_breach_risk",
            "demand_risk",
            "churn_risk",
            "seaport_berth_availability",
            "weather_sensitive_operations",
            "public_transit_disruption_risk",
        ],
        help="print one catalog goal example",
    )
    prediction_goal_catalog.add_argument("--check", action="store_true", help="check generated prediction-goal catalog drift")
    prediction_goal_catalog.add_argument("--write", action="store_true", help="refresh generated prediction-goal catalog fixture")
    prediction_goal_catalog.set_defaults(func=cmd_prediction_goal_catalog)

    setup_engine = subparsers.add_parser(
        "setup-engine",
        help="turn a host prediction goal into a checked OPE engine setup readback",
    )
    setup_engine.add_argument(
        "--goal",
        default="add predictions to my app",
        help="host prediction goal to turn into candidate contracts and source roles",
    )
    setup_engine.add_argument(
        "--view",
        choices=[
            "full",
            "summary",
            "contracts",
            "sources",
            "baseline",
            "host-wrapper",
            "claim-boundary",
            "examples",
        ],
        default="full",
        help="print a focused setup-engine view",
    )
    setup_engine.add_argument("--check", action="store_true", help="check generated setup-engine drift")
    setup_engine.add_argument("--write", action="store_true", help="refresh generated setup-engine fixture")
    setup_engine.set_defaults(func=cmd_setup_engine)

    prediction_feature_setup = subparsers.add_parser(
        "prediction-feature-setup",
        help="print compact prediction feature setup request/response contract readbacks",
    )
    prediction_feature_setup.add_argument(
        "--view",
        choices=["full", "request", "responses", "response", "interfaces", "boundary", "summary"],
        default="full",
        help="print a focused prediction feature setup view",
    )
    prediction_feature_setup.add_argument(
        "--case",
        choices=["accepted", "needs_clarification", "blocked", "rejected", "response_too_large"],
        default="accepted",
        help="response example case for --view response",
    )
    prediction_feature_setup.add_argument("--check", action="store_true", help="check generated prediction feature setup drift")
    prediction_feature_setup.add_argument("--write", action="store_true", help="refresh generated prediction feature setup fixture")
    prediction_feature_setup.set_defaults(func=cmd_prediction_feature_setup)

    agent_guide = subparsers.add_parser(
        "agent-guide",
        help="print checked guidance for agents turning messy prompts into safe OPE next moves",
    )
    agent_guide.add_argument(
        "--section",
        choices=["summary", "cases", "planner", "generic", "helsinki", "instructions", "boundary"],
        help="print one agent guidance section",
    )
    agent_guide.add_argument(
        "--case",
        choices=["accepted", "needs_clarification", "blocked", "rejected", "response_too_large"],
        help="print one guidance case",
    )
    agent_guide.add_argument("--check", action="store_true", help="check generated agent guidance drift")
    agent_guide.add_argument("--write", action="store_true", help="refresh generated agent guidance fixture")
    agent_guide.set_defaults(func=cmd_agent_guidance)

    postgres_compatibility = subparsers.add_parser(
        "postgres-compatibility",
        help="print checked SQLite-to-Postgres lifecycle storage compatibility readback",
    )
    postgres_compatibility.add_argument(
        "--view",
        choices=["full", "tables", "contract", "scenarios", "guards", "migration", "boundary"],
        default="full",
        help="print a focused Postgres compatibility view",
    )
    postgres_compatibility.add_argument(
        "--check",
        action="store_true",
        help="check generated Postgres compatibility drift",
    )
    postgres_compatibility.add_argument(
        "--write",
        action="store_true",
        help="refresh generated Postgres compatibility fixture",
    )
    postgres_compatibility.set_defaults(func=cmd_postgres_compatibility)

    database_source_adapter_runtime = subparsers.add_parser(
        "database-source-adapter-runtime",
        help="print checked approved database source-adapter runtime readback",
    )
    database_source_adapter_runtime.add_argument(
        "--case",
        choices=[
            "approved_fixture",
            "missing_approval",
            "missing_credential_reference",
            "unsafe_query_boundary",
            "oversized_result",
            "stale_source",
            "leakage_risk",
            "missing_outcome_source",
            "insufficient_comparable_history",
        ],
        help="print one checked database adapter runtime case",
    )
    database_source_adapter_runtime.add_argument(
        "--view",
        choices=["full", "cases", "approved", "blocked", "routing", "readbacks", "boundary", "summary"],
        default="full",
        help="print a focused database source-adapter runtime view",
    )
    database_source_adapter_runtime.add_argument(
        "--check",
        action="store_true",
        help="check generated database source-adapter runtime drift",
    )
    database_source_adapter_runtime.add_argument(
        "--write",
        action="store_true",
        help="refresh generated database source-adapter runtime fixture",
    )
    database_source_adapter_runtime.set_defaults(func=cmd_database_source_adapter_runtime)

    opp_provider_adapter = subparsers.add_parser(
        "opp-provider-adapter",
        help="print checked optional Open Prediction Protocol provider-adapter readback",
    )
    opp_provider_adapter.add_argument(
        "--case",
        choices=[
            "accepted_forecast_card",
            "unsupported_market",
            "malformed_outcome_spec",
            "missing_source_policy",
            "provider_timeout",
            "response_too_large",
        ],
        help="print one checked OPP provider-adapter conformance case",
    )
    opp_provider_adapter.add_argument(
        "--view",
        choices=[
            "full",
            "request",
            "response",
            "agent-card",
            "cases",
            "accepted",
            "blocked",
            "conformance",
            "boundary",
            "readbacks",
            "summary",
        ],
        default="full",
        help="print a focused OPP provider-adapter view",
    )
    opp_provider_adapter.add_argument(
        "--check",
        action="store_true",
        help="check generated OPP provider-adapter drift",
    )
    opp_provider_adapter.add_argument(
        "--write",
        action="store_true",
        help="refresh generated OPP provider-adapter fixture",
    )
    opp_provider_adapter.set_defaults(func=cmd_opp_provider_adapter)

    persistent_sqlite_policy = subparsers.add_parser(
        "persistent-sqlite-policy",
        help="print checked persistent SQLite path policy and readiness boundary",
    )
    persistent_sqlite_policy.add_argument(
        "--case",
        choices=[
            "ephemeral_default",
            "approved_workspace_path",
            "missing_approval",
            "outside_workspace",
            "symlink_escape",
            "existing_unmigrated_json_state",
            "schema_version_mismatch",
            "backup_missing",
            "lock_conflict",
            "readonly_filesystem",
        ],
        help="print one checked persistent SQLite path policy case",
    )
    persistent_sqlite_policy.add_argument(
        "--view",
        choices=[
            "full",
            "path",
            "cases",
            "ready",
            "blocked",
            "migration",
            "backup-lock",
            "guards",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="print a focused persistent SQLite policy view",
    )
    persistent_sqlite_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated persistent SQLite policy drift",
    )
    persistent_sqlite_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated persistent SQLite policy fixture",
    )
    persistent_sqlite_policy.set_defaults(func=cmd_persistent_sqlite_policy)

    lifecycle_lease_policy = subparsers.add_parser(
        "lifecycle-lease-policy",
        help="print checked lifecycle operation lease and idempotency policy readback",
    )
    lifecycle_lease_policy.add_argument(
        "--operation",
        choices=[
            "campaign.create_run",
            "forecast.create",
            "forecast.recalculate",
            "question.cancel",
            "question.annul",
            "resolution.record",
            "score.create",
            "evidence.append",
            "pre_calibration.bind",
            "method.apply",
            "method.rollback",
            "state.import_json",
            "record.archive",
            "record.redact",
        ],
        help="print one lifecycle operation lease policy",
    )
    lifecycle_lease_policy.add_argument(
        "--view",
        choices=[
            "full",
            "source",
            "operations",
            "strict",
            "idempotency",
            "cases",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="print a focused lifecycle lease policy view",
    )
    lifecycle_lease_policy.add_argument(
        "--check",
        action="store_true",
        help="check generated lifecycle lease policy drift",
    )
    lifecycle_lease_policy.add_argument(
        "--write",
        action="store_true",
        help="refresh generated lifecycle lease policy fixture",
    )
    lifecycle_lease_policy.set_defaults(func=cmd_lifecycle_lease_policy)

    runtime_transport_readiness = subparsers.add_parser(
        "runtime-transport-readiness",
        help="print checked runtime transport readiness and hosted/HTTP boundary readback",
    )
    runtime_transport_readiness.add_argument(
        "--surface",
        choices=[
            "embedded_internal_api",
            "cli",
            "agent_call",
            "local_mcp_stdio",
            "local_http_adapter",
            "queue_adapter",
            "hosted_service_runtime",
            "opp_http_provider",
        ],
        help="print one runtime transport surface",
    )
    runtime_transport_readiness.add_argument(
        "--case",
        choices=[
            "normal_check_http_server",
            "implicit_hosted_service",
            "opp_http_endpoint_request",
            "queue_worker_without_readiness",
            "production_secret_value_in_record",
            "default_live_fetch",
            "unbounded_background_daemon",
        ],
        help="print one blocked runtime transport case",
    )
    runtime_transport_readiness.add_argument(
        "--view",
        choices=[
            "full",
            "current",
            "future",
            "decisions",
            "criteria",
            "blocked",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="print a focused runtime transport readiness view",
    )
    runtime_transport_readiness.add_argument(
        "--check",
        action="store_true",
        help="check generated runtime transport readiness drift",
    )
    runtime_transport_readiness.add_argument(
        "--write",
        action="store_true",
        help="refresh generated runtime transport readiness fixture",
    )
    runtime_transport_readiness.set_defaults(func=cmd_runtime_transport_readiness)

    workspace_tenant_isolation = subparsers.add_parser(
        "workspace-tenant-isolation",
        help="print checked tenant-scoped workspace isolation policy readback",
    )
    workspace_tenant_isolation.add_argument(
        "--tenant-id",
        choices=["tenant-001", "tenant-002"],
        help="print one tenant workspace binding",
    )
    workspace_tenant_isolation.add_argument(
        "--case",
        choices=[
            "same_tenant_workspace_read",
            "cross_tenant_prediction_read",
            "cross_workspace_source_binding_reuse",
            "cross_tenant_queue_peek",
            "idempotency_namespace_collision",
            "credential_reference_other_tenant",
            "admin_override_without_audit",
        ],
        help="print one checked tenant access case",
    )
    workspace_tenant_isolation.add_argument(
        "--view",
        choices=[
            "full",
            "source",
            "tenants",
            "model",
            "scope",
            "resources",
            "queues",
            "sources",
            "cases",
            "readbacks",
            "boundary",
            "summary",
        ],
        default="full",
        help="print a focused workspace tenant isolation view",
    )
    workspace_tenant_isolation.add_argument(
        "--check",
        action="store_true",
        help="check generated workspace tenant isolation drift",
    )
    workspace_tenant_isolation.add_argument(
        "--write",
        action="store_true",
        help="refresh generated workspace tenant isolation fixture",
    )
    workspace_tenant_isolation.set_defaults(func=cmd_workspace_tenant_isolation)

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
    transit_track_record_gate.add_argument("--campaign", help="explicit campaign ledger id to include")
    transit_track_record_gate.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="explicitly read the ignored local campaign evidence ledger",
    )
    transit_track_record_gate.add_argument(
        "--ledger-case",
        choices=["excluded_missing_outcome", "comparable_scored"],
        help="checked campaign evidence-ledger case to include",
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

    mcp_adoption = subparsers.add_parser(
        "mcp-adoption",
        help="check, refresh, or print the local MCP adoption path transcripts",
    )
    mcp_adoption.add_argument("--check", action="store_true", help="check generated MCP adoption path drift")
    mcp_adoption.add_argument("--write", action="store_true", help="refresh generated MCP adoption path")
    mcp_adoption.add_argument(
        "--view",
        choices=["full", "success", "blocked", "boundary", "summary"],
        default="full",
        help="print one MCP adoption path view",
    )
    mcp_adoption.set_defaults(func=cmd_mcp_adoption)

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
        "--input-summary",
        help="classify one sanitized pilot summary and print a local ledger append plan",
    )
    pilot_evidence.add_argument(
        "--write-local",
        action="store_true",
        help="append an accepted sanitized summary to the ignored local pilot evidence ledger",
    )
    pilot_evidence.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="read ignored local pilot evidence instead of the checked synthetic ledger",
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
            "engine_setup_shortcut_comprehension",
            "repeating_prediction_campaign",
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
        "--input",
        help="classify one caller-supplied sanitized pilot summary JSON file without writing ledger rows",
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

    pilot_summary_template = subparsers.add_parser(
        "pilot-summary-template",
        help="check, refresh, or print the sanitized pilot summary template",
    )
    pilot_summary_template.add_argument(
        "--task",
        choices=[
            "local_file_setup_readback",
            "accepted_adapter_output_ready",
            "unsafe_source_block",
            "forecast_run_readback",
            "claim_gate_readback",
            "engine_setup_shortcut_comprehension",
            "repeating_prediction_campaign",
        ],
        help="pilot task scenario to draft a sanitized summary for",
    )
    pilot_summary_template.add_argument(
        "--section",
        choices=["summary", "draft", "guidance", "checklist", "commands", "boundary", "warnings"],
        help="print one pilot summary template section",
    )
    pilot_summary_template.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot summary template drift",
    )
    pilot_summary_template.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot summary template",
    )
    pilot_summary_template.set_defaults(func=cmd_pilot_summary_template)

    pilot_findings = subparsers.add_parser(
        "pilot-findings",
        help="check, refresh, or print sanitized real-session pilot findings",
    )
    pilot_findings.add_argument(
        "--section",
        choices=["summary", "friction", "next-actions", "boundary"],
        help="print one pilot findings section",
    )
    pilot_findings.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="include ignored local pilot evidence rows from .ope/live",
    )
    pilot_findings.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot findings drift",
    )
    pilot_findings.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot findings",
    )
    pilot_findings.set_defaults(func=cmd_pilot_findings)

    pilot_supervision_status = subparsers.add_parser(
        "pilot-supervision-status",
        help="check, refresh, or print the supervised pilot operator status readback",
    )
    pilot_supervision_status.add_argument(
        "--section",
        choices=["summary", "progress", "commands", "checks", "boundary", "warnings"],
        help="print one pilot supervision status section",
    )
    pilot_supervision_status.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="include ignored local pilot evidence rows from .ope/live",
    )
    pilot_supervision_status.add_argument(
        "--local-ledger",
        help="override ignored local pilot evidence ledger path for tests or local runs",
    )
    pilot_supervision_status.add_argument(
        "--check",
        action="store_true",
        help="check generated pilot supervision status drift",
    )
    pilot_supervision_status.add_argument(
        "--write",
        action="store_true",
        help="refresh generated pilot supervision status",
    )
    pilot_supervision_status.set_defaults(func=cmd_pilot_supervision_status)

    simulated_agent_pilot = subparsers.add_parser(
        "simulated-agent-pilot",
        help="check, refresh, or print user-authorized simulated agent pilot sessions",
    )
    simulated_agent_pilot.add_argument(
        "--section",
        choices=["summary", "sessions", "friction", "boundary", "user-prompt"],
        help="print one simulated agent pilot section",
    )
    simulated_agent_pilot.add_argument(
        "--check",
        action="store_true",
        help="check generated simulated agent pilot drift",
    )
    simulated_agent_pilot.add_argument(
        "--write",
        action="store_true",
        help="refresh generated simulated agent pilot",
    )
    simulated_agent_pilot.set_defaults(func=cmd_simulated_agent_pilot)

    generated_types_decision = subparsers.add_parser(
        "generated-types-decision",
        help="check, refresh, or print the generated runtime types decision",
    )
    generated_types_decision.add_argument(
        "--section",
        choices=["summary", "evidence", "json-fallback", "blocked", "gates", "boundary"],
        help="print one generated runtime types decision section",
    )
    generated_types_decision.add_argument(
        "--check",
        action="store_true",
        help="check generated runtime types decision drift",
    )
    generated_types_decision.add_argument(
        "--write",
        action="store_true",
        help="refresh generated runtime types decision",
    )
    generated_types_decision.set_defaults(func=cmd_generated_types_decision)

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
            "campaign_start",
            "campaign_forecast_created",
            "campaign_resolve_due",
            "campaign_resolver_executed",
            "campaign_append_ready",
            "campaign_appended",
            "campaign_calibration_threshold_met",
            "campaign_paused",
            "campaign_resumed",
            "campaign_stopped",
            "agent_integration_readiness",
            "agent_integration_candidates",
            "agent_integration_guided_forecast",
            "agent_integration_missing_weather_block",
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
            "resolve",
            "doctor",
            "resume",
            "append-ready",
            "append",
            "calibration-status",
            "pre-calibration",
            "method-update-gate",
            "method-update-plan",
            "apply-method-update",
            "rollback-method-update",
            "explain",
            "pilot-runbook",
            "pilot-readiness",
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
    prediction_campaign.add_argument(
        "--full-materialization",
        action="store_true",
        help="expand the complete local pilot plan for prediction-campaign plan",
    )
    prediction_campaign.add_argument("--until", help="dry-run runner until-date boundary")
    prediction_campaign.add_argument("--calibration-target", type=int, help="dry-run runner calibration target")
    prediction_campaign.add_argument("--post-calibration-action", help="dry-run runner post-calibration action")
    prediction_campaign.add_argument("--post-calibration-delay", help="dry-run runner post-calibration delay")
    prediction_campaign.add_argument("--setup-json", help="dry-run runner setup JSON input path")
    prediction_campaign.add_argument("--manifest-json", help="dry-run runner manifest JSON input path")
    prediction_campaign.add_argument("--history-source", help="approved historical delay CSV/JSON source for pre-calibration")
    prediction_campaign.add_argument("--campaign", help="explicit campaign id for local campaign readbacks")
    prediction_campaign.add_argument("--run-id", help="dry-run forecast creation run ID")
    prediction_campaign.add_argument(
        "--write-local",
        action="store_true",
        help="explicit local campaign write flag; checked readbacks remain non-mutating",
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
        "--pre-calibrate",
        action="store_true",
        help="optional historical-only pre-calibration before an explicit local launch write",
    )
    prediction_campaign.add_argument("--outcome-csv", help="approved local transit outcome CSV/JSON for campaign resolution")
    prediction_campaign.add_argument(
        "--missing-outcome",
        action="store_true",
        help="write an explicit missing-outcome campaign resolution exclusion",
    )
    prediction_campaign.add_argument(
        "--watch",
        action="store_true",
        help="run bounded foreground forecast scheduling ticks",
    )
    prediction_campaign.add_argument(
        "--max-ticks",
        type=int,
        help="number of bounded foreground forecast scheduling ticks",
    )
    prediction_campaign.add_argument(
        "--poll-seconds",
        type=int,
        help="seconds between bounded foreground forecast scheduling ticks",
    )
    prediction_campaign.add_argument(
        "--now",
        help="UTC runner clock for bounded forecast scheduling decisions",
    )
    prediction_campaign.add_argument(
        "--attempt-case",
        choices=["due_open", "already_resolved", "ambiguous", "annulled", "missed", "blocked_duplicate"],
        help="checked prediction-campaign resolve case",
    )
    prediction_campaign.add_argument(
        "--resume-case",
        choices=["checked_fixture_bundle", "interrupted_after_forecast_write"],
        help="checked prediction-campaign resume case",
    )
    prediction_campaign.add_argument(
        "--ledger-case",
        choices=["excluded_missing_outcome", "comparable_scored"],
        help="checked prediction-campaign evidence-ledger case",
    )
    prediction_campaign.add_argument(
        "--calibration-case",
        choices=["below_threshold", "threshold_met", "too_many_exclusions", "post_calibration_restart"],
        help="checked prediction-campaign calibration-status case",
    )
    prediction_campaign.add_argument(
        "--method-update-case",
        choices=[
            "below_threshold",
            "threshold_met_needs_approval",
            "approved_plan_ready",
            "regression_risk",
        ],
        help="checked prediction-campaign method-update gate case",
    )
    prediction_campaign.add_argument(
        "--method-update-plan-case",
        choices=["gate_blocked", "regression_risk", "approval_missing", "rollback_missing", "plan_ready"],
        help="checked prediction-campaign method-update plan case",
    )
    prediction_campaign.add_argument(
        "--method-update-plan-id",
        help="checked method-update plan id for apply or rollback commands",
    )
    prediction_campaign.add_argument(
        "--from-local",
        action="store_true",
        help="explicitly inspect ignored local campaign state for resume or evidence-ledger append",
    )
    prediction_campaign.add_argument(
        "--from-local-ledger",
        action="store_true",
        help="explicitly inspect the ignored local campaign evidence ledger",
    )
    prediction_campaign.add_argument(
        "--output-format",
        choices=["json", "jsonl", "human"],
        help="dry-run runner output format",
    )
    prediction_campaign.add_argument(
        "--view",
        choices=[
            "runner",
            "campaign-creation",
            "forecast-schedule",
            "decisions",
            "pre-calibration",
            "missed-run-policy",
            "source",
            "method",
            "binding",
            "attempt",
            "target",
            "guards",
            "result",
            "doctor",
            "health",
            "queues",
            "duplicates",
            "recovery",
            "resume",
            "state",
            "checks",
            "actions",
            "ledger",
            "policy",
            "candidate",
            "rows",
            "write",
            "result",
            "gate",
            "evidence",
            "proposal",
            "approval",
            "decision",
            "plan",
            "command",
            "rollback",
            "preflight",
            "calibration",
            "thresholds",
            "readback",
            "pilot",
            "cycle",
            "explain",
            "snapshot",
            "task",
            "workflow",
            "errors",
            "agent",
            "claims",
            "runbook",
            "scope",
            "operator-status",
            "smoke",
            "steps",
            "success",
            "abort",
            "readiness",
            "manual",
            "commands",
            "blocked",
            "summary",
            "boundary",
        ],
        help="print one start readback view",
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
            "agent_integration_readiness",
            "agent_integration_candidates",
            "agent_integration_guided_forecast",
            "setup_engine",
            "prediction_feature_setup",
            "campaign_plan",
            "campaign_status",
            "campaign_health",
            "campaign_append_readiness",
            "campaign_calibration_status",
            "internal_api",
            "database_source_adapter_runtime_status",
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
    agent_call.add_argument(
        "--scenario",
        choices=["helsinki_bus_disruption"],
        help="checked agent integration starter scenario",
    )
    agent_call.add_argument(
        "--goal",
        default="add predictions to my app",
        help="host prediction goal for setup_engine agent-call readbacks",
    )
    agent_call.add_argument(
        "--view",
        choices=[
            "full",
            "summary",
            "contracts",
            "sources",
            "baseline",
            "host-wrapper",
            "claim-boundary",
            "examples",
        ],
        dest="setup_engine_view",
        help="focused setup_engine agent-call view",
    )
    agent_call.add_argument(
        "--case",
        choices=[
            "accepted_adapter_output",
            "missing_weather_source",
            "missing_baseline_source",
            "missing_outcome_source",
            "ambiguous_service_window",
            "vague_geography",
            "missing_resolution_source",
            "unapproved_source",
            "raw_credential_value",
            "raw_sql_query",
            "unsafe_adapter_output",
            "private_row_exposure",
            "post_outcome_evidence",
        ],
        dest="guided_case",
        help="checked agent integration guided forecast case",
    )
    agent_call.add_argument(
        "--internal-operation",
        choices=[
            "create_prediction",
            "update_prediction",
            "start_prediction",
            "pause_prediction",
            "resume_prediction",
            "run_tick",
            "resolve_due",
            "append_evidence",
            "read_status",
            "database_source_adapter_status",
            "read_forecast_card",
            "read_lifecycle_bundle",
            "archive_record",
            "redact_record",
        ],
        help="stable embedded internal API operation for internal_api agent-call wrapper",
    )
    agent_call.add_argument("--prediction-id", help="prediction id for internal_api agent-call wrapper")
    agent_call.add_argument("--idempotency-key", help="idempotency key for effectful internal_api operations")
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
