# Runtime Security And Hardening

Status: checked local readback for lightweight runtime hardening.

This contract records the security and runtime-hardening boundaries that apply before OPE expands into broader source execution, hosted workers, external transports, or private database/API runtimes. It is intentionally local and small: normal checks do not install runtime packages, start hidden services, fetch live sources, or write persistent state.

## Commands

```bash
python3 scripts/ope.py runtime-security
python3 scripts/ope.py runtime-security --view budget
python3 scripts/ope.py runtime-security --view modules
python3 scripts/ope.py runtime-security --view surfaces
python3 scripts/ope.py runtime-security --view threats
python3 scripts/ope.py runtime-security --view blocked
python3 scripts/ope.py runtime-security --view boundary
python3 scripts/ope.py runtime-security --check
```

The checked fixture is written to:

```text
spec/fixtures/generated/runtime-security/ope-runtime-security.generated.json
```

Runtime transport promotion is checked separately by `spec/runtime-transport-readiness.md` and `python3 scripts/ope.py runtime-transport-readiness`. Local HTTP, queue, hosted service, and OPP HTTP provider behavior stay deferred there until security, adoption, storage, secret-reference, and operations readiness are met.

## Boundary

The runtime-security readback covers:

- dependency budget: core runtime remains Python standard library only; `ruff` and `mypy` are dev-only release tools;
- module boundaries: lifecycle, storage adapter, source adapter, method adapter, transport adapter, worker runtime, and domain/source setup stay separated by clear call classes;
- runtime surface controls: embedded internal API, local SQLite storage adapter, background worker, local source runtime, and domain/source setup declare path allow-listing, symlink escape checks, database path checks, input limits, response limits, sanitized diagnostics, and credential-reference-only handling;
- credential handling: OPE records may carry credential references, source policy IDs, and sanitized provenance, but not credential values;
- threat notes: malicious source data, prompt/source injection, path traversal, idempotency replay, lease abuse, oversized responses, and accidental private-data exposure have checked or bounded mitigations;
- blocked examples: path traversal, symlink escape, database outside allow-list, oversized response, and credential value in record all return sanitized diagnostics without echoing raw values.

## Non-Goals

This is not an independent security audit, hosted runtime authorization system, secret manager, web firewall, production database connector, or live source execution framework. It does not make broader quality, privacy, or compliance claims. Future hosted, database-backed, or private-source runtimes must pass equivalent checks before promotion.
