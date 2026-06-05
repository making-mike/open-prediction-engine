#!/usr/bin/env python3
"""Check runtime security and hardening readback invariants."""

from __future__ import annotations

try:
    from generate_runtime_security import build_runtime_security
except ModuleNotFoundError as exc:  # pragma: no cover - red phase until the generator exists
    raise AssertionError("runtime security generator is missing") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    security = build_runtime_security()

    require(security["securityStatus"] == "lightweight_runtime_hardening_checked", "security status drifted")
    require(security["runtimeScope"] == "embedded_local_runtime", "runtime scope drifted")

    dependency = security["dependencyBudget"]
    require(dependency["coreRuntimeDependencyPolicy"] == "python_stdlib_only", "core runtime should stay stdlib-only")
    require(dependency["thirdPartyRuntimeDependenciesAllowed"] is False, "third-party runtime deps should stay blocked")
    require(dependency["packageInstallRequiredForNormalChecks"] is False, "normal checks should not require install")
    require({"ruff", "mypy"}.issubset(set(dependency["devOnlyDependencies"])), "dev-only static tools drifted")
    require("python_standard_library" in dependency["allowedRuntimeDependencyGroups"], "stdlib budget missing")

    modules = {item["moduleName"]: item for item in security["moduleBoundaries"]}
    expected_modules = {
        "core_lifecycle",
        "storage_adapter",
        "source_adapter",
        "method_adapter",
        "transport_adapter",
        "worker_runtime",
        "domain_source_setup",
    }
    require(set(modules) == expected_modules, "module-boundary coverage drifted")
    for module in modules.values():
        require(module["singleResponsibility"] is True, f"{module['moduleName']} should have one clear responsibility")
        require(module["rawSqlExposed"] is False, f"{module['moduleName']} must not expose raw SQL")
        require(module["credentialValuesAccepted"] is False, f"{module['moduleName']} must not accept credential values")
        require(module["hiddenServiceRequired"] is False, f"{module['moduleName']} must not require hidden services")
        require(module["adapterBoundaryDocumented"] is True, f"{module['moduleName']} boundary should be documented")

    surfaces = {item["surfaceName"]: item for item in security["runtimeSurfaceControls"]}
    expected_surfaces = {
        "embedded_internal_api",
        "local_sqlite_storage_adapter",
        "background_worker_runtime",
        "local_source_runtime",
        "domain_source_setup",
    }
    require(set(surfaces) == expected_surfaces, "runtime surface coverage drifted")
    for surface in surfaces.values():
        require(surface["pathAllowlistRequired"] is True, f"{surface['surfaceName']} should require path allow-listing")
        require(surface["symlinkEscapeCheckRequired"] is True, f"{surface['surfaceName']} should require symlink checks")
        require(surface["databasePathCheckRequired"] is True, f"{surface['surfaceName']} should require database path checks")
        require(surface["responseSizeLimitBytes"] <= 65536, f"{surface['surfaceName']} response budget is too large")
        require(surface["inputSizeLimitBytes"] <= 262144, f"{surface['surfaceName']} input budget is too large")
        require(surface["sanitizedDiagnosticsRequired"] is True, f"{surface['surfaceName']} diagnostics should be sanitized")
        require(surface["credentialReferenceOnly"] is True, f"{surface['surfaceName']} should use credential refs only")
        require(surface["credentialValuesStored"] is False, f"{surface['surfaceName']} must not store credential values")
        require(surface["networkAccessDefault"] == "disabled", f"{surface['surfaceName']} should disable network by default")

    path_guards = security["pathAndDatabaseGuards"]
    require(path_guards["pathTraversalBlocked"] is True, "path traversal should be blocked")
    require(path_guards["symlinkEscapeBlocked"] is True, "symlink escapes should be blocked")
    require(path_guards["absolutePathRequiresApproval"] is True, "absolute paths should require approval")
    require(path_guards["databasePathAllowlistRequired"] is True, "database path allow-list should be required")
    require(path_guards["persistentDatabaseDefaultAllowed"] is False, "persistent DB should not be default")
    require(".ope/state" in path_guards["allowedLocalStateRoots"], "local state allow-list should include .ope/state")

    credentials = security["credentialHandling"]
    require(credentials["credentialValuesStoredInRecords"] is False, "records must not store credential values")
    require(credentials["credentialReferencesAllowed"] is True, "credential references should be allowed")
    require(credentials["redactionReceiptRequiredForUnsafeFields"] is True, "unsafe fields should use redaction receipts")
    require(credentials["sourcePolicyIdRequired"] is True, "source policy ids should be required")
    require(credentials["sanitizedProvenanceRequired"] is True, "sanitized provenance should be required")
    require(credentials["environmentSecretEchoAllowed"] is False, "environment secret echo should stay blocked")

    threats = {item["threatName"]: item for item in security["threatModelNotes"]}
    expected_threats = {
        "malicious_source_data",
        "prompt_source_injection",
        "path_traversal",
        "idempotency_replay",
        "lease_abuse",
        "oversized_responses",
        "accidental_private_data_exposure",
    }
    require(set(threats) == expected_threats, "threat model coverage drifted")
    for threat in threats.values():
        require(threat["mitigationStatus"] == "checked_or_bounded", f"{threat['threatName']} mitigation drifted")
        require(threat["rawSensitiveDataExposed"] is False, f"{threat['threatName']} should not expose raw sensitive data")
        require(threat["checkedBy"], f"{threat['threatName']} should list checks")

    checks = {item["command"] for item in security["agentReadableChecks"]}
    require("python3 scripts/check_runtime_security.py" in checks, "runtime security check command missing")
    require("python3 scripts/check_hardening.py" in checks, "general hardening check command missing")
    require("python3 scripts/ope.py runtime-security --check" in checks, "CLI runtime-security check missing")

    blocked = {item["caseName"]: item for item in security["blockedExamples"]}
    for case_name in ["path_traversal", "symlink_escape", "database_outside_allowlist", "oversized_response", "credential_value_in_record"]:
        require(case_name in blocked, f"blocked example {case_name} missing")
        require(blocked[case_name]["blocked"] is True, f"{case_name} should be blocked")
        require(blocked[case_name]["sanitizedDiagnosticCode"], f"{case_name} should expose sanitized diagnostics")
        require(blocked[case_name]["rawValueEchoed"] is False, f"{case_name} must not echo raw values")

    summary = security["summary"]
    require(summary["runtimeDependencyCount"] == 0, "runtime dependency count should stay zero")
    require(summary["moduleBoundaryCount"] == len(expected_modules), "module boundary count drifted")
    require(summary["surfaceControlCount"] == len(expected_surfaces), "surface control count drifted")
    require(summary["threatModelNoteCount"] == len(expected_threats), "threat model count drifted")
    require(summary["blockedExampleCount"] == 5, "blocked example count drifted")
    require(summary["normalChecksStartHiddenService"] is False, "normal checks must not start hidden services")

    boundary = security["executionBoundary"]
    for key in [
        "hostedRuntimeRequired",
        "networkListenerStarted",
        "liveSourceFetchDefault",
        "credentialValuesStored",
        "rawSqlExposed",
        "rawFileLayoutExposed",
        "unboundedBackgroundLoopAllowed",
        "physicalDeleteAllowed",
    ]:
        require(boundary[key] is False, f"execution boundary {key} should stay false")

    print("checked runtime security hardening")


if __name__ == "__main__":
    main()
