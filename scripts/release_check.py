#!/usr/bin/env python3
"""Run the current release-readiness check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    run([sys.executable, "scripts/run_checks.py"])
    run([sys.executable, "scripts/check_static_analysis.py"])


if __name__ == "__main__":
    main()
