#!/usr/bin/env python3
"""Check agent adapter envelope invariants."""

from __future__ import annotations

from copy import deepcopy
import json

from build_agent_adapter_fixtures import (
    OUTPUT_FILES,
    AgentAdapterError,
    FORECAST_EXECUTION_ENVELOPE_CASES,
    build_envelopes,
    render_json,
    source_handoff_forecast_outputs_cache_info,
    validate_envelope_semantics,
)
from ope_schema import SPEC, validate_record


REQUIRED_SUCCESS_OPERATIONS = {
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
    "setup_engine",
    "campaign_plan",
    "campaign_status",
    "campaign_health",
    "campaign_append_readiness",
    "campaign_calibration_status",
    "resolution_jobs",
    "resolution_scheduler_status",
    "resolution_status",
    "scoring_summary",
}


def text_contains_local_absolute_path(value: object) -> bool:
    return "/Users/" in json.dumps(value, sort_keys=True)


def assert_schema_rejects(data: dict[str, object], label: str) -> None:
    if not validate_record(data, SPEC / "agent-envelope.schema.json"):
        raise AssertionError(f"agent-envelope schema should reject {label}")


def assert_semantics_reject(data: dict[str, object], label: str) -> None:
    try:
        validate_envelope_semantics(data)
    except AgentAdapterError:
        return
    raise AssertionError(f"agent envelope semantic checks should reject {label}")


def main() -> None:
    envelopes = build_envelopes()
    if set(envelopes) != set(OUTPUT_FILES.values()):
        raise AssertionError("agent adapter should emit the expected fixed envelope filenames")
    if len(envelopes) != 57:
        raise AssertionError("agent adapter should emit fifty success envelopes and seven error envelopes")
    cache_info = source_handoff_forecast_outputs_cache_info()
    if cache_info.misses != 1 or cache_info.hits < len(FORECAST_EXECUTION_ENVELOPE_CASES) - 1:
        raise AssertionError("agent adapter should reuse source-handoff forecast outputs across execution cases")

    success = [item for item in envelopes.values() if item["status"] == "ok"]
    error = [item for item in envelopes.values() if item["status"] == "error"]
    if {item["operation"] for item in success} != REQUIRED_SUCCESS_OPERATIONS:
        raise AssertionError("agent adapter success envelopes should cover every required operation")
    if len(success) != 50:
        raise AssertionError("agent adapter should include exactly fifty success examples")
    if len(error) != 7:
        raise AssertionError("agent adapter should include exactly seven sanitized error examples")
    if any(item["exitCode"] != 0 for item in success):
        raise AssertionError("successful agent envelopes should use exit code 0")
    if any(text_contains_local_absolute_path(item) for item in error):
        raise AssertionError("sanitized error envelopes should not expose absolute local paths")

    def find_error_envelope(operation: str, input_ref: str | None = None) -> dict[str, object]:
        for item in error:
            if item["operation"] != operation:
                continue
            if input_ref is not None and item["adapterRequest"]["inputRef"] != input_ref:
                continue
            return item
        raise AssertionError(f"missing error envelope for {operation} {input_ref or ''}".strip())

    error_envelope = find_error_envelope("forecast_card")
    if error_envelope["operation"] != "forecast_card":
        raise AssertionError("sanitized error example should use the forecast-card operation")
    if error_envelope["exitCode"] != 4:
        raise AssertionError("missing record errors should map to exit code 4")
    if error_envelope["error"]["code"] != "not_found":
        raise AssertionError("missing record error should use the not_found code")
    if error_envelope["payload"] is not None:
        raise AssertionError("error envelopes should not carry a success payload")

    private_error = find_error_envelope("private_setup_bundle")
    if private_error["exitCode"] != 4:
        raise AssertionError("missing private setup bundle errors should map to exit code 4")
    if private_error["error"]["code"] != "not_found":
        raise AssertionError("missing private setup bundle error should use the not_found code")
    if private_error["recordBinding"]["requestId"] != "privatesetuprequest-999":
        raise AssertionError("missing private setup bundle error should preserve requested setup request id")
    if private_error["payload"] is not None:
        raise AssertionError("private setup bundle error envelope should not carry a success payload")

    source_builder_error = find_error_envelope("private_setup_source_builder")
    if source_builder_error["exitCode"] != 2:
        raise AssertionError("malformed source-builder errors should map to exit code 2")
    if source_builder_error["error"]["code"] != "validation_failed":
        raise AssertionError("malformed source-builder error should use the validation_failed code")
    if source_builder_error["payload"] is not None:
        raise AssertionError("source-builder error envelope should not carry a success payload")
    missing_workspace_error = find_error_envelope("resolution_jobs", "resolutionjobregistry-998")
    if missing_workspace_error["exitCode"] != 4 or missing_workspace_error["error"]["code"] != "not_found":
        raise AssertionError("missing live workspace errors should map to sanitized not_found")
    if missing_workspace_error["state"]["planStatus"] != "missing_live_workspace":
        raise AssertionError("missing live workspace error should expose safe plan status")
    if missing_workspace_error["payload"] is not None:
        raise AssertionError("missing live workspace error envelope should not carry a payload")

    unreadable_state_error = find_error_envelope("resolution_jobs", "resolutionjobregistry-997")
    if unreadable_state_error["exitCode"] != 4 or unreadable_state_error["error"]["code"] != "access_denied":
        raise AssertionError("unreadable state errors should map to sanitized access_denied")
    if unreadable_state_error["state"]["planStatus"] != "unreadable_state_file":
        raise AssertionError("unreadable state error should expose safe plan status")
    if unreadable_state_error["payload"] is not None:
        raise AssertionError("unreadable state error envelope should not carry a payload")

    malformed_log_error = find_error_envelope("resolution_scheduler_status", "resolutionschedulerstatus-998")
    if malformed_log_error["exitCode"] != 2 or malformed_log_error["error"]["code"] != "validation_failed":
        raise AssertionError("malformed scheduler logs should map to sanitized validation_failed")
    if malformed_log_error["state"]["planStatus"] != "malformed_scheduler_log":
        raise AssertionError("malformed scheduler log error should expose safe plan status")
    if malformed_log_error["payload"] is not None:
        raise AssertionError("malformed scheduler log error envelope should not carry a payload")

    oversized_readback_error = find_error_envelope("resolution_scheduler_status", "resolutionschedulerstatus-997")
    if oversized_readback_error["exitCode"] != 5 or oversized_readback_error["error"]["code"] != "response_too_large":
        raise AssertionError("oversized scheduler readbacks should map to sanitized response_too_large")
    if oversized_readback_error["state"]["planStatus"] != "oversized_readback":
        raise AssertionError("oversized scheduler readback error should expose safe plan status")
    if oversized_readback_error["payload"] is not None:
        raise AssertionError("oversized scheduler readback error envelope should not carry a payload")

    def success_envelope(operation: str, forecast_id: str | None = None) -> dict[str, object]:
        for item in success:
            if item["operation"] != operation:
                continue
            if forecast_id is not None and item["recordBinding"]["forecastId"] != forecast_id:
                continue
            return item
        raise AssertionError(f"missing success envelope for {operation} {forecast_id or ''}".strip())

    request = success_envelope("forecast_request_validation")
    if request["payload"]["decisionStatus"] != "accepted":
        raise AssertionError("request validation envelope should show accepted status")
    if request["state"]["dataMode"] != "auto":
        raise AssertionError("request validation envelope should preserve auto data mode")

    plan = success_envelope("evidence_plan")
    if plan["payload"]["planStatus"] != "planned":
        raise AssertionError("evidence-plan envelope should expose planned status")
    if plan["state"]["executionMode"] != "dry_run":
        raise AssertionError("evidence-plan envelope should expose dry-run execution mode")

    card = success_envelope("forecast_card", "forecast-602")
    card_record = card["payload"]["record"]
    if card_record["forecastId"] != "forecast-602":
        raise AssertionError("forecast-card envelope should bind forecast-602")
    if card_record["requestBinding"]["sourceMode"] != "auto_evidence_fixture_replay":
        raise AssertionError("forecast-card envelope should expose auto-evidence fixture replay mode")
    if card_record["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("forecast-card envelope should preserve quality claim boundary")

    trace = success_envelope("evidence_trace", "forecast-602")
    trace_record = trace["payload"]["record"]
    if trace_record["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence-trace envelope should preserve connector result-set binding")
    if trace_record["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("evidence-trace envelope must not claim all evidence coverage")
    if trace_record["controls"]["rawStackTracesExposed"] is not False:
        raise AssertionError("evidence-trace envelope should keep raw diagnostics hidden")

    bundle = success_envelope("lifecycle_bundle", "forecast-602")
    if bundle["payload"]["record"]["includedRecords"]["scoringReport"] != "scoring-601":
        raise AssertionError("lifecycle-bundle envelope should include the scoring report")

    resolution = success_envelope("resolution_status", "forecast-602")
    if resolution["payload"]["resolutionStatus"] != "resolved":
        raise AssertionError("resolution-status envelope should expose resolved status")
    if resolution["recordBinding"]["resolutionRecordId"] != "resolution-601":
        raise AssertionError("resolution-status envelope should preserve resolution binding")

    scoring = success_envelope("scoring_summary", "forecast-602")
    if scoring["payload"]["scoreStatus"] != "scored":
        raise AssertionError("scoring-summary envelope should expose scored status")
    if scoring["payload"]["baselineLift"] <= 0:
        raise AssertionError("scoring-summary envelope should preserve positive baseline lift")
    if scoring["recordBinding"]["scoringReportId"] != "scoring-601":
        raise AssertionError("scoring-summary envelope should preserve scoring binding")

    setup_engine = success_envelope("setup_engine")
    setup_payload = setup_engine["payload"]
    if setup_payload["setupEngineId"] != "setupengine-001":
        raise AssertionError("setup-engine envelope should return the checked setup-engine record")
    if setup_payload["candidateForecastContracts"][0]["contractStatus"] != "forecastable":
        raise AssertionError("setup-engine envelope should expose a forecastable first candidate")
    if setup_payload["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("setup-engine envelope should render before forecast artifacts")
    if setup_payload["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("setup-engine envelope must keep quality claims blocked")
    if setup_engine["state"]["forecastStatus"] != "not_created_by_setup_engine":
        raise AssertionError("setup-engine envelope must not create forecasts")

    resolution_jobs = success_envelope("resolution_jobs")
    resolution_jobs_payload = resolution_jobs["payload"]
    if resolution_jobs_payload["summary"]["pendingDueCount"] != 1:
        raise AssertionError("resolution-jobs envelope should expose one due fixture job")
    if resolution_jobs_payload["executionBoundary"]["registryExecutesResolvers"] is not False:
        raise AssertionError("resolution-jobs envelope must not execute resolvers")
    due_jobs = [job for job in resolution_jobs_payload["jobs"] if job["jobStatus"] == "pending_due"]
    if due_jobs[0]["agentAction"]["recommendedAction"] != "call_resolver_execute":
        raise AssertionError("resolution-jobs envelope should route due jobs to resolver execution")
    if resolution_jobs["state"]["resolutionStatus"] != "pending_due":
        raise AssertionError("resolution-jobs envelope state should show due work")

    scheduler_status = success_envelope("resolution_scheduler_status")
    scheduler_status_payload = scheduler_status["payload"]
    if scheduler_status_payload["executionMode"] != "dry_run":
        raise AssertionError("resolution-scheduler-status envelope should expose dry-run mode")
    if scheduler_status_payload["lastTick"]["tickStatus"] != "due_pending":
        raise AssertionError("resolution-scheduler-status envelope should expose the latest due-pending tick")
    if scheduler_status_payload["logPath"] != ".ope/live/resolution-scheduler/scheduler-runs.jsonl":
        raise AssertionError("resolution-scheduler-status envelope should expose the scheduler log path")
    queue_states = {row["queueState"]: row for row in scheduler_status_payload["queueStatusReadbacks"]}
    if set(queue_states) != {"pending_due", "pending_not_due", "already_resolved", "invalid_state", "failed", "empty_queue"}:
        raise AssertionError("resolution-scheduler-status envelope should expose every compact queue state")
    if queue_states["pending_due"]["presentInLatestTick"] is not True:
        raise AssertionError("resolution-scheduler-status envelope should mark due work present")
    if scheduler_status_payload["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("resolution-scheduler-status envelope must not execute resolvers")

    campaign_plan = success_envelope("campaign_plan")
    if campaign_plan["payload"]["predictionCampaignManifestId"] != "predictioncampaignmanifest-001":
        raise AssertionError("campaign-plan envelope should return the checked manifest")
    if campaign_plan["payload"]["plannedRuns"][0]["forecastId"] != "forecast-1301":
        raise AssertionError("campaign-plan envelope should expose the next campaign forecast")
    if campaign_plan["payload"]["localStatePolicy"]["normalChecksWriteLiveState"] is not False:
        raise AssertionError("campaign-plan envelope must keep normal checks non-mutating")

    campaign_status = success_envelope("campaign_status")
    if campaign_status["payload"]["predictionCampaignExplainId"] != "predictioncampaignexplain-001":
        raise AssertionError("campaign-status envelope should return the explain readback")
    if campaign_status["payload"]["campaignSnapshot"]["nextForecastId"] != "forecast-1301":
        raise AssertionError("campaign-status envelope should expose the next forecast id")
    if campaign_status["payload"]["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("campaign-status envelope must keep quality claims blocked")

    campaign_health = success_envelope("campaign_health")
    if campaign_health["payload"]["predictionCampaignDoctorId"] != "predictioncampaigndoctor-001":
        raise AssertionError("campaign-health envelope should return the doctor readback")
    if campaign_health["payload"]["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("campaign-health envelope must not execute resolvers")

    campaign_append = success_envelope("campaign_append_readiness")
    if campaign_append["payload"]["appendCandidate"]["comparableAppendReady"] is not False:
        raise AssertionError("campaign-append-readiness default envelope should not be comparable-ready")
    if campaign_append["payload"]["executionBoundary"]["appendsCorpusEvidence"] is not False:
        raise AssertionError("campaign-append-readiness envelope must not append corpus evidence")

    campaign_calibration = success_envelope("campaign_calibration_status")
    if campaign_calibration["payload"]["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("campaign-calibration-status envelope should expose below-threshold status")
    if campaign_calibration["payload"]["executionBoundary"]["updatesForecastProbabilities"] is not False:
        raise AssertionError("campaign-calibration-status envelope must not update probabilities")

    setup_card = success_envelope("forecast_card", "forecast-1102")
    setup_card_record = setup_card["payload"]["record"]
    setup_binding = setup_card_record["setupBinding"]
    if setup_card_record["forecastId"] != "forecast-1102" or setup_card_record["questionId"] != "question-1102":
        raise AssertionError("private setup forecast card readback should bind forecast-1102/question-1102")
    if setup_binding["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("private setup forecast card readback should expose setup forecast run binding")
    if setup_binding["sourceIntakeHandoffId"] != "sourceintakehandoff-002":
        raise AssertionError("private setup forecast card readback should expose source-handoff binding")
    if setup_binding["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("private setup forecast card readback should expose method-gate binding")
    if setup_card_record["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("private setup forecast card readback should keep source-handoff quality claim blocked")

    setup_bundle = success_envelope("lifecycle_bundle", "forecast-1102")
    setup_bundle_record = setup_bundle["payload"]["record"]
    if setup_bundle_record["includedRecords"]["setupForecastRun"] != "setupforecastrun-1102":
        raise AssertionError("private setup lifecycle bundle should include the setup forecast run")
    if setup_bundle_record["records"]["setupForecastRun"]["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("private setup lifecycle bundle should preserve method-gate binding")
    if setup_bundle_record["records"]["outcomeSummary"]["qualityClaimStatus"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("private setup lifecycle bundle should keep quality claim provisional")

    setup_resolution = success_envelope("resolution_status", "forecast-1102")
    if setup_resolution["payload"]["resolutionRecordId"] != "resolution-1102":
        raise AssertionError("private setup resolution readback should bind resolution-1102")
    if setup_resolution["payload"]["qualityClaim"]["resolvedComparableSourceHandoffOutcomes"] != 1:
        raise AssertionError("private setup resolution readback should expose source-handoff sample count")

    setup_scoring = success_envelope("scoring_summary", "forecast-1102")
    if setup_scoring["payload"]["scoringReportId"] != "scoring-1102":
        raise AssertionError("private setup scoring readback should bind scoring-1102")
    if setup_scoring["payload"]["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("private setup scoring readback should keep quality claim blocked")
    if setup_scoring["payload"]["baselineLift"] <= 0:
        raise AssertionError("private setup scoring readback should preserve positive baseline lift")

    private_setup = success_envelope("private_setup_bundle")
    private_setup_payload = private_setup["payload"]
    if private_setup_payload["sourceKind"] != "local_file":
        raise AssertionError("private-setup-bundle envelope should expose the local-file setup case")
    if private_setup["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-bundle envelope should preserve private setup request binding")
    if private_setup_payload["runbookGuidance"]["nextActionLabel"] != "run_source_builder":
        raise AssertionError("private-setup-bundle envelope should route local files to source-builder guidance")
    if private_setup_payload["claimBoundary"]["bundleDoesNotPredict"] is not True:
        raise AssertionError("private-setup-bundle envelope should not predict")
    if private_setup_payload["executionBoundary"]["bundleDoesNotExecute"] is not True:
        raise AssertionError("private-setup-bundle envelope should stay non-executing")
    if private_setup_payload["executionBoundary"]["runsSuggestedCommand"] is not False:
        raise AssertionError("private-setup-bundle envelope should not run suggested commands")

    adapter_runbook = success_envelope("private_setup_adapter_runbook")
    adapter_runbook_payload = adapter_runbook["payload"]
    sequence_ops = [item["operation"] for item in adapter_runbook_payload["operationSequence"]]
    if sequence_ops[:5] != [
        "private_setup_bundle",
        "private_setup_source_builder",
        "private_setup_source_handoff",
        "private_setup_method_gate",
        "private_setup_forecast_execution",
    ]:
        raise AssertionError("private-setup-adapter-runbook envelope should expose setup operation sequence")
    if sequence_ops[-4:] != ["forecast_card", "lifecycle_bundle", "resolution_status", "scoring_summary"]:
        raise AssertionError("private-setup-adapter-runbook envelope should route generated forecasts to normal reads")
    if adapter_runbook["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-adapter-runbook envelope should preserve private setup request binding")
    if adapter_runbook_payload["executionBoundary"]["runbookDoesNotExecute"] is not True:
        raise AssertionError("private-setup-adapter-runbook envelope should stay guidance-only")
    if adapter_runbook_payload["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-setup-adapter-runbook envelope should not run adapter calls")
    if adapter_runbook_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-adapter-runbook envelope should not create forecast artifacts")

    adapter_conformance_summary = success_envelope("private_setup_adapter_conformance_summary")
    adapter_conformance_summary_payload = adapter_conformance_summary["payload"]
    if adapter_conformance_summary_payload["privateSetupAdapterConformanceSummaryId"] != "privatesetupadapterconformancesummary-001":
        raise AssertionError("private-setup-adapter-conformance-summary envelope should return the checked compact summary")
    if adapter_conformance_summary_payload["bindings"]["privateSetupAdapterConformanceMatrixId"] != "privatesetupadapterconformancematrix-001":
        raise AssertionError("private-setup-adapter-conformance-summary envelope should bind the full matrix")
    if adapter_conformance_summary_payload["caseTotals"]["totalCases"] != 31:
        raise AssertionError("private-setup-adapter-conformance-summary envelope should expose total conformance cases")
    if adapter_conformance_summary_payload["readSurface"]["compactSummaryDoesNotEmbedEnvelopes"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary envelope should remain compact")
    size_budget = adapter_conformance_summary_payload["sizeBudget"]
    if len(render_json(adapter_conformance_summary_payload).encode("utf-8")) > size_budget["compactSummaryPayloadMaxBytes"]:
        raise AssertionError("private-setup-adapter-conformance-summary payload should fit its compact budget")
    if len(render_json(adapter_conformance_summary).encode("utf-8")) > size_budget["compactAgentEnvelopeMaxBytes"]:
        raise AssertionError("private-setup-adapter-conformance-summary envelope should fit its compact budget")
    if size_budget["fullMatrixRequiresExplicitCommand"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary should make full matrix reads explicit")
    if size_budget["oversizedAdapterErrorCode"] != "response_too_large":
        raise AssertionError("private-setup-adapter-conformance-summary should declare response_too_large for oversized reads")
    if "operationCases" in adapter_conformance_summary_payload:
        raise AssertionError("private-setup-adapter-conformance-summary payload should not embed matrix rows")
    if adapter_conformance_summary_payload["artifactBoundary"]["artifactCreationAllowedOnlyFor"] != "private_setup_forecast_execution:confirmed_builder_draft":
        raise AssertionError("private-setup-adapter-conformance-summary envelope should keep artifact creation scoped")
    if adapter_conformance_summary_payload["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary envelope should stay read-only")
    if adapter_conformance_summary_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-adapter-conformance-summary envelope should not create forecast artifacts")

    source_guidance = success_envelope("private_source_adapter_guidance")
    source_guidance_payload = source_guidance["payload"]
    if source_guidance_payload["bindingSummary"]["privateSourceAdapterCapabilityId"] != "privatesourceadaptercapability-001":
        raise AssertionError("private-source-adapter guidance should bind the capability record")
    if source_guidance_payload["bindingSummary"]["privateSourceAdapterOutcomeMatrixId"] != "privateadapteroutcomematrix-001":
        raise AssertionError("private-source-adapter guidance should bind the outcome matrix")
    if source_guidance_payload["bindingSummary"]["privateSourceAdapterIntakeBridgeId"] != "privateadapterintakebridge-001":
        raise AssertionError("private-source-adapter guidance should bind the intake bridge")
    source_summary = {item["sourceKind"]: item for item in source_guidance_payload["sourceKindSummary"]}
    if source_summary["local_file"]["allowedEntrypoint"] != "source_builder":
        raise AssertionError("private-source-adapter guidance should route local files to source-builder")
    if source_summary["manual_mapping"]["requiresApproval"] is not True:
        raise AssertionError("private-source-adapter guidance should preserve manual mapping confirmation")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        row = source_summary[source_kind]
        if row["implementationStatus"] != "planned_contract_only" or row["allowedEntrypoint"] != "no_current_entrypoint":
            raise AssertionError(f"private-source-adapter guidance should keep {source_kind} planned-only")
        if row["canExecuteSourceRead"] or row["canCreateForecastArtifacts"] or row["canCreateScoringRecords"]:
            raise AssertionError(f"private-source-adapter guidance should keep {source_kind} non-generating")
    if source_guidance_payload["executionBoundary"]["guidanceDoesNotExecute"] is not True:
        raise AssertionError("private-source-adapter guidance should stay guidance-only")
    if source_guidance_payload["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-source-adapter guidance should not execute adapter calls")
    if source_guidance_payload["executionBoundary"]["createsSourceManifests"] is not False:
        raise AssertionError("private-source-adapter guidance should not create source manifests")
    if source_guidance_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-adapter guidance should not create forecast artifacts")

    source_kind_selection = success_envelope("private_source_kind_selection")
    source_kind_selection_payload = source_kind_selection["payload"]
    if source_kind_selection_payload["privateSourceKindSelectionExamplesId"] != "privatesourcekindselectionexamples-001":
        raise AssertionError("private-source-kind selection should return the checked examples record")
    if source_kind_selection_payload["bindings"]["privateSourceAdapterGuidanceId"] != "privatesourceadapterguidance-001":
        raise AssertionError("private-source-kind selection should bind source adapter guidance")
    if source_kind_selection_payload["bindings"]["privateSetupAdapterChainRunbookId"] != "privatesetupadapterchainrunbook-001":
        raise AssertionError("private-source-kind selection should bind the adapter-chain runbook")
    selection_rows = {
        item["sourceKind"]: item
        for item in source_kind_selection_payload["selectionExamples"]
    }
    if selection_rows["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise AssertionError("private-source-kind selection should route local files to source-builder")
    if selection_rows["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("private-source-kind selection should require manual mapping confirmation")
    if selection_rows["auto_evidence_connector"]["recommendation"]["immediateAction"] != "call_fixture_evidence":
        raise AssertionError("private-source-kind selection should route auto evidence to fixture evidence")
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        if selection_rows[source_kind]["recommendation"]["immediateAction"] != "wait_for_runtime":
            raise AssertionError(f"private-source-kind selection should keep {source_kind} planned-only")
    if selection_rows["unregistered_source"]["recommendation"]["immediateAction"] != "replace_source":
        raise AssertionError("private-source-kind selection should require unregistered source replacement")
    if selection_rows["unsafe_source"]["recommendation"]["immediateAction"] != "reject_source":
        raise AssertionError("private-source-kind selection should reject unsafe sources")
    if source_kind_selection_payload["executionBoundary"]["examplesDoNotExecute"] is not True:
        raise AssertionError("private-source-kind selection should stay guidance-only")
    if source_kind_selection_payload["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("private-source-kind selection should not execute commands")
    if source_kind_selection_payload["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-kind selection should not create forecast artifacts")

    source_builder_envelopes = [
        item for item in success
        if item["operation"] == "private_setup_source_builder"
    ]
    if len(source_builder_envelopes) != 5:
        raise AssertionError("agent adapter should include five source-builder outcome envelopes")
    source_builder_by_case = {
        item["payload"]["sourceBuilderCase"]: item
        for item in source_builder_envelopes
    }
    local_builder = source_builder_by_case["local_draft"]["payload"]
    if local_builder["sourceManifestBuild"]["buildStatus"] != "draft_ready":
        raise AssertionError("source-builder local draft should be draft-ready")
    if local_builder["sourceManifest"] is None or local_builder["fieldMapping"] is None:
        raise AssertionError("source-builder local draft should include draft manifest and mapping payloads")
    if local_builder["sourceManifestBuild"]["forecastGenerationAllowed"] is not False:
        raise AssertionError("source-builder local draft must not allow forecast generation")
    inferred_mappings = [
        item for item in local_builder["fieldMapping"]["mappings"] + local_builder["fieldMapping"]["aliasMappings"]
        if item["mappingOrigin"] == "agent_inferred"
    ]
    if not inferred_mappings:
        raise AssertionError("source-builder local draft should include proposed inferred mappings")
    if not all(item["mappingStatus"] == "proposed" and item["requiresConfirmation"] is True for item in inferred_mappings):
        raise AssertionError("source-builder inferred mappings should remain proposed and confirmation-gated")
    for case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        rejected = source_builder_by_case[case]["payload"]
        if rejected["sourceManifestBuild"]["buildStatus"] != "rejected":
            raise AssertionError(f"source-builder {case} should be rejected")
        if rejected["sourceManifest"] is not None or rejected["fieldMapping"] is not None:
            raise AssertionError(f"source-builder {case} should not include drafts")
        if rejected["executionBoundary"]["createsForecastArtifacts"] is not False:
            raise AssertionError(f"source-builder {case} should not create forecast artifacts")

    source_handoff_envelopes = [
        item for item in success
        if item["operation"] == "private_setup_source_handoff"
    ]
    if len(source_handoff_envelopes) != 7:
        raise AssertionError("agent adapter should include seven source-handoff outcome envelopes")
    source_handoff_by_case = {
        item["payload"]["sourceHandoffCase"]: item
        for item in source_handoff_envelopes
    }
    expected_handoff_cases = {
        "unconfirmed_builder_draft",
        "confirmed_builder_draft",
        "insufficient_confirmed_builder_draft",
        "contains_secret",
        "unsupported_format",
        "oversized",
        "leakage",
    }
    if set(source_handoff_by_case) != expected_handoff_cases:
        raise AssertionError("source-handoff envelopes should cover every checked handoff case")
    confirmed_handoff = source_handoff_by_case["confirmed_builder_draft"]["payload"]
    if confirmed_handoff["sourceIntakeHandoff"]["handoffStatus"] != "ready_for_method_gating":
        raise AssertionError("confirmed source handoff should be ready for method gating")
    if confirmed_handoff["adapterGuidance"]["canProceedToMethodGating"] is not True:
        raise AssertionError("confirmed source handoff should route toward method gates")
    if confirmed_handoff["adapterGuidance"]["forecastExecutionAllowed"] is not False:
        raise AssertionError("source-handoff adapter must not directly allow forecast execution")
    if confirmed_handoff["bindingSummary"]["sourceIntakeReportId"] != "sourceintakereport-102":
        raise AssertionError("confirmed source handoff should preserve source-intake report binding")
    unconfirmed_handoff = source_handoff_by_case["unconfirmed_builder_draft"]["payload"]
    if unconfirmed_handoff["mappingConfirmation"]["required"] is not True:
        raise AssertionError("unconfirmed source handoff should require mapping confirmation")
    if unconfirmed_handoff["adapterGuidance"]["canProceedToMethodGating"] is not False:
        raise AssertionError("unconfirmed source handoff must not proceed to method gates")
    insufficient_handoff = source_handoff_by_case["insufficient_confirmed_builder_draft"]["payload"]
    if insufficient_handoff["adapterGuidance"]["requiresMoreData"] is not True:
        raise AssertionError("insufficient source handoff should require more data")
    for case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        rejected = source_handoff_by_case[case]["payload"]
        if rejected["sourceIntakeHandoff"]["handoffStatus"] != "blocked_by_builder_rejection":
            raise AssertionError(f"source-handoff {case} should be blocked by builder rejection")
        if rejected["sourceIntakeReport"] is not None:
            raise AssertionError(f"source-handoff {case} should not include source intake reports")
        if rejected["executionBoundary"]["createsForecastArtifacts"] is not False:
            raise AssertionError(f"source-handoff {case} should not create forecast artifacts")
        if rejected["executionBoundary"]["bypassesSetupBenchmarkOrMethodGate"] is not False:
            raise AssertionError(f"source-handoff {case} should not bypass method gates")

    method_gate_envelopes = [
        item for item in success
        if item["operation"] == "private_setup_method_gate"
    ]
    if len(method_gate_envelopes) != 7:
        raise AssertionError("agent adapter should include seven method-gate outcome envelopes")
    method_gate_by_case = {
        item["payload"]["methodGateCase"]: item
        for item in method_gate_envelopes
    }
    if set(method_gate_by_case) != expected_handoff_cases:
        raise AssertionError("method-gate envelopes should cover every checked source-handoff case")
    confirmed_gate = method_gate_by_case["confirmed_builder_draft"]["payload"]
    if confirmed_gate["sourceHandoffMethodGate"]["methodGateStatus"] != "method_selected":
        raise AssertionError("confirmed method gate should select a method")
    if confirmed_gate["setupBenchmarkGate"]["decision"]["executionAllowed"] is not True:
        raise AssertionError("confirmed method gate should preserve benchmark execution permission")
    if confirmed_gate["setupMethodDecision"]["decisionStatus"] != "method_selected":
        raise AssertionError("confirmed method gate should preserve method decision status")
    if confirmed_gate["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not True:
        raise AssertionError("confirmed method gate should recommend explicit setup forecast execution")
    if confirmed_gate["adapterGuidance"]["adapterCreatesForecastArtifacts"] is not False:
        raise AssertionError("method-gate adapter must not create forecast artifacts")
    unconfirmed_gate = method_gate_by_case["unconfirmed_builder_draft"]["payload"]
    if unconfirmed_gate["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("unconfirmed method gate should require mapping confirmation")
    if unconfirmed_gate["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not False:
        raise AssertionError("unconfirmed method gate must not recommend forecast execution")
    insufficient_gate = method_gate_by_case["insufficient_confirmed_builder_draft"]["payload"]
    if insufficient_gate["adapterGuidance"]["requiresMoreData"] is not True:
        raise AssertionError("insufficient method gate should require more data")
    for case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        rejected = method_gate_by_case[case]["payload"]
        if rejected["sourceHandoffMethodGate"]["methodGateStatus"] != "not_entered_source_intake":
            raise AssertionError(f"method-gate {case} should not enter source intake")
        if rejected["setupBenchmarkGate"] is not None or rejected["setupMethodDecision"] is not None:
            raise AssertionError(f"method-gate {case} should not include benchmark or method decision payloads")
        if rejected["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not False:
            raise AssertionError(f"method-gate {case} should not recommend forecast execution")
        if rejected["executionBoundary"]["executesSetupForecast"] is not False:
            raise AssertionError(f"method-gate {case} should not execute setup forecasts")

    forecast_execution_envelopes = [
        item for item in success
        if item["operation"] == "private_setup_forecast_execution"
    ]
    if len(forecast_execution_envelopes) != 7:
        raise AssertionError("agent adapter should include seven forecast-execution outcome envelopes")
    forecast_execution_by_case = {
        item["payload"]["forecastExecutionCase"]: item
        for item in forecast_execution_envelopes
    }
    if set(forecast_execution_by_case) != expected_handoff_cases:
        raise AssertionError("forecast-execution envelopes should cover every checked source-handoff case")
    confirmed_execution = forecast_execution_by_case["confirmed_builder_draft"]["payload"]
    if confirmed_execution["setupForecastRun"]["runStatus"] != "generated":
        raise AssertionError("confirmed forecast execution should generate a setup forecast run")
    if confirmed_execution["bindingSummary"]["forecastId"] != "forecast-1102":
        raise AssertionError("confirmed forecast execution should bind forecast-1102")
    if confirmed_execution["adapterGuidance"]["forecastArtifactsCreated"] is not True:
        raise AssertionError("confirmed forecast execution should create forecast artifacts")
    if confirmed_execution["forecastArtifacts"]["forecastArtifact"]["forecastId"] != "forecast-1102":
        raise AssertionError("confirmed forecast execution should return the bound forecast artifact")
    if confirmed_execution["forecastArtifacts"]["forecastArtifact"]["forecastOutput"] == confirmed_execution["forecastArtifacts"]["forecastArtifact"]["baselineForecast"]:
        raise AssertionError("confirmed forecast execution should preserve the benchmark-gated deterministic forecast output")
    if confirmed_execution["executionBoundary"]["createsScoringRecords"] is not False:
        raise AssertionError("forecast execution must not create scoring records")
    if confirmed_execution["executionBoundary"]["resolvesOutcome"] is not False:
        raise AssertionError("forecast execution must not resolve outcomes")
    unconfirmed_execution = forecast_execution_by_case["unconfirmed_builder_draft"]["payload"]
    if unconfirmed_execution["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("unconfirmed forecast execution should require mapping confirmation")
    if unconfirmed_execution["adapterGuidance"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("unconfirmed forecast execution must not create forecast artifacts")
    insufficient_execution = forecast_execution_by_case["insufficient_confirmed_builder_draft"]["payload"]
    if insufficient_execution["adapterGuidance"]["requiresMoreData"] is not True:
        raise AssertionError("insufficient forecast execution should require more data")
    for case in ["contains_secret", "unsupported_format", "oversized", "leakage"]:
        rejected = forecast_execution_by_case[case]["payload"]
        if rejected["setupForecastRun"]["runStatus"] != "blocked":
            raise AssertionError(f"forecast execution {case} should be blocked")
        if rejected["bindingSummary"]["forecastId"] is not None:
            raise AssertionError(f"forecast execution {case} should not bind a forecast")
        if rejected["forecastArtifacts"]["forecastArtifact"] is not None:
            raise AssertionError(f"forecast execution {case} should not return forecast artifacts")
        if rejected["executionBoundary"]["createsForecastArtifacts"] is not False:
            raise AssertionError(f"forecast execution {case} should not create forecast artifacts")

    for filename, item in envelopes.items():
        rendered = render_json(item)
        if '"error": null' not in rendered and item["status"] == "ok":
            raise AssertionError(f"{filename} success envelope should carry an explicit null error")

    malformed_status = deepcopy(card)
    malformed_status["status"] = "error"
    malformed_status["exitCode"] = 0
    malformed_status["error"] = None
    assert_schema_rejects(malformed_status, "error status with exit code 0 and null error")

    operation_mismatch = deepcopy(card)
    operation_mismatch["adapterRequest"]["operation"] = "scoring_summary"
    assert_semantics_reject(operation_mismatch, "adapter operation mismatch")

    binding_mismatch = deepcopy(card)
    binding_mismatch["recordBinding"]["forecastId"] = "forecast-999"
    assert_semantics_reject(binding_mismatch, "forecast binding mismatch")

    print("checked agent adapter envelopes")


if __name__ == "__main__":
    main()
