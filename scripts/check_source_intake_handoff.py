#!/usr/bin/env python3
"""Check source-builder to source-intake handoff boundaries."""

from __future__ import annotations

from generate_source_intake_handoff import CASE_ORDER, build_handoffs
from read_ope_record import RECORD_TYPES


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def handoffs_by_case() -> dict[str, dict]:
    return {
        case: records[0]
        for case, records in build_handoffs().items()
    }


def main() -> None:
    handoffs = handoffs_by_case()
    require(set(handoffs) == set(CASE_ORDER), "handoff cases should match expected order")

    unconfirmed = handoffs["unconfirmed_builder_draft"]
    require(unconfirmed["handoffStatus"] == "needs_mapping_confirmation", "unconfirmed draft should need confirmation")
    require(unconfirmed["nextAction"] == "ask_mapping_confirmation", "unconfirmed draft should ask for mapping confirmation")
    require(unconfirmed["sourceIntakeStatus"] == "needs_confirmation", "source intake should classify unconfirmed draft as needs_confirmation")
    require(unconfirmed["forecastGenerationAllowed"] is False, "unconfirmed draft must not allow forecast generation")
    require(unconfirmed["mappingSummary"]["proposedMappingCount"] > 0, "unconfirmed draft should preserve proposed mappings")

    confirmed = handoffs["confirmed_builder_draft"]
    require(confirmed["handoffStatus"] == "ready_for_method_gating", "confirmed draft should be ready for method gating")
    require(confirmed["nextAction"] == "proceed_to_method_gating", "confirmed draft should proceed to method gating")
    require(confirmed["sourceIntakeStatus"] == "accepted", "confirmed draft should produce accepted source intake")
    require(confirmed["mappingSummary"]["requiresConfirmation"] is False, "confirmed draft should have no pending mappings")
    require(confirmed["mappingSummary"]["confirmedMappingCount"] == confirmed["mappingSummary"]["totalMappings"], "all confirmed-draft mappings should be confirmed")

    insufficient = handoffs["insufficient_confirmed_builder_draft"]
    require(insufficient["handoffStatus"] == "needs_more_data", "insufficient draft should need more data")
    require(insufficient["nextAction"] == "collect_more_data", "insufficient draft should ask agent to collect data")
    require(insufficient["sourceIntakeStatus"] == "rejected", "insufficient confirmed draft should be rejected by intake")
    require(insufficient["forecastGenerationAllowed"] is False, "insufficient draft should not allow forecast generation")

    expected_rejections = {
        "contains_secret": "source_contains_secrets",
        "unsupported_format": "unsupported_format",
        "oversized": "file_too_large",
        "leakage": "post_outcome_leakage_indicator",
    }
    for case, reason in expected_rejections.items():
        handoff = handoffs[case]
        require(handoff["handoffStatus"] == "blocked_by_builder_rejection", f"{case} should be blocked by builder")
        require(handoff["nextAction"] == "replace_rejected_sources", f"{case} should ask replacement")
        require(handoff["sourceIntakeStatus"] is None, f"{case} should not enter source intake")
        require(reason in handoff["builderRejectionSummary"]["reasonCodes"], f"{case} should preserve {reason}")
        require(handoff["forecastGenerationAllowed"] is False, f"{case} should not allow forecast generation")

    require(
        "source-intake-handoff" not in RECORD_TYPES,
        "source-intake handoff drafts should not become public read surfaces",
    )
    print("checked source intake handoff")


if __name__ == "__main__":
    main()
