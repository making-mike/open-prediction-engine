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


def main() -> None:
    run_cli("generate-fixtures")
    run_cli("resolve-live")
    run_cli("evidence-plan")
    run_cli("gather-evidence")
    run_cli("source-connectors", "--check")
    run_cli("live-readiness", "--check")
    run_cli("domain-setups", "--check")
    run_cli("source-intake", "--check")
    run_cli("source-builder", "--check")
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
    if domain_setups_payload["count"] != 2:
        raise AssertionError("CLI domain-setups should expose two setup records")
    setup_summaries = {item["domain"]: item for item in domain_setups_payload["domainSetups"]}
    if setup_summaries["weather-logistics"]["maturityStatus"] != "fixture_ready":
        raise AssertionError("CLI domain-setups should expose weather-logistics as fixture-ready")
    if setup_summaries["seaport-berth-availability"]["maturityStatus"] != "candidate":
        raise AssertionError("CLI domain-setups should expose seaport setup as candidate")

    seaport_setup = run_cli("domain-setups", "--setup", "seaport-berth-availability")
    seaport_setup_payload = json.loads(seaport_setup.stdout)
    if seaport_setup_payload["localImplementation"]["forecastRunnable"] is not False:
        raise AssertionError("CLI candidate domain setup should not be forecast runnable")
    if seaport_setup_payload["claimPolicy"]["calibrationClaimAllowed"] is not False:
        raise AssertionError("CLI candidate domain setup should block calibration claims")
    if seaport_setup_payload["claimPolicy"]["productionReadinessClaimAllowed"] is not False:
        raise AssertionError("CLI candidate domain setup should block production readiness claims")

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

    agent_envelopes = run_cli("agent-envelopes")
    agent_envelopes_payload = json.loads(agent_envelopes.stdout)
    if agent_envelopes_payload["count"] != 8:
        raise AssertionError("CLI agent-envelopes should return seven success envelopes and one error envelope")
    success_operations = {
        item["operation"]
        for item in agent_envelopes_payload["envelopes"]
        if item["status"] == "ok"
    }
    if "forecast_card" not in success_operations or "evidence_trace" not in success_operations or "scoring_summary" not in success_operations:
        raise AssertionError("CLI agent-envelopes should expose card, evidence trace, and scoring operations")

    agent_protocol_map = run_cli("agent-protocol-map")
    agent_protocol_map_payload = json.loads(agent_protocol_map.stdout)
    if len(agent_protocol_map_payload["operations"]) != 7:
        raise AssertionError("CLI agent-protocol-map should expose every agent operation")
    protocol_runtime = agent_protocol_map_payload["adapterContract"]["protocolRuntimeImplemented"]
    if protocol_runtime is not True:
        raise AssertionError("CLI agent-protocol-map should reflect local MCP stdio support")
    transports = {item["transport"]: item for item in agent_protocol_map_payload["transportBoundaries"]}
    if transports["mcp"]["implemented"] is not True:
        raise AssertionError("CLI agent-protocol-map should mark local MCP stdio as implemented")
    if transports["http"]["implemented"] is not False or transports["queue"]["implemented"] is not False:
        raise AssertionError("CLI agent-protocol-map should keep HTTP and queue mapping-only")

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
