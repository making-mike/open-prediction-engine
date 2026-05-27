#!/usr/bin/env python3
"""Generate or check the local OPE release manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated"
MANIFEST_PATH = GENERATED / "release-manifest.generated.json"
RECORD_INDEX = GENERATED / "record-index.generated.json"
PIPELINE_OUTCOME = GENERATED / "pipeline-resolution" / "weather-logistics-pipeline-resolution-outcome-summary.generated.json"
LIVE_OUTCOME = GENERATED / "live-outcome" / "live-weather-logistics-outcome-summary.generated.json"
AUTO_EVIDENCE_OUTCOME = (
    GENERATED
    / "auto-evidence-resolution"
    / "weather-logistics-auto-evidence-resolution-outcome-summary.generated.json"
)
SOURCE_HANDOFF_OUTCOME = (
    GENERATED
    / "source-handoff-resolution"
    / "weather-logistics-source-handoff-resolution-outcome-summary.generated.json"
)
SCHEMA = SPEC / "release-manifest.schema.json"
GENERATED_AT = "2026-06-06T11:00:00Z"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def schema_files() -> list[str]:
    return [
        str(path.relative_to(ROOT))
        for path in sorted(SPEC.glob("*.schema.json"))
    ]


def read_surfaces(record_index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "recordType": record_set["recordType"],
            "count": record_set["count"],
        }
        for record_set in record_index["recordSets"]
    ]


def build_manifest() -> dict[str, Any]:
    record_index = load_json(RECORD_INDEX)
    pipeline_outcome = load_json(PIPELINE_OUTCOME)
    live_outcome = load_json(LIVE_OUTCOME)
    auto_evidence_outcome = load_json(AUTO_EVIDENCE_OUTCOME)
    source_handoff_outcome = load_json(SOURCE_HANDOFF_OUTCOME)
    schemas = schema_files()
    manifest = {
        "releaseManifestId": "releasemanifest-001",
        "generatedAt": GENERATED_AT,
        "project": {
            "name": "open-prediction-engine",
            "runtime": "python3-standard-library",
            "packageManager": "none",
        },
        "releaseStatus": {
            "status": "fixture_ready",
            "networkApiImplemented": False,
            "hostedServiceImplemented": False,
            "liveCalibrationClaimAllowed": False,
        },
        "ci": {
            "provider": "github_actions",
            "workflowPath": ".github/workflows/release-check.yml",
            "releaseCheckCommand": "python3 scripts/release_check.py",
            "compileCommand": "python3 -m py_compile scripts/*.py",
        },
        "commands": {
            "setupCheck": "python3 --version",
            "test": "python3 scripts/run_checks.py",
            "releaseCheck": "python3 scripts/release_check.py",
            "cli": "python3 scripts/ope.py",
        },
        "contracts": {
            "schemaFileCount": len(schemas),
            "schemaFiles": schemas,
        },
        "readSurfaces": read_surfaces(record_index),
        "claimBoundaries": {
            "domain": "weather-logistics",
            "minimumCalibrationSampleSize": pipeline_outcome["minimumCalibrationSampleSize"],
            "resolvedPipelineOutcomes": pipeline_outcome["resolvedComparablePipelineOutcomes"],
            "resolvedLiveOutcomes": live_outcome["resolvedComparableLiveOutcomes"],
            "resolvedAutoEvidenceOutcomes": auto_evidence_outcome["resolvedComparableAutoEvidenceOutcomes"],
            "resolvedSourceHandoffOutcomes": source_handoff_outcome["resolvedComparableSourceHandoffOutcomes"],
            "qualityClaimStatus": "not_enough_resolved_comparable_outcomes",
        },
        "nonGoals": [
            "network_api",
            "hosted_service",
            "production_agent_adapter_runtime",
            "production_live_data_workflow",
            "production_auto_evidence_fetching",
            "production_forecast_use_of_live_connector_results",
            "hosted_scheduler_runtime",
            "os_scheduler_installation",
            "public_forecast_use_of_local_live_drafts",
            "public_forecast_use_of_unapproved_source_builder_drafts",
            "public_forecast_use_of_unapproved_source_handoff_drafts",
            "generic_private_api_database_runtime",
            "generic_manual_upload_runtime",
            "private_source_adapter_execution",
            "private_source_adapter_outcome_execution",
            "private_source_adapter_bridge_execution",
            "private_setup_request_execution",
            "private_setup_first_action_execution",
            "private_setup_first_action_runbook_execution",
            "private_setup_agent_bundle_execution",
            "private_setup_source_builder_forecast_execution",
            "private_setup_source_builder_public_read_records",
            "private_setup_source_handoff_forecast_execution",
            "private_setup_source_handoff_public_read_records",
            "private_setup_method_gate_forecast_execution",
            "private_setup_method_gate_public_read_records",
            "private_setup_forecast_execution_from_blocked_cases",
            "private_setup_forecast_execution_resolution",
            "private_setup_forecast_execution_scoring",
            "private_setup_forecast_execution_live_fetch",
            "private_setup_forecast_readback_private_api",
            "private_setup_forecast_readback_new_semantics",
            "private_setup_forecast_readback_quality_claim",
            "private_setup_adapter_chain_runbook_execution",
            "private_setup_adapter_chain_runbook_adapter_calls",
            "private_setup_adapter_chain_runbook_artifact_creation",
            "private_setup_adapter_runbook_execution",
            "private_setup_adapter_runbook_adapter_calls",
            "private_setup_adapter_runbook_artifact_creation",
            "private_setup_adapter_conformance_matrix_execution",
            "private_setup_adapter_conformance_matrix_artifact_creation",
            "private_setup_adapter_conformance_summary_execution",
            "private_setup_adapter_conformance_summary_artifact_creation",
            "private_source_adapter_guidance_execution",
            "private_source_adapter_guidance_source_reads",
            "private_source_adapter_guidance_artifact_creation",
            "private_source_kind_selection_execution",
            "private_source_kind_selection_commands",
            "private_source_kind_selection_source_reads",
            "private_source_kind_selection_artifact_creation",
            "private_source_kind_selection_forecast_execution",
            "private_source_kind_selection_scoring",
            "private_source_kind_query_matrix_execution",
            "private_source_kind_query_matrix_artifact_creation",
            "resolution_runtime_reliability_execution",
            "resolution_runtime_reliability_live_fetch",
            "resolution_runtime_reliability_artifact_creation",
            "transit_forward_run_corpus_execution",
            "transit_forward_run_corpus_live_fetch",
            "transit_forward_run_corpus_calibration_claim",
            "transit_track_record_gate_execution",
            "transit_track_record_gate_below_threshold_calibration_summary",
            "transit_track_record_gate_live_fetch",
            "transit_method_options_execution",
            "transit_method_options_non_baseline_selection",
            "transit_method_options_live_fetch",
            "integration_live_fetch_in_release_checks",
            "local_live_capture_in_release_checks",
            "unbounded_web_crawling",
            "live_calibration_claim",
            "universal_prediction_oracle",
        ],
    }
    errors = validate_record(manifest, SCHEMA)
    if errors:
        raise AssertionError(f"release manifest schema validation failed: {errors[0]}")
    return manifest


def write_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.write_text(render_json(manifest), encoding="utf-8")
    print("generated release manifest")


def check_manifest(manifest: dict[str, Any]) -> None:
    expected = render_json(manifest)
    if not MANIFEST_PATH.exists():
        print(f"missing release manifest: {MANIFEST_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_release_manifest.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = MANIFEST_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"release manifest drift: {MANIFEST_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_release_manifest.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked release manifest")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write manifest instead of checking it")
    args = parser.parse_args()
    manifest = build_manifest()
    if args.write:
        write_manifest(manifest)
    else:
        check_manifest(manifest)


if __name__ == "__main__":
    main()
