#!/usr/bin/env python3
"""Generate or check the narrow approved local-source runtime."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from build_source_manifest import LOCAL_FIXTURES
from generate_source_intake_handoff import build_handoffs
from generate_source_handoff_method_gate import build_records as build_method_gate_records
from ope_schema import SPEC, validate_record
from read_ope_record import read_record
from run_source_handoff_forecast import build_outputs as build_source_handoff_forecast_outputs
from run_source_handoff_forecast import output_prefix
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "local-source-runtime"
OUTPUT_PATH = GENERATED / "weather-logistics-local-source-runtime.generated.json"
SCHEMA = SPEC / "local-source-runtime.schema.json"
GENERATED_AT = "2026-06-10T09:20:00Z"
SOURCE_POLICY_ID = "sourcepolicy-850"
MAX_FILE_BYTES = 2048
MAX_TOTAL_BYTES = 4096

CASE_ORDER = [
    "approved_local_folder",
    "missing_approval",
    "credentials_detected",
    "unsafe_path",
    "oversized_response",
    "schema_mismatch",
    "leakage_indicator",
]

ROLE_FILES = [
    ("weather_forecast", "weather-forecast.json"),
    ("historical_baseline", "history.csv"),
    ("declared_operations_outcome", "outcome.csv"),
]


class LocalSourceRuntimeError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def is_allowlisted(path: Path) -> bool:
    try:
        path.resolve().relative_to(LOCAL_FIXTURES.resolve())
        return True
    except ValueError:
        return False


def file_size(path: Path) -> int:
    return path.stat().st_size if path.exists() and path.is_file() else 0


def folder_total_bytes(folder: Path) -> int:
    return sum(file_size(folder / filename) for _role, filename in ROLE_FILES)


def diagnostic(index: int, level: str, message: str) -> dict[str, Any]:
    return {
        "diagnosticId": f"localsourceruntimediagnostic-{index:03d}",
        "level": level,
        "message": message,
        "rawDetailIncluded": False,
    }


def empty_bindings() -> dict[str, None]:
    return {
        "sourceManifestBuildId": None,
        "sourceIntakeHandoffId": None,
        "sourceIntakeReportId": None,
        "setupBenchmarkGateId": None,
        "setupMethodDecisionId": None,
        "setupForecastRunId": None,
        "forecastId": None,
        "questionId": None,
        "forecastCardId": None,
    }


def controls(
    *,
    approval: bool,
    allowlist: bool,
    size_ok: bool,
    builder: bool,
    intake: bool,
    method: bool,
    explicit_forecast: bool,
) -> dict[str, bool]:
    return {
        "sourcePolicyBound": True,
        "approvalVerified": approval,
        "pathAllowlistPassed": allowlist,
        "sizeLimitPassed": size_ok,
        "sourceBuilderInspected": builder,
        "sourceIntakeValidated": intake,
        "methodGateValidated": method,
        "explicitForecastExecutionValidated": explicit_forecast,
        "runtimeCreatedForecastArtifacts": False,
        "networkAccess": False,
        "liveFetch": False,
        "credentialsRead": False,
        "credentialsStored": False,
        "rawRowsStored": False,
        "arbitraryParsing": False,
        "hostedRuntime": False,
    }


def runtime_case(
    *,
    index: int,
    case: str,
    input_path: str,
    runtime_status: str,
    next_action: str,
    approval_present: bool,
    allowlist_status: str,
    total_bytes: int,
    diagnostics: list[dict[str, Any]],
    blocked_reasons: list[str],
    bindings: dict[str, Any],
    case_controls: dict[str, bool],
) -> dict[str, Any]:
    return {
        "caseId": f"localsourceruntimecase-{index:03d}",
        "case": case,
        "inputPath": input_path,
        "runtimeStatus": runtime_status,
        "nextAction": next_action,
        "approvalPresent": approval_present,
        "allowlistStatus": allowlist_status,
        "totalBytes": total_bytes,
        "diagnostics": diagnostics,
        "blockedReasons": sorted(blocked_reasons),
        "bindings": bindings,
        "controls": case_controls,
    }


def handoff_bindings(case: str, handoffs: dict[str, Any]) -> dict[str, Any]:
    handoff, _build, _manifest, _mapping, _report = handoffs[case]
    bindings = empty_bindings()
    bindings["sourceManifestBuildId"] = handoff["sourceManifestBuildId"]
    bindings["sourceIntakeHandoffId"] = handoff["sourceIntakeHandoffId"]
    bindings["sourceIntakeReportId"] = handoff["sourceIntakeReportId"]
    return bindings


def approved_bindings(
    handoffs: dict[str, Any],
    method_gate_records: dict[str, Any],
    forecast_outputs: dict[str, Any],
) -> dict[str, Any]:
    handoff, _build, _manifest, _mapping, _report = handoffs["confirmed_builder_draft"]
    summary, _benchmark_gate, decision = method_gate_records["confirmed_builder_draft"]
    run = forecast_outputs[
        f"{output_prefix('confirmed_builder_draft')}-setup-forecast-run.generated.json"
    ]
    bindings = empty_bindings()
    bindings.update(
        {
            "sourceManifestBuildId": handoff["sourceManifestBuildId"],
            "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
            "sourceIntakeReportId": handoff["sourceIntakeReportId"],
            "setupBenchmarkGateId": summary["setupBenchmarkGateId"],
            "setupMethodDecisionId": decision["setupMethodDecisionId"],
            "setupForecastRunId": run["setupForecastRunId"],
            "forecastId": run["recordBinding"]["forecastId"],
            "questionId": run["recordBinding"]["questionId"],
            "forecastCardId": run["recordBinding"]["forecastCardId"],
        }
    )
    return bindings


def count_status(cases: list[dict[str, Any]], status: str) -> int:
    return sum(1 for item in cases if item["runtimeStatus"] == status)


def build_runtime() -> dict[str, Any]:
    handoffs = build_handoffs()
    method_gate_records = build_method_gate_records()
    forecast_outputs = build_source_handoff_forecast_outputs()
    card_response = read_record("forecast-card", "forecast-1102", "question-1102")
    card = card_response["record"]

    approved_folder = LOCAL_FIXTURES
    accepted_bindings = approved_bindings(handoffs, method_gate_records, forecast_outputs)
    cases = [
        runtime_case(
            index=1,
            case="approved_local_folder",
            input_path=rel(approved_folder),
            runtime_status="forecast_card_ready",
            next_action="read_forecast_card",
            approval_present=True,
            allowlist_status="passed",
            total_bytes=folder_total_bytes(approved_folder),
            diagnostics=[
                diagnostic(1, "info", "Caller-approved local folder matched the OPE allow-list and required role files."),
                diagnostic(2, "info", "Existing source-builder, intake, method gate, and explicit forecast execution records produced forecast-1102."),
            ],
            blocked_reasons=[],
            bindings=accepted_bindings,
            case_controls=controls(
                approval=True,
                allowlist=True,
                size_ok=True,
                builder=True,
                intake=True,
                method=True,
                explicit_forecast=True,
            ),
        ),
        runtime_case(
            index=2,
            case="missing_approval",
            input_path=rel(approved_folder),
            runtime_status="blocked_missing_approval",
            next_action="confirm_approval",
            approval_present=False,
            allowlist_status="passed",
            total_bytes=0,
            diagnostics=[
                diagnostic(3, "error", "Runtime did not inspect local files because caller approval was missing."),
            ],
            blocked_reasons=["caller_approval_missing"],
            bindings=empty_bindings(),
            case_controls=controls(
                approval=False,
                allowlist=True,
                size_ok=True,
                builder=False,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
        runtime_case(
            index=3,
            case="credentials_detected",
            input_path=rel(LOCAL_FIXTURES / "contains-secret.csv"),
            runtime_status="blocked_credentials",
            next_action="remove_credentials",
            approval_present=True,
            allowlist_status="passed",
            total_bytes=file_size(LOCAL_FIXTURES / "contains-secret.csv"),
            diagnostics=[
                diagnostic(4, "error", "Credential-like fields were detected and blocked before source intake."),
            ],
            blocked_reasons=["source_contains_secrets"],
            bindings=handoff_bindings("contains_secret", handoffs),
            case_controls=controls(
                approval=True,
                allowlist=True,
                size_ok=True,
                builder=True,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
        runtime_case(
            index=4,
            case="unsafe_path",
            input_path="/tmp/ope-unapproved/private-source.csv",
            runtime_status="blocked_unsafe_path",
            next_action="choose_allowlisted_path",
            approval_present=True,
            allowlist_status="failed",
            total_bytes=0,
            diagnostics=[
                diagnostic(5, "error", "Input path is outside the configured local source runtime allow-list."),
            ],
            blocked_reasons=["path_not_allowlisted"],
            bindings=empty_bindings(),
            case_controls=controls(
                approval=True,
                allowlist=False,
                size_ok=False,
                builder=False,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
        runtime_case(
            index=5,
            case="oversized_response",
            input_path=rel(LOCAL_FIXTURES / "oversized.csv"),
            runtime_status="blocked_oversized",
            next_action="reduce_file_size",
            approval_present=True,
            allowlist_status="passed",
            total_bytes=file_size(LOCAL_FIXTURES / "oversized.csv"),
            diagnostics=[
                diagnostic(6, "error", "Local file exceeds the narrow runtime size limit."),
            ],
            blocked_reasons=["file_too_large"],
            bindings=handoff_bindings("oversized", handoffs),
            case_controls=controls(
                approval=True,
                allowlist=True,
                size_ok=False,
                builder=True,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
        runtime_case(
            index=6,
            case="schema_mismatch",
            input_path=rel(LOCAL_FIXTURES / "unsupported.txt"),
            runtime_status="blocked_schema_mismatch",
            next_action="replace_with_supported_schema",
            approval_present=True,
            allowlist_status="passed",
            total_bytes=file_size(LOCAL_FIXTURES / "unsupported.txt"),
            diagnostics=[
                diagnostic(7, "error", "Local file format is outside the runtime CSV/JSON schema boundary."),
            ],
            blocked_reasons=["unsupported_format"],
            bindings=handoff_bindings("unsupported_format", handoffs),
            case_controls=controls(
                approval=True,
                allowlist=True,
                size_ok=True,
                builder=True,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
        runtime_case(
            index=7,
            case="leakage_indicator",
            input_path=rel(LOCAL_FIXTURES / "post-outcome-leakage.csv"),
            runtime_status="blocked_leakage",
            next_action="remove_leakage_source",
            approval_present=True,
            allowlist_status="passed",
            total_bytes=file_size(LOCAL_FIXTURES / "post-outcome-leakage.csv"),
            diagnostics=[
                diagnostic(8, "error", "Post-outcome leakage indicators were detected and blocked before source intake."),
            ],
            blocked_reasons=["post_outcome_leakage_indicator"],
            bindings=handoff_bindings("leakage", handoffs),
            case_controls=controls(
                approval=True,
                allowlist=True,
                size_ok=True,
                builder=True,
                intake=False,
                method=False,
                explicit_forecast=False,
            ),
        ),
    ]

    runtime = {
        "localSourceRuntimeId": "localsourceruntime-001",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "runtimeMode": "approved_local_folder_runtime",
        "runtimePolicy": {
            "sourcePolicyId": SOURCE_POLICY_ID,
            "approvalRequired": True,
            "allowedRoots": [rel(LOCAL_FIXTURES)],
            "requiredRoleFiles": [
                {"sourceRole": role, "fileName": filename}
                for role, filename in ROLE_FILES
            ],
            "allowedFormats": ["csv", "json"],
            "maxFileBytes": MAX_FILE_BYTES,
            "maxTotalBytes": MAX_TOTAL_BYTES,
            "allowNetworkAccess": False,
            "credentialStorageImplemented": False,
            "rawRetention": "metadata_only",
        },
        "runtimeCases": cases,
        "forecastCardReadback": {
            "forecastId": card["forecastId"],
            "questionId": card["questionId"],
            "cardId": card["cardId"],
            "readCommand": "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "readStatus": "available",
            "probability": card["forecast"]["probability"],
            "claimStatus": card["qualityClaim"]["status"],
            "sourceRuntimeCaseId": "localsourceruntimecase-001",
        },
        "summary": {
            "caseCount": len(cases),
            "forecastCardReadyCount": count_status(cases, "forecast_card_ready"),
            "blockedCount": sum(1 for item in cases if item["runtimeStatus"] != "forecast_card_ready"),
            "missingApprovalCount": count_status(cases, "blocked_missing_approval"),
            "credentialBlockedCount": count_status(cases, "blocked_credentials"),
            "unsafePathBlockedCount": count_status(cases, "blocked_unsafe_path"),
            "oversizedBlockedCount": count_status(cases, "blocked_oversized"),
            "schemaMismatchBlockedCount": count_status(cases, "blocked_schema_mismatch"),
            "leakageBlockedCount": count_status(cases, "blocked_leakage"),
            "qualityClaimAllowed": False,
            "productionConnectorClaimAllowed": False,
        },
        "executionBoundary": {
            "runtimeReadsAllowlistedLocalFiles": True,
            "runtimeRequiresCallerApproval": True,
            "normalChecksDeterministicOffline": True,
            "networkAccess": False,
            "liveFetch": False,
            "credentialStorage": False,
            "rawRowsStored": False,
            "arbitraryPrivateApiParsing": False,
            "arbitraryDatabaseParsing": False,
            "hostedRuntime": False,
            "osWatcherInstalled": False,
            "runtimeCreatesForecastArtifacts": False,
            "explicitForecastExecutionRequired": True,
            "qualityClaimAllowed": False,
            "productionConnectorClaimAllowed": False,
        },
        "warnings": [
            "This runtime is limited to caller-approved local CSV/JSON files under the configured allow-listed folder.",
            "Accepted files still pass through source builder, source intake, setup benchmark, setup method decision, and explicit forecast execution gates.",
            "The runtime does not parse arbitrary private APIs, databases, credentials, or hosted watch events.",
            "Forecast quality and production connector claims remain blocked.",
        ],
    }
    validate_runtime(runtime)
    return runtime


def validate_runtime(runtime: dict[str, Any]) -> None:
    errors = validate_record(runtime, SCHEMA)
    if errors:
        raise LocalSourceRuntimeError(f"local source runtime schema validation failed: {errors[0]}")
    cases = runtime["runtimeCases"]
    if [item["case"] for item in cases] != CASE_ORDER:
        raise LocalSourceRuntimeError("local source runtime case coverage drifted")
    cases_by_name = {item["case"]: item for item in cases}
    accepted = cases_by_name["approved_local_folder"]
    if not is_allowlisted(LOCAL_FIXTURES):
        raise LocalSourceRuntimeError("configured local source fixture root should be allowlisted")
    if accepted["runtimeStatus"] != "forecast_card_ready" or accepted["nextAction"] != "read_forecast_card":
        raise LocalSourceRuntimeError("approved local folder should produce forecast-card readback")
    if accepted["bindings"]["forecastId"] != "forecast-1102" or accepted["bindings"]["forecastCardId"] != "forecastcard-forecast-1102":
        raise LocalSourceRuntimeError("approved local folder should bind forecast-1102 card")
    for key in [
        "sourceBuilderInspected",
        "sourceIntakeValidated",
        "methodGateValidated",
        "explicitForecastExecutionValidated",
    ]:
        if accepted["controls"][key] is not True:
            raise LocalSourceRuntimeError(f"approved local folder should validate {key}")
    if accepted["controls"]["runtimeCreatedForecastArtifacts"]:
        raise LocalSourceRuntimeError("runtime must not create forecast artifacts directly")

    expectations = {
        "missing_approval": ("blocked_missing_approval", "confirm_approval", "caller_approval_missing"),
        "credentials_detected": ("blocked_credentials", "remove_credentials", "source_contains_secrets"),
        "unsafe_path": ("blocked_unsafe_path", "choose_allowlisted_path", "path_not_allowlisted"),
        "oversized_response": ("blocked_oversized", "reduce_file_size", "file_too_large"),
        "schema_mismatch": ("blocked_schema_mismatch", "replace_with_supported_schema", "unsupported_format"),
        "leakage_indicator": ("blocked_leakage", "remove_leakage_source", "post_outcome_leakage_indicator"),
    }
    for case, (status, next_action, reason) in expectations.items():
        item = cases_by_name[case]
        if item["runtimeStatus"] != status or item["nextAction"] != next_action:
            raise LocalSourceRuntimeError(f"{case} runtime status or next action drifted")
        if reason not in item["blockedReasons"]:
            raise LocalSourceRuntimeError(f"{case} should include blocked reason {reason}")
        if item["bindings"]["forecastId"] is not None:
            raise LocalSourceRuntimeError(f"{case} must not bind a forecast")
        if item["controls"]["explicitForecastExecutionValidated"]:
            raise LocalSourceRuntimeError(f"{case} must not reach explicit forecast execution")

    unsafe = cases_by_name["unsafe_path"]
    if unsafe["allowlistStatus"] != "failed" or unsafe["controls"]["pathAllowlistPassed"]:
        raise LocalSourceRuntimeError("unsafe path should fail allowlist checks")

    summary = runtime["summary"]
    if summary["forecastCardReadyCount"] != 1 or summary["blockedCount"] != 6:
        raise LocalSourceRuntimeError("local source runtime summary counts drifted")
    if summary["qualityClaimAllowed"] or summary["productionConnectorClaimAllowed"]:
        raise LocalSourceRuntimeError("local source runtime must keep quality and production connector claims blocked")

    readback = runtime["forecastCardReadback"]
    if readback["forecastId"] != accepted["bindings"]["forecastId"]:
        raise LocalSourceRuntimeError("forecast-card readback should bind accepted runtime case")
    if readback["claimStatus"] != "not_enough_resolved_source_handoff_outcomes":
        raise LocalSourceRuntimeError("local runtime forecast-card claim status drifted")

    boundary = runtime["executionBoundary"]
    if not boundary["runtimeReadsAllowlistedLocalFiles"] or not boundary["runtimeRequiresCallerApproval"]:
        raise LocalSourceRuntimeError("local runtime should read only approved allowlisted files")
    if not boundary["normalChecksDeterministicOffline"] or not boundary["explicitForecastExecutionRequired"]:
        raise LocalSourceRuntimeError("local runtime should stay deterministic and require explicit forecast execution")
    for key, value in boundary.items():
        if key in {
            "runtimeReadsAllowlistedLocalFiles",
            "runtimeRequiresCallerApproval",
            "normalChecksDeterministicOffline",
            "explicitForecastExecutionRequired",
        }:
            continue
        if value is not False:
            raise LocalSourceRuntimeError(f"local runtime boundary {key} should be false")


def summary(runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "localSourceRuntimeId": runtime["localSourceRuntimeId"],
        "runtimeMode": runtime["runtimeMode"],
        "sourcePolicyId": runtime["runtimePolicy"]["sourcePolicyId"],
        "summary": runtime["summary"],
        "forecastCardReadback": runtime["forecastCardReadback"],
        "cases": [
            {
                "case": item["case"],
                "runtimeStatus": item["runtimeStatus"],
                "nextAction": item["nextAction"],
                "forecastId": item["bindings"]["forecastId"],
                "blockedReasons": item["blockedReasons"],
            }
            for item in runtime["runtimeCases"]
        ],
    }


def write_runtime(runtime: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, runtime, label="local source runtime", regen="python3 scripts/generate_local_source_runtime.py --write")


def check_runtime(runtime: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, runtime, label="local source runtime", regen="python3 scripts/generate_local_source_runtime.py --write")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one local source runtime case")
    parser.add_argument("--check", action="store_true", help="check generated local source runtime drift")
    parser.add_argument("--write", action="store_true", help="write generated local source runtime")
    args = parser.parse_args()
    try:
        runtime = build_runtime()
    except LocalSourceRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_runtime(runtime)
    elif args.check:
        check_runtime(runtime)
    elif args.case:
        row = next(item for item in runtime["runtimeCases"] if item["case"] == args.case)
        sys.stdout.write(render_json(row))
    else:
        sys.stdout.write(render_json(summary(runtime)))


if __name__ == "__main__":
    main()
