#!/usr/bin/env python3
"""Check prediction campaign forecast write-plan invariants."""

from __future__ import annotations

import tempfile
from pathlib import Path

from generate_prediction_campaign_forecast_write import build_prediction_campaign_forecast_write
from prediction_campaign_forecast_write_runtime import (
    PredictionCampaignForecastWriteError,
    ensure_safe_local_path,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_raises(callable_obj, message: str) -> None:
    try:
        callable_obj()
    except PredictionCampaignForecastWriteError:
        return
    raise AssertionError(message)


def check_safe_local_path_guards() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        state_root = workspace / ".ope" / "live" / "prediction-campaigns"
        state_root.mkdir(parents=True)
        outside = Path(temp_dir) / "outside"
        outside.mkdir()

        safe_value = ".ope/live/prediction-campaigns/predictioncampaign-001/predictionrun-1301/forecast-1301.json"
        safe_path = ensure_safe_local_path(safe_value, workspace_root=workspace)
        require(safe_path == workspace / safe_value, "safe local campaign path should stay under workspace root")

        require_raises(
            lambda: ensure_safe_local_path("/tmp/forecast-1301.json", workspace_root=workspace),
            "absolute paths should be rejected",
        )
        require_raises(
            lambda: ensure_safe_local_path(".ope/live/prediction-campaigns/../forecast-1301.json", workspace_root=workspace),
            "parent traversal should be rejected",
        )

        symlink_child = state_root / "escape-child"
        symlink_child.symlink_to(outside, target_is_directory=True)
        require_raises(
            lambda: ensure_safe_local_path(
                ".ope/live/prediction-campaigns/escape-child/forecast-1301.json",
                workspace_root=workspace,
            ),
            "symlinked child paths outside campaign state root should be rejected",
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        live_root = workspace / ".ope" / "live"
        live_root.mkdir(parents=True)
        outside = Path(temp_dir) / "outside-root"
        outside.mkdir()
        (live_root / "prediction-campaigns").symlink_to(outside, target_is_directory=True)
        require_raises(
            lambda: ensure_safe_local_path(
                ".ope/live/prediction-campaigns/forecast-1301.json",
                workspace_root=workspace,
            ),
            "symlinked campaign state root outside the workspace should be rejected",
        )


def main() -> None:
    check_safe_local_path_guards()
    plan = build_prediction_campaign_forecast_write()
    bindings = plan["bindings"]
    target = plan["targetState"]
    artifacts = plan["sourceArtifacts"]
    guards = plan["writeGuards"]
    command = plan["commandSurface"]
    summary = plan["summary"]
    boundary = plan["executionBoundary"]

    require(plan["writeStatus"] == "ready_for_explicit_local_write", "forecast write status drifted")
    require(plan["domain"] == "weather-transit-delays", "forecast write domain drifted")
    require(bindings["predictionCampaignManifestId"] == "predictioncampaignmanifest-001", "manifest binding drifted")
    require(bindings["predictionCampaignRunnerId"] == "predictioncampaignrunner-001", "runner binding drifted")
    require(
        bindings["predictionCampaignForecastCreationId"] == "predictioncampaignforecastcreation-001",
        "forecast creation binding drifted",
    )
    require(bindings["runId"] == "predictionrun-1301", "run binding drifted")
    require(bindings["forecastId"] == "forecast-1301", "forecast binding drifted")
    require(bindings["questionId"] == "question-1301", "question binding drifted")
    require(bindings["evidencePacketId"] == "evidence-1301", "evidence binding drifted")
    require(bindings["historyId"] == "history-1301", "history binding drifted")
    require(bindings["sourcePolicyId"] == "sourcepolicy-1201", "source policy binding drifted")

    require(len(artifacts) == 4, "forecast write should bind four lifecycle records")
    artifact_types = {artifact["recordType"] for artifact in artifacts}
    require(
        artifact_types == {"forecast_question", "evidence_packet", "forecast_artifact", "forecast_history"},
        "forecast write lifecycle record types drifted",
    )
    for artifact in artifacts:
        require(artifact["fixturePath"].startswith("spec/fixtures/generated/"), "fixture path should be checked")
        require(artifact["targetPath"].startswith(".ope/live/prediction-campaigns/"), "target path should be ignored live state")
        require(len(artifact["contentHash"]) == 64, "lifecycle content hash should be sha256")
        require(artifact["schemaFile"].startswith("spec/"), "schema file binding should be checked")

    require(target["workspaceRoot"] == ".ope/live/prediction-campaigns", "workspace root drifted")
    require(target["artifactDirectory"].endswith("/predictionrun-1301"), "artifact directory drifted")
    require(target["forecastArtifactPath"].endswith("/forecast-1301.json"), "forecast target path drifted")
    require(target["questionPath"].endswith("/question-1301.json"), "question target path drifted")
    require(target["evidencePacketPath"].endswith("/evidence-1301.json"), "evidence target path drifted")
    require(target["forecastHistoryPath"].endswith("/history-1301.json"), "history target path drifted")
    require(target["idempotencyKey"] == "predictioncampaign-001:predictionrun-1301:forecast-1301", "idempotency key drifted")
    require(target["relativePathsOnly"] is True, "target paths must stay relative")
    require(target["gitIgnored"] is True, "target state should be ignored")
    require(target["normalChecksWriteLiveState"] is False, "normal checks must not write live state")
    require(target["credentialsStored"] is False, "forecast write must not store credentials")
    require(target["privateRowsStored"] is False, "forecast write must not store private rows")
    require(target["sanitizedDiagnosticsOnly"] is True, "diagnostics boundary drifted")

    require(len(guards) == 8, "forecast write guard count drifted")
    for guard in guards:
        require(guard["guardStatus"] == "pass", "checked fixture guards should pass")
        require(guard["blocksWrite"] is False, "checked fixture guards should not block the ready run")
    require(len([guard for guard in guards if guard["requiredBeforeWrite"]]) == 7, "required guard count drifted")

    require(command["command"] == "python3 scripts/ope.py prediction-campaign forecast-write", "command drifted")
    for flag in ["--run-id", "--manifest-json", "--write-local", "--output-format"]:
        require(flag in command["acceptedFlags"], f"{flag} should be documented by the forecast write surface")
    require(command["defaultMode"] == "checked_write_plan", "default mode drifted")
    require(command["explicitWriteFlagRequired"] is True, "explicit write flag should be required")
    require(command["normalChecksExecuteWrite"] is False, "normal checks must not execute writes")

    require(summary["forecastWritePlanImplemented"] is True, "forecast write plan should be implemented")
    require(summary["effectfulLocalWriteImplemented"] is False, "effectful local write should remain future work")
    require(summary["lifecycleRecordCount"] == 4, "lifecycle count drifted")
    require(summary["writeGuardCount"] == 8, "write guard summary count drifted")
    require(summary["writesIgnoredLiveStateInNormalChecks"] is False, "normal checks must not write ignored state")
    require(summary["normalChecksUseLiveNetwork"] is False, "normal checks must stay offline")
    require(summary["resolverExecutionImplemented"] is False, "forecast write must not run resolvers")
    require(summary["qualityClaimAllowed"] is False, "forecast write must not allow quality claims")

    require(boundary["readOnlyWritePlan"] is True, "boundary should be read-only write planning")
    for key, value in boundary.items():
        if key == "readOnlyWritePlan":
            continue
        require(value is False, f"execution boundary {key} should remain false")

    print("checked prediction campaign forecast write")


if __name__ == "__main__":
    main()
