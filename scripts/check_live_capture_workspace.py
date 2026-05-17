#!/usr/bin/env python3
"""Check ignored local live capture workspace boundaries."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from fetch_open_meteo_weather import build_url, load_fixture, normalize_response
from generate_live_connector_readiness import build_readiness
from live_capture_workspace import (
    DEFAULT_WORKSPACE,
    build_draft_source_set,
    build_live_result_set,
    render_json,
    save_live_result_set,
    validate_live_capture_file,
)
from plan_auto_evidence import DEFAULT_REQUEST, build_plan


ROOT = Path(__file__).resolve().parents[1]
WEATHER_FIXTURE = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
RECORD_INDEX = ROOT / "spec" / "fixtures" / "generated" / "record-index.generated.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def fixture_integration_result() -> dict:
    service_date = "2026-06-03"
    location = "warsaw"
    payload, raw = load_fixture(WEATHER_FIXTURE)
    normalized = normalize_response(
        payload=payload,
        raw=raw,
        source_url=build_url(location, service_date),
        retrieved_at="2026-06-02T09:30:00Z",
        location_key=location,
        service_date=service_date,
    )
    return {
        "mode": "integration_live_fetch",
        "serviceDate": service_date,
        "location": location,
        "connectorKey": "open_meteo_weather",
        "sourceConnectorRegistryId": "sourceconnectorregistry-001",
        "sourceConnectorResultSetId": "sourceconnectorresults-001",
        "connectorResultId": "connectorresult-001",
        "controls": {
            "networkAccess": True,
            "liveFetch": True,
            "effectfulGeneration": False,
            "credentialUsed": False,
            "promptVisibleCredentialAccepted": False,
        },
        "resultStatus": "succeeded_live_fetch",
        "rawSourceMetadata": {
            "mode": "live_fetch",
            "sourceUri": normalized["sourceRef"]["uri"],
            "contentHash": normalized["sourceRef"]["contentHash"],
            "rawPreviewStored": False,
        },
        "provenance": {
            "sourceRef": normalized["sourceRef"],
            "retrievedAt": normalized["sourceRef"]["retrievedAt"],
            "storesContentHash": True,
            "allEvidenceClaimed": False,
        },
        "normalizedFields": normalized["normalizedFields"],
        "retrievalDiagnostics": {
            "diagnosticLevel": "none",
            "publicMessage": "Opt-in live Open-Meteo readiness fetch succeeded.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
    }


def failed_integration_result() -> dict:
    result = fixture_integration_result()
    return {
        **result,
        "resultStatus": "failed_sanitized",
        "rawSourceMetadata": None,
        "provenance": None,
        "normalizedFields": None,
        "retrievalDiagnostics": {
            "diagnosticLevel": "sanitized",
            "publicMessage": "Live connector check failed; inspect trusted local logs or rerun explicitly.",
            "rawDiagnosticStored": False,
            "rawStackTraceExposed": False,
        },
    }


def check_gitignore_and_public_index() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    require(".ope/live/" in gitignore, ".ope/live/ should stay git ignored")
    index = json.loads(RECORD_INDEX.read_text(encoding="utf-8"))
    serialized = json.dumps(index)
    require(".ope/live" not in serialized, "public record index must not expose local live captures")
    require(index["access"]["source"] == "spec/fixtures/generated", "record index should remain committed-fixture scoped")


def check_capture_round_trip() -> None:
    readiness = build_readiness(DEFAULT_REQUEST)
    plan = build_plan(DEFAULT_REQUEST)
    require(plan["sourcePolicy"]["allowNetworkAccess"] is True, "auto request should allow explicit live readiness")
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / ".ope" / "live"
        result_set = build_live_result_set(
            readiness=readiness,
            integration_result=fixture_integration_result(),
            request_path=DEFAULT_REQUEST,
            generated_at="2026-06-02T09:40:00Z",
        )
        path = save_live_result_set(
            result_set=result_set,
            workspace=workspace,
            location="warsaw",
            service_date="2026-06-03",
        )
        require(path.exists(), "local live capture should be written")
        require(DEFAULT_WORKSPACE.name == "live", "default local live workspace should be .ope/live")

        loaded = validate_live_capture_file(path)
        require(loaded["executionMode"] == "integration_live_fetch", "live capture should preserve integration mode")
        require(loaded["controls"]["networkAccess"] is True, "live capture should record network access")
        require(loaded["connectorResults"][0]["rawSourceMetadata"]["rawPreviewStored"] is False, "raw previews must not be stored")

        draft = build_draft_source_set(result_set=loaded, request_path=DEFAULT_REQUEST)
        require(draft["executionMode"] == "live_fetch", "draft source set should mark live_fetch")
        require(draft["controls"]["effectfulGeneration"] is False, "draft source set must not forecast")
        require(draft["provenanceSummary"]["allEvidenceClaimed"] is False, "draft must not claim all evidence")
        require(draft["records"][0]["rawSourceMetadata"]["fixturePath"] is None, "live draft should not fake a fixture path")
        require(draft["records"][0]["sourceQuality"]["freshnessStatus"] == "within_policy", "draft should enforce freshness")


def check_failed_capture_cannot_become_draft() -> None:
    readiness = build_readiness(DEFAULT_REQUEST)
    result_set = build_live_result_set(
        readiness=readiness,
        integration_result=failed_integration_result(),
        request_path=DEFAULT_REQUEST,
        generated_at="2026-06-02T09:40:00Z",
    )
    require(result_set["connectorResults"][0]["resultStatus"] == "failed_sanitized", "failed capture should stay sanitized")
    try:
        build_draft_source_set(result_set=result_set, request_path=DEFAULT_REQUEST)
    except Exception as exc:
        require("requires exactly one successful" in str(exc), "failed capture should fail for the expected reason")
    else:
        raise AssertionError("failed live capture should not become evidence source-set draft")


def main() -> None:
    check_gitignore_and_public_index()
    check_capture_round_trip()
    check_failed_capture_cannot_become_draft()
    print("checked local live capture workspace")


if __name__ == "__main__":
    main()
