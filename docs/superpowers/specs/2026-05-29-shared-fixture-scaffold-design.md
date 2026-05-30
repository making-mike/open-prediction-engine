# Shared Fixture Scaffold — Design

- **Date:** 2026-05-29
- **Status:** approved (design); pending implementation plan
- **Scope item:** Review finding #3 — extract the duplicated generate/check scaffold.

## Problem

The repo grows by cloning a per-feature scaffold across ~180 scripts. Two
snippets dominate the duplication:

- `render_json(data)` — `json.dumps(data, indent=2, sort_keys=False) + "\n"` —
  is **byte-identical in 71 files**.
- The fixture **write / drift-check** pair is structurally identical in **70
  files**: `mkdir` + `write_text(render_json(...))` on write, and on check
  read-the-file / compare-to-expected / print `missing …` or `… drift:` to
  stderr / `SystemExit(1)`.

Because each copy is independent, any change to the pattern means editing dozens
of files, and bugs fixed in one copy don't propagate. This is the largest
structural quality liability in the codebase.

## Goal

One shared home for these helpers; every script imports them instead of carrying
its own copy. Behavior is unchanged.

## Non-goals (YAGNI)

- No `GeneratedArtifact`/class abstraction.
- No consolidation of `main()`/argparse boilerplate.
- No changes to schemas, specs, docs, or **fixture content**.
- No new dependencies (stdlib-only is preserved).

## Design

New module `scripts/ope_fixtures.py`, kept separate from `ope_schema.py`
(validation vs. fixture I/O are different concerns). Four functions:

```python
def render_json(data) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"

def compact_json(data) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=False) + "\n"

def write_generated(path, data, *, label, regen) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")
    print(f"generated {label}")

def check_generated(path, data, *, label, regen) -> None:
    expected = render_json(data)
    if not path.exists():
        print(f"missing {label}: {path}", file=sys.stderr)
        print(f"run `{regen}`", file=sys.stderr)
        raise SystemExit(1)
    if path.read_text(encoding="utf-8") != expected:
        print(f"{label} drift: {path}", file=sys.stderr)
        print(f"run `{regen}`", file=sys.stderr)
        raise SystemExit(1)
    print(f"checked {label}")
```

Two design choices make this a drop-in replacement:

1. **`label` + `regen` parameters reproduce today's exact stdout/stderr.**
   e.g. `label="resolution scheduler"` → `generated resolution scheduler`,
   `missing resolution scheduler: <path>`, `resolution scheduler drift: <path>`,
   `checked resolution scheduler`; `regen="python3 scripts/... --write"` →
   `run \`python3 scripts/... --write\``. Several checks (notably
   `check_cli.py`) grep this output, so the strings must match exactly.
2. **`path` is passed in, not hardcoded.** The 3 dual-output generators compute
   their path (campaign vs. default) and pass it; the helper stays generic.

## Key invariant

Every step must leave `git diff spec/fixtures/generated/` **empty** and
`python3 scripts/run_checks.py` **green**. Byte-identical output proves the
change is a pure refactor. The existing drift checks are the regression test —
no test framework is added.

## Incremental rollout

Each step is its own commit, gated on the invariant above.

- **Step 0 — create the module.** Add `scripts/ope_fixtures.py` with the four
  helpers. No call sites yet. Verify it imports and `run_checks.py` is green.
- **Step 1 — migrate `render_json` (71 files, batches of ~15).** In each file,
  delete the local `def render_json` and add
  `from ope_fixtures import render_json`. Zero behavior risk (identical body).
  ~5 commits.
- **Step 2 — migrate the ~67 single-output `write_X`/`check_X` (batches of
  ~10).** Replace each pair with calls to `write_generated`/`check_generated`,
  sourcing `path`/`label`/`regen` from the file's existing constants. Confirm no
  output-string regressions (the `label`/`regen` mapping reproduces them).
- **Step 3 — the 3 dual-output specials.** `generate_resolution_jobs.py`,
  `run_resolution_scheduler.py`, `run_transit_delay_forward.py`: the caller
  computes the path (including the campaign branch / per-file loop) and calls the
  helper. Verify campaign + default + multi-file checks.

`compact_json` lives in one file today (JSONL scheduler logs); it moves to the
shared module for cohesion but is not a duplication win.

## Special cases

- **Multi-file generators** (e.g. `run_transit_delay_forecast.py` writes 7
  files) call the helper once per file.
- **Dual-output / campaign generators** pass the resolved path per Step 3.
- Any file whose `write`/`check` message does **not** fit the `label`/`regen`
  shape stays on its own implementation rather than being forced into the
  helper — correctness over coverage.

## Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| A migrated file changes fixture bytes | `git diff spec/fixtures/generated/` must be empty after each batch; revert that batch if not. |
| An output-grepping check breaks (e.g. `check_cli.py`) | `label`/`regen` reproduce exact strings; `run_checks.py` green per batch catches any miss. |
| Circular import | `ope_fixtures.py` imports only stdlib; generators import from it. No cycle. |
| Large blast radius | Small batches, each its own commit and its own suite run. |

## Acceptance criteria

- `scripts/ope_fixtures.py` exists and is the single definition of the four
  helpers.
- No remaining local `def render_json` in `scripts/` (71 → 0).
- The ~67 simple generators use `write_generated`/`check_generated`.
- `python3 scripts/run_checks.py` green; `git diff spec/fixtures/generated/`
  empty across the whole effort.
