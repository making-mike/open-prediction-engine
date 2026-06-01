#!/usr/bin/env python3
"""Run dev-only static analysis checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_HINT = 'install dev-only tools with `python3 -m pip install "ruff>=0.8,<1" "mypy>=1.13,<2"`'


def run(label: str, command: list[str]) -> None:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)
    if result.returncode == 0:
        return
    missing_module = f"No module named {label!r}"
    if missing_module in result.stderr:
        print(f"{label} is not installed; {INSTALL_HINT}", file=sys.stderr)
    raise SystemExit(result.returncode)


def main() -> None:
    run("ruff", [sys.executable, "-m", "ruff", "check", "scripts"])
    run("mypy", [sys.executable, "-m", "mypy"])
    print("checked static analysis")


if __name__ == "__main__":
    main()
