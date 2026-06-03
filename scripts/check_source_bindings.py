#!/usr/bin/env python3
"""Check source binding setup semantics."""

from __future__ import annotations

from generate_source_bindings import (
    ACCEPTED,
    BLOCKED,
    PARTIAL,
    REJECTED,
    build_source_bindings,
)


REQUIRED_CHECKS = {
    "mapping_confidence",
    "source_quality",
    "leakage",
    "freshness",
    "privacy",
    "outcome_availability",
}

REQUIRED_OPERATIONS = {
    "source_binding.draft",
    "source_binding.validate",
    "source_binding.confirm",
    "source_binding.update",
    "source_binding.archive",
    "source_binding.redact",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    bindings = build_source_bindings()
    require(set(bindings) == {ACCEPTED, PARTIAL, REJECTED, BLOCKED}, "source binding case coverage drifted")

    approved_source_kinds = set()
    domains = set()
    for binding in bindings.values():
        domains.add(binding["domainKey"])
        role_rows = binding["sourceRoleBindings"]
        check_rows = binding["preForecastChecks"]
        operation_rows = binding["setupOperations"]
        require({row["checkName"] for row in check_rows} == REQUIRED_CHECKS, "pre-forecast checks drifted")
        require({row["operationName"] for row in operation_rows} == REQUIRED_OPERATIONS, "setup operation coverage drifted")
        require(binding["credentialPolicy"]["credentialValuesStored"] is False, "credential values must not be stored")
        require(binding["executionBoundary"]["createsForecasts"] is False, "source binding readbacks must not create forecasts")
        require(binding["executionBoundary"]["readsPrivateData"] is False, "source binding checks must not read private data")
        require(binding["executionBoundary"]["executesApiCalls"] is False, "source binding checks must not execute APIs")
        require(binding["executionBoundary"]["executesDatabaseQueries"] is False, "source binding checks must not execute databases")
        require(
            binding["configurationInputBoundary"]["arbitraryPrivateApiParsingByOpe"] is False,
            "OPE must not parse arbitrary private APIs directly",
        )
        require(
            binding["configurationInputBoundary"]["arbitraryDatabaseParsingByOpe"] is False,
            "OPE must not parse arbitrary databases directly",
        )
        for operation in operation_rows:
            require(operation["requiresReceipt"] is True, "setup operations should be receipt-backed")
            require(operation["requiresIdempotencyKey"] is True, "setup operations should be idempotent")
            require(operation["requiresLease"] is True, "setup operations should require leases")
            require(operation["writesRawConfig"] is False, "setup operations must not write raw config")
            require(operation["physicalDeleteAllowed"] is False, "setup operations must not physically delete")
        for role in role_rows:
            if role["approvalStatus"] == "approved":
                approved_source_kinds.add(role["sourceKind"])
            require(role["credentialValuesStored"] is False, "role bindings must not store credentials")
            if role["bindingStatus"] == "confirmed":
                require(role["sanitizedManifestProvided"] is True, "confirmed roles need sanitized manifests")
            if role["roleKey"].endswith("_outcome"):
                require(role["forecastTimeAllowed"] is False, "outcome roles must be resolution-only")

    require(domains == {"weather-transit-delays", "seaport-berth-availability"}, "domain examples drifted")
    require(
        {"api", "database", "local_file", "source_adapter_output"}.issubset(approved_source_kinds),
        "source bindings should cover approved local file, adapter, API, and database sources",
    )

    accepted = bindings[ACCEPTED]
    require(accepted["nextAction"] == "forecast_generation_allowed", "accepted binding next action drifted")
    require(accepted["summary"]["forecastGenerationAllowed"] is True, "accepted binding should allow forecast generation")
    require(all(not row["blocksForecast"] for row in accepted["preForecastChecks"]), "accepted checks should not block")
    require(all(row["bindingStatus"] == "confirmed" for row in accepted["sourceRoleBindings"]), "accepted roles should be confirmed")

    partial = bindings[PARTIAL]
    require(partial["nextAction"] == "collect_missing_source_binding", "partial binding next action drifted")
    require(partial["summary"]["forecastGenerationAllowed"] is False, "partial binding must block forecasts")
    require(any(row["bindingStatus"] == "missing" for row in partial["sourceRoleBindings"]), "partial case should expose missing role")
    require(any(row["checkStatus"] == "fail" for row in partial["preForecastChecks"]), "partial case should expose failed check")

    rejected = bindings[REJECTED]
    require(rejected["nextAction"] == "replace_source_binding", "rejected binding next action drifted")
    require(rejected["summary"]["forecastGenerationAllowed"] is False, "rejected binding must block forecasts")
    require(any(row["approvalStatus"] == "rejected" for row in rejected["sourceRoleBindings"]), "rejected case should reject sources")

    blocked = bindings[BLOCKED]
    require(blocked["nextAction"] == "stop_unsafe_source_binding", "blocked binding next action drifted")
    require(blocked["credentialPolicy"]["rawCredentialValueDetected"] is True, "blocked case should detect raw credentials")
    require(all(row["blocksForecast"] for row in blocked["preForecastChecks"]), "blocked case should block every check")
    require(any(row["rawSqlAllowed"] for row in blocked["sourceRoleBindings"]), "blocked case should expose raw SQL detection")
    require(any(row["privateParsingByOpe"] for row in blocked["sourceRoleBindings"]), "blocked case should expose private parsing risk")

    print("checked source bindings")


if __name__ == "__main__":
    main()
