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


def mvp_local_runtime() -> dict[str, Any]:
    return {
        "surfaceStatus": "local_mvp_fixture_ready",
        "runtimeMode": "local_cli_and_generated_records",
        "runbookPath": "spec/mvp-local-runtime.md",
        "supportedSourceInputs": [
            "approved_local_csv_json",
            "accepted_source_adapter_output",
            "committed_fixture_request",
            "policy_bound_promoted_fixture_source_set",
        ],
        "happyPath": {
            "setupCommand": "python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
            "forecastCommand": "python3 scripts/ope.py forecast-run",
            "readbackCommands": [
                "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
                "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
                "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
            ],
            "resolutionCommand": "python3 scripts/ope.py resolve-source-handoff",
            "scoringCommand": "python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102",
            "corpusReadbackCommand": "python3 scripts/ope.py transit-track-record-gate",
            "failureRecoveryCommand": "python3 scripts/ope.py resolution-runtime-reliability",
            "expectedForecastIds": ["forecast-602", "forecast-702", "forecast-1102", "forecast-1201"],
        },
        "machineInterfaces": [
            {
                "interface": "cli",
                "command": "python3 scripts/ope.py",
                "status": "implemented_local",
                "minimumUse": "Run setup, forecast, resolution, scoring, readback, and release checks locally.",
            },
            {
                "interface": "agent_call",
                "command": "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
                "status": "implemented_local",
                "minimumUse": "Return one schema-bound envelope with exit code, status, record binding, and payload.",
            },
            {
                "interface": "mcp_stdio",
                "command": "python3 scripts/ope.py mcp-stdio",
                "status": "local_scaffold",
                "minimumUse": "Expose the local dispatcher as MCP stdio tools for MCP-capable hosts.",
            },
        ],
        "smokeChecks": [
            {
                "checkId": "mvp-smoke-local-setup-readback",
                "command": "python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
                "expected": "forecast-1102 is resolved and scored, with quality claim still sample-size-blocked.",
            },
            {
                "checkId": "mvp-smoke-forecast-run",
                "command": "python3 scripts/ope.py forecast-run",
                "expected": "forecast-602 completes through forecast card, evidence trace, bundle, resolution, and score bindings.",
            },
            {
                "checkId": "mvp-smoke-agent-envelope",
                "command": "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
                "expected": "agent-call returns an ok envelope for the normal forecast-card readback.",
            },
            {
                "checkId": "mvp-smoke-resolution-jobs",
                "command": "python3 scripts/ope.py resolution-jobs",
                "expected": "resolution jobs expose next actions without executing resolver commands.",
            },
            {
                "checkId": "mvp-smoke-corpus-claim-gate",
                "command": "python3 scripts/ope.py transit-track-record-gate",
                "expected": "corpus readback reports below-threshold track-record and calibration status.",
            },
        ],
        "blockedPathExamples": [
            {
                "case": "missing_approval",
                "command": "python3 scripts/ope.py private-setup-orchestrator --case missing_approval",
                "expectedStatus": "missing_approval",
                "nextAction": "confirm_approval",
                "forecastArtifactsCreated": False,
            },
            {
                "case": "unconfirmed_mapping",
                "command": "python3 scripts/ope.py private-setup-orchestrator --case unconfirmed_mapping",
                "expectedStatus": "needs_confirmation",
                "nextAction": "confirm_mapping",
                "forecastArtifactsCreated": False,
            },
            {
                "case": "unsafe_source",
                "command": "python3 scripts/ope.py private-setup-orchestrator --case unsafe_source",
                "expectedStatus": "blocked_unsafe",
                "nextAction": "stop_unsafe_connector",
                "forecastArtifactsCreated": False,
            },
            {
                "case": "response_too_large",
                "command": "python3 scripts/ope.py private-setup-orchestrator --case response_too_large",
                "expectedStatus": "response_too_large",
                "nextAction": "retry_with_smaller_readback",
                "forecastArtifactsCreated": False,
            },
        ],
        "claimReview": {
            "qualityClaimsAllowed": False,
            "trackRecordStatus": "not_enough_resolved_comparable_outcomes",
            "calibrationStatus": "not_enough_resolved_comparable_outcomes",
            "liveCalibrationClaimAllowed": False,
            "normalChecksUseLiveNetwork": False,
            "nonGoalRefs": [
                "network_api",
                "hosted_service",
                "production_agent_adapter_runtime",
                "generic_private_api_database_runtime",
                "production_forecast_use_of_live_connector_results",
                "live_calibration_claim",
                "unbounded_web_crawling",
            ],
        },
    }


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
        "mvpLocalRuntime": mvp_local_runtime(),
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
            "source_adapter_intake_connector_execution",
            "source_adapter_intake_live_fetch",
            "source_adapter_intake_credential_storage",
            "source_adapter_intake_raw_private_rows",
            "source_adapter_intake_forecast_execution",
            "generic_private_api_database_runtime",
            "generic_manual_upload_runtime",
            "private_source_adapter_execution",
            "private_source_adapter_outcome_execution",
            "private_source_adapter_bridge_execution",
            "private_setup_request_execution",
            "private_setup_first_action_execution",
            "private_setup_first_action_runbook_execution",
            "private_setup_agent_bundle_execution",
            "private_setup_orchestrator_execution",
            "private_setup_orchestrator_source_reads",
            "private_setup_orchestrator_forecast_creation",
            "private_setup_orchestrator_scoring_creation",
            "private_setup_orchestrator_credential_storage",
            "private_setup_orchestrator_live_fetch",
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
            "transit_live_evidence_promotion_live_fetch",
            "transit_live_evidence_promotion_live_workspace_reads",
            "transit_live_evidence_promotion_post_close_forecast_evidence",
            "transit_live_evidence_promotion_resolution_only_forecast_evidence",
            "transit_live_evidence_promotion_production_runtime",
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
