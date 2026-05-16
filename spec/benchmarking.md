# Benchmark And Anti-Leakage Rules

Benchmark runs must prove that a forecast used only information available before the declared retrieval cutoff. A benchmark run that includes known-answer material, post-resolution material, or resolution-source observations in its forecast inputs is invalid.

## Required Records

Each benchmark run records:

- benchmark run ID
- started and ended timestamps
- question IDs
- model ID and version
- model training cutoff when known
- retrieval window
- source fetch references with retrieval timestamps
- source content hashes where available
- leakage-control booleans

## Clean Pre-Outcome Run

A clean benchmark run must satisfy all of these checks:

- retrieval window ends before the forecast question closes
- model training cutoff is not after the retrieval window
- every fetched source has `retrievedAt`
- every fetched source has `contentHash`
- every fetched source was retrieved no later than the retrieval window end
- fetched sources do not include primary or fallback resolution sources
- `knownAnswerExcluded` is true
- `postOutcomeDataBlocked` is true
- `sourceTimestampsRecorded` is true

## Post-Resolution Leakage Audit

When a benchmark run is reviewed after outcomes are known, the audit must check:

- no source URI or hash matches a resolution source
- no source retrieval timestamp is after the retrieval window
- no prompt, feature snapshot, or rationale includes the resolved outcome
- no model training cutoff is after the retrieval window unless the benchmark is explicitly labeled contaminated
- no corrected or backfilled source was substituted for the source state available at retrieval time
- invalidated runs are kept as negative fixtures instead of silently deleted

## Fixture Coverage

The first benchmark fixtures are:

- `spec/fixtures/benchmark/clean-pre-outcome-run.json`: expected to pass.
- `spec/fixtures/benchmark/post-outcome-leakage-run.json`: expected to fail the anti-leakage checker.
