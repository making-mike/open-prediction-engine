#!/usr/bin/env python3
"""Generate or check private setup first-action dispatcher fixtures."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from generate_private_setup_requests import build_request_set, render_json
from private_setup_action_dispatcher import action_from_request_row, validate_action


ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "spec" / "fixtures" / "generated" / "private-setup-actions"


def action_path(source_kind: str) -> Path:
    return GENERATED / f"ope-private-setup-first-action-{source_kind.replace('_', '-')}.generated.json"


def build_actions() -> list[dict[str, Any]]:
    request_set = build_request_set()
    actions: list[dict[str, Any]] = []
    for index, row in enumerate(request_set["requestRows"], start=1):
        actions.append(action_from_request_row(row, request_set, sequence=index))
    return actions


def write_actions(actions: list[dict[str, Any]]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for action in actions:
        action_path(action["sourceKind"]).write_text(render_json(action), encoding="utf-8")
    print(f"generated {len(actions)} private setup first actions")


def check_actions(actions: list[dict[str, Any]]) -> None:
    for action in actions:
        path = action_path(action["sourceKind"])
        expected = render_json(action)
        if not path.exists():
            print(f"missing private setup first action: {path}", file=sys.stderr)
            print("run `python3 scripts/generate_private_setup_first_actions.py --write`", file=sys.stderr)
            raise SystemExit(1)
        actual = path.read_text(encoding="utf-8")
        if actual != expected:
            print(f"private setup first action drift: {path}", file=sys.stderr)
            print("run `python3 scripts/generate_private_setup_first_actions.py --write`", file=sys.stderr)
            raise SystemExit(1)
    print(f"checked {len(actions)} private setup first actions")


def load_generated_actions() -> list[dict[str, Any]] | None:
    paths = sorted(GENERATED.glob("ope-private-setup-first-action-*.generated.json"))
    paths = [path for path in paths if path.name != "ope-private-setup-first-action-runbook.generated.json"]
    if not paths:
        return None
    actions = []
    for path in paths:
        action = json.loads(path.read_text(encoding="utf-8"))
        validate_action(action)
        actions.append(action)
    return sorted(actions, key=lambda item: item["privateSetupFirstActionId"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check generated private setup first-action drift")
    parser.add_argument("--write", action="store_true", help="write generated private setup first actions")
    parser.add_argument("--rebuild", action="store_true", help="rebuild before printing instead of loading checked fixtures")
    args = parser.parse_args()
    actions = build_actions() if args.write or args.check or args.rebuild else (load_generated_actions() or build_actions())
    if args.write:
        write_actions(actions)
    elif args.check:
        check_actions(actions)
    else:
        sys.stdout.write(render_json({"count": len(actions), "actions": actions}))


if __name__ == "__main__":
    main()
