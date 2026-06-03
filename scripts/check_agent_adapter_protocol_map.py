#!/usr/bin/env python3
"""Check agent adapter protocol-map invariants."""

from __future__ import annotations

from generate_agent_adapter_protocol_map import ENVELOPE_SCHEMA, OPERATIONS, build_protocol_map


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    protocol_map = build_protocol_map()
    require(
        protocol_map["adapterContract"]["runtimeStatus"] == "local_mcp_stdio_scaffold",
        "protocol map should advertise the local MCP stdio scaffold",
    )
    require(
        protocol_map["adapterContract"]["localDispatcherImplemented"] is True,
        "local dispatcher should be marked implemented",
    )
    require(
        protocol_map["adapterContract"]["protocolRuntimeImplemented"] is True,
        "protocol runtime flag should reflect local MCP stdio support",
    )
    require(
        protocol_map["adapterContract"]["mcpStdioScaffoldImplemented"] is True,
        "MCP stdio scaffold should be marked implemented",
    )
    require(
        protocol_map["adapterContract"]["httpRuntimeImplemented"] is False,
        "HTTP runtime should remain unimplemented",
    )
    require(
        protocol_map["adapterContract"]["queueRuntimeImplemented"] is False,
        "queue runtime should remain unimplemented",
    )

    operations = {item["operation"]: item for item in protocol_map["operations"]}
    require(set(operations) == set(OPERATIONS), "protocol map should cover every agent operation exactly once")
    for operation, item in operations.items():
        require(item["outputEnvelopeSchema"] == ENVELOPE_SCHEMA, f"{operation} should return the agent envelope schema")
        require(item["localCli"]["implemented"] is True, f"{operation} should have an implemented local CLI mapping")
        require(
            item["localCli"]["exitCodeSource"] == "agentEnvelope.exitCode",
            f"{operation} should preserve envelope exit codes",
        )
        require(item["mcp"]["implemented"] is True, f"{operation} should expose MCP stdio scaffold support")
        require(item["http"]["implemented"] is False, f"{operation} must not claim HTTP runtime support")
        require(item["queue"]["implemented"] is False, f"{operation} must not claim queue runtime support")
        require(
            item["mcp"]["toolName"] == f"ope_{operation}",
            f"{operation} should have a deterministic MCP tool name",
        )
        require(
            item["queue"]["requestMessageType"] == f"ope.{operation}.requested",
            f"{operation} should have a deterministic queue message type",
        )
        require(
            item["queue"]["resultMessageType"] == "ope.agent_envelope.ready",
            f"{operation} queue result should be an agent envelope",
        )
        for transport in ["mcp", "http", "queue"]:
            boundary = item[transport]["credentialBoundary"]
            require("secret" not in boundary.lower(), f"{operation} {transport} boundary should avoid secret material")
            require("argument" in boundary.lower() or "payload" in boundary.lower(), f"{operation} {transport} boundary should name prompt-visible boundaries")

    evidence_plan = operations["evidence_plan"]
    require(evidence_plan["requiresApproval"] is True, "evidence plan should remain approval-aware")
    require(
        evidence_plan["sideEffectLevel"] == "dry_run_generation",
        "evidence plan should be dry-run generation, not live fetching",
    )
    for operation in [
        "evidence_trace",
        "forecast_card",
        "lifecycle_bundle",
        "private_setup_bundle",
        "private_setup_adapter_runbook",
        "private_setup_adapter_conformance_summary",
        "private_source_adapter_guidance",
        "private_source_kind_selection",
        "campaign_plan",
        "campaign_status",
        "campaign_health",
        "campaign_append_readiness",
        "campaign_calibration_status",
        "internal_api",
        "resolution_jobs",
        "resolution_scheduler_status",
        "resolution_status",
        "scoring_summary",
    ]:
        require(operations[operation]["requiresApproval"] is False, f"{operation} should be read/status-only")
    internal_api = operations["internal_api"]
    require(
        internal_api["sideEffectLevel"] == "dry_run_generation",
        "internal API wrapper should be a dry-run generation adapter",
    )
    require(
        internal_api["inputRecordType"] == "internal_api_request",
        "internal API wrapper should bind internal API request records",
    )
    internal_fields = {item["name"]: item for item in internal_api["inputFields"]}
    require("internalOperation" in internal_fields, "internal API wrapper should expose internalOperation")
    require("predictionId" in internal_fields, "internal API wrapper should expose predictionId")
    require("idempotencyKey" in internal_fields, "internal API wrapper should expose idempotencyKey")
    require(
        "non-mutating dry-run mode" in internal_api["usageGuidance"],
        "internal API wrapper guidance should preserve dry-run semantics",
    )
    adapter_runbook = operations["private_setup_adapter_runbook"]
    require(
        adapter_runbook["sideEffectLevel"] == "read_only",
        "adapter-runbook operation should be read-only guidance",
    )
    require(
        adapter_runbook["inputRecordType"] == "private_setup_adapter_chain_runbook",
        "adapter-runbook operation should return the checked runbook record type",
    )
    require(
        len(adapter_runbook["inputFields"]) == 2,
        "adapter-runbook operation should expose only maxBytes and callerIntent",
    )
    require(
        "without executing adapter calls" in adapter_runbook["usageGuidance"],
        "adapter-runbook guidance should preserve the non-execution boundary",
    )
    adapter_conformance_summary = operations["private_setup_adapter_conformance_summary"]
    require(
        adapter_conformance_summary["sideEffectLevel"] == "read_only",
        "adapter conformance summary should be read-only",
    )
    require(
        adapter_conformance_summary["inputRecordType"] == "private_setup_adapter_conformance_summary",
        "adapter conformance summary should bind compact summary records",
    )
    require(
        len(adapter_conformance_summary["inputFields"]) == 2,
        "adapter conformance summary should expose only maxBytes and callerIntent",
    )
    require(
        "without loading the full embedded-envelope matrix" in adapter_conformance_summary["usageGuidance"],
        "adapter conformance summary guidance should preserve the compact boundary",
    )
    source_guidance = operations["private_source_adapter_guidance"]
    require(
        source_guidance["sideEffectLevel"] == "read_only",
        "private source adapter guidance should be read-only",
    )
    require(
        source_guidance["inputRecordType"] == "private_source_adapter_capability",
        "private source adapter guidance should bind capability records",
    )
    require(
        len(source_guidance["inputFields"]) == 2,
        "private source adapter guidance should expose only maxBytes and callerIntent",
    )
    require(
        "without executing source reads" in source_guidance["usageGuidance"],
        "private source adapter guidance should preserve the non-execution boundary",
    )
    source_selection = operations["private_source_kind_selection"]
    require(
        source_selection["sideEffectLevel"] == "read_only",
        "private source-kind selection should be read-only",
    )
    require(
        source_selection["inputRecordType"] == "private_source_kind_selection_examples",
        "private source-kind selection should bind selection example records",
    )
    require(
        len(source_selection["inputFields"]) == 3,
        "private source-kind selection should expose sourceKind plus maxBytes and callerIntent",
    )
    source_selection_fields = {item["name"]: item for item in source_selection["inputFields"]}
    require(
        source_selection_fields["sourceKind"]["type"] == "string",
        "private source-kind selection sourceKind should be a string query argument",
    )
    require(
        "selected example" in source_selection_fields["sourceKind"]["notes"],
        "private source-kind selection sourceKind notes should describe the compact selected response",
    )
    require(
        "without executing source setup" in source_selection["usageGuidance"],
        "private source-kind selection should preserve the non-execution boundary",
    )
    for operation, record_type in {
        "campaign_plan": "prediction_campaign_manifest",
        "campaign_status": "prediction_campaign_explain",
        "campaign_health": "prediction_campaign_doctor",
        "campaign_append_readiness": "prediction_campaign_evidence_ledger",
        "campaign_calibration_status": "prediction_campaign_calibration_status",
    }.items():
        item = operations[operation]
        require(item["sideEffectLevel"] == "read_only", f"{operation} should be read-only")
        require(item["inputRecordType"] == record_type, f"{operation} input record type drifted")
        require(len(item["inputFields"]) == 2, f"{operation} should expose only maxBytes and callerIntent")
        require(item["requiresApproval"] is False, f"{operation} should be approval-free readback")
        require("without" in item["usageGuidance"], f"{operation} should name its non-execution boundary")
    source_builder = operations["private_setup_source_builder"]
    require(source_builder["requiresApproval"] is True, "source-builder adapter should require caller-approved paths")
    require(
        source_builder["sideEffectLevel"] == "dry_run_generation",
        "source-builder adapter should be draft generation, not forecast execution",
    )
    source_builder_fields = {item["name"]: item for item in source_builder["inputFields"]}
    require("sourceBuilderInputs" in source_builder_fields, "source-builder adapter should expose explicit source inputs")
    require(
        source_builder_fields["sourceBuilderInputs"]["type"] == "string-list",
        "source-builder inputs should be an explicit list of approved paths",
    )
    source_handoff = operations["private_setup_source_handoff"]
    require(source_handoff["requiresApproval"] is True, "source-handoff adapter should preserve confirmation gates")
    require(
        source_handoff["sideEffectLevel"] == "dry_run_generation",
        "source-handoff adapter should be next-action guidance, not forecast execution",
    )
    source_handoff_fields = {item["name"]: item for item in source_handoff["inputFields"]}
    require("sourceHandoffCase" in source_handoff_fields, "source-handoff adapter should expose checked handoff cases")
    require(
        "raw private data" in source_handoff_fields["sourceHandoffCase"]["notes"],
        "source-handoff case notes should prohibit raw private data",
    )
    method_gate = operations["private_setup_method_gate"]
    require(method_gate["requiresApproval"] is True, "method-gate adapter should preserve benchmark and method gates")
    require(
        method_gate["sideEffectLevel"] == "dry_run_generation",
        "method-gate adapter should be next-action guidance, not forecast execution",
    )
    method_gate_fields = {item["name"]: item for item in method_gate["inputFields"]}
    require("methodGateCase" in method_gate_fields, "method-gate adapter should expose checked method-gate cases")
    require(
        "raw private data" in method_gate_fields["methodGateCase"]["notes"],
        "method-gate case notes should prohibit raw private data",
    )
    forecast_execution = operations["private_setup_forecast_execution"]
    require(
        forecast_execution["requiresApproval"] is True,
        "forecast-execution adapter should preserve explicit execution approval",
    )
    require(
        forecast_execution["sideEffectLevel"] == "forecast_execution",
        "forecast-execution adapter should be labeled as forecast execution",
    )
    forecast_execution_fields = {item["name"]: item for item in forecast_execution["inputFields"]}
    require(
        "forecastExecutionCase" in forecast_execution_fields,
        "forecast-execution adapter should expose checked execution cases",
    )
    require(
        "raw private data" in forecast_execution_fields["forecastExecutionCase"]["notes"],
        "forecast-execution case notes should prohibit raw private data",
    )
    require(
        "normal read operations" in forecast_execution["usageGuidance"],
        "forecast-execution guidance should route generated forecasts to normal reads",
    )
    require(
        "generated private setup forecasts" in operations["forecast_card"]["usageGuidance"],
        "forecast-card guidance should cover setup-generated readback",
    )
    resolution_jobs = operations["resolution_jobs"]
    require(
        resolution_jobs["sideEffectLevel"] == "read_only",
        "resolution-jobs operation should be read-only",
    )
    require(
        resolution_jobs["inputRecordType"] == "resolution_job_registry",
        "resolution-jobs operation should bind registry records",
    )
    require(
        len(resolution_jobs["inputFields"]) == 2,
        "resolution-jobs operation should expose only maxBytes and callerIntent",
    )
    require(
        "without reading local state files or executing resolvers" in resolution_jobs["usageGuidance"],
        "resolution-jobs guidance should preserve readback and non-execution boundaries",
    )
    scheduler_status = operations["resolution_scheduler_status"]
    require(
        scheduler_status["sideEffectLevel"] == "read_only",
        "resolution-scheduler-status operation should be read-only",
    )
    require(
        scheduler_status["inputRecordType"] == "resolution_scheduler_status",
        "resolution-scheduler-status operation should bind compact scheduler status records",
    )
    require(
        len(scheduler_status["inputFields"]) == 2,
        "resolution-scheduler-status operation should expose only maxBytes and callerIntent",
    )
    require(
        "without starting a scheduler" in scheduler_status["usageGuidance"],
        "resolution-scheduler-status guidance should preserve non-execution boundaries",
    )

    exit_codes = {item["exitCode"]: item for item in protocol_map["exitCodeMapping"]}
    require(set(exit_codes) == {0, 1, 2, 3, 4, 5}, "exit code mapping should cover 0 through 5")
    require(exit_codes[0]["status"] == "ok", "exit code 0 should be ok")
    require("approval_required" in exit_codes[3]["errorCodes"], "exit code 3 should map approval_required")
    require("response_too_large" in exit_codes[5]["errorCodes"], "exit code 5 should map response_too_large")

    transports = {item["transport"]: item for item in protocol_map["transportBoundaries"]}
    require(transports["local_cli"]["implemented"] is True, "local CLI should be implemented")
    require(transports["mcp"]["implemented"] is True, "MCP stdio scaffold should be implemented")
    for transport in ["http", "queue"]:
        require(transports[transport]["implemented"] is False, f"{transport} should remain mapping-only")
        require("credential" in transports[transport]["credentialBoundary"].lower(), f"{transport} should define credentials")

    examples = {item["preferredOperation"] for item in protocol_map["decisionExamples"]}
    for operation in [
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
        "resolution_jobs",
        "resolution_scheduler_status",
        "resolution_status",
        "scoring_summary",
    ]:
        require(operation in examples, f"decision examples should explain when to use {operation}")
    forecast_execution_examples = [
        item
        for item in protocol_map["decisionExamples"]
        if item["preferredOperation"] == "private_setup_forecast_execution"
    ]
    require(
        any("private setup read API" in item["downstreamRule"] for item in forecast_execution_examples),
        "forecast-execution decision example should reject a private setup read API",
    )

    warnings = " ".join(protocol_map["warnings"]).lower()
    require("http and queue" in warnings and "not implemented" in warnings, "warnings should state HTTP and queue are not implemented")
    require("local scaffold" in warnings, "warnings should describe MCP as a local scaffold")
    require("approval" in warnings, "warnings should preserve approval-gate boundaries")
    require("secrets" in warnings, "warnings should prohibit secrets in protocol-visible records")

    print("checked agent adapter protocol map")


if __name__ == "__main__":
    main()
