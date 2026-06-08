#!/usr/bin/env python3
"""Smoke-test the local single-operation agent adapter dispatcher."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
DISPATCHER = [sys.executable, "scripts/ope.py", "agent-call"]


def run_dispatcher(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*DISPATCHER, *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"dispatcher did not return JSON: {result.stdout!r} {result.stderr!r}") from exc
    errors = validate_record(data, SPEC / "agent-envelope.schema.json")
    if errors:
        raise AssertionError(f"dispatcher envelope failed schema validation: {errors[0]}")
    return data


def assert_error(
    result: subprocess.CompletedProcess[str],
    *,
    exit_code: int,
    error_code: str,
) -> dict[str, object]:
    data = payload(result)
    if result.returncode != exit_code:
        raise AssertionError(f"expected exit code {exit_code}, got {result.returncode}")
    if data["status"] != "error":
        raise AssertionError("expected an error envelope")
    if data["exitCode"] != exit_code:
        raise AssertionError("error envelope exitCode should match process exit code")
    if data["error"]["code"] != error_code:
        raise AssertionError(f"expected error code {error_code}, got {data['error']['code']}")
    if "/Users/" in result.stdout or "Traceback" in result.stderr:
        raise AssertionError("dispatcher error output should be sanitized")
    return data


def assert_setup_forecast_readback(operation: str) -> dict[str, object]:
    result = run_dispatcher(
        "--operation",
        operation,
        "--forecast-id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    data = payload(result)
    if result.returncode != 0:
        raise AssertionError(f"private setup {operation} readback should succeed")
    return data


def main() -> None:
    success = run_dispatcher(
        "--operation",
        "forecast_card",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    success_payload = payload(success)
    if success.returncode != 0:
        raise AssertionError(f"forecast-card agent call should succeed: {success.stderr}")
    if success_payload["payload"]["record"]["forecastId"] != "forecast-602":
        raise AssertionError("forecast-card agent call should bind forecast-602")
    if success_payload["recordBinding"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("forecast-card agent call should preserve source policy binding")

    trace = run_dispatcher(
        "--operation",
        "evidence_trace",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    trace_payload = payload(trace)
    if trace.returncode != 0:
        raise AssertionError(f"evidence-trace agent call should succeed: {trace.stderr}")
    if trace_payload["payload"]["record"]["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence-trace agent call should preserve connector result-set binding")
    if trace_payload["recordBinding"]["evidenceSourceSetId"] != "evidencesourceset-019":
        raise AssertionError("evidence-trace agent call should preserve source-set binding")

    scoring = run_dispatcher(
        "--operation",
        "scoring_summary",
        "--forecast-id",
        "forecast-602",
        "--question-id",
        "question-601",
    )
    scoring_payload = payload(scoring)
    if scoring.returncode != 0 or scoring_payload["payload"]["scoringReportId"] != "scoring-601":
        raise AssertionError("scoring-summary agent call should return scoring-601")

    private_setup = run_dispatcher(
        "--operation",
        "private_setup_bundle",
        "--private-setup-request-id",
        "privatesetuprequest-001",
    )
    private_setup_payload = payload(private_setup)
    if private_setup.returncode != 0:
        raise AssertionError(f"private-setup-bundle agent call should succeed: {private_setup.stderr}")
    private_bundle = private_setup_payload["payload"]
    if private_bundle["sourceKind"] != "local_file":
        raise AssertionError("private-setup-bundle agent call should return the local-file bundle")
    if private_setup_payload["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-bundle agent call should preserve private setup request id")
    if private_bundle["executionBoundary"]["bundleDoesNotExecute"] is not True:
        raise AssertionError("private-setup-bundle agent call must stay non-executing")
    if private_bundle["executionBoundary"]["runsSuggestedCommand"] is not False:
        raise AssertionError("private-setup-bundle agent call must not run suggested commands")

    adapter_runbook = run_dispatcher(
        "--operation",
        "private_setup_adapter_runbook",
    )
    adapter_runbook_payload = payload(adapter_runbook)
    if adapter_runbook.returncode != 0:
        raise AssertionError(f"private-setup-adapter-runbook agent call should succeed: {adapter_runbook.stderr}")
    adapter_runbook_record = adapter_runbook_payload["payload"]
    if adapter_runbook_record["privateSetupAdapterChainRunbookId"] != "privatesetupadapterchainrunbook-001":
        raise AssertionError("private-setup-adapter-runbook agent call should return the checked runbook")
    if adapter_runbook_payload["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("private-setup-adapter-runbook agent call should preserve request binding")
    if adapter_runbook_record["executionBoundary"]["runbookDoesNotExecute"] is not True:
        raise AssertionError("private-setup-adapter-runbook agent call must stay guidance-only")
    if adapter_runbook_record["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-setup-adapter-runbook agent call must not run adapter calls")
    if adapter_runbook_record["operationSequence"][-4]["operation"] != "forecast_card":
        raise AssertionError("private-setup-adapter-runbook agent call should route readback to forecast_card")

    adapter_conformance_summary = run_dispatcher(
        "--operation",
        "private_setup_adapter_conformance_summary",
    )
    adapter_conformance_summary_payload = payload(adapter_conformance_summary)
    if adapter_conformance_summary.returncode != 0:
        raise AssertionError(
            f"private-setup-adapter-conformance-summary agent call should succeed: {adapter_conformance_summary.stderr}"
        )
    adapter_conformance_record = adapter_conformance_summary_payload["payload"]
    if adapter_conformance_record["privateSetupAdapterConformanceSummaryId"] != "privatesetupadapterconformancesummary-001":
        raise AssertionError("private-setup-adapter-conformance-summary agent call should return the compact summary")
    if adapter_conformance_summary_payload["adapterRequest"]["inputRecordType"] != "private_setup_adapter_conformance_summary":
        raise AssertionError("private-setup-adapter-conformance-summary agent call should expose the summary input type")
    if adapter_conformance_record["caseTotals"]["totalCases"] != 31:
        raise AssertionError("private-setup-adapter-conformance-summary agent call should expose matrix case totals")
    if adapter_conformance_record["readSurface"]["compactSummaryDoesNotEmbedEnvelopes"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary agent call should stay compact")
    size_budget = adapter_conformance_record["sizeBudget"]
    if len(adapter_conformance_summary.stdout.encode("utf-8")) > size_budget["compactAgentEnvelopeMaxBytes"]:
        raise AssertionError("private-setup-adapter-conformance-summary agent call should fit compact envelope budget")
    if size_budget["fullMatrixRequiresExplicitCommand"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary should keep full matrix reads explicit")
    if size_budget["oversizedAdapterErrorCode"] != "response_too_large":
        raise AssertionError("private-setup-adapter-conformance-summary should declare response_too_large for oversized reads")
    if "operationCases" in adapter_conformance_record:
        raise AssertionError("private-setup-adapter-conformance-summary should not embed full matrix rows")
    bounded_adapter_conformance_summary = run_dispatcher(
        "--operation",
        "private_setup_adapter_conformance_summary",
        "--max-bytes",
        str(size_budget["compactAgentEnvelopeMaxBytes"]),
    )
    if bounded_adapter_conformance_summary.returncode != 0:
        raise AssertionError("private-setup-adapter-conformance-summary should fit declared maxBytes budget")
    oversized_adapter_conformance_summary = assert_error(
        run_dispatcher(
            "--operation",
            "private_setup_adapter_conformance_summary",
            "--max-bytes",
            "1000",
        ),
        exit_code=5,
        error_code="response_too_large",
    )
    if oversized_adapter_conformance_summary["payload"] is not None:
        raise AssertionError("oversized conformance summary envelope should not include the compact payload")
    if adapter_conformance_record["executionBoundary"]["summaryDoesNotExecute"] is not True:
        raise AssertionError("private-setup-adapter-conformance-summary agent call should not execute")
    if adapter_conformance_record["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-setup-adapter-conformance-summary agent call should not create forecasts")

    setup_engine = run_dispatcher(
        "--operation",
        "setup_engine",
        "--goal",
        "add predictions to my app",
    )
    setup_engine_payload = payload(setup_engine)
    if setup_engine.returncode != 0:
        raise AssertionError(f"setup-engine agent call should succeed: {setup_engine.stderr}")
    setup_record = setup_engine_payload["payload"]
    if setup_record["setupEngineId"] != "setupengine-001":
        raise AssertionError("setup-engine agent call should return the checked setup-engine record")
    if setup_record["candidateForecastContracts"][0]["contractStatus"] != "forecastable":
        raise AssertionError("setup-engine agent call should expose a forecastable first candidate")
    if setup_record["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("setup-engine agent call should render setup before forecast artifacts")
    if setup_record["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("setup-engine agent call should keep quality claims blocked")
    if setup_engine_payload["state"]["forecastStatus"] != "not_created_by_setup_engine":
        raise AssertionError("setup-engine agent call must not create forecasts")

    resolution_jobs = run_dispatcher(
        "--operation",
        "resolution_jobs",
    )
    resolution_jobs_payload = payload(resolution_jobs)
    if resolution_jobs.returncode != 0:
        raise AssertionError(f"resolution-jobs agent call should succeed: {resolution_jobs.stderr}")
    resolution_jobs_record = resolution_jobs_payload["payload"]
    if resolution_jobs_record["summary"]["pendingDueCount"] != 1:
        raise AssertionError("resolution-jobs agent call should expose one due job")
    if resolution_jobs_record["executionBoundary"]["registryExecutesResolvers"] is not False:
        raise AssertionError("resolution-jobs agent call must not execute resolvers")
    due_jobs = [job for job in resolution_jobs_record["jobs"] if job["jobStatus"] == "pending_due"]
    if due_jobs[0]["agentAction"]["recommendedAction"] != "call_resolver_execute":
        raise AssertionError("resolution-jobs agent call should route due jobs to resolver execution")

    scheduler_status = run_dispatcher(
        "--operation",
        "resolution_scheduler_status",
    )
    scheduler_status_payload = payload(scheduler_status)
    if scheduler_status.returncode != 0:
        raise AssertionError(f"resolution-scheduler-status agent call should succeed: {scheduler_status.stderr}")
    scheduler_status_record = scheduler_status_payload["payload"]
    if scheduler_status_record["executionMode"] != "dry_run":
        raise AssertionError("resolution-scheduler-status agent call should expose dry-run mode")
    if scheduler_status_record["lastTick"]["tickStatus"] != "due_pending":
        raise AssertionError("resolution-scheduler-status agent call should expose the last due-pending tick")
    if scheduler_status_record["logPath"] != ".ope/live/resolution-scheduler/scheduler-runs.jsonl":
        raise AssertionError("resolution-scheduler-status agent call should expose the log path")
    scheduler_queue_states = {row["queueState"]: row for row in scheduler_status_record["queueStatusReadbacks"]}
    if scheduler_queue_states["failed"]["presentInLatestTick"] is not False:
        raise AssertionError("resolution-scheduler-status fixture should show no failed queue work")
    if scheduler_status_record["executionBoundary"]["statusReadExecutesScheduler"] is not False:
        raise AssertionError("resolution-scheduler-status agent call must not start the scheduler")
    if scheduler_status_record["executionBoundary"]["executesResolvers"] is not False:
        raise AssertionError("resolution-scheduler-status agent call must not execute resolvers")
    oversized_scheduler_status = assert_error(
        run_dispatcher(
            "--operation",
            "resolution_scheduler_status",
            "--max-bytes",
            "1000",
        ),
        exit_code=5,
        error_code="response_too_large",
    )
    if oversized_scheduler_status["payload"] is not None:
        raise AssertionError("oversized scheduler-status envelope should not include the readback payload")

    campaign_status = run_dispatcher(
        "--operation",
        "campaign_status",
    )
    campaign_status_payload = payload(campaign_status)
    if campaign_status.returncode != 0:
        raise AssertionError(f"campaign-status agent call should succeed: {campaign_status.stderr}")
    campaign_status_record = campaign_status_payload["payload"]
    if campaign_status_record["predictionCampaignExplainId"] != "predictioncampaignexplain-001":
        raise AssertionError("campaign-status agent call should return the explain readback")
    if campaign_status_record["campaignSnapshot"]["nextForecastId"] != "forecast-1301":
        raise AssertionError("campaign-status agent call should expose forecast-1301")
    if campaign_status_record["claimBoundary"]["qualityClaimAllowed"] is not False:
        raise AssertionError("campaign-status agent call must keep quality claims blocked")

    campaign_calibration = run_dispatcher(
        "--operation",
        "campaign_calibration_status",
    )
    campaign_calibration_payload = payload(campaign_calibration)
    if campaign_calibration.returncode != 0:
        raise AssertionError(f"campaign-calibration-status agent call should succeed: {campaign_calibration.stderr}")
    campaign_calibration_record = campaign_calibration_payload["payload"]
    if campaign_calibration_record["calibrationStatus"] != "not_enough_resolved_comparable_outcomes":
        raise AssertionError("campaign-calibration-status should expose below-threshold status")
    if campaign_calibration_record["executionBoundary"]["updatesForecastProbabilities"] is not False:
        raise AssertionError("campaign-calibration-status must not update probabilities")

    internal_api = run_dispatcher(
        "--operation",
        "internal_api",
        "--internal-operation",
        "start_prediction",
        "--prediction-id",
        "predictioncampaign-001",
    )
    internal_api_payload = payload(internal_api)
    if internal_api.returncode != 0:
        raise AssertionError(f"internal-api agent call should succeed: {internal_api.stderr}")
    internal_api_record = internal_api_payload["payload"]
    if internal_api_record["operationName"] != "start_prediction":
        raise AssertionError("internal-api agent call should return the requested internal operation")
    if internal_api_record["operationReceiptId"] is None:
        raise AssertionError("internal-api effectful dry-run should describe the receipt it will return")
    if internal_api_record["executionBoundary"]["writesState"] is not False:
        raise AssertionError("internal-api agent call must be non-mutating")

    database_runtime = run_dispatcher(
        "--operation",
        "database_source_adapter_runtime_status",
    )
    database_runtime_payload = payload(database_runtime)
    if database_runtime.returncode != 0:
        raise AssertionError(f"database source-adapter runtime agent call should succeed: {database_runtime.stderr}")
    database_runtime_record = database_runtime_payload["payload"]
    if database_runtime_record["runtimeStatus"] != "approved_database_source_adapter_runtime_checked":
        raise AssertionError("database source-adapter runtime agent call status drifted")
    if database_runtime_payload["adapterRequest"]["inputRecordType"] != "database_source_adapter_runtime":
        raise AssertionError("database source-adapter runtime agent call input type drifted")
    if database_runtime_record["summary"]["approvedExecutionPathCount"] != 1:
        raise AssertionError("database source-adapter runtime should expose one approved path")
    if database_runtime_record["executionBoundary"]["normalChecksConnectToDatabase"] is not False:
        raise AssertionError("database source-adapter runtime agent call must stay offline")
    if database_runtime_record["executionBoundary"]["credentialValuesStored"] is not False:
        raise AssertionError("database source-adapter runtime agent call must not store credentials")
    if database_runtime_record["executionBoundary"]["rawPrivateRowsStored"] is not False:
        raise AssertionError("database source-adapter runtime agent call must not store raw rows")
    if database_runtime_record["routing"]["databaseSpecificForecastPathCreated"] is not False:
        raise AssertionError("database source-adapter runtime must not create a database-specific forecast path")

    source_guidance = run_dispatcher(
        "--operation",
        "private_source_adapter_guidance",
    )
    source_guidance_payload = payload(source_guidance)
    if source_guidance.returncode != 0:
        raise AssertionError(f"private-source-adapter-guidance agent call should succeed: {source_guidance.stderr}")
    source_guidance_record = source_guidance_payload["payload"]
    if source_guidance_record["bindingSummary"]["privateSourceAdapterCapabilityId"] != "privatesourceadaptercapability-001":
        raise AssertionError("private-source-adapter-guidance agent call should bind capabilities")
    if source_guidance_record["bindingSummary"]["privateSourceAdapterOutcomeMatrixId"] != "privateadapteroutcomematrix-001":
        raise AssertionError("private-source-adapter-guidance agent call should bind outcome matrix")
    source_summary = {item["sourceKind"]: item for item in source_guidance_record["sourceKindSummary"]}
    if source_summary["local_file"]["allowedEntrypoint"] != "source_builder":
        raise AssertionError("private-source-adapter-guidance agent call should route local files to source-builder")
    if source_summary["private_api"]["allowedEntrypoint"] != "no_current_entrypoint":
        raise AssertionError("private-source-adapter-guidance agent call should keep private API runtime planned-only")
    if source_guidance_record["executionBoundary"]["guidanceDoesNotExecute"] is not True:
        raise AssertionError("private-source-adapter-guidance agent call should stay guidance-only")
    if source_guidance_record["executionBoundary"]["runsAdapterCalls"] is not False:
        raise AssertionError("private-source-adapter-guidance agent call should not execute adapter calls")
    if source_guidance_record["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-adapter-guidance agent call should not create forecasts")

    source_kind_selection = run_dispatcher(
        "--operation",
        "private_source_kind_selection",
    )
    source_kind_selection_payload = payload(source_kind_selection)
    if source_kind_selection.returncode != 0:
        raise AssertionError(f"private-source-kind-selection agent call should succeed: {source_kind_selection.stderr}")
    source_kind_selection_record = source_kind_selection_payload["payload"]
    if source_kind_selection_record["privateSourceKindSelectionExamplesId"] != "privatesourcekindselectionexamples-001":
        raise AssertionError("private-source-kind-selection agent call should return checked examples")
    if source_kind_selection_payload["adapterRequest"]["inputRecordType"] != "private_source_kind_selection_examples":
        raise AssertionError("private-source-kind-selection agent call should expose the examples input type")
    if source_kind_selection_record["bindings"]["privateSourceAdapterGuidanceId"] != "privatesourceadapterguidance-001":
        raise AssertionError("private-source-kind-selection agent call should bind source adapter guidance")
    selection_examples = {
        item["sourceKind"]: item
        for item in source_kind_selection_record["selectionExamples"]
    }
    if selection_examples["local_file"]["recommendation"]["immediateAction"] != "call_source_builder_adapter":
        raise AssertionError("private-source-kind-selection agent call should route local files to source-builder")
    if selection_examples["manual_mapping"]["recommendation"]["requiresCallerConfirmation"] is not True:
        raise AssertionError("private-source-kind-selection agent call should require manual mapping confirmation")
    if selection_examples["private_database"]["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("private-source-kind-selection agent call should keep private database planned-only")
    if source_kind_selection_record["executionBoundary"]["examplesDoNotExecute"] is not True:
        raise AssertionError("private-source-kind-selection agent call should stay guidance-only")
    if source_kind_selection_record["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("private-source-kind-selection agent call should not execute commands")
    if source_kind_selection_record["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-kind-selection agent call should not create forecasts")

    selected_source_kind = run_dispatcher(
        "--operation",
        "private_source_kind_selection",
        "--source-kind",
        "private_api",
    )
    selected_source_kind_payload = payload(selected_source_kind)
    if selected_source_kind.returncode != 0:
        raise AssertionError(f"private-source-kind-selection query should succeed: {selected_source_kind.stderr}")
    selected_source_kind_record = selected_source_kind_payload["payload"]
    if selected_source_kind_record["runtimeStatus"] != "selected_example_only":
        raise AssertionError("private-source-kind-selection query should return a compact selected-example payload")
    if selected_source_kind_record["requestedSourceKind"] != "private_api":
        raise AssertionError("private-source-kind-selection query should echo the requested source kind")
    if "selectionExamples" in selected_source_kind_record:
        raise AssertionError("private-source-kind-selection query should not return the full examples list")
    selected_example = selected_source_kind_record["selectedExample"]
    if selected_example["sourceKind"] != "private_api":
        raise AssertionError("private-source-kind-selection query should select the private API example")
    if selected_example["recommendation"]["immediateAction"] != "wait_for_runtime":
        raise AssertionError("private-source-kind-selection query should keep private API planned-only")
    if selected_source_kind_payload["state"]["sourceMode"] != "private_api":
        raise AssertionError("private-source-kind-selection query state should preserve selected source kind")
    if selected_source_kind_payload["state"]["planStatus"] != "selected_example_only":
        raise AssertionError("private-source-kind-selection query state should expose compact selection status")
    if selected_source_kind_record["executionBoundary"]["examplesDoNotExecute"] is not True:
        raise AssertionError("private-source-kind-selection query should stay guidance-only")
    if selected_source_kind_record["executionBoundary"]["runsCommands"] is not False:
        raise AssertionError("private-source-kind-selection query should not run commands")
    if selected_source_kind_record["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("private-source-kind-selection query should not create forecast artifacts")

    unknown_source_kind = assert_error(
        run_dispatcher(
            "--operation",
            "private_source_kind_selection",
            "--source-kind",
            "spreadsheet_macro",
        ),
        exit_code=2,
        error_code="bad_request",
    )
    if unknown_source_kind["payload"] is not None:
        raise AssertionError("unknown source-kind query should not include a payload")
    if unknown_source_kind["state"]["sourceMode"] != "spreadsheet_macro":
        raise AssertionError("unknown source-kind query should preserve sanitized requested source kind state")

    private_bad_request_example = run_dispatcher(
        "--operation",
        "private_setup_bundle",
        "--private-setup-case",
        "unknown_source_kind",
    )
    private_bad_request_payload = payload(private_bad_request_example)
    if private_bad_request_example.returncode != 0:
        raise AssertionError("private-setup-bundle bad-request example should be readable")
    if private_bad_request_payload["payload"]["actionSummary"]["errorCode"] != "unknown_source_kind":
        raise AssertionError("private-setup-bundle case read should expose the requested bad-request class")

    source_builder = run_dispatcher(
        "--operation",
        "private_setup_source_builder",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--source-builder-case",
        "local_draft",
    )
    source_builder_payload = payload(source_builder)
    if source_builder.returncode != 0:
        raise AssertionError(f"private-setup-source-builder agent call should succeed: {source_builder.stderr}")
    source_builder_result = source_builder_payload["payload"]
    source_builder_build = source_builder_result["sourceManifestBuild"]
    if source_builder_build["buildStatus"] != "draft_ready":
        raise AssertionError("source-builder agent call should return a draft-ready build")
    if source_builder_payload["recordBinding"]["requestId"] != "privatesetuprequest-001":
        raise AssertionError("source-builder agent call should preserve private setup request id")
    if source_builder_build["forecastGenerationAllowed"] is not False:
        raise AssertionError("source-builder agent call must not allow forecast generation")
    if source_builder_result["sourceManifest"] is None or source_builder_result["fieldMapping"] is None:
        raise AssertionError("source-builder agent call should include draft manifest and mapping payloads")
    if source_builder_result["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("source-builder agent call must not create forecast artifacts")

    rejected_source_builder = run_dispatcher(
        "--operation",
        "private_setup_source_builder",
        "--source-builder-case",
        "contains_secret",
    )
    rejected_source_builder_payload = payload(rejected_source_builder)
    if rejected_source_builder.returncode != 0:
        raise AssertionError("source-builder rejected-source cases should return an ok adapter envelope")
    rejected_payload = rejected_source_builder_payload["payload"]
    if rejected_payload["sourceManifestBuild"]["buildStatus"] != "rejected":
        raise AssertionError("source-builder contains-secret case should be rejected in the payload")
    if rejected_payload["sourceManifest"] is not None or rejected_payload["fieldMapping"] is not None:
        raise AssertionError("source-builder rejected cases should not include draft artifacts")

    source_builder_input = run_dispatcher(
        "--operation",
        "private_setup_source_builder",
        "--source-builder-input",
        "weather_forecast=spec/fixtures/local-source-files/weather-forecast.json",
        "--source-builder-input",
        "historical_baseline=spec/fixtures/local-source-files/history.csv",
        "--source-builder-input",
        "declared_operations_outcome=spec/fixtures/local-source-files/outcome.csv",
        "--source-builder-mapping-hint",
        "declared_operations_outcome.date=service_date",
    )
    source_builder_input_payload = payload(source_builder_input)
    if source_builder_input.returncode != 0:
        raise AssertionError("source-builder explicit local inputs should succeed")
    if source_builder_input_payload["payload"]["inputMode"] != "caller_approved_files":
        raise AssertionError("source-builder explicit inputs should be labeled caller-approved")

    source_handoff = run_dispatcher(
        "--operation",
        "private_setup_source_handoff",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--source-handoff-case",
        "confirmed_builder_draft",
    )
    source_handoff_payload = payload(source_handoff)
    if source_handoff.returncode != 0:
        raise AssertionError(f"private-setup-source-handoff agent call should succeed: {source_handoff.stderr}")
    source_handoff_result = source_handoff_payload["payload"]
    if source_handoff_result["sourceIntakeHandoff"]["handoffStatus"] != "ready_for_method_gating":
        raise AssertionError("source-handoff confirmed case should be ready for method gating")
    if source_handoff_result["adapterGuidance"]["canProceedToMethodGating"] is not True:
        raise AssertionError("source-handoff confirmed case should expose method-gate readiness")
    if source_handoff_result["adapterGuidance"]["forecastExecutionAllowed"] is not False:
        raise AssertionError("source-handoff adapter must not directly allow forecast execution")
    if source_handoff_result["bindingSummary"]["sourceIntakeReportId"] != "sourceintakereport-102":
        raise AssertionError("source-handoff adapter should preserve source-intake report binding")
    if source_handoff_result["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("source-handoff adapter must not create forecast artifacts")

    blocked_source_handoff = run_dispatcher(
        "--operation",
        "private_setup_source_handoff",
        "--source-handoff-case",
        "unconfirmed_builder_draft",
    )
    blocked_source_handoff_payload = payload(blocked_source_handoff)
    if blocked_source_handoff.returncode != 0:
        raise AssertionError("source-handoff blocked cases should return an ok adapter envelope")
    blocked_handoff = blocked_source_handoff_payload["payload"]
    if blocked_handoff["mappingConfirmation"]["required"] is not True:
        raise AssertionError("source-handoff unconfirmed case should require mapping confirmation")
    if blocked_handoff["adapterGuidance"]["canProceedToMethodGating"] is not False:
        raise AssertionError("source-handoff unconfirmed case must not proceed to method gates")

    rejected_source_handoff = run_dispatcher(
        "--operation",
        "private_setup_source_handoff",
        "--source-handoff-case",
        "leakage",
    )
    rejected_source_handoff_payload = payload(rejected_source_handoff)
    if rejected_source_handoff.returncode != 0:
        raise AssertionError("source-handoff rejected-source cases should return an ok adapter envelope")
    rejected_handoff = rejected_source_handoff_payload["payload"]
    if rejected_handoff["sourceIntakeHandoff"]["handoffStatus"] != "blocked_by_builder_rejection":
        raise AssertionError("source-handoff leakage case should be blocked")
    if rejected_handoff["sourceIntakeReport"] is not None:
        raise AssertionError("source-handoff rejected cases should not include source-intake reports")

    method_gate = run_dispatcher(
        "--operation",
        "private_setup_method_gate",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--method-gate-case",
        "confirmed_builder_draft",
    )
    method_gate_payload = payload(method_gate)
    if method_gate.returncode != 0:
        raise AssertionError(f"private-setup-method-gate agent call should succeed: {method_gate.stderr}")
    method_gate_result = method_gate_payload["payload"]
    if method_gate_result["sourceHandoffMethodGate"]["methodGateStatus"] != "method_selected":
        raise AssertionError("method-gate confirmed case should select a method")
    if method_gate_result["setupBenchmarkGate"]["decision"]["executionAllowed"] is not True:
        raise AssertionError("method-gate confirmed case should preserve benchmark permission")
    if method_gate_result["setupMethodDecision"]["decisionStatus"] != "method_selected":
        raise AssertionError("method-gate confirmed case should preserve method decision")
    if method_gate_result["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not True:
        raise AssertionError("method-gate confirmed case should recommend explicit setup forecast execution")
    if method_gate_result["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("method-gate adapter must not create forecast artifacts")

    blocked_method_gate = run_dispatcher(
        "--operation",
        "private_setup_method_gate",
        "--method-gate-case",
        "unconfirmed_builder_draft",
    )
    blocked_method_gate_payload = payload(blocked_method_gate)
    if blocked_method_gate.returncode != 0:
        raise AssertionError("method-gate blocked cases should return an ok adapter envelope")
    blocked_gate = blocked_method_gate_payload["payload"]
    if blocked_gate["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("method-gate unconfirmed case should require mapping confirmation")
    if blocked_gate["adapterGuidance"]["canRecommendExplicitSetupForecastExecution"] is not False:
        raise AssertionError("method-gate unconfirmed case must not recommend forecast execution")

    rejected_method_gate = run_dispatcher(
        "--operation",
        "private_setup_method_gate",
        "--method-gate-case",
        "leakage",
    )
    rejected_method_gate_payload = payload(rejected_method_gate)
    if rejected_method_gate.returncode != 0:
        raise AssertionError("method-gate rejected-source cases should return an ok adapter envelope")
    rejected_gate = rejected_method_gate_payload["payload"]
    if rejected_gate["sourceHandoffMethodGate"]["methodGateStatus"] != "not_entered_source_intake":
        raise AssertionError("method-gate leakage case should not enter source intake")
    if rejected_gate["setupBenchmarkGate"] is not None or rejected_gate["setupMethodDecision"] is not None:
        raise AssertionError("method-gate rejected cases should not include benchmark or method decisions")

    forecast_execution = run_dispatcher(
        "--operation",
        "private_setup_forecast_execution",
        "--private-setup-request-id",
        "privatesetuprequest-001",
        "--forecast-execution-case",
        "confirmed_builder_draft",
    )
    forecast_execution_payload = payload(forecast_execution)
    if forecast_execution.returncode != 0:
        raise AssertionError(f"private-setup-forecast-execution agent call should succeed: {forecast_execution.stderr}")
    forecast_execution_result = forecast_execution_payload["payload"]
    if forecast_execution_result["setupForecastRun"]["runStatus"] != "generated":
        raise AssertionError("forecast-execution confirmed case should generate a run")
    if forecast_execution_result["bindingSummary"]["forecastId"] != "forecast-1102":
        raise AssertionError("forecast-execution confirmed case should bind forecast-1102")
    if forecast_execution_result["forecastArtifacts"]["forecastArtifact"]["forecastId"] != "forecast-1102":
        raise AssertionError("forecast-execution confirmed case should return the forecast artifact")
    if forecast_execution_result["adapterGuidance"]["forecastArtifactsCreated"] is not True:
        raise AssertionError("forecast-execution confirmed case should report created artifacts")
    if forecast_execution_result["executionBoundary"]["createsScoringRecords"] is not False:
        raise AssertionError("forecast-execution adapter must not create scoring records")

    blocked_forecast_execution = run_dispatcher(
        "--operation",
        "private_setup_forecast_execution",
        "--forecast-execution-case",
        "unconfirmed_builder_draft",
    )
    blocked_forecast_execution_payload = payload(blocked_forecast_execution)
    if blocked_forecast_execution.returncode != 0:
        raise AssertionError("forecast-execution blocked cases should return an ok adapter envelope")
    blocked_execution = blocked_forecast_execution_payload["payload"]
    if blocked_execution["adapterGuidance"]["requiresMappingConfirmation"] is not True:
        raise AssertionError("forecast-execution unconfirmed case should require mapping confirmation")
    if blocked_execution["bindingSummary"]["forecastId"] is not None:
        raise AssertionError("forecast-execution blocked cases should not bind forecasts")
    if blocked_execution["forecastArtifacts"]["forecastArtifact"] is not None:
        raise AssertionError("forecast-execution blocked cases should not return forecast artifacts")

    rejected_forecast_execution = run_dispatcher(
        "--operation",
        "private_setup_forecast_execution",
        "--forecast-execution-case",
        "leakage",
    )
    rejected_forecast_execution_payload = payload(rejected_forecast_execution)
    if rejected_forecast_execution.returncode != 0:
        raise AssertionError("forecast-execution rejected-source cases should return an ok adapter envelope")
    rejected_execution = rejected_forecast_execution_payload["payload"]
    if rejected_execution["setupForecastRun"]["runStatus"] != "blocked":
        raise AssertionError("forecast-execution leakage case should be blocked")
    if rejected_execution["executionBoundary"]["createsForecastArtifacts"] is not False:
        raise AssertionError("forecast-execution leakage case must not create artifacts")

    setup_card_payload = assert_setup_forecast_readback("forecast_card")
    setup_card_record = setup_card_payload["payload"]["record"]
    if setup_card_record["setupBinding"]["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("private setup forecast-card readback should expose setup forecast run")
    if setup_card_record["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("private setup forecast-card readback should keep quality claim blocked")

    setup_bundle_payload = assert_setup_forecast_readback("lifecycle_bundle")
    if setup_bundle_payload["payload"]["record"]["includedRecords"]["setupForecastRun"] != "setupforecastrun-1102":
        raise AssertionError("private setup lifecycle-bundle readback should include setup run")

    setup_resolution_payload = assert_setup_forecast_readback("resolution_status")
    if setup_resolution_payload["payload"]["resolutionRecordId"] != "resolution-1102":
        raise AssertionError("private setup resolution-status readback should bind resolution-1102")
    if setup_resolution_payload["payload"]["qualityClaim"]["resolvedComparableSourceHandoffOutcomes"] != 1:
        raise AssertionError("private setup resolution-status readback should expose source-handoff sample count")

    setup_scoring_payload = assert_setup_forecast_readback("scoring_summary")
    if setup_scoring_payload["payload"]["scoringReportId"] != "scoring-1102":
        raise AssertionError("private setup scoring-summary readback should bind scoring-1102")
    if setup_scoring_payload["payload"]["qualityClaim"]["status"] != "not_enough_resolved_source_handoff_outcomes":
        raise AssertionError("private setup scoring-summary readback should keep quality claim blocked")

    request = run_dispatcher(
        "--operation",
        "forecast_request_validation",
        "--request",
        "spec/fixtures/requests/auto-weather-logistics-request.json",
    )
    request_payload = payload(request)
    if request.returncode != 0 or request_payload["payload"]["decisionStatus"] != "accepted":
        raise AssertionError("request-validation agent call should return accepted decision")

    not_found = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-999",
            "--question-id",
            "question-601",
        ),
        exit_code=4,
        error_code="not_found",
    )
    if not_found["recordBinding"]["forecastId"] != "forecast-999":
        raise AssertionError("not-found envelope should preserve requested forecast id")

    binding = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-602",
            "--question-id",
            "question-999",
        ),
        exit_code=4,
        error_code="binding_mismatch",
    )
    if binding["recordBinding"]["questionId"] != "question-999":
        raise AssertionError("binding-mismatch envelope should preserve requested question id")

    approval = assert_error(
        run_dispatcher(
            "--operation",
            "evidence_plan",
            "--request",
            "spec/fixtures/requests/approval-required-sensitive-request.json",
        ),
        exit_code=3,
        error_code="approval_required",
    )
    if approval["state"]["planStatus"] != "blocked":
        raise AssertionError("approval-required envelope should preserve blocked plan status")

    too_large = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-602",
            "--question-id",
            "question-601",
            "--max-bytes",
            "500",
        ),
        exit_code=5,
        error_code="response_too_large",
    )
    if too_large["payload"] is not None:
        raise AssertionError("response-too-large envelope should not include the oversized payload")

    invalid_max_bytes = assert_error(
        run_dispatcher(
            "--operation",
            "forecast_card",
            "--forecast-id",
            "forecast-602",
            "--question-id",
            "question-601",
            "--max-bytes",
            "0",
        ),
        exit_code=2,
        error_code="bad_request",
    )
    if invalid_max_bytes["adapterRequest"]["maxBytes"] is not None:
        raise AssertionError("invalid maxBytes envelope should not echo schema-invalid maxBytes")

    missing_private_setup = assert_error(
        run_dispatcher(
            "--operation",
            "private_setup_bundle",
            "--private-setup-request-id",
            "privatesetuprequest-999",
        ),
        exit_code=4,
        error_code="not_found",
    )
    if missing_private_setup["recordBinding"]["requestId"] != "privatesetuprequest-999":
        raise AssertionError("missing private setup envelope should preserve requested setup request id")

    malformed_source_builder = assert_error(
        run_dispatcher(
            "--operation",
            "private_setup_source_builder",
            "--source-builder-input",
            "malformed-input",
        ),
        exit_code=2,
        error_code="validation_failed",
    )
    if malformed_source_builder["payload"] is not None:
        raise AssertionError("malformed source-builder envelope should not include a payload")

    print("checked local agent adapter dispatcher")


if __name__ == "__main__":
    main()
