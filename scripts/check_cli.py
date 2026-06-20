#!/usr/bin/env python3
"""Smoke-test the local OPE CLI wrapper."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from check_lifecycle_operation_store import REQUIRED_COMPATIBILITY_CLASSES, REQUIRED_WRITE_LOCAL_COMMANDS
from check_live_capture_workspace import fixture_integration_result
from generate_lifecycle_operation_store import SCENARIO_NAMES
from generate_live_connector_readiness import build_readiness
from live_capture_workspace import build_live_result_set, save_live_result_set


ROOT = Path(__file__).resolve().parents[1]
FULL_DRIFT_CHECKS = os.environ.get("OPE_CLI_FULL_DRIFT_CHECKS") == "1"


def run_ope_command(*args: str, check: bool) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "scripts/ope.py", *args]
    rendered = shlex.join(command)
    started = time.perf_counter()
    print(f"[check_cli] start {rendered}", file=sys.stderr, flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    print(
        f"[check_cli] done exit={result.returncode} elapsed={time.perf_counter() - started:.2f}s {rendered}",
        file=sys.stderr,
        flush=True,
    )
    if check:
        result.check_returncode()
    return result


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return run_ope_command(*args, check=True)


def run_cli_unchecked(*args: str) -> subprocess.CompletedProcess[str]:
    return run_ope_command(*args, check=False)


def run_optional_drift_check(*args: str, expected_stdout: str, label: str) -> None:
    if not FULL_DRIFT_CHECKS:
        print(
            f"[check_cli] skip duplicate drift check for {label}; set OPE_CLI_FULL_DRIFT_CHECKS=1 to run it",
            file=sys.stderr,
            flush=True,
        )
        return
    result = run_cli(*args)
    if expected_stdout not in result.stdout:
        raise AssertionError(f"CLI {label} check output drifted")


def agent_call_setup_readback(operation: str) -> dict[str, object]:
    result = run_cli(
        "agent-call",
        "--operation",
        operation,
        "--forecast-id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    return json.loads(result.stdout)


def main() -> None:
    generate_fixtures_list = run_cli("generate-fixtures", "--list")
    if "scripts/generate_prediction_campaign_explain.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the campaign explain generator")
    if "scripts/generate_prediction_campaign_pre_calibration.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the campaign pre-calibration generator")
    if "scripts/generate_helsinki_traffic_pilot_runbook.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the Helsinki pilot runbook generator")
    if "scripts/generate_helsinki_traffic_pilot_readiness.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the Helsinki pilot readiness generator")
    if "scripts/generate_lifecycle_operation_store.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the lifecycle operation store generator")
    if "scripts/generate_postgres_compatibility.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the Postgres compatibility generator")
    if "scripts/generate_database_source_adapter_runtime.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the database source-adapter runtime generator")
    if "scripts/generate_opp_provider_adapter.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the OPP provider-adapter generator")
    if "scripts/generate_persistent_sqlite_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the persistent SQLite policy generator")
    if "scripts/generate_lifecycle_lease_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the lifecycle lease policy generator")
    if "scripts/generate_runtime_transport_readiness.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the runtime transport readiness generator")
    if "scripts/generate_internal_api.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the internal API generator")
    if "scripts/generate_prediction_workspace_registry.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the prediction workspace registry generator")
    if "scripts/generate_source_bindings.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the source binding generator")
    if "scripts/generate_domain_source_field_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the domain/source field policy generator")
    if "scripts/generate_credential_reference_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the credential-reference policy generator")
    if "scripts/generate_retention_redaction_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the retention/redaction policy generator")
    if "scripts/generate_private_auto_evidence_policy.py --check" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures should list the private auto-evidence policy generator")
    if "fixture commands" not in generate_fixtures_list.stdout:
        raise AssertionError("CLI generate-fixtures list output drifted")
    run_cli("resolve-live")
    run_cli("evidence-plan")
    run_cli("gather-evidence")
    run_cli("source-connectors", "--check")
    run_cli("live-readiness", "--check")
    run_cli("transit-api-connector", "--check")
    run_cli("domain-setups", "--check")
    run_cli("domain-configs", "--check")
    run_cli("source-bindings", "--check")
    run_cli("domain-source-field-policy", "--check")
    run_cli("credential-reference-policy", "--check")
    run_cli("retention-redaction-policy", "--check")
    run_cli("private-auto-evidence-policy", "--check")
    run_cli("transit-delay-forward-run", "--check")
    run_cli("resolve-due-forward-runs", "--check")
    run_cli("resolution-jobs", "--check")
    run_cli("resolution-scheduler", "--check")
    run_cli("resolution-runtime-reliability", "--check")
    run_optional_drift_check(
        "lifecycle-operation-store",
        "--check",
        expected_stdout="checked lifecycle operation store",
        label="lifecycle-operation-store",
    )
    run_cli("transit-forward-run-corpus", "--check")
    transit_corpus_growth = run_cli("transit-corpus-growth")
    transit_corpus_growth_payload = json.loads(transit_corpus_growth.stdout)
    if transit_corpus_growth_payload["projectedComparableResolved"] != 2:
        raise AssertionError("CLI transit-corpus-growth projected comparable count drifted")
    growth_candidates = {
        item["candidateCase"]: item for item in transit_corpus_growth_payload["candidateUpdates"]
    }
    if growth_candidates["comparable_resolved"]["appendDecision"] != "append_ready":
        raise AssertionError("CLI transit-corpus-growth should expose append-ready comparable candidate")
    if growth_candidates["leakage_risk"]["appendDecision"] != "reject_from_corpus":
        raise AssertionError("CLI transit-corpus-growth should reject leakage-risk candidates")
    transit_corpus_growth_check = run_cli("transit-corpus-growth", "--check")
    if "checked transit corpus growth loop" not in transit_corpus_growth_check.stdout:
        raise AssertionError("CLI transit-corpus-growth check output drifted")
    run_cli("transit-track-record-gate", "--check")
    run_cli("transit-method-options", "--check")
    run_cli("transit-live-evidence-promotion", "--check")
    run_cli("source-intake", "--check")
    run_cli("source-builder", "--check")
    run_cli("source-adapter-output", "--check")
    source_adapter_intake = run_cli("source-adapter-intake")
    source_adapter_intake_payload = json.loads(source_adapter_intake.stdout)
    if source_adapter_intake_payload["caseCount"] != 5:
        raise AssertionError("CLI source-adapter-intake should expose five conformance cases")
    source_adapter_intake_cases = {
        item["case"]: item for item in source_adapter_intake_payload["cases"]
    }
    if source_adapter_intake_cases["accepted"]["nextAction"] != "proceed_to_method_gating":
        raise AssertionError("CLI source-adapter-intake should route accepted output to method gate")
    if source_adapter_intake_cases["needs_confirmation"]["nextAction"] != "ask_mapping_confirmation":
        raise AssertionError("CLI source-adapter-intake should route proposed mappings to confirmation")
    if source_adapter_intake_cases["insufficient_data"]["nextAction"] != "collect_more_data":
        raise AssertionError("CLI source-adapter-intake should route insufficient data to collection")
    if source_adapter_intake_cases["rejected"]["nextAction"] != "replace_source":
        raise AssertionError("CLI source-adapter-intake should route rejected output to replacement")
    if source_adapter_intake_cases["unsafe_blocked"]["nextAction"] != "stop_unsafe_connector":
        raise AssertionError("CLI source-adapter-intake should stop unsafe outputs")
    source_adapter_intake_check = run_cli("source-adapter-intake", "--check")
    if "checked source adapter intake fixtures" not in source_adapter_intake_check.stdout:
        raise AssertionError("CLI source-adapter-intake check output drifted")
    source_quality = run_cli("source-quality")
    source_quality_payload = json.loads(source_quality.stdout)
    if source_quality_payload["summary"]["caseCount"] != 7:
        raise AssertionError("CLI source-quality should expose seven quality cases")
    source_quality_cases = {
        item["case"]: item for item in source_quality_payload["caseRows"]
    }
    if source_quality_cases["source_intake_accepted"]["qualityStatus"] != "forecast_usable":
        raise AssertionError("CLI source-quality should expose forecast-usable accepted intake")
    if source_quality_cases["source_intake_needs_confirmation"]["recommendedNextAction"] != "confirm_mappings":
        raise AssertionError("CLI source-quality should ask to confirm mappings")
    if source_quality_cases["adapter_insufficient_data"]["recommendedNextAction"] != "collect_more_data":
        raise AssertionError("CLI source-quality should route insufficient data to collection")
    if source_quality_cases["adapter_unsafe"]["recommendedNextAction"] != "stop_unsafe_connector":
        raise AssertionError("CLI source-quality should stop unsafe adapter output")
    source_quality_check = run_cli("source-quality", "--check")
    if "checked source quality mapping confidence" not in source_quality_check.stdout:
        raise AssertionError("CLI source-quality check output drifted")
    run_cli("source-handoff", "--check")
    run_optional_drift_check(
        "source-handoff-method",
        "--check",
        expected_stdout="checked source handoff method gates",
        label="source-handoff-method",
    )
    run_cli("auto-forecast")
    run_cli("resolve-auto-evidence")
    run_cli("historical-forecast")
    run_cli("method-comparison", "--check")
    run_cli("method-selection", "--check")
    run_cli("setup-benchmark", "--check")
    run_cli("setup-method", "--check")
    run_cli("setup-forecast", "--check")
    run_optional_drift_check(
        "source-handoff-forecast",
        "--check",
        expected_stdout="checked 12 source-handoff setup forecast outputs",
        label="source-handoff-forecast",
    )
    local_source_runtime = run_cli("local-source-runtime")
    local_source_runtime_payload = json.loads(local_source_runtime.stdout)
    if local_source_runtime_payload["summary"]["forecastCardReadyCount"] != 1:
        raise AssertionError("CLI local-source-runtime should expose one forecast-card-ready case")
    if local_source_runtime_payload["forecastCardReadback"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI local-source-runtime should bind forecast-1102 readback")
    runtime_cases = {
        item["case"]: item for item in local_source_runtime_payload["cases"]
    }
    if runtime_cases["approved_local_folder"]["runtimeStatus"] != "forecast_card_ready":
        raise AssertionError("CLI local-source-runtime should accept approved local folder")
    if runtime_cases["missing_approval"]["nextAction"] != "confirm_approval":
        raise AssertionError("CLI local-source-runtime should ask for missing approval")
    if runtime_cases["unsafe_path"]["runtimeStatus"] != "blocked_unsafe_path":
        raise AssertionError("CLI local-source-runtime should block unsafe paths")
    run_optional_drift_check(
        "local-source-runtime",
        "--check",
        expected_stdout="checked local source runtime",
        label="local-source-runtime",
    )
    run_cli("resolve-source-handoff")
    run_optional_drift_check(
        "source-handoff-runbook",
        "--check",
        expected_stdout="checked source handoff setup runbook",
        label="source-handoff-runbook",
    )
    run_optional_drift_check(
        "private-setup-workflow",
        "--check",
        expected_stdout="checked private setup workflow",
        label="private-setup-workflow",
    )
    run_optional_drift_check(
        "private-source-adapters",
        "--check",
        expected_stdout="checked private source adapter capabilities",
        label="private-source-adapters",
    )
    run_optional_drift_check(
        "private-source-adapter-outcomes",
        "--check",
        expected_stdout="checked private source adapter outcome matrix",
        label="private-source-adapter-outcomes",
    )
    run_optional_drift_check(
        "private-source-adapter-bridge",
        "--check",
        expected_stdout="checked private source adapter intake bridge",
        label="private-source-adapter-bridge",
    )
    run_optional_drift_check(
        "private-setup-requests",
        "--check",
        expected_stdout="checked private setup requests",
        label="private-setup-requests",
    )
    run_optional_drift_check(
        "private-setup-actions",
        "--check",
        expected_stdout="checked private setup first actions",
        label="private-setup-actions",
    )
    run_optional_drift_check(
        "private-setup-action-runbook",
        "--check",
        expected_stdout="checked private setup first-action runbook",
        label="private-setup-action-runbook",
    )
    run_optional_drift_check(
        "private-setup-bundles",
        "--check",
        expected_stdout="checked private setup agent bundles",
        label="private-setup-bundles",
    )
    private_setup_orchestrator = run_cli("private-setup-orchestrator")
    private_setup_orchestrator_payload = json.loads(private_setup_orchestrator.stdout)
    if private_setup_orchestrator_payload["runCount"] != 8:
        raise AssertionError("CLI private-setup-orchestrator should expose eight runs")
    orchestrator_cases = {
        item["runCase"]: item for item in private_setup_orchestrator_payload["runs"]
    }
    if orchestrator_cases["local_file_confirmed"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI private-setup-orchestrator should expose local-file forecast readback")
    if orchestrator_cases["source_adapter_output_accepted"]["nextAction"] != "run_explicit_setup_forecast_execution":
        raise AssertionError("CLI private-setup-orchestrator should route accepted adapter output to forecast execution")
    if orchestrator_cases["unsafe_source"]["nextAction"] != "stop_unsafe_connector":
        raise AssertionError("CLI private-setup-orchestrator should stop unsafe source output")
    run_optional_drift_check(
        "private-setup-orchestrator",
        "--check",
        expected_stdout="checked private setup orchestrator",
        label="private-setup-orchestrator",
    )
    agent_pilot_validation = run_cli("agent-pilot-validation")
    agent_pilot_validation_payload = json.loads(agent_pilot_validation.stdout)
    if agent_pilot_validation_payload["taskCount"] != 6:
        raise AssertionError("CLI agent-pilot-validation should expose six task scenarios")
    pilot_scenarios = {
        item["scenarioKey"]: item for item in agent_pilot_validation_payload["taskScenarios"]
    }
    if pilot_scenarios["local_file_setup_readback"]["expectedOutcomeClass"] != "completed_forecast_readback":
        raise AssertionError("CLI agent-pilot-validation local-file scenario drifted")
    if pilot_scenarios["accepted_adapter_output_ready"]["expectedOutcomeClass"] != "ready_for_forecast_execution":
        raise AssertionError("CLI agent-pilot-validation accepted-adapter scenario drifted")
    if pilot_scenarios["unsafe_source_block"]["expectedOutcomeClass"] != "blocked_unsafe":
        raise AssertionError("CLI agent-pilot-validation unsafe-source scenario drifted")
    if pilot_scenarios["engine_setup_shortcut_comprehension"]["expectedOutcomeClass"] != "setup_engine_shortcut_readback":
        raise AssertionError("CLI agent-pilot-validation setup-comprehension scenario drifted")
    run_optional_drift_check(
        "agent-pilot-validation",
        "--check",
        expected_stdout="checked agent pilot validation pack",
        label="agent-pilot-validation",
    )
    pilot_evidence = run_cli("pilot-evidence")
    pilot_evidence_payload = json.loads(pilot_evidence.stdout)
    if pilot_evidence_payload["summary"]["acceptedRealSessionCount"] != 0:
        raise AssertionError("CLI pilot-evidence should not count real sessions yet")
    if pilot_evidence_payload["summary"]["pilotEvidenceStatus"] != "real_sessions_needed":
        raise AssertionError("CLI pilot-evidence should require real sessions")
    pilot_evidence_cases = {
        item["caseKey"]: item for item in pilot_evidence_payload["caseRows"]
    }
    if pilot_evidence_cases["accepted_sanitized_summary"]["intakeStatus"] != "accepted_for_aggregation":
        raise AssertionError("CLI pilot-evidence should expose accepted sanitized summary")
    if pilot_evidence_cases["raw_transcript_blocked"]["intakeStatus"] != "blocked_raw_transcript":
        raise AssertionError("CLI pilot-evidence should block raw transcripts")
    if pilot_evidence_cases["claim_boundary_confusion"]["acceptedForAggregation"] is not True:
        raise AssertionError("CLI pilot-evidence should aggregate sanitized claim-boundary issues")
    pilot_evidence_summary = run_cli("pilot-evidence", "--section", "summary")
    pilot_evidence_summary_payload = json.loads(pilot_evidence_summary.stdout)
    if pilot_evidence_summary_payload["expansionEvidenceReady"] is not False:
        raise AssertionError("CLI pilot-evidence summary should not unblock expansion")
    pilot_evidence_append_plan = run_cli(
        "pilot-evidence",
        "--input-summary",
        "spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json",
    )
    pilot_evidence_append_payload = json.loads(pilot_evidence_append_plan.stdout)
    if pilot_evidence_append_payload["appendDecision"] != "ready_for_local_write":
        raise AssertionError("CLI pilot-evidence append plan should be ready for explicit local write")
    if pilot_evidence_append_payload["writeLocalRequired"] is not True:
        raise AssertionError("CLI pilot-evidence append plan should require local write")
    if pilot_evidence_append_payload["writeLocalRequested"] is not False:
        raise AssertionError("CLI pilot-evidence append plan should be dry-run by default")
    if pilot_evidence_append_payload["ledgerRowsWritten"] != 0:
        raise AssertionError("CLI pilot-evidence append plan must not write rows by default")
    if pilot_evidence_append_payload["realSessionsRecorded"] != 0:
        raise AssertionError("CLI pilot-evidence append plan must not record sessions by default")
    pilot_evidence_blocked_append = run_cli(
        "pilot-evidence",
        "--input-summary",
        "spec/fixtures/pilot-summary-intake/blocked-raw-transcript-summary.json",
    )
    pilot_evidence_blocked_payload = json.loads(pilot_evidence_blocked_append.stdout)
    if pilot_evidence_blocked_payload["appendDecision"] != "blocked_by_intake":
        raise AssertionError("CLI pilot-evidence append plan should block unsafe summaries")
    if pilot_evidence_blocked_payload["candidateRow"] is not None:
        raise AssertionError("CLI pilot-evidence blocked append plan must not expose a candidate row")
    run_optional_drift_check(
        "pilot-evidence",
        "--check",
        expected_stdout="checked pilot evidence ledger",
        label="pilot-evidence",
    )
    pilot_session_packet = run_cli("pilot-session-packet")
    pilot_session_packet_payload = json.loads(pilot_session_packet.stdout)
    if pilot_session_packet_payload["collectionSummary"]["taskCardCount"] != 7:
        raise AssertionError("CLI pilot-session-packet should expose seven task cards")
    if pilot_session_packet_payload["collectionSummary"]["realSessionsRecorded"] != 0:
        raise AssertionError("CLI pilot-session-packet should not record real sessions")
    if pilot_session_packet_payload["collectionSummary"]["expansionEvidenceReady"] is not False:
        raise AssertionError("CLI pilot-session-packet must not unblock expansion")
    pilot_session_tasks = {
        item["scenarioKey"]: item for item in pilot_session_packet_payload["taskCards"]
    }
    if pilot_session_tasks["claim_gate_readback"]["claimBoundaryRequired"] is not True:
        raise AssertionError("CLI pilot-session-packet should require claim-boundary capture for claim gate")
    if pilot_session_tasks["repeating_prediction_campaign"]["claimBoundaryRequired"] is not True:
        raise AssertionError("CLI pilot-session-packet should require claim-boundary capture for repeating campaign")
    if pilot_session_tasks["engine_setup_shortcut_comprehension"]["claimBoundaryRequired"] is not True:
        raise AssertionError("CLI pilot-session-packet should require claim-boundary capture for setup comprehension")
    pilot_session_setup_task = run_cli("pilot-session-packet", "--task", "engine_setup_shortcut_comprehension")
    pilot_session_setup_task_payload = json.loads(pilot_session_setup_task.stdout)
    if pilot_session_setup_task_payload["taskId"] != "agentpilottask-006":
        raise AssertionError("CLI pilot-session-packet setup task id drifted")
    if pilot_session_setup_task_payload["scenarioKey"] != "engine_setup_shortcut_comprehension":
        raise AssertionError("CLI pilot-session-packet setup task selector drifted")
    pilot_session_template = run_cli("pilot-session-packet", "--section", "template")
    pilot_session_template_payload = json.loads(pilot_session_template.stdout)
    if not pilot_session_template_payload["ledgerSubmissionShape"]["canSubmitToPilotEvidence"]:
        raise AssertionError("CLI pilot-session-packet template should be ledger-submission shaped")
    run_optional_drift_check(
        "pilot-session-packet",
        "--check",
        expected_stdout="checked pilot session packet",
        label="pilot-session-packet",
    )
    pilot_session_brief = run_cli("pilot-session-brief", "--section", "summary")
    pilot_session_brief_payload = json.loads(pilot_session_brief.stdout)
    if pilot_session_brief_payload["briefStatus"] != "ready_for_supervised_session":
        raise AssertionError("CLI pilot-session-brief summary status drifted")
    if pilot_session_brief_payload["recommendedScenarioKey"] != "engine_setup_shortcut_comprehension":
        raise AssertionError("CLI pilot-session-brief should default to setup comprehension")
    if pilot_session_brief_payload["genericAgentGuidanceReady"] is not True:
        raise AssertionError("CLI pilot-session-brief should expose generic guidance")
    if pilot_session_brief_payload["draftLedgerReady"] is not False:
        raise AssertionError("CLI pilot-session-brief draft must not be ledger-ready unchanged")
    if pilot_session_brief_payload["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI pilot-session-brief must keep quality claims blocked")
    pilot_session_brief_commands = run_cli("pilot-session-brief", "--section", "commands")
    pilot_session_brief_commands_payload = json.loads(pilot_session_brief_commands.stdout)
    if pilot_session_brief_commands_payload[1]["command"] != "python3 scripts/ope.py agent-guide --section generic":
        raise AssertionError("CLI pilot-session-brief should route through generic agent guidance")
    if pilot_session_brief_commands_payload[5]["mutatesLocalState"] is not True:
        raise AssertionError("CLI pilot-session-brief should mark explicit append as the only mutation")
    run_optional_drift_check(
        "pilot-session-brief",
        "--check",
        expected_stdout="checked pilot session brief",
        label="pilot-session-brief",
    )
    pilot_summary_intake = run_cli("pilot-summary-intake")
    pilot_summary_intake_payload = json.loads(pilot_summary_intake.stdout)
    if pilot_summary_intake_payload["summary"]["acceptedLedgerReadyCount"] != 2:
        raise AssertionError("CLI pilot-summary-intake should expose two ledger-ready examples")
    if pilot_summary_intake_payload["summary"]["realSessionsRecorded"] != 0:
        raise AssertionError("CLI pilot-summary-intake should not record real sessions")
    if pilot_summary_intake_payload["summary"]["ledgerRowsWritten"] != 0:
        raise AssertionError("CLI pilot-summary-intake should not write ledger rows")
    pilot_summary_cases = {
        item["caseKey"]: item for item in pilot_summary_intake_payload["submissionCases"]
    }
    if pilot_summary_cases["accepted_local_setup_summary"]["ledgerReady"] is not True:
        raise AssertionError("CLI pilot-summary-intake should accept sanitized local setup summaries")
    if pilot_summary_cases["blocked_raw_transcript"]["intakeDecision"] != "block_raw_transcript":
        raise AssertionError("CLI pilot-summary-intake should block raw transcripts")
    if pilot_summary_cases["blocked_quality_claim"]["intakeDecision"] != "block_claim_overreach":
        raise AssertionError("CLI pilot-summary-intake should block quality overclaims")
    pilot_summary_input = run_cli(
        "pilot-summary-intake",
        "--input",
        "spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json",
    )
    pilot_summary_input_payload = json.loads(pilot_summary_input.stdout)
    if pilot_summary_input_payload["intakeDecision"] != "accept_for_ledger_review":
        raise AssertionError("CLI pilot-summary-intake input should classify accepted summaries")
    if pilot_summary_input_payload["candidateRealSessionEvidence"] is not True:
        raise AssertionError("CLI pilot-summary-intake input should mark accepted summaries as candidate evidence")
    if pilot_summary_input_payload["contributesRealSessionEvidence"] is not False:
        raise AssertionError("CLI pilot-summary-intake input must not count real evidence")
    if pilot_summary_input_payload["ledgerRowsWritten"] != 0:
        raise AssertionError("CLI pilot-summary-intake input must not write ledger rows")
    pilot_summary_blocked_input = run_cli(
        "pilot-summary-intake",
        "--input",
        "spec/fixtures/pilot-summary-intake/blocked-raw-transcript-summary.json",
    )
    pilot_summary_blocked_payload = json.loads(pilot_summary_blocked_input.stdout)
    if pilot_summary_blocked_payload["intakeDecision"] != "block_raw_transcript":
        raise AssertionError("CLI pilot-summary-intake input should block raw transcript summaries")
    if pilot_summary_blocked_payload["candidateRealSessionEvidence"] is not False:
        raise AssertionError("CLI pilot-summary-intake blocked input must not be candidate evidence")
    pilot_summary_review = run_cli(
        "pilot-summary-review",
        "--input",
        "spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json",
        "--section",
        "summary",
    )
    pilot_summary_review_payload = json.loads(pilot_summary_review.stdout)
    if pilot_summary_review_payload["appendDecision"] != "ready_for_local_write":
        raise AssertionError("CLI pilot-summary-review should expose append-ready accepted summaries")
    if pilot_summary_review_payload["canAppendWithWriteLocal"] is not True:
        raise AssertionError("CLI pilot-summary-review should mark accepted summaries as write-local eligible")
    if pilot_summary_review_payload["ledgerRowsWritten"] != 0:
        raise AssertionError("CLI pilot-summary-review must remain read-only")
    pilot_summary_review_blocked = run_cli(
        "pilot-summary-review",
        "--input",
        "spec/fixtures/pilot-summary-intake/blocked-raw-transcript-summary.json",
        "--section",
        "summary",
    )
    pilot_summary_review_blocked_payload = json.loads(pilot_summary_review_blocked.stdout)
    if pilot_summary_review_blocked_payload["appendDecision"] != "blocked_by_intake":
        raise AssertionError("CLI pilot-summary-review should block unsafe summaries")
    if pilot_summary_review_blocked_payload["canAppendWithWriteLocal"] is not False:
        raise AssertionError("CLI pilot-summary-review must not allow blocked summaries to append")
    run_optional_drift_check(
        "pilot-summary-review",
        "--check",
        expected_stdout="checked pilot summary review",
        label="pilot-summary-review",
    )
    pilot_summary_rules = run_cli("pilot-summary-intake", "--section", "rules")
    pilot_summary_rules_payload = json.loads(pilot_summary_rules.stdout)
    if pilot_summary_rules_payload[0]["decision"] != "Accept for ledger review.":
        raise AssertionError("CLI pilot-summary-intake rules order drifted")
    run_optional_drift_check(
        "pilot-summary-intake",
        "--check",
        expected_stdout="checked pilot summary intake",
        label="pilot-summary-intake",
    )
    pilot_summary_template = run_cli("pilot-summary-template", "--section", "summary")
    pilot_summary_template_payload = json.loads(pilot_summary_template.stdout)
    if pilot_summary_template_payload["templateStatus"] != "ready_for_operator_fill":
        raise AssertionError("CLI pilot-summary-template summary status drifted")
    if pilot_summary_template_payload["recommendedScenarioKey"] != "engine_setup_shortcut_comprehension":
        raise AssertionError("CLI pilot-summary-template should default to setup comprehension")
    if pilot_summary_template_payload["draftLedgerReady"] is not False:
        raise AssertionError("CLI pilot-summary-template draft must not be ledger-ready unchanged")
    if pilot_summary_template_payload["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI pilot-summary-template must keep quality claims blocked")
    pilot_summary_template_draft = run_cli("pilot-summary-template", "--section", "draft")
    pilot_summary_template_draft_payload = json.loads(pilot_summary_template_draft.stdout)
    if pilot_summary_template_draft_payload["dimensionRatings"] != []:
        raise AssertionError("CLI pilot-summary-template draft should require operator-entered ratings")
    if pilot_summary_template_draft_payload["riskSignals"]["unredactedSourceDetailDetected"] is not True:
        raise AssertionError("CLI pilot-summary-template draft should classify as needs-redaction unchanged")
    pilot_summary_template_commands = run_cli("pilot-summary-template", "--section", "commands")
    pilot_summary_template_commands_payload = json.loads(pilot_summary_template_commands.stdout)
    if pilot_summary_template_commands_payload[0]["command"] != "python3 scripts/ope.py pilot-summary-template --section draft":
        raise AssertionError("CLI pilot-summary-template should expose the draft print command first")
    if pilot_summary_template_commands_payload[2]["mutatesLocalState"] is not True:
        raise AssertionError("CLI pilot-summary-template should mark explicit local append as the only mutation")
    run_optional_drift_check(
        "pilot-summary-template",
        "--check",
        expected_stdout="checked pilot summary template",
        label="pilot-summary-template",
    )
    simulated_agent_pilot = run_cli("simulated-agent-pilot", "--section", "summary")
    simulated_agent_pilot_payload = json.loads(simulated_agent_pilot.stdout)
    if simulated_agent_pilot_payload["simulatedSessionCount"] != 8:
        raise AssertionError("CLI simulated-agent-pilot should expose eight simulated sessions")
    if simulated_agent_pilot_payload["userPromptSessionCount"] != 1:
        raise AssertionError("CLI simulated-agent-pilot should expose one user prompt")
    if simulated_agent_pilot_payload["nonHelsinkiSessionCount"] != 3:
        raise AssertionError("CLI simulated-agent-pilot should expose three non-Helsinki sessions")
    if simulated_agent_pilot_payload["engineSetupComprehensionReady"] is not True:
        raise AssertionError("CLI simulated-agent-pilot should expose setup comprehension readiness")
    if simulated_agent_pilot_payload["realSessionsRecorded"] != 0:
        raise AssertionError("CLI simulated-agent-pilot should not count real sessions")
    if simulated_agent_pilot_payload["pilotEvidenceReady"] is not False:
        raise AssertionError("CLI simulated-agent-pilot must not unblock real pilot evidence")
    run_optional_drift_check(
        "simulated-agent-pilot",
        "--check",
        expected_stdout="checked simulated agent pilot",
        label="simulated-agent-pilot",
    )
    pilot_supervision_status = run_cli("pilot-supervision-status")
    pilot_supervision_status_payload = json.loads(pilot_supervision_status.stdout)
    if pilot_supervision_status_payload["status"] != "real_sessions_needed":
        raise AssertionError("CLI pilot-supervision-status should require real sessions")
    if pilot_supervision_status_payload["localEvidenceMode"] != "not_requested":
        raise AssertionError("CLI pilot-supervision-status should not inspect local evidence by default")
    if pilot_supervision_status_payload["realSessionProgress"]["remainingMinimumSessions"] != 3:
        raise AssertionError("CLI pilot-supervision-status should expose three remaining minimum sessions")
    if (
        pilot_supervision_status_payload["recommendedNextTask"]["scenarioKey"]
        != "engine_setup_shortcut_comprehension"
    ):
        raise AssertionError("CLI pilot-supervision-status recommended task drifted")
    if pilot_supervision_status_payload["executionBoundary"]["qualityClaimsUpgraded"] is not False:
        raise AssertionError("CLI pilot-supervision-status must not upgrade quality claims")
    pilot_supervision_summary = run_cli("pilot-supervision-status", "--section", "summary")
    pilot_supervision_summary_payload = json.loads(pilot_supervision_summary.stdout)
    if pilot_supervision_summary_payload["remainingMinimumSessions"] != 3:
        raise AssertionError("CLI pilot-supervision-status summary should expose remaining sessions")
    if pilot_supervision_summary_payload["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI pilot-supervision-status summary must keep quality claims blocked")
    pilot_supervision_commands = run_cli("pilot-supervision-status", "--section", "commands")
    pilot_supervision_commands_payload = json.loads(pilot_supervision_commands.stdout)
    if pilot_supervision_commands_payload[0]["command"] != "python3 scripts/ope.py pilot-session-packet --task engine_setup_shortcut_comprehension":
        raise AssertionError("CLI pilot-supervision-status command sequence should open the setup task first")
    if pilot_supervision_commands_payload[3]["mutatesLocalState"] is not True:
        raise AssertionError("CLI pilot-supervision-status should mark local evidence append as the only local mutation")
    run_optional_drift_check(
        "pilot-supervision-status",
        "--check",
        expected_stdout="checked pilot supervision status",
        label="pilot-supervision-status",
    )
    local_usage_trace = run_cli("local-usage-trace")
    local_usage_trace_payload = json.loads(local_usage_trace.stdout)
    if local_usage_trace_payload["totalEvents"] != 27:
        raise AssertionError("CLI local-usage-trace should expose twenty-seven events")
    if local_usage_trace_payload["forecastCompletionRate"] != 1.0:
        raise AssertionError("CLI local-usage-trace forecast completion rate drifted")
    if local_usage_trace_payload["hostedTelemetryEnabled"] is not False:
        raise AssertionError("CLI local-usage-trace must not enable hosted telemetry")
    usage_events = {
        item["sourceCase"]: item for item in local_usage_trace_payload["events"]
    }
    if usage_events["unsafe_source_block"]["outcome"] != "blocked":
        raise AssertionError("CLI local-usage-trace should include unsafe blocked path")
    if usage_events["response_too_large_readback"]["sanitizedErrorClass"] != "response_too_large":
        raise AssertionError("CLI local-usage-trace should expose sanitized oversized readback")
    if usage_events["setup_engine_stockout_comprehension"]["eventClass"] != "setup_comprehension":
        raise AssertionError("CLI local-usage-trace should include setup comprehension events")
    if usage_events["campaign_calibration_threshold_met"]["eventClass"] != "campaign":
        raise AssertionError("CLI local-usage-trace should expose campaign lifecycle events")
    if usage_events["agent_integration_guided_forecast"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI local-usage-trace should expose guided agent integration forecast binding")
    if usage_events["agent_integration_missing_weather_block"]["sanitizedErrorClass"] != "missing_source":
        raise AssertionError("CLI local-usage-trace should expose missing-source integration blocker")
    run_optional_drift_check(
        "local-usage-trace",
        "--check",
        expected_stdout="checked local usage trace",
        label="local-usage-trace",
    )
    developer_adoption = run_cli("developer-adoption")
    developer_adoption_payload = json.loads(developer_adoption.stdout)
    if developer_adoption_payload["summary"]["quickstartStepCount"] != 8:
        raise AssertionError("CLI developer-adoption should expose eight quickstart steps")
    if developer_adoption_payload["bindings"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI developer-adoption should bind forecast-1102")
    adoption_interfaces = {
        item["interface"] for item in developer_adoption_payload["integrationInterfaces"]
    }
    if adoption_interfaces != {"cli", "agent_call", "mcp_stdio"}:
        raise AssertionError("CLI developer-adoption should cover CLI, agent-call, and MCP stdio")
    if developer_adoption_payload["typeGenerationDecision"]["generatedTypesIncluded"]:
        raise AssertionError("CLI developer-adoption should defer generated runtime types")
    developer_quickstart = run_cli("developer-adoption", "--section", "quickstart")
    developer_quickstart_payload = json.loads(developer_quickstart.stdout)
    if developer_quickstart_payload[0]["command"] != "python3 scripts/ope.py setup-engine --goal \"add predictions to my app\"":
        raise AssertionError("CLI developer-adoption quickstart should begin with setup-engine front door")
    if "host_wrapper.py" not in developer_quickstart_payload[1]["command"]:
        raise AssertionError("CLI developer-adoption quickstart should render setup-first host wrapper")
    if developer_quickstart_payload[2]["command"] != "python3 --version":
        raise AssertionError("CLI developer-adoption quickstart should include Python setup")
    if "prediction-campaign explain" not in developer_quickstart_payload[-1]["command"]:
        raise AssertionError("CLI developer-adoption quickstart should evaluate recurring campaigns")
    run_optional_drift_check(
        "developer-adoption",
        "--check",
        expected_stdout="checked developer adoption surface",
        label="developer-adoption",
    )
    expansion_readiness = run_cli("expansion-readiness")
    expansion_readiness_payload = json.loads(expansion_readiness.stdout)
    if expansion_readiness_payload["gateStatus"] != "blocked_pending_evidence":
        raise AssertionError("CLI expansion-readiness should remain blocked pending evidence")
    if expansion_readiness_payload["summary"]["readyOptionCount"] != 0:
        raise AssertionError("CLI expansion-readiness should not mark options ready")
    if expansion_readiness_payload["bindings"]["developerAdoptionSurfaceId"] != "developeradoptionsurface-001":
        raise AssertionError("CLI expansion-readiness adoption binding drifted")
    if expansion_readiness_payload["bindings"]["pilotEvidenceLedgerId"] != "pilotevidenceledger-001":
        raise AssertionError("CLI expansion-readiness pilot evidence binding drifted")
    expansion_options = {
        item["area"]: item for item in expansion_readiness_payload["expansionOptions"]
    }
    if set(expansion_options) != {
        "hosted_runtime",
        "broader_private_sources",
        "live_forecast_evidence",
        "stronger_methods",
        "generated_runtime_types",
    }:
        raise AssertionError("CLI expansion-readiness option coverage drifted")
    if expansion_options["hosted_runtime"]["status"] != "blocked_pending_evidence":
        raise AssertionError("CLI expansion-readiness should block hosted runtime")
    if expansion_options["generated_runtime_types"]["status"] != "deferred_pending_adoption_evidence":
        raise AssertionError("CLI expansion-readiness should defer generated runtime types")
    expansion_evidence = {
        item["source"]: item for item in expansion_readiness_payload["evidenceInputs"]
    }
    if expansion_evidence["repeating prediction campaign explain"]["status"] != "met":
        raise AssertionError("CLI expansion-readiness should evaluate recurring prediction setup")
    expansion_option_section = run_cli("expansion-readiness", "--section", "options")
    expansion_option_payload = json.loads(expansion_option_section.stdout)
    if expansion_option_payload[0]["area"] != "hosted_runtime":
        raise AssertionError("CLI expansion-readiness option section order drifted")
    run_optional_drift_check(
        "expansion-readiness",
        "--check",
        expected_stdout="checked expansion readiness gate",
        label="expansion-readiness",
    )
    repeating_setup = run_cli("repeating-prediction-setup")
    repeating_setup_payload = json.loads(repeating_setup.stdout)
    if repeating_setup_payload["setupStatus"] != "contract_ready_non_executing":
        raise AssertionError("CLI repeating-prediction-setup status drifted")
    if repeating_setup_payload["summary"]["campaignExampleCount"] != 6:
        raise AssertionError("CLI repeating-prediction-setup should expose six campaign examples")
    if repeating_setup_payload["summary"]["runnerImplemented"] is not False:
        raise AssertionError("CLI repeating-prediction-setup must not implement a runner")
    repeating_cases = {
        item["caseKey"]: item for item in repeating_setup_payload["campaignExamples"]
    }
    if repeating_cases["daily_100_run_transit_calibration"]["schedulePolicy"]["targetCount"] != 100:
        raise AssertionError("CLI repeating-prediction-setup daily calibration target drifted")
    if repeating_cases["post_calibration_restart_campaign"]["postCalibrationPolicy"]["action"] != "pause_then_resume_after":
        raise AssertionError("CLI repeating-prediction-setup post-calibration policy drifted")
    repeating_schedules = run_cli("repeating-prediction-setup", "--section", "schedules")
    repeating_schedules_payload = json.loads(repeating_schedules.stdout)
    if repeating_schedules_payload[0]["policyKind"] != "fixed_count":
        raise AssertionError("CLI repeating-prediction-setup schedule section order drifted")
    repeating_setup_check = run_cli("repeating-prediction-setup", "--check")
    if "checked repeating prediction setup" not in repeating_setup_check.stdout:
        raise AssertionError("CLI repeating-prediction-setup check output drifted")
    prediction_campaign = run_cli("prediction-campaign")
    prediction_campaign_payload = json.loads(prediction_campaign.stdout)
    if prediction_campaign_payload["manifestStatus"] != "planned_dry_run_non_executing":
        raise AssertionError("CLI prediction-campaign manifest status drifted")
    if prediction_campaign_payload["summary"]["plannedRunCount"] != 4:
        raise AssertionError("CLI prediction-campaign should expose four dry-run planned runs")
    if prediction_campaign_payload["summary"]["targetRunCount"] != 100:
        raise AssertionError("CLI prediction-campaign should expose the 100-run pilot target")
    if prediction_campaign_payload["summary"]["runnerImplemented"] is not False:
        raise AssertionError("CLI prediction-campaign must not implement a runner")
    if prediction_campaign_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI prediction-campaign must not create forecast artifacts")
    campaign_plan = run_cli("prediction-campaign", "plan")
    campaign_plan_payload = json.loads(campaign_plan.stdout)
    if campaign_plan_payload["plannedRuns"][0]["runId"] != "predictionrun-1301":
        raise AssertionError("CLI prediction-campaign plan first run ID drifted")
    if campaign_plan_payload["plannedRuns"][0]["forecastId"] == "forecast-1102":
        raise AssertionError("CLI prediction-campaign plan must not reuse fixture forecast IDs")
    if campaign_plan_payload["materialization"]["materializationMode"] != "bounded_preview":
        raise AssertionError("CLI prediction-campaign plan should default to bounded preview")
    campaign_full_plan = run_cli("prediction-campaign", "plan", "--count", "100", "--full-materialization")
    campaign_full_plan_payload = json.loads(campaign_full_plan.stdout)
    if campaign_full_plan_payload["materialization"]["materializationMode"] != "full_100_run_pilot":
        raise AssertionError("CLI prediction-campaign full materialization mode drifted")
    if len(campaign_full_plan_payload["plannedRuns"]) != 100:
        raise AssertionError("CLI prediction-campaign full materialization should expose 100 runs")
    if campaign_full_plan_payload["plannedRuns"][-1]["runId"] != "predictionrun-1400":
        raise AssertionError("CLI prediction-campaign full materialization final run drifted")
    if campaign_full_plan_payload["materialization"]["duplicateConflictCount"] != 0:
        raise AssertionError("CLI prediction-campaign full materialization duplicate audit drifted")
    campaign_status = run_cli("prediction-campaign", "status")
    campaign_status_payload = json.loads(campaign_status.stdout)
    if campaign_status_payload["progress"]["nextResolutionRunId"] != "none":
        raise AssertionError("CLI prediction-campaign status should have no due resolution yet")
    prediction_campaign_check = run_cli("prediction-campaign", "--check")
    if "checked prediction campaign manifest" not in prediction_campaign_check.stdout:
        raise AssertionError("CLI prediction-campaign check output drifted")
    prediction_campaign_start = run_cli("prediction-campaign", "start")
    prediction_campaign_start_payload = json.loads(prediction_campaign_start.stdout)
    if prediction_campaign_start_payload["runnerStatus"] != "dry_run_ready_non_executing":
        raise AssertionError("CLI prediction-campaign start status drifted")
    if prediction_campaign_start_payload["summary"]["forecastCreationImplemented"] is not True:
        raise AssertionError("CLI prediction-campaign start should expose explicit local forecast creation")
    if prediction_campaign_start_payload["progress"]["nextForecastRunId"] != "predictionrun-1301":
        raise AssertionError("CLI prediction-campaign start next forecast run drifted")
    if prediction_campaign_start_payload["progress"]["materializedRunCount"] != 4:
        raise AssertionError("CLI prediction-campaign start materialized count drifted")
    if prediction_campaign_start_payload["outputModes"]["capturedStdoutMode"] != "jsonl":
        raise AssertionError("CLI prediction-campaign start captured output mode drifted")
    if prediction_campaign_start_payload["campaignCreationRequest"]["inputMode"] != "default_fixture":
        raise AssertionError("CLI prediction-campaign start default input mode drifted")
    if prediction_campaign_start_payload["campaignCreationRequest"]["targetCount"] != "100":
        raise AssertionError("CLI prediction-campaign start target count drifted")
    if prediction_campaign_start_payload["preCalibration"]["requestStatus"] != "not_requested":
        raise AssertionError("CLI prediction-campaign start should not pre-calibrate by default")
    if prediction_campaign_start_payload["forecastSchedule"]["readyRunId"] != "predictionrun-1301":
        raise AssertionError("CLI prediction-campaign start forecast schedule ready run drifted")
    if prediction_campaign_start_payload["missedRunPolicy"]["recordedRunStatus"] != "missed":
        raise AssertionError("CLI prediction-campaign start missed-run status drifted")
    if prediction_campaign_start_payload["missedRunPolicy"]["excludedFromComparableEvidence"] is not True:
        raise AssertionError("CLI prediction-campaign start must exclude missed runs from comparable evidence")
    prediction_campaign_missed_policy = run_cli("prediction-campaign", "start", "--view", "missed-run-policy")
    prediction_campaign_missed_policy_payload = json.loads(prediction_campaign_missed_policy.stdout)
    if prediction_campaign_missed_policy_payload["exclusionReasonCode"] != "missed_forecast_close":
        raise AssertionError("CLI prediction-campaign missed-run policy reason drifted")
    if prediction_campaign_missed_policy_payload["appendsCorpusEvidence"] is not False:
        raise AssertionError("CLI prediction-campaign missed-run policy must not append corpus evidence")
    prediction_campaign_forecast_schedule = run_cli("prediction-campaign", "start", "--view", "forecast-schedule")
    prediction_campaign_forecast_schedule_payload = json.loads(prediction_campaign_forecast_schedule.stdout)
    if prediction_campaign_forecast_schedule_payload["creationCommand"] != "python3 scripts/ope.py prediction-campaign start --write-local --output-format jsonl":
        raise AssertionError("CLI prediction-campaign forecast schedule command drifted")
    if prediction_campaign_forecast_schedule_payload["createsForecastArtifactsInDryRun"] is not False:
        raise AssertionError("CLI prediction-campaign forecast schedule must remain dry-run non-mutating")
    prediction_campaign_foreground = run_cli(
        "prediction-campaign",
        "start",
        "--watch",
        "--max-ticks",
        "1",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_foreground_payload = json.loads(prediction_campaign_foreground.stdout)
    if prediction_campaign_foreground_payload["runnerStatus"] != "foreground_forecast_ticks_completed":
        raise AssertionError("CLI prediction-campaign foreground tick status drifted")
    if prediction_campaign_foreground_payload["executionMode"] != "dry_run":
        raise AssertionError("CLI prediction-campaign foreground tick should default to dry-run")
    if prediction_campaign_foreground_payload["summary"]["boundedForegroundSchedulingImplemented"] is not True:
        raise AssertionError("CLI prediction-campaign foreground tick should expose bounded foreground scheduling")
    if prediction_campaign_foreground_payload["summary"]["futureWindowPollingImplemented"] is not False:
        raise AssertionError("CLI prediction-campaign foreground tick should not claim future-window polling")
    if prediction_campaign_foreground_payload["executionBoundary"]["writesCampaignState"] is not False:
        raise AssertionError("CLI prediction-campaign foreground dry-run must not write campaign state")
    if prediction_campaign_foreground_payload["executionBoundary"]["writesPreCalibrationState"] is not False:
        raise AssertionError("CLI prediction-campaign foreground dry-run must not write pre-calibration state")
    prediction_campaign_next_due = run_cli(
        "prediction-campaign",
        "start",
        "--now",
        "2026-06-12T00:00:00Z",
        "--watch",
        "--max-ticks",
        "1",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_next_due_payload = json.loads(prediction_campaign_next_due.stdout)
    if prediction_campaign_next_due_payload["ticks"][0]["readyRunId"] != "predictionrun-1302":
        raise AssertionError("CLI prediction-campaign next-due scheduling run drifted")
    if prediction_campaign_next_due_payload["summary"]["nextDueRunSchedulingImplemented"] is not True:
        raise AssertionError("CLI prediction-campaign foreground tick should expose next-due scheduling")
    prediction_campaign_mini_smoke = run_cli(
        "prediction-campaign",
        "start",
        "--plan-count",
        "3",
        "--count",
        "3",
        "--view",
        "forecast-schedule",
    )
    prediction_campaign_mini_smoke_payload = json.loads(prediction_campaign_mini_smoke.stdout)
    if len(prediction_campaign_mini_smoke_payload["scheduleRows"]) != 3:
        raise AssertionError("CLI prediction-campaign mini smoke should expose three schedule rows")
    if prediction_campaign_mini_smoke_payload["scheduleRows"][-1]["runId"] != "predictionrun-1303":
        raise AssertionError("CLI prediction-campaign mini smoke final run drifted")
    prediction_campaign_full_next_due = run_cli(
        "prediction-campaign",
        "start",
        "--now",
        "2026-09-18T00:00:00Z",
        "--count",
        "100",
        "--full-materialization",
        "--watch",
        "--max-ticks",
        "1",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_full_next_due_payload = json.loads(prediction_campaign_full_next_due.stdout)
    if prediction_campaign_full_next_due_payload["ticks"][0]["readyRunId"] != "predictionrun-1400":
        raise AssertionError("CLI prediction-campaign full materialized scheduling run drifted")
    if len(prediction_campaign_full_next_due_payload["ticks"][0]["actions"]) != 100:
        raise AssertionError("CLI prediction-campaign full materialized tick should inspect 100 actions")
    if prediction_campaign_full_next_due_payload["executionBoundary"]["writesCampaignState"] is not False:
        raise AssertionError("CLI prediction-campaign full materialized dry-run must not write campaign state")
    prediction_campaign_start_flags = run_cli(
        "prediction-campaign",
        "start",
        "--domain",
        "weather-transit-delays",
        "--service-window",
        "morning_peak",
        "--interval",
        "P1D",
        "--count",
        "100",
        "--live-weather",
        "--execute-resolvers",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_start_flags_payload = json.loads(prediction_campaign_start_flags.stdout)
    if prediction_campaign_start_flags_payload["executionBoundary"]["fetchesLiveData"] is not False:
        raise AssertionError("CLI prediction-campaign start flags must remain dry-run non-fetching")
    if prediction_campaign_start_flags_payload["campaignCreationRequest"]["inputMode"] != "flag_overrides":
        raise AssertionError("CLI prediction-campaign start flags should be reflected as overrides")
    if prediction_campaign_start_flags_payload["campaignCreationRequest"]["targetCount"] != "100":
        raise AssertionError("CLI prediction-campaign start flag count drifted")
    if prediction_campaign_start_flags_payload["campaignCreationRequest"]["liveWeatherRequested"] is not True:
        raise AssertionError("CLI prediction-campaign start should record explicit live weather requests")
    if prediction_campaign_start_flags_payload["campaignCreationRequest"]["resolverExecutionRequested"] is not True:
        raise AssertionError("CLI prediction-campaign start should record explicit resolver requests")
    prediction_campaign_start_pre_calibration = run_cli(
        "prediction-campaign",
        "start",
        "--pre-calibrate",
        "--view",
        "pre-calibration",
    )
    prediction_campaign_start_pre_calibration_payload = json.loads(prediction_campaign_start_pre_calibration.stdout)
    if prediction_campaign_start_pre_calibration_payload["requestStatus"] != "requested":
        raise AssertionError("CLI prediction-campaign start should expose requested pre-calibration")
    if prediction_campaign_start_pre_calibration_payload["preCalibrationStatus"] != "ready":
        raise AssertionError("CLI prediction-campaign start pre-calibration should be ready")
    if prediction_campaign_start_pre_calibration_payload["calibratedProbability"] != 0.25:
        raise AssertionError("CLI prediction-campaign start pre-calibration probability drifted")
    prediction_campaign_setup_json = run_cli(
        "prediction-campaign",
        "start",
        "--setup-json",
        "spec/fixtures/generated/repeating-prediction-setup/ope-repeating-prediction-setup.generated.json",
        "--view",
        "campaign-creation",
    )
    prediction_campaign_setup_json_payload = json.loads(prediction_campaign_setup_json.stdout)
    if prediction_campaign_setup_json_payload["inputMode"] != "setup_json":
        raise AssertionError("CLI prediction-campaign start should accept setup JSON")
    if prediction_campaign_setup_json_payload["acceptedForDryRun"] is not True:
        raise AssertionError("CLI prediction-campaign setup JSON should be accepted for dry-run")
    prediction_campaign_start_check = run_cli("prediction-campaign", "start", "--check")
    if "checked prediction campaign runner" not in prediction_campaign_start_check.stdout:
        raise AssertionError("CLI prediction-campaign start check output drifted")
    prediction_campaign_forecast_create = run_cli("prediction-campaign", "forecast-create")
    prediction_campaign_forecast_create_payload = json.loads(prediction_campaign_forecast_create.stdout)
    if prediction_campaign_forecast_create_payload["creationStatus"] != "ready_dry_run_creation_request":
        raise AssertionError("CLI prediction-campaign forecast-create status drifted")
    if prediction_campaign_forecast_create_payload["readyRun"]["runId"] != "predictionrun-1301":
        raise AssertionError("CLI prediction-campaign forecast-create run drifted")
    if prediction_campaign_forecast_create_payload["summary"]["effectfulForecastCreationImplemented"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-create must not create forecasts yet")
    if prediction_campaign_forecast_create_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-create must remain non-mutating")
    prediction_campaign_forecast_create_flags = run_cli(
        "prediction-campaign",
        "forecast-create",
        "--run-id",
        "predictionrun-1301",
        "--live-weather",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_forecast_create_flags_payload = json.loads(prediction_campaign_forecast_create_flags.stdout)
    if prediction_campaign_forecast_create_flags_payload["executionBoundary"]["fetchesLiveData"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-create flags must remain dry-run non-fetching")
    prediction_campaign_forecast_create_check = run_cli("prediction-campaign", "forecast-create", "--check")
    if "checked prediction campaign forecast creation" not in prediction_campaign_forecast_create_check.stdout:
        raise AssertionError("CLI prediction-campaign forecast-create check output drifted")
    prediction_campaign_forecast_artifact = run_cli("prediction-campaign", "forecast-artifact")
    prediction_campaign_forecast_artifact_payload = json.loads(prediction_campaign_forecast_artifact.stdout)
    if prediction_campaign_forecast_artifact_payload["forecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-campaign forecast-artifact forecast ID drifted")
    if prediction_campaign_forecast_artifact_payload["questionId"] != "question-1301":
        raise AssertionError("CLI prediction-campaign forecast-artifact question ID drifted")
    if (
        prediction_campaign_forecast_artifact_payload["forecastOutput"]
        != prediction_campaign_forecast_artifact_payload["baselineForecast"]
    ):
        raise AssertionError("CLI prediction-campaign forecast-artifact must remain baseline-only")
    prediction_campaign_forecast_artifact_flags = run_cli(
        "prediction-campaign",
        "forecast-artifact",
        "--live-weather",
        "--execute-resolvers",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_forecast_artifact_flags_payload = json.loads(prediction_campaign_forecast_artifact_flags.stdout)
    if prediction_campaign_forecast_artifact_flags_payload["forecastOutput"]["probability"] != 0.25:
        raise AssertionError("CLI prediction-campaign forecast-artifact flags must remain checked fixture-only")
    prediction_campaign_forecast_artifact_check = run_cli("prediction-campaign", "forecast-artifact", "--check")
    if "checked prediction campaign forecast artifact" not in prediction_campaign_forecast_artifact_check.stdout:
        raise AssertionError("CLI prediction-campaign forecast-artifact check output drifted")
    prediction_campaign_forecast_write = run_cli("prediction-campaign", "forecast-write")
    prediction_campaign_forecast_write_payload = json.loads(prediction_campaign_forecast_write.stdout)
    if prediction_campaign_forecast_write_payload["writeStatus"] != "ready_for_explicit_local_write":
        raise AssertionError("CLI prediction-campaign forecast-write status drifted")
    if prediction_campaign_forecast_write_payload["bindings"]["forecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-campaign forecast-write forecast binding drifted")
    if prediction_campaign_forecast_write_payload["summary"]["effectfulLocalWriteImplemented"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-write must remain non-mutating")
    if prediction_campaign_forecast_write_payload["executionBoundary"]["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-write must not write ignored live state")
    prediction_campaign_forecast_write_flags = run_cli(
        "prediction-campaign",
        "forecast-write",
        "--run-id",
        "predictionrun-1301",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_forecast_write_flags_payload = json.loads(prediction_campaign_forecast_write_flags.stdout)
    if prediction_campaign_forecast_write_flags_payload["commandSurface"]["normalChecksExecuteWrite"] is not False:
        raise AssertionError("CLI prediction-campaign forecast-write flags must remain checked non-mutating")
    prediction_campaign_forecast_write_check = run_cli("prediction-campaign", "forecast-write", "--check")
    if "checked prediction campaign forecast write" not in prediction_campaign_forecast_write_check.stdout:
        raise AssertionError("CLI prediction-campaign forecast-write check output drifted")
    prediction_campaign_resolution_attempt = run_cli("prediction-campaign", "resolve")
    prediction_campaign_resolution_attempt_payload = json.loads(prediction_campaign_resolution_attempt.stdout)
    if prediction_campaign_resolution_attempt_payload["attemptStatus"] != "dry_run_due_ready":
        raise AssertionError("CLI prediction-campaign resolve status drifted")
    if prediction_campaign_resolution_attempt_payload["bindings"]["forecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-campaign resolve forecast binding drifted")
    if prediction_campaign_resolution_attempt_payload["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("CLI prediction-campaign resolve must not execute resolvers by default")
    prediction_campaign_resolution_execute = run_cli(
        "prediction-campaign",
        "resolve",
        "--run-id",
        "predictionrun-1301",
        "--execute-resolvers",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_resolution_execute_payload = json.loads(prediction_campaign_resolution_execute.stdout)
    if prediction_campaign_resolution_execute_payload["attemptStatus"] != "blocked_missing_outcome_source":
        raise AssertionError("CLI prediction-campaign resolve explicit execution should block on missing outcome source")
    if prediction_campaign_resolution_execute_payload["attemptResult"]["failureCategory"] != "source_unavailable":
        raise AssertionError("CLI prediction-campaign resolve failure category drifted")
    prediction_campaign_resolution_source_ready = run_cli(
        "prediction-campaign",
        "resolve",
        "--run-id",
        "predictionrun-1301",
        "--execute-resolvers",
        "--outcome-csv",
        ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_resolution_source_ready_payload = json.loads(prediction_campaign_resolution_source_ready.stdout)
    if prediction_campaign_resolution_source_ready_payload["attemptStatus"] != "dry_run_execute_ready":
        raise AssertionError("CLI prediction-campaign resolve should be ready when an outcome source is declared")
    if prediction_campaign_resolution_source_ready_payload["summary"]["resolutionArtifactsCreated"] is not False:
        raise AssertionError("CLI prediction-campaign resolve source-ready readback must remain non-mutating")
    prediction_campaign_resolution_duplicate = run_cli(
        "prediction-campaign",
        "resolve",
        "--attempt-case",
        "blocked_duplicate",
        "--execute-resolvers",
        "--output-format",
        "jsonl",
    )
    prediction_campaign_resolution_duplicate_payload = json.loads(prediction_campaign_resolution_duplicate.stdout)
    if prediction_campaign_resolution_duplicate_payload["attemptStatus"] != "blocked_duplicate_run":
        raise AssertionError("CLI prediction-campaign resolve duplicate case should block")
    if prediction_campaign_resolution_duplicate_payload["attemptResult"]["failureCategory"] != "duplicate_blocked":
        raise AssertionError("CLI prediction-campaign resolve duplicate failure category drifted")
    if prediction_campaign_resolution_duplicate_payload["duplicateSafety"]["duplicateScoringBlocked"] is not True:
        raise AssertionError("CLI prediction-campaign resolve duplicate safety should block duplicate scoring")
    prediction_campaign_resolution_attempt_check = run_cli("prediction-campaign", "resolve", "--check")
    if "checked prediction campaign resolution attempt" not in prediction_campaign_resolution_attempt_check.stdout:
        raise AssertionError("CLI prediction-campaign resolve check output drifted")
    prediction_campaign_doctor = run_cli("prediction-campaign", "doctor")
    prediction_campaign_doctor_payload = json.loads(prediction_campaign_doctor.stdout)
    if prediction_campaign_doctor_payload["doctorStatus"] != "actionable_due_run":
        raise AssertionError("CLI prediction-campaign doctor status drifted")
    if prediction_campaign_doctor_payload["health"]["dueRunCount"] != 1:
        raise AssertionError("CLI prediction-campaign doctor should expose one due run")
    if prediction_campaign_doctor_payload["health"]["blockedRunCount"] != 1:
        raise AssertionError("CLI prediction-campaign doctor should expose the blocked resolver path")
    if prediction_campaign_doctor_payload["duplicateProtection"]["priorEvidenceOverwriteAllowed"] is not False:
        raise AssertionError("CLI prediction-campaign doctor must block prior-evidence overwrite")
    if prediction_campaign_doctor_payload["executionBoundary"]["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign doctor must not write ignored state")
    prediction_campaign_doctor_waiting = run_cli(
        "prediction-campaign",
        "doctor",
        "--now",
        "2026-06-11T07:14:59Z",
        "--view",
        "health",
    )
    prediction_campaign_doctor_waiting_payload = json.loads(prediction_campaign_doctor_waiting.stdout)
    if prediction_campaign_doctor_waiting_payload["waitingRunCount"] != 1:
        raise AssertionError("CLI prediction-campaign doctor waiting view drifted")
    run_optional_drift_check(
        "prediction-campaign",
        "doctor",
        "--check",
        expected_stdout="checked prediction campaign doctor",
        label="prediction-campaign doctor",
    )
    prediction_campaign_resume = run_cli("prediction-campaign", "resume")
    prediction_campaign_resume_payload = json.loads(prediction_campaign_resume.stdout)
    if prediction_campaign_resume_payload["resumeStatus"] != "checked_resume_plan_non_mutating":
        raise AssertionError("CLI prediction-campaign resume status drifted")
    if prediction_campaign_resume_payload["bindings"]["forecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-campaign resume forecast binding drifted")
    if prediction_campaign_resume_payload["summary"]["effectfulResumeImplemented"] is not False:
        raise AssertionError("CLI prediction-campaign resume must remain non-effectful")
    if prediction_campaign_resume_payload["executionBoundary"]["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign resume must not write ignored live state")
    prediction_campaign_interrupted_resume = run_cli(
        "prediction-campaign",
        "resume",
        "--resume-case",
        "interrupted_after_forecast_write",
        "--view",
        "state",
    )
    prediction_campaign_interrupted_resume_payload = json.loads(prediction_campaign_interrupted_resume.stdout)
    if prediction_campaign_interrupted_resume_payload["sourceKind"] != "simulated_interrupted_campaign_state":
        raise AssertionError("CLI prediction-campaign interrupted resume source kind drifted")
    if prediction_campaign_interrupted_resume_payload["localRunStateCount"] != 1:
        raise AssertionError("CLI prediction-campaign interrupted resume should find one local run state")
    if prediction_campaign_interrupted_resume_payload["priorEvidenceOverwriteAllowed"] is not False:
        raise AssertionError("CLI prediction-campaign interrupted resume must not allow overwrite")
    prediction_campaign_resume_check = run_cli("prediction-campaign", "resume", "--check")
    if "checked prediction campaign resume" not in prediction_campaign_resume_check.stdout:
        raise AssertionError("CLI prediction-campaign resume check output drifted")
    prediction_campaign_append_ready = run_cli("prediction-campaign", "append-ready")
    prediction_campaign_append_ready_payload = json.loads(prediction_campaign_append_ready.stdout)
    if prediction_campaign_append_ready_payload["ledgerStatus"] != "checked_exclusion_append_ready":
        raise AssertionError("CLI prediction-campaign append-ready status drifted")
    if prediction_campaign_append_ready_payload["summary"]["excludedRowCount"] != 1:
        raise AssertionError("CLI prediction-campaign append-ready excluded row count drifted")
    if prediction_campaign_append_ready_payload["executionBoundary"]["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign append-ready must not write ignored state")
    prediction_campaign_append_comparable = run_cli(
        "prediction-campaign",
        "append",
        "--ledger-case",
        "comparable_scored",
        "--view",
        "summary",
    )
    prediction_campaign_append_comparable_payload = json.loads(prediction_campaign_append_comparable.stdout)
    if prediction_campaign_append_comparable_payload["comparableRowCount"] != 1:
        raise AssertionError("CLI prediction-campaign append comparable row count drifted")
    if prediction_campaign_append_comparable_payload["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign append dry run must not write ignored state")
    prediction_campaign_ledger_check = run_cli("prediction-campaign", "append-ready", "--check")
    if "checked prediction campaign evidence ledger" not in prediction_campaign_ledger_check.stdout:
        raise AssertionError("CLI prediction-campaign evidence ledger check output drifted")
    prediction_campaign_calibration = run_cli("prediction-campaign", "calibration-status")
    prediction_campaign_calibration_payload = json.loads(prediction_campaign_calibration.stdout)
    if prediction_campaign_calibration_payload["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("CLI prediction-campaign calibration-status default drifted")
    if prediction_campaign_calibration_payload["calibrationReadback"]["summaryGenerated"]:
        raise AssertionError("CLI prediction-campaign calibration-status must not summarize below threshold")
    prediction_campaign_calibration_threshold = run_cli(
        "prediction-campaign",
        "calibration-status",
        "--calibration-case",
        "threshold_met",
        "--view",
        "readback",
    )
    prediction_campaign_calibration_threshold_payload = json.loads(prediction_campaign_calibration_threshold.stdout)
    if prediction_campaign_calibration_threshold_payload["summaryGenerated"] is not True:
        raise AssertionError("CLI prediction-campaign calibration threshold case should generate a summary")
    if prediction_campaign_calibration_threshold_payload["automaticMethodChangeAllowed"]:
        raise AssertionError("CLI prediction-campaign calibration must not allow automatic method changes")
    prediction_campaign_calibration_restart = run_cli(
        "prediction-campaign",
        "calibration-status",
        "--calibration-case",
        "post_calibration_restart",
        "--view",
        "cycle",
    )
    prediction_campaign_calibration_restart_payload = json.loads(prediction_campaign_calibration_restart.stdout)
    if prediction_campaign_calibration_restart_payload["postCalibrationAction"] != "pause_then_resume_after":
        raise AssertionError("CLI prediction-campaign calibration restart action drifted")
    prediction_campaign_calibration_check = run_cli("prediction-campaign", "calibration-status", "--check")
    if "checked prediction campaign calibration status" not in prediction_campaign_calibration_check.stdout:
        raise AssertionError("CLI prediction-campaign calibration status check output drifted")
    prediction_campaign_pre_calibration = run_cli("prediction-campaign", "pre-calibration")
    prediction_campaign_pre_calibration_payload = json.loads(prediction_campaign_pre_calibration.stdout)
    if prediction_campaign_pre_calibration_payload["preCalibrationStatus"] != "ready":
        raise AssertionError("CLI prediction-campaign pre-calibration status drifted")
    if prediction_campaign_pre_calibration_payload["calibrationMethod"]["calibratedProbability"] != 0.25:
        raise AssertionError("CLI prediction-campaign pre-calibration probability drifted")
    if prediction_campaign_pre_calibration_payload["executionBoundary"]["writesIgnoredLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign pre-calibration must not write by default")
    prediction_campaign_pre_calibration_method = run_cli(
        "prediction-campaign",
        "pre-calibration",
        "--view",
        "method",
    )
    prediction_campaign_pre_calibration_method_payload = json.loads(prediction_campaign_pre_calibration_method.stdout)
    if prediction_campaign_pre_calibration_method_payload["positiveOutcomeCount"] != 7:
        raise AssertionError("CLI prediction-campaign pre-calibration positive count drifted")
    prediction_campaign_pre_calibration_check = run_cli("prediction-campaign", "pre-calibration", "--check")
    if "checked prediction campaign pre-calibration" not in prediction_campaign_pre_calibration_check.stdout:
        raise AssertionError("CLI prediction-campaign pre-calibration check output drifted")
    prediction_campaign_method_gate = run_cli("prediction-campaign", "method-update-gate")
    prediction_campaign_method_gate_payload = json.loads(prediction_campaign_method_gate.stdout)
    if prediction_campaign_method_gate_payload["gateStatus"] != "blocked_insufficient_calibration_evidence":
        raise AssertionError("CLI prediction-campaign method-update gate default drifted")
    if prediction_campaign_method_gate_payload["decision"]["methodUpdatePlanReady"]:
        raise AssertionError("CLI prediction-campaign method-update gate must not be plan-ready below threshold")
    if prediction_campaign_method_gate_payload["executionBoundary"]["changesForecastMethod"]:
        raise AssertionError("CLI prediction-campaign method-update gate must not change methods")
    prediction_campaign_method_gate_approved = run_cli(
        "prediction-campaign",
        "method-update-gate",
        "--method-update-case",
        "approved_plan_ready",
        "--view",
        "decision",
    )
    prediction_campaign_method_gate_approved_payload = json.loads(prediction_campaign_method_gate_approved.stdout)
    if prediction_campaign_method_gate_approved_payload["methodUpdatePlanReady"] is not True:
        raise AssertionError("CLI prediction-campaign method-update approved case should be plan-ready")
    if prediction_campaign_method_gate_approved_payload["effectfulUpdateAllowedNow"]:
        raise AssertionError("CLI prediction-campaign method-update gate must remain non-effectful")
    prediction_campaign_method_gate_check = run_cli("prediction-campaign", "method-update-gate", "--check")
    if "checked prediction campaign method update gate" not in prediction_campaign_method_gate_check.stdout:
        raise AssertionError("CLI prediction-campaign method-update gate check output drifted")
    prediction_campaign_method_plan = run_cli("prediction-campaign", "method-update-plan")
    prediction_campaign_method_plan_payload = json.loads(prediction_campaign_method_plan.stdout)
    if prediction_campaign_method_plan_payload["planStatus"] != "blocked_by_method_update_gate":
        raise AssertionError("CLI prediction-campaign method-update plan default drifted")
    if prediction_campaign_method_plan_payload["decision"]["methodUpdatePlanReady"]:
        raise AssertionError("CLI prediction-campaign method-update plan must not be ready when gate-blocked")
    if prediction_campaign_method_plan_payload["executionBoundary"]["writesPlanArtifact"]:
        raise AssertionError("CLI prediction-campaign method-update plan must not write plan artifacts")
    prediction_campaign_method_plan_ready = run_cli(
        "prediction-campaign",
        "method-update-plan",
        "--method-update-plan-case",
        "plan_ready",
        "--view",
        "command",
    )
    prediction_campaign_method_plan_ready_payload = json.loads(prediction_campaign_method_plan_ready.stdout)
    if not prediction_campaign_method_plan_ready_payload["implementedNow"]:
        raise AssertionError("CLI prediction-campaign method-update plan should expose the implemented explicit command")
    if prediction_campaign_method_plan_ready_payload["normalChecksMayRun"]:
        raise AssertionError("CLI prediction-campaign method-update plan future command must stay out of normal checks")
    prediction_campaign_method_plan_check = run_cli("prediction-campaign", "method-update-plan", "--check")
    if "checked prediction campaign method update plan" not in prediction_campaign_method_plan_check.stdout:
        raise AssertionError("CLI prediction-campaign method-update plan check output drifted")
    prediction_campaign_method_apply = run_cli("prediction-campaign", "apply-method-update")
    prediction_campaign_method_apply_payload = json.loads(prediction_campaign_method_apply.stdout)
    if prediction_campaign_method_apply_payload["actionStatus"] != "blocked_by_method_update_plan":
        raise AssertionError("CLI prediction-campaign method-update apply default drifted")
    if prediction_campaign_method_apply_payload["executionBoundary"]["writesMethodBinding"]:
        raise AssertionError("CLI prediction-campaign method-update apply default must not write bindings")
    prediction_campaign_method_apply_ready = run_cli(
        "prediction-campaign",
        "apply-method-update",
        "--method-update-plan-case",
        "plan_ready",
        "--view",
        "summary",
    )
    prediction_campaign_method_apply_ready_payload = json.loads(prediction_campaign_method_apply_ready.stdout)
    if prediction_campaign_method_apply_ready_payload["localWriteEligible"] is not True:
        raise AssertionError("CLI prediction-campaign method-update apply should be eligible when plan-ready")
    if prediction_campaign_method_apply_ready_payload["targetMethodId"] != "transitmethod-101":
        raise AssertionError("CLI prediction-campaign method-update apply target drifted")
    prediction_campaign_method_rollback_ready = run_cli(
        "prediction-campaign",
        "rollback-method-update",
        "--method-update-plan-case",
        "plan_ready",
        "--view",
        "summary",
    )
    prediction_campaign_method_rollback_ready_payload = json.loads(prediction_campaign_method_rollback_ready.stdout)
    if prediction_campaign_method_rollback_ready_payload["targetMethodId"] != "transitmethod-100":
        raise AssertionError("CLI prediction-campaign method-update rollback target drifted")
    prediction_campaign_method_action_check = run_cli("prediction-campaign", "apply-method-update", "--check")
    if "checked prediction campaign method update action" not in prediction_campaign_method_action_check.stdout:
        raise AssertionError("CLI prediction-campaign method-update action check output drifted")
    prediction_campaign_explain = run_cli("prediction-campaign", "explain")
    prediction_campaign_explain_payload = json.loads(prediction_campaign_explain.stdout)
    if prediction_campaign_explain_payload["campaignSnapshot"]["nextForecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-campaign explain next forecast drifted")
    if prediction_campaign_explain_payload["summary"]["agentAdapterReadbacksImplemented"] is not True:
        raise AssertionError("CLI prediction-campaign explain should expose agent adapter readbacks")
    run_optional_drift_check(
        "prediction-campaign",
        "explain",
        "--check",
        expected_stdout="checked prediction campaign explain",
        label="prediction-campaign explain",
    )
    prediction_campaign_pilot_runbook = run_cli("prediction-campaign", "pilot-runbook")
    prediction_campaign_pilot_runbook_payload = json.loads(prediction_campaign_pilot_runbook.stdout)
    if prediction_campaign_pilot_runbook_payload["pilotScope"]["targetRunCount"] != 100:
        raise AssertionError("CLI prediction-campaign pilot runbook target drifted")
    if prediction_campaign_pilot_runbook_payload["summary"]["bestAvailableMethodId"] != "transitmethod-100":
        raise AssertionError("CLI prediction-campaign pilot runbook best method drifted")
    if prediction_campaign_pilot_runbook_payload["executionBoundary"]["normalChecksWriteLiveState"] is not False:
        raise AssertionError("CLI prediction-campaign pilot runbook must not write local state")
    prediction_campaign_pilot_status = run_cli("prediction-campaign", "pilot-runbook", "--view", "operator-status")
    prediction_campaign_pilot_status_payload = json.loads(prediction_campaign_pilot_status.stdout)
    if prediction_campaign_pilot_status_payload["calibrationThreshold"] != 100:
        raise AssertionError("CLI prediction-campaign pilot status calibration threshold drifted")
    if len(prediction_campaign_pilot_status_payload["statusCommands"]) != 7:
        raise AssertionError("CLI prediction-campaign pilot status command count drifted")
    prediction_campaign_pilot_smoke = run_cli("prediction-campaign", "pilot-runbook", "--view", "smoke")
    prediction_campaign_pilot_smoke_payload = json.loads(prediction_campaign_pilot_smoke.stdout)
    if prediction_campaign_pilot_smoke_payload["expectedRunIds"][-1] != "predictionrun-1303":
        raise AssertionError("CLI prediction-campaign pilot smoke final run drifted")
    run_optional_drift_check(
        "prediction-campaign",
        "pilot-runbook",
        "--check",
        expected_stdout="checked Helsinki traffic pilot runbook",
        label="prediction-campaign pilot-runbook",
    )
    prediction_campaign_pilot_readiness = run_cli("prediction-campaign", "pilot-readiness")
    prediction_campaign_pilot_readiness_payload = json.loads(prediction_campaign_pilot_readiness.stdout)
    if prediction_campaign_pilot_readiness_payload["readinessSummary"]["targetRunCount"] != 100:
        raise AssertionError("CLI prediction-campaign pilot readiness target drifted")
    if prediction_campaign_pilot_readiness_payload["summary"]["checkedPrerequisitesPassed"] is not True:
        raise AssertionError("CLI prediction-campaign pilot readiness checked prerequisites should pass")
    if prediction_campaign_pilot_readiness_payload["executionBoundary"]["startsPilot"] is not False:
        raise AssertionError("CLI prediction-campaign pilot readiness must not start the pilot")
    prediction_campaign_pilot_readiness_commands = run_cli(
        "prediction-campaign",
        "pilot-readiness",
        "--view",
        "commands",
    )
    prediction_campaign_pilot_readiness_commands_payload = json.loads(prediction_campaign_pilot_readiness_commands.stdout)
    if prediction_campaign_pilot_readiness_commands_payload[4]["commandKey"] != "launch_first_write":
        raise AssertionError("CLI prediction-campaign pilot readiness launch command drifted")
    if "--pre-calibrate" not in prediction_campaign_pilot_readiness_commands_payload[4]["command"]:
        raise AssertionError("CLI prediction-campaign pilot readiness launch should include pre-calibration")
    run_optional_drift_check(
        "prediction-campaign",
        "pilot-readiness",
        "--check",
        expected_stdout="checked Helsinki traffic pilot readiness",
        label="prediction-campaign pilot-readiness",
    )
    run_optional_drift_check(
        "private-setup-adapter-runbook",
        "--check",
        expected_stdout="checked private setup adapter-chain runbook",
        label="private-setup-adapter-runbook",
    )
    run_optional_drift_check(
        "private-setup-adapter-conformance",
        "--check",
        expected_stdout="checked private setup adapter conformance matrix",
        label="private-setup-adapter-conformance",
    )
    run_optional_drift_check(
        "private-setup-adapter-conformance-summary",
        "--check",
        expected_stdout="checked private setup adapter conformance summary",
        label="private-setup-adapter-conformance-summary",
    )
    run_optional_drift_check(
        "private-source-kind-selection",
        "--check",
        expected_stdout="checked private source-kind selection examples",
        label="private-source-kind-selection",
    )
    run_optional_drift_check(
        "private-source-kind-query-matrix",
        "--check",
        expected_stdout="checked private source-kind query matrix",
        label="private-source-kind-query-matrix",
    )
    run_cli("recalculation", "--check")
    run_cli("forecast-run", "--check")
    run_cli("forecast-run-matrix", "--check")
    run_cli("forecast-runbook", "--check")
    run_optional_drift_check(
        "agent-envelopes",
        "--check",
        expected_stdout="checked 56 agent adapter envelopes",
        label="agent-envelopes",
    )
    run_optional_drift_check(
        "agent-protocol-map",
        "--check",
        expected_stdout="checked agent adapter protocol map",
        label="agent-protocol-map",
    )
    run_cli("pipeline")
    run_cli("resolve-pipeline")
    run_cli("manifest")

    artifact = run_cli(
        "read",
        "--record-type",
        "forecast-artifact",
        "--id",
        "forecast-101",
        "--question-id",
        "question-101",
    )
    artifact_payload = json.loads(artifact.stdout)
    if artifact_payload["record"]["forecastId"] != "forecast-101":
        raise AssertionError("CLI read returned wrong artifact")

    bundle = run_cli(
        "read",
        "--record-type",
        "forecast-bundle",
        "--id",
        "forecast-502",
        "--question-id",
        "question-501",
    )
    bundle_payload = json.loads(bundle.stdout)
    if bundle_payload["record"]["includedRecords"]["scoringReport"] != "scoring-501":
        raise AssertionError("CLI read returned wrong forecast bundle")

    card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-502",
        "--question-id",
        "question-501",
    )
    card_payload = json.loads(card.stdout)
    if card_payload["record"]["qualityClaim"]["status"] != "not_enough_resolved_pipeline_outcomes":
        raise AssertionError("CLI read returned wrong forecast card")

    historical_card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-702",
        "--question-id",
        "question-701",
    )
    historical_card_payload = json.loads(historical_card.stdout)
    if historical_card_payload["record"]["forecast"]["probability"] != 0.22:
        raise AssertionError("CLI read returned wrong historical baseline forecast card")
    if historical_card_payload["record"]["links"]["evidenceTrace"] is not None:
        raise AssertionError("historical baseline forecast card should not link evidence trace")

    setup_card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-901",
        "--question-id",
        "question-901",
    )
    setup_card_payload = json.loads(setup_card.stdout)
    setup_binding = setup_card_payload["record"]["setupBinding"]
    if setup_binding["setupForecastRunId"] != "setupforecastrun-901":
        raise AssertionError("CLI read missed setup forecast run binding")
    if setup_binding["setupBenchmarkGateId"] != "setupbenchmarkgate-001":
        raise AssertionError("CLI setup forecast card should expose setup benchmark gate")
    if setup_binding["selectedMethodClass"] != "deterministic_statistical":
        raise AssertionError("CLI setup forecast card should expose selected deterministic method")
    if setup_card_payload["record"]["forecast"]["probability"] <= setup_card_payload["record"]["baseline"]["probability"]:
        raise AssertionError("CLI setup forecast card should expose non-baseline deterministic probability")
    if setup_card_payload["record"]["links"]["evidenceTrace"] is not None:
        raise AssertionError("setup forecast card should not link evidence trace")

    source_handoff_card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    source_handoff_card_payload = json.loads(source_handoff_card.stdout)
    source_handoff_binding = source_handoff_card_payload["record"]["setupBinding"]
    if source_handoff_binding["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("CLI source-handoff forecast card should expose setup run")
    if source_handoff_binding["sourceIntakeHandoffId"] != "sourceintakehandoff-002":
        raise AssertionError("CLI source-handoff forecast card should expose handoff binding")
    if source_handoff_binding["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("CLI source-handoff forecast card should expose method gate binding")
    if source_handoff_binding["setupBenchmarkGateId"] != "setupbenchmarkgate-102":
        raise AssertionError("CLI source-handoff forecast card should expose handoff benchmark gate")
    if source_handoff_card_payload["record"]["forecast"]["probability"] <= source_handoff_card_payload["record"]["baseline"]["probability"]:
        raise AssertionError("CLI source-handoff forecast card should expose deterministic probability")
    if source_handoff_card_payload["record"]["links"]["evidenceTrace"] is not None:
        raise AssertionError("source-handoff forecast card should not link evidence trace")

    evidence_trace = run_cli(
        "read",
        "--record-type",
        "evidence-trace",
        "--id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    evidence_trace_payload = json.loads(evidence_trace.stdout)
    trace_record = evidence_trace_payload["record"]
    if trace_record["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("CLI read returned wrong evidence trace connector result-set binding")
    if trace_record["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("CLI evidence trace must not claim all evidence coverage")

    source_set = run_cli(
        "read",
        "--record-type",
        "evidence-source-set",
        "--id",
        "evidencesourceset-019",
    )
    source_set_payload = json.loads(source_set.stdout)
    if source_set_payload["record"]["sourceConnectorRegistryId"] != "sourceconnectorregistry-001":
        raise AssertionError("CLI read should expose evidence source-set connector registry binding")

    connector_results_read = run_cli(
        "read",
        "--record-type",
        "source-connector-results",
        "--id",
        "sourceconnectorresults-001",
    )
    connector_results_read_payload = json.loads(connector_results_read.stdout)
    if connector_results_read_payload["record"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("CLI read should expose source connector result set")

    listed = run_cli("list", "--record-type", "forecast-artifact", "--domain", "weather-logistics")
    listed_payload = json.loads(listed.stdout)
    if listed_payload["count"] < 1:
        raise AssertionError("CLI list returned no weather-logistics artifacts")

    decision = run_cli(
        "request",
        "--input",
        "spec/fixtures/requests/valid-weather-logistics-request.json",
    )
    decision_payload = json.loads(decision.stdout)
    if decision_payload["decisionStatus"] != "accepted":
        raise AssertionError("CLI request validation returned wrong decision")

    auto_decision = run_cli(
        "request",
        "--input",
        "spec/fixtures/requests/auto-weather-logistics-request.json",
    )
    auto_decision_payload = json.loads(auto_decision.stdout)
    if auto_decision_payload["decisionStatus"] != "accepted":
        raise AssertionError("CLI auto request validation returned wrong decision")

    evidence_plan = run_cli("evidence-plan")
    evidence_plan_payload = json.loads(evidence_plan.stdout)
    if evidence_plan_payload["planStatus"] != "planned":
        raise AssertionError("CLI evidence-plan returned wrong status")

    gathered = run_cli("gather-evidence")
    gathered_payload = json.loads(gathered.stdout)
    if gathered_payload["executionMode"] != "fixture_replay":
        raise AssertionError("CLI gather-evidence returned wrong execution mode")
    if gathered_payload["provenanceSummary"]["sourceCount"] != 2:
        raise AssertionError("CLI gather-evidence returned wrong source count")

    source_connectors = run_cli("source-connectors")
    source_connectors_payload = json.loads(source_connectors.stdout)
    connectors = {item["connectorKey"]: item for item in source_connectors_payload["connectors"]}
    if connectors["open_meteo_weather"]["policyBinding"]["allowedBySourcePolicy"] is not True:
        raise AssertionError("CLI source-connectors should allow Open-Meteo under source policy")
    if connectors["web_search"]["status"] != "unsupported":
        raise AssertionError("CLI source-connectors should keep web search unsupported")
    if connectors["market_price_feed"]["sourceClass"] != "market_price":
        raise AssertionError("CLI source-connectors should expose unsupported market_price source class")

    source_connector_results = run_cli("source-connectors", "--results")
    source_connector_results_payload = json.loads(source_connector_results.stdout)
    results = {item["connectorKey"]: item for item in source_connector_results_payload["connectorResults"]}
    if results["open_meteo_weather"]["resultStatus"] != "succeeded_fixture_replay":
        raise AssertionError("CLI source-connectors --results should include fixture weather result")
    if results["market_price_feed"]["normalizedFields"] is not None:
        raise AssertionError("CLI source-connectors --results should not normalize unsupported source classes")

    live_readiness = run_cli("live-readiness")
    live_readiness_payload = json.loads(live_readiness.stdout)
    if live_readiness_payload["readinessStatus"] != "ready_for_explicit_integration_check":
        raise AssertionError("CLI live-readiness should expose opt-in readiness")
    modes = live_readiness_payload["executionModes"]
    if modes["fixtureReplay"]["enabledInNormalChecks"] is not True:
        raise AssertionError("CLI live-readiness should keep fixture replay in normal checks")
    if modes["integrationLiveFetch"]["enabledInNormalChecks"] is not False:
        raise AssertionError("CLI live-readiness should keep integration live fetch out of normal checks")
    if modes["integrationLiveFetch"]["requiresExplicitFlag"] is not True:
        raise AssertionError("CLI live-readiness should require explicit live flag")
    if live_readiness_payload["networkBoundary"]["allowBroadWebSearch"] is not False:
        raise AssertionError("CLI live-readiness must not enable broad web search")
    if live_readiness_payload["claimBoundary"]["normalReleaseChecksOffline"] is not True:
        raise AssertionError("CLI live-readiness should preserve offline release checks")

    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / ".ope" / "live"
        result_set = build_live_result_set(
            readiness=build_readiness(),
            integration_result=fixture_integration_result(),
            generated_at="2026-06-02T09:40:00Z",
        )
        capture_path = save_live_result_set(
            result_set=result_set,
            workspace=workspace,
            location="warsaw",
            service_date="2026-06-03",
        )
        live_capture_check = run_cli("live-capture", "--input", str(capture_path), "--check")
        if "checked local live capture" not in live_capture_check.stdout:
            raise AssertionError("CLI live-capture should validate local live captures")
        live_draft = run_cli("live-capture", "--input", str(capture_path), "--draft-source-set")
        live_draft_payload = json.loads(live_draft.stdout)
        if live_draft_payload["executionMode"] != "live_fetch":
            raise AssertionError("CLI live-capture should build a live_fetch draft source set")
        if live_draft_payload["provenanceSummary"]["allEvidenceClaimed"] is not False:
            raise AssertionError("CLI live-capture draft must not claim all evidence")
        draft_path = Path(tmp) / ".ope" / "live" / "draft-source-set.json"
        run_cli(
            "live-capture",
            "--input",
            str(capture_path),
            "--draft-source-set",
            "--write",
            "--output",
            str(draft_path),
        )
        if not draft_path.exists():
            raise AssertionError("CLI live-capture --write should create a local draft")

    domain_setups = run_cli("domain-setups")
    domain_setups_payload = json.loads(domain_setups.stdout)
    if domain_setups_payload["count"] != 3:
        raise AssertionError("CLI domain-setups should expose three setup records")
    setup_summaries = {item["domain"]: item for item in domain_setups_payload["domainSetups"]}
    if setup_summaries["weather-logistics"]["maturityStatus"] != "fixture_ready":
        raise AssertionError("CLI domain-setups should expose weather-logistics as fixture-ready")
    if setup_summaries["seaport-berth-availability"]["maturityStatus"] != "candidate":
        raise AssertionError("CLI domain-setups should expose seaport setup as candidate")
    if setup_summaries["weather-transit-delays"]["forecastRunnable"] is not True:
        raise AssertionError("CLI domain-setups should expose transit delay setup as locally runnable")

    seaport_setup = run_cli("domain-setups", "--setup", "seaport-berth-availability")
    seaport_setup_payload = json.loads(seaport_setup.stdout)
    if seaport_setup_payload["localImplementation"]["forecastRunnable"] is not False:
        raise AssertionError("CLI candidate domain setup should not be forecast runnable")
    if seaport_setup_payload["claimPolicy"]["calibrationClaimAllowed"] is not False:
        raise AssertionError("CLI candidate domain setup should block calibration claims")
    if seaport_setup_payload["claimPolicy"]["productionReadinessClaimAllowed"] is not False:
        raise AssertionError("CLI candidate domain setup should block production readiness claims")

    transit_setup = run_cli("domain-setups", "--setup", "weather-transit-delays")
    transit_setup_payload = json.loads(transit_setup.stdout)
    if transit_setup_payload["localImplementation"]["forecastRunnable"] is not True:
        raise AssertionError("CLI transit domain setup should expose local forecast runnable")
    if transit_setup_payload["claimPolicy"]["calibrationClaimAllowed"] is not False:
        raise AssertionError("CLI transit domain setup should block calibration claims")

    domain_configs = run_cli("domain-configs")
    domain_configs_payload = json.loads(domain_configs.stdout)
    if domain_configs_payload["configCount"] != 2:
        raise AssertionError("CLI domain-configs should expose two config records")
    config_summaries = {item["domainKey"]: item for item in domain_configs_payload["domains"]}
    if config_summaries["weather-transit-delays"]["configStatus"] != "defined_readback":
        raise AssertionError("CLI domain-configs should expose transit config as defined")
    if config_summaries["seaport-berth-availability"]["configStatus"] != "candidate_readback":
        raise AssertionError("CLI domain-configs should expose seaport config as candidate")
    if config_summaries["seaport-berth-availability"]["credentialsExcluded"] is not True:
        raise AssertionError("CLI domain-configs should exclude credentials")

    transit_config = run_cli("domain-configs", "--domain", "weather-transit-delays")
    transit_config_payload = json.loads(transit_config.stdout)
    if transit_config_payload["baselineMethod"]["methodId"] != "transitmethod-100":
        raise AssertionError("CLI transit domain config baseline method drifted")
    if transit_config_payload["claimBoundaries"]["calibrationClaimAllowed"] is not False:
        raise AssertionError("CLI transit domain config should block calibration claims")
    transit_config_roles = {item["roleKey"]: item for item in transit_config_payload["acceptedSourceRoles"]}
    if transit_config_roles["transit_delay_outcome"]["forecastTimeAllowed"] is not False:
        raise AssertionError("CLI transit outcome role must be resolution-only")

    seaport_config = run_cli("domain-configs", "--domain", "seaport-berth-availability")
    seaport_config_payload = json.loads(seaport_config.stdout)
    seaport_config_roles = {item["roleKey"]: item for item in seaport_config_payload["acceptedSourceRoles"]}
    if "database" not in seaport_config_roles["vessel_schedule"]["acceptedSourceKinds"]:
        raise AssertionError("CLI seaport domain config should allow database adapters")
    if seaport_config_payload["executionBoundary"]["readsPrivateData"] is not False:
        raise AssertionError("CLI seaport domain config must not read private data")

    source_bindings = run_cli("source-bindings")
    source_bindings_payload = json.loads(source_bindings.stdout)
    if source_bindings_payload["bindingCaseCount"] != 4:
        raise AssertionError("CLI source-bindings should expose four setup cases")
    if {"api", "database", "local_file", "source_adapter_output"} - set(source_bindings_payload["approvedSourceKinds"]):
        raise AssertionError("CLI source-bindings should cover approved local file, adapter, API, and database sources")
    source_binding_cases = {
        item["bindingCase"]: item for item in source_bindings_payload["cases"]
    }
    if source_binding_cases["accepted"]["nextAction"] != "forecast_generation_allowed":
        raise AssertionError("CLI source-bindings accepted case should allow lifecycle forecast generation")
    if source_binding_cases["partial"]["nextAction"] != "collect_missing_source_binding":
        raise AssertionError("CLI source-bindings partial case should request missing source bindings")
    if source_binding_cases["rejected"]["nextAction"] != "replace_source_binding":
        raise AssertionError("CLI source-bindings rejected case should request replacement")
    if source_binding_cases["blocked"]["nextAction"] != "stop_unsafe_source_binding":
        raise AssertionError("CLI source-bindings blocked case should stop unsafe setup")
    if any(item["credentialValuesStored"] for item in source_binding_cases.values()):
        raise AssertionError("CLI source-bindings must not store credential values")
    source_binding_operations = {
        item["operationName"]: item for item in source_bindings_payload["setupOperations"]
    }
    if set(source_binding_operations) != {
        "source_binding.draft",
        "source_binding.validate",
        "source_binding.confirm",
        "source_binding.update",
        "source_binding.archive",
        "source_binding.redact",
    }:
        raise AssertionError("CLI source-bindings setup operation coverage drifted")
    if source_binding_operations["source_binding.archive"]["internalApiOperation"] != "archive_record":
        raise AssertionError("CLI source-bindings archive should map to internal archive operation")
    accepted_binding = run_cli("source-bindings", "--case", "accepted")
    accepted_binding_payload = json.loads(accepted_binding.stdout)
    if accepted_binding_payload["summary"]["forecastGenerationAllowed"] is not True:
        raise AssertionError("CLI source-bindings accepted case should allow forecast generation")
    if any(item["blocksForecast"] for item in accepted_binding_payload["preForecastChecks"]):
        raise AssertionError("CLI source-bindings accepted case should not expose forecast blockers")
    partial_binding = run_cli("source-bindings", "--case", "partial")
    partial_binding_payload = json.loads(partial_binding.stdout)
    if partial_binding_payload["summary"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("CLI source-bindings partial case should block forecast generation")
    if not any(item["bindingStatus"] == "missing" for item in partial_binding_payload["sourceRoleBindings"]):
        raise AssertionError("CLI source-bindings partial case should expose missing source role")
    rejected_binding = run_cli("source-bindings", "--case", "rejected")
    rejected_binding_payload = json.loads(rejected_binding.stdout)
    if rejected_binding_payload["nextAction"] != "replace_source_binding":
        raise AssertionError("CLI source-bindings rejected case should route to source replacement")
    blocked_binding = run_cli("source-bindings", "--case", "blocked")
    blocked_binding_payload = json.loads(blocked_binding.stdout)
    if blocked_binding_payload["credentialPolicy"]["rawCredentialValueDetected"] is not True:
        raise AssertionError("CLI source-bindings blocked case should detect raw credential-like input")
    if not all(item["blocksForecast"] for item in blocked_binding_payload["preForecastChecks"]):
        raise AssertionError("CLI source-bindings blocked case should block every pre-forecast check")

    domain_source_policy = run_cli("domain-source-field-policy")
    domain_source_policy_payload = json.loads(domain_source_policy.stdout)
    if domain_source_policy_payload["policyStatus"] != "domain_source_field_policy_checked":
        raise AssertionError("CLI domain-source-field-policy status drifted")
    if (
        domain_source_policy_payload["decisionStatus"]
        != "universal_domain_and_source_fields_with_domain_extension_boundary"
    ):
        raise AssertionError("CLI domain-source-field-policy decision status drifted")
    if domain_source_policy_payload["normalChecksMutateState"] is not False:
        raise AssertionError("CLI domain-source-field-policy must keep normal checks non-mutating")
    if domain_source_policy_payload["generatedRuntimeTypesIncluded"] is not False:
        raise AssertionError("CLI domain-source-field-policy must not generate runtime types")
    domain_source_summary = domain_source_policy_payload["summary"]
    expected_domain_source_counts = {
        "universalDomainFieldCount": 10,
        "universalSourceBindingFieldCount": 10,
        "domainSpecificExtensionFieldCount": 8,
        "blockedFieldCount": 6,
        "sourceKindRuleCount": 5,
        "fieldDecisionCaseCount": 7,
    }
    for key, expected in expected_domain_source_counts.items():
        if domain_source_summary[key] != expected:
            raise AssertionError(f"CLI domain-source-field-policy {key} drifted")
    domain_source_fields = run_cli("domain-source-field-policy", "--view", "domain-fields")
    domain_source_fields_payload = json.loads(domain_source_fields.stdout)
    if len(domain_source_fields_payload) != 10:
        raise AssertionError("CLI domain-source-field-policy should expose ten universal domain fields")
    if any(item["requirementLevel"] != "required_every_domain" for item in domain_source_fields_payload):
        raise AssertionError("CLI domain-source-field-policy domain fields should be required")
    if any(item["domainExtensionAllowed"] for item in domain_source_fields_payload):
        raise AssertionError("CLI domain-source-field-policy domain fields must not move to extensions")
    if any(item["credentialValuesAllowed"] or item["rawPrivateDataAllowed"] for item in domain_source_fields_payload):
        raise AssertionError("CLI domain-source-field-policy domain fields must block secrets and raw private data")
    domain_source_source_fields = run_cli("domain-source-field-policy", "--view", "source-fields")
    domain_source_source_fields_payload = json.loads(domain_source_source_fields.stdout)
    if len(domain_source_source_fields_payload) != 10:
        raise AssertionError("CLI domain-source-field-policy should expose ten universal source fields")
    if any(item["requirementLevel"] != "required_every_source_binding" for item in domain_source_source_fields_payload):
        raise AssertionError("CLI domain-source-field-policy source fields should be required")
    domain_source_extensions = run_cli("domain-source-field-policy", "--view", "extensions")
    domain_source_extensions_payload = json.loads(domain_source_extensions.stdout)
    if len(domain_source_extensions_payload) != 8:
        raise AssertionError("CLI domain-source-field-policy should expose eight extension fields")
    if any(item["requirementLevel"] != "domain_specific_extension" for item in domain_source_extensions_payload):
        raise AssertionError("CLI domain-source-field-policy extensions should be extension level")
    if any(not item["domainExtensionAllowed"] for item in domain_source_extensions_payload):
        raise AssertionError("CLI domain-source-field-policy extensions should be domain-extension allowed")
    if any(item["credentialValuesAllowed"] or item["rawPrivateDataAllowed"] for item in domain_source_extensions_payload):
        raise AssertionError("CLI domain-source-field-policy extensions must block secrets and raw private data")
    domain_source_blocked = run_cli("domain-source-field-policy", "--view", "blocked")
    domain_source_blocked_payload = json.loads(domain_source_blocked.stdout)
    if len(domain_source_blocked_payload) != 6:
        raise AssertionError("CLI domain-source-field-policy should expose six blocked fields")
    if any(item["requirementLevel"] != "blocked" for item in domain_source_blocked_payload):
        raise AssertionError("CLI domain-source-field-policy blocked fields should stay blocked")
    if any(item["domainExtensionAllowed"] for item in domain_source_blocked_payload):
        raise AssertionError("CLI domain-source-field-policy blocked fields must not be extensions")
    domain_source_kinds = run_cli("domain-source-field-policy", "--view", "source-kinds")
    domain_source_kinds_payload = json.loads(domain_source_kinds.stdout)
    source_kind_rules = {item["sourceKind"]: item for item in domain_source_kinds_payload}
    if set(source_kind_rules) != {"fixture", "local_file", "source_adapter_output", "api", "database"}:
        raise AssertionError("CLI domain-source-field-policy source kind coverage drifted")
    for source_kind, rule in source_kind_rules.items():
        if rule["sourceRefRequired"] is not True or rule["adapterRefRequired"] is not True:
            raise AssertionError(f"CLI domain-source-field-policy {source_kind} should require refs")
        if rule["credentialValueAllowed"] or rule["rawPayloadStored"]:
            raise AssertionError(f"CLI domain-source-field-policy {source_kind} must block raw payloads and credentials")
    if source_kind_rules["api"]["credentialReferenceRequired"] is not True:
        raise AssertionError("CLI domain-source-field-policy private API sources should require credential refs")
    if source_kind_rules["database"]["credentialReferenceRequired"] is not True:
        raise AssertionError("CLI domain-source-field-policy database sources should require credential refs")
    domain_source_case = run_cli("domain-source-field-policy", "--case", "raw_sql_query_as_binding_field")
    domain_source_case_payload = json.loads(domain_source_case.stdout)
    if domain_source_case_payload["caseStatus"] != "blocked_raw_sql_field":
        raise AssertionError("CLI domain-source-field-policy raw SQL case status drifted")
    if domain_source_case_payload["forecastArtifactsCreated"] is not False:
        raise AssertionError("CLI domain-source-field-policy raw SQL case must not create forecast artifacts")
    if domain_source_case_payload["sanitizedDiagnosticsOnly"] is not True:
        raise AssertionError("CLI domain-source-field-policy raw SQL case must keep diagnostics sanitized")
    domain_source_field = run_cli("domain-source-field-policy", "--field", "role_required_fields")
    domain_source_field_payload = json.loads(domain_source_field.stdout)
    if domain_source_field_payload["requirementLevel"] != "domain_specific_extension":
        raise AssertionError("CLI domain-source-field-policy role_required_fields should be an extension")
    if domain_source_field_payload["domainExtensionAllowed"] is not True:
        raise AssertionError("CLI domain-source-field-policy role_required_fields should allow extension")
    domain_source_boundary = run_cli("domain-source-field-policy", "--view", "boundary")
    domain_source_boundary_payload = json.loads(domain_source_boundary.stdout)
    for key in [
        "normalChecksWriteState",
        "createsForecasts",
        "readsPrivateData",
        "storesCredentialValues",
        "rawSqlAllowed",
        "arbitraryPrivateApiParsingByOpe",
        "arbitraryDatabaseParsingByOpe",
        "hostedRuntimeImplemented",
        "qualityClaimsUpgraded",
    ]:
        if domain_source_boundary_payload[key] is not False:
            raise AssertionError(f"CLI domain-source-field-policy boundary {key} should stay false")
    if any(domain_source_boundary_payload.values()):
        raise AssertionError("CLI domain-source-field-policy boundary flags should all stay false")
    domain_source_check = run_cli("domain-source-field-policy", "--check")
    if "checked domain source field policy" not in domain_source_check.stdout:
        raise AssertionError("CLI domain-source-field-policy --check did not check generated output")

    credential_policy = run_cli("credential-reference-policy")
    credential_policy_payload = json.loads(credential_policy.stdout)
    if credential_policy_payload["policyStatus"] != "credential_reference_policy_checked":
        raise AssertionError("CLI credential-reference-policy status drifted")
    if (
        credential_policy_payload["decisionStatus"]
        != "opaque_caller_owned_references_scoped_to_workspace_source_and_adapter"
    ):
        raise AssertionError("CLI credential-reference-policy decision status drifted")
    if credential_policy_payload["normalChecksMutateState"] is not False:
        raise AssertionError("CLI credential-reference-policy must keep normal checks non-mutating")
    if credential_policy_payload["secretResolverImplemented"] is not False:
        raise AssertionError("CLI credential-reference-policy must not implement a secret resolver")
    credential_summary = credential_policy_payload["summary"]
    expected_credential_counts = {
        "acceptedReferenceMechanismCount": 4,
        "requiredScopeKeyCount": 8,
        "lifecycleStateCount": 6,
        "consumerRuleCount": 6,
        "credentialReferenceCaseCount": 11,
        "blockedCaseCount": 8,
    }
    for key, expected in expected_credential_counts.items():
        if credential_summary[key] != expected:
            raise AssertionError(f"CLI credential-reference-policy {key} drifted")
    if credential_summary["normalChecksResolveSecrets"] is not False:
        raise AssertionError("CLI credential-reference-policy summary must block normal-check secret resolution")
    if credential_summary["secretResolverImplemented"] is not False:
        raise AssertionError("CLI credential-reference-policy summary must not implement a secret resolver")

    credential_mechanisms = run_cli("credential-reference-policy", "--view", "mechanisms")
    credential_mechanisms_payload = json.loads(credential_mechanisms.stdout)
    if [item["mechanismName"] for item in credential_mechanisms_payload] != [
        "caller_secret_store_alias",
        "host_runtime_secret_handle",
        "local_operator_session_ref",
        "public_no_credential",
    ]:
        raise AssertionError("CLI credential-reference-policy mechanism order drifted")
    for item in credential_mechanisms_payload:
        if item["secretValueStored"] or item["secretLookupDuringNormalChecks"] or item["promptVisibleSecretAllowed"]:
            raise AssertionError("CLI credential-reference-policy mechanisms must not expose secret values")
        if len(item["requiredScopeKeys"]) != 8:
            raise AssertionError("CLI credential-reference-policy mechanisms should carry eight scope keys")
    credential_mechanism = run_cli("credential-reference-policy", "--mechanism", "host_runtime_secret_handle")
    credential_mechanism_payload = json.loads(credential_mechanism.stdout)
    if "database" not in credential_mechanism_payload["allowedForSourceKinds"]:
        raise AssertionError("CLI credential-reference-policy host runtime handles should allow database references")
    if credential_mechanism_payload["secretLookupDuringNormalChecks"] is not False:
        raise AssertionError("CLI credential-reference-policy host runtime handles must not resolve in normal checks")

    credential_scope = run_cli("credential-reference-policy", "--view", "scope")
    credential_scope_payload = json.loads(credential_scope.stdout)
    if len(credential_scope_payload) != 8:
        raise AssertionError("CLI credential-reference-policy should expose eight scope keys")
    if any(not item["requiredForPrivateApi"] or not item["requiredForDatabase"] for item in credential_scope_payload):
        raise AssertionError("CLI credential-reference-policy scope keys should apply to APIs and databases")
    if any(item["containsSecretMaterial"] for item in credential_scope_payload):
        raise AssertionError("CLI credential-reference-policy scope keys must not contain secret material")
    credential_scope_key = run_cli("credential-reference-policy", "--scope-key", "tenant_id")
    credential_scope_key_payload = json.loads(credential_scope_key.stdout)
    if "cross-tenant" not in credential_scope_key_payload["prevents"]:
        raise AssertionError("CLI credential-reference-policy tenant scope should prevent cross-tenant reuse")

    credential_lifecycle = run_cli("credential-reference-policy", "--view", "lifecycle")
    credential_lifecycle_payload = json.loads(credential_lifecycle.stdout)
    lifecycle_rows = {item["stateName"]: item for item in credential_lifecycle_payload}
    if set(lifecycle_rows) != {"proposed", "approved", "active", "rotation_due", "revoked", "redaction_required"}:
        raise AssertionError("CLI credential-reference-policy lifecycle coverage drifted")
    if lifecycle_rows["active"]["allowsRuntimeUse"] is not True:
        raise AssertionError("CLI credential-reference-policy active state should allow explicit runtime use")
    if lifecycle_rows["revoked"]["allowsRuntimeUse"] is not False:
        raise AssertionError("CLI credential-reference-policy revoked state must block runtime use")
    if any(item["allowsNormalCheckSecretResolution"] for item in credential_lifecycle_payload):
        raise AssertionError("CLI credential-reference-policy lifecycle must block normal-check secret resolution")
    credential_state = run_cli("credential-reference-policy", "--state", "redaction_required")
    credential_state_payload = json.loads(credential_state.stdout)
    if credential_state_payload["requiresRedactionReceipt"] is not True:
        raise AssertionError("CLI credential-reference-policy redaction state should require a redaction receipt")

    credential_consumers = run_cli("credential-reference-policy", "--view", "consumers")
    credential_consumers_payload = json.loads(credential_consumers.stdout)
    consumer_rows = {item["consumerName"]: item for item in credential_consumers_payload}
    if set(consumer_rows) != {
        "private_api_adapter",
        "database_adapter",
        "source_binding_validation",
        "runtime_readback",
        "agent_envelope",
        "normal_checks",
    }:
        raise AssertionError("CLI credential-reference-policy consumer coverage drifted")
    if consumer_rows["normal_checks"]["mayUseCredentialReference"] is not False:
        raise AssertionError("CLI credential-reference-policy normal checks must not use credential references")
    for item in consumer_rows.values():
        if item["canReceiveCredentialValue"] or item["canResolveSecretInNormalChecks"]:
            raise AssertionError("CLI credential-reference-policy consumers must not receive or resolve credentials")
        if not item["requiresScopeMatch"] or not item["requiresAdapterMatch"]:
            raise AssertionError("CLI credential-reference-policy consumers should require scope and adapter matches")
    credential_consumer = run_cli("credential-reference-policy", "--consumer", "database_adapter")
    credential_consumer_payload = json.loads(credential_consumer.stdout)
    if "explicit_runtime_query" not in credential_consumer_payload["allowedOperations"]:
        raise AssertionError("CLI credential-reference-policy database adapter operation coverage drifted")

    credential_cases = run_cli("credential-reference-policy", "--view", "cases")
    credential_cases_payload = json.loads(credential_cases.stdout)
    if len(credential_cases_payload) != 11:
        raise AssertionError("CLI credential-reference-policy should expose eleven cases")
    credential_case_rows = {item["caseName"]: item for item in credential_cases_payload}
    if credential_case_rows["accepted_database_reference"]["canEnterAdapterRuntime"] is not True:
        raise AssertionError("CLI credential-reference-policy accepted database ref should enter adapter runtime")
    if credential_case_rows["accepted_private_api_reference"]["canEnterAdapterRuntime"] is not False:
        raise AssertionError("CLI credential-reference-policy private API runtime should remain deferred")
    for name, item in credential_case_rows.items():
        if item["credentialValuesStored"] or item["secretResolvedInNormalChecks"] or item["crossTenantReuseAllowed"]:
            raise AssertionError(f"CLI credential-reference-policy case {name} must not store or resolve credentials")
        if item["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError(f"CLI credential-reference-policy case {name} should keep diagnostics sanitized")
    for name in [
        "missing_reference_for_private_api",
        "raw_api_token_submitted",
        "database_password_in_connection_string",
        "cross_tenant_reference",
        "unscoped_reference",
        "adapter_mismatch",
        "revoked_reference",
        "normal_check_resolution_attempt",
    ]:
        if not credential_case_rows[name]["caseStatus"].startswith("blocked_"):
            raise AssertionError(f"CLI credential-reference-policy {name} should be blocked")
        if credential_case_rows[name]["sourceBindingAccepted"] is not False:
            raise AssertionError(f"CLI credential-reference-policy {name} must not accept source binding")
    credential_case = run_cli("credential-reference-policy", "--case", "database_password_in_connection_string")
    credential_case_payload = json.loads(credential_case.stdout)
    if credential_case_payload["caseStatus"] != "blocked_database_password_connection_string":
        raise AssertionError("CLI credential-reference-policy connection-string case status drifted")
    if credential_case_payload["canEnterAdapterRuntime"] is not False:
        raise AssertionError("CLI credential-reference-policy connection-string case must not enter adapter runtime")

    credential_boundary = run_cli("credential-reference-policy", "--view", "boundary")
    credential_boundary_payload = json.loads(credential_boundary.stdout)
    for key in [
        "normalChecksResolveSecrets",
        "storesCredentialValues",
        "printsCredentialValues",
        "readsEnvironmentSecrets",
        "writesSecretStore",
        "crossTenantCredentialReuseAllowed",
        "unscopedReferencesAllowed",
        "rawConnectionStringsAllowed",
        "databaseConnectionsOpened",
        "apiCallsExecuted",
        "hostedSecretManagerImplemented",
        "qualityClaimsUpgraded",
    ]:
        if credential_boundary_payload[key] is not False:
            raise AssertionError(f"CLI credential-reference-policy boundary {key} should stay false")
    if any(credential_boundary_payload.values()):
        raise AssertionError("CLI credential-reference-policy boundary flags should all stay false")
    credential_check = run_cli("credential-reference-policy", "--check")
    if "checked credential reference policy" not in credential_check.stdout:
        raise AssertionError("CLI credential-reference-policy --check did not check generated output")

    retention_policy = run_cli("retention-redaction-policy")
    retention_policy_payload = json.loads(retention_policy.stdout)
    if retention_policy_payload["policyStatus"] != "retention_redaction_policy_checked":
        raise AssertionError("CLI retention-redaction-policy status drifted")
    if (
        retention_policy_payload["decisionStatus"]
        != "tombstones_and_redaction_receipts_default_physical_delete_exception_only"
    ):
        raise AssertionError("CLI retention-redaction-policy decision status drifted")
    if retention_policy_payload["normalChecksMutateState"] is not False:
        raise AssertionError("CLI retention-redaction-policy must keep normal checks non-mutating")
    if retention_policy_payload["physicalDeleteDefaultEnabled"] is not False:
        raise AssertionError("CLI retention-redaction-policy must keep physical delete non-default")
    retention_summary = retention_policy_payload["summary"]
    expected_retention_counts = {
        "retentionClassCount": 8,
        "policyActionCount": 5,
        "decisionCaseCount": 12,
        "physicalDeleteGateCount": 8,
        "readbackCount": 7,
        "physicalDeleteExceptionCaseCount": 2,
        "blockedPhysicalDeleteCaseCount": 3,
    }
    for key, expected in expected_retention_counts.items():
        if retention_summary[key] != expected:
            raise AssertionError(f"CLI retention-redaction-policy {key} drifted")
    if retention_summary["normalChecksMutateState"] is not False:
        raise AssertionError("CLI retention-redaction-policy summary must keep normal checks non-mutating")
    if retention_summary["physicalDeleteDefaultEnabled"] is not False:
        raise AssertionError("CLI retention-redaction-policy summary must keep physical delete non-default")

    retention_classes = run_cli("retention-redaction-policy", "--view", "classes")
    retention_classes_payload = json.loads(retention_classes.stdout)
    retention_class_rows = {item["recordClass"]: item for item in retention_classes_payload}
    if set(retention_class_rows) != {
        "forecast_lifecycle_record",
        "evidence_trace_record",
        "source_connector_result",
        "source_binding_config",
        "credential_reference_record",
        "pilot_session_summary",
        "local_usage_trace_event",
        "operation_receipt",
    }:
        raise AssertionError("CLI retention-redaction-policy class coverage drifted")
    if retention_class_rows["forecast_lifecycle_record"]["physicalDeleteEligible"] is not False:
        raise AssertionError("CLI retention-redaction-policy must not physically delete forecast lifecycles")
    if retention_class_rows["credential_reference_record"]["retainCredentialValues"] is not False:
        raise AssertionError("CLI retention-redaction-policy must not retain credential values")
    if retention_class_rows["pilot_session_summary"]["rawContentRetained"] is not False:
        raise AssertionError("CLI retention-redaction-policy must not retain raw pilot content")
    if retention_class_rows["local_usage_trace_event"]["aggregateOnlyAfterWindow"] is not True:
        raise AssertionError("CLI retention-redaction-policy should aggregate usage traces after the window")
    for item in retention_class_rows.values():
        if item["silentDeleteAllowed"] or item["normalChecksWriteState"]:
            raise AssertionError("CLI retention-redaction-policy classes must not silently delete or write state")
        if item["auditMetadataRetained"] is not True:
            raise AssertionError("CLI retention-redaction-policy classes should retain audit metadata")

    retention_class = run_cli("retention-redaction-policy", "--record-class", "forecast_lifecycle_record")
    retention_class_payload = json.loads(retention_class.stdout)
    if retention_class_payload["defaultAction"] != "retain_append_only":
        raise AssertionError("CLI retention-redaction-policy forecast lifecycle default action drifted")

    retention_actions = run_cli("retention-redaction-policy", "--view", "actions")
    retention_actions_payload = json.loads(retention_actions.stdout)
    retention_action_rows = {item["actionName"]: item for item in retention_actions_payload}
    if retention_action_rows["archive_tombstone"]["writesAuditTombstone"] is not True:
        raise AssertionError("CLI retention-redaction-policy archive should write tombstones")
    if retention_action_rows["redaction_receipt"]["writesRedactionReceipt"] is not True:
        raise AssertionError("CLI retention-redaction-policy redaction should write receipts")
    if retention_action_rows["physical_delete_exception"]["requiresAllPhysicalDeleteGates"] is not True:
        raise AssertionError("CLI retention-redaction-policy physical delete should require all gates")
    for name, item in retention_action_rows.items():
        if item["normalChecksExecuteAction"] or item["silentDeleteAllowed"]:
            raise AssertionError(f"CLI retention-redaction-policy action {name} must not execute or silently delete")
        if name != "physical_delete_exception" and item["physicallyDeletesRecords"]:
            raise AssertionError(f"CLI retention-redaction-policy action {name} must not physically delete")
    retention_action = run_cli("retention-redaction-policy", "--action", "physical_delete_exception")
    retention_action_payload = json.loads(retention_action.stdout)
    if retention_action_payload["operationName"] != "future.physical_delete_exception":
        raise AssertionError("CLI retention-redaction-policy physical delete operation should stay future-only")

    retention_gates = run_cli("retention-redaction-policy", "--view", "gates")
    retention_gates_payload = json.loads(retention_gates.stdout)
    retention_gate_rows = {item["gateName"]: item for item in retention_gates_payload}
    if len(retention_gate_rows) != 8:
        raise AssertionError("CLI retention-redaction-policy should expose eight physical-delete gates")
    if retention_gate_rows["record_class_allows_physical_delete"]["blocksForecastHistory"] is not True:
        raise AssertionError("CLI retention-redaction-policy record-class gate should block forecast history")
    if retention_gate_rows["audit_tombstone_retained"]["requiredForException"] is not True:
        raise AssertionError("CLI retention-redaction-policy audit tombstone gate should be required")
    if retention_gate_rows["redaction_receipt_retained"]["requiredForException"] is not True:
        raise AssertionError("CLI retention-redaction-policy redaction receipt gate should be required")
    for item in retention_gate_rows.values():
        if not item["requiredForException"] or item["normalChecksEvaluateAsEffectful"]:
            raise AssertionError("CLI retention-redaction-policy gates must be required and non-effectful")
    retention_gate = run_cli("retention-redaction-policy", "--gate", "record_class_allows_physical_delete")
    retention_gate_payload = json.loads(retention_gate.stdout)
    if retention_gate_payload["failureStatus"] != "blocked_record_class":
        raise AssertionError("CLI retention-redaction-policy record-class gate failure status drifted")

    retention_cases = run_cli("retention-redaction-policy", "--view", "cases")
    retention_cases_payload = json.loads(retention_cases.stdout)
    retention_case_rows = {item["caseName"]: item for item in retention_cases_payload}
    if len(retention_case_rows) != 12:
        raise AssertionError("CLI retention-redaction-policy should expose twelve cases")
    if retention_case_rows["archive_inactive_prediction"]["selectedAction"] != "archive_tombstone":
        raise AssertionError("CLI retention-redaction-policy archive case action drifted")
    if retention_case_rows["redact_credential_like_field"]["selectedAction"] != "redaction_receipt":
        raise AssertionError("CLI retention-redaction-policy credential redaction action drifted")
    if retention_case_rows["source_connector_raw_preview_requested"]["caseStatus"] != "blocked_raw_retention":
        raise AssertionError("CLI retention-redaction-policy raw preview case should block")
    if retention_case_rows["physical_delete_with_authorized_erasure"]["caseStatus"] != "exception_preflight_ready":
        raise AssertionError("CLI retention-redaction-policy authorized erasure case drifted")
    if retention_case_rows["physical_delete_for_forecast_history"]["caseStatus"] != "blocked_record_class":
        raise AssertionError("CLI retention-redaction-policy forecast physical delete case should block")
    for name, item in retention_case_rows.items():
        if item["normalChecksWriteState"] or item["credentialValuesRetained"]:
            raise AssertionError(f"CLI retention-redaction-policy case {name} must not write state or retain credentials")
        if item["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError(f"CLI retention-redaction-policy case {name} should keep diagnostics sanitized")
        if item["selectedAction"] != "physical_delete_exception" and item["physicallyDeletesRecords"]:
            raise AssertionError(f"CLI retention-redaction-policy case {name} must not physically delete")
    retention_case = run_cli("retention-redaction-policy", "--case", "physical_delete_missing_legal_basis")
    retention_case_payload = json.loads(retention_case.stdout)
    if retention_case_payload["caseStatus"] != "blocked_missing_gate":
        raise AssertionError("CLI retention-redaction-policy missing legal basis case should block")

    retention_boundary = run_cli("retention-redaction-policy", "--view", "boundary")
    retention_boundary_payload = json.loads(retention_boundary.stdout)
    for key in [
        "normalChecksPhysicallyDelete",
        "normalChecksWriteState",
        "silentDeleteAllowed",
        "forecastHistoryRewriteAllowed",
        "credentialValuesRetained",
        "rawPrivateRowsRetained",
        "rawPilotTranscriptsRetained",
        "physicalDeleteDefaultEnabled",
        "hostedErasureWorkflowImplemented",
        "qualityClaimsUpgraded",
    ]:
        if retention_boundary_payload[key] is not False:
            raise AssertionError(f"CLI retention-redaction-policy boundary {key} should stay false")
    if any(retention_boundary_payload.values()):
        raise AssertionError("CLI retention-redaction-policy boundary flags should all stay false")
    retention_check = run_cli("retention-redaction-policy", "--check")
    if "checked retention redaction policy" not in retention_check.stdout:
        raise AssertionError("CLI retention-redaction-policy --check did not check generated output")

    private_auto_policy = run_cli("private-auto-evidence-policy")
    private_auto_policy_payload = json.loads(private_auto_policy.stdout)
    if private_auto_policy_payload["policyStatus"] != "private_auto_evidence_policy_checked":
        raise AssertionError("CLI private-auto-evidence-policy status drifted")
    if (
        private_auto_policy_payload["decisionStatus"]
        != "private_data_auto_requires_bound_source_policy_and_approved_adapters"
    ):
        raise AssertionError("CLI private-auto-evidence-policy decision status drifted")
    if private_auto_policy_payload["normalChecksMutateState"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy must keep normal checks non-mutating")
    if private_auto_policy_payload["normalChecksReadPrivateSources"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy must not read private sources")
    private_auto_summary = private_auto_policy_payload["summary"]
    expected_private_auto_counts = {
        "sourceKindCount": 8,
        "policyGateCount": 12,
        "decisionCaseCount": 13,
        "readbackCount": 10,
        "blockedCaseCount": 8,
        "manifestOnlyCaseCount": 2,
    }
    for key, expected in expected_private_auto_counts.items():
        if private_auto_summary[key] != expected:
            raise AssertionError(f"CLI private-auto-evidence-policy {key} drifted")
    if private_auto_summary["normalChecksReadPrivateSources"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy summary must not read private sources")
    if private_auto_summary["normalChecksMutateState"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy summary must keep normal checks non-mutating")

    private_auto_source = run_cli("private-auto-evidence-policy", "--view", "source")
    private_auto_source_payload = json.loads(private_auto_source.stdout)
    if private_auto_source_payload["sourcePolicySchemaId"] != "https://openprediction.engine/spec/source-policy.schema.json":
        raise AssertionError("CLI private-auto-evidence-policy source-policy schema binding drifted")
    if private_auto_source_payload["credentialReferencePolicyStatus"] != "credential_reference_policy_checked":
        raise AssertionError("CLI private-auto-evidence-policy credential source drifted")
    if private_auto_source_payload["retentionRedactionPolicyStatus"] != "retention_redaction_policy_checked":
        raise AssertionError("CLI private-auto-evidence-policy retention source drifted")
    if private_auto_source_payload["normalChecksWriteState"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy source bindings must stay read-only")

    private_auto_kinds = run_cli("private-auto-evidence-policy", "--view", "source-kinds")
    private_auto_kinds_payload = json.loads(private_auto_kinds.stdout)
    private_auto_kind_rows = {item["sourceKind"]: item for item in private_auto_kinds_payload}
    if set(private_auto_kind_rows) != {
        "local_file",
        "manual_mapping",
        "auto_evidence_connector",
        "source_adapter_output",
        "database_query_manifest",
        "private_api_manifest",
        "manual_upload",
        "web_search",
    }:
        raise AssertionError("CLI private-auto-evidence-policy source-kind coverage drifted")
    if private_auto_kind_rows["local_file"]["currentPolicyStatus"] != "allowed_with_approved_local_runtime":
        raise AssertionError("CLI private-auto-evidence-policy local file status drifted")
    if private_auto_kind_rows["source_adapter_output"]["currentPolicyStatus"] != "allowed_with_sanitized_adapter_output":
        raise AssertionError("CLI private-auto-evidence-policy adapter output status drifted")
    if private_auto_kind_rows["database_query_manifest"]["currentPolicyStatus"] != "manifest_only_no_raw_sql_execution":
        raise AssertionError("CLI private-auto-evidence-policy database manifest status drifted")
    if private_auto_kind_rows["private_api_manifest"]["credentialReferenceRequired"] is not True:
        raise AssertionError("CLI private-auto-evidence-policy private API should require credentials by reference")
    if private_auto_kind_rows["web_search"]["currentPolicyStatus"] != "blocked_for_private_data_auto":
        raise AssertionError("CLI private-auto-evidence-policy should block private web search")
    if private_auto_kind_rows["web_search"]["networkAccessAllowed"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy should not allow private web search network access")
    for name, item in private_auto_kind_rows.items():
        if not item["sourcePolicyRequired"] or not item["tenantWorkspaceScopeRequired"]:
            raise AssertionError(f"CLI private-auto-evidence-policy source kind {name} must require policy and scope")
        if item["normalChecksReadPrivateSource"] or item["normalChecksResolveCredential"]:
            raise AssertionError(f"CLI private-auto-evidence-policy source kind {name} must stay non-effectful")
        if item["rawPayloadRetentionAllowed"]:
            raise AssertionError(f"CLI private-auto-evidence-policy source kind {name} must not retain raw payloads")

    private_auto_kind = run_cli("private-auto-evidence-policy", "--source-kind", "private_api_manifest")
    private_auto_kind_payload = json.loads(private_auto_kind.stdout)
    if private_auto_kind_payload["currentPolicyStatus"] != "manifest_only_no_runtime_execution":
        raise AssertionError("CLI private-auto-evidence-policy private API source-kind status drifted")

    private_auto_gates = run_cli("private-auto-evidence-policy", "--view", "gates")
    private_auto_gates_payload = json.loads(private_auto_gates.stdout)
    private_auto_gate_rows = {item["gateName"]: item for item in private_auto_gates_payload}
    if len(private_auto_gate_rows) != 12:
        raise AssertionError("CLI private-auto-evidence-policy should expose twelve gates")
    if private_auto_gate_rows["credential_reference_scoped"]["blocksCredentialValues"] is not True:
        raise AssertionError("CLI private-auto-evidence-policy credential gate should block credential values")
    if private_auto_gate_rows["adapter_capability_checked"]["blocksUnregisteredAdapters"] is not True:
        raise AssertionError("CLI private-auto-evidence-policy adapter gate should block unregistered adapters")
    if private_auto_gate_rows["forecast_before_close_preserved"]["blocksPostOutcomeEvidence"] is not True:
        raise AssertionError("CLI private-auto-evidence-policy forecast timing gate should block post-outcome evidence")
    for item in private_auto_gate_rows.values():
        if not item["requiredForPrivateAuto"] or item["normalChecksEvaluateAsEffectful"]:
            raise AssertionError("CLI private-auto-evidence-policy gates must be required and non-effectful")
    private_auto_gate = run_cli("private-auto-evidence-policy", "--gate", "adapter_capability_checked")
    private_auto_gate_payload = json.loads(private_auto_gate.stdout)
    if private_auto_gate_payload["failureStatus"] != "blocked_unregistered_adapter":
        raise AssertionError("CLI private-auto-evidence-policy adapter gate failure status drifted")

    private_auto_cases = run_cli("private-auto-evidence-policy", "--view", "cases")
    private_auto_cases_payload = json.loads(private_auto_cases.stdout)
    private_auto_case_rows = {item["caseName"]: item for item in private_auto_cases_payload}
    if len(private_auto_case_rows) != 13:
        raise AssertionError("CLI private-auto-evidence-policy should expose thirteen cases")
    if private_auto_case_rows["approved_local_file_auto"]["caseStatus"] != "policy_ready":
        raise AssertionError("CLI private-auto-evidence-policy approved local file case drifted")
    if private_auto_case_rows["approved_database_query_manifest"]["caseStatus"] != "manifest_ready_no_execution":
        raise AssertionError("CLI private-auto-evidence-policy database manifest case drifted")
    if private_auto_case_rows["manual_upload_without_adapter_contract"]["caseStatus"] != "blocked_missing_adapter_contract":
        raise AssertionError("CLI private-auto-evidence-policy manual upload case should block")
    if private_auto_case_rows["database_raw_sql_auto"]["caseStatus"] != "blocked_raw_sql":
        raise AssertionError("CLI private-auto-evidence-policy raw SQL case should block")
    if private_auto_case_rows["web_search_private_setup"]["caseStatus"] != "blocked_private_web_search":
        raise AssertionError("CLI private-auto-evidence-policy private web search case should block")
    if private_auto_case_rows["post_outcome_capture_as_forecast_evidence"]["caseStatus"] != "blocked_post_outcome_evidence":
        raise AssertionError("CLI private-auto-evidence-policy post-outcome evidence case should block")
    if private_auto_case_rows["raw_private_payload_retention"]["caseStatus"] != "blocked_raw_payload_retention":
        raise AssertionError("CLI private-auto-evidence-policy raw payload retention case should block")
    for name, item in private_auto_case_rows.items():
        if item["normalChecksReadPrivateSources"] or item["normalChecksWriteState"] or item["credentialValuesStored"]:
            raise AssertionError(f"CLI private-auto-evidence-policy case {name} must stay non-effectful")
        if item["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError(f"CLI private-auto-evidence-policy case {name} should keep diagnostics sanitized")
        if item["caseStatus"].startswith("blocked_") and item["eligibleForForecastExecution"]:
            raise AssertionError(f"CLI private-auto-evidence-policy blocked case {name} must not be forecast-eligible")
    private_auto_case = run_cli("private-auto-evidence-policy", "--case", "web_search_private_setup")
    private_auto_case_payload = json.loads(private_auto_case.stdout)
    if private_auto_case_payload["sourcePolicyBound"] is not False:
        raise AssertionError("CLI private-auto-evidence-policy web search case should remain unbound")

    private_auto_boundary = run_cli("private-auto-evidence-policy", "--view", "boundary")
    private_auto_boundary_payload = json.loads(private_auto_boundary.stdout)
    for key in [
        "normalChecksReadPrivateSources",
        "normalChecksResolveSecrets",
        "normalChecksNetworkAccess",
        "normalChecksWriteState",
        "arbitraryWebSearchAllowed",
        "arbitraryPrivateApiParsingAllowed",
        "arbitraryDatabaseParsingAllowed",
        "rawSqlExecutionAllowed",
        "rawPrivatePayloadRetentionAllowed",
        "postOutcomeEvidenceAsForecastEvidenceAllowed",
        "hostedRuntimeImplemented",
        "qualityClaimsUpgraded",
        "generatedRuntimeTypesEnabled",
    ]:
        if private_auto_boundary_payload[key] is not False:
            raise AssertionError(f"CLI private-auto-evidence-policy boundary {key} should stay false")
    if any(private_auto_boundary_payload.values()):
        raise AssertionError("CLI private-auto-evidence-policy boundary flags should all stay false")
    private_auto_check = run_cli("private-auto-evidence-policy", "--check")
    if "checked private auto-evidence policy" not in private_auto_check.stdout:
        raise AssertionError("CLI private-auto-evidence-policy --check did not check generated output")

    transit_forecast = run_cli("transit-delay-forecast")
    transit_forecast_payload = json.loads(transit_forecast.stdout)
    if transit_forecast_payload["domain"] != "weather-transit-delays":
        raise AssertionError("CLI transit-delay-forecast should return transit domain")
    if transit_forecast_payload["forecast"]["probability"] <= transit_forecast_payload["baseline"]["probability"]:
        raise AssertionError("CLI transit-delay-forecast fixture should lift above baseline")
    if transit_forecast_payload["score"]["scoreStatus"] != "scored":
        raise AssertionError("CLI transit-delay-forecast fixture should score resolved outcome")
    if transit_forecast_payload["qualityClaim"]["status"] != "not_enough_resolved_transit_delay_outcomes":
        raise AssertionError("CLI transit-delay-forecast should keep quality claim blocked")
    transit_forecast_check = run_cli("transit-delay-forecast", "--check")
    if "checked 7 transit delay forecast outputs" not in transit_forecast_check.stdout:
        raise AssertionError("CLI transit-delay-forecast --check did not check generated outputs")

    transit_forward = run_cli("transit-delay-forward-run")
    transit_forward_payload = json.loads(transit_forward.stdout)
    if transit_forward_payload["runMode"] != "fixture_replay":
        raise AssertionError("CLI transit-delay-forward-run should default to fixture replay")
    if transit_forward_payload["runStatus"] != "scored":
        raise AssertionError("CLI transit-delay-forward-run fixture should score the outcome")
    if transit_forward_payload["forecastStage"]["probability"] <= transit_forward_payload["forecastStage"]["baselineProbability"]:
        raise AssertionError("CLI transit-delay-forward-run fixture should lift above baseline")
    if transit_forward_payload["resolutionStage"]["status"] != "resolved":
        raise AssertionError("CLI transit-delay-forward-run fixture should resolve the outcome")
    if transit_forward_payload["scoreStage"]["scoreStatus"] != "scored":
        raise AssertionError("CLI transit-delay-forward-run fixture should expose scoring")
    if transit_forward_payload["claimBoundary"]["calibrationClaimAllowed"]:
        raise AssertionError("CLI transit-delay-forward-run should keep calibration claims blocked")
    transit_forward_check = run_cli("transit-delay-forward-run", "--check")
    if "checked transit delay forward run" not in transit_forward_check.stdout:
        raise AssertionError("CLI transit-delay-forward-run --check did not check generated output")

    forward_resolver = run_cli("resolve-due-forward-runs")
    forward_resolver_payload = json.loads(forward_resolver.stdout)
    if forward_resolver_payload["runMode"] != "fixture_scan":
        raise AssertionError("CLI resolve-due-forward-runs should default to fixture scan")
    if forward_resolver_payload["executionMode"] != "dry_run":
        raise AssertionError("CLI resolve-due-forward-runs should default to dry-run mode")
    if forward_resolver_payload["scanSummary"]["dueCount"] != 2:
        raise AssertionError("CLI resolve-due-forward-runs fixture should find one due and one stale-due run")
    if forward_resolver_payload["scanSummary"]["executedCount"] != 0:
        raise AssertionError("CLI resolve-due-forward-runs fixture should not execute runs")
    if forward_resolver_payload["executionBoundary"]["sourceFetchPerformed"]:
        raise AssertionError("CLI resolve-due-forward-runs fixture should not fetch sources")
    forward_resolver_check = run_cli("resolve-due-forward-runs", "--check")
    if "checked transit forward-run resolver" not in forward_resolver_check.stdout:
        raise AssertionError("CLI resolve-due-forward-runs --check did not check generated output")

    resolution_jobs = run_cli("resolution-jobs")
    resolution_jobs_payload = json.loads(resolution_jobs.stdout)
    if resolution_jobs_payload["registryMode"] != "fixture_registry":
        raise AssertionError("CLI resolution-jobs should default to fixture registry")
    if resolution_jobs_payload["summary"]["pendingDueCount"] != 1:
        raise AssertionError("CLI resolution-jobs should expose one due fixture job")
    if resolution_jobs_payload["executionBoundary"]["registryExecutesResolvers"]:
        raise AssertionError("CLI resolution-jobs must not execute resolver commands")
    due_jobs = [job for job in resolution_jobs_payload["jobs"] if job["jobStatus"] == "pending_due"]
    if due_jobs[0]["agentAction"]["recommendedAction"] != "call_resolver_execute":
        raise AssertionError("CLI resolution-jobs should route due jobs to resolver execution")
    resolution_jobs_check = run_cli("resolution-jobs", "--check")
    if "checked resolution jobs" not in resolution_jobs_check.stdout:
        raise AssertionError("CLI resolution-jobs --check did not check generated output")
    campaign_resolution_jobs = run_cli("resolution-jobs", "--campaign", "predictioncampaign-001")
    campaign_resolution_jobs_payload = json.loads(campaign_resolution_jobs.stdout)
    if campaign_resolution_jobs_payload["registryMode"] != "campaign_fixture_registry":
        raise AssertionError("CLI campaign resolution-jobs should use campaign fixture mode")
    if campaign_resolution_jobs_payload["summary"]["jobCount"] != 5:
        raise AssertionError("CLI campaign resolution-jobs should include one campaign forecast job beside the four forward-run jobs")
    campaign_jobs = [
        job for job in campaign_resolution_jobs_payload["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    if len(campaign_jobs) != 1:
        raise AssertionError("CLI campaign resolution-jobs should expose one campaign job")
    if campaign_jobs[0]["target"]["forecastId"] != "forecast-1301":
        raise AssertionError("CLI campaign resolution-jobs forecast binding drifted")
    if campaign_jobs[0]["agentAction"]["recommendedAction"] != "wait":
        raise AssertionError("CLI campaign resolution-jobs should tell agents to wait")
    due_campaign_resolution_jobs = run_cli(
        "resolution-jobs",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_resolution_jobs_payload = json.loads(due_campaign_resolution_jobs.stdout)
    due_campaign_jobs = [
        job for job in due_campaign_resolution_jobs_payload["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    if due_campaign_jobs[0]["agentAction"]["recommendedAction"] != "call_campaign_resolver_attempt":
        raise AssertionError("CLI due campaign resolution-jobs should route to the checked resolver attempt")
    if "prediction-campaign resolve" not in " ".join(due_campaign_jobs[0]["agentAction"]["commands"]):
        raise AssertionError("CLI due campaign resolution-jobs should include the resolver-attempt command")
    campaign_resolution_jobs_check = run_cli("resolution-jobs", "--campaign", "predictioncampaign-001", "--check")
    if "checked resolution jobs" not in campaign_resolution_jobs_check.stdout:
        raise AssertionError("CLI campaign resolution-jobs --check did not check generated output")

    resolution_scheduler = run_cli("resolution-scheduler")
    resolution_scheduler_payload = json.loads(resolution_scheduler.stdout)
    if resolution_scheduler_payload["schedulerMode"] != "fixture_once":
        raise AssertionError("CLI resolution-scheduler should default to one fixture tick")
    if resolution_scheduler_payload["executionMode"] != "dry_run":
        raise AssertionError("CLI resolution-scheduler should default to dry-run mode")
    scheduler_tick = resolution_scheduler_payload["ticks"][0]
    if scheduler_tick["jobSummary"]["pendingDueCount"] != 1:
        raise AssertionError("CLI resolution-scheduler fixture should see one due job")
    if scheduler_tick["tickStatus"] != "due_pending":
        raise AssertionError("CLI resolution-scheduler fixture should wait for --execute")
    if scheduler_tick["resolverSummary"]["ranResolver"]:
        raise AssertionError("CLI resolution-scheduler dry-run should not run resolver execution")
    scheduler_boundary = resolution_scheduler_payload["executionBoundary"]
    if scheduler_boundary["hostedSchedulerCreated"] or scheduler_boundary["osSchedulerCreated"]:
        raise AssertionError("CLI resolution-scheduler must not create hosted or OS schedulers")
    resolution_scheduler_check = run_cli("resolution-scheduler", "--check")
    if "checked resolution scheduler" not in resolution_scheduler_check.stdout:
        raise AssertionError("CLI resolution-scheduler --check did not check generated output")
    campaign_scheduler = run_cli("resolution-scheduler", "--campaign", "predictioncampaign-001")
    campaign_scheduler_payload = json.loads(campaign_scheduler.stdout)
    if campaign_scheduler_payload["schedulerMode"] != "campaign_fixture_once":
        raise AssertionError("CLI campaign resolution-scheduler should use campaign fixture mode")
    if campaign_scheduler_payload["ticks"][0]["jobSummary"]["jobCount"] != 5:
        raise AssertionError("CLI campaign resolution-scheduler should include the campaign job")
    campaign_actions = [
        action for action in campaign_scheduler_payload["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    if len(campaign_actions) != 1:
        raise AssertionError("CLI campaign resolution-scheduler should expose one campaign action")
    if campaign_actions[0]["schedulerAction"] != "wait_until_due":
        raise AssertionError("CLI campaign resolution-scheduler should wait for the campaign resolution time")
    due_campaign_scheduler = run_cli(
        "resolution-scheduler",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_scheduler_payload = json.loads(due_campaign_scheduler.stdout)
    due_campaign_actions = [
        action for action in due_campaign_scheduler_payload["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    if due_campaign_actions[0]["schedulerAction"] != "campaign_resolver_attempt_ready":
        raise AssertionError("CLI due campaign scheduler should route to the checked resolver attempt")
    campaign_scheduler_check = run_cli("resolution-scheduler", "--campaign", "predictioncampaign-001", "--check")
    if "checked resolution scheduler" not in campaign_scheduler_check.stdout:
        raise AssertionError("CLI campaign resolution-scheduler --check did not check generated output")

    runtime_reliability = run_cli("resolution-runtime-reliability")
    runtime_reliability_payload = json.loads(runtime_reliability.stdout)
    failure_classes = {item["failureClass"] for item in runtime_reliability_payload["failureTaxonomy"]}
    if len(failure_classes) != 11 or "rate_limits" not in failure_classes or "late_capture_window" not in failure_classes:
        raise AssertionError("CLI resolution-runtime-reliability should expose the checked failure taxonomy")
    if any(item["rawDiagnosticsExposed"] for item in runtime_reliability_payload["failureTaxonomy"]):
        raise AssertionError("CLI resolution-runtime-reliability should expose only sanitized failure diagnostics")
    reliability_boundary = runtime_reliability_payload["executionBoundary"]
    if not reliability_boundary["readModelDoesNotExecute"] or reliability_boundary["normalChecksUseLiveNetwork"]:
        raise AssertionError("CLI resolution-runtime-reliability should remain a non-executing offline read model")
    if reliability_boundary["usesPostCloseOutcomeAsForecastEvidence"]:
        raise AssertionError("CLI resolution-runtime-reliability must block outcome-as-forecast provenance")
    if runtime_reliability_payload["sourcePolicyBoundary"]["liveCaptureFilesCommitted"]:
        raise AssertionError("CLI resolution-runtime-reliability should keep live captures local")
    resolution_only_actions = [
        item for item in runtime_reliability_payload["provenanceLedger"] if item["resolutionOnlyEvidence"]
    ]
    if not resolution_only_actions or any(item["forecastTimeEvidence"] for item in resolution_only_actions):
        raise AssertionError("CLI resolution-runtime-reliability should separate resolution-only evidence")
    runtime_reliability_check = run_cli("resolution-runtime-reliability", "--check")
    if "checked resolution runtime reliability" not in runtime_reliability_check.stdout:
        raise AssertionError("CLI resolution-runtime-reliability --check did not check generated output")

    lifecycle_store = run_cli("lifecycle-operation-store")
    lifecycle_store_payload = json.loads(lifecycle_store.stdout)
    lifecycle_operations = {item["operationName"]: item for item in lifecycle_store_payload["operationCatalog"]}
    if {"forecast.create", "resolution.record", "score.create", "pre_calibration.bind", "state.import_json", "record.archive", "record.redact"} - set(lifecycle_operations):
        raise AssertionError("CLI lifecycle-operation-store should expose core lifecycle operations")
    if lifecycle_store_payload["summary"]["firstBackend"] != "local_sqlite":
        raise AssertionError("CLI lifecycle-operation-store should plan SQLite as the first backend")
    if lifecycle_store_payload["summary"]["productionDesignBackend"] != "postgres_design":
        raise AssertionError("CLI lifecycle-operation-store should keep Postgres as the production design target")
    if not lifecycle_store_payload["summary"]["sqliteRuntimeChecked"]:
        raise AssertionError("CLI lifecycle-operation-store should expose a checked SQLite runtime")
    if lifecycle_store_payload["summary"]["runtimeScenarioCount"] != len(SCENARIO_NAMES):
        raise AssertionError("CLI lifecycle-operation-store should expose the required runtime scenarios")
    if lifecycle_store_payload["summary"]["writeLocalOperationCoverageCount"] != len(REQUIRED_WRITE_LOCAL_COMMANDS):
        raise AssertionError("CLI lifecycle-operation-store should cover the current write-local command paths")
    if not lifecycle_store_payload["summary"]["allWriteLocalPathsReceiptBacked"]:
        raise AssertionError("CLI lifecycle-operation-store should receipt-back all write-local command paths")
    if not lifecycle_store_payload["summary"]["allWriteLocalPathsReadModelBacked"]:
        raise AssertionError("CLI lifecycle-operation-store should read-model-back all write-local command paths")
    if lifecycle_store_payload["summary"]["fileDatabaseCompatibilityCheckCount"] != len(REQUIRED_COMPATIBILITY_CLASSES):
        raise AssertionError("CLI lifecycle-operation-store should expose file/database compatibility checks")
    if not lifecycle_store_payload["summary"]["fileDatabaseCompatibilityChecked"]:
        raise AssertionError("CLI lifecycle-operation-store should check file/database compatibility")
    lifecycle_boundary = lifecycle_store_payload["executionBoundary"]
    if lifecycle_boundary["readbackExecutesDatabaseWrites"] or lifecycle_boundary["rawCrudExposedToAgents"]:
        raise AssertionError("CLI lifecycle-operation-store must remain non-mutating and block raw CRUD")
    if not lifecycle_boundary["sqliteRuntimeImplemented"] or not lifecycle_boundary["sqliteScenarioUsesEphemeralDatabase"]:
        raise AssertionError("CLI lifecycle-operation-store should exercise the local SQLite adapter")
    if lifecycle_store_payload["mutationSemantics"]["forecastArtifactsMutable"]:
        raise AssertionError("CLI lifecycle-operation-store must keep forecast artifacts immutable")
    if lifecycle_store_payload["mutationSemantics"]["deleteAllowedAsPhysicalDefault"]:
        raise AssertionError("CLI lifecycle-operation-store must replace physical delete with lifecycle operations")
    lifecycle_compat = lifecycle_store_payload["jsonCompatibilityAdapter"]
    if lifecycle_compat["adapterStatus"] != "current_compatibility_adapter":
        raise AssertionError("CLI lifecycle-operation-store should expose ignored JSON as the current compatibility adapter")
    if lifecycle_compat["automaticMigrationAllowed"] or lifecycle_compat["normalChecksWriteLiveState"]:
        raise AssertionError("CLI lifecycle-operation-store compatibility adapter must not auto-migrate or write in checks")
    if not lifecycle_compat["migrationReceiptRequired"] or not lifecycle_compat["contentHashCheckRequired"]:
        raise AssertionError("CLI lifecycle-operation-store compatibility adapter should require receipts and content hashes")
    lifecycle_read_models = {item["readModelName"] for item in lifecycle_store_payload["readModels"]}
    if {"next_due_forecast", "recovery_actions", "pilot_findings"} - lifecycle_read_models:
        raise AssertionError("CLI lifecycle-operation-store should expose agent read models")
    lifecycle_scenarios = {item["scenarioName"]: item for item in lifecycle_store_payload["runtimeScenarios"]}
    if lifecycle_scenarios["retry-idempotent"]["duplicateRecordsCreated"] != 0:
        raise AssertionError("CLI lifecycle-operation-store retry scenario should avoid duplicate records")
    if lifecycle_scenarios["lease-conflict"]["executionStatus"] != "blocked_lease_conflict":
        raise AssertionError("CLI lifecycle-operation-store should expose a blocked lease-conflict scenario")
    if lifecycle_scenarios["pre-calibration-bind"]["operationName"] != "pre_calibration.bind":
        raise AssertionError("CLI lifecycle-operation-store should expose database-native pre-calibration binding")
    if lifecycle_scenarios["pre-calibration-bind"]["preflight"]["plannedWrites"][1]["recordType"] != "pre_calibration_binding":
        raise AssertionError("CLI lifecycle-operation-store pre-calibration binding should write its own audit record")
    if lifecycle_scenarios["campaign-forecast-create"]["immutableRecordsInserted"] != 4:
        raise AssertionError("CLI lifecycle-operation-store campaign forecast bridge should write four lifecycle records")
    if not all(row["matchesSourceHash"] for row in lifecycle_scenarios["campaign-forecast-create"]["payloadHashBindings"]):
        raise AssertionError("CLI lifecycle-operation-store campaign bridge hashes should match source payloads")
    if lifecycle_scenarios["campaign-evidence-append"]["preflight"]["plannedWrites"][1]["recordType"] != "evidence_ledger_row":
        raise AssertionError("CLI lifecycle-operation-store campaign append bridge should write evidence ledger rows")
    if lifecycle_scenarios["pilot-evidence-append"]["preflight"]["plannedWrites"][1]["recordType"] != "pilot_evidence_ledger_row":
        raise AssertionError("CLI lifecycle-operation-store pilot append bridge should write pilot evidence ledger rows")
    if "pilot_findings" not in lifecycle_scenarios["pilot-evidence-append"]["readModelEffects"]:
        raise AssertionError("CLI lifecycle-operation-store pilot append bridge should update pilot findings")
    if "calibration_status" in lifecycle_scenarios["pilot-evidence-append"]["readModelEffects"]:
        raise AssertionError("CLI lifecycle-operation-store pilot append bridge must not update calibration status")
    if "track_record_progress" in lifecycle_scenarios["pilot-evidence-append"]["readModelEffects"]:
        raise AssertionError("CLI lifecycle-operation-store pilot append bridge must not update track-record progress")
    if "append_readiness" not in lifecycle_scenarios["campaign-score-create"]["readModelEffects"]:
        raise AssertionError("CLI lifecycle-operation-store scoring bridge should update append readiness")
    if "calibration_status" not in lifecycle_scenarios["campaign-evidence-append"]["readModelEffects"]:
        raise AssertionError("CLI lifecycle-operation-store append bridge should update calibration status")
    lifecycle_write_local_commands = {
        item["commandPath"] for item in lifecycle_store_payload["writeLocalOperationCoverage"]
    }
    if "prediction-campaign resolve --execute-resolvers --write-local" not in lifecycle_write_local_commands:
        raise AssertionError("CLI lifecycle-operation-store should map resolver write-local commands to lifecycle operations")
    if "prediction-campaign start --pre-calibrate --write-local" not in lifecycle_write_local_commands:
        raise AssertionError("CLI lifecycle-operation-store should map pre-calibrated starts to lifecycle operations")
    if "pilot-evidence --input-summary --write-local" not in lifecycle_write_local_commands:
        raise AssertionError("CLI lifecycle-operation-store should map pilot evidence writes to lifecycle operations")
    lifecycle_compatibility_classes = {
        item["recordClass"] for item in lifecycle_store_payload["fileDatabaseCompatibilityChecks"]
    }
    if {"forecast_lifecycle_records", "resolution_records", "scoring_reports", "evidence_ledger_rows", "pilot_evidence_ledger_rows"} - lifecycle_compatibility_classes:
        raise AssertionError("CLI lifecycle-operation-store should check file/database compatibility for campaign records")
    if any(item["databaseDuplicateRecordsCreated"] for item in lifecycle_store_payload["fileDatabaseCompatibilityChecks"]):
        raise AssertionError("CLI lifecycle-operation-store compatibility checks should prevent duplicate database records")
    migration_summary = lifecycle_scenarios["json-state-import"]["migrationImportSummary"]
    if migration_summary is None or not migration_summary["contentHashesPreserved"]:
        raise AssertionError("CLI lifecycle-operation-store JSON import should preserve content hashes")
    if not migration_summary["forecastProbabilitiesPreserved"] or migration_summary["historicalForecastRewriteCount"] != 0:
        raise AssertionError("CLI lifecycle-operation-store JSON import should preserve probabilities and avoid history rewrites")
    if lifecycle_scenarios["archive"]["physicalDeletes"] != 0 or lifecycle_scenarios["redaction"]["physicalDeletes"] != 0:
        raise AssertionError("CLI lifecycle-operation-store should replace delete-like operations with audit records")
    lifecycle_scenario = run_cli("lifecycle-operation-store", "--scenario", "method-rollback")
    lifecycle_scenario_payload = json.loads(lifecycle_scenario.stdout)
    if lifecycle_scenario_payload["scenarioName"] != "method-rollback":
        raise AssertionError("CLI lifecycle-operation-store --scenario should print the requested scenario")
    if lifecycle_scenario_payload["preflight"]["plannedWrites"][1]["writeMode"] != "prospective_binding":
        raise AssertionError("CLI lifecycle-operation-store method rollback should be prospective")
    pilot_lifecycle_scenario = run_cli("lifecycle-operation-store", "--scenario", "pilot-evidence-append")
    pilot_lifecycle_payload = json.loads(pilot_lifecycle_scenario.stdout)
    if pilot_lifecycle_payload["scenarioName"] != "pilot-evidence-append":
        raise AssertionError("CLI lifecycle-operation-store --scenario should print the requested pilot scenario")
    if pilot_lifecycle_payload["preflight"]["plannedWrites"][1]["recordType"] != "pilot_evidence_ledger_row":
        raise AssertionError("CLI lifecycle-operation-store pilot scenario should plan a pilot evidence ledger row")
    run_optional_drift_check(
        "lifecycle-operation-store",
        "--check",
        expected_stdout="checked lifecycle operation store",
        label="lifecycle-operation-store",
    )

    internal_api = run_cli("internal-api")
    internal_api_payload = json.loads(internal_api.stdout)
    if internal_api_payload["summary"]["operationCount"] != 14:
        raise AssertionError("CLI internal-api should expose the stable 14-operation surface")
    if internal_api_payload["summary"]["readOnlyOperationCount"] != 4:
        raise AssertionError("CLI internal-api should expose four read-only operations")
    if not internal_api_payload["summary"]["allEffectfulOperationsReceiptBacked"]:
        raise AssertionError("CLI internal-api should receipt-back effectful operations")
    if internal_api_payload["nonInterferenceBoundary"]["rawSqlExposed"]:
        raise AssertionError("CLI internal-api must not expose raw SQL")
    internal_operations = {
        item["operationName"]: item for item in internal_api_payload["operationSurface"]
    }
    database_status_operation = internal_operations["database_source_adapter_status"]
    if database_status_operation["operationKind"] != "read_only":
        raise AssertionError("CLI internal-api database source-adapter status should be read-only")
    if database_status_operation["returnsReadModels"] != ["source_adapter_runtime_status"]:
        raise AssertionError("CLI internal-api database source-adapter status read model drifted")
    internal_api_start = run_cli("internal-api", "--operation", "start_prediction")
    internal_api_start_payload = json.loads(internal_api_start.stdout)
    if internal_api_start_payload["operationName"] != "start_prediction":
        raise AssertionError("CLI internal-api --operation should print the requested operation")
    if "forecast.create" not in internal_api_start_payload["lifecycleOperations"]:
        raise AssertionError("CLI internal-api start_prediction should map to forecast.create")
    internal_api_database = run_cli("internal-api", "--operation", "database_source_adapter_status")
    internal_api_database_payload = json.loads(internal_api_database.stdout)
    if internal_api_database_payload["operationName"] != "database_source_adapter_status":
        raise AssertionError("CLI internal-api database source-adapter status operation drifted")
    if internal_api_database_payload["operationKind"] != "read_only":
        raise AssertionError("CLI internal-api database source-adapter status should be read-only")
    if internal_api_database_payload["requiresOperationReceipt"] is not False:
        raise AssertionError("CLI internal-api database source-adapter status should not require a receipt")
    if internal_api_database_payload["returnsReadModels"] != ["source_adapter_runtime_status"]:
        raise AssertionError("CLI internal-api database source-adapter status readback drifted")
    if internal_api_database_payload["rawSqlExposed"] is not False:
        raise AssertionError("CLI internal-api database source-adapter status must not expose raw SQL")
    internal_api_database_call = run_cli(
        "agent-call",
        "--operation",
        "internal_api",
        "--internal-operation",
        "database_source_adapter_status",
    )
    internal_api_database_call_payload = json.loads(internal_api_database_call.stdout)
    if internal_api_database_call_payload["payload"]["callStatus"] != "read_ready":
        raise AssertionError("CLI internal-api database source-adapter status call should be read-ready")
    if internal_api_database_call_payload["payload"]["operationReceiptId"] is not None:
        raise AssertionError("CLI internal-api database source-adapter status call should not return a receipt")
    if internal_api_database_call_payload["payload"]["readModelRefs"] != ["source_adapter_runtime_status"]:
        raise AssertionError("CLI internal-api database source-adapter status call read model drifted")
    if internal_api_database_call_payload["payload"]["executionBoundary"]["rawSqlExposed"] is not False:
        raise AssertionError("CLI internal-api database source-adapter status call must not expose raw SQL")
    internal_api_check = run_cli("internal-api", "--check")
    if "checked internal API" not in internal_api_check.stdout:
        raise AssertionError("CLI internal-api --check did not check generated output")

    workspace_registry = run_cli("prediction-workspace-registry")
    workspace_registry_payload = json.loads(workspace_registry.stdout)
    if workspace_registry_payload["summary"]["predictionCount"] != 2:
        raise AssertionError("CLI prediction-workspace-registry should expose two predictions")
    if workspace_registry_payload["summary"]["activePredictionCount"] != 1:
        raise AssertionError("CLI prediction-workspace-registry should expose one active prediction")
    registry_entries = {
        item["predictionId"]: item for item in workspace_registry_payload["predictions"]
    }
    if set(registry_entries) != {"prediction-001", "prediction-002"}:
        raise AssertionError("CLI prediction-workspace-registry prediction IDs drifted")
    if registry_entries["prediction-001"]["domainId"] != "domainweathertransitdelays-001":
        raise AssertionError("CLI prediction-workspace-registry active domain binding drifted")
    if registry_entries["prediction-002"]["status"] != "paused":
        raise AssertionError("CLI prediction-workspace-registry paused status drifted")
    registry_read_models = workspace_registry_payload["readModels"]
    if set(registry_read_models) != {
        "allPredictions",
        "activePredictions",
        "dueForecasts",
        "dueResolutions",
        "blockedOperations",
        "failedOperations",
        "sourceHealthBlockers",
        "calibrationProgress",
        "trackRecordProgress",
    }:
        raise AssertionError("CLI prediction-workspace-registry read model coverage drifted")
    if registry_read_models["dueForecasts"][0]["forecastId"] != "forecast-1301":
        raise AssertionError("CLI prediction-workspace-registry due forecast binding drifted")
    if registry_read_models["dueResolutions"][0]["resolutionJobId"] != "resolutionjob-1301":
        raise AssertionError("CLI prediction-workspace-registry due resolution binding drifted")
    if registry_read_models["blockedOperations"][0]["operationStatus"] != "blocked":
        raise AssertionError("CLI prediction-workspace-registry blocked operation readback drifted")
    if registry_read_models["failedOperations"][0]["operationStatus"] != "failed":
        raise AssertionError("CLI prediction-workspace-registry failed operation readback drifted")
    if registry_read_models["sourceHealthBlockers"][0]["sourceBindingId"] != "sourcebinding-002":
        raise AssertionError("CLI prediction-workspace-registry source-health blocker drifted")
    if not workspace_registry_payload["summary"]["readModelsPresent"]:
        raise AssertionError("CLI prediction-workspace-registry should expose workspace read models")
    registry_config_operations = {
        item["operationName"]: item for item in workspace_registry_payload["configurationLifecycleOperations"]
    }
    if set(registry_config_operations) != {
        "prediction.config_create",
        "prediction.config_update",
        "prediction.config_archive",
        "prediction.config_redact",
    }:
        raise AssertionError("CLI prediction-workspace-registry configuration operation coverage drifted")
    if registry_config_operations["prediction.config_archive"]["auditRecordKind"] != "archive_tombstone":
        raise AssertionError("CLI prediction-workspace-registry archive should use a tombstone")
    if registry_config_operations["prediction.config_redact"]["auditRecordKind"] != "redaction_receipt":
        raise AssertionError("CLI prediction-workspace-registry redact should use a redaction receipt")
    if any(item["rawConfigMutationAllowed"] for item in registry_config_operations.values()):
        raise AssertionError("CLI prediction-workspace-registry must block raw config mutation")
    if any(item["physicalDeleteAllowed"] for item in registry_config_operations.values()):
        raise AssertionError("CLI prediction-workspace-registry must replace physical delete")
    if not workspace_registry_payload["summary"]["configurationOperationsAuditBacked"]:
        raise AssertionError("CLI prediction-workspace-registry should audit-back config operations")
    registry_concurrency_controls = {
        item["predictionId"]: item for item in workspace_registry_payload["perPredictionConcurrencyControls"]
    }
    if set(registry_concurrency_controls) != {"prediction-001", "prediction-002"}:
        raise AssertionError("CLI prediction-workspace-registry concurrency control coverage drifted")
    if len({item["idempotencyNamespaceId"] for item in registry_concurrency_controls.values()}) != 2:
        raise AssertionError("CLI prediction-workspace-registry idempotency namespaces should be unique")
    if len({item["leaseId"] for item in registry_concurrency_controls.values()}) != 2:
        raise AssertionError("CLI prediction-workspace-registry lease IDs should be unique")
    if not all(item["crossPredictionConcurrencyAllowed"] for item in registry_concurrency_controls.values()):
        raise AssertionError("CLI prediction-workspace-registry should allow different prediction concurrency")
    if not all(item["samePredictionConcurrentMutationBlocked"] for item in registry_concurrency_controls.values()):
        raise AssertionError("CLI prediction-workspace-registry should block same-prediction races")
    registry_resource_controls = workspace_registry_payload["workspaceResourceControls"]
    if registry_resource_controls["currentActivePredictionCount"] > registry_resource_controls["maximumActivePredictions"]:
        raise AssertionError("CLI prediction-workspace-registry active prediction limit exceeded")
    if registry_resource_controls["currentQueuedOperationCount"] > registry_resource_controls["maximumQueuedOperations"]:
        raise AssertionError("CLI prediction-workspace-registry queued operation limit exceeded")
    if registry_resource_controls["currentReadbackBytes"] > registry_resource_controls["maximumReadbackBytes"]:
        raise AssertionError("CLI prediction-workspace-registry readback limit exceeded")
    registry_budgets = {
        item["predictionId"]: item for item in registry_resource_controls["perPredictionExecutionBudgets"]
    }
    if set(registry_budgets) != {"prediction-001", "prediction-002"}:
        raise AssertionError("CLI prediction-workspace-registry execution budget coverage drifted")
    if registry_budgets["prediction-001"]["budgetStatus"] != "within_budget":
        raise AssertionError("CLI prediction-workspace-registry active budget status drifted")
    if registry_budgets["prediction-002"]["budgetStatus"] != "blocked":
        raise AssertionError("CLI prediction-workspace-registry paused budget status drifted")
    if not workspace_registry_payload["summary"]["resourceControlsPresent"]:
        raise AssertionError("CLI prediction-workspace-registry should expose resource controls")
    registry_isolation_checks = {
        item["checkName"]: item for item in workspace_registry_payload["isolationChecks"]
    }
    if set(registry_isolation_checks) != {
        "record_write_scope",
        "source_binding_scope",
        "method_binding_scope",
        "read_model_scope",
    }:
        raise AssertionError("CLI prediction-workspace-registry isolation coverage drifted")
    if any(item["crossPredictionWriteAllowed"] for item in registry_isolation_checks.values()):
        raise AssertionError("CLI prediction-workspace-registry should block cross-prediction writes")
    if not all(item["samePredictionWriteAllowed"] for item in registry_isolation_checks.values()):
        raise AssertionError("CLI prediction-workspace-registry should keep same-prediction writes lease-gated")
    if not all(item["auditRecordRequired"] for item in registry_isolation_checks.values()):
        raise AssertionError("CLI prediction-workspace-registry should audit blocked isolation checks")
    if not workspace_registry_payload["summary"]["isolationChecksPresent"]:
        raise AssertionError("CLI prediction-workspace-registry should expose isolation checks")
    if workspace_registry_payload["executionBoundary"]["writesRegistryState"]:
        raise AssertionError("CLI prediction-workspace-registry must remain readback-only")
    workspace_registry_entry = run_cli("prediction-workspace-registry", "--prediction-id", "prediction-001")
    workspace_registry_entry_payload = json.loads(workspace_registry_entry.stdout)
    if workspace_registry_entry_payload["predictionId"] != "prediction-001":
        raise AssertionError("CLI prediction-workspace-registry --prediction-id should print the requested entry")
    workspace_registry_check = run_cli("prediction-workspace-registry", "--check")
    if "checked prediction workspace registry" not in workspace_registry_check.stdout:
        raise AssertionError("CLI prediction-workspace-registry --check did not check generated output")

    background_worker = run_cli("background-worker")
    background_worker_payload = json.loads(background_worker.stdout)
    if background_worker_payload["runtimeStatus"] != "bounded_local_worker_defined":
        raise AssertionError("CLI background-worker runtime status drifted")
    if background_worker_payload["summary"]["commandCount"] != 7:
        raise AssertionError("CLI background-worker command coverage drifted")
    if background_worker_payload["sidecarBoundary"]["networkListenerStarted"]:
        raise AssertionError("CLI background-worker must not start a network listener")
    background_worker_loop = run_cli("background-worker", "--view", "loop")
    background_worker_loop_payload = json.loads(background_worker_loop.stdout)
    if background_worker_loop_payload["loopStatus"] != "completed_dry_run":
        raise AssertionError("CLI background-worker loop should complete one dry-run tick")
    if background_worker_loop_payload["tickExecutions"][0]["internalApiOperation"] != "run_tick":
        raise AssertionError("CLI background-worker loop should call foreground-equivalent run_tick")
    if background_worker_loop_payload["tickExecutions"][0]["internalApiCall"]["dryRun"] is not True:
        raise AssertionError("CLI background-worker loop should keep the internal API call dry-run")
    if background_worker_loop_payload["resourceUsage"]["withinLimits"] is not True:
        raise AssertionError("CLI background-worker loop should stay within configured resource limits")
    background_worker_commit = run_cli("background-worker", "--view", "commit")
    background_worker_commit_payload = json.loads(background_worker_commit.stdout)
    if background_worker_commit_payload["lifecycleOperationName"] != "forecast.create":
        raise AssertionError("CLI background-worker commit should use forecast.create lifecycle operation")
    if background_worker_commit_payload["lifecycleResult"]["operationStatus"] != "committed":
        raise AssertionError("CLI background-worker commit should commit through the lifecycle store")
    if background_worker_commit_payload["leaseLifecycle"]["leaseReleased"] is not True:
        raise AssertionError("CLI background-worker commit should release its lease")
    if background_worker_commit_payload["executionBoundary"]["persistentStateWritten"] is not False:
        raise AssertionError("CLI background-worker commit check should not write persistent state")
    background_worker_control = run_cli("background-worker", "--view", "control")
    background_worker_control_payload = json.loads(background_worker_control.stdout)
    if background_worker_control_payload["controlStateStatus"] != "lifecycle_backed_control_state_checked":
        raise AssertionError("CLI background-worker control state status drifted")
    if background_worker_control_payload["summary"]["lifecycleReceiptsWritten"] != 4:
        raise AssertionError("CLI background-worker control should write four lifecycle receipts")
    if background_worker_control_payload["summary"]["leasesReleased"] != 4:
        raise AssertionError("CLI background-worker control should release all control leases")
    if background_worker_control_payload["healthReadback"]["workerState"] != "stopped":
        raise AssertionError("CLI background-worker health should read final stopped control state")
    if background_worker_control_payload["executionBoundary"]["persistentStateWritten"] is not False:
        raise AssertionError("CLI background-worker control check should not write persistent state")
    background_worker_sidecar = run_cli("background-worker", "--view", "sidecar")
    background_worker_sidecar_payload = json.loads(background_worker_sidecar.stdout)
    if background_worker_sidecar_payload["sidecarStatus"] != "checked_local_sidecar_semantics":
        raise AssertionError("CLI background-worker sidecar status drifted")
    if background_worker_sidecar_payload["normalChecksStartProcess"] is not False:
        raise AssertionError("CLI background-worker sidecar check should not start a process")
    if background_worker_sidecar_payload["activationReadback"]["heartbeatReadback"]["heartbeatStatus"] != "healthy_idle":
        raise AssertionError("CLI background-worker sidecar heartbeat drifted")
    if background_worker_sidecar_payload["activationReadback"]["shutdownReadback"]["shutdownStatus"] != "clean_shutdown_readback":
        raise AssertionError("CLI background-worker sidecar shutdown drifted")
    if background_worker_sidecar_payload["executionBoundary"]["hiddenDaemonStarted"] is not False:
        raise AssertionError("CLI background-worker sidecar must not start hidden daemon")
    background_worker_check = run_cli("background-worker", "--check")
    if "checked background worker runtime" not in background_worker_check.stdout:
        raise AssertionError("CLI background-worker --check did not check generated output")

    runtime_security = run_cli("runtime-security")
    runtime_security_payload = json.loads(runtime_security.stdout)
    if runtime_security_payload["securityStatus"] != "lightweight_runtime_hardening_checked":
        raise AssertionError("CLI runtime-security status drifted")
    if runtime_security_payload["dependencyBudget"]["runtimeDependencyCount"] != 0:
        raise AssertionError("CLI runtime-security should keep runtime dependencies at zero")
    if runtime_security_payload["summary"]["moduleBoundaryCount"] != 7:
        raise AssertionError("CLI runtime-security module boundary coverage drifted")
    if runtime_security_payload["executionBoundary"]["networkListenerStarted"] is not False:
        raise AssertionError("CLI runtime-security should not start a network listener")
    runtime_security_budget = run_cli("runtime-security", "--view", "budget")
    runtime_security_budget_payload = json.loads(runtime_security_budget.stdout)
    if runtime_security_budget_payload["coreRuntimeDependencyPolicy"] != "python_stdlib_only":
        raise AssertionError("CLI runtime-security budget should keep stdlib-only policy")
    if runtime_security_budget_payload["packageInstallRequiredForNormalChecks"] is not False:
        raise AssertionError("CLI runtime-security budget should not require normal installs")
    runtime_security_surfaces = run_cli("runtime-security", "--view", "surfaces")
    runtime_security_surface_payload = json.loads(runtime_security_surfaces.stdout)
    if len(runtime_security_surface_payload) != 5:
        raise AssertionError("CLI runtime-security surface coverage drifted")
    if any(item["credentialValuesStored"] for item in runtime_security_surface_payload):
        raise AssertionError("CLI runtime-security surfaces must not store credential values")
    if any(item["responseSizeLimitBytes"] > 65536 for item in runtime_security_surface_payload):
        raise AssertionError("CLI runtime-security response limits are too large")
    runtime_security_threats = run_cli("runtime-security", "--view", "threats")
    runtime_security_threat_payload = json.loads(runtime_security_threats.stdout)
    threat_names = {item["threatName"] for item in runtime_security_threat_payload}
    if "prompt_source_injection" not in threat_names or "lease_abuse" not in threat_names:
        raise AssertionError("CLI runtime-security threat model coverage drifted")
    if any(item["rawSensitiveDataExposed"] for item in runtime_security_threat_payload):
        raise AssertionError("CLI runtime-security threat notes should not expose raw sensitive data")
    runtime_security_blocked = run_cli("runtime-security", "--view", "blocked")
    runtime_security_blocked_payload = json.loads(runtime_security_blocked.stdout)
    blocked_cases = {item["caseName"]: item for item in runtime_security_blocked_payload}
    if blocked_cases["credential_value_in_record"]["rawValueEchoed"] is not False:
        raise AssertionError("CLI runtime-security blocked credential case must not echo raw values")
    runtime_security_boundary = run_cli("runtime-security", "--view", "boundary")
    runtime_security_boundary_payload = json.loads(runtime_security_boundary.stdout)
    if runtime_security_boundary_payload["hostedRuntimeRequired"] is not False:
        raise AssertionError("CLI runtime-security should not require hosted runtime")
    if runtime_security_boundary_payload["unboundedBackgroundLoopAllowed"] is not False:
        raise AssertionError("CLI runtime-security should block unbounded background loops")
    runtime_security_check = run_cli("runtime-security", "--check")
    if "checked runtime security hardening" not in runtime_security_check.stdout:
        raise AssertionError("CLI runtime-security --check did not check generated output")

    explain_fit = run_cli("explain-fit", "--goal", "add predictions to my app")
    if "Use OPE for:" not in explain_fit.stdout:
        raise AssertionError("CLI explain-fit should name OPE use cases")
    if "Bring yourself:" not in explain_fit.stdout:
        raise AssertionError("CLI explain-fit should name host-provided parts")
    if len(explain_fit.stdout.splitlines()) > 12:
        raise AssertionError("CLI explain-fit default output should remain compact")
    explain_fit_extensions = run_cli("explain-fit", "--view", "extension-points", "--output-format", "json")
    explain_fit_extensions_payload = json.loads(explain_fit_extensions.stdout)
    extension_keys = {item["extensionKey"] for item in explain_fit_extensions_payload}
    if extension_keys != {"source_adapter", "forecast_method", "resolver", "scorer", "host_app_wrapper"}:
        raise AssertionError("CLI explain-fit extension point coverage drifted")
    if any(item["createsHostedRuntime"] for item in explain_fit_extensions_payload):
        raise AssertionError("CLI explain-fit extension points must not create hosted runtime")
    explain_fit_byo = run_cli("explain-fit", "--view", "byo-model", "--output-format", "json")
    explain_fit_byo_payload = json.loads(explain_fit_byo.stdout)
    if explain_fit_byo_payload["modelFrameworkRequired"] is not False:
        raise AssertionError("CLI explain-fit BYO model path should be framework-neutral")
    if explain_fit_byo_payload["baselineComparisonRequired"] is not True:
        raise AssertionError("CLI explain-fit BYO model path should require baseline comparison")
    capabilities = run_cli("capabilities")
    capabilities_payload = json.loads(capabilities.stdout)
    capability_keys = {item["capabilityKey"] for item in capabilities_payload["helpsWith"]}
    if "forecast_contracts" not in capability_keys or "calibration_gates" not in capability_keys:
        raise AssertionError("CLI capabilities should expose forecast contracts and calibration gates")
    non_goal_keys = {item["nonGoalKey"] for item in capabilities_payload["doesNotProvide"]}
    if "frontend" not in non_goal_keys or "trained_model" not in non_goal_keys:
        raise AssertionError("CLI capabilities should expose frontend and trained model non-goals")
    adoption_eval = run_cli("adoption-eval", "--output-format", "json")
    adoption_eval_payload = json.loads(adoption_eval.stdout)
    if adoption_eval_payload["targetMinutes"] != 5:
        raise AssertionError("CLI adoption-eval target should remain five minutes")
    if adoption_eval_payload["passesWithoutNetwork"] is not True or adoption_eval_payload["writesState"] is not False:
        raise AssertionError("CLI adoption-eval must remain offline and non-mutating")
    prediction_agent_adoption_check = run_cli("explain-fit", "--check")
    if "checked prediction agent adoption" not in prediction_agent_adoption_check.stdout:
        raise AssertionError("CLI explain-fit --check did not check generated adoption output")

    prediction_goal_catalog = run_cli("prediction-goal-catalog")
    prediction_goal_catalog_payload = json.loads(prediction_goal_catalog.stdout)
    if prediction_goal_catalog_payload["catalogStatus"] != "checked_domain_agnostic_goal_catalog":
        raise AssertionError("CLI prediction-goal-catalog status drifted")
    if prediction_goal_catalog_payload["summary"]["goalExampleCount"] != 8:
        raise AssertionError("CLI prediction-goal-catalog should expose eight examples")
    if prediction_goal_catalog_payload["summary"]["classificationCount"] != 4:
        raise AssertionError("CLI prediction-goal-catalog classification coverage drifted")
    if prediction_goal_catalog_payload["summary"]["helsinkiDefaultNarrative"] is not False:
        raise AssertionError("CLI prediction-goal-catalog must not default to Helsinki")
    if prediction_goal_catalog_payload["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI prediction-goal-catalog must block quality claims")
    stockout_catalog = run_cli("prediction-goal-catalog", "--goal", "stockout_risk")
    stockout_catalog_payload = json.loads(stockout_catalog.stdout)
    if stockout_catalog_payload["classification"] != "forecastable":
        raise AssertionError("CLI prediction-goal-catalog stockout goal should be forecastable")
    catalog_summary = run_cli("prediction-goal-catalog", "--view", "summary")
    catalog_summary_payload = json.loads(catalog_summary.stdout)
    if catalog_summary_payload["view"] != "summary":
        raise AssertionError("CLI prediction-goal-catalog summary view drifted")
    prediction_goal_catalog_check = run_cli("prediction-goal-catalog", "--check")
    if "checked prediction goal catalog" not in prediction_goal_catalog_check.stdout:
        raise AssertionError("CLI prediction-goal-catalog --check did not check generated output")

    setup_engine = run_cli("setup-engine", "--goal", "add predictions to my app")
    setup_engine_payload = json.loads(setup_engine.stdout)
    if setup_engine_payload["engineSetupStatus"] != "checked_readback":
        raise AssertionError("CLI setup-engine status drifted")
    if setup_engine_payload["inputMode"] != "goal_text":
        raise AssertionError("CLI setup-engine goal-text input mode drifted")
    if setup_engine_payload["requestSummary"]["completenessStatus"] != "goal_text_only":
        raise AssertionError("CLI setup-engine goal-text request summary drifted")
    if setup_engine_payload["candidateForecastContracts"][0]["contractStatus"] != "forecastable":
        raise AssertionError("CLI setup-engine should expose a forecastable first candidate")
    if setup_engine_payload["candidateForecastContracts"][0]["baselineMethod"]["methodId"] != "historical_frequency_baseline":
        raise AssertionError("CLI setup-engine should start from the historical baseline")
    if setup_engine_payload["forecastCardPreview"]["forecastArtifactCreated"] is not False:
        raise AssertionError("CLI setup-engine forecast-card preview must not create artifacts")
    if setup_engine_payload["forecastCardPreview"]["probabilityAvailable"] is not False:
        raise AssertionError("CLI setup-engine forecast-card preview must not expose probability")
    if setup_engine_payload["forecastCardPreview"]["evidenceStatus"] != "source_intake_required":
        raise AssertionError("CLI setup-engine goal-text preview evidence status drifted")
    if setup_engine_payload["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("CLI setup-engine host wrapper should render before forecast artifacts")
    if "forecastCardPreview" not in setup_engine_payload["hostWrapper"]["renderSections"]:
        raise AssertionError("CLI setup-engine host wrapper should render forecast-card preview")
    if setup_engine_payload["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI setup-engine must keep quality claims blocked")
    setup_engine_request = run_cli(
        "setup-engine",
        "--request",
        "spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json",
        "--view",
        "request",
    )
    setup_engine_request_payload = json.loads(setup_engine_request.stdout)
    if setup_engine_request_payload["inputMode"] != "structured_request":
        raise AssertionError("CLI setup-engine structured request mode drifted")
    if setup_engine_request_payload["requestSummary"]["setupEngineRequestId"] != "setupenginerequest-001":
        raise AssertionError("CLI setup-engine request id drifted")
    if setup_engine_request_payload["requestSummary"]["readyForSourceIntake"] is not True:
        raise AssertionError("CLI setup-engine request should be source-intake ready")
    setup_engine_preview = run_cli(
        "setup-engine",
        "--request",
        "spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json",
        "--view",
        "forecast-card-preview",
    )
    setup_engine_preview_payload = json.loads(setup_engine_preview.stdout)
    if setup_engine_preview_payload["view"] != "forecast-card-preview":
        raise AssertionError("CLI setup-engine forecast-card-preview view drifted")
    if setup_engine_preview_payload["forecastCardPreview"]["generatedFrom"] != "structured_request":
        raise AssertionError("CLI setup-engine preview source drifted")
    if setup_engine_preview_payload["forecastCardPreview"]["evidenceStatus"] != "structured_sources_ready_for_intake":
        raise AssertionError("CLI setup-engine preview should be source-intake ready")
    if setup_engine_preview_payload["forecastCardPreview"]["probabilityAvailable"] is not False:
        raise AssertionError("CLI setup-engine preview must not expose probability")
    blocked_setup_engine_request = run_cli(
        "setup-engine",
        "--request",
        "spec/fixtures/setup-engine-requests/blocked-raw-crm-request.json",
        "--view",
        "request",
    )
    blocked_setup_engine_request_payload = json.loads(blocked_setup_engine_request.stdout)
    if blocked_setup_engine_request_payload["requestSummary"]["completenessStatus"] != "blocked_by_unsafe_inputs":
        raise AssertionError("CLI setup-engine blocked request should report unsafe inputs")
    setup_engine_sources = run_cli("setup-engine", "--goal", "add predictions to my app", "--view", "sources")
    setup_engine_sources_payload = json.loads(setup_engine_sources.stdout)
    if setup_engine_sources_payload["view"] != "sources":
        raise AssertionError("CLI setup-engine sources view drifted")
    setup_role_names = {item["roleName"] for item in setup_engine_sources_payload["requiredSourceRoles"]}
    if {"forecast_time_signal", "historical_outcome", "resolution_outcome"} - setup_role_names:
        raise AssertionError("CLI setup-engine sources should expose domain-agnostic source roles")
    setup_engine_examples = run_cli("setup-engine", "--goal", "add predictions to my app", "--view", "examples")
    setup_engine_examples_payload = json.loads(setup_engine_examples.stdout)
    if setup_engine_examples_payload["catalogBinding"]["predictionGoalCatalogId"] != "predictiongoalcatalog-001":
        raise AssertionError("CLI setup-engine examples should bind prediction goal catalog")
    setup_example_keys = {item["goalKey"] for item in setup_engine_examples_payload["exampleGoals"]}
    if "public_transit_disruption_risk" not in setup_example_keys or "stockout_risk" not in setup_example_keys:
        raise AssertionError("CLI setup-engine examples should expose generic catalog examples")
    setup_engine_check = run_cli("setup-engine", "--check")
    if "checked setup engine" not in setup_engine_check.stdout:
        raise AssertionError("CLI setup-engine --check did not check generated output")

    agent_implementation_kit = run_cli("agent-implementation-kit")
    agent_implementation_kit_payload = json.loads(agent_implementation_kit.stdout)
    if agent_implementation_kit_payload["kitStatus"] != "agent_prediction_implementation_kit_checked":
        raise AssertionError("CLI agent-implementation-kit status drifted")
    if agent_implementation_kit_payload["summary"]["manualStepCount"] != 12:
        raise AssertionError("CLI agent-implementation-kit manual step count drifted")
    if agent_implementation_kit_payload["summary"]["quickstartStepCount"] != 5:
        raise AssertionError("CLI agent-implementation-kit quickstart step count drifted")
    if agent_implementation_kit_payload["executionBoundary"]["questionDiscoveryCreatesForecastArtifacts"] is not False:
        raise AssertionError("CLI agent-implementation-kit discovery must not create forecast artifacts")
    agent_implementation_quickstart = run_cli("agent-implementation-kit", "--view", "quickstart")
    agent_implementation_quickstart_payload = json.loads(agent_implementation_quickstart.stdout)
    if agent_implementation_quickstart_payload["frontDoorStatus"] != "implementation_follow_up_entrypoint":
        raise AssertionError("CLI agent-implementation-kit quickstart status drifted")
    if agent_implementation_quickstart_payload["steps"][0]["stepKey"] != "start_with_setup_engine":
        raise AssertionError("CLI agent-implementation-kit quickstart first step drifted")
    if agent_implementation_quickstart_payload["steps"][1]["stepKey"] != "render_host_wrapper_setup_plan":
        raise AssertionError("CLI agent-implementation-kit quickstart setup-plan step drifted")
    step_two_command = agent_implementation_quickstart_payload["steps"][1]["command"]
    if "examples/embed-ope-prediction-feature/host_wrapper.py" not in step_two_command:
        raise AssertionError("CLI agent-implementation-kit quickstart should render the host wrapper setup plan")
    wrapper_call_sequence = agent_implementation_quickstart_payload["copyableWrapper"]["callSequence"]
    if wrapper_call_sequence[:2] != ["setup_engine", "render_setup_engine_host_wrapper"]:
        raise AssertionError("CLI agent-implementation-kit wrapper sequence should render setup engine before forecasts")
    if agent_implementation_quickstart_payload["copyableWrapper"]["storesCredentialValues"] is not False:
        raise AssertionError("CLI agent-implementation-kit quickstart wrapper must not store credentials")
    if agent_implementation_quickstart_payload["hostedRuntimeRequired"] is not False:
        raise AssertionError("CLI agent-implementation-kit quickstart must not require hosted runtime")
    agent_implementation_manual = run_cli("agent-implementation-kit", "--view", "manual")
    agent_implementation_manual_payload = json.loads(agent_implementation_manual.stdout)
    manual_steps = [item["stepKey"] for item in agent_implementation_manual_payload["steps"]]
    if manual_steps[0] != "detect_decision_under_uncertainty" or manual_steps[-1] != "inspect_calibration":
        raise AssertionError("CLI agent-implementation-kit manual step order drifted")
    agent_implementation_intake = run_cli("agent-implementation-kit", "--view", "intake")
    agent_implementation_intake_payload = json.loads(agent_implementation_intake.stdout)
    intake_fields = {item["fieldName"] for item in agent_implementation_intake_payload["requiredFields"]}
    if "decisionToSupport" not in intake_fields or "approvedSourceRefs" not in intake_fields:
        raise AssertionError("CLI agent-implementation-kit intake fields drifted")
    if agent_implementation_intake_payload["credentialValuesAccepted"] is not False:
        raise AssertionError("CLI agent-implementation-kit intake must block credential values")
    agent_implementation_candidates = run_cli("agent-implementation-kit", "--view", "candidates")
    agent_implementation_candidates_payload = json.loads(agent_implementation_candidates.stdout)
    candidate_rows = {item["candidateStatus"]: item for item in agent_implementation_candidates_payload}
    if set(candidate_rows) != {"forecastable", "needs_clarification", "blocked", "rejected"}:
        raise AssertionError("CLI agent-implementation-kit candidate status coverage drifted")
    if candidate_rows["forecastable"]["routesToExistingSurfaces"] is not True:
        raise AssertionError("CLI agent-implementation-kit forecastable candidate should route to existing surfaces")
    agent_implementation_validation = run_cli("agent-implementation-kit", "--view", "validation")
    agent_implementation_validation_payload = json.loads(agent_implementation_validation.stdout)
    if any(item["createsForecastArtifacts"] for item in agent_implementation_validation_payload):
        raise AssertionError("CLI agent-implementation-kit validation must not create forecast artifacts")
    agent_implementation_adapters = run_cli("agent-implementation-kit", "--view", "adapters")
    agent_implementation_adapters_payload = json.loads(agent_implementation_adapters.stdout)
    adapter_rows = {item["adapterName"]: item for item in agent_implementation_adapters_payload}
    if adapter_rows["future_http_queue"]["implementedStatus"] != "future_transport_only":
        raise AssertionError("CLI agent-implementation-kit should keep HTTP/queue future-only")
    if any(item["hiddenServiceRequired"] for item in agent_implementation_adapters_payload):
        raise AssertionError("CLI agent-implementation-kit adapters should not require hidden services")
    agent_implementation_templates = run_cli("agent-implementation-kit", "--view", "templates")
    agent_implementation_templates_payload = json.loads(agent_implementation_templates.stdout)
    if len(agent_implementation_templates_payload) != 3:
        raise AssertionError("CLI agent-implementation-kit starter template coverage drifted")
    if any(item["storesCredentials"] for item in agent_implementation_templates_payload):
        raise AssertionError("CLI agent-implementation-kit templates must not store credentials")
    agent_implementation_blocked = run_cli("agent-implementation-kit", "--view", "blocked")
    agent_implementation_blocked_payload = json.loads(agent_implementation_blocked.stdout)
    blocked_guidance = {item["behaviorKey"]: item for item in agent_implementation_blocked_payload}
    if blocked_guidance["free_form_oracle"]["allowed"] is not False:
        raise AssertionError("CLI agent-implementation-kit must block free-form oracle behavior")
    agent_implementation_boundary = run_cli("agent-implementation-kit", "--view", "boundary")
    agent_implementation_boundary_payload = json.loads(agent_implementation_boundary.stdout)
    if agent_implementation_boundary_payload["credentialValuesStored"] is not False:
        raise AssertionError("CLI agent-implementation-kit boundary must block credential storage")
    if agent_implementation_boundary_payload["automaticMethodUpgradeAllowed"] is not False:
        raise AssertionError("CLI agent-implementation-kit boundary must block automatic method upgrades")
    agent_implementation_check = run_cli("agent-implementation-kit", "--check")
    if "checked agent implementation kit" not in agent_implementation_check.stdout:
        raise AssertionError("CLI agent-implementation-kit --check did not check generated output")

    agent_integration = run_cli("agent-integrate")
    agent_integration_payload = json.loads(agent_integration.stdout)
    if agent_integration_payload["integrationStatus"] != "agent_integration_golden_path_checked":
        raise AssertionError("CLI agent-integrate status drifted")
    if agent_integration_payload["summary"]["firstForecastFastTargetMet"] is not True:
        raise AssertionError("CLI agent-integrate should meet the fast first forecast target")
    if agent_integration_payload["executionBoundary"]["hostedRuntimeImplemented"] is not False:
        raise AssertionError("CLI agent-integrate must not claim hosted runtime")
    agent_integration_candidates = run_cli("agent-integrate", "--view", "candidates")
    agent_integration_candidate_payload = json.loads(agent_integration_candidates.stdout)
    integration_candidates = {item["caseKey"]: item for item in agent_integration_candidate_payload}
    if integration_candidates["helsinki_surface_transit_peak_delay"]["status"] != "forecastable":
        raise AssertionError("CLI agent-integrate should expose forecastable Helsinki candidate")
    if integration_candidates["vague_next_week_transit"]["status"] != "needs_clarification":
        raise AssertionError("CLI agent-integrate should mark vague next-week transit as needs_clarification")
    if "raw_sql_query" not in integration_candidates["raw_sql_query"]["reasonCodes"]:
        raise AssertionError("CLI agent-integrate should expose raw SQL blocker code")
    agent_integration_guided = run_cli("agent-integrate", "--run-guided", "--case", "accepted_adapter_output")
    agent_integration_guided_payload = json.loads(agent_integration_guided.stdout)
    if agent_integration_guided_payload["guidedStatus"] != "forecast_card_ready":
        raise AssertionError("CLI agent-integrate accepted guided case should reach a forecast card")
    if agent_integration_guided_payload["toolCallCount"] > 3:
        raise AssertionError("CLI agent-integrate accepted guided case should stay within three calls")
    if agent_integration_guided_payload["forecastId"] != "forecast-1102":
        raise AssertionError("CLI agent-integrate accepted guided case should bind forecast-1102")
    agent_integration_blocked = run_cli("agent-integrate", "--run-guided", "--case", "missing_weather_source")
    agent_integration_blocked_payload = json.loads(agent_integration_blocked.stdout)
    if agent_integration_blocked_payload["guidedStatus"] != "blocked":
        raise AssertionError("CLI agent-integrate blocked guided case should stay blocked")
    if agent_integration_blocked_payload["forecastId"] is not None:
        raise AssertionError("CLI agent-integrate blocked guided case must not bind a forecast")
    agent_integration_agent_call = run_cli(
        "agent-call",
        "--operation",
        "agent_integration_guided_forecast",
        "--case",
        "accepted_adapter_output",
    )
    agent_integration_agent_call_payload = json.loads(agent_integration_agent_call.stdout)
    if agent_integration_agent_call_payload["payload"]["forecastCardCommand"] != agent_integration_guided_payload["forecastCardCommand"]:
        raise AssertionError("CLI agent-call guided integration should match agent-integrate forecast-card command")
    agent_integration_check = run_cli("agent-integrate", "--check")
    if "checked agent integration golden path" not in agent_integration_check.stdout:
        raise AssertionError("CLI agent-integrate --check did not check generated output")

    agent_guidance_summary = run_cli("agent-guide", "--section", "summary")
    agent_guidance_summary_payload = json.loads(agent_guidance_summary.stdout)
    if agent_guidance_summary_payload["guidanceCaseCount"] != 5:
        raise AssertionError("CLI agent-guide should expose five guidance cases")
    if agent_guidance_summary_payload["promptPlannerReady"] is not True:
        raise AssertionError("CLI agent-guide should expose a ready prompt planner")
    if agent_guidance_summary_payload["domainAgnosticFlowReady"] is not True:
        raise AssertionError("CLI agent-guide should expose domain-agnostic setup flow")
    if agent_guidance_summary_payload["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI agent-guide must not allow quality claims")
    agent_guidance_generic = run_cli("agent-guide", "--section", "generic")
    agent_guidance_generic_payload = json.loads(agent_guidance_generic.stdout)
    if agent_guidance_generic_payload["flowStatus"] != "checked_domain_agnostic_setup_flow":
        raise AssertionError("CLI agent-guide generic flow status drifted")
    if 'python3 scripts/ope.py setup-engine --goal "<host prediction goal>"' not in agent_guidance_generic_payload["safeNextCommands"]:
        raise AssertionError("CLI agent-guide generic flow should route through setup-engine")
    if agent_guidance_generic_payload["keepsHelsinkiAsExample"] is not True:
        raise AssertionError("CLI agent-guide generic flow should keep Helsinki as one example")
    agent_guidance_clarify = run_cli("agent-guide", "--case", "needs_clarification")
    agent_guidance_clarify_payload = json.loads(agent_guidance_clarify.stdout)
    if agent_guidance_clarify_payload["agentNextMove"] != "ask_user":
        raise AssertionError("CLI agent-guide clarification case should ask the user")
    if len(agent_guidance_clarify_payload["questionsToAsk"]) != 4:
        raise AssertionError("CLI agent-guide should expose four Helsinki clarification questions")
    agent_guidance_check = run_cli("agent-guide", "--check")
    if "checked agent guidance" not in agent_guidance_check.stdout:
        raise AssertionError("CLI agent-guide --check did not check generated output")

    postgres_compatibility = run_cli("postgres-compatibility")
    postgres_compatibility_payload = json.loads(postgres_compatibility.stdout)
    if postgres_compatibility_payload["compatibilityStatus"] != "sqlite_to_postgres_semantics_checked":
        raise AssertionError("CLI postgres-compatibility status drifted")
    if postgres_compatibility_payload["summary"]["tableCount"] != 8:
        raise AssertionError("CLI postgres-compatibility table count drifted")
    if postgres_compatibility_payload["summary"]["scenarioCount"] != len(SCENARIO_NAMES):
        raise AssertionError("CLI postgres-compatibility scenario count drifted")
    if postgres_compatibility_payload["postgresRuntimeImplemented"] is not False:
        raise AssertionError("CLI postgres-compatibility must not claim a Postgres runtime")
    postgres_boundary = run_cli("postgres-compatibility", "--view", "boundary")
    postgres_boundary_payload = json.loads(postgres_boundary.stdout)
    if postgres_boundary_payload["postgresConnectionOpened"] is not False:
        raise AssertionError("CLI postgres-compatibility boundary must not open Postgres")
    if postgres_boundary_payload["schemaMigrationExecuted"] is not False:
        raise AssertionError("CLI postgres-compatibility boundary must not execute migrations")
    postgres_scenarios = run_cli("postgres-compatibility", "--view", "scenarios")
    postgres_scenario_payload = json.loads(postgres_scenarios.stdout)
    if postgres_scenario_payload[1]["expectedPostgresBehavior"] != "return_existing_receipt":
        raise AssertionError("CLI postgres-compatibility retry behavior drifted")
    postgres_scenario_by_name = {item["scenarioName"]: item for item in postgres_scenario_payload}
    if postgres_scenario_by_name["json-state-import"]["migrationBoundary"] != "explicit_receipt_backed_import":
        raise AssertionError("CLI postgres-compatibility migration boundary drifted")
    if postgres_scenario_by_name["pilot-evidence-append"]["operationName"] != "evidence.append":
        raise AssertionError("CLI postgres-compatibility should include pilot evidence append")
    postgres_check = run_cli("postgres-compatibility", "--check")
    if "checked postgres compatibility" not in postgres_check.stdout:
        raise AssertionError("CLI postgres-compatibility --check did not check generated output")

    database_runtime = run_cli("database-source-adapter-runtime")
    database_runtime_payload = json.loads(database_runtime.stdout)
    if database_runtime_payload["runtimeStatus"] != "approved_database_source_adapter_runtime_checked":
        raise AssertionError("CLI database-source-adapter-runtime status drifted")
    if database_runtime_payload["summary"]["caseCount"] != 9:
        raise AssertionError("CLI database-source-adapter-runtime case count drifted")
    if database_runtime_payload["summary"]["approvedExecutionPathCount"] != 1:
        raise AssertionError("CLI database-source-adapter-runtime should expose one approved execution path")
    if database_runtime_payload["summary"]["blockedCaseCount"] != 8:
        raise AssertionError("CLI database-source-adapter-runtime blocked count drifted")
    if database_runtime_payload["executionBoundary"]["normalChecksConnectToDatabase"] is not False:
        raise AssertionError("CLI database-source-adapter-runtime must not connect to databases in normal checks")
    if database_runtime_payload["executionBoundary"]["credentialValuesStored"] is not False:
        raise AssertionError("CLI database-source-adapter-runtime must not store credential values")
    database_approved = run_cli("database-source-adapter-runtime", "--case", "approved_fixture")
    database_approved_payload = json.loads(database_approved.stdout)
    if database_approved_payload["canEnterSourceAdapterIntake"] is not True:
        raise AssertionError("CLI database-source-adapter-runtime approved fixture should enter adapter intake")
    if database_approved_payload["sanitizedAdapterOutput"]["provenanceSummary"]["rawRowsIncluded"] is not False:
        raise AssertionError("CLI database-source-adapter-runtime approved fixture must not include raw rows")
    if database_approved_payload["sanitizedAdapterOutput"]["queryBoundarySummary"]["rawSqlIncluded"] is not False:
        raise AssertionError("CLI database-source-adapter-runtime approved fixture must not include raw SQL")
    database_blocked = run_cli("database-source-adapter-runtime", "--view", "blocked")
    database_blocked_payload = json.loads(database_blocked.stdout)
    if len(database_blocked_payload) != 8:
        raise AssertionError("CLI database-source-adapter-runtime blocked view should expose eight cases")
    if any(item["canEnterSourceAdapterIntake"] for item in database_blocked_payload):
        raise AssertionError("CLI database-source-adapter-runtime blocked cases must stop before adapter intake")
    if any(item["credentialValuesStored"] for item in database_blocked_payload):
        raise AssertionError("CLI database-source-adapter-runtime blocked cases must not store credentials")
    database_boundary = run_cli("database-source-adapter-runtime", "--view", "boundary")
    database_boundary_payload = json.loads(database_boundary.stdout)
    if any(database_boundary_payload.values()):
        raise AssertionError("CLI database-source-adapter-runtime boundary flags should all stay false")
    database_check = run_cli("database-source-adapter-runtime", "--check")
    if "checked database source-adapter runtime" not in database_check.stdout:
        raise AssertionError("CLI database-source-adapter-runtime --check did not check generated output")

    opp_provider = run_cli("opp-provider-adapter")
    opp_provider_payload = json.loads(opp_provider.stdout)
    if opp_provider_payload["providerAdapterStatus"] != "optional_opp_provider_adapter_checked":
        raise AssertionError("CLI opp-provider-adapter status drifted")
    if opp_provider_payload["adapterScope"] != "interop_mapping_over_ope_lifecycle_records":
        raise AssertionError("CLI opp-provider-adapter scope drifted")
    if opp_provider_payload["summary"]["requestMappingCount"] != 8:
        raise AssertionError("CLI opp-provider-adapter request mapping count drifted")
    if opp_provider_payload["protocolBoundary"]["oppReplacesOpeLifecycleRecords"] is not False:
        raise AssertionError("CLI opp-provider-adapter must not replace OPE records")
    if opp_provider_payload["protocolBoundary"]["httpRuntimeImplemented"] is not False:
        raise AssertionError("CLI opp-provider-adapter must keep HTTP runtime future")
    opp_agent_card = run_cli("opp-provider-adapter", "--view", "agent-card")
    opp_agent_card_payload = json.loads(opp_agent_card.stdout)
    if opp_agent_card_payload["advertisedRuntime"] != "local_cli_fixture_only":
        raise AssertionError("CLI opp-provider-adapter Agent Card runtime drifted")
    if opp_agent_card_payload["httpEndpointAdvertised"] is not False:
        raise AssertionError("CLI opp-provider-adapter Agent Card must not advertise HTTP")
    if opp_agent_card_payload["supportedPricingModes"] != ["free_local_fixture"]:
        raise AssertionError("CLI opp-provider-adapter Agent Card pricing drifted")
    opp_accepted = run_cli("opp-provider-adapter", "--case", "accepted_forecast_card")
    opp_accepted_payload = json.loads(opp_accepted.stdout)
    if opp_accepted_payload["caseStatus"] != "response_ready":
        raise AssertionError("CLI opp-provider-adapter accepted case status drifted")
    if opp_accepted_payload["predictionResponse"]["probability"] != opp_accepted_payload["opeForecastCard"]["probability"]:
        raise AssertionError("CLI opp-provider-adapter response probability should come from OPE card")
    if opp_accepted_payload["predictionResponse"]["audit"]["forecastId"] != "forecast-602":
        raise AssertionError("CLI opp-provider-adapter accepted response forecast binding drifted")
    if opp_accepted_payload["predictionResponse"]["audit"]["evidenceTraceId"] != "forecast-602":
        raise AssertionError("CLI opp-provider-adapter evidence trace binding drifted")
    if opp_accepted_payload["forecastArtifactsCreated"] is not False:
        raise AssertionError("CLI opp-provider-adapter accepted case must not create artifacts")
    opp_blocked = run_cli("opp-provider-adapter", "--view", "blocked")
    opp_blocked_payload = json.loads(opp_blocked.stdout)
    if len(opp_blocked_payload) != 5:
        raise AssertionError("CLI opp-provider-adapter blocked view should expose five cases")
    if any(item["forecastArtifactsCreated"] for item in opp_blocked_payload):
        raise AssertionError("CLI opp-provider-adapter blocked cases must not create artifacts")
    if any(item["opeRecordsMutated"] for item in opp_blocked_payload):
        raise AssertionError("CLI opp-provider-adapter blocked cases must not mutate OPE records")
    opp_boundary = run_cli("opp-provider-adapter", "--view", "boundary")
    opp_boundary_payload = json.loads(opp_boundary.stdout)
    if opp_boundary_payload["opeRecordsAuthoritative"] is not True:
        raise AssertionError("CLI opp-provider-adapter boundary should keep OPE records authoritative")
    for key in [
        "httpRuntimeImplemented",
        "sseRuntimeImplemented",
        "paymentSettlementImplemented",
        "aggregationRuntimeImplemented",
        "networkListenerStarted",
        "normalChecksUseNetwork",
        "qualityClaimsUpgraded",
    ]:
        if opp_boundary_payload[key] is not False:
            raise AssertionError(f"CLI opp-provider-adapter boundary {key} should stay false")
    opp_check = run_cli("opp-provider-adapter", "--check")
    if "checked OPP provider adapter" not in opp_check.stdout:
        raise AssertionError("CLI opp-provider-adapter --check did not check generated output")

    persistent_sqlite_policy = run_cli("persistent-sqlite-policy")
    persistent_sqlite_policy_payload = json.loads(persistent_sqlite_policy.stdout)
    if persistent_sqlite_policy_payload["policyStatus"] != "persistent_sqlite_path_policy_checked":
        raise AssertionError("CLI persistent-sqlite-policy status drifted")
    if persistent_sqlite_policy_payload["decisionStatus"] != "explicit_opt_in_ready_not_default":
        raise AssertionError("CLI persistent-sqlite-policy decision status drifted")
    if persistent_sqlite_policy_payload["summary"]["caseCount"] != 10:
        raise AssertionError("CLI persistent-sqlite-policy case count drifted")
    if persistent_sqlite_policy_payload["summary"]["blockedCaseCount"] != 8:
        raise AssertionError("CLI persistent-sqlite-policy blocked count drifted")
    if persistent_sqlite_policy_payload["summary"]["readyCaseCount"] != 2:
        raise AssertionError("CLI persistent-sqlite-policy ready count drifted")
    if persistent_sqlite_policy_payload["normalChecksUseEphemeralSqlite"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy must keep normal checks ephemeral")
    if persistent_sqlite_policy_payload["persistentSqliteDefaultEnabled"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy must not enable persistent SQLite by default")
    if persistent_sqlite_policy_payload["executionBoundary"]["normalChecksCreatePersistentDatabase"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy must not create persistent databases in normal checks")
    if persistent_sqlite_policy_payload["executionBoundary"]["credentialValuesStored"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy must not store credential values")
    persistent_sqlite_approved = run_cli("persistent-sqlite-policy", "--case", "approved_workspace_path")
    persistent_sqlite_approved_payload = json.loads(persistent_sqlite_approved.stdout)
    if persistent_sqlite_approved_payload["caseStatus"] != "persistent_path_ready_for_explicit_write":
        raise AssertionError("CLI persistent-sqlite-policy approved path status drifted")
    if persistent_sqlite_approved_payload["requiresExplicitWriteFlag"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy approved path should require explicit write")
    if persistent_sqlite_approved_payload["normalChecksCreatePersistentDatabase"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy approved path must not create DB in normal checks")
    persistent_sqlite_blocked = run_cli("persistent-sqlite-policy", "--view", "blocked")
    persistent_sqlite_blocked_payload = json.loads(persistent_sqlite_blocked.stdout)
    if len(persistent_sqlite_blocked_payload) != 8:
        raise AssertionError("CLI persistent-sqlite-policy blocked view should expose eight cases")
    if any(item["persistentDatabaseCreated"] for item in persistent_sqlite_blocked_payload):
        raise AssertionError("CLI persistent-sqlite-policy blocked cases must not create persistent DBs")
    if any(item["operationReceiptsWritten"] for item in persistent_sqlite_blocked_payload):
        raise AssertionError("CLI persistent-sqlite-policy blocked cases must not write receipts")
    if any(item["sanitizedDiagnosticsOnly"] is not True for item in persistent_sqlite_blocked_payload):
        raise AssertionError("CLI persistent-sqlite-policy blocked cases should keep diagnostics sanitized")
    persistent_sqlite_migration = run_cli("persistent-sqlite-policy", "--view", "migration")
    persistent_sqlite_migration_payload = json.loads(persistent_sqlite_migration.stdout)
    if persistent_sqlite_migration_payload["automaticMigrationAllowed"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy must block automatic migration")
    if persistent_sqlite_migration_payload["dryRunRequiredBeforeWrite"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy should require migration dry-run")
    if persistent_sqlite_migration_payload["backupRequiredBeforeWrite"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy should require backup before migration")
    if persistent_sqlite_migration_payload["historicalForecastRewriteAllowed"] is not False:
        raise AssertionError("CLI persistent-sqlite-policy must not rewrite forecast history")
    persistent_sqlite_backup_lock = run_cli("persistent-sqlite-policy", "--view", "backup-lock")
    persistent_sqlite_backup_lock_payload = json.loads(persistent_sqlite_backup_lock.stdout)
    if persistent_sqlite_backup_lock_payload["sqliteBusyTimeoutMs"] != 5000:
        raise AssertionError("CLI persistent-sqlite-policy busy timeout drifted")
    if persistent_sqlite_backup_lock_payload["operationLeaseAlignmentRequired"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy should require operation lease alignment")
    if persistent_sqlite_backup_lock_payload["staleLockRecoveryRequiresReceipt"] is not True:
        raise AssertionError("CLI persistent-sqlite-policy should require stale lock recovery receipts")
    persistent_sqlite_boundary = run_cli("persistent-sqlite-policy", "--view", "boundary")
    persistent_sqlite_boundary_payload = json.loads(persistent_sqlite_boundary.stdout)
    if any(persistent_sqlite_boundary_payload.values()):
        raise AssertionError("CLI persistent-sqlite-policy boundary flags should all stay false")
    persistent_sqlite_check = run_cli("persistent-sqlite-policy", "--check")
    if "checked persistent SQLite policy" not in persistent_sqlite_check.stdout:
        raise AssertionError("CLI persistent-sqlite-policy --check did not check generated output")

    lifecycle_lease_policy = run_cli("lifecycle-lease-policy")
    lifecycle_lease_policy_payload = json.loads(lifecycle_lease_policy.stdout)
    if lifecycle_lease_policy_payload["policyStatus"] != "lifecycle_operation_lease_policy_checked":
        raise AssertionError("CLI lifecycle-lease-policy status drifted")
    if (
        lifecycle_lease_policy_payload["decisionStatus"]
        != "strict_leases_for_race_prone_writes_idempotency_for_append_only_receipts"
    ):
        raise AssertionError("CLI lifecycle-lease-policy decision status drifted")
    if lifecycle_lease_policy_payload["summary"]["operationCount"] != 14:
        raise AssertionError("CLI lifecycle-lease-policy operation count drifted")
    if lifecycle_lease_policy_payload["summary"]["strictLeaseCount"] != 9:
        raise AssertionError("CLI lifecycle-lease-policy strict lease count drifted")
    if lifecycle_lease_policy_payload["summary"]["idempotencyOnlyCount"] != 5:
        raise AssertionError("CLI lifecycle-lease-policy idempotency-only count drifted")
    if lifecycle_lease_policy_payload["summary"]["conflictCaseCount"] != 8:
        raise AssertionError("CLI lifecycle-lease-policy conflict case count drifted")
    if lifecycle_lease_policy_payload["normalChecksAcquireLeases"] is not False:
        raise AssertionError("CLI lifecycle-lease-policy must not acquire leases in normal checks")
    if lifecycle_lease_policy_payload["allEffectfulOperationsRequireIdempotency"] is not True:
        raise AssertionError("CLI lifecycle-lease-policy should require idempotency for all effectful operations")
    for key in ["normalChecksWriteState", "leasesAcquiredByReadback", "rawCrudExposed"]:
        if lifecycle_lease_policy_payload["executionBoundary"][key] is not False:
            raise AssertionError(f"CLI lifecycle-lease-policy boundary {key} should stay false")
    lifecycle_lease_strict = run_cli("lifecycle-lease-policy", "--view", "strict")
    lifecycle_lease_strict_payload = json.loads(lifecycle_lease_strict.stdout)
    if len(lifecycle_lease_strict_payload) != 9:
        raise AssertionError("CLI lifecycle-lease-policy strict view should expose nine operations")
    if any(item["guardMode"] != "strict_lease" or item["leaseRequired"] is not True for item in lifecycle_lease_strict_payload):
        raise AssertionError("CLI lifecycle-lease-policy strict operations should require leases")
    if any(item["leaseKeyTemplate"] == "none" for item in lifecycle_lease_strict_payload):
        raise AssertionError("CLI lifecycle-lease-policy strict operations should expose lease key templates")
    if any(item["normalChecksAcquireLease"] for item in lifecycle_lease_strict_payload):
        raise AssertionError("CLI lifecycle-lease-policy strict readback must not acquire leases")
    lifecycle_lease_idempotency = run_cli("lifecycle-lease-policy", "--view", "idempotency")
    lifecycle_lease_idempotency_payload = json.loads(lifecycle_lease_idempotency.stdout)
    if len(lifecycle_lease_idempotency_payload) != 5:
        raise AssertionError("CLI lifecycle-lease-policy idempotency view should expose five operations")
    if any(item["guardMode"] != "idempotency_only" or item["leaseRequired"] for item in lifecycle_lease_idempotency_payload):
        raise AssertionError("CLI lifecycle-lease-policy idempotency-only operations should not require leases")
    if any(item["leaseKeyTemplate"] != "none" for item in lifecycle_lease_idempotency_payload):
        raise AssertionError("CLI lifecycle-lease-policy idempotency-only operations should not expose lease key templates")
    lifecycle_lease_recalculate = run_cli("lifecycle-lease-policy", "--operation", "forecast.recalculate")
    lifecycle_lease_recalculate_payload = json.loads(lifecycle_lease_recalculate.stdout)
    if lifecycle_lease_recalculate_payload["policyReason"] != "append_history_entries_are_idempotent_by_source_hash":
        raise AssertionError("CLI lifecycle-lease-policy recalculation reason drifted")
    if lifecycle_lease_recalculate_payload["blockedConflictStatus"] != "return_existing_receipt_or_block_mismatch":
        raise AssertionError("CLI lifecycle-lease-policy recalculation conflict policy drifted")
    lifecycle_lease_cases = run_cli("lifecycle-lease-policy", "--view", "cases")
    lifecycle_lease_cases_payload = json.loads(lifecycle_lease_cases.stdout)
    if len(lifecycle_lease_cases_payload) != 8:
        raise AssertionError("CLI lifecycle-lease-policy cases view should expose eight cases")
    if any(item["operationReceiptsWritten"] for item in lifecycle_lease_cases_payload):
        raise AssertionError("CLI lifecycle-lease-policy cases must not write receipts")
    if any(item["immutableRecordsWritten"] for item in lifecycle_lease_cases_payload):
        raise AssertionError("CLI lifecycle-lease-policy cases must not write records")
    if any(item["sanitizedDiagnosticsOnly"] is not True for item in lifecycle_lease_cases_payload):
        raise AssertionError("CLI lifecycle-lease-policy cases should keep diagnostics sanitized")
    lifecycle_lease_boundary = run_cli("lifecycle-lease-policy", "--view", "boundary")
    lifecycle_lease_boundary_payload = json.loads(lifecycle_lease_boundary.stdout)
    for key in [
        "normalChecksWriteState",
        "leasesAcquiredByReadback",
        "persistentDatabaseCreated",
        "hostedRuntimeImplemented",
        "postgresConnectionOpened",
        "rawCrudExposed",
        "credentialValuesStored",
        "physicalDeleteAllowed",
        "forecastHistoryRewriteAllowed",
        "qualityClaimsUpgraded",
    ]:
        if lifecycle_lease_boundary_payload[key] is not False:
            raise AssertionError(f"CLI lifecycle-lease-policy boundary {key} should stay false")
    if any(lifecycle_lease_boundary_payload.values()):
        raise AssertionError("CLI lifecycle-lease-policy boundary flags should all stay false")
    lifecycle_lease_check = run_cli("lifecycle-lease-policy", "--check")
    if "checked lifecycle lease policy" not in lifecycle_lease_check.stdout:
        raise AssertionError("CLI lifecycle-lease-policy --check did not check generated output")

    runtime_transport = run_cli("runtime-transport-readiness")
    runtime_transport_payload = json.loads(runtime_transport.stdout)
    if runtime_transport_payload["readinessStatus"] != "runtime_transport_readiness_checked":
        raise AssertionError("CLI runtime-transport-readiness status drifted")
    if runtime_transport_payload["decisionStatus"] != "local_surfaces_ready_http_queue_and_hosted_deferred":
        raise AssertionError("CLI runtime-transport-readiness decision status drifted")
    if runtime_transport_payload["summary"]["currentSurfaceCount"] != 4:
        raise AssertionError("CLI runtime-transport-readiness current surface count drifted")
    if runtime_transport_payload["summary"]["futureSurfaceCount"] != 4:
        raise AssertionError("CLI runtime-transport-readiness future surface count drifted")
    if runtime_transport_payload["summary"]["readinessCriteriaCount"] != 10:
        raise AssertionError("CLI runtime-transport-readiness criteria count drifted")
    if runtime_transport_payload["summary"]["metLocalCriteriaCount"] != 6:
        raise AssertionError("CLI runtime-transport-readiness met local criteria count drifted")
    if runtime_transport_payload["summary"]["blockedCaseCount"] != 7:
        raise AssertionError("CLI runtime-transport-readiness blocked case count drifted")
    if runtime_transport_payload["hostedRuntimeAllowedNow"] is not False:
        raise AssertionError("CLI runtime-transport-readiness must block hosted runtime")
    if runtime_transport_payload["localHttpAllowedNow"] is not False:
        raise AssertionError("CLI runtime-transport-readiness must defer local HTTP")
    if runtime_transport_payload["normalChecksOffline"] is not True:
        raise AssertionError("CLI runtime-transport-readiness normal checks should stay offline")
    runtime_transport_current = run_cli("runtime-transport-readiness", "--view", "current")
    runtime_transport_current_payload = json.loads(runtime_transport_current.stdout)
    if len(runtime_transport_current_payload) != 4:
        raise AssertionError("CLI runtime-transport-readiness current view should expose four surfaces")
    if any(item["startsNetworkListener"] for item in runtime_transport_current_payload):
        raise AssertionError("CLI runtime-transport-readiness current surfaces must not start listeners")
    if any(item["hostedRuntimeRequired"] for item in runtime_transport_current_payload):
        raise AssertionError("CLI runtime-transport-readiness current surfaces must not require hosted runtime")
    runtime_transport_future = run_cli("runtime-transport-readiness", "--view", "future")
    runtime_transport_future_payload = json.loads(runtime_transport_future.stdout)
    if len(runtime_transport_future_payload) != 4:
        raise AssertionError("CLI runtime-transport-readiness future view should expose four surfaces")
    if any(item["implementedNow"] or item["advertisedNow"] or item["normalChecksStartSurface"] for item in runtime_transport_future_payload):
        raise AssertionError("CLI runtime-transport-readiness future surfaces must stay unimplemented and unadvertised")
    runtime_transport_hosted = run_cli("runtime-transport-readiness", "--surface", "hosted_service_runtime")
    runtime_transport_hosted_payload = json.loads(runtime_transport_hosted.stdout)
    if runtime_transport_hosted_payload["surfaceStatus"] != "blocked_pending_readiness_gate":
        raise AssertionError("CLI runtime-transport-readiness hosted runtime status drifted")
    if runtime_transport_hosted_payload["implementedNow"] is not False:
        raise AssertionError("CLI runtime-transport-readiness hosted runtime must not be implemented")
    runtime_transport_decisions = run_cli("runtime-transport-readiness", "--view", "decisions")
    runtime_transport_decisions_payload = json.loads(runtime_transport_decisions.stdout)
    if runtime_transport_decisions_payload["firstEmbeddedRuntime"] != "in_process_cli_agent_call_and_local_mcp":
        raise AssertionError("CLI runtime-transport-readiness embedded runtime decision drifted")
    if runtime_transport_decisions_payload["localHttpDecision"] != "deferred_until_adoption_need_and_security_gate":
        raise AssertionError("CLI runtime-transport-readiness local HTTP decision drifted")
    if runtime_transport_decisions_payload["hostedRuntimeDecision"] != "deferred_until_pilot_security_storage_and_ops_readiness":
        raise AssertionError("CLI runtime-transport-readiness hosted decision drifted")
    runtime_transport_blocked = run_cli("runtime-transport-readiness", "--view", "blocked")
    runtime_transport_blocked_payload = json.loads(runtime_transport_blocked.stdout)
    if len(runtime_transport_blocked_payload) != 7:
        raise AssertionError("CLI runtime-transport-readiness blocked view should expose seven cases")
    if any(item["networkListenerStarted"] for item in runtime_transport_blocked_payload):
        raise AssertionError("CLI runtime-transport-readiness blocked cases must not start listeners")
    if any(item["hostedRuntimeStarted"] for item in runtime_transport_blocked_payload):
        raise AssertionError("CLI runtime-transport-readiness blocked cases must not start hosted runtime")
    if any(item["stateWritten"] for item in runtime_transport_blocked_payload):
        raise AssertionError("CLI runtime-transport-readiness blocked cases must not write state")
    if any(item["sanitizedDiagnosticsOnly"] is not True for item in runtime_transport_blocked_payload):
        raise AssertionError("CLI runtime-transport-readiness blocked cases should keep diagnostics sanitized")
    runtime_transport_http_case = run_cli("runtime-transport-readiness", "--case", "normal_check_http_server")
    runtime_transport_http_case_payload = json.loads(runtime_transport_http_case.stdout)
    if runtime_transport_http_case_payload["caseStatus"] != "blocked_normal_check_network_listener":
        raise AssertionError("CLI runtime-transport-readiness HTTP blocked case drifted")
    runtime_transport_boundary = run_cli("runtime-transport-readiness", "--view", "boundary")
    runtime_transport_boundary_payload = json.loads(runtime_transport_boundary.stdout)
    for key in [
        "networkListenerStarted",
        "localHttpServerImplemented",
        "hostedServiceImplemented",
        "queueRuntimeImplemented",
        "oppHttpProviderImplemented",
        "normalChecksUseNetwork",
        "normalChecksWriteState",
        "credentialValuesStored",
        "paymentSettlementImplemented",
        "productionLiveFetchEnabled",
        "qualityClaimsUpgraded",
    ]:
        if runtime_transport_boundary_payload[key] is not False:
            raise AssertionError(f"CLI runtime-transport-readiness boundary {key} should stay false")
    if any(runtime_transport_boundary_payload.values()):
        raise AssertionError("CLI runtime-transport-readiness boundary flags should all stay false")
    runtime_transport_check = run_cli("runtime-transport-readiness", "--check")
    if "checked runtime transport readiness" not in runtime_transport_check.stdout:
        raise AssertionError("CLI runtime-transport-readiness --check did not check generated output")

    workspace_tenant = run_cli("workspace-tenant-isolation")
    workspace_tenant_payload = json.loads(workspace_tenant.stdout)
    if workspace_tenant_payload["isolationStatus"] != "workspace_tenant_isolation_checked":
        raise AssertionError("CLI workspace-tenant-isolation status drifted")
    if (
        workspace_tenant_payload["decisionStatus"]
        != "tenant_scoped_workspaces_with_resource_source_and_queue_isolation"
    ):
        raise AssertionError("CLI workspace-tenant-isolation decision status drifted")
    if workspace_tenant_payload["summary"]["tenantWorkspaceCount"] != 2:
        raise AssertionError("CLI workspace-tenant-isolation tenant count drifted")
    if workspace_tenant_payload["summary"]["scopeKeyCount"] != 5:
        raise AssertionError("CLI workspace-tenant-isolation scope key count drifted")
    if workspace_tenant_payload["summary"]["queuePolicyCount"] != 8:
        raise AssertionError("CLI workspace-tenant-isolation queue policy count drifted")
    if workspace_tenant_payload["summary"]["sourcePolicyCount"] != 5:
        raise AssertionError("CLI workspace-tenant-isolation source policy count drifted")
    if workspace_tenant_payload["summary"]["accessCaseCount"] != 7:
        raise AssertionError("CLI workspace-tenant-isolation access case count drifted")
    if workspace_tenant_payload["summary"]["blockedAccessCaseCount"] != 6:
        raise AssertionError("CLI workspace-tenant-isolation blocked case count drifted")
    if workspace_tenant_payload["normalChecksMutateState"] is not False:
        raise AssertionError("CLI workspace-tenant-isolation must not mutate state in normal checks")
    if workspace_tenant_payload["hostedTenantRuntimeImplemented"] is not False:
        raise AssertionError("CLI workspace-tenant-isolation must not implement hosted tenant runtime")
    workspace_tenant_scope = run_cli("workspace-tenant-isolation", "--view", "scope")
    workspace_tenant_scope_payload = json.loads(workspace_tenant_scope.stdout)
    if [item["scopeKeyName"] for item in workspace_tenant_scope_payload] != [
        "tenant_id",
        "workspace_id",
        "prediction_id",
        "source_binding_id",
        "operation_idempotency_namespace",
    ]:
        raise AssertionError("CLI workspace-tenant-isolation scope key order drifted")
    if any(item["rawValuePublic"] for item in workspace_tenant_scope_payload):
        raise AssertionError("CLI workspace-tenant-isolation scope keys must not expose raw values")
    workspace_tenant_queues = run_cli("workspace-tenant-isolation", "--view", "queues")
    workspace_tenant_queues_payload = json.loads(workspace_tenant_queues.stdout)
    if len(workspace_tenant_queues_payload) != 8:
        raise AssertionError("CLI workspace-tenant-isolation queue view should expose eight policies")
    if any(item["crossTenantPeekAllowed"] for item in workspace_tenant_queues_payload):
        raise AssertionError("CLI workspace-tenant-isolation queues must block cross-tenant peek")
    if any(item["rawQueueCrudExposed"] for item in workspace_tenant_queues_payload):
        raise AssertionError("CLI workspace-tenant-isolation queues must not expose raw CRUD")
    workspace_tenant_sources = run_cli("workspace-tenant-isolation", "--view", "sources")
    workspace_tenant_sources_payload = json.loads(workspace_tenant_sources.stdout)
    if len(workspace_tenant_sources_payload) != 5:
        raise AssertionError("CLI workspace-tenant-isolation source view should expose five policies")
    if any(item["crossTenantReuseAllowed"] for item in workspace_tenant_sources_payload):
        raise AssertionError("CLI workspace-tenant-isolation sources must block cross-tenant reuse")
    if any(item["credentialValuesStored"] or item["rawPrivateRowsStored"] for item in workspace_tenant_sources_payload):
        raise AssertionError("CLI workspace-tenant-isolation sources must not store credentials or raw rows")
    workspace_tenant_case = run_cli("workspace-tenant-isolation", "--case", "cross_tenant_prediction_read")
    workspace_tenant_case_payload = json.loads(workspace_tenant_case.stdout)
    if workspace_tenant_case_payload["caseStatus"] != "blocked_cross_tenant_prediction_read":
        raise AssertionError("CLI workspace-tenant-isolation blocked case status drifted")
    if workspace_tenant_case_payload["accessAllowed"] is not False:
        raise AssertionError("CLI workspace-tenant-isolation blocked case must not allow access")
    workspace_tenant_tenant = run_cli("workspace-tenant-isolation", "--tenant-id", "tenant-001")
    workspace_tenant_tenant_payload = json.loads(workspace_tenant_tenant.stdout)
    if workspace_tenant_tenant_payload["workspaceId"] != "opeworkspace-001":
        raise AssertionError("CLI workspace-tenant-isolation tenant workspace binding drifted")
    if workspace_tenant_tenant_payload["rawSqlExposed"] or workspace_tenant_tenant_payload["rawPrivateRowsExposed"]:
        raise AssertionError("CLI workspace-tenant-isolation tenant view must not expose raw storage")
    workspace_tenant_boundary = run_cli("workspace-tenant-isolation", "--view", "boundary")
    workspace_tenant_boundary_payload = json.loads(workspace_tenant_boundary.stdout)
    for key in [
        "normalChecksWriteState",
        "hostedTenantRuntimeImplemented",
        "crossTenantReadAllowed",
        "crossTenantSourceReuseAllowed",
        "crossTenantQueueScanAllowed",
        "credentialValuesStored",
        "rawPrivateRowsStored",
        "networkListenerStarted",
        "rawCrudExposed",
        "qualityClaimsUpgraded",
    ]:
        if workspace_tenant_boundary_payload[key] is not False:
            raise AssertionError(f"CLI workspace-tenant-isolation boundary {key} should stay false")
    if any(workspace_tenant_boundary_payload.values()):
        raise AssertionError("CLI workspace-tenant-isolation boundary flags should all stay false")
    workspace_tenant_check = run_cli("workspace-tenant-isolation", "--check")
    if "checked workspace tenant isolation" not in workspace_tenant_check.stdout:
        raise AssertionError("CLI workspace-tenant-isolation --check did not check generated output")

    transit_corpus = run_cli("transit-forward-run-corpus")
    transit_corpus_payload = json.loads(transit_corpus.stdout)
    corpus_summary = transit_corpus_payload["summary"]
    if corpus_summary["corpusCount"] != 7:
        raise AssertionError("CLI transit-forward-run-corpus should expose seven fixture rows")
    if corpus_summary["comparableResolvedCount"] != 1 or corpus_summary["excludedCount"] != 6:
        raise AssertionError("CLI transit-forward-run-corpus should expose comparable and excluded counts")
    exclusion_reasons = {item["exclusionReason"] for item in transit_corpus_payload["excludedRuns"]}
    if exclusion_reasons != {"ambiguous", "annulled", "low_coverage", "invalid_window", "feed_unavailable", "non_comparable"}:
        raise AssertionError("CLI transit-forward-run-corpus should expose all exclusion reasons")
    comparable_run = transit_corpus_payload["comparableRuns"][0]
    if not comparable_run["forecastBinding"]["forecastBeforeClose"]:
        raise AssertionError("CLI transit-forward-run-corpus should preserve forecast-before-close timing")
    if not comparable_run["resolutionBinding"]["resolvedAfterHorizon"]:
        raise AssertionError("CLI transit-forward-run-corpus should preserve resolution-after-horizon timing")
    if comparable_run["scoreBinding"]["baselineLift"] <= 0:
        raise AssertionError("CLI transit-forward-run-corpus should bind score-against-baseline data")
    corpus_boundary = transit_corpus_payload["claimBoundary"]
    if corpus_boundary["calibrationClaimAllowed"] or corpus_boundary["baselineTrackRecordAllowed"]:
        raise AssertionError("CLI transit-forward-run-corpus should block calibration and track-record claims")
    if transit_corpus_payload["readSurface"]["fetchesLiveData"]:
        raise AssertionError("CLI transit-forward-run-corpus read surface must not fetch live data")
    transit_corpus_check = run_cli("transit-forward-run-corpus", "--check")
    if "checked transit forward-run corpus" not in transit_corpus_check.stdout:
        raise AssertionError("CLI transit-forward-run-corpus --check did not check generated output")

    transit_track_gate = run_cli("transit-track-record-gate")
    transit_track_gate_payload = json.loads(transit_track_gate.stdout)
    gate_samples = transit_track_gate_payload["sampleSummary"]
    if gate_samples["resolvedComparableSampleSize"] != 1 or gate_samples["excludedSampleSize"] != 6:
        raise AssertionError("CLI transit-track-record-gate should expose resolved and excluded sample sizes")
    if gate_samples["trackRecordStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("CLI transit-track-record-gate should keep track-record status below threshold")
    if gate_samples["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("CLI transit-track-record-gate should keep calibration status below threshold")
    track_summary = transit_track_gate_payload["trackRecordSummary"]
    if track_summary["primaryScore"] != 0.4489 or track_summary["baselineScore"] != 0.5625:
        raise AssertionError("CLI transit-track-record-gate should expose Brier and baseline scores")
    if track_summary["baselineLift"] != 0.1136:
        raise AssertionError("CLI transit-track-record-gate should expose baseline lift")
    if track_summary["resolvedSampleSize"] != 1 or track_summary["excludedSampleSize"] != 6:
        raise AssertionError("CLI transit-track-record-gate should expose sample sizes in summary")
    horizon_coverage = transit_track_gate_payload["coverageSummary"]["horizonWindowCoverage"]
    if horizon_coverage["comparableWindowCount"] != 1 or horizon_coverage["excludedWindowCount"] != 6:
        raise AssertionError("CLI transit-track-record-gate should expose horizon/window coverage")
    calibration_gate = transit_track_gate_payload["calibrationGate"]
    if calibration_gate["summaryGenerated"] or calibration_gate["calibrationSummary"] is not None:
        raise AssertionError("CLI transit-track-record-gate should not generate below-threshold calibration")
    gate_boundary = transit_track_gate_payload["claimBoundary"]
    if (
        gate_boundary["qualityClaimAllowed"]
        or gate_boundary["baselineTrackRecordAllowed"]
        or gate_boundary["calibrationClaimAllowed"]
    ):
        raise AssertionError("CLI transit-track-record-gate should block quality, track-record, and calibration claims")
    if gate_boundary["oneOffForwardRunCanCreateCalibrationEvidence"]:
        raise AssertionError("CLI transit-track-record-gate must reject one-off calibration evidence")
    if transit_track_gate_payload["readSurface"]["fetchesLiveData"]:
        raise AssertionError("CLI transit-track-record-gate read surface must not fetch live data")
    transit_track_campaign_gate = run_cli("transit-track-record-gate", "--campaign", "predictioncampaign-001")
    transit_track_campaign_payload = json.loads(transit_track_campaign_gate.stdout)
    if transit_track_campaign_payload["campaignLedger"]["included"] is not True:
        raise AssertionError("CLI transit-track-record-gate --campaign should include campaign ledger")
    if transit_track_campaign_payload["sampleSummary"]["excludedSampleSize"] != 7:
        raise AssertionError("CLI transit-track-record-gate --campaign should include campaign excluded row")
    transit_track_campaign_comparable_gate = run_cli(
        "transit-track-record-gate",
        "--campaign",
        "predictioncampaign-001",
        "--ledger-case",
        "comparable_scored",
    )
    transit_track_campaign_comparable_payload = json.loads(transit_track_campaign_comparable_gate.stdout)
    if transit_track_campaign_comparable_payload["sampleSummary"]["resolvedComparableSampleSize"] != 2:
        raise AssertionError("CLI transit-track-record-gate campaign comparable sample size drifted")
    if transit_track_campaign_comparable_payload["claimBoundary"]["calibrationClaimAllowed"]:
        raise AssertionError("CLI transit-track-record-gate campaign ledger must not unlock calibration below threshold")
    transit_track_gate_check = run_cli("transit-track-record-gate", "--check")
    if "checked transit baseline track-record gate" not in transit_track_gate_check.stdout:
        raise AssertionError("CLI transit-track-record-gate --check did not check generated output")

    transit_method_options = run_cli("transit-method-options")
    transit_method_options_payload = json.loads(transit_method_options.stdout)
    default_selection = transit_method_options_payload["defaultSelection"]
    if not default_selection["baselineOnlyDefault"] or default_selection["selectedMethodId"] != "transitmethod-100":
        raise AssertionError("CLI transit-method-options should keep baseline as default")
    method_evidence = transit_method_options_payload["corpusEvidence"]
    if method_evidence["resolvedComparableSampleSize"] != 1:
        raise AssertionError("CLI transit-method-options should expose one comparable sample")
    if method_evidence["minimumComparableResolvedForNonBaselineSelection"] != 30:
        raise AssertionError("CLI transit-method-options should preserve non-baseline threshold")
    method_options = {item["methodId"]: item for item in transit_method_options_payload["methodOptions"]}
    weather_method = method_options["transitmethod-101"]
    if weather_method["status"] != "evidence_only" or weather_method["selectionEligibility"] != "rejected":
        raise AssertionError("CLI transit-method-options should keep weather adjustment evidence-only")
    if weather_method["baselineLift"] != 0.1136:
        raise AssertionError("CLI transit-method-options should expose weather-adjustment baseline lift")
    if "resolved_comparable_sample_below_threshold" not in weather_method["rejectionReasons"]:
        raise AssertionError("CLI transit-method-options should reject weather adjustment below threshold")
    for method_id in ["transitmethod-201", "transitmethod-301", "transitmethod-401", "transitmethod-501", "transitmethod-601"]:
        if method_options[method_id]["selectionEligibility"] != "proposed_only":
            raise AssertionError("CLI transit-method-options should keep richer methods proposed-only")
    method_comparison = transit_method_options_payload["methodComparison"]
    if method_comparison["sameWindowOutcomeUsedAsForecastEvidence"]:
        raise AssertionError("CLI transit-method-options must not use same-window outcomes as forecast evidence")
    if method_comparison["bestCandidateBaselineLift"] != 0.1136:
        raise AssertionError("CLI transit-method-options should expose method comparison lift")
    method_boundary = transit_method_options_payload["claimBoundary"]
    if (
        method_boundary["nonBaselineSelectionAllowed"]
        or method_boundary["trainedMlAllowed"]
        or method_boundary["ensembleAllowed"]
        or method_boundary["retrievalAssistedAllowed"]
        or method_boundary["externalReferenceAllowed"]
    ):
        raise AssertionError("CLI transit-method-options should block non-baseline and richer method families")
    if transit_method_options_payload["readSurface"]["selectsNonBaselineMethod"]:
        raise AssertionError("CLI transit-method-options read surface must not select a non-baseline method")
    transit_method_options_check = run_cli("transit-method-options", "--check")
    if "checked transit method options" not in transit_method_options_check.stdout:
        raise AssertionError("CLI transit-method-options --check did not check generated output")

    transit_live_promotion = run_cli("transit-live-evidence-promotion")
    transit_live_promotion_payload = json.loads(transit_live_promotion.stdout)
    promotion_policy = transit_live_promotion_payload["policyBinding"]
    if promotion_policy["normalChecksMayReadLiveWorkspace"] or promotion_policy["normalChecksMayFetchLiveNetwork"]:
        raise AssertionError("CLI transit-live-evidence-promotion should keep normal checks offline")
    if promotion_policy["retention"]["rawLocalArtifactsCommitted"]:
        raise AssertionError("CLI transit-live-evidence-promotion should not commit raw live artifacts")
    promotion_counts = transit_live_promotion_payload["readbackSummary"]["surfaceCounts"]
    if (
        promotion_counts["committedFixtures"] != 1
        or promotion_counts["localLiveDrafts"] != 2
        or promotion_counts["promotedForecastTimeEvidence"] != 1
        or promotion_counts["resolutionOnlyEvidence"] != 1
    ):
        raise AssertionError("CLI transit-live-evidence-promotion should distinguish evidence surfaces")
    promotion_cases = {item["promotionCaseId"]: item for item in transit_live_promotion_payload["promotionCases"]}
    promoted_case = promotion_cases["transitlivepromotioncase-003"]
    if promoted_case["promotionStatus"] != "promoted":
        raise AssertionError("CLI transit-live-evidence-promotion should include a promoted case")
    if promoted_case["gateChecks"]["captureTimingStatus"] != "pre_close":
        raise AssertionError("CLI transit-live-evidence-promotion promoted case should be pre-close")
    if promoted_case["gateChecks"]["freshnessStatus"] != "within_policy":
        raise AssertionError("CLI transit-live-evidence-promotion promoted case should pass freshness")
    if not promoted_case["sanitizedBinding"]["forecastTimeSourceSetBound"]:
        raise AssertionError("CLI transit-live-evidence-promotion should bind promoted source set")
    post_close_case = promotion_cases["transitlivepromotioncase-004"]
    if "capture_after_forecast_close" not in post_close_case["rejectionReasons"]:
        raise AssertionError("CLI transit-live-evidence-promotion should reject post-close captures")
    resolution_only_case = promotion_cases["transitlivepromotioncase-005"]
    if "source_role_resolution_only" not in resolution_only_case["rejectionReasons"]:
        raise AssertionError("CLI transit-live-evidence-promotion should reject resolution-only evidence")
    promotion_boundary = transit_live_promotion_payload["claimBoundary"]
    if (
        promotion_boundary["promotesPostCloseEvidence"]
        or promotion_boundary["promotesResolutionOnlyEvidence"]
        or promotion_boundary["createsForecastArtifacts"]
        or promotion_boundary["fetchesLiveData"]
    ):
        raise AssertionError("CLI transit-live-evidence-promotion should keep blocked claims false")
    promoted_source_set = run_cli(
        "read",
        "--record-type",
        "evidence-source-set",
        "--id",
        transit_live_promotion_payload["readbackSummary"]["promotedEvidenceSourceSetId"],
    )
    promoted_source_set_payload = json.loads(promoted_source_set.stdout)
    if promoted_source_set_payload["record"]["evidenceSourceSetId"] != "evidencesourceset-1201":
        raise AssertionError("CLI read should expose promoted transit evidence source set")
    if promoted_source_set_payload["record"]["records"][0]["connector"] != "open_meteo_weather":
        raise AssertionError("CLI read should preserve promoted Open-Meteo source binding")
    transit_live_promotion_check = run_cli("transit-live-evidence-promotion", "--check")
    if "checked transit live evidence promotion" not in transit_live_promotion_check.stdout:
        raise AssertionError("CLI transit-live-evidence-promotion --check did not check generated output")

    transit_api_connector = run_cli("transit-api-connector")
    transit_api_connector_payload = json.loads(transit_api_connector.stdout)
    if transit_api_connector_payload["provider"]["providerId"] != "hsl_gtfs_rt_trip_updates":
        raise AssertionError("CLI transit-api-connector should expose HSL TripUpdates")
    if transit_api_connector_payload["api"]["requiresCredentials"] is not False:
        raise AssertionError("CLI transit-api-connector should not require credentials")
    if transit_api_connector_payload["api"]["requestParametersSupported"] is not False:
        raise AssertionError("CLI transit-api-connector should not claim request filtering")
    if not transit_api_connector_payload["api"]["companionStaticGtfsPackage"].endswith("/gtfs/hsl.zip"):
        raise AssertionError("CLI transit-api-connector should name companion static GTFS")
    if transit_api_connector_payload["decoder"]["scheduleJoinStatus"] != "implemented_opt_in":
        raise AssertionError("CLI transit-api-connector should expose opt-in schedule join")
    if "start_time" not in transit_api_connector_payload["decoder"]["scheduleJoinMatchKeys"]:
        raise AssertionError("CLI transit-api-connector should declare schedule join match keys")
    if "delay_seconds" not in transit_api_connector_payload["decoder"]["decodedFields"]:
        raise AssertionError("CLI transit-api-connector should decode delay seconds")
    if transit_api_connector_payload["sourceAdapterBoundary"]["canProduceSourceAdapterOutput"] is not True:
        raise AssertionError("CLI transit-api-connector should produce source adapter output")
    if transit_api_connector_payload["sourceAdapterBoundary"]["createsForecastArtifacts"]:
        raise AssertionError("CLI transit-api-connector must not create forecast artifacts")
    if transit_api_connector_payload["sourceAdapterBoundary"]["createsScoringRecords"]:
        raise AssertionError("CLI transit-api-connector must not create scoring records")
    if transit_api_connector_payload["liveBoundary"]["normalChecksOffline"] is not True:
        raise AssertionError("CLI transit-api-connector should keep normal checks offline")
    transit_api_connector_check = run_cli("transit-api-connector", "--check")
    if "checked transit API connector" not in transit_api_connector_check.stdout:
        raise AssertionError("CLI transit-api-connector --check did not check generated output")

    source_intake = run_cli("source-intake")
    source_intake_payload = json.loads(source_intake.stdout)
    if source_intake_payload["count"] != 4:
        raise AssertionError("CLI source-intake should expose four intake outcomes")
    intake_summaries = {item["case"]: item for item in source_intake_payload["reports"]}
    if intake_summaries["accepted"]["intakeStatus"] != "accepted":
        raise AssertionError("CLI source-intake accepted case should be accepted")
    if "deterministic_statistical" not in intake_summaries["accepted"]["eligibleMethods"]:
        raise AssertionError("CLI source-intake accepted case should enable deterministic method")
    if intake_summaries["accepted_partial"]["eligibleMethods"] != ["historical_baseline"]:
        raise AssertionError("CLI source-intake partial case should only enable baseline")
    if intake_summaries["needs_confirmation"]["canProduceForecast"] is not False:
        raise AssertionError("CLI source-intake proposed mappings should block forecasts")
    if intake_summaries["rejected"]["intakeStatus"] != "rejected":
        raise AssertionError("CLI source-intake rejected case should be rejected")

    needs_confirmation_intake = run_cli("source-intake", "--case", "needs_confirmation")
    needs_confirmation_payload = json.loads(needs_confirmation_intake.stdout)
    if not any(item["decision"] == "proposed" for item in needs_confirmation_payload["mappingDecisions"]):
        raise AssertionError("CLI source-intake should expose proposed mappings")
    if needs_confirmation_payload["forecastGenerationAllowed"] is not False:
        raise AssertionError("CLI source-intake needs-confirmation case should not allow forecast generation")

    source_builder = run_cli("source-builder")
    source_builder_payload = json.loads(source_builder.stdout)
    if source_builder_payload["count"] != 5:
        raise AssertionError("CLI source-builder should expose five builder outcomes")
    source_builds = {item["case"]: item for item in source_builder_payload["builds"]}
    if source_builds["local_draft"]["buildStatus"] != "draft_ready":
        raise AssertionError("CLI source-builder local draft should be draft-ready")
    if source_builds["local_draft"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("CLI source-builder should not allow forecast generation")
    if source_builds["local_draft"]["confirmationRequired"] is not True:
        raise AssertionError("CLI source-builder should require confirmation for inferred mappings")
    for case in ("contains_secret", "unsupported_format", "oversized", "leakage"):
        if source_builds[case]["buildStatus"] != "rejected":
            raise AssertionError(f"CLI source-builder {case} case should be rejected")

    source_builder_case = run_cli("source-builder", "--case", "local_draft")
    source_builder_case_payload = json.loads(source_builder_case.stdout)
    if source_builder_case_payload["draftArtifacts"]["sourceManifestId"] != "sourcemanifestdraft-001":
        raise AssertionError("CLI source-builder should bind the draft source manifest")
    if not any(item["fileFormat"] == "json" for item in source_builder_case_payload["inputFiles"]):
        raise AssertionError("CLI source-builder should inspect JSON files")
    if not any(item["fileFormat"] == "csv" for item in source_builder_case_payload["inputFiles"]):
        raise AssertionError("CLI source-builder should inspect CSV files")

    source_adapter_output = run_cli("source-adapter-output")
    source_adapter_output_payload = json.loads(source_adapter_output.stdout)
    if source_adapter_output_payload["outputStatus"] != "intake_ready":
        raise AssertionError("CLI source-adapter-output should expose an intake-ready handoff")
    if source_adapter_output_payload["adapter"]["implementationLocation"] != "external_agent":
        raise AssertionError("CLI source-adapter-output should model an external connector")
    if source_adapter_output_payload["controls"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("CLI source-adapter-output must not create forecast artifacts")
    if source_adapter_output_payload["controls"]["sourceIntakeAlreadyRun"] is not False:
        raise AssertionError("CLI source-adapter-output must precede source intake")
    if source_adapter_output_payload["nextAction"] != "run_source_intake":
        raise AssertionError("CLI source-adapter-output should route confirmed mappings to source intake")
    adapter_roles = {
        item["sourceRole"]
        for item in source_adapter_output_payload["sourceManifest"]["sources"]
    }
    if "transit_delay_outcome" not in adapter_roles:
        raise AssertionError("CLI source-adapter-output should preserve the transit outcome source role")
    if source_adapter_output_payload["provenanceSummary"]["rawRowsIncluded"] is not False:
        raise AssertionError("CLI source-adapter-output should not include raw rows")
    source_adapter_output_check = run_cli("source-adapter-output", "--check")
    if "checked source adapter output" not in source_adapter_output_check.stdout:
        raise AssertionError("CLI source-adapter-output --check did not check generated output")

    source_handoff = run_cli("source-handoff")
    source_handoff_payload = json.loads(source_handoff.stdout)
    if source_handoff_payload["count"] != 7:
        raise AssertionError("CLI source-handoff should expose seven handoff outcomes")
    handoffs = {item["case"]: item for item in source_handoff_payload["handoffs"]}
    if handoffs["unconfirmed_builder_draft"]["nextAction"] != "ask_mapping_confirmation":
        raise AssertionError("CLI source-handoff should ask confirmation for unconfirmed drafts")
    if handoffs["confirmed_builder_draft"]["nextAction"] != "proceed_to_method_gating":
        raise AssertionError("CLI source-handoff should proceed after confirmed accepted intake")
    if handoffs["insufficient_confirmed_builder_draft"]["nextAction"] != "collect_more_data":
        raise AssertionError("CLI source-handoff should ask for more data when sample size is insufficient")
    if handoffs["contains_secret"]["nextAction"] != "replace_rejected_sources":
        raise AssertionError("CLI source-handoff should preserve builder rejection next actions")

    source_handoff_case = run_cli("source-handoff", "--case", "confirmed_builder_draft")
    source_handoff_case_payload = json.loads(source_handoff_case.stdout)
    if source_handoff_case_payload["sourceIntakeStatus"] != "accepted":
        raise AssertionError("CLI source-handoff confirmed case should bind accepted source intake")
    if source_handoff_case_payload["mappingSummary"]["requiresConfirmation"] is not False:
        raise AssertionError("CLI source-handoff confirmed case should have confirmed mappings")

    source_handoff_method = run_cli("source-handoff-method")
    source_handoff_method_payload = json.loads(source_handoff_method.stdout)
    if source_handoff_method_payload["count"] != 7:
        raise AssertionError("CLI source-handoff-method should expose seven method-gate outcomes")
    handoff_methods = {item["case"]: item for item in source_handoff_method_payload["methodGates"]}
    if handoff_methods["unconfirmed_builder_draft"]["methodGateStatus"] != "needs_mapping_confirmation":
        raise AssertionError("CLI source-handoff-method should block unconfirmed mappings")
    if handoff_methods["confirmed_builder_draft"]["methodGateStatus"] != "method_selected":
        raise AssertionError("CLI source-handoff-method should select a method for confirmed intake")
    if handoff_methods["confirmed_builder_draft"]["selectedMethodClass"] != "deterministic_statistical":
        raise AssertionError("CLI source-handoff-method should expose selected deterministic method")
    if handoff_methods["confirmed_builder_draft"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("CLI source-handoff-method should not create forecast artifacts")
    if handoff_methods["insufficient_confirmed_builder_draft"]["methodGateStatus"] != "needs_more_data":
        raise AssertionError("CLI source-handoff-method should ask for more data on insufficient intake")
    if handoff_methods["contains_secret"]["methodGateStatus"] != "not_entered_source_intake":
        raise AssertionError("CLI source-handoff-method should keep rejected builder inputs out of source intake")

    source_handoff_method_case = run_cli("source-handoff-method", "--case", "confirmed_builder_draft")
    source_handoff_method_case_payload = json.loads(source_handoff_method_case.stdout)
    if source_handoff_method_case_payload["setupBenchmarkGateId"] != "setupbenchmarkgate-102":
        raise AssertionError("CLI source-handoff-method confirmed case should bind handoff benchmark gate")
    if source_handoff_method_case_payload["nextAction"] != "await_explicit_setup_forecast_execution":
        raise AssertionError("CLI source-handoff-method should require explicit setup forecast execution")

    auto_forecast = run_cli("auto-forecast")
    if "checked 6 auto-evidence forecast outputs" not in auto_forecast.stdout:
        raise AssertionError("CLI auto-forecast did not check generated outputs")

    auto_resolution = run_cli("resolve-auto-evidence")
    if "checked 6 auto-evidence resolution outputs" not in auto_resolution.stdout:
        raise AssertionError("CLI resolve-auto-evidence did not check generated outputs")

    historical_forecast = run_cli("historical-forecast")
    if "checked 6 historical baseline forecast outputs" not in historical_forecast.stdout:
        raise AssertionError("CLI historical-forecast did not check generated outputs")

    method_comparison = run_cli("method-comparison")
    method_comparison_payload = json.loads(method_comparison.stdout)
    if len(method_comparison_payload["comparisons"]) != 5:
        raise AssertionError("CLI method-comparison should compare every non-baseline method")

    method_selection = run_cli("method-selection")
    method_selection_payload = json.loads(method_selection.stdout)
    if method_selection_payload["selectionStatus"] != "fallback_selected":
        raise AssertionError("CLI method-selection should explain baseline fallback")

    setup_benchmark = run_cli("setup-benchmark")
    setup_benchmark_payload = json.loads(setup_benchmark.stdout)
    if setup_benchmark_payload["count"] != 4:
        raise AssertionError("CLI setup-benchmark should expose four gate outcomes")
    setup_gates = {item["case"]: item for item in setup_benchmark_payload["gates"]}
    if setup_gates["accepted"]["gateStatus"] != "approved_provisional":
        raise AssertionError("CLI setup-benchmark accepted case should approve provisional execution")
    if setup_gates["accepted"]["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI setup-benchmark should keep quality claims blocked")
    if setup_gates["accepted_partial"]["executionAllowed"] is not False:
        raise AssertionError("CLI setup-benchmark partial case should block execution")

    setup_method = run_cli("setup-method")
    setup_method_payload = json.loads(setup_method.stdout)
    if setup_method_payload["count"] != 4:
        raise AssertionError("CLI setup-method should expose four source-intake decisions")
    setup_decisions = {item["case"]: item for item in setup_method_payload["decisions"]}
    if setup_decisions["accepted"]["decisionStatus"] != "method_selected":
        raise AssertionError("CLI setup-method accepted case should select benchmark-approved method")
    if setup_decisions["accepted"]["selectedMethodClass"] != "deterministic_statistical":
        raise AssertionError("CLI setup-method accepted case should select deterministic method")
    if setup_decisions["accepted_partial"]["selectedMethodClass"] != "historical_baseline":
        raise AssertionError("CLI setup-method partial case should keep baseline selected")
    if setup_decisions["needs_confirmation"]["decisionStatus"] != "needs_confirmation":
        raise AssertionError("CLI setup-method should block proposed mappings")
    if setup_decisions["rejected"]["selectedMethodClass"] != "none":
        raise AssertionError("CLI setup-method rejected case must not select a method")

    accepted_setup_method = run_cli("setup-method", "--case", "accepted")
    accepted_setup_method_payload = json.loads(accepted_setup_method.stdout)
    setup_candidates = {
        item["methodClass"]: item for item in accepted_setup_method_payload["methodCandidates"]
    }
    if setup_candidates["deterministic_statistical"]["sourceEligibilityStatus"] != "eligible":
        raise AssertionError("CLI setup-method should show deterministic source eligibility")
    if setup_candidates["deterministic_statistical"]["finalEligibilityStatus"] != "eligible":
        raise AssertionError("CLI setup-method should accept deterministic method through benchmark gate")
    if "quality_sample_threshold_not_met" not in setup_candidates["deterministic_statistical"]["reasonCodes"]:
        raise AssertionError("CLI setup-method should preserve quality claim boundary")

    setup_forecast = run_cli("setup-forecast")
    if "checked 14 setup forecast execution outputs" not in setup_forecast.stdout:
        raise AssertionError("CLI setup-forecast did not check generated outputs")

    source_handoff_forecast = run_cli("source-handoff-forecast")
    source_handoff_forecast_payload = json.loads(source_handoff_forecast.stdout)
    if source_handoff_forecast_payload["count"] != 7:
        raise AssertionError("CLI source-handoff-forecast should expose seven handoff runs")
    handoff_runs = {item["case"]: item for item in source_handoff_forecast_payload["runs"]}
    if handoff_runs["confirmed_builder_draft"]["runStatus"] != "generated":
        raise AssertionError("CLI source-handoff-forecast should generate confirmed handoff run")
    if handoff_runs["confirmed_builder_draft"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI source-handoff-forecast should expose forecast-1102")
    if handoff_runs["unconfirmed_builder_draft"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("CLI source-handoff-forecast should block unconfirmed handoffs")
    if handoff_runs["contains_secret"]["runStatus"] != "blocked":
        raise AssertionError("CLI source-handoff-forecast should block builder-rejected handoffs")

    source_handoff_forecast_case = run_cli("source-handoff-forecast", "--case", "confirmed_builder_draft")
    source_handoff_forecast_case_payload = json.loads(source_handoff_forecast_case.stdout)
    if source_handoff_forecast_case_payload["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("CLI source-handoff-forecast should bind source handoff method gate")
    if source_handoff_forecast_case_payload["setupBenchmarkGateId"] != "setupbenchmarkgate-102":
        raise AssertionError("CLI source-handoff-forecast should bind handoff benchmark gate")
    if source_handoff_forecast_case_payload["recordBinding"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI source-handoff-forecast should bind generated forecast")

    source_handoff_resolution = run_cli("resolve-source-handoff")
    if "checked 6 source-handoff resolution outputs" not in source_handoff_resolution.stdout:
        raise AssertionError("CLI resolve-source-handoff did not check generated outputs")

    resolved_source_handoff_card = run_cli(
        "read",
        "--record-type",
        "forecast-card",
        "--id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    resolved_source_handoff_payload = json.loads(resolved_source_handoff_card.stdout)
    if resolved_source_handoff_payload["record"]["status"] != "resolved":
        raise AssertionError("CLI source-handoff forecast card should surface resolved status")
    if resolved_source_handoff_payload["record"]["score"]["scoreStatus"] != "scored":
        raise AssertionError("CLI source-handoff forecast card should surface scoring")
    if resolved_source_handoff_payload["record"]["qualityClaim"]["resolvedComparableOutcomes"] != 1:
        raise AssertionError("CLI source-handoff forecast card should expose resolved sample count")

    recalculation = run_cli("recalculation")
    if "checked recalculation history records" not in recalculation.stdout:
        raise AssertionError("CLI recalculation should check generated recalculation records")

    forecast_run = run_cli("forecast-run")
    forecast_run_payload = json.loads(forecast_run.stdout)
    if forecast_run_payload["runStatus"] != "completed":
        raise AssertionError("CLI forecast-run should complete the fixture-safe auto-evidence run")
    if forecast_run_payload["recordBinding"]["forecastId"] != "forecast-602":
        raise AssertionError("CLI forecast-run should bind forecast-602")
    if forecast_run_payload["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("CLI forecast-run should keep the quality claim provisional")
    if forecast_run_payload["outputs"]["evidenceTrace"]["operation"] != "evidence_trace":
        raise AssertionError("CLI forecast-run should link the evidence trace")

    historical_forecast_run = run_cli(
        "forecast-run",
        "--request",
        "spec/fixtures/requests/historical-weather-logistics-request.json",
    )
    historical_forecast_run_payload = json.loads(historical_forecast_run.stdout)
    if historical_forecast_run_payload["runStatus"] != "completed":
        raise AssertionError("CLI historical forecast-run should complete")
    if historical_forecast_run_payload["sourceMode"] != "committed_fixture":
        raise AssertionError("CLI historical forecast-run should use committed fixture source mode")
    if historical_forecast_run_payload["recordBinding"]["forecastId"] != "forecast-702":
        raise AssertionError("CLI historical forecast-run should bind forecast-702")
    if historical_forecast_run_payload["forecast"]["probability"] != 0.22:
        raise AssertionError("CLI historical forecast-run should expose baseline probability")
    if historical_forecast_run_payload["outputs"]["evidenceTrace"] is not None:
        raise AssertionError("CLI historical forecast-run should not link evidence trace")

    forecast_run_matrix = run_cli("forecast-run-matrix")
    forecast_run_matrix_payload = json.loads(forecast_run_matrix.stdout)
    classes = {item["outcomeClass"] for item in forecast_run_matrix_payload["outcomes"]}
    expected_classes = {
        "accepted",
        "rejected",
        "blocked",
        "canceled",
        "unsupported_fixture_path",
        "response_too_large",
    }
    if classes != expected_classes:
        raise AssertionError("CLI forecast-run-matrix should expose each intake outcome class")
    for item in forecast_run_matrix_payload["outcomes"]:
        if item["outcomeClass"] != "accepted" and item["generatesForecastOutputs"]:
            raise AssertionError("CLI forecast-run-matrix should not generate outputs for failure classes")

    forecast_runbook = run_cli("forecast-runbook")
    forecast_runbook_payload = json.loads(forecast_runbook.stdout)
    if forecast_runbook_payload["entrypoints"]["mcpTool"] != "ope_forecast_run":
        raise AssertionError("CLI forecast-runbook should identify the forecast-run MCP tool")
    playbooks = {item["outcomeClass"]: item for item in forecast_runbook_payload["outcomePlaybooks"]}
    if set(playbooks) != expected_classes:
        raise AssertionError("CLI forecast-runbook should cover every intake outcome class")
    if playbooks["accepted"]["nextActionLabel"] != "read_forecast_card":
        raise AssertionError("CLI forecast-runbook should send accepted runs to the forecast card")
    if playbooks["blocked"]["nextActionLabel"] != "request_approval":
        raise AssertionError("CLI forecast-runbook should ask approval for blocked runs")
    if forecast_runbook_payload["exampleSequence"]["forecastId"] != "forecast-602":
        raise AssertionError("CLI forecast-runbook should bind the accepted forecast example")

    source_handoff_runbook = run_cli("source-handoff-runbook")
    source_handoff_runbook_payload = json.loads(source_handoff_runbook.stdout)
    if source_handoff_runbook_payload["entrypoints"]["runbookSchema"] != "spec/source-handoff-setup-runbook.schema.json":
        raise AssertionError("CLI source-handoff-runbook should identify the runbook schema")
    source_handoff_playbooks = {
        item["case"]: item
        for item in source_handoff_runbook_payload["casePlaybooks"]
    }
    if source_handoff_playbooks["confirmed_builder_draft"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI source-handoff-runbook should bind the confirmed handoff forecast")
    if source_handoff_playbooks["confirmed_builder_draft"]["scored"] is not True:
        raise AssertionError("CLI source-handoff-runbook should expose resolved scoring for the confirmed handoff")
    if source_handoff_playbooks["unconfirmed_builder_draft"]["nextActionLabel"] != "ask_mapping_confirmation":
        raise AssertionError("CLI source-handoff-runbook should keep unconfirmed drafts gated")
    if source_handoff_playbooks["contains_secret"]["mustNotForecast"] is not True:
        raise AssertionError("CLI source-handoff-runbook should forbid rejected source forecasts")

    private_setup_workflow = run_cli("private-setup-workflow")
    private_setup_workflow_payload = json.loads(private_setup_workflow.stdout)
    if private_setup_workflow_payload["scope"] != "domain_agnostic":
        raise AssertionError("CLI private-setup-workflow should be domain agnostic")
    phases = [item["phase"] for item in private_setup_workflow_payload["phases"]]
    if phases != [
        "source_discovery",
        "mapping_confirmation",
        "source_intake",
        "method_gating",
        "forecast_execution",
        "recalculation",
        "resolution",
        "scoring",
    ]:
        raise AssertionError("CLI private-setup-workflow should expose the full setup phase order")
    source_support = {
        item["sourceKind"]: item
        for item in private_setup_workflow_payload["supportedSourceKinds"]
    }
    if source_support["private_api"]["allowedInCurrentFixture"]:
        raise AssertionError("CLI private-setup-workflow should not allow private API fixtures yet")
    if source_support["private_database"]["allowedInCurrentFixture"]:
        raise AssertionError("CLI private-setup-workflow should not allow private database fixtures yet")
    if source_support["manual_upload"]["allowedInCurrentFixture"]:
        raise AssertionError("CLI private-setup-workflow should not allow manual upload fixtures yet")
    reference = private_setup_workflow_payload["referenceImplementation"]
    if reference["forecastId"] != "forecast-1102" or reference["referenceDomain"] != "weather-logistics":
        raise AssertionError("CLI private-setup-workflow should bind the source-handoff reference fixture")

    private_source_adapters = run_cli("private-source-adapters")
    private_source_adapters_payload = json.loads(private_source_adapters.stdout)
    if private_source_adapters_payload["boundPrivateSetupWorkflowId"] != "privatesetupworkflow-001":
        raise AssertionError("CLI private-source-adapters should bind the private setup workflow")
    adapters = {
        item["sourceKind"]: item
        for item in private_source_adapters_payload["adapters"]
    }
    if set(adapters) != set(source_support):
        raise AssertionError("CLI private-source-adapters should cover every workflow source kind")
    if adapters["local_file"]["implementationStatus"] != "implemented_fixture":
        raise AssertionError("CLI private-source-adapters should expose local files as fixture implemented")
    if adapters["local_file"]["nextAction"] != "use_source_builder":
        raise AssertionError("CLI private-source-adapters should route local files to source builder")
    if adapters["manual_mapping"]["approvalRequired"] is not True:
        raise AssertionError("CLI private-source-adapters should approval-gate manual mapping")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        item = adapters[source_kind]
        if item["setupOutcomeIfRequested"] != "runtime_not_implemented":
            raise AssertionError(f"CLI private-source-adapters should keep {source_kind} runtime-not-implemented")
        if item["canFetchLive"] or item["canExecuteInNormalChecks"] or item["canParseGeneric"]:
            raise AssertionError(f"CLI private-source-adapters should keep {source_kind} non-executable")
    if any(item["canStoreSecrets"] for item in adapters.values()):
        raise AssertionError("CLI private-source-adapters should not allow secret storage")
    boundary = private_source_adapters_payload["executionBoundary"]
    if boundary["declarationsDoNotExecute"] is not True or boundary["normalChecksOffline"] is not True:
        raise AssertionError("CLI private-source-adapters should preserve declaration-only offline checks")

    private_source_adapter_outcomes = run_cli("private-source-adapter-outcomes")
    private_source_adapter_outcomes_payload = json.loads(private_source_adapter_outcomes.stdout)
    if private_source_adapter_outcomes_payload["boundPrivateSourceAdapterCapabilityId"] != "privatesourceadaptercapability-001":
        raise AssertionError("CLI private-source-adapter-outcomes should bind adapter capabilities")
    outcome_rows = {
        item["sourceKind"]: item
        for item in private_source_adapter_outcomes_payload["outcomeRows"]
    }
    for source_kind in adapters:
        if outcome_rows[source_kind]["capabilityBindingStatus"] != "bound_adapter":
            raise AssertionError(f"CLI private-source-adapter-outcomes should bind {source_kind}")
    if outcome_rows["local_file"]["agentNextAction"] != "run_source_builder":
        raise AssertionError("CLI private-source-adapter-outcomes should route local files to source builder")
    if outcome_rows["manual_mapping"]["outcomeClass"] != "approval_required_fixture":
        raise AssertionError("CLI private-source-adapter-outcomes should require manual mapping confirmation")
    if outcome_rows["manual_upload"]["outcomeClass"] != "planned_runtime":
        raise AssertionError("CLI private-source-adapter-outcomes should keep manual upload planned-only")
    for source_kind in ("private_api", "private_database"):
        if outcome_rows[source_kind]["outcomeClass"] != "credential_missing":
            raise AssertionError(f"CLI private-source-adapter-outcomes should surface {source_kind} credential boundary")
        if outcome_rows[source_kind]["hasCredentialRuntime"] is not False:
            raise AssertionError(f"CLI private-source-adapter-outcomes should keep {source_kind} credential runtime absent")
    if outcome_rows["unregistered_source"]["setupOutcomeClass"] != "unsupported_source":
        raise AssertionError("CLI private-source-adapter-outcomes should reject unregistered source kinds")
    if outcome_rows["unsafe_source"]["setupOutcomeClass"] != "rejected_source":
        raise AssertionError("CLI private-source-adapter-outcomes should reject unsafe source kinds")
    for row in outcome_rows.values():
        if row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
            raise AssertionError("CLI private-source-adapter-outcomes should not create forecast or scoring records")
    outcome_boundary = private_source_adapter_outcomes_payload["executionBoundary"]
    if outcome_boundary["matrixDoesNotExecute"] is not True or outcome_boundary["storesCredentials"] is not False:
        raise AssertionError("CLI private-source-adapter-outcomes should stay non-executing and credential-free")

    private_source_adapter_bridge = run_cli("private-source-adapter-bridge")
    private_source_adapter_bridge_payload = json.loads(private_source_adapter_bridge.stdout)
    if private_source_adapter_bridge_payload["boundPrivateSourceAdapterOutcomeMatrixId"] != "privateadapteroutcomematrix-001":
        raise AssertionError("CLI private-source-adapter-bridge should bind adapter outcome matrix")
    bridge_rows = {
        item["sourceKind"]: item
        for item in private_source_adapter_bridge_payload["bridgeRows"]
    }
    if set(bridge_rows) != set(outcome_rows):
        raise AssertionError("CLI private-source-adapter-bridge should cover every outcome row")
    if bridge_rows["local_file"]["currentCommand"] != "python3 scripts/ope.py source-builder":
        raise AssertionError("CLI private-source-adapter-bridge should route local files to source-builder")
    if "draft_source_manifest" not in bridge_rows["local_file"]["allowedDownstreamOutputs"]:
        raise AssertionError("CLI private-source-adapter-bridge should allow local draft manifest downstream")
    if bridge_rows["manual_mapping"]["retryCommand"] != "python3 scripts/ope.py source-handoff --case confirmed_builder_draft":
        raise AssertionError("CLI private-source-adapter-bridge should route confirmed mappings to source-handoff")
    if bridge_rows["manual_mapping"]["currentCommand"] != "none":
        raise AssertionError("CLI private-source-adapter-bridge should not run manual mapping before confirmation")
    if bridge_rows["auto_evidence_connector"]["currentCommand"] != "python3 scripts/ope.py gather-evidence":
        raise AssertionError("CLI private-source-adapter-bridge should route auto evidence to fixture gathering")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        row = bridge_rows[source_kind]
        if row["allowedEntrypoint"] != "no_current_entrypoint":
            raise AssertionError(f"CLI private-source-adapter-bridge should block {source_kind} entrypoint")
        if row["allowedDownstreamOutputs"]:
            raise AssertionError(f"CLI private-source-adapter-bridge should keep {source_kind} non-generating")
    for source_kind in ("unregistered_source", "unsafe_source"):
        if bridge_rows[source_kind]["allowedEntrypoint"] != "no_current_entrypoint":
            raise AssertionError(f"CLI private-source-adapter-bridge should stop {source_kind}")
    for row in bridge_rows.values():
        if row["bridgeCreatesOutputs"] or row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
            raise AssertionError("CLI private-source-adapter-bridge should not create outputs")
    bridge_boundary = private_source_adapter_bridge_payload["executionBoundary"]
    if bridge_boundary["bridgeDoesNotExecute"] is not True or bridge_boundary["onlyRoutesToCheckedEntrypoints"] is not True:
        raise AssertionError("CLI private-source-adapter-bridge should stay non-executing and route checked entrypoints")

    private_setup_requests = run_cli("private-setup-requests")
    private_setup_requests_payload = json.loads(private_setup_requests.stdout)
    if private_setup_requests_payload["boundPrivateSourceAdapterIntakeBridgeId"] != "privateadapterintakebridge-001":
        raise AssertionError("CLI private-setup-requests should bind adapter bridge")
    request_rows = {
        item["selectedSourceKind"]: item
        for item in private_setup_requests_payload["requestRows"]
    }
    if set(request_rows) != set(bridge_rows):
        raise AssertionError("CLI private-setup-requests should cover every bridge source kind")
    if request_rows["local_file"]["routeDecision"] != "run_source_builder":
        raise AssertionError("CLI private-setup-requests should route local files to source-builder")
    if request_rows["manual_mapping"]["routeDecision"] != "request_mapping_confirmation":
        raise AssertionError("CLI private-setup-requests should require mapping confirmation")
    if request_rows["auto_evidence_connector"]["routeDecision"] != "use_fixture_evidence":
        raise AssertionError("CLI private-setup-requests should route auto evidence to fixture evidence")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        if request_rows[source_kind]["routeDecision"] != "wait_for_runtime":
            raise AssertionError(f"CLI private-setup-requests should wait for {source_kind} runtime")
    if request_rows["unregistered_source"]["routeDecision"] != "replace_source":
        raise AssertionError("CLI private-setup-requests should replace unregistered sources")
    if request_rows["unsafe_source"]["routeDecision"] != "stop":
        raise AssertionError("CLI private-setup-requests should stop unsafe sources")
    for row in request_rows.values():
        if row["createsOutputs"] or row["canReadPrivateData"] or row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
            raise AssertionError("CLI private-setup-requests should not read, forecast, score, or create outputs")
    request_boundary = private_setup_requests_payload["executionBoundary"]
    if request_boundary["requestSetDoesNotExecute"] is not True or request_boundary["routesOnlyThroughAdapterBridge"] is not True:
        raise AssertionError("CLI private-setup-requests should stay non-executing and bridge-routed")

    private_setup_actions = run_cli("private-setup-actions")
    private_setup_actions_payload = json.loads(private_setup_actions.stdout)
    if private_setup_actions_payload["count"] != 8:
        raise AssertionError("CLI private-setup-actions should expose eight first-action fixtures")
    action_rows = {
        item["sourceKind"]: item
        for item in private_setup_actions_payload["actions"]
    }
    if set(action_rows) != set(request_rows):
        raise AssertionError("CLI private-setup-actions should cover every request source kind")
    if action_rows["local_file"]["actionStatus"] != "ready_to_run_checked_command":
        raise AssertionError("CLI private-setup-actions should make local files ready for source-builder")
    if action_rows["manual_mapping"]["actionStatus"] != "confirmation_required":
        raise AssertionError("CLI private-setup-actions should require manual mapping confirmation")
    if action_rows["auto_evidence_connector"]["actionStatus"] != "fixture_ready":
        raise AssertionError("CLI private-setup-actions should make auto evidence fixture-ready")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        if action_rows[source_kind]["actionStatus"] != "runtime_not_implemented":
            raise AssertionError(f"CLI private-setup-actions should wait for {source_kind} runtime")
    if action_rows["unregistered_source"]["actionStatus"] != "source_replacement_required":
        raise AssertionError("CLI private-setup-actions should ask for unregistered source replacement")
    if action_rows["unsafe_source"]["actionStatus"] != "rejected_unsafe_source":
        raise AssertionError("CLI private-setup-actions should reject unsafe sources")
    for row in action_rows.values():
        boundary = row["executionBoundary"]
        if boundary["dispatcherDoesNotExecute"] is not True or boundary["runsSuggestedCommand"] is not False:
            raise AssertionError("CLI private-setup-actions should stay non-executing")
        if boundary["createsForecastArtifacts"] or boundary["createsScoringRecords"] or boundary["storesCredentials"]:
            raise AssertionError("CLI private-setup-actions should not forecast, score, or store credentials")

    private_setup_action = run_cli("private-setup-action", "--request-id", "privatesetuprequest-001")
    private_setup_action_payload = json.loads(private_setup_action.stdout)
    if private_setup_action_payload["sourceKind"] != "local_file":
        raise AssertionError("CLI private-setup-action should dispatch request id to local file")
    if private_setup_action_payload["commandToRun"] != "python3 scripts/ope.py source-builder":
        raise AssertionError("CLI private-setup-action should expose checked source-builder command")
    private_api_action = run_cli("private-setup-action", "--request-id", "privatesetuprequest-005")
    private_api_action_payload = json.loads(private_api_action.stdout)
    if private_api_action_payload["actionStatus"] != "runtime_not_implemented":
        raise AssertionError("CLI private-setup-action should keep private API runtime planned-only")

    with tempfile.TemporaryDirectory() as tmp:
        unknown_request = Path(tmp) / "unknown-private-setup-request.json"
        unknown_request.write_text(
            json.dumps(
                {
                    "privateSetupRequestId": "privatesetuprequest-990",
                    "selectedSourceKind": "spreadsheet_macro",
                    "sourcePolicy": {
                        "dataMode": "provided",
                        "allowedSourceKinds": ["spreadsheet_macro"],
                        "approvalStatus": "confirmed",
                        "allowLiveFetch": False,
                        "allowCredentialUse": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        unknown_action = subprocess.run(
            [sys.executable, "scripts/ope.py", "private-setup-action", "--input", str(unknown_request)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if unknown_action.returncode != 2:
            raise AssertionError("CLI private-setup-action unknown source should exit 2")
        unknown_payload = json.loads(unknown_action.stdout)
        if unknown_payload["error"]["code"] != "unknown_source_kind":
            raise AssertionError("CLI private-setup-action should sanitize unknown source kind")
        if unknown_payload["executionBoundary"]["runsSuggestedCommand"] is not False:
            raise AssertionError("CLI private-setup-action unknown source should not execute")

    private_setup_action_runbook = run_cli("private-setup-action-runbook")
    private_setup_action_runbook_payload = json.loads(private_setup_action_runbook.stdout)
    if private_setup_action_runbook_payload["runtimeStatus"] != "runbook_guidance_only":
        raise AssertionError("CLI private-setup-action-runbook should be guidance-only")
    expected_action_statuses = {
        "ready_to_run_checked_command",
        "confirmation_required",
        "fixture_ready",
        "runtime_not_implemented",
        "source_replacement_required",
        "rejected_unsafe_source",
        "bad_request",
    }
    if set(private_setup_action_runbook_payload["statusCoverage"]) != expected_action_statuses:
        raise AssertionError("CLI private-setup-action-runbook should cover every first-action status")
    runbook_rows = {
        item["sourceKind"]: item
        for item in private_setup_action_runbook_payload["casePlaybooks"]
    }
    if set(runbook_rows) != set(action_rows):
        raise AssertionError("CLI private-setup-action-runbook should bind every action fixture")
    if runbook_rows["local_file"]["nextActionLabel"] != "run_source_builder":
        raise AssertionError("CLI private-setup-action-runbook should route local files to source-builder")
    if runbook_rows["local_file"]["expectedOutputClass"] != "source_manifest_build":
        raise AssertionError("CLI private-setup-action-runbook should expect local source manifest build")
    if runbook_rows["manual_mapping"]["nextActionLabel"] != "ask_mapping_confirmation":
        raise AssertionError("CLI private-setup-action-runbook should ask mapping confirmation")
    if runbook_rows["manual_mapping"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("CLI private-setup-action-runbook should preserve manual confirmation")
    if runbook_rows["auto_evidence_connector"]["nextActionLabel"] != "run_fixture_evidence":
        raise AssertionError("CLI private-setup-action-runbook should route auto evidence to fixture evidence")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        if runbook_rows[source_kind]["nextActionLabel"] != "wait_for_runtime":
            raise AssertionError(f"CLI private-setup-action-runbook should wait for {source_kind} runtime")
        if runbook_rows[source_kind]["mayEnterSourceIntakeAfterRequiredAction"] is not False:
            raise AssertionError(f"CLI private-setup-action-runbook should keep {source_kind} out of source intake")
    if runbook_rows["unregistered_source"]["nextActionLabel"] != "replace_source":
        raise AssertionError("CLI private-setup-action-runbook should ask for source replacement")
    if runbook_rows["unsafe_source"]["nextActionLabel"] != "stop_unsafe_source":
        raise AssertionError("CLI private-setup-action-runbook should stop unsafe sources")
    bad_request_rows = {
        item["errorCode"]: item
        for item in private_setup_action_runbook_payload["badRequestPlaybooks"]
    }
    if {"unknown_source_kind", "missing_approval"} - set(bad_request_rows):
        raise AssertionError("CLI private-setup-action-runbook should cover bad request classes")
    for row in list(runbook_rows.values()) + list(bad_request_rows.values()):
        if row["forecastExecutionAllowed"] or row["scoringAllowed"]:
            raise AssertionError("CLI private-setup-action-runbook should not allow forecast or scoring")
        if row["nextActionLabel"] in {"wait_for_runtime", "replace_source", "stop_unsafe_source", "fix_bad_request"}:
            if row["mayEnterSourceIntakeAfterRequiredAction"]:
                raise AssertionError("CLI private-setup-action-runbook should keep blocked rows out of source intake")
    runbook_boundary = private_setup_action_runbook_payload["executionBoundary"]
    if runbook_boundary["runbookDoesNotExecute"] is not True or runbook_boundary["runsSuggestedCommand"] is not False:
        raise AssertionError("CLI private-setup-action-runbook should stay non-executing")

    private_setup_bundles = run_cli("private-setup-bundles")
    private_setup_bundles_payload = json.loads(private_setup_bundles.stdout)
    if private_setup_bundles_payload["count"] != 10:
        raise AssertionError("CLI private-setup-bundles should expose eight known and two bad-request bundles")
    bundle_rows = {
        item["sourceKind"]: item
        for item in private_setup_bundles_payload["bundles"]
        if item["bundleKind"] == "known_request"
    }
    bad_bundle_rows = {
        item["actionSummary"]["errorCode"]: item
        for item in private_setup_bundles_payload["bundles"]
        if item["bundleKind"] == "bad_request_example"
    }
    if set(bundle_rows) != set(request_rows):
        raise AssertionError("CLI private-setup-bundles should cover every request source kind")
    if {"unknown_source_kind", "missing_approval"} - set(bad_bundle_rows):
        raise AssertionError("CLI private-setup-bundles should include bad-request examples")
    if bundle_rows["local_file"]["runbookGuidance"]["nextActionLabel"] != "run_source_builder":
        raise AssertionError("CLI private-setup-bundles should route local file to source-builder")
    if bundle_rows["manual_mapping"]["runbookGuidance"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("CLI private-setup-bundles should preserve mapping confirmation")
    if bundle_rows["auto_evidence_connector"]["runbookGuidance"]["expectedOutputClass"] != "evidence_source_set":
        raise AssertionError("CLI private-setup-bundles should expose auto evidence source-set output")
    for source_kind in ("manual_upload", "private_api", "private_database"):
        bundle = bundle_rows[source_kind]
        if bundle["runbookGuidance"]["nextActionLabel"] != "wait_for_runtime":
            raise AssertionError(f"CLI private-setup-bundles should wait for {source_kind} runtime")
        if bundle["runbookGuidance"]["mayEnterSourceIntakeAfterRequiredAction"] is not False:
            raise AssertionError(f"CLI private-setup-bundles should keep {source_kind} out of source intake")
    if bundle_rows["unsafe_source"]["runbookGuidance"]["nextActionLabel"] != "stop_unsafe_source":
        raise AssertionError("CLI private-setup-bundles should stop unsafe sources")
    for bundle in private_setup_bundles_payload["bundles"]:
        if bundle["claimBoundary"]["bundleDoesNotPredict"] is not True:
            raise AssertionError("CLI private-setup-bundles should not predict")
        if bundle["claimBoundary"]["forecastExecutionAllowed"] or bundle["claimBoundary"]["scoringAllowed"]:
            raise AssertionError("CLI private-setup-bundles should block forecast and scoring claims")
        if bundle["executionBoundary"]["bundleDoesNotExecute"] is not True:
            raise AssertionError("CLI private-setup-bundles should stay non-executing")
        if bundle["executionBoundary"]["runsSuggestedCommand"] is not False:
            raise AssertionError("CLI private-setup-bundles should not run suggested commands")

    private_setup_bundle = run_cli("private-setup-bundle", "--request-id", "privatesetuprequest-001")
    private_setup_bundle_payload = json.loads(private_setup_bundle.stdout)
    if private_setup_bundle_payload["sourceKind"] != "local_file":
        raise AssertionError("CLI private-setup-bundle should return local file by request id")
    unknown_bundle = run_cli("private-setup-bundle", "--case", "unknown_source_kind")
    unknown_bundle_payload = json.loads(unknown_bundle.stdout)
    if unknown_bundle_payload["actionSummary"]["errorCode"] != "unknown_source_kind":
        raise AssertionError("CLI private-setup-bundle should expose unknown source bad-request bundle")

    adapter_runbook = run_cli("private-setup-adapter-runbook")
    adapter_runbook_payload = json.loads(adapter_runbook.stdout)
    sequence_ops = [item["operation"] for item in adapter_runbook_payload["operationSequence"]]
    if sequence_ops[:5] != [
        "private_setup_bundle",
        "private_setup_source_builder",
        "private_setup_source_handoff",
        "private_setup_method_gate",
        "private_setup_forecast_execution",
    ]:
        raise AssertionError("CLI private-setup-adapter-runbook should expose setup adapter sequence")
    if sequence_ops[-4:] != ["forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"]:
        raise AssertionError("CLI private-setup-adapter-runbook should route generated forecasts to normal readbacks")
    adapter_branches = {item["branchName"]: item for item in adapter_runbook_payload["branchPlaybooks"]}
    if adapter_branches["mapping_confirmation_required"]["allowedNextOperation"] is not None:
        raise AssertionError("CLI private-setup-adapter-runbook should stop unconfirmed mappings")
    if adapter_branches["generated_forecast_readback"]["allowedNextOperation"] != "forecast_card":
        raise AssertionError("CLI private-setup-adapter-runbook should route generated forecasts to forecast_card")
    if adapter_runbook_payload["executionBoundary"]["runbookDoesNotExecute"] is not True:
        raise AssertionError("CLI private-setup-adapter-runbook should remain guidance-only")
    if adapter_runbook_payload["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("CLI private-setup-adapter-runbook should not run adapter calls")

    adapter_conformance = run_cli("private-setup-adapter-conformance")
    adapter_conformance_payload = json.loads(adapter_conformance.stdout)
    if adapter_conformance_payload["runtimeStatus"] != "adapter_conformance_examples_only":
        raise AssertionError("CLI private-setup-adapter-conformance should expose conformance examples")
    conformance_cases = adapter_conformance_payload["operationCases"]
    if len(conformance_cases) != 31:
        raise AssertionError("CLI private-setup-adapter-conformance should cover 31 operation cases")
    conformance_phase_counts: dict[str, int] = {}
    for case in conformance_cases:
        conformance_phase_counts[case["phase"]] = conformance_phase_counts.get(case["phase"], 0) + 1
    if conformance_phase_counts != {
        "source_builder": 6,
        "source_handoff": 7,
        "method_gate": 7,
        "forecast_execution": 7,
        "forecast_readback": 4,
    }:
        raise AssertionError("CLI private-setup-adapter-conformance phase counts drifted")
    conformance_by_case = {case["adapterCase"]: case for case in conformance_cases}
    if conformance_by_case["malformed_input"]["expectedErrorCode"] != "validation_failed":
        raise AssertionError("CLI private-setup-adapter-conformance should include sanitized validation error")
    confirmed_forecast = [
        case for case in conformance_cases
        if case["operation"] == "private_setup_forecast_execution"
        and case["adapterCase"] == "confirmed_builder_draft"
    ][0]
    if confirmed_forecast["forecastArtifactsCreated"] is not True:
        raise AssertionError("CLI private-setup-adapter-conformance should mark confirmed execution as artifact-generating")
    if confirmed_forecast["nextAction"] != "read_forecast_card":
        raise AssertionError("CLI private-setup-adapter-conformance should route generated forecasts to forecast-card readback")
    readback_operations = {
        case["operation"]
        for case in conformance_cases
        if case["phase"] == "forecast_readback"
    }
    if readback_operations != {"forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"}:
        raise AssertionError("CLI private-setup-adapter-conformance should include normal forecast readbacks")
    if adapter_conformance_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("CLI private-setup-adapter-conformance should not run commands")
    if adapter_conformance_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI private-setup-adapter-conformance should not create forecast artifacts")

    adapter_conformance_summary = run_cli("private-setup-adapter-conformance-summary")
    adapter_conformance_summary_payload = json.loads(adapter_conformance_summary.stdout)
    if adapter_conformance_summary_payload["runtimeStatus"] != "compact_adapter_conformance_summary":
        raise AssertionError("CLI private-setup-adapter-conformance-summary should expose compact conformance status")
    if adapter_conformance_summary_payload["caseTotals"]["totalCases"] != 31:
        raise AssertionError("CLI private-setup-adapter-conformance-summary should preserve total conformance cases")
    if adapter_conformance_summary_payload["bindings"]["privateSetupAdapterConformanceMatrixId"] != "privatesetupadapterconformancematrix-001":
        raise AssertionError("CLI private-setup-adapter-conformance-summary should bind the full matrix")
    if adapter_conformance_summary_payload["readSurface"]["compactSummaryDoesNotEmbedEnvelopes"] is not True:
        raise AssertionError("CLI private-setup-adapter-conformance-summary should not embed envelopes")
    if adapter_conformance_summary_payload["readSurface"]["agentOperation"] != "private_setup_adapter_conformance_summary":
        raise AssertionError("CLI private-setup-adapter-conformance-summary should name the agent operation")
    if adapter_conformance_summary_payload["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise AssertionError("CLI private-setup-adapter-conformance-summary should not execute")
    if adapter_conformance_summary_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI private-setup-adapter-conformance-summary should not create forecast artifacts")

    source_kind_selection = run_cli("private-source-kind-selection")
    source_kind_selection_payload = json.loads(source_kind_selection.stdout)
    source_kind_examples = {
        item["sourceKind"]: item for item in source_kind_selection_payload["selectionExamples"]
    }
    if len(source_kind_examples) != 8:
        raise AssertionError("CLI private-source-kind-selection should cover eight source kinds")
    if source_kind_examples["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise AssertionError("CLI private-source-kind-selection should route local files to source-builder adapter")
    if source_kind_examples["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("CLI private-source-kind-selection should require manual mapping confirmation")
    if source_kind_examples["auto_evidence_connector"]["recommendation"]["immediateAction"] != "call_fixture_evidence":
        raise AssertionError("CLI private-source-kind-selection should route auto evidence to fixture evidence")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        if source_kind_examples[source_kind]["recommendation"]["immediateAction"] != "wait_for_runtime":
            raise AssertionError(f"CLI private-source-kind-selection should keep {source_kind} planned-only")
    if source_kind_examples["unregistered_source"]["recommendation"]["immediateAction"] != "replace_source":
        raise AssertionError("CLI private-source-kind-selection should replace unregistered sources")
    if source_kind_examples["unsafe_source"]["recommendation"]["immediateAction"] != "reject_source":
        raise AssertionError("CLI private-source-kind-selection should reject unsafe sources")
    if source_kind_selection_payload["executionBoundary"]["examplesDoNotExecute"] is not True:
        raise AssertionError("CLI private-source-kind-selection should remain guidance-only")
    if source_kind_selection_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("CLI private-source-kind-selection should not run commands")

    source_kind_query_matrix = run_cli("private-source-kind-query-matrix")
    source_kind_query_matrix_payload = json.loads(source_kind_query_matrix.stdout)
    if source_kind_query_matrix_payload["runtimeStatus"] != "adapter_query_examples_only":
        raise AssertionError("CLI private-source-kind-query-matrix should expose adapter query examples")
    query_cases = source_kind_query_matrix_payload["queryCases"]
    if len(query_cases) != 10:
        raise AssertionError("CLI private-source-kind-query-matrix should cover full, selected, and unsupported queries")
    if query_cases[0]["payloadShape"] != "full_examples":
        raise AssertionError("CLI private-source-kind-query-matrix should include the full-list response")
    selected_query_cases = {
        item["sourceKind"]: item
        for item in query_cases
        if item["queryMode"] == "selected_source_kind"
    }
    if selected_query_cases["private_api"]["payloadShape"] != "selected_example_only":
        raise AssertionError("CLI private-source-kind-query-matrix should include compact selected private API response")
    if selected_query_cases["private_api"]["expectedImmediateAction"] != "wait_for_runtime":
        raise AssertionError("CLI private-source-kind-query-matrix should keep private API planned-only")
    if "selectionExamples" in selected_query_cases["private_api"]["envelope"]["payload"]:
        raise AssertionError("CLI private-source-kind-query-matrix selected response should omit full examples")
    unsupported_query = query_cases[-1]
    if unsupported_query["expectedErrorCode"] != "bad_request" or unsupported_query["envelope"]["payload"] is not None:
        raise AssertionError("CLI private-source-kind-query-matrix should include a sanitized unsupported-source error")
    if source_kind_query_matrix_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("CLI private-source-kind-query-matrix should not run commands")

    agent_envelopes = run_cli("agent-envelopes")
    agent_envelopes_payload = json.loads(agent_envelopes.stdout)
    if agent_envelopes_payload["count"] != 57:
        raise AssertionError("CLI agent-envelopes should return fifty success envelopes and seven error envelopes")
    success_operations = {
        item["operation"]
        for item in agent_envelopes_payload["envelopes"]
        if item["status"] == "ok"
    }
    if (
        "forecast_card" not in success_operations
        or "evidence_trace" not in success_operations
        or "scoring_summary" not in success_operations
        or "private_setup_bundle" not in success_operations
        or "private_setup_adapter_runbook" not in success_operations
        or "private_setup_adapter_conformance_summary" not in success_operations
        or "private_source_adapter_guidance" not in success_operations
        or "private_source_kind_selection" not in success_operations
        or "private_setup_source_builder" not in success_operations
        or "private_setup_source_handoff" not in success_operations
        or "private_setup_method_gate" not in success_operations
        or "private_setup_forecast_execution" not in success_operations
        or "setup_engine" not in success_operations
        or "resolution_jobs" not in success_operations
        or "resolution_scheduler_status" not in success_operations
        or "campaign_plan" not in success_operations
        or "campaign_status" not in success_operations
        or "campaign_health" not in success_operations
        or "campaign_append_readiness" not in success_operations
        or "campaign_calibration_status" not in success_operations
    ):
        raise AssertionError("CLI agent-envelopes should expose card, evidence trace, scoring, and private setup operations")
    readback_cards = [
        item for item in agent_envelopes_payload["envelopes"]
        if item["status"] == "ok"
        and item["operation"] == "forecast_card"
        and item["recordBinding"]["forecastId"] == "forecast-1102"
    ]
    if len(readback_cards) != 1:
        raise AssertionError("CLI agent-envelopes should include a private setup forecast-card readback example")
    if readback_cards[0]["payload"]["record"]["setupBinding"]["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("CLI agent-envelopes should preserve setup forecast run binding in readback")
    error_envelopes = [
        item for item in agent_envelopes_payload["envelopes"]
        if item["status"] == "error"
    ]
    error_cases = {
        (item["operation"], item["adapterRequest"]["inputRef"], item["error"]["code"])
        for item in error_envelopes
    }
    expected_resolution_errors = {
        ("resolution_jobs", "resolutionjobregistry-998", "not_found"),
        ("resolution_jobs", "resolutionjobregistry-997", "access_denied"),
        ("resolution_scheduler_status", "resolutionschedulerstatus-998", "validation_failed"),
        ("resolution_scheduler_status", "resolutionschedulerstatus-997", "response_too_large"),
    }
    if not expected_resolution_errors.issubset(error_cases):
        raise AssertionError("CLI agent-envelopes should include sanitized resolution readback error examples")
    if any(item["payload"] is not None for item in error_envelopes):
        raise AssertionError("CLI agent-envelopes sanitized errors should not include payloads")

    agent_protocol_map = run_cli("agent-protocol-map")
    agent_protocol_map_payload = json.loads(agent_protocol_map.stdout)
    protocol_operation_names = {
        item["operation"]
        for item in agent_protocol_map_payload["operations"]
    }
    expected_protocol_operations = success_operations | {
        "agent_integration_readiness",
        "agent_integration_candidates",
        "agent_integration_guided_forecast",
        "internal_api",
    }
    if protocol_operation_names != expected_protocol_operations:
        raise AssertionError("CLI agent-protocol-map should expose every agent operation")
    protocol_runtime = agent_protocol_map_payload["adapterContract"]["protocolRuntimeImplemented"]
    if protocol_runtime is not True:
        raise AssertionError("CLI agent-protocol-map should reflect local MCP stdio support")
    transports = {item["transport"]: item for item in agent_protocol_map_payload["transportBoundaries"]}
    if transports["mcp"]["implemented"] is not True:
        raise AssertionError("CLI agent-protocol-map should mark local MCP stdio as implemented")
    if transports["http"]["implemented"] is not False or transports["queue"]["implemented"] is not False:
        raise AssertionError("CLI agent-protocol-map should keep HTTP and queue mapping-only")
    protocol_operations = {
        item["operation"]: item
        for item in agent_protocol_map_payload["operations"]
    }
    source_selection_fields = {
        item["name"]: item
        for item in protocol_operations["private_source_kind_selection"]["inputFields"]
    }
    if source_selection_fields["sourceKind"]["type"] != "string":
        raise AssertionError("CLI agent-protocol-map should expose sourceKind for selected source-kind queries")
    conformance_summary_operation = protocol_operations["private_setup_adapter_conformance_summary"]
    if conformance_summary_operation["inputRecordType"] != "private_setup_adapter_conformance_summary":
        raise AssertionError("CLI agent-protocol-map should expose the conformance summary input type")
    if conformance_summary_operation["sideEffectLevel"] != "read_only":
        raise AssertionError("CLI agent-protocol-map should keep conformance summary read-only")
    setup_engine_operation = protocol_operations["setup_engine"]
    if setup_engine_operation["inputRecordType"] != "setup_engine":
        raise AssertionError("CLI agent-protocol-map should expose setup-engine input type")
    if setup_engine_operation["sideEffectLevel"] != "read_only":
        raise AssertionError("CLI agent-protocol-map should keep setup-engine read-only")
    setup_engine_fields = {item["name"] for item in setup_engine_operation["inputFields"]}
    if {"goal", "setupEngineRequest", "view"} - setup_engine_fields:
        raise AssertionError("CLI agent-protocol-map should expose setup-engine goal, request, and view arguments")
    if protocol_operations["resolution_jobs"]["inputRecordType"] != "resolution_job_registry":
        raise AssertionError("CLI agent-protocol-map should expose resolution job registry readbacks")
    if protocol_operations["resolution_scheduler_status"]["inputRecordType"] != "resolution_scheduler_status":
        raise AssertionError("CLI agent-protocol-map should expose scheduler status readbacks")
    if protocol_operations["resolution_scheduler_status"]["sideEffectLevel"] != "read_only":
        raise AssertionError("CLI agent-protocol-map should keep scheduler status read-only")
    if protocol_operations["campaign_status"]["inputRecordType"] != "prediction_campaign_explain":
        raise AssertionError("CLI agent-protocol-map should expose campaign status readbacks")
    if protocol_operations["campaign_calibration_status"]["sideEffectLevel"] != "read_only":
        raise AssertionError("CLI agent-protocol-map should keep campaign calibration status read-only")

    agent_call = run_cli(
        "agent-call",
        "--operation",
        "forecast_card",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    agent_call_payload = json.loads(agent_call.stdout)
    if agent_call_payload["status"] != "ok":
        raise AssertionError("CLI agent-call should return an ok envelope")
    if agent_call_payload["payload"]["record"]["forecastId"] != "forecast-602":
        raise AssertionError("CLI agent-call should bind forecast-602")

    trace_call = run_cli(
        "agent-call",
        "--operation",
        "evidence_trace",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    trace_call_payload = json.loads(trace_call.stdout)
    if trace_call_payload["payload"]["record"]["recordBinding"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("CLI evidence-trace agent-call should bind the source set")

    setup_engine_call = run_cli(
        "agent-call",
        "--operation",
        "setup_engine",
        "--goal",
        "add predictions to my app",
        "--view",
        "summary",
    )
    setup_engine_call_payload = json.loads(setup_engine_call.stdout)
    if setup_engine_call_payload["status"] != "ok":
        raise AssertionError("CLI setup-engine agent-call should return an ok envelope")
    if setup_engine_call_payload["payload"]["view"] != "summary":
        raise AssertionError("CLI setup-engine agent-call should preserve requested view")
    if setup_engine_call_payload["payload"]["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("CLI setup-engine agent-call should render setup before forecast artifacts")
    if setup_engine_call_payload["payload"]["forecastCardPreview"]["probabilityAvailable"] is not False:
        raise AssertionError("CLI setup-engine agent-call preview must not expose probability")
    if setup_engine_call_payload["state"]["forecastStatus"] != "not_created_by_setup_engine":
        raise AssertionError("CLI setup-engine agent-call must not create forecasts")
    setup_engine_request_call = run_cli(
        "agent-call",
        "--operation",
        "setup_engine",
        "--setup-engine-request",
        "spec/fixtures/setup-engine-requests/accepted-stockout-risk-request.json",
        "--view",
        "summary",
    )
    setup_engine_request_call_payload = json.loads(setup_engine_request_call.stdout)
    if setup_engine_request_call_payload["adapterRequest"]["inputRef"] != "setupengine-001":
        raise AssertionError("CLI setup-engine request agent-call input ref drifted")
    if setup_engine_request_call_payload["payload"]["inputMode"] != "structured_request":
        raise AssertionError("CLI setup-engine request agent-call input mode drifted")
    if setup_engine_request_call_payload["payload"]["requestSummary"]["setupEngineRequestId"] != "setupenginerequest-001":
        raise AssertionError("CLI setup-engine request agent-call summary id drifted")
    if setup_engine_request_call_payload["payload"]["requestSummary"]["readyForSourceIntake"] is not True:
        raise AssertionError("CLI setup-engine request agent-call readiness drifted")

    private_setup_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_bundle",
        "--private-setup-request-id",
        "privatesetuprequest-001",
    )
    private_setup_call_payload = json.loads(private_setup_call.stdout)
    if private_setup_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-bundle agent-call should return an ok envelope")
    if private_setup_call_payload["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("CLI private-setup-bundle agent-call should preserve request binding")
    if private_setup_call_payload["payload"]["executionBoundary"]["runsSuggestedCommand"] is not False:
        raise AssertionError("CLI private-setup-bundle agent-call should not execute setup commands")

    adapter_runbook_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_adapter_runbook",
    )
    adapter_runbook_call_payload = json.loads(adapter_runbook_call.stdout)
    if adapter_runbook_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-adapter-runbook agent-call should return an ok envelope")
    adapter_runbook_call_record = adapter_runbook_call_payload["payload"]
    if adapter_runbook_call_record["privateSetupAdapterChainRunbookId"] != "privatesetupadapterchainrunbook-001":
        raise AssertionError("CLI private-setup-adapter-runbook should return the checked runbook")
    if adapter_runbook_call_record["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("CLI private-setup-adapter-runbook should not execute adapter calls")
    if adapter_runbook_call_record["operationSequence"][-4]["operation"] != "forecast_card":
        raise AssertionError("CLI private-setup-adapter-runbook should route generated forecasts to forecast_card")

    adapter_conformance_summary_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_adapter_conformance_summary",
    )
    adapter_conformance_summary_call_payload = json.loads(adapter_conformance_summary_call.stdout)
    if adapter_conformance_summary_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-adapter-conformance-summary agent-call should return an ok envelope")
    adapter_conformance_summary_call_record = adapter_conformance_summary_call_payload["payload"]
    if adapter_conformance_summary_call_record["caseTotals"]["totalCases"] != 31:
        raise AssertionError("CLI private-setup-adapter-conformance-summary agent-call should return case totals")
    if adapter_conformance_summary_call_record["readSurface"]["compactSummaryDoesNotEmbedEnvelopes"] is not True:
        raise AssertionError("CLI private-setup-adapter-conformance-summary agent-call should return compact summary")
    if adapter_conformance_summary_call_record["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise AssertionError("CLI private-setup-adapter-conformance-summary agent-call should not execute")
    if adapter_conformance_summary_call_record["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI private-setup-adapter-conformance-summary agent-call should not create forecast artifacts")

    resolution_jobs_call = run_cli(
        "agent-call",
        "--operation",
        "resolution_jobs",
    )
    resolution_jobs_call_payload = json.loads(resolution_jobs_call.stdout)
    if resolution_jobs_call_payload["status"] != "ok":
        raise AssertionError("CLI resolution-jobs agent-call should return an ok envelope")
    resolution_jobs_call_record = resolution_jobs_call_payload["payload"]
    if resolution_jobs_call_record["summary"]["pendingDueCount"] != 1:
        raise AssertionError("CLI resolution-jobs agent-call should expose due work")
    if resolution_jobs_call_record["executionBoundary"]["registryExecutesResolvers"] is not False:
        raise AssertionError("CLI resolution-jobs agent-call should not execute resolvers")

    scheduler_status_call = run_cli(
        "agent-call",
        "--operation",
        "resolution_scheduler_status",
    )
    scheduler_status_call_payload = json.loads(scheduler_status_call.stdout)
    if scheduler_status_call_payload["status"] != "ok":
        raise AssertionError("CLI resolution-scheduler-status agent-call should return an ok envelope")
    scheduler_status_record = scheduler_status_call_payload["payload"]
    if scheduler_status_record["lastTick"]["tickStatus"] != "due_pending":
        raise AssertionError("CLI resolution-scheduler-status agent-call should expose the latest tick")
    if scheduler_status_record["executionMode"] != "dry_run":
        raise AssertionError("CLI resolution-scheduler-status agent-call should expose dry-run mode")
    if scheduler_status_record["logPath"] != ".ope/live/resolution-scheduler/scheduler-runs.jsonl":
        raise AssertionError("CLI resolution-scheduler-status agent-call should expose the log path")
    if scheduler_status_record["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("CLI resolution-scheduler-status agent-call should not execute resolvers")

    campaign_status_call = run_cli(
        "agent-call",
        "--operation",
        "campaign_status",
    )
    campaign_status_call_payload = json.loads(campaign_status_call.stdout)
    if campaign_status_call_payload["status"] != "ok":
        raise AssertionError("CLI campaign-status agent-call should return an ok envelope")
    campaign_status_record = campaign_status_call_payload["payload"]
    if campaign_status_record["campaignSnapshot"]["nextForecastId"] != "forecast-1301":
        raise AssertionError("CLI campaign-status agent-call should expose forecast-1301")
    if campaign_status_record["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("CLI campaign-status agent-call should keep quality claims blocked")

    database_runtime_call = run_cli(
        "agent-call",
        "--operation",
        "database_source_adapter_runtime_status",
    )
    database_runtime_call_payload = json.loads(database_runtime_call.stdout)
    if database_runtime_call_payload["status"] != "ok":
        raise AssertionError("CLI database source-adapter runtime agent-call should return an ok envelope")
    database_runtime_call_record = database_runtime_call_payload["payload"]
    if database_runtime_call_record["runtimeStatus"] != "approved_database_source_adapter_runtime_checked":
        raise AssertionError("CLI database source-adapter runtime agent-call status drifted")
    if database_runtime_call_payload["adapterRequest"]["inputRecordType"] != "database_source_adapter_runtime":
        raise AssertionError("CLI database source-adapter runtime agent-call input type drifted")
    if database_runtime_call_record["summary"]["approvedExecutionPathCount"] != 1:
        raise AssertionError("CLI database source-adapter runtime agent-call should expose one approved path")
    if database_runtime_call_record["executionBoundary"]["normalChecksConnectToDatabase"] is not False:
        raise AssertionError("CLI database source-adapter runtime agent-call must not connect to databases")
    if database_runtime_call_record["executionBoundary"]["credentialValuesStored"] is not False:
        raise AssertionError("CLI database source-adapter runtime agent-call must not store credentials")
    if database_runtime_call_record["executionBoundary"]["rawPrivateRowsStored"] is not False:
        raise AssertionError("CLI database source-adapter runtime agent-call must not store raw rows")

    source_guidance_call = run_cli(
        "agent-call",
        "--operation",
        "private_source_adapter_guidance",
    )
    source_guidance_call_payload = json.loads(source_guidance_call.stdout)
    if source_guidance_call_payload["status"] != "ok":
        raise AssertionError("CLI private-source-adapter-guidance agent-call should return an ok envelope")
    source_guidance_record = source_guidance_call_payload["payload"]
    if source_guidance_record["bindingSummary"]["privateSourceAdapterCapabilityId"] != "privatesourceadaptercapability-001":
        raise AssertionError("CLI private-source-adapter-guidance should bind capabilities")
    source_guidance_summary = {item["sourceKind"]: item for item in source_guidance_record["sourceKindSummary"]}
    if source_guidance_summary["local_file"]["allowedEntrypoint"] != "source_builder":
        raise AssertionError("CLI private-source-adapter-guidance should route local files to source-builder")
    if source_guidance_summary["private_api"]["allowedEntrypoint"] != "no_current_entrypoint":
        raise AssertionError("CLI private-source-adapter-guidance should keep private API planned-only")
    if source_guidance_record["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("CLI private-source-adapter-guidance should not execute adapter calls")
    if source_guidance_record["executionBoundary"]["createsSourceManifests"] is not False:
        raise AssertionError("CLI private-source-adapter-guidance should not create source manifests")

    source_kind_selection_call = run_cli(
        "agent-call",
        "--operation",
        "private_source_kind_selection",
    )
    source_kind_selection_call_payload = json.loads(source_kind_selection_call.stdout)
    if source_kind_selection_call_payload["status"] != "ok":
        raise AssertionError("CLI private-source-kind-selection agent-call should return an ok envelope")
    source_kind_selection_record = source_kind_selection_call_payload["payload"]
    if source_kind_selection_record["privateSourceKindSelectionExamplesId"] != "privatesourcekindselectionexamples-001":
        raise AssertionError("CLI private-source-kind-selection should return the checked examples")
    source_kind_selection_rows = {
        item["sourceKind"]: item
        for item in source_kind_selection_record["selectionExamples"]
    }
    if source_kind_selection_rows["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise AssertionError("CLI private-source-kind-selection should route local files to source-builder")
    if source_kind_selection_rows["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("CLI private-source-kind-selection should require mapping confirmation")
    if source_kind_selection_rows["private_database"]["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("CLI private-source-kind-selection should keep private database planned-only")
    if source_kind_selection_record["executionBoundary"]["examplesDoNotExecute"] is not True:
        raise AssertionError("CLI private-source-kind-selection should stay guidance-only")
    if source_kind_selection_record["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("CLI private-source-kind-selection should not execute commands")

    selected_source_kind_call = run_cli(
        "agent-call",
        "--operation",
        "private_source_kind_selection",
        "--source-kind",
        "private_api",
    )
    selected_source_kind_payload = json.loads(selected_source_kind_call.stdout)
    if selected_source_kind_payload["status"] != "ok":
        raise AssertionError("CLI selected source-kind agent-call should return an ok envelope")
    selected_source_kind_record = selected_source_kind_payload["payload"]
    if selected_source_kind_record["runtimeStatus"] != "selected_example_only":
        raise AssertionError("CLI selected source-kind agent-call should return a compact selected payload")
    if selected_source_kind_record["requestedSourceKind"] != "private_api":
        raise AssertionError("CLI selected source-kind agent-call should echo the selected source kind")
    if "selectionExamples" in selected_source_kind_record:
        raise AssertionError("CLI selected source-kind agent-call should not return the full examples list")
    if selected_source_kind_record["selectedExample"]["sourceKind"] != "private_api":
        raise AssertionError("CLI selected source-kind agent-call should include the private API example")
    if selected_source_kind_record["selectedExample"]["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("CLI selected source-kind agent-call should keep private API planned-only")
    if selected_source_kind_payload["state"]["sourceMode"] != "private_api":
        raise AssertionError("CLI selected source-kind agent-call should preserve source mode")
    if selected_source_kind_record["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("CLI selected source-kind agent-call should not run commands")

    unknown_source_kind_call = run_cli_unchecked(
        "agent-call",
        "--operation",
        "private_source_kind_selection",
        "--source-kind",
        "spreadsheet_macro",
    )
    if unknown_source_kind_call.returncode != 2:
        raise AssertionError("CLI unknown source-kind agent-call should return exit code 2")
    unknown_source_kind_payload = json.loads(unknown_source_kind_call.stdout)
    if unknown_source_kind_payload["status"] != "error":
        raise AssertionError("CLI unknown source-kind agent-call should return an error envelope")
    if unknown_source_kind_payload["error"]["code"] != "bad_request":
        raise AssertionError("CLI unknown source-kind agent-call should return a bad_request code")
    if unknown_source_kind_payload["payload"] is not None:
        raise AssertionError("CLI unknown source-kind agent-call should not include a payload")
    if "/Users/" in unknown_source_kind_call.stdout or "Traceback" in unknown_source_kind_call.stderr:
        raise AssertionError("CLI unknown source-kind agent-call should keep diagnostics sanitized")

    source_builder_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_source_builder",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--source-builder-case",
        "local_draft",
    )
    source_builder_call_payload = json.loads(source_builder_call.stdout)
    if source_builder_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-source-builder agent-call should return an ok envelope")
    source_builder_result = source_builder_call_payload["payload"]
    if source_builder_result["sourceManifestBuild"]["buildStatus"] != "draft_ready":
        raise AssertionError("CLI private-setup-source-builder should produce draft-ready guidance")
    if source_builder_result["sourceManifestBuild"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("CLI private-setup-source-builder should keep forecast generation blocked")
    if source_builder_result["fieldMapping"] is None:
        raise AssertionError("CLI private-setup-source-builder should include draft field mapping")
    if source_builder_result["executionBoundary"]["readsOnlyCallerApprovedFiles"] is not True:
        raise AssertionError("CLI private-setup-source-builder should only read caller-approved files")
    if source_builder_result["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI private-setup-source-builder should not create forecast artifacts")

    rejected_source_builder_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_source_builder",
        "--source-builder-case",
        "leakage",
    )
    rejected_source_builder_payload = json.loads(rejected_source_builder_call.stdout)
    if rejected_source_builder_payload["payload"]["sourceManifestBuild"]["buildStatus"] != "rejected":
        raise AssertionError("CLI private-setup-source-builder should expose rejected cases in the payload")
    if rejected_source_builder_payload["payload"]["sourceManifest"] is not None:
        raise AssertionError("CLI private-setup-source-builder rejected cases should not include draft manifests")

    source_handoff_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_source_handoff",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--source-handoff-case",
        "confirmed_builder_draft",
    )
    source_handoff_call_payload = json.loads(source_handoff_call.stdout)
    if source_handoff_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-source-handoff agent-call should return an ok envelope")
    source_handoff_result = source_handoff_call_payload["payload"]
    if source_handoff_result["sourceIntakeHandoff"]["handoffStatus"] != "ready_for_method_gating":
        raise AssertionError("CLI private-setup-source-handoff should expose confirmed handoff readiness")
    if source_handoff_result["adapterGuidance"]["canProceedToMethodGating"] is not True:
        raise AssertionError("CLI private-setup-source-handoff should route confirmed cases toward method gates")
    if source_handoff_result["adapterGuidance"]["forecastExecutionAllowed"] is not False:
        raise AssertionError("CLI private-setup-source-handoff should not directly allow forecast execution")
    if source_handoff_result["bindingSummary"]["sourceIntakeReportId"] != "sourceintakereport-102":
        raise AssertionError("CLI private-setup-source-handoff should preserve source-intake report binding")

    blocked_source_handoff_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_source_handoff",
        "--source-handoff-case",
        "unconfirmed_builder_draft",
    )
    blocked_source_handoff_payload = json.loads(blocked_source_handoff_call.stdout)
    if blocked_source_handoff_payload["payload"]["mappingConfirmation"]["required"] is not True:
        raise AssertionError("CLI private-setup-source-handoff should preserve mapping confirmation gates")
    if blocked_source_handoff_payload["payload"]["adapterGuidance"]["canProceedToMethodGating"] is not False:
        raise AssertionError("CLI private-setup-source-handoff should block unconfirmed handoffs before method gates")

    method_gate_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_method_gate",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--method-gate-case",
        "confirmed_builder_draft",
    )
    method_gate_call_payload = json.loads(method_gate_call.stdout)
    if method_gate_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-method-gate agent-call should return an ok envelope")
    method_gate_result = method_gate_call_payload["payload"]
    if method_gate_result["sourceHandoffMethodGate"]["methodGateStatus"] != "method_selected":
        raise AssertionError("CLI private-setup-method-gate should expose selected method")
    if method_gate_result["setupBenchmarkGate"]["decision"]["executionAllowed"] is not True:
        raise AssertionError("CLI private-setup-method-gate should preserve benchmark execution permission")
    if method_gate_result["setupMethodDecision"]["decisionStatus"] != "method_selected":
        raise AssertionError("CLI private-setup-method-gate should preserve method decision")
    if method_gate_result["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not True:
        raise AssertionError("CLI private-setup-method-gate should recommend explicit setup forecast execution")
    if method_gate_result["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("CLI private-setup-method-gate should not create forecast artifacts")

    blocked_method_gate_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_method_gate",
        "--method-gate-case",
        "unconfirmed_builder_draft",
    )
    blocked_method_gate_payload = json.loads(blocked_method_gate_call.stdout)
    if blocked_method_gate_payload["payload"]["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("CLI private-setup-method-gate should preserve mapping confirmation gates")
    if blocked_method_gate_payload["payload"]["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not False:
        raise AssertionError("CLI private-setup-method-gate should block unconfirmed cases before forecast execution")

    forecast_execution_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_forecast_execution",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--forecast-execution-case",
        "confirmed_builder_draft",
    )
    forecast_execution_call_payload = json.loads(forecast_execution_call.stdout)
    if forecast_execution_call_payload["status"] != "ok":
        raise AssertionError("CLI private-setup-forecast-execution agent-call should return an ok envelope")
    forecast_execution_result = forecast_execution_call_payload["payload"]
    if forecast_execution_result["setupForecastRun"]["runStatus"] != "generated":
        raise AssertionError("CLI private-setup-forecast-execution should generate the confirmed run")
    if forecast_execution_result["bindingSummary"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI private-setup-forecast-execution should bind forecast-1102")
    if forecast_execution_result["forecastArtifacts"]["forecastArtifact"]["forecastId"] != "forecast-1102":
        raise AssertionError("CLI private-setup-forecast-execution should return the forecast artifact")
    if forecast_execution_result["executionBoundary"]["createsScoringRecords"] is not False:
        raise AssertionError("CLI private-setup-forecast-execution should not create scoring records")

    blocked_forecast_execution_call = run_cli(
        "agent-call",
        "--operation",
        "private_setup_forecast_execution",
        "--forecast-execution-case",
        "unconfirmed_builder_draft",
    )
    blocked_forecast_execution_payload = json.loads(blocked_forecast_execution_call.stdout)
    if blocked_forecast_execution_payload["payload"]["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("CLI private-setup-forecast-execution should preserve mapping confirmation gates")
    if blocked_forecast_execution_payload["payload"]["bindingSummary"]["forecastId"] is not None:
        raise AssertionError("CLI private-setup-forecast-execution should block unconfirmed cases before artifacts")

    setup_card_payload = agent_call_setup_readback("forecast_card")
    if setup_card_payload["payload"]["record"]["setupBinding"]["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("CLI forecast-card readback should expose private setup forecast run binding")
    if setup_card_payload["payload"]["record"]["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("CLI forecast-card readback should keep source-handoff quality claims blocked")

    setup_bundle_payload = agent_call_setup_readback("lifecycle_bundle")
    if setup_bundle_payload["payload"]["record"]["includedRecords"]["setupForecastRun"] != "setupforecastrun-1102":
        raise AssertionError("CLI lifecycle-bundle readback should include setup forecast run")

    setup_resolution_payload = agent_call_setup_readback("resolution_status")
    if setup_resolution_payload["payload"]["resolutionRecordId"] != "resolution-1102":
        raise AssertionError("CLI resolution-status readback should bind resolution-1102")
    if setup_resolution_payload["payload"]["qualityClaim"]["resolvedComparableSourceHandoffOutcomes"] != 1:
        raise AssertionError("CLI resolution-status readback should expose source-handoff sample count")

    setup_scoring_payload = agent_call_setup_readback("scoring_summary")
    if setup_scoring_payload["payload"]["scoringReportId"] != "scoring-1102":
        raise AssertionError("CLI scoring-summary readback should bind scoring-1102")
    if setup_scoring_payload["payload"]["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("CLI scoring-summary readback should keep quality claims blocked")

    validated = run_cli(
        "validate",
        "--input",
        "spec/fixtures/valid/binary-weather-logistics-question.json",
    )
    validation_payload = json.loads(validated.stdout)
    if validation_payload["valid"] is not True:
        raise AssertionError("CLI contract validation returned wrong decision")

    weather = run_cli(
        "weather",
        "--location",
        "warsaw",
        "--service-date",
        "2026-06-03",
        "--fixture",
        "spec/fixtures/live/open-meteo-warsaw-forecast-response.json",
        "--retrieved-at",
        "2026-06-02T09:30:00Z",
    )
    weather_payload = json.loads(weather.stdout)
    if weather_payload["normalizedFields"]["forecastDailyPrecipitationMm"] != 24:
        raise AssertionError("CLI weather normalization drifted")

    print("checked local OPE CLI")


if __name__ == "__main__":
    main()
