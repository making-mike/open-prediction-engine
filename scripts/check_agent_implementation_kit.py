#!/usr/bin/env python3
"""Check agent prediction implementation kit invariants."""

from __future__ import annotations

try:
    from generate_agent_implementation_kit import build_agent_implementation_kit
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until the generator exists
    raise AssertionError("agent implementation kit generator is missing") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    kit = build_agent_implementation_kit()

    require(kit["kitStatus"] == "agent_prediction_implementation_kit_checked", "kit status drifted")
    require(kit["kitScope"] == "local_agent_readback_and_templates", "kit scope drifted")

    quickstart = kit["quickstartFrontDoor"]
    require(quickstart["frontDoorStatus"] == "implementation_follow_up_entrypoint", "quickstart status drifted")
    require(quickstart["entryCommand"] == "python3 scripts/ope.py setup-engine --goal \"add predictions to my app\"", "quickstart command drifted")
    require(quickstart["targetTimeToFirstCommandMinutes"] == 10, "quickstart target time drifted")
    require(quickstart["createsNewForecastPath"] is False, "quickstart must not create a new forecast path")
    require(quickstart["hostedRuntimeRequired"] is False, "quickstart must not require hosted runtime")
    require(quickstart["qualityClaimUpgraded"] is False, "quickstart must not upgrade quality claims")
    quickstart_steps = [item["stepKey"] for item in quickstart["steps"]]
    require(
        quickstart_steps == [
            "start_with_setup_engine",
            "render_host_wrapper_setup_plan",
            "run_guided_forecast",
            "read_forecast_card",
            "inspect_lifecycle_bundle",
        ],
        "quickstart step order drifted",
    )
    require(
        quickstart["steps"][0]["command"] == "python3 scripts/ope.py setup-engine --goal \"add predictions to my app\"",
        "quickstart first step should route through setup-engine",
    )
    require(
        "host_wrapper.py" in quickstart["steps"][1]["command"],
        "quickstart should render setup-first host wrapper",
    )
    require(
        quickstart["steps"][2]["command"] == "python3 scripts/ope.py agent-integrate --run-guided --case accepted_adapter_output",
        "quickstart should route guided forecast through accepted adapter output case",
    )
    require("forecast-1102" in quickstart["steps"][3]["command"], "quickstart should expose forecast-card command")
    require("forecast-bundle" in quickstart["steps"][4]["command"], "quickstart should expose lifecycle-bundle command")

    wrapper = quickstart["copyableWrapper"]
    require(wrapper["wrapperStatus"] == "outline_only_uses_existing_surfaces", "copyable wrapper status drifted")
    require(wrapper["storesCredentialValues"] is False, "copyable wrapper must not store credential values")
    require(wrapper["acceptsRawPrivateRows"] is False, "copyable wrapper must not accept raw private rows")
    require(wrapper["acceptsRawSql"] is False, "copyable wrapper must not accept raw SQL")
    require(wrapper["opensNetworkListener"] is False, "copyable wrapper must not open a network listener")
    require(
        wrapper["callSequence"] == [
            "setup_engine",
            "render_setup_engine_host_wrapper",
            "prediction_feature_setup_response",
            "forecast_card_readback",
            "lifecycle_bundle_readback",
        ],
        "copyable wrapper call sequence drifted",
    )

    manual_steps = {item["stepKey"]: item for item in kit["predictionManual"]["steps"]}
    expected_steps = [
        "detect_decision_under_uncertainty",
        "describe_app_goal",
        "bind_approved_sources",
        "discover_candidate_contracts",
        "validate_candidate_contracts",
        "create_prediction",
        "start_prediction",
        "run_tick_or_worker",
        "read_forecast_card",
        "resolve_outcome",
        "append_evidence_and_score",
        "inspect_calibration",
    ]
    require(list(manual_steps) == expected_steps, "prediction manual step order drifted")
    for step in manual_steps.values():
        require(step["createsForecastArtifacts"] is False or step["stepKey"] == "start_prediction", "only start step may create forecast artifacts")
        require(step["requiresApprovedSources"] is True, f"{step['stepKey']} should require approved source context")
        require(step["claimBoundaryReminder"], f"{step['stepKey']} should include a claim boundary reminder")

    intake = kit["questionDiscoveryIntakeContract"]
    required_fields = {item["fieldName"]: item for item in intake["requiredFields"]}
    for field in [
        "appGoal",
        "decisionToSupport",
        "approvedSourceRefs",
        "sourceRoles",
        "forecastTimeEvidencePolicy",
        "resolutionEvidencePolicy",
        "candidateOutcomeWindows",
        "resolutionSourceHints",
        "safetyImpact",
    ]:
        require(field in required_fields, f"question discovery intake missing {field}")
    require(intake["optionalFields"] == ["existingSetupId", "domainHint", "methodPreferenceHint"], "optional intake fields drifted")
    require(intake["credentialValuesAccepted"] is False, "question discovery intake must not accept credential values")
    require(intake["rawPrivateRowsAccepted"] is False, "question discovery intake must not accept raw private rows")

    candidates = {item["candidateStatus"]: item for item in kit["candidateContractReadbacks"]}
    require(set(candidates) == {"forecastable", "needs_clarification", "blocked", "rejected"}, "candidate status coverage drifted")
    forecastable = candidates["forecastable"]
    require(forecastable["canonicalQuestion"], "forecastable candidate should expose canonical question")
    require(forecastable["outputType"] == "binary", "forecastable candidate output type drifted")
    require(forecastable["baselineFeasible"] is True, "forecastable candidate should have baseline feasibility")
    require(forecastable["sourceReadiness"] == "ready", "forecastable candidate source readiness drifted")
    require(forecastable["routesToExistingSurfaces"] is True, "forecastable candidate should route to existing surfaces")
    require("source-intake" in forecastable["nextSurfaceCommands"], "forecastable candidate should route through source-intake")
    require("setup-method" in forecastable["nextSurfaceCommands"], "forecastable candidate should route through setup-method")
    require(candidates["needs_clarification"]["blockerCode"] == "ambiguous_resolution_window", "clarification blocker drifted")
    require(candidates["blocked"]["blockerCode"] == "source_policy_or_safety_blocker", "blocked candidate drifted")
    require(candidates["rejected"]["blockerCode"] == "post_outcome_or_unresolvable", "rejected candidate drifted")

    validation_reports = {item["candidateStatus"]: item for item in kit["mechanicalValidationReports"]}
    require(set(validation_reports) == set(candidates), "validation report coverage drifted")
    expected_checks = {
        "schema_validity",
        "future_boundary",
        "resolvability",
        "source_policy_binding",
        "leakage_risk",
        "outcome_availability",
        "mapping_confidence",
        "baseline_feasibility",
        "method_eligibility",
        "scoring_readiness",
        "calibration_readiness_boundary",
    }
    for report in validation_reports.values():
        checks = {item["checkName"]: item for item in report["checks"]}
        require(set(checks) == expected_checks, f"{report['candidateStatus']} validation checks drifted")
        require(report["createsForecastArtifacts"] is False, f"{report['candidateStatus']} validation must not create artifacts")
        require(report["rawSourceDataExposed"] is False, f"{report['candidateStatus']} validation must not expose raw source data")

    source_paths = {item["pathKey"]: item for item in kit["firstRunSourcePaths"]}
    require(source_paths["approved_local_files_now"]["immediateAction"] == "run_source_builder", "local files path drifted")
    require(source_paths["sanitized_adapter_output_now"]["immediateAction"] == "run_source_adapter_intake", "adapter output path drifted")
    require(source_paths["database_or_private_api_waits"]["immediateAction"] == "wait_for_checked_runtime", "database/private API path drifted")
    for path in source_paths.values():
        require(path["credentialValuesStored"] is False, f"{path['pathKey']} must not store credential values")

    adapters = {item["adapterName"]: item for item in kit["adapterReadbacks"]}
    require(set(adapters) == {"in_process", "cli", "agent_call", "local_mcp_stdio", "future_http_queue"}, "adapter readback coverage drifted")
    for adapter in adapters.values():
        require(adapter["sharesInternalApiSemantics"] is True, f"{adapter['adapterName']} should share internal API semantics")
        require(adapter["rawSqlExposed"] is False, f"{adapter['adapterName']} must not expose raw SQL")
        require(adapter["hiddenServiceRequired"] is False, f"{adapter['adapterName']} must not require hidden services")
    require(adapters["future_http_queue"]["implementedStatus"] == "future_transport_only", "future transport status drifted")

    forbidden = {item["behaviorKey"]: item for item in kit["doNotImplementGuidance"]}
    for behavior in [
        "free_form_oracle",
        "raw_crud_writes",
        "unbounded_background_loops",
        "silent_deletion",
        "hidden_live_fetches",
        "credential_storage_in_records",
        "automatic_method_upgrades",
    ]:
        require(behavior in forbidden, f"missing do-not-implement guidance for {behavior}")
        require(forbidden[behavior]["allowed"] is False, f"{behavior} must remain disallowed")

    templates = {item["templateKey"]: item for item in kit["starterTemplates"]}
    require(set(templates) == {"embedded_service", "cli_flow", "mcp_host_wrapper"}, "starter template coverage drifted")
    for template in templates.values():
        require(template["createsHostedService"] is False, f"{template['templateKey']} must not create hosted service")
        require(template["storesCredentials"] is False, f"{template['templateKey']} must not store credentials")
        require(template["usesExistingSurfaces"] is True, f"{template['templateKey']} should use existing surfaces")

    conformance = kit["conformanceFixturePack"]
    require(conformance["questionDiscoveryIntakeCount"] == 1, "question discovery intake count drifted")
    require(conformance["candidateReadbackCount"] == 4, "candidate readback count drifted")
    require(conformance["validationReportCount"] == 4, "validation report count drifted")
    require(conformance["blockedPathExampleCount"] >= 4, "blocked path example count drifted")
    require(conformance["normalChecksCreateForecastArtifacts"] is False, "conformance checks must not create forecast artifacts")

    boundary = kit["executionBoundary"]
    for key in [
        "freeFormOracleAllowed",
        "questionDiscoveryCreatesForecastArtifacts",
        "rawCrudWritesAllowed",
        "unboundedBackgroundLoopsAllowed",
        "silentDeletionAllowed",
        "hiddenLiveFetchAllowed",
        "credentialValuesStored",
        "automaticMethodUpgradeAllowed",
        "hostedRuntimeRequired",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    summary = kit["summary"]
    require(summary["quickstartStepCount"] == 5, "quickstart step count drifted")
    require(summary["manualStepCount"] == len(expected_steps), "manual step count drifted")
    require(summary["candidateReadbackCount"] == 4, "candidate count drifted")
    require(summary["validationReportCount"] == 4, "validation report count drifted")
    require(summary["adapterReadbackCount"] == 5, "adapter readback count drifted")
    require(summary["starterTemplateCount"] == 3, "starter template count drifted")

    print("checked agent implementation kit")


if __name__ == "__main__":
    main()
