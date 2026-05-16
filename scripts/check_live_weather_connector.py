#!/usr/bin/env python3
"""Check the allow-listed live weather connector in fixture mode."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from fetch_open_meteo_weather import (
    DAILY_VARIABLES,
    OPEN_METEO_ENDPOINT,
    build_url,
    load_fixture,
    normalize_response,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-forecast-response.json"
MISSING_DATE_FIXTURE = ROOT / "spec" / "fixtures" / "live" / "open-meteo-warsaw-missing-date-response.json"
SERVICE_DATE = "2026-06-03"
RETRIEVED_AT = "2026-06-02T09:30:00Z"


def main() -> None:
    url = build_url("warsaw", SERVICE_DATE)
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if f"{parsed.scheme}://{parsed.netloc}{parsed.path}" != OPEN_METEO_ENDPOINT:
        raise AssertionError("connector must use the allow-listed Open-Meteo forecast endpoint")
    if query.get("daily") != [",".join(DAILY_VARIABLES)]:
        raise AssertionError("connector daily variables drifted from the allow-list")
    if query.get("timezone") != ["Europe/Warsaw"]:
        raise AssertionError("connector must request the allow-listed Warsaw timezone")
    if query.get("start_date") != [SERVICE_DATE] or query.get("end_date") != [SERVICE_DATE]:
        raise AssertionError("connector must request exactly one service date")

    payload, raw = load_fixture(FIXTURE)
    normalized = normalize_response(
        payload=payload,
        raw=raw,
        source_url=url,
        retrieved_at=RETRIEVED_AT,
        location_key="warsaw",
        service_date=SERVICE_DATE,
    )
    if normalized["sourceRef"]["sourceType"] != "public_dataset":
        raise AssertionError("live weather source must normalize as public_dataset")
    fields = normalized["normalizedFields"]
    if fields["forecastDailyPrecipitationMm"] != 24:
        raise AssertionError("fixture precipitation normalization drifted")
    if fields["precipitationProbabilityMaxPercent"] != 86:
        raise AssertionError("fixture precipitation probability normalization drifted")
    if not normalized["sourceRef"]["contentHash"].startswith("sha256-"):
        raise AssertionError("normalized live source must include a content hash")
    if normalized["correctionReviewRequired"] is not False:
        raise AssertionError("current source should not require correction review")

    corrected = normalize_response(
        payload=payload,
        raw=raw,
        source_url=url,
        retrieved_at=RETRIEVED_AT,
        location_key="warsaw",
        service_date=SERVICE_DATE,
        source_status="corrected",
    )
    if corrected["sourceStatus"] != "corrected":
        raise AssertionError("corrected source status was not preserved")
    if corrected["correctionReviewRequired"] is not True:
        raise AssertionError("corrected source should require review")

    missing_payload, missing_raw = load_fixture(MISSING_DATE_FIXTURE)
    try:
        normalize_response(
            payload=missing_payload,
            raw=missing_raw,
            source_url=url,
            retrieved_at=RETRIEVED_AT,
            location_key="warsaw",
            service_date=SERVICE_DATE,
        )
    except ValueError as exc:
        if "does not include service date" not in str(exc):
            raise
    else:
        raise AssertionError("missing service date fixture should be treated as stale/unusable")
    json.dumps(normalized)
    print("checked live weather connector fixture mode")


if __name__ == "__main__":
    main()
