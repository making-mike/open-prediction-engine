# Read-Only Record Access

Status: implemented as a local file interface.

OPE currently exposes read-only access through `scripts/read_ope_record.py`. It does not start a server, generate forecasts, fetch live sources, or mutate repository files.

## Supported Records

Supported record types:

- `forecast-bundle`
- `forecast-card`
- `forecast-artifact`
- `track-record`

Forecast bundles are assembled on read from public generated records and are looked up by `forecastId`.

Forecast cards are compact, claim-safe summaries assembled from the same lifecycle records and are looked up by `forecastId`.

Forecast artifacts are looked up by `forecastId`.

Track records are looked up by `trackRecordReportId`.

## Usage

Read a forecast artifact:

```bash
python3 scripts/read_ope_record.py --record-type forecast-artifact --id forecast-101 --question-id question-101
```

Read a forecast lifecycle bundle:

```bash
python3 scripts/read_ope_record.py --record-type forecast-bundle --id forecast-502 --question-id question-501
python3 scripts/ope.py read --record-type forecast-bundle --id forecast-502 --question-id question-501
```

Read a compact forecast card:

```bash
python3 scripts/ope.py read --record-type forecast-card --id forecast-502 --question-id question-501
```

Read a track record:

```bash
python3 scripts/read_ope_record.py --record-type track-record --id trackrecord-101
```

List public records:

```bash
python3 scripts/read_ope_record.py --record-type forecast-artifact --list --domain weather-logistics
python3 scripts/ope.py list --record-type track-record
```

## Safety Rules

The file interface enforces:

- one record per request
- response-size limit through `--max-bytes`
- optional question binding for question-scoped records
- forecast artifact binding to the sibling evidence packet when available
- forecast bundle binding across artifact, evidence, history, resolution, scoring, outcome summary, and pipeline run records when those records exist
- forecast cards omit source hashes, supporting evidence URIs, raw provenance arrays, and full rationale text
- public error sanitization
- access denial for private or embargoed records
- generated record index drift checks through `scripts/generate_record_index.py`
- schema checks for forecast cards and the public record index through `scripts/check_read_contracts.py`

Errors are returned as JSON with stable public codes. Local filesystem paths are not included in public error messages.

## Non-Goals

This is not a network API, authorization system, or live forecast request surface. It is a local read-only interface over committed and generated fixture records.
