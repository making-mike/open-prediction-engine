#!/usr/bin/env python3
"""Generate or check builder-draft source-intake handoff records."""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path
from typing import Any

from build_source_manifest import (
    LOCAL_FIXTURES,
    build_case as build_source_case,
    build_from_inputs,
    render_json,
)
from generate_source_intake import CASE_REPORT_IDS, evaluate_intake, validate_manifest_and_mapping
from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "source-handoff"
HANDOFF_SCHEMA = SPEC / "source-intake-handoff.schema.json"
BUILD_SCHEMA = SPEC / "source-manifest-build.schema.json"
SOURCE_MANIFEST_SCHEMA = SPEC / "source-manifest.schema.json"
FIELD_MAPPING_SCHEMA = SPEC / "field-mapping.schema.json"
REPORT_SCHEMA = SPEC / "source-intake-report.schema.json"
GENERATED_AT = "2026-06-06T18:10:00Z"

CASE_ORDER = [
    "unconfirmed_builder_draft",
    "confirmed_builder_draft",
    "insufficient_confirmed_builder_draft",
    "contains_secret",
    "unsupported_format",
    "oversized",
    "leakage",
]

HANDOFF_IDS = {
    "unconfirmed_builder_draft": "sourceintakehandoff-001",
    "confirmed_builder_draft": "sourceintakehandoff-002",
    "insufficient_confirmed_builder_draft": "sourceintakehandoff-003",
    "contains_secret": "sourceintakehandoff-004",
    "unsupported_format": "sourceintakehandoff-005",
    "oversized": "sourceintakehandoff-006",
    "leakage": "sourceintakehandoff-007",
}

HANDOFF_REPORT_IDS = {
    "unconfirmed_builder_draft": "sourceintakereport-101",
    "confirmed_builder_draft": "sourceintakereport-102",
    "insufficient_confirmed_builder_draft": "sourceintakereport-103",
}
CASE_REPORT_IDS.update(HANDOFF_REPORT_IDS)


class SourceIntakeHandoffError(Exception):
    pass


def case_slug(case: str) -> str:
    return case.replace("_", "-")


def paths_for(case: str) -> dict[str, Path]:
    slug = case_slug(case)
    return {
        "handoff": GENERATED / f"weather-logistics-{slug}-source-intake-handoff.generated.json",
        "build": GENERATED / f"weather-logistics-{slug}-source-manifest-build.generated.json",
        "manifest": GENERATED / f"weather-logistics-{slug}-source-manifest.json",
        "mapping": GENERATED / f"weather-logistics-{slug}-field-mapping.json",
        "report": GENERATED / f"weather-logistics-{slug}-source-intake-report.generated.json",
    }


def relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_or_raise(record: dict[str, Any], schema: Path, label: str) -> None:
    errors = validate_record(record, schema)
    if errors:
        raise SourceIntakeHandoffError(f"{label} schema validation failed: {errors[0]}")


def confirm_mapping(field_mapping: dict[str, Any], field_mapping_id: str | None = None) -> dict[str, Any]:
    confirmed = copy.deepcopy(field_mapping)
    if field_mapping_id is not None:
        confirmed["fieldMappingId"] = field_mapping_id
    for item in confirmed["mappings"]:
        if item["requiresConfirmation"] or item["mappingStatus"] == "proposed":
            item["mappingOrigin"] = "user_provided"
            item["mappingStatus"] = "confirmed"
            item["requiresConfirmation"] = False
            item["confidence"] = 1.0
            item["validationNotes"] = ["Caller confirmed the builder-proposed mapping before source intake."]
    for item in confirmed["aliasMappings"]:
        if item["requiresConfirmation"] or item["mappingStatus"] == "proposed":
            item["mappingOrigin"] = "user_provided"
            item["mappingStatus"] = "confirmed"
            item["requiresConfirmation"] = False
    return confirmed


def mapping_summary(field_mapping: dict[str, Any] | None) -> dict[str, Any]:
    if field_mapping is None:
        return {
            "totalMappings": 0,
            "proposedMappingCount": 0,
            "confirmedMappingCount": 0,
            "agentInferredMappingCount": 0,
            "requiresConfirmation": False,
        }
    all_mappings = field_mapping["mappings"] + field_mapping["aliasMappings"]
    proposed = [
        item
        for item in all_mappings
        if item["requiresConfirmation"] or item["mappingStatus"] == "proposed"
    ]
    confirmed = [item for item in all_mappings if item["mappingStatus"] == "confirmed"]
    inferred = [item for item in all_mappings if item["mappingOrigin"] == "agent_inferred"]
    return {
        "totalMappings": len(all_mappings),
        "proposedMappingCount": len(proposed),
        "confirmedMappingCount": len(confirmed),
        "agentInferredMappingCount": len(inferred),
        "requiresConfirmation": bool(proposed),
    }


def builder_rejection_summary(build: dict[str, Any]) -> dict[str, Any]:
    rejected = [
        item
        for item in build["inputFiles"]
        if item["inspectionStatus"] == "rejected"
    ]
    reasons = sorted(
        {
            reason
            for item in rejected
            for reason in item["reasonCodes"]
        }
    )
    return {
        "rejectedInputCount": len(rejected),
        "reasonCodes": reasons,
    }


def intake_reason_codes(report: dict[str, Any] | None) -> set[str]:
    if report is None:
        return set()
    reasons: set[str] = set()
    for source in report["sourceDecisions"]:
        reasons.update(source["reasonCodes"])
    for mapping in report["mappingDecisions"]:
        reasons.update(mapping["reasonCodes"])
    return reasons


def next_action(
    build: dict[str, Any],
    report: dict[str, Any] | None,
    summary: dict[str, Any],
) -> tuple[str, str]:
    builder_rejections = builder_rejection_summary(build)
    if builder_rejections["rejectedInputCount"] > 0:
        return "blocked_by_builder_rejection", "replace_rejected_sources"
    if summary["requiresConfirmation"] or (report and report["intakeStatus"] == "needs_confirmation"):
        return "needs_mapping_confirmation", "ask_mapping_confirmation"
    reasons = intake_reason_codes(report)
    if {"insufficient_comparable_rows", "insufficient_positive_outcomes"} & reasons:
        return "needs_more_data", "collect_more_data"
    if report and report["intakeStatus"] in {"accepted", "accepted_partial"}:
        return "ready_for_method_gating", "proceed_to_method_gating"
    return "blocked_by_builder_rejection", "replace_rejected_sources"


def actions_for(
    handoff_status: str,
    next_action_value: str,
    report: dict[str, Any] | None,
    builder_rejections: dict[str, Any],
) -> list[str]:
    if next_action_value == "ask_mapping_confirmation":
        return ["Ask the caller to confirm proposed field and alias mappings before forecast execution."]
    if next_action_value == "proceed_to_method_gating":
        return ["Pass the accepted source-intake report to setup benchmark and method gates."]
    if next_action_value == "collect_more_data":
        return ["Collect enough comparable historical rows and positive outcomes before method gating."]
    if builder_rejections["reasonCodes"]:
        return [f"Replace rejected builder inputs before source intake: {', '.join(builder_rejections['reasonCodes'])}."]
    if report is not None:
        return list(report["requiredActions"])
    return [f"Resolve handoff status {handoff_status} before source intake."]


def warnings_for(report: dict[str, Any] | None) -> list[str]:
    warnings = [
        "Source-builder handoffs do not create forecast artifacts.",
        "Setup method gates are still required after accepted source intake.",
    ]
    if report is not None:
        warnings.extend(report["warnings"])
    return list(dict.fromkeys(warnings))


def prepare_case(case: str) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    if case in {"unconfirmed_builder_draft", "confirmed_builder_draft"}:
        build, manifest, field_mapping = build_source_case("local_draft")
        if case == "confirmed_builder_draft":
            assert field_mapping is not None
            field_mapping = confirm_mapping(field_mapping, "fieldmappingdraft-102")
    elif case == "insufficient_confirmed_builder_draft":
        build, manifest, field_mapping = build_from_inputs(
            103,
            case,
            [
                ("weather_forecast", LOCAL_FIXTURES / "weather-forecast.json"),
                ("historical_baseline", LOCAL_FIXTURES / "tiny-history.csv"),
                ("declared_operations_outcome", LOCAL_FIXTURES / "outcome.csv"),
            ],
            output_dir=GENERATED,
            mapping_hints={
                ("declared_operations_outcome", "date"): "service_date",
            },
        )
        assert field_mapping is not None
        field_mapping = confirm_mapping(field_mapping)
    else:
        source_case = {
            "contains_secret": "contains_secret",
            "unsupported_format": "unsupported_format",
            "oversized": "oversized",
            "leakage": "leakage",
        }[case]
        build, manifest, field_mapping = build_source_case(source_case)

    report = None
    if manifest is not None and field_mapping is not None:
        validate_manifest_and_mapping(case, manifest, field_mapping)
        report = evaluate_intake(case, manifest, field_mapping)
    return build, manifest, field_mapping, report


def build_handoff(case: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    build, manifest, field_mapping, report = prepare_case(case)
    paths = paths_for(case)
    summary = mapping_summary(field_mapping)
    builder_rejections = builder_rejection_summary(build)
    handoff_status, next_action_value = next_action(build, report, summary)
    draft_artifacts = {
        "sourceManifestBuildPath": relative(paths["build"]),
        "sourceManifestPath": relative(paths["manifest"]) if manifest is not None else None,
        "fieldMappingPath": relative(paths["mapping"]) if field_mapping is not None else None,
        "sourceIntakeReportPath": relative(paths["report"]) if report is not None else None,
    }
    handoff = {
        "sourceIntakeHandoffId": HANDOFF_IDS[case],
        "generatedAt": GENERATED_AT,
        "case": case,
        "domainSetupId": build["domainSetupId"],
        "domain": build["domain"],
        "sourceManifestBuildId": build["sourceManifestBuildId"],
        "handoffStatus": handoff_status,
        "nextAction": next_action_value,
        "canEnterSourceIntake": build["canEnterSourceIntake"],
        "forecastGenerationAllowed": bool(report and report["forecastGenerationAllowed"]),
        "sourceManifestId": manifest["sourceManifestId"] if manifest is not None else None,
        "fieldMappingId": field_mapping["fieldMappingId"] if field_mapping is not None else None,
        "sourceIntakeReportId": report["sourceIntakeReportId"] if report is not None else None,
        "sourceIntakeStatus": report["intakeStatus"] if report is not None else None,
        "mappingSummary": summary,
        "builderRejectionSummary": builder_rejections,
        "draftArtifacts": draft_artifacts,
        "requiredActions": actions_for(handoff_status, next_action_value, report, builder_rejections),
        "warnings": warnings_for(report),
    }
    validate_or_raise(build, BUILD_SCHEMA, "source manifest build")
    if manifest is not None:
        validate_or_raise(manifest, SOURCE_MANIFEST_SCHEMA, "source manifest")
    if field_mapping is not None:
        validate_or_raise(field_mapping, FIELD_MAPPING_SCHEMA, "field mapping")
    if report is not None:
        validate_or_raise(report, REPORT_SCHEMA, "source intake report")
    validate_or_raise(handoff, HANDOFF_SCHEMA, "source intake handoff")
    return handoff, build, manifest, field_mapping, report


def build_handoffs() -> dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]]:
    return {
        case: build_handoff(case)
        for case in CASE_ORDER
    }


def write_outputs(records: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for case, (handoff, build, manifest, field_mapping, report) in records.items():
        paths = paths_for(case)
        paths["handoff"].write_text(render_json(handoff), encoding="utf-8")
        paths["build"].write_text(render_json(build), encoding="utf-8")
        if manifest is not None:
            paths["manifest"].write_text(render_json(manifest), encoding="utf-8")
        if field_mapping is not None:
            paths["mapping"].write_text(render_json(field_mapping), encoding="utf-8")
        if report is not None:
            paths["report"].write_text(render_json(report), encoding="utf-8")
    print("generated source intake handoff records")


def check_outputs(records: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]]) -> None:
    expected: dict[Path, str] = {}
    for case, (handoff, build, manifest, field_mapping, report) in records.items():
        paths = paths_for(case)
        expected[paths["handoff"]] = render_json(handoff)
        expected[paths["build"]] = render_json(build)
        if manifest is not None:
            expected[paths["manifest"]] = render_json(manifest)
        if field_mapping is not None:
            expected[paths["mapping"]] = render_json(field_mapping)
        if report is not None:
            expected[paths["report"]] = render_json(report)
    errors = []
    for path, contents in expected.items():
        if not path.exists():
            errors.append(f"missing source intake handoff output: {path}")
            continue
        if path.read_text(encoding="utf-8") != contents:
            errors.append(f"source intake handoff drift: {path}")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print("run `python3 scripts/generate_source_intake_handoff.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked source intake handoff records")


def summary(records: dict[str, tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]]) -> dict[str, Any]:
    return {
        "count": len(records),
        "handoffs": [
            {
                "case": case,
                "sourceIntakeHandoffId": handoff["sourceIntakeHandoffId"],
                "handoffStatus": handoff["handoffStatus"],
                "nextAction": handoff["nextAction"],
                "sourceIntakeStatus": handoff["sourceIntakeStatus"],
                "forecastGenerationAllowed": handoff["forecastGenerationAllowed"],
            }
            for case, (handoff, _build, _manifest, _mapping, _report) in records.items()
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_ORDER, help="print one source intake handoff record")
    parser.add_argument("--check", action="store_true", help="check generated source intake handoff drift")
    parser.add_argument("--write", action="store_true", help="write generated source intake handoff records")
    args = parser.parse_args()
    try:
        records = build_handoffs()
    except SourceIntakeHandoffError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_outputs(records)
    elif args.check:
        check_outputs(records)
    elif args.case:
        sys.stdout.write(render_json(records[args.case][0]))
    else:
        sys.stdout.write(render_json(summary(records)))


if __name__ == "__main__":
    main()
