#!/usr/bin/env python3
"""Generate or check external source-adapter intake fixtures."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

from generate_source_intake import (
    CASE_REPORT_IDS,
    accepted_case,
    evaluate_intake,
    needs_confirmation_case,
    rejected_case,
    validate_manifest_and_mapping,
)
from generate_setup_benchmark_gate import build_gate
from ope_schema import SPEC, validate_record
from select_setup_method import build_decision


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-adapter-intake"
MATRIX_PATH = GENERATED / "weather-logistics-source-adapter-intake.generated.json"
SCHEMA = SPEC / "source-adapter-intake.schema.json"
SOURCE_ADAPTER_OUTPUT_SCHEMA = SPEC / "source-adapter-output.schema.json"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"
SOURCE_INTAKE_REPORT_SCHEMA = SPEC / "source-intake-report.schema.json"
SETUP_BENCHMARK_GATE_SCHEMA = SPEC / "setup-benchmark-gate.schema.json"
SETUP_METHOD_DECISION_SCHEMA = SPEC / "setup-method-decision.schema.json"
GENERATED_AT = "2026-06-10T04:20:00Z"

CASE_ORDER = ["accepted", "needs_confirmation", "insufficient_data", "rejected", "unsafe"]
CASE_NUMBERS = {
    "accepted": 1301,
    "needs_confirmation": 1302,
    "insufficient_data": 1303,
    "rejected": 1304,
    "unsafe": 1305,
}
SOURCE_INTAKE_REPORT_IDS = {
    "accepted": "sourceintakereport-1301",
    "needs_confirmation": "sourceintakereport-1302",
    "insufficient_data": "sourceintakereport-1303",
    "rejected": "sourceintakereport-1304",
}
SETUP_BENCHMARK_GATE_IDS = {
    "accepted": "setupbenchmarkgate-1301",
    "needs_confirmation": "setupbenchmarkgate-1302",
    "insufficient_data": "setupbenchmarkgate-1303",
    "rejected": "setupbenchmarkgate-1304",
}
SETUP_METHOD_DECISION_IDS = {
    "accepted": "setupmethoddecision-1301",
    "needs_confirmation": "setupmethoddecision-1302",
    "insufficient_data": "setupmethoddecision-1303",
    "rejected": "setupmethoddecision-1304",
}


class SourceAdapterIntakeError(Exception):
    pass


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def source_adapter_output_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-source-adapter-output.generated.json"


def source_intake_report_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-source-intake-report.generated.json"


def setup_benchmark_gate_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-setup-benchmark-gate.generated.json"


def setup_method_decision_path(case: str) -> Path:
    return GENERATED / f"weather-logistics-{case_slug(case)}-setup-method-decision.generated.json"


def clone_case(case: str, manifest: dict[str, Any], field_mapping: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    number = CASE_NUMBERS[case]
    manifest = copy.deepcopy(manifest)
    field_mapping = copy.deepcopy(field_mapping)
    source_id_map: dict[str, str] = {}

    manifest["sourceManifestId"] = f"sourcemanifest-{number}"
    field_mapping["sourceManifestId"] = manifest["sourceManifestId"]
    field_mapping["fieldMappingId"] = f"fieldmapping-{number}"

    for index, source in enumerate(manifest["sources"], start=1):
        original = source["sourceId"]
        source["sourceId"] = f"manifestsource-{number}{index}"
        source_id_map[original] = source["sourceId"]
        source["connectorType"] = "agent_extraction"

    for index, item in enumerate(field_mapping["mappings"], start=1):
        item["mappingId"] = f"mapping-{number}{index}"
        item["sourceId"] = source_id_map[item["sourceId"]]

    for index, item in enumerate(field_mapping["aliasMappings"], start=1):
        item["aliasMappingId"] = f"aliasmapping-{number}{index}"

    validate_manifest_and_mapping(case, manifest, field_mapping)
    return manifest, field_mapping


def insufficient_data_case() -> tuple[dict[str, Any], dict[str, Any]]:
    manifest, field_mapping = accepted_case()
    manifest, field_mapping = clone_case("insufficient_data", manifest, field_mapping)
    for source in manifest["sources"]:
        if source["sourceRole"] != "historical_baseline":
            continue
        source["displayName"] = "External Adapter Tiny Historical Sample"
        source["sourceRef"] = "local://external-adapter/weather-logistics/tiny-history.csv"
        source["contentHash"] = "hash-adapter-tiny-history-001"
        source["rowCount"] = 5
        source["positiveOutcomeCount"] = 0
        for field in source["fieldInventory"]:
            field["sampleCount"] = 5
            field["nonNullCount"] = 5
    validate_manifest_and_mapping("insufficient_data", manifest, field_mapping)
    return manifest, field_mapping


def base_case_inputs() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    accepted_manifest, accepted_mapping = clone_case("accepted", *accepted_case())
    needs_manifest, needs_mapping = clone_case("needs_confirmation", *needs_confirmation_case())
    rejected_manifest, rejected_mapping = clone_case("rejected", *rejected_case())
    unsafe_manifest, unsafe_mapping = clone_case("unsafe", *accepted_case())
    return {
        "accepted": (accepted_manifest, accepted_mapping),
        "needs_confirmation": (needs_manifest, needs_mapping),
        "insufficient_data": insufficient_data_case(),
        "rejected": (rejected_manifest, rejected_mapping),
        "unsafe": (unsafe_manifest, unsafe_mapping),
    }


def has_mapping_confirmation(field_mapping: dict[str, Any]) -> bool:
    return any(
        item["requiresConfirmation"] or item["mappingStatus"] == "proposed"
        for item in field_mapping["mappings"] + field_mapping["aliasMappings"]
    )


def build_source_adapter_output(
    case: str,
    manifest: dict[str, Any],
    field_mapping: dict[str, Any],
) -> dict[str, Any]:
    number = CASE_NUMBERS[case]
    unsafe = case == "unsafe"
    output_status = {
        "accepted": "intake_ready",
        "needs_confirmation": "needs_confirmation",
        "insufficient_data": "intake_ready",
        "rejected": "rejected",
        "unsafe": "rejected",
    }[case]
    next_action = {
        "accepted": "run_source_intake",
        "needs_confirmation": "ask_mapping_confirmation",
        "insufficient_data": "run_source_intake",
        "rejected": "replace_source",
        "unsafe": "replace_source",
    }[case]
    diagnostics = [
        {
            "diagnosticId": f"sourceadapterdiagnostic-{number}1",
            "level": "info",
            "message": "External adapter output was normalized into OPE source manifest and field mapping contracts.",
            "rawDetailIncluded": False,
        }
    ]
    if case == "unsafe":
        diagnostics.append(
            {
                "diagnosticId": f"sourceadapterdiagnostic-{number}2",
                "level": "error",
                "message": "Adapter output crossed credential or raw-row boundaries and is blocked before source intake.",
                "rawDetailIncluded": False,
            }
        )
    elif case == "needs_confirmation":
        diagnostics.append(
            {
                "diagnosticId": f"sourceadapterdiagnostic-{number}2",
                "level": "warning",
                "message": "Agent-inferred field mappings require caller confirmation before forecast execution.",
                "rawDetailIncluded": False,
            }
        )
    elif case == "insufficient_data":
        diagnostics.append(
            {
                "diagnosticId": f"sourceadapterdiagnostic-{number}2",
                "level": "warning",
                "message": "Adapter-provided historical baseline sample is below setup intake thresholds.",
                "rawDetailIncluded": False,
            }
        )

    output = {
        "sourceAdapterOutputId": f"sourceadapteroutput-{number}",
        "generatedAt": GENERATED_AT,
        "outputStatus": output_status,
        "adapter": {
            "adapterId": f"sourceadapter-{number}",
            "displayName": f"Weather logistics external adapter {case_slug(case)} fixture",
            "adapterVersion": "external-intake-v0",
            "implementationLocation": "external_agent",
            "sourceKind": "agent_extraction",
            "ownsForecastSemantics": False,
        },
        "execution": {
            "adapterRunId": f"sourceadapterrun-{number}",
            "executionMode": "external_runtime_capture",
            "startedAt": GENERATED_AT,
            "completedAt": GENERATED_AT,
            "normalChecksOffline": True,
            "liveFetchPerformed": False,
            "credentialsUsed": unsafe,
            "credentialsStored": False,
        },
        "domainBinding": {
            "domainSetupId": manifest["domainSetupId"],
            "domain": manifest["domain"],
            "questionTemplateId": manifest["forecastParameters"]["questionTemplateId"],
            "sourceRoles": [source["sourceRole"] for source in manifest["sources"]],
        },
        "sourceManifest": manifest,
        "fieldMapping": field_mapping,
        "handoffBoundary": {
            "canEnterSourceIntake": not unsafe,
            "sourceIntakeRequired": True,
            "mappingConfirmationRequired": has_mapping_confirmation(field_mapping),
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "allowedNextCommands": [
                "python3 scripts/ope.py source-adapter-intake --check",
                "python3 scripts/ope.py source-intake --check",
            ]
            if not unsafe
            else ["replace unsafe external connector output before running OPE intake"],
        },
        "provenanceSummary": {
            "sourceCount": len(manifest["sources"]),
            "rowCount": sum(source["rowCount"] for source in manifest["sources"]),
            "contentHashesStored": True,
            "rawRowsIncluded": unsafe,
            "allEvidenceClaimed": False,
            "diagnostics": diagnostics,
        },
        "controls": {
            "readOnly": True,
            "forecastGenerationAllowed": False,
            "forecastArtifactsCreated": False,
            "sourceIntakeAlreadyRun": False,
            "credentialStorageImplemented": False,
            "promptVisibleCredentialsAccepted": unsafe,
            "rawPrivateRowsStored": unsafe,
            "sanitizedErrorsOnly": not unsafe,
        },
        "nextAction": next_action,
        "warnings": [
            "Source adapter outputs do not create forecast artifacts or scoring records.",
            "Connector execution, credentials, and live fetching stay outside OPE core for this MVP path.",
        ],
    }
    validate_source_adapter_output(case, output)
    return output


def validate_source_adapter_output(case: str, output: dict[str, Any]) -> None:
    errors = validate_record(output, SOURCE_ADAPTER_OUTPUT_SCHEMA)
    if errors:
        raise SourceAdapterIntakeError(f"{case} source adapter output schema validation failed: {errors[0]}")
    manifest_errors = validate_record(output["sourceManifest"], SOURCE_MANIFEST_SCHEMA)
    if manifest_errors:
        raise SourceAdapterIntakeError(f"{case} embedded source manifest validation failed: {manifest_errors[0]}")
    mapping_errors = validate_record(output["fieldMapping"], FIELD_MAPPING_SCHEMA)
    if mapping_errors:
        raise SourceAdapterIntakeError(f"{case} embedded field mapping validation failed: {mapping_errors[0]}")
    if output["fieldMapping"]["sourceManifestId"] != output["sourceManifest"]["sourceManifestId"]:
        raise SourceAdapterIntakeError(f"{case} embedded manifest and field mapping are not bound")
    if output["adapter"]["ownsForecastSemantics"]:
        raise SourceAdapterIntakeError(f"{case} source adapter must not own forecast semantics")
    if output["controls"]["forecastArtifactsCreated"] or output["controls"]["forecastGenerationAllowed"]:
        raise SourceAdapterIntakeError(f"{case} source adapter output must not create or allow forecasts")
    if output["controls"]["credentialStorageImplemented"] or output["execution"]["credentialsStored"]:
        raise SourceAdapterIntakeError(f"{case} source adapter output must not store credentials")
    if case != "unsafe":
        if output["execution"]["credentialsUsed"] or output["controls"]["promptVisibleCredentialsAccepted"]:
            raise SourceAdapterIntakeError(f"{case} safe adapter output crossed credential boundary")
        if output["provenanceSummary"]["rawRowsIncluded"] or output["controls"]["rawPrivateRowsStored"]:
            raise SourceAdapterIntakeError(f"{case} safe adapter output crossed raw-row boundary")
    else:
        if output["handoffBoundary"]["canEnterSourceIntake"]:
            raise SourceAdapterIntakeError("unsafe adapter output must be blocked before source intake")


def build_report_gate_decision(
    case: str,
    output: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    if case == "unsafe":
        return None, None, None
    CASE_REPORT_IDS[case] = SOURCE_INTAKE_REPORT_IDS[case]
    report = evaluate_intake(case, output["sourceManifest"], output["fieldMapping"])
    setup_case = "rejected" if case == "insufficient_data" else case
    gate = build_gate(setup_case, report, gate_id=SETUP_BENCHMARK_GATE_IDS[case])
    decision = build_decision(
        setup_case,
        report,
        gate,
        decision_id=SETUP_METHOD_DECISION_IDS[case],
    )
    validate_generated_artifacts(case, report, gate, decision)
    return report, gate, decision


def validate_generated_artifacts(
    case: str,
    report: dict[str, Any],
    gate: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    for label, record, schema in [
        ("source intake report", report, SOURCE_INTAKE_REPORT_SCHEMA),
        ("setup benchmark gate", gate, SETUP_BENCHMARK_GATE_SCHEMA),
        ("setup method decision", decision, SETUP_METHOD_DECISION_SCHEMA),
    ]:
        errors = validate_record(record, schema)
        if errors:
            raise SourceAdapterIntakeError(f"{case} {label} validation failed: {errors[0]}")


def validation_summary(output: dict[str, Any], report: dict[str, Any] | None) -> dict[str, Any]:
    unsafe = output["controls"]["promptVisibleCredentialsAccepted"] or output["provenanceSummary"]["rawRowsIncluded"]
    if unsafe:
        leakage_status = "blocked_before_intake"
        credential_status = "blocked_before_intake"
    elif report is not None and any(
        source["checks"]["leakageRisk"]["status"] == "failed"
        for source in report["sourceDecisions"]
    ):
        leakage_status = "failed"
        credential_status = "passed"
    else:
        leakage_status = "passed"
        credential_status = "passed"

    return {
        "sourceAdapterOutputSchemaValid": True,
        "manifestValid": True,
        "fieldMappingValid": True,
        "provenanceSummaryValid": output["provenanceSummary"]["contentHashesStored"],
        "sourceRolesValid": report is None or all(
            source["decision"] != "rejected" or "unknown_source_role" not in source["reasonCodes"]
            for source in report["sourceDecisions"]
        ),
        "freshnessValid": report is None or not any(
            source["checks"]["sourceFreshness"]["status"] == "failed"
            for source in report["sourceDecisions"]
        ),
        "leakageStatus": leakage_status,
        "credentialBoundaryStatus": credential_status,
        "rawRowsIncluded": output["provenanceSummary"]["rawRowsIncluded"],
        "allEvidenceClaimed": output["provenanceSummary"]["allEvidenceClaimed"],
    }


def rejection_reasons(report: dict[str, Any] | None, output: dict[str, Any]) -> list[str]:
    reasons: set[str] = set()
    if output["controls"]["promptVisibleCredentialsAccepted"]:
        reasons.add("prompt_visible_credentials_not_allowed")
    if output["controls"]["rawPrivateRowsStored"] or output["provenanceSummary"]["rawRowsIncluded"]:
        reasons.add("raw_private_rows_not_allowed")
    if report is not None:
        for source in report["sourceDecisions"]:
            if source["decision"] == "rejected":
                reasons.update(source["reasonCodes"])
        for mapping in report["mappingDecisions"]:
            if mapping["decision"] in {"proposed", "rejected"}:
                reasons.update(mapping["reasonCodes"])
    return sorted(reasons)


def adapter_status(case: str, report: dict[str, Any] | None, output: dict[str, Any]) -> str:
    if case == "unsafe":
        return "unsafe_blocked"
    if case == "rejected":
        return "rejected"
    if report is None:
        return "rejected"
    reasons = rejection_reasons(report, output)
    if report["intakeStatus"] == "accepted":
        return "accepted"
    if report["intakeStatus"] == "needs_confirmation":
        return "needs_confirmation"
    if {"insufficient_comparable_rows", "insufficient_positive_outcomes"} & set(reasons):
        return "insufficient_data"
    return "rejected"


def next_action_for_status(status: str) -> str:
    return {
        "accepted": "proceed_to_method_gating",
        "needs_confirmation": "ask_mapping_confirmation",
        "insufficient_data": "collect_more_data",
        "rejected": "replace_source",
        "unsafe_blocked": "stop_unsafe_connector",
    }[status]


def method_status_for(
    status: str,
    decision: dict[str, Any] | None,
) -> str:
    if status == "unsafe_blocked":
        return "blocked_unsafe"
    if decision is None:
        return "not_entered_source_intake"
    if status == "needs_confirmation":
        return "needs_mapping_confirmation"
    if status == "insufficient_data":
        return "needs_more_data"
    decision_status = decision["decisionStatus"]
    if decision_status in {"method_selected", "baseline_selected"}:
        return decision_status
    return "rejected"


def build_case_row(
    case: str,
    output: dict[str, Any],
    report: dict[str, Any] | None,
    gate: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> dict[str, Any]:
    status = adapter_status(case, report, output)
    reasons = rejection_reasons(report, output)
    selected_method = decision["selectedMethodClass"] if decision is not None else None
    return {
        "caseId": f"sourceadapterintakecase-{CASE_NUMBERS[case]}",
        "case": status,
        "sourceAdapterOutputId": output["sourceAdapterOutputId"],
        "sourceAdapterOutputPath": rel(source_adapter_output_path(case)),
        "outputStatus": output["outputStatus"],
        "sourceKind": output["adapter"]["sourceKind"],
        "implementationLocation": output["adapter"]["implementationLocation"],
        "executionMode": output["execution"]["executionMode"],
        "validationSummary": validation_summary(output, report),
        "intakeRoute": {
            "canEnterSourceIntake": output["handoffBoundary"]["canEnterSourceIntake"],
            "sourceIntakeReportId": report["sourceIntakeReportId"] if report is not None else None,
            "sourceIntakeStatus": report["intakeStatus"] if report is not None else None,
            "adapterIntakeStatus": status,
            "nextAction": next_action_for_status(status),
        },
        "methodGateSummary": {
            "setupBenchmarkGateId": gate["setupBenchmarkGateId"] if gate is not None else None,
            "setupMethodDecisionId": decision["setupMethodDecisionId"] if decision is not None else None,
            "methodGateStatus": method_status_for(status, decision),
            "selectedMethodClass": selected_method,
            "forecastArtifactsCreated": False,
            "qualityClaimAllowed": False,
        },
        "generatedArtifacts": {
            "sourceAdapterOutput": rel(source_adapter_output_path(case)),
            "sourceIntakeReport": rel(source_intake_report_path(case)) if report is not None else None,
            "setupBenchmarkGate": rel(setup_benchmark_gate_path(case)) if gate is not None else None,
            "setupMethodDecision": rel(setup_method_decision_path(case)) if decision is not None else None,
        },
        "rejectionReasons": reasons,
        "requiredActions": required_actions(status, report),
    }


def required_actions(status: str, report: dict[str, Any] | None) -> list[str]:
    if status == "accepted":
        return ["Proceed to checked setup method gate before forecast execution."]
    if status == "unsafe_blocked":
        return ["Stop the connector handoff and replace the output with a sanitized source-adapter output."]
    if status == "insufficient_data":
        return ["Collect more comparable historical rows and positive outcomes before method selection."]
    if status == "needs_confirmation":
        return ["Confirm agent-inferred field and alias mappings before method selection."]
    actions = list(report["requiredActions"] if report is not None else [])
    if not actions:
        actions.append("Replace the rejected source-adapter output before retrying intake.")
    return actions


def build_records() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any] | None],
    dict[str, dict[str, Any] | None],
    dict[str, dict[str, Any] | None],
    dict[str, Any],
]:
    cases = base_case_inputs()
    outputs: dict[str, dict[str, Any]] = {}
    reports: dict[str, dict[str, Any] | None] = {}
    gates: dict[str, dict[str, Any] | None] = {}
    decisions: dict[str, dict[str, Any] | None] = {}
    rows: list[dict[str, Any]] = []
    for case in CASE_ORDER:
        manifest, field_mapping = cases[case]
        output = build_source_adapter_output(case, manifest, field_mapping)
        report, gate, decision = build_report_gate_decision(case, output)
        outputs[case] = output
        reports[case] = report
        gates[case] = gate
        decisions[case] = decision
        rows.append(build_case_row(case, output, report, gate, decision))

    summary_counts = {
        "acceptedCount": sum(1 for row in rows if row["case"] == "accepted"),
        "needsConfirmationCount": sum(1 for row in rows if row["case"] == "needs_confirmation"),
        "insufficientDataCount": sum(1 for row in rows if row["case"] == "insufficient_data"),
        "rejectedCount": sum(1 for row in rows if row["case"] == "rejected"),
        "unsafeBlockedCount": sum(1 for row in rows if row["case"] == "unsafe_blocked"),
    }
    matrix = {
        "sourceAdapterIntakeId": "sourceadapterintake-1301",
        "generatedAt": GENERATED_AT,
        "domain": "weather-logistics",
        "intakeMode": "external_adapter_output_to_checked_intake",
        "contractBindings": {
            "sourceAdapterOutputSchema": "spec/source-adapter-output.schema.json",
            "sourceManifestSchema": "spec/source-manifest.schema.json",
            "fieldMappingSchema": "spec/field-mapping.schema.json",
            "sourceIntakeReportSchema": "spec/source-intake-report.schema.json",
            "setupBenchmarkGateSchema": "spec/setup-benchmark-gate.schema.json",
            "setupMethodDecisionSchema": "spec/setup-method-decision.schema.json",
            "existingTransitAdapterOutputPath": (
                "spec/fixtures/generated/source-adapter-output/"
                "weather-transit-delays-source-adapter-output.generated.json"
            ),
        },
        "intakeCases": rows,
        "summary": {
            "caseCount": len(rows),
            **summary_counts,
            "sourceIntakeReportsGenerated": sum(1 for report in reports.values() if report is not None),
            "methodDecisionsGenerated": sum(1 for decision in decisions.values() if decision is not None),
        },
        "claimBoundary": {
            "executesConnector": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "acceptsPromptVisibleCredentials": False,
            "acceptsRawPrivateRows": False,
            "createsForecastArtifacts": False,
            "createsScoringRecords": False,
            "bypassesSourceIntake": False,
            "bypassesMethodGate": False,
            "claimsConnectorSafety": False,
        },
        "readSurface": {
            "command": "python3 scripts/ope.py source-adapter-intake",
            "normalChecksOffline": True,
            "mutatesExternalSystems": False,
            "requiresCredentials": False,
            "writesOnlyGeneratedFixtures": True,
        },
        "warnings": [
            "Source adapter intake validates sanitized connector handoffs; it does not execute connector code.",
            "Unsafe adapter outputs are blocked before source intake and must not be repaired inside OPE core.",
            "Accepted outputs still need setup benchmark and method decisions before forecast execution.",
        ],
    }
    validate_matrix(matrix)
    return outputs, reports, gates, decisions, matrix


def validate_matrix(matrix: dict[str, Any]) -> None:
    errors = validate_record(matrix, SCHEMA)
    if errors:
        raise SourceAdapterIntakeError(f"source adapter intake schema validation failed: {errors[0]}")
    statuses = [row["case"] for row in matrix["intakeCases"]]
    expected = ["accepted", "needs_confirmation", "insufficient_data", "rejected", "unsafe_blocked"]
    if statuses != expected:
        raise SourceAdapterIntakeError(f"source adapter intake case status drifted: {statuses}")
    boundary = matrix["claimBoundary"]
    for key, value in boundary.items():
        if value is not False:
            raise SourceAdapterIntakeError(f"claim boundary {key} should be false")
    accepted = matrix["intakeCases"][0]
    if accepted["methodGateSummary"]["methodGateStatus"] != "method_selected":
        raise SourceAdapterIntakeError("accepted adapter output should reach method selection")
    unsafe = matrix["intakeCases"][-1]
    if unsafe["intakeRoute"]["canEnterSourceIntake"] or unsafe["intakeRoute"]["sourceIntakeReportId"] is not None:
        raise SourceAdapterIntakeError("unsafe adapter output should not enter source intake")


def summary(matrix: dict[str, Any]) -> dict[str, Any]:
    return {
        "sourceAdapterIntakeId": matrix["sourceAdapterIntakeId"],
        "domain": matrix["domain"],
        "caseCount": matrix["summary"]["caseCount"],
        "cases": [
            {
                "case": row["case"],
                "sourceAdapterOutputId": row["sourceAdapterOutputId"],
                "sourceIntakeStatus": row["intakeRoute"]["sourceIntakeStatus"],
                "nextAction": row["intakeRoute"]["nextAction"],
                "methodGateStatus": row["methodGateSummary"]["methodGateStatus"],
            }
            for row in matrix["intakeCases"]
        ],
    }


def expected_outputs(
    outputs: dict[str, dict[str, Any]],
    reports: dict[str, dict[str, Any] | None],
    gates: dict[str, dict[str, Any] | None],
    decisions: dict[str, dict[str, Any] | None],
    matrix: dict[str, Any],
) -> dict[Path, str]:
    expected: dict[Path, str] = {MATRIX_PATH: render_json(matrix)}
    for case, output in outputs.items():
        expected[source_adapter_output_path(case)] = render_json(output)
        if reports[case] is not None:
            expected[source_intake_report_path(case)] = render_json(reports[case])
        if gates[case] is not None:
            expected[setup_benchmark_gate_path(case)] = render_json(gates[case])
        if decisions[case] is not None:
            expected[setup_method_decision_path(case)] = render_json(decisions[case])
    return expected


def write_outputs(expected: dict[Path, str]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    expected_names = {path.name for path in expected}
    for path in GENERATED.glob("*.generated.json"):
        if path.name not in expected_names:
            path.unlink()
    for path, contents in expected.items():
        path.write_text(contents, encoding="utf-8")
    print("generated source adapter intake fixtures")


def check_outputs(expected: dict[Path, str]) -> None:
    errors: list[str] = []
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing source adapter intake output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"source adapter intake drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_source_adapter_intake.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source adapter intake fixtures")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source adapter intake case row")
    parser.add_argument("--check", action="store_true", help="check generated source adapter intake drift")
    parser.add_argument("--write", action="store_true", help="write generated source adapter intake fixtures")
    args = parser.parse_args()
    try:
        outputs, reports, gates, decisions, matrix = build_records()
    except SourceAdapterIntakeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    expected = expected_outputs(outputs, reports, gates, decisions, matrix)
    if args.write:
        write_outputs(expected)
    elif args.check:
        check_outputs(expected)
    elif args.case:
        row = next(item for item in matrix["intakeCases"] if item["case"] == args.case or item["case"] == f"{args.case}_blocked")
        sys.stdout.write(render_json(row))
    else:
        sys.stdout.write(render_json(summary(matrix)))


if __name__ == "__main__":
    main()
