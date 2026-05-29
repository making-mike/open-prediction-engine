#!/usr/bin/env python3
"""Validate read-surface outputs against explicit contracts."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ope_schema import SPEC, load_json, validate_record
from read_ope_record import read_record


ROOT = Path(__file__).resolve().parents[1]
RECORD_INDEX = ROOT / "spec" / "fixtures" / "generated" / "record-index.generated.json"
FORECAST_CARD_SCHEMA = SPEC / "forecast-card.schema.json"
EVIDENCE_TRACE_SCHEMA = SPEC / "evidence-trace.schema.json"
RECORD_INDEX_SCHEMA = SPEC / "record-index.schema.json"


def assert_valid(data: object, schema_path: Path, label: str) -> None:
    errors = validate_record(data, schema_path)
    if errors:
        raise AssertionError(f"{label} failed schema validation: {errors[0]}")


def main() -> None:
    index = load_json(RECORD_INDEX)
    assert_valid(index, RECORD_INDEX_SCHEMA, "record index")
    indexed_types = {record_set["recordType"] for record_set in index["recordSets"]}
    for required_type in [
        "evidence-source-set",
        "evidence-trace",
        "forecast-artifact",
        "forecast-bundle",
        "forecast-card",
        "source-connector-results",
        "track-record",
    ]:
        if required_type not in indexed_types:
            raise AssertionError(f"record index missing {required_type}")

    card_response = read_record("forecast-card", "forecast-502", "question-501")
    card = card_response["record"]
    assert_valid(card, FORECAST_CARD_SCHEMA, "forecast card")
    if card["qualityClaim"]["minimumSampleSize"] <= card["qualityClaim"]["resolvedComparableOutcomes"]:
        raise AssertionError("forecast card should preserve below-threshold claim boundary")
    if card["requestBinding"]["effectfulGeneration"] is not False:
        raise AssertionError("forecast card should preserve dry-run request binding")

    auto_card_response = read_record("forecast-card", "forecast-602", "question-601")
    auto_card = auto_card_response["record"]
    assert_valid(auto_card, FORECAST_CARD_SCHEMA, "auto-evidence forecast card")
    if auto_card["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("auto-evidence forecast card should preserve claim boundary")
    if auto_card["requestBinding"]["sourcePolicyId"] != "sourcepolicy-019":
        raise AssertionError("auto-evidence forecast card should preserve source-policy binding")
    if auto_card["links"]["evidenceTrace"] != "evidencetrace-602":
        raise AssertionError("auto-evidence forecast card should link evidence trace")

    historical_card_response = read_record("forecast-card", "forecast-702", "question-701")
    historical_card = historical_card_response["record"]
    assert_valid(historical_card, FORECAST_CARD_SCHEMA, "historical baseline forecast card")
    if historical_card["forecast"] != historical_card["baseline"]:
        raise AssertionError("historical forecast card should expose baseline equality")
    if historical_card["links"]["evidenceTrace"] is not None:
        raise AssertionError("historical forecast card should not link an evidence trace")
    if historical_card["requestBinding"]["sourceMode"] != "committed_fixture":
        raise AssertionError("historical forecast card should preserve committed fixture source mode")

    setup_card_response = read_record("forecast-card", "forecast-901", "question-901")
    setup_card = setup_card_response["record"]
    assert_valid(setup_card, FORECAST_CARD_SCHEMA, "setup forecast card")
    if setup_card["setupBinding"]["setupForecastRunId"] != "setupforecastrun-901":
        raise AssertionError("setup forecast card should preserve setup run binding")
    if setup_card["setupBinding"]["sourceIntakeReportId"] != "sourceintakereport-001":
        raise AssertionError("setup forecast card should preserve source-intake binding")
    if setup_card["setupBinding"]["setupBenchmarkGateId"] != "setupbenchmarkgate-001":
        raise AssertionError("setup forecast card should preserve setup benchmark binding")
    if setup_card["forecast"]["probability"] <= setup_card["baseline"]["probability"]:
        raise AssertionError("setup forecast card should expose deterministic lift over baseline")
    if setup_card["links"]["evidenceTrace"] is not None:
        raise AssertionError("setup forecast card should not link an evidence trace")

    handoff_card_response = read_record("forecast-card", "forecast-1102", "question-1102")
    handoff_card = handoff_card_response["record"]
    assert_valid(handoff_card, FORECAST_CARD_SCHEMA, "source-handoff setup forecast card")
    if handoff_card["setupBinding"]["setupForecastRunId"] != "setupforecastrun-1102":
        raise AssertionError("source-handoff forecast card should preserve setup run binding")
    if handoff_card["setupBinding"]["sourceIntakeHandoffId"] != "sourceintakehandoff-002":
        raise AssertionError("source-handoff forecast card should preserve handoff binding")
    if handoff_card["setupBinding"]["sourceHandoffMethodGateId"] != "sourcehandoffmethodgate-002":
        raise AssertionError("source-handoff forecast card should preserve method gate binding")
    if handoff_card["setupBinding"]["setupBenchmarkGateId"] != "setupbenchmarkgate-102":
        raise AssertionError("source-handoff forecast card should preserve benchmark binding")
    if handoff_card["forecast"]["probability"] <= handoff_card["baseline"]["probability"]:
        raise AssertionError("source-handoff forecast card should expose deterministic lift over baseline")
    if handoff_card["links"]["evidenceTrace"] is not None:
        raise AssertionError("source-handoff forecast card should not link an evidence trace")

    campaign_card_response = read_record("forecast-card", "forecast-1301", "question-1301")
    campaign_card = campaign_card_response["record"]
    assert_valid(campaign_card, FORECAST_CARD_SCHEMA, "prediction campaign forecast card")
    if campaign_card["status"] != "open":
        raise AssertionError("prediction campaign forecast card should remain open")
    if campaign_card["score"] is not None:
        raise AssertionError("prediction campaign forecast card should remain unscored")
    if campaign_card["forecast"] != campaign_card["baseline"]:
        raise AssertionError("prediction campaign forecast card should preserve baseline-only output")
    if campaign_card["requestBinding"]["pipelineRunId"] is not None:
        raise AssertionError("prediction campaign forecast card should not invent a pipeline run")

    trace_response = read_record("evidence-trace", "forecast-602", "question-601")
    trace = trace_response["record"]
    assert_valid(trace, EVIDENCE_TRACE_SCHEMA, "evidence trace")
    if trace["recordBinding"]["sourceConnectorRegistryId"] != "sourceconnectorregistry-001":
        raise AssertionError("evidence trace should preserve connector registry binding")
    if trace["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence trace should preserve connector result-set binding")
    if trace["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("evidence trace should not claim all evidence coverage")
    if trace["controls"]["promptVisibleCredentialsAccepted"] is not False:
        raise AssertionError("evidence trace should not accept prompt-visible credentials")

    malformed = deepcopy(card)
    del malformed["warnings"]
    if not validate_record(malformed, FORECAST_CARD_SCHEMA):
        raise AssertionError("forecast-card schema should reject missing warnings")

    print("checked read surface contracts")


if __name__ == "__main__":
    main()
