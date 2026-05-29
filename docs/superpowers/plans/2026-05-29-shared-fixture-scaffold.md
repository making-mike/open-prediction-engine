# Shared Fixture Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the duplicated fixture-scaffold code (the 71×-copied `render_json` and the 70×-copied write / drift-check pair) by moving it into one shared module that every script imports.

**Architecture:** New stdlib-only module `scripts/ope_fixtures.py` with four functions (`render_json`, `compact_json`, `write_generated`, `check_generated`). Scripts import them instead of carrying local copies. The refactor is behavior-preserving: generated fixtures stay **byte-identical**, and the existing `--check` drift checks (run by `scripts/run_checks.py`) are the regression test. No new dependencies, no test framework, no schema/spec/doc/fixture changes.

**Tech Stack:** Python 3.12 standard library only. Verification via `python3 scripts/run_checks.py` (168 checks) plus a new `scripts/check_ope_fixtures.py` unit check.

**Design reference:** `docs/superpowers/specs/2026-05-29-shared-fixture-scaffold-design.md`

---

## The repeated verification gate (used by every migration batch)

After each batch, run this **gate**. All three must hold before committing:

```bash
python3 -m py_compile scripts/*.py                 # 1. everything still compiles/imports
python3 scripts/run_checks.py                      # 2. all 168 checks green
git status --porcelain spec/fixtures/generated/    # 3. MUST print nothing
```

- Gate 2 is definitive: every generator's `--check` rebuilds its record in memory, renders it, and compares to the committed fixture. If the refactor changed a single output byte, `--check` fails and the suite goes red. **Suite green ⟺ output identical.**
- Gate 3 is belt-and-suspenders: we never run `--write` during migration, so the committed fixtures must remain untouched on disk.
- `run_checks.py` takes ~2 minutes (the `check_cli.py` stage shells out to the CLI many times). If you want a faster per-batch loop, run only the migrated files' own `--check` per batch and run the full suite once at the end of each Task. The full suite is the authority.

---

## Task 0: Create the shared module and its unit check

**Files:**
- Create: `scripts/ope_fixtures.py`
- Create: `scripts/check_ope_fixtures.py`
- Modify: `scripts/run_checks.py` (add one line)

- [ ] **Step 1: Write the failing check first**

Create `scripts/check_ope_fixtures.py`:

```python
#!/usr/bin/env python3
"""Check the shared fixture-scaffold helpers."""

from __future__ import annotations

import io
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from ope_fixtures import check_generated, compact_json, render_json, write_generated


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    sample = {"b": 1, "a": [1, 2]}
    require(
        render_json(sample) == '{\n  "b": 1,\n  "a": [\n    1,\n    2\n  ]\n}\n',
        "render_json must pretty-print indent=2, insertion order, trailing newline",
    )
    require(
        compact_json(sample) == '{"b":1,"a":[1,2]}\n',
        "compact_json must use compact separators and a trailing newline",
    )

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "nested" / "record.generated.json"
        regen = "python3 scripts/generate_example.py --write"

        out = io.StringIO()
        with redirect_stdout(out):
            write_generated(path, sample, label="example record", regen=regen)
        require(path.read_text(encoding="utf-8") == render_json(sample), "write_generated must write render_json output")
        require(out.getvalue() == "generated example record\n", "write_generated must announce generation")

        out = io.StringIO()
        with redirect_stdout(out):
            check_generated(path, sample, label="example record", regen=regen)
        require(out.getvalue() == "checked example record\n", "check_generated must announce a clean check")

        path.write_text("drifted\n", encoding="utf-8")
        err = io.StringIO()
        raised = False
        try:
            with redirect_stderr(err):
                check_generated(path, sample, label="example record", regen=regen)
        except SystemExit as exc:
            raised = exc.code == 1
        require(raised, "check_generated must SystemExit(1) on drift")
        require("example record drift:" in err.getvalue(), "drift message must name the label")
        require(regen in err.getvalue(), "drift message must include the regen command")

        missing = Path(tmp) / "absent.generated.json"
        err = io.StringIO()
        raised = False
        try:
            with redirect_stderr(err):
                check_generated(missing, sample, label="example record", regen=regen)
        except SystemExit as exc:
            raised = exc.code == 1
        require(raised, "check_generated must SystemExit(1) when the file is missing")
        require("missing example record:" in err.getvalue(), "missing message must name the label")

    print("checked shared fixture helpers")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it to confirm it fails (module does not exist yet)**

Run: `python3 scripts/check_ope_fixtures.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'ope_fixtures'`

- [ ] **Step 3: Create the module**

Create `scripts/ope_fixtures.py`:

```python
#!/usr/bin/env python3
"""Shared helpers for rendering and writing/checking generated fixtures."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"


def compact_json(data: Any) -> str:
    return json.dumps(data, separators=(",", ":"), sort_keys=False) + "\n"


def write_generated(path: Path, data: Any, *, label: str, regen: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_json(data), encoding="utf-8")
    print(f"generated {label}")


def check_generated(path: Path, data: Any, *, label: str, regen: str) -> None:
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

- [ ] **Step 4: Run the check to confirm it passes**

Run: `python3 scripts/check_ope_fixtures.py`
Expected: PASS — prints `checked shared fixture helpers`

- [ ] **Step 5: Wire the check into the suite**

In `scripts/run_checks.py`, immediately after the `check_schema_contracts.py` line (line 20), add:

```python
    run([sys.executable, "scripts/check_ope_fixtures.py"])
```

- [ ] **Step 6: Run the gate and commit**

```bash
python3 -m py_compile scripts/*.py
python3 scripts/run_checks.py
git status --porcelain spec/fixtures/generated/   # must be empty
git add scripts/ope_fixtures.py scripts/check_ope_fixtures.py scripts/run_checks.py
git commit -m "refactor: add shared ope_fixtures module with render/write/check helpers"
```

---

## Task 1: Migrate `render_json` to the shared module (71 files, ~5 batches)

**Files:** every script that defines a local `render_json`. Discover the current list with:

```bash
grep -rl "def render_json" scripts/*.py    # 71 files as of 2026-05-29
```

**The per-file transformation is identical everywhere.** In each file:

1. Add `from ope_fixtures import render_json` to the import block (next to the existing `from ope_schema import ...` line; if the file imports other local siblings like `import resolve_due_transit_forward_runs as resolver`, put it with those).
2. Delete the local definition:

```python
def render_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=False) + "\n"
```

3. Leave `import json` and `from typing import Any` even if now unused — removing them risks breaking files that use them elsewhere, and there is no linter to fail on unused imports. (An optional unused-import pass can follow later.)

- [ ] **Step 1: Pick the next batch of ~15 files from the grep list.**

- [ ] **Step 2: Apply the transformation above to each file in the batch.**

Concrete example — `scripts/generate_resolution_runtime_reliability.py`:
- Add after `from ope_schema import SPEC, validate_record`:
  ```python
  from ope_fixtures import render_json
  ```
- Delete lines 26-27 (`def render_json(data: Any) -> str:` and its return).

- [ ] **Step 3: Run the gate**

```bash
python3 -m py_compile scripts/*.py
python3 scripts/run_checks.py
git status --porcelain spec/fixtures/generated/   # must be empty
```
Expected: all green, no fixture changes. (Because the moved body is byte-identical, output cannot change; a failure here means a missed `def render_json` deletion or a bad import.)

- [ ] **Step 4: Commit the batch**

```bash
git add -A scripts/
git commit -m "refactor: use shared render_json (batch N/5)"
```

- [ ] **Step 5: Repeat Steps 1-4 until `grep -rl "def render_json" scripts/*.py` returns only... nothing.**

Verify completion:
```bash
grep -rl "def render_json" scripts/*.py    # expected: no output
```

---

## Task 2: Migrate the simple single-output `write_X` / `check_X` pairs (~67 files, ~7 batches)

These are the generators/runners whose write+check follow the exact single-output drift pattern. Discover them:

```bash
grep -rl "write_text(render_json(" scripts/*.py    # 70 files; excludes the 3 specials in Task 3
```

Exclude the three Task 3 specials: `generate_resolution_jobs.py`, `run_resolution_scheduler.py`, `run_transit_delay_forward.py`.

**The per-file transformation (delegation — keeps call sites and any cross-module imports intact):** replace the *bodies* of the local `write_*`/`check_*` functions with one call each to the shared helpers, carrying the file's existing `label` (the noun in its `generated <noun>` / `<noun> drift:` messages) and `regen` (its exact `` run `…` `` command). Keep the function names/signatures and `main()` unchanged.

Add the import:
```python
from ope_fixtures import render_json, write_generated, check_generated
```

Concrete example — `scripts/generate_resolution_runtime_reliability.py`.

**Before** (lines 362-379):
```python
def write_reliability(reliability: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_json(reliability), encoding="utf-8")
    print("generated resolution runtime reliability")


def check_reliability(reliability: dict[str, Any]) -> None:
    expected = render_json(reliability)
    if not OUTPUT_PATH.exists():
        print(f"missing resolution runtime reliability: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_resolution_runtime_reliability.py --write`", file=sys.stderr)
        raise SystemExit(1)
    actual = OUTPUT_PATH.read_text(encoding="utf-8")
    if actual != expected:
        print(f"resolution runtime reliability drift: {OUTPUT_PATH}", file=sys.stderr)
        print("run `python3 scripts/generate_resolution_runtime_reliability.py --write`", file=sys.stderr)
        raise SystemExit(1)
    print("checked resolution runtime reliability")
```

**After:**
```python
_LABEL = "resolution runtime reliability"
_REGEN = "python3 scripts/generate_resolution_runtime_reliability.py --write"


def write_reliability(reliability: dict[str, Any]) -> None:
    write_generated(OUTPUT_PATH, reliability, label=_LABEL, regen=_REGEN)


def check_reliability(reliability: dict[str, Any]) -> None:
    check_generated(OUTPUT_PATH, reliability, label=_LABEL, regen=_REGEN)
```

This produces byte-identical stdout/stderr (`generated resolution runtime reliability`, `missing resolution runtime reliability: <path>`, `resolution runtime reliability drift: <path>`, `checked resolution runtime reliability`) — which matters because `check_cli.py` and the per-feature checks grep these strings.

- [ ] **Step 1: Pick the next batch of ~10 files from the (filtered) grep list.**

- [ ] **Step 2: For each file, read its current `write_*`/`check_*`, copy its exact label noun and regen command, and apply the delegation transformation above.** Add the `write_generated, check_generated` import.

- [ ] **Step 3: Run the gate**

```bash
python3 -m py_compile scripts/*.py
python3 scripts/run_checks.py
git status --porcelain spec/fixtures/generated/   # must be empty
```
Expected: all green. A red `--check` or a `check_cli.py` string-match failure means a `label`/`regen` value didn't match the original output — fix that file's `_LABEL`/`_REGEN`.

- [ ] **Step 4: Commit the batch**

```bash
git add -A scripts/
git commit -m "refactor: use shared write/check helpers (batch N/7)"
```

- [ ] **Step 5: Repeat until the filtered list is exhausted.**

---

## Task 3: Migrate the 3 dual-output / parameterized specials

These compute their output path at runtime, so the caller passes the resolved `path` to the helper.

**Files:**
- Modify: `scripts/generate_resolution_jobs.py`
- Modify: `scripts/run_resolution_scheduler.py`
- Modify: `scripts/run_transit_delay_forward.py`

- [ ] **Step 1: `generate_resolution_jobs.py`** — it already has `output_path(args)` (returns `OUTPUT_PATH` or `CAMPAIGN_OUTPUT_PATH`) and `write_registry(registry, args)` / `check_registry(registry, args)`. Replace their bodies:

```python
from ope_fixtures import render_json, write_generated, check_generated

_LABEL = "resolution jobs"
_REGEN = "python3 scripts/generate_resolution_jobs.py --write"


def write_registry(registry: dict[str, Any], args: argparse.Namespace) -> None:
    write_generated(output_path(args), registry, label=_LABEL, regen=_REGEN)


def check_registry(registry: dict[str, Any], args: argparse.Namespace) -> None:
    check_generated(output_path(args), registry, label=_LABEL, regen=_REGEN)
```
Keep `output_path`, `GENERATED`, and `main()` as-is. (`write_generated` does its own `mkdir`, so the old `GENERATED.mkdir` line is now inside the helper.)

- [ ] **Step 2: `run_resolution_scheduler.py`** — same shape: it has `output_path(args)`, `write_report(report, args)`, `check_report(report, args)`. Replace their bodies with `write_generated(output_path(args), report, label="resolution scheduler", regen="python3 scripts/run_resolution_scheduler.py --write")` and the `check_generated` equivalent. Add the import. **Also** replace this file's local `render_json` and `compact_json` with `from ope_fixtures import render_json, compact_json` (this is the one file that defines `compact_json`); leave `append_log`/JSONL logic untouched.

- [ ] **Step 3: `run_transit_delay_forward.py`** — open it and read its current write/check (around `validate_summary`, line ~344, and `OUTPUT_PATH = …weather-transit-delays-forward-run.generated.json`, line 22). Apply the same delegation: `write_generated(<its output path>, summary, label="transit delay forward run", regen="python3 scripts/run_transit_delay_forward.py --write")` and `check_generated(...)`, using the file's **existing** label noun and regen string verbatim (copy them from its current messages; do not invent). Preserve any live/phase path logic by passing the path the original code used.

- [ ] **Step 4: Run the gate, with extra attention to the campaign + forward-run checks**

```bash
python3 -m py_compile scripts/*.py
python3 scripts/run_resolution_scheduler.py --check
python3 scripts/run_resolution_scheduler.py --campaign predictioncampaign-001 --check
python3 scripts/generate_resolution_jobs.py --check
python3 scripts/generate_resolution_jobs.py --campaign predictioncampaign-001 --check
python3 scripts/run_transit_delay_forward.py --check
python3 scripts/run_checks.py
git status --porcelain spec/fixtures/generated/   # must be empty
```
Expected: all green.

- [ ] **Step 5: Commit**

```bash
git add -A scripts/
git commit -m "refactor: route dual-output generators through shared write/check helpers"
```

---

## Final verification

- [ ] **No local `render_json` remains:** `grep -rl "def render_json" scripts/*.py` → no output.
- [ ] **No local single-output drift logic remains:** `grep -rln "drift:" scripts/*.py` should now only match `scripts/ope_fixtures.py`.
- [ ] **Suite green:** `python3 scripts/run_checks.py`.
- [ ] **Zero fixture churn across the whole effort:** `git diff --stat <first-commit>^..HEAD -- spec/fixtures/generated/` → empty.

---

## Self-Review (completed during planning)

- **Spec coverage:** module + 4 helpers (Task 0) ✓; `render_json` dedup (Task 1) ✓; `write_generated`/`check_generated` dedup for simple generators (Task 2) ✓; 3 dual-output specials (Task 3) ✓; byte-identical invariant + gate (every Task) ✓; `compact_json` relocation (Task 3 Step 2) ✓; non-goals respected (no class, no schema/spec/doc/fixture edits) ✓.
- **Placeholder scan:** none — every code step shows complete code; file lists are produced by exact `grep` commands rather than stale hardcoded paths.
- **Type/name consistency:** helper names and signatures (`render_json`, `compact_json`, `write_generated(path, data, *, label, regen)`, `check_generated(path, data, *, label, regen)`) are identical in Task 0's definition, Task 0's check, and every call site in Tasks 1-3.
- **Known soft spot:** Task 3 Step 3 (`run_transit_delay_forward.py`) instructs reading the file's current label/regen rather than quoting them, because its exact strings weren't captured during planning. The gate (campaign + forward-run `--check`) catches any mismatch.
