# Question Lifecycle

OPE treats each forecast question as a scoring contract. Background text can help model or human forecasters, but resolution criteria must be able to stand on their own.

## States

| State | Meaning |
|---|---|
| `draft` | Question is being prepared and must not accept forecasts. |
| `approved` | Question contract passed review but is not yet open. |
| `open` | Forecasts may be accepted. |
| `closed` | Forecast intake is closed, but the outcome is not yet recorded. |
| `resolved` | Outcome was recorded from declared sources. |
| `ambiguous` | Reality cannot be determined clearly enough from the declared sources. |
| `annulled` | Reality may be knowable, but the question contract was defective. |
| `re_resolved` | A prior resolution was corrected under explicit review. |

## Required Timing

Every question must have absolute timestamps for:

- `openAt`
- `closeAt`
- `resolveAt`

Relative dates such as "tomorrow" may appear in a title, but the contract must store absolute dates.

## Resolution Governance

Every question must identify:

- resolution authority
- primary resolution source
- fallback resolution sources, when available
- valid outcome space
- unscorable handling

## Unscorable Outcomes

Use `ambiguous` when reality or source evidence is unclear.

Use `annulled` when the question contract itself failed, for example because the title and resolution criteria conflict.

Ambiguous and annulled questions should be counted in track-record reports but excluded from normal scoring summaries.
