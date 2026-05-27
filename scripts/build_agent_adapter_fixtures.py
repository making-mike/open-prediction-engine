#!/usr/bin/env python3
"""Build or check transport-neutral agent adapter envelope fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from functools import cache
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from plan_auto_evidence import DEFAULT_REQUEST, build_plan
from build_source_manifest import CASE_ORDER as SOURCE_BUILDER_CASES
from build_source_manifest import build_case as build_source_case
from build_source_manifest import build_from_inputs, parse_inputs, parse_mapping_hints
from build_source_manifest import SourceBuildError
from generate_private_setup_agent_bundles import PrivateSetupAgentBundleError, bundle_by_request_id
from generate_private_source_adapter_capabilities import build_capabilities as build_private_source_adapter_capabilities
from generate_private_source_adapter_intake_bridge import build_bridge as build_private_source_adapter_intake_bridge
from generate_private_source_adapter_outcome_matrix import build_matrix as build_private_source_adapter_outcome_matrix
from generate_source_intake_handoff import CASE_ORDER as SOURCE_HANDOFF_CASES
from generate_source_intake_handoff import SourceIntakeHandoffError
from generate_source_intake_handoff import build_handoff as build_source_handoff
from generate_source_handoff_method_gate import CASE_ORDER as METHOD_GATE_CASES
from generate_source_handoff_method_gate import SourceHandoffMethodGateError
from generate_source_handoff_method_gate import build_case as build_source_handoff_method_gate
from read_ope_record import PublicError, read_record
from run_source_handoff_forecast import CASE_ORDER as FORECAST_EXECUTION_CASES
from run_source_handoff_forecast import SourceHandoffForecastError
from run_source_handoff_forecast import build_outputs as build_source_handoff_forecast_outputs
from run_source_handoff_forecast import output_prefix as source_handoff_forecast_output_prefix
from validate_forecast_request import load_json, validate_request


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "agent-adapter"
SCHEMA = SPEC / "agent-envelope.schema.json"
PRIVATE_SETUP_ADAPTER_RUNBOOK_SCHEMA = SPEC / "private-setup-adapter-chain-runbook.schema.json"
PRIVATE_SETUP_ADAPTER_RUNBOOK_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "private-setup-adapter-chain"
    / "ope-private-setup-adapter-chain-runbook.generated.json"
)
PRIVATE_SETUP_ADAPTER_CONFORMANCE_SUMMARY_SCHEMA = SPEC / "private-setup-adapter-conformance-summary.schema.json"
PRIVATE_SETUP_ADAPTER_CONFORMANCE_SUMMARY_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "private-setup-adapter-conformance"
    / "ope-private-setup-adapter-conformance-summary.generated.json"
)
PRIVATE_SOURCE_KIND_SELECTION_SCHEMA = SPEC / "private-source-kind-selection-examples.schema.json"
PRIVATE_SOURCE_KIND_SELECTION_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "private-source-kind-selection"
    / "ope-private-source-kind-selection-examples.generated.json"
)
RESOLUTION_JOB_REGISTRY_SCHEMA = SPEC / "resolution-job-registry.schema.json"
RESOLUTION_JOB_REGISTRY_PATH = ROOT / "spec" / "fixtures" / "generated" / "resolution-jobs" / "resolution-jobs.generated.json"
RESOLUTION_SCHEDULER_RUN_SCHEMA = SPEC / "resolution-scheduler-run.schema.json"
RESOLUTION_SCHEDULER_RUN_PATH = (
    ROOT
    / "spec"
    / "fixtures"
    / "generated"
    / "resolution-scheduler"
    / "resolution-scheduler-run.generated.json"
)
RESOLUTION_SCHEDULER_LOG_PATH = ".ope/live/resolution-scheduler/scheduler-runs.jsonl"
GENERATED_AT = "2026-06-06T12:20:00Z"
FORECAST_ID = "forecast-602"
QUESTION_ID = "question-601"
SOURCE_HANDOFF_FORECAST_ID = "forecast-1102"
SOURCE_HANDOFF_QUESTION_ID = "question-1102"
MISSING_FORECAST_ID = "forecast-999"
PRIVATE_SETUP_REQUEST_ID = "privatesetuprequest-001"
MISSING_PRIVATE_SETUP_REQUEST_ID = "privatesetuprequest-999"
SOURCE_BUILDER_ENVELOPE_CASES = [
    "local_draft",
    "contains_secret",
    "unsupported_format",
    "oversized",
    "leakage",
]
SOURCE_HANDOFF_ENVELOPE_CASES = [
    "unconfirmed_builder_draft",
    "confirmed_builder_draft",
    "insufficient_confirmed_builder_draft",
    "contains_secret",
    "unsupported_format",
    "oversized",
    "leakage",
]
METHOD_GATE_ENVELOPE_CASES = [
    "unconfirmed_builder_draft",
    "confirmed_builder_draft",
    "insufficient_confirmed_builder_draft",
    "contains_secret",
    "unsupported_format",
    "oversized",
    "leakage",
]
FORECAST_EXECUTION_ENVELOPE_CASES = [
    "unconfirmed_builder_draft",
    "confirmed_builder_draft",
    "insufficient_confirmed_builder_draft",
    "contains_secret",
    "unsupported_format",
    "oversized",
    "leakage",
]

OUTPUT_FILES = {
    "forecast_request_validation": "ope-agent-forecast-request-validation-envelope.generated.json",
    "evidence_plan": "ope-agent-evidence-plan-envelope.generated.json",
    "evidence_trace": "ope-agent-evidence-trace-envelope.generated.json",
    "forecast_card": "ope-agent-forecast-card-envelope.generated.json",
    "lifecycle_bundle": "ope-agent-lifecycle-bundle-envelope.generated.json",
    "private_setup_bundle": "ope-agent-private-setup-bundle-envelope.generated.json",
    "private_setup_adapter_runbook": "ope-agent-private-setup-adapter-runbook-envelope.generated.json",
    "private_setup_adapter_conformance_summary": "ope-agent-private-setup-adapter-conformance-summary-envelope.generated.json",
    "private_source_adapter_guidance": "ope-agent-private-source-adapter-guidance-envelope.generated.json",
    "private_source_kind_selection": "ope-agent-private-source-kind-selection-envelope.generated.json",
    "private_setup_source_builder": "ope-agent-private-setup-source-builder-envelope.generated.json",
    "private_setup_source_builder_contains_secret": "ope-agent-private-setup-source-builder-contains-secret-envelope.generated.json",
    "private_setup_source_builder_unsupported_format": "ope-agent-private-setup-source-builder-unsupported-format-envelope.generated.json",
    "private_setup_source_builder_oversized": "ope-agent-private-setup-source-builder-oversized-envelope.generated.json",
    "private_setup_source_builder_leakage": "ope-agent-private-setup-source-builder-leakage-envelope.generated.json",
    "private_setup_source_handoff_unconfirmed_builder_draft": "ope-agent-private-setup-source-handoff-unconfirmed-builder-draft-envelope.generated.json",
    "private_setup_source_handoff_confirmed_builder_draft": "ope-agent-private-setup-source-handoff-confirmed-builder-draft-envelope.generated.json",
    "private_setup_source_handoff_insufficient_confirmed_builder_draft": "ope-agent-private-setup-source-handoff-insufficient-confirmed-builder-draft-envelope.generated.json",
    "private_setup_source_handoff_contains_secret": "ope-agent-private-setup-source-handoff-contains-secret-envelope.generated.json",
    "private_setup_source_handoff_unsupported_format": "ope-agent-private-setup-source-handoff-unsupported-format-envelope.generated.json",
    "private_setup_source_handoff_oversized": "ope-agent-private-setup-source-handoff-oversized-envelope.generated.json",
    "private_setup_source_handoff_leakage": "ope-agent-private-setup-source-handoff-leakage-envelope.generated.json",
    "private_setup_method_gate_unconfirmed_builder_draft": "ope-agent-private-setup-method-gate-unconfirmed-builder-draft-envelope.generated.json",
    "private_setup_method_gate_confirmed_builder_draft": "ope-agent-private-setup-method-gate-confirmed-builder-draft-envelope.generated.json",
    "private_setup_method_gate_insufficient_confirmed_builder_draft": "ope-agent-private-setup-method-gate-insufficient-confirmed-builder-draft-envelope.generated.json",
    "private_setup_method_gate_contains_secret": "ope-agent-private-setup-method-gate-contains-secret-envelope.generated.json",
    "private_setup_method_gate_unsupported_format": "ope-agent-private-setup-method-gate-unsupported-format-envelope.generated.json",
    "private_setup_method_gate_oversized": "ope-agent-private-setup-method-gate-oversized-envelope.generated.json",
    "private_setup_method_gate_leakage": "ope-agent-private-setup-method-gate-leakage-envelope.generated.json",
    "private_setup_forecast_execution_unconfirmed_builder_draft": "ope-agent-private-setup-forecast-execution-unconfirmed-builder-draft-envelope.generated.json",
    "private_setup_forecast_execution_confirmed_builder_draft": "ope-agent-private-setup-forecast-execution-confirmed-builder-draft-envelope.generated.json",
    "private_setup_forecast_execution_insufficient_confirmed_builder_draft": "ope-agent-private-setup-forecast-execution-insufficient-confirmed-builder-draft-envelope.generated.json",
    "private_setup_forecast_execution_contains_secret": "ope-agent-private-setup-forecast-execution-contains-secret-envelope.generated.json",
    "private_setup_forecast_execution_unsupported_format": "ope-agent-private-setup-forecast-execution-unsupported-format-envelope.generated.json",
    "private_setup_forecast_execution_oversized": "ope-agent-private-setup-forecast-execution-oversized-envelope.generated.json",
    "private_setup_forecast_execution_leakage": "ope-agent-private-setup-forecast-execution-leakage-envelope.generated.json",
    "private_setup_forecast_card_readback": "ope-agent-private-setup-forecast-card-readback-envelope.generated.json",
    "private_setup_lifecycle_bundle_readback": "ope-agent-private-setup-lifecycle-bundle-readback-envelope.generated.json",
    "private_setup_resolution_status_readback": "ope-agent-private-setup-resolution-status-readback-envelope.generated.json",
    "private_setup_scoring_summary_readback": "ope-agent-private-setup-scoring-summary-readback-envelope.generated.json",
    "resolution_jobs": "ope-agent-resolution-jobs-envelope.generated.json",
    "resolution_scheduler_status": "ope-agent-resolution-scheduler-status-envelope.generated.json",
    "resolution_jobs_missing_live_workspace_error": "ope-agent-resolution-jobs-missing-live-workspace-error-envelope.generated.json",
    "resolution_jobs_unreadable_state_error": "ope-agent-resolution-jobs-unreadable-state-error-envelope.generated.json",
    "resolution_scheduler_malformed_log_error": "ope-agent-resolution-scheduler-malformed-log-error-envelope.generated.json",
    "resolution_scheduler_oversized_readback_error": "ope-agent-resolution-scheduler-oversized-readback-error-envelope.generated.json",
    "resolution_status": "ope-agent-resolution-status-envelope.generated.json",
    "scoring_summary": "ope-agent-scoring-summary-envelope.generated.json",
    "forecast_card_error": "ope-agent-sanitized-error-envelope.generated.json",
    "private_setup_bundle_error": "ope-agent-private-setup-bundle-sanitized-error-envelope.generated.json",
    "private_setup_source_builder_error": "ope-agent-private-setup-source-builder-sanitized-error-envelope.generated.json",
}

EXIT_CODES = {
    "ok": 0,
    "bad_request": 2,
    "validation_failed": 2,
    "approval_required": 3,
    "not_found": 4,
    "access_denied": 4,
    "binding_mismatch": 4,
    "conflict": 4,
    "response_too_large": 5,
    "rate_limited": 5,
    "internal_error": 1,
}


class AgentAdapterError(Exception):
    pass


@cache
def source_handoff_forecast_outputs() -> dict[str, Any]:
    return build_source_handoff_forecast_outputs()


def source_handoff_forecast_outputs_cache_info() -> Any:
    return source_handoff_forecast_outputs.cache_info()


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def nullable_binding(**values: str | None) -> dict[str, str | None]:
    binding = {
        "requestId": None,
        "pipelineRunId": None,
        "questionId": None,
        "forecastId": None,
        "evidencePlanId": None,
        "evidenceSourceSetId": None,
        "sourcePolicyId": None,
        "resolutionRecordId": None,
        "scoringReportId": None,
    }
    binding.update(values)
    return binding


def nullable_state(**values: str | None) -> dict[str, str | None]:
    state = {
        "decisionStatus": None,
        "approvalStatus": None,
        "dataMode": None,
        "planStatus": None,
        "executionMode": None,
        "sourceMode": None,
        "forecastStatus": None,
        "resolutionStatus": None,
        "scoreStatus": None,
        "qualityClaimStatus": None,
    }
    state.update(values)
    return state


def adapter(capability_mode: str) -> dict[str, str]:
    return {
        "surface": "local_cli",
        "adapterVersion": "0.1.0",
        "transport": "stdio_process",
        "capabilityMode": capability_mode,
    }


def adapter_request(
    operation: str,
    input_record_type: str,
    input_ref: str,
    *,
    question_id: str | None = None,
    forecast_id: str | None = None,
    max_bytes: int | None = None,
    caller_intent: str,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "inputRecordType": input_record_type,
        "inputRef": input_ref,
        "questionId": question_id,
        "forecastId": forecast_id,
        "maxBytes": max_bytes,
        "callerIntent": caller_intent,
    }


def envelope(
    envelope_id: str,
    operation: str,
    capability_mode: str,
    input_record_type: str,
    input_ref: str,
    payload: dict[str, Any] | None,
    *,
    question_id: str | None = None,
    forecast_id: str | None = None,
    caller_intent: str,
    record_binding: dict[str, str | None],
    state: dict[str, str | None],
    max_bytes: int | None = 65536,
    status: str = "ok",
    error: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    exit_code = 0 if status == "ok" else EXIT_CODES.get(error["code"], 1) if error else 1
    return {
        "agentEnvelopeId": envelope_id,
        "generatedAt": GENERATED_AT,
        "adapter": adapter(capability_mode),
        "operation": operation,
        "adapterRequest": adapter_request(
            operation,
            input_record_type,
            input_ref,
            question_id=question_id,
            forecast_id=forecast_id,
            max_bytes=max_bytes,
            caller_intent=caller_intent,
        ),
        "recordBinding": record_binding,
        "state": state,
        "status": status,
        "exitCode": exit_code,
        "payload": payload,
        "error": error,
        "warnings": warnings or [],
    }


def expect_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AgentAdapterError(f"{label} mismatch")


def expect_optional_equal(label: str, actual: Any, expected: Any) -> None:
    if actual is not None and expected is not None and actual != expected:
        raise AgentAdapterError(f"{label} mismatch")


def validate_status_semantics(item: dict[str, Any]) -> None:
    status = item["status"]
    if status == "ok":
        expect_equal("ok envelope exit code", item["exitCode"], 0)
        if item["error"] is not None:
            raise AgentAdapterError("ok envelope must not include an error object")
        if not isinstance(item["payload"], dict):
            raise AgentAdapterError("ok envelope must include an object payload")
        return
    if item["exitCode"] == 0:
        raise AgentAdapterError("error envelope must use a nonzero exit code")
    if item["payload"] is not None:
        raise AgentAdapterError("error envelope must not include a success payload")
    if not isinstance(item["error"], dict):
        raise AgentAdapterError("error envelope must include an error object")


def validate_record_binding(item: dict[str, Any]) -> None:
    request = item["adapterRequest"]
    binding = item["recordBinding"]
    expect_equal("adapter operation", request["operation"], item["operation"])
    expect_optional_equal("adapter request question binding", request["questionId"], binding["questionId"])
    expect_optional_equal("adapter request forecast binding", request["forecastId"], binding["forecastId"])


def validate_payload_binding(item: dict[str, Any]) -> None:
    if item["status"] == "error":
        return

    operation = item["operation"]
    request = item["adapterRequest"]
    binding = item["recordBinding"]
    payload = item["payload"]

    if operation == "forecast_request_validation":
        expect_equal("request validation input ref", payload["requestId"], request["inputRef"])
        expect_equal("request validation request binding", payload["requestId"], binding["requestId"])
        expect_equal("request validation decision state", payload["decisionStatus"], item["state"]["decisionStatus"])
        expect_equal(
            "request validation source policy binding",
            payload["auditLog"]["sourcePolicyId"],
            binding["sourcePolicyId"],
        )
        return

    if operation == "evidence_plan":
        expect_equal("evidence plan input ref", payload["evidencePlanId"], request["inputRef"])
        expect_equal("evidence plan request binding", payload["requestId"], binding["requestId"])
        expect_equal("evidence plan id binding", payload["evidencePlanId"], binding["evidencePlanId"])
        expect_equal("evidence plan source policy binding", payload["sourcePolicy"]["sourcePolicyId"], binding["sourcePolicyId"])
        expect_equal("evidence plan state", payload["planStatus"], item["state"]["planStatus"])
        return

    if operation == "evidence_trace":
        response = payload
        trace = response["record"]
        trace_binding = trace["recordBinding"]
        expect_equal("evidence trace response record id", response["recordId"], request["inputRef"])
        expect_equal("evidence trace forecast binding", trace["forecastId"], binding["forecastId"])
        expect_equal("evidence trace question binding", trace["questionId"], binding["questionId"])
        expect_equal("evidence trace request binding", trace_binding["requestId"], binding["requestId"])
        expect_equal("evidence trace pipeline binding", trace_binding["pipelineRunId"], binding["pipelineRunId"])
        expect_equal("evidence trace evidence plan binding", trace_binding["evidencePlanId"], binding["evidencePlanId"])
        expect_equal(
            "evidence trace source-set binding",
            trace_binding["evidenceSourceSetId"],
            binding["evidenceSourceSetId"],
        )
        expect_equal("evidence trace source-policy binding", trace_binding["sourcePolicyId"], binding["sourcePolicyId"])
        expect_equal("evidence trace resolution binding", trace_binding["resolutionRecordId"], binding["resolutionRecordId"])
        expect_equal("evidence trace scoring binding", trace_binding["scoringReportId"], binding["scoringReportId"])
        return

    if operation in {"forecast_card", "lifecycle_bundle"}:
        response = payload
        record = response["record"]
        expect_equal(f"{operation} response record id", response["recordId"], request["inputRef"])
        expect_equal(f"{operation} forecast binding", record["forecastId"], binding["forecastId"])
        expect_equal(f"{operation} question binding", record["questionId"], binding["questionId"])
        if operation == "forecast_card":
            request_binding = record["requestBinding"]
            links = record["links"]
            expect_equal("forecast card request binding", request_binding["requestId"], binding["requestId"])
            expect_equal("forecast card pipeline binding", request_binding["pipelineRunId"], binding["pipelineRunId"])
            expect_equal("forecast card evidence plan binding", request_binding["evidencePlanId"], binding["evidencePlanId"])
            expect_equal(
                "forecast card evidence source-set binding",
                request_binding["evidenceSourceSetId"],
                binding["evidenceSourceSetId"],
            )
            expect_equal("forecast card source policy binding", request_binding["sourcePolicyId"], binding["sourcePolicyId"])
            expect_equal("forecast card resolution binding", links["resolutionRecord"], binding["resolutionRecordId"])
            expect_equal("forecast card scoring binding", links["scoringReport"], binding["scoringReportId"])
            setup_binding = record.get("setupBinding")
            if setup_binding is not None and setup_binding["setupForecastRunId"] is not None:
                expect_equal("forecast card setup forecast binding", setup_binding["setupForecastRunId"], "setupforecastrun-1102")
                expect_equal("forecast card source handoff binding", setup_binding["sourceIntakeHandoffId"], "sourceintakehandoff-002")
                expect_equal("forecast card method gate binding", setup_binding["sourceHandoffMethodGateId"], "sourcehandoffmethodgate-002")
                expect_equal("forecast card setup method binding", setup_binding["setupMethodDecisionId"], "setupmethoddecision-102")
        else:
            included = record["includedRecords"]
            expect_equal("bundle resolution binding", included["resolutionRecord"], binding["resolutionRecordId"])
            expect_equal("bundle scoring binding", included["scoringReport"], binding["scoringReportId"])
            expect_equal("bundle pipeline binding", included["pipelineRun"], binding["pipelineRunId"])
            if included["setupForecastRun"] is not None:
                setup_run = record["records"]["setupForecastRun"]
                expect_equal("bundle setup run binding", included["setupForecastRun"], setup_run["setupForecastRunId"])
                expect_equal("bundle source handoff binding", setup_run["sourceIntakeHandoffId"], "sourceintakehandoff-002")
                expect_equal("bundle method gate binding", setup_run["sourceHandoffMethodGateId"], "sourcehandoffmethodgate-002")
        return

    if operation == "resolution_status":
        expect_equal("resolution status input ref", payload["resolutionRecordId"], request["inputRef"])
        expect_equal("resolution status forecast binding", payload["forecastId"], binding["forecastId"])
        expect_equal("resolution status question binding", payload["questionId"], binding["questionId"])
        expect_equal("resolution status record binding", payload["resolutionRecordId"], binding["resolutionRecordId"])
        expect_equal("resolution status state", payload["resolutionStatus"], item["state"]["resolutionStatus"])
        return

    if operation == "scoring_summary":
        expect_equal("scoring summary input ref", payload["scoringReportId"], request["inputRef"])
        expect_equal("scoring summary forecast binding", payload["forecastId"], binding["forecastId"])
        expect_equal("scoring summary question binding", payload["questionId"], binding["questionId"])
        expect_equal("scoring summary record binding", payload["scoringReportId"], binding["scoringReportId"])
        expect_equal("scoring summary state", payload["scoreStatus"], item["state"]["scoreStatus"])
        return

    if operation == "resolution_jobs":
        registry = payload
        expect_equal("resolution jobs input ref", registry["resolutionJobRegistryId"], request["inputRef"])
        expect_equal("resolution jobs state", "pending_due", item["state"]["resolutionStatus"])
        if registry["summary"]["pendingDueCount"] != 1:
            raise AgentAdapterError("resolution jobs should expose one due fixture job")
        if registry["executionBoundary"]["registryExecutesResolvers"] is not False:
            raise AgentAdapterError("resolution jobs must not execute resolvers")
        due_jobs = [job for job in registry["jobs"] if job["jobStatus"] == "pending_due"]
        if due_jobs[0]["agentAction"]["recommendedAction"] != "call_resolver_execute":
            raise AgentAdapterError("resolution jobs should route due jobs to checked resolver execution")
        for job in registry["jobs"]:
            boundary = job["claimBoundary"]
            if boundary["createsForecastArtifacts"] or boundary["createsResolutionArtifacts"]:
                raise AgentAdapterError("resolution jobs must not create forecast or resolution artifacts")
            if boundary["calibrationClaimAllowed"]:
                raise AgentAdapterError("resolution jobs must not create calibration claims")
        return

    if operation == "resolution_scheduler_status":
        status = payload
        tick = status["lastTick"]
        queue_states = {row["queueState"]: row for row in status["queueStatusReadbacks"]}
        expect_equal("resolution scheduler status input ref", status["resolutionSchedulerStatusId"], request["inputRef"])
        expect_equal("resolution scheduler run binding", status["resolutionSchedulerRunId"], status["schedulerRun"]["resolutionSchedulerRunId"])
        expect_equal("resolution scheduler state", tick["tickStatus"], item["state"]["resolutionStatus"])
        if status["executionMode"] != "dry_run":
            raise AgentAdapterError("resolution scheduler status fixture should expose dry-run execution mode")
        if status["logPath"] != RESOLUTION_SCHEDULER_LOG_PATH:
            raise AgentAdapterError("resolution scheduler status should expose the checked log path")
        if tick["jobSummary"]["pendingDueCount"] != 1 or tick["tickStatus"] != "due_pending":
            raise AgentAdapterError("resolution scheduler status should expose the latest due-pending tick")
        if queue_states["pending_due"]["presentInLatestTick"] is not True:
            raise AgentAdapterError("resolution scheduler status should include the pending due queue state")
        for queue_state in ["pending_not_due", "already_resolved", "invalid_state", "failed", "empty_queue"]:
            if queue_state not in queue_states:
                raise AgentAdapterError(f"resolution scheduler status missing {queue_state} readback")
        boundary = status["executionBoundary"]
        for key in [
            "statusReadExecutesScheduler",
            "executesResolvers",
            "fetchesLiveSources",
            "createsForecastArtifacts",
            "createsResolutionArtifacts",
            "createsScoringRecords",
            "hostedSchedulerCreated",
            "osSchedulerCreated",
            "calibrationClaimAllowed",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"resolution scheduler status boundary should keep {key} false")
        return

    if operation == "private_setup_bundle":
        bundle = payload
        request_summary = bundle["requestSummary"]
        action_summary = bundle["actionSummary"]
        source_policy = request_summary["sourcePolicy"]
        expect_equal("private setup bundle input ref", bundle["privateSetupAgentBundleId"], request["inputRef"])
        expect_equal("private setup request binding", request_summary["privateSetupRequestId"], binding["requestId"])
        expect_equal("private setup decision state", action_summary["routeDecision"], item["state"]["decisionStatus"])
        expect_equal("private setup approval state", source_policy["approvalStatus"], item["state"]["approvalStatus"])
        expect_equal("private setup data mode state", source_policy["dataMode"], item["state"]["dataMode"])
        expect_equal("private setup source mode state", bundle["sourceKind"], item["state"]["sourceMode"])
        if bundle["executionBoundary"]["bundleDoesNotExecute"] is not True:
            raise AgentAdapterError("private setup bundle must stay non-executing")
        if bundle["executionBoundary"]["runsSuggestedCommand"] is not False:
            raise AgentAdapterError("private setup bundle must not run suggested commands")
        if bundle["claimBoundary"]["forecastExecutionAllowed"] or bundle["claimBoundary"]["scoringAllowed"]:
            raise AgentAdapterError("private setup bundle must not allow forecast execution or scoring")
        return

    if operation == "private_setup_adapter_runbook":
        runbook = payload
        source_path = runbook["sourcePath"]
        boundary = runbook["executionBoundary"]
        expect_equal("private setup adapter runbook input ref", runbook["privateSetupAdapterChainRunbookId"], request["inputRef"])
        expect_equal("private setup adapter runbook request binding", source_path["privateSetupRequestId"], binding["requestId"])
        expect_equal("private setup adapter runbook state", runbook["runtimeStatus"], item["state"]["planStatus"])
        expect_equal("private setup adapter runbook source mode", source_path["sourceKind"], item["state"]["sourceMode"])
        expected_sequence = [
            "private_setup_bundle",
            "private_setup_source_builder",
            "private_setup_source_handoff",
            "private_setup_method_gate",
            "private_setup_forecast_execution",
            "forecast_card",
            "lifecycle_bundle",
            "resolution_status",
            "scoring_summary",
        ]
        if [step["operation"] for step in runbook["operationSequence"]] != expected_sequence:
            raise AgentAdapterError("private setup adapter runbook should preserve the checked operation sequence")
        if boundary["runbookDoesNotExecute"] is not True or boundary["runsAdapterCalls"] is not False:
            raise AgentAdapterError("private setup adapter runbook must stay non-executing")
        for key in [
            "readsPrivateData",
            "createsSourceManifests",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
            "createsHostedRuntime",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"private setup adapter runbook boundary should keep {key} false")
        branches = {item["branchName"]: item for item in runbook["branchPlaybooks"]}
        if branches["mapping_confirmation_required"]["allowedNextOperation"] is not None:
            raise AgentAdapterError("private setup adapter runbook should stop unconfirmed mappings")
        if branches["generated_forecast_readback"]["allowedNextOperation"] != "forecast_card":
            raise AgentAdapterError("private setup adapter runbook should route generated forecasts to normal readback")
        return

    if operation == "private_source_adapter_guidance":
        guidance = payload
        capability = guidance["capability"]
        matrix = guidance["outcomeMatrix"]
        bridge = guidance["intakeBridge"]
        summary = guidance["bindingSummary"]
        expect_equal("private source adapter guidance input ref", capability["privateSourceAdapterCapabilityId"], request["inputRef"])
        expect_equal(
            "private source adapter capability binding",
            capability["privateSourceAdapterCapabilityId"],
            summary["privateSourceAdapterCapabilityId"],
        )
        expect_equal(
            "private source adapter matrix binding",
            matrix["privateSourceAdapterOutcomeMatrixId"],
            summary["privateSourceAdapterOutcomeMatrixId"],
        )
        expect_equal(
            "private source adapter bridge binding",
            bridge["privateSourceAdapterIntakeBridgeId"],
            summary["privateSourceAdapterIntakeBridgeId"],
        )
        expect_equal("private source adapter workflow binding", capability["boundPrivateSetupWorkflowId"], summary["privateSetupWorkflowId"])
        expect_equal(
            "private source adapter matrix capability binding",
            matrix["boundPrivateSourceAdapterCapabilityId"],
            capability["privateSourceAdapterCapabilityId"],
        )
        expect_equal(
            "private source adapter bridge matrix binding",
            bridge["boundPrivateSourceAdapterOutcomeMatrixId"],
            matrix["privateSourceAdapterOutcomeMatrixId"],
        )
        expect_equal("private source adapter state", guidance["runtimeStatus"], item["state"]["planStatus"])
        if item["state"]["executionMode"] != "read_only_guidance":
            raise AgentAdapterError("private source adapter guidance should be read-only guidance")
        if capability["supportedSourceKinds"] != summary["supportedSourceKinds"]:
            raise AgentAdapterError("private source adapter guidance should preserve source-kind order")
        if [row["sourceKind"] for row in guidance["sourceKindSummary"]] != summary["supportedSourceKinds"] + [
            "unregistered_source",
            "unsafe_source",
        ]:
            raise AgentAdapterError("private source adapter guidance should summarize supported and rejected source kinds")
        source_summary = {row["sourceKind"]: row for row in guidance["sourceKindSummary"]}
        if source_summary["local_file"]["allowedEntrypoint"] != "source_builder":
            raise AgentAdapterError("private source adapter guidance should route local files to source-builder")
        if source_summary["manual_mapping"]["requiresApproval"] is not True:
            raise AgentAdapterError("private source adapter guidance should preserve manual mapping confirmation")
        for source_kind in ["manual_upload", "private_api", "private_database"]:
            row = source_summary[source_kind]
            if row["implementationStatus"] != "planned_contract_only" or row["allowedEntrypoint"] != "no_current_entrypoint":
                raise AgentAdapterError(f"private source adapter guidance should keep {source_kind} planned-only")
            if row["canExecuteSourceRead"] or row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
                raise AgentAdapterError(f"private source adapter guidance should keep {source_kind} non-generating")
        for source_kind in ["unregistered_source", "unsafe_source"]:
            row = source_summary[source_kind]
            if row["allowedEntrypoint"] != "no_current_entrypoint":
                raise AgentAdapterError(f"private source adapter guidance should stop {source_kind}")
            if row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
                raise AgentAdapterError(f"private source adapter guidance should keep {source_kind} non-generating")
        boundary = guidance["executionBoundary"]
        if boundary["guidanceDoesNotExecute"] is not True or boundary["runsAdapterCalls"] is not False:
            raise AgentAdapterError("private source adapter guidance must stay non-executing")
        for key in [
            "readsPrivateData",
            "createsSourceManifests",
            "createsFieldMappings",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
            "createsHostedRuntime",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"private source adapter guidance boundary should keep {key} false")
        return

    if operation == "private_source_kind_selection":
        examples = payload
        selected = examples.get("selectedExample")
        if selected is not None:
            expect_equal(
                "private source-kind selection query input ref",
                examples["privateSourceKindSelectionExamplesId"],
                request["inputRef"],
            )
            expect_equal(
                "private source-kind selection query selected source",
                selected["sourceKind"],
                examples["requestedSourceKind"],
            )
            expect_equal(
                "private source-kind selection query state source",
                item["state"]["sourceMode"],
                examples["requestedSourceKind"],
            )
            expect_equal(
                "private source-kind selection query state status",
                item["state"]["planStatus"],
                examples["runtimeStatus"],
            )
            if selected["sourceKind"] not in examples["availableSourceKinds"]:
                raise AgentAdapterError("selected private source-kind query should list the selected source kind")
            if selected["recommendation"]["forecastArtifactsAllowed"] or selected["recommendation"]["scoringAllowed"]:
                raise AgentAdapterError("selected private source-kind recommendation must not allow forecast or scoring")
            if selected["recommendation"]["stopBeforeForecast"] is not True:
                raise AgentAdapterError("selected private source-kind recommendation must stop before forecasts")
            if examples["executionBoundary"]["examplesDoNotExecute"] is not True:
                raise AgentAdapterError("selected private source-kind query must stay non-executing")
            if examples["executionBoundary"]["runsCommands"] is not False:
                raise AgentAdapterError("selected private source-kind query must not run commands")
            return

        bindings = examples["bindings"]
        boundary = examples["executionBoundary"]
        expect_equal(
            "private source-kind selection input ref",
            examples["privateSourceKindSelectionExamplesId"],
            request["inputRef"],
        )
        expect_equal("private source-kind selection state", examples["runtimeStatus"], item["state"]["planStatus"])
        expect_equal(
            "private source-kind selection guidance binding",
            bindings["privateSourceAdapterGuidanceId"],
            "privatesourceadapterguidance-001",
        )
        expect_equal(
            "private source-kind selection capability binding",
            bindings["privateSourceAdapterCapabilityId"],
            "privatesourceadaptercapability-001",
        )
        expect_equal(
            "private source-kind selection runbook binding",
            bindings["privateSetupAdapterChainRunbookId"],
            "privatesetupadapterchainrunbook-001",
        )
        if item["state"]["executionMode"] != "read_only_guidance":
            raise AgentAdapterError("private source-kind selection should be read-only guidance")
        source_order = [row["sourceKind"] for row in examples["selectionExamples"]]
        if source_order != [
            "local_file",
            "manual_mapping",
            "manual_upload",
            "auto_evidence_connector",
            "private_api",
            "private_database",
            "unregistered_source",
            "unsafe_source",
        ]:
            raise AgentAdapterError("private source-kind selection should preserve source-kind order")
        rows = {row["sourceKind"]: row for row in examples["selectionExamples"]}
        if rows["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
            raise AgentAdapterError("private source-kind selection should route local files to source-builder")
        if rows["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
            raise AgentAdapterError("private source-kind selection should require manual mapping confirmation")
        if rows["auto_evidence_connector"]["recommendation"]["immediateAction"] != "call_fixture_evidence":
            raise AgentAdapterError("private source-kind selection should route auto evidence to fixture evidence")
        for source_kind in ["manual_upload", "private_api", "private_database"]:
            if rows[source_kind]["recommendation"]["immediateAction"] != "wait_for_runtime":
                raise AgentAdapterError(f"private source-kind selection should keep {source_kind} planned-only")
        if rows["unregistered_source"]["recommendation"]["immediateAction"] != "replace_source":
            raise AgentAdapterError("private source-kind selection should require unregistered source replacement")
        if rows["unsafe_source"]["recommendation"]["immediateAction"] != "reject_source":
            raise AgentAdapterError("private source-kind selection should reject unsafe sources")
        if boundary["examplesDoNotExecute"] is not True or boundary["runsCommands"] is not False:
            raise AgentAdapterError("private source-kind selection must stay non-executing")
        for key in [
            "readsPrivateData",
            "createsSourceManifests",
            "createsFieldMappings",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
            "createsHostedRuntime",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"private source-kind selection boundary should keep {key} false")
        return

    if operation == "private_setup_source_builder":
        result = payload
        build = result["sourceManifestBuild"]
        expect_equal("source builder input ref", build["sourceManifestBuildId"], request["inputRef"])
        expect_equal("source builder request binding", result["privateSetupRequestId"], binding["requestId"])
        expect_equal("source builder state", build["buildStatus"], item["state"]["planStatus"])
        expect_equal("source builder source mode", "local_file", item["state"]["sourceMode"])
        if build["forecastGenerationAllowed"] is not False:
            raise AgentAdapterError("source builder must not allow forecast generation")
        boundary = result["executionBoundary"]
        if boundary["adapterDoesNotExecuteSourceSetup"] is not True:
            raise AgentAdapterError("source builder adapter must not execute setup commands")
        for key in [
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"source builder adapter boundary should keep {key} false")
        if build["buildStatus"] == "rejected":
            if result["sourceManifest"] is not None or result["fieldMapping"] is not None:
                raise AgentAdapterError("rejected source builder payload must not include draft artifacts")
        if result["fieldMapping"] is not None:
            proposed = [
                item for item in result["fieldMapping"]["mappings"] + result["fieldMapping"]["aliasMappings"]
                if item["mappingOrigin"] == "agent_inferred"
            ]
            if not all(item["mappingStatus"] == "proposed" and item["requiresConfirmation"] is True for item in proposed):
                raise AgentAdapterError("agent-inferred mappings must stay proposed and confirmation-gated")
        return

    if operation == "private_setup_source_handoff":
        result = payload
        handoff = result["sourceIntakeHandoff"]
        expect_equal("source handoff input ref", handoff["sourceIntakeHandoffId"], request["inputRef"])
        expect_equal("source handoff request binding", result["privateSetupRequestId"], binding["requestId"])
        expect_equal("source handoff state", handoff["handoffStatus"], item["state"]["planStatus"])
        expect_equal("source handoff source mode", "local_file", item["state"]["sourceMode"])
        bindings = result["bindingSummary"]
        expect_equal("source handoff build binding", handoff["sourceManifestBuildId"], bindings["sourceManifestBuildId"])
        expect_equal("source handoff id binding", handoff["sourceIntakeHandoffId"], bindings["sourceIntakeHandoffId"])
        expect_equal("source handoff intake binding", handoff["sourceIntakeReportId"], bindings["sourceIntakeReportId"])
        expect_equal("source handoff mapping binding", handoff["fieldMappingId"], bindings["fieldMappingId"])
        ready_for_method_gating = handoff["handoffStatus"] == "ready_for_method_gating"
        guidance = result["adapterGuidance"]
        if guidance["canProceedToMethodGating"] is not ready_for_method_gating:
            raise AgentAdapterError("source handoff method-gating guidance should mirror handoff status")
        if ready_for_method_gating and result["sourceHandoffCase"] != "confirmed_builder_draft":
            raise AgentAdapterError("only the confirmed builder handoff may proceed toward method gates")
        if not ready_for_method_gating and guidance["allowedNextEntrypoint"] == "setup_method_gates":
            raise AgentAdapterError("blocked handoffs must not route to setup method gates")
        if guidance["forecastExecutionAllowed"] or guidance["scoringAllowed"]:
            raise AgentAdapterError("source handoff adapter must not allow forecast execution or scoring")
        boundary = result["executionBoundary"]
        for key in [
            "acceptsRawPrivateData",
            "runsSuggestedCommand",
            "createsPublicReadRecords",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
            "bypassesSetupBenchmarkOrMethodGate",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"source handoff adapter boundary should keep {key} false")
        if boundary["adapterDoesNotExecuteSourceHandoff"] is not True:
            raise AgentAdapterError("source handoff adapter must not execute source handoff commands")
        return

    if operation == "private_setup_method_gate":
        result = payload
        method_gate = result["sourceHandoffMethodGate"]
        expect_equal("method gate input ref", method_gate["sourceHandoffMethodGateId"], request["inputRef"])
        expect_equal("method gate request binding", result["privateSetupRequestId"], binding["requestId"])
        expect_equal("method gate state", method_gate["methodGateStatus"], item["state"]["planStatus"])
        expect_equal("method gate source mode", "local_file", item["state"]["sourceMode"])
        bindings = result["bindingSummary"]
        expect_equal("method gate handoff binding", method_gate["sourceIntakeHandoffId"], bindings["sourceIntakeHandoffId"])
        expect_equal("method gate intake binding", method_gate["sourceIntakeReportId"], bindings["sourceIntakeReportId"])
        expect_equal("method gate benchmark binding", method_gate["setupBenchmarkGateId"], bindings["setupBenchmarkGateId"])
        expect_equal("method gate decision binding", method_gate["setupMethodDecisionId"], bindings["setupMethodDecisionId"])
        guidance = result["adapterGuidance"]
        can_recommend = guidance["canRecommendExplicitSetupForecastExecution"]
        allowed_by_gate = guidance["forecastExecutionAllowedByGate"]
        if can_recommend != allowed_by_gate:
            raise AgentAdapterError("method gate forecast recommendation should mirror gate permission")
        if can_recommend and result["methodGateCase"] != "confirmed_builder_draft":
            raise AgentAdapterError("only the confirmed method gate may recommend setup forecast execution")
        if can_recommend and method_gate["nextAction"] != "await_explicit_setup_forecast_execution":
            raise AgentAdapterError("method gate forecast recommendation must require explicit setup forecast execution")
        if not can_recommend and guidance["allowedNextEntrypoint"] == "setup_forecast_execution":
            raise AgentAdapterError("blocked method gates must not route to setup forecast execution")
        if method_gate["forecastArtifactsCreated"] is not False:
            raise AgentAdapterError("method gate summaries must not create forecast artifacts")
        if result["setupMethodDecision"] is not None:
            decision = result["setupMethodDecision"]
            expect_equal("method gate decision payload binding", method_gate["setupMethodDecisionId"], decision["setupMethodDecisionId"])
            expect_equal("method gate decision source-intake binding", method_gate["sourceIntakeReportId"], decision["sourceIntakeReportId"])
        if result["setupBenchmarkGate"] is not None:
            benchmark = result["setupBenchmarkGate"]
            expect_equal("method gate benchmark payload binding", method_gate["setupBenchmarkGateId"], benchmark["setupBenchmarkGateId"])
            expect_equal("method gate benchmark source-intake binding", method_gate["sourceIntakeReportId"], benchmark["sourceIntakeReportId"])
        boundary = result["executionBoundary"]
        for key in [
            "acceptsRawPrivateData",
            "runsSuggestedCommand",
            "createsPublicReadRecords",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "fetchesLiveData",
            "storesCredentials",
            "bypassesSetupBenchmarkOrMethodDecision",
            "executesSetupForecast",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"method gate adapter boundary should keep {key} false")
        if boundary["adapterDoesNotExecuteMethodGate"] is not True:
            raise AgentAdapterError("method gate adapter must not execute setup method gates")
        return

    if operation == "private_setup_forecast_execution":
        result = payload
        run = result["setupForecastRun"]
        expect_equal("forecast execution input ref", run["setupForecastRunId"], request["inputRef"])
        expect_equal("forecast execution request binding", result["privateSetupRequestId"], binding["requestId"])
        expect_equal("forecast execution state", run["runStatus"], item["state"]["planStatus"])
        expect_equal("forecast execution source mode", run["sourceMode"], item["state"]["sourceMode"])
        bindings = result["bindingSummary"]
        expect_equal("forecast execution run binding", run["setupForecastRunId"], bindings["setupForecastRunId"])
        expect_equal("forecast execution handoff binding", run["sourceIntakeHandoffId"], bindings["sourceIntakeHandoffId"])
        expect_equal("forecast execution method-gate binding", run["sourceHandoffMethodGateId"], bindings["sourceHandoffMethodGateId"])
        expect_equal("forecast execution forecast binding", run["recordBinding"]["forecastId"], bindings["forecastId"])
        expect_equal("forecast execution question binding", run["recordBinding"]["questionId"], bindings["questionId"])
        generated = run["runStatus"] == "generated"
        if result["adapterGuidance"]["forecastArtifactsCreated"] is not generated:
            raise AgentAdapterError("forecast execution guidance should mirror run artifact creation")
        if result["executionBoundary"]["createsForecastArtifacts"] is not generated:
            raise AgentAdapterError("forecast execution boundary should mirror run artifact creation")
        if generated:
            if result["forecastExecutionCase"] != "confirmed_builder_draft":
                raise AgentAdapterError("only confirmed handoff forecast execution may generate artifacts")
            if result["sourceHandoffMethodGate"]["nextAction"] != "await_explicit_setup_forecast_execution":
                raise AgentAdapterError("generated forecast execution must follow explicit method-gate recommendation")
            if not all(result["forecastArtifacts"][name] is not None for name in [
                "question",
                "featureSnapshot",
                "evidencePacket",
                "forecastArtifact",
                "forecastHistory",
            ]):
                raise AgentAdapterError("generated forecast execution must return all forecast artifacts")
            artifact = result["forecastArtifacts"]["forecastArtifact"]
            evidence = result["forecastArtifacts"]["evidencePacket"]
            question = result["forecastArtifacts"]["question"]
            history = result["forecastArtifacts"]["forecastHistory"]
            expect_equal("forecast execution artifact forecast binding", artifact["forecastId"], bindings["forecastId"])
            expect_equal("forecast execution evidence forecast binding", evidence["forecastId"], bindings["forecastId"])
            expect_equal("forecast execution question binding", question["questionId"], bindings["questionId"])
            expect_equal("forecast execution history binding", history["historyId"], bindings["historyId"])
            if artifact["forecastOutput"] == artifact["baselineForecast"]:
                raise AgentAdapterError("confirmed forecast execution should expose benchmark-gated model lift candidate")
            if result["adapterGuidance"]["allowedNextEntrypoint"] != "forecast_card":
                raise AgentAdapterError("generated forecast execution should route to forecast-card read")
        else:
            if any(value is not None for value in run["recordBinding"].values()):
                raise AgentAdapterError("blocked forecast execution must not bind forecast artifacts")
            if any(value is not None for value in result["forecastArtifacts"].values()):
                raise AgentAdapterError("blocked forecast execution must not return forecast artifacts")
            if result["adapterGuidance"]["allowedNextEntrypoint"] == "forecast_card":
                raise AgentAdapterError("blocked forecast execution must not route to forecast-card read")
        boundary = result["executionBoundary"]
        for key in [
            "acceptsRawPrivateData",
            "runsSuggestedCommand",
            "createsScoringRecords",
            "resolvesOutcome",
            "fetchesLiveData",
            "storesCredentials",
            "usesPostCloseEvidence",
            "bypassesSourceIntakeBenchmarkOrMethodDecision",
        ]:
            if boundary[key] is not False:
                raise AgentAdapterError(f"forecast execution adapter boundary should keep {key} false")
        if boundary["adapterExecutesSetupForecast"] is not generated:
            raise AgentAdapterError("forecast execution adapter should execute only generated runs")
        return


def validate_envelope_semantics(item: dict[str, Any]) -> None:
    validate_status_semantics(item)
    validate_record_binding(item)
    validate_payload_binding(item)


def binding_from_card(card: dict[str, Any]) -> dict[str, str | None]:
    request_binding = card["requestBinding"]
    links = card["links"]
    return nullable_binding(
        requestId=request_binding["requestId"],
        pipelineRunId=request_binding["pipelineRunId"],
        questionId=card["questionId"],
        forecastId=card["forecastId"],
        evidencePlanId=request_binding["evidencePlanId"],
        evidenceSourceSetId=request_binding["evidenceSourceSetId"],
        sourcePolicyId=request_binding["sourcePolicyId"],
        resolutionRecordId=links["resolutionRecord"],
        scoringReportId=links["scoringReport"],
    )


def binding_from_trace(trace: dict[str, Any], card: dict[str, Any]) -> dict[str, str | None]:
    trace_binding = trace["recordBinding"]
    card_binding = binding_from_card(card)
    return nullable_binding(
        requestId=trace_binding["requestId"],
        pipelineRunId=trace_binding["pipelineRunId"],
        questionId=trace_binding["questionId"],
        forecastId=trace_binding["forecastId"],
        evidencePlanId=trace_binding["evidencePlanId"],
        evidenceSourceSetId=trace_binding["evidenceSourceSetId"],
        sourcePolicyId=trace_binding["sourcePolicyId"],
        resolutionRecordId=card_binding["resolutionRecordId"],
        scoringReportId=card_binding["scoringReportId"],
    )


def state_from_card(card: dict[str, Any]) -> dict[str, str | None]:
    setup_binding = card.get("setupBinding")
    if isinstance(setup_binding, dict) and setup_binding.get("setupForecastRunId"):
        return nullable_state(
            decisionStatus=setup_binding["runStatus"],
            approvalStatus="method_gate_checked",
            dataMode="provided",
            executionMode="fixture_dry_run",
            sourceMode="source_handoff_fixture",
            forecastStatus=card["status"],
            resolutionStatus=card["resolution"]["status"],
            scoreStatus=card["score"]["scoreStatus"] if card["score"] else None,
            qualityClaimStatus=card["qualityClaim"]["status"],
        )
    request_binding = card["requestBinding"]
    return nullable_state(
        decisionStatus="accepted",
        approvalStatus="approved",
        dataMode="auto",
        executionMode=request_binding["executionMode"],
        sourceMode=request_binding["sourceMode"],
        forecastStatus=card["status"],
        resolutionStatus=card["resolution"]["status"],
        scoreStatus=card["score"]["scoreStatus"] if card["score"] else None,
        qualityClaimStatus=card["qualityClaim"]["status"],
    )


def build_request_validation_envelope() -> dict[str, Any]:
    request = load_json(DEFAULT_REQUEST)
    decision = validate_request(request)
    return envelope(
        "agentenvelope-001",
        "forecast_request_validation",
        "validation",
        "forecast_request",
        request["requestId"],
        decision,
        caller_intent="Validate an agent-submitted forecast request without executing it.",
        record_binding=nullable_binding(
            requestId=request["requestId"],
            sourcePolicyId=request["sourcePolicy"]["sourcePolicyId"],
        ),
        state=nullable_state(
            decisionStatus=decision["decisionStatus"],
            approvalStatus=request["approval"]["status"],
            dataMode=request["dataMode"],
        ),
        warnings=[
            "Validation does not execute forecast generation or live evidence fetching.",
        ],
    )


def build_evidence_plan_envelope() -> dict[str, Any]:
    plan = build_plan(DEFAULT_REQUEST)
    return envelope(
        "agentenvelope-002",
        "evidence_plan",
        "dry_run_generation",
        "evidence_gathering_plan",
        plan["evidencePlanId"],
        plan,
        caller_intent="Inspect the dry-run evidence plan before any live source gathering.",
        record_binding=nullable_binding(
            requestId=plan["requestId"],
            evidencePlanId=plan["evidencePlanId"],
            sourcePolicyId=plan["sourcePolicy"]["sourcePolicyId"],
        ),
        state=nullable_state(
            decisionStatus="accepted",
            approvalStatus="approved",
            dataMode=plan["dataMode"],
            planStatus=plan["planStatus"],
            executionMode=plan["executionMode"],
        ),
        warnings=plan["warnings"],
    )


def build_card_and_bundle(
    forecast_id: str = FORECAST_ID,
    question_id: str = QUESTION_ID,
) -> tuple[dict[str, Any], dict[str, Any]]:
    card_response = read_record("forecast-card", forecast_id, question_id)
    bundle_response = read_record("forecast-bundle", forecast_id, question_id)
    return card_response, bundle_response


def build_forecast_card_envelope(
    card_response: dict[str, Any],
    *,
    envelope_id: str = "agentenvelope-003",
    caller_intent: str = "Read a compact claim-safe forecast card before deciding whether to act.",
) -> dict[str, Any]:
    card = card_response["record"]
    return envelope(
        envelope_id,
        "forecast_card",
        "read_only",
        "forecast_card",
        card["forecastId"],
        card_response,
        question_id=card["questionId"],
        forecast_id=card["forecastId"],
        caller_intent=caller_intent,
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=card["warnings"],
    )


def build_evidence_trace_envelope(
    card_response: dict[str, Any],
    trace_response: dict[str, Any],
) -> dict[str, Any]:
    card = card_response["record"]
    trace = trace_response["record"]
    return envelope(
        "agentenvelope-004",
        "evidence_trace",
        "read_only",
        "evidence_trace",
        trace["forecastId"],
        trace_response,
        question_id=trace["questionId"],
        forecast_id=trace["forecastId"],
        caller_intent="Inspect connector-bound evidence provenance without reading raw fixtures.",
        record_binding=binding_from_trace(trace, card),
        state=state_from_card(card),
        warnings=trace["warnings"],
    )


def build_lifecycle_bundle_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
    *,
    envelope_id: str = "agentenvelope-005",
    caller_intent: str = "Inspect the bound lifecycle bundle for provenance and audit context.",
) -> dict[str, Any]:
    card = card_response["record"]
    bundle = bundle_response["record"]
    return envelope(
        envelope_id,
        "lifecycle_bundle",
        "read_only",
        "lifecycle_bundle",
        bundle["forecastId"],
        bundle_response,
        question_id=bundle["questionId"],
        forecast_id=bundle["forecastId"],
        caller_intent=caller_intent,
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "Bundle read is local and read-only; it does not mutate forecast lifecycle records.",
            "Full bundles are larger than forecast cards and may include detailed provenance records.",
        ],
    )


def build_resolution_status_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
    *,
    envelope_id: str = "agentenvelope-006",
    caller_intent: str = "Check whether the forecast is resolved, ambiguous, annulled, or still pending.",
) -> dict[str, Any]:
    card = card_response["record"]
    records = bundle_response["record"]["records"]
    resolution = records["resolutionRecord"]
    outcome_summary = records["outcomeSummary"]
    quality_claim = {
        "publicationStatus": outcome_summary["publicationStatus"],
        "qualityClaimStatus": outcome_summary["qualityClaimStatus"],
        "minimumCalibrationSampleSize": outcome_summary["minimumCalibrationSampleSize"],
    }
    for key in [
        "resolvedComparableAutoEvidenceOutcomes",
        "resolvedComparablePipelineOutcomes",
        "resolvedComparableLiveOutcomes",
        "resolvedComparableSourceHandoffOutcomes",
    ]:
        if key in outcome_summary:
            quality_claim[key] = outcome_summary[key]
    payload = {
        "forecastId": card["forecastId"],
        "questionId": card["questionId"],
        "resolutionRecordId": resolution["resolutionRecordId"],
        "resolutionStatus": resolution["status"],
        "resolvedAt": resolution["resolvedAt"],
        "resolvedOutcome": resolution["resolvedOutcome"],
        "resolutionSource": resolution["resolutionSource"],
        "qualityClaim": quality_claim,
    }
    return envelope(
        envelope_id,
        "resolution_status",
        "resolution_check",
        "resolution_status",
        resolution["resolutionRecordId"],
        payload,
        question_id=card["questionId"],
        forecast_id=card["forecastId"],
        caller_intent=caller_intent,
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "Resolution is fixture-mode and should not be treated as a production live-source workflow.",
        ],
    )


def build_scoring_summary_envelope(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
    *,
    envelope_id: str = "agentenvelope-007",
    caller_intent: str = "Read the score summary and baseline comparison before making a quality claim.",
) -> dict[str, Any]:
    card = card_response["record"]
    records = bundle_response["record"]["records"]
    scoring = records["scoringReport"]
    payload = {
        "forecastId": card["forecastId"],
        "questionId": card["questionId"],
        "scoringReportId": scoring["scoringReportId"],
        "scoreStatus": scoring["scoreStatus"],
        "scoringRule": scoring["scoringRule"],
        "primaryScore": scoring["primaryScore"],
        "baselineScore": scoring["baselineScore"],
        "baselineLift": scoring["baselineLift"],
        "higherIsBetter": scoring["higherIsBetter"],
        "generatedAt": scoring["generatedAt"],
        "qualityClaim": card["qualityClaim"],
    }
    return envelope(
        envelope_id,
        "scoring_summary",
        "scoring_read",
        "scoring_summary",
        scoring["scoringReportId"],
        payload,
        question_id=card["questionId"],
        forecast_id=card["forecastId"],
        caller_intent=caller_intent,
        record_binding=binding_from_card(card),
        state=state_from_card(card),
        warnings=[
            "A single scored fixture outcome is not enough for a live calibration or quality claim.",
        ],
    )


def state_from_private_setup_bundle(bundle: dict[str, Any]) -> dict[str, str | None]:
    request_summary = bundle["requestSummary"]
    action_summary = bundle["actionSummary"]
    source_policy = request_summary["sourcePolicy"]
    return nullable_state(
        decisionStatus=action_summary["routeDecision"],
        approvalStatus=source_policy["approvalStatus"],
        dataMode=source_policy["dataMode"],
        planStatus=bundle["runtimeStatus"],
        sourceMode=bundle["sourceKind"],
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def load_private_setup_adapter_runbook() -> dict[str, Any]:
    runbook = json.loads(PRIVATE_SETUP_ADAPTER_RUNBOOK_PATH.read_text(encoding="utf-8"))
    errors = validate_record(runbook, PRIVATE_SETUP_ADAPTER_RUNBOOK_SCHEMA)
    if errors:
        raise AgentAdapterError(f"private setup adapter-chain runbook validation failed: {errors[0]}")
    return runbook


def state_from_private_setup_adapter_runbook(runbook: dict[str, Any]) -> dict[str, str | None]:
    source_path = runbook["sourcePath"]
    return nullable_state(
        decisionStatus="adapter_chain_guidance",
        approvalStatus=source_path["approvalStatus"],
        dataMode=source_path["dataMode"],
        planStatus=runbook["runtimeStatus"],
        executionMode="read_only_guidance",
        sourceMode=source_path["sourceKind"],
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_adapter_runbook_envelope() -> dict[str, Any]:
    runbook = load_private_setup_adapter_runbook()
    source_path = runbook["sourcePath"]
    return envelope(
        "agentenvelope-042",
        "private_setup_adapter_runbook",
        "read_only",
        "private_setup_adapter_chain_runbook",
        runbook["privateSetupAdapterChainRunbookId"],
        runbook,
        caller_intent="Read the private setup adapter-chain runbook without executing adapter calls.",
        record_binding=nullable_binding(requestId=source_path["privateSetupRequestId"]),
        state=state_from_private_setup_adapter_runbook(runbook),
        warnings=[
            *runbook["warnings"],
            "The adapter envelope is read-only and does not execute the operation sequence.",
        ],
    )


def load_private_setup_adapter_conformance_summary() -> dict[str, Any]:
    summary = json.loads(PRIVATE_SETUP_ADAPTER_CONFORMANCE_SUMMARY_PATH.read_text(encoding="utf-8"))
    errors = validate_record(summary, PRIVATE_SETUP_ADAPTER_CONFORMANCE_SUMMARY_SCHEMA)
    if errors:
        raise AgentAdapterError(f"private setup adapter conformance summary validation failed: {errors[0]}")
    return summary


def state_from_private_setup_adapter_conformance_summary(summary: dict[str, Any]) -> dict[str, str | None]:
    return nullable_state(
        decisionStatus="adapter_conformance_summary",
        approvalStatus="not_required",
        dataMode="generated_fixture",
        planStatus=summary["runtimeStatus"],
        executionMode="read_only_guidance",
        sourceMode="private_setup_adapter_conformance",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_adapter_conformance_summary_envelope() -> dict[str, Any]:
    summary = load_private_setup_adapter_conformance_summary()
    return envelope(
        "agentenvelope-045",
        "private_setup_adapter_conformance_summary",
        "read_only",
        "private_setup_adapter_conformance_summary",
        summary["privateSetupAdapterConformanceSummaryId"],
        summary,
        caller_intent="Read compact private setup adapter conformance guidance without loading full envelopes.",
        record_binding=nullable_binding(
            questionId=summary["bindings"]["generatedQuestionId"],
            forecastId=summary["bindings"]["generatedForecastId"],
        ),
        state=state_from_private_setup_adapter_conformance_summary(summary),
        warnings=[
            *summary["warnings"],
            "The adapter envelope is read-only and does not execute adapter calls or create forecast artifacts.",
        ],
    )


def load_resolution_job_registry() -> dict[str, Any]:
    registry = json.loads(RESOLUTION_JOB_REGISTRY_PATH.read_text(encoding="utf-8"))
    errors = validate_record(registry, RESOLUTION_JOB_REGISTRY_SCHEMA)
    if errors:
        raise AgentAdapterError(f"resolution job registry validation failed: {errors[0]}")
    return registry


def state_from_resolution_job_registry(registry: dict[str, Any]) -> dict[str, str | None]:
    summary = registry["summary"]
    if summary["pendingDueCount"] > 0:
        resolution_status = "pending_due"
    elif summary["pendingNotDueCount"] > 0:
        resolution_status = "pending_not_due"
    elif summary["invalidCount"] > 0:
        resolution_status = "invalid_state"
    else:
        resolution_status = "idle"
    return nullable_state(
        decisionStatus="resolution_jobs_readback",
        approvalStatus="not_required",
        dataMode=registry["registryMode"],
        planStatus="read_only_registry",
        executionMode="read_only",
        sourceMode=registry["sourceBinding"]["sourceKind"],
        forecastStatus="not_created",
        resolutionStatus=resolution_status,
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_resolution_jobs_envelope() -> dict[str, Any]:
    registry = load_resolution_job_registry()
    return envelope(
        "agentenvelope-046",
        "resolution_jobs",
        "read_only",
        "resolution_job_registry",
        registry["resolutionJobRegistryId"],
        registry,
        caller_intent="Read resolution job registry guidance without executing resolvers.",
        record_binding=nullable_binding(),
        state=state_from_resolution_job_registry(registry),
        warnings=[
            *registry["warnings"],
            "The adapter envelope is read-only and cannot execute resolver commands.",
        ],
    )


def load_resolution_scheduler_run() -> dict[str, Any]:
    report = json.loads(RESOLUTION_SCHEDULER_RUN_PATH.read_text(encoding="utf-8"))
    errors = validate_record(report, RESOLUTION_SCHEDULER_RUN_SCHEMA)
    if errors:
        raise AgentAdapterError(f"resolution scheduler run validation failed: {errors[0]}")
    return report


def next_scheduler_action(report: dict[str, Any]) -> dict[str, Any]:
    tick = report["ticks"][-1]
    if tick["tickStatus"] == "failed":
        return {
            "recommendedAction": "inspect_failed_scheduler_tick",
            "reason": "the latest scheduler tick reported resolver failures",
        }
    if tick["tickStatus"] == "due_pending" and report["executionMode"] == "dry_run":
        return {
            "recommendedAction": "run_checked_resolver_when_approved",
            "reason": "at least one job is due, but this readback did not execute resolvers",
        }
    if tick["tickStatus"] == "waiting":
        return {
            "recommendedAction": "wait_until_due",
            "reason": "no jobs are due yet",
        }
    if tick["tickStatus"] == "executed":
        return {
            "recommendedAction": "read_resolved_outputs",
            "reason": "the latest scheduler tick executed at least one resolver",
        }
    return {
        "recommendedAction": "inspect_resolution_jobs",
        "reason": "the scheduler is idle or all jobs are already resolved",
    }


def scheduler_queue_readbacks(tick: dict[str, Any]) -> list[dict[str, Any]]:
    jobs = tick["jobSummary"]
    failed_count = tick["resolverSummary"]["failedCount"]
    return [
        {
            "queueState": "pending_due",
            "count": jobs["pendingDueCount"],
            "presentInLatestTick": jobs["pendingDueCount"] > 0,
            "nextRecommendedAction": "run_checked_resolver_when_approved",
        },
        {
            "queueState": "pending_not_due",
            "count": jobs["pendingNotDueCount"],
            "presentInLatestTick": jobs["pendingNotDueCount"] > 0,
            "nextRecommendedAction": "wait_until_due",
        },
        {
            "queueState": "already_resolved",
            "count": jobs["alreadyResolvedCount"],
            "presentInLatestTick": jobs["alreadyResolvedCount"] > 0,
            "nextRecommendedAction": "read_resolved_outputs",
        },
        {
            "queueState": "invalid_state",
            "count": jobs["invalidCount"],
            "presentInLatestTick": jobs["invalidCount"] > 0,
            "nextRecommendedAction": "inspect_invalid_state",
        },
        {
            "queueState": "failed",
            "count": failed_count,
            "presentInLatestTick": failed_count > 0 or tick["tickStatus"] == "failed",
            "nextRecommendedAction": "inspect_failed_scheduler_tick",
        },
        {
            "queueState": "empty_queue",
            "count": 0 if jobs["jobCount"] else 1,
            "presentInLatestTick": jobs["jobCount"] == 0,
            "nextRecommendedAction": "no_action_needed",
        },
    ]


def resolution_scheduler_status_payload(report: dict[str, Any]) -> dict[str, Any]:
    tick = report["ticks"][-1]
    shutdown = report.get("shutdown")
    return {
        "resolutionSchedulerStatusId": "resolutionschedulerstatus-001",
        "resolutionSchedulerRunId": report["resolutionSchedulerRunId"],
        "generatedAt": report["generatedAt"],
        "runtimeStatus": "scheduler_status_readback",
        "schedulerMode": report["schedulerMode"],
        "executionMode": report["executionMode"],
        "logPath": RESOLUTION_SCHEDULER_LOG_PATH,
        "schedulerRun": report,
        "lastTick": {
            "tickNumber": tick["tickNumber"],
            "startedAt": tick["startedAt"],
            "tickStatus": tick["tickStatus"],
            "jobSummary": tick["jobSummary"],
            "resolverSummary": tick["resolverSummary"],
            "actions": tick["actions"],
            "nextPollSeconds": tick["nextPollSeconds"],
        },
        "lastShutdown": {
            "shutdownReason": shutdown["shutdownReason"] if shutdown else None,
            "lastTickNumber": shutdown["lastTickNumber"] if shutdown else None,
            "logFile": shutdown["logFile"] if shutdown else RESOLUTION_SCHEDULER_LOG_PATH,
        },
        "queueStatusReadbacks": scheduler_queue_readbacks(tick),
        "nextRecommendedAction": next_scheduler_action(report),
        "executionBoundary": {
            "statusReadExecutesScheduler": False,
            "executesResolvers": False,
            "fetchesLiveSources": False,
            "createsForecastArtifacts": False,
            "createsResolutionArtifacts": False,
            "createsScoringRecords": False,
            "hostedSchedulerCreated": False,
            "osSchedulerCreated": False,
            "calibrationClaimAllowed": False,
        },
        "warnings": [
            "This status readback is read-only and does not start a scheduler.",
            "Use resolution_jobs before resolver execution, and use checked resolver commands only when execution is approved.",
        ],
    }


def state_from_resolution_scheduler_status(payload: dict[str, Any]) -> dict[str, str | None]:
    report = payload["schedulerRun"]
    return nullable_state(
        decisionStatus="resolution_scheduler_status_readback",
        approvalStatus="not_required",
        dataMode=report["schedulerMode"],
        planStatus=payload["runtimeStatus"],
        executionMode=report["executionMode"],
        sourceMode="foreground_terminal_scheduler",
        forecastStatus="not_created",
        resolutionStatus=payload["lastTick"]["tickStatus"],
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_resolution_scheduler_status_envelope() -> dict[str, Any]:
    payload = resolution_scheduler_status_payload(load_resolution_scheduler_run())
    return envelope(
        "agentenvelope-047",
        "resolution_scheduler_status",
        "read_only",
        "resolution_scheduler_status",
        payload["resolutionSchedulerStatusId"],
        payload,
        caller_intent="Read the latest checked resolution scheduler status without starting a scheduler.",
        record_binding=nullable_binding(),
        state=state_from_resolution_scheduler_status(payload),
        warnings=[
            *payload["warnings"],
            "The adapter envelope is read-only and cannot execute due jobs.",
        ],
    )


def resolution_readback_error_envelope(
    *,
    envelope_id: str,
    operation: str,
    input_record_type: str,
    input_ref: str,
    caller_intent: str,
    error_code: str,
    message: str,
    retryable: bool,
    state: dict[str, str | None],
) -> dict[str, Any]:
    return envelope(
        envelope_id,
        operation,
        "read_only",
        input_record_type,
        input_ref,
        None,
        caller_intent=caller_intent,
        record_binding=nullable_binding(),
        state=state,
        status="error",
        error={
            "code": error_code,
            "message": message,
            "retryable": retryable,
        },
        warnings=[
            "Error payload is sanitized and does not expose absolute local paths, raw state-file contents, scheduler log contents, or stack traces.",
            "Resolution readback error examples are conformance fixtures only and do not execute resolvers or start schedulers.",
        ],
    )


def build_resolution_jobs_missing_live_workspace_error_envelope() -> dict[str, Any]:
    return resolution_readback_error_envelope(
        envelope_id="agentenvelope-048",
        operation="resolution_jobs",
        input_record_type="resolution_job_registry",
        input_ref="resolutionjobregistry-998",
        caller_intent="Read resolution jobs from a missing live workspace to demonstrate sanitized errors.",
        error_code="not_found",
        message="Live resolution workspace was not found.",
        retryable=True,
        state=nullable_state(
            decisionStatus="resolution_jobs_readback_blocked",
            approvalStatus="not_required",
            dataMode="live_registry",
            planStatus="missing_live_workspace",
            executionMode="read_only",
            sourceMode="forward_run_state",
            forecastStatus="not_created",
            resolutionStatus="not_started",
            scoreStatus="not_created",
            qualityClaimStatus="not_allowed",
        ),
    )


def build_resolution_jobs_unreadable_state_error_envelope() -> dict[str, Any]:
    return resolution_readback_error_envelope(
        envelope_id="agentenvelope-049",
        operation="resolution_jobs",
        input_record_type="resolution_job_registry",
        input_ref="resolutionjobregistry-997",
        caller_intent="Read resolution jobs from an unreadable state file to demonstrate sanitized errors.",
        error_code="access_denied",
        message="Resolution state file could not be read.",
        retryable=True,
        state=nullable_state(
            decisionStatus="resolution_jobs_readback_blocked",
            approvalStatus="not_required",
            dataMode="live_registry",
            planStatus="unreadable_state_file",
            executionMode="read_only",
            sourceMode="forward_run_state",
            forecastStatus="not_created",
            resolutionStatus="invalid_state",
            scoreStatus="not_created",
            qualityClaimStatus="not_allowed",
        ),
    )


def build_resolution_scheduler_malformed_log_error_envelope() -> dict[str, Any]:
    return resolution_readback_error_envelope(
        envelope_id="agentenvelope-050",
        operation="resolution_scheduler_status",
        input_record_type="resolution_scheduler_status",
        input_ref="resolutionschedulerstatus-998",
        caller_intent="Read scheduler status from a malformed scheduler log to demonstrate sanitized errors.",
        error_code="validation_failed",
        message="Resolution scheduler log could not be parsed as checked JSONL.",
        retryable=True,
        state=nullable_state(
            decisionStatus="resolution_scheduler_status_blocked",
            approvalStatus="not_required",
            dataMode="live_watch",
            planStatus="malformed_scheduler_log",
            executionMode="read_only",
            sourceMode="foreground_terminal_scheduler",
            forecastStatus="not_created",
            resolutionStatus="failed",
            scoreStatus="not_created",
            qualityClaimStatus="not_allowed",
        ),
    )


def build_resolution_scheduler_oversized_readback_error_envelope() -> dict[str, Any]:
    return resolution_readback_error_envelope(
        envelope_id="agentenvelope-051",
        operation="resolution_scheduler_status",
        input_record_type="resolution_scheduler_status",
        input_ref="resolutionschedulerstatus-997",
        caller_intent="Read an oversized scheduler status payload to demonstrate sanitized size-limit errors.",
        error_code="response_too_large",
        message="Resolution scheduler status readback exceeds configured size limit.",
        retryable=True,
        state=nullable_state(
            decisionStatus="resolution_scheduler_status_blocked",
            approvalStatus="not_required",
            dataMode="live_watch",
            planStatus="oversized_readback",
            executionMode="read_only",
            sourceMode="foreground_terminal_scheduler",
            forecastStatus="not_created",
            resolutionStatus="not_started",
            scoreStatus="not_created",
            qualityClaimStatus="not_allowed",
        ),
    )


def private_source_adapter_guidance_payload() -> dict[str, Any]:
    capability = build_private_source_adapter_capabilities()
    matrix = build_private_source_adapter_outcome_matrix()
    bridge = build_private_source_adapter_intake_bridge()
    adapters = {item["sourceKind"]: item for item in capability["adapters"]}
    rows = {item["sourceKind"]: item for item in matrix["outcomeRows"]}
    bridge_rows = {item["sourceKind"]: item for item in bridge["bridgeRows"]}
    supported_source_kinds = capability["supportedSourceKinds"]
    summary = []
    for source_kind in supported_source_kinds + ["unregistered_source", "unsafe_source"]:
        row = rows[source_kind]
        bridge_row = bridge_rows[source_kind]
        adapter_item = adapters.get(source_kind)
        summary.append(
            {
                "sourceKind": source_kind,
                "implementationStatus": adapter_item["implementationStatus"] if adapter_item else "not_declared",
                "availabilityStatus": adapter_item["availabilityStatus"] if adapter_item else "not_declared",
                "outcomeClass": row["outcomeClass"],
                "setupOutcomeClass": row["setupOutcomeClass"],
                "requiresApproval": row["requiresApproval"],
                "requiresCredential": row["requiresCredential"],
                "canEnterSetup": row["canEnterSetup"],
                "canExecuteSourceRead": row["canExecuteSourceRead"],
                "allowedEntrypoint": bridge_row["allowedEntrypoint"],
                "currentCommand": bridge_row["currentCommand"],
                "retryCondition": bridge_row["retryCondition"],
                "canCreateForecastArtifacts": row["canCreateForecastArtifacts"],
                "canCreateScoringRecords": row["canCreateScoringRecords"],
                "agentNextAction": row["agentNextAction"],
            }
        )
    return {
        "privateSourceAdapterGuidanceId": "privatesourceadapterguidance-001",
        "generatedAt": GENERATED_AT,
        "scope": "domain_agnostic",
        "runtimeStatus": "guidance_only",
        "bindingSummary": {
            "privateSourceAdapterCapabilityId": capability["privateSourceAdapterCapabilityId"],
            "privateSourceAdapterOutcomeMatrixId": matrix["privateSourceAdapterOutcomeMatrixId"],
            "privateSourceAdapterIntakeBridgeId": bridge["privateSourceAdapterIntakeBridgeId"],
            "privateSetupWorkflowId": capability["boundPrivateSetupWorkflowId"],
            "supportedSourceKinds": supported_source_kinds,
        },
        "sourceKindSummary": summary,
        "capability": capability,
        "outcomeMatrix": matrix,
        "intakeBridge": bridge,
        "executionBoundary": {
            "guidanceDoesNotExecute": True,
            "runsAdapterCalls": False,
            "readsPrivateData": False,
            "createsSourceManifests": False,
            "createsFieldMappings": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "createsHostedRuntime": False,
        },
        "warnings": [
            "Private source adapter guidance is read-only and does not execute source reads.",
            "Private API, private database, and manual upload adapters remain planned-only until a runtime lands.",
            "Use source-builder or source-handoff only through later checked operations after caller approval.",
            "This guidance does not create source manifests, forecasts, resolution records, scoring records, or credentials.",
        ],
    }


def state_from_private_source_adapter_guidance(guidance: dict[str, Any]) -> dict[str, str | None]:
    return nullable_state(
        decisionStatus="private_source_adapter_guidance",
        approvalStatus="mixed_by_source_kind",
        dataMode="provided_or_auto",
        planStatus=guidance["runtimeStatus"],
        executionMode="read_only_guidance",
        sourceMode="private_source_adapter",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_source_adapter_guidance_envelope() -> dict[str, Any]:
    guidance = private_source_adapter_guidance_payload()
    return envelope(
        "agentenvelope-043",
        "private_source_adapter_guidance",
        "read_only",
        "private_source_adapter_capability",
        guidance["bindingSummary"]["privateSourceAdapterCapabilityId"],
        guidance,
        caller_intent="Read private source adapter capability and next-action guidance without executing source reads.",
        record_binding=nullable_binding(),
        state=state_from_private_source_adapter_guidance(guidance),
        warnings=guidance["warnings"],
    )


def load_private_source_kind_selection_examples() -> dict[str, Any]:
    examples = json.loads(PRIVATE_SOURCE_KIND_SELECTION_PATH.read_text(encoding="utf-8"))
    errors = validate_record(examples, PRIVATE_SOURCE_KIND_SELECTION_SCHEMA)
    if errors:
        raise AgentAdapterError(f"private source-kind selection examples validation failed: {errors[0]}")
    return examples


def state_from_private_source_kind_selection(
    examples: dict[str, Any],
    source_kind: str | None = None,
) -> dict[str, str | None]:
    return nullable_state(
        decisionStatus="private_source_kind_selection",
        approvalStatus="mixed_by_source_kind",
        dataMode="provided_or_auto",
        planStatus=examples["runtimeStatus"],
        executionMode="read_only_guidance",
        sourceMode=source_kind or "private_source_kind_selection",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_source_kind_selection_envelope() -> dict[str, Any]:
    examples = load_private_source_kind_selection_examples()
    return envelope(
        "agentenvelope-044",
        "private_source_kind_selection",
        "read_only",
        "private_source_kind_selection_examples",
        examples["privateSourceKindSelectionExamplesId"],
        examples,
        caller_intent="Read private source-kind selection examples without executing the chosen setup path.",
        record_binding=nullable_binding(),
        state=state_from_private_source_kind_selection(examples),
        warnings=[
            *examples["warnings"],
            "The adapter envelope is read-only and does not execute source setup, fixture evidence, forecast execution, or scoring.",
        ],
    )


def build_private_setup_bundle_envelope() -> dict[str, Any]:
    bundle = bundle_by_request_id(PRIVATE_SETUP_REQUEST_ID)
    request_summary = bundle["requestSummary"]
    return envelope(
        "agentenvelope-009",
        "private_setup_bundle",
        "read_only",
        "private_setup_agent_bundle",
        bundle["privateSetupAgentBundleId"],
        bundle,
        caller_intent="Read private setup guidance without executing source setup.",
        record_binding=nullable_binding(requestId=request_summary["privateSetupRequestId"]),
        state=state_from_private_setup_bundle(bundle),
        warnings=[
            *bundle["warnings"],
            "The adapter envelope is read-only and does not execute the suggested setup command.",
        ],
    )


def source_builder_result_payload(
    *,
    private_setup_request_id: str = PRIVATE_SETUP_REQUEST_ID,
    source_builder_case: str = "local_draft",
    source_builder_inputs: list[str] | None = None,
    mapping_hints: list[str] | None = None,
) -> dict[str, Any]:
    if source_builder_inputs and source_builder_case != "local_draft":
        raise SourceBuildError("provide either source builder fixture case or explicit source-builder inputs")
    if source_builder_inputs:
        build, manifest, field_mapping = build_from_inputs(
            999,
            "local-input",
            parse_inputs(source_builder_inputs),
            mapping_hints=parse_mapping_hints(mapping_hints or []),
        )
        input_mode = "caller_approved_files"
    else:
        if source_builder_case not in SOURCE_BUILDER_CASES:
            raise SourceBuildError(f"unknown source builder case: {source_builder_case}")
        build, manifest, field_mapping = build_source_case(source_builder_case)
        input_mode = "checked_fixture_case"

    rejected = build["buildStatus"] == "rejected"
    next_action = "replace_rejected_sources" if rejected else "review_and_confirm_mappings"
    if not build["confirmationRequired"] and not rejected:
        next_action = "proceed_to_source_handoff"
    return {
        "sourceBuilderAdapterResultId": f"sourcebuilderadapterresult-{build['sourceManifestBuildId'].rsplit('-', 1)[-1]}",
        "privateSetupRequestId": private_setup_request_id,
        "inputMode": input_mode,
        "sourceBuilderCase": source_builder_case if not source_builder_inputs else "local_input",
        "sourceManifestBuild": build,
        "sourceManifest": manifest,
        "fieldMapping": field_mapping,
        "adapterGuidance": {
            "nextAction": next_action,
            "allowedNextEntrypoint": "source_handoff" if build["canEnterSourceIntake"] else "no_current_entrypoint",
            "requiresMappingConfirmation": build["confirmationRequired"],
            "mayEnterSourceIntakeAfterConfirmation": build["canEnterSourceIntake"],
            "forecastExecutionAllowed": False,
            "scoringAllowed": False,
        },
        "executionBoundary": {
            "adapterDoesNotExecuteSourceSetup": True,
            "readsOnlyCallerApprovedFiles": True,
            "runsSuggestedCommand": False,
            "createsPublicReadRecords": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
        },
        "warnings": [
            "Source-builder adapter output is draft guidance and does not authorize forecast execution.",
            "Agent-inferred mappings remain proposed until deterministic validation or caller confirmation accepts them.",
            "Rejected source-builder inputs must be replaced before source intake, method gates, forecasts, or scoring.",
        ],
    }


def state_from_source_builder_payload(payload: dict[str, Any]) -> dict[str, str | None]:
    build = payload["sourceManifestBuild"]
    return nullable_state(
        decisionStatus=payload["adapterGuidance"]["nextAction"],
        approvalStatus="caller_approved_inputs",
        dataMode="provided",
        planStatus=build["buildStatus"],
        executionMode="draft_generation",
        sourceMode="local_file",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_source_builder_envelope(case: str, sequence: int) -> dict[str, Any]:
    payload = source_builder_result_payload(source_builder_case=case)
    build = payload["sourceManifestBuild"]
    return envelope(
        f"agentenvelope-{sequence:03d}",
        "private_setup_source_builder",
        "dry_run_generation",
        "source_manifest_build",
        build["sourceManifestBuildId"],
        payload,
        caller_intent="Inspect caller-approved local files and draft source setup guidance.",
        record_binding=nullable_binding(requestId=payload["privateSetupRequestId"]),
        state=state_from_source_builder_payload(payload),
        warnings=payload["warnings"],
    )


def build_private_setup_source_builder_error_envelope() -> dict[str, Any]:
    try:
        source_builder_result_payload(source_builder_inputs=["malformed-input"])
    except SourceBuildError:
        return envelope(
            "agentenvelope-016",
            "private_setup_source_builder",
            "dry_run_generation",
            "source_manifest_build",
            "sourcemanifestbuild-000",
            None,
            caller_intent="Inspect malformed source-builder input to demonstrate sanitized errors.",
            record_binding=nullable_binding(requestId=PRIVATE_SETUP_REQUEST_ID),
            state=nullable_state(),
            status="error",
            error={
                "code": "validation_failed",
                "message": "Source-builder input could not be parsed or validated.",
                "retryable": False,
            },
            warnings=[
                "Error payloads are sanitized and must not expose local absolute paths or raw diagnostics.",
            ],
        )
    raise AgentAdapterError("malformed source-builder input unexpectedly succeeded")


def source_handoff_result_payload(
    *,
    private_setup_request_id: str = PRIVATE_SETUP_REQUEST_ID,
    source_handoff_case: str = "unconfirmed_builder_draft",
) -> dict[str, Any]:
    if source_handoff_case not in SOURCE_HANDOFF_CASES:
        raise SourceIntakeHandoffError(f"unknown source handoff case: {source_handoff_case}")
    handoff, build, manifest, field_mapping, report = build_source_handoff(source_handoff_case)
    ready_for_method_gating = handoff["handoffStatus"] == "ready_for_method_gating"
    if handoff["nextAction"] == "ask_mapping_confirmation":
        allowed_next_entrypoint = "mapping_confirmation"
    elif handoff["nextAction"] == "collect_more_data":
        allowed_next_entrypoint = "source_builder"
    elif handoff["nextAction"] == "replace_rejected_sources":
        allowed_next_entrypoint = "source_builder"
    elif ready_for_method_gating:
        allowed_next_entrypoint = "setup_method_gates"
    else:
        allowed_next_entrypoint = "no_current_entrypoint"
    return {
        "sourceHandoffAdapterResultId": f"sourcehandoffadapterresult-{handoff['sourceIntakeHandoffId'].rsplit('-', 1)[-1]}",
        "privateSetupRequestId": private_setup_request_id,
        "sourceHandoffCase": source_handoff_case,
        "sourceIntakeHandoff": handoff,
        "sourceManifestBuild": build,
        "sourceManifest": manifest,
        "fieldMapping": field_mapping,
        "sourceIntakeReport": report,
        "bindingSummary": {
            "sourceManifestBuildId": handoff["sourceManifestBuildId"],
            "sourceManifestId": handoff["sourceManifestId"],
            "fieldMappingId": handoff["fieldMappingId"],
            "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
            "sourceIntakeReportId": handoff["sourceIntakeReportId"],
        },
        "mappingConfirmation": {
            "required": handoff["mappingSummary"]["requiresConfirmation"],
            "proposedMappingCount": handoff["mappingSummary"]["proposedMappingCount"],
            "confirmedMappingCount": handoff["mappingSummary"]["confirmedMappingCount"],
            "agentInferredMappingCount": handoff["mappingSummary"]["agentInferredMappingCount"],
            "confirmationStatus": "required" if handoff["mappingSummary"]["requiresConfirmation"] else "confirmed_or_not_required",
        },
        "adapterGuidance": {
            "nextAction": handoff["nextAction"],
            "allowedNextEntrypoint": allowed_next_entrypoint,
            "canProceedToMethodGating": ready_for_method_gating,
            "requiresMappingConfirmation": handoff["mappingSummary"]["requiresConfirmation"],
            "requiresMoreData": handoff["nextAction"] == "collect_more_data",
            "requiresSourceReplacement": handoff["nextAction"] == "replace_rejected_sources",
            "forecastExecutionAllowed": False,
            "scoringAllowed": False,
        },
        "executionBoundary": {
            "adapterDoesNotExecuteSourceHandoff": True,
            "acceptsRawPrivateData": False,
            "runsSuggestedCommand": False,
            "createsPublicReadRecords": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "bypassesSetupBenchmarkOrMethodGate": False,
        },
        "warnings": [
            "Source-handoff adapter output is next-action guidance and does not execute source intake or forecasts.",
            "Only confirmed accepted handoffs may proceed toward setup benchmark and method gates.",
            "Setup benchmark and method decisions are still required before any forecast artifacts are created.",
        ],
    }


def state_from_source_handoff_payload(payload: dict[str, Any]) -> dict[str, str | None]:
    handoff = payload["sourceIntakeHandoff"]
    return nullable_state(
        decisionStatus=handoff["nextAction"],
        approvalStatus="caller_confirmation_required" if handoff["mappingSummary"]["requiresConfirmation"] else "caller_confirmed_or_not_required",
        dataMode="provided",
        planStatus=handoff["handoffStatus"],
        executionMode="source_handoff_guidance",
        sourceMode="local_file",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_source_handoff_envelope(case: str, sequence: int) -> dict[str, Any]:
    payload = source_handoff_result_payload(source_handoff_case=case)
    handoff = payload["sourceIntakeHandoff"]
    return envelope(
        f"agentenvelope-{sequence:03d}",
        "private_setup_source_handoff",
        "dry_run_generation",
        "source_intake_handoff",
        handoff["sourceIntakeHandoffId"],
        payload,
        caller_intent="Read checked source-handoff next-action guidance without executing setup gates.",
        record_binding=nullable_binding(requestId=payload["privateSetupRequestId"]),
        state=state_from_source_handoff_payload(payload),
        warnings=payload["warnings"],
    )


def method_gate_allows_explicit_setup_forecast(
    method_gate: dict[str, Any],
    benchmark_gate: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> bool:
    if method_gate["nextAction"] != "await_explicit_setup_forecast_execution":
        return False
    if decision is None or decision["decisionStatus"] not in {"method_selected", "baseline_selected"}:
        return False
    if decision["selectedMethodClass"] == "historical_baseline":
        return True
    return bool(benchmark_gate and benchmark_gate["decision"]["executionAllowed"])


def method_gate_next_entrypoint(method_gate: dict[str, Any], can_recommend_forecast: bool) -> str:
    if can_recommend_forecast:
        return "setup_forecast_execution"
    if method_gate["nextAction"] == "ask_mapping_confirmation":
        return "mapping_confirmation"
    if method_gate["nextAction"] in {"collect_more_data", "replace_rejected_sources"}:
        return "source_builder"
    if method_gate["nextAction"] == "review_method_rejection":
        return "method_review"
    return "no_current_entrypoint"


def method_gate_result_payload(
    *,
    private_setup_request_id: str = PRIVATE_SETUP_REQUEST_ID,
    method_gate_case: str = "unconfirmed_builder_draft",
) -> dict[str, Any]:
    if method_gate_case not in METHOD_GATE_CASES:
        raise SourceHandoffMethodGateError(f"unknown source handoff method gate case: {method_gate_case}")
    method_gate, benchmark_gate, decision = build_source_handoff_method_gate(method_gate_case)
    handoff = build_source_handoff(method_gate_case)[0]
    can_recommend_forecast = method_gate_allows_explicit_setup_forecast(method_gate, benchmark_gate, decision)
    selected_method = method_gate["selectedMethodClass"]
    return {
        "methodGateAdapterResultId": f"methodgateadapterresult-{method_gate['sourceHandoffMethodGateId'].rsplit('-', 1)[-1]}",
        "privateSetupRequestId": private_setup_request_id,
        "methodGateCase": method_gate_case,
        "sourceHandoffMethodGate": method_gate,
        "sourceIntakeHandoff": handoff,
        "setupBenchmarkGate": benchmark_gate,
        "setupMethodDecision": decision,
        "bindingSummary": {
            "sourceIntakeHandoffId": method_gate["sourceIntakeHandoffId"],
            "sourceIntakeReportId": method_gate["sourceIntakeReportId"],
            "setupBenchmarkGateId": method_gate["setupBenchmarkGateId"],
            "setupMethodDecisionId": method_gate["setupMethodDecisionId"],
            "selectedSetupBenchmarkGateId": decision["selectedSetupBenchmarkGateId"] if decision is not None else None,
            "sourceManifestId": decision["sourceManifestId"] if decision is not None else handoff["sourceManifestId"],
            "fieldMappingId": decision["fieldMappingId"] if decision is not None else handoff["fieldMappingId"],
        },
        "methodGateSummary": {
            "methodGateStatus": method_gate["methodGateStatus"],
            "nextAction": method_gate["nextAction"],
            "selectedMethodClass": selected_method,
            "selectedForecastMode": method_gate["selectedForecastMode"],
            "benchmarkGateStatus": method_gate["eligibilitySummary"]["benchmarkGateStatus"],
            "benchmarkExecutionAllowed": method_gate["eligibilitySummary"]["benchmarkExecutionAllowed"],
            "methodDecisionStatus": method_gate["eligibilitySummary"]["methodDecisionStatus"],
            "qualityClaimAllowed": method_gate["eligibilitySummary"]["qualityClaimAllowed"],
        },
        "adapterGuidance": {
            "nextAction": method_gate["nextAction"],
            "allowedNextEntrypoint": method_gate_next_entrypoint(method_gate, can_recommend_forecast),
            "canRecommendExplicitSetupForecastExecution": can_recommend_forecast,
            "forecastExecutionAllowedByGate": can_recommend_forecast,
            "selectedMethodClass": selected_method,
            "selectedForecastMode": method_gate["selectedForecastMode"],
            "requiresMappingConfirmation": method_gate["nextAction"] == "ask_mapping_confirmation",
            "requiresMoreData": method_gate["nextAction"] == "collect_more_data",
            "requiresSourceReplacement": method_gate["nextAction"] == "replace_rejected_sources",
            "requiresMethodReview": method_gate["nextAction"] == "review_method_rejection",
            "adapterCreatesForecastArtifacts": False,
            "scoringAllowed": False,
        },
        "executionBoundary": {
            "adapterDoesNotExecuteMethodGate": True,
            "acceptsRawPrivateData": False,
            "runsSuggestedCommand": False,
            "createsPublicReadRecords": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "bypassesSetupBenchmarkOrMethodDecision": False,
            "executesSetupForecast": False,
        },
        "warnings": [
            "Method-gate adapter output is next-action guidance and does not execute setup forecasts.",
            "Explicit setup forecast execution is a separate step after benchmark and method decisions allow it.",
            "Quality, calibration, production-readiness, and state-of-the-art claims remain blocked unless later evidence allows them.",
        ],
    }


def state_from_method_gate_payload(payload: dict[str, Any]) -> dict[str, str | None]:
    method_gate = payload["sourceHandoffMethodGate"]
    return nullable_state(
        decisionStatus=method_gate["nextAction"],
        approvalStatus="method_gate_checked",
        dataMode="provided",
        planStatus=method_gate["methodGateStatus"],
        executionMode="method_gate_guidance",
        sourceMode="local_file",
        forecastStatus="not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_method_gate_envelope(case: str, sequence: int) -> dict[str, Any]:
    payload = method_gate_result_payload(method_gate_case=case)
    method_gate = payload["sourceHandoffMethodGate"]
    return envelope(
        f"agentenvelope-{sequence:03d}",
        "private_setup_method_gate",
        "dry_run_generation",
        "source_handoff_method_gate",
        method_gate["sourceHandoffMethodGateId"],
        payload,
        caller_intent="Read setup benchmark and method-gate guidance without executing forecasts.",
        record_binding=nullable_binding(requestId=payload["privateSetupRequestId"]),
        state=state_from_method_gate_payload(payload),
        warnings=payload["warnings"],
    )


def forecast_execution_artifacts(case: str, outputs: dict[str, Any], generated: bool) -> dict[str, Any | None]:
    if not generated:
        return {
            "question": None,
            "featureSnapshot": None,
            "evidencePacket": None,
            "forecastArtifact": None,
            "forecastHistory": None,
        }
    prefix = source_handoff_forecast_output_prefix(case)
    return {
        "question": outputs[f"{prefix}-question.generated.json"],
        "featureSnapshot": outputs[f"{prefix}-feature-snapshot.generated.json"],
        "evidencePacket": outputs[f"{prefix}-evidence.generated.json"],
        "forecastArtifact": outputs[f"{prefix}-artifact.generated.json"],
        "forecastHistory": outputs[f"{prefix}-history.generated.json"],
    }


def forecast_execution_next_entrypoint(run: dict[str, Any]) -> str:
    if run["runStatus"] == "generated":
        return "forecast_card"
    reasons = set(run["blockedReasons"])
    if "mapping_confirmation_required" in reasons or "source_intake_needs_confirmation" in reasons:
        return "mapping_confirmation"
    if "more_data_required" in reasons:
        return "source_builder"
    if "builder_rejection" in reasons or "source_intake_rejected" in reasons:
        return "source_builder"
    if "method_decision_rejected" in reasons or "method_decision_needs_confirmation" in reasons:
        return "method_review"
    return "no_current_entrypoint"


def forecast_execution_result_payload(
    *,
    private_setup_request_id: str = PRIVATE_SETUP_REQUEST_ID,
    forecast_execution_case: str = "unconfirmed_builder_draft",
) -> dict[str, Any]:
    if forecast_execution_case not in FORECAST_EXECUTION_CASES:
        raise SourceHandoffForecastError(f"unknown source handoff forecast execution case: {forecast_execution_case}")
    outputs = source_handoff_forecast_outputs()
    prefix = source_handoff_forecast_output_prefix(forecast_execution_case)
    run = outputs[f"{prefix}-setup-forecast-run.generated.json"]
    method_gate_payload = method_gate_result_payload(
        private_setup_request_id=private_setup_request_id,
        method_gate_case=forecast_execution_case,
    )
    generated = run["runStatus"] == "generated"
    method_gate_allows_forecast = method_gate_payload["adapterGuidance"]["forecastExecutionAllowedByGate"]
    if generated and not method_gate_allows_forecast:
        raise SourceHandoffForecastError("generated forecast execution requires method-gate forecast permission")
    if generated and forecast_execution_case != "confirmed_builder_draft":
        raise SourceHandoffForecastError("only confirmed builder draft may generate source-handoff forecast artifacts")

    record_binding = run["recordBinding"]
    artifacts = forecast_execution_artifacts(forecast_execution_case, outputs, generated)
    allowed_next_entrypoint = forecast_execution_next_entrypoint(run)
    return {
        "forecastExecutionAdapterResultId": f"forecastexecutionadapterresult-{run['setupForecastRunId'].rsplit('-', 1)[-1]}",
        "privateSetupRequestId": private_setup_request_id,
        "forecastExecutionCase": forecast_execution_case,
        "setupForecastRun": run,
        "sourceHandoffMethodGate": method_gate_payload["sourceHandoffMethodGate"],
        "sourceIntakeHandoff": method_gate_payload["sourceIntakeHandoff"],
        "setupBenchmarkGate": method_gate_payload["setupBenchmarkGate"],
        "setupMethodDecision": method_gate_payload["setupMethodDecision"],
        "forecastArtifacts": artifacts,
        "bindingSummary": {
            "sourceManifestId": run["sourceManifestId"],
            "fieldMappingId": run["fieldMappingId"],
            "sourceIntakeReportId": run["sourceIntakeReportId"],
            "sourceIntakeHandoffId": run["sourceIntakeHandoffId"],
            "sourceHandoffMethodGateId": run["sourceHandoffMethodGateId"],
            "setupBenchmarkGateId": run["setupBenchmarkGateId"],
            "setupMethodDecisionId": run["setupMethodDecisionId"],
            "setupForecastRunId": run["setupForecastRunId"],
            "questionId": record_binding["questionId"],
            "forecastId": record_binding["forecastId"],
            "evidencePacketId": record_binding["evidencePacketId"],
            "historyId": record_binding["historyId"],
            "forecastCardId": record_binding["forecastCardId"],
            "forecastBundleId": record_binding["forecastBundleId"],
        },
        "forecastExecutionSummary": {
            "runStatus": run["runStatus"],
            "executionMode": run["executionMode"],
            "sourceMode": run["sourceMode"],
            "selectedMethodClass": run["selectedMethodClass"],
            "selectedForecastMode": run["selectedForecastMode"],
            "forecastArtifactsCreated": generated,
            "generatedForecastId": record_binding["forecastId"],
            "blockedReasons": run["blockedReasons"],
        },
        "adapterGuidance": {
            "nextAction": "read_forecast_card" if generated else "resolve_forecast_execution_blockers",
            "allowedNextEntrypoint": allowed_next_entrypoint,
            "forecastArtifactsCreated": generated,
            "canReadForecastCard": generated,
            "canProceedToResolutionWhenOutcomeAvailable": generated,
            "requiresMappingConfirmation": allowed_next_entrypoint == "mapping_confirmation",
            "requiresMoreData": "more_data_required" in run["blockedReasons"],
            "requiresSourceReplacement": any(
                reason in run["blockedReasons"]
                for reason in ["builder_rejection", "source_intake_rejected"]
            ),
            "requiresMethodReview": allowed_next_entrypoint == "method_review",
            "scoringAllowed": False,
        },
        "executionBoundary": {
            "adapterExecutesSetupForecast": generated,
            "acceptsRawPrivateData": False,
            "runsSuggestedCommand": False,
            "createsPublicReadRecords": generated,
            "createsForecastArtifacts": generated,
            "createsScoringRecords": False,
            "resolvesOutcome": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "usesPostCloseEvidence": False,
            "bypassesSourceIntakeBenchmarkOrMethodDecision": False,
        },
        "warnings": [
            "Forecast execution adapter is fixture-mode and preserves source-handoff, benchmark, and method-decision gates.",
            "Only the confirmed source-handoff method-gate case may return forecast artifacts.",
            "Forecast execution does not resolve outcomes, score forecasts, calibrate, fetch live data, or store credentials.",
        ],
    }


def state_from_forecast_execution_payload(payload: dict[str, Any]) -> dict[str, str | None]:
    run = payload["setupForecastRun"]
    return nullable_state(
        decisionStatus=payload["adapterGuidance"]["nextAction"],
        approvalStatus="method_gate_checked",
        dataMode="provided",
        planStatus=run["runStatus"],
        executionMode=run["executionMode"],
        sourceMode=run["sourceMode"],
        forecastStatus="open" if run["runStatus"] == "generated" else "not_created",
        resolutionStatus="not_started",
        scoreStatus="not_created",
        qualityClaimStatus="not_allowed",
    )


def build_private_setup_forecast_execution_envelope(case: str, sequence: int) -> dict[str, Any]:
    payload = forecast_execution_result_payload(forecast_execution_case=case)
    run = payload["setupForecastRun"]
    return envelope(
        f"agentenvelope-{sequence:03d}",
        "private_setup_forecast_execution",
        "forecast_execution",
        "setup_forecast_run",
        run["setupForecastRunId"],
        payload,
        caller_intent="Run checked setup forecast execution after source intake, benchmark, and method gates allow it.",
        record_binding=nullable_binding(
            requestId=payload["privateSetupRequestId"],
            questionId=run["recordBinding"]["questionId"],
            forecastId=run["recordBinding"]["forecastId"],
        ),
        state=state_from_forecast_execution_payload(payload),
        warnings=payload["warnings"],
    )


def build_private_setup_forecast_readback_envelopes(
    card_response: dict[str, Any],
    bundle_response: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        OUTPUT_FILES["private_setup_forecast_card_readback"]: build_forecast_card_envelope(
            card_response,
            envelope_id="agentenvelope-038",
            caller_intent="Read the generated private setup forecast card after checked forecast execution.",
        ),
        OUTPUT_FILES["private_setup_lifecycle_bundle_readback"]: build_lifecycle_bundle_envelope(
            card_response,
            bundle_response,
            envelope_id="agentenvelope-039",
            caller_intent="Inspect the generated private setup forecast lifecycle bundle and setup bindings.",
        ),
        OUTPUT_FILES["private_setup_resolution_status_readback"]: build_resolution_status_envelope(
            card_response,
            bundle_response,
            envelope_id="agentenvelope-040",
            caller_intent="Read the generated private setup forecast resolution status after outcome resolution.",
        ),
        OUTPUT_FILES["private_setup_scoring_summary_readback"]: build_scoring_summary_envelope(
            card_response,
            bundle_response,
            envelope_id="agentenvelope-041",
            caller_intent="Read the generated private setup forecast score while preserving sample-size limits.",
        ),
    }


def build_error_envelope() -> dict[str, Any]:
    try:
        read_record("forecast-card", MISSING_FORECAST_ID, QUESTION_ID)
    except PublicError as exc:
        return envelope(
            "agentenvelope-008",
            "forecast_card",
            "read_only",
            "forecast_card",
            MISSING_FORECAST_ID,
            None,
            question_id=QUESTION_ID,
            forecast_id=MISSING_FORECAST_ID,
            caller_intent="Read a forecast card that does not exist to demonstrate sanitized errors.",
            record_binding=nullable_binding(questionId=QUESTION_ID, forecastId=MISSING_FORECAST_ID),
            state=nullable_state(),
            status="error",
            error={
                "code": exc.code,
                "message": exc.message,
                "retryable": False,
            },
            warnings=[
                "Error payloads are sanitized and must not expose local absolute paths or raw diagnostics.",
            ],
        )
    raise AgentAdapterError("missing-record read unexpectedly succeeded")


def build_private_setup_bundle_error_envelope() -> dict[str, Any]:
    try:
        bundle_by_request_id(MISSING_PRIVATE_SETUP_REQUEST_ID)
    except PrivateSetupAgentBundleError:
        return envelope(
            "agentenvelope-010",
            "private_setup_bundle",
            "read_only",
            "private_setup_agent_bundle",
            MISSING_PRIVATE_SETUP_REQUEST_ID,
            None,
            caller_intent="Read a private setup bundle that does not exist to demonstrate sanitized errors.",
            record_binding=nullable_binding(requestId=MISSING_PRIVATE_SETUP_REQUEST_ID),
            state=nullable_state(),
            status="error",
            error={
                "code": "not_found",
                "message": "Private setup agent bundle was not found.",
                "retryable": False,
            },
            warnings=[
                "Error payloads are sanitized and must not expose local absolute paths or raw diagnostics.",
            ],
        )
    raise AgentAdapterError("missing private setup bundle read unexpectedly succeeded")


def build_envelopes() -> dict[str, dict[str, Any]]:
    card_response, bundle_response = build_card_and_bundle()
    setup_card_response, setup_bundle_response = build_card_and_bundle(
        SOURCE_HANDOFF_FORECAST_ID,
        SOURCE_HANDOFF_QUESTION_ID,
    )
    trace_response = read_record("evidence-trace", FORECAST_ID, QUESTION_ID)
    envelopes = {
        OUTPUT_FILES["forecast_request_validation"]: build_request_validation_envelope(),
        OUTPUT_FILES["evidence_plan"]: build_evidence_plan_envelope(),
        OUTPUT_FILES["forecast_card"]: build_forecast_card_envelope(card_response),
        OUTPUT_FILES["evidence_trace"]: build_evidence_trace_envelope(card_response, trace_response),
        OUTPUT_FILES["lifecycle_bundle"]: build_lifecycle_bundle_envelope(card_response, bundle_response),
        OUTPUT_FILES["resolution_status"]: build_resolution_status_envelope(card_response, bundle_response),
        OUTPUT_FILES["scoring_summary"]: build_scoring_summary_envelope(card_response, bundle_response),
        OUTPUT_FILES["resolution_jobs"]: build_resolution_jobs_envelope(),
        OUTPUT_FILES["resolution_scheduler_status"]: build_resolution_scheduler_status_envelope(),
        OUTPUT_FILES["private_setup_bundle"]: build_private_setup_bundle_envelope(),
        OUTPUT_FILES["private_setup_adapter_runbook"]: build_private_setup_adapter_runbook_envelope(),
        OUTPUT_FILES["private_setup_adapter_conformance_summary"]: build_private_setup_adapter_conformance_summary_envelope(),
        OUTPUT_FILES["private_source_adapter_guidance"]: build_private_source_adapter_guidance_envelope(),
        OUTPUT_FILES["private_source_kind_selection"]: build_private_source_kind_selection_envelope(),
        OUTPUT_FILES["private_setup_source_builder"]: build_private_setup_source_builder_envelope("local_draft", 11),
        OUTPUT_FILES["private_setup_source_builder_contains_secret"]: build_private_setup_source_builder_envelope(
            "contains_secret",
            12,
        ),
        OUTPUT_FILES["private_setup_source_builder_unsupported_format"]: build_private_setup_source_builder_envelope(
            "unsupported_format",
            13,
        ),
        OUTPUT_FILES["private_setup_source_builder_oversized"]: build_private_setup_source_builder_envelope(
            "oversized",
            14,
        ),
        OUTPUT_FILES["private_setup_source_builder_leakage"]: build_private_setup_source_builder_envelope(
            "leakage",
            15,
        ),
        OUTPUT_FILES["private_setup_source_handoff_unconfirmed_builder_draft"]: build_private_setup_source_handoff_envelope(
            "unconfirmed_builder_draft",
            17,
        ),
        OUTPUT_FILES["private_setup_source_handoff_confirmed_builder_draft"]: build_private_setup_source_handoff_envelope(
            "confirmed_builder_draft",
            18,
        ),
        OUTPUT_FILES["private_setup_source_handoff_insufficient_confirmed_builder_draft"]: build_private_setup_source_handoff_envelope(
            "insufficient_confirmed_builder_draft",
            19,
        ),
        OUTPUT_FILES["private_setup_source_handoff_contains_secret"]: build_private_setup_source_handoff_envelope(
            "contains_secret",
            20,
        ),
        OUTPUT_FILES["private_setup_source_handoff_unsupported_format"]: build_private_setup_source_handoff_envelope(
            "unsupported_format",
            21,
        ),
        OUTPUT_FILES["private_setup_source_handoff_oversized"]: build_private_setup_source_handoff_envelope(
            "oversized",
            22,
        ),
        OUTPUT_FILES["private_setup_source_handoff_leakage"]: build_private_setup_source_handoff_envelope(
            "leakage",
            23,
        ),
        OUTPUT_FILES["private_setup_method_gate_unconfirmed_builder_draft"]: build_private_setup_method_gate_envelope(
            "unconfirmed_builder_draft",
            24,
        ),
        OUTPUT_FILES["private_setup_method_gate_confirmed_builder_draft"]: build_private_setup_method_gate_envelope(
            "confirmed_builder_draft",
            25,
        ),
        OUTPUT_FILES["private_setup_method_gate_insufficient_confirmed_builder_draft"]: build_private_setup_method_gate_envelope(
            "insufficient_confirmed_builder_draft",
            26,
        ),
        OUTPUT_FILES["private_setup_method_gate_contains_secret"]: build_private_setup_method_gate_envelope(
            "contains_secret",
            27,
        ),
        OUTPUT_FILES["private_setup_method_gate_unsupported_format"]: build_private_setup_method_gate_envelope(
            "unsupported_format",
            28,
        ),
        OUTPUT_FILES["private_setup_method_gate_oversized"]: build_private_setup_method_gate_envelope(
            "oversized",
            29,
        ),
        OUTPUT_FILES["private_setup_method_gate_leakage"]: build_private_setup_method_gate_envelope(
            "leakage",
            30,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_unconfirmed_builder_draft"]: build_private_setup_forecast_execution_envelope(
            "unconfirmed_builder_draft",
            31,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_confirmed_builder_draft"]: build_private_setup_forecast_execution_envelope(
            "confirmed_builder_draft",
            32,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_insufficient_confirmed_builder_draft"]: build_private_setup_forecast_execution_envelope(
            "insufficient_confirmed_builder_draft",
            33,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_contains_secret"]: build_private_setup_forecast_execution_envelope(
            "contains_secret",
            34,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_unsupported_format"]: build_private_setup_forecast_execution_envelope(
            "unsupported_format",
            35,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_oversized"]: build_private_setup_forecast_execution_envelope(
            "oversized",
            36,
        ),
        OUTPUT_FILES["private_setup_forecast_execution_leakage"]: build_private_setup_forecast_execution_envelope(
            "leakage",
            37,
        ),
        **build_private_setup_forecast_readback_envelopes(setup_card_response, setup_bundle_response),
        OUTPUT_FILES["forecast_card_error"]: build_error_envelope(),
        OUTPUT_FILES["private_setup_bundle_error"]: build_private_setup_bundle_error_envelope(),
        OUTPUT_FILES["private_setup_source_builder_error"]: build_private_setup_source_builder_error_envelope(),
        OUTPUT_FILES["resolution_jobs_missing_live_workspace_error"]: build_resolution_jobs_missing_live_workspace_error_envelope(),
        OUTPUT_FILES["resolution_jobs_unreadable_state_error"]: build_resolution_jobs_unreadable_state_error_envelope(),
        OUTPUT_FILES["resolution_scheduler_malformed_log_error"]: build_resolution_scheduler_malformed_log_error_envelope(),
        OUTPUT_FILES["resolution_scheduler_oversized_readback_error"]: build_resolution_scheduler_oversized_readback_error_envelope(),
    }
    for filename, item in envelopes.items():
        errors = validate_record(item, SCHEMA)
        if errors:
            raise AgentAdapterError(f"{filename} schema validation failed: {errors[0]}")
        try:
            validate_envelope_semantics(item)
        except AgentAdapterError as exc:
            raise AgentAdapterError(f"{filename} semantic validation failed: {exc}") from exc
    return envelopes


def write_envelopes(envelopes: dict[str, dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for filename, item in envelopes.items():
        (GENERATED / filename).write_text(render_json(item), encoding="utf-8")
    print(f"generated {len(envelopes)} agent adapter envelopes")


def check_envelopes(envelopes: dict[str, dict[str, Any]]) -> None:
    for filename, item in envelopes.items():
        path = GENERATED / filename
        if not path.exists():
            print(f"missing agent adapter envelope: {path}", file=sys.stderr)
            print("run `python3 scripts/build_agent_adapter_fixtures.py --write`", file=sys.stderr)
            raise SystemExit(1)
        expected = render_json(item)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"agent adapter envelope drift: {path}", file=sys.stderr)
            print("run `python3 scripts/build_agent_adapter_fixtures.py --write`", file=sys.stderr)
            raise SystemExit(1)
    print(f"checked {len(envelopes)} agent adapter envelopes")


def envelope_collection(envelopes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "agentEnvelopeSetId": "agentenvelopeset-001",
        "generatedAt": GENERATED_AT,
        "count": len(envelopes),
        "envelopes": list(envelopes.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated agent-envelope drift")
    parser.add_argument("--write", action="store_true", help="write generated agent-envelope fixtures")
    args = parser.parse_args()
    try:
        envelopes = build_envelopes()
    except (AgentAdapterError, PublicError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_envelopes(envelopes)
    elif args.check:
        check_envelopes(envelopes)
    else:
        sys.stdout.write(render_json(envelope_collection(envelopes)))


if __name__ == "__main__":
    main()
