#!/usr/bin/env python3
"""Check agent adapter envelope invariants."""

from __future__ import annotations

from copy import deepcopy
import json

from build_agent_adapter_fixtures import (
    OUTPUT_FILES,
    AgentAdapterError,
    build_envelopes,
    render_json,
    validate_envelope_semantics,
)
from ope_schema import SPEC, validate_record


REQUIRED_SUCCESS_OPERATIONS = {
    "forecast_request_validation",
    "evidence_plan",
    "evidence_trace",
    "forecast_card",
    "lifecycle_bundle",
    "resolution_status",
    "scoring_summary",
}


def text_contains_local_absolute_path(value: object) -> bool:
    return "/Users/" in json.dumps(value, sort_keys=True)


def assert_schema_rejects(data: dict[str, object], label: str) -> None:
    if not validate_record(data, SPEC / "agent-envelope.schema.json"):
        raise AssertionError(f"agent-envelope schema should reject {label}")


def assert_semantics_reject(data: dict[str, object], label: str) -> None:
    try:
        validate_envelope_semantics(data)
    except AgentAdapterError:
        return
    raise AssertionError(f"agent envelope semantic checks should reject {label}")


def main() -> None:
    envelopes = build_envelopes()
    if set(envelopes) != set(OUTPUT_FILES.values()):
        raise AssertionError("agent adapter should emit the expected fixed envelope filenames")
    if len(envelopes) != 8:
        raise AssertionError("agent adapter should emit seven success envelopes and one error envelope")

    success = [item for item in envelopes.values() if item["status"] == "ok"]
    error = [item for item in envelopes.values() if item["status"] == "error"]
    if {item["operation"] for item in success} != REQUIRED_SUCCESS_OPERATIONS:
        raise AssertionError("agent adapter success envelopes should cover every required operation")
    if len(error) != 1:
        raise AssertionError("agent adapter should include exactly one sanitized error example")
    if any(item["exitCode"] != 0 for item in success):
        raise AssertionError("successful agent envelopes should use exit code 0")

    error_envelope = error[0]
    if error_envelope["operation"] != "forecast_card":
        raise AssertionError("sanitized error example should use the forecast-card operation")
    if error_envelope["exitCode"] != 4:
        raise AssertionError("missing record errors should map to exit code 4")
    if error_envelope["error"]["code"] != "not_found":
        raise AssertionError("missing record error should use the not_found code")
    if error_envelope["payload"] is not None:
        raise AssertionError("error envelopes should not carry a success payload")
    if text_contains_local_absolute_path(error_envelope):
        raise AssertionError("sanitized error envelope should not expose absolute local paths")

    by_operation = {item["operation"]: item for item in success}
    request = by_operation["forecast_request_validation"]
    if request["payload"]["decisionStatus"] != "accepted":
        raise AssertionError("request validation envelope should show accepted status")
    if request["state"]["dataMode"] != "auto":
        raise AssertionError("request validation envelope should preserve auto data mode")

    plan = by_operation["evidence_plan"]
    if plan["payload"]["planStatus"] != "planned":
        raise AssertionError("evidence-plan envelope should expose planned status")
    if plan["state"]["executionMode"] != "dry_run":
        raise AssertionError("evidence-plan envelope should expose dry-run execution mode")

    card = by_operation["forecast_card"]
    card_record = card["payload"]["record"]
    if card_record["forecastId"] != "forecast-602":
        raise AssertionError("forecast-card envelope should bind forecast-602")
    if card_record["requestBinding"]["sourceMode"] != "auto_evidence_fixture_replay":
        raise AssertionError("forecast-card envelope should expose auto-evidence fixture replay mode")
    if card_record["qualityClaim"]["status"] != "not_enough_resolved_auto_evidence_outcomes":
        raise AssertionError("forecast-card envelope should preserve quality claim boundary")

    trace = by_operation["evidence_trace"]
    trace_record = trace["payload"]["record"]
    if trace_record["recordBinding"]["sourceConnectorResultSetId"] != "sourceconnectorresults-001":
        raise AssertionError("evidence-trace envelope should preserve connector result-set binding")
    if trace_record["provenanceSummary"]["allEvidenceClaimed"] is not False:
        raise AssertionError("evidence-trace envelope must not claim all evidence coverage")
    if trace_record["controls"]["rawStackTracesExposed"] is not False:
        raise AssertionError("evidence-trace envelope should keep raw diagnostics hidden")

    bundle = by_operation["lifecycle_bundle"]
    if bundle["payload"]["record"]["includedRecords"]["scoringReport"] != "scoring-601":
        raise AssertionError("lifecycle-bundle envelope should include the scoring report")

    resolution = by_operation["resolution_status"]
    if resolution["payload"]["resolutionStatus"] != "resolved":
        raise AssertionError("resolution-status envelope should expose resolved status")
    if resolution["recordBinding"]["resolutionRecordId"] != "resolution-601":
        raise AssertionError("resolution-status envelope should preserve resolution binding")

    scoring = by_operation["scoring_summary"]
    if scoring["payload"]["scoreStatus"] != "scored":
        raise AssertionError("scoring-summary envelope should expose scored status")
    if scoring["payload"]["baselineLift"] <= 0:
        raise AssertionError("scoring-summary envelope should preserve positive baseline lift")
    if scoring["recordBinding"]["scoringReportId"] != "scoring-601":
        raise AssertionError("scoring-summary envelope should preserve scoring binding")

    for filename, item in envelopes.items():
        rendered = render_json(item)
        if '"error": null' not in rendered and item["status"] == "ok":
            raise AssertionError(f"{filename} success envelope should carry an explicit null error")

    malformed_status = deepcopy(card)
    malformed_status["status"] = "error"
    malformed_status["exitCode"] = 0
    malformed_status["error"] = None
    assert_schema_rejects(malformed_status, "error status with exit code 0 and null error")

    operation_mismatch = deepcopy(card)
    operation_mismatch["adapterRequest"]["operation"] = "scoring_summary"
    assert_semantics_reject(operation_mismatch, "adapter operation mismatch")

    binding_mismatch = deepcopy(card)
    binding_mismatch["recordBinding"]["forecastId"] = "forecast-999"
    assert_semantics_reject(binding_mismatch, "forecast binding mismatch")

    print("checked agent adapter envelopes")


if __name__ == "__main__":
    main()
