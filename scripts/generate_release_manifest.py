#!/usr/bin/env python3
"""Generate or check the local OPE release manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ope_schema import SPEC, validate_record
from ope_fixtures import render_json


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
            "approved_local_folder_runtime",
            "approved_database_adapter_runtime",
            "accepted_source_adapter_output",
            "agent_integration_starter_pack",
            "committed_fixture_request",
            "policy_bound_promoted_fixture_source_set",
        ],
        "happyPath": {
            "setupCommand": "python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
            "forecastCommand": "python3 scripts/ope.py forecast-run",
            "readbackCommands": [
                "python3 scripts/ope.py local-source-runtime",
                "python3 scripts/ope.py agent-integrate",
                "python3 scripts/ope.py developer-adoption",
                "python3 scripts/ope.py pilot-evidence",
                "python3 scripts/ope.py pilot-session-packet",
                "python3 scripts/ope.py pilot-summary-intake",
                "python3 scripts/ope.py pilot-findings --section summary",
                "python3 scripts/ope.py generated-types-decision --section summary",
                "python3 scripts/ope.py expansion-readiness",
                "python3 scripts/ope.py repeating-prediction-setup",
                "python3 scripts/ope.py prediction-campaign plan",
                "python3 scripts/ope.py prediction-campaign start",
                "python3 scripts/ope.py prediction-campaign start --view campaign-creation",
                "python3 scripts/ope.py prediction-campaign start --view forecast-schedule",
                "python3 scripts/ope.py prediction-campaign pre-calibration",
                "python3 scripts/ope.py prediction-campaign start --pre-calibrate --view pre-calibration",
                "python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl",
                "python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl",
                "python3 scripts/ope.py prediction-campaign forecast-create",
                "python3 scripts/ope.py prediction-campaign forecast-artifact",
                "python3 scripts/ope.py prediction-campaign forecast-write",
                "python3 scripts/ope.py prediction-campaign resolve",
                "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers",
                "python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers",
                "python3 scripts/ope.py prediction-campaign doctor",
                "python3 scripts/ope.py prediction-campaign resume",
                "python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state",
                "python3 scripts/ope.py prediction-campaign append-ready",
                "python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary",
                "python3 scripts/ope.py prediction-campaign calibration-status",
                "python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle",
                "python3 scripts/ope.py prediction-campaign method-update-gate",
                "python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view decision",
                "python3 scripts/ope.py prediction-campaign method-update-plan",
                "python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command",
                "python3 scripts/ope.py prediction-campaign apply-method-update",
                "python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary",
                "python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary",
                "python3 scripts/ope.py prediction-campaign explain",
                "python3 scripts/ope.py prediction-campaign explain --view task",
                "python3 scripts/ope.py prediction-campaign pilot-runbook",
                "python3 scripts/ope.py prediction-campaign pilot-runbook --view smoke",
                "python3 scripts/ope.py prediction-campaign pilot-runbook --view operator-status",
                "python3 scripts/ope.py prediction-campaign pilot-readiness",
                "python3 scripts/ope.py prediction-campaign pilot-readiness --view commands",
                "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
                "python3 scripts/ope.py postgres-compatibility",
                "python3 scripts/ope.py database-source-adapter-runtime",
                "python3 scripts/ope.py opp-provider-adapter",
                "python3 scripts/ope.py persistent-sqlite-policy",
                "python3 scripts/ope.py lifecycle-lease-policy",
                "python3 scripts/ope.py runtime-transport-readiness",
                "python3 scripts/ope.py workspace-tenant-isolation",
                "python3 scripts/ope.py domain-source-field-policy",
                "python3 scripts/ope.py credential-reference-policy",
                "python3 scripts/ope.py retention-redaction-policy",
                "python3 scripts/ope.py private-auto-evidence-policy",
                "python3 scripts/ope.py agent-call --operation campaign_plan",
                "python3 scripts/ope.py agent-call --operation campaign_status",
                "python3 scripts/ope.py agent-call --operation campaign_health",
                "python3 scripts/ope.py agent-call --operation campaign_append_readiness",
                "python3 scripts/ope.py agent-call --operation campaign_calibration_status",
                "python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001",
                "python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001",
                "python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z",
                "python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001",
                "python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z",
                "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
                "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
                "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
            ],
            "resolutionCommand": "python3 scripts/ope.py resolve-source-handoff",
            "scoringCommand": "python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102",
            "corpusReadbackCommand": "python3 scripts/ope.py transit-track-record-gate",
            "failureRecoveryCommand": "python3 scripts/ope.py resolution-runtime-reliability",
            "expectedForecastIds": ["forecast-602", "forecast-702", "forecast-1102", "forecast-1201", "forecast-1301"],
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
                "checkId": "mvp-smoke-local-source-runtime",
                "command": "python3 scripts/ope.py local-source-runtime",
                "expected": "approved local-folder runtime binds to forecast-1102 and exposes blocked examples without creating artifacts directly.",
            },
            {
                "checkId": "mvp-smoke-runtime-security",
                "command": "python3 scripts/ope.py runtime-security",
                "expected": "lightweight runtime hardening readback exposes dependency budget, module boundaries, runtime surface controls, threat notes, and blocked examples without starting hidden services.",
            },
            {
                "checkId": "mvp-smoke-agent-implementation-kit",
                "command": "python3 scripts/ope.py agent-implementation-kit",
                "expected": "agent prediction implementation kit exposes the quickstart front door, compact manual, question-discovery intake, candidate readbacks, validation reports, adapter guidance, and starter templates without creating forecast artifacts.",
            },
            {
                "checkId": "mvp-smoke-fast-agent-adoption",
                "command": "python3 scripts/ope.py smoke",
                "expected": "fast external-agent smoke runs schema sanity, developer-adoption, agent implementation kit, agent integration candidates, guided forecast, and forecast-card readback with progress output and no state writes.",
            },
            {
                "checkId": "mvp-smoke-agent-integration",
                "command": "python3 scripts/ope.py agent-integrate",
                "expected": "agent incorporation golden path exposes Helsinki starter readiness, forecastable and non-forecastable candidates, guided forecast-card command, and first-forecast-fast metrics without hosted runtime or claim upgrades.",
            },
            {
                "checkId": "mvp-smoke-agent-guidance",
                "command": "python3 scripts/ope.py agent-guide --section summary",
                "expected": "agent guidance loop exposes prompt classification, next moves, Helsinki narrowing questions, and an instruction pack without source execution, artifact creation, hosted runtime, or quality claim upgrades.",
            },
            {
                "checkId": "mvp-smoke-prediction-feature-setup",
                "command": "python3 scripts/ope.py prediction-feature-setup",
                "expected": "stable prediction-feature setup contract exposes compact request, response, interface, and boundary readbacks for accepted, clarification, blocked, rejected, and response-too-large cases without source execution or artifact creation.",
            },
            {
                "checkId": "mvp-smoke-embedded-prediction-feature-example",
                "command": "python3 examples/embed-ope-prediction-feature/host_wrapper.py --request examples/embed-ope-prediction-feature/fixtures/approved_feature_request.json --output-format json",
                "expected": "copyable host wrapper calls the stable prediction-feature setup contract, reads forecast-1102, and keeps hosted runtime, credentials, raw rows, raw SQL, hidden workers, and quality claims blocked.",
            },
            {
                "checkId": "mvp-smoke-mcp-adoption-path",
                "command": "python3 scripts/ope.py mcp-adoption --view summary",
                "expected": "MCP adoption path exposes the readiness, candidates, guided forecast, forecast-card sequence plus blocked unsafe and response-too-large transcripts with selector-only arguments.",
            },
            {
                "checkId": "mvp-smoke-postgres-compatibility",
                "command": "python3 scripts/ope.py postgres-compatibility",
                "expected": "SQLite-to-Postgres lifecycle storage semantics are checked while Postgres connections, migrations, hosted storage, and production database operations stay outside normal checks.",
            },
            {
                "checkId": "mvp-smoke-database-source-adapter-runtime",
                "command": "python3 scripts/ope.py database-source-adapter-runtime",
                "expected": "caller-approved database adapter output is checked through one sanitized fixture path while production DB connections, credential values, raw rows, and DB-specific forecast paths remain blocked.",
            },
            {
                "checkId": "mvp-smoke-opp-provider-adapter",
                "command": "python3 scripts/ope.py opp-provider-adapter",
                "expected": "optional OPP provider adapter mappings, Agent Card, accepted response, blocked cases, and conformance plan are checked without starting HTTP, SSE, payment, aggregation, or hosted service runtimes.",
            },
            {
                "checkId": "mvp-smoke-persistent-sqlite-policy",
                "command": "python3 scripts/ope.py persistent-sqlite-policy",
                "expected": "opt-in persistent SQLite path policy is checked with caller approval, allowlisted .ope/state paths, migration backup and lock guards, and no normal persistent database creation.",
            },
            {
                "checkId": "mvp-smoke-lifecycle-lease-policy",
                "command": "python3 scripts/ope.py lifecycle-lease-policy",
                "expected": "lifecycle operation lease policy is checked with nine strict-lease operations, five idempotency-only operations, conflict cases, and no lease acquisition or state mutation in normal checks.",
            },
            {
                "checkId": "mvp-smoke-runtime-transport-readiness",
                "command": "python3 scripts/ope.py runtime-transport-readiness",
                "expected": "runtime transport readiness is checked with local in-process, CLI, agent-call, and MCP surfaces ready while local HTTP, queue, hosted service, and OPP HTTP provider behavior remain deferred and non-networked in normal checks.",
            },
            {
                "checkId": "mvp-smoke-workspace-tenant-isolation",
                "command": "python3 scripts/ope.py workspace-tenant-isolation",
                "expected": "tenant-scoped workspace isolation is checked for resource limits, source bindings, operation queues, credential references, blocked cross-tenant access, and non-mutating normal checks.",
            },
            {
                "checkId": "mvp-smoke-domain-source-field-policy",
                "command": "python3 scripts/ope.py domain-source-field-policy",
                "expected": "universal domain fields, universal source-binding fields, domain-specific extension containers, source-kind credential references, and blocked raw/claim fields are classified without generating runtime types or creating artifacts.",
            },
            {
                "checkId": "mvp-smoke-credential-reference-policy",
                "command": "python3 scripts/ope.py credential-reference-policy",
                "expected": "opaque caller-owned credential references are checked with tenant/workspace/source/adapter scope, lifecycle and consumer rules, blocked raw secret cases, and no secret resolution or storage in normal checks.",
            },
            {
                "checkId": "mvp-smoke-retention-redaction-policy",
                "command": "python3 scripts/ope.py retention-redaction-policy",
                "expected": "retention and redaction policy is checked with append-only retention, archive tombstones, redaction receipts, physical-delete exception gates, and no silent or normal-check physical deletion.",
            },
            {
                "checkId": "mvp-smoke-private-auto-evidence-policy",
                "command": "python3 scripts/ope.py private-auto-evidence-policy",
                "expected": "private data:auto source-policy is checked with bound source kinds, policy gates, blocked web search/raw SQL/raw payload cases, and no private-source reads or secret resolution in normal checks.",
            },
            {
                "checkId": "mvp-smoke-developer-adoption",
                "command": "python3 scripts/ope.py developer-adoption",
                "expected": "quickstart, scenario, integrations, release notes, and type-generation boundary are available.",
            },
            {
                "checkId": "mvp-smoke-pilot-evidence",
                "command": "python3 scripts/ope.py pilot-evidence",
                "expected": "sanitized pilot evidence intake examples are available while real session count remains zero.",
            },
            {
                "checkId": "mvp-smoke-pilot-session-packet",
                "command": "python3 scripts/ope.py pilot-session-packet",
                "expected": "real pilot-session task cards, sanitization checks, and ledger-ready template are available without recording real sessions.",
            },
            {
                "checkId": "mvp-smoke-pilot-summary-intake",
                "command": "python3 scripts/ope.py pilot-summary-intake",
                "expected": "sanitized summary intake examples classify ledger-ready, redaction-needed, and blocked cases without writing ledger rows.",
            },
            {
                "checkId": "mvp-smoke-simulated-agent-pilot",
                "command": "python3 scripts/ope.py simulated-agent-pilot --section summary",
                "expected": "user-authorized simulated agent pilot covers five prediction-feature setup prompts with approximate token/time counts while recording zero real sessions.",
            },
            {
                "checkId": "mvp-smoke-pilot-findings",
                "command": "python3 scripts/ope.py pilot-findings --section summary",
                "expected": "pilot findings readback reports five simulated agent sessions, zero accepted real sessions, real-session evidence still needed, and no expansion, generated-types, quality, or hosted-runtime claim unlocked.",
            },
            {
                "checkId": "mvp-smoke-generated-types-decision",
                "command": "python3 scripts/ope.py generated-types-decision --section summary",
                "expected": "generated runtime types decision remains deferred with no selected language targets, no generated files, and stable JSON examples plus validator commands as the fallback.",
            },
            {
                "checkId": "mvp-smoke-expansion-readiness",
                "command": "python3 scripts/ope.py expansion-readiness",
                "expected": "post-MVP expansion options remain blocked or deferred until real pilot, corpus, and adoption evidence justify them.",
            },
            {
                "checkId": "mvp-smoke-repeating-prediction-setup",
                "command": "python3 scripts/ope.py repeating-prediction-setup",
                "expected": "repeating prediction setup recurrence examples are available without starting a runner, scheduler, live fetch, or campaign-state mutation.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-plan",
                "command": "python3 scripts/ope.py prediction-campaign plan",
                "expected": "prediction campaign dry-run plan exposes unique future run IDs without creating forecast artifacts or writing live campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-start",
                "command": "python3 scripts/ope.py prediction-campaign start",
                "expected": "prediction campaign start exposes the dry-run terminal runner surface without sleeping, polling, fetching live data, or creating forecasts.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-creation-input",
                "command": "python3 scripts/ope.py prediction-campaign start --view campaign-creation",
                "expected": "prediction campaign start normalizes default, flag, setup JSON, and manifest JSON inputs without writing campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-forecast-schedule",
                "command": "python3 scripts/ope.py prediction-campaign start --view forecast-schedule",
                "expected": "prediction campaign start maps ready, waiting, missed, and duplicate forecast schedule actions without writing campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-pre-calibration",
                "command": "python3 scripts/ope.py prediction-campaign pre-calibration",
                "expected": "prediction campaign pre-calibration computes an optional historical-only baseline binding without live fetches, method changes, or local writes.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-start-pre-calibration",
                "command": "python3 scripts/ope.py prediction-campaign start --pre-calibrate --view pre-calibration",
                "expected": "prediction campaign start exposes requested pre-calibration before any explicit launch write.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-foreground-tick",
                "command": "python3 scripts/ope.py prediction-campaign start --watch --max-ticks 1 --output-format jsonl",
                "expected": "prediction campaign start runs one bounded foreground forecast scheduling tick without writing campaign state unless --write-local is explicit.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-next-due-tick",
                "command": "python3 scripts/ope.py prediction-campaign start --now 2026-06-12T00:00:00Z --watch --max-ticks 1 --output-format jsonl",
                "expected": "prediction campaign start can move the runner clock and choose predictionrun-1302 as the next due forecast without writing campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-forecast-create",
                "command": "python3 scripts/ope.py prediction-campaign forecast-create",
                "expected": "prediction campaign forecast-create exposes the ready run and planned artifact IDs without writing campaign state or creating forecasts.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-forecast-artifact",
                "command": "python3 scripts/ope.py prediction-campaign forecast-artifact",
                "expected": "prediction campaign forecast-artifact exposes the checked unresolved baseline-only forecast-1301 record without live fetch, resolver execution, or campaign-state writes.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-forecast-write",
                "command": "python3 scripts/ope.py prediction-campaign forecast-write",
                "expected": "prediction campaign forecast-write exposes the guarded ignored-local-state write plan without executing the write during normal checks.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-resolution-attempt",
                "command": "python3 scripts/ope.py prediction-campaign resolve",
                "expected": "prediction campaign resolve exposes a due dry-run campaign resolver attempt without creating resolution or scoring records.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-resolution-execute-request",
                "command": "python3 scripts/ope.py prediction-campaign resolve --run-id predictionrun-1301 --execute-resolvers",
                "expected": "prediction campaign resolve records an explicit resolver request and blocks on the missing checked outcome source without executing resolvers.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-resolution-duplicate-block",
                "command": "python3 scripts/ope.py prediction-campaign resolve --attempt-case blocked_duplicate --execute-resolvers",
                "expected": "prediction campaign resolve blocks duplicate resolution and duplicate scoring without creating artifacts.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-doctor",
                "command": "python3 scripts/ope.py prediction-campaign doctor",
                "expected": "prediction campaign doctor exposes due, waiting, failed, blocked, append-ready, duplicate, and recovery readbacks without reading or writing ignored campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-resume",
                "command": "python3 scripts/ope.py prediction-campaign resume",
                "expected": "prediction campaign resume exposes checked recovery actions after interruption without reading or writing ignored live state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-interrupted-resume",
                "command": "python3 scripts/ope.py prediction-campaign resume --resume-case interrupted_after_forecast_write --view state",
                "expected": "prediction campaign resume can inspect interrupted run state and idempotency counts while preserving prior evidence.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-append-ready",
                "command": "python3 scripts/ope.py prediction-campaign append-ready",
                "expected": "prediction campaign append-ready exposes exclusion-audit append rows and comparable append blockers without writing ignored state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-append-comparable",
                "command": "python3 scripts/ope.py prediction-campaign append --ledger-case comparable_scored --view summary",
                "expected": "prediction campaign append dry-run exposes the comparable scored row shape and idempotent write boundary.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-calibration-status",
                "command": "python3 scripts/ope.py prediction-campaign calibration-status",
                "expected": "prediction campaign calibration-status reports below-threshold evidence without generating calibration summaries.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-post-calibration-restart",
                "command": "python3 scripts/ope.py prediction-campaign calibration-status --calibration-case post_calibration_restart --view cycle",
                "expected": "prediction campaign calibration-status reports the pause-and-resume continuation decision without mutating cycle state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-gate",
                "command": "python3 scripts/ope.py prediction-campaign method-update-gate",
                "expected": "prediction campaign method-update gate blocks below-threshold updates without changing probabilities, methods, or campaign state.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-approved-plan",
                "command": "python3 scripts/ope.py prediction-campaign method-update-gate --method-update-case approved_plan_ready --view decision",
                "expected": "prediction campaign method-update gate can report a plan-ready approved case while still requiring a future explicit effectful command.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-plan",
                "command": "python3 scripts/ope.py prediction-campaign method-update-plan",
                "expected": "prediction campaign method-update plan records the approval and rollback blockers without writing plan artifacts.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-plan-ready",
                "command": "python3 scripts/ope.py prediction-campaign method-update-plan --method-update-plan-case plan_ready --view command",
                "expected": "prediction campaign method-update plan reports the guarded effectful command shape while keeping it out of normal checks.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-apply",
                "command": "python3 scripts/ope.py prediction-campaign apply-method-update",
                "expected": "prediction campaign apply-method-update blocks by default without writing method bindings.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-apply-ready",
                "command": "python3 scripts/ope.py prediction-campaign apply-method-update --method-update-plan-case plan_ready --view summary",
                "expected": "prediction campaign apply-method-update reports the eligible weather-adjustment target only after a plan-ready readback.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-method-update-rollback-ready",
                "command": "python3 scripts/ope.py prediction-campaign rollback-method-update --method-update-plan-case plan_ready --view summary",
                "expected": "prediction campaign rollback-method-update reports the baseline restore target without mutating state unless --write-local is explicit.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-explain",
                "command": "python3 scripts/ope.py prediction-campaign explain",
                "expected": "prediction campaign explain reports next forecast, next resolution, evidence threshold, pilot task, adapter readbacks, and claim boundary.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-pilot-runbook",
                "command": "python3 scripts/ope.py prediction-campaign pilot-runbook",
                "expected": "prediction campaign pilot-runbook reports the 100-run Helsinki procedure, 3-run smoke path, operator status, success criteria, abort criteria, and baseline-first method boundary.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-pilot-readiness",
                "command": "python3 scripts/ope.py prediction-campaign pilot-readiness",
                "expected": "prediction campaign pilot-readiness reports checked launch prerequisites, manual confirmations, launch commands, blocked actions, and the baseline-first method boundary without starting the pilot.",
            },
            {
                "checkId": "mvp-smoke-prediction-campaign-mini-smoke",
                "command": "python3 scripts/ope.py prediction-campaign start --plan-count 3 --count 3 --watch --max-ticks 1 --output-format jsonl",
                "expected": "prediction campaign mini smoke runs one bounded 3-run foreground tick without writing local state unless --write-local is explicit.",
            },
            {
                "checkId": "mvp-smoke-agent-campaign-status",
                "command": "python3 scripts/ope.py agent-call --operation campaign_status",
                "expected": "agent-call returns a read-only campaign explain envelope for forecast-1301 without creating campaign artifacts.",
            },
            {
                "checkId": "mvp-smoke-transit-track-record-campaign-ledger",
                "command": "python3 scripts/ope.py transit-track-record-gate --campaign predictioncampaign-001",
                "expected": "transit track-record gate explicitly includes campaign ledger rows while preserving below-threshold claim boundaries.",
            },
            {
                "checkId": "mvp-smoke-campaign-resolution-jobs",
                "command": "python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001",
                "expected": "campaign-aware resolution jobs include the checked forecast-1301 run and tell agents to wait without executing resolvers.",
            },
            {
                "checkId": "mvp-smoke-campaign-resolution-jobs-due",
                "command": "python3 scripts/ope.py resolution-jobs --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z",
                "expected": "campaign-aware resolution jobs route the due forecast-1301 run to the checked prediction-campaign resolve command without executing resolvers.",
            },
            {
                "checkId": "mvp-smoke-campaign-resolution-scheduler",
                "command": "python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001",
                "expected": "campaign-aware resolution scheduler ticks include the checked forecast-1301 wait action without executing campaign resolvers.",
            },
            {
                "checkId": "mvp-smoke-campaign-resolution-scheduler-due",
                "command": "python3 scripts/ope.py resolution-scheduler --campaign predictioncampaign-001 --now 2026-06-11T07:15:00Z",
                "expected": "campaign-aware resolution scheduler ticks expose the checked campaign resolver-attempt-ready action without executing campaign resolvers.",
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
                "agent_pilot_validation_session_execution",
                "agent_pilot_validation_quality_claim",
                "local_usage_trace_hosted_telemetry",
                "local_usage_trace_live_fetch",
                "source_quality_mapping_confidence_source_execution",
                "source_quality_mapping_confidence_quality_claim",
                "local_source_runtime_arbitrary_private_api",
                "local_source_runtime_credential_storage",
                "local_source_runtime_hosted_runtime",
                "postgres_runtime_execution",
                "postgres_migration_execution",
                "hosted_storage_claim",
                "database_source_adapter_production_connection",
                "database_source_adapter_credential_values",
                "database_source_adapter_raw_private_rows",
                "opp_provider_http_runtime",
                "opp_provider_sse_streaming",
                "opp_provider_payment_settlement",
                "opp_provider_aggregation",
                "persistent_sqlite_default_runtime",
                "persistent_sqlite_normal_check_state_write",
                "persistent_sqlite_automatic_json_migration",
                "persistent_sqlite_unapproved_path",
                "lifecycle_lease_policy_readback_lease_acquisition",
                "lifecycle_lease_policy_raw_lock_control",
                "runtime_transport_http_listener",
                "runtime_transport_hosted_service",
                "runtime_transport_queue_runtime",
                "runtime_transport_opp_http_provider",
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
            "database_source_adapter_production_connection",
            "database_source_adapter_credential_values",
            "database_source_adapter_raw_private_rows",
            "opp_provider_http_runtime",
            "opp_provider_sse_streaming",
            "opp_provider_payment_settlement",
            "opp_provider_aggregation",
            "persistent_sqlite_default_runtime",
            "persistent_sqlite_normal_check_state_write",
            "persistent_sqlite_automatic_json_migration",
            "persistent_sqlite_unapproved_path",
            "lifecycle_lease_policy_readback_lease_acquisition",
            "lifecycle_lease_policy_raw_lock_control",
            "runtime_transport_http_listener",
            "runtime_transport_hosted_service",
            "runtime_transport_queue_runtime",
            "runtime_transport_opp_http_provider",
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
            "agent_pilot_validation_session_execution",
            "agent_pilot_validation_raw_transcript_storage",
            "agent_pilot_validation_private_data_storage",
            "agent_pilot_validation_quality_claim",
            "local_usage_trace_hosted_telemetry",
            "local_usage_trace_raw_prompt_storage",
            "local_usage_trace_raw_transcript_storage",
            "local_usage_trace_private_data_storage",
            "local_usage_trace_credential_storage",
            "local_usage_trace_live_fetch",
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
            "transit_corpus_growth_canonical_mutation",
            "transit_corpus_growth_live_fetch",
            "transit_corpus_growth_quality_claim",
            "source_quality_mapping_confidence_source_execution",
            "source_quality_mapping_confidence_artifact_creation",
            "source_quality_mapping_confidence_quality_claim",
            "local_source_runtime_arbitrary_private_api",
            "local_source_runtime_database_parsing",
            "local_source_runtime_credential_storage",
            "local_source_runtime_live_fetch",
            "local_source_runtime_hosted_runtime",
            "local_source_runtime_forecast_artifact_creation",
            "runtime_security_independent_audit_claim",
            "runtime_security_secret_manager",
            "runtime_security_hosted_runtime_execution",
            "runtime_security_live_source_execution",
            "runtime_security_private_database_connector",
            "agent_implementation_kit_free_form_oracle",
            "agent_implementation_kit_question_discovery_artifact_creation",
            "agent_implementation_kit_raw_crud_writes",
            "agent_implementation_kit_hidden_live_fetch",
            "agent_implementation_kit_credential_storage",
            "agent_implementation_kit_automatic_method_upgrade",
            "prediction_feature_setup_forecast_artifact_creation",
            "prediction_feature_setup_private_source_execution",
            "prediction_feature_setup_credential_storage",
            "prediction_feature_setup_raw_sql",
            "prediction_feature_setup_hosted_runtime",
            "prediction_feature_setup_quality_claim",
            "embedded_prediction_feature_hosted_runtime",
            "embedded_prediction_feature_credential_storage",
            "embedded_prediction_feature_raw_private_rows",
            "embedded_prediction_feature_raw_sql",
            "embedded_prediction_feature_hidden_worker",
            "embedded_prediction_feature_quality_claim",
            "mcp_adoption_credential_argument",
            "mcp_adoption_raw_sql_argument",
            "mcp_adoption_raw_private_rows",
            "mcp_adoption_hidden_live_fetch",
            "mcp_adoption_hosted_runtime",
            "mcp_adoption_forecast_artifact_creation",
            "postgres_runtime_execution",
            "postgres_migration_execution",
            "hosted_storage_claim",
            "developer_adoption_surface_command_execution",
            "developer_adoption_surface_type_generation",
            "developer_adoption_surface_quality_claim",
            "pilot_evidence_raw_transcript_storage",
            "pilot_evidence_private_data_storage",
            "pilot_evidence_real_session_claim",
            "pilot_evidence_quality_claim",
            "pilot_session_packet_session_execution",
            "pilot_session_packet_raw_transcript_storage",
            "pilot_session_packet_private_data_storage",
            "pilot_session_packet_ledger_write",
            "pilot_session_packet_quality_claim",
            "pilot_summary_intake_real_session_recording",
            "pilot_summary_intake_raw_transcript_storage",
            "pilot_summary_intake_private_data_storage",
            "pilot_summary_intake_ledger_write",
            "pilot_summary_intake_quality_claim",
            "pilot_findings_raw_transcript_storage",
            "pilot_findings_private_data_storage",
            "pilot_findings_host_project_secret_storage",
            "pilot_findings_quality_claim",
            "pilot_findings_generated_types_unlock",
            "pilot_findings_hosted_runtime_unlock",
            "generated_types_full_spec_sdk",
            "generated_types_hosted_client_sdk",
            "generated_types_private_source_runtime",
            "generated_types_quality_claim",
            "generated_types_generated_files",
            "expansion_readiness_hosted_runtime_execution",
            "expansion_readiness_private_source_execution",
            "expansion_readiness_live_fetch",
            "expansion_readiness_type_generation",
            "expansion_readiness_quality_claim",
            "transit_track_record_gate_execution",
            "transit_track_record_gate_below_threshold_calibration_summary",
            "transit_track_record_gate_live_fetch",
            "transit_method_options_execution",
            "transit_method_options_non_baseline_selection",
            "transit_method_options_live_fetch",
            "prediction_campaign_method_update_gate_probability_update",
            "prediction_campaign_method_update_gate_method_change",
            "prediction_campaign_method_update_gate_registry_write",
            "prediction_campaign_method_update_plan_artifact_write",
            "prediction_campaign_method_update_plan_effectful_command",
            "prediction_campaign_method_update_plan_rollback_rewrite",
            "prediction_campaign_method_update_action_normal_check_mutation",
            "prediction_campaign_method_update_action_prior_history_rewrite",
            "prediction_campaign_method_update_action_registry_write",
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
