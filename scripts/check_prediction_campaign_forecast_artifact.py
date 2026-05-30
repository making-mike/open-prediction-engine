#!/usr/bin/env python3
"""Check prediction campaign forecast artifact invariants."""

from __future__ import annotations

from datetime import datetime

from generate_prediction_campaign_forecast_artifact import build_prediction_campaign_forecast_artifact


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> None:
    records = build_prediction_campaign_forecast_artifact()
    question = records["question"]
    evidence = records["evidence"]
    artifact = records["artifact"]
    history = records["history"]

    require(question["questionId"] == "question-1301", "campaign forecast question ID drifted")
    require(question["status"] == "open", "campaign forecast question should remain open")
    require(question["domain"] == "weather-transit-delays", "campaign forecast question domain drifted")
    require(question["primaryResolutionSource"]["sourceId"] == "source-1304", "future outcome source binding drifted")
    require(question["incentiveRiskReview"]["riskLevel"] == "minimal", "campaign forecast risk level drifted")

    require(artifact["forecastId"] == "forecast-1301", "campaign forecast artifact ID drifted")
    require(artifact["questionId"] == question["questionId"], "campaign forecast question binding drifted")
    require(artifact["evidencePacketId"] == "evidence-1301", "campaign evidence packet binding drifted")
    require(artifact["questionStatus"] == "open", "campaign forecast artifact should remain unresolved")
    require(artifact["forecastOutput"] == artifact["baselineForecast"], "campaign forecast must remain baseline-only")
    require(artifact["forecastOutput"]["probability"] == 0.25, "campaign baseline probability drifted")
    require(
        parse_time(artifact["forecastedAt"]) < parse_time(artifact["closedAt"]),
        "campaign forecast must be created before close",
    )
    require(
        parse_time(artifact["closedAt"]) < parse_time(artifact["horizon"]["startsAt"]),
        "campaign forecast must close before horizon starts",
    )

    require(evidence["forecastId"] == artifact["forecastId"], "campaign evidence forecast binding drifted")
    require(evidence["questionId"] == question["questionId"], "campaign evidence question binding drifted")
    require(evidence["forecastOutput"] == artifact["forecastOutput"], "campaign evidence forecast drifted")
    require(evidence["baselineForecast"] == artifact["baselineForecast"], "campaign evidence baseline drifted")
    require("public_dataset" in evidence["inputSourceClasses"], "campaign evidence should bind historical fixture data")
    require("other" in evidence["inputSourceClasses"], "campaign evidence should bind campaign control records")
    require(len(evidence["provenanceReferences"]) == 3, "campaign provenance reference count drifted")
    require(
        any(ref["sourceId"] == "source-1302" for ref in evidence["provenanceReferences"]),
        "campaign manifest provenance missing",
    )
    require(
        any(ref["sourceId"] == "source-1303" for ref in evidence["provenanceReferences"]),
        "campaign forecast-creation provenance missing",
    )
    require(
        "baseline-only default" in " ".join(evidence["keyFactors"]),
        "campaign evidence should preserve baseline-only method reason",
    )

    require(history["historyId"] == "history-1301", "campaign forecast history ID drifted")
    require(history["questionId"] == question["questionId"], "campaign history question binding drifted")
    require(len(history["entries"]) == 1, "campaign history should contain one active entry")
    entry = history["entries"][0]
    require(entry["forecastId"] == artifact["forecastId"], "campaign history forecast binding drifted")
    require(entry["sourceClass"] == "baseline", "campaign history source class should remain baseline")
    require(entry["evidencePacketId"] == evidence["evidencePacketId"], "campaign history evidence binding drifted")

    print("checked prediction campaign forecast artifact")


if __name__ == "__main__":
    main()
