#!/usr/bin/env python3
"""Check the CI release workflow stays aligned with local release expectations."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-check.yml"


def main() -> None:
    if not WORKFLOW.exists():
        raise AssertionError("missing release-check workflow")
    text = WORKFLOW.read_text(encoding="utf-8")
    required_snippets = [
        "name: Release Check",
        "pull_request:",
        "push:",
        "branches:",
        "- main",
        "permissions:",
        "contents: read",
        "actions/checkout@v4",
        "actions/setup-python@v5",
        'python-version: "3.12"',
        "python3 --version",
        "Install dev-only static analysis tools",
        'python3 -m pip install "ruff>=0.8,<1" "mypy>=1.13,<2"',
        "python3 scripts/release_check.py",
        "python3 -m py_compile scripts/*.py",
    ]
    for snippet in required_snippets:
        if snippet not in text:
            raise AssertionError(f"release-check workflow missing {snippet!r}")

    forbidden_snippets = [
        "secrets.",
        "deploy",
        "publish",
        "gh release",
        "git push",
        "docker login",
        "pypi",
        "npm publish",
        "curl ",
        "wget ",
    ]
    lower_text = text.lower()
    for snippet in forbidden_snippets:
        if snippet in lower_text:
            raise AssertionError(f"release-check workflow contains forbidden snippet {snippet!r}")

    print("checked CI release workflow")


if __name__ == "__main__":
    main()
