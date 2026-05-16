#!/usr/bin/env python3
"""Check that all committed JSON schemas and fixtures parse."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    paths = sorted(ROOT.glob("spec/**/*.json"))
    for path in paths:
        json.loads(path.read_text())
    print(f"parsed {len(paths)} JSON files")


if __name__ == "__main__":
    main()
