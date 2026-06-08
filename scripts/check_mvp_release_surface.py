#!/usr/bin/env python3
"""Smoke-check the local MVP release surface and claim boundary."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from generate_lifecycle_operation_store import SCENARIO_NAMES
from generate_release_manifest import build_manifest


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_command(command: list[str]) -> dict[str, Any]:
    rendered = shlex.join(command)
    started = time.perf_counter()
    print(f"[check_mvp_release_surface] start {rendered}", file=sys.stderr, flush=True)
    result = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    print(
        (
            f"[check_mvp_release_surface] done exit={result.returncode} "
            f"elapsed={time.perf_counter() - started:.2f}s {rendered}"
        ),
        file=sys.stderr,
        flush=True,
    )
    result.check_returncode()
    return json.loads(result.stdout)


def run_cli(*args: str) -> dict[str, Any]:
    command = [sys.executable, "scripts/ope.py", *args]
    return run_command(command)


def main() -> None:
    manifest = build_manifest()
    mvp = manifest["mvpLocalRuntime"]
    claim_review = mvp["claimReview"]

    require(mvp["surfaceStatus"] == "local_mvp_fixture_ready", "MVP surface status drifted")
    require(mvp["runtimeMode"] == "local_cli_and_generated_records", "MVP runtime mode drifted")
    require(mvp["runbookPath"] == "spec/mvp-local-runtime.md", "MVP runbook path drifted")
    require("approved_local_folder_runtime" in mvp["supportedSourceInputs"], "MVP should expose the approved local-folder runtime")
    require({item["interface"] for item in mvp["machineInterfaces"]} == {"cli", "agent_call", "mcp_stdio"}, "MVP machine interface coverage drifted")
    require(claim_review["qualityClaimsAllowed"] is False, "MVP must not allow quality claims")
    require(claim_review["liveCalibrationClaimAllowed"] is False, "MVP must not allow live calibration claims")
    require(claim_review["normalChecksUseLiveNetwork"] is False, "MVP release checks must stay offline")
    for non_goal in claim_review["nonGoalRefs"]:
        require(non_goal in manifest["nonGoals"], f"MVP non-goal {non_goal} missing from release manifest")

    local = run_cli("private-setup-orchestrator", "--case", "local_file_confirmed")
    require(local["orchestratorStatus"] == "completed_forecast_readback", "local setup path should complete readback")
    require(local["forecastId"] == "forecast-1102", "local setup path should bind forecast-1102")
    require(local["readbackSummary"]["scoreStatus"] == "scored", "local setup path should expose scored readback")
    require(local["qualityClaimAllowed"] is False, "local setup path must keep quality claim blocked")

    local_runtime = run_cli("local-source-runtime")
    require(local_runtime["summary"]["forecastCardReadyCount"] == 1, "local source runtime should expose one ready card")
    require(local_runtime["forecastCardReadback"]["forecastId"] == "forecast-1102", "local source runtime forecast binding drifted")
    require(local_runtime["summary"]["blockedCount"] == 6, "local source runtime should expose blocked examples")
    require(local_runtime["summary"]["qualityClaimAllowed"] is False, "local source runtime must keep quality claims blocked")

    runtime_security = run_cli("runtime-security")
    require(
        runtime_security["securityStatus"] == "lightweight_runtime_hardening_checked",
        "runtime security status drifted",
    )
    require(runtime_security["dependencyBudget"]["runtimeDependencyCount"] == 0, "runtime dependencies should stay zero")
    require(runtime_security["summary"]["moduleBoundaryCount"] == 7, "runtime security module boundary count drifted")
    require(runtime_security["summary"]["surfaceControlCount"] == 5, "runtime security surface control count drifted")
    require(runtime_security["executionBoundary"]["hostedRuntimeRequired"] is False, "runtime security must not require hosted runtime")
    require(runtime_security["executionBoundary"]["credentialValuesStored"] is False, "runtime security must block credential values")

    agent_kit = run_cli("agent-implementation-kit")
    require(agent_kit["kitStatus"] == "agent_prediction_implementation_kit_checked", "agent kit status drifted")
    require(agent_kit["summary"]["quickstartStepCount"] == 5, "agent kit quickstart step count drifted")
    require(agent_kit["quickstartFrontDoor"]["frontDoorStatus"] == "implementation_follow_up_entrypoint", "agent kit quickstart status drifted")
    require(agent_kit["summary"]["manualStepCount"] == 12, "agent kit manual step count drifted")
    require(agent_kit["summary"]["candidateReadbackCount"] == 4, "agent kit candidate readback count drifted")
    require(agent_kit["summary"]["validationReportCount"] == 4, "agent kit validation report count drifted")
    require(agent_kit["executionBoundary"]["questionDiscoveryCreatesForecastArtifacts"] is False, "question discovery must not create artifacts")
    require(agent_kit["executionBoundary"]["freeFormOracleAllowed"] is False, "agent kit must block free-form oracle behavior")

    agent_integration = run_cli("agent-integrate")
    require(
        agent_integration["integrationStatus"] == "agent_integration_golden_path_checked",
        "agent integration status drifted",
    )
    require(
        agent_integration["summary"]["firstForecastFastTargetMet"] is True,
        "agent integration should meet the first forecast fast gate",
    )
    require(
        agent_integration["summary"]["forecastId"] == "forecast-1102",
        "agent integration forecast binding drifted",
    )
    require(
        agent_integration["efficiencyGate"]["acceptedCaseToolCallCount"] <= 3,
        "agent integration accepted case should stay within three routine calls",
    )
    require(
        agent_integration["executionBoundary"]["qualityClaimsUpgraded"] is False,
        "agent integration must not upgrade quality claims",
    )
    require(
        agent_integration["executionBoundary"]["hostedRuntimeImplemented"] is False,
        "agent integration must not claim hosted runtime",
    )

    agent_guidance = run_cli("agent-guide", "--section", "summary")
    require(agent_guidance["guidanceCaseCount"] == 5, "agent guidance case count drifted")
    require(agent_guidance["implementedMilestoneCount"] == 5, "agent guidance milestone coverage drifted")
    require(agent_guidance["promptPlannerReady"] is True, "agent guidance should expose prompt planner")
    require(agent_guidance["domainAgnosticFlowReady"] is True, "agent guidance should expose generic setup flow")
    require(agent_guidance["helsinkiNarrowingFlowReady"] is True, "agent guidance should expose Helsinki narrowing flow")
    require(agent_guidance["instructionPackReady"] is True, "agent guidance should expose instruction pack")
    require(agent_guidance["forecastArtifactsCreated"] is False, "agent guidance must not create artifacts")
    require(agent_guidance["qualityClaimAllowed"] is False, "agent guidance must not allow quality claims")
    agent_guidance_generic = run_cli("agent-guide", "--section", "generic")
    require(
        agent_guidance_generic["flowStatus"] == "checked_domain_agnostic_setup_flow",
        "agent guidance generic flow status drifted",
    )
    require(
        agent_guidance_generic["keepsHelsinkiAsExample"] is True,
        "agent guidance generic flow should keep Helsinki as an example",
    )

    prediction_feature_setup = run_cli("prediction-feature-setup")
    require(
        prediction_feature_setup["setupStatus"] == "checked_compact_contract",
        "prediction feature setup status drifted",
    )
    require(
        prediction_feature_setup["summary"]["responseExampleCount"] == 5,
        "prediction feature setup response count drifted",
    )
    require(
        prediction_feature_setup["summary"]["acceptedForecastId"] == "forecast-1102",
        "prediction feature setup forecast binding drifted",
    )
    require(
        prediction_feature_setup["createsNewForecastPath"] is False,
        "prediction feature setup must not create a new forecast path",
    )
    require(
        prediction_feature_setup["executionBoundary"]["createsForecastArtifacts"] is False,
        "prediction feature setup must not create forecast artifacts",
    )
    require(
        prediction_feature_setup["executionBoundary"]["qualityClaimAllowed"] is False,
        "prediction feature setup must not allow quality claims",
    )

    setup_engine = run_cli("setup-engine", "--goal", "add predictions to my app")
    require(setup_engine["engineSetupStatus"] == "checked_readback", "setup-engine status drifted")
    require(
        setup_engine["candidateForecastContracts"][0]["contractStatus"] == "forecastable",
        "setup-engine should expose a forecastable first candidate",
    )
    require(
        setup_engine["hostWrapper"]["renderBeforeForecastArtifacts"] is True,
        "setup-engine host wrapper should render before forecast artifacts",
    )
    require(
        setup_engine["claimBoundary"]["qualityClaimAllowed"] is False,
        "setup-engine must keep quality claims blocked",
    )
    require(setup_engine["createsForecastArtifacts"] is False, "setup-engine must not create forecast artifacts")
    require(setup_engine["hostedRuntimeRequired"] is False, "setup-engine must not require hosted runtime")

    prediction_goal_catalog = run_cli("prediction-goal-catalog")
    require(
        prediction_goal_catalog["catalogStatus"] == "checked_domain_agnostic_goal_catalog",
        "prediction goal catalog status drifted",
    )
    require(
        prediction_goal_catalog["summary"]["goalExampleCount"] == 8,
        "prediction goal catalog should expose eight examples",
    )
    require(
        prediction_goal_catalog["summary"]["helsinkiDefaultNarrative"] is False,
        "prediction goal catalog must not default to Helsinki",
    )
    require(
        prediction_goal_catalog["qualityClaimAllowed"] is False,
        "prediction goal catalog must block quality claims",
    )
    require(
        prediction_goal_catalog["createsForecastArtifacts"] is False,
        "prediction goal catalog must not create forecast artifacts",
    )
    require(
        prediction_goal_catalog["hostedRuntimeRequired"] is False,
        "prediction goal catalog must not require hosted runtime",
    )

    embedded_example = run_command(
        [
            sys.executable,
            "examples/embed-ope-prediction-feature/host_wrapper.py",
            "--request",
            "examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json",
            "--output-format",
            "json",
        ]
    )
    require(
        embedded_example["exampleStatus"] == "setup_plan_and_forecast_card_ready",
        "embedded prediction feature example status drifted",
    )
    require(
        embedded_example["opeCallSequence"][0].startswith("python3 scripts/ope.py setup-engine"),
        "embedded prediction feature example must call setup-engine first",
    )
    require(
        embedded_example["setupEnginePlan"]["renderBeforeForecastArtifacts"] is True,
        "embedded prediction feature example must render setup plan before forecast card",
    )
    require(
        embedded_example["setupEnginePlan"]["baselineStatus"]["defaultMethodId"] == "historical_frequency_baseline",
        "embedded prediction feature example should expose baseline guidance",
    )
    require(
        embedded_example["summary"]["forecastId"] == "forecast-1102",
        "embedded prediction feature example forecast binding drifted",
    )
    require(
        embedded_example["executionBoundary"]["opensNetworkListener"] is False,
        "embedded prediction feature example must not open a network listener",
    )
    require(
        embedded_example["executionBoundary"]["storesCredentialValues"] is False,
        "embedded prediction feature example must not store credentials",
    )
    require(
        embedded_example["executionBoundary"]["qualityClaimAllowed"] is False,
        "embedded prediction feature example must not allow quality claims",
    )
    require(
        embedded_example["executionBoundary"]["implementsCustomRiskEngine"] is False,
        "embedded prediction feature example must not implement a host risk engine",
    )

    mcp_adoption = run_cli("mcp-adoption", "--view", "summary")
    require(
        mcp_adoption["adoptionStatus"] == "checked_mcp_adoption_transcripts",
        "MCP adoption path status drifted",
    )
    require(
        mcp_adoption["summary"]["successStepCount"] == 4,
        "MCP adoption path success step count drifted",
    )
    require(
        mcp_adoption["summary"]["blockedTranscriptCount"] == 5,
        "MCP adoption path blocked transcript count drifted",
    )
    require(
        mcp_adoption["summary"]["acceptedForecastId"] == "forecast-1102",
        "MCP adoption path forecast binding drifted",
    )

    postgres = run_cli("postgres-compatibility")
    require(postgres["compatibilityStatus"] == "sqlite_to_postgres_semantics_checked", "Postgres compatibility status drifted")
    require(postgres["summary"]["tableCount"] == 8, "Postgres compatibility table count drifted")
    require(postgres["summary"]["scenarioCount"] == len(SCENARIO_NAMES), "Postgres compatibility scenario count drifted")
    require(postgres["normalChecksConnectToPostgres"] is False, "Postgres compatibility checks must stay offline")
    require(postgres["postgresRuntimeImplemented"] is False, "Postgres compatibility must not claim runtime implementation")
    require(postgres["executionBoundary"]["schemaMigrationExecuted"] is False, "Postgres compatibility must not execute migrations")

    database_runtime = run_cli("database-source-adapter-runtime")
    require(
        database_runtime["runtimeStatus"] == "approved_database_source_adapter_runtime_checked",
        "database source-adapter runtime status drifted",
    )
    require(database_runtime["summary"]["caseCount"] == 9, "database source-adapter runtime case count drifted")
    require(database_runtime["summary"]["approvedExecutionPathCount"] == 1, "database source-adapter runtime approved path count drifted")
    require(database_runtime["summary"]["blockedCaseCount"] == 8, "database source-adapter runtime blocked count drifted")
    require(database_runtime["executionBoundary"]["normalChecksConnectToDatabase"] is False, "database runtime checks must stay offline")
    require(database_runtime["executionBoundary"]["credentialValuesStored"] is False, "database runtime must not store credentials")
    require(database_runtime["executionBoundary"]["rawPrivateRowsStored"] is False, "database runtime must not store raw rows")
    require(database_runtime["routing"]["databaseSpecificForecastPathCreated"] is False, "database runtime must not create a DB-specific forecast path")

    opp_provider = run_cli("opp-provider-adapter")
    require(
        opp_provider["providerAdapterStatus"] == "optional_opp_provider_adapter_checked",
        "OPP provider adapter status drifted",
    )
    require(opp_provider["normalChecksOffline"] is True, "OPP provider adapter normal checks must stay offline")
    require(opp_provider["localMcpStdioTested"] is True, "OPP provider adapter should keep local MCP stdio as tested protocol")
    require(opp_provider["httpProviderRuntimeImplemented"] is False, "OPP provider adapter must keep HTTP runtime future")
    require(opp_provider["sseStreamingImplemented"] is False, "OPP provider adapter must keep SSE future")
    require(opp_provider["paymentSettlementImplemented"] is False, "OPP provider adapter must keep payment settlement future")
    require(opp_provider["aggregationImplemented"] is False, "OPP provider adapter must keep aggregation future")
    require(
        opp_provider["protocolBoundary"]["opeRecordsAuthoritative"] is True,
        "OPP provider adapter must keep OPE records authoritative",
    )
    require(
        opp_provider["protocolBoundary"]["qualityClaimsUpgraded"] is False,
        "OPP provider adapter must not upgrade quality claims",
    )
    require(opp_provider["summary"]["supportedDomainCount"] >= 3, "OPP provider adapter domain coverage drifted")

    persistent_sqlite_policy = run_cli("persistent-sqlite-policy")
    require(
        persistent_sqlite_policy["policyStatus"] == "persistent_sqlite_path_policy_checked",
        "persistent SQLite policy status drifted",
    )
    require(
        persistent_sqlite_policy["persistentSqliteDefaultEnabled"] is False,
        "persistent SQLite must not become default",
    )
    require(
        persistent_sqlite_policy["normalChecksUseEphemeralSqlite"] is True,
        "persistent SQLite policy should keep normal checks ephemeral",
    )
    require(
        persistent_sqlite_policy["executionBoundary"]["normalChecksCreatePersistentDatabase"] is False,
        "persistent SQLite policy must not create persistent databases in normal checks",
    )
    require(
        persistent_sqlite_policy["executionBoundary"]["credentialValuesStored"] is False,
        "persistent SQLite policy must not store credential values",
    )
    require(
        persistent_sqlite_policy["summary"]["readyCaseCount"] == 2,
        "persistent SQLite policy ready count drifted",
    )

    lifecycle_lease_policy = run_cli("lifecycle-lease-policy")
    require(
        lifecycle_lease_policy["policyStatus"] == "lifecycle_operation_lease_policy_checked",
        "lifecycle lease policy status drifted",
    )
    require(
        lifecycle_lease_policy["summary"]["strictLeaseCount"] == 9,
        "lifecycle lease policy strict lease count drifted",
    )
    require(
        lifecycle_lease_policy["summary"]["idempotencyOnlyCount"] == 5,
        "lifecycle lease policy idempotency-only count drifted",
    )
    require(
        lifecycle_lease_policy["summary"]["allEffectfulOperationsRequireIdempotency"] is True,
        "lifecycle lease policy should require idempotency for all effectful operations",
    )
    require(
        lifecycle_lease_policy["summary"]["normalChecksAcquireLeases"] is False,
        "lifecycle lease policy should keep normal checks lease-free",
    )
    require(
        lifecycle_lease_policy["executionBoundary"]["rawCrudExposed"] is False,
        "lifecycle lease policy must not expose raw CRUD",
    )
    require(
        lifecycle_lease_policy["executionBoundary"]["hostedRuntimeImplemented"] is False,
        "lifecycle lease policy must not claim hosted runtime implementation",
    )
    require(
        lifecycle_lease_policy["executionBoundary"]["leasesAcquiredByReadback"] is False,
        "lifecycle lease policy readbacks must not acquire leases",
    )

    runtime_transport = run_cli("runtime-transport-readiness")
    require(
        runtime_transport["readinessStatus"] == "runtime_transport_readiness_checked",
        "runtime transport readiness status drifted",
    )
    require(
        runtime_transport["summary"]["currentSurfaceCount"] == 4,
        "runtime transport current surface count drifted",
    )
    require(
        runtime_transport["summary"]["futureSurfaceCount"] == 4,
        "runtime transport future surface count drifted",
    )
    require(
        runtime_transport["summary"]["metLocalCriteriaCount"] == 6,
        "runtime transport met local criteria count drifted",
    )
    require(
        runtime_transport["summary"]["blockedCaseCount"] == 7,
        "runtime transport blocked case count drifted",
    )
    require(
        runtime_transport["hostedRuntimeAllowedNow"] is False,
        "runtime transport readiness must keep hosted runtime blocked",
    )
    require(
        runtime_transport["localHttpAllowedNow"] is False,
        "runtime transport readiness must keep local HTTP deferred",
    )
    require(
        runtime_transport["executionBoundary"]["networkListenerStarted"] is False,
        "runtime transport readiness must not start network listeners",
    )
    require(
        runtime_transport["executionBoundary"]["hostedServiceImplemented"] is False,
        "runtime transport readiness must not implement hosted service",
    )

    workspace_tenant = run_cli("workspace-tenant-isolation")
    require(
        workspace_tenant["isolationStatus"] == "workspace_tenant_isolation_checked",
        "workspace tenant isolation status drifted",
    )
    require(
        workspace_tenant["summary"]["tenantWorkspaceCount"] == 2,
        "workspace tenant isolation should expose two tenant workspaces",
    )
    require(
        workspace_tenant["summary"]["blockedAccessCaseCount"] == 6,
        "workspace tenant isolation should expose six blocked access cases",
    )
    require(
        workspace_tenant["normalChecksMutateState"] is False,
        "workspace tenant isolation must keep normal checks non-mutating",
    )
    require(
        workspace_tenant["hostedTenantRuntimeImplemented"] is False,
        "workspace tenant isolation must not implement hosted tenant runtime",
    )
    require(
        workspace_tenant["executionBoundary"]["crossTenantReadAllowed"] is False,
        "workspace tenant isolation must block cross-tenant reads",
    )
    require(
        workspace_tenant["executionBoundary"]["crossTenantSourceReuseAllowed"] is False,
        "workspace tenant isolation must block cross-tenant source reuse",
    )

    domain_source_policy = run_cli("domain-source-field-policy")
    require(
        domain_source_policy["policyStatus"] == "domain_source_field_policy_checked",
        "domain/source field policy status drifted",
    )
    require(
        domain_source_policy["summary"]["universalDomainFieldCount"] == 10,
        "domain/source field policy domain field count drifted",
    )
    require(
        domain_source_policy["summary"]["universalSourceBindingFieldCount"] == 10,
        "domain/source field policy source field count drifted",
    )
    require(
        domain_source_policy["summary"]["domainSpecificExtensionFieldCount"] == 8,
        "domain/source field policy extension count drifted",
    )
    require(
        domain_source_policy["normalChecksMutateState"] is False,
        "domain/source field policy must keep normal checks non-mutating",
    )
    require(
        domain_source_policy["generatedRuntimeTypesIncluded"] is False,
        "domain/source field policy must not generate runtime types",
    )
    require(
        domain_source_policy["executionBoundary"]["rawSqlAllowed"] is False,
        "domain/source field policy must block raw SQL fields",
    )
    require(
        domain_source_policy["executionBoundary"]["hostedRuntimeImplemented"] is False,
        "domain/source field policy must not implement hosted runtime",
    )

    credential_policy = run_cli("credential-reference-policy")
    require(
        credential_policy["policyStatus"] == "credential_reference_policy_checked",
        "credential reference policy status drifted",
    )
    require(
        credential_policy["summary"]["acceptedReferenceMechanismCount"] == 4,
        "credential reference mechanism count drifted",
    )
    require(
        credential_policy["summary"]["requiredScopeKeyCount"] == 8,
        "credential reference scope key count drifted",
    )
    require(
        credential_policy["summary"]["blockedCaseCount"] == 8,
        "credential reference blocked case count drifted",
    )
    require(
        credential_policy["normalChecksMutateState"] is False,
        "credential reference policy must keep normal checks non-mutating",
    )
    require(
        credential_policy["secretResolverImplemented"] is False,
        "credential reference policy must not implement a secret resolver",
    )
    require(
        credential_policy["executionBoundary"]["normalChecksResolveSecrets"] is False,
        "credential reference policy must not resolve secrets in normal checks",
    )

    retention_policy = run_cli("retention-redaction-policy")
    require(
        retention_policy["policyStatus"] == "retention_redaction_policy_checked",
        "retention/redaction policy status drifted",
    )
    require(
        retention_policy["summary"]["retentionClassCount"] == 8,
        "retention/redaction class count drifted",
    )
    require(
        retention_policy["summary"]["physicalDeleteGateCount"] == 8,
        "retention/redaction physical delete gate count drifted",
    )
    require(
        retention_policy["summary"]["decisionCaseCount"] == 12,
        "retention/redaction case count drifted",
    )
    require(
        retention_policy["normalChecksMutateState"] is False,
        "retention/redaction policy must keep normal checks non-mutating",
    )
    require(
        retention_policy["physicalDeleteDefaultEnabled"] is False,
        "retention/redaction policy must keep physical delete non-default",
    )
    require(
        retention_policy["executionBoundary"]["normalChecksPhysicallyDelete"] is False,
        "retention/redaction policy must not physically delete in normal checks",
    )
    require(
        retention_policy["executionBoundary"]["silentDeleteAllowed"] is False,
        "retention/redaction policy must block silent delete",
    )
    require(
        credential_policy["executionBoundary"]["storesCredentialValues"] is False,
        "credential reference policy must not store credential values",
    )

    private_auto_policy = run_cli("private-auto-evidence-policy")
    require(
        private_auto_policy["policyStatus"] == "private_auto_evidence_policy_checked",
        "private auto-evidence policy status drifted",
    )
    require(
        private_auto_policy["summary"]["sourceKindCount"] == 8,
        "private auto-evidence source-kind count drifted",
    )
    require(
        private_auto_policy["summary"]["policyGateCount"] == 12,
        "private auto-evidence gate count drifted",
    )
    require(
        private_auto_policy["summary"]["decisionCaseCount"] == 13,
        "private auto-evidence case count drifted",
    )
    require(
        private_auto_policy["normalChecksReadPrivateSources"] is False,
        "private auto-evidence policy must not read private sources in normal checks",
    )
    require(
        private_auto_policy["executionBoundary"]["arbitraryWebSearchAllowed"] is False,
        "private auto-evidence policy must block arbitrary web search",
    )
    require(
        private_auto_policy["executionBoundary"]["rawSqlExecutionAllowed"] is False,
        "private auto-evidence policy must block raw SQL execution",
    )
    require(
        private_auto_policy["executionBoundary"]["generatedRuntimeTypesEnabled"] is False,
        "private auto-evidence policy must not enable generated runtime types",
    )

    adoption = run_cli("developer-adoption")
    require(adoption["summary"]["quickstartStepCount"] == 8, "developer adoption quickstart count drifted")
    require(adoption["bindings"]["forecastId"] == "forecast-1102", "developer adoption forecast binding drifted")
    require(adoption["summary"]["qualityClaimAllowed"] is False, "developer adoption must keep quality claims blocked")
    require(adoption["summary"]["generatedTypesIncluded"] is False, "developer adoption should defer generated runtime types")

    pilot_evidence = run_cli("pilot-evidence")
    require(pilot_evidence["summary"]["acceptedRealSessionCount"] == 0, "pilot evidence should not count real sessions yet")
    require(pilot_evidence["summary"]["pilotEvidenceStatus"] == "real_sessions_needed", "pilot evidence should require real sessions")
    require(pilot_evidence["summary"]["expansionEvidenceReady"] is False, "pilot evidence must not unblock expansion")
    require(pilot_evidence["summary"]["qualityClaimAllowed"] is False, "pilot evidence must keep quality claims blocked")
    pilot_evidence_append = run_cli(
        "pilot-evidence",
        "--input-summary",
        "spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json",
    )
    require(
        pilot_evidence_append["appendDecision"] == "ready_for_local_write",
        "pilot evidence append plan should be ready for explicit local write",
    )
    require(
        pilot_evidence_append["writeLocalRequested"] is False,
        "pilot evidence append plan should be dry-run by default",
    )
    require(
        pilot_evidence_append["ledgerRowsWritten"] == 0,
        "pilot evidence append plan must not write local rows by default",
    )
    pilot_lifecycle = run_cli("lifecycle-operation-store", "--scenario", "pilot-evidence-append")
    require(pilot_lifecycle["scenarioName"] == "pilot-evidence-append", "pilot evidence lifecycle scenario drifted")
    require(pilot_lifecycle["operationName"] == "evidence.append", "pilot evidence lifecycle operation drifted")
    require(
        pilot_lifecycle["preflight"]["plannedWrites"][1]["recordType"] == "pilot_evidence_ledger_row",
        "pilot evidence lifecycle should plan a pilot evidence ledger row",
    )
    require("pilot_findings" in pilot_lifecycle["readModelEffects"], "pilot evidence lifecycle should update pilot findings")
    require("calibration_status" not in pilot_lifecycle["readModelEffects"], "pilot evidence lifecycle must not update calibration status")
    require("track_record_progress" not in pilot_lifecycle["readModelEffects"], "pilot evidence lifecycle must not update track record")

    pilot_session = run_cli("pilot-session-packet")
    require(pilot_session["collectionSummary"]["taskCardCount"] == 7, "pilot session packet should expose seven task cards")
    require(pilot_session["collectionSummary"]["realSessionsRecorded"] == 0, "pilot session packet must not record real sessions")
    require(pilot_session["collectionSummary"]["ledgerSubmissionReady"] is True, "pilot session packet should be ledger-submission ready")
    require(pilot_session["collectionSummary"]["expansionEvidenceReady"] is False, "pilot session packet must not unblock expansion")
    require(pilot_session["collectionSummary"]["qualityClaimAllowed"] is False, "pilot session packet must keep quality claims blocked")

    pilot_summary = run_cli("pilot-summary-intake")
    require(pilot_summary["summary"]["acceptedLedgerReadyCount"] == 2, "pilot summary intake should expose two ledger-ready examples")
    require(pilot_summary["summary"]["blockedCaseCount"] == 3, "pilot summary intake should expose blocked examples")
    require(pilot_summary["summary"]["realSessionsRecorded"] == 0, "pilot summary intake must not record real sessions")
    require(pilot_summary["summary"]["ledgerRowsWritten"] == 0, "pilot summary intake must not write ledger rows")
    require(pilot_summary["summary"]["expansionEvidenceReady"] is False, "pilot summary intake must not unblock expansion")
    require(pilot_summary["summary"]["qualityClaimAllowed"] is False, "pilot summary intake must keep quality claims blocked")
    pilot_summary_input = run_cli(
        "pilot-summary-intake",
        "--input",
        "spec/fixtures/pilot-summary-intake/accepted-setup-engine-summary.json",
    )
    require(
        pilot_summary_input["intakeDecision"] == "accept_for_ledger_review",
        "pilot summary input classifier should accept sanitized setup-engine summaries",
    )
    require(
        pilot_summary_input["candidateRealSessionEvidence"] is True,
        "pilot summary input classifier should mark accepted summaries as candidate real-session evidence",
    )
    require(
        pilot_summary_input["contributesRealSessionEvidence"] is False,
        "pilot summary input classifier must not count real sessions",
    )
    require(pilot_summary_input["ledgerRowsWritten"] == 0, "pilot summary input classifier must not write ledger rows")

    pilot_summary_template = run_cli("pilot-summary-template", "--section", "summary")
    require(pilot_summary_template["templateStatus"] == "ready_for_operator_fill", "pilot summary template should be operator-fill ready")
    require(
        pilot_summary_template["recommendedScenarioKey"] == "engine_setup_shortcut_comprehension",
        "pilot summary template should default to setup-comprehension task",
    )
    require(pilot_summary_template["draftLedgerReady"] is False, "pilot summary template draft must not be ledger-ready unchanged")
    require(
        pilot_summary_template["draftContributesRealSessionEvidence"] is False,
        "pilot summary template draft must not count real evidence",
    )
    require(pilot_summary_template["qualityClaimAllowed"] is False, "pilot summary template must keep quality claims blocked")
    require(pilot_summary_template["hostedRuntimeAllowed"] is False, "pilot summary template must keep hosted runtime blocked")

    simulated_pilot = run_cli("simulated-agent-pilot", "--section", "summary")
    require(simulated_pilot["simulatedSessionCount"] == 8, "simulated pilot should expose eight sessions")
    require(simulated_pilot["userPromptSessionCount"] == 1, "simulated pilot should include the user prompt")
    require(simulated_pilot["generatedPromptSessionCount"] == 7, "simulated pilot should include seven generated prompts")
    require(simulated_pilot["nonHelsinkiSessionCount"] == 3, "simulated pilot should include non-Helsinki prompts")
    require(simulated_pilot["engineSetupComprehensionReady"] is True, "simulated pilot should expose setup comprehension readiness")
    require(simulated_pilot["realSessionsRecorded"] == 0, "simulated pilot must not record real sessions")
    require(simulated_pilot["pilotEvidenceReady"] is False, "simulated pilot must not unblock real pilot evidence")
    require(simulated_pilot["qualityClaimAllowed"] is False, "simulated pilot must keep quality claims blocked")

    pilot_findings = run_cli("pilot-findings", "--section", "summary")
    require(pilot_findings["acceptedRealSessionCount"] == 0, "pilot findings should not fabricate real sessions")
    require(pilot_findings["acceptedSimulatedAgentSessionCount"] == 8, "pilot findings should expose simulated sessions")
    require(pilot_findings["nonHelsinkiSimulatedSessionCount"] == 3, "pilot findings should expose non-Helsinki sessions")
    require(pilot_findings["agentSimulationEvidenceReady"] is True, "pilot findings should mark simulation evidence ready")
    require(pilot_findings["pilotEvidenceReady"] is False, "pilot findings should require real sessions")
    require(pilot_findings["localPilotEvidenceMode"] == "not_requested", "pilot findings should not read local evidence by default")
    require(pilot_findings["generatedTypesEvidenceReady"] is False, "pilot findings should not unblock generated types")
    require(pilot_findings["qualityClaimAllowed"] is False, "pilot findings should not allow quality claims")
    require(pilot_findings["hostedRuntimeAllowed"] is False, "pilot findings should not allow hosted runtime")

    pilot_supervision = run_cli("pilot-supervision-status", "--section", "summary")
    require(pilot_supervision["status"] == "real_sessions_needed", "pilot supervision status should require real sessions")
    require(pilot_supervision["acceptedRealSessionCount"] == 0, "pilot supervision status must not fabricate real sessions")
    require(pilot_supervision["remainingMinimumSessions"] == 3, "pilot supervision status should expose remaining minimum sessions")
    require(pilot_supervision["remainingTargetSessions"] == 5, "pilot supervision status should expose remaining target sessions")
    require(
        pilot_supervision["recommendedScenarioKey"] == "engine_setup_shortcut_comprehension",
        "pilot supervision status should recommend setup-comprehension task",
    )
    require(pilot_supervision["pilotEvidenceReady"] is False, "pilot supervision status should keep pilot evidence blocked")
    require(pilot_supervision["qualityClaimAllowed"] is False, "pilot supervision status should keep quality claims blocked")
    require(pilot_supervision["hostedRuntimeAllowed"] is False, "pilot supervision status should keep hosted runtime blocked")

    generated_types = run_cli("generated-types-decision", "--section", "summary")
    require(
        generated_types["decisionStatus"] == "defer_until_adoption_evidence",
        "generated types decision should remain deferred",
    )
    require(generated_types["generatedTypesIncluded"] is False, "generated types must not be included")
    require(generated_types["selectedLanguageTargetCount"] == 0, "generated types target count drifted")
    require(generated_types["acceptedRealSessionCount"] == 0, "generated types decision should reflect zero real sessions")
    require(
        generated_types["acceptedSimulatedAgentSessionCount"] == 8,
        "generated types decision should reflect simulated sessions",
    )

    expansion = run_cli("expansion-readiness")
    require(expansion["gateStatus"] == "blocked_pending_evidence", "expansion readiness should remain blocked")
    require(expansion["bindings"]["pilotEvidenceLedgerId"] == "pilotevidenceledger-001", "expansion readiness pilot evidence binding drifted")
    require(expansion["summary"]["readyOptionCount"] == 0, "expansion readiness should not mark options ready")
    require(expansion["summary"]["hostedRuntimeAllowed"] is False, "expansion readiness must block hosted runtime")
    require(expansion["summary"]["qualityClaimAllowed"] is False, "expansion readiness must block quality claims")
    require(expansion["summary"]["generatedTypesIncluded"] is False, "expansion readiness should defer generated runtime types")

    campaign_plan = run_cli("prediction-campaign", "plan")
    require(campaign_plan["planningWindow"]["dryRunPlannerImplemented"] is True, "prediction campaign should expose a dry-run planner")
    require(len(campaign_plan["plannedRuns"]) == 4, "prediction campaign should expose four planned runs")
    require(campaign_plan["plannedRuns"][0]["runId"] == "predictionrun-1301", "prediction campaign run ID drifted")
    require(campaign_plan["plannedRuns"][0]["createsForecastArtifacts"] is False, "prediction campaign must not create artifacts")

    campaign_runner = run_cli("prediction-campaign", "start")
    require(campaign_runner["runnerStatus"] == "dry_run_ready_non_executing", "prediction campaign runner status drifted")
    require(campaign_runner["summary"]["terminalRunnerSurfaceImplemented"] is True, "prediction campaign runner surface should be implemented")
    require(campaign_runner["summary"]["forecastCreationImplemented"] is True, "prediction campaign runner should expose explicit local forecast creation")
    require(campaign_runner["summary"]["preCalibrationImplemented"] is True, "prediction campaign runner should expose pre-calibration")
    require(campaign_runner["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign runner must not write live state")

    campaign_pre_calibration = run_cli("prediction-campaign", "pre-calibration")
    require(campaign_pre_calibration["preCalibrationStatus"] == "ready", "prediction campaign pre-calibration status drifted")
    require(campaign_pre_calibration["calibrationMethod"]["calibratedProbability"] == 0.25, "prediction campaign pre-calibration probability drifted")
    require(campaign_pre_calibration["summary"]["historicalOnly"] is True, "prediction campaign pre-calibration must be historical-only")
    require(campaign_pre_calibration["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign pre-calibration must not write by default")

    campaign_forecast_creation = run_cli("prediction-campaign", "forecast-create")
    require(campaign_forecast_creation["creationStatus"] == "ready_dry_run_creation_request", "prediction campaign forecast creation status drifted")
    require(campaign_forecast_creation["readyRun"]["runId"] == "predictionrun-1301", "prediction campaign forecast creation run drifted")
    require(campaign_forecast_creation["summary"]["effectfulForecastCreationImplemented"] is False, "prediction campaign forecast creation must remain non-effectful")
    require(campaign_forecast_creation["executionBoundary"]["createsForecastArtifacts"] is False, "prediction campaign forecast creation must not create artifacts")

    campaign_forecast_artifact = run_cli("prediction-campaign", "forecast-artifact")
    require(campaign_forecast_artifact["forecastId"] == "forecast-1301", "prediction campaign forecast artifact ID drifted")
    require(campaign_forecast_artifact["questionId"] == "question-1301", "prediction campaign forecast question ID drifted")
    require(campaign_forecast_artifact["questionStatus"] == "open", "prediction campaign forecast should remain unresolved")
    require(
        campaign_forecast_artifact["forecastOutput"] == campaign_forecast_artifact["baselineForecast"],
        "prediction campaign forecast artifact should remain baseline-only",
    )

    campaign_card = run_cli("read", "--record-type", "forecast-card", "--id", "forecast-1301", "--question-id", "question-1301")
    require(campaign_card["record"]["status"] == "open", "prediction campaign forecast card should remain open")
    require(campaign_card["record"]["score"] is None, "prediction campaign forecast card should remain unscored")
    require(campaign_card["record"]["qualityClaim"]["status"] == "unresolved", "prediction campaign forecast card quality boundary drifted")

    campaign_forecast_write = run_cli("prediction-campaign", "forecast-write")
    require(campaign_forecast_write["writeStatus"] == "ready_for_explicit_local_write", "prediction campaign forecast write status drifted")
    require(campaign_forecast_write["bindings"]["forecastId"] == "forecast-1301", "prediction campaign forecast write binding drifted")
    require(campaign_forecast_write["summary"]["effectfulLocalWriteImplemented"] is False, "prediction campaign forecast write should remain a plan")
    require(campaign_forecast_write["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign forecast write must not mutate state")

    campaign_resolution_attempt = run_cli("prediction-campaign", "resolve")
    require(campaign_resolution_attempt["attemptStatus"] == "dry_run_due_ready", "prediction campaign resolution attempt status drifted")
    require(campaign_resolution_attempt["bindings"]["forecastId"] == "forecast-1301", "prediction campaign resolution attempt binding drifted")
    require(campaign_resolution_attempt["attemptResult"]["failureCategory"] == "none", "dry-run resolution attempt should not fail")
    require(campaign_resolution_attempt["executionBoundary"]["executesResolvers"] is False, "resolution attempt must not execute resolvers")

    campaign_resolution_execute = run_cli("prediction-campaign", "resolve", "--run-id", "predictionrun-1301", "--execute-resolvers")
    require(campaign_resolution_execute["attemptStatus"] == "blocked_missing_outcome_source", "explicit resolution attempt status drifted")
    require(campaign_resolution_execute["attemptResult"]["failureCategory"] == "source_unavailable", "explicit resolution attempt failure category drifted")
    require(campaign_resolution_execute["summary"]["resolverExecutionImplemented"] is True, "resolver execution runtime should be implemented")
    require(campaign_resolution_execute["duplicateSafety"]["duplicateScoringBlocked"] is True, "resolution attempt must block duplicate scoring")

    campaign_resolution_source_ready = run_cli(
        "prediction-campaign",
        "resolve",
        "--run-id",
        "predictionrun-1301",
        "--execute-resolvers",
        "--outcome-csv",
        ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/outcome.csv",
    )
    require(
        campaign_resolution_source_ready["attemptStatus"] == "dry_run_execute_ready",
        "declared outcome source should make resolution ready for explicit write",
    )
    require(
        campaign_resolution_source_ready["summary"]["resolutionArtifactsCreated"] is False,
        "source-ready resolution readback must remain non-mutating",
    )

    campaign_resolution_duplicate = run_cli("prediction-campaign", "resolve", "--attempt-case", "blocked_duplicate", "--execute-resolvers")
    require(campaign_resolution_duplicate["attemptStatus"] == "blocked_duplicate_run", "duplicate resolution attempt status drifted")
    require(campaign_resolution_duplicate["attemptResult"]["failureCategory"] == "duplicate_blocked", "duplicate resolution failure category drifted")
    require(campaign_resolution_duplicate["attemptResult"]["scoringRecordsCreated"] is False, "duplicate resolution attempt must not create scoring")

    campaign_doctor = run_cli("prediction-campaign", "doctor")
    require(campaign_doctor["doctorStatus"] == "actionable_due_run", "prediction campaign doctor status drifted")
    require(campaign_doctor["health"]["dueRunCount"] == 1, "prediction campaign doctor should expose one due run")
    require(campaign_doctor["health"]["blockedRunCount"] == 1, "prediction campaign doctor should expose one blocked resolver path")
    require(campaign_doctor["duplicateProtection"]["priorEvidenceOverwriteAllowed"] is False, "doctor must block prior evidence overwrite")
    require(campaign_doctor["summary"]["appendReadyReadbackImplemented"] is True, "doctor should expose append-ready readback")
    require(campaign_doctor["executionBoundary"]["writesIgnoredLiveState"] is False, "doctor must not write ignored state")

    campaign_resume = run_cli("prediction-campaign", "resume")
    require(campaign_resume["resumeStatus"] == "checked_resume_plan_non_mutating", "prediction campaign resume status drifted")
    require(campaign_resume["bindings"]["forecastId"] == "forecast-1301", "prediction campaign resume forecast binding drifted")
    require(campaign_resume["observedState"]["priorEvidenceOverwriteAllowed"] is False, "prediction campaign resume must not allow overwrite")
    require(campaign_resume["summary"]["effectfulResumeImplemented"] is False, "prediction campaign resume must remain non-effectful")
    require(campaign_resume["executionBoundary"]["writesIgnoredLiveState"] is False, "prediction campaign resume must not write live state")

    campaign_resume_state = run_cli("prediction-campaign", "resume", "--resume-case", "interrupted_after_forecast_write", "--view", "state")
    require(campaign_resume_state["sourceKind"] == "simulated_interrupted_campaign_state", "interrupted resume source kind drifted")
    require(campaign_resume_state["localRunStateCount"] == 1, "interrupted resume should find one run state")
    require(campaign_resume_state["priorEvidenceOverwriteAllowed"] is False, "interrupted resume must not allow overwrite")

    campaign_append_ready = run_cli("prediction-campaign", "append-ready")
    require(campaign_append_ready["ledgerStatus"] == "checked_exclusion_append_ready", "append-ready ledger status drifted")
    require(campaign_append_ready["summary"]["excludedRowCount"] == 1, "append-ready should expose one exclusion row")
    require(campaign_append_ready["executionBoundary"]["writesIgnoredLiveState"] is False, "append-ready must stay dry-run")
    campaign_append_summary = run_cli("prediction-campaign", "append", "--ledger-case", "comparable_scored", "--view", "summary")
    require(campaign_append_summary["comparableRowCount"] == 1, "append dry-run should expose one comparable row")
    require(campaign_append_summary["writesIgnoredLiveState"] is False, "append dry-run must not write ignored state")

    adapter = run_cli("private-setup-orchestrator", "--case", "source_adapter_output_accepted")
    require(adapter["orchestratorStatus"] == "ready_for_forecast_execution", "accepted adapter path should stop before forecast execution")
    require(adapter["forecastId"] is None, "accepted adapter path must not invent forecast artifacts")
    require(adapter["nextAction"] == "run_explicit_setup_forecast_execution", "accepted adapter path should route to explicit forecast execution")

    blocked_expectations = {
        "missing_approval": ("missing_approval", "confirm_approval"),
        "unconfirmed_mapping": ("needs_confirmation", "confirm_mapping"),
        "unsafe_source": ("blocked_unsafe", "stop_unsafe_connector"),
        "response_too_large": ("response_too_large", "retry_with_smaller_readback"),
    }
    for case, (status, next_action) in blocked_expectations.items():
        run = run_cli("private-setup-orchestrator", "--case", case)
        require(run["orchestratorStatus"] == status, f"{case} status drifted")
        require(run["nextAction"] == next_action, f"{case} next action drifted")
        require(run["forecastArtifactsPresent"] is False, f"{case} must not create forecast artifacts")
        require(run["forecastId"] is None, f"{case} must not bind a forecast")

    forecast_run = run_cli("forecast-run")
    require(forecast_run["runStatus"] == "completed", "MVP forecast-run should complete")
    require(forecast_run["recordBinding"]["forecastId"] == "forecast-602", "MVP forecast-run forecast binding drifted")
    require(forecast_run["state"]["scoreStatus"] == "scored", "MVP forecast-run should expose scored state")
    require(forecast_run["qualityClaim"]["status"] == "not_enough_resolved_auto_evidence_outcomes", "MVP forecast-run must keep quality provisional")

    envelope = run_cli(
        "agent-call",
        "--operation",
        "forecast_card",
        "--forecast-id",
        "forecast-1102",
        "--question-id",
        "question-1102",
    )
    require(envelope["status"] == "ok", "MVP agent-call forecast card should return ok")
    require(envelope["exitCode"] == 0, "MVP agent-call forecast card should return exit code 0")
    require(envelope["recordBinding"]["forecastId"] == "forecast-1102", "MVP agent-call forecast binding drifted")

    protocol_map = run_cli("agent-protocol-map")
    require(protocol_map["adapterContract"]["mcpCommand"] == "python3 scripts/ope.py mcp-stdio", "MVP MCP command drifted")
    require(protocol_map["adapterContract"]["mcpStdioScaffoldImplemented"] is True, "MVP MCP scaffold should be implemented")
    require(protocol_map["adapterContract"]["httpRuntimeImplemented"] is False, "MVP must not claim HTTP runtime")
    require(protocol_map["adapterContract"]["queueRuntimeImplemented"] is False, "MVP must not claim queue runtime")

    resolution_jobs = run_cli("resolution-jobs")
    require(resolution_jobs["summary"]["pendingDueCount"] == 1, "MVP resolution jobs should expose one due fixture job")
    require(resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "MVP resolution jobs must not execute resolvers")

    campaign_resolution_jobs = run_cli("resolution-jobs", "--campaign", "predictioncampaign-001")
    campaign_jobs = [
        job for job in campaign_resolution_jobs["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    require(campaign_resolution_jobs["registryMode"] == "campaign_fixture_registry", "campaign resolution jobs mode drifted")
    require(len(campaign_jobs) == 1, "campaign resolution jobs should expose one campaign job")
    require(campaign_jobs[0]["target"]["forecastId"] == "forecast-1301", "campaign resolution job forecast binding drifted")
    require(campaign_jobs[0]["agentAction"]["recommendedAction"] == "wait", "campaign resolution job should tell agents to wait")
    require(campaign_resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "campaign resolution jobs must not execute resolvers")

    due_campaign_resolution_jobs = run_cli(
        "resolution-jobs",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_jobs = [
        job for job in due_campaign_resolution_jobs["jobs"]
        if job["target"].get("campaignId") == "predictioncampaign-001"
    ]
    require(due_campaign_jobs[0]["agentAction"]["recommendedAction"] == "call_campaign_resolver_attempt", "due campaign job should route to resolver attempt")
    require(due_campaign_resolution_jobs["executionBoundary"]["registryExecutesResolvers"] is False, "due campaign resolution jobs must not execute resolvers")

    campaign_scheduler = run_cli("resolution-scheduler", "--campaign", "predictioncampaign-001")
    campaign_actions = [
        action for action in campaign_scheduler["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    require(campaign_scheduler["schedulerMode"] == "campaign_fixture_once", "campaign scheduler mode drifted")
    require(len(campaign_actions) == 1, "campaign scheduler should expose one campaign action")
    require(campaign_actions[0]["schedulerAction"] == "wait_until_due", "campaign scheduler should wait until due")
    require(campaign_scheduler["executionMode"] == "dry_run", "campaign scheduler fixture should stay dry-run")
    require(campaign_scheduler["executionBoundary"]["hostedSchedulerCreated"] is False, "campaign scheduler must not create hosted schedulers")

    due_campaign_scheduler = run_cli(
        "resolution-scheduler",
        "--campaign",
        "predictioncampaign-001",
        "--now",
        "2026-06-11T07:15:00Z",
    )
    due_campaign_actions = [
        action for action in due_campaign_scheduler["ticks"][0]["actions"]
        if action["statePath"].startswith(".ope/live/prediction-campaigns/")
    ]
    require(due_campaign_actions[0]["schedulerAction"] == "campaign_resolver_attempt_ready", "due campaign scheduler action drifted")
    require(due_campaign_scheduler["ticks"][0]["resolverSummary"]["ranResolver"] is False, "due campaign scheduler must not run resolvers")

    track_gate = run_cli("transit-track-record-gate")
    require(track_gate["claimBoundary"]["qualityClaimAllowed"] is False, "MVP transit gate must block quality claims")
    require(track_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "MVP transit gate must block calibration claims")
    require(track_gate["calibrationGate"]["summaryGenerated"] is False, "MVP transit gate must not generate calibration below threshold")
    campaign_track_gate = run_cli("transit-track-record-gate", "--campaign", "predictioncampaign-001")
    require(campaign_track_gate["campaignLedger"]["included"] is True, "MVP transit gate should include explicit campaign ledger")
    require(campaign_track_gate["sampleSummary"]["excludedSampleSize"] == 7, "campaign ledger should add excluded audit rows")
    campaign_comparable_gate = run_cli(
        "transit-track-record-gate",
        "--campaign",
        "predictioncampaign-001",
        "--ledger-case",
        "comparable_scored",
    )
    require(campaign_comparable_gate["sampleSummary"]["resolvedComparableSampleSize"] == 2, "campaign comparable ledger should add sample")
    require(campaign_comparable_gate["claimBoundary"]["calibrationClaimAllowed"] is False, "campaign ledger must not unlock calibration below threshold")
    campaign_calibration = run_cli("prediction-campaign", "calibration-status")
    require(
        campaign_calibration["calibrationStatus"] == "not_enough_resolved_comparable_outcomes",
        "campaign calibration default should stay below threshold",
    )
    require(campaign_calibration["calibrationReadback"]["summaryGenerated"] is False, "below-threshold calibration must not summarize")
    campaign_restart = run_cli(
        "prediction-campaign",
        "calibration-status",
        "--calibration-case",
        "post_calibration_restart",
        "--view",
        "cycle",
    )
    require(campaign_restart["postCalibrationAction"] == "pause_then_resume_after", "post-calibration restart action drifted")
    require(campaign_restart["writesCampaignState"] is False, "post-calibration restart readback must not mutate state")
    campaign_method_gate = run_cli("prediction-campaign", "method-update-gate")
    require(
        campaign_method_gate["gateStatus"] == "blocked_insufficient_calibration_evidence",
        "campaign method-update gate default should stay below threshold",
    )
    require(
        campaign_method_gate["decision"]["effectfulUpdateAllowedNow"] is False,
        "campaign method-update gate must not allow effectful updates",
    )
    require(
        campaign_method_gate["executionBoundary"]["changesForecastMethod"] is False,
        "campaign method-update gate must not change forecast methods",
    )
    campaign_method_plan = run_cli("prediction-campaign", "method-update-plan")
    require(
        campaign_method_plan["planStatus"] == "blocked_by_method_update_gate",
        "campaign method-update plan default should be gate-blocked",
    )
    require(
        campaign_method_plan["decision"]["effectfulUpdateAllowedNow"] is False,
        "campaign method-update plan must not allow effectful updates",
    )
    require(
        campaign_method_plan["futureEffectfulCommand"]["implementedNow"] is True,
        "campaign method-update plan should expose the guarded effectful command",
    )
    campaign_method_apply = run_cli("prediction-campaign", "apply-method-update")
    require(
        campaign_method_apply["actionStatus"] == "blocked_by_method_update_plan",
        "campaign method-update apply default should be plan-blocked",
    )
    require(
        campaign_method_apply["executionBoundary"]["writesMethodBinding"] is False,
        "campaign method-update apply dry run must not write method bindings",
    )
    campaign_explain = run_cli("prediction-campaign", "explain")
    require(campaign_explain["predictionCampaignExplainId"] == "predictioncampaignexplain-001", "campaign explain ID drifted")
    require(campaign_explain["campaignSnapshot"]["nextForecastId"] == "forecast-1301", "campaign explain next forecast drifted")
    require(campaign_explain["claimBoundary"]["qualityClaimAllowed"] is False, "campaign explain must block quality claims")
    require(campaign_explain["summary"]["agentAdapterReadbacksImplemented"] is True, "campaign explain should expose adapter readbacks")
    campaign_pilot_runbook = run_cli("prediction-campaign", "pilot-runbook")
    require(
        campaign_pilot_runbook["pilotScope"]["targetRunCount"] == 100,
        "campaign pilot runbook target count drifted",
    )
    require(
        campaign_pilot_runbook["miniCampaignSmoke"]["runCount"] == 3,
        "campaign pilot runbook mini smoke count drifted",
    )
    require(
        campaign_pilot_runbook["summary"]["bestAvailableMethodId"] == "transitmethod-100",
        "campaign pilot runbook best method drifted",
    )
    require(
        campaign_pilot_runbook["executionBoundary"]["normalChecksWriteLiveState"] is False,
        "campaign pilot runbook must not write local state",
    )
    campaign_pilot_readiness = run_cli("prediction-campaign", "pilot-readiness")
    require(
        campaign_pilot_readiness["readinessStatus"] == "checked_ready_for_operator_launch",
        "campaign pilot readiness status drifted",
    )
    require(
        campaign_pilot_readiness["summary"]["checkedPrerequisitesPassed"] is True,
        "campaign pilot readiness checked prerequisites should pass",
    )
    require(
        campaign_pilot_readiness["executionBoundary"]["startsPilot"] is False,
        "campaign pilot readiness must not start the pilot",
    )
    campaign_agent = run_cli("agent-call", "--operation", "campaign_status")
    require(campaign_agent["status"] == "ok", "campaign status agent-call should return ok")
    require(campaign_agent["payload"]["campaignSnapshot"]["nextForecastId"] == "forecast-1301", "campaign status agent-call next forecast drifted")
    require(campaign_agent["payload"]["executionBoundary"]["createsForecastArtifacts"] is False, "campaign status agent-call must not create artifacts")

    database_agent = run_cli("agent-call", "--operation", "database_source_adapter_runtime_status")
    require(database_agent["status"] == "ok", "database runtime agent-call should return ok")
    require(database_agent["payload"]["summary"]["approvedExecutionPathCount"] == 1, "database runtime agent-call approved path count drifted")
    require(database_agent["payload"]["executionBoundary"]["normalChecksConnectToDatabase"] is False, "database runtime agent-call must stay offline")
    require(database_agent["payload"]["executionBoundary"]["credentialValuesStored"] is False, "database runtime agent-call must not store credentials")

    print("checked MVP release surface")


if __name__ == "__main__":
    main()
