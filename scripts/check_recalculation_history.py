#!/usr/bin/env python3
"""Check recalculation append-history and leakage guardrails."""

from __future__ import annotations

from generate_recalculation_history import (
    ACCEPTED_RUN_PATH,
    ACCEPTED_TRIGGER_PATH,
    ARTIFACT_PATH,
    EVIDENCE_PATH,
    HISTORY_PATH,
    REJECTED_RUN_PATH,
    REJECTED_TRIGGER_PATH,
    build_outputs,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    outputs = build_outputs()
    accepted_trigger = outputs[ACCEPTED_TRIGGER_PATH]
    rejected_trigger = outputs[REJECTED_TRIGGER_PATH]
    accepted_run = outputs[ACCEPTED_RUN_PATH]
    rejected_run = outputs[REJECTED_RUN_PATH]
    evidence = outputs[EVIDENCE_PATH]
    artifact = outputs[ARTIFACT_PATH]
    history = outputs[HISTORY_PATH]

    require(accepted_trigger["triggerStatus"] == "accepted", "forecast-time trigger should be accepted")
    require(accepted_trigger["availableBeforeForecastClose"] is True, "accepted trigger should be pre-close")
    require(accepted_trigger["postOutcomeEvidence"] is False, "accepted trigger must not use post-outcome evidence")
    require(accepted_trigger["sourceRole"] == "forecast_input", "accepted trigger should be forecast input")

    require(accepted_run["runStatus"] == "updated", "accepted recalculation should update")
    require(accepted_run["previousForecast"]["probability"] == 0.41, "previous probability should be preserved")
    require(accepted_run["updatedForecast"]["probability"] == 0.57, "updated probability should be preserved")
    require(
        accepted_run["updatedForecast"]["forecastId"] == artifact["forecastId"] == evidence["forecastId"],
        "updated forecast should bind artifact and evidence",
    )
    require(
        accepted_run["changedEvidence"]["updatedEvidencePacketId"] == evidence["evidencePacketId"],
        "updated evidence packet should be recorded",
    )

    entries = history["entries"]
    require(len(entries) == 3, "recalculated history should append a third entry")
    require(entries[1]["forecastId"] == "forecast-602", "previous forecast should remain in history")
    require(entries[1]["state"] == "superseded", "previous forecast should become superseded")
    require(entries[2]["forecastId"] == "forecast-801", "updated forecast should be appended")
    require(entries[2]["state"] == "active", "updated forecast should be active")
    require(entries[2]["supersedesForecastId"] == "forecast-602", "updated forecast should supersede previous forecast")

    forecast_source_ids = {source["sourceId"] for source in evidence["provenanceReferences"]}
    resolution_source_ids = {
        evidence["resolutionSource"]["sourceId"],
        *[source["sourceId"] for source in evidence["fallbackResolutionSources"]],
    }
    require(
        not forecast_source_ids.intersection(resolution_source_ids),
        "forecast provenance must not include resolution sources",
    )

    require(rejected_trigger["triggerStatus"] == "rejected", "post-outcome trigger should be rejected")
    require(rejected_trigger["postOutcomeEvidence"] is True, "rejected trigger should demonstrate post-outcome evidence")
    require(
        "post_outcome_evidence" in rejected_trigger["guardrailReasons"],
        "rejected trigger should record post-outcome reason",
    )
    require(rejected_run["runStatus"] == "rejected", "post-outcome recalculation should be rejected")
    require(rejected_run["updatedForecast"] is None, "rejected recalculation must not produce forecast")
    require(
        rejected_run["historyAppend"]["appendedForecastId"] is None,
        "rejected recalculation must not append forecast state",
    )

    print("checked recalculation history")


if __name__ == "__main__":
    main()
