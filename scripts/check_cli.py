#!/usr/bin/env python3
"""Smoke-test the local OPE CLI wrapper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from check_live_capture_workspace import fixture_integration_result
from generate_live_connector_readiness import build_readiness
from live_capture_workspace import build_live_result_set, save_live_result_set


ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )


def run_cli_unchecked(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/ope.py", *args],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


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
    run_cli("generate-fixtures")
    run_cli("resolve-live")
    run_cli("evidence-plan")
    run_cli("gather-evidence")
    run_cli("source-connectors", "--check")
    run_cli("live-readiness", "--check")
    run_cli("transit-api-connector", "--check")
    run_cli("domain-setups", "--check")
    run_cli("transit-delay-forward-run", "--check")
    run_cli("resolve-due-forward-runs", "--check")
    run_cli("resolution-jobs", "--check")
    run_cli("resolution-scheduler", "--check")
    run_cli("source-intake", "--check")
    run_cli("source-builder", "--check")
    run_cli("source-adapter-output", "--check")
    run_cli("source-handoff", "--check")
    run_cli("source-handoff-method", "--check")
    run_cli("auto-forecast")
    run_cli("resolve-auto-evidence")
    run_cli("historical-forecast")
    run_cli("method-comparison", "--check")
    run_cli("method-selection", "--check")
    run_cli("setup-benchmark", "--check")
    run_cli("setup-method", "--check")
    run_cli("setup-forecast", "--check")
    run_cli("source-handoff-forecast", "--check")
    run_cli("resolve-source-handoff")
    run_cli("source-handoff-runbook", "--check")
    run_cli("private-setup-workflow", "--check")
    run_cli("private-source-adapters", "--check")
    run_cli("private-source-adapter-outcomes", "--check")
    run_cli("private-source-adapter-bridge", "--check")
    run_cli("private-setup-requests", "--check")
    run_cli("private-setup-actions", "--check")
    run_cli("private-setup-action-runbook", "--check")
    run_cli("private-setup-bundles", "--check")
    run_cli("private-setup-adapter-runbook", "--check")
    run_cli("private-setup-adapter-conformance", "--check")
    run_cli("private-setup-adapter-conformance-summary", "--check")
    run_cli("private-source-kind-selection", "--check")
    run_cli("private-source-kind-query-matrix", "--check")
    run_cli("recalculation", "--check")
    run_cli("forecast-run", "--check")
    run_cli("forecast-run-matrix", "--check")
    run_cli("forecast-runbook", "--check")
    run_cli("agent-envelopes", "--check")
    run_cli("agent-protocol-map", "--check")
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
    if forward_resolver_payload["scanSummary"]["dueCount"] != 1:
        raise AssertionError("CLI resolve-due-forward-runs fixture should find one due run")
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
    if agent_envelopes_payload["count"] != 45:
        raise AssertionError("CLI agent-envelopes should return forty-two success envelopes and three error envelopes")
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

    agent_protocol_map = run_cli("agent-protocol-map")
    agent_protocol_map_payload = json.loads(agent_protocol_map.stdout)
    if len(agent_protocol_map_payload["operations"]) != 16:
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
