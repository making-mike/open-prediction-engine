#!/usr/bin/env python3
"""Check local source manifest builder boundaries."""

from __future__ import annotations

from build_source_manifest import CASE_ORDER, build_case
from read_ope_record import RECORD_TYPES


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def reason_codes(build: dict) -> set[str]:
    codes: set[str] = set()
    for item in build["inputFiles"]:
        codes.update(item["reasonCodes"])
    return codes


def main() -> None:
    built = {case: build_case(case) for case in CASE_ORDER}

    local_build, manifest, field_mapping = built["local_draft"]
    require(local_build["buildStatus"] == "draft_ready", "local draft case should be draft-ready")
    require(local_build["canEnterSourceIntake"] is True, "local draft should be suitable for source intake")
    require(local_build["forecastGenerationAllowed"] is False, "builder must not allow forecast execution")
    require(local_build["confirmationRequired"] is True, "agent-inferred mappings should require confirmation")
    require(manifest is not None, "local draft should emit a source manifest")
    require(field_mapping is not None, "local draft should emit a field mapping")

    formats = {item["fileFormat"] for item in local_build["inputFiles"]}
    require({"csv", "json"}.issubset(formats), "builder should inspect both CSV and JSON files")
    require(
        all(item["inspectionStatus"] == "inspected" for item in local_build["inputFiles"]),
        "local draft files should be inspected",
    )
    require(
        all(item["forecastGenerationAllowed"] is False for item in [local_build]),
        "builder records should keep forecast generation blocked",
    )

    assert manifest is not None
    weather_source = next(source for source in manifest["sources"] if source["sourceRole"] == "weather_forecast")
    require(weather_source["connectorType"] == "local_file", "draft sources should use local_file connector type")
    require(weather_source["privacy"]["privacyClass"] == "public", "public dataset drafts should retain public privacy class")
    require(weather_source["retrieval"]["availableBeforeForecastClose"] is True, "weather draft should be pre-close")
    require(
        weather_source["featureSummary"]["numericValues"][0]["fieldName"] == "forecast_daily_precipitation_mm",
        "weather draft should expose sanitized precipitation feature summary",
    )
    require(
        all(
            field["exampleValuesStored"] is False
            for source in manifest["sources"]
            for field in source["fieldInventory"]
        ),
        "draft manifests must not store raw example values",
    )

    assert field_mapping is not None
    mapping_origins = {item["mappingOrigin"] for item in field_mapping["mappings"]}
    require("user_provided" in mapping_origins, "draft mapping should include user-provided mapping hints")
    require("registry_backed" in mapping_origins, "draft mapping should include registry-backed mappings")
    require("agent_inferred" in mapping_origins, "draft mapping should include agent-inferred mappings")
    require(
        all(
            item["mappingStatus"] == "proposed" and item["requiresConfirmation"] is True
            for item in field_mapping["mappings"]
            if item["mappingOrigin"] == "agent_inferred"
        ),
        "agent-inferred field mappings must stay proposed and confirmation-gated",
    )
    require(
        all(
            item["mappingStatus"] == "proposed" and item["requiresConfirmation"] is True
            for item in field_mapping["aliasMappings"]
            if item["mappingOrigin"] == "agent_inferred"
        ),
        "agent-inferred alias mappings must stay proposed and confirmation-gated",
    )

    expected_rejections = {
        "contains_secret": "source_contains_secrets",
        "unsupported_format": "unsupported_format",
        "oversized": "file_too_large",
        "leakage": "post_outcome_leakage_indicator",
    }
    for case, reason in expected_rejections.items():
        build, rejected_manifest, rejected_mapping = built[case]
        require(build["buildStatus"] == "rejected", f"{case} should be rejected")
        require(build["canEnterSourceIntake"] is False, f"{case} should not enter source intake")
        require(build["forecastGenerationAllowed"] is False, f"{case} should not allow forecast generation")
        require(reason in reason_codes(build), f"{case} should include {reason}")
        require(rejected_manifest is None, f"{case} should not emit a draft manifest")
        require(rejected_mapping is None, f"{case} should not emit a draft mapping")
        require(build["draftArtifacts"]["sourceManifestId"] is None, f"{case} should not bind draft artifacts")

    require(
        "source-manifest-build" not in RECORD_TYPES,
        "source builder drafts should not become public read surfaces",
    )
    print("checked source manifest builder")


if __name__ == "__main__":
    main()
