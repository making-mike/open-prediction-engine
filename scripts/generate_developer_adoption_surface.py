#!/usr/bin/env python3
"""Generate or check the local MVP developer adoption surface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_local_source_runtime import build_runtime
from generate_release_manifest import build_manifest
from ope_schema import SPEC, validate_record
from read_ope_record import read_record
from ope_fixtures import check_generated, render_json, write_generated


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "developer-adoption"
OUTPUT_PATH = GENERATED / "ope-developer-adoption-surface.generated.json"
SCHEMA = SPEC / "developer-adoption-surface.schema.json"
GENERATED_AT = "2026-06-10T10:05:00Z"

QUICKSTART_ORDER = [
    "setup_check",
    "normal_checks",
    "local_runtime",
    "forecast_card",
    "lifecycle_bundle",
    "claim_gate",
    "recurring_campaign",
]

SCENARIO_PHASES = [
    "source_setup",
    "runtime_gate",
    "forecast_readback",
    "lifecycle_bundle",
    "resolution_scoring",
    "claim_review",
]


class DeveloperAdoptionSurfaceError(Exception):
    pass


def quickstart_step(index: int, key: str, title: str, command: str, expected: str, seconds: int) -> dict[str, Any]:
    return {
        "stepId": f"adoptionquickstart-{index:03d}",
        "order": index,
        "title": title,
        "command": command,
        "expected": expected,
        "timeBudgetSeconds": seconds,
        "_key": key,
    }


def strip_private_keys(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if not key.startswith("_")} for row in rows]


def scenario_step(
    index: int,
    phase: str,
    command: str,
    expected_status: str,
    forecast_id: str | None,
    question_id: str | None,
    creates_artifacts: bool,
) -> dict[str, Any]:
    return {
        "stepId": f"adoptionscenario-{index:03d}",
        "phase": phase,
        "command": command,
        "expectedStatus": expected_status,
        "forecastId": forecast_id,
        "questionId": question_id,
        "createsArtifacts": creates_artifacts,
        "qualityClaimAllowed": False,
    }


def integration_note(
    interface: str,
    implemented_status: str,
    minimum_input: str,
    example_command: str,
    expected_output: str,
    boundary: str,
) -> dict[str, Any]:
    return {
        "interface": interface,
        "implementedStatus": implemented_status,
        "minimumInput": minimum_input,
        "exampleCommand": example_command,
        "expectedOutput": expected_output,
        "boundary": boundary,
    }


def release_section(category: str, items: list[str]) -> dict[str, Any]:
    return {
        "category": category,
        "items": items,
    }


def success_check(index: int, command: str, expected: str) -> dict[str, Any]:
    return {
        "checkId": f"adoptioncheck-{index:03d}",
        "command": command,
        "expected": expected,
    }


def build_quickstart() -> list[dict[str, Any]]:
    rows = [
        quickstart_step(
            1,
            "setup_check",
            "Confirm Python runtime",
            "python3 --version",
            "Python 3.12+ is preferred; the repository uses only the standard library.",
            20,
        ),
        quickstart_step(
            2,
            "normal_checks",
            "Run the local check suite",
            "python3 scripts/run_checks.py",
            "All schema, fixture, read-surface, agent, and release checks pass without live network access.",
            900,
        ),
        quickstart_step(
            3,
            "local_runtime",
            "Inspect approved local-folder runtime",
            "python3 scripts/ope.py local-source-runtime",
            "The approved local-folder case binds to forecast-1102 and blocked examples remain non-generating.",
            30,
        ),
        quickstart_step(
            4,
            "forecast_card",
            "Read the first forecast card",
            "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
            "A compact forecast card is available with probability, baseline, setup binding, and claim warning.",
            20,
        ),
        quickstart_step(
            5,
            "lifecycle_bundle",
            "Read the lifecycle bundle",
            "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
            "The bundle links question, evidence, forecast artifact, history, resolution, scoring, and setup bindings.",
            20,
        ),
        quickstart_step(
            6,
            "claim_gate",
            "Inspect the claim boundary",
            "python3 scripts/ope.py transit-track-record-gate",
            "The public transport gate remains below track-record and calibration thresholds.",
            20,
        ),
        quickstart_step(
            7,
            "recurring_campaign",
            "Evaluate recurring campaign readiness",
            "python3 scripts/ope.py prediction-campaign explain",
            "The campaign explain readback names the next forecast, next resolution, evidence threshold, and claim boundary before hosted scheduling work.",
            30,
        ),
    ]
    return strip_private_keys(rows)


def build_scenario() -> dict[str, Any]:
    return {
        "scenarioId": "adoptionscenario-100",
        "title": "Approved Local Source To Forecast Readback",
        "goal": "Reach a valid forecast card and lifecycle bundle from the checked local MVP while preserving source, method, resolution, scoring, and claim boundaries.",
        "steps": [
            scenario_step(
                1,
                "source_setup",
                "python3 scripts/ope.py private-setup-orchestrator --case local_file_confirmed",
                "completed_forecast_readback",
                "forecast-1102",
                "question-1102",
                False,
            ),
            scenario_step(
                2,
                "runtime_gate",
                "python3 scripts/ope.py local-source-runtime --case approved_local_folder",
                "forecast_card_ready",
                "forecast-1102",
                "question-1102",
                False,
            ),
            scenario_step(
                3,
                "forecast_readback",
                "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102",
                "available",
                "forecast-1102",
                "question-1102",
                False,
            ),
            scenario_step(
                4,
                "lifecycle_bundle",
                "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102",
                "available",
                "forecast-1102",
                "question-1102",
                False,
            ),
            scenario_step(
                5,
                "resolution_scoring",
                "python3 scripts/ope.py agent-call --operation scoring_summary --forecast-id forecast-1102 --question-id question-1102",
                "ok",
                "forecast-1102",
                "question-1102",
                False,
            ),
            scenario_step(
                6,
                "claim_review",
                "python3 scripts/ope.py transit-track-record-gate",
                "not_enough_resolved_comparable_outcomes",
                "forecast-1102",
                "question-1102",
                False,
            ),
        ],
        "expectedFinalState": {
            "forecastId": "forecast-1102",
            "questionId": "question-1102",
            "forecastCardAvailable": True,
            "lifecycleBundleAvailable": True,
            "resolutionStatus": "resolved",
            "scoreStatus": "scored",
            "qualityClaimAllowed": False,
        },
    }


def build_integration_notes() -> list[dict[str, Any]]:
    return [
        integration_note(
            "cli",
            "implemented_local",
            "A local shell with Python and repository files.",
            "python3 scripts/ope.py local-source-runtime",
            "JSON summary or one section/case with checked IDs, statuses, commands, and claim boundaries.",
            "CLI commands are local and deterministic by default; live probes remain explicit opt-in commands.",
        ),
        integration_note(
            "agent_call",
            "implemented_local",
            "Operation name plus IDs such as forecastId=forecast-1102 and questionId=question-1102.",
            "python3 scripts/ope.py agent-call --operation forecast_card --forecast-id forecast-1102 --question-id question-1102",
            "One transport-neutral envelope with status, exitCode, recordBinding, payload, and sanitized errors.",
            "Agent-call is a local dispatcher, not a hosted API or production protocol service; campaign readbacks must be evaluated before hosted scheduling.",
        ),
        integration_note(
            "mcp_stdio",
            "local_scaffold",
            "An MCP-capable host that can launch python3 scripts/ope.py mcp-stdio.",
            "python3 scripts/ope.py mcp-stdio",
            "MCP tools expose the same local dispatcher envelope semantics over stdio.",
            "The MCP adapter is local stdio only; HTTP and queue adapters remain future protocol mappings.",
        ),
    ]


def build_release_notes() -> list[dict[str, Any]]:
    return [
        release_section(
            "implemented",
            [
                "Local CLI checks, readbacks, forecast cards, lifecycle bundles, and generated record validation.",
                "Approved local-folder source runtime for checked CSV/JSON fixture files under path and size limits.",
                "Transport-neutral agent-call envelopes and local MCP stdio scaffold over the same dispatcher.",
                "Resolution, scoring, source-handoff, setup method, source-quality, usage-trace, and pilot-validation readbacks.",
                "Repeating prediction campaign explain, adapter, MCP, and pilot task readbacks for local campaign comprehension.",
            ],
        ),
        release_section(
            "fixture_only",
            [
                "Weather-logistics source-handoff forecast, resolution, and scoring remain checked fixture-mode paths.",
                "Public transport corpus growth, method options, track-record gates, and live evidence promotion remain below claim thresholds.",
                "Usage traces and pilot summaries are synthetic checked examples, not real hosted telemetry.",
                "Recurring campaign events are checked local readbacks and do not create hosted schedules or production watchers.",
            ],
        ),
        release_section(
            "non_goal",
            [
                "No hosted service, network API, production SDK, or production agent adapter runtime is implemented.",
                "No arbitrary private API/database parsing, credential storage, raw private-row retention, or hosted watcher exists.",
                "No calibration, broad forecast-quality, or production connector claim is allowed from the current examples.",
                "No generated language-specific runtime types are included before adoption evidence shows they reduce setup friction.",
                "No hosted scheduling or broader private-source runtime should be promoted before recurring prediction setup is evaluated.",
            ],
        ),
    ]


def build_success_checks() -> list[dict[str, Any]]:
    return [
        success_check(1, "python3 scripts/ope.py developer-adoption --check", "developer adoption surface fixture is current"),
        success_check(2, "python3 scripts/ope.py local-source-runtime --check", "approved local-folder runtime fixture is current"),
        success_check(3, "python3 scripts/ope.py read --record-type forecast-card --id forecast-1102 --question-id question-1102", "forecast card readback succeeds"),
        success_check(4, "python3 scripts/ope.py read --record-type forecast-bundle --id forecast-1102 --question-id question-1102", "lifecycle bundle readback succeeds"),
        success_check(5, "python3 scripts/check_mvp_release_surface.py", "local MVP smoke check passes"),
        success_check(6, "python3 scripts/ope.py prediction-campaign explain --view summary", "recurring prediction campaign readback explains local status"),
        success_check(7, "python3 scripts/run_checks.py", "canonical dependency-free check suite passes"),
    ]


def build_developer_adoption_surface() -> dict[str, Any]:
    manifest = build_manifest()
    local_runtime = build_runtime()
    card = read_record("forecast-card", "forecast-1102", "question-1102")["record"]
    bundle = read_record("forecast-bundle", "forecast-1102", "question-1102")["record"]
    quickstart = build_quickstart()
    scenario = build_scenario()
    integrations = build_integration_notes()
    release_notes = build_release_notes()
    type_decision = {
        "decisionStatus": "defer_until_adoption_evidence",
        "currentContractSource": "JSON Schema contracts under spec/ remain the source of truth for the local MVP.",
        "rationale": "Generated language-specific types should wait until pilot or adoption evidence shows they reduce setup friction more than they add maintenance surface.",
        "triggerToRevisit": "Revisit when agent pilot summaries or local usage traces show repeated integration friction around schema shape or validation.",
        "generatedTypesIncluded": False,
    }
    surface = {
        "developerAdoptionSurfaceId": "developeradoptionsurface-001",
        "generatedAt": GENERATED_AT,
        "surfaceStatus": "local_mvp_adoption_ready",
        "audience": ["developer", "agent", "mcp_host", "maintainer"],
        "bindings": {
            "releaseManifestId": manifest["releaseManifestId"],
            "mvpRunbookPath": manifest["mvpLocalRuntime"]["runbookPath"],
            "localSourceRuntimeId": local_runtime["localSourceRuntimeId"],
            "forecastId": card["forecastId"],
            "questionId": card["questionId"],
            "forecastCardId": card["cardId"],
            "forecastBundleId": bundle["bundleId"],
        },
        "quickstart": quickstart,
        "exampleScenario": scenario,
        "integrationNotes": integrations,
        "releaseNotes": release_notes,
        "typeGenerationDecision": type_decision,
        "successChecks": build_success_checks(),
        "summary": {
            "quickstartStepCount": len(quickstart),
            "scenarioStepCount": len(scenario["steps"]),
            "integrationCount": len(integrations),
            "implementedNoteCount": len(release_notes[0]["items"]),
            "fixtureOnlyNoteCount": len(release_notes[1]["items"]),
            "nonGoalNoteCount": len(release_notes[2]["items"]),
            "firstForecastId": card["forecastId"],
            "qualityClaimAllowed": False,
            "generatedTypesIncluded": False,
        },
        "executionBoundary": {
            "readOnlyGuide": True,
            "normalChecksDeterministicOffline": True,
            "executesCommands": False,
            "createsForecastArtifacts": False,
            "fetchesLiveData": False,
            "storesCredentials": False,
            "storesPrivateRows": False,
            "hostedRuntime": False,
            "productionSdk": False,
            "languageTypesGenerated": False,
            "qualityClaimAllowed": False,
        },
        "warnings": [
            "Developer adoption surface is a read-only guide over existing checked local records.",
            "Commands named in the guide are not executed by the generator or checker.",
            "Fixture examples do not imply calibration, production connector support, or broad forecast quality.",
            "Generated language-specific runtime types remain deferred until adoption evidence justifies them.",
        ],
    }
    validate_surface(surface)
    return surface


def validate_surface(surface: dict[str, Any]) -> None:
    errors = validate_record(surface, SCHEMA)
    if errors:
        raise DeveloperAdoptionSurfaceError(f"developer adoption surface schema validation failed: {errors[0]}")
    quickstart = surface["quickstart"]
    if [item["order"] for item in quickstart] != list(range(1, len(quickstart) + 1)):
        raise DeveloperAdoptionSurfaceError("quickstart order drifted")
    if [item["title"] for item in quickstart][:2] != ["Confirm Python runtime", "Run the local check suite"]:
        raise DeveloperAdoptionSurfaceError("quickstart should begin with setup and checks")
    scenario = surface["exampleScenario"]
    phases = [item["phase"] for item in scenario["steps"]]
    if phases != SCENARIO_PHASES:
        raise DeveloperAdoptionSurfaceError("scenario phase order drifted")
    if scenario["expectedFinalState"]["forecastId"] != "forecast-1102":
        raise DeveloperAdoptionSurfaceError("adoption scenario should bind forecast-1102")
    if scenario["expectedFinalState"]["qualityClaimAllowed"]:
        raise DeveloperAdoptionSurfaceError("adoption scenario must keep quality claim blocked")
    integrations = {item["interface"]: item for item in surface["integrationNotes"]}
    if set(integrations) != {"cli", "agent_call", "mcp_stdio"}:
        raise DeveloperAdoptionSurfaceError("integration notes must cover cli, agent_call, and mcp_stdio")
    if integrations["mcp_stdio"]["implementedStatus"] != "local_scaffold":
        raise DeveloperAdoptionSurfaceError("MCP stdio should remain a local scaffold")
    release_categories = {item["category"] for item in surface["releaseNotes"]}
    if release_categories != {"implemented", "fixture_only", "non_goal"}:
        raise DeveloperAdoptionSurfaceError("release note category coverage drifted")
    if surface["typeGenerationDecision"]["generatedTypesIncluded"]:
        raise DeveloperAdoptionSurfaceError("developer adoption surface must not include generated runtime types yet")
    boundary = surface["executionBoundary"]
    for key, value in boundary.items():
        if key in {"readOnlyGuide", "normalChecksDeterministicOffline"}:
            if value is not True:
                raise DeveloperAdoptionSurfaceError(f"execution boundary {key} should be true")
        elif value is not False:
            raise DeveloperAdoptionSurfaceError(f"execution boundary {key} should be false")
    summary = surface["summary"]
    if summary["quickstartStepCount"] < 5 or summary["scenarioStepCount"] != 6:
        raise DeveloperAdoptionSurfaceError("developer adoption summary counts drifted")
    if summary["qualityClaimAllowed"] or summary["generatedTypesIncluded"]:
        raise DeveloperAdoptionSurfaceError("developer adoption summary must keep claims and generated types blocked")


def summary(surface: dict[str, Any]) -> dict[str, Any]:
    return {
        "developerAdoptionSurfaceId": surface["developerAdoptionSurfaceId"],
        "surfaceStatus": surface["surfaceStatus"],
        "bindings": surface["bindings"],
        "summary": surface["summary"],
        "quickstart": surface["quickstart"],
        "integrationInterfaces": [
            {
                "interface": item["interface"],
                "implementedStatus": item["implementedStatus"],
                "exampleCommand": item["exampleCommand"],
            }
            for item in surface["integrationNotes"]
        ],
        "typeGenerationDecision": surface["typeGenerationDecision"],
    }


def section(surface: dict[str, Any], section_name: str) -> Any:
    if section_name == "quickstart":
        return surface["quickstart"]
    if section_name == "scenario":
        return surface["exampleScenario"]
    if section_name == "integrations":
        return surface["integrationNotes"]
    if section_name == "release-notes":
        return surface["releaseNotes"]
    if section_name == "type-decision":
        return surface["typeGenerationDecision"]
    raise DeveloperAdoptionSurfaceError(f"unsupported section {section_name}")


def write_surface(surface: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, surface, label="developer adoption surface", regen="python3 scripts/generate_developer_adoption_surface.py --write")


def check_surface(surface: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, surface, label="developer adoption surface", regen="python3 scripts/generate_developer_adoption_surface.py --write")


def load_generated_surface() -> dict[str, Any] | None:
    if not OUTPUT_PATH.exists():
        return None
    surface = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    validate_surface(surface)
    return surface


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--section",
        choices=["quickstart", "scenario", "integrations", "release-notes", "type-decision"],
        help="print one adoption surface section",
    )
    parser.add_argument("--check", action="store_true", help="check generated developer adoption surface drift")
    parser.add_argument("--write", action="store_true", help="refresh generated developer adoption surface")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading the checked fixture")
    args = parser.parse_args()
    try:
        if args.write or args.check or args.rebuild:
            surface = build_developer_adoption_surface()
        else:
            surface = load_generated_surface() or build_developer_adoption_surface()
    except DeveloperAdoptionSurfaceError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    if args.write:
        write_surface(surface)
    elif args.check:
        check_surface(surface)
    elif args.section:
        sys.stdout.write(render_json(section(surface, args.section)))
    else:
        sys.stdout.write(render_json(summary(surface)))


if __name__ == "__main__":
    main()
