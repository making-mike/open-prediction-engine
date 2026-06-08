#!/usr/bin/env python3
"""Run lightweight hardening checks for release readiness."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

from read_ope_record import PublicError, render_response, validate_artifact_binding
from validate_forecast_request import validate_request


ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "PRODUCT.md",
    ROOT / "roadmap.md",
    ROOT / "whitepaper.md",
    ROOT / "research",
    ROOT / "spec",
    ROOT / "scripts",
    ROOT / ".agents",
    ROOT / ".github",
]
SECRET_PATTERNS = [
    re.compile(r"OPENAI_API_KEY\s*="),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
]
SCAN_SUFFIXES = {".csv", ".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}


def iter_text_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.suffix in SCAN_SUFFIXES:
                yield child


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_no_secrets() -> None:
    for path in iter_text_files(SCAN_ROOTS):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                rel = path.relative_to(ROOT)
                raise AssertionError(f"potential secret pattern in {rel}")


def assert_malformed_artifact_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "broken-artifact.generated.json"
        evidence = root / "broken-evidence.generated.json"
        artifact.write_text(
            json.dumps(
                {
                    "forecastId": "forecast-999",
                    "questionId": "question-999",
                    "evidencePacketId": "evidence-999",
                }
            ),
            encoding="utf-8",
        )
        evidence.write_text(
            json.dumps(
                {
                    "forecastId": "forecast-998",
                    "questionId": "question-999",
                    "evidencePacketId": "evidence-999",
                }
            ),
            encoding="utf-8",
        )
        try:
            validate_artifact_binding(artifact, load_json(artifact))
        except PublicError as exc:
            if exc.code != "binding_mismatch":
                raise
        else:
            raise AssertionError("malformed artifact/evidence binding should fail")


def assert_oversized_io_fails() -> None:
    try:
        render_response({"record": {"large": "x" * 100}}, max_bytes=20)
    except PublicError as exc:
        if exc.code != "response_too_large":
            raise
    else:
        raise AssertionError("oversized read response should fail")

    request = load_json(ROOT / "spec" / "fixtures" / "requests" / "valid-weather-logistics-request.json")
    request["questionText"] = "Will " + ("very " * 160) + "large request pass?"
    decision = validate_request(request)
    if "oversized_input" not in decision["reasonCodes"]:
        raise AssertionError("oversized request text should be rejected")


def assert_unique_ids(label: str, paths: Iterable[Path], id_field: str) -> None:
    seen: dict[str, Path] = {}
    for path in paths:
        data = load_json(path)
        if id_field not in data:
            continue
        value = data[id_field]
        if value in seen:
            first = seen[value].relative_to(ROOT)
            second = path.relative_to(ROOT)
            raise AssertionError(f"duplicate {label} id {value}: {first} and {second}")
        seen[value] = path


def assert_no_duplicate_records() -> None:
    generated = ROOT / "spec" / "fixtures" / "generated"
    requests = ROOT / "spec" / "fixtures" / "requests"
    benchmarks = ROOT / "spec" / "fixtures" / "benchmark"
    assert_unique_ids("forecast artifact", generated.glob("**/*artifact*.json"), "forecastId")
    assert_unique_ids("track record", generated.glob("**/*track-record*.json"), "trackRecordReportId")
    assert_unique_ids("forecast request", requests.glob("*.json"), "requestId")
    assert_unique_ids("benchmark run", benchmarks.glob("*.json"), "benchmarkRunId")


def assert_aggregate_dependency_review() -> None:
    aggregate = load_json(ROOT / "spec" / "fixtures" / "valid" / "weather-logistics-aggregate-forecast.json")
    included = [item for item in aggregate["includedForecasts"] if item.get("included", True)]
    if len({item["forecastId"] for item in included}) != len(included):
        raise AssertionError("aggregate fixture includes duplicate forecast ids")
    if sum(float(item["weight"]) for item in included) <= 0:
        raise AssertionError("aggregate fixture must have positive included weight")
    source_classes = {item["sourceClass"] for item in included}
    independence = aggregate["dependencyAssessment"]["independenceLevel"]
    if {"baseline", "model"}.issubset(source_classes) and independence == "high":
        raise AssertionError("baseline/model aggregate must not claim high independence")


def assert_claim_review_exists() -> None:
    checklist = ROOT / "spec" / "claim-review.md"
    text = checklist.read_text(encoding="utf-8")
    required = ["sample size", "baseline-lift", "fixture", "provisional live"]
    for phrase in required:
        if phrase not in text:
            raise AssertionError(f"claim review checklist missing {phrase!r}")


def assert_adapter_read_surface_size_guards() -> None:
    generated = ROOT / "spec" / "fixtures" / "generated" / "private-setup-adapter-conformance"
    summary_path = generated / "ope-private-setup-adapter-conformance-summary.generated.json"
    matrix_path = generated / "ope-private-setup-adapter-conformance-matrix.generated.json"
    summary = load_json(summary_path)
    budget = summary["sizeBudget"]
    if "operationCases" in summary or "envelopes" in summary:
        raise AssertionError("compact adapter conformance summary must not embed matrix rows or envelopes")
    if summary_path.stat().st_size > budget["compactSummaryPayloadMaxBytes"]:
        raise AssertionError("compact adapter conformance summary exceeds payload budget")
    if matrix_path.stat().st_size <= summary_path.stat().st_size * 10:
        raise AssertionError("full adapter conformance matrix should remain opt-in and much larger than summary")
    if matrix_path.stat().st_size > budget["fullMatrixReferenceMaxBytes"]:
        raise AssertionError("full adapter conformance matrix exceeds reference budget")
    if budget["fullMatrixRequiresExplicitCommand"] is not True:
        raise AssertionError("full adapter conformance matrix should require an explicit command")
    if budget["oversizedAdapterErrorCode"] != "response_too_large":
        raise AssertionError("adapter conformance summary must use the standard size-limit error code")


def assert_runtime_security_contract() -> None:
    path = ROOT / "spec" / "fixtures" / "generated" / "runtime-security" / "ope-runtime-security.generated.json"
    security = load_json(path)
    if security["dependencyBudget"]["runtimeDependencyCount"] != 0:
        raise AssertionError("runtime security should keep runtime dependency count at zero")
    if security["dependencyBudget"]["thirdPartyRuntimeDependenciesAllowed"] is not False:
        raise AssertionError("runtime security should block third-party runtime dependencies")
    if any(surface["credentialValuesStored"] for surface in security["runtimeSurfaceControls"]):
        raise AssertionError("runtime security surfaces must not store credential values")
    if any(surface["responseSizeLimitBytes"] > 65536 for surface in security["runtimeSurfaceControls"]):
        raise AssertionError("runtime security response limits should stay compact")
    boundary = security["executionBoundary"]
    for key in ["hostedRuntimeRequired", "networkListenerStarted", "liveSourceFetchDefault", "credentialValuesStored"]:
        if boundary[key] is not False:
            raise AssertionError(f"runtime security boundary {key} should stay false")


def assert_database_source_adapter_runtime_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "database-source-adapter-runtime"
        / "ope-database-source-adapter-runtime.generated.json"
    )
    runtime = load_json(path)
    boundary = runtime["executionBoundary"]
    for key in [
        "productionDatabaseConnectionOpened",
        "normalChecksConnectToDatabase",
        "credentialValuesStored",
        "rawSqlWithSecretsAccepted",
        "rawPrivateRowsStored",
        "stackTracesExposed",
        "unapprovedSchemaScansAllowed",
        "arbitraryDatabaseAccessAllowed",
        "forecastArtifactsCreated",
        "scoringRecordsCreated",
        "hostedRuntimeRequired",
    ]:
        if boundary[key] is not False:
            raise AssertionError(f"database runtime boundary {key} should stay false")
    cases = runtime["runtimeCases"]
    approved = cases[0]
    output = approved["sanitizedAdapterOutput"]
    if output["provenanceSummary"]["credentialValuesIncluded"] is not False:
        raise AssertionError("approved database runtime output must not include credential values")
    if output["provenanceSummary"]["rawRowsIncluded"] is not False:
        raise AssertionError("approved database runtime output must not include raw private rows")
    if output["queryBoundarySummary"]["rawSqlWithSecretsIncluded"] is not False:
        raise AssertionError("approved database runtime output must not include raw SQL with secrets")
    for case in cases[1:]:
        if case["canEnterSourceAdapterIntake"] is not False:
            raise AssertionError("blocked database runtime cases must stop before source-adapter intake")
        if case["forecastArtifactsCreated"] is not False:
            raise AssertionError("blocked database runtime cases must not create forecast artifacts")
        if case["rawPrivateRowsStored"] is not False:
            raise AssertionError("blocked database runtime cases must not store raw private rows")
        if case["credentialValuesStored"] is not False:
            raise AssertionError("blocked database runtime cases must not store credentials")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("blocked database runtime cases should keep diagnostics sanitized")


def assert_opp_provider_adapter_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "opp-provider-adapter"
        / "ope-opp-provider-adapter.generated.json"
    )
    adapter = load_json(path)
    if adapter["httpProviderRuntimeImplemented"] is not False:
        raise AssertionError("OPP provider adapter must not claim HTTP runtime implementation")
    if adapter["sseStreamingImplemented"] is not False:
        raise AssertionError("OPP provider adapter must not claim SSE implementation")
    if adapter["paymentSettlementImplemented"] is not False:
        raise AssertionError("OPP provider adapter must not claim payment settlement")
    if adapter["aggregationImplemented"] is not False:
        raise AssertionError("OPP provider adapter must not claim aggregation")
    if adapter["hostedServiceRequired"] is not False:
        raise AssertionError("OPP provider adapter must not require a hosted service")
    boundary = adapter["protocolBoundary"]
    for key in [
        "oppReplacesOpeLifecycleRecords",
        "httpRuntimeImplemented",
        "sseRuntimeImplemented",
        "paymentSettlementImplemented",
        "aggregationRuntimeImplemented",
        "hostedServiceImplemented",
        "networkListenerStarted",
        "normalChecksUseNetwork",
        "rawLifecycleBundleEmbeddedByDefault",
        "qualityClaimsUpgraded",
    ]:
        if boundary[key] is not False:
            raise AssertionError(f"OPP provider adapter boundary {key} should stay false")
    if adapter["responseMapping"]["rawLifecycleBundleEmbedded"] is not False:
        raise AssertionError("OPP response mapping must not embed full lifecycle bundles by default")
    for readback in adapter["readbacks"]:
        if readback["mutatesState"] is not False:
            raise AssertionError("OPP provider adapter readbacks must not mutate state")
        if readback["startsNetworkListener"] is not False:
            raise AssertionError("OPP provider adapter readbacks must not start network listeners")
    for case in adapter["conformanceCases"][1:]:
        if case["forecastArtifactsCreated"] is not False:
            raise AssertionError("blocked OPP provider adapter cases must not create forecast artifacts")
        if case["opeRecordsMutated"] is not False:
            raise AssertionError("blocked OPP provider adapter cases must not mutate OPE records")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("blocked OPP provider adapter cases should keep diagnostics sanitized")


def assert_persistent_sqlite_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "persistent-sqlite-policy"
        / "ope-persistent-sqlite-policy.generated.json"
    )
    policy = load_json(path)
    if policy["persistentSqliteDefaultEnabled"] is not False:
        raise AssertionError("persistent SQLite must not be enabled by default")
    if policy["normalChecksUseEphemeralSqlite"] is not True:
        raise AssertionError("normal checks should keep using ephemeral SQLite")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"persistent SQLite policy boundary {key} should stay false")
    path_policy = policy["pathPolicy"]
    if path_policy["pathTraversalBlocked"] is not True:
        raise AssertionError("persistent SQLite path policy should block traversal")
    if path_policy["symlinkEscapeBlocked"] is not True:
        raise AssertionError("persistent SQLite path policy should block symlink escapes")
    if path_policy["credentialValuesAccepted"] is not False:
        raise AssertionError("persistent SQLite path policy must not accept credential values")
    if ".ope/state" not in path_policy["allowedRelativeRoots"]:
        raise AssertionError("persistent SQLite path policy should allowlist the local state root")
    for case in policy["pathCases"][2:]:
        if case["persistentDatabaseCreated"] is not False:
            raise AssertionError("blocked persistent SQLite cases must not create databases")
        if case["operationReceiptsWritten"] is not False:
            raise AssertionError("blocked persistent SQLite cases must not write operation receipts")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("blocked persistent SQLite cases should keep diagnostics sanitized")
    migration = policy["migrationPolicy"]
    if migration["automaticMigrationAllowed"] is not False:
        raise AssertionError("persistent SQLite migration must not run automatically")
    if migration["historicalForecastRewriteAllowed"] is not False:
        raise AssertionError("persistent SQLite migration must not rewrite forecast history")


def assert_lifecycle_lease_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "lifecycle-lease-policy"
        / "ope-lifecycle-lease-policy.generated.json"
    )
    policy = load_json(path)
    if policy["policyStatus"] != "lifecycle_operation_lease_policy_checked":
        raise AssertionError("lifecycle lease policy status drifted")
    if policy["allEffectfulOperationsRequireIdempotency"] is not True:
        raise AssertionError("lifecycle lease policy should require idempotency for all effectful operations")
    if policy["normalChecksAcquireLeases"] is not False:
        raise AssertionError("lifecycle lease policy should keep normal checks lease-free")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"lifecycle lease policy boundary {key} should stay false")
    strict_count = 0
    idempotency_count = 0
    for operation in policy["operationPolicies"]:
        if operation["preflightRequired"] is not True:
            raise AssertionError("lifecycle lease operations should require preflight checks")
        if operation["idempotencyKeyRequired"] is not True:
            raise AssertionError("lifecycle lease operations should require idempotency keys")
        if operation["operationReceiptRequired"] is not True:
            raise AssertionError("lifecycle lease operations should require operation receipts")
        if operation["normalChecksAcquireLease"] is not False:
            raise AssertionError("lifecycle lease readbacks must not acquire leases")
        if operation["rawCrudExposed"] is not False:
            raise AssertionError("lifecycle lease policy must not expose raw CRUD")
        if operation["qualityClaimAllowed"] is not False:
            raise AssertionError("lifecycle lease policy must not upgrade quality claims")
        if operation["guardMode"] == "strict_lease":
            strict_count += 1
            if operation["leaseRequired"] is not True:
                raise AssertionError("strict lifecycle operations should require leases")
        elif operation["guardMode"] == "idempotency_only":
            idempotency_count += 1
            if operation["leaseRequired"] is not False:
                raise AssertionError("idempotency-only lifecycle operations should not require leases")
        else:
            raise AssertionError("unknown lifecycle lease guard mode")
    if strict_count != 9 or idempotency_count != 5:
        raise AssertionError("lifecycle lease policy guard counts drifted")
    for case in policy["conflictCases"]:
        if case["operationReceiptsWritten"] is not False:
            raise AssertionError("lifecycle lease conflict cases must not write receipts")
        if case["immutableRecordsWritten"] is not False:
            raise AssertionError("lifecycle lease conflict cases must not write records")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("lifecycle lease conflict cases should keep diagnostics sanitized")


def assert_runtime_transport_readiness_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "runtime-transport-readiness"
        / "ope-runtime-transport-readiness.generated.json"
    )
    readiness = load_json(path)
    if readiness["readinessStatus"] != "runtime_transport_readiness_checked":
        raise AssertionError("runtime transport readiness status drifted")
    if readiness["normalChecksOffline"] is not True:
        raise AssertionError("runtime transport readiness should keep normal checks offline")
    if readiness["hostedRuntimeAllowedNow"] is not False:
        raise AssertionError("runtime transport readiness should block hosted runtime")
    if readiness["localHttpAllowedNow"] is not False:
        raise AssertionError("runtime transport readiness should defer local HTTP")
    boundary = readiness["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"runtime transport readiness boundary {key} should stay false")
    for surface in readiness["currentSurfaces"]:
        if surface["startsNetworkListener"] is not False:
            raise AssertionError("current transport surfaces must not start network listeners")
        if surface["hostedRuntimeRequired"] is not False:
            raise AssertionError("current transport surfaces must not require hosted runtime")
        if surface["credentialValuesAccepted"] is not False:
            raise AssertionError("current transport surfaces must not accept credential values")
    for surface in readiness["futureSurfaces"]:
        if surface["implementedNow"] is not False:
            raise AssertionError("future transport surfaces must not be implemented now")
        if surface["advertisedNow"] is not False:
            raise AssertionError("future transport surfaces must not be advertised now")
        if surface["normalChecksStartSurface"] is not False:
            raise AssertionError("future transport surfaces must not start in normal checks")
    for case in readiness["blockedCases"]:
        if case["networkListenerStarted"] is not False:
            raise AssertionError("blocked transport cases must not start listeners")
        if case["hostedRuntimeStarted"] is not False:
            raise AssertionError("blocked transport cases must not start hosted runtime")
        if case["stateWritten"] is not False:
            raise AssertionError("blocked transport cases must not write state")
        if case["credentialValuesStored"] is not False:
            raise AssertionError("blocked transport cases must not store credential values")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("blocked transport cases should keep diagnostics sanitized")


def assert_workspace_tenant_isolation_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "workspace-tenant-isolation"
        / "ope-workspace-tenant-isolation.generated.json"
    )
    isolation = load_json(path)
    if isolation["isolationStatus"] != "workspace_tenant_isolation_checked":
        raise AssertionError("workspace tenant isolation status drifted")
    if isolation["normalChecksMutateState"] is not False:
        raise AssertionError("workspace tenant isolation should keep normal checks non-mutating")
    if isolation["hostedTenantRuntimeImplemented"] is not False:
        raise AssertionError("workspace tenant isolation should not implement hosted tenant runtime")
    boundary = isolation["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"workspace tenant isolation boundary {key} should stay false")
    for binding in isolation["tenantWorkspaceBindings"]:
        if binding["rawSqlExposed"] is not False:
            raise AssertionError("tenant workspace bindings must not expose raw SQL")
        if binding["rawPrivateRowsExposed"] is not False:
            raise AssertionError("tenant workspace bindings must not expose raw private rows")
    for policy in isolation["operationQueuePolicies"]:
        if policy["crossTenantPeekAllowed"] is not False:
            raise AssertionError("operation queue policies must block cross-tenant peek")
        if policy["rawQueueCrudExposed"] is not False:
            raise AssertionError("operation queue policies must not expose raw queue CRUD")
        if policy["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("operation queue policies should keep diagnostics sanitized")
    for policy in isolation["sourceBindingPolicies"]:
        if policy["crossTenantReuseAllowed"] is not False:
            raise AssertionError("source binding policies must block cross-tenant reuse")
        if policy["credentialValuesStored"] is not False:
            raise AssertionError("source binding policies must not store credential values")
        if policy["rawPrivateRowsStored"] is not False:
            raise AssertionError("source binding policies must not store raw private rows")
    for case in isolation["accessCases"][1:]:
        if case["accessAllowed"] is not False:
            raise AssertionError("blocked tenant access cases must not allow access")
        if case["credentialValuesStored"] is not False:
            raise AssertionError("blocked tenant access cases must not store credential values")
        if case["operationReceiptsWritten"] is not False:
            raise AssertionError("blocked tenant access cases must not write receipts")
        if case["immutableRecordsWritten"] is not False:
            raise AssertionError("blocked tenant access cases must not write records")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("blocked tenant access cases should keep diagnostics sanitized")


def assert_domain_source_field_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "domain-source-field-policy"
        / "ope-domain-source-field-policy.generated.json"
    )
    policy = load_json(path)
    if policy["policyStatus"] != "domain_source_field_policy_checked":
        raise AssertionError("domain/source field policy status drifted")
    if policy["normalChecksMutateState"] is not False:
        raise AssertionError("domain/source field policy should keep normal checks non-mutating")
    if policy["generatedRuntimeTypesIncluded"] is not False:
        raise AssertionError("domain/source field policy should not generate runtime types")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"domain/source field policy boundary {key} should stay false")
    for field in policy["blockedFields"]:
        if field["requirementLevel"] != "blocked":
            raise AssertionError("domain/source blocked fields must use blocked requirement level")
        if field["domainExtensionAllowed"] is not False:
            raise AssertionError("domain/source blocked fields must not be extension-safe")
        if field["credentialValuesAllowed"] is not False:
            raise AssertionError("domain/source blocked fields must not allow credential values")
        if field["rawPrivateDataAllowed"] is not False:
            raise AssertionError("domain/source blocked fields must not allow raw private data")
    for rule in policy["sourceKindFieldRules"]:
        if rule["credentialValueAllowed"] is not False:
            raise AssertionError("domain/source source-kind rules must not allow credential values")
        if rule["rawPayloadStored"] is not False:
            raise AssertionError("domain/source source-kind rules must not store raw payloads")
    for case in policy["fieldDecisionCases"]:
        if case["forecastArtifactsCreated"] is not False:
            raise AssertionError("domain/source field cases must not create forecast artifacts")
        if case["credentialValuesStored"] is not False:
            raise AssertionError("domain/source field cases must not store credential values")
        if case["rawPrivateDataStored"] is not False:
            raise AssertionError("domain/source field cases must not store raw private data")
        if case["policyViolation"] is True and case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("domain/source blocked cases should keep diagnostics sanitized")


def assert_credential_reference_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "credential-reference-policy"
        / "ope-credential-reference-policy.generated.json"
    )
    policy = load_json(path)
    if policy["policyStatus"] != "credential_reference_policy_checked":
        raise AssertionError("credential reference policy status drifted")
    if policy["normalChecksMutateState"] is not False:
        raise AssertionError("credential reference policy should keep normal checks non-mutating")
    if policy["secretResolverImplemented"] is not False:
        raise AssertionError("credential reference policy should not implement a secret resolver")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"credential reference policy boundary {key} should stay false")
    for mechanism in policy["acceptedReferenceMechanisms"]:
        if mechanism["secretValueStored"] is not False:
            raise AssertionError("credential mechanisms must not store secret values")
        if mechanism["secretLookupDuringNormalChecks"] is not False:
            raise AssertionError("credential mechanisms must not resolve secrets in normal checks")
        if mechanism["promptVisibleSecretAllowed"] is not False:
            raise AssertionError("credential mechanisms must block prompt-visible secrets")
    for key in policy["requiredScopeKeys"]:
        if key["containsSecretMaterial"] is not False:
            raise AssertionError("credential scope keys must not contain secret material")
        if key["requiredForPrivateApi"] is not True:
            raise AssertionError("credential scope keys must be required for private APIs")
        if key["requiredForDatabase"] is not True:
            raise AssertionError("credential scope keys must be required for databases")
    for rule in policy["consumerRules"]:
        if rule["canReceiveCredentialValue"] is not False:
            raise AssertionError("credential consumer rules must not receive credential values")
        if rule["canResolveSecretInNormalChecks"] is not False:
            raise AssertionError("credential consumer rules must not resolve secrets in normal checks")
        if rule["requiresScopeMatch"] is not True or rule["requiresAdapterMatch"] is not True:
            raise AssertionError("credential consumer rules must require scope and adapter matches")
    for case in policy["credentialReferenceCases"]:
        if case["credentialValuesStored"] is not False:
            raise AssertionError("credential cases must not store credential values")
        if case["secretResolvedInNormalChecks"] is not False:
            raise AssertionError("credential cases must not resolve secrets in normal checks")
        if case["crossTenantReuseAllowed"] is not False:
            raise AssertionError("credential cases must not allow cross-tenant reuse")
        if case["caseStatus"].startswith("blocked_") and case["sourceBindingAccepted"] is not False:
            raise AssertionError("blocked credential cases must not accept source bindings")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("credential cases should keep diagnostics sanitized")


def assert_retention_redaction_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "retention-redaction-policy"
        / "ope-retention-redaction-policy.generated.json"
    )
    policy = load_json(path)
    if policy["policyStatus"] != "retention_redaction_policy_checked":
        raise AssertionError("retention/redaction policy status drifted")
    if policy["normalChecksMutateState"] is not False:
        raise AssertionError("retention/redaction policy should keep normal checks non-mutating")
    if policy["physicalDeleteDefaultEnabled"] is not False:
        raise AssertionError("retention/redaction policy should not enable physical delete by default")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"retention/redaction policy boundary {key} should stay false")
    if policy["sourceBindings"]["physicalDeletesInLifecycleScenarios"] != 0:
        raise AssertionError("retention/redaction policy source lifecycle scenarios must not physically delete")
    for item in policy["retentionClasses"]:
        if item["silentDeleteAllowed"] is not False:
            raise AssertionError("retention classes must not allow silent delete")
        if item["normalChecksWriteState"] is not False:
            raise AssertionError("retention classes must not write state in normal checks")
        if item["retainCredentialValues"] is not False:
            raise AssertionError("retention classes must not retain credential values")
        if item["auditMetadataRetained"] is not True:
            raise AssertionError("retention classes must retain audit metadata")
    for action in policy["policyActions"]:
        if action["normalChecksExecuteAction"] is not False:
            raise AssertionError("retention actions must not execute in normal checks")
        if action["silentDeleteAllowed"] is not False:
            raise AssertionError("retention actions must not allow silent delete")
        if action["actionName"] != "physical_delete_exception" and action["physicallyDeletesRecords"] is not False:
            raise AssertionError("only physical delete exception action may physically delete")
    for gate in policy["physicalDeleteGates"]:
        if gate["requiredForException"] is not True:
            raise AssertionError("physical delete gates must all be required")
        if gate["normalChecksEvaluateAsEffectful"] is not False:
            raise AssertionError("physical delete gates must stay non-effectful in normal checks")
    for case in policy["decisionCases"]:
        if case["normalChecksWriteState"] is not False:
            raise AssertionError("retention cases must not write state")
        if case["credentialValuesRetained"] is not False:
            raise AssertionError("retention cases must not retain credential values")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("retention cases should keep diagnostics sanitized")
        if case["selectedAction"] != "physical_delete_exception" and case["physicallyDeletesRecords"] is not False:
            raise AssertionError("non-exception retention cases must not physically delete")


def assert_private_auto_evidence_policy_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "private-auto-evidence-policy"
        / "ope-private-auto-evidence-policy.generated.json"
    )
    policy = load_json(path)
    if policy["policyStatus"] != "private_auto_evidence_policy_checked":
        raise AssertionError("private auto-evidence policy status drifted")
    if policy["normalChecksMutateState"] is not False:
        raise AssertionError("private auto-evidence policy should keep normal checks non-mutating")
    if policy["normalChecksReadPrivateSources"] is not False:
        raise AssertionError("private auto-evidence policy should not read private sources")
    boundary = policy["executionBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise AssertionError(f"private auto-evidence policy boundary {key} should stay false")
    for item in policy["sourceKindPolicies"]:
        if item["sourcePolicyRequired"] is not True:
            raise AssertionError("private auto source kinds must require source policy")
        if item["tenantWorkspaceScopeRequired"] is not True:
            raise AssertionError("private auto source kinds must require tenant/workspace scope")
        if item["normalChecksReadPrivateSource"] is not False:
            raise AssertionError("private auto source kinds must not read private sources in normal checks")
        if item["normalChecksResolveCredential"] is not False:
            raise AssertionError("private auto source kinds must not resolve credentials")
        if item["rawPayloadRetentionAllowed"] is not False:
            raise AssertionError("private auto source kinds must not retain raw payloads")
    for gate in policy["policyGates"]:
        if gate["requiredForPrivateAuto"] is not True:
            raise AssertionError("private auto policy gates must all be required")
        if gate["normalChecksEvaluateAsEffectful"] is not False:
            raise AssertionError("private auto policy gates must stay non-effectful")
    for case in policy["decisionCases"]:
        if case["normalChecksReadPrivateSources"] is not False:
            raise AssertionError("private auto cases must not read private sources")
        if case["normalChecksWriteState"] is not False:
            raise AssertionError("private auto cases must not write state")
        if case["credentialValuesStored"] is not False:
            raise AssertionError("private auto cases must not store credential values")
        if case["sanitizedDiagnosticsOnly"] is not True:
            raise AssertionError("private auto cases should keep diagnostics sanitized")
        if case["caseStatus"].startswith("blocked_") and case["eligibleForForecastExecution"] is not False:
            raise AssertionError("blocked private auto cases must not be forecast-eligible")
    for readback in policy["readbacks"]:
        if readback["mutatesState"] is not False:
            raise AssertionError("private auto readbacks must not mutate state")
        if readback["readsPrivateSource"] is not False:
            raise AssertionError("private auto readbacks must not read private sources")
        if readback["resolvesCredentials"] is not False:
            raise AssertionError("private auto readbacks must not resolve credentials")


def assert_agent_integration_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "agent-integration"
        / "ope-agent-integration.generated.json"
    )
    integration = load_json(path)
    if integration["integrationStatus"] != "agent_integration_golden_path_checked":
        raise AssertionError("agent integration status drifted")
    boundary = integration["executionBoundary"]
    if boundary["approvedFilesAndSanitizedAdaptersOnly"] is not True:
        raise AssertionError("agent integration should allow only approved files and sanitized adapters")
    if boundary["normalChecksAreReadOnly"] is not True:
        raise AssertionError("agent integration normal checks should stay read-only")
    for key, value in boundary.items():
        if key in {
            "approvedFilesAndSanitizedAdaptersOnly",
            "normalChecksAreReadOnly",
            "hostedRuntimeBlocked",
            "qualityClaimUpgradeBlocked",
            "calibrationClaimUpgradeBlocked",
        }:
            continue
        if value is not False:
            raise AssertionError(f"agent integration boundary {key} should stay false")
    accepted = {item["caseKey"]: item for item in integration["guidedForecastCases"]}["accepted_adapter_output"]
    if accepted["toolCallCount"] > 3:
        raise AssertionError("agent integration accepted case should stay within three routine calls")
    if accepted["createsForecastArtifacts"] is not False:
        raise AssertionError("agent integration readback should not create forecast artifacts")
    for item in integration["guidedForecastCases"]:
        if item["guidedStatus"] == "blocked" and item["forecastId"] is not None:
            raise AssertionError("blocked agent integration cases must not bind forecast ids")
        if item["guidedStatus"] == "blocked" and item["forecastCardCommand"] is not None:
            raise AssertionError("blocked agent integration cases must not expose forecast-card commands")


def assert_prediction_feature_setup_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "prediction-feature-setup"
        / "ope-prediction-feature-setup.generated.json"
    )
    setup = load_json(path)
    if setup["setupStatus"] != "checked_compact_contract":
        raise AssertionError("prediction feature setup status drifted")
    if setup["createsNewForecastPath"] is not False:
        raise AssertionError("prediction feature setup must not create a new forecast path")
    if setup["hostedRuntimeRequired"] is not False:
        raise AssertionError("prediction feature setup must not require hosted runtime")
    request = setup["requestContract"]
    for key in ["acceptsCredentialValues", "acceptsRawPrivateRows", "acceptsRawSql"]:
        if request[key] is not False:
            raise AssertionError(f"prediction feature setup request boundary {key} should stay false")
    for response in setup["responseExamples"]:
        for key in [
            "createsForecastArtifacts",
            "executesPrivateSources",
            "storesCredentialValues",
            "storesRawPrivateRows",
            "qualityClaimAllowed",
        ]:
            if response[key] is not False:
                raise AssertionError(f"prediction feature setup response boundary {key} should stay false")
    for key, value in setup["executionBoundary"].items():
        if value is not False:
            raise AssertionError(f"prediction feature setup execution boundary {key} should stay false")


def assert_setup_engine_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "setup-engine"
        / "ope-setup-engine.generated.json"
    )
    setup = load_json(path)
    if setup["engineSetupStatus"] != "checked_readback":
        raise AssertionError("setup-engine status drifted")
    if setup["createsForecastArtifacts"] is not False:
        raise AssertionError("setup-engine must not create forecast artifacts")
    if setup["hostedRuntimeRequired"] is not False:
        raise AssertionError("setup-engine must not require hosted runtime")
    if setup["hostWrapper"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("setup-engine host wrapper should render before forecast artifacts")
    for role in setup["requiredSourceRoles"]:
        for key in ["acceptsCredentialValues", "acceptsRawPrivateRows", "acceptsRawSql"]:
            if role[key] is not False:
                raise AssertionError(f"setup-engine source role {role['roleName']} boundary {key} should stay false")
    for key in [
        "qualityClaimAllowed",
        "calibrationClaimAllowed",
        "hostedRuntimeProvided",
        "trainedModelProvided",
        "executesLiveFetch",
        "acceptsRawSql",
        "acceptsCredentialValues",
        "acceptsRawPrivateRows",
    ]:
        if setup["claimBoundary"][key] is not False:
            raise AssertionError(f"setup-engine claim boundary {key} should stay false")


def assert_prediction_goal_catalog_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "prediction-goal-catalog"
        / "ope-prediction-goal-catalog.generated.json"
    )
    catalog = load_json(path)
    if catalog["catalogStatus"] != "checked_domain_agnostic_goal_catalog":
        raise AssertionError("prediction goal catalog status drifted")
    for key in ["qualityClaimAllowed", "createsForecastArtifacts", "hostedRuntimeRequired"]:
        if catalog[key] is not False:
            raise AssertionError(f"prediction goal catalog top-level boundary {key} should stay false")
    for key, value in catalog["executionBoundary"].items():
        if value is not False:
            raise AssertionError(f"prediction goal catalog execution boundary {key} should stay false")
    for example in catalog["goalExamples"]:
        for key in ["qualityClaimAllowed", "createsForecastArtifacts", "hostedRuntimeRequired"]:
            if example[key] is not False:
                raise AssertionError(f"prediction goal catalog example {example['goalKey']} boundary {key} should stay false")
        if example["classification"] in {"blocked", "rejected"} and not example["blockedReason"]:
            raise AssertionError(f"prediction goal catalog example {example['goalKey']} should explain blocked/rejected handling")


def assert_embedded_host_wrapper_boundary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "examples/embed-ope-prediction-feature/host_wrapper.py",
            "--request",
            "examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json",
            "--output-format",
            "json",
        ],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise AssertionError(f"embedded host wrapper failed: {result.stderr or result.stdout}")
    payload = json.loads(result.stdout)
    if payload["exampleStatus"] != "setup_plan_and_forecast_card_ready":
        raise AssertionError("embedded host wrapper should render setup plan before forecast card")
    if not payload["opeCallSequence"][0].startswith("python3 scripts/ope.py setup-engine"):
        raise AssertionError("embedded host wrapper must call setup-engine first")
    if payload["setupEnginePlan"]["renderBeforeForecastArtifacts"] is not True:
        raise AssertionError("embedded host wrapper setup plan should render before forecast artifacts")
    for key, value in payload["executionBoundary"].items():
        if value is not False:
            raise AssertionError(f"embedded host wrapper execution boundary {key} should stay false")


def assert_agent_guidance_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "agent-guidance"
        / "ope-agent-guidance.generated.json"
    )
    guidance = load_json(path)
    if guidance["guidanceStatus"] != "checked_agent_guidance_loop":
        raise AssertionError("agent guidance status drifted")
    if guidance["summary"]["guidanceCaseCount"] != 5:
        raise AssertionError("agent guidance should expose five cases")
    if guidance["summary"]["realSessionsRecorded"] != 0:
        raise AssertionError("agent guidance must not count real sessions")
    if guidance["summary"]["forecastArtifactsCreated"] is not False:
        raise AssertionError("agent guidance must not create forecast artifacts")
    boundary = guidance["executionBoundary"]
    for key, value in boundary.items():
        if key in {"agentUsesOwnIntelligence", "normalChecksAreReadOnly"}:
            if value is not True:
                raise AssertionError(f"agent guidance boundary {key} should stay true")
            continue
        if value is not False:
            raise AssertionError(f"agent guidance boundary {key} should stay false")
    for case in guidance["guidanceCases"]:
        for key in [
            "createsForecastArtifacts",
            "storesCredentialValues",
            "storesRawPrivateRows",
            "executesSources",
            "qualityClaimAllowed",
        ]:
            if case[key] is not False:
                raise AssertionError(f"agent guidance case {case['caseKey']} boundary {key} should stay false")


def assert_simulated_agent_pilot_boundary() -> None:
    path = (
        ROOT
        / "spec"
        / "fixtures"
        / "generated"
        / "simulated-agent-pilot"
        / "ope-simulated-agent-pilot.generated.json"
    )
    simulated = load_json(path)
    if simulated["simulationStatus"] != "checked_agent_only_simulation":
        raise AssertionError("simulated agent pilot status drifted")
    if simulated["summary"]["simulatedSessionCount"] != 8:
        raise AssertionError("simulated agent pilot should include eight simulated sessions")
    if simulated["summary"]["nonHelsinkiSessionCount"] != 3:
        raise AssertionError("simulated agent pilot should include three non-Helsinki sessions")
    if simulated["summary"]["engineSetupComprehensionReady"] is not True:
        raise AssertionError("simulated agent pilot should expose setup comprehension readiness")
    if simulated["summary"]["realSessionsRecorded"] != 0:
        raise AssertionError("simulated agent pilot must not count real sessions")
    if simulated["summary"]["pilotEvidenceReady"] is not False:
        raise AssertionError("simulated agent pilot must not unblock real pilot evidence")
    boundary = simulated["executionBoundary"]
    if boundary["agentOnlySimulation"] is not True:
        raise AssertionError("simulated agent pilot should be marked agent-only")
    if boundary["realSessionsRecorded"] != 0:
        raise AssertionError("simulated agent pilot boundary must keep real sessions at zero")
    for key in [
        "rawTranscriptsStored",
        "rawPromptLogsStoredAsPilotEvidence",
        "privateDataStored",
        "credentialValuesStored",
        "hostProjectSecretsStored",
        "forecastArtifactsCreated",
        "qualityClaimsUpgraded",
        "calibrationClaimsUpgraded",
        "hostedRuntimeUnblocked",
        "generatedTypesUnblocked",
    ]:
        if boundary[key] is not False:
            raise AssertionError(f"simulated agent pilot boundary {key} should stay false")


def main() -> None:
    assert_no_secrets()
    assert_malformed_artifact_fails()
    assert_oversized_io_fails()
    assert_no_duplicate_records()
    assert_aggregate_dependency_review()
    assert_claim_review_exists()
    assert_adapter_read_surface_size_guards()
    assert_runtime_security_contract()
    assert_database_source_adapter_runtime_boundary()
    assert_opp_provider_adapter_boundary()
    assert_persistent_sqlite_policy_boundary()
    assert_lifecycle_lease_policy_boundary()
    assert_runtime_transport_readiness_boundary()
    assert_workspace_tenant_isolation_boundary()
    assert_domain_source_field_policy_boundary()
    assert_credential_reference_policy_boundary()
    assert_retention_redaction_policy_boundary()
    assert_private_auto_evidence_policy_boundary()
    assert_agent_integration_boundary()
    assert_prediction_feature_setup_boundary()
    assert_setup_engine_boundary()
    assert_prediction_goal_catalog_boundary()
    assert_embedded_host_wrapper_boundary()
    assert_agent_guidance_boundary()
    assert_simulated_agent_pilot_boundary()
    print("checked hardening guardrails")


if __name__ == "__main__":
    main()
