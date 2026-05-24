#!/usr/bin/env python3
"""Check private setup first-action dispatcher boundaries."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from generate_private_setup_first_actions import build_actions
from generate_private_setup_requests import build_request_set
from private_setup_action_dispatcher import dispatch_action


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_dispatcher(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/private_setup_action_dispatcher.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )


def main() -> None:
    request_set = build_request_set()
    request_rows = {row["selectedSourceKind"]: row for row in request_set["requestRows"]}
    actions = build_actions()
    action_rows = {row["sourceKind"]: row for row in actions}

    require(set(action_rows) == set(request_rows), "first actions should cover every private setup request row")

    for source_kind, action in action_rows.items():
        request_row = request_rows[source_kind]
        binding = action["requestBinding"]
        require(
            binding["privateSetupRequestSetId"] == request_set["privateSetupRequestSetId"],
            f"{source_kind} should bind request set",
        )
        require(
            binding["privateSetupRequestId"] == request_row["privateSetupRequestId"],
            f"{source_kind} should bind request id",
        )
        require(
            binding["boundPrivateSourceAdapterIntakeBridgeId"]
            == request_set["boundPrivateSourceAdapterIntakeBridgeId"],
            f"{source_kind} should bind adapter bridge",
        )
        require(action["routeDecision"] == request_row["routeDecision"], f"{source_kind} route decision drifted")
        require(action["allowedEntrypoint"] == request_row["allowedEntrypoint"], f"{source_kind} entrypoint drifted")
        require(action["commandToRun"] == request_row["commandToRun"], f"{source_kind} command drifted")
        boundary = action["executionBoundary"]
        require(boundary["dispatcherDoesNotExecute"] is True, f"{source_kind} dispatcher should not execute")
        require(boundary["runsSuggestedCommand"] is False, f"{source_kind} dispatcher should not run commands")
        for key in [
            "readsPrivateData",
            "createsSourceManifests",
            "createsFieldMappings",
            "createsForecastArtifacts",
            "createsScoringRecords",
            "storesCredentials",
        ]:
            require(boundary[key] is False, f"{source_kind} {key} should remain false")

    require(
        action_rows["local_file"]["actionStatus"] == "ready_to_run_checked_command",
        "local file should be ready for source-builder command",
    )
    require(action_rows["local_file"]["error"]["code"] == "none", "local file should not surface an error")
    require(
        action_rows["manual_mapping"]["actionStatus"] == "confirmation_required",
        "manual mapping should require confirmation",
    )
    require(
        action_rows["manual_mapping"]["error"]["code"] == "confirmation_required",
        "manual mapping should expose confirmation error code",
    )
    require(
        action_rows["auto_evidence_connector"]["actionStatus"] == "fixture_ready",
        "auto evidence should be fixture-ready",
    )
    require(
        action_rows["auto_evidence_connector"]["commandToRun"] == "python3 scripts/ope.py gather-evidence",
        "auto evidence command should route to fixture gathering",
    )
    for source_kind in ["manual_upload", "private_api", "private_database"]:
        require(
            action_rows[source_kind]["actionStatus"] == "runtime_not_implemented",
            f"{source_kind} should wait for runtime",
        )
        require(action_rows[source_kind]["commandToRun"] == "none", f"{source_kind} should expose no command")
    require(
        action_rows["unregistered_source"]["actionStatus"] == "source_replacement_required",
        "unregistered source should ask for replacement",
    )
    require(
        action_rows["unsafe_source"]["actionStatus"] == "rejected_unsafe_source",
        "unsafe source should be rejected",
    )

    dispatched = dispatch_action(request_id="privatesetuprequest-001")
    require(dispatched["sourceKind"] == "local_file", "dispatch by request id should return local file")
    require(dispatched["exitCode"] == 0, "dispatch by request id should succeed")

    unknown = dispatch_action(request_id="privatesetuprequest-999")
    require(unknown["actionStatus"] == "bad_request", "unknown request id should return bad_request action")
    require(unknown["error"]["code"] == "bad_request", "unknown request id should use bad_request code")
    require(unknown["exitCode"] == 2, "unknown request id should use exit code 2")

    with tempfile.TemporaryDirectory() as tmp:
        unknown_path = Path(tmp) / "unknown-source.json"
        unknown_path.write_text(
            json.dumps(
                {
                    "privateSetupRequestId": "privatesetuprequest-990",
                    "selectedSourceKind": "spreadsheet_macro",
                    "sourcePolicy": {
                        "dataMode": "provided",
                        "allowedSourceKinds": ["spreadsheet_macro"],
                        "approvalStatus": "confirmed",
                        "allowLiveFetch": False,
                        "allowCredentialUse": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        completed = run_dispatcher("--input", str(unknown_path))
        require(completed.returncode == 2, "unknown source kind should exit 2")
        payload = json.loads(completed.stdout)
        require(payload["actionStatus"] == "bad_request", "unknown source kind should return bad_request")
        require(payload["error"]["code"] == "unknown_source_kind", "unknown source kind should be sanitized")
        require(payload["executionBoundary"]["runsSuggestedCommand"] is False, "unknown source should not execute")

        missing_approval_path = Path(tmp) / "missing-approval.json"
        missing_approval_path.write_text(
            json.dumps(
                {
                    "privateSetupRequestId": "privatesetuprequest-991",
                    "selectedSourceKind": "private_api",
                    "sourcePolicy": {
                        "dataMode": "provided",
                        "allowedSourceKinds": ["private_api"],
                        "approvalStatus": "requested",
                        "allowLiveFetch": False,
                        "allowCredentialUse": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        missing_approval = run_dispatcher("--input", str(missing_approval_path))
        require(missing_approval.returncode == 2, "missing approval should exit 2")
        missing_payload = json.loads(missing_approval.stdout)
        require(missing_payload["error"]["code"] == "missing_approval", "missing approval should be sanitized")
        require(missing_payload["allowedEntrypoint"] == "no_current_entrypoint", "missing approval should block entrypoint")

    print("checked private setup first actions")


if __name__ == "__main__":
    main()
