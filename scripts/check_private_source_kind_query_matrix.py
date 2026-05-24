#!/usr/bin/env python3
"""Check private source-kind query matrix boundaries."""

from __future__ import annotations

from generate_private_source_kind_query_matrix import (
    SOURCE_KIND_ORDER,
    UNSUPPORTED_SOURCE_KIND,
    build_matrix,
)
from generate_private_source_kind_selection_examples import build_examples


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    matrix = build_matrix()
    examples = {
        item["sourceKind"]: item
        for item in build_examples()["selectionExamples"]
    }
    cases = matrix["queryCases"]

    require(len(cases) == 10, "query matrix should include full, eight selected, and unsupported cases")
    require(cases[0]["queryMode"] == "full_list", "first query case should be the full list")
    full_envelope = cases[0]["envelope"]
    require(full_envelope["status"] == "ok", "full-list query should succeed")
    require(cases[0]["payloadShape"] == "full_examples", "full-list query should return full examples")
    require(
        "selectionExamples" in full_envelope["payload"],
        "full-list query should include selection examples",
    )

    selected_cases = cases[1:9]
    require(
        [case["sourceKind"] for case in selected_cases] == SOURCE_KIND_ORDER,
        "selected query cases should preserve source-kind order",
    )
    for case in selected_cases:
        source_kind = case["sourceKind"]
        envelope = case["envelope"]
        payload = envelope["payload"]
        expected = examples[source_kind]
        require(case["queryMode"] == "selected_source_kind", f"{source_kind} should be selected mode")
        require(envelope["status"] == "ok", f"{source_kind} selected query should succeed")
        require(envelope["exitCode"] == 0, f"{source_kind} selected query should exit 0")
        require(case["payloadShape"] == "selected_example_only", f"{source_kind} should be compact")
        require("selectionExamples" not in payload, f"{source_kind} selected query should omit full examples")
        require(payload["requestedSourceKind"] == source_kind, f"{source_kind} should echo source kind")
        require(payload["selectedExample"]["selectionExampleId"] == expected["selectionExampleId"], f"{source_kind} selected example drift")
        require(
            payload["selectedExample"]["recommendation"]["immediateAction"] == case["expectedImmediateAction"],
            f"{source_kind} immediate action drift",
        )
        require(envelope["state"]["sourceMode"] == source_kind, f"{source_kind} state source mode drift")
        require(envelope["state"]["planStatus"] == "selected_example_only", f"{source_kind} state status drift")
        boundary = payload["executionBoundary"]
        require(boundary["examplesDoNotExecute"] is True, f"{source_kind} should not execute")
        require(boundary["runsCommands"] is False, f"{source_kind} should not run commands")
        require(boundary["createsForecastArtifacts"] is False, f"{source_kind} should not create forecasts")
        require(boundary["createsScoringRecords"] is False, f"{source_kind} should not create scores")

    unsupported = cases[-1]
    unsupported_envelope = unsupported["envelope"]
    require(unsupported["queryMode"] == "unsupported_source_kind", "last query case should be unsupported")
    require(unsupported["sourceKind"] == UNSUPPORTED_SOURCE_KIND, "unsupported case should use checked unsupported kind")
    require(unsupported_envelope["status"] == "error", "unsupported query should return error envelope")
    require(unsupported_envelope["exitCode"] == 2, "unsupported query should map to exit code 2")
    require(unsupported_envelope["error"]["code"] == "bad_request", "unsupported query should be bad_request")
    require(unsupported_envelope["payload"] is None, "unsupported query should not include payload")
    require(unsupported_envelope["state"]["sourceMode"] == UNSUPPORTED_SOURCE_KIND, "unsupported query should preserve source mode")

    boundary = matrix["executionBoundary"]
    require(boundary["matrixDoesNotExecute"] is True, "matrix should not execute")
    require(boundary["usesAdapterEnvelopeOnly"] is True, "matrix should use adapter envelope only")
    for key in [
        "readsPrivateData",
        "runsCommands",
        "createsSourceManifests",
        "createsFieldMappings",
        "createsForecastArtifacts",
        "createsScoringRecords",
        "fetchesLiveData",
        "storesCredentials",
        "createsHostedRuntime",
    ]:
        require(boundary[key] is False, f"{key} should remain false")

    print("checked private source-kind query matrix")


if __name__ == "__main__":
    main()
