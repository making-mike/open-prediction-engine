# Field Purpose And Safety Review

This note records the first review pass for the core OPE contracts. It does not replace schema validation or contract tests.

## Public By Default

These fields are intended to be safe for public or shared artifacts when populated carefully:

- record ids: `questionId`, `forecastId`, `historyId`, `evidencePacketId`, `resolutionRecordId`, `scoringReportId`, `pipelineRunId`, `requestId`
- lifecycle fields: `status`, `openAt`, `closeAt`, `resolveAt`, `forecastedAt`, `resolvedAt`
- forecast descriptors: `domain`, `horizon`, `outputType`, `forecastOutput`
- scoring descriptors: `scoringRule`, `scoreStatus`, `primaryScore`, `baselineScore`, `baselineLift`
- aggregate descriptors: `method`, `recencyHandling`, `sourceClass`, `dependencyAssessment`
- track-record counts and summary metrics

These fields should still be reviewed for domain-specific sensitivity. A harmless logistics fixture can become sensitive in a private operational deployment.

## Review Before Public Release

These fields may reveal operational intent, source access, or model behavior:

- `title`
- `background`
- `resolutionCriteria`
- `resolutionAuthority`
- `primaryResolutionSource`
- `fallbackResolutionSources`
- `provenanceReferences`
- `featureSnapshotRef`
- `rationaleSummary`
- `keyFactors`
- `model`
- `sourceFetches`
- `retrievalWindow`
- `leakageControls.auditNotes`

Before publishing these fields, check for private demand signals, source credentials, personal data, protected business information, and post-outcome leakage.

## Private Or Restricted By Default

These fields should usually remain internal unless explicitly cleared:

- raw source URIs for non-public data
- content hashes that reveal private dataset inventory
- model configuration hashes tied to proprietary systems
- benchmark audit notes
- source fetch records for embargoed or paid data
- clarification history containing user-provided private context

## Contract Purpose Summary

| Contract | Purpose | Primary risk |
|---|---|---|
| `forecast-question` | Defines the resolvable question contract. | Vague or sensitive question wording. |
| `forecast-history` | Preserves timestamped forecast states. | Retroactive mutation or private forecast timing leaks. |
| `forecast-artifact` | Carries portable forecast output. | Request/result mismatch. |
| `evidence-packet` | Binds forecast, provenance, baseline, and resolution plan. | Over-sharing source details or model rationale. |
| `aggregate-forecast` | Describes ensemble or aggregate forecasts. | Treating correlated sources as independent. |
| `resolution-record` | Records resolved or unscorable outcomes. | Forcing ambiguous outcomes into normal scores. |
| `scoring-report` | Reports scoring or exclusion result. | Score sign convention confusion. |
| `track-record-report` | Summarizes comparable forecast performance. | Overclaiming from small samples. |
| `calibration-summary` | Reports calibration buckets and error. | Generalizing local calibration across domains. |
| `benchmark-run` | Records anti-leakage benchmark execution. | Post-outcome contamination or source leakage. |
| `forecast-request` | Captures controlled forecast intake. | Private intent, unsafe prompts, or approval bypass. |
| `pipeline-run` | Summarizes local request-to-forecast execution. | Mistaking dry-run artifacts for a hosted service result. |
| `forecast-card` | Provides a compact claim-safe read summary. | Over-trusting a summary without inspecting full lifecycle records. |
| `record-index` | Lists public generated records by read type. | Exposing private or embargoed record existence. |

## Follow-Up

When runtime tooling is selected, turn this review into executable checks where possible:

- reject secret-looking values in public fields
- reject missing resolution authority or source
- reject scored reports for ambiguous and annulled outcomes
- reject mismatched question ids across linked records
- reject benchmark runs without retrieval timestamps
