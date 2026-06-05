# Runtime Transport Readiness

Status: checked runtime transport readiness gate.

Last reviewed: 2026-06-04.

OPE currently supports local, non-networked runtime surfaces. This readiness gate answers when local HTTP, queue, hosted service, and OPP HTTP provider behavior may be introduced: not yet. The checked current runtime remains in-process internal API, CLI, `agent-call`, and local MCP stdio.

Default checked readback:

```bash
python3 scripts/ope.py runtime-transport-readiness
python3 scripts/ope.py runtime-transport-readiness --view summary
python3 scripts/ope.py runtime-transport-readiness --view current
python3 scripts/ope.py runtime-transport-readiness --view future
python3 scripts/ope.py runtime-transport-readiness --view decisions
python3 scripts/ope.py runtime-transport-readiness --view criteria
python3 scripts/ope.py runtime-transport-readiness --view blocked
python3 scripts/ope.py runtime-transport-readiness --view boundary
python3 scripts/ope.py runtime-transport-readiness --surface hosted_service_runtime
python3 scripts/ope.py runtime-transport-readiness --case normal_check_http_server
python3 scripts/ope.py runtime-transport-readiness --check
```

## Current Surfaces

The checked local surfaces are:

- `embedded_internal_api`
- `cli`
- `agent_call`
- `local_mcp_stdio`

These surfaces are covered by normal checks, do not start network listeners, do not require hosted runtime, do not mutate state by default, and do not accept credential values.

## Future Surfaces

The following surfaces remain deferred or blocked:

- `local_http_adapter`: deferred until adoption evidence and security checks show a concrete need for a listener.
- `queue_adapter`: deferred until a hosted/runtime gate exists.
- `hosted_service_runtime`: blocked until pilot, security, storage, and operations readiness are checked.
- `opp_http_provider`: future adapter work only; today OPP remains a checked fixture mapping over OPE records.

## Readiness Criteria

Six criteria are met for local readbacks: internal API stability, lifecycle operation store checks, runtime security checks, persistent SQLite policy, lifecycle lease policy, and agent adapter protocol-map checks.

Hosted or HTTP promotion remains blocked by missing real pilot/adoption evidence, hosted observability, production secret-reference policy, and hosted storage migration execution. Postgres compatibility is a semantics checkpoint, not hosted storage readiness.

## Blocked Cases

The readback records blocked cases for normal-check HTTP servers, implicit hosted services, OPP HTTP endpoint requests, queue workers without readiness, credential values in records, default live fetches, and unbounded background daemons. Each blocked case starts no listener, starts no hosted runtime, writes no state, stores no credentials, and returns sanitized diagnostics.

## Boundary

This contract does not implement local HTTP, hosted service, queue runtime, OPP HTTP provider, payment settlement, production live fetching, credential storage, or stronger quality claims. It is a readiness gate that keeps transports as wrappers over OPE semantics rather than new behavior.
